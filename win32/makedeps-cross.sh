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
  export CROSS_TOOL_PREFIX=i586-mingw32msvc
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
assert_binary_on_path libtoolize
assert_binary_on_path make
assert_binary_on_path pkg-config
assert_binary_on_path python
assert_binary_on_path svn
assert_binary_on_path tar
assert_binary_on_path unzip
assert_binary_on_path wget

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

export PATH="$PREFIX"/bin:"$PATH"

download () {
  basename="`basename "$1"`"
  if test ! -f "$basename"; then
    wget -c -O "$basename".part "$1"
    mv -v "$basename".part "$basename"
  fi
}

# We use win-iconv instead of full-fledged GNU libiconv because it still does
# everything the other deps need and is far smaller.
WINICONV="win-iconv-0.0.2"
if test ! -f "$PREFIX"/build-stamps/win-iconv; then
  download http://win-iconv.googlecode.com/files/$WINICONV.tar.bz2
  tar jxvf $WINICONV.tar.bz2
  cd $WINICONV
  make clean
  make -n iconv.dll win_iconv.exe | sed -e 's/^/$CROSS_TOOL_PREFIX-/' | sh -ex
  $CROSS_GCC -mdll -o iconv.dll -Wl,--out-implib,libiconv.a iconv.def win_iconv.o
  cp -v iconv.dll win_iconv.exe "$PREFIX"/bin
  cp -v iconv.h "$PREFIX"/include
  echo '' >>"$PREFIX"/include/iconv.h  # squelch warnings about no newline at the end
  sed -i -e 's://.*$::' "$PREFIX"/include/iconv.h  # squelch warnings about C++ comments
  cp -v libiconv.a "$PREFIX"/lib
  cd ..
  touch "$PREFIX"/build-stamps/win-iconv
  $RM_RF $WINICONV
fi

# zlib
ZLIB="zlib-1.2.5"
if test ! -f "$PREFIX"/build-stamps/zlib; then
  download http://www.zlib.net/$ZLIB.tar.bz2
  tar jxvf $ZLIB.tar.bz2
  cd $ZLIB
  make -f win32/Makefile.gcc PREFIX="$CROSS_TOOL_PREFIX"- zlib1.dll
  cp -v zlib.h zconf.h "$PREFIX"/include
  cp -v zlib1.dll "$PREFIX"/bin
  cp -v libzdll.a "$PREFIX"/lib/libz.a
  cd ..
  touch "$PREFIX"/build-stamps/zlib
  $RM_RF $ZLIB
fi

# Flags passed to every dependency's ./configure script, for those deps that use autoconf and friends.
COMMON_AUTOCONF_FLAGS="--prefix=$PREFIX --host=$CROSS_TOOL_PREFIX --disable-static --enable-shared CPPFLAGS=-I$PREFIX/include LDFLAGS=-L$PREFIX/lib"

# Runtime (libintl) of GNU Gettext
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

# GLib
GLIB="glib-2.26.1"
if test ! -f "$PREFIX"/build-stamps/glib; then
  download http://ftp.gnome.org/pub/GNOME/sources/glib/2.26/$GLIB.tar.bz2
  tar jxvf $GLIB.tar.bz2
  cd $GLIB
  ./configure $COMMON_AUTOCONF_FLAGS
  make -C glib
  make -C gthread
  make -C gobject glib-genmarshal.exe
  wine-shwrap gobject/glib-genmarshal
  make
  make install
  cd ..
  touch "$PREFIX"/build-stamps/glib
  $RM_RF $GLIB
fi

# pkg-config
PKGCONFIG="pkg-config-0.25"
if test ! -f "$PREFIX"/build-stamps/pkg-config; then
  download http://pkgconfig.freedesktop.org/releases/$PKGCONFIG.tar.gz
  tar zxvf $PKGCONFIG.tar.gz
  cd $PKGCONFIG
  ./configure $COMMON_AUTOCONF_FLAGS
  make
  make install
  cd ..
  touch "$PREFIX"/build-stamps/pkg-config
  $RM_RF $PKGCONFIG
fi

# The rest of GNU Gettext
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
LIBOGG="libogg-1.2.1"
if test ! -f "$PREFIX"/build-stamps/libogg; then
  download http://downloads.xiph.org/releases/ogg/$LIBOGG.tar.gz
  tar zxvf $LIBOGG.tar.gz
  cd $LIBOGG
  libtoolize
  autoreconf  # fix buggy configure test for 16-bit types
  ./configure $COMMON_AUTOCONF_FLAGS
  make
  make install
  cd ..
  touch "$PREFIX"/build-stamps/libogg
  $RM_RF $LIBOGG
fi

# libvorbis
LIBVORBIS="libvorbis-1.3.2"
if test ! -f "$PREFIX"/build-stamps/libvorbis; then
  download http://downloads.xiph.org/releases/vorbis/$LIBVORBIS.tar.bz2
  tar jxvf $LIBVORBIS.tar.bz2
  cd $LIBVORBIS
  ./configure $COMMON_AUTOCONF_FLAGS
  make
  make install
  cd ..
  touch "$PREFIX"/build-stamps/libvorbis
  $RM_RF $LIBVORBIS
fi

# libtheora
LIBTHEORA="libtheora-1.1.1"
if test ! -f "$PREFIX"/build-stamps/libtheora; then
  download http://downloads.xiph.org/releases/theora/$LIBTHEORA.tar.bz2
  tar jxvf $LIBTHEORA.tar.bz2
  cd $LIBTHEORA
  ./configure $COMMON_AUTOCONF_FLAGS
  make
  make install
  cd ..
  touch "$PREFIX"/build-stamps/libtheora
  $RM_RF $LIBTHEORA
fi

# ffmpeg
# We only need libswscale.
if test ! -f "$PREFIX"/build-stamps/ffmpeg; then
  if test ! -d ffmpeg; then
    svn co svn://svn.ffmpeg.org/ffmpeg/trunk ffmpeg
  else
    svn up ffmpeg
  fi
  cd ffmpeg
  ./configure --prefix="$PREFIX" --cc="$CROSS_GCC" --nm="$CROSS_NM" --target-os=mingw32 --arch=i386 --disable-static --enable-shared --enable-gpl --enable-runtime-cpudetect --enable-memalign-hack --disable-everything --disable-ffmpeg --disable-ffplay --disable-ffserver --disable-ffprobe --disable-avdevice --disable-avcodec --disable-avcore --disable-avformat --disable-avfilter
  sed -i -e 's/-Werror=[^ ]*//g' config.mak
  make
  make install
  for lib in avutil swscale; do
    # FFmpeg symlinks its DLLs to a few different names, differing in the level
    # of detail of their version number, rather like what is done with ELF shared
    # libraries.  Unfortunately, the real DLL for each one is *not* the one that
    # the implibs reference (that is, the one that will be required at runtime),
    # so we must rename it after we nuke the symlinks.
    find "$PREFIX"/bin -type l -name "${lib}*.dll" -print0 | xargs -0 rm -f
    libfile="`find "$PREFIX"/bin -name "${lib}*.dll" | sed -e 1q`"
    mv -v "$libfile" "`echo "$libfile" | sed -e "s/\($lib-[0-9]*\)[.0-9]*\.dll/\1.dll/"`"
  done
  cd ..
  touch "$PREFIX"/build-stamps/ffmpeg
  $RM_RF ffmpeg
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

echo -n "Creating .def files... "
python makedefs.py deps/lib deps/bin "$CROSS_DLLTOOL -I"
echo "done"
