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

from OpenGL.GL import *

import Collada

class Mesh:
  def __init__(self, fileName):
    self.doc = Collada.DaeDocument()
    self.doc.LoadDocumentFromFile(fileName)
    self.geoms = {}
    
  def _unflatten(self, array, stride):
    return [tuple(array[i * stride : (i + 1) * stride]) for i in range(len(array) / stride)]

  def setupLight(self, light, n, pos):
    l = light.techniqueCommon
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0 + n)
    glLightfv(GL_LIGHT0 + n, GL_POSITION, (pos[0], pos[1], pos[2], 0.0))
    glLightfv(GL_LIGHT0 + n, GL_DIFFUSE, (l.color[0], l.color[1], l.color[2], 0.0))
    glLightfv(GL_LIGHT0 + n, GL_AMBIENT, (0.0, 0.0, 0.0, 0.0))

  def setupMaterial(self, material):
    for m in material.techniqueCommon.iMaterials:
      if m.object:
        for fx in m.object.iEffects:
          if fx.object:
            shader = fx.object.profileCommon.technique.shader
            if isinstance(shader, Collada.DaeFxShadePhong):
              glMaterialf (GL_FRONT_AND_BACK, GL_SHININESS, shader.shininess.float)
              glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT,   shader.ambient.color.rgba)
              glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE,   shader.diffuse.color.rgba)
              glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR,  shader.specular.color.rgba)

  def render(self, geomName = None):
    found = False
    if self.geoms:
      # setup lights
      for scene in self.doc.visualScenesLibrary.items:
        for node in scene.nodes:
          for n, light in enumerate(node.iLights):
            if light.object:
              # TODO: hierarchical node transformation, other types of lights
              pos = [0.0, 0.0, 0.0]
              for t in node.transforms:
                if t[0] == "translate":
                  pos = t[1]
              self.setupLight(light.object, n, pos)
              
      # render geometry
      for scene in self.doc.visualScenesLibrary.items:
        for node in scene.nodes:
          if geomName is not None and node.name != geomName:
            continue
          found = True
          for geom in node.iGeometries:
            if geom.object:
              for mat in geom.bindMaterials:
                self.setupMaterial(mat)
                
              glPushMatrix()
              for t in node.transforms:
                if t[0] == "translate":
                  glTranslatef(*t[1])
                elif t[0] == "rotate":
                  glRotatef(t[1][3], t[1][0], t[1][1], t[1][2])
                elif t[0] == "scale":
                  glScalef(*t[1])
              if geom.object.name in self.geoms:
                glCallList(self.geoms[geom.object.name])
              glPopMatrix()
      glDisable(GL_LIGHTING)
      for n in range(8):
        glDisable(GL_LIGHT0 + n)
      return found

    for geom in self.doc.geometriesLibrary.items:
      self.geoms[geom.name] = glGenLists(1)
      glNewList(self.geoms[geom.name], GL_COMPILE)

      for prim in geom.data.primitives:
        maxOffset = vertexOffset = normalOffset = 0
        vertexOffset = None
        normalOffset = None
        texcoordOffset = None
        vertices = None
        normals = None
        texcoords = None

        for input in prim.inputs:
          maxOffset = max(maxOffset, input.offset)
          if input.semantic == "VERTEX":
            vertexOffset = input.offset
            vertices = geom.data.FindSource(geom.data.vertices.FindInput("POSITION"))
            assert vertices.techniqueCommon.accessor.stride == 3
            vertices = self._unflatten(vertices.source.data, vertices.techniqueCommon.accessor.stride)
          elif input.semantic == "NORMAL":
            normalOffset = input.offset
            normals = geom.data.FindSource(input)
            normals = self._unflatten(normals.source.data, 3)
          elif input.semantic == "TEXCOORD":
            texcoordOffset = input.offset
            texcoords = geom.data.FindSource(input)
            texcoords = self._unflatten(texcoords.source.data, 2)

        if normalOffset is None:
          normals = geom.data.FindSource(geom.data.vertices.FindInput("NORMAL"))
          normals = self._unflatten(normals.source.data, 3)
          normalOffset = vertexOffset

        def drawElement(indices, offset, array, func):
          if offset is not None:
            func(*array[indices[offset]])
        
        if hasattr(prim, "polygons"):
          for poly in prim.polygons:
            glBegin(GL_POLYGON)
            for indices in self._unflatten(poly, maxOffset + 1):
              drawElement(indices, normalOffset,   normals,   glNormal3f)
              drawElement(indices, texcoordOffset, texcoords, glTexCoord2f)
              drawElement(indices, vertexOffset,   vertices,  glVertex3f)
            glEnd()
        elif hasattr(prim, "triangles"):
         glBegin(GL_TRIANGLES)
         for indices in self._unflatten(prim.triangles, maxOffset + 1):
            drawElement(indices, normalOffset,   normals,   glNormal3f)
            drawElement(indices, texcoordOffset, texcoords, glTexCoord2f)
            drawElement(indices, vertexOffset,   vertices,  glVertex3f)
         glEnd()
          
      glEndList()

    if self.geoms:
      return self.render(geomName)

  def find(self, geomName = None):
    found = False
    if self.geoms:            
      # render geometry
      for scene in self.doc.visualScenesLibrary.items:
        for node in scene.nodes:
          if geomName is not None and node.name != geomName:
            continue
          found = True


    return found