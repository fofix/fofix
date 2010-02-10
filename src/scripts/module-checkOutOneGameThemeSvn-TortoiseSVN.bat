call backToFoFiXroot.bat
cd data\themes

IF EXIST "%currentThemeFolder%" GOTO CheckoutDone 
echo Checking out %currentThemeFolder% from %urlOfThemeSvn% ...
START /WAIT %TortoiseSVN%TortoiseProc.exe /command:checkout /path:"%localpath%%currentThemeFolder%" /url:"%urlOfThemeSvn%" /closeonend:%CloseOnEnd%
:CheckoutDone

cd ..
cd ..
cd src\scripts