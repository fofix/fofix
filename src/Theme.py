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

from OpenGL.GL import *
import Config
import Log

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

#blazingamer
Config.define("theme", "menu_x",       float, None)
Config.define("theme", "menu_y",       float, None)
Config.define("theme", "rbmenu",       bool, False)


Config.define("theme", "loading_x",       float, None)
Config.define("theme", "loading_y",       float, None)

Config.define("theme", "twoDnote",       bool, True)
Config.define("theme", "twoDkeys",       bool, True)
Config.define("theme", "threeDspin",       bool, True)
Config.define("theme", "opencolor",       str, "#FF9933")

Config.define("theme", "songback",       bool, False)
Config.define("theme", "versiontag",       bool, False)
Config.define("theme", "rmtype",       int, None)

#TWD
Config.define("theme", "menu_neck_choose_x", float, 0.1)
Config.define("theme", "menu_neck_choose_y", float, 0.05)

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

Config.define("theme", "pause_bkg_x",       float, None)
Config.define("theme", "pause_bkg_y",       float, None)
Config.define("theme", "pause_text_x",       float, None)
Config.define("theme", "pause_text_y",       float, None)

Config.define("theme", "opt_bkg_x",       float, None)
Config.define("theme", "opt_bkg_y",       float, None)
Config.define("theme", "opt_text_x",       float, None)
Config.define("theme", "opt_text_y",       float, None)
Config.define("theme", "opt_text_color",  str, "#FFFFFF")
Config.define("theme", "opt_selected_color",  str, "#FFBF00")


Config.define("theme", "main_menu_scale",       float, None)
Config.define("theme", "main_menu_vspacing",       float, None)
Config.define("theme", "sub_menu_x",       float, None)
Config.define("theme", "sub_menu_y",       float, None)

Config.define("theme", "career_title_color",  str, "#000000")
Config.define("theme", "song_name_text_color",  str, "#FFFFFF")
Config.define("theme", "song_name_selected_color",  str, "#FFBF00")
Config.define("theme", "artist_text_color",  str, "#4080FF")
Config.define("theme", "artist_selected_color",  str, "#4080FF")
Config.define("theme", "library_text_color",  str, "#FFFFFF")
Config.define("theme", "library_selected_color",  str, "#FFBF00")


Config.define("theme", "pause_text_color",  str, "#FFFFFF")
Config.define("theme", "pause_selected_color",  str, "#FFBF00")
Config.define("theme", "fail_text_color",  str, "#FFFFFF")
Config.define("theme", "fail_selected_color",  str, "#FFBF00")

#MFH - crowd cheer loop delay in theme.ini: if not exist, use value from settings. Otherwise, use theme.ini value.
Config.define("theme", "crowd_loop_delay",  int, None)

#MFH - for instrument / difficulty / practice section submenu positioning
Config.define("theme", "song_select_submenu_x",  float, None)
Config.define("theme", "song_select_submenu_y",  float, None)

#MFH - for scaling song info during countdown
Config.define("theme", "song_info_display_scale",  float, 0.0020)

#MFH - option for Rock Band 2 theme.ini - only show # of stars you are working on
Config.define("theme", "display_all_grey_stars",  bool, True)

#MFH - y offset = lines, x offset = spaces
Config.define("theme", "song_select_submenu_offset_lines",  int, 2)
Config.define("theme", "song_select_submenu_offset_spaces",  int, 2)

#Qstick - hopo indicator position and color
Config.define("theme", "hopo_indicator_x",       float, None)
Config.define("theme", "hopo_indicator_y",       float, None)
Config.define("theme", "hopo_indicator_active_color",   str, "#FFFFFF")
Config.define("theme", "hopo_indicator_inactive_color",   str, "#666666")

#Qstick - Misc
Config.define("theme", "song_list_display",       int, None)

#RACER:
Config.define("theme", "fail_bkg_x",       float, None)
Config.define("theme", "fail_bkg_y",       float, None)
Config.define("theme", "fail_text_x",       float, None)
Config.define("theme", "fail_text_y",       float, None)



backgroundColor = None
baseColor       = None
selectedColor   = None
fretColors      = None
gh3flameColor   = None

hopoColor       = None
spotColor       = None
keyColor        = None
key2Color       = None
tracksColor     = None
barsColor       = None
glowColor       = None

flameColors     = None
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
twoDnote = None
twoDkeys = None
threeDspin = None
opencolor = None
meshColor = None
songback = None
versiontag = None
rmtype = None

#evilynux
songlist_score_colorVar = None
songlistcd_score_colorVar = None
rockmeter_score_colorVar = None
ingame_stats_colorVar = None

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

pause_bkg_xPos = None
pause_bkg_yPos = None
pause_text_xPos = None
pause_text_yPos = None

opt_bkg_xPos = None
opt_bkg_yPos = None
opt_text_xPos = None
opt_text_yPos = None

main_menu_scaleVar = None
main_menu_vspacingVar = None
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
fail_text_colorVar = None
fail_selected_colorVar = None

#MFH - crowd cheer loop delay in theme.ini: if not exist, use value from settings. Otherwise, use theme.ini value.
crowdLoopDelay = None

#MFH - for instrument / difficulty / practice section submenu positioning
songSelectSubmenuX = None
songSelectSubmenuY = None

#TWD - for neck chooser text positionning
neck_prompt_x = None
neck_prompt_y = None

#MFH - for scaling song info during countdown
songInfoDisplayScale = None

#MFH - y offset = lines, x offset = spaces
songSelectSubmenuOffsetLines = None
songSelectSubmenuOffsetSpaces = None

#MFH - option for Rock Band 2 theme.ini - only show # of stars you are working on
displayAllGreyStars = None

#Qstick - hopo indicator position and color
hopoIndicatorX = None
hopoIndicatorY = None
hopoIndicatorActiveColor = None
hopoIndicatorInactiveColor = None

#Qstick - misc
songListDisplay = None

#Racer:
fail_bkg_xPos = None
fail_bkg_yPos = None
fail_text_xPos = None
fail_text_yPos = None



def hexToColor(color):
  if color[0] == "#":
    color = color[1:]
    if len(color) == 3:
      return (int(color[0], 16) / 15.0, int(color[1], 16) / 15.0, int(color[2], 16) / 15.0)
    return (int(color[0:2], 16) / 255.0, int(color[2:4], 16) / 255.0, int(color[4:6], 16) / 255.0)
  elif color.lower() == "off":
    return (-1, -1, -1)
  elif color.lower() == "fret":
    return (-2, -2, -2)
  return (0, 0, 0)
    
def colorToHex(color):
  return "#" + ("".join(["%02x" % int(c * 255) for c in color]))

def setSelectedColor(alpha = 1.0):
  glColor4f(*(selectedColor + (alpha,)))

def setBaseColor(alpha = 1.0):
  glColor4f(*(baseColor + (alpha,)))
  


def open(config):
  # Read in theme.ini specific variables
  
  setupColors(config)
  setupFrets(config)
  setupFlameColors(config)
  setupFlameSizes(config)
  setupSpinny(config)
  setupPOV(config)
  setupMisc(config)
  setupMenu(config)
  setupSonglist(config) #MFH
  setupPauseNOpt(config) #MFH
  setupTWOD(config)
  setupFail(config) #racer
  setupEvilynux(config)
  setupRockmeter(config)
  setupNeckChooser(config)
  setupHopoIndicator(config)
  

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
  global fretColors
    
  if fretColors == None:
    fretColors = [hexToColor(config.get("theme", "fret%d_color" % i)) for i in range(5)]
  else:
    fretColors[0] = hexToColor(config.get("theme", "fret0_color"))
    fretColors[1] = hexToColor(config.get("theme", "fret1_color"))
    fretColors[2] = hexToColor(config.get("theme", "fret2_color"))
    fretColors[3] = hexToColor(config.get("theme", "fret3_color"))
    fretColors[4] = hexToColor(config.get("theme", "fret4_color"))

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
    flameColors[0][5] = hexToColor(config.get("theme", "flame4_1X_color"))
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
    flameSizes[0][5] = config.get("theme", "flame4_1X_size")
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
  global displayAllGreyStars
  global songListDisplay

  loadingPhrase = config.get("theme", "loading_phrase")
  resultsPhrase = config.get("theme", "results_phrase")
  creditSong = config.get("theme", "credit_song")
  crowdLoopDelay = config.get("theme", "crowd_loop_delay")
  songInfoDisplayScale = config.get("theme", "song_info_display_scale")
  displayAllGreyStars = config.get("theme", "display_all_grey_stars")
  songListDisplay = config.get("theme", "song_list_display")

#MFH:
def setupSonglist(config):
  global song_cd_Xpos, song_cdscore_Xpos, song_list_Xpos, song_listscore_Xpos
  global song_listcd_cd_Xpos, song_listcd_cd_Ypos, song_listcd_score_Xpos, song_listcd_score_Ypos, song_listcd_list_Xpos

  global main_menu_scaleVar, main_menu_vspacingVar, sub_menu_xVar, sub_menu_yVar
  global career_title_colorVar, opt_text_colorVar, opt_selected_colorVar
  global song_name_text_colorVar, song_name_selected_colorVar
  global artist_text_colorVar, artist_selected_colorVar
  global library_text_colorVar, library_selected_colorVar
  global pause_text_colorVar, pause_selected_colorVar
  global fail_text_colorVar, fail_selected_colorVar
  global songSelectSubmenuX, songSelectSubmenuY
  global songSelectSubmenuOffsetLines, songSelectSubmenuOffsetSpaces
  
  global song_rb2_name_colorVar, song_rb2_name_selected_colorVar, song_rb2_diff_colorVar, song_rb2_artist_colorVar


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
  main_menu_scaleVar = config.get("theme", "main_menu_scale")
  main_menu_vspacingVar = config.get("theme", "main_menu_vspacing")
  sub_menu_xVar = config.get("theme", "sub_menu_x")
  sub_menu_yVar = config.get("theme", "sub_menu_y")
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
  fail_text_colorVar = config.get("theme", "fail_text_color")
  fail_selected_colorVar = config.get("theme", "fail_selected_color")
  
  song_rb2_name_colorVar = config.get("theme", "song_rb2_name_color")
  song_rb2_name_selected_colorVar = config.get("theme", "song_rb2_name_selected_color")
  song_rb2_diff_colorVar = config.get("theme", "song_rb2_diff_color")
  song_rb2_artist_colorVar = config.get("theme", "song_rb2_artist_color")

  
def setupPauseNOpt(config):
  global pause_bkg_xPos, pause_bkg_yPos, pause_text_xPos, pause_text_yPos
  global opt_bkg_xPos, opt_bkg_yPos, opt_text_xPos, opt_text_yPos

  pause_bkg_xPos = config.get("theme", "pause_bkg_x")
  pause_bkg_yPos = config.get("theme", "pause_bkg_y")
  pause_text_xPos = config.get("theme", "pause_text_x")
  pause_text_yPos = config.get("theme", "pause_text_y")
  opt_bkg_xPos = config.get("theme", "opt_bkg_x")
  opt_bkg_yPos = config.get("theme", "opt_bkg_y")
  opt_text_xPos = config.get("theme", "opt_text_x")
  opt_text_yPos = config.get("theme", "opt_text_y")
  
def setupMenu(config):
  global menuX, menuY, menuRB
  global loadingX, loadingY
  global songback, versiontag
  
  menuX = config.get("theme", "menu_x")
  menuY = config.get("theme", "menu_y")
  menuRB = config.get("theme", "rbmenu")
  loadingX = config.get("theme", "loading_x")
  loadingY = config.get("theme", "loading_y")
  songback = config.get("theme", "songback")
  versiontag = config.get("theme", "versiontag")


def setupTWOD(config):
  global twoDnote, twoDkeys, threeDspin, opencolor
  
  twoDnote = config.get("theme", "twoDnote")
  twoDkeys = config.get("theme", "twoDkeys")
  threeDspin = config.get("theme", "threeDspin")
  opencolor = hexToColor(config.get("theme", "opencolor"))


#racer:
def setupFail(config):
  global fail_bkg_xPos, fail_bkg_yPos, fail_text_xPos, fail_text_yPos

  fail_bkg_xPos = config.get("theme", "fail_bkg_x") 
  fail_bkg_yPos = config.get("theme", "fail_bkg_y")
  fail_text_xPos = config.get("theme", "fail_text_x")
  fail_text_yPos = config.get("theme", "fail_text_y")

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


