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

#DEFAULT_COLOR_BACKGROUND = "#330000"
DEFAULT_COLOR_BACKGROUND = "#000000"
#DEFAULT_COLOR_BASE       = "#FFFF80"
DEFAULT_COLOR_BASE       = "#FFFFFF"
DEFAULT_COLOR_SELECTED   = "#FFBF00"
DEFAULT_COLOR_FRET0      = "#22FF22"
DEFAULT_COLOR_FRET1      = "#FF2222"
DEFAULT_COLOR_FRET2      = "#FFFF22"
DEFAULT_COLOR_FRET3      = "#3333FF"
DEFAULT_COLOR_FRET4      = "#FF9933"

DEFAULT_COLOR_MESH       = "#000000" #blazingamer
DEFAULT_COLOR_HOPO       = "#00AAAA"
DEFAULT_COLOR_SPOT       = "#FFFFFF"
DEFAULT_COLOR_KEY        = "#333333"
DEFAULT_COLOR_KEY2       = "#000000"
DEFAULT_COLOR_TRACKS     = "#FFFF80"
DEFAULT_COLOR_BARS       = "#FFFF80"
DEFAULT_COLOR_GLOW       = "fret"

DEFAULT_COLOR_FLAME0_1X   = "#d5ff82"
DEFAULT_COLOR_FLAME1_1X   = "#ff8880"
DEFAULT_COLOR_FLAME2_1X   = "#faf66b"
DEFAULT_COLOR_FLAME3_1X   = "#a4f8ff"
DEFAULT_COLOR_FLAME4_1X   = "#ffde8c"
DEFAULT_COLOR_FLAME0_2X   = "#d5ff82"
DEFAULT_COLOR_FLAME1_2X   = "#ff8880"
DEFAULT_COLOR_FLAME2_2X   = "#faf66b"
DEFAULT_COLOR_FLAME3_2X   = "#a4f8ff"
DEFAULT_COLOR_FLAME4_2X   = "#ffde8c"
DEFAULT_COLOR_FLAME0_3X   = "#d5ff82"
DEFAULT_COLOR_FLAME1_3X   = "#ff8880"
DEFAULT_COLOR_FLAME2_3X   = "#faf66b"
DEFAULT_COLOR_FLAME3_3X   = "#a4f8ff"
DEFAULT_COLOR_FLAME4_3X   = "#ffde8c"
DEFAULT_COLOR_FLAME0_4X   = "#d5ff82"
DEFAULT_COLOR_FLAME1_4X   = "#ff8880"
DEFAULT_COLOR_FLAME2_4X   = "#faf66b"
DEFAULT_COLOR_FLAME3_4X   = "#a4f8ff"
DEFAULT_COLOR_FLAME4_4X   = "#ffde8c"

GH3_COLOR_FLAME = "#BF6006"

DEFAULT_SIZE_FLAME0_1X   = 0.075
DEFAULT_SIZE_FLAME1_1X   = 0.075
DEFAULT_SIZE_FLAME2_1X   = 0.075
DEFAULT_SIZE_FLAME3_1X   = 0.075
DEFAULT_SIZE_FLAME4_1X   = 0.075
DEFAULT_SIZE_FLAME0_2X   = 0.075
DEFAULT_SIZE_FLAME1_2X   = 0.075
DEFAULT_SIZE_FLAME2_2X   = 0.075
DEFAULT_SIZE_FLAME3_2X   = 0.075
DEFAULT_SIZE_FLAME4_2X   = 0.075
DEFAULT_SIZE_FLAME0_3X   = 0.075
DEFAULT_SIZE_FLAME1_3X   = 0.075
DEFAULT_SIZE_FLAME2_3X   = 0.075
DEFAULT_SIZE_FLAME3_3X   = 0.075
DEFAULT_SIZE_FLAME4_3X   = 0.075
DEFAULT_SIZE_FLAME0_4X   = 0.075
DEFAULT_SIZE_FLAME1_4X   = 0.075
DEFAULT_SIZE_FLAME2_4X   = 0.075
DEFAULT_SIZE_FLAME3_4X   = 0.075
DEFAULT_SIZE_FLAME4_4X   = 0.075

DEFAULT_SPINNY           = False

DEFAULT_X_TARGET_POV     = 0.0
DEFAULT_Y_TARGET_POV     = 0.0
DEFAULT_Z_TARGET_POV     = 4.0

DEFAULT_X_ORIGIN_POV     = 0.0
DEFAULT_Y_ORIGIN_POV     = 3.0
DEFAULT_Z_ORIGIN_POV     = -3.0

DEFAULT_PHRASE_LOADING   = None
DEFAULT_PHRASE_RESULTS   = None
DEFAULT_SONG_CREDIT      = "Unknown"

#blazingamer
DEFAULT_X_MENU           = None
DEFAULT_Y_MENU           = None

DEFAULT_X_loading        = None
DEFAULT_Y_loading        = None

DEFAULT_TWODNOTE         = True
DEFAULT_TWODKEYS         = True
DEFAULT_THREEDSPIN       = True
DEFAULT_COLOR_OPEN      = "#FF9933"

DEFAULT_SONGBACK         = False
DEFAULT_VERSIONTAG       = False
DEFAULT_RMTYPE           = None

#evilynux
DEFAULT_ROCKMETER_SCORE_COLOR = "#93C351"
DEFAULT_INGAME_STATS_COLOR = "#FFFFFF"
DEFAULT_SONGLIST_SCORE_COLOR = "#FFFFFF" # evilynux - score color

#MFH:
DEFAULT_SONGCDX         = None
DEFAULT_SONGCDSCOREX    = None
DEFAULT_SONGLISTX       = None
DEFAULT_SONGLISTSCOREX  = None

DEFAULT_PAUSE_BKG_X     = None
DEFAULT_PAUSE_BKG_Y     = None
DEFAULT_PAUSE_TEXT_X    = None
DEFAULT_PAUSE_TEXT_Y    = None

DEFAULT_OPT_BKG_X     = None
DEFAULT_OPT_BKG_Y     = None
DEFAULT_OPT_TEXT_X    = None
DEFAULT_OPT_TEXT_Y    = None

#MFH:
DEFAULT_MAIN_MENU_SCALE = None
DEFAULT_MAIN_MENU_VSPACING = None

DEFAULT_SUB_MENU_XPOS = None
DEFAULT_SUB_MENU_YPOS = None

DEFAULT_CAREER_TITLE_COLOR = "#000000"
DEFAULT_OPT_TEXT_COLOR = "#FFFFFF"
DEFAULT_OPT_SELECTED_COLOR = "#FFBF00"
DEFAULT_SONG_NAME_TEXT_COLOR = "#FFFFFF"
DEFAULT_SONG_NAME_SELECTED_COLOR = "#FFBF00"
DEFAULT_ARTIST_TEXT_COLOR = "#4080FF"
DEFAULT_ARTIST_SELECTED_COLOR = "#4080FF"
DEFAULT_LIBRARY_TEXT_COLOR = "#FFFFFF"
DEFAULT_LIBRARY_SELECTED_COLOR = "#FFBF00"
DEFAULT_PAUSE_TEXT_COLOR = "#FFFFFF"
DEFAULT_PAUSE_SELECTED_COLOR = "#FFBF00"
DEFAULT_FAIL_TEXT_COLOR = "#FFFFFF"
DEFAULT_FAIL_SELECTED_COLOR = "#FFBF00"

#MFH - crowd cheer loop delay in theme.ini: if not exist, use value from settings. Otherwise, use theme.ini value.
DEFAULT_CROWD_LOOP_DELAY = None

#MFH - for instrument / difficulty / practice section submenu positioning
DEFAULT_SONG_SELECT_SUBMENU_X = None
DEFAULT_SONG_SELECT_SUBMENU_Y = None


#racer:
DEFAULT_FAIL_BKG_X     = None
DEFAULT_FAIL_BKG_Y     = None
DEFAULT_FAIL_TEXT_X    = None
DEFAULT_FAIL_TEXT_Y    = None




# read the color scheme from the config file
Config.define("theme", "background_color",  str, DEFAULT_COLOR_BACKGROUND)
Config.define("theme", "base_color",        str, DEFAULT_COLOR_BASE)
Config.define("theme", "selected_color",    str, DEFAULT_COLOR_SELECTED)

Config.define("theme", "mesh_color",        str, DEFAULT_COLOR_MESH)#blazingamer
Config.define("theme", "hopo_color",        str, DEFAULT_COLOR_HOPO)
Config.define("theme", "spot_color",        str, DEFAULT_COLOR_SPOT)
Config.define("theme", "key_color",         str, DEFAULT_COLOR_KEY)
Config.define("theme", "key2_color",        str, DEFAULT_COLOR_KEY2)
Config.define("theme", "tracks_color",      str, DEFAULT_COLOR_TRACKS)
Config.define("theme", "bars_color",        str, DEFAULT_COLOR_BARS)
Config.define("theme", "glow_color",        str, DEFAULT_COLOR_GLOW)

Config.define("theme", "loading_phrase",    str, DEFAULT_PHRASE_LOADING)
Config.define("theme", "results_phrase",    str, DEFAULT_PHRASE_RESULTS)
Config.define("theme", "credit_song",       str, DEFAULT_SONG_CREDIT)

Config.define("theme", "fret0_color",       str, DEFAULT_COLOR_FRET0)
Config.define("theme", "fret1_color",       str, DEFAULT_COLOR_FRET1)
Config.define("theme", "fret2_color",       str, DEFAULT_COLOR_FRET2)
Config.define("theme", "fret3_color",       str, DEFAULT_COLOR_FRET3)
Config.define("theme", "fret4_color",       str, DEFAULT_COLOR_FRET4)

Config.define("theme", "flame0_1X_color",    str, DEFAULT_COLOR_FLAME0_1X)
Config.define("theme", "flame1_1X_color",    str, DEFAULT_COLOR_FLAME1_1X)
Config.define("theme", "flame2_1X_color",    str, DEFAULT_COLOR_FLAME2_1X)
Config.define("theme", "flame3_1X_color",    str, DEFAULT_COLOR_FLAME3_1X)
Config.define("theme", "flame4_1X_color",    str, DEFAULT_COLOR_FLAME4_1X)
Config.define("theme", "flame0_2X_color",    str, DEFAULT_COLOR_FLAME0_2X)
Config.define("theme", "flame1_2X_color",    str, DEFAULT_COLOR_FLAME1_2X)
Config.define("theme", "flame2_2X_color",    str, DEFAULT_COLOR_FLAME2_2X)
Config.define("theme", "flame3_2X_color",    str, DEFAULT_COLOR_FLAME3_2X)
Config.define("theme", "flame4_2X_color",    str, DEFAULT_COLOR_FLAME4_2X)
Config.define("theme", "flame0_3X_color",    str, DEFAULT_COLOR_FLAME0_3X)
Config.define("theme", "flame1_3X_color",    str, DEFAULT_COLOR_FLAME1_3X)
Config.define("theme", "flame2_3X_color",    str, DEFAULT_COLOR_FLAME2_3X)
Config.define("theme", "flame3_3X_color",    str, DEFAULT_COLOR_FLAME3_3X)
Config.define("theme", "flame4_3X_color",    str, DEFAULT_COLOR_FLAME4_3X)
Config.define("theme", "flame0_4X_color",    str, DEFAULT_COLOR_FLAME0_4X)
Config.define("theme", "flame1_4X_color",    str, DEFAULT_COLOR_FLAME1_4X)
Config.define("theme", "flame2_4X_color",    str, DEFAULT_COLOR_FLAME2_4X)
Config.define("theme", "flame3_4X_color",    str, DEFAULT_COLOR_FLAME3_4X)
Config.define("theme", "flame4_4X_color",    str, DEFAULT_COLOR_FLAME4_4X)

Config.define("theme", "flame_gh3_color",    str, GH3_COLOR_FLAME)

Config.define("theme", "flame0_1X_size",     float, DEFAULT_SIZE_FLAME0_1X)
Config.define("theme", "flame1_1X_size",     float, DEFAULT_SIZE_FLAME1_1X)
Config.define("theme", "flame2_1X_size",     float, DEFAULT_SIZE_FLAME2_1X)
Config.define("theme", "flame3_1X_size",     float, DEFAULT_SIZE_FLAME3_1X)
Config.define("theme", "flame4_1X_size",     float, DEFAULT_SIZE_FLAME4_1X)
Config.define("theme", "flame0_2X_size",     float, DEFAULT_SIZE_FLAME0_2X)
Config.define("theme", "flame1_2X_size",     float, DEFAULT_SIZE_FLAME1_2X)
Config.define("theme", "flame2_2X_size",     float, DEFAULT_SIZE_FLAME2_2X)
Config.define("theme", "flame3_2X_size",     float, DEFAULT_SIZE_FLAME3_2X)
Config.define("theme", "flame4_2X_size",     float, DEFAULT_SIZE_FLAME4_2X)
Config.define("theme", "flame0_3X_size",     float, DEFAULT_SIZE_FLAME0_3X)
Config.define("theme", "flame1_3X_size",     float, DEFAULT_SIZE_FLAME1_3X)
Config.define("theme", "flame2_3X_size",     float, DEFAULT_SIZE_FLAME2_3X)
Config.define("theme", "flame3_3X_size",     float, DEFAULT_SIZE_FLAME3_3X)
Config.define("theme", "flame4_3X_size",     float, DEFAULT_SIZE_FLAME4_3X)
Config.define("theme", "flame0_4X_size",     float, DEFAULT_SIZE_FLAME0_4X)
Config.define("theme", "flame1_4X_size",     float, DEFAULT_SIZE_FLAME1_4X)
Config.define("theme", "flame2_4X_size",     float, DEFAULT_SIZE_FLAME2_4X)
Config.define("theme", "flame3_4X_size",     float, DEFAULT_SIZE_FLAME3_4X)
Config.define("theme", "flame4_4X_size",     float, DEFAULT_SIZE_FLAME4_4X)

Config.define("theme", "disable_song_spinny",    bool, DEFAULT_SPINNY)
Config.define("theme", "disable_editor_spinny",  bool, DEFAULT_SPINNY)
Config.define("theme", "disable_results_spinny", bool, DEFAULT_SPINNY)
Config.define("theme", "disable_menu_spinny",    bool, DEFAULT_SPINNY)

Config.define("theme", "pov_target_x",       float, DEFAULT_X_TARGET_POV)
Config.define("theme", "pov_target_y",       float, DEFAULT_Y_TARGET_POV)
Config.define("theme", "pov_target_z",       float, DEFAULT_Z_TARGET_POV)

Config.define("theme", "pov_origin_x",       float, DEFAULT_X_ORIGIN_POV)
Config.define("theme", "pov_origin_y",       float, DEFAULT_Y_ORIGIN_POV)
Config.define("theme", "pov_origin_z",       float, DEFAULT_Z_ORIGIN_POV)

#blazingamer
Config.define("theme", "menu_x",       float, DEFAULT_X_MENU)
Config.define("theme", "menu_y",       float, DEFAULT_Y_MENU)

Config.define("theme", "loading_x",       float, DEFAULT_X_loading)
Config.define("theme", "loading_y",       float, DEFAULT_Y_loading)

Config.define("theme", "twoDnote",       bool, DEFAULT_TWODNOTE)
Config.define("theme", "twoDkeys",       bool, DEFAULT_TWODKEYS)
Config.define("theme", "threeDspin",       bool, DEFAULT_THREEDSPIN)
Config.define("theme", "opencolor",       str, DEFAULT_COLOR_OPEN)

Config.define("theme", "songback",       bool, DEFAULT_SONGBACK)
Config.define("theme", "versiontag",       bool, DEFAULT_VERSIONTAG)
Config.define("theme", "rmtype",       int, DEFAULT_RMTYPE)

#evilynux
Config.define("theme", "songlist_score_color",  str, DEFAULT_SONGLIST_SCORE_COLOR)
Config.define("theme", "rockmeter_score_color",  str, DEFAULT_ROCKMETER_SCORE_COLOR)
Config.define("theme", "ingame_stats_color",  str, DEFAULT_INGAME_STATS_COLOR)

#MFH
Config.define("theme", "song_cd_x",       float, DEFAULT_SONGCDX)
Config.define("theme", "song_cdscore_x",       float, DEFAULT_SONGCDSCOREX)
Config.define("theme", "song_list_x",       float, DEFAULT_SONGLISTX)
Config.define("theme", "song_listscore_x",       float, DEFAULT_SONGLISTSCOREX)

Config.define("theme", "pause_bkg_x",       float, DEFAULT_PAUSE_BKG_X)
Config.define("theme", "pause_bkg_y",       float, DEFAULT_PAUSE_BKG_Y)
Config.define("theme", "pause_text_x",       float, DEFAULT_PAUSE_TEXT_X)
Config.define("theme", "pause_text_y",       float, DEFAULT_PAUSE_TEXT_Y)

Config.define("theme", "opt_bkg_x",       float, DEFAULT_OPT_BKG_X)
Config.define("theme", "opt_bkg_y",       float, DEFAULT_OPT_BKG_Y)
Config.define("theme", "opt_text_x",       float, DEFAULT_OPT_TEXT_X)
Config.define("theme", "opt_text_y",       float, DEFAULT_OPT_TEXT_Y)
Config.define("theme", "opt_text_color",  str, DEFAULT_OPT_TEXT_COLOR)
Config.define("theme", "opt_selected_color",  str, DEFAULT_OPT_SELECTED_COLOR)


Config.define("theme", "main_menu_scale",       float, DEFAULT_MAIN_MENU_SCALE)
Config.define("theme", "main_menu_vspacing",       float, DEFAULT_MAIN_MENU_VSPACING)
Config.define("theme", "sub_menu_x",       float, DEFAULT_SUB_MENU_XPOS)
Config.define("theme", "sub_menu_y",       float, DEFAULT_SUB_MENU_YPOS)

Config.define("theme", "career_title_color",  str, DEFAULT_CAREER_TITLE_COLOR)
Config.define("theme", "song_name_text_color",  str, DEFAULT_SONG_NAME_TEXT_COLOR)
Config.define("theme", "song_name_selected_color",  str, DEFAULT_SONG_NAME_SELECTED_COLOR)
Config.define("theme", "artist_text_color",  str, DEFAULT_ARTIST_TEXT_COLOR)
Config.define("theme", "artist_selected_color",  str, DEFAULT_ARTIST_SELECTED_COLOR)
Config.define("theme", "library_text_color",  str, DEFAULT_LIBRARY_TEXT_COLOR)
Config.define("theme", "library_selected_color",  str, DEFAULT_LIBRARY_SELECTED_COLOR)

Config.define("theme", "pause_text_color",  str, DEFAULT_PAUSE_TEXT_COLOR)
Config.define("theme", "pause_selected_color",  str, DEFAULT_PAUSE_SELECTED_COLOR)
Config.define("theme", "fail_text_color",  str, DEFAULT_FAIL_TEXT_COLOR)
Config.define("theme", "fail_selected_color",  str, DEFAULT_FAIL_SELECTED_COLOR)

#MFH - crowd cheer loop delay in theme.ini: if not exist, use value from settings. Otherwise, use theme.ini value.
Config.define("theme", "crowd_loop_delay",  int, DEFAULT_CROWD_LOOP_DELAY)

#MFH - for instrument / difficulty / practice section submenu positioning
Config.define("theme", "song_select_submenu_x",  int, DEFAULT_SONG_SELECT_SUBMENU_X)
Config.define("theme", "song_select_submenu_y",  int, DEFAULT_SONG_SELECT_SUBMENU_Y)

#RACER:
Config.define("theme", "fail_bkg_x",       float, DEFAULT_FAIL_BKG_X)
Config.define("theme", "fail_bkg_y",       float, DEFAULT_FAIL_BKG_Y)
Config.define("theme", "fail_text_x",       float, DEFAULT_FAIL_TEXT_X)
Config.define("theme", "fail_text_y",       float, DEFAULT_FAIL_TEXT_Y)



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
rockmeter_score_colorVar = None
ingame_stats_colorVar = None

#MFH:
song_cd_Xpos = None         #Songlist in CD mode: horizontal position of CDs/cases
song_cdscore_Xpos = None    #Songlist in CD mode: horizontal position of score info
song_list_Xpos = None       #Songlist in List mode: horizontal position of song names/artists
song_listscore_Xpos = None  #Songlist in List mode: horizontal position of score info

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

pause_text_colorVar = None
pause_selected_colorVar = None
fail_text_colorVar = None
fail_selected_colorVar = None

#MFH - crowd cheer loop delay in theme.ini: if not exist, use value from settings. Otherwise, use theme.ini value.
crowdLoopDelay = None

#MFH - for instrument / difficulty / practice section submenu positioning
songSelectSubmenuX = None
songSelectSubmenuY = None

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

def setupColors(config):
  global backgroundColor, baseColor, selectedColor
  global hopoColor, spotColor, meshColor
  global keyColor, key2Color
  global tracksColor, barsColor, glowColor
  
  temp = config.get("theme", "background_color")
  if backgroundColor == None or temp != DEFAULT_COLOR_BACKGROUND:
    backgroundColor = hexToColor(temp)  

  temp = config.get("theme", "base_color")
  if baseColor == None or temp != DEFAULT_COLOR_BASE:
    baseColor = hexToColor(temp)

  temp = config.get("theme", "selected_color")
  if selectedColor == None or temp != DEFAULT_COLOR_SELECTED:
    selectedColor = hexToColor(temp)

  temp = config.get("theme", "mesh_color")
  if meshColor == None or temp != DEFAULT_COLOR_MESH:
    meshColor = hexToColor(temp)

  temp = config.get("theme", "hopo_color")
  if hopoColor == None or temp != DEFAULT_COLOR_HOPO:
    hopoColor = hexToColor(temp)

  temp = config.get("theme", "spot_color")
  if spotColor == None or temp != DEFAULT_COLOR_SPOT:
    spotColor = hexToColor(temp)

  temp = config.get("theme", "key_color")
  if keyColor == None or temp != DEFAULT_COLOR_KEY:
    keyColor = hexToColor(temp)

  temp = config.get("theme", "key2_color")
  if key2Color == None or temp != DEFAULT_COLOR_KEY2:
    key2Color = hexToColor(temp)    

  temp = config.get("theme", "tracks_color")
  if tracksColor == None or temp != DEFAULT_COLOR_TRACKS:
    tracksColor = hexToColor(temp)

  temp = config.get("theme", "bars_color")
  if barsColor == None or temp != DEFAULT_COLOR_BARS:
    barsColor = hexToColor(temp)    

  temp = config.get("theme", "glow_color")
  if glowColor == None or temp != DEFAULT_COLOR_GLOW:
    glowColor = hexToColor(temp)
    
def setupFrets(config):
  global fretColors
    
  if fretColors == None:
    fretColors = [hexToColor(config.get("theme", "fret%d_color" % i)) for i in range(5)]
  else:
    temp = config.get("theme", "fret0_color")
    if temp != DEFAULT_COLOR_FRET0:
      fretColors[0] = hexToColor(temp)

    temp = config.get("theme", "fret1_color")
    if temp != DEFAULT_COLOR_FRET1:
      fretColors[1] = hexToColor(temp)

    temp = config.get("theme", "fret2_color")
    if temp != DEFAULT_COLOR_FRET2:
      fretColors[2] = hexToColor(temp)

    temp = config.get("theme", "fret3_color")
    if temp != DEFAULT_COLOR_FRET3:
      fretColors[3] = hexToColor(temp)

    temp = config.get("theme", "fret4_color")
    if temp != DEFAULT_COLOR_FRET4:
      fretColors[4] = hexToColor(temp)

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
    temp = config.get("theme", "flame0_1X_color")
    if temp != DEFAULT_COLOR_FLAME0_1X:
      flameColors[0][0] = hexToColor(temp)

    temp = config.get("theme", "flame1_1X_color")
    if temp != DEFAULT_COLOR_FLAME1_1X:
      flameColors[0][1] = hexToColor(temp)

    temp = config.get("theme", "flame2_1X_color")
    if temp != DEFAULT_COLOR_FLAME2_1X:
      flameColors[0][2] = hexToColor(temp)

    temp = config.get("theme", "flame3_1X_color")
    if temp != DEFAULT_COLOR_FLAME3_1X:
      flameColors[0][3] = hexToColor(temp)

    temp = config.get("theme", "flame4_1X_color")
    if temp != DEFAULT_COLOR_FLAME4_1X:
      flameColors[0][4] = hexToColor(temp)
      
    temp = config.get("theme", "flame0_2X_color")
    if temp != DEFAULT_COLOR_FLAME0_2X:
      flameColors[1][0] = hexToColor(temp)

    temp = config.get("theme", "flame1_2X_color")
    if temp != DEFAULT_COLOR_FLAME1_2X:
      flameColors[1][1] = hexToColor(temp)

    temp = config.get("theme", "flame2_2X_color")
    if temp != DEFAULT_COLOR_FLAME2_2X:
      flameColors[1][2] = hexToColor(temp)

    temp = config.get("theme", "flame3_2X_color")
    if temp != DEFAULT_COLOR_FLAME3_2X:
      flameColors[1][3] = hexToColor(temp)

    temp = config.get("theme", "flame4_2X_color")
    if temp != DEFAULT_COLOR_FLAME4_2X:
      flameColors[1][4] = hexToColor(temp)
      
    temp = config.get("theme", "flame0_3X_color")
    if temp != DEFAULT_COLOR_FLAME0_3X:
      flameColors[2][0] = hexToColor(temp)

    temp = config.get("theme", "flame1_3X_color")
    if temp != DEFAULT_COLOR_FLAME1_3X:
      flameColors[2][1] = hexToColor(temp)

    temp = config.get("theme", "flame2_3X_color")
    if temp != DEFAULT_COLOR_FLAME2_3X:
      flameColors[2][2] = hexToColor(temp)

    temp = config.get("theme", "flame3_3X_color")
    if temp != DEFAULT_COLOR_FLAME3_3X:
      flameColors[2][3] = hexToColor(temp)

    temp = config.get("theme", "flame4_3X_color")
    if temp != DEFAULT_COLOR_FLAME4_3X:
      flameColors[2][4] = hexToColor(temp)

    temp = config.get("theme", "flame0_4X_color")
    if temp != DEFAULT_COLOR_FLAME0_4X:
      flameColors[3][0] = hexToColor(temp)

    temp = config.get("theme", "flame1_4X_color")
    if temp != DEFAULT_COLOR_FLAME1_4X:
      flameColors[3][1] = hexToColor(temp)

    temp = config.get("theme", "flame2_4X_color")
    if temp != DEFAULT_COLOR_FLAME2_4X:
      flameColors[3][2] = hexToColor(temp)

    temp = config.get("theme", "flame3_4X_color")
    if temp != DEFAULT_COLOR_FLAME3_4X:
      flameColors[3][3] = hexToColor(temp)

    temp = config.get("theme", "flame4_4X_color")
    if temp != DEFAULT_COLOR_FLAME4_4X:
      flameColors[3][4] = hexToColor(temp)
        
def setupFlameSizes(config):
  global flameSizes

  if flameSizes == None:
    flameSizes = [[config.get("theme", "flame%d_1X_size" % i) for i in range(5)]]
    flameSizes.append([config.get("theme", "flame%d_2X_size" % i) for i in range(5)])
    flameSizes.append([config.get("theme", "flame%d_3X_size" % i) for i in range(5)])
    flameSizes.append([config.get("theme", "flame%d_4X_size" % i) for i in range(5)])
  else:
    temp = config.get("theme", "flame0_1X_size")
    if temp != DEFAULT_SIZE_FLAME0_1X:
      flameSizes[0][0] = temp
      
    temp = config.get("theme", "flame1_1X_size")
    if temp != DEFAULT_SIZE_FLAME1_1X:
      flameSizes[0][1] = temp
      
    temp = config.get("theme", "flame2_1X_size")
    if temp != DEFAULT_SIZE_FLAME2_1X:
      flameSizes[0][2] = temp
      
    temp = config.get("theme", "flame3_1X_size")
    if temp != DEFAULT_SIZE_FLAME3_1X:
      flameSizes[0][3] = temp
      
    temp = config.get("theme", "flame4_1X_size")
    if temp != DEFAULT_SIZE_FLAME4_1X:
      flameSizes[0][4] = temp

    temp = config.get("theme", "flame0_2X_size")
    if temp != DEFAULT_SIZE_FLAME0_2X:
      flameSizes[1][0] = temp
      
    temp = config.get("theme", "flame1_2X_size")
    if temp != DEFAULT_SIZE_FLAME1_2X:
      flameSizes[1][1] = temp
      
    temp = config.get("theme", "flame2_2X_size")
    if temp != DEFAULT_SIZE_FLAME2_2X:
      flameSizes[1][2] = temp
      
    temp = config.get("theme", "flame3_2X_size")
    if temp != DEFAULT_SIZE_FLAME3_2X:
      flameSizes[1][3] = temp
      
    temp = config.get("theme", "flame4_2X_size")
    if temp != DEFAULT_SIZE_FLAME4_2X:
      flameSizes[1][4] = temp

    temp = config.get("theme", "flame0_3X_size")
    if temp != DEFAULT_SIZE_FLAME0_3X:
      flameSizes[2][0] = temp
      
    temp = config.get("theme", "flame1_3X_size")
    if temp != DEFAULT_SIZE_FLAME1_3X:
      flameSizes[2][1] = temp
      
    temp = config.get("theme", "flame2_3X_size")
    if temp != DEFAULT_SIZE_FLAME2_3X:
      flameSizes[2][2] = temp
      
    temp = config.get("theme", "flame3_3X_size")
    if temp != DEFAULT_SIZE_FLAME3_3X:
      flameSizes[2][3] = temp
      
    temp = config.get("theme", "flame4_3X_size")
    if temp != DEFAULT_SIZE_FLAME4_3X:
      flameSizes[2][4] = temp

    temp = config.get("theme", "flame0_4X_size")
    if temp != DEFAULT_SIZE_FLAME0_4X:
      flameSizes[3][0] = temp
      
    temp = config.get("theme", "flame1_4X_size")
    if temp != DEFAULT_SIZE_FLAME1_4X:
      flameSizes[3][1] = temp
      
    temp = config.get("theme", "flame2_4X_size")
    if temp != DEFAULT_SIZE_FLAME2_4X:
      flameSizes[3][2] = temp
      
    temp = config.get("theme", "flame3_4X_size")
    if temp != DEFAULT_SIZE_FLAME3_4X:
      flameSizes[3][3] = temp
      
    temp = config.get("theme", "flame4_4X_size")
    if temp != DEFAULT_SIZE_FLAME4_4X:
      flameSizes[3][4] = temp

def setupSpinny(config):
  global spinnySongDisabled, spinnyEditorDisabled, spinnyResultsDisabled, spinnyMenuDisabled

  temp = config.get("theme", "disable_song_spinny")
  if spinnySongDisabled == None or temp != DEFAULT_SPINNY:
    spinnySongDisabled = temp

  temp = config.get("theme", "disable_editor_spinny")
  if spinnyEditorDisabled == None or temp != DEFAULT_SPINNY:
    spinnyEditorDisabled = temp
    
  temp = config.get("theme", "disable_results_spinny")
  if spinnyResultsDisabled == None or temp != DEFAULT_SPINNY:
    spinnyResultsDisabled = temp
    
  temp = config.get("theme", "disable_menu_spinny")
  if spinnyMenuDisabled == None or temp != DEFAULT_SPINNY:
    spinnyMenuDisabled = temp

def setupPOV(config):
  global povTargetX, povTargetY, povTargetZ
  global povOriginX, povOriginY, povOriginZ
  
  temp = config.get("theme", "pov_target_x")
  if povTargetX == None or temp != DEFAULT_X_TARGET_POV:
    povTargetX = temp  

  temp = config.get("theme", "pov_target_y")
  if povTargetY == None or temp != DEFAULT_Y_TARGET_POV:
    povTargetY = temp

  temp = config.get("theme", "pov_target_z")
  if povTargetZ == None or temp != DEFAULT_Z_TARGET_POV:
    povTargetZ = temp

  temp = config.get("theme", "pov_origin_x")
  if povOriginX == None or temp != DEFAULT_X_ORIGIN_POV:
    povOriginX = temp  

  temp = config.get("theme", "pov_origin_y")
  if povOriginY == None or temp != DEFAULT_Y_ORIGIN_POV:
    povOriginY = temp

  temp = config.get("theme", "pov_origin_z")
  if povOriginZ == None or temp != DEFAULT_Z_ORIGIN_POV:
    povOriginZ = temp

def setupMisc(config):
  global loadingPhrase, resultsPhrase
  global creditSong
  global crowdLoopDelay

  temp = config.get("theme", "loading_phrase")
  #Log.debug("Loading phrases found: " + temp)
  if loadingPhrase == None or temp != DEFAULT_PHRASE_LOADING:
    loadingPhrase = temp

  temp = config.get("theme", "results_phrase")
  if resultsPhrase == None or temp != DEFAULT_PHRASE_RESULTS:
    resultsPhrase = temp

  temp = config.get("theme", "credit_song")
  if creditSong == None or temp != DEFAULT_SONG_CREDIT:
    creditSong = temp

  #MFH - crowd cheer loop delay in theme.ini: if not exist, use value from settings. Otherwise, use theme.ini value.
  temp = config.get("theme", "crowd_loop_delay")
  if crowdLoopDelay == None or temp != DEFAULT_CROWD_LOOP_DELAY:
    crowdLoopDelay = temp



#MFH:
def setupSonglist(config):
  global song_cd_Xpos, song_cdscore_Xpos, song_list_Xpos, song_listscore_Xpos

  global main_menu_scaleVar, main_menu_vspacingVar, sub_menu_xVar, sub_menu_yVar
  global career_title_colorVar, opt_text_colorVar, opt_selected_colorVar
  global song_name_text_colorVar, song_name_selected_colorVar
  global artist_text_colorVar, artist_selected_colorVar
  global library_text_colorVar, library_selected_colorVar
  global pause_text_colorVar, pause_selected_colorVar
  global fail_text_colorVar, fail_selected_colorVar
  global songSelectSubmenuX, songSelectSubmenuY

#MFH - for instrument / difficulty / practice section submenu positioning
  temp = config.get("theme", "song_select_submenu_x")
  if songSelectSubmenuX == None or temp != DEFAULT_SONG_SELECT_SUBMENU_X:
    songSelectSubmenuX = temp  

  temp = config.get("theme", "song_select_submenu_y")
  if songSelectSubmenuY == None or temp != DEFAULT_SONG_SELECT_SUBMENU_Y:
    songSelectSubmenuY = temp  

  temp = config.get("theme", "song_cd_x")
  if song_cd_Xpos == None or temp != DEFAULT_SONGCDX:
    song_cd_Xpos = temp  

  temp = config.get("theme", "song_cdscore_x")
  if song_cdscore_Xpos == None or temp != DEFAULT_SONGCDSCOREX:
    song_cdscore_Xpos = temp  

  temp = config.get("theme", "song_list_x")
  if song_list_Xpos == None or temp != DEFAULT_SONGLISTX:
    song_list_Xpos = temp  

  temp = config.get("theme", "song_listscore_x")
  if song_listscore_Xpos == None or temp != DEFAULT_SONGLISTSCOREX:
    song_listscore_Xpos = temp  

  #MFH - adding new options here
  temp = config.get("theme", "main_menu_scale")
  if main_menu_scaleVar == None or temp != DEFAULT_MAIN_MENU_SCALE:
    main_menu_scaleVar = temp  

  temp = config.get("theme", "main_menu_vspacing")
  if main_menu_vspacingVar == None or temp != DEFAULT_MAIN_MENU_VSPACING:
    main_menu_vspacingVar = temp  

  temp = config.get("theme", "sub_menu_x")
  if sub_menu_xVar == None or temp != DEFAULT_SUB_MENU_XPOS:
    sub_menu_xVar = temp  

  temp = config.get("theme", "sub_menu_y")
  if sub_menu_yVar == None or temp != DEFAULT_SUB_MENU_YPOS:
    sub_menu_yVar = temp  

  temp = config.get("theme", "career_title_color")
  if career_title_colorVar == None or temp != DEFAULT_CAREER_TITLE_COLOR:
    career_title_colorVar = temp  

  temp = config.get("theme", "opt_text_color")
  if opt_text_colorVar == None or temp != DEFAULT_OPT_TEXT_COLOR:
    opt_text_colorVar = temp  

  temp = config.get("theme", "opt_selected_color")
  if opt_selected_colorVar == None or temp != DEFAULT_OPT_SELECTED_COLOR:
    opt_selected_colorVar = temp  

  temp = config.get("theme", "song_name_text_color")
  if song_name_text_colorVar == None or temp != DEFAULT_SONG_NAME_TEXT_COLOR:
    song_name_text_colorVar = temp  

  temp = config.get("theme", "song_name_selected_color")
  if song_name_selected_colorVar == None or temp != DEFAULT_SONG_NAME_SELECTED_COLOR:
    song_name_selected_colorVar = temp  

  temp = config.get("theme", "artist_text_color")
  if artist_text_colorVar == None or temp != DEFAULT_ARTIST_TEXT_COLOR:
    artist_text_colorVar = temp  

  temp = config.get("theme", "artist_selected_color")
  if artist_selected_colorVar == None or temp != DEFAULT_ARTIST_SELECTED_COLOR:
    artist_selected_colorVar = temp  

  temp = config.get("theme", "library_text_color")
  if library_text_colorVar == None or temp != DEFAULT_LIBRARY_TEXT_COLOR:
    library_text_colorVar = temp  

  temp = config.get("theme", "library_selected_color")
  if library_selected_colorVar == None or temp != DEFAULT_LIBRARY_SELECTED_COLOR:
    library_selected_colorVar = temp  

  temp = config.get("theme", "pause_text_color")
  if pause_text_colorVar == None or temp != DEFAULT_PAUSE_TEXT_COLOR:
    pause_text_colorVar = temp  

  temp = config.get("theme", "pause_selected_color")
  if pause_selected_colorVar == None or temp != DEFAULT_PAUSE_SELECTED_COLOR:
    pause_selected_colorVar = temp  

  temp = config.get("theme", "fail_text_color")
  if fail_text_colorVar == None or temp != DEFAULT_FAIL_TEXT_COLOR:
    fail_text_colorVar = temp  

  temp = config.get("theme", "fail_selected_color")
  if fail_selected_colorVar == None or temp != DEFAULT_FAIL_SELECTED_COLOR:
    fail_selected_colorVar = temp  

def setupPauseNOpt(config):
  global pause_bkg_xPos, pause_bkg_yPos, pause_text_xPos, pause_text_yPos
  global opt_bkg_xPos, opt_bkg_yPos, opt_text_xPos, opt_text_yPos

  temp = config.get("theme", "pause_bkg_x")
  if pause_bkg_xPos == None or temp != DEFAULT_PAUSE_BKG_X:
    pause_bkg_xPos = temp  

  temp = config.get("theme", "pause_bkg_y")
  if pause_bkg_yPos == None or temp != DEFAULT_PAUSE_BKG_Y:
    pause_bkg_yPos = temp  

  temp = config.get("theme", "pause_text_x")
  if pause_text_xPos == None or temp != DEFAULT_PAUSE_TEXT_X:
    pause_text_xPos = temp  

  temp = config.get("theme", "pause_text_y")
  if pause_text_yPos == None or temp != DEFAULT_PAUSE_TEXT_Y:
    pause_text_yPos = temp  

  temp = config.get("theme", "opt_bkg_x")
  if opt_bkg_xPos == None or temp != DEFAULT_OPT_BKG_X:
    opt_bkg_xPos = temp  

  temp = config.get("theme", "opt_bkg_y")
  if opt_bkg_yPos == None or temp != DEFAULT_OPT_BKG_Y:
    opt_bkg_yPos = temp  

  temp = config.get("theme", "opt_text_x")
  if opt_text_xPos == None or temp != DEFAULT_OPT_TEXT_X:
    opt_text_xPos = temp  

  temp = config.get("theme", "opt_text_y")
  if opt_text_yPos == None or temp != DEFAULT_OPT_TEXT_Y:
    opt_text_yPos = temp  


def setupMenu(config):
  global menuX, menuY
  global loadingX, loadingY
  global songback, versiontag
  
  temp = config.get("theme", "menu_x")
  if menuX == None or temp != DEFAULT_X_MENU:
    menuX = temp  

  temp = config.get("theme", "menu_y")
  if menuY == None or temp != DEFAULT_Y_MENU:
    menuY = temp

  temp = config.get("theme", "loading_x")
  if loadingX == None or temp != DEFAULT_X_loading:
    loadingX = temp  

  temp = config.get("theme", "loading_y")
  if loadingY == None or temp != DEFAULT_Y_loading:
    loadingY = temp

  temp = config.get("theme", "songback")
  if songback == None or temp != DEFAULT_SONGBACK:
    songback = temp

  temp = config.get("theme", "versiontag")
  if versiontag == None or temp != DEFAULT_VERSIONTAG:
    versiontag = temp

def setupTWOD(config):
  global twoDnote, twoDkeys, threeDspin, opencolor
  
  temp = config.get("theme", "twoDnote")
  if twoDnote == None or temp != DEFAULT_TWODNOTE:
    twoDnote = temp  

  temp = config.get("theme", "twoDkeys")
  if twoDkeys == None or temp != DEFAULT_TWODKEYS:
    twoDkeys = temp

  temp = config.get("theme", "threeDspin")
  if threeDspin == None or temp != DEFAULT_THREEDSPIN:
    threeDspin = temp

  temp = config.get("theme", "opencolor")
  if opencolor == None or temp != DEFAULT_COLOR_OPEN:
    opencolor = hexToColor(temp) 

#racer:
def setupFail(config):
  global fail_bkg_xPos, fail_bkg_yPos, fail_text_xPos, fail_text_yPos

  temp = config.get("theme", "fail_bkg_x")
  if fail_bkg_xPos == None or temp != DEFAULT_FAIL_BKG_X:
    fail_bkg_xPos = temp  

  temp = config.get("theme", "fail_bkg_y")
  if fail_bkg_yPos == None or temp != DEFAULT_FAIL_BKG_Y:
    fail_bkg_yPos = temp  

  temp = config.get("theme", "fail_text_x")
  if fail_text_xPos == None or temp != DEFAULT_FAIL_TEXT_X:
    fail_text_xPos = temp  

  temp = config.get("theme", "fail_text_y")
  if fail_text_yPos == None or temp != DEFAULT_FAIL_TEXT_Y:
    fail_text_yPos = temp 

def setupRockmeter(config):
  global rmtype

  temp = config.get("theme", "rmtype")
  if rmtype == None or temp != DEFAULT_RMTYPE:
    rmtype = temp  

def setupEvilynux(config):
  global songlist_score_colorVar, rockmeter_score_colorVar, ingame_stats_colorVar

  temp = config.get("theme", "songlist_score_color")
  if songlist_score_colorVar == None or temp != DEFAULT_SONGLIST_SCORE_COLOR:
    songlist_score_colorVar = temp  

  temp = config.get("theme", "rockmeter_score_color")
  if rockmeter_score_colorVar == None or temp != DEFAULT_ROCKMETER_SCORE_COLOR:
    rockmeter_score_colorVar = temp  

  temp = config.get("theme", "ingame_stats_color")
  if ingame_stats_colorVar == None or temp != DEFAULT_INGAME_STATS_COLOR:
    ingame_stats_colorVar = temp  


def write(f, config):
  # Write read in theme.ini specific variables
  # Should be sorted

  f.write("[theme]\n")
  
  writeColors(f, config)
  writeFrets(f, config)
  writeFlameColors(f, config)
  writeFlameSizes(f, config)
  writeSpinny(f, config)
  writePOV(f, config)
  writeMisc(f, config)
  writeMenu(f, config)
  writeSonglist(f, config)  #MFH
  writePauseNOpt(f, config) #MFH
  writeTWOD(f, config)
  writeFail(f, config) #racer
  writeEvilynux(f, config)
  writeRockmeter(f, config)

def writeColors(f, config):
  global backgroundColor, baseColor, selectedColor
  global hopoColor, spotColor, meshColor
  global keyColor, key2Color
  global tracksColor, barsColor, glowColor

  f.write("%s = %s\n" % ("background_color", backgroundColor))
  f.write("%s = %s\n" % ("base_color", baseColor))
  f.write("%s = %s\n" % ("selected_color", selectedColor))
  f.write("%s = %s\n" % ("mesh_color", meshColor))
  f.write("%s = %s\n" % ("hopo_color", hopoColor))
  f.write("%s = %s\n" % ("spot_color", spotColor))
  f.write("%s = %s\n" % ("key_color", keyColor))
  f.write("%s = %s\n" % ("key2_color", key2Color))
  f.write("%s = %s\n" % ("tracks_color", tracksColor))
  f.write("%s = %s\n" % ("bars_color", barsColor))
  f.write("%s = %s\n" % ("glow_color", glowColor))

def writeFrets(f, config):
  global fretColors
    
  f.write("%s = %s\n" % ("fret0_color", fretColors[0]))
  f.write("%s = %s\n" % ("fret1_color", fretColors[1]))
  f.write("%s = %s\n" % ("fret2_color", fretColors[2]))
  f.write("%s = %s\n" % ("fret3_color", fretColors[3]))
  f.write("%s = %s\n" % ("fret4_color", fretColors[4]))

def writeFlameColors(f, config):
  global flameColors
  
  f.write("%s = %s\n" % ("flame0_1X_color", flameColors[0][0]))
  f.write("%s = %s\n" % ("flame1_1X_color", flameColors[0][1]))
  f.write("%s = %s\n" % ("flame2_1X_color", flameColors[0][2]))
  f.write("%s = %s\n" % ("flame3_1X_color", flameColors[0][3]))
  f.write("%s = %s\n" % ("flame4_1X_color", flameColors[0][4]))
  f.write("%s = %s\n" % ("flame0_2X_color", flameColors[1][0]))
  f.write("%s = %s\n" % ("flame1_2X_color", flameColors[1][1]))
  f.write("%s = %s\n" % ("flame2_2X_color", flameColors[1][2]))
  f.write("%s = %s\n" % ("flame3_2X_color", flameColors[1][3]))
  f.write("%s = %s\n" % ("flame4_2X_color", flameColors[1][4]))
  f.write("%s = %s\n" % ("flame0_3X_color", flameColors[2][0]))
  f.write("%s = %s\n" % ("flame1_3X_color", flameColors[2][1]))
  f.write("%s = %s\n" % ("flame2_3X_color", flameColors[2][2]))
  f.write("%s = %s\n" % ("flame3_3X_color", flameColors[2][3]))
  f.write("%s = %s\n" % ("flame4_3X_color", flameColors[2][4]))
  f.write("%s = %s\n" % ("flame0_4X_color", flameColors[3][0]))
  f.write("%s = %s\n" % ("flame1_4X_color", flameColors[3][1]))
  f.write("%s = %s\n" % ("flame2_4X_color", flameColors[3][2]))
  f.write("%s = %s\n" % ("flame3_4X_color", flameColors[3][3]))
  f.write("%s = %s\n" % ("flame4_4X_color", flameColors[3][4]))
  f.write("%s = %s\n" % ("flame_gh3_color", gh3flameColor))
  
def writeFlameSizes(f, config):
  global flameSizes
  
  f.write("%s = %s\n" % ("flame0_1X_size", flameSizes[0][0]))
  f.write("%s = %s\n" % ("flame1_1X_size", flameSizes[0][1]))
  f.write("%s = %s\n" % ("flame2_1X_size", flameSizes[0][2]))
  f.write("%s = %s\n" % ("flame3_1X_size", flameSizes[0][3]))
  f.write("%s = %s\n" % ("flame4_1X_size", flameSizes[0][4]))
  f.write("%s = %s\n" % ("flame0_2X_size", flameSizes[1][0]))
  f.write("%s = %s\n" % ("flame1_2X_size", flameSizes[1][1]))
  f.write("%s = %s\n" % ("flame2_2X_size", flameSizes[1][2]))
  f.write("%s = %s\n" % ("flame3_2X_size", flameSizes[1][3]))
  f.write("%s = %s\n" % ("flame4_2X_size", flameSizes[1][4]))
  f.write("%s = %s\n" % ("flame0_3X_size", flameSizes[2][0]))
  f.write("%s = %s\n" % ("flame1_3X_size", flameSizes[2][1]))
  f.write("%s = %s\n" % ("flame2_3X_size", flameSizes[2][2]))
  f.write("%s = %s\n" % ("flame3_3X_size", flameSizes[2][3]))
  f.write("%s = %s\n" % ("flame4_3X_size", flameSizes[2][4]))
  f.write("%s = %s\n" % ("flame0_4X_size", flameSizes[3][0]))
  f.write("%s = %s\n" % ("flame1_4X_size", flameSizes[3][1]))
  f.write("%s = %s\n" % ("flame2_4X_size", flameSizes[3][2]))
  f.write("%s = %s\n" % ("flame3_4X_size", flameSizes[3][3]))
  f.write("%s = %s\n" % ("flame4_4X_size", flameSizes[3][4]))

def writeSpinny(f, config):
  global spinnySongDisabled, spinnyEditorDisabled, spinnyResultsDisabled, spinnyMenuDisabled

  f.write("%s = %s\n" % ("disable_song_spinny", spinnySongDisabled))
  f.write("%s = %s\n" % ("disable_editor_spinny", spinnyEditorDisabled))
  f.write("%s = %s\n" % ("disable_results_spinny", spinnyResultsDisabled))
  f.write("%s = %s\n" % ("disable_menu_spinny", spinnyMenuDisabled))

def writePOV(f, config):
  global povTargetX, povTargetY, povTargetZ
  global povOriginX, povOriginY, povOriginZ
  
  f.write("%s = %s\n" % ("pov_target_x", povTargetX))
  f.write("%s = %s\n" % ("pov_target_y", povTargetY))
  f.write("%s = %s\n" % ("pov_target_z", povTargetZ))
  f.write("%s = %s\n" % ("pov_origin_x", povOriginX))
  f.write("%s = %s\n" % ("pov_origin_y", povOriginY))
  f.write("%s = %s\n" % ("pov_origin_z", povOriginZ))
        
def writeMisc(f, config):
  global loadingPhrase, resultsPhrase
  global creditSong
  global crowdLoopDelay

  f.write("%s = %s\n" % ("loading_phrase", loadingPhrase))
  f.write("%s = %s\n" % ("results_phrase", resultsPhrase))
  f.write("%s = %s\n" % ("credit_song", creditSong))
 
  #MFH - crowd cheer loop delay in theme.ini: if not exist, use value from settings. Otherwise, use theme.ini value.
  f.write("%s = %s\n" % ("crowd_loop_delay", crowdLoopDelay))

#MFH:  
def writeSonglist(f, config):
  global song_cd_Xpos, song_cdscore_Xpos
  global song_list_Xpos, song_listscore_Xpos

  global main_menu_scaleVar, main_menu_vspacingVar, sub_menu_xVar, sub_menu_yVar
  global career_title_colorVar, opt_text_colorVar, opt_selected_colorVar
  global song_name_text_colorVar, song_name_selected_colorVar
  global artist_text_colorVar, artist_selected_colorVar
  global library_text_colorVar, library_selected_colorVar
  global pause_text_colorVar, pause_selected_colorVar
  global fail_text_colorVar, fail_selected_colorVar
  global songlist_score_colorVar # evilynux - score color

  global songSelectSubmenuX, songSelectSubmenuY

  #MFH - for instrument / difficulty / practice section submenu positioning
  f.write("%s = %s\n" % ("song_select_submenu_x", songSelectSubmenuX))
  f.write("%s = %s\n" % ("song_select_submenu_y", songSelectSubmenuY))

  f.write("%s = %s\n" % ("song_cd_x", song_cd_Xpos))
  f.write("%s = %s\n" % ("song_cdscore_x", song_cdscore_Xpos))
  f.write("%s = %s\n" % ("song_list_x", song_list_Xpos))
  f.write("%s = %s\n" % ("song_listscore_x", song_listscore_Xpos))


  #MFH - adding new options here
  f.write("%s = %s\n" % ("main_menu_scale", main_menu_scaleVar))
  f.write("%s = %s\n" % ("main_menu_vspacing", main_menu_vspacingVar))
  f.write("%s = %s\n" % ("sub_menu_x", sub_menu_xVar))
  f.write("%s = %s\n" % ("sub_menu_y", sub_menu_yVar))
  f.write("%s = %s\n" % ("career_title_color", career_title_colorVar))
  f.write("%s = %s\n" % ("opt_text_color", opt_text_colorVar))
  f.write("%s = %s\n" % ("opt_selected_color", opt_selected_colorVar))
  f.write("%s = %s\n" % ("song_name_text_color", song_name_text_colorVar))
  f.write("%s = %s\n" % ("song_name_selected_color", song_name_selected_colorVar))
  f.write("%s = %s\n" % ("artist_text_color", artist_text_colorVar))
  f.write("%s = %s\n" % ("artist_selected_color", artist_selected_colorVar))
  f.write("%s = %s\n" % ("library_text_color", library_text_colorVar))
  f.write("%s = %s\n" % ("library_selected_color", library_selected_colorVar))
  f.write("%s = %s\n" % ("pause_text_color", pause_text_colorVar))
  f.write("%s = %s\n" % ("pause_selected_color", pause_selected_colorVar))
  f.write("%s = %s\n" % ("fail_text_color", fail_text_colorVar))
  f.write("%s = %s\n" % ("fail_selected_color", fail_selected_colorVar))
  f.write("%s = %s\n" % ("songlist_score_color", songlist_score_colorVar)) # evilynux - score color


def writePauseNOpt(f, config):
  global pause_bkg_xPos, pause_bkg_yPos, pause_text_xPos, pause_text_yPos
  global opt_bkg_xPos, opt_bkg_yPos, opt_text_xPos, opt_text_yPos
  
  f.write("%s = %s\n" % ("pause_bkg_x", pause_bkg_xPos))
  f.write("%s = %s\n" % ("pause_bkg_y", pause_bkg_yPos))
  f.write("%s = %s\n" % ("pause_text_x", pause_text_xPos))
  f.write("%s = %s\n" % ("pause_text_y", pause_text_yPos))
  f.write("%s = %s\n" % ("opt_bkg_x", opt_bkg_xPos))
  f.write("%s = %s\n" % ("opt_bkg_y", opt_bkg_yPos))
  f.write("%s = %s\n" % ("opt_text_x", opt_text_xPos))
  f.write("%s = %s\n" % ("opt_text_y", opt_text_yPos))


def writeMenu(f, config):
  global menuX, menuY
  global loadingX, loadingY
  global songback

  f.write("%s = %s\n" % ("menu_x", menuX))
  f.write("%s = %s\n" % ("menu_y", menuY))
  f.write("%s = %s\n" % ("loading_x", loadingX))
  f.write("%s = %s\n" % ("loading_y", loadingY))
  f.write("%s = %s\n" % ("songback", songback))
  f.write("%s = %s\n" % ("versiontag", versiontag))

def writeTWOD(f, config):
  global twoDnote, twoDkeys, threeDspin, opencolor
 
  f.write("%s = %s\n" % ("twoDnote", twoDnote))
  f.write("%s = %s\n" % ("twoDkeys", twoDkeys))
  f.write("%s = %s\n" % ("threeDspin", threeDspin))
  f.write("%s = %s\n" % ("opencolor", opencolor))

def writeFail(f, config): #racer
  global fail_bkg_xPos, fail_bkg_yPos, fail_text_xPos, fail_text_yPos
  
  f.write("%s = %s\n" % ("fail_bkg_x", fail_bkg_xPos))
  f.write("%s = %s\n" % ("fail_bkg_y", fail_bkg_yPos))
  f.write("%s = %s\n" % ("fail_text_x", fail_text_xPos))
  f.write("%s = %s\n" % ("fail_text_y", fail_text_yPos))

def writeEvilynux(f, config):

  global songlist_score_colorVar, rockmeter_score_colorVar, ingame_stats_colorVar

  f.write("%s = %s\n" % ("songlist_score_color", songlist_score_colorVar))
  f.write("%s = %s\n" % ("rockmeter_score_color", rockmeter_score_colorVar))
  f.write("%s = %s\n" % ("ingame_stats_color", ingame_stats_colorVar))

def writeRockmeter(f, config):
  global rmtype

  f.write("%s = %s\n" % ("rmtype", rmtype))
