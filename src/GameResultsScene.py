#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire                                                     #
# Copyright (C) 2006 Sami Kyöstilä                                  #
#               2008 Alarian                                        #
#               2008 myfingershurt                                  #
#               2008 Glorandwarf                                    #
#               2008 ShiekOdaSandz                                  #
#               2008 Blazingamer                                    #
#               2008 evilynux <evilynux@gmail.com>                  #
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

from Scene import Scene, SuppressScene
import Scorekeeper
import Dialogs
import Song
import Data
from Menu import Menu
from Audio import Sound
from Language import _

import hashlib
import Cerealizer
import binascii
import urllib
import Log

import pygame
import random
import os
from OpenGL.GL import *

class GameResultsScene(Scene):
  def __init__(self, engine, libraryName, songName, scores = None, coOpType = False, careerMode = False):
    Scene.__init__(self, engine)
    
    if self.engine.world.sceneName == "GameResultsScene":  #MFH - dual / triple loading cycle fix
      Log.warn("Extra GameResultsScene was instantiated, but detected and shut down.  Cause unknown.")
      raise SuppressScene  #stump
    else:
      self.engine.world.sceneName = "GameResultsScene"
    
    self.logClassInits = self.engine.config.get("game", "log_class_inits")
    if self.logClassInits == 1:
      Log.debug("GameResultsScene class init...")
    
    players = self.players
    if coOpType > 0:
      self.scoring        = [scores.pop()]
      self.coOpScoring    = scores
    else:
      self.scoring        = scores
      self.coOpScoring    = None
    self.libraryName      = libraryName
    self.cheats           = [[] for i in self.scoring]
    self.numCheats        = [0 for i in self.scoring]
    self.songName         = songName
    self.coOpType         = coOpType
    self.careerMode       = careerMode
    self.counter          = 0
    self.animationTimer   = 0
    self.scoreRollTimer   = [0 for i in self.scoring]
    self.delay            = [0 for i in self.scoring]
    self.waiting          = False
    self.resultStep       = 0
    self.resultSubStep    = [0 for i in self.scoring]
    self.currentCheat     = [0 for i in self.scoring]
    self.finishedCheat    = [-1 for i in self.scoring]
    self.currentScore     = [0 for i in self.scoring]
    self.newScore         = [0 for i in self.scoring]
    self.diffScore        = [0 for i in self.scoring]
    self.totalHandicap    = [100.0 for i in self.scoring]
    self.progressReady    = False
    self.progressToScores = False
    self.rolling          = [False for i in self.scoring]
    self.space            = [1 for i in self.scoring]
    self.finalScore       = [0 for i in self.scoring]
    self.originalScore    = [0 for i in self.scoring]
    self.cheatsApply      = True
    self.skipCheats       = False
    self.showHighscores   = False
    self.singleView       = False
    self.highscoreIndex   = [-1 for i in players]
    self.haveRunScores    = False
    self.doneScores       = False
    self.shownScores      = False
    self.doneCount        = False
    self.noScore          = [False for i in players]
    self.scorePart        = None
    self.scoreDifficulty  = None
    self.taunt            = None
    self.uploadingScores  = [False for i in players]
    self.uploadResponse   = [None for i in players]
    self.uploadResult     = None # holder for response.
    self.resultNum        = 0    # holder for response
    self.hsRollIndex      = 0
    self.offset           = 0.0
    self.pctRoll          = 0.0
    self.vis              = 1.0
    self.pauseScroll      = 0
    self.careerStars      = self.engine.config.get("game", "career_star_min")
    self.detailedScores   = False #to do.
    self.playerList       = self.players
    self.resultStar       = [float(i) for i in self.engine.theme.result_star]
    
    self.scoreScrollStartOffset = .8
    for i in self.playerList:
      i.cache = None
    
    self.coOpDiff    = _("Co-Op Mode") #To be changed to something.
    self.coOpPart    = _("Co-Op Mode") #To be changed to something.
    
    self.tsSettings  = _("settings")
    self.tsHopos     = _("HOPOs")
    self.tsHitWindow = _("Hit Window")
    self.tsHandicap  = _("Adjusted Score Multiplier:")
    self.tsOriginal  = _("Original Score:")
    
    if len(self.engine.world.songQueue) == 0:
      if self.engine.world.playingQueue:
        items = [
        (_("Continue"),       self.changeSong),
        (_("Replay Setlist"), self.replaySetlist),
        #(_("Detailed Stats"), self.stats), #akedrou - to do
        (_("Quit"),           self.quit),
      ]
      else:
        items = [
          (_("Continue"),       self.changeSong),
          (_("Replay"),         self.replay),
          #(_("Detailed Stats"), self.stats), #akedrou - to do
          (_("Quit"),           self.quit),
        ]
    else:
      items = [
        (_("Continue"),       self.changeSong),
        (_("End Setlist"),    self.endSetlist),
        #(_("Detailed Stats"), self.stats), #akedrou - to do
        (_("Quit"),           self.quit),
      ]
    
    self.menu = Menu(self.engine, items, onCancel = self.quit, name = "gameresult", pos = (self.engine.theme.result_menu_x, self.engine.theme.result_menu_y))
    
    #Get theme information
    themename  = self.engine.data.themeLabel
    self.theme = self.engine.data.theme
    
    self.loaded = False
    
    phrase = random.choice(self.engine.theme.resultsPhrase)
    if phrase == "None":
      i = random.randint(0,5)
      if i == 0:
        phrase = _("Relax, it was an excellent show.")
      elif i == 1:
        phrase = _("Truly Amazing!")
      elif i == 2:
        phrase = _("Thanks for playing!")
      elif i == 3:
        phrase = _("One more song can't hurt!")
      elif i == 4:
        phrase = _("What an amazing performance!")
      else:
        phrase = _("That's how it's done!")
    loadingScreen = Dialogs.showLoadingSplashScreen(self.engine, phrase)
    self.engine.resource.load(self, "song", lambda: Song.loadSong(self.engine, songName, library = self.libraryName, notesOnly = True, part = [player.part for player in self.playerList]), onLoad = self.songLoaded, synch = True)

    self.fullView = self.engine.view.geometry[2:4]
    
    self.Congratphrase = self.engine.config.get("game", "congrats")#blazingamer
    self.keepCount     = self.engine.config.get("game", "keep_play_count")
    
    self.showHandicap  = self.engine.config.get("handicap", "detailed_handicap")
    
    self.resultCheerLoop = self.engine.config.get("game", "result_cheer_loop")
    
    self.starScoring = self.engine.config.get("game", "star_scoring")
    self.starMass    = [0 for i in self.scoring]
    self.oldStars    = [0 for i in self.scoring]
    
    self.cheerLoopDelay  = self.engine.theme.crowdLoopDelay
    if self.cheerLoopDelay == None:
      self.cheerLoopDelay = self.engine.config.get("game", "cheer_loop_delay")
    Log.debug("Cheer loop delay used: %d" % self.cheerLoopDelay)
    
    self.cheerLoopCounter = self.cheerLoopDelay
    
    a = self.playerList[0].getPart()
    b = self.playerList[0].getDifficulty()
    for i in range(len(self.playerList)):
      if self.playerList[i].getPart() != a or self.playerList[i].getDifficulty() != b:
        break
    else:
      self.singleView = True
    
    slowdown = self.engine.audioSpeedFactor
    # evilynux - Reset speed
    self.engine.setSpeedFactor(1.0)

    a = len(Scorekeeper.HANDICAPS)
    for i, scoreCard in enumerate(self.scoring):
      scoreCard.updateHandicapValue()
      earlyHitHandicap      = 1.0 #scoreCard.earlyHitWindowSizeHandicap #akedrou - replace when implementing handicap.
      self.finalScore[i]    = int(scoreCard.score * (scoreCard.handicapValue/100.0))
      self.originalScore[i] = scoreCard.score
      self.starMass[i] = 100 * scoreCard.stars
      self.oldStars[i] = scoreCard.stars
      
      for j in range(a):
        if (scoreCard.handicap>>j)&1 == 1:
          if j == 1: #scalable - added to long handicap.
            if slowdown != 1:
              if slowdown < 1:
                cut = (100.0**slowdown)/100.0
              else:
                cut = (100.0*slowdown)/100.0
              self.cheats[i].append((Scorekeeper.SCALABLE_NAMES[0], cut))
              self.starMass[i]   = int(self.starMass[i]   * cut)
              scoreCard.longHandicap += "aud,%.2f;" % slowdown
            if earlyHitHandicap != 1.0:
              self.cheats[i].append((Scorekeeper.SCALABLE_NAMES[1], earlyHitHandicap))
              self.starMass[i]   = int(self.starMass[i]   * earlyHitHandicap)
              scoreCard.longHandicap += "ehw,%.2f;" % earlyHitHandicap
          else:
            self.cheats[i].append((Scorekeeper.HANDICAP_NAMES[(a-1)-j], Scorekeeper.HANDICAPS[j]))
            self.starMass[i]   = int(self.starMass[i]   * Scorekeeper.HANDICAPS[j])
    
    for cheatList in self.cheats:
      if len(cheatList) > 0:
        break
    else:
      self.skipCheats = True
    
    self.hopoStyle = self.engine.config.get("game", "hopo_system")
    gh2sloppy      = self.engine.config.get("game", "gh2_sloppy")
    if gh2sloppy == 1:
      self.hopoStyle = _("GH2 Sloppy")
    elif self.hopoStyle == 0:
      self.hopoStyle = _("None")
    elif self.hopoStyle == 1:
      self.hopoStyle = _("RF-Mod")
    elif self.hopoStyle == 2:
      self.hopoStyle = _("GH2 Strict")
    elif self.hopoStyle == 3:
      self.hopoStyle = _("GH2")
    else:
      self.hopoStyle = _("New System")
    
    self.hopoFreq   = self.engine.config.get("coffee", "hopo_frequency")
    useSongHopoFreq = self.engine.config.get("game", "song_hopo_freq")
    songHopoFreq    = self.playerList[0].hopoFreq
    noteHitWindow   = self.engine.config.get("game", "note_hit_window")
    try:
      songHopoFreq  = abs(int(songHopoFreq))
    except Exception, e:
      songHopoFreq  = 10
    if useSongHopoFreq == 1 and songHopoFreq < 6:
      self.hopoFreq = songHopoFreq
    
    if self.hopoFreq == 0:
      self.hopoFreq = _("Least")
    elif self.hopoFreq == 1:
      self.hopoFreq = _("Less")
    elif self.hopoFreq == 2:
      self.hopoFreq = _("Normal")
    elif self.hopoFreq == 3:
      self.hopoFreq = _("More")
    elif self.hopoFreq == 4:
      self.hopoFreq = _("Even More")
    elif self.hopoFreq == 5:
      self.hopoFreq = _("Most")
    
    if noteHitWindow == 0:
      self.hitWindow = _("Tightest")
    elif noteHitWindow == 1:
      self.hitWindow = _("Tight")
    elif noteHitWindow == 3:
      self.hitWindow = _("Wide")
    elif noteHitWindow == 4:
      self.hitWindow = _("Widest")
    else:
      self.hitWindow = _("Standard")
    
    jurgen   = self.engine.config.get("game", "jurgmode")
    jurgplay = self.engine.config.get("game", "jurgtype")
    
    self.progressKeys   = []
    self.playerProgressKeys = [[] for i in self.playerList]
    for i, player in enumerate(self.playerList):
      self.progressKeys.extend(player.progressKeys)
      self.playerProgressKeys[i] = player.progressKeys
    if jurgen == 0:
      if jurgplay == 1 and len(self.playerList) > 1:
        self.playerProgressKeys[1] = self.progressKeys
      else:
        self.playerProgressKeys = [self.progressKeys for i in self.playerList]
    
    self.part = [None for i in self.playerList]
    self.partImage = True
    if self.coOpType > 0:
      if not self.engine.loadImgDrawing(self, "background", os.path.join("themes", themename, "gameresultscoop.png")):
        self.engine.loadImgDrawing(self, "background", os.path.join("themes", themename, "gameresults.png"))
    else:
      self.engine.loadImgDrawing(self, "background", os.path.join("themes", themename, "gameresults.png"))

    #MFH - moved all star images to Data.py, alter all references accordingly:
    #self.star1 = self.engine.data.star1
    #self.star2 = self.engine.data.star2
    #self.star3 = self.engine.data.star3
    #self.star4 = self.engine.data.star4
    #self.starPerfect = self.engine.data.starPerfect
    #self.starFC = self.engine.data.starFC
    #self.fcStars = self.engine.data.fcStars
    #self.maskStars = self.engine.data.maskStars
    titleFormat = self.engine.theme.result_song_form
    if not titleFormat:
      titleFormat = 0
    self.scaleTitle  = titleFormat&1
    self.centerTitle = titleFormat>>1&1
    
    if self.coOpType > 0:
      for i, score in enumerate(self.coOpScoring):
        if not self.partImage:
          break
        if score.instrument == [4]:
          if not self.engine.loadImgDrawing(self, "partLoad", os.path.join("themes",themename,"drum.png")):
            if not self.engine.loadImgDrawing(self, "partLoad", os.path.join("drum.png")):
              self.partImage = False
        elif score.instrument == [2]:
          if not self.engine.loadImgDrawing(self, "partLoad", os.path.join("themes",themename,"bass.png")):
            if not self.engine.loadImgDrawing(self, "partLoad", os.path.join("bass.png")):
              self.partImage = False
        elif score.instrument == [5]:
          if not self.engine.loadImgDrawing(self, "partLoad", os.path.join("themes",themename,"mic.png")):
            if not self.engine.loadImgDrawing(self, "partLoad", os.path.join("mic.png")):
              self.partImage = False
        else:
          if not self.engine.loadImgDrawing(self, "partLoad", os.path.join("themes",themename,"guitar.png")):
            if not self.engine.loadImgDrawing(self, "partLoad", os.path.join("guitar.png")):
              self.partImage = False
        if self.partLoad:
          self.part[i] = self.partLoad
    else:
      for i, score in enumerate(self.scoring):
        if not self.partImage:
          break
        if score.instrument == [4]:
          if not self.engine.loadImgDrawing(self, "partLoad", os.path.join("themes",themename,"drum.png")):
            if not self.engine.loadImgDrawing(self, "partLoad", os.path.join("drum.png")):
              self.partImage = False
        elif score.instrument == [2]:
          if not self.engine.loadImgDrawing(self, "partLoad", os.path.join("themes",themename,"bass.png")):
            if not self.engine.loadImgDrawing(self, "partLoad", os.path.join("bass.png")):
              self.partImage = False
        elif score.instrument == [5]:
          if not self.engine.loadImgDrawing(self, "partLoad", os.path.join("themes",themename,"mic.png")):
            if not self.engine.loadImgDrawing(self, "partLoad", os.path.join("mic.png")):
              self.partImage = False
        else:
          if not self.engine.loadImgDrawing(self, "partLoad", os.path.join("themes",themename,"guitar.png")):
            if not self.engine.loadImgDrawing(self, "partLoad", os.path.join("guitar.png")):
              self.partImage = False
        if self.partLoad:
          self.part[i] = self.partLoad

    self.partLoad = None
    
    Dialogs.hideLoadingSplashScreen(self.engine, loadingScreen)
 
  def handleWorldCharts(self, result):
    self.uploadResponse[self.resultNum] = self.uploadResult
    self.resultNum += 1
  
  def keyPressed(self, key, unicode):
    ret = Scene.keyPressed(self, key, unicode)
    c = self.controls.keyPressed(key)
    
    if self.song and (c in self.progressKeys or key == pygame.K_RETURN or key == pygame.K_ESCAPE):
      if self.progressReady:
        self.resultStep += 1
        self.resultSubStep = [0 for i in self.scoring]
        self.progressReady = False
      elif self.progressToScores:
        self.resultStep = 2
        self.resultSubStep = [0 for i in self.scoring]
        self.progressToScores = False
      for i in range(len(self.scoring)):
        if self.coOpType > 0:
          if self.rolling[i]:
            self.skipRoll(i)
            self.skipShrink(i)
          if self.delay[i] > 0:
            self.skipDelay(i)
          break
        elif c in self.playerProgressKeys[i] or key == pygame.K_RETURN or key == pygame.K_ESCAPE:
          if self.rolling[i]:
            self.skipRoll(i)
            self.skipShrink(i)
          if self.delay[i] > 0:
            self.skipDelay(i)
          break
      if self.waiting:
        self.waiting = False
      if self.detailedScores:
        self.detailedScores = False
      if self.resultStep == 3:
        self.engine.view.pushLayer(self.menu)
        self.resultStep += 1
  
  def quit(self):
    self.background = None
    self.song = None
    self.engine.view.popLayer(self.menu)
    self.engine.world.finishGame()
  
  def replay(self):
    self.background = None
    self.song = None
    self.engine.view.popLayer(self.menu)
    self.engine.world.createScene("GuitarScene", libraryName = self.libraryName, songName = self.songName)
  
  def replaySetlist(self):
    self.background = None
    self.song = None
    self.engine.view.popLayer(self.menu)
    self.engine.world.songQueue.replayFullQueue()
    self.engine.world.createScene("SongChoosingScene")
  
  def endSetlist(self):
    self.background = None
    self.song = None
    self.engine.view.popLayer(self.menu)
    self.engine.world.songQueue.reset()
    self.engine.world.playingQueue = False
    self.engine.world.createScene("SongChoosingScene")
  
  def changeSong(self):
    self.background = None
    self.song = None
    self.engine.view.popLayer(self.menu)
    if self.engine.world.playingQueue:
      if self.coOpScoring:
        self.engine.world.songQueue.addScores(self.coOpScoring)
      else:
        self.engine.world.songQueue.addScores(self.scoring)
    self.engine.world.createScene("SongChoosingScene")
  
  def stats(self):
    self.detailedScores = True
  
  def songLoaded(self, song):
    for i, player in enumerate(self.playerList):
      song.difficulty[i] = player.difficulty
    
    self.loaded = True
  
  def nextHighScore(self):
    if self.hsRollIndex < len(self.playerList):
      self.scoreDifficulty = self.playerList[self.hsRollIndex].difficulty
      self.scorePart = self.playerList[self.hsRollIndex].part
      return
    elif not self.shownScores:
      self.scorePart = self.song.info.parts[0]
      self.scoreDifficulty = self.song.info.partDifficulties[self.scorePart.id][0]
      self.shownScores = True
      return
    
    found = 0  
    for part in self.song.info.parts:
      for difficulty in self.song.info.partDifficulties[part.id]:
        if found == 1:
          self.scoreDifficulty = difficulty
          self.scorePart = part
          return
        
        if self.scoreDifficulty == difficulty and self.scorePart == part:
          found = 1
    
    self.scorePart = self.song.info.parts[0]
    self.scoreDifficulty = self.song.info.partDifficulties[self.scorePart.id][0]
  
  def startRoll(self, playerNum):
    self.diffScore[playerNum] = self.newScore[playerNum] - self.currentScore[playerNum]
    self.scoreRollTimer[playerNum] = 0
    self.rolling[playerNum] = True
  
  def scoreRoll(self, playerNum, ticks):
    if self.currentScore[playerNum] != self.newScore[playerNum]:
      self.currentScore[playerNum] += int((self.diffScore[playerNum]*ticks)/500.0)
      if self.diffScore[playerNum] > 0:
        if self.currentScore[playerNum] > self.newScore[playerNum]:
          self.currentScore[playerNum] = self.newScore[playerNum]
      else:
        if self.currentScore[playerNum] < self.newScore[playerNum]:
          self.currentScore[playerNum] = self.newScore[playerNum]
    else:
      self.rolling[playerNum] = False
  
  def skipRoll(self, playerNum):
    if self.rolling[playerNum]:
      self.currentScore[playerNum] = self.newScore[playerNum]
      self.rolling[playerNum] = False
  
  def shrinkSpace(self, playerNum, ticks):
    self.space[playerNum] -= ticks/1000.0
    if self.space[playerNum] < 1:
      self.space[playerNum] = 1
  
  def skipShrink(self, playerNum):
    if self.space[playerNum] > 1:
      self.space[playerNum] = 1
  
  def processDelay(self, playerNum, ticks):
    if self.delay[playerNum] > 0:
      self.delay[playerNum] -= ticks
      if self.delay[playerNum] < 0:
        self.delay[playerNum] = 0
  
  def skipDelay(self, playerNum):
    if self.delay[playerNum] > 0:
      self.delay[playerNum] = 0
  
  def uploadHighscores(self, part = Song.parts[Song.GUITAR_PART], playerNum = 0, scoreExt = None):
    player = self.playerList[playerNum]
    i      = playerNum
    try:
      d = {
        "songName": "%s" % (Song.removeSongOrderPrefixFromName(self.song.info.name)),
        "songHash": self.song.getHash(),
        "scores":   None,
        "scores_ext": None,
        "version":  self.engine.uploadVersion,
        "songPart": part
      }
      scores     = {}
      scores_ext = {}
      upname = self.playerList[i].upname
      # evilynux - the str() around the upname is not there for fun,
      #            it's used to convert the unicode string so the server 
      #            scripts accept it. 
      scoreHash = hashlib.sha1("%d%d%d%s" % (player.getDifficultyInt(), self.finalScore[i], self.scoring[i].stars, str(upname))).hexdigest()
      scores[player.getDifficultyInt()]     = [(self.finalScore[i], self.scoring[i].stars, str(upname), scoreHash)]
      scores_ext[player.getDifficultyInt()] = [(scoreHash, self.scoring[i].stars) + scoreExt]
      d["scores"] = binascii.hexlify(Cerealizer.dumps(scores))
      d["scores_ext"] = binascii.hexlify(Cerealizer.dumps(scores_ext))
      url = self.engine.config.get("network", "uploadurl_w67_starpower")
      data = urllib.urlopen(url + "?" + urllib.urlencode(d)).read()
      Log.debug("Score upload result: %s" % data)
      return data   #MFH - want to return the actual result data.
    except Exception, e:
      Log.error("Score upload error: %s" % e)
      return False
    return True
  
  def runScores(self):
    self.haveRunScores = True
    for i, scoreCard in enumerate(self.scoring):
      if self.noScore[i]:
        continue
      scores = self.song.info.getHighscores(self.playerList[i].difficulty, part = self.playerList[i].part)
      if not scores or self.finalScore[i] > scores[-1][0] or len(scores) < 5:
        name = Dialogs.getText(self.engine, _("%d points is a new high score! Enter your name:") % self.finalScore[i], self.playerList[i].upname)
        if name:
          self.playerList[i].upname = name
        scoreExt = (scoreCard.notesHit, scoreCard.totalStreakNotes, scoreCard.hiStreak, self.engine.uploadVersion, scoreCard.handicap, scoreCard.longHandicap, self.originalScore[i])
        self.highscoreIndex[i] = self.song.info.addHighscore(self.playerList[i].difficulty, self.finalScore[i], scoreCard.stars, self.playerList[i].name, part = self.playerList[i].part, scoreExt = scoreExt)
        self.song.info.save()
        
        if self.engine.config.get("network", "uploadscores"):
          self.uploadingScores[i] = True
          fn = lambda: self.uploadHighscores(part = self.playerList[i].part, playerNum = i, scoreExt = scoreExt)
          
          self.engine.resource.load(self, "uploadResult", fn, onLoad = self.handleWorldCharts)
    self.doneScores = True
    self.hsRollIndex = 0
    self.nextHighScore()
  
  def run(self, ticks):
    Scene.run(self, ticks)
    
    self.time           += ticks / 50.0
    self.counter        += ticks
    self.animationTimer += ticks
    
    if self.resultStep == 0 and self.loaded:
      if self.showHandicap == 0 and not self.skipCheats:
        for i, scoreCard in enumerate(self.scoring):
          if not self.rolling[i] and self.resultSubStep[i] == 0:
            self.newScore[i] = self.finalScore[i]
            scoreCard.score = self.finalScore[i]
            for cheat in self.cheats[i]:
              self.totalHandicap[i] *= cheat[1]
              if cheat[1] < 1.0:
                scoreCard.cheatsApply = True
            scoreCard.updateAvMult()
            scoreCard.getStarScores()
            if self.starScoring == 0:
              if scoreCard.cheatsApply:
                scoreCard.stars = min(int(self.starMass[i]/100),5)
              if scoreCard.stars > self.oldStars[i]:
                scoreCard.stars = self.oldStars[i]
            self.space[i] = 1.5
            self.startRoll(i)
          if self.rolling[i]:
            self.scoreRoll(i, ticks)
          if not self.rolling[i]:
            self.resultSubStep[i] += 1
          if self.space[i] > 1:
            self.shrinkSpace(i, ticks)
        if min(self.resultSubStep) > 0:
          self.progressToScores = True
      else:
        for i, scoreCard in enumerate(self.scoring):
          self.scoreRollTimer[i] += ticks
          if not self.rolling[i] and self.resultSubStep[i] == 0:
            self.newScore[i] = scoreCard.score
            scoreCard.updateAvMult()
            scoreCard.getStarScores()
            self.space[i] = 1.5
            self.startRoll(i)
          if self.rolling[i]:
            self.scoreRoll(i, ticks)
          if not self.rolling[i]:
            self.resultSubStep[i] += 1
          if self.space[i] > 1:
            self.shrinkSpace(i, ticks)
        
        if min(self.resultSubStep) > 0:
          self.progressReady = True
    
    if self.resultStep == 1:
      if self.skipCheats:
        self.resultStep += 1
      else:
        for i, scoreCard in enumerate(self.scoring):
          if self.resultSubStep[i] == 0:
            if self.currentCheat[i] < len(self.cheats[i]):
              self.scoreRollTimer[i] += ticks
              if self.finishedCheat[i] == -1:
                self.cheatsApply = True
              if not self.rolling[i]:
                if self.delay[i] == 0 and self.finishedCheat[i] < self.currentCheat[i] and not self.waiting:
                  if self.cheats[i][self.currentCheat[i]][1] < 1.0:
                    scoreCard.cheatsApply = True
                  self.newScore[i] = int(self.currentScore[i] * self.cheats[i][self.currentCheat[i]][1])
                  self.totalHandicap[i] *= self.cheats[i][self.currentCheat[i]][1]
                  if self.starScoring == 0:
                    self.starMass[i] *= self.cheats[i][self.currentCheat[i]][1]
                    if scoreCard.cheatsApply:
                      scoreCard.stars = min(int(self.starMass[i]/100),5)
                    if scoreCard.stars > self.oldStars[i]:
                      scoreCard.stars = self.oldStars[i]
                  self.startRoll(i)
                  self.finishedCheat[i] += 1
                  self.engine.data.getScrewUpSound().play()
                elif self.delay[i] == 0 and self.finishedCheat[i] == self.currentCheat[i]:
                  self.currentCheat[i] += 1
                  self.delay[i] = 3000
                  self.waiting  = True
                else:
                  self.processDelay(i, ticks)
              if self.rolling[i]:
                self.scoreRoll(i, ticks)
                scoreCard.score = self.currentScore[i]
                if self.starScoring > 0:
                  star = scoreCard.stars
                  scoreCard.updateAvMult()
                  scoreCard.getStarScores()
                  if scoreCard.score == 0:
                    scoreCard.stars = 0
                  if star > scoreCard.stars and self.engine.data.starLostSoundFound:
                    self.engine.data.starLostSound.play()
                  elif star < scoreCard.stars and self.engine.data.starDingSoundFound:
                    self.engine.data.starDingSound.play()
            else:
              self.resultSubStep[i] += 1
          if self.resultSubStep[i] == 1:
            if self.starScoring == 0:
              star = scoreCard.stars
              if scoreCard.cheatsApply:
                scoreCard.stars = min(int(self.starMass[i]/100),5)
              if scoreCard.stars > self.oldStars[i]:
                scoreCard.stars = self.oldStars[i]
              if star > scoreCard.stars and self.engine.data.starLostSoundFound:
                self.engine.data.starLostSound.play()
              elif star < scoreCard.stars and self.engine.data.starDingSoundFound:
                self.engine.data.starDingSound.play()
            self.resultSubStep[i] += 1
            self.currentScore[i] = self.finalScore[i]
        
        if min(self.resultSubStep) > 1:
          self.progressReady = True
    
    if self.resultStep == 2:
      if self.coOpType == 0:
        for i, player in enumerate(self.playerList):
          if self.finalScore[i] == 0:
            self.noScore[i] = True
        if not self.haveRunScores:
          self.nextHighScore()
          self.runScores()

        if self.doneScores:
          if len(self.playerList) > 1 and self.playerList[0].part == self.playerList[1].part and self.playerList[0].difficulty == self.playerList[1].difficulty and self.highscoreIndex[0] != -1 and self.highscoreIndex[1] != -1 and self.highscoreIndex[1] <= self.highscoreIndex[0]:
            self.highscoreIndex[0] += 1
      else:
        self.nextHighScore()
      if self.keepCount > 0 and not self.doneCount:
        if self.song.info.count:
          count = int(self.song.info.count)
        else:
          count = 0
        count += 1
        if self.careerMode and not self.song.info.completed and self.scoring[0].stars >= self.careerStars:
          Log.debug("Song completed")
          self.song.info.completed = True
        self.song.info.count = "%d" % count
        self.song.info.save()
        self.doneCount = True
      self.resultStep = 3
      
      #MFH - re-adding taunt logic from r912:
      taunt = None

      #MFH - this is just a dirty hack.  Dirty, dirty hack.  Should be refined.
      scoreToUse = self.currentScore[0]
      starsToUse = self.scoring[0].stars
      accuracyToUse = self.scoring[0].hitAccuracy

      #MFH TODO - utilize new functions in self.engine.data to automatically enumerate any number of the following soundfiles automatically, for issue 73
      if self.Congratphrase:
        if scoreToUse == 0:
          taunt = os.path.join("sounds","jurgen1.ogg")
        elif accuracyToUse == 100.0:    #MFH - this will only play when you 100% a song
          taunt = random.choice([os.path.join("sounds","100pct1.ogg"), os.path.join("sounds","100pct2.ogg"), os.path.join("sounds","100pct3.ogg")])
        elif accuracyToUse >= 99.0:    #MFH - these 3 sounds will only play when you get > 99.0%
          taunt = random.choice([os.path.join("sounds","99pct1.ogg"), os.path.join("sounds","99pct2.ogg"), os.path.join("sounds","99pct3.ogg")])

        elif starsToUse > 0 and starsToUse < 4:   #MFH - ok, fine - perhaps Jurgen shouldn't insult a 4-star score. :)
          taunt = random.choice([os.path.join("sounds","jurgen2.ogg"), os.path.join("sounds","jurgen3.ogg"), os.path.join("sounds","jurgen4.ogg"), os.path.join("sounds","jurgen5.ogg")])
        elif starsToUse >= 5:
          taunt = random.choice([os.path.join("sounds","perfect1.ogg"), os.path.join("sounds","perfect2.ogg"), os.path.join("sounds","perfect3.ogg")])

      if taunt:
        try:
          self.engine.resource.load(self, "taunt", lambda: Sound(self.engine.resource.fileName(taunt)))
        except IOError:
          taunt = None
          self.taunt = None
      
    
    if self.resultStep > 2:
      if self.pauseScroll < 5000:
        self.pauseScroll += ticks
      else:
        self.offset -= .001
    


    if self.counter > 5000 and self.taunt:
      self.taunt.setVolume(self.engine.config.get("audio", "SFX_volume"))
      self.taunt.play()
      self.taunt = None
    
    if self.engine.data.cheerSoundFound > 0 and self.resultCheerLoop > 0:
      if self.resultCheerLoop == 2 or (self.resultCheerLoop == 1 and self.engine.data.cheerSoundFound == 2):
        self.cheerLoopCounter += 1
        if self.cheerLoopCounter >= self.cheerLoopDelay:
          self.cheerLoopCounter = 0
          self.engine.data.crowdSound.play()
  
  def render(self, visibility, topMost):
    self.engine.view.setViewport(1,0)
    Scene.render(self, visibility, topMost)
    
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_COLOR_MATERIAL)
    
    self.engine.view.setOrthogonalProjection(normalize = True)
    
    try:
      if self.detailedScores:
        self.renderStats(visibility, topMost)
      else:
        if self.coOpType > 0:
          self.renderInitialCoOpScore(visibility, topMost)
        else:
          self.renderInitialScore(visibility, topMost)
        if self.resultStep > 0:
          self.renderCheatList(visibility, topMost)
        if self.resultStep > 2:
          self.renderHighScores(visibility, topMost)
    finally:
      self.engine.view.setViewport(1,0)
      self.engine.view.resetProjection()
  
  def renderInitialScore(self, visibility, topMost):
    bigFont = self.engine.data.bigFont
    defFont = self.engine.data.font
    
    v = ((1 - visibility) **2)
    
    w, h = self.fullView
    if self.background:
      self.engine.drawImage(self.background, scale = (1.0,-1.0), coord = (w/2,h/2), stretched = 3)
    
    self.engine.theme.setBaseColor(1-v)
    
    if self.song:
      try:
        text = self.engine.theme.result_song_text % Song.removeSongOrderPrefixFromName(self.song.info.name)
      except TypeError:
        text = "%s %s" % (Song.removeSongOrderPrefixFromName(self.song.info.name), self.engine.theme.result_song_text)
      try:
        r, g, b = self.engine.theme.hexToColorResults(self.engine.theme.result_song[3])
        glColor3f(r, g, b)
      except IndexError:
        self.engine.theme.setBaseColor(1-v)
      try:
        font = self.engine.data.fontDict[self.engine.theme.result_song[4]]
      except:
        font = defFont
      if self.scaleTitle == 1:
        if self.centerTitle == 1:
          max = .97 - (abs(.5 - float(self.engine.theme.result_song[0]))*2)
          scale = font.scaleText(text, max, scale = float(self.engine.theme.result_song[2]))
          wText, hText = font.getStringSize(text, scale = scale)
          xText = float(self.engine.theme.result_song[0])-wText/2
          if xText < .03:
            xText = .03
          font.render(text, (xText, float(self.engine.theme.result_song[1])), scale = scale)
        else:
          scale = font.scaleText(text, .97 - float(self.engine.theme.result_song[0]), scale = float(self.engine.theme.result_song[2]))
          font.render(text, (float(self.engine.theme.result_song[0]), float(self.engine.theme.result_song[1])), scale = scale)
      else:
        if self.centerTitle == 1:
          Dialogs.wrapCenteredText(font, (float(self.engine.theme.result_song[0]), float(self.engine.theme.result_song[1]) - v), text, 0.9, float(self.engine.theme.result_song[2]))
        else:
          Dialogs.wrapText(font, (float(self.engine.theme.result_song[0]), float(self.engine.theme.result_song[1]) - v), text, 0.9, float(self.engine.theme.result_song[2]))
      
      for i, scoreCard in enumerate(self.scoring):
        self.engine.view.setViewportHalf(len(self.scoring),i)
        
        text = "%d/%d" % (scoreCard.notesHit, scoreCard.totalStreakNotes)
        try:
          text = self.engine.theme.result_stats_notes_text % text
        except TypeError:
          text = "%s %s" % (text, self.engine.theme.result_stats_notes_text)
        try:
          r, g, b = self.engine.theme.hexToColorResults(self.engine.theme.result_stats_notes[3])
          glColor3f(r, g, b)
        except IndexError:
          self.engine.theme.setBaseColor(1-v)
        try:
          font = self.engine.data.fontDict[self.engine.theme.result_stats_notes[4]]
        except:
          font = defFont
        wText, hText = font.getStringSize(text, scale = float(self.engine.theme.result_stats_notes[2]))
        Dialogs.wrapText(font, (float(self.engine.theme.result_stats_notes[0]) - wText/2, float(self.engine.theme.result_stats_notes[1]) + v), text, 0.9, float(self.engine.theme.result_stats_notes[2]))
        
        try:
          r, g, b = self.engine.theme.hexToColorResults(self.engine.theme.result_score[3])
          glColor3f(r, g, b)
        except IndexError:
          self.engine.theme.setBaseColor(1-v)
        try:
          font = self.engine.data.fontDict[self.engine.theme.result_score[4]]
        except:
          font = bigFont
        text = "%d" % self.currentScore[i]
        wText, hText = font.getStringSize(text, scale = float(self.engine.theme.result_score[2]))
        font.render(text, (float(self.engine.theme.result_score[0]) - wText / 2, float(self.engine.theme.result_score[1]) + v), scale = float(self.engine.theme.result_score[2]))
        
        if self.resultStep == 0:
          space = self.space[i]
        else:
          space = 1

        scale = self.resultStar[2]

        try:
          hspacing = self.resultStar[3]
        except IndexError:
          hspacing = 1.0
        self.engine.drawStarScore(w, h, self.resultStar[0], self.resultStar[1], scoreCard.stars, scale, space = space, horiz_spacing = hspacing, align = 1)
        
#-        if scoreCard.stars > 5:
#-          for j in range(5):
#-            if self.fcStars and scoreCard.stars == 7:
#-              star = self.starFC
#-            else:
#-              star = self.starPerfect
#-            try:
#-              wide = star.width1()*float(self.engine.theme.result_star[3])
#-            except IndexError:
#-              wide = star.width1()*.5
#-            if self.maskStars:
#-              if self.theme == 2:
#-                self.engine.drawImage(star, scale = (scale,-scale), coord = (((w*self.engine.theme.result_star[0])+wide*j)*space**4,h*float(self.engine.theme.result_star[1])), color = (1, 1, 0, 1))
#-              else:
#-                self.engine.drawImage(star, scale = (scale,-scale), coord = (((w*float(self.engine.theme.result_star[0]))+wide*j)*space**4,h*float(self.engine.theme.result_star[1])), color = (0, 1, 0, 1))
#-            else:
#-              self.engine.drawImage(star, scale = (scale,-scale), coord = (((w*float(self.engine.theme.result_star[0]))+wide*j)*space**4,h*float(self.engine.theme.result_star[1])))
#-        else:
#-          for j in range(5):
#-            if j < scoreCard.stars:
#-              star = self.star2
#-            else:
#-              star = self.star1
#-            try:
#-              wide = star.width1()*float(self.engine.theme.result_star[3])
#-            except IndexError:
#-              wide = star.width1()*.5
#-            self.engine.drawImage(star, scale = (scale,-scale), coord = (((w*float(self.engine.theme.result_star[0]))+wide*j)*space**4,h*float(self.engine.theme.result_star[1])))


        
        settingsText = "%s %s - %s: %s / %s, %s: %s" % (self.engine.versionString, self.tsSettings, self.tsHopos, self.hopoStyle, self.hopoFreq, self.tsHitWindow, self.hitWindow)
        settingsScale = 0.0012
        wText, hText = defFont.getStringSize(settingsText, settingsScale)
        defFont.render(settingsText, (.5 - wText/2, 0.05), scale = settingsScale)
        
        try:
          font = self.engine.data.fontDict[self.engine.theme.result_stats_accuracy[4]]
        except:
          font = defFont
        text = _(self.engine.theme.result_stats_accuracy_text) % scoreCard.hitAccuracy
        wText, hText = font.getStringSize(text)
        try:
          r, g, b = self.engine.theme.hexToColorResults(self.engine.theme.result_stats_accuracy[3])
          glColor3f(r, g, b)
        except IndexError:
          self.engine.theme.setBaseColor(1-v)
        font.render(text, (float(self.engine.theme.result_stats_accuracy[0]) - wText / 2, float(self.engine.theme.result_stats_accuracy[1]) + v), scale = float(self.engine.theme.result_stats_accuracy[2]))
        
        try:
          font = self.engine.data.fontDict[self.engine.theme.result_stats_streak[4]]
        except:
          font = defFont
        text = _(self.engine.theme.result_stats_streak_text) % scoreCard.hiStreak
        wText, hText = font.getStringSize(text)
        try:
          r, g, b = self.engine.theme.hexToColorResults(self.engine.theme.result_stats_streak[3])
          glColor3f(r, g, b)
        except IndexError:
          self.engine.theme.setBaseColor(1-v)
        font.render(text, (float(self.engine.theme.result_stats_streak[0]) - wText / 2, float(self.engine.theme.result_stats_streak[1]) + v), scale = float(self.engine.theme.result_stats_streak[2]))
        
        try:
          font = self.engine.data.fontDict[self.engine.theme.result_stats_diff[4]]
        except:
          font = defFont
        text = _(self.engine.theme.result_stats_diff_text) % self.playerList[i].difficulty
        wText, hText = font.getStringSize(text)
        try:
          r, g, b = self.engine.theme.hexToColorResults(self.engine.theme.result_stats_diff[3])
          glColor3f(r, g, b)
        except IndexError:
          self.engine.theme.setBaseColor(1-v)
        font.render(text, (float(self.engine.theme.result_stats_diff[0]) - wText / 2, float(self.engine.theme.result_stats_diff[1]) + v), scale = float(self.engine.theme.result_stats_diff[2]))
        
        try:
          font = self.engine.data.fontDict[self.engine.theme.result_stats_name[4]]
        except:
          font = defFont
        text = self.playerList[i].name
        wText, hText = font.getStringSize(text)
        try:
          r, g, b = self.engine.theme.hexToColorResults(self.engine.theme.result_stats_name[3])
          glColor3f(r, g, b)
        except IndexError:
          self.engine.theme.setBaseColor(1-v)
        font.render(text, (float(self.engine.theme.result_stats_name[0]) - wText / 2, float(self.engine.theme.result_stats_name[1]) + v), scale = float(self.engine.theme.result_stats_name[2]))
        
        if self.engine.theme.result_stats_part_text.strip() == "$icon$" and not self.partImage:
          text = "%s"
        else:
          text = self.engine.theme.result_stats_part_text.strip()
        
        try:
          font = self.engine.data.fontDict[self.engine.theme.result_stats_part[4]]
        except:
          font = defFont
        if text == "$icon$" and self.partImage:
          self.engine.drawImage(self.part[i], scale = (float(self.engine.theme.result_stats_part[2]),-float(self.engine.theme.result_stats_part[2])), coord = (w*float(self.engine.theme.result_stats_part[0]),h*float(self.engine.theme.result_stats_part[1])))
        else:
          text = _(self.engine.theme.result_stats_part_text) % self.playerList[i].part
          wText, hText = font.getStringSize(text)
          try:
            r, g, b = self.engine.theme.hexToColorResults(self.engine.theme.result_stats_part[3])
            glColor3f(r, g, b)
          except IndexError:
            self.engine.theme.setBaseColor(1-v)
          font.render(text, (float(self.engine.theme.result_stats_part[0]) - wText / 2, float(self.engine.theme.result_stats_part[1]) + v), scale = float(self.engine.theme.result_stats_part[2]))
  
  def renderInitialCoOpScore(self, visibility, topMost):
    bigFont = self.engine.data.bigFont
    defFont = self.engine.data.font
    
    v = ((1 - visibility) **2)
    
    w, h = self.fullView
    if self.background:
      self.engine.drawImage(self.background, scale = (1.0,-1.0), coord = (w/2,h/2), stretched = 3)
    
    self.engine.theme.setBaseColor(1-v)
    
    if self.song:
      try:
        text = self.engine.theme.result_song_text % Song.removeSongOrderPrefixFromName(self.song.info.name)
      except TypeError:
        text = "%s %s" % (Song.removeSongOrderPrefixFromName(self.song.info.name), self.engine.theme.result_song_text)
      try:
        r, g, b = self.engine.theme.hexToColorResults(self.engine.theme.result_song[3])
        glColor3f(r, g, b)
      except IndexError:
        self.engine.theme.setBaseColor(1-v)
      try:
        font = self.engine.data.fontDict[self.engine.theme.result_song[4]]
      except:
        font = defFont
      wText, hText = font.getStringSize(text, scale = float(self.engine.theme.result_song[2]))
      if self.scaleTitle == 1:
        if self.centerTitle == 1:
          max = .94 - (abs(.5 - float(self.engine.theme.result_song[0]))*2)
          scale = font.scaleText(text, max, scale = float(self.engine.theme.result_song[2]))
          wText, hText = font.getStringSize(text, scale = scale)
          xText = float(self.engine.theme.result_song[0])-wText/2
          if xText < .03:
            xText = .03
          font.render(text, (xText, float(self.engine.theme.result_song[1])), scale = scale)
        else:
          scale = font.scaleText(text, .97 - float(self.engine.theme.result_song[0]), scale = float(self.engine.theme.result_song[2]))
          font.render(text, (float(self.engine.theme.result_song[0]), float(self.engine.theme.result_song[1])), scale = scale)
      else:
        if self.centerTitle == 1:
          Dialogs.wrapCenteredText(font, (float(self.engine.theme.result_song[0]), float(self.engine.theme.result_song[1]) - v), text, 0.9, float(self.engine.theme.result_song[2]))
        else:
          Dialogs.wrapText(font, (float(self.engine.theme.result_song[0]), float(self.engine.theme.result_song[1]) - v), text, 0.9, float(self.engine.theme.result_song[2]))
      
      scoreCard = self.scoring[0]
      i = 0

      try:
        r, g, b = self.engine.theme.hexToColorResults(self.engine.theme.result_score[3])
        glColor3f(r, g, b)
      except IndexError:
        self.engine.theme.setBaseColor(1-v)
      text = "%d" % self.currentScore[i]
      try:
        font = self.engine.data.fontDict[self.engine.theme.result_score[4]]
      except:
        font = bigFont
      wText, hText = font.getStringSize(text, scale = float(self.engine.theme.result_score[2]))
      font.render(text, (float(self.engine.theme.result_score[0]) - wText / 2, float(self.engine.theme.result_score[1]) + v), scale = float(self.engine.theme.result_score[2]))
      
      if self.resultStep == 0:
        space = self.space[i]
      else:
        space = 1

      scale = self.resultStar[2]
          
      try:
        hspacing = self.resultStar[3]
      except IndexError:
        hspacing = 1.1
      self.engine.drawStarScore(w, h, self.resultStar[0], self.resultStar[1], scoreCard.stars, scale, horiz_spacing = hspacing, space = space, align = 1)

#-      if scoreCard.stars > 5:
#-        for j in range(5):
#-          if self.fcStars and scoreCard.stars == 7:
#-            star = self.starFC
#-          else:
#-            star = self.starPerfect
#-          try:
#-            wide = star.width1()*float(self.engine.theme.result_star[3])
#-          except IndexError:
#-            wide = star.width1()*.5
#-          if self.maskStars:
#-            if self.theme == 2:
#-              self.engine.drawImage(star, scale = (float(self.engine.theme.result_star[2]),-float(self.engine.theme.result_star[2])), coord = (((w*self.engine.theme.result_star[0])+wide*j)*space**4,h*float(self.engine.theme.result_star[1])), color = (1, 1, 0, 1))
#-            else:
#-              self.engine.drawImage(star, scale = (float(self.engine.theme.result_star[2]),-float(self.engine.theme.result_star[2])), coord = (((w*float(self.engine.theme.result_star[0]))+wide*j)*space**4,h*float(self.engine.theme.result_star[1])), color = (0, 1, 0, 1))
#-          else:
#-            self.engine.drawImage(star, scale = (float(self.engine.theme.result_star[2]),-float(self.engine.theme.result_star[2])), coord = (((w*float(self.engine.theme.result_star[0]))+wide*j)*space**4,h*float(self.engine.theme.result_star[1])))
#-      else:
#-        for j in range(5):
#-          if j < scoreCard.stars:
#-            star = self.star2
#-          else:
#-            star = self.star1
#-          try:
#-            wide = star.width1()*float(self.engine.theme.result_star[3])
#-          except IndexError:
#-            wide = star.width1()*.5
#-          self.engine.drawImage(star, scale = (float(self.engine.theme.result_star[2]),-float(self.engine.theme.result_star[2])), coord = (((w*float(self.engine.theme.result_star[0]))+wide*j)*space**4,h*float(self.engine.theme.result_star[1])))
      
      settingsText = "%s %s - %s: %s / %s, %s: %s" % (self.engine.versionString, self.tsSettings, self.tsHopos, self.hopoStyle, self.hopoFreq, self.tsHitWindow, self.hitWindow)
      settingsScale = 0.0012
      wText, hText = font.getStringSize(settingsText, settingsScale)
      defFont.render(settingsText, (.5 - wText/2, 0.0), scale = settingsScale)
      
      if self.coOpType == 2:
        try:
          font = self.engine.data.fontDict[self.engine.theme.result_stats_streak[4]]
        except:
          font = defFont
        text = _(self.engine.theme.result_stats_streak_text) % scoreCard.hiStreak
        wText, hText = font.getStringSize(text)
        try:
          r, g, b = self.engine.theme.hexToColorResults(self.engine.theme.result_stats_streak[3])
          glColor3f(r, g, b)
        except IndexError:
          self.engine.theme.setBaseColor(1-v)
        font.render(text, (float(self.engine.theme.result_stats_streak[0]) - wText / 2, float(self.engine.theme.result_stats_streak[1]) + v), scale = float(self.engine.theme.result_stats_streak[2]))
      
      for i, scoreCard in enumerate(self.coOpScoring):
        self.engine.view.setViewportHalf(len(self.coOpScoring),i)
        
        text = "%d/%d" % (scoreCard.notesHit, scoreCard.totalStreakNotes)
        try:
          text = self.engine.theme.result_stats_notes_text % text
        except TypeError:
          text = "%s %s" % (text, self.engine.theme.result_stats_notes_text)
        try:
          r, g, b = self.engine.theme.hexToColorResults(self.engine.theme.result_stats_notes[3])
          glColor3f(r, g, b)
        except IndexError:
          self.engine.theme.setBaseColor(1-v)
        try:
          font = self.engine.data.fontDict[self.engine.theme.result_stats_notes[4]]
        except:
          font = defFont
        wText, hText = font.getStringSize(text, scale = float(self.engine.theme.result_stats_notes[2]))
        Dialogs.wrapText(font, (float(self.engine.theme.result_stats_notes[0]) - wText/2, float(self.engine.theme.result_stats_notes[1]) + v), text, 0.9, float(self.engine.theme.result_stats_notes[2]))
        
        text = _(self.engine.theme.result_stats_accuracy_text) % scoreCard.hitAccuracy
        try:
          font = self.engine.data.fontDict[self.engine.theme.result_stats_accuracy[4]]
        except:
          font = defFont
        wText, hText = font.getStringSize(text)
        try:
          r, g, b = self.engine.theme.hexToColorResults(self.engine.theme.result_stats_accuracy[3])
          glColor3f(r, g, b)
        except IndexError:
          self.engine.theme.setBaseColor(1-v)
        font.render(text, (float(self.engine.theme.result_stats_accuracy[0]) - wText / 2, float(self.engine.theme.result_stats_accuracy[1]) + v), scale = float(self.engine.theme.result_stats_accuracy[2]))
        
        if self.coOpType < 2: # not GH Co-Op
          text = _(self.engine.theme.result_stats_streak_text) % scoreCard.hiStreak
          try:
            font = self.engine.data.fontDict[self.engine.theme.result_stats_streak[4]]
          except:
            font = defFont
          wText, hText = font.getStringSize(text)
          try:
            r, g, b = self.engine.theme.hexToColorResults(self.engine.theme.result_stats_streak[3])
            glColor3f(r, g, b)
          except IndexError:
            self.engine.theme.setBaseColor(1-v)
          font.render(text, (float(self.engine.theme.result_stats_streak[0]) - wText / 2, float(self.engine.theme.result_stats_streak[1]) + v), scale = float(self.engine.theme.result_stats_streak[2]))
        
        text = _(self.engine.theme.result_stats_diff_text) % self.playerList[i].difficulty
        try:
          font = self.engine.data.fontDict[self.engine.theme.result_stats_diff[4]]
        except:
          font = defFont
        wText, hText = font.getStringSize(text)
        try:
          r, g, b = self.engine.theme.hexToColorResults(self.engine.theme.result_stats_diff[3])
          glColor3f(r, g, b)
        except IndexError:
          self.engine.theme.setBaseColor(1-v)
        font.render(text, (float(self.engine.theme.result_stats_diff[0]) - wText / 2, float(self.engine.theme.result_stats_diff[1]) + v), scale = float(self.engine.theme.result_stats_diff[2]))
        
        text = self.playerList[i].name
        try:
          font = self.engine.data.fontDict[self.engine.theme.result_stats_name[4]]
        except:
          font = defFont
        wText, hText = font.getStringSize(text)
        try:
          r, g, b = self.engine.theme.hexToColorResults(self.engine.theme.result_stats_name[3])
          glColor3f(r, g, b)
        except IndexError:
          self.engine.theme.setBaseColor(1-v)
        font.render(text, (float(self.engine.theme.result_stats_name[0]) - wText / 2, float(self.engine.theme.result_stats_name[1]) + v), scale = float(self.engine.theme.result_stats_name[2]))
        
        if self.engine.theme.result_stats_part_text.strip() == "$icon$" and not self.partImage:
          text = "%s"
        else:
          text = self.engine.theme.result_stats_part_text.strip()
        
        if text == "$icon$" and self.partImage:
          self.engine.drawImage(self.part[i], scale = (float(self.engine.theme.result_stats_part[2]),-float(self.engine.theme.result_stats_part[2])), coord = (w*float(self.engine.theme.result_stats_part[0]),h*float(self.engine.theme.result_stats_part[1])))
        else:
          try:
            text = text % self.playerList[i].part
          except TypeError:
            text = "%s %s" % (text, self.playerList[i].part)
          try:
            font = self.engine.data.fontDict[self.engine.theme.result_stats_part[4]]
          except:
            font = defFont
          wText, hText = font.getStringSize(text)
          try:
            r, g, b = self.engine.theme.hexToColorResults(self.engine.theme.result_stats_part[3])
            glColor3f(r, g, b)
          except IndexError:
            self.engine.theme.setBaseColor(1-v)
          font.render(text, (float(self.engine.theme.result_stats_part[0]) - wText / 2, float(self.engine.theme.result_stats_part[1]) + v), scale = float(self.engine.theme.result_stats_part[2]))
  
  def renderCheatList(self, visibility, topMost):
    bigFont = self.engine.data.bigFont
    try:
      font  = self.engine.data.fontDict[self.engine.theme.result_cheats_font]
    except KeyError:
      font  = self.engine.data.font
    
    if self.coOpType > 0:
      self.engine.view.setViewport(1,0)
    
    v = ((1 - visibility) **2)
    w, h = self.fullView
    for i, scoreCard in enumerate(self.scoring): #receiving with sliced viewport!
      if len(self.cheats[i]) == 0:
        continue
      if self.resultStep == 1:
        try:
          text  = self.cheats[i][self.finishedCheat[i]][0]
          text2 = "%.1f%%" % (self.cheats[i][self.finishedCheat[i]][1] * 100)
          text3 = self.totalHandicap[i]
          text4 = self.originalScore[i]
        except IndexError:
          continue
      else:
        text  = ""
        text2 = ""
        for j in range(len(self.cheats[i])):
          text  += self.cheats[i][j][0]
          if j < len(self.cheats[i])-1:
            text += ", "
          if j > 0:
            text2 += " x "
          text2 += "%.1f%%" % (self.cheats[i][j][1] * 100)
        text3 = self.totalHandicap[i]
        text4 = self.originalScore[i]
      wText, hText = font.getStringSize(text, scale = float(self.engine.theme.result_cheats_info[2]))
      try:
        r, g, b = self.engine.theme.hexToColorResults(self.engine.theme.result_cheats_color)
        glColor3f(r, g, b)
      except IndexError:
        self.engine.theme.setBaseColor(1-v)
      font.render(text, (float(self.engine.theme.result_cheats_info[0]) - wText / 2, float(self.engine.theme.result_cheats_info[1]) + v), scale = float(self.engine.theme.result_cheats_info[2]))
      wText, hText = font.getStringSize(text2, scale = .0015)
      font.render(text2, (float(self.engine.theme.result_cheats_numbers[0]) - wText / 2, float(self.engine.theme.result_cheats_numbers[1]) + v), scale = float(self.engine.theme.result_cheats_numbers[2]))
      text = "%s %.1f%%" % (self.tsHandicap, text3)
      wText, hText = font.getStringSize(text, scale = float(self.engine.theme.result_cheats_percent[2]))
      font.render(text, (float(self.engine.theme.result_cheats_percent[0]) - wText / 2, float(self.engine.theme.result_cheats_percent[1]) + v), scale = float(self.engine.theme.result_cheats_percent[2]))
      text = "%s %d" % (self.tsOriginal, text4)
      wText, hText = font.getStringSize(text2, scale = float(self.engine.theme.result_cheats_score[2]))
      font.render(text, (float(self.engine.theme.result_cheats_score[0]) - wText / 2, float(self.engine.theme.result_cheats_score[1]) + v), scale = float(self.engine.theme.result_cheats_score[2]))
  
  def renderHighScores(self, visibility, topMost):
    if self.coOpType == 0:
      self.engine.view.setViewport(1,0)

    bigFont = self.engine.data.bigFont
    try:
      font  = self.engine.data.fontDict[self.engine.theme.result_high_score_font]
    except KeyError:
      font  = self.engine.data.font
    Dialogs.fadeScreen(.2)
    v = ((1 - visibility) **2)
    
    w, h = self.fullView

    scale = 0.0017
    endScroll = -.14
    
    # evilynux - highscore
    if self.song is not None:
      text = _("%s High Scores for %s") % (self.scorePart, Song.removeSongOrderPrefixFromName(self.song.info.name))
    else:
      text = _("%s High Scores") % self.scorePart
    w1, h1 = font.getStringSize(text)
    
    self.engine.theme.setBaseColor(1 - v)
    font.render(text, (.5 - w1 / 2, .01 - v + self.offset))
    
    text = _("Difficulty: %s") % (self.scoreDifficulty)
    w1, h1 = font.getStringSize(text)
    self.engine.theme.setBaseColor(1 - v)
    font.render(text, (.5 - w1 / 2, .01 - v + h1 + self.offset))
    
    x = .01
    y = .16 + v
    
    if self.song:
      i = -1
      for i, scores in enumerate(self.song.info.getHighscores(self.scoreDifficulty, part = self.scorePart)):
        score, stars, name, scoreExt = scores
        try:
          notesHit, notesTotal, noteStreak, modVersion, handicap, handicapLong, originalScore = scoreExt
        except ValueError:
          Log.warn("Old highscores found.")
          notesHit, notesTotal, noteStreak, modVersion, oldScores1, oldScores2 = scoreExt
          handicap = 0
          handicapLong = "None"
          originalScore = score
        for j,player in enumerate(self.playerList):
          if (self.time % 10.0) < 5.0 and i == self.highscoreIndex[j] and self.scoreDifficulty == player.difficulty and self.scorePart == player.part:
            self.engine.theme.setSelectedColor(1 - v)
            break
          else:
            self.engine.theme.setBaseColor(1 - v)
        font.render("%d." % (i + 1), (x, y + self.offset),    scale = scale)
        if notesTotal != 0:
          score = "%s %.1f%%" % (score, (float(notesHit) / notesTotal) * 100.0)
        if noteStreak != 0:
          score = "%s (%d)" % (score, noteStreak)
        font.render(unicode(score), (x + .05, y + self.offset),   scale = scale)
        options = ""
        w2, h2 = font.getStringSize(options, scale = scale / 2)
        font.render(unicode(options), (.6 - w2, y + self.offset),   scale = scale / 2)
        # evilynux - Fixed star size following Font render bugfix
        # akedrou  - Fixed stars to render as stars after custom glyph removal... ...beautiful yPos
        #font.render(unicode(Data.STAR2 * stars + Data.STAR1 * (5 - stars)), (x + .6, y + self.offset), scale = scale * 1.8)
        self.engine.drawStarScore(w, h, x+.6, 1.0-((y+self.offset+h2)/self.engine.data.fontScreenBottom), stars, scale * 15)

        for j,player in enumerate(self.playerList):
          if (self.time % 10.0) < 5.0 and i == self.highscoreIndex[j] and self.scoreDifficulty == player.difficulty and self.scorePart == player.part:
            self.engine.theme.setSelectedColor(1 - v)
            break
          else:
            self.engine.theme.setBaseColor(1 - v)
        font.render(name, (x + .8, y + self.offset), scale = scale)
        y += h1
        endScroll -= .07
      
      if self.offset < endScroll or (i == -1 and self.doneScores):
        self.offset = self.scoreScrollStartOffset
        self.hsRollIndex += 1
        self.nextHighScore()
    
    for j,player in enumerate(self.playerList): #MFH 
      if self.uploadingScores[j]:
        sScale = 0.001
        sW, sH = font.getStringSize("A", scale = sScale)
        sYPos = .7 - ( (sH * 1.25) * j)
        self.engine.theme.setBaseColor(1 - v)
        if self.uploadResponse[j] is None:
          upScoreText = _("Uploading Scores...")
          font.render("P%d (%s) %s" % (j+1, player.upname, upScoreText), (.05, sYPos + v), scale = sScale)
        else:
          result = str(self.uploadResponse[j]).split(";")
          if len(result) > 0:
            upScoreText1 = _("Scores uploaded!")
            if result[0] == "True":
              #MFH - display rank if it was successful
              if len(result) > 1:
                upScoreText2 = _("Your highscore ranks")
                upScoreText3 = _("on the world starpower chart!")
                font.render("P%d (%s) %s %s  ... %s #%d %s" % (j+1, player.upname, player.part.text, upScoreText1, upScoreText2, int(result[1]), upScoreText3), (.05, sYPos + v), scale = sScale)
              else:
                upScoreText2 = _("but your rank is unknown.")
                font.render("P%d (%s) %s %s  ... %s" % (j+1, player.upname, player.part.text, upScoreText1, upScoreText2), (.05, sYPos + v), scale = sScale)
            else:
              upScoreText2 = _("but there was no new highscore.")
              font.render("P%d (%s) %s %s  ... %s" % (j+1, player.upname, player.part.text, upScoreText1, upScoreText2), (.05, sYPos + v), scale = sScale)
          else:
            upScoreText1 = _("Score upload failed!  World charts may be down.")
            font.render("P%d (%s) %s %s" % (j+1, player.upname, player.part.text, upScoreText1), (.05, sYPos + v), scale = sScale)
  
  def renderStats(self, visibility, topMost):
    pass #to be added.
