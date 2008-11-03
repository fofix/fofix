CXFREEZE=/usr/src/experimental/cx_Freeze-3.0.3/FreezePython
PYTHON=python2.4
PYTHON_LIBS=/usr/lib/python2.4
USE_AMANITH=1
MESSAGESPOT=src/messages.pot

# evilynux - Dynamically update the version number, this is "clever" but hard to understand... :-(
VERSION=`grep "versionString =" src/GameEngine.py | sed -e "s/.\+\(\([0-9]\+\.\)\+[0-9]\+\).\+/\1/g"`

all:	dist

patch: dist
	@echo --- Creating patch
	[ -d FoFiX-${VERSION}-Patch-GNULinux-64bit ] && \
	rm -rf FoFiX-${VERSION}-Patch-GNULinux-64bit* || echo
	perl Dist-Patch3_0xx-GNULinux.pl FoFiX-${VERSION}-Patch-GNULinux-64bit
	tar -cjvf FoFiX-${VERSION}-Patch-GNULinux-64bit.tar.bz2 FoFiX-${VERSION}-Patch-GNULinux-64bit/

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
OpenGL.arrays.numpymodule,\
OpenGL.arrays.ctypesarrays,\
OpenGL.arrays.ctypesparameters,\
OpenGL.arrays.ctypespointers,\
OpenGL.arrays.strings,\
OpenGL.arrays.numbers,\
OpenGL.arrays.nones,\
xml.sax.drivers2.drv_pyexpat,\
GameResultsScene src/FretsOnFire.py

	@echo --- Copying data
	cd src; $(PYTHON) setup.py install_data --install-dir ../dist ; cd ..

#	@echo --- Fixing PyOpenGL-ctypes
#	cp -Lr $(PYTHON_LIBS)/site-packages/PyOpenGL*egg-info dist

ifneq ($(USE_AMANITH), 1)
	@echo --- Rendering SVG files to PNG images
	cd dist; $(PYTHON) ../src/svg2png.py; cd ..
endif

	@echo --- Fixing stuff
ifeq ($(USE_AMANITH), 1)
	strip dist/_amanith.so
	cp /home/evilynux/FoF-pkg/libamanith.so.1.64bit dist/libamanith.so.1
else
	rm dist/_amanith.so
endif

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

doc:
	cd doc ; epydoc -n "Frets On Fire" ../src/*.py ; cd ..

run:	dist
	@cd dist ; ./FretsOnFire ; cd ..

sdist:	doc
	mkdir FretsOnFire-src-$(VERSION)
	mkdir FretsOnFire-src-$(VERSION)/src
	mkdir FretsOnFire-src-$(VERSION)/src/midi
	mkdir FretsOnFire-src-$(VERSION)/doc
	mkdir FretsOnFire-src-$(VERSION)/data
	mkdir FretsOnFire-src-$(VERSION)/data/translations
	cp -rvp src/*.py      FretsOnFire-src-$(VERSION)/src
	cp -rvp src/*.pot     FretsOnFire-src-$(VERSION)/src
	cp -rvp src/midi/*.py FretsOnFire-src-$(VERSION)/src/midi
	cp -rvp doc/html      FretsOnFire-src-$(VERSION)/doc
	cp -rvp *.txt         FretsOnFire-src-$(VERSION)
	cp -rvp Makefile*     FretsOnFire-src-$(VERSION)
	cp -rvp data/translations/*.po     FretsOnFire-src-$(VERSION)/data/translations
	cp -rvp data/translations/update*     FretsOnFire-src-$(VERSION)/data/translations
	tar cvzf FretsOnFire-src-$(VERSION).tar.gz FretsOnFire-src-$(VERSION)

translations:
	xgettext --from-code iso-8859-1 -k_ -kN_ -o $(MESSAGESPOT) src/*.py
	
clean:
	@rm -rf dist build doc/html

.PHONY: dist doc sdist

