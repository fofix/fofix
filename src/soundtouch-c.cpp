/* soundtouch-c: A C shim around most of the SoundTouch audio processor.
 * Copyright (C) 2011 John Stumpo
 *
 * This program is covered by the same license as the SoundTouch library
 * itself, namely (as of this writing) the GNU Lesser General Public
 * License, version 2.1 or (at your option) any later version.  See the
 * license of the SoundTouch library for more information.
 */

#include "soundtouch-c.h"
#include <SoundTouch.h>
#include <new>
#include <glib.h>

extern "C"
{

SoundTouch* soundtouch_new(void)
{
  // The reason we do a g_malloc and placement new here is so this
  // object doesn't depend on anything C++-related beyond symbols from
  // SoundTouch. This allows us to link it with MSVC tools on Windows and
  // successfully bridge to the MinGW-compiled SoundTouch DLL.
  //
  // If SoundTouch itself wants to include this, it can just do ordinary
  // new and delete here and in soundtouch_delete, as the constraint on
  // linked-to symbols then no longer applies.
  return new(g_malloc(sizeof(SoundTouch))) SoundTouch();
}

void soundtouch_delete(SoundTouch* st)
{
  // See comment in soundtouch_new().
  st->~SoundTouch();
  g_free(st);
}

const char* soundtouch_get_version_string(void)
{
  return SoundTouch::getVersionString();
}

unsigned int soundtouch_get_version_id(void)
{
  return SoundTouch::getVersionId();
}

void soundtouch_set_rate(SoundTouch* st, float rate)
{
  st->setRate(rate);
}

void soundtouch_set_tempo(SoundTouch* st, float tempo)
{
  st->setTempo(tempo);
}

void soundtouch_set_rate_change(SoundTouch* st, float rate)
{
  st->setRateChange(rate);
}

void soundtouch_set_tempo_change(SoundTouch* st, float tempo)
{
  st->setTempoChange(tempo);
}

void soundtouch_set_pitch(SoundTouch* st, float pitch)
{
  st->setPitch(pitch);
}

void soundtouch_set_pitch_octaves(SoundTouch* st, float pitch)
{
  st->setPitchOctaves(pitch);
}

void soundtouch_set_pitch_semitones(SoundTouch* st, float pitch)
{
  st->setPitchSemiTones(pitch);
}

void soundtouch_set_channels(SoundTouch* st, unsigned int channels)
{
  st->setChannels(channels);
}

void soundtouch_set_sample_rate(SoundTouch* st, unsigned int rate)
{
  st->setSampleRate(rate);
}

void soundtouch_flush(SoundTouch* st)
{
  st->flush();
}

void soundtouch_put_samples(SoundTouch* st, const float* input_buffer, unsigned int num_samples)
{
  st->putSamples(input_buffer, num_samples);
}

void soundtouch_clear(SoundTouch* st)
{
  st->clear();
}

unsigned int soundtouch_num_unprocessed_samples(const SoundTouch* st)
{
  return st->numUnprocessedSamples();
}

unsigned int soundtouch_receive_samples(SoundTouch* st, float* output_buffer, unsigned int num_samples)
{
  return st->receiveSamples(output_buffer, num_samples);
}

unsigned int soundtouch_num_samples(const SoundTouch* st)
{
  return st->numSamples();
}

int soundtouch_is_empty(const SoundTouch* st)
{
  return st->isEmpty();
}

} /* extern "C" */
