# evilynux - Change this path to make it point to your cxFreeze
CXFREEZE=/usr/src/experimental/cx_Freeze-3.0.3/FreezePython

PYTHON=python2.4
PYTHON_LIBS=/usr/lib/python2.4
MESSAGESPOT=messages.pot

# evilynux - Update files from SVN and build version number at the same time. This is "clever" but hard to understand... :-(
SVN_VERSION = $(shell svn up | sed -e "s/.\+\ \([0-9]\+\)\./r\1/")
MAIN_VERSION = $(shell grep "+ version" src/GameEngine.py | sed -e "s/\s/_/g" | sed -e "s/^.\+\(\([0-9]\.\)\+[^\"]\+\).\+/1/")
VERSION = "${MAIN_VERSION}~${SVN_VERSION}"
# evilynux - Dynamically get the architecture; only supports 32bit/64bit
UNAME = $(shell uname -m)
ARCH = $(shell test $(UNAME) = "i686" && echo 32bit || echo 64bit)
# evilynux - Folder names for both patches and full releases
DIRFULL=FoFiX-${VERSION}-Full-GNULinux-${ARCH}
DIRPATCH=FoFiX-${VERSION}-Patch-GNULinux-${ARCH}

all:	dist

patch: dist
	@echo --- Creating patch
	[ -d ${DIRPATCH} ] && \
	rm -rf ${DIRPATCH}* || echo 
	perl pkg/Package-GNULinux.pl -d ${DIRPATCH} -l pkg/Dist-Patch3_0xx-GNULinux.lst &&\
	tar -cjvf ${DIRPATCH}.tar.bz2 ${DIRPATCH}/

bindist: dist
	@echo --- Creating full release
	[ -d ${DIRFULL} ] && \
	rm -rf ${DIRFULL}* || echo 
	perl pkg/Package-GNULinux.pl -d ${DIRFULL} -l pkg/Dist-MegaLight-GNULinux.lst &&\
	tar -cjvf ${DIRFULL}.tar.bz2 ${DIRFULL}/

dist:
	@echo --- Detected version: ${VERSION}
	@echo --- Building binary
	$(CXFREEZE) --target-dir dist \
--include-modules \
encodings.string_escape,\
encodings.iso8859_1,\
SongChoosingScene,\
GuitarScene,\
ctypes.util,pkg_resources,weakref,Image,\
OpenGL,\
xml.sax.drivers2.drv_pyexpat,\
GameResultsScene src/FretsOnFire.py

	-cp /usr/lib/libpython2.4.so.1.0 \
           /usr/lib/libSDL_ttf-2.0.so.0 \
           /usr/lib/libSDL_mixer-1.2.so.0 \
           /usr/lib/libvorbisfile.so.3 \
           /usr/lib/libvorbis.so.0 \
           /usr/lib/libogg.so.0 \
           /usr/lib/libsmpeg-0.4.so.0 \
           /usr/lib/libffi.so.5 \
           /usr/lib/liblapack.so.3gf \
           /usr/lib/libmikmod.so.2 \
           dist
	mv dist/FretsOnFire dist/FretsOnFire.bin
	-cp src/launcher.sh dist/FretsOnFire
	-chmod +x dist/FretsOnFire

translations:
	cd src && \
	xgettext --from-code iso-8859-1 -k_ -kN_ -o $(MESSAGESPOT) *.py && \
	cd ..

clean:
	@rm -rf dist

.PHONY: clean

