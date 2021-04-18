#####################################################################
# -*- coding: utf-8 -*-                                             #
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

from __future__ import with_statement

from OpenGL.GL import *
from collada import Collada
from collada.polygons import Polygons
from collada.scene import RotateTransform
from collada.scene import ScaleTransform
from collada.scene import TranslateTransform
from collada.triangleset import TriangleSet
import numpy as np

from fofix.core import cmgl


class Mesh:

    def __init__(self, filename):
        self.doc = Collada(filename)
        self.geoms = {}
        self.fullGeoms = {}

    def setupLight(self, light, n, pos):
        """ Setup light

        :param light: the light to setup
        :param n: the indice of the light
        :param pos: the position of the light
        :type light: collada.light.BoundLight
        :type n: int
        :type pos: tuple of 3 elements
        """
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0 + n)
        glLightfv(GL_LIGHT0 + n, GL_POSITION, np.array([pos[0], pos[1], pos[2], 0.0], dtype=np.float32))
        glLightfv(GL_LIGHT0 + n, GL_DIFFUSE, np.array([light.color[0], light.color[1], light.color[2], 0.0], dtype=np.float32))
        glLightfv(GL_LIGHT0 + n, GL_AMBIENT, np.array([0.0, 0.0, 0.0, 0.0], dtype=np.float32))

    def setupMaterial(self, material):
        """ Setup material """
        effect = material.effect

        if effect.shadingtype == "phong":
            glMaterialf (GL_FRONT_AND_BACK, GL_SHININESS, effect.shininess)
            glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT,   effect.ambient)
            glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE,   effect.diffuse)
            glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR,  effect.specular)

    def drawElement(self, indices, offset, array, func):
        """ Draw an element

        :param array: list of elements to draw
        :param func: the function to apply
        :type indices: int
        :type offset: int
        """
        if array is not None:
            func(*array[indices[offset]])

    def render(self, geomName=None):
        if geomName in self.fullGeoms:
            self.fullGeoms[geomName]()
            return

        # Prepare a new list for all the geometry
        if not self.geoms:
            # get geometries
            for geom in self.doc.geometries:
                self.geoms[geom.name] = cmgl.GList()
                with self.geoms[geom.name]:

                    # get primitives
                    for prim in geom.primitives:
                        vertices = None
                        normals = None
                        texcoords = None

                        # get input list
                        sources = prim.getInputList()
                        for input_tuple in sources.getList():
                            ioffset, isemantic, isource, iset = input_tuple
                            if isemantic == "VERTEX":
                                vertices = geom.sourceById[isource.lstrip('#')]
                                assert len(vertices.components) == 3
                            elif isemantic == "NORMAL":
                                normals = geom.sourceById[isource.lstrip('#')]
                            elif isemantic == "TEXCOORD":
                                texcoords = geom.sourceById[isource.lstrip('#')]

                        # draw polygons
                        if isinstance(prim, Polygons):
                            for poly in prim:
                                glBegin(GL_POLYGON)
                                if len(poly.texcoord_indices) != 0:
                                    indices = zip(poly.indices,
                                            poly.texcoord_indices[0],
                                            poly.normal_indices)
                                else:
                                    indices = zip(poly.indices,
                                            poly.normal_indices)

                                for i in indices:
                                    self.drawElement(i, -1, normals,   glNormal3f)
                                    self.drawElement(i,  1, texcoords, glTexCoord2f)
                                    self.drawElement(i,  0, vertices,  glVertex3f)
                                glEnd()
                        elif isinstance(prim, TriangleSet):
                            glBegin(GL_TRIANGLES)
                            for triangle in prim:
                                if len(triangle.texcoord_indices) != 0:
                                    indices = zip(triangle.indices,
                                            triangle.texcoord_indices[0],
                                            triangle.normal_indices)
                                else:
                                    indices = zip(triangle.indices,
                                            triangle.normal_indices)

                                for i in indices:
                                    self.drawElement(i, -1, normals,   glNormal3f)
                                    self.drawElement(i,  1, texcoords, glTexCoord2f)
                                    self.drawElement(i,  0, vertices,  glVertex3f)
                            glEnd()

        # Prepare a new display list for this particular geometry
        self.fullGeoms[geomName] = cmgl.GList()
        with self.fullGeoms[geomName]:

            if self.geoms:
                # setup lights
                for scene in self.doc.scenes:
                    for node in scene.nodes:
                        for n, light in enumerate(node.objects('light')):
                            if light:
                                # TODO: hierarchical node transformation, other types of lights
                                pos = [0.0, 0.0, 0.0, 1.0]
                                for t in node.transforms:
                                    if isinstance(t, TranslateTransform):
                                        pos = (t.x, t.y, t.z)
                                self.setupLight(light, n, pos)

                # render geometry
                for scene in self.doc.scenes:
                    for node in scene.nodes:
                        if geomName is not None and node.id != geomName:
                            continue
                        for geom in node.objects('geometry'):
                            if geom:
                                # for matnode in geom.materialnodebysymbol.values():
                                #     mat = matnode.target
                                #     self.setupMaterial(mat)

                                glPushMatrix()
                                for t in node.transforms:
                                    if isinstance(t, TranslateTransform):
                                        glTranslatef(t.x, t.y, t.z)
                                    elif isinstance(t, RotateTransform):
                                        glRotatef(t.angle, t.x, t.y, t.z)
                                    elif isinstance(t, ScaleTransform):
                                        glScalef(t.x, t.y, t.z)
                                if geom.original.name in self.geoms:
                                    self.geoms[geom.original.name]()
                                glPopMatrix()
                glDisable(GL_LIGHTING)
                for n in range(8):
                    glDisable(GL_LIGHT0 + n)

        # Render the new list
        self.render(geomName)

    def find(self, geomName=None):
        """ Find if a node scene exists

        :param geomName: the node scene name to find
        :rtype: boolean
        """
        found = False
        if self.geoms:
            # render geometry
            for scene in self.doc.scenes:
                for node in scene.nodes:
                    if geomName is not None and node.id != geomName:
                        continue
                    found = True
        return found
