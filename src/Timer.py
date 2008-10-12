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
import time

class Timer(object):
  def __init__(self, fps = 60, tickrate = 1.0):
    self.fps                   = fps
    self.timestep              = 1000.0 / fps
    self.tickrate              = tickrate
    self.ticks                 = self.getTime()
    self.frame                 = 0
    self.fpsEstimate           = 0
    self.fpsEstimateStartTick  = self.ticks
    self.fpsEstimateStartFrame = self.frame
    self.highPriority          = False

  def getTime(self):
    return int(pygame.time.get_ticks() * self.tickrate)

  time = property(getTime)

  def advanceFrame(self):
    while True:
      ticks = self.getTime()
      diff = ticks - self.ticks
      if diff >= self.timestep:
        break
      if not self.highPriority:
        pygame.time.wait(0)

    self.ticks = ticks
    self.frame += 1

    if ticks > self.fpsEstimateStartTick + 250:
      n = self.frame - self.fpsEstimateStartFrame
      self.fpsEstimate = 1000.0 * n / (ticks - self.fpsEstimateStartTick)
      self.fpsEstimateStartTick = ticks
      self.fpsEstimateStartFrame = self.frame

    return [min(diff, self.timestep * 16)]
    #timeslice = max(self.timestep, min(diff, self.timestep * 16))
    #timeslice = max(self.timestep, timeslice - self.timestep)
    #return [self.timestep] * int(self.timestep / timeslice)
