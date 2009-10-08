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
  sys.stderr.write('This script only works on Windows.\n')
  sys.exit(1)

import win32api
import win32con
import sha
try:
  import sqlite3
except ImportError:
  import pysqlite2.dbapi2 as sqlite3

from Tkinter import *

class CleanHashCacheWindow(object):
  def __init__(self, master, db):
    self.master = master
    self.db = db
    master.title('CleanHashCache')
    master.protocol('WM_DELETE_WINDOW', self.close)
    frame = Frame(master)

    lbl = Label(master, text='Double-click a version\nto delete its hashes.')
    lbl.pack(side=TOP, padx=10, pady=10)

    self.listbox = Listbox(master, exportselection=0)
    for version in [row[0] for row in self.db.execute('SELECT `version` FROM `verlist`').fetchall()]:
      self.listbox.insert(END, version)
    self.listbox.bind('<Double-Button-1>', lambda e: self.delete())
    self.listbox.pack(side=TOP, padx=10, pady=0)

    okbutton = Button(master, text='Done', command=self.close)
    okbutton.pack(side=TOP, padx=10, pady=10, fill=BOTH, expand=1)

    master.resizable(0, 0)

  def run(self):
    self.master.mainloop()

  def delete(self):
    if len(self.listbox.curselection()):
      if win32api.MessageBox(self.master.winfo_id(),
        'Really delete this version\'s hashes?\nThis cannot be undone!',
        'CleanHashCache', win32con.MB_YESNO|win32con.MB_ICONQUESTION) == win32con.IDYES:
          vername = str(self.listbox.get(self.listbox.curselection()[0]))
          self.db.execute('DELETE FROM `verlist` WHERE `version` = ?', [vername])
          self.db.commit()
          self.db.execute('DROP TABLE `hashes_%s`' % sha.sha(vername).hexdigest())
          self.db.commit()
          self.listbox.delete(self.listbox.curselection()[0])

  def close(self):
    self.db.commit()
    self.db.execute('VACUUM')
    self.db.commit()
    self.db.close()
    self.master.withdraw()
    self.master.quit()

def main():
  hashcache = sqlite3.Connection('HashCache')
  hashcache.execute('CREATE TABLE IF NOT EXISTS `verlist` (`version` STRING UNIQUE)')
  hashcache.commit()
  CleanHashCacheWindow(Tk(), hashcache).run()
  sys.exit(0)

try:
  main()
except (KeyboardInterrupt, SystemExit):
  raise
except:
  import traceback
  import win32clipboard
  if win32api.MessageBox(0, 'A fatal error has occurred.  This program will now terminate.\n\n' +
    traceback.format_exc() + '\n\nCopy traceback to Clipboard?',
    'CleanHashCache', win32con.MB_YESNO|win32con.MB_ICONSTOP) == win32con.IDYES:
      win32clipboard.OpenClipboard()
      win32clipboard.EmptyClipboard()
      win32clipboard.SetClipboardText(traceback.format_exc())
      win32clipboard.CloseClipboard()      
  raise
