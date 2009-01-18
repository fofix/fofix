#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire X (FoFiX)                                           #
# Copyright (C) 2009 myfingershurt                                  #
#               2009 John Stumpo                                    #
#                                                                   #
# This program is free software; you can redistribute it and/or     #
# modify it under the terms of the GNU General Public License       #
# as published by the Free Software Foundation; either version 2    #
# of the License, or (at your option) any later version.            #
#                                                                   #
# This program is distributed in the hope that it will be useful,   #
# but WITHOUT ANY WARRANTY; without even the implied warranty of    #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the     #
# GNU General Public License for more details.                      #
#                                                                   #
# You should have received a copy of the GNU General Public License #
# along with this program; if not, write to the Free Software       #
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,        #
# MA  02110-1301, USA.                                              #
#####################################################################

__version__ = '$Id$'

import os
if os.name != 'nt':
  sys.stderr.write('This script only works on Windows.\n')
  sys.exit(1)

import ListToNSIS
import _winreg
import sys
import shutil
import win32api

us = r'..\FretsOnFire.exe'
if not os.path.isfile(us):
  sys.stderr.write("There's no FretsOnFire.exe - did you compile yet?\n")
  sys.exit(1)
vdict = win32api.GetFileVersionInfo(us, '\\')
# Unfortunately we need to do some bit-twiddling to retrieve the main version number.
FOFIX_VERSION = '%d.%d.%d.%d' % (vdict['FileVersionMS'] >> 16, vdict['FileVersionMS'] & 0xffff, vdict['FileVersionLS'] >> 16, vdict['FileVersionLS'] & 0xffff)
FOFIX_VERSION_FULL = str(win32api.GetFileVersionInfo(us, r'\StringFileInfo\%04x%04x\ProductVersion' % win32api.GetFileVersionInfo(us, r'\VarFileInfo\Translation')[0]))

MLDist = ListToNSIS.NsisScriptGenerator('..')
MLDist.readList('Dist-MegaLight-AllTutorials.lst')
MLDist.readExcludeList('filesToExclude.lst')

os.chdir('..')

# Find NSIS.
try:
  key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, r'Software\NSIS')
  nsisPath = _winreg.QueryValueEx(key, '')[0]
  _winreg.CloseKey(key)
except WindowsError:
  sys.stderr.write("Looks like you don't have NSIS - get it at http://nsis.sourceforge.net/\n")
  sys.exit(1)
makensis = os.path.join(nsisPath, 'makensis.exe')

# Generate the script.
builder = ListToNSIS.NsisScriptBuilder(r"""
!define FOFIX_VERSION %s
!define FOFIX_VERSION_FULL "%s"
!include "MUI2.nsh"

# Installer title and filename.
Name 'FoFiX v${FOFIX_VERSION_FULL}'
OutFile 'pkg\FoFiX v${FOFIX_VERSION_FULL} Setup.exe'

# Installer parameters.
SetCompressor /SOLID lzma
RequestExecutionLevel user  # no UAC on Vista
ShowInstDetails show
ShowUninstDetails show

# Where we're going (by default at least)
InstallDir '$DOCUMENTS\FoFiX'
# Where we're stashing the install location.
InstallDirRegKey HKCU 'SOFTWARE\myfingershurt\FoFiX' InstallRoot

# More installer parameters.
!define MUI_ABORTWARNING
!define MUI_UNABORTWARNING
!define MUI_FINISHPAGE_NOAUTOCLOSE
!define MUI_UNFINISHPAGE_NOAUTOCLOSE
!define MUI_LICENSEPAGE_RADIOBUTTONS
!define MUI_HEADERIMAGE
# gfx pending
#!define MUI_HEADERIMAGE_BITMAP "pkg\installer_gfx\header.bmp"
#!define MUI_HEADERIMAGE_UNBITMAP "pkg\installer_gfx\header.bmp"

# The pages of the installer...
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "COPYING"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

# ...and of the uninstaller.
!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

# Throw in a cool background image.
# gfx pending
#!define MUI_CUSTOMFUNCTION_GUIINIT startBackground
#Function startBackground
#  InitPluginsDir
#  File /oname=$PLUGINSDIR\background.bmp pkg\installer_gfx\background.bmp
#  BgImage::SetBG /NOUNLOAD /FILLSCREEN $PLUGINSDIR\background.bmp
#  BgImage::Redraw /NOUNLOAD
#FunctionEnd
#Function .onGUIEnd
#  BgImage::Destroy
#FunctionEnd

!insertmacro MUI_LANGUAGE "English"

# Add version info to the resulting installers.
# I know py2exe has some sort of options that can let FretsOnFire.exe have version info too...
VIProductVersion "${FOFIX_VERSION}"
VIAddVersionKey /LANG=1033 "CompanyName" "FoFiX Team"
VIAddVersionKey /LANG=1033 "FileDescription" "FoFiX Setup"
VIAddVersionKey /LANG=1033 "FileVersion" "${FOFIX_VERSION_FULL}"
VIAddVersionKey /LANG=1033 "InternalName" "FoFiX v${FOFIX_VERSION_FULL} Setup.exe"
VIAddVersionKey /LANG=1033 "LegalCopyright" "© 2008-2009 FoFiX Team.  GNU GPL v2 or later."
VIAddVersionKey /LANG=1033 "OriginalFilename" "FoFiX v${FOFIX_VERSION_FULL} Setup.exe"
VIAddVersionKey /LANG=1033 "ProductName" "FoFiX"
VIAddVersionKey /LANG=1033 "ProductVersion" "${FOFIX_VERSION_FULL}"
""" % (FOFIX_VERSION, FOFIX_VERSION_FULL))

builder.addSection('FoFiX Core', r'''
SectionIn RO
%s
WriteRegStr HKCU "SOFTWARE\myfingershurt\FoFiX" InstallRoot $INSTDIR
WriteUninstaller uninst.exe
CreateDirectory "$SMPROGRAMS\FoFiX"
CreateShortcut "$SMPROGRAMS\FoFiX\FoFiX.lnk" "$INSTDIR\FretsOnFire.exe"
CreateShortcut "$SMPROGRAMS\FoFiX\FoFiX Installation Folder.lnk" "$INSTDIR"
CreateShortcut "$SMPROGRAMS\FoFiX\Uninstall FoFiX.lnk" "$INSTDIR\uninst.exe"
''' % MLDist.getInstallScript(), r'''
%s
Delete "$SMPROGRAMS\FoFiX\FoFiX.lnk"
Delete "$SMPROGRAMS\FoFiX\FoFiX Installation Folder.lnk"
Delete "$SMPROGRAMS\FoFiX\Uninstall FoFiX.lnk"
RmDir "$SMPROGRAMS\FoFiX"
Delete "$INSTDIR\uninst.exe"
DeleteRegValue HKCU "SOFTWARE\myfingershurt\FoFiX" InstallRoot
DeleteRegKey /ifempty HKCU "SOFTWARE\myfingershurt\FoFiX"
DeleteRegKey /ifempty HKCU "SOFTWARE\myfingershurt"
RmDir "$INSTDIR"
''' % MLDist.getUninstallScript(), 'Installs the core of FoFiX (required).')
builder.filterSection('MegaLight GH3', r'data\themes\MegaLight GH3', 'Installs the MegaLight GH3 theme.', secStart='SectionGroup /e "Themes"\r\nSection')
builder.filterSection('MegaLight', r'data\themes\MegaLight', 'Installs the MegaLight theme.', secEnd='SectionEnd\r\nSectionGroupEnd')
builder.filterSection('Low Poly CD List', r'data\mods\Low Poly CD List', 'Installs less complex CD meshes for the song list.', secStart='SectionGroup /e "Mods"\r\nSection')
builder.filterSection('MegaLight RB Notes', r'data\mods\MegaLight RB Notes', 'Installs Rock Band-like notes for the MegaLight theme.', secEnd='SectionEnd\r\nSectionGroupEnd')
builder.filterSection('Jurgen Tutorial', r'data\tutorials\jurgenfof', 'Installs the tutorial from the original Frets on Fire.', secStart='SectionGroup /e "Tutorials"\r\nSection')
builder.filterSection('Bang Bang, Mystery Man', r'data\tutorials\bangbang', r'Installs $\"Bang Bang, Mystery Man$\" as a tutorial song.')
builder.filterSection('Drum Test Song', r'data\tutorials\drumtest', 'Installs a short song for testing drum functionality.', secStart='Section /o', secEnd='SectionEnd\r\nSectionGroupEnd')
builder.filterSection('Stock Necks', r'data\necks\Neck_', 'Installs all stock guitar neck images.', instHeader='SetOutPath "$INSTDIR\\data\\necks"\r\n')
builder.filterSection('Source Code', 'src', 'Installs the FoFiX source code.', secStart='Section /o')
builder.filterSection('Wiki Pages', 'FoFiX-wiki', 'Installs the FoFiX wiki pages.', secStart='Section /o')

# Unfortunately the installer graphics can only be BMPs, which are enormous.
# Make them now out of PNGs that we'll do the real work with.
# gfx pending
#from PIL import Image
#bkgd = Image.open(os.path.join('pkg', 'installer_gfx', 'background.png'))
#bkgd.convert('RGB').save(os.path.join('pkg', 'installer_gfx', 'background.bmp'))

# Generate and compile the NSIS script.
open('Setup.nsi', 'w').write(builder.getScript())
if os.path.isfile('fretsonfire.ini'):
  os.rename('fretsonfire.ini', 'fretsonfire.bak')
shutil.copy(os.path.join('pkg', 'fretsonfire.fresh.ini'), 'fretsonfire.ini')
os.spawnl(os.P_WAIT, makensis, 'makensis.exe', 'Setup.nsi')
os.unlink('fretsonfire.ini')
if os.path.isfile('fretsonfire.bak'):
  os.rename('fretsonfire.bak', 'fretsonfire.ini')
os.unlink('Setup.nsi')

# gfx pending
#os.unlink(os.path.join('pkg', 'installer_gfx', 'background.bmp'))