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

# Keyboard Hero setup script
from distutils.core import setup
import sys, SceneFactory, Version, glob, os

try:
  import py2exe
  from py2exe.resources.VersionInfo import RT_VERSION
  from py2exe.resources.VersionInfo import Version as VersionResource
except ImportError:
  pass

options = {
  "py2exe": {
    "dist_dir":  "../dist",
    "includes":  SceneFactory.scenes,
    "excludes":  [
      "glew.gl.apple",
      "glew.gl.ati",
      "glew.gl.atix",
      "glew.gl.hp",
      "glew.gl.ibm",
      "glew.gl.ingr",
      "glew.gl.intel",
      "glew.gl.ktx",
      "glew.gl.mesa",
      "glew.gl.oml",
      "glew.gl.pgi",
      "glew.gl.rend",
      "glew.gl.s3",
      "glew.gl.sgi",
      "glew.gl.sgis",
      "glew.gl.sgix",
      "glew.gl.sun",
      "glew.gl.sunx",
      "glew.gl.threedfx",
      "glew.gl.win",
      "ode",
      "_ssl",
      "bz2",
      "email",
      "calendar",
      "bisect",
      "difflib",
      "doctest",
      "ftplib",
      "getpass",
      "gopherlib",
      "heapq",
      "macpath",
      "macurl2path",
      "GimpGradientFile",
      "GimpPaletteFile",
      "PaletteFile",
      "macosx",
    ],
    "optimize":  2,
  }
}

dataFiles = [
  "default.ttf",
  "title.ttf",
  "international.ttf",
  "key.dae",
  "note.dae",
  "cassette.dae",
  "label.dae",
  "library.dae",
  "library_label.dae",
  "glow.png",
]


dataFiles      = ["../data/" + f for f in dataFiles]

def songFiles(song, extra = []):
  return ["../data/songs/%s/%s" % (song, f) for f in ["guitar.ogg", "notes.mid", "song.ini", "song.ogg"] + extra]

dataFiles = [
  ("data",                    dataFiles),
  ("data/translations",       glob.glob("../data/translations/*.mo")),
]

#stump: grab version info from engine
import GameEngine
fullVersionString = GameEngine.version

def setupWindows():
  setup(version = Version.version(),
        description = "Rockin' it Oldskool!",
        name = "Frets on Fire",
        url = "http://www.unrealvoodoo.org",
        windows = [
          {
            "script":          "FretsOnFire.py",
            "icon_resources":  [(1, "fof.ico")],
            "other_resources": [(RT_VERSION, 1, VersionResource(
              #stump: the parameter below must consist only of up to four numerical fields separated by dots
              fullVersionString[7:12],  # extract "x.yyy" from "FoFiX vx.yyy ..."
              file_description="Frets on Fire X",
              legal_copyright=r"© 2008-2009 FoFiX Team.  GNU GPL v2 or later.",
              company_name="FoFiX Team",
              internal_name="FretsOnFire.exe",
              original_filename="FretsOnFire.exe",
              product_name="FoFiX",
              #stump: when run from the exe, FoFiX will claim to be "FoFiX v" + product_version
              product_version=fullVersionString[7:]  # remove "FoFiX v" from front
            ).resource_bytes())]
          }
        ],
        zipfile = "data/library.zip",
        data_files = dataFiles,
        options = options)
