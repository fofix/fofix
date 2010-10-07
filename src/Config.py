#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire                                                     #
# Copyright (C) 2006 Sami Kyöstilä                                  #
#               2008 myfingershurt                                  #
#               2008 Capo                                           #
#               2008 Glorandwarf                                    #
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

from ConfigParser import RawConfigParser
import Log
import Resource
import os

encoding  = "iso-8859-1"
config    = None
prototype = {}

logIniReads = 0   #MFH - INI reads disabled by default during the startup period
logUndefinedGets = 0 

class MyConfigParser(RawConfigParser):
  def _writeSection(self, fp, sectionName, sectionItems):
    fp.write("[%s]\n" % sectionName)
    for key, value in sorted(sectionItems):
      if key != "__name__":
        fp.write("%s = %s\n" % (key, str(value).replace('\n', '\n\t')))
    fp.write("\n")

  def write(self, fp, type = 0):
      if type == 1:
        return self.writeController(fp)
      elif type == 2:
        return self.writePlayer(fp)
      if self.defaults():
        self._writeSection(fp, DEFAULTSECT, self.defaults().items())
      for section in sorted(self.sections()):
        if section not in ("theme", "controller", "player"):
          self._writeSection(fp, section, self.items(section))

  def writeTheme(self, fp):
      if self.defaults():
        self._writeSection(fp, DEFAULTSECT, self.defaults().items())
      if self.has_section('theme'):
        self._writeSection(fp, 'theme', self.items('theme'))

  def writeController(self, fp):
      if self.defaults():
        self._writeSection(fp, DEFAULTSECT, self.defaults().items())
      if self.has_section('controller'):
        self._writeSection(fp, 'controller', self.items('controller'))

  def writePlayer(self, fp):
      if self.defaults():
        self._writeSection(fp, DEFAULTSECT, self.defaults().items())
      if self.has_section('player'):
        self._writeSection(fp, 'player', self.items('player'))

class Option:
  """A prototype configuration key."""
  def __init__(self, **args):
    for key, value in args.items():
      setattr(self, key, value)
      
def define(section, option, type, default = None, text = None, options = None, prototype = prototype, tipText = None):
  """
  Define a configuration key.
  
  @param section:    Section name
  @param option:     Option name
  @param type:       Key type (e.g. str, int, ...)
  @param default:    Default value for the key
  @param text:       Text description for the key
  @param options:    Either a mapping of values to text descriptions
                    (e.g. {True: 'Yes', False: 'No'}) or a list of possible values
  @param prototype:  Configuration prototype mapping
  @param tipText:    Helpful tip text to display in option menus.
  """
  if not section in prototype:
    prototype[section] = {}
    
  if type == bool and not options:
    options = [True, False]
    
  prototype[section][option] = Option(type = type, default = default, text = text, options = options, tipText = tipText)

def load(fileName = None, setAsDefault = False, type = 0):
  """Load a configuration with the default prototype"""
  global config, logIniReads, logUndefinedGets
  c = Config(prototype, fileName, type)
  if setAsDefault and not config:
    config = c
  logIniReads = c.get("game", "log_ini_reads")
  logUndefinedGets = c.get("game", "log_undefined_gets")
  return c

#def unLoad():   #MFH - to unload the global config object for later reload
#  global config
#  config = None

class Config:
  """A configuration registry."""
  def __init__(self, prototype, fileName = None, type = 0):
    """
    @param prototype:  The configuration protype mapping
    @param fileName:   The file that holds this configuration registry
    """
    self.prototype = prototype

    # read configuration
    self.config = MyConfigParser()

    if fileName:
      if not os.path.isfile(fileName):
        path = Resource.getWritableResourcePath()
        fileName = os.path.join(path, fileName)
      self.config.read(fileName)
  
    self.fileName  = fileName
    self.type = type
  
    # fix the defaults and non-existing keys
    for section, options in prototype.items():
      if not self.config.has_section(section):
        self.config.add_section(section)
      for option in options.keys():
        type    = options[option].type
        default = options[option].default
        if not self.config.has_option(section, option):
          self.config.set(section, option, str(default))
    
  def get(self, section, option):
    """
    Read a configuration key.
    
    @param section:   Section name
    @param option:    Option name
    @return:          Key value
    """
    
    global logIniReads, logUndefinedGets

    try:
      type    = self.prototype[section][option].type
      default = self.prototype[section][option].default
    except KeyError:
      if logUndefinedGets == 1:
        Log.warn("Config key %s.%s not defined while reading %s." % (section, option, self.fileName))
      type, default = str, None
  
    value = self.config.has_option(section, option) and self.config.get(section, option) or default
    if type == bool:
      value = str(value).lower()
      if value in ("1", "true", "yes", "on"):
        value = True
      elif value in ("none", ""):
        value = default #allows None-default bools to return None
      else:
        value = False
    else:
      try:
        value = type(value)
      except:
        value = None
      
    #myfingershurt: verbose log output
    if logIniReads == 1:
      Log.debug("Config.get: %s.%s = %s" % (section, option, value))
    return value
  
  def getOptions(self, section, option):
    """
    Read the preset options of a configuration key.
    
    @param section:   Section name
    @param option:    Option name
    @return:          Tuple of Key list and Values list
    """
    global logIniReads, logUndefinedGets


    try:
      options = self.prototype[section][option].options.values()
      keys    = self.prototype[section][option].options.keys()
      type    = self.prototype[section][option].type
    except KeyError:
      if logUndefinedGets == 1:
        Log.warn("Config key %s.%s not defined while reading %s." % (section, option, self.fileName))
      type = None
      
    optionList = []
  
    if type != None:
      for i in range(len(options)):
        value = keys[i]
        if type == bool:
          value = str(value).lower()
          if value in ("1", "true", "yes", "on"):
            value = True
          else:
            value = False
        else:
          try:
            value = type(value)
          except:
            value = None
        optionList.append(value)
      
    #myfingershurt: verbose log output
    if logIniReads == 1:
      Log.debug("Config.getOptions: %s.%s = %s" % (section, option, str(optionList)))
    return optionList, options
  
  def getTipText(self, section, option):
    """
    Return the tip text for a configuration key.
    
    @param section:   Section name
    @param option:    Option name
    @return:          Tip Text String
    """
    
    global logIniReads, logUndefinedGets

    try:
      text = self.prototype[section][option].tipText
    except KeyError:
      if logUndefinedGets == 1:
        Log.warn("Config key %s.%s not defined while reading %s." % (section, option, self.fileName))
      text = None
      
    #myfingershurt: verbose log output
    if logIniReads == 1:
      Log.debug("Config.getTipText: %s.%s = %s" % (section, option, text))
    return text

#-------------------------
# glorandwarf: returns the default value of a configuration key
  def getDefault(self, section, option):
    """
    Read the default value of a configuration key.
    
    @param section:   Section name
    @param option:    Option name
    @return:          Key value
    """
    global logIniReads, logUndefinedGets


    try:
      type    = self.prototype[section][option].type
      default = self.prototype[section][option].default
    except KeyError:
      if logUndefinedGets == 1:
        Log.warn("Config key %s.%s not defined while reading %s." % (section, option, self.fileName))
      type, default = str, None
  
    value = default
    if type == bool:
      value = str(value).lower()
      if value in ("1", "true", "yes", "on"):
        value = True
      else:
        value = False
    else:
      try:
        value = type(value)
      except:
        value = None
      
    #myfingershurt: verbose log output
    if logIniReads == 1:
      Log.debug("Config.getDefault: %s.%s = %s" % (section, option, value))
    return value
#-------------------------

  def set(self, section, option, value):
    """
    Set the value of a configuration key.
    
    @param section:   Section name
    @param option:    Option name
    @param value:     Value name
    """

    global logUndefinedGets

    try:
      prototype[section][option]
    except KeyError:
      if logUndefinedGets == 1:
        Log.warn("Config key %s.%s not defined while writing %s." % (section, option, self.fileName))
    
    if not self.config.has_section(section):
      self.config.add_section(section)

    if type(value) == unicode:
      value = value.encode(encoding)
    else:
      value = str(value)

    self.config.set(section, option, value)
    
    f = open(self.fileName, "w")
    self.config.write(f, self.type)
    f.close()


def get(section, option):
  """
  Read the value of a global configuration key.
  
  @param section:   Section name
  @param option:    Option name
  @return:          Key value
  """
  global config
  
  #MFH - for init config.gets
  #if config == None:
  #  load()

  return config.get(section, option)
  
def set(section, option, value):
  """
  Write the value of a global configuration key.
  
  @param section:   Section name
  @param option:    Option name
  @param value:     New key value
  """
  global config
  return config.set(section, option, value)

#-------------------------
# glorandwarf: returns the default value of the configuration key
def getDefault(section, option):
  """
  Read the default value of a global configuration key.
  
  @param section:   Section name
  @param option:    Option name
  @return:          Key value
  """
  global config
  return config.getDefault(section, option)

def getTipText(section, option):
  """
  Return the tip text for a global configuration key.
  
  @param section:   Section name
  @param option:    Option name
  @return:          Tip Text String
  """
  global config
  return config.getTipText(section, option)

#-------------------------
def getOptions(section, option):
  """
  Read the default value of a global configuration key.
  
  @param section:   Section name
  @param option:    Option name
  @return:          Tuple of Key list and Values list
  """
  global config
  return config.getOptions(section, option)

#-------------------------
