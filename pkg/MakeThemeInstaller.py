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
import sys
if os.name != 'nt':
  sys.stderr.write('This script works only on Windows.\n')
  sys.exit(1)

from Tkinter import *

try:
  import sqlite3
except ImportError:
  import pysqlite2.dbapi2 as sqlite3

import _winreg
import win32api
import win32con
import win32gui
import pywintypes

class ThemeSelectWindow(object):
  def __init__(self, master, themelist):
    self.master = master
    master.title('Theme Installer Generator')
    master.protocol('WM_DELETE_WINDOW', lambda: sys.exit(0))
    frame = Frame(master)

    lbl = Label(master, text='Choose theme to package:')
    lbl.pack(side=TOP, padx=10, pady=10)

    self.listbox = Listbox(master, exportselection=0)
    for theme in themelist:
      self.listbox.insert(END, theme)
    self.listbox.bind('<Double-Button-1>', lambda e: self.ok())
    self.listbox.pack(side=TOP, padx=10, pady=0)

    okbutton = Button(master, text='OK', command=self.ok)
    okbutton.pack(side=TOP, padx=10, pady=10, fill=BOTH, expand=1)

    master.resizable(0, 0)

  def run(self):
    self.master.mainloop()
    return self.listbox.get(self.listbox.curselection()[0])

  def ok(self):
    if len(self.listbox.curselection()):
      self.master.withdraw()
      self.master.quit()


class VersionSelectWindow(object):
  def __init__(self, master):
    self.master = master
    master.title('Theme Installer Generator')
    master.protocol('WM_DELETE_WINDOW', lambda: sys.exit(0))
    frame = Frame(master)

    lbl = Label(master, text='Version number:')
    lbl.pack(side=TOP, padx=10, pady=10)

    self.entry = Entry(master)
    self.entry.bind('<Return>', lambda e: self.ok())
    self.entry.pack(side=TOP, padx=10, pady=0)

    okbutton = Button(master, text='OK', command=self.ok)
    okbutton.pack(side=TOP, padx=10, pady=10, fill=BOTH, expand=1)

    master.resizable(0, 0)

  def run(self):
    self.master.mainloop()
    return self.entry.get()

  def ok(self):
    if self.entry.get() != '':
      self.master.withdraw()
      self.master.quit()


def main():
  # Find NSIS.
  try:
    key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, r'Software\NSIS')
    nsisPath = _winreg.QueryValueEx(key, '')[0]
    _winreg.CloseKey(key)
  except WindowsError:
    win32api.MessageBox(0, '''To create theme installers, you must have NSIS installed on your system.

NSIS is needed to create theme installers, but not to use them.

NSIS is free software that can be downloaded from http://nsis.sourceforge.net/.''',
      'Theme Installer Generator', win32con.MB_OK|win32con.MB_ICONSTOP)
    sys.exit(1)
  makensis = os.path.join(nsisPath, 'makensis.exe')

  # Find possible themes.
  themes = []
  os.chdir(os.path.join('..', 'data', 'themes'))
  for name in os.listdir('.'):
    if os.path.isfile(os.path.join(name, 'theme.ini')):
      themes.append(name)

  # Get the theme and its version number.
  themesel = ThemeSelectWindow(Tk(), themes)
  theme = themesel.run()

  versel = VersionSelectWindow(Tk())
  version = versel.run()

  # Allow a license agreement to be added.
  if win32api.MessageBox(0, 'Would you like to display a license agreement in the installer?',
    'Theme Installer Generator', win32con.MB_YESNO|win32con.MB_ICONQUESTION) == win32con.IDYES:
      try:
        licensefile = win32gui.GetOpenFileNameW(
          Filter='License Agreements (COPYING,LICENSE,*.txt,*.rtf)\0COPYING;LICENSE;*.txt;*.rtf\0All Files (*.*)\0*.*\0',
          Title='Theme Installer Generator: Select license agreement',
          Flags=win32con.OFN_DONTADDTORECENT|win32con.OFN_FILEMUSTEXIST|win32con.OFN_HIDEREADONLY|win32con.OFN_NOCHANGEDIR)[0]
      except pywintypes.error:
        sys.exit(0)
  else:
      licensefile = None

  # Where are we putting this?
  try:
    destfile = win32gui.GetSaveFileNameW(
      Filter='Executable files (*.exe)\0*.exe\0All Files (*.*)\0*.*\0',
      Title='Theme Installer Generator: Save installer',
      Flags=win32con.OFN_DONTADDTORECENT|win32con.OFN_OVERWRITEPROMPT|win32con.OFN_HIDEREADONLY|win32con.OFN_NOCHANGEDIR)[0]
  except pywintypes.error:
    sys.exit(0)

  # Let's do this.
  script = r"""
!define THEME_NAME "%s"
!define THEME_VERSION "%s"
!include "MUI2.nsh"

# Installer title and filename.
Name 'FoFiX Theme "${THEME_NAME}" v${THEME_VERSION}'
OutFile '%s'

# Installer parameters.
SetCompressor /SOLID lzma
RequestExecutionLevel user  # no UAC on Vista
ShowInstDetails show

# Where we're going (by default at least)
InstallDir '$DOCUMENTS\FoFiX'
# Where we stashed the install location.
InstallDirRegKey HKCU 'SOFTWARE\myfingershurt\FoFiX' InstallRoot

# Function to run FoFiX from the finish page.
Function runFoFiX
  SetOutPath $INSTDIR
  Exec $INSTDIR\FoFiX.exe
FunctionEnd

# More installer parameters.
!define MUI_ABORTWARNING
!define MUI_FINISHPAGE_NOAUTOCLOSE
!define MUI_FINISHPAGE_NOREBOOTSUPPORT
!define MUI_FINISHPAGE_RUN
!define MUI_FINISHPAGE_RUN_TEXT "Run FoFiX"
!define MUI_FINISHPAGE_RUN_FUNCTION runFoFiX
!define MUI_LICENSEPAGE_RADIOBUTTONS
!define MUI_HEADERIMAGE
!define MUI_FINISHPAGE_TEXT "FoFiX Theme $\"${THEME_NAME}$\" v${THEME_VERSION} has been installed on your computer.$\r$\n$\r$\nClick Finish to close this wizard.$\r$\n$\r$\nInstaller framework by John Stumpo."
!define MUI_FINISHPAGE_TEXT_LARGE
# gfx pending
#!define MUI_HEADERIMAGE_BITMAP "pkg\installer_gfx\header.bmp"

# Function to verify the install path.
Function verifyFoFiXInstDir
  IfFileExists $INSTDIR haveDir
  Abort
haveDir:
  IfFileExists $INSTDIR\FoFiX.exe allow
  MessageBox MB_YESNO|MB_ICONEXCLAMATION "This does not look like a valid FoFiX installation folder.$\r$\n$\r$\nIf you would like to merely unpack the theme files into this folder, you may continue anyway.$\r$\n$\r$\nContinue?" IDYES allow
  Abort
allow:
FunctionEnd

# The pages of the installer...
!insertmacro MUI_PAGE_WELCOME
%s
!define MUI_PAGE_CUSTOMFUNCTION_LEAVE verifyFoFiXInstDir
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

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

Section
""" % tuple(map(str, (theme, version, destfile, licensefile and ('!insertmacro MUI_PAGE_LICENSE "%s"' % licensefile) or '')))
  for root, dirs, files in os.walk(theme):
    if root.find('.svn') != -1:  #stump: skip .svn folders
      continue
    script += 'SetOutPath "$INSTDIR\\data\\themes\\%s\\%s"\r\n' % (theme, root[len(theme):])
    for f in files:
      script += 'File "%s"\r\n' % os.path.join(root, f)
  script += 'SetOutPath $INSTDIR\r\nSectionEnd\r\n'
  open('Setup.nsi', 'w').write(script)
  if os.spawnl(os.P_WAIT, makensis, 'makensis.exe', 'Setup.nsi') != 0:
    raise RuntimeError, 'Installer generation failed.'
  os.unlink('Setup.nsi')
  win32api.MessageBox(0, 'Installer generation complete.', 'Theme Installer Generator',
    win32con.MB_OK|win32con.MB_ICONINFORMATION)

try:
  main()
except (KeyboardInterrupt, SystemExit):
  raise
except:
  import traceback
  import win32clipboard
  if win32api.MessageBox(0, 'A fatal error has occurred.  This program will now terminate.\n\n' +
    traceback.format_exc() + '\n\nCopy traceback to Clipboard?',
    'Theme Installer Generator', win32con.MB_YESNO|win32con.MB_ICONSTOP) == win32con.IDYES:
      win32clipboard.OpenClipboard()
      win32clipboard.EmptyClipboard()
      win32clipboard.SetClipboardText(traceback.format_exc())
      win32clipboard.CloseClipboard()      
  raise
