#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire X (FoFiX)                                           #
# Copyright (C) 2011-2012 FoFiX Team                                #
#               2011-2012 John Stumpo                               #
#                                                                   #
# This program is free software; you can redistribute it and/or     #
# modify it under the terms of the GNU General Public License       #
# as published by the Free Software Foundation; either version 2    #
# of the License, or (at your option) any later version.            #
#                                                                   #
# This program is distributed in the hope that it will be useful,   #
# but WITHOUT ANY WARRANTY; without even the implied warranty of    #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the     #
# GNU General Public License for more details.                      #
#                                                                   #
# You should have received a copy of the GNU General Public License #
# along with this program; if not, write to the Free Software       #
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,        #
# MA  02110-1301, USA.                                              #
#####################################################################

# First a thin wrapper around VideoPlayer from VideoPlayerCore.c...

cdef extern from "MixStream.h":
    ctypedef struct CMixStream "MixStream":
        pass

    ctypedef int GQuark
    ctypedef struct GError:
        GQuark domain
        char* message
    GQuark G_FILE_ERROR
    GQuark MIX_STREAM_ERROR
    GQuark MIX_STREAM_OV_ERROR
    void g_error_free(GError*)

    CMixStream* mix_stream_new_vorbisfile(char*, GError**)
    void mix_stream_destroy(CMixStream*)
    int mix_stream_play(CMixStream*, int)
    bint mix_stream_is_playing(CMixStream*)
    void mix_stream_stop(CMixStream*)
    double mix_stream_seek(CMixStream*, double)
    double mix_stream_get_position(CMixStream*)
    double mix_stream_get_length(CMixStream*)
    void mix_stream_set_pitch_semitones(CMixStream*, float)
    void mix_stream_set_speed(CMixStream*, float)


class MixStreamError(Exception):
    pass

class VorbisFileError(Exception):
    pass

cdef object raise_from_gerror(GError* err):
    assert err is not NULL
    if err.domain == MIX_STREAM_ERROR:
        exc = MixStreamError(err.message)
    elif err.domain == MIX_STREAM_OV_ERROR:
        exc = VorbisFileError(err.message)
    elif err.domain == G_FILE_ERROR:
        exc = IOError(err.message)
    else:
        exc = Exception(err.message)
    g_error_free(err)
    raise exc

cdef class VorbisFileMixStream(object):
    cdef CMixStream* stream

    def __cinit__(self, char* filename):
        cdef GError* err = NULL
        self.stream = mix_stream_new_vorbisfile(filename, &err)
        if self.stream is NULL:
            raise_from_gerror(err)

    def __dealloc__(self):
        if self.stream is not NULL:
            mix_stream_destroy(self.stream)

    def play(self, int channel=-1):
        return mix_stream_play(self.stream, channel)

    def is_playing(self):
        return mix_stream_is_playing(self.stream)

    def stop(self):
        mix_stream_stop(self.stream)

    def seek(self, double time):
        return mix_stream_seek(self.stream, time)

    def get_position(self):
        return mix_stream_get_position(self.stream)

    def get_length(self):
        return mix_stream_get_length(self.stream)

    def set_pitch_semitones(self, float semitones):
        mix_stream_set_pitch_semitones(self.stream, semitones)

    def set_speed(self, float speed):
        mix_stream_set_speed(self.stream, speed)
