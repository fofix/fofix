#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Tests for the module fofix.core.Mod"""

import os

from fofix.core import Mod
from fofix.core.GameEngine import GameEngine
from fofix.core import Config
from fofix.core import Version


def test_get_mods_path():
    # set the game engine
    config_filename = Version.PROGRAM_UNIXSTYLE_NAME + ".ini"
    config = Config.load(config_filename, setAsDefault=True)
    engine = GameEngine(config)
    # get mods path
    mods_path = Mod._get_mods_path(engine)

    assert mods_path == os.path.join(os.getcwd(), "data", "mods")


def test_init():
    # set the game engine
    config_filename = Version.PROGRAM_UNIXSTYLE_NAME + ".ini"
    config = Config.load(config_filename, setAsDefault=True)
    engine = GameEngine(config)
    # init mods
    Mod.init(engine)

    assert "mods" in Config.prototype


def test_get_available_mods():
    # set the game engine
    config_filename = Version.PROGRAM_UNIXSTYLE_NAME + ".ini"
    config = Config.load(config_filename, setAsDefault=True)
    engine = GameEngine(config)
    # get available mods
    available_mods = Mod.get_available_mods(engine)

    assert len(available_mods) > 0


def test_get_active_mods():
    # set the game engine
    config_filename = Version.PROGRAM_UNIXSTYLE_NAME + ".ini"
    config = Config.load(config_filename, setAsDefault=True)
    engine = GameEngine(config)
    # get active mods
    active_mods = Mod.get_active_mods(engine)
    assert len(active_mods) == 0

    # activate a mod
    mods = Mod.get_available_mods(engine)
    Mod.activate_mod(engine, mods[0])
    active_mods = Mod.get_active_mods(engine)
    assert len(active_mods) == 1
    assert mods[0] in active_mods

    # deactivate a mod
    Mod.deactivate_mod(engine, mods[0])
    active_mods = Mod.get_active_mods(engine)
    assert len(active_mods) == 0
    assert mods[0] not in active_mods
