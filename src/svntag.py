# pitchbend - pitch-bend the output of the SDL mixer
# Copyright (C) 2008-2009 John Stumpo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

#__version__ = '$Id: svntag.py 5 2009-01-01 05:00:35Z stump $'

import os

def get_svn_info(path='.'):
  f = open(os.path.join(path, '.svn', 'entries'))
  f.readline(200)
  f.readline(200)
  f.readline(200)
  num_str = f.readline(200).strip()
  repo_str = f.readline(200).strip()
  f.readline(200)
  f.readline(200)
  f.readline(200)
  f.readline(200)
  #date_str, time_str = f.readline(200).strip().partition('T')[::2]
  #return {'revnum': num_str, 'repo': repo_str, 'date': date_str,  'time': time_str}
  return {'revnum': num_str, 'repo': repo_str}
  
if __name__ == '__main__':
  import sys
  try:
    print repr(get_svn_info(sys.argv[1]))
  except IndexError:
    print repr(get_svn_info())
