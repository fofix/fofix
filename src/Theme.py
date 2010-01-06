#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire X (FoFiX)                                           #
# Copyright (C) 2006 Sami Kyöstilä                                  #
#               2008 myfingershurt                                  #
#               2008 Blazingamer                                    #
#               2008 evilynux <evilynux@gmail.com>                  #
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

import Log
import Version
import os
import sys
import imp

import Config
import Song
from OpenGL.GL import *
from OpenGL.GLU import *
import string
import math
from Language import _
from Shader import shaders
from Task import Task

#Theme Constants.

LEFT   = 0
CENTER = 1
RIGHT  = 2

# read the color scheme from the config file
Config.define("theme", "background_color",  str, "#000000")
Config.define("theme", "base_color",        str, "#FFFFFF")
Config.define("theme", "selected_color",    str, "#FFBF00")

Config.define("theme", "mesh_color",        str, "#000000")#blazingamer
Config.define("theme", "hopo_color",        str, "#00AAAA")
Config.define("theme", "spot_color",        str, "#FFFFFF")
Config.define("theme", "key_color",         str, "#333333")
Config.define("theme", "key2_color",        str, "#000000")
Config.define("theme", "tracks_color",      str, "#FFFF80")
Config.define("theme", "bars_color",        str, "#FFFF80")
Config.define("theme", "glow_color",        str, "fret")

Config.define("theme", "loading_phrase",    str, None)
Config.define("theme", "results_phrase",    str, None)

Config.define("theme", "fret0_color",       str, "#22FF22")
Config.define("theme", "fret1_color",       str, "#FF2222")
Config.define("theme", "fret2_color",       str, "#FFFF22")
Config.define("theme", "fret3_color",       str, "#3333FF")
Config.define("theme", "fret4_color",       str, "#FF9933")
Config.define("theme", "fret5_color",       str, "#CC22CC")

Config.define("theme", "pov_target_x",       float, None)
Config.define("theme", "pov_target_y",       float, None)
Config.define("theme", "pov_target_z",       float, None)

Config.define("theme", "pov_origin_x",       float, None)
Config.define("theme", "pov_origin_y",       float, None)
Config.define("theme", "pov_origin_z",       float, None)

#Volshebnyi - spNote and killswitch tail colors
Config.define("theme", "fretS_color",       str, "#4CB2E5")
Config.define("theme", "fretK_color",       str, "#000000")
Config.define("theme", "use_fret_colors",   bool, False)
Config.define("theme", "obar_hscale",       float, 0.7)
Config.define("theme", "obar_3dfill",       bool, False)

#blazingamer
Config.define("theme", "menu_x",       float, None)
Config.define("theme", "menu_y",       float, None)
Config.define("theme", "rbmenu",       bool, False)


Config.define("theme", "loading_x",       float, 0.5)
Config.define("theme", "loading_y",       float, 0.6)
Config.define("theme", "loading_text_color", str, "#FFFFFF")
Config.define("theme", "loading_font_scale", float, 0.0015)
Config.define("theme", "loading_right_margin", float, 1.0)
Config.define("theme", "loading_line_spacing", float, 1.0)

Config.define("theme", "twoDnote",       bool, True)
Config.define("theme", "twoDkeys",       bool, True)
Config.define("theme", "threeDspin",       bool, True)
Config.define("theme", "fret_press",     bool,  True)
Config.define("theme", "opencolor",       str, "#FF9933")

Config.define("theme", "versiontag",       bool, False)
Config.define("theme", "rmtype",       int, None)
Config.define("theme", "mark_solo_sections", int, 2)

Config.define("theme", "shadowoffsetx", float, .0022)
Config.define("theme", "shadowoffsety", float, .0005)

Config.define("theme", "noterot1",      float, 0)
Config.define("theme", "noterot2",      float, 0)
Config.define("theme", "noterot3",      float, 0)
Config.define("theme", "noterot4",      float, 0)
Config.define("theme", "noterot5",      float, 0)

Config.define("theme", "keyrot1",      float, 0)
Config.define("theme", "keyrot2",      float, 0)
Config.define("theme", "keyrot3",      float, 0)
Config.define("theme", "keyrot4",      float, 0)
Config.define("theme", "keyrot5",      float, 0)

Config.define("theme", "drumnoterot1",      float, 0)
Config.define("theme", "drumnoterot2",      float, 0)
Config.define("theme", "drumnoterot3",      float, 0)
Config.define("theme", "drumnoterot4",      float, 0)
Config.define("theme", "drumnoterot5",      float, 0)

Config.define("theme", "drumkeyrot1",      float, 0)
Config.define("theme", "drumkeyrot2",      float, 0)
Config.define("theme", "drumkeyrot3",      float, 0)
Config.define("theme", "drumkeyrot4",      float, 0)
Config.define("theme", "drumkeyrot5",      float, 0)

Config.define("theme", "notepos1",      float, 0)
Config.define("theme", "notepos2",      float, 0)
Config.define("theme", "notepos3",      float, 0)
Config.define("theme", "notepos4",      float, 0)
Config.define("theme", "notepos5",      float, 0)

Config.define("theme", "drumnotepos1",      float, 0)
Config.define("theme", "drumnotepos2",      float, 0)
Config.define("theme", "drumnotepos3",      float, 0)
Config.define("theme", "drumnotepos4",      float, 0)
Config.define("theme", "drumnotepos5",      float, 0)

Config.define("theme", "keypos1",      float, 0)
Config.define("theme", "keypos2",      float, 0)
Config.define("theme", "keypos3",      float, 0)
Config.define("theme", "keypos4",      float, 0)
Config.define("theme", "keypos5",      float, 0)

Config.define("theme", "drumkeypos1",      float, 0)
Config.define("theme", "drumkeypos2",      float, 0)
Config.define("theme", "drumkeypos3",      float, 0)
Config.define("theme", "drumkeypos4",      float, 0)
Config.define("theme", "drumkeypos5",      float, 0)

#TWD
Config.define("theme", "menu_neck_choose_x", float, 0.1)
Config.define("theme", "menu_neck_choose_y", float, 0.05)

#akedrou - lobby/control activator/avatars
Config.define("theme", "control_activate_x", float, 0.645)
Config.define("theme", "control_activate_select_x", float, 0.5)
Config.define("theme", "control_activate_part_x", float, 0.41)
Config.define("theme", "control_activate_y", float, 0.18)
Config.define("theme", "control_activate_scale", float, 0.0018)
Config.define("theme", "control_activate_part_size", float, 22.000)
Config.define("theme", "control_activate_space", float, 0.045)
Config.define("theme", "control_activate_font", str, "font")
Config.define("theme", "control_description_x", float, 0.5)
Config.define("theme", "control_description_y", float, 0.13)
Config.define("theme", "control_description_scale", float, 0.002)
Config.define("theme", "control_description_font", str, "font")
Config.define("theme", "control_check_x", float, 0.16)
Config.define("theme", "control_check_y", float, 0.26)
Config.define("theme", "control_check_text_y", float, 0.61)
Config.define("theme", "control_check_part_mult", float, 2.8)
Config.define("theme", "control_check_space", float, 0.23)
Config.define("theme", "control_check_scale", float, 0.0018)
Config.define("theme", "control_check_font", str, "font")
Config.define("theme", "lobby_mode", int, 0)
Config.define("theme", "lobby_preview_x", float, 0.7)
Config.define("theme", "lobby_preview_y", float, 0.0) #worldrave
Config.define("theme", "lobby_preview_spacing", float, 0.04)
Config.define("theme", "lobby_title_x", float, 0.5)
Config.define("theme", "lobby_title_y", float, 0.07)
Config.define("theme", "lobby_title_character_x", float, 0.26)
Config.define("theme", "lobby_title_character_y", float, 0.24)
Config.define("theme", "lobby_title_scale", float, 0.0024)
Config.define("theme", "lobby_title_font", str, "loadingFont")
Config.define("theme", "lobby_avatar_x", float, 0.7)
Config.define("theme", "lobby_avatar_y", float, 0.75)
Config.define("theme", "lobby_avatar_scale", float, 1.0)
Config.define("theme", "lobby_select_x", float, 0.4)
Config.define("theme", "lobby_select_y", float, 0.32)
Config.define("theme", "lobby_select_image_x", float, 0.255)
Config.define("theme", "lobby_select_image_y", float, 0.335)
Config.define("theme", "lobby_select_scale", float, 0.0018)
Config.define("theme", "lobby_select_space", float, 0.04)
Config.define("theme", "lobby_select_font", str, "font")
Config.define("theme", "lobby_select_length", int, 5)
Config.define("theme", "lobby_title_color", str, "#FFFFFF")
Config.define("theme", "lobby_player_color", str, "#FFFFFF")
Config.define("theme", "lobby_info_color", str, "#FFFFFF")
Config.define("theme", "lobby_font_color", str, "#FFFFFF")
Config.define("theme", "lobby_select_color", str, "#FFBF00")
Config.define("theme", "lobby_disable_color", str, "#666666")
Config.define("theme", "character_create_x", float, 0.25)
Config.define("theme", "character_create_y", float, 0.15)
Config.define("theme", "character_create_help_x", float, 0.5)
Config.define("theme", "character_create_help_y", float, 0.73)
Config.define("theme", "character_create_help_scale", float, 0.0018)
Config.define("theme", "character_create_option_x", float, 0.75)
Config.define("theme", "character_create_option_font", str, "font")
Config.define("theme", "character_create_font_color", str, "#FFFFFF")
Config.define("theme", "character_create_select_color", str, "#FFBF00")
Config.define("theme", "character_create_help_color", str, "#FFFFFF")
Config.define("theme", "character_create_help_font", str, "loadingFont")
Config.define("theme", "character_create_scale", float, .0018)
Config.define("theme", "character_create_space", float, .045)
Config.define("theme", "avatar_select_text_x",   float, .44)
Config.define("theme", "avatar_select_text_y",   float, .16)
Config.define("theme", "avatar_select_text_scale",   float, .0027)
Config.define("theme", "avatar_select_font",   str, "font")
Config.define("theme", "avatar_select_avatar_x", float, .667)
Config.define("theme", "avatar_select_avatar_y", float, .5)
Config.define("theme", "avatar_select_wheel_y", float, 0.0)

#akedrou, with the vocals, in notepad++
Config.define("theme", "vocal_meter_size", float, 45.000)
Config.define("theme", "vocal_meter_x", float, .25)
Config.define("theme", "vocal_meter_y", float, .8)
Config.define("theme", "vocal_mult_x", float, .28)
Config.define("theme", "vocal_mult_y", float, .8)
Config.define("theme", "vocal_power_x", float, .5)
Config.define("theme", "vocal_power_y", float, .8)
Config.define("theme", "vocal_fillup_center_x", int, 139)
Config.define("theme", "vocal_fillup_center_y", int, 151)
Config.define("theme", "vocal_fillup_in_radius", int, 25)
Config.define("theme", "vocal_fillup_out_radius", int, 139)
Config.define("theme", "vocal_fillup_color", str, "#DFDFDE")
Config.define("theme", "vocal_fillup_factor", float, 300.000)
Config.define("theme", "vocal_circular_fillup", bool, True)
Config.define("theme", "vocal_lane_size", float, .002)
Config.define("theme", "vocal_glow_size", float, .012)
Config.define("theme", "vocal_glow_fade", float, .6)
Config.define("theme", "vocal_lane_color", str, "#99FF80")
Config.define("theme", "vocal_shadow_color", str, "#CCFFBF")
Config.define("theme", "vocal_glow_color", str, "#33FF00")
Config.define("theme", "vocal_lane_color_star", str, "#FFFF80")
Config.define("theme", "vocal_shadow_color_star", str, "#FFFFBF")
Config.define("theme", "vocal_glow_color_star", str, "#FFFF00")

#worldrave
Config.define("theme", "setlistguidebuttonsposX", float, 0.408)
Config.define("theme", "setlistguidebuttonsposY", float, 0.0322)
Config.define("theme", "setlistguidebuttonsscaleX", float, 0.29)
Config.define("theme", "setlistguidebuttonsscaleY", float, 0.308)
Config.define("theme", "setlistpreviewbuttonposX", float, 0.5)
Config.define("theme", "setlistpreviewbuttonposY", float, 0.5)
Config.define("theme", "setlistpreviewbuttonscaleX", float, 0.5)
Config.define("theme", "setlistpreviewbuttonscaleY", float, 0.5)
Config.define("theme", "versiontagposX", float, 0.5)
Config.define("theme", "versiontagposY", float, 0.5)

#evilynux
Config.define("theme", "songlist_score_color",  str, "#93C351")
Config.define("theme", "songlistcd_score_color",  str, "#FFFFFF")
Config.define("theme", "rockmeter_score_color",  str, "#FFFFFF")
Config.define("theme", "ingame_stats_color",  str, "#FFFFFF")

#MFH
Config.define("theme", "song_cd_x",       float, 0.0)
Config.define("theme", "song_cdscore_x",       float, 0.6)
Config.define("theme", "song_list_x",       float, 0.15)
Config.define("theme", "song_listscore_x",       float, 0.8)

Config.define("theme", "song_listcd_cd_x",       float, .75)
Config.define("theme", "song_listcd_cd_y",       float, .6)
Config.define("theme", "song_listcd_score_x",       float, .6)
Config.define("theme", "song_listcd_score_y",       float, .5)
Config.define("theme", "song_listcd_list_x",       float, .1)

Config.define("theme", "song_rb2_diff_color",       str, "#FFBF00")

Config.define("theme", "pause_bkg",       str, "0.5,0.5,1.0,1.0")
Config.define("theme", "pause_text_x",       float, None)
Config.define("theme", "pause_text_y",       float, None)
Config.define("theme", "pause_text_color",  str, "#FFFFFF")
Config.define("theme", "pause_selected_color",  str, "#FFBF00")

Config.define("theme", "opt_bkg",   str, "0.5,0.5,1.0,1.0")
Config.define("theme", "opt_text_x",       float, None)
Config.define("theme", "opt_text_y",       float, None)
Config.define("theme", "opt_text_color",  str, "#FFFFFF")
Config.define("theme", "opt_selected_color",  str, "#FFBF00")


Config.define("theme", "main_menu_scale",       float, None)
Config.define("theme", "main_menu_vspacing",       float, None)
Config.define("theme", "use_solo_submenu",       bool, None)
Config.define("theme", "sub_menu_x",       float, None)
Config.define("theme", "sub_menu_y",       float, None)

Config.define("theme", "menu_tip_text_y", float, .7)
Config.define("theme", "menu_tip_text_font", str, "font")
Config.define("theme", "menu_tip_text_scale", float, .002)
Config.define("theme", "menu_tip_text_color", str, None)
Config.define("theme", "menu_tip_text_scroll_space", float, .25)
Config.define("theme", "menu_tip_text_scroll_mode", int, 0)
Config.define("theme", "menu_tip_text_display", bool, False)

Config.define("theme", "career_title_color",  str, "#000000")
Config.define("theme", "song_name_text_color",  str, "#FFFFFF")
Config.define("theme", "song_name_selected_color",  str, "#FFBF00")
Config.define("theme", "artist_text_color",  str, "#4080FF")
Config.define("theme", "artist_selected_color",  str, "#4080FF")
Config.define("theme", "library_text_color",  str, "#FFFFFF")
Config.define("theme", "library_selected_color",  str, "#FFBF00")


Config.define("theme", "fail_text_color",  str, "#FFFFFF")
Config.define("theme", "fail_completed_color",  str, "#FFFFFF")
Config.define("theme", "fail_selected_color",  str, "#FFBF00")

Config.define("theme", "result_score", str, ".5,.11,0.0025,None,None")
Config.define("theme", "result_song", str, ".05,.045,.002,None,None")
Config.define("theme", "result_song_form", int, 0)
Config.define("theme", "result_song_text", str, "%s Finished!")
Config.define("theme", "result_star", str, ".5,.4,0.15,1.1")
Config.define("theme", "result_star_type", int, 0)
Config.define("theme", "result_stats_diff", str, ".5,.55,0.002,None,None")
Config.define("theme", "result_stats_diff_text", str, "Difficulty: %s")
Config.define("theme", "result_stats_part", str, ".5,.64,0.002,None,None")
Config.define("theme", "result_stats_part_text", str, "Part: %s")
Config.define("theme", "result_stats_name", str, ".5,.73,0.002,None,None")
Config.define("theme", "result_stats_streak", str, ".5,.58,0.002,None,None")
Config.define("theme", "result_stats_streak_text", str, "Long Streak: %s")
Config.define("theme", "result_stats_accuracy", str, ".5,.61,0.002,None,None")
Config.define("theme", "result_stats_accuracy_text", str, "Accuracy: %.1f%%")
Config.define("theme", "result_stats_notes", str, ".5,.52,0.002,None,None")
Config.define("theme", "result_stats_notes_text", str, "%s Notes Hit")
Config.define("theme", "result_cheats_info", str, ".5,.3,.002")
Config.define("theme", "result_cheats_numbers", str, ".5,.35,.0015")
Config.define("theme", "result_cheats_score", str, ".75,.4,.0015")
Config.define("theme", "result_cheats_percent", str, ".45,.4,.0015")
Config.define("theme", "result_cheats_color", str, "#FFFFFF")
Config.define("theme", "result_cheats_font", str, "font")
Config.define("theme", "result_high_score_font", str, "font")
Config.define("theme", "result_menu_x", float, .5)
Config.define("theme", "result_menu_y", float, .2)

Config.define("theme", "jurgen_text_pos", str, "1,1,.00035")


#MFH - crowd cheer loop delay in ini: if not exist, use value from settings. Otherwise, use ini value.
Config.define("theme", "crowd_loop_delay",  int, None)

#MFH - for instrument / difficulty / practice section submenu positioning
Config.define("theme", "song_select_submenu_x",  float, None)
Config.define("theme", "song_select_submenu_y",  float, None)

#MFH - for scaling song info during countdown
Config.define("theme", "song_info_display_scale",  float, 0.0020)

#Worldrave - for song info display positioning
Config.define("theme", "song_info_display_X",  float, 0.05)
Config.define("theme", "song_info_display_Y",  float, 0.05)
Config.define("theme", "neck_length",    float, 9.0)

#MFH - option for Rock Band 2 ini - only show # of stars you are working on
Config.define("theme", "display_all_grey_stars",  bool, True)
Config.define("theme", "small_1x_mult", bool, True)

#MFH - y offset = lines, x offset = spaces
Config.define("theme", "song_select_submenu_offset_lines",  int, 2)
Config.define("theme", "song_select_submenu_offset_spaces",  int, 2)

#Qstick - hopo indicator position and color
Config.define("theme", "hopo_indicator_x",       float, None)
Config.define("theme", "hopo_indicator_y",       float, None)
Config.define("theme", "hopo_indicator_active_color",   str, "#FFFFFF")
Config.define("theme", "hopo_indicator_inactive_color",   str, "#666666")

#stump - parameters for continuous fillup of stars
Config.define("theme", "star_fillup_center_x", int, None)
Config.define("theme", "star_fillup_center_y", int, None)
Config.define("theme", "star_fillup_in_radius", int, None)
Config.define("theme", "star_fillup_out_radius", int, None)
Config.define("theme", "star_fillup_color", str, None)

#Qstick - Misc
Config.define("theme", "song_list_display",       int, None)
Config.define("theme", "neck_width",    float, 3.0)
Config.define("theme", "power_up_name", str, None)

#Qstick - Results Screen

#RACER:
Config.define("theme", "fail_bkg",       str, "0.5,0.5,1.0,1.0")
Config.define("theme", "fail_text_x",       float, None)
Config.define("theme", "fail_text_y",       float, None)
Config.define("theme", "fail_songname_x",  float, 0.5)
Config.define("theme", "fail_songname_y",  float, 0.35)

defaultDict = {}
defaultDict['panelAvatarDimension'] = (200.00, 110.00)
defaultDict['lobbyTitleText']      = _("Lobby")
defaultDict['lobbyTitleTextPos']   = (.98, .1)
defaultDict['lobbyTitleTextAlign'] = RIGHT
defaultDict['lobbyTitleTextScale'] = .0005
defaultDict['lobbyTitleTextFont']  = "font"

defaultDict['lobbySubtitleText']      = _("Choose Your Character!")
defaultDict['lobbySubtitleTextPos']   = (.5, .1)
defaultDict['lobbySubtitleTextAlign'] = CENTER
defaultDict['lobbySubtitleTextScale'] = .0015
defaultDict['lobbySubtitleTextFont']  = "font"

defaultDict['lobbyOptionScale']       = .001
defaultDict['lobbyOptionAlign']       = CENTER
defaultDict['lobbyOptionFont']        = "font"
defaultDict['lobbyOptionPos']         = (.5, .46)
defaultDict['lobbyOptionSpace']       = .04
defaultDict['lobbyOptionColor']       = (1,1,1)

defaultDict['lobbySaveCharScale']     = .001
defaultDict['lobbySaveCharAlign']     = CENTER
defaultDict['lobbySaveCharFont']      = "font"
defaultDict['lobbySaveCharColor']     = (1,1,1)

defaultDict['lobbyPanelNameFont']     = "font"
defaultDict['lobbyPanelNameScale']    = .001
defaultDict['lobbyPanelNameAlign']    = LEFT
defaultDict['lobbyControlPos']        = (.5,.375)
defaultDict['lobbyControlFont']       = "font"
defaultDict['lobbyControlScale']      = .0025
defaultDict['lobbyControlAlign']      = CENTER
defaultDict['lobbyHeaderColor']       = (1,1,1)
defaultDict['lobbySelectLength']      = 4
defaultDict['lobbyPanelAvatarDimension'] = (200.00, 110.00)

defaultDict['lobbyKeyboardModColor']  = (1,1,1)
defaultDict['lobbySelectedColor'] = (1,1,1)
defaultDict['lobbyDisabledColor'] = (.6,.6,.6)

defaultDict['lobbyPanelSize']    = (.2, .8)
defaultDict['lobbyPanelSpacing'] = .24

classNames = {'setlist': lambda x: Setlist(x), 'themeLobby': lambda x: ThemeLobby(x), 'partDiff': lambda x: ThemeParts(x)}

class Theme(Task):
  def __str__(self):
    return "Default Theme Renderer"
  
  def __getattr__(self, attr):
    try: #getting to this function is kinda slow. Set it on the first get to keep renders from lagging.
      object.__getattribute__(self, '__dict__')[attr] = defaultDict[attr]
      if Config.get("game", "log_undefined_gets") == 1:
        Log.debug("No theme variable for %s - Loading default..." % attr)
      return object.__getattribute__(self, attr)
    except KeyError:
      if attr in classNames.keys():
        Log.warn("No theme class for %s - Loading default..." % attr)
        object.__getattribute__(self, '__dict__')[attr] = classNames[attr](self)
        return object.__getattribute__(self, attr)
      elif attr.startswith('__') and attr.endswith('__'): #for object's attributes (eg: __hash__, __eq__)
        return object.__getattribute__(self, attr)
      Log.error("Attempted to load theme variable %s - no default found." % attr)
  
  def __init__(self, path, name, iniFile = True):
    self.name = name
    self.path = path
    
    self.themePath = os.path.join(Version.dataPath(),"themes", name)
    if not os.path.exists(self.themePath):
      Log.error("Theme: %s does not exist!\n" % self.themePath)
      name = Config.get("coffee", "themename")
      Log.notice("Theme: Attempting fallback to default theme \"%s\"." % name)
      self.themePath = os.path.join(Version.dataPath(),"themes", name)
      if not os.path.exists(self.themePath):
        Log.error("Theme: %s does not exist!\nExiting.\n" % self.themePath)
        sys.exit(1)

    if iniFile:
      self.config = Config.load(os.path.join(self.themePath, "theme.ini"))
      config = self.config
      
      #Colors
      self.backgroundColor = self.hexToColor(self.config.get("theme", "background_color"))  
      self.baseColor = self.hexToColor(self.config.get("theme", "base_color"))
      self.selectedColor = self.hexToColor(self.config.get("theme", "selected_color"))
      self.meshColor = self.hexToColor(self.config.get("theme", "mesh_color"))
      self.hopoColor = self.hexToColor(self.config.get("theme", "hopo_color"))
      self.spotColor = self.hexToColor(self.config.get("theme", "spot_color"))
      self.keyColor = self.hexToColor(self.config.get("theme", "key_color"))
      self.key2Color = self.hexToColor(self.config.get("theme", "key2_color"))
      self.tracksColor = self.hexToColor(self.config.get("theme", "tracks_color"))
      self.barsColor = self.hexToColor(self.config.get("theme", "bars_color"))
      self.glowColor = self.hexToColor(self.config.get("theme", "glow_color"))
      
      #Note Colors (this applies to frets and notes)
      self.noteColors = [self.hexToColor(config.get("theme", "fret%d_color" % i)) for i in range(6)]
      self.spNoteColor = self.hexToColor(config.get("theme", "fretS_color"))
      self.killNoteColor = self.hexToColor(config.get("theme", "fretK_color"))
      self.use_fret_colors = config.get("theme", "use_fret_colors")
      
      #Point of View
      self.povTargetX = config.get("theme", "pov_target_x")  
      self.povTargetY = config.get("theme", "pov_target_y")
      self.povTargetZ = config.get("theme", "pov_target_z")
      self.povOriginX = config.get("theme", "pov_origin_x")
      self.povOriginY = config.get("theme", "pov_origin_y")
      self.povOriginZ = config.get("theme", "pov_origin_z")
      
      #Loading phrases
      self.loadingPhrase = config.get("theme", "loading_phrase").split('_')
      self.resultsPhrase = config.get("theme", "results_phrase").split('_')
      
      #Miscellany (aka Garbage no one cares about)
      self.crowdLoopDelay = config.get("theme", "crowd_loop_delay")
      self.songInfoDisplayScale = config.get("theme", "song_info_display_scale")
      self.songInfoDisplayX = config.get("theme", "song_info_display_X")
      self.songInfoDisplayY = config.get("theme", "song_info_display_Y")
      self.displayAllGreyStars = config.get("theme", "display_all_grey_stars")
      self.smallMult = config.get("theme", "small_1x_mult")
      self.jurgTextPos = config.get("theme", "jurgen_text_pos").split(",")
      self.oBarHScale = config.get("theme", "obar_hscale")
      self.oBar3dFill = config.get("theme", "obar_3dfill")
      self.power_up_name = config.get("theme", "power_up_name")
      
      #Continuous star fillup!
      self.starFillupCenterX = config.get("theme", "star_fillup_center_x")
      self.starFillupCenterY = config.get("theme", "star_fillup_center_y")
      self.starFillupInRadius = config.get("theme", "star_fillup_in_radius")
      self.starFillupOutRadius = config.get("theme", "star_fillup_out_radius")
      self.starFillupColor = config.get("theme", "star_fillup_color")
      
      #Neck size, neck choose (yeah? you got a problem with that goruping?)
      self.neckWidth = config.get("theme", "neck_width")
      self.neckLength = config.get("theme", "neck_length")
      self.neck_prompt_x = config.get("theme", "menu_neck_choose_x")
      self.neck_prompt_y = config.get("theme", "menu_neck_choose_y")
      
      #Setlist
      self.songListDisplay = config.get("theme", "song_list_display")
      self.setlistguidebuttonsposX = config.get("theme", "setlistguidebuttonsposX")
      self.setlistguidebuttonsposY = config.get("theme", "setlistguidebuttonsposY")
      self.setlistguidebuttonsscaleX = config.get("theme", "setlistguidebuttonsscaleX")
      self.setlistguidebuttonsscaleY = config.get("theme", "setlistguidebuttonsscaleY")
      self.setlistpreviewbuttonposX = config.get("theme", "setlistpreviewbuttonposX")
      self.setlistpreviewbuttonposY = config.get("theme", "setlistpreviewbuttonposY")
      self.setlistpreviewbuttonscaleX = config.get("theme", "setlistpreviewbuttonscaleX")
      self.setlistpreviewbuttonscaleY = config.get("theme", "setlistpreviewbuttonscaleY")
      self.versiontagposX = config.get("theme", "versiontagposX")
      self.versiontagposY = config.get("theme", "versiontagposY")
      self.songSelectSubmenuOffsetLines = config.get("theme", "song_select_submenu_offset_lines")
      self.songSelectSubmenuOffsetSpaces = config.get("theme", "song_select_submenu_offset_spaces")
      self.songSelectSubmenuX = config.get("theme", "song_select_submenu_x")
      self.songSelectSubmenuY = config.get("theme", "song_select_submenu_y")
      self.song_cd_Xpos = config.get("theme", "song_cd_x")
      self.song_listcd_cd_Xpos = config.get("theme", "song_listcd_cd_x")
      self.song_listcd_cd_Ypos = config.get("theme", "song_listcd_cd_y")
      self.song_listcd_score_Xpos = config.get("theme", "song_listcd_score_x")
      self.song_listcd_score_Ypos = config.get("theme", "song_listcd_score_y")
      self.songlist_score_colorVar = self.hexToColor(config.get("theme", "songlist_score_color"))
      self.songlistcd_score_colorVar = self.hexToColor(config.get("theme", "songlistcd_score_color"))
      self.song_listcd_list_Xpos = config.get("theme", "song_listcd_list_x")
      self.song_cdscore_Xpos = config.get("theme", "song_cdscore_x")
      self.song_list_Xpos = config.get("theme", "song_list_x")
      self.song_listscore_Xpos = config.get("theme", "song_listscore_x")
      self.career_title_colorVar = self.hexToColor(config.get("theme", "career_title_color"))
      self.opt_text_colorVar = self.hexToColor(config.get("theme", "opt_text_color"))
      self.opt_selected_colorVar = self.hexToColor(config.get("theme", "opt_selected_color"))
      self.song_name_text_colorVar = self.hexToColor(config.get("theme", "song_name_text_color"))
      self.song_name_selected_colorVar = self.hexToColor(config.get("theme", "song_name_selected_color"))
      self.artist_text_colorVar = self.hexToColor(config.get("theme", "artist_text_color"))
      self.artist_selected_colorVar = self.hexToColor(config.get("theme", "artist_selected_color"))
      self.library_text_colorVar = self.hexToColor(config.get("theme", "library_text_color"))
      self.library_selected_colorVar = self.hexToColor(config.get("theme", "library_selected_color"))
      self.pause_text_colorVar = self.hexToColor(config.get("theme", "pause_text_color"))
      self.pause_selected_colorVar = self.hexToColor(config.get("theme", "pause_selected_color"))
      self.fail_completed_colorVar = self.hexToColor(config.get("theme", "fail_completed_color"))
      self.fail_text_colorVar = self.hexToColor(config.get("theme", "fail_text_color"))
      self.fail_selected_colorVar = self.hexToColor(config.get("theme", "fail_selected_color"))
      self.song_rb2_diff_colorVar = self.hexToColor(config.get("theme", "song_rb2_diff_color"))
      
      #pause menu and fail menu
      self.pause_bkg_pos = config.get("theme", "pause_bkg").split(",")
      self.pause_text_xPos = config.get("theme", "pause_text_x")
      self.pause_text_yPos = config.get("theme", "pause_text_y")
      self.opt_bkg_size = config.get("theme", "opt_bkg").split(",")
      self.opt_text_xPos = config.get("theme", "opt_text_x")
      self.opt_text_yPos = config.get("theme", "opt_text_y")
      self.fail_bkg_pos = config.get("theme", "fail_bkg").split(",")
      self.fail_text_xPos = config.get("theme", "fail_text_x")
      self.fail_text_yPos = config.get("theme", "fail_text_y")
      self.fail_songname_xPos = config.get("theme", "fail_songname_x") 
      self.fail_songname_yPos = config.get("theme", "fail_songname_y") 
      
      #main menu system
      self.menuX = config.get("theme", "menu_x")
      self.menuY = config.get("theme", "menu_y")
      self.menuRB = config.get("theme", "rbmenu")
      self.loadingX = config.get("theme", "loading_x")
      self.loadingY = config.get("theme", "loading_y")
      self.loadingColor = self.hexToColor(config.get("theme", "loading_text_color"))
      self.loadingFScale = config.get("theme", "loading_font_scale")
      self.loadingRMargin = config.get("theme", "loading_right_margin")
      self.loadingLSpacing = config.get ("theme", "loading_line_spacing")
      self.main_menu_scaleVar = config.get("theme", "main_menu_scale")
      self.main_menu_vspacingVar = config.get("theme", "main_menu_vspacing")
      self.use_solo_submenu = config.get("theme", "use_solo_submenu")
      self.sub_menu_xVar = config.get("theme", "sub_menu_x")
      self.sub_menu_yVar = config.get("theme", "sub_menu_y")
      self.songback = config.get("theme", "songback")
      self.versiontag = config.get("theme", "versiontag")
      self.shadowoffsetx = config.get("theme", "shadowoffsetx")
      self.shadowoffsety = config.get("theme", "shadowoffsety")
      self.menuTipTextY = config.get("theme", "menu_tip_text_y")
      self.menuTipTextFont = config.get("theme", "menu_tip_text_font")
      self.menuTipTextScale = config.get("theme", "menu_tip_text_scale")
      self.menuTipTextColor = self.hexToColorResults(config.get("theme", "menu_tip_text_color"))
      self.menuTipTextScrollSpace = config.get("theme", "menu_tip_text_scroll_space")
      self.menuTipTextScrollMode = config.get("theme", "menu_tip_text_scroll_mode")
      self.menuTipTextDisplay = config.get("theme", "menu_tip_text_display")
      
      #Lobby
      self.controlActivateX = config.get("theme", "control_activate_x")
      self.controlActivateSelectX = config.get("theme", "control_activate_select_x")
      self.controlActivatePartX = config.get("theme", "control_activate_part_x")
      self.controlActivateY = config.get("theme", "control_activate_y")
      self.controlActivateScale = config.get("theme", "control_activate_scale")
      self.controlActivateSpace = config.get("theme", "control_activate_space")
      self.controlActivatePartSize = config.get("theme", "control_activate_part_size")
      self.controlActivateFont = config.get("theme", "control_activate_font")
      self.controlDescriptionX = config.get("theme", "control_description_x")
      self.controlDescriptionY = config.get("theme", "control_description_y")
      self.controlDescriptionScale = config.get("theme", "control_description_scale")
      self.controlDescriptionFont = config.get("theme", "control_description_font")
      self.controlCheckX = config.get("theme", "control_check_x")
      self.controlCheckY = config.get("theme", "control_check_y")
      self.controlCheckTextY = config.get("theme", "control_check_text_y")
      self.controlCheckPartMult = config.get("theme", "control_check_part_mult")
      self.controlCheckScale = config.get("theme", "control_check_scale")
      self.controlCheckSpace = config.get("theme", "control_check_space")
      self.controlCheckFont  = config.get("theme", "control_check_font")
      self.lobbyMode = config.get("theme", "lobby_mode")
      self.lobbyPreviewX = config.get("theme", "lobby_preview_x")
      self.lobbyPreviewY = config.get("theme", "lobby_preview_y")
      self.lobbyPreviewSpacing = config.get("theme", "lobby_preview_spacing")
      self.lobbyTitleX = config.get("theme", "lobby_title_x")
      self.lobbyTitleY = config.get("theme", "lobby_title_y")
      self.lobbyTitleCharacterX = config.get("theme", "lobby_title_character_x")
      self.lobbyTitleCharacterY = config.get("theme", "lobby_title_character_y")
      self.lobbyTitleScale = config.get("theme", "lobby_title_scale")
      self.lobbyTitleFont = config.get("theme", "lobby_title_font")
      self.lobbyAvatarX = config.get("theme", "lobby_avatar_x")
      self.lobbyAvatarY = config.get("theme", "lobby_avatar_y")
      self.lobbyAvatarScale = config.get("theme", "lobby_avatar_scale")
      self.lobbySelectX = config.get("theme", "lobby_select_x")
      self.lobbySelectY = config.get("theme", "lobby_select_y")
      self.lobbySelectImageX = config.get("theme", "lobby_select_image_x")
      self.lobbySelectImageY = config.get("theme", "lobby_select_image_y")
      self.lobbySelectScale = config.get("theme", "lobby_select_scale")
      self.lobbySelectSpace = config.get("theme", "lobby_select_space")
      self.lobbySelectFont = config.get("theme", "lobby_select_font")
      self.lobbySelectLength = config.get("theme", "lobby_select_length")
      self.lobbyTitleColor = self.hexToColor(config.get("theme", "lobby_title_color"))
      self.lobbyInfoColor = self.hexToColor(config.get("theme", "lobby_info_color"))
      self.lobbyFontColor = self.hexToColor(config.get("theme", "lobby_font_color"))
      self.lobbyPlayerColor = self.hexToColor(config.get("theme", "lobby_player_color"))
      self.lobbySelectColor = self.hexToColor(config.get("theme", "lobby_select_color"))
      self.lobbyDisableColor = self.hexToColor(config.get("theme", "lobby_disable_color"))
      self.characterCreateX = config.get("theme", "character_create_x")
      self.characterCreateY = config.get("theme", "character_create_y")
      self.characterCreateOptionX = config.get("theme", "character_create_option_x")
      self.characterCreateFontColor = self.hexToColor(config.get("theme", "character_create_font_color"))
      self.characterCreateSelectColor = self.hexToColor(config.get("theme", "character_create_select_color"))
      self.characterCreateHelpColor = self.hexToColor(config.get("theme", "character_create_help_color"))
      self.characterCreateHelpX = config.get("theme", "character_create_help_x")
      self.characterCreateHelpY = config.get("theme", "character_create_help_y")
      self.characterCreateHelpScale = config.get("theme", "character_create_help_scale")
      self.characterCreateOptionFont = config.get("theme", "character_create_option_font")
      self.characterCreateHelpFont = config.get("theme", "character_create_help_font")
      self.characterCreateScale = config.get("theme", "character_create_scale")
      self.characterCreateSpace = config.get("theme", "character_create_space")
      self.avatarSelectTextX = config.get("theme","avatar_select_text_x")
      self.avatarSelectTextY = config.get("theme","avatar_select_text_y")
      self.avatarSelectTextScale = config.get("theme","avatar_select_text_scale")
      self.avatarSelectFont = config.get("theme","avatar_select_font")
      self.avatarSelectAvX = config.get("theme","avatar_select_avatar_x")
      self.avatarSelectAvY = config.get("theme","avatar_select_avatar_y")
      self.avatarSelectWheelY = config.get("theme","avatar_select_wheel_y")
      
      #Vocal mode
      self.vocalMeterSize = config.get("theme", "vocal_meter_size")
      self.vocalMeterX = config.get("theme", "vocal_meter_x")
      self.vocalMeterY = config.get("theme", "vocal_meter_y")
      self.vocalMultX  = config.get("theme", "vocal_mult_x")
      self.vocalMultY  = config.get("theme", "vocal_mult_y")
      self.vocalPowerX = config.get("theme", "vocal_power_x")
      self.vocalPowerY = config.get("theme", "vocal_power_y")
      self.vocalFillupCenterX = config.get("theme", "vocal_fillup_center_x")
      self.vocalFillupCenterY = config.get("theme", "vocal_fillup_center_y")
      self.vocalFillupInRadius = config.get("theme", "vocal_fillup_in_radius")
      self.vocalFillupOutRadius = config.get("theme", "vocal_fillup_out_radius")
      self.vocalFillupFactor = config.get("theme", "vocal_fillup_factor")
      self.vocalFillupColor = config.get("theme", "vocal_fillup_color")
      self.vocalCircularFillup = config.get("theme", "vocal_circular_fillup")
      self.vocalLaneSize = config.get("theme", "vocal_lane_size")
      self.vocalGlowSize = config.get("theme", "vocal_glow_size")
      self.vocalGlowFade = config.get("theme", "vocal_glow_fade")
      self.vocalLaneColor = self.hexToColorResults(config.get("theme","vocal_lane_color"))
      self.vocalShadowColor = self.hexToColorResults(config.get("theme","vocal_shadow_color"))
      self.vocalGlowColor = self.hexToColorResults(config.get("theme","vocal_glow_color"))
      self.vocalLaneColorStar = self.hexToColorResults(config.get("theme","vocal_lane_color_star"))
      self.vocalShadowColorStar = self.hexToColorResults(config.get("theme","vocal_shadow_color_star"))
      self.vocalGlowColorStar = self.hexToColorResults(config.get("theme","vocal_glow_color_star"))
      
      #3D Note/Fret rendering system
      self.twoDnote = config.get("theme", "twoDnote")
      self.twoDkeys = config.get("theme", "twoDkeys")
      self.threeDspin = config.get("theme", "threeDspin")
      self.fret_press = config.get("theme", "fret_press")
      self.noterot = [config.get("theme", "noterot"+str(i+1)) for i in range(5)]
      self.keyrot  = [config.get("theme", "keyrot"+str(i+1)) for i in range(5)]
      self.drumnoterot = [config.get("theme", "drumnoterot"+str(i+1)) for i in range(5)]
      self.drumkeyrot = [config.get("theme", "drumkeyrot"+str(i+1)) for i in range(5)]
      self.notepos = [config.get("theme", "notepos"+str(i+1)) for i in range(5)]
      self.keypos  = [config.get("theme", "keypos"+str(i+1)) for i in range(5)]
      self.drumnotepos = [config.get("theme", "drumnotepos"+str(i+1)) for i in range(5)]
      self.drumkeypos = [config.get("theme", "drumkeypos"+str(i+1)) for i in range(5)]
      
      #In-game rendering
      self.rockmeter_score_colorVar = self.hexToColorResults(config.get("theme", "rockmeter_score_color"))
      self.ingame_stats_colorVar = self.hexToColorResults(config.get("theme", "ingame_stats_color"))
      self.hopoIndicatorX = config.get("theme", "hopo_indicator_x")
      self.hopoIndicatorY = config.get("theme", "hopo_indicator_y")  
      self.hopoIndicatorActiveColor = self.hexToColor(config.get("theme", "hopo_indicator_active_color"))
      self.hopoIndicatorInactiveColor = self.hexToColor(config.get("theme", "hopo_indicator_inactive_color"))
      self.markSolos = config.get("theme","mark_solo_sections")
      
      #Game results scene
      self.result_score = config.get("theme", "result_score").split(",")
      self.result_star = config.get("theme", "result_star").split(",")
      self.result_song = config.get("theme", "result_song").split(",")
      self.result_song_form = config.get("theme", "result_song_form")
      self.result_song_text = config.get("theme", "result_song_text").strip()
      self.result_stats_part = config.get("theme", "result_stats_part").split(",")
      self.result_stats_part_text = config.get("theme", "result_stats_part_text").strip()
      self.result_stats_name = config.get("theme", "result_stats_name").split(",")
      self.result_stats_diff = config.get("theme", "result_stats_diff").split(",")
      self.result_stats_diff_text = config.get("theme", "result_stats_diff_text").strip()
      self.result_stats_accuracy = config.get("theme", "result_stats_accuracy").split(",")
      self.result_stats_accuracy_text = config.get("theme", "result_stats_accuracy_text").strip()
      self.result_stats_streak = config.get("theme", "result_stats_streak").split(",")
      self.result_stats_streak_text = config.get("theme", "result_stats_streak_text").strip()
      self.result_stats_notes = config.get("theme", "result_stats_notes").split(",")
      self.result_stats_notes_text = config.get("theme", "result_stats_notes_text").strip()
      self.result_cheats_info = config.get("theme", "result_cheats_info").split(",")
      self.result_cheats_numbers = config.get("theme", "result_cheats_numbers").split(",")
      self.result_cheats_percent = config.get("theme", "result_cheats_percent").split(",")
      self.result_cheats_score   = config.get("theme", "result_cheats_score").split(",")
      self.result_cheats_color   = config.get("theme", "result_cheats_color")
      self.result_cheats_font    = config.get("theme", "result_cheats_font")
      self.result_high_score_font = config.get("theme", "result_high_score_font")
      self.result_menu_x         = config.get("theme", "result_menu_x")
      self.result_menu_y         = config.get("theme", "result_menu_y")
      self.result_star_type      = config.get("theme", "result_star_type")
      
      #Submenus
      allfiles = os.listdir(os.path.join(self.themePath,"menu"))
      self.submenuScale = {}
      self.submenuX = {}
      self.submenuY = {}
      self.submenuVSpace = {}
      listmenu = []
      for name in allfiles:
        if name.find("text") > -1:
          found = os.path.splitext(name)[0]
          if found == "maintext":
            continue
          Config.define("theme", found, str, None)
          self.submenuScale[found] = None
          self.submenuX[found] = None
          self.submenuY[found] = None
          self.submenuVSpace[found] = None
          listmenu.append(found)
      for i in listmenu:
        if i == "maintext":
          continue
        try:
          self.submenuX[i] = config.get("theme", i).split(",")[0].strip()
        except IndexError:
          self.submenuX[i] = None
        try:
          self.submenuY[i] = config.get("theme", i).split(",")[1].strip()
        except IndexError:
          self.submenuY[i] = None
        try:
          self.submenuScale[i] = config.get("theme", i).split(",")[2].strip()
        except IndexError:
          self.submenuScale[i] = None
        try:
          self.submenuVSpace[i] = config.get("theme", i).split(",")[3].strip()
        except IndexError:
          self.submenuVSpace[i] = None
    
    else:
      #Colors
      self.backgroundColor = (0,0,0)
      self.baseColor = (1,1,1)
      self.selectedColor = (1,.75,0)
      self.meshColor = (0,0,0)
      self.hopoColor = (0,.667,.667)
      self.spotColor = (1,1,1)
      self.keyColor = (.2,.2,.2)
      self.key2Color = (0,0,0)
      self.tracksColor = (1,1,.5)
      self.barsColor = (1,1,.5)
      self.glowColor = (-2,-2,-2)
      
      #Note Colors (this applies to frets and notes)
      self.noteColors = [(.133,1,.133),(1,.133,.133),(1,1,.133),(.2,.2,1),(1,.6,.3),(.8,.133,.8)]
      self.spNoteColor = (.3,.7,.9)
      self.killNoteColor = (0,0,0)
      self.use_fret_colors = False
      
      #Point of View
      self.povTargetX = None
      self.povTargetY = None
      self.povTargetZ = None
      self.povOriginX = None
      self.povOriginY = None
      self.povOriginZ = None
      
      #Loading phrases
      self.loadingPhrase = ["None"]
      self.resultsPhrase = ["None"]
      
      #Miscellany (aka Garbage no one cares about)
      self.crowdLoopDelay = None
      self.songInfoDisplayScale = .0020
      self.songInfoDisplayX = .05
      self.songInfoDisplayY = .05
      self.displayAllGreyStars = True
      self.smallMult = True
      self.jurgTextPos = [1,1,.00035]
      self.oBarHScale = .7
      self.oBar3dFill = False
      self.power_up_name = None
      
      #Continuous star fillup!
      self.starFillupCenterX = None
      self.starFillupCenterY = None
      self.starFillupInRadius = None
      self.starFillupOutRadius = None
      self.starFillupColor = None
      
      #Neck size, neck choose (yeah? you got a problem with that goruping?)
      self.neckWidth = 3.0
      self.neckLength = 9.0
      self.neck_prompt_x = .1
      self.neck_prompt_y = .05
      
      #Setlist
      self.songListDisplay = 1
      self.setlistguidebuttonsposX = .408
      self.setlistguidebuttonsposY = .0322
      self.setlistguidebuttonsscaleX = .29
      self.setlistguidebuttonsscaleY = .308
      self.setlistpreviewbuttonposX = .5
      self.setlistpreviewbuttonposY = .5
      self.setlistpreviewbuttonscaleX = .5
      self.setlistpreviewbuttonscaleY = .5
      self.versiontagposX = .5
      self.versiontagposY = .5
      self.songSelectSubmenuOffsetLines = 2
      self.songSelectSubmenuOffsetSpaces = 2
      self.songSelectSubmenuX = None
      self.songSelectSubmenuY = None
      self.song_cd_Xpos = 0.0
      self.song_listcd_cd_Xpos = .75
      self.song_listcd_cd_Ypos = .6
      self.song_listcd_score_Xpos = .6
      self.song_listcd_score_Ypos = .5
      self.songlist_score_colorVar = (.58,.76,.32)
      self.songlistcd_score_colorVar = (1,1,1)
      self.song_listcd_list_Xpos = .1
      self.song_cdscore_Xpos = .6
      self.song_list_Xpos = .15
      self.song_listscore_Xpos = .8
      self.career_title_colorVar = (0,0,0)
      self.song_name_text_colorVar = (1,1,1)
      self.song_name_selected_colorVar = (1,.75,0)
      self.artist_text_colorVar = (.25,.5,1)
      self.artist_selected_colorVar = (.25,.5,1)
      self.library_text_colorVar = (1,1,1)
      self.library_selected_colorVar = (1,.75,0)
      self.pause_text_colorVar = (1,1,1)
      self.pause_selected_colorVar = (1,.75,0)
      self.fail_completed_colorVar = (1,1,1)
      self.fail_text_colorVar = (1,1,1)
      self.fail_selected_colorVar = (1,.75,0)
      self.song_rb2_diff_colorVar = (1,.75,0)
      
      #pause menu and fail menu
      self.pause_bkg_pos = [.5,.5,1.0,1.0]
      self.pause_text_xPos = None
      self.pause_text_yPos = None
      self.opt_text_colorVar = (1,1,1)
      self.opt_selected_colorVar = (1,.75,0)
      self.opt_bkg_size = [.5,.5,1.0,1.0]
      self.opt_text_xPos = None
      self.opt_text_yPos = None
      self.fail_bkg_pos = [.5,.5,1.0,1.0]
      self.fail_text_xPos = None
      self.fail_text_yPos = None
      self.fail_songname_xPos = .5
      self.fail_songname_yPos = .35
      
      #main menu system
      self.menuX = None
      self.menuY = None
      self.menuRB = False
      self.loadingX = .5
      self.loadingY = .6
      self.loadingColor = (1,1,1)
      self.loadingFScale = .0015
      self.loadingRMargin = 1.0
      self.loadingLSpacing = 1.0
      self.main_menu_scaleVar = None
      self.main_menu_vspacingVar = None
      self.use_solo_submenu = None
      self.sub_menu_xVar = None
      self.sub_menu_yVar = None
      self.versiontag = False
      self.shadowoffsetx = .0022
      self.shadowoffsety = .0005
      self.menuTipTextY = .7
      self.menuTipTextFont = "font"
      self.menuTipTextScale = .002
      self.menuTipTextColor = None
      self.menuTipTextScrollSpace = .25
      self.menuTipTextScrollMode = 0
      self.menuTipTextDisplay = False
      
      self.characterCreateX = .25
      self.characterCreateY = .15
      self.characterCreateOptionX = .75
      self.characterCreateFontColor = (1,1,1)
      self.characterCreateSelectColor = (1,.75,0)
      self.characterCreateHelpColor = (1,1,1)
      self.characterCreateHelpX = .5
      self.characterCreateHelpY = .73
      self.characterCreateHelpScale = .0018
      self.characterCreateOptionFont = "font"
      self.characterCreateHelpFont = "loadingFont"
      self.characterCreateScale = .0018
      self.characterCreateSpace = .045
      self.avatarSelectTextX = .44
      self.avatarSelectTextY = .16
      self.avatarSelectTextScale = .0027
      self.avatarSelectFont = "font"
      self.avatarSelectAvX = .667
      self.avatarSelectAvY = .5
      self.avatarSelectWheelY = 0.0
      
      #Vocal mode
      self.vocalMeterSize = 45.000
      self.vocalMeterX = .25
      self.vocalMeterY = .8
      self.vocalMultX  = .28
      self.vocalMultY  = .8
      self.vocalPowerX = .5
      self.vocalPowerY = .8
      self.vocalFillupCenterX = 139
      self.vocalFillupCenterY = 151
      self.vocalFillupInRadius = 25
      self.vocalFillupOutRadius = 139
      self.vocalFillupFactor = 300.000
      self.vocalFillupColor = (.87,.87,.87)
      self.vocalCircularFillup = True
      self.vocalLaneSize = .002
      self.vocalGlowSize = .012
      self.vocalGlowFade = .6
      self.vocalLaneColor = (.6,1,.5)
      self.vocalShadowColor = (.8,1,.75)
      self.vocalGlowColor = (.2,1,0)
      self.vocalLaneColorStar = (1,1,.5)
      self.vocalShadowColorStar = (1,1,.75)
      self.vocalGlowColorStar = (1,1,0)
      
      #3D Note/Fret rendering system
      self.twoDnote = True
      self.twoDkeys = True
      self.threeDspin = True
      self.fret_press = True
      self.noterot = [0 for i in range(5)]
      self.keyrot  = [0 for i in range(5)]
      self.drumnoterot = [0 for i in range(5)]
      self.drumkeyrot = [0 for i in range(5)]
      self.notepos = [0 for i in range(5)]
      self.keypos  = [0 for i in range(5)]
      self.drumnotepos = [0 for i in range(5)]
      self.drumkeypos = [0 for i in range(5)]
      
      #In-game rendering
      self.rockmeter_score_colorVar = (1,1,1)
      self.ingame_stats_colorVar = (1,1,1)
      self.hopoIndicatorX = None
      self.hopoIndicatorY = None
      self.hopoIndicatorActiveColor = (1,1,1)
      self.hopoIndicatorInactiveColor = (.6,.6,.6)
      self.markSolos = 2
      
      #Game results scene
      self.result_score = [.5,.11,.0025,None,None]
      self.result_star = [.5,.4,.15,1.1]
      self.result_song = [.05,.045,.002,None,None]
      self.result_song_form = 0
      self.result_song_text = _("%s Finished!")
      self.result_stats_part = [.5,.64,0.002,None,None]
      self.result_stats_part_text = _("Part: %s")
      self.result_stats_name = [.5,.73,0.002,None,None]
      self.result_stats_diff = [.5,.55,.002,None,None]
      self.result_stats_diff_text = _("Difficulty: %s")
      self.result_stats_accuracy = [.5,.61,.002,None,None]
      self.result_stats_accuracy_text = _("Accuracy: %.1f%%")
      self.result_stats_streak = [.5,.58,.002,None,None]
      self.result_stats_streak_text = _("Longest Streak: %d")
      self.result_stats_notes = [.5,.52,.002,None,None]
      self.result_stats_notes_text = _("%s Notes Hit")
      self.result_cheats_info = [.5,.3,.002]
      self.result_cheats_numbers = [.5,.35,.0015]
      self.result_cheats_percent = [.45,.4,.0015]
      self.result_cheats_score   = [.75,.4,.0015]
      self.result_cheats_color   = (1,1,1)
      self.result_cheats_font    = "font"
      self.result_high_score_font = "font"
      self.result_menu_x         = .5
      self.result_menu_y         = .2
      self.result_star_type      = 0
      
      #Submenus
      self.submenuScale = {}
      self.submenuX = {}
      self.submenuY = {}
      self.submenuVSpace = {}
  
  def setSelectedColor(self, alpha = 1.0):
    glColor4f(*(self.selectedColor + (alpha,)))

  def setBaseColor(self, alpha = 1.0):
    glColor4f(*(self.baseColor + (alpha,)))
  
  def hexToColorResults(self, color):
    if isinstance(color, tuple):
      return color
    elif color is None:
      return self.baseColor
    color = color.strip()
    if color[0] == "#":
      color = color[1:]
      if len(color) == 3:
        return (int(color[0], 16) / 15.0, int(color[1], 16) / 15.0, int(color[2], 16) / 15.0)
      return (int(color[0:2], 16) / 255.0, int(color[2:4], 16) / 255.0, int(color[4:6], 16) / 255.0)
    return self.baseColor
  
  @staticmethod
  def hexToColor(color):
    if isinstance(color, tuple):
      return color
    elif color is None:
      return (0,0,0)
    if color[0] == "#":
      color = color[1:]
      if len(color) == 3:
        return (int(color[0], 16) / 15.0, int(color[1], 16) / 15.0, int(color[2], 16) / 15.0)
      elif len(color) == 4:
        return (int(color[0], 16) / 15.0, int(color[1], 16) / 15.0, int(color[2], 16) / 15.0, int(color[2], 16) / 15.0)
      return (int(color[0:2], 16) / 255.0, int(color[2:4], 16) / 255.0, int(color[4:6], 16) / 255.0)
    elif color.lower() == "off":
      return (-1, -1, -1)
    elif color.lower() == "fret":
      return (-2, -2, -2)
    return (0, 0, 0)
  
  def rgbToColor(self, color):
    retVal = []
    for c in color:
      if isinstance(c, int) and i > 1:
        retVal.append(float(c)/255.0)
    return tuple(retval)
  
  @staticmethod
  def colorToHex(color):
    if isinstance(color, str):
      return color
    return "#" + ("".join(["%02x" % int(c * 255) for c in color]))

  def packTupleKey(self, key, type = str):
    vals = key.split(',')
    if isinstance(type, list):
      retval = tuple(type[i](n.strip()) for i, n in enumerate(vals))
    else:
      retval = tuple(type(n.strip()) for n in vals)
    return retval
  
  def fadeScreen(self, v):
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_COLOR_MATERIAL)

    glBegin(GL_TRIANGLE_STRIP)
    glColor4f(0, 0, 0, .3 - v * .3)
    glVertex2f(0, 0)
    glColor4f(0, 0, 0, .3 - v * .3)
    glVertex2f(1, 0)
    glColor4f(0, 0, 0, .9 - v * .9)
    glVertex2f(0, 1)
    glColor4f(0, 0, 0, .9 - v * .9)
    glVertex2f(1, 1)
    glEnd()
  
  def loadThemeModule(self, moduleName):
    try:
      fp, pathname, description = imp.find_module(moduleName,[self.path])
      module = imp.load_module(moduleName, fp, pathname, description)
      if moduleName in ["CustomLobby", "ThemeLobby"]:
        return module.CustomLobby(self)
      elif moduleName in ["CustomSetlist", "Setlist"]:
        return module.CustomSetlist(self)
      elif moduleName in ["CustomParts", "ThemeParts"]:
        return module.CustomParts(self)
      else:
        return None
    except ImportError:
      if moduleName in ["CustomLobby", "ThemeLobby"]:
        return ThemeLobby(self)
      elif moduleName in ["CustomSetlist", "Setlist"]:
        return Setlist(self)
      elif moduleName in ["CustomParts", "ThemeParts"]:
        return ThemeParts(self)
      else:
        return None
  
  def run(self, ticks):
    pass

class ThemeLobby:
  def __init__(self, theme):
    self.theme = theme
  def run(self, ticks):
    pass
  def renderPanels(self, lobby):
    x = 0.04
    y = .1
    w, h = lobby.geometry
    font = lobby.fontDict['font']
    controlFont   = lobby.fontDict[self.theme.lobbyControlFont]
    panelNameFont = lobby.fontDict[self.theme.lobbyPanelNameFont]
    optionFont    = lobby.fontDict[self.theme.lobbyOptionFont]
    saveCharFont  = lobby.fontDict[self.theme.lobbySaveCharFont]
    wP = w*self.theme.lobbyPanelSize[0]
    hP = h*self.theme.lobbyPanelSize[1]
    for i in range(4):
      if i == lobby.keyControl:
        if lobby.img_keyboard:
          lobby.drawImage(lobby.img_keyboard, scale = (.1, -.1), coord = (wP*.8+w*x, hP*.95+h*y))
      j = lobby.panelOrder[i]
      if j in lobby.blockedPlayers:
        glColor3f(*self.theme.lobbyDisabledColor)
      else:
        glColor3f(*self.theme.lobbyHeaderColor)
      if self.theme.lobbyTitleText:
        lobby.fontDict[self.theme.lobbyTitleTextFont].render(self.theme.lobbyTitleText, self.theme.lobbyTitleTextPos, scale = self.theme.lobbyTitleTextScale, align = self.theme.lobbyTitleTextAlign)
      if self.theme.lobbySubtitleText:
        lobby.fontDict[self.theme.lobbySubtitleTextFont].render(self.theme.lobbySubtitleText, self.theme.lobbySubtitleTextPos, scale = self.theme.lobbySubtitleTextScale, align = self.theme.lobbySubtitleTextAlign)
      if lobby.img_panel:
        lobby.drawImage(lobby.img_panel, scale = (self.theme.lobbyPanelSize[0], -self.theme.lobbyPanelSize[1]), coord = (wP*.5+w*x,hP*.5+h*y), stretched = 3)
      controlFont.render(lobby.controls[j], (self.theme.lobbyPanelSize[0]*self.theme.lobbyControlPos[0]+x, self.theme.lobbyPanelSize[1]*self.theme.lobbyControlPos[1]+y), scale = self.theme.lobbyControlScale, align = self.theme.lobbyControlAlign, new = True)
      panelNameFont.render(lobby.options[lobby.selected[j]].lower(), (x, y), scale = self.theme.lobbyPanelNameScale, align = self.theme.lobbyPanelNameAlign, new = True)
      for l, k in enumerate(range(lobby.pos[j][0], lobby.pos[j][1]+1)):
        if k >= len(lobby.options):
          break
        if lobby.selected[j] == k and (j not in lobby.blockedPlayers or j in lobby.selectedPlayers):
          if lobby.img_selected:
            lobby.drawImage(lobby.img_selected, scale = (.5, -.5), coord = (wP*.5+w*x, hP*(.46*.75)+h*y-(h*.04*l)/.75))
          if lobby.avatars[k]:
            lobby.drawImage(lobby.avatars[k], scale = (lobby.avatarScale[k], -lobby.avatarScale[k]), coord = (wP*.5+w*x, hP*.7+h*y))
          elif k == 0 and lobby.img_newchar_av:
            lobby.drawImage(lobby.img_newchar_av, scale = (lobby.newCharAvScale, -lobby.newCharAvScale), coord = (wP*.5+w*x, hP*.7+h*y))
          elif lobby.img_default_av:
            lobby.drawImage(lobby.img_default_av, scale = (lobby.defaultAvScale, -lobby.defaultAvScale), coord = (wP*.5+w*x, hP*.7+h*y))
          glColor3f(*self.theme.lobbySelectedColor)
        elif k in lobby.blockedItems or j in lobby.blockedPlayers:
          glColor3f(*self.theme.lobbyDisabledColor)
        else:
          glColor3f(*self.theme.lobbyOptionColor)
        if k == 1:
          glColor3f(*self.theme.lobbySaveCharColor)
          saveCharFont.render(lobby.options[k], (self.theme.lobbyPanelSize[0]*self.theme.lobbyOptionPos[0]+x,self.theme.lobbyPanelSize[1]*self.theme.lobbyOptionPos[1]+y+self.theme.lobbyOptionSpace*l), scale = self.theme.lobbySaveCharScale, align = self.theme.lobbySaveCharAlign, new = True)
        else:
          optionFont.render(lobby.options[k], (self.theme.lobbyPanelSize[0]*self.theme.lobbyOptionPos[0]+x,self.theme.lobbyPanelSize[1]*self.theme.lobbyOptionPos[1]+y+self.theme.lobbyOptionSpace*l), scale = self.theme.lobbyOptionScale, align = self.theme.lobbyOptionAlign, new = True)
      x += self.theme.lobbyPanelSpacing

class ThemeParts:
  def __init__(self, theme):
    self.theme = theme
  def run(self, ticks):
    pass
  def renderPanels(self, dialog):
    x = 0.04
    y = .1
    w, h = dialog.geometry
    font = dialog.fontDict['font']
    wP = w*.2
    hP = h*.8
    for i in range(len(dialog.players)):
      r = 1
      if i == dialog.keyControl:
        if dialog.img_keyboard:
          r = 0
          dialog.drawImage(dialog.img_keyboard, scale = (.1, -.1), coord = (wP*.8+w*x, hP*.95+h*y))
      if dialog.img_panel:
        dialog.drawImage(dialog.img_panel, scale = (.2, -.8), coord = (wP*.5+w*x,hP*.5+h*y), stretched = 3)
      a = (i in dialog.readyPlayers) and .5 or 1
      glColor4f(1,1,1,a)
      font.render(dialog.players[i].name, (.2*.5+x, .3+y), scale = .0025, align = 1, new = True)
      font.render(dialog.players[i].name.lower(), (x, y), scale = .001, align = 0, new = True)
      if dialog.mode[i] == 0:
        for p in range(len(dialog.parts[i])):
          if dialog.selected[i] == p:
            if dialog.img_selected:
              dialog.drawImage(dialog.img_selected, scale = (.5, -.5), coord = (wP*.5+w*x, hP*(.46*.75)+h*y-(h*.04*p)/.75))
            glColor3f(1,0,r)
          else:
            glColor3f(r,1,1)
          font.render(str(dialog.parts[i][p]), (.2*.5+x,.8*.46+y+.04*p), scale = .001, align = 1, new = True)
      elif dialog.mode[i] == 1:
        for d in range(len(dialog.info.partDifficulties[dialog.players[i].part.id])):
          if dialog.selected[i] == d:
            if dialog.img_selected:
              dialog.drawImage(dialog.img_selected, scale = (.5, -.5), coord = (wP*.5+w*x, hP*(.46*.75)+h*y-(h*.04*d)/.75))
            glColor3f(1,0,r)
          else:
            glColor3f(r,1,1)
          font.render(str(dialog.info.partDifficulties[dialog.players[i].part.id][d]), (.2*.5+x,.8*.46+y+.04*d), scale = .001, align = 1, new = True)
        if i in dialog.readyPlayers:
          if dialog.img_ready:
            dialog.drawImage(dialog.img_ready, scale = (.5, -.5), coord = (wP*.5+w*x,hP*(.75*.46)+h*y))
      x += .24

class Setlist:
  def __init__(self, theme):
    self.theme = theme
    self.setlist_type = theme.songListDisplay
    if self.setlist_type is None:
      self.setlist_type = 1
    if self.setlist_type == 0: #CD mode
      self.setlistStyle = 0
      self.headerSkip = 0
      self.footerSkip = 0
      self.labelType = 1
      self.labelDistance = 2
      self.showMoreLabels = True
      self.texturedLabels = True
      self.itemsPerPage = 1
      self.showLockedSongs = False
      self.showSortTiers = True
      self.selectTiers = False
      self.itemSize = (0,.125)
    elif self.setlist_type == 1: #List mode
      self.setlistStyle = 1
      self.headerSkip = 2
      self.footerSkip = 1
      self.labelType = 0
      self.labelDistance = 0
      self.showMoreLabels = False
      self.texturedLabels = False
      self.itemsPerPage = 7
      self.showLockedSongs = False
      self.showSortTiers = True
      self.selectTiers = False
      self.itemSize = (0,.126)
    elif self.setlist_type == 2: #List/CD mode
      self.setlistStyle = 1
      self.headerSkip = 0
      self.footerSkip = 1
      self.labelType = 1
      self.labelDistance = 1
      self.showMoreLabels = False
      self.texturedLabels = True
      self.itemsPerPage = 8
      self.showLockedSongs = False
      self.showSortTiers = True
      self.selectTiers = False
      self.itemSize = (0,.125)
    else: #RB2 mode
      self.setlistStyle = 0
      self.headerSkip = 0
      self.footerSkip = 0
      self.labelType = 0
      self.labelDistance = 1
      self.showMoreLabels = False
      self.texturedLabels = False
      self.itemsPerPage = 12
      self.showLockedSongs = True
      self.showSortTiers = True
      self.selectTiers = False
      self.itemSize = (0,.07)

    self.career_title_color = self.theme.career_title_colorVar
    self.song_name_text_color = self.theme.song_name_text_colorVar
    self.song_name_selected_color = self.theme.song_name_selected_colorVar
    self.song_rb2_diff_color = self.theme.song_rb2_diff_colorVar
    self.artist_text_color = self.theme.artist_text_colorVar
    self.artist_selected_color = self.theme.artist_selected_colorVar
    self.library_text_color = self.theme.library_text_colorVar
    self.library_selected_color = self.theme.library_selected_colorVar
    self.songlist_score_color = self.theme.songlist_score_colorVar
    self.songlistcd_score_color = self.theme.songlistcd_score_colorVar

    self.song_cd_xpos = theme.song_cd_Xpos
    self.song_cdscore_xpos = theme.song_cdscore_Xpos
    self.song_list_xpos = theme.song_list_Xpos
    self.song_listscore_xpos = theme.song_listscore_Xpos
    self.song_listcd_list_xpos = theme.song_listcd_list_Xpos
    self.song_listcd_cd_xpos = theme.song_listcd_cd_Xpos
    self.song_listcd_cd_ypos = theme.song_listcd_cd_Ypos
    self.song_listcd_score_xpos = theme.song_listcd_score_Xpos
    self.song_listcd_score_ypos = theme.song_listcd_score_Ypos
  
  def run(self, ticks):
    pass
  
  def renderHeader(self, scene):
    pass
  
  def renderUnselectedItem(self, scene, i, n):
    w, h = scene.geometry
    font = scene.fontDict['songListFont']
    lfont = scene.fontDict['songListFont']
    sfont = scene.fontDict['shadowfont']
    if self.setlist_type == 0:
      return
    elif self.setlist_type == 1:
      if not scene.items:
        return
      item = scene.items[i]

      glColor4f(0,0,0,1)
      if isinstance(item, Song.SongInfo) or isinstance(item, Song.RandomSongInfo):
        c1,c2,c3 = self.song_name_text_color
        glColor3f(c1,c2,c3)
      elif isinstance(item, Song.LibraryInfo):
        c1,c2,c3 = self.library_text_color
        glColor3f(c1,c2,c3)
      elif isinstance(item, Song.TitleInfo) or isinstance(item, Song.SortTitleInfo):
        c1,c2,c3 = self.career_title_color
        glColor3f(c1,c2,c3)
          
      text = item.name
      
      if isinstance(item, Song.SongInfo) and item.getLocked(): #TODO: SongDB
        text = _("-- Locked --")
      
      if isinstance(item, Song.SongInfo): #MFH - add indentation when tier sorting
        if scene.tiersPresent:
          text = "    " + text
      
      if isinstance(item, Song.TitleInfo) or isinstance(item, Song.SortTitleInfo):
        text = string.upper(text)

      scale = lfont.scaleText(text, maxwidth = 0.440)

      lfont.render(text, (self.song_list_xpos, .0925*(n+1)-.0375), scale = scale)


      #MFH - Song list score / info display:
      if isinstance(item, Song.SongInfo) and not item.getLocked():
        scale = 0.0009
        text = scene.scoreDifficulty.text
        c1,c2,c3 = self.songlist_score_color
        glColor3f(c1,c2,c3)
        lfont.render(text, (self.song_listscore_xpos, .0925*(n+1)-.034), scale=scale, align = 2)
        if not item.frets == "":
          suffix = ", ("+item.frets+")"
        else:
          suffix = ""

        if not item.year == "":
          yeartag = ", "+item.year
        else:
          yeartag = ""


        scale = .0014
        c1,c2,c3 = self.artist_text_color
        glColor3f(c1,c2,c3)

        # evilynux - Force uppercase display for artist name
        text = string.upper(item.artist)+suffix+yeartag
        
        # evilynux - automatically scale artist name and year
        scale = lfont.scaleText(text, maxwidth = 0.440, scale = scale)
        if scale > .0014:
          scale = .0014

        lfont.render(text, (self.song_list_xpos+.05, .0925*(n+1)+.0125), scale=scale)

        score = _("Nil")
        stars = 0
        name = ""

        try:
          difficulties = item.partDifficulties[scene.scorePart.id]
        except KeyError:
          difficulties = []
        for d in difficulties:
          if d.id == scene.scoreDifficulty.id:
            scores = item.getHighscores(d, part = scene.scorePart)
            if scores:
              score, stars, name, scoreExt = scores[0]
              try:
                notesHit, notesTotal, noteStreak, modVersion, handicap, handicapLong, originalScore = scoreExt
              except ValueError:
                notesHit, notesTotal, noteStreak, modVersion, oldScores1, oldScores2 = scoreExt
                handicap = 0
                handicapLong = "None"
                originalScore = score
            else:
              score, stars, name = 0, 0, "---"
        
        if score == _("Nil") and scene.nilShowNextScore:   #MFH
          for d in difficulties:   #MFH - just take the first valid difficulty you can find and display it.
            scores = item.getHighscores(d, part = scene.scorePart)
            if scores:
              score, stars, name, scoreExt = scores[0]
              try:
                notesHit, notesTotal, noteStreak, modVersion, handicap, handicapLong, originalScore = scoreExt
              except ValueError:
                notesHit, notesTotal, noteStreak, modVersion, oldScores1, oldScores2 = scoreExt
                handicap = 0
                handicapLong = "None"
                originalScore = score
              break
            else:
              score, stars, name = 0, 0, "---"
          else:
            score, stars, name = _("Nil"), 0, "---"
            
        
        


        starx = self.song_listscore_xpos+.01
        stary = .0925*(n+1)-0.039
        starscale = 0.03
        stary = 1.0 - (stary / scene.fontScreenBottom)
        scene.drawStarScore(w, h, starx, stary - h/2, stars, starscale, horiz_spacing = 1.0, hqStar = True) #MFH

        scale = 0.0014
        # evilynux - score color
        c1,c2,c3 = self.songlist_score_color
        glColor3f(c1,c2,c3)
        # evilynux - hit% and note streak only if enabled
        if score is not _("Nil") and score > 0 and notesTotal != 0:
          text = "%.1f%% (%d)" % ((float(notesHit) / notesTotal) * 100.0, noteStreak)
          lfont.render(text, (self.song_listscore_xpos+.1, .0925*(n+1)-.015), scale=scale, align = 2)

        text = str(score)
        lfont.render(text, (self.song_listscore_xpos+.1, .0925*(n+1)+.0125), scale=scale*1.28, align = 2)
    
    elif self.setlist_type == 2: #old list/cd
      y = h*(.87-(.1*n))
      if not scene.items:
        return
      item = scene.items[i]
      if isinstance(item, Song.SongInfo) or isinstance(item, Song.RandomSongInfo):
        c1,c2,c3 = self.song_name_text_color
        glColor4f(c1,c2,c3,1)
      if isinstance(item, Song.LibraryInfo):
        c1,c2,c3 = self.library_text_color
        glColor4f(c1,c2,c3,1)
      if isinstance(item, Song.TitleInfo) or isinstance(item, Song.SortTitleInfo):
        c1,c2,c3 = self.career_title_color
        glColor4f(c1,c2,c3,1)
      text = item.name
      if isinstance(item, Song.SongInfo) and item.getLocked():
        text = _("-- Locked --")
      if isinstance(item, Song.SongInfo): #MFH - add indentation when tier sorting
        if scene.tiersPresent:
          text = "    " + text
      if isinstance(item, Song.TitleInfo) or isinstance(item, Song.SortTitleInfo):
        text = string.upper(text)
      scale = font.scaleText(text, maxwidth = 0.45)
      font.render(text, (self.song_listcd_list_xpos, .09*(n+1)), scale = scale)
      if isinstance(item, Song.SongInfo) and not item.getLocked():
        if not item.frets == "":
          suffix = ", ("+item.frets+")"
        else:
          suffix = ""
        
        if not item.year == "":
          yeartag = ", "+item.year
        else:
          yeartag = ""
        
        scale = .0014
        c1,c2,c3 = self.artist_text_color
        glColor4f(c1,c2,c3,1)

        text = string.upper(item.artist)+suffix+yeartag

        scale = font.scaleText(text, maxwidth = 0.4, scale = scale)
        font.render(text, (self.song_listcd_list_xpos + .05, .09*(n+1)+.05), scale=scale)
    elif self.setlist_type == 3: #old rb2
      font = scene.fontDict['songListFont']
      if not scene.items or scene.itemIcons is None:
        return
      item = scene.items[i]
      y = h*(.7825-(.0459*(n+1)))
      
      if scene.img_tier:
        imgwidth = scene.img_tier.width1()
        imgheight = scene.img_tier.height1()
        wfactor = 381.1/imgwidth
        hfactor = 24.000/imgheight
        if isinstance(item, Song.TitleInfo) or isinstance(item, Song.SortTitleInfo) and scene.img_tier:
          scene.drawImage(scene.img_tier, scale = (wfactor,-hfactor), coord = (w/1.587, h-((0.055*h)*(n+1))-(0.219*h)))

      icon = None
      if isinstance(item, Song.SongInfo):
        if item.icon != "":
          try:
            icon = scene.itemIcons[item.icon]
            imgwidth = icon.width1()
            wfactor = 23.000/imgwidth
            scene.drawImage(icon, scale = (wfactor,-wfactor), coord = (w/2.86, h-((0.055*h)*(n+1))-(0.219*h)))
          except KeyError:
            pass
      elif isinstance(item, Song.LibraryInfo):
        try:
          icon = scene.itemIcons["Library"]
          imgwidth = icon.width1()
          wfactor = 23.000/imgwidth
          scene.drawImage(icon, scale = (wfactor,-wfactor), coord = (w/2.86, h-((0.055*h)*(n+1))-(0.219*h)))
        except KeyError:
          pass
      elif isinstance(item, Song.RandomSongInfo):
        try:
          icon = scene.itemIcons["Random"]
          imgwidth = icon.width1()
          wfactor = 23.000/imgwidth
          scene.drawImage(icon, scale = (wfactor,-wfactor), coord = (w/2.86, h-((0.055*h)*(n+1))-(0.219*h)))
        except KeyError:
          pass
      
      if isinstance(item, Song.SongInfo) or isinstance(item, Song.LibraryInfo):
        c1,c2,c3 = self.song_name_text_color
        glColor4f(c1,c2,c3,1)
      elif isinstance(item, Song.TitleInfo) or isinstance(item, Song.SortTitleInfo):
        c1,c2,c3 = self.career_title_color
        glColor4f(c1,c2,c3,1)
      elif isinstance(item, Song.RandomSongInfo):
        c1,c2,c3 = self.song_name_text_color
        glColor4f(c1,c2,c3,1)
      
      text = item.name
      
      
      if isinstance(item, Song.SongInfo) and item.getLocked():
        text = _("-- Locked --")
        
      if isinstance(item, Song.SongInfo): #MFH - add indentation when tier sorting
        if scene.tiersPresent or icon:
          text = "    " + text
        

      # evilynux - Force uppercase display for Career titles
      maxwidth = .55
        
      if isinstance(item, Song.TitleInfo) or isinstance(item, Song.SortTitleInfo):
        text = string.upper(text)
        
      scale = .0015
      wt, ht = font.getStringSize(text, scale = scale)

      while wt > maxwidth:
        tlength = len(text) - 4
        text = text[:tlength] + "..."
        wt, ht = font.getStringSize(text, scale = scale)
        if wt < .45:
          break
        
        
      font.render(text, (.35, .0413*(n+1)+.15), scale = scale)

      if isinstance(item, Song.SongInfo):
        if not item.getLocked():
          try:
            difficulties = item.partDifficulties[scene.scorePart.id]
          except KeyError:
            difficulties = []
          for d in difficulties:
            if d.id == scene.scoreDifficulty.id:
              scores = item.getHighscores(d, part = scene.scorePart)
              if scores:
                score, stars, name, scoreExt = scores[0]
                try:
                  notesHit, notesTotal, noteStreak, modVersion, handicap, handicapLong, originalScore = scoreExt
                except ValueError:
                  notesHit, notesTotal, noteStreak, modVersion, oldScores1, oldScores2 = scoreExt
                  handicap = 0
                  handicapLong = "None"
                  originalScore = score
                break
              else:
                score, stars, name = 0, 0, "---"
          else:
            score, stars, name = _("Nil"), 0, "---"
          
          if score == _("Nil") and scene.nilShowNextScore:   #MFH
            for d in difficulties:   #MFH - just take the first valid difficulty you can find and display it.
              scores = item.getHighscores(d, part = scene.scorePart)
              if scores:
                score, stars, name, scoreExt = scores[0]
                try:
                  notesHit, notesTotal, noteStreak, modVersion, handicap, handicapLong, originalScore = scoreExt
                except ValueError:
                  notesHit, notesTotal, noteStreak, modVersion, oldScores1, oldScores2 = scoreExt
                  handicap = 0
                  handicapLong = "None"
                  originalScore = score
                break
              else:
                score, stars, name = 0, 0, "---"
            else:
              score, stars, name = _("Nil"), 0, "---"

          #evilynux - hit% and note streak if enabled
          scale = 0.0009
          if score is not _("Nil") and score > 0 and notesTotal != 0:
            text = "%.1f%% (%d)" % ((float(notesHit) / notesTotal) * 100.0, noteStreak)
            font.render(text, (.92, .0413*(n+1)+.163), scale=scale, align = 2)
                
          text = str(score)
          
          font.render(text, (.92, .0413*(n+1)+.15), scale=scale, align = 2)

  def renderSelectedItem(self, scene, n):
    w, h = scene.geometry
    font = scene.fontDict['songListFont']
    lfont = scene.fontDict['songListFont']
    sfont = scene.fontDict['shadowfont']
    item = scene.selectedItem
    if not item:
      return
    if isinstance(item, Song.BlankSpaceInfo):
      return
    if self.setlist_type == 0:
      return
    elif self.setlist_type == 1:
      y = h*(.88-(.125*n))
      if scene.img_item_select:
        wfactor = scene.img_item_select.widthf(pixelw = 635.000)
        scene.drawImage(scene.img_item_select, scale = (wfactor,-wfactor), coord = (w/2.1, y))
      glColor4f(0,0,0,1)
      if isinstance(item, Song.SongInfo) or isinstance(item, Song.RandomSongInfo):
        c1,c2,c3 = self.song_name_selected_color
        glColor3f(c1,c2,c3)
      elif isinstance(item, Song.LibraryInfo):
        c1,c2,c3 = self.library_selected_color
        glColor3f(c1,c2,c3)
      elif isinstance(item, Song.TitleInfo) or isinstance(item, Song.SortTitleInfo):
        c1,c2,c3 = self.career_title_color
        glColor3f(c1,c2,c3)
          
      text = item.name
      
      if isinstance(item, Song.SongInfo) and item.getLocked(): #TODO: SongDB
        text = _("-- Locked --")
      
      if isinstance(item, Song.SongInfo): #MFH - add indentation when tier sorting
        if scene.tiersPresent:
          text = "    " + text
      
      if isinstance(item, Song.TitleInfo) or isinstance(item, Song.SortTitleInfo):
        text = string.upper(text)

      scale = sfont.scaleText(text, maxwidth = 0.440)

      sfont.render(text, (self.song_list_xpos, .0925*(n+1)-.0375), scale = scale)


      #MFH - Song list score / info display:
      if isinstance(item, Song.SongInfo) and not item.getLocked():
        scale = 0.0009
        text = scene.scoreDifficulty.text
        c1,c2,c3 = self.songlist_score_color
        glColor3f(c1,c2,c3)
        lfont.render(text, (self.song_listscore_xpos, .0925*(n+1)-.034), scale=scale, align = 2)
        if not item.frets == "":
          suffix = ", ("+item.frets+")"
        else:
          suffix = ""

        if not item.year == "":
          yeartag = ", "+item.year
        else:
          yeartag = ""


        scale = .0014
        c1,c2,c3 = self.artist_selected_color
        glColor3f(c1,c2,c3)

        # evilynux - Force uppercase display for artist name
        text = string.upper(item.artist)+suffix+yeartag
        
        # evilynux - automatically scale artist name and year
        scale = lfont.scaleText(text, maxwidth = 0.440, scale = scale)
        if scale > .0014:
          scale = .0014

        lfont.render(text, (self.song_list_xpos+.05, .0925*(n+1)+.0125), scale=scale)

        score = _("Nil")
        stars = 0
        name = ""

        try:
          difficulties = item.partDifficulties[scene.scorePart.id]
        except KeyError:
          difficulties = []
        for d in difficulties:
          if d.id == scene.scoreDifficulty.id:
            scores = item.getHighscores(d, part = scene.scorePart)
            if scores:
              score, stars, name, scoreExt = scores[0]
              try:
                notesHit, notesTotal, noteStreak, modVersion, handicap, handicapLong, originalScore = scoreExt
              except ValueError:
                notesHit, notesTotal, noteStreak, modVersion, oldScores1, oldScores2 = scoreExt
                handicap = 0
                handicapLong = "None"
                originalScore = score
            else:
              score, stars, name = 0, 0, "---"
        
        if score == _("Nil") and scene.nilShowNextScore:   #MFH
          for d in difficulties:   #MFH - just take the first valid difficulty you can find and display it.
            scores = item.getHighscores(d, part = scene.scorePart)
            if scores:
              score, stars, name, scoreExt = scores[0]
              try:
                notesHit, notesTotal, noteStreak, modVersion, handicap, handicapLong, originalScore = scoreExt
              except ValueError:
                notesHit, notesTotal, noteStreak, modVersion, oldScores1, oldScores2 = scoreExt
                handicap = 0
                handicapLong = "None"
                originalScore = score
              break
            else:
              score, stars, name = 0, 0, "---"
          else:
            score, stars, name = _("Nil"), 0, "---"
            
        starx = self.song_listscore_xpos+.01
        stary = .0925*(n+1)-0.039
        starscale = 0.03
        stary = 1.0 - (stary / scene.fontScreenBottom)
        scene.drawStarScore(w, h, starx, stary - h/2, stars, starscale, horiz_spacing = 1.0, hqStar = True) #MFH

        scale = 0.0014
        # evilynux - score color
        c1,c2,c3 = self.songlist_score_color
        glColor3f(c1,c2,c3)
        # evilynux - hit% and note streak only if enabled
        if score is not _("Nil") and score > 0 and notesTotal != 0:
          text = "%.1f%% (%d)" % ((float(notesHit) / notesTotal) * 100.0, noteStreak)
          lfont.render(text, (self.song_listscore_xpos+.1, .0925*(n+1)-.015), scale=scale, align = 2)

        text = str(score)
        lfont.render(text, (self.song_listscore_xpos+.1, .0925*(n+1)+.0125), scale=scale*1.28, align = 2)
    elif self.setlist_type == 2:
      y = h*(.87-(.1*n))
      glColor4f(1,1,1,1)
      if scene.img_selected:
        imgwidth = scene.img_selected.width1()
        scene.drawImage(scene.img_selected, scale = (1, -1), coord = (self.song_listcd_list_xpos * w + (imgwidth*.64/2), y*1.2-h*.215))
      text = scene.library
      font.render(text, (.05, .01))
      if scene.songLoader:
        font.render(_("Loading Preview..."), (.05, .7), scale = 0.001)
      
      if isinstance(item, Song.SongInfo):
        c1,c2,c3 = self.song_name_selected_color
        glColor4f(c1,c2,c3,1)
        if item.getLocked():
          text = item.getUnlockText()
        elif scene.careerMode and not item.completed:
          text = _("Play To Advance")
        elif scene.practiceMode:
          text = _("Practice")
        elif item.count:
          count = int(item.count)
          if count == 1: 
            text = _("Played Once")
          else:
            text = _("Played %d times.") % count
        else:
          text = _("Quickplay")
      elif isinstance(item, Song.LibraryInfo):
        c1,c2,c3 = self.library_selected_color
        glColor4f(c1,c2,c3,1)
        if item.songCount == 1:
          text = _("There Is 1 Song In This Setlist.")
        elif item.songCount > 1:
          text = _("There Are %d Songs In This Setlist.") % (item.songCount)
        else:
          text = ""
      elif isinstance(item, Song.TitleInfo) or isinstance(item, Song.SortTitleInfo):
        text = _("Tier")
        c1,c2,c3 = self.career_title_color
        glColor4f(c1,c2,c3,1)
      elif isinstance(item, Song.RandomSongInfo):
        text = _("Random Song")
        c1,c2,c3 = self.song_name_selected_color
        glColor4f(c1,c2,c3,1)
      
      font.render(text, (self.song_listcd_score_xpos, .085), scale = 0.0012)
      
      if isinstance(item, Song.SongInfo) or isinstance(item, Song.RandomSongInfo):
        c1,c2,c3 = self.song_name_selected_color
        glColor4f(c1,c2,c3,1)
      elif isinstance(item, Song.LibraryInfo):
        c1,c2,c3 = self.library_selected_color
        glColor4f(c1,c2,c3,1)
      elif isinstance(item, Song.TitleInfo) or isinstance(item, Song.SortTitleInfo):
        c1,c2,c3 = self.career_title_color
        glColor4f(c1,c2,c3,1)
      text = item.name
      if isinstance(item, Song.SongInfo) and item.getLocked():
        text = _("-- Locked --")
        
      if isinstance(item, Song.SongInfo): #MFH - add indentation when tier sorting
        if scene.tiersPresent:
          text = "    " + text

      elif isinstance(item, Song.TitleInfo) or isinstance(item, Song.SortTitleInfo):
        text = string.upper(text)
        
      scale = font.scaleText(text, maxwidth = 0.45)
      font.render(text, (self.song_listcd_list_xpos, .09*(n+1)), scale = scale)
      
      if isinstance(item, Song.SongInfo) and not item.getLocked():
        if not item.frets == "":
          suffix = ", ("+item.frets+")"
        else:
          suffix = ""
        
        if not item.year == "":
          yeartag = ", "+item.year
        else:
          yeartag = ""
        
        scale = .0014
        c1,c2,c3 = self.artist_selected_color
        glColor4f(c1,c2,c3,1)
        text = string.upper(item.artist)+suffix+yeartag

        scale = font.scaleText(text, maxwidth = 0.4, scale = scale)
        font.render(text, (self.song_listcd_list_xpos + .05, .09*(n+1)+.05), scale=scale)
    
    elif self.setlist_type == 3:
      y = h*(.7825-(.0459*(n)))
      
      if scene.img_tier:
        imgwidth = scene.img_tier.width1()
        imgheight = scene.img_tier.height1()
        wfactor = 381.1/imgwidth
        hfactor = 24.000/imgheight
        if isinstance(item, Song.TitleInfo) or isinstance(item, Song.SortTitleInfo):
          scene.drawImage(scene.img_tier, scale = (wfactor,-hfactor), coord = (w/1.587, h-((0.055*h)*(n+1))-(0.219*h)))
      
      if scene.img_selected:
        imgwidth = scene.img_selected.width1()
        imgheight = scene.img_selected.height1()
        wfactor = 381.5/imgwidth
        hfactor = 36.000/imgheight

        scene.drawImage(scene.img_selected, scale = (wfactor,-hfactor), coord = (w/1.587, y*1.2-h*.213))
      
      
      icon = None
      if isinstance(item, Song.SongInfo):
        if item.icon != "":
          try:
            icon = scene.itemIcons[item.icon]
            imgwidth = icon.width1()
            wfactor = 23.000/imgwidth
            scene.drawImage(icon, scale = (wfactor,-wfactor), coord = (w/2.86, h-((0.055*h)*(n+1))-(0.219*h)))
          except KeyError:
            pass
        
        c1,c2,c3 = self.song_name_selected_color
        glColor3f(c1,c2,c3)
        if item.getLocked():
          text = item.getUnlockText()
        elif scene.careerMode and not item.completed:
          text = _("Play To Advance")
        elif scene.practiceMode:
          text = _("Practice")
        elif item.count:
          count = int(item.count)
          if count == 1: 
            text = _("Played Once")
          else:
            text = _("Played %d times.") % count
        else:
          text = _("Quickplay")
      elif isinstance(item, Song.LibraryInfo):
        try:
          icon = scene.itemIcons["Library"]
          imgwidth = icon.width1()
          wfactor = 23.000/imgwidth
          scene.drawImage(icon, scale = (wfactor,-wfactor), coord = (w/2.86, h-((0.055*h)*(n+1))-(0.219*h)))
        except KeyError:
          pass
        c1,c2,c3 = self.library_selected_color
        glColor3f(c1,c2,c3)
        if item.songCount == 1:
          text = _("There Is 1 Song In This Setlist.")
        elif item.songCount > 1:
          text = _("There Are %d Songs In This Setlist.") % (item.songCount)
        else:
          text = ""
      elif isinstance(item, Song.TitleInfo) or isinstance(item, Song.SortTitleInfo):
        text = _("Tier")
        c1,c2,c3 = self.career_title_color
        glColor3f(c1,c2,c3)
      elif isinstance(item, Song.RandomSongInfo):
        try:
          icon = scene.itemIcons["Random"]
          imgwidth = icon.width1()
          wfactor = 23.000/imgwidth
          scene.drawImage(icon, scale = (wfactor,-wfactor), coord = (w/2.86, h-((0.055*h)*(n+1))-(0.219*h)))
        except KeyError:
          pass
        text = _("Random Song")
        c1,c2,c3 = self.career_title_color
        glColor3f(c1,c2,c3)
      
      font.render(text, (0.92, .13), scale = 0.0012, align = 2)
      
      maxwidth = .45
      if isinstance(item, Song.SongInfo) or isinstance(item, Song.LibraryInfo) or isinstance(item, Song.RandomSongInfo):
        c1,c2,c3 = self.song_name_selected_color
        glColor4f(c1,c2,c3,1)
      if isinstance(item, Song.TitleInfo) or isinstance(item, Song.SortTitleInfo):
        c1,c2,c3 = self.career_title_color
        glColor4f(c1,c2,c3,1)
      
      text = item.name
      
      if isinstance(item, Song.SongInfo) and item.getLocked():
        text = _("-- Locked --")
        
      if isinstance(item, Song.SongInfo): #MFH - add indentation when tier sorting
        if scene.tiersPresent or icon:
          text = "    " + text
        

      # evilynux - Force uppercase display for Career titles
      if isinstance(item, Song.TitleInfo) or isinstance(item, Song.SortTitleInfo):
        maxwidth = .55
        text = string.upper(text)
        
      scale = .0015
      wt, ht = font.getStringSize(text, scale = scale)

      while wt > maxwidth:
        tlength = len(text) - 4
        text = text[:tlength] + "..."
        wt, ht = font.getStringSize(text, scale = scale)
        if wt < .45:
          break
        
        
      font.render(text, (.35, .0413*(n+1)+.15), scale = scale) #add theme option for song_listCD_xpos

      if isinstance(item, Song.SongInfo):
        if not item.getLocked():
          try:
            difficulties = item.partDifficulties[scene.scorePart.id]
          except KeyError:
            difficulties = []
          for d in difficulties:
            if d.id == scene.scoreDifficulty.id:
              scores = item.getHighscores(d, part = scene.scorePart)
              if scores:
                score, stars, name, scoreExt = scores[0]
                try:
                  notesHit, notesTotal, noteStreak, modVersion, handicap, handicapLong, originalScore = scoreExt
                except ValueError:
                  notesHit, notesTotal, noteStreak, modVersion, oldScores1, oldScores2 = scoreExt
                  handicap = 0
                  handicapLong = "None"
                  originalScore = score
                break
              else:
                score, stars, name = 0, 0, "---"
          else:
            score, stars, name = _("Nil"), 0, "---"
          if score == _("Nil") and scene.nilShowNextScore:   #MFH
            for d in difficulties:   #MFH - just take the first valid difficulty you can find and display it.
              scores = item.getHighscores(d, part = scene.scorePart)
              if scores:
                score, stars, name, scoreExt = scores[0]
                try:
                  notesHit, notesTotal, noteStreak, modVersion, handicap, handicapLong, originalScore = scoreExt
                except ValueError:
                  notesHit, notesTotal, noteStreak, modVersion, oldScores1, oldScores2 = scoreExt
                  handicap = 0
                  handicapLong = "None"
                  originalScore = score
                break
              else:
                score, stars, name = 0, 0, "---"
            else:
              score, stars, name = _("Nil"), 0, "---"

          scale = 0.0009
          if score is not _("Nil") and score > 0 and notesTotal != 0:
            text = "%.1f%% (%d)" % ((float(notesHit) / notesTotal) * 100.0, noteStreak)
            w, h = font.getStringSize(text, scale=scale)
            font.render(text, (.92, .0413*(n+1)+.163), scale=scale, align = 2)
          
          text = str(score)
          
          font.render(text, (.92, .0413*(n+1)+.15), scale=scale, align = 2)

  def renderItem(self, scene, color, label):
    if not scene.itemMesh:
      return
    if color:
      glColor3f(*color)
    glEnable(GL_COLOR_MATERIAL)
    if self.setlist_type == 2:
      glRotate(90, 0, 0, 1)
      glRotate(((scene.time - scene.lastTime) * 2 % 360) - 90, 1, 0, 0)
    scene.itemMesh.render("Mesh_001")
    glColor3f(.1, .1, .1)
    scene.itemMesh.render("Mesh")
    if label and scene.label:
      glEnable(GL_TEXTURE_2D)
      label.bind()
      glColor3f(1, 1, 1)
      glMatrixMode(GL_TEXTURE)
      glScalef(1, -1, 1)
      glMatrixMode(GL_MODELVIEW)
      scene.label.render("Mesh_001")
      glMatrixMode(GL_TEXTURE)
      glLoadIdentity()
      glMatrixMode(GL_MODELVIEW)
      glDisable(GL_TEXTURE_2D)
      if shaders.enable("cd"):
        scene.itemMesh.render("Mesh_001")
        shaders.disable()

  def renderLibrary(self, scene, color, label):
    if not scene.libraryMesh:
      return
    if color:
      glColor3f(*color)
    
    glEnable(GL_NORMALIZE)
    glEnable(GL_COLOR_MATERIAL)
    if self.setlist_type == 2:
      glRotate(-180, 0, 1, 0)
      glRotate(-90, 0, 0, 1)
      glRotate(((scene.time - scene.lastTime) * 4 % 360) - 90, 1, 0, 0)
    scene.libraryMesh.render("Mesh_001")
    glColor3f(.1, .1, .1)
    scene.libraryMesh.render("Mesh")

    # Draw the label if there is one
    if label and scene.libraryLabel:
      glEnable(GL_TEXTURE_2D)
      label.bind()
      glColor3f(1, 1, 1)
      glMatrixMode(GL_TEXTURE)
      glScalef(1, -1, 1)
      glMatrixMode(GL_MODELVIEW)
      scene.libraryLabel.render()
      glMatrixMode(GL_TEXTURE)
      glLoadIdentity()
      glMatrixMode(GL_MODELVIEW)
      glDisable(GL_TEXTURE_2D)
    glDisable(GL_NORMALIZE)
    
  def renderTitle(self, scene, color, label):
    if not scene.tierMesh:
      return

    if color:
      glColor3f(*color)

    glEnable(GL_NORMALIZE)
    glEnable(GL_COLOR_MATERIAL)
    scene.tierMesh.render("Mesh_001")
    glColor3f(.1, .1, .1)
    scene.tierMesh.render("Mesh")

    # Draw the label if there is one
    if label:
      glEnable(GL_TEXTURE_2D)
      label.bind()
      glColor3f(1, 1, 1)
      glMatrixMode(GL_TEXTURE)
      glScalef(1, -1, 1)
      glMatrixMode(GL_MODELVIEW)
      scene.libraryLabel.render()
      glMatrixMode(GL_TEXTURE)
      glLoadIdentity()
      glMatrixMode(GL_MODELVIEW)
      glDisable(GL_TEXTURE_2D)
    glDisable(GL_NORMALIZE)
    
  def renderRandom(self, scene, color, label):
    if not scene.itemMesh:
      return

    if color:
      glColor3f(*color)

    glEnable(GL_NORMALIZE)
    glEnable(GL_COLOR_MATERIAL)
    scene.itemMesh.render("Mesh_001")
    glColor3f(.1, .1, .1)
    scene.itemMesh.render("Mesh")

    # Draw the label if there is one
    if label:
      glEnable(GL_TEXTURE_2D)
      label.bind()
      glColor3f(1, 1, 1)
      glMatrixMode(GL_TEXTURE)
      glScalef(1, -1, 1)
      glMatrixMode(GL_MODELVIEW)
      scene.libraryLabel.render()
      glMatrixMode(GL_TEXTURE)
      glLoadIdentity()
      glMatrixMode(GL_MODELVIEW)
      glDisable(GL_TEXTURE_2D)
    glDisable(GL_NORMALIZE)

  def renderAlbumArt(self, scene):
    if not scene.itemLabels:
      return
    if self.setlist_type == 0:
      w, h = scene.geometry
      try:
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluPerspective(60, scene.aspectRatio, 0.1, 1000)
        
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        glEnable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)
        glDepthMask(1)
        
        offset = 0
        if scene.time < 40:
          offset = 10*((40 - scene.time)/40.0)**4
        scene.camera.origin = (-10 + offset, -scene.cameraOffset, 4   - self.song_cd_xpos + offset)
        scene.camera.target = (  0 + offset, -scene.cameraOffset, 2.5 - self.song_cd_xpos + offset)
        scene.camera.apply()
        
        y = 0.0
        for i, item in enumerate(scene.items):
          c = math.sin(scene.itemRenderAngles[i] * math.pi / 180)
          
          if isinstance(item, Song.SongInfo):
            h = c * 4.0 + (1 - c) * .8
          elif isinstance(item, Song.LibraryInfo):
            h = c * 4.0 + (1 - c) * 1.2
          elif isinstance(item, Song.TitleInfo) or isinstance(item, Song.SortTitleInfo):
            h = c * 4.0 + (1 - c) * 2.4
          elif isinstance(item, Song.RandomSongInfo):
            h = c * 4.0 + (1 - c) * .8
          else:
            continue
          
          d = (y + h * .5 + scene.camera.origin[1]) / (4 * (scene.camera.target[2] - scene.camera.origin[2]))
          if i == scene.selectedIndex:
            scene.selectedOffset = y + h / 2
            self.theme.setSelectedColor()
          else:
            self.theme.setBaseColor()
          
          glTranslatef(0, -h / 2, 0)
          glPushMatrix()
          if abs(d) < 1.2:
            label = scene.itemLabels[i]
            if label == "Random":
              label = scene.img_random_label
            if label == False:
              label = scene.img_empty_label
            if isinstance(item, Song.SongInfo):
              glRotate(scene.itemRenderAngles[i], 0, 0, 1)
              self.renderItem(scene, item.cassetteColor, label)
            elif isinstance(item, Song.LibraryInfo):
              #myfingershurt: cd cases are backwards
              glRotate(-scene.itemRenderAngles[i], 0, 1, 0)    #spin 90 degrees around y axis
              glRotate(-scene.itemRenderAngles[i], 0, 1, 0)    #spin 90 degrees around y axis again, now case is corrected
              glRotate(-scene.itemRenderAngles[i], 0, 0, 1)    #bring cd case up for viewing
              if i == scene.selectedIndex:
                glRotate(((scene.time - scene.lastTime) * 4 % 360) - 90, 1, 0, 0)
              self.renderLibrary(scene, item.color, label)
            elif isinstance(item, Song.TitleInfo):
              #myfingershurt: cd cases are backwards
              glRotate(-scene.itemRenderAngles[i], 0, 0.5, 0)    #spin 90 degrees around y axis
              glRotate(-scene.itemRenderAngles[i], 0, 0.5, 0)    #spin 90 degrees around y axis again, now case is corrected
              glRotate(-scene.itemRenderAngles[i], 0, 0, 0.5)    #bring cd case up for viewing
              if i == scene.selectedIndex:
                glRotate(((scene.time - scene.lastTime) * 4 % 360) - 90, 1, 0, 0)
              self.renderTitle(scene, item.color, label)
            elif isinstance(item, Song.RandomSongInfo):
              #myfingershurt: cd cases are backwards
              glRotate(scene.itemRenderAngles[i], 0, 0, 1)
              self.renderRandom(scene, item.color, label)
          glPopMatrix()
          
          glTranslatef(0, -h/2, 0)
          y+= h
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)
        glDepthMask(0)
      finally:
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        
    elif self.setlist_type == 1:
      return
    elif self.setlist_type == 2:
      w, h = scene.geometry
      try:
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        
        glLoadIdentity()
        gluPerspective(60, scene.aspectRatio, 0.1, 1000)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        glEnable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)
        glDepthMask(1)
        
        offset = 0
        if scene.time < 40:
          offset = 10*((40 - scene.time)/40.0)**4
        scene.camera.origin = (-9,(5.196/scene.aspectRatio) - (5.196*2/scene.aspectRatio)*self.song_listcd_cd_ypos,(5.196*scene.aspectRatio)-(5.196*2*scene.aspectRatio)*self.song_listcd_cd_xpos)
        scene.camera.target = ( 0,(5.196/scene.aspectRatio) - (5.196*2/scene.aspectRatio)*self.song_listcd_cd_ypos,(5.196*scene.aspectRatio)-(5.196*2*scene.aspectRatio)*self.song_listcd_cd_xpos)
        scene.camera.apply()
            
        y = 0.0

        

        glPushMatrix()
        item = scene.selectedItem
        i = scene.selectedIndex
        label = scene.itemLabels[i]
        if label == "Random":
          label = scene.img_random_label
        if not label:
          label = scene.img_empty_label
        if isinstance(item, Song.SongInfo):
          if scene.labelType:
            self.renderItem(scene, item.cassetteColor, label)
          else:
            self.renderLibrary(scene, item.cassetteColor, label)
        elif isinstance(item, Song.LibraryInfo):
          self.renderLibrary(scene, item.color, label)
        elif isinstance(item, Song.RandomSongInfo):
          if scene.labelType:
            self.renderItem(scene, None, label)
          else:
            self.renderLibrary(scene, None, label)
        glPopMatrix()
        
        glTranslatef(0, -h / 2, 0)
        y += h

        glDisable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)
        glDepthMask(0)
      finally:
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
      
      #resets the rendering
      glMatrixMode(GL_PROJECTION)
      glLoadIdentity()
      viewport = glGetIntegerv(GL_VIEWPORT)
      w = viewport[2] - viewport[0]
      h = viewport[3] - viewport[1]
      h *= (float(w) / float(h)) / (4.0 / 3.0)
      glOrtho(0, 1, h/w, 0, -100, 100)
      glMatrixMode(GL_MODELVIEW)
      glLoadIdentity()
      
      glEnable(GL_BLEND)
      glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
      glEnable(GL_COLOR_MATERIAL)
      self.theme.setBaseColor(1)
    elif self.setlist_type == 3:
      w, h = scene.geometry
      item  = scene.items[scene.selectedIndex]
      i = scene.selectedIndex
      img = None
      lockImg = None
      if scene.itemLabels[i] == "Random":
        if scene.img_random_label:
          img = scene.img_random_label
          imgwidth = img.width1()
          wfactor = 155.000/imgwidth
        elif scene.img_empty_label:
          img = scene.img_empty_label
          imgwidth = img.width1()
          wfactor = 155.000/imgwidth
      elif not scene.itemLabels[i]:
        if scene.img_empty_label != None:
          imgwidth = scene.img_empty_label.width1()
          wfactor = 155.000/imgwidth
          img = scene.img_empty_label
      elif scene.itemLabels[i]:
        img = scene.itemLabels[i]
        imgwidth = img.width1()
        wfactor = 155.000/imgwidth
      if isinstance(item, Song.SongInfo) and item.getLocked():
        if scene.img_locked_label:
          imgwidth = scene.img_locked_label.width1()
          wfactor2 = 155.000/imgwidth
          lockImg = scene.img_locked_label
        elif scene.img_empty_label:
          imgwidth = scene.img_empty_label.width1()
          wfactor = 155.000/imgwidth
          img = scene.img_empty_label
      if img:
        scene.drawImage(img, scale = (wfactor,-wfactor), coord = (.21*w,.59*h))
      if lockImg:
        scene.drawImage(lockImg, scale = (wfactor2,-wfactor2), coord = (.21*w,.59*h))

  def renderForeground(self, scene):
    font = scene.fontDict['songListFont']
    w, h = scene.geometry
    if self.setlist_type == 2:
      text = scene.scorePart.text
      scale = 0.00250
      glColor3f(1, 1, 1)
      font.render(text, (0.95, 0.000), scale=scale, align = 2)
    elif self.setlist_type == 3:
      font = scene.fontDict['songListFont']

      c1,c2,c3 = self.song_rb2_diff_color
      glColor3f(c1,c2,c3)
      
      font.render(_("DIFFICULTY"), (.095, .5325), scale = 0.0018)
      scale = 0.0014
      text = _("BAND")
      font.render(text, (.17, .5585), scale = scale, align = 2)
      text = _("GUITAR")
      font.render(text, (.17, .5835), scale = scale, align = 2)
      text = _("DRUM")
      font.render(text, (.17, .6085), scale = scale, align = 2)
      text = _("BASS")
      font.render(text, (.17, .6335), scale = scale, align = 2)
      text = _("VOCALS")
      font.render(text, (.17, .6585), scale = scale, align = 2)

      #Add support for lead and rhythm diff

      #Qstick - Sorting Text
      text = _("SORTING:") + "     "
      if scene.sortOrder == 0: #title
        text = text + _("ALPHABETICALLY BY TITLE")
      elif scene.sortOrder == 1: #artist
        text = text + _("ALPHABETICALLY BY ARTIST")
      elif scene.sortOrder == 2: #timesplayed
        text = text + _("BY PLAY COUNT")
      elif scene.sortOrder == 3: #album
        text = text + _("ALPHABETICALLY BY ALBUM")
      elif scene.sortOrder == 4: #genre
        text = text + _("ALPHABETICALLY BY GENRE")
      elif scene.sortOrder == 5: #year
        text = text + _("BY YEAR")
      elif scene.sortOrder == 6: #Band Difficulty
        text = text + _("BY BAND DIFFICULTY")
      elif scene.sortOrder == 7: #Band Difficulty
        text = text + _("BY INSTRUMENT DIFFICULTY")
      else:
        text = text + _("BY SONG COLLECTION")
        
      font.render(text, (.13, .152), scale = 0.0017)

      if scene.songLoader:
        font.render(_("Loading Preview..."), (.05, .7), scale = 0.001)
      return
    if scene.img_list_button_guide:
      scene.drawImage(scene.img_list_button_guide, scale = (.5, -.5), coord = (w*.5,0), fit = 2)
    if scene.songLoader:
      font.render(_("Loading Preview..."), (.5, .7), align = 1)
    if scene.searching:
      font.render(scene.searchText, (.5, .7), align = 1)
    if scene.img_list_fg:
      scene.drawImage(scene.img_list_fg, scale = (1.0, -1.0), coord = (w/2,h/2), stretched = 3)
  
  def renderSelectedInfo(self, scene):
    if self.setlist_type == 0: #note... clean this up. this was a rush job.
      if not scene.selectedItem:
        return
      font = scene.fontDict['font']
      screenw, screenh = scene.geometry
      v = 0
      try:
        lfont = scene.fontDict['lfont']
      except KeyError:
        lfont = font
      
      # here we reset the rendering... without pushing the matrices. (they be thar)
      # (otherwise copying engine.view.setOrthogonalProjection)
      glMatrixMode(GL_PROJECTION)
      glLoadIdentity()
      viewport = glGetIntegerv(GL_VIEWPORT)
      w = viewport[2] - viewport[0]
      h = viewport[3] - viewport[1]
      h *= (float(w) / float(h)) / (4.0 / 3.0)
      glOrtho(0, 1, h/w, 0, -100, 100)
      glMatrixMode(GL_MODELVIEW)
      glLoadIdentity()
      
      glEnable(GL_BLEND)
      glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
      glEnable(GL_COLOR_MATERIAL)
      self.theme.setBaseColor(1)

      if scene.songLoader:
        font.render(_("Loading Preview..."), (.05, .7), scale = 0.001)

      #x = .6
      x = self.song_cdscore_xpos
      y = .15

      self.theme.setSelectedColor(1)

      c1,c2,c3 = self.song_name_selected_color
      glColor3f(c1,c2,c3)
      
      item  = scene.selectedItem

      angle = scene.itemRenderAngles[scene.selectedIndex]
      f = ((90.0 - angle) / 90.0) ** 2

      cText = item.name
      if (isinstance(item, Song.SongInfo) and item.getLocked()):
        cText = _("-- Locked --")

      fh = lfont.getHeight()*0.0016
      lfont.render(cText, (x, y), scale = 0.0016)

      if isinstance(item, Song.SongInfo):
        self.theme.setBaseColor(1)

        c1,c2,c3 = self.artist_selected_color
        glColor3f(c1,c2,c3)
        
        if not item.year == "":
          yeartag = ", "+item.year
        else:
          yeartag = ""
        
        cText = item.artist + yeartag
        if (item.getLocked()):
          cText = "" # avoid giving away artist of locked song
        
        # evilynux - Use font w/o outline
        lfont.render(cText, (x, y+fh), scale = 0.0016)

        if item.count:
          self.theme.setSelectedColor(1)

          c1,c2,c3 = self.song_name_selected_color
          glColor3f(c1,c2,c3)

          count = int(item.count)
          if count == 1: 
            text = _("Played %d time") % count
          else:
            text = _("Played %d times") % count

          if item.getLocked():
            text = item.getUnlockText()
          elif scene.careerMode and not item.completed:
            text = _("Play To Advance.")
          font.render(text, (x, y+2*fh), scale = 0.001)
        else:
          text = _("Never Played")
          if item.getLocked():
            text = item.getUnlockText()
          elif scene.careerMode and not item.completed:
            text = _("Play To Advance.")
          lfont.render(text, (x, y+3*fh), scale = 0.001)

        self.theme.setSelectedColor(1 - v)

        c1,c2,c3 = self.songlistcd_score_color
        glColor3f(c1,c2,c3)

        scale = 0.0011
        
        #x = .6
        x = self.song_cdscore_xpos
        y = .42
        try:
          difficulties = item.partDifficulties[scene.scorePart.id]
        except KeyError:
          difficulties = []
        if len(difficulties) > 3:
          y = .42
        elif len(difficulties) == 0:
          score, stars, name = "---", 0, "---"
        
        for d in difficulties:
          scores = item.getHighscores(d, part = scene.scorePart)
          
          if scores:
            score, stars, name, scoreExt = scores[0]
            try:
              notesHit, notesTotal, noteStreak, modVersion, handicap, handicapLong, originalScore = scoreExt
            except ValueError:
              notesHit, notesTotal, noteStreak, modVersion, oldScores1, oldScores2 = scoreExt
              handicap = 0
              handicapLong = "None"
              originalScore = score
          else:
            score, stars, name = "---", 0, "---"
          self.theme.setBaseColor(1)
          font.render(Song.difficulties[d.id].text, (x, y), scale = scale)

          starscale = 0.02
          stary = 1.0 - y/scene.fontScreenBottom
          scene.drawStarScore(screenw, screenh, x+.01, stary-2*fh, stars, starscale, hqStar = True) #volshebnyi

          self.theme.setSelectedColor(1)
          # evilynux - Also use hit%/noteStreak SongList option
          if scores:
            if notesTotal != 0:
              score = "%s %.1f%%" % (score, (float(notesHit) / notesTotal) * 100.0)
            if noteStreak != 0:
              score = "%s (%d)" % (score, noteStreak)
          font.render(unicode(score), (x + .15, y),     scale = scale)
          font.render(name,       (x + .15, y + fh),     scale = scale)
          y += 2 * fh
      elif isinstance(item, Song.LibraryInfo):
        self.theme.setBaseColor(1)
        c1,c2,c3 = self.library_selected_color
        
        glColor3f(c1,c2,c3)

        if item.songCount == 1:
          songCount = _("One Song In This Setlist")
        else:
          songCount = _("%d Songs In This Setlist") % item.songCount
        font.render(songCount, (x, y + 3*fh), scale = 0.0016)
        
      elif isinstance(item, Song.RandomSongInfo):
        self.theme.setBaseColor(1 - v)

        c1,c2,c3 = self.song_name_selected_color
        glColor3f(c1,c2,c3)

        font.render(_("(Random Song)"), (x, y + 3*fh), scale = 0.0016)

      #MFH CD list
      text = scene.scorePart.text
      scale = 0.00250
      #glColor3f(1, 1, 1)
      c1,c2,c3 = self.song_name_selected_color
      glColor3f(c1,c2,c3)
      w, h = font.getStringSize(text, scale=scale)
      font.render(text, (0.95-w, 0.000), scale=scale)
      # finally:
        # pass
    elif self.setlist_type == 1:
      return
    elif self.setlist_type == 2:
      if not scene.selectedItem:
        return
      item = scene.selectedItem
      font = scene.fontDict['font']
      w, h = scene.geometry
      try:
        lfont = scene.fontDict['lfont']
      except KeyError:
        lfont = font
      fh = lfont.getHeight()*0.0016
      if isinstance(item, Song.SongInfo):
        angle = scene.itemRenderAngles[scene.selectedIndex]
        f = ((90.0 - angle) / 90.0) ** 2

        self.theme.setSelectedColor(1)
        
        c1,c2,c3 = self.songlistcd_score_color
        glColor4f(c1,c2,c3,1)

        scale = 0.0013
        x = self.song_listcd_score_xpos
        y = self.song_listcd_score_ypos + f / 2.0
        try:
          difficulties = item.partDifficulties[scene.scorePart.id]
        except KeyError:
          difficulties = []
          score, stars, name = "---", 0, "---"
        if len(difficulties) > 3:
          y = self.song_listcd_score_ypos + f / 2.0
        
        #new
        for d in difficulties:
          scores =  item.getHighscores(d, part = scene.scorePart)
          if scores:
            score, stars, name, scoreExt = scores[0]
            try:
              notesHit, notesTotal, noteStreak, modVersion, handicap, handicapLong, originalScore = scoreExt
            except ValueError:
              notesHit, notesTotal, noteStreak, modVersion, oldScores1, oldScores2 = scoreExt
              handicap = 0
              handicapLong = "None"
              originalScore = score
          else:
            score, stars, name = "---", 0, "---"
          
          font.render(Song.difficulties[d.id].text, (x, y), scale = scale)
          
          starscale = 0.02
          starx = x + starscale/2
          stary = 1.0 - (y / scene.fontScreenBottom) - fh - starscale
          scene.drawStarScore(w, h, starx, stary, stars, starscale) #MFH
          c1,c2,c3 = self.songlistcd_score_color
          glColor3f(c1,c2,c3)
          if scores:
            if notesTotal != 0:
              score = "%s %.1f%%" % (score, (float(notesHit) / notesTotal) * 100.0)
            if noteStreak != 0:
              score = "%s (%d)" % (score, noteStreak)
          font.render(unicode(score), (x + .15, y),     scale = scale)
          font.render(name,       (x + .15, y + fh),     scale = scale)
          y += 2 * fh + f / 4.0
    elif self.setlist_type == 3:
      w, h = scene.geometry
      font = scene.fontDict['songListFont']
      item = scene.selectedItem
      if isinstance(item, Song.SongInfo):
        text = item.artist
        if (item.getLocked()):
          text = "" # avoid giving away artist of locked song

        scale = 0.0015
        wt, ht = font.getStringSize(text, scale=scale)
        
        while wt > .21:
          tlength = len(text) - 4
          text = text[:tlength] + "..."
          wt, ht = font.getStringSize(text, scale = scale)
          if wt < .22:
            break
          
        c1,c2,c3 = self.artist_text_color
        glColor3f(c1,c2,c3)
        
        text = string.upper(text)
        font.render(text, (.095, .44), scale = scale)
        
        if scene.img_diff3 != None:
          imgwidth = scene.img_diff3.width1()
          imgheight = scene.img_diff3.height1()
          wfactor1 = 13.0/imgwidth
        
        albumtag = item.album
        albumtag = string.upper(albumtag)
        wt, ht = font.getStringSize(albumtag, scale=scale)
        
        while wt > .21:
          tlength = len(albumtag) - 4
          albumtag = albumtag[:tlength] + "..."
          wt, ht = font.getStringSize(albumtag, scale = scale)
          if wt < .22:
            break                    

        font.render(albumtag, (.095, .47), scale = 0.0015)
        
        genretag = item.genre
        font.render(genretag, (.095, .49), scale = 0.0015)                                

        yeartag = item.year           
        font.render(yeartag, (.095, .51), scale = 0.0015)

     
        for i in range(5):
          glColor3f(1, 1, 1) 
          if i == 0:
            diff = item.diffSong
          elif i == 1:
            diff = item.diffGuitar
          elif i == 2:
            diff = item.diffDrums
          elif i == 3:
            diff = item.diffBass
          elif i == 4:
            diff = item.diffVocals
          if scene.img_diff1 == None or scene.img_diff2 == None or scene.img_diff3 == None:
            if diff == -1:
              font.render("N/A", (.18, .5585 + i*.025), scale = 0.0014)
            elif diff == 6:
              glColor3f(1, 1, 0)  
              font.render(str("*" * (diff -1)), (.18, 0.5685 + i*.025), scale = 0.003)
            else:
              font.render(str("*" * diff + " " * (5 - diff)), (.18, 0.5685 + i*.025), scale = 0.003)
          else:
            if diff == -1:
              font.render("N/A", (.18, .5585 + i*.025), scale = 0.0014)
            elif diff == 6:
              for k in range(0,5):
                scene.drawImage(scene.img_diff3, scale = (wfactor1,-wfactor1), coord = ((.19+.03*k)*w, (0.2354-.0333*i)*h))
            else:
              for k in range(0,diff):
                scene.drawImage(scene.img_diff2, scale = (wfactor1,-wfactor1), coord = ((.19+.03*k)*w, (0.2354-.0333*i)*h))
              for k in range(0, 5-diff):
                scene.drawImage(scene.img_diff1, scale = (wfactor1,-wfactor1), coord = ((.31-.03*k)*w, (0.2354-.0333*i)*h))

  def renderMoreInfo(self, scene):
    if not scene.items:
      return
    if not scene.selectedItem:
      return
    item = scene.selectedItem
    i = scene.selectedIndex
    y = 0
    w, h = scene.geometry
    font = scene.fontDict['songListFont']
    self.theme.fadeScreen(0.25)
    if scene.moreInfoTime < 500:
      y = 1.0-(float(scene.moreInfoTime)/500.0)
    yI = y*h
    if scene.img_panel:
      scene.drawImage(scene.img_panel, scale = (1.0, -1.0), coord = (w*.5,h*.5+yI), stretched = 3)
    if scene.img_tabs:
      r0 = (0, (1.0/3.0), 0, .5)
      r1 = ((1.0/3.0),(2.0/3.0), 0, .5)
      r2 = ((2.0/3.0),1.0,0,.5)
      if scene.infoPage == 0:
        r0 = (0, (1.0/3.0), .5, 1.0)
        scene.drawImage(scene.img_tab1, scale = (.5, -.5), coord = (w*.5,h*.5+yI))
        text = item.name
        if item.artist != "":
          text += " by %s" % item.artist
        if item.year != "":
          text += " (%s)" % item.year
        scale = font.scaleText(text, .45, .0015)
        font.render(text, (.52, .25-y), scale = scale, align = 1)
        if scene.itemLabels[i]:
          imgwidth = scene.itemLabels[i].width1()
          wfactor = 95.000/imgwidth
          scene.drawImage(scene.itemLabels[i], (wfactor, -wfactor), (w*.375,h*.5+yI))
        elif scene.img_empty_label:
          imgwidth = scene.img_empty_label.width1()
          wfactor = 95.000/imgwidth
          scene.drawImage(scene.img_empty_label, (wfactor, -wfactor), (w*.375,h*.5+yI))
        text = item.album
        if text == "":
          text = _("No Album")
        scale = font.scaleText(text, .2, .0015)
        font.render(text, (.56, .305-y), scale = scale)
        text = item.genre
        if text == "":
          text = _("No Genre")
        scale = font.scaleText(text, .2, .0015)
        font.render(text, (.56, .35-y), scale = scale)
      elif scene.infoPage == 1:
        r1 = ((1.0/3.0),(2.0/3.0), .5, 1.0)
        scene.drawImage(scene.img_tab2, scale = (.5, -.5), coord = (w*.5,h*.5+yI))
      elif scene.infoPage == 2:
        r2 = ((2.0/3.0),1.0, .5, 1.0)
        scene.drawImage(scene.img_tab3, scale = (.5, -.5), coord = (w*.5,h*.5+yI))
      scene.drawImage(scene.img_tabs, scale = (.5*(1.0/3.0), -.25), coord = (w*.36,h*.72+yI), rect = r0)
      scene.drawImage(scene.img_tabs, scale = (.5*(1.0/3.0), -.25), coord = (w*.51,h*.72+yI), rect = r1)
      scene.drawImage(scene.img_tabs, scale = (.5*(1.0/3.0), -.25), coord = (w*.66,h*.72+yI), rect = r2)
  
  def renderMiniLobby(self, scene):
    return
  