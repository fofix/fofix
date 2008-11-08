call GetTranslatableText.bat
python setup.py py2exe
pause
cd scripts
call ClearCompiledPycs.bat
cd ..
del data\*.pyd
del data\*.dll
rem pause
copy dist\FretsOnFire.exe FretsOnFire.exe
copy dist\w9xpopen.exe w9xpopen.exe
copy dist\data\library.zip data\library.zip
copy dist\data\*.pyd data\
copy dist\data\*.dll data\
copy /y dist\*.dll
rd /s /q dist
pause