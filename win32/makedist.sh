#!/bin/sh -e

echo -n "Copying deps/ into dist/... "
mkdir -p dist
cp -a deps dist
echo "done"

echo -n 'Removing unnecessary files... '
rm -rf dist/deps/build-stamps dist/deps/doc dist/deps/etc dist/deps/share dist/deps/lib/gettext
rm -f dist/deps/lib/*.la dist/deps/bin/wine-shwrap dist/deps/bin/pkg-config
echo "done"

echo -n "Stripping binaries and libraries... "
i686-w64-mingw32-strip --strip-all dist/deps/bin/*.exe dist/deps/bin/*.dll
i686-w64-mingw32-strip --strip-debug dist/deps/lib/*.lib dist/deps/lib/*.a
echo "done"
ZIPFILE="fofix-win32-deppack-`date +%Y%m%d`.zip"
rm -f "$ZIPFILE"
(cd dist && zip -9r ../"$ZIPFILE" deps)
