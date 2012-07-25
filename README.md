Frets on Fire X - FoFiX
=======================

This is Frets on Fire X, a highly customizable rhythm game supporting many modes of guitar, bass, drum, and vocal gameplay for up to four players. It is the continuation of a long succession of modifications to the original Frets on Fire by Unreal Voodoo.

Website: http://code.google.com/p/fofix/

Repository (GitHub): http://github.com/fofix/fofix

  $ git clone git://github.com/fofix/fofix.git

How to set yourself up to run from source
=========================================

Table of Contents
-----------------
1. [Checking out the latest code](#Checking-out-the-latest-code)
2. [Notes on Python versions](#Notes-on-Python-versions)
3. [Notes on PyOpenGL versions](#Notes-on-PyOpenGL-versions)
4. [Setting up Python and third-party dependencies](#Setting-up-Python-and-third-party-dependencies)
5. [Compiling the native modules](#Compiling-the-native-modules)
6. [Starting the game](#Starting-the-game)
7. [Making binaries](#Making-binaries)

<a name="Checking-out-the-latest-code"></a>
Checking out the latest code
----------------------------

If you're reading this from the GitHub project view, you might want to
clone the repository so you have your own copy of the latest source files.
Otherwise, you have everything you need and so can skip this section.
_If you go the Git way, remember that some things might be broken or
incomplete at any given time!_

There's a [guide][] to accessing the Git repository and interacting with
other development resources if you don't know how to clone the repository.
There is also the [Google Code wiki page about obtaining the source][gsfg].
  [guide]: http://www.fretsonfire.net/forums/viewtopic.php?f=32&t=47966
  [gsfg]: http://code.google.com/p/fofix/wiki/GettingSourceFromGit?tm=4

_It is highly recommended that when you run from git, you keep a separate
folder containing the latest stable release.  New features and fixes that
become available from git might cause other issues affecting playability._

_Alternatively, you can learn how to rewind the branch you are on to a
state that worked if the latest one breaks on you._

----

<a name="Notes-on-Python-versions"></a>
Notes on Python versions
------------------------

### Anything below 2.6
Support for running FoFiX under Python 2.4 with PyOpenGL 2.x has been
dropped for good.  We warned you for quite a while that support could be
removed at any time.  If you still don't have a 2.6 environment set up,
it's *long* past time to reconstruct your environment using Python 2.6
and PyOpenGL 3.x.

The code now uses Python features that are not compatible with anything
below Python 2.6.

### 2.6
Our current gold standard.  2.6 is currently the lowest Python version
we will maintain compatibility and support for, and most development
takes place on Python 2.6.

### 2.7 and any future 2.x version
2.7 works, though you're on your own installing the dependency packages.
We will actively work toward compatibility with any future 2.x release
that may occur, though the Python developers are unlikely to release
anything beyond the 2.7 series.

### 3.x
We do not support Python 3.x in any way, nor are we likely to for a very
long time.  3.x breaks compatibility with 2.x in many non-trivial ways.

----

<a name="Notes-on-PyOpenGL-versions"></a>
Notes on PyOpenGL versions
--------------------------

### 2.x
Nice and fast but obsolete, needs hacks to work completely right for us,
and won't work on Python 2.5 and up.  Needless to say, we don't use or
support this anymore.

### 3.x
An almost complete rewrite that does everything we need (and then some)
right out of the box.  This is the only series we support.  Unfortunately,
it's written in pure Python with many levels of wrapping, so it's
rather slow.  PyOpenGL-accelerate helps somewhat, but it's not much.
Sometimes we will write our own binding of hard-hit functions in C for
increased speed.

----

<a name="Setting-up-Python-and-third-party-dependencies"></a>
Setting up Python and third-party dependencies
----------------------------------------------

Follow the instructions for your operating system.

### Windows

#### Getting Python
We recommend that Windows users use **32-bit Python 2.6**.  The
instructions below are written in terms of 32-bit Python 2.6.  (It can
be difficult to find or build packages for Python 2.7 and 64-bit Python
under Windows.)

First, you will need Python itself.  Go to [the Python download page][]
and select the most recent 2.6.x release.  The most recent 2.6.x at the
time of this writing is 2.6.6 ([direct link][py2.6.6-win32]).  Again,
_32-bit is recommended, even if you have a 64-bit system._  Install
by double-clicking the .msi file, and be sure to remember which folder
you install Python to, as you will need to know for the next step.
(If you use default settings, Python should end up in: `C:\Python26`)

  [the Python download page]: http://www.python.org/download/
  [py2.6.6-win32]: http://python.org/ftp/python/2.6.6/python-2.6.6.msi

#### Adding Python to the PATH
You will need to add the Python installation folder to the PATH.
Open the Start menu, right-click on "Computer" ("My Computer" before
Windows Vista), and choose Properties.  Go to the Advanced tab, then
click Environment Variables.  Under System Variables, find where the
variable "`PATH`" (or "`Path`") is set, and double-click it to edit it.
Add a semicolon (`;`) to the end of the existing value, then type the
folder name in after the semicolon.  Click OK in each window until you
are out of System Properties.

#### Downloading and installing third-party dependencies

You will now need to download and install the necessary third-party
dependency modules.  Versions are the most recent available at the time
of this writing.  You may wish to check the project websites for more
recent releases.  If you do not use the links here, or if you are not
using 32-bit Python 2.6, be sure you get packages appropriate for your
Python installation.

The following packages are required:

  * PyWin32 ([direct link to build 216](http://sourceforge.net/projects/pywin32/files/pywin32/Build216/pywin32-216.win32-py2.6.exe))
  * numpy ([direct link to 1.5.0](http://download.sourceforge.net/numpy/numpy-1.5.0-win32-superpack-python2.6.exe))
  * pygame ([direct link to 1.9.1](http://pygame.org/ftp/pygame-1.9.1.win32-py2.6.msi))
  * PyOpenGL ([direct link to 3.0.1](http://pypi.python.org/packages/any/P/PyOpenGL/PyOpenGL-3.0.1.win32.exe))
  * Python Imaging Library ([direct link to 1.1.7+](http://github.com/downloads/fuzion/pil-2009-raclette/PIL-1.1.7-2009-raclette-r358.win32-py2.6.exe))
  * Cython ([link to 0.14.1](http://www.lfd.uci.edu/~gohlke/pythonlibs/#cython))

The following packages are optional:

  * pyopengl-accelerate ([direct link to 3.0.1-r365](http://github.com/downloads/fuzion/pil-2009-raclette/PyOpenGL-accelerate-3.0.1-r365.win32-py2.6.exe))

    This will make PyOpenGL go a good bit faster. _Highly recommended!_

  * py2exe ([direct link to 0.6.9](http://downloads.sourceforge.net/py2exe/py2exe-0.6.9.win32-py2.6.exe))

    This allows you to freeze the code into standalone EXEs for
    distribution.  There's no advantage at all to doing so unless you're
    going to be distributing binaries.

  * pitchbend ([direct link to 0.3-EndOfLife](http://www.mediafire.com/file/zlinjzzj0km/pitchbend-0.3-EndOfLife.win32-py2.6.exe))

    This provides rudimentary, badly-implemented support for a
    whammy pitchbend effect.  It will be replaced with a much better
    implementation soon.

  * pyaudio ([direct link to 0.2.4](http://people.csail.mit.edu/hubert/pyaudio/packages/pyaudio-0.2.4.py26.exe))

    This provides support for microphone input, which is required for
    vocal play.

Install all packages by double-clicking the .exe or .msi files that
you downloaded.

#### Installing the Win32 Dependency Pack

Some code in FoFiX depends on external libraries written in C. The
`win32/` directory contains build scripts, but it can be difficult to
get the proper environment set up to use them.

Since building and setting up these libraries can be difficult, we are
making available a prebuilt archive of everything you need to compile
FoFiX's native modules. Download the latest FoFiX Win32 Dependency Pack
from [here](http://www.mediafire.com/?x0000ohmctblb) and unzip it into the
`win32/` directory. (The `deps/` directory in the archive should become
a subdirectory of the `win32/` directory.) Now you are ready to compile
the native modules.


### Mac OS X

Someone with a Mac will have to expand this section.


### GNU/Linux

#### Notes about distributions
The following instructions are generic and should work on most GNU/Linux
distributions.  We have added many specific notes about Debian and Ubuntu
since those are the most popular distributions, but that does not mean
that FoFiX won't work on other distributions.

*Note:* On many distributions (including Debian and Ubuntu), in all
places where the Python interpreter is called or a Python package name
is mentioned, `python` can be replaced by a specific version, _e.g._
`python2.6`. Remember that if you do it once, you'll have to do it
everywhere.

_If we do not mention your distribution here and you have helpful tips
for getting FoFiX to work, please come into IRC and tell us about it.
Or file a bug telling us about your procedure._

#### Installing required packages
The following are required:

  * Python (tested with 2.6 on Ubuntu Karmic and Lucid)
  * pygame (at least version 1.9 is required if you want MIDI instrument input or you're on x86_64)
  * PyOpenGL (3.x)
  * numpy
  * Python Imaging Library (PIL)
  * Numeric (only required if you have a pygame version earlier than 1.9)
  * Python's development headers
  * A C++ compiler
  * Cython
  * pkg-config
  * The OpenGL, GLU, GLib, SDL, SDL_mixer, libogg, libvorbisfile,
    libtheora, and libswscale (part of ffmpeg) development headers

The following are optional (refer to the Windows instructions to see
what each one is needed for):

  * pitchbend
  * pyaudio

For those of you on Debian or Ubuntu, this means installing the
following packages: `python-pygame`, `python-opengl`, `python-numpy`,
`python-imaging`, `python-dev`, `build-essential`, `cython`, `pkg-config`,
`libgl1-mesa-dev`, `libglu1-mesa-dev`, `libglib2.0-dev`, `libsdl1.2-dev`,
`libsdl-mixer1.2-dev`, `libogg-dev`, `libvorbisfile-dev`, `libtheora-dev`,
`libswscale-dev`.  If you're stuck without pygame 1.9, also install
`python-numeric`.

Some packages can be troublesome, so we have notes below about certain
packages.

*Note:* If you end up custom-building any packages, it is not strictly
necessary to install them system-wide.  You can instead use the PYTHONPATH
environment variable when starting FoFiX to allow Python to find them.
For example:

    export PYTHONPATH=~/pygame-1.9.1release/build/lib.linux-x86_64-2.6:~/pyaudio/build/lib.linux-x86_64-2.6
    python FoFiX.py

#### About pygame 1.9.x
If your distribution has pygame 1.9.x in its repositories, then there
you are.

If you're running Debian, you will find that there is no pygame 1.9.x
package (not even in sid).  Manually downloading and installing the
appropriate package [from Ubuntu][ubu python-pygame] should do the trick.
  [ubu python-pygame]: http://packages.ubuntu.com/lucid/python-pygame

Those with other distributions can manually download and build the latest
pygame release.

    wget -c http://www.pygame.org/ftp/pygame-1.9.1release.tar.gz
    tar zxvf pygame-1.9.1release.tar.gz
    cd pygame-1.9.1release/
    python setup.py build

It can be installed system-wide with (as root):

    python setup.py install

#### About pyaudio
Debian and Ubuntu don't have it in their repositories, but a package is
available [here](http://people.csail.mit.edu/hubert/pyaudio/#packages)
if you're using Python 2.6.

Other distributions that lack pyaudio can find the source for it elsewhere
on that page.

#### About pitchbend
We're going to be getting rid of it soon, its quality leaves a lot to
be desired, and its dependency libraries can be troublesome or might
not be packaged for your distribution.  Our advice is not to bother
with pitchbend.

If you want to try it anyway, make sure you have the SDL_mixer
and libsndobj development headers (under Debian and Ubuntu,
`libsdl-mixer1.2-dev` and `libsndobj-dev`) and type:

    git clone git://git.jstump.com/git/pitchbend.git
    cd pitchbend
    python setup.py build

It can be installed system-wide with (as root):

    python setup.py install

----
<a name="Compiling-the-native-modules"></a>
Compiling the native modules
----------------------------

Some parts of FoFiX are written in C or C++.  These must be compiled
before you can start the game from source.

Make sure that you have a C compiler installed (see below if you don't
have one), then open a command prompt, use the `cd` command to navigate
to the `src` directory in the source tree, then type

    python setup.py build_ext --inplace --force

You will have to do this **every time** you receive changes to a `.c`,
`.cpp`, `.h`, `.hpp`, or `.pyx` file after an update.  Otherwise you
are in danger of weird crashes, and our first question will probably be
whether or not you rebuilt the native modules.

(If `setup.py` complains about any programs or libraries being missing,
check that you have installed all of the dependencies, and for Windows
users, that the Win32 Dependency Pack is unpacked in the proper location.)

As for making sure you have a compiler, read the section for your
operating system.

### Windows

Install Microsoft Visual C++ 2008 Express Edition
by going [to the Visual Studio Express download
page](http://www.microsoft.com/express/Downloads/), clicking "Visual
Studio 2008 Express", and clicking "Visual C++ 2008 Express Edition".
(If you happen to have one of the paid versions of MSVC 2008, that
will work just fine too.)  You don't have to bother registering it, as
you won't be using the GUI, which is the only place where registration
is enforced.

Versions other than 2008 _will not work_.  Native modules for Python
programs must be compiled with the same version of Visual C++ that was
used to compile Python, and the official Python 2.6 and 2.7 releases were
built with Visual C++ 2008.  (Don't worry if you have other versions of
any Visual Studio components installed - they can peacefully coexist.)

### Mac OS X

Install Xcode.  Someone with a Mac will have to expand this section.

### GNU/Linux

Install the appropriate package from your distribution's repository.

Under Debian and Ubuntu, you want `build-essential`.


----
<a name="Starting-the-game"></a>
Starting the game
-----------------

Open a command prompt and navigate to the `src` directory in your source
tree using the `cd` command.  Then type

    python FoFiX.py

The game will start from source.

Alternatively, if you're running Windows, you can merely double-click
`src/scripts/RunFofFromSources.bat` to run the game.

----
<a name="Making-binaries"></a>
Making binaries
---------------

Follow the instructions for your operating system.

_Unofficial binaries are completely unsupported and will warn the user
accordingly when they are started._

### Windows

If you installed py2exe, you can freeze the code into an EXE by
double-clicking `src/scripts/RebuildWin.bat`.

Be aware that whether you are running from source or EXE has negligible
impact on performance except while the game is just starting up, and even
then there is practically no difference.  This means that there really
is no point in creating the EXE unless you are going to distribute FoFiX
to others.

### Mac OS X

The `setup.py` is py2app-aware.  Someone with a Mac will have to expand
this section.

### GNU/Linux

We don't support GNU/Linux binaries anymore.  Just run from source for
now; we'll make the standard `python setup.py install` do the right
thing sooner or later (certainly before 4.0 is released).

