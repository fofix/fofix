call GetTranslatableText.bat
python setup.py py2exe
rem pause
call ClearCompiledPycs.bat
cd ..
copy dist\FretsOnFire.exe FretsOnFire.exe
copy dist\data\library.zip data\library.zip
rd /s /q dist
