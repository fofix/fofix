#!/usr/bin/env python
# -*- coding: utf-8 -*-
#####################################################################
#                                                                   #
# Frets on Fire X                                                   #
# Copyright (C) 2009-2018 FoFiX Team                                #
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
import distutils.ccompiler
from distutils.dep_util import newer
from distutils.command.install import install as _install
import sys, glob, os, fnmatch
import subprocess
import shlex

import numpy

from fofix.core import Version, SceneFactory

from setuptools import setup, Extension, Command
from Cython.Build import cythonize


def glob_recursive(directory, file_pattern="*"):
    """ Like glob, but recurses sub-dirs.
    :param directory: directory from which to start searching
    :param file_pattern: (default '*')
        optional name pattern for desired files. Used to filter files at
        every level; NOT used to filter directories.
    :return: list(str) of path to every file found.
    """
    matches = []
    for subdir, dirnames, filenames in os.walk(directory):
        for filename in fnmatch.filter(filenames, file_pattern):
            matches.append(os.path.join(subdir, filename))
    return matches

def to_data_files(target, top, files):
    """ Convert plain list of files to something data_files would like.
    Each file's location will be computed relative to 'top'; the resulting sub-path
    will be the location under 'target' where py2exe will place the file.
    The result is effectively a set of directories inside of 'target'
    that reproduce the structure of directories inside 'top'.
    This lets you move a set of files from any location in your source tree
    into any location in the distro.

    :param target: str - relative path inside of py2exe distro where files shall go
    :param top: str - absolute (or relative to system current) path to remove from each of the paths in 'files'
    :param files: list(str) of file paths to process
    :return: list( (str, list(str)) ) - the structure required by py2exe.options.data_files
    """
    outs = {}
    # normalize top
    top = os.path.normpath(os.path.abspath(top))
    for f in files:
        # normalize each file
        f = os.path.normpath(os.path.abspath(f))
        # compute path relative to 'top'
        rel = os.path.relpath(os.path.dirname(f), top)
        subtarg = os.path.join(target, rel)
        # save file under corresponding relative path
        lst = outs.get(subtarg)
        if not lst:
            lst = list()
            outs[subtarg] = lst
        lst.append(f)
    return [(k,outs[k]) for k in sorted(outs.keys())]


# Hack to fix "No such file or directory: 'numpy-atlas.dll'".
# https://stackoverflow.com/questions/36191770/py2exe-errno-2-no-such-file-or-directory-numpy-atlas-dll
if os.name == 'nt':
    paths = set()
    np_path = numpy.__path__[0]
    for dirpath, _, filenames in os.walk(np_path):
        for item in filenames:
            if item.endswith('.dll'):
                paths.add(dirpath)
    sys.path.append(*list(paths))
#--end hack


data_files = [
    (".", ["./AUTHORS", "./COPYING", "./CREDITS", "./CHANGELOG"]),
    #("doc", glob.glob("./doc/*")), #TODO run Makefile to build this first
]
data_files.extend( to_data_files("data", "./data", glob_recursive("./data")) )


# Start setting up py2{exe,app} and building the argument set for setup().
# setup() arguments that are not specific to either are near the bottom of
# the script, just before the actual call to setup().
setup_args = {}
if os.name == 'nt':
    try:
        import py2exe
    except ImportError:
        if 'py2exe' in sys.argv:
            sys.stderr.write('py2exe must be installed to create .exe files.\n')
            sys.exit(1)
    else:
        from py2exe.resources.VersionInfo import RT_VERSION
        from py2exe.resources.VersionInfo import Version as VersionResource
        # sometimes py2.6 py2exe thinks parts of pygame are "system" DLLs...
        __orig_isSystemDLL = py2exe.build_exe.isSystemDLL
        def isSystemDLL(pathname):
            exclude = ['pygame', 'libogg']
            for dll in exclude:
                if pathname.lower().find(dll) != -1:
                    return 0
            return __orig_isSystemDLL(pathname)
        py2exe.build_exe.isSystemDLL = isSystemDLL

        setup_args.update({
            'zipfile': "data/library.zip",
            'windows': [
                {
                    "script":          "FoFiX.py",
                    "icon_resources":  [(1, "./win32/fofix.ico")],
                    "other_resources": [(RT_VERSION, 1, VersionResource(
                        # the parameter below must consist only of up to four numerical fields separated by dots
                        Version.versionNum(),
                        file_description="Frets on Fire X",
                        legal_copyright=r"© 2008-2013 FoFiX Team.  GNU GPL v2 or later.",
                        company_name="FoFiX Team",
                        internal_name="FoFiX.exe",
                        original_filename="FoFiX.exe",
                        product_name=Version.PROGRAM_NAME,
                        # when run from the exe, FoFiX will claim to be "FoFiX v" + product_version
                        product_version=Version.version()
                        ).resource_bytes())]
                }
            ],
            'data_files': data_files
        })
elif sys.platform == 'darwin':
    try:
        import py2app
    except ImportError:
        if 'py2app' in sys.argv:
            sys.stderr.write('py2app must be installed to create .app bundles.\n')
            sys.exit(1)

    setup_args.update({
      'app': ['FoFiX.py'],
      'data_files': [
        (".", ["./AUTHORS", "./COPYING", "./CREDITS", "./CHANGELOG", "./makefile", "./README.md"]),
        ("doc", glob.glob("./doc/*")),
        ("data", glob.glob("./data/*")),
      ],
      # these arguments interfere with the py2exe version tagging code,
      # so only use them for py2app even though they are standard distutils
      # arguments.  When they are present, py2exe synthesizes its own version
      # info resource, superseding the one we specify explicitly above.
      'version': Version.version(),
      'description': "Frets on Fire X",
      'name': "FoFiX",
      'url': "https://github.com/fofix/fofix",
    })


# Forced includes needed for PIL.
extraIncludes = [
  "PIL.PngImagePlugin",
  "PIL.JpegImagePlugin",
  "PIL.GimpPaletteFile",
  "PIL.GimpGradientFile",
  "PIL.PaletteFile"
]

# Forced includes needed for pyOpenGL 3 and the accelerator.
import OpenGL
if int(OpenGL.__version__[0]) > 2:
    extraIncludes += [
      "OpenGL.arrays.ctypesarrays",
      "OpenGL.arrays.numpymodule",
      "OpenGL.arrays.lists",
      "OpenGL.arrays.numbers",
      "OpenGL.arrays.strings",  # needed by shader code
      "OpenGL.arrays.ctypesparameters",
    ]
    if os.name == 'nt':
        extraIncludes.append("OpenGL.platform.win32")

    # The pyopengl-accelerator format handlers import this
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
  "dist_dir": "./dist",
  "includes": SceneFactory.scenes + extraIncludes,
  "excludes": [
    "ode",
    "_ssl",
    "bz2",
    "email",
    "calendar",
    "doctest",
    "ftplib",
    "getpass",
    "gopherlib",
    "macpath",
    "macurl2path",
    "PIL.GimpGradientFile",
    "PIL.GimpPaletteFile",
    "PIL.PaletteFile",
    "GimpGradientFile",  # we still need the non-PIL names for these
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
  'iconfile': './icon_mac_composed.icns',
  'plist': {
    'CFBundleIdentifier': 'org.pythonmac.FoFiX.FretsonFire',
    'CFBundleSignature': 'FoFX',
    'NSHumanReadableCopyright': u"\xa9 2008-2013 FoFiX Team.  GNU GPL v2 or later.",
  }
})


def find_command(cmd):
    '''Find a program on the PATH, or, on win32, in the dependency pack.'''

    sys.stdout.write('checking for program %s... ' % cmd)

    if os.name == 'nt':
        # Only accept something from the dependency pack.
        path = os.path.join('.', 'win32', 'deps', 'bin', cmd+'.exe')
    else:
        # Search the PATH.
        path = None
        for dir in os.environ['PATH'].split(os.pathsep):
            if os.access(os.path.join(dir, cmd), os.X_OK):
                path = os.path.join(dir, cmd)
                break

    if path is None or not os.path.isfile(path):
        print('not found')
        sys.stderr.write('Could not find required program "%s".\n' % cmd)
        if os.name == 'nt':
            sys.stderr.write('(Check that you have the latest version of the dependency pack installed.)\n')
        sys.exit(1)

    print(path)
    return path


# Find pkg-config so we can find the libraries we need.
pkg_config = find_command('pkg-config')


def pc_exists(pkg):
    '''Check whether pkg-config thinks a library exists.'''
    if os.spawnl(os.P_WAIT, pkg_config, 'pkg-config', '--exists', pkg) == 0:
        return True
    else:
        return False


# Blacklist MinGW-specific dependency libraries on Windows.
if os.name == 'nt':
    lib_blacklist = ['m', 'mingw32']
else:
    lib_blacklist = []


def pc_info(pkg, altnames=[]):
    '''Obtain build options for a library from pkg-config and
    return a dict that can be expanded into the argument list for
    L{distutils.core.Extension}.'''

    sys.stdout.write('checking for library %s... ' % pkg)
    if not pc_exists(pkg):
        for name in altnames:
            if pc_exists(name):
                pkg = name
                sys.stdout.write('(using alternative name %s) ' % pkg)
                break
        else:
            print('not found')
            sys.stderr.write('Could not find required library "%s".\n' % pkg)
            sys.stderr.write('(Also tried the following alternative names: %s)\n' % ', '.join(altnames))
            if os.name == 'nt':
                sys.stderr.write('(Check that you have the latest version of the dependency pack installed.)\n')
            else:
                sys.stderr.write('(Check that you have the appropriate development package installed.)\n')
            sys.exit(1)

    cflags = shlex.split(subprocess.check_output([pkg_config, '--cflags', pkg]).decode())
    libs = shlex.split(subprocess.check_output([pkg_config, '--libs', pkg]).decode())

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
      'libraries': [x[2:] for x in libs if x[:2] == '-l' and x[2:] not in lib_blacklist],
      'library_dirs': [x[2:] for x in libs if x[:2] == '-L'],
    }

    print('ok')
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
    try:
        gl_info = pc_info('gl')
    except SystemExit:
        # Work around to include opengl.framwork during compilation on OSX.
        os.environ['LDFLAGS'] = '-framework opengl'
        os.environ['CFLAGS'] = '-framework opengl'
        gl_info = {
          'define_macros': [],
          'include_dirs': [],
          'libraries': [],
          'library_dirs': [],
        }
# Build a similar info record for the numpy headers.
numpy_info = {'include_dirs': [numpy.get_include()]}


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

# Make "setup.py install" do nothing until we configure something more sensible.
class install(_install):
    def run(self, *args, **kw):
        sys.stderr.write('This is not the correct way to install FoFiX.\n')
        sys.exit(1)


# Convert .po files into .mo files.
class msgfmt(Command):
    user_options = []
    description = 'convert .po files in data/po into .mo files in data/translations'

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        msgfmt_cmd = find_command('msgfmt')
        for pofile in glob.glob(os.path.join('data', 'po', '*.po')):
            mofile = os.path.join('data', 'translations', os.path.basename(pofile)[:-3] + '.mo')
            if newer(pofile, mofile):
                self.mkpath(os.path.dirname(mofile))
                self.spawn([msgfmt_cmd, '-c', '-o', mofile, pofile])


# Extract translatable strings.
class xgettext(Command):
    user_options = []
    description = 'extract translatable strings from source code'

    # The function names that indicate a translatable string.
    FUNCNAMES = ['_', 'N_']

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        py_files = glob_recursive('.', '*.py')
        xgettext_cmd = find_command('xgettext')
        potfile = os.path.join('data', 'po', 'messages.pot')
        self.spawn([xgettext_cmd,
          '--package-name=' + Version.PROGRAM_NAME,
          '--package-version=' + Version.version(),
          '--copyright-holder=FoFiX Team',
          ' --sort-output',
          '-o', potfile] +
          ['-k' + funcname for funcname in self.FUNCNAMES] +
          py_files)


if os.name == 'nt':
    vidInclude = ['.', 'win32/deps/include/msinttypes']
else:
    vidInclude = ['.']

extensions = [
    Extension('fofix.lib.cmgl', ['fofix/core/cmgl/cmgl.pyx'], **combine_info(numpy_info, gl_info)),
    Extension('fofix.lib._pypitch',
              language='c++',
              sources=['fofix/core/pypitch/_pypitch.pyx', 'fofix/core/pypitch/pitch.cpp']),
    Extension('fofix.lib._VideoPlayer',
              ['fofix/core/VideoPlayer/_VideoPlayer.pyx', 'fofix/core/VideoPlayer/VideoPlayer.c'],
              **combine_info(gl_info, ogg_info, theoradec_info, glib_info, swscale_info,
              {'include_dirs': vidInclude}))
]

# Add the common arguments to setup().
# This includes arguments to cause FoFiX's extension modules to be built.
setup_args.update({
  'options': options,
  'ext_modules': cythonize(extensions),
  'cmdclass': {'install': install, 'msgfmt': msgfmt, 'xgettext': xgettext},
})

# If we're on Windows, add the dependency directory to the PATH so py2exe will
# pick up necessary DLLs from there.
if os.name == 'nt':
    os.environ['PATH'] = os.path.abspath(os.path.join('.', 'win32', 'deps', 'bin')) + os.pathsep + os.environ['PATH']

# And finally...
setup(**setup_args)
