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

import Menu
from Language import _
import Dialogs
import Config
import Mod
import Audio

import pygame
import os

import Log

import Theme

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
    Menu.Choice.__init__(self, text = o.text, callback = self.change, values = values, valueIndex = valueIndex)
    
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
    
    if self.autoApply:
      self.apply()
    else:
      self.engine.restartRequired = True

  def apply(self):
    if self.changed:
      self.config.set(self.section, self.option, self.value)

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
  def __init__(self, engine, config, section, option):
    self.engine  = engine

    self.logClassInits = self.engine.config.get("game", "log_class_inits")
    if self.logClassInits == 1:
      Log.debug("KeyConfigChoice class init (Settings.py)...")

    self.config  = config
    self.section = section
    self.option  = option
    self.changed = False
    self.value   = None

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
    return "%s: %s" % (o.text, pygame.key.name(keycode(v)).capitalize())
    
  def change(self):
    o = self.config.prototype[self.section][self.option]

    if isinstance(o.options, dict):
      for k, v in o.options.items():
        if v == value:
          value = k
          break

    key = Dialogs.getKey(self.engine, _("Press a key for '%s' or Escape to cancel.") % (o.text))

    if key:
      #------------------------------------------
      
      #myfingershurt: key conflict checker operation mode
      if self.keyCheckerMode == 2:    #enforce; do not allow conflicting key assignments, force reversion
        # glorandwarf: sets the new key mapping and checks for a conflict
        if self.engine.input.setNewKeyMapping(self.section, self.option, key) == False:
          # key mapping would conflict, warn the user
          Dialogs.showMessage(self.engine, _("That key is already in use. Please choose another."))
        self.engine.input.reloadControls()

      elif self.keyCheckerMode == 1:    #just notify, but allow the change
        # glorandwarf: sets the new key mapping and checks for a conflict
        if self.engine.input.setNewKeyMapping(self.section, self.option, key) == False:
          # key mapping would conflict, warn the user
          Dialogs.showMessage(self.engine, _("A key conflict exists somewhere. You should fix it."))
        self.engine.input.reloadControls()
      
      else:   #don't even check.
        # glorandwarf: sets the new key mapping and checks for a conflict
        temp = self.engine.input.setNewKeyMapping(self.section, self.option, key)
          # key mapping would conflict, warn the user
        self.engine.input.reloadControls()
      
      
      
      #------------------------------------------

  def apply(self):
    pass

class SettingsMenu(Menu.Menu):
  def __init__(self, engine):

    self.engine = engine
    self.logClassInits = self.engine.config.get("game", "log_class_inits")
    if self.logClassInits == 1:
      Log.debug("SettingsMenu class init (Settings.py)...")

    modSettings = [
      ConfigChoice(engine, engine.config, "mods",  "mod_" + m) for m in Mod.getAvailableMods(engine)
    ]
    
    StagesOptions = [
      ConfigChoice(engine, engine.config, "game", "stage_mode", autoApply = True),   #myfingershurt
      ConfigChoice(engine, engine.config, "game", "animated_stage_folder", autoApply = True),   #myfingershurt
      ConfigChoice(engine, engine.config, "game", "song_stage", autoApply = True),   #myfingershurt
      ConfigChoice(engine, engine.config, "game", "rotate_stages", autoApply = True),   #myfingershurt
      ConfigChoice(engine, engine.config, "game", "stage_rotate_delay", autoApply = True),   #myfingershurt - user defined stage rotate delay
      ConfigChoice(engine, engine.config, "game", "stage_animate", autoApply = True),   #myfingershurt - user defined stage rotate delay
      ConfigChoice(engine, engine.config, "game", "stage_animate_delay", autoApply = True),   #myfingershurt - user defined stage rotate delay
      ConfigChoice(engine, engine.config, "game", "miss_pauses_anim", autoApply = True),
    ]
    StagesOptionsMenu = Menu.Menu(engine, StagesOptions)
    
    HOPOSettings = [
       ConfigChoice(engine, engine.config, "game", "hopo_system", autoApply = True),      #myfingershurt
       ConfigChoice(engine, engine.config, "coffee", "hopo_frequency", autoApply = True),
       ConfigChoice(engine, engine.config, "game", "song_hopo_freq", autoApply = True),      #myfingershurt
       ConfigChoice(engine, engine.config, "game", "hopo_after_chord", autoApply = True),      #myfingershurt
    ]
    HOPOSettingsMenu = Menu.Menu(engine, HOPOSettings)
    
    LyricsSettings = [
       ConfigChoice(engine, engine.config, "game", "rb_midi_lyrics", autoApply = True, isQuickset = 1),      #myfingershurt
       ConfigChoice(engine, engine.config, "game", "midi_lyric_mode", autoApply = True, isQuickset = 1),      #myfingershurt
       ConfigChoice(engine, engine.config, "game", "rb_midi_sections", autoApply = True, isQuickset = 1),      #myfingershurt
       ConfigChoice(engine, engine.config, "game", "lyric_mode", autoApply = True, isQuickset = 1),      #myfingershurt
       ConfigChoice(engine, engine.config, "game", "script_lyric_pos", autoApply = True),      #myfingershurt
    ]
    LyricsSettingsMenu = Menu.Menu(engine, LyricsSettings)
    
    JurgenSettings = [
       ConfigChoice(engine, engine.config, "game", "jurgmode", autoApply = True),#Spikehead777
       ConfigChoice(engine, engine.config, "game", "jurgtype", autoApply = True),#Spikehead777
       ConfigChoice(engine, engine.config, "game", "jurglogic", autoApply = True),#MFH
       ConfigChoice(engine, engine.config, "game", "jurgtext", autoApply = True),#hman
    ]
    JurgenSettingsMenu = Menu.Menu(engine, JurgenSettings)
           
    FoFiXAdvancedSettings = [
      ConfigChoice(engine, engine.config, "game",   "note_hit_window", autoApply = True), #alarian: defines hit window
      ConfigChoice(engine, engine.config, "performance", "star_score_updates", autoApply = True, isQuickset = 1),   #MFH
      ConfigChoice(engine, engine.config, "game", "bass_groove_enable", autoApply = True, isQuickset = 2),#myfingershurt
      ConfigChoice(engine, engine.config, "game", "lphrases", autoApply = True),#blazingamer
      ConfigChoice(engine, engine.config, "game", "decimal_places", autoApply = True), #MFH
      ConfigChoice(engine, engine.config, "game", "ignore_open_strums", autoApply = True),      #myfingershurt
      ConfigChoice(engine, engine.config, "game", "big_rock_endings", autoApply = True, isQuickset = 2),#myfingershurt
      ConfigChoice(engine, engine.config, "game", "big_rock_logic", autoApply = True),	#volshebnyi
      ConfigChoice(engine, engine.config, "game", "starpower_mode", autoApply = True),#myfingershurt
      ConfigChoice(engine, engine.config, "game", "party_time", autoApply = True),
    ]
    FoFiXAdvancedSettingsMenu = Menu.Menu(engine, FoFiXAdvancedSettings)
    
    FoFiXBasicSettings = [
      ConfigChoice(engine, engine.config, "game",  "language"),
      ConfigChoice(engine, engine.config, "game", "T_sound", autoApply = True), #Faaa Drum sound
      ConfigChoice(engine, engine.config, "game", "star_scoring", autoApply = True),#myfingershurt
      ConfigChoice(engine, engine.config, "game", "resume_countdown", autoApply = True), #akedrou
      ConfigChoice(engine, engine.config, "game", "whammy_saves_starpower", autoApply = True),#myfingershurt
      ConfigChoice(engine, engine.config, "game", "sp_notes_while_active", autoApply = True, isQuickset = 2),   #myfingershurt - setting for gaining more SP while active
      ConfigChoice(engine, engine.config, "game", "drum_sp_mode", autoApply = True),#myfingershurt
      ConfigChoice(engine, engine.config, "game",  "uploadscores", autoApply = True),
      ConfigChoice(engine, engine.config, "audio",  "delay", autoApply = True),     #myfingershurt: so a/v delay can be set without restarting FoF
      (_("Advanced Gameplay Settings"), FoFiXAdvancedSettings),
      (_("HO/PO Settings"), HOPOSettingsMenu),
    ]
    FoFiXBasicSettingsMenu = Menu.Menu(engine, FoFiXBasicSettings)
    
    drumKeySettings = [
      KeyConfigChoice(engine, engine.config, "player0", "key_bass"),
      KeyConfigChoice(engine, engine.config, "player0", "key_drum1a"),
      KeyConfigChoice(engine, engine.config, "player0", "key_drum1b"),
      KeyConfigChoice(engine, engine.config, "player0", "key_drum2a"),
      KeyConfigChoice(engine, engine.config, "player0", "key_drum2b"),
      KeyConfigChoice(engine, engine.config, "player0", "key_drum3a"),
      KeyConfigChoice(engine, engine.config, "player0", "key_drum3b"),
      KeyConfigChoice(engine, engine.config, "player0", "key_drum4a"),
      KeyConfigChoice(engine, engine.config, "player0", "key_drum4b"),
      KeyConfigChoice(engine, engine.config, "player0", "key_drum_up"), #shun - directionals
      KeyConfigChoice(engine, engine.config, "player0", "key_drum_down"),
      KeyConfigChoice(engine, engine.config, "player0", "key_drum_left"),
      KeyConfigChoice(engine, engine.config, "player0", "key_drum_right"),
      KeyConfigChoice(engine, engine.config, "player0", "key_drum_cancel"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_bass"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_drum1a"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_drum1b"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_drum2a"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_drum2b"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_drum3a"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_drum3b"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_drum4a"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_drum4b"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_drum_up"), #shun - directionals
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_drum_down"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_drum_left"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_drum_right"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_drum_cancel"),

    ]       
    drumKeySettingsMenu = Menu.Menu(engine, drumKeySettings)

#shun - alternate drum keys
    altDrumKeySettings = [
      #ConfigChoice(engine.config, "game", "auto_drum_sp", autoApply = True),#myfingershurt #shun- probably not needed for alt(?)
      KeyConfigChoice(engine, engine.config, "player0", "akey_bass"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_drum1a"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_drum1b"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_drum2a"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_drum2b"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_drum3a"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_drum3b"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_drum4a"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_drum4b"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_drum_up"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_drum_down"), #shun - directionals
      KeyConfigChoice(engine, engine.config, "player0", "akey_drum_left"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_drum_right"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_drum_cancel"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_bass"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_drum1a"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_drum1b"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_drum2a"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_drum2b"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_drum3a"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_drum3b"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_drum4a"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_drum4b"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_drum_up"), # shun -directionals
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_drum_down"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_drum_left"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_drum_right"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_drum_cancel"),
    ]       
    altDrumKeySettingsMenu = Menu.Menu(engine, altDrumKeySettings)

    player0Keys = [
      KeyConfigChoice(engine, engine.config, "player0", "key_action1"),
      KeyConfigChoice(engine, engine.config, "player0", "key_action2"),
      KeyConfigChoice(engine, engine.config, "player0", "key_1"),
      KeyConfigChoice(engine, engine.config, "player0", "key_2"),
      KeyConfigChoice(engine, engine.config, "player0", "key_3"),
      KeyConfigChoice(engine, engine.config, "player0", "key_4"),
      KeyConfigChoice(engine, engine.config, "player0", "key_5"),
      KeyConfigChoice(engine, engine.config, "player0", "key_left"),
      KeyConfigChoice(engine, engine.config, "player0", "key_right"),
      KeyConfigChoice(engine, engine.config, "player0", "key_up"),
      KeyConfigChoice(engine, engine.config, "player0", "key_down"),
      KeyConfigChoice(engine, engine.config, "player0", "key_cancel"),
      KeyConfigChoice(engine, engine.config, "player0", "key_star"),
      KeyConfigChoice(engine, engine.config, "player0", "key_kill"),
    ]
    player0KeyMenu = Menu.Menu(engine, player0Keys)

    player0AltKeys = [
      KeyConfigChoice(engine, engine.config, "player0", "akey_action1"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_action2"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_1"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_2"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_3"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_4"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_5"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_left"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_right"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_up"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_down"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_cancel"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_star"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_kill"),
    ]
    player0AltKeyMenu = Menu.Menu(engine, player0AltKeys)

    player1Keys = [
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_action1"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_action2"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_1"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_2"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_3"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_4"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_5"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_left"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_right"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_up"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_down"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_cancel"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_star"),#added by ShiekOdaSandz
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_kill"),#added by ShiekOdaSandz
    ]
    player1KeyMenu = Menu.Menu(engine, player1Keys)

    player1AltKeys = [
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_action1"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_action2"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_1"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_2"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_3"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_4"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_5"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_left"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_right"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_up"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_down"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_cancel"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_star"),#added by ShiekOdaSandz
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_kill"),#added by ShiekOdaSandz
    ]
    player1AltKeyMenu = Menu.Menu(engine, player1AltKeys)
    
    KeyChangeSettings = [
      ConfigChoice(engine, engine.config, "game", "key_checker_mode", autoApply = True),#myfingershurt
      (_("Player 1 Keys"), player0KeyMenu),
      (_("Player 1 Alt. Keys"), player0AltKeyMenu),
      (_("Player 2 Keys"), player1KeyMenu),
      (_("Player 2 Alt. Keys"), player1AltKeyMenu),
      (_("Drum Keys" ), drumKeySettingsMenu),
      (_("Alt. Drum Keys" ), altDrumKeySettingsMenu),
    ]
    KeyChangeMenu = Menu.Menu(engine, KeyChangeSettings)

    keySettings = [
      ConfigChoice(engine, engine.config, "game", "alt_keys", autoApply = True),
      (_("Change Controls"), KeyChangeMenu),
      (_("Test Guitars"), lambda: Dialogs.testKeys(engine)),
      (_("Test Drums"), lambda: Dialogs.testDrums(engine)),
      ConfigChoice(engine, engine.config, "game", "p2_menu_nav", autoApply = True),#myfingershurt
      ConfigChoice(engine, engine.config, "game", "drum_navigation", autoApply = True),#myfingershurt
      ConfigChoice(engine, engine.config, "game", "analog_killsw_mode", autoApply = True),#myfingershurt
      ConfigChoice(engine, engine.config, "game", "analog_killsw_mode_p2", autoApply = True),#myfingershurt
      ConfigChoice(engine, engine.config, "player0",  "leftymode", autoApply = True),
      ConfigChoice(engine, engine.config, "player1",  "leftymode", autoApply = True), #QQstarS
      ConfigChoice(engine, engine.config, "player0",  "two_chord_max", autoApply = True),
      ConfigChoice(engine, engine.config, "player1",  "two_chord_max", autoApply = True), #QQstarS
    ]
    keySettingsMenu = Menu.Menu(engine, keySettings)
    
    fretSettings = [
      ConfigChoice(engine, engine.config, "fretboard", "point_of_view", autoApply = True, isQuickset = 2),
      ConfigChoice(engine, engine.config, "game", "notedisappear", autoApply = True),
      ConfigChoice(engine, engine.config, "game", "frets_under_notes", autoApply = True), #MFH
      ConfigChoice(engine, engine.config, "game", "nstype", autoApply = True),      #blazingamer
      ConfigChoice(engine, engine.config, "coffee", "neckSpeed", autoApply = True),
      ConfigChoice(engine, engine.config, "game", "large_drum_neck", autoApply = True),      #myfingershurt
      ConfigChoice(engine, engine.config, "game", "bass_groove_neck", autoApply = True),      #myfingershurt
      ConfigChoice(engine, engine.config, "game", "guitar_solo_neck", autoApply = True),      #myfingershurt
      ConfigChoice(engine, engine.config, "game", "incoming_neck_mode", autoApply = True, isQuickset = 1),      #myfingershurt
    ]
    fretSettingsMenu = Menu.Menu(engine, fretSettings)
    
    AdvancedVideoSettings = [
      ConfigChoice(engine, engine.config, "video",  "fps"),
      ConfigChoice(engine, engine.config, "game", "accuracy_pos", autoApply = True),
      ConfigChoice(engine, engine.config, "game", "gsolo_acc_pos", autoApply = True, isQuickset = 1), #MFH
      ConfigChoice(engine, engine.config, "coffee", "noterotate", autoApply = True), #blazingamer
      ConfigChoice(engine, engine.config, "game", "gfx_version_tag", autoApply = True), #MFH
      ConfigChoice(engine, engine.config, "video",  "multisamples", isQuickset = 1),
      ConfigChoice(engine, engine.config, "game", "in_game_font_shadowing", autoApply = True),      #myfingershurt
      ConfigChoice(engine, engine.config, "performance", "preload_glyph_cache", autoApply = True, isQuickset = 1),#evilynux
      ConfigChoice(engine, engine.config, "performance", "static_strings", autoApply = True, isQuickset = 1),      #myfingershurt
      ConfigChoice(engine, engine.config, "performance", "killfx", autoApply = True, isQuickset = 1),   #blazingamer
    ]
    AdvancedVideoSettingsMenu = Menu.Menu(engine, AdvancedVideoSettings)
    
    ThemeDisplaySettings = [
      ConfigChoice(engine, engine.config, "game", "rb_sp_neck_glow", autoApply = True),
      ConfigChoice(engine, engine.config, "game",   "small_rb_mult", autoApply = True), #blazingamer
      ConfigChoice(engine, engine.config, "game", "rbnote", autoApply = True), #racer
      ConfigChoice(engine, engine.config, "game", "starfx", autoApply = True),
      ConfigChoice(engine, engine.config, "performance", "starspin", autoApply = True, isQuickset = 1),
    ]
    ThemeDisplayMenu = Menu.Menu(engine, ThemeDisplaySettings)
    
    InGameDisplaySettings = [
      (_("Theme Display Settings"), ThemeDisplayMenu),
      ConfigChoice(engine, engine.config, "game", "in_game_stars", autoApply = True, isQuickset = 2),#myfingershurt
      ConfigChoice(engine, engine.config, "game", "partial_stars", autoApply = True, isQuickset = 1),#myfingershurt
      ConfigChoice(engine, engine.config, "performance", "star_continuous_fillup", autoApply = True, isQuickset = 1), #stump
      ConfigChoice(engine, engine.config, "coffee", "game_phrases", autoApply = True, isQuickset = 1),
      ConfigChoice(engine, engine.config, "game", "hopo_indicator", autoApply = True),
      ConfigChoice(engine, engine.config, "game", "accuracy_mode", autoApply = True),
      ConfigChoice(engine, engine.config, "performance", "in_game_stats", autoApply = True, isQuickset = 1),#myfingershurt
      ConfigChoice(engine, engine.config, "game", "gsolo_accuracy_disp", autoApply = True, isQuickset = 1), #MFH
      ConfigChoice(engine, engine.config, "game", "solo_frame", autoApply = True),      #myfingershurt
      ConfigChoice(engine, engine.config, "video", "disable_fretsfx", autoApply = True),
      ConfigChoice(engine, engine.config, "video", "hitglow_color", autoApply = True),
      ConfigChoice(engine, engine.config, "game", "game_time", autoApply = True),  
      ConfigChoice(engine, engine.config, "video", "counting", autoApply = True, isQuickset = 2),
    ]
    InGameDisplayMenu = Menu.Menu(engine, InGameDisplaySettings)
      
    modes = engine.video.getVideoModes()
    modes.reverse()
    Config.define("video",  "resolution", str,   "1024x768", text = _("Video Resolution"), options = ["%dx%d" % (m[0], m[1]) for m in modes])
    videoSettings = [
      ConfigChoice(engine, engine.config, "coffee", "themename"), #was autoapply... why?
      ConfigChoice(engine, engine.config, "video",  "resolution"),
      ConfigChoice(engine, engine.config, "video",  "fullscreen"),
      (_("Stages Options"), StagesOptionsMenu),
      (_("Choose P1 Neck >"), lambda: Dialogs.chooseNeck(engine,player=0,prompt=_("Yellow (#3) / Blue (#4) to change:"))),
      (_("Choose P2 Neck >"), lambda: Dialogs.chooseNeck(engine,player=1,prompt=_("Yellow (#3) / Blue (#4) to change:"))),
      (_("Fretboard Settings"), fretSettingsMenu),
      (_("Lyrics Settings"), LyricsSettingsMenu),
      (_("In-Game Display Settings"), InGameDisplayMenu),
      (_("Advanced Video Settings"), AdvancedVideoSettingsMenu),
    ]
    videoSettingsMenu = Menu.Menu(engine, videoSettings)

    
    volumeSettings = [
      VolumeConfigChoice(engine, engine.config, "audio",  "guitarvol", autoApply = True),
      VolumeConfigChoice(engine, engine.config, "audio",  "songvol", autoApply = True),
      VolumeConfigChoice(engine, engine.config, "audio",  "rhythmvol", autoApply = True),
      VolumeConfigChoice(engine, engine.config, "audio",  "screwupvol", autoApply = True),
      VolumeConfigChoice(engine, engine.config, "audio",  "miss_volume", autoApply = True),
      VolumeConfigChoice(engine, engine.config, "audio",  "single_track_miss_volume", autoApply = True),
      VolumeConfigChoice(engine, engine.config, "audio",  "crowd_volume", autoApply = True), #akedrou
      VolumeConfigChoice(engine, engine.config, "audio",  "kill_volume", autoApply = True), #MFH
      VolumeConfigChoice(engine, engine.config, "audio",  "SFX_volume", autoApply = True), #MFH
    ]
    volumeSettingsMenu = Menu.Menu(engine, volumeSettings)
    
    AdvancedAudioSettings = [
       ConfigChoice(engine, engine.config, "audio",  "frequency"),
       ConfigChoice(engine, engine.config, "audio",  "bits"),
       ConfigChoice(engine, engine.config, "audio",  "buffersize"),
       ConfigChoice(engine, engine.config, "game", "result_cheer_loop", autoApply = True), #MFH
       ConfigChoice(engine, engine.config, "game", "cheer_loop_delay", autoApply = True), #MFH
    ]
    AdvancedAudioSettingsMenu = Menu.Menu(engine, AdvancedAudioSettings)

    audioSettings = [
      (_("Volume Settings"),    volumeSettingsMenu),
      ConfigChoice(engine, engine.config, "game", "sustain_muting", autoApply = True),   #myfingershurt
      ConfigChoice(engine, engine.config, "audio", "mute_last_second", autoApply = True), #MFH
      ConfigChoice(engine, engine.config, "game", "bass_kick_sound", autoApply = True),   #myfingershurt
      ConfigChoice(engine, engine.config, "game", "star_claps", autoApply = True),      #myfingershurt
      ConfigChoice(engine, engine.config, "game", "beat_claps", autoApply = True), #racer
      ConfigChoice(engine, engine.config, "audio",  "whammy_effect", autoApply = True),     #MFH
      ConfigChoice(engine, engine.config, "audio", "enable_crowd_tracks", autoApply = True), #akedrou: I don't like this here, but "audio" menu is empty of choices.
      (_("Advanced Audio Settings"), AdvancedAudioSettingsMenu),
    ]
    audioSettingsMenu = Menu.Menu(engine, audioSettings)
    
    #MFH - new menu
    logfileSettings = [
      ConfigChoice(engine, engine.config, "game", "log_ini_reads", autoApply = True),#myfingershurt
      ConfigChoice(engine, engine.config, "game", "log_class_inits", autoApply = True),#myfingershurt
      ConfigChoice(engine, engine.config, "game", "log_loadings", autoApply = True),#myfingershurt
      ConfigChoice(engine, engine.config, "game", "log_sections", autoApply = True),#myfingershurt
      ConfigChoice(engine, engine.config, "game", "log_undefined_gets", autoApply = True),#myfingershurt
      ConfigChoice(engine, engine.config, "game", "log_marker_notes", autoApply = True),#myfingershurt
      ConfigChoice(engine, engine.config, "game", "log_starpower_misses", autoApply = True),#myfingershurt
      ConfigChoice(engine, engine.config, "log",   "log_unedited_midis", autoApply = True),#myfingershurt
    ]
    logfileSettingsMenu = Menu.Menu(engine, logfileSettings)

    debugSettings = [
      ConfigChoice(engine, engine.config, "video", "show_fps", autoApply = True),#evilynux
      ConfigChoice(engine, engine.config, "game", "kill_debug", autoApply = True),#myfingershurt
      ConfigChoice(engine, engine.config, "game", "hopo_debug_disp", autoApply = True),#myfingershurt
      ConfigChoice(engine, engine.config, "game", "rock_band_events", autoApply = True),#myfingershurt
      ConfigChoice(engine, engine.config, "game", "show_unused_text_events", autoApply = True),#myfingershurt
      ConfigChoice(engine, engine.config, "debug",   "use_unedited_midis", autoApply = True),#myfingershurt
      #ConfigChoice(engine.config, "game", "font_rendering_mode", autoApply = True),#myfingershurt
      ConfigChoice(engine, engine.config, "debug",   "show_freestyle_active", autoApply = True),#myfingershurt
    ]
    debugSettingsMenu = Menu.Menu(engine, debugSettings)
    
    quickSettings = [
      ConfigChoice(engine, engine.config, "quickset", "performance", autoApply = True),
      ConfigChoice(engine, engine.config, "quickset", "gameplay", autoApply = True),
    ]
    quicksetMenu = Menu.Menu(engine, quickSettings)

    listSettings = [
      (_("Change Setlist Path >"), self.baseLibrarySelect),
      ConfigChoice(engine, engine.config, "coffee", "song_display_mode", autoApply = True),
      ConfigChoice(engine, engine.config, "game",  "sort_order", autoApply = True),
      ConfigChoice(engine, engine.config, "game", "sort_direction", autoApply = True),
      ConfigChoice(engine, engine.config, "game", "song_listing_mode", autoApply = True, isQuickset = 2),
      ConfigChoice(engine, engine.config, "game", "quickplay_tiers", autoApply = True),  #myfingershurt
      ConfigChoice(engine, engine.config, "coffee", "songfilepath", autoApply = True),
      #(_("Select List All Folder >"), self.listAllFolderSelect), #- Not Working Yet - Qstick
      ConfigChoice(engine, engine.config, "game", "songcovertype", autoApply = True),
      ConfigChoice(engine, engine.config, "game", "songlistrotation", autoApply = True, isQuickset = 1),
      ConfigChoice(engine, engine.config, "performance", "disable_librotation", autoApply = True),
      ConfigChoice(engine, engine.config, "game", "song_icons", autoApply = True),
      ConfigChoice(engine, engine.config, "game", "preload_labels", autoApply = True),
      ConfigChoice(engine, engine.config, "audio", "disable_preview", autoApply = True),  #myfingershurt
      ConfigChoice(engine, engine.config, "game", "songlist_instrument", autoApply = True), #MFH
      ConfigChoice(engine, engine.config, "game", "songlist_difficulty", autoApply = True), #evilynux
      ConfigChoice(engine, engine.config, "game",  "whammy_changes_sort_order", autoApply = True), #stump
      ConfigChoice(engine, engine.config, "game", "songlist_extra_stats", autoApply = True), #evilynux
      ConfigChoice(engine, engine.config, "game", "HSMovement", autoApply = True), #racer
      ConfigChoice(engine, engine.config, "performance", "disable_libcount", autoApply = True), 
      ConfigChoice(engine, engine.config, "performance", "cache_song_metadata", autoApply = True, isQuickset = 1), #stump
    ]
    listSettingsMenu = Menu.Menu(engine, listSettings)
    
    
    AdvancedSettings = [
      ConfigChoice(engine, engine.config, "performance", "game_priority", autoApply = True, isQuickset = 1),
      (_("Debug Settings"), debugSettingsMenu),
      (_("Log Settings"),    logfileSettingsMenu),
    ]
    AdvancedSettingsMenu = Menu.Menu(engine, AdvancedSettings)
    
    Cheats = [
      ConfigChoice(engine, engine.config, "game", "jurgmode", autoApply = True),
      (_("Jurgen Settings"), JurgenSettingsMenu),
      ConfigChoice(engine, engine.config, "game", "gh2_sloppy", autoApply = True),
      ConfigChoice(engine, engine.config, "game", "hit_window_cheat", autoApply = True),
      ConfigChoice(engine, engine.config, "coffee", "hopo_freq_cheat", autoApply = True),
      ConfigChoice(engine, engine.config, "coffee", "failingEnabled", autoApply = True),
      ConfigChoice(engine, engine.config, "audio",  "slow_down_divisor", autoApply = True),     #MFH
      (_("Mod settings"), modSettings),
    ]
    CheatMenu = Menu.Menu(engine, Cheats)
    
    settings = [
      (_("Gameplay Settings"),   FoFiXBasicSettingsMenu),
      (_("Control Settings"),          keySettingsMenu),
      (_("Display Settings"),     videoSettingsMenu),
      (_("Audio Settings"),      audioSettingsMenu),
      (_("Setlist Settings"),   listSettingsMenu),
      (_("Advanced Settings"), AdvancedSettingsMenu),
      (_("Mods, Cheats, AI"), CheatMenu),
      (_("%s Credits") % (engine.versionString), lambda: Dialogs.showCredits(engine)), # evilynux - Show Credits!
      (_("Quickset"), quicksetMenu),
      (_("Hide Advanced Options"), self.advancedSettings)
    ]
  
    self.settingsToApply = videoSettings + \
                           AdvancedAudioSettings + \
			                     AdvancedVideoSettings + \
                           FoFiXBasicSettings + \
                           InGameDisplaySettings + \
                           ThemeDisplaySettings + \
                           quickSettings + \
                           modSettings

#-    self.settingsToApply = settings + \
#-                           videoSettings + \
#-                           AdvancedAudioSettings + \
#-                           volumeSettings + \
#-                           keySettings + \
#-			                     AdvancedVideoSettings + \
#-                           FoFiXBasicSettings + \11/26/2008 11:10:30 PM
#-                           perfSettings + \
#-                           listSettings + \
#-                           modSettings

    self.opt_text_x = Theme.opt_text_xPos
    self.opt_text_y = Theme.opt_text_yPos

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


    self.opt_text_color = Theme.hexToColor(Theme.opt_text_colorVar)
    self.opt_selected_color = Theme.hexToColor(Theme.opt_selected_colorVar)

    Log.debug("Option text / selected hex colors: " + Theme.opt_text_colorVar + " / " + Theme.opt_selected_colorVar)


    if self.opt_text_color == None:
      self.opt_text_color = (1,1,1)
    if self.opt_selected_color == None:
      self.opt_selected_color = (1,0.75,0)

    Log.debug("Option text / selected colors: " + str(self.opt_text_color) + " / " + str(self.opt_selected_color))



    Menu.Menu.__init__(self, engine, settings, onCancel = self.applySettings, pos = (self.opt_text_x, self.opt_text_y), textColor = self.opt_text_color, selectedColor = self.opt_selected_color)   #MFH - add position to this so we can move it

  def quickset(self):
    #akedrou - quickset (based on Fablaculp's Performance Autoset)
    self.config = self.engine.config
    perfSetNum = self.config.get("quickset","performance")
    gameSetNum = self.config.get("quickset","gameplay")
    
    if gameSetNum == 1:
      self.config.set("game", "sp_notes_while_active", 1)
      self.config.set("game", "bass_groove_enable", 1)
      self.config.set("game", "big_rock_endings", 1)
      self.config.set("game", "in_game_stars", 1)
      self.config.set("coffee", "song_display_mode", 4)
      Log.debug("Quickset Gameplay - Theme-Based")
      
    elif gameSetNum == 2:
      self.config.set("game", "sp_notes_while_active", 2)
      self.config.set("game", "bass_groove_enable", 2)
      self.config.set("game", "big_rock_endings", 2)
      Log.debug("Quickset Gameplay - MIDI-Based")
      
    elif gameSetNum == 3:
      self.config.set("game", "sp_notes_while_active", 3)
      self.config.set("game", "bass_groove_enable", 3)
      self.config.set("game", "big_rock_endings", 2)
      self.config.set("game", "in_game_stars", 2)
      self.config.set("game", "counting", True)
      Log.debug("Quickset Gameplay - RB style")
      
    elif gameSetNum == 4:
      self.config.set("game", "sp_notes_while_active", 0)
      self.config.set("game", "bass_groove_enable", 0)
      self.config.set("game", "big_rock_endings", 0)
      self.config.set("game", "in_game_stars", 0)
      self.config.set("coffee", "song_display_mode", 1)
      self.config.set("game", "counting", False)
      Log.debug("Quickset Gameplay - GH style")
      
    elif gameSetNum == 5: # This needs work.
      self.config.set("game", "sp_notes_while_active", 0)
      self.config.set("game", "bass_groove_enable", 0)
      self.config.set("game", "big_rock_endings", 0)
      self.config.set("game", "in_game_stars", 0)
      self.config.set("coffee", "song_display_mode", 1)
      self.config.set("game", "counting", True)
      Log.debug("Quickset Gameplay - WT style")
      
    # elif gameSetNum == 6: #FoFiX mode - perhaps soon.
      
    else:
      Log.debug("Quickset Gameplay - Manual")
    
    if perfSetNum == 1:
      self.config.set("performance", "game_priority", 2)
      self.config.set("performance", "starspin", False)
      self.config.set("game", "rb_midi_lyrics", 0)
      self.config.set("game", "rb_midi_sections", 0)
      self.config.set("game", "gsolo_acc_disp", 0)
      self.config.set("game", "incoming_neck_mode", 0)
      self.config.set("game", "midi_lyric_mode", 2)
      self.config.set("video", "multisamples", 0)
      self.config.set("coffee", "game_phrases", 0)
      self.config.set("game", "partial_stars", 0)
      self.config.set("game", "songlistrotation", False)
      self.config.set("game", "song_listing_mode", 0)
      self.config.set("game", "song_display_mode", 1)
      self.config.set("game", "stage_animate", 0)
      self.config.set("game", "lyric_mode", 0)
      self.config.set("audio", "enable_crowd_tracks", 0)
      self.config.set("performance", "in_game_stats", 0)
      self.config.set("performance", "static_strings", True)
      self.config.set("performance", "killfx", 2)
      self.config.set("performance", "star_score_updates", 0)
      self.config.set("performance", "preload_glyph_cache", False)
      self.config.set("performance", "cache_song_metadata", False)
      Log.debug("Quickset Performance - Fastest")
      
    elif perfSetNum == 2:
      self.config.set("performance", "game_priority", 2)
      self.config.set("performance", "starspin", False)
      self.config.set("game", "rb_midi_lyrics", 1)
      self.config.set("game", "rb_midi_sections", 1)
      self.config.set("game", "gsolo_acc_disp", 1)
      self.config.set("game", "incoming_neck_mode", 1)
      self.config.set("game", "midi_lyric_mode", 2)
      self.config.set("video", "multisamples", 2)
      self.config.set("coffee", "game_phrases", 1)
      self.config.set("game", "partial_stars", 1)
      self.config.set("game", "songlistrotation", False)
      self.config.set("game", "song_listing_mode", 0)
      self.config.set("game", "stage_animate", 0)
      self.config.set("game", "lyric_mode", 2)
      self.config.set("audio", "enable_crowd_tracks", 1)
      self.config.set("performance", "in_game_stats", 0)
      self.config.set("performance", "static_strings", True)
      self.config.set("performance", "killfx", 0)
      self.config.set("performance", "star_score_updates", 0)
      self.config.set("performance", "preload_glyph_cache", True)
      self.config.set("performance", "cache_song_metadata", True)
      Log.debug("Quickset Performance - Fast")
      
    elif perfSetNum == 3:
      self.config.set("performance", "game_priority", 2)
      self.config.set("performance", "starspin", True)
      self.config.set("game", "rb_midi_lyrics", 2)
      self.config.set("game", "rb_midi_sections", 2)
      self.config.set("game", "gsolo_acc_disp", 1)
      self.config.set("game", "incoming_neck_mode", 2)
      self.config.set("game", "midi_lyric_mode", 2)
      self.config.set("video", "multisamples", 4)
      self.config.set("coffee", "game_phrases", 2)
      self.config.set("game", "partial_stars", 1)
      self.config.set("game", "songlistrotation", True)
      self.config.set("game", "lyric_mode", 2)
      self.config.set("audio", "enable_crowd_tracks", 1)
      self.config.set("performance", "in_game_stats", 2)
      self.config.set("performance", "static_strings", True)
      self.config.set("performance", "killfx", 0)
      self.config.set("performance", "star_score_updates", 1)
      self.config.set("performance", "preload_glyph_cache", True)
      self.config.set("performance", "cache_song_metadata", True)
      Log.debug("Quickset Performance - Quality")
      
    elif perfSetNum == 4:
      self.config.set("performance", "game_priority", 2)
      self.config.set("performance", "starspin", True)
      self.config.set("game", "rb_midi_lyrics", 2)
      self.config.set("game", "rb_midi_sections", 2)
      self.config.set("game", "gsolo_acc_disp", 2)
      self.config.set("game", "incoming_neck_mode", 2)
      self.config.set("game", "midi_lyric_mode", 0)
      self.config.set("video", "multisamples", 4)
      self.config.set("coffee", "game_phrases", 2)
      self.config.set("game", "partial_stars", 1)
      self.config.set("game", "songlistrotation", True)
      self.config.set("game", "lyric_mode", 2)
      self.config.set("audio", "enable_crowd_tracks", 1)
      self.config.set("performance", "in_game_stats", 2)
      self.config.set("performance", "static_strings", False)
      self.config.set("performance", "killfx", 0)
      self.config.set("performance", "star_score_updates", 1)
      self.config.set("performance", "preload_glyph_cache", True)
      self.config.set("performance", "cache_song_metadata", True)
      Log.debug("Quickset Performance - Highest Quality")
      
    else:
      Log.debug("Quickset Performance - Manual")
  
  def applySettings(self):
    self.quickset()
    if self.engine.restartRequired or self.engine.quicksetRestart:
      Dialogs.showMessage(self.engine, _("FoFiX needs to restart to apply setting changes."))
      for option in self.settingsToApply:
        if isinstance(option, ConfigChoice):
          option.apply()
      self.engine.restart()
    
  def advancedSettings(self):
    Config.set("game", "adv_settings", False)
    self.engine.advSettings = False
    if not self.engine.restartRequired:
      self.engine.view.popLayer(self)
      self.engine.input.removeKeyListener(self)
    else:
      self.applySettings()

  def resetLanguageToEnglish(self):
    Log.debug("settings.resetLanguageToEnglish function call...")
    if self.engine.config.get("game", "language") != "":
      self.engine.config.set("game", "language", "")
      self.engine.restart()


  #def listAllFolderSelect(self):
  #  Log.debug("settings.baseLibrarySelect function call...")
  #  newPath = Dialogs.chooseFile(self.engine, masks = ["*/*"], prompt = _("Choose a New List All directory."), dirSelect = True)
  #  if newPath != None:
  #    Config.set("game", "listall_folder", os.path.dirname(newPath))
  #    Log.debug(newPath)
  #    Log.debug(os.path.dirname(newPath))
  #    self.engine.resource.refreshBaseLib()   #myfingershurt - to let user continue with new songpath without restart
      
  def baseLibrarySelect(self):
    Log.debug("settings.baseLibrarySelect function call...")
    newPath = Dialogs.chooseFile(self.engine, masks = ["*/songs"], prompt = _("Choose a new songs directory."), dirSelect = True)
    if newPath != None:
      Config.set("game", "base_library", os.path.dirname(newPath))
      Config.set("game", "selected_library", "songs")
      Config.set("game", "selected_song", "")
      self.engine.resource.refreshBaseLib()   #myfingershurt - to let user continue with new songpath without restart
    

class BasicSettingsMenu(Menu.Menu):
  def __init__(self, engine):

    self.engine = engine

    self.logClassInits = self.engine.config.get("game", "log_class_inits")
    if self.logClassInits == 1:
      Log.debug("BasicSettingsMenu class init (Settings.py)...")
      
    modSettings = [
      ConfigChoice(engine, engine.config, "mods",  "mod_" + m) for m in Mod.getAvailableMods(engine)
    ]
    
    FoFiXBasicSettings = [
      ConfigChoice(engine, engine.config, "game",  "language"),
      ConfigChoice(engine, engine.config, "game", "T_sound", autoApply = True), #Faaa Drum sound
      ConfigChoice(engine, engine.config, "game", "star_scoring", autoApply = True),#myfingershurt
      ConfigChoice(engine, engine.config, "game", "resume_countdown", autoApply = True), #akedrou
      ConfigChoice(engine, engine.config, "game", "whammy_saves_starpower", autoApply = True),#myfingershurt
      ConfigChoice(engine, engine.config, "game", "sp_notes_while_active", autoApply = True, isQuickset = 2),   #myfingershurt - setting for gaining more SP while active
      ConfigChoice(engine, engine.config, "game", "drum_sp_mode", autoApply = True),#myfingershurt
      ConfigChoice(engine, engine.config, "game",  "uploadscores", autoApply = True),
      ConfigChoice(engine, engine.config, "audio",  "delay", autoApply = True),     #myfingershurt: so a/v delay can be set without restarting FoF
    ]
    FoFiXBasicSettingsMenu = Menu.Menu(engine, FoFiXBasicSettings)
    
    drumKeySettings = [
      KeyConfigChoice(engine, engine.config, "player0", "key_bass"),
      KeyConfigChoice(engine, engine.config, "player0", "key_drum1a"),
      KeyConfigChoice(engine, engine.config, "player0", "key_drum1b"),
      KeyConfigChoice(engine, engine.config, "player0", "key_drum2a"),
      KeyConfigChoice(engine, engine.config, "player0", "key_drum2b"),
      KeyConfigChoice(engine, engine.config, "player0", "key_drum3a"),
      KeyConfigChoice(engine, engine.config, "player0", "key_drum3b"),
      KeyConfigChoice(engine, engine.config, "player0", "key_drum4a"),
      KeyConfigChoice(engine, engine.config, "player0", "key_drum4b"),
      KeyConfigChoice(engine, engine.config, "player0", "key_drum_up"), #shun - directionals
      KeyConfigChoice(engine, engine.config, "player0", "key_drum_down"),
      KeyConfigChoice(engine, engine.config, "player0", "key_drum_left"),
      KeyConfigChoice(engine, engine.config, "player0", "key_drum_right"),
      KeyConfigChoice(engine, engine.config, "player0", "key_drum_cancel"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_bass"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_drum1a"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_drum1b"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_drum2a"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_drum2b"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_drum3a"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_drum3b"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_drum4a"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_drum4b"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_drum_up"), #shun - directionals
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_drum_down"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_drum_left"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_drum_right"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_drum_cancel"),

    ]       
    drumKeySettingsMenu = Menu.Menu(engine, drumKeySettings)

#shun - alternate drum keys
    altDrumKeySettings = [
      KeyConfigChoice(engine, engine.config, "player0", "akey_bass"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_drum1a"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_drum1b"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_drum2a"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_drum2b"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_drum3a"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_drum3b"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_drum4a"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_drum4b"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_drum_up"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_drum_down"), #shun - directionals
      KeyConfigChoice(engine, engine.config, "player0", "akey_drum_left"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_drum_right"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_drum_cancel"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_bass"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_drum1a"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_drum1b"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_drum2a"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_drum2b"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_drum3a"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_drum3b"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_drum4a"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_drum4b"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_drum_up"), # shun -directionals
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_drum_down"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_drum_left"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_drum_right"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_drum_cancel"),
    ]       
    altDrumKeySettingsMenu = Menu.Menu(engine, altDrumKeySettings)

    player0Keys = [
      KeyConfigChoice(engine, engine.config, "player0", "key_action1"),
      KeyConfigChoice(engine, engine.config, "player0", "key_action2"),
      KeyConfigChoice(engine, engine.config, "player0", "key_1"),
      KeyConfigChoice(engine, engine.config, "player0", "key_2"),
      KeyConfigChoice(engine, engine.config, "player0", "key_3"),
      KeyConfigChoice(engine, engine.config, "player0", "key_4"),
      KeyConfigChoice(engine, engine.config, "player0", "key_5"),
      KeyConfigChoice(engine, engine.config, "player0", "key_left"),
      KeyConfigChoice(engine, engine.config, "player0", "key_right"),
      KeyConfigChoice(engine, engine.config, "player0", "key_up"),
      KeyConfigChoice(engine, engine.config, "player0", "key_down"),
      KeyConfigChoice(engine, engine.config, "player0", "key_cancel"),
      KeyConfigChoice(engine, engine.config, "player0", "key_star"),
      KeyConfigChoice(engine, engine.config, "player0", "key_kill"),
    ]
    player0KeyMenu = Menu.Menu(engine, player0Keys)

    player0AltKeys = [
      KeyConfigChoice(engine, engine.config, "player0", "akey_action1"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_action2"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_1"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_2"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_3"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_4"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_5"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_left"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_right"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_up"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_down"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_cancel"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_star"),
      KeyConfigChoice(engine, engine.config, "player0", "akey_kill"),
    ]
    player0AltKeyMenu = Menu.Menu(engine, player0AltKeys)

    player1Keys = [
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_action1"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_action2"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_1"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_2"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_3"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_4"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_5"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_left"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_right"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_up"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_down"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_cancel"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_star"),#added by ShiekOdaSandz
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_kill"),#added by ShiekOdaSandz
    ]
    player1KeyMenu = Menu.Menu(engine, player1Keys)

    player1AltKeys = [
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_action1"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_action2"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_1"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_2"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_3"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_4"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_5"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_left"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_right"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_up"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_down"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_cancel"),
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_star"),#added by ShiekOdaSandz
      KeyConfigChoice(engine, engine.config, "player1", "aplayer_2_key_kill"),#added by ShiekOdaSandz
    ]
    player1AltKeyMenu = Menu.Menu(engine, player1AltKeys)
    
    KeyChangeSettings = [
      ConfigChoice(engine, engine.config, "game", "key_checker_mode", autoApply = True),#myfingershurt
      (_("Player 1 Keys"), player0KeyMenu),
      (_("Player 1 Alt. Keys"), player0AltKeyMenu),
      (_("Player 2 Keys"), player1KeyMenu),
      (_("Player 2 Alt. Keys"), player1AltKeyMenu),
      (_("Drum Keys" ), drumKeySettingsMenu),
      (_("Alt. Drum Keys" ), altDrumKeySettingsMenu),
    ]
    KeyChangeMenu = Menu.Menu(engine, KeyChangeSettings)

    keySettings = [
      ConfigChoice(engine, engine.config, "game", "alt_keys", autoApply = True),
      (_("Change Controls"), KeyChangeMenu),
      (_("Test Guitars"), lambda: Dialogs.testKeys(engine)),
      (_("Test Drums"), lambda: Dialogs.testDrums(engine)),
      ConfigChoice(engine, engine.config, "game", "p2_menu_nav", autoApply = True),#myfingershurt
      ConfigChoice(engine, engine.config, "game", "drum_navigation", autoApply = True),#myfingershurt
      ConfigChoice(engine, engine.config, "game", "analog_killsw_mode", autoApply = True),#myfingershurt
      ConfigChoice(engine, engine.config, "game", "analog_killsw_mode_p2", autoApply = True),#myfingershurt
      ConfigChoice(engine, engine.config, "player0",  "leftymode", autoApply = True),
      ConfigChoice(engine, engine.config, "player1",  "leftymode", autoApply = True), #QQstarS
      ConfigChoice(engine, engine.config, "player0",  "two_chord_max", autoApply = True),
      ConfigChoice(engine, engine.config, "player1",  "two_chord_max", autoApply = True), #QQstarS
    ]
    keySettingsMenu = Menu.Menu(engine, keySettings)
    
    InGameDisplaySettings = [
      ConfigChoice(engine, engine.config, "game", "in_game_stars", autoApply = True, isQuickset = 2),#myfingershurt
      ConfigChoice(engine, engine.config, "game", "accuracy_mode", autoApply = True),
      ConfigChoice(engine, engine.config, "performance", "in_game_stats", autoApply = True, isQuickset = 1),#myfingershurt
      ConfigChoice(engine, engine.config, "game", "game_time", autoApply = True),  
      ConfigChoice(engine, engine.config, "video", "counting", autoApply = True, isQuickset = 2),
    ]
    InGameDisplayMenu = Menu.Menu(engine, InGameDisplaySettings)
      
    modes = engine.video.getVideoModes()
    modes.reverse()
    Config.define("video",  "resolution", str,   "1024x768", text = _("Video Resolution"), options = ["%dx%d" % (m[0], m[1]) for m in modes])
    videoSettings = [
      ConfigChoice(engine, engine.config, "coffee", "themename"),
      ConfigChoice(engine, engine.config, "video",  "resolution"),
      ConfigChoice(engine, engine.config, "video",  "fullscreen"),
      ConfigChoice(engine, engine.config, "game", "stage_mode", autoApply = True),   #myfingershurt
      (_("Choose P1 Neck >"), lambda: Dialogs.chooseNeck(engine,player=0,prompt=_("Yellow (#3) / Blue (#4) to change:"))),
      (_("Choose P2 Neck >"), lambda: Dialogs.chooseNeck(engine,player=1,prompt=_("Yellow (#3) / Blue (#4) to change:"))),
      (_("In-Game Display Settings"), InGameDisplayMenu),
    ]
    videoSettingsMenu = Menu.Menu(engine, videoSettings)

    
    volumeSettings = [
      VolumeConfigChoice(engine, engine.config, "audio",  "guitarvol", autoApply = True),
      VolumeConfigChoice(engine, engine.config, "audio",  "songvol", autoApply = True),
      VolumeConfigChoice(engine, engine.config, "audio",  "rhythmvol", autoApply = True),
      VolumeConfigChoice(engine, engine.config, "audio",  "screwupvol", autoApply = True),
      VolumeConfigChoice(engine, engine.config, "audio",  "miss_volume", autoApply = True),
      VolumeConfigChoice(engine, engine.config, "audio",  "single_track_miss_volume", autoApply = True),
      VolumeConfigChoice(engine, engine.config, "audio",  "crowd_volume", autoApply = True), #akedrou
      VolumeConfigChoice(engine, engine.config, "audio",  "kill_volume", autoApply = True), #MFH
      VolumeConfigChoice(engine, engine.config, "audio",  "SFX_volume", autoApply = True), #MFH
    ]
    volumeSettingsMenu = Menu.Menu(engine, volumeSettings)

    audioSettings = [
      (_("Volume Settings"),    volumeSettingsMenu),
      ConfigChoice(engine, engine.config, "game", "star_claps", autoApply = True),      #myfingershurt
      ConfigChoice(engine, engine.config, "game", "beat_claps", autoApply = True), #racer
      ConfigChoice(engine, engine.config, "audio",  "whammy_effect", autoApply = True),     #MFH
      ConfigChoice(engine, engine.config, "audio", "enable_crowd_tracks", autoApply = True), #akedrou
    ]
    audioSettingsMenu = Menu.Menu(engine, audioSettings)
    
    quickSettings = [
      ConfigChoice(engine, engine.config, "quickset", "performance", autoApply = True),
      ConfigChoice(engine, engine.config, "quickset", "gameplay", autoApply = True),
    ]
    quicksetMenu = Menu.Menu(engine, quickSettings)

    listSettings = [
      (_("Change Setlist Path >"), self.baseLibrarySelect),
      ConfigChoice(engine, engine.config, "coffee", "song_display_mode", autoApply = True),
      ConfigChoice(engine, engine.config, "game",  "sort_order", autoApply = True),
      ConfigChoice(engine, engine.config, "game", "sort_direction", autoApply = True),
      ConfigChoice(engine, engine.config, "game", "song_listing_mode", autoApply = True, isQuickset = 2),
      ConfigChoice(engine, engine.config, "game", "quickplay_tiers", autoApply = True),  #myfingershurt
      ConfigChoice(engine, engine.config, "game", "songcovertype", autoApply = True),
      ConfigChoice(engine, engine.config, "game", "song_icons", autoApply = True),
      ConfigChoice(engine, engine.config, "game", "songlist_instrument", autoApply = True), #MFH
      ConfigChoice(engine, engine.config, "game", "songlist_difficulty", autoApply = True), #evilynux
    ]
    listSettingsMenu = Menu.Menu(engine, listSettings)

    Cheats = [
      ConfigChoice(engine, engine.config, "game", "jurgmode", autoApply = True),
      ConfigChoice(engine, engine.config, "game", "jurgtype", autoApply = True),
      ConfigChoice(engine, engine.config, "game", "gh2_sloppy", autoApply = True),
      ConfigChoice(engine, engine.config, "game", "hit_window_cheat", autoApply = True),
      ConfigChoice(engine, engine.config, "coffee", "hopo_freq_cheat", autoApply = True),
      ConfigChoice(engine, engine.config, "coffee", "failingEnabled", autoApply = True),
      ConfigChoice(engine, engine.config, "audio",  "slow_down_divisor", autoApply = True),     #MFH
      (_("Mod settings"), modSettings),
    ]
    CheatMenu = Menu.Menu(engine, Cheats)
    
    settings = [
      (_("Gameplay Settings"),   FoFiXBasicSettingsMenu),
      (_("Control Settings"),          keySettingsMenu),
      (_("Display Settings"),     videoSettingsMenu),
      (_("Audio Settings"),      audioSettingsMenu),
      (_("Setlist Settings"),   listSettingsMenu),
      (_("Mods, Cheats, AI"), CheatMenu),
      (_("%s Credits") % (engine.versionString), lambda: Dialogs.showCredits(engine)), # evilynux - Show Credits!
      (_("Quickset"), quicksetMenu),
      (_("See Advanced Options"), self.advancedSettings)
    ]
  
    self.settingsToApply = FoFiXBasicSettings + \
                           videoSettings + \
                           modSettings
  
    self.opt_text_x = Theme.opt_text_xPos
    self.opt_text_y = Theme.opt_text_yPos

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


    self.opt_text_color = Theme.hexToColor(Theme.opt_text_colorVar)
    self.opt_selected_color = Theme.hexToColor(Theme.opt_selected_colorVar)

    Log.debug("Option text / selected hex colors: " + Theme.opt_text_colorVar + " / " + Theme.opt_selected_colorVar)


    if self.opt_text_color == None:
      self.opt_text_color = (1,1,1)
    if self.opt_selected_color == None:
      self.opt_selected_color = (1,0.75,0)

    Log.debug("Option text / selected colors: " + str(self.opt_text_color) + " / " + str(self.opt_selected_color))



    Menu.Menu.__init__(self, engine, settings, onCancel = self.applySettings, pos = (self.opt_text_x, self.opt_text_y), textColor = self.opt_text_color, selectedColor = self.opt_selected_color)   #MFH - add position to this so we can move it

  def quickset(self):
    #akedrou - quickset (based on Fablaculp's Performance Autoset)
    self.config = self.engine.config
    perfSetNum = self.config.get("quickset","performance")
    gameSetNum = self.config.get("quickset","gameplay")
    
    if gameSetNum == 1:
      self.config.set("game", "sp_notes_while_active", 1)
      self.config.set("game", "bass_groove_enable", 1)
      self.config.set("game", "big_rock_endings", 1)
      self.config.set("game", "in_game_stars", 1)
      self.config.set("coffee", "song_display_mode", 4)
      Log.debug("Quickset Gameplay - Theme-Based")
      
    elif gameSetNum == 2:
      self.config.set("game", "sp_notes_while_active", 2)
      self.config.set("game", "bass_groove_enable", 2)
      self.config.set("game", "big_rock_endings", 2)
      Log.debug("Quickset Gameplay - MIDI-Based")
      
    elif gameSetNum == 3:
      self.config.set("game", "sp_notes_while_active", 3)
      self.config.set("game", "bass_groove_enable", 3)
      self.config.set("game", "big_rock_endings", 2)
      self.config.set("game", "in_game_stars", 2)
      self.config.set("game", "counting", True)
      Log.debug("Quickset Gameplay - RB style")
      
    elif gameSetNum == 4:
      self.config.set("game", "sp_notes_while_active", 0)
      self.config.set("game", "bass_groove_enable", 0)
      self.config.set("game", "big_rock_endings", 0)
      self.config.set("game", "in_game_stars", 0)
      self.config.set("coffee", "song_display_mode", 1)
      self.config.set("game", "counting", False)
      Log.debug("Quickset Gameplay - GH style")
      
    elif gameSetNum == 5: # This needs work.
      self.config.set("game", "sp_notes_while_active", 0)
      self.config.set("game", "bass_groove_enable", 0)
      self.config.set("game", "big_rock_endings", 0)
      self.config.set("game", "in_game_stars", 0)
      self.config.set("coffee", "song_display_mode", 1)
      self.config.set("game", "counting", True)
      Log.debug("Quickset Gameplay - WT style")
      
    # elif gameSetNum == 6: #FoFiX mode - perhaps soon.
      
    else:
      Log.debug("Quickset Gameplay - Manual")
    
    if perfSetNum == 1:
      self.config.set("performance", "game_priority", 2)
      self.config.set("performance", "starspin", False)
      self.config.set("game", "rb_midi_lyrics", 0)
      self.config.set("game", "rb_midi_sections", 0)
      self.config.set("game", "gsolo_acc_disp", 0)
      self.config.set("game", "incoming_neck_mode", 0)
      self.config.set("game", "midi_lyric_mode", 2)
      self.config.set("video", "multisamples", 0)
      self.config.set("coffee", "game_phrases", 0)
      self.config.set("game", "partial_stars", 0)
      self.config.set("game", "songlistrotation", False)
      self.config.set("game", "song_listing_mode", 0)
      self.config.set("game", "song_display_mode", 1)
      self.config.set("game", "stage_animate", 0)
      self.config.set("game", "lyric_mode", 0)
      self.config.set("audio", "enable_crowd_tracks", 0)
      self.config.set("performance", "in_game_stats", 0)
      self.config.set("performance", "static_strings", True)
      self.config.set("performance", "killfx", 2)
      self.config.set("performance", "star_score_updates", 0)
      self.config.set("performance", "preload_glyph_cache", False)
      self.config.set("performance", "cache_song_metadata", False)
      Log.debug("Quickset Performance - Fastest")
      
    elif perfSetNum == 2:
      self.config.set("performance", "game_priority", 2)
      self.config.set("performance", "starspin", False)
      self.config.set("game", "rb_midi_lyrics", 1)
      self.config.set("game", "rb_midi_sections", 1)
      self.config.set("game", "gsolo_acc_disp", 1)
      self.config.set("game", "incoming_neck_mode", 1)
      self.config.set("game", "midi_lyric_mode", 2)
      self.config.set("video", "multisamples", 2)
      self.config.set("coffee", "game_phrases", 1)
      self.config.set("game", "partial_stars", 1)
      self.config.set("game", "songlistrotation", False)
      self.config.set("game", "song_listing_mode", 0)
      self.config.set("game", "stage_animate", 0)
      self.config.set("game", "lyric_mode", 2)
      self.config.set("audio", "enable_crowd_tracks", 1)
      self.config.set("performance", "in_game_stats", 0)
      self.config.set("performance", "static_strings", True)
      self.config.set("performance", "killfx", 0)
      self.config.set("performance", "star_score_updates", 0)
      self.config.set("performance", "preload_glyph_cache", True)
      self.config.set("performance", "cache_song_metadata", True)
      Log.debug("Quickset Performance - Fast")
      
    elif perfSetNum == 3:
      self.config.set("performance", "game_priority", 2)
      self.config.set("performance", "starspin", True)
      self.config.set("game", "rb_midi_lyrics", 2)
      self.config.set("game", "rb_midi_sections", 2)
      self.config.set("game", "gsolo_acc_disp", 1)
      self.config.set("game", "incoming_neck_mode", 2)
      self.config.set("game", "midi_lyric_mode", 2)
      self.config.set("video", "multisamples", 4)
      self.config.set("coffee", "game_phrases", 2)
      self.config.set("game", "partial_stars", 1)
      self.config.set("game", "songlistrotation", True)
      self.config.set("game", "lyric_mode", 2)
      self.config.set("audio", "enable_crowd_tracks", 1)
      self.config.set("performance", "in_game_stats", 2)
      self.config.set("performance", "static_strings", True)
      self.config.set("performance", "killfx", 0)
      self.config.set("performance", "star_score_updates", 1)
      self.config.set("performance", "preload_glyph_cache", True)
      self.config.set("performance", "cache_song_metadata", True)
      Log.debug("Quickset Performance - Quality")
      
    elif perfSetNum == 4:
      self.config.set("performance", "game_priority", 2)
      self.config.set("performance", "starspin", True)
      self.config.set("game", "rb_midi_lyrics", 2)
      self.config.set("game", "rb_midi_sections", 2)
      self.config.set("game", "gsolo_acc_disp", 2)
      self.config.set("game", "incoming_neck_mode", 2)
      self.config.set("game", "midi_lyric_mode", 0)
      self.config.set("video", "multisamples", 4)
      self.config.set("coffee", "game_phrases", 2)
      self.config.set("game", "partial_stars", 1)
      self.config.set("game", "songlistrotation", True)
      self.config.set("game", "lyric_mode", 2)
      self.config.set("audio", "enable_crowd_tracks", 1)
      self.config.set("performance", "in_game_stats", 2)
      self.config.set("performance", "static_strings", False)
      self.config.set("performance", "killfx", 0)
      self.config.set("performance", "star_score_updates", 1)
      self.config.set("performance", "preload_glyph_cache", True)
      self.config.set("performance", "cache_song_metadata", True)
      Log.debug("Quickset Performance - Highest Quality")
      
    else:
      Log.debug("Quickset Performance - Manual")
    
  def applySettings(self):
    self.quickset()
    if self.engine.restartRequired or self.engine.quicksetRestart:
      Dialogs.showMessage(self.engine, _("FoFiX needs to restart to apply setting changes."))
      for option in self.settingsToApply:
        if isinstance(option, ConfigChoice):
          option.apply()
      self.engine.restart()
    
  def advancedSettings(self):
    Config.set("game", "adv_settings", True)
    self.engine.advSettings = True
    if not self.engine.restartRequired:
      self.engine.view.popLayer(self)
      self.engine.input.removeKeyListener(self)
    else:
      self.applySettings()

  def resetLanguageToEnglish(self):
    Log.debug("settings.resetLanguageToEnglish function call...")
    if self.engine.config.get("game", "language") != "":
      self.engine.config.set("game", "language", "")
      self.engine.restart()

  def baseLibrarySelect(self):
    Log.debug("settings.baseLibrarySelect function call...")
    newPath = Dialogs.chooseFile(self.engine, masks = ["*/songs"], prompt = _("Choose a new songs directory."), dirSelect = True)
    if newPath != None:
      Config.set("game", "base_library", os.path.dirname(newPath))
      Config.set("game", "selected_library", "songs")
      Config.set("game", "selected_song", "")
      self.engine.resource.refreshBaseLib()   #myfingershurt - to let user continue with new songpath without restart

class GameSettingsMenu(Menu.Menu):
  def __init__(self, engine, gTextColor, gSelectedColor):

    self.logClassInits = Config.get("game", "log_class_inits")
    if self.logClassInits == 1:
      Log.debug("GameSettingsMenu class init (Settings.py)...")
    
    Cheats = [
      ConfigChoice(engine, engine.config, "game", "jurgmode", autoApply = True),#Jurgen config -- Spikehead777
      ConfigChoice(engine, engine.config, "game", "jurgtype", autoApply = True),#Jurgen controls -- Spikehead777
      ConfigChoice(engine, engine.config, "game", "jurglogic", autoApply = True),#MFH
     #MFH
    ]
    CheatMenu = Menu.Menu(engine, Cheats, pos = (.350, .310), viewSize = 5, textColor = gTextColor, selectedColor = gSelectedColor)
    
    settings = [
      (_("Cheats"), CheatMenu),
      VolumeConfigChoice(engine, engine.config, "audio",  "guitarvol", autoApply = True),
      VolumeConfigChoice(engine, engine.config, "audio",  "songvol", autoApply = True),
      VolumeConfigChoice(engine, engine.config, "audio",  "rhythmvol", autoApply = True),
      VolumeConfigChoice(engine, engine.config, "audio",  "screwupvol", autoApply = True),
      VolumeConfigChoice(engine, engine.config, "audio",  "miss_volume", autoApply = True),
      VolumeConfigChoice(engine, engine.config, "audio",  "single_track_miss_volume", autoApply = True),
      VolumeConfigChoice(engine, engine.config, "audio",  "crowd_volume", autoApply = True),
      VolumeConfigChoice(engine, engine.config, "audio",  "kill_volume", autoApply = True), #MFH
      VolumeConfigChoice(engine, engine.config, "audio",  "SFX_volume", autoApply = True), #MFH
      ConfigChoice(engine, engine.config, "audio", "enable_crowd_tracks", autoApply = True), #akedrou
      ConfigChoice(engine, engine.config, "audio",  "delay", autoApply = True),   #myfingershurt: so the a/v delay can be adjusted in-game
      ConfigChoice(engine, engine.config, "game", "stage_rotate_delay", autoApply = True),   #myfingershurt - user defined stage rotate delay
      ConfigChoice(engine, engine.config, "game", "stage_animate_delay", autoApply = True),   #myfingershurt - user defined stage rotate delay
      ConfigChoice(engine, engine.config, "player0",  "leftymode", autoApply = True),
      ConfigChoice(engine, engine.config, "player1",  "leftymode", autoApply = True), #QQstarS
    ]
    Menu.Menu.__init__(self, engine, settings, pos = (.360, .250), viewSize = 5, textColor = gTextColor, selectedColor = gSelectedColor) #Worldrave- Changed Pause-Submenu Position more centered until i add a theme.ini setting.

