#!/usr/bin/env python
# -*- coding: utf-8 -*-

#####################################################################
# Frets on Fire                                                     #
# Copyright (C) 2006 Sami Kyöstilä                                  #
#               2008 myfingershurt                                  #
#               2009 Pascal Giard                                   #
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


# Song difficulties
EXP_DIF     = 0
HAR_DIF     = 1
MED_DIF     = 2
EAS_DIF     = 3

# MIDI note value constants
EXP_GEM_0 = 0x60
EXP_GEM_1 = 0x61
EXP_GEM_2 = 0x62
EXP_GEM_3 = 0x63
EXP_GEM_4 = 0x64

HAR_GEM_0 = 0x54
HAR_GEM_1 = 0x55
HAR_GEM_2 = 0x56
HAR_GEM_3 = 0x57
HAR_GEM_4 = 0x58

MED_GEM_0 = 0x48
MED_GEM_1 = 0x49
MED_GEM_2 = 0x4a
MED_GEM_3 = 0x4b
MED_GEM_4 = 0x4c

EAS_GEM_0 = 0x3c
EAS_GEM_1 = 0x3d
EAS_GEM_2 = 0x3e
EAS_GEM_3 = 0x3f
EAS_GEM_4 = 0x40

#
# One MIDI track is divided into four 'zones' representing the four difficulty
# levels.  This dict maps the MIDI notes to difficulty/button pairs.  The
# specific notes listed above must be used to indicate which button should be
# pressed.
#
NOTE_MAP = {     # difficulty, note
  EXP_GEM_0: (EXP_DIF, 0), #======== #0x60 = 96 = C 8
  EXP_GEM_1: (EXP_DIF, 1),           #0x61 = 97 = Db8
  EXP_GEM_2: (EXP_DIF, 2),           #0x62 = 98 = D 8
  EXP_GEM_3: (EXP_DIF, 3),           #0x63 = 99 = Eb8
  EXP_GEM_4: (EXP_DIF, 4),           #0x64 = 100= E 8

  HAR_GEM_0: (HAR_DIF, 0), #======== #0x54 = 84 = C 7
  HAR_GEM_1: (HAR_DIF, 1),           #0x55 = 85 = Db7
  HAR_GEM_2: (HAR_DIF, 2),           #0x56 = 86 = D 7
  HAR_GEM_3: (HAR_DIF, 3),           #0x57 = 87 = Eb7
  HAR_GEM_4: (HAR_DIF, 4),           #0x58 = 88 = E 7

  MED_GEM_0: (MED_DIF, 0), #======== #0x48 = 72 = C 6
  MED_GEM_1: (MED_DIF, 1),           #0x49 = 73 = Db6
  MED_GEM_2: (MED_DIF, 2),           #0x4a = 74 = D 6
  MED_GEM_3: (MED_DIF, 3),           #0x4b = 75 = Eb6
  MED_GEM_4: (MED_DIF, 4),           #0x4c = 76 = E 6

  EAS_GEM_0: (EAS_DIF, 0), #======== #0x3c = 60 = C 5
  EAS_GEM_1: (EAS_DIF, 1),           #0x3d = 61 = Db5
  EAS_GEM_2: (EAS_DIF, 2),           #0x3e = 62 = D 5
  EAS_GEM_3: (EAS_DIF, 3),           #0x3f = 63 = Eb5
  EAS_GEM_4: (EAS_DIF, 4),           #0x40 = 64 = E 5
}

# Real / Pro Guitar midi markers
EXP_REAL_GTR_E2 = 0x60
EXP_REAL_GTR_A2 = 0x61
EXP_REAL_GTR_D3 = 0x62
EXP_REAL_GTR_G3 = 0x63
EXP_REAL_GTR_B3 = 0x64
EXP_REAL_GTR_E4 = 0x65

HAR_REAL_GTR_E2 = 0x48
HAR_REAL_GTR_A2 = 0x49
HAR_REAL_GTR_D3 = 0x4a
HAR_REAL_GTR_G3 = 0x4b
HAR_REAL_GTR_B3 = 0x4c
HAR_REAL_GTR_E4 = 0x4d

MED_REAL_GTR_E2 = 0x30
MED_REAL_GTR_A2 = 0x31
MED_REAL_GTR_D3 = 0x32
MED_REAL_GTR_G3 = 0x33
MED_REAL_GTR_B3 = 0x34
MED_REAL_GTR_E4 = 0x35

EAS_REAL_GTR_E2 = 0x18
EAS_REAL_GTR_A2 = 0x19
EAS_REAL_GTR_D3 = 0x1a
EAS_REAL_GTR_G3 = 0x1b
EAS_REAL_GTR_B3 = 0x1c
EAS_REAL_GTR_E4 = 0x1d

#
# As above for NOTE_MAP, but for the "real" guitar (whatever that is.)
#
REAL_GTR_NOTE_MAP = {                # difficulty, note
  EXP_REAL_GTR_E2: (EXP_DIF, 0),
  EXP_REAL_GTR_A2: (EXP_DIF, 1), 
  EXP_REAL_GTR_D3: (EXP_DIF, 2),
  EXP_REAL_GTR_G3: (EXP_DIF, 3),
  EXP_REAL_GTR_B3: (EXP_DIF, 4),
  EXP_REAL_GTR_E4: (EXP_DIF, 5),

  HAR_REAL_GTR_E2: (HAR_DIF, 0),
  HAR_REAL_GTR_A2: (HAR_DIF, 1),
  HAR_REAL_GTR_D3: (HAR_DIF, 2),
  HAR_REAL_GTR_G3: (HAR_DIF, 3),
  HAR_REAL_GTR_B3: (HAR_DIF, 4),
  HAR_REAL_GTR_E4: (HAR_DIF, 5),

  MED_REAL_GTR_E2: (MED_DIF, 0),
  MED_REAL_GTR_A2: (MED_DIF, 1),
  MED_REAL_GTR_D3: (MED_DIF, 2),
  MED_REAL_GTR_G3: (MED_DIF, 3),
  MED_REAL_GTR_B3: (MED_DIF, 4),
  MED_REAL_GTR_E4: (MED_DIF, 5),

  EAS_REAL_GTR_E2: (EAS_DIF, 0),
  EAS_REAL_GTR_A2: (EAS_DIF, 1),
  EAS_REAL_GTR_D3: (EAS_DIF, 2),
  EAS_REAL_GTR_G3: (EAS_DIF, 3),
  EAS_REAL_GTR_B3: (EAS_DIF, 4),
  EAS_REAL_GTR_E4: (EAS_DIF, 5),
}


# -- special note numbers -- #
# Star Power
SP_MARKING_NOTE = 0x67     #note 103 = G 8
# Overdrive
OD_MARKING_NOTE = 0x74     #note 116 = G#9
# Hammer-On / Pull-Off
HOPO_MARKING_NOTES = []
PRO_HOPO_MARKING_NOTES = [0x1e, 0x36, 0x4e, 0x66]
# Free Style
FREESTYLE_MARKING_NOTE = 0x7c      #notes 120 - 124 = drum fills & BREs - always all 5 notes present



DEFAULT_BPM = 120.0
DEFAULT_LIBRARY = "songs"

# special / global text-event tracks for the separated text-event list variable
TK_SCRIPT = 0         #script.txt events
TK_SECTIONS = 1       #Section events
TK_GUITAR_SOLOS = 2   #Guitar Solo start/stop events
TK_LYRICS = 3         #RB MIDI Lyric events
TK_UNUSED_TEXT = 4    #Unused / other text events

GUITAR_TRACK            = 0
RHYTHM_TRACK            = 1
DRUM_TRACK              = 2
VOCAL_TRACK             = 3

MIDI_TYPE_GH            = 0       #GH type MIDIs have starpower phrases marked with a long G8 note on that instrument's track
MIDI_TYPE_RB            = 1       #RB type MIDIs have overdrive phrases marked with a long G#9 note on that instrument's track
MIDI_TYPE_WT            = 2       #WT type MIDIs have six notes and HOPOs marked on F# of the track

EARLY_HIT_WINDOW_NONE   = 1       #GH1/RB1/RB2 = NONE
EARLY_HIT_WINDOW_HALF   = 2       #GH2/GH3/GHA/GH80's = HALF
EARLY_HIT_WINDOW_FULL   = 3       #FoF = FULL

GUITAR_PART             = 0
RHYTHM_PART             = 1
BASS_PART               = 2
LEAD_PART               = 3
DRUM_PART               = 4
VOCAL_PART              = 5
KEYS_PART               = 6
PRO_GUITAR_PART         = 7
PRO_BASS_PART           = 8
PRO_DRUM_PART           = 9
PRO_KEYS_PART           = 10
