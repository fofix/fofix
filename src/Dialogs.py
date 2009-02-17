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
import time

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
import random

#myfingershurt: drums :)
import Drum

# evilynux - MFH-Alarian Mod credits
from Credits import Credits

import Config
import Settings

#MFH - for cd/song list
from Svg import ImgDrawing, SvgContext

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
    if x + (w/2) > rightMargin*1.11 or word == "\n":
      w, h = font.getStringSize(sentence, scale = scale)
      #x = startXpos
      glPushMatrix()
      glRotate(visibility * (n + 1) * -45, 0, 0, 1)
      font.render(sentence, (x - (w/2), y + visibility * n), scale = scale)
      glPopMatrix()
      sentence = word
      y += h
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
    y += h
  
    #if word == "\n":
    #  continue
    #x += w + space
  return (x, y)

  #space = font.getStringSize(" ", scale = scale)[0]
  #startXpos = x - (rightMargin-x) #for a symmetrical text wrapping
  #x = startXpos
  #for n, word in enumerate(text.split(" ")):
  #  w, h = font.getStringSize(word, scale = scale)
  #  if x + w > rightMargin*1.11 or word == "\n":
  #    x = startXpos
  #    y += h*.5 # Worldrave - Modified spacing between lines
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

    self.logClassInits = self.engine.config.get("game", "log_class_inits")
    if self.logClassInits == 1:
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

    self.logClassInits = self.engine.config.get("game", "log_class_inits")
    if self.logClassInits == 1:
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

    self.logClassInits = self.engine.config.get("game", "log_class_inits")
    if self.logClassInits == 1:
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

    try:
      v = (1 - visibility) ** 2
      fadeScreen(v)

      w, h = self.engine.view.geometry[2:4]
      
      #MFH - auto-scaling of loading screen
      imgwidth = self.engine.data.loadingImage.width1()
      wfactor = 640.000/imgwidth
      self.engine.drawImage(self.engine.data.loadingImage, scale = (wfactor,-wfactor), coord = (w/2,h/2))

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

    self.logClassInits = self.engine.config.get("game", "log_class_inits")
    if self.logClassInits == 1:
      Log.debug("MessageScreen class init (Dialogs.py)...")
    

  def shown(self):
    self.engine.input.addKeyListener(self, priority = True)

  def keyPressed(self, key, unicode):
    c = self.engine.input.controls.getMapping(key)
    if c in Player.KEY1S + Player.KEY2S + Player.DRUM1S + Player.DRUM4S + Player.CANCELS or key == pygame.K_RETURN or key == pygame.K_ESCAPE:
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
    
    self.logClassInits = self.engine.config.get("game", "log_class_inits")
    if self.logClassInits == 1:
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
    self.songlistcd_score_color = Theme.hexToColor(Theme.songlistcd_score_colorVar)
    
    self.song_rb2_name_color = Theme.hexToColor(Theme.song_rb2_name_colorVar)
    self.song_rb2_name_selected_color = Theme.hexToColor(Theme.song_rb2_name_selected_colorVar)
    self.song_rb2_diff_color = Theme.hexToColor(Theme.song_rb2_diff_colorVar)
    self.song_rb2_artist_color = Theme.hexToColor(Theme.song_rb2_artist_colorVar)

    

    self.listRotation = self.engine.config.get("game", "songlistrotation")
    self.songCoverType = self.engine.config.get("game", "songcovertype")
    self.listingMode = engine.config.get("game","song_listing_mode")
    self.songIcons = engine.config.get("game", "song_icons")
    self.preLoadSongLabels = engine.config.get("game", "preload_labels")
    
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

    try:
      self.song_listcd_cd_xpos = Theme.song_listcd_cd_Xpos
      Log.debug("song_listcd_cd_xpos found: " + str(self.song_listcd_cd_xpos))
    except Exception, e:
      Log.warn("Unable to load Theme song_listcd_cd_xpos: %s" % e) 
      self.song_listcd_cd_xpos = None

    try:
      self.song_listcd_cd_ypos = Theme.song_listcd_cd_Ypos
      Log.debug("song_listcd_cd_ypos found: " + str(self.song_listcd_cd_ypos))
    except Exception, e:
      Log.warn("Unable to load Theme song_listcd_cd_ypos: %s" % e) 
      self.song_listcd_cd_ypos = None

    try:
      self.song_listcd_score_xpos = Theme.song_listcd_score_Xpos
      Log.debug("song_listcd_score_xpos found: " + str(self.song_listcd_score_xpos))
    except Exception, e:
      Log.warn("Unable to load Theme song_listcd_score_xpos: %s" % e) 
      self.song_listcd_score_xpos = None

    try:
      self.song_listcd_score_ypos = Theme.song_listcd_score_Ypos
      Log.debug("song_listcd_score_ypos found: " + str(self.song_listcd_score_ypos))
    except Exception, e:
      Log.warn("Unable to load Theme song_listcd_score_ypos: %s" % e) 
      self.song_listcd_score_ypos = None

    try:
      self.song_listcd_list_xpos = Theme.song_listcd_list_Xpos
      Log.debug("song_listcd_list_xpos found: " + str(self.song_listcd_list_xpos))
    except Exception, e:
      Log.warn("Unable to load Theme song_listcd_list_xpos: %s" % e) 
      self.song_listcd_list_xpos = None


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
      
    #Qstick - List/CD mode element positions
    if self.song_listcd_cd_xpos == None:
      self.song_listcd_cd_xpos = .75
  
    if self.song_listcd_cd_ypos == None:
      self.song_listcd_cd_ypos = .6
      
    if self.song_listcd_score_xpos == None:
      self.song_listcd_score_xpos = 0.6

    if self.song_listcd_score_ypos == None:
      self.song_listcd_score_ypos = 0.5
      
    if self.song_listcd_list_xpos == None:
      self.song_listcd_list_xpos = .1
    

    
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
    self.scrollUp       = False
    self.scrollDown     = False
    self.click          = False
    
    self.halfTime = 0

    #RF-mod
    self.previewDisabled  = self.engine.config.get("audio", "disable_preview")
    self.sortOrder        = self.engine.config.get("game", "sort_order")
    self.rotationDisabled = self.engine.config.get("performance", "disable_librotation")
    self.spinnyDisabled   = self.engine.config.get("game", "disable_spinny")

    self.sortorder = engine.config.get("game", "sort_order")
    self.sortdirection = engine.config.get("game", "sort_direction")

    self.sfxVolume    = self.engine.config.get("audio", "SFX_volume")
    self.engine.data.selectSound.setVolume(self.sfxVolume)

    #Get Theme
    themename = self.engine.data.themeLabel
    self.theme = self.engine.data.theme

    
    self.display = self.engine.config.get("coffee", "song_display_mode")
    if self.display == 4:
      if Theme.songListDisplay != None:
        self.display = Theme.songListDisplay
      else:
        self.display = 1

    self.tut = self.engine.config.get("game", "tut")

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
    if self.tut == True:
      self.library = self.engine.tutorialFolder

    self.loadCollection()


    #MFH configurable default instrument display with 5th / orange fret
    #   need to keep track of the instrument number and instrument name
    self.instrumentNum = self.engine.config.get("game", "songlist_instrument")
    if self.instrumentNum == 4:
      self.instrument = "Drums"
      self.instrumentNice = _("Drums")
    elif self.instrumentNum == 3:
      self.instrument = "Lead Guitar"
      self.instrumentNice = _("Lead")
    elif self.instrumentNum == 2:
      self.instrument = "Bass Guitar"
      self.instrumentNice = _("Bass")
    elif self.instrumentNum == 1:
      self.instrument = "Rhythm Guitar"
      self.instrumentNice = _("Rhythm")
    else: 
      self.instrument = "Guitar"
      self.instrumentNice = _("Guitar")

    self.diffTrans = {}
    self.diffTrans["Expert"] = _("Expert")
    self.diffTrans["Hard"]   = _("Hard")
    self.diffTrans["Medium"] = _("Medium")
    self.diffTrans["Easy"]   = _("Easy")

    if self.display == 0:
      self.engine.resource.load(self, "cassette",     lambda: Mesh(self.engine.resource.fileName("cassette.dae")), synch = True)
      self.engine.resource.load(self, "label",        lambda: Mesh(self.engine.resource.fileName("label.dae")), synch = True)
      self.engine.resource.load(self, "libraryMesh",  lambda: Mesh(self.engine.resource.fileName("library.dae")), synch = True)
      self.engine.resource.load(self, "libraryLabel", lambda: Mesh(self.engine.resource.fileName("library_label.dae")), synch = True)
      self.engine.loadImgDrawing(self, "background",  os.path.join("themes",themename,"menu","songchoosepaper.png"))
    elif self.display == 1:

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
        self.diffNice = self.diffTrans[self.diff]
      elif self.diff == 2:
        self.diff = "Medium"
        self.diffNice = self.diffTrans[self.diff]
      elif self.diff == 1:
        self.diff = "Hard"
        self.diffNice = self.diffTrans[self.diff]
      else: # self.diff == 0:
        self.diff = "Expert"
        self.diffNice = self.diffTrans[self.diff]
    elif self.display == 2:
      self.engine.resource.load(self, "cassette",     lambda: Mesh(self.engine.resource.fileName("cassette.dae")), synch = True)
      self.engine.resource.load(self, "label",        lambda: Mesh(self.engine.resource.fileName("label.dae")), synch = True)
      self.engine.resource.load(self, "libraryMesh",  lambda: Mesh(self.engine.resource.fileName("library.dae")), synch = True)
      self.engine.resource.load(self, "libraryLabel", lambda: Mesh(self.engine.resource.fileName("library_label.dae")), synch = True)
      try:
        self.engine.loadImgDrawing(self, "background",       os.path.join("themes",themename,"menu","songchooselistcd.png"))
      except IOError:
        self.engine.loadImgDrawing(self, "background",       os.path.join("themes",themename,"menu","songchoosepaper.png"))
      try:
        self.engine.loadImgDrawing(self, "selectedlistcd",    os.path.join("themes",themename,"menu","selectedlistcd.png"))
      except IOError:
        self.engine.loadImgDrawing(self, "selected",    os.path.join("themes",themename,"menu","selected.png"))
        self.selectedlistcd = None
    elif self.display == 3:
      try:
        self.engine.loadImgDrawing(self, "background",  os.path.join("themes",themename,"menu","songchooserb2.png"))
      except IOError:
        self.background = None
        self.engine.loadImgDrawing(self, "background",       os.path.join("themes",themename,"menu","songchoosepaper.png"))
      try:
        self.engine.loadImgDrawing(self, "selected",    os.path.join("themes",themename,"menu","selectedrb2.png"))
      except IOError:
        self.engine.loadImgDrawing(self, "selected",    os.path.join("themes",themename,"menu","selected.png"))
      try:
        self.engine.loadImgDrawing(self, "tierbg",    os.path.join("themes",themename,"menu","tier.png"))
      except IOError:
        self.tierbg = None
      try:
        self.engine.loadImgDrawing(self, "emptyLabel",    os.path.join("themes",themename,"menu","emptylabel.png"))
      except IOError:
        self.emptyLabel = None
      try:
        self.engine.loadImgDrawing(self, "lockedLabel",    os.path.join("themes",themename,"menu","lockedlabel.png"))
      except IOError:
        self.lockedLabel = self.emptyLabel
      try:
        self.engine.loadImgDrawing(self, "diffimg1",    os.path.join("themes",themename,"menu","diff1.png"))
        self.engine.loadImgDrawing(self, "diffimg2",    os.path.join("themes",themename,"menu","diff2.png"))
        self.engine.loadImgDrawing(self, "diffimg3",    os.path.join("themes",themename,"menu","diff3.png"))
      except IOError:
        self.diffimg1 = self.engine.data.star3
        self.diffimg2 = self.engine.data.star4
        self.diffimg3 = self.engine.data.starPerfect
        
      #song icon loading
      if self.songIcons:
        self.itemIcons = []
        self.itemIconNames = []
        iconFolder = engine.resource.fileName(os.path.join("themes",themename,"menu","icon"))
        if os.path.exists(iconFolder):
          for filename in os.listdir(iconFolder):
            if os.path.splitext(filename)[1].lower() == ".png":
              
              thisfile = self.engine.resource.fileName("themes",themename,"menu","icon",filename)
              if os.path.exists(thisfile):
                self.itemIcons.append(ImgDrawing(self.engine.data.svg, thisfile))
                self.itemIconNames.append(os.path.splitext(filename)[0])
             
  
        
      self.scoreTimer = 0

      # evilynux - configurable default highscores difficulty display
      self.diff = self.engine.config.get("game", "songlist_difficulty")
      if self.diff == 3:
        self.diff = "Easy"
        self.diffNice = self.diffTrans[self.diff]
      elif self.diff == 2:
        self.diff = "Medium"
        self.diffNice = self.diffTrans[self.diff]
      elif self.diff == 1:
        self.diff = "Hard"
        self.diffNice = self.diffTrans[self.diff]
      else: # self.diff == 0:
        self.diff = "Expert"
        self.diffNice = self.diffTrans[self.diff]
        
      #if self.rotationDisabled:
      #  item = self.items[self.selectedIndex]
      #  Log.debug(os.path.join(self.library, item.songName,    "label.png"))
      #  try:
      #    if isinstance(item, Song.SongInfo):
      #      
      #      self.engine.loadImgDrawing(self, "currentlabel", os.path.join(self.library, item.songName,    "label.png"))
      #    elif isinstance(item, Song.LibraryInfo):
      #      self.engine.loadImgDrawing(self, "currentlabel", os.path.join(item.libraryName,    "label.png"))
      #    else:
      #      self.currentlabel = None
      #  except IOError:
      #    self.currentlabel = None


      
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
    self.loadStartTime = time.time()
    
    # evilynux - Has to be synchronous so we don't return with an empty library list!
    self.engine.resource.load(self, "libraries", lambda: Song.getAvailableLibraries(self.engine, self.library), onLoad = self.libraryListLoaded, synch = True)

    #showLoadingScreen(self.engine, lambda: self.loaded, text = _("Browsing Collection..."))

    

  def libraryListLoaded(self, libraries):
    Log.debug("Dialogs.libraryListLoaded() function call...")
    #self.engine.resource.load(self, "songs",     lambda: Song.getAvailableSongs(self.engine, self.library), onLoad = self.songListLoaded)
    self.engine.resource.load(self, "songs",     lambda: Song.getAvailableSongsAndTitles(self.engine, self.library, progressCallback=self.progressCallback), onLoad = self.songListLoaded, synch = True) # evilynux - Less BlackSOD[?]

  def progressCallback(self, percent):
    if time.time() - self.loadStartTime > 7:
      changeLoadingSplashScreenText(self.engine, self.splash, _("Browsing Collection...") + ' (%d%%)' % (percent*100))

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
    if self.display != 4:
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

    if self.listingMode == 0:
      self.items         = self.libraries + self.songs
    else:
      self.items         = self.songs

    if self.items == []:    #MFH: Catch when there ain't a damn thing in the current folder - back out!
      if self.library != Song.DEFAULT_LIBRARY:
        hideLoadingSplashScreen(self.engine, self.splash)
        self.splash = None
        self.initialItem = self.library
        self.library     = os.path.dirname(self.library)
        self.selectedItem = None
        self.loadCollection()
        return


    #Log.debug("Dialogs.songListLoaded: self.items = " + str(self.items))
    Log.debug("Dialogs.songListLoaded.")

    self.itemAngles    = [0.0] * len(self.items)
    self.itemLabels    = [None] * len(self.items)
    self.loaded        = True
    self.searchText    = ""
    self.searching     = False
    
    if self.display != 1:
      if self.preLoadSongLabels:
        for i in range(0,len(self.items)):
          self.loadItemLabel(i)
    
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

      elif isinstance(item, Song.TitleInfo) or isinstance(item, Song.SortTitleInfo):
        self.tiersArePresent = True 

    # if the first item is a title, start on the second one
    #FIXME: potential infinite loop if there are only titles
    
    #else:
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
    themename = self.engine.data.themeLabel
    item = self.items[i]
    if self.itemLabels[i] is None:
      if isinstance(item, Song.SongInfo):
        if (item.getLocked()):
          self.itemLabels[i] = "Locked"
          return
        elif self.songCoverType:
          label = self.engine.resource.fileName(item.libraryNam, item.songName,    "label.png")
        else:
          label = self.engine.resource.fileName(item.libraryNam, item.songName,    "album.png")

      elif isinstance(item, Song.LibraryInfo):
        label = self.engine.resource.fileName(item.libraryName, "label.png")
      elif isinstance(item, Song.RandomSongInfo):
        label = self.engine.resource.fileName("themes",themename,"menu","random.png")
      else:
        return
      if os.path.exists(label):
        #MFH - load as 2D drawing and not a texture when in CD/List mode:
        if self.display == 2 and not self.listRotation:
          #self.engine.loadImgDrawing(self, "itemLabels[i]",  label)
          self.itemLabels[i] = ImgDrawing(self.engine.data.svg, label)
        elif self.display == 3:
          self.itemLabels[i] = ImgDrawing(self.engine.data.svg, label)
        else:
          self.itemLabels[i] = Texture(label)
      else:
        if self.display == 3:
          self.itemLabels[i] = "Empty"

  def updateSelection(self):
  
    self.selectedItem  = self.items[self.selectedIndex]
    self.songCountdown = 1024

    #myfingershurt: only if CD list
    if self.display != 1:
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
        # evilynux - "song" might be in the process of being created by a song preview,
        #            stopping the songLoader is safer.
        if self.songLoader:
          self.songLoader.stop()
        #if not self.song: #MFH - play the sound immediately, THEN process.
        self.engine.data.acceptSound.setVolume(self.sfxVolume)  #MFH
        self.engine.data.acceptSound.play()
        if isinstance(self.selectedItem, Song.LibraryInfo):
          self.library = self.selectedItem.libraryName
          self.initialItem = None
          Log.debug("New library selected: " + str(self.library) )
          self.loadCollection()
        elif isinstance(self.selectedItem, Song.SongInfo) and not self.selectedItem.getLocked():
        #else:
          
          if self.listingMode == 1:
            self.library = self.selectedItem.libraryNam
            
          self.engine.view.popLayer(self)
          self.accepted = True
        elif isinstance(self.selectedItem, Song.RandomSongInfo):
          while True:
            self.selectedItem = self.items[random.randint(0,len(self.items)-1)]
            if isinstance(self.selectedItem, Song.SongInfo) and not self.selectedItem.getLocked():
              break
          
          if self.listingMode == 1:
            self.library = self.selectedItem.libraryNam
            
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
          
    elif c in Player.KILLS and self.engine.config.get("game", "whammy_changes_sort_order"):
        orderings = self.engine.config.getOptions("game", "sort_order")[1]
        self.sortOrder += 1
        if self.sortOrder > len(orderings):
          self.sortOrder = 0
        self.engine.config.set("game", "sort_order", self.sortOrder)
        if self.songLoader:
          self.songLoader.stop()
        if self.song:
          self.song.fadeout(1000)
        self.selectedItem = None
        self.loadCollection()

        
    elif c in Player.CANCELS + Player.KEY2S or (c in Player.DRUM1S and self.drumNav):
      # evilynux - "song" might be in the process of being created,
      #            stopping the songLoader is safer.
      if self.songLoader:
        self.songLoader.stop()
      #if not self.song:
      self.engine.data.cancelSound.setVolume(self.sfxVolume)  #MFH
      self.engine.data.cancelSound.play()
      if self.library != Song.DEFAULT_LIBRARY and self.tut == False and self.listingMode == 0:
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
        if isinstance(self.items[self.selectedIndex], Song.TitleInfo) or isinstance(self.items[self.selectedIndex], Song.SortTitleInfo):  #MFH - if we just found a title, we need to go once more to ensure we're goin back a title:
          self.selectedIndex = (self.selectedIndex - 1) % len(self.items)
        while not ( isinstance(self.items[self.selectedIndex], Song.TitleInfo) or isinstance(self.items[self.selectedIndex], Song.CareerResetterInfo) or isinstance(self.items[self.selectedIndex], Song.SortTitleInfo) ):
          self.selectedIndex = (self.selectedIndex - 1) % len(self.items)
        while 1:
          if isinstance(self.items[self.selectedIndex], Song.CareerResetterInfo):
            break
          self.selectedIndex = (self.selectedIndex + 1) % len(self.items)
          if self.matchesSearch(self.items[self.selectedIndex]) and not isinstance(self.items[self.selectedIndex], Song.TitleInfo) and not isinstance(self.items[self.selectedIndex], Song.SortTitleInfo):
            break
        self.updateSelection()
    
    elif c in Player.RIGHTS:
      #if self.tiersArePresent or self.careerMode: # if there are no titles, we'll have an infinite loop = bad
      if self.tiersArePresent: # if there are no titles, we'll have an infinite loop = bad
        self.selectedIndex = (self.selectedIndex + 1) % len(self.items) #MFH - nudge it down one count to get things started.
        while not ( isinstance(self.items[self.selectedIndex], Song.TitleInfo) or isinstance(self.items[self.selectedIndex], Song.CareerResetterInfo) or isinstance(self.items[self.selectedIndex], Song.SortTitleInfo) ):
          self.selectedIndex = (self.selectedIndex + 1) % len(self.items)
        while 1:
          if isinstance(self.items[self.selectedIndex], Song.CareerResetterInfo):
            break
          self.selectedIndex = (self.selectedIndex + 1) % len(self.items)
          if self.matchesSearch(self.items[self.selectedIndex]) and not isinstance(self.items[self.selectedIndex], Song.TitleInfo) and not isinstance(self.items[self.selectedIndex], Song.SortTitleInfo):
            break
        self.updateSelection()
    

        
    #myfingershurt: adding yellow fret preview again
    elif c in Player.KEY3S:
      self.playSong = True

    #racer: highscores change on fret hit
    elif c in Player.KEY4S or (c in Player.BASEDRUMS and self.drumNav):
     self.highScoreChange = True

    #MFH - instrument change on 5th fret
    #elif c in Player.KEY5S or (c in Player.DRUM3S and self.drumNav):
    elif c in Player.KEY5S:   #MFH can't use drum3, that's for down
     self.instrumentChange = True


    elif c in Player.UPS + Player.ACTION1S or (c in Player.DRUM2S and self.drumNav):
      self.scrollUp = True
      self.click = False
      self.scroll(0)
    elif c in Player.DOWNS + Player.ACTION2S or (c in Player.DRUM3S and self.drumNav):
      self.scrollDown = True
      self.click = False
      self.scroll(1)
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
  
  def keyReleased(self, key):
    if not self.items or self.accepted:
      return
    c = self.engine.input.controls.getMapping(key)
    if c in Player.UPS + Player.ACTION1S or (c in Player.DRUM2S and self.drumNav):
      self.scrollUp = False
      self.click = False
    elif c in Player.DOWNS + Player.ACTION2S or (c in Player.DRUM3S and self.drumNav):
      self.scrollDown = False
      self.click = False
    else:
      self.click = False
    return True
  
  def scroll(self, dir):
    if not self.click or (self.click and (self.time - self.lastTime > 10)):
      self.engine.data.selectSound.play()
      if dir == 0:
        #if not self.song:
        # self.engine.data.selectSound.setVolume(self.sfxVolume)  #MFH
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
                 isinstance(self.items[currentIndex], Song.RandomSongInfo) or \
                 (self.display == 0 and isinstance(self.items[currentIndex], Song.TitleInfo)):
                break
            self.selectedIndex = currentIndex

            if self.matchesSearch(self.items[self.selectedIndex]):
            #if self.matchesSearch(self.items[self.selectedIndex]) and not isinstance(self.items[self.selectedIndex], Song.TitleInfo):
              break
        self.updateSelection()
      elif dir == 1:
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
                 isinstance(self.items[currentIndex], Song.RandomSongInfo) or \
                 (self.display == 0 and isinstance(self.items[currentIndex], Song.TitleInfo)):
                break
            self.selectedIndex = currentIndex
          
            if self.matchesSearch(self.items[self.selectedIndex]):
            #if self.matchesSearch(self.items[self.selectedIndex]) and not isinstance(self.items[self.selectedIndex], Song.TitleInfo):
              break
        self.updateSelection()
      self.click = True

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
      try:
        self.songLoader.stop()
      except:
        self.songLoader = None

    self.songLoader = self.engine.resource.load(self, None, lambda: Song.loadSong(self.engine, song, playbackOnly = True, library = self.library), synch = False, onLoad = self.songLoaded) #Blazingamer - asynchronous preview loading allows "Loading Preview..." to correctly disappear.

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
    
    self.halfTime = ~self.halfTime
    if self.halfTime == 0:
      if self.scrollDown:
        self.scroll(1)
      elif self.scrollUp:
        self.scroll(0)

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

    if self.display == 2:
      glRotate(90, 0, 0, 1)
      if self.listRotation:
        glRotate(((self.time - self.lastTime) * 2 % 360) - 90, 1, 0, 0)
    self.cassette.render("Mesh_001")
    glColor3f(.1, .1, .1)
    self.cassette.render("Mesh")
    
    if isinstance(label, str): #locked
      return
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
    if self.display == 2:
      glRotate(-180, 0, 1, 0)
      glRotate(-90, 0, 0, 1)
      if self.listRotation:
        glRotate(((self.time - self.lastTime) * 4 % 360) - 90, 1, 0, 0)
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
    if self.items != []:
      v = (1 - visibility) ** 2
  
      # render the background
      t = self.time / 100
      
      self.engine.view.setViewport(1,0)
      w, h, = self.engine.view.geometry[2:4]
      screenw = w
      screenh = h
      r = .5
  
      if self.display != 1: #
        #MFH - auto background image scaling
        imgwidth = self.background.width1()
        wfactor = 640.000/imgwidth
        self.engine.drawImage(self.background, scale = (wfactor,-wfactor), coord = (w/2,h/2))
      else:
        imgwidth = self.paper.width1()
        wfactor = 640.000/imgwidth
        if self.background != None:
          self.engine.drawImage(self.background, scale = (.5,-.5), coord = (w/2,h/2))
        else:
          self.background = None
  
        if self.songback:
        # evilynux - Fixed, there's a two song offset and two lines should be skipped
          if self.selectedIndex == 1 or self.selectedIndex == 2:
            y = 0
          else:
            y = h*(self.selectedIndex-2)*2/16
          papercoord = (w/2,y + h/2)
        else:
          papercoord = (w/2,h/2)

        self.engine.drawImage(self.paper, scale = (wfactor,-wfactor), coord = papercoord)
  
        #racer: render preview graphic
      if self.previewDisabled == True and self.preview != None:
        self.engine.drawImage(self.preview, scale = (.5,-.5), coord = (w/2, h/2))
      else:
        self.preview = None
  
  
  
    
  
      #MFH - initializing these local variables so no "undefined" crashes result
      text = ""  
      notesTotal = 0    
      notesHit = 0
      noteStreak = 0

      if self.instrumentChange:
        self.instrumentChange = False
        self.instrumentNum += 1
        if self.instrumentNum > 4:
          self.instrumentNum = 0
        if self.instrumentNum == 4:
          self.instrument = "Drums"
          self.instrumentNice = _("Drums")
        elif self.instrumentNum == 3:
          self.instrument = "Lead Guitar"
          self.instrumentNice = _("Lead")
        elif self.instrumentNum == 2:
          self.instrument = "Bass Guitar"
          self.instrumentNice = _("Bass")
        elif self.instrumentNum == 1:
          self.instrument = "Rhythm Guitar"
          self.instrumentNice = _("Rhythm")
        else: 
          self.instrument = "Guitar"
          self.instrumentNice = _("Guitar")
        self.engine.config.set("game", "songlist_instrument", self.instrumentNum)
        if self.sortOrder == 7:
            if self.songLoader:
              self.songLoader.stop()
            if self.song:
              self.song.fadeout(1000)
            self.selectedItem = None
            self.loadCollection()
  
      if self.display == 0: #CDs Mode
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
            elif isinstance(item, Song.RandomSongInfo):
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
              elif isinstance(item, Song.RandomSongInfo):
                #myfingershurt: cd cases are backwards
                glRotate(self.itemAngles[i], 0, 0, 1)
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
  
              c1,c2,c3 = self.songlistcd_score_color
              glColor3f(c1,c2,c3)
  
              scale = 0.0011
              w, h = font.getStringSize(self.prompt, scale = scale)
              
              #x = .6
              x = self.song_cdscore_xpos
              y = .5 + f / 2.0
              if len(item.difficulties) > 3:
                y = .42 + f / 2.0
              
              #for p in item.parts:    #MFH - look at selected instrument!
              #  if str(p) == self.instrument:
              for d in item.difficulties:
                scores = item.getHighscores(d, part = Song.parts[self.instrumentNum])
                #scores = item.getHighscoresWithPartString(d, part = self.instrument)
                
                if scores:
                  score, stars, name, scoreExt = scores[0]
                  try:
                    notesHit, notesTotal, noteStreak, modVersion, handicap, handicapLong, originalScore = scoreExt
                  except ValueError:
                    notesHit, notesTotal, noteStreak, modVersion, oldScores1, oldScores2 = scoreExt
                    handicap = 0
                    handicapLong = "None"
                    originalScore = score
                else:
                  score, stars, name = "---", 0, "---"
                Theme.setBaseColor(1 - v)
                font.render(unicode(d),     (x, y),           scale = scale)

                starscale = scale*1.4
                stary = 1.0 - y/self.engine.data.fontScreenBottom - h * 1.8
                self.engine.drawStarScore(screenw, screenh, x, stary, stars, starscale, hqStar = True) #MFH

#-                # evilynux - Fixed star size following Font render bugfix
#-                if stars == 7: #akedrou
#-                  glColor3f(0, .5, 1) #should be customizable
#-                  font.render(unicode(Data.STAR2 * 5), (x, y + h), scale = scale * 1.8)
#-                elif stars == 6 and self.theme == 2:    #gold stars in RB songlist
#-                  glColor3f(1, 1, 0)  
#-                  font.render(unicode(Data.STAR2 * 5), (x, y + h), scale = scale * 1.8)
#-                elif stars == 6:
#-                  glColor3f(0, 1, 0)  
#-                  font.render(unicode(Data.STAR2 * 5), (x, y + h), scale = scale * 1.8)
#-                else:
#-                  font.render(unicode(Data.STAR2 * stars + Data.STAR1 * (5 - stars)), (x, y + h), scale = scale * 1.8)


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
  
            elif isinstance(item, Song.RandomSongInfo):
              Theme.setBaseColor(1 - v)
  
              c1,c2,c3 = self.song_name_selected_color
              glColor3f(c1,c2,c3)
  
              careerResetText = ""
              wrapText(font, (x, pos[1] + 3 * font.getHeight() * 0.0016), careerResetText, visibility = f, scale = 0.0016)
  
          #MFH CD list
          text = self.instrumentNice
          scale = 0.00250
          #glColor3f(1, 1, 1)
          c1,c2,c3 = self.song_name_selected_color
          glColor3f(c1,c2,c3)
          w, h = font.getStringSize(text, scale=scale)
          font.render(text, (0.95-w, 0.000), scale=scale)
  
  
  
  
        finally:
          self.engine.view.resetProjection()
          nuttin = True
      

          
      elif self.display == 1:   #MFH - song List display
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
  
            #MFH - TODO - add logic for special 4-item songlist to prevent jumping up and down
            if self.selectedIndex < 5 and maxIndex < 5:
              pos = self.selectedIndex - self.selectedIndex, self.selectedIndex + (5-self.selectedIndex)
              y = h*(.63-(.125*self.selectedIndex))
            elif self.selectedIndex == 0:#Selection is first item in list
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
            self.engine.drawImage(self.selected, scale = (wfactor,-wfactor), coord = (w/2.1, y-h*.01))
  
            #Render current library path
            glColor4f(1,1,1,1)
            text = self.library
            w, h = font.getStringSize(text)
  
            if self.searchText:
              text = _("Filter: %s") % (self.searchText) + "|"
              if not self.matchesSearch(self.items[self.selectedIndex]):
                text += " (%s)" % _("Not found")
              font.render(text, (.05, .7 + v), scale = 0.001)
            elif self.songLoader:
              font.render(_("Loading Preview..."), (.05, .7 + v), scale = 0.001)
  
  
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
                      text = _("There are %d songs in this folder") % (item.songCount)
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
                elif isinstance(item, Song.RandomSongInfo):
                  text = _("Random Song")
                  c1,c2,c3 = self.career_title_color
                  glColor3f(c1,c2,c3)
  
  
                if i == self.selectedIndex:
                  font.render(text, (self.song_list_xpos, .15))
  
                
                if i == self.selectedIndex:
                  glColor4f(.7,.5,.25,1)
                  if isinstance(item, Song.SongInfo) or isinstance(item, Song.RandomSongInfo):
                    c1,c2,c3 = self.song_name_selected_color
                    glColor3f(c1,c2,c3)
                  if isinstance(item, Song.LibraryInfo):
                    c1,c2,c3 = self.library_selected_color
                    glColor3f(c1,c2,c3)
                  if isinstance(item, Song.TitleInfo) or isinstance(item, Song.CareerResetterInfo) or isinstance(item, Song.BlankSpaceInfo):
                    c1,c2,c3 = self.career_title_color
                    glColor3f(c1,c2,c3)
                else:
                  glColor4f(0,0,0,1)
                  if isinstance(item, Song.SongInfo) or isinstance(item, Song.RandomSongInfo):
                    c1,c2,c3 = self.song_name_text_color
                    glColor3f(c1,c2,c3)
                  if isinstance(item, Song.LibraryInfo):
                    c1,c2,c3 = self.library_text_color
                    glColor3f(c1,c2,c3)
                  if isinstance(item, Song.TitleInfo) or isinstance(item, Song.CareerResetterInfo) or isinstance(item, Song.BlankSpaceInfo):
                    c1,c2,c3 = self.career_title_color
                    glColor3f(c1,c2,c3)
                    
                text = item.name
                
                if isinstance(item, Song.SongInfo) and item.getLocked():
                  text = _("-- Locked --")
                
                if isinstance(item, Song.SongInfo): #MFH - add indentation when tier sorting
                  if self.tiersArePresent:
                    text = self.indentString + text
                
                # evilynux - Force uppercase display for Career titles
                if isinstance(item, Song.TitleInfo) or isinstance(item, Song.CareerResetterInfo) or isinstance(item, Song.BlankSpaceInfo):
                  text = string.upper(text)
  
                # evilynux - automatically scale song name
                scale = font.scaleText(text, maxwidth = 0.440)
                w, h = font.getStringSize(text, scale = scale)

                if i == self.selectedIndex:
                  sfont.render(text, (self.song_list_xpos, .0935*(i+1)-pos[0]*.0935+.15), scale = scale)
                else:
                  lfont.render(text, (self.song_list_xpos, .0935*(i+1)-pos[0]*.0935+.15), scale = scale)


                #MFH - Song list score / info display:
                if isinstance(item, Song.SongInfo) and not item.getLocked():
                  scale = 0.0009
                  text = self.diffNice
                  w, h = font.getStringSize(text, scale=scale)
                  # evilynux - score color
                  c1,c2,c3 = self.songlist_score_color
                  glColor3f(c1,c2,c3)
                  # evilynux - tweaked position to fit hit% and note streak
                  if self.extraStats:
                    lfont.render(text, (self.song_listscore_xpos-w-.02, .0935*(i+1)-pos[0]*.0935+.1575-h/2), scale=scale)
                  else:
                    lfont.render(text, (self.song_listscore_xpos-w-.02, .0935*(i+1)-pos[0]*.0935+.2-h/2), scale=scale)
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
                  
                  # evilynux - automatically scale artist name and year
                  scale = font.scaleText(text, maxwidth = 0.440, scale = scale)
                  if scale > .0014:
                    scale = .0014
                  w, h = font.getStringSize(text, scale = scale)

                  lfont.render(text, (self.song_list_xpos+.05, .0935*(i+1)-pos[0]*.0935+.2), scale=scale)
  
                  if self.scoreTimer == 0 and self.highScoreType == 0: #racer: regular-style highscore movement
                    if self.diff == "Easy":
                      self.diff = "Medium"
                      self.diffNice = self.diffTrans[self.diff]
                    elif self.diff == "Medium":
                      self.diff = "Hard"
                      self.diffNice = self.diffTrans[self.diff]
                    elif self.diff == "Hard":
                      self.diff = "Expert"
                      self.diffNice = self.diffTrans[self.diff]
                    elif self.diff == "Expert":
                      self.diff = "Easy"
                      self.diffNice = self.diffTrans[self.diff]
  
                  #racer: score can be changed by fret button:
                  #MFH - and now they will be remembered as well
                  if self.highScoreChange == True and self.highScoreType == 1:
                    if self.diff == "Easy":
                      self.diff = "Medium"
                      self.diffNice = self.diffTrans[self.diff]
                      self.engine.config.set("game", "songlist_difficulty", 2)
                      self.highScoreChange = False
                    elif self.diff == "Medium":
                      self.diff = "Hard"
                      self.diffNice = self.diffTrans[self.diff]
                      self.engine.config.set("game", "songlist_difficulty", 1)
                      self.highScoreChange = False
                    elif self.diff == "Hard":
                      self.diff = "Expert"
                      self.diffNice = self.diffTrans[self.diff]
                      self.engine.config.set("game", "songlist_difficulty", 0)
                      self.highScoreChange = False
                    elif self.diff == "Expert":
                      self.diff = "Easy"
                      self.diffNice = self.diffTrans[self.diff]
                      self.engine.config.set("game", "songlist_difficulty", 3)
                      self.highScoreChange = False
  
                  score = _("Nil")
                  stars = 0
                  name = ""
                  
                  #for p in item.parts:    #MFH - look at selected instrument!
                  #  if str(p) == self.instrument:
                  for d in item.difficulties:
                    if str(d) == self.diff:
                      scores = item.getHighscores(d, part = Song.parts[self.instrumentNum])
                      #scores = item.getHighscoresWithPartString(d, part = self.instrument)
                      if scores:
                        score, stars, name, scoreExt = scores[0]
                        try:
                          notesHit, notesTotal, noteStreak, modVersion, handicap, handicapLong, originalScore = scoreExt
                        except ValueError:
                          notesHit, notesTotal, noteStreak, modVersion, oldScores1, oldScores2 = scoreExt
                          handicap = 0
                          handicapLong = "None"
                          originalScore = score
                      else:
                        score, stars, name = 0, 0, "---"

                  starx = self.song_listscore_xpos+.018
                  if self.extraStats:
                    stary = .0935*(i+1)-pos[0]*.0935+.1825-0.034
                  else:
                    stary = .0935*(i+1)-pos[0]*.0935+.2-0.034
                  #stary = 0.5
                  starscale = .025
                  stary = 1.0 - (stary / self.engine.data.fontScreenBottom) - h/2
                  self.engine.drawStarScore(screenw, screenh, starx, stary, stars, starscale, hqStar = True) #MFH

#-                  #QQstarS:add  to show stars
#-                  if stars == 7:
#-                    glColor3f(1, 1, 1)  # ought there be some special glyph for the perfect/fc scores..?
#-                    if self.extraStats:
#-                      lfont.render(unicode(Data.STAR4 * 5), (self.song_listscore_xpos+.018, .0935*(i+1)-pos[0]*.0935+.1825-0.034), scale = scale * 2.0) #Worldrave - Uses STAR3 and STAR4 now w/ fallback
#-                    else:
#-                      lfont.render(unicode(Data.STAR4 * 5), (self.song_listscore_xpos+.018, .0935*(i+1)-pos[0]*.0935+.2-0.034), scale = scale * 2.0) #Worldrave - Uses STAR3 and STAR4 now w/ fallback
#-                  elif stars == 6:
#-                    glColor3f(1, 1, 1)  
#-                    if self.extraStats:
#-                      lfont.render(unicode(Data.STAR4 * 5), (self.song_listscore_xpos+.018, .0935*(i+1)-pos[0]*.0935+.1825-0.034), scale = scale * 2.0) #Worldrave - Uses STAR3 and STAR4 now w/ fallback
#-                    else:
#-                      lfont.render(unicode(Data.STAR4 * 5), (self.song_listscore_xpos+.018, .0935*(i+1)-pos[0]*.0935+.2-0.034), scale = scale * 2.0) #Worldrave - Uses STAR3 and STAR4 now w/ fallback
#-                  elif score>0 and stars>=0 and name!="":
#-                    glColor3f(1, 1, 1)
#-                    #ShiekOdaSandz: Fixed stars so they display left to right, not right to left
#-                    if self.extraStats:
#-                      lfont.render(unicode(Data.STAR4 * stars+Data.STAR3 * (5 - stars)), (self.song_listscore_xpos+.018*.03, .0935*(i+1)-pos[0]*.0935+.1825-0.034), scale = scale * 2.0) #ShiekOdaSandz: Fixed stars so they display left to right, not right to left @Worldrave - Uses STAR3 and STAR4 now w/ fallback
#-                    else:
#-                      lfont.render(unicode(Data.STAR4 * stars+Data.STAR3 * (5 - stars)), (self.song_listscore_xpos+.018*.03, .0935*(i+1)-pos[0]*.0935+.2-0.034), scale = scale * 2.0) #ShiekOdaSandz: Fixed stars so they display left to right, not right to left @Worldrave - Uses STAR3 and STAR4 now w/ fallback
#-                    #QQstarS: end of add


  
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
                    lfont.render(text, (self.song_listscore_xpos+.1-w, .0935*(i+1)-pos[0]*.0935+.2), scale=scale*1.28)
                  else: #QQstarS: 
                    lfont.render(text, (self.song_listscore_xpos+.1-w, .0935*(i+1)-pos[0]*.0935+.2), scale=scale*1.28)
  
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
            if self.selectedIndex < 5 and maxIndex < 5:
              pos = self.selectedIndex - self.selectedIndex, self.selectedIndex + (5-self.selectedIndex)
              y = h*(.63-(.125*self.selectedIndex))
            elif self.selectedIndex == 0:
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

            self.engine.drawImage(self.selected, scale = (1,-1), coord = (w/2.1, y-h*.01))
  
            glColor4f(1,1,1,1)
            text = self.library
            w, h = font.getStringSize(text)
            if self.filepathenable:
              font.render(text, (self.song_list_xpos, .19))
            
            if self.searchText:
              text = _("Filter: %s") % (self.searchText) + "|"
              if not self.matchesSearch(self.items[self.selectedIndex]):
                text += " (%s)" % _("Not found")
              font.render(text, (.05, .7 + v), scale = 0.001)
            elif self.songLoader:
              font.render(_("Loading Preview..."), (.05, .7 + v), scale = 0.001)

            #Render song list items  
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
                      text = _("There Are %d Songs In This Setlist.") % (item.songCount)
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
                elif isinstance(item, Song.RandomSongInfo):
                  text = _("Random Song")
                  c1,c2,c3 = self.career_title_color
                  glColor3f(c1,c2,c3)
  
                if i == self.selectedIndex:
                  w, h = font.getStringSize(text)
                  font.render(text, (.5-w/2, .15))
                
                if i == self.selectedIndex:
                  glColor4f(.7,.5,.25,1)
                  if isinstance(item, Song.SongInfo) or isinstance(item, Song.RandomSongInfo):
                    c1,c2,c3 = self.song_name_selected_color
                    glColor3f(c1,c2,c3)
                  if isinstance(item, Song.LibraryInfo):
                    c1,c2,c3 = self.library_selected_color
                    glColor3f(c1,c2,c3)
                  if isinstance(item, Song.TitleInfo) or isinstance(item, Song.CareerResetterInfo) or isinstance(item, Song.BlankSpaceInfo):
                    c1,c2,c3 = self.career_title_color
                    glColor3f(c1,c2,c3)
                else:
                  glColor4f(0,0,0,1)
                  if isinstance(item, Song.SongInfo):
                    c1,c2,c3 = self.song_name_text_color
                    glColor3f(c1,c2,c3)
                  if isinstance(item, Song.RandomSongInfo):
                    c1,c2,c3 = self.song_name_text_color
                    glColor3f(c1,c2,c3)
                  if isinstance(item, Song.LibraryInfo):
                    c1,c2,c3 = self.library_text_color
                    glColor3f(c1,c2,c3)
                  if isinstance(item, Song.TitleInfo) or isinstance(item, Song.CareerResetterInfo) or isinstance(item, Song.BlankSpaceInfo):
                    c1,c2,c3 = self.career_title_color
                    glColor3f(c1,c2,c3)
                text = item.name
  
                if isinstance(item, Song.SongInfo) and item.getLocked():
                  text = _("-- Locked --")
  
                if isinstance(item, Song.SongInfo): #MFH - add indentation when tier sorting
                  if self.tiersArePresent:
                    text = self.indentString + text
  
                # evilynux/blazingamer - Force uppercase display
                if isinstance(item, Song.TitleInfo) or isinstance(item, Song.CareerResetterInfo) or isinstance(item, Song.BlankSpaceInfo):
                  text = string.upper(text)
  
                # evilynux - automatically scale song name
                scale = font.scaleText(text, maxwidth = 0.64)
                w, h = font.getStringSize(text, scale = scale)

                font.render(text, (self.song_list_xpos, .0935*(i+1)-pos[0]*.0935+.15), scale = scale)
  
                if isinstance(item, Song.SongInfo) and not item.getLocked():
                  scale = 0.0009
                  text = self.diffNice
                  w, h = font.getStringSize(text, scale=scale)
                  # evilynux - score color
                  c1,c2,c3 = self.songlist_score_color
                  glColor3f(c1,c2,c3)
                  if self.extraStats:
                    # evilynux - tweaked position to fit hit% and note streak
                    font.render(text, (self.song_listscore_xpos-w-.025, .0935*(i+1)-pos[0]*.0935+.185-h/2), scale=scale)
                  else:
                    font.render(text, (self.song_listscore_xpos-w-.025, .0935*(i+1)-pos[0]*.0935+.2-h/2), scale=scale)
                  
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
  
                  # evilynux - automatically scale artist name and year
                  scale = font.scaleText(text, maxwidth = 0.554, scale = scale)
                  if scale > .0014:
                    scale = .0014
                  w, h = font.getStringSize(text, scale = scale)

                  font.render(text, (self.song_list_xpos+.05, .0935*(i+1)-pos[0]*.0935+.2), scale=scale)
  
                  if self.scoreTimer == 0 and self.highScoreType == 0: #racer: regular-style highscore movement
                    if self.diff == "Easy":
                      self.diff = "Medium"
                      self.diffNice = self.diffTrans[self.diff]
                    elif self.diff == "Medium":
                      self.diff = "Hard"
                      self.diffNice = self.diffTrans[self.diff]
                    elif self.diff == "Hard":
                      self.diff = "Expert"
                      self.diffNice = self.diffTrans[self.diff]
                    elif self.diff == "Expert":
                      self.diff = "Easy"
                      self.diffNice = self.diffTrans[self.diff]
  
                  #racer: score can be changed by fret button:
                  #MFH - and now they will be remembered as well
                  if self.highScoreChange == True and self.highScoreType == 1:
                    if self.diff == "Easy":
                      self.diff = "Medium"
                      self.diffNice = self.diffTrans[self.diff]
                      self.engine.config.set("game", "songlist_difficulty", 2)
                      self.highScoreChange = False
                    elif self.diff == "Medium":
                      self.diff = "Hard"
                      self.diffNice = self.diffTrans[self.diff]
                      self.engine.config.set("game", "songlist_difficulty", 1)
                      self.highScoreChange = False
                    elif self.diff == "Hard":
                      self.diff = "Expert"
                      self.diffNice = self.diffTrans[self.diff]
                      self.engine.config.set("game", "songlist_difficulty", 0)
                      self.highScoreChange = False
                    elif self.diff == "Expert":
                      self.diff = "Easy"
                      self.diffNice = self.diffTrans[self.diff]
                      self.engine.config.set("game", "songlist_difficulty", 3)
                      self.highScoreChange = False
  
                  score = _("Nil")
                  stars = 0
                  name = ""
                  
                  #for p in item.parts:    #MFH - look at selected instrument!
                  #  if str(p) == self.instrument:
                  for d in item.difficulties:
                    if str(d) == self.diff:
                      scores = item.getHighscores(d, part = Song.parts[self.instrumentNum])
                      #scores = item.getHighscoresWithPartString(d, part = self.instrument)
                      if scores:
                        score, stars, name, scoreExt = scores[0]
                        try:
                          notesHit, notesTotal, noteStreak, modVersion, handicap, handicapLong, originalScore = scoreExt
                        except ValueError:
                          notesHit, notesTotal, noteStreak, modVersion, oldScores1, oldScores2 = scoreExt
                          handicap = 0
                          handicapLong = "None"
                          originalScore = score
                      else:
                        score, stars, name = 0, 0, "---"
  

                  starx = self.song_listscore_xpos-.01
                  if self.extraStats:
                    stary = .0935*(i+1)-pos[0]*.0935+.1705
                  else:
                    stary = .0935*(i+1)-pos[0]*.0935+.2-0.0145
                  #stary = 0.5
                  starscale = scale*1.8
                  stary = 1.0 - (stary / self.engine.data.fontScreenBottom)
                  if i < pos[1]:
                    self.engine.drawStarScore(screenw, screenh, starx, stary, stars, starscale) #MFH

#-                  #QQstarS:add  to show stars
#-                  # evilynux - Tweaked position to fit hit% and note streak
#-                  #            Readjusted star size following font fix
#-                  if stars == 7:
#-                    glColor3f(.6, .6, .75)    #platinum-y? stars in RB theme
#-                    if self.extraStats:
#-                      font.render(unicode(Data.STAR2 * 5), (self.song_listscore_xpos+.018, .0935*(i+1)-pos[0]*.0935+.18-0.0145), scale = scale * 1.8)
#-                    else:
#-                      font.render(unicode(Data.STAR2 * 5), (self.song_listscore_xpos+.018, .0935*(i+1)-pos[0]*.0935+.2-0.0145), scale = scale * 1.8)
#-                  if stars == 6:
#-                    glColor3f(1, 1, 0)    #gold stars in RB theme
#-                    if self.extraStats:
#-                      font.render(unicode(Data.STAR2 * 5), (self.song_listscore_xpos+.018, .0935*(i+1)-pos[0]*.0935+.18-0.0145), scale = scale * 1.8)
#-                    else:
#-                      font.render(unicode(Data.STAR2 * 5), (self.song_listscore_xpos+.018, .0935*(i+1)-pos[0]*.0935+.2-0.0145), scale = scale * 1.8)
#-                  elif score>0 and stars>=0 and name!="":
#-                    glColor3f(1, 1, 1)
#-                    # ShiekOdaSandz: Fixed stars so they display left to right, not right to left
#-                    if self.extraStats:
#-                      font.render(unicode(Data.STAR2 * stars+Data.STAR1 * (5 - stars)), (self.song_listscore_xpos+.018, .0935*(i+1)-pos[0]*.0935+.18-0.0145), scale = scale * 1.8)
#-                    else:
#-                      font.render(unicode(Data.STAR2 * stars+Data.STAR1 * (5 - stars)), (self.song_listscore_xpos+.018, .0935*(i+1)-pos[0]*.0935+.2-0.0145), scale = scale * 1.8)#ShiekOdaSandz: Fixed stars so they display left to right, not right to left
#-                  #QQstarS: end of add


  
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
        text = self.instrumentNice
        scale = 0.00250
        glColor3f(1, 1, 1)
        w, h = font.getStringSize(text, scale=scale)
        font.render(text, (0.85-w, 0.10), scale=scale)
        self.engine.view.resetProjection()

      elif self.display == 2:   #Qstick/Blazingamer - Combo CD/List
        item  = self.items[self.selectedIndex]
        i = self.selectedIndex
        if not self.listRotation:
          if self.itemLabels[i]:
            imgwidth = self.itemLabels[i].width1()
            wfactor = 214.000/imgwidth
            self.engine.drawImage(self.itemLabels[i], scale = (wfactor,-wfactor),
                                  coord = (self.song_listcd_cd_xpos * w,self.song_listcd_cd_ypos*h))
        else:
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
            self.camera.origin = (-9,(5.196/self.engine.view.aspectRatio) - (5.196*2/self.engine.view.aspectRatio)*self.song_listcd_cd_ypos,(5.196*self.engine.view.aspectRatio)-(5.196*2*self.engine.view.aspectRatio)*self.song_listcd_cd_xpos)
            self.camera.target = ( 0,(5.196/self.engine.view.aspectRatio) - (5.196*2/self.engine.view.aspectRatio)*self.song_listcd_cd_ypos,(5.196*self.engine.view.aspectRatio)-(5.196*2*self.engine.view.aspectRatio)*self.song_listcd_cd_xpos)
            self.camera.apply()
                
            y = 0.0

            

            glPushMatrix()
            if isinstance(item, Song.SongInfo):
              if self.songCoverType:
                self.renderCassette(item.cassetteColor, self.itemLabels[i])
              else:
                self.renderLibrary(item.cassetteColor, self.itemLabels[i])
            elif isinstance(item, Song.LibraryInfo):
              self.renderLibrary(item.color, self.itemLabels[i])
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
        font = self.engine.data.songListFont
        
        try:
          glEnable(GL_BLEND)
          glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
          glEnable(GL_COLOR_MATERIAL)
          Theme.setBaseColor(0)
          
          
          
          for i, item in enumerate(self.items):
            maxIndex = i
          if self.selectedIndex < 7 and maxIndex < 7:
            pos = self.selectedIndex - self.selectedIndex, self.selectedIndex + (7-self.selectedIndex)
            y = h*(.87-(.1*self.selectedIndex))
          elif self.selectedIndex == 0:#Selection is first item in list
            pos = (self.selectedIndex, self.selectedIndex +7)
            y = h*0.87
          elif self.selectedIndex == 1:#Second item in list
            pos = (self.selectedIndex-1, self.selectedIndex+6)
            y = h*0.77
          elif self.selectedIndex == 2:#Second item in list
            pos = (self.selectedIndex-2, self.selectedIndex+5)
            y = h*0.67
          elif self.selectedIndex == maxIndex-2:
            pos = (self.selectedIndex-4, self.selectedIndex+3)
            y = h*0.47
          elif self.selectedIndex == maxIndex-1:#Second to last item in list
            pos = (self.selectedIndex-5, self.selectedIndex+2)
            y = h*0.37
          elif self.selectedIndex == maxIndex and not self.selectedIndex == 1:#Third to Last in list and not third item
            pos = (self.selectedIndex-6, self.selectedIndex+1)
            y = h*0.27
          else:
            pos = (self.selectedIndex-3, self.selectedIndex+4)#Any other item than above
            y = h*0.57

          if self.theme == 0 or self.theme == 1:
            lfont = self.engine.data.songListFont
            sfont = self.engine.data.shadowfont
            
            glColor4f(1,1,1,1)
            text = self.library
            w, h = font.getStringSize(text)
            if self.filepathenable:
              font.render(text, (.05, .01))
            
            if self.searchText:
              text = _("Filter: %s") % (self.searchText) + "|"
              if not self.matchesSearch(self.items[self.selectedIndex]):
                text += " (%s)" % _("Not found")
              font.render(text, (.05, .7 + v), scale = 0.001)
            elif self.songLoader:
              font.render(_("Loading Preview..."), (.05, .7 + v), scale = 0.001)
              
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
                      text = _("There Are %d Songs In This Setlist.") % (item.songCount)
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
                elif isinstance(item, Song.RandomSongInfo):
                  text = _("Random Song")
                  c1,c2,c3 = self.career_title_color
                  glColor3f(c1,c2,c3)
                
                if i == self.selectedIndex:
                  w, h = font.getStringSize(text)
                  font.render(text, (self.song_listcd_score_xpos, .085), scale = 0.0012)
                
                if i == self.selectedIndex:
                  glColor4f(.7,.5,.25,1)
                  if isinstance(item, Song.SongInfo) or isinstance(item, Song.RandomSongInfo):
                    c1,c2,c3 = self.song_name_selected_color
                    glColor3f(c1,c2,c3)
                  if isinstance(item, Song.LibraryInfo):
                    c1,c2,c3 = self.library_selected_color
                    glColor3f(c1,c2,c3)
                  if isinstance(item, Song.TitleInfo) or isinstance(item, Song.CareerResetterInfo) or isinstance(item, Song.BlankSpaceInfo):
                    c1,c2,c3 = self.career_title_color
                    glColor3f(c1,c2,c3)
                else:
                  glColor4f(0,0,0,1)
                  if isinstance(item, Song.SongInfo) or isinstance(item, Song.RandomSongInfo):
                    c1,c2,c3 = self.song_name_text_color
                    glColor3f(c1,c2,c3)
                  if isinstance(item, Song.LibraryInfo):
                    c1,c2,c3 = self.library_text_color
                    glColor3f(c1,c2,c3)
                  if isinstance(item, Song.TitleInfo) or isinstance(item, Song.CareerResetterInfo) or isinstance(item, Song.BlankSpaceInfo):
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
                  
                if isinstance(item, Song.CareerResetterInfo):
                  text = string.upper(text)
  
                if isinstance(item, Song.BlankSpaceInfo):
                  text = string.upper(text)
                  
                scale = font.scaleText(text, maxwidth = 0.45)
                w, h = font.getStringSize(text, scale = scale)
                
                if i == self.selectedIndex:
                  sfont.render(text, (self.song_listcd_list_xpos, .09*(i+1)-pos[0]*.09), scale = scale) #add theme option for song_listCD_xpos
                else:
                  lfont.render(text, (self.song_listcd_list_xpos, .09*(i+1)-pos[0]*.09), scale = scale) #add theme option for song_listCD_xpos
                  
                angle = self.itemAngles[self.selectedIndex]
                f = ((90.0 - angle) / 90.0) ** 2
                
                if isinstance(item, Song.SongInfo) and not item.getLocked():
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
  
                  # evilynux - automatically scale artist name and year
                  scale = font.scaleText(text, maxwidth = 0.4, scale = scale)
                  w, h = font.getStringSize(text, scale = scale)

                  lfont.render(text, (self.song_listcd_list_xpos + .05, .09*(i+1)-pos[0]*.09+.05), scale=scale)
            
                
                item  = self.items[self.selectedIndex]
                if self.matchesSearch(item):
                  if isinstance(item, Song.SongInfo):
                    angle = self.itemAngles[self.selectedIndex]
                    f = ((90.0 - angle) / 90.0) ** 2

                    
                    c1,c2,c3 = self.songlistcd_score_color
                    glColor3f(c1,c2,c3)
      
                    scale = 0.0013
                    w, h = font.getStringSize(self.prompt, scale = scale)
                    x = self.song_listcd_score_xpos
                    y = self.song_listcd_score_ypos + f / 2.0
                    if len(item.difficulties) > 3:
                      y = self.song_listcd_score_ypos + f / 2.0
                    
                    #new
                    for d in item.difficulties:
                      #scores =  item.getHighscoresWithPartString(d, part = self.instrument)
                      scores =  item.getHighscores(d, part = Song.parts[self.instrumentNum])
                      if scores:
                        score, stars, name, scoreExt = scores[0]
                        try:
                          notesHit, notesTotal, noteStreak, modVersion, handicap, handicapLong, originalScore = scoreExt
                        except ValueError:
                          notesHit, notesTotal, noteStreak, modVersion, oldScores1, oldScores2 = scoreExt
                          handicap = 0
                          handicapLong = "None"
                          originalScore = score
                      else:
                        score, stars, name = "---", 0, "---"
                      #Theme.setBaseColor(1 - v)
                      lfont.render(unicode(d),     (x, y),           scale = scale)


                      starx = x
                      #stary = y+h
                      stary = y+h*1.5
                      #stary = 0.5+h
                      starscale = .025
                      stary = 1.0 - (stary / self.engine.data.fontScreenBottom)
                      self.engine.drawStarScore(screenw, screenh, starx, stary, stars, starscale, hqStar = True) #MFH

#-                      if stars == 6 and self.theme == 2:
#-                        glColor3f(1, 1, 0)  
#-                        lfont.render(unicode(Data.STAR2 * (stars -1)), (x, y + h), scale = scale * 1.8)
#-                      elif stars == 6:
#-                        glColor3f(0, 1, 0)  
#-                        lfont.render(unicode(Data.STAR2 * (stars -1)), (x, y + h), scale = scale * 1.8)
#-                      else:
#-                        lfont.render(unicode(Data.STAR2 * stars + Data.STAR1 * (5 - stars)), (x, y + h), scale = scale * 1.8)
#-                      #Theme.setSelectedColor(1 - v)
                      
                                      

                      c1,c2,c3 = self.songlistcd_score_color
                      glColor3f(c1,c2,c3)
                      if scores:
                        if self.extraStats:
                          if notesTotal != 0:
                            score = "%s %.1f%%" % (score, (float(notesHit) / notesTotal) * 100.0)
                          if noteStreak != 0:
                            score = "%s (%d)" % (score, noteStreak)
                      lfont.render(unicode(score), (x + .15, y),     scale = scale)
                      lfont.render(name,       (x + .15, y + h),     scale = scale)
                      y += 2 * h + f / 4.0
            
          elif self.theme == 2:
            if self.selectedlistcd == None:
              imgwidth = self.selected.width1()
              self.engine.drawImage(self.selected, scale = (.64, -1.05), coord = (self.song_listcd_list_xpos * w + (imgwidth*.64/2), y*1.2-h*.215))
            else:
              self.engine.drawImage(self.selectedlistcd, scale = (1,-1), coord =(self.song_listcd_list_xpos * w + (imgwidth/2), y*1.2-h*.215))
            
            glColor4f(1,1,1,1)
            text = self.library
            w, h = font.getStringSize(text)
            if self.filepathenable:
              font.render(text, (.05, .01))
            
            if self.searchText:
              text = _("Filter: %s") % (self.searchText) + "|"
              if not self.matchesSearch(self.items[self.selectedIndex]):
                text += " (%s)" % _("Not found")
              font.render(text, (.05, .7 + v), scale = 0.001)
            elif self.songLoader:
              font.render(_("Loading Preview..."), (.05, .7 + v), scale = 0.001)
              
            x = self.song_cdscore_xpos #Add theme.ini option for song_cdlistscore_xpos
            font.render(self.prompt, (self.song_listcd_score_xpos, .05-v))
            
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
                      text = _("There Are %d Songs In This Setlist.") % (item.songCount)
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
                elif isinstance(item, Song.RandomSongInfo):
                  text = _("Random Song")
                  c1,c2,c3 = self.career_title_color
                  glColor3f(c1,c2,c3)
                
                if i == self.selectedIndex:
                  w, h = font.getStringSize(text)
                  font.render(text, (self.song_listcd_score_xpos, .085), scale = 0.0012)
                
                if i == self.selectedIndex:
                  glColor4f(.7,.5,.25,1)
                  if isinstance(item, Song.SongInfo) or isinstance(item, Song.RandomSongInfo):
                    c1,c2,c3 = self.song_name_selected_color
                    glColor3f(c1,c2,c3)
                  if isinstance(item, Song.LibraryInfo):
                    c1,c2,c3 = self.library_selected_color
                    glColor3f(c1,c2,c3)
                  if isinstance(item, Song.TitleInfo) or isinstance(item, Song.BlankSpaceInfo) or isinstance(item, Song.CareerResetterInfo):
                    c1,c2,c3 = self.career_title_color
                    glColor3f(c1,c2,c3)
                else:
                  glColor4f(0,0,0,1)
                  if isinstance(item, Song.SongInfo) or isinstance(item, Song.RandomSongInfo):
                    c1,c2,c3 = self.song_name_text_color
                    glColor3f(c1,c2,c3)
                  if isinstance(item, Song.LibraryInfo):
                    c1,c2,c3 = self.library_text_color
                    glColor3f(c1,c2,c3)
                  if isinstance(item, Song.TitleInfo) or isinstance(item, Song.CareerResetterInfo) or isinstance(item, Song.BlankSpaceInfo):
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
                  
                if isinstance(item, Song.CareerResetterInfo):
                  text = string.upper(text)
  
                if isinstance(item, Song.BlankSpaceInfo):
                  text = string.upper(text)
                  
                scale = font.scaleText(text, maxwidth = 0.45)
                w, h = font.getStringSize(text, scale = scale)

                font.render(text, (self.song_listcd_list_xpos, .09*(i+1)-pos[0]*.09), scale = scale) #add theme option for song_listCD_xpos
                
                if isinstance(item, Song.SongInfo) and not item.getLocked():
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
  
                  # evilynux - automatically scale artist name and year
                  scale = font.scaleText(text, maxwidth = 0.4, scale = scale)
                  w, h = font.getStringSize(text, scale = scale)

                  font.render(text, (self.song_listcd_list_xpos + .05, .09*(i+1)-pos[0]*.09+.05), scale=scale) #add theme song_listCD_Xpos
            
                
                item  = self.items[self.selectedIndex]
                if self.matchesSearch(item):
                  if isinstance(item, Song.SongInfo):
                    angle = self.itemAngles[self.selectedIndex]
                    f = ((90.0 - angle) / 90.0) ** 2
        
                    Theme.setSelectedColor(1 - v)
                    
                    c1,c2,c3 = self.songlistcd_score_color
                    glColor3f(c1,c2,c3)
      
                    scale = 0.0013
                    w, h = font.getStringSize(self.prompt, scale = scale)
                    x = self.song_listcd_score_xpos
                    y = self.song_listcd_score_ypos + f / 2.0
                    if len(item.difficulties) > 3:
                      y = self.song_listcd_score_ypos + f / 2.0
                    
                    #new
                    for d in item.difficulties:
                      #scores =  item.getHighscoresWithPartString(d, part = self.instrument)
                      scores =  item.getHighscores(d, part = Song.parts[self.instrumentNum])
                      if scores:
                        score, stars, name, scoreExt = scores[0]
                        try:
                          notesHit, notesTotal, noteStreak, modVersion, handicap, handicapLong, originalScore = scoreExt
                        except ValueError:
                          notesHit, notesTotal, noteStreak, modVersion, oldScores1, oldScores2 = scoreExt
                          handicap = 0
                          handicapLong = "None"
                          originalScore = score
                      else:
                        score, stars, name = "---", 0, "---"
                      
                      font.render(unicode(d),     (x, y),           scale = scale)
                      

                      starx = x + .01
                      #stary = y+h
                      stary = y + .032
                      #stary = 0.5+h
                      starscale = scale*1.8
                      stary = 1.0 - (stary / self.engine.data.fontScreenBottom)
                      self.engine.drawStarScore(screenw, screenh, starx, stary, stars, starscale) #MFH

#-                      if stars == 7 and self.theme == 2:
#-                        glColor3f(.6, .6, .75)  
#-                        font.render(unicode(Data.STAR2 * (stars -1)), (x, y + h), scale = scale * 1.8)
#-                      elif stars == 7:
#-                        glColor3f(0, .75, 1)  
#-                        font.render(unicode(Data.STAR2 * (stars -1)), (x, y + h), scale = scale * 1.8)
#-                      if stars == 6 and self.theme == 2:
#-                        glColor3f(1, 1, 0)  
#-                        font.render(unicode(Data.STAR2 * (stars -1)), (x, y + h), scale = scale * 1.8)
#-                      elif stars == 6:
#-                        glColor3f(0, 1, 0)  
#-                        font.render(unicode(Data.STAR2 * (stars -1)), (x, y + h), scale = scale * 1.8)
#-                      else:
#-                        font.render(unicode(Data.STAR2 * stars + Data.STAR1 * (5 - stars)), (x, y + h), scale = scale * 1.8)
#-                      #Theme.setSelectedColor(1 - v)
                      
                                      
                      c1,c2,c3 = self.songlistcd_score_color
                      glColor3f(c1,c2,c3)
                      if scores:
                        if self.extraStats:
                          if notesTotal != 0:
                            score = "%s %.1f%%" % (score, (float(notesHit) / notesTotal) * 100.0)
                          if noteStreak != 0:
                            score = "%s (%d)" % (score, noteStreak)
                      font.render(unicode(score), (x + .15, y),     scale = scale)
                      font.render(name,       (x + .15, y + h),     scale = scale)
                      y += 2 * h + f / 4.0
              
        finally:
          text = self.instrumentNice
          scale = 0.00250
          glColor3f(1, 1, 1)
          w, h = font.getStringSize(text, scale=scale)
          font.render(text, (0.95-w, 0.000), scale=scale)
          self.engine.view.resetProjection()
          nuttin = True

          
      elif self.display == 3:   #Qstick - rb2 Mode
        item  = self.items[self.selectedIndex]
        i = self.selectedIndex
        if self.itemLabels[i] == "Empty":   #added so that emptylabel.png is only loaded once and not on every empty song
          if self.emptyLabel != None:
            imgwidth = self.emptyLabel.width1()
            wfactor = 155.000/imgwidth
            self.engine.drawImage(self.emptyLabel, scale = (wfactor,-wfactor), coord = (.21*w,.59*h))
        elif self.itemLabels[i] == "Locked":   #added so that emptylabel.png is only loaded once and not on every empty song
          if self.lockedLabel != None:
            imgwidth = self.lockedLabel.width1()
            wfactor = 155.000/imgwidth
            self.engine.drawImage(self.lockedLabel, scale = (wfactor,-wfactor), coord = (.21*w,.59*h))
        elif self.itemLabels[i]:
          imgwidth = self.itemLabels[i].width1()
          wfactor = 155.000/imgwidth
          self.engine.drawImage(self.itemLabels[i], scale = (wfactor,-wfactor), coord = (.21*w,.59*h))

        self.engine.view.setOrthogonalProjection(normalize = True)
        font = self.engine.data.songListFont
        
        try:
          glEnable(GL_BLEND)
          glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
          glEnable(GL_COLOR_MATERIAL)
          Theme.setBaseColor(0)
          
          
          for i, item in enumerate(self.items):
            maxIndex = i
          if self.selectedIndex < 11 and maxIndex < 11:
            pos = self.selectedIndex - self.selectedIndex, self.selectedIndex + (11-self.selectedIndex)
            y = h*(.7825-(.0459*self.selectedIndex))
          elif self.selectedIndex == 0:#Selection is first item in list
            pos = (self.selectedIndex, self.selectedIndex +11)
            y = h*0.7825
          elif self.selectedIndex == 1:#Second item in list
            pos = (self.selectedIndex-1, self.selectedIndex+10)
            y = h*0.7365
          elif self.selectedIndex == 2:#Second item in list
            pos = (self.selectedIndex-2, self.selectedIndex+9)
            y = h*0.6909
          elif self.selectedIndex == 3:
            pos = (self.selectedIndex-3, self.selectedIndex+8)
            y = h*0.6447
          elif self.selectedIndex == 4:
            pos = (self.selectedIndex-4, self.selectedIndex+7)
            y = h*0.5988
          elif self.selectedIndex == 5:
            pos = (self.selectedIndex-5, self.selectedIndex+6)
            y = h*0.5529
          elif self.selectedIndex == maxIndex-4:
            pos = (self.selectedIndex-7, self.selectedIndex+4)
            y = h*0.4611
          elif self.selectedIndex == maxIndex-3:
            pos = (self.selectedIndex-8, self.selectedIndex+3)
            y = h*0.4152
          elif self.selectedIndex == maxIndex-2:
            pos = (self.selectedIndex-9, self.selectedIndex+2)
            y = h*0.3693
          elif self.selectedIndex == maxIndex-1:#Second to last item in list
            pos = (self.selectedIndex-10, self.selectedIndex+1)
            y = h*0.3234
          elif self.selectedIndex == maxIndex and not self.selectedIndex == 2:#Third to Last in list and not third item
            pos = (self.selectedIndex-11, self.selectedIndex)
            y = h*0.2775
          else:
            pos = (self.selectedIndex-6, self.selectedIndex+5)#Any other item than above
            y = h*0.507
            
            
          if self.tierbg != None:
            imgwidth = self.tierbg.width1()
            imgheight = self.tierbg.height1()
            wfactor = 381.1/imgwidth
            hfactor = 24.000/imgheight
          for i, item in enumerate(self.items):
            if i >= pos[0] and i <= pos[1]:
              if isinstance(item, Song.TitleInfo) or isinstance(item, Song.SortTitleInfo):
                if self.tierbg != None:
                  w, h, = self.engine.view.geometry[2:4]
                  self.engine.drawImage(self.tierbg, scale = (wfactor,-hfactor), coord = (w/1.587, h-((0.055*h)*(i+1)-pos[0]*(0.055*h))-(0.219*h)))


          imgwidth = self.selected.width1()
          imgheight = self.selected.height1()
          wfactor = 381.5/imgwidth
          hfactor = 36.000/imgheight

          self.engine.drawImage(self.selected, scale = (wfactor,-hfactor), coord = (w/1.587, y*1.2-h*.213))
          
          
          if self.diffimg1 != None:
            imgwidth = self.diffimg3.width1()
            imgheight = self.diffimg3.height1()
            wfactor1 = 13.0/imgwidth

          c1,c2,c3 = self.song_rb2_diff_color
          glColor3f(c1,c2,c3)
          
          font.render(_("DIFFICULTY"), (.095, .54), scale = 0.0018)
          scale = 0.0014
          text = _("BAND")
          w, h = font.getStringSize(text, scale = scale)
          font.render(text, (.17 - w, .57), scale = scale)
          text = _("GUITAR")
          w, h = font.getStringSize(text, scale = scale)
          font.render(text, (.17 - w, .595), scale = scale)
          text = _("DRUM")
          w, h = font.getStringSize(text, scale = scale)
          font.render(text, (.17 - w, .62), scale = scale)
          text = _("BASS")
          w, h = font.getStringSize(text, scale = scale)
          font.render(text, (.17 - w, .645), scale = scale)

          #Add support for lead and rhythm diff          

          #Qstick - Sorting Text
          text = _("SORTING:") + "     "
          if self.sortOrder == 0: #title
            text = text + _("ALPHABETICALLY BY TITLE")
          elif self.sortOrder == 1: #artist
            text = text + _("ALPHABETICALLY BY ARTIST")
          elif self.sortOrder == 2: #timesplayed
            text = text + _("BY PLAY COUNT")
          elif self.sortOrder == 3: #album
            text = text + _("ALPHABETICALLY BY ALBUM")
          elif self.sortOrder == 4: #genre
            text = text + _("ALPHABETICALLY BY GENRE")
          elif self.sortOrder == 5: #year
            text = text + _("BY YEAR")
          elif self.sortOrder == 6: #Band Difficulty
            text = text + _("BY BAND DIFFICULTY")
          elif self.sortOrder == 7: #Band Difficulty
            text = text + _("BY INSTRUMENT DIFFICULTY")
          else:
            text = text + _("BY SONG COLLECTION")
            
          font.render(text, (.13, .152), scale = 0.0017)

          if self.searchText:
            text = _("Filter: %s") % (self.searchText) + "|"
            if not self.matchesSearch(self.items[self.selectedIndex]):
              text += " (%s)" % _("Not found")
            font.render(text, (.05, .7 + v), scale = 0.001)
          elif self.songLoader:
            font.render(_("Loading Preview..."), (.05, .7 + v), scale = 0.001)
          
          for i, item in enumerate(self.items):
            if i >= pos[0] and i <= pos[1]:

              if isinstance(item, Song.SongInfo):
                if self.songIcons:    
                  if item.icon != "":
                    iconNum = None
                    try:
                      iconNum = self.itemIconNames.index(item.icon)
                      imgwidth = self.itemIcons[iconNum].width1()
                      wfactor = 23.000/imgwidth
                      w, h, = self.engine.view.geometry[2:4]
                      self.engine.drawImage(self.itemIcons[iconNum], scale = (wfactor,-wfactor), coord = (w/2.86, h-((0.055*h)*(i+1)-pos[0]*(0.055*h))-(0.219*h)))
                    except ValueError:
                      iconNum = -1
                
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
                    text = _("There Are %d Songs In This Setlist.") % (item.songCount)
                  else:
                    text = ""
              elif isinstance(item, Song.TitleInfo) or isinstance(item, Song.SortTitleInfo):
                text = _("Tier")
                c1,c2,c3 = self.career_title_color
                glColor3f(c1,c2,c3)
                

              elif isinstance(item, Song.CareerResetterInfo):
                text = _("Reset this entire career")
                c1,c2,c3 = self.career_title_color
                glColor3f(c1,c2,c3)
                
              elif isinstance(item, Song.RandomSongInfo):
                text = _("Random Song")
                c1,c2,c3 = self.career_title_color
                glColor3f(c1,c2,c3)
              
              if i == self.selectedIndex:
                w, h = font.getStringSize(text, scale = 0.0012)
                font.render(text, (0.92-w, .13), scale = 0.0012)
              
              maxwidth = .45
              if i == self.selectedIndex:
                glColor4f(.7,.5,.25,1)
                if isinstance(item, Song.SongInfo) or isinstance(item, Song.LibraryInfo) or isinstance(item, Song.RandomSongInfo):
                  c1,c2,c3 = self.song_rb2_name_selected_color
                  glColor3f(c1,c2,c3)
                if isinstance(item, Song.TitleInfo) or isinstance(item, Song.SortTitleInfo) or isinstance(item, Song.CareerResetterInfo) or isinstance(item, Song.BlankSpaceInfo):
                  c1,c2,c3 = self.career_title_color
                  glColor3f(c1,c2,c3)
              else:
                glColor4f(0,0,0,1)
                if isinstance(item, Song.SongInfo) or isinstance(item, Song.LibraryInfo):
                  c1,c2,c3 = self.song_rb2_name_color
                  glColor3f(c1,c2,c3)
                if isinstance(item, Song.TitleInfo) or isinstance(item, Song.SortTitleInfo) or isinstance(item, Song.CareerResetterInfo) or isinstance(item, Song.BlankSpaceInfo):
                  c1,c2,c3 = self.career_title_color
                  glColor3f(c1,c2,c3)
                if isinstance(item, Song.RandomSongInfo):
                  c1,c2,c3 = self.song_name_text_color
                  glColor3f(c1,c2,c3)
              
              text = item.name
              
              if isinstance(item, Song.SongInfo) and item.getLocked():
                text = _("-- Locked --")
                
              if isinstance(item, Song.SongInfo): #MFH - add indentation when tier sorting
                if self.tiersArePresent or self.songIcons:
                  text = self.indentString + text
                

              # evilynux - Force uppercase display for Career titles
              if isinstance(item, Song.TitleInfo) or isinstance(item, Song.SortTitleInfo):
                maxwidth = .55
                
              if isinstance(item, Song.TitleInfo) or isinstance(item, Song.SortTitleInfo) or isinstance(item, Song.CareerResetterInfo) or isinstance(item, Song.BlankSpaceInfo):
                text = string.upper(text)
                
              scale = .0015
              w, h = font.getStringSize(text, scale = scale)

              while w > maxwidth:
                tlength = len(text) - 4
                text = text[:tlength] + "..."
                w, h = font.getStringSize(text, scale = scale)
                if w < .45:
                  break
                
                
              font.render(text, (.35, .0413*(i+1)-pos[0]*.0413+.15), scale = scale) #add theme option for song_listCD_xpos

              if isinstance(item, Song.SongInfo):
                if self.scoreTimer == 0 and self.highScoreType == 0: #racer: regular-style highscore movement
                  if self.diff == "Easy":
                    self.diff = "Medium"
                    self.diffNice = self.diffTrans[self.diff]
                  elif self.diff == "Medium":
                    self.diff = "Hard"
                    self.diffNice = self.diffTrans[self.diff]
                  elif self.diff == "Hard":
                    self.diff = "Expert"
                    self.diffNice = self.diffTrans[self.diff]
                  elif self.diff == "Expert":
                    self.diff = "Easy"
                    self.diffNice = self.diffTrans[self.diff]
                
                #racer: score can be changed by fret button:
                #MFH - and now they will be remembered as well
                if self.highScoreChange == True and self.highScoreType == 1:
                  if self.diff == "Easy":
                    self.diff = "Medium"
                    self.diffNice = self.diffTrans[self.diff]
                    self.engine.config.set("game", "songlist_difficulty", 2)
                    self.highScoreChange = False
                  elif self.diff == "Medium":
                    self.diff = "Hard"
                    self.diffNice = self.diffTrans[self.diff]
                    self.engine.config.set("game", "songlist_difficulty", 1)
                    self.highScoreChange = False
                  elif self.diff == "Hard":
                    self.diff = "Expert"
                    self.diffNice = self.diffTrans[self.diff]
                    self.engine.config.set("game", "songlist_difficulty", 0)
                    self.highScoreChange = False
                  elif self.diff == "Expert":
                    self.diff = "Easy"
                    self.diffNice = self.diffTrans[self.diff]
                    self.engine.config.set("game", "songlist_difficulty", 3)
                    self.highScoreChange = False

                if not (item.getLocked()):
                  score = _("Nil")
                  stars = 0
                  name = ""
                  
                  #for p in item.parts:    #MFH - look at selected instrument!
                  #  if str(p) == self.instrument:
                  for d in item.difficulties:
                    if str(d) == self.diff:
                      scores = item.getHighscores(d, part = Song.parts[self.instrumentNum])
                      #scores = item.getHighscoresWithPartString(d, part = self.instrument)
                      if scores:
                        score, stars, name, scoreExt = scores[0]
                        try:
                          notesHit, notesTotal, noteStreak, modVersion, handicap, handicapLong, originalScore = scoreExt
                        except ValueError:
                          notesHit, notesTotal, noteStreak, modVersion, oldScores1, oldScores2 = scoreExt
                          handicap = 0
                          handicapLong = "None"
                          originalScore = score
                      else:
                        score, stars, name = 0, 0, "---"
  
  
                  scale = 0.0014
                  #evilynux - hit% and note streak if enabled
                  if self.extraStats:
                    scale = 0.0009
                    if score is not _("Nil") and score > 0 and notesTotal != 0:
                      text = "%.1f%% (%d)" % ((float(notesHit) / notesTotal) * 100.0, noteStreak)
                      w, h = font.getStringSize(text, scale=scale)
                      font.render(text, (.92-w, .0413*(i+1)-pos[0]*.0413+.163), scale=scale)
                        
                  text = str(score)
                  w, h = font.getStringSize(text, scale=scale)
                  
                  font.render(text, (.92-w, .0413*(i+1)-pos[0]*.0413+.15), scale=scale)
  
                  if self.scoreTimer < 1000:
                    self.scoreTimer += 1
                  else:
                    self.scoreTimer = 0
                    
                  if i == self.selectedIndex:
                    text = item.artist
                    if (item.getLocked()):
                      text = "" # avoid giving away artist of locked song
  
                    scale = 0.0015
                    w, h = font.getStringSize(text, scale=scale)
                    
                    while w > .21:
                      tlength = len(text) - 4
                      text = text[:tlength] + "..."
                      w, h = font.getStringSize(text, scale = scale)
                      if w < .22:
                        break
                      
                    c1,c2,c3 = self.song_rb2_artist_color
                    glColor3f(c1,c2,c3)
                    
                    text = string.upper(text)
                    font.render(text, (.095, .44), scale = scale)
                    
                    albumtag = item.album
                      
                    albumtag = string.upper(albumtag)
                    w, h = font.getStringSize(albumtag, scale=scale)
                    
                    while w > .21:
                      tlength = len(albumtag) - 4
                      albumtag = albumtag[:tlength] + "..."
                      w, h = font.getStringSize(albumtag, scale = scale)
                      if w < .22:
                        break                    
  
                    font.render(albumtag, (.095, .47), scale = 0.0015)
                    
                    genretag = item.genre
                    font.render(genretag, (.095, .49), scale = 0.0015)                                
  
                    yeartag = item.year           
                    font.render(yeartag, (.095, .51), scale = 0.0015)

                 
                    for i in range(0,4):
                      glColor3f(1, 1, 1) 
                      if i == 0:
                        diff = item.diffSong
                      if i == 1:
                        diff = item.diffGuitar
                      if i == 2:
                        diff = item.diffDrums
                      if i == 3:
                        diff = item.diffBass
                      if self.diffimg1 == None:
                        if diff == -1:
                          font.render("N/A", (.18, .57 + i*.025), scale = 0.0014)
                        elif diff == 6:
                          glColor3f(1, 1, 0)  
                          font.render(unicode(Data.STAR2 * (diff -1)), (.18, 0.575 + i*.025), scale = 0.003)
                        else:
                          font.render(unicode(Data.STAR2 * diff + Data.STAR1 * (5 - diff)), (.18, 0.575 + i*.025), scale = 0.003)
                      else:
                        w, h, = self.engine.view.geometry[2:4]
                        if diff == -1:
                          font.render("N/A", (.18, .57 + i*.025), scale = 0.0014)
                        elif diff == 6:
                          for k in range(0,5):
                            self.engine.drawImage(self.diffimg3, scale = (wfactor1,-wfactor1), coord = ((.19+.03*k)*w, (0.22-.035*i)*h))
                        else:
                          for k in range(0,diff):
                            self.engine.drawImage(self.diffimg2, scale = (wfactor1,-wfactor1), coord = ((.19+.03*k)*w, (0.22-.035*i)*h))
                          for k in range(0, 5-diff):
                            self.engine.drawImage(self.diffimg1, scale = (wfactor1,-wfactor1), coord = ((.31-.03*k)*w, (0.22-.035*i)*h))
           
        finally:
          text = self.instrumentNice + " - " + self.diffNice
          scale = 0.0017
          glColor3f(1, 1, 1)
          w, h = font.getStringSize(text, scale=scale)
          font.render(text, (0.92-w, 0.152), scale=scale)
          self.engine.view.resetProjection()
          nuttin = True
          
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

    self.logClassInits = self.engine.config.get("game", "log_class_inits")
    if self.logClassInits == 1:
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
      self.engine.drawImage(self.neckBlackBack, scale = (wfactor,-wfactor), coord = (w/2,h/2))


    #MFH - auto background scaling 
    imgwidth = self.background.width1()
    wfactor = 640.000/imgwidth
    self.engine.drawImage(self.background, scale = (wfactor,-wfactor), coord = (w/2,h/2))


      
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
  def __init__(self, engine, selected = None, prompt = "", player = 0):
    self.prompt         = prompt
    self.prompt_x       = Theme.neck_prompt_x
    self.prompt_y       = Theme.neck_prompt_y
    self.engine         = engine
    self.player         = player

    self.logClassInits = self.engine.config.get("game", "log_class_inits")
    if self.logClassInits == 1:
      Log.debug("Player %d NeckChooser class init (Dialogs.py)..." % (self.player))
    
    splash = showLoadingSplashScreen(self.engine, _("Loading necks..."))

    self.neck = []
    self.necks = ["2none", "none"]
    self.maxNeck = 0

    self.neckSettingName = "neck_choose_p%d" % (self.player)
    self.selectedNeck = Config.get("coffee", self.neckSettingName)

    # evilynux - improved loading logic to support arbitrary filenames
    #          - os.listdir is not garanteed to return a sorted list, so sort it!
    neckfiles = os.listdir(self.engine.resource.fileName("necks"))
    neckfiles.sort()

    for i in neckfiles:   #MFH - first go through and find the random neck
      if ( str(i) == "randomneck.png"  or str(i) == "Neck_0.png" ):    #MFH 
        randomNeck = i
        #exists = 1
        
        try:
          neckImage = engine.loadImgDrawing(self, "neck"+str(i), os.path.join("necks",str(i)))
          # evilynux - Warning, Thumbs.db won't fail at engine.loadImgDrawing
  
        except IOError:
          exists = 0
          break

        if neckImage is None:
          exists = 0
        else:
          exists = 1
  
        if exists == 1:
          self.neck.append(str(i)[:-4]) # evilynux - filename w/o extension
          self.necks.append(neckImage)


    for i in neckfiles:
      # evilynux - Special cases, ignore these...
      #if( str(i) == "overdriveneck.png" or str(i)[-4:] != ".png" ):
      #exists = 1
      #if( str(i) == "overdriveneck.png" or not i.endswith(".png") ):
      if( str(i) == "overdriveneck.png" or str(i) == "randomneck.png"  or str(i) == "Neck_0.png" or str(i)[-4:] != ".png" ):    #MFH 
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
    Config.define("coffee",   self.neckSettingName,  str,  0,  text = _("Neck"), options = self.neck)
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
      Settings.ConfigChoice(engine, engine.config, "coffee",   self.neckSettingName, autoApply = True)
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
    self.selectedNeck = Config.get("coffee", self.neckSettingName)    #MFH - update this in the run not render
    
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
     self.engine.drawImage(self.neckBlackBack, scale = (wfactor,-wfactor), coord = (w/2,h/2))



   #self.selectedNeck = Config.get("coffee", self.neckSettingName)
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
   if self.theme != 2:
     neckcoord = (w/1.31,h/2)
   else:
     neckcoord = (w/1.22,h/2)
   self.engine.drawImage(currentNeck, scale = (-wfactor,wfactor), coord = neckcoord)
   

   wfactor = lastNeck1.widthf(pixelw = self.wfac2)
   self.engine.drawImage(lastNeck1, scale = (-wfactor,wfactor), coord = (self.x1,self.y1))
   wfactor = lastNeck.widthf(pixelw = self.wfac2)
   self.engine.drawImage(lastNeck, scale = (-wfactor,wfactor), coord = (self.x2,self.y2))
   wfactor = currentNeck.widthf(pixelw = self.wfac2)
   self.engine.drawImage(currentNeck, scale = (-wfactor,wfactor), coord = (self.x3,self.y3))
   wfactor = nextNeck.widthf(pixelw = self.wfac2)
   self.engine.drawImage(nextNeck, scale = (-wfactor,wfactor), coord = (self.x4,self.y4))   
   wfactor = nextNeck1.widthf(pixelw = self.wfac2)
   self.engine.drawImage(nextNeck1, scale = (-wfactor,wfactor), coord = (self.x5,self.y5))
   
   if self.menu.currentIndex == 0:
     self.engine.drawImage(self.neckSelect, scale = (-1,1), coord = (self.x6, self.y6))

   #MFH - draw neck BG on top of necks
   #MFH - auto background scaling
   imgwidth = self.neckBG.width1()
   wfactor = 640.000/imgwidth
   self.engine.drawImage(self.neckBG, scale = (wfactor,-wfactor), coord = (w/2,h/2))

  
   self.engine.view.setOrthogonalProjection(normalize = True)
   font = self.engine.data.font
   
   try:
     glEnable(GL_BLEND)
     glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
     glEnable(GL_COLOR_MATERIAL)
     Theme.setBaseColor(1 - v)
     wrapText(font, (self.prompt_x, self.prompt_y - v), self.prompt)
   finally:
     self.engine.view.resetProjection()
   #==============================================================

    
    


class ItemChooser(BackgroundLayer, KeyListener):
  """Item menu layer."""
  def __init__(self, engine, items, selected = None, prompt = "", pos = None):    #MFH
    self.prompt         = prompt
    self.engine         = engine
    
    self.logClassInits = self.engine.config.get("game", "log_class_inits")
    if self.logClassInits == 1:
      Log.debug("ItemChooser class init (Dialogs.py)...")
    
    self.accepted       = False
    self.selectedItem   = None
    self.time           = 0.0

    self.font = self.engine.data.streakFont2
    self.promptScale = 0.002
    self.promptWidth, self.promptHeight = self.font.getStringSize(self.prompt, scale=self.promptScale)
    widthOfSpace, heightOfSpace = self.font.getStringSize(" ", scale=self.promptScale)

    if pos: #MFH
      self.songSelectSubmenuOffsetLines = Theme.songSelectSubmenuOffsetLines
      self.songSelectSubmenuOffsetSpaces = Theme.songSelectSubmenuOffsetSpaces
      self.posX, self.posY = pos
      wrapX, wrapY = wrapText(self.font, (self.posX, self.posY), self.prompt, scale = self.promptScale)
      #self.posY += self.promptHeight*2
      #self.posX -= self.promptWidth/2
      #self.menu = Menu(self.engine, choices = [(c, self._callbackForItem(c)) for c in items], onClose = self.close, onCancel = self.cancel, font = self.engine.data.streakFont2, pos = (self.posX + widthOfSpace*2, wrapY + self.promptHeight*2) )
      self.menu = Menu(self.engine, choices = [(c, self._callbackForItem(c)) for c in items], onClose = self.close, onCancel = self.cancel, font = self.engine.data.streakFont2, pos = (self.posX + widthOfSpace*(self.songSelectSubmenuOffsetSpaces+1), wrapY + self.promptHeight*(self.songSelectSubmenuOffsetLines+1)) )
    else:
      self.posX = .1    #MFH - default
      self.posY = .05   #MFH - default
      self.menu = Menu(self.engine, choices = [(c, self._callbackForItem(c)) for c in items], onClose = self.close, onCancel = self.cancel, font = self.engine.data.streakFont2)
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
    self.engine.drawImage(self.background, scale = (wfactor,-wfactor), coord = (w/2,h/2))

      
    self.engine.view.setOrthogonalProjection(normalize = True)
    
    
    try:
      glEnable(GL_BLEND)
      glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
      glEnable(GL_COLOR_MATERIAL)
      Theme.setBaseColor(1 - v)
      #wrapText(self.font, (.1, .05 - v), self.prompt)
      wrapText(self.font, (self.posX, self.posY - v), self.prompt, scale = self.promptScale)
    finally:
      self.engine.view.resetProjection()
      
      
class BpmEstimator(Layer, KeyListener):
  """Beats per minute value estimation layer."""
  def __init__(self, engine, song, prompt = ""):
    self.prompt         = prompt
    self.engine         = engine

    self.logClassInits = self.engine.config.get("game", "log_class_inits")
    if self.logClassInits == 1:
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
    
    self.logClassInits = self.engine.config.get("game", "log_class_inits")
    if self.logClassInits == 1:
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
      self.playerList = [0,1] # evilynux - Static for now, should be eventually made dynamic to support more players
      self.analogKillMode = [self.engine.config.get("game", "analog_killsw_mode"),self.engine.config.get("game", "analog_killsw_mode_p2")]
      self.whammyVolAdjStep = 0.1
      self.isKillAnalog = [False for i in self.playerList]
      self.whichJoy = [0 for i in self.playerList]
      self.whichAxis = [0 for i in self.playerList]
      self.whammyVol = [0.0 for i in self.playerList]
      self.targetWhammyVol = [0.0 for i in self.playerList]
      self.defaultWhammyVol = [self.analogKillMode[i]-1.0 for i, thePlayer in enumerate(self.playerList)]   #makes xbox defaults 1.0, PS2 defaults 0.0

      for i, thePlayer in enumerate(self.playerList):
        if self.analogKillMode[i] == 3:   #XBOX inverted mode
          self.defaultWhammyVol[i] = -1.0

      self.actualWhammyVol = [self.defaultWhammyVol[i] for i, thePlayer in enumerate(self.playerList)]
      self.lastWhammyVol = [self.defaultWhammyVol[i] for i, thePlayer in enumerate(self.playerList)]
      KillKeyCode = [0 for i in self.playerList]

      if len(self.engine.input.joysticks) != 0:
        if self.analogKillMode[0] > 0:
          KillKeyCode[0] = self.controls.getReverseMapping(Player.KILL)
          self.isKillAnalog[0], self.whichJoy[0], self.whichAxis[0] = self.engine.input.getWhammyAxis(KillKeyCode[0])
        if self.analogKillMode[1] > 0:
          KillKeyCode[1] = self.controls.getReverseMapping(Player.PLAYER_2_KILL)
          self.isKillAnalog[1], self.whichJoy[1], self.whichAxis[1] = self.engine.input.getWhammyAxis(KillKeyCode[1])
  
        #evilynux - Compute analog killswitch value
        for i, thePlayer in enumerate(self.playerList):
          if self.isKillAnalog[i]:
            if self.analogKillMode[i] == 2:  #XBOX mode: (1.0 at rest, -1.0 fully depressed)
              self.whammyVol[i] = 1.0 - (round(10* ((self.engine.input.joysticks[self.whichJoy[i]].get_axis(self.whichAxis[i])+1.0) / 2.0 ))/10.0)

            elif self.analogKillMode[i] == 3:  #XBOX Inverted mode: (-1.0 at rest, 1.0 fully depressed)
              self.whammyVol[i] = (round(10* ((self.engine.input.joysticks[self.whichJoy[i]].get_axis(self.whichAxis[i])+1.0) / 2.0 ))/10.0)
                
            else: #PS2 mode: (0.0 at rest, fluctuates between 1.0 and -1.0 when pressed)
              self.whammyVol[i] = (round(10*(abs(self.engine.input.joysticks[self.whichJoy[i]].get_axis(self.whichAxis[i]))))/10.0)
    
            if self.whammyVol[i] > 0.0 and self.whammyVol[i] < 0.1:
              self.whammyVol[i] = 0.1

            self.lastWhammyVol[i] = self.whammyVol[i]

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
   

    self.logClassInits = self.engine.config.get("game", "log_class_inits")
    if self.logClassInits == 1:
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
  
def chooseItem(engine, items, prompt, selected = None, pos = None):   #MFH
  """
  Ask the user to one item from a list.
  
  @param engine:    Game engine
  @param items:     List of items
  @param prompt:    Prompt shown to the user
  @param selected:  Item selected by default
  @param pos:       Position tuple (x,y) for placing the menu
  """
  d = ItemChooser(engine, items, prompt = prompt, selected = selected, pos = pos)
  _runDialog(engine, d)
  return d.getSelectedItem()

#MFH - on-demand Neck Chooser
def chooseNeck(engine, prompt = "", selected = None, player = 0):
  """
  Ask the user to one item from a list.
  
  @param engine:    Game engine
  @param items:     List of items
  @param prompt:    Prompt shown to the user
  @param selected:  Item selected by default
  """
  d = NeckChooser(engine, prompt = prompt, selected = selected, player = player)
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
    self.textColor = Theme.loadingColor
    self.allowtext = self.engine.config.get("game", "lphrases")  

    self.logClassInits = self.engine.config.get("game", "log_class_inits")
    if self.logClassInits == 1:
      Log.debug("LoadingSplashScreen class init (Dialogs.py)...")

    #Get theme
    themename = self.engine.data.themeLabel
    self.theme = self.engine.data.theme

  def shown(self):
    self.engine.input.addKeyListener(self, priority = True)

  def keyPressed(self, key, unicode):
    return True
    
  def hidden(self):
    self.engine.input.removeKeyListener(self)

  def run(self, ticks):
    self.time += ticks / 50.0
  
  def render(self, visibility, topMost):
    self.engine.view.setViewport(1,0)
    self.engine.view.setOrthogonalProjection(normalize = True)
    font = self.engine.data.loadingFont   #MFH - new font support

    if not font:
      return

    try:
      v = (1 - visibility) ** 2
      fadeScreen(v)

      w, h = self.engine.view.geometry[2:4]
      self.engine.drawImage(self.engine.data.loadingImage, scale = (.5, -.5), coord = (w / 2, h / 2))

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

      #akedrou - support for Loading Text Color
      c1,c2,c3 = self.textColor
      glColor3f(c1,c2,c3)
      
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

def changeLoadingSplashScreenText(engine, splash, text=_("Loading...")):
  splash.text = text
  engine.run()

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
  #else:
  #  Log.debug("Song name starting with a period filtered from prefix removal logic: " + name)
  return name
