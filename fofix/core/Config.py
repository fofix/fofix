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

import os
import StringIO
from ConfigParser import RawConfigParser

from fretwork import log
from fretwork.unicode import utf8, unicodify

from fofix.core import VFS

config    = None
prototype = {}


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

        for section in sorted(self.sections()):
            if section not in ("theme", "controller", "player"):
                self._writeSection(fp, section, self.items(section))
    def read(self, filenames, encoding=None):
        print filenames
        if isinstance(filenames, str) or isinstance(filenames, unicode):
            filenames = [filenames]

        read_ok = []
        for filename in filenames:
            configData = None
            try:
                with open(filename) as fp:

                    #self._read(fp, filename)
                    configData = fp.read()
                configLines = configData.split('\n')
                configLines = [line for line in configSplit
                                   if line.strip()[0:2] != '//']
                configData = '\n'.join(configLines)
                strFp = StringIO.StringIO(configData)
                self._read(strFp, filename)
            except OSError:
                continue
            read_ok.append(filename)
        return read_ok

    def writeController(self, fp):
        if self.has_section('controller'):
            self._writeSection(fp, 'controller', self.items('controller'))

    def writePlayer(self, fp):
        if self.has_section('player'):
            self._writeSection(fp, 'player', self.items('player'))

    def get(self, section, option):
        return unicodify(RawConfigParser.get(self, section, option))

    def set(self, section, option, value=None):
        if value is not None:
            value = utf8(value)
        RawConfigParser.set(self, section, option, value)

class Option(object):
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
    if section not in prototype:
        prototype[section] = {}

    if type == bool and not options:
        options = [True, False]

    prototype[section][option] = Option(type = type, default = default, text = text, options = options, tipText = tipText)

def load(fileName = None, setAsDefault = False, type = 0):
    """Load a configuration with the default prototype"""
    global config
    c = Config(prototype, fileName, type)
    if setAsDefault and not config:
        config = c
    return c

def _convertValue(value, type, default=False):
    """
    Convert a raw config string to the proper data type.
    @param value: the raw value
    @param type:  the desired type
    @return:      the converted value
    """
    if type is bool:
        value = str(value).lower()
        if value in ("1", "true", "yes", "on"):
            return True
        elif value in ("none", ""):
            return default #allows None-default bools to return None
        else:
            return False
    elif issubclass(type, basestring):
        return unicodify(value)
    else:
        try:
            return type(value)
        except:
            return None

class Config(object):
    """A configuration registry."""
    def __init__(self, prototype, fileName = None, type = 0):
        """
        @param prototype:  The configuration prototype mapping
        @param fileName:   The file that holds this configuration registry
        """
        self.prototype = prototype

        # read configuration
        self.config = MyConfigParser()

        if fileName:
            if not os.path.isfile(fileName):
                path = VFS.getWritableResourcePath()
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

        try:
            type    = self.prototype[section][option].type
            default = self.prototype[section][option].default
        except KeyError:
            log.error("Config key %s.%s not defined while reading %s." % (section, option, self.fileName))
            raise

        value = _convertValue(self.config.get(section, option) if self.config.has_option(section, option) else default, type, default)

        return value

    def getOptions(self, section, option):
        """
        Read the preset options of a configuration key.

        @param section:   Section name
        @param option:    Option name
        @return:          Tuple of Key list and Values list
        """

        try:
            options = self.prototype[section][option].options.values()
            keys    = self.prototype[section][option].options.keys()
            type    = self.prototype[section][option].type
        except KeyError:
            log.error("Config key %s.%s not defined while reading %s." % (section, option, self.fileName))
            raise

        optionList = []

        if type is not None:
            for i in range(len(options)):
                value = _convertValue(keys[i], type)
                optionList.append(value)

        return optionList, options

    def getTipText(self, section, option):
        """
        Return the tip text for a configuration key.

        @param section:   Section name
        @param option:    Option name
        @return:          Tip Text String
        """

        try:
            text = self.prototype[section][option].tipText
        except KeyError:
            log.error("Config key %s.%s not defined while reading %s." % (section, option, self.fileName))
            raise

        return text

    def getDefault(self, section, option):
        """
        Read the default value of a configuration key.

        @param section:   Section name
        @param option:    Option name
        @return:          Key value
        """

        try:
            type    = self.prototype[section][option].type
            default = self.prototype[section][option].default
        except KeyError:
            log.error("Config key %s.%s not defined while reading %s." % (section, option, self.fileName))
            raise

        value = _convertValue(default, type)

        return value

    def set(self, section, option, value):
        """
        Set the value of a configuration key.

        @param section:   Section name
        @param option:    Option name
        @param value:     Value name
        """

        try:
            prototype[section][option]
        except KeyError:
            log.error("Config key %s.%s not defined while writing %s." % (section, option, self.fileName))
            raise

        if not self.config.has_section(section):
            self.config.add_section(section)

        self.config.set(section, option, utf8(value))

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

    return config.get(section, option)

def set(section, option, value):
    """
    Write the value of a global configuration key.

    @param section:   Section name
    @param option:    Option name
    @param value:     New key value
    """
    return config.set(section, option, value)

def getDefault(section, option):
    """
    Read the default value of a global configuration key.

    @param section:   Section name
    @param option:    Option name
    @return:          Key value
    """
    return config.getDefault(section, option)

def getTipText(section, option):
    """
    Return the tip text for a global configuration key.

    @param section:   Section name
    @param option:    Option name
    @return:          Tip Text String
    """
    return config.getTipText(section, option)

def getOptions(section, option):
    """
    Read the default value of a global configuration key.

    @param section:   Section name
    @param option:    Option name
    @return:          Tuple of Key list and Values list
    """
    return config.getOptions(section, option)
