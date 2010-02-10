set TortoiseSVN=C:\Progra~1\TortoiseSVN\bin\
set home_srcbin_dir=S:\Data\Games\FretsOnFire\FoFiX\

START /WAIT %TortoiseSVN%TortoiseProc.exe /command:update /path:"%home_srcbin_dir%" /closeonend:1

rem This pause will let you see any SVN update errors
rem in case this doesn't just work...
rem pause

call GetTranslatableText.bat
python setup.py py2exe
rem This pause will let you see any compile or linking errors
rem in case this doesn't just work...
rem pause

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
rem pause

echo Testing loopback network connection...
rem ping 127.0.0.1 >nul
ping 127.0.0.1

echo Running FoFiX...
FretsOnFire.exe