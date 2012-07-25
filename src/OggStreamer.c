/*
 * oggstreamer - Ogg Vorbis streamer for SDL_mixer/pygame
 * Copyright (C) 2009 John Stumpo
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#include <Python.h>
#include <vorbis/vorbisfile.h>
#include <SDL.h>
#include <SDL_mixer.h>

#if PY_MAJOR_VERSION >= 3
#define PY3K
#endif

#define OGGSTREAM_BUFFER_SIZE 131072
#define PLAY_CHUNK_SIZE (OGGSTREAM_BUFFER_SIZE / 4)
#define MAX_CHANNELS 64

typedef struct {
  PyObject_HEAD
  int channel;  /* SDL_mixer channel number that this stream is tied to */
  OggVorbis_File ovfile;  /* libvorbisfile handle */
  char* buffer;  /* ring buffer for audio data */
  int bufpos;  /* buffer position for next Mix_PlayChannel call */
  int bufsize;  /* number of valid bytes in buffer */
  Mix_Chunk chunk;  /* structure used to play samples from buffer */
} PyStreamingOggSoundObject;

static PyStreamingOggSoundObject* channelmap[MAX_CHANNELS];

static PyObject* PyExc_OggStreamerError;

/* Read more sound into the buffer.
   Returns NULL on success or a pointer to an error message on error. */
static char* sos_fillbuf_nogil(PyStreamingOggSoundObject* self)
{
  static char errmsgbuf[256];
  int freq;
  Uint16 format;
  int channels;
  char buf[4096];
  int be;
  int wordsize;
  int signedsamps;
  int curstream;
  int readsize;
  long bytes_read;
  int startpos;
  int endpos;

  if (!Mix_QuerySpec(&freq, &format, &channels)) {
    strncpy(errmsgbuf, Mix_GetError(), sizeof(errmsgbuf) - 1);
    errmsgbuf[sizeof(errmsgbuf) - 1] = '\0';
    return errmsgbuf;
  }

  switch (format) {
    case AUDIO_U8: be = 0; wordsize = 1; signedsamps = 0; break;
    case AUDIO_S8: be = 0; wordsize = 1; signedsamps = 1; break;
    case AUDIO_U16LSB: be = 0; wordsize = 2; signedsamps = 0; break;
    case AUDIO_S16LSB: be = 0; wordsize = 2; signedsamps = 1; break;
    case AUDIO_U16MSB: be = 1; wordsize = 2; signedsamps = 0; break;
    case AUDIO_S16MSB: be = 1; wordsize = 2; signedsamps = 1; break;
    default:
      Py_FatalError("sos_fillbuf_nogil: should not happen!");
      return errmsgbuf;  /* make compiler happy */
  }

  /* TODO: sampling rate and channel count munging */
  while (self->bufsize < OGGSTREAM_BUFFER_SIZE) {
    readsize = OGGSTREAM_BUFFER_SIZE - self->bufsize;
    if (readsize > 4096)
      readsize = 4096;
    bytes_read = ov_read(&self->ovfile, buf, readsize,
      be, wordsize, signedsamps, &curstream);
    if (bytes_read == 0)
      return NULL;
    else if (bytes_read < 0) {
      snprintf(errmsgbuf, sizeof(errmsgbuf), "ov_read: %ld", bytes_read);
      return errmsgbuf;
    }

    startpos = (self->bufpos + self->bufsize) % OGGSTREAM_BUFFER_SIZE;
    endpos = (startpos + bytes_read) % OGGSTREAM_BUFFER_SIZE;
    if (endpos > startpos) {
      memcpy(self->buffer + startpos, buf, bytes_read);
    } else {
      memcpy(self->buffer + startpos, buf, OGGSTREAM_BUFFER_SIZE - startpos);
      memcpy(self->buffer, buf + (OGGSTREAM_BUFFER_SIZE - startpos), endpos);
    }

    self->bufsize += bytes_read;
  }

  return NULL;
}

static int sos_fillbuf(PyStreamingOggSoundObject* self)
{
  char* result;
  if ((result = sos_fillbuf_nogil(self)) != NULL) {
    PyErr_Format(PyExc_OggStreamerError, "%s", result);
    return 0;
  } else {
    return 1;
  }
}

static int sos_stop_nohalt(PyStreamingOggSoundObject* self)
{
  int channel = self->channel;
  Py_XDECREF(channelmap[channel]);
  channelmap[channel] = NULL;
  return channel;
}

static void sos_stop(PyStreamingOggSoundObject* self)
{
  int channel = sos_stop_nohalt(self);
  if (SDL_WasInit(SDL_INIT_AUDIO))
    Mix_HaltChannel(channel);
}

static void sos_channelFinished(int channel)
{
  PyStreamingOggSoundObject* self = channelmap[channel];
  if (!self)
    return;

  self->bufpos += self->chunk.alen;
  self->bufpos %= OGGSTREAM_BUFFER_SIZE;
  self->bufsize -= self->chunk.alen;
  self->chunk.abuf = (Uint8*)(self->buffer + self->bufpos);
  self->chunk.alen =
    (PLAY_CHUNK_SIZE < self->bufsize) ? PLAY_CHUNK_SIZE : self->bufsize;
  if (self->bufsize <= 0) {
    sos_stop_nohalt(self);
  } else {
    if (Mix_PlayChannel(channel, &self->chunk, 0) == -1) {
      sos_stop_nohalt(self);
    }
    sos_fillbuf_nogil(self);
  }
}

static int sos_play(PyStreamingOggSoundObject* self)
{
  if (!sos_fillbuf(self))
    return 0;

  self->chunk.abuf = (Uint8*)(self->buffer + self->bufpos);
  self->chunk.alen =
    (PLAY_CHUNK_SIZE < self->bufsize) ? PLAY_CHUNK_SIZE : self->bufsize;
  Py_INCREF(self);
  channelmap[self->channel] = self;
  Mix_ChannelFinished(sos_channelFinished);
  if (Mix_PlayChannel(self->channel, &self->chunk, 0) == -1) {
    PyErr_Format(PyExc_OggStreamerError, "%s", Mix_GetError());
    Py_DECREF(self);
    channelmap[self->channel] = NULL;
    return 0;
  }
  return 1;
}

static int sos_seek_and_reset(PyStreamingOggSoundObject* self, double offset)
{
  int retval;

  sos_stop(self);

  if (offset != -1.0) {
    retval = ov_time_seek(&self->ovfile, offset);
    if (retval != 0) {
      PyErr_Format(PyExc_OggStreamerError, "ov_time_seek: %d", retval);
      return 0;
    }
  }

  self->bufpos = 0;
  self->bufsize = 0;
  return sos_fillbuf(self);
}

static int sos_isPlaying(PyStreamingOggSoundObject* self)
{
  return Mix_Playing(self->channel);
}

static PyObject* StreamingOggSound_New(PyTypeObject* type,
  PyObject* args, PyObject* kw)
{
  int retval;
  int channel;
  char* filename;
  char* buf;
  char* kwnames[] = {"channel", "filename", NULL};
  PyStreamingOggSoundObject* self;

  if (!PyArg_ParseTupleAndKeywords(args, kw, "is",
    kwnames, &channel, &filename))
      return NULL;

  if (!SDL_WasInit(SDL_INIT_AUDIO))
    return PyErr_Format(PyExc_OggStreamerError, "SDL audio is not initialized");

  if (!(buf = malloc(OGGSTREAM_BUFFER_SIZE)))
    return PyErr_NoMemory();

  if (!(self = (PyStreamingOggSoundObject*)type->tp_alloc(type, 0))) {
    free(buf);
    return NULL;
  }

  self->channel = channel;
  self->buffer = buf;
  self->chunk.allocated = 0;
  self->chunk.abuf = NULL;
  self->chunk.alen = 0;
  self->chunk.volume = 128;

  retval = ov_fopen(filename, &self->ovfile);
  if (retval < 0) {
    Py_DECREF(self);
    return PyErr_Format(PyExc_OggStreamerError, "ov_fopen: %d", retval);
  }

  if (!sos_seek_and_reset(self, -1.0)) {
    Py_DECREF(self);
    return NULL;
  }

  return (PyObject*)self;
}

static void StreamingOggSound_Dealloc(PyStreamingOggSoundObject* self)
{
  sos_stop(self);
  ov_clear(&self->ovfile);
  free(self->buffer);
#ifdef PY3K
  Py_TYPE(self)->tp_free((PyObject*)self);
#else
  self->ob_type->tp_free((PyObject*)self);
#endif
}

static PyObject* StreamingOggSound_GetDuration(PyObject* self, PyObject* args)
{
  if (!PyArg_ParseTuple(args, ""))
    return NULL;

  return PyFloat_FromDouble(ov_time_total(
    &((PyStreamingOggSoundObject*)self)->ovfile, -1));
}

static PyObject* StreamingOggSound_Seek(PyObject* self, PyObject* args)
{
  double offset;
  int mustRestart;
  if (!PyArg_ParseTuple(args, "d", &offset))
    return NULL;

  mustRestart = sos_isPlaying((PyStreamingOggSoundObject*)self);
  if (!sos_seek_and_reset((PyStreamingOggSoundObject*)self, offset))
    return NULL;
  if (mustRestart)
    if (!sos_play((PyStreamingOggSoundObject*)self))
      return NULL;
  Py_RETURN_NONE;
}

static PyObject* StreamingOggSound_Rewind(PyObject* self, PyObject* args)
{
  PyObject* seekarg;
  PyObject* retval;
  if (!PyArg_ParseTuple(args, ""))
    return NULL;

  seekarg = Py_BuildValue("(d)", 0.0);
  retval = StreamingOggSound_Seek(self, seekarg);
  Py_DECREF(seekarg);
  return retval;
}

static PyObject* StreamingOggSound_StreamIsPlaying(PyObject* self,
  PyObject* args)
{
  if (!PyArg_ParseTuple(args, ""))
    return NULL;

  return PyBool_FromLong((long)
    sos_isPlaying((PyStreamingOggSoundObject*)self));
}

static PyObject* StreamingOggSound_Play(PyObject* self, PyObject* args)
{
  if (!PyArg_ParseTuple(args, ""))
    return NULL;

  if (!sos_play((PyStreamingOggSoundObject*)self))
    return NULL;

  Py_RETURN_NONE;
}

static PyObject* StreamingOggSound_Stop(PyObject* self, PyObject* args)
{
  if (!PyArg_ParseTuple(args, ""))
    return NULL;

  if (!sos_seek_and_reset((PyStreamingOggSoundObject*)self, 0.0))
    return NULL;

  Py_RETURN_NONE;
}

static PyObject* StreamingOggSound_SetVolume(PyObject* self, PyObject* args)
{
  double newvol;
  if (!PyArg_ParseTuple(args, "d", &newvol))
    return NULL;

  Mix_Volume(((PyStreamingOggSoundObject*)(self))->channel,
    (int)(newvol * MIX_MAX_VOLUME));
  Py_RETURN_NONE;
}

static PyMethodDef StreamingOggSound_MethodTable[] = {
  {"getDuration", StreamingOggSound_GetDuration, METH_VARARGS,
    "Get the duration of the stream in seconds."},
  {"seek", StreamingOggSound_Seek, METH_VARARGS,
    "Seek to a given position (in seconds) in the stream."},
  /* TODO: tell (or getPosition or whatever we should call it */
  {"rewind", StreamingOggSound_Rewind, METH_VARARGS,
    "Go back to the beginning of the stream."},
  {"streamIsPlaying", StreamingOggSound_StreamIsPlaying, METH_VARARGS,
    "Check whether the stream is currently playing."},
  {"play", StreamingOggSound_Play, METH_VARARGS,
    "Start playing the stream."},
  {"stop", StreamingOggSound_Stop, METH_VARARGS,
    "Stop the stream."},
  {"setVolume", StreamingOggSound_SetVolume, METH_VARARGS,
    "Set the volume of the stream."},
  {NULL, NULL, 0, NULL},
};

static PyTypeObject StreamingOggSound_Type = {
#ifdef PY3K
  PyVarObject_HEAD_INIT(NULL, 0)
#else
  PyObject_HEAD_INIT(NULL)
  0,  /* ob_size */
#endif
  "StreamingOggSound",  /* name */
  sizeof(PyStreamingOggSoundObject),  /* basicsize */
  0,  /* itemsize */
  (destructor)StreamingOggSound_Dealloc,  /* dealloc */
  0,  /* print */
  0,  /* getattr */
  0,  /* setattr */
  0,  /* compare (reserved in py3k) */
  0,  /* repr */
  0,  /* as_number */
  0,  /* as_sequence */
  0,  /* as_mapping */
  0,  /* hash */
  0,  /* call */
  0,  /* str */
  0,  /* getattro */
  0,  /* setattro */
  0,  /* as_buffer */
  Py_TPFLAGS_DEFAULT,  /* tp_flags */
  "StreamingOggSound object",  /* doc */
  0,  /* traverse */
  0,  /* clear */
  0,  /* richcompare */
  0,  /* weaklistoffset */
  0,  /* iter */
  0,  /* iternext */
  StreamingOggSound_MethodTable,  /* methods */
  0,  /* members */
  0,  /* getset */
  0,  /* base */
  0,  /* dict */
  0,  /* descr_get */
  0,  /* descr_set */
  0,  /* dictoffset */
  0,  /* init */
  0,  /* alloc */
  StreamingOggSound_New,  /* new */
};

/* We don't have any functions to expose *directly* to Python. */
static PyMethodDef OggStreamerModule_MethodTable[] = {
  {NULL, NULL, 0, NULL},
};

#ifdef PY3K
static PyModuleDef OggStreamerModule_ModuleTable = {
  PyModuleDef_HEAD_INIT,
  "OggStreamer",
  NULL,
  -1,
  OggStreamerModule_MethodTable,
};
#endif

#ifdef PY3K
#define RAISE return NULL
#else
#define RAISE return
#endif

/* Module initialization function.
   Called on "import OggStreamer".  */
PyMODINIT_FUNC
#ifdef PY3K
PyInit_OggStreamer
#else
initOggStreamer
#endif
(void)
{
  PyObject* mod;

  /* Clear the channel map. */
  memset(channelmap, 0, sizeof(channelmap));

#ifdef PY3K
  mod = PyModule_Create(&OggStreamerModule_ModuleTable);
#else
  mod = Py_InitModule("OggStreamer", OggStreamerModule_MethodTable);
#endif

  /* Expose the StreamingOggSound class to Python. */
  if (PyType_Ready(&StreamingOggSound_Type) < 0)
    RAISE;
  Py_INCREF(&StreamingOggSound_Type);
  PyModule_AddObject(mod, "StreamingOggSound",
    (PyObject*)&StreamingOggSound_Type);

  /* Define our custom exception type. */
  PyExc_OggStreamerError = PyErr_NewException("OggStreamer.OggStreamerError",
    PyExc_Exception, NULL);
  PyModule_AddObject(mod, "OggStreamerError", PyExc_OggStreamerError);

#ifdef PY3K
  return mod;
#endif

}
