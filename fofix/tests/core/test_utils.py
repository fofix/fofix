#!/usr/bin/python
# -*- coding: utf-8 -*-

import unittest
import warnings

import six

from fofix.core.utils import deprecated
from fofix.core.utils import unicodify
from fofix.core.utils import utf8


class UtilsTest(unittest.TestCase):

    def test_deprecated_empty(self):
        @deprecated()
        def func(val):
            return val

        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter("always")
            f = func(42)
            self.assertEqual(f, 42)

        self.assertEqual(len(caught_warnings), 1)
        self.assertEqual(caught_warnings[0].category, DeprecationWarning)
        self.assertEqual(str(caught_warnings[0].message), "func is deprecated")

    def test_deprecated_details(self):
        details = "Use another func"

        @deprecated(details=details)
        def func_details(val):
            return val

        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter("always")
            f = func_details(42)
            self.assertEqual(f, 42)

        message = "func_details is deprecated: %s" % details
        self.assertEqual(len(caught_warnings), 1)
        self.assertEqual(caught_warnings[0].category, DeprecationWarning)
        self.assertEqual(str(caught_warnings[0].message), message)

    def test_unicodify(self):
        simple_s = "Jurgen"
        accent_s = "Jürgen"
        simple_b = six.b("Jurgen")
        simple_u = six.u("Jürgen")
        u_simple_s = unicodify(simple_s)
        u_accent_s = unicodify(accent_s)
        u_simple_b = unicodify(simple_b)
        u_simple_u = unicodify(simple_u)

        self.assertIs(type(u_simple_s), six.text_type)
        self.assertIs(type(u_accent_s), six.text_type)
        self.assertIs(type(u_simple_b), six.text_type)
        self.assertIs(type(u_simple_u), six.text_type)
        self.assertEqual(u_simple_s, simple_s)
        self.assertEqual(u_accent_s, six.u("J\xfcrgen"))
        self.assertEqual(u_simple_b, simple_s)
        self.assertEqual(u_simple_u, simple_u)

    def test_utf8(self):
        simple_s = "Jurgen"
        accent_s = "Jürgen"
        simple_b = six.b("Jurgen")
        u_simple_s = utf8(simple_s)
        u_accent_s = utf8(accent_s)
        u_simple_b = utf8(simple_b)

        self.assertIs(type(u_simple_s), six.binary_type)
        self.assertIs(type(u_accent_s), six.binary_type)
        self.assertIs(type(u_simple_b), six.binary_type)
        self.assertEqual(u_simple_s, simple_b)
        self.assertEqual(u_accent_s, u_accent_s)
        self.assertEqual(u_simple_b, simple_b)
