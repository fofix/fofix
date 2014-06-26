/* soundtouch-c: A C shim around most of the SoundTouch audio processor.
 * Copyright (C) 2011 John Stumpo
 *
 * This program is covered by the same license as the SoundTouch library
 * itself, namely (as of this writing) the GNU Lesser General Public
 * License, version 2.1 or (at your option) any later version.  See the
 * license of the SoundTouch library for more information.
 */

#ifndef SOUNDTOUCH_C_H
#define SOUNDTOUCH_C_H

#ifdef __cplusplus
namespace soundtouch { struct SoundTouch; }
using soundtouch::SoundTouch;
extern "C" {
#else
typedef struct SoundTouch SoundTouch;
#endif

SoundTouch* soundtouch_new(void);
void soundtouch_delete(SoundTouch*);

const char* soundtouch_get_version_string(void);
unsigned int soundtouch_get_version_id(void);

void soundtouch_set_rate(SoundTouch*, float);
void soundtouch_set_tempo(SoundTouch*, float);
void soundtouch_set_rate_change(SoundTouch*, float);
void soundtouch_set_tempo_change(SoundTouch*, float);

void soundtouch_set_pitch(SoundTouch*, float);
void soundtouch_set_pitch_octaves(SoundTouch*, float);
void soundtouch_set_pitch_semitones(SoundTouch*, float);

void soundtouch_set_channels(SoundTouch*, unsigned int);
void soundtouch_set_sample_rate(SoundTouch*, unsigned int);

void soundtouch_flush(SoundTouch*);
void soundtouch_put_samples(SoundTouch*, const float*, unsigned int);
void soundtouch_clear(SoundTouch*);
unsigned int soundtouch_num_unprocessed_samples(const SoundTouch*);
unsigned int soundtouch_receive_samples(SoundTouch*, float*, unsigned int);
unsigned int soundtouch_num_samples(const SoundTouch*);
int soundtouch_is_empty(const SoundTouch*);

#ifdef __cplusplus
}
#endif

#endif
