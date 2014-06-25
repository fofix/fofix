#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire                                                     #
# Copyright (C) 2006 Sami Kyöstilä                                  #
#               2008 Alarian                                        #
#               2008 myfingershurt                                  #
#               2008 Spikehead777                                   #
#               2008 Glorandwarf                                    #
#               2008 ShiekOdaSandz                                  #
#               2008 QQStarS                                        #
#               2008 Blazingamer                                    #
#               2008 evilynux <evilynux@gmail.com>                  #
#               2008 fablaculp                                      #
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

from views import Menu
from core.Language import _
from views import Dialogs
from configuration import Config
from configuration import Mod
from game import Player
import Version
from views.View import BackgroundLayer
from Input import KeyListener
from game.Song import VOCAL_PART
from util import VFS

import pygame
import os

from util import Log

class ConfigChoice(Menu.Choice):
    def __init__(self, engine, config, section, option, autoApply = False, isQuickset = 0):
        self.engine    = engine
        self.config    = config

        self.logClassInits = self.engine.config.get("game", "log_class_inits")
        if self.logClassInits == 1:
            Log.debug("ConfigChoice class init (Settings.py)...")

        self.section    = section
        self.option     = option
        self.changed    = False
        self.value      = None
        self.autoApply  = autoApply
        self.isQuickset = isQuickset
        tipText = config.getTipText(section, option)
        o = config.prototype[section][option]
        v = config.get(section, option)
        if isinstance(o.options, dict):
            values     = o.options.values()
            values.sort()
            try:
                valueIndex = values.index(o.options[v])
            except KeyError:
                valueIndex = 0
        elif isinstance(o.options, list):
            values     = o.options
            try:
                valueIndex = values.index(v)
            except ValueError:
                valueIndex = 0
        else:
            raise RuntimeError("No usable options for %s.%s." % (section, option))
        Menu.Choice.__init__(self, text = o.text, callback = self.change, values = values, valueIndex = valueIndex, tipText = tipText)

    def change(self, value):
        o = self.config.prototype[self.section][self.option]

        if isinstance(o.options, dict):
            for k, v in o.options.items():
                if v == value:
                    value = k
                    break

        self.changed = True
        self.value   = value

        if self.isQuickset == 1: # performance quickset
            self.config.set("quickset","performance",0)
            self.engine.quicksetPerf = 0
        elif self.isQuickset == 2: # gameplay quickset
            self.config.set("quickset","gameplay",0)

        if self.section == "quickset":
            if self.option == "performance":
                if self.value == self.engine.quicksetPerf or self.value == 0:
                    self.engine.quicksetRestart = False
                else:
                    self.engine.quicksetRestart = True

        self.apply()  #stump: it wasn't correctly saving some "restart required" settings
        if not self.autoApply:
            self.engine.restartRequired = True

    def apply(self):
        if self.changed:
            self.config.set(self.section, self.option, self.value)

class ActiveConfigChoice(ConfigChoice):
    """
    ConfigChoice with an additional callback function.
    """
    def __init__(self, engine, config, section, option, onChange, autoApply = True, volume = False):
        ConfigChoice.__init__(self, engine, config, section, option, autoApply = autoApply)
        self.engine   = engine
        self.onChange = onChange
        self.volume   = volume

        self.logClassInits = self.engine.config.get("game", "log_class_inits")
        if self.logClassInits == 1:
            Log.debug("ActiveConfigChoice class init (Settings.py)...")

    def change(self, value):
        ConfigChoice.change(self, value)
        if self.volume:
            sound = self.engine.data.screwUpSound
            sound.setVolume(self.value)
            sound.play()

    def apply(self):
        ConfigChoice.apply(self)
        self.onChange()

class VolumeConfigChoice(ConfigChoice):
    def __init__(self, engine, config, section, option, autoApply = False):
        ConfigChoice.__init__(self, engine, config, section, option, autoApply)
        self.engine = engine

        self.logClassInits = self.engine.config.get("game", "log_class_inits")
        if self.logClassInits == 1:
            Log.debug("VolumeConfigChoice class init (Settings.py)...")


    def change(self, value):
        ConfigChoice.change(self, value)
        sound = self.engine.data.screwUpSound
        sound.setVolume(self.value)
        sound.play()

class KeyConfigChoice(Menu.Choice):
    def __init__(self, engine, config, section, option, noneOK = False, shift = None):
        self.engine  = engine

        self.logClassInits = self.engine.config.get("game", "log_class_inits")
        if self.logClassInits == 1:
            Log.debug("KeyConfigChoice class init (Settings.py)...")

        self.config  = config
        self.section = section
        self.option  = option
        self.changed = False
        self.value   = None
        self.noneOK  = noneOK
        self.shift   = shift
        self.type    = self.config.get("controller", "type")
        self.name    = self.config.get("controller", "name")
        self.frets   = []

        def keycode(k):
            try:
                return int(k)
            except:
                return getattr(pygame, k)

        if self.shift:
            self.frets.append(keycode(self.config.get("controller", "key_1")))
            self.frets.append(keycode(self.config.get("controller", "key_2")))
            self.frets.append(keycode(self.config.get("controller", "key_3")))
            self.frets.append(keycode(self.config.get("controller", "key_4")))
            self.frets.append(keycode(self.config.get("controller", "key_5")))

        self.keyCheckerMode = self.config.get("game","key_checker_mode")

        self.option = self.option

        Menu.Choice.__init__(self, text = "", callback = self.change)

    def getText(self, selected):
        def keycode(k):
            try:
                return int(k)
            except:
                return getattr(pygame, k)
        o = self.config.prototype[self.section][self.option]
        v = self.config.get(self.section, self.option)
        if isinstance(o.text, tuple):
            type = self.type
            if len(o.text) == 5:
                text = o.text[type]
            else:
                if type == 4:
                    type = 0
            if len(o.text) == 4:
                text = o.text[type]
            elif len(o.text) == 3:
                text = o.text[max(0, type-1)]
            elif len(o.text) == 2:
                if type < 2:
                    text = o.text[0]
                else:
                    text = o.text[1]
        else:
            text = o.text
        if v == "None":
            keyname = "Disabled"
        else:
            keyname = pygame.key.name(keycode(v)).capitalize()
        return "%s: %s" % (text, keyname)

    def change(self):
        o = self.config.prototype[self.section][self.option]

        if isinstance(o.text, tuple):
            type = self.type
            if len(o.text) == 5:
                text = o.text[type]
            else:
                if type == 4:
                    type = 0
            if len(o.text) == 4:
                text = o.text[type]
            elif len(o.text) == 3:
                text = o.text[max(0, type-1)]
            elif len(o.text) == 2:
                if type < 2:
                    text = o.text[0]
                else:
                    text = o.text[1]
        else:
            text = o.text
        if self.shift:
            key = Dialogs.getKey(self.engine, self.shift, specialKeyList = self.frets)
        else:
            if self.noneOK:
                key = Dialogs.getKey(self.engine, _("Press a key for '%s' or hold Escape to disable.") % text)
            else:
                key = Dialogs.getKey(self.engine, _("Press a key for '%s' or hold Escape to cancel.") % text)

        if key:
            Player.setNewKeyMapping(self.engine, self.config, self.section, self.option, key)
            if self.name in self.engine.input.controls.controlList:
                self.engine.input.reloadControls()
        else:
            if self.noneOK:
                Player.setNewKeyMapping(self.engine, self.config, self.section, self.option, "None")
                if self.name in self.engine.input.controls.controlList:
                    self.engine.input.reloadControls()

    def apply(self):
        pass

def chooseControl(engine, mode = "edit", refresh = None):
    """
    Ask the user to choose a controller for editing or deletion.

    @param engine:    Game engine
    @param mode:      "edit" or "delete" controller
    """
    mode     = mode == "delete" and 1 or 0
    options  = []
    for i in Player.controllerDict.keys():
        if i != "defaultg" and i != "None" and i != "defaultd" and i != "defaultm":
            options.append(i)
    options.sort()
    if len(options) == 0:
        Dialogs.showMessage(engine, _("No Controllers Found."))
        return
    d = ControlChooser(engine, mode, options)
    Dialogs._runDialog(engine, d)
    if refresh:
        refresh()

def createControl(engine, control = "", edit = False, refresh = None):
    d = ControlCreator(engine, control, edit = edit)
    Dialogs._runDialog(engine, d)
    if refresh:
        refresh()

class ControlChooser(Menu.Menu):
    def __init__(self, engine, mode, options):
        self.engine  = engine
        self.mode    = mode
        self.options = options
        self.default = self.engine.config.get("game", "control0")

        self.logClassInits = self.engine.config.get("game", "log_class_inits")
        if self.logClassInits == 1:
            Log.debug("ControlChooser class init (Settings.py)...")

        self.selected = None
        self.d        = None
        self.creating = False
        self.time     = 0.0

        Menu.Menu.__init__(self, self.engine, choices = [(c, self._callbackForItem(c)) for c in options])
        if self.default in options:
            self.selectItem(options.index(self.default))

    def _callbackForItem(self, item):
        def cb():
            self.choose(item)
        return cb

    def choose(self, item):
        self.selected = item
        if self.mode == 0:
            createControl(self.engine, self.selected, edit = True)
            self.engine.view.popLayer(self)
        else:
            self.delete(self.selected)

    def delete(self, item):
        tsYes = _("Yes")
        q = Dialogs.chooseItem(self.engine, [tsYes, _("No")], _("Are you sure you want to delete this controller?"))
        if q == tsYes:
            Player.deleteControl(item)
            self.engine.view.popLayer(self)

class ControlCreator(BackgroundLayer, KeyListener):
    def __init__(self, engine, control = "", edit = False):
        self.engine  = engine
        self.control = control
        self.edit    = edit
        self.logClassInits = self.engine.config.get("game", "log_class_inits")
        if self.logClassInits == 1:
            Log.debug("ControlCreator class init (Settings.py)...")

        self.time   = 0.0
        self.badname     = ["defaultg", "defaultd", "defaultm"] #ensures that defaultm is included - duplicate is ok
        for i in Player.controllerDict.keys():
            self.badname.append(i.lower())

        self.menu = None
        self.config = None

    def shown(self):
        while (self.control.strip().lower() in self.badname or self.control.strip() == "") and not self.edit:
            self.control = Dialogs.getText(self.engine, _("Please name your controller"), self.control)
            if self.control.strip().lower() in self.badname:
                Dialogs.showMessage(self.engine, _("That name is already taken."))
            elif self.control.strip() == "":
                Dialogs.showMessage(self.engine, _("Canceled."))
                self.cancel()
                break
        else:
            self.setupMenu()

    def cancel(self):
        Player.loadControls()
        self.engine.input.reloadControls()
        self.engine.view.popLayer(self.menu)
        self.engine.view.popLayer(self)

    def setupMenu(self):
        self.config = None
        #stump: Temporary use of private stuff in Player until we complete the VFS transition in Config.
        if not VFS.isfile(Player._makeControllerIniName(self.control)):
            cr = VFS.open(Player._makeControllerIniName(self.control), "w")
            cr.close()
        self.config = Config.load(VFS.resolveWrite(Player._makeControllerIniName(self.control)), type = 1)
        name = self.config.get("controller", "name")
        if name != self.control:
            self.config.set("controller", "name", self.control)
        type = self.config.get("controller", "type")

        if type != 5:
            if str(self.config.get("controller", "key_1")) == "None":
                self.config.set("controller", "key_1", self.config.getDefault("controller", "key_1"))
            if str(self.config.get("controller", "key_2")) == "None":
                self.config.set("controller", "key_2", self.config.getDefault("controller", "key_2"))
            if str(self.config.get("controller", "key_3")) == "None":
                self.config.set("controller", "key_3", self.config.getDefault("controller", "key_3"))
            if str(self.config.get("controller", "key_4")) == "None":
                self.config.set("controller", "key_4", self.config.getDefault("controller", "key_4"))
            if str(self.config.get("controller", "key_action1")) == "None":
                self.config.set("controller", "key_action1", self.config.getDefault("controller", "key_action1"))
            if str(self.config.get("controller", "key_action2")) == "None":
                self.config.set("controller", "key_action2", self.config.getDefault("controller", "key_action2"))

        if type == 0:
            self.config.set("controller", "key_1a", None)
            if str(self.config.get("controller", "key_5")) == "None":
                self.config.set("controller", "key_5", self.config.getDefault("controller", "key_5"))
            if str(self.config.get("controller", "key_kill")) == "None":
                self.config.set("controller", "key_kill", self.config.getDefault("controller", "key_kill"))
            controlKeys = [
              ActiveConfigChoice(self.engine, self.config, "controller", "type", self.changeType),
              KeyConfigChoice(self.engine, self.config, "controller", "key_action1"),
              KeyConfigChoice(self.engine, self.config, "controller", "key_action2"),
              KeyConfigChoice(self.engine, self.config, "controller", "key_1"),
              KeyConfigChoice(self.engine, self.config, "controller", "key_2"),
              KeyConfigChoice(self.engine, self.config, "controller", "key_3"),
              KeyConfigChoice(self.engine, self.config, "controller", "key_4"),
              KeyConfigChoice(self.engine, self.config, "controller", "key_5"),
              KeyConfigChoice(self.engine, self.config, "controller", "key_1a", True),
              KeyConfigChoice(self.engine, self.config, "controller", "key_2a", True),
              KeyConfigChoice(self.engine, self.config, "controller", "key_3a", True),
              KeyConfigChoice(self.engine, self.config, "controller", "key_4a", True),
              KeyConfigChoice(self.engine, self.config, "controller", "key_5a", True),
              KeyConfigChoice(self.engine, self.config, "controller", "key_left", True),
              KeyConfigChoice(self.engine, self.config, "controller", "key_right", True),
              KeyConfigChoice(self.engine, self.config, "controller", "key_up", True),
              KeyConfigChoice(self.engine, self.config, "controller", "key_down", True),
              KeyConfigChoice(self.engine, self.config, "controller", "key_cancel"),
              KeyConfigChoice(self.engine, self.config, "controller", "key_start"),
              KeyConfigChoice(self.engine, self.config, "controller", "key_star", True),
              KeyConfigChoice(self.engine, self.config, "controller", "key_kill"),
              ConfigChoice(   self.engine, self.config, "controller", "analog_kill", autoApply = True),
              ConfigChoice(   self.engine, self.config, "controller", "analog_sp", autoApply = True),
              ConfigChoice(   self.engine, self.config, "controller", "analog_sp_threshold", autoApply = True),
              ConfigChoice(   self.engine, self.config, "controller", "analog_sp_sensitivity", autoApply = True),
              #ConfigChoice(   self.engine, self.config, "controller", "analog_fx", autoApply = True), #FIXME: Analog FX
              ConfigChoice(   self.engine, self.config, "controller", "two_chord_max", autoApply = True),
              (_("Rename Controller"), self.renameController),
            ]
        elif type == 1:
            self.config.set("controller", "key_2a", None)
            self.config.set("controller", "key_3a", None)
            self.config.set("controller", "key_4a", None)
            self.config.set("controller", "key_5a", None)
            if str(self.config.get("controller", "key_5")) == "None":
                self.config.set("controller", "key_5", self.config.getDefault("controller", "key_5"))
            if str(self.config.get("controller", "key_1a")) == "None":
                self.config.set("controller", "key_1a", self.config.getDefault("controller", "key_1a"))
            if str(self.config.get("controller", "key_kill")) == "None":
                self.config.set("controller", "key_kill", self.config.getDefault("controller", "key_kill"))

            controlKeys = [
              ActiveConfigChoice(self.engine, self.config, "controller", "type", self.changeType),
              KeyConfigChoice(self.engine, self.config, "controller", "key_action1"),
              KeyConfigChoice(self.engine, self.config, "controller", "key_action2"),
              KeyConfigChoice(self.engine, self.config, "controller", "key_1"),
              KeyConfigChoice(self.engine, self.config, "controller", "key_2"),
              KeyConfigChoice(self.engine, self.config, "controller", "key_3"),
              KeyConfigChoice(self.engine, self.config, "controller", "key_4"),
              KeyConfigChoice(self.engine, self.config, "controller", "key_5"),
              KeyConfigChoice(self.engine, self.config, "controller", "key_1a", shift = _("Press the solo shift key. Be sure to assign the frets first! Hold Escape to cancel.")),
              KeyConfigChoice(self.engine, self.config, "controller", "key_left", True),
              KeyConfigChoice(self.engine, self.config, "controller", "key_right", True),
              KeyConfigChoice(self.engine, self.config, "controller", "key_up", True),
              KeyConfigChoice(self.engine, self.config, "controller", "key_down", True),
              KeyConfigChoice(self.engine, self.config, "controller", "key_cancel"),
              KeyConfigChoice(self.engine, self.config, "controller", "key_start"),
              KeyConfigChoice(self.engine, self.config, "controller", "key_star", True),
              KeyConfigChoice(self.engine, self.config, "controller", "key_kill"),
              ConfigChoice(   self.engine, self.config, "controller", "analog_kill", autoApply = True),
              ConfigChoice(   self.engine, self.config, "controller", "analog_sp", autoApply = True),
              ConfigChoice(   self.engine, self.config, "controller", "analog_sp_threshold", autoApply = True),
              ConfigChoice(   self.engine, self.config, "controller", "analog_sp_sensitivity", autoApply = True),
              #ConfigChoice(   self.engine, self.config, "controller", "analog_fx", autoApply = True), #FIXME: Analog FX
              (_("Rename Controller"), self.renameController),
            ]
        elif type == 2:
            self.config.set("controller", "key_5", None)
            self.config.set("controller", "key_5a", None)
            self.config.set("controller", "key_kill", None)

            controlKeys = [
              ActiveConfigChoice(self.engine, self.config, "controller", "type", self.changeType),
              KeyConfigChoice(self.engine, self.config, "controller", "key_2"),
              KeyConfigChoice(self.engine, self.config, "controller", "key_2a", True),
              KeyConfigChoice(self.engine, self.config, "controller", "key_3"),
              KeyConfigChoice(self.engine, self.config, "controller", "key_3a", True),
              KeyConfigChoice(self.engine, self.config, "controller", "key_4"),
              KeyConfigChoice(self.engine, self.config, "controller", "key_4a", True),
              KeyConfigChoice(self.engine, self.config, "controller", "key_1"),
              KeyConfigChoice(self.engine, self.config, "controller", "key_1a", True),
              KeyConfigChoice(self.engine, self.config, "controller", "key_action1"),
              KeyConfigChoice(self.engine, self.config, "controller", "key_action2", True),
              KeyConfigChoice(self.engine, self.config, "controller", "key_left", True),
              KeyConfigChoice(self.engine, self.config, "controller", "key_right", True),
              KeyConfigChoice(self.engine, self.config, "controller", "key_up", True),
              KeyConfigChoice(self.engine, self.config, "controller", "key_down", True),
              KeyConfigChoice(self.engine, self.config, "controller", "key_cancel"),
              KeyConfigChoice(self.engine, self.config, "controller", "key_start"),
              KeyConfigChoice(self.engine, self.config, "controller", "key_star", True),
              ConfigChoice(   self.engine, self.config, "controller", "analog_sp", autoApply = True),
              ConfigChoice(   self.engine, self.config, "controller", "analog_sp_threshold", autoApply = True),
              ConfigChoice(   self.engine, self.config, "controller", "analog_sp_sensitivity", autoApply = True),
              #ConfigChoice(   self.engine, self.config, "controller", "analog_drum", autoApply = True), #FIXME: Analog Drum
              (_("Rename Controller"), self.renameController),
            ]
        elif type == 3:
            self.config.set("controller", "key_kill", None)
            controlKeys = [
              ActiveConfigChoice(self.engine, self.config, "controller", "type", self.changeType),
              KeyConfigChoice(self.engine, self.config, "controller", "key_2"),
              KeyConfigChoice(self.engine, self.config, "controller", "key_2a", True),
              KeyConfigChoice(self.engine, self.config, "controller", "key_3"),
              KeyConfigChoice(self.engine, self.config, "controller", "key_3a", True),
              KeyConfigChoice(self.engine, self.config, "controller", "key_4"),
              KeyConfigChoice(self.engine, self.config, "controller", "key_4a", True),
              KeyConfigChoice(self.engine, self.config, "controller", "key_5"),
              KeyConfigChoice(self.engine, self.config, "controller", "key_5a", True),
              KeyConfigChoice(self.engine, self.config, "controller", "key_1"),
              KeyConfigChoice(self.engine, self.config, "controller", "key_1a", True),
              KeyConfigChoice(self.engine, self.config, "controller", "key_action1"),
              KeyConfigChoice(self.engine, self.config, "controller", "key_action2", True),
              KeyConfigChoice(self.engine, self.config, "controller", "key_left", True),
              KeyConfigChoice(self.engine, self.config, "controller", "key_right", True),
              KeyConfigChoice(self.engine, self.config, "controller", "key_up", True),
              KeyConfigChoice(self.engine, self.config, "controller", "key_down", True),
              KeyConfigChoice(self.engine, self.config, "controller", "key_cancel"),
              KeyConfigChoice(self.engine, self.config, "controller", "key_start"),
              KeyConfigChoice(self.engine, self.config, "controller", "key_star", True),
              ConfigChoice(   self.engine, self.config, "controller", "analog_sp", autoApply = True),
              ConfigChoice(   self.engine, self.config, "controller", "analog_sp_threshold", autoApply = True),
              ConfigChoice(   self.engine, self.config, "controller", "analog_sp_sensitivity", autoApply = True),
              #ConfigChoice(   self.engine, self.config, "controller", "analog_drum", autoApply = True), #FIXME: Analog Drum
              (_("Rename Controller"), self.renameController),
            ]
        elif type == 4:
            self.config.set("controller", "key_2a", None)
            self.config.set("controller", "key_3a", None)
            self.config.set("controller", "key_4a", None)
            self.config.set("controller", "key_5a", None)
            if str(self.config.get("controller", "key_5")) == "None":
                self.config.set("controller", "key_5", self.config.getDefault("controller", "key_5"))
            if str(self.config.get("controller", "key_1a")) == "None":
                self.config.set("controller", "key_1a", self.config.getDefault("controller", "key_1a"))
            if str(self.config.get("controller", "key_kill")) == "None":
                self.config.set("controller", "key_kill", self.config.getDefault("controller", "key_kill"))

            controlKeys = [
              ActiveConfigChoice(self.engine, self.config, "controller", "type", self.changeType),
              KeyConfigChoice(self.engine, self.config, "controller", "key_action1"),
              KeyConfigChoice(self.engine, self.config, "controller", "key_action2"),
              KeyConfigChoice(self.engine, self.config, "controller", "key_1"),
              KeyConfigChoice(self.engine, self.config, "controller", "key_2"),
              KeyConfigChoice(self.engine, self.config, "controller", "key_3"),
              KeyConfigChoice(self.engine, self.config, "controller", "key_4"),
              KeyConfigChoice(self.engine, self.config, "controller", "key_5"),
              KeyConfigChoice(self.engine, self.config, "controller", "key_1a", shift = _("Press the highest fret on the slider. Hold Escape to cancel.")),
              KeyConfigChoice(self.engine, self.config, "controller", "key_left", True),
              KeyConfigChoice(self.engine, self.config, "controller", "key_right", True),
              KeyConfigChoice(self.engine, self.config, "controller", "key_up", True),
              KeyConfigChoice(self.engine, self.config, "controller", "key_down", True),
              KeyConfigChoice(self.engine, self.config, "controller", "key_cancel"),
              KeyConfigChoice(self.engine, self.config, "controller", "key_start"),
              KeyConfigChoice(self.engine, self.config, "controller", "key_star"),
              KeyConfigChoice(self.engine, self.config, "controller", "key_kill"),
              ConfigChoice(   self.engine, self.config, "controller", "analog_kill", autoApply = True),
              ConfigChoice(   self.engine, self.config, "controller", "analog_slide", autoApply = True),
              ConfigChoice(   self.engine, self.config, "controller", "analog_sp", autoApply = True),
              ConfigChoice(   self.engine, self.config, "controller", "analog_sp_threshold", autoApply = True),
              ConfigChoice(   self.engine, self.config, "controller", "analog_sp_sensitivity", autoApply = True),
              #ConfigChoice(   self.engine, self.config, "controller", "analog_fx", autoApply = True), #FIXME: Analog FX
              (_("Rename Controller"), self.renameController),
            ]
        elif type == 5:
            self.config.set("controller", "key_1", None)
            self.config.set("controller", "key_2", None)
            self.config.set("controller", "key_3", None)
            self.config.set("controller", "key_4", None)
            self.config.set("controller", "key_5", None)
            self.config.set("controller", "key_1a", None)
            self.config.set("controller", "key_2a", None)
            self.config.set("controller", "key_3a", None)
            self.config.set("controller", "key_4a", None)
            self.config.set("controller", "key_5a", None)
            self.config.set("controller", "key_kill", None)
            self.config.set("controller", "key_star", None)
            self.config.set("controller", "key_action1", None)
            self.config.set("controller", "key_action2", None)
            controlKeys = [
              ActiveConfigChoice(self.engine, self.config, "controller", "type", self.changeType),
              ConfigChoice(   self.engine, self.config, "controller", "mic_device", autoApply = True),
              KeyConfigChoice(self.engine, self.config, "controller", "key_left", True),
              KeyConfigChoice(self.engine, self.config, "controller", "key_right", True),
              KeyConfigChoice(self.engine, self.config, "controller", "key_up", True),
              KeyConfigChoice(self.engine, self.config, "controller", "key_down", True),
              KeyConfigChoice(self.engine, self.config, "controller", "key_cancel"),
              KeyConfigChoice(self.engine, self.config, "controller", "key_start"),
              ConfigChoice(   self.engine, self.config, "controller", "mic_tap_sensitivity", autoApply = True),
              ConfigChoice(   self.engine, self.config, "controller", "mic_passthrough_volume", autoApply = True),
              (_("Rename Controller"), self.renameController),
            ]
        self.menu = Menu.Menu(self.engine, controlKeys, onCancel = self.cancel)
        self.engine.view.pushLayer(self.menu)

    def changeType(self):
        self.engine.view.popLayer(self.menu)
        self.setupMenu()

    def renameController(self):
        newControl = ""
        while newControl.strip().lower() in self.badname or newControl.strip() == "":
            newControl = Dialogs.getText(self.engine, _("Please rename your controller"), self.control)
            if newControl.strip().lower() in self.badname and not newControl.strip() == self.control:
                Dialogs.showMessage(self.engine, _("That name is already taken."))
            elif newControl.strip() == "" or newControl.strip() == self.control:
                Dialogs.showMessage(self.engine, _("Canceled."))
                break
        else:
            Player.renameControl(self.control, newControl)
            self.control = newControl
            self.engine.view.popLayer(self.menu)
            self.setupMenu()

    def run(self, ticks):
        self.time += ticks/50.0

    def render(self, visibility, topMost):
        pass


class SettingsMenu(Menu.Menu):
    def __init__(self, engine):

        self.engine = engine
        self.logClassInits = self.engine.config.get("game", "log_class_inits")
        if self.logClassInits == 1:
            Log.debug("SettingsMenu class init (Settings.py)...")

        self.keyCheckerMode = Config.get("game", "key_checker_mode")

        self.opt_text_x = self.engine.theme.opt_text_xPos
        self.opt_text_y = self.engine.theme.opt_text_yPos

        if engine.data.theme == 0:
            if self.opt_text_x == None:
                self.opt_text_x = .44
            if self.opt_text_y == None:
                self.opt_text_y = .14
        elif engine.data.theme == 1:
            if self.opt_text_x == None:
                self.opt_text_x = .38
            if self.opt_text_y == None:
                self.opt_text_y = .15
        elif engine.data.theme == 2:
            if self.opt_text_x == None:
                self.opt_text_x = .25
            if self.opt_text_y == None:
                self.opt_text_y = .14


        self.opt_text_color = self.engine.theme.hexToColor(self.engine.theme.opt_text_colorVar)
        self.opt_selected_color = self.engine.theme.hexToColor(self.engine.theme.opt_selected_colorVar)

        if self.opt_text_color == None:
            self.opt_text_color = (1,1,1)
        if self.opt_selected_color == None:
            self.opt_selected_color = (1,0.75,0)

        self.modSettings = [
          ConfigChoice(engine, engine.config, "mods",  "mod_" + m) for m in Mod.getAvailableMods(engine)
        ]
        if len(self.modSettings) > 0:
            self.modSettingsMenu = Menu.Menu(self.engine, self.modSettings, pos = (self.opt_text_x, self.opt_text_y), textColor = self.opt_text_color, selectedColor = self.opt_selected_color)
        else:
            self.modSettingsMenu = self.modSettings

        self.stagesOptions = [
          ConfigChoice(self.engine, self.engine.config, "game", "stage_mode", autoApply = True),   #myfingershurt
          ConfigChoice(self.engine, self.engine.config, "game", "animated_stage_folder", autoApply = True),   #myfingershurt
          ConfigChoice(self.engine, self.engine.config, "game", "song_stage", autoApply = True),   #myfingershurt
          ConfigChoice(self.engine, self.engine.config, "game", "rotate_stages", autoApply = True),   #myfingershurt
          ConfigChoice(self.engine, self.engine.config, "game", "stage_rotate_delay", autoApply = True),   #myfingershurt - user defined stage rotate delay
          ConfigChoice(self.engine, self.engine.config, "game", "stage_animate", autoApply = True),   #myfingershurt - user defined stage rotate delay
          ConfigChoice(self.engine, self.engine.config, "game", "stage_animate_delay", autoApply = True),   #myfingershurt - user defined stage rotate delay
          ConfigChoice(self.engine, self.engine.config, "game", "miss_pauses_anim", autoApply = True),
        ]
        self.stagesOptionsMenu = Menu.Menu(self.engine, self.stagesOptions, pos = (self.opt_text_x, self.opt_text_y), textColor = self.opt_text_color, selectedColor = self.opt_selected_color)

        self.hopoSettings = [
           ConfigChoice(self.engine, self.engine.config, "game", "hopo_system", autoApply = True),      #myfingershurt
           ConfigChoice(self.engine, self.engine.config, "game", "song_hopo_freq", autoApply = True),      #myfingershurt
           ConfigChoice(self.engine, self.engine.config, "game", "hopo_after_chord", autoApply = True),      #myfingershurt
        ]
        self.hopoSettingsMenu = Menu.Menu(self.engine, self.hopoSettings, pos = (self.opt_text_x, self.opt_text_y), textColor = self.opt_text_color, selectedColor = self.opt_selected_color)

        self.lyricsSettings = [
           ConfigChoice(self.engine, self.engine.config, "game", "midi_lyric_mode", autoApply = True, isQuickset = 1),      #myfingershurt
           ConfigChoice(self.engine, self.engine.config, "game", "vocal_scroll", autoApply = True, isQuickset = 1),      #akedrou
           ConfigChoice(self.engine, self.engine.config, "game", "vocal_speed", autoApply = True, isQuickset = 1),      #akedrou
           ConfigChoice(self.engine, self.engine.config, "game", "rb_midi_lyrics", autoApply = True, isQuickset = 1),      #myfingershurt
           ConfigChoice(self.engine, self.engine.config, "game", "rb_midi_sections", autoApply = True, isQuickset = 1),      #myfingershurt
           ConfigChoice(self.engine, self.engine.config, "game", "lyric_mode", autoApply = True, isQuickset = 1),      #myfingershurt
           ConfigChoice(self.engine, self.engine.config, "game", "script_lyric_pos", autoApply = True),      #myfingershurt
        ]
        self.lyricsSettingsMenu = Menu.Menu(self.engine, self.lyricsSettings, pos = (self.opt_text_x, self.opt_text_y), textColor = self.opt_text_color, selectedColor = self.opt_selected_color)

        jurgenSettings = self.refreshJurgenSettings(init = True)
        self.jurgenSettingsMenu = Menu.Menu(self.engine, jurgenSettings, pos = (self.opt_text_x, self.opt_text_y), textColor = self.opt_text_color, selectedColor = self.opt_selected_color)

        self.advancedGameSettings = [
          ConfigChoice(self.engine, self.engine.config, "performance", "star_score_updates", autoApply = True, isQuickset = 1),   #MFH
          ConfigChoice(self.engine, self.engine.config, "game", "bass_groove_enable", autoApply = True, isQuickset = 2),#myfingershurt
          ConfigChoice(self.engine, self.engine.config, "game", "mark_solo_sections", autoApply = True),
          ConfigChoice(self.engine, self.engine.config, "game", "lphrases", autoApply = True),#blazingamer
          ConfigChoice(self.engine, self.engine.config, "game", "decimal_places", autoApply = True), #MFH
          ConfigChoice(self.engine, self.engine.config, "game", "ignore_open_strums", autoApply = True),      #myfingershurt
          ConfigChoice(self.engine, self.engine.config, "game", "big_rock_endings", autoApply = True, isQuickset = 2),#myfingershurt
          ConfigChoice(self.engine, self.engine.config, "game", "starpower_mode", autoApply = True),#myfingershurt
          ConfigChoice(self.engine, self.engine.config, "game", "party_time", autoApply = True),
          ConfigChoice(self.engine, self.engine.config, "game", "keep_play_count", autoApply = True),
          ConfigChoice(self.engine, self.engine.config, "game", "lost_focus_pause", autoApply = True),
        ]
        self.advancedGameSettingsMenu = Menu.Menu(self.engine, self.advancedGameSettings, pos = (self.opt_text_x, self.opt_text_y), textColor = self.opt_text_color, selectedColor = self.opt_selected_color)

        self.battleObjectSettings = [
          ConfigChoice(engine, engine.config, "game", "battle_Whammy", autoApply = True),
          ConfigChoice(engine, engine.config, "game", "battle_Diff_Up", autoApply = True),
          ConfigChoice(engine, engine.config, "game", "battle_String_Break", autoApply = True),
          ConfigChoice(engine, engine.config, "game", "battle_Double", autoApply = True),
          ConfigChoice(engine, engine.config, "game", "battle_Death_Drain", autoApply = True),
          ConfigChoice(engine, engine.config, "game", "battle_Amp_Overload", autoApply = True),
          ConfigChoice(engine, engine.config, "game", "battle_Switch_Controls", autoApply = True),
          ConfigChoice(engine, engine.config, "game", "battle_Steal", autoApply = True),
          ConfigChoice(engine, engine.config, "game", "battle_Tune", autoApply = True),
        ]

        self.battleObjectSettingsMenu = Menu.Menu(self.engine, self.battleObjectSettings, pos = (self.opt_text_x, self.opt_text_y), textColor = self.opt_text_color, selectedColor = self.opt_selected_color)

        self.battleSettings = [
          (_("Battle Objects"), self.battleObjectSettingsMenu, _("Set which objects can appear in Battle Mode")),
        ]

        self.battleSettingsMenu = Menu.Menu(self.engine, self.battleSettings, pos = (self.opt_text_x, self.opt_text_y), textColor = self.opt_text_color, selectedColor = self.opt_selected_color)

        self.basicSettings = [
          ConfigChoice(self.engine, self.engine.config, "game",  "language"),
          ConfigChoice(self.engine, self.engine.config, "game", "T_sound", autoApply = True), #Faaa Drum sound
          ConfigChoice(self.engine, self.engine.config, "game", "star_scoring", autoApply = True),#myfingershurt
          ConfigChoice(self.engine, self.engine.config, "game", "career_star_min", autoApply = True), #akedrou
          ConfigChoice(self.engine, self.engine.config, "game", "resume_countdown", autoApply = True), #akedrou
          ConfigChoice(self.engine, self.engine.config, "game", "sp_notes_while_active", autoApply = True, isQuickset = 2),   #myfingershurt - setting for gaining more SP while active
          ConfigChoice(self.engine, self.engine.config, "game", "drum_sp_mode", autoApply = True),#myfingershurt
          ConfigChoice(self.engine, self.engine.config, "network",  "uploadscores", autoApply = True),
          ConfigChoice(self.engine, self.engine.config, "audio",  "delay", autoApply = True),     #myfingershurt: so a/v delay can be set without restarting FoF
          (_("Advanced Gameplay Settings"), self.advancedGameSettingsMenu, _("Set advanced gameplay settings that affect the game rules.")),
          (_("Vocal Mode Settings"), self.lyricsSettingsMenu, _("Change settings that affect lyrics and in-game vocals.")),
          (_("HO/PO Settings"), self.hopoSettingsMenu, _("Change settings that affect hammer-ons and pull-offs (HO/PO).")),
          (_("Battle Settings"), self.battleSettingsMenu, _("Change settings that affect battle mode.")),
        ]

        self.basicSettingsMenu = Menu.Menu(self.engine, self.basicSettings, pos = (self.opt_text_x, self.opt_text_y), textColor = self.opt_text_color, selectedColor = self.opt_selected_color)

        self.keyChangeSettings = [
          (_("Test Controller 1"), lambda: self.keyTest(0), _("Test the controller configured for slot 1.")),
          (_("Test Controller 2"), lambda: self.keyTest(1), _("Test the controller configured for slot 2.")),
          (_("Test Controller 3"), lambda: self.keyTest(2), _("Test the controller configured for slot 3.")),
          (_("Test Controller 4"), lambda: self.keyTest(3), _("Test the controller configured for slot 4.")),
        ]
        self.keyChangeMenu = Menu.Menu(self.engine, self.keyChangeSettings, pos = (self.opt_text_x, self.opt_text_y), textColor = self.opt_text_color, selectedColor = self.opt_selected_color)

        self.keySettings = self.refreshKeySettings(init = True)
        self.keySettingsMenu = Menu.Menu(self.engine, self.keySettings, onClose = self.controlCheck, pos = (self.opt_text_x, self.opt_text_y), textColor = self.opt_text_color, selectedColor = self.opt_selected_color)

        self.neckTransparency = [      #volshebnyi
          ConfigChoice(self.engine, self.engine.config, "game", "necks_alpha", autoApply = True),
          ConfigChoice(self.engine, self.engine.config, "game", "neck_alpha", autoApply = True),
          ConfigChoice(self.engine, self.engine.config, "game", "solo_neck_alpha", autoApply = True),
          ConfigChoice(self.engine, self.engine.config, "game", "bg_neck_alpha", autoApply = True),
          ConfigChoice(self.engine, self.engine.config, "game", "fail_neck_alpha", autoApply = True),
          ConfigChoice(self.engine, self.engine.config, "game", "4x_neck_alpha", autoApply = True),
          ConfigChoice(self.engine, self.engine.config, "game", "overlay_neck_alpha", autoApply = True),
        ]
        self.neckTransparencyMenu = Menu.Menu(self.engine, self.neckTransparency, pos = (self.opt_text_x, self.opt_text_y), textColor = self.opt_text_color, selectedColor = self.opt_selected_color)

        self.shaderSettings = [      #volshebnyi
          ConfigChoice(self.engine, self.engine.config, "video", "shader_use", autoApply = True),
          ConfigChoice(self.engine, self.engine.config, "video", "shader_neck", autoApply = True),
          ConfigChoice(self.engine, self.engine.config, "video", "shader_stage", autoApply = True),
          ConfigChoice(self.engine, self.engine.config, "video", "shader_sololight", autoApply = True),
          ConfigChoice(self.engine, self.engine.config, "video", "shader_tail", autoApply = True),
          ConfigChoice(self.engine, self.engine.config, "video", "shader_notes", autoApply = True),
          ConfigChoice(self.engine, self.engine.config, "video", "shader_cd", autoApply = True),
        ]
        self.shaderSettings = Menu.Menu(self.engine, self.shaderSettings, pos = (self.opt_text_x, self.opt_text_y), textColor = self.opt_text_color, selectedColor = self.opt_selected_color)

        self.advancedVideoSettings = [
          ConfigChoice(self.engine, self.engine.config, "engine", "highpriority", isQuickset = 1),
          ConfigChoice(self.engine, self.engine.config, "video",  "fps", isQuickset = 1),
          ConfigChoice(self.engine, self.engine.config, "game", "accuracy_pos", autoApply = True),
          ConfigChoice(self.engine, self.engine.config, "game", "gsolo_acc_pos", autoApply = True, isQuickset = 1), #MFH
          ConfigChoice(self.engine, self.engine.config, "coffee", "noterotate", autoApply = True), #blazingamer
          ConfigChoice(self.engine, self.engine.config, "game", "gfx_version_tag", autoApply = True), #MFH
          ConfigChoice(self.engine, self.engine.config, "video",  "multisamples", isQuickset = 1),
          ConfigChoice(self.engine, self.engine.config, "performance", "static_strings", autoApply = True, isQuickset = 1),      #myfingershurt
          ConfigChoice(self.engine, self.engine.config, "performance", "killfx", autoApply = True, isQuickset = 1),   #blazingamer
          (_("More Effects"), self.shaderSettings, _("Change the settings of the shader system.")), #volshebnyi
        ]
        self.advancedVideoSettingsMenu = Menu.Menu(self.engine, self.advancedVideoSettings, pos = (self.opt_text_x, self.opt_text_y), textColor = self.opt_text_color, selectedColor = self.opt_selected_color)

        self.fretSettings = [
          ConfigChoice(self.engine, self.engine.config, "fretboard", "point_of_view", autoApply = True, isQuickset = 2),
          ConfigChoice(self.engine, self.engine.config, "fretboard", "neck_intro_animation", autoApply = True), #weirdpeople
          ConfigChoice(self.engine, self.engine.config, "game", "notedisappear", autoApply = True),
          ConfigChoice(self.engine, self.engine.config, "game", "frets_under_notes", autoApply = True), #MFH
          ConfigChoice(self.engine, self.engine.config, "game", "nstype", autoApply = True),      #blazingamer
          ConfigChoice(self.engine, self.engine.config, "coffee", "neckSpeed", autoApply = True),
          ConfigChoice(self.engine, self.engine.config, "game", "large_drum_neck", autoApply = True),      #myfingershurt
          ConfigChoice(self.engine, self.engine.config, "game", "bass_groove_neck", autoApply = True),      #myfingershurt
          ConfigChoice(self.engine, self.engine.config, "game", "guitar_solo_neck", autoApply = True),      #myfingershurt
          ConfigChoice(self.engine, self.engine.config, "game", "4x_neck", autoApply = True),      #myfingershurt
          ConfigChoice(self.engine, self.engine.config, "fretboard", "ovrneckoverlay", autoApply = True),
          ConfigChoice(self.engine, self.engine.config, "game", "incoming_neck_mode", autoApply = True, isQuickset = 1),
          #myfingershurt
          (_("Change Neck Transparency"), self.neckTransparencyMenu, _("Change the transparency of the various in-game necks.")), #volshebnyi
        ]
        self.fretSettingsMenu = Menu.Menu(self.engine, self.fretSettings, pos = (self.opt_text_x, self.opt_text_y), textColor = self.opt_text_color, selectedColor = self.opt_selected_color)

        self.themeDisplaySettings = [
          ConfigChoice(self.engine, self.engine.config, "game", "rb_sp_neck_glow", autoApply = True),
          ConfigChoice(self.engine, self.engine.config, "performance", "animated_notes", autoApply = True, isQuickset = 1),
        ]
        self.themeDisplayMenu = Menu.Menu(self.engine, self.themeDisplaySettings, pos = (self.opt_text_x, self.opt_text_y), textColor = self.opt_text_color, selectedColor = self.opt_selected_color)

        self.inGameDisplaySettings = [
          (_("Theme Display Settings"), self.themeDisplayMenu, _("Change settings that only affect certain theme types.")),
          ConfigChoice(self.engine, self.engine.config, "game", "in_game_stars", autoApply = True, isQuickset = 2),
          ConfigChoice(self.engine, self.engine.config, "coffee", "game_phrases", autoApply = True, isQuickset = 1),
          ConfigChoice(self.engine, self.engine.config, "game", "hopo_indicator", autoApply = True),
          ConfigChoice(self.engine, self.engine.config, "game", "accuracy_mode", autoApply = True),
          ConfigChoice(self.engine, self.engine.config, "performance", "in_game_stats", autoApply = True, isQuickset = 1),
          ConfigChoice(self.engine, self.engine.config, "game", "gsolo_accuracy_disp", autoApply = True, isQuickset = 1), #MFH
          ConfigChoice(self.engine, self.engine.config, "game", "solo_frame", autoApply = True),      #myfingershurt
          ConfigChoice(self.engine, self.engine.config, "video", "disable_fretsfx", autoApply = True),
          ConfigChoice(self.engine, self.engine.config, "video", "disable_flamesfx", autoApply = True),
          ConfigChoice(self.engine, self.engine.config, "video", "hitglow_color", autoApply = True),
          ConfigChoice(self.engine, self.engine.config, "video", "counting", autoApply = True, isQuickset = 2),
        ]
        self.inGameDisplayMenu = Menu.Menu(self.engine, self.inGameDisplaySettings, pos = (self.opt_text_x, self.opt_text_y), textColor = self.opt_text_color, selectedColor = self.opt_selected_color)

        modes = self.engine.video.getVideoModes()
        modes.reverse()
        Config.define("video",  "resolution", str,   "1024x768", text = _("Video Resolution"), options = ["%dx%d" % (m[0], m[1]) for m in modes], tipText = _("Set the resolution of the game. In windowed mode, higher values mean a larger screen."))
        self.videoSettings = [
          ConfigChoice(engine, engine.config, "coffee", "themename"), #was autoapply... why?
          ConfigChoice(engine, engine.config, "video",  "resolution"),
          ConfigChoice(engine, engine.config, "video",  "fullscreen"),
          ConfigChoice(engine, engine.config, "video", "disable_screensaver"),  #stump
          ConfigChoice(engine, engine.config, "game", "use_graphical_submenu", autoApply = True, isQuickset = 1),
          (_("Stages Options"), self.stagesOptionsMenu, _("Change settings related to the in-game background.")),
          (_("Choose Default Neck >"), lambda: Dialogs.chooseNeck(self.engine), _("Choose your default neck. You still have to choose which neck you use for your character in the character select screen.")),
          (_("Fretboard Settings"), self.fretSettingsMenu, _("Change settings related to the fretboard.")),
          (_("In-Game Display Settings"), self.inGameDisplayMenu, _("Change what and where things appear in-game.")),
          (_("Advanced Video Settings"), self.advancedVideoSettingsMenu, _("Change advanced video settings.")),
        ]
        self.videoSettingsMenu = Menu.Menu(self.engine, self.videoSettings, pos = (self.opt_text_x, self.opt_text_y), textColor = self.opt_text_color, selectedColor = self.opt_selected_color)


        self.volumeSettings = [
          VolumeConfigChoice(engine, engine.config, "audio",  "guitarvol", autoApply = True),
          VolumeConfigChoice(engine, engine.config, "audio",  "songvol", autoApply = True),
          VolumeConfigChoice(engine, engine.config, "audio",  "screwupvol", autoApply = True),
          VolumeConfigChoice(engine, engine.config, "audio",  "miss_volume", autoApply = True),
          VolumeConfigChoice(engine, engine.config, "audio",  "single_track_miss_volume", autoApply = True),
          VolumeConfigChoice(engine, engine.config, "audio",  "crowd_volume", autoApply = True), #akedrou
          VolumeConfigChoice(engine, engine.config, "audio",  "kill_volume", autoApply = True), #MFH
          ActiveConfigChoice(engine, engine.config, "audio",  "SFX_volume", autoApply = True, onChange = self.engine.data.SetAllSoundFxObjectVolumes, volume = True), #MFH
          ActiveConfigChoice(engine, engine.config, "audio",  "menu_volume", autoApply = True, onChange = self.engine.mainMenu.setMenuVolume),
        ]
        self.volumeSettingsMenu = Menu.Menu(engine, self.volumeSettings, pos = (self.opt_text_x, self.opt_text_y), textColor = self.opt_text_color, selectedColor = self.opt_selected_color)

        self.advancedAudioSettings = [
           ConfigChoice(engine, engine.config, "audio",  "frequency"),
           ConfigChoice(engine, engine.config, "audio",  "bits"),
           ConfigChoice(engine, engine.config, "audio",  "buffersize"),
           ConfigChoice(engine, engine.config, "game", "result_cheer_loop", autoApply = True), #MFH
           ConfigChoice(engine, engine.config, "game", "cheer_loop_delay", autoApply = True), #MFH
        ]
        self.advancedAudioSettingsMenu = Menu.Menu(engine, self.advancedAudioSettings, pos = (self.opt_text_x, self.opt_text_y), textColor = self.opt_text_color, selectedColor = self.opt_selected_color)

        self.audioSettings = [
          (_("Volume Settings"),    self.volumeSettingsMenu, _("Change the volume of game sounds.")),
          ConfigChoice(engine, engine.config, "game", "sustain_muting", autoApply = True),   #myfingershurt
          ConfigChoice(engine, engine.config, "game", "mute_drum_fill", autoApply = True),
          ConfigChoice(engine, engine.config, "audio", "mute_last_second", autoApply = True), #MFH
          ConfigChoice(engine, engine.config, "game", "bass_kick_sound", autoApply = True),   #myfingershurt
          ConfigChoice(engine, engine.config, "game", "star_claps", autoApply = True),      #myfingershurt
          ConfigChoice(engine, engine.config, "game", "beat_claps", autoApply = True), #racer
          ConfigChoice(engine, engine.config, "audio",  "whammy_effect", autoApply = True),     #MFH
          ConfigChoice(engine, engine.config, "audio", "enable_crowd_tracks", autoApply = True),
          (_("Advanced Audio Settings"), self.advancedAudioSettingsMenu, _("Change advanced audio settings.")),
        ]
        self.audioSettingsMenu = Menu.Menu(engine, self.audioSettings, pos = (self.opt_text_x, self.opt_text_y), textColor = self.opt_text_color, selectedColor = self.opt_selected_color)

        #MFH - new menu
        self.logfileSettings = [
          ConfigChoice(engine, engine.config, "game", "log_class_inits", autoApply = True),#myfingershurt
          ConfigChoice(engine, engine.config, "game", "log_loadings", autoApply = True),#myfingershurt
          ConfigChoice(engine, engine.config, "game", "log_sections", autoApply = True),#myfingershurt
          ConfigChoice(engine, engine.config, "game", "log_marker_notes", autoApply = True),#myfingershurt
          ConfigChoice(engine, engine.config, "game", "log_starpower_misses", autoApply = True),#myfingershurt
          ConfigChoice(engine, engine.config, "log",   "log_unedited_midis", autoApply = True),#myfingershurt
          ConfigChoice(engine, engine.config, "log",   "log_lyric_events", autoApply = True),#myfingershurt
          ConfigChoice(engine, engine.config, "log",   "log_tempo_events", autoApply = True),#myfingershurt
          ConfigChoice(engine, engine.config, "log",   "log_image_not_found", autoApply = True),
        ]
        self.logfileSettingsMenu = Menu.Menu(engine, self.logfileSettings, pos = (self.opt_text_x, self.opt_text_y), textColor = self.opt_text_color, selectedColor = self.opt_selected_color)

        self.debugSettings = [
          ConfigChoice(engine, engine.config, "video", "show_fps"),#evilynux
          ConfigChoice(engine, engine.config, "game", "kill_debug", autoApply = True),#myfingershurt
          ConfigChoice(engine, engine.config, "game", "hopo_debug_disp", autoApply = True),#myfingershurt
          ConfigChoice(engine, engine.config, "game", "show_unused_text_events", autoApply = True),#myfingershurt
          ConfigChoice(engine, engine.config, "debug",   "use_unedited_midis", autoApply = True),#myfingershurt
          ConfigChoice(engine, engine.config, "debug", "show_raw_vocal_data", autoApply = True), #akedrou
          ConfigChoice(engine, engine.config, "debug",   "show_freestyle_active", autoApply = True),#myfingershurt
          ConfigChoice(engine, engine.config, "debug",   "show_bpm", autoApply = True),#myfingershurt
          ConfigChoice(engine, engine.config, "debug",   "use_new_vbpm_beta", autoApply = True),#myfingershurt
        ]
        self.debugSettingsMenu = Menu.Menu(engine, self.debugSettings, pos = (self.opt_text_x, self.opt_text_y), textColor = self.opt_text_color, selectedColor = self.opt_selected_color)

        self.quickSettings = [
          ConfigChoice(engine, engine.config, "quickset", "performance", autoApply = True),
          ConfigChoice(engine, engine.config, "quickset", "gameplay", autoApply = True),
        ]
        self.quicksetMenu = Menu.Menu(engine, self.quickSettings, pos = (self.opt_text_x, self.opt_text_y), textColor = self.opt_text_color, selectedColor = self.opt_selected_color)

        self.listSettings = [
          (_("Change Setlist Path >"), self.baseLibrarySelect, _("Set the path to a folder named 'songs' that contains your songs.")),
          ConfigChoice(engine, engine.config, "game",  "sort_order", autoApply = True),
          ConfigChoice(engine, engine.config, "game", "sort_direction", autoApply = True),
          ConfigChoice(engine, engine.config, "game", "quickplay_tiers", autoApply = True),  #myfingershurt
          ConfigChoice(engine, engine.config, "coffee", "songfilepath", autoApply = True),
          #(_("Select List All Folder >"), self.listAllFolderSelect), #- Not Working Yet - Qstick
          ConfigChoice(engine, engine.config, "game", "songcovertype", autoApply = True),
          ConfigChoice(engine, engine.config, "game", "queue_parts", autoApply = True),
          ConfigChoice(engine, engine.config, "game", "queue_diff", autoApply = True),
          ConfigChoice(engine, engine.config, "game", "preload_labels", autoApply = True),
          ConfigChoice(engine, engine.config, "audio", "disable_preview", autoApply = True),  #myfingershurt
          ConfigChoice(engine, engine.config, "game", "songlist_instrument", autoApply = True), #MFH
          ConfigChoice(engine, engine.config, "game", "songlist_difficulty", autoApply = True), #evilynux
          ConfigChoice(engine, engine.config, "game",  "whammy_changes_sort_order", autoApply = True), #stump
          ConfigChoice(engine, engine.config, "game", "HSMovement", autoApply = True), #racer
          ConfigChoice(engine, engine.config, "performance", "disable_libcount", autoApply = True, isQuickset = 1),
          ConfigChoice(engine, engine.config, "performance", "cache_song_metadata", autoApply = True, isQuickset = 1), #stump
          ConfigChoice(engine, engine.config, "songlist",  "nil_show_next_score", autoApply = True), #MFH
        ]
        self.listSettingsMenu = Menu.Menu(engine, self.listSettings, pos = (self.opt_text_x, self.opt_text_y), textColor = self.opt_text_color, selectedColor = self.opt_selected_color)


        advancedSettings = [
          ConfigChoice(engine, engine.config, "performance", "game_priority", autoApply = True, isQuickset = 1),
          ConfigChoice(engine, engine.config, "performance", "restrict_to_first_processor"),  #stump
          (_("Debug Settings"), self.debugSettingsMenu, _("Settings for coders to debug. Probably not worth changing.")),
          (_("Log Settings"),    self.logfileSettingsMenu, _("Adds junk information to the logfile. Probably not useful in bug reports.")),
        ]
        self.advancedSettingsMenu = Menu.Menu(engine, advancedSettings, pos = (self.opt_text_x, self.opt_text_y), textColor = self.opt_text_color, selectedColor = self.opt_selected_color)

        self.cheats = [
          (_("AI Settings"), self.jurgenSettingsMenu, _("Change the settings of the AI")),
          ConfigChoice(engine, engine.config, "game", "gh2_sloppy", autoApply = True),
          ConfigChoice(engine, engine.config, "game", "whammy_saves_starpower", autoApply = True),#myfingershurt
          ConfigChoice(self.engine, self.engine.config, "game",   "note_hit_window", autoApply = True), #alarian: defines hit window
          ConfigChoice(engine, engine.config, "coffee", "hopo_frequency", autoApply = True),
          ConfigChoice(engine, engine.config, "coffee", "failingEnabled", autoApply = True),
          ConfigChoice(engine, engine.config, "audio",  "speed_factor", autoApply = True),     #MFH
          ConfigChoice(engine, engine.config, "handicap",  "early_hit_window", autoApply = True),     #MFH
          ConfigChoice(engine, engine.config, "handicap", "detailed_handicap", autoApply = True),
          (_("Mod settings"), self.modSettingsMenu, _("Enable or disable any mods you have installed.")),
        ]
        self.cheatMenu = Menu.Menu(engine, self.cheats, pos = (self.opt_text_x, self.opt_text_y), textColor = self.opt_text_color, selectedColor = self.opt_selected_color)

        settings = [
          (_("Gameplay Settings"),   self.basicSettingsMenu, _("Settings that affect the rules of the game.")),
          (_("Control Settings"),     self.keySettingsMenu, _("Create, delete, and edit your controls.")),
          (_("Display Settings"),     self.videoSettingsMenu, _("Theme, neck, resolution, etc.")),
          (_("Audio Settings"),      self.audioSettingsMenu, _("Volume controls, etc.")),
          (_("Setlist Settings"),   self.listSettingsMenu, _("Settings that affect the setlist.")),
          (_("Advanced Settings"), self.advancedSettingsMenu, _("Settings that probably don't need to be changed.")),
          (_("Mods, Cheats, AI"), self.cheatMenu, _("Set Jurgen to play for you, or other cheats.")),
          (_("%s Credits") % (Version.PROGRAM_NAME), lambda: Dialogs.showCredits(engine), _("See who made this game.")),
          (_("Quickset"), self.quicksetMenu, _("A quick way to set many advanced settings.")),
          (_("Hide Advanced Options"), self.advancedSettings)
        ]

        self.settingsToApply = self.videoSettings + \
                               self.advancedAudioSettings + \
                               self.advancedVideoSettings + \
                               self.basicSettings + \
                               self.keySettings + \
                               self.inGameDisplaySettings + \
                               self.themeDisplaySettings + \
                               self.debugSettings + \
                               self.quickSettings + \
                               self.modSettings

        Menu.Menu.__init__(self, engine, settings, name = "advsettings", onCancel = self.applySettings, pos = (self.opt_text_x, self.opt_text_y), textColor = self.opt_text_color, selectedColor = self.opt_selected_color)   #MFH - add position to this so we can move it

    def applySettings(self):
        quickset(self.engine.config)
        if self.engine.restartRequired or self.engine.quicksetRestart:
            Dialogs.showMessage(self.engine, _("FoFiX needs to restart to apply setting changes."))
            for option in self.settingsToApply:
                if isinstance(option, ConfigChoice):
                    option.apply()
            self.engine.restart()

    def refreshJurgenSettings(self, init = False):
        choices = []
        maxplayer = self.engine.config.get("performance", "max_players")
        for i in range(maxplayer):
            choices.append(ConfigChoice(self.engine, self.engine.config, "game", "jurg_p%d" % i, autoApply = True))
            choices.append(ConfigChoice(self.engine, self.engine.config, "game", "jurg_skill_p%d" % i, autoApply = True))
            choices.append(ConfigChoice(self.engine, self.engine.config, "game", "jurg_logic_p%d" % i, autoApply = True))
        if init:
            return choices
        self.engine.mainMenu.settingsMenuObject.jurgenSettingsMenu.choices = choices

    def refreshKeySettings(self, init = False):
        choices = [ #the reacharound
          Menu.Choice(_("Test Controls"), self.keyChangeMenu, tipText = _("Go here to test your controllers.")),
          ActiveConfigChoice(self.engine, self.engine.config, "game", "control0", onChange = self.engine.input.reloadControls),
          ActiveConfigChoice(self.engine, self.engine.config, "game", "control1", onChange = self.engine.input.reloadControls),
          ActiveConfigChoice(self.engine, self.engine.config, "game", "control2", onChange = self.engine.input.reloadControls),
          ActiveConfigChoice(self.engine, self.engine.config, "game", "control3", onChange = self.engine.input.reloadControls),
          Menu.Choice(_("New Controller"),    lambda: createControl(self.engine, refresh = self.refreshKeySettings), tipText = _("Create a new controller to use.")),
          Menu.Choice(_("Edit Controller"),   lambda: chooseControl(self.engine, refresh = self.refreshKeySettings), tipText = _("Edit a controller you have created.")),
          Menu.Choice(_("Delete Controller"), lambda: chooseControl(self.engine, "delete", refresh = self.refreshKeySettings), tipText = _("Delete a controller you have created.")),
          ActiveConfigChoice(self.engine, self.engine.config, "performance", "max_players", onChange = self.refreshJurgenSettings), #akedrou
          ActiveConfigChoice(self.engine, self.engine.config, "game", "scroll_delay", onChange = self.scrollSet),
          ActiveConfigChoice(self.engine, self.engine.config, "game", "scroll_rate", onChange = self.scrollSet),
          ActiveConfigChoice(self.engine, self.engine.config, "game", "p2_menu_nav", onChange = self.engine.input.reloadControls),#myfingershurt
          ActiveConfigChoice(self.engine, self.engine.config, "game", "drum_navigation", onChange = self.engine.input.reloadControls),#myfingershurt
          ActiveConfigChoice(self.engine, self.engine.config, "game", "key_checker_mode", onChange = self.engine.input.reloadControls),#myfingershurt
        ]
        if init:
            return choices
        self.engine.mainMenu.settingsMenuObject.keySettingsMenu.choices = choices

    def controlCheck(self):
        control = [self.engine.config.get("game", "control0")]
        self.keyCheckerMode = Config.get("game", "key_checker_mode")
        if str(control[0]) == "None":
            Dialogs.showMessage(self.engine, _("You must specify a controller for slot 1!"))
            self.engine.view.pushLayer(self.keySettingsMenu)
        else:
            for i in range(1,4):
                c = self.engine.config.get("game", "control%d" % i)
                if c in control and str(c) != "None":
                    Dialogs.showMessage(self.engine, _("Controllers in slots %d and %d conflict. Setting %d to None.") % (control.index(c)+1, i+1, i+1))
                    self.engine.config.set("game", "control%d" % i, None)
                else:
                    control.append(c)
            self.engine.input.reloadControls()
            if len(self.engine.input.controls.overlap) > 0 and self.keyCheckerMode > 0:
                n = 0
                for i in self.engine.input.controls.overlap:
                    if n > 2 and len(self.engine.input.controls.overlap) > 4:
                        Dialogs.showMessage(self.engine, _("%d more conflicts.") % (len(self.engine.input.controls.overlap)-3))
                        break
                    Dialogs.showMessage(self.engine, i)
                    n+= 1
                if self.keyCheckerMode == 2:
                    self.engine.view.pushLayer(self.keySettingsMenu)
            self.refreshKeySettings()

    def advancedSettings(self):
        Config.set("game", "adv_settings", False)
        self.engine.advSettings = False
        if not self.engine.restartRequired:
            self.engine.view.popLayer(self)
            self.engine.input.removeKeyListener(self)
        else:
            self.applySettings()

    def keyTest(self, controller):
        if str(self.engine.input.controls.controls[controller]) == "None":
            Dialogs.showMessage(self.engine, "No controller set for slot %d" % (controller+1))
        else:
            Dialogs.testKeys(self.engine, controller)

    def scrollSet(self):
        self.engine.scrollRate = self.engine.config.get("game", "scroll_rate")
        self.engine.scrollDelay = self.engine.config.get("game", "scroll_delay")

    def resetLanguageToEnglish(self):
        Log.debug("settings.resetLanguageToEnglish function call...")
        if self.engine.config.get("game", "language") != "":
            self.engine.config.set("game", "language", "")
            self.engine.restart()

    def baseLibrarySelect(self):
        Log.debug("settings.baseLibrarySelect function call...")
        newPath = Dialogs.chooseFile(self.engine, masks = ["*/*"], prompt = _("Choose a new songs directory."), dirSelect = True)
        if newPath != None:
            Config.set("setlist", "base_library", os.path.dirname(newPath))
            Config.set("setlist", "selected_library", os.path.basename(newPath))
            Config.set("setlist", "selected_song", "")
            self.engine.resource.refreshBaseLib()   #myfingershurt - to let user continue with new songpath without restart


class BasicSettingsMenu(Menu.Menu):
    def __init__(self, engine):

        self.engine = engine
        self.keyActive = True
        self.confirmNeck = False

        self.logClassInits = self.engine.config.get("game", "log_class_inits")
        if self.logClassInits == 1:
            Log.debug("BasicSettingsMenu class init (Settings.py)...")

        self.opt_text_x = self.engine.theme.opt_text_xPos
        self.opt_text_y = self.engine.theme.opt_text_yPos

        if engine.data.theme == 0:
            if self.opt_text_x == None:
                self.opt_text_x = .44
            if self.opt_text_y == None:
                self.opt_text_y = .14
        elif engine.data.theme == 1:
            if self.opt_text_x == None:
                self.opt_text_x = .38
            if self.opt_text_y == None:
                self.opt_text_y = .15
        elif engine.data.theme == 2:
            if self.opt_text_x == None:
                self.opt_text_x = .25
            if self.opt_text_y == None:
                self.opt_text_y = .14


        self.opt_text_color = self.engine.theme.hexToColor(self.engine.theme.opt_text_colorVar)
        self.opt_selected_color = self.engine.theme.hexToColor(self.engine.theme.opt_selected_colorVar)

        if self.opt_text_color == None:
            self.opt_text_color = (1,1,1)
        if self.opt_selected_color == None:
            self.opt_selected_color = (1,0.75,0)

        self.modSettings = [
          ConfigChoice(engine, engine.config, "mods",  "mod_" + m) for m in Mod.getAvailableMods(engine)
        ]
        if len(self.modSettings) > 0:
            self.modSettingsMenu = Menu.Menu(self.engine, self.modSettings, pos = (self.opt_text_x, self.opt_text_y), textColor = self.opt_text_color, selectedColor = self.opt_selected_color)
        else:
            self.modSettingsMenu = self.modSettings

        FoFiXBasicSettings = [
          ConfigChoice(engine, engine.config, "game",  "language"),
          ConfigChoice(engine, engine.config, "game", "T_sound", autoApply = True), #Faaa Drum sound
          ConfigChoice(engine, engine.config, "game", "star_scoring", autoApply = True),#myfingershurt
          ConfigChoice(engine, engine.config, "game", "career_star_min", autoApply = True), #akedrou
          ConfigChoice(engine, engine.config, "game", "resume_countdown", autoApply = True), #akedrou
          ConfigChoice(engine, engine.config, "game", "sp_notes_while_active", autoApply = True, isQuickset = 2),   #myfingershurt - setting for gaining more SP while active
          ConfigChoice(engine, engine.config, "game", "drum_sp_mode", autoApply = True),#myfingershurt
          ConfigChoice(engine, engine.config, "network",  "uploadscores", autoApply = True),
          ConfigChoice(engine, engine.config, "audio",  "delay", autoApply = True),     #myfingershurt: so a/v delay can be set without restarting FoF
        ]
        FoFiXBasicSettingsMenu = Menu.Menu(engine, FoFiXBasicSettings, pos = (self.opt_text_x, self.opt_text_y), textColor = self.opt_text_color, selectedColor = self.opt_selected_color)

        self.keyChangeSettings = [
          (_("Test Controller 1"), lambda: self.keyTest(0), _("Test the controller configured for slot 1.")),
          (_("Test Controller 2"), lambda: self.keyTest(1), _("Test the controller configured for slot 2.")),
          (_("Test Controller 3"), lambda: self.keyTest(2), _("Test the controller configured for slot 3.")),
          (_("Test Controller 4"), lambda: self.keyTest(3), _("Test the controller configured for slot 4.")),
        ]
        self.keyChangeMenu = Menu.Menu(self.engine, self.keyChangeSettings, pos = (self.opt_text_x, self.opt_text_y), textColor = self.opt_text_color, selectedColor = self.opt_selected_color)

        self.keySettings = self.refreshKeySettings(init = True)
        self.keySettingsMenu = Menu.Menu(self.engine, self.keySettings, onClose = self.controlCheck, pos = (self.opt_text_x, self.opt_text_y), textColor = self.opt_text_color, selectedColor = self.opt_selected_color)

        InGameDisplaySettings = [
          ConfigChoice(engine, engine.config, "game", "in_game_stars", autoApply = True, isQuickset = 2),
          ConfigChoice(engine, engine.config, "game", "accuracy_mode", autoApply = True),
          ConfigChoice(engine, engine.config, "performance", "in_game_stats", autoApply = True, isQuickset = 1),
          ConfigChoice(engine, engine.config, "video", "counting", autoApply = True, isQuickset = 2),
        ]
        InGameDisplayMenu = Menu.Menu(engine, InGameDisplaySettings, pos = (self.opt_text_x, self.opt_text_y), textColor = self.opt_text_color, selectedColor = self.opt_selected_color)

        modes = engine.video.getVideoModes()
        modes.reverse()
        Config.define("video",  "resolution", str,   "1024x768", text = _("Video Resolution"), options = ["%dx%d" % (m[0], m[1]) for m in modes], tipText = _("Set the resolution of the game. In windowed mode, higher values mean a larger screen."))
        videoSettings = [
          ConfigChoice(engine, engine.config, "coffee", "themename"),
          ConfigChoice(engine, engine.config, "video",  "resolution"),
          ConfigChoice(engine, engine.config, "video",  "fullscreen"),
          ConfigChoice(engine, engine.config, "game", "stage_mode", autoApply = True),   #myfingershurt
          ConfigChoice(engine, engine.config, "game", "use_graphical_submenu", autoApply = True, isQuickset = 1),
          (_("Choose Default Neck >"), lambda: Dialogs.chooseNeck(self.engine), _("Choose your default neck. You still have to choose which neck you use for your character in the character select screen.")),
          (_("In-Game Display Settings"), InGameDisplayMenu, _("Change what and where things appear in-game.")),
        ]
        self.videoSettingsMenu = Menu.Menu(engine, videoSettings, pos = (self.opt_text_x, self.opt_text_y), textColor = self.opt_text_color, selectedColor = self.opt_selected_color)


        volumeSettings = [
          VolumeConfigChoice(engine, engine.config, "audio",  "guitarvol", autoApply = True),
          VolumeConfigChoice(engine, engine.config, "audio",  "songvol", autoApply = True),
          VolumeConfigChoice(engine, engine.config, "audio",  "screwupvol", autoApply = True),
          VolumeConfigChoice(engine, engine.config, "audio",  "miss_volume", autoApply = True),
          VolumeConfigChoice(engine, engine.config, "audio",  "single_track_miss_volume", autoApply = True),
          VolumeConfigChoice(engine, engine.config, "audio",  "crowd_volume", autoApply = True), #akedrou
          VolumeConfigChoice(engine, engine.config, "audio",  "kill_volume", autoApply = True), #MFH
          ActiveConfigChoice(engine, engine.config, "audio",  "SFX_volume", autoApply = True, onChange = self.engine.data.SetAllSoundFxObjectVolumes, volume = True), #MFH
          ActiveConfigChoice(engine, engine.config, "audio",  "menu_volume", autoApply = True, onChange = self.engine.mainMenu.setMenuVolume),
        ]
        volumeSettingsMenu = Menu.Menu(engine, volumeSettings, pos = (self.opt_text_x, self.opt_text_y), textColor = self.opt_text_color, selectedColor = self.opt_selected_color)

        audioSettings = [
          (_("Volume Settings"),    volumeSettingsMenu, _("Change the volume of game sounds.")),
          ConfigChoice(engine, engine.config, "game", "star_claps", autoApply = True),      #myfingershurt
          ConfigChoice(engine, engine.config, "game", "beat_claps", autoApply = True), #racer
          ConfigChoice(engine, engine.config, "audio",  "whammy_effect", autoApply = True),     #MFH
          ConfigChoice(engine, engine.config, "audio", "enable_crowd_tracks", autoApply = True), #akedrou
        ]
        audioSettingsMenu = Menu.Menu(engine, audioSettings, pos = (self.opt_text_x, self.opt_text_y), textColor = self.opt_text_color, selectedColor = self.opt_selected_color)

        quickSettings = [
          ConfigChoice(engine, engine.config, "quickset", "performance", autoApply = True),
          ConfigChoice(engine, engine.config, "quickset", "gameplay", autoApply = True),
        ]
        quicksetMenu = Menu.Menu(engine, quickSettings, pos = (self.opt_text_x, self.opt_text_y), textColor = self.opt_text_color, selectedColor = self.opt_selected_color)

        listSettings = [
          (_("Change Setlist Path >"), self.baseLibrarySelect, _("Set the path to a folder named 'songs' that contains your songs.")),
          ConfigChoice(engine, engine.config, "game",  "sort_order", autoApply = True),
          ConfigChoice(engine, engine.config, "game", "sort_direction", autoApply = True),
          ConfigChoice(engine, engine.config, "game", "quickplay_tiers", autoApply = True),  #myfingershurt
          ConfigChoice(engine, engine.config, "game", "songcovertype", autoApply = True),
          ConfigChoice(engine, engine.config, "game", "songlist_instrument", autoApply = True), #MFH
          ConfigChoice(engine, engine.config, "game", "songlist_difficulty", autoApply = True), #evilynux
        ]
        listSettingsMenu = Menu.Menu(engine, listSettings, pos = (self.opt_text_x, self.opt_text_y), textColor = self.opt_text_color, selectedColor = self.opt_selected_color)

        Cheats = self.refreshCheatSettings(init = True)
        self.cheatMenu = Menu.Menu(engine, Cheats, pos = (self.opt_text_x, self.opt_text_y), textColor = self.opt_text_color, selectedColor = self.opt_selected_color)

        settings = [
          (_("Gameplay Settings"),   FoFiXBasicSettingsMenu, _("Settings that affect the rules of the game.")),
          (_("Control Settings"),          self.keySettingsMenu, _("Create, delete, and edit your controls.")),
          (_("Display Settings"),     self.videoSettingsMenu, _("Theme, neck, resolution, etc.")),
          (_("Audio Settings"),      audioSettingsMenu, _("Volume controls, etc.")),
          (_("Setlist Settings"),   listSettingsMenu, _("Settings that affect the setlist.")),
          (_("Mods, Cheats, AI"), self.cheatMenu, _("Set Jurgen to play for you, or other cheats.")),
          (_("%s Credits") % (engine.versionString), lambda: Dialogs.showCredits(engine), _("See who made this game.")), # evilynux - Show Credits!
          (_("Quickset"), quicksetMenu, _("A quick way to set many advanced settings.")),
          (_("See Advanced Options"), self.advancedSettings)
        ]

        self.settingsToApply = FoFiXBasicSettings + \
                               videoSettings + \
                               self.modSettings



        Menu.Menu.__init__(self, engine, settings, name = "settings", onCancel = self.applySettings, pos = (self.opt_text_x, self.opt_text_y), textColor = self.opt_text_color, selectedColor = self.opt_selected_color)   #MFH - add position to this so we can move it

    def applySettings(self):
        quickset(self.engine.config)
        if self.engine.restartRequired or self.engine.quicksetRestart:
            Dialogs.showMessage(self.engine, _("FoFiX needs to restart to apply setting changes."))
            for option in self.settingsToApply:
                if isinstance(option, ConfigChoice):
                    option.apply()
            self.engine.restart()

    def refreshKeySettings(self, init = False):
        choices = [ #the reacharound
          Menu.Choice(_("Test Controls"), self.keyChangeMenu, tipText = _("Go here to test your controllers.")),
          ActiveConfigChoice(self.engine, self.engine.config, "game", "control0", onChange = self.engine.input.reloadControls),
          ActiveConfigChoice(self.engine, self.engine.config, "game", "control1", onChange = self.engine.input.reloadControls),
          ActiveConfigChoice(self.engine, self.engine.config, "game", "control2", onChange = self.engine.input.reloadControls),
          ActiveConfigChoice(self.engine, self.engine.config, "game", "control3", onChange = self.engine.input.reloadControls),
          Menu.Choice(_("New Controller"),    lambda: createControl(self.engine, refresh = self.refreshKeySettings), tipText = _("Create a new controller to use.")),
          Menu.Choice(_("Edit Controller"),   lambda: chooseControl(self.engine, refresh = self.refreshKeySettings), tipText = _("Edit a controller you have created.")),
          Menu.Choice(_("Delete Controller"), lambda: chooseControl(self.engine, "delete", refresh = self.refreshKeySettings), tipText = _("Delete a controller you have created.")),
          ActiveConfigChoice(self.engine, self.engine.config, "game", "p2_menu_nav", onChange = self.engine.input.reloadControls),#myfingershurt
          ActiveConfigChoice(self.engine, self.engine.config, "game", "drum_navigation", onChange = self.engine.input.reloadControls),#myfingershurt
          ActiveConfigChoice(self.engine, self.engine.config, "game", "key_checker_mode", onChange = self.engine.input.reloadControls),#myfingershurt
        ]
        if init:
            return choices
        self.engine.mainMenu.settingsMenuObject.keySettingsMenu.choices = choices

    def refreshCheatSettings(self, init = False):
        choices = []
        maxplayers = self.engine.config.get("performance", "max_players")
        for i in range(maxplayers):
            choices.append(ConfigChoice(self.engine, self.engine.config, "game", "jurg_p%d" % i, autoApply = True))
        choicesb = [ConfigChoice(self.engine, self.engine.config, "game", "gh2_sloppy", autoApply = True),
          ConfigChoice(self.engine, self.engine.config, "game", "whammy_saves_starpower", autoApply = True),#myfingershurt
          ConfigChoice(self.engine, self.engine.config, "game",   "note_hit_window", autoApply = True), #alarian: defines hit window
          ConfigChoice(self.engine, self.engine.config, "coffee", "hopo_frequency", autoApply = True),
          ConfigChoice(self.engine, self.engine.config, "coffee", "failingEnabled", autoApply = True),
          ConfigChoice(self.engine, self.engine.config, "audio",  "speed_factor", autoApply = True),     #MFH
          ConfigChoice(self.engine, self.engine.config, "handicap",  "early_hit_window", autoApply = True),     #MFH
          (_("Mod settings"), self.modSettingsMenu, _("Enable or disable any mods you have installed.")),]
        choices.extend(choicesb)
        if init:
            return choices
        self.engine.mainMenu.settingsMenuObject.cheatMenu.choices = choices

    def controlCheck(self):
        control = [self.engine.config.get("game", "control0")]
        self.keyCheckerMode = Config.get("game", "key_checker_mode")
        if str(control[0]) == "None":
            Dialogs.showMessage(self.engine, _("You must specify a controller for slot 1!"))
            self.engine.view.pushLayer(self.keySettingsMenu)
        else:
            for i in range(1,4):
                c = self.engine.config.get("game", "control%d" % i)
                if c in control and str(c) != "None":
                    Dialogs.showMessage(self.engine, _("Controllers in slots %d and %d conflict. Setting %d to None.") % (control.index(c)+1, i+1, i+1))
                    self.engine.config.set("game", "control%d" % i, None)
                else:
                    control.append(c)
            self.engine.input.reloadControls()
            if len(self.engine.input.controls.overlap) > 0 and self.keyCheckerMode > 0:
                n = 0
                for i in self.engine.input.controls.overlap:
                    if n > 1:
                        Dialogs.showMessage(self.engine, _("%d more conflicts.") % (len(self.engine.input.controls.overlap)-2))
                    Dialogs.showMessage(self.engine, i)
                    n+= 1
                if self.keyCheckerMode == 2:
                    self.engine.view.pushLayer(self.keySettingsMenu)
            self.refreshKeySettings()

    def advancedSettings(self):
        Config.set("game", "adv_settings", True)
        self.engine.advSettings = True
        if not self.engine.restartRequired:
            self.engine.view.popLayer(self)
            self.engine.input.removeKeyListener(self)
        else:
            self.applySettings()

    def keyTest(self, controller):
        if str(self.engine.input.controls.controls[controller]) == "None":
            Dialogs.showMessage(self.engine, "No controller set for slot %d" % (controller+1))
        else:
            Dialogs.testKeys(self.engine, controller)

    def resetLanguageToEnglish(self):
        Log.debug("settings.resetLanguageToEnglish function call...")
        if self.engine.config.get("game", "language") != "":
            self.engine.config.set("game", "language", "")
            self.engine.restart()

    def baseLibrarySelect(self):
        Log.debug("settings.baseLibrarySelect function call...")
        newPath = Dialogs.chooseFile(self.engine, masks = ["*/*"], prompt = _("Choose a new songs directory."), dirSelect = True)
        if newPath != None:
            Config.set("setlist", "base_library", os.path.dirname(newPath))
            Config.set("setlist", "selected_library", os.path.basename(newPath))
            Config.set("setlist", "selected_song", "")
            self.engine.resource.refreshBaseLib()   #myfingershurt - to let user continue with new songpath without restart

def quickset(config):
    #akedrou - quickset (based on Fablaculp's Performance Autoset)
    perfSetNum = config.get("quickset","performance")
    gameSetNum = config.get("quickset","gameplay")

    if gameSetNum == 1:
        config.set("game", "sp_notes_while_active", 1)
        config.set("game", "bass_groove_enable", 1)
        config.set("game", "big_rock_endings", 1)
        config.set("game", "in_game_stars", 1)
        config.set("game", "mark_solo_sections", 2)
        Log.debug("Quickset Gameplay - Theme-Based")

    elif gameSetNum == 2:
        config.set("game", "sp_notes_while_active", 2)
        config.set("game", "bass_groove_enable", 2)
        config.set("game", "big_rock_endings", 2)
        config.set("game", "mark_solo_sections", 3)
        Log.debug("Quickset Gameplay - MIDI-Based")

    elif gameSetNum == 3:
        config.set("game", "sp_notes_while_active", 3)
        config.set("game", "bass_groove_enable", 3)
        config.set("game", "big_rock_endings", 2)
        config.set("game", "in_game_stars", 2)
        config.set("game", "counting", True)
        config.set("game", "mark_solo_sections", 1)
        Log.debug("Quickset Gameplay - RB style")

    elif gameSetNum == 4:
        config.set("game", "sp_notes_while_active", 0)
        config.set("game", "bass_groove_enable", 0)
        config.set("game", "big_rock_endings", 0)
        config.set("game", "in_game_stars", 0)
        config.set("game", "counting", False)
        config.set("game", "mark_solo_sections", 0)
        Log.debug("Quickset Gameplay - GH style")

    elif gameSetNum == 5: # This needs work.
        config.set("game", "sp_notes_while_active", 0)
        config.set("game", "bass_groove_enable", 0)
        config.set("game", "big_rock_endings", 0)
        config.set("game", "in_game_stars", 0)
        config.set("game", "counting", True)
        config.set("game", "mark_solo_sections", 1)
        Log.debug("Quickset Gameplay - WT style")

    # elif gameSetNum == 6: #FoFiX mode - perhaps soon.

    else:
        Log.debug("Quickset Gameplay - Manual")

    if perfSetNum == 1:
        config.set("engine", "highpriority", False)
        config.set("performance", "game_priority", 2)
        config.set("performance", "animated_notes", False)
        config.set("game", "rb_midi_lyrics", 0)
        config.set("game", "rb_midi_sections", 0)
        config.set("game", "gsolo_acc_disp", 0)
        config.set("game", "incoming_neck_mode", 0)
        config.set("game", "midi_lyric_mode", 2)
        config.set("video", "fps", 60)
        config.set("video", "multisamples", 0)
        config.set("video", "shader_use", False)
        config.set("coffee", "game_phrases", 0)
        config.set("game", "stage_animate", 0)
        config.set("game", "lyric_mode", 0)
        config.set("game", "use_graphical_submenu", 0)
        config.set("audio", "enable_crowd_tracks", 0)
        config.set("performance", "in_game_stats", 0)
        config.set("performance", "static_strings", True)
        config.set("performance", "disable_libcount", True)
        config.set("performance", "killfx", 2)
        config.set("performance", "star_score_updates", 0)
        config.set("performance", "cache_song_metadata", False)
        Log.debug("Quickset Performance - Fastest")

    elif perfSetNum == 2:
        config.set("engine", "highpriority", False)
        config.set("performance", "game_priority", 2)
        config.set("performance", "animated_notes", False)
        config.set("game", "rb_midi_lyrics", 1)
        config.set("game", "rb_midi_sections", 1)
        config.set("game", "gsolo_acc_disp", 1)
        config.set("game", "incoming_neck_mode", 1)
        config.set("game", "midi_lyric_mode", 2)
        config.set("video", "fps", 60)
        config.set("video", "multisamples", 2)
        config.set("coffee", "game_phrases", 1)
        config.set("game", "partial_stars", 1)
        config.set("game", "stage_animate", 0)
        config.set("game", "lyric_mode", 2)
        config.set("game", "use_graphical_submenu", 0)
        config.set("audio", "enable_crowd_tracks", 1)
        config.set("performance", "in_game_stats", 0)
        config.set("performance", "static_strings", True)
        config.set("performance", "disable_libcount", True)
        config.set("performance", "killfx", 0)
        config.set("performance", "star_score_updates", 0)
        config.set("performance", "cache_song_metadata", True)
        Log.debug("Quickset Performance - Fast")

    elif perfSetNum == 3:
        config.set("engine", "highpriority", False)
        config.set("performance", "game_priority", 2)
        config.set("performance", "animated_notes", True)
        config.set("game", "rb_midi_lyrics", 2)
        config.set("game", "rb_midi_sections", 2)
        config.set("game", "gsolo_acc_disp", 1)
        config.set("game", "incoming_neck_mode", 2)
        config.set("game", "midi_lyric_mode", 2)
        config.set("video", "fps", 60)
        config.set("video", "multisamples", 4)
        config.set("coffee", "game_phrases", 2)
        config.set("game", "partial_stars", 1)
        config.set("game", "lyric_mode", 2)
        config.set("game", "use_graphical_submenu", 1)
        config.set("audio", "enable_crowd_tracks", 1)
        config.set("performance", "in_game_stats", 2)
        config.set("performance", "static_strings", True)
        config.set("performance", "disable_libcount", True)
        config.set("performance", "killfx", 0)
        config.set("performance", "star_score_updates", 1)
        config.set("performance", "cache_song_metadata", True)
        Log.debug("Quickset Performance - Quality")

    elif perfSetNum == 4:
        config.set("engine", "highpriority", False)
        config.set("performance", "game_priority", 2)
        config.set("performance", "animated_notes", True)
        config.set("game", "rb_midi_lyrics", 2)
        config.set("game", "rb_midi_sections", 2)
        config.set("game", "gsolo_acc_disp", 2)
        config.set("game", "incoming_neck_mode", 2)
        config.set("game", "midi_lyric_mode", 0)
        config.set("video", "fps", 60)
        config.set("video", "multisamples", 4)
        config.set("video", "shader_use", True)
        config.set("coffee", "game_phrases", 2)
        config.set("game", "partial_stars", 1)
        config.set("game", "lyric_mode", 2)
        config.set("game", "use_graphical_submenu", 1)
        config.set("audio", "enable_crowd_tracks", 1)
        config.set("performance", "in_game_stats", 2)
        config.set("performance", "static_strings", False)
        config.set("performance", "disable_libcount", False)
        config.set("performance", "killfx", 0)
        config.set("performance", "star_score_updates", 1)
        config.set("performance", "cache_song_metadata", True)
        Log.debug("Quickset Performance - Highest Quality")

    else:
        Log.debug("Quickset Performance - Manual")

class GameSettingsMenu(Menu.Menu):
    def __init__(self, engine, gTextColor, gSelectedColor, players):

        self.logClassInits = Config.get("game", "log_class_inits")
        if self.logClassInits == 1:
            Log.debug("GameSettingsMenu class init (Settings.py)...")

        Cheats = []

        for i, player in enumerate(players):
            Cheats.append(ConfigChoice(engine, engine.config, "game", "jurg_p%d" % i, autoApply = True))#Jurgen config -- Spikehead777
            if player.part.id != VOCAL_PART:
                Cheats.append(ConfigChoice(engine, engine.config, "game", "jurg_logic_p%d" % i, autoApply = True))#MFH
             #MFH
        CheatMenu = Menu.Menu(engine, Cheats, pos = (.350, .310), viewSize = 5, textColor = gTextColor, selectedColor = gSelectedColor)

        settings = [
          (_("Cheats"), CheatMenu),
          VolumeConfigChoice(engine, engine.config, "audio",  "guitarvol", autoApply = True),
          VolumeConfigChoice(engine, engine.config, "audio",  "songvol", autoApply = True),
          VolumeConfigChoice(engine, engine.config, "audio",  "screwupvol", autoApply = True),
          VolumeConfigChoice(engine, engine.config, "audio",  "miss_volume", autoApply = True),
          VolumeConfigChoice(engine, engine.config, "audio",  "single_track_miss_volume", autoApply = True),
          VolumeConfigChoice(engine, engine.config, "audio",  "crowd_volume", autoApply = True),
          VolumeConfigChoice(engine, engine.config, "audio",  "kill_volume", autoApply = True), #MFH
          ActiveConfigChoice(engine, engine.config, "audio",  "SFX_volume", autoApply = True, onChange = engine.data.SetAllSoundFxObjectVolumes, volume = True), #MFH
          ConfigChoice(engine, engine.config, "audio", "enable_crowd_tracks", autoApply = True), #akedrou
          ConfigChoice(engine, engine.config, "audio",  "delay", autoApply = True),   #myfingershurt: so the a/v delay can be adjusted in-game
          ConfigChoice(engine, engine.config, "game", "stage_rotate_delay", autoApply = True),   #myfingershurt - user defined stage rotate delay
          ConfigChoice(engine, engine.config, "game", "stage_animate_delay", autoApply = True),   #myfingershurt - user defined stage rotate delay
        ]
        Menu.Menu.__init__(self, engine, settings, pos = (.360, .250), viewSize = 5, textColor = gTextColor, selectedColor = gSelectedColor, showTips = False) #Worldrave- Changed Pause-Submenu Position more centered until i add a theme.ini setting.

class GameCareerSettingsMenu(Menu.Menu):
    def __init__(self, engine, gTextColor, gSelectedColor, players):

        self.logClassInits = Config.get("game", "log_class_inits")
        if self.logClassInits == 1:
            Log.debug("GameSettingsMenu class init (Settings.py)...")
        settings = [
          VolumeConfigChoice(engine, engine.config, "audio",  "guitarvol", autoApply = True),
          VolumeConfigChoice(engine, engine.config, "audio",  "songvol", autoApply = True),
          VolumeConfigChoice(engine, engine.config, "audio",  "screwupvol", autoApply = True),
          VolumeConfigChoice(engine, engine.config, "audio",  "miss_volume", autoApply = True),
          VolumeConfigChoice(engine, engine.config, "audio",  "single_track_miss_volume", autoApply = True),
          VolumeConfigChoice(engine, engine.config, "audio",  "crowd_volume", autoApply = True),
          VolumeConfigChoice(engine, engine.config, "audio",  "kill_volume", autoApply = True), #MFH
          ActiveConfigChoice(engine, engine.config, "audio",  "SFX_volume", autoApply = True, onChange = engine.data.SetAllSoundFxObjectVolumes, volume = True), #MFH
          ConfigChoice(engine, engine.config, "audio", "enable_crowd_tracks", autoApply = True), #akedrou
          ConfigChoice(engine, engine.config, "audio",  "delay", autoApply = True),   #myfingershurt: so the a/v delay can be adjusted in-game
          ConfigChoice(engine, engine.config, "game", "stage_rotate_delay", autoApply = True),   #myfingershurt - user defined stage rotate delay
          ConfigChoice(engine, engine.config, "game", "stage_animate_delay", autoApply = True),   #myfingershurt - user defined stage rotate delay
        ]
        Menu.Menu.__init__(self, engine, settings, pos = (.360, .250), viewSize = 5, textColor = gTextColor, selectedColor = gSelectedColor, showTips = False) #Worldrave- Changed Pause-Submenu Position more centered until i add a theme.ini setting.
