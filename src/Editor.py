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
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import colorsys

from View import Layer
from Input import KeyListener
from Song import loadSong, createSong, Note, difficulties, DEFAULT_LIBRARY
from Guitar import Guitar, PLAYER1KEYS, PLAYER2KEYS
from Camera import Camera
from Menu import Menu, Choice
from Language import _
import MainMenu
import Dialogs
import Player
import Theme
import Log
import shutil, os, struct, wave, tempfile
from struct import unpack

KEYS = PLAYER1KEYS

class Editor(Layer, KeyListener):
  """Song editor layer."""
  def __init__(self, engine, songName = None, libraryName = DEFAULT_LIBRARY):
    self.engine      = engine
    self.time        = 0.0
    self.guitar      = Guitar(self.engine, editorMode = True)
    self.controls    = Player.Controls()
    self.camera      = Camera()
    self.pos         = 0.0
    self.snapPos     = 0.0
    self.scrollPos   = 0.0
    self.scrollSpeed = 0.0
    self.newNotes    = None
    self.newNotePos  = 0.0
    self.song        = None
    self.engine.loadSvgDrawing(self, "background", "editor.svg")
    self.modified    = False
    self.songName    = songName
    self.libraryName = libraryName
    self.heldFrets   = set()

    self.spinnyDisabled   = self.engine.config.get("game", "disable_spinny")    

    mainMenu = [
      (_("Save Song"),                  self.save),
      (_("Set Song Name"),              self.setSongName),
      (_("Set Artist Name"),            self.setArtistName),
      (_("Set Beats per Minute"),       self.setBpm),
      (_("Estimate Beats per Minute"),  self.estimateBpm),
      (_("Set A/V delay"),              self.setAVDelay),
      (_("Set Cassette Color"),         self.setCassetteColor),
      (_("Set Cassette Label"),         self.setCassetteLabel),
      (_("Editing Help"),               self.help),
      (_("Quit to Main Menu"),          self.quit),
    ]
    self.menu = Menu(self.engine, mainMenu)

  def save(self):
    if not self.modified:
      Dialogs.showMessage(self.engine, _("There are no changes to save."))
      return

    def save():
      self.song.save()
      self.modified = False

    self.engine.resource.load(function = save)
    Dialogs.showLoadingScreen(self.engine, lambda: not self.modified, text = _("Saving..."))
    Dialogs.showMessage(self.engine, _("'%s' saved.") % self.song.info.name)

  def help(self):
    Dialogs.showMessage(self.engine, _("Editing keys: ") +
                                     _("Arrows - Move cursor, ") +
                                     _("Space - Play/pause song, ") +
                                     _("Enter - Make note (hold and move for long notes), ") +
                                     _("Delete - Delete note, ") +
                                     _("Page Up/Down - Change difficulty"))


  def setSongName(self):
    name = Dialogs.getText(self.engine, _("Enter Song Name"), self.song.info.name)
    if name:
      self.song.info.name = name
      self.modified = True

  def setArtistName(self):
    name = Dialogs.getText(self.engine, _("Enter Artist Name"), self.song.info.artist)
    if name:
      self.song.info.artist = name
      self.modified = True

  def setAVDelay(self):
    delay = Dialogs.getText(self.engine, _("Enter A/V delay in milliseconds"), unicode(self.song.info.delay))
    if delay:
      try:
        self.song.info.delay = int(delay)
        self.modified = True
      except ValueError:
        Dialogs.showMessage(self.engine, _("That isn't a number."))

  def setBpm(self):
    bpm = Dialogs.getText(self.engine, _("Enter Beats per Minute Value"), unicode(self.song.bpm))
    if bpm:
      try:
        self.song.setBpm(float(bpm))
        self.modified = True
      except ValueError:
        Dialogs.showMessage(self.engine, _("That isn't a number."))

  def estimateBpm(self):
    bpm = Dialogs.estimateBpm(self.engine, self.song, _("Tap the Space bar to the beat of the song. Press Enter when done or Escape to cancel."))
    if bpm is not None:
      self.song.setBpm(bpm)
      self.modified = True

  def setCassetteColor(self):
    if self.song.info.cassetteColor:
      color = Theme.colorToHex(self.song.info.cassetteColor)
    else:
      color = ""
    color = Dialogs.getText(self.engine, _("Enter cassette color in HTML (#RRGGBB) format."), color)
    if color:
      try:
        self.song.info.setCassetteColor(Theme.hexToColor(color))
        self.modified = True
      except ValueError:
        Dialogs.showMessage(self.engine, _("That isn't a color."))

  def setCassetteLabel(self):
    label = Dialogs.chooseFile(self.engine, masks = ["*.png"], prompt = _("Choose a 256x128 PNG format label image."))
    if label:
      songPath = self.engine.resource.fileName("songs", self.songName, writable = True)
      shutil.copyfile(label, os.path.join(songPath, "label.png"))
      self.modified = True

  def shown(self):
    self.engine.input.addKeyListener(self)

    if not self.songName:
      self.libraryName, self.songName = Dialogs.chooseSong(self.engine)

    if not self.songName:
      self.engine.view.popLayer(self)
      return

    self.engine.resource.load(self, "song", lambda: loadSong(self.engine, self.songName, seekable = True, library = self.libraryName))
    Dialogs.showLoadingScreen(self.engine, lambda: self.song, text = _("Loading song..."))

  def hidden(self):
    if self.song:
      self.song.stop()
    self.engine.input.removeKeyListener(self)
    #self.engine.view.pushLayer(MainMenu.MainMenu(self.engine))
    self.engine.view.pushLayer(self.engine.mainMenu)    #rchiav: use already-existing MainMenu instance

  def controlPressed(self, control):
    if not self.song:
      return

    if control in Player.UPS:
      self.guitar.selectPreviousString()
    elif control in Player.DOWNS:
      self.guitar.selectNextString()
    elif control in Player.LEFTS:
      self.pos = self.snapPos - self.song.period / 4
    elif control in Player.RIGHTS:
      self.pos = self.snapPos + self.song.period / 4
    elif control in KEYS:
      self.heldFrets.add(KEYS.index(control))
    elif control in Player.ACTION1S + Player.ACTION2S:
      self.newNotePos = self.snapPos
      # Add notes for the frets that are held down or for the selected string.
      if self.heldFrets:
        self.newNotes = [Note(f, self.song.period / 4) for f in self.heldFrets]
      else:
        self.newNotes = [Note(self.guitar.selectedString, self.song.period / 4)]
      self.modified   = True

  def controlReleased(self, control):
    if not self.song:
      return

    if control in Player.ACTION1S + Player.ACTION2S and self.newNotes and not self.heldFrets:
      self.newNotes = []
    elif control in KEYS:
      self.heldFrets.remove(KEYS.index(control))
      if not self.heldFrets and self.newNotes:
        self.newNotes = []

  def quit(self):
    self.engine.view.popLayer(self)
    self.engine.view.popLayer(self.menu)

  def keyPressed(self, key, unicode):
    c = self.engine.input.controls.getMapping(key)
    if c in Player.CANCELS:
      self.engine.view.pushLayer(self.menu)
    elif key == pygame.K_PAGEDOWN and self.song:
      d = self.song.difficulty[0]
      v = difficulties.values()
      self.song.difficulty[0] = v[(v.index(d) + 1) % len(v)]
    elif key == pygame.K_PAGEUP and self.song:
      d = self.song.difficulty[0]
      v = difficulties.values()
      self.song.difficulty[0] = v[(v.index(d) - 1) % len(v)]
    elif key == pygame.K_DELETE and self.song:
      # gather up all events that intersect the cursor and delete the ones on the selected string
      t1 = self.snapPos
      t2 = self.snapPos + self.song.period / 4
      e  = [(time, event) for time, event in self.song.track[0].getEvents(t1, t2) if isinstance(event, Note)]
      for time, event in e:
        if event.number == self.guitar.selectedString:
          self.song.track[0].removeEvent(time, event)
          self.modified = True
    elif key == pygame.K_SPACE and self.song:
      if self.song.isPlaying():
        self.song.stop()
      else:
        self.song.play(start = self.pos)
    c = self.controls.keyPressed(key)
    if c:
      self.controlPressed(c)
    return True

  def keyReleased(self, key):
    c = self.controls.keyReleased(key)
    if c:
      self.controlReleased(c)
    return True

  def run(self, ticks):
    self.time += ticks / 50.0

    if not self.song:
      return

    self.guitar.run(ticks, self.scrollPos, self.controls)

    if not self.song.isPlaying():
      if (self.controls.getState(Player.RIGHT) or self.controls.getState(Player.PLAYER_2_RIGHT)) and not (self.controls.getState(Player.LEFT) or self.controls.getState(Player.PLAYER_2_LEFT)):
        self.pos += self.song.period * self.scrollSpeed
        self.scrollSpeed += ticks / 4096.0
      elif (self.controls.getState(Player.LEFT) or self.controls.getState(Player.PLAYER_2_LEFT)) and not (self.controls.getState(Player.RIGHT) or self.controls.getState(Player.PLAYER_2_RIGHT)):
        self.pos -= self.song.period * self.scrollSpeed
        self.scrollSpeed += ticks / 4096.0
      else:
        self.scrollSpeed = 0
    else:
      self.pos = self.song.getPosition()

    self.pos = max(0, self.pos)

    quarterBeat = int(self.pos / (self.song.period / 4) + .5)
    self.snapPos = quarterBeat * (self.song.period / 4)

    # note adding
    if self.newNotes:
      if self.snapPos < self.newNotePos:
        self.newNotes = []
      for note in self.newNotes:
        self.song.track[0].removeEvent(self.newNotePos, note)
        note.length = max(self.song.period / 4, self.snapPos - self.newNotePos)
        # remove all notes under the this new note
        oldNotes = [(time, event) for time, event in self.song.track[0].getEvents(self.newNotePos, self.newNotePos + note.length) if isinstance(event, Note)]
        for time, event in oldNotes:
          if event.number == note.number:
            self.song.track[0].removeEvent(time, event)
            if time < self.newNotePos:
              event.length = self.newNotePos - time
              self.song.track[0].addEvent(time, event)
        self.song.track[0].addEvent(self.newNotePos, note)

    if self.song.isPlaying():
      self.scrollPos = self.pos
    else:
      self.scrollPos = (self.scrollPos + self.snapPos) / 2.0

  def render(self, visibility, topMost):
    if not self.song:
      return

    v = 1.0 - ((1 - visibility) ** 2)

    # render the background
    t = self.time / 100 + 34
    w, h, = self.engine.view.geometry[2:4]
    r = .5

    if self.spinnyDisabled != True and Theme.spinnyEditorDisabled:    
      self.background.transform.reset()
      self.background.transform.translate(w / 2 + math.sin(t / 2) * w / 2 * r, h / 2 + math.cos(t) * h / 2 * r)
      self.background.transform.rotate(-t)
      self.background.transform.scale(math.sin(t / 8) + 2, math.sin(t / 8) + 2)
    self.background.draw()

    self.camera.target = ( 2, 0, 5.5)
    self.camera.origin = (-2, 9, 5.5)

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60, 4.0 / 3.0, 0.1, 1000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    self.camera.apply()
    self.guitar.render(v, self.song, self.scrollPos, self.controls)

    self.engine.view.setOrthogonalProjection(normalize = True)
    font = self.engine.data.font

    try:
      Theme.setSelectedColor()

      w, h = font.getStringSize(" ")

      if self.song.isPlaying():
        status = _("Playing")
      else:
        status = _("Stopped")

      t = "%d.%02d'%03d" % (self.pos / 60000, (self.pos % 60000) / 1000, self.pos % 1000)
      font.render(t, (.05, .05 - h / 2))
      font.render(status, (.05, .05 + h / 2))
      font.render(unicode(self.song.difficulty[0]), (.05, .05 + 3 * h / 2))

      Theme.setBaseColor()
      text = self.song.info.name + (self.modified and "*" or "")
      Dialogs.wrapText(font, (.5, .05 - h / 2), text)
    finally:
      self.engine.view.resetProjection()

class Importer(Layer):
  """
  Song importer.

  This importer needs two OGG tracks for the new song; one is the background track
  and the other is the guitar track. The importer will create a blank note and info files
  and copy the tracks under the data directory.
  """
  def __init__(self, engine):
    self.engine        = engine
    self.wizardStarted = False
    self.song          = None
    self.songName      = None

  def hidden(self):
    if self.songName:
      self.engine.view.pushLayer(Editor(self.engine, self.songName))
    else:
      self.engine.view.pushLayer(MainMenu.MainMenu(self.engine))

  def run(self, ticks):
    if self.wizardStarted:
      return
    self.wizardStarted = True

    name = ""
    while True:
      masks = ["*.ogg"]
      name  = Dialogs.getText(self.engine, prompt = _("Enter a name for the song."), text = name)

      if not name:
        self.engine.view.popLayer(self)
        return

      path = os.path.abspath(self.engine.resource.fileName("songs", name))
      if os.path.isdir(path):
        Dialogs.showMessage(self.engine, _("That song already exists."))
      else:
        break

    guitarTrack     = Dialogs.chooseFile(self.engine, masks = masks, prompt = _("Choose the Instrument Track (OGG format)."))

    if not guitarTrack:
      self.engine.view.popLayer(self)
      return

    backgroundTrack = Dialogs.chooseFile(self.engine, masks = masks, prompt = _("Choose the Background Track (OGG format) or press Escape to skip."))

    # Create the song
    loader = self.engine.resource.load(self, "song", lambda: createSong(self.engine, name, guitarTrack, backgroundTrack))
    Dialogs.showLoadingScreen(self.engine, lambda: self.song or loader.exception, text = _("Importing..."))

    if not loader.exception:
      self.songName = name
    self.engine.view.popLayer(self)

class ArkFile(object):
  """
  An interface to the ARK file format of Guitar Hero.

  The format of the archive and the index file was studied from
  Game Extractor by WATTO Studios.
  """
  def __init__(self, indexFileName, dataFileName):
    self.dataFileName = dataFileName

    # Read the available files from the index
    f = open(indexFileName, "rb")
    magic, version1, version2, arkSize, length = unpack("IIIII", f.read(5 * 4))

    Log.debug("Reading HDR file v%d.%d. Main archive is %d bytes." % (version1, version2, arkSize))

    # Read the name array
    fileNameData = f.read(length)
    fileNameCount, = unpack("I", f.read(4))
    fileNameOffsets = [unpack("I", f.read(4))[0] for i in range(fileNameCount)]

    # Read the pointers to the names
    names = []
    for i, offset in enumerate(fileNameOffsets):
      length = fileNameData[offset:].find("\x00")
      fileName = fileNameData[offset:offset + length]
      names.append(fileName)

    # Read the file names themselves
    fileCount, = unpack("I", f.read(4))

    self.files = {}
    for i in range(fileCount):
      offset, fileIndex, dirIndex, length, null = unpack("IIIII", f.read(5 * 4))
      fullName = "%s/%s" % (names[dirIndex], names[fileIndex])
      self.files[fullName] = offset, length
      Log.debug("File: %s at offset %d, length %d bytes." % (fullName, offset, length))
    Log.debug("Archive contains %d files." % len(self.files))
    f.close()

  def openFile(self, name, mode = "rb"):
    offset, length = self.files[name]
    f = open(self.dataFileName, mode)
    f.seek(offset)
    return f

  def fileLength(self, name):
    offset, length = self.files[name]
    return length

  def extractFile(self, name, outputFile):
    f = self.openFile(name)
    length = self.fileLength(name)

    if type(outputFile) == str:
      out = open(outputFile, "wb")
    else:
      out = outputFile

    while length > 0:
      data = f.read(4096)
      data = data[:min(length, len(data))]
      length -= len(data)
      out.write(data)
    f.close()

    if type(outputFile) == str:
      out.close()

class GHImporter(Layer):
  """
  Guitar Hero(tm) song importer.

  This importer takes the original Guitar Hero PS2 DVD and extracts the songs from it.
  Thanks to Sami Vaarala for the initial implementation!
  """
  def __init__(self, engine):
    self.engine        = engine
    self.wizardStarted = False
    self.done          = False
    self.songs         = None
    self.statusText    = ""
    self.stageInfoText = ""
    self.stageProgress = 0.0

  def hidden(self):
    self.engine.boostBackgroundThreads(False)
    self.engine.view.pushLayer(MainMenu.MainMenu(self.engine))

  def decodeVgsStreams(self, vgsFile, length):
    Log.notice("Decompressing %d byte VGS file." % (length))

    # This decompressor is based on VAG-Depack by bITmASTER
    f = vgsFile

    c = [[           0.0,          0.0 ],
         [   60.0 / 64.0,          0.0 ],
         [  115.0 / 64.0, -52.0 / 64.0 ],
         [   98.0 / 64.0, -55.0 / 64.0 ],
         [  122.0 / 64.0, -60.0 / 64.0 ],
         [           0.0,          0.0 ],
         [           0.0,          0.0 ],
         [           0.0,          0.0 ]]

    class StreamDecoder:
      """XA ADPCM decoder"""
      def __init__(self):
        self.s_1     = 0.0
        self.s_2     = 0.0
        self.samples = [0.0] * 28

      def decode(self, block, predict_nr, shift_factor):
        for i in range(0, 28, 2):
          d = block[i >> 1]
          s = (d & 0xf) << 12
          if s & 0x8000:
            s = (s & 0xffff) - 0x10000
          self.samples[i] = float(s >> shift_factor)
          s = (d & 0xf0) << 8
          if s & 0x8000:
            s = (s & 0xffff) - 0x10000
          self.samples[i + 1] = float(s >> shift_factor)

        for i in range(28):
          self.samples[i] += self.s_1 * c[predict_nr][0] + self.s_2 * c[predict_nr][1]
          self.s_2 = self.s_1
          self.s_1 = self.samples[i]

        return self.samples

    maxStreams = 8
    streams    = [StreamDecoder() for i in range(maxStreams)]

    def byte(d):
      if len(d):
        return struct.unpack("b", d)[0]
      return 0

    startPos = f.tell()

    while True:
      self.stageProgress = float(f.tell() - startPos) / length

      d = f.read(1)
      if not d:
        break
      predict_nr   = byte(d)
      shift_factor = predict_nr & 0xf
      predict_nr >>= 4
      flags        = byte(f.read(1))

      if flags == 7 or flags < 0:
        break

      streamId     = flags % maxStreams
      block        = [byte(f.read(1)) for i in range(14)]
      samples      = streams[streamId].decode(block, predict_nr, shift_factor)
      yield (streamId, struct.pack("28h", *[max(min(int(d + .5), 32767), -32768) for d in samples]))

    f.close()

  def joinPcmFiles(self, pcmLeft, pcmRight, waveOut, sampleRate = 44100):
    pcmLeft  = open(pcmLeft, "rb")
    pcmRight = open(pcmRight, "rb")
    w = wave.open(waveOut, "w")
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(sampleRate)

    pcmLeft.seek(0, 2)
    length = pcmLeft.tell()
    pcmLeft.seek(0)

    while length:
      self.stageProgress = float(pcmLeft.tell()) / length
      l = pcmLeft.read(2)
      r = pcmRight.read(2)
      if not l or not r:
        break
      w.writeframesraw(l + r)
    w.close()
    pcmLeft.close()
    pcmRight.close()

  def decodeVgsFile(self, vgsFile, length, outputSongOggFile, outputGuitarOggFile, outputRhythmOggFile, workPath):
    # Split the file into different tracks
    self.stageInfoText = _("Stage 1/8: Splitting VGS file")

    f         = vgsFile
    blockSize = 16

    header = f.read(0x80)
    magic, version = unpack("4si", header[:4 + 4])
    assert magic == "VgS!"
    header = header[4 + 4:]

    Log.debug("VGS version %d" % (version))

    streams = []
    for channels in range(16):
      rate, blocks = unpack("ii", header[:4 + 4])
      header = header[4 + 4:]
      if not rate or not blocks:
        break
      Log.debug("Stream %d: %d blocks at %d Hz" % (len(streams), blocks, rate))
      streams.append((rate, blocks))

    out = [open(os.path.join(workPath, "chan%d.pcm") % c, "wb") for c in range(channels)]

    for channel, data in self.decodeVgsStreams(vgsFile, length):
      if channel >= 0 and channel < len(out):
        out[channel].write(data)

    [o.close() for o in out]

    # Join the left and right tracks to stereo wave files
    Log.notice("Joining song and guitar tracks")
    songWaveFile   = os.path.join(workPath, "song.wav")
    guitarWaveFile = os.path.join(workPath, "guitar.wav")
    rhythmWaveFile = os.path.join(workPath, "rhythm.wav")

    self.stageInfoText = _("Stage 6/8: Joining song stereo tracks")
    self.joinPcmFiles(os.path.join(workPath, "chan0.pcm"),
                      os.path.join(workPath, "chan1.pcm"),
                      songWaveFile, sampleRate = streams[0][0])
    self.stageInfoText = _("Stage 7/8: Joining guitar stereo tracks")
    self.joinPcmFiles(os.path.join(workPath, "chan2.pcm"),
                      os.path.join(workPath, "chan3.pcm"),
                      guitarWaveFile, sampleRate = streams[2][0])

    if channels == 5:
      self.joinPcmFiles(os.path.join(workPath, "chan4.pcm"),
                        os.path.join(workPath, "chan4.pcm"),
                        rhythmWaveFile, sampleRate = streams[4][0])
    elif channels == 6:
      self.joinPcmFiles(os.path.join(workPath, "chan4.pcm"),
                        os.path.join(workPath, "chan5.pcm"),
                        rhythmWaveFile, sampleRate = streams[4][0])

    # Compress wave files
    self.stageInfoText = _("Stage 8/8: Compressing tracks")
    self.stageProgress = 0.0 / channels
    Log.notice("Compressing song and guitar tracks")
    self.compressWaveFileToOgg(songWaveFile,   outputSongOggFile)
    self.stageProgress = 2.0 / channels
    self.compressWaveFileToOgg(guitarWaveFile, outputGuitarOggFile)
    self.stageProgress = 4.0 / channels
    if channels in [5, 6]:
      self.compressWaveFileToOgg(rhythmWaveFile, outputRhythmOggFile)
      self.stageProgress = 6.0 / channels

    # Cleanup
    for chan in range(channels):
      os.unlink(os.path.join(workPath, "chan%d.pcm" % chan))
    os.unlink(songWaveFile)
    os.unlink(guitarWaveFile)
    if channels in [5, 6]:
      os.unlink(rhythmWaveFile)

  def compressWaveFileToOgg(self, waveFile, oggFile):
    os.system('oggenc "%s" --resample 44100 -q 6 -o "%s"' % (waveFile, oggFile))

  def isOggEncoderPresent(self):
    if os.name == "nt":
      return os.system("oggenc -h > NUL:") == 0
    return os.system("oggenc > /dev/null 2>&1") == 256

  def importSongs(self, headerPath, archivePath, workPath):
    try:
      try:
        os.mkdir(workPath)
      except:
        pass

      # Read the song map
      self.statusText = _("Reading the song list.")
      songMap = {}
      vgsMap =  {}
      for line in open(self.engine.resource.fileName("ghmidimap.txt")):
        songName, fullName, artist = map(lambda s: s.strip(), line.strip().split(";"))
        songMap[songName] = (fullName, artist)

      self.statusText = _("Reading the archive index.")
      archive = ArkFile(headerPath, archivePath)
      songPath = self.engine.resource.fileName("songs", writable = True)
      songs    = []

      # Filter out the songs that aren't in this archive
      for songName, data in songMap.items():
        vgsMap[songName] = "songs/%s/%s.vgs" % (songName, songName)
        if not vgsMap[songName] in archive.files:
          vgsMap[songName] = "songs/%s/%s_sp.vgs" % (songName, songName)
          if not vgsMap[songName] in archive.files:
            Log.warn("VGS file for song '%s' not found in this archive." % songName)
            del songMap[songName]
            continue

        if os.path.exists(os.path.join(songPath, songName)):
          Log.warn("Song '%s' already exists." % songName)
          del songMap[songName]
          continue

      for songName, data in songMap.items():
        fullName, artist = data

        Log.notice("Extracting song '%s'" % songName)
        self.statusText = _("Extracting %s by %s. %d of %d songs imported. Yeah, this is going to take forever.") % (fullName, artist, len(songs), len(songMap))

        archiveMidiFile = "songs/%s/%s.mid" % (songName, songName)
        archiveVgsFile  = vgsMap[songName]

        # Check that the required files exist
        if not archiveMidiFile in archive.files:
          Log.warn("MIDI file for song '%s' not found." % songName)
          continue

        if not archiveVgsFile in archive.files:
          Log.warn("VGS file for song '%s' not found." % songName)
          continue

        # Debug dump
        #vgsFile       = archive.openFile(archiveVgsFile)
        #open("/tmp/test.vgs", "wb").write(vgsFile.read(archive.fileLength(archiveVgsFile)))

        # Grab the VGS file
        vgsFile       = archive.openFile(archiveVgsFile)
        vgsFileLength = archive.fileLength(archiveVgsFile)
        guitarOggFile = os.path.join(workPath, "guitar.ogg")
        songOggFile   = os.path.join(workPath, "song.ogg")
        rhythmOggFile = os.path.join(workPath, "rhythm.ogg")
        self.decodeVgsFile(vgsFile, vgsFileLength, songOggFile, guitarOggFile, rhythmOggFile, workPath)
        vgsFile.close()

        # Create the song
        if not os.path.isfile(rhythmOggFile):
          rhythmOggFile = None

        song = createSong(self.engine, songName, guitarOggFile, songOggFile, rhythmOggFile)
        song.info.name   = fullName.strip()
        song.info.artist = artist.strip()
        song.save()

        # Grab the MIDI file
        archive.extractFile(archiveMidiFile, os.path.join(songPath, songName, "notes.mid"))

        # Done with this song
        songs.append(songName)

      # Clean up
      shutil.rmtree(workPath)

      self.stageInfoText = _("Ready")
      self.stageProgress = 1.0
      Log.debug("Songs imported: " + ", ".join(songs))
      return songs
    except:
      self.done = True
      raise

  def run(self, ticks):
    if self.done == True or self.songs is not None:
      songs = self.songs
      self.songs = None
      self.done = None
      self.statusText = ""
      if songs:
        Dialogs.showMessage(self.engine, _("All done! %d songs imported. Have fun!") % (len(songs)))
      else:
        Dialogs.showMessage(self.engine, _("No songs could be imported, sorry. Check the log files for more information."))
      self.engine.view.popLayer(self)
    if self.wizardStarted:
      return
    self.wizardStarted = True

    # Check for necessary software
    if not self.isOggEncoderPresent():
      if os.name == "nt":
        Dialogs.showMessage(self.engine, _("Ogg Vorbis encoder (oggenc.exe) not found. Please install it to the game directory and try again."))
      else:
        Dialogs.showMessage(self.engine, _("Ogg Vorbis encoder (oggenc) not found. Please install it and try again."))
      self.engine.view.popLayer(self)
      return

    Dialogs.showMessage(self.engine, _("Make sure you have at least 500 megabytes of free disk space before using this importer."))

    path = ""
    while True:
      path = Dialogs.getText(self.engine, prompt = _("Enter the path to the mounted Guitar Hero (tm) DVD"), text = path)

      if not path:
        self.engine.view.popLayer(self)
        return

      headerPath  = os.path.join(path, "gen", "main.hdr")
      archivePath = os.path.join(path, "gen", "main_0.ark")
      if not os.path.isfile(headerPath) or not os.path.isfile(archivePath):
        Dialogs.showMessage(self.engine, _("That's not it. Try again."))
      else:
       break

    workPath = tempfile.mkdtemp("fretsonfire")
    self.engine.boostBackgroundThreads(True)
    self.engine.resource.load(self, "songs", lambda: self.importSongs(headerPath, archivePath, workPath))

  def render(self, visibility, topMost):
    v = (1 - visibility) ** 2

    self.engine.view.setOrthogonalProjection(normalize = True)
    font = self.engine.data.font

    try:
      w, h = font.getStringSize(" ")

      Theme.setSelectedColor()
      font.render(_("Importing Songs"), (.05, .05 - v))
      if self.stageInfoText:
        font.render("%s (%d%%)" % (self.stageInfoText, 100 * self.stageProgress), (.05, .7 + v), scale = 0.001)

      Theme.setBaseColor()
      Dialogs.wrapText(font, (.1, .3 + v), self.statusText)
    finally:
      self.engine.view.resetProjection()
