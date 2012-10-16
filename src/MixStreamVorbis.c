/* Frets on Fire X (FoFiX)
 * Copyright (C) 2012 FoFiX Team
 *               2012 John Stumpo
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
#include <vorbis/vorbisfile.h>
#include <errno.h>


/* strerror-like function for libvorbis{,file} error codes
 * ...would be nice if libvorbis itself had something like this...
 */
static const char* vf_strerror(int vf_err)
{
  switch (vf_err) {
    case 0: return "Success";
    case OV_EREAD: return "Read error";
    case OV_EFAULT: return "Internal fault in libvorbis";
    case OV_EIMPL: return "Feature not implemented";
    case OV_EINVAL: return "Invalid argument within libvorbis";
    case OV_ENOTVORBIS: return "Not Ogg Vorbis";
    case OV_EBADHEADER: return "Bad file header";
    case OV_EVERSION: return "Unsupported format revision";
    case OV_EBADLINK: return "Undecodable link";
    case OV_ENOSEEK: return "Stream is not seekable";
    default: return "General failure";
  }
}


/* Read callback for a libvorbisfile-backed stream. */
static gsize vf_read_cb(float* buf, gsize bufsize, void* data)
{
  OggVorbis_File* vf = data;
  int channels = ov_info(vf, -1)->channels;
  int samples = bufsize / (channels * sizeof(float));
  float** pcm;
  int streamno;
  int i, j;

  /* Decode the samples. */
  samples = ov_read_float(vf, &pcm, samples, &streamno);
  if (samples < 0) {
    g_warning("Error in vorbisfile read callback: %s", vf_strerror(samples));
    return 0;
  }

  /* Copy the samples into the buffer. */
  for (i = 0; i < samples; i++)
    for (j = 0; j < channels; j++)
      *(buf++) = pcm[j][i];

  return samples * channels * sizeof(float);
}


/* Free callback for a libvorbisfile-backed stream. */
static void vf_free_cb(void* data)
{
  ov_clear((OggVorbis_File*)data);
  g_free(data);
}


/* Create a MixStream that plays Ogg Vorbis audio from the given file name. */
MixStream* mix_stream_new_vorbisfile(const char* filename, GError** err)
{
  MixStream* stream;
  OggVorbis_File* vf = g_new(OggVorbis_File, 1);
  int vf_err;
  vorbis_info* vi;

  errno = 0;
  if ((vf_err = ov_fopen(filename, vf)) != 0) {
    if (errno != 0)
      g_set_error(err, G_FILE_ERROR, g_file_error_from_errno(errno),
        "Failed to open file: %s", g_strerror(errno));
    else
      g_set_error(err, MIX_STREAM_OV_ERROR, vf_err,
        "Failed to initialize decoder: %s", vf_strerror(vf_err));
    g_free(vf);
    return NULL;
  }

  vi = ov_info(vf, -1);

  stream = mix_stream_new(vi->rate, vi->channels, vf_read_cb, vf_free_cb, vf, err);
  if (stream == NULL) {
    ov_clear(vf);
    g_free(vf);
    return NULL;
  }
  return stream;
}


/* For GErrors we might return. */
GQuark mix_stream_ov_error_quark(void)
{
  return g_quark_from_static_string("mix-stream-ov-error-quark");
}
