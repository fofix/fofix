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
  "keyboard.svg",
  "cassette.svg",
  "editor.svg",
  "key.dae",
  "note.dae",
  "cassette.dae",
  "label.dae",
  "library.dae",
  "library_label.dae",
  "crunch1.ogg",
  "crunch2.ogg",
  "crunch3.ogg",
  "out.ogg",
  "start.ogg",
  "in.ogg",
  "star1.svg",
  "star2.svg",
  "glow.svg",
  "ball1.svg",
  "ball2.svg",
  "left.svg",
  "right.svg",
  "fiba1.ogg",
  "fiba2.ogg",
  "fiba3.ogg",
  "fiba4.ogg",
  "fiba5.ogg",
  "fiba6.ogg",
  "neck.svg",
  "pose.svg",
  "logo.svg",
  "menu.ogg",  
  "2x.svg",  
  "3x.svg",  
  "4x.svg",
  "perfect1.ogg",
  "perfect2.ogg",
  "perfect3.ogg",
  "myhero.ogg",
  "jurgen1.ogg",
  "jurgen2.ogg",
  "jurgen3.ogg",
  "jurgen4.ogg",
  "jurgen5.ogg",
  "icon.png",
  "ghmidimap.txt",
  "stage_background.svg",
  "stage_audience1.svg",
  "stage_audience2.svg",
  "stage_drums.svg",
  "stage_bassdrum.svg",
  "stage_light.svg",
  "stage_lights1.svg",
  "stage_lights2.svg",
  "stage_speakers.svg",
  "stage_speaker_cones.svg",
  "stage.ini",
  "loading.svg",
]

chillyModFiles = [
  "mods/Chilly/theme.ini",
  "mods/Chilly/flame1.svg",
  "mods/Chilly/flame2.svg",
  "mods/Chilly/logo.svg",
  "mods/Chilly/neck.svg"
]

lightModFiles = [
  "mods/LightGraphics/stage.ini",
  "mods/LightGraphics/2x.png",
  "mods/LightGraphics/3x.png",
  "mods/LightGraphics/4x.png",
  "mods/LightGraphics/ball1.png",
  "mods/LightGraphics/ball2.png",
  "mods/LightGraphics/cassette.png",
  "mods/LightGraphics/editor.png",
  "mods/LightGraphics/flame1.png",
  "mods/LightGraphics/flame2.png",
  "mods/LightGraphics/glow.png",
  "mods/LightGraphics/keyboard.png",
  "mods/LightGraphics/left.png",
  "mods/LightGraphics/light.png",
  "mods/LightGraphics/loading.png",
  "mods/LightGraphics/logo.png",
  "mods/LightGraphics/neck.png",
  "mods/LightGraphics/pose.png",
  "mods/LightGraphics/right.png",
  "mods/LightGraphics/star1.png",
  "mods/LightGraphics/star2.png",
  "mods/LightGraphics/star.png",
  "mods/LightGraphics/2x.svg",
  "mods/LightGraphics/3x.svg",
  "mods/LightGraphics/4x.svg",
  "mods/LightGraphics/ball1.svg",
  "mods/LightGraphics/ball2.svg",
  "mods/LightGraphics/cassette.svg",
  "mods/LightGraphics/editor.svg",
  "mods/LightGraphics/flame1.svg",
  "mods/LightGraphics/flame2.svg",
  "mods/LightGraphics/glow.svg",
  "mods/LightGraphics/keyboard.svg",
  "mods/LightGraphics/left.svg",
  "mods/LightGraphics/light.svg",
  "mods/LightGraphics/loading.svg",
  "mods/LightGraphics/logo.svg",
  "mods/LightGraphics/neck.svg",
  "mods/LightGraphics/pose.svg",
  "mods/LightGraphics/right.svg",
  "mods/LightGraphics/star1.svg",
  "mods/LightGraphics/star2.svg",
  "mods/LightGraphics/star.svg"
]

dataFiles      = ["../data/" + f for f in dataFiles]
chillyModFiles = ["../data/" + f for f in chillyModFiles]
lightModFiles  = ["../data/" + f for f in lightModFiles]

def songFiles(song, extra = []):
  return ["../data/songs/%s/%s" % (song, f) for f in ["guitar.ogg", "notes.mid", "song.ini", "song.ogg"] + extra]

dataFiles = [
  (".", ["../readme.txt",     "../copying.txt"]),
  ("data",                    dataFiles),
  ("data/songs/defy",         songFiles("defy", ["label.png"])),
  ("data/songs/bangbang",     songFiles("bangbang", ["label.png"])),
  ("data/songs/twibmpg",      songFiles("twibmpg", ["label.png"])),
  ("data/songs/tutorial",     songFiles("tutorial", ["esc.svg", "keyboard.svg", "script.txt", "pose.svg"])),
  ("data/mods/Chilly",        chillyModFiles),
  ("data/mods/LightGraphics", lightModFiles),
  ("data/translations",       glob.glob("../data/translations/*.mo")),
]

if os.name == "nt":
  setup(version = Version.version(),
        description = "Rockin' it Oldskool!",
        name = "Frets on Fire",
        url = "http://www.unrealvoodoo.org",
        windows = [
          {
            "script":          "FretsOnFire.py",
            "icon_resources":  [(1, "../data/icon.ico")]
          }
        ],
        zipfile = "data/library.zip",
        data_files = dataFiles,
        options = options)
else:
  setup(version = Version.version(),
        description = "Rockin' it Oldskool!",
        name = "Frets on Fire",
        url = "http://www.unrealvoodoo.org",
        data_files = dataFiles,
        options = options)

