#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire                                                     #
# Copyright (C) 2006 Sami Kyöstilä                                  #
#               2008 myfingershurt                                  #
#               2008 evilynux <evilynux@gmail.com>                  #
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

import re
import os
from xml import sax
from OpenGL.GL import *
from Numeric import reshape, matrixmultiply, transpose, identity, zeros, Float
from math import sin, cos

import Log
import Config
from Texture import Texture, TextureException

import DummyAmanith as amanith
haveAmanith = True

# Add support for 'foo in attributes' syntax
if not hasattr(sax.xmlreader.AttributesImpl, '__contains__'):
  sax.xmlreader.AttributesImpl.__contains__ = sax.xmlreader.AttributesImpl.has_key

#
#  Bugs and limitations:
#
#  - only the translate() and matrix() transforms are supported
#  - only paths are supported
#  - only constant color, linear gradient and radial gradient fill supported
#

Config.define("opengl",  "svgshaders",   bool,  False, text = "Use OpenGL SVG shaders",   options = {False: "No", True: "Yes"})

class SvgGradient:
  def __init__(self, gradientDesc, transform):
    self.gradientDesc = gradientDesc
    self.transform = transform

  def applyTransform(self, transform):
    m = matrixmultiply(transform.matrix, self.transform.matrix)
    self.gradientDesc.SetMatrix(transform.getGMatrix(m))

class SvgContext:
  def __init__(self, geometry):
    self.kernel = amanith.GKernel()
    self.geometry = geometry
    self.drawBoard = amanith.GOpenGLBoard(geometry[0], geometry[0] + geometry[2],
                                          geometry[1], geometry[1] + geometry[3])
    self.drawBoard.SetShadersEnabled(Config.get("opengl", "svgshaders"))
    self.transform = SvgTransform()
    self.setGeometry(geometry)
    self.setProjection(geometry)
  
    # eat any possible OpenGL errors -- we can't handle them anyway
    try:
      glMatrixMode(GL_MODELVIEW)
    except:
      Log.warn("SVG renderer initialization failed; expect corrupted graphics. " +
               "To fix this, upgrade your OpenGL drivers and set your display " +
               "to 32 bit color precision.")

  def setGeometry(self, geometry = None):
    self.drawBoard.SetViewport(geometry[0], geometry[1],
                               geometry[2], geometry[3])
    self.transform.reset()
    self.transform.scale(geometry[2] / 640.0, geometry[3] / 480.0)

  def setProjection(self, geometry = None):
    geometry = geometry or self.geometry
    self.drawBoard.SetProjection(geometry[0], geometry[0] + geometry[2],
                                 geometry[1], geometry[1] + geometry[3])
    self.geometry = geometry

  def clear(self, r = 0, g = 0, b = 0, a = 0):
    self.drawBoard.Clear(r, g, b, a)

class SvgRenderStyle:
  def __init__(self, baseStyle = None):
    self.strokeColor = None
    self.strokeWidth = None
    self.fillColor = None
    self.strokeLineJoin = None
    self.strokeOpacity = None
    self.fillOpacity = None
    
    if baseStyle:
      self.__dict__.update(baseStyle.__dict__)

  def parseStyle(self, style):
    s = {}
    for m in re.finditer(r"(.+?):\s*(.+?)(;|$)\s*", style):
      s[m.group(1)] = m.group(2)
    return s

  def parseColor(self, color, defs = None):
    if color.lower() == "none":
      return None

    try:
      return SvgColors.colors[color.lower()]
    except KeyError:
      pass
      
    if color[0] == "#":
      color = color[1:]
      if len(color) == 3:
        return (int(color[0], 16) / 15.0, int(color[1], 16) / 15.0, int(color[2], 16) / 15.0, 1.0)
      return (int(color[0:2], 16) / 255.0, int(color[2:4], 16) / 255.0, int(color[4:6], 16) / 255.0, 1.0)
    else:
      if not defs:
        Log.warn("No patterns or gradients defined.")
        return None
      m = re.match("url\(#(.+)\)", color)
      if m:
        id = m.group(1)
        if not id in defs:
          Log.warn("Pattern/gradient %s has not been defined." % id)
        return defs.get(id)

  def __cmp__(self, s):
    if s:
      for k, v in self.__dict__.items():
        if v != getattr(s, k):
          return 1
      return 0
    return 1

  def __repr__(self):
    return "<SvgRenderStyle " + " ".join(["%s:%s" % (k, v) for k, v in self.__dict__.items()]) + ">"

  def applyAttributes(self, attrs, defs):
    style = attrs.get("style")
    if style:
      style = self.parseStyle(style)
      #print style
      if "stroke" in style:
        self.strokeColor = self.parseColor(style["stroke"], defs)
      if "fill" in style:
        self.fillColor = self.parseColor(style["fill"], defs)
      if "stroke-width" in style:
        self.strokeWidth = float(style["stroke-width"].replace("px", ""))
      if "stroke-opacity" in style:
        self.strokeOpacity = float(style["stroke-opacity"])
      if "fill-opacity" in style:
        self.fillOpacity = float(style["fill-opacity"])
      if "stroke-linejoin" in style:
        j = style["stroke-linejoin"].lower()
        if j == "miter":
          self.strokeLineJoin = amanith.G_MITER_JOIN
        elif j == "round":
          self.strokeLineJoin = amanith.G_ROUND_JOIN
        elif j == "bevel":
          self.strokeLineJoin = amanith.G_BEVEL_JOIN

  def apply(self, drawBoard, transform):
    if self.strokeColor is not None:
      if isinstance(self.strokeColor, SvgGradient):
        self.strokeColor.applyTransform(transform)
        drawBoard.SetStrokePaintType(amanith.G_GRADIENT_PAINT_TYPE)
        drawBoard.SetStrokeGradient(self.strokeColor.gradientDesc)
      else:
        drawBoard.SetStrokePaintType(amanith.G_COLOR_PAINT_TYPE)
        drawBoard.SetStrokeColor(*self.strokeColor)
      drawBoard.SetStrokeEnabled(True)
    else:
      drawBoard.SetStrokeEnabled(False)
    
    if self.fillColor is not None:
      if isinstance(self.fillColor, SvgGradient):
        self.fillColor.applyTransform(transform)
        drawBoard.SetFillPaintType(amanith.G_GRADIENT_PAINT_TYPE)
        drawBoard.SetFillGradient(self.fillColor.gradientDesc)
      else:
        drawBoard.SetFillPaintType(amanith.G_COLOR_PAINT_TYPE)
        drawBoard.SetFillColor(*self.fillColor)
      drawBoard.SetFillEnabled(True)
    else:
      drawBoard.SetFillEnabled(False)

    if self.strokeWidth is not None:
      drawBoard.SetStrokeWidth(self.strokeWidth)
    
    if self.strokeOpacity is not None:
      drawBoard.SetStrokeOpacity(self.strokeOpacity)
      
    if self.fillOpacity is not None:
      drawBoard.SetFillOpacity(self.fillOpacity)

    if self.strokeLineJoin is not None:
      drawBoard.SetStrokeJoinStyle(self.strokeLineJoin)

class SvgTransform:
  def __init__(self, baseTransform = None):
    self._gmatrix = amanith.GMatrix33()
    self.reset()
    
    if baseTransform:
      self.matrix = baseTransform.matrix.copy()

  def applyAttributes(self, attrs, key = "transform"):
    transform = attrs.get(key)
    if transform:
      m = re.match(r"translate\(\s*(.+?)\s*,(.+?)\s*\)", transform)
      if m:
        dx, dy = [float(c) for c in m.groups()]
        self.matrix[0, 2] += dx
        self.matrix[1, 2] += dy
      m = re.match(r"matrix\(\s*" + "\s*,\s*".join(["(.+?)"] * 6) + r"\s*\)", transform)
      if m:
        e = [float(c) for c in m.groups()]
        e = [e[0], e[2], e[4], e[1], e[3], e[5], 0, 0, 1]
        m = reshape(e, (3, 3))
        self.matrix = matrixmultiply(self.matrix, m)

  def transform(self, transform):
    self.matrix = matrixmultiply(self.matrix, transform.matrix)

  def reset(self):
    self.matrix = identity(3, typecode = Float)

  def translate(self, dx, dy):
    m = zeros((3, 3))
    m[0, 2] = dx
    m[1, 2] = dy
    self.matrix += m

  def rotate(self, angle):
    m = identity(3, typecode = Float)
    s = sin(angle)
    c = cos(angle)
    m[0, 0] =  c
    m[0, 1] = -s
    m[1, 0] =  s
    m[1, 1] =  c
    self.matrix = matrixmultiply(self.matrix, m)

  def scale(self, sx, sy):
    m = identity(3, typecode = Float)
    m[0, 0] = sx
    m[1, 1] = sy
    self.matrix = matrixmultiply(self.matrix, m)

  def applyGL(self):
    # Interpret the 2D matrix as 3D
    m = self.matrix
    m = [m[0, 0], m[1, 0], 0.0, 0.0,
         m[0, 1], m[1, 1], 0.0, 0.0,
             0.0,     0.0, 1.0, 0.0,
         m[0, 2], m[1, 2], 0.0, 1.0]
    glMultMatrixf(m)

  def getGMatrix(self, m):
    self._gmatrix.Set( \
      m[0, 0], m[0, 1], m[0, 2], \
      m[1, 0], m[1, 1], m[1, 2], \
      m[2, 0], m[2, 1], m[2, 2])
    return self._gmatrix

  def apply(self, drawBoard):
    drawBoard.SetModelViewMatrix(self.getGMatrix(self.matrix))

class SvgHandler(sax.ContentHandler):
  def __init__(self, drawBoard, cache):
    self.drawBoard = drawBoard
    self.styleStack = [SvgRenderStyle()]
    self.contextStack = [None]
    self.transformStack = [SvgTransform()]
    self.defs = {}
    self.cache = cache
  
  def startElement(self, name, attrs):
    style = SvgRenderStyle(self.style())
    style.applyAttributes(attrs, self.defs)
    self.styleStack.append(style)
    
    transform = SvgTransform(self.transform())
    transform.applyAttributes(attrs)
    self.transformStack.append(transform)
    
    try:
      f = "start" + name.capitalize()
      #print f, self.transformStack
      #print len(self.styleStack)
      f = getattr(self, f)
    except AttributeError:
      return
    f(attrs)

  def endElement(self, name):
    try:
      f = "end" + name.capitalize()
      #print f, self.contextStack
      getattr(self, f)()
    except AttributeError:
      pass
    self.styleStack.pop()
    self.transformStack.pop()

  def startG(self, attrs):
    self.contextStack.append("g")

  def endG(self):
    self.contextStack.pop()

  def startDefs(self, attrs):
    self.contextStack.append("defs")

  def endDefs(self):
    self.contextStack.pop()

  def startMarker(self, attrs):
    self.contextStack.append("marker")

  def endMarker(self):
    self.contextStack.pop()

  def context(self):
    return self.contextStack[-1]

  def style(self):
    return self.styleStack[-1]

  def transform(self):
    return self.transformStack[-1]

  def startPath(self, attrs):
    if self.context() in ["g", None]:
      if "d" in attrs:
        self.style().apply(self.drawBoard, self.transform())
        self.transform().apply(self.drawBoard)
        d = str(attrs["d"])
        self.cache.addStroke(self.style(), self.transform(), self.drawBoard.DrawPaths(d))

  def createLinearGradient(self, attrs, keys):
    a = dict(attrs)
    if not "x1" in a or not "x2" in a or not "y1" in a or not "y2" in a:
      a["x1"] = a["y1"] = 0.0
      a["x2"] = a["y2"] = 1.0
    if "id" in a and "x1" in a and "x2" in a and "y1" in a and "y2" in a:
      transform = SvgTransform()
      if "gradientTransform" in a:
        transform.applyAttributes(a, key = "gradientTransform")
      x1, y1, x2, y2 = [float(a[k]) for k in ["x1", "y1", "x2", "y2"]]
      return a["id"], self.drawBoard.CreateLinearGradient((x1, y1), (x2, y2), keys), transform
    return None, None, None

  def createRadialGradient(self, attrs, keys):
    a = dict(attrs)
    if not "cx" in a or not "cy" in a or not "fx" in a or not "fy" in a:
      a["cx"] = a["cy"] = 0.0
      a["fx"] = a["fy"] = 1.0
    if "id" in a and "cx" in a and "cy" in a and "fx" in a and "fy" in a and "r" in a:
      transform = SvgTransform()
      if "gradientTransform" in a:
        transform.applyAttributes(a, key = "gradientTransform")
      cx, cy, fx, fy, r = [float(a[k]) for k in ["cx", "cy", "fx", "fy", "r"]]
      return a["id"], self.drawBoard.CreateRadialGradient((cx, cy), (fx, fy), r, keys), transform
    return None, None, None

  def startLineargradient(self, attrs):
    if self.context() == "defs":
      if "xlink:href" in attrs:
        id = attrs["xlink:href"][1:]
        if not id in self.defs:
          Log.warn("Linear gradient %s has not been defined." % id)
        else:
          keys = self.defs[id].gradientDesc.ColorKeys()
          id, grad, trans = self.createLinearGradient(attrs, keys)
          self.defs[id] = SvgGradient(grad, trans)
      else:
        self.contextStack.append("gradient")
        self.stops = []
        self.gradientAttrs = attrs
    
  def startRadialgradient(self, attrs):
    if self.context() == "defs":
      if "xlink:href" in attrs:
        id = attrs["xlink:href"][1:]
        if not id in self.defs:
          Log.warn("Radial gradient %s has not been defined." % id)
        else:
          keys = self.defs[id].gradientDesc.ColorKeys()
          id, grad, trans = self.createRadialGradient(attrs, keys)
          self.defs[id] = SvgGradient(grad, trans)
      else:
        self.contextStack.append("gradient")
        self.stops = []
        self.gradientAttrs = attrs

  def parseKeys(self, stops):
    keys = []
    for stop in self.stops:
      color, opacity, offset = None, None, None
      if "style" in stop:
        style =  self.style().parseStyle(stop["style"])
        if "stop-color" in style:
          color = self.style().parseColor(style["stop-color"])
        if "stop-opacity" in style:
          opacity = float(style["stop-opacity"])
      if "offset" in stop:
        offset = float(stop["offset"])
      if offset is not None and (color is not None or opacity is not None):
        if opacity is None: opacity = 1.0
        k = amanith.GKeyValue(offset, (color[0], color[1], color[2], opacity))
        keys.append(k)
    return keys
    
  def endLineargradient(self):
    if self.context() == "gradient":
      keys = self.parseKeys(self.stops)
      id, grad, trans = self.createLinearGradient(self.gradientAttrs, keys)
      del self.stops
      del self.gradientAttrs
      if id and grad:
        self.defs[id] = SvgGradient(grad, trans)
      self.contextStack.pop()
    
  def endRadialgradient(self):
    if self.context() == "gradient":
      keys = self.parseKeys(self.stops)
      id, grad, trans = self.createRadialGradient(self.gradientAttrs, keys)
      del self.stops
      del self.gradientAttrs
      if id and grad:
        self.defs[id] = SvgGradient(grad, trans)
      self.contextStack.pop()
    
  def startStop(self, attrs):
    if self.context() == "gradient":
      self.stops.append(attrs)
    
class SvgCache:
  def __init__(self, drawBoard):
    self.drawBoard = drawBoard
    self.displayList = []
    self.transforms = {}
    self.bank = drawBoard.CreateCacheBank()

  def beginCaching(self):
    self.drawBoard.SetCacheBank(self.bank)
    self.drawBoard.SetTargetMode(amanith.G_CACHE_MODE)

  def endCaching(self):
    self.drawBoard.SetTargetMode(amanith.G_COLOR_MODE)
    self.drawBoard.SetCacheBank(None)

  def addStroke(self, style, transform, slot):
    if self.displayList:
      lastStyle = self.displayList[-1][0]
    else:
      lastStyle = None

    self.transforms[slot] = transform
    
    if lastStyle == style:
      lastSlotStart, lastSlotEnd = self.displayList[-1][1][-1]
      if lastSlotEnd == slot - 1:
        self.displayList[-1][1][-1] = (lastSlotStart, slot)
      else:
        self.displayList[-1][1].append((slot, slot))
    else:
      self.displayList.append((style, [(slot, slot)]))

  def draw(self, baseTransform):
    self.drawBoard.SetCacheBank(self.bank)
    for style, slotList in self.displayList:
      transform = SvgTransform(baseTransform)
      transform.transform(self.transforms[slotList[0][0]])
      transform.apply(self.drawBoard)
      style.apply(self.drawBoard, transform)
      for firstSlot, lastSlot in slotList:
        self.drawBoard.DrawCacheSlots(firstSlot, lastSlot)
    self.drawBoard.SetCacheBank(None)

    # eat any possible OpenGL errors -- we can't handle them anyway
    try:
      glMatrixMode(GL_MODELVIEW)
    except:
      pass

class ImgDrawing:
  def __init__(self, context, ImgData):
    self.ImgData = None
    self.texture = None
    self.context = context
    self.cache = None
    self.transform = SvgTransform()

    # Detect the type of data passed in
    if type(ImgData) == file:
      self.ImgData = ImgData.read()
    elif type(ImgData) == str:
      bitmapFile = ImgData.replace(".svg", ".png")
      # Load PNG files directly
      if ImgData.endswith(".png"):
        self.texture = Texture(ImgData)
      # Check whether we have a prerendered bitmap version of the SVG file
      elif ImgData.endswith(".svg") and os.path.exists(bitmapFile):
        Log.debug("Loading cached bitmap '%s' instead of '%s'." % (bitmapFile, ImgData))
        self.texture = Texture(bitmapFile)
      else:
        if not haveAmanith:
          e = "PyAmanith support is deprecated and you are trying to load an SVG file."
          Log.error(e)
          raise RuntimeError(e)
        Log.debug("Loading SVG file '%s'." % (ImgData))
        self.ImgData = open(ImgData).read()

    # Make sure we have a valid texture
    if not self.texture:
      if type(ImgData) == str:
        e = "Unable to load texture for %s." % ImgData
      else:
        e = "Unable to load texture for SVG file."
      Log.error(e)
      raise RuntimeError(e)

  def _cacheDrawing(self, drawBoard):
    self.cache.beginCaching()
    parser = sax.make_parser()
    sax.parseString(self.ImgData, SvgHandler(drawBoard, self.cache))
    self.cache.endCaching()
    del self.ImgData

  def convertToTexture(self, width, height):
    if self.texture:
      return

    e = "SVG drawing does not have a valid texture image."
    Log.error(e)
    raise RuntimeError(e)

  def _getEffectiveTransform(self):
    transform = SvgTransform(self.transform)
    transform.transform(self.context.transform)
    return transform

  def width1(self):
    width = self.texture.pixelSize[0]
    if not width == None:
      return width
    else:
      return 0

  #myfingershurt:
  def height1(self):
    height = self.texture.pixelSize[1]
    if not height == None:
      return height
    else:
      return 0


  def widthf(self, pixelw):
    width = self.texture.pixelSize[0]
    wfactor = pixelw/width
    if not width == None:
      return wfactor
    else:
      return 0    

  def _render(self, transform):
    glMatrixMode(GL_TEXTURE)
    glPushMatrix()
    glMatrixMode(GL_MODELVIEW)
    
    glPushAttrib(GL_ENABLE_BIT | GL_TEXTURE_BIT | GL_STENCIL_BUFFER_BIT | GL_TRANSFORM_BIT | GL_COLOR_BUFFER_BIT | GL_POLYGON_BIT | GL_CURRENT_BIT | GL_DEPTH_BUFFER_BIT)
    if not self.cache:
      self.cache = SvgCache(self.context.drawBoard)
      self._cacheDrawing(self.context.drawBoard)
    self.cache.draw(transform)
    glPopAttrib()

    glMatrixMode(GL_TEXTURE)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

  def draw(self, color = (1, 1, 1, 1), rect = (0,1,0,1)):
    glMatrixMode(GL_TEXTURE)
    glPushMatrix()
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    self.context.setProjection()
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()

    transform = self._getEffectiveTransform()
    if self.texture:
      glLoadIdentity()
      transform.applyGL()

      glScalef(self.texture.pixelSize[0], self.texture.pixelSize[1], 1)
      glTranslatef(-.5, -.5, 0)
      glColor4f(*color)
      
      self.texture.bind()
      glEnable(GL_TEXTURE_2D)
      glBegin(GL_TRIANGLE_STRIP)
      glTexCoord2f(rect[0], rect[3])
      glVertex2f(0.0, 1.0)
      glTexCoord2f(rect[1], rect[3])
      glVertex2f(1.0, 1.0)
      glTexCoord2f(rect[0], rect[2])
      glVertex2f(0.0, 0.0)
      glTexCoord2f(rect[1], rect[2])
      glVertex2f(1.0, 0.0)
      glEnd()
      glDisable(GL_TEXTURE_2D)
    else:
      self._render(transform)
    glMatrixMode(GL_TEXTURE)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
