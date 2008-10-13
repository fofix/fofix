#!/usr/bin/python
#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire                                                     #
# Copyright (C) 2006 Sami Kyöstilä                                  #
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

"""Run all unit tests."""

import sys
import os
import unittest

tests = []

for root, dirs, files in os.walk("."):
  for f in files:
    f = os.path.join(root, f)
    if f.endswith("Test.py"):
      m = os.path.basename(f).replace(".py", "")
      d = os.path.dirname(f)
      sys.path.append(d)
      tests.append(__import__(m))

suite = unittest.TestSuite()

if "-i" in sys.argv:
  suffix = "TestInteractive"
else:
  suffix = "Test"

for test in tests:
  for item in dir(test):
    if item.endswith(suffix):
      suite.addTest(unittest.makeSuite(test.__dict__[item]))
  
unittest.TextTestRunner(verbosity = 2).run(suite)
