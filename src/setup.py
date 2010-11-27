#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-                                        #
#####################################################################
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
from distutils.core import setup, Extension
import distutils.ccompiler
from distutils.dep_util import newer
from Cython.Distutils import build_ext as _build_ext
import sys, SceneFactory, Version, glob, os
import numpy as np
import shlex
import subprocess


# Start setting up py2{exe,app} and building the argument set for setup().
# setup() arguments that are not specific to either are near the bottom of
# the script, just before the actual call to setup().
setup_args = {}
if os.name == 'nt':
  try:
    import py2exe
  except ImportError:
    if 'py2exe' in sys.argv:
      print >>sys.stderr, 'py2exe must be installed to create .exe files.'
      sys.exit(1)
  else:
    from py2exe.resources.VersionInfo import RT_VERSION
    from py2exe.resources.VersionInfo import Version as VersionResource
    #stump: sometimes py2.6 py2exe thinks parts of pygame are "system" DLLs...
    __orig_isSystemDLL = py2exe.build_exe.isSystemDLL
    def isSystemDLL(pathname):
      if pathname.lower().find('pygame') != -1:
        return 0
      return __orig_isSystemDLL(pathname)
    py2exe.build_exe.isSystemDLL = isSystemDLL

    setup_args.update({
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
            product_name=Version.PROGRAM_NAME,
            #stump: when run from the exe, FoFiX will claim to be "FoFiX v" + product_version
            product_version=Version.version()
          ).resource_bytes())]
        }
      ]
    })
elif sys.platform == 'darwin':
  try:
    import py2app
  except ImportError:
    if 'py2app' in sys.argv:
      print >>sys.stderr, 'py2app must be installed to create .app bundles.'
      sys.exit(1)

  setup_args.update({
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
  })


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

extraDllExcludes = []

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


def find_command(cmd):
  '''Find a program on the PATH, or, on win32, in the dependency pack.'''

  print 'checking for program %s...' % cmd,

  if os.name == 'nt':
    # Only accept something from the dependency pack.
    path = os.path.join('..', 'win32', 'deps', 'bin', cmd+'.exe')
  else:
    # Search the PATH.
    path = None
    for dir in os.environ['PATH'].split(os.pathsep):
      if os.access(os.path.join(dir, cmd), os.X_OK):
        path = os.path.join(dir, cmd)
        break

  if path is None or not os.path.isfile(path):
    print 'not found'
    print >>sys.stderr, 'Could not find required program "%s".' % cmd
    if os.name == 'nt':
      print >>sys.stderr, '(Check that you have the latest version of the dependency pack installed.)'
    sys.exit(1)

  print path
  return path


# Find pkg-config so we can find the libraries we need.
pkg_config = find_command('pkg-config')


def pc_exists(pkg):
  '''Check whether pkg-config thinks a library exists.'''
  if os.spawnl(os.P_WAIT, pkg_config, 'pkg-config', '--exists', pkg) == 0:
    return True
  else:
    return False


# {py26hack} - Python 2.7 has subprocess.check_output for this purpose.
def grab_stdout(*args, **kw):
  '''Obtain standard output from a subprocess invocation, raising an exception
  if the subprocess fails.'''

  kw['stdout'] = subprocess.PIPE
  proc = subprocess.Popen(*args, **kw)
  stdout = proc.communicate()[0]
  if proc.returncode != 0:
    raise RuntimeError, 'subprocess %r returned %d' % (args[0], proc.returncode)
  return stdout


def pc_info(pkg):
  '''Obtain build options for a library from pkg-config and
  return a dict that can be expanded into the argument list for
  L{distutils.core.Extension}.'''

  print 'checking for library %s...' % pkg,
  if not pc_exists(pkg):
    print 'not found'
    print >>sys.stderr, 'Could not find required library "%s".' % pkg
    if os.name == 'nt':
      print >>sys.stderr, '(Check that you have the latest version of the dependency pack installed.)'
    else:
      print >>sys.stderr, '(Check that you have the appropriate development package installed.)'
    sys.exit(1)

  cflags = shlex.split(grab_stdout([pkg_config, '--cflags', pkg]))
  libs = shlex.split(grab_stdout([pkg_config, '--libs', pkg]))

  # Pick out anything interesting in the cflags and libs, and
  # silently drop the rest.
  def def_split(x):
    pair = list(x.split('=', 1))
    if len(pair) == 1:
      pair.append(None)
    return tuple(pair)
  info = {
    'define_macros': [def_split(x[2:]) for x in cflags if x[:2] == '-D'],
    'include_dirs': [x[2:] for x in cflags if x[:2] == '-I'],
    'libraries': [x[2:] for x in libs if x[:2] == '-l'],
    'library_dirs': [x[2:] for x in libs if x[:2] == '-L'],
  }

  print 'ok'
  return info


ogg_info = pc_info('ogg')
theoradec_info = pc_info('theoradec')
glib_info = pc_info('glib-2.0')
swscale_info = pc_info('libswscale')
if os.name == 'nt':
  # Windows systems: we just know what the OpenGL library is.
  gl_info = {'libraries': ['opengl32']}
  # And glib needs a slight hack to work correctly.
  glib_info['define_macros'].append(('inline', '__inline'))
else:
  # Other systems: we ask pkg-config.
  gl_info = pc_info('gl')
# Build a similar info record for the numpy headers.
numpy_info = {'include_dirs': [np.get_include()]}


def combine_info(*args):
  '''Combine multiple result dicts from L{pc_info} into one.'''

  info = {
    'define_macros': [],
    'include_dirs': [],
    'libraries': [],
    'library_dirs': [],
  }

  for a in args:
    info['define_macros'].extend(a.get('define_macros', []))
    info['include_dirs'].extend(a.get('include_dirs', []))
    info['libraries'].extend(a.get('libraries', []))
    info['library_dirs'].extend(a.get('library_dirs', []))

  return info


# Extend the build_ext command further to rebuild the import libraries on
# an MSVC build under Windows so they actually work.
class build_ext(_build_ext):
  def run(self, *args, **kw):
    if self.compiler is None:
      self.compiler = distutils.ccompiler.get_default_compiler()
    if self.compiler == 'msvc':
      msvc = distutils.ccompiler.new_compiler(compiler='msvc', verbose=self.verbose, dry_run=self.dry_run, force=self.force)
      msvc.initialize()
      for deffile in glob.glob(os.path.join('..', 'win32', 'deps', 'lib', '*.def')):
        libfile = os.path.splitext(deffile)[0] + '.lib'
        if newer(deffile, libfile):
          msvc.spawn([msvc.lib, '/nologo', '/machine:x86', '/out:'+libfile, '/def:'+deffile])
    return _build_ext.run(self, *args, **kw)

# Add the common arguments to setup().
# This includes arguments to cause FoFiX's extension modules to be built.
setup_args.update({
  'options': options,
  'ext_modules': [
    Extension('cmgl', ['cmgl.pyx'], **combine_info(numpy_info, gl_info)),
    Extension('pypitch._pypitch',
              language='c++',
              sources=['pypitch/_pypitch.pyx', 'pypitch/pitch.cpp',
                       'pypitch/AnalyzerInput.cpp']),
    Extension('VideoPlayer', ['VideoPlayer.pyx', 'VideoPlayerCore.c'],
              **combine_info(gl_info, ogg_info, theoradec_info, glib_info, swscale_info))
  ],
  'cmdclass': {'build_ext': build_ext},
})

# If we're on Windows, add the dependency directory to the PATH so py2exe will
# pick up necessary DLLs from there.
if os.name == 'nt':
  os.environ['PATH'] = os.path.abspath(os.path.join('..', 'win32', 'deps', 'bin')) + os.pathsep + os.environ['PATH']

# And finally...
setup(**setup_args)
