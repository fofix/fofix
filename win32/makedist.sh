#!/bin/sh -e

mkdir -pv dist
cp -av deps dist

rm -rf dist/deps/build-stamps dist/deps/etc dist/deps/share dist/deps/lib/gettext
rm -vf dist/deps/lib/*.la dist/deps/bin/wine-shwrap dist/deps/bin/pkg-config
i586-mingw32msvc-strip --strip-all dist/deps/bin/*.exe dist/deps/bin/*.dll
ZIPFILE="fofix-win32-deppack-`date +%Y%m%d`.zip"
rm -f "$ZIPFILE"
(cd dist && zip -9r ../"$ZIPFILE" deps)
