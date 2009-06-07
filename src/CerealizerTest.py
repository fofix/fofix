#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# FoFiX                                                             #
# Copyright (C) 2009 Pascal Giard <evilynux@gmail.com>              #
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
import unittest
try:
  import hashlib
except ImportError:
  import sha
  class hashlib:
    sha1 = sha.sha
import Cerealizer
import binascii
import urllib

class CerealizerTest(unittest.TestCase):
  def setUp(self):
    difficulty = 0      # Expert
    score = 123456      # Final score
    nbrStars = 4        # Number of stars
    name = "SomePlayer" # Player name
    scoreHash = hashlib.sha1("%d%d%d%s" % (difficulty, score, nbrStars, name)
                             ).hexdigest()
    self.scores = {}
    self.scores[difficulty] = [(score, nbrStars, name, scoreHash)]

  def testIntegrity(self):
    expected = self.scores
    scoresSerial = binascii.hexlify(Cerealizer.dumps(self.scores))
    result = Cerealizer.loads(binascii.unhexlify(scoresSerial))
    self.assertEqual(result, expected)

  def testHash(self):
    scoresHash = "63657265616c310a330a646963740a6c6973740a7475706c650a340a"\
                 "6936333834360a69350a7531310a50617363616c4769617264733430"\
                 "0a343839666538656632343239646564373637363835373930303936"\
                 "31323531633136303662373863310a72310a69310a310a72320a72300a"
    scores = Cerealizer.loads(binascii.unhexlify(scoresHash))
    #print scores[1][0][2]
    self.assertEqual(scores[1][0][2], "PascalGiard")

if __name__ == "__main__":
  unittest.main()
