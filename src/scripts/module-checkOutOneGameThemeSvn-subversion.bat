call backToFoFiXroot.bat
cd data\themes

IF EXIST "%currentThemeFolder%" GOTO CheckoutDone 
echo Checking out %currentThemeFolder% from %urlOfThemeSvn% ...
svn checkout "%urlOfThemeSvn%" "%currentThemeFolder%"
:CheckoutDone

cd ..
cd ..
cd src\scripts