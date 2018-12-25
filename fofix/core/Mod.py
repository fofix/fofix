#####################################################################
# -*- coding: utf-8 -*-                                             #
#                                                                   #
# Frets on Fire                                                     #
# Copyright (C) 2006 Sami Ky?stil?                                  #
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

import logging
import os

from fofix.core.Language import _
from fofix.core import Config
from fofix.core import Theme


log = logging.getLogger(__name__)


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
    try:
        dirList = os.listdir(modPath)
    except OSError:
        log.warning("Could not find mods directory")
        return []
    return [m for m in dirList if os.path.isdir(os.path.join(modPath, m)) and not m.startswith(".")]

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
