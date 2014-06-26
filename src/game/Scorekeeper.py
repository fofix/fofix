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

from core.Language import _
from game import Song
from util import Log
from configuration import Config
from datetime import datetime

HANDICAPS = [.75, 1.0, .8, .9, .75, .8, 1.05, 1.1, 1.03, 1.02, 1.01, .95, .9, .85, .7, .95, 0.0, .5, .7, .7]
HANDICAP_NAMES = [_("Auto Kick Bass"), _("Medium Assist Mode"), _("Easy Assist Mode"), _("Jurgen Played!"), \
                  _("Effects Saved SP"), _("All Tapping"), _("HOPO Frequency: Most"), _("HOPO Frequency: Even More"), \
                  _("HOPO Frequency: More"), _("HOPO Frequency: Less"), _("HOPO Frequency: Least"), _("HOPO Disabled!"), \
                  _("Hit Window: Tightest!"), _("Hit Window: Tight!"), _("Hit Window: Wider"), _("Hit Window: Widest"), \
                  _("Two Note Chords"), _("No Fail Mode"), "Scalable Cheat", _("Sloppy Mode!")]
SCALABLE_NAMES = [_("Song Slowdown"), _("Early Hit Window Adjustment")]
SCORE_MULTIPLIER = [0, 10, 20, 30]
BASS_GROOVE_SCORE_MULTIPLIER = [0, 10, 20, 30, 40, 50]

#like Guitar Hero
GH_STAR_VALUES = [0.0, 0.2, 0.4, 1.2, 2.0, 2.8]
        
#like Rockband
RB_STAR_VALUES = [0.0, 0.21, 0.46, 0.77, 1.85, 3.08, 4.52]
RB_BASS_STAR_VALUES = [0.0, 0.21, 0.5, 0.9, 2.77, 4.62, 6.78]
RB_DRUM_STAR_VALUES = [0.0, 0.21, 0.46, 0.77, 1.85, 3.08, 4.29]
RB_VOC_STAR_VALUES = [0.0, 0.21, 0.46, 0.77, 1.85, 3.08, 4.18]
                    
#RB+GH mix
MIX_STAR_VALUES = [0.0, 0.25, 0.5, 1.0, 2.0, 3.0, 5.3]
MIX_BASS_STAR_VALUES = [0.0, 0.25, 0.5, 1.0, 2.0, 3.0, 4.8]
MIX_DRUM_STAR_VALUES = [0.0, 0.25, 0.5, 1.0, 2.0, 3.0, 4.65]
MIX_COOP_STAR_VALUES = [0.0, 0.25, 0.5, 1.0, 2.0, 3.0, 4.8]

#accuracy-based
FOF_STAR_VALUES = [0, 10, 30, 50, 75, 95, 100]

class ScoreCard(object):
    def __init__(self, instrument, coOpType = False):
        self.coOpType = coOpType            #does the score card belong to a CoOp system
        self.instrument = instrument        # 0 = Guitar, 2 = Bass, 4 = Drum
        self.bassGrooveEnabled = False      #is the player in bass groove
        
        logClassInits = Config.get("game", "log_class_inits")
        if logClassInits == 1:
            Log.debug("ScoreCard class init...")
            
                                                                                
        self.avMult = 0.0                   #vocal multiplier percentage 
        self.hitAccuracy = 0.0              #accuracy rating/delay
        self.score  = 0                     #player's score
        
        #lowest amount the player can earn per not hit
        if instrument == [5]:
            self.baseScore = 0
        else:
            self.baseScore = 50
            
        self.notesHit = 0                   #number of notes hit
        self.percNotesHit = 0               #percentage of total notes hit
        self.notesMissed = 0                #number of notes missed
        self.hiStreak = 0                   #highest streak done by the player
        self.streak  = 0                    #current streak
        
        self.totalStreakNotes = 0
        self.totalNotes = 0
        self.totalPercNotes = 0
        
        #cheating/handicap system
        self.cheatsApply = False
        self.cheats = []                    
        self.scalable = []
        self.earlyHitWindowSizeHandicap = 1.0
        self.handicap = 0
        self.longHandicap  = ""
        self.handicapValue = 100.0
        
        #star scoring
        self.starScoring = Config.get("game", "star_scoring")
                                            #star scoring type
        self.updateOnScore = True           #star's update during play
        self.stars = 0                      #current number of stars
        self.starRatio = 0.0                #percentage of how close the player is to the next star
        self.star = [0 for i in range(7)]   #keep track of values required to know when the player has hit the next star value
        
        #figure out which star setting to use
        s = ""
        if self.starScoring == 1: #GH-style (mult thresholds, hit threshold for 5/6 stars)
            s += "GH"
        elif self.starScoring > 1: #RB-style (mult thresholds, optional 100% gold star)
            if self.starScoring == 4:
                s += "RB"
            else:
                s += "MIX"
                
            if self.coOpType:
                s += "_COOP"
            elif self.instrument[0] == Song.DRUM_PART:
                s += "_DRUM"
            elif self.instrument[0] == Song.VOCAL_PART:
                s += "_VOC"
            elif self.instrument[0] == Song.BASS_PART:
                s += "_BASS"
        else: #hit accuracy thresholds
            s += "FOF"
        s += "_STAR_VALUES"
        
        self.star = globals()[s]
        
        self.endingScore = 0
        self.endingStreakBroken = False
        self.endingAwarded = False          
        self.lastNoteEvent = None
        self.lastNoteTime  = 0.0
        self.freestyleWasJustActive = False

    #resets all the values 
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
        self.starRatio = 0.0
        self.endingScore = 0
        self.endingStreakBroken = False
        self.endingAwarded = False
        self.freestyleWasJustActive = False

    def getStarScores(self, tempExtraScore = 0):
        try:
            if self.updateOnScore == 1 and self.instrument[0] != Song.VOCAL_PART:
                avMult = float(self.score+tempExtraScore) / float(self.totalNotes * self.baseScore)
            else:
                avMult = self.avMult
        except ZeroDivisionError:
                avMult = self.avMult
        if self.starScoring == 1: #GH-style
            if self.hitAccuracy == 100.0 and self.hiStreak == self.totalStreakNotes and not self.cheatsApply:
                self.stars = 7
                self.starRatio = 0
                return 7
            if self.hitAccuracy == 100.0 and not self.cheatsApply:
                self.stars = 6
                self.starRatio = 0
                return 6
            elif (self.hitAccuracy >= 90.0 and not self.cheatsApply) or avMult >= self.star[5]:
                self.stars = 5
                self.starRatio = 0
                return 5
        elif self.starScoring >= 2: #RB-style and RB+GH (and RB2)
            hundredGold = True
            if self.starScoring == 2: 
                hundredGold = False
            if hundredGold and self.hitAccuracy == 1.0 and self.hiStreak == self.totalStreakNotes and not self.cheatsApply:
                self.stars = 7
                self.starRatio = 0
                return 7
            if (self.hitAccuracy == 1.0 and hundredGold) or avMult > self.star[6]:
                self.stars = 6
                self.starRatio = 0
                return 6
            elif avMult >= self.star[5]:
                self.stars = 5
                self.starRatio = 0
                return 5
        else: #FoF
            if self.hitAccuracy == 1.0 and self.hiStreak == self.totalStreakNotes and not self.cheatsApply:
                self.stars = 7
                self.starRatio = 0
                return 7
            if self.hitAccuracy == self.star[6]:
                self.stars = 6
                self.starRatio = 0
                return 6
            elif self.hitAccuracy >= self.star[5]:
                self.stars = 5
                self.starRatio = 0
                return 5
        
        for i in range(4, -1, -1):
            if avMult >= self.star[i]:
                part = avMult - self.star[i]
                partPct = part / (self.star[i+1] - self.star[i])
                self.stars = i
                self.starRatio = partPct
                return i
        
    def updateAvMult(self):
        try:
            self.hitAccuracy = (float(self.notesHit) / float(self.totalStreakNotes) ) * 100.0
        except ZeroDivisionError:
            self.hitAccuracy = 0.0
        try:
            if self.instrument[0] == Song.VOCAL_PART and not self.coOpType:
                self.avMult = float(self.score)/float(self.baseScore)
            else:
                self.avMult = self.score/float(self.totalNotes*self.baseScore)
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


#some constants for the rock scoring
_rockMax = 30000.0
_rockMin = 0
_rockHi = _rockMax/3.0*2.0
_rockLo = _rockMax/3.0
_multHi = 4
_multBassHi = 6
_minBase = 400.0
_minMax = 900.0
_pluBase = 15
_pluMax = 750.0
_minGain = 2
_pluGain = 7

#handles the scoring of the rockmeter
class RockmeterScoring(object):
    def __init__(self, player):
        self.rock = _rockMax/2.0        #amount of rock the player has
        self.mult = 1
        self.percentage = .5
        self.failing = False            #is the player failing
        self.inGreen = False            #is the player in the top percentile
        self.timesFailed = 0            #number of times failed (only useful in coOp)
        self.minusRock = _minBase       #amount of rock to subtract when decreasing
        self.plusRock = _pluBase        #amount of rock to add when increasing
        self.player = player
        self.instrument = player.instrument
        
    #starts the process
    def start(self):
        self.rock = _rockMax/2.0
        self.failing = False
        self.inGreen = False
        self.mult = 1
        self.timesFailed = 0
        self.percentage = .5
        self.minusRock = _minBase
        self.plusRock = _pluBase
            
    #increases the player's rock
    def increaseRock(self, vScore = 0):
        
        if self.instrument.isVocal:
            rockPlusAmt = 500 + (500 * (vScore-2))
            self.rock += rockPlusAmt
            return
            
        if self.instrument.isDrum: 
            self.drumStart = True
    
        self.plusRock = min(self.plusRock + _pluGain*self.mult, _pluMax)
        self.rock += self.plusRock
                    
        self.minusRock = _minBase
        
    #decreases the rock of the player
    #if they have a lot of missed notes it should take off more
    def decreaseRock(self, more = False, less = False, vScore = 0):
        rockMinusAmount = 0

        if self.instrument.isVocal:
            rockMinusAmount = 500 * (3 - vScore)
            self.rock -= rockMinusAmount
            return
            
        if more:
            self.minusRock += _minGain/self.mult
            rockMinusAmount = self.minusRock/self.mult
            self.rock -= rockMinusAmount
        if less:
            self.minusRock += _minGain/5.0/self.mult
            rockMinusAmount = self.minusRock/5.0/self.mult
            self.rock -= rockMinusAmount

        self.plusRock = _pluBase 

    #revives the player after failing in coOp mode
    def coOpRescue(self):
        self.start()          #resets the rockmeter for the player
        self.rock = _rockHi   #gives them a little boost

    def run(self):
        #locks the rockmeter so you can't go above/below the boundary values
        self.rock = min(max(self.rock, _rockMin), _rockMax)
        
        self.inGreen = self.rock > _rockHi
        self.failing = self.rock < _rockLo
        self.failed = self.rock <= _rockMin
        self.percentage = self.rock/_rockMax
        
        multMax = _multHi
        if self.instrument.isBassGuitar:
            multMax = _multBassHi

        
        #starpower mult boost
        self.mult = self.player.scoreCard.getScoreMultiplier()
        if self.instrument.starPowerActive:
            self.mult *= 2
        
        
_drainRate = 500000    #amount of microseconds that need to pass before it drains rock again

#Different rockmeter for keeping track of coOp modes
class CoOpRockmeterScoring(RockmeterScoring):
    def __init__(self, players, coOp = None):
        self.rock = _rockMax/2.0        #amount of rock the player has
        self.mult = 1
        self.percentage = .5
        self.failing = 0                #players failing
        self.failed = False             #has it failed all together      
        self.deadList = []              #players who have failed
        self.numDead = 0                #number of players who have failed
        self.inGreen = 0                #players in green failing
        self.coOp = coOp                #co-op type
        self.minusRock = _minBase       #amount of rock to subtract when decreasing
        self.plusRock = _pluBase        #amount of rock to add when increasing
        self.players = players
        self.drainTime = 0              #time in microseconds recorded to know when to 
                                        # drain from the rockmeter again
        
    #starts the process
    def start(self):
        self.rock = _rockMax/2.0
        self.failing = False
        self.inGreen = False
        self.mult = 1
        self.percentage = .5
        self.minusRock = _minBase
        self.plusRock = _pluBase
            
    #increases the player's rock
    def increaseRock(self, vScore = 0):
    
        self.plusRock = min(self.plusRock + _pluGain*self.mult, _pluMax)
        self.rock += self.plusRock
                    
        self.minusRock = _minBase
        
    #decreases the rock of the player
    #if they have a lot of missed notes it should take off more
    def decreaseRock(self, more = False, less = False, vScore = 0):
        rockMinusAmount = 0
            
        if more:
            self.minusRock += _minGain/self.mult
            rockMinusAmount = self.minusRock/self.mult
            self.rock -= rockMinusAmount
        if less:
            self.minusRock += _minGain/5.0/self.mult
            rockMinusAmount = self.minusRock/5.0/self.mult
            self.rock -= rockMinusAmount

        self.plusRock = _pluBase 
        
    def drain(self):
        self.minusRock += _minGain/10.0/self.mult
        self.rock -= self.minusRock
                    
    def run(self):
        self.rock = min(max(self.rock, _rockMin), _rockMax)
        self.percentage = self.rock/_rockMax
        self.numDead = len(self.deadList)
        
        self.failed = self.rock <= _rockMin
                
        self.mult = 1
        self.failing = self.rock <= _rockLo

        if self.numDead > 0:
            dt = datetime.now().microsecond % _drainRate
            if dt < self.drainTime:
                self.drain()
            self.drainTime = dt
        elif not self.coOp == "RB":
            self.rock = 0
            for player in self.players:
                self.rock += player.rockCard.rock
            self.rock /= len(self.players)
            self.rock *= 3.0/2.0
            
        for player in self.players:
            if player.instrument.starPowerActive:
                self.mult *= 2
            if player.rockCard.failed:
                if not player in self.deadList:
                    self.deadList.append(player)
        
