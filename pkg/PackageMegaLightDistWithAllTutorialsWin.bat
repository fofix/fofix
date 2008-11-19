cd ..
copy fretsonfire.ini fretsonfire.bak
copy pkg\fretsonfire.fresh.ini fretsonfire.ini
"C:\Program Files\WinRAR\winrar" u -dh -s -m5 -tl -ibck -x@pkg\filesToExclude.lst pkg\FoFiX-Full-Windows(MegaLight).rar @pkg\Dist-MegaLight-AllTutorials.lst
copy fretsonfire.bak fretsonfire.ini
del fretsonfire.bak
