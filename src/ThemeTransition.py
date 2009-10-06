#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire X                                                   #
# Copyright (C) 2009 FoFiX Team                                     #
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

#Note! This is only meant as a stopgap while the new theme architecture is being written.
#Do not add to this unless you are aware of this fact!
#-akedrou

import Config
import Theme
import Song
import Data
from OpenGL.GL import *
from OpenGL.GLU import *
import string
import math
from Language import _
import Dialogs
from Shader import shaders

setlist_type = Theme.songListDisplay
if str(setlist_type) == "None":
  setlist_type = Config.get("coffee", "song_display_mode")
  if setlist_type == 4:
    setlist_type = 1

if setlist_type == 0: #CD mode
  setlistStyle = 0
  headerSkip = 0
  footerSkip = 0
  labelType = 1
  labelDistance = 2
  showMoreLabels = True
  texturedLabels = True
  itemsPerPage = 1
  showLockedSongs = False
  showSortTiers = True
  selectTiers = False
  itemSize = (0,.125)
elif setlist_type == 1: #List mode
  setlistStyle = 1
  headerSkip = 2
  footerSkip = 1
  labelType = 0
  labelDistance = 0
  showMoreLabels = False
  texturedLabels = False
  itemsPerPage = 7
  showLockedSongs = False
  showSortTiers = True
  selectTiers = False
  itemSize = (0,.125)
elif setlist_type == 2: #List/CD mode
  setlistStyle = 1
  headerSkip = 0
  footerSkip = 1
  labelType = 1
  labelDistance = 1
  showMoreLabels = False
  texturedLabels = True
  itemsPerPage = 8
  showLockedSongs = False
  showSortTiers = True
  selectTiers = False
  itemSize = (0,.125)
else: #RB2 mode
  setlistStyle = 0
  headerSkip = 0
  footerSkip = 0
  labelType = 0
  labelDistance = 1
  showMoreLabels = False
  texturedLabels = False
  itemsPerPage = 12
  showLockedSongs = True
  showSortTiers = True
  selectTiers = False
  itemSize = (0,.07)
career_title_color = Theme.hexToColor(Theme.career_title_colorVar)
song_name_text_color = Theme.hexToColor(Theme.song_name_text_colorVar)
song_cd_xpos = Theme.song_cd_Xpos
song_cdscore_xpos = Theme.song_cdscore_Xpos
song_rb2_name_color = Theme.hexToColor(Theme.song_rb2_name_colorVar)
song_name_selected_color = Theme.hexToColor(Theme.song_name_selected_colorVar)
song_rb2_name_selected_color = Theme.hexToColor(Theme.song_rb2_name_selected_colorVar)
song_rb2_diff_color = Theme.hexToColor(Theme.song_rb2_diff_colorVar)
song_rb2_artist_color = Theme.hexToColor(Theme.song_rb2_artist_colorVar)
artist_text_color = Theme.hexToColor(Theme.artist_text_colorVar)
artist_selected_color = Theme.hexToColor(Theme.artist_selected_colorVar)
library_text_color = Theme.hexToColor(Theme.library_text_colorVar)
library_selected_color = Theme.hexToColor(Theme.library_selected_colorVar)
songlist_score_color = Theme.hexToColor(Theme.songlist_score_colorVar)
songlistcd_score_color = Theme.hexToColor(Theme.songlistcd_score_colorVar)
song_list_xpos = Theme.song_list_Xpos
song_listcd_list_xpos = Theme.song_listcd_list_Xpos
song_listcd_cd_xpos = Theme.song_listcd_cd_Xpos
song_listcd_cd_ypos = Theme.song_listcd_cd_Ypos
song_listcd_score_xpos = Theme.song_listcd_score_Xpos
song_listcd_score_ypos = Theme.song_listcd_score_Ypos

if song_cd_xpos is None:
  song_cd_xpos = 0.0
elif song_cd_xpos > 5:
  song_cd_xpos = 5.0
elif song_cd_xpos < 0:
  song_cd_xpos = 0.0
if song_cdscore_xpos is None:
  song_cdscore_xpos = 0.6
if str(song_list_xpos) == "None":
  song_list_xpos = 0.15
song_listscore_xpos = Theme.song_listscore_Xpos
if str(song_listscore_xpos) == "None":
  song_listscore_xpos = 0.8
if song_listcd_list_xpos == None:
  song_listcd_list_xpos = .1
if song_listcd_cd_xpos == None:
  song_listcd_cd_xpos = .75
if song_listcd_cd_ypos == None:
  song_listcd_cd_ypos = .6
if song_listcd_score_xpos == None:
  song_listcd_score_xpos = 0.6
if song_listcd_score_ypos == None:
  song_listcd_score_ypos = 0.5

def renderHeader(self): #self here used to make it easier on me, yo
  pass
def renderUnselectedItem(self, i, n):
  w, h = self.engine.view.geometry[2:4]
  font = self.engine.data.songListFont
  lfont = self.engine.data.songListFont
  sfont = self.engine.data.shadowfont
  if setlist_type == 0:
    return
  elif setlist_type == 1:
    if not self.items:
      return
    item = self.items[i]

    glColor4f(0,0,0,1)
    if isinstance(item, Song.SongInfo) or isinstance(item, Song.RandomSongInfo):
      c1,c2,c3 = song_name_text_color
      glColor3f(c1,c2,c3)
    elif isinstance(item, Song.LibraryInfo):
      c1,c2,c3 = library_text_color
      glColor3f(c1,c2,c3)
    elif isinstance(item, Song.TitleInfo) or isinstance(item, Song.SortTitleInfo):
      c1,c2,c3 = career_title_color
      glColor3f(c1,c2,c3)
        
    text = item.name
    
    if isinstance(item, Song.SongInfo) and item.getLocked(): #TODO: SongDB
      text = _("-- Locked --")
    
    if isinstance(item, Song.SongInfo): #MFH - add indentation when tier sorting
      if self.tiersPresent:
        text = "   " + text
    
    if isinstance(item, Song.TitleInfo) or isinstance(item, Song.SortTitleInfo):
      text = string.upper(text)

    scale = lfont.scaleText(text, maxwidth = 0.440)

    lfont.render(text, (song_list_xpos, .0925*(n+1)-.0375), scale = scale)


    #MFH - Song list score / info display:
    if isinstance(item, Song.SongInfo) and not item.getLocked():
      scale = 0.0009
      text = self.scoreDifficulty.text
      c1,c2,c3 = songlist_score_color
      glColor3f(c1,c2,c3)
      lfont.render(text, (song_listscore_xpos, .0925*(n+1)-.034), scale=scale, align = 2)
      if not item.frets == "":
        suffix = ", ("+item.frets+")"
      else:
        suffix = ""

      if not item.year == "":
        yeartag = ", "+item.year
      else:
        yeartag = ""


      scale = .0014
      c1,c2,c3 = artist_text_color
      glColor3f(c1,c2,c3)

      # evilynux - Force uppercase display for artist name
      text = string.upper(item.artist)+suffix+yeartag
      
      # evilynux - automatically scale artist name and year
      scale = lfont.scaleText(text, maxwidth = 0.440, scale = scale)
      if scale > .0014:
        scale = .0014

      lfont.render(text, (song_list_xpos+.05, .0925*(n+1)+.0125), scale=scale)

      score = _("Nil")
      stars = 0
      name = ""

      try:
        difficulties = item.partDifficulties[self.scorePart.id]
      except KeyError:
        difficulties = []
      for d in difficulties:
        if d.id == self.scoreDifficulty.id:
          scores = item.getHighscores(d, part = self.scorePart)
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
      
      if score == _("Nil") and self.nilShowNextScore:   #MFH
        for d in difficulties:   #MFH - just take the first valid difficulty you can find and display it.
          scores = item.getHighscores(d, part = self.scorePart)
          if scores:
            score, stars, name, scoreExt = scores[0]
            try:
              notesHit, notesTotal, noteStreak, modVersion, handicap, handicapLong, originalScore = scoreExt
            except ValueError:
              notesHit, notesTotal, noteStreak, modVersion, oldScores1, oldScores2 = scoreExt
              handicap = 0
              handicapLong = "None"
              originalScore = score
            break
          else:
            score, stars, name = 0, 0, "---"
        else:
          score, stars, name = _("Nil"), 0, "---"
          
      
      


      starx = song_listscore_xpos+.01
      stary = .0925*(n+1)-0.039
      starscale = 0.03
      stary = 1.0 - (stary / self.engine.data.fontScreenBottom)
      self.engine.drawStarScore(w, h, starx, stary - h/2, stars, starscale, horiz_spacing = 1.0, hqStar = True) #MFH

      scale = 0.0014
      # evilynux - score color
      c1,c2,c3 = songlist_score_color
      glColor3f(c1,c2,c3)
      # evilynux - hit% and note streak only if enabled
      if score is not _("Nil") and score > 0 and notesTotal != 0:
        text = "%.1f%% (%d)" % ((float(notesHit) / notesTotal) * 100.0, noteStreak)
        lfont.render(text, (song_listscore_xpos+.1, .0925*(n+1)-.015), scale=scale, align = 2)

      text = str(score)
      lfont.render(text, (song_listscore_xpos+.1, .0925*(n+1)+.0125), scale=scale*1.28, align = 2)
  
  elif setlist_type == 2: #old list/cd
    y = h*(.87-(.1*n))
    if not self.items:
      return
    item = self.items[i]
    if isinstance(item, Song.SongInfo) or isinstance(item, Song.RandomSongInfo):
      c1,c2,c3 = song_name_text_color
      glColor4f(c1,c2,c3,1)
    if isinstance(item, Song.LibraryInfo):
      c1,c2,c3 = library_text_color
      glColor4f(c1,c2,c3,1)
    if isinstance(item, Song.TitleInfo) or isinstance(item, Song.SortTitleInfo):
      c1,c2,c3 = career_title_color
      glColor4f(c1,c2,c3,1)
    text = item.name
    if isinstance(item, Song.SongInfo) and item.getLocked():
      text = _("-- Locked --")
    if isinstance(item, Song.SongInfo): #MFH - add indentation when tier sorting
      if self.tiersPresent:
        text = "   " + text
    if isinstance(item, Song.TitleInfo) or isinstance(item, Song.SortTitleInfo):
      text = string.upper(text)
    scale = font.scaleText(text, maxwidth = 0.45)
    font.render(text, (song_listcd_list_xpos, .09*(n+1)), scale = scale)
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
      c1,c2,c3 = artist_text_color
      glColor4f(c1,c2,c3,1)

      text = string.upper(item.artist)+suffix+yeartag

      scale = font.scaleText(text, maxwidth = 0.4, scale = scale)
      font.render(text, (song_listcd_list_xpos + .05, .09*(n+1)+.05), scale=scale)
  elif setlist_type == 3: #old rb2
    font = self.engine.data.songListFont
    if not self.items or not self.itemIcons:
      return
    item = self.items[i]
    y = h*(.7825-(.0459*(n+1)))
    
    if self.img_tier:
      imgwidth = self.img_tier.width1()
      imgheight = self.img_tier.height1()
      wfactor = 381.1/imgwidth
      hfactor = 24.000/imgheight
      if isinstance(item, Song.TitleInfo) or isinstance(item, Song.SortTitleInfo) and self.img_tier:
        self.engine.drawImage(self.img_tier, scale = (wfactor,-hfactor), coord = (w/1.587, h-((0.055*h)*(n+1))-(0.219*h)))

    icon = None
    if isinstance(item, Song.SongInfo):
      if item.icon != "":
        try:
          icon = self.itemIcons[item.icon]
          imgwidth = icon.width1()
          wfactor = 23.000/imgwidth
          self.engine.drawImage(icon, scale = (wfactor,-wfactor), coord = (w/2.86, h-((0.055*(n+1))-(0.219*h))))
        except KeyError:
          pass
    elif isinstance(item, Song.LibraryInfo):
      try:
        icon = self.itemIcons["Library"]
        imgwidth = icon.width1()
        wfactor = 23.000/imgwidth
        self.engine.drawImage(icon, scale = (wfactor,-wfactor), coord = (w/2.86, h-((0.055*(n+1))-(0.219*h))))
      except KeyError:
        pass
    elif isinstance(item, Song.RandomSongInfo):
      try:
        icon = self.itemIcons["Random"]
        imgwidth = icon.width1()
        wfactor = 23.000/imgwidth
        self.engine.drawImage(icon, scale = (wfactor,-wfactor), coord = (w/2.86, h-((0.055*(n+1))-(0.219*h))))
      except KeyError:
        pass
    
    if isinstance(item, Song.SongInfo) or isinstance(item, Song.LibraryInfo):
      c1,c2,c3 = song_rb2_name_color
      glColor4f(c1,c2,c3,1)
    elif isinstance(item, Song.TitleInfo) or isinstance(item, Song.SortTitleInfo):
      c1,c2,c3 = career_title_color
      glColor4f(c1,c2,c3,1)
    elif isinstance(item, Song.RandomSongInfo):
      c1,c2,c3 = song_rb2_name_color
      glColor4f(c1,c2,c3,1)
    
    text = item.name
    
    if isinstance(item, Song.SongInfo) and item.getLocked():
      text = _("-- Locked --")
      
    if isinstance(item, Song.SongInfo): #MFH - add indentation when tier sorting
      if self.tiersPresent or icon:
        text = "   " + text
      

    # evilynux - Force uppercase display for Career titles
    maxwidth = .55
      
    if isinstance(item, Song.TitleInfo) or isinstance(item, Song.SortTitleInfo):
      text = string.upper(text)
      
    scale = .0015
    wt, ht = font.getStringSize(text, scale = scale)

    while wt > maxwidth:
      tlength = len(text) - 4
      text = text[:tlength] + "..."
      wt, ht = font.getStringSize(text, scale = scale)
      if wt < .45:
        break
      
      
    font.render(text, (.35, .0413*(n+1)+.15), scale = scale)

    if isinstance(item, Song.SongInfo):
      if not item.getLocked():
        try:
          difficulties = item.partDifficulties[self.scorePart.id]
        except KeyError:
          difficulties = []
        for d in difficulties:
          if d.id == self.scoreDifficulty.id:
            scores = item.getHighscores(d, part = self.scorePart)
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
        
        if score == _("Nil") and self.nilShowNextScore:   #MFH
          for d in difficulties:   #MFH - just take the first valid difficulty you can find and display it.
            scores = item.getHighscores(d, part = self.scorePart)
            if scores:
              score, stars, name, scoreExt = scores[0]
              try:
                notesHit, notesTotal, noteStreak, modVersion, handicap, handicapLong, originalScore = scoreExt
              except ValueError:
                notesHit, notesTotal, noteStreak, modVersion, oldScores1, oldScores2 = scoreExt
                handicap = 0
                handicapLong = "None"
                originalScore = score
              break
            else:
              score, stars, name = 0, 0, "---"
          else:
            score, stars, name = _("Nil"), 0, "---"

        #evilynux - hit% and note streak if enabled
        scale = 0.0009
        if score is not _("Nil") and score > 0 and notesTotal != 0:
          text = "%.1f%% (%d)" % ((float(notesHit) / notesTotal) * 100.0, noteStreak)
          font.render(text, (.92, .0413*(n+1)+.163), scale=scale, align = 2)
              
        text = str(score)
        
        font.render(text, (.92, .0413*(n+1)+.15), scale=scale, align = 2)

def renderSelectedItem(self, n):
  w, h = self.engine.view.geometry[2:4]
  font = self.engine.data.songListFont
  lfont = self.engine.data.songListFont
  sfont = self.engine.data.shadowfont
  item = self.selectedItem
  if not item:
    return
  if isinstance(item, Song.BlankSpaceInfo):
    return
  if setlist_type == 0:
    return
  elif setlist_type == 1:
    y = h*(.88-(.125*n))
    if self.img_item_select:
      wfactor = self.img_item_select.widthf(pixelw = 635.000)
      self.engine.drawImage(self.img_item_select, scale = (wfactor,-wfactor), coord = (w/2.1, y))
    glColor4f(0,0,0,1)
    if isinstance(item, Song.SongInfo) or isinstance(item, Song.RandomSongInfo):
      c1,c2,c3 = song_name_selected_color
      glColor3f(c1,c2,c3)
    elif isinstance(item, Song.LibraryInfo):
      c1,c2,c3 = library_selected_color
      glColor3f(c1,c2,c3)
    elif isinstance(item, Song.TitleInfo) or isinstance(item, Song.SortTitleInfo):
      c1,c2,c3 = career_title_color
      glColor3f(c1,c2,c3)
        
    text = item.name
    
    if isinstance(item, Song.SongInfo) and item.getLocked(): #TODO: SongDB
      text = _("-- Locked --")
    
    if isinstance(item, Song.SongInfo): #MFH - add indentation when tier sorting
      if self.tiersPresent:
        text = "   " + text
    
    if isinstance(item, Song.TitleInfo) or isinstance(item, Song.SortTitleInfo):
      text = string.upper(text)

    scale = sfont.scaleText(text, maxwidth = 0.440)

    sfont.render(text, (song_list_xpos, .0925*(n+1)-.0375), scale = scale)


    #MFH - Song list score / info display:
    if isinstance(item, Song.SongInfo) and not item.getLocked():
      scale = 0.0009
      text = self.scoreDifficulty.text
      c1,c2,c3 = songlist_score_color
      glColor3f(c1,c2,c3)
      lfont.render(text, (song_listscore_xpos, .0925*(n+1)-.034), scale=scale, align = 2)
      if not item.frets == "":
        suffix = ", ("+item.frets+")"
      else:
        suffix = ""

      if not item.year == "":
        yeartag = ", "+item.year
      else:
        yeartag = ""


      scale = .0014
      c1,c2,c3 = artist_selected_color
      glColor3f(c1,c2,c3)

      # evilynux - Force uppercase display for artist name
      text = string.upper(item.artist)+suffix+yeartag
      
      # evilynux - automatically scale artist name and year
      scale = lfont.scaleText(text, maxwidth = 0.440, scale = scale)
      if scale > .0014:
        scale = .0014

      lfont.render(text, (song_list_xpos+.05, .0925*(n+1)+.0125), scale=scale)

      score = _("Nil")
      stars = 0
      name = ""

      try:
        difficulties = item.partDifficulties[self.scorePart.id]
      except KeyError:
        difficulties = []
      for d in difficulties:
        if d.id == self.scoreDifficulty.id:
          scores = item.getHighscores(d, part = self.scorePart)
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
      
      if score == _("Nil") and self.nilShowNextScore:   #MFH
        for d in difficulties:   #MFH - just take the first valid difficulty you can find and display it.
          scores = item.getHighscores(d, part = self.scorePart)
          if scores:
            score, stars, name, scoreExt = scores[0]
            try:
              notesHit, notesTotal, noteStreak, modVersion, handicap, handicapLong, originalScore = scoreExt
            except ValueError:
              notesHit, notesTotal, noteStreak, modVersion, oldScores1, oldScores2 = scoreExt
              handicap = 0
              handicapLong = "None"
              originalScore = score
            break
          else:
            score, stars, name = 0, 0, "---"
        else:
          score, stars, name = _("Nil"), 0, "---"
          
      starx = song_listscore_xpos+.01
      stary = .0925*(n+1)-0.039
      starscale = 0.03
      stary = 1.0 - (stary / self.engine.data.fontScreenBottom)
      self.engine.drawStarScore(w, h, starx, stary - h/2, stars, starscale, horiz_spacing = 1.0, hqStar = True) #MFH

      scale = 0.0014
      # evilynux - score color
      c1,c2,c3 = songlist_score_color
      glColor3f(c1,c2,c3)
      # evilynux - hit% and note streak only if enabled
      if score is not _("Nil") and score > 0 and notesTotal != 0:
        text = "%.1f%% (%d)" % ((float(notesHit) / notesTotal) * 100.0, noteStreak)
        lfont.render(text, (song_listscore_xpos+.1, .0925*(n+1)-.015), scale=scale, align = 2)

      text = str(score)
      lfont.render(text, (song_listscore_xpos+.1, .0925*(n+1)+.0125), scale=scale*1.28, align = 2)
  elif setlist_type == 2:
    y = h*(.87-(.1*n))
    glColor4f(1,1,1,1)
    if self.img_selected:
      imgwidth = self.img_selected.width1()
      self.engine.drawImage(self.img_selected, scale = (1, -1), coord = (song_listcd_list_xpos * w + (imgwidth*.64/2), y*1.2-h*.215))
    text = self.library
    font.render(text, (.05, .01))
    if self.songLoader:
      font.render(_("Loading Preview..."), (.05, .7), scale = 0.001)
    
    if isinstance(item, Song.SongInfo):
      c1,c2,c3 = song_name_selected_color
      glColor4f(c1,c2,c3,1)
      if item.getLocked():
        text = item.getUnlockText()
      elif self.careerMode and not item.completed:
        text = _("Play To Advance")
      elif self.practiceMode:
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
      c1,c2,c3 = library_selected_color
      glColor4f(c1,c2,c3,1)
      if item.songCount == 1:
        text = _("There Is 1 Song In This Setlist.")
      elif item.songCount > 1:
        text = _("There Are %d Songs In This Setlist.") % (item.songCount)
      else:
        text = ""
    elif isinstance(item, Song.TitleInfo) or isinstance(item, Song.SortTitleInfo):
      text = _("Tier")
      c1,c2,c3 = career_title_color
      glColor4f(c1,c2,c3,1)
    elif isinstance(item, Song.RandomSongInfo):
      text = _("Random Song")
      c1,c2,c3 = song_name_selected_color
      glColor4f(c1,c2,c3,1)
    
    font.render(text, (song_listcd_score_xpos, .085), scale = 0.0012)
    
    if isinstance(item, Song.SongInfo) or isinstance(item, Song.RandomSongInfo):
      c1,c2,c3 = song_name_selected_color
      glColor4f(c1,c2,c3,1)
    elif isinstance(item, Song.LibraryInfo):
      c1,c2,c3 = library_selected_color
      glColor4f(c1,c2,c3,1)
    elif isinstance(item, Song.TitleInfo) or isinstance(item, Song.SortTitleInfo):
      c1,c2,c3 = career_title_color
      glColor4f(c1,c2,c3,1)
    text = item.name
    if isinstance(item, Song.SongInfo) and item.getLocked():
      text = _("-- Locked --")
      
    if isinstance(item, Song.SongInfo): #MFH - add indentation when tier sorting
      if self.tiersPresent:
        text = "   " + text

    elif isinstance(item, Song.TitleInfo) or isinstance(item, Song.SortTitleInfo):
      text = string.upper(text)
      
    scale = font.scaleText(text, maxwidth = 0.45)
    font.render(text, (song_listcd_list_xpos, .09*(n+1)), scale = scale)
    
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
      c1,c2,c3 = artist_selected_color
      glColor4f(c1,c2,c3,1)
      text = string.upper(item.artist)+suffix+yeartag

      scale = font.scaleText(text, maxwidth = 0.4, scale = scale)
      font.render(text, (song_listcd_list_xpos + .05, .09*(n+1)+.05), scale=scale)
  
  elif setlist_type == 3:
    y = h*(.7825-(.0459*(n)))
    
    if self.img_tier:
      imgwidth = self.img_tier.width1()
      imgheight = self.img_tier.height1()
      wfactor = 381.1/imgwidth
      hfactor = 24.000/imgheight
      if isinstance(item, Song.TitleInfo) or isinstance(item, Song.SortTitleInfo):
        self.engine.drawImage(self.img_tier, scale = (wfactor,-hfactor), coord = (w/1.587, h-((0.055*h)*(n+1))-(0.219*h)))
    
    if self.img_selected:
      imgwidth = self.img_selected.width1()
      imgheight = self.img_selected.height1()
      wfactor = 381.5/imgwidth
      hfactor = 36.000/imgheight

      self.engine.drawImage(self.img_selected, scale = (wfactor,-hfactor), coord = (w/1.587, y*1.2-h*.213))
    
    
    icon = None
    if isinstance(item, Song.SongInfo):
      if item.icon != "":
        try:
          icon = self.itemIcons[item.icon]
          imgwidth = icon.width1()
          wfactor = 23.000/imgwidth
          self.engine.drawImage(icon, scale = (wfactor,-wfactor), coord = (w/2.86, h-((0.055*(n+1))-(0.219*h))))
        except KeyError:
          pass
      
      c1,c2,c3 = song_rb2_name_selected_color
      glColor3f(c1,c2,c3)
      if item.getLocked():
        text = item.getUnlockText()
      elif self.careerMode and not item.completed:
        text = _("Play To Advance")
      elif self.practiceMode:
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
      try:
        icon = self.itemIcons["Library"]
        imgwidth = icon.width1()
        wfactor = 23.000/imgwidth
        self.engine.drawImage(icon, scale = (wfactor,-wfactor), coord = (w/2.86, h-((0.055*(n+1))-(0.219*h))))
      except KeyError:
        pass
      c1,c2,c3 = library_selected_color
      glColor3f(c1,c2,c3)
      if item.songCount == 1:
        text = _("There Is 1 Song In This Setlist.")
      elif item.songCount > 1:
        text = _("There Are %d Songs In This Setlist.") % (item.songCount)
      else:
        text = ""
    elif isinstance(item, Song.TitleInfo) or isinstance(item, Song.SortTitleInfo):
      text = _("Tier")
      c1,c2,c3 = career_title_color
      glColor3f(c1,c2,c3)
    elif isinstance(item, Song.RandomSongInfo):
      try:
        icon = self.itemIcons["Random"]
        imgwidth = icon.width1()
        wfactor = 23.000/imgwidth
        self.engine.drawImage(icon, scale = (wfactor,-wfactor), coord = (w/2.86, h-((0.055*(n+1))-(0.219*h))))
      except KeyError:
        pass
      text = _("Random Song")
      c1,c2,c3 = career_title_color
      glColor3f(c1,c2,c3)
    
    font.render(text, (0.92, .13), scale = 0.0012, align = 2)
    
    maxwidth = .45
    if isinstance(item, Song.SongInfo) or isinstance(item, Song.LibraryInfo) or isinstance(item, Song.RandomSongInfo):
      c1,c2,c3 = song_rb2_name_selected_color
      glColor4f(c1,c2,c3,1)
    if isinstance(item, Song.TitleInfo) or isinstance(item, Song.SortTitleInfo):
      c1,c2,c3 = career_title_color
      glColor4f(c1,c2,c3,1)
    
    text = item.name
    
    if isinstance(item, Song.SongInfo) and item.getLocked():
      text = _("-- Locked --")
      
    if isinstance(item, Song.SongInfo): #MFH - add indentation when tier sorting
      if self.tiersPresent or icon:
        text = "   " + text
      

    # evilynux - Force uppercase display for Career titles
    if isinstance(item, Song.TitleInfo) or isinstance(item, Song.SortTitleInfo):
      maxwidth = .55
      text = string.upper(text)
      
    scale = .0015
    wt, ht = font.getStringSize(text, scale = scale)

    while wt > maxwidth:
      tlength = len(text) - 4
      text = text[:tlength] + "..."
      wt, ht = font.getStringSize(text, scale = scale)
      if wt < .45:
        break
      
      
    font.render(text, (.35, .0413*(n+1)+.15), scale = scale) #add theme option for song_listCD_xpos

    if isinstance(item, Song.SongInfo):
      if not item.getLocked():
        try:
          difficulties = item.partDifficulties[self.scorePart.id]
        except KeyError:
          difficulties = []
        for d in difficulties:
          if d.id == self.scoreDifficulty.id:
            scores = item.getHighscores(d, part = self.scorePart)
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
        
        if score == _("Nil") and self.nilShowNextScore:   #MFH
          for d in difficulties:   #MFH - just take the first valid difficulty you can find and display it.
            scores = item.getHighscores(d, part = self.scorePart)
            if scores:
              score, stars, name, scoreExt = scores[0]
              try:
                notesHit, notesTotal, noteStreak, modVersion, handicap, handicapLong, originalScore = scoreExt
              except ValueError:
                notesHit, notesTotal, noteStreak, modVersion, oldScores1, oldScores2 = scoreExt
                handicap = 0
                handicapLong = "None"
                originalScore = score
              break
            else:
              score, stars, name = 0, 0, "---"
          else:
            score, stars, name = _("Nil"), 0, "---"

        scale = 0.0009
        if score is not _("Nil") and score > 0 and notesTotal != 0:
          text = "%.1f%% (%d)" % ((float(notesHit) / notesTotal) * 100.0, noteStreak)
          w, h = font.getStringSize(text, scale=scale)
          font.render(text, (.92, .0413*(n+1)+.163), scale=scale, align = 2)
        
        text = str(score)
        
        font.render(text, (.92, .0413*(n+1)+.15), scale=scale, align = 2)

def renderItem(self, color, label):
  if not self.itemMesh:
    return
  if color:
    glColor3f(*color)
  glEnable(GL_COLOR_MATERIAL)
  if setlist_type == 2:
    glRotate(90, 0, 0, 1)
    glRotate(((self.time - self.lastTime) * 2 % 360) - 90, 1, 0, 0)
  self.itemMesh.render("Mesh_001")
  glColor3f(.1, .1, .1)
  self.itemMesh.render("Mesh")
  if label:
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
    if shaders.enable("cd"):
      self.cassette.render("Mesh_001")
      shaders.disable()

def renderLibrary(self, color, label):
  if not self.libraryMesh:
    return
  if color:
    glColor3f(*color)
  
  glEnable(GL_NORMALIZE)
  glEnable(GL_COLOR_MATERIAL)
  if setlist_type == 2:
    glRotate(-180, 0, 1, 0)
    glRotate(-90, 0, 0, 1)
    glRotate(((self.time - self.lastTime) * 4 % 360) - 90, 1, 0, 0)
  self.libraryMesh.render("Mesh_001")
  glColor3f(.1, .1, .1)
  self.libraryMesh.render("Mesh")

  # Draw the label if there is one
  if label:
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
  
def renderTitle(self, color, label):
  if not self.tierMesh:
    return

  if color:
    glColor3f(*color)

  glEnable(GL_NORMALIZE)
  glEnable(GL_COLOR_MATERIAL)
  self.tierMesh.render("Mesh_001")
  glColor3f(.1, .1, .1)
  self.tierMesh.render("Mesh")

  # Draw the label if there is one
  if label:
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
  
def renderRandom(self, color, label):
  if not self.itemMesh:
    return

  if color:
    glColor3f(*color)

  glEnable(GL_NORMALIZE)
  glEnable(GL_COLOR_MATERIAL)
  self.itemMesh.render("Mesh_001")
  glColor3f(.1, .1, .1)
  self.itemMesh.render("Mesh")

  # Draw the label if there is one
  if label:
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

def renderAlbumArt(self):
  if not self.itemLabels:
    return
  if setlist_type == 0:
    w, h = self.engine.view.geometry[2:4]
    try:
      glMatrixMode(GL_PROJECTION)
      glPushMatrix()
      glLoadIdentity()
      gluPerspective(60, self.engine.view.aspectRatio, 0.1, 1000)
      
      glMatrixMode(GL_MODELVIEW)
      glLoadIdentity()
      
      glEnable(GL_DEPTH_TEST)
      glDisable(GL_CULL_FACE)
      glDepthMask(1)
      
      offset = 0
      if self.time < 40:
        offset = 10*((40 - self.time)/40.0)**4
      self.camera.origin = (-10 + offset, -self.cameraOffset, 4   - song_cd_xpos + offset)
      self.camera.target = (  0 + offset, -self.cameraOffset, 2.5 - song_cd_xpos + offset)
      self.camera.apply()
      
      y = 0.0
      for i, item in enumerate(self.items):
        c = math.sin(self.itemRenderAngles[i] * math.pi / 180)
        
        if isinstance(item, Song.SongInfo):
          h = c * 4.0 + (1 - c) * .8
        elif isinstance(item, Song.LibraryInfo):
          h = c * 4.0 + (1 - c) * 1.2
        elif isinstance(item, Song.TitleInfo) or isinstance(item, Song.SortTitleInfo):
          h = c * 4.0 + (1 - c) * 2.4
        elif isinstance(item, Song.RandomSongInfo):
          h = c * 4.0 + (1 - c) * .8
        else:
          continue
        
        d = (y + h * .5 + self.camera.origin[1]) / (4 * (self.camera.target[2] - self.camera.origin[2]))
        if i == self.selectedIndex:
          self.selectedOffset = y + h / 2
          Theme.setSelectedColor()
        else:
          Theme.setBaseColor()
        
        glTranslatef(0, -h / 2, 0)
        glPushMatrix()
        if abs(d) < 1.2:
          label = self.itemLabels[i]
          if label == "Random":
            label = self.img_random_label
          if label == False:
            label = self.img_empty_label
          if isinstance(item, Song.SongInfo):
            glRotate(self.itemRenderAngles[i], 0, 0, 1)
            renderItem(self, item.cassetteColor, label)
          elif isinstance(item, Song.LibraryInfo):
            #myfingershurt: cd cases are backwards
            glRotate(-self.itemRenderAngles[i], 0, 1, 0)    #spin 90 degrees around y axis
            glRotate(-self.itemRenderAngles[i], 0, 1, 0)    #spin 90 degrees around y axis again, now case is corrected
            glRotate(-self.itemRenderAngles[i], 0, 0, 1)    #bring cd case up for viewing
            if i == self.selectedIndex:
              glRotate(((self.time - self.lastTime) * 4 % 360) - 90, 1, 0, 0)
            renderLibrary(self, item.color, label)
          elif isinstance(item, Song.TitleInfo):
            #myfingershurt: cd cases are backwards
            glRotate(-self.itemRenderAngles[i], 0, 0.5, 0)    #spin 90 degrees around y axis
            glRotate(-self.itemRenderAngles[i], 0, 0.5, 0)    #spin 90 degrees around y axis again, now case is corrected
            glRotate(-self.itemRenderAngles[i], 0, 0, 0.5)    #bring cd case up for viewing
            if i == self.selectedIndex:
              glRotate(((self.time - self.lastTime) * 4 % 360) - 90, 1, 0, 0)
            renderTitle(self, item.color, label)
          elif isinstance(item, Song.RandomSongInfo):
            #myfingershurt: cd cases are backwards
            glRotate(self.itemRenderAngles[i], 0, 0, 1)
            renderRandom(self, item.color, label)
        glPopMatrix()
        
        glTranslatef(0, -h/2, 0)
        y+= h
      glDisable(GL_DEPTH_TEST)
      glDisable(GL_CULL_FACE)
      glDepthMask(0)
    finally:
      glMatrixMode(GL_PROJECTION)
      glPopMatrix()
      glMatrixMode(GL_MODELVIEW)
      
  elif setlist_type == 1:
    return
  elif setlist_type == 2:
    w, h = self.engine.view.geometry[2:4]
    try:
      glMatrixMode(GL_PROJECTION)
      glPushMatrix()
      
      glLoadIdentity()
      gluPerspective(60, self.engine.view.aspectRatio, 0.1, 1000)
      glMatrixMode(GL_MODELVIEW)
      glLoadIdentity()
      
      glEnable(GL_DEPTH_TEST)
      glDisable(GL_CULL_FACE)
      glDepthMask(1)
      
      offset = 0
      if self.time < 40:
        offset = 10*((40 - self.time)/40.0)**4
      self.camera.origin = (-9,(5.196/self.engine.view.aspectRatio) - (5.196*2/self.engine.view.aspectRatio)*song_listcd_cd_ypos,(5.196*self.engine.view.aspectRatio)-(5.196*2*self.engine.view.aspectRatio)*song_listcd_cd_xpos)
      self.camera.target = ( 0,(5.196/self.engine.view.aspectRatio) - (5.196*2/self.engine.view.aspectRatio)*song_listcd_cd_ypos,(5.196*self.engine.view.aspectRatio)-(5.196*2*self.engine.view.aspectRatio)*song_listcd_cd_xpos)
      self.camera.apply()
          
      y = 0.0

      

      glPushMatrix()
      item = self.selectedItem
      i = self.selectedIndex
      label = self.itemLabels[i]
      if label == "Random":
        label = self.img_random_label
      if not label:
        label = self.img_empty_label
      if isinstance(item, Song.SongInfo):
        if self.labelType:
          renderItem(self, item.cassetteColor, label)
        else:
          renderLibrary(self, item.cassetteColor, label)
      elif isinstance(item, Song.LibraryInfo):
        renderLibrary(self, item.color, label)
      elif isinstance(item, Song.RandomSongInfo):
        if self.labelType:
          renderItem(self, None, label)
        else:
          renderLibrary(self, None, label)
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
    
    #resets the rendering
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    viewport = glGetIntegerv(GL_VIEWPORT)
    w = viewport[2] - viewport[0]
    h = viewport[3] - viewport[1]
    h *= (float(w) / float(h)) / (4.0 / 3.0)
    glOrtho(0, 1, h/w, 0, -100, 100)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_COLOR_MATERIAL)
    Theme.setBaseColor(1)
  elif setlist_type == 3:
    w, h = self.engine.view.geometry[2:4]
    item  = self.items[self.selectedIndex]
    i = self.selectedIndex
    img = None
    lockImg = None
    if self.itemLabels[i] == "Random":
      if self.img_random_label:
        img = self.img_random_label
        imgwidth = img.width1()
        wfactor = 155.000/imgwidth
      elif self.img_empty_label:
        img = self.img_empty_label
        imgwidth = img.width1()
        wfactor = 155.000/imgwidth
    elif not self.itemLabels[i]:
      if self.img_empty_label != None:
        imgwidth = self.img_empty_label.width1()
        wfactor = 155.000/imgwidth
        img = self.img_empty_label
    elif self.itemLabels[i]:
      img = self.itemLabels[i]
      imgwidth = img.width1()
      wfactor = 155.000/imgwidth
    if isinstance(item, Song.SongInfo) and item.getLocked():
      if self.img_locked_label:
        imgwidth = self.img_locked_label.width1()
        wfactor2 = 155.000/imgwidth
        lockImg = self.img_locked_label
      else:
        imgwidth = self.img_empty_label.width1()
        wfactor = 155.000/imgwidth
        img = self.img_empty_label
    if img:
      self.engine.drawImage(img, scale = (wfactor,-wfactor), coord = (.21*w,.59*h))
    if lockImg:
      self.engine.drawImage(lockImg, scale = (wfactor2,-wfactor2), coord = (.21*w,.59*h))

def renderForeground(self):
  font = self.engine.data.songListFont
  w, h = self.engine.view.geometry[2:4]
  if setlist_type == 2:
    text = self.scorePart.text
    scale = 0.00250
    glColor3f(1, 1, 1)
    font.render(text, (0.95, 0.000), scale=scale, align = 2)
  elif setlist_type == 3:
    font = self.engine.data.songListFont

    c1,c2,c3 = song_rb2_diff_color
    glColor3f(c1,c2,c3)
    
    font.render(_("DIFFICULTY"), (.095, .5325), scale = 0.0018)
    scale = 0.0014
    text = _("BAND")
    font.render(text, (.17, .5585), scale = scale, align = 2)
    text = _("GUITAR")
    font.render(text, (.17, .5835), scale = scale, align = 2)
    text = _("DRUM")
    font.render(text, (.17, .6085), scale = scale, align = 2)
    text = _("BASS")
    font.render(text, (.17, .6335), scale = scale, align = 2)
    text = _("VOCALS")
    font.render(text, (.17, .6585), scale = scale, align = 2)

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
      font.render(text, (.05, .7), scale = 0.001)
    elif self.songLoader:
      font.render(_("Loading Preview..."), (.05, .7), scale = 0.001)
    return
  if self.img_list_button_guide:
    self.engine.drawImage(self.img_list_button_guide, scale = (.5, -.5), coord = (w*.4,h*.4))
  if self.songLoader:
    font.render(_("Loading Preview..."), (.5, .7), align = 1)
  if self.img_list_fg:
    self.engine.drawImage(self.img_list_fg, scale = (1.0, -1.0), coord = (w/2,h/2), stretched = 3)

def renderSelectedInfo(self):
  if setlist_type == 0: #note... clean this up. this was a rush job.
    if not self.selectedItem:
      return
    font = self.engine.data.font
    screenw, screenh = self.engine.view.geometry[2:4]
    v = 0
    try:
      lfont = self.engine.data.lfont
    except:
      lfont = font
    
    # here we reset the rendering... without pushing the matrices. (they be thar)
    # (otherwise copying engine.view.setOrthogonalProjection)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    viewport = glGetIntegerv(GL_VIEWPORT)
    w = viewport[2] - viewport[0]
    h = viewport[3] - viewport[1]
    h *= (float(w) / float(h)) / (4.0 / 3.0)
    glOrtho(0, 1, h/w, 0, -100, 100)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_COLOR_MATERIAL)
    Theme.setBaseColor(1)

    if self.songLoader:
      font.render(_("Loading Preview..."), (.05, .7), scale = 0.001)

    #x = .6
    x = song_cdscore_xpos
    y = .15

    Theme.setSelectedColor(1)

    c1,c2,c3 = song_name_selected_color
    glColor3f(c1,c2,c3)
    
    item  = self.selectedItem

    angle = self.itemRenderAngles[self.selectedIndex]
    f = ((90.0 - angle) / 90.0) ** 2

    cText = item.name
    if (isinstance(item, Song.SongInfo) and item.getLocked()):
      cText = _("-- Locked --")

    fh = lfont.getHeight()*0.0016
    lfont.render(cText, (x, y), scale = 0.0016)

    if isinstance(item, Song.SongInfo):
      Theme.setBaseColor(1)

      c1,c2,c3 = artist_selected_color
      glColor3f(c1,c2,c3)
      
      if not item.year == "":
        yeartag = ", "+item.year
      else:
        yeartag = ""
      
      cText = item.artist + yeartag
      if (item.getLocked()):
        cText = "" # avoid giving away artist of locked song
      
      # evilynux - Use font w/o outline
      lfont.render(cText, (x, y+fh), scale = 0.0016)

      if item.count:
        Theme.setSelectedColor(1)

        c1,c2,c3 = song_name_selected_color
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
        font.render(text, (x, y+2*fh), scale = 0.001)
      else:
        text = _("Never Played")
        if item.getLocked():
          text = item.getUnlockText()
        elif self.careerMode and not item.completed:
          text = _("Play To Advance.")
        lfont.render(text, (x, y+3*fh), scale = 0.001)

      Theme.setSelectedColor(1 - v)

      c1,c2,c3 = songlistcd_score_color
      glColor3f(c1,c2,c3)

      scale = 0.0011
      
      #x = .6
      x = song_cdscore_xpos
      y = .42
      try:
        difficulties = item.partDifficulties[self.scorePart.id]
      except KeyError:
        difficulties = []
      if len(difficulties) > 3:
        y = .42
      elif len(difficulties) == 0:
        score, stars, name = "---", 0, "---"
      
      for d in difficulties:
        scores = item.getHighscores(d, part = self.scorePart)
        
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
        Theme.setBaseColor(1)
        font.render(Song.difficulties[d.id].text, (x, y), scale = scale)

        starscale = 0.02
        stary = 1.0 - y/self.engine.data.fontScreenBottom
        self.engine.drawStarScore(screenw, screenh, x+.01, stary-2*fh, stars, starscale, hqStar = True) #volshebnyi

        Theme.setSelectedColor(1)
        # evilynux - Also use hit%/noteStreak SongList option
        if scores:
          if notesTotal != 0:
            score = "%s %.1f%%" % (score, (float(notesHit) / notesTotal) * 100.0)
          if noteStreak != 0:
            score = "%s (%d)" % (score, noteStreak)
        font.render(unicode(score), (x + .15, y),     scale = scale)
        font.render(name,       (x + .15, y + fh),     scale = scale)
        y += 2 * fh
    elif isinstance(item, Song.LibraryInfo):
      Theme.setBaseColor(1)
      c1,c2,c3 = library_selected_color
      
      glColor3f(c1,c2,c3)

      if item.songCount == 1:
        songCount = _("One Song In This Setlist")
      else:
        songCount = _("%d Songs In This Setlist") % item.songCount
      font.render(songCount, (x, y + 3*fh), scale = 0.0016)
      
    elif isinstance(item, Song.RandomSongInfo):
      Theme.setBaseColor(1 - v)

      c1,c2,c3 = song_name_selected_color
      glColor3f(c1,c2,c3)

      font.render(_("(Random Song)"), (x, y + 3*fh), scale = 0.0016)

    #MFH CD list
    text = self.scorePart.text
    scale = 0.00250
    #glColor3f(1, 1, 1)
    c1,c2,c3 = song_name_selected_color
    glColor3f(c1,c2,c3)
    w, h = font.getStringSize(text, scale=scale)
    font.render(text, (0.95-w, 0.000), scale=scale)
    # finally:
      # pass
  elif setlist_type == 1:
    return
  elif setlist_type == 2:
    if not self.selectedItem:
      return
    item = self.selectedItem
    font = self.engine.data.font
    w, h = self.engine.view.geometry[2:4]
    try:
      lfont = self.engine.data.lfont
    except:
      lfont = font
    fh = lfont.getHeight()*0.0016
    if isinstance(item, Song.SongInfo):
      angle = self.itemRenderAngles[self.selectedIndex]
      f = ((90.0 - angle) / 90.0) ** 2

      Theme.setSelectedColor(1)
      
      c1,c2,c3 = songlistcd_score_color
      glColor4f(c1,c2,c3,1)

      scale = 0.0013
      x = song_listcd_score_xpos
      y = song_listcd_score_ypos + f / 2.0
      try:
        difficulties = item.partDifficulties[self.scorePart.id]
      except KeyError:
        difficulties = []
        score, stars, name = "---", 0, "---"
      if len(difficulties) > 3:
        y = song_listcd_score_ypos + f / 2.0
      
      #new
      for d in difficulties:
        scores =  item.getHighscores(d, part = self.scorePart)
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
        
        font.render(Song.difficulties[d.id].text, (x, y), scale = scale)
        
        starscale = 0.02
        starx = x + starscale/2
        stary = 1.0 - (y / self.engine.data.fontScreenBottom) - fh - starscale
        self.engine.drawStarScore(w, h, starx, stary, stars, starscale) #MFH
        c1,c2,c3 = songlistcd_score_color
        glColor3f(c1,c2,c3)
        if scores:
          if notesTotal != 0:
            score = "%s %.1f%%" % (score, (float(notesHit) / notesTotal) * 100.0)
          if noteStreak != 0:
            score = "%s (%d)" % (score, noteStreak)
        font.render(unicode(score), (x + .15, y),     scale = scale)
        font.render(name,       (x + .15, y + fh),     scale = scale)
        y += 2 * fh + f / 4.0
  elif setlist_type == 3:
    w, h = self.engine.view.geometry[2:4]
    font = self.engine.data.songListFont
    item = self.selectedItem
    if isinstance(item, Song.SongInfo):
      text = item.artist
      if (item.getLocked()):
        text = "" # avoid giving away artist of locked song

      scale = 0.0015
      wt, ht = font.getStringSize(text, scale=scale)
      
      while wt > .21:
        tlength = len(text) - 4
        text = text[:tlength] + "..."
        wt, ht = font.getStringSize(text, scale = scale)
        if wt < .22:
          break
        
      c1,c2,c3 = song_rb2_artist_color
      glColor3f(c1,c2,c3)
      
      text = string.upper(text)
      font.render(text, (.095, .44), scale = scale)
      
      if self.img_diff3 != None:
        imgwidth = self.img_diff3.width1()
        imgheight = self.img_diff3.height1()
        wfactor1 = 13.0/imgwidth
      
      albumtag = item.album
      albumtag = string.upper(albumtag)
      wt, ht = font.getStringSize(albumtag, scale=scale)
      
      while wt > .21:
        tlength = len(albumtag) - 4
        albumtag = albumtag[:tlength] + "..."
        wt, ht = font.getStringSize(albumtag, scale = scale)
        if wt < .22:
          break                    

      font.render(albumtag, (.095, .47), scale = 0.0015)
      
      genretag = item.genre
      font.render(genretag, (.095, .49), scale = 0.0015)                                

      yeartag = item.year           
      font.render(yeartag, (.095, .51), scale = 0.0015)

   
      for i in range(5):
        glColor3f(1, 1, 1) 
        if i == 0:
          diff = item.diffSong
        elif i == 1:
          diff = item.diffGuitar
        elif i == 2:
          diff = item.diffDrums
        elif i == 3:
          diff = item.diffBass
        elif i == 4:
          diff = item.diffVocals
        if self.img_diff1 == None:
          if diff == -1:
            font.render("N/A", (.18, .5585 + i*.025), scale = 0.0014)
          elif diff == 6:
            glColor3f(1, 1, 0)  
            font.render(str(Data.STAR2 * (diff -1)), (.18, 0.5685 + i*.025), scale = 0.003)
          else:
            font.render(str(Data.STAR2 * diff + Data.STAR1 * (5 - diff)), (.18, 0.5685 + i*.025), scale = 0.003)
        else:
          if diff == -1:
            font.render("N/A", (.18, .5585 + i*.025), scale = 0.0014)
          elif diff == 6:
            for k in range(0,5):
              self.engine.drawImage(self.img_diff3, scale = (wfactor1,-wfactor1), coord = ((.19+.03*k)*w, (0.2354-.0333*i)*h))
          else:
            for k in range(0,diff):
              self.engine.drawImage(self.img_diff2, scale = (wfactor1,-wfactor1), coord = ((.19+.03*k)*w, (0.2354-.0333*i)*h))
            for k in range(0, 5-diff):
              self.engine.drawImage(self.img_diff1, scale = (wfactor1,-wfactor1), coord = ((.31-.03*k)*w, (0.2354-.0333*i)*h))

def renderMoreInfo(self):
  if not self.items:
    return
  if not self.selectedItem:
    return
  item = self.selectedItem
  i = self.selectedIndex
  y = 0
  w, h = self.engine.view.geometry[2:4]
  font = self.engine.data.songListFont
  Dialogs.fadeScreen(0.25)
  if self.moreInfoTime < 500:
    y = 1.0-(float(self.moreInfoTime)/500.0)
  yI = y*h
  if self.img_panel:
    self.engine.drawImage(self.img_panel, scale = (1.0, -1.0), coord = (w*.5,h*.5+yI), stretched = 3)
  if self.img_tabs:
    r0 = (0, (1.0/3.0), 0, .5)
    r1 = ((1.0/3.0),(2.0/3.0), 0, .5)
    r2 = ((2.0/3.0),1.0,0,.5)
    if self.infoPage == 0:
      r0 = (0, (1.0/3.0), .5, 1.0)
      self.engine.drawImage(self.img_tab1, scale = (.5, -.5), coord = (w*.5,h*.5+yI))
      text = item.name
      if item.artist != "":
        text += " by %s" % item.artist
      if item.year != "":
        text += " (%s)" % item.year
      scale = font.scaleText(text, .45, .0015)
      font.render(text, (.52, .25-y), scale = scale, align = 1)
      if self.itemLabels[i]:
        imgwidth = self.itemLabels[i].width1()
        wfactor = 95.000/imgwidth
        self.engine.drawImage(self.itemLabels[i], (wfactor, -wfactor), (w*.375,h*.5+yI))
      elif self.img_empty_label:
        imgwidth = self.img_empty_label.width1()
        wfactor = 95.000/imgwidth
        self.engine.drawImage(self.img_empty_label, (wfactor, -wfactor), (w*.375,h*.5+yI))
      text = item.album
      if text == "":
        text = _("No Album")
      scale = font.scaleText(text, .2, .0015)
      font.render(text, (.56, .305-y), scale = scale)
      text = item.genre
      if text == "":
        text = _("No Genre")
      scale = font.scaleText(text, .2, .0015)
      font.render(text, (.56, .35-y), scale = scale)
    elif self.infoPage == 1:
      r1 = ((1.0/3.0),(2.0/3.0), .5, 1.0)
      self.engine.drawImage(self.img_tab2, scale = (.5, -.5), coord = (w*.5,h*.5+yI))
    elif self.infoPage == 2:
      r2 = ((2.0/3.0),1.0, .5, 1.0)
      self.engine.drawImage(self.img_tab3, scale = (.5, -.5), coord = (w*.5,h*.5+yI))
    self.engine.drawImage(self.img_tabs, scale = (.5*(1.0/3.0), -.25), coord = (w*.36,h*.72+yI), rect = r0)
    self.engine.drawImage(self.img_tabs, scale = (.5*(1.0/3.0), -.25), coord = (w*.51,h*.72+yI), rect = r1)
    self.engine.drawImage(self.img_tabs, scale = (.5*(1.0/3.0), -.25), coord = (w*.66,h*.72+yI), rect = r2)
