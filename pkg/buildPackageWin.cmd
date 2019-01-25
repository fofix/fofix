REM  this script will build the binarys with py2exe
REM  and makes the folder ready for distribution

cd ..
python setup.py py2exe

rd /S /Q build
rd /S /Q scripts
del *.pyc


xcopy dist\* . /E /Y
rd /S /Q dist
rd /S /Q svg

pause
