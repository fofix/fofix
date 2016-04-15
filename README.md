[![Code Health](https://landscape.io/github/fofix/fofix/master/landscape.svg?style=flat)](https://landscape.io/github/fofix/fofix/master) [![Gitter](https://badges.gitter.im/fofix/fofix.svg)](https://gitter.im/fofix/fofix?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=body_badge)


Frets on Fire X - FoFiX
=======================

This is Frets on Fire X, a highly customizable rhythm game supporting many modes of guitar, bass, drum, and vocal gameplay for up to four players. It is the continuation of a long succession of modifications to the original Frets on Fire by Unreal Voodoo.

Repository (GitHub): http://github.com/fofix/fofix

  $ git clone git://github.com/fofix/fofix.git

Chat with us on IRC: #fofix on oftc.net  ([web interface](https://webchat.oftc.net/))

Chat with us on [Gitter](https://gitter.im/fofix/fofix)


How to set yourself up to run from source
=========================================

Table of Contents
-----------------
1. [Checking out the latest code](#Checking-out-the-latest-code)
2. [Notes on Python versions](#Notes-on-Python-versions)
4. [Setting up Python and third-party dependencies](#Setting-up-Python-and-third-party-dependencies)
5. [Compiling the native modules](#Compiling-the-native-modules)
6. [Building the translations](#Building-the-translations)
7. [Starting the game](#Starting-the-game)
8. [Making binaries](#Making-binaries)

<a name="Checking-out-the-latest-code"></a>
Checking out the latest code
----------------------------

If you're reading this from the GitHub project view, you might want to
clone the repository so you have your own copy of the latest source files.
Otherwise, you have everything you need and so can skip this section.
_If you go the Git way, remember that some things might be broken or
incomplete at any given time!_

To clone this repository you can use the following git command:
`git clone https://github.com/fofix/fofix.git`

There's also [guide][] to accessing the Git repository and interacting with
other development resources..
  [guide]: http://www.fretsonfire.net/forums/viewtopic.php?f=32&t=47966

_As a warning when running from git, you will want to keep a separate
folder containing the latest stable release.  New features and fixes that
become available from git might cause other issues affecting playability._

----

<a name="Notes-on-Python-versions"></a>
Notes on Python versions
------------------------
Python 2.7 is currently the lowest version we support. Anything below that has been dropped.

We do not currently support Python 3.x but we have been slowly preparing for the transition.  3.x breaks compatibility with 2.x in many non-trivial ways. Therfor we have a lot of work before we can make the jump. Fretwork will likely get full python 3 support first, and then the games. 

----

<a name="Setting-up-Python-and-third-party-dependencies"></a>
Setting up Python and third-party dependencies
----------------------------------------------

Follow the instructions for your operating system.

*Note* We are in the process of switching to using virtualenv, so these
instructions will change.

### Windows

#### Getting Python
We recommend that Windows users use **32-bit Python 2.7**.  The
instructions below are written in terms of 32-bit Python 2.7.

First, you will need Python itself.  Go to [the Python download page][]
and select the most recent 2.7.x release.  The most recent 2.7.x at the
time of this writing is 2.7.10 ([direct link][py2.7.10-win32]).  Again,
_32-bit is recommended, even if you have a 64-bit system._  Install
by double-clicking the .msi file, and be sure to remember which folder
you install Python to, as you will need to know for the next step.
(If you use default settings, Python should end up in: `C:\Python26`)

  [the Python download page]: https://www.python.org/downloads/
  [py2.7.10-win32]: https://www.python.org/ftp/python/2.7.10/python-2.7.10.msi

#### Adding Python to the PATH

The python installer can automatically add python to the PATH variable,
if the "Add python.exe to Path" option is selected in the install. If
this was not selected during installation, follow the following guide.

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
using 32-bit Python 2.7, be sure you get packages appropriate for your
Python installation.

The following packages are required:

  * PyWin32 ([direct link to build 219](http://sourceforge.net/projects/pywin32/files/pywin32/Build%20219/pywin32-219.win32-py2.7.exe))
  * numpy ([direct link to 1.9.2](http://sourceforge.net/projects/numpy/files/NumPy/1.9.2/numpy-1.9.2-win32-superpack-python2.7.exe))
  * pygame ([direct link to 1.9.1](http://pygame.org/ftp/pygame-1.9.1.win32-py2.7.msi))
  * PyOpenGL ([direct link to 3.0.1](https://pypi.python.org/packages/any/P/PyOpenGL/PyOpenGL-3.1.0.win32.exe#md5=f175505f4f9e21c8c5c6adc794296d81))
  * Pillow ([direct link to 2.9.0](https://pypi.python.org/packages/2.7/P/Pillow/Pillow-2.9.0.win32-py2.7.exe#md5=2a2d5d447e03d1231cfb7700b6806912))
  * Cython ([link to 0.23](http://www.lfd.uci.edu/~gohlke/pythonlibs/#cython))

    This is a Python Wheel, after downloading install it using pip:

    ```pip install Cython‑0.23‑cp27‑none‑win32.whl```

The following packages are optional:

  * pyopengl-accelerate ([direct link to 3.1.0](https://pypi.python.org/packages/2.7/P/PyOpenGL-accelerate/PyOpenGL-accelerate-3.1.0.win32-py2.7.exe#md5=911efd7965928ec9168e7f8a6cf35537))

    This will make PyOpenGL go a good bit faster. _Highly recommended!_

  * py2exe ([direct link to 0.9.2.2](https://pypi.python.org/packages/any/p/py2exe/py2exe-0.9.2.2.win32.exe#md5=f1684d39de2ed8287a0a36eb241f81e5))

    This allows you to freeze the code into standalone EXEs for
    distribution.  There's no advantage at all to doing so unless you're
    going to be distributing binaries.

  * pyaudio ([direct link to 0.2.8](https://people.csail.mit.edu/hubert/pyaudio/packages/pyaudio-0.2.8.py27.exe))

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
from [here](https://dl.dropboxusercontent.com/u/37405488/fofix-win32-deppack-20130304-updated.zip) and unzip it into the
`win32/` directory. (The `deps/` directory in the archive should become
a subdirectory of the `win32/` directory.) Now you are ready to compile
the native modules.


#### Installing fretwork
Fretwork is our new initiative to share some code with a fork of FoF called Frets on Fire: Reborn.
Some code from this repo has been move out into fretwork. To install fretwork download the following wheel: ([direct link to 0.1.1](https://github.com/fofix/fretwork/releases/download/0.1.1/fretwork-0.1.1-cp27-none-win32.whl))
Then install it using the following command:
```pip install fretwork-0.1.1-cp27-none-win32.whl```

#### Upgrading fretwork
If you have previously installed fretwork make sure you download the latest release from above then following command:

```pip install fretwork-0.1.1-cp27-none-win32.whl --upgrade```


### Mac OS X

This section will be expanded soon, but as it stands it is only possible to run from sources on osx. Packaging is broken.


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
  * Python Imaging Library (PIL) or Pillow
  * Python's development headers
  * A C++ compiler
  * Cython
  * pkg-config
  * cerealizer
  * fretwork
  * The OpenGL, GLU, GLib, SDL, SDL_mixer, libogg, libvorbisfile,
    libtheora, libsoundtouch, and libswscale (part of ffmpeg) development headers

The following are optional (refer to the Windows instructions to see
what each one is needed for):

  * pyaudio
  * the GNU gettext tools (for translations)

For those of you on Debian or Ubuntu, this means installing the
following packages: `python-pygame`, `python-opengl`, `python-numpy`,
`python-imaging`, `python-dev`, `build-essential`, `cython`, `pkg-config`,
`libgl1-mesa-dev`, `libglu1-mesa-dev`, `libglib2.0-dev`, `libsdl1.2-dev`,
`libsdl-mixer1.2-dev`, `libogg-dev`, `libvorbisfile-dev`, `libtheora-dev`,
`libswscale-dev`, `libsoundtouch-dev`, and if you want translations, `gettext`.

Cerealizer should be installed via pip

For Fretwork you should download the sourcecode of the latest release ([over here](https://github.com/fofix/fretwork/releases/)), extract the files and run the following command:

```pip2 install fretwork-0.1.1.tar.gz```

This command may depend on how your distribution provides pip, and what python versions you have installed.


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

Install Microsoft Visual C++ Compiler for Python 2.7
by going [here](http://www.microsoft.com/en-us/download/details.aspx?id=44266).
(If you happen to have any version of MSVC 2008, that
will work just fine too.)

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
<a name="Building-the-translations"></a>
Building the translations
-------------------------

_This part is optional._

FoFiX's interface can appear in languages other than English. If you
want to try other languages, you must have the GNU gettext tools
available. (They are included in the Win32 Dependency Pack; under
Debian-like systems, install the `gettext` package.) Then open a command
prompt, navigate to the `src` directory in your source tree using the
`cd` command, and type

    python setup.py msgfmt

to build the translations. Many are incomplete or outdated; improvements
would be greatly appreciated. (We will write a more detailed guide on
translating soon.)

If you make or receive changes to a `.po` file for a translation you are
using, be sure to do this step again to make the game use the modified
version.

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
