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

from collections import OrderedDict
from functools import total_ordering
import binascii
import copy
import glob
import hashlib
import logging
import os
import random
import re
import time

from fretwork import midi
from fretwork.audio import StreamingSound
from six.moves import cPickle  # Cerealizer and sqlite3 don't seem to like each other that much
from six.moves.urllib.parse import urlencode
from six.moves.urllib.request import urlopen
import cerealizer
import six

from fofix.core import Config
from fofix.core import VFS
from fofix.core import Version
from fofix.core.Language import _
from fofix.core.Theme import *
from fofix.core.Theme import hexToColor, colorToHex
from fofix.game.song.songconstants import *


log = logging.getLogger(__name__)


# code for adding tracks, inside song.py:
# self.song.eventTracks[TK_SCRIPT].addEvent(self.abs_time(), event)  # add an event to the script.txt track
# self.song.eventTracks[TK_SECTIONS].addEvent(self.abs_time(), event)  # add an event to the sections track
# self.song.eventTracks[TK_GUITAR_SOLOS].addEvent(self.abs_time(), event)  # add an event to the guitar solos track
# self.song.eventTracks[TK_LYRICS].addEvent(self.abs_time(), event)  # add an event to the lyrics track
# self.song.eventTracks[TK_UNUSED_TEXT].addEvent(self.abs_time(), event)
# # add an event to the unused text track

# code for accessing track objects, outside song.py:
# self.song.eventTracks[Song.TK_SCRIPT]
# self.song.eventTracks[Song.TK_SECTIONS]
# self.song.eventTracks[Song.TK_GUITAR_SOLOS]
# self.song.eventTracks[Song.TK_LYRICS]
# self.song.eventTracks[Song.TK_UNUSED_TEXT]

# This is the sorting order, grouped by instruments.
#
# Guitar
# Pro Guitar
# Lead
# Rhythm
# Bass
# Pro Bass
# Keys
# Pro Keys
# Vocals
# Drums
# Pro Drums

PART_SORTING = [0, 3, 4, 2, 9, 8, 6, 1, 5, 10, 7]

TRACK_ID_NAME_MAP = {
    VOCAL_PART: 'vocals',
    GUITAR_PART: 'guitar',
    PRO_GUITAR_PART: 'guitar',
    LEAD_PART: 'guitar',
    RHYTHM_PART: 'rhythm',
    BASS_PART: 'rhythm',
    PRO_BASS_PART: 'rhythm',
    DRUM_PART: 'drums',
    PRO_DRUM_PART: 'drums',
    KEYS_PART: 'keys',
    PRO_KEYS_PART: 'keys',
}

TRACK_NAME_ID_MAP = {
    'guitar': [GUITAR_PART, PRO_GUITAR_PART],
    'rhythm': [RHYTHM_PART, BASS_PART, PRO_BASS_PART],
    'drums': [DRUM_PART, PRO_DRUM_PART],
    'keys': [KEYS_PART, PRO_KEYS_PART],
    'vocals': [VOCAL_PART],
}


PITCH_SHIFTABLES = (GUITAR_PART, RHYTHM_PART, BASS_PART, LEAD_PART, KEYS_PART,
                    PRO_GUITAR_PART, PRO_BASS_PART, PRO_KEYS_PART)

instrumentDiff = {
    0: (lambda a: a.diffGuitar),
    1: (lambda a: a.diffGuitar),
    2: (lambda a: a.diffBass),
    3: (lambda a: a.diffGuitar),
    4: (lambda a: a.diffDrums),
    5: (lambda a: a.diffVocals)
}


@total_ordering
class Part(object):
    def __init__(self, uid, text, trackName):
        self.id = uid               # int uid for this instance
        self.text = text            # str friendly name for this instance
        self.trackName = trackName  # list(str) of names which the part is called in the midi

    def __eq__(self, other):
        # if it's not being compared with a part, we probably want its real ID.
        if isinstance(other, Part):
            compare = PART_SORTING[self.id] == PART_SORTING[other.id]
        else:
            compare = self.id == other
        return compare

    def __lt__(self, other):
        # if it's not being compared with a part, we probably want its real ID.
        if isinstance(other, Part):
            compare = PART_SORTING[self.id] < PART_SORTING[other.id]
        else:
            compare = self.id < other
        return compare

    def __str__(self):
        return self.text

    def __repr__(self):
        return self.text


parts = {
    GUITAR_PART: Part(GUITAR_PART, _("Guitar"), ["PART GUITAR", "T1 GEMS", "Click", "Midi Out"]),
    RHYTHM_PART: Part(RHYTHM_PART, _("Rhythm"), ["PART RHYTHM"]),
    BASS_PART:   Part(BASS_PART,   _("Bass"),   ["PART BASS"]),
    LEAD_PART:   Part(LEAD_PART,   _("Lead"),   ["PART LEAD"]),
    DRUM_PART:   Part(DRUM_PART,   _("Drums"),  ["PART DRUMS", "PART DRUM"]),
    VOCAL_PART:  Part(VOCAL_PART,  _("Vocals"), ["PART VOCALS"]),
    KEYS_PART:  Part(KEYS_PART,  _("Keys"), ["PART KEYS"]),
    PRO_GUITAR_PART: Part(PRO_GUITAR_PART, _("Pro Guitar"), ["PART REAL GUITAR"]),
    PRO_BASS_PART: Part(PRO_BASS_PART, _("Pro Bass"), ["PART REAL BASS"]),
    PRO_DRUM_PART: Part(PRO_DRUM_PART, _("Pro Drum"), ["PART REAL DRUM"]),
    PRO_KEYS_PART: Part(PRO_KEYS_PART, _("Pro Keys"), ["PART REAL_KEYS_X", "PART REAL_KEYS_H", "PART REAL_KEYS_M", "PART REAL_KEYS_E"])
}


@total_ordering
class Difficulty(object):
    def __init__(self, uid, text):
        self.id = uid
        self.text = text

    def __eq__(self, other):
        if isinstance(other, Difficulty):
            return self.id == other.id
        else:
            return self.id == other

    def __lt__(self, other):
        if isinstance(other, Difficulty):
            return self.id < other.id
        else:
            return self.id < other

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

defaultSections = ["Start", "1/4", "1/2", "3/4"]


# Load the song database and check that it is completely initialized.
_SCHEMA_VERSION = 7  # stump: current database format version number
_songDB = VFS.openSqlite3('/userdata/SongCache.sqlite')
try:
    _dbversion = _songDB.execute(
        "SELECT `value` FROM `config` WHERE `key` = 'version'").fetchone()[0]
    if int(_dbversion) == 6:
        log.debug('Upgrading song cache schema version 6 to 7.')
        _songDB.execute('ALTER TABLE `songinfo` ADD `seen` INT')
        _songDB.execute('UPDATE `songinfo` SET `seen` = 0')
        _songDB.execute("UPDATE `config` SET `value` = '7' WHERE `key` = 'version'")
        _songDB.commit()
        _dbversion = 7
    # (Insert future schema upgrades here - with ifs, not elifs, so we are
    #  able to upgrade starting at *any* schema version we support
    #  upgrading from, like so.)
    # if _dbversion == 7:
    #  log.debug('Upgrading song cache schema version 7 to 8.')
    #  _songDB.execute(sql needed to do the update)
    #  _songDB.commit()
    #  _dbversion = 8
    if _dbversion == _SCHEMA_VERSION:
        _mustReinitialize = False
    else:
        _mustReinitialize = True
        log.debug('Song cache has incompatible schema version; forcing reinitialization.')
except Exception:
    _mustReinitialize = True
if _mustReinitialize:
    log.debug('Initializing song cache.')
    # Clean out the database, then make our tables.
    for tbl in _songDB.execute("SELECT `name` FROM `sqlite_master` WHERE `type` = 'table'").fetchall():
        _songDB.execute('DROP TABLE `%s`' % tbl)
    _songDB.execute('VACUUM')
    # if you need to change the database schema, do it here, then bump
    # the version number, a small bit above here.
    _songDB.execute('CREATE TABLE `config` (`key` STRING UNIQUE, `value` STRING)')
    _songDB.execute('CREATE TABLE `songinfo` (`hash` STRING UNIQUE, `info` STRING, `seen` INT)')
    _songDB.execute('INSERT INTO `config` (`key`, `value`) VALUES (?, ?)',
                    ('version', _SCHEMA_VERSION))
    _songDB.commit()


class SongInfo(object):
    """ A song object """

    def __init__(self, infoFileName, songLibrary=DEFAULT_LIBRARY):
        self.songName = os.path.basename(os.path.dirname(infoFileName))
        self.fileName = infoFileName
        self.libraryNam = songLibrary[:]
        self.info = Config.MyConfigParser()
        self._partDifficulties = {}
        self._parts = None
        self._midiStyle = None
        self.highScores = {}

        self.locked = False

        # want to read valid sections from the MIDI in for practice mode selection here:
        self._sections = None

        self.name = _("NoName")

        log.debug("SongInfo class init (song.py)")

        self.info.read(infoFileName)

        self.logSections = Config.get("game", "log_sections")
        self.logUneditedMidis = Config.get("log", "log_unedited_midis")

        self.useUneditedMidis = Config.get("debug", "use_unedited_midis")
        if self.useUneditedMidis == 1:  # auto
            if os.path.isfile(os.path.join(os.path.dirname(self.fileName), "notes-unedited.mid")):
                notefile = "notes-unedited.mid"
                if self.logUneditedMidis == 1:
                    log.debug("notes-unedited.mid found, using instead of notes.mid! - " + self.name)
            else:
                notefile = "notes.mid"
                if self.logUneditedMidis == 1:
                    log.info("notes-unedited.mid not found, using notes.mid - " + self.name)
        else:
            notefile = "notes.mid"
            if self.logUneditedMidis == 1:
                log.info("notes-unedited.mid not found, using notes.mid - " + self.name)
        self.noteFileName = os.path.join(os.path.dirname(self.fileName), notefile)

        for part in parts.values():
            self.getScores(part)

        # metadata caching
        if Config.get("performance", "cache_song_metadata"):
            songhash = hashlib.sha1(open(self.noteFileName, 'rb').read()).hexdigest()
            try:  # it crashes here on previews!
                result = _songDB.execute('SELECT `info` FROM `songinfo` WHERE `hash` = ?', [
                                         songhash]).fetchone()
                if result is None:
                    log.info('Song %s was not found in the cache.' % infoFileName)
            except Exception:
                log.error('Cache retrieval failed for %s: ' % infoFileName)
                result = None

            if result is not None:
                try:
                    self.__dict__.update(cPickle.loads(str(result[0])))
                    _songDB.execute('UPDATE `songinfo` SET `seen` = 1 WHERE `hash` = ?', [songhash])
                    log.debug('Song %s successfully loaded from cache.' % infoFileName)
                    return
                except Exception:
                    # The entry is there but could not be loaded.
                    # Nuke it and let it be rebuilt.
                    log.error('Song %s has invalid cache data (will rebuild): ' % infoFileName)
                    _songDB.execute('DELETE FROM `songinfo` WHERE `hash` = ?', [songhash])

            # preload this stuff...
            self.getParts()
            self.getSections()

            # Write this song's info into the cache.
            log.debug('Writing out cache for song %s.' % self.fileName)
            pdict = {}
            for key in ('_parts', '_partDifficulties', '_midiStyle', '_sections'):
                pdict[key] = getattr(self, key)
            _songDB.execute('INSERT OR REPLACE INTO `songinfo` (`hash`, `info`, `seen`) VALUES (?, ?, 1)', [
                            songhash, cPickle.dumps(pdict)])

    def addHighscore(self, difficulty, score, stars, name, part=parts[GUITAR_PART], scoreExt=(0, 0, 0, "RF-mod", 0, "None", 0)):
        highScores = self.highScores[str(part)]

        if difficulty.id not in highScores:
            highScores[difficulty.id] = []
        highScores[difficulty.id].append((score, stars, name, scoreExt))
        highScores[difficulty.id].sort(key=lambda h: h[0], reverse=True)
        highScores[difficulty.id] = highScores[difficulty.id][:5]
        for i, scores in enumerate(highScores[difficulty.id]):
            _score, _stars, _name, _scores_ext = scores
            if _score == score and _stars == stars and _name == name:
                return i
        return -1

    def getScores(self, part):
        """ Read highscores and verify their hashes """
        # There ain't no security like security throught obscurity :)
        self.highScores[str(part)] = {}

        if part.id is not GUITAR_PART:
            scores = self._get("scores_" + str(part), str, "")
            scores_ext = self._get("scores_" + str(part) + "_ext", str, "")
        else:
            scores = self._get("scores", str, "")
            scores_ext = self._get("scores_ext", str, "")

        if scores:
            try:
                scores = cerealizer.loads(binascii.unhexlify(scores))
            except Exception:
                log.error("High scores lost! Can't parse scores = %s" % scores)
                scores = None

        if not scores:
            return

        if scores_ext:
            try:
                scores_ext = cerealizer.loads(binascii.unhexlify(scores_ext))
            except Exception:
                log.error("High scores lost! Can't parse scores_ext = %s" % scores_ext)
                scores_ext = None

        for difficulty in scores.keys():
            try:
                difficulty = difficulties[difficulty]
            except KeyError:
                continue
            for i, base_scores in enumerate(scores[difficulty.id]):
                score, stars, name, _hash = base_scores
                if scores_ext:
                    # Someone may have mixed extended and non extended
                    try:
                        if len(scores_ext[difficulty.id][i]) < 9:
                            hash_ext, stars2, notesHit, notesTotal, noteStreak, modVersion, oldInfo, oldInfo2 = scores_ext[
                                difficulty.id][i]
                            handicapValue = 0
                            longHandicap = "None"
                            originalScore = 0
                        else:
                            hash_ext, stars2, notesHit, notesTotal, noteStreak, modVersion, handicapValue, longHandicap, originalScore = scores_ext[
                                difficulty.id][i]
                        scoreExt = (notesHit, notesTotal, noteStreak, modVersion,
                                    handicapValue, longHandicap, originalScore)
                    except Exception:
                        hash_ext = 0
                        scoreExt = (0, 0, 0, "RF-mod", 0, "None", 0)
                if self.getScoreHash(difficulty, score, stars, name) == _hash:
                    if scores_ext and _hash == hash_ext:
                        self.addHighscore(difficulty, score, stars, name, part, scoreExt=scoreExt)
                    else:
                        self.addHighscore(difficulty, score, stars, name, part)
                else:
                    log.warning("Weak hack attempt detected. Better luck next time.")

    def _set(self, attr, value):
        if not self.info.has_section("song"):
            self.info.add_section("song")
        self.info.set("song", attr, value)

    def getObfuscatedScores(self, part=parts[GUITAR_PART]):
        s = {}
        highScores = self.highScores[str(part)]

        for difficulty in highScores.keys():
            if isinstance(difficulty, Difficulty):
                diff = difficulty.id
            else:
                diff = difficulty
            s[diff] = [(score, stars, name, self.getScoreHash(difficulty, score, stars, name))
                       for score, stars, name, scores_ext in highScores[difficulty]]
        return binascii.hexlify(cerealizer.dumps(s))

    def getObfuscatedScoresExt(self, part=parts[GUITAR_PART]):
        s = {}
        highScores = self.highScores[str(part)]

        for difficulty in highScores.keys():
            if isinstance(difficulty, Difficulty):
                diff = difficulty.id
            else:
                diff = difficulty
            s[diff] = [(self.getScoreHash(difficulty, score, stars, name), stars) +
                       scores_ext for score, stars, name, scores_ext in highScores[difficulty]]
        return binascii.hexlify(cerealizer.dumps(s))

    def save(self):
        if self.highScores:
            for part in self._parts:
                if part.id is not GUITAR_PART:
                    self._set("scores_" + str(part), self.getObfuscatedScores(part))
                    self._set("scores_" + str(part) + "_ext", self.getObfuscatedScoresExt(part))
                else:
                    self._set("scores", self.getObfuscatedScores(part))
                    self._set("scores_ext", self.getObfuscatedScoresExt(part))

        try:
            f = open(self.fileName, "w")
        except IOError as e:
            log.error("Cannot save high scores due to: " + str(e))
        else:
            self.info.write(f)
            f.close()

    def _get(self, attr, type=None, default=""):
        try:
            v = self.info.get("song", attr)
        except Exception:
            v = default
        if v == "":  # key found, but empty - need to catch as int("") will burn.
            v = default
        if v is not None and type:
            v = type(v)
        return v

    def getPartDifficulties(self):
        if len(self._partDifficulties) != 0:
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
            log.debug("Retrieving parts from: " + noteFileName)
            info = MidiPartsDiffReader()

            midiIn = midi.MidiInFile(info, noteFileName)
            midiIn.read()
            if info.parts == []:
                log.debug("Improperly named tracks. Attempting to force first track guitar.")
                info = MidiPartsDiffReader(forceGuitar=True)
                midiIn = midi.MidiInFile(info, noteFileName)
                midiIn.read()
            if info.parts == []:
                raise Exception("No tracks found in %s" % noteFileName)
            self._midiStyle = info.midiStyle
            info.parts.sort(key=lambda ipart: ipart.id)
            self._parts = info.parts
            for part in info.parts:
                if self.tutorial:
                    self._partDifficulties[part.id] = [difficulties[HAR_DIF]]
                    continue
                info.difficulties[part.id].sort(key=lambda idiff: idiff.id)
                self._partDifficulties[part.id] = info.difficulties[part.id]
        except Exception:
            log.warning("Note file not parsed correctly. Selected part and/or difficulty may not be available.")
            self._parts = parts.values()
            for part in self._parts:
                self._partDifficulties[part.id] = difficulties.values()
        return self._parts

    def getName(self):
        return self._get("name")

    def setName(self, value):
        self._set("name", value)

    @property
    def artist(self):
        return self._get("artist")

    @property
    def album(self):
        return self._get("album")

    @property
    def genre(self):
        return self._get("genre")

    @property
    def icon(self):
        return self._get("icon")

    @property
    def bossBattle(self):
        return self._get("boss_battle")

    @property
    def diffSong(self):
        return self._get("diff_band", int, -1)

    @property
    def diffGuitar(self):
        return self._get("diff_guitar", int, -1)

    @property
    def diffDrums(self):
        return self._get("diff_drums", int, -1)

    @property
    def diffBass(self):
        return self._get("diff_bass", int, -1)

    @property
    def diffVocals(self):
        return self._get("diff_vocals", int, -1)

    @property
    def year(self):
        return self._get("year")

    @property
    def loadingPhrase(self):
        return self._get("loading_phrase")

    @property
    def cassetteColor(self):
        c = self._get("cassettecolor")
        if c:
            return hexToColor(c)

    def getScoreHash(self, difficulty, score, stars, name):
        if isinstance(difficulty, Difficulty):
            difficulty = difficulty.id
        return hashlib.sha1(six.b("%d%d%d%s" % (difficulty, score, stars, six.b(name)))).hexdigest()

    @property
    def delay(self):
        return self._get("delay", int, 0)

    @property
    def frets(self):
        return self._get("frets")

    @property
    def version(self):
        return self._get("version")

    @property
    def tags(self):
        return self._get("tags")

    @property
    def hopo(self):
        return self._get("hopo")

    def getCount(self):
        return self._get("count")

    def setCount(self, value):
        self._set("count", value)

    @property
    def eighthNoteHopo(self):
        return self._get("eighthnote_hopo")

    @property
    def lyrics(self):
        return self._get("lyrics")

    @property
    # because of how RB3 pro drums are formatted, this tag
    # detects a way to properly read the cymbals notes in the midi
    def prodrum(self):
        return self._get("pro_drum")

    def getHighscoresWithPartString(self, difficulty, part=str(parts[GUITAR_PART])):
        return self.getHighscores(difficulty, part)

    def getHighscores(self, difficulty, part=parts[GUITAR_PART]):
        highScores = self.highScores[str(part)]

        try:
            return highScores[difficulty.id]
        except KeyError:
            return []

    def uploadHighscores(self, url, songHash, part=parts[GUITAR_PART]):
        if part == parts[VOCAL_PART]:  # not implemented
            return False
        try:
            d = {
                "songName": self.songName,
                "songHash": songHash,
                "scores":   self.getObfuscatedScores(part=part),
                "scores_ext": self.getObfuscatedScoresExt(part=part),
                "version":  "%s-3.100" % Version.PROGRAM_NAME,
                "songPart": part
            }
            data = urlopen(url + "?" + urlencode(d)).read()
            log.debug("Score upload result: %s" % data)
            return data  # want to return the actual result data.
        except Exception as e:
            log.error("Score upload error: %s" % e)
            return False
        return True

    @property
    def tutorial(self):
        return self._get("tutorial", int, 0) == 1

    def findTag(self, find, value=None):
        for tag in self.tags.split(','):
            temp = tag.split('=')
            if find == temp[0]:
                if value is None:
                    return True
                elif len(temp) == 2 and value == temp[1]:
                    return True

        return False

    def getSections(self):
        if self._sections is not None:
            return self._sections
        # See which sections are available
        try:
            noteFileName = self.noteFileName
            log.debug("Retrieving sections from: " + noteFileName)
            info = MidiSectionReader()
            midiIn = midi.MidiInFile(info, noteFileName)
            try:
                midiIn.read()
            except MidiSectionReader.Done:
                pass
            self._sections = info.sections
            if len(self._sections) <= 1:
                self._sections = info.noteCountSections
                self._sections.insert(0, ["0:00 -> Start", 0.0])

                # only log if enabled
                log.warning("Song.py: Using auto-generated note count sections...")
                if self.logSections == 1:
                    log.debug("Practice sections: " + str(self._sections))

            else:
                self._sections.insert(0, ["0:00 -> Start", 0.0])

                # only log if enabled
                if self.logSections == 1:
                    log.debug("Practice sections: " + str(self._sections))

        except Exception as e:
            log.warning("Song.py: Unable to retrieve section names for practice mode selection: %s" % e)
            self._sections = None
        return self._sections

    def getUnlockID(self):
        return self._get("unlock_id")

    def getUnlockRequire(self):
        return self._get("unlock_require")

    def getUnlockText(self):
        return self._get("unlock_text", default=_("This song is locked."))

    # This takes True or False, not the value in the ini
    def setCompleted(self, value):
        if value:
            self._set("unlock_completed", len(
                removeSongOrderPrefixFromName(self.name)) * len(self.artist) + 1)
        else:
            self._set("unlock_completed", 0)

    # This returns True or False, not the value in the ini
    def getCompleted(self):
        iniValue = self._get("unlock_completed", int, default=0)
        # yay, security through obscurity!
        if iniValue == len(removeSongOrderPrefixFromName(self.name)) * len(self.artist) + 1:
            return True
        else:
            return False

    def setLocked(self, value):
        self.locked = value

    # WARNING this will only work on a SongInfo loaded via getAvailableSongs
    def getLocked(self):
        return self.locked

    # adding song.ini setting to allow fretter to specify early hit
    # window size (none, half, or full)
    @property
    def early_hit_window_size(self):
        return self._get("early_hit_window_size", str)

    @property
    def hopofreq(self):
        return self._get("hopofreq")

    name = property(getName, setName)
    # New RF-mod Items
    parts = property(getParts)
    count = property(getCount, setCount)

    completed = property(getCompleted, setCompleted)
    sections = property(getSections)


class LibraryInfo(object):
    def __init__(self, libraryName, infoFileName):
        self.libraryName = libraryName
        self.fileName = infoFileName
        self.info = Config.MyConfigParser()
        self.songCount = 0

        self.artist = None

        log.debug("LibraryInfo class init (song.py)...")

        try:
            self.info.read(infoFileName)
        except Exception:
            pass

        # Set a default name
        if not self.name:
            self.name = os.path.basename(os.path.dirname(self.fileName))
        if Config.get("performance", "disable_libcount"):
            return
        # Count the available songs
        libraryRoot = os.path.dirname(self.fileName)
        if os.path.isdir(libraryRoot):
            for name in os.listdir(libraryRoot):
                if not os.path.isdir(os.path.join(libraryRoot, name)) or name.startswith("."):
                    continue
                if os.path.isfile(os.path.join(libraryRoot, name, "notes.mid")):
                    self.songCount += 1
                elif os.path.isfile(os.path.join(libraryRoot, name, "notes-unedited.mid")):
                    self.songCount += 1

    def _set(self, attr, value):
        if not self.info.has_section("library"):
            self.info.add_section("library")
        self.info.set("library", attr, value)

    def save(self):
        if os.access(os.path.dirname(self.fileName), os.W_OK):
            f = open(self.fileName, "w")
            self.info.write(f)
            f.close()

    def _get(self, attr, type=None, default=""):
        try:
            v = self.info.get("library", attr)
        except Exception:
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
            return hexToColor(c)

    def setColor(self, color):
        self._set("color", colorToHex(color))

    name = property(getName, setName)
    color = property(getColor, setColor)


class BlankSpaceInfo(object):
    def __init__(self, nameToDisplay=""):
        self.name = nameToDisplay
        self.color = None
        self.artist = None  # prevents search errors

        log.debug("BlankSpaceInfo class init (song.py)...")

    def getUnlockID(self):
        return ""


class CareerResetterInfo(object):
    def __init__(self):
        self.name = _("Reset Career")
        self.color = None
        self.artist = None  # prevents search errors

        log.debug("CareerResetterInfo class init (song.py)...")


class RandomSongInfo(object):
    def __init__(self):
        self.name = _("   (Random Song)")
        self.color = None
        self.artist = None  # prevents search errors

        log.debug("RandomSongInfo class init (song.py)...")


class TitleInfo(object):
    def __init__(self, config, section):
        self.info = config
        self.section = section
        self.artist = None  # prevents search errors

        log.debug("TitleInfo class init (song.py)...")

    def _set(self, attr, value):
        self.info.set(self.section, attr, value)

    def _get(self, attr, type=None, default=""):
        try:
            v = self.info.get(self.section, attr)
        except Exception:
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
            return hexToColor(c)

    def setColor(self, color):
        self._set("color", colorToHex(color))

    def getUnlockID(self):
        return self._get("unlock_id")

    name = property(getName, setName)
    color = property(getColor, setColor)


class SortTitleInfo(object):
    def __init__(self, nameToDisplay):
        self.name = nameToDisplay
        self.color = None
        self.artist = None  # prevents search errors

        log.debug("TitleInfo class init (song.py)...")

    def getUnlockID(self):
        return self.name


class Event(object):
    def __init__(self, length):
        self.length = length


class MarkerNote(Event):
    def __init__(self, number, length, endMarker=False):
        Event.__init__(self, length)
        self.number = number
        self.endMarker = endMarker
        self.happened = False

    def __repr__(self):
        return "<#%d>" % self.number


class Note(Event):
    def __init__(self, number, length, special=False, tappable=0, star=False, finalStar=False):
        Event.__init__(self, length)
        self.number = number  # keeps track of fret number
        self.played = False
        self.special = special
        self.tappable = tappable
        # RF-mod
        self.hopod = False
        self.skipped = False
        self.flameCount = 0
        self.HCount2 = 0
        self.star = star
        self.finalStar = finalStar
        self.noteBpm = 0.0
        # pro-mode
        self.lane = 0  # named lane to be vague so then it can be used in guitar and drums

    def __repr__(self):
        return "<#%d>" % self.number


class VocalNote(Event):
    def __init__(self, note, length, tap=False):
        Event.__init__(self, length)
        self.note = note
        self.phrase = 0
        self.played = False
        self.stopped = False
        self.accuracy = 0.0
        self.tap = tap
        self.speak = False
        self.extra = False  # not sure what this is yet - "^"
        self.lyric = None
        self.heldNote = False


class Bars(Event):
    def __init__(self, barType):
        Event.__init__(self, barType)
        self.barType = barType  # 0 half-beat, 1 beat, 2 measure
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


class Track(object):
    granularity = 50

    def __init__(self, engine):
        self.events = []
        self.allEvents = []
        self.marked = False

        self.currentIndex = None
        self.maxIndex = None

        log.debug("Track class init (song.py)...")

    def __getitem__(self, index):
        return self.allEvents[index]

    def __len__(self):
        return len(self.allEvents)

    @property
    def length(self):
        lastTime = 0
        for _time, event in self.getAllEvents():
            if not isinstance(event, Note) and not isinstance(event, VocalPhrase):
                continue
            if _time + event.length > lastTime:
                lastTime = _time + event.length
        return round((lastTime + 1000.0) / 1000.0) * 1000.0

    def addEvent(self, time, event):
        for t in range(int(time / self.granularity), int((time + event.length) / self.granularity) + 1):
            if len(self.events) < t + 1:
                n = t + 1 - len(self.events)
                n *= 8
                self.events = self.events + [[] for n in range(n)]
            self.events[t].append((time - (t * self.granularity), event))
        self.allEvents.append((time, event))

        if self.maxIndex is None:  # tracking track size
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

            # tracking track size
            if self.maxIndex is not None:
                self.maxIndex -= 1
                if self.maxIndex < 0:
                    self.maxIndex = None
                    self.currentIndex = None

    def getNextEvent(self, lookAhead=0):
        if self.maxIndex is not None and self.currentIndex is not None:
            # lookAhead > 0 means look that many indices ahead of the Next event
            if (self.currentIndex + lookAhead) <= self.maxIndex:
                return self.allEvents[self.currentIndex + lookAhead]
        return None

    def getPrevEvent(self, lookBehind=0):  # lookBehind of 0 = return previous event.
        if self.maxIndex is not None and self.currentIndex is not None:
            # lookBehind > 0 means look that many indices behind of the Prev event
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
                if (time, event) not in events:
                    events.append((time, event))
        return events

    def getAllEvents(self):
        return self.allEvents

    def reset(self):
        if self.maxIndex:
            self.currentIndex = 0
        for eventList in self.events:
            for _time, event in eventList:
                if isinstance(event, Note):
                    event.played = False
                    event.hopod = False
                    event.skipped = False
                    event.flameCount = 0
                if isinstance(event, MarkerNote):
                    event.happened = False


class VocalTrack(Track):
    def __init__(self, engine):
        self.allNotes = {}  # dict(int -> tuple(num,Event)) -- basically a time -> Event map
        self.allWords = {}
        self.starTimes = []
        self.minPitch = 127
        self.maxPitch = 0
        self.logTempoEvents = 0
        if engine:
            self.logTempoEvents = engine.config.get("log", "log_tempo_events")
        Track.__init__(self, engine)

    def getAllNotes(self):
        return self.allNotes

    def addEvent(self, time, event):
        if isinstance(event, VocalNote) or isinstance(event, VocalPhrase):
            Track.addEvent(self, time, event)

    def removeTempoEvents(self):
        for _time, event in self.allEvents:
            if isinstance(event, Tempo):
                self.allEvents.remove((_time, event))
                if self.logTempoEvents == 1:
                    log.debug("Tempo event removed from VocalTrack during cleanup: " +
                              str(event.bpm) + "bpm")

    def markPhrases(self):
        phraseId = 0
        phraseTimes = []
        markStars = False
        if len(self.starTimes) < 2:
            markStars = True
            log.warning(
                "This song does not appear to have any vocal star power events - falling back on auto-generation.")
        for _time, event in self.getAllEvents():
            if isinstance(event, VocalPhrase):
                if _time in self.starTimes and not markStars:
                    event.star = True
                if _time in phraseTimes:
                    log.warning("Phrase repeated - some lyric phrase errors may occur.")
                    phraseId += 1
                    continue
                if markStars and phraseId + 1 % 7 == 0:
                    event.star = True
                phraseTimes.append(_time)
                phraseId += 1
        for _time, notes in self.allNotes.items():
            phraseId = 0
            for i, phraseTime in enumerate(self.getAllEvents()):
                if _time > phraseTime[0] and _time < phraseTime[0] + phraseTime[1].length:
                    phraseId = i
                    if phraseId < 0:
                        phraseId = 0
                    break
            notes[1].phrase = phraseId
            if not notes[1].tap:
                try:
                    lyric = self.allWords[notes[0]]
                except KeyError:
                    lyric = None
                if lyric:
                    if lyric.find("+") >= 0:
                        notes[1].heldNote = True
                    else:
                        if lyric.find("#") >= 0:
                            notes[1].speak = True
                            notes[1].lyric = lyric.strip("#")
                        elif lyric.find("^") >= 0:
                            notes[1].extra = True
                            notes[1].lyric = lyric.strip("^")
                        else:
                            notes[1].lyric = lyric
            else:
                self.allEvents[phraseId][1].tapPhrase = True
            self.allEvents[phraseId][1].addEvent(notes[0], notes[1])
            self.allEvents[phraseId][1].minPitch = min(
                self.allEvents[phraseId][1].minPitch, notes[1].note)
            self.allEvents[phraseId][1].maxPitch = max(
                self.allEvents[phraseId][1].maxPitch, notes[1].note)
        for _time, event in self.getAllEvents():
            if isinstance(event, VocalPhrase):
                event.sort()

    def reset(self):
        if self.maxIndex:
            self.currentIndex = 0
        for eventList in self.events:
            for _time, event in eventList:
                if isinstance(event, VocalPhrase):
                    for _time, note in event.allEvents:
                        note.played = False
                        note.stopped = False
                        note.accuracy = 0.0


class VocalPhrase(VocalTrack, Event):
    def __init__(self, length, star=False):
        Event.__init__(self, length)
        VocalTrack.__init__(self, engine=None)
        self.star = star
        self.tapPhrase = False

    def sort(self):
        eventDict = {}
        newEvents = []
        for _time, event in self.allEvents:
            if isinstance(event, VocalNote):
                eventDict[int(_time)] = (_time, event)
        times = list(eventDict.keys())
        times.sort()
        for _time in times:
            newEvents.append(eventDict[_time])
        self.allEvents = newEvents


class TempoTrack(Track):
    """ Special Track type for tempo events """

    def __init__(self, engine):
        Track.__init__(self, engine)
        self.currentBpm = DEFAULT_BPM

    def reset(self):
        self.currentBpm = DEFAULT_BPM

    def getCurrentTempo(self, pos):
        """ Track current tempo in realtime based on time / position """
        if self.currentIndex:
            tempEventHolder = self.getNextEvent()  # check if next BPM change is here yet
            if tempEventHolder:
                _time, event = tempEventHolder
                if pos >= _time:
                    self.currentIndex += 1
                    self.currentBpm = event.bpm
        return self.currentBpm

    def getNextTempoChange(self, pos):
        if self.currentIndex:
            return self.getNextEvent()
        return None

    # will hunt through all tempo events to find it - intended for use
    # during initializations only!
    def searchCurrentTempo(self, pos):
        foundBpm = None
        foundTime = None
        for _time, event in self.allEvents:
            if not foundBpm or not foundTime:
                foundBpm = event.bpm
                foundTime = _time
            else:
                # want to discard if the foundTime is before pos, but this event is after pos.
                # -- also want to take newer BPM if time > foundTime >= pos
                if _time <= pos:  # first required condition.
                    if _time > foundTime:  # second required condition for sorting.
                        foundBpm = event.bpm
                        foundTime = _time
        if foundBpm:
            return foundBpm
        else:  # return default BPM if no events
            return DEFAULT_BPM


class NoteTrack(Track):
    """ Special Track type for note events, with marking functions """

    def __init__(self, engine):
        Track.__init__(self, engine)
        self.chordFudge = 1

        self.hopoTick = engine.config.get("coffee", "hopo_frequency")
        self.songHopoFreq = engine.config.get("game", "song_hopo_freq")
        self.logTempoEvents = engine.config.get("log", "log_tempo_events")

    def removeTempoEvents(self):
        for _time, event in self.allEvents:
            if isinstance(event, Tempo):
                self.allEvents.remove((_time, event))
                if self.logTempoEvents == 1:
                    log.debug("Tempo event removed from NoteTrack during cleanup: " +
                              str(event.bpm) + "bpm")

    def flipDrums(self):
        for _time, event in self.allEvents:
            if isinstance(event, Note):
                event.number = (5 - event.number) % 5

    def markHopo(self, eighthNH, HoposAfterChords, songHopoFreq):
        lastTick = 0
        lastTime = 0
        lastEvent = Note

        tickDelta = 0
        noteDelta = 0

        try:
            songHopoFreq = int(songHopoFreq)
        except Exception:
            songHopoFreq = None
        if self.songHopoFreq == 1 and songHopoFreq in [0, 1, 2, 3, 4, 5]:
            log.debug("markHopoGH2: song-specific HOPO frequency %d forced" % songHopoFreq)
            self.hopoTick = songHopoFreq

        # dtb file says 170 ticks
        hopoDelta = 170
        if str(eighthNH) == "1":
            hopoDelta = 250
        else:
            hopoDelta = 170

        self.chordFudge = 1  # there should be no chord fudge.

        if self.hopoTick == 0:
            ticksPerBeat = 960
        elif self.hopoTick == 1:
            ticksPerBeat = 720
        elif self.hopoTick == 2:
            ticksPerBeat = 480
        elif self.hopoTick == 3:
            ticksPerBeat = 360
        elif self.hopoTick == 4:
            ticksPerBeat = 240
        else:
            ticksPerBeat = 240
            hopoDelta = 250

        hopoNotes = []

        tickDeltaBeforeLast = 0  # 3 notes in the past
        lastTickDelta = 0  # 2 notes in the past

        bpmNotes = []
        firstTime = 1

        # to prevent crashes on songs without a BPM set
        bpmEvent = None
        bpm = None

        # If already processed abort
        if self.marked:
            return

        for _time, event in self.allEvents:
            if isinstance(event, Tempo):
                bpmNotes.append([_time, event])
                continue
            if not isinstance(event, Note):
                continue

            while bpmNotes and _time >= bpmNotes[0][0]:
                # Adjust to new BPM
                # bpm = bpmNotes[0][1].bpm
                bpmTime, bpmEvent = bpmNotes.pop(0)
                bpm = bpmEvent.bpm

            if not bpm:
                bpm = DEFAULT_BPM

            tick = (_time * bpm * ticksPerBeat) / 60000.0
            lastTick = (lastTime * bpm * ticksPerBeat) / 60000.0

            # skip first note
            if firstTime == 1:
                event.tappable = -3
                lastEvent = event
                lastTime = _time
                eventBeforeLast = lastEvent
                eventBeforeEventBeforeLast = eventBeforeLast
                firstTime = 0
                continue

            # tickDeltaBeforeTickDeltaBeforeLast = tickDeltaBeforeLast    #4 notes in the past
            tickDeltaBeforeLast = lastTickDelta  # 3 notes in the past
            lastTickDelta = tickDelta  # 2 notes in the past

            tickDelta = tick - lastTick
            noteDelta = event.number - lastEvent.number
            # This initial sweep drops any notes within the timing
            # threshold into the hopoNotes array (which would be more aptly named,
            #  the "potentialHopoNotes" array).  Another loop down below
            #   further refines the HOPO determinations...

            # previous note and current note HOPOable
            if tickDelta <= hopoDelta:
                # Add both notes to HOPO list even if duplicate.  Will come out in processing
                if (not hopoNotes) or not (hopoNotes[-1][0] == lastTime and hopoNotes[-1][1] == lastEvent):
                    # special case for first marker note.  Change it to a HOPO start
                    if not hopoNotes and lastEvent.tappable == -3:
                        lastEvent.tappable = 1
                    # this may be incorrect if a bpm event happened inbetween this note and
                    # last note

                    if bpmEvent:
                        hopoNotes.append([lastTime, bpmEvent])

                    hopoNotes.append([lastTime, lastEvent])

                if bpmEvent:
                    hopoNotes.append([bpmTime, bpmEvent])

                hopoNotes.append([_time, event])

            # HOPO definitely over - time since last note too great.
            if tickDelta > hopoDelta:
                if hopoNotes != []:
                    # If the last event is the last HOPO note, mark it as a HOPO end
                    if lastEvent.tappable != -1 and hopoNotes[-1][1] == lastEvent:
                        if lastEvent.tappable >= 0:
                            lastEvent.tappable = 3
                        else:
                            lastEvent.tappable = -1

        # note pattern:
            # R R R R R
            # Y       Y
        # should be
            # 1 3-2-2-4
        # first pass:
            # actual: if first RY considered "same note" as next R:
            # -4 0-2-2
            # if last RY considered "same note" as prev R:
            # -4 0-2-2-2
            # actual: if first RY not considered "same note" as next R:
            # -4 0-2-2

            # This is the same note as before
            elif noteDelta == 0:
                # Add both notes to bad list even if duplicate.  Will come out in processing
                # to fix same-note HOPO bug.
                if HoposAfterChords:
                    if lastEvent.tappable != -4:  # if the last note was not a chord,
                        # and if the event before last was a chord, don't remark the last one.
                        if eventBeforeLast.tappable == -4 and lastTickDelta <= hopoDelta:
                            event.tappable = -5
                        else:
                            event.tappable = -2
                        # yeah, mark the last one.
                        lastEvent.tappable = -2
                else:
                    event.tappable = -2
                    lastEvent.tappable = -2

            # This is a chord
            # both this note and the last note are listed at the same time
            # to allow after-chord HOPOs, we need a separate identification for "chord" notes
            # and also might need to track the "last" chord notes in a separate array
            elif tickDelta < self.chordFudge:
                # Add both notes to bad list even if duplicate.  Will come out in processing
                if HoposAfterChords:
                    if eventBeforeLast.tappable == -2 and lastTickDelta <= hopoDelta:
                        if eventBeforeEventBeforeLast.tappable >= 0 and tickDeltaBeforeLast <= hopoDelta:
                            eventBeforeLast.tappable = -5  # special case that needs to be caught
                        if lastEvent.tappable == -2:  # catch case where event before last event was marked as the same note
                            if eventBeforeEventBeforeLast.tappable >= 0 and tickDeltaBeforeLast <= hopoDelta:
                                eventBeforeLast.tappable = 0
                    lastEvent.tappable = -4
                    event.tappable = -4
                # keep track of chords as they are found
                else:
                    lastEvent.tappable = -1
                    event.tappable = -1

            # to really check marking, need to track 3 notes into the past.
            eventBeforeEventBeforeLast = eventBeforeLast
            eventBeforeLast = lastEvent
            lastEvent = event
            lastTime = _time

        else:
            # Add last note to HOPO list if applicable
            if noteDelta != 0 and tickDelta > self.chordFudge and tickDelta < hopoDelta and isinstance(event, Note):

                if bpmEvent:
                    hopoNotes.append([_time, bpmEvent])

                hopoNotes.append([_time, event])

            # marker: (next - FOR loop)----

        # comments - updated marking system
        # --at this point, the initial note marking sweep has taken place.  Here is further marking of hopoNotes.
        # the .tappable property has special meanings:
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

        tickDeltaBeforeTickDeltaBeforeLast = 0  # 4 notes in the past
        tickDeltaBeforeLast = 0  # 3 notes in the past
        lastTickDelta = 0  # 2 notes in the past

        bpmNotes = []

        for _time, note in list(hopoNotes):
            if isinstance(note, Tempo):
                bpmNotes.append([_time, note])
                continue
            if not isinstance(note, Note):
                continue
            while bpmNotes and _time >= bpmNotes[0][0]:
                # Adjust to new BPM
                # bpm = bpmNotes[0][1].bpm
                bpmTime, bpmEvent = bpmNotes.pop(0)
                bpm = bpmEvent.bpm

            if firstTime == 1:
                if note.tappable >= 0:
                    note.tappable = 1
                lastEvent = note
                lastTime = _time
                firstTime = 0
                eventBeforeLast = lastEvent
                eventBeforeEventBeforeLast = eventBeforeLast
                eventBeforeEventBeforeEventBeforeLast = eventBeforeLast
                continue

            # need to recompute (or carry forward) BPM at this time

            tickDeltaBeforeTickDeltaBeforeLast = tickDeltaBeforeLast  # 4 notes in the past
            tickDeltaBeforeLast = lastTickDelta  # 3 notes in the past
            lastTickDelta = tickDelta  # 2 notes in the past
            tick = (_time * bpm * ticksPerBeat) / 60000.0
            lastTick = (lastTime * bpm * ticksPerBeat) / 60000.0
            tickDelta = tick - lastTick

            # current Note Invalid for HOPO----------
            if note.tappable < 0:

                # test note pattern:
                # R   R     R R R R
                # Y Y Y Y Y     Y
                # first pass:
                # -4-2-4-2-5-2-2-4
                # second pass:
                # 1 3 1 3 1 3-2-4

                # If current note is beginning of a same note sequence, it's valid for END of HOPO only
                # need to alter this to not screw up single-same-note-before chords:
                if lastEvent.tappable in [1, 2] and note.tappable == -2:
                    note.tappable = 3
                # If current note is invalid for HOPO, and previous note was start of a
                # HOPO section, then previous note not HOPO
                elif lastEvent.tappable == 1:
                    lastEvent.tappable = 0

                # and let's not forget the special case when two same-note-sequences on
                # different frets are in sequence:
                elif lastEvent.tappable == -2 and note.tappable == -2 and lastEvent.number != note.number:
                    lastEvent.tappable = 1
                    note.tappable = 3
                # special case where the new -5 note is followed by a string same notes on
                # a different fret:
                elif lastEvent.tappable == -5 and note.tappable == -2:
                    lastEvent.tappable = 1
                    note.tappable = 3

                # special case where last note was a chord, and this note is counted as
                # the same note as the last in the chord
                elif lastEvent.tappable == -4 and note.tappable == -2:
                    thisNoteShouldStillBeAHopo = True
                    # determine the highest note in the chord:
                    topChordNote = lastEvent.number
                    if eventBeforeLast.number > topChordNote:
                        topChordNote = eventBeforeLast.number
                    numChordNotes = 2
                    # now to determine how many notes were in that chord:
                    if tickDeltaBeforeLast < self.chordFudge:  # is there a 3rd note in the same chord?
                        if eventBeforeEventBeforeLast.number > topChordNote:
                            topChordNote = eventBeforeEventBeforeLast.number
                        numChordNotes = 3
                        if tickDeltaBeforeTickDeltaBeforeLast < self.chordFudge:  # is there a 4th note in the same chord?
                            if eventBeforeEventBeforeEventBeforeLast.number > topChordNote:
                                topChordNote = eventBeforeEventBeforeEventBeforeLast.number
                            numChordNotes = 4
                    if topChordNote == note.number:  # only if the note number matches the top chord note do we outlaw the HOPO.
                        thisNoteShouldStillBeAHopo = False
                    if thisNoteShouldStillBeAHopo:
                        # here, need to go back and mark all notes in this chord as tappable = 1 not just the last one.
                        # chord max of 4 frets (5 is just ridiculous) - so if "lastEvent" is the
                        # 4th, must go back and change 3rd, 2nd, and 1st
                        lastEvent.tappable = 1
                        eventBeforeLast.tappable = 1  # at least 2 notes in chord
                        if numChordNotes >= 3:  # is there a 3rd note in the same chord?
                            eventBeforeEventBeforeLast.tappable = 1
                            if numChordNotes == 4:  # is there a 4th note in the same chord?
                                eventBeforeEventBeforeEventBeforeLast.tappable = 1
                        note.tappable = 3

                # If current note is invalid for HOPO, and previous note was a HOPO
                # section, then previous note is end of HOPO
                elif lastEvent.tappable > 0:
                    lastEvent.tappable = 3
            # current note valid
            elif note.tappable >= 0:
                # String of same notes can be followed by HOPO
                if note.tappable == 3:

                    # the new after-chord HOPO special logic needs to also be
                    # applied here
                    if lastEvent.tappable == -5:  # special case, still can be HOPO start
                        lastEvent.tappable = 1
                    if lastEvent.tappable == -4:  # chord
                        thisNoteShouldStillBeAHopo = True
                        # determine the highest note in the chord:
                        topChordNote = lastEvent.number
                        if eventBeforeLast.number > topChordNote:
                            topChordNote = eventBeforeLast.number
                        numChordNotes = 2
                        # now to determine how many notes were in that chord:
                        if tickDeltaBeforeLast < self.chordFudge:  # is there a 3rd note in the same chord?
                            if eventBeforeEventBeforeLast.number > topChordNote:
                                topChordNote = eventBeforeEventBeforeLast.number
                            numChordNotes = 3
                            if tickDeltaBeforeTickDeltaBeforeLast < self.chordFudge:  # is there a 4th note in the same chord?
                                if eventBeforeEventBeforeEventBeforeLast.number > topChordNote:
                                    topChordNote = eventBeforeEventBeforeEventBeforeLast.number
                                numChordNotes = 4
                        if topChordNote == note.number:  # only if the note number matches the top chord note do we outlaw the HOPO.
                            thisNoteShouldStillBeAHopo = False
                        if thisNoteShouldStillBeAHopo:
                            # here, need to go back and mark all notes in this chord as tappable = 1 not just the last one.
                            # chord max of 4 frets (5 is just ridiculous) - so if "lastEvent" is the
                            # 4th, must go back and change 3rd, 2nd, and 1st
                            lastEvent.tappable = 1
                            eventBeforeLast.tappable = 1  # at least 2 notes in chord
                            if numChordNotes >= 3:  # is there a 3rd note in the same chord?
                                eventBeforeEventBeforeLast.tappable = 1
                                if numChordNotes == 4:  # is there a 4th note in the same chord?
                                    eventBeforeEventBeforeEventBeforeLast.tappable = 1
                        else:
                            note.tappable = -1

                    # This is the end of a valid HOPO section
                    if lastEvent.tappable in [1, 2]:
                        eventBeforeEventBeforeEventBeforeLast = eventBeforeLast
                        eventBeforeEventBeforeLast = eventBeforeLast
                        eventBeforeLast = lastEvent
                        lastEvent = note
                        lastTime = _time
                        continue
                    if lastEvent.tappable == -2:
                        # If its the same note again it's invalid
                        if lastEvent.number == note.number:
                            note.tappable = -2
                        else:
                            lastEvent.tappable = 1
                    elif lastEvent.tappable == 0:
                        lastEvent.tappable = 1
                    # If last note was invalid or end of HOPO section, and current note is
                    # end, it is really not HOPO
                    elif lastEvent.tappable not in [1, 2]:
                        note.tappable = 0
                    # If last event was invalid or end of HOPO section, current note is start
                    # of HOPO
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

                # default case, tappable=0
                else:
                    if lastEvent.tappable == -5:  # special case, still can be HOPO start
                        lastEvent.tappable = 1
                    if lastEvent.tappable == -4:  # chord
                        thisNoteShouldStillBeAHopo = True
                        # determine the highest note in the chord:
                        topChordNote = lastEvent.number
                        if eventBeforeLast.number > topChordNote:
                            topChordNote = eventBeforeLast.number
                        numChordNotes = 2
                        # now to determine how many notes were in that chord:
                        if tickDeltaBeforeLast < self.chordFudge:  # is there a 3rd note in the same chord?
                            if eventBeforeEventBeforeLast.number > topChordNote:
                                topChordNote = eventBeforeEventBeforeLast.number
                            numChordNotes = 3
                            if tickDeltaBeforeTickDeltaBeforeLast < self.chordFudge:  # is there a 4th note in the same chord?
                                if eventBeforeEventBeforeEventBeforeLast.number > topChordNote:
                                    topChordNote = eventBeforeEventBeforeEventBeforeLast.number
                                numChordNotes = 4
                        if topChordNote == note.number:  # only if the note number matches the top chord note do we outlaw the HOPO.
                            thisNoteShouldStillBeAHopo = False
                        if thisNoteShouldStillBeAHopo:
                            # here, need to go back and mark all notes in this chord as tappable = 1 not just the last one.
                            # chord max of 4 frets (5 is just ridiculous) - so if "lastEvent" is the
                            # 4th, must go back and change 3rd, 2nd, and 1st
                            lastEvent.tappable = 1
                            eventBeforeLast.tappable = 1  # at least 2 notes in chord
                            if numChordNotes >= 3:  # is there a 3rd note in the same chord?
                                eventBeforeEventBeforeLast.tappable = 1
                                if numChordNotes == 4:  # is there a 4th note in the same chord?
                                    eventBeforeEventBeforeEventBeforeLast.tappable = 1
                        else:
                            note.tappable = -1

                    if lastEvent.tappable == -2 and tickDelta <= hopoDelta:  # same note
                        lastEvent.tappable = 1
                    if lastEvent.tappable == 3 and tickDelta <= hopoDelta:  # supposedly last of a HOPO
                        lastEvent.tappable = 2

                    if lastEvent.tappable != 2 and lastEvent.tappable != 1:
                        note.tappable = 1
                    else:
                        if note.tappable == 1:
                            note.tappable = 1
                        else:
                            note.tappable = 2

            # to really check marking, need to track 4 notes into the past.
            eventBeforeEventBeforeEventBeforeLast = eventBeforeLast
            eventBeforeEventBeforeLast = eventBeforeLast
            eventBeforeLast = lastEvent
            lastEvent = note
            lastTime = _time
        else:
            if note is not None:
                # Handle last note
                # If it is the start of a HOPO, it's not really a HOPO
                if note.tappable == 1:
                    note.tappable = 0
                # If it is the middle of a HOPO, it's really the end of a HOPO
                elif note.tappable == 2:
                    # here, need to check if the last note is a HOPO after
                    # chord and is being merged into the chord (which happens if too close to
                    # end of song)
                    if tickDelta < self.chordFudge:
                        note.tappable = -4
                    else:
                        note.tappable = 3
        self.marked = True

    def markBars(self):
        tempoTime = []
        tempoBpm = []

        # get all the bpm changes and their times

        # TODO - count tempo events.  If 0, realize and log that this is a
        # song with no tempo events - and go mark all 120BPM bars.
        endBpm = None
        endTime = None
        for _time, event in self.allEvents:
            if isinstance(event, Tempo):
                tempoTime.append(_time)
                tempoBpm.append(event.bpm)
                endBpm = event.bpm
                continue
            if isinstance(event, Note):
                endTime = _time + event.length + 30000
                continue

        if endTime:
            tempoTime.append(endTime)
        if endBpm:
            tempoBpm.append(endBpm)

        # calculate and add the measures/beats/half-beats
        passes = 0
        limit = len(tempoTime)
        _time = tempoTime[0]
        THnote = 256.0  # 256th note
        drawBar = True
        i = 0
        while i < (limit - 1):
            msTotal = tempoTime[i + 1] - _time
            if msTotal == 0:
                i += 1
                continue
            tempbpm = tempoBpm[i]
            nbars = (msTotal * (tempbpm / (240.0 / THnote))) / 1000.0
            inc = msTotal / nbars

            while _time < tempoTime[i + 1]:
                if drawBar:
                    if passes % (THnote / 1.0) == 0.0:  # 256/1
                        event = Bars(2)  # measure
                        self.addEvent(_time, event)
                    elif passes % (THnote / 4.0) == 0.0:  # 256/4
                        event = Bars(1)  # beat
                        self.addEvent(_time, event)
                    elif passes % (THnote / 8.0) == 0.0:  # 256/8
                        event = Bars(0)  # half-beat
                        self.addEvent(_time, event)

                    passes = passes + 1

                _time = _time + inc
                drawBar = True

            if _time > tempoTime[i + 1]:
                _time = _time - inc
                drawBar = False

            i += 1

        # add the last measure/beat/half-beat
        if _time == tempoTime[i]:
            if passes % (THnote / 1.0) == 0.0:  # 256/1
                event = Bars(2)  # measure
                self.addEvent(_time, event)
            elif passes % (THnote / 4.0) == 0.0:  # 256/4
                event = Bars(1)  # beat
                self.addEvent(_time, event)
            elif passes % (THnote / 8.0) == 0.0:  # 256/8
                event = Bars(0)  # half-beat
                self.addEvent(_time, event)


class Song(object):
    def __init__(self, engine, infoFileName, songTrackNames, noteFileName, scriptFileName=None, partlist=[parts[GUITAR_PART]]):
        self.engine = engine

        log.debug("Song class init (song.py)...")

        self.info = SongInfo(infoFileName)
        self.tracks = []
        for i in partlist:
            if i == parts[VOCAL_PART]:
                self.tracks.append([VocalTrack(self.engine)])
            else:
                self.tracks.append([NoteTrack(self.engine) for t in range(len(difficulties))])

        self.difficulty = [difficulties[EXP_DIF] for i in partlist]
        self._playing = False
        self.start = 0.0
        self.noteFileName = noteFileName

        self.bpm = DEFAULT_BPM  # enforcing a default / fallback tempo of 120 BPM

        self.period = 60000.0 / self.bpm  # enforcing a default / fallback tempo of 120 BPM

        self.readyToGo = False  # to prevent anything from happening until all prepration & initialization is complete!

        self.parts = partlist
        self.delay = self.engine.config.get("audio", "delay")
        self.delay += self.info.delay
        self.missVolume = self.engine.config.get("audio", "miss_volume")
        self.backVolume = self.engine.config.get("audio", "songvol")
        self.activeVolume = self.engine.config.get("audio", "guitarvol")
        self.crowdVolume = self.engine.config.get("audio", "crowd_volume")

        self.hasMidiLyrics = False
        self.midiStyle = self.info.midiStyle

        # holds the detected early hit window size for the current song
        self.earlyHitWindowSize = EARLY_HIT_WINDOW_HALF

        self.hasStarpowerPaths = False
        self.hasFreestyleMarkings = False

        # add a separate variable to house the special text event tracks:
        # special text-event tracks for the separated text-event list variable
        # should result in eventTracks[0] through [4]
        self.eventTracks = [Track(self.engine) for t in range(0, 5)]

        self.midiEventTracks = []
        self.activeAudioTracks = []
        for i in partlist:
            if i == parts[VOCAL_PART]:
                self.midiEventTracks.append([None])
                self.activeAudioTracks.append(VOCAL_TRACK)
            else:
                self.midiEventTracks.append([Track(self.engine) for t in range(len(difficulties))])
                if i == parts[GUITAR_PART] or i == parts[LEAD_PART] or i == parts[PRO_GUITAR_PART]:
                    self.activeAudioTracks.append(GUITAR_TRACK)
                elif i == parts[RHYTHM_PART] or i == parts[BASS_PART]:
                    self.activeAudioTracks.append(RHYTHM_TRACK)
                elif i == parts[DRUM_PART] or i == parts[PRO_DRUM_PART]:
                    self.activeAudioTracks.append(DRUM_TRACK)

        self.vocalEventTrack = VocalTrack(self.engine)

        self.tempoEventTrack = TempoTrack(self.engine)  # need a separated Tempo/BPM track!

        self.breMarkerTime = None

        self.songTracks = OrderedDict()

        channel = 0

        for instrument, filePaths in songTrackNames.items():
            for filePath in filePaths:
                if instrument not in self.songTracks:
                    self.songTracks[instrument] = []
                try:
                    self.songTracks[instrument].append(StreamingSound(
                        self.engine.audio.getChannel(channel), six.b(filePath)))
                    channel += 1
                except Exception as e:
                    log.error("Unable to load song track: %s" % e)

        self.songTrack = self.songTracks.get('song', [])
        self.guitarTrack = self.songTracks.get('guitar', [])
        self.rhythmTrack = self.songTracks.get('rhythm', [])
        self.drumTrack = self.songTracks.get('drums', [])
        self.crowdTrack = self.songTracks.get('crowd', [])
        self.vocalTrack = self.songTracks.get('vocal', [])
        self.keyTrack = self.songTracks.get('keys', [])

        # single audio track song detection
        self.singleTrackSong = False
        trackCount = 0
        for name, trackGroup in self.songTracks.items():
            if len(trackGroup) > 0:
                trackCount += 1

        if trackCount == 1:
            self.singleTrackSong = True
            # force single-track miss volume setting instead
            self.missVolume = self.engine.config.get("audio", "single_track_miss_volume")
            log.debug(
                "Song with only a single audio track identified - single-track miss volume applied: " + str(self.missVolume))

        # load the notes
        if noteFileName:
            log.debug("Retrieving notes from: " + noteFileName)
            midiIn = midi.MidiInFile(MidiReader(self), noteFileName)
            midiIn.read()

        # load the script
        if scriptFileName and os.path.isfile(scriptFileName):
            scriptReader = ScriptReader(self, open(scriptFileName))
            scriptReader.read()

        # set playback speed
        if self.engine.audioSpeedFactor != 1.0:
            self.setSpeed(self.engine.audioSpeedFactor)

    @property
    def length(self):
        length = 0
        for t in self.tracks:
            for n in t:  # note/vocal tracks
                if n.length > length:
                    length += (n.length - length)
        length += 3000.0
        return length

    def refreshAudioDelay(self):
        """ Re-retrieve the a/v delay setting so it can be changed in-game """
        self.delay = self.engine.config.get("audio", "delay")
        self.delay += self.info.delay

    def refreshVolumes(self):
        """ Refresh the miss volume after a pause """
        if self.singleTrackSong:
            # force single-track miss volume setting instead
            self.missVolume = self.engine.config.get("audio", "single_track_miss_volume")
        else:
            self.missVolume = self.engine.config.get("audio", "miss_volume")
        self.activeVolume = self.engine.config.get("audio", "guitarvol")
        self.backVolume = self.engine.config.get("audio", "songvol")

    def getCurrentTempo(self, pos):
        return self.tempoEventTrack.getCurrentTempo(pos)

    def getHash(self):
        h = hashlib.sha1()
        bs = 1024

        with open(self.noteFileName, 'rb') as f:
            while True:
                data = f.read(bs)
                if not data:
                    break
                h.update(data)

        return h.hexdigest()

    def setBpm(self, bpm):
        self.bpm = bpm
        self.period = 60000.0 / self.bpm

    def save(self):
        self.info.save()

    def play(self, start=0.0):
        self.start = start

        for name, trackGroups in self.songTracks.items():
            for track in trackGroups:
                if track:
                    track.setPosition(start / 1000.0)
                    track.play()

        for track in self.songTrack:
            if self.singleTrackSong:
                track.setVolume(self.activeVolume)
            else:
                track.setVolume(self.backVolume)

        self._playing = True

    def pause(self):
        self.engine.audio.pause()

    def unpause(self):
        self.engine.audio.unpause()

    def setInstrumentVolume(self, volume, part):
        # This function is called way to much during sustained notes.
        # IMO it should be called only if the note is hit or missed not
        # practically every game loop...
        if not self.singleTrackSong:
            for trackId in TRACK_ID_NAME_MAP.keys():
                if part == parts[trackId]:
                    trackName = TRACK_ID_NAME_MAP[trackId]

                    for track in self.songTracks[trackName]:
                        if volume == 0:
                            track.setVolume(self.missVolume)
                        elif volume == 1:
                            if part in self.activeAudioTracks:
                                track.setVolume(self.activeVolume)
                            else:
                                track.setVolume(self.backVolume)
                        else:
                            track.setVolume(volume)

    def setInstrumentPitch(self, semitones, part):
        if not self.singleTrackSong:
            for pitchPart in PITCH_SHIFTABLES:
                if part == parts[pitchPart]:
                    trackName = TRACK_ID_NAME_MAP[pitchPart]
                    for streamer in self.songTracks[trackName]:
                        streamer.setPitchBendSemitones(semitones)

    def resetInstrumentPitch(self, part):
        self.setInstrumentPitch(0.0, part)

    def setBackgroundVolume(self, volume):
        for track in self.songTrack:
            if volume == 1:
                track.setVolume(self.backVolume)
            else:
                track.setVolume(volume)

    def setCrowdVolume(self, volume):
        for track in self.crowdTrack:
            if volume == 1:
                track.setVolume(self.crowdVolume)
            else:
                track.setVolume(volume)

    def setAllTrackVolumes(self, volume):
        for groupName, trackGroup in self.songTracks.items():
            for track in trackGroup:
                if volume == 0:
                    track.setVolume(self.missVolume)
                elif volume == 1:
                    if groupName != "song" and (TRACK_NAME_ID_MAP[groupName] in self.activeAudioTracks or self.singleTrackSong):
                        track.setVolume(self.activeVolume)
                    else:
                        track.setVolume(self.backVolume)
                else:
                    track.setVolume(volume)

    def stop(self):
        for tracks in self.tracks:
            for track in tracks:
                track.reset()

        for tracks in self.midiEventTracks:
            for track in tracks:
                if track is not None:
                    track.reset()

        for trackGroups in self.songTracks.values():
            for track in trackGroups:
                if track:
                    track.stop()

        self._playing = False

    def setSpeed(self, speed):
        for trackGroups in self.songTracks.values():
            for track in trackGroups:
                if track:
                    track.setSpeed(speed)

    def fadeout(self, time):
        for tracks in self.tracks:
            for track in tracks:
                track.reset()

        for trackGroups in self.songTracks.values():
            for track in trackGroups:
                if track:
                    track.fadeout(time)

        self._playing = False

    def getPosition(self):
        if not self._playing:
            pos = 0.0
        else:
            pos = self.songTrack[0].getPosition() * 1000.0

        if pos < 0.0:
            pos = 0.0
        return pos - self.delay

    def isPlaying(self):
        return self._playing and self.songTrack[0].isPlaying()

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

    def getMidiEventTrack(self):  # for new special MIDI marker note track
        return [self.midiEventTracks[i][self.difficulty[i].id] for i in range(len(self.difficulty))]
    midiEventTrack = property(getMidiEventTrack)


class ScriptReader(object):
    def __init__(self, song, scriptFile):
        self.song = song
        self.file = scriptFile

        log.debug("ScriptReader class init (song.py)...")

    def read(self):
        for line in self.file:
            if line.startswith("#") or line.isspace():
                continue
            _time, length, type, data = re.split("[\t ]+", line.strip(), 3)
            _time = float(_time)
            length = float(length)

            if type == "text":
                event = TextEvent(data, length)
            elif type == "pic":
                event = PictureEvent(data, length)
            else:
                continue

            # add an event to the script.txt track
            self.song.eventTracks[TK_SCRIPT].addEvent(_time, event)


class MidiReader(midi.MidiOutStream):
    """ Fully parse and load a MIDI file for gameplay. """

    def __init__(self, song):
        midi.MidiOutStream.__init__(self)
        self.song = song
        self.heldNotes = {}
        self.velocity = {}
        self.ticksPerBeat = 480
        self.tempoMarkers = []
        self.partTrack = 0
        self.partnumber = -1

        self.vocalTrack = False
        self.useVocalTrack = False
        self.vocalOverlapCheck = []

        log.debug("MidiReader class init (song.py)...")

        self.logMarkerNotes = Config.get("game", "log_marker_notes")
        self.logTempoEvents = Config.get("log", "log_tempo_events")
        self.logSections = Config.get("game", "log_sections")

        self.guitarSoloIndex = 0
        self.guitarSoloActive = False
        self.guitarSoloSectionMarkers = False

    def addEvent(self, track, event, time=None):
        if self.partnumber == -1:
            # Looks like notes have started appearing before any part information.
            # Lets assume its part0
            self.partnumber = self.song.parts[0]

        if self.partnumber is None and isinstance(event, Note):
            return True

        if time is None:
            time = self.abs_time()
        assert time >= 0

        if track is None:
            for t in self.song.tracks:
                for s in t:
                    s.addEvent(time, event)
        else:

            tracklist = [i for i, j in enumerate(self.song.parts) if self.partnumber == j]
            for i in tracklist:
                # Each track needs it's own copy of the event, otherwise they'll interfere
                eventcopy = copy.deepcopy(event)
                if track < len(self.song.tracks[i]):
                    self.song.tracks[i][track].addEvent(time, eventcopy)

    def addVocalEvent(self, event, time=None):
        if time is None:
            time = self.abs_time()
        assert time >= 0

        if not self.useVocalTrack:
            return True

        track = [i for i, j in enumerate(self.song.parts) if self.partnumber == j][0]
        if isinstance(event, VocalNote):
            self.song.track[track].minPitch = min(event.note, self.song.track[track].minPitch)
            self.song.track[track].maxPitch = max(event.note, self.song.track[track].maxPitch)
            self.song.track[track].allNotes[int(time)] = (time, event)
        elif isinstance(event, VocalPhrase):
            self.song.track[track].addEvent(time, event)

    def addVocalLyric(self, text):
        _time = self.abs_time()
        assert _time >= 0

        if not self.useVocalTrack:
            return True

        if self.partnumber is None:
            return False

        for i, j in enumerate(self.song.parts):
            if self.partnumber == j:
                track = i

        self.song.track[track].allWords[_time] = text

    def addVocalStar(self, time):
        if time is None:
            time = self.abs_time()
        assert time >= 0

        if not self.useVocalTrack:
            return True

        track = [i for i, j in enumerate(self.song.parts) if self.partnumber == j][0]
        self.song.track[track].starTimes.append(time)

    def addTempoEvent(self, event, time=None):  # universal Tempo track handling
        if not isinstance(event, Tempo):
            return

        if time is None:
            time = self.abs_time()
        assert time >= 0

        # add tempo events to the universal tempo track
        self.song.tempoEventTrack.addEvent(time, event)
        if self.logTempoEvents == 1:
            log.debug("Tempo event added to Tempo track: " +
                      str(time) + " - " + str(event.bpm) + "BPM")

    def addSpecialMidiEvent(self, track, event, time=None):
        if self.partnumber == -1:
            # Looks like notes have started appearing before any part information.
            # Lets assume its part0
            self.partnumber = self.song.parts[0]

        if self.partnumber is None and isinstance(event, MarkerNote):
            return True

        if time is None:
            time = self.abs_time()
        assert time >= 0

        if track is None:
            for t in self.song.midiEventTracks:
                for s in t:
                    s.addEvent(time, event)
        else:

            tracklist = [i for i, j in enumerate(self.song.parts) if self.partnumber == j]
            for i in tracklist:
                # Each track needs it's own copy of the event, otherwise they'll interfere
                eventcopy = copy.deepcopy(event)
                if track < len(self.song.midiEventTracks[i]):
                    self.song.midiEventTracks[i][track].addEvent(time, eventcopy)

    def abs_time(self):
        def ticksToBeats(ticks, bpm):
            return (60000.0 * ticks) / (bpm * self.ticksPerBeat)

        if self.song.bpm:
            currentTime = midi.MidiOutStream.abs_time(self)

            scaledTime = 0.0
            tempoMarkerTime = 0.0
            currentBpm = self.song.bpm
            for i, marker in enumerate(self.tempoMarkers):
                _time, bpm = marker
                if _time > currentTime:
                    break
                scaledTime += ticksToBeats(_time - tempoMarkerTime, currentBpm)
                tempoMarkerTime, currentBpm = _time, bpm
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
        self.addTempoEvent(Tempo(bpm))

    def sequence_name(self, text):
        self.partnumber = None

        for part in self.song.parts:
            if text in part.trackName:
                if part.id == VOCAL_PART:
                    self.vocalTrack = True
                    self.useVocalTrack = True
                self.partnumber = part
                break  # should only have one instance of an instrument

        if self.logSections:
            if self.partnumber:
                log.debug("Found sequence_name in MIDI: %s, recognized as %s" %
                          (text, self.partnumber))
            else:
                log.debug("Found sequence_name in MIDI: %s, unrecognized and skipped" % text)

        if self.partnumber:
            if text in parts[VOCAL_PART].trackName and parts[VOCAL_PART] not in self.song.parts:
                self.useVocalTrack = False

            self.guitarSoloIndex = 0
            self.guitarSoloActive = False

    def note_on(self, channel, note, velocity):
        if self.partnumber is None:
            return
        self.velocity[note] = velocity
        self.heldNotes[(self.get_current_track(), channel, note)] = self.abs_time()

    def note_off(self, channel, note, velocity):
        if self.partnumber is None:
            return
        try:
            startTime = self.heldNotes[(self.get_current_track(), channel, note)]
            endTime = self.abs_time()
            del self.heldNotes[(self.get_current_track(), channel, note)]
            if self.vocalTrack:
                if note > 39 and note < 84:
                    self.addVocalEvent(VocalNote(note, endTime - startTime), time=startTime)
                elif note == 96:  # tambourine
                    self.addVocalEvent(VocalNote(note, 1, True), time=startTime)
                elif note == 105 or note == 106:
                    if startTime not in self.vocalOverlapCheck:
                        self.addVocalEvent(VocalPhrase(endTime - startTime), time=startTime)
                        self.vocalOverlapCheck.append(startTime)
                elif note == OD_MARKING_NOTE:
                    self.addVocalStar(startTime)
                return
            if note in NOTE_MAP:
                track, number = NOTE_MAP[note]
                self.addEvent(track, Note(number, endTime - startTime,
                                          special=self.velocity[note] == 127), time=startTime)

            # use self.midiEventTracks to store all the special MIDI marker notes, keep the clutter out of the main notes lists
            #  also -- to make use of marker notes in real-time, must add a new attribute to MarkerNote class "endMarker"
            # if this is == True, then the note is just an event to mark the end of
            # the previous note (which has length and is used in other ways)

            elif note == OD_MARKING_NOTE:
                self.song.hasStarpowerPaths = True
                self.earlyHitWindowSize = EARLY_HIT_WINDOW_NONE

                for diff in difficulties:
                    self.addSpecialMidiEvent(diff, MarkerNote(
                        note, endTime - startTime), time=startTime)
                    self.addSpecialMidiEvent(diff, MarkerNote(
                        note, 1, endMarker=True), time=endTime + 1)  # ending marker note
                    if self.logMarkerNotes == 1:
                        log.debug("RB Overdrive MarkerNote at %f added to part: %s and difficulty: %s" % (
                            startTime, self.partnumber, difficulties[diff]))

            elif note == SP_MARKING_NOTE:
                self.song.hasStarpowerPaths = True
                for diff in difficulties:
                    self.addSpecialMidiEvent(diff, MarkerNote(
                        note, endTime - startTime), time=startTime)
                    self.addSpecialMidiEvent(diff, MarkerNote(
                        note, 1, endMarker=True), time=endTime + 1)  # ending marker note
                    if self.logMarkerNotes == 1:
                        log.debug("GH Starpower (or RB Solo) MarkerNote at %f added to part: %s and difficulty: %s" % (
                            startTime, self.partnumber, difficulties[diff]))

            elif note == FREESTYLE_MARKING_NOTE:  # for drum fills and big rock endings
                self.song.hasFreestyleMarkings = True
                for diff in difficulties:
                    self.addSpecialMidiEvent(diff, MarkerNote(
                        note, endTime - startTime), time=startTime)
                    if self.logMarkerNotes == 1:
                        log.debug("RB freestyle section (drum fill or BRE) at %f added to part: %s and difficulty: %s" % (
                            startTime, self.partnumber, difficulties[diff]))
            else:
                pass
        except KeyError:
            log.warning("MIDI note 0x%x on channel %d ending at %d was never started." %
                        (note, channel, self.abs_time()))

    # OK - this needs to be optimized.
    # There should be a separate "Sections" track, and a separate "Lyrics" track created for their respective events
    # Then another separate "Text Events" track to put all the unused events,
    # so they don't bog down the game when it looks through / filters / sorts
    # these track event lists

    # adding MIDI text event access
    # these events happen on their own track, and are processed after the note tracks.
    # just mark the guitar solo sections ahead of time
    # and then write an iteration routine to go through whatever track / difficulty is being played in GuitarScene
    # to find these markers and count the notes and add a new text event
    # containing each solo's note count
    def text(self, text):
        if text.find("GNMIDI") < 0:  # to filter out the midi class illegal usage / trial timeout messages
            # if sequence name is PART VOCALS then look for text event lyrics
            if self.vocalTrack:
                if text.find("[") < 0:  # not a marker
                    event = TextEvent(text, 400.0)
                    self.addVocalLyric(text)
                    self.song.hasMidiLyrics = True
                    # add an event to the lyrics track
                    self.song.eventTracks[TK_LYRICS].addEvent(self.abs_time(), event)

            else:

                unusedEvent = None
                event = None
                gSoloEvent = False
                # also convert all underscores to spaces so it look better
                text = text.replace("_", " ")
                if text.lower().find("section") >= 0:
                    self.guitarSoloSectionMarkers = True  # GH1 dont use section markers... GH2+ do
                    # strip unnecessary text / chars:
                    text = text.replace("section", "")
                    text = text.replace("[", "")
                    text = text.replace("]", "")
                    # also convert "gtr" to "Guitar"
                    text = text.replace("gtr", "Guitar")
                    event = TextEvent(text, 250.0)
                    if text.lower().find("big rock ending") >= 0:
                        curTime = self.abs_time()
                        log.debug("Big Rock Ending section event marker found at " + str(curTime))
                        self.song.breMarkerTime = curTime

                    if text.lower().find("solo") >= 0 and text.lower().find("drum") < 0 and text.lower().find("outro") < 0 and text.lower().find("organ") < 0 and text.lower().find("synth") < 0 and text.lower().find("bass") < 0 and text.lower().find("harmonica") < 0:
                        gSoloEvent = True
                        gSolo = True
                    # Foreplay Long Time "[section_gtr_lead_1]"
                    elif text.lower().find("guitar") >= 0 and text.lower().find("lead") >= 0:
                        gSoloEvent = True
                        gSolo = True
                    elif text.lower().find("guitar") >= 0 and text.lower().find("line") >= 0:  # support for REM Orange Crush style solos
                        gSoloEvent = True
                        gSolo = True
                    # support for Pleasure solos "[section gtr_ostinato]"
                    elif text.lower().find("guitar") >= 0 and text.lower().find("ostinato") >= 0:
                        gSoloEvent = True
                        gSolo = True
                    else:  # this is the cue to end solos...
                        gSoloEvent = True
                        gSolo = False
                elif text.lower().find("solo") >= 0 and text.find("[") < 0 and text.lower().find("drum") < 0 and text.lower().find("map") < 0 and text.lower().find("play") < 0 and not self.guitarSoloSectionMarkers:
                    event = TextEvent(text, 250.0)
                    gSoloEvent = True
                    if text.lower().find("off") >= 0:
                        gSolo = False
                    else:
                        gSolo = True
                # this is an alternate GH1-style solo end marker
                elif (text.lower().find("verse") >= 0 or text.lower().find("chorus") >= 0) and text.find("[") < 0 and not self.guitarSoloSectionMarkers:
                    event = TextEvent(text, 250.0)
                    gSoloEvent = True
                    gSolo = False
                # this is an alternate GH1-style solo end marker
                elif text.lower().find("gtr") >= 0 and text.lower().find("off") >= 0 and text.find("[") < 0 and not self.guitarSoloSectionMarkers:
                    # also convert "gtr" to "Guitar"
                    text = text.replace("gtr", "Guitar")
                    event = TextEvent(text, 100.0)
                    gSoloEvent = True
                    gSolo = False
                else:  # unused text event
                    unusedEvent = TextEvent(text, 100.0)
                # now, check for guitar solo status change:
                if gSoloEvent:
                    if gSolo:
                        if not self.guitarSoloActive:
                            self.guitarSoloActive = True
                            soloEvent = TextEvent("GSOLO ON", 250.0)
                            log.debug("GSOLO ON event " + event.text +
                                      " found at time " + str(self.abs_time()))
                            # add an event to the guitar solos track
                            self.song.eventTracks[TK_GUITAR_SOLOS].addEvent(
                                self.abs_time(), soloEvent)
                    else:  # this is the cue to end solos...
                        if self.guitarSoloActive:
                            # here, check to make sure we're not ending a guitar solo that has
                            # just started!!
                            curTime = self.abs_time()
                            if self.song.eventTracks[TK_GUITAR_SOLOS][-1][0] < curTime:
                                self.guitarSoloActive = False
                                soloEvent = TextEvent("GSOLO OFF", 250.0)
                                log.debug("GSOLO OFF event " + event.text +
                                          " found at time " + str(curTime))
                                self.guitarSoloIndex += 1
                                # add an event to the guitar solos track
                                self.song.eventTracks[TK_GUITAR_SOLOS].addEvent(curTime, soloEvent)

                if event:
                    curTime = self.abs_time()
                    if len(self.song.eventTracks[TK_SECTIONS]) <= 1:
                        # add an event to the sections track
                        self.song.eventTracks[TK_SECTIONS].addEvent(curTime, event)
                    elif len(self.song.eventTracks[TK_SECTIONS]) > 1:  # ensure it exists first
                        # ensure we're not adding two consecutive sections to the same location!
                        if self.song.eventTracks[TK_SECTIONS][-1][0] < curTime:
                            # add an event to the sections track
                            self.song.eventTracks[TK_SECTIONS].addEvent(curTime, event)
                elif unusedEvent:
                    # add an event to the unused text track
                    self.song.eventTracks[TK_UNUSED_TEXT].addEvent(self.abs_time(), unusedEvent)

    def lyric(self, text):
        """ Adding MIDI lyric event access """
        if text.find("GNMIDI") < 0:  # to filter out the midi class illegal usage / trial timeout messages
            event = TextEvent(text, 400.0)
            self.addVocalLyric(text)
            self.song.hasMidiLyrics = True
            # add an event to the lyrics track
            self.song.eventTracks[TK_LYRICS].addEvent(self.abs_time(), event)


class MidiSectionReader(midi.MidiOutStream):
    # We exit via this exception so that we don't need to read the whole file in
    class Done(object):
        pass

    def __init__(self):
        midi.MidiOutStream.__init__(self)
        self.difficulties = []

        log.debug("MidiSectionReader class init (song.py)...")
        self.logSections = Config.get("game", "log_sections")

        # practice section support
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

            scaledTime = 0.0
            tempoMarkerTime = 0.0
            currentBpm = self.bpm
            for i, marker in enumerate(self.tempoMarkers):
                _time, bpm = marker
                if _time > currentTime:
                    break
                scaledTime += ticksToBeats(_time - tempoMarkerTime, currentBpm)
                tempoMarkerTime, currentBpm = _time, bpm
            return scaledTime + ticksToBeats(currentTime - tempoMarkerTime, currentBpm)
        return 0.0

    def tempo(self, value):
        self.bpm = 60.0 * 10.0**6 / value
        self.tempoMarkers.append((midi.MidiOutStream.abs_time(self), self.bpm))

    def note_on(self, channel, note, velocity):
        pos = float(midi.MidiOutStream.abs_time(self))
        if (pos / 60000) >= self.nextSectionMinute:
            text = "%d:%02d -> " % (pos / 60000, (pos % 60000) / 1000) + \
                "Section " + str(round(self.nextSectionMinute, 2))
            self.nextSectionMinute += 0.25

            # only log if enabled
            if self.logSections == 1:
                log.debug("Found potential default practice section: " + str(pos) + " - " + text)

            self.noteCountSections.append([text, pos])

    def lyric(self, text):
        """ Filter lyric events """
        if text.find("GNMIDI") < 0:  # to filter out the midi class illegal usage / trial timeout messages
            text = ""

    # adding text event / section retrieval here
    # also must prevent "Done" flag setting so can read whole MIDI file, all text events
    def text(self, text):
        if text.find("GNMIDI") < 0:  # to filter out the midi class illegal usage / trial timeout messages
            pos = self.abs_time()
            text = text.replace("_", " ")
            if text.lower().find("section") >= 0:
                if not self.guitarSoloSectionMarkers:
                    self.guitarSoloSectionMarkers = True  # GH1 dont use section markers... GH2+ do
                    self.sections = []  # reset sections
                # strip unnecessary text / chars:
                text = text.replace("section", "")
                text = text.replace("[", "")
                text = text.replace("]", "")
                # also convert "gtr" to "Guitar"
                text = text.replace("gtr", "Guitar")

                # only log if enabled
                if self.logSections == 1:
                    log.debug("Found <section> potential RB-style practice section: " + str(pos) + " - " + text)

                text = "%d:%02d -> " % (pos / 60000, (pos % 60000) / 1000) + text
                self.sections.append([text, pos])

            elif text.lower().find("solo") >= 0 and text.find("[") < 0 and text.lower().find("drum") < 0 and text.lower().find("map") < 0 and text.lower().find("play") < 0 and not self.guitarSoloSectionMarkers:

                # only log if enabled
                if self.logSections == 1:
                    log.debug("Found potential GH1-style practice section: " + str(pos) + " - " + text)

                text = "%d:%02d -> " % (pos / 60000, (pos % 60000) / 1000) + text
                self.sections.append([text, pos])
            # this is an alternate GH1-style solo end marker
            elif text.lower().find("verse") >= 0 and text.find("[") < 0 and not self.guitarSoloSectionMarkers:

                # only log if enabled
                if self.logSections == 1:
                    log.debug("Found potential GH1-style practice section: " + str(pos) + " - " + text)

                text = "%d:%02d -> " % (pos / 60000, (pos % 60000) / 1000) + text
                self.sections.append([text, pos])
            # this is an alternate GH1-style solo end marker
            elif text.lower().find("gtr") >= 0 and text.lower().find("off") >= 0 and text.find("[") < 0 and not self.guitarSoloSectionMarkers:
                # also convert "gtr" to "Guitar"
                text = text.replace("gtr", "Guitar")

                # only log if enabled
                if self.logSections == 1:
                    log.debug("Found potential GH1-style practice section: " + str(pos) + " - " + text)

                text = "%d:%02d -> " % (pos / 60000, (pos % 60000) / 1000) + text
                self.sections.append([text, pos])
            # General GH1-style sections.  Messy but effective.
            elif not self.guitarSoloSectionMarkers:

                # only log if enabled
                if self.logSections == 1:
                    log.debug("Found potential GH1-style practice section: " + str(pos) + " - " + text)

                text = "%d:%02d -> " % (pos / 60000, (pos % 60000) / 1000) + text
                self.sections.append([text, pos])

            else:  # unused text event
                text = ""


class SongQueue(object):
    """ Stores a list of songs to be played. """

    def __init__(self):
        self.songName = []
        self.library = []
        self.diffs = []
        self.parts = []
        self.totalSongName = []
        self.totalLibrary = []
        self.scores = []

        log.debug("SongQueue class init (song.py)...")

    def __len__(self):
        return len(self.songName)

    def isLastSong(self, songName, library):
        if len(self.songName) == 0 or len(self.library) == 0:
            return False
        if songName == self.songName[-1] and library == self.library[-1]:
            return True
        return False

    def addSong(self, songName, library):
        """ Add a song to the SongQueue """
        self.songName.append(songName)
        self.library.append(library)

    def addSongCheckReady(self, songName, library):
        """
        Check if a song should be added to the SongQueue. If the song is the same as the
        previous, assume the player intended to start the game instead.

        :param songName: folder name of song to be queued.
        :param library: path from the default library to the song's parent folder.
        :return: True if game is ready to start; False if song is added to queue.
        :rtype: bool
        """
        if self.isLastSong(songName, library):
            return True
        else:
            self.addSong(songName, library)
            return False

    def setFullQueue(self):
        self.totalSongName = self.songName[:]
        self.totalLibrary = self.library[:]

    def replayFullQueue(self):
        self.songName = self.totalSongName[:]
        self.library = self.totalLibrary[:]
        self.scores = []

    def getSong(self):
        if len(self.songName) == 0 or len(self.library) == 0:
            log.warning("SongQueue.getSong: Empty queue get.")
            return False
        song = self.songName.pop(0)
        library = self.library.pop(0)
        return song, library

    def getRandomSong(self):
        if len(self.songName) == 0 or len(self.library) == 0:
            log.warning("SongQueue.getRandomSong: Empty queue get.")
            return False
        n = random.randint(0, len(self.songName) - 1)
        song = self.songName.pop(n)
        library = self.library.pop(n)
        return song, library

    def getParts(self):
        return self.parts

    def getDiffs(self):
        return self.diffs

    def addScores(self, scores):
        self.scores.append(scores)

    def reset(self):
        self.totalSongName = []
        self.totalLibrary = []
        self.songName = []
        self.library = []
        self.diffs = []
        self.parts = []
        self.scores = []


class MidiPartsDiffReader(midi.MidiOutStream):
    """ Partially parse a MIDI file for the parts & difficulty.
    To fully load the file, see MidiReader above.
    """

    def __init__(self, forceGuitar=False):
        midi.MidiOutStream.__init__(self)
        self.parts = []
        self.difficulties = {}
        self.currentPart = -1
        self.nextPart = 0
        self.forceGuitar = forceGuitar
        self.firstTrack = False
        self.notesFound = [0, 0, 0, 0]
        self._drumFound = False
        self._ODNoteFound = False
        self._SPNoteFound = False

        self.logSections = Config.get("game", "log_sections")
        log.debug("MidiPartsDiffReader class init (song.py)...")

    def getMidiStyle(self):
        if self._ODNoteFound:
            log.debug("MIDI Type identified as RB")
            return MIDI_TYPE_RB
        elif self._drumFound and self._SPNoteFound:
            log.debug("MIDI Type identified as WT")
            return MIDI_TYPE_WT
        else:
            log.debug("MIDI Type identified as GH")
            return MIDI_TYPE_GH
    midiStyle = property(getMidiStyle)

    def start_of_track(self, n_track=0):
        if self.forceGuitar:
            if not self.firstTrack:
                if parts[GUITAR_PART] not in self.parts:
                    part = parts[GUITAR_PART]
                    self.parts.append(part)
                    self.nextPart = None
                    self.currentPart = part.id
                    self.notesFound = [0, 0, 0, 0]
                    self.difficulties[part.id] = []
                    if self.logSections == 1:
                        tempText = "No recognized tracks found. Using first track, and identifying it as "
                        tempText2 = "GUITAR_PART"
                        log.debug(tempText + tempText2)
                self.firstTrack = True
            else:
                log.info("This song has multiple tracks, none properly named. Behavior may be erratic.")

    def sequence_name(self, text):
        """ Track name encountered in file, see if we can match it to an instrument part. """

        if self.logSections == 1:
            tempText = "MIDI sequence_name found: " + text + ", recognized and added to list as "
            tempText2 = ""

        for part in parts.values():
            if text in part.trackName:
                if part not in self.parts:
                    if part.id == VOCAL_PART:
                        self.parts.append(part)
                        self.nextPart = None
                        self.currentPart = part.id
                        self.difficulties[part.id] = difficulties.values()
                    else:
                        self.nextPart = part
                        self.currentPart = self.nextPart.id
                        self.notesFound = [0, 0, 0, 0]
                        if part.id == DRUM_PART or part.id == PRO_DRUM_PART:
                            self._drumFound = True
                    if self.logSections == 1:
                        tempText2 = part.trackName[0].replace(" ", "_")
                        log.debug(tempText + tempText2)
                    return
        self.currentPart = -1

    def addPart(self):
        self.parts.append(self.nextPart)
        self.difficulties[self.nextPart.id] = []
        self.nextPart = None

    def note_on(self, channel, note, velocity):
        """ Note found, register its difficulty. """

        if self.currentPart == -1:
            return
        if note == OD_MARKING_NOTE:
            self._ODNoteFound = True
        elif note == SP_MARKING_NOTE:
            self._SPNoteFound = True
        try:
            try:
                # shortcut if we've already found all difficulty levels
                if len(self.difficulties[self.currentPart]) == len(difficulties):
                    return
            except KeyError:
                pass
            diff, button = NOTE_MAP[note]
            self.notesFound[diff] += 1
            if self.notesFound[diff] > 5:
                if self.nextPart is not None:
                    self.addPart()
                diffObj = difficulties[diff]
                if diffObj not in self.difficulties[self.currentPart]:
                    self.difficulties[self.currentPart].append(diffObj)
        except KeyError:
            pass


def loadSong(engine, name, library=DEFAULT_LIBRARY, playbackOnly=False, notesOnly=False, part=[parts[GUITAR_PART]], practiceMode=False, practiceSpeed=.5):

    log.debug("loadSong function call (song.py)...")
    crowdsEnabled = engine.config.get("audio", "enable_crowd_tracks")
    slowDownFactor = engine.config.get("audio", "speed_factor")

    songFiles = {}
    noteFile = None
    infoFile = engine.resource.fileName(library, name, "song.ini", writable=True)
    scriptFile = engine.resource.fileName(library, name, "script.txt")

    if not notesOnly:
        # work around for glob and fnmatch not having a way to excape characters
        # such as [ ] in filepaths... wtf glob! Python 3.3 added glob.escape to
        # escape all characters that cause the problem. For now the change dir
        # method is a cleaner work around than reimpplementing that function here.
        orgpath = os.path.abspath('.')
        os.chdir(engine.resource.fileName(library, name))
        songOggFiles = glob.glob('*.ogg')

        os.chdir(orgpath)

        # All song file entries are going to be lists because there is a possibilty
        # for the drums of having multiple tracks. This will make things simpler.
        for f in songOggFiles:
            instName = f.split('.')[0].lower()

            # Check for numbered audio tracks
            isNumbered = re.compile(r'^.*_\d').match(instName)
            if isNumbered:
                # take the part of the name before the underscore for the name.
                instName = instName.split('_')[0]

            # get the number of additional tracks
            instReNumbered = re.compile(r'^{0}_\d'.format(instName))
            numCount = len([i for i in songOggFiles if instReNumbered.match(i)])

            # skip non numbered ogg files if there are others that are.
            if numCount > 0 and not isNumbered:
                continue

            if instName not in songFiles:
                songFiles[instName] = []

            songFiles[instName].append(engine.resource.fileName(library, name, f))

        if 'song' not in songFiles:
            songFiles['song'] = songFiles['guitar']
            del songFiles['guitar']

        # check to see if the guitar and song ogg's are the same file, if so use only one.
        if 'song' in songFiles and 'guitar' in songFiles:

            with open(songFiles['song'][0], 'rb') as f:
                songHash = hashlib.sha1(f.read()).hexdigest()

            with open(songFiles['guitar'][0], 'rb') as f:
                guitarHash = hashlib.sha1(f.read()).hexdigest()

            if songHash == guitarHash:
                songFiles.pop('guitar', None)

        if crowdsEnabled == 0:
            songFiles.pop('crowd', None)

        if practiceMode:
            slowDownFactor = practiceSpeed
            partFile = songFiles['song']

            if (part[0] == parts[GUITAR_PART] or part[0] == parts[PRO_GUITAR_PART]) and 'guitar' in songFiles.keys():
                partFile = songFiles['guitar']
            elif part[0] == parts[BASS_PART] and 'rhythm' in songFiles.keys():
                partFile = songFiles['rhythm']
            elif (part[0] == parts[DRUM_PART] or part[0] == parts[PRO_DRUM_PART]) and 'drums' in songFiles.keys():
                partFile = songFiles['drums']

            songFiles = {'song': partFile}

        if playbackOnly:
            songFiles.pop('crowd', None)
            if 'preview' in songFiles.keys():
                pvFile = songFiles['preview']
                songFiles = {'song': pvFile}
        else:
            songFiles.pop('preview', None)

    if not playbackOnly:
        logUneditedMidis = engine.config.get("log", "log_unedited_midis")
        useUneditedMidis = engine.config.get("debug", "use_unedited_midis")
        if useUneditedMidis == 1:  # auto
            noteFile = engine.resource.fileName(library, name, "notes-unedited.mid", writable=True)
            if os.path.isfile(noteFile):
                if logUneditedMidis == 1:
                    log.debug("notes-unedited.mid found, using instead of notes.mid! - " + name)
            else:
                noteFile = engine.resource.fileName(library, name, "notes.mid", writable=True)
                if logUneditedMidis == 1:
                    log.debug("notes-unedited.mid not found, using notes.mid - " + name)
        else:
            noteFile = engine.resource.fileName(library, name, "notes.mid", writable=True)
            if logUneditedMidis == 1:
                log.debug("notes-unedited.mid not found, using notes.mid - " + name)

    engine.audioSpeedFactor = slowDownFactor

    song = Song(engine, infoFile, songFiles, noteFile, scriptFile, part)
    return song


def loadSongInfo(engine, name, library=DEFAULT_LIBRARY):
    # RF-mod (not needed?)
    infoFile = engine.resource.fileName(library, name, "song.ini", writable=True)
    return SongInfo(infoFile, library)


def getDefaultLibrary(engine):
    return LibraryInfo(DEFAULT_LIBRARY, engine.resource.fileName(DEFAULT_LIBRARY, "library.ini"))


def getAvailableLibraries(engine, library=DEFAULT_LIBRARY):
    """ Find libraries (i.e. sub-directories of songs) inside a directory.

    :param library: directory to search
    :return: list[LibraryInfo]
    """
    log.debug("Song.getAvailableLibraries function call...library = " + str(library))
    # Search for libraries in both the read-write and read-only directories
    songRoots = [engine.resource.fileName(library),
                 engine.resource.fileName(library, writable=True)]
    libraries = []
    libraryRoots = []

    for songRoot in set(songRoots):
        if not os.path.exists(songRoot):
            return libraries
        for libraryRoot in os.listdir(songRoot):
            if libraryRoot == ".git":
                # filter the git folder
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
            continue  # why were these here? we must filter out empty libraries
            # I'll tell you why -- so that empty ("tiered" / organizational)
            # folders are displayed, granting access to songs in subfolders...

            dirs = os.listdir(libraryRoot)
            for name in dirs:
                if os.path.isfile(os.path.join(libraryRoot, name, "song.ini")):
                    if libraryRoot not in libraryRoots:
                        libName = library + os.path.join(libraryRoot.replace(songRoot, ""))
                        libraries.append(LibraryInfo(
                            libName, os.path.join(libraryRoot, "library.ini")))
                        libraryRoots.append(libraryRoot)

    libraries.sort(key=lambda lib: lib.name.lower())

    return libraries


def getAvailableSongs(engine, library=DEFAULT_LIBRARY, includeTutorials=False, progressCallback=lambda p: None):
    order = engine.config.get("game", "sort_order")
    tut = engine.config.get("game", "tut")
    direction = engine.config.get("game", "sort_direction")
    if tut:
        includeTutorials = True

    # Career Mode determination
    gameMode1p = engine.world.gameMode
    careerMode = gameMode1p == 2

    # Search for songs in both the read-write and read-only directories
    if library is None:
        return []
    songRoots = [engine.resource.fileName(
        library), engine.resource.fileName(library, writable=True)]
    names = []
    for songRoot in songRoots:
        if not os.path.exists(songRoot):
            return []
        for name in os.listdir(songRoot):
            if not os.path.isfile(os.path.join(songRoot, name, "notes.mid")) and not os.path.isfile(os.path.join(songRoot, name, "notes-unedited.mid")):
                continue
            if not os.path.isfile(os.path.join(songRoot, name, "song.ini")) or name.startswith("."):
                continue
            if name not in names:
                names.append(name)
    songs = []
    for name in names:
        progressCallback(len(songs) / float(len(names)))
        songs.append(SongInfo(engine.resource.fileName(
            library, name, "song.ini", writable=True), library))
    if Config.get("performance", "cache_song_metadata"):
        _songDB.commit()
    if not includeTutorials:
        songs = [song for song in songs if not song.tutorial]
    songs = [song for song in songs if not song.artist == '=FOLDER=']
    # unlock system
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

    # sort songs
    if direction == 0:
        if order == 1:
            songs.sort(key=lambda k_song: k_song.artist.lower())
        elif order == 2:
            songs.sort(key=lambda k_song: int(k_song.count + str(0)), reverse=True)
        elif order == 0:
            songs.sort(key=lambda k_song: k_song.name.lower())
        elif order == 3:
            songs.sort(key=lambda k_song: k_song.album.lower())
        elif order == 4:
            songs.sort(key=lambda k_song: k_song.genre.lower())
        elif order == 5:
            songs.sort(key=lambda k_song: k_song.year.lower())
        elif order == 6:
            songs.sort(key=lambda k_song: k_song.diffSong)
        elif order == 7:
            songs.sort(key=lambda k_song: theInstrumentDiff(k_song))
        elif order == 8:
            songs.sort(key=lambda k_song: k_song.icon.lower())
    else:
        if order == 1:
            songs.sort(key=lambda k_song: k_song.artist.lower(), reverse=True)
        elif order == 2:
            songs.sort(key=lambda k_song: int(k_song.count + str(0)))
        elif order == 0:
            songs.sort(key=lambda k_song: k_song.name.lower(), reverse=True)
        elif order == 3:
            songs.sort(key=lambda k_song: k_song.album.lower(), reverse=True)
        elif order == 4:
            songs.sort(key=lambda k_song: k_song.genre.lower(), reverse=True)
        elif order == 5:
            songs.sort(key=lambda k_song: k_song.year.lower(), reverse=True)
        elif order == 6:
            songs.sort(key=lambda k_song: k_song.diffSong, reverse=True)
        elif order == 7:
            songs.sort(key=lambda k_song: theInstrumentDiff(k_song), reverse=True)
        elif order == 8:
            songs.sort(key=lambda k_song: k_song.icon.lower(), reverse=True)

    return songs


def getSortingTitles(engine, songList=[]):
    sortOrder = engine.config.get("game", "sort_order")
    titles = []
    sortTitles = []

    instrument = engine.config.get("game", "songlist_instrument")
    theInstrumentDiff = instrumentDiff[instrument]

    for songItem in songList:
        if sortOrder == 1:
            try:
                titles.index(songItem.artist.lower())
            except ValueError:
                titles.append(songItem.artist.lower())
                sortTitles.append(SortTitleInfo(songItem.artist))
        elif sortOrder == 0:
            name = removeSongOrderPrefixFromName(songItem.name)
            if name[0].isdigit():
                sortName = "123"
            elif not name[0].isalnum():
                sortName = "!@#"
            else:
                sortName = name[0].lower()
            try:
                titles.index(sortName)
            except ValueError:
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


def getAvailableTitles(engine, library=DEFAULT_LIBRARY):
    """ Get available titles / sections for an album """
    gameMode1p = engine.world.gameMode
    if library is None:
        return []

    # get the titles.ini file from the library path
    path = os.path.join(engine.resource.fileName(library, writable=True), "titles.ini")
    if not os.path.isfile(path):
        return []

    # get sections from the config file
    config = Config.MyConfigParser()
    titles = []
    try:
        config.read(path)
        sections = config.get("titles", "sections")

        # add a TitleInfo object for each section
        for section in sections.split():
            titles.append(TitleInfo(config, section))

        # add a BlankSpaceInfo object at the end for career mode
        if gameMode1p == 2:
            titles.append(BlankSpaceInfo(_("End of Career")))

    except Exception:
        log.warning("titles.ini could not be read (song.py)")
        return []

    return titles


def getAvailableSongsAndTitles(engine, library=DEFAULT_LIBRARY, includeTutorials=False, progressCallback=lambda p: None):

    # NOTE: list-all mode and career modes are BROKEN as of now
    if library is None:
        return []

    # Career Mode determination
    careerMode = (engine.world.gameMode == 2)
    quickPlayCareerTiers = engine.config.get("game", "quickplay_tiers")

    # get avalaible songs
    items = getAvailableSongs(engine, library, includeTutorials, progressCallback=progressCallback)

    # get titles
    titles = []
    if quickPlayCareerTiers == 1 or careerMode:
        titles = getAvailableTitles(engine, library)
    if titles == []:
        titles = getSortingTitles(engine, items)
    else:
        # sort songs per unlock id
        items.sort(key=lambda item: item.getUnlockID())

    # sort songs per titles (title, song, song, title, song, song, blank)
    all_items = sort_songs_per_title(items, titles)

    # random mode
    if (not careerMode) and len(all_items) != 0:
        all_items.insert(0, RandomSongInfo())

    return all_items


def sort_songs_per_title(songs, titles):
    """ Group songs by (unlock) title and put titles before each song group """
    items = list()

    # first title
    i = 0
    title = titles[i]
    items.append(title)

    # next titles and songs
    for song in songs:
        # comparison: unlock_id or name
        if isinstance(title, TitleInfo):
            # the unlock category
            compare = title.getUnlockID() not in song.getUnlockID()
        elif isinstance(title, SortTitleInfo):
            # SortTitleInfo contains the first letter of songs
            compare = title.name.lower() != song.name[0].lower()
        else:
            compare = False

        # insert the title if the slot is complete
        if compare:
            i += 1
            if i < len(titles):
                title = titles[i]
                items.append(title)
        # insert the song
        items.append(song)

    # insert the blank title if needed
    if titles[-1] not in items:
        items.append(titles[-1])

    return items


def removeSongOrderPrefixFromName(name):
    return re.sub(r'^[0-9]+\. *', '', name)


def updateSongDatabase(engine):
    # putting it at the top causes circular-import-related problems...
    from fofix.game import Dialogs
    log.debug('Updating song cache.')
    _songDB.execute('UPDATE `songinfo` SET `seen` = 0')
    # one-element list to avoid having to throw this into the global namespace
    # for updatePhase's sake
    lastScreenUpdateTime = [time.time()]
    loadingScreen = Dialogs.showLoadingSplashScreen(engine, _('Checking song database...'))

    def updatePhase(text):
        if time.time() - lastScreenUpdateTime[0] > 0.25:
            Dialogs.changeLoadingSplashScreenText(engine, loadingScreen, _(
                'Checking song database...') + ' \n ' + text)
            lastScreenUpdateTime[0] = time.time()

    # use some array-indexing trickery so we don't have to do this recursively
    i = 0
    folders = [getDefaultLibrary(engine)]
    while i < len(folders):
        updatePhase(_('Enumerating song folders... (%d so far)') % len(folders))
        folders.extend(getAvailableLibraries(engine, folders[i].libraryName))
        i += 1
    for i, folder in enumerate(folders):
        getAvailableSongs(engine, folder.libraryName, progressCallback=lambda p: updatePhase('%s \n %s \n %s' % (
            _('Caching song data...'), folder.libraryName, (_('(folder %d of %d; %d%% of this folder)') % (i + 1, len(folders), (p * 100))))))
    updatePhase(_('Pruning leftover entries...'))
    prunecount = _songDB.execute('DELETE FROM `songinfo` WHERE `seen` = 0').rowcount
    if prunecount != 0:
        _songDB.execute('VACUUM')
        log.debug('Pruned %d cache entries.' % prunecount)
    _songDB.commit()
    Dialogs.hideLoadingSplashScreen(engine, loadingScreen)
