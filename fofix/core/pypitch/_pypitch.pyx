# pypitch - analyze audio streams for pitch
# Copyright (C) 2008-2009, 2015 John Stumpo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

__version__ = '$Id$'

from libcpp.vector cimport vector

cdef extern from "pitch.hpp" nogil:
    cdef cppclass _Tone 'Tone':
        double freq
        double db
        double stabledb
        double* harmonics
        int age
    cdef cppclass _Analyzer 'Analyzer':
        _Analyzer(double)
        void input[T](T, T)
        void process()
        double getPeak()
        vector[double] getFormants()
        const _Tone* findTone(double, double)


class Tone:
    def __init__(self, freq, db, stabledb, harmonics, age):
        self.freq = freq
        self.db = db
        self.stabledb = stabledb
        self.harmonics = harmonics
        self.age = age

cdef object PyTone_FromTone(const _Tone* t):
    cdef int i
    if t == NULL:
        return None
    harmonics = []
    for 0 <= i < 8:
        harmonics.append(t.harmonics[i])
    return Tone(t.freq, t.db, t.stabledb, harmonics, t.age)

cdef class Analyzer:
    cdef _Analyzer* _this
    def __cinit__(self, double rate):
        self._this = new _Analyzer(rate)
    def __dealloc__(self):
        del self._this
    def input(self, instr):
        cdef float* begin
        if not isinstance(instr, str):
            instr = instr.tostring()  # assume it was a numpy array
        begin = <float*><char*>instr
        self._this.input(begin, begin + (len(instr) / sizeof(float)))
    def process(self):
        self._this.process()
    def getPeak(self):
        return self._this.getPeak()
    def getFormants(self):
        cdef vector[double] v
        cdef unsigned int i
        cdef double cur
        v = self._this.getFormants()
        formants = []
        for 0 <= i < v.size():
            cur = v[i]
            if cur == 0.0:
                formants.append(None)
            else:
                formants.append(cur)
        return formants
    def findTone(self, double minfreq=65.0, double maxfreq=1000.0):
        return PyTone_FromTone(self._this.findTone(minfreq, maxfreq))
