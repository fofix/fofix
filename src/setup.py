#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire X                                                   #
# Copyright (C) 2009-2010 FoFiX Team                                #
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

# FoFiX fully unified setup script
from distutils.core import setup
import sys, glob, os
from FoFiX import SceneFactory, Version

if os.name != 'nt' and sys.platform != 'darwin':
  raise RuntimeError, 'This script is only meaningful for OS X and Windows.'


# Start setting up py2{exe,app} and building the argument set for setup().
# setup() arguments that are not specific to either are near the bottom of
# the script, just before the actual call to setup().
if os.name == 'nt':
  import py2exe
  from py2exe.resources.VersionInfo import RT_VERSION
  from py2exe.resources.VersionInfo import Version as VersionResource
  #stump: sometimes py2.6 py2exe thinks parts of pygame are "system" DLLs...
  __orig_isSystemDLL = py2exe.build_exe.isSystemDLL
  def isSystemDLL(pathname):
    if pathname.lower().find('pygame') != -1:
      return 0
    return __orig_isSystemDLL(pathname)
  py2exe.build_exe.isSystemDLL = isSystemDLL

  setup_args = {
    'zipfile': "data/library.zip",
    'windows': [
      {
        "script":          "FoFiX.py",
        "icon_resources":  [(1, "fofix.ico")],
        "other_resources": [(RT_VERSION, 1, VersionResource(
          #stump: the parameter below must consist only of up to four numerical fields separated by dots
          Version.versionNum(),
          file_description="Frets on Fire X",
          legal_copyright=r"© 2008-2010 FoFiX Team.  GNU GPL v2 or later.",
          company_name="FoFiX Team",
          internal_name="FoFiX.exe",
          original_filename="FoFiX.exe",
          product_name=Version.appNameSexy(),
          #stump: when run from the exe, FoFiX will claim to be "FoFiX v" + product_version
          product_version=Version.version()
        ).resource_bytes())]
      }
    ]
  }
elif sys.platform == 'darwin':
  import py2app
  setup_args = {
    'app': ['FoFiX.py'],
    'data_files': [
      (".", ["../AUTHORS", "../COPYING", "../CREDITS", "../ChangeLog", "../Makefile", "../NEWS", "../README"]),
      ("doc", glob.glob("../doc/*")),
      ("data", glob.glob("../data/*")),
    ],
    #stump: these arguments interfere with the py2exe version tagging code,
    #  so only use them for py2app even though they are standard distutils
    #  arguments.  When they are present, py2exe synthesizes its own version
    #  info resource, superseding the one we specify explicitly above.
    'version': Version.version(),
    'description': "Frets on Fire X",
    'name': "FoFiX",
    'url': "http://code.google.com/p/fofix/",
  }


# Forced includes needed for PIL.
extraIncludes = [
  "PIL.PngImagePlugin",
  "PIL.JpegImagePlugin",
]

# Forced includes needed for pyOpenGL 3 and the accelerator.
import OpenGL
if int(OpenGL.__version__[0]) > 2:
  extraIncludes += [
    "OpenGL.arrays.ctypesarrays",
    "OpenGL.arrays.numpymodule",
    "OpenGL.arrays.lists",
    "OpenGL.arrays.numbers",
    "OpenGL.arrays.strings",  #stump: needed by shader code
  ]
  if os.name == 'nt':
    extraIncludes.append("OpenGL.platform.win32")

  #stump: The pyopengl-accelerator format handlers import this
  # module using the Python/C API, so the packaging tools don't
  # know that it is needed.
  try:
    from OpenGL_accelerate import formathandler
    extraIncludes.append("OpenGL_accelerate.formathandler")
  except ImportError:
    pass

# A couple things we need for pygst under Windows...
extraDllExcludes = []
if os.name == 'nt':
  try:
    # Get the pygst dirs into sys.path if they're there.
    import pygst
    pygst.require('0.10')
    # Skip the DLLs used by pygst; the player code handles them itself.
    extraDllExcludes += [os.path.basename(d) for d in glob.glob(os.path.join('..', 'gstreamer', 'bin', 'libgst*.dll'))]
  except ImportError:
    pass

# Command-specific options shared between py2exe and py2app.
common_options = {
  "dist_dir": "../dist",
  "includes": SceneFactory.scenes + extraIncludes,
  "excludes": [
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
    "PIL.GimpGradientFile",
    "PIL.GimpPaletteFile",
    "PIL.PaletteFile",
    "GimpGradientFile",  #stump: we still need the non-PIL names for these
    "GimpPaletteFile",   # because they get included under these names when
    "PaletteFile",       # excluded above...
    "multiprocessing",
    "Tkinter",
    "Pyrex",
    "distutils",
    "pydoc",
    "py_compile",
    "compiler",
  ]
}

# Copy then specialize the command-specific options.
options = {
  'py2exe': common_options.copy(),
  'py2app': common_options.copy(),
}
options['py2exe'].update({
  "dll_excludes": [
    "msvcp90.dll",
    "mswsock.dll",
    "powrprof.dll",
    "w9xpopen.exe",
    "libgio-2.0-0.dll",
    "libglib-2.0-0.dll",
    "libgmodule-2.0-0.dll",
    "libgobject-2.0-0.dll",
    "libgthread-2.0-0.dll",
  ] + extraDllExcludes,
  "optimize": 2
})
options['py2exe']['excludes'].extend([
  'macosx',
])
options['py2app'].update({
  'argv_emulation': True,
  'iconfile': '../icon_mac_composed.icns',
  'plist': {
    'CFBundleIdentifier': 'org.pythonmac.FoFiX.FretsonFire',
    'CFBundleSignature': 'FoFX',
    'NSHumanReadableCopyright': u"\xa9 2008-2010 FoFiX Team.  GNU GPL v2 or later.",
  }
})

# Add the common arguments to setup().
setup_args.update({
  'options': options,
})

# And finally...
setup(**setup_args)
