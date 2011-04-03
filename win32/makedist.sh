#!/bin/sh -e

mkdir -pv dist
cp -av deps dist

rm -rf dist/deps/build-stamps dist/deps/doc dist/deps/etc dist/deps/share dist/deps/lib/gettext
rm -vf dist/deps/lib/*.la dist/deps/bin/wine-shwrap dist/deps/bin/pkg-config
i686-w64-mingw32-strip --strip-all dist/deps/bin/*.exe dist/deps/bin/*.dll
i686-w64-mingw32-strip --strip-debug dist/deps/lib/*.lib dist/deps/lib/*.a
ZIPFILE="fofix-win32-deppack-`date +%Y%m%d`.zip"
rm -f "$ZIPFILE"
(cd dist && zip -9r ../"$ZIPFILE" deps)
