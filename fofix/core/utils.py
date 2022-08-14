#!/usr/bin/python
# -*- coding: utf-8 -*-

import functools
import warnings

import six


def deprecated(deprecated_in=None, removed_in=None, details=""):
    """Decorator for deprecation

    See https://pypi.org/project/deprecation/
    """
    def _function_wrapper(func):

        @functools.wraps(func)
        def _inner(*args, **kwargs):
            deprecated_in_msg, removed_in_msg, details_msg = "", "", ""
            if deprecated_in is not None:
                deprecated_in_msg = " as of %s" % deprecated_in
            if removed_in is not None:
                removed_in_msg = " and will be removed in %s" % removed_in
            if details:
                details_msg = ": %s" % details

            message = "%s is deprecated%s%s%s" % (func.__name__, deprecated_in_msg, removed_in_msg, details_msg)
            warnings.warn(message, category=DeprecationWarning, stacklevel=2)

            return func(*args, **kwargs)

        return _inner
    return _function_wrapper


@deprecated(details="Use fretwork.unicode.unicodify (v1) instead")
def unicodify(s):
    """Return a unicode string"""
    if isinstance(s, six.binary_type):
        return s.decode('utf-8')

    if isinstance(s, six.text_type):
        return s

    return str(s)


@deprecated(details="Use fretwork.unicode.utf8 (v1) instead")
def utf8(s):
    """Return a valid UTF-8 bytestring"""
    return unicodify(s).encode("utf-8")
