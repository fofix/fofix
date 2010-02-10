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

'''Functions for working with WinRAR listfiles and
converting them to NSIS script instructions.'''

__version__ = '$Id$'

import os
import win32api
import fnmatch
import hashlib

class NsisScriptGenerator(object):
  def __init__(self, baseFolder='.', hashCache=None, oldTblName=None, newTblName=None):
    self.nodeList = []
    self.baseFolder = baseFolder
    self.hashCache = hashCache
    self.oldTblName = None
    self.newTblName = None
    if oldTblName is not None:
      self.oldTblName = hashlib.sha1(oldTblName).hexdigest()
    if newTblName is not None:
      self.newTblName = hashlib.sha1(newTblName).hexdigest()
    if self.hashCache is not None:
      self.hashCache.execute('INSERT OR REPLACE INTO `verlist` (`version`) VALUES (?)', [newTblName])
      self.hashCache.execute('DROP TABLE IF EXISTS `hashes_%s`' % self.newTblName)
      self.hashCache.commit()
      self.hashCache.execute('VACUUM')
      self.hashCache.execute('CREATE TABLE `hashes_%s` (`path` STRING UNIQUE, `hash` STRING)' % self.newTblName)
      self.hashCache.commit()
  def readList(self, listname):
    l = open(listname, 'r')
    for line in l:
      line = line.partition('//')[0].strip()  # remove comments
      if not len(line):
        continue
      if line[0] == '"' and line[-1] == '"':
        line = line[1:-1]
      oldpwd = os.getcwd()
      os.chdir(self.baseFolder)
      if os.path.dirname(line) == '' or os.path.isdir(os.path.dirname(line)):
        for f in win32api.FindFiles(line):
          path = os.path.join(os.path.dirname(line), f[8])
          if os.path.isfile(path) and path.find('.svn') == -1:  # omit .svn folders
            if self.hashCache is not None:
              newhash = hashlib.sha1(open(path, 'rb').read()).hexdigest()
              self.hashCache.execute('INSERT OR REPLACE INTO `hashes_%s` (`path`, `hash`) VALUES (?, ?)' % self.newTblName, [path, newhash])
              if self.oldTblName is not None:
                oldhash = self.hashCache.execute('SELECT `hash` FROM `hashes_%s` WHERE `path` = ?' % self.oldTblName, [path]).fetchone()
                if oldhash is not None and oldhash[0] == newhash:
                  continue
            self.nodeList.append(path)
      os.chdir(oldpwd)
    l.close()
  def readExcludeList(self, listname):
    patterns = []
    l = open(listname, 'r')
    for line in l:
      line = line.partition('//')[0].strip()  # remove comments
      if not len(line):
        continue
      if line[0] == '"' and line[-1] == '"':
        line = line[1:-1]
      patterns.append(line)
    l.close()
    for p in patterns:
      self.nodeList = [n for n in self.nodeList if not fnmatch.fnmatch(n.lower(), p.lower())]
  def getInstallScript(self):
    prevFolder = None
    script = ''
    for f in self.nodeList:
      if os.path.dirname(f) != prevFolder:
        script += 'SetOutPath "$INSTDIR\\%s"\r\n' % os.path.dirname(f).replace('..\\', '')
        prevFolder = os.path.dirname(f)
      script += 'File "%s"\r\n' % f
    script += 'SetOutPath "$INSTDIR"\r\n'
    return script
  def getUninstallScript(self):
    prevFolder = None
    script = ''
    for f in reversed(self.nodeList):
      if os.path.dirname(f) != prevFolder:
        if prevFolder is not None:
          p = prevFolder.replace('..\\', '')
          while len(p):
            script += 'RmDir "$INSTDIR\\%s"\r\n' % p
            p = os.path.dirname(p)
        prevFolder = os.path.dirname(f)
      script += 'Delete "$INSTDIR\\%s"\r\n' % f.replace('..\\', '')
    if prevFolder is not None:
      script += 'RmDir "$INSTDIR\\%s"\r\n' % prevFolder.replace('..\\', '')
    return script

def separate(path, scriptIn):
  scriptOut = ([], [])
  for l in scriptIn.splitlines():
    if l.lower().find(path.lower()) == -1:
      scriptOut[0].append(l)
    else:
      scriptOut[1].append(l)
  return ('\r\n'.join(x) for x in scriptOut)

class NsisScriptBuilder(object):
  def __init__(self, header):
    self.header = header
    self.sectionScripts = []
  def addSection(self, secName, secInstContent, secUninstContent, secDescription, secStart='Section', secEnd='SectionEnd'):
    self.sectionScripts.append([secName, secInstContent, secUninstContent, secDescription, secStart, secEnd])
  def filterSection(self, secName, secFilter, secDescription, secStart='Section', secEnd='SectionEnd', instHeader='', instFooter='', uninstHeader='', uninstFooter=''):
    self.sectionScripts[0][1], instContent = separate(secFilter, self.sectionScripts[0][1])
    self.sectionScripts[0][2], uninstContent = separate(secFilter, self.sectionScripts[0][2])
    self.addSection(secName, instHeader+instContent+instFooter, uninstHeader+uninstContent+uninstFooter, secDescription, secStart, secEnd)
  def getScript(self):
    script = self.header
    for name, instContent, uninstContent, desc, start, end in self.sectionScripts:
      script += '''
%s "%s" SecID_%s
%s
%s
''' % (start, name, hashlib.sha1(name).hexdigest(), instContent, end)
    script += '!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN\r\n'
    for name, instContent, uninstContent, desc, start, end in self.sectionScripts:
      script += '!insertmacro MUI_DESCRIPTION_TEXT ${SecID_%s} "%s"\r\n' % (hashlib.sha1(name).hexdigest(), desc)
    script += '!insertmacro MUI_FUNCTION_DESCRIPTION_END\r\n'
    for name, instContent, uninstContent, desc, start, end in reversed(self.sectionScripts):
      script += '''
Section "un.%s"
%s
SectionEnd
''' % (name, uninstContent)
    return script
