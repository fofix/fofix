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

import Config
import Version
import Log
import gettext
import os
import glob

Config.define("game", "language", str, "")

def getAvailableLanguages():
  return [os.path.basename(l).capitalize().replace(".mo", "").replace("_", " ") for l in glob.glob(os.path.join(Version.dataPath(), "translations", "*.mo"))]

def dummyTranslator(string):
  return string

encoding = Config.load(Version.appName() + ".ini").get("game", "encoding")
language = Config.load(Version.appName() + ".ini").get("game", "language")
_ = dummyTranslator

if language:
  try:
    trFile = os.path.join(Version.dataPath(), "translations", "%s.mo" % language.lower().replace(" ", "_"))
    catalog = gettext.GNUTranslations(open(trFile, "rb"))
    def translate(m):
      if encoding == None:
        return catalog.gettext(m).decode("utf-8")
      else:
        return catalog.gettext(m).decode(encoding)
    _ = translate
  except Exception, x:
    Log.warn("Unable to select language '%s': %s" % (language, x))
    language = None

# Define the config key again now that we have some options for it
langOptions = {"": "English"}
for lang in getAvailableLanguages():
  langOptions[lang] = _(lang)
Config.define("game", "language", str, "", _("Language"), langOptions)
