cd..
copy fofix.ini fofix.bak
copy pkg\fofix.fresh.ini fofix.ini
"C:\Program Files\WinRAR\winrar" u -dh -s -m5 -tl -ibck -x@pkg\filesToExclude.lst pkg\FoFiX-PatchFrom3_1xx-Win32.rar @pkg\Dist-Patch3_1xx.lst
copy fofix.bak fofix.ini
del fofix.bak
