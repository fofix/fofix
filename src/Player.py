#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire                                                     #
# Copyright (C) 2006 Sami Kyöstilä                                  #
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

import pygame
import Config
import Song
from Language import _

import Log

#myfingershurt: manually re-enumerated these to avoid conflicts
#PLAYER 0 KEYS
LEFT              = 0x1
RIGHT             = 0x2
UP                = 0x4
DOWN              = 0x8
ACTION1           = 0x10
ACTION2           = 0x20
KEY1              = 0x40
KEY2              = 0x80
KEY3              = 0x100
KEY4              = 0x200
KEY5              = 0x400
CANCEL            = 0x800
STAR              = 0x1000
KILL              = 0x2000
#myfingershurt: adding drums
DRUM1A            = 0x4000
DRUM2A            = 0x8000
DRUM3A            = 0x10000
DRUM4A            = 0x20000
BASS              = 0x40000
DRUM1B            = 0x80000
DRUM2B            = 0x100000
DRUM3B            = 0x200000
DRUM4B            = 0x400000
#PLAYER 1 KEYS
PLAYER_2_LEFT     = 0x1000000
PLAYER_2_RIGHT    = 0x2000000
PLAYER_2_UP       = 0x4000000
PLAYER_2_DOWN     = 0x8000000
PLAYER_2_ACTION1  = 0x10000000
PLAYER_2_ACTION2  = 0x20000000
PLAYER_2_KEY1     = 0x40000000
PLAYER_2_KEY2     = 0x80000000
PLAYER_2_KEY3     = 0x100000000
PLAYER_2_KEY4     = 0x200000000
PLAYER_2_KEY5     = 0x400000000
PLAYER_2_CANCEL   = 0x800000000
PLAYER_2_STAR     = 0x1000000000
PLAYER_2_KILL     = 0x2000000000
#myfingershurt: adding drums
PLAYER_2_DRUM1A   = 0x4000000000
PLAYER_2_DRUM2A   = 0x8000000000
PLAYER_2_DRUM3A   = 0x10000000000
PLAYER_2_DRUM4A   = 0x20000000000
PLAYER_2_BASS     = 0x40000000000
PLAYER_2_DRUM1B   = 0x80000000000
PLAYER_2_DRUM2B   = 0x100000000000
PLAYER_2_DRUM3B   = 0x200000000000
PLAYER_2_DRUM4B   = 0x400000000000

LEFTS  = [LEFT,PLAYER_2_LEFT]
RIGHTS = [RIGHT,PLAYER_2_RIGHT]
UPS    = [UP,PLAYER_2_UP]
DOWNS  = [DOWN,PLAYER_2_DOWN]
ACTION1S= [ACTION1,PLAYER_2_ACTION1]
ACTION2S= [ACTION2,PLAYER_2_ACTION2]
CANCELS= [CANCEL,PLAYER_2_CANCEL]
KEY1S  = [KEY1,PLAYER_2_KEY1]
KEY2S  = [KEY2,PLAYER_2_KEY2]
KEY3S  = [KEY3,PLAYER_2_KEY3]
KEY4S  = [KEY4,PLAYER_2_KEY4]
KEY5S  = [KEY5,PLAYER_2_KEY5]
STARS  = [STAR,PLAYER_2_STAR] # glorandwarf: don't know if this is needed but...
KILLS  = [KILL,PLAYER_2_KILL] # glorandwarf: don't know if this is needed but...

#myfingershurt: adding drums
DRUM1S = [DRUM1A, DRUM1B, PLAYER_2_DRUM1A, PLAYER_2_DRUM1B]
DRUM2S = [DRUM2A, DRUM2B, PLAYER_2_DRUM2A, PLAYER_2_DRUM2B]
DRUM3S = [DRUM3A, DRUM3B, PLAYER_2_DRUM3A, PLAYER_2_DRUM3B]
DRUM4S = [DRUM4A, DRUM4B, PLAYER_2_DRUM4A, PLAYER_2_DRUM4B]
BASEDRUMS = [BASS, PLAYER_2_BASS]

SCORE_MULTIPLIER = [0, 10, 20, 30]
BASS_GROOVE_SCORE_MULTIPLIER = [0, 10, 20, 30, 40, 50]

# define configuration keys
Config.define("player0", "key_left",     str, "K_LEFT",   text = _("P1 Move left"))
Config.define("player0", "key_right",    str, "K_RIGHT",  text = _("P1 Move right"))
Config.define("player0", "key_up",       str, "K_UP",     text = _("P1 Move up"))
Config.define("player0", "key_down",     str, "K_DOWN",   text = _("P1 Move down"))
Config.define("player0", "key_action1",  str, "K_RETURN", text = _("P1 Pick"))
Config.define("player0", "key_action2",  str, "K_RSHIFT", text = _("P1 Secondary Pick"))
Config.define("player0", "key_1",        str, "K_F1",     text = _("P1 Fret #1"))
Config.define("player0", "key_2",        str, "K_F2",     text = _("P1 Fret #2"))
Config.define("player0", "key_3",        str, "K_F3",     text = _("P1 Fret #3"))
Config.define("player0", "key_4",        str, "K_F4",     text = _("P1 Fret #4"))
Config.define("player0", "key_5",        str, "K_F5",     text = _("P1 Fret #5"))
Config.define("player0", "key_cancel",   str, "K_ESCAPE", text = _("P1 Cancel"))
Config.define("player0", "key_star",     str, "K_PAGEDOWN", text = _("P1 StarPower"))
Config.define("player0", "key_kill",     str, "K_PAGEUP", text = _("P1 Killswitch"))
Config.define("player0", "akey_left",    str, "K_LEFT",   text = _("Alt P1 Move left"))
Config.define("player0", "akey_right",   str, "K_RIGHT",  text = _("Alt P1 Move right"))
Config.define("player0", "akey_up",      str, "K_UP",     text = _("Alt P1 Move up"))
Config.define("player0", "akey_down",    str, "K_DOWN",   text = _("Alt P1 Move down"))
Config.define("player0", "akey_action1", str, "K_RETURN", text = _("Alt P1 Pick"))
Config.define("player0", "akey_action2", str, "K_RSHIFT", text = _("Alt P1 Secondary Pick"))
Config.define("player0", "akey_1",       str, "K_F1",     text = _("Alt P1 Fret #1"))
Config.define("player0", "akey_2",       str, "K_F2",     text = _("Alt P1 Fret #2"))
Config.define("player0", "akey_3",       str, "K_F3",     text = _("Alt P1 Fret #3"))
Config.define("player0", "akey_4",       str, "K_F4",     text = _("Alt P1 Fret #4"))
Config.define("player0", "akey_5",       str, "K_F5",     text = _("Alt P1 Fret #5"))
Config.define("player0", "akey_cancel",  str, "K_ESCAPE", text = _("Alt P1 Cancel"))
Config.define("player0", "akey_star",    str, "K_PAGEDOWN", text = _("Alt P1 StarPower"))
Config.define("player0", "akey_kill",    str, "K_PAGEUP", text = _("Alt P1 Killswitch"))

Config.define("player0", "name",         str, "")
Config.define("player0", "difficulty",   int, Song.MED_DIF)
Config.define("player0", "part",         int, Song.GUITAR_PART)

##alarian
Config.define("player1", "player_2_key_left",     str, "K_LEFT",     text = _("P2 Move left")) #QQstarS: set it
Config.define("player1", "player_2_key_right",    str, "K_RIGHT",    text = _("P2 Move right"))
Config.define("player1", "player_2_key_up",       str, "K_UP",       text = _("P2 Move up"))
Config.define("player1", "player_2_key_down",     str, "K_DOWN",     text = _("P2 Move down"))
Config.define("player1", "player_2_key_action1",  str, "K_DELETE",   text = _("P2 Pick")) # glorandwarf
Config.define("player1", "player_2_key_action2",  str, "K_INSERT",   text = _("P2 Secondary Pick")) # glorandwarf
Config.define("player1", "player_2_key_1",        str, "K_F8",       text = _("P2 Fret #1"))
Config.define("player1", "player_2_key_2",        str, "K_F9",       text = _("P2 Fret #2"))
Config.define("player1", "player_2_key_3",        str, "K_F10",      text = _("P2 Fret #3"))
Config.define("player1", "player_2_key_4",        str, "K_F11",      text = _("P2 Fret #4"))
Config.define("player1", "player_2_key_5",        str, "K_F12",      text = _("P2 Fret #5"))
Config.define("player1", "player_2_key_cancel",   str, "K_F7",       text = _("P2 Cancel"))
Config.define("player1", "player_2_key_star",     str, "K_HOME", text = _("P2 StarPower")) #QQstarS:add the starpower key
Config.define("player1", "player_2_key_kill",     str, "K_END", text = _("P2 Killswitch")) #QQstarS:add kill key
##
Config.define("player1", "aplayer_2_key_left",     str, "K_LEFT",     text = _("Alt P2 Move left"))
Config.define("player1", "aplayer_2_key_right",    str, "K_RIGHT",    text = _("Alt P2 Move right"))
Config.define("player1", "aplayer_2_key_up",       str, "K_UP",       text = _("Alt P2 Move up"))
Config.define("player1", "aplayer_2_key_down",     str, "K_DOWN",     text = _("Alt P2 Move down"))
Config.define("player1", "aplayer_2_key_action1",  str, "K_DELETE",   text = _("Alt P2 Pick")) # glorandwarf
Config.define("player1", "aplayer_2_key_action2",  str, "K_INSERT",   text = _("Alt P2 Secondary Pick")) # glorandwarf
Config.define("player1", "aplayer_2_key_1",        str, "K_F8",       text = _("Alt P2 Fret #1"))
Config.define("player1", "aplayer_2_key_2",        str, "K_F9",       text = _("Alt P2 Fret #2"))
Config.define("player1", "aplayer_2_key_3",        str, "K_F10",      text = _("Alt P2 Fret #3"))
Config.define("player1", "aplayer_2_key_4",        str, "K_F11",      text = _("Alt P2 Fret #4"))
Config.define("player1", "aplayer_2_key_5",        str, "K_F12",      text = _("Alt P2 Fret #5"))
Config.define("player1", "aplayer_2_key_cancel",   str, "K_F7",       text = _("Alt P2 Cancel"))
Config.define("player1", "aplayer_2_key_star",     str, "K_HOME", text = _("Alt P2 StarPower"))  #QQstarS:add
Config.define("player1", "aplayer_2_key_kill",     str, "K_END", text = _("Alt P2 Killswitch"))  #QQstarS:add

#myfingershurt: drums
Config.define("player0", "key_bass", str, "K_SPACE", text = _("Bass drum"))
Config.define("player0", "key_drum1a", str, "K_a", text = _("Drum #1"))
Config.define("player0", "key_drum2a", str, "K_e", text = _("Drum #2"))
Config.define("player0", "key_drum3a", str, "K_t", text = _("Drum #3"))
Config.define("player0", "key_drum4a", str, "K_u", text = _("Drum #4"))
Config.define("player0", "key_drum1b", str, "K_s", text = _("Drum #1"))
Config.define("player0", "key_drum2b", str, "K_r", text = _("Drum #2"))
Config.define("player0", "key_drum3b", str, "K_y", text = _("Drum #3"))
Config.define("player0", "key_drum4b", str, "K_i", text = _("Drum #4"))
Config.define("player1", "player_2_key_bass", str, "K_l", text = _("Player 2 Bass drum"))
Config.define("player1", "player_2_key_drum1a", str, "K_z", text = _("Player 2 Drum #1"))
Config.define("player1", "player_2_key_drum2a", str, "K_d", text = _("Player 2 Drum #2"))
Config.define("player1", "player_2_key_drum3a", str, "K_g", text = _("Player 2 Drum #3"))
Config.define("player1", "player_2_key_drum4a", str, "K_j", text = _("Player 2 Drum #4"))
Config.define("player1", "player_2_key_drum1b", str, "K_x", text = _("Player 2 Drum #1"))
Config.define("player1", "player_2_key_drum2b", str, "K_f", text = _("Player 2 Drum #2"))
Config.define("player1", "player_2_key_drum3b", str, "K_h", text = _("Player 2 Drum #3"))
Config.define("player1", "player_2_key_drum4b", str, "K_k", text = _("Player 2 Drum #4"))


Config.define("player1", "name",         str, "")
Config.define("player1", "difficulty",   int, Song.MED_DIF)
Config.define("player1", "part",         int, Song.GUITAR_PART)

class Controls:
  def __init__(self):
    Log.debug("Controls class init (Player.py)...")
    
    def keycode(name, player):
      playerstring = "player" + str(player)
      k = Config.get(playerstring, name)
      try:
        return int(k)
      except:
        return getattr(pygame, k)
    
    self.flags = 0
    prefix = ""

    self.Player2KeysEnabled = Config.get("game", "p2_menu_nav")
    
    self.keyCheckerMode = Config.get("game","key_checker_mode")
    
    useAltKeySet = Config.get("game", "alt_keys")
    if useAltKeySet == True:
      prefix = "a"
      
    #----------------------------------------------------------
    # glorandwarf: only map in player 2's keys if needed
    self.controlMapping = {
      keycode("%skey_left" % (prefix), 0):      LEFT,
      keycode("%skey_right" % (prefix), 0):     RIGHT,
      keycode("%skey_up" % (prefix), 0):        UP,
      keycode("%skey_down" % (prefix), 0):      DOWN,
      keycode("%skey_action1" % (prefix), 0):   ACTION1,
      keycode("%skey_action2" % (prefix), 0):   ACTION2,
      keycode("%skey_1" % (prefix), 0):         KEY1,
      keycode("%skey_2" % (prefix), 0):         KEY2,
      keycode("%skey_3" % (prefix), 0):         KEY3,
      keycode("%skey_4" % (prefix), 0):         KEY4,
      keycode("%skey_5" % (prefix), 0):         KEY5,
      keycode("%skey_cancel" % (prefix), 0):    CANCEL,
      keycode("%skey_star" % (prefix), 0):      STAR,
      keycode("%skey_kill" % (prefix), 0):      KILL,
      keycode("key_bass", 0):      BASS,    #myfingershurt: drums
      keycode("key_drum1a", 0):    DRUM1A,  
      keycode("key_drum2a", 0):    DRUM2A,
      keycode("key_drum3a", 0):    DRUM3A,
      keycode("key_drum4a", 0):    DRUM4A,
      keycode("key_drum1b", 0):    DRUM1B,
      keycode("key_drum2b", 0):    DRUM2B,
      keycode("key_drum3b", 0):    DRUM3B,
      keycode("key_drum4b", 0):    DRUM4B,

      
    }
    if self.Player2KeysEnabled == 1:    #MFH - menu option for this
      p2map = {
        keycode("%splayer_2_key_action1" % (prefix), 1):   PLAYER_2_ACTION1, #QQstarS:add
        keycode("%splayer_2_key_action2" % (prefix), 1):   PLAYER_2_ACTION2,
        keycode("%splayer_2_key_1" % (prefix), 1):         PLAYER_2_KEY1,
        keycode("%splayer_2_key_2" % (prefix), 1):         PLAYER_2_KEY2,
        keycode("%splayer_2_key_3" % (prefix), 1):         PLAYER_2_KEY3,
        keycode("%splayer_2_key_4" % (prefix), 1):         PLAYER_2_KEY4,
        keycode("%splayer_2_key_5" % (prefix), 1):         PLAYER_2_KEY5,
        keycode("%splayer_2_key_left" % (prefix), 1):      PLAYER_2_LEFT,
        keycode("%splayer_2_key_right" % (prefix), 1):     PLAYER_2_RIGHT,
        keycode("%splayer_2_key_up" % (prefix), 1):        PLAYER_2_UP,
        keycode("%splayer_2_key_down" % (prefix), 1):      PLAYER_2_DOWN,
        keycode("%splayer_2_key_cancel" % (prefix), 1):    PLAYER_2_CANCEL,
        keycode("%splayer_2_key_star" % (prefix), 1):      PLAYER_2_STAR, #QQstarS:add
        keycode("%splayer_2_key_kill" % (prefix), 1):      PLAYER_2_KILL, #QQstarS:add
        keycode("player_2_key_bass", 1):      PLAYER_2_BASS,    #myfingershurt: drums
        keycode("player_2_key_drum1a", 1):    PLAYER_2_DRUM1A,  
        keycode("player_2_key_drum2a", 1):    PLAYER_2_DRUM2A,
        keycode("player_2_key_drum3a", 1):    PLAYER_2_DRUM3A,
        keycode("player_2_key_drum4a", 1):    PLAYER_2_DRUM4A,
        keycode("player_2_key_drum1b", 1):    PLAYER_2_DRUM1B,
        keycode("player_2_key_drum2b", 1):    PLAYER_2_DRUM2B,
        keycode("player_2_key_drum3b", 1):    PLAYER_2_DRUM3B,
        keycode("player_2_key_drum4b", 1):    PLAYER_2_DRUM4B,
      }
      self.controlMapping.update(p2map)
    #----------------------------------------------------------

    self.reverseControlMapping = dict((value, key) for key, value in self.controlMapping.iteritems() )
      
    # Multiple key support
    self.heldKeys = {}

  def getMapping(self, key):
    return self.controlMapping.get(key)
  def getReverseMapping(self, control):
    return self.reverseControlMapping.get(control)

  def keyPressed(self, key):
    c = self.getMapping(key)
    if c:
      self.toggle(c, True)
      if c in self.heldKeys and not key in self.heldKeys[c]:
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

  #----------------------------------------------------------

  # glorandwarf: returns False if there are any key mapping conflicts
  def isKeyMappingOK(self):
    def keycode(name, player, alt):
      playerstring = "player" + str(player)
      name = "key_" + name
      if player == 1:
        name = "player_2_" + name
      if alt == True:
        name = "a" + name
      k = Config.get(playerstring, name)
      try:
        return int(k)
      except:
        return getattr(pygame, k)

    # list of keys to look for
    drumkeyNames = ["drum1a","drum1b","drum2a","drum2b","drum3a","drum3b","drum4a","drum4b","bass"]
    keyNames = ["left","right","up","down","action1","action2","1","2","3","4","5","cancel","star","kill"]
    keyNames = keyNames + drumkeyNames
    drumnumKeys = len(drumkeyNames)
    numKeys = len(keyNames)
    
    # build a list and set for each key mapping group
    p1list = []
    p2list = []
    p1list_alt = []
    p2list_alt = []
    for index in range(numKeys):
      p1list.append(keycode(keyNames[index], 0, False))
      p2list.append(keycode(keyNames[index], 1, False))
    for index in range(numKeys - drumnumKeys):      
      p1list_alt.append(keycode(keyNames[index], 0, True))
      p2list_alt.append(keycode(keyNames[index], 1, True))
    p1set = set(p1list)
    p2set = set(p2list)
    p1set_alt = set(p1list_alt)
    p2set_alt = set(p2list_alt)

    # check each set for possible conflicts
    if len(p1set) != numKeys or len(p2set) != numKeys or len(p1set_alt) != (numKeys - drumnumKeys) or len(p2set_alt) != (numKeys - drumnumKeys):
      return False
       
    # check for conflicts between normal sets
    overlap = len(p1set.intersection(p2set))
    if overlap > 4:   # too many overlaps to be only movement keys, conflict!
      return False
    elif overlap > 0:   # check the movement keys for overlaps
      if p1list[0] == p2list[0]:  overlap -= 1    # KEY_LEFT
      if p1list[1] == p2list[1]:  overlap -= 1    # KEY_RIGHT
      if p1list[2] == p2list[2]:  overlap -= 1    # KEY_UP
      if p1list[3] == p2list[3]:  overlap -= 1    # KEY_DOWN
      if overlap > 0: # any remaining overlaps conflict!
        return False

    # check for conflicts between alternate sets
    overlap = len(p1set_alt.intersection(p2set_alt))
    if overlap > 4:   # too many overlaps to be only movement keys, conflict!
      return False
    elif overlap > 0:   # check the movement keys for overlaps
      if p1list_alt[0] == p2list_alt[0]:  overlap -= 1    # KEY_LEFT
      if p1list_alt[1] == p2list_alt[1]:  overlap -= 1    # KEY_RIGHT
      if p1list_alt[2] == p2list_alt[2]:  overlap -= 1    # KEY_UP
      if p1list_alt[3] == p2list_alt[3]:  overlap -= 1    # KEY_DOWN
      if overlap > 0: # any remaining overlaps conflict!
        return False

    # everything tests OK
    return True

  #----------------------------------------------------------

  # glorandwarf: restores the controls to their defaults
  def restoreDefaultKeyMappings(self):
    def key(name, player, alt):
      playerstring = "player" + str(player)
      name = "key_" + name
      if player == 1:
        name = "player_2_" + name
      if alt == True:
        name = "a" + name
      k = Config.getDefault(playerstring, name)
      Config.set(playerstring, name, k)

    # list of keys to look for
    drumkeyNames = ["drum1a","drum1b","drum2a","drum2b","drum3a","drum3b","drum4a","drum4b","bass"]
    keyNames = ["left","right","up","down","action1","action2","1","2","3","4","5","cancel","star","kill"]
    keyNames = keyNames + drumkeyNames

    # restore the keys to their defaults
    for index in range(len(keyNames)):
      key(keyNames[index], 0, False)
      key(keyNames[index], 1, False)
    for index in range(len(keyNames) - len(drumkeyNames)):
      key(keyNames[index], 0, True)
      key(keyNames[index], 1, True)

  #----------------------------------------------------------

  # glorandwarf: sets the key mapping and checks for a conflict
  # restores the old mapping if a conflict occurred
  def setNewKeyMapping(self, section, option, key):
    oldKey = Config.get(section, option)
    Config.set(section, option, key)
    if self.isKeyMappingOK() == False:
    
      if self.keyCheckerMode == 2:   #enforce no conflicts!
        Config.set(section, option, oldKey)
      return False
    return True
      
  #----------------------------------------------------------

class Player(object):
  def __init__(self, owner, name, number):
    Log.debug("Player class init (Player.py)...")
    self.owner    = owner
    self.controls = Controls()
    self.reset()
    self.playerstring = "player" + str(number)
    self.whichPart = Config.get(self.playerstring, "part")
    
    self.bassGrooveEnableMode = Config.get("game", "bass_groove_enable")
    self.currentTheme = 1
    
    #MFH - need to store selected practice mode and start position here
    self.practiceMode = False
    self.practiceSection = None
    self.startPos = 0.0
    
    
  def reset(self):
    self.score         = 0
    self._streak       = 0
    self.notesHit      = 0
    self.longestStreak = 0
    self.cheating      = False
    self.twoChord      = 0
    
  def getName(self):
    return Config.get(self.playerstring, "name")
    
  def setName(self, name):
    Config.set(self.playerstring, "name", name)
    
  name = property(getName, setName)
  
  def getStreak(self):
    return self._streak
    
  def setStreak(self, value):
    self._streak = value
    self.longestStreak = max(self._streak, self.longestStreak)
    
  streak = property(getStreak, setStreak)
    
  def getDifficulty(self):
    return Song.difficulties.get(Config.get(self.playerstring, "difficulty"))
    
  def setDifficulty(self, difficulty):
    Config.set(self.playerstring, "difficulty", difficulty.id)

  def getPart(self):
    #myfingershurt: this should not be reading from the ini file each time it wants to know the part.  Also add "self."
    #part = Config.get(self.playerstring, "part")
    if self.whichPart == -1:
      return "Party Mode"
    elif self.whichPart == -2:
      return "No Player 2"
    else:
      return Song.parts.get(self.whichPart)
    
  def setPart(self, part):
    if part == "Party Mode":
      Config.set(self.playerstring, "part", -1)
      self.whichPart = -1    #myfingershurt: also need to set self.part here to avoid unnecessary ini reads
    elif part == "No Player 2":
      Config.set(self.playerstring, "part", -2)
      self.whichPart = -2    #myfingershurt: also need to set self.part here to avoid unnecessary ini reads
    else:
      Config.set(self.playerstring, "part", part.id)    
      self.whichPart = part.id    #myfingershurt: also need to set self.part here to avoid unnecessary ini reads
    
  difficulty = property(getDifficulty, setDifficulty)
  part = property(getPart, setPart)
  
  def addScore(self, score):
    self.score += score * self.getScoreMultiplier()
    
  def getScoreMultiplier(self):
    
    #if self.getPart() == "Bass Guitar":    #myfingershurt: bass groove
    if self.part.text == "Bass Guitar" and (self.bassGrooveEnableMode == 2 or (self.currentTheme == 2 and self.bassGrooveEnableMode == 1) ):    #myfingershurt: bass groove
      try:
        return BASS_GROOVE_SCORE_MULTIPLIER.index((self.streak / 10) * 10) + 1
      except ValueError:
        return len(BASS_GROOVE_SCORE_MULTIPLIER)
    else:
      try:
        return SCORE_MULTIPLIER.index((self.streak / 10) * 10) + 1
      except ValueError:
        return len(SCORE_MULTIPLIER)
