@echo off
set TortoiseSVN=C:\Progra~1\TortoiseSVN\bin\
set localpath=.\


echo RB1 / RbMFH theme by MFH
set currentThemeFolder=Rock Band 1
set urlOfThemeSvn=http://svn.xp-dev.com/svn/myfingershurt-fofix-rb1-theme/
call module-checkOutOneGameThemeSvn-subversion.bat

echo RB2 theme by kid 
set currentThemeFolder=Rock Band 2
set urlOfThemeSvn=http://svn.xp-dev.com/svn/kristijan_mkd_RockBand2Theme/
call module-checkOutOneGameThemeSvn-subversion.bat

echo The Beatles: Rock Band by @ir15
set currentThemeFolder=The Beatles Rock Band
set urlOfThemeSvn=http://svn.xp-dev.com/svn/TBRB/The Beatles RB Theme/
call module-checkOutOneGameThemeSvn-subversion.bat

echo GH3 theme by Worldrave
set currentThemeFolder=Guitar Hero III
set urlOfThemeSvn=http://svn.xp-dev.com/svn/worldrave-guitarheroIII/
call module-checkOutOneGameThemeSvn-subversion.bat

echo Guitar Hero Aerosmith by worldrave
set currentThemeFolder=Guitar Hero Aerosmith
set urlOfThemeSvn=http://svn.xp-dev.com/svn/worldrave-guitarhero-aerosmith/
call module-checkOutOneGameThemeSvn-subversion.bat

echo Guitar Hero World Tour by gamexprt1 
set currentThemeFolder=Guitar Hero World Tour
set urlOfThemeSvn=http://svn.xp-dev.com/svn/gamexprt1-GHWT/Guitar Hero World Tour/
call module-checkOutOneGameThemeSvn-subversion.bat

echo Guitar Hero: Metallica by kid  
set currentThemeFolder=Guitar Hero Metallica
set urlOfThemeSvn=http://svn2.xp-dev.com/svn/kristijan_mkd-GuitarHeroMetallicaOriginal/
call module-checkOutOneGameThemeSvn-subversion.bat

echo Guitar Hero: Metallica by stashincash06  
set currentThemeFolder=Guitar Hero Metallica sc
set urlOfThemeSvn=http://svn2.xp-dev.com/svn/stashincash06-Guitar-Hero-Metallica/Guitar Hero Metallica
call module-checkOutOneGameThemeSvn-subversion.bat

echo Guitar Hero: Metallica custom by kid  
set currentThemeFolder=Guitar Hero Metallica cust
set urlOfThemeSvn=http://svn.xp-dev.com/svn/kristijan_mkd-GH-Metallica/
call module-checkOutOneGameThemeSvn-subversion.bat


Rem ---------------Other (non-GH/RB game clones) themes-------------------

echo Geetar Hero theme by slantyr
set currentThemeFolder=Geetar Hero
set urlOfThemeSvn=http://svn.xp-dev.com/svn/slantyr-GeetarHero/
call module-checkOutOneGameThemeSvn-subversion.bat

echo Bioshock theme by slantyr
set currentThemeFolder=Bioshock
set urlOfThemeSvn=http://svn.xp-dev.com/svn/slantyr-BioShock/
call module-checkOutOneGameThemeSvn-subversion.bat

echo AC/DC theme
set currentThemeFolder=AC DC
set urlOfThemeSvn=http://svn2.xp-dev.com/svn/PaulTechNox-ACDC-Theme/
call module-checkOutOneGameThemeSvn-subversion.bat

echo STARZ theme
set currentThemeFolder=Starz
set urlOfThemeSvn=http://svn2.xp-dev.com/svn/Hazzerz-STaRZ/
call module-checkOutOneGameThemeSvn-subversion.bat





cd ..
cd ..
pause

