Installation
============

From a package
---------------

Here is a list of some packages available for Unix distributions.

.. image https://repology.org/badge/vertical-allrepos/fofix.svg
    :target: https://repology.org/metapackage/fofix
    :alt: Packaging status


From sources
-------------

- Get the `latest release <https://github.com/fofix/fofix/releases/latest>`_ or `sources <https://github.com/fofix/fofix>`_
- install dependencies:
    - OS specific dependencies:
        - `Windows`_
        - `Unix`_
    - Python dependencies: ``pip install -r requirements.txt``
    - optional dependencies:
        - ``pyopengl-accelerate``: this will make PyOpenGL go a good bit faster
        - ``pyaudio``: this provides support for microphone input, which is required for vocal play
        - ``gettext``: for translations
- compile native modules::

    python setup.py build_ext --inplace --force


Windows
+++++++

Install the following dependencies:
    - ``pyWin32``
    - `win32 dependency pack <https://dl.dropboxusercontent.com/u/37405488/fofix-win32-deppack-20130304-updated.zip>`_ (to unzip into the ``win32`` directory)


Unix
++++

Install the following dependencies:
    -  a C++ compiler
    - ``Python`` 2.7
    - ``OpenGL``
    - ``ffmpeg``
    - ``pkg-config``
    - python's developpment headers
    - and: ``GLU``, ``GLib``, ``SDL``, ``SDL_mixer``, ``libogg``, ``libvorbisfile``, ``libtheora``, ``libsoundtouch``, ``libswscale`` (part of ``ffmpeg``) development headers
