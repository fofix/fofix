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


def _get_mods_path(engine):
    """Get the path of mods"""
    return engine.resource.fileName("mods")


def init(engine):
    """Init mods"""
    # define configuration keys for all available mods
    for mod_name in get_available_mods(engine):
        Config.define("mods", "mod_" + mod_name, bool, False, text=mod_name, options={False: _("Off"), True: _("On")})

    # init all active mods
    for mod in get_active_mods(engine):
        activate_mod(engine, mod)


def get_available_mods(engine):
    """Get available mods"""
    mods_path = _get_mods_path(engine)
    try:
        dir_list = os.listdir(mods_path)
    except OSError:
        log.warning("Could not find mods directory")
        return []
    return [mod for mod in dir_list if os.path.isdir(os.path.join(mods_path, mod)) and not mod.startswith(".")]


def get_active_mods(engine):
    """Get active mods"""
    mods = []
    for mod_name in get_available_mods(engine):
        if engine.config.get("mods", "mod_" + mod_name):
            mods.append(mod_name)
    mods.sort()
    return mods


def activate_mod(engine, mod_name):
    """Activate a mod"""
    # get the path of the mod
    mods_path = _get_mods_path(engine)
    mod_path = os.path.join(mods_path, mod_name)
    theme_mod_path = os.path.join(mod_path, "theme.ini")

    # add the path to resource data
    if os.path.isdir(mod_path):
        engine.resource.addDataPath(mod_path)
        # activate the mod
        engine.config.set("mods", "mod_" + mod_name, True)
        # load the theme of the mod
        if os.path.isfile(theme_mod_path):
            theme = Config.load(theme_mod_path)
            Theme.open(theme)


def deactivate_mod(engine, mod_name):
    """Deactivate a mod"""
    # get the path of the mod
    mods_path = _get_mods_path(engine)
    mod_path = os.path.join(mods_path, mod_name)
    # remove the path from resource data
    engine.resource.removeDataPath(mod_path)
    # deactivate the mod
    engine.config.set("mods", "mod_" + mod_name, False)
