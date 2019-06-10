#####################################################################
# Frets on Fire X (FoFiX)                                           #
# Copyright (C) 2012 FoFiX Team                                     #
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

from fofix.game.song import difficulties, parts
from fofix.core.Language import _
from fofix.core import Config

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

# define configuration keys
Config.define("engine", "highpriority", bool,  False, text = _("FPS Limiter"),           options = {False: _("On (Set Below)"), True: _("Off (Auto Max FPS)")}, tipText = _("Use this to enable or disable the FPS Limiter. If off, the game will render as many frames as possible. (This is affected by the 'Performance' quickset)"))
Config.define("game",   "adv_settings", bool,  False)
Config.define("video",  "fullscreen",   bool,  False,  text = _("Fullscreen Mode"),      options = {False: _("No"), True: _("Yes")}, tipText = _("Play either in fullscreen ('Yes') or windowed ('No') mode."))
Config.define("video",  "multisamples", int,   4,     text = _("Antialiasing Quality"), options = {0: _("None"), 2: "2x", 4: "4x", 6: "6x", 8: "8x"}, tipText = _("Sets the antialiasing quality of openGL rendering. Higher values reduce jaggediness, but could affect performance. (This is affected by the 'Performance' quickset)"))
Config.define("video",  "disable_fretsfx", bool, False, text = _("Show Fret Glow Effect"), options = {False: _("Yes"), True: _("No")}, tipText = _("Turn on or off the glow that appears around a fret when you press it."))
Config.define("video",  "disable_flamesfx", bool, False, text = _("Show Fret Flame Effect"), options = {False: _("Yes"), True: _("No")}, tipText = _("Turn on or off the flame that appears around a fret when you press it."))
Config.define("video",  "resolution",   str,   "640x480")
Config.define("video",  "fps",          int,   60,    text = _("Frames per Second"), options = dict([(n, n) for n in range(1, 121)]), tipText = _("Set the number of frames to render per second. Higher values are better, but your computer may not be able to keep up. You probably can leave this alone. (This is affected by the 'Performance' quickset)"))
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

Config.define("performance",  "animated_notes", bool,     True,  text = _("Animated Notes"), options = {True: _("Yes"), False: _("No")}, tipText = _("This will animate notes as they come towards you, if that is included in your theme. This can have a hit on performance. (This is affected by the 'Performance' quickset)"))
Config.define("audio",  "frequency",    int,   44100, text = _("Sample Frequency"), options = [8000, 11025, 22050, 32000, 44100, 48000], tipText = _("Set the sample frequency for the audio in the game. You almost certainly want to leave this at 44100 Hz unless you really know what you're doing."))
Config.define("audio",  "bits",         int,   16,    text = _("Sample Bits"), options = [16, 8], tipText = _("Set the sample bits for the audio in the game. You almost certainly want to leave this at 16-bit unless you really know what you're doing."))
Config.define("audio",  "stereo",       bool,  True)

Config.define("network",   "uploadscores", bool,  False, text = _("Upload Highscores"),    options = {False: _("No"), True: _("Yes")}, tipText = _("If enabled, your high scores will be sent to the server to rank you against other players."))
Config.define("network",   "uploadurl",    str,   "http://www.wembley1967.com/chart/uploadsp.php") # evilynux - new one starting 20080902

Config.define("setlist", "base_library",      str, "")
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
Config.define("game",   "notedisappear",      int,   1,  text = _("Missed Notes"), options = {0: _("Disappear"), 1: _("Keep on going"), 2: _("Turn Red")}, tipText = _("When you miss a note, this sets whether they disappear from the fretboard, scroll off the bottom of the screen or turn red"))

#akedrou - Quickset (based on Fablaculp's Performance Autoset)
Config.define("quickset", "performance", int, 0, text = _("Performance"), options = sortOptionsByKey({0: _("Manual"), 1: _("Pure Speed"), 2: _("Fast"), 3: _("Quality (Recommended)"), 4: _("Max Quality (Slow)")}), tipText = _("Set the performance of your game. You can fine-tune in the advanced menus."))
Config.define("quickset", "gameplay",    int, 0, text = _("Gameplay"),    options = sortOptionsByKey({0: _("Manual"), 1: _("Theme-Based"), 2: _("MIDI Based"), 3: _("RB Style"), 4: _("GH Style"), 5: _("WT Style")}), tipText = _("Sets how the game 'feels' to play. Theme-Based lets the theme creator decide. MIDI Based lets the fretter decide."))
Config.define("game", "lost_focus_pause", bool, True, text = _("Pause on Loss of Focus"), options = {False: _("Off"), True: _("On")}, tipText = _("Set whether the game automatically pauses when another application steals input focus."))

#myfingershurt: HOPO settings
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

Config.define("game", "decimal_places",      int, 1,  text = _("Stat Decimal Places"), options = dict([(n, n) for n in range(0, 3)]), tipText = _("Determines how many decimal places will be noted in displaying stats."))

Config.define("game",   "ignore_open_strums",          bool, True,  text = _("Ignore Open Strums"), options = {False: _("No"), True: _("Yes")}, tipText = _("If enabled, strumming without holding any frets down won't be counted."))
Config.define("performance",   "static_strings",          bool, True,  text = _("Static Strings"), options = {False: _("No"), True: _("Yes")}, tipText = _("If enabled, the 'strings' on your fretboard will not scroll."))
Config.define("game",   "whammy_saves_starpower",          bool, False,  text = _("Effects Save SP"), options = {False: _("No"), True: _("Yes")}, tipText = _("If enabled, whammying while in SP will slow down its decrease. And your score will be handicapped by 5%."))
Config.define("game",   "hopo_indicator",          bool, False,  text = _("Show HO/PO Indicator"), options = {False: _("No"), True: _("Yes")}, tipText = _("If enabled, 'HOPO' will appear in game. When there are HOPO notes active, it will turn white."))
Config.define("game",   "quickplay_tiers",          int, 1,  text = _("Use Tiers in Quickplay"), options = {0: _("Off"), 1: _("Normal"), 2: _("Sorting")}, tipText = _("Sets whether to mark tiers in quickplay mode. 'Normal' will use the career tiers and 'Sorting' will insert tiers based on the current sort order."))
Config.define("performance",   "star_score_updates",          int, 1,  text = _("Star Updates"), options = {0: _("On Hit"), 1: _("Score Change")}, tipText = _("If set to 'On Hit', your star score will only be checked when you hit a note. If set to 'Score Change', your star score will constantly update. (This is affected by the 'Performance' quickset)"))
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
Config.define("game", "hopo_debug_disp",      int, 0,  text = _("HO/PO Debug"), options = {0: _("Off"), 1: _("On")}, tipText = _("If enabled, various log messages will be recorded regarding the HO/PO system. Please leave this disabled if submitting logs for bug reports unless you are certain it is necessary."))
Config.define("game", "gsolo_accuracy_disp",      int, 1,  text = _("Show Solo Stats"), options = {0: _("Off"), 1: _("Percent"), 2: _("Detail")}, tipText = _("Sets whether to show your solo results when you finish a solo. 'Percent' will only show the percentage, while 'Detail' includes additional information."))
Config.define("game", "star_scoring",       int, 3,     text = _("Star Scoring Style"), options = sortOptionsByKey({0: _("Accuracy"), 1: _("GH"), 2: _("RB"), 3: _("RB+GH"), 4: _("RB2")}), tipText = _("Sets which system to use to calculate your star score."))#MFH
Config.define("game", "career_star_min",    int, 3,     text = _("Career Mode Advance"), options = {0: _("0 (Song Finish)"), 1: _("1 Star"), 2: _("2 Stars"), 3: _("3 Stars"), 4: _("4 Stars"), 5: _("5 Stars"), 6: _("6 (Gold Stars)"), 7: _("7 (Full Combo)")}, tipText = _("Determine how many stars are needed on a song before it is unlocked in career mode."))
Config.define("game", "gsolo_accuracy_pos",       int, 3,     text = _("Solo Stat Positioning"), options = sortOptionsByKey({0: _("Right"), 1: _("Center"), 2: _("Left"), 3: _("Rock Band")}), tipText = _("Sets where your solo result stats will be displayed."))#MFH,(racer: added RB)
Config.define("game", "bass_groove_enable",       int, 1,     text = _("Bass Groove"), options = {0: _("Off"), 1: _("By Theme"), 2: _("By MIDI"), 3: _("On")}, tipText = _("Enable or disable bass groove (additional score multiplier for bass)")) #MFH
Config.define("game", "T_sound",      int, 2,  text = _("Drum Miss Penalty"), options = {0: _("Always"), 1: _("Song Start"), 2: _("First Note")}, tipText = _("Determines when drum hits count as misses: When the song begins, after the first note, or always.")) #Faaa Drum sound
Config.define("game", "gfx_version_tag",       int, 1,     text = _("Show Theme Version Tag"), options = {0: _("No"), 1: _("Yes")}, tipText = _("Places the theme's version tag over menus and dialogs.")) #MFH
Config.define("game", "p2_menu_nav",       int, 1,     text = _("Menu Navigation"), options = {0: _("P1 Only"), 1: _("All Players")}, tipText = _("Sets whether all players can navigate the menu, or only the controller set as Player 1 and the master keys.")) #MFH
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

Config.define("debug",   "show_raw_vocal_data", int, 0,  text = _("Show Raw Vocal Data"), options = {0: _("Off"), 1: _("On")}, tipText = _("If enabled, various information about the microphone input will be show in text on screen. Probably only needed for vocal debugging."))

Config.define("audio",  "speed_factor",  float,    1.0,  text = _("Speed Factor"),   options = sortOptionsByKey({1.0: _("1.00x"), 0.75: _("0.75x"), 0.50: _("0.50x"), 0.25: _("0.25x")}), tipText = _("Sets the speed to play the audio at. Your score will be severely penalized if you slow the music down."))  #MFH

Config.define("audio",  "whammy_effect",  int,    0,  text = _("Effects Mode"),   options = {0: _("Killswitch"), 1: _("Pitchbend")}, tipText = _("Sets whether to use a killswitch or pitchbend as the effect on your whammy."))  #MFH


#MFH - log settings
Config.define("game",   "log_class_inits",          int, 0,    text = _("Log Class Inits"), options = {0: _("No"), 1: _("Yes")}, tipText = _("Logs most class initializations in '__init__'. This is unnecessary information in bug reports; please leave it disabled unless you are certain it is relevant."))
Config.define("game",   "log_loadings",          int, 0,    text = _("Log Loadings"), options = {0: _("No"), 1: _("Yes")}, tipText = _("Logs resource loads. This is unnecessary information in bug reports; please leave it disabled unless you are certain it is relevant."))
Config.define("game",   "log_sections",          int, 0,    text = _("Log MIDI Sections"), options = {0: _("No"), 1: _("Yes")}, tipText = _("Logs MIDI sections. This is unnecessary information in bug reports; please leave it disabled unless you are certain it is relevant."))
Config.define("game",   "log_marker_notes",          int, 0,    text = _("Log Marker Notes"), options = {0: _("No"), 1: _("Yes")}, tipText = _("Logs MIDI marker notes (solo, SP, etc). This is unnecessary information in bug reports; please leave it disabled unless you are certain it is relevant."))
Config.define("log",   "log_unedited_midis",          int, 0,    text = _("Log Unedited MIDIs"), options = {0: _("No"), 1: _("Yes")}, tipText = _("Logs when notes-unedited.mid is used. This is unnecessary information."))
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
Config.define("performance",   "disable_libcount",    bool,  True,  text = _("Show Setlist Size"),    options = {False: _("Yes"), True: _("No")}, tipText = _("Show the number of songs inside of each setlist."))

Config.define("game",   "jurg_p0",             bool, False,   text = _("P1 AI"), options = {True: _("On"), False: _("Off")}, tipText = _("Enable or disable the player 1 AI"))
Config.define("game",   "jurg_skill_p0",        int, 5,   text = _("P1 AI Personality"), options = {0: _("1. KiD"), 1: _("2. Stump"), 2: _("3. akedRobot"), 3: _("4. Q"), 4: _("5. MFH"), 5: _("6. Jurgen")}, tipText = _("Set the personality of the player 1 AI. The numbers correspond with their skill."))

Config.define("game",   "jurg_p1",             bool, False,   text = _("P2 AI"), options = {True: _("On"), False: _("Off")}, tipText = _("Enable or disable the player 2 AI"))
Config.define("game",   "jurg_skill_p1",        int, 5,   text = _("P2 AI Personality"), options = {0: _("1. KiD"), 1: _("2. Stump"), 2: _("3. akedRobot"), 3: _("4. Q"), 4: _("5. MFH"), 5: _("6. Jurgen")}, tipText = _("Set the personality of the player 2 AI. The numbers correspond with their skill."))

Config.define("game",   "jurg_p2",             bool, False,   text = _("P3 AI"), options = {True: _("On"), False: _("Off")}, tipText = _("Enable or disable the player 3 AI"))
Config.define("game",   "jurg_skill_p2",        int, 5,   text = _("P3 AI Personality"), options = {0: _("1. KiD"), 1: _("2. Stump"), 2: _("3. akedRobot"), 3: _("4. Q"), 4: _("5. MFH"), 5: _("6. Jurgen")}, tipText = _("Set the personality of the player 3 AI. The numbers correspond with their skill."))

Config.define("game",   "jurg_p3",             bool, False,   text = _("P4 AI"), options = {True: _("On"), False: _("Off")}, tipText = _("Enable or disable the player 4 AI"))
Config.define("game",   "jurg_skill_p3",        int, 5,   text = _("P4 AI Personality"), options = {0: _("1. KiD"), 1: _("2. Stump"), 2: _("3. akedRobot"), 3: _("4. Q"), 4: _("5. MFH"), 5: _("6. Jurgen")}, tipText = _("Set the personality of the player 4 AI. The numbers correspond with their skill."))

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

Config.define("coffee", "neckSpeed",            int,  100,      text = _("Board Speed Percent"),        options = dict([(n, n) for n in range(10, 410, 10)]), tipText = _("Sets how quickly note will scroll"))
Config.define("coffee", "failingEnabled",       bool, True,     text = _("No Fail"),             options = {True: _("Off"), False: _("On")}, tipText = _("Sets whether or not you can fail out of a song."))

# evilynux - configurable default highscores difficulty display.
# Index assigned following same standard as command line argument.
Config.define("game", "songlist_difficulty", int, 0, text = _("Difficulty (Setlist Score)"), options = difficulties, tipText = _("Sets the default difficulty displayed in the setlist score."))

Config.define("game", "songlist_instrument", int, 0, text = _("Instrument (Setlist Score)"), options = parts, tipText = _("Sets the default part displayed in the setlist score."))  #MFH
