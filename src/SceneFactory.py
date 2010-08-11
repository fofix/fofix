#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire X (FoFiX)                                           #
# Copyright (C) 2006 Sami Kyöstilä                                  #
#               2009 FoFiX Team                                     #
#               2009 akedrou                                        #
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

# Scenes
import glob

scenes = [n.replace(".py", "") for n in glob.glob("*Scene.py")]

def _import(name):
  globals()[name] = __import__(name)

def create(engine, name, **args):

  _import(name)

  m = globals()[name]
  return getattr(m, name)(engine = engine, **args)
