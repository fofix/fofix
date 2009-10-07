#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire                                                     #
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
Config.define("theme", "credit_song",       str, "Unknown")

Config.define("theme", "fret0_color",       str, "#22FF22")
Config.define("theme", "fret1_color",       str, "#FF2222")
Config.define("theme", "fret2_color",       str, "#FFFF22")
Config.define("theme", "fret3_color",       str, "#3333FF")
Config.define("theme", "fret4_color",       str, "#FF9933")
Config.define("theme", "open_fret_color",   str, "#CC22CC")

Config.define("theme", "flame0_1X_color",    str, "#d5ff82")
Config.define("theme", "flame1_1X_color",    str, "#ff8880")
Config.define("theme", "flame2_1X_color",    str, "#faf66b")
Config.define("theme", "flame3_1X_color",    str, "#a4f8ff")
Config.define("theme", "flame4_1X_color",    str, "#ffde8c")
Config.define("theme", "flame0_2X_color",    str, "#d5ff82")
Config.define("theme", "flame1_2X_color",    str, "#ff8880")
Config.define("theme", "flame2_2X_color",    str, "#faf66b")
Config.define("theme", "flame3_2X_color",    str, "#a4f8ff")
Config.define("theme", "flame4_2X_color",    str, "#ffde8c")
Config.define("theme", "flame0_3X_color",    str, "#d5ff82")
Config.define("theme", "flame1_3X_color",    str, "#ff8880")
Config.define("theme", "flame2_3X_color",    str, "#faf66b")
Config.define("theme", "flame3_3X_color",    str, "#a4f8ff")
Config.define("theme", "flame4_3X_color",    str, "#ffde8c")
Config.define("theme", "flame0_4X_color",    str, "#d5ff82")
Config.define("theme", "flame1_4X_color",    str, "#ff8880")
Config.define("theme", "flame2_4X_color",    str, "#faf66b")
Config.define("theme", "flame3_4X_color",    str, "#a4f8ff")
Config.define("theme", "flame4_4X_color",    str, "#ffde8c")

Config.define("theme", "flame_gh3_color",    str, "#BF6006")

Config.define("theme", "flame0_1X_size",     float, 0.075)
Config.define("theme", "flame1_1X_size",     float, 0.075)
Config.define("theme", "flame2_1X_size",     float, 0.075)
Config.define("theme", "flame3_1X_size",     float, 0.075)
Config.define("theme", "flame4_1X_size",     float, 0.075)
Config.define("theme", "flame0_2X_size",     float, 0.075)
Config.define("theme", "flame1_2X_size",     float, 0.075)
Config.define("theme", "flame2_2X_size",     float, 0.075)
Config.define("theme", "flame3_2X_size",     float, 0.075)
Config.define("theme", "flame4_2X_size",     float, 0.075)
Config.define("theme", "flame0_3X_size",     float, 0.075)
Config.define("theme", "flame1_3X_size",     float, 0.075)
Config.define("theme", "flame2_3X_size",     float, 0.075)
Config.define("theme", "flame3_3X_size",     float, 0.075)
Config.define("theme", "flame4_3X_size",     float, 0.075)
Config.define("theme", "flame0_4X_size",     float, 0.075)
Config.define("theme", "flame1_4X_size",     float, 0.075)
Config.define("theme", "flame2_4X_size",     float, 0.075)
Config.define("theme", "flame3_4X_size",     float, 0.075)
Config.define("theme", "flame4_4X_size",     float, 0.075)

Config.define("theme", "disable_song_spinny",    bool, False)
Config.define("theme", "disable_editor_spinny",  bool, False)
Config.define("theme", "disable_results_spinny", bool, False)
Config.define("theme", "disable_menu_spinny",    bool, False)

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

Config.define("theme", "songback",       bool, False)
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
Config.define("theme", "song_cd_x",       float, None)
Config.define("theme", "song_cdscore_x",       float, None)
Config.define("theme", "song_list_x",       float, None)
Config.define("theme", "song_listscore_x",       float, None)

Config.define("theme", "song_listcd_cd_x",       float, None)
Config.define("theme", "song_listcd_cd_y",       float, None)
Config.define("theme", "song_listcd_score_x",       float, None)
Config.define("theme", "song_listcd_score_y",       float, None)
Config.define("theme", "song_listcd_list_x",       float, None)

Config.define("theme", "song_rb2_name_color",       str, "#FFFFFF")
Config.define("theme", "song_rb2_name_selected_color",       str, "#FFBF00")
Config.define("theme", "song_rb2_diff_color",       str, "#FFBF00")
Config.define("theme", "song_rb2_artist_color",       str, "#4080FF")

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

submenuX = {}
submenuY = {}
submenuV = {}

backgroundColor = None
baseColor       = None
selectedColor   = None
fretColors      = None
gh3flameColor   = None
use_fret_colors = None

hopoColor       = None
spotColor       = None
keyColor        = None
key2Color       = None
tracksColor     = None
barsColor       = None
glowColor       = None

flameColors     = None
openFretColor   = None
flameSizes      = None
loadingPhrase   = None
resultsPhrase   = None
startingPhrase  = None

spinnySongDisabled = None
spinnyEditorDisabled = None
spinnyResultsDisabled = None
spinnyMenuDisabled = None

creditSong = None
povTargetX = None
povTargetY = None
povTargetZ = None
povOriginX = None
povOriginY = None
povOriginZ = None

#Blazingamer
menuX = None
menuY = None
menuRB = None
loadingX = None
loadingY = None
loadingColor = None
loadingFScale = None
loadingRMargin = None
loadingLSpacing = None
twoDnote = None
twoDkeys = None
threeDspin = None
fret_press = None
opencolor = None
meshColor = None
songback = None
versiontag = None
rmtype = None
shadowoffsetx = None
shadowoffsety = None

#akedrou
menuTipTextY = None
menuTipTextFont = None
menuTipTextScale = None
menuTipTextColor = None
menuTipTextScrollSpace = None
menuTipTextScrollMode = None
menuTipTextDisplay = None

#evilynux
songlist_score_colorVar = None
songlistcd_score_colorVar = None
rockmeter_score_colorVar = None
ingame_stats_colorVar = None

#akedrou - lobby/control setup
controlActivateX = None
controlActivateSelectX = None
controlActivatePartX = None
controlActivateY = None
controlActivateScale = None
controlActivatePartSize = None
controlActivateSpace = None
controlActivateFont = None
controlDescriptionY = None
controlDescriptionX = None
controlDescriptionScale = None
controlDescriptionFont = None
controlCheckX = None
controlCheckY = None
controlCheckTextY = None
controlCheckPartMult = None
controlCheckSpace = None
controlCheckScale = None
controlCheckFont  = None
lobbyMode = None
lobbyPreviewX = None
lobbyPreviewY = None #worldrave
lobbyPreviewSpacing = None
lobbyTitleX = None
lobbyTitleY = None
lobbyTitleCharacterX = None
lobbyTitleCharacterY = None
lobbyTitleScale = None
lobbyTitleFont = None
lobbyAvatarX = None
lobbyAvatarY = None
lobbyAvatarScale = None
lobbySelectX = None
lobbySelectY = None
lobbySelectImageX = None
lobbySelectImageY = None
lobbySelectScale = None
lobbySelectSpace = None
lobbySelectFont = None
lobbySelectLength = None
lobbyTitleColor = None
lobbyInfoColor = None
lobbyFontColor = None
lobbyPlayerColor = None
lobbySelectColor = None
lobbyDisableColor = None
characterCreateX = None
characterCreateY = None
characterCreateOptionX = None
characterCreateFontColor = None
characterCreateSelectColor = None
characterCreateHelpColor = None
characterCreateHelpX = None
characterCreateHelpY = None
characterCreateHelpScale = None
characterCreateOptionFont = None
characterCreateHelpFont = None
characterCreateScale = None
characterCreateSpace = None
avatarSelectTextX = None
avatarSelectTextY = None
avatarSelectTextScale = None
avatarSelectFont = None
avatarSelectAvX = None
avatarSelectAvY = None
avatarSelectWheelY = None

vocalMeterSize = None
vocalMeterX = None
vocalMeterY = None
vocalMultX  = None
vocalMultY  = None
vocalPowerX = None
vocalPowerY = None
vocalFillupCenterX = None
vocalFillupCenterY = None
vocalFillupInRadius = None
vocalFillupOutRadius = None
vocalFillupColor = None
vocalFillupFactor = None
vocalCircularFillup = None
vocalLaneSize = None
vocalGlowSize = None
vocalGlowFade = None
vocalLaneColor = None
vocalShadowColor = None
vocalGlowColor = None
vocalLaneColorStar = None
vocalShadowColorStar = None
vocalGlowColorStar = None

#worldrave 
setlistguidebuttonsposX = None
setlistguidebuttonsposY = None
setlistguidebuttonsscaleX = None
setlistguidebuttonsscaleY = None
setlistpreviewbuttonposX = None
setlistpreviewbuttonposY = None
setlistpreviewbuttonscaleY = None
setlistpreviewbuttonscaleY = None

noterot = [0]*5
notepos = [0]*5
drumnoterot = [0]*5
drumnotepos = [0]*5
keyrot = [0]*5
keypos = [0]*5
drumkeyrot = [0]*5
drumkeypos = [0]*5

#MFH:
song_cd_Xpos = None         #Songlist in CD mode: horizontal position of CDs/cases
song_cdscore_Xpos = None    #Songlist in CD mode: horizontal position of score info
song_list_Xpos = None       #Songlist in List mode: horizontal position of song names/artists
song_listscore_Xpos = None  #Songlist in List mode: horizontal position of score info

song_listcd_cd_Xpos = None
song_listcd_cd_Ypos = None
song_listcd_score_Xpos = None
song_listcd_score_Ypos = None
song_listcd_list_Xpos = None

pause_bkg_pos = [None]*4
pause_text_xPos = None
pause_text_yPos = None

opt_bkg_size = [None]*4
opt_text_xPos = None
opt_text_yPos = None

main_menu_scaleVar = None
main_menu_vspacingVar = None
use_solo_submenu = None
sub_menu_xVar = None
sub_menu_yVar = None

career_title_colorVar = None
opt_text_colorVar = None
opt_selected_colorVar = None
song_name_text_colorVar = None
song_name_selected_colorVar = None
artist_text_colorVar = None
artist_selected_colorVar = None
library_text_colorVar = None
library_selected_colorVar = None

song_rb2_name_colorVar = None
song_rb2_name_selected_colorVar = None
song_rb2_diff_colorVar = None
song_rb2_artist_colorVar = None

pause_text_colorVar = None
pause_selected_colorVar = None
fail_completed_colorVar = None
fail_text_colorVar = None
fail_selected_colorVar = None

#MFH - crowd cheer loop delay in ini: if not exist, use value from settings. Otherwise, use ini value.
crowdLoopDelay = None

#MFH - for instrument / difficulty / practice section submenu positioning
songSelectSubmenuX = None
songSelectSubmenuY = None

#TWD - for neck chooser text positionning
neck_prompt_x = None
neck_prompt_y = None

#MFH - for scaling song info during countdown
songInfoDisplayScale = None

#Worldrave - for position of song info display during countdown
songInfoDisplayX = None
songInfoDisplayY = None
versiontagposX = None
versiontagposY = None
neckLength = None

#MFH - y offset = lines, x offset = spaces
songSelectSubmenuOffsetLines = None
songSelectSubmenuOffsetSpaces = None

#MFH - option for Rock Band 2 ini - only show # of stars you are working on
displayAllGreyStars = None
smallMult = None

#Qstick - hopo indicator position and color
hopoIndicatorX = None
hopoIndicatorY = None
hopoIndicatorActiveColor = None
hopoIndicatorInactiveColor = None

#stump - parameters for continuous fillup of stars
starFillupCenterX = None
starFillupCenterY = None
starFillupInRadius = None
starFillupOutRadius = None
starFillupColor = None

#Qstick - misc
songListDisplay = None
neckWidth = None
markSolos = None
power_up_name = None #akedrou

result_score = [None] * 5
result_star = [None] * 4
result_song = [None] * 5
result_song_form = None
result_song_text = None
result_stats_part = [None] * 5
result_stats_part_text = None
result_stats_name = [None] * 5
result_stats_diff = [None] * 5
result_stats_diff_text = None
result_stats_accuracy = [None] * 5
result_stats_accuracy_text = None
result_stats_streak = [None] * 5
result_stats_streak_text = None
result_stats_notes = [None] * 5
result_stats_notes_text = None
#akedrou
result_cheats_info = [None] * 3
result_cheats_numbers = [None] * 3
result_cheats_score = [None] * 3
result_cheats_percent = [None] * 3
result_cheats_color = None
result_cheats_font  = None
result_high_score_font = None
result_menu_x = None
result_menu_y = None
result_star_type = None

jurgTextPos = [None] * 3


#Racer:
#fail_bkg_xPos = None
#fail_bkg_yPos = None
fail_bkg_pos = [None]*4
fail_text_xPos = None
fail_text_yPos = None



def hexToColor(color):
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

def hexToColorResults(color):
  color = color.strip()
  if color[0] == "#":
    color = color[1:]
    if len(color) == 3:
      return (int(color[0], 16) / 15.0, int(color[1], 16) / 15.0, int(color[2], 16) / 15.0)
    return (int(color[0:2], 16) / 255.0, int(color[2:4], 16) / 255.0, int(color[4:6], 16) / 255.0)
  return baseColor
    
def colorToHex(color):
  return "#" + ("".join(["%02x" % int(c * 255) for c in color]))

def setSelectedColor(alpha = 1.0):
  glColor4f(*(selectedColor + (alpha,)))

def setBaseColor(alpha = 1.0):
  glColor4f(*(baseColor + (alpha,)))
  
def packTupleKey(key, type = str):
  vals = key.split(',')
  if isinstance(type, list):
    retval = tuple(type[i](n.strip()) for i, n in enumerate(vals))
  else:
    retval = tuple(type(n.strip()) for n in vals)
  return retval

def open(config, themepath = None):
  # Read in ini specific variables

  
  setupColors(config)
  setupFrets(config)
  setupFlameColors(config)
  setupFlameSizes(config)
  setupSpinny(config)
  setupPOV(config)
  setupMisc(config)
  setupMenu(config)
  setupLobby(config) #akedrou
  setupVocals(config) #akedrou
  setupSonglist(config) #MFH
  setupPauseNOpt(config) #MFH
  setupTWOD(config)
  setupFail(config) #racer
  setupEvilynux(config)
  setupRockmeter(config)
  setupNeckChooser(config)
  setupHopoIndicator(config)
  setupResults(config)
  setupSubmenus(config, themepath)

 
  

def setupNeckChooser(config):
  global neck_prompt_x, neck_prompt_y
  
  neck_prompt_x = config.get("theme", "menu_neck_choose_x")
  neck_prompt_y = config.get("theme", "menu_neck_choose_y")


def setupColors(config):
  global backgroundColor, baseColor, selectedColor
  global hopoColor, spotColor, meshColor
  global keyColor, key2Color
  global tracksColor, barsColor, glowColor
  
  backgroundColor = hexToColor(config.get("theme", "background_color"))  
  baseColor = hexToColor(config.get("theme", "base_color"))
  selectedColor = hexToColor(config.get("theme", "selected_color"))
  meshColor = hexToColor(config.get("theme", "mesh_color"))
  hopoColor = hexToColor(config.get("theme", "hopo_color"))
  spotColor = hexToColor(config.get("theme", "spot_color"))
  keyColor = hexToColor(config.get("theme", "key_color"))
  key2Color = hexToColor(config.get("theme", "key2_color"))
  tracksColor = hexToColor(config.get("theme", "tracks_color"))
  barsColor = hexToColor(config.get("theme", "bars_color"))
  glowColor = hexToColor(config.get("theme", "glow_color"))
 
def setupFrets(config):
  global fretColors, openFretColor, use_fret_colors
    
  if fretColors == None:
    fretColors = [hexToColor(config.get("theme", "fret%d_color" % i)) for i in range(5)]
    fretColors.append(hexToColor(config.get("theme", "fretS_color"))) #Volshebnyi - spNote color
    fretColors.append(hexToColor(config.get("theme", "fretK_color"))) #Volshebnyi - killswitch tail color
  else:
    fretColors[0] = hexToColor(config.get("theme", "fret0_color"))
    fretColors[1] = hexToColor(config.get("theme", "fret1_color"))
    fretColors[2] = hexToColor(config.get("theme", "fret2_color"))
    fretColors[3] = hexToColor(config.get("theme", "fret3_color"))
    fretColors[4] = hexToColor(config.get("theme", "fret4_color"))
    fretColors[5] = hexToColor(config.get("theme", "fretS_color"))
    fretColors[6] = hexToColor(config.get("theme", "fretK_color"))
  openFretColor = hexToColor(config.get("theme", "open_fret_color"))
  use_fret_colors = config.get("theme", "use_fret_colors")

def setupFlameColors(config):
  global flameColors
  global gh3flameColor

  temp = config.get("theme", "flame_gh3_color")
  gh3flameColor = hexToColor(temp)
  if flameColors == None:
    flameColors = [[hexToColor(config.get("theme", "flame%d_1X_color" % i)) for i in range(5)]]
    flameColors.append([hexToColor(config.get("theme", "flame%d_2X_color" % i)) for i in range(5)])
    flameColors.append([hexToColor(config.get("theme", "flame%d_3X_color" % i)) for i in range(5)])
    flameColors.append([hexToColor(config.get("theme", "flame%d_4X_color" % i)) for i in range(5)])
  else:
    flameColors[0][0] = hexToColor(config.get("theme", "flame0_1X_color"))
    flameColors[0][1] = hexToColor(config.get("theme", "flame1_1X_color"))
    flameColors[0][2] = hexToColor(config.get("theme", "flame2_1X_color"))
    flameColors[0][3] = hexToColor(config.get("theme", "flame3_1X_color"))
    flameColors[0][4] = hexToColor(config.get("theme", "flame4_1X_color"))
    flameColors[1][0] = hexToColor(config.get("theme", "flame0_2X_color"))
    flameColors[1][1] = hexToColor(config.get("theme", "flame1_2X_color"))
    flameColors[1][2] = hexToColor(config.get("theme", "flame2_2X_color"))
    flameColors[1][3] = hexToColor(config.get("theme", "flame3_2X_color"))
    flameColors[1][4] = hexToColor(config.get("theme", "flame4_2X_color"))
    flameColors[2][0] = hexToColor(config.get("theme", "flame0_3X_color"))
    flameColors[2][1] = hexToColor(config.get("theme", "flame1_3X_color"))
    flameColors[2][2] = hexToColor(config.get("theme", "flame2_3X_color")) 
    flameColors[2][3] = hexToColor(config.get("theme", "flame3_3X_color"))
    flameColors[2][4] = hexToColor(config.get("theme", "flame4_3X_color"))
    flameColors[3][0] = hexToColor(config.get("theme", "flame0_4X_color"))
    flameColors[3][1] = hexToColor(config.get("theme", "flame1_4X_color"))
    flameColors[3][2] = hexToColor(config.get("theme", "flame2_4X_color"))
    flameColors[3][3] = hexToColor(config.get("theme", "flame3_4X_color"))
    flameColors[3][4] = hexToColor(config.get("theme", "flame4_4X_color"))

        
def setupFlameSizes(config):
  global flameSizes

  if flameSizes == None:
    flameSizes = [[config.get("theme", "flame%d_1X_size" % i) for i in range(5)]]
    flameSizes.append([config.get("theme", "flame%d_2X_size" % i) for i in range(5)])
    flameSizes.append([config.get("theme", "flame%d_3X_size" % i) for i in range(5)])
    flameSizes.append([config.get("theme", "flame%d_4X_size" % i) for i in range(5)])
  else:
    flameSizes[0][0] = config.get("theme", "flame0_1X_size")
    flameSizes[0][1] = config.get("theme", "flame1_1X_size")
    flameSizes[0][2] = config.get("theme", "flame2_1X_size")
    flameSizes[0][3] = config.get("theme", "flame3_1X_size")
    flameSizes[0][4] = config.get("theme", "flame4_1X_size")
    flameSizes[1][0] = config.get("theme", "flame0_2X_size")
    flameSizes[1][1] = config.get("theme", "flame1_2X_size")
    flameSizes[1][2] = config.get("theme", "flame2_2X_size")
    flameSizes[1][3] = config.get("theme", "flame3_2X_size")
    flameSizes[1][4] = config.get("theme", "flame4_2X_size")
    flameSizes[2][0] = config.get("theme", "flame0_3X_size")
    flameSizes[2][1] = config.get("theme", "flame1_3X_size")
    flameSizes[2][2] = config.get("theme", "flame2_3X_size") 
    flameSizes[2][3] = config.get("theme", "flame3_3X_size")
    flameSizes[2][4] = config.get("theme", "flame4_3X_size")
    flameSizes[3][0] = config.get("theme", "flame0_4X_size")
    flameSizes[3][1] = config.get("theme", "flame1_4X_size")
    flameSizes[3][2] = config.get("theme", "flame2_4X_size")
    flameSizes[3][3] = config.get("theme", "flame3_4X_size")
    flameSizes[3][4] = config.get("theme", "flame4_4X_size")
    
def setupSpinny(config):
  global spinnySongDisabled, spinnyEditorDisabled, spinnyResultsDisabled, spinnyMenuDisabled

  spinnySongDisabled = config.get("theme", "disable_song_spinny")
  spinnyEditorDisabled = config.get("theme", "disable_editor_spinny")
  spinnyResultsDisabled = config.get("theme", "disable_results_spinny")
  spinnyMenuDisabled = config.get("theme", "disable_menu_spinny")
  
def setupPOV(config):
  global povTargetX, povTargetY, povTargetZ
  global povOriginX, povOriginY, povOriginZ
  
  povTargetX = config.get("theme", "pov_target_x")  
  povTargetY = config.get("theme", "pov_target_y")
  povTargetZ = config.get("theme", "pov_target_z")
  povOriginX = config.get("theme", "pov_origin_x")
  povOriginY = config.get("theme", "pov_origin_y")
  povOriginZ = config.get("theme", "pov_origin_z")

def setupMisc(config):
  global loadingPhrase, resultsPhrase
  global creditSong
  global crowdLoopDelay
  global songInfoDisplayScale
  global songInfoDisplayX
  global songInfoDisplayY
  global displayAllGreyStars, smallMult
  global starFillupCenterX
  global starFillupCenterY
  global starFillupInRadius
  global starFillupOutRadius
  global starFillupColor
  global songListDisplay
  global jurgTextPos
  global oBarHScale
  global oBar3dFill
  global neckWidth
  global neckLength
  global markSolos
  global power_up_name

  loadingPhrase = config.get("theme", "loading_phrase")
  resultsPhrase = config.get("theme", "results_phrase")
  creditSong = config.get("theme", "credit_song")
  crowdLoopDelay = config.get("theme", "crowd_loop_delay")
  songInfoDisplayScale = config.get("theme", "song_info_display_scale")
  songInfoDisplayX = config.get("theme", "song_info_display_X")
  songInfoDisplayY = config.get("theme", "song_info_display_Y")
  displayAllGreyStars = config.get("theme", "display_all_grey_stars")
  smallMult = config.get("theme", "small_1x_mult")
  starFillupCenterX = config.get("theme", "star_fillup_center_x")
  starFillupCenterY = config.get("theme", "star_fillup_center_y")
  starFillupInRadius = config.get("theme", "star_fillup_in_radius")
  starFillupOutRadius = config.get("theme", "star_fillup_out_radius")
  starFillupColor = config.get("theme", "star_fillup_color")
  songListDisplay = config.get("theme", "song_list_display")
  jurgTextPos = config.get("theme", "jurgen_text_pos").split(",")
  oBarHScale = config.get("theme", "obar_hscale")
  oBar3dFill = config.get("theme", "obar_3dfill")
  neckWidth = config.get("theme", "neck_width")
  neckLength = config.get("theme", "neck_length")
  markSolos = config.get("theme", "mark_solo_sections")
  power_up_name = config.get("theme", "power_up_name")
#MFH:
def setupSonglist(config):
  global song_cd_Xpos, song_cdscore_Xpos, song_list_Xpos, song_listscore_Xpos
  global song_listcd_cd_Xpos, song_listcd_cd_Ypos, song_listcd_score_Xpos, song_listcd_score_Ypos, song_listcd_list_Xpos

  global setlistguidebuttonsposX, setlistguidebuttonsposY, setlistguidebuttonsscaleX, setlistguidebuttonsscaleY
  global setlistpreviewbuttonposX, setlistpreviewbuttonposY, setlistpreviewbuttonscaleX, setlistpreviewbuttonscaleY
  global career_title_colorVar, opt_text_colorVar, opt_selected_colorVar
  global song_name_text_colorVar, song_name_selected_colorVar
  global artist_text_colorVar, artist_selected_colorVar
  global library_text_colorVar, library_selected_colorVar
  global pause_text_colorVar, pause_selected_colorVar
  global fail_text_colorVar, fail_selected_colorVar, fail_completed_colorVar
  global songSelectSubmenuX, songSelectSubmenuY
  global songSelectSubmenuOffsetLines, songSelectSubmenuOffsetSpaces
  global versiontagposX, versiontagposY
  
  global song_rb2_name_colorVar, song_rb2_name_selected_colorVar, song_rb2_diff_colorVar, song_rb2_artist_colorVar

  setlistguidebuttonsposX = config.get("theme", "setlistguidebuttonsposX")
  setlistguidebuttonsposY = config.get("theme", "setlistguidebuttonsposY")
  setlistguidebuttonsscaleX = config.get("theme", "setlistguidebuttonsscaleX")
  setlistguidebuttonsscaleY = config.get("theme", "setlistguidebuttonsscaleY")
  setlistpreviewbuttonposX = config.get("theme", "setlistpreviewbuttonposX")
  setlistpreviewbuttonposY = config.get("theme", "setlistpreviewbuttonposY")
  setlistpreviewbuttonscaleX = config.get("theme", "setlistpreviewbuttonscaleX")
  setlistpreviewbuttonscaleY = config.get("theme", "setlistpreviewbuttonscaleY")
  versiontagposX = config.get("theme", "versiontagposX")
  versiontagposY = config.get("theme", "versiontagposY")
  songSelectSubmenuOffsetLines = config.get("theme", "song_select_submenu_offset_lines")
  songSelectSubmenuOffsetSpaces = config.get("theme", "song_select_submenu_offset_spaces")
  songSelectSubmenuX = config.get("theme", "song_select_submenu_x")
  songSelectSubmenuY = config.get("theme", "song_select_submenu_y")
  song_cd_Xpos = config.get("theme", "song_cd_x")
  song_listcd_cd_Xpos = config.get("theme", "song_listcd_cd_x")
  song_listcd_cd_Ypos = config.get("theme", "song_listcd_cd_y")
  song_listcd_score_Xpos = config.get("theme", "song_listcd_score_x")
  song_listcd_score_Ypos = config.get("theme", "song_listcd_score_y")
  song_listcd_list_Xpos = config.get("theme", "song_listcd_list_x")
  song_cdscore_Xpos = config.get("theme", "song_cdscore_x")
  song_list_Xpos = config.get("theme", "song_list_x")
  song_listscore_Xpos = config.get("theme", "song_listscore_x")
  career_title_colorVar = config.get("theme", "career_title_color")
  opt_text_colorVar = config.get("theme", "opt_text_color")
  opt_selected_colorVar = config.get("theme", "opt_selected_color")
  song_name_text_colorVar = config.get("theme", "song_name_text_color")
  song_name_selected_colorVar = config.get("theme", "song_name_selected_color")
  artist_text_colorVar = config.get("theme", "artist_text_color")
  artist_selected_colorVar = config.get("theme", "artist_selected_color")
  library_text_colorVar = config.get("theme", "library_text_color")
  library_selected_colorVar = config.get("theme", "library_selected_color")
  pause_text_colorVar = config.get("theme", "pause_text_color")
  pause_selected_colorVar = config.get("theme", "pause_selected_color")
  fail_completed_colorVar = config.get("theme", "fail_completed_color")
  fail_text_colorVar = config.get("theme", "fail_text_color")
  fail_selected_colorVar = config.get("theme", "fail_selected_color")
  
  song_rb2_name_colorVar = config.get("theme", "song_rb2_name_color")
  song_rb2_name_selected_colorVar = config.get("theme", "song_rb2_name_selected_color")
  song_rb2_diff_colorVar = config.get("theme", "song_rb2_diff_color")
  song_rb2_artist_colorVar = config.get("theme", "song_rb2_artist_color")

  
def setupPauseNOpt(config):
  global pause_bkg_pos, pause_text_xPos, pause_text_yPos
  global opt_bkg_size, opt_text_xPos, opt_text_yPos

  pause_bkg_pos = config.get("theme", "pause_bkg").split(",")
  pause_text_xPos = config.get("theme", "pause_text_x")
  pause_text_yPos = config.get("theme", "pause_text_y")
  opt_bkg_size = config.get("theme", "opt_bkg").split(",")
  opt_text_xPos = config.get("theme", "opt_text_x")
  opt_text_yPos = config.get("theme", "opt_text_y")
  
def setupMenu(config):
  global menuX, menuY, menuRB
  global loadingX, loadingY, loadingColor, loadingFScale, loadingRMargin, loadingLSpacing
  global main_menu_scaleVar, main_menu_vspacingVar, use_solo_submenu, sub_menu_xVar, sub_menu_yVar
  global songback, versiontag, shadowoffsetx, shadowoffsety, menuTipTextY, menuTipTextScrollSpace
  global menuTipTextFont, menuTipTextScale, menuTipTextScrollMode, menuTipTextDisplay, menuTipTextColor
  
  menuX = config.get("theme", "menu_x")
  menuY = config.get("theme", "menu_y")
  menuRB = config.get("theme", "rbmenu")
  loadingX = config.get("theme", "loading_x")
  loadingY = config.get("theme", "loading_y")
  loadingColor = hexToColor(config.get("theme", "loading_text_color"))
  loadingFScale = config.get("theme", "loading_font_scale")
  loadingRMargin = config.get("theme", "loading_right_margin")
  loadingLSpacing = config.get ("theme", "loading_line_spacing")
  main_menu_scaleVar = config.get("theme", "main_menu_scale")
  main_menu_vspacingVar = config.get("theme", "main_menu_vspacing")
  use_solo_submenu = config.get("theme", "use_solo_submenu")
  sub_menu_xVar = config.get("theme", "sub_menu_x")
  sub_menu_yVar = config.get("theme", "sub_menu_y")
  songback = config.get("theme", "songback")
  versiontag = config.get("theme", "versiontag")
  shadowoffsetx = config.get("theme", "shadowoffsetx")
  shadowoffsety = config.get("theme", "shadowoffsety")
  menuTipTextY = config.get("theme", "menu_tip_text_y")
  menuTipTextFont = config.get("theme", "menu_tip_text_font")
  menuTipTextScale = config.get("theme", "menu_tip_text_scale")
  menuTipTextColor = hexToColorResults(config.get("theme", "menu_tip_text_color"))
  menuTipTextScrollSpace = config.get("theme", "menu_tip_text_scroll_space")
  menuTipTextScrollMode = config.get("theme", "menu_tip_text_scroll_mode")
  menuTipTextDisplay = config.get("theme", "menu_tip_text_display")

def setupLobby(config):
  global controlActivateX, controlActivateY, controlActivateScale, controlActivateFont, controlCheckTextY
  global controlActivateSelectX, controlActivatePartX, controlActivateSpace, controlActivatePartSize
  global controlDescriptionX, controlDescriptionY, controlDescriptionScale, controlDescriptionFont, controlCheckSpace
  global controlCheckX, controlCheckY, controlCheckScale, controlCheckPartMult, controlCheckFont, lobbyPreviewX
  global lobbyTitleX, lobbyTitleY, lobbyTitleScale, lobbyTitleCharacterX, lobbyTitleCharacterY, lobbySelectScale
  global lobbySelectImageX, lobbySelectImageY, lobbySelectSpace, characterCreateHelpY, lobbyPreviewY
  global lobbyTitleFont, lobbySelectX, lobbySelectY, lobbySelectFont, characterCreateX, characterCreateY
  global characterCreateOptionX, characterCreateScale, characterCreateSpace, characterCreateHelpFont
  global characterCreateOptionFont, characterCreateHelpX, characterCreateHelpScale, avatarSelectWheelY
  global characterCreateFontColor, characterCreateSelectColor, characterCreateHelpColor
  global lobbyFontColor, lobbySelectColor, lobbyDisableColor, lobbyTitleColor, lobbyInfoColor, lobbyPlayerColor
  global lobbySelectLength, lobbyMode, lobbyPreviewSpacing, lobbyAvatarX, lobbyAvatarY, lobbyAvatarScale
  global avatarSelectTextX, avatarSelectTextY, avatarSelectTextScale, avatarSelectFont, avatarSelectAvX, avatarSelectAvY
  
  controlActivateX = config.get("theme", "control_activate_x")
  controlActivateSelectX = config.get("theme", "control_activate_select_x")
  controlActivatePartX = config.get("theme", "control_activate_part_x")
  controlActivateY = config.get("theme", "control_activate_y")
  controlActivateScale = config.get("theme", "control_activate_scale")
  controlActivateSpace = config.get("theme", "control_activate_space")
  controlActivatePartSize = config.get("theme", "control_activate_part_size")
  controlActivateFont = config.get("theme", "control_activate_font")
  controlDescriptionX = config.get("theme", "control_description_x")
  controlDescriptionY = config.get("theme", "control_description_y")
  controlDescriptionScale = config.get("theme", "control_description_scale")
  controlDescriptionFont = config.get("theme", "control_description_font")
  controlCheckX = config.get("theme", "control_check_x")
  controlCheckY = config.get("theme", "control_check_y")
  controlCheckTextY = config.get("theme", "control_check_text_y")
  controlCheckPartMult = config.get("theme", "control_check_part_mult")
  controlCheckScale = config.get("theme", "control_check_scale")
  controlCheckSpace = config.get("theme", "control_check_space")
  controlCheckFont  = config.get("theme", "control_check_font")
  lobbyMode = config.get("theme", "lobby_mode")
  lobbyPreviewX = config.get("theme", "lobby_preview_x")
  lobbyPreviewY = config.get("theme", "lobby_preview_y")
  lobbyPreviewSpacing = config.get("theme", "lobby_preview_spacing")
  lobbyTitleX = config.get("theme", "lobby_title_x")
  lobbyTitleY = config.get("theme", "lobby_title_y")
  lobbyTitleCharacterX = config.get("theme", "lobby_title_character_x")
  lobbyTitleCharacterY = config.get("theme", "lobby_title_character_y")
  lobbyTitleScale = config.get("theme", "lobby_title_scale")
  lobbyTitleFont = config.get("theme", "lobby_title_font")
  lobbyAvatarX = config.get("theme", "lobby_avatar_x")
  lobbyAvatarY = config.get("theme", "lobby_avatar_y")
  lobbyAvatarScale = config.get("theme", "lobby_avatar_scale")
  lobbySelectX = config.get("theme", "lobby_select_x")
  lobbySelectY = config.get("theme", "lobby_select_y")
  lobbySelectImageX = config.get("theme", "lobby_select_image_x")
  lobbySelectImageY = config.get("theme", "lobby_select_image_y")
  lobbySelectScale = config.get("theme", "lobby_select_scale")
  lobbySelectSpace = config.get("theme", "lobby_select_space")
  lobbySelectFont = config.get("theme", "lobby_select_font")
  lobbySelectLength = config.get("theme", "lobby_select_length")
  lobbyTitleColor = hexToColor(config.get("theme", "lobby_title_color"))
  lobbyInfoColor = hexToColor(config.get("theme", "lobby_info_color"))
  lobbyFontColor = hexToColor(config.get("theme", "lobby_font_color"))
  lobbyPlayerColor = hexToColor(config.get("theme", "lobby_player_color"))
  lobbySelectColor = hexToColor(config.get("theme", "lobby_select_color"))
  lobbyDisableColor = hexToColor(config.get("theme", "lobby_disable_color"))
  characterCreateX = config.get("theme", "character_create_x")
  characterCreateY = config.get("theme", "character_create_y")
  characterCreateOptionX = config.get("theme", "character_create_option_x")
  characterCreateFontColor = hexToColor(config.get("theme", "character_create_font_color"))
  characterCreateSelectColor = hexToColor(config.get("theme", "character_create_select_color"))
  characterCreateHelpColor = hexToColor(config.get("theme", "character_create_help_color"))
  characterCreateHelpX = config.get("theme", "character_create_help_x")
  characterCreateHelpY = config.get("theme", "character_create_help_y")
  characterCreateHelpScale = config.get("theme", "character_create_help_scale")
  characterCreateOptionFont = config.get("theme", "character_create_option_font")
  characterCreateHelpFont = config.get("theme", "character_create_help_font")
  characterCreateScale = config.get("theme", "character_create_scale")
  characterCreateSpace = config.get("theme", "character_create_space")
  avatarSelectTextX = config.get("theme","avatar_select_text_x")
  avatarSelectTextY = config.get("theme","avatar_select_text_y")
  avatarSelectTextScale = config.get("theme","avatar_select_text_scale")
  avatarSelectFont = config.get("theme","avatar_select_font")
  avatarSelectAvX = config.get("theme","avatar_select_avatar_x")
  avatarSelectAvY = config.get("theme","avatar_select_avatar_y")
  avatarSelectWheelY = config.get("theme","avatar_select_wheel_y")

def setupVocals(config):
  global vocalMeterSize, vocalMeterX, vocalMeterY, vocalMultX, vocalMultY, vocalPowerX, vocalPowerY
  global vocalFillupCenterX, vocalFillupCenterY, vocalFillupInRadius, vocalFillupOutRadius
  global vocalFillupColor, vocalFillupFactor, vocalCircularFillup, vocalLaneSize, vocalGlowSize, vocalGlowFade
  global vocalLaneColor, vocalShadowColor, vocalGlowColor, vocalLaneColorStar, vocalShadowColorStar, vocalGlowColorStar
  
  vocalMeterSize = config.get("theme", "vocal_meter_size")
  vocalMeterX = config.get("theme", "vocal_meter_x")
  vocalMeterY = config.get("theme", "vocal_meter_y")
  vocalMultX  = config.get("theme", "vocal_mult_x")
  vocalMultY  = config.get("theme", "vocal_mult_y")
  vocalPowerX = config.get("theme", "vocal_power_x")
  vocalPowerY = config.get("theme", "vocal_power_y")
  vocalFillupCenterX = config.get("theme", "vocal_fillup_center_x")
  vocalFillupCenterY = config.get("theme", "vocal_fillup_center_y")
  vocalFillupInRadius = config.get("theme", "vocal_fillup_in_radius")
  vocalFillupOutRadius = config.get("theme", "vocal_fillup_out_radius")
  vocalFillupFactor = config.get("theme", "vocal_fillup_factor")
  vocalFillupColor = config.get("theme", "vocal_fillup_color")
  vocalCircularFillup = config.get("theme", "vocal_circular_fillup")
  vocalLaneSize = config.get("theme", "vocal_lane_size")
  vocalGlowSize = config.get("theme", "vocal_glow_size")
  vocalGlowFade = config.get("theme", "vocal_glow_fade")
  vocalLaneColor = hexToColorResults(config.get("theme","vocal_lane_color"))
  vocalShadowColor = hexToColorResults(config.get("theme","vocal_shadow_color"))
  vocalGlowColor = hexToColorResults(config.get("theme","vocal_glow_color"))
  vocalLaneColorStar = hexToColorResults(config.get("theme","vocal_lane_color_star"))
  vocalShadowColorStar = hexToColorResults(config.get("theme","vocal_shadow_color_star"))
  vocalGlowColorStar = hexToColorResults(config.get("theme","vocal_glow_color_star"))

def setupTWOD(config):
  global twoDnote, twoDkeys, threeDspin, opencolor, fret_press
  global noterot, keyrot, drumnoterot, drumkeyrot
  global notepos, keypos, drumnotepos, drumkeypos
  
  twoDnote = config.get("theme", "twoDnote")
  twoDkeys = config.get("theme", "twoDkeys")
  threeDspin = config.get("theme", "threeDspin")
  fret_press = config.get("theme", "fret_press")
  opencolor = hexToColor(config.get("theme", "opencolor"))
  noterot = [config.get("theme", "noterot"+str(i+1)) for i in range(5)]
  keyrot  = [config.get("theme", "keyrot"+str(i+1)) for i in range(5)]
  drumnoterot = [config.get("theme", "drumnoterot"+str(i+1)) for i in range(5)]
  drumkeyrot = [config.get("theme", "drumkeyrot"+str(i+1)) for i in range(5)]
  notepos = [config.get("theme", "notepos"+str(i+1)) for i in range(5)]
  keypos  = [config.get("theme", "keypos"+str(i+1)) for i in range(5)]
  drumnotepos = [config.get("theme", "drumnotepos"+str(i+1)) for i in range(5)]
  drumkeypos = [config.get("theme", "drumkeypos"+str(i+1)) for i in range(5)]

#racer:
def setupFail(config):
  global fail_bkg_pos, fail_text_xPos, fail_text_yPos, fail_songname_xPos, fail_songname_yPos

  fail_bkg_pos = config.get("theme", "fail_bkg").split(",")
  fail_text_xPos = config.get("theme", "fail_text_x")
  fail_text_yPos = config.get("theme", "fail_text_y")
  fail_songname_xPos = config.get("theme", "fail_songname_x") 
  fail_songname_yPos = config.get("theme", "fail_songname_y") 

def setupRockmeter(config):
  global rmtype

  rmtype = config.get("theme", "rmtype")

def setupEvilynux(config):
  global songlist_score_colorVar, songlistcd_score_colorVar, rockmeter_score_colorVar, ingame_stats_colorVar

  songlist_score_colorVar = config.get("theme", "songlist_score_color")
  songlistcd_score_colorVar = config.get("theme", "songlistcd_score_color")
  rockmeter_score_colorVar = config.get("theme", "rockmeter_score_color")
  ingame_stats_colorVar = config.get("theme", "ingame_stats_color")

    
def setupHopoIndicator(config):
  global hopoIndicatorX, hopoIndicatorY
  global hopoIndicatorActiveColor, hopoIndicatorInactiveColor
  
  hopoIndicatorX = config.get("theme", "hopo_indicator_x")
  hopoIndicatorY = config.get("theme", "hopo_indicator_y")  
  hopoIndicatorActiveColor = hexToColor(config.get("theme", "hopo_indicator_active_color"))
  hopoIndicatorInactiveColor = hexToColor(config.get("theme", "hopo_indicator_inactive_color"))
  
def setupResults(config):
  global result_score, result_star, result_song, result_song_text, result_song_form, result_stats_part, result_stats_diff
  global result_stats_diff_text, result_stats_part_text, result_stats_streak_text, result_stats_accuracy_text
  global result_stats_accuracy, result_stats_streak, result_stats_notes, result_stats_notes_text
  global result_cheats_info, result_cheats_numbers, result_cheats_percent, result_cheats_score, result_cheats_color
  global result_menu_x, result_menu_y, result_star_type, result_stats_name, result_cheats_font, result_high_score_font
  
  result_score = config.get("theme", "result_score").split(",")
  result_star = config.get("theme", "result_star").split(",")
  result_song = config.get("theme", "result_song").split(",")
  result_song_form = config.get("theme", "result_song_form")
  result_song_text = config.get("theme", "result_song_text").strip()
  result_stats_part = config.get("theme", "result_stats_part").split(",")
  result_stats_part_text = config.get("theme", "result_stats_part_text").strip()
  result_stats_name = config.get("theme", "result_stats_name").split(",")
  result_stats_diff = config.get("theme", "result_stats_diff").split(",")
  result_stats_diff_text = config.get("theme", "result_stats_diff_text").strip()
  result_stats_accuracy = config.get("theme", "result_stats_accuracy").split(",")
  result_stats_accuracy_text = config.get("theme", "result_stats_accuracy_text").strip()
  result_stats_streak = config.get("theme", "result_stats_streak").split(",")
  result_stats_streak_text = config.get("theme", "result_stats_streak_text").strip()
  result_stats_notes = config.get("theme", "result_stats_notes").split(",")
  result_stats_notes_text = config.get("theme", "result_stats_notes_text").strip()
  result_cheats_info = config.get("theme", "result_cheats_info").split(",")
  result_cheats_numbers = config.get("theme", "result_cheats_numbers").split(",")
  result_cheats_percent = config.get("theme", "result_cheats_percent").split(",")
  result_cheats_score   = config.get("theme", "result_cheats_score").split(",")
  result_cheats_color   = config.get("theme", "result_cheats_color")
  result_cheats_font    = config.get("theme", "result_cheats_font")
  result_high_score_font = config.get("theme", "result_high_score_font")
  result_menu_x         = config.get("theme", "result_menu_x")
  result_menu_y         = config.get("theme", "result_menu_y")
  result_star_type      = config.get("theme", "result_star_type")

def setupSubmenus(config, themepath = None):
  if not themepath:
    return
  global submenuScale, submenuX, submenuY, submenuVSpace
  allfiles = os.listdir(themepath)
  submenuScale = {}
  submenuX = {}
  submenuY = {}
  submenuVSpace = {}
  listmenu = []
  for name in allfiles:
    if name.find("text") > -1:
      found = os.path.splitext(name)[0]
      if found == "maintext":
        continue
      Config.define("theme", found, str, None)
      submenuScale[found] = None
      submenuX[found] = None
      submenuY[found] = None
      submenuVSpace[found] = None
      listmenu.append(found)
  for i in listmenu:
    if i == "maintext":
      continue
    try:
      submenuX[i] = config.get("theme", i).split(",")[0].strip()
    except IndexError:
      submenuX[i] = None
    try:
      submenuY[i] = config.get("theme", i).split(",")[1].strip()
    except IndexError:
      submenuY[i] = None
    try:
      submenuScale[i] = config.get("theme", i).split(",")[2].strip()
    except IndexError:
      submenuScale[i] = None
    try:
      submenuVSpace[i] = config.get("theme", i).split(",")[3].strip()
    except IndexError:
      submenuVSpace[i] = None







      
class ThemeTrans:
  def __init__(self,themepath):
    try:
      fp, pathname, description = imp.find_module("ThemeSetlist",[themepath])
      if description[0] == ".py":
        TT = imp.load_module("ThemeSetlist", fp, pathname, description)
        self.setlist = TT.Setlist()
        Log.debug("Custom Theme Files Loaded")
      else:
        Log.debug("No Theme Files Found")
    except:
      self.setlist = SetlistBase()
      Log.debug("No Theme Files Found")
      
class SetlistBase:
  setlist_type = 3
  if setlist_type == 0: #CD mode
    setlistStyle = 0
    headerSkip = 0
    footerSkip = 0
    labelType = 1
    labelDistance = 2
    showMoreLabels = True
    texturedLabels = True
    itemsPerPage = 1
    showLockedSongs = False
    showSortTiers = True
    selectTiers = False
    itemSize = (0,.125)
  elif setlist_type == 1: #List mode
    setlistStyle = 1
    headerSkip = 2
    footerSkip = 1
    labelType = 0
    labelDistance = 0
    showMoreLabels = False
    texturedLabels = False
    itemsPerPage = 7
    showLockedSongs = False
    showSortTiers = True
    selectTiers = False
    itemSize = (0,.125)
  elif setlist_type == 2: #List/CD mode
    setlistStyle = 1
    headerSkip = 0
    footerSkip = 1
    labelType = 1
    labelDistance = 1
    showMoreLabels = False
    texturedLabels = True
    itemsPerPage = 8
    showLockedSongs = False
    showSortTiers = True
    selectTiers = False
    itemSize = (0,.125)
  else: #RB2 mode
    setlistStyle = 0
    headerSkip = 0
    footerSkip = 0
    labelType = 0
    labelDistance = 1
    showMoreLabels = False
    texturedLabels = False
    itemsPerPage = 12
    showLockedSongs = True
    showSortTiers = True
    selectTiers = False
    itemSize = (0,.07)

  career_title_color = hexToColor("#FFFFFF")
  song_name_text_color = hexToColor("#FFFFFF")
  song_name_selected_color = hexToColor("#FFBF00")
  song_rb2_diff_color = hexToColor("#FFFFFF")
  artist_text_color = hexToColor("#FFFFFF")
  artist_selected_color = hexToColor("#FFBF00")
  library_text_color = hexToColor("#FFFFFF")
  library_selected_color = hexToColor("#FFBF00")
  songlist_score_color = hexToColor("#FFFFFF")
  songlistcd_score_color = hexToColor("#FFFFFF")

  song_cd_xpos = 0.0
  song_cdscore_xpos = 0.6
  song_list_xpos = 0.15
  song_listscore_xpos = 0.8
  song_listcd_list_xpos = .1
  song_listcd_cd_xpos = .75
  song_listcd_cd_ypos = .6
  song_listcd_score_xpos = 0.6
  song_listcd_score_ypos = 0.5


  def renderHeader(self, scene): #self here used to make it easier on me, yo
    pass
    pass
  def renderUnselectedItem(self, scene, i, n):
    w, h = scene.engine.view.geometry[2:4]
    font = scene.engine.data.songListFont
    lfont = scene.engine.data.songListFont
    sfont = scene.engine.data.shadowfont
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
          text = "   " + text
      
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
        stary = 1.0 - (stary / scene.engine.data.fontScreenBottom)
        scene.engine.drawStarScore(w, h, starx, stary - h/2, stars, starscale, horiz_spacing = 1.0, hqStar = True) #MFH

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
          text = "   " + text
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
      font = scene.engine.data.songListFont
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
          scene.engine.drawImage(scene.img_tier, scale = (wfactor,-hfactor), coord = (w/1.587, h-((0.055*h)*(n+1))-(0.219*h)))

      icon = None
      if isinstance(item, Song.SongInfo):
        if item.icon != "":
          try:
            icon = scene.itemIcons[item.icon]
            imgwidth = icon.width1()
            wfactor = 23.000/imgwidth
            scene.engine.drawImage(icon, scale = (wfactor,-wfactor), coord = (w/2.86, h-((0.055*(n+1))-(0.219*h))))
          except KeyError:
            pass
      elif isinstance(item, Song.LibraryInfo):
        try:
          icon = scene.itemIcons["Library"]
          imgwidth = icon.width1()
          wfactor = 23.000/imgwidth
          scene.engine.drawImage(icon, scale = (wfactor,-wfactor), coord = (w/2.86, h-((0.055*(n+1))-(0.219*h))))
        except KeyError:
          pass
      elif isinstance(item, Song.RandomSongInfo):
        try:
          icon = scene.itemIcons["Random"]
          imgwidth = icon.width1()
          wfactor = 23.000/imgwidth
          scene.engine.drawImage(icon, scale = (wfactor,-wfactor), coord = (w/2.86, h-((0.055*(n+1))-(0.219*h))))
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
          text = "   " + text
        

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
    w, h = scene.engine.view.geometry[2:4]
    font = scene.engine.data.songListFont
    lfont = scene.engine.data.songListFont
    sfont = scene.engine.data.shadowfont
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
        scene.engine.drawImage(scene.img_item_select, scale = (wfactor,-wfactor), coord = (w/2.1, y))
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
          text = "   " + text
      
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
        stary = 1.0 - (stary / scene.engine.data.fontScreenBottom)
        scene.engine.drawStarScore(w, h, starx, stary - h/2, stars, starscale, horiz_spacing = 1.0, hqStar = True) #MFH

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
        scene.engine.drawImage(scene.img_selected, scale = (1, -1), coord = (self.song_listcd_list_xpos * w + (imgwidth*.64/2), y*1.2-h*.215))
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
          text = "   " + text

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
          scene.engine.drawImage(scene.img_tier, scale = (wfactor,-hfactor), coord = (w/1.587, h-((0.055*h)*(n+1))-(0.219*h)))
      
      if scene.img_selected:
        imgwidth = scene.img_selected.width1()
        imgheight = scene.img_selected.height1()
        wfactor = 381.5/imgwidth
        hfactor = 36.000/imgheight

        scene.engine.drawImage(scene.img_selected, scale = (wfactor,-hfactor), coord = (w/1.587, y*1.2-h*.213))
      
      
      icon = None
      if isinstance(item, Song.SongInfo):
        if item.icon != "":
          try:
            icon = scene.itemIcons[item.icon]
            imgwidth = icon.width1()
            wfactor = 23.000/imgwidth
            scene.engine.drawImage(icon, scale = (wfactor,-wfactor), coord = (w/2.86, h-((0.055*(n+1))-(0.219*h))))
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
          scene.engine.drawImage(icon, scale = (wfactor,-wfactor), coord = (w/2.86, h-((0.055*(n+1))-(0.219*h))))
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
          scene.engine.drawImage(icon, scale = (wfactor,-wfactor), coord = (w/2.86, h-((0.055*(n+1))-(0.219*h))))
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
          text = "   " + text
        

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
      w, h = scene.engine.view.geometry[2:4]
      try:
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluPerspective(60, scene.engine.view.aspectRatio, 0.1, 1000)
        
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
            setSelectedColor()
          else:
            setBaseColor()
          
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
      w, h = scene.engine.view.geometry[2:4]
      try:
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        
        glLoadIdentity()
        gluPerspective(60, scene.engine.view.aspectRatio, 0.1, 1000)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        glEnable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)
        glDepthMask(1)
        
        offset = 0
        if scene.time < 40:
          offset = 10*((40 - scene.time)/40.0)**4
        scene.camera.origin = (-9,(5.196/scene.engine.view.aspectRatio) - (5.196*2/scene.engine.view.aspectRatio)*self.song_listcd_cd_ypos,(5.196*scene.engine.view.aspectRatio)-(5.196*2*scene.engine.view.aspectRatio)*self.song_listcd_cd_xpos)
        scene.camera.target = ( 0,(5.196/scene.engine.view.aspectRatio) - (5.196*2/scene.engine.view.aspectRatio)*self.song_listcd_cd_ypos,(5.196*scene.engine.view.aspectRatio)-(5.196*2*scene.engine.view.aspectRatio)*self.song_listcd_cd_xpos)
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
      setBaseColor(1)
    elif self.setlist_type == 3:
      w, h = scene.engine.view.geometry[2:4]
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
        scene.engine.drawImage(img, scale = (wfactor,-wfactor), coord = (.21*w,.59*h))
      if lockImg:
        scene.engine.drawImage(lockImg, scale = (wfactor2,-wfactor2), coord = (.21*w,.59*h))

  def renderForeground(self, scene):
    font = scene.engine.data.songListFont
    w, h = scene.engine.view.geometry[2:4]
    if self.setlist_type == 2:
      text = scene.scorePart.text
      scale = 0.00250
      glColor3f(1, 1, 1)
      font.render(text, (0.95, 0.000), scale=scale, align = 2)
    elif self.setlist_type == 3:
      font = scene.engine.data.songListFont

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

      if scene.searchText:
        text = _("Filter: %s") % (scene.searchText) + "|"
        if not scene.matchesSearch(scene.items[scene.selectedIndex]):
          text += " (%s)" % _("Not found")
        font.render(text, (.05, .7), scale = 0.001)
      elif scene.songLoader:
        font.render(_("Loading Preview..."), (.05, .7), scale = 0.001)
      return
    if scene.img_list_button_guide:
      scene.engine.drawImage(scene.img_list_button_guide, scale = (.5, -.5), coord = (w*.5,0), fit = 2)
    if scene.songLoader:
      font.render(_("Loading Preview..."), (.5, .7), align = 1)
    if scene.img_list_fg:
      scene.engine.drawImage(scene.img_list_fg, scale = (1.0, -1.0), coord = (w/2,h/2), stretched = 3)

  def renderSelectedInfo(self, scene):
    if self.setlist_type == 0: #note... clean this up. this was a rush job.
      if not scene.selectedItem:
        return
      font = scene.engine.data.font
      screenw, screenh = scene.engine.view.geometry[2:4]
      v = 0
      try:
        lfont = scene.engine.data.lfont
      except:
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
      setBaseColor(1)

      if scene.songLoader:
        font.render(_("Loading Preview..."), (.05, .7), scale = 0.001)

      #x = .6
      x = self.song_cdscore_xpos
      y = .15

      setSelectedColor(1)

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
        setBaseColor(1)

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
          setSelectedColor(1)

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

        setSelectedColor(1 - v)

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
          setBaseColor(1)
          font.render(Song.difficulties[d.id].text, (x, y), scale = scale)

          starscale = 0.02
          stary = 1.0 - y/scene.engine.data.fontScreenBottom
          scene.engine.drawStarScore(screenw, screenh, x+.01, stary-2*fh, stars, starscale, hqStar = True) #volshebnyi

          setSelectedColor(1)
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
        setBaseColor(1)
        c1,c2,c3 = self.library_selected_color
        
        glColor3f(c1,c2,c3)

        if item.songCount == 1:
          songCount = _("One Song In This Setlist")
        else:
          songCount = _("%d Songs In This Setlist") % item.songCount
        font.render(songCount, (x, y + 3*fh), scale = 0.0016)
        
      elif isinstance(item, Song.RandomSongInfo):
        setBaseColor(1 - v)

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
      font = scene.engine.data.font
      w, h = scene.engine.view.geometry[2:4]
      try:
        lfont = scene.engine.data.lfont
      except:
        lfont = font
      fh = lfont.getHeight()*0.0016
      if isinstance(item, Song.SongInfo):
        angle = scene.itemRenderAngles[scene.selectedIndex]
        f = ((90.0 - angle) / 90.0) ** 2

        setSelectedColor(1)
        
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
          stary = 1.0 - (y / scene.engine.data.fontScreenBottom) - fh - starscale
          scene.engine.drawStarScore(w, h, starx, stary, stars, starscale) #MFH
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
      w, h = scene.engine.view.geometry[2:4]
      font = scene.engine.data.songListFont
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
                scene.engine.drawImage(scene.img_diff3, scale = (wfactor1,-wfactor1), coord = ((.19+.03*k)*w, (0.2354-.0333*i)*h))
            else:
              for k in range(0,diff):
                scene.engine.drawImage(scene.img_diff2, scale = (wfactor1,-wfactor1), coord = ((.19+.03*k)*w, (0.2354-.0333*i)*h))
              for k in range(0, 5-diff):
                scene.engine.drawImage(scene.img_diff1, scale = (wfactor1,-wfactor1), coord = ((.31-.03*k)*w, (0.2354-.0333*i)*h))

  def renderMoreInfo(self, scene):
    if not scene.items:
      return
    if not scene.selectedItem:
      return
    item = scene.selectedItem
    i = scene.selectedIndex
    y = 0
    w, h = scene.engine.view.geometry[2:4]
    font = scene.engine.data.songListFont
    Dialogs.fadeScreen(0.25)
    if scene.moreInfoTime < 500:
      y = 1.0-(float(scene.moreInfoTime)/500.0)
    yI = y*h
    if scene.img_panel:
      scene.engine.drawImage(scene.img_panel, scale = (1.0, -1.0), coord = (w*.5,h*.5+yI), stretched = 3)
    if scene.img_tabs:
      r0 = (0, (1.0/3.0), 0, .5)
      r1 = ((1.0/3.0),(2.0/3.0), 0, .5)
      r2 = ((2.0/3.0),1.0,0,.5)
      if scene.infoPage == 0:
        r0 = (0, (1.0/3.0), .5, 1.0)
        scene.engine.drawImage(scene.img_tab1, scale = (.5, -.5), coord = (w*.5,h*.5+yI))
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
          scene.engine.drawImage(scene.itemLabels[i], (wfactor, -wfactor), (w*.375,h*.5+yI))
        elif scene.img_empty_label:
          imgwidth = scene.img_empty_label.width1()
          wfactor = 95.000/imgwidth
          scene.engine.drawImage(scene.img_empty_label, (wfactor, -wfactor), (w*.375,h*.5+yI))
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
        scene.engine.drawImage(scene.img_tab2, scale = (.5, -.5), coord = (w*.5,h*.5+yI))
      elif scene.infoPage == 2:
        r2 = ((2.0/3.0),1.0, .5, 1.0)
        scene.engine.drawImage(scene.img_tab3, scale = (.5, -.5), coord = (w*.5,h*.5+yI))
      scene.engine.drawImage(scene.img_tabs, scale = (.5*(1.0/3.0), -.25), coord = (w*.36,h*.72+yI), rect = r0)
      scene.engine.drawImage(scene.img_tabs, scale = (.5*(1.0/3.0), -.25), coord = (w*.51,h*.72+yI), rect = r1)
      scene.engine.drawImage(scene.img_tabs, scale = (.5*(1.0/3.0), -.25), coord = (w*.66,h*.72+yI), rect = r2)
