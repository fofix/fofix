call GetTranslatableText.bat
python setup.py py2exe
pause
cd scripts
call ClearCompiledPycs.bat
cd ..
del *.exe
del *.dll
del *.exe.log
del data\*.pyd
del data\*.dll
del data\*.zip
rem pause
copy dist\data\*.zip data\
copy dist\data\*.pyd data\
copy dist\data\*.dll data\
copy /y dist\*.exe
copy /y dist\*.dll
rd /s /q dist
pause