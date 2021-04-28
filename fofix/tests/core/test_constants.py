#!/usr/bin/python
# -*- coding: utf-8 -*-

import unittest

from fofix.core.constants import isTrue


class ConstantsTest(unittest.TestCase):

    def test_istrue(self):
        # true values
        self.assertTrue(isTrue("1"))
        self.assertTrue(isTrue("true"))
        self.assertTrue(isTrue("yes"))
        self.assertTrue(isTrue("on"))
        # false values
        self.assertFalse(isTrue("0"))
        self.assertFalse(isTrue("false"))
        self.assertFalse(isTrue("off"))
