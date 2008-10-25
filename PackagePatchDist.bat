copy fretsonfire.ini fretsonfire.bak
copy fretsonfire.fresh.ini fretsonfire.ini
"C:\Program Files\WinRAR\winrar" u -dh -s -m5 -tl -ibck FoFiX-Patch.rar @Dist-Patch3_0xx.lst
copy fretsonfire.bak fretsonfire.ini