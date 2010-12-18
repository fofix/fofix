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

from OpenGL.GL import *
from OpenGL import __version__ as OpenGLVersion
import numpy as np
from PIL import Image
import pygame
import gc
import os
import sys
import imp

from Video import Video
from Audio import Audio
from View import View
from Input import Input, KeyListener, SystemEventListener
from Resource import Resource
from Data import Data
from World import World
from Svg import SvgContext
#alarian
#from Song import EAS_DIF, MED_DIF, HAR_DIF, EXP_DIF
from Debug import DebugLayer
from Language import _
import Log
import Config
import Dialogs
from Theme import Theme
import Version
import Mod
import Player
from Shader import shaders
from Song import difficulties, parts

import cmgl

class ConfigOption:
  def __init__(self, id, text):
    self.id   = id
    self.text = text
  
  def __str__(self):
    return self.text
  
  def __repr__(self):
    return self.text
  
  def __cmp__(self, other):
    try:
      return cmp(self.id, other.id)
    except:
      return -1

def sortOptionsByKey(dict):
  a = {}
  for k in dict.keys():
    a[k] = ConfigOption(k, dict[k])
  return a

# evilynux - Grab name and version from Version class.
version = "%s v%s" % ( Version.PROGRAM_NAME, Version.version() )

# define configuration keys
Config.define("engine", "highpriority", bool,  False, text = _("FPS Limiter"),           options = {False: _("On (Set Below)"), True: _("Off (Auto Max FPS)")}, tipText = _("Use this to enable or disable the FPS Limiter. If off, the game will render as many frames as possible. (This is affected by the 'Performance' quickset)"))
Config.define("game",   "adv_settings", bool,  False)
Config.define("video",  "fullscreen",   bool,  False,  text = _("Fullscreen Mode"),      options = {False: _("No"), True: _("Yes")}, tipText = _("Play either in fullscreen ('Yes') or windowed ('No') mode."))
Config.define("video",  "multisamples", int,   4,     text = _("Antialiasing Quality"), options = {0: _("None"), 2: "2x", 4: "4x", 6: "6x", 8: "8x"}, tipText = _("Sets the antialiasing quality of openGL rendering. Higher values reduce jaggediness, but could affect performance. (This is affected by the 'Performance' quickset)"))
Config.define("video",  "disable_fretsfx", bool, False, text = _("Show Fret Glow Effect"), options = {False: _("Yes"), True: _("No")}, tipText = _("Turn on or off the glow that appears around a fret when you press it."))
Config.define("video",  "disable_flamesfx", bool, False, text = _("Show Fret Flame Effect"), options = {False: _("Yes"), True: _("No")}, tipText = _("Turn on or off the flame that appears around a fret when you press it."))
Config.define("video",  "resolution",   str,   "640x480")
Config.define("video",  "fps",          int,   80,    text = _("Frames per Second"), options = dict([(n, n) for n in range(1, 120)]), tipText = _("Set the number of frames to render per second. Higher values are better, but your computer may not be able to keep up. You probably can leave this alone. (This is affected by the 'Performance' quickset)"))
Config.define("video",  "show_fps",     bool,   False,  text = _("Print Frames per Second"), options = {False: _("No"), True: _("Yes")}, tipText = _("This will display your FPS on some screens, and if running from sources will print your FPS there every two seconds."))
Config.define("video",  "hitglow_color", int,  0,     text = _("Fret Glow Color"), options = {0: _("Same as Fret"), 1: _("Actual Color")}, tipText = _("Sets whether or not the fret glow image will be color-masked with the theme-determined fret color."))

Config.define("video",  "shader_use",     bool,   True,  text = _("Use Shaders"), options = {False: _("No"), True: _("Yes")}, tipText = _("Enable or disable the use of shaders. Shaders are visual effects. This must be set to 'Yes' to use the settings below. 'By Theme' leaves it to the theme creator."))
Config.define("video",  "shader_neck",     str,   "theme",  text = _("Neck"), options = {"Disabled":_("Disabled"), "neck": _("Flashing"), "theme": _("By Theme")}, tipText = _("A bright flash along your fretboard reflecting the notes you've hit. 'By Theme' leaves it to the theme creator."))
Config.define("video",  "shader_stage",     str,   "theme",  text = _("Stage"), options = {"Disabled":_("Disabled"), "stage": _("EQ Lightning"), "theme": _("By Theme")}, tipText = _("A visual waveform centered above you fretboard. 'By Theme' leaves it to the theme creator."))
Config.define("video",  "shader_sololight",     str,   "sololight",  text = _("Solo and SP"), options = {"Disabled":_("Disabled"), "sololight": _("Lightnings"), "theme": _("By Theme")}, tipText = _("Enables lightning along the side of your fretboard when you are in solos or use SP. 'By Theme' leaves it to the theme creator."))
Config.define("video",  "shader_tail",     str,   "tail2",  text = _("Tails"), options = {"Disabled":_("Classic"), "tail1": _("Lightnings"), "tail2": _("RB2"), "theme": _("By Theme")}, tipText = _("Sets the tail effect. Choose from classic tails, lightning, or RB2 style. 'By Theme' leaves it to the theme creator."))
Config.define("video",  "shader_notes",     str,   "theme",  text = _("Notes"), options = {"Disabled":_("Disabled"), "notes": _("Metal"), "theme": _("By Theme")}, tipText = _("Gives your notes a metallic sheen. 'By Theme' leaves it to the theme creator."))
Config.define("video",  "shader_cd",     str,   "cd",  text = _("CDs"), options = {"None":_("Disabled"), "cd": _("White"), "theme": _("By Theme")}, tipText = _("Adds a soft lighting effect to CD labels in CD setlist mode."))

#stump
Config.define('video',  'disable_screensaver', bool, True, text=_('Disable Screensaver'), options={True: _('Yes'), False: _('No')}, tipText=_('Set whether the game disables the screensaver while it is running.  Does not necessarily work on all platforms.'))

Config.define("performance",  "starspin", bool,     True,  text = _("Animated Star Notes"), options = {True: _("Yes"), False: _("No")}, tipText = _("This will animate star notes as they come towards you, if that is included in your theme. This can have a hit on performance. (This is affected by the 'Performance' quickset)"))
Config.define("audio",  "frequency",    int,   44100, text = _("Sample Frequency"), options = [8000, 11025, 22050, 32000, 44100, 48000], tipText = _("Set the sample frequency for the audio in the game. You almost certainly want to leave this at 44100 Hz unless you really know what you're doing."))
Config.define("audio",  "bits",         int,   16,    text = _("Sample Bits"), options = [16, 8], tipText = _("Set the sample bits for the audio in the game. You almost certainly want to leave this at 16-bit unless you really know what you're doing."))
Config.define("audio",  "stereo",       bool,  True)

Config.define("network",   "uploadscores", bool,  False, text = _("Upload Highscores"),    options = {False: _("No"), True: _("Yes")}, tipText = _("If enabled, your high scores will be sent to the server to rank you against other players."))
Config.define("network",   "uploadurl_w67_starpower",    str,   "http://www.wembley1967.com/chart/uploadsp.php") # evilynux - new one starting 20080902

Config.define("setlist", "selected_library",  str, "")
Config.define("setlist", "selected_song",     str, "")

Config.define("game", "queue_format", int, 0, text = _("Song Queue System"),     options = {0: _("Disabled"), 1: _("Automatic")}, tipText = _("Enables or disables creating multi-song sets in the setlist."))
Config.define("game", "queue_order",  int, 0, text = _("Song Queue Order"),      options = {0: _("In Order"), 1: _("Random")}, tipText = _("Sets the order in which songs added to the queue will be played."))
Config.define("game", "queue_parts",  int, 0, text = _("Song Queue Parts"),      options = {0: _("Closest Available"), 1: _("Always Ask")}, tipText = _("Choose the behavior when the chosen part is not available in all queued songs. 'Closest Available' will match lead parts to guitar and bass to rhythm, or guitar if no rhythm parts are available. 'Always Ask' brings up the part select screen."))
Config.define("game", "queue_diff",   int, 0, text = _("Song Queue Difficulty"), options = {0: _("Closest Down"), 1: _("Closest Up"), 2: _("Always Ask")}, tipText = _("Choose the behavior when the chosen difficulty is not available in all queued songs. 'Closest Up' will prefer a harder difficulty, while 'Closest Down' will prefer an easier one. 'Always Ask' brings up the difficulty select screen."))

#used internally:
Config.define("game",   "players",             int,  1)
Config.define("game",   "player0",             str,  None)
Config.define("game",   "player1",             str,  None)
Config.define("game",   "player2",             str,  None)
Config.define("game",   "player3",             str,  None)
Config.define("game",   "default_neck",        str,  "defaultneck")
Config.define("game",   "last_theme",          str,  "")
Config.define("game",   "joysticks",           int,  0)

#myfingershurt: default buffersize changed from 4096 to 2048:
Config.define("audio",  "buffersize",   int,   2048,  text = _("Buffer Size"), options = [256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536], tipText = _("Set your audio buffer size. Higher values will reduce audio popping, but increase game lag. Only change this if you are having audio quality issues, and use the lowest value that sounds right."))
Config.define("audio",  "delay",        int,   100,   text = _("A/V Delay"), options = dict([(n, n) for n in range(-1000, 1001)]), tipText = _("Set your A/V delay. Unfortunately for now you have to use trial and error."))
Config.define("audio",  "screwupvol", float,   0.25,  text = _("Screw-Up Sounds"), options = sortOptionsByKey({0.0: _("Off"), .25: _("Quiet"), .5: _("Loud"), 1.0: _("Painful")}), tipText = _("How loud should the sound of your screwing up be? Very."))

#MFH: below are normal 0-10 volume settings.
#akedrou - these are 1-10 (not 0-10) because a setting of 0 will trigger the "miss volume"
Config.define("audio",  "guitarvol",  float,    1.0,  text = _("Active Track Volume"),   options = dict([(n / 100.0, "%02d/10" % (n / 10)) for n in range(10, 110, 10)]), tipText = _("Volume of the parts you are playing."))
Config.define("audio",  "songvol",    float,    0.8,  text = _("Background Volume"),     options = dict([(n / 100.0, "%02d/10" % (n / 10)) for n in range(10, 110, 10)]), tipText = _("Volume of the parts you are not playing."))

Config.define("performance", "game_priority",       int,   2,      text = _("Process Priority"), options = sortOptionsByKey({0: _("Idle"), 1: _("Low"), 2: _("Normal"), 3:_("Above Normal"), 4:_("High"), 5:_("Realtime")}), tipText = _("Change this to increase the priority of the FoFiX process. Don't change this unless you know what you're doing. DO NOT set this to Realtime. Ever."))
Config.define("performance", "restrict_to_first_processor", bool, False, text=_("Restrict to First Core (Win32 Only)"), options={False: _("No"), True: _("Yes")}, tipText=_("Choose whether to restrict the game to running on only the first processor core on the system. Only has an effect under Windows."))  #stump
Config.define("performance", "use_psyco", bool, False, text=_("Use Psyco"), options={False: _("No"), True: _("Yes")}, tipText = _("Enable or disable the Psyco specializing compiler. Tests have indicated the game runs faster with it off."))  #stump
Config.define("game",   "notedisappear",      int,   1,  text = _("Missed Notes"), options = {0: _("Disappear"), 1: _("Keep on going"), 2: _("Turn Red")}, tipText = _("When you miss a note, this sets whether they disappear from the fretboard, scroll off the bottom of the screen or turn red"))

#akedrou - Quickset (based on Fablaculp's Performance Autoset)
Config.define("quickset", "performance", int, 0, text = _("Performance"), options = sortOptionsByKey({0: _("Manual"), 1: _("Pure Speed"), 2: _("Fast"), 3: _("Quality (Recommended)"), 4: _("Max Quality (Slow)")}), tipText = _("Set the performance of your game. You can fine-tune in the advanced menus."))
Config.define("quickset", "gameplay",    int, 0, text = _("Gameplay"),    options = sortOptionsByKey({0: _("Manual"), 1: _("Theme-Based"), 2: _("MIDI Based"), 3: _("RB Style"), 4: _("GH Style"), 5: _("WT Style")}), tipText = _("Sets how the game 'feels' to play. Theme-Based lets the theme creator decide. MIDI Based lets the fretter decide."))
Config.define("game", "lost_focus_pause", bool, True, text = _("Pause on Loss of Focus"), options = {False: _("Off"), True: _("On")}, tipText = _("Set whether the game automatically pauses when another application steals input focus."))

#myfingershurt: HOPO settings
Config.define("game",   "hopo_system",          int,   3,      text = _("HO/PO System"), options = sortOptionsByKey({0: _("None"), 1: _("RF-Mod"), 2: _("GH2 Strict"), 3: _("GH2")}), tipText = _("Set the system used for marking hammer-ons and pull-offs (HO/PO). You can either disable them altogether, use the RF-Mod method, or the GH2 system."))
Config.define("game",   "gh2_sloppy",          int,   0,      text = _("GH2 Sloppy Mode"), options = {0: _("Off"), 1: _("On")}, tipText = _("Sloppy mode allows you to hold higher frets while tapping lower frets during HO/PO sections. This will lower your score by 25%."))
Config.define("coffee", "hopo_frequency",            int,   2,   text = _("HO/PO Frequency"),    options = sortOptionsByKey({0: _("Least"), 1: _("Less"), 2: _("Normal"), 3: _("More"), 4: _("Even More"), 5: _("Most")}), tipText = _("Sets the window used to determine HO/PO notes. Increasing the frequency will reduce your score, and lower settings will give you a tiny bonus."))
Config.define("game", "hopo_after_chord",      int,   1,   text = _("HO/PO After Chord"),    options = {0: _("Off"), 1: _("On")}, tipText = _("This will determine whether or not HO/PO notes can follow a chord. This only applies to the GH2 systems."))
Config.define("game", "accuracy_mode",      int,   2,   text = _("Show Hit Accuracy"),    options = sortOptionsByKey({0: _("Off"), 1: _("Numeric"), 2: _("Friendly"), 3: _("Both")}), tipText = _("Shows how accurate your note hits are. Numeric will give a time in milliseconds, and Friendly will use English to inform you. Both will show, well, both. Useful for determining your A/V delay."))
Config.define("game", "accuracy_pos",      int,   1,   text = _("Hit Accuracy Pos"),    options = sortOptionsByKey({0: _("Center"), 1: _("Top-Right Corner"), 2: _("Bottom-Left Corner"), 3: _("Center-Bottom")}), tipText = _("Sets where the accuracy information will be displayed, if enabled.")) #QQstarS:acc show

Config.define("performance", "max_players", int, 2, text = _("Max Players"), options = {2: 2, 3: 3, 4: 4}, tipText = _("Set the maximum number of players in Co-Op modes. Be aware that higher numbers are associated with a significant drop in performance."))

#myfingershurt:
Config.define("game",  "stage_rotate_delay",        int,   800,   text = _("Slideshow Delay"), options = dict([(n, n) for n in range(0, 10, 1)] + [(n, n) for n in range(10, 50, 10)] + [(n, n) for n in range(50, 2001, 50)]), tipText = _("Sets how long, in milliseconds, to wait between each frame in a stage slideshow."))
Config.define("game",  "stage_animate_delay",        int,   3,   text = _("Animation Delay"), options = dict([(n, n) for n in range(0, 10, 1)] + [(n, n) for n in range(10, 50, 10)] + [(n, n) for n in range(50, 2001, 50)]), tipText = _("Sets how long, in milliseconds, to wait between each frame in a stage animation."))
Config.define("game",   "rotate_stages",           int,  0,  text = _("Stage Slideshow"),  options = {0: _("Off"), 1: _("Random"), 2: _("In Order"), 3: _("BackNForth")}, tipText = _("Sets the method used to rotate frames in a stage slideshow.")) 
Config.define("game",   "stage_animate",           int,  0,  text = _("Stage Animation"),  options = {0: _("Off"), 1: _("Random"), 2: _("In Order"), 3: _("BackNForth")}, tipText = _("Sets the method used to rotate frames in a stage animation.")) 
Config.define("game",   "stage_mode",           int,  0,  text = _("Stage Selection"),  options = {0: _("Random"), 1: _("Default"), 2: _("Blank"), 3: _("Video")}, tipText = _("Set the background for your stage. Default will use the default background, and Blank puts you in a dark room. Probably a lot like the one you're in now."))
Config.define("game",   "song_stage",           int,  1,  text = _("Song Stage"),  options = {0: _("Off"), 1: _("On") }, tipText = _("Fretters can include a stage to be used with their songs. If this is enabled, you can see it.")) #MFH
Config.define("game",   "lyric_mode",           int,   2,   text = _("Script Lyric Display"), options = sortOptionsByKey({0: _("Off"), 1: _("By Song"), 2: _("Always"), 3: _("Dual Lyric Prevention")}), tipText = _("Sets whether lyrics from a script.txt file are displayed. 'By Song' lets the fretter decide. 'Always' always displays script lyrics, if available, and 'Dual Lyric Prevention' will disable script lyrics if there are MIDI lyrics. (This is affected by the 'Performance' quickset)"))#racer
Config.define("game",   "frets_under_notes",          bool, True,  text = _("Frets Under Notes"), options = {False: _("No"), True: _("Yes")}, tipText = _("Sets whether the notes slide under the frets or over them."))
Config.define("game",   "drum_navigation",          bool, True,  text = _("Drum Navigation"), options = {False: _("Off"), True: _("On")}, tipText = _("If enabled, drum keys will be allowed to navigate menus. If not, only guitar keys and keyboard master keys will."))

Config.define("game",   "ignore_open_strums",          bool, True,  text = _("Ignore Open Strums"), options = {False: _("No"), True: _("Yes")}, tipText = _("If enabled, strumming without holding any frets down won't be counted."))
Config.define("performance",   "static_strings",          bool, True,  text = _("Static Strings"), options = {False: _("No"), True: _("Yes")}, tipText = _("If enabled, the 'strings' on your fretboard will not scroll."))
Config.define("game",   "whammy_saves_starpower",          bool, False,  text = _("Effects Save SP"), options = {False: _("No"), True: _("Yes")}, tipText = _("If enabled, whammying while in SP will slow down its decrease. And your score will be handicapped by 5%."))
Config.define("game",   "hopo_indicator",          bool, False,  text = _("Show HO/PO Indicator"), options = {False: _("No"), True: _("Yes")}, tipText = _("If enabled, 'HOPO' will appear in game. When there are HOPO notes active, it will turn white."))
Config.define("game",   "quickplay_tiers",          int, 1,  text = _("Use Tiers in Quickplay"), options = {0: _("Off"), 1: _("Normal"), 2: _("Sorting")}, tipText = _("Sets whether to mark tiers in quickplay mode. 'Normal' will use the career tiers and 'Sorting' will insert tiers based on the current sort order."))
Config.define("performance",   "star_score_updates",          int, 1,  text = _("Star Updates"), options = {0: _("On Hit"), 1: _("Score Change")}, tipText = _("If set to 'On Hit', your star score will only be checked when you hit a note. If set to 'Score Change', your star score will constantly update. (This is affected by the 'Performance' quickset)"))
Config.define("performance",   "star_continuous_fillup",          bool, True,  text = _("Partial Star Continuous Fillup"), options = {False: _("No"), True: _("Yes")}, tipText = _("Sets whether your partial stars will fill up gradually ('Yes') or in chunks. (This is affected by the 'Performance' quickset)")) #stump
Config.define("game", "resume_countdown", int, 1, text = _("Countdown on Resume"), options = {0: _("No"), 1: _("Yes")}, tipText = _("If enabled, there will be a three second countdown when you unpause."))

Config.define("game", "script_lyric_pos",      int,   0,   text = _("Script Lyric Position"),    options = {0: _("Bottom"), 1: _("Top")}, tipText = _("Display script lyrics at either the bottom or top of the screen.")) #MFH - script.txt lyric display position


Config.define("game",   "star_claps",          bool, False,  text = _("Starpower Claps"), options = {False: _("Off"), True: _("On")}, tipText = _("Enables a clapping sound effect to be used on the beats in Starpower."))
Config.define("audio", "disable_preview",      bool, True,  text = _("Song Previews"), options = {False: _("Automatic"), True: _("Yellow Fret (#3)")}, tipText = _("If set to 'Automatic', songs will automatically start previewing when you select them. Otherwise you must press the third fret."))
Config.define("game", "rb_sp_neck_glow",      bool, False,  text = _("RB SP Neck Glow"), options = {False: _("Off"), True: _("On")}, tipText = _("Sets a neck glow effect during SP in RB-type themes."))
Config.define("game",   "sp_notes_while_active",  int,  2,  text = _("SP Refill Mode"),  options = sortOptionsByKey({0: _("None"), 1: _("By Theme"), 2: _("By MIDI Type"), 3: _("Always")}), tipText = _("Sets whether you can earn more starpower while using it. In 'By MIDI Type', only MIDIs that mark RB-style sections will use this. (This is set by the 'Gameplay' quickset)")) 

#MFH wuz here.  Yeah.
Config.define("game", "kill_debug",      bool, False,  text = _("Effects Debug"), options = {False: _("Off"), True: _("On")}, tipText = _("If enabled, will show on-screen the raw data of your killswitch/whammy."))
Config.define("game", "drum_sp_mode",      int, 0,  text = _("Drum SP"), options = {0: _("Auto / Fills"), 1: _("Manual / Fills")}, tipText = _("Determines how drum starpower is activated when there are no drum fills. Auto will automatically activate when available, and Manual will wait for the 'Starpower' button to be pressed."))
Config.define("game", "large_drum_neck",      bool, False,  text = _("Large Drum Neck"), options = {False: _("No"), True: _("Yes")}, tipText = _("If enabled, will show a larger neck when playing drums."))
Config.define("game", "bass_groove_neck",      int, 2,  text = _("Bass Groove Neck"), options = {0: _("Off"), 1: _("Replace"), 2: _("Overlay")}, tipText = _("Sets the style of the Bass Groove neck. 'Replace' replaces your neck with the special neck, while 'Overlay' lays the neck over top."))
Config.define("game", "guitar_solo_neck",      int, 2,  text = _("Guitar Solo Neck"), options = {0: _("Off"), 1: _("Replace"), 2: _("Overlay")}, tipText = _("Sets the style of the Guitar Solo neck. 'Replace' replaces your neck with the special neck, while 'Overlay' lays the neck over top."))
Config.define("game", "4x_neck",      int, 2,  text = _("4x Neck"), options = {0: _("Off"), 1: _("Replace"), 2: _("Overlay")}, tipText = _("Sets the style of the 4x multiplier neck. 'Replace' replaces your neck with the special neck, while 'Overlay' lays the neck over top."))
Config.define("game", "show_unused_text_events",      bool, False,  text = _("Show Unused Events"), options = {False: _("No"), True: _("Yes")}, tipText = _("If enabled, various MIDI events not used by the game will be shown on-screen."))
Config.define("game", "bass_kick_sound",      bool, False,  text = _("Kick Bass Sound"), options = {False: _("Off"), True: _("On")}, tipText = _("If enabled, you'll hear a kick bass sound when you use the kick pedal."))
Config.define("game", "rb_midi_lyrics",           int,  1,   text = _("Show Lyrics in All Modes"), options = {0: _("No"), 1: _("Single Player"), 2: _("Always")}, tipText = _("Sets whether or not MIDI lyrics will be displayed in modes without a vocalist. 'Single Player' will only show lyrics when in Solo modes."))
Config.define("game", "rb_midi_sections",           int,  0,   text = _("Show MIDI Sections"), options = {0: _("No"), 1: _("Single Player"), 2: _("Always")}, tipText = _("Sets whether or not to scroll the names of sections as marked in the MIDI files."))
Config.define("game", "key_checker_mode",      int, 1,  text = _("Key Conflicts"), options = sortOptionsByKey({0: _("Don't check"), 1: _("Notify"), 2: _("Enforce")}), tipText = _("Sets how the game handles key conflicts. 'Don't check' doesn't check, but conflicts will affect play. 'Notify' will inform you, but allow you to continue, and 'Enforce' will not allow you to exit the menu until all key conflicts have been resolved."))
Config.define("performance", "in_game_stats",      int, 0,  text = _("Show In-Game Stats"), options = {0: _("Off"), 1: _("By Theme"), 2: _("On")}, tipText = _("Sets whether or not to show detailed stats as you play. 'By Theme' leaves it to the theme creator."))
Config.define("game", "in_game_stars",      int, 1,  text = _("Show Stars In-Game"), options = {0: _("Off"), 1: _("By Theme"), 2: _("On")}, tipText = _("Sets whether or not to show your star score as you play. 'By Theme' leaves it to the theme creator."))
Config.define("game", "partial_stars",      int, 1,  text = _("Show Partial Stars"), options = {0: _("Off"), 1: _("On")}, tipText = _("Sets whether or not to show partial stars, if available"))
Config.define("game", "hopo_debug_disp",      int, 0,  text = _("HO/PO Debug"), options = {0: _("Off"), 1: _("On")}, tipText = _("If enabled, various log messages will be recorded regarding the HO/PO system. Please leave this disabled if submitting logs for bug reports unless you are certain it is necessary."))
Config.define("game", "gsolo_accuracy_disp",      int, 1,  text = _("Show Solo Stats"), options = {0: _("Off"), 1: _("Percent"), 2: _("Detail")}, tipText = _("Sets whether to show your solo results when you finish a solo. 'Percent' will only show the percentage, while 'Detail' includes additional information."))
Config.define("game", "decimal_places",      int, 1,  text = _("Stat Decimal Places"), options = dict([(n, n) for n in range(0, 3)]), tipText = _("Determines how many decimal places will be noted in displaying stats."))
Config.define("game", "star_scoring",       int, 3,     text = _("Star Scoring Style"), options = sortOptionsByKey({0: _("Accuracy"), 1: _("GH"), 2: _("RB"), 3: _("RB+GH"), 4: _("RB2")}), tipText = _("Sets which system to use to calculate your star score."))#MFH
Config.define("game", "career_star_min",    int, 3,     text = _("Career Mode Advance"), options = {0: _("0 (Song Finish)"), 1: _("1 Star"), 2: _("2 Stars"), 3: _("3 Stars"), 4: _("4 Stars"), 5: _("5 Stars"), 6: _("6 (Gold Stars)"), 7: _("7 (Full Combo)")}, tipText = _("Determine how many stars are needed on a song before it is unlocked in career mode."))
Config.define("game", "gsolo_acc_pos",       int, 3,     text = _("Solo Stat Positioning"), options = sortOptionsByKey({0: _("Right"), 1: _("Center"), 2: _("Left"), 3: _("Rock Band")}), tipText = _("Sets where your solo result stats will be displayed."))#MFH,(racer: added RB)
Config.define("game", "bass_groove_enable",       int, 1,     text = _("Bass Groove"), options = {0: _("Off"), 1: _("By Theme"), 2: _("By MIDI"), 3: _("On")}, tipText = _("Enable or disable bass groove (additional score multiplier for bass)")) #MFH
Config.define("game", "T_sound",      int, 2,  text = _("Drum Miss Penalty"), options = {0: _("Always"), 1: _("Song Start"), 2: _("First Note")}, tipText = _("Determines when drum hits count as misses: When the song begins, after the first note, or always.")) #Faaa Drum sound
Config.define("game", "game_time",       int, 1,     text = _("Time Display Format"), options = {0: _("Off"), 1: _("Countdown"), 2: _("Elapsed")}, tipText = _("Sets whether the song time is displayed as time elapsed, time remaining, or not at all")) #MFH
Config.define("game", "gfx_version_tag",       int, 1,     text = _("Show Theme Version Tag"), options = {0: _("No"), 1: _("Yes")}, tipText = _("Places the theme's version tag over menus and dialogs.")) #MFH
Config.define("game", "p2_menu_nav",       int, 1,     text = _("Menu Navigation"), options = {0: _("P1 Only"), 1: _("All Players")}, tipText = _("Sets whether all players can navigate the menu, or only the controller set as Player 1 and the master keys.")) #MFH
Config.define("game", "in_game_font_shadowing",      bool, False,  text = _("In-Game Font Shadow"), options = {False: _("Off"), True: _("On")}, tipText = _("Sets whether or not a shadowed font will be used, if available."))
Config.define("audio", "mute_last_second",       int, 0,     text = _("Mute Last Second"), options = {0: _("No"), 1: _("Yes")}, tipText = _("Cuts the volume with one second remaining to prevent any pops when the song ends.")) #MFH
Config.define("game", "result_cheer_loop",       int, 2,     text = _("Results Cheer Loop"), options = {0: _("Off"), 1: _("Theme"), 2: _("On")}, tipText = _("Sets whether the cheering sound heard on the result screen will loop. 'Theme' leaves it to the theme creator.")) #MFH
Config.define("game",  "cheer_loop_delay",        int,   550,   text = _("Cheer Loop Delay"), options = dict([(n, n) for n in range(0, 10, 1)] + [(n, n) for n in range(10, 50, 10)] + [(n, n) for n in range(50, 2001, 50)]), tipText = _("Sets the time, in milliseconds, to wait before playing the result cheer again (if looping is enabled)."))
Config.define("game", "miss_pauses_anim",       int, 0,     text = _("Miss Pauses Anim"), options = {0: _("Off"), 1: _("On")}, tipText = _("When enabled, missing a note will pause the stage animation.")) #MFH
Config.define("game", "song_hopo_freq",       int, 1,     text = _("Song HO/PO Freq"), options = {0: _("Off"), 1: _("On")}, tipText = _("Sets whether or not to use the HO/PO Frequency setting determined by the fretter, if available.")) #MFH
Config.define("game",   "mute_drum_fill",           int, 1,    text = _("Mute Drum Track During Fills"), options = {0: _("No"), 1:_("Yes")}, tipText = _("Sets whether or not the drum track will be muted during drum fills (so you can hear yourself have at it!)"))
Config.define("game",   "sustain_muting",          int, 1,    text = _("Sustain Muting"), options = sortOptionsByKey({0: _("Never Mute"), 1: _("Very Early"), 2: _("Early"), 3: _("Standard"), 4: _("Always Mute")}), tipText = _("Sets the window used to determine whether or not to mute a dropped sustain note. 'Early' means it will only mute when you drop the sustain relatively early."))
Config.define("game",   "solo_frame",          int, 1,    text = _("Show Solo Frame"), options = {0: _("Off"), 1: _("On")}, tipText = _("Sets whether to show a frame around the solo stats, if available."))
Config.define("game",   "mark_solo_sections",  int, 1,    text = _("Enable Guitar Solos"), options = sortOptionsByKey({0: _("Never"), 1: _("Always"), 2: _("By Theme"), 3: _("MIDI Only")}), tipText = _("Sets the logic used to mark solos. 'Always' will mark solos in sections if available. 'By Theme' leaves it to the theme creator. 'MIDI Only' only enables solos marked with the MIDI marker note."))
Config.define("game",   "starpower_mode",          int, 2,    text = _("SP Mode"), options = {0: _("Off"), 1: _("FoF"), 2: _("Auto MIDI")}, tipText = _("Sets the logic used to determine starpower phrases. 'FoF' will generate paths based on the number of notes. 'Auto MIDI' will use MIDI markers to determine the paths, and fall back on the FoF mode if none are available."))
Config.define("game",   "incoming_neck_mode",          int, 2,    text = _("Inc. Neck Mode"), options = sortOptionsByKey({0: _("Off"), 1: _("Start Only"), 2: _("Start & End")}), tipText = _("Sets how and whether to render incoming solo necks. 'Start Only' will scroll it in but not out, while 'Start & End' does both."))
Config.define("game", "big_rock_endings",           int,  2,   text = _("Big Rock Endings"), options = sortOptionsByKey({0: _("Off"), 1: _("By Theme"), 2: _("On")}), tipText = _("Enable or disable big rock endings. 'By Theme' leaves it to the theme creator."))
Config.define("game",  "neck_alpha",  float,    1.0,  text = _("Main Neck"),   options = dict([(n / 100.0, "%3d%s" % (n,"%")) for n in range(0, 110, 10)]), tipText = _("Set the transparency of the main neck. 100% is fully visible."))
Config.define("game",  "solo_neck_alpha",  float,    1.0,  text = _("Solo Neck"),   options = dict([(n / 100.0, "%3d%s" % (n,"%")) for n in range(0, 110, 10)]), tipText = _("Set the transparency of the solo neck. 100% is fully visible."))
Config.define("game",  "bg_neck_alpha",  float,    1.0,  text = _("Bass Groove Neck"),   options = dict([(n / 100.0, "%3d%s" % (n,"%")) for n in range(0, 110, 10)]), tipText = _("Set the transparency of the bass groove neck. 100% is fully visible."))
Config.define("game",  "fail_neck_alpha",  float,    1.0,  text = _("Fail Neck"),   options = dict([(n / 100.0, "%3d%s" % (n,"%")) for n in range(0, 110, 10)]), tipText = _("Set the transparency of the failing neck. 100% is fully visible."))
Config.define("game",  "4x_neck_alpha",  float,    1.0,  text = _("4x Neck"),   options = dict([(n / 100.0, "%3d%s" % (n,"%")) for n in range(0, 110, 10)]), tipText = _("Set the transparency of the 4x multiplier neck. 100% is fully visible."))
Config.define("game",  "overlay_neck_alpha",  float,    1.0,  text = _("Overlay Neck"),   options = dict([(n / 100.0, "%3d%s" % (n,"%")) for n in range(0, 110, 10)]), tipText = _("Set the transparency of neck overlays. 100% is fully visible."))
Config.define("game",  "necks_alpha",  float,    1.0,  text = _("All Necks"),   options = dict([(n / 100.0, "%3d%s" % (n,"%")) for n in range(0, 110, 10)]), tipText = _("Set the master transparency of all necks. 100% is fully visible."))
Config.define("songlist",  "nil_show_next_score", int, 0, text = _("Show Any Available Score"), options = {0: _("Off"), 1: _("On")}, tipText = _("When set to 'On', this will look for any available score on the currently selected instrument for setlist score display, if one is not available at the chosen difficulty."))

Config.define("game", "scroll_delay",             int, 500,  text = _("Scroll Delay"), options = dict([(n, n) for n in range(100, 2001, 100)]), tipText = _("Sets how long, in milliseconds, to wait before beginning to scroll."))
Config.define("game", "scroll_rate",              int, 50,   text = _("Scroll Rate"),  options = dict([(n, 10-((n/10)-1)) for n in range(10, 101, 10)]), tipText = _("Sets how quickly menus will scroll."))

#MFH - debug settings
Config.define("debug",   "use_unedited_midis",          int, 1,    text = _("Use (notes-unedited.mid)"), options = {0: _("No"), 1: _("Yes")}, tipText = _("Sets whether to look for (and use) a 'notes-unedited.mid' before 'notes.mid'. There's no reason to change this."))
Config.define("debug",   "show_freestyle_active",          int, 0,    text = _("Show Fill Status"), options = {0: _("No"), 1: _("Yes")}, tipText = _("When enabled, whether or not you are in a drum fill/freestyle ending will be displayed in text on the screen."))
Config.define("debug",   "show_bpm",          int, 0,    text = _("Show BPM"), options = {0: _("No"), 1: _("Yes")}, tipText = _("When enabled, the current song BPM will be shown on screen."))
Config.define("debug",   "use_new_vbpm_beta",          int, 0,    text = _("New BPM Logic"), options = {0: _("Off"), 1: _("On")}, tipText = _("If enabled, the game will attempt to use the new BPM logic. This is not a finished feature. Use at your own risk."))
Config.define("debug", "use_new_song_database", bool, False, text=_("New Song Database Code"), options={False: _("Off"), True: _("On")}, tipText=_("Activates the new, incomplete song database code."))  #stump

Config.define("debug",   "show_raw_vocal_data", int, 0,  text = _("Show Raw Vocal Data"), options = {0: _("Off"), 1: _("On")}, tipText = _("If enabled, various information about the microphone input will be show in text on screen. Probably only needed for vocal debugging."))

Config.define("audio",  "speed_factor",  float,    1.0,  text = _("Speed Factor"),   options = sortOptionsByKey({1.0: _("1.00x"), 0.75: _("0.75x"), 0.50: _("0.50x"), 0.25: _("0.25x")}), tipText = _("Sets the speed to play the audio at. Your score will be severely penalized if you slow the music down."))  #MFH

Config.define("audio",  "whammy_effect",  int,    0,  text = _("Effects Mode"),   options = {0: _("Killswitch"), 1: _("Pitchbend")}, tipText = _("Sets whether to use a killswitch or pitchbend as the effect on your whammy."))  #MFH


#MFH - log settings
Config.define("game",   "log_ini_reads",          int, 0,    text = _("Log INI Reads"), options = {0: _("No"), 1: _("Yes")}, tipText = _("Logs any read to an INI file. This is unnecessary information in bug reports; please leave it disabled unless you are certain it is relevant."))
Config.define("game",   "log_class_inits",          int, 0,    text = _("Log Class Inits"), options = {0: _("No"), 1: _("Yes")}, tipText = _("Logs most class initializations in '__init__'. This is unnecessary information in bug reports; please leave it disabled unless you are certain it is relevant."))
Config.define("game",   "log_loadings",          int, 0,    text = _("Log Loadings"), options = {0: _("No"), 1: _("Yes")}, tipText = _("Logs resource loads. This is unnecessary information in bug reports; please leave it disabled unless you are certain it is relevant."))
Config.define("game",   "log_sections",          int, 0,    text = _("Log MIDI Sections"), options = {0: _("No"), 1: _("Yes")}, tipText = _("Logs MIDI sections. This is unnecessary information in bug reports; please leave it disabled unless you are certain it is relevant."))
Config.define("game",   "log_undefined_gets",          int, 0,    text = _("Log Undefined GETs"), options = {0: _("No"), 1: _("Yes")}, tipText = _("Logs attempts to read an undefined config key. This is unnecessary information."))
Config.define("game",   "log_marker_notes",          int, 0,    text = _("Log Marker Notes"), options = {0: _("No"), 1: _("Yes")}, tipText = _("Logs MIDI marker notes (solo, SP, etc). This is unnecessary information in bug reports; please leave it disabled unless you are certain it is relevant."))
Config.define("game",   "log_starpower_misses",          int, 0,    text = _("Log SP Misses"), options = {0: _("No"), 1: _("Yes")}, tipText = _("Logs SP phrase misses. This is unnecessary information."))
Config.define("log",   "log_unedited_midis",          int, 0,    text = _("Log Unedited MIDIs"), options = {0: _("No"), 1: _("Yes")}, tipText = _("Logs when notes-unedited.mid is used. This is unnecessary information."))
Config.define("log",   "log_lyric_events",          int, 0,    text = _("Log Lyric Events"), options = {0: _("No"), 1: _("Yes")}, tipText = _("Logs MIDI lyric events. This is unnecessary information in bug reports; please leave it disabled unless you are certain it is relevant."))
Config.define("log",   "log_tempo_events",          int, 0,    text = _("Log Tempo Events"), options = {0: _("No"), 1: _("Yes")}, tipText = _("Logs MIDI tempo events. This is unnecessary information in bug reports; please leave it disabled unless you are certain it is relevant."))
Config.define("log",   "log_image_not_found",       int, 0,    text = _("Log Missing Images"), options = {0: _("No"), 1:_("Only on single images"), 2:_("Always")}, tipText = _("Logs when files loaded are not found. 'Only on single images' skips logging when directories are loaded."))

Config.define("game", "beat_claps",          bool, False,  text = _("Practice Beat Claps"), options = {False: _("Off"), True: _("On")}, tipText = _("Enables clap sound effects on every beat in practice mode.")) #racer
Config.define("game", "HSMovement",      int,   1,   text = _("Change Score Display"),    options = {0: _("Auto"), 1: _("Blue Fret (#4)")}, tipText = _("Sets whether to change the setlist high score difficulty automatically or with the fourth fret.")) #racer

#Q
Config.define("game", "battle_Whammy",      int,   1,   text = _("Whammy"),    options = {0: _("Off"), 1: _("On")}, tipText = _("Makes opponent miss notes until the whammy bar is pushed a few times")) 
Config.define("game", "battle_Diff_Up",      int,   1,   text = _("Difficulty Up"),    options = {0: _("Off"), 1: _("On")}, tipText = _("Ups opponent's difficulty for a while (if not playing on Expert)")) 
Config.define("game", "battle_String_Break",      int,   1,   text = _("String Break"),    options = {0: _("Off"), 1: _("On")}, tipText = _("Breaks a string, causing your opponent to miss notes on that fret until they push the fret button several times.")) 
Config.define("game", "battle_Double",      int,   1,   text = _("Double Notes"),    options = {0: _("Off"), 1: _("On")}, tipText = _("Makes single notes into chords, and chords into even bigger ones.")) 
Config.define("game", "battle_Death_Drain",      int,   2,   text = _("Death Drain"),    options = {0: _("Off"), 1: _("On"), 2: _("Sudden Death Only")}, tipText = _("Drains your opponents life until they die. 'Sudden Death Only' keeps this from appearing until you reach sudden death mode.")) 
Config.define("game", "battle_Amp_Overload",      int,   1,   text = _("Amp Overload"),    options = {0: _("Off"), 1: _("On")}, tipText = _("Makes opponent's amp flip out, making notes disappear and reappear randomly.")) 
Config.define("game", "battle_Switch_Controls",      int,   1,   text = _("Switch Controls"),    options = {0: _("Off"), 1: _("On")}, tipText = _("Switches opponent to (or from) lefty mode for a bit!")) 
Config.define("game", "battle_Steal",      int,   1,   text = _("Steal Object"),    options = {0: _("Off"), 1: _("On")}, tipText = _("Steals an object your opponent has.")) 
Config.define("game", "battle_Tune",      int,   1,   text = _("Guitar Tune"),    options = {0: _("Off"), 1: _("On")}, tipText = _("Makes opponent miss all notes until they play a scale.")) 

#blazingamer
Config.define("game", "congrats",       bool, True,     text = _("Score SFX"),             options = {True: _("On"), False: _("Off")}, tipText = _("Sets whether or not to have Jurgen taunt (or, I suppose, congratulate) you at the end of a song."))#blazingamer
Config.define("game", "starfx",       bool, True,     text = _("GH SP Lights"),             options = {True: _("On"), False: _("Off")}, tipText = _("Sets whether to fade images over the starpower bulbs in GH themes when fully lit."))#blazingamer
Config.define("game", "small_rb_mult",      int, 1,     text = _("RB Small 1x Multiplier"),             options = {0: _("Off"), 1: _("By Theme"), 2: _("On")}, tipText = _("When enabled, RB-type themes will have a smaller mult image when the multiplier is at 1x. 'By Theme' leaves it to the theme creator."))#blazingamer
Config.define("game", "nstype",       int, 2,     text = _("Board Speed Mode"),             options = sortOptionsByKey({0: _("BPM"), 1: _("Difficulty"), 2: _("BPM & Diff"), 3: _("Percentage")}), tipText = _("Sets what determines the speed of the scrolling notes."))
Config.define("game", "lphrases",       bool, True,     text = _("Loading Phrases"),             options = {True: _("On"), False: _("Off")}, tipText = _("Sets whether or not to use loading phrases while loading a song"))
Config.define("performance", "killfx",       int, 0,     text = _("Effects Display Mode"),             options = {0: _("Static"), 1: _("Animated"), 2: _("Off")}, tipText = _("Sets whether or not the whammy effect is animated. (This is affected by the 'Performance' quickset)"))
Config.define("coffee", "songfilepath",       bool, True,     text = _("Show Filepath"),             options = {True: _("Show"), False: _("Hide")}, tipText = _("Sets whether or not to show the filepath of the song."))
Config.define("coffee", "noterotate",       bool, False,     text = _("3D Note Rotation"),             options = {True: _("Old"), False: _("New")}, tipText = _("Sets the manner of 3D Note Rotation."))
Config.define("coffee", "game_phrases",       int, 2,     text = _("Show In-Game Text"),             options = {0: _("Never"), 1: _("Only Note Streaks"), 2: _("Always")}, tipText = _("Sets whether or not to show text in-game. This includes note streaks and 'Starpower Ready'. (This is affected by the 'Performance' quickset)"))
Config.define("game", "preload_labels",          bool, False,     text = _("Preload Song Labels"),     options = {True: _("Yes"), False: _("No")}, tipText = _("Sets whether to preload all song labels on load. With large setlists, this option is extremely slow."))
Config.define("game", "songcovertype",        bool, False,     text = _("Label Type"),      options = {True: _("CD Labels"), False: _("Album Covers")}, tipText = _("Sets whether to show CD labels or album covers as the art."))
Config.define("game", "keep_play_count", int, 1, text = _("Remember Play Count"), options = {0: _("No"), 1: _("Yes")}, tipText = _("Keeps track of how many times you've played each song."))
Config.define("game", "tut",       bool, False) #-tutorial
Config.define("video", "counting",       bool, False,     text = _("Show at Song Start"),             options = {True: _("Part"), False: _("Countdown")}, tipText = _("Sets whether to show a countdown or your name and part at the song's start."))
Config.define("fretboard", "ovrneckoverlay",       bool, True,     text = _("Overdrive Neck"),             options = {True: _("Overlay"), False: _("Replace")}, tipText = _("Sets the style of the Overdrive neck. 'Replace' replaces your neck with the special neck, while 'Overlay' lays the neck over top."))

Config.define("game",   "note_hit_window",          int, 2,    text = _("Note Hit Window"), options = sortOptionsByKey({0: _("Tightest"), 1: _("Tight"), 2: _("Standard"), 3: _("Wide"), 4: _("Widest")}), tipText = _("Sets how accurate you need to be while playing."))#racer blazingamer

Config.define("handicap",   "early_hit_window",          int, 0,    text = _("Early Hit Window"), options = sortOptionsByKey({0: _("Auto"), 1: _("None (RB2)"), 2: _("Half (GH2)"), 3: _("Full (FoF)")}), tipText = _("Sets how much time before the note is part of the hit window. 'Auto' uses the MIDI to determine."))  #MFH
Config.define("handicap",  "detailed_handicap",       int, 1,     text = _("Show Detailed Handicap"), options = {0: _("No"), 1: _("Yes")}, tipText = _("Shows the handicaps individually on the result screen."))


Config.define("game",   "disable_vbpm",        bool,  False,  text = _("Disable Variable BPM"),  options = {False: _("No"), True: _("Yes")}, tipText = _("This will disable the use of the Variable BPM logic."))
Config.define("game",   "sort_direction",      int, 0,    text = _("Sort Direction"), options = {0: _("Ascending"), 1: _("Descending")}, tipText = _("Choose whether to sort in ascending (A-Z) or descending (Z-A) order."))
Config.define("game",   "sort_order",          int,   0,      text = _("Sort Setlist By"), options = sortOptionsByKey({0: _("Title"), 1: _("Artist"), 2: _("Times played"), 3: _("Album"), 4: _("Genre"), 5: _("Year"), 6: _("Band Difficulty"), 7: _("Difficulty"), 8:_("Song Collection")}), tipText = _("Choose how to sort the setlist by default."))
Config.define("game",   "whammy_changes_sort_order", bool, True, text = _("Whammy Changes Sort Order"), options = {False: _("No"), True: _("Yes")}, tipText = _("When enabled, pressing the whammy bar will change the sort order in the setlist."))
Config.define("fretboard",   "neck_intro_animation",        int,   4,      text = _("Neck Intro Animation"), options = sortOptionsByKey({0: _("Original"), 1: _("Guitar Hero"), 2: _("Rock Band"), 3: _("Off"), 4: _("Theme")}), tipText = _("Sets what the neck animation looks like. Set it to 'Theme' to leave it to the theme creator.")) #weirdpeople
Config.define("fretboard",   "point_of_view",                 int,   5,      text = _("Point Of View"), options = sortOptionsByKey({0: _("FoF"), 1: _("GH3"), 2: _("Rock Band"), 3: _("GH2"), 4: _("Rock Rev"), 5: _("Theme")}), tipText = _("Sets the camera's point of view. Set it to any game, or set it to 'Theme' to leave it to the theme creator.")) #Racer, Blazingamer
Config.define("game",   "party_time",          int,   30,     text = _("Party Mode Timer"), options = dict([(n, n) for n in range(1, 99)]), tipText = _("Sets the timer in Party Mode."))
Config.define("performance",   "disable_libcount",    bool,  True,  text = _("Show Setlist Size"),    options = {False: _("Yes"), True: _("No")}, tipText = _("Show the number of songs inside of each setlist."))

Config.define("game",   "jurg_p0",             bool, False,   text = _("P1 AI"), options = {True: _("On"), False: _("Off")}, tipText = _("Enable or disable the player 1 AI"))
Config.define("game",   "jurg_skill_p0",        int, 5,   text = _("P1 AI Personality"), options = {0: _("1. KiD"), 1: _("2. Stump"), 2: _("3. akedRobot"), 3: _("4. Q"), 4: _("5. MFH"), 5: _("6. Jurgen")}, tipText = _("Set the personality of the player 1 AI. The numbers correspond with their skill."))
Config.define("game",   "jurg_logic_p0",            int,   1,      text = _("P1 AI Logic"), options = sortOptionsByKey({0: _("Original"), 1: _("MFH-Early"), 2: _("MFH-OnTime1"), 3: _("MFH-OnTime2")}), tipText = _("Set the logic used for the player 1 AI. 'Original' cannot handle fast sections. 'MFH-Early' attempts to hit notes as they enter the hit window. 'MFH-OnTime' are implementations that attempt to hit the notes as they happen, like a real player."))

Config.define("game",   "jurg_p1",             bool, False,   text = _("P2 AI"), options = {True: _("On"), False: _("Off")}, tipText = _("Enable or disable the player 2 AI"))
Config.define("game",   "jurg_skill_p1",        int, 5,   text = _("P2 AI Personality"), options = {0: _("1. KiD"), 1: _("2. Stump"), 2: _("3. akedRobot"), 3: _("4. Q"), 4: _("5. MFH"), 5: _("6. Jurgen")}, tipText = _("Set the personality of the player 2 AI. The numbers correspond with their skill."))
Config.define("game",   "jurg_logic_p1",            int,   1,      text = _("P2 AI Logic"), options = sortOptionsByKey({0: _("Original"), 1: _("MFH-Early"), 2: _("MFH-OnTime1"), 3: _("MFH-OnTime2")}), tipText = _("Set the logic used for the player 2 AI. 'Original' cannot handle fast sections. 'MFH-Early' attempts to hit notes as they enter the hit window. 'MFH-OnTime' are implementations that attempt to hit the notes as they happen, like a real player."))

Config.define("game",   "jurg_p2",             bool, False,   text = _("P3 AI"), options = {True: _("On"), False: _("Off")}, tipText = _("Enable or disable the player 3 AI"))
Config.define("game",   "jurg_skill_p2",        int, 5,   text = _("P3 AI Personality"), options = {0: _("1. KiD"), 1: _("2. Stump"), 2: _("3. akedRobot"), 3: _("4. Q"), 4: _("5. MFH"), 5: _("6. Jurgen")}, tipText = _("Set the personality of the player 3 AI. The numbers correspond with their skill."))
Config.define("game",   "jurg_logic_p2",            int,   1,      text = _("P3 AI Logic"), options = sortOptionsByKey({0: _("Original"), 1: _("MFH-Early"), 2: _("MFH-OnTime1"), 3: _("MFH-OnTime2")}), tipText = _("Set the logic used for the player 3 AI. 'Original' cannot handle fast sections. 'MFH-Early' attempts to hit notes as they enter the hit window. 'MFH-OnTime' are implementations that attempt to hit the notes as they happen, like a real player."))

Config.define("game",   "jurg_p3",             bool, False,   text = _("P4 AI"), options = {True: _("On"), False: _("Off")}, tipText = _("Enable or disable the player 4 AI"))
Config.define("game",   "jurg_skill_p3",        int, 5,   text = _("P4 AI Personality"), options = {0: _("1. KiD"), 1: _("2. Stump"), 2: _("3. akedRobot"), 3: _("4. Q"), 4: _("5. MFH"), 5: _("6. Jurgen")}, tipText = _("Set the personality of the player 4 AI. The numbers correspond with their skill."))
Config.define("game",   "jurg_logic_p3",            int,   1,      text = _("P4 AI Logic"), options = sortOptionsByKey({0: _("Original"), 1: _("MFH-Early"), 2: _("MFH-OnTime1"), 3: _("MFH-OnTime2")}), tipText = _("Set the logic used for the player 4 AI. 'Original' cannot handle fast sections. 'MFH-Early' attempts to hit notes as they enter the hit window. 'MFH-OnTime' are implementations that attempt to hit the notes as they happen, like a real player."))

#akedrou
Config.define("game",   "midi_lyric_mode",     int, 2,     text = _("Lyric Display Mode"),  options = {0: _("Scrolling"), 1: _("Simple Lines"), 2: _("2-Line")}, tipText = _("Sets the display mode for MIDI lyrics. Both 'Simple Lines' and '2-Line' will show as single phrases when playing the vocal part."))
Config.define("game",   "vocal_scroll",        int, 2,     text = _("Lyric Speed Mode"),    options = sortOptionsByKey({0: _("BPM"), 1: _("Difficulty"), 2: _("BPM & Diff")}), tipText = _("Sets what determines the speed of the scrolling lyrics."))
Config.define("game",   "vocal_speed",         int, 100,   text = _("Lyric Speed Percent"), options = dict([(n, n) for n in range(10, 410, 10)]), tipText = _("Sets how quickly lyrics will scroll."))

Config.define("game", "use_graphical_submenu", int,   1,      text = _("Graphical Submenus"), options = {0: _("Disabled"), 1: _("Enabled")}, tipText = _("Enable or disable the use of graphical submenus."))

Config.define("audio",  "enable_crowd_tracks", int,  1,      text = _("Crowd Cheers"), options = sortOptionsByKey({0: _("Off (Disabled)"), 1: _("During SP Only"), 2: _("During SP & Green"), 3: _("Always On")}), tipText = _("Sets when the crowd will cheer for you (if a crowd.ogg is present). 'During SP' will have them sing along in star power, and 'During SP & Green' will have them cheering both in SP and when your rock meter is above 2/3")) #akedrou
Config.define("audio",  "miss_volume",         float, 0.2,    text = _("Miss Volume"), options = dict([(n / 100.0, "%02d/10" % (n / 10)) for n in range(0, 110, 10)]), tipText = _("Set the volume of the active track when you miss a note."))  #MFH
Config.define("audio",  "single_track_miss_volume",         float, 0.9,    text = _("Single Track Miss"), options = dict([(n / 100.0, "%02d/10" % (n / 10)) for n in range(0, 110, 10)]), tipText = _("When playing a song with only a single track, this sets the volume of the track when you miss a note."))  #MFH
Config.define("audio",  "menu_volume",         float, 0.6,    text = _("Menu Volume"), options = dict([(n / 100.0, "%02d/10" % (n / 10)) for n in range(0, 110, 10)]), tipText = _("Set the volume of the background menu music.")) #akedrou

Config.define("audio",  "crowd_volume",       float, 0.8,    text = _("Crowd Volume"), options = dict([(n / 100.0, "%02d/10" % (n / 10)) for n in range(0, 110, 10)]), tipText = _("Set the volume of the crowd.")) #akedrou

Config.define("audio",  "kill_volume",         float, 0.0,    text = _("Kill Volume"), options = dict([(n / 100.0, "%02d/10" % (n / 10)) for n in range(0, 110, 10)]), tipText = _("Sets the volume when using the killswitch."))  #MFH
Config.define("audio",  "SFX_volume",         float, 0.7,    text = _("SFX Volume"), options = dict([(n / 100.0, "%02d/10" % (n / 10)) for n in range(0, 110, 10)]), tipText = _("Sets the volume of various sound effects."))  #MFH

#stump: allow metadata caching to be turned off
Config.define("performance", "cache_song_metadata", bool, True, text=_("Cache Song Metadata"), options={False: _("No"), True: _("Yes")}, tipText = _("This will allow information about the songs to be stored for quick access later at the cost of a slow first time loading."))


##Alarian: Get unlimited themes by foldername
themepath = os.path.join(Version.dataPath(), "themes")
themes = []
defaultTheme = None           #myfingershurt
allthemes = os.listdir(themepath)
for name in allthemes:
  if os.path.exists(os.path.join(themepath,name,"notes","notes.png")):
    themes.append(name)
    if name == "MegaLight V4":
      defaultTheme = name

i = len(themes)
if i == 0:
  if os.name == 'posix':
    Log.error("No valid theme found!\n"+\
              "Make sure theme files are properly cased "+\
              "e.g. notes.png works, Notes.png doesn't\n")
  else:
    Log.error("No valid theme found!")
  sys.exit(1);
  
if defaultTheme is None:
  defaultTheme = themes[0]    #myfingershurt

#myfingershurt: default theme must be an existing one!
Config.define("coffee", "themename",           str,   defaultTheme,      text = _("Theme"),                options = dict([(str(themes[n]),themes[n]) for n in range(0, i)]), tipText = _("Sets the overall graphical feel of the game. You can find and download many more at fretsonfire.net"))

##Alarian: End Get unlimited themes by foldername
Player.loadControls()

Config.define("coffee", "neckSpeed",            int,  100,      text = _("Board Speed Percent"),        options = dict([(n, n) for n in range(10, 410, 10)]), tipText = _("Sets how quickly note will scroll"))
Config.define("coffee", "failingEnabled",       bool, True,     text = _("No Fail"),             options = {True: _("Off"), False: _("On")}, tipText = _("Sets whether or not you can fail out of a song."))

# evilynux - configurable default highscores difficulty display.
# Index assigned following same standard as command line argument.
Config.define("game", "songlist_difficulty", int, 0, text = _("Difficulty (Setlist Score)"), options = difficulties, tipText = _("Sets the default difficulty displayed in the setlist score."))

Config.define("game", "songlist_instrument", int, 0, text = _("Instrument (Setlist Score)"), options = parts, tipText = _("Sets the default part displayed in the setlist score."))  #MFH


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

class GameEngine(object):
  """The main game engine."""
  def __init__(self, config = None):

    Log.debug("GameEngine class init (GameEngine.py)...")
    self.mainMenu = None    #placeholder for main menu object - to prevent reinstantiation
    
    self.createdGuitarScene = False   #MFH - so we only create ONE guitarscene...!
    self.currentScene = None
    
    self.versionString = version  #stump: other version stuff moved to allow full version string to be retrieved without instantiating GameEngine
    self.uploadVersion = "%s-4.0" % Version.PROGRAM_NAME #akedrou - the version passed to the upload site.

    self.dataPath = Version.dataPath()
    Log.debug(self.versionString + " starting up...")
    Log.debug("Python version: " + sys.version.split(' ')[0])
    Log.debug("Pygame version: " + str(pygame.version.ver) )
    Log.debug("PyOpenGL version: " + OpenGLVersion)
    Log.debug("Numpy version: " + np.__version__)
    Log.debug("PIL version: " + Image.VERSION)
    Log.debug("sys.argv: " + repr(sys.argv))
    Log.debug("os.name: " + os.name)
    Log.debug("sys.platform: " + sys.platform)
    if os.name == 'nt':
      import win32api
      Log.debug("win32api.GetVersionEx(1): " + repr(win32api.GetVersionEx(1)))
    elif os.name == 'posix':
      Log.debug("os.uname(): " + repr(os.uname()))

    """
    Constructor.
    @param config:  L{Config} instance for settings
    """

    self.tutorialFolder = "tutorials"

    if not config:
      config = Config.load()

    self.config  = config

    fps          = self.config.get("video", "fps")

    self.tasks = []
    self.frameTasks = []
    self.fps = fps
    self.currentTask = None
    self.paused = []
    self.running = True
    self.clock = pygame.time.Clock()

    self.title             = self.versionString
    self.restartRequested  = False

    # evilynux - Check if theme icon exists first, then fallback on FoFiX icon.
    themename = self.config.get("coffee", "themename")
    themeicon = os.path.join(Version.dataPath(), "themes", themename, "icon.png")
    fofixicon = os.path.join(Version.dataPath(), "fofix_icon.png")
    icon = None
    if os.path.exists(themeicon):
      icon = themeicon
    elif os.path.exists(fofixicon):
      icon = fofixicon

    self.video             = Video(self.title, icon)
    if self.config.get("video", "disable_screensaver"):
      self.video.disableScreensaver()

    self.audio             = Audio()
    self.frames            = 0
    self.fpsEstimate       = 0
    self.lastTime          = 0
    self.elapsedTime       = 0
    self.priority          = self.config.get("engine", "highpriority")
    self.show_fps          = self.config.get("video", "show_fps")
    self.advSettings       = self.config.get("game", "adv_settings")
    self.restartRequired   = False
    self.quicksetRestart   = False
    self.quicksetPerf      = self.config.get("quickset", "performance")
    self.scrollRate        = self.config.get("game", "scroll_rate")
    self.scrollDelay       = self.config.get("game", "scroll_delay")
    
    Log.debug("Initializing audio.")
    frequency    = self.config.get("audio", "frequency")
    bits         = self.config.get("audio", "bits")
    stereo       = self.config.get("audio", "stereo")
    bufferSize   = self.config.get("audio", "buffersize")
    
    self.frequency = frequency    #MFH - store this for later reference!
    self.bits = bits
    self.stereo = stereo
    self.bufferSize = bufferSize
    
    self.cmdPlay           = 0
    self.cmdMode           = None
    self.cmdDiff           = None
    self.cmdPart           = None
    
    self.gameStarted       = False
    self.world             = None

    #MFH - TODO - Audio speed divisor needs to be changed to audio speed factor, so can support 0.75x (3/4 speed)
    self.audioSpeedFactor = 0
    self.setSpeedFactor(1)   #MFH - handles initialization at full speed    
    
    Log.debug("Initializing video.")
    #myfingershurt: ensuring windowed mode starts up in center of the screen instead of cascading positions:
    os.environ['SDL_VIDEO_WINDOW_POS'] = 'center'

    width, height = [int(s) for s in self.config.get("video", "resolution").split("x")]
    fullscreen    = self.config.get("video", "fullscreen")
    multisamples  = self.config.get("video", "multisamples")
    self.video.setMode((width, height), fullscreen = fullscreen, multisamples = multisamples)
    
    if self.video.default:
      self.config.set("video", "fullscreen", False)
      self.config.set("video", "resolution", "800x600")
    
    if self.config.get("video", "shader_use"):
      shaders.set(os.path.join(Version.dataPath(), "shaders"))

    # Enable the high priority timer if configured
    if self.priority:
      Log.debug("Enabling high priority timer.")
      self.fps = 0 # High priority

    # evilynux - This was generating an error on the first pass (at least under
    #            GNU/Linux) as the Viewport was not set yet.
    try:
      viewport = glGetIntegerv(GL_VIEWPORT)
    except:
      viewport = [0, 0, width, height]
    h = viewport[3] - viewport[1]
    w = viewport[2] - viewport[0]
    geometry = (0, 0, w, h)
    self.svg = SvgContext(geometry)
    glViewport(int(viewport[0]), int(viewport[1]), int(viewport[2]), int(viewport[3]))

    self.startupMessages   = self.video.error
    self.input     = Input()
    self.view      = View(self, geometry)
    self.resizeScreen(w, h)

    self.resource  = Resource(Version.dataPath())
    self.server    = None
    self.sessions  = []
    self.mainloop  = self.loading
    self.menuMusic = False
    
    self.setlistMsg = None

    
    # Load game modifications
    Mod.init(self)
    self.addTask(self.input, synchronized = False)
    
    self.addTask(self.view, synchronized = False)
    
    self.addTask(self.resource, synchronized = False)

    self.data = Data(self.resource, self.svg)

    ##MFH: Animated stage folder selection option
    #<themename>\Stages still contains the backgrounds for when stage rotation is off, and practice.png
    #subfolders under Stages\ will each be treated as a separate animated stage set
    
    self.stageFolders = []
    currentTheme = themename
    
    stagespath = os.path.join(Version.dataPath(), "themes", currentTheme, "backgrounds")
    themepath  = os.path.join(Version.dataPath(), "themes", currentTheme)
    if os.path.exists(stagespath):
      self.stageFolders = []
      allFolders = os.listdir(stagespath)   #this also includes all the stage files - so check to see if there is at least one .png file inside each folder to be sure it's an animated stage folder
      for name in allFolders:
        aniStageFolderListing = []
        thisIsAnAnimatedStageFolder = False
        try:
          aniStageFolderListing = os.listdir(os.path.join(stagespath,name))
        except Exception, e:
          thisIsAnAnimatedStageFolder = False
        for aniFile in aniStageFolderListing:
          if os.path.splitext(aniFile)[1] == ".png" or os.path.splitext(aniFile)[1] ==  ".jpg" or os.path.splitext(aniFile)[1] == ".jpeg":  #we've found at least one .png file here, chances are this is a valid animated stage folder
            thisIsAnAnimatedStageFolder = True
        if thisIsAnAnimatedStageFolder:
          self.stageFolders.append(name)


      i = len(self.stageFolders)
      if i > 0: #only set default to first animated subfolder if one exists - otherwise use Normal!
        defaultAniStage = str(self.stageFolders[0])
      else:
        defaultAniStage = "Normal"
      Log.debug("Default animated stage for " + currentTheme + " theme = " + defaultAniStage)
      aniStageOptions = dict([(str(self.stageFolders[n]),self.stageFolders[n]) for n in range(0, i)])
      aniStageOptions.update({"Normal":_("Slideshow")})
      if i > 1:   #only add Random setting if more than one animated stage exists
        aniStageOptions.update({"Random":_("Random")})
      Config.define("game", "animated_stage_folder", str, defaultAniStage, text = _("Animated Stage"), options = aniStageOptions )
      
      #MFH: here, need to track and check a new ini entry for last theme - so when theme changes we can re-default animated stage to first found
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

    
    
    try:
      fp, pathname, description = imp.find_module("CustomTheme",[themepath])
      theme = imp.load_module("CustomTheme", fp, pathname, description)
      self.theme = theme.CustomTheme(themepath, themename)
    except ImportError:
      self.theme = Theme(themepath, themename)
    
    self.addTask(self.theme)

    
    self.input.addKeyListener(FullScreenSwitcher(self), priority = True)
    self.input.addSystemEventListener(SystemEventHandler(self))

    self.debugLayer         = None
    self.startupLayer       = None
    self.loadingScreenShown = False
    self.graphicMenuShown   = False
    
    # evilynux - Printing on the console with a frozen binary may cause a crash.
    if hasattr(sys, "frozen"):
      self.print_fps_in_console = False
    else:
      self.print_fps_in_console = True

    Log.debug("Ready.")
    

  def setSpeedFactor(self, factor):
    '''
    allows for slowing down streaming audio tracks
    @param factor:
    '''
    if self.audioSpeedFactor != factor:   #MFH - don't re-init to the same divisor.
      try:
        self.audio.close()    #MFH - ensure no audio is playing during the switch!
        self.audio.pre_open(frequency = int(self.frequency*factor), bits = self.bits, stereo = self.stereo, bufferSize = self.bufferSize)
        self.audio.open(frequency = int(self.frequency*factor), bits = self.bits, stereo = self.stereo, bufferSize = self.bufferSize)
        self.audioSpeedFactor = factor
        pygame.init()
        Log.debug("Initializing pygame.mixer & audio system at " + str(self.frequency*factor) + " Hz." )
      except Exception, e:
        Log.error("Failed to initialize or re-initialize pygame.mixer & audio system - crash imminent!")
  
  # evilynux - This stops the crowd cheers if they're still playing (issue 317).
  def quit(self):
    # evilynux - self.audio.close() crashes when we attempt to restart
    if not self.restartRequested:
      self.audio.close()
    Player.savePlayers()
    for t in list(self.tasks + self.frameTasks):
      self.removeTask(t)
    self.running = False

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
  
  def startWorld(self, players, maxplayers = None, gameMode = 0, multiMode = 0, allowGuitar = True, allowDrum = True, allowMic = False, tutorial = False):
    self.world = World(self, players, maxplayers, gameMode, multiMode, allowGuitar, allowDrum, allowMic, tutorial)
  
  def finishGame(self):
    if not self.world:
      Log.notice("GameEngine.finishGame called before World created.")
      return
    self.world.finishGame()
    self.world = None
    self.gameStarted = False
    self.view.pushLayer(self.mainMenu)

  def loadImgDrawing(self, target, name, fileName, textureSize = None):
    """
    Load an SVG drawing synchronously.
    
    @param target:      An object that will own the drawing
    @param name:        The name of the attribute the drawing will be assigned to
    @param fileName:    The name of the file in the data directory
    @param textureSize: Either None or (x, y), in which case the file will
                        be rendered to an x by y texture
    @return:            L{ImgDrawing} instance
    """
    return self.data.loadImgDrawing(target, name, fileName, textureSize)

  #volshebnyi
  def drawStarScore(self, screenwidth, screenheight, xpos, ypos, stars, scale = None, horiz_spacing = 1.2, space = 1.0, hqStar = False, align = 0):
    minScale = 0.02
    w = screenwidth
    h = screenheight
    if not scale:
      scale = minScale
    elif scale < minScale:
      scale = minScale
    if self.data.fcStars and stars == 7:
      star = self.data.starFC
    else:
      star = self.data.starPerfect
    wide = scale * horiz_spacing
    if align == 1: #center - akedrou (simplifying the alignment...)
      xpos  -= (2 * wide)
    elif align == 2: #right
      xpos  -= (4 * wide)
    if stars > 5:
      for j in range(5):

        if self.data.maskStars:
          if self.data.theme == 2:
            self.drawImage(star, scale = (scale,-scale), coord = (w*(xpos+wide*j)*space**4,h*ypos), color = (1, 1, 0, 1), stretched=11)
          else:
            self.drawImage(star, scale = (scale,-scale), coord = (w*(xpos+wide*j)*space**4,h*ypos), color = (0, 1, 0, 1), stretched=11)
        else:
          self.drawImage(star, scale = (scale,-scale), coord = (w*(xpos+wide*j)*space**4,h*ypos), stretched=11)
    else:
      for j in range(5):
        if j < stars:
          if hqStar:
            star = self.data.star4
          else:
            star = self.data.star2
        else:
          if hqStar:
            star = self.data.star3
          else:
            star = self.data.star1
        self.drawImage(star, scale = (scale,-scale), coord = (w*(xpos+wide*j)*space**4,h*ypos), stretched=11)

  def drawImage(self, image, scale = (1.0, -1.0), coord = (0, 0), rot = 0, \
                color = (1,1,1,1), rect = (0,1,0,1), stretched = 0, fit = 0, \
                alignment = 1, valignment = 1):
    """
    Draws the image/surface to screen

    @param image:        The openGL surface
    @param scale:        Scale factor (between 0.0 and 1.0, second value must be negative due to texture flipping)
    @param coord:        Where the image will be translated to on the screen
    @param rot:          How many degrees it will be rotated
    @param color:        The color of the image
                             (values are between 0.0 and 1.0)
                             (can have 3 values or 4, if 3 are given the alpha is automatically set to 1.0)
    @param rect:         The surface rectangle, this is used for cropping the texture
    @param stretched:    Stretches the image in one of 5 ways according to following passed values
                             1) fits it to the width of the viewport
                             2) fits it to the height of the viewport
                            11) fits it to the width of the viewport and scales the height while keeping the aspect ratio
                            12) fits it to the heigh of the viewport and scales the width while keeping the aspect ratio
                             0) stretches it so it fits the whole viewport
                         Any other values will have the image maintain its size passed by scale
    @param fit:          Adjusts the texture so the coordinate for the y-axis placement can be
                         on the top side (1), bottom side (2), or center point (any other value) of the image
    @param alignment:    Adjusts the texture so the coordinate for x-axis placement can either be
                         on the left side (0), center point (1), or right(2) side of the image 
    @param valignment:   Adjusts the texture so the coordinate for y-axis placement can either be
                         on the bottom side (0), center point (1), or top(2) side of the image
    """
    
    width, height = scale
    x, y = coord
    if stretched == 1: # fit to width
      width  = width  / image.pixelSize[0] * self.view.geometry[2]
    elif stretched == 2: # fit to height
      height = height / image.pixelSize[1] * self.view.geometry[3]
    elif stretched == 11: # fit to width and keep ratio
      width  = width  / image.pixelSize[0] * self.view.geometry[2]
      height = height / image.pixelSize[0] * self.view.geometry[2]
    elif stretched == 12: # fit to height and keep ratio
      width  = width  / image.pixelSize[1] * self.view.geometry[3]
      height = height / image.pixelSize[1] * self.view.geometry[3]
    elif not stretched == 0: # fit to screen
      width  = width  / image.pixelSize[0] * self.view.geometry[2]
      height = height / image.pixelSize[1] * self.view.geometry[3]

    if fit == 1: #y is on top (not center)
      y = y - ((image.pixelSize[1] * abs(scale[1]))*.5*(self.view.geometry[3]/480.0))
    elif fit == 2: #y is on bottom
      y = y + ((image.pixelSize[1] * abs(scale[1]))*.5*(self.view.geometry[3]/480.0))

    image.setRect(rect)  
    image.setScale(width, height)
    image.setPosition(x, y)
    image.setAlignment(alignment)
    image.setVAlignment(valignment)
    image.setAngle(rot)
    image.setColor(color)
    image.draw()

  #blazingamer
  def draw3Dtex(self, image, vertex, texcoord, coord = None, scale = None, rot = None, color = (1,1,1), multiples = False, alpha = False, depth = False, vertscale = 0):
    '''
    Simplifies tex rendering
    
    @param image: self.xxx - tells the system which image/resource should be mapped to the plane
    @param vertex: (Left, Top, Right, Bottom) - sets the points that define where the plane will be drawn
    @param texcoord: (Left, Top, Right, Bottom) - sets where the texture should be drawn on the plane
    @param coord: (x,y,z) - where on the screen the plane will be rendered within the 3d field
    @param scale: (x,y,z) - scales an glplane how far in each direction

    @param rot: (degrees, x-axis, y-axis, z-axis)
    a digit in the axis is how many times you want to rotate degrees around that axis
    
    @param color: (r,g,b) - sets the color of the image when rendered 
    0 = No Color, 1 = Full color

    @param multiples: True/False
    defines whether or not there should be multiples of the plane drawn at the same time
    only really used with the rendering of the notes, keys, and flames

    @param alpha: True/False - defines whether or not the image should have black turned into transparent
    only really used with hitglows and flames
    
    @param depth: True/False - sets the depth by which the object is rendered
    only really used by keys and notes
    
    @param vertscale: # - changes the yscale when setting vertex points
    only really used by notes
    '''

    if alpha == True:
      glBlendFunc(GL_SRC_ALPHA, GL_ONE)

    if len(color) == 4:
      col_array  = np.array([[color[0],color[1],color[2], color[3]],
                         [color[0],color[1],color[2], color[3]],
                         [color[0],color[1],color[2], color[3]],
                         [color[0],color[1],color[2], color[3]]], dtype=np.float32)
    else:
      col_array  = np.array([[color[0],color[1],color[2], 1],
                         [color[0],color[1],color[2], 1],
                         [color[0],color[1],color[2], 1],
                         [color[0],color[1],color[2], 1]], dtype=np.float32)
    
    glEnable(GL_TEXTURE_2D)  
    image.texture.bind()
    
    if multiples == True:
      glPushMatrix()
      
    if coord != None:
      glTranslate(coord[0], coord[1], coord[2])
    if rot != None:
      glRotate(rot[0], rot[1], rot[2], rot[3])
    if scale != None:
      glScalef(scale[0], scale[1], scale[2])

    if depth == True:
      glDepthMask(1)

    triangVtx = np.array(
        [[ vertex[0],  vertscale, vertex[1]],
         [ vertex[2],  vertscale, vertex[1]],
         [ vertex[0], -vertscale, vertex[3]],
         [ vertex[2], -vertscale, vertex[3]]], dtype=np.float32)

    textriangVtx = np.array(
        [[texcoord[0], texcoord[1]],
         [texcoord[2], texcoord[1]],
         [texcoord[0], texcoord[3]],
         [texcoord[2], texcoord[3]]], dtype=np.float32)

    cmgl.drawArrays(GL_TRIANGLE_STRIP, vertices=triangVtx, colors=col_array, texcoords=textriangVtx)
    
    if depth == True:
      glDepthMask(0)
      
    if multiples == True:
      glPopMatrix()

    glDisable(GL_TEXTURE_2D)
    
    if alpha == True:
      glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)                   
  #glorandwarf: renamed to retrieve the path of the file
  def fileExists(self, fileName):
    return self.data.fileExists(fileName)
  
  def getPath(self, fileName):
    return self.data.getPath(fileName)

  def loading(self):
    """Loading state loop."""
    done = self.doRun()
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
    self.svg.clear(*self.theme.backgroundColor)

  def addTask(self, task, synchronized = True):
    """
    Add a task to the engine.

    @param task:          L{Task} to add
    @type  synchronized:  bool
    @param synchronized:  If True, the task will be run with small
                          timesteps tied to the engine clock.
                          Otherwise the task will be run once per frame.
    """
    if synchronized:
      queue = self.tasks
    else:
      queue = self.frameTasks

    if not task in queue:
      queue.append(task)
      task.started()

  def removeTask(self, task):
    """
    Remove a task from the engine.

    @param task:    L{Task} to remove
    """
    found = False
    queues = self._getTaskQueues(task)
    for q in queues:
      q.remove(task)
    if queues:
      task.stopped()

  def _getTaskQueues(self, task):
    queues = []
    for queue in [self.tasks, self.frameTasks]:
      if task in queue:
        queues.append(queue)
    return queues

  def pauseTask(self, task):
    """
    Pause a task.

    @param task:  L{Task} to pause
    """
    self.paused.append(task)

  def resumeTask(self, task):
    """
    Resume a paused task.

    @param task:  L{Task} to resume
    """
    self.paused.remove(task)

  def enableGarbageCollection(self, enabled):
    """
    Enable or disable garbage collection whenever a random garbage
    collection run would be undesirable. Disabling the garbage collector
    has the unfortunate side-effect that your memory usage will skyrocket.
    """
    if enabled:
      gc.enable()
    else:
      gc.disable()

  def collectGarbage(self):
    """
    Run a garbage collection run.
    """
    gc.collect()

  def _runTask(self, task, ticks = 0):
    if not task in self.paused:
      self.currentTask = task
      task.run(ticks)
      self.currentTask = None

  def main(self):
    """Main state loop."""
    done = self.doRun()
    self.clearScreen()
    self.view.render()
    if self.debugLayer:
      self.debugLayer.render(1.0, True)
    self.video.flip()
    # evilynux - Estimate the rendered frames per second.
    if self.show_fps:
      self.frames = self.frames+1
      # Estimate every 120 frames when highpriority is True.
      # Estimate every 2*config.fps when highpriority is False,
      # if you are on target, that should be every 2 seconds.
      if( not self.priority and self.frames == (self.fps << 1) ) or ( self.priority and self.frames == 120 ):
        currentTime = pygame.time.get_ticks()
        self.elapsedTime = currentTime-self.lastTime
        self.lastTime = currentTime
        self.fpsEstimate = self.frames*(1000.0/self.elapsedTime)
        if self.print_fps_in_console == True:
          print("%.2f fps" % self.fpsEstimate)
        self.frames = 0 
    return done

  def doRun(self):
    """Run one cycle of the task scheduler engine."""
    if not self.frameTasks and not self.tasks:
      return False

    for task in self.frameTasks:
      self._runTask(task)
    tick = self.clock.get_time()
    for task in self.tasks:
      self._runTask(task, tick)
    self.clock.tick(self.fps)
    return True

  def run(self):
    return self.mainloop()
