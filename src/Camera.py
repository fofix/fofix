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

from OpenGL.GLU import *

class Camera:
  def __init__(self):
    # Camera origin vector
    self.origin = (10.0, 0.0, 10.0)
    # Camera target vector
    self.target = (0.0, 0.0, 0.0)
    # Camera up vector
    self.up     = (0.0, 1.0, 0.0)

  def apply(self):
    """Load the camera matrix."""
    gluLookAt(self.origin[0], self.origin[1], self.origin[2],
              self.target[0], self.target[1], self.target[2],
              self.up[0],     self.up[1],     self.up[2])

