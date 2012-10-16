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

#ifndef MIXSTREAM_H
#define MIXSTREAM_H

#include <glib.h>

typedef struct _MixStream MixStream;

typedef gsize(*mix_stream_read_cb)(float* buf, gsize bufsize, void* data);
typedef void(*mix_stream_free_cb)(void* data);
MixStream* mix_stream_new(int samprate, int channels, mix_stream_read_cb read_cb, mix_stream_free_cb free_cb, void* data, GError** err);
MixStream* mix_stream_new_vorbisfile(const char* filename, GError** err);
void mix_stream_destroy(MixStream* stream);

int mix_stream_play(MixStream* stream, int channel);
gboolean mix_stream_is_playing(const MixStream* stream);
void mix_stream_stop(MixStream* stream);

void mix_stream_set_pitch_semitones(MixStream* stream, float semitones);

GQuark mix_stream_error_quark(void);
#define MIX_STREAM_ERROR mix_stream_error_quark()
GQuark mix_stream_ov_error_quark(void);
#define MIX_STREAM_OV_ERROR mix_stream_ov_error_quark()

typedef enum {
  MIX_STREAM_MIXER_UNINIT
} MixStreamError;

#endif
