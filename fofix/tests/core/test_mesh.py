#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import unittest

from fofix.core.Mesh import Mesh


class MeshTest(unittest.TestCase):

    def setUp(self):
        self.filename = os.path.join('data', 'note.dae')

    def test_find(self):
        mesh = Mesh(self.filename)
        mesh.render()

        self.assertTrue(mesh.find('Mesh_001'))
        self.assertTrue(mesh.find('Mesh_002'))
        self.assertFalse(mesh.find('Mesh_003'))
