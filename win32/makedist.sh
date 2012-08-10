#!/bin/sh -e

echo -n "Copying deps/ into dist/... "
mkdir -p dist
cp -a deps dist
echo "done"

echo -n "Removing unnecessary files (except in bin/ and lib/)... "
rm -rf dist/deps/build-stamps dist/deps/doc dist/deps/etc dist/deps/share dist/deps/lib/gettext
echo "done"
echo -n "Removing libtool libs, existing .def files, and unneeded scripts... "
rm -f dist/deps/lib/*.la dist/deps/lib/*.def dist/deps/bin/wine-shwrap dist/deps/bin/pkg-config dist/deps/bin/i686-w64-mingw32-gcc dist/deps/bin/i686-w64-mingw32-g++
echo "done"

echo -n "Generating .def files... "
python makedefs.py dist/deps/lib dist/deps/bin "i686-w64-mingw32-dlltool -I"
echo "done"
echo -n "Stripping binaries and libraries... "
i686-w64-mingw32-strip --strip-all dist/deps/bin/*.exe dist/deps/bin/*.dll
i686-w64-mingw32-strip --strip-debug dist/deps/lib/*.lib dist/deps/lib/*.a
echo "done"
echo -n "Generating README... "
cat README.deppack.stub dist/deps/URLs >dist/README.txt
todos dist/README.txt
rm -f dist/deps/URLs
echo "done"
ZIPFILE="fofix-win32-deppack-`date +%Y%m%d`.zip"
rm -f "$ZIPFILE"
(cd dist && zip -9r ../"$ZIPFILE" *)
