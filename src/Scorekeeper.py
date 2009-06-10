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
#               2009 akedrou                                        #
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

import os
from Language import _
import Song
import Log
import Config

HANDICAPS = [.75, 1.0, .8, .9, .75, .8, 1.05, 1.1, 1.03, 1.02, 1.01, .95, .9, .85, .7, .95, 0.0, .5, .7, .7]
HANDICAP_NAMES = [_("Auto Kick Bass"), _("Medium Assist Mode"), _("Easy Assist Mode"), _("Jurgen Played!"), \
                  _("Effects Saved SP"), _("All Tapping"), _("HOPO Frequency: Most"), _("HOPO Frequency: Even More"), \
                  _("HOPO Frequency: More"), _("HOPO Frequency: Less"), _("HOPO Frequency: Least"), _("HOPO Disabled!"), \
                  _("Hit Window: Tightest!"), _("Hit Window: Tight!"), _("Hit Window: Wider"), _("Hit Window: Widest"), \
                  _("Two Note Chords"), _("No Fail Mode"), "Scalable Cheat", _("Sloppy Mode!")]
SCALABLE_NAMES = [_("Song Slowdown"), _("Early Hit Window Adjustment")]
SCORE_MULTIPLIER = [0, 10, 20, 30]
BASS_GROOVE_SCORE_MULTIPLIER = [0, 10, 20, 30, 40, 50]

class ScoreCard(object):
  def __init__(self, instrument, coOpType = False):
    self.coOpType = coOpType
    logClassInits = Config.get("game", "log_class_inits")
    if logClassInits == 1:
      Log.debug("ScoreCard class init...")
    self.starScoring = Config.get("game", "star_scoring")
    self.updateOnScore = Config.get("game", "star_score_updates")
    self.avMult = 0.0
    self.hitAccuracy = 0.0
    self.score  = 0
    if instrument == [5]:
      self.baseScore = 200
    else:
      self.baseScore = 50
    self.notesHit = 0
    self.notesMissed = 0
    self.instrument = instrument # 0 = Guitar, 2 = Bass, 4 = Drum
    self.bassGrooveEnabled = False
    self.hiStreak = 0
    self._streak  = 0
    self.cheats = []
    self.scalable = []
    self.earlyHitWindowSizeHandicap = 1.0
    self.handicap = 0
    self.longHandicap  = ""
    self.handicapValue = 100.0
    self.totalStreakNotes = 0
    self.totalNotes = 0
    self.cheatsApply = False
    self.stars = 0
    self.partialStars = 0
    self.starRatio = 0.0
    self.star = [0 for i in range(7)]
    if self.starScoring == 1: #GH-style (mult thresholds, hit threshold for 5/6 stars)
      self.star[5] = 2.8
      self.star[4] = 2.0
      self.star[3] = 1.2
      self.star[2] = 0.4
      self.star[1] = 0.2 #akedrou - GH may start with 1 star, but why do we need to?
      self.star[0] = 0.0
    elif self.starScoring > 1: #RB-style (mult thresholds, optional 100% gold star)
      if self.starScoring == 4:
        if self.instrument[0] == Song.BASS_PART and not self.coOpType:
          self.star[6] = 6.78
          self.star[5] = 4.62
          self.star[4] = 2.77
          self.star[3] = 0.90
          self.star[2] = 0.50
          self.star[1] = 0.46
          self.star[0] = 0.0
        else:
          if self.instrument[0] == Song.DRUM_PART and not self.coOpType:
            self.star[6] = 4.29
          else:
            self.star[6] = 4.52
          self.star[5] = 3.08
          self.star[4] = 1.85
          self.star[3] = 0.77
          self.star[2] = 0.46
          self.star[1] = 0.21
          self.star[0] = 0.0
      else:
        self.star[5] = 3.0
        self.star[4] = 2.0
        self.star[3] = 1.0
        self.star[2] = 0.5
        self.star[1] = 0.25
        self.star[0] = 0.0
        if self.coOpType:
          self.star[6] = 4.8
        elif self.instrument[0] == Song.BASS_PART: # bass
          self.star[6] = 4.8
        elif self.instrument[0] == Song.DRUM_PART: # drum
          self.star[6] = 4.65
        else:
          self.star[6] = 5.3
    else: #hit accuracy thresholds
      self.star[6] = 100
      self.star[5] = 95
      self.star[4] = 75
      self.star[3] = 50
      self.star[2] = 30
      self.star[1] = 10
      self.star[0] = 0
    
    self.endingScore = 0    #MFH
    self.endingStreakBroken = False   #MFH
    self.endingAwarded = False    #MFH
    self.lastNoteEvent = None    #MFH
    self.lastNoteTime  = 0.0
    self.freestyleWasJustActive = False  #MFH

  
  def reset(self):
    self.avMult = 0.0
    self.hitAccuracy = 0.0
    self.score  = 0
    self.notesHit = 0
    self.notesMissed = 0
    self.hiStreak = 0
    self._streak = 0
    self.cheats = []
    self.handicap = 0
    self.longHandicap  = ""
    self.handicapValue = 100.0
    self.cheatsApply = False
    self.stars = 0
    self.partialStars = 0
    self.starRatio = 0.0
    self.endingScore = 0    #MFH
    self.endingStreakBroken = False   #MFH
    self.endingAwarded = False    #MFH
    self.freestyleWasJustActive = False  #MFH

  def getStarScores(self, tempExtraScore = 0):
    oldStar = self.stars
    if self.updateOnScore == 1:
      avMult = float(self.score+tempExtraScore) / float(self.totalNotes * self.baseScore)
    else:
      avMult = self.avMult
    if self.starScoring == 1: #GH-style
      if self.hitAccuracy == 100.0 and self.hiStreak == self.totalStreakNotes and not self.cheatsApply:
        self.stars = 7
        self.partialStars = 0
        self.starRatio = 0
        return 7
      if self.hitAccuracy == 100.0 and not self.cheatsApply:
        self.stars = 6
        self.partialStars = 0
        self.starRatio = 0
        return 6
      elif (self.hitAccuracy >= 90.0 and not self.cheatsApply) or avMult >= self.star[5]:
        self.stars = 5
        self.partialStars = 0
        self.starRatio = 0
        return 5
      else:
        for i in range(4, -1, -1):
          if avMult >= self.star[i]:
            part = avMult - self.star[i]
            partPct = part / (self.star[i+1] - self.star[i])
            partStar = int(8*partPct)
            partStar = min(partStar, 7) #catches 99.very9%, just in case
            self.stars = i
            self.partialStars = partStar
            self.starRatio = partPct
            return i
    elif self.starScoring >= 2: #RB-style and RB+GH (and RB2)
      hundredGold = True
      if self.starScoring == 2: 
        hundredGold = False
      if hundredGold and self.hitAccuracy == 1.0 and self.hiStreak == self.totalStreakNotes and not self.cheatsApply:
        self.stars = 7
        self.partialStars = 0
        self.starRatio = 0
        return 7
      if (self.hitAccuracy == 1.0 and hundredGold) or avMult > self.star[6]:
        self.stars = 6
        self.partialStars = 0
        self.starRatio = 0
        return 6
      elif avMult >= self.star[5]:
        self.stars = 5
        self.partialStars = 0
        self.starRatio = 0
        return 5
      else:
        for i in range(4, -1, -1):
          if avMult >= self.star[i]:
            part = avMult - self.star[i]
            partPct = part / (self.star[i+1] - self.star[i])
            partStar = int(8*partPct)
            partStar = min(partStar, 7) #catches 99.very9%, just in case
            self.stars = i
            self.partialStars = partStar
            self.starRatio = partPct
            return i
    else: #FoF
      if self.hitAccuracy == 1.0 and self.hiStreak == self.totalStreakNotes and not self.cheatsApply:
        self.stars = 7
        self.partialStars = 0
        self.starRatio = 0
        return 7
      if self.hitAccuracy == self.star[6]:
        self.stars = 6
        self.partialStars = 0
        self.starRatio = 0
        return 6
      elif self.hitAccuracy >= self.star[5]:
        self.stars = 5
        self.partialStars = 0
        self.starRatio = 0
        return 5
      else:
        for i in range(4, -1, -1):
          if self.hitAccuracy >= self.star[i]:
            part = self.hitAccuracy - self.star[i]
            partPct = part / (self.star[i+1] - self.star[i])
            partStar = int(8*partPct)
            partStar = min(partStar, 7) #catches 99.very9%, just in case
            self.stars = i
            self.partialStars = partStar
            self.starRatio = partPct
            return i

  def updateAvMult(self):
    try:
      self.hitAccuracy = (float(self.notesHit) / float(self.totalStreakNotes) ) * 100.0
    except ZeroDivisionError:
      self.hitAccuracy = 0.0
    try:
      self.avMult      = self.score/float(self.totalNotes*self.baseScore)
    except ZeroDivisionError:
      self.avMult      = 1.0
  
  def updateHandicapValue(self):
    self.handicapValue = 100.0
    slowdown = Config.get("audio","speed_factor")
    earlyHitHandicap      = 1.0 #self.earlyHitWindowSizeHandicap #akedrou - replace when implementing handicap.
    for j in range(len(HANDICAPS)):
      if (self.handicap>>j)&1 == 1:
        if j == 1: #scalable
          if slowdown != 1:
            if slowdown < 1:
              cut = (100.0**slowdown)/100.0
            else:
              cut = (100.0*slowdown)/100.0
            self.handicapValue *= cut
          if earlyHitHandicap != 1.0:
            self.handicapValue *= earlyHitHandicap
        else:
          self.handicapValue *= HANDICAPS[j]
  
  def getStreak(self):
    return self._streak
    
  def setStreak(self, value):
    self._streak = value
    self.hiStreak = max(self._streak, self.hiStreak)
  
  streak = property(getStreak, setStreak)
  
  def addScore(self, score):
    self.score += score * self.getScoreMultiplier()

  def addEndingScore(self):
    self.score += self.endingScore

  def getScoreMultiplier(self):
    if self.instrument == [Song.BASS_PART] and self.bassGrooveEnabled:    #myfingershurt: bass groove
      try:
        return BASS_GROOVE_SCORE_MULTIPLIER.index((self.streak / 10) * 10) + 1
      except ValueError:
        return len(BASS_GROOVE_SCORE_MULTIPLIER)
    elif self.instrument == [Song.VOCAL_PART]:
      return min(self.streak + 1, 4)
    else:
      try:
        return SCORE_MULTIPLIER.index((self.streak / 10) * 10) + 1
      except ValueError:
        return len(SCORE_MULTIPLIER)

class Rockmeter:
  pass # future breaking out of rockmeter can likely go here. Scorekeeper seems fitting.

