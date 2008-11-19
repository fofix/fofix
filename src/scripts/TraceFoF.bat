call ClearCompiledPycs

rem Below traces execution in immediate window:
rem python -m trace --trace FretsOnFire.py

rem Below traces to a file (HUGE - to the tune of ~10MB / Second!)
del trace.log
rem python -m trace --trace FretsOnFire.py > trace.log

rem ...and ignores base modules
python -m trace --trace --ignore-dir midi --ignore-module iso8859_1 --ignore-module codecs --ignore-module utf_8 --ignore-module latin_1 --ignore-module string --ignore-module ntpath --ignore-module GL__init__ --ignore-module Numeric --ignore-module Precision --ignore-module ArrayPrinter --ignore-module pickle --ignore-module sre --ignore-module sre_compile --ignore-module sre_parse --ignore-module copy --ignore-module inspect --ignore-module dis --ignore-module opcode --ignore-module StringIO --ignore-module copy_reg --ignore-module color --ignore-module colordict --ignore-module cursors --ignore-module sprite --ignore-module sysfont --ignore-module socket --ignore-module os --ignore-module asyncore --ignore-module shutil --ignore-module threading --ignore-module new --ignore-module urllib --ignore-module urlparse --ignore-module nturl2path --ignore-module gettext --ignore-module fnmatch --ignore-module glob --ignore-module stat --ignore-module multisample --ignore-module __future__ --ignore-module GLU__init__ --ignore-module _exceptions --ignore-module handler --ignore-module xmlreader --ignore-module random --ignore-module amanith --ignore-module zipfile --ignore-module minicompat --ignore-module xmlbuilder --ignore-module minidom --ignore-module domreg --ignore-module locale --ignore-module colorsys --ignore-module getopt --ignore-module expatreader --ignore-module expat --ignore-module saxutils --ignore-module weakref --ignore-module NodeFilter --ignore-module FixTk --ignore-module Image --ignore-module ImageMode --ignore-module ImagePalette --ignore-module ImageFile --ignore-module BmpImagePlugin --ignore-module PngImagePlugin --ignore-module JpegImagePlugin --ignore-module PpmImagePlugin --ignore-module GifImagePlugin --ignore-module Config --ignore-module ConfigParser --ignore-module Svg --ignore-module Texture FretsOnFire.py > trace.log

rem Disabled "--ignore-module" statements:
rem 

rem Below stores line execution counts (only written after close - not good for crashes or hangs):
rem python -m trace -c -C traced FretsOnFire.py


cd scripts
call ClearCompiledPycs
pause
