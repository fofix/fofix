#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire                                                     #
# Copyright (C) 2006 Sami Kyöstilä                                  #
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

import os
import Config
import Theme
from Language import _

def _getModPath(engine):
  return engine.resource.fileName("mods")

def init(engine):
  # define configuration keys for all available mods
  for m in getAvailableMods(engine):
    Config.define("mods", "mod_" + m, bool, False, text = m,  options = {False: _("Off"), True: _("On")})

  # init all active mods
  for m in getActiveMods(engine):
    activateMod(engine, m)

def getAvailableMods(engine):
  modPath = _getModPath(engine)
  return [m for m in os.listdir(modPath) if os.path.isdir(os.path.join(modPath, m)) and not m.startswith(".")]

def getActiveMods(engine):
  mods = []
  for mod in getAvailableMods(engine):
    if engine.config.get("mods", "mod_" + mod):
      mods.append(mod)
  mods.sort()
  return mods

def activateMod(engine, modName):
  modPath = _getModPath(engine)
  m = os.path.join(modPath, modName)
  t = os.path.join(m, "theme.ini")
  if os.path.isdir(m):
    engine.resource.addDataPath(m)
    if os.path.isfile(t):
      theme = Config.load(t)
      Theme.open(theme)


def deactivateMod(engine, modName):
  modPath = _getModPath(engine)
  m = os.path.join(modPath, modName)
  engine.resource.removeDataPath(m)
