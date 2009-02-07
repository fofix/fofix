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

from Scene import SceneServer, SceneClient
import Player
import Scorekeeper
import Dialogs
import Song
import Data
import Theme
from Menu import Menu
from Audio import Sound
from Language import _

import Config
import sha
import Cerealizer
import binascii
import urllib
import Log

import pygame
import math
import random
import os
from OpenGL.GL import *


class GameResultsScene:
  pass

class GameResultsSceneServer(GameResultsScene, SceneServer):
  pass

class GameResultsSceneClient(GameResultsScene, SceneClient):
  def createClient(self, libraryName, songName, players = 1, scores = None, coOpType = False, careerMode = False):
  
    self.logClassInits = self.engine.config.get("game", "log_class_inits")
    if self.logClassInits == 1:
      Log.debug("GameResultsSceneClient class init...")

    self.libraryName      = libraryName
    self.cheats           = [[] for i in scores]
    self.numCheats        = [0 for i in scores]
    self.songName         = songName
    self.coOpType         = coOpType
    self.careerMode       = careerMode
    self.counter          = 0
    self.animationTimer   = 0
    self.scoreRollTimer   = [0 for i in scores]
    self.delay            = [0 for i in scores]
    self.waiting          = False
    self.resultStep       = 0
    self.resultSubStep    = [0 for i in scores]
    self.currentCheat     = [0 for i in scores]
    self.finishedCheat    = [-1 for i in scores]
    self.scoring          = scores
    self.currentScore     = [0 for i in scores]
    self.newScore         = [0 for i in scores]
    self.diffScore        = [0 for i in scores]
    self.totalHandicap    = [100.0 for i in scores]
    self.progressReady    = False
    self.rolling          = [False for i in scores]
    self.space            = [1 for i in scores]
    self.finalScore       = [0 for i in scores]
    self.originalScore    = [0 for i in scores]
    self.cheatsApply      = True
    self.showHighscores   = False
    self.singleView       = False
    self.highscoreIndex   = [-1 for i in players]
    self.haveRunScores    = False
    self.doneScores       = False
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
    self.nextScene        = None
    self.offset           = .8
    self.pctRoll          = 0.0
    self.vis              = 1.0
    self.pauseScroll      = None
    self.careerStars      = self.engine.config.get("game", "career_star_min")
    self.detailedScores   = False #to do.
    self.playerList       = players
    
    self.scoreScrollStartOffset = .8
    
    self.coOpDiff    = _("Co-Op Mode") #To be changed to something.
    self.coOpPart    = _("Co-Op Mode") #To be changed to something.
    
    self.tsSettings  = _("settings")
    self.tsHopos     = _("HOPOs")
    self.tsHitWindow = _("Hit Window")
    self.tsHandicap  = _("Adjusted Score Multiplier:")
    self.tsOriginal  = _("Original Score:")
    
    items = [
      (_("Continue"),       self.changeSong),
      (_("Replay"),         self.replay),
      #(_("Detailed Stats"), self.stats), #akedrou - to do
      (_("Quit"),           self.quit),
    ]
    
    self.menu = Menu(self.engine, items, onCancel = self.quit, pos = (.2, .5))
    
    self.engine.resource.load(self, "song", lambda: Song.loadSong(self.engine, songName, library = self.libraryName, notesOnly = True, part = [player.part for player in self.playerList]), onLoad = self.songLoaded)
    
    #Get theme information
    themename  = self.engine.data.themeLabel
    self.theme = self.engine.data.theme
    
    self.loaded = False
    
    self.fullView = self.engine.view.geometry[2:4]
    
    self.congratPhrase = self.engine.config.get("game", "congrats")
    self.keepCount     = self.engine.config.get("game", "keep_play_count")
    
    self.resultCheerLoop = self.engine.config.get("game", "result_cheer_loop")
    
    self.starScoring = self.engine.config.get("game", "star_scoring")
    self.starMass    = [0 for i in self.playerList]
    
    self.cheerLoopDelay  = Theme.crowdLoopDelay
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
    
    slowdown = self.engine.config.get("audio", "speed_factor")
    a = len(Scorekeeper.HANDICAPS)
    for i, scoreCard in enumerate(self.scoring):
      self.finalScore[i]    = scoreCard.score
      self.originalScore[i] = scoreCard.score
      if self.starScoring == 0: #FoF-mode
        self.starMass[i] = 100 * scoreCard.stars
      
      for j in range(a):
        if (scoreCard.handicap>>j)&1 == 1:
          if Scorekeeper.HANDICAPS[j] == 1.0: #audio divisor - added to long handicap.
            cut = (100.0**slowdown)/100.0
            self.cheats[i].append((Scorekeeper.HANDICAP_NAMES[(a-1)-j], cut))
            self.finalScore[i] = int(self.finalScore[i] * cut)
            scoreCard.longHandicap += "aud,%.2f," % slowdown
          else:
            self.cheats[i].append((Scorekeeper.HANDICAP_NAMES[(a-1)-j], Scorekeeper.HANDICAPS[j]))
            self.finalScore[i] = int(self.finalScore[i] * Scorekeeper.HANDICAPS[i])
    
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
    hopoFreqCheat   = self.engine.config.get("coffee", "hopo_freq_cheat")
    noteHitWindow   = self.engine.config.get("game", "note_hit_window")
    hitWindowCheat  = self.engine.config.get("game", "hit_window_cheat")
    try:
      songHopoFreq  = abs(int(songHopoFreq))
    except Exception, e:
      songHopoFreq  = 10
    if useSongHopoFreq == 1 and songHopoFreq < 6:
      self.hopoFreq = songHopoFreq
    
    if hopoFreqCheat == 1:
      self.hopoFreq = _("More")
    elif hopoFreqCheat == 2:
      self.hopoFreq = _("Even More")
    elif self.hopoFreq == 0:
      self.hopoFreq = _("Least")
    elif self.hopoFreq == 1:
      self.hopoFreq = _("Less")
    elif self.hopoFreq == 2:
      self.hopoFreq = _("Normal")
    elif self.hopoFreq == 3:
      self.hopoFreq = _("Most")
    
    if hitWindowCheat == 1:
      self.hitWindow = _("Widest")
    elif hitWindowCheat == 2:
      self.hitWindow = _("Wide")
    elif noteHitWindow == 2:
      self.hitWindow = _("Tightest")
    elif noteHitWindow == 1:
      self.hitWindow = _("Tight")
    else:
      self.hitWindow = _("Standard")
    
    jurgen   = self.engine.config.get("game", "jurgmode")
    jurgplay = self.engine.config.get("game", "jurgtype")
    
    self.progressKeys   = []
    self.progressKeys.extend(Player.KEY1S)
    self.progressKeys.extend(Player.KEY2S)
    self.progressKeys.extend(Player.CANCELS)
    self.progressKeys.extend(Player.DRUM1S)
    self.progressKeys.extend(Player.DRUM4S)
    self.p1ProgressKeys = [Player.KEY1, Player.KEY2, Player.CANCEL, Player.DRUM1A, Player.DRUM4A]
    self.p2ProgressKeys = [Player.PLAYER_2_KEY1, Player.PLAYER_2_KEY2, Player.PLAYER_2_CANCEL, Player.PLAYER_2_DRUM1A, Player.PLAYER_2_DRUM4A]
    if jurgen == 0:
      if jurgplay == 1:
        self.p2ProgressKeys = self.progressKeys
      else:
        self.p1ProgressKeys = self.progressKeys
        self.p2ProgressKeys = self.progressKeys
    
    self.maskStars = False
    self.fcStars   = True
    self.engine.loadImgDrawing(self, "background", os.path.join("themes", themename, "gameresults.png"))
    try:
      self.engine.loadImgDrawing(self, "star3", os.path.join("themes",themename,"star3.png"))
      self.engine.loadImgDrawing(self, "star4", os.path.join("themes",themename,"star4.png"))
    except IOError:
      self.engine.loadImgDrawing(self, "star3", os.path.join("themes",themename,"star1.png"))
      self.engine.loadImgDrawing(self, "star4", os.path.join("themes",themename,"star2.png"))
    try:
      self.engine.loadImgDrawing(self, "star5", os.path.join("themes",themename,"star5.png"))
      self.engine.loadImgDrawing(self, "star6", os.path.join("themes",themename,"star6.png"))
    except IOError:
      try:
        self.engine.loadImgDrawing(self, "star5", os.path.join("themes",themename,"starperfect.png"))
        self.star6   = None
        self.fcStars = False
      except IOError:
        self.engine.loadImgDrawing(self, "star5", os.path.join("themes",themename,"star2.png"))
        self.star6     = None
        self.fcStars   = False
        self.maskStars = True

    
    phrase = random.choice(Theme.resultsPhrase.split("_"))
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
    Dialogs.showLoadingScreen(self.engine, lambda: self.song, text = phrase)
    
  def handleWorldCharts(self, result):
    self.uploadResponse[self.resultNum] = self.uploadResult
    self.resultNum += 1
  
  def keyPressed(self, key, unicode):
    ret = SceneClient.keyPressed(self, key, unicode)
    c = self.controls.keyPressed(key)
    
    if self.song and (c in self.progressKeys or key == pygame.K_RETURN or key == pygame.K_ESCAPE):
      if self.progressReady:
        self.resultStep += 1
        self.resultSubStep = [0 for i in self.scoring]
        self.progressReady = False
      for i in range(len(self.scoring)):
        if self.coOpType:
          if self.rolling[i]:
            self.skipRoll(i)
            self.skipShrink(i)
          if self.delay[i] > 0:
            self.skipDelay(i)
          break
        elif i == 0 and (c in self.p1ProgressKeys or key == pygame.K_RETURN or key == pygame.K_ESCAPE):
          if self.rolling[i]:
            self.skipRoll(i)
            self.skipShrink(i)
          if self.delay[i] > 0:
            self.skipDelay(i)
          break
        elif i == 1 and (c in self.p2ProgressKeys or key == pygame.K_RETURN or key == pygame.K_ESCAPE):
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
  
  def hidden(self):
    SceneClient.hidden(self)
    if self.nextScene:
      self.nextScene()
  
  def quit(self):
    self.background = None
    self.song = None
    self.engine.view.popLayer(self.menu)
    self.session.world.finishGame()
  
  def replay(self):
    self.background = None
    self.song = None
    self.engine.view.popLayer(self.menu)
    self.session.world.deleteScene(self)
    self.nextScene = lambda: self.session.world.createScene("GuitarScene", libraryName = self.libraryName, songName = self.songName, Players = len(self.playerList))
  
  def changeSong(self):
    self.background = None
    self.song = None
    self.engine.view.popLayer(self.menu)
    self.session.world.deleteScene(self)
    self.nextScene = lambda: self.session.world.createScene("SongChoosingScene")
  
  def stats(self):
    self.detailedScores = True
  
  def songLoaded(self, song):
    for i, player in enumerate(self.playerList):
      song.difficulty[i] = player.difficulty
    
    self.loaded = True
  
  def nextHighScore(self):
    if self.scoreDifficulty == None:
      self.scoreDifficulty = self.playerList[self.hsRollIndex].difficulty
    if self.scorePart == None:
      self.scorePart = self.playerList[self.hsRollIndex].part
      return
    
    found = 0  
    for part in self.song.info.parts:
      for difficulty in self.song.info.difficulties:
        if found == 1:
          self.scoreDifficulty = difficulty
          self.scorePart = part
          return
        
        if self.scoreDifficulty == difficulty and self.scorePart == part:
          found = 1

    self.scoreDifficulty = self.song.info.difficulties[0]
    self.scorePart = self.song.info.parts[0]
  
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
        "songName": "%s" % (Dialogs.removeSongOrderPrefixFromName(self.song.info.name)),
        "songHash": self.song.getHash(),
        "scores":   None,
        "scores_ext": None,
        "version":  self.engine.uploadVersion,
        "songPart": part
      }
      scores     = {}
      scores_ext = {}
      scoreHash = sha.sha("%d%d%d%s" % (player.getDifficultyInt(), self.finalScore[i], self.scoring[i].stars, self.playerList[i].name)).hexdigest()
      scores[player.getDifficultyInt()]     = [(self.finalScore[i], self.scoring[i].stars, self.playerList[i].name, scoreHash)]
      scores_ext[player.getDifficultyInt()] = [(scoreHash, self.scoring[i].stars) + scoreExt]
      d["scores"] = binascii.hexlify(Cerealizer.dumps(scores))
      d["scores_ext"] = binascii.hexlify(Cerealizer.dumps(scores_ext))
      url = self.engine.config.get("game", "uploadurl_w67_starpower")
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
        name = Dialogs.getText(self.engine, _("%d points is a new high score! Enter your name:") % self.finalScore[i], self.playerList[i].name)
        if name:
          self.playerList[i].name = name
        scoreExt = (scoreCard.notesHit, scoreCard.totalStreakNotes, scoreCard.hiStreak, self.engine.uploadVersion, scoreCard.handicap, scoreCard.longHandicap, self.originalScore[i])
        self.highscoreIndex[i] = self.song.info.addHighscore(self.playerList[i].difficulty, self.finalScore[i], scoreCard.stars, self.playerList[i].name, part = self.playerList[i].part, scoreExt = scoreExt)
        self.song.info.save()
        
        if self.engine.config.get("game", "uploadscores"):
          self.uploadingScores[i] = True
          fn = lambda: self.uploadHighscores(part = self.playerList[i].part, playerNum = i, scoreExt = scoreExt)
          
          self.engine.resource.load(self, "uploadResult", fn, onLoad = self.handleWorldCharts)
    self.doneScores = True
  
  def run(self, ticks):
    SceneClient.run(self, ticks)
    
    self.time           += ticks / 50.0
    self.counter        += ticks
    self.animationTimer += ticks
    
    if self.resultStep == 0 and self.loaded:
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
      for i, scoreCard in enumerate(self.scoring):
        if self.resultSubStep[i] == 0:
          if self.currentCheat[i] < len(self.cheats[i]):
            self.scoreRollTimer[i] += ticks
            if self.finishedCheat[i] == -1:
              scoreCard.cheatsApply = True
              self.cheatsApply = True
            if not self.rolling[i]:
              if self.delay[i] == 0 and self.finishedCheat[i] < self.currentCheat[i] and not self.waiting:
                self.newScore[i] = int(self.currentScore[i] * self.cheats[i][self.currentCheat[i]][1])
                self.totalHandicap[i] *= self.cheats[i][self.currentCheat[i]][1]
                if self.starScoring == 0:
                  self.starMass[i] *= self.cheats[i][self.currentCheat[i]][1]
                  scoreCard.stars = min(int(self.starMass[i]/100),5)
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
                if star > scoreCard.stars and self.engine.data.starLostSoundFound:
                  self.engine.data.starLostSound.play()
          else:
            self.resultSubStep[i] += 1
      
      if min(self.resultSubStep) > 0:
        self.progressReady = True
    
    if self.resultStep == 2:
      if not self.coOpType:
        for i, player in enumerate(self.playerList):
          if self.finalScore[i] == 0:
            self.noScore[i] = True
        if not self.haveRunScores:
          self.runScores()

        if self.doneScores:
          if len(self.playerList) > 1 and self.playerList[0].part == self.playerList[1].part and self.playerList[0].difficulty == self.playerList[1].difficulty and self.highscoreIndex[0] != -1 and self.highscoreIndex[1] != -1 and self.highscoreIndex[1] <= self.highscoreIndex[0]:
            self.highscoreIndex[0] += 1
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
    
    if self.resultStep > 3:
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
    SceneClient.render(self, visibility, topMost)
    
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_COLOR_MATERIAL)
    
    self.engine.view.setOrthogonalProjection(normalize = True)
    
    try:
      if self.detailedScores:
        self.renderStats(visibility, topMost)
      else:
        self.renderInitialScore(visibility, topMost)
        if self.resultStep > 0:
          self.renderCheatList(visibility, topMost)
        if self.resultStep > 2:
          self.renderHighScores(visibility, topMost)
    
    finally:
      self.engine.view.resetProjection()
  
  def renderInitialScore(self, visibility, topMost):
    bigFont = self.engine.data.bigFont
    font    = self.engine.data.font
    
    v = ((1 - visibility) **2)
    
    w, h = self.fullView
    if self.background:
      wFactor = 640.000/self.background.width1()
      self.engine.drawImage(self.background, scale = (wFactor,-wFactor), coord = (w/2,h/2))
    
    Theme.setBaseColor(1-v)
    
    if self.song:
      try:
        text = Theme.result_song_text % Dialogs.removeSongOrderPrefixFromName(self.song.info.name)
      except TypeError:
        text = "%s %s" % (Dialogs.removeSongOrderPrefixFromName(self.song.info.name), Theme.result_song_text)
      
      wText, hText = font.getStringSize(text, scale = float(Theme.result_song[2]))
      Dialogs.wrapText(font, (float(Theme.result_song[0]), float(Theme.result_song[1]) - v), text, 0.9, float(Theme.result_song[2]))
      
      for i, scoreCard in enumerate(self.scoring):
        self.engine.view.setViewportHalf(len(self.scoring),i)
        
        text = "%d/%d" % (scoreCard.notesHit, scoreCard.totalStreakNotes)
        try:
          text = Theme.result_stats_notes_text % text
        except TypeError:
          text = "%s %s" % (text, Theme.result_stats_notes_text)
        wText, hText = font.getStringSize(text, scale = float(Theme.result_stats_notes[2]))
        Dialogs.wrapText(font, (float(Theme.result_stats_notes[0]) - wText/2, float(Theme.result_stats_notes[1]) + v), text, 0.9, float(Theme.result_stats_notes[2]))
        
        text = "%d" % self.currentScore[i]
        wText, hText = bigFont.getStringSize(text, scale = float(Theme.result_score[2]))
        bigFont.render(text, (float(Theme.result_score[0]) - wText / 2, float(Theme.result_score[1]) + v), scale = float(Theme.result_score[2]))
        
        if self.resultStep == 0:
          space = self.space[i]
        else:
          space = 1
        
        if scoreCard.stars > 5:
          for j in range(5):
            if self.fcStars and scoreCard.stars == 7:
              star = self.star6
            else:
              star = self.star5
            try:
              wide = star.width1()*float(Theme.result_star[3])
            except IndexError:
              wide = star.width1()*.5
            if self.maskStars:
              if self.theme == 2:
                self.engine.drawImage(star, scale = (float(Theme.result_star[2]),-float(Theme.result_star[2])), coord = (((w*Theme.result_star[0])+wide*j)*space**4,h*float(Theme.result_star[1])), color = (1, 1, 0, 1))
              else:
                self.engine.drawImage(star, scale = (float(Theme.result_star[2]),-float(Theme.result_star[2])), coord = (((w*float(Theme.result_star[0]))+wide*j)*space**4,h*float(Theme.result_star[1])), color = (0, 1, 0, 1))
            else:
              self.engine.drawImage(star, scale = (float(Theme.result_star[2]),-float(Theme.result_star[2])), coord = (((w*float(Theme.result_star[0]))+wide*j)*space**4,h*float(Theme.result_star[1])))
        else:
          for j in range(5):
            if j < scoreCard.stars:
              star = self.star4
            else:
              star = self.star3
            wide = star.width1()*.5
            self.engine.drawImage(star, scale = (float(Theme.result_star[2]),-float(Theme.result_star[2])), coord = (((w*float(Theme.result_star[0]))+wide*j)*space**4,h*float(Theme.result_star[1])))
        
        settingsText = "%s %s - %s: %s / %s, %s: %s" % (self.engine.versionString, self.tsSettings, self.tsHopos, self.hopoStyle, self.hopoFreq, self.tsHitWindow, self.hitWindow)
        settingsScale = 0.0012
        wText, hText = font.getStringSize(settingsText, settingsScale)
        font.render(settingsText, (.5 - wText/2, 0.0), scale = settingsScale)
        
        text = _(Theme.result_stats_accuracy_text) % scoreCard.hitAccuracy
        wText, hText = font.getStringSize(text)
        try:
          r, g, b = Theme.hexToColorResults(Theme.result_stats_accuracy[3])
          glColor3f(r, g, b)
        except IndexError:
          Theme.setBaseColor(1-v)
        font.render(text, (float(Theme.result_stats_accuracy[0]) - wText / 2, float(Theme.result_stats_accuracy[1]) + v), scale = float(Theme.result_stats_accuracy[2]))
        
        text = _(Theme.result_stats_streak_text) % scoreCard.hiStreak
        wText, hText = font.getStringSize(text)
        try:
          r, g, b = Theme.hexToColorResults(Theme.result_stats_streak[3])
          glColor3f(r, g, b)
        except IndexError:
          Theme.setBaseColor(1-v)
        font.render(text, (float(Theme.result_stats_streak[0]) - wText / 2, float(Theme.result_stats_streak[1]) + v), scale = float(Theme.result_stats_streak[2]))
        
        text = _(Theme.result_stats_diff_text) % self.playerList[i].difficulty
        if self.coOpType:
          text = _(Theme.result_stats_diff_text) % self.coOpDiff
        wText, hText = font.getStringSize(text)
        try:
          r, g, b = Theme.hexToColorResults(Theme.result_stats_diff[3])
          glColor3f(r, g, b)
        except IndexError:
          Theme.setBaseColor(1-v)
        font.render(text, (float(Theme.result_stats_diff[0]) - wText / 2, float(Theme.result_stats_diff[1]) + v), scale = float(Theme.result_stats_diff[2]))
        
        text = _(Theme.result_stats_part_text) % self.playerList[i].part
        if self.coOpType:
          text = _(Theme.result_stats_part_text) % self.coOpPart
        wText, hText = font.getStringSize(text)
        try:
          r, g, b = Theme.hexToColorResults(Theme.result_stats_part[3])
          glColor3f(r, g, b)
        except IndexError:
          Theme.setBaseColor(1-v)
        font.render(text, (float(Theme.result_stats_part[0]) - wText / 2, float(Theme.result_stats_part[1]) + v), scale = float(Theme.result_stats_part[2]))
  
  def renderCheatList(self, visibility, topMost):
    bigFont = self.engine.data.bigFont
    font    = self.engine.data.font
    
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
      wText, hText = font.getStringSize(text, scale = float(Theme.result_cheats_info[2]))
      try:
        r, g, b = Theme.hexToColorResults(Theme.result_cheats_color)
        glColor3f(r, g, b)
      except IndexError:
        Theme.setBaseColor(1-v)
      font.render(text, (float(Theme.result_cheats_info[0]) - wText / 2, float(Theme.result_cheats_info[1]) + v), scale = float(Theme.result_cheats_info[2]))
      wText, hText = font.getStringSize(text2, scale = .0015)
      font.render(text2, (float(Theme.result_cheats_numbers[0]) - wText / 2, float(Theme.result_cheats_numbers[1]) + v), scale = float(Theme.result_cheats_numbers[2]))
      text = "%s %.1f%%" % (self.tsHandicap, text3)
      wText, hText = font.getStringSize(text, scale = float(Theme.result_cheats_percent[2]))
      font.render(text, (float(Theme.result_cheats_percent[0]) - wText / 2, float(Theme.result_cheats_percent[1]) + v), scale = float(Theme.result_cheats_percent[2]))
      text = "%s %d" % (self.tsOriginal, text4)
      wText, hText = font.getStringSize(text2, scale = float(Theme.result_cheats_score[2]))
      font.render(text, (float(Theme.result_cheats_score[0]) - wText / 2, float(Theme.result_cheats_score[1]) + v), scale = float(Theme.result_cheats_score[2]))
  
  def renderHighScores(self, visibility, topMost):
    self.engine.view.setViewport(1,0)
    bigFont = self.engine.data.bigFont
    font    = self.engine.data.font
    Dialogs.fadeScreen(.4)
    v = ((1 - visibility) **2)
    
    w, h = self.fullView
    
    for j,player in enumerate(self.playerList):
      scale = 0.0017
      endScroll = -.14
      
      if self.pauseScroll != None:
        self.offset = 0.0
      
      if self.pauseScroll > 0.5:
        self.pauseScroll = None
      if self.offset == None:
        self.offset = 0
        self.pauseScroll = 0
        self.nextHighScore()
      
      
      # evilynux - highscore
      if self.song is not None:
        text = _("%s High Scores for %s") % (self.scorePart, Dialogs.removeSongOrderPrefixFromName(self.song.info.name))
      else:
        text = _("%s High Scores") % self.scorePart
      w, h = font.getStringSize(text)
      
      Theme.setBaseColor(1 - v)
      font.render(text, (.5 - w / 2, .01 - v + self.offset))
      
      text = _("Difficulty: %s") % (self.scoreDifficulty)
      w, h = font.getStringSize(text)
      Theme.setBaseColor(1 - v)
      font.render(text, (.5 - w / 2, .01 - v + h + self.offset))
      
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
        if stars == 7: #akedrou
          stars = 5
          perfect = 2
        if stars == 6:
          stars = 5
          perfect = 1
        else:
          perfect = 0
        for j,player in enumerate(self.playerList):
          if (self.time % 10.0) < 5.0 and i == self.highscoreIndex[j] and self.scoreDifficulty == player.difficulty and self.scorePart == player.part:
            Theme.setSelectedColor(1 - v)
            break
          else:
            Theme.setBaseColor(1 - v)
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
        if perfect == 2: #akedrou - 7-star (FC) support
          glColor3f(0, .5, 1) # these should be customizable.
        elif perfect == 1 and self.theme == 2:
          glColor3f(1, 1, 0) #racer: perfect is now gold for rock band
        elif perfect == 1 and self.theme < 2:
          glColor3f(0, 1, 0) #racer: perfect is green for any non-RB theme
        font.render(unicode(Data.STAR2 * stars + Data.STAR1 * (5 - stars)), (x + .6, y + self.offset), scale = scale * 1.8)
        for j,player in enumerate(self.playerList):
          if (self.time % 10.0) < 5.0 and i == self.highscoreIndex[j] and self.scoreDifficulty == player.difficulty and self.scorePart == player.part:
            Theme.setSelectedColor(1 - v)
            break
          else:
            Theme.setBaseColor(1 - v)
        font.render(name, (x + .8, y + self.offset), scale = scale)
        y += h
        endScroll -= .07
      
      if self.offset < endScroll or i == -1:
        self.offset = self.scoreScrollStartOffset
        self.nextHighScore()
        endScroll = -0.14
    
    for j,player in enumerate(self.playerList): #MFH 
      if self.uploadingScores[j]:
        sScale = 0.001
        sW, sH = font.getStringSize("A", scale = sScale)
        sYPos = .7 - ( (sH * 1.25) * j)
        Theme.setBaseColor(1 - v)
        if self.uploadResponse[j] is None:
          upScoreText = _("Uploading Scores...")
          font.render("P%d (%s) %s" % (j+1, player.name, upScoreText), (.05, sYPos + v), scale = sScale)
        else:
          result = str(self.uploadResponse[j]).split(";")
          if len(result) > 0:
            upScoreText1 = _("Scores uploaded!")
            if result[0] == "True":
              #MFH - display rank if it was successful
              if len(result) > 1:
                upScoreText2 = _("Your highscore ranks")
                upScoreText3 = _("on the world starpower chart!")
                font.render("P%d (%s) %s %s  ... %s #%d %s" % (j+1, player.name, player.part.text, upScoreText1, upScoreText2, int(result[1]), upScoreText3), (.05, sYPos + v), scale = sScale)
              else:
                upScoreText2 = _("but your rank is unknown.")
                font.render("P%d (%s) %s %s  ... %s" % (j+1, player.name, player.part.text, upScoreText1, upScoreText2), (.05, sYPos + v), scale = sScale)
            else:
              upScoreText2 = _("but there was no new highscore.")
              font.render("P%d (%s) %s %s  ... %s" % (j+1, player.name, player.part.text, upScoreText1, upScoreText2), (.05, sYPos + v), scale = sScale)
          else:
            upScoreText1 = _("Score upload failed!  World charts may be down.")
            font.render("P%d (%s) %s %s" % (j+1, player.name, player.part.text, upScoreText1), (.05, sYPos + v), scale = sScale)
  
  def renderStats(self, visibility, topMost):
    pass #to be added.
