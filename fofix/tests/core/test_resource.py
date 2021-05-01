#!/usr/bin/python
# -*- coding: utf-8 -*-

import time
import unittest

from Queue import Queue
from threading import BoundedSemaphore

from fofix.core.Resource import Loader
from fofix.core.Resource import Resource


class MyClass(object):

    def __init__(self):
        self.myattribute = "my value"


def load():
    time.sleep(0.01)
    return "my result"


class LoaderTest(unittest.TestCase):

    def setUp(self):
        self.target = MyClass
        name = "myattribute"
        function = load
        result_queue = Queue()
        loader_semaphore = BoundedSemaphore(value=1)
        on_load = None
        on_cancel = None
        self.loader = Loader(self.target, name, function, result_queue, loader_semaphore, on_load, on_cancel)

    def test_init(self):
        self.assertIsNone(self.loader.target.myattribute)

    def test_run(self):
        self.loader.run()
        result = self.loader.resultQueue.get(self.target)
        self.assertEqual(result, self.loader)

    def test_str(self):
        # not canceled
        self.assertEqual(str(self.loader), "load(myattribute) ")

        # canceled
        self.loader.cancel()
        self.assertEqual(str(self.loader), "load(myattribute) (canceled)")

    def test_cancel(self):
        # not canceled
        self.assertFalse(self.loader.canceled)

        # canceled
        self.loader.cancel()
        self.assertTrue(self.loader.canceled)

    def test_load(self):
        # with a fair function
        self.assertEqual(self.loader.time, 0.0)
        self.loader.load()
        self.assertGreater(self.loader.time, 0)
        self.assertEqual(self.loader.result, "my result")
        self.assertIsNone(self.loader.exception)

        # with a bad function
        loader_ko = self.loader
        loader_ko.function = (lambda: 1+"a")
        self.loader.load()
        self.assertIsNotNone(loader_ko.exception)

    def test_finish(self):
        # not canceled
        ## with exception
        err = TypeError("unsupported operand type(s) for +: 'int' and 'str'")
        self.loader.exception = [err.__class__, err, ""]
        with self.assertRaises(TypeError) as cm:
            self.loader.finish()
        self.assertEqual(cm.expected, err.__class__)
        self.assertEqual(str(cm.exception), str(err))

        ## without exception
        self.loader.exception = None
        self.loader.load()
        self.loader.finish()
        self.assertEqual(self.loader.target.myattribute, "my result")

        # restore and cancel
        self.loader.target.myattribute = None
        self.loader.cancel()
        self.loader.load()
        self.loader.finish()
        self.assertIsNone(self.loader.target.myattribute)


class ResourceTest(unittest.TestCase):

    def setUp(self):
        self.datapath = ""

    def test_init(self):
        Resource()

    def test_refresh_base_lib(self):
        resource = Resource()
        resource.refreshBaseLib()

    def test_add_data_path(self):
        path = "another-path"
        resource = Resource()
        # add the path
        resource.addDataPath(path)
        self.assertIn(path, resource.dataPaths)
        # re-add the path
        resource.addDataPath(path)
        self.assertEqual(resource.dataPaths.count(path), 1)

    def test_remove_data_path(self):
        path = "another-path"
        resource = Resource()
        # add the path
        resource.addDataPath(path)
        self.assertIn(path, resource.dataPaths)
        # remove the path
        resource.removeDataPath(path)
        self.assertNotIn(path, resource.dataPaths)
        # remove the path again
        resource.removeDataPath(path)

    def test_load(self):
        resource = Resource()
        # asynchro
        synch = False
        loader = resource.load(MyClass, "myattribute", load, synch)
        self.assertIs(type(loader), Loader)
        self.assertIn(loader, resource.loaders)

        # synchro
        synch = True
        loader = resource.load(MyClass, "myattribute", load, synch)
        self.assertEqual(loader, "my result")
