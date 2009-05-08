set TortoiseSVN=C:\Progra~1\TortoiseSVN\bin\

set FofDrive=X:

set ExportDestination=X:\Games\FoFiX\FoFiX_export_temp

set home_srcbin_dir=X:\Games\FoFiX\FoFiX
set home_src_wiki_dir=X:\Games\FoFiX\FoFiX-wiki

svn export %home_src_wiki_dir% %ExportDestination%\FoFiX-wiki
svn export %home_srcbin_dir% %ExportDestination%\FoFiX

%FofDrive%
cd %ExportDestination%\FoFiX\src\scripts
call RebuildWin.bat
cd pkg
call Package3_1xxPatchDistWin.bat
cd pkg
call PackageMegaLightDistWin.bat

cd ..
move FoFiX\pkg\*.rar .\

rd /s /q FoFiX
rd /s /q FoFiX-wiki

pause
