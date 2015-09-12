#####################################################################
# Frets on Fire X (FoFiX)                                           #
# Copyright (C) 2014 FoFiX Team                                     #
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

import platform
import time
import pygame.time


# Clock on Unix systems is not accurate and only counts program running time
# On windows it counts all time
# But time isnt as good as clock on windows
# If we move to python 3.3+ we can move to solely time.monotonic()
# If time is not monitonic the timer could get negitive delta values (bad)
if platform.system() == 'Windows':
    timeFunc = time.clock
else:
    timeFunc = time.time

class Timer(object):
    def __init__(self):

        self.startTime = self.currentTime = self.previousTime = self.time()

        self.tickDelta = 0

    def time(self):
        ''' Get current time in milliseconds '''
        return timeFunc() * 1000

    def delta_time(self):
        '''Return time delta since startTime'''
        return self.time() - self.startTime

    def tick(self):
        ''' Returns the delta between the current and previous ticks '''

        self.previousTime = self.currentTime
        self.currentTime = self.time()
        self.tickDelta = self.currentTime - self.previousTime

        return self.tickDelta

class FpsTimer(Timer):
    def __init__(self):

        super(FpsTimer, self).__init__()

        self.frames = 0
        self.fpsTime = 0
        self.fps = 0

    def tick(self):
        ''' Calculates time delta since last call. 
            Also accumulates the delta and increments frame counter. '''

        self.previousTime = self.currentTime
        self.currentTime = self.time()
        self.tickDelta = self.currentTime - self.previousTime

        self.fpsTime += self.tickDelta
        self.frames += 1

        return self.tickDelta

    def get_fps(self):
        ''' Calculates and return the average fps then resets the counter. '''
        if self.fpsTime == 0:
            self.fpsTime += 1
        self.fps = self.frames / (self.fpsTime / 1000.0)
        self.fpsTime = 0
        self.frames = 0

        return self.fps

    def delay(self, fps):
        ''' Reimplementation of pygame.time.Clock.tick() delay functionality. Needed for fps limiting.'''

        if fps:
            endtime = 1000.0/fps
            delay = (endtime - (self.time() - self.currentTime))
            if delay < 0:
                delay = 0

            # Limit FPS
            # pygame did a very inaccurate job because the imput value
            # needed to be an integer
            while (delay):
                curr = self.time() - self.currentTime
                if endtime <= curr:
                    break

