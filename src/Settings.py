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
  def __init__(self, config, section, option, autoApply = False):
    self.config    = config
    
    self.logClassInits = Config.get("game", "log_class_inits")
    if self.logClassInits == 1:
      Log.debug("ConfigChoice class init (Settings.py)...")
    
    self.section   = section
    self.option    = option
    self.changed   = False
    self.value     = None
    self.autoApply = autoApply
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
    
    if self.autoApply:
      self.apply()

  def apply(self):
    if self.changed:
      self.config.set(self.section, self.option, self.value)

class VolumeConfigChoice(ConfigChoice):
  def __init__(self, engine, config, section, option, autoApply = False):
    ConfigChoice.__init__(self, config, section, option, autoApply)
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

    
    applyItem = [(_("Apply New Settings"), self.applySettings)]

    modSettings = [
      ConfigChoice(engine.config, "mods",  "mod_" + m) for m in Mod.getAvailableMods(engine)
    ] + applyItem
    
    StagesOptions = [
      ConfigChoice(engine.config, "game", "stage_mode", autoApply = True),   #myfingershurt
      ConfigChoice(engine.config, "game", "animated_stage_folder", autoApply = True),   #myfingershurt
      ConfigChoice(engine.config, "game", "song_stage", autoApply = True),   #myfingershurt
      ConfigChoice(engine.config, "game", "rotate_stages", autoApply = True),   #myfingershurt
      ConfigChoice(engine.config, "game", "stage_rotate_delay", autoApply = True),   #myfingershurt - user defined stage rotate delay
      ConfigChoice(engine.config, "game", "stage_animate", autoApply = True),   #myfingershurt - user defined stage rotate delay
      ConfigChoice(engine.config, "game", "stage_animate_delay", autoApply = True),   #myfingershurt - user defined stage rotate delay
    ]
    StagesOptionsMenu = Menu.Menu(engine, StagesOptions)
    
    HOPOSettings = [
       ConfigChoice(engine.config, "game", "hopo_indicator", autoApply = True),      #myfingershurt
       ConfigChoice(engine.config, "game", "hopo_style", autoApply = True),      #myfingershurt
       ConfigChoice(engine.config, "coffee", "moreHopo", autoApply = True),
       ConfigChoice(engine.config, "game", "song_hopo_freq", autoApply = True),      #myfingershurt
       ConfigChoice(engine.config, "game", "hopo_after_chord", autoApply = True),      #myfingershurt
    ]
    HOPOSettingsMenu = Menu.Menu(engine, HOPOSettings)
    
    LyricsSettings = [
       ConfigChoice(engine.config, "game", "lyric_mode", autoApply = True),      #myfingershurt
       ConfigChoice(engine.config, "game", "script_lyric_pos", autoApply = True),      #myfingershurt
    ]
    LyricsSettingsMenu = Menu.Menu(engine, LyricsSettings)
    
    JurgenSettings = [
       ConfigChoice(engine.config, "game", "jurgdef", autoApply = True),#Spikehead777
       ConfigChoice(engine.config, "game", "jurgtype", autoApply = True),#Spikehead777
       ConfigChoice(engine.config, "game", "jurglogic", autoApply = True),#MFH
       ConfigChoice(engine.config, "game", "jurgtext", autoApply = True),#hman
    ]
    JurgenSettingsMenu = Menu.Menu(engine, JurgenSettings)
           
    FoFiXBasicSettings = [
      ConfigChoice(engine.config, "game",  "language"),
      ConfigChoice(engine.config, "coffee", "themename",    autoApply = True),
      (_("Stages Options"), StagesOptionsMenu),
      (_("HO/PO Settings"), HOPOSettingsMenu),
      (_("Lyrics Settings"), LyricsSettingsMenu),
      (_("Jurgen Settings"), JurgenSettingsMenu),
      (_("Choose P1 Neck >"), lambda: Dialogs.chooseNeck(engine,player=0,prompt=_("Yellow (#3) / Blue (#4) to change:"))),
      (_("Choose P2 Neck >"), lambda: Dialogs.chooseNeck(engine,player=1,prompt=_("Yellow (#3) / Blue (#4) to change:"))),
      ConfigChoice(engine.config, "game", "ignore_open_strums", autoApply = True),      #myfingershurt
      ConfigChoice(engine.config, "game", "star_scoring", autoApply = True),#myfingershurt
      ConfigChoice(engine.config, "coffee", "failingEnabled", autoApply = True),
      ConfigChoice(engine.config, "game",  "uploadscores", autoApply = True),
    ]
    FoFiXBasicSettingsMenu = Menu.Menu(engine, FoFiXBasicSettings)
    
    FoFiXAdvancedSettings = [
       ConfigChoice(engine.config, "game", "party_time", autoApply = True),
       ConfigChoice(engine.config, "game", "rb_midi_lyrics", autoApply = True),      #myfingershurt
       ConfigChoice(engine.config, "game", "rb_midi_sections", autoApply = True),      #myfingershurt
       ConfigChoice(engine.config, "game", "bass_groove_enable", autoApply = True),#myfingershurt
       ConfigChoice(engine.config, "game", "lphrases", autoApply = True),#blazingamer
       ConfigChoice(engine.config, "game", "whammy_saves_starpower", autoApply = True),#myfingershurt
       ConfigChoice(engine.config, "game", "starpower_mode", autoApply = True),#myfingershurt
    ]
    FoFiXAdvancedSettingsMenu = Menu.Menu(engine, FoFiXAdvancedSettings)
    
    drumKeySettings = [
      (_("Test Keys"), lambda: Dialogs.testDrums(engine)),
      ConfigChoice(engine.config, "game", "auto_drum_sp", autoApply = True),#myfingershurt
      KeyConfigChoice(engine, engine.config, "player0", "key_bass"),
      KeyConfigChoice(engine, engine.config, "player0", "key_drum1a"),
      KeyConfigChoice(engine, engine.config, "player0", "key_drum1b"),
      KeyConfigChoice(engine, engine.config, "player0", "key_drum2a"),
      KeyConfigChoice(engine, engine.config, "player0", "key_drum2b"),
      KeyConfigChoice(engine, engine.config, "player0", "key_drum3a"),
      KeyConfigChoice(engine, engine.config, "player0", "key_drum3b"),
      KeyConfigChoice(engine, engine.config, "player0", "key_drum4a"),
      KeyConfigChoice(engine, engine.config, "player0", "key_drum4b"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_bass"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_drum1a"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_drum1b"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_drum2a"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_drum2b"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_drum3a"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_drum3b"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_drum4a"),
      KeyConfigChoice(engine, engine.config, "player1", "player_2_key_drum4b"),
    ]       
    drumKeySettingsMenu = Menu.Menu(engine, drumKeySettings)


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
    
    AdvancedKeySettings = [
       ConfigChoice(engine.config, "game", "analog_killsw_mode", autoApply = True),#myfingershurt
       ConfigChoice(engine.config, "player0",  "two_chord_max", autoApply = True),
       ConfigChoice(engine.config, "player0",  "leftymode", autoApply = True),
       ConfigChoice(engine.config, "game", "analog_killsw_mode_p2", autoApply = True),#myfingershurt
       ConfigChoice(engine.config, "player1",  "two_chord_max", autoApply = True), #QQstarS
       ConfigChoice(engine.config, "player1",  "leftymode", autoApply = True), #QQstarS
       ConfigChoice(engine.config, "game", "drum_navigation", autoApply = True),#myfingershurt
       ConfigChoice(engine.config, "game", "p2_menu_nav", autoApply = True),#myfingershurt
   ]
    AdvancedKeySettingsMenu = Menu.Menu(engine, AdvancedKeySettings)

    keySettings = [
      ConfigChoice(engine.config, "game", "key_checker_mode", autoApply = True),#myfingershurt
      ConfigChoice(engine.config, "game", "alt_keys", autoApply = True),
      (_("Player 1 Keys"), player0KeyMenu),
      (_("Player 1 Alt. Keys"), player0AltKeyMenu),
      (_("Player 2 Keys"), player1KeyMenu),
      (_("Player 2 Alt. Keys"), player1AltKeyMenu),
      (_("Drum keys" ), drumKeySettingsMenu),
      (_("Test Keys"), lambda: Dialogs.testKeys(engine)),
      (_("Advanced controls"), AdvancedKeySettingsMenu),
    ]
    keySettingsMenu = Menu.Menu(engine, keySettings)
    
    AdvancedVideoSettings = [
       ConfigChoice(engine.config, "video",  "fps"),
       ConfigChoice(engine.config, "game", "game_time", autoApply = True),      
       ConfigChoice(engine.config, "game", "accuracy_mode", autoApply = True),
       ConfigChoice(engine.config, "game", "accuracy_pos", autoApply = True),
       ConfigChoice(engine.config, "game", "decimal_places", autoApply = True), #MFH
       ConfigChoice(engine.config, "game", "gsolo_accuracy_disp", autoApply = True), #MFH
       ConfigChoice(engine.config, "game", "gsolo_acc_pos", autoApply = True), #MFH
       ConfigChoice(engine.config, "coffee", "noterotate", autoApply = True), #blazingamer
       ConfigChoice(engine.config, "game", "gfx_version_tag", autoApply = True), #MFH
    ]
    AdvancedVideoSettingsMenu = Menu.Menu(engine, AdvancedVideoSettings)
      
    modes = engine.video.getVideoModes()
    modes.reverse()
    Config.define("video",  "resolution", str,   "1024x768", text = _("Video Resolution"), options = ["%dx%d" % (m[0], m[1]) for m in modes])
    videoSettings = [
      ConfigChoice(engine.config, "video",  "resolution"),
      ConfigChoice(engine.config, "video",  "fullscreen"),
      ConfigChoice(engine.config, "video",  "multisamples"),
      ConfigChoice(engine.config, "video", "disable_fretsfx"),
      ConfigChoice(engine.config, "video", "hitglow_color"),
      ConfigChoice(engine.config, "video", "counting", autoApply = True),
      (_("Advanced Video Settings"), AdvancedVideoSettingsMenu),
    ]
    videoSettingsMenu = Menu.Menu(engine, videoSettings)

    fretSettings = [
      ConfigChoice(engine.config, "fretboard", "point_of_view", autoApply = True),
      ConfigChoice(engine.config, "coffee", "phrases", autoApply = True),
      ConfigChoice(engine.config, "game", "notedisappear", autoApply = True),
      ConfigChoice(engine.config, "game", "frets_under_notes", autoApply = True), #MFH
      ConfigChoice(engine.config, "game", "nstype", autoApply = True),      #blazingamer
      ConfigChoice(engine.config, "coffee", "neckSpeed", autoApply = True),
      ConfigChoice(engine.config, "game",   "hit_window", autoApply = True), #alarian: defines hit window
      ConfigChoice(engine.config, "game", "large_drum_neck", autoApply = True),      #myfingershurt
      ConfigChoice(engine.config, "game", "bass_groove_neck", autoApply = True),      #myfingershurt
      ConfigChoice(engine.config, "game", "guitar_solo_neck", autoApply = True),      #myfingershurt
      ConfigChoice(engine.config, "game", "incoming_neck_mode", autoApply = True),      #myfingershurt
      ConfigChoice(engine.config, "game", "solo_frame", autoApply = True),      #myfingershurt
      ConfigChoice(engine.config, "game", "in_game_font_shadowing", autoApply = True),      #myfingershurt
    ]
    fretSettingsMenu = Menu.Menu(engine, fretSettings)
    
    volumeSettings = [
      VolumeConfigChoice(engine, engine.config, "audio",  "guitarvol", autoApply = True),
      VolumeConfigChoice(engine, engine.config, "audio",  "songvol", autoApply = True),
      VolumeConfigChoice(engine, engine.config, "audio",  "rhythmvol", autoApply = True),
      VolumeConfigChoice(engine, engine.config, "audio",  "screwupvol", autoApply = True),
      VolumeConfigChoice(engine, engine.config, "audio",  "miss_volume", autoApply = True),
      VolumeConfigChoice(engine, engine.config, "audio",  "single_track_miss_volume", autoApply = True),
      VolumeConfigChoice(engine, engine.config, "audio",  "kill_volume", autoApply = True), #MFH
      VolumeConfigChoice(engine, engine.config, "audio",  "SFX_volume", autoApply = True), #MFH
    ]
    volumeSettingsMenu = Menu.Menu(engine, volumeSettings)
    
    AdvancedAudioSettings = [
       ConfigChoice(engine.config, "audio",  "delay", autoApply = True),     #myfingershurt: so a/v delay can be set without restarting FoF
       ConfigChoice(engine.config, "audio",  "frequency"),
       ConfigChoice(engine.config, "audio",  "bits"),
       ConfigChoice(engine.config, "audio",  "buffersize"),
       #ConfigChoice(engine.config, "game", "mute_sustain_releases", autoApply = True),   #myfingershurt
       ConfigChoice(engine.config, "game", "sustain_muting", autoApply = True),   #myfingershurt
       ConfigChoice(engine.config, "audio", "mute_last_second", autoApply = True), #MFH
       ConfigChoice(engine.config, "game", "bass_kick_sound", autoApply = True),   #myfingershurt
       ConfigChoice(engine.config, "game", "T_sound", autoApply = True), #Faaa Drum sound
       ConfigChoice(engine.config, "game", "result_cheer_loop", autoApply = True), #MFH
       ConfigChoice(engine.config, "game", "cheer_loop_delay", autoApply = True), #MFH
       ConfigChoice(engine.config, "game", "star_claps", autoApply = True),      #myfingershurt
       ConfigChoice(engine.config, "game", "beat_claps", autoApply = True), #racer
    ]
    AdvancedAudioSettingsMenu = Menu.Menu(engine, AdvancedAudioSettings)

    audioSettings = [
      (_("Volume Settings"),    volumeSettingsMenu),
      (_("Advanced Audio Settings"), AdvancedAudioSettingsMenu),
    ]
    audioSettingsMenu = Menu.Menu(engine, audioSettings)
    
    #MFH - new menu
    logfileSettings = [
      ConfigChoice(engine.config, "game", "log_ini_reads", autoApply = True),#myfingershurt
      ConfigChoice(engine.config, "game", "log_class_inits", autoApply = True),#myfingershurt
      ConfigChoice(engine.config, "game", "log_loadings", autoApply = True),#myfingershurt
      ConfigChoice(engine.config, "game", "log_sections", autoApply = True),#myfingershurt
      ConfigChoice(engine.config, "game", "log_undefined_gets", autoApply = True),#myfingershurt
      ConfigChoice(engine.config, "game", "log_marker_notes", autoApply = True),#myfingershurt
      ConfigChoice(engine.config, "game", "log_starpower_misses", autoApply = True),#myfingershurt
    ]
    logfileSettingsMenu = Menu.Menu(engine, logfileSettings)

    debugSettings = [
      ConfigChoice(engine.config, "video", "show_fps", autoApply = True),#evilynux
      ConfigChoice(engine.config, "game", "kill_debug", autoApply = True),#myfingershurt
      ConfigChoice(engine.config, "game", "hopo_debug_disp", autoApply = True),#myfingershurt
      ConfigChoice(engine.config, "game", "rock_band_events", autoApply = True),#myfingershurt
      ConfigChoice(engine.config, "game", "show_unused_text_events", autoApply = True),#myfingershurt
      #ConfigChoice(engine.config, "game", "font_rendering_mode", autoApply = True),#myfingershurt
      (_("Log Settings"),    logfileSettingsMenu),
    ]
    debugSettingsMenu = Menu.Menu(engine, debugSettings)
    
    ManualPerfSettings = [
       ConfigChoice(engine.config, "performance", "game_priority", autoApply = True),
       ConfigChoice(engine.config, "performance", "disable_libcount", autoApply = True),
       ConfigChoice(engine.config, "performance", "disable_librotation", autoApply = True),
       ConfigChoice(engine.config, "performance", "starspin"),
       ConfigChoice(engine.config, "performance", "static_strings", autoApply = True),      #myfingershurt
       ConfigChoice(engine.config, "performance", "killfx", autoApply = True),   #blazingamer
       ConfigChoice(engine.config, "performance", "star_score_updates", autoApply = True),   #MFH
       ConfigChoice(engine.config, "performance", "in_game_stats", autoApply = True),#myfingershurt
       ConfigChoice(engine.config, "performance", "preload_glyph_cache", autoApply = True),#evilynux
    ]
    ManualPerfSettingsMenu = Menu.Menu(engine, ManualPerfSettings)
    
    perfSettings = [
      ConfigChoice(engine.config, "performance", "autoset", autoApply = True),
      (_("Manual Settings (Autoset must be off)"), ManualPerfSettingsMenu),
      (_("Debug Settings"), debugSettingsMenu),
    ]
    perfSettingsMenu = Menu.Menu(engine, perfSettings)

    listSettings = [
      (_("Select Song Library >"), self.baseLibrarySelect),
      ConfigChoice(engine.config, "coffee", "songfilepath", autoApply = True),
      ConfigChoice(engine.config, "game",  "sort_order", autoApply = True),
      ConfigChoice(engine.config, "coffee", "songdisplay", autoApply = True),
      ConfigChoice(engine.config, "audio", "disable_preview", autoApply = True),  #myfingershurt
      ConfigChoice(engine.config, "game", "songlist_instrument", autoApply = True), #MFH
      ConfigChoice(engine.config, "game", "songlist_difficulty", autoApply = True), #evilynux
      ConfigChoice(engine.config, "game", "songlist_extra_stats", autoApply = True), #evilynux
      ConfigChoice(engine.config, "game", "HSMovement", autoApply = True), #racer
      ConfigChoice(engine.config, "game", "quickplay_career_tiers", autoApply = True),  #myfingershurt
    ]
    listSettingsMenu = Menu.Menu(engine, listSettings)

    ThemeSettings = [
      ConfigChoice(engine.config, "game", "miss_pauses_anim", autoApply = True),   #myfingershurt
      ConfigChoice(engine.config, "game", "rb_sp_neck_glow", autoApply = True),
      ConfigChoice(engine.config, "game",   "rbmfx", autoApply = True), #blazingamer
      ConfigChoice(engine.config, "game", "starfx", autoApply = True),
      ConfigChoice(engine.config, "game", "rbnote", autoApply = True), #racer
      ConfigChoice(engine.config, "game", "in_game_stars", autoApply = True),#myfingershurt
      ConfigChoice(engine.config, "game", "partial_stars", autoApply = True),#myfingershurt
      ConfigChoice(engine.config, "game", "sp_notes_while_active", autoApply = True),   #myfingershurt - setting for gaining more SP while active
    ]
    ThemeSettingsMenu = Menu.Menu(engine, ThemeSettings)
    
    
    AdvancedSettings = [
       (_("FoFix Advanced Settings"), FoFiXAdvancedSettingsMenu),
       (_("Theme Settings"), ThemeSettingsMenu),
       (_("Fretboard Settings"), fretSettingsMenu),
    ]
    AdvancedSettingsMenu = Menu.Menu(engine, AdvancedSettings)
    
    settings = [
      (_(engine.versionString+_(" Basic Settings")),   FoFiXBasicSettingsMenu),
      (_("Controls"),          keySettingsMenu),
      (_("Library"),   listSettingsMenu),
      (_("Audio"),      audioSettingsMenu),
      (_("Video"),     videoSettingsMenu),
      (_("Performances/Debug"), perfSettingsMenu),
      (_("Advanced Settings"), AdvancedSettingsMenu),
      (_("Mod settings"), modSettings),
      (_("Credits"), lambda: Dialogs.showCredits(engine)), # evilynux - Show Credits!
      (_("Apply New Settings"), self.applySettings)
    ]
  
    self.settingsToApply = videoSettings + \
                           AdvancedAudioSettings + \
                           keySettings + \
			                     AdvancedVideoSettings + \
                           FoFiXBasicSettings + \
                           perfSettings + \
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



    Menu.Menu.__init__(self, engine, settings, pos = (self.opt_text_x, self.opt_text_y), textColor = self.opt_text_color, selectedColor = self.opt_selected_color)   #MFH - add position to this so we can move it

  def applySettings(self):
    for option in self.settingsToApply:
      if isinstance(option, ConfigChoice):
        option.apply()
    self.engine.restart()

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
  def __init__(self, engine):

    self.logClassInits = Config.get("game", "log_class_inits")
    if self.logClassInits == 1:
      Log.debug("GameSettingsMenu class init (Settings.py)...")

    settings = [
      VolumeConfigChoice(engine, engine.config, "audio",  "guitarvol", autoApply = True),
      VolumeConfigChoice(engine, engine.config, "audio",  "songvol", autoApply = True),
      VolumeConfigChoice(engine, engine.config, "audio",  "rhythmvol", autoApply = True),
      VolumeConfigChoice(engine, engine.config, "audio",  "screwupvol", autoApply = True),
      VolumeConfigChoice(engine, engine.config, "audio",  "miss_volume", autoApply = True),
      VolumeConfigChoice(engine, engine.config, "audio",  "single_track_miss_volume", autoApply = True),
      VolumeConfigChoice(engine, engine.config, "audio",  "kill_volume", autoApply = True), #MFH
      VolumeConfigChoice(engine, engine.config, "audio",  "SFX_volume", autoApply = True), #MFH
      ConfigChoice(engine.config, "audio",  "delay", autoApply = True),   #myfingershurt: so the a/v delay can be adjusted in-game
      ConfigChoice(engine.config, "game", "jurgdef", autoApply = True),#Jurgen config -- Spikehead777
      ConfigChoice(engine.config, "game", "jurgtype", autoApply = True),#Jurgen controls -- Spikehead777
      ConfigChoice(engine.config, "game", "jurglogic", autoApply = True),#MFH
      ConfigChoice(engine.config, "game", "stage_rotate_delay", autoApply = True),   #myfingershurt - user defined stage rotate delay
      ConfigChoice(engine.config, "game", "stage_animate_delay", autoApply = True),   #myfingershurt - user defined stage rotate delay
      ConfigChoice(engine.config, "player0",  "leftymode", autoApply = True),
      ConfigChoice(engine.config, "player1",  "leftymode", autoApply = True), #QQstarS
    ]
    Menu.Menu.__init__(self, engine, settings, pos = (.3, .31), viewSize = 5)

