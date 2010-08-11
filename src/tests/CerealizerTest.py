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
import hashlib
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
    # For the record, the worldchart used to reject the following 3 hashes...
    # (name strings are UTF8 encoded)
    scoresHash = "63657265616c310a330a646963740a6c6973740a7475706c650a340a"\
                 "6936333834360a69350a7531310a50617363616c4769617264733430"\
                 "0a343839666538656632343239646564373637363835373930303936"\
                 "31323531633136303662373863310a72310a69310a310a72320a72300a"
    scores = Cerealizer.loads(binascii.unhexlify(scoresHash))
    #print scores[1][0][2]
    self.assertEqual(scores[1][0][2], "PascalGiard")
    #scoreExtHash = "63657265616c310a330a646963740a6c6973740a7475706c650a"\
    #               "390a7334300a3438396665386566323432396465643736373638"\
    #               "353739303039363132353163313630366237386369350a693236"\
    #               "310a693237300a6937320a7331310a466f4669582d332e313030"\
    #               "69300a73300a6936333834360a310a72310a69310a310a72320a"\
    #               "72300a"
    #songHash = "6551c0f99efddfd3c5c7ef2d407c81b8e3001a43"

    # Worldchart accepts this one (name string is NOT UTF8 encoded)
    scoresHash = "63657265616c310a330a646963740a6c6973740a7475706c650a340a"\
                 "693234323032320a69350a73350a417a7a636f7334300a3233336431"\
                 "37373139653539323066366461373034633432343864646632313930"\
                 "32323939656438310a72310a69300a310a72320a72300a"
    scores = Cerealizer.loads(binascii.unhexlify(scoresHash))
    self.assertEqual(scores[0][0][2], "Azzco")
    #print scores[0][0] # Shows that name string IS NOT UTF8 encoded

    # Worldchart used to reject this one (name string is UTF8 encoded)
    scoresHash = "63657265616c310a330a646963740a6c6973740a7475706c650a340a"\
                 "693135313632390a69340a75350a417a7a636f7334300a3661306562"\
                 "35346438343962613065376464363836396430373966386631316366"\
                 "61333133633264310a72310a69300a310a72320a72300a"
    scores = Cerealizer.loads(binascii.unhexlify(scoresHash))
    self.assertEqual(scores[0][0][2], "Azzco")
    print scores[0][0] # Shows that name string IS UTF8 encoded
    print scores[0][0][2]
    score = scores[0][0][0], scores[0][0][1], str(scores[0][0][2]), scores[0][0][3]
    print score

if __name__ == "__main__":
  unittest.main()
