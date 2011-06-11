#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire                                                     #
# Copyright (C) 2006 Sami Kyostila                                  #
#               2008 Alarian                                        #
#               2008 myfingershurt                                  #
#               2008 Capo                                           #
#               2008 Glorandwarf                                    #
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

from Neck import Neck
from copy import deepcopy
from Shader import shaders

from Instrument import *
from OpenGL.GL import *

class Guitar(Instrument):
  def __init__(self, engine, playerObj, editorMode = False, player = 0, bass = False):
    Instrument.__init__(self, engine, playerObj, player)

    self.isDrum = False
    self.isBassGuitar = bass
    self.isVocal = False

    self.strings        = 5

    self.debugMode = False
    self.gameMode2p = self.engine.world.multiMode
    self.matchingNotes = []
            
    self.logClassInits = self.engine.config.get("game", "log_class_inits")
    if self.logClassInits == 1:
      Log.debug("Guitar class init...")
    
    self.lastPlayedNotes = []   #MFH - for reverting when game discovers it implied incorrectly
    
    self.missedNotes    = []
    self.missedNoteNums = []
    self.editorMode     = editorMode

    self.freestyleHitFlameCounts = [0 for n in range(self.strings+1)]    #MFH

    self.fretWeight     = [0.0] * self.strings
    self.fretActivity   = [0.0] * self.strings

    self.drumFretButtons = None

    #myfingershurt:
    self.hopoStyle        = self.engine.config.get("game", "hopo_system")
    self.gh2sloppy        = self.engine.config.get("game", "gh2_sloppy")
    if self.gh2sloppy == 1:
      self.hopoStyle = 4
    self.sfxVolume    = self.engine.config.get("audio", "SFX_volume")
    
    #blazingamer
    self.killfx = self.engine.config.get("performance", "killfx")
    self.killCount         = 0
    
    self.bigMax = 1
    
    #Get theme
    #now theme determination logic is only in data.py:
    self.theme = self.engine.data.theme

    self.oFlash = None

    self.lanenumber     = float(5)
    self.fretImgColNumber = float(3)

    #myfingershurt:
    self.bassGrooveNeckMode = self.engine.config.get("game", "bass_groove_neck")

    self.tailsEnabled = True

    self.loadImages()
    
    self.twoChordMax = False

    self.rockLevel = 0.0

    self.neck = Neck(self.engine, self, playerObj)

  def renderFreestyleFlames(self, visibility, controls):
    if self.flameColors[0][0][0] == -1:
      return

    w = self.boardWidth / self.strings

    v = 1.0 - visibility


    flameLimit = 10.0
    flameLimitHalf = round(flameLimit/2.0)
    for fretNum in range(self.strings):
      if controls.getState(self.keys[fretNum]) or controls.getState(self.keys[fretNum+5]):

        if self.freestyleHitFlameCounts[fretNum] < flameLimit:
          ms = math.sin(self.time) * .25 + 1
  
          x  = (self.strings / 2 - fretNum) * w
  
          ff = 1 + 0.25       
          y = v + ff / 6
  
          if self.theme == 2:
            y -= 0.5
          
          flameSize = self.flameSizes[self.cappedScoreMult - 1][fretNum]
          if self.theme == 0 or self.theme == 1: #THIS SETS UP GH3 COLOR, ELSE ROCKBAND(which is DEFAULT in Theme.py)
            flameColor = self.gh3flameColor
          else: #MFH - fixing crash!
            flameColor = self.fretColors[fretNum]
          if flameColor[0] == -2:
            flameColor = self.fretColors[fretNum]
          
          ff += 1.5 #ff first time is 2.75 after this
  
          if self.freestyleHitFlameCounts[fretNum] < flameLimitHalf:
            flamecol = tuple([flameColor[ifc] for ifc in range(3)])
            rbStarColor = (.1, .1, .2, .3)
            xOffset = (.0, - .005, .005, .0)
            yOffset = (.20, .255, .255, .255)
            scaleMod = .6 * ms * ff
            scaleFix = (6.0, 5.5, 5.0, 4.7)
            for step in range(4):
              if self.starPowerActive and self.theme < 2:
                flamecol = self.spColor
              else: #Default starcolor (Rockband)
                flamecol = (rbStarColor[step],)*3
              hfCount = self.freestyleHitFlameCounts[fretNum]
              if step == 0:
                hfCount += 1
              if self.disableFlameSFX != True:
                self.engine.draw3Dtex(self.hitflames2Drawing, coord = (x+xOffset[step], y+yOffset[step], 0), rot = (90, 1, 0, 0),
                                    scale = (.25 + .05 * step + scaleMod, hfCount/scaleFix[step] + scaleMod, hfCount/scaleFix[step] + scaleMod),
                                    vertex = (-flameSize * ff,-flameSize * ff,flameSize * ff,flameSize * ff),
                                    texcoord = (0.0,0.0,1.0,1.0), multiples = True, alpha = True, color = flamecol)
          
          else:
            flameColorMod = 0.1 * (flameLimit - self.freestyleHitFlameCounts[fretNum])
            flamecol = tuple([flameColor[ifc]*flameColorMod for ifc in range(3)])
            xOffset = (.0, - .005, .005, .005)
            yOffset = (.35, .405, .355, .355)
            scaleMod = .6 * ms * ff
            scaleFix = (3.0, 2.5, 2.0, 1.7)
            for step in range(4):
              hfCount = self.freestyleHitFlameCounts[fretNum]
              if step == 0:
                hfCount += 1
              else:  
                if self.starPowerActive and self.theme < 2:
                  flamecol = self.spColor
                else: #Default starcolor (Rockband)
                  flamecol = (.4+.1*step,)*3
              if self.disableFlameSFX != True:
                self.engine.draw3Dtex(self.hitflames1Drawing, coord = (x+xOffset[step], y+yOffset[step], 0), rot = (90, 1, 0, 0),
                                    scale = (.25 + .05 * step + scaleMod, hfCount/scaleFix[step] + scaleMod, hfCount/scaleFix[step] + scaleMod),
                                    vertex = (-flameSize * ff,-flameSize * ff,flameSize * ff,flameSize * ff),
                                    texcoord = (0.0,0.0,1.0,1.0), multiples = True, alpha = True, color = flamecol)            

          self.freestyleHitFlameCounts[fretNum] += 1
      
        else:   #MFH - flame count is done - reset it!
          self.freestyleHitFlameCounts[fretNum] = 0    #MFH

  def render(self, visibility, song, pos, controls, killswitch):
  
    if shaders.turnon:
      shaders.globals["dfActive"] = self.drumFillsActive
      shaders.globals["breActive"] = self.freestyleActive
      shaders.globals["rockLevel"] = self.rockLevel
      if shaders.globals["killswitch"] != killswitch:
        shaders.globals["killswitchPos"] = pos
      shaders.globals["killswitch"] = killswitch
      shaders.modVar("height",0.2,0.2,1.0,"tail")
      

    if not self.starNotesSet == True:
      self.totalNotes = 0
      
      
      for time, event in song.track[self.player].getAllEvents():
        if not isinstance(event, Note):
          continue
        self.totalNotes += 1
        
        
      stars = []
      maxStars = []
      maxPhrase = self.totalNotes/120
      for q in range(0,maxPhrase):
        for n in range(0,10):
          stars.append(self.totalNotes/maxPhrase*(q)+n+maxPhrase/4)
        maxStars.append(self.totalNotes/maxPhrase*(q)+10+maxPhrase/4)
      i = 0
      for time, event in song.track[self.player].getAllEvents():
        if not isinstance(event, Note):
          continue
        for a in stars:
          if i == a:
            self.starNotes.append(time)
            event.star = True
        for a in maxStars:
          if i == a:
            self.maxStars.append(time)
            event.finalStar = True
        i += 1
      for time, event in song.track[self.player].getAllEvents():
        if not isinstance(event, Note):
          continue
        for q in self.starNotes:
          if time == q:
            event.star = True
        for q in self.maxStars:
          if time == q:   #MFH - no need to mark only the final SP phrase note as the finalStar as in drums, they will be hit simultaneously here.
            event.finalStar = True
      self.starNotesSet = True

    if not (self.coOpFailed and not self.coOpRestart):
      glEnable(GL_BLEND)
      glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
      glEnable(GL_COLOR_MATERIAL)

      if self.leftyMode:
        if not self.battleStatus[6]:
          glScalef(-1, 1, 1)
      elif self.battleStatus[6]:
        glScalef(-1, 1, 1)

      if self.freestyleActive:
        self.renderFreestyleLanes(visibility, song, pos, None) #MFH - render the lanes on top of the notes.
        self.renderFrets(visibility, song, controls)

        if self.hitFlamesPresent:   #MFH - only if present!
          self.renderFreestyleFlames(visibility, controls)    #MFH - freestyle hit flames

      else:    
        self.renderTails(visibility, song, pos, killswitch)
        if self.fretsUnderNotes:  #MFH
          if self.twoDnote == True:
            self.renderFrets(visibility, song, controls)
            self.renderNotes(visibility, song, pos)
          else:
            self.renderNotes(visibility, song, pos)
            self.renderFrets(visibility, song, controls)
        else:
          self.renderNotes(visibility, song, pos)
          self.renderFrets(visibility, song, controls)

        self.renderFreestyleLanes(visibility, song, pos, None) #MFH - render the lanes on top of the notes.

        
        if self.hitFlamesPresent:   #MFH - only if present!
          self.renderHitGlow()
          self.renderHitTrails(controls)
          self.renderFlames(song, pos, controls)    #MFH - only when freestyle inactive!
        
      if self.leftyMode:
        if not self.battleStatus[6]:
          glScalef(-1, 1, 1)
      elif self.battleStatus[6]:
        glScalef(-1, 1, 1)

  def getDoubleNotes(self, notes):
    if self.battleStatus[7] and notes != []:
      notes = sorted(notes, key=lambda x: x[0])
      curTime = 0
      tempnotes = []
      tempnumbers = []
      curNumbers = []
      noteCount = 0
      for time, note in notes:
        noteCount += 1
        if not isinstance(note, Note):
          if noteCount == len(notes) and len(curNumbers) < 3 and len(curNumbers) > 0:
            maxNote = curNumbers[0]
            minNote = curNumbers[0]
            for i in range(0, len(curNumbers)):
              if curNumbers[i] > maxNote:
                maxNote = curNumbers[i]
              if curNumbers[i] < minNote:
                minNote = curNumbers[i]
            curNumbers = []
            if maxNote < 4:
              tempnumbers.append(maxNote + 1)
            elif minNote > 0:
              tempnumbers.append(minNote - 1)
            else:
              tempnumbers.append(2)
          elif noteCount == len(notes) and len(curNumbers) > 2:
            tempnumbers.append(-1)
            curNumbers = []
          continue
        if time != curTime:
          if curTime != 0 and len(curNumbers) < 3:
            maxNote = curNumbers[0]
            minNote = curNumbers[0]
            for i in range(0, len(curNumbers)):
              if curNumbers[i] > maxNote:
                maxNote = curNumbers[i]
              if curNumbers[i] < minNote:
                minNote = curNumbers[i]
            curNumbers = []
            if maxNote < 4:
              tempnumbers.append(maxNote + 1)
            elif minNote > 0:
              tempnumbers.append(minNote - 1)
            else:
              tempnumbers.append(2)
          elif (curTime != 0 or noteCount == len(notes)) and len(curNumbers) > 2:
            tempnumbers.append(-1)
            curNumbers = []
          tempnotes.append((time,deepcopy(note)))
          curTime = time
          curNumbers.append(note.number)
          if noteCount == len(notes) and len(curNumbers) < 3:
            maxNote = curNumbers[0]
            minNote = curNumbers[0]
            for i in range(0, len(curNumbers)):
              if curNumbers[i] > maxNote:
                maxNote = curNumbers[i]
              if curNumbers[i] < minNote:
                minNote = curNumbers[i]
            curNumbers = []
            if maxNote < 4:
              tempnumbers.append(maxNote + 1)
            elif minNote > 0:
              tempnumbers.append(minNote - 1)
            else:
              tempnumbers.append(2)
          elif noteCount == len(notes) and len(curNumbers) > 2:
            tempnumbers.append(-1)
            curNumbers = []
        else:
          curNumbers.append(note.number)
          if noteCount == len(notes) and len(curNumbers) < 3:
            maxNote = curNumbers[0]
            minNote = curNumbers[0]
            for i in range(0, len(curNumbers)):
              if curNumbers[i] > maxNote:
                maxNote = curNumbers[i]
              if curNumbers[i] < minNote:
                minNote = curNumbers[i]
            curNumbers = []
            if maxNote < 4:
              tempnumbers.append(maxNote + 1)
            elif minNote > 0:
              tempnumbers.append(minNote - 1)
            else:
              tempnumbers.append(2)
          elif noteCount == len(notes) and len(curNumbers) > 2:
            tempnumbers.append(-1)
            curNumbers = []
      noteCount = 0
      for time, note in tempnotes:
        if tempnumbers[noteCount] != -1:
          note.number = tempnumbers[noteCount]
          noteCount += 1
          if time > self.battleStartTimes[7] + self.currentPeriod * self.beatsPerBoard and time < self.battleStartTimes[7] - self.currentPeriod * self.beatsPerBoard + self.battleDoubleLength:
            notes.append((time,note))
        else:
          noteCount += 1
    return sorted(notes, key=lambda x: x[0])


  def controlsMatchNotes(self, controls, notes):
    # no notes?
    if not notes:
      return False
  
    # check each valid chord
    chords = {}
    for time, note in notes:
      if not time in chords:
        chords[time] = []
      chords[time].append((time, note))

    #Make sure the notes are in the right time order
    chordlist = chords.values()
    chordlist.sort(lambda a, b: cmp(a[0][0], b[0][0]))

    twochord = 0
    for chord in chordlist:
      # matching keys?
      requiredKeys = [note.number for time, note in chord]
      requiredKeys = self.uniqify(requiredKeys)
      
      if len(requiredKeys) > 2 and self.twoChordMax == True:
        twochord = 0
        for k in self.keys:
          if controls.getState(k):
            twochord += 1
        if twochord == 2:
          skipped = len(requiredKeys) - 2
          requiredKeys = [min(requiredKeys), max(requiredKeys)]
        else:
          twochord = 0

      for n in range(self.strings):
        if n in requiredKeys and not (controls.getState(self.keys[n]) or controls.getState(self.keys[n+5])):
          return False
        if not n in requiredKeys and (controls.getState(self.keys[n]) or controls.getState(self.keys[n+5])):
          # The lower frets can be held down
          if n > max(requiredKeys):
            return False
      if twochord != 0:
        if twochord != 2:
          for time, note in chord:
            note.played = True
        else:
          self.twoChordApply = True
          for time, note in chord:
            note.skipped = True
          chord[0][1].skipped = False
          chord[-1][1].skipped = False
          chord[0][1].played = True
          chord[-1][1].played = True
    if twochord == 2:
      self.twoChord += skipped

    return True

  def controlsMatchNotes2(self, controls, notes, hopo = False):
    # no notes?
    if not notes:
      return False

    # check each valid chord
    chords = {}
    for time, note in notes:
      if note.hopod == True and (controls.getState(self.keys[note.number]) or controls.getState(self.keys[note.number + 5])):
        self.playedNotes = []
        return True
      if not time in chords:
        chords[time] = []
      chords[time].append((time, note))

    #Make sure the notes are in the right time order
    chordlist = chords.values()
    chordlist.sort(lambda a, b: cmp(a[0][0], b[0][0]))

    twochord = 0
    for chord in chordlist:
      # matching keys?
      requiredKeys = [note.number for time, note in chord]
      requiredKeys = self.uniqify(requiredKeys)

      if len(requiredKeys) > 2 and self.twoChordMax == True:
        twochord = 0
        for n, k in enumerate(self.keys):
          if controls.getState(k):
            twochord += 1
        if twochord == 2:
          skipped = len(requiredKeys) - 2
          requiredKeys = [min(requiredKeys), max(requiredKeys)]
        else:
          twochord = 0
        
      for n in range(self.strings):
        if n in requiredKeys and not (controls.getState(self.keys[n]) or controls.getState(self.keys[n+5])):
          return False
        if not n in requiredKeys and (controls.getState(self.keys[n]) or controls.getState(self.keys[n+5])):
          # The lower frets can be held down
          if hopo == False and n >= min(requiredKeys):
            return False
      if twochord != 0:
        if twochord != 2:
          for time, note in chord:
            note.played = True
        else:
          self.twoChordApply = True
          for time, note in chord:
            note.skipped = True
          chord[0][1].skipped = False
          chord[-1][1].skipped = False
          chord[0][1].played = True
          chord[-1][1].played = True
        
    if twochord == 2:
      self.twoChord += skipped
      
    return True

  def controlsMatchNotes3(self, controls, notes, hopo = False):
    # no notes?
    if not notes:
      return False

    # check each valid chord
    chords = {}
    for time, note in notes:
      if note.hopod == True and (controls.getState(self.keys[note.number]) or controls.getState(self.keys[note.number + 5])):
        self.playedNotes = []
        return True
      if not time in chords:
        chords[time] = []
      chords[time].append((time, note))

    #Make sure the notes are in the right time order
    chordlist = chords.values()
    chordlist.sort(key=lambda a: a[0][0])

    self.missedNotes = []
    self.missedNoteNums = []
    twochord = 0
    for chord in chordlist:
      # matching keys?
      requiredKeys = [note.number for time, note in chord]
      requiredKeys = self.uniqify(requiredKeys)

      if len(requiredKeys) > 2 and self.twoChordMax == True:
        twochord = 0
        for n, k in enumerate(self.keys):
          if controls.getState(k):
            twochord += 1
        if twochord == 2:
          skipped = len(requiredKeys) - 2
          requiredKeys = [min(requiredKeys), max(requiredKeys)]
        else:
          twochord = 0
          
      if (self.controlsMatchNote3(controls, chord, requiredKeys, hopo)):
        if twochord != 2:
          for time, note in chord:
            note.played = True
        else:
          self.twoChordApply = True
          for time, note in chord:
            note.skipped = True
          chord[0][1].skipped = False
          chord[-1][1].skipped = False
          chord[0][1].played = True
          chord[-1][1].played = True
        break
      if hopo == True:
        break
      self.missedNotes.append(chord)
    else:
      self.missedNotes = []
      self.missedNoteNums = []
    
    for chord in self.missedNotes:
      for time, note in chord:
        if self.debugMode:
          self.missedNoteNums.append(note.number)
        note.skipped = True
        note.played = False
    if twochord == 2:
      self.twoChord += skipped
      
    return True

  #MFH - special function for HOPO intentions checking
  def controlsMatchNextChord(self, controls, notes):
    # no notes?
    if not notes:
      return False

    # check each valid chord
    chords = {}
    for time, note in notes:
      if not time in chords:
        chords[time] = []
      chords[time].append((time, note))

    #Make sure the notes are in the right time order
    chordlist = chords.values()
    chordlist.sort(key=lambda a: a[0][0])

    twochord = 0
    for chord in chordlist:
      # matching keys?
      self.requiredKeys = [note.number for time, note in chord]
      self.requiredKeys = self.uniqify(self.requiredKeys)

      if len(self.requiredKeys) > 2 and self.twoChordMax == True:
        twochord = 0
        self.twoChordApply = True
        for n, k in enumerate(self.keys):
          if controls.getState(k):
            twochord += 1
        if twochord == 2:
          self.requiredKeys = [min(self.requiredKeys), max(self.requiredKeys)]
        else:
          twochord = 0
          
      if (self.controlsMatchNote3(controls, chord, self.requiredKeys, False)):
        return True
      else:
        return False




  def uniqify(self, seq, idfun=None): 
    # order preserving
    if idfun is None:
        def idfun(x): return x
    seen = {}
    result = []
    for item in seq:
        marker = idfun(item)
        # in old Python versions:
        # if seen.has_key(marker)
        # but in new ones:
        if marker in seen: continue
        seen[marker] = 1
        result.append(item)
    return result
  
  def controlsMatchNote3(self, controls, chordTuple, requiredKeys, hopo):
    if len(chordTuple) > 1:
    #Chords must match exactly
      for n in range(self.strings):
        if (n in requiredKeys and not (controls.getState(self.keys[n]) or controls.getState(self.keys[n+5]))) or (n not in requiredKeys and (controls.getState(self.keys[n]) or controls.getState(self.keys[n+5]))):
          return False
    else:
    #Single Note must match that note
      requiredKey = requiredKeys[0]
      if not controls.getState(self.keys[requiredKey]) and not controls.getState(self.keys[requiredKey+5]):
        return False


      #myfingershurt: this is where to filter out higher frets held when HOPOing:
      if hopo == False or self.hopoStyle == 2 or self.hopoStyle == 3:
      #Check for higher numbered frets if not a HOPO or if GH2 strict mode
        for n, k in enumerate(self.keys):
          if (n > requiredKey and n < 5) or (n > 4 and n > requiredKey + 5):
          #higher numbered frets cannot be held
            if controls.getState(k):
              return False

    return True
  
  def startPick(self, song, pos, controls, hopo = False):
    if hopo == True:
      res = startPick2(song, pos, controls, hopo)
      return res
    if not song:
      return False
    if not song.readyToGo:
      return False
    
    self.playedNotes = []
    
    self.matchingNotes = self.getRequiredNotesMFH(song, pos)

    if self.controlsMatchNotes(controls, self.matchingNotes):
      self.pickStartPos = pos
      for time, note in self.matchingNotes:
        if note.skipped == True:
          continue
        self.pickStartPos = max(self.pickStartPos, time)
        note.played       = True
        self.playedNotes.append([time, note])
        if self.guitarSolo:
          self.currentGuitarSoloHitNotes += 1
      return True
    return False

  def startPick2(self, song, pos, controls, hopo = False):
    if not song:
      return False
    if not song.readyToGo:
      return False
    
    self.playedNotes = []
    
    self.matchingNotes = self.getRequiredNotesMFH(song, pos, hopo)

    if self.controlsMatchNotes2(controls, self.matchingNotes, hopo):
      self.pickStartPos = pos
      for time, note in self.matchingNotes:
        if note.skipped == True:
          continue
        self.pickStartPos = max(self.pickStartPos, time)
        if hopo:
          note.hopod        = True
        else:
          note.played       = True
        if note.tappable == 1 or note.tappable == 2:
          self.hopoActive = time
          self.wasLastNoteHopod = True
        elif note.tappable == 3:
          self.hopoActive = -time
          self.wasLastNoteHopod = True
        else:
          self.hopoActive = 0
          self.wasLastNoteHopod = False
        self.playedNotes.append([time, note])
        if self.guitarSolo:
          self.currentGuitarSoloHitNotes += 1
        
      self.hopoLast     = note.number
      return True
    return False

  def startPick3(self, song, pos, controls, hopo = False):
    if not song:
      return False
    if not song.readyToGo:
      return False
    
    self.lastPlayedNotes = self.playedNotes
    self.playedNotes = []
    
    self.matchingNotes = self.getRequiredNotesMFH(song, pos)

    self.controlsMatchNotes3(controls, self.matchingNotes, hopo)

    #myfingershurt
    
    for time, note in self.matchingNotes:
      if note.played != True:
        continue
      
      if shaders.turnon:
        shaders.var["fret"][self.player][note.number]=shaders.time()
        shaders.var["fretpos"][self.player][note.number]=pos
        
      
      self.pickStartPos = pos
      self.pickStartPos = max(self.pickStartPos, time)
      if hopo:
        note.hopod        = True
      else:
        note.played       = True
      if note.tappable == 1 or note.tappable == 2:
        self.hopoActive = time
        self.wasLastNoteHopod = True
      elif note.tappable == 3:
        self.hopoActive = -time
        self.wasLastNoteHopod = True
        if hopo:  #MFH - you just tapped a 3 - make a note of it. (har har)
          self.hopoProblemNoteNum = note.number
          self.sameNoteHopoString = True
      else:
        self.hopoActive = 0
        self.wasLastNoteHopod = False
      self.hopoLast     = note.number
      self.playedNotes.append([time, note])
      if self.guitarSolo:
        self.currentGuitarSoloHitNotes += 1
        

     
    #myfingershurt: be sure to catch when a chord is played
    if len(self.playedNotes) > 1:
      lastPlayedNote = None
      for time, note in self.playedNotes:
        if isinstance(lastPlayedNote, Note):
          if note.tappable == 1 and lastPlayedNote.tappable == 1:
            self.LastStrumWasChord = True
          else:
            self.LastStrumWasChord = False
        lastPlayedNote = note
    
    elif len(self.playedNotes) > 0: #ensure at least that a note was played here
      self.LastStrumWasChord = False

    if len(self.playedNotes) != 0:
      return True
    return False

  def soloFreestylePick(self, song, pos, controls):
    numHits = 0
    for theFret in range(5):
      self.freestyleHit[theFret] = controls.getState(self.keys[theFret+5])
      if self.freestyleHit[theFret]:
        if shaders.turnon:
          shaders.var["fret"][self.player][theFret]=shaders.time()
          shaders.var["fretpos"][self.player][theFret]=pos
        numHits += 1
    return numHits

  #MFH - TODO - handle freestyle picks here
  def freestylePick(self, song, pos, controls):
    numHits = 0
    #if not song:
    #  return numHits
    
    if not controls.getState(self.actions[0]) and not controls.getState(self.actions[1]):
      return 0

    for theFret in range(5):
      self.freestyleHit[theFret] = controls.getState(self.keys[theFret])
      if self.freestyleHit[theFret]:
        if shaders.turnon:
          shaders.var["fret"][self.player][theFret]=shaders.time()
          shaders.var["fretpos"][self.player][theFret]=pos
        numHits += 1
    return numHits
    
  def getPickLength(self, pos):
    if not self.playedNotes:
      return 0.0
    
    # The pick length is limited by the played notes
    pickLength = pos - self.pickStartPos
    for time, note in self.playedNotes:
      pickLength = min(pickLength, note.length)
    return pickLength

  def run(self, ticks, pos, controls):
  
    if not self.paused:
      self.time += ticks
    
    #MFH - Determine which frame to display for starpower notes
    if self.noteSpin:
      self.indexCount = self.indexCount + 1
      if self.indexCount > self.Animspeed-1:
        self.indexCount = 0
      self.noteSpinFrameIndex = (self.indexCount * self.noteSpinFrames - (self.indexCount * self.noteSpinFrames) % self.Animspeed) / self.Animspeed
      if self.noteSpinFrameIndex > self.noteSpinFrames - 1:
        self.noteSpinFrameIndex = 0

    #myfingershurt: must not decrease SP if paused.
    if self.starPowerActive == True and self.paused == False:
      self.starPower -= ticks/self.starPowerDecreaseDivisor 
      if self.starPower <= 0:
        self.starPower = 0
        self.starPowerActive = False
        self.engine.data.starDeActivateSound.play()

    
    # update frets
    if self.editorMode:
      if (controls.getState(self.actions[0]) or controls.getState(self.actions[1])):
        for i in range(self.strings):
          if controls.getState(self.keys[i]) or controls.getState(self.keys[i+5]):
            activeFrets.append(i)
        activeFrets = activeFrets or [self.selectedString]
      else:
        activeFrets = []
    else:
      activeFrets = [note.number for time, note in self.playedNotes]
    
    for n in range(self.strings):
      if controls.getState(self.keys[n]) or controls.getState(self.keys[n+5]) or (self.editorMode and self.selectedString == n):
        self.fretWeight[n] = 0.5
      else:
        self.fretWeight[n] = max(self.fretWeight[n] - ticks / 64.0, 0.0)
      if n in activeFrets:
        self.fretActivity[n] = min(self.fretActivity[n] + ticks / 32.0, 1.0)
      else:
        self.fretActivity[n] = max(self.fretActivity[n] - ticks / 64.0, 0.0)
      
      #MFH - THIS is where note sustains should be determined... NOT in renderNotes / renderFrets / renderFlames  -.-
      if self.fretActivity[n]:
        self.hit[n] = True
      else:
        self.hit[n] = False

    
    if self.vbpmLogicType == 0:   #MFH - VBPM (old)
      if self.currentBpm != self.targetBpm:
        diff = self.targetBpm - self.currentBpm
        if (round((diff * .03), 4) != 0):
          self.currentBpm = round(self.currentBpm + (diff * .03), 4)
        else:
          self.currentBpm = self.targetBpm
        self.setBPM(self.currentBpm) # glorandwarf: was setDynamicBPM(self.currentBpm)

    for time, note in self.playedNotes:
      if pos > time + note.length:
        return False

    return True

