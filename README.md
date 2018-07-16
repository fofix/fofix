Frets on Fire X - FoFiX
=======================

[![Code Health](https://landscape.io/github/fofix/fofix/master/landscape.svg?style=flat)](https://landscape.io/github/fofix/fofix/master)
[![Build Status](https://travis-ci.org/fofix/fofix.svg?branch=master)](https://travis-ci.org/fofix/fofix)
[![Documentation Status](https://readthedocs.org/projects/fofix/badge/?version=latest)](https://fofix.readthedocs.io/en/latest/?badge=latest)
[![Gitter](https://badges.gitter.im/fofix/fofix.svg)](https://gitter.im/fofix/fofix?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=body_badge)


This is Frets on Fire X, a highly customizable rhythm game supporting many modes of guitar, bass, drum, and vocal gameplay for up to four players. It is the continuation of a long succession of modifications to the original Frets on Fire by Unreal Voodoo.

- repository: https://github.com/fofix/fofix
- IRC: #fofix on oftc.net ([web interface](https://webchat.oftc.net/))
- Gitter: [web interface](https://gitter.im/fofix/fofix)
- unofficial forum: https://www.fretsonfire.org/forums/viewforum.php?f=32


Setup
-----

### Dependencies

First, you will need **Python 2.7**.

Python dependencies: run `pip install -r requirements.txt`.

Optional dependencies:

- `pyopengl-accelerate`: this will make PyOpenGL go a good bit faster
- `pyaudio`: this provides support for microphone input, which is required for vocal play
- `gettext`: for translations

OS-specific dependencies:

- Windows:
    - Only 32bit Python is supported
    - [pyWin32](https://sourceforge.net/projects/pywin32/files/pywin32/)
    - [win32 dependency pack](https://www.dropbox.com/s/p8xv4pktq670q9i/fofix-win32-deppack-20130304-updated.zip?dl=0) (to unzip into the `win32` directory)

- Unix:
    - a C++ compiler
    - `OpenGL`
    - `ffmpeg`
    - `pkg-config`
    - python's developpment headers
    - and: `GLU`, `GLib`, `SDL`, `SDL_mixer`, `libogg`, `libvorbisfile`, `libtheora`, `libsoundtouch`, `libswscale` (part of `ffmpeg`) development headers

    About `cerealizer`, you need to reinstall it. You can run those commands for
    example:

        pip download cerealizer
        tar jxf Cerealizer*.tar.bz2 -C /tmp/
        cd /tmp/Cerealizer-*
        pip install --upgrade .
        cd -
        rm -r /tmp/Cerealizer-* Cerealizer-*


### Native modules

Some parts of FoFiX are written in C or C++. These must be compiled
before you can start the game from source:

    python setup.py build_ext --inplace --force


Start the game
--------------

    python FoFiX.py
