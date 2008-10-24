copy fretsonfire.ini fretsonfire.bak
copy fretsonfire.fresh.ini fretsonfire.ini
"C:\Program Files\WinRAR\winrar" u -dh -s -m5 -tl -ibck FoFiX-MegaLight.rar @Dist-MegaLight.lst
copy fretsonfire.bak fretsonfire.ini