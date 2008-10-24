#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire                                                     #
# Copyright (C) 2006 Sami Kyöstilä                                  #
#               2008 myfingershurt                                  #
#               2008 Glorandwarf                                    #
#               2008 ShiekOdaSandz                                  #
#               2008 QQStarS                                        #
#               2008 Blazingamer                                    #
#               2008 evilynux <evilynux@gmail.com>                  #
#                                                                   #
# This program is free software; you can redistribute it and/or     #
# modify it under the terms of the GNU General Public License      #
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

"""A bunch of dialog functions for interacting with the user."""

import pygame
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import os
import fnmatch
import string

from View import Layer, BackgroundLayer
from Input import KeyListener
from Camera import Camera
from Mesh import Mesh
from Menu import Menu
from Language import _
from Texture import Texture
import Theme
import Log
import Song
import Data
import Player
import Guitar
import Svg

#myfingershurt: drums :)
import Drum

# evilynux - MFH-Alarian Mod credits
from Credits import Credits

import Config
import Settings


#MFH - for loading phrases
def wrapCenteredText(font, pos, text, rightMargin = 0.9, scale = 0.002, visibility = 0.0):
  """
  Wrap a piece of text inside given margins.
  
  @param pos:         (x, y) tuple, x defines the centerline
  @param text:        Text to wrap
  @param rightMargin: Right margin
  @param scale:       Text scale
  @param visibility:  Visibility factor [0..1], 0 is fully visible
  """
  
  
  x, y = pos

  #MFH: rewriting WrapCenteredText function to properly wrap lines in a centered fashion around a defined centerline (x)
  #space = font.getStringSize(" ", scale = scale)[0]
  #startXpos = x - (rightMargin-x) #for a symmetrical text wrapping
  #x = startXpos
  sentence = ""
  for n, word in enumerate(text.split(" ")):
    w, h = font.getStringSize(sentence + " " + word, scale = scale)
    if x + (w/2) > rightMargin or word == "\n":
      w, h = font.getStringSize(sentence, scale = scale)
      #x = startXpos
      glPushMatrix()
      glRotate(visibility * (n + 1) * -45, 0, 0, 1)
      font.render(sentence, (x - (w/2), y + visibility * n), scale = scale)
      glPopMatrix()
      sentence = word
      y += h*.8 # evilynux - Reduced spacing between lines (worldrave request)
    else:
      if sentence == "" or sentence == "\n":
        sentence = word
      else:
        sentence = sentence + " " + word
  else:
    w, h = font.getStringSize(sentence, scale = scale)
    glPushMatrix()
    glRotate(visibility * (n + 1) * -45, 0, 0, 1)
    font.render(sentence, (x - (w/2), y + visibility * n), scale = scale)
    glPopMatrix()
    y += h*.8 # evilynux - Reduced spacing between lines (worldrave request)
  
    #if word == "\n":
    #  continue
    #x += w + space
  return (x, y)

  #space = font.getStringSize(" ", scale = scale)[0]
  #startXpos = x - (rightMargin-x) #for a symmetrical text wrapping
  #x = startXpos
  #for n, word in enumerate(text.split(" ")):
  #  w, h = font.getStringSize(word, scale = scale)
  #  if x + w > rightMargin or word == "\n":
  #    x = startXpos
  #    y += h*.8 # evilynux - Reduced spacing between lines (worldrave request)
  #  if word == "\n":
  #    continue
  #  glPushMatrix()
  #  glRotate(visibility * (n + 1) * -45, 0, 0, 1)
  #  font.render(word, (x, y + visibility * n), scale = scale)
  #  glPopMatrix()
  #  x += w + space
  #return (x - space, y)


def wrapText(font, pos, text, rightMargin = 0.9, scale = 0.002, visibility = 0.0):
  """
  Wrap a piece of text inside given margins.
  
  @param pos:         (x, y) tuple, x defines the left margin
  @param text:        Text to wrap
  @param rightMargin: Right margin
  @param scale:       Text scale
  @param visibility:  Visibility factor [0..1], 0 is fully visible
  """
  x, y = pos
  w = h = 0
  space = font.getStringSize(" ", scale = scale)[0]

  # evilynux - No longer requires "\n" to be in between spaces
  for n, sentence in enumerate(text.split("\n")):
    y += h
    x = pos[0]
    if n == 0:
      y = pos[1]
    for n, word in enumerate(sentence.strip().split(" ")):
      w, h = font.getStringSize(word, scale = scale)
      if x + w > rightMargin:
        x = pos[0]
        y += h
      glPushMatrix()
      glRotate(visibility * (n + 1) * -45, 0, 0, 1)
      font.render(word, (x, y + visibility * n), scale = scale)
      glPopMatrix()
      x += w + space
  return (x - space, y)

def fadeScreen(v):
  """
  Fade the screen to a dark color to make whatever is on top easier to read.
  
  @param v: Visibility factor [0..1], 0 is fully visible
  """
  glEnable(GL_BLEND)
  glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
  glEnable(GL_COLOR_MATERIAL)

  glBegin(GL_TRIANGLE_STRIP)
  glColor4f(0, 0, 0, .3 - v * .3)
  glVertex2f(0, 0)
  glColor4f(0, 0, 0, .3 - v * .3)
  glVertex2f(1, 0)
  glColor4f(0, 0, 0, .9 - v * .9)
  glVertex2f(0, 1)
  glColor4f(0, 0, 0, .9 - v * .9)
  glVertex2f(1, 1)
  glEnd()
  

class GetText(Layer, KeyListener):
  """Text input layer."""
  def __init__(self, engine, prompt = "", text = ""):
    self.text = text
    self.prompt = prompt
    self.engine = engine
    self.time = 0
    self.accepted = False
    Log.debug("GetText class init (Dialogs.py)...")
    
    self.sfxVolume    = self.engine.config.get("audio", "SFX_volume")

    self.drumHighScoreNav = self.engine.config.get("game", "drum_navigation")  #MFH
    
    
    
  def shown(self):
    self.engine.input.addKeyListener(self, priority = True)
    self.engine.input.enableKeyRepeat()
    
  def hidden(self):
    self.engine.input.removeKeyListener(self)
    self.engine.input.disableKeyRepeat()
    
  def keyPressed(self, key, unicode):
    self.time = 0
    c = self.engine.input.controls.getMapping(key)
    
    #if (c in Player.KEY1S or key == pygame.K_RETURN) and not self.accepted:
    #if (c in Player.KEY1S or key == pygame.K_RETURN or c in Player.DRUM4S) and not self.accepted:   #MFH - adding support for green drum "OK"
    if (c in Player.KEY1S or key == pygame.K_RETURN or (c in Player.DRUM4S and self.drumHighScoreNav)) and not self.accepted:   #MFH - adding support for green drum "OK"
      self.engine.view.popLayer(self)
      self.accepted = True
      if c in Player.KEY1S:
        self.engine.data.acceptSound.setVolume(self.sfxVolume)  #MFH
        self.engine.data.acceptSound.play()
    elif c in Player.CANCELS + Player.KEY2S and not self.accepted:
      self.text = None
      self.engine.view.popLayer(self)
      self.accepted = True
      if c in Player.KEY2S:
        self.engine.data.cancelSound.setVolume(self.sfxVolume)  #MFH
        self.engine.data.cancelSound.play()
    elif (c in Player.KEY4S or key == pygame.K_BACKSPACE) and not self.accepted:
      self.text = self.text[:-1]
      if c in Player.KEY4S:
        self.engine.data.cancelSound.setVolume(self.sfxVolume)  #MFH
        self.engine.data.cancelSound.play()
    elif c in Player.KEY3S and not self.accepted:
      self.text += self.text[len(self.text) - 1]
      self.engine.data.acceptSound.setVolume(self.sfxVolume)  #MFH
      self.engine.data.acceptSound.play()
    elif c in Player.ACTION1S and not self.accepted:
      if len(self.text) == 0:
        self.text = "A"
        return True
      letter = self.text[len(self.text)-1]
      letterNum = ord(letter)
      if letterNum == ord('A'):
        letterNum = ord(' ')
      elif letterNum == ord(' '):
        letterNum = ord('_')
      elif letterNum == ord('_'):
        letterNum = ord('-')
      elif letterNum == ord('-'):
        letterNum = ord('9')
      elif letterNum == ord('0'):
        letterNum = ord('z')
      elif letterNum == ord('a'):
        letterNum = ord('Z')        
      else:
        letterNum -= 1
      self.text = self.text[:-1] + chr(letterNum)
      self.engine.data.selectSound.setVolume(self.sfxVolume)  #MFH
      self.engine.data.selectSound.play()
    elif c in Player.ACTION2S and not self.accepted:
      if len(self.text) == 0:
        self.text = "A"
        return True
      letter = self.text[len(self.text)-1]
      letterNum = ord(letter)
      if letterNum == ord('Z'):
        letterNum = ord('a')
      elif letterNum == ord('z'):
        letterNum = ord('0')
      elif letterNum == ord('9'):
        letterNum = ord('-')
      elif letterNum == ord('-'):
        letterNum = ord('_')
      elif letterNum == ord('_'):
        letterNum = ord(' ')
      elif letterNum == ord(' '):
        letterNum = ord('A')
      else:
        letterNum += 1
      self.text = self.text[:-1] + chr(letterNum)
      self.engine.data.selectSound.setVolume(self.sfxVolume)  #MFH
      self.engine.data.selectSound.play()
    elif unicode and ord(unicode) > 31 and not self.accepted:
      self.text += unicode
    return True
    
  def run(self, ticks):
    self.time += ticks / 50.0
  
  def render(self, visibility, topMost):
    self.engine.view.setViewport(1,0)
    self.engine.view.setOrthogonalProjection(normalize = True)
    font = self.engine.data.font
    
    try:
      v = (1 - visibility) ** 2
      
      fadeScreen(v)
      Theme.setBaseColor(1 - v)

      if (self.time % 10) < 5 and visibility > .9:
        cursor = "|"
      else:
        cursor = ""

      pos = wrapText(font, (.1, .33 - v), self.prompt)

      Theme.setSelectedColor(1 - v)
      
      if self.text is not None:
        pos = wrapText(font, (.1, (pos[1] + v) + .08 + v / 4), self.text)
        font.render(cursor, pos)
      
    finally:
      self.engine.view.resetProjection()

class GetKey(Layer, KeyListener):
  """Key choosing layer."""
  def __init__(self, engine, prompt = "", key = None):
    self.key = key
    self.prompt = prompt
    self.engine = engine
    self.time = 0
    self.accepted = False
    Log.debug("GetKey class init (Dialogs.py)...")
    
  def shown(self):
    self.engine.input.addKeyListener(self, priority = True)
    
  def hidden(self):
    self.engine.input.removeKeyListener(self)
    
  def keyPressed(self, key, unicode):
    c = self.engine.input.controls.getMapping(key)
    if c in Player.CANCELS + Player.KEY2S and not self.accepted:
      self.key = None
      self.engine.view.popLayer(self)
      self.accepted = True
    elif not self.accepted:
      self.key = key
      self.engine.view.popLayer(self)
      self.accepted = True
    return True
    
  def run(self, ticks):
    self.time += ticks / 50.0
  
  def render(self, visibility, topMost):
    self.engine.view.setViewport(1,0)
    self.engine.view.setOrthogonalProjection(normalize = True)
    font = self.engine.data.font
    
    try:
      v = (1 - visibility) ** 2
      
      fadeScreen(v)
      Theme.setBaseColor(1 - v)

      pos = wrapText(font, (.1, .33 - v), self.prompt)

      Theme.setSelectedColor(1 - v)

      if self.key is not None:
        text = pygame.key.name(self.key).capitalize()
        pos = wrapText(font, (.1, (pos[1] + v) + .08 + v / 4), text)
      
    finally:
      self.engine.view.resetProjection()

class LoadingScreen(Layer, KeyListener):
  """Loading screen layer."""
  def __init__(self, engine, condition, text, allowCancel = False):
    self.engine       = engine
    self.text         = text
    self.condition    = condition
    self.ready        = False
    self.allowCancel  = allowCancel
    self.time         = 0.0
    Log.debug("LoadingScreen class init (Dialogs.py)...")
    self.loadingx = Theme.loadingX
    self.loadingy = Theme.loadingY
    self.allowtext = self.engine.config.get("game", "lphrases")    

    #Get theme
    themename = self.engine.data.themeLabel
    self.theme = self.engine.data.theme

  def shown(self):
    self.engine.input.addKeyListener(self, priority = True)

  def keyPressed(self, key, unicode):
    c = self.engine.input.controls.getMapping(key)
    if self.allowCancel and c in Player.CANCELS:
      self.engine.view.popLayer(self)
    return True
    
  def hidden(self):
    self.engine.boostBackgroundThreads(False)
    self.engine.input.removeKeyListener(self)

  def run(self, ticks):
    self.time += ticks / 50.0
    if not self.ready and self.condition():
      self.engine.view.popLayer(self)
      self.ready = True
  
  def render(self, visibility, topMost):
    self.engine.view.setViewport(1,0)
    self.engine.view.setOrthogonalProjection(normalize = True)
    #font = self.engine.data.font
    font = self.engine.data.loadingFont

    if not font:
      return

    if visibility > 0.9:
      self.engine.boostBackgroundThreads(True)
    else:
      self.engine.boostBackgroundThreads(False)
    
    try:
      v = (1 - visibility) ** 2
      fadeScreen(v)

      w, h = self.engine.view.geometry[2:4]
      
      #MFH - auto-scaling of loading screen
      imgwidth = self.engine.data.loadingImage.width1()
      wfactor = 640.000/imgwidth
      self.engine.data.loadingImage.transform.reset()
      self.engine.data.loadingImage.transform.translate(w/2,h/2)
      self.engine.data.loadingImage.transform.scale(wfactor,-wfactor)
      self.engine.data.loadingImage.draw(color = (1, 1, 1, 1))

      Theme.setBaseColor(1 - v)
      w, h = font.getStringSize(self.text)

      if self.loadingx != None:
        if self.loadingy != None:
          x = self.loadingx - w / 2
          y = self.loadingy - h / 2 + v * .5
        else:
          x = self.loadingx - w / 2
          y = .6 - h / 2 + v * .5
      elif self.loadingy != None:
        x = .5 - w / 2
        y = .6 - h / 2 + v * .5
      else:
        x = .5 - w / 2
        y = .6 - h / 2 + v * .5

      if self.allowtext:
        font.render(self.text, (x, y))     

    finally:
      self.engine.view.resetProjection()

class MessageScreen(Layer, KeyListener):
  """Message screen layer."""
  def __init__(self, engine, text, prompt = _("<OK>")):
    self.engine = engine
    self.text = text
    self.time = 0.0
    self.prompt = prompt
    Log.debug("MessageScreen class init (Dialogs.py)...")
    

  def shown(self):
    self.engine.input.addKeyListener(self, priority = True)

  def keyPressed(self, key, unicode):
    c = self.engine.input.controls.getMapping(key)
    if c in Player.KEY1S + Player.KEY2S + Player.CANCELS or key == pygame.K_RETURN:
      self.engine.view.popLayer(self)
    return True
    
  def hidden(self):
    self.engine.input.removeKeyListener(self)

  def run(self, ticks):
    self.time += ticks / 50.0
  
  def render(self, visibility, topMost):
    self.engine.view.setViewport(1,0)
    self.engine.view.setOrthogonalProjection(normalize = True)
    font = self.engine.data.font

    if not font:
      return
    
    try:
      v = (1 - visibility) ** 2
      fadeScreen(v)

      x = .1
      y = .3 + v * 2
      Theme.setBaseColor(1 - v)
      pos = wrapText(font, (x, y), self.text, visibility = v)

      w, h = font.getStringSize(self.prompt, scale = 0.001)
      x = .5 - w / 2
      y = pos[1] + 3 * h + v * 2
      Theme.setSelectedColor(1 - v)
      font.render(self.prompt, (x, y), scale = 0.001)
      
    finally:
      self.engine.view.resetProjection()
      
class SongChooser(Layer, KeyListener):
  """Song choosing layer."""
  def __init__(self, engine, prompt = "", selectedSong = None, selectedLibrary = None):
    self.prompt         = prompt
    self.engine         = engine
    
    Log.debug("SongChooser class init (Dialogs.py)...")

    #MFH - retrieve game parameters:
    self.gamePlayers = self.engine.config.get("game", "players")
    self.gameMode1p = self.engine.config.get("player0","mode_1p")
    self.gameMode2p = self.engine.config.get("player1","mode_2p")
    if self.gameMode1p == 2:
      self.careerMode = True
    else:
      self.careerMode = False
    
    self.drumNav = self.engine.config.get("game", "drum_navigation")  #MFH
    
    
    self.career_title_color = Theme.hexToColor(Theme.career_title_colorVar)
    self.song_name_text_color = Theme.hexToColor(Theme.song_name_text_colorVar)
    self.song_name_selected_color = Theme.hexToColor(Theme.song_name_selected_colorVar)
    self.artist_text_color = Theme.hexToColor(Theme.artist_text_colorVar)
    self.artist_selected_color = Theme.hexToColor(Theme.artist_selected_colorVar)
    self.library_text_color = Theme.hexToColor(Theme.library_text_colorVar)
    self.library_selected_color = Theme.hexToColor(Theme.library_selected_colorVar)
    self.songlist_score_color = Theme.hexToColor(Theme.songlist_score_colorVar)

    Log.debug("Songlist artist colors: " + str(self.artist_text_color) + " / " + str(self.artist_selected_color))



    #MFH
    try:
      self.song_cd_xpos = Theme.song_cd_Xpos
      Log.debug("song_cd_xpos found: " + str(self.song_cd_xpos))
    except Exception, e:
      Log.warn("Unable to load Theme song_cd_xpos: %s" % e) 
      self.song_cd_xpos = None

    try:
      self.song_cdscore_xpos = Theme.song_cdscore_Xpos
      Log.debug("song_cdscore_xpos found: " + str(self.song_cdscore_xpos))
    except Exception, e:
      Log.warn("Unable to load Theme song_cdscore_xpos: %s" % e) 
      self.song_cdscore_xpos = None

    try:
      self.song_list_xpos = Theme.song_list_Xpos
      Log.debug("song_list_xpos found: " + str(self.song_list_xpos))
    except Exception, e:
      Log.warn("Unable to load Theme song_list_xpos: %s" % e) 
      self.song_list_xpos = None

    try:
      self.song_listscore_xpos = Theme.song_listscore_Xpos
      Log.debug("song_listscore_xpos found: " + str(self.song_listscore_xpos))
    except Exception, e:
      Log.warn("Unable to load Theme song_listscore_xpos: %s" % e) 
      self.song_listscore_xpos = None


    #pre-determine these values and just replace them with these variables in the render function:

    #Blazingamer CD X position fix
    if self.song_cd_xpos == None:
      self.song_cd_xpos = 0.0
    elif self.song_cd_xpos > 5:
      self.song_cd_xpos = 5.0
    elif self.song_cd_xpos < 0:
      self.song_cd_xpos = 0.0


    if self.song_cdscore_xpos == None:
      self.song_cdscore_xpos = 0.6

    if self.song_list_xpos == None:
      self.song_list_xpos = 0.15

    if self.song_listscore_xpos == None:
      self.song_listscore_xpos = 0.8
    

    
    self.time           = 0
    self.lastTime       = 0
    self.accepted       = False
    self.selectedIndex  = 0
    self.camera         = Camera()
    self.cassetteHeight = .8
    self.cassetteWidth  = 4.0
    self.libraryHeight  = 1.2
    self.libraryWidth   = 4.0

    self.titleHeight    = 2.4
    self.titleWidth     = 4.0

    self.itemAngles     = None
    self.itemLabels     = None
    self.selectedOffset = 0.0
    self.cameraOffset   = 0.0
    self.selectedItem   = None
    self.song           = None
    self.songCountdown  = 1024
    self.songLoader     = None
    self.initialItem    = selectedSong
    self.library        = selectedLibrary
    self.searchText     = ""
    self.searching      = False

    #RF-mod
    self.previewDisabled  = self.engine.config.get("audio", "disable_preview")
    self.sortOrder        = self.engine.config.get("game", "sort_order")
    self.rotationDisabled = self.engine.config.get("performance", "disable_librotation")
    self.spinnyDisabled   = self.engine.config.get("game", "disable_spinny")

    self.sfxVolume    = self.engine.config.get("audio", "SFX_volume")

    #Get Theme
    themename = self.engine.data.themeLabel
    self.theme = self.engine.data.theme

    self.display = self.engine.config.get("coffee", "songdisplay")

    self.songback = Theme.songback
    self.filepathenable = self.engine.config.get("coffee", "songfilepath")

    temp = self.engine.config.get("game", "search_key")
    
    if temp != "None":
      self.searchKey = ord(temp[0])
    else:
      self.searchKey = ord('/')
    
    # Use the default library if this one doesn't exist
    if not self.library or not os.path.isdir(self.engine.resource.fileName(self.library)):
      self.library = Song.DEFAULT_LIBRARY

    self.loadCollection()


    #MFH configurable default instrument display with 5th / orange fret
    self.instrument = self.engine.config.get("game", "songlist_instrument")
    if self.instrument == 4:
      self.instrument = "Drums"
    elif self.instrument == 3:
      self.instrument = "Lead Guitar"
    elif self.instrument == 2:
      self.instrument = "Bass Guitar"
    elif self.instrument == 1:
      self.instrument = "Rhythm Guitar"
    else: 
      self.instrument = "Guitar"

    if self.display:
      self.engine.resource.load(self, "cassette",     lambda: Mesh(self.engine.resource.fileName("cassette.dae")), synch = True)
      self.engine.resource.load(self, "label",        lambda: Mesh(self.engine.resource.fileName("label.dae")), synch = True)
      self.engine.resource.load(self, "libraryMesh",  lambda: Mesh(self.engine.resource.fileName("library.dae")), synch = True)
      self.engine.resource.load(self, "libraryLabel", lambda: Mesh(self.engine.resource.fileName("library_label.dae")), synch = True)
      self.engine.loadImgDrawing(self, "background",  os.path.join("themes",themename,"menu","songchoosepaper.png"))
    else:
      try:
        self.engine.loadImgDrawing(self, "background",  os.path.join("themes",themename,"menu","songchooseback.png"))
      except IOError:
        self.background = None
      self.engine.loadImgDrawing(self, "paper",       os.path.join("themes",themename,"menu","songchoosepaper.png"))
      self.engine.loadImgDrawing(self, "selected",    os.path.join("themes",themename,"menu","selected.png"))
      self.scoreTimer = 0


      # evilynux - configurable default highscores difficulty display
      self.diff = self.engine.config.get("game", "songlist_difficulty")
      if self.diff == 3:
        self.diff = "Easy"
      elif self.diff == 2:
        self.diff = "Medium"
      elif self.diff == 1:
        self.diff = "Hard"
      else: # self.diff == 0:
        self.diff = "Expert"

    # evilynux - Shall we show hit% and note streak?
    self.extraStats = self.engine.config.get("game", "songlist_extra_stats")
    #myfingershurt: adding yellow fret preview again
    self.playSong = False

#racer: preview graphic
    try:
      self.engine.loadImgDrawing(self, "preview",  os.path.join("themes",themename,"menu","preview.png"))
    except IOError:
      self.preview = None

#racer: highscores are changed by fret
    self.highScoreChange = False
    self.highScoreType = self.engine.config.get("game", "HSMovement")

    self.instrumentChange = False   #MFH

  def loadCollection(self):
    Log.debug("Dialogs.loadCollection() function call...")
    self.loaded = False
    #showLoadingScreen(self.engine, lambda: self.loaded, text = _("Browsing Collection..."))
    self.splash = showLoadingSplashScreen(self.engine, _("Browsing Collection..."))
    
    self.engine.resource.load(self, "libraries", lambda: Song.getAvailableLibraries(self.engine, self.library), onLoad = self.libraryListLoaded, synch = True) # evilynux - Less BlackSOD[?]

    #showLoadingScreen(self.engine, lambda: self.loaded, text = _("Browsing Collection..."))

    

  def libraryListLoaded(self, libraries):
    Log.debug("Dialogs.libraryListLoaded() function call...")
    #self.engine.resource.load(self, "songs",     lambda: Song.getAvailableSongs(self.engine, self.library), onLoad = self.songListLoaded)
    self.engine.resource.load(self, "songs",     lambda: Song.getAvailableSongsAndTitles(self.engine, self.library), onLoad = self.songListLoaded, synch = True) # evilynux - Less BlackSOD[?]

  def isInt(self, possibleInt):
    try:
      #MFH - remove any leading zeros (for songs with 01. or 02. for example)        
      splitName = possibleInt.split("0",1)
      while splitName[0] == "":
        splitName = possibleInt.split("0",1)
        if len(splitName) > 1:
          if splitName[0] == "":
            possibleInt = splitName[1]
      if str(int(possibleInt)) == str(possibleInt):
        #Log.debug("Dialogs.isInt: " + str(possibleInt) + " = TRUE")
        return True
      else:
        #Log.debug("Dialogs.isInt: " + str(possibleInt) + " = FALSE")
        return False
    except Exception, e:
      return False
      #Log.debug("Dialogs.isInt: " + str(possibleInt) + " = FALSE, exception: " + str(e) )
      
  def removeSongOrderPrefixFromItem(self, item):
    if not item.name.startswith("."):
      splitName = item.name.split(".",1)
      #Log.debug("Dialogs.songListLoaded: Separating song name from prefix: " + str(splitName) )
      if self.isInt(splitName[0]) and len(splitName) > 1:
        item.name = splitName[1]
        #while len(splitName) > 1: #now remove any remaining leading spaces
        splitName[0] = ""
        while splitName[0] == "":
          splitName = item.name.split(" ",1)
          if len(splitName) > 1:
            if splitName[0] == "":
              item.name = splitName[1]
              #Log.debug("Dialogs.songListLoaded: Removing song name prefix, new name = " + splitName[1])
    else:
      Log.debug("Song name starting with a period filtered from prefix removal logic: " + item.name)



  def songListLoaded(self, songs):
    if self.songLoader:
      self.songLoader.stop() # evilynux - cancel() became stop()
    self.selectedIndex = 0
    
    #MFH: Here, scan self.songs for a SongInfo followed by a TitleInfo.  Insert a BlankSpaceInfo object in between them. (one will already be in front of a CareerResetterInfo)
    addingBlankSpaces = True
    foundEndOfCareerYet = False
    while addingBlankSpaces:
      lastObjectWasASong = False
      for i, item in enumerate(self.songs):
        if isinstance(item, Song.SongInfo):
          lastObjectWasASong = True
        elif isinstance(item, Song.TitleInfo):
          if lastObjectWasASong:
            self.songs.insert(i, Song.BlankSpaceInfo())
            Log.debug("Dialogs.py: Inserted blank space in self.songs list before " + item.getName())
            break   #now that the self.songs list has changed, we must re-enumerate and look for the next place to insert a space
          lastObjectWasASong = False
        elif isinstance(item, Song.BlankSpaceInfo):
          if item.name == _("End of Career") and not foundEndOfCareerYet:   #also want to insert a blank space after the end of career marker
            self.songs.insert(i, Song.BlankSpaceInfo())   #insert a blank space before End of Career
            self.songs.insert(i+2, Song.BlankSpaceInfo())   #...and after End of Career (which is now shifted up one index)
            foundEndOfCareerYet = True
            Log.debug("Dialogs.py: Inserted blank space in self.songs list after " + item.getName())
            break   #now that the self.songs list has changed, we must re-enumerate and look for the next place to insert a space
          lastObjectWasASong = False
        else:
          lastObjectWasASong = False
      else:   #executed after the for loop finishes
        addingBlankSpaces = False   #finished adding blank spaces, exit while loop
        Log.debug("Dialogs.py: Finished inserting blank spaces in self.songs.")

    #MFH: Second scan through songlist items to remove any resulting double blank spaces
    removingBlankSpaces = True
    foundEndOfCareerYet = False
    while removingBlankSpaces:
      lastObjectWasASpace = False
      for i, item in enumerate(self.songs):
        if isinstance(item, Song.BlankSpaceInfo) and item.name == "":
          if lastObjectWasASpace:
            #self.songs.remove(i)
            del self.songs[i]
            break
          
          lastObjectWasASpace = True
        else:
          lastObjectWasASpace = False
      else:   #executed after the for loop finishes
        removingBlankSpaces = False   #finished adding blank spaces, exit while loop
        Log.debug("Dialogs.py: Finished filtering doubled blank spaces in self.songs.")


    self.items         = self.libraries + self.songs

    #Log.debug("Dialogs.songListLoaded: self.items = " + str(self.items))
    Log.debug("Dialogs.songListLoaded.")

    self.itemAngles    = [0.0] * len(self.items)
    self.itemLabels    = [None] * len(self.items)
    self.loaded        = True
    self.searchText    = ""
    self.searching     = False
    if self.initialItem is not None:
      for i, item in enumerate(self.items):
        if isinstance(item, Song.SongInfo) and self.initialItem == item.songName:
          self.selectedIndex =  i
          break
        elif isinstance(item, Song.LibraryInfo) and self.initialItem == item.libraryName:
          self.selectedIndex =  i
          break

    #MFH
    self.tiersArePresent = False
    self.indentString = "   "

    #MFH: filter out song name prefixes "1." "2." etc 
    #   but -- also must NOT get stuck here on ellipsises (such as RBDLC - Metallica - ...And Justice For All)
    for i, item in enumerate(self.items):
      if isinstance(item, Song.SongInfo):


        self.removeSongOrderPrefixFromItem(item)
#-        if not item.name.startswith("."):
#-          splitName = item.name.split(".",1)
#-          #Log.debug("Dialogs.songListLoaded: Separating song name from prefix: " + str(splitName) )
#-          if self.isInt(splitName[0]) and len(splitName) > 1:
#-            item.name = splitName[1]
#-            #while len(splitName) > 1: #now remove any remaining leading spaces
#-            splitName[0] = ""
#-            while splitName[0] == "":
#-              splitName = item.name.split(" ",1)
#-              if len(splitName) > 1:
#-                if splitName[0] == "":
#-                  item.name = splitName[1]
#-                  #Log.debug("Dialogs.songListLoaded: Removing song name prefix, new name = " + splitName[1])
#-        else:
#-          Log.debug("Song name starting with a period filtered from prefix removal logic: " + item.name)

      elif isinstance(item, Song.TitleInfo):
        self.tiersArePresent = True 

    # if the first item is a title, start on the second one
    #FIXME: potential infinite loop if there are only titles
    if self.items == []:    #MFH: Catch when there ain't a damn thing in the current folder - back out!
      if self.library != Song.DEFAULT_LIBRARY:
        self.initialItem = self.library
        self.library     = os.path.dirname(self.library)
        self.selectedItem = None
        self.loadCollection()
    
    else:
    #if self.items != []:
      while isinstance(self.items[self.selectedIndex], Song.TitleInfo):
        self.selectedIndex = (self.selectedIndex + 1) % len(self.items)
    # Load labels for libraries right away
    #if self.items != []:
      self.updateSelection()

    hideLoadingSplashScreen(self.engine, self.splash)
    self.splash = None

    
  def shown(self):
    self.engine.input.addKeyListener(self, priority = True)
    self.engine.input.enableKeyRepeat()
    
  def hidden(self):
    if self.songLoader:
      self.songLoader.stop() # evilynux - cancel() became stop()
    if self.song:
      self.song.fadeout(1000)
      self.song = None
    self.engine.input.removeKeyListener(self)
    self.engine.input.disableKeyRepeat()
    
  def getSelectedSong(self):
    if isinstance(self.selectedItem, Song.SongInfo):
      return self.selectedItem.songName

  def getSelectedItem(self):
    return self.selectedItem


  def getSelectedLibrary(self):
    return self.library

  def getItems(self):
    return self.items
  
  def loadItemLabel(self, i):
    # Load the item label if it isn't yet loaded
    item = self.items[i]
    if self.itemLabels[i] is None:
      if isinstance(item, Song.SongInfo):
        label = self.engine.resource.fileName(self.library, item.songName,    "label.png")
      elif isinstance(item, Song.LibraryInfo):
        label = self.engine.resource.fileName(item.libraryName, "label.png")
      else:
        return
      if os.path.exists(label):
        self.itemLabels[i] = Texture(label)

  def updateSelection(self):
  
    self.selectedItem  = self.items[self.selectedIndex]
    self.songCountdown = 1024

    #myfingershurt: only if CD list
    if self.display:
      if self.selectedIndex > 1:
        self.loadItemLabel(self.selectedIndex - 1)
      self.loadItemLabel(self.selectedIndex)
      if self.selectedIndex < len(self.items) - 1:
        self.loadItemLabel(self.selectedIndex + 1)
    
  def keyPressed(self, key, unicode): #racer: drum nav.
    if not self.items or self.accepted:
      return

    self.lastTime = self.time
    c = self.engine.input.controls.getMapping(key)
    if c in Player.KEY1S or key == pygame.K_RETURN or (c in Player.DRUM4S and self.drumNav):
      if self.matchesSearch(self.selectedItem):
        #if not self.song: #MFH - play the sound immediately, THEN process.
        self.engine.data.acceptSound.setVolume(self.sfxVolume)  #MFH
        self.engine.data.acceptSound.play()
        if isinstance(self.selectedItem, Song.LibraryInfo):
          self.library     = self.selectedItem.libraryName
          self.initialItem = None
          Log.debug("New library selected: " + str(self.library) )
          self.loadCollection()
        elif isinstance(self.selectedItem, Song.SongInfo) and not self.selectedItem.getLocked():
        #else:
          self.engine.view.popLayer(self)
          self.accepted = True
        elif isinstance(self.selectedItem, Song.CareerResetterInfo):  #MFH - here's where to actually reset careers
          self.engine.view.popLayer(self)
          while True:
            isYouSure = chooseItem(self.engine, [_("No"),_("Yes")], _("Are you sure you want to reset this entire career?") )
            if isYouSure:
              if isYouSure == _("Yes"):
                splash = showLoadingSplashScreen(self.engine, _("Resetting career..."))
                for i, item in enumerate(self.items):
                  if isinstance(item, Song.SongInfo) and item.completed:
                    item.completed = False
                    item.save()
                self.loadCollection()
                hideLoadingSplashScreen(self.engine, splash)
                splash = None
              break
            else:
              break  
          self.engine.view.pushLayer(self)
        
    elif c in Player.CANCELS + Player.KEY2S or (c in Player.DRUM1S and self.drumNav):
      #if not self.song:
      self.engine.data.cancelSound.setVolume(self.sfxVolume)  #MFH
      self.engine.data.cancelSound.play()
      if self.library != Song.DEFAULT_LIBRARY:
        self.initialItem = self.library
        self.library     = os.path.dirname(self.library)
        if self.song:
          self.song.fadeout(1000)
        self.selectedItem = None
        self.loadCollection()
      else:
        self.selectedItem = None
        self.engine.view.popLayer(self)
        self.accepted = True

    # left + right to quickly skip to the item after the next title
    elif c in Player.LEFTS:
      #if self.tiersArePresent or self.careerMode: # if there are no titles, we'll have an infinite loop = bad
      if self.tiersArePresent: # if there are no titles, we'll have an infinite loop = bad
        self.selectedIndex = (self.selectedIndex - 1) % len(self.items)   #MFH - nudge it up one count.
        if isinstance(self.items[self.selectedIndex], Song.TitleInfo):  #MFH - if we just found a title, we need to go once more to ensure we're goin back a title:
          self.selectedIndex = (self.selectedIndex - 1) % len(self.items)
        while not ( isinstance(self.items[self.selectedIndex], Song.TitleInfo) or isinstance(self.items[self.selectedIndex], Song.CareerResetterInfo) ):
          self.selectedIndex = (self.selectedIndex - 1) % len(self.items)
        while 1:
          if isinstance(self.items[self.selectedIndex], Song.CareerResetterInfo):
            break
          self.selectedIndex = (self.selectedIndex + 1) % len(self.items)
          if self.matchesSearch(self.items[self.selectedIndex]) and not isinstance(self.items[self.selectedIndex], Song.TitleInfo):
            break
        self.updateSelection()
    
    elif c in Player.RIGHTS:
      #if self.tiersArePresent or self.careerMode: # if there are no titles, we'll have an infinite loop = bad
      if self.tiersArePresent: # if there are no titles, we'll have an infinite loop = bad
        self.selectedIndex = (self.selectedIndex + 1) % len(self.items) #MFH - nudge it down one count to get things started.
        while not ( isinstance(self.items[self.selectedIndex], Song.TitleInfo) or isinstance(self.items[self.selectedIndex], Song.CareerResetterInfo) ):
          self.selectedIndex = (self.selectedIndex + 1) % len(self.items)
        while 1:
          if isinstance(self.items[self.selectedIndex], Song.CareerResetterInfo):
            break
          self.selectedIndex = (self.selectedIndex + 1) % len(self.items)
          if self.matchesSearch(self.items[self.selectedIndex]) and not isinstance(self.items[self.selectedIndex], Song.TitleInfo):
            break
        self.updateSelection()
    

        
    #myfingershurt: adding yellow fret preview again
    elif c in Player.KEY3S:
      self.playSong = True

  #racer: highscores change on fret hit
    elif c in Player.KEY4S or (c in Player.BASEDRUMS and self.drumNav):
     self.highScoreChange = True

    #MFH - instrument change on 5th fret
    elif c in Player.KEY5S or (c in Player.DRUM3S and self.drumNav):
     self.instrumentChange = True


    elif c in Player.UPS + Player.ACTION1S or (c in Player.DRUM2S and self.drumNav):
      #if not self.song:
      self.engine.data.selectSound.setVolume(self.sfxVolume)  #MFH
      self.engine.data.selectSound.play()
      if self.matchesSearch(self.items[self.selectedIndex]):
        while 1:
          #self.selectedIndex = (self.selectedIndex - 1) % len(self.items)
          # evilynux - Skip blank lines and Tier names
          currentIndex = self.selectedIndex
          while 1:
            currentIndex = (currentIndex - 1) % len(self.items)
            if isinstance(self.items[currentIndex], Song.SongInfo) or \
               isinstance(self.items[currentIndex], Song.CareerResetterInfo) or \
               isinstance(self.items[currentIndex], Song.LibraryInfo) or \
               (self.display and isinstance(self.items[currentIndex], Song.TitleInfo)):
              break
          self.selectedIndex = currentIndex

          if self.matchesSearch(self.items[self.selectedIndex]):
          #if self.matchesSearch(self.items[self.selectedIndex]) and not isinstance(self.items[self.selectedIndex], Song.TitleInfo):
            break
      self.updateSelection()
    elif c in Player.DOWNS + Player.ACTION2S or (c in Player.DRUM3S and self.drumNav):
      #if not self.song:
      self.engine.data.selectSound.setVolume(self.sfxVolume)  #MFH
      self.engine.data.selectSound.play()
      if self.matchesSearch(self.items[self.selectedIndex]):
        while 1:
          #self.selectedIndex = (self.selectedIndex + 1) % len(self.items)
          # evilynux - Skip blank lines and Tier names
          currentIndex = self.selectedIndex
          while 1:
            currentIndex = (currentIndex + 1) % len(self.items)
            if isinstance(self.items[currentIndex], Song.SongInfo) or \
               isinstance(self.items[currentIndex], Song.CareerResetterInfo) or \
               isinstance(self.items[currentIndex], Song.LibraryInfo) or \
               (self.display and isinstance(self.items[currentIndex], Song.TitleInfo)):
              break
          self.selectedIndex = currentIndex
          
          if self.matchesSearch(self.items[self.selectedIndex]):
          #if self.matchesSearch(self.items[self.selectedIndex]) and not isinstance(self.items[self.selectedIndex], Song.TitleInfo):
            break
      self.updateSelection()
    elif key == pygame.K_BACKSPACE and not self.accepted:
      self.searchText = self.searchText[:-1]
      if self.searchText == "":
        self.searching = False
    elif key == self.searchKey:
      if self.searching == False:
        self.searching = True
      else:
        self.searching == False
    elif self.searching == True and unicode and ord(unicode) > 31 and not self.accepted:
      self.searchText += unicode
      self.doSearch()
    elif self.searching == False and ((key >= ord('a') and key <= ord('z')) or (key >= ord('A') and key <= ord('Z')) or (key >= ord('0') and key <= ord('9'))):
      k1 = unicode
      k2 = k1.capitalize()
      found = 0
      
      for i in range(len(self.items)):
        if self.sortOrder == 1:
          if not self.items[i].artist:
            continue
          if self.items[i].artist[0] == k1 or self.items[i].artist[0] == k2:
            found = 1
            break
        else:
          if not self.items[i].name:
            continue
          if self.items[i].name[0] == k1 or self.items[i].name[0] == k2:
            found = 1
            break
      if found == 1 and self.selectedIndex != i:
        self.selectedIndex = i
        self.updateSelection() 
    return True

  def matchesSearch(self, item):
    if not self.searchText:
      return True
    if isinstance(item, Song.SongInfo):
      if self.searchText.lower() in item.name.lower() or self.searchText.lower() in item.artist.lower():
        return True
    elif isinstance(item, Song.LibraryInfo):
      if self.searchText.lower() in item.name.lower():
        return True
    return False

  def doSearch(self):
    if not self.searchText:
      return
      
    for i, item in enumerate(self.items):
      if self.matchesSearch(item):
          self.selectedIndex =  i
          self.updateSelection()
          break

  def songLoaded(self, song):
    self.songLoader = None

    if self.song:
      self.song.stop()
    
    song.setGuitarVolume(self.engine.config.get("audio", "guitarvol"))
    song.setBackgroundVolume(self.engine.config.get("audio", "songvol"))
    song.setRhythmVolume(self.engine.config.get("audio", "rhythmvol"))
    song.play()
    self.song = song

  def playSelectedSong(self):
    song = self.getSelectedSong()
    if not song:
      return
    
    songItem = self.getSelectedItem()
    
    #MFH - check for career mode, and song's unlocked status before playing
    #Need to check if song is locked; not completed (then current songs can be previewable)
    if self.careerMode and songItem.getLocked():
      if self.song:
        self.song.fadeout(1000)
      return
    
    # evilynux - Stop already playing song if any
    if self.songLoader:
      self.songLoader.stop()

    self.songLoader = self.engine.resource.load(self, None, lambda: Song.loadSong(self.engine, song, playbackOnly = True, library = self.library), synch = True, onLoad = self.songLoaded) # evilynux - Less BlackSOD[?]    

  def run(self, ticks):
    self.time += ticks / 50.0


    if self.previewDisabled:
      #myfingershurt: adding yellow fret preview again, and making it compatible with the auto-preview setting
      if self.playSong == True:
        self.playSelectedSong()
        self.playSong = False
    elif self.songCountdown > 0:
      self.songCountdown -= ticks
      if self.songCountdown <= 0:
        self.playSelectedSong()

    d = self.cameraOffset - self.selectedOffset
    self.cameraOffset -= d * ticks / 192.0
    
    for i in range(len(self.itemAngles)):
      if i == self.selectedIndex:
        self.itemAngles[i] = min(90, self.itemAngles[i] + ticks / 2.0)
      else:
        self.itemAngles[i] = max(0,  self.itemAngles[i] - ticks / 2.0)
    
  def renderCassette(self, color, label):
    if not self.cassette:
      return

    if color:
      glColor3f(*color)

    glEnable(GL_COLOR_MATERIAL)
    self.cassette.render("Mesh_001")
    glColor3f(.1, .1, .1)
    self.cassette.render("Mesh")

    # Draw the label if there is one
    if label is not None:
      glEnable(GL_TEXTURE_2D)
      label.bind()
      glColor3f(1, 1, 1)
      glMatrixMode(GL_TEXTURE)
      glScalef(1, -1, 1)
      glMatrixMode(GL_MODELVIEW)
      self.label.render("Mesh_001")
      glMatrixMode(GL_TEXTURE)
      glLoadIdentity()
      glMatrixMode(GL_MODELVIEW)
      glDisable(GL_TEXTURE_2D)
  
  def renderLibrary(self, color, label):
    if not self.libraryMesh:
      return

    if color:
      glColor3f(*color)

    glEnable(GL_NORMALIZE)
    glEnable(GL_COLOR_MATERIAL)
    self.libraryMesh.render("Mesh_001")
    glColor3f(.1, .1, .1)
    self.libraryMesh.render("Mesh")

    # Draw the label if there is one
    if label is not None:
      glEnable(GL_TEXTURE_2D)
      label.bind()
      glColor3f(1, 1, 1)
      glMatrixMode(GL_TEXTURE)
      glScalef(1, -1, 1)
      glMatrixMode(GL_MODELVIEW)
      self.libraryLabel.render()
      glMatrixMode(GL_TEXTURE)
      glLoadIdentity()
      glMatrixMode(GL_MODELVIEW)
      glDisable(GL_TEXTURE_2D)
    glDisable(GL_NORMALIZE)

#MFH - need to render titles (with new function so future expansion can include title labels):
  def renderTitle(self, color, label):
    if not self.libraryMesh:
      return

    if color:
      glColor3f(*color)

    glEnable(GL_NORMALIZE)
    glEnable(GL_COLOR_MATERIAL)
    self.libraryMesh.render("Mesh_001")
    glColor3f(.1, .1, .1)
    self.libraryMesh.render("Mesh")

    # Draw the label if there is one
    if label is not None:
      glEnable(GL_TEXTURE_2D)
      label.bind()
      glColor3f(1, 1, 1)
      glMatrixMode(GL_TEXTURE)
      glScalef(1, -1, 1)
      glMatrixMode(GL_MODELVIEW)
      self.libraryLabel.render()
      glMatrixMode(GL_TEXTURE)
      glLoadIdentity()
      glMatrixMode(GL_MODELVIEW)
      glDisable(GL_TEXTURE_2D)
    glDisable(GL_NORMALIZE)


#MFH - need to render the Career Resetter (with new function so future expansion can include a label):
  def renderCareerResetter(self, color, label):
    if not self.libraryMesh:
      return

    if color:
      glColor3f(*color)

    glEnable(GL_NORMALIZE)
    glEnable(GL_COLOR_MATERIAL)
    self.libraryMesh.render("Mesh_001")
    glColor3f(.1, .1, .1)
    self.libraryMesh.render("Mesh")

    # Draw the label if there is one
    if label is not None:
      glEnable(GL_TEXTURE_2D)
      label.bind()
      glColor3f(1, 1, 1)
      glMatrixMode(GL_TEXTURE)
      glScalef(1, -1, 1)
      glMatrixMode(GL_MODELVIEW)
      self.libraryLabel.render()
      glMatrixMode(GL_TEXTURE)
      glLoadIdentity()
      glMatrixMode(GL_MODELVIEW)
      glDisable(GL_TEXTURE_2D)
    glDisable(GL_NORMALIZE)


  
  def render(self, visibility, topMost):
    v = (1 - visibility) ** 2

    # render the background
    t = self.time / 100
    
    self.engine.view.setViewport(1,0)
    w, h, = self.engine.view.geometry[2:4]
    r = .5

    if self.display:
      #MFH - auto background image scaling
      imgwidth = self.background.width1()
      wfactor = 640.000/imgwidth
      self.background.transform.reset()
      self.background.transform.translate(w/2,h/2)
      self.background.transform.scale(wfactor,-wfactor)
      self.background.draw()  
    else:
      imgwidth = self.paper.width1()
      wfactor = 640.000/imgwidth
      if self.background != None:
        self.background.transform.reset()
        self.background.transform.translate(w/2,h/2)
        self.background.transform.scale(.5,-.5)
        self.background.draw()
      else:
        self.background = None 

      self.paper.transform.reset()
      if self.songback:
      # evilynux - Fixed, there's a two song offset and two lines should be skipped
        if self.selectedIndex == 1 or self.selectedIndex == 2:
          y = 0
        else:
          y = h*(self.selectedIndex-2)*2/16
        self.paper.transform.translate(w/2,y + h/2)
      else:
        self.paper.transform.translate(w/2,h/2)
      self.paper.transform.scale(wfactor,-wfactor) 
      self.paper.draw()  

      #racer: render preview graphic
    if self.previewDisabled == True and self.preview != None:
      self.preview.transform.reset()
      self.preview.transform.translate(w/2,h/2)
      self.preview.transform.scale(.5,-.5)
      self.preview.draw()
    else:
      self.preview = None



  

    #MFH - initializing these local variables so no "undefined" crashes result
    text = ""  
    notesTotal = 0    
    notesHit = 0
    noteStreak = 0

    if self.instrumentChange:
      self.instrumentChange = False
      if self.instrument == "Lead Guitar":
        self.instrument = "Drums"
        self.engine.config.set("game", "songlist_instrument", 4)
      elif self.instrument == "Bass Guitar":
        self.instrument = "Lead Guitar"
        self.engine.config.set("game", "songlist_instrument", 3)
      elif self.instrument == "Rhythm Guitar":
        self.instrument = "Bass Guitar"
        self.engine.config.set("game", "songlist_instrument", 2)
      elif self.instrument == "Guitar":
        self.instrument = "Rhythm Guitar"
        self.engine.config.set("game", "songlist_instrument", 1)
      else: # self.diff == 0:
        self.instrument = "Guitar"
        self.engine.config.set("game", "songlist_instrument", 0)

    if self.display:
    # render the item list
      try:
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()

        #myfingershurt: indentation was screwy here
        glLoadIdentity()
        gluPerspective(60, self.engine.view.aspectRatio, 0.1, 1000)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
            
        glEnable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)
        glDepthMask(1)
            
        offset = 10 * (v ** 2)
        
        #self.camera.origin = (-10 + offset, -self.cameraOffset, 4   + offset)
        #self.camera.target = (  0 + offset, -self.cameraOffset, 2.5 + offset)

        #Blazingamer's CD X position fix        
        self.camera.origin = (-10 + offset, -self.cameraOffset, 4   - self.song_cd_xpos + offset)
        self.camera.target = (  0 + offset, -self.cameraOffset, 2.5 - self.song_cd_xpos + offset)

        
        self.camera.apply()
            
        y = 0.0
        for i, item in enumerate(self.items):

          if not self.matchesSearch(item):
            continue
        
          c = math.sin(self.itemAngles[i] * math.pi / 180)
        
          if isinstance(item, Song.SongInfo):
            h = c * self.cassetteWidth + (1 - c) * self.cassetteHeight
          elif isinstance(item, Song.LibraryInfo):
            h = c * self.libraryWidth + (1 - c) * self.libraryHeight
          elif isinstance(item, Song.TitleInfo):
            h = c * self.titleWidth + (1 - c) * self.titleHeight
          elif isinstance(item, Song.CareerResetterInfo):
            h = c * self.titleWidth + (1 - c) * self.titleHeight
          elif isinstance(item, Song.BlankSpaceInfo):
            h = c * self.titleWidth + (1 - c) * self.titleHeight


        
          d = (y + h * .5 + self.camera.origin[1]) / (4 * (self.camera.target[2] - self.camera.origin[2]))
  
          if i == self.selectedIndex:
            self.selectedOffset = y + h / 2
            Theme.setSelectedColor()
          else:
            Theme.setBaseColor()
          
          #MFH - I think this is where CD songs are positioned --- Nope!
          glTranslatef(0, -h / 2, 0)
          #glTranslatef(self.song_cd_xpos, -h / 2, 0)
          
        
          glPushMatrix()
          if abs(d) < 1.2:
            if isinstance(item, Song.SongInfo):
              glRotate(self.itemAngles[i], 0, 0, 1)
              self.renderCassette(item.cassetteColor, self.itemLabels[i])
            elif isinstance(item, Song.LibraryInfo):
              #myfingershurt: cd cases are backwards
              glRotate(-self.itemAngles[i], 0, 1, 0)    #spin 90 degrees around y axis
              glRotate(-self.itemAngles[i], 0, 1, 0)    #spin 90 degrees around y axis again, now case is corrected
              glRotate(-self.itemAngles[i], 0, 0, 1)    #bring cd case up for viewing
              if i == self.selectedIndex and self.rotationDisabled == False:
                glRotate(((self.time - self.lastTime) * 4 % 360) - 90, 1, 0, 0)
              self.renderLibrary(item.color, self.itemLabels[i])
            elif isinstance(item, Song.TitleInfo):
              #myfingershurt: cd cases are backwards
              glRotate(-self.itemAngles[i], 0, 0.5, 0)    #spin 90 degrees around y axis
              glRotate(-self.itemAngles[i], 0, 0.5, 0)    #spin 90 degrees around y axis again, now case is corrected
              glRotate(-self.itemAngles[i], 0, 0, 0.5)    #bring cd case up for viewing
              if i == self.selectedIndex and self.rotationDisabled == False:
                glRotate(((self.time - self.lastTime) * 4 % 360) - 90, 1, 0, 0)
              self.renderTitle(item.color, self.itemLabels[i])
            elif isinstance(item, Song.CareerResetterInfo):
              #myfingershurt: cd cases are backwards
              glRotate(-self.itemAngles[i], 0, 0.5, 0)    #spin 90 degrees around y axis
              glRotate(-self.itemAngles[i], 0, 0.5, 0)    #spin 90 degrees around y axis again, now case is corrected
              glRotate(-self.itemAngles[i], 0, 0, 0.5)    #bring cd case up for viewing
              if i == self.selectedIndex and self.rotationDisabled == False:
                glRotate(((self.time - self.lastTime) * 4 % 360) - 90, 1, 0, 0)
              self.renderCareerResetter(item.color, self.itemLabels[i])


          glPopMatrix()
        
          glTranslatef(0, -h / 2, 0)
          y += h
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)
        glDepthMask(0)
      
      finally:
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
    
      # render the song info
      self.engine.view.setOrthogonalProjection(normalize = True)
      font = self.engine.data.font
      # evilynux - GH theme? Use not-outlined font. Beware, RbMFH doesn't have any lfont!
      if self.theme == 0 or self.theme == 1:
        lfont = self.engine.data.lfont
      else:
        lfont = font
    
      try:
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_COLOR_MATERIAL)
        Theme.setBaseColor(1 - v)

        if self.searchText:
          text = _("Filter: %s") % (self.searchText) + "|"
          if not self.matchesSearch(self.items[self.selectedIndex]):
            text += " (%s)" % _("Not found")
          font.render(text, (.05, .7 + v), scale = 0.001)
        elif self.songLoader:
          font.render(_("Loading Preview..."), (.05, .7 + v), scale = 0.001)

        #x = .6
        x = self.song_cdscore_xpos
        y = .15
        font.render(self.prompt, (x, .05 - v))

        Theme.setSelectedColor(1 - v)

        c1,c2,c3 = self.song_name_selected_color
        glColor3f(c1,c2,c3)
        
        item  = self.items[self.selectedIndex]

        if self.matchesSearch(item):
          angle = self.itemAngles[self.selectedIndex]
          f = ((90.0 - angle) / 90.0) ** 2

          cText = item.name
          if (isinstance(item, Song.SongInfo) and item.getLocked()):
            cText = _("-- Locked --")

          # evilynux - Use font w/o outline
          pos = wrapText(lfont, (x, y), cText, visibility = f, scale = 0.0016)

          if isinstance(item, Song.SongInfo):
            Theme.setBaseColor(1 - v)

            c1,c2,c3 = self.artist_selected_color
            glColor3f(c1,c2,c3)
            
            if not item.year == "":
              yeartag = ", "+item.year
            else:
              yeartag = ""
            
            cText = item.artist + yeartag
            if (item.getLocked()):
              cText = "" # avoid giving away artist of locked song
            
            # evilynux - Use font w/o outline
            pos = wrapText(lfont, (x, pos[1] + font.getHeight() * 0.0016), cText, visibility = f, scale = 0.0016)

            if item.count:
              Theme.setSelectedColor(1 - v)

              c1,c2,c3 = self.song_name_selected_color
              glColor3f(c1,c2,c3)

              count = int(item.count)
              if count == 1: 
                text = _("Played %d time") % count
              else:
                text = _("Played %d times") % count

              if item.getLocked():
                text = item.getUnlockText()
              elif self.careerMode and not item.completed:
                text = _("Play To Advance.")
              # evilynux - small text, use font w/o outline, else unreadable
              pos = wrapText(lfont, (x, pos[1] + font.getHeight() * 0.0016), text, visibility = f, scale = 0.001)
            else:
              if item.getLocked():
                text = item.getUnlockText()
              elif self.careerMode and not item.completed:
                text = _("Play To Advance.")
              # evilynux - small text, use font w/o outline, else unreadable
              pos = wrapText(lfont, (x, pos[1] + font.getHeight() * 0.0016), text, visibility = f, scale = 0.001)

            Theme.setSelectedColor(1 - v)

            c1,c2,c3 = self.song_name_selected_color
            glColor3f(c1,c2,c3)

            scale = 0.0011
            w, h = font.getStringSize(self.prompt, scale = scale)
            
            #x = .6
            x = self.song_cdscore_xpos
            y = .5 + f / 2.0
            if len(item.difficulties) > 3:
              y = .42 + f / 2.0
            
            for p in item.parts:    #MFH - look at selected instrument!
              if str(p) == self.instrument:
                for d in item.difficulties:
                  scores = item.getHighscores(d)
                  if scores:
                    score, stars, name, scoreExt = scores[0]
                    notesHit, notesTotal, noteStreak, modVersion, modOptions1, modOptions2 = scoreExt
                  else:
                    score, stars, name = "---", 0, "---"
                  Theme.setBaseColor(1 - v)
                  font.render(unicode(d),     (x, y),           scale = scale)
                  # evilynux - Fixed star size following Font render bugfix
                  if stars == 6 and self.theme == 2:    #gold stars in RB songlist
                    glColor3f(1, 1, 0)  
                    font.render(unicode(Data.STAR2 * (stars -1)), (x, y + h), scale = scale * 1.8)
                  elif stars == 6:
                    glColor3f(0, 1, 0)  
                    font.render(unicode(Data.STAR2 * (stars -1)), (x, y + h), scale = scale * 1.8)
                  else:
                    font.render(unicode(Data.STAR2 * stars + Data.STAR1 * (5 - stars)), (x, y + h), scale = scale * 1.8)
                  Theme.setSelectedColor(1 - v)
                  # evilynux - Also use hit%/noteStreak SongList option
                  if scores:
                    if self.extraStats:
                      if notesTotal != 0:
                        score = "%s %.1f%%" % (score, (float(notesHit) / notesTotal) * 100.0)
                      if noteStreak != 0:
                        score = "%s (%d)" % (score, noteStreak)
                  font.render(unicode(score), (x + .15, y),     scale = scale)
                  font.render(name,       (x + .15, y + h),     scale = scale)
                  y += 2 * h + f / 4.0
          elif isinstance(item, Song.LibraryInfo):
            Theme.setBaseColor(1 - v)

            c1,c2,c3 = self.library_selected_color
            glColor3f(c1,c2,c3)

            if item.songCount == 1:
              songCount = _("One Song In This Setlist")
            else:
              songCount = _("%d Songs In This Setlist") % item.songCount
            if item.songCount > 0:
              wrapText(font, (x, pos[1] + 3 * font.getHeight() * 0.0016), songCount, visibility = f, scale = 0.0016)

          elif isinstance(item, Song.CareerResetterInfo):
            Theme.setBaseColor(1 - v)

            c1,c2,c3 = self.career_title_color
            glColor3f(c1,c2,c3)

            careerResetText = _("Reset this entire career")
            wrapText(font, (x, pos[1] + 3 * font.getHeight() * 0.0016), careerResetText, visibility = f, scale = 0.0016)


        #MFH CD list
        text = self.instrument
        scale = 0.00250
        #glColor3f(1, 1, 1)
        c1,c2,c3 = self.song_name_selected_color
        glColor3f(c1,c2,c3)
        w, h = font.getStringSize(text, scale=scale)
        font.render(text, (0.95-w, 0.000), scale=scale)




      finally:
        self.engine.view.resetProjection()
        nuttin = True
    
    else:   #MFH - song List display
      if self.theme == 0 or self.theme == 1:
        # render the song info
        self.engine.view.setOrthogonalProjection(normalize = True)
        font = self.engine.data.songListFont
        lfont = self.engine.data.songListFont
        sfont = self.engine.data.shadowfont
        #font = self.engine.data.font
        #lfont = self.engine.data.lfont
      
        try:
          glEnable(GL_BLEND)
          glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
          glEnable(GL_COLOR_MATERIAL)
          Theme.setBaseColor(0)

          for i, item in enumerate(self.items):
            maxIndex = i

          if self.selectedIndex == 0:#Selection is first item in list
            pos = (self.selectedIndex, self.selectedIndex +5)
            y = h*0.63
          elif self.selectedIndex == 1:#Second item in list
            pos = (self.selectedIndex-1, self.selectedIndex+4)
            y = h*0.5
          elif self.selectedIndex == maxIndex-1:#Second to last item in list
            pos = (self.selectedIndex-3, self.selectedIndex+2)
            y = h*0.26
          elif self.selectedIndex == maxIndex and not self.selectedIndex == 2:#Last in list and not third item
            pos = (self.selectedIndex-4, self.selectedIndex+1)
            y = h*0.13
          else:
            pos = (self.selectedIndex-2, self.selectedIndex+3)#Any other item than above
            y = h*0.38

          #Render the selection grahics
          wfactor = self.selected.widthf(pixelw = 635.000)
          self.selected.transform.reset()
          self.selected.transform.scale(wfactor,-wfactor)
          self.selected.transform.translate(w/2.1, y-h*.01)
          self.selected.draw()

          #Render current library path
          glColor4f(1,1,1,1)
          text = self.library
          w, h = font.getStringSize(text)

          if self.filepathenable:
            font.render(text, (self.song_list_xpos, .19))


          #Render song list items
          glColor4f(1,1,1,1)
          for i, item in enumerate(self.items):
            if i >= pos[0] and i < pos[1]:

              if isinstance(item, Song.SongInfo):
                c1,c2,c3 = self.song_name_selected_color
                glColor3f(c1,c2,c3)
                if i == self.selectedIndex:
                  if item.getLocked():
                    text = item.getUnlockText()
                  elif self.careerMode and not item.completed:
                    text = _("Play To Advance.")
                  elif self.gameMode1p == 1: #evilynux - Practice mode
                    text = _("Practice")
                  elif item.count:
                    count = int(item.count)
                    if count == 1: 
                      text = _("Played Once")
                    else:
                      text = _("Played %d times.") % count
                  else:
                    text = _("Quickplay")
              elif isinstance(item, Song.LibraryInfo):
                c1,c2,c3 = self.library_selected_color
                glColor3f(c1,c2,c3)
                if i == self.selectedIndex:
                  if item.songCount == 1:
                    text = _("There Is 1 Song In This Setlist")
                  elif item.songCount > 1:
                    text = _("There are %d songs in this folder" % (item.songCount))
                  else:
                    text = ""

              elif isinstance(item, Song.TitleInfo):
                text = _("Tier")
                c1,c2,c3 = self.career_title_color
                glColor3f(c1,c2,c3)

              elif isinstance(item, Song.CareerResetterInfo):
                text = _("Reset this entire career")
                c1,c2,c3 = self.career_title_color
                glColor3f(c1,c2,c3)


              if i == self.selectedIndex:
                font.render(text, (self.song_list_xpos, .15))

              
              if i == self.selectedIndex:
                glColor4f(.7,.5,.25,1)
                if isinstance(item, Song.SongInfo):
                  c1,c2,c3 = self.song_name_selected_color
                  glColor3f(c1,c2,c3)
                if isinstance(item, Song.LibraryInfo):
                  c1,c2,c3 = self.library_selected_color
                  glColor3f(c1,c2,c3)
                if isinstance(item, Song.TitleInfo):
                  c1,c2,c3 = self.career_title_color
                  glColor3f(c1,c2,c3)
                if isinstance(item, Song.CareerResetterInfo):
                  c1,c2,c3 = self.career_title_color
                  glColor3f(c1,c2,c3)
                if isinstance(item, Song.BlankSpaceInfo):
                  c1,c2,c3 = self.career_title_color
                  glColor3f(c1,c2,c3)
              else:
                glColor4f(0,0,0,1)
                if isinstance(item, Song.SongInfo):
                  c1,c2,c3 = self.song_name_text_color
                  glColor3f(c1,c2,c3)
                if isinstance(item, Song.LibraryInfo):
                  c1,c2,c3 = self.library_text_color
                  glColor3f(c1,c2,c3)
                if isinstance(item, Song.TitleInfo):
                  c1,c2,c3 = self.career_title_color
                  glColor3f(c1,c2,c3)
                if isinstance(item, Song.CareerResetterInfo):
                  c1,c2,c3 = self.career_title_color
                  glColor3f(c1,c2,c3)
                if isinstance(item, Song.BlankSpaceInfo):
                  c1,c2,c3 = self.career_title_color
                  glColor3f(c1,c2,c3)
              text = item.name
              
              if isinstance(item, Song.SongInfo) and item.getLocked():
                text = _("-- Locked --")
              
              if isinstance(item, Song.SongInfo): #MFH - add indentation when tier sorting
                if self.tiersArePresent:
                  text = self.indentString + text
              
              # evilynux - Force uppercase display for Career titles
              if isinstance(item, Song.TitleInfo):
                text = string.upper(text)

              #MFH: ...and also for the Career Resetter, to help set it apart
              if isinstance(item, Song.CareerResetterInfo):
                text = string.upper(text)

              if isinstance(item, Song.BlankSpaceInfo):   #for the End of Career marker
                text = string.upper(text)


              w, h = font.getStringSize(text)
              if i == self.selectedIndex:
                sfont.render(text, (self.song_list_xpos, .0935*(i+1)-pos[0]*.0935+.15))
              else:
                lfont.render(text, (self.song_list_xpos, .0935*(i+1)-pos[0]*.0935+.15))

      
              #MFH - Song list score / info display:
              if isinstance(item, Song.SongInfo) and not item.getLocked():
                scale = 0.0009
                text = self.diff
                w, h = font.getStringSize(text, scale=scale)
                # evilynux - score color
                c1,c2,c3 = self.songlist_score_color
                glColor3f(c1,c2,c3)
                # evilynux - tweaked position to fit hit% and note streak
                if self.extraStats:
                  lfont.render(text, (self.song_listscore_xpos-w/2, .0935*(i+1)-pos[0]*.0935+.1575-h/2), scale=scale)
                else:
                  lfont.render(text, (self.song_listscore_xpos-w/2, .0935*(i+1)-pos[0]*.0935+.2-h/2), scale=scale)
                if not item.frets == "":
                  suffix = ", ("+item.frets+")"
                else:
                  suffix = ""

                if not item.year == "":
                  yeartag = ", "+item.year
                else:
                  yeartag = ""


                scale = .0014
                glColor4f(.25,.5,1,1)

                if i == self.selectedIndex:
                  c1,c2,c3 = self.artist_selected_color
                else:
                  c1,c2,c3 = self.artist_text_color
                glColor3f(c1,c2,c3)

                # evilynux - Force uppercase display for artist name
                text = string.upper(item.artist)+suffix+yeartag
                
                w, h = font.getStringSize(text, scale=scale)
                lfont.render(text, (self.song_list_xpos+.05, .0935*(i+1)-pos[0]*.0935+.2), scale=scale)

                if self.scoreTimer == 0 and self.highScoreType == 0: #racer: regular-style highscore movement
                  if self.diff == "Easy":
                    self.diff = "Medium"
                  elif self.diff == "Medium":
                    self.diff = "Hard"
                  elif self.diff == "Hard":
                    self.diff = "Expert"
                  elif self.diff == "Expert":
                    self.diff = "Easy"

                #racer: score can be changed by fret button:
                #MFH - and now they will be remembered as well
                if self.highScoreChange == True and self.highScoreType == 1:
                  if self.diff == "Easy":
                    self.diff = "Medium"
                    self.engine.config.set("game", "songlist_difficulty", 2)
                    self.highScoreChange = False
                  elif self.diff == "Medium":
                    self.diff = "Hard"
                    self.engine.config.set("game", "songlist_difficulty", 1)
                    self.highScoreChange = False
                  elif self.diff == "Hard":
                    self.diff = "Expert"
                    self.engine.config.set("game", "songlist_difficulty", 0)
                    self.highScoreChange = False
                  elif self.diff == "Expert":
                    self.diff = "Easy"
                    self.engine.config.set("game", "songlist_difficulty", 3)
                    self.highScoreChange = False

                score = _("Nil")
                stars = 0
                name = ""
                
                for p in item.parts:    #MFH - look at selected instrument!
                  if str(p) == self.instrument:
                    for d in item.difficulties:
                      if str(d) == self.diff:
                        scores = item.getHighscores(d)
                        if scores:
                          score, stars, name, scoreExt = scores[0]
                          notesHit, notesTotal, noteStreak, modVersion, modOptions1, modOptions2 = scoreExt
                        else:
                          score, stars, name = 0, 0, "---"

                #QQstarS:add  to show stars
                if stars == 6:
                  glColor3f(1, 1, 1)  
                  if self.extraStats:
                    lfont.render(unicode(Data.STAR2 * (stars -1)), (self.song_listscore_xpos+.018, .0935*(i+1)-pos[0]*.0935+.1825-0.034), scale = scale * 1.8) #was scale 2.8
                  else:
                    lfont.render(unicode(Data.STAR2 * (stars -1)), (self.song_listscore_xpos+.018, .0935*(i+1)-pos[0]*.0935+.2-0.034), scale = scale * 1.8) #was scale 2.8
                elif score>0 and stars>=0 and name!="":
                  glColor3f(1, 1, 1)
                  #ShiekOdaSandz: Fixed stars so they display left to right, not right to left
                  if self.extraStats:
                    lfont.render(unicode(Data.STAR2 * stars+Data.STAR1 * (5 - stars)), (self.song_listscore_xpos+.018, .0935*(i+1)-pos[0]*.0935+.1825-0.034), scale = scale * 1.8) #was scale 2.8 #ShiekOdaSandz: Fixed stars so they display left to right, not right to left
                  else:
                    lfont.render(unicode(Data.STAR2 * stars+Data.STAR1 * (5 - stars)), (self.song_listscore_xpos+.018, .0935*(i+1)-pos[0]*.0935+.2-0.034), scale = scale * 1.8) #was scale 2.8 #ShiekOdaSandz: Fixed stars so they display left to right, not right to left
                  #QQstarS: end of add

                scale = 0.0014
                # evilynux - score color
                c1,c2,c3 = self.songlist_score_color
                glColor3f(c1,c2,c3)
                # evilynux - hit% and note streak only if enabled
                if self.extraStats:
                  if score is not _("Nil") and score > 0 and notesTotal != 0:
                    text = "%.1f%% (%d)" % ((float(notesHit) / notesTotal) * 100.0, noteStreak)
                    w, h = font.getStringSize(text, scale=scale)
                    lfont.render(text, (self.song_listscore_xpos+.1-w, .0935*(i+1)-pos[0]*.0935+.1725), scale=scale)

                text = str(score)
                w, h = font.getStringSize(text, scale=scale)
                if score > 0 and score!=_("Nil"): #QQstarS: score >0 that have the back color
                  # evilynux - No more outline
                  lfont.render(text, (self.song_listscore_xpos+.1-w, .0935*(i+1)-pos[0]*.0935+.2), scale=scale)
                else: #QQstarS: 
                  lfont.render(text, (self.song_listscore_xpos+.1-w, .0935*(i+1)-pos[0]*.0935+.2), scale=scale)

                if self.scoreTimer < 1000:
                  self.scoreTimer += 1
                else:
                  self.scoreTimer = 0
            
        finally:
        #  self.engine.view.resetProjection()
          nuttin = True
      
      elif self.theme == 2: # RbMFH
        # render the song info
        self.engine.view.setOrthogonalProjection(normalize = True)
        #font = self.engine.data.font
        font = self.engine.data.songListFont
      
        try:
          glEnable(GL_BLEND)
          glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
          glEnable(GL_COLOR_MATERIAL)
          Theme.setBaseColor(0)

          for i, item in enumerate(self.items):
            maxIndex = i

          if self.selectedIndex == 0:
            pos = (self.selectedIndex, self.selectedIndex +5)
            y = h*0.63
          elif self.selectedIndex == 1:
            pos = (self.selectedIndex-1, self.selectedIndex+4)
            y = h*0.5
          elif self.selectedIndex == maxIndex-1:
            pos = (self.selectedIndex-3, self.selectedIndex+2)
            y = h*0.26
          elif self.selectedIndex == maxIndex and not self.selectedIndex == 2:
            pos = (self.selectedIndex-4, self.selectedIndex+1)
            y = h*0.13
          else:
            pos = (self.selectedIndex-2, self.selectedIndex+3)
            y = h*0.38

          self.selected.transform.reset()
          self.selected.transform.scale(1,-1)
          self.selected.transform.translate(w/2.1, y-h*.01)
          self.selected.draw()

          glColor4f(1,1,1,1)
          text = self.library
          w, h = font.getStringSize(text)
          if self.filepathenable:
            font.render(text, (self.song_list_xpos, .19))
          
          for i, item in enumerate(self.items):
            if i >= pos[0] and i <= pos[1]:

              if isinstance(item, Song.SongInfo):
                c1,c2,c3 = self.song_name_selected_color
                glColor3f(c1,c2,c3)
                if i == self.selectedIndex:
                  if item.getLocked():
                    text = item.getUnlockText()
                  elif self.careerMode and not item.completed:
                    text = _("Play To Advance")
                  elif self.gameMode1p == 1: #evilynux - Practice mode
                    text = _("Practice")
                  elif item.count:
                    count = int(item.count)
                    if count == 1: 
                      text = _("Played Once")
                    else:
                      text = _("Played %d times.") % count
                  else:
                    text = _("Quickplay")
              elif isinstance(item, Song.LibraryInfo):
                c1,c2,c3 = self.library_selected_color
                glColor3f(c1,c2,c3)
                if i == self.selectedIndex:
                  if item.songCount == 1:
                    text = _("There Is 1 Song In This Setlist.")
                  elif item.songCount > 1:
                    text = _("There Are %d Songs In This Setlist." % (item.songCount))
                  else:
                    text = ""
              elif isinstance(item, Song.TitleInfo):
                text = _("Tier")
                c1,c2,c3 = self.career_title_color
                glColor3f(c1,c2,c3)
              elif isinstance(item, Song.CareerResetterInfo):
                text = _("Reset this entire career")
                c1,c2,c3 = self.career_title_color
                glColor3f(c1,c2,c3)

              if i == self.selectedIndex:
                w, h = font.getStringSize(text)
                font.render(text, (.5-w/2, .15))
              
              if i == self.selectedIndex:
                glColor4f(.7,.5,.25,1)
                if isinstance(item, Song.SongInfo):
                  c1,c2,c3 = self.song_name_selected_color
                  glColor3f(c1,c2,c3)
                if isinstance(item, Song.LibraryInfo):
                  c1,c2,c3 = self.library_selected_color
                  glColor3f(c1,c2,c3)
                if isinstance(item, Song.TitleInfo):
                  c1,c2,c3 = self.career_title_color
                  glColor3f(c1,c2,c3)
                if isinstance(item, Song.CareerResetterInfo):
                  c1,c2,c3 = self.career_title_color
                  glColor3f(c1,c2,c3)
                if isinstance(item, Song.BlankSpaceInfo):
                  c1,c2,c3 = self.career_title_color
                  glColor3f(c1,c2,c3)
              else:
                glColor4f(0,0,0,1)
                if isinstance(item, Song.SongInfo):
                  c1,c2,c3 = self.song_name_text_color
                  glColor3f(c1,c2,c3)
                if isinstance(item, Song.LibraryInfo):
                  c1,c2,c3 = self.library_text_color
                  glColor3f(c1,c2,c3)
                if isinstance(item, Song.TitleInfo):
                  c1,c2,c3 = self.career_title_color
                  glColor3f(c1,c2,c3)
                if isinstance(item, Song.CareerResetterInfo):
                  c1,c2,c3 = self.career_title_color
                  glColor3f(c1,c2,c3)
                if isinstance(item, Song.BlankSpaceInfo):
                  c1,c2,c3 = self.career_title_color
                  glColor3f(c1,c2,c3)
              text = item.name

              if isinstance(item, Song.SongInfo) and item.getLocked():
                text = _("-- Locked --")

              if isinstance(item, Song.SongInfo): #MFH - add indentation when tier sorting
                if self.tiersArePresent:
                  text = self.indentString + text

              # evilynux - Force uppercase display for Career titles
              if isinstance(item, Song.TitleInfo):
                text = string.upper(text)

              #MFH: ...and also for the Career Resetter, to help set it apart
              if isinstance(item, Song.CareerResetterInfo):
                text = string.upper(text)

              if isinstance(item, Song.BlankSpaceInfo):
                text = string.upper(text)

              
              w, h = font.getStringSize(text)
              font.render(text, (self.song_list_xpos, .0935*(i+1)-pos[0]*.0935+.15))

              if isinstance(item, Song.SongInfo) and not item.getLocked():
                scale = 0.0009
                text = self.diff
                w, h = font.getStringSize(text, scale=scale)
                # evilynux - score color
                c1,c2,c3 = self.songlist_score_color
                glColor3f(c1,c2,c3)
                if self.extraStats:
                  # evilynux - tweaked position to fit hit% and note streak
                  font.render(text, (self.song_listscore_xpos-w/2, .0935*(i+1)-pos[0]*.0935+.1775-h/2), scale=scale)
                else:
                  font.render(text, (self.song_listscore_xpos-w/2, .0935*(i+1)-pos[0]*.0935+.2-h/2), scale=scale)
                
                if not item.frets == "":
                  suffix = ", ("+item.frets+")"
                else:
                  suffix = ""
                
                if not item.year == "":
                  yeartag = ", "+item.year
                else:
                  yeartag = ""
                
                  
                scale = .0014
                glColor4f(.25,.5,1,1)

                if i == self.selectedIndex:
                  c1,c2,c3 = self.artist_selected_color
                else:
                  c1,c2,c3 = self.artist_text_color
                glColor3f(c1,c2,c3)

                # evilynux - Force uppercase display for artist name
                text = string.upper(item.artist)+suffix+yeartag


                w, h = font.getStringSize(text, scale=scale)
                font.render(text, (self.song_list_xpos+.05, .0935*(i+1)-pos[0]*.0935+.2), scale=scale)

                if self.scoreTimer == 0 and self.highScoreType == 0: #racer: regular-style highscore movement
                  if self.diff == "Easy":
                    self.diff = "Medium"
                  elif self.diff == "Medium":
                    self.diff = "Hard"
                  elif self.diff == "Hard":
                    self.diff = "Expert"
                  elif self.diff == "Expert":
                    self.diff = "Easy"

                #racer: score can be changed by fret button:
                #MFH - and now they will be remembered as well
                if self.highScoreChange == True and self.highScoreType == 1:
                  if self.diff == "Easy":
                    self.diff = "Medium"
                    self.engine.config.set("game", "songlist_difficulty", 2)
                    self.highScoreChange = False
                  elif self.diff == "Medium":
                    self.diff = "Hard"
                    self.engine.config.set("game", "songlist_difficulty", 1)
                    self.highScoreChange = False
                  elif self.diff == "Hard":
                    self.diff = "Expert"
                    self.engine.config.set("game", "songlist_difficulty", 0)
                    self.highScoreChange = False
                  elif self.diff == "Expert":
                    self.diff = "Easy"
                    self.engine.config.set("game", "songlist_difficulty", 3)
                    self.highScoreChange = False

                score = _("Nil")
                stars = 0
                name = ""
                
                for p in item.parts:    #MFH - look at selected instrument!
                  if str(p) == self.instrument:
                    for d in item.difficulties:
                      if str(d) == self.diff:
                        scores = item.getHighscores(d)
                        if scores:
                          score, stars, name, scoreExt = scores[0]
                          notesHit, notesTotal, noteStreak, modVersion, modOptions1, modOptions2 = scoreExt
                        else:
                          score, stars, name = 0, 0, "---"

                #QQstarS:add  to show stars
                # evilynux - Tweaked position to fit hit% and note streak
                #            Readjusted star size following font fix
                if stars == 6:
                  glColor3f(1, 1, 0)    #gold stars in RB theme
                  if self.extraStats:
                    font.render(unicode(Data.STAR2 * (stars -1)), (self.song_listscore_xpos+.018, .0935*(i+1)-pos[0]*.0935+.18-0.0145), scale = scale * 1.8)
                  else:
                    font.render(unicode(Data.STAR2 * (stars -1)), (self.song_listscore_xpos+.018, .0935*(i+1)-pos[0]*.0935+.2-0.0145), scale = scale * 1.8)
                elif score>0 and stars>=0 and name!="":
                  glColor3f(1, 1, 1)
                  # ShiekOdaSandz: Fixed stars so they display left to right, not right to left
                  if self.extraStats:
                    font.render(unicode(Data.STAR2 * stars+Data.STAR1 * (5 - stars)), (self.song_listscore_xpos+.018, .0935*(i+1)-pos[0]*.0935+.18-0.0145), scale = scale * 1.8)
                  else:
                    font.render(unicode(Data.STAR2 * stars+Data.STAR1 * (5 - stars)), (self.song_listscore_xpos+.018, .0935*(i+1)-pos[0]*.0935+.2-0.0145), scale = scale * 1.8)#ShiekOdaSandz: Fixed stars so they display left to right, not right to left
                #QQstarS: end of add

                scale = 0.0014
                # evilynux - score color
                c1,c2,c3 = self.songlist_score_color
                glColor3f(c1,c2,c3)
                #evilynux - hit% and note streak if enabled
                if self.extraStats:
                  if score is not _("Nil") and score > 0 and notesTotal != 0:
                    text = "%.1f%% (%d)" % ((float(notesHit) / notesTotal) * 100.0, noteStreak)
                    # evilynux - changed positions a little for nice note streak integration
                    w, h = font.getStringSize(text, scale=scale)
                    font.render(text, (self.song_listscore_xpos+.11-w, .0935*(i+1)-pos[0]*.0935+.1825), scale=scale)

                text = str(score)
                w, h = font.getStringSize(text, scale=scale)

                # evilynux - changed positions a little for nice note streak integration
                font.render(text, (self.song_listscore_xpos+.11-w, .0935*(i+1)-pos[0]*.0935+.205), scale=scale)

                if self.scoreTimer < 1000:
                  self.scoreTimer += 1
                else:
                  self.scoreTimer = 0
      
      
            
        finally:
        #  self.engine.view.resetProjection()
          nuttin = True
      
      #MFH - after songlist / CD and theme conditionals - common executions
      text = self.instrument
      scale = 0.00250
      glColor3f(1, 1, 1)
      w, h = font.getStringSize(text, scale=scale)
      font.render(text, (0.85-w, 0.10), scale=scale)

      self.engine.view.resetProjection()
          
class FileChooser(BackgroundLayer, KeyListener):
  """File choosing layer."""
  def __init__(self, engine, masks, path, prompt = "", dirSelect = False):
    self.masks          = masks
    self.path           = path
    self.prompt         = prompt
    self.engine         = engine
    self.accepted       = False
    self.selectedFile   = None
    self.time           = 0.0
    self.menu           = None

    Log.debug("FileChooser class init (Dialogs.py)...")
    

    self.dirSelect      = dirSelect
    self.spinnyDisabled = self.engine.config.get("game", "disable_spinny")

    #Get theme
    themename = self.engine.data.themeLabel
    #now theme determination logic is only in data.py:
    self.theme = self.engine.data.theme

   #MFH - added simple black background to place in front of Options background, behind Neck BG, for transparent neck displays
    try:
      self.engine.loadImgDrawing(self, "neckBlackBack", ("neckblackback.png"))
    except IOError:
      self.neckBlackBack = None


    self.engine.loadImgDrawing(self, "background", os.path.join("themes",themename,"editor.png"))
    
  def _getFileCallback(self, fileName):
    return lambda: self.chooseFile(fileName)

  def _getFileText(self, fileName):
    f = os.path.join(self.path, fileName)
    if fileName == "..":
      return _("[Parent Folder]")
    if self.dirSelect == True:
      for mask in self.masks:
        if fnmatch.fnmatch(fileName, mask):
          return _("[Accept Folder]")
    if os.path.isdir(f):
      return _("%s [Folder]") % fileName
    return fileName

  def getFiles(self):
    files = [".."]
    for fn in os.listdir(self.path):
      if fn.startswith("."): continue
      f = os.path.join(self.path, fn)
      for mask in self.masks:
        if fnmatch.fnmatch(fn, mask):
          break
      else:
        if not os.path.isdir(f):
          continue
      files.append(fn)
    files.sort()
    if self.dirSelect == True and (fnmatch.fnmatch(self.path, self.masks[0])):
      files.insert(0, self.path)
    return files

  def getDisks(self):
    import win32file, string
    driveLetters=[]
    for drive in string.letters[len(string.letters) / 2:]:
      if win32file.GetDriveType(drive + ":") == win32file.DRIVE_FIXED:
        driveLetters.append(drive + ":\\")
    return driveLetters
  
  def updateFiles(self):
    if self.menu:
      self.engine.view.popLayer(self.menu)

    if self.path == "toplevel" and os.name != "nt":
      self.path = "/"
      
    if self.path == "toplevel":
      self.menu = Menu(self.engine, choices = [(self._getFileText(f), self._getFileCallback(f)) for f in self.getDisks()], onClose = self.close, onCancel = self.cancel)
    else:
      self.menu = Menu(self.engine, choices = [(self._getFileText(f), self._getFileCallback(f)) for f in self.getFiles()], onClose = self.close, onCancel = self.cancel)
    self.engine.view.pushLayer(self.menu)

  def chooseFile(self, fileName):
    if self.dirSelect == True:
      for mask in self.masks:
        if fnmatch.fnmatch(fileName, mask):
          self.selectedFile = fileName
          accepted = True
          self.engine.view.popLayer(self.menu)
          self.engine.view.popLayer(self)
          self.menu = None
          return

    if self.path == "toplevel":
      self.path = ""
    path = os.path.abspath(os.path.join(self.path, fileName))

    if os.path.isdir(path):

      if path == self.path and fileName == "..":
        self.path = "toplevel"
      else:
        self.path = path
      self.updateFiles()
      return
    self.selectedFile = path
    accepted = True
    self.engine.view.popLayer(self.menu)
    self.engine.view.popLayer(self)
    self.menu = None
    
  def cancel(self):
    self.accepted = True
    self.engine.view.popLayer(self)

  def close(self):
    if not self.menu:
      self.accepted = True
      self.engine.view.popLayer(self)
    
  def shown(self):
    self.updateFiles()
    
  def getSelectedFile(self):
    return self.selectedFile
  
  def run(self, ticks):
    self.time += ticks / 50.0
    
  def render(self, visibility, topMost):
    v = (1 - visibility) ** 2

    # render the background

    t = self.time / 100
    self.engine.view.setViewport(1,0)
    w, h, = self.engine.view.geometry[2:4]
    r = .5

    #MFH - draw neck black BG in for transparent areas (covers options BG):
    if self.neckBlackBack != None:
      #MFH - auto background scaling 
      imgwidth = self.neckBlackBack.width1()
      wfactor = 640.000/imgwidth
      self.neckBlackBack.transform.reset()
      self.neckBlackBack.transform.translate(w/2,h/2)
      self.neckBlackBack.transform.scale(wfactor,-wfactor)
      self.neckBlackBack.draw()  


    #MFH - auto background scaling 
    imgwidth = self.background.width1()
    wfactor = 640.000/imgwidth
    self.background.transform.reset()
    self.background.transform.translate(w/2,h/2)
    #self.background.transform.scale(1,-1)
    self.background.transform.scale(wfactor,-wfactor)
    self.background.draw()  


      
    self.engine.view.setOrthogonalProjection(normalize = True)
    font = self.engine.data.font
    
    try:
      glEnable(GL_BLEND)
      glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
      glEnable(GL_COLOR_MATERIAL)
      Theme.setBaseColor(1 - v)
      wrapText(font, (.1, .05 - v), self.prompt)
    finally:
      self.engine.view.resetProjection()




#==============================================================
#MFH - on-demand Neck Select menu
class NeckChooser(BackgroundLayer, KeyListener):
  """Item menu layer."""
  def __init__(self, engine, selected = None, prompt = ""):
    self.prompt         = prompt
    self.engine         = engine
    
    Log.debug("NeckChooser class init (Dialogs.py)...")
    
    splash = showLoadingSplashScreen(self.engine, _("Loading necks..."))

    self.neck = []
    self.necks = ["2none", "none"]
    self.maxNeck = 0
    self.selectedNeck = Config.get("coffee", "neck_choose")

    # evilynux - improved loading logic to support arbitrary filenames
    #          - os.listdir is not garanteed to return a sorted list, so sort it!
    neckfiles = os.listdir(self.engine.resource.fileName("necks"))
    neckfiles.sort()

    for i in neckfiles:
      # evilynux - Special cases, ignore these...
      #if( str(i) == "overdriveneck.png" or str(i)[-4:] != ".png" ):
      if( str(i) == "overdriveneck.png" or not i.endswith(".png") ):
        exists = 0
        continue
      try:
        neckImage = engine.loadImgDrawing(self, "neck"+str(i), os.path.join("necks",str(i)))
        # evilynux - Warning, Thumbs.db won't fail at engine.loadImgDrawing

      except IOError:
        exists = 0
        break
      else:
        # evilynux - Warning, pseudo valid images like Thumbs.db won't fail - we need to catch those bastards
        if neckImage is None:
         exists = 0
        else:
         exists = 1

      if exists == 1:
        self.neck.append(str(i)[:-4]) # evilynux - filename w/o extension
        self.necks.append(neckImage)
        self.maxNeck += 1
    self.maxNeck -= 1 # evilynux - confusing, but there's an offset of -1
    Config.define("coffee",   "neck_choose",         str,   0,  text = _("Neck"), options = self.neck)
    Config.set("coffee",   "max_neck", self.maxNeck)

    self.necks.append("none")
    self.necks.append("2none")
    
    self.accepted       = False
    self.time           = 0.0
    

    #Get theme
    self.themename = self.engine.data.themeLabel
    self.theme = self.engine.data.theme

   #MFH - added simple black background to place in front of Options background, behind Neck BG, for transparent neck displays
    try:
      self.engine.loadImgDrawing(self, "neckBlackBack", ("neckblackback.png"))
    except IOError:
      self.neckBlackBack = None

   
   
    self.engine.loadImgDrawing(self, "neckBG", os.path.join("themes",self.themename,"menu","neckchoosebg.png"))
    self.engine.loadImgDrawing(self, "neckSelect", os.path.join("themes",self.themename,"menu","neckchooseselect.png"))

    neckChooseSettings = [
      Settings.ConfigChoice(engine.config, "coffee",   "neck_choose", autoApply = True)
    ]
    self.menu = Menu(self.engine, neckChooseSettings, pos = (12,12), onClose = self.close, onCancel = self.cancel)

    # ready... hide the splash screen
    hideLoadingSplashScreen(self.engine, splash)
    splash = None




    
  def _callbackForNeck(self):
    def cb():
      self.chooseNeck()
    return cb
    
  def chooseNeck(self):
    #self.selectedNeck = neck
    accepted = True
    self.engine.view.popLayer(self.menu)
    self.engine.view.popLayer(self)
    
  def cancel(self):
    self.accepted = True
    self.engine.view.popLayer(self)

  def close(self):
    self.accepted = True
    self.engine.view.popLayer(self)
    
  def shown(self):
    self.engine.view.pushLayer(self.menu)
    
  def getSelectedNeck(self):
    return self.selectedNeck
  
  def run(self, ticks):
    self.time += ticks / 50.0
    
  def render(self, visibility, topMost):
   v = (1 - visibility) ** 2
   # render the background
   t = self.time / 100
   self.engine.view.setViewport(1,0)
   w, h, = self.engine.view.geometry[2:4]
   r = .5


   #MFH - draw neck black BG in for transparent necks (covers options BG):
   if self.neckBlackBack != None:
     #MFH - auto background scaling
     imgwidth = self.neckBlackBack.width1()
     wfactor = 640.000/imgwidth
     self.neckBlackBack.transform.reset()
     self.neckBlackBack.transform.translate(w/2,h/2)
     self.neckBlackBack.transform.scale(wfactor,-wfactor)
     self.neckBlackBack.draw()  



   self.selectedNeck = Config.get("coffee", "neck_choose")
   # evilynux - search for index number of selected neck
   found = False
   for i in range(len(self.neck)):
     # Second condition of the "if" is for backward compatibility
     if (str(self.selectedNeck) == self.neck[i]) or ("Neck_"+str(self.selectedNeck) == self.neck[i]):
       self.selectedNeck = i
       found = True
       break
   if not found:
     self.selectedNeck = 0

   currentNeck = self.necks[int(self.selectedNeck)+2]
   lastNeck1 = self.necks[int(self.selectedNeck)]
   if lastNeck1 == "none":
     lastNeck1 = self.necks[self.maxNeck+2]
   elif lastNeck1 == "2none":
     lastNeck1 = self.necks[self.maxNeck+1]
   lastNeck = self.necks[int(self.selectedNeck)+1]
   if lastNeck == "none":
     lastNeck = self.necks[self.maxNeck+2]

   nextNeck = self.necks[int(self.selectedNeck)+3]
   if nextNeck == "none":
     nextNeck = self.necks[2]
     
   nextNeck1 = self.necks[int(self.selectedNeck)+4]
   if nextNeck1 == "none":
     nextNeck1 = self.necks[2]
   elif nextNeck1 == "2none":
     nextNeck1 = self.necks[3]

   if self.theme == 2:
     self.x1 = w*0.067
     self.x2 = w*0.187
     self.x3 = w*0.307
     self.x4 = w*0.427
     self.x5 = w*0.547
     self.x6 = w*0.296
     self.y1 = h*0.420
     self.y2 = h*0.420
     self.y3 = h*0.420
     self.y4 = h*0.420
     self.y5 = h*0.420
     self.y6 = h*0.420
     self.wfac = 192.000
     self.wfac2 = 62.000  
   else:
     self.x1 = w*0.05
     self.x2 = w*0.175
     self.x3 = w*0.296
     self.x4 = w*0.42
     self.x5 = w*0.539
     self.x6 = w*0.296
     self.y1 = h*0.420
     self.y2 = h*0.554
     self.y3 = h*0.415
     self.y4 = h*0.554
     self.y5 = h*0.402
     self.y6 = h*0.423
     self.wfac = 187.000
     self.wfac2 = 64.000



   wfactor = currentNeck.widthf(pixelw = self.wfac)
   currentNeck.transform.reset()
   if self.theme != 2:
     currentNeck.transform.translate(w/1.31,h/2)
   else:
     currentNeck.transform.translate(w/1.22,h/2)
   currentNeck.transform.scale(-wfactor,wfactor)
   currentNeck.draw()

   wfactor = lastNeck1.widthf(pixelw = self.wfac2)
   lastNeck1.transform.reset()
   lastNeck1.transform.translate(self.x1,self.y1)
   lastNeck1.transform.scale(-wfactor,wfactor)
   lastNeck1.draw()
   wfactor = lastNeck.widthf(pixelw = self.wfac2)
   lastNeck.transform.reset()
   lastNeck.transform.translate(self.x2,self.y2)
   lastNeck.transform.scale(-wfactor,wfactor)
   lastNeck.draw()
   wfactor = currentNeck.widthf(pixelw = self.wfac2)
   currentNeck.transform.reset()
   currentNeck.transform.translate(self.x3,self.y3)
   currentNeck.transform.scale(-wfactor,wfactor)
   currentNeck.draw()
   wfactor = nextNeck.widthf(pixelw = self.wfac2)
   nextNeck.transform.reset()
   nextNeck.transform.translate(self.x4,self.y4)
   nextNeck.transform.scale(-wfactor,wfactor)
   nextNeck.draw()
   wfactor = nextNeck1.widthf(pixelw = self.wfac2)
   nextNeck1.transform.reset()
   nextNeck1.transform.translate(self.x5,self.y5)
   nextNeck1.transform.scale(-wfactor,wfactor)
   nextNeck1.draw()

   if self.menu.currentIndex == 0:
     self.neckSelect.transform.reset()
     self.neckSelect.transform.translate(self.x6, self.y6)
     self.neckSelect.transform.scale(-1,1)
     self.neckSelect.draw()

   #MFH - draw neck BG on top of necks
   #MFH - auto background scaling
   imgwidth = self.neckBG.width1()
   wfactor = 640.000/imgwidth
   self.neckBG.transform.reset()
   self.neckBG.transform.translate(w/2,h/2)
   self.neckBG.transform.scale(wfactor,-wfactor)
   self.neckBG.draw()  


     
   self.engine.view.setOrthogonalProjection(normalize = True)
   font = self.engine.data.font
   
   try:
     glEnable(GL_BLEND)
     glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
     glEnable(GL_COLOR_MATERIAL)
     Theme.setBaseColor(1 - v)
     wrapText(font, (.1, .05 - v), self.prompt)
   finally:
     self.engine.view.resetProjection()
   #==============================================================

    
    


class ItemChooser(BackgroundLayer, KeyListener):
  """Item menu layer."""
  def __init__(self, engine, items, selected = None, prompt = ""):
    self.prompt         = prompt
    self.engine         = engine
    
    Log.debug("ItemChooser class init (Dialogs.py)...")
    
    
    self.accepted       = False
    self.selectedItem   = None
    self.time           = 0.0
    self.menu = Menu(self.engine, choices = [(c, self._callbackForItem(c)) for c in items], onClose = self.close, onCancel = self.cancel)
    self.spinnyDisabled = self.engine.config.get("game", "disable_spinny")
    
    if selected and selected in items:
      self.menu.selectItem(items.index(selected))

    #Get theme
    themename = self.engine.data.themeLabel
    self.theme = self.engine.data.theme
    self.engine.loadImgDrawing(self, "background", os.path.join("themes",themename,"editor.png"))
    
  def _callbackForItem(self, item):
    def cb():
      self.chooseItem(item)
    return cb
    
  def chooseItem(self, item):
    self.selectedItem = item
    accepted = True
    self.engine.view.popLayer(self.menu)
    self.engine.view.popLayer(self)
    
  def cancel(self):
    self.accepted = True
    self.engine.view.popLayer(self)

  def close(self):
    self.accepted = True
    self.engine.view.popLayer(self)
    
  def shown(self):
    self.engine.view.pushLayer(self.menu)
    
  def getSelectedItem(self):
    return self.selectedItem
  
  def run(self, ticks):
    self.time += ticks / 50.0
    
  def render(self, visibility, topMost):
    v = (1 - visibility) ** 2

    # render the background
    t = self.time / 100
    self.engine.view.setViewport(1,0)
    w, h, = self.engine.view.geometry[2:4]
    r = .5
    


    #MFH - auto background scaling 
    imgwidth = self.background.width1()
    wfactor = 640.000/imgwidth
    self.background.transform.reset()
    self.background.transform.translate(w/2,h/2)
    #self.background.transform.scale(1,-1)
    self.background.transform.scale(wfactor,-wfactor)
    self.background.draw()  

      
    self.engine.view.setOrthogonalProjection(normalize = True)
    font = self.engine.data.font
    
    try:
      glEnable(GL_BLEND)
      glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
      glEnable(GL_COLOR_MATERIAL)
      Theme.setBaseColor(1 - v)
      wrapText(font, (.1, .05 - v), self.prompt)
    finally:
      self.engine.view.resetProjection()
      
      
class BpmEstimator(Layer, KeyListener):
  """Beats per minute value estimation layer."""
  def __init__(self, engine, song, prompt = ""):
    self.prompt         = prompt
    self.engine         = engine
    Log.debug("BpmEstimator class init (Dialogs.py)...")

    self.song           = song
    self.accepted       = False
    self.bpm            = None
    self.time           = 0.0
    self.beats          = []
    
    
  def shown(self):
    self.engine.input.addKeyListener(self, priority = True)
    self.song.play()
  
  def hidden(self):
    self.engine.input.removeKeyListener(self)
    self.song.fadeout(1000)
    
  def keyPressed(self, key, unicode):
    if self.accepted:
      return True
      
    c = self.engine.input.controls.getMapping(key)
    if key == pygame.K_SPACE:
      self.beats.append(self.time)
      if len(self.beats) > 12:
        diffs = [self.beats[i + 1] - self.beats[i] for i in range(len(self.beats) - 1)]
        self.bpm = 60000.0 / (sum(diffs) / float(len(diffs)))
        self.beats = self.beats[-12:]
    elif c in Player.CANCELS + Player.KEY2S:
      self.engine.view.popLayer(self)
      self.accepted = True
      self.bpm      = None
    elif c in Player.KEY1S or key == pygame.K_RETURN:
      self.engine.view.popLayer(self)
      self.accepted = True
      
    return True
  
  def run(self, ticks):
    self.time += ticks
    
  def render(self, visibility, topMost):
    v = (1 - visibility) ** 2
    
    self.engine.view.setViewport(1,0)
    self.engine.view.setOrthogonalProjection(normalize = True)
    font = self.engine.data.font
    
    fadeScreen(v)
          
    try:
      glEnable(GL_BLEND)
      glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
      glEnable(GL_COLOR_MATERIAL)
      Theme.setBaseColor(1 - v)
      wrapText(font, (.1, .2 - v), self.prompt)
      
      if self.bpm is not None:
        Theme.setSelectedColor(1 - v)
        wrapText(font, (.1, .5 + v),  _("%.2f beats per minute") % (self.bpm))
    finally:
      self.engine.view.resetProjection()
      
class KeyTester(Layer, KeyListener):
  """Keyboard configuration testing layer."""
  def __init__(self, engine, prompt = ""):
    self.prompt         = prompt
    self.engine         = engine
    
    Log.debug("KeyTester class init (Dialogs.py)...")
    
    
    self.accepted       = False
    self.time           = 0.0
    self.controls       = Player.Controls()
    self.fretColors     = Theme.fretColors
    
  def shown(self):
    self.engine.input.addKeyListener(self, priority = True)
  
  def hidden(self):
    self.engine.input.removeKeyListener(self)
    
  def keyPressed(self, key, unicode):
    if self.accepted:
      return True

    self.controls.keyPressed(key)
    c = self.engine.input.controls.getMapping(key)
    if c in Player.CANCELS:
      self.engine.view.popLayer(self)
      self.accepted = True
    return True

  def keyReleased(self, key):
    self.controls.keyReleased(key)
  
  def run(self, ticks):
    self.time += ticks
    
  def render(self, visibility, topMost):
    v = (1 - visibility) ** 2
    
    self.engine.view.setViewport(1,0)
    self.engine.view.setOrthogonalProjection(normalize = True)
    font = self.engine.data.font
    
    fadeScreen(v)
          
    try:
      glEnable(GL_BLEND)
      glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
      glEnable(GL_COLOR_MATERIAL)
      Theme.setBaseColor(1 - v)
      wrapText(font, (.1, .2 - v), self.prompt)

      for n, c in enumerate(Guitar.PLAYER1KEYS):
        if self.controls.getState(c):
          glColor3f(*self.fretColors[n%5])
        else:
          glColor3f(.4, .4, .4)
        font.render("#%d" % (n + 1), (.5 - .15 * (2 - n), .4 + v))

      for n, c in enumerate(Guitar.PLAYER2KEYS):
        if self.controls.getState(c):
          glColor3f(*self.fretColors[n%5])
        else:
          glColor3f(.4, .4, .4)
        #font.render("#%d" % (n + 1), (.5 - .15 * (2 - n), 0.15+.4 + v))          
        font.render("#%d" % (n + 1), (.5 - .15 * (2 - n), 0.15+.4 + v))

      if self.controls.getState(Player.STAR):
        Theme.setSelectedColor(1 - v)
      else:
        glColor3f(.4, .4, .4)
      font.render(_("StarPower"), (.25, .45 + v))

      #evilynux - Get killswitch mode (analog or digital?)
      # If analog, get and show attenuation. Most code taken from GuitarScene.
      self.analogKillMode = [self.engine.config.get("game", "analog_killsw_mode"),self.engine.config.get("game", "analog_killsw_mode_p2")]
      self.isKillAnalog = [False,False]
      self.whichJoy = [0,0]
      self.whichAxis = [0,0]
      self.whammyVol = [0.0,0.0]
      self.targetWhammyVol = [0.0,0.0]
      self.defaultWhammyVol = [self.analogKillMode[0]-1.0,self.analogKillMode[1]-1.0]   #makes xbox defaults 1.0, PS2 defaults 0.0

      if self.analogKillMode[0] == 3:   #XBOX inverted mode
        self.defaultWhammyVol[0] = -1.0
      if self.analogKillMode[1] == 3:   #XBOX inverted mode
        self.defaultWhammyVol[1] = -1.0

      self.actualWhammyVol = [self.defaultWhammyVol[0],self.defaultWhammyVol[1]]
      self.whammyVolAdjStep = 0.1
      self.lastWhammyVol = [self.defaultWhammyVol[0],self.defaultWhammyVol[1]]
      KillKeyCode = [0,0]

      if len(self.engine.input.joysticks) != 0:
        if self.analogKillMode[0] > 0:
          KillKeyCode[0] = self.controls.getReverseMapping(Player.KILL)
          self.isKillAnalog[0], self.whichJoy[0], self.whichAxis[0] = self.engine.input.getWhammyAxis(KillKeyCode[0])
        if self.analogKillMode[1] > 0:
          KillKeyCode[1] = self.controls.getReverseMapping(Player.PLAYER_2_KILL)
          self.isKillAnalog[1], self.whichJoy[1], self.whichAxis[1] = self.engine.input.getWhammyAxis(KillKeyCode[1])
  
        #evilynux - Compute analog killswitch value
        for i in range(0,1):
          if self.isKillAnalog[i]:
            if self.analogKillMode[i] == 2:  #XBOX mode: (1.0 at rest, -1.0 fully depressed)
              self.whammyVol[i] = 1.0 - (round(10* ((self.engine.input.joysticks[self.whichJoy[i]].get_axis(self.whichAxis[i])+1.0) / 2.0 ))/10.0)
  
            elif self.analogKillMode[i] == 3:  #XBOX Inverted mode: (-1.0 at rest, 1.0 fully depressed)
              self.whammyVol[i] = (round(10* ((self.engine.input.joysticks[self.whichJoy[i]].get_axis(self.whichAxis[i])+1.0) / 2.0 ))/10.0)
                
            else: #PS2 mode: (0.0 at rest, fluctuates between 1.0 and -1.0 when pressed)
              self.whammyVol[i] = (round(10*(abs(self.engine.input.joysticks[self.whichJoy[i]].get_axis(self.whichAxis[i]))))/10.0)
    
            if self.whammyVol[i] > 0.0 and self.whammyVol[i] < 0.1:
              self.whammyVol[i] = 0.1
  
          if self.whammyVol[i] > 0.0 and self.whammyVol[i] < 0.1:
            self.whammyVol[i] = 0.1

      #evilynux - Player 1 analog killswitch rendering
      if self.whammyVol[0] > 0:
        Theme.setSelectedColor(1 - v)
        font.render(_("Killswitch %d%%") % (self.whammyVol[0]*100), (.55, .45 + v))
      else:
        if self.controls.getState(Player.KILL):
          Theme.setSelectedColor(1 - v)
        else:
          glColor3f(.4, .4, .4)
        font.render(_("Killswitch"), (.55, .45 + v))


      if self.controls.getState(Player.PLAYER_2_STAR):
        Theme.setSelectedColor(1 - v)
      else:
        glColor3f(.4, .4, .4)
      font.render(_("StarPower"), (.25, .6 + v))

      #evilynux - Player 2 analog killswitch rendering
      if self.whammyVol[1] > 0:
        Theme.setSelectedColor(1 - v)
        font.render(_("Killswitch %d%%") % (self.whammyVol[1]*100), (.55, .6 + v))
      else:
        if self.controls.getState(Player.PLAYER_2_KILL):
          Theme.setSelectedColor(1 - v)
        else:
          glColor3f(.4, .4, .4)
        font.render(_("Killswitch"), (.55, .6 + v))

      if self.controls.getState(Player.ACTION1) or self.controls.getState(Player.ACTION2):
        Theme.setSelectedColor(1 - v)
      else:
        glColor3f(.4, .4, .4)
      font.render(_("Pick!"), (.45, .5 + v))

      if self.controls.getState(Player.PLAYER_2_ACTION1) or self.controls.getState(Player.PLAYER_2_ACTION2):
        Theme.setSelectedColor(1 - v)
      else:
        glColor3f(.4, .4, .4)          
      font.render(_("Pick!"), (.45, 0.65 + v))

        
    finally:
      self.engine.view.resetProjection()






#myfingershurt: drums :)
class DrumTester(KeyTester):
  """Keyboard configuration testing layer."""
  def __init__(self, engine, prompt = ""):
    self.prompt         = prompt
    self.engine         = engine
   
    Log.debug("DrumTester class init (Dialogs.py)...")
    
    
    self.accepted       = False
    self.time           = 0.0
    self.controls       = Player.Controls()
    self.fretColors     = [(0, 1, 0), (1, 0, 0), (1, 1, 0), (0, 0, 1), (1, 0, 1)]
    
  def render(self, visibility, topMost):
    v = (1 - visibility) ** 2
    
    self.engine.view.setViewport(1,0)
    self.engine.view.setOrthogonalProjection(normalize = True)
    font = self.engine.data.font
    
    fadeScreen(v)
          
    try:
      glEnable(GL_BLEND)
      glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
      glEnable(GL_COLOR_MATERIAL)
      Theme.setBaseColor(1 - v)
      wrapText(font, (.1, .2 - v), self.prompt)

      for n, c in enumerate(Drum.PLAYER1DRUMS): 
        glColor3f(.4, .4, .4)
        if n == 0:
          if self.controls.getState(c):
            glColor3f(*self.fretColors[0])  
          font.render("Bass", (.5 - .13 * (2.5 - n), .5 + v))
        elif n < 5:
          if self.controls.getState(c):
            glColor3f(*self.fretColors[n])
          font.render("#%d" % (n), (.5 - .13 * (2.5 - n), .4 + v))
        elif n < 9:
          if self.controls.getState(c):
            glColor3f(*self.fretColors[n-4])  
          font.render("#%d" % (n), (.5 - .13 * (2.5 - n + 4), .45 + v))     
      for n, c in enumerate(Drum.PLAYER2DRUMS):  
        glColor3f(.4, .4, .4)
        if n == 0:
          if self.controls.getState(c):
            glColor3f(*self.fretColors[0])  
          font.render("Bass", (.5 - .13 * (2.5 - n), .7 + v))               
        elif n < 5:
          if self.controls.getState(c):
            glColor3f(*self.fretColors[n])            
          font.render("#%d" % (n), (.5 - .13 * (2.5 - n), .6 + v))
        elif n < 9:
          if self.controls.getState(c):
            glColor3f(*self.fretColors[n-4]) 
          font.render("#%d" % (n), (.5 - .13 * (2.5 - n + 4), .65 + v))     

    finally:
      self.engine.view.resetProjection()

      


      
def _runDialog(engine, dialog):
  """Run a dialog in a sub event loop until it is finished."""
  if not engine.running:
    return
  
  engine.view.pushLayer(dialog)

  while engine.running and dialog in engine.view.layers:
    engine.run()

def getText(engine, prompt, text = ""):
  """
  Get a string of text from the user.
  
  @param engine:  Game engine
  @param prompt:  Prompt shown to the user
  @param text:    Default text
  """
  d = GetText(engine, prompt, text)
  _runDialog(engine, d)
  return d.text

def getKey(engine, prompt, key = None):
  """
  Ask the user to choose a key.
  
  @param engine:  Game engine
  @param prompt:  Prompt shown to the user
  @param key:     Default key
  """
  d = GetKey(engine, prompt, key)
  _runDialog(engine, d)
  return d.key

def chooseSong(engine, prompt = _("Choose a Song"), selectedSong = None, selectedLibrary = None):
  """
  Ask the user to select a song.
  
  @param engine:           Game engine
  @param prompt:           Prompt shown to the user
  @param selectedSong:     Name of song to select initially
  @param selectedLibrary:  Name of the library where to search for the songs or None for the default library

  @returns a (library, song) pair
  """
  d = SongChooser(engine, prompt, selectedLibrary = selectedLibrary, selectedSong = selectedSong)

  if d.getItems() == []:
    return (None, None)
  else:
    _runDialog(engine, d)
  return (d.getSelectedLibrary(), d.getSelectedSong())
  
def chooseFile(engine, masks = ["*.*"], path = ".", prompt = _("Choose a File"), dirSelect = False):
  """
  Ask the user to select a file.
  
  @param engine:  Game engine
  @param masks:   List of glob masks for files that are acceptable
  @param path:    Initial path
  @param prompt:  Prompt shown to the user
  """
  d = FileChooser(engine, masks, path, prompt, dirSelect)
  _runDialog(engine, d)
  return d.getSelectedFile()
  
def chooseItem(engine, items, prompt, selected = None):
  """
  Ask the user to one item from a list.
  
  @param engine:    Game engine
  @param items:     List of items
  @param prompt:    Prompt shown to the user
  @param selected:  Item selected by default
  """
  d = ItemChooser(engine, items, prompt = prompt, selected = selected)
  _runDialog(engine, d)
  return d.getSelectedItem()

#MFH - on-demand Neck Chooser
def chooseNeck(engine, prompt = "", selected = None):
  """
  Ask the user to one item from a list.
  
  @param engine:    Game engine
  @param items:     List of items
  @param prompt:    Prompt shown to the user
  @param selected:  Item selected by default
  """
  d = NeckChooser(engine, prompt = prompt, selected = selected)
  _runDialog(engine, d)
  return d.getSelectedNeck()

# evilynux - Show creadits
def showCredits(engine):
  d = Credits(engine)
  _runDialog(engine, d)
  
def testKeys(engine, prompt = _("Play with the keys and press Escape when you're done.")):
  """
  Have the user test the current keyboard configuration.
  
  @param engine:  Game engine
  @param prompt:  Prompt shown to the user
  """
  d = KeyTester(engine, prompt = prompt)
  _runDialog(engine, d)

#myfingershurt: drums
def testDrums(engine, prompt = _("Play with the keys and press Escape when you're done.")):
  """
  Have the user test the current keyboard configuration.
  
  @param engine:  Game engine
  @param prompt:  Prompt shown to the user
  """
  d = DrumTester(engine, prompt = prompt)
  _runDialog(engine, d)

  
def showLoadingScreen(engine, condition, text = _("Loading..."), allowCancel = False):
  """
  Show a loading screen until a condition is met.
  
  @param engine:      Game engine
  @param condition:   A function that will be polled until it returns a true value
  @param text:        Text shown to the user
  @type  allowCancel: bool
  @param allowCancel: Can the loading be canceled
  @return:            True if the condition was met, Fales if the loading was canceled.
  """
  
  # poll the condition first for some time
  n = 0
  while n < 32:
    n += 1
    if condition():
      return True
    engine.run()

  d = LoadingScreen(engine, condition, text, allowCancel)
  _runDialog(engine, d)
  return d.ready

def showMessage(engine, text):
  """
  Show a message to the user.
  
  @param engine:  Game engine
  @param text:    Message text
  """
  Log.notice("%s" % text)
  d = MessageScreen(engine, text)
  _runDialog(engine, d)

def estimateBpm(engine, song, prompt):
  """
  Ask the user to estimate the beats per minute value of a song.
  
  @param engine:  Game engine
  @param song:    Song instance
  @param prompt:  Prompt shown to the user
  """
  d = BpmEstimator(engine, song, prompt)
  _runDialog(engine, d)
  return d.bpm
  
#=======================================================================
# glorandwarf: added derived class LoadingSplashScreen

class LoadingSplashScreen(Layer, KeyListener):
  """Loading splash screen layer"""
  def __init__(self, engine, text):
    self.engine       = engine
    self.text         = text
    self.time         = 0.0
    self.loadingx = Theme.loadingX
    self.loadingy = Theme.loadingY  
    self.allowtext = self.engine.config.get("game", "lphrases")  

    Log.debug("LoadingSplashScreen class init (Dialogs.py)...")

    #Get theme
    themename = self.engine.data.themeLabel
    self.theme = self.engine.data.theme

  def shown(self):
    self.engine.input.addKeyListener(self, priority = True)

  def keyPressed(self, key, unicode):
    return True
    
  def hidden(self):
    self.engine.boostBackgroundThreads(False)
    self.engine.input.removeKeyListener(self)

  def run(self, ticks):
    self.time += ticks / 50.0
  
  def render(self, visibility, topMost):
    self.engine.view.setViewport(1,0)
    self.engine.view.setOrthogonalProjection(normalize = True)
    font = self.engine.data.loadingFont   #MFH - new font support

    if not font:
      return

    if visibility > 0.9:
      self.engine.boostBackgroundThreads(True)
    else:
      self.engine.boostBackgroundThreads(False)
    
    try:
      v = (1 - visibility) ** 2
      fadeScreen(v)

      w, h = self.engine.view.geometry[2:4]
      self.engine.data.loadingImage.transform.reset()
      self.engine.data.loadingImage.transform.translate(w / 2, h / 2)
      self.engine.data.loadingImage.transform.scale(.5, -.5)
      self.engine.data.loadingImage.draw(color = (1, 1, 1, 1))

      Theme.setBaseColor(1 - v)
      
      if self.theme == 1:
        fscale = 0.0016
      else:
        fscale = 0.0015
      w, h = font.getStringSize(self.text, scale=fscale)

      if self.loadingx != None:
        if self.loadingy != None:
          x = self.loadingx
          y = self.loadingy - h / 2 + v * .5
        else:
          x = self.loadingx
          y = .6 - h / 2 + v * .5
      elif self.loadingy != None:
        x = .5
        y = .6 - h / 2 + v * .5
      else:
        x = .5
        y = .6 - h / 2 + v * .5

      # evilynux - Made text about 2 times smaller (as requested by worldrave)
      if self.allowtext:
        if self.theme == 1:   #GH3 themes get different right margin, and always call wrap function
           wrapCenteredText(font, (x,y), self.text, scale = fscale, rightMargin = 0.82)
        elif w > 0.9 or x > 0.5:   #longer than a single line?
          wrapCenteredText(font, (x,y), self.text, scale = fscale)
        else:
          font.render(self.text, (x - w/2, y), scale = fscale)

    finally:
      self.engine.view.resetProjection()
    
def showLoadingSplashScreen(engine, text = _("Loading...")):
  splash = LoadingSplashScreen(engine, text)
  engine.view.pushLayer(splash)
  engine.run()
  return splash

def hideLoadingSplashScreen(engine, splash):
  engine.view.popLayer(splash)


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
      #Log.debug("Dialogs.isInt: " + str(possibleInt) + " = TRUE")
      return True
    else:
      #Log.debug("Dialogs.isInt: " + str(possibleInt) + " = FALSE")
      return False
  except Exception, e:
    return False
    #Log.debug("Dialogs.isInt: " + str(possibleInt) + " = FALSE, exception: " + str(e) )


def removeSongOrderPrefixFromName(name):
  if not name.startswith("."):
    splitName = name.split(".",1)
    #Log.debug("Dialogs.songListLoaded: Separating song name from prefix: " + str(splitName) )
    if isInt(splitName[0]) and len(splitName) > 1:
      name = splitName[1]
      #while len(splitName) > 1: #now remove any remaining leading spaces
      splitName[0] = ""
      while splitName[0] == "":
        splitName = name.split(" ",1)
        if len(splitName) > 1:
          if splitName[0] == "":
            name = splitName[1]
            #Log.debug("Dialogs.songListLoaded: Removing song name prefix, new name = " + splitName[1])
  else:
    Log.debug("Song name starting with a period filtered from prefix removal logic: " + item.name)
  return name
