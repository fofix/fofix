/* Frets on Fire X (FoFiX)
 * Copyright (C) 2011-2012 FoFiX Team
 *               2011-2012 John Stumpo
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
 * MA  02110-1301, USA.
 */

#include "MixStream.h"

#include "soundtouch-c.h"
#include <SDL_mixer.h>
#include <SDL.h>

#define FRAMES_PER_CHUNK 4096

struct _MixStream {
  int samprate;
  int channels;
  mix_stream_read_cb read_cb;
  mix_stream_seek_cb seek_cb;
  mix_stream_length_cb length_cb;
  mix_stream_free_cb free_cb;
  void* cb_data;
  int channel;
  SoundTouch* soundtouch;
  Mix_Chunk chunk;
  gboolean input_eof;
  gboolean eof;
  int out_freq;
  Uint16 out_format;
  int out_channels;
  int out_sample_size;
  gboolean out_samples_signed;
  gboolean byteswap_needed;
  GMutex* st_mutex;
  double next_read_time;
  double out_speed;
  double chunk_start_time;
  Uint32 chunk_start_ticks;
};

static GHashTable* chan_table = NULL;
static GStaticMutex chan_table_mutex = G_STATIC_MUTEX_INIT;

static void _mix_stream_soundtouchify(MixStream* stream);


/* Create a stream that will play data returned by read_cb.
 *   - samprate and channels specify the format returned by read_cb
 *   - seek_cb is called to attempt a seek (may be NULL if not implemented)
 *   - length_cb is called to get total length (may be NULL if not implemented)
 *   - free_cb is called on data when the stream is destroyed (may be NULL)
 *   - data is passed to the callbacks
 */
MixStream* mix_stream_new(int samprate, int channels, mix_stream_read_cb read_cb,
  mix_stream_seek_cb seek_cb, mix_stream_length_cb length_cb,
  mix_stream_free_cb free_cb, void* data, GError** err)
{
  MixStream* stream;

  if (!g_thread_supported())
    g_thread_init(NULL);

  stream = g_new0(MixStream, 1);
  stream->samprate = samprate;
  stream->channels = channels;
  stream->read_cb = read_cb;
  stream->seek_cb = seek_cb;
  stream->length_cb = length_cb;
  stream->free_cb = free_cb;
  stream->cb_data = data;
  stream->channel = -1;
  stream->chunk.volume = MIX_MAX_VOLUME;
  stream->out_speed = 1.0;

  if (!Mix_QuerySpec(&stream->out_freq, &stream->out_format, &stream->out_channels)) {
    g_set_error(err, MIX_STREAM_ERROR, MIX_STREAM_MIXER_UNINIT,
      "SDL_mixer is not initialized");
    g_free(stream);
    return NULL;
  }

  switch (stream->out_format) {
    case AUDIO_S8:     stream->out_sample_size = 1; stream->out_samples_signed = TRUE ; stream->byteswap_needed = FALSE; break;
    case AUDIO_U8:     stream->out_sample_size = 1; stream->out_samples_signed = FALSE; stream->byteswap_needed = FALSE; break;
#if G_BYTE_ORDER == G_LITTLE_ENDIAN
    case AUDIO_S16LSB: stream->out_sample_size = 2; stream->out_samples_signed = TRUE ; stream->byteswap_needed = FALSE; break;
    case AUDIO_U16LSB: stream->out_sample_size = 2; stream->out_samples_signed = FALSE; stream->byteswap_needed = FALSE; break;
    case AUDIO_S16MSB: stream->out_sample_size = 2; stream->out_samples_signed = TRUE ; stream->byteswap_needed = TRUE ; break;
    case AUDIO_U16MSB: stream->out_sample_size = 2; stream->out_samples_signed = FALSE; stream->byteswap_needed = TRUE ; break;
#else
    case AUDIO_S16LSB: stream->out_sample_size = 2; stream->out_samples_signed = TRUE ; stream->byteswap_needed = TRUE ; break;
    case AUDIO_U16LSB: stream->out_sample_size = 2; stream->out_samples_signed = FALSE; stream->byteswap_needed = TRUE ; break;
    case AUDIO_S16MSB: stream->out_sample_size = 2; stream->out_samples_signed = TRUE ; stream->byteswap_needed = FALSE; break;
    case AUDIO_U16MSB: stream->out_sample_size = 2; stream->out_samples_signed = FALSE; stream->byteswap_needed = FALSE; break;
#endif
    default: g_assert_not_reached(); break;
  }

  stream->st_mutex = g_mutex_new();

  if (stream->samprate != stream->out_freq) {
    _mix_stream_soundtouchify(stream);
    soundtouch_set_rate(stream->soundtouch, (float)stream->samprate/(float)stream->out_freq);
  }

  return stream;
}


/* Free a MixStream. */
void mix_stream_destroy(MixStream* stream)
{
  if (stream->channel != -1)
    mix_stream_stop(stream);
  g_mutex_free(stream->st_mutex);
  if (stream->soundtouch != NULL)
    soundtouch_delete(stream->soundtouch);
  if (stream->free_cb != NULL)
    stream->free_cb(stream->cb_data);
  g_free(stream);
}


/* Ensure the stream is using a soundtouch object. */
static void _mix_stream_soundtouchify(MixStream* stream)
{
  g_mutex_lock(stream->st_mutex);
  if (stream->soundtouch == NULL) {
    stream->soundtouch = soundtouch_new();
    soundtouch_set_sample_rate(stream->soundtouch, stream->samprate);
    soundtouch_set_channels(stream->soundtouch, stream->channels);
  }
  g_mutex_unlock(stream->st_mutex);
}


/* Fill a float buffer using a read callback and possibly a SoundTouch object. */
static gsize _mix_stream_fill_floatbuf(MixStream* stream, float* buf, gsize numframes, guint channels)
{
  const gsize frame_size = sizeof(float) * channels;
  gsize frames_obtained = 0;
  gsize frames_read;
  while (numframes > 0) {

    g_mutex_lock(stream->st_mutex);
    if (stream->soundtouch == NULL) {
      frames_read = stream->read_cb(buf, numframes * frame_size, stream->cb_data) / frame_size;
    } else {
      while (!stream->input_eof && soundtouch_num_samples(stream->soundtouch) < numframes) {
        frames_read = stream->read_cb(buf, numframes * frame_size, stream->cb_data) / frame_size;
        if (frames_read == 0) {
          stream->input_eof = TRUE;
          soundtouch_flush(stream->soundtouch);
          break;
        }
        soundtouch_put_samples(stream->soundtouch, buf, frames_read);
      }
      frames_read = soundtouch_receive_samples(stream->soundtouch, buf, numframes);
    }
    g_mutex_unlock(stream->st_mutex);

    if (frames_read == 0) {
      if (frames_obtained != 0) {
        /* Fill up the rest of the buffer with silence. */
        memset(buf, 0, numframes * frame_size);
        frames_obtained += numframes;
      }
      stream->eof = TRUE;
      break;
    }

    frames_obtained += frames_read;
    buf += frames_read * channels;
    numframes -= frames_read;
  }
  return frames_obtained;
}


/* Set the stream's audio chunk be the next size bytes of audio. */
static gboolean _mix_stream_nextchunk(MixStream* stream, gsize size)
{
  // compute necessary number of samples
  // if there's an active soundtouch object:
  //   while not enough samples in soundtouch output:
  //     call callback to get more samples
  //     feed new samples to soundtouch
  // else:
  //   call callback to get samples
  // perform any necessary conversions
  int needed_frames;
  int obtained_frames;
  float* floatbuf;
  guint8* out_buf;

  if (stream->eof)
    return FALSE;

  if (stream->chunk.alen < size) {
    stream->chunk.abuf = g_realloc(stream->chunk.abuf, size);
    stream->chunk.alen = size;
  }
  out_buf = stream->chunk.abuf;

  needed_frames = size / (stream->out_channels * stream->out_sample_size);

  floatbuf = g_newa(float, needed_frames * stream->channels);
  obtained_frames = _mix_stream_fill_floatbuf(stream, floatbuf, needed_frames, stream->channels);
  if (obtained_frames == 0)
    return FALSE;

  while (size > 0) {
    float current_sample = *(floatbuf++);
    /* If we're converting stereo to mono, average this sample with the other channel's. */
    if (stream->channels == 2 && stream->out_channels == 1)
      current_sample = (float)(0.5 * (current_sample + *(floatbuf++)));
    current_sample = CLAMP(current_sample, -1.0, 1.0);

#define OUTPUT_SAMPLE(type, value) { *(type*)out_buf = (type)(value); out_buf += sizeof(type); size -= sizeof(type); }

    /* Convert and output the sample. */
    if (stream->out_samples_signed) {
      if (stream->out_sample_size == 1) {
        OUTPUT_SAMPLE(gint8, current_sample * G_MAXINT8);
      } else if (!stream->byteswap_needed) {
        OUTPUT_SAMPLE(gint16, current_sample * G_MAXINT16);
      } else {
        OUTPUT_SAMPLE(guint16, GUINT16_SWAP_LE_BE((guint16)(gint16)(current_sample * G_MAXINT16)));
      }
    } else {
      current_sample = (float)(current_sample * 0.5 + 0.5);
      if (stream->out_sample_size == 1) {
        OUTPUT_SAMPLE(guint8, current_sample * G_MAXUINT8);
      } else if (!stream->byteswap_needed) {
        OUTPUT_SAMPLE(guint16, current_sample * G_MAXUINT16);
      } else {
        OUTPUT_SAMPLE(guint16, GUINT16_SWAP_LE_BE((guint16)(current_sample * G_MAXUINT16)));
      }
    }

    /* If we're converting mono to stereo, duplicate the sample. */
    if (stream->channels == 1 && stream->out_channels == 2) {
      if (stream->out_sample_size == 1) {
        OUTPUT_SAMPLE(guint8, *(guint8*)(out_buf - sizeof(guint8)));
      } else {
        OUTPUT_SAMPLE(guint16, *(guint16*)(out_buf - sizeof(guint16)));
      }
    }

#undef OUTPUT_SAMPLE

  }

  stream->chunk_start_time = stream->next_read_time;
  stream->next_read_time += (stream->out_speed * obtained_frames) / stream->out_freq;

  return TRUE;
}


static void _mix_stream_channel_finished(int channel)
{
  MixStream* stream;

  g_static_mutex_lock(&chan_table_mutex);
  stream = g_hash_table_lookup(chan_table, &channel);
  g_static_mutex_unlock(&chan_table_mutex);

  if (stream == NULL)
    return;

  if (!_mix_stream_nextchunk(stream, FRAMES_PER_CHUNK)) {
    g_static_mutex_lock(&chan_table_mutex);
    g_hash_table_remove(chan_table, &stream->channel);
    stream->channel = -1;
    g_static_mutex_unlock(&chan_table_mutex);
    return;
  }

  Mix_PlayChannel(channel, &stream->chunk, 0);
  stream->chunk_start_ticks = SDL_GetTicks();
}


/* Begin playing a MixStream from its current position. */
int mix_stream_play(MixStream* stream, int requested_channel)
{
  int real_channel;

  if (stream->channel != -1)
    return -1;

  g_static_mutex_lock(&chan_table_mutex);
  if (chan_table == NULL)
    chan_table = g_hash_table_new_full(g_int_hash, g_int_equal, g_free, NULL);
  g_static_mutex_unlock(&chan_table_mutex);

  _mix_stream_nextchunk(stream, FRAMES_PER_CHUNK);

  /* Sadly we can't call Mix_PlayChannel with the channel table lock held, as
   * we have to take it in the channel-finished callback, which runs with
   * the SDL audio lock held, but Mix_PlayChannel itself takes the SDL audio
   * lock, so we'd risk deadlocking.
   *
   * So if we want SDL_mixer to pick a channel for us, just do it without the
   * lock and deal with the possiblity that the chunk might finish before we
   * record the channel-stream mapping in the channel table.
   */
  Mix_ChannelFinished(_mix_stream_channel_finished);
  if (requested_channel == -1) {
    real_channel = Mix_PlayChannel(-1, &stream->chunk, 0);
    if (real_channel == -1)
      return -1;
  } else {
    real_channel = requested_channel;
  }

  /* Now we know what channel we're on. Put it into the channel table. */
  g_static_mutex_lock(&chan_table_mutex);
  stream->channel = real_channel;
  g_hash_table_insert(chan_table, g_memdup(&stream->channel, sizeof(int)), stream);
  g_static_mutex_unlock(&chan_table_mutex);

  stream->chunk_start_ticks = SDL_GetTicks();
  if (requested_channel == -1)
    return real_channel;
  else
    return Mix_PlayChannel(real_channel, &stream->chunk, 0);
}


/* Check whether a MixStream is playing. */
gboolean mix_stream_is_playing(const MixStream* stream)
{
  gboolean playing;

  /* Between SDL_mixer noticing that a chunk finished playing and when the
   * callback plays the next chunk, the internal variable that Mix_Playing
   * uses gets set to indicate not playing. That whole dance occurs with the
   * SDL audio lock held, so take it when doing this check to prevent false
   * indications that the stream is not playing.
   */
  SDL_LockAudio();
  playing = ((stream->channel != -1) && Mix_Playing(stream->channel));
  SDL_UnlockAudio();
  return playing;
}


/* Stop playing a MixStream. */
void mix_stream_stop(MixStream* stream)
{
  if (stream->channel != -1) {
    /* Unregister the stream so the callback won't do anything more with the stream.
       Again we have the channel table lock/SDL audio lock dilemma...  */
    g_static_mutex_lock(&chan_table_mutex);
    g_hash_table_remove(chan_table, &stream->channel);
    stream->channel = -1;
    g_static_mutex_unlock(&chan_table_mutex);

    Mix_HaltChannel(stream->channel);
    /* It would seem like we should wait on a condition variable here, but
     * it turns out that SDL_mixer calls the channel-finished callback from
     * Mix_HaltChannel. Not that it's good to rely on implementation
     * details like that, but it saves us a lot of extra trouble.
     */
  }
}


/* Set pitch of a MixStream. */
void mix_stream_set_pitch_semitones(MixStream* stream, float semitones)
{
  _mix_stream_soundtouchify(stream);
  g_mutex_lock(stream->st_mutex);
  soundtouch_set_pitch_semitones(stream->soundtouch, semitones);
  g_mutex_unlock(stream->st_mutex);
}


/* Set speed of a MixStream without affecting pitch. */
void mix_stream_set_speed(MixStream* stream, float speed)
{
  _mix_stream_soundtouchify(stream);
  g_mutex_lock(stream->st_mutex);
  soundtouch_set_tempo(stream->soundtouch, speed);
  stream->out_speed = speed;
  g_mutex_unlock(stream->st_mutex);
}


/* Seek to time (in seconds) from the beginning of a MixStream's
 * underlying content and return the new time. Returns a negative
 * value on error or if the content is unseekable.
 */
double mix_stream_seek(MixStream* stream, double time)
{
  double new_time;
  if (stream->seek_cb == NULL)
    return -1.0;
  SDL_LockAudio();
  new_time = stream->seek_cb(time, stream->cb_data);
  g_mutex_lock(stream->st_mutex);
  if (stream->soundtouch != NULL)
    soundtouch_clear(stream->soundtouch);
  stream->eof = FALSE;
  stream->input_eof = FALSE;
  stream->next_read_time = new_time;
  g_mutex_unlock(stream->st_mutex);
  SDL_UnlockAudio();
  return new_time;
}


/* Get current playback position in seconds (with respect to the
 * underlying content!) of a MixStream if this is well-defined for
 * the underlying content. Returns a negative value on error.
 */
double mix_stream_get_position(MixStream* stream)
{
  /* This is one of the more critical functions to be sure we get right, as the
   * notes on screen will be positioned based on whatever this function says.
   */
  double chunk_time;
  double time_since_chunk_start;
  double position;

  if (!mix_stream_is_playing(stream))
    return -1.0;

  SDL_LockAudio();
  chunk_time = (double)FRAMES_PER_CHUNK/(double)stream->out_freq;
  time_since_chunk_start = CLAMP((SDL_GetTicks() - stream->chunk_start_ticks) / 1000.0, 0.0, chunk_time);
  position = stream->chunk_start_time + stream->out_speed * time_since_chunk_start;
  SDL_UnlockAudio();
  return position;
}


/* Get total length in seconds of a MixStream's underlying content.
 * Returns a negative value if this quantity is not defined.
 */
double mix_stream_get_length(MixStream* stream)
{
  double length;
  if (stream->length_cb == NULL)
    return -1.0;
  SDL_LockAudio();
  length = stream->length_cb(stream->cb_data);
  SDL_UnlockAudio();
  return length;
}


/* For GErrors we might return. */
GQuark mix_stream_error_quark(void)
{
  return g_quark_from_static_string("mix-stream-error-quark");
}
