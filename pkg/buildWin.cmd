REM  this script will build Win binarys
REM  and create a 7z archive and installer

pushd .
call buildPackageWin.cmd
popd
pushd .
python createArchiveWin.py
call createArchiveWin.cmd
popd
del createArchiveWin.cmd
python MakeFoFiXInstaller.py

pause