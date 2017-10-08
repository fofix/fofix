#!/usr/bin/python
# -*- coding: utf-8 -*-

# FoFiX
# Copyright (C) 2017 FoFiX team
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


import re
import unittest

from fofix.core import Version


class VersionTest(unittest.TestCase):

    def test_revision_git(self):
        """Test the revision format"""
        revision = Version.revision()
        pattern_revision = "development \(git .* \w+\)"
        match_revision = re.match(pattern_revision, revision)
        self.assertIsNotNone(match_revision)

    def test_versionNum(self):
        """Test the version format"""
        version_num = Version.versionNum()
        pattern_version = "\d+.\d+.\d+"
        match_version = re.match(pattern_version, version_num)
        self.assertIsNotNone(match_version)

    def test_version(self):
        """Test the complete version format"""
        complete_version = Version.version()
        version_num = Version.versionNum()
        release = Version.revision()
        expected_version = "%s %s" % (version_num, release)
        self.assertEqual(complete_version, expected_version)
