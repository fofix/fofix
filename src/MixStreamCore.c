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

#define FRAMES_PER_CHUNK 4096

struct _MixStream {
  int samprate;
  int channels;
  mix_stream_read_cb read_cb;
  mix_stream_free_cb free_cb;
  void* cb_data;
  int channel;
  SoundTouch* soundtouch;
  Mix_Chunk chunk;
  gboolean input_eof;
  gboolean eof;
};

static GHashTable* chan_table = NULL;
static GStaticMutex chan_table_mutex = G_STATIC_MUTEX_INIT;


/* Create a stream that will play data returned by read_cb.
 *   - samprate and channels specify the format returned by read_cb
 *   - free_cb is called on data when the stream is destroyed
 *   - data is passed to the callbacks
 */
MixStream* mix_stream_new(int samprate, int channels, mix_stream_read_cb read_cb, mix_stream_free_cb free_cb, void* data, GError** err)
{
  MixStream* stream;

  if (!g_thread_supported())
    g_thread_init(NULL);

  stream = g_new0(MixStream, 1);
  stream->samprate = samprate;
  stream->channels = channels;
  stream->read_cb = read_cb;
  stream->free_cb = free_cb;
  stream->cb_data = data;
  stream->channel = -1;
  stream->chunk.volume = MIX_MAX_VOLUME;
  return stream;
}


/* Free a MixStream. */
void mix_stream_destroy(MixStream* stream)
{
  if (stream->channel != -1)
    mix_stream_stop(stream);
  if (stream->soundtouch != NULL)
    soundtouch_delete(stream->soundtouch);
  stream->free_cb(stream->cb_data);
  g_free(stream);
}


/* Fill a float buffer using a read callback and possibly a SoundTouch object. */
static gsize _mix_stream_fill_floatbuf(MixStream* stream, float* buf, gsize numframes, guint channels)
{
  const gsize frame_size = sizeof(float) * channels;
  gsize frames_obtained = 0;
  gsize frames_read;
  while (numframes > 0) {

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
  int sample_size;
  gboolean samples_signed;
  gboolean byteswap_needed;
  float* floatbuf;
  int out_freq;
  Uint16 out_format;
  int out_channels;
  guint8* out_buf;

  if (stream->eof)
    return FALSE;

  if (stream->chunk.alen < size) {
    stream->chunk.abuf = g_realloc(stream->chunk.abuf, size);
    stream->chunk.alen = size;
  }
  out_buf = stream->chunk.abuf;

  Mix_QuerySpec(&out_freq, &out_format, &out_channels);

  switch (out_format) {
    case AUDIO_S8:     sample_size = 1; samples_signed = TRUE ; byteswap_needed = FALSE; break;
    case AUDIO_U8:     sample_size = 1; samples_signed = FALSE; byteswap_needed = FALSE; break;
#if G_BYTE_ORDER == G_LITTLE_ENDIAN
    case AUDIO_S16LSB: sample_size = 2; samples_signed = TRUE ; byteswap_needed = FALSE; break;
    case AUDIO_U16LSB: sample_size = 2; samples_signed = FALSE; byteswap_needed = FALSE; break;
    case AUDIO_S16MSB: sample_size = 2; samples_signed = TRUE ; byteswap_needed = TRUE ; break;
    case AUDIO_U16MSB: sample_size = 2; samples_signed = FALSE; byteswap_needed = TRUE ; break;
#else
    case AUDIO_S16LSB: sample_size = 2; samples_signed = TRUE ; byteswap_needed = TRUE ; break;
    case AUDIO_U16LSB: sample_size = 2; samples_signed = FALSE; byteswap_needed = TRUE ; break;
    case AUDIO_S16MSB: sample_size = 2; samples_signed = TRUE ; byteswap_needed = FALSE; break;
    case AUDIO_U16MSB: sample_size = 2; samples_signed = FALSE; byteswap_needed = FALSE; break;
#endif
    default: g_assert_not_reached(); break;
  }

  needed_frames = size / (out_channels * sample_size);

  floatbuf = g_newa(float, needed_frames * stream->channels);
  obtained_frames = _mix_stream_fill_floatbuf(stream, floatbuf, needed_frames, stream->channels);
  if (obtained_frames == 0)
    return FALSE;

  while (size > 0) {
    float current_sample = *(floatbuf++);
    /* If we're converting stereo to mono, average this sample with the other channel's. */
    if (stream->channels == 2 && out_channels == 1)
      current_sample = (float)(0.5 * (current_sample + *(floatbuf++)));

#define OUTPUT_SAMPLE(type, value) { *(type*)out_buf = (type)(value); out_buf += sizeof(type); size -= sizeof(type); }

    /* Convert and output the sample. */
    if (samples_signed) {
      if (sample_size == 1) {
        OUTPUT_SAMPLE(gint8, current_sample * G_MAXINT8);
      } else if (!byteswap_needed) {
        OUTPUT_SAMPLE(gint16, current_sample * G_MAXINT16);
      } else {
        OUTPUT_SAMPLE(guint16, GUINT16_SWAP_LE_BE((guint16)(gint16)(current_sample * G_MAXINT16)));
      }
    } else {
      current_sample = (float)(current_sample * 0.5 + 0.5);
      if (sample_size == 1) {
        OUTPUT_SAMPLE(guint8, current_sample * G_MAXUINT8);
      } else if (!byteswap_needed) {
        OUTPUT_SAMPLE(guint16, current_sample * G_MAXUINT16);
      } else {
        OUTPUT_SAMPLE(guint16, GUINT16_SWAP_LE_BE((guint16)(current_sample * G_MAXUINT16)));
      }
    }

    /* If we're converting mono to stereo, duplicate the sample. */
    if (stream->channels == 1 && out_channels == 2) {
      if (sample_size == 1) {
        OUTPUT_SAMPLE(guint8, *(guint8*)(out_buf - sizeof(guint8)));
      } else {
        OUTPUT_SAMPLE(guint16, *(guint16*)(out_buf - sizeof(guint16)));
      }
    }

#undef OUTPUT_SAMPLE

  }

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
    stream->channel = -1;
    return;
  }

  Mix_PlayChannel(channel, &stream->chunk, 0);
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


/* For GErrors we might return. */
GQuark mix_stream_error_quark(void)
{
  return g_quark_from_static_string("mix-stream-error-quark");
}
