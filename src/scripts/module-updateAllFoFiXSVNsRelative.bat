call backToFoFiXroot.bat

set TortoiseSVN=C:\Progra~1\TortoiseSVN\bin\
set localpath=.\


rem FoFiX development trunk / HEAD revision
rem read-only SVN @ http://fofix.googlecode.com/svn/MFH-Mod/trunk/
rem full SVN @ https://fofix.googlecode.com/svn/MFH-Mod/trunk/
START /WAIT %TortoiseSVN%TortoiseProc.exe /command:update /path:"%localpath%" /closeonend:%CloseOnEnd%

cd wiki
START /WAIT %TortoiseSVN%TortoiseProc.exe /command:update /path:"%localpath%" /closeonend:%CloseOnEnd%

rem RB1 / RbMFH theme by MFH - SVN @ http://svn.xp-dev.com/svn/myfingershurt-fofix-rb1-theme/
cd ..\data\themes\Rock Band 1
START /WAIT %TortoiseSVN%TortoiseProc.exe /command:update /path:"%localpath%" /closeonend:%CloseOnEnd%

rem RB2 theme by kid - SVN @ http://svn.xp-dev.com/svn/kristijan_mkd_RockBand2Theme/
cd ..
cd Rock Band 2
START /WAIT %TortoiseSVN%TortoiseProc.exe /command:update /path:"%localpath%" /closeonend:%CloseOnEnd%

rem GH3 theme by Worldrave - SVN @ http://svn.xp-dev.com/svn/worldrave-guitarheroIII/
cd ..
cd Guitar Hero III
START /WAIT %TortoiseSVN%TortoiseProc.exe /command:update /path:"%localpath%" /closeonend:%CloseOnEnd%


cd ..
cd ..
cd ..
rem pause

