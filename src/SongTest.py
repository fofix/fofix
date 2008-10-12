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

import unittest, pygame
import shutil, os, sys

from GameEngine import GameEngine
from Song import Song, Note

class SongTest(unittest.TestCase):
  def testLoading(self):
    e = GameEngine()
    infoFile   = e.resource.fileName("songs", "defy", "song.ini")
    guitarFile = e.resource.fileName("songs", "defy", "guitar.ogg")
    songFile   = e.resource.fileName("songs", "defy", "song.ogg")
    noteFile   = e.resource.fileName("songs", "defy", "notes.mid")
    song = Song(e, infoFile, guitarFile, songFile, None, noteFile)

    assert int(song.bpm) == 122

  def testSaving(self):
    e = GameEngine()
    
    # Make a temp copy
    tmp   = "songtest_tmp"
    files = ["song.ini", "guitar.ogg", "song.ogg", "notes.mid"]
    try:
      os.mkdir(tmp)
      for f in files:
        shutil.copy(e.resource.fileName("songs", "defy", f), tmp)
    
      infoFile   = os.path.join(tmp, "song.ini")
      guitarFile = os.path.join(tmp, "guitar.ogg")
      songFile   = os.path.join(tmp, "song.ogg")
      noteFile   = os.path.join(tmp, "notes.mid")
      song       = Song(e, infoFile, guitarFile, songFile, None, noteFile)
      
      events1 = song.track.allEvents[:]
      
      song.save()
      song       = Song(e, infoFile, guitarFile, songFile, None, noteFile)
      
      events2 = song.track.allEvents[:]

      notes1 = [(time, event) for time, event in events1 if isinstance(event, Note)]      
      notes2 = [(time, event) for time, event in events2 if isinstance(event, Note)]
      
      for i, event in enumerate(zip(notes1, notes2)):
        t1, n1 = event[0]
        t2, n2 = event[1]
        
        if "-v" in sys.argv:
          print "%8d. %.3f + %.3f\t%2d\t     %.3f + %.3f\t%2d" % (i, t1, n1.length, n1.number, t2, n2.length, n2.number)
        
        # Allow 2ms of rounding error
        assert abs(t1 - t2) < 2
        assert abs(n1.length - n2.length) < 2
        assert n1.number == n2.number
    finally:
      # Load another song to free the copy
      pygame.mixer.music.load(e.resource.fileName("songs", "defy", "guitar.ogg"))
      shutil.rmtree(tmp)
    
  
if __name__ == "__main__":
  unittest.main()
