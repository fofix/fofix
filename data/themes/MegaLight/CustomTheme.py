#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire X                                                   #
# Copyright (C) 2006 Sami Kyöstilä                                  #
#               2008 myfingershurt                                  #
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

import math

from OpenGL.GL import *
from OpenGL.GLU import *
import six

from fofix.core.Theme import *
from fofix.game import song


class CustomTheme(Theme):
    def __init__(self, path, name):
        Theme.__init__(self, path, name)

        self.menuRB = True
        self.menuX = .25
        self.menuY = .70

        self.fail_text_yPos = .4

        self.displayAllGreyStars = False
        self.sub_menu_xVar = .21
        self.sub_menu_yVar = .15
        self.menuTipTextDisplay = True
        self.songSelectSubmenuX = 0.1
        self.songSelectSubmenuY = 0.075
        self.songSelectSubmenuOffsetLines = 4
        self.songSelectSubmenuOffsetSpaces = 3
        self.song_name_text_colorVar = (1,1,1)
        self.songListDisplay = 0
        self.starFillupCenterX = 139
        self.starFillupCenterY = 151
        self.starFillupInRadius = 121
        self.starFillupOutRadius = 138
        self.starFillupColor = (1,.95,.37)
        self.holdFlameYPos = .1
        self.hitFlameYPos = .5
        self.loadingPhrase = ["If you see a series of glowing white notes, hit it perfectly to gain Energy.","The louder the better!",\
                          "You can buy a real guitar for pretty cheap - maybe it's time to invest.",\
                          "Play flawlessly to get a score multiplier going.  The longer you hold a streak, the higher your multiplier will get.",\
                          "Overdrive can score you tons of points, slay the crowd, and even save your life.",\
                          "If you're going to smash a guitar on stage, make sure you have a backup first.",\
                          "Jack The Ripper is dead, but I'll bet your fingers think otherwise.",\
                          "If your drummer thinks he has an idea, give him a Kit Kat and let him re-think that.",\
                          "Dropping your pants on-stage doesn't deploy star power.","If you're out of songs and you still have time left in your set... wrecking your gear is as good a plan as any.",\
                          "Everything you need to know to be a rocker you learned in kindergarten: -A, B, C, D, E, F, G, 1, 2, 3, 4 -- be creative.",\
                          "Try not to suck this time.","Sleeping with a groupie just means you did a good job.","Mind your effects switch... The Wah-Wah doesn't belong in EVERY song!","Rock On!"]
        self.setlist = CustomSetlist(self)

class CustomSetlist(Setlist):
    def __init__(self, theme):
        self.theme = theme
        self.setlist_type = 0
        self.setlistStyle = 0
        self.headerSkip = 0
        self.footerSkip = 0
        self.labelType = 1
        self.labelDistance = 2
        self.showMoreLabels = True
        self.texturedLabels = True
        self.itemsPerPage = 1
        self.showLockedSongs = False
        self.showSortTiers = True
        self.selectTiers = False
        self.itemSize = (0,.125)

        self.career_title_color = self.theme.career_title_colorVar
        self.song_name_text_color = self.theme.song_name_text_colorVar
        self.song_name_selected_color = self.theme.song_name_selected_colorVar
        self.song_rb2_diff_color = self.theme.song_rb2_diff_colorVar
        self.artist_text_color = self.theme.artist_text_colorVar
        self.artist_selected_color = self.theme.artist_selected_colorVar
        self.library_text_color = self.theme.library_text_colorVar
        self.library_selected_color = self.theme.library_selected_colorVar
        self.songlist_score_color = self.theme.songlist_score_colorVar
        self.songlistcd_score_color = self.theme.songlistcd_score_colorVar

        self.song_cd_xpos = theme.song_cd_Xpos
        self.song_cdscore_xpos = theme.song_cdscore_Xpos
        self.song_list_xpos = theme.song_list_Xpos
        self.song_listscore_xpos = theme.song_listscore_Xpos
        self.song_listcd_list_xpos = theme.song_listcd_list_Xpos
        self.song_listcd_cd_xpos = theme.song_listcd_cd_Xpos
        self.song_listcd_cd_ypos = theme.song_listcd_cd_Ypos
        self.song_listcd_score_xpos = theme.song_listcd_score_Xpos
        self.song_listcd_score_ypos = theme.song_listcd_score_Ypos

    def renderUnselectedItem(self, scene, i, n):
        return

    def renderSelectedItem(self, scene, n):
        return

    def renderAlbumArt(self, scene):
        if not scene.itemLabels:
            return
        w, h = scene.engine.view.geometry[2:4]
        try:
            glMatrixMode(GL_PROJECTION)
            glPushMatrix()
            glLoadIdentity()
            gluPerspective(60, scene.engine.view.aspectRatio, 0.1, 1000)

            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()

            glEnable(GL_DEPTH_TEST)
            glDisable(GL_CULL_FACE)
            glDepthMask(1)

            offset = 0
            if scene.time < 40:
                offset = 10*((40 - scene.time)/40.0)**4
            scene.camera.origin = (-10 + offset, -scene.cameraOffset, 4   - self.song_cd_xpos + offset)
            scene.camera.target = (  0 + offset, -scene.cameraOffset, 2.5 - self.song_cd_xpos + offset)
            scene.camera.apply()

            y = 0.0
            for i, item in enumerate(scene.items):
                c = math.sin(scene.itemRenderAngles[i] * math.pi / 180)

                if isinstance(item, song.SongInfo):
                    h = c * 4.0 + (1 - c) * .8
                elif isinstance(item, song.LibraryInfo):
                    h = c * 4.0 + (1 - c) * 1.2
                elif isinstance(item, song.TitleInfo) or isinstance(item, song.SortTitleInfo):
                    h = c * 4.0 + (1 - c) * 2.4
                elif isinstance(item, song.RandomSongInfo):
                    h = c * 4.0 + (1 - c) * .8
                else:
                    continue

                d = (y + h * .5 + scene.camera.origin[1]) / (4 * (scene.camera.target[2] - scene.camera.origin[2]))
                if i == scene.selectedIndex:
                    scene.selectedOffset = y + h / 2
                    self.theme.setSelectedColor()
                else:
                    self.theme.setBaseColor()

                glTranslatef(0, -h / 2, 0)
                glPushMatrix()
                if abs(d) < 1.2:
                    label = scene.itemLabels[i]
                    if label == "Random":
                        label = scene.img_random_label
                    if not label:
                        label = scene.img_empty_label
                    if isinstance(item, song.SongInfo):
                        glRotate(scene.itemRenderAngles[i], 0, 0, 1)
                        self.renderItem(scene, item.cassetteColor, label)
                    elif isinstance(item, song.LibraryInfo):
                        #myfingershurt: cd cases are backwards
                        glRotate(-scene.itemRenderAngles[i], 0, 1, 0)    #spin 90 degrees around y axis
                        glRotate(-scene.itemRenderAngles[i], 0, 1, 0)    #spin 90 degrees around y axis again, now case is corrected
                        glRotate(-scene.itemRenderAngles[i], 0, 0, 1)    #bring cd case up for viewing
                        if i == scene.selectedIndex:
                            glRotate(((scene.time - scene.lastTime) * 4 % 360) - 90, 1, 0, 0)
                        self.renderLibrary(scene, item.color, label)
                    elif isinstance(item, song.TitleInfo):
                        #myfingershurt: cd cases are backwards
                        glRotate(-scene.itemRenderAngles[i], 0, 0.5, 0)    #spin 90 degrees around y axis
                        glRotate(-scene.itemRenderAngles[i], 0, 0.5, 0)    #spin 90 degrees around y axis again, now case is corrected
                        glRotate(-scene.itemRenderAngles[i], 0, 0, 0.5)    #bring cd case up for viewing
                        if i == scene.selectedIndex:
                            glRotate(((scene.time - scene.lastTime) * 4 % 360) - 90, 1, 0, 0)
                        self.renderTitle(scene, item.color, label)
                    elif isinstance(item, song.RandomSongInfo):
                        #myfingershurt: cd cases are backwards
                        glRotate(scene.itemRenderAngles[i], 0, 0, 1)
                        self.renderRandom(scene, item.color, label)
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

    def renderSelectedInfo(self, scene):
        if not scene.selectedItem:
            return
        font = scene.engine.data.font
        screenw, screenh = scene.engine.view.geometry[2:4]
        v = 0
        try:
            lfont = scene.engine.data.lfont
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
        self.theme.setBaseColor(1)

        if scene.songLoader:
            font.render(_("Loading Preview..."), (.05, .7), scale = 0.001)

        #x = .6
        x = self.song_cdscore_xpos
        y = .15

        self.theme.setSelectedColor(1)

        c1,c2,c3 = self.song_name_selected_color
        glColor3f(c1,c2,c3)

        item  = scene.selectedItem

        angle = scene.itemRenderAngles[scene.selectedIndex]
        f = ((90.0 - angle) / 90.0) ** 2

        cText = item.name
        if (isinstance(item, song.SongInfo) and item.getLocked()):
            cText = _("-- Locked --")

        fh = lfont.getHeight()*0.0016
        lfont.render(cText, (x, y), scale = 0.0016)

        if isinstance(item, song.SongInfo):
            self.theme.setBaseColor(1)

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
            lfont.render(cText, (x, y+fh), scale = 0.0016)

            if item.count:
                self.theme.setSelectedColor(1)

                c1,c2,c3 = self.song_name_selected_color
                glColor3f(c1,c2,c3)

                count = int(item.count)
                if count == 1:
                    text = _("Played %d time") % count
                else:
                    text = _("Played %d times") % count

                if item.getLocked():
                    text = item.getUnlockText()
                elif scene.careerMode and not item.completed:
                    text = _("Play To Advance.")
                font.render(text, (x, y+2*fh), scale = 0.001)
            else:
                text = _("Never Played")
                if item.getLocked():
                    text = item.getUnlockText()
                elif scene.careerMode and not item.completed:
                    text = _("Play To Advance.")
                lfont.render(text, (x, y+3*fh), scale = 0.001)

            self.theme.setSelectedColor(1 - v)

            c1,c2,c3 = self.songlistcd_score_color
            glColor3f(c1,c2,c3)

            scale = 0.0011

            #x = .6
            x = self.song_cdscore_xpos
            y = .42
            try:
                difficulties = item.partDifficulties[scene.scorePart.id]
            except KeyError:
                difficulties = []
            if len(difficulties) > 3:
                y = .42
            elif len(difficulties) == 0:
                score, stars, name = "---", 0, "---"

            for d in difficulties:
                scores = item.getHighscores(d, part = scene.scorePart)

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
                self.theme.setBaseColor(1)
                font.render(song.difficulties[d.id].text, (x, y), scale = scale)

                starscale = 0.02
                stary = 1.0 - y/scene.engine.data.fontScreenBottom
                scene.engine.drawStarScore(screenw, screenh, x+.01, stary-2*fh, stars, starscale, hqStar = True) #volshebnyi

                self.theme.setSelectedColor(1)
                # evilynux - Also use hit%/noteStreak SongList option
                if scores:
                    if notesTotal != 0:
                        score = "%s %.1f%%" % (score, (float(notesHit) / notesTotal) * 100.0)
                    if noteStreak != 0:
                        score = "%s (%d)" % (score, noteStreak)
                font.render(six.u(score), (x + .15, y),     scale = scale)
                font.render(name,       (x + .15, y + fh),     scale = scale)
                y += 2 * fh
        elif isinstance(item, song.LibraryInfo):
            self.theme.setBaseColor(1)
            c1,c2,c3 = self.library_selected_color

            glColor3f(c1,c2,c3)

            if item.songCount == 1:
                songCount = _("One Song In This Setlist")
            else:
                songCount = _("%d Songs In This Setlist") % item.songCount
            font.render(songCount, (x, y + 3*fh), scale = 0.0016)

        elif isinstance(item, song.RandomSongInfo):
            self.theme.setBaseColor(1 - v)

            c1,c2,c3 = self.song_name_selected_color
            glColor3f(c1,c2,c3)

            font.render(_("(Random Song)"), (x, y + 3*fh), scale = 0.0016)

        #MFH CD list
        text = scene.scorePart.text
        scale = 0.00250
        #glColor3f(1, 1, 1)
        c1,c2,c3 = self.song_name_selected_color
        glColor3f(c1,c2,c3)
        w, h = font.getStringSize(text, scale=scale)
        font.render(text, (0.95-w, 0.000), scale=scale)
