echo .
echo .
echo .
echo Autocheckout of SVN themes, if script exists....
call checkOutAllGameThemeSvns-subversion.bat

rem cd src\scripts
rem If autocheckout script does not exist, the following will ensure we're back at the root.  
rem ... if autocheckout script does exist, the following will not be found and all will be well.
call backToFoFiXroot.bat

set TortoiseSVN=C:\Progra~1\TortoiseSVN\bin\
set localpath=.\

echo .
echo .
echo .
echo Autoupdate of SVN themes, if they exist...

echo FoFiX development trunk / HEAD revision
rem read-only SVN @ http://fofix.googlecode.com/svn/MFH-Mod/trunk/
rem full SVN @ https://fofix.googlecode.com/svn/MFH-Mod/trunk/
START /WAIT %TortoiseSVN%TortoiseProc.exe /command:update /path:"%localpath%" /closeonend:%CloseOnEnd%

echo FoFiX wiki page source (if local copy exists...)
cd wiki
START /WAIT %TortoiseSVN%TortoiseProc.exe /command:update /path:"%localpath%" /closeonend:%CloseOnEnd%

cd ..\data\themes

echo RB1 / RbMFH theme by MFH - SVN @ http://svn.xp-dev.com/svn/myfingershurt-fofix-rb1-theme/
cd Rock Band 1
START /WAIT %TortoiseSVN%TortoiseProc.exe /command:update /path:"%localpath%" /closeonend:%CloseOnEnd%

cd ..
echo RB1 Beta theme - SVN @ http://svn.xp-dev.com/svn/rbbeta/trunk/
cd Rock Band 1 beta
START /WAIT %TortoiseSVN%TortoiseProc.exe /command:update /path:"%localpath%" /closeonend:%CloseOnEnd%

echo RB2 theme by kid - SVN @ http://svn.xp-dev.com/svn/kristijan_mkd_RockBand2Theme/
cd ..
cd Rock Band 2
START /WAIT %TortoiseSVN%TortoiseProc.exe /command:update /path:"%localpath%" /closeonend:%CloseOnEnd%

echo The Beatles: Rock Band by @ir15 - SVN @ http://svn.xp-dev.com/svn/TBRB/The Beatles RB Theme/
cd ..
cd The Beatles Rock Band
START /WAIT %TortoiseSVN%TortoiseProc.exe /command:update /path:"%localpath%" /closeonend:%CloseOnEnd%

echo Guitar Hero III theme by worldrave - SVN @ http://svn.xp-dev.com/svn/worldrave-guitarheroIII/
cd ..
cd Guitar Hero III
START /WAIT %TortoiseSVN%TortoiseProc.exe /command:update /path:"%localpath%" /closeonend:%CloseOnEnd%

echo Guitar Hero Aerosmith by worldrave - SVN @ http://svn.xp-dev.com/svn/worldrave-guitarhero-aerosmith/
cd ..
cd Guitar Hero Aerosmith
START /WAIT %TortoiseSVN%TortoiseProc.exe /command:update /path:"%localpath%" /closeonend:%CloseOnEnd%

echo Guitar Hero World Tour by gamexprt1 - SVN @ http://svn.xp-dev.com/svn/gamexprt1-GHWT/Guitar Hero World Tour/
cd ..
cd Guitar Hero World Tour
START /WAIT %TortoiseSVN%TortoiseProc.exe /command:update /path:"%localpath%" /closeonend:%CloseOnEnd%

echo Guitar Hero: Metallica by kid - SVN @ http://svn2.xp-dev.com/svn/kristijan_mkd-GuitarHeroMetallicaOriginal/
cd ..
cd Guitar Hero Metallica
START /WAIT %TortoiseSVN%TortoiseProc.exe /command:update /path:"%localpath%" /closeonend:%CloseOnEnd%

echo Guitar Hero: Metallica by stashincash06 - SVN @ http://svn2.xp-dev.com/svn/stashincash06-Guitar-Hero-Metallica/Guitar Hero Metallica
cd ..
cd Guitar Hero Metallica sc
START /WAIT %TortoiseSVN%TortoiseProc.exe /command:update /path:"%localpath%" /closeonend:%CloseOnEnd%

echo Guitar Hero: Metallica custom by kid - SVN @ http://svn.xp-dev.com/svn/kristijan_mkd-GH-Metallica/
cd ..
cd Guitar Hero Metallica cust
START /WAIT %TortoiseSVN%TortoiseProc.exe /command:update /path:"%localpath%" /closeonend:%CloseOnEnd%

echo ....now for non-GH/RB game themes:
Rem ---------------Other (non-GH/RB game clones) themes-------------------


echo Geetar Hero theme by slantyr - SVN @ http://svn.xp-dev.com/svn/slantyr-GeetarHero/
cd ..
cd Geetar Hero
START /WAIT %TortoiseSVN%TortoiseProc.exe /command:update /path:"%localpath%" /closeonend:%CloseOnEnd%

echo Bioshock theme by slantyr - SVN @ http://svn.xp-dev.com/svn/slantyr-BioShock/
cd ..
cd Bioshock
START /WAIT %TortoiseSVN%TortoiseProc.exe /command:update /path:"%localpath%" /closeonend:%CloseOnEnd%

echo AC/DC theme - SVN @ http://svn2.xp-dev.com/svn/PaulTechNox-ACDC-Theme/
cd ..
cd AC DC
START /WAIT %TortoiseSVN%TortoiseProc.exe /command:update /path:"%localpath%" /closeonend:%CloseOnEnd%

echo STARZ theme - SVN @ http://svn2.xp-dev.com/svn/Hazzerz-STaRZ/
cd ..
cd Starz
START /WAIT %TortoiseSVN%TortoiseProc.exe /command:update /path:"%localpath%" /closeonend:%CloseOnEnd%


cd ..
cd ..
rem pause

