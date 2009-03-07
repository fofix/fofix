set GnuBin=C:\Progra~1\GnuWin32\bin
cd ..
rem xgettext --from-code iso-8859-1 -k_ -kN_ -o src/messages.pot src/*.py
%GnuBin%\xgettext --from-code iso-8859-1 -k_ -kN_ -o messages.pot *.py