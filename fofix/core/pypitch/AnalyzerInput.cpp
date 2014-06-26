/*
 * pypitch - analyze audio streams for pitch
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

/* $Id$ */

#include <Python.h>

#include "AnalyzerInput.hpp"

PyObject* feedAnalyzer(Analyzer* a, PyObject* instr)
{
  float* a_input;

  if (!PyString_Check(instr))
    return PyErr_Format(PyExc_TypeError, "a string is required");

  a_input = (float*)PyString_AsString(instr);
  a->input(a_input, a_input + (PyString_Size(instr) / sizeof(float)));

  Py_RETURN_NONE;
}
