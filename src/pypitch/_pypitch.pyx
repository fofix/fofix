# pypitch - analyze audio streams for pitch
# Copyright (C) 2008-2009 John Stumpo
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

cdef extern from "vector":
  ctypedef struct _DoubleVector 'std::vector<double>':
    double (*get 'operator[]' )(int) nogil
    int (*size)() nogil

cdef extern from "pitch.hpp":
  ctypedef struct _Tone 'const Tone':
    double freq
    double db
    double stabledb
    double* harmonics
    int age
  ctypedef struct _Analyzer 'Analyzer':
    void (*process)() nogil
    double (*getPeak)() nogil
    _DoubleVector (*getFormants)() nogil
    _Tone* (*findTone)(double, double) nogil
  _Analyzer* new_Analyzer 'new Analyzer' (double) nogil
  void delete_Analyzer 'delete' (_Analyzer*) nogil

cdef extern from "AnalyzerInput.hpp":
  object feedAnalyzer(_Analyzer*, object)

class Tone:
  def __init__(self, freq, db, stabledb, harmonics, age):
    self.freq = freq
    self.db = db
    self.stabledb = stabledb
    self.harmonics = harmonics
    self.age = age

cdef object PyTone_FromTone(_Tone* t):
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
    self._this = new_Analyzer(rate)
  def __dealloc__(self):
    delete_Analyzer(self._this)
  def input(self, instr):
    if not typecheck(instr, str):
      instr = instr.tostring()  # assume it was a numpy array
    return feedAnalyzer(self._this, instr)
  def process(self):
    self._this.process()
  def getPeak(self):
    return self._this.getPeak()
  def getFormants(self):
    cdef _DoubleVector v
    cdef int i
    cdef double cur
    v = self._this.getFormants()
    formants = []
    for 0 <= i < v.size():
      cur = v.get(i)
      if cur == 0.0:
        formants.append(None)
      else:
        formants.append(cur)
    return formants
  def findTone(self, double minfreq=70.0, double maxfreq=700.0):
    return PyTone_FromTone(self._this.findTone(minfreq, maxfreq))
