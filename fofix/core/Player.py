#####################################################################
# -*- coding: utf-8 -*-                                             #
#                                                                   #
# Frets on Fire                                                     #
# Copyright (C) 2006 Sami Kyöstilä                                  #
#               2008 Alarian                                        #
#               2008 myfingershurt                                  #
#               2008 Glorandwarf                                    #
#               2008 QQStarS                                        #
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

import logging

import pygame

from fofix.core.Language import _
from fofix.core import Microphone
from fofix.core import Config
from fofix.game import song
from fofix.core import VFS


log = logging.getLogger(__name__)


class ConfigOption:
    """ Deprecated: also in fofix.core.ConfigDefs """

    def __init__(self, id, text):
        self.id   = id
        self.text = text

    def __str__(self):
        return self.text

    def __repr__(self):
        return self.text

    def __cmp__(self, other):
        try:
            if self.id > other.id:
                return 1
            elif self.id == other.id:
                return 0
            else:
                return -1
        except Exception:
            return -1


def sortOptionsByKey(dict):
    """ Deprecated: also in fofix.core.ConfigDefs """
    a = {}
    for k in dict.keys():
        a[k] = ConfigOption(k, dict[k])
    return a

# Redoing this, sir. Redoing this...
CONTROL1  = [1 << n for n in xrange(20)]
CONTROL2  = [1 << n for n in xrange(20, 40)]
CONTROL3  = [1 << n for n in xrange(40, 60)]
CONTROL4  = [1 << n for n in xrange(60, 80)]
CONTROLS  = [CONTROL1, CONTROL2, CONTROL3, CONTROL4]
LEFT      = 0
RIGHT     = 1
UP        = 2
DOWN      = 3
START     = 4
CANCEL    = 5
KEY1      = 6
KEY1A     = 7
KEY2      = 8
KEY2A     = 9
KEY3      = 10
KEY3A     = 11
KEY4      = 12
KEY4A     = 13
KEY5      = 14
KEY5A     = 15
ACTION1   = 16
ACTION2   = 17
STAR      = 18
KILL      = 19

# note that the drum controls map to guitar controls. Controller type is important!
DRUM1     = 8
DRUM1A    = 9
DRUM2     = 10
DRUM2A    = 11
DRUM3     = 12
DRUM3A    = 13
DRUM4     = 14
DRUM4A    = 15
DRUM5     = 6
DRUM5A    = 7
DRUMBASS  = 16
DRUMBASSA = 17

GUITARTYPES = [-1, 0, 1, 4]
DRUMTYPES   = [-1, 2, 3]
MICTYPES    = [5]

lefts    = [CONTROL1[LEFT], CONTROL2[LEFT], CONTROL3[LEFT], CONTROL4[LEFT]]
rights   = [CONTROL1[RIGHT], CONTROL2[RIGHT], CONTROL3[RIGHT], CONTROL4[RIGHT]]
ups      = [CONTROL1[UP], CONTROL2[UP], CONTROL3[UP], CONTROL4[UP]]
downs    = [CONTROL1[DOWN], CONTROL2[DOWN], CONTROL3[DOWN], CONTROL4[DOWN]]
starts   = [CONTROL1[START], CONTROL2[START], CONTROL3[START], CONTROL4[START]]
cancels  = [CONTROL1[CANCEL], CONTROL2[CANCEL], CONTROL3[CANCEL], CONTROL4[CANCEL]]
stars    = [CONTROL1[STAR], CONTROL2[STAR], CONTROL3[STAR], CONTROL4[STAR]] # XXX: don't know if this is needed but...

key1s    = []
key2s    = []
key3s    = []
key4s    = []
key5s    = []
keysolos = []
action1s = []
action2s = []
kills    = [] # XXX: don't know if this is needed but...

drum1s    = []
drum2s    = []
drum3s    = []
drum4s    = []
drum5s    = []
bassdrums = []

guitarkeynames = ["Left", "Right", "Up", "Down", "Cancel", "Select", "Fret 1", "Solo Fret 1", "Fret 2", "Solo Fret 2", "Fret 3",
                  "Solo Fret 3", "Fret 4", "Solo Fret 4", "Fret 5", "Solo Fret 5", "Action 1", "Action 2", "Star Key", "Effects Key"]
drumkey4names  = ["Left", "Right", "Up", "Down", "Cancel", "Select", "Drum 4", "Drum 4 B", "Drum 1", "Drum 1 B", "Drum 2", "Drum 2 B",
                  "Drum 3", "Drum 3 B", "None", "None", "Bass Drum", "Bass Drum B", "Star Key", "None"]
drumkey5names  = ["Left", "Right", "Up", "Down", "Cancel", "Select", "Drum 5", "Drum 5 B", "Drum 1", "Drum 1 B", "Cymbal 2", "Cymbal 2 B",
                  "Drum 3", "Drum 3 B", "Cymbal 4", "Cymbal 4 B", "Bass Drum", "Bass Drum B", "Star Key", "None"]

menuUp   = []
menuDown = []
menuPrev = []
menuNext = []
menuYes  = []
menuNo   = []

CONTROLLER1KEYS = [CONTROL1[KEY1], CONTROL1[KEY2], CONTROL1[KEY3], CONTROL1[KEY4], CONTROL1[KEY5], CONTROL1[KEY1A], CONTROL1[KEY2A], CONTROL1[KEY3A], CONTROL1[KEY4A], CONTROL1[KEY5A]]
CONTROLLER2KEYS = [CONTROL2[KEY1], CONTROL2[KEY2], CONTROL2[KEY3], CONTROL2[KEY4], CONTROL2[KEY5], CONTROL2[KEY1A], CONTROL2[KEY2A], CONTROL2[KEY3A], CONTROL2[KEY4A], CONTROL2[KEY5A]]
CONTROLLER3KEYS = [CONTROL3[KEY1], CONTROL3[KEY2], CONTROL3[KEY3], CONTROL3[KEY4], CONTROL3[KEY5], CONTROL3[KEY1A], CONTROL3[KEY2A], CONTROL3[KEY3A], CONTROL3[KEY4A], CONTROL3[KEY5A]]
CONTROLLER4KEYS = [CONTROL4[KEY1], CONTROL4[KEY2], CONTROL4[KEY3], CONTROL4[KEY4], CONTROL4[KEY5], CONTROL4[KEY1A], CONTROL4[KEY2A], CONTROL4[KEY3A], CONTROL4[KEY4A], CONTROL4[KEY5A]]
CONTROLLER1ACTIONS = [CONTROL1[ACTION1], CONTROL1[ACTION2]]
CONTROLLER2ACTIONS = [CONTROL2[ACTION1], CONTROL2[ACTION2]]
CONTROLLER3ACTIONS = [CONTROL3[ACTION1], CONTROL3[ACTION2]]
CONTROLLER4ACTIONS = [CONTROL4[ACTION1], CONTROL4[ACTION2]]
CONTROLLER1DRUMS = [CONTROL1[DRUM1], CONTROL1[DRUM1A], CONTROL1[DRUM2], CONTROL1[DRUM2A], CONTROL1[DRUM3], CONTROL1[DRUM3A], CONTROL1[DRUM4], CONTROL1[DRUM4A], CONTROL1[DRUM5], CONTROL1[DRUM5A], CONTROL1[DRUMBASS], CONTROL1[DRUMBASSA]]
CONTROLLER2DRUMS = [CONTROL2[DRUM1], CONTROL2[DRUM1A], CONTROL2[DRUM2], CONTROL2[DRUM2A], CONTROL2[DRUM3], CONTROL2[DRUM3A], CONTROL2[DRUM4], CONTROL2[DRUM4A], CONTROL2[DRUM5], CONTROL2[DRUM5A], CONTROL2[DRUMBASS], CONTROL2[DRUMBASSA]]
CONTROLLER3DRUMS = [CONTROL3[DRUM1], CONTROL3[DRUM1A], CONTROL3[DRUM2], CONTROL3[DRUM2A], CONTROL3[DRUM3], CONTROL3[DRUM3A], CONTROL3[DRUM4], CONTROL3[DRUM4A], CONTROL3[DRUM5], CONTROL3[DRUM5A], CONTROL3[DRUMBASS], CONTROL3[DRUMBASSA]]
CONTROLLER4DRUMS = [CONTROL4[DRUM1], CONTROL4[DRUM1A], CONTROL4[DRUM2], CONTROL4[DRUM2A], CONTROL4[DRUM3], CONTROL4[DRUM3A], CONTROL4[DRUM4], CONTROL4[DRUM4A], CONTROL4[DRUM5], CONTROL4[DRUM5A], CONTROL4[DRUMBASS], CONTROL4[DRUMBASSA]]

SCORE_MULTIPLIER = [0, 10, 20, 30]
BASS_GROOVE_SCORE_MULTIPLIER = [0, 10, 20, 30, 40, 50]

player0 = []
player1 = []
player2 = []
player3 = []
playerkeys = []

# define configuration keys
Config.define("controller", "name",          str, tipText=_("Name your controller."))
Config.define("controller", "key_left",      str, "K_LEFT",     text=_("Move left"))
Config.define("controller", "key_right",     str, "K_RIGHT",    text=_("Move right"))
Config.define("controller", "key_up",        str, "K_UP",       text=_("Move up"))
Config.define("controller", "key_down",      str, "K_DOWN",     text=_("Move down"))
Config.define("controller", "key_action1",   str, "K_RETURN",   text=(_("Pick"), _("Bass Drum")))
Config.define("controller", "key_action2",   str, "K_RSHIFT",   text=(_("Secondary Pick"), _("Bass Drum 2")))
Config.define("controller", "key_1",         str, "K_F1",       text=(_("Fret #1"), _("Drum #4"), _("Drum #5")))
Config.define("controller", "key_2",         str, "K_F2",       text=(_("Fret #2"), _("Drum #1")))
Config.define("controller", "key_3",         str, "K_F3",       text=(_("Fret #3"), _("Drum #2"), _("Cymbal #2")))
Config.define("controller", "key_4",         str, "K_F4",       text=(_("Fret #4"), _("Drum #3")))
Config.define("controller", "key_5",         str, "K_F5",       text=(_("Fret #5"), None, _("Cymbal #4")))
Config.define("controller", "key_1a",        str, "K_F6",       text=(_("Solo Fret #1"), _("Solo Key"), _("Drum #4"), _("Drum #5"), _("Analog Slider")))
Config.define("controller", "key_2a",        str, "K_F7",       text=(_("Solo Fret #2"), _("Drum #1")))
Config.define("controller", "key_3a",        str, "K_F8",       text=(_("Solo Fret #3"), _("Drum #2"), _("Cymbal #2")))
Config.define("controller", "key_4a",        str, "K_F9",       text=(_("Solo Fret #4"), _("Drum #3")))
Config.define("controller", "key_5a",        str, "K_F10",      text=(_("Solo Fret #5"), None, _("Cymbal #4")))
Config.define("controller", "key_cancel",    str, "K_ESCAPE",   text=_("Cancel"))
Config.define("controller", "key_star",      str, "K_PAGEDOWN", text=_("StarPower"))
Config.define("controller", "key_kill",      str, "K_PAGEUP",   text=_("Whammy"))
Config.define("controller", "key_start",     str, "K_LCTRL",    text=_("Start"))
Config.define("controller", "two_chord_max", int, 0,            text=_("Two-Chord Max"),   options={0: _("Off"), 1: _("On")}, tipText=_("When enabled, the highest notes in large note chords are auto-played."))
Config.define("controller", "type",          int, 0,            text=_("Controller Type"), options=sortOptionsByKey({0: _("Standard Guitar"), 1: _("Solo Shift Guitar"), 2: _("Drum Set (4-Drum)"), 4: _("Analog Slide Guitar"), 5: _("Microphone")}), tipText=_("'Standard Guitar' is for keyboards and pre-WT GH-series guitars. 'Solo Shift Guitar' is for RB-series guitars and keyboards who want to use a shift key for solo frets. 'Analog Slide Guitar' is for guitars with an analog slider bar.")) #, 3: _("Drum Set (3-Drum 2-Cymbal)")
Config.define("controller", "analog_sp",     int, 0,            text=_("Analog SP"),       options={0: _("Disabled"), 1: _("Enabled")}, tipText=_("Enables analog SP (as in the XBOX Xplorer controller.)"))
Config.define("controller", "analog_sp_threshold",   int, 60,   text=_("Analog SP Threshold"), options=dict([(n, n) for n in range(10, 101, 10)]), tipText=_("Sets a threshold level for activating SP in analog mode."))
Config.define("controller", "analog_sp_sensitivity", int, 4,    text=_("Analog SP Sensitivity"), options=dict([(n, n+1) for n in range(10)]), tipText=_("Sets the sensitivity for activating SP in analog mode."))
Config.define("controller", "analog_drum",   int, 0,            text=_("Analog Drums"),    options={0: _("Disabled"), 1: _("PS2/PS3/Wii"), 2: _("XBOX"), 3: _("XBOX Inv.")}, tipText=_("Enables analog drums as in RB2 and GH drumsets.")) #FIXME: Analog Drum
Config.define("controller", "analog_slide",  int, 0,            text=_("Analog Slider"),    options={0: _("Default"), 1: _("Inverted")}, tipText=_("Experimental testing for the analog slide mode."))
Config.define("controller", "analog_kill",   int, 0,            text = _("Analog Effects"),  options={0: _("Disabled"), 1: _("PS2/PS3/Wii"), 2: _("XBOX"), 3: _("XBOX Inv.")}, tipText=_("Enables analog whammy bar. Set to the system your controller was designed for."))
Config.define("controller", "analog_fx",     int, 0,            text=_("Sound FX Switch"), options={0: _("Switch"), 1: _("Cycle")})  #FIXME: Analog FX
Config.define("controller", "mic_device",    int, -1,           text=_("Microphone Device"), options=Microphone.getAvailableMics())
Config.define("controller", "mic_tap_sensitivity", int, 5,      text=_("Tap Sensitivity"), options=dict((n, n) for n in range(1, 21)), tipText=_("Sets how sensitive the microphone is to being tapped."))
Config.define("controller", "mic_passthrough_volume", float, 0.0, text=_("Passthrough Volume"), options=dict((n / 100.0, n) for n in range(101)), tipText=_("Sets how loud you hear yourself singing."))

Config.define("player", "name",          str, "")
Config.define("player", "difficulty",    int, song.MED_DIF)
Config.define("player", "part",          int, song.GUITAR_PART)
Config.define("player", "neck",          str, "")
Config.define("player", "necktype",      str, 2, text=_("Neck Type"),     options={0: _("Default Neck"), 1: _("Theme Neck"), 2: _("Specific Neck")})
Config.define("player", "leftymode",     int, 0, text=_("Lefty Mode"),    options={0: _("Off"), 1: _("On")})
Config.define("player", "drumflip",      int, 0, text=_("Drum Flip"),     options={0: _("Off"), 1: _("On")})
Config.define("player", "two_chord_max", int, 0, text=_("Two-Chord Max"), options={0: _("Off"), 1: _("On")})
Config.define("player", "assist_mode",   int, 0, text=_("Assist Mode"),   options={0: _("Off"), 1: _("Easy Assist"), 2: _("Medium Assist")})
Config.define("player", "auto_kick",     int, 0, text=_("Auto Kick"),     options={0: _("Off"), 1: _("On")})
Config.define("player", "controller",    int, 0)

# Overlay the users folder in /data with one in the user data folder.
VFS.mount(VFS.resolveRead('/data/users'), 'users')
VFS.mountWritable(VFS.resolveWrite('/userdata/users'), 'users')
controlpath = '/users/controllers'
playerpath = '/users/players'


def _makeControllerIniName(name):
    '''Turn a controller name into a virtual path to the appropriate ini.'''
    return '%s/%s.ini' % (controlpath, name)


def _makePlayerIniName(name):
    '''Turn a player name into a virtual path to the appropriate ini.'''
    return '%s/%s.ini' % (playerpath, name)


control0 = None
control1 = None
control2 = None
control3 = None
controlDict = {}
controllerDict = {}
playername = []
playerpref = []
playerstat = []

# Load the player database and check that it is fully initialized.
_SCHEMA_VERSION = 3
_playerDB = VFS.openSqlite3('%s/%s' % (playerpath, 'FoFiX-players.cache'))
_updateTables = 0
try:
    v = _playerDB.execute("SELECT `value` FROM `config` WHERE `key` = 'version'").fetchone()[0]
    if int(v) != _SCHEMA_VERSION:
        _updateTables = 2  # an old version. We don't want to just burn old tables.
except Exception:
    _updateTables = 1  # no good table
# needs to handle old versions eventually.
if _updateTables > 0:
    for tbl in _playerDB.execute("SELECT `name` FROM `sqlite_master` WHERE `type` = 'table'").fetchall():
        _playerDB.execute('DROP TABLE `%s`' % tbl)
    _playerDB.commit()
    _playerDB.execute('VACUUM')
    _playerDB.execute('CREATE TABLE `config` (`key` STRING UNIQUE, `value` STRING)')
    _playerDB.execute('CREATE TABLE `players` (`name` STRING UNIQUE, `lefty` INT, `drumflip` INT, `autokick` INT, `assist` INT, `twochord` INT, `necktype` INT, `neck` STRING, \
                   `part` INT, `difficulty` INT, `upname` STRING, `control` INT, `changed` INT, `loaded` INT)')
    _playerDB.execute('CREATE TABLE `stats` (`song` STRING, `hash` STRING, `player` STRING)')
    _playerDB.execute("INSERT INTO `config` (`key`, `value`) VALUES (?, ?)", ('version', _SCHEMA_VERSION))
    _playerDB.commit()


def resetStats(player=None):
    if player is None:
        _playerDB.execute('UPDATE `stats` SET `hit` = 0, `notes` = 0, `sc1` = 0, `sc2` = 0, `sc3` = 0, `sc4` = 0, `sc5` = 0, `ha1` = 0, `ha2` = 0, `ha3` = 0, `ha4` = 0, `ha5` = 0')
    else:
        _playerDB.execute('UPDATE `stats` SET `hit` = 0, `notes` = 0, `sc1` = 0, `sc2` = 0, `sc3` = 0, `sc4` = 0, `sc5` = 0, `ha1` = 0, `ha2` = 0, `ha3` = 0, `ha4` = 0, `ha5` = 0 WHERE `name` = ?', [player])
    _playerDB.commit()


def loadPlayers():
    global playername, playerpref, playerstat
    playername = []
    playerpref = []
    playerstat = []
    allplayers = VFS.listdir(playerpath)
    for name in allplayers:
        if name == "default.ini":
            continue
        if name.lower().endswith(".ini") and len(name) > 4:
            playername.append(name[0:len(name)-4])
            pref = _playerDB.execute('SELECT * FROM `players` WHERE `name` = ?', [playername[-1]]).fetchone()
            try:
                if len(pref) == 14:
                    playerpref.append((pref[1], pref[2], pref[3], pref[4], pref[5], pref[6], pref[7], pref[8], pref[9], pref[10]))
            except TypeError:
                try:
                    c = Config.load(VFS.resolveRead(_makePlayerIniName(name[:-4])), type=2)
                    lefty   = c.get("player", "leftymode")
                    drumf   = c.get("player", "drumflip")
                    autok   = c.get("player", "auto_kick")
                    assist  = c.get("player", "assist_mode")
                    twoch   = c.get("player", "two_chord_max")
                    neck    = c.get("player", "neck")
                    neckt   = c.get("player", "necktype")
                    part    = c.get("player", "part")
                    diff    = c.get("player", "difficulty")
                    upname  = c.get("player", "name")
                    control = c.get("player", "controller")
                    del c
                    _playerDB.execute('INSERT INTO `players` VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 1)', [playername[-1], lefty, drumf, autok, assist, twoch, neckt, neck, part, diff, upname, control])
                    playerpref.append((lefty, drumf, autok, assist, twoch, neckt, neck, part, diff, upname))
                except IOError:
                    _playerDB.execute('INSERT INTO `players` VALUES (?, 0, 0, 0, 0, 0, 0, ``, 0, 2, ``, 0, 0, 1)', [playername[-1]])
                    playerpref.append((0, 0, 0, 0, 0, 0, '', 0, 2, '', 0))
            _playerDB.execute('UPDATE `players` SET `loaded` = 1 WHERE `name` = ?', [playername[-1]])
            _playerDB.commit()
    return 1


def savePlayers():
    for pref in _playerDB.execute('SELECT * FROM `players` WHERE `changed` = 1').fetchall():
        try:
            c = Config.load(VFS.resolveWrite(_makePlayerIniName(str(pref[0]))), type=2)
            c.set("player", "leftymode", int(pref[1]))
            c.set("player", "drumflip", int(pref[2]))
            c.set("player", "auto_kick", int(pref[3]))
            c.set("player", "assist_mode", int(pref[4]))
            c.set("player", "two_chord_max", int(pref[5]))
            c.set("player", "necktype", int(pref[6]))
            c.set("player", "neck", str(pref[7]))
            c.set("player", "part", int(pref[8]))
            c.set("player", "difficulty", int(pref[9]))
            c.set("player", "name", str(pref[10]))
            c.set("player", "controller", int(pref[11]))
            del c
            _playerDB.execute('UPDATE `players` SET `changed` = 0 WHERE `name` = ?', [pref[0]])
        except Exception:
            c = VFS.open(_makePlayerIniName(str(pref[0])), "w")
            c.close()
            c = Config.load(VFS.resolveWrite(_makePlayerIniName(str(pref[0]))), type=2)
            c.set("player", "leftymode", int(pref[1]))
            c.set("player", "drumflip", int(pref[2]))
            c.set("player", "auto_kick", int(pref[3]))
            c.set("player", "assist_mode", int(pref[4]))
            c.set("player", "two_chord_max", int(pref[5]))
            c.set("player", "necktype", int(pref[6]))
            c.set("player", "neck", str(pref[7]))
            c.set("player", "part", int(pref[8]))
            c.set("player", "difficulty", int(pref[9]))
            c.set("player", "name", str(pref[10]))
            c.set("player", "controller", int(pref[11]))
            del c
            _playerDB.execute('UPDATE `players` SET `changed` = 0 WHERE `name` = ?', [pref[0]])
    _playerDB.execute('UPDATE `players` SET `loaded` = 0')
    _playerDB.commit()


def updatePlayer(player, pref):
    a = _playerDB.execute('SELECT * FROM `players` WHERE `name` = ?', [player]).fetchone()
    try:
        a = a[0]
    except Exception:
        a = None
    if a is not None:
        _playerDB.execute('UPDATE `players` SET `name` = ?, `lefty` = ?, `drumflip` = ?, `autokick` = ?, `assist` = ?, `twochord` = ?, `necktype` = ?, `neck` = ?, \
                       `part` = 0, `difficulty` = 2, `upname` = ?, `control` = 0, `changed` = 1, `loaded` = 1 WHERE `name` = ?', pref + [player])
        if player != pref[0]:
            VFS.rename(_makePlayerIniName(player), _makePlayerIniName(pref[0]))
    else:
        _playerDB.execute('INSERT INTO `players` VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 2, ?, 0, 1, 1)', pref)
    _playerDB.commit()
    savePlayers()
    loadPlayers()


def deletePlayer(player):
    _playerDB.execute('DELETE FROM `players` WHERE `name` = ?', [player])
    VFS.unlink(_makePlayerIniName(player))
    if VFS.isfile('%s/%s.png' % (playerpath, player)):
        VFS.unlink('%s/%s.png' % (playerpath, player))
    savePlayers()
    loadPlayers()


def loadControls():
    global controllerDict
    controllers = []
    allcontrollers = VFS.listdir(controlpath)
    default = ["defaultd.ini", "defaultg.ini", "defaultm.ini"]
    for name in allcontrollers:
        if name.lower().endswith(".ini") and len(name) > 4:
            if name in default:
                continue
            controllers.append(name[0:len(name)-4])

    i = len(controllers)
    controllerDict = dict([(str(controllers[n]), controllers[n]) for n in range(0, i)])
    controllerDict["defaultg"] = _("Default Guitar")
    controllerDict["defaultd"] = _("Default Drum")
    defMic = None
    if Microphone.supported:
        controllerDict["defaultm"] = _("Default Microphone")
        defMic = "defaultm"
    tsControl    = _("Controller %d")
    tsControlTip = _("Select the controller for slot %d")
    i = 1
    Config.define("game", "control0", str, "defaultg", text=tsControl % 1, options=controllerDict, tipText=tsControlTip % 1)

    controllerDict[_("None")] = None

    Config.define("game", "control1", str, "defaultd", text=tsControl % 2, options=controllerDict, tipText=tsControlTip % 2)
    Config.define("game", "control2", str, defMic,     text=tsControl % 3, options=controllerDict, tipText=tsControlTip % 3)
    Config.define("game", "control3", str, None,       text=tsControl % 4, options=controllerDict, tipText=tsControlTip % 4)


def deleteControl(control):
    VFS.unlink(_makeControllerIniName(control))
    defaultUsed = -1
    for i in range(4):
        get = Config.get("game", "control%d" % i)
        if get == control:
            if i == 0:
                Config.set("game", "control%d" % i, "defaultg")
                defaultUsed = 0
            else:
                Config.set("game", "control%d" % i, None)
        if get == "defaultg" and defaultUsed > -1:
            Config.set("game", "control%d" % i, None)
    loadControls()


def renameControl(control, newname):
    VFS.rename(_makeControllerIniName(control), _makeControllerIniName(newname))
    for i in range(4):
        if Config.get("game", "control%d" % i) == control:
            Config.set("game", "control%d" % i, newname)
    loadControls()


def pluginControls(activeControls):
    global playerkeys, player0, player1, player2, player3
    playerkeys = [None] * 4
    for player, control in enumerate(activeControls):
        if control == 0:
            playerkeys[player] = CONTROL1
        elif control == 1:
            playerkeys[player] = CONTROL2
        elif control == 2:
            playerkeys[player] = CONTROL3
        elif control == 3:
            playerkeys[player] = CONTROL4
    player0 = playerkeys[0]
    player1 = playerkeys[1]
    player2 = playerkeys[2]
    player3 = playerkeys[3]


class Controls:
    def __init__(self):

        self.logClassInits = Config.get("game", "log_class_inits")
        if self.logClassInits == 1:
            log.debug("Controls class init (Player.py)...")

        self.controls = []
        self.controls.append(Config.get("game", "control0"))
        self.controls.append(Config.get("game", "control1"))
        self.controls.append(Config.get("game", "control2"))
        self.controls.append(Config.get("game", "control3"))
        self.config = []
        self.controlList = []
        self.maxplayers = 0
        self.guitars    = 0
        self.drums      = 0
        self.mics       = 0
        self.overlap    = []

        self.p2Nav = Config.get("game", "p2_menu_nav")
        self.drumNav = Config.get("game", "drum_navigation")

        self.keyCheckerMode = Config.get("game", "key_checker_mode")

        if VFS.isfile(_makeControllerIniName(self.controls[0])):
            self.config.append(Config.load(VFS.resolveRead(_makeControllerIniName(self.controls[0])), type=1))
            if VFS.isfile(_makeControllerIniName(self.controls[1])) and self.controls[1] != "None":
                self.config.append(Config.load(VFS.resolveRead(_makeControllerIniName(self.controls[1])), type=1))
            else:
                self.config.append(None)
                Config.set("game", "control1", None)
                self.controls[1] = "None"
            if VFS.isfile(_makeControllerIniName(self.controls[2])) and self.controls[2] != "None":
                self.config.append(Config.load(VFS.resolveRead(_makeControllerIniName(self.controls[2])), type=1))
            else:
                self.config.append(None)
                Config.set("game", "control2", None)
                self.controls[2] = "None"
            if VFS.isfile(_makeControllerIniName(self.controls[3])) and self.controls[3] != "None":
                self.config.append(Config.load(VFS.resolveRead(_makeControllerIniName(self.controls[3])), type=1))
            else:
                self.config.append(None)
                Config.set("game", "control3", None)
                self.controls[3] = "None"
        else:
            confM = None
            if Microphone.supported:
                confM = Config.load(VFS.resolveRead(_makeControllerIniName("defaultm")), type=1)
            self.config.append(Config.load(VFS.resolveRead(_makeControllerIniName("defaultg")), type=1))
            self.config.append(Config.load(VFS.resolveRead(_makeControllerIniName("defaultd")), type=1))
            self.config.append(confM)
            self.config.append(None)
            Config.set("game", "control0", "defaultg")
            Config.set("game", "control1", "defaultd")
            self.controls = ["defaultg", "defaultd"]
            if confM is not None:
                Config.set("game", "control2", "defaultm")
                self.controls.append("defaultm")
            else:
                Config.set("game", "control2", None)
                self.controls.append("None")
            Config.set("game", "control3", None)
            self.controls.append("None")

        self.type       = []
        self.analogKill = []
        self.analogSP   = []
        self.analogSPThresh = []
        self.analogSPSense  = []
        self.analogDrum = [] #FIXME: Analog Drum
        self.analogSlide = []
        self.analogFX   = [] #FIXME: Analog FX
        self.twoChord   = []
        self.micDevice  = []
        self.micTapSensitivity = []
        self.micPassthroughVolume = []

        self.flags = 0

        for i in self.config:
            if i:
                type = i.get("controller", "type")
                if type == 5:
                    self.mics += 1
                elif type > 1:
                    self.guitars += 1
                else:
                    self.drums += 1
                self.type.append(type)
                self.analogKill.append(i.get("controller", "analog_kill"))
                self.analogSP.append(i.get("controller", "analog_sp"))
                self.analogSPThresh.append(i.get("controller", "analog_sp_threshold"))
                self.analogSPSense.append(i.get("controller", "analog_sp_sensitivity"))
                self.analogDrum.append(i.get("controller", "analog_drum"))  #FIXME: Analog Drum
                self.analogSlide.append(i.get("controller", "analog_slide"))
                self.analogFX.append(i.get("controller", "analog_fx"))  #FIXME: Analog FX
                self.micDevice.append(i.get("controller", "mic_device"))
                self.micTapSensitivity.append(i.get("controller", "mic_tap_sensitivity"))
                self.micPassthroughVolume.append(i.get("controller", "mic_passthrough_volume"))
                self.twoChord.append(i.get("controller", "two_chord_max"))
                self.controlList.append(i.get("controller", "name"))
            else:
                self.type.append(None)
                self.analogKill.append(None)
                self.analogSP.append(None)
                self.analogFX.append(None)  #FIXME: Analog FX
                self.twoChord.append(None)

        def keycode(name, config):
            if not config:
                return "None"
            k = config.get("controller", name)
            if k == "None":
                return "None"
            try:
                return int(k)
            except Exception:
                return getattr(pygame, k)

        self.controlMapping = {}
        global menuUp, menuDown, menuNext, menuPrev, menuYes, menuNo
        global drum1s, drum2s, drum3s, drum4s, drum5s, bassdrums
        global key1s, key2s, key3s, key4s, key5s, keysolos, action1s, action2s, kills
        menuUp = []
        menuDown = []
        menuNext = []
        menuPrev = []
        menuYes = []
        menuNo = []
        drum1s = []
        drum2s = []
        drum3s = []
        drum4s = []
        drum5s = []
        bassdrums = []
        key1s = []
        key2s = []
        key3s = []
        key4s = []
        key5s = []
        keysolos = []
        action1s = []
        action2s = []
        kills = []

        for i, config in enumerate(self.config):
            if self.type[i] in DRUMTYPES: #drum set
                drum1s.extend([CONTROLS[i][DRUM1], CONTROLS[i][DRUM1A]])
                drum2s.extend([CONTROLS[i][DRUM2], CONTROLS[i][DRUM2A]])
                drum3s.extend([CONTROLS[i][DRUM3], CONTROLS[i][DRUM3A]])
                drum4s.extend([CONTROLS[i][DRUM4], CONTROLS[i][DRUM4A]])
                drum5s.extend([CONTROLS[i][DRUM5], CONTROLS[i][DRUM5A]])
                bassdrums.extend([CONTROLS[i][DRUMBASS], CONTROLS[i][DRUMBASSA]])
                if self.p2Nav == 1 or (self.p2Nav == 0 and i == 0):
                    if self.drumNav:
                        menuUp.extend([CONTROLS[i][DRUM2], CONTROLS[i][DRUM2A]])
                        if self.type[i] == 3:
                            menuDown.extend([CONTROLS[i][DRUM4], CONTROLS[i][DRUM4A]])
                        else:
                            menuDown.extend([CONTROLS[i][DRUM3], CONTROLS[i][DRUM3A]])
                        menuYes.extend([CONTROLS[i][DRUM5], CONTROLS[i][DRUM5A]])
                        menuNo.extend([CONTROLS[i][DRUM1], CONTROLS[i][DRUM1A]])
                    menuYes.append(CONTROLS[i][START])
                    menuNo.append(CONTROLS[i][CANCEL])
                    menuUp.append(CONTROLS[i][UP])
                    menuDown.append(CONTROLS[i][DOWN])
                    menuNext.append(CONTROLS[i][RIGHT])
                    menuPrev.append(CONTROLS[i][LEFT])
            elif self.type[i] in MICTYPES:  # it's a mic
                if self.p2Nav == 1 or (self.p2Nav == 0 and i == 0):
                    menuUp.append(CONTROLS[i][UP])
                    menuDown.append(CONTROLS[i][DOWN])
                    menuNext.append(CONTROLS[i][RIGHT])
                    menuPrev.append(CONTROLS[i][LEFT])
                    menuYes.append(CONTROLS[i][START])
                    menuNo.append(CONTROLS[i][CANCEL])
            elif self.type[i] in GUITARTYPES:
                if self.type[i] == 0:
                    key1s.extend([CONTROLS[i][KEY1], CONTROLS[i][KEY1A]])
                else:
                    key1s.extend([CONTROLS[i][KEY1]])
                key2s.extend([CONTROLS[i][KEY2], CONTROLS[i][KEY2A]])
                key3s.extend([CONTROLS[i][KEY3], CONTROLS[i][KEY3A]])
                key4s.extend([CONTROLS[i][KEY4], CONTROLS[i][KEY4A]])
                key5s.extend([CONTROLS[i][KEY5], CONTROLS[i][KEY5A]])
                keysolos.extend([CONTROLS[i][KEY1A], CONTROLS[i][KEY2A], CONTROLS[i][KEY3A], CONTROLS[i][KEY4A], CONTROLS[i][KEY5A]])
                action1s.extend([CONTROLS[i][ACTION1]])
                action2s.extend([CONTROLS[i][ACTION2]])
                kills.extend([CONTROLS[i][KILL]])
                if self.p2Nav == 1 or (self.p2Nav == 0 and i == 0):
                    menuUp.extend([CONTROLS[i][ACTION1], CONTROLS[i][UP]])
                    menuDown.extend([CONTROLS[i][ACTION2], CONTROLS[i][DOWN]])
                    menuNext.extend([CONTROLS[i][RIGHT], CONTROLS[i][KEY4], CONTROLS[i][KEY4A]])
                    menuPrev.extend([CONTROLS[i][LEFT], CONTROLS[i][KEY3], CONTROLS[i][KEY3A]])
                    menuYes.extend([CONTROLS[i][KEY1], CONTROLS[i][KEY1A], CONTROLS[i][START]])
                    menuNo.extend([CONTROLS[i][KEY2], CONTROLS[i][KEY2A], CONTROLS[i][CANCEL]])

            if self.type[i] == 3:
                # drums do not need special declarations!
                controlMapping = {
                    keycode("key_left", config):          CONTROLS[i][LEFT],
                    keycode("key_right", config):         CONTROLS[i][RIGHT],
                    keycode("key_up", config):            CONTROLS[i][UP],
                    keycode("key_down", config):          CONTROLS[i][DOWN],
                    keycode("key_star", config):          CONTROLS[i][STAR],
                    keycode("key_cancel", config):        CONTROLS[i][CANCEL],
                    keycode("key_1a", config):            CONTROLS[i][DRUM5A],  # order is important. This minimizes key conflicts.
                    keycode("key_2a", config):            CONTROLS[i][DRUM1A],
                    keycode("key_3a", config):            CONTROLS[i][DRUM2A],
                    keycode("key_4a", config):            CONTROLS[i][DRUM3A],
                    keycode("key_5a", config):            CONTROLS[i][DRUM4A],
                    keycode("key_action2", config):       CONTROLS[i][DRUMBASSA],
                    keycode("key_1", config):             CONTROLS[i][DRUM5],
                    keycode("key_2", config):             CONTROLS[i][DRUM1],
                    keycode("key_3", config):             CONTROLS[i][DRUM2],
                    keycode("key_4", config):             CONTROLS[i][DRUM3],
                    keycode("key_5", config):             CONTROLS[i][DRUM4],
                    keycode("key_action1", config):       CONTROLS[i][DRUMBASS],
                    keycode("key_start", config):         CONTROLS[i][START],
                }
            elif self.type[i] == 2:
                # drums do not need special declarations!
                controlMapping = {
                    keycode("key_left", config):          CONTROLS[i][LEFT],
                    keycode("key_right", config):         CONTROLS[i][RIGHT],
                    keycode("key_up", config):            CONTROLS[i][UP],
                    keycode("key_down", config):          CONTROLS[i][DOWN],
                    keycode("key_star", config):          CONTROLS[i][STAR],
                    keycode("key_cancel", config):        CONTROLS[i][CANCEL],
                    keycode("key_1a", config):            CONTROLS[i][DRUM5A],  # order is important. This minimizes key conflicts.
                    keycode("key_2a", config):            CONTROLS[i][DRUM1A],
                    keycode("key_3a", config):            CONTROLS[i][DRUM2A],
                    keycode("key_4a", config):            CONTROLS[i][DRUM3A],
                    keycode("key_action2", config):       CONTROLS[i][DRUMBASSA],
                    keycode("key_1", config):             CONTROLS[i][DRUM5],
                    keycode("key_2", config):             CONTROLS[i][DRUM1],
                    keycode("key_3", config):             CONTROLS[i][DRUM2],
                    keycode("key_4", config):             CONTROLS[i][DRUM3],
                    keycode("key_action1", config):       CONTROLS[i][DRUMBASS],
                    keycode("key_start", config):         CONTROLS[i][START],
                }
            elif self.type[i] > -1:
                # drums do not need special declarations!
                controlMapping = {
                    keycode("key_left", config):          CONTROLS[i][LEFT],
                    keycode("key_right", config):         CONTROLS[i][RIGHT],
                    keycode("key_up", config):            CONTROLS[i][UP],
                    keycode("key_down", config):          CONTROLS[i][DOWN],
                    keycode("key_cancel", config):        CONTROLS[i][CANCEL],
                    keycode("key_star", config):          CONTROLS[i][STAR],
                    keycode("key_kill", config):          CONTROLS[i][KILL],
                    keycode("key_1a", config):            CONTROLS[i][KEY1A],  # order is important. This minimizes key conflicts.
                    keycode("key_2a", config):            CONTROLS[i][KEY2A],
                    keycode("key_3a", config):            CONTROLS[i][KEY3A],
                    keycode("key_4a", config):            CONTROLS[i][KEY4A],
                    keycode("key_5a", config):            CONTROLS[i][KEY5A],
                    keycode("key_1", config):             CONTROLS[i][KEY1],
                    keycode("key_2", config):             CONTROLS[i][KEY2],
                    keycode("key_3", config):             CONTROLS[i][KEY3],
                    keycode("key_4", config):             CONTROLS[i][KEY4],
                    keycode("key_5", config):             CONTROLS[i][KEY5],
                    keycode("key_action2", config):       CONTROLS[i][ACTION2],
                    keycode("key_action1", config):       CONTROLS[i][ACTION1],
                    keycode("key_start", config):         CONTROLS[i][START],
                }
            else:
                controlMapping = {}
            controlMapping = self.checkMapping(controlMapping, i)
            self.controlMapping.update(controlMapping)

        self.reverseControlMapping = dict((value, key) for key, value in self.controlMapping.items())

        # Multiple key support
        self.heldKeys = {}

    def checkMapping(self, newDict, i):
        def keyName(value):
            if value in CONTROL1:
                name = "Controller 1"
                control = CONTROL1
                n = 0
            elif value in CONTROL2:
                name = "Controller 2"
                control = CONTROL2
                n = 1
            elif value in CONTROL3:
                name = "Controller 3"
                control = CONTROL3
                n = 2
            else:
                name = "Controller 4"
                control = CONTROL4
                n = 3
            for j in range(20):
                if value == control[j]:
                    if self.type[n] == 2:
                        return name + " " + drumkey4names[j]
                    elif self.type[n] == 3:
                        return name + " " + drumkey5names[j]
                    else:
                        return name + " " + guitarkeynames[j]
            else:
                log.info("Key value not found.")
                return "Error"

        if self.keyCheckerMode == 0:
            return newDict
        okconflict = lefts + rights + ups + downs + starts + cancels
        a = []
        for key, value in newDict.items():
            if key == "None":
                continue
            if key in self.controlMapping.keys():
                if value in okconflict:
                    if self.getMapping(key) in okconflict:
                        continue
                a.append(_("%s conflicts with %s") % (keyName(value), keyName(self.getMapping(key))))
        if len(a) == 0:
            return newDict
        self.overlap.extend(a)
        return newDict

    def getMapping(self, key):
        return self.controlMapping.get(key)

    def getReverseMapping(self, control):
        return self.reverseControlMapping.get(control)

    def keyPressed(self, key):
        c = self.getMapping(key)
        if c:
            self.toggle(c, True)
            if c in self.heldKeys and key not in self.heldKeys[c]:
                self.heldKeys[c].append(key)
            return c
        return None

    def keyReleased(self, key):
        c = self.getMapping(key)
        if c:
            if c in self.heldKeys:
                if key in self.heldKeys[c]:
                    self.heldKeys[c].remove(key)
                    if not self.heldKeys[c]:
                        self.toggle(c, False)
                        return c
                return None
            self.toggle(c, False)
            return c
        return None

    def toggle(self, control, state):
        prevState = self.flags
        if state:
            self.flags |= control
            return not prevState & control
        else:
            self.flags &= ~control
            return prevState & control

    def getState(self, control):
        return self.flags & control


# returns False if there are any key mapping conflicts
def isKeyMappingOK(config, start):
    def keycode(name, config):
        k = config.get("controller", name)
        if k is None or k == "None":
            return None
        try:
            return int(k)
        except Exception:
            return getattr(pygame, k)

    # list of keys to look for
    keyNames = ["key_action1", "key_action2", "key_1", "key_2", "key_3", "key_4", "key_5", "key_1a", "key_2a", "key_3a", "key_4a", "key_5a", "key_start", "key_star", "key_kill", "key_cancel"]
    overlap = []
    keyVal = []
    for i in keyNames:
        if config.get("controller", i) in keyVal and i != start:
            overlap.append(config.prototype["controller"][i].text)
        else:
            keyVal.append(keycode(i, config))

    if len(overlap) > 0:
        return overlap

        # everything tests OK
    return 0


# sets the key mapping and checks for a conflict #FIXME
# restores the old mapping if a conflict occurred
def setNewKeyMapping(engine, config, section, option, key):
    oldKey = config.get(section, option)
    config.set(section, option, key)
    keyCheckerMode = Config.get("game", "key_checker_mode")
    if key == "None" or key is None:
        return True
    b = isKeyMappingOK(config, option)
    if b != 0:
        if keyCheckerMode > 0:
            from fofix.game import Dialogs
            Dialogs.showMessage(engine, _("This key conflicts with the following keys: %s") % str(b))
        if keyCheckerMode == 2:   #enforce no conflicts!
            config.set(section, option, oldKey)
        return False
    return True


class Player(object):
    def __init__(self, name, number):

        self.logClassInits = Config.get("game", "log_class_inits")
        if self.logClassInits == 1:
            log.debug("Player class init (Player.py)...")

        self.name = name

        self.reset()
        self.keyList = None

        self.progressKeys = []
        self.drums        = []
        self.keys         = []
        self.soloKeys     = []
        self.soloShift    = None
        self.soloSlide    = False
        self.actions      = []
        self.yes          = []
        self.no           = []
        self.conf         = []
        self.up           = []
        self.down         = []
        self.left         = []
        self.right        = []
        self.controller   = -1
        self.controlType  = -1

        self.guitarNum    = None
        self.number       = number

        self.bassGrooveEnabled = False
        self.currentTheme = 1

        self.lefty       = _playerDB.execute('SELECT `lefty` FROM `players` WHERE `name` = ?', [self.name]).fetchone()[0]
        self.twoChordMax = _playerDB.execute('SELECT `twochord` FROM `players` WHERE `name` = ?', [self.name]).fetchone()[0]
        self.drumflip    = _playerDB.execute('SELECT `drumflip` FROM `players` WHERE `name` = ?', [self.name]).fetchone()[0]
        self.assistMode  = _playerDB.execute('SELECT `assist` FROM `players` WHERE `name` = ?', [self.name]).fetchone()[0]
        self.autoKick    = _playerDB.execute('SELECT `autokick` FROM `players` WHERE `name` = ?', [self.name]).fetchone()[0]
        self.neck        = _playerDB.execute('SELECT `neck` FROM `players` WHERE `name` = ?', [self.name]).fetchone()[0]
        self.neckType    = _playerDB.execute('SELECT `necktype` FROM `players` WHERE `name` = ?', [self.name]).fetchone()[0]
        self.whichPart   = _playerDB.execute('SELECT `part` FROM `players` WHERE `name` = ?', [self.name]).fetchone()[0]
        self._upname      = _playerDB.execute('SELECT `upname` FROM `players` WHERE `name` = ?', [self.name]).fetchone()[0]
        self._difficulty  = _playerDB.execute('SELECT `difficulty` FROM `players` WHERE `name` = ?', [self.name]).fetchone()[0]
        # need to store selected practice mode and start position here
        self.practiceMode = False
        self.practiceSpeed = 1.0
        self.practiceSection = None
        self.startPos = 0.0

        self.hopoFreq = None

    def reset(self):
        self.twoChord = 0

    def configController(self):
        if self.keyList:
            if self.controlType == 1:
                self.keys     = [self.keyList[KEY1], self.keyList[KEY2], self.keyList[KEY3], self.keyList[KEY4], self.keyList[KEY5],
                                 self.keyList[KEY1], self.keyList[KEY2], self.keyList[KEY3], self.keyList[KEY4], self.keyList[KEY5]]
                self.soloKeys = [self.keyList[KEY1], self.keyList[KEY2], self.keyList[KEY3], self.keyList[KEY4], self.keyList[KEY5]]
            else:
                self.keys = [self.keyList[KEY1], self.keyList[KEY2], self.keyList[KEY3], self.keyList[KEY4], self.keyList[KEY5],
                             self.keyList[KEY1A], self.keyList[KEY2A], self.keyList[KEY3A], self.keyList[KEY4A], self.keyList[KEY5A]]
                self.soloKeys = [self.keyList[KEY1A], self.keyList[KEY2A], self.keyList[KEY3A], self.keyList[KEY4A], self.keyList[KEY5A]]
            self.soloShift = self.keyList[KEY1A]
            self.drumSolo = []
            self.actions  = [self.keyList[ACTION1], self.keyList[ACTION2]]
            self.drums    = [self.keyList[DRUMBASS], self.keyList[DRUM1], self.keyList[DRUM2], self.keyList[DRUM3], self.keyList[DRUM5],
                             self.keyList[DRUMBASSA], self.keyList[DRUM1A], self.keyList[DRUM2A], self.keyList[DRUM3A], self.keyList[DRUM5A]]
            if self.controlType == 1:
                self.progressKeys = [self.keyList[KEY1], self.keyList[CANCEL], self.keyList[START], self.keyList[KEY2]]
            else:
                self.progressKeys = [self.keyList[KEY1], self.keyList[KEY1A], self.keyList[CANCEL], self.keyList[START], self.keyList[KEY2],
                                     self.keyList[KEY2A]]
            if self.controlType == 4:
                self.soloSlide = True
            else:
                self.soloSlide = False
            if self.controlType in GUITARTYPES:
                self.yes  = [self.keyList[KEY1]]
                if self.controlType == 1:
                    self.yes.append(self.keyList[KEY1A])
                self.no   = [self.keyList[KEY2], self.keyList[KEY2A]]
                self.up   = [self.keyList[ACTION1]]
                self.down = [self.keyList[ACTION2]]
            elif self.controlType == 2:
                self.yes  = [self.keyList[DRUM5], self.keyList[DRUM5A]]
                self.no   = [self.keyList[DRUM1], self.keyList[DRUM1A]]
                self.up   = [self.keyList[DRUM2], self.keyList[DRUM2A]]
                self.down = [self.keyList[DRUM3], self.keyList[DRUM3A]]
                self.conf = [self.keyList[DRUMBASS], self.keyList[DRUMBASSA]]
            self.yes.append(self.keyList[START])
            self.no.append(self.keyList[CANCEL])
            self.up.append(self.keyList[UP])
            self.down.append(self.keyList[DOWN])
            self.left.append(self.keyList[LEFT])
            self.right.append(self.keyList[RIGHT])
            # add drum4 to the drums when ready
            return True
        else:
            return False

    def getName(self):
        if self._upname == "" or self._upname is None:
            return self.name
        else:
            return self._upname

    def setName(self, name):
        _playerDB.execute('UPDATE `players` SET `upname` = ?, `changed` = 1 WHERE `name` = ?', [name, self.name])
        _playerDB.commit()
        self._upname = name

    def getDifficulty(self):
        return song.difficulties.get(self._difficulty)

    def setDifficulty(self, difficulty):
        _playerDB.execute('UPDATE `players` SET `difficulty` = ?, `changed` = 1 WHERE `name` = ?', [difficulty.id, self.name])
        _playerDB.commit()
        self._difficulty = difficulty.id

    def getDifficultyInt(self):
        return self._difficulty

    def getPart(self):
        # this should not be reading from the ini file each time it wants to know the part
        if self.whichPart == -2:
            return "No Player 2"
        else:
            return song.parts.get(self.whichPart)

    def setPart(self, part):
        if part == "No Player 2":
            self.whichPart = -2  # also need to set self.part here to avoid unnecessary ini reads
        else:
            self.whichPart = part.id  # also need to set self.part here to avoid unnecessary ini reads
        _playerDB.execute('UPDATE `players` SET `part` = ?, `changed` = 1 WHERE `name` = ?', [self.whichPart, self.name])
        _playerDB.commit()

    difficulty = property(getDifficulty, setDifficulty)
    part = property(getPart, setPart)
    upname = property(getName, setName)
