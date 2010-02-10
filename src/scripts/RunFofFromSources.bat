call ClearCompiledPycs
python FoFiX.py
pause
rem - this new pause allows the game to restart for new settings 
rem - - without deleting the compiled files.
cd scripts
call ClearCompiledPycs
pause
