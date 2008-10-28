#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire                                                     #
# Copyright (C) 2006 Sami Kyöstilä                                  #
#               2008 Alarian                                        #
#               2008 myfingershurt                                  #
#               2008 Glorandwarf                                    #
#               2008 Spikehead777                                   #
#               2008 QQStarS                                        #
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
import pygame
import os
import sys

from Engine import Engine, Task
from Video import Video
from Audio import Audio
from View import View
from Input import Input, KeyListener, SystemEventListener
from Resource import Resource
from Data import Data
from Server import Server
from Session import ClientSession
from Svg import SvgContext, ImgDrawing, LOW_QUALITY, NORMAL_QUALITY, HIGH_QUALITY
#alarian
#from Song import EAS_DIF, MED_DIF, HAR_DIF, EXP_DIF
from Debug import DebugLayer
from Language import _
import Network
import Log
import Config
import Dialogs
import Theme
import Version
import Mod


# define configuration keys
Config.define("engine", "tickrate",     float, 1.0)
Config.define("engine", "highpriority", bool,  True)
Config.define("game",   "uploadscores", bool,  False, text = _("Upload Highscores"),    options = {False: _("No"), True: _("Yes")})
Config.define("game",   "leftymode",    bool,  False, text = _("Lefty mode"),           options = {False: _("No"), True: _("Yes")})
Config.define("video",  "fullscreen",   bool,  False,  text = _("Fullscreen Mode"),      options = {False: _("No"), True: _("Yes")})
Config.define("video",  "multisamples", int,   4,     text = _("Antialiasing Quality"), options = {0: _("None"), 2: "2x", 4: "4x", 6: "6x", 8: "8x"})
Config.define("video",  "disable_fretsfx", bool, False, text = _("Enable Glow-FX"), options = {False: _("Yes"), True: _("No")})
Config.define("video",  "resolution",   str,   "640x480")
Config.define("video",  "fps",          int,   80,    text = _("Frames per Second"), options = dict([(n, n) for n in range(1, 120)]))
Config.define("video",  "hitglow_color", int,  0,     text = _("Glow-FX Color"), options = {0: _("Same as Fret"), 1: _("Actual Color")})
Config.define("video",  "hitflame_color", int, 0,     text = _("Hitflames Color"), options = {0: _("Theme Specific"), 1: _("Same as Fret"), 2: _("Actual Color")})
Config.define("performance",  "starspin", bool,     True,  text = _("Starnotes"), options = {True: _("Animated"), False: _("Static")})
Config.define("opengl", "svgquality",   int,   NORMAL_QUALITY,  text = _("SVG Quality"), options = {LOW_QUALITY: _("Low"), NORMAL_QUALITY: _("Normal"), HIGH_QUALITY: _("High")})
Config.define("audio",  "frequency",    int,   44100, text = _("Sample Frequency"), options = [8000, 11025, 22050, 32000, 44100, 48000])
Config.define("audio",  "bits",         int,   16,    text = _("Sample Bits"), options = [16, 8])
Config.define("audio",  "stereo",       bool,  True)

#MFH - Frame Buffer Object support: nevermind, needs GLEWpy and Pyrex and some other such addon...
#Config.define("opengl",  "supportfbo",       bool,  True)


#used internally:
Config.define("game",   "players",             int,   1)
Config.define("player0","mode_1p",           int,  0)
Config.define("player1","mode_2p",           int,  0)

Config.define("game","last_theme",           str,  "")



#myfingershurt: default buffersize changed from 4096 to 2048:
Config.define("audio",  "buffersize",   int,   2048,  text = _("Buffer Size"), options = [256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536])
Config.define("audio",  "delay",        int,   100,   text = _("A/V delay"), options = dict([(n, n) for n in range(0, 1001)]))
Config.define("audio",  "screwupvol", float,   0.25,  text = _("Screw Up sounds"), options = {0.0: _("Off"), .25: _("Quiet"), .5: _("Loud"), 1.0: _("Painful")})

#MFH: below are normal 0-10 volume settings.
Config.define("audio",  "guitarvol",  float,    1.0,  text = _("Guitar Volume"),   options = dict([(n / 100.0, "%02d/10" % (n / 10)) for n in range(0, 110, 10)]))
Config.define("audio",  "songvol",    float,    1.0,  text = _("Song Volume"),     options = dict([(n / 100.0, "%02d/10" % (n / 10)) for n in range(0, 110, 10)]))
Config.define("audio",  "rhythmvol",  float,    1.0,  text = _("Rhythm Volume"),   options = dict([(n / 100.0, "%02d/10" % (n / 10)) for n in range(0, 110, 10)]))

Config.define("performance", "game_priority",       int,   2,      text = _("Priority"), options = {0: _("0 Idle"), 1: _("1 Low"), 2: _("2 Normal"), 3:_("3 Above Normal"), 4:_("4 High"), 5:_("5 Realtime")})
Config.define("game",   "alt_keys",            bool,  False,  text = _("Keyset"), options = {False: _("Normal"), True: _("Alternate")})
Config.define("game",   "margin",              int,   0,      text = _("Hit Margin"), options = {0: _("FoF"), 1: _("Capo")})
Config.define("game",   "notedisappear",      bool,   False,  text = _("Missed Notes"), options = {False: _("Disappear"), True: _("Keep on going")})

#myfingershurt: the following two lines are not used in gameplay,
# but are still used in the encrypted score system.  Therefore, the simplest
# way to prevent users from having issues is to leave these two lines uncommented
# (so they automatically create the entries with defaults if they do not exist)
Config.define("game",   "tapping",      int,   0,  text = _("HO/PO"),       options = {0: _("Yes"), 1: _("No")})
Config.define("game",   "hopo_mark",           int,   1,      text = _("HO/PO Note Marks"), options = {0: _("FoF"), 1: _("RFmod")})
#myfingershurt: HOPO settings
Config.define("game",   "hopo_style",          int,   4,      text = _("HO/PO System"), options = {0: _("None"), 1: _("RF-Mod"), 2: _("GH2 Strict"), 3: _("GH2 Sloppy"), 4: _("GH2")})
Config.define("coffee", "moreHopo",            int,   1,   text = _("HO/PO Frequency"),    options = {0: _("Less"), 1: _("Normal"), 2: _("More")})
Config.define("game", "hopo_after_chord",      int,   1,   text = _("HO/PO After Chord"),    options = {0: _("Off"), 1: _("On")})
Config.define("game", "accuracy_mode",      int,   2,   text = _("Accuracy"),    options = {0: _("Off"), 1: _("Numeric"), 2: _("Friendly"), 3: _("Both")})
Config.define("game", "accuracy_pos",      int,   1,   text = _("Accuracy Words Pos"),    options = {0: _("Center"), 1: _("Right-top Corner"), 2: _("Left-Bottom Corner"), 3: _("Center-Bottom")}) #QQstarS:acc show
Config.define("game",  "stage_rotate_delay",        int,   800,   text = _("Rotate Delay"), options = dict([(n, n) for n in range(0, 10, 1)] + [(n, n) for n in range(10, 50, 10)] + [(n, n) for n in range(50, 2001, 50)]))
Config.define("game",  "stage_animate_delay",        int,   3,   text = _("Animation Delay"), options = dict([(n, n) for n in range(0, 10, 1)] + [(n, n) for n in range(10, 50, 10)] + [(n, n) for n in range(50, 2001, 50)]))

Config.define("game",   "stage_mode",           int,  0,  text = _("Stages"),  options = {0: _("Random"), 1: _("Default"), 2: _("Blank") } )
Config.define("game",   "song_stage",           int,  1,  text = _("Song Stage"),  options = {0: _("Off"), 1: _("On") } ) #MFH


#myfingershurt:
Config.define("game",   "rotate_stages",           int,  0,  text = _("Rotate Stages"),  options = {0: _("No"), 1: _("Random"), 2: _("In Order"), 3: _("BackNForth")} ) 
Config.define("game",   "lyric_mode",           int,   2,   text = _("Lyrics"), options = {0: _("Off"), 1: _("song.ini"), 2: _("Auto"), 3: _("Dual Lyric Prevention")})#racer
Config.define("game",   "frets_under_notes",          bool, True,  text = _("Frets under notes"), options = {False: _("No"), True: _("Yes")})
#Config.define("game",   "drum_highscore_nav",          bool, False,  text = _("Drum highscore nav"), options = {False: _("Off"), True: _("On")})
Config.define("game",   "drum_navigation",          bool, False,  text = _("Drum navigation"), options = {False: _("Off"), True: _("On")})

Config.define("game",   "ignore_open_strums",          bool, True,  text = _("Ignore open strums"), options = {False: _("No"), True: _("Yes")})
Config.define("performance",   "static_strings",          bool, True,  text = _("Static strings"), options = {False: _("No"), True: _("Yes")})
Config.define("game",   "whammy_saves_starpower",          bool, False,  text = _("Whammy saves SP"), options = {False: _("No"), True: _("Yes")})
Config.define("game",   "mute_sustain_releases",          bool, False,  text = _("Mute sustain releases"), options = {False: _("No"), True: _("Yes")})
Config.define("game",   "hopo_indicator",          bool, False,  text = _("HOPO Indicator"), options = {False: _("Off"), True: _("On")})
Config.define("game",   "quickplay_career_tiers",          bool, True,  text = _("Quickplay Tiers"), options = {False: _("Off"), True: _("On")})
Config.define("performance",   "star_score_updates",          int, 1,  text = _("Star Updates"), options = {0: _("On Hit"), 1: _("Score Change")})

Config.define("game", "script_lyric_pos",      int,   0,   text = _("Script Lyric Pos"),    options = {0: _("Bottom"), 1: _("Top")}) #MFH - script.txt lyric display position


Config.define("game",   "star_claps",          bool, False,  text = _("Starpower Clap SFX"), options = {False: _("Off"), True: _("On")})
Config.define("audio", "disable_preview",      bool, True,  text = _("Song Previews"), options = {False: _("Auto"), True: _("Yellow Fret (#3)")})
Config.define("game", "uploadurl_w67_starpower",    str,   "http://www.wembley1967.com/chart/uploadsp.php") # evilynux - new one starting 20080902
Config.define("game", "rb_sp_neck_glow",      bool, False,  text = _("RB SP Neck Glow"), options = {False: _("Off"), True: _("On")})
Config.define("game",   "sp_notes_while_active",  int,  1,  text = _("SP Refill"),  options = {0: _("None"), 1: _("Rock Band"), 2: _("Yes")} ) 

Config.define("game", "analog_killsw_mode",      int, 0,  text = _("Analog Killswitch P1"), options = {0: _("Off"), 1: _("PS2/PS3/Wii"), 2: _("XBOX"), 3: _("XBOX Inv")})
Config.define("game", "analog_killsw_mode_p2",      int, 0,  text = _("Analog Killswitch P2"), options = {0: _("Off"), 1: _("PS2/PS3/Wii"), 2: _("XBOX"), 3: _("XBOX Inv")})

#MFH wuz here.  Yeah.
Config.define("game", "kill_debug",      bool, False,  text = _("Killsw Debug"), options = {False: _("Off"), True: _("On")})
Config.define("game", "auto_drum_sp",      bool, False,  text = _("Auto Drum SP"), options = {False: _("No"), True: _("Yes")})
Config.define("game", "large_drum_neck",      bool, False,  text = _("Large Drum Neck"), options = {False: _("No"), True: _("Yes")})
Config.define("game", "bass_groove_neck",      int, 1,  text = _("Bass Groove Neck"), options = {0: _("Off"), 1: _("Replace"), 2: _("Overlay")})
Config.define("game", "guitar_solo_neck",      int, 2,  text = _("Guitar Solo Neck"), options = {0: _("Off"), 1: _("Replace"), 2: _("Overlay")})
Config.define("game", "rock_band_events",      int, 1,  text = _("Rock Band MIDI events"), options = {0: _("Off"), 1: _("RB Only"), 2: _("On")})
Config.define("game", "show_unused_text_events",      bool, False,  text = _("Show unused events"), options = {False: _("No"), True: _("Yes")})
Config.define("game", "bass_kick_sound",      bool, False,  text = _("Bass kick sound"), options = {False: _("Off"), True: _("On")})
Config.define("game", "rb_midi_lyrics",           int,  1,   text = _("MIDI/RB Lyrics"), options = {0: _("Off"), 1: _("1p Only"), 2: _("Auto")})
Config.define("game", "rb_midi_sections",           int,  1,   text = _("MIDI/RB Sections"), options = {0: _("Off"), 1: _("1p Only"), 2: _("Auto")})
Config.define("game", "key_checker_mode",      int, 1,  text = _("Key Conflicts"), options = {0: _("No check"), 1: _("Notify"), 2: _("Enforce")})
Config.define("performance", "in_game_stats",      int, 0,  text = _("In-Game Stats"), options = {0: _("Off"), 1: _("RB Only"), 2: _("On")})
Config.define("game", "in_game_stars",      int, 1,  text = _("In-Game Stars"), options = {0: _("Off"), 1: _("RB Only"), 2: _("On")})
Config.define("game", "partial_stars",      int, 1,  text = _("Partial Stars"), options = {0: _("Off"), 1: _("Auto")})
Config.define("game", "hopo_debug_disp",      int, 0,  text = _("HOPO Debug"), options = {0: _("Off"), 1: _("On")})
Config.define("game", "gsolo_accuracy_disp",      int, 1,  text = _("Solo Accuracy"), options = {0: _("Off"), 1: _("Percent"), 2: _("Detail")})
Config.define("game", "decimal_places",      int, 1,  text = _("Decimal Places"), options = dict([(n, n) for n in range(0, 3)]))
Config.define("game", "star_scoring",       int, 3,     text = _("Star Scoring"), options = {0: _("FoF"), 1: _("GH"), 2: _("RB"), 3: _("RB+GH")})#MFH
Config.define("game", "gsolo_acc_pos",       int, 3,     text = _("GtrSolo Pos."), options = {0: _("Right"), 1: _("Center"), 2: _("Left"), 3: _("Rock Band")})#MFH,(racer: added RB)
Config.define("game", "bass_groove_enable",       int, 1,     text = _("Bass Groove"), options = {0: _("Off"), 1: _("RB Only"), 2: _("On")}) #MFH
Config.define("game", "T_sound",      int, 2,  text = _("Drum Misses"), options = {0: _("Always"), 1: _("Song Start"), 2: _("First Note")} ) #Faaa Drum sound
Config.define("game", "game_time",       int, 1,     text = _("Game Time"), options = {0: _("Off"), 1: _("Countdown"), 2: _("Elapsed")}) #MFH
Config.define("game", "gfx_version_tag",       int, 1,     text = _("GfxVersionTag"), options = {0: _("Off"), 1: _("On")}) #MFH
Config.define("game", "p2_menu_nav",       int, 1,     text = _("P2 Menu Navigate"), options = {0: _("Off"), 1: _("On")}) #MFH
Config.define("game", "in_game_font_shadowing",      bool, False,  text = _("In-Game Font Shadow"), options = {False: _("Off"), True: _("On")})
Config.define("audio", "mute_last_second",       int, 0,     text = _("Mute last second"), options = {0: _("No"), 1: _("Yes")}) #MFH
Config.define("game", "result_cheer_loop",       int, 2,     text = _("Results Cheer Loop"), options = {0: _("Off"), 1: _("Theme"), 2: _("Auto")}) #MFH
Config.define("game",  "cheer_loop_delay",        int,   550,   text = _("Cheer Loop Delay"), options = dict([(n, n) for n in range(0, 10, 1)] + [(n, n) for n in range(10, 50, 10)] + [(n, n) for n in range(50, 2001, 50)]))
Config.define("game", "miss_pauses_anim",       int, 1,     text = _("Miss Pauses Anim"), options = {0: _("Off"), 1: _("On")}) #MFH
Config.define("game", "song_hopo_freq",       int, 1,     text = _("Song HOPO Freq"), options = {0: _("Off"), 1: _("Auto")}) #MFH



#racer
Config.define("game", "rbnote",      int,   0,   text = _("Rock Band Version"),    options = {0: _("Regular"), 1: _("Beta")}) #racer
Config.define("game", "beat_claps",          bool, False,  text = _("Practice Beat Claps"), options = {False: _("Off"), True: _("On")}) #racer
#Fixed invalid ini error finally!!!
Config.define("game", "board_speed",      int,   0) #racer
Config.define("game", "HSMovement",      int,   1,   text = _("Song Choosing Highscores"),    options = {0: _("Auto"), 1: _("Blue Fret (#4)")}) #racer


#blazingamer
Config.define("game", "congrats",       bool, True,     text = _("Score SFX"),             options = {True: _("On"), False: _("Off")})#blazingamer
Config.define("game", "starfx",       bool, True,     text = _("GH SP Lights"),             options = {True: _("On"), False: _("Off")})#blazingamer
Config.define("game", "rbmfx",       bool, True,     text = _("RB Mult Grow"),             options = {True: _("On"), False: _("Off")})#blazingamer
Config.define("game", "nstype",       int, 2,     text = _("Board Speed"),             options = {0: _("BPM"), 1: _("Difficulty"), 2: _("BPM & Diff"), 3: _("Percentage")})
Config.define("game", "lphrases",       bool, True,     text = _("Loading Phrases"),             options = {True: _("On"), False: _("Off")})
Config.define("performance", "killfx",       int, 0,     text = _("Killswitch FX"),             options = {0: _("Static"), 1: _("Animated"), 2: _("Off")})
Config.define("coffee", "songfilepath",       bool, True,     text = _("Library Filepath"),             options = {True: _("Show"), False: _("Hide")})
Config.define("coffee", "noterotate",       bool, False,     text = _("Rotate 3D Notes"),             options = {True: _("1.1"), False: _("1.2")})
Config.define("coffee", "phrases",       bool, True,     text = _("Phrases"),             options = {True: _("On"), False: _("Off")})
Config.define("coffee", "songdisplay",       bool, False,     text = _("Song Display"),             options = {True: _("CDs"), False: _("List")})
Config.define("game", "tut",       bool, False,     text = _("tut"),             options = {True: _("yes"), False: _("no")})


Config.define("game",   "hit_window",          int, 1,    text = _("Note Hit-window"), options = {0: _("Wide"), 1: _("Standard"), 2: _("Tight"), 3: _("Hot Pants Tight"), 4: _("Tight Like a Tiger")})#racer blazingamer
Config.define("game",   "disable_vbpm",        bool,  False,  text = _("Disable Variable BPM"),  options = {False: _("No"), True: _("Yes")})
Config.define("game",   "sort_order",          int,   0,      text = _("Sort Order"), options = {0: _("Title"), 1: _("Artist"), 2: _("Times played")})
Config.define("game",   "pov",                 int,   3,      text = _("Point Of View"), options = {0: _("FoF"), 1: _("GH3"), 2: _("Custom"), 3: _("Rock Band"), 4: _("GH2"), 5: _("Rock Rev"), 6: _("Theme")}) #Racer, Blazingamer
Config.define("game",   "party_time",          int,   30,     text = _("Party Mode Timer"), options = dict([(n, n) for n in range(1, 99)]))
Config.define("performance",   "disable_libcount",    bool,  True,  text = _("Disable Library Count"),    options = {False: _("No"), True: _("Yes")})
Config.define("performance",   "disable_librotation", bool,  True,  text = _("Disable Library Rotation"),    options = {False: _("No"), True: _("Yes")})

#Spikehead777
Config.define("game",   "jurgdef",             bool,  False,  text = _("Enable Jurgen"),    options = {False: _("No"), True: _("Yes")})
Config.define("game",   "jurgtype",            int,   2,      text = _("Jurgen Player"), options = {0: _("1"), 1: _("2"), 2: _("Both")}  )
#MFH
Config.define("game",   "jurglogic",            int,   1,      text = _("Jurgen Logic"), options = {0: _("Original"), 1: _("MFH-Early"), 2: _("MFH-OnTime1"), 3: _("MFH-OnTime2")}  )



Config.define("audio",  "miss_volume",         float, 0.2,    text = _("Miss Volume"), options = dict([(n / 100.0, "%d%%" % n) for n in range(0, 100, 10)]))
Config.define("audio",  "kill_volume",         float, 0.0,    text = _("Kill Volume"), options = dict([(n / 100.0, "%02d/10" % (n / 10)) for n in range(0, 110, 10)]))  #MFH
Config.define("audio",  "SFX_volume",         float, 0.7,    text = _("SFX Volume"), options = dict([(n / 100.0, "%02d/10" % (n / 10)) for n in range(0, 110, 10)]))  #MFH


Config.define("player0","two_chord_max",       bool,  False,  text = _("P1 Two Key Chords Only"),  options = {False: _("No"), True: _("Yes")})
Config.define("player0","leftymode",           bool,  False,  text = _("P1 Lefty mode"),           options = {False: _("No"), True: _("Yes")})
Config.define("player1","two_chord_max",       bool,  False,  text = _("P2 Two Key Chords Only"),  options = {False: _("No"), True: _("Yes")}) #QQstarS
Config.define("player1","leftymode",           bool,  False,  text = _("P2 Lefty mode"),           options = {False: _("No"), True: _("Yes")}) #QQstarS

# evilynux - Preload glyph cache may require more VRAM. Disable it if you're low on VRAM e.g. less than 64MB
Config.define("performance","preload_glyph_cache", bool,  True,  text = _("Preload Glyph Cache"), options = {False: _("No"), True: _("Yes")})

##Alarian: Get unlimited themes by foldername
themepath = os.path.join("data","themes")
if not hasattr(sys,"frozen"):
  themepath = os.path.join("..",themepath)
themes = []
defaultTheme = None           #myfingershurt
allthemes = os.listdir(themepath)
for name in allthemes:
  if os.path.exists(os.path.join(themepath,name,"notes.png")):
    themes.append(name)
    if name == "MegaLight" and defaultTheme != "Rock Band 1":         #myfingershurt
      defaultTheme = name     #myfingershurt
    if name == "Rock Band 1":         #myfingershurt
      defaultTheme = name     #myfingershurt

i = len(themes)

if defaultTheme != "MegaLight" and defaultTheme != "Rock Band 1":     #myfingershurt
  defaultTheme = themes[0]    #myfingershurt

#myfingershurt: default theme must be an existing one!
Config.define("coffee", "themename",           str,   defaultTheme,      text = _("Theme"),                options = dict([(str(themes[n]),themes[n]) for n in range(0, i)]))

##Alarian: End Get unlimited themes by foldername



Config.define("coffee", "neckSpeed",            int,  100,      text = _("Speed Percent"),        options = dict([(n, n) for n in range(10, 410, 10)]))
Config.define("coffee", "failingEnabled",       bool, True,     text = _("Failing"),             options = {True: _("Yes"), False: _("No")})

# evilynux - configurable default highscores difficulty display.
# Index assigned following same standard as command line argument.
Config.define("game", "songlist_difficulty", int, 0, text = _("Show Difficulty"), options = {0: "Expert", 1: "Hard", 2: "Medium", 3: "Easy"}  )
Config.define("game", "songlist_extra_stats", bool, True, text = _("Display hit% and note streak"), options = {True: _("Yes"), False: _("No")} )

Config.define("game", "songlist_instrument", int, 0, text = _("Show Instrument"), options = {0: "Guitar", 1: "Rhythm Guitar", 2: "Bass Guitar", 3: "Lead Guitar", 4: "Drums"}  )  #MFH


class FullScreenSwitcher(KeyListener):
  """
  A keyboard listener that looks for special built-in key combinations,
  such as the fullscreen toggle (Alt-Enter).
  """
  def __init__(self, engine):
    self.engine = engine
    self.altStatus = False
  
  def keyPressed(self, key, unicode):
    if key == pygame.K_LALT:
      self.altStatus = True
    elif key == pygame.K_RETURN and self.altStatus:
      if not self.engine.toggleFullscreen():
        Log.error("Unable to toggle fullscreen mode.")
      return True
    elif key == pygame.K_d and self.altStatus:
      self.engine.setDebugModeEnabled(not self.engine.isDebugModeEnabled())
      return True
    elif key == pygame.K_g and self.altStatus and self.engine.isDebugModeEnabled():
      self.engine.debugLayer.gcDump()
      return True

  def keyReleased(self, key):
    if key == pygame.K_LALT:
      self.altStatus = False
      
class SystemEventHandler(SystemEventListener):
  """
  A system event listener that takes care of restarting the game when needed
  and reacting to screen resize events.
  """
  def __init__(self, engine):
    self.engine = engine

  def screenResized(self, size):
    self.engine.resizeScreen(size[0], size[1])
    
  def restartRequested(self):
    self.engine.restart()
    
  def quit(self):
    self.engine.quit()

class GameEngine(Engine):
  """The main game engine."""
  def __init__(self, config = None):
    Log.debug("GameEngine class init (GameEngine.py)...")

    self.mainMenu = None    #placeholder for main menu object - to prevent reinstantiation

    self.versionString = "FoFiX v3.025 beta"
    
    Log.debug(self.versionString + " starting up...")
    
    Log.debug("pygame version: " + str(pygame.version.ver) )

    """
    Constructor.

    @param config:  L{Config} instance for settings
    """


    self.tutorialFolder = "tutorials"

    if not config:
      config = Config.load()
      
    self.config  = config
    
    fps          = self.config.get("video", "fps")
    tickrate     = self.config.get("engine", "tickrate")
    Engine.__init__(self, fps = fps, tickrate = tickrate)
    
    self.title             = _("Frets on Fire " + self.versionString)
    self.restartRequested  = False
    self.handlingException = False
    self.video             = Video(self.title)
    self.audio             = Audio()

    Log.debug("Initializing audio.")
    frequency    = self.config.get("audio", "frequency")
    bits         = self.config.get("audio", "bits")
    stereo       = self.config.get("audio", "stereo")
    bufferSize   = self.config.get("audio", "buffersize")
    
    self.audio.pre_open(frequency = frequency, bits = bits, stereo = stereo, bufferSize = bufferSize)
    self.audio.open(frequency = frequency, bits = bits, stereo = stereo, bufferSize = bufferSize)
    
    pygame.init()
    
    Log.debug("Initializing video.")
    #myfingershurt: ensuring windowed mode starts up in center of the screen instead of cascading positions:
    os.environ['SDL_VIDEO_WINDOW_POS'] = 'center'

    width, height = [int(s) for s in self.config.get("video", "resolution").split("x")]
    fullscreen    = self.config.get("video", "fullscreen")
    multisamples  = self.config.get("video", "multisamples")
    self.video.setMode((width, height), fullscreen = fullscreen, multisamples = multisamples)

    # Enable the high priority timer if configured
    if self.config.get("engine", "highpriority"):
      Log.debug("Enabling high priority timer.")
      self.timer.highPriority = True

    viewport = glGetIntegerv(GL_VIEWPORT)
    h = viewport[3] - viewport[1]
    w = viewport[2] - viewport[0]
    geometry = (0, 0, w, h)
    self.svg = SvgContext(geometry)
    self.svg.setRenderingQuality(self.config.get("opengl", "svgquality"))
    glViewport(*viewport)

    self.input     = Input()
    self.view      = View(self, geometry)
    self.resizeScreen(w, h)

    self.resource  = Resource(Version.dataPath())
    self.server    = None
    self.sessions  = []
    self.mainloop  = self.loading

    
    # Load game modifications
    Mod.init(self)
    
    self.addTask(self.input, synchronized = False)
    self.addTask(self.view)
    self.addTask(self.resource, synchronized = False)
    
    

    self.data = Data(self.resource, self.svg)
    themename = self.data.themeLabel

    ##MFH: Animated stage folder selection option
    #<themename>\Stages still contains the backgrounds for when stage rotation is off, and practice.png
    #subfolders under Stages\ will each be treated as a separate animated stage set
    
    self.stageFolders = []
    currentTheme = themename
    
    #if not hasattr(sys,"frozen"):
    #  themepath = os.path.join("..",themepath)
    stagespath = os.path.join("data","themes",currentTheme,"stages")
    if not hasattr(sys,"frozen"):   #MFH - so animated stages work with sources
      stagespath = os.path.join("..",stagespath)
    if os.path.exists(stagespath):
      self.stageFolders = []
      allFolders = os.listdir(stagespath)   #this also includes all the stage files - so check to see if there is at least one .png file inside each folder to be sure it's an animated stage folder
      for name in allFolders:
        aniStageFolderListing = []
        thisIsAnAnimatedStageFolder = False
        try:
          aniStageFolderListing = os.listdir(os.path.join(stagespath,name))
        except Exception, e:
          #Log.debug(name + " is not a folder, cannot list contents: " + str(e))
          thisIsAnAnimatedStageFolder = False
        for aniFile in aniStageFolderListing:
          if os.path.splitext(aniFile)[1] == ".png":  #we've found at least one .png file here, chances are this is a valid animated stage folder
            thisIsAnAnimatedStageFolder = True
        if thisIsAnAnimatedStageFolder:
          self.stageFolders.append(name)


      #stageFolders.append("Standard")  #MFH: Standard selects the base Stages folder for stage rotation, instead of one of it's subfolders
      i = len(self.stageFolders)
      if i > 0: #only set default to first animated subfolder if one exists - otherwise use Normal!
        defaultAniStage = str(self.stageFolders[0])
      else:
        defaultAniStage = "Normal"
      Log.debug("Default animated stage for " + currentTheme + " theme = " + defaultAniStage)
      aniStageOptions = dict([(str(self.stageFolders[n]),self.stageFolders[n]) for n in range(0, i)])
      aniStageOptions.update({"Normal":_("Normal")})
      if i > 1:   #only add Random setting if more than one animated stage exists
        aniStageOptions.update({"Random":_("Random")})
      Config.define("game", "animated_stage_folder", str, defaultAniStage, text = _("Animated Stage"), options = aniStageOptions )
      
      #MFH: TODO here, need to track and check a new ini entry for last theme - so when theme changes we can re-default animated stage to first found
      lastTheme = self.config.get("game","last_theme")
      if lastTheme == "" or lastTheme != currentTheme:   #MFH - no last theme, and theme just changed:
        self.config.set("game","animated_stage_folder",defaultAniStage)   #force defaultAniStage
      self.config.set("game","last_theme",currentTheme)
      
      selectedAnimatedStage = self.config.get("game", "animated_stage_folder")
      if selectedAnimatedStage != "Normal" and selectedAnimatedStage != "Random":
        if not os.path.exists(os.path.join(stagespath,selectedAnimatedStage)):
          Log.warn("Selected animated stage folder " + selectedAnimatedStage + " does not exist, forcing Normal.")
          self.config.set("game","animated_stage_folder","Normal") #MFH: force "Standard" currently selected animated stage folder is invalid
    else:
      Config.define("game", "animated_stage_folder", str, "None", text = _("Animated Stage"), options = ["None",_("None")])
      Log.warn("No stages\ folder found, forcing None setting for Animated Stage.")
      self.config.set("game","animated_stage_folder", "None") #MFH: force "None" when Stages folder can't be found

    
    # Load default theme
    try:
      theme = Config.load(self.resource.fileName("themes", themename, "theme.ini"))
    except IOError:
      theme = Config.load(self.resource.fileName("theme.ini"))
    Theme.open(theme)
  

    
    self.input.addKeyListener(FullScreenSwitcher(self), priority = True)
    self.input.addSystemEventListener(SystemEventHandler(self))

    self.debugLayer         = None
    self.startupLayer       = None
    self.loadingScreenShown = False
    
    Log.debug("Ready.")

  def setStartupLayer(self, startupLayer):
    """
    Set the L{Layer} that will be shown when the all
    the resources have been loaded. See L{Data}

    @param startupLayer:    Startup L{Layer}
    """
    self.startupLayer = startupLayer

  def isDebugModeEnabled(self):
    return bool(self.debugLayer)
    
  def setDebugModeEnabled(self, enabled):
    """
    Show or hide the debug layer.

    @type enabled: bool
    """
    if enabled:
      self.debugLayer = DebugLayer(self)
    else:
      self.debugLayer = None
    
  def toggleFullscreen(self):
    """
    Toggle between fullscreen and windowed mode.

    @return: True on success
    """
    if not self.video.toggleFullscreen():
      # on windows, the fullscreen toggle kills our textures, se we must restart the whole game
      self.input.broadcastSystemEvent("restartRequested")
      self.config.set("video", "fullscreen", not self.video.fullscreen)
      return True
    self.config.set("video", "fullscreen", self.video.fullscreen)
    return True
    
  def restart(self):
    """Restart the game."""
    if not self.restartRequested:
      self.restartRequested = True
      self.input.broadcastSystemEvent("restartRequested")
    else:
      self.quit()
    
  def resizeScreen(self, width, height):
    """
    Resize the game screen.

    @param width:   New width in pixels
    @param height:  New height in pixels
    """
    self.view.setGeometry((0, 0, width, height))
    self.svg.setGeometry((0, 0, width, height))
    
  def isServerRunning(self):
    return bool(self.server)

  def startServer(self):
    """Start the game server."""
    if not self.server:
      Log.debug("Starting server.")
      self.server = Server(self)
      self.addTask(self.server, synchronized = False)

  def connect(self, host):
    """
    Connect to a game server.

    @param host:  Name of host to connect to
    @return:      L{Session} connected to remote server
    """
    Log.debug("Connecting to host %s." % host)
    session = ClientSession(self)
    session.connect(host)
    self.addTask(session, synchronized = False)
    self.sessions.append(session)
    return session

  def stopServer(self):
    """Stop the game server."""
    if self.server:
      Log.debug("Stopping server.")
      self.removeTask(self.server)
      self.server = None

  def disconnect(self, session):
    """
    Disconnect a L{Session}

    param session:    L{Session} to disconnect
    """
    if session in self.sessions:
      Log.debug("Disconnecting.")
      self.removeTask(session)
      self.sessions.remove(session)

  def loadImgDrawing(self, target, name, fileName, textureSize = None):
    """
    Load an SVG drawing synchronously.
    
    @param target:      An object that will own the drawing
    @param name:        The name of the attribute the drawing will be assigned to
    @param fileName:    The name of the file in the data directory
    @param textureSize  Either None or (x, y), in which case the file will
                        be rendered to an x by y texture
    @return:            L{ImgDrawing} instance
    """
    return self.data.loadImgDrawing(target, name, fileName, textureSize)

  #glorandwarf: renamed to retrieve the path of the file
  def fileExists(self, fileName):
    return self.data.fileExists(fileName)
    
  def getPath(self, fileName):
    return self.data.getPath(fileName)

  def loading(self):
    """Loading state loop."""
    done = Engine.run(self)
    self.clearScreen()
    
    if self.data.essentialResourcesLoaded():
      if not self.loadingScreenShown:
        self.loadingScreenShown = True
        Dialogs.showLoadingScreen(self, self.data.resourcesLoaded)
        if self.startupLayer:
          self.view.pushLayer(self.startupLayer)
        self.mainloop = self.main
      self.view.render()
    self.video.flip()
    return done

  def clearScreen(self):
    self.svg.clear(*Theme.backgroundColor)

  def main(self):
    """Main state loop."""
    try:
      # Tune the scheduler priority so that transitions are as smooth as possible
      if self.view.isTransitionInProgress():
        self.boostBackgroundThreads(False)
      else:
        self.boostBackgroundThreads(True)
      
      done = Engine.run(self)
      self.clearScreen()
      self.view.render()
      if self.debugLayer:
        self.debugLayer.render(1.0, True)
      self.video.flip()
      return done
    except:
      Log.error("Loading error:")

  def run(self):
    try:
      return self.mainloop()
    except KeyboardInterrupt:
      sys.exit(0)
    except SystemExit:
      sys.exit(0)
    except Exception, e:
      def clearMatrixStack(stack):
        try:
          glMatrixMode(stack)
          for i in range(16):
            glPopMatrix()
        except:
          pass

      if self.handlingException:
        # A recursive exception is fatal as we can't reliably reset the GL state
        Log.error("Recursive exception:")
        sys.exit(1)

      self.handlingException = True
      Log.error("%s, %s: %s" % (e.__class__.__name__,e.__class__, e))
      import traceback
      traceback.print_exc()

      clearMatrixStack(GL_PROJECTION)
      clearMatrixStack(GL_MODELVIEW)
      
      Dialogs.showMessage(self, str(e.__class__.__name__) + ":" + unicode(e))
      self.handlingException = False
      return True
