#!/bin/sh -e
# Script to cross-compile FoFiX's dependency libraries for Win32.
#   (Derived from a similar script I wrote for Performous.)
# Copyright (C) 2010 John Stumpo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

die () { echo "$@" >&2 ; exit 1 ; }

assert_binary_on_path () {
  if which "$1" >/dev/null 2>&1; then
    echo found program "$1"
  else
    echo did not find "$1", which is required
    exit 1
  fi
}

if test -z "$CROSS_TOOL_PREFIX"; then
  export CROSS_TOOL_PREFIX=i686-w64-mingw32
fi
echo "Using cross compilers prefixed with '$CROSS_TOOL_PREFIX-'."
echo "(Set CROSS_TOOL_PREFIX to change this; don't include the trailing hyphen.)"
if test -z "$CROSS_GCC"; then
  assert_binary_on_path "$CROSS_TOOL_PREFIX"-gcc
  export CROSS_GCC="$CROSS_TOOL_PREFIX"-gcc
  assert_binary_on_path "$CROSS_TOOL_PREFIX"-g++
  export CROSS_GXX="$CROSS_TOOL_PREFIX"-g++
  assert_binary_on_path "$CROSS_TOOL_PREFIX"-ar
  export CROSS_AR="$CROSS_TOOL_PREFIX"-ar
  assert_binary_on_path "$CROSS_TOOL_PREFIX"-ranlib
  export CROSS_RANLIB="$CROSS_TOOL_PREFIX"-ranlib
  assert_binary_on_path "$CROSS_TOOL_PREFIX"-ld
  export CROSS_LD="$CROSS_TOOL_PREFIX"-ld
  assert_binary_on_path "$CROSS_TOOL_PREFIX"-dlltool
  export CROSS_DLLTOOL="$CROSS_TOOL_PREFIX"-dlltool
  assert_binary_on_path "$CROSS_TOOL_PREFIX"-nm
  export CROSS_NM="$CROSS_TOOL_PREFIX"-nm
  assert_binary_on_path "$CROSS_TOOL_PREFIX"-windres
  export CROSS_WINDRES="$CROSS_TOOL_PREFIX"-windres
fi
if test -z "$WINE"; then
  assert_binary_on_path wine
  export WINE=wine
fi
echo "wine: $WINE"

assert_binary_on_path autoreconf
assert_binary_on_path bzip2
assert_binary_on_path gzip
assert_binary_on_path libtoolize
assert_binary_on_path make
assert_binary_on_path patch
assert_binary_on_path pkg-config
assert_binary_on_path python
assert_binary_on_path tar
assert_binary_on_path unzip
assert_binary_on_path wget
assert_binary_on_path xz
assert_binary_on_path yasm

SCRIPTDIR="`pwd`"
export PREFIX="`pwd`"/deps
export WINEPREFIX="`pwd`"/wine
mkdir -pv "$PREFIX"/bin "$PREFIX"/lib "$PREFIX"/include "$PREFIX"/lib/pkgconfig "$PREFIX"/build-stamps
if test -n "$KEEPTEMP"; then
  RM_RF=true
  echo 'Keeping the built source trees, as you requested.'
else
  RM_RF="rm -rf"
  echo 'Unpacked source trees will be removed after compilation.'
  echo '(Set KEEPTEMP to any value to preserve them.)'
fi

echo 'setting up wine environment'
$WINE reg add 'HKCU\Environment' /v PATH /d Z:"`echo "$PREFIX" | tr '/' '\\'`"\\bin

echo 'creating pkg-config wrapper for cross-compiled environment'
cat >"$PREFIX"/bin/pkg-config <<EOF
#!/bin/sh -e
exec env PKG_CONFIG_LIBDIR='$PREFIX'/lib/pkgconfig '`which pkg-config`' "\$@"
EOF
chmod -v 0755 "$PREFIX"/bin/pkg-config
cat >"$PREFIX"/bin/wine-shwrap <<"EOF"
#!/bin/sh -e
path="`(cd $(dirname "$1") && pwd)`/`basename "$1"`"
echo '#!/bin/bash -e' >"$1"
echo '$WINE '"$path"'.exe "$@" | tr -d '"'\\\015'" >>"$1"
echo 'exit ${PIPESTATUS[0]}' >>"$1"
chmod 0755 "$1"
EOF
chmod 0755 $PREFIX/bin/wine-shwrap

echo 'creating compiler wrappers'
cat >"$PREFIX"/bin/"$CROSS_GCC" <<"EOF"
#!/usr/bin/python
import sys, os
STATIC_LIBS = ['-lstdc++', '-lgcc', '-lgcc_eh']
def fixed_args(args):
    for n, arg in enumerate(args):
        if arg in STATIC_LIBS:
            yield '-Wl,-Bstatic'
        yield arg
        if arg in STATIC_LIBS:
            yield '-Wl,--exclude-libs,lib%s.a,-Bdynamic' % arg[2:]
        if n == 0:
            yield '-static-libgcc'
            yield '-static-libstdc++'
for p in os.environ['PATH'].split(os.pathsep):
    candidate = os.path.join(p, os.path.basename(__file__))
    if os.access(candidate, os.X_OK) and not os.path.samefile(candidate, __file__):
        os.execv(candidate, list(fixed_args(sys.argv)))
EOF
chmod -v 0755 "$PREFIX"/bin/"$CROSS_GCC"
ln -svf "$CROSS_GCC" "$PREFIX"/bin/"$CROSS_GXX"

export PATH="$PREFIX"/bin:"$PATH"

download () {
  basename="`basename "$1"`"
  if test ! -f "$basename"; then
    wget -c -O "$basename".part "$1"
    mv -v "$basename".part "$basename"
  fi
  test -f "$PREFIX"/URLs && cp -f "$PREFIX"/URLs "$PREFIX"/URLs.new
  echo "$1" >>"$PREFIX"/URLs.new
  sort "$PREFIX"/URLs.new | uniq >"$PREFIX"/URLs
  rm -f "$PREFIX"/URLs.new
}

# We use win-iconv instead of full-fledged GNU libiconv because it still does
# everything the other deps need and is far smaller.
WINICONV="win-iconv-0.0.4"
if test ! -f "$PREFIX"/build-stamps/win-iconv; then
  download http://win-iconv.googlecode.com/files/$WINICONV.tar.bz2
  tar jxvf $WINICONV.tar.bz2
  cd $WINICONV
  make CC="$CROSS_GCC" iconv.dll
  cp -v iconv.dll "$PREFIX"/bin
  cp -v iconv.h "$PREFIX"/include
  echo '' >>"$PREFIX"/include/iconv.h  # squelch warnings about no newline at the end
  sed -i -e 's://.*$::' "$PREFIX"/include/iconv.h  # squelch warnings about C++ comments
  cp -v libiconv.dll.a "$PREFIX"/lib
  cd ..
  touch "$PREFIX"/build-stamps/win-iconv
  $RM_RF $WINICONV
fi

# zlib
ZLIB="zlib-1.2.7"
if test ! -f "$PREFIX"/build-stamps/zlib; then
  download http://www.zlib.net/$ZLIB.tar.bz2
  tar jxvf $ZLIB.tar.bz2
  cd $ZLIB
  make -f win32/Makefile.gcc PREFIX="$CROSS_TOOL_PREFIX"- zlib1.dll
  cp -v zlib.h zconf.h "$PREFIX"/include
  cp -v zlib1.dll "$PREFIX"/bin
  cp -v libz.dll.a "$PREFIX"/lib
  cd ..
  touch "$PREFIX"/build-stamps/zlib
  $RM_RF $ZLIB
fi

# Flags passed to every dependency's ./configure script, for those deps that use autoconf and friends.
COMMON_AUTOCONF_FLAGS="--prefix=$PREFIX --host=$CROSS_TOOL_PREFIX --disable-static --enable-shared CPPFLAGS=-I$PREFIX/include LDFLAGS=-L$PREFIX/lib"

# Runtime (libintl) of GNU Gettext
# We build the rest later, after certain libraries are in place, to save
# space as the tools can link to those libraries rather than use gettext's
# internal copy. But some of those libs use libintl themselves, so...
GETTEXT="gettext-0.18.1.1"
if test ! -f "$PREFIX"/build-stamps/gettext-runtime; then
  download http://ftp.gnu.org/gnu/gettext/$GETTEXT.tar.gz
  tar zxvf $GETTEXT.tar.gz
  cd $GETTEXT/gettext-runtime
  ./configure $COMMON_AUTOCONF_FLAGS --enable-relocatable --disable-libasprintf --disable-java --disable-csharp
  make
  make install
  cd ../..
  touch "$PREFIX"/build-stamps/gettext-runtime
  $RM_RF $GETTEXT
fi

# We don't really need this, but GObject requires it.
# Not that we're using GObject or anything, but glib's configure script
# refuses to run without it and this is the path of least resistance.
LIBFFI="libffi-3.0.11"
if test ! -f "$PREFIX"/build-stamps/libffi; then
  download ftp://sourceware.org/pub/libffi/$LIBFFI.tar.gz
  tar zxvf $LIBFFI.tar.gz
  cd $LIBFFI
  ./configure $COMMON_AUTOCONF_FLAGS --enable-portable-binary
  make
  make install
  cd ..
  touch "$PREFIX"/build-stamps/libffi
  $RM_RF $LIBFFI
fi

# GLib
GLIB="glib-2.32.4"
if test ! -f "$PREFIX"/build-stamps/glib; then
  download http://ftp.gnome.org/pub/GNOME/sources/glib/2.32/$GLIB.tar.xz
  tar Jxvf $GLIB.tar.xz
  cd $GLIB
  ./configure $COMMON_AUTOCONF_FLAGS
  make -C glib
  make -C gthread
  make -C glib install
  make -C gthread install
  cp -v glib-2.0.pc gthread-2.0.pc "$PREFIX"/lib/pkgconfig
  cd ..
  touch "$PREFIX"/build-stamps/glib
  $RM_RF $GLIB
fi

# pkg-config
PKGCONFIG="pkg-config-0.27"
if test ! -f "$PREFIX"/build-stamps/pkg-config; then
  download http://pkgconfig.freedesktop.org/releases/$PKGCONFIG.tar.gz
  tar zxvf $PKGCONFIG.tar.gz
  cd $PKGCONFIG
  patch -Np1 -i ../pkg-config-win32-prefix-escaping.patch
  ./configure $COMMON_AUTOCONF_FLAGS
  make
  make install
  cd ..
  touch "$PREFIX"/build-stamps/pkg-config
  $RM_RF $PKGCONFIG
fi

# The rest of GNU Gettext
# See the note on the runtime for why we split the
# build like this. If libunistring, libxml2, or libcroco
# are ever added, we should do this after them.
if test ! -f "$PREFIX"/build-stamps/gettext; then
  download http://ftp.gnu.org/gnu/gettext/$GETTEXT.tar.gz
  tar zxvf $GETTEXT.tar.gz
  cd $GETTEXT
  ./configure $COMMON_AUTOCONF_FLAGS --enable-relocatable --disable-libasprintf --disable-java --disable-csharp CXX="$CROSS_GXX"
  make
  make install
  cd ..
  touch "$PREFIX"/build-stamps/gettext
  $RM_RF $GETTEXT
fi

# libogg
LIBOGG="libogg-1.3.0"
if test ! -f "$PREFIX"/build-stamps/libogg; then
  download http://downloads.xiph.org/releases/ogg/$LIBOGG.tar.xz
  tar Jxvf $LIBOGG.tar.xz
  cd $LIBOGG
  ./configure $COMMON_AUTOCONF_FLAGS
  make
  make install
  cd ..
  touch "$PREFIX"/build-stamps/libogg
  $RM_RF $LIBOGG
fi

# libvorbis
LIBVORBIS="libvorbis-1.3.3"
if test ! -f "$PREFIX"/build-stamps/libvorbis; then
  download http://downloads.xiph.org/releases/vorbis/$LIBVORBIS.tar.xz
  tar Jxvf $LIBVORBIS.tar.xz
  cd $LIBVORBIS
  ./configure $COMMON_AUTOCONF_FLAGS
  make
  make install
  cd ..
  touch "$PREFIX"/build-stamps/libvorbis
  $RM_RF $LIBVORBIS
fi

# libtheora
LIBTHEORA="libtheora-1.2.0alpha1"
if test ! -f "$PREFIX"/build-stamps/libtheora; then
  download http://downloads.xiph.org/releases/theora/$LIBTHEORA.tar.xz
  tar Jxvf $LIBTHEORA.tar.xz
  cd $LIBTHEORA
  ./configure $COMMON_AUTOCONF_FLAGS
  make
  make install
  cd ..
  touch "$PREFIX"/build-stamps/libtheora
  $RM_RF $LIBTHEORA
fi

# libsmf
LIBSMF="libsmf-1.3"
if test ! -f "$PREFIX"/build-stamps/libsmf; then
  download http://download.sourceforge.net/libsmf/$LIBSMF.tar.gz
  tar zxvf $LIBSMF.tar.gz
  cd $LIBSMF
  ./configure $COMMON_AUTOCONF_FLAGS
  make LDFLAGS=-no-undefined
  make install
  cd ..
  touch "$PREFIX"/build-stamps/libsmf
  $RM_RF $LIBSMF
fi

# soundtouch
SOUNDTOUCH="soundtouch-1.6.0"
if test ! -f "$PREFIX"/build-stamps/soundtouch; then
  download http://www.surina.net/soundtouch/$SOUNDTOUCH.tar.gz
  tar zxvf $SOUNDTOUCH.tar.gz
  cd soundtouch
  ./bootstrap
  ./configure $COMMON_AUTOCONF_FLAGS
  make LDFLAGS=-no-undefined
  make install
  cd ..
  touch "$PREFIX"/build-stamps/soundtouch
  $RM_RF soundtouch
fi

# soundtouch-c
# The reason we build this here even though it's from code in src/
# is that we need a bridge into the MinGW-compiled C++ code that is
# SoundTouch that we can link to with MSVC.
if test ! -f "$PREFIX"/build-stamps/soundtouch-c; then
  $CROSS_GXX -g -O2 -W -Wall `pkg-config --cflags glib-2.0 soundtouch` -fno-exceptions -fno-rtti -c -o soundtouch-c.o ../src/MixStream/soundtouch-c.cpp
  rm -f "$PREFIX"/lib/soundtouch-c.lib
  $CROSS_AR cru "$PREFIX"/lib/soundtouch-c.lib soundtouch-c.o
  $CROSS_RANLIB "$PREFIX"/lib/soundtouch-c.lib
  touch "$PREFIX"/build-stamps/soundtouch-c
  $RM_RF soundtouch-c.o
fi

# SDL
SDL="SDL-1.2.15"
if test ! -f "$PREFIX"/build-stamps/sdl; then
  download http://www.libsdl.org/release/$SDL.tar.gz
  tar zxvf $SDL.tar.gz
  cd $SDL
  ./configure $COMMON_AUTOCONF_FLAGS
  make
  make install
  mv -v "$PREFIX"/lib/libSDLmain.a "$PREFIX"/lib/SDLmain.lib
  rm -f "$PREFIX"/lib/libSDLmain.la
  # Compatible with MSVC, unlike what was already installed as SDL_config.h
  cp -v include/SDL_config_win32.h "$PREFIX"/include/SDL/SDL_config.h
  cd ..
  touch "$PREFIX"/build-stamps/sdl
  $RM_RF $SDL
fi

# SDL_mixer
SDLMIXER="SDL_mixer-1.2.12"
if test ! -f "$PREFIX"/build-stamps/sdl_mixer; then
  download http://www.libsdl.org/projects/SDL_mixer/release/$SDLMIXER.tar.gz
  tar zxvf $SDLMIXER.tar.gz
  cd $SDLMIXER
  ./configure $COMMON_AUTOCONF_FLAGS --disable-music-mod --disable-music-midi --disable-music-mp3
  make
  make install
  cd ..
  touch "$PREFIX"/build-stamps/sdl_mixer
  $RM_RF $SDLMIXER
fi

# portaudio
PORTAUDIO="pa_stable_v19_20111121"
if test ! -f "$PREFIX"/build-stamps/portaudio; then
  download http://www.portaudio.com/archives/$PORTAUDIO.tgz
  tar zxvf $PORTAUDIO.tgz
  cd portaudio
  ./configure $COMMON_AUTOCONF_FLAGS --with-winapi=directx
  make
  make install
  cd ..
  touch "$PREFIX"/build-stamps/portaudio
  $RM_RF portaudio
fi

# ffmpeg
# We only need libswscale.
FFMPEG="ffmpeg-0.11.1"
if test ! -f "$PREFIX"/build-stamps/ffmpeg; then
  download http://www.ffmpeg.org/releases/$FFMPEG.tar.bz2
  tar jxvf $FFMPEG.tar.bz2
  cd $FFMPEG
  patch -Np1 -i ../ffmpeg-implib-install.patch
  ./configure --prefix="$PREFIX" --cc="$CROSS_GCC" --nm="$CROSS_NM" --target-os=mingw32 --arch=i386 --disable-static --enable-shared --enable-runtime-cpudetect --enable-memalign-hack --disable-everything --disable-ffmpeg --disable-ffplay --disable-ffserver --disable-ffprobe --disable-avdevice --disable-avcodec --disable-avformat --disable-avfilter --disable-swresample
  make
  make install
  cd ..
  touch "$PREFIX"/build-stamps/ffmpeg
  $RM_RF $FFMPEG
fi

# msinttypes
# MSVC needs these to compile stuff that uses ffmpeg. Since they intentionally
# do not work with gcc, we install them to a subdirectory of deps/include
# and feed MSVC an appropriate include_dir option in setup.py.
if test ! -f "$PREFIX"/build-stamps/msinttypes; then
  download http://msinttypes.googlecode.com/files/msinttypes-r26.zip
  unzip -od deps/include/msinttypes msinttypes-r26.zip stdint.h inttypes.h
  touch "$PREFIX"/build-stamps/msinttypes
fi

echo "All dependencies done."
