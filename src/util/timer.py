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

        self.currentTime = self.previousTime = self.time()

        self.tickDelta = 0

    def time(self):
        return timeFunc() * 1000

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
        ''' Returns the delta between the current and previous ticks '''

        self.previousTime = self.currentTime
        self.currentTime = self.time()
        self.tickDelta = self.currentTime - self.previousTime

        self.fpsTime += self.tickDelta
        self.frames += 1

        return self.tickDelta

    def get_fps(self):
        self.fps = self.frames / (self.fpsTime / 1000.0)
        self.fpsTime = 0
        self.frames = 0

        return self.fps

    def delay(self, fps):

        if fps:
            endtime = 1000.0/fps
            delay = int( endtime - (self.time() - self.currentTime) )

            if delay < 0:
                delay = 0

            #print (endtime, self.tickDelta, delay)

            pygame.time.delay(delay)

