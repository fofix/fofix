#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire                                                     #
# Copyright (C) 2006 Sami Kyöstilä                                  #
#               2008 myfingershurt                                  #
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

import midi
import Log
import Audio
import Config
import os
import re
import shutil
import Config
#stump: when we completely drop 2.4 support, change this to just "import hashlib"
try:
  import hashlib
except ImportError:
  import sha
  class hashlib:
    sha1 = sha.sha
import binascii
import Cerealizer
import urllib
import Version
import Theme
import copy
import string
import cPickle  #stump: Cerealizer and sqlite3 don't seem to like each other that much...
from Language import _

#stump: turns out the sqlite3 module didn't appear until Python 2.5...
try:
  import sqlite3
  canCache = True
except ImportError:
  try:
    import pysqlite2.dbapi2 as sqlite3  # close enough
    canCache = True
  except ImportError:
    canCache = False

DEFAULT_BPM = 120.0
DEFAULT_LIBRARY         = "songs"

EXP_DIF     = 0
HAR_DIF     = 1
MED_DIF     = 2
EAS_DIF     = 3

#MFH - special / global text-event tracks for the separated text-event list variable
TK_SCRIPT = 0         #script.txt events
TK_SECTIONS = 1       #Section events
TK_GUITAR_SOLOS = 2   #Guitar Solo start/stop events
TK_LYRICS = 3         #RB MIDI Lyric events
TK_UNUSED_TEXT = 4    #Unused / other text events

#code for adding tracks, inside song.py:
#self.song.eventTracks[TK_SCRIPT].addEvent(self.abs_time(), event)  #MFH - add an event to the script.txt track
#self.song.eventTracks[TK_SECTIONS].addEvent(self.abs_time(), event)  #MFH - add an event to the sections track
#self.song.eventTracks[TK_GUITAR_SOLOS].addEvent(self.abs_time(), event)  #MFH - add an event to the guitar solos track
#self.song.eventTracks[TK_LYRICS].addEvent(self.abs_time(), event)  #MFH - add an event to the lyrics track
#self.song.eventTracks[TK_UNUSED_TEXT].addEvent(self.abs_time(), event)  #MFH - add an event to the unused text track

#code for accessing track objects, outside song.py:
#self.song.eventTracks[Song.TK_SCRIPT]
#self.song.eventTracks[Song.TK_SECTIONS]
#self.song.eventTracks[Song.TK_GUITAR_SOLOS]
#self.song.eventTracks[Song.TK_LYRICS]
#self.song.eventTracks[Song.TK_UNUSED_TEXT]


#FOF_TYPE                = 0
#GH1_TYPE                = 1
#GH2_TYPE                = 2

#MFH
MIDI_TYPE_GH            = 0       #GH type MIDIs have starpower phrases marked with a long G8 note on that instrument's track
MIDI_TYPE_RB            = 1       #RB type MIDIs have overdrive phrases marked with a long G#9 note on that instrument's track
MIDI_TYPE_WT            = 2       #WT type MIDIs have six notes and HOPOs marked on F# of the track

#MFH 
EARLY_HIT_WINDOW_NONE   = 1       #GH1/RB1/RB2 = NONE
EARLY_HIT_WINDOW_HALF   = 2       #GH2/GH3/GHA/GH80's = HALF
EARLY_HIT_WINDOW_FULL   = 3       #FoF = FULL

GUITAR_PART             = 0
RHYTHM_PART             = 1
BASS_PART               = 2
LEAD_PART               = 3
DRUM_PART               = 4
VOCAL_PART              = 5

instrumentDiff = {
  0 : (lambda a: a.diffGuitar),
  1 : (lambda a: a.diffGuitar),
  2 : (lambda a: a.diffBass),
  3 : (lambda a: a.diffGuitar),
  4 : (lambda a: a.diffDrums),
  5 : (lambda a: a.diffVocals)
}

class Part:
  def __init__(self, id, text):
    self.id   = id
    self.text = text

    #self.logClassInits = Config.get("game", "log_class_inits")
    #if self.logClassInits == 1:
    #  Log.debug("Part class init (song.py)...")
    
  def __str__(self):
    return self.text

  def __repr__(self):
    return self.text

parts = {
  GUITAR_PART: Part(GUITAR_PART, _("Guitar")),
  RHYTHM_PART: Part(RHYTHM_PART, _("Rhythm")),
  BASS_PART:   Part(BASS_PART,   _("Bass")),
  LEAD_PART:   Part(LEAD_PART,   _("Lead")),
  DRUM_PART:   Part(DRUM_PART,   _("Drums")),
  VOCAL_PART:  Part(VOCAL_PART,  _("Vocals")),
}

class Difficulty:
  def __init__(self, id, text):
    self.id   = id
    self.text = text

    #self.logClassInits = Config.get("game", "log_class_inits")
    #if self.logClassInits == 1:
    #  Log.debug("Difficulty class init (song.py)...")

    
  def __str__(self):
    return self.text

  def __repr__(self):
    return self.text

difficulties = {
  EAS_DIF: Difficulty(EAS_DIF, _("Easy")),
  MED_DIF: Difficulty(MED_DIF, _("Medium")),
  HAR_DIF: Difficulty(HAR_DIF, _("Hard")),
  EXP_DIF: Difficulty(EXP_DIF, _("Expert")),
}

defaultSections = ["Start","1/4","1/2","3/4"]



# stump: manage cache files
class CacheManager(object):
  SCHEMA_VERSION = 4  #stump: current cache format version number
  def __init__(self):
    self.caches = {}
  def getCache(self, infoFileName):
    '''Given the path of a song.ini, return a SQLite connection to the
    associated cache.'''
    cachePath = os.path.dirname(os.path.dirname(infoFileName))
    if self.caches.has_key(cachePath):
      return self.caches[cachePath]
    # The cache must be opened or created.
    oldcwd = os.getcwd()
    try:
      os.chdir(cachePath)  #stump: work around bug in SQLite unicode path name handling
      conn = sqlite3.Connection('.fofix-cache')
    finally:
      os.chdir(oldcwd)
    # Check that the cache is completely initialized.
    try:
      v = conn.execute("SELECT `value` FROM `config` WHERE `key` = 'version'").fetchone()[0]
      mustReinitialize = (int(v) != self.SCHEMA_VERSION)
    except:
      mustReinitialize = True
    if mustReinitialize:
      # Clean out the database, then make our tables.
      for tbl in conn.execute("SELECT `name` FROM `sqlite_master` WHERE `type` = 'table'").fetchall():
        conn.execute('DROP TABLE `%s`' % tbl)
      conn.commit()
      conn.execute('VACUUM')
      #stump: if you need to change the database schema, do it here, then bump the version number, a small bit above here.
      conn.execute('CREATE TABLE `config` (`key` STRING UNIQUE, `value` STRING)')
      conn.execute('CREATE TABLE `songinfo` (`hash` STRING UNIQUE, `info` STRING)')
      conn.execute('INSERT INTO `config` (`key`, `value`) VALUES (?, ?)', ('version', self.SCHEMA_VERSION))
      conn.commit()
    self.caches[cachePath] = conn
    return conn
cacheManager = CacheManager()  # singleton instance
del CacheManager


class SongInfo(object):
  def __init__(self, infoFileName, songLibrary = DEFAULT_LIBRARY, allowCacheUsage = False):
    self.songName      = os.path.basename(os.path.dirname(infoFileName))
    self.fileName      = infoFileName
    self.libraryNam       = songLibrary[songLibrary.find(DEFAULT_LIBRARY):]
    self.info          = Config.MyConfigParser()
    self._partDifficulties = {}
    self._parts        = None
    self._midiStyle    = None
    if Config.get("performance", "cache_song_metadata"):
      self.allowCacheUsage = allowCacheUsage  #stump
    else:
      self.allowCacheUsage = False

    self.locked = False

    #MFH - want to read valid sections from the MIDI in for practice mode selection here:
    self._sections = None
    

    self.name = _("NoName")
    

    try:
      self.info.read(infoFileName)
    except:
      pass
    
    self.logClassInits = Config.get("game", "log_class_inits")
    if self.logClassInits == 1:
      Log.debug("SongInfo class init (song.py): " + self.name)

    self.logSections = Config.get("game", "log_sections")

    self.logUneditedMidis = Config.get("log",   "log_unedited_midis")

    self.useUneditedMidis = Config.get("debug",   "use_unedited_midis")
    if self.useUneditedMidis == 1:    #auto
      #if os.path.exists(os.path.join(os.path.dirname(self.fileName), "notes-unedited.mid"))
      if os.path.isfile(os.path.join(os.path.dirname(self.fileName), "notes-unedited.mid")):
        notefile = "notes-unedited.mid"
        if self.logUneditedMidis == 1:
          Log.debug("notes-unedited.mid found, using instead of notes.mid! - " + self.name)
      else:
        notefile = "notes.mid"
        if self.logUneditedMidis == 1:
          Log.debug("notes-unedited.mid not found, using notes.mid - " + self.name)
    else:
      notefile = "notes.mid"
      if self.logUneditedMidis == 1:
        Log.debug("notes-unedited.mid not found, using notes.mid - " + self.name)
    self.noteFileName = os.path.join(os.path.dirname(self.fileName), notefile)
    
    # stump: Check the cache for the presence of this song.
    if canCache and self.allowCacheUsage:
      self.stateHash = hashlib.sha1(open(self.noteFileName, 'rb').read() + open(self.fileName, 'rb').read()).hexdigest()
      cache = cacheManager.getCache(self.fileName)

      try:    #MFH - it crashes here on previews!
        result = cache.execute('SELECT `info` FROM `songinfo` WHERE `hash` = ?', [self.stateHash]).fetchone()
      except Exception, e:
        Log.error(str(e))
        result = None

      if result is not None:
        try:
          self.__dict__.update(cPickle.loads(str(result[0])))
          return
        except:
          # The entry is there but could not be loaded.
          # Nuke it and let it be rebuilt further down.
          cache.execute('DELETE FROM `songinfo` WHERE `hash` = ?', [self.stateHash])

    # Read highscores and verify their hashes.
    # There ain't no security like security throught obscurity :)
    self.highScores = {}
    
    scores = self._get("scores", str, "")
    scores_ext = self._get("scores_ext", str, "")
    if scores:
      scores = Cerealizer.loads(binascii.unhexlify(scores))
      if scores_ext:
        scores_ext = Cerealizer.loads(binascii.unhexlify(scores_ext))
      for difficulty in scores.keys():
        try:
          difficulty = difficulties[difficulty]
        except KeyError:
          continue
        for i, base_scores in enumerate(scores[difficulty.id]):
          score, stars, name, hash = base_scores
          if scores_ext != "":
            #Someone may have mixed extended and non extended
            try:
              if len(scores_ext[difficulty.id][i]) < 9:
                hash_ext, stars2, notesHit, notesTotal, noteStreak, modVersion, oldInfo, oldInfo2 =  scores_ext[difficulty.id][i]
                handicapValue = 0
                longHandicap = "None"
                originalScore = 0
              else:
                hash_ext, stars2, notesHit, notesTotal, noteStreak, modVersion, handicapValue, longHandicap, originalScore =  scores_ext[difficulty.id][i]
              scoreExt = (notesHit, notesTotal, noteStreak, modVersion, handicapValue, longHandicap, originalScore)
            except:
              hash_ext = 0
              scoreExt = (0, 0, 0 , "RF-mod", 0, "None", 0)
          if self.getScoreHash(difficulty, score, stars, name) == hash:
            if scores_ext != "" and hash == hash_ext:
              self.addHighscore(difficulty, score, stars, name, part = parts[GUITAR_PART], scoreExt = scoreExt)
            else:
              self.addHighscore(difficulty, score, stars, name, part = parts[GUITAR_PART])
          else:
            Log.warn("Weak hack attempt detected. Better luck next time.")

    self.highScoresRhythm = {}
    
    scores = self._get("scores_rhythm", str, "")
    scores_ext = self._get("scores_rhythm_ext", str, "")
    if scores:
      scores = Cerealizer.loads(binascii.unhexlify(scores))
      if scores_ext:
        scores_ext = Cerealizer.loads(binascii.unhexlify(scores_ext))
      for difficulty in scores.keys():
        try:
          difficulty = difficulties[difficulty]
        except KeyError:
          continue
        #for score, stars, name, hash in scores[difficulty.id]:
        #  if self.getScoreHash(difficulty, score, stars, name) == hash:
        #    self.addHighscore(difficulty, score, stars, name, part = parts[RHYTHM_PART])
        #  else:
        #    Log.warn("Weak hack attempt detected. Better luck next time.")
        for i, base_scores in enumerate(scores[difficulty.id]):
          score, stars, name, hash = base_scores
          if scores_ext != "":
            #Someone may have mixed extended and non extended
            try:
              if len(scores_ext[difficulty.id][i]) < 9:
                hash_ext, stars2, notesHit, notesTotal, noteStreak, modVersion, oldInfo, oldInfo2 =  scores_ext[difficulty.id][i]
                handicapValue = 0
                longHandicap = "None"
                originalScore = 0
              else:
                hash_ext, stars2, notesHit, notesTotal, noteStreak, modVersion, handicapValue, longHandicap, originalScore =  scores_ext[difficulty.id][i]
              scoreExt = (notesHit, notesTotal, noteStreak, modVersion, handicapValue, longHandicap, originalScore)
            except:
              hash_ext = 0
              scoreExt = (0, 0, 0 , "RF-mod", 0, "None", 0)
          if self.getScoreHash(difficulty, score, stars, name) == hash:
            if scores_ext != "" and hash == hash_ext:
              self.addHighscore(difficulty, score, stars, name, part = parts[RHYTHM_PART], scoreExt = scoreExt)
            else:
              self.addHighscore(difficulty, score, stars, name, part = parts[RHYTHM_PART])
          else:
            Log.warn("Weak hack attempt detected. Better luck next time.")

    self.highScoresBass = {}
    
    scores = self._get("scores_bass", str, "")
    scores_ext = self._get("scores_bass_ext", str, "")
    if scores:
      scores = Cerealizer.loads(binascii.unhexlify(scores))
      if scores_ext:
        scores_ext = Cerealizer.loads(binascii.unhexlify(scores_ext))
      for difficulty in scores.keys():
        try:
          difficulty = difficulties[difficulty]
        except KeyError:
          continue
        #for score, stars, name, hash in scores[difficulty.id]:
        #  if self.getScoreHash(difficulty, score, stars, name) == hash:
        #    self.addHighscore(difficulty, score, stars, name, part = parts[BASS_PART])
        #  else:
        #    Log.warn("Weak hack attempt detected. Better luck next time.")
        for i, base_scores in enumerate(scores[difficulty.id]):
          score, stars, name, hash = base_scores
          if scores_ext != "":
            #Someone may have mixed extended and non extended
            try:
              if len(scores_ext[difficulty.id][i]) < 9:
                hash_ext, stars2, notesHit, notesTotal, noteStreak, modVersion, oldInfo, oldInfo2 =  scores_ext[difficulty.id][i]
                handicapValue = 0
                longHandicap = "None"
                originalScore = 0
              else:
                hash_ext, stars2, notesHit, notesTotal, noteStreak, modVersion, handicapValue, longHandicap, originalScore =  scores_ext[difficulty.id][i]
              scoreExt = (notesHit, notesTotal, noteStreak, modVersion, handicapValue, longHandicap, originalScore)
            except:
              hash_ext = 0
              scoreExt = (0, 0, 0 , "RF-mod", 0, "None", 0)
          if self.getScoreHash(difficulty, score, stars, name) == hash:
            if scores_ext != "" and hash == hash_ext:
              self.addHighscore(difficulty, score, stars, name, part = parts[BASS_PART], scoreExt = scoreExt)
            else:
              self.addHighscore(difficulty, score, stars, name, part = parts[BASS_PART])
          else:
            Log.warn("Weak hack attempt detected. Better luck next time.")

    self.highScoresLead = {}
    
    scores = self._get("scores_lead", str, "")
    scores_ext = self._get("scores_lead_ext", str, "")
    if scores:
      scores = Cerealizer.loads(binascii.unhexlify(scores))
      if scores_ext:
        scores_ext = Cerealizer.loads(binascii.unhexlify(scores_ext))
      for difficulty in scores.keys():
        try:
          difficulty = difficulties[difficulty]
        except KeyError:
          continue
        #for score, stars, name, hash in scores[difficulty.id]:
        #  if self.getScoreHash(difficulty, score, stars, name) == hash:
        #    self.addHighscore(difficulty, score, stars, name, part = parts[LEAD_PART])
        #  else:
        #    Log.warn("Weak hack attempt detected. Better luck next time.")            
        for i, base_scores in enumerate(scores[difficulty.id]):
          score, stars, name, hash = base_scores
          if scores_ext != "":
            #Someone may have mixed extended and non extended
            try:
              if len(scores_ext[difficulty.id][i]) < 9:
                hash_ext, stars2, notesHit, notesTotal, noteStreak, modVersion, oldInfo, oldInfo2 =  scores_ext[difficulty.id][i]
                handicapValue = 0
                longHandicap = "None"
                originalScore = 0
              else:
                hash_ext, stars2, notesHit, notesTotal, noteStreak, modVersion, handicapValue, longHandicap, originalScore =  scores_ext[difficulty.id][i]
              scoreExt = (notesHit, notesTotal, noteStreak, modVersion, handicapValue, longHandicap, originalScore)
            except:
              hash_ext = 0
              scoreExt = (0, 0, 0 , "RF-mod", 0, "None", 0)
          if self.getScoreHash(difficulty, score, stars, name) == hash:
            if scores_ext != "" and hash == hash_ext:
              self.addHighscore(difficulty, score, stars, name, part = parts[LEAD_PART], scoreExt = scoreExt)
            else:
              self.addHighscore(difficulty, score, stars, name, part = parts[LEAD_PART])
          else:
            Log.warn("Weak hack attempt detected. Better luck next time.")

    #myfingershurt: drums :)
    self.highScoresDrum = {}
    
    scores = self._get("scores_drum", str, "")
    scores_ext = self._get("scores_drum_ext", str, "")
    if scores:
      scores = Cerealizer.loads(binascii.unhexlify(scores))
      if scores_ext:
        scores_ext = Cerealizer.loads(binascii.unhexlify(scores_ext))
      for difficulty in scores.keys():
        try:
          difficulty = difficulties[difficulty]
        except KeyError:
          continue
        #for score, stars, name, hash in scores[difficulty.id]:
        #  if self.getScoreHash(difficulty, score, stars, name) == hash:
        #    self.addHighscore(difficulty, score, stars, name, part = parts[DRUM_PART])
        #  else:
        #    Log.warn("Weak hack attempt detected. Better luck next time.")         
        for i, base_scores in enumerate(scores[difficulty.id]):
          score, stars, name, hash = base_scores
          if scores_ext != "":
            #Someone may have mixed extended and non extended
            try:
              if len(scores_ext[difficulty.id][i]) < 9:
                hash_ext, stars2, notesHit, notesTotal, noteStreak, modVersion, oldInfo, oldInfo2 =  scores_ext[difficulty.id][i]
                handicapValue = 0
                longHandicap = "None"
                originalScore = 0
              else:
                hash_ext, stars2, notesHit, notesTotal, noteStreak, modVersion, handicapValue, longHandicap, originalScore =  scores_ext[difficulty.id][i]
              scoreExt = (notesHit, notesTotal, noteStreak, modVersion, handicapValue, longHandicap, originalScore)
            except:
              hash_ext = 0
              scoreExt = (0, 0, 0 , "RF-mod", 0, "None", 0)
          if self.getScoreHash(difficulty, score, stars, name) == hash:
            if scores_ext != "" and hash == hash_ext:
              self.addHighscore(difficulty, score, stars, name, part = parts[DRUM_PART], scoreExt = scoreExt)
            else:
              self.addHighscore(difficulty, score, stars, name, part = parts[DRUM_PART])
          else:
            Log.warn("Weak hack attempt detected. Better luck next time.")

    #akedrou - vocals!
    self.highScoresVocal = {}
    
    scores = self._get("scores_vocal", str, "")
    scores_ext = self._get("scores_vocal_ext", str, "")
    if scores:
      scores = Cerealizer.loads(binascii.unhexlify(scores))
      if scores_ext:
        scores_ext = Cerealizer.loads(binascii.unhexlify(scores_ext))
      for difficulty in scores.keys():
        try:
          difficulty = difficulties[difficulty]
        except KeyError:
          continue
        #for score, stars, name, hash in scores[difficulty.id]:
        #  if self.getScoreHash(difficulty, score, stars, name) == hash:
        #    self.addHighscore(difficulty, score, stars, name, part = parts[DRUM_PART])
        #  else:
        #    Log.warn("Weak hack attempt detected. Better luck next time.")         
        for i, base_scores in enumerate(scores[difficulty.id]):
          score, stars, name, hash = base_scores
          if scores_ext != "":
            #Someone may have mixed extended and non extended
            try:
              if len(scores_ext[difficulty.id][i]) < 9:
                hash_ext, stars2, notesHit, notesTotal, noteStreak, modVersion, oldInfo, oldInfo2 =  scores_ext[difficulty.id][i]
                handicapValue = 0
                longHandicap = "None"
                originalScore = 0
              else:
                hash_ext, stars2, notesHit, notesTotal, noteStreak, modVersion, handicapValue, longHandicap, originalScore =  scores_ext[difficulty.id][i]
              scoreExt = (notesHit, notesTotal, noteStreak, modVersion, handicapValue, longHandicap, originalScore)
            except:
              hash_ext = 0
              scoreExt = (0, 0, 0 , "RF-mod", 0, "None", 0)
          if self.getScoreHash(difficulty, score, stars, name) == hash:
            if scores_ext != "" and hash == hash_ext:
              self.addHighscore(difficulty, score, stars, name, part = parts[DRUM_PART], scoreExt = scoreExt)
            else:
              self.addHighscore(difficulty, score, stars, name, part = parts[DRUM_PART])
          else:
            Log.warn("Weak hack attempt detected. Better luck next time.")

            
    if canCache and self.allowCacheUsage:  #stump: preload this stuff into the cache
      self.getParts()
      self.getSections()
    self.writeCache()
            
  # stump: Write this song's info into the cache.
  def writeCache(self):
    if canCache and self.allowCacheUsage:
      self.stateHash = hashlib.sha1(open(self.noteFileName, 'rb').read() + open(self.fileName, 'rb').read()).hexdigest()
      cache = cacheManager.getCache(self.fileName)
      pkl = cPickle.dumps(self.__dict__)
      cache.execute('INSERT OR REPLACE INTO `songinfo` (`hash`, `info`) VALUES (?, ?)', [self.stateHash, pkl])


  def _set(self, attr, value):
    if not self.info.has_section("song"):
      self.info.add_section("song")
    if type(value) == unicode:
      value = value.encode(Config.encoding)
    else:
      value = str(value)
    self.info.set("song", attr, value)
    
  def getObfuscatedScores(self, part = parts[GUITAR_PART]):
    s = {}
    if part == parts[GUITAR_PART]:
      highScores = self.highScores
    elif part == parts[RHYTHM_PART]:
      highScores = self.highScoresRhythm
    elif part == parts[BASS_PART]:
      highScores = self.highScoresBass
    elif part == parts[LEAD_PART]:
      highScores = self.highScoresLead
    elif part == parts[DRUM_PART]:
      highScores = self.highScoresDrum
    elif part == parts[VOCAL_PART]:
      highScores = self.highScoresVocal
    else:
      highScores = self.highScores
      
    for difficulty in highScores.keys():
      s[difficulty.id] = [(score, stars, name, self.getScoreHash(difficulty, score, stars, name)) for score, stars, name, scores_ext in highScores[difficulty]]
    return binascii.hexlify(Cerealizer.dumps(s))

  def getObfuscatedScoresExt(self, part = parts[GUITAR_PART]):
    s = {}
    if part == parts[GUITAR_PART]:
      highScores = self.highScores
    elif part == parts[RHYTHM_PART]:
      highScores = self.highScoresRhythm
    elif part == parts[BASS_PART]:
      highScores = self.highScoresBass
    elif part == parts[LEAD_PART]:
      highScores = self.highScoresLead
    elif part == parts[DRUM_PART]:
      highScores = self.highScoresDrum
    elif part == parts[VOCAL_PART]:
      highScores = self.highScoresVocal
    else:
      highScores = self.highScores
      
    for difficulty in highScores.keys():
      s[difficulty.id] = [(self.getScoreHash(difficulty, score, stars, name), stars) + scores_ext for score, stars, name, scores_ext in highScores[difficulty]]
    return binascii.hexlify(Cerealizer.dumps(s))

  def save(self):
    if self.highScores != {}:
      self._set("scores",        self.getObfuscatedScores(part = parts[GUITAR_PART]))
      self._set("scores_ext",    self.getObfuscatedScoresExt(part = parts[GUITAR_PART]))
    if self.highScoresRhythm != {}:
      self._set("scores_rhythm", self.getObfuscatedScores(part = parts[RHYTHM_PART]))
      self._set("scores_rhythm_ext", self.getObfuscatedScoresExt(part = parts[RHYTHM_PART]))
    if self.highScoresBass != {}:
      self._set("scores_bass",   self.getObfuscatedScores(part = parts[BASS_PART]))
      self._set("scores_bass_ext",   self.getObfuscatedScoresExt(part = parts[BASS_PART]))
    if self.highScoresLead != {}:
      self._set("scores_lead",   self.getObfuscatedScores(part = parts[LEAD_PART]))
      self._set("scores_lead_ext",   self.getObfuscatedScoresExt(part = parts[LEAD_PART]))
    #myfingershurt: drums :)
    if self.highScoresDrum != {}:
      self._set("scores_drum", self.getObfuscatedScores(part = parts[DRUM_PART]))
      self._set("scores_drum_ext", self.getObfuscatedScoresExt(part = parts[DRUM_PART]))
    #akedrou
    if self.highScoresVocal != {}:
      self._set("scores_vocal", self.getObfuscatedScores(part = parts[VOCAL_PART]))
      self._set("scores_vocal_ext", self.getObfuscatedScoresExt(part = parts[VOCAL_PART]))
    
    if os.access(os.path.dirname(self.fileName), os.W_OK) == True:
      f = open(self.fileName, "w")
      self.info.write(f)
      f.close()
    
  def _get(self, attr, type = None, default = ""):
    try:
      v = self.info.get("song", attr)
    except:
      v = default
    if v is not None and type:
      v = type(v)
    return v

#  def getDifficulties(self):
#    # Tutorials only have the medium difficulty
#    if self.tutorial:
#      return [difficulties[HAR_DIF]]
#
#    if self._difficulties is not None:
#      return self._difficulties
#
#    # See which difficulties are available
#    try:
#
#      noteFileName = self.noteFileName
#      
#      Log.debug("Retrieving difficulties from: " + noteFileName)
#      info = MidiInfoReaderNoSections()
#      midiIn = midi.MidiInFile(info, noteFileName)
#      try:
#        midiIn.read()
#      except MidiInfoReaderNoSections.Done:
#        pass
#      info.difficulties.sort(lambda a, b: cmp(b.id, a.id))
#      self._difficulties = info.difficulties
#    except:
#      self._difficulties = difficulties.values()
#    return self._difficulties

  def getPartDifficulties(self):
    if len(self._partDifficulties) is not 0:
      return self._partDifficulties
    self.getParts()
    return self._partDifficulties
  
  partDifficulties = property(getPartDifficulties)
  
  def getMidiStyle(self):
    if self._midiStyle is not None:
      return self._midiStyle
    self.getParts()
    return self._midiStyle
  
  midiStyle = property(getMidiStyle)
  
  def getParts(self):
    if self._parts is not None:
      return self._parts

    # See which parts are available
    try:
      noteFileName = self.noteFileName
      Log.debug("Retrieving parts from: " + noteFileName)
      info = MidiPartsDiffReader()

      midiIn = midi.MidiInFile(info, noteFileName)
      midiIn.read()
      if info.parts == []:
        Log.debug("Improperly named tracks. Attempting to force first track guitar.")
        info = MidiPartsDiffReader(forceGuitar = True)
        midiIn = midi.MidiInFile(info, noteFileName)
        midiIn.read()
      if info.parts == []:
        Log.warn("No tracks found!")
        raise Exception
      self._midiStyle = info.midiStyle
      info.parts.sort(lambda b, a: cmp(b.id, a.id))
      self._parts = info.parts
      for part in info.parts:
        if self.tutorial:
          self._partDifficulties[part.id] = [difficulties[HAR_DIF]]
          continue
        info.difficulties[part.id].sort(lambda a, b: cmp(a.id, b.id))
        self._partDifficulties[part.id] = info.difficulties[part.id]
    except:
      Log.warn("Note file not parsed correctly. Selected part and/or difficulty may not be available.")
      self._parts = parts.values()
      for part in self._parts:
        self._partDifficulties[part.id] = difficulties.values()
    return self._parts

  def getName(self):
    return self._get("name")

  def setName(self, value):
    self._set("name", value)

  def getArtist(self):
    return self._get("artist")

  def getAlbum(self):
    return self._get("album")

  def getGenre(self):
    return self._get("genre")
    
  def getIcon(self):
    return self._get("icon")
  
  def getBossBattle(self):
    return self._get("boss_battle")

  def getDiffSong(self):
    return self._get("diff_band", int, -1)

  def getDiffGuitar(self):
    return self._get("diff_guitar", int, -1)

  def getDiffDrums(self):
    return self._get("diff_drums", int, -1)

  def getDiffBass(self):
    return self._get("diff_bass", int, -1)     

  def getYear(self):
    return self._get("year")

  def getLoading(self):
    return self._get("loading_phrase")

  def getCassetteColor(self):
    c = self._get("cassettecolor")
    if c:
      return Theme.hexToColor(c)
  
  def setCassetteColor(self, color):
    self._set("cassettecolor", Theme.colorToHex(color))
  
  def setArtist(self, value):
    self._set("artist", value)

  def setAlbum(self, value):
    self._set("album", value)

  def setGenre(self, value):
    self._set("genre", value)
    
  def setIcon(self, value):
    self._set("icon", value)
    
  def setBossBattle(self, value):
    self._set("boss_battle", value)

  def setDiffSong(self, value):
    self._set("diff_band", value)

  def setDiffGuitar(self, value):
    self._set("diff_guitar", value)

  def setDiffDrums(self, value):
    self._set("diff_drums", value)

  def setDiffBass(self, value):
    self._set("diff_bass", value)       

  def setYear(self, value):
    self._set("year", value)

  def setLoading(self, value):
    self._set("loading_phrase", value)
    
  def getScoreHash(self, difficulty, score, stars, name):
    return hashlib.sha1("%d%d%d%s" % (difficulty.id, score, stars, name)).hexdigest()
    
  def getDelay(self):
    return self._get("delay", int, 0)
    
  def setDelay(self, value):
    return self._set("delay", value)

  def getFrets(self):
    return self._get("frets")

  def setFrets(self, value):
    self._set("frets", value)
    
  def getVersion(self):
    return self._get("version")

  def setVersion(self, value):
    self._set("version", value)

  def getTags(self):
    return self._get("tags")

  def setTags(self, value):
    self._set("tags", value)

  def getHopo(self):
    return self._get("hopo")

  def setHopo(self, value):
    self._set("hopo", value)

  def getCount(self):
    return self._get("count")

  def setCount(self, value):
    self._set("count", value)

  def getEighthNoteHopo(self):
    return self._get("eighthnote_hopo")

  def setEighthNoteHopo(self, value):
    self._set("eighthnote_hopo", value)

  def getLyrics(self):
    return self._get("lyrics")

  def setLyrics(self, value):
    self._set("lyrics", value)    
        

  def getHighscoresWithPartString(self, difficulty, part = str(parts[GUITAR_PART]) ):
    if part == str(parts[GUITAR_PART]):
      highScores = self.highScores
    elif part == str(parts[RHYTHM_PART]):
      highScores = self.highScoresRhythm
    elif part == str(parts[BASS_PART]):
      highScores = self.highScoresBass
    elif part == str(parts[LEAD_PART]):
      highScores = self.highScoresLead
    #myfingershurt: drums :)
    elif part == str(parts[DRUM_PART]):
      highScores = self.highScoresDrum
    elif part == str(parts[VOCAL_PART]): #akedrou - vocals!
      highScores = self.highScoresVocal
    else:
      highScores = self.highScores
      
    try:
      return highScores[difficulty]
    except KeyError:
      return []


  def getHighscores(self, difficulty, part = parts[GUITAR_PART]):
    if part == parts[GUITAR_PART]:
      highScores = self.highScores
    elif part == parts[RHYTHM_PART]:
      highScores = self.highScoresRhythm
    elif part == parts[BASS_PART]:
      highScores = self.highScoresBass
    elif part == parts[LEAD_PART]:
      highScores = self.highScoresLead
    #myfingershurt: drums :)
    elif part == parts[DRUM_PART]:
      highScores = self.highScoresDrum
    elif part == parts[VOCAL_PART]: #akedrou - vocals!
      highScores = self.highScoresVocal
    else:
      highScores = self.highScores
      
    try:
      return highScores[difficulty]
    except KeyError:
      return []
      
  def uploadHighscores(self, url, songHash, part = parts[GUITAR_PART]):
    if part == parts[VOCAL_PART]: #not implemented
      return False
    try:
      d = {
        "songName": self.songName,
        "songHash": songHash,
        "scores":   self.getObfuscatedScores(part = part),
        "scores_ext": self.getObfuscatedScoresExt(part = part),
        "version":  "%s-3.100" % Version.appNameSexy(),
        "songPart": part
      }
      data = urllib.urlopen(url + "?" + urllib.urlencode(d)).read()
      Log.debug("Score upload result: %s" % data)
      #return data == "True"
      return data   #MFH - want to return the actual result data.
    except Exception, e:
      Log.error("Score upload error: %s" % e)
      return False
    return True
  
  def addHighscore(self, difficulty, score, stars, name, part = parts[GUITAR_PART], scoreExt = (0, 0, 0, "RF-mod", 0, "None", 0)):
    if part == parts[GUITAR_PART]:
      highScores = self.highScores
    elif part == parts[RHYTHM_PART]:
      highScores = self.highScoresRhythm
    elif part == parts[BASS_PART]:
      highScores = self.highScoresBass
    elif part == parts[LEAD_PART]:
      highScores = self.highScoresLead
    #myfingershurt: drums :)
    elif part == parts[DRUM_PART]:
      highScores = self.highScoresDrum
    elif part == parts[VOCAL_PART]: #akedrou - vocals!
      highScores = self.highScoresVocal
    else:
      highScores = self.highScores

    if not difficulty in highScores:
      highScores[difficulty] = []
    highScores[difficulty].append((score, stars, name, scoreExt))
    highScores[difficulty].sort(lambda a, b: {True: -1, False: 1}[a[0] > b[0]])
    highScores[difficulty] = highScores[difficulty][:5]
    for i, scores in enumerate(highScores[difficulty]):
      _score, _stars, _name, _scores_ext = scores
      if _score == score and _stars == stars and _name == name:
        return i
    return -1

  def isTutorial(self):
    return self._get("tutorial", int, 0) == 1

  def findTag(self, find, value = None):
    for tag in self.tags.split(','):
      temp = tag.split('=')
      if find == temp[0]:
        if value == None:
          return True
        elif len(temp) == 2 and value == temp[1]:
          return True

    return False
      

  def getSections(self):    #MFH
    if self._sections is not None:
      return self._sections
    # See which sections are available
    try:
      noteFileName = self.noteFileName
      Log.debug("Retrieving sections from: " + noteFileName)
      info = MidiSectionReader()
      midiIn = midi.MidiInFile(info, noteFileName)
      try:
        midiIn.read()
      except MidiSectionReader.Done:
        pass
      self._sections = info.sections
      if len(self._sections) <= 1:
        self._sections = info.noteCountSections
        self._sections.insert(0,["0:00 -> Start", 0.0])
        
        #MFH - only log if enabled
        Log.warn("Song.py: Using auto-generated note count sections...")
        if self.logSections == 1:
          Log.debug("Practice sections: " + str(self._sections))
            
      else:
        self._sections.insert(0,["0:00 -> Start", 0.0])

        #MFH - only log if enabled
        if self.logSections == 1:
          Log.debug("Practice sections: " + str(self._sections))

    except Exception, e:
      Log.warn("Song.py: Unable to retrieve section names for practice mode selection: %s" % e)
      self._sections = None
    return self._sections


    #coolguy567's unlock system
  def getUnlockID(self):
    return self._get("unlock_id")
    
  def getUnlockRequire(self):
    return self._get("unlock_require")
  
  def getUnlockText(self):
    return self._get("unlock_text", default = _("This song is locked."))
  
  # This takes True or False, not the value in the ini
  def setCompleted(self, value):
    if value:
      self._set("unlock_completed", len(self.name) * len(self.artist) + 1)
    else:
      self._set("unlock_completed", 0)
    
  # This returns True or False, not the value in the ini
  def getCompleted(self):
    iniValue = self._get("unlock_completed", int, default = 0)
    if iniValue == len(self.name) * len(self.artist) + 1: # yay, security through obscurity!
      return True
    else:
      return False
  
  def setLocked(self, value):
    self.locked = value
  
  # WARNING this will only work on a SongInfo loaded via getAvailableSongs
  # (yeah, I know)
  def getLocked(self):
    return self.locked


  #MFH - adding song.ini setting to allow fretter to specify early hit window size (none, half, or full)
  def getEarlyHitWindowSize(self):  #MFH
    return self._get("early_hit_window_size", str)

  def setEarlyHitWindowSize(self, value):   #MFH
    self._set("early_hit_window_size", value)



  def getHopoFreq(self):  #MFH
    return self._get("hopofreq")

  def setHopoFreq(self, value):   #MFH
    self._set("hopofreq", value)

    
  name          = property(getName, setName)
  artist        = property(getArtist, setArtist)
  year          = property(getYear, setYear)
  loading       = property(getLoading, setLoading)
  delay         = property(getDelay, setDelay)
  tutorial      = property(isTutorial)
#  difficulties  = property(getDifficulties)
  cassetteColor = property(getCassetteColor, setCassetteColor)
  #New RF-mod Items
  parts         = property(getParts)
  frets         = property(getFrets, setFrets)
  version       = property(getVersion, setVersion)
  tags          = property(getTags, setTags)
  hopo          = property(getHopo, setHopo)
  count         = property(getCount, setCount)
  lyrics        = property(getLyrics, setLyrics)
  EighthNoteHopo = property(getEighthNoteHopo, setEighthNoteHopo)
  hopofreq = property(getHopoFreq, setHopoFreq)   #MFH
  #New rb2 setlist
  album         = property(getAlbum, setAlbum)
  genre         = property(getGenre, setGenre)
  icon         = property(getIcon, setIcon)
  diffSong     = property(getDiffSong, setDiffSong)
  diffGuitar   = property(getDiffGuitar, setDiffGuitar)
  diffBass     = property(getDiffBass, setDiffBass)
  diffDrums    = property(getDiffDrums, setDiffDrums)
  #boss battles
  bossBattle   = property(getBossBattle, setBossBattle)
  #May no longer be necessary
  folder        = False
  
  completed     = property(getCompleted, setCompleted)
  sections      = property(getSections)   #MFH

  early_hit_window_size = property(getEarlyHitWindowSize, setEarlyHitWindowSize)   #MFH


class LibraryInfo(object):
  def __init__(self, libraryName, infoFileName):
    self.libraryName   = libraryName
    self.fileName      = infoFileName
    self.info          = Config.MyConfigParser()
    self.songCount     = 0

    self.artist = None

    self.logClassInits = Config.get("game", "log_class_inits")
    if self.logClassInits == 1:
      Log.debug("LibraryInfo class init (song.py)...")
    

    try:
      self.info.read(infoFileName)
    except:
      pass

    # Set a default name
    if not self.name:
      self.name = os.path.basename(os.path.dirname(self.fileName))
    if Config.get("performance", "disable_libcount") == True:
      return
    # Count the available songs
    libraryRoot = os.path.dirname(self.fileName)
    for name in os.listdir(libraryRoot):
      if not os.path.isdir(os.path.join(libraryRoot, name)) or name.startswith("."):
      #if not os.path.isdir(os.path.join(libraryRoot, name)):
        continue
      if os.path.isfile(os.path.join(libraryRoot, name, "notes.mid")):
        self.songCount += 1
      elif os.path.isfile(os.path.join(libraryRoot, name, "notes-unedited.mid")):
        self.songCount += 1


  def _set(self, attr, value):
    if not self.info.has_section("library"):
      self.info.add_section("library")
    if type(value) == unicode:
      value = value.encode(Config.encoding)
    else:
      value = str(value)
    self.info.set("library", attr, value)
    
  def save(self):
    if os.access(os.path.dirname(self.fileName), os.W_OK) == True:
      f = open(self.fileName, "w")
      self.info.write(f)
      f.close()
    
  def _get(self, attr, type = None, default = ""):
    try:
      v = self.info.get("library", attr)
    except:
      v = default
    if v is not None and type:
      v = type(v)
    return v

  def getName(self):
    return self._get("name")

  def setName(self, value):
    self._set("name", value)

  def getColor(self):
    c = self._get("color")
    if c:
      return Theme.hexToColor(c)
  
  def setColor(self, color):
    self._set("color", Theme.colorToHex(color))
        
  name          = property(getName, setName)
  color         = property(getColor, setColor)




class BlankSpaceInfo(object): #MFH
  #def __init__(self, config, section):
  def __init__(self, nameToDisplay = ""):
    #self.info    = config
    #self.section = section
    self.nameToDisplay = nameToDisplay

    self.logClassInits = Config.get("game", "log_class_inits")
    if self.logClassInits == 1:
      Log.debug("BlankSpaceInfo class init (song.py)...")

    self.artist = None    #MFH - prevents search errors

  def _set(self, attr, value):
    if type(value) == unicode:
      value = value.encode(Config.encoding)
    else:
      value = str(value)
    self.info.set(self.section, attr, value)
    
  def _get(self, attr, type = None, default = ""):
    try:
      v = self.info.get(self.section, attr)
    except:
      v = default
    if v is not None and type:
      v = type(v)
    return v

  def getName(self):
    #return self._get("name")
    return self.nameToDisplay

  def setName(self, value):
    self._set("name", value)

  def getColor(self):
    c = self._get("color")
    if c:
      return Theme.hexToColor(c)
  
  def setColor(self, color):
    self._set("color", Theme.colorToHex(color))

  def getUnlockID(self):
    return ""

         
  name          = property(getName, setName)
  color         = property(getColor, setColor)



class CareerResetterInfo(object): #MFH
  #def __init__(self, config, section):
  def __init__(self):
    #self.info    = config
    #self.section = section

    self.logClassInits = Config.get("game", "log_class_inits")
    if self.logClassInits == 1:
      Log.debug("CareerResetterInfo class init (song.py)...")

    self.artist = None    #MFH - prevents search errors

  def _set(self, attr, value):
    if type(value) == unicode:
      value = value.encode(Config.encoding)
    else:
      value = str(value)
    self.info.set(self.section, attr, value)
    
  def _get(self, attr, type = None, default = ""):
    try:
      v = self.info.get(self.section, attr)
    except:
      v = default
    if v is not None and type:
      v = type(v)
    return v

  def getName(self):
    #return self._get("name")
    return _("Reset Career")

  def setName(self, value):
    self._set("name", value)

  def getColor(self):
    c = self._get("color")
    if c:
      return Theme.hexToColor(c)
  
  def setColor(self, color):
    self._set("color", Theme.colorToHex(color))
         
  name          = property(getName, setName)
  color         = property(getColor, setColor)


class RandomSongInfo(object): #MFH
  #def __init__(self, config, section):
  def __init__(self):
    #self.info    = config
    #self.section = section

    self.logClassInits = Config.get("game", "log_class_inits")
    if self.logClassInits == 1:
      Log.debug("RandomSongInfo class init (song.py)...")

    self.artist = None    #MFH - prevents search errors

  def _set(self, attr, value):
    if type(value) == unicode:
      value = value.encode(Config.encoding)
    else:
      value = str(value)
    self.info.set(self.section, attr, value)
    
  def _get(self, attr, type = None, default = ""):
    try:
      v = self.info.get(self.section, attr)
    except:
      v = default
    if v is not None and type:
      v = type(v)
    return v

  def getName(self):
    #return self._get("name")
    return _("   (Random Song)")

  def setName(self, value):
    self._set("name", value)

  def getColor(self):
    c = self._get("color")
    if c:
      return Theme.hexToColor(c)
  
  def setColor(self, color):
    self._set("color", Theme.colorToHex(color))
         
  name          = property(getName, setName)
  color         = property(getColor, setColor)  


#coolguy567's unlock system
class TitleInfo(object):
  def __init__(self, config, section):
    self.info    = config
    self.section = section

    self.logClassInits = Config.get("game", "log_class_inits")
    if self.logClassInits == 1:
      Log.debug("TitleInfo class init (song.py)...")

    self.artist = None    #MFH - prevents search errors

  def _set(self, attr, value):
    if type(value) == unicode:
      value = value.encode(Config.encoding)
    else:
      value = str(value)
    self.info.set(self.section, attr, value)
    
  def _get(self, attr, type = None, default = ""):
    try:
      v = self.info.get(self.section, attr)
    except:
      v = default
    if v is not None and type:
      v = type(v)
    return v

  def getName(self):
    return self._get("name")

  def setName(self, value):
    self._set("name", value)

  def getColor(self):
    c = self._get("color")
    if c:
      return Theme.hexToColor(c)
  
  def setColor(self, color):
    self._set("color", Theme.colorToHex(color))
        
  def getUnlockID(self):
    return self._get("unlock_id")
        
  name          = property(getName, setName)
  color         = property(getColor, setColor)


class SortTitleInfo(object):
  def __init__(self, nameToDisplay):
    
    self.nameToDisplay = nameToDisplay

    self.logClassInits = Config.get("game", "log_class_inits")
    if self.logClassInits == 1:
      Log.debug("TitleInfo class init (song.py)...")

    self.artist = None    #MFH - prevents search errors

  def _set(self, attr, value):
    if type(value) == unicode:
      value = value.encode(Config.encoding)
    else:
      value = str(value)
    self.info.set(self.section, attr, value)
    
  def _get(self, attr, type = None, default = ""):
    try:
      v = self.info.get(self.section, attr)
    except:
      v = default
    if v is not None and type:
      v = type(v)
    return v

  def getName(self):
    return self.nameToDisplay

  def setName(self, value):
    self._set("name", value)

  def getColor(self):
    c = self._get("color")
    if c:
      return Theme.hexToColor(c)
  
  def setColor(self, color):
    self._set("color", Theme.colorToHex(color))
        
  def getUnlockID(self):
    return self.nameToDisplay
        
  name          = property(getName, setName)
  color         = property(getColor, setColor)


class Event:
  def __init__(self, length):
    self.length = length


class MarkerNote(Event): #MFH
  def __init__(self, number, length, endMarker = False):
    Event.__init__(self, length)
    self.number   = number
    self.endMarker = endMarker
    self.happened = False
    
  def __repr__(self):
    return "<#%d>" % self.number


class Note(Event):
  def __init__(self, number, length, special = False, tappable = 0, star = False, finalStar = False):
    Event.__init__(self, length)
    self.number   = number
    self.played   = False
    self.special  = special
    self.tappable = tappable
    #RF-mod
    self.hopod   = False
    self.skipped = False
    self.flameCount = 0
    self.star = star
    self.finalStar = finalStar
    self.noteBpm = 0.0
    
    
  def __repr__(self):
    return "<#%d>" % self.number

class VocalNote(Event):
  def __init__(self, note, length, tap = False):
    Event.__init__(self, length)
    self.note = note
    self.phrase = 0
    self.played = False
    self.stopped = False
    self.accuracy = 0.0
    self.tap = tap
    self.speak = False
    self.extra = False #not sure what this is yet - "^"
    self.lyric = None
    self.heldNote = False

class Bars(Event):
  def __init__(self, barType):
    Event.__init__(self, barType)
    self.barType   = barType #0 half-beat, 1 beat, 2 measure
    self.soundPlayed = False
    
  def __repr__(self):
    return "<#%d>" % self.barType

class Tempo(Event):
  def __init__(self, bpm):
    Event.__init__(self, 0)
    self.bpm = bpm
    
  def __repr__(self):
    return "<%d bpm>" % self.bpm

class TextEvent(Event):
  def __init__(self, text, length):
    Event.__init__(self, length)
    self.text = text

  def __repr__(self):
    return "<%s>" % self.text

class PictureEvent(Event):
  def __init__(self, fileName, length):
    Event.__init__(self, length)
    self.fileName = fileName

class Track:    #MFH - Changing Track class to a base class.  NoteTrack and TempoTrack will extend it.
  granularity = 50
  
  def __init__(self, engine):
    self.events = []
    self.allEvents = []
    self.marked = False

    self.currentIndex = None   #MFH
    self.maxIndex = None   #MFH

    if engine is not None:
      self.logClassInits = Config.get("game", "log_class_inits")
      if self.logClassInits == 1:
        Log.debug("Track class init (song.py)...")

    #self.chordFudge = 1

    #self.hopoTick = engine.config.get("coffee", "hopo_frequency")
    #self.hopoTickCheat = engine.config.get("coffee", "hopo_freq_cheat")
    #self.songHopoFreq = engine.config.get("game", "song_hopo_freq")

  def __getitem__(self, index):
    #if isinstance(index, slice):
    #    return [x**2 for x in index]
    #else:
    #    return index**2
    #return index**2
    return self.allEvents[index]

  def __len__(self):
    return len(self.allEvents)

  def addEvent(self, time, event):
    for t in range(int(time / self.granularity), int((time + event.length) / self.granularity) + 1):
      if len(self.events) < t + 1:
        n = t + 1 - len(self.events)
        n *= 8
        self.events = self.events + [[] for n in range(n)]
      self.events[t].append((time - (t * self.granularity), event))
    self.allEvents.append((time, event))
    
    if self.maxIndex == None:   #MFH - tracking track size
      self.maxIndex = 0
      self.currentIndex = 0
    else:
      self.maxIndex += 1

  def removeEvent(self, time, event):
    for t in range(int(time / self.granularity), int((time + event.length) / self.granularity) + 1):
      e = (time - (t * self.granularity), event)
      if t < len(self.events) and e in self.events[t]:
        self.events[t].remove(e)
    if (time, event) in self.allEvents:
      self.allEvents.remove((time, event))
      
      #MFH - tracking track size
      if self.maxIndex != None:
        self.maxIndex -= 1
        if self.maxIndex < 0:
          self.maxIndex = None
          self.currentIndex = None

  def getNextEvent(self, lookAhead = 0):  #MFH
    if self.maxIndex != None and self.currentIndex != None:
      #lookAhead > 0 means look that many indices ahead of the Next event
      if (self.currentIndex + lookAhead) <= self.maxIndex:
        return self.allEvents[self.currentIndex + lookAhead]
    return None
  
  def getPrevEvent(self, lookBehind = 0):  #MFH - lookBehind of 0 = return previous event.
    if self.maxIndex != None and self.currentIndex != None:
      #lookBehind > 0 means look that many indices behind of the Prev event
      if (self.currentIndex - 1 - lookBehind) >= 0:
        return self.allEvents[self.currentIndex - 1 - lookBehind]
    return None

  def getEvents(self, startTime, endTime):
    t1, t2 = [int(x) for x in [startTime / self.granularity, endTime / self.granularity]]
    if t1 > t2:
      t1, t2 = t2, t1

    events = []
    for t in range(max(t1, 0), min(len(self.events), t2)):
      for diff, event in self.events[t]:
        time = (self.granularity * t) + diff
        if not (time, event) in events:
          events.append((time, event))
    return events

  def getAllEvents(self):
    return self.allEvents

  def reset(self):
    if self.maxIndex:
      self.currentIndex = 0
    for eventList in self.events:
      for time, event in eventList:
        if isinstance(event, Note):
          event.played = False
          event.hopod = False
          event.skipped = False
          event.flameCount = 0
        if isinstance(event, MarkerNote):
          event.happened = False

class VocalTrack(Track):
  def __init__(self, engine):
    self.allNotes = {}
    self.allWords = {}
    self.starTimes = []
    self.minPitch = 127
    self.maxPitch = 0
    self.logTempoEvents = 0
    if engine:
      self.logTempoEvents = engine.config.get("log",   "log_tempo_events")
    Track.__init__(self, engine)
    
  def getAllNotes(self):
    return self.allNotes
  
  def addEvent(self, time, event):
    if isinstance(event, VocalNote) or isinstance(event, VocalPhrase):
      Track.addEvent(self, time, event)

  def removeTempoEvents(self):
    for time, event in self.allEvents:
      if isinstance(event, Tempo):
        self.allEvents.remove((time, event))
        if self.logTempoEvents == 1:
          Log.debug("Tempo event removed from VocalTrack during cleanup: " + str(event.bpm) + "bpm")
  
  def markPhrases(self):
    phraseId = 0
    stars = []
    phraseTimes = []
    markStars = False
    if len(self.starTimes) < 2:
      markStars = True
      Log.warn("This song does not appear to have any vocal star power events - falling back on auto-generation.")
    for time, event in self.getAllEvents():
      if isinstance(event, VocalPhrase):
        if time in self.starTimes and not markStars:
          event.star = True
        if time in phraseTimes:
          Log.warn("Phrase repeated - some lyric phrase errors may occur.")
          #self.removeEvent(time, event)
          phraseId += 1
          continue
        if markStars and phraseId+1 % 7 == 0:
          event.star = True
        phraseTimes.append(time)
        phraseId += 1
    index = 0
    for time, tuple in self.allNotes.iteritems():
      phraseId = 0
      for i, phraseTime in enumerate(self.getAllEvents()):
        if time > phraseTime[0] and time < phraseTime[0] + phraseTime[1].length:
          phraseId = i
          if phraseId < 0:
            phraseId = 0
          break
      tuple[1].phrase = phraseId
      if not tuple[1].tap:
        try:
          lyric = self.allWords[tuple[0]]
        except KeyError:
          lyric = None
        if lyric:
          if lyric.find("+") >= 0:
            tuple[1].heldNote = True
          else:
            if lyric.find("#") >= 0:
              tuple[1].speak = True
              tuple[1].lyric = lyric.strip("#")
            elif lyric.find("^") >= 0:
              tuple[1].extra = True
              tuple[1].lyric = lyric.strip("^")
            else:
              tuple[1].lyric = lyric
      else:
        self.allEvents[phraseId][1].tapPhrase = True
      self.allEvents[phraseId][1].addEvent(tuple[0], tuple[1])
      self.allEvents[phraseId][1].minPitch = min(self.allEvents[phraseId][1].minPitch, tuple[1].note)
      self.allEvents[phraseId][1].maxPitch = max(self.allEvents[phraseId][1].maxPitch, tuple[1].note)
    for time, event in self.getAllEvents():
      if isinstance(event, VocalPhrase):
        event.sort()
  
  def reset(self):
    if self.maxIndex:
      self.currentIndex = 0
    for eventList in self.events:
      for time, event in eventList:
        if isinstance(event, VocalPhrase):
          for time, note in event.allEvents:
            note.played = False
            note.stopped = False
            note.accuracy = 0.0

class VocalPhrase(VocalTrack, Event):
  def __init__(self, length, star = False):
    Event.__init__(self, length)
    VocalTrack.__init__(self, engine = None)
    self.star = star
    self.tapPhrase = False
  
  def sort(self):
    eventDict = {}
    newEvents = []
    for time, event in self.allEvents:
      if isinstance(event, VocalNote):
        eventDict[int(time)] = (time, event)
    times = eventDict.keys()
    times.sort()
    for time in times:
      newEvents.append(eventDict[time])
    self.allEvents = newEvents

class TempoTrack(Track):    #MFH - special Track type for tempo events
  def __init__(self, engine):
    Track.__init__(self, engine)
    self.currentBpm = DEFAULT_BPM

  def reset(self):
    self.currentBpm = DEFAULT_BPM
    
  #MFH - function to track current tempo in realtime based on time / position
  def getCurrentTempo(self, pos):   #MFH
    if self.currentIndex:
      tempEventHolder = self.getNextEvent()   #MFH - check if next BPM change is here yet
      if tempEventHolder:
        time, event = tempEventHolder
        if pos >= time:
          self.currentIndex += 1
          self.currentBpm = event.bpm
    return self.currentBpm

  def getNextTempoChange(self, pos):  #MFH
    if self.currentIndex:
      #return self.getNextEvent(lookAhead = 1)
      return self.getNextEvent()
    return None 
  
  def searchCurrentTempo(self, pos):    #MFH - will hunt through all tempo events to find it - intended for use during initializations only!
    foundBpm = None
    foundTime = None
    for time, event in self.allEvents:
      if not foundBpm or not foundTime:
        foundBpm = event.bpm
        foundTime = time
      else:
        #MFH - want to discard if the foundTime is before pos, but this event is after pos.
        # -- also want to take newer BPM if time > foundTime >= pos
        if time <= pos:   #MFH - first required condition.
          if time > foundTime:    #MFH - second required condition for sorting.
            foundBpm = event.bpm
            foundTime = time
    if foundBpm:
      return foundBpm
    else:   #MFH - return default BPM if no events
      return DEFAULT_BPM

class NoteTrack(Track):   #MFH - special Track type for note events, with marking functions
  def __init__(self, engine):
    Track.__init__(self, engine)
    self.chordFudge = 1

    self.hopoTick = engine.config.get("coffee", "hopo_frequency")
    self.hopoTickCheat = engine.config.get("coffee", "hopo_freq_cheat")
    self.songHopoFreq = engine.config.get("game", "song_hopo_freq")
    self.logTempoEvents = engine.config.get("log",   "log_tempo_events")

  def removeTempoEvents(self):
    for time, event in self.allEvents:
      if isinstance(event, Tempo):
        self.allEvents.remove((time, event))
        if self.logTempoEvents == 1:
          Log.debug("Tempo event removed from NoteTrack during cleanup: " + str(event.bpm) + "bpm")


  def markHopoRF(self, EighthNH, songHopoFreq):
    lastTick = 0
    lastTime  = 0
    lastEvent = Note
    
    tickDelta = 0
    noteDelta = 0

    try:
      songHopoFreq = int(songHopoFreq)
    except Exception, e:
      songHopoFreq = None
    #  Log.warn("Song.ini HOPO Frequency setting is invalid -- forcing Normal (value 1)")
      if self.songHopoFreq == 1 and (songHopoFreq == 0 or songHopoFreq == 1 or songHopoFreq == 2 or songHopoFreq == 3 or songHopoFreq == 4 or songHopoFreq == 5):
        Log.debug("markHopoRF: song-specific HOPO frequency %d forced" % songHopoFreq)
        self.hopoTick = songHopoFreq

    #dtb file says 170 ticks
    hopoDelta = 170
    if str(EighthNH) == "1":
        hopoDelta = 250
    else:
        hopoDelta = 170
    self.chordFudge = 10

    if self.hopoTick == 0:
      ticksPerBeat = 960
    elif self.hopoTick == 1:
      ticksPerBeat = 720
    elif self.hopoTick == 2:
      ticksPerBeat = 480
    else:
      ticksPerBeat = 240
      hopoDelta = 250
      
    if self.hopoTickCheat == 1:
      ticksPerBeat = 360
    elif self.hopoTickCheat == 2:
      ticksPerBeat = 240
      
    hopoNotes = []
    chordNotes = []
    sameNotes = []
    bpmNotes = []
    firstTime = 1

    #If already processed abort   
    if self.marked == True:
      return
    
    for time, event in self.allEvents:
      if isinstance(event, Tempo):
        bpmNotes.append([time, event])
        continue
      if not isinstance(event, Note):
        continue
      
      while bpmNotes and time >= bpmNotes[0][0]:
        #Adjust to new BPM
        #bpm = bpmNotes[0][1].bpm
        bpmTime, bpmEvent = bpmNotes.pop(0)
        bpm = bpmEvent.bpm
      

      tick = (time * bpm * ticksPerBeat) / 60000.0
      lastTick = (lastTime * bpm * ticksPerBeat) / 60000.0
      
      #skip first note
      if firstTime == 1:
        event.tappable = -3
        lastEvent = event
        lastTime  = time
        firstTime = 0
        continue

      tickDelta = tick - lastTick        
      noteDelta = event.number - lastEvent.number

      #previous note and current note HOPOable      
      if tickDelta <= hopoDelta:
        #Add both notes to HOPO list even if duplicate.  Will come out in processing
        if (not hopoNotes) or not (hopoNotes[-1][0] == lastTime and hopoNotes[-1][1] == lastEvent):
          #special case for first marker note.  Change it to a HOPO start
          if not hopoNotes and lastEvent.tappable == -3:
            lastEvent.tappable = 1
          #this may be incorrect if a bpm event happened inbetween this note and last note
          hopoNotes.append([lastTime, bpmEvent])
          hopoNotes.append([lastTime, lastEvent])

        hopoNotes.append([bpmTime, bpmEvent])
        hopoNotes.append([time, event])
        
      #HOPO Over        
      if tickDelta > hopoDelta:
        if hopoNotes != []:
          #If the last event is the last HOPO note, mark it as a HOPO end
          if lastEvent.tappable != -1 and hopoNotes[-1][1] == lastEvent:
            if lastEvent.tappable >= 0:
              lastEvent.tappable = 3
            else:
              lastEvent.tappable = -1

      #This is the same note as before
      elif noteDelta == 0:
        #Add both notes to bad list even if duplicate.  Will come out in processing
        sameNotes.append(lastEvent)
        sameNotes.append(event)
        lastEvent.tappable = -2
        event.tappable = -2
            
      #This is a chord
      elif tickDelta < self.chordFudge:
        #Add both notes to bad list even if duplicate.  Will come out in processing
        if len(chordNotes) != 0 and chordNotes[-1] != lastEvent:
          chordNotes.append(lastEvent)
        chordNotes.append(event)
        lastEvent.tappable = -1
        event.tappable = -1
        
      lastEvent = event
      lastTime = time
    else:
      #Add last note to HOPO list if applicable
      if noteDelta != 0 and tickDelta > 1.5 and tickDelta < hopoDelta and isinstance(event, Note):
        hopoNotes.append([time, bpmEvent])
        hopoNotes.append([time, event])

    firstTime = 1
    note = None

    for note in list(chordNotes):
      #chord notes -1
      note.tappable = -1   

    for note in list(sameNotes):
      #same note in string -2
      note.tappable = -2

    bpmNotes = []
    
    for time, note in list(hopoNotes):
      if isinstance(note, Tempo):
        bpmNotes.append([time, note])
        continue
      if not isinstance(note, Note):
        continue
      while bpmNotes and time >= bpmNotes[0][0]:
        #Adjust to new BPM
        #bpm = bpmNotes[0][1].bpm
        bpmTime, bpmEvent = bpmNotes.pop(0)
        bpm = bpmEvent.bpm

      if firstTime == 1:
        if note.tappable >= 0:
          note.tappable = 1
        lastEvent = note
        firstTime = 0
        continue

      #need to recompute (or carry forward) BPM at this time
      tick = (time * bpm * ticksPerBeat) / 60000.0
      lastTick = (lastTime * bpm * ticksPerBeat) / 60000.0
      tickDelta = tick - lastTick

      #current Note Invalid
      if note.tappable < 0:
        #If current note is invalid for HOPO, and previous note was start of a HOPO section, then previous note not HOPO
        if lastEvent.tappable == 1:
          lastEvent.tappable = 0
        #If current note is beginning of a same note sequence, it's valid for END of HOPO only
        elif lastEvent.tappable > 0:
          lastEvent.tappable = 3
      #current note valid
      elif note.tappable >= 0:
        #String of same notes can be followed by HOPO
        if note.tappable == 3:
          #This is the end of a valid HOPO section
          if lastEvent.tappable == 1 or lastEvent.tappable == 2:
            lastEvent = note
            lastTime = time
            continue
          if lastEvent.tappable == -2:
            #If its the same note again it's invalid
            if lastEvent.number == note.number:
              note.tappable = -2
            else:
              lastEvent.tappable = 1
          elif lastEvent.tappable == 0:
            lastEvent.tappable = 1
          #If last note was invalid or end of HOPO section, and current note is end, it is really not HOPO
          elif lastEvent.tappable != 2 and lastEvent.tappable != 1:
            note.tappable = 0
          #If last event was invalid or end of HOPO section, current note is start of HOPO
          else:
            note.tappable = 1
        elif note.tappable == 2:
          if lastEvent.tappable == -2:
            note.tappable = 1
          elif lastEvent.tappable == -1:
            note.tappable = 0
        elif note.tappable == 1:
          if lastEvent.tappable == 2:
            note.tappable = 0
        else:
          if lastEvent.tappable == -2:
            if tickDelta <= hopoDelta:
              lastEvent.tappable = 1
              
          if lastEvent.tappable != 2 and lastEvent.tappable != 1:
            note.tappable = 1
          else:
            if note.tappable == 1:
              note.tappable = 1
            else:
              note.tappable = 2
      lastEvent = note
      lastTime = time
    else:
      if note != None:
        #Handle last note
        #If it is the start of a HOPO, it's not really a HOPO
        if note.tappable == 1:
          note.tappable = 0
        #If it is the middle of a HOPO, it's really the end of a HOPO
        elif note.tappable == 2:
          note.tappable = 3      
    self.marked = True

    for time, event in self.allEvents:
      if isinstance(event, Tempo):
        bpmNotes.append([time, event])
        continue
      if not isinstance(event, Note):
        continue



#---------------------
  def markHopoGH2(self, EighthNH, HoposAfterChords, songHopoFreq):
    lastTick = 0
    lastTime  = 0
    lastEvent = Note
    
    tickDelta = 0
    noteDelta = 0

    try:
      songHopoFreq = int(songHopoFreq)
    except Exception, e:
      songHopoFreq = None
    #  Log.warn("Song.ini HOPO Frequency setting is invalid -- forcing Normal (value 1)")
    if self.songHopoFreq == 1 and (songHopoFreq == 0 or songHopoFreq == 1 or songHopoFreq == 2 or songHopoFreq == 3 or songHopoFreq == 4 or songHopoFreq == 5):
      Log.debug("markHopoGH2: song-specific HOPO frequency %d forced" % songHopoFreq)
      self.hopoTick = songHopoFreq


    #dtb file says 170 ticks
    hopoDelta = 170
    if str(EighthNH) == "1":
        hopoDelta = 250
    else:
        hopoDelta = 170

    #chordFudge = 10
    self.chordFudge = 1   #MFH - there should be no chord fudge.

    if self.hopoTick == 0:
      ticksPerBeat = 960
    elif self.hopoTick == 1:
      ticksPerBeat = 720
    elif self.hopoTick == 2:
      ticksPerBeat = 480
    else:
      ticksPerBeat = 240
      hopoDelta = 250
      
    if self.hopoTickCheat == 1:
      ticksPerBeat = 360
    elif self.hopoTickCheat == 2:
      ticksPerBeat = 240
      
    hopoNotes = []

    #myfingershurt:
    tickDeltaBeforeLast = 0     #3 notes in the past
    lastTickDelta = 0   #2 notes in the past

    
    bpmNotes = []
    firstTime = 1

    #MFH - to prevent crashes on songs without a BPM set
    bpmEvent = None
    bpm = None

    #If already processed abort   
    if self.marked == True:
      return
    
    for time, event in self.allEvents:
      if isinstance(event, Tempo):
        bpmNotes.append([time, event])
        continue
      if not isinstance(event, Note):
        continue


      
      while bpmNotes and time >= bpmNotes[0][0]:
        #Adjust to new BPM
        #bpm = bpmNotes[0][1].bpm
        bpmTime, bpmEvent = bpmNotes.pop(0)
        bpm = bpmEvent.bpm

      if not bpm:
        bpm = DEFAULT_BPM

      tick = (time * bpm * ticksPerBeat) / 60000.0
      lastTick = (lastTime * bpm * ticksPerBeat) / 60000.0
      


     
      #skip first note
      if firstTime == 1:
        event.tappable = -3
        lastEvent = event
        lastTime  = time
        eventBeforeLast = lastEvent
        timeBeforeLast = lastTime
        eventBeforeEventBeforeLast = eventBeforeLast
        timeBeforeTimeBeforeLast = timeBeforeLast
        firstTime = 0
        continue

      #tickDeltaBeforeTickDeltaBeforeLast = tickDeltaBeforeLast    #4 notes in the past
      tickDeltaBeforeLast = lastTickDelta     #3 notes in the past
      lastTickDelta = tickDelta   #2 notes in the past
      
      tickDelta = tick - lastTick        
      noteDelta = event.number - lastEvent.number
      #myfingershurt: This initial sweep drops any notes within the timing 
      # threshold into the hopoNotes array (which would be more aptly named,
      #  the "potentialHopoNotes" array).  Another loop down below 
      #   further refines the HOPO determinations...
      
      #previous note and current note HOPOable      
      if tickDelta <= hopoDelta:
        #Add both notes to HOPO list even if duplicate.  Will come out in processing
        if (not hopoNotes) or not (hopoNotes[-1][0] == lastTime and hopoNotes[-1][1] == lastEvent):
          #special case for first marker note.  Change it to a HOPO start
          if not hopoNotes and lastEvent.tappable == -3:
            lastEvent.tappable = 1
          #this may be incorrect if a bpm event happened inbetween this note and last note


          if bpmEvent:
            hopoNotes.append([lastTime, bpmEvent])
          
          hopoNotes.append([lastTime, lastEvent])
          

        if bpmEvent:
          hopoNotes.append([bpmTime, bpmEvent])

        hopoNotes.append([time, event])




        
      #HOPO definitely over - time since last note too great.
      if tickDelta > hopoDelta:
        if hopoNotes != []:
          #If the last event is the last HOPO note, mark it as a HOPO end
          if lastEvent.tappable != -1 and hopoNotes[-1][1] == lastEvent:
            if lastEvent.tappable >= 0:
              lastEvent.tappable = 3
            else:
              lastEvent.tappable = -1






    #note pattern:
      # R R R R R
      # Y       Y
    #should be
      # 1 3-2-2-4
    #first pass:
      #actual: if first RY considered "same note" as next R:
      #-4 0-2-2
       #if last RY considered "same note" as prev R:
      #-4 0-2-2-2
      #actual: if first RY not considered "same note" as next R:
      #-4 0-2-2
    

      #This is the same note as before
      elif noteDelta == 0:
        #Add both notes to bad list even if duplicate.  Will come out in processing
        #myfingershurt: to fix same-note HOPO bug.
        if HoposAfterChords:
          if lastEvent.tappable != -4:   #if the last note was not a chord,
            if eventBeforeLast.tappable == -4 and lastTickDelta <= hopoDelta:  #and if the event before last was a chord, don't remark the last one.
              event.tappable = -5
            else:
              event.tappable = -2
            #myfingershurt: yeah, mark the last one.  
            lastEvent.tappable = -2
        else:
          event.tappable = -2
          lastEvent.tappable = -2







            
      #This is a chord
      #myfingershurt: both this note and the last note are listed at the same time
      #to allow after-chord HOPOs, we need a separate identification for "chord" notes
      #and also might need to track the "last" chord notes in a separate array
      elif tickDelta < self.chordFudge:
        #Add both notes to bad list even if duplicate.  Will come out in processing
        #myfingershurt:
        if HoposAfterChords:
          if eventBeforeLast.tappable == -2 and lastTickDelta <= hopoDelta:
            if eventBeforeEventBeforeLast.tappable >= 0 and tickDeltaBeforeLast <= hopoDelta:
              eventBeforeLast.tappable = -5   #special case that needs to be caught
            if lastEvent.tappable == -2:    #catch case where event before last event was marked as the same note
              if eventBeforeEventBeforeLast.tappable >= 0 and tickDeltaBeforeLast <= hopoDelta:
                eventBeforeLast.tappable = 0
          lastEvent.tappable = -4
          event.tappable = -4
        #keep track of chords as they are found
        else:
          lastEvent.tappable = -1
          event.tappable = -1

        


        
      #myfingershurt: to really check marking, need to track 3 notes into the past. 
      eventBeforeEventBeforeLast = eventBeforeLast
      timeBeforeTimeBeforeLast = timeBeforeLast
      eventBeforeLast = lastEvent
      timeBeforeLast = lastTime
      lastEvent = event
      lastTime = time

    else:
      #Add last note to HOPO list if applicable
      #myfingershurt:
      if noteDelta != 0 and tickDelta > self.chordFudge and tickDelta < hopoDelta and isinstance(event, Note):

        if bpmEvent:
          hopoNotes.append([time, bpmEvent])

        hopoNotes.append([time, event])

      #myfingershurt marker: (next - FOR loop)----

    #myfingershurt: comments - updated marking system
    #--at this point, the initial note marking sweep has taken place.  Here is further marking of hopoNotes.
    #the .tappable property has special meanings:
    # -5 = This note is the same as the last note, which was a HOPO, and the next note is a chord.
    #       or, this note is the same as the last note, which was a HOPO, so no matter what it shouldn't be tappable.
    # -4 = This note is part of a chord
    # -3 = This is the very first note in a song
    # -2 = This note is part of a string of "same notes"
    # -1 = This note is too far away from the last note to be tappable.
    #  0 = This note is nowhere near another note and must be strummed (also default value)
    #  1 = This note is the first in a string of HOPOs - this note must be strummed to initiate the HOPOs following it!
    #  2 = This note is in the midst of HOPOs
    #  3 = This note is the final of a string of HOPOs


    firstTime = 1
    note = None

    tickDeltaBeforeTickDeltaBeforeLast = 0    #4 notes in the past
    tickDeltaBeforeLast = 0     #3 notes in the past
    lastTickDelta = 0   #2 notes in the past

    bpmNotes = []
    
    for time, note in list(hopoNotes):
      if isinstance(note, Tempo):
        bpmNotes.append([time, note])
        continue
      if not isinstance(note, Note):
        continue
      while bpmNotes and time >= bpmNotes[0][0]:
        #Adjust to new BPM
        #bpm = bpmNotes[0][1].bpm
        bpmTime, bpmEvent = bpmNotes.pop(0)
        bpm = bpmEvent.bpm

      if firstTime == 1:
        if note.tappable >= 0:
          note.tappable = 1
        lastEvent = note
        lastTime = time
        firstTime = 0
        eventBeforeLast = lastEvent
        eventBeforeEventBeforeLast = eventBeforeLast
        eventBeforeEventBeforeEventBeforeLast = eventBeforeLast
        continue




      #need to recompute (or carry forward) BPM at this time

      tickDeltaBeforeTickDeltaBeforeLast = tickDeltaBeforeLast    #4 notes in the past
      tickDeltaBeforeLast = lastTickDelta     #3 notes in the past
      lastTickDelta = tickDelta   #2 notes in the past


      tick = (time * bpm * ticksPerBeat) / 60000.0
      lastTick = (lastTime * bpm * ticksPerBeat) / 60000.0
      tickDelta = tick - lastTick



      #current Note Invalid for HOPO----------
      if note.tappable < 0:

    #test note pattern:
      # R   R     R R R R
      # Y Y Y Y Y     Y
    #first pass:
      #-4-2-4-2-5-2-2-4 
    #second pass:
      # 1 3 1 3 1 3-2-4 

        #myfingershurt:
        #If current note is beginning of a same note sequence, it's valid for END of HOPO only
        #need to alter this to not screw up single-same-note-before chords:
        #elif lastEvent.tappable == 2 and note.tappable == -2:
        if (lastEvent.tappable == 1 or lastEvent.tappable == 2) and note.tappable == -2:
          note.tappable = 3
        #If current note is invalid for HOPO, and previous note was start of a HOPO section, then previous note not HOPO
        elif lastEvent.tappable == 1:
          lastEvent.tappable = 0


        #and let's not forget the special case when two same-note-sequences on different frets are in sequence:
        elif lastEvent.tappable == -2 and note.tappable == -2 and lastEvent.number != note.number:
          lastEvent.tappable = 1
          note.tappable = 3
        #special case where the new -5 note is followed by a string same notes on a different fret:
        elif lastEvent.tappable == -5 and note.tappable == -2:
          lastEvent.tappable = 1
          note.tappable = 3
        
        #special case where last note was a chord, and this note is counted as the same note as the last in the chord
        elif lastEvent.tappable == -4 and note.tappable == -2:
          thisNoteShouldStillBeAHopo = True
          #determine the highest note in the chord:
          topChordNote = lastEvent.number    
          if eventBeforeLast.number > topChordNote:
            topChordNote = eventBeforeLast.number
          numChordNotes = 2
          #now to determine how many notes were in that chord:
          if tickDeltaBeforeLast < self.chordFudge:  #is there a 3rd note in the same chord?
            if eventBeforeEventBeforeLast.number > topChordNote:
              topChordNote = eventBeforeEventBeforeLast.number
            numChordNotes = 3
            if tickDeltaBeforeTickDeltaBeforeLast < self.chordFudge:  #is there a 4th note in the same chord?
              if eventBeforeEventBeforeEventBeforeLast.number > topChordNote:
                topChordNote = eventBeforeEventBeforeEventBeforeLast.number
              numChordNotes = 4
          if topChordNote == note.number:   #only if the note number matches the top chord note do we outlaw the HOPO.
            thisNoteShouldStillBeAHopo = False
          if thisNoteShouldStillBeAHopo:
            #here, need to go back and mark all notes in this chord as tappable = 1 not just the last one.
            #chord max of 4 frets (5 is just ridiculous) - so if "lastEvent" is the 4th, must go back and change 3rd, 2nd, and 1st
            lastEvent.tappable = 1
            eventBeforeLast.tappable = 1    #at least 2 notes in chord
            if numChordNotes >= 3:  #is there a 3rd note in the same chord?
              eventBeforeEventBeforeLast.tappable = 1
              if numChordNotes == 4:  #is there a 4th note in the same chord?
                eventBeforeEventBeforeEventBeforeLast.tappable = 1
            note.tappable = 3

        #If current note is invalid for HOPO, and previous note was a HOPO section, then previous note is end of HOPO
        elif lastEvent.tappable > 0:
          lastEvent.tappable = 3
      #current note valid
      elif note.tappable >= 0:
        #String of same notes can be followed by HOPO
        if note.tappable == 3:

          #myfingershurt: the new after-chord HOPO special logic needs to also be applied here
          if lastEvent.tappable == -5:  #special case, still can be HOPO start
            lastEvent.tappable = 1
          if lastEvent.tappable == -4:  #chord
            thisNoteShouldStillBeAHopo = True
            #determine the highest note in the chord:
            topChordNote = lastEvent.number    
            if eventBeforeLast.number > topChordNote:
              topChordNote = eventBeforeLast.number
            numChordNotes = 2
            #now to determine how many notes were in that chord:
            if tickDeltaBeforeLast < self.chordFudge:  #is there a 3rd note in the same chord?
              if eventBeforeEventBeforeLast.number > topChordNote:
                topChordNote = eventBeforeEventBeforeLast.number
              numChordNotes = 3
              if tickDeltaBeforeTickDeltaBeforeLast < self.chordFudge:  #is there a 4th note in the same chord?
                if eventBeforeEventBeforeEventBeforeLast.number > topChordNote:
                  topChordNote = eventBeforeEventBeforeEventBeforeLast.number
                numChordNotes = 4
            if topChordNote == note.number:   #only if the note number matches the top chord note do we outlaw the HOPO.
              thisNoteShouldStillBeAHopo = False
            if thisNoteShouldStillBeAHopo:
              #here, need to go back and mark all notes in this chord as tappable = 1 not just the last one.
              #chord max of 4 frets (5 is just ridiculous) - so if "lastEvent" is the 4th, must go back and change 3rd, 2nd, and 1st
              lastEvent.tappable = 1
              eventBeforeLast.tappable = 1    #at least 2 notes in chord
              if numChordNotes >= 3:  #is there a 3rd note in the same chord?
                eventBeforeEventBeforeLast.tappable = 1
                if numChordNotes == 4:  #is there a 4th note in the same chord?
                  eventBeforeEventBeforeEventBeforeLast.tappable = 1
            else:
              note.tappable = -1

          #This is the end of a valid HOPO section
          if lastEvent.tappable == 1 or lastEvent.tappable == 2:
            eventBeforeEventBeforeEventBeforeLast = eventBeforeLast
            #timeBeforeTimeBeforeTimeBeforeLast = timeBeforeLast
            eventBeforeEventBeforeLast = eventBeforeLast
            #timeBeforeTimeBeforeLast = timeBeforeLast
            eventBeforeLast = lastEvent
            #timeBeforeLast = lastTime
            lastEvent = note
            lastTime = time
            continue
          if lastEvent.tappable == -2:
            #If its the same note again it's invalid
            if lastEvent.number == note.number:
              note.tappable = -2
            else:
              lastEvent.tappable = 1
          elif lastEvent.tappable == 0:
            lastEvent.tappable = 1
          #If last note was invalid or end of HOPO section, and current note is end, it is really not HOPO
          elif lastEvent.tappable != 2 and lastEvent.tappable != 1:
            note.tappable = 0
          #If last event was invalid or end of HOPO section, current note is start of HOPO
          else:
            note.tappable = 1
        elif note.tappable == 2:
          if lastEvent.tappable == -2:
            note.tappable = 1
          elif lastEvent.tappable == -1:
            note.tappable = 0
          elif lastEvent.tappable == 3:
            lastEvent.tappable = 2



        elif note.tappable == 1:
          if lastEvent.tappable == 2:
            note.tappable = 0



        #myfingershurt: default case, tappable=0
        else:
          if lastEvent.tappable == -5:  #special case, still can be HOPO start
            lastEvent.tappable = 1
          if lastEvent.tappable == -4:  #chord
            thisNoteShouldStillBeAHopo = True
            #determine the highest note in the chord:
            topChordNote = lastEvent.number    
            if eventBeforeLast.number > topChordNote:
              topChordNote = eventBeforeLast.number
            numChordNotes = 2
            #now to determine how many notes were in that chord:
            if tickDeltaBeforeLast < self.chordFudge:  #is there a 3rd note in the same chord?
              if eventBeforeEventBeforeLast.number > topChordNote:
                topChordNote = eventBeforeEventBeforeLast.number
              numChordNotes = 3
              if tickDeltaBeforeTickDeltaBeforeLast < self.chordFudge:  #is there a 4th note in the same chord?
                if eventBeforeEventBeforeEventBeforeLast.number > topChordNote:
                  topChordNote = eventBeforeEventBeforeEventBeforeLast.number
                numChordNotes = 4
            if topChordNote == note.number:   #only if the note number matches the top chord note do we outlaw the HOPO.
              thisNoteShouldStillBeAHopo = False
            if thisNoteShouldStillBeAHopo:
              #here, need to go back and mark all notes in this chord as tappable = 1 not just the last one.
              #chord max of 4 frets (5 is just ridiculous) - so if "lastEvent" is the 4th, must go back and change 3rd, 2nd, and 1st
              lastEvent.tappable = 1
              eventBeforeLast.tappable = 1    #at least 2 notes in chord
              if numChordNotes >= 3:  #is there a 3rd note in the same chord?
                eventBeforeEventBeforeLast.tappable = 1
                if numChordNotes == 4:  #is there a 4th note in the same chord?
                  eventBeforeEventBeforeEventBeforeLast.tappable = 1
            else:
              note.tappable = -1

          if lastEvent.tappable == -2 and tickDelta <= hopoDelta:  #same note
            lastEvent.tappable = 1
          if lastEvent.tappable == 3 and tickDelta <= hopoDelta:   #supposedly last of a HOPO
            lastEvent.tappable = 2
          
          if lastEvent.tappable != 2 and lastEvent.tappable != 1:
            note.tappable = 1
          else:
            if note.tappable == 1:
              note.tappable = 1
            else:
              note.tappable = 2
      

      #myfingershurt: to really check marking, need to track 4 notes into the past.
      eventBeforeEventBeforeEventBeforeLast = eventBeforeLast
      eventBeforeEventBeforeLast = eventBeforeLast
      eventBeforeLast = lastEvent
      lastEvent = note
      lastTime = time
    else:
      if note != None:
        #Handle last note
        #If it is the start of a HOPO, it's not really a HOPO
        if note.tappable == 1:
          note.tappable = 0
        #If it is the middle of a HOPO, it's really the end of a HOPO
        elif note.tappable == 2:
          #myfingershurt: here, need to check if the last note is a HOPO after chord and is being merged into the chord (which happens if too close to end of song)
          if tickDelta < self.chordFudge:
            note.tappable = -4
          else:
            note.tappable = 3      
    self.marked = True

  def markBars(self):
    tempoTime = []
    tempoBpm = []

    #get all the bpm changes and their times

    #MFH - TODO - count tempo events.  If 0, realize and log that this is a song with no tempo events - and go mark all 120BPM bars.
    endBpm = None
    endTime = None
    for time, event in self.allEvents:
      if isinstance(event, Tempo):
        tempoTime.append(time)
        tempoBpm.append(event.bpm)
        endBpm = event.bpm
        continue
      if isinstance(event, Note):
        endTime = time + event.length + 30000
        continue
    
    if endTime:
      tempoTime.append(endTime)
    if endBpm:
      tempoBpm.append(endBpm)

    #calculate and add the measures/beats/half-beats
    passes = 0  
    limit = len(tempoTime)
    time = tempoTime[0]
    THnote = 256.0 #256th note
    drawBar = True
    i = 0
    while i < (limit - 1):
      msTotal = tempoTime[i+1] - time
      if msTotal == 0:
        i += 1
        continue
      tempbpm = tempoBpm[i]
      nbars = (msTotal * (tempbpm / (240.0 / THnote) )) / 1000.0 
      inc = msTotal / nbars

      while time < tempoTime[i+1]:
        if drawBar == True:
          if (passes % (THnote / 1.0) == 0.0): #256/1
            event = Bars(2) #measure
            self.addEvent(time, event)
          elif (passes % (THnote / 4.0) == 0.0): #256/4
            event = Bars(1) #beat
            self.addEvent(time, event)
          elif (passes % (THnote / 8.0) == 0.0): #256/8
            event = Bars(0) #half-beat
            self.addEvent(time, event)
          
          passes = passes + 1
          
        time = time + inc
        drawBar = True

      if time > tempoTime[i+1]:
        time = time - inc
        drawBar = False
        
      i += 1

    #add the last measure/beat/half-beat
    if time == tempoTime[i]:
      if (passes % (THnote / 1.0) == 0.0): #256/1
        event = Bars(2) #measure
        self.addEvent(time, event)
      elif (passes % (THnote / 4.0) == 0.0): #256/4
        event = Bars(1) #beat
        self.addEvent(time, event)
      elif (passes % (THnote / 8.0) == 0.0): #256/8
        event = Bars(0) #half-beat
        self.addEvent(time, event)


class Song(object):
  def __init__(self, engine, infoFileName, songTrackName, guitarTrackName, rhythmTrackName, noteFileName, scriptFileName = None, partlist = [parts[GUITAR_PART]], drumTrackName = None, crowdTrackName = None):
    self.engine        = engine
    
    self.logClassInits = self.engine.config.get("game", "log_class_inits")
    if self.logClassInits == 1:
      Log.debug("Song class init (song.py)...")
    
    self.info         = SongInfo(infoFileName)
    self.tracks = []
    for i in partlist:
      if i == parts[VOCAL_PART]:
        self.tracks.append([VocalTrack(self.engine)])
      else:
        self.tracks.append([NoteTrack(self.engine) for t in range(len(difficulties))])
    
    self.difficulty   = [difficulties[EXP_DIF] for i in partlist]
    self._playing     = False
    self.start        = 0.0
    self.noteFileName = noteFileName
    
    #self.bpm          = None
    self.bpm          = DEFAULT_BPM     #MFH - enforcing a default / fallback tempo of 120 BPM

    #self.period       = 0
    self.period = 60000.0 / self.bpm    #MFH - enforcing a default / fallback tempo of 120 BPM

    self.readyToGo = False    #MFH - to prevent anything from happening until all prepration & initialization is complete!

    
    self.parts        = partlist
    self.delay        = self.engine.config.get("audio", "delay")
    self.delay        += self.info.delay
    self.missVolume   = self.engine.config.get("audio", "miss_volume")
    #self.songVolume   = self.engine.config.get("audio", "songvol") #akedrou

    self.hasMidiLyrics = False
    self.midiStyle = self.info.midiStyle

    self.earlyHitWindowSize = EARLY_HIT_WINDOW_HALF   #MFH - holds the detected early hit window size for the current song

    self.hasStarpowerPaths = False
    self.hasFreestyleMarkings = False

    #MFH - add a separate variable to house the special text event tracks:
    #MFH - special text-event tracks for the separated text-event list variable
    #TK_SCRIPT = 0         #script.txt events
    #TK_SECTIONS = 1       #Section events
    #TK_GUITAR_SOLOS = 2   #Guitar Solo start/stop events
    #TK_LYRICS = 3         #RB MIDI Lyric events
    #TK_UNUSED_TEXT = 4    #Unused / other text events
    self.eventTracks       = [Track(self.engine) for t in range(0,5)]    #MFH - should result in eventTracks[0] through [4]
    
    self.midiEventTracks   = []
    for i in partlist:
      if i == parts[VOCAL_PART]:
        self.midiEventTracks.append([None])
      else:
        self.midiEventTracks.append([Track(self.engine) for t in range(len(difficulties))])
    
    self.vocalEventTrack   = VocalTrack(self.engine)

    self.tempoEventTrack = TempoTrack(self.engine)   #MFH - need a separated Tempo/BPM track!

    self.breMarkerTime = None

    self.music = None


    #self.slowDownFactor = self.engine.config.get("audio", "speed_factor")
    #self.engine.setSpeedFactor(self.slowDownFactor)    #MFH 

    # load the tracks
    #if self.engine.audioSpeedFactor == 1:    #MFH - only use the music track   
    if songTrackName:
      self.music       = Audio.Music(songTrackName)

    self.guitarTrack = None
    self.rhythmTrack = None
    
    #myfingershurt:
    self.drumTrack = None
    #akedrou
    self.crowdTrack = None
    #if songTrackName:
    #  drumTrackName = songTrackName.replace("song.ogg","drums.ogg")

    try:
      if guitarTrackName:
        self.guitarTrack = Audio.StreamingSound(self.engine, self.engine.audio.getChannel(1), guitarTrackName)
    except Exception, e:
      Log.warn("Unable to load guitar track: %s" % e)

    try:
      if rhythmTrackName:
        self.rhythmTrack = Audio.StreamingSound(self.engine, self.engine.audio.getChannel(2), rhythmTrackName)
    except Exception, e:
      Log.warn("Unable to load rhythm track: %s" % e)

    
    try:
      if drumTrackName:
        self.drumTrack = Audio.StreamingSound(self.engine, self.engine.audio.getChannel(3), drumTrackName)
    except Exception, e:
      Log.warn("Unable to load drum track: %s" % e)
      
    try:
      if crowdTrackName:
        self.crowdTrack = Audio.StreamingSound(self.engine, self.engine.audio.getChannel(4), crowdTrackName)
    except Exception, e:
      Log.warn("Unable to load crowd track: %s" % e)

    #MFH - single audio track song detection
    self.singleTrackSong = False
    if (self.music == None) or (self.guitarTrack == None and self.rhythmTrack == None and self.drumTrack == None):
      if not (self.music == None and self.guitarTrack == None and self.rhythmTrack == None and self.drumTrack == None):
        self.singleTrackSong = True
        self.missVolume = self.engine.config.get("audio", "single_track_miss_volume")   #MFH - force single-track miss volume setting instead
        Log.debug("Song with only a single audio track identified - single-track miss volume applied: " + str(self.missVolume))


    # load the notes   
    if noteFileName:
      Log.debug("Retrieving notes from: " + noteFileName)
      midiIn = midi.MidiInFile(MidiReader(self), noteFileName)
      midiIn.read()
      
    # load the script
    if scriptFileName and os.path.isfile(scriptFileName):
      scriptReader = ScriptReader(self, open(scriptFileName))
      scriptReader.read()

  #myfingershurt: new function to re-retrieve the a/v delay setting so it can be changed in-game:
  def refreshAudioDelay(self):  
    self.delay        = self.engine.config.get("audio", "delay")
    self.delay        += self.info.delay

  #myfingershurt: new function to refresh the miss volume after a pause
  def refreshMissVolume(self):  
    if self.singleTrackSong:
      self.missVolume = self.engine.config.get("audio", "single_track_miss_volume")   #MFH - force single-track miss volume setting instead
    else:
      self.missVolume   = self.engine.config.get("audio", "miss_volume")

  
  def getCurrentTempo(self, pos):  #MFH
    return self.tempoEventTrack.getCurrentTempo(pos)


  def getHash(self):
    h = hashlib.sha1()
    f = open(self.noteFileName, "rb")
    bs = 1024
    while 1:
      data = f.read(bs)
      if not data: break
      h.update(data)
    return h.hexdigest()
  
  def setBpm(self, bpm):
    self.bpm    = bpm
    self.period = 60000.0 / self.bpm

  def save(self):
    self.info.save()
    f = open(self.noteFileName + ".tmp", "wb")
    midiOut = MidiWriter(self, midi.MidiOutFile(f))
    midiOut.write()
    f.close()

    # Rename the output file after it has been succesfully written
    shutil.move(self.noteFileName + ".tmp", self.noteFileName)

  def play(self, start = 0.0):
    self.start = start
    
    #RF-mod No longer needed?
    
    if self.engine.audioSpeedFactor == 1:  #MFH - shut this track up if slowing audio down!    
      self.music.play(0, start / 1000.0)
      self.music.setVolume(1.0)
    else:
      self.music.play(1.0/self.engine.audioSpeedFactor, start / 1000.0)  #tell music to loop 2 times for 1/2 speed, 4 times for 1/4 speed (so it doesn't end early)
      self.music.setVolume(0.0)   
    
    if self.guitarTrack:
      assert start == 0.0
      self.guitarTrack.play()
    if self.rhythmTrack:
      assert start == 0.0
      self.rhythmTrack.play()
    #myfingershurt
    if self.drumTrack:
      assert start == 0.0
      self.drumTrack.play()
    if self.crowdTrack:
      assert start == 0.0
      self.crowdTrack.play()
    self._playing = True

  def pause(self):
    self.music.pause()
    self.engine.audio.pause()

  def unpause(self):
    self.music.unpause()
    self.engine.audio.unpause()

  def setInstrumentVolume(self, volume, part):
    if part == parts[GUITAR_PART]:
      self.setGuitarVolume(volume)
    elif part == parts[BASS_PART]:
      self.setRhythmVolume(volume)
    elif part == parts[RHYTHM_PART]:
      self.setRhythmVolume(volume)
    elif part == parts[DRUM_PART]:
      self.setDrumVolume(volume)
    else:
      self.setRhythmVolume(volume)
      
  def setGuitarVolume(self, volume):
    if self.guitarTrack:
      if volume == 0:
        self.guitarTrack.setVolume(self.missVolume)
      else:
        self.guitarTrack.setVolume(volume)
    #This is only used if there is no guitar.ogg to lower the volume of song.ogg instead of muting this track
    else:
      if volume == 0:
        self.music.setVolume(self.missVolume * 1.5)
      else:
        self.music.setVolume(volume)

  def setRhythmVolume(self, volume):
    if self.rhythmTrack:
      if volume == 0:
        self.rhythmTrack.setVolume(self.missVolume)
      else:
        self.rhythmTrack.setVolume(volume)
  
  def setDrumVolume(self, volume):
    if self.drumTrack:
      if volume == 0:
        self.drumTrack.setVolume(self.missVolume)
      else:
        self.drumTrack.setVolume(volume)
        
  #stump: pitch bending
  def setInstrumentPitch(self, pitch, part):
    if part == parts[GUITAR_PART]:
      if self.guitarTrack:
        self.guitarTrack.setPitchBend(pitch)
      else:
        self.music.setPitchBend(pitch)
    elif part == parts[DRUM_PART]:
      pass
    else:
      if self.rhythmTrack:
        self.rhythmTrack.setPitchBend(pitch)

  def resetInstrumentPitch(self, part):
    if part == parts[GUITAR_PART]:
      if self.guitarTrack:
        self.guitarTrack.stopPitchBend()
      else:
        self.music.stopPitchBend()
    elif part == parts[DRUM_PART]:
      pass
    else:
      if self.rhythmTrack:
        self.rhythmTrack.stopPitchBend()

  def setBackgroundVolume(self, volume):
    self.music.setVolume(volume)
  
  def setCrowdVolume(self, volume):
    if self.crowdTrack:
      self.crowdTrack.setVolume(volume)
  
  def setAllTrackVolumes(self, volume):
    self.setBackgroundVolume(volume)
    self.setDrumVolume(volume)
    self.setRhythmVolume(volume)
    self.setGuitarVolume(volume)
    self.setCrowdVolume(volume)
    
  def stop(self):
    for tracks in self.tracks:
      for track in tracks:
        track.reset()

    for tracks in self.midiEventTracks:
      for track in tracks:
        if track is not None:
          track.reset()

      
    if self.music:  #MFH
      self.music.stop()
      self.music.rewind()

    if self.guitarTrack:
      self.guitarTrack.stop()
    if self.rhythmTrack:
      self.rhythmTrack.stop()
    if self.drumTrack:
      self.drumTrack.stop()
    if self.crowdTrack:
      self.crowdTrack.stop()
    self._playing = False

  def fadeout(self, time):
    for tracks in self.tracks:
      for track in tracks:
        track.reset()
    
    self.music.fadeout(time)
    if self.guitarTrack:
      self.guitarTrack.fadeout(time)
    if self.rhythmTrack:
      self.rhythmTrack.fadeout(time)
    if self.drumTrack:
      self.drumTrack.fadeout(time)
    if self.crowdTrack:
      self.crowdTrack.fadeout(time)
    self._playing = False

  def clearPause(self):
    self.music.isPause = False
    self.music.toUnpause = False
    self.music.pausePos = 0.0
  
  def getPosition(self):
    if not self._playing:
      pos = 0.0
    else:
      pos = self.music.getPosition()


      if self.engine.audioSpeedFactor != 1:   #MFH - to correct for slowdown's positioning
        #pos /= self.engine.audioSpeedFactor    
        pos *= self.engine.audioSpeedFactor
        
    if pos < 0.0:
      pos = 0.0
    return pos + self.start - self.delay

  def isPlaying(self):
    #MFH - check here to see if any audio tracks are still playing first!
    #MFH from the Future sez: but only if in slowdown mode!
    if self.engine.audioSpeedFactor == 1:
      return self._playing and self.music.isPlaying()
    else:   #altered speed mode!
      if self.guitarTrack and self.guitarTrack.streamIsPlaying() > 0: 
        return True
      if self.rhythmTrack and self.rhythmTrack.streamIsPlaying() > 0:
        return True
      if self.drumTrack and self.drumTrack.streamIsPlaying() > 0:
        return True
      else:
        return self._playing and self.music.isPlaying() 

  def getBeat(self):
    return self.getPosition() / self.period

  def update(self, ticks):
    pass

  def getTrack(self):
    return [self.tracks[i][self.difficulty[i].id] for i in range(len(self.difficulty))]

  def getIsSingleAudioTrack(self):
    return self.singleTrackSong

  track = property(getTrack)
  isSingleAudioTrack = property(getIsSingleAudioTrack)

  def getMidiEventTrack(self):   #MFH - for new special MIDI marker note track
    return [self.midiEventTracks[i][self.difficulty[i].id] for i in range(len(self.difficulty))]
  midiEventTrack = property(getMidiEventTrack)  


#MFH - translating / marking the common MIDI notes:
noteMap = {     # difficulty, note
  0x60: (EXP_DIF, 0), #=========#0x60 = 96 = C 8
  0x61: (EXP_DIF, 1),           #0x61 = 97 = Db8
  0x62: (EXP_DIF, 2),           #0x62 = 98 = D 8
  0x63: (EXP_DIF, 3),           #0x63 = 99 = Eb8
  0x64: (EXP_DIF, 4),           #0x64 = 100= E 8
  0x54: (HAR_DIF, 0), #=========#0x54 = 84 = C 7
  0x55: (HAR_DIF, 1),           #0x55 = 85 = Db7
  0x56: (HAR_DIF, 2),           #0x56 = 86 = D 7
  0x57: (HAR_DIF, 3),           #0x57 = 87 = Eb7
  0x58: (HAR_DIF, 4),           #0x58 = 88 = E 7
  0x48: (MED_DIF, 0), #=========#0x48 = 72 = C 6
  0x49: (MED_DIF, 1),           #0x49 = 73 = Db6
  0x4a: (MED_DIF, 2),           #0x4a = 74 = D 6
  0x4b: (MED_DIF, 3),           #0x4b = 75 = Eb6
  0x4c: (MED_DIF, 4),           #0x4c = 76 = E 6
  0x3c: (EAS_DIF, 0), #=========#0x3c = 60 = C 5
  0x3d: (EAS_DIF, 1),           #0x3d = 61 = Db5
  0x3e: (EAS_DIF, 2),           #0x3e = 62 = D 5
  0x3f: (EAS_DIF, 3),           #0x3f = 63 = Eb5
  0x40: (EAS_DIF, 4),           #0x40 = 64 = E 5
}

#MFH - special note numbers
starPowerMarkingNote = 103     #note 103 = G 8
overDriveMarkingNote = 116     #note 116 = G#9

freestyleMarkingNote = 124      #notes 120 - 124 = drum fills & BREs - always all 5 notes present


reverseNoteMap = dict([(v, k) for k, v in noteMap.items()])


class MidiWriter:
  def __init__(self, song, out):
    self.song         = song
    self.out          = out
    self.ticksPerBeat = 480

    self.logClassInits = Config.get("game", "log_class_inits")
    if self.logClassInits == 1:
      Log.debug("MidiWriter class init (song.py)...")
    

  def midiTime(self, time):
    return int(self.song.bpm * self.ticksPerBeat * time / 60000.0)

  def write(self):
    self.out.header(division = self.ticksPerBeat)
    self.out.start_of_track()
    self.out.update_time(0)
    if self.song.bpm:
      self.out.tempo(int(60.0 * 10.0**6 / self.song.bpm))
    else:
      self.out.tempo(int(60.0 * 10.0**6 / 122.0))

    # Collect all events
    events = [zip([difficulty] * len(track.getAllEvents()), track.getAllEvents()) for difficulty, track in enumerate(self.song.tracks[0])]
    events = reduce(lambda a, b: a + b, events)
    events.sort(lambda a, b: {True: 1, False: -1}[a[1][0] > b[1][0]])
    heldNotes = []

    for difficulty, event in events:
      time, event = event
      if isinstance(event, Note):
        time = self.midiTime(time)

        # Turn off any held notes that were active before this point in time
        for note, endTime in list(heldNotes):
          if endTime <= time:
            self.out.update_time(endTime, relative = 0)
            self.out.note_off(0, note)
            heldNotes.remove((note, endTime))

        note = reverseNoteMap[(difficulty, event.number)]
        self.out.update_time(time, relative = 0)
        self.out.note_on(0, note, event.special and 127 or 100)
        heldNotes.append((note, time + self.midiTime(event.length)))
        heldNotes.sort(lambda a, b: {True: 1, False: -1}[a[1] > b[1]])

    # Turn off any remaining notes
    for note, endTime in heldNotes:
      self.out.update_time(endTime, relative = 0)
      self.out.note_off(0, note)
      
    self.out.update_time(0)
    self.out.end_of_track()
    self.out.eof()
    self.out.write()

class ScriptReader:
  def __init__(self, song, scriptFile):
    self.song = song
    self.file = scriptFile

    self.logClassInits = Config.get("game", "log_class_inits")
    if self.logClassInits == 1:
      Log.debug("ScriptReader class init (song.py)...")
    

  def read(self):
    for line in self.file:
      if line.startswith("#") or line.isspace(): continue
      time, length, type, data = re.split("[\t ]+", line.strip(), 3)
      time   = float(time)
      length = float(length)

      if type == "text":
        event = TextEvent(data, length)
      elif type == "pic":
        event = PictureEvent(data, length)
      else:
        continue

      self.song.eventTracks[TK_SCRIPT].addEvent(time, event)  #MFH - add an event to the script.txt track

      #for track in self.song.tracks:
      #  for t in track:
      #    t.addEvent(time, event)

class MidiReader(midi.MidiOutStream):
  def __init__(self, song):
    midi.MidiOutStream.__init__(self)
    self.song = song
    self.heldNotes = {}
    self.velocity  = {}
    self.ticksPerBeat = 480
    self.tempoMarkers = []
    self.partTrack = 0
    self.partnumber = -1

    self.vocalTrack = False
    self.useVocalTrack = False
    self.vocalOverlapCheck = []

    self.logClassInits = Config.get("game", "log_class_inits")
    if self.logClassInits == 1:
      Log.debug("MidiReader class init (song.py)...")

    self.logMarkerNotes = Config.get("game", "log_marker_notes")

    self.logTempoEvents = Config.get("log",   "log_tempo_events")

    self.logSections = Config.get("game", "log_sections")
    
    self.readTextAndLyricEvents = Config.get("game","rock_band_events")
    self.guitarSoloIndex = 0
    self.guitarSoloActive = False
    self.guitarSoloSectionMarkers = False

  def addEvent(self, track, event, time = None):
    if self.partnumber == -1:
      #Looks like notes have started appearing before any part information. Lets assume its part0
      self.partnumber = self.song.parts[0]
    
    if (self.partnumber == None) and isinstance(event, Note):
      return True

    if time is None:
      time = self.abs_time()
    assert time >= 0
    
    if track is None:
      for t in self.song.tracks:
        for s in t:
          s.addEvent(time, event)
    else:
      
      tracklist = [i for i,j in enumerate(self.song.parts) if self.partnumber == j]
      for i in tracklist:
        #Each track needs it's own copy of the event, otherwise they'll interfere
        eventcopy = copy.deepcopy(event)
        if track < len(self.song.tracks[i]):
          self.song.tracks[i][track].addEvent(time, eventcopy)
  
  def addVocalEvent(self, event, time = None):
    if time is None:
      time = self.abs_time()
    assert time >= 0
    
    if not self.useVocalTrack:
      return True
    
    track = [i for i,j in enumerate(self.song.parts) if self.partnumber == j][0]
    if isinstance(event, VocalNote):
      self.song.track[track].minPitch = min(event.note, self.song.track[track].minPitch)
      self.song.track[track].maxPitch = max(event.note, self.song.track[track].maxPitch)
      self.song.track[track].allNotes[int(time)] = (time, event)
    elif isinstance(event, VocalPhrase):
      self.song.track[track].addEvent(time, event)
  
  def addVocalLyric(self, text):
    time = self.abs_time()
    assert time >= 0
    
    if not self.useVocalTrack:
      return True
    
    track = [i for i,j in enumerate(self.song.parts) if self.partnumber == j][0]
    self.song.track[track].allWords[time] = text
  
  def addVocalStar(self, time):
    if time is None:
      time = self.abs_time()
    assert time >= 0
    
    if not self.useVocalTrack:
      return True
    
    track = [i for i,j in enumerate(self.song.parts) if self.partnumber == j][0]
    self.song.track[track].starTimes.append(time)

  def addTempoEvent(self, event, time = None):    #MFH - universal Tempo track handling
    if not isinstance(event, Tempo):
      return

    if time is None:
      time = self.abs_time()
    assert time >= 0
    
    #add tempo events to the universal tempo track
    self.song.tempoEventTrack.addEvent(time, event)
    if self.logTempoEvents == 1:
      Log.debug("Tempo event added to Tempo track: " + str(time) + " - " + str(event.bpm) + "BPM" )

  def addSpecialMidiEvent(self, track, event, time = None):    #MFH
    if self.partnumber == -1:
      #Looks like notes have started appearing before any part information. Lets assume its part0
      self.partnumber = self.song.parts[0]
    
    if (self.partnumber == None) and isinstance(event, MarkerNote):
      return True

    if time is None:
      time = self.abs_time()
    assert time >= 0
    
    if track is None:
      for t in self.song.midiEventTracks:
        for s in t:
          s.addEvent(time, event)
    else:
      
      tracklist = [i for i,j in enumerate(self.song.parts) if self.partnumber == j]
      for i in tracklist:
        #Each track needs it's own copy of the event, otherwise they'll interfere
        eventcopy = copy.deepcopy(event)
        if track < len(self.song.midiEventTracks[i]):
          self.song.midiEventTracks[i][track].addEvent(time, eventcopy)


  def abs_time(self):
    def ticksToBeats(ticks, bpm):
      return (60000.0 * ticks) / (bpm * self.ticksPerBeat)
      
    if self.song.bpm:
      currentTime = midi.MidiOutStream.abs_time(self)

      scaledTime      = 0.0
      tempoMarkerTime = 0.0
      currentBpm      = self.song.bpm
      for i, marker in enumerate(self.tempoMarkers):
        time, bpm = marker
        if time > currentTime:
          break
        scaledTime += ticksToBeats(time - tempoMarkerTime, currentBpm)
        tempoMarkerTime, currentBpm = time, bpm
      return scaledTime + ticksToBeats(currentTime - tempoMarkerTime, currentBpm)
    return 0.0

  def header(self, format, nTracks, division):
    self.ticksPerBeat = division
    if nTracks == 2:
      self.partTrack = 1
    
  def tempo(self, value):
    bpm = 60.0 * 10.0**6 / value
    self.tempoMarkers.append((midi.MidiOutStream.abs_time(self), bpm))
    if not self.song.bpm:
      self.song.setBpm(bpm)
    self.addEvent(None, Tempo(bpm))
    self.addTempoEvent(Tempo(bpm))  #MFH 

  def sequence_name(self, text):
    #if self.get_current_track() == 0:
    self.partnumber = None

    tempText = "Found sequence_name in MIDI: " + text + ", recognized as "
    tempText2 = ""
    if (text == "PART GUITAR" or text == "T1 GEMS" or text == "Click" or text == "MIDI out") and parts[GUITAR_PART] in self.song.parts:
      self.partnumber = parts[GUITAR_PART]
      if self.logSections == 1:
        tempText2 = "GUITAR_PART"
    elif text == "PART RHYTHM" and parts[RHYTHM_PART] in self.song.parts:
      self.partnumber = parts[RHYTHM_PART]
      if self.logSections == 1:
        tempText2 = "RHYTHM_PART"
    elif text == "PART BASS" and parts[BASS_PART] in self.song.parts:
      self.partnumber = parts[BASS_PART]
      if self.logSections == 1:
        tempText2 = "BASS_PART"
    elif text == "PART GUITAR COOP" and parts[LEAD_PART] in self.song.parts:
      self.partnumber = parts[LEAD_PART]
      if self.logSections == 1:
        tempText2 = "LEAD_PART"
    elif (text == "PART DRUM" or text == "PART DRUMS") and parts[DRUM_PART] in self.song.parts:
      self.partnumber = parts[DRUM_PART]
      if self.logSections == 1:
        tempText2 = "DRUM_PART"
    
    elif text == "PART VOCALS": # MFH 
      self.partnumber = parts[VOCAL_PART]
      self.vocalTrack = True
      if self.partnumber in self.song.parts:
        self.useVocalTrack = True
      else:
        self.useVocalTrack = False
    else:
      self.vocalTrack = False
    #for rock band unaltered rip compatibility
    #-elif text == "PART DRUMS" and parts[DRUM_PART] in self.song.parts:
      #-self.partnumber = parts[DRUM_PART]
    #-elif self.get_current_track() <= 1 and parts [GUITAR_PART] in self.song.parts:
      #-#Oh dear, the track wasn't recognised, lets just assume it was the guitar part
      #-self.partnumber = parts[GUITAR_PART]

    if self.logSections == 1:
      Log.debug(tempText + tempText2)

    self.guitarSoloIndex = 0
    self.guitarSoloActive = False

      
  def note_on(self, channel, note, velocity):
    if self.partnumber == None:
      return
    self.velocity[note] = velocity
    self.heldNotes[(self.get_current_track(), channel, note)] = self.abs_time()

  def note_off(self, channel, note, velocity):
    if self.partnumber == None:
      return
    try:
      startTime = self.heldNotes[(self.get_current_track(), channel, note)]
      endTime   = self.abs_time()
      del self.heldNotes[(self.get_current_track(), channel, note)]
      if self.vocalTrack:
        if note > 39 and note < 84:
          self.addVocalEvent(VocalNote(note, endTime - startTime), time = startTime)
        elif note == 96: #tambourine
          self.addVocalEvent(VocalNote(note, 1, True), time = startTime)
        elif note == 105 or note == 106:
          if startTime not in self.vocalOverlapCheck:
            self.addVocalEvent(VocalPhrase(endTime - startTime), time = startTime)
            self.vocalOverlapCheck.append(startTime)
        elif note == overDriveMarkingNote:
          self.addVocalStar(startTime)
        return
      if note in noteMap:
        track, number = noteMap[note]
        self.addEvent(track, Note(number, endTime - startTime, special = self.velocity[note] == 127), time = startTime)

      #MFH: use self.midiEventTracks to store all the special MIDI marker notes, keep the clutter out of the main notes lists
      #  also -- to make use of marker notes in real-time, must add a new attribute to MarkerNote class "endMarker"
      #     if this is == True, then the note is just an event to mark the end of the previous note (which has length and is used in other ways)



      
      elif note == overDriveMarkingNote:    #MFH
        self.song.hasStarpowerPaths = True
        self.earlyHitWindowSize = EARLY_HIT_WINDOW_NONE

        #for diff in self.song.difficulty:
        for diff in difficulties:
          #self.addEvent(diff, MarkerNote(note, endTime - startTime), time = startTime)
          self.addSpecialMidiEvent(diff, MarkerNote(note, endTime - startTime), time = startTime)
          self.addSpecialMidiEvent(diff, MarkerNote(note, 1, endMarker = True), time = endTime+1)   #ending marker note
          if self.logMarkerNotes == 1:
            Log.debug("RB Overdrive MarkerNote at %f added to part: %s and difficulty: %s" % ( startTime, self.partnumber, difficulties[diff] ) )

      elif note == starPowerMarkingNote:    #MFH
        self.song.hasStarpowerPaths = True
        #for diff in self.song.difficulty:
        for diff in difficulties:
          #self.addEvent(diff, MarkerNote(note, endTime - startTime), time = startTime)
          self.addSpecialMidiEvent(diff, MarkerNote(note, endTime - startTime), time = startTime)
          self.addSpecialMidiEvent(diff, MarkerNote(note, 1, endMarker = True), time = endTime+1)   #ending marker note
          if self.logMarkerNotes == 1:
            Log.debug("GH Starpower (or RB Solo) MarkerNote at %f added to part: %s and difficulty: %s" % ( startTime, self.partnumber, difficulties[diff] ) )

      elif note == freestyleMarkingNote:    #MFH - for drum fills and big rock endings
        self.song.hasFreestyleMarkings = True
        #for diff in self.song.difficulty:
        for diff in difficulties:
          #self.addEvent(diff, MarkerNote(note, endTime - startTime), time = startTime)
          self.addSpecialMidiEvent(diff, MarkerNote(note, endTime - startTime), time = startTime)
          #self.addSpecialMidiEvent(diff, MarkerNote(note, 1, endMarker = True), time = endTime+1)   #ending marker note
          if self.logMarkerNotes == 1:
            Log.debug("RB freestyle section (drum fill or BRE) at %f added to part: %s and difficulty: %s" % ( startTime, self.partnumber, difficulties[diff] ) )

      else:
        #Log.warn("MIDI note 0x%x at %d does not map to any game note." % (note, self.abs_time()))
        pass
    except KeyError:
      Log.warn("MIDI note 0x%x on channel %d ending at %d was never started." % (note, channel, self.abs_time()))

  
  #MFH - OK - this needs to be optimized.
  #There should be a separate "Sections" track, and a separate "Lyrics" track created for their respective events
  #Then another separate "Text Events" track to put all the unused events, so they don't bog down the game when it looks through / filters / sorts these track event lists
  
  
  #myfingershurt: adding MIDI text event access
  #these events happen on their own track, and are processed after the note tracks.
  #just mark the guitar solo sections ahead of time 
  #and then write an iteration routine to go through whatever track / difficulty is being played in GuitarScene 
  #to find these markers and count the notes and add a new text event containing each solo's note count
  def text(self, text):
    if text.find("GNMIDI") < 0:   #to filter out the midi class illegal usage / trial timeout messages
      #Log.debug(str(self.abs_time()) + "-MIDI Text: " + text)
      if self.readTextAndLyricEvents > 0:

        #MFH - if sequence name is PART VOCALS then look for text event lyrics
        if self.vocalTrack:
          if text.find("[") < 0:    #not a marker
            event = TextEvent(text, 400.0)
            self.addVocalLyric(text)
            self.song.hasMidiLyrics = True
            self.song.eventTracks[TK_LYRICS].addEvent(self.abs_time(), event)  #MFH - add an event to the lyrics track

        else:        
        


          unusedEvent = None
          event = None
          gSoloEvent = False
          #also convert all underscores to spaces so it look better
          text = text.replace("_"," ")
          if text.lower().find("section") >= 0:
            self.guitarSoloSectionMarkers = True      #GH1 dont use section markers... GH2+ do
            #strip unnecessary text / chars:
            text = text.replace("section","")
            text = text.replace("[","")
            text = text.replace("]","")
            #also convert "gtr" to "Guitar"
            text = text.replace("gtr","Guitar")
            #event = TextEvent("SEC: " + text, 250.0)
            event = TextEvent(text, 250.0)
            if text.lower().find("big rock ending") >= 0:
              curTime = self.abs_time()
              Log.debug("Big Rock Ending section event marker found at " + str(curTime) )
              self.song.breMarkerTime = curTime
          
            if text.lower().find("solo") >= 0 and text.lower().find("drum") < 0 and text.lower().find("outro") < 0 and text.lower().find("organ") < 0 and text.lower().find("synth") < 0 and text.lower().find("bass") < 0 and text.lower().find("harmonica") < 0:
              gSoloEvent = True
              gSolo = True
            elif text.lower().find("guitar") >= 0 and text.lower().find("lead") >= 0:    #Foreplay Long Time "[section_gtr_lead_1]"
              gSoloEvent = True
              gSolo = True
            elif text.lower().find("guitar") >= 0 and text.lower().find("line") >= 0:   #support for REM Orange Crush style solos
              gSoloEvent = True
              gSolo = True
            elif text.lower().find("guitar") >= 0 and text.lower().find("ostinato") >= 0:   #support for Pleasure solos "[section gtr_ostinato]"
              gSoloEvent = True
              gSolo = True
            else: #this is the cue to end solos...
              gSoloEvent = True
              gSolo = False
          elif text.lower().find("solo") >= 0 and text.find("[") < 0 and text.lower().find("drum") < 0 and text.lower().find("map") < 0 and text.lower().find("play") < 0 and not self.guitarSoloSectionMarkers:
            #event = TextEvent("SEC: " + text, 250.0)
            event = TextEvent(text, 250.0)
            gSoloEvent = True
            if text.lower().find("off") >= 0:
              gSolo = False
            else:
              gSolo = True
          elif (text.lower().find("verse") >= 0 or text.lower().find("chorus") >= 0) and text.find("[") < 0 and not self.guitarSoloSectionMarkers:   #this is an alternate GH1-style solo end marker
            #event = TextEvent("SEC: " + text, 250.0)
            event = TextEvent(text, 250.0)
            gSoloEvent = True
            gSolo = False
          elif text.lower().find("gtr") >= 0 and text.lower().find("off") >= 0 and text.find("[") < 0 and not self.guitarSoloSectionMarkers:   #this is an alternate GH1-style solo end marker
            #also convert "gtr" to "Guitar"
            text = text.replace("gtr","Guitar")
            #event = TextEvent("SEC: " + text, 100.0)
            event = TextEvent(text, 100.0)
            gSoloEvent = True
            gSolo = False
          else:  #unused text event
            #unusedEvent = TextEvent("TXT: " + text, 100.0)
            unusedEvent = TextEvent(text, 100.0)
          #now, check for guitar solo status change:
          soloSlop = 150.0   
          if gSoloEvent:
            if gSolo:
              if not self.guitarSoloActive:
                self.guitarSoloActive = True
                soloEvent = TextEvent("GSOLO ON", 250.0)
                Log.debug("GSOLO ON event " + event.text + " found at time " + str(self.abs_time()) )
                self.song.eventTracks[TK_GUITAR_SOLOS].addEvent(self.abs_time(), soloEvent)  #MFH - add an event to the guitar solos track
            else: #this is the cue to end solos...
              if self.guitarSoloActive:
                #MFH - here, check to make sure we're not ending a guitar solo that has just started!!
                curTime = self.abs_time()
                if self.song.eventTracks[TK_GUITAR_SOLOS][-1][0] < curTime:
                  self.guitarSoloActive = False
                  soloEvent = TextEvent("GSOLO OFF", 250.0)
                  Log.debug("GSOLO OFF event " + event.text + " found at time " + str(curTime) )
                  self.guitarSoloIndex += 1
                  self.song.eventTracks[TK_GUITAR_SOLOS].addEvent(curTime, soloEvent)  #MFH - add an event to the guitar solos track
      
          if event:
            curTime = self.abs_time()
            if len(self.song.eventTracks[TK_SECTIONS]) <= 1:
              self.song.eventTracks[TK_SECTIONS].addEvent(curTime, event)  #MFH - add an event to the sections track
            elif len(self.song.eventTracks[TK_SECTIONS]) > 1:    #ensure it exists first
              if self.song.eventTracks[TK_SECTIONS][-1][0] < curTime: #ensure we're not adding two consecutive sections to the same location!
                self.song.eventTracks[TK_SECTIONS].addEvent(curTime, event)  #MFH - add an event to the sections track
          elif unusedEvent:
            self.song.eventTracks[TK_UNUSED_TEXT].addEvent(self.abs_time(), unusedEvent)  #MFH - add an event to the unused text track
          
          #for track in self.song.tracks:
          #  for t in track:
          #    t.addEvent(self.abs_time(), event)
  
        


  #myfingershurt: adding MIDI lyric event access
  def lyric(self, text):
    if text.find("GNMIDI") < 0:   #to filter out the midi class illegal usage / trial timeout messages
      #Log.debug(str(self.abs_time()) + "-MIDI Lyric: " + text)
      if self.readTextAndLyricEvents > 0:
        #event = TextEvent("LYR: " + text, 400.0)
        event = TextEvent(text, 400.0)
        self.addVocalLyric(text)
        self.song.hasMidiLyrics = True
        self.song.eventTracks[TK_LYRICS].addEvent(self.abs_time(), event)  #MFH - add an event to the lyrics track
        #for track in self.song.tracks:
        #  for t in track:
        #    t.addEvent(self.abs_time(), event)

class MidiSectionReader(midi.MidiOutStream):
  # We exit via this exception so that we don't need to read the whole file in
  class Done: pass
  
  def __init__(self):
    midi.MidiOutStream.__init__(self)
    self.difficulties = []

    self.logClassInits = Config.get("game", "log_class_inits")
    if self.logClassInits == 1:
      Log.debug("MidiSectionReader class init (song.py)...")

    self.logSections = Config.get("game", "log_sections")

    #MFH: practice section support:
    self.ticksPerBeat = 480
    self.sections = []
    self.tempoMarkers = []
    self.guitarSoloSectionMarkers = False
    self.bpm = None

    self.noteCountSections = []
    self.nextSectionMinute = 0.25
    

  def header(self, format=0, nTracks=1, division=96):
    self.ticksPerBeat = division
  
  def abs_time(self):
    def ticksToBeats(ticks, bpm):
      return (60000.0 * ticks) / (bpm * self.ticksPerBeat)
      
    if self.bpm:
      currentTime = midi.MidiOutStream.abs_time(self)

      scaledTime      = 0.0
      tempoMarkerTime = 0.0
      currentBpm      = self.bpm
      for i, marker in enumerate(self.tempoMarkers):
        time, bpm = marker
        if time > currentTime:
          break
        scaledTime += ticksToBeats(time - tempoMarkerTime, currentBpm)
        tempoMarkerTime, currentBpm = time, bpm
      return scaledTime + ticksToBeats(currentTime - tempoMarkerTime, currentBpm)
    return 0.0
    
  def tempo(self, value):
    self.bpm = 60.0 * 10.0**6 / value
    self.tempoMarkers.append((midi.MidiOutStream.abs_time(self), self.bpm))
    
  def note_on(self, channel, note, velocity):
    pos = float(midi.MidiOutStream.abs_time(self))
    if (pos / 60000) >= self.nextSectionMinute:
      text = "%d:%02d -> " % (pos / 60000, (pos % 60000) / 1000) + "Section " + str(round(self.nextSectionMinute,2))
      self.nextSectionMinute += 0.25
      
      #MFH - only log if enabled
      if self.logSections == 1:
        Log.debug("Found potential default practice section: " + str(pos) + " - " + text)

      self.noteCountSections.append([text,pos])

  def lyric(self, text):  #filter lyric events
    if text.find("GNMIDI") < 0:   #to filter out the midi class illegal usage / trial timeout messages
      #Log.debug(str(self.abs_time()) + "-MIDI Lyric: " + text)
      text = ""

  #MFH - adding text event / section retrieval here 
  #also must prevent "Done" flag setting so can read whole MIDI file, all text events
  def text(self, text):
    if text.find("GNMIDI") < 0:   #to filter out the midi class illegal usage / trial timeout messages
      pos = self.abs_time()
      #Log.debug("Found MidiInfoReader text event: " + text)
      #if self.readTextAndLyricEvents > 0:
      text = text.replace("_"," ")
      if text.lower().find("section") >= 0:
        if not self.guitarSoloSectionMarkers:
          self.guitarSoloSectionMarkers = True      #GH1 dont use section markers... GH2+ do
          self.sections = []  #reset sections
        #strip unnecessary text / chars:
        text = text.replace("section","")
        text = text.replace("[","")
        text = text.replace("]","")
        #also convert "gtr" to "Guitar"
        text = text.replace("gtr","Guitar")

        #MFH - only log if enabled
        if self.logSections == 1:
          Log.debug("Found <section> potential RB-style practice section: " + str(pos) + " - " + text)

        text = "%d:%02d -> " % (pos / 60000, (pos % 60000) / 1000) + text
        self.sections.append([text,pos])
        
        
      elif text.lower().find("solo") >= 0 and text.find("[") < 0 and text.lower().find("drum") < 0 and text.lower().find("map") < 0 and text.lower().find("play") < 0 and not self.guitarSoloSectionMarkers:

        #MFH - only log if enabled
        if self.logSections == 1:
          Log.debug("Found potential GH1-style practice section: " + str(pos) + " - " + text)

        text = "%d:%02d -> " % (pos / 60000, (pos % 60000) / 1000) + text
        self.sections.append([text,pos])
      elif text.lower().find("verse") >= 0 and text.find("[") < 0 and not self.guitarSoloSectionMarkers:   #this is an alternate GH1-style solo end marker

        #MFH - only log if enabled
        if self.logSections == 1:
          Log.debug("Found potential GH1-style practice section: " + str(pos) + " - " + text)

        text = "%d:%02d -> " % (pos / 60000, (pos % 60000) / 1000) + text
        self.sections.append([text,pos])
      elif text.lower().find("gtr") >= 0 and text.lower().find("off") >= 0 and text.find("[") < 0 and not self.guitarSoloSectionMarkers:   #this is an alternate GH1-style solo end marker
        #also convert "gtr" to "Guitar"
        text = text.replace("gtr","Guitar")

        #MFH - only log if enabled
        if self.logSections == 1:
          Log.debug("Found potential GH1-style practice section: " + str(pos) + " - " + text)

        text = "%d:%02d -> " % (pos / 60000, (pos % 60000) / 1000) + text
        self.sections.append([text,pos])
      elif not self.guitarSoloSectionMarkers:   #General GH1-style sections.  Messy but effective.

        #MFH - only log if enabled
        if self.logSections == 1:
          Log.debug("Found potential GH1-style practice section: " + str(pos) + " - " + text)

        text = "%d:%02d -> " % (pos / 60000, (pos % 60000) / 1000) + text
        self.sections.append([text,pos])
        
      else:  #unused text event
        text = ""





class SongQueue:
  def __init__(self):
    self.songName = []
    self.library = []
    self.players = []
    self.difficulty1 = []
    self.difficulty2 = []
    self.part1 = []
    self.part2 = []     

    self.logClassInits = Config.get("game", "log_class_inits")
    if self.logClassInits == 1:
      Log.debug("SongQueue class init (song.py)...")
        
  def addSong(self, songName, library, players, difficulty1, difficulty2, part1, part2):
    self.songName.append(songName)
    self.library.append(library)
    self.players.append(players)
    self.difficulty1.append(difficulty1)
    self.difficulty2.append(difficulty2)
    self.part1.append(part1)
    self.part2.append(part2)
  
  def nextSong(self, counter): #should be called getSong now, but don't know how to refactor in python
    nextSong = [self.songName[counter], self.library[counter], self.players[counter], 
                self.difficulty1[counter], self.difficulty2[counter], 
                self.part1[counter], self.part2[counter]]
    return nextSong
  
  def load(self, engine, loadfile):        
    path = os.path.abspath(engine.resource.loadfile("queues", loadame))
    self = pickle.load("%s%s" %path %loadfile)
  
  def save(self, engine, fileName):
    if not fileName:
        return False
    path = os.path.abspath(engine.resource.fileName("queues", fileName))
    if os.path.isdir(path):
        return False
    savefile = open(("%(p)s%(f)s.que") % {"p" : path, "f": fileName}, "w")
    pickle.dump(self, savefile)
    savefile.close
    return True
  
  def reset(self):
    self.songName = []
    self.library = []
    self.players = []
    self.difficulty1 = []
    self.difficulty2 = []
    self.part1 = []
    self.part2 = [] 

class MidiPartsDiffReader(midi.MidiOutStream):
  
  def __init__(self, forceGuitar = False):
    midi.MidiOutStream.__init__(self)
    self.parts = []
    self.difficulties = {}
    self.currentPart = -1
    self.nextPart    = 0
    self.forceGuitar = forceGuitar
    self.firstTrack   = False
    self.notesFound   = [0, 0, 0, 0]
    self._drumFound   = False
    self._ODNoteFound = False
    self._SPNoteFound = False

    self.logClassInits = Config.get("game", "log_class_inits")
    if self.logClassInits == 1:
      Log.debug("MidiPartsDiffReader class init (song.py)...")

    self.logSections = Config.get("game", "log_sections")
  
  def getMidiStyle(self):
    if self._ODNoteFound:
      Log.debug("MIDI Type identified as RB")
      return MIDI_TYPE_RB
    elif self._drumFound and self._SPNoteFound:
      Log.debug("MIDI Type identified as WT")
      return MIDI_TYPE_WT
    else:
      Log.debug("MIDI Type identified as GH")
      return MIDI_TYPE_GH
  midiStyle = property(getMidiStyle)
  
  def start_of_track(self, n_track=0):
    if self.forceGuitar:
      if not self.firstTrack:
        if not parts[GUITAR_PART] in self.parts:
          part = parts[GUITAR_PART]
          self.parts.append(part)
          self.nextPart = None
          self.currentPart = part.id
          self.notesFound  = [0, 0, 0, 0]
          self.difficulties[part.id] = []
          if self.logSections == 1:
            tempText = "No recognized tracks found. Using first track, and identifying it as "
            tempText2 = "GUITAR_PART"
            Log.debug(tempText + tempText2)
        self.firstTrack = True
      else:
        Log.notice("This song has multiple tracks, none properly named. Behavior may be erratic.")
    
  def sequence_name(self, text):

    if self.logSections == 1:
      tempText = "MIDI sequence_name found: " + text + ", recognized and added to list as "
      tempText2 = ""

    if text == "PART GUITAR" or text == "T1 GEMS" or text == "Click":
      if not parts[GUITAR_PART] in self.parts:
        self.nextPart = parts[GUITAR_PART]
        self.currentPart = self.nextPart.id
        self.notesFound  = [0, 0, 0, 0]
        if self.logSections == 1:
          tempText2 = "GUITAR_PART"
          Log.debug(tempText + tempText2)

    elif text == "PART RHYTHM":
      if not parts[RHYTHM_PART] in self.parts:
        self.nextPart = parts[RHYTHM_PART]
        self.currentPart = self.nextPart.id
        self.notesFound  = [0, 0, 0, 0]
        if self.logSections == 1:
          tempText2 = "RHYTHM_PART"
          Log.debug(tempText + tempText2)
     
    elif text == "PART BASS":
      if not parts[BASS_PART] in self.parts:
        self.nextPart = parts[BASS_PART]
        self.currentPart = self.nextPart.id
        self.notesFound  = [0, 0, 0, 0]
        if self.logSections == 1:
          tempText2 = "BASS_PART"
          Log.debug(tempText + tempText2)

    elif text == "PART GUITAR COOP":
      if not parts[LEAD_PART] in self.parts:
        self.nextPart = parts[LEAD_PART]
        self.currentPart = self.nextPart.id
        self.notesFound  = [0, 0, 0, 0]
        if self.logSections == 1:
          tempText2 = "LEAD_PART"
          Log.debug(tempText + tempText2)

    #myfingershurt: drums, rock band rip compatible :)
    elif text == "PART DRUM" or text == "PART DRUMS":
      if not parts[DRUM_PART] in self.parts:
        self.nextPart = parts[DRUM_PART]
        self.currentPart = self.nextPart.id
        self.notesFound  = [0, 0, 0, 0]
        self._drumFound  = True #drum parts appear to be obligatory in WT songs, even if phantom.
        if self.logSections == 1:
          tempText2 = "DRUM_PART"
          Log.debug(tempText + tempText2)
    
    elif text == "PART VOCALS":
      if not parts[VOCAL_PART] in self.parts:
        part = parts[VOCAL_PART]
        self.parts.append(part)
        self.nextPart = None
        self.currentPart = part.id
        self.difficulties[part.id] = difficulties.values()
        if self.logSections == 1:
          tempText2 = "VOCAL_PART"
          Log.debug(tempText + tempText2)
    
    else:
      self.currentPart = -1
  
  def addPart(self):
    self.parts.append(self.nextPart)
    self.difficulties[self.nextPart.id] = []
    self.nextPart = None
  
  def note_on(self, channel, note, velocity):
    if self.currentPart == -1:
      return
    if note == overDriveMarkingNote:
      self._ODNoteFound = True
    elif note == starPowerMarkingNote:
      self._SPNoteFound = True
    try:
      try:
        if len(self.difficulties[self.currentPart]) == len(difficulties):
          return
      except KeyError:
        pass
      track, number = noteMap[note]
      self.notesFound[track] += 1
      if self.notesFound[track] > 5:
        if self.nextPart is not None:
          self.addPart()
        diff = difficulties[track]
        if not diff in self.difficulties[self.currentPart]:
          self.difficulties[self.currentPart].append(diff)
    except KeyError:
      pass

def loadSong(engine, name, library = DEFAULT_LIBRARY, seekable = False, playbackOnly = False, notesOnly = False, part = [parts[GUITAR_PART]], practiceMode = False):

  Log.debug("loadSong function call (song.py)...")
  crowdsEnabled = engine.config.get("audio", "crowd_tracks_enabled")

  #RF-mod (not needed?)
  guitarFile = engine.resource.fileName(library, name, "guitar.ogg")
  songFile   = engine.resource.fileName(library, name, "song.ogg")
  rhythmFile = engine.resource.fileName(library, name, "rhythm.ogg")
  crowdFile  = engine.resource.fileName(library, name, "crowd.ogg")

  logUneditedMidis = engine.config.get("log",   "log_unedited_midis")

  useUneditedMidis = engine.config.get("debug",   "use_unedited_midis")
  if useUneditedMidis == 1:    #auto
    noteFile   = engine.resource.fileName(library, name, "notes-unedited.mid", writable = True)
    #if os.path.exists(os.path.join(os.path.dirname(self.fileName), "notes-unedited.mid"))
    if os.path.isfile(noteFile):
      if logUneditedMidis == 1:
        Log.debug("notes-unedited.mid found, using instead of notes.mid! - " + name)
    else:
      noteFile   = engine.resource.fileName(library, name, "notes.mid", writable = True)
      if logUneditedMidis == 1:
        Log.debug("notes-unedited.mid not found, using notes.mid - " + name)
  else:
    noteFile   = engine.resource.fileName(library, name, "notes.mid", writable = True)
    if logUneditedMidis == 1:
      Log.debug("notes-unedited.mid not found, using notes.mid - " + name)


  #noteFile   = engine.resource.fileName(library, name, "notes.mid", writable = True)
  
  infoFile   = engine.resource.fileName(library, name, "song.ini", writable = True)
  scriptFile = engine.resource.fileName(library, name, "script.txt")
  previewFile = engine.resource.fileName(library, name, "preview.ogg")
  #myfingershurt:
  drumFile = engine.resource.fileName(library, name, "drums.ogg")


  if seekable:
    if os.path.isfile(guitarFile) and os.path.isfile(songFile):
      # TODO: perform mixing here
      songFile   = guitarFile
      guitarFile = None
      rhythmFile = ""
    else:
      songFile   = guitarFile
      guitarFile = None
      rhythmFile = ""
      
  if not os.path.isfile(songFile):
    songFile   = guitarFile
    guitarFile = None
  
  if not os.path.isfile(rhythmFile):
    rhythmFile = None
    #if os.path.isfile(alternteRhythmFile):    #support for bass.ogg
      #rhythmFile = alternateRhythmFile

  if not os.path.isfile(drumFile):
    drumFile = None
  
  if not os.path.isfile(crowdFile):
    crowdFile = None
    #if os.path.isfile(songCrowdFile) and useSongCrowdTrack:   #supports song+crowd... may be (re)implemented later.
      #crowdFile = songCrowdFile
      #Log.warn("crowd.ogg file not found. Using song+crowd.ogg instead! Volumes may be off.")

  if crowdsEnabled == 0:
    crowdFile = None      


  if songFile != None and guitarFile != None:
    #check for the same file
    songStat = os.stat(songFile)
    guitarStat = os.stat(guitarFile)
    #Simply checking file size, no md5
    if songStat.st_size == guitarStat.st_size:
      guitarFile = None


    
  if practiceMode:    #single track practice mode only!
    if part[0] == parts[GUITAR_PART] and guitarFile != None:
      songFile = guitarFile
    elif part[0] == parts[BASS_PART] and rhythmFile != None:
      songFile = rhythmFile
    elif part[0] == parts[DRUM_PART] and drumFile != None:
      songFile = drumFile
    guitarFile = None
    rhythmFile = None
    drumFile = None
    crowdFile = None

  slowDownFactor = engine.config.get("audio", "speed_factor")
  engine.setSpeedFactor(slowDownFactor)    #MFH 
    

  #MFH - check for slowdown mode here.  If slowdown, and single track song (or practice mode), 
  #  duplicate single track to a streamingAudio track so the slowed down version can be heard.
  if engine.audioSpeedFactor != 1:
    crowdFile = None
    #count tracks:
    audioTrackCount = 0
    if guitarFile:
      audioTrackCount += 1
    if rhythmFile:
      audioTrackCount += 1
    if drumFile:
      audioTrackCount += 1
    if audioTrackCount < 1:
      if part[0] == parts[GUITAR_PART]:
        guitarFile = songFile
      elif part[0] == parts[BASS_PART]:
        rhythmFile = songFile
      elif part[0] == parts[DRUM_PART]:
        drumFile = songFile
      else:
        guitarFile = songFile
      



  if playbackOnly:
    noteFile = None
    crowdFile = None
    if os.path.isfile(previewFile):
      songFile = previewFile
      guitarFile = None
      rhythmFile = None
      drumFile = None
      
  if notesOnly:
    songFile = None
    crowdFile = None
    guitarFile = None
    rhythmFile = None
    previewFile = None
    drumFile = None
      
  song       = Song(engine, infoFile, songFile, guitarFile, rhythmFile, noteFile, scriptFile, part, drumFile, crowdFile)
  return song

def loadSongInfo(engine, name, library = DEFAULT_LIBRARY):
  #RF-mod (not needed?)
  infoFile   = engine.resource.fileName(library, name, "song.ini", writable = True)
  return SongInfo(infoFile, library)
  
def createSong(engine, name, guitarTrackName, backgroundTrackName, rhythmTrackName = None, library = DEFAULT_LIBRARY):
  #RF-mod (not needed?)
  path = os.path.abspath(engine.resource.fileName(library, name, writable = True))
  os.makedirs(path)
  
  guitarFile = engine.resource.fileName(library, name, "guitar.ogg", writable = True)
  songFile   = engine.resource.fileName(library, name, "song.ogg",   writable = True)
  noteFile   = engine.resource.fileName(library, name, "notes.mid",  writable = True)
  infoFile   = engine.resource.fileName(library, name, "song.ini",   writable = True)
  
  shutil.copy(guitarTrackName, guitarFile)
  
  if backgroundTrackName:
    shutil.copy(backgroundTrackName, songFile)
  else:
    songFile   = guitarFile
    guitarFile = None

  if rhythmTrackName:
    rhythmFile = engine.resource.fileName(library, name, "rhythm.ogg", writable = True)
    shutil.copy(rhythmTrackName, rhythmFile)
  else:
    rhythmFile = None
    
  f = open(noteFile, "wb")
  m = midi.MidiOutFile(f)
  m.header()
  m.start_of_track()
  m.update_time(0)
  m.end_of_track()
  m.eof()
  m.write()
  f.close()

  song = Song(engine, infoFile, songFile, guitarFile, rhythmFile, noteFile)
  song.info.name = name
  song.save()
  
  return song

def getDefaultLibrary(engine):
  return LibraryInfo(DEFAULT_LIBRARY, engine.resource.fileName(DEFAULT_LIBRARY, "library.ini"))

def getAvailableLibraries(engine, library = DEFAULT_LIBRARY):
  Log.debug("Song.getAvailableLibraries function call...library = " + str(library) )
  # Search for libraries in both the read-write and read-only directories
  songRoots    = [engine.resource.fileName(library),
                  engine.resource.fileName(library, writable = True)]
  libraries    = []
  libraryRoots = []

  for songRoot in set(songRoots):
    if (os.path.exists(songRoot) == False):
      return libraries
    for libraryRoot in os.listdir(songRoot):
      if libraryRoot == ".svn":   #MFH - filter out the hidden SVN control folder!
        continue
      libraryRoot = os.path.join(songRoot, libraryRoot)
      if not os.path.isdir(libraryRoot):
        continue
      if os.path.isfile(os.path.join(libraryRoot, "notes.mid")):
        continue
      if os.path.isfile(os.path.join(libraryRoot, "notes-unedited.mid")):
        continue

      libName = library + os.path.join(libraryRoot.replace(songRoot, ""))
      
      libraries.append(LibraryInfo(libName, os.path.join(libraryRoot, "library.ini")))
      #Log.debug("Library added: " + str(libraries) )
      continue # why were these here? we must filter out empty libraries - coolguy567
                #MFH - I'll tell you why -- so that empty ("tiered" / organizational) folders are displayed, granting access to songs in subfolders...
      
      dirs = os.listdir(libraryRoot)
      for name in dirs:
        if os.path.isfile(os.path.join(libraryRoot, name, "song.ini")):
          if not libraryRoot in libraryRoots:
            libName = library + os.path.join(libraryRoot.replace(songRoot, ""))
            libraries.append(LibraryInfo(libName, os.path.join(libraryRoot, "library.ini")))
            #Log.debug("Library added: " + str(libraries) )
            libraryRoots.append(libraryRoot)
   
  libraries.sort(lambda a, b: cmp(a.name.lower(), b.name.lower()))
  
  return libraries

def getAvailableSongs(engine, library = DEFAULT_LIBRARY, includeTutorials = False, progressCallback = lambda p: None):
  order = engine.config.get("game", "sort_order")
  tut = engine.config.get("game", "tut")
  direction = engine.config.get("game", "sort_direction")
  if tut:
    includeTutorials = True

  #MFH - Career Mode determination:
  gameMode1p = engine.config.get("game","game_mode")
  if gameMode1p == 2:
    careerMode = True
  else:
    careerMode = False

  # Search for songs in both the read-write and read-only directories
  if library == None:
    return []
  songRoots = [engine.resource.fileName(library), engine.resource.fileName(library, writable = True)]
  names = []
  for songRoot in songRoots:
    if (os.path.exists(songRoot) == False):
      return []
    for name in os.listdir(songRoot):
      #if not os.path.isfile(os.path.join(songRoot, name, "notes.mid")):
      if ( not os.path.isfile(os.path.join(songRoot, name, "notes.mid")) ) and ( not os.path.isfile(os.path.join(songRoot, name, "notes-unedited.mid")) ):
        continue
      if not os.path.isfile(os.path.join(songRoot, name, "song.ini")) or name.startswith("."):
       #if not os.path.isfile(os.path.join(songRoot, name, "song.ini")):
        continue
      if not name in names:
        names.append(name)
  songs = []
  for name in names:
    progressCallback(len(songs)/float(len(names)))
    songs.append(SongInfo(engine.resource.fileName(library, name, "song.ini", writable = True), library, allowCacheUsage=True))
  if len(songs) and canCache and Config.get("performance", "cache_song_metadata"):
    cache = cacheManager.getCache(songs[0].fileName)
    #stump: clean up the cache
    if cache.execute('DELETE FROM `songinfo` WHERE `hash` NOT IN (' + ','.join("'%s'" % s.stateHash for s in songs) + ')').rowcount > 0:
      cache.execute('VACUUM')  # compact the database if anything was deleted on the previous line
    cache.commit()  # commit any changes to the cache all at once
  if not includeTutorials:
    songs = [song for song in songs if not song.tutorial]
  songs = [song for song in songs if not song.artist == '=FOLDER=']
    #coolguy567's unlock system
  if careerMode:
    for song in songs:
      if song.getUnlockRequire() != "":
        song.setLocked(False)
        for song2 in songs:
          if song.getUnlockRequire() == song2.getUnlockID() and not song2.completed:
            song.setLocked(True)
      else:
        song.setLocked(False)
  instrument = engine.config.get("game", "songlist_instrument")
  theInstrumentDiff = instrumentDiff[instrument]
  if direction == 0:
    if order == 1:
      songs.sort(lambda a, b: cmp(a.artist.lower(), b.artist.lower()))
    elif order == 2:
      songs.sort(lambda a, b: cmp(int(b.count+str(0)), int(a.count+str(0))))
    elif order == 0:
      songs.sort(lambda a, b: cmp(a.name.lower(), b.name.lower()))
    elif order == 3:
      songs.sort(lambda a, b: cmp(a.album.lower(), b.album.lower()))
    elif order == 4:
      songs.sort(lambda a, b: cmp(a.genre.lower(), b.genre.lower()))
    elif order == 5:
      songs.sort(lambda a, b: cmp(a.year.lower(), b.year.lower()))
    elif order == 6:
      songs.sort(lambda a, b: cmp(a.diffSong, b.diffSong))
    elif order == 7:
      songs.sort(lambda a, b: cmp(theInstrumentDiff(a), theInstrumentDiff(b)))
    elif order == 8:
      songs.sort(lambda a, b: cmp(a.icon.lower(), b.icon.lower()))
  else:
    if order == 1:
      songs.sort(lambda a, b: cmp(b.artist.lower(), a.artist.lower()))
    elif order == 2:
      songs.sort(lambda a, b: cmp(int(a.count+str(0)), int(b.count+str(0))))
    elif order == 0:
      songs.sort(lambda a, b: cmp(b.name.lower(), a.name.lower()))
    elif order == 3:
      songs.sort(lambda a, b: cmp(b.album.lower(), a.album.lower()))
    elif order == 4:
      songs.sort(lambda a, b: cmp(b.genre.lower(), a.genre.lower()))
    elif order == 5:
      songs.sort(lambda a, b: cmp(b.year.lower(), a.year.lower()))
    elif order == 6:
      songs.sort(lambda a, b: cmp(b.diffSong, a.diffSong))
    elif order == 7:
      songs.sort(lambda a, b: cmp(theInstrumentDiff(b), theInstrumentDiff(a)))
    elif order == 8:
      songs.sort(lambda a, b: cmp(b.icon.lower(), a.icon.lower()))
  return songs

  #coolguy567's unlock system
def getSortingTitles(engine, songList = []):
  sortOrder = engine.config.get("game","sort_order")
  titles = []
  sortTitles = []
  
  instrument = engine.config.get("game", "songlist_instrument")
  theInstrumentDiff = instrumentDiff[instrument]

  #if sortOrder == 0:
  #  for i in range (65,90):
  #    sortTitles.append(SortTitleInfo(chr(i)))
  #elif sortOrder == 1:
  for songItem in songList:
    if sortOrder == 1:
      try:
        titles.index(songItem.artist.lower())
      except ValueError:
        titles.append(songItem.artist.lower())
        sortTitles.append(SortTitleInfo(songItem.artist))
    elif sortOrder == 0:
      try:
        if songItem.name[0].isdigit():
          sortName = "123"
        elif not songItem.name[0].isalnum():
          sortName = "!@#"
        else:
          sortName = songItem.name[0].lower()
        titles.index(sortName)
      except ValueError:
        if songItem.name[0].isdigit():
          sortName = "123"
        elif not songItem.name[0].isalnum():
          sortName = "!@#"
        else:
          sortName = songItem.name[0].lower()
        titles.append(sortName)
        sortTitles.append(SortTitleInfo(sortName.upper()))
    elif sortOrder == 2:
      try:
        titles.index(songItem.count)
      except ValueError:
        titles.append(songItem.count)
        if songItem.count == "":
          sortTitles.append(SortTitleInfo("0"))
          titles.append("0")
        else:
          sortTitles.append(SortTitleInfo(songItem.count))
    elif sortOrder == 3:
      try:
        titles.index(songItem.album.lower())
      except ValueError:
        titles.append(songItem.album.lower())
        sortTitles.append(SortTitleInfo(songItem.album))
    elif sortOrder == 4:
      try:
        titles.index(songItem.genre.lower())
      except ValueError:
        titles.append(songItem.genre.lower())
        sortTitles.append(SortTitleInfo(songItem.genre))
    elif sortOrder == 5:
      try:
        titles.index(songItem.year)
      except ValueError:
        titles.append(songItem.year)
        sortTitles.append(SortTitleInfo(songItem.year))
    elif sortOrder == 6:
      try:
        titles.index(songItem.diffSong)
      except ValueError:
        titles.append(songItem.diffSong)
        sortTitles.append(SortTitleInfo(str(songItem.diffSong)))
    elif sortOrder == 7:
      try:
        titles.index(theInstrumentDiff(songItem))
      except ValueError:
        titles.append(theInstrumentDiff(songItem))
        sortTitles.append(SortTitleInfo(str(theInstrumentDiff(songItem))))
    elif sortOrder == 8:
      try:
        titles.index(songItem.icon.lower())
      except ValueError:
        titles.append(songItem.icon.lower())
        sortTitles.append(SortTitleInfo(songItem.icon))
        
  return sortTitles
  
  
def getAvailableTitles(engine, library = DEFAULT_LIBRARY):
  gameMode1p = engine.config.get("game","game_mode")
  if library == None:
    return []
  
  path = os.path.join(engine.resource.fileName(library, writable = True), "titles.ini")
  if not os.path.isfile(path):
    return []
  
  config = Config.MyConfigParser()
  titles = []
  try:
    config.read(path)
    sections = config.get("titles", "sections")
    
    for section in sections.split():
      titles.append(TitleInfo(config, section))
    
    if gameMode1p == 2:
      titles.append(BlankSpaceInfo(_("End of Career")))
    
  except:
    Log.debug("titles.ini could not be read (song.py)")
    return []
  
  return titles
  
def getAvailableSongsAndTitles(engine, library = DEFAULT_LIBRARY, includeTutorials = False, progressCallback = lambda p: None):
  listingMode = engine.config.get("game","song_listing_mode")
  if library == None:
    return []

  #MFH - Career Mode determination:
  gameMode1p = engine.config.get("game","game_mode")
  if gameMode1p == 2:
    careerMode = True
    quickPlayMode = False
  else:
    careerMode = False
    if gameMode1p == 0:
      quickPlayMode = True
    else:
      quickPlayMode = False
      
  quickPlayCareerTiers = engine.config.get("game", "quickplay_tiers")


  if listingMode == 0 or careerMode:
    items = getAvailableSongs(engine, library, includeTutorials, progressCallback=progressCallback)
    if quickPlayMode and quickPlayCareerTiers == 0:
      titles = []
    else:
      if quickPlayCareerTiers == 1 or careerMode:
        titles = getAvailableTitles(engine, library)
      else:
        titles = getSortingTitles(engine, items)
    items = items + titles
  else:
    items = []
    titles = []
    rootDir = engine.resource.fileName(DEFAULT_LIBRARY)

    items = getAvailableSongs(engine, rootDir, includeTutorials, progressCallback=progressCallback)
    for root, subFolders, files in os.walk(rootDir):
      for folder in subFolders:
        libName = os.path.join(root,folder)
        items = items + getAvailableSongs(engine, libName, includeTutorials, progressCallback=progressCallback)
        if quickPlayMode and quickPlayCareerTiers == 0:
          titles = []
        else:
          if quickPlayCareerTiers == 1:
            titles = titles + getAvailableTitles(engine, libName)
    if quickPlayCareerTiers == 2:
      titles = getSortingTitles(engine, items)
    items = items + titles
        
  items.sort(lambda a, b: compareSongsAndTitles(engine, a, b))
  
  
  if quickPlayMode and len(items) != 0:
    items.insert(0, RandomSongInfo())

  if careerMode and titles != []:
    items.append(BlankSpaceInfo())
    items.append(CareerResetterInfo())
  
  return items
  
def compareSongsAndTitles(engine, a, b):
  #MFH - want to push all non-career songs in a folder below all titles and career songs
  
  #When an unlock_id does not exist in song.ini, a blank string "" value is returned.
  #Can check for this to determine that this song should be below any titles or non-None unlock_id's

  #>>> def numeric_compare(x, y):
  #>>>    if x>y:
  #>>>       return 1
  #>>>    elif x==y:
  #>>>       return 0
  #>>>    else: # x<y
  #>>>       return -1

  #MFH - Career Mode determination:
  gameMode1p = engine.config.get("game","game_mode")
  order = engine.config.get("game", "sort_order")
  
  #MFH - must check here for an invalid Sort Order setting and correct it!
  orderings = engine.config.getOptions("game", "sort_order")[1]
  if order >= len(orderings):
    order = 0
    engine.config.set("game", "sort_order", order)

  instrument = engine.config.get("game", "songlist_instrument")
  theInstrumentDiff = instrumentDiff[instrument]
  direction = engine.config.get("game", "sort_direction")
  if gameMode1p == 2:
    careerMode = True
    quickPlayMode = False
  else:
    careerMode = False
    #if gameMode1p == 0: #akedrou - different sorting for practice mode and quickplay mode??
    quickPlayMode = True
    #else:
    #  quickPlayMode = False
      
  quickPlayCareerTiers = engine.config.get("game", "quickplay_tiers")
  if quickPlayMode and quickPlayCareerTiers == 0:
    if direction == 0:
      if order == 1:
        return cmp(a.artist.lower(), b.artist.lower())
      elif order == 2:
        return cmp(int(b.count+str(0)), int(a.count+str(0)))
      elif order == 0:
        return cmp(removeSongOrderPrefixFromName(a.name).lower(), removeSongOrderPrefixFromName(b.name).lower())
      elif order == 3:
        return cmp(a.album.lower(), b.album.lower())
      elif order == 4:
        return cmp(a.genre.lower(), b.genre.lower())
      elif order == 5:
        return cmp(a.year.lower(), b.year.lower())
      elif order == 6:
        return cmp(a.diffSong, b.diffSong)
      elif order == 7:
        return cmp(theInstrumentDiff(a), theInstrumentDiff(b))
      elif order == 8:
        return cmp(a.icon.lower(), b.icon.lower())
    else:
      if order == 1:
        return cmp(b.artist.lower(), a.artist.lower())
      elif order == 2:
        return cmp(int(a.count+str(0)), int(b.count+str(0)))
      elif order == 0:
        return cmp(removeSongOrderPrefixFromName(b.name).lower(), removeSongOrderPrefixFromName(a.name).lower())
      elif order == 3:
        return cmp(b.album.lower(), a.album.lower())
      elif order == 4:
        return cmp(b.genre.lower(), a.genre.lower())
      elif order == 5:
        return cmp(b.year.lower(), a.year.lower())
      elif order == 6:
        return cmp(b.diffSong, a.diffSong)
      elif order == 7:
        return cmp(theInstrumentDiff(a), theInstrumentDiff(b))
      elif order == 8:
        return cmp(b.icon.lower(), a.icon.lower())
  elif gameMode1p != 2 and quickPlayCareerTiers == 2:
    Aval = ""
    Bval = ""
    if isinstance(a, SongInfo):
      if order == 0:
        Aval = removeSongOrderPrefixFromName(a.name)[0].lower()
        if Aval.isdigit():
          Aval = "123"
        if not Aval.isalnum():
          Aval = "!@#"
      elif order == 1:
        Aval = a.artist.lower()
      elif order == 2:
        Aval = int(a.count+str(0))
        if Aval == "":
          Aval = "0"
      elif order == 3:
        Aval = a.album.lower()
      elif order == 4:
        Aval = a.genre.lower()
      elif order == 5:
        Aval = a.year.lower()
      elif order == 6:
        Aval = a.diffSong
      elif order == 7:
        Aval = theInstrumentDiff(a)
      elif order == 8:
        Aval = a.icon.lower()
    elif isinstance(a, SortTitleInfo):
      if order == 2:
        Aval = int(a.name+str(0))
      elif order == 6 or order == 7:
        Aval = int(a.name)
      else:
        Aval = a.name.lower()
      
    if isinstance(b, SongInfo):
      if order == 0:
        Bval = removeSongOrderPrefixFromName(b.name)[0].lower()
        if Bval.isdigit():
          Bval = "123"
        if not Bval.isalnum():
          Bval = "!@#"
      elif order == 1:
        Bval = b.artist.lower()
      elif order == 2:
        Bval = int(b.count+str(0))
        if Bval == "":
          Bval = "0"
      elif order == 3:
        Bval = b.album.lower()
      elif order == 4:
        Bval = b.genre.lower()
      elif order == 5:
        Bval = b.year.lower()
      elif order == 6:
        Bval = b.diffSong
      elif order == 7:
        Bval = theInstrumentDiff(b)
      elif order == 8:
        Bval = b.icon.lower()
    elif isinstance(b, SortTitleInfo):
      if order == 2:
        Bval = int(b.name+str(0))
      elif order == 6 or order == 7:
        Bval = int(b.name)
      else:
        Bval = b.name.lower()

    if Aval != Bval:    #MFH - if returned unlock IDs are different, sort by unlock ID (this roughly sorts the tiers and shoves "bonus" songs to the top)
      if direction == 0:
        return cmp(Aval, Bval)
      else:
        return cmp(Bval, Aval)
    elif isinstance(a, SortTitleInfo) and isinstance(b, SortTitleInfo):
      return 0
    elif isinstance(a, SortTitleInfo) and isinstance(b, SongInfo):
      return -1
    elif isinstance(a, SongInfo) and isinstance(b, SortTitleInfo):
      return 1
    else:
      return cmp(a.name, b.name)

  else:
    #Log.debug("Unlock IDs found, a=" + str(a.getUnlockID()) + ", b=" + str(b.getUnlockID()) )
    if a.getUnlockID() == "" and b.getUnlockID() != "":   #MFH - a is a bonus song, b is involved in career mode
      return 1
    elif b.getUnlockID() == "" and a.getUnlockID() != "":   #MFH - b is a bonus song, a is involved in career mode - this is fine.
      return -1
    elif a.getUnlockID() == "" and b.getUnlockID() == "":   #MFH - a and b are both bonus songs; apply sorting logic.
      #MFH: catch BlankSpaceInfo ("end of career") marker, ensure it goes to the top of the bonus songlist
      if isinstance(a, SongInfo) and isinstance(b, BlankSpaceInfo):   #a is a bonus song, b is a blank space (end of career marker)
        return 1
      elif isinstance(a, BlankSpaceInfo) and isinstance(b, SongInfo):   #a is a blank space, b is a bonus song (end of career marker) - this is fine.
        return -1
      else: #both bonus songs, apply sort order:
        if direction == 0:
          if order == 1:
            return cmp(a.artist.lower(), b.artist.lower())
          elif order == 2:
            return cmp(int(b.count+str(0)), int(a.count+str(0)))
          elif order == 0:
            return cmp(removeSongOrderPrefixFromName(a.name).lower(), removeSongOrderPrefixFromName(b.name).lower())
          elif order == 3:
            return cmp(a.album.lower(), b.album.lower())
          elif order == 4:
            return cmp(a.genre.lower(), b.genre.lower())
          elif order == 5:
            return cmp(a.year.lower(), b.year.lower())
          elif order == 6:
            return cmp(a.diffSong, b.diffSong)
          elif order == 7:
            return cmp(theInstrumentDiff(a), theInstrumentDiff(b))
          elif order == 8:
            return cmp(a.icon.lower(), b.icon.lower())
        else:
          if order == 1:
            return cmp(b.artist.lower(), a.artist.lower())
          elif order == 2:
            return cmp(int(a.count+str(0)), int(b.count+str(0)))
          elif order == 0:
            return cmp(removeSongOrderPrefixFromName(b.name).lower(), removeSongOrderPrefixFromName(a.name).lower())
          elif order == 3:
            return cmp(b.album.lower(), a.album.lower())
          elif order == 4:
            return cmp(b.genre.lower(), a.genre.lower())
          elif order == 5:
            return cmp(b.year.lower(), a.year.lower())
          elif order == 6:
            return cmp(b.diffSong, a.diffSong)
          elif order == 7:
            return cmp(theInstrumentDiff(b), theInstrumentDiff(a))
          elif order == 8:
            return cmp(b.icon.lower(), a.icon.lower())
    #original career sorting logic:
    elif a.getUnlockID() != b.getUnlockID():    #MFH - if returned unlock IDs are different, sort by unlock ID (this roughly sorts the tiers and shoves "bonus" songs to the top)
      return cmp(a.getUnlockID(), b.getUnlockID())
    elif isinstance(a, TitleInfo) and isinstance(b, TitleInfo):
      return 0
    elif isinstance(a, TitleInfo) and isinstance(b, SongInfo):
      return -1
    elif isinstance(a, SongInfo) and isinstance(b, TitleInfo):
      return 1
    
    else:   #MFH - This is where career songs are sorted within tiers -- we want to force sorting by "name" only:
      return cmp(a.name.lower(), b.name.lower())    #MFH - force sort by name for career songs

def isInt(possibleInt):
  try:
    #MFH - remove any leading zeros (for songs with 01. or 02. for example)        
    splitName = possibleInt.split("0",1)
    while splitName[0] == "":
      splitName = possibleInt.split("0",1)
      if len(splitName) > 1:
        if splitName[0] == "":
          possibleInt = splitName[1]
    if str(int(possibleInt)) == str(possibleInt):
      return True
    else:
      return False
  except Exception, e:
    return False

def removeSongOrderPrefixFromName(name): #copied from Dialogs - can't import it here.
  if not name.startswith("."):
    splitName = name.split(".",1)
    if isInt(splitName[0]) and len(splitName) > 1:
      name = splitName[1]
      splitName[0] = ""
      while splitName[0] == "":
        splitName = name.split(" ",1)
        if len(splitName) > 1:
          if splitName[0] == "":
            name = splitName[1]
  return name
  
