#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire X                                                   #
# Copyright (C) 2009 FoFiX Team                                     #
#               2006 Sami Kyöstilä                                  #
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

#stump: Start building a list of forced includes.
extraIncludes = [
  "PIL.PngImagePlugin",
  "PIL.JpegImagePlugin",
]

#stump: if we're running pyOpenGL 3, do the necessary black magic.
import OpenGL
import pygame
if int(OpenGL.__version__[0]) > 2:
  extraIncludes += [
    "OpenGL.platform.win32",
    "OpenGL.arrays.ctypesarrays",
    "OpenGL.arrays.numpymodule",
    "OpenGL.arrays.lists",
    "OpenGL.arrays.numbers",
    "OpenGL.arrays.strings",  #stump: needed by shader code
  ]

#stump: The pyopengl-accelerator format handlers import this
# module using the Python/C API, so py2exe doesn't know that
# it is needed.
try:
  from OpenGL_accelerate import formathandler
  extraIncludes.append("OpenGL_accelerate.formathandler")
except ImportError:
  pass

options = {
  "py2exe": {
    "dist_dir":  "../dist",
    "includes":  SceneFactory.scenes + extraIncludes,
    "excludes":  [
      "ode",
      "_ssl",
      "bz2",
      "email",
      "calendar",
      "difflib",
      "doctest",
      "ftplib",
      "getpass",
      "gopherlib",
      "macpath",
      "macurl2path",
      "multiprocessing",
      "PIL.GimpGradientFile",
      "PIL.GimpPaletteFile",
      "PIL.PaletteFile",
      "GimpGradientFile",  #stump: we still need the non-PIL names for these
      "GimpPaletteFile",   # because they get included under these names when
      "PaletteFile",       # excluded above...
      "macosx",
      "Tkinter",
      "Pyrex",
      "distutils",
      "pydoc",
      "py_compile",
      "compiler",
    ],
    "dll_excludes":  [
      "msvcp90.dll",
      "mswsock.dll",
      "powrprof.dll"
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

#stump: sometimes py2.6 py2exe thinks parts of pygame are "system" DLLs...
__orig_isSystemDLL = py2exe.build_exe.isSystemDLL
def isSystemDLL(pathname):
  if pathname.lower().find('pygame') != -1:
    return 0
  return __orig_isSystemDLL(pathname)
py2exe.build_exe.isSystemDLL = isSystemDLL

#evilynux: Grab version info from Version class
def setupWindows():
  setup(#stump: these arguments interfere with the version tagging code,
        #  but they don't really do anything important anyway.  When the
        #  version tagging code was modified, they suddenly became a valid
        #  source of info for py2exe to synthesize a version info resource
        #  of its own, which supersedes the one specified further down.
        #version = Version.VERSION,
        #description = "Rockin' it Oldskool!",
        #name = Version.appNameSexy(),
        #url = Version.URL,
        windows = [
          {
            "script":          "FoFiX.py",
            "icon_resources":  [(1, "fofix.ico")],
            "other_resources": [(RT_VERSION, 1, VersionResource(
              #stump: the parameter below must consist only of up to four numerical fields separated by dots
              Version.versionNum(),
              file_description="Frets on Fire X",
              legal_copyright=r"© 2008-2009 FoFiX Team.  GNU GPL v2 or later.",
              company_name="FoFiX Team",
              internal_name="FoFiX.exe",
              original_filename="FoFiX.exe",
              product_name=Version.appNameSexy(),
              #stump: when run from the exe, FoFiX will claim to be "FoFiX v" + product_version
              product_version=Version.version()
            ).resource_bytes())]
          }
        ],
        zipfile = "data/library.zip",
        data_files = dataFiles,
        options = options)
