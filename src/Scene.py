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

from Player import Player
from View import BackgroundLayer
from Session import MessageHandler, Message
from Input import KeyListener
from Camera import Camera
import Network
import Player
import Config

from OpenGL.GL import *
from OpenGL.GLU import *
#from OpenGL.GLUT import *
import math
import colorsys
import pygame
from Numeric import array, Float, transpose, reshape, matrixmultiply

Config.define("network", "updateinterval", int, 72)

# Messages from client to server
class CreateActor(Message): pass
class ControlEvent(Message): pass

# Messages from server to client
class ActorCreated(Message): pass
class ActorDeleted(Message): pass
class ActorData(Message): pass
class ControlData(Message): pass

class Actor:
  def __init__(self, scene):
    self.scene = scene
    self.body = ode.Body(scene.world)
    self.geom = None
    self.mass = ode.Mass()
    self.svgDrawing = None
    self.scale = 1.0
    self.rotation = 0

  def getState(self):
    return (self.body.getPosition(),
            self.body.getQuaternion(),
            self.body.getLinearVel(),
            self.body.getAngularVel())

  def setSvgDrawing(self, svgDrawing):
    svgDrawing.convertToTexture(256, 256)
    self.svgDrawing = svgDrawing

  def setState(self, pos, quat, linearVel, angularVel):
    self.body.setPosition(pos)
    self.body.setQuaternion(quat)
    self.body.setLinearVel(linearVel)
    self.body.setAngularVel(angularVel)

  def render(self):
    s = self.svgDrawing
    if not s:
      return

    x, y, z    = self.body.getPosition()
    modelview  = glGetDoublev(GL_MODELVIEW_MATRIX)
    projection = glGetDoublev(GL_PROJECTION_MATRIX)
    viewport   = glGetIntegerv(GL_VIEWPORT)

    # calculate the z coordinate
    m = transpose(reshape(modelview, (4, 4)))
    wz = -matrixmultiply(m, reshape((x, y, z, 1), (4, 1)))[2][0]

    # don't draw anything if we're behind the viewer
    if wz < 0.1:
      return

    # calculate the screen-space x and y coordinates
    x, y, z = gluProject(x, y, z, modelview, projection, viewport)
    scale = self.scale / wz

    s.transform.reset()
    s.transform.translate(x, y)
    s.transform.scale(scale, -scale)
    s.transform.rotate(self.rotation)
    s.draw()

class BoxActor(Actor):
  def __init__(self, scene, owner, size = [1.0, 1.0, 1.0], density = 1.0):
    Actor.__init__(self, scene)
    self.owner = owner
    self.size = size
    self.mass.setBox(density, size[0], size[1], size[2])
    self.geom = ode.GeomBox(self.scene.space, lengths = size)
    self.geom.setBody(self.body)
    import random
    self.body.setPosition((random.random(), random.random(), random.random() * 3))
    
  def render(self):
    Actor.render(self)

    x, y, z = self.body.getPosition()
    R = self.body.getRotation()
    T = array((R[0], R[3], R[6], 0,
               R[1], R[4], R[7], 0,
               R[2], R[5], R[8], 0,
                  x,    y,    z, 1), Float)
    glPushMatrix()
    glMultMatrixd(T.tolist())
    sx, sy, sz = self.size
    glScale(sx, sy, sz)

    glDisable(GL_LIGHTING)
    glEnable(GL_BLEND)
    glBlendFunc(GL_ONE, GL_ONE)

    glFrontFace(GL_CW)
    glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
    glColor3f(1, 1, 1)
    #glutSolidCube(1)
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    glEnable(GL_LIGHTING)
    glFrontFace(GL_CCW)
    glColor4f(*[abs(x) + .3 for x in self.body.getLinearVel() + (.5,)])
    glScale(.97, .97, .97)
    #glutSolidCube(1)
    glDisable(GL_LIGHTING)
    glPopMatrix()
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

#glutInit([]) # FIXME: do we need glut?

class Scene(MessageHandler, BackgroundLayer):
  def __init__(self, engine, owner, **args):
    self.objects = Network.ObjectCollection()
    self.args    = args
    self.owner   = owner
    self.engine  = engine
    self.actors  = []
    self.camera  = Camera()
    self.world   = None
    self.space   = None
    self.time    = 0.0
    self.actors  = []
    self.players = []
    self.createCommon(**args)

  def initPhysics(self):
    import ode

    # Create a default world and a space
    self.world = ode.World()
    self.world.setGravity((0, -9.81 , 0))
    self.world.setERP(0.8)
    self.world.setCFM(1e-5)
    self.space = ode.Space()
    self.contactGroup = ode.JointGroup()

  def addPlayer(self, player):
    self.players.append(player)

  def removePlayer(self, player):
    self.players.remove(player)

  def createCommon(self, **args):
    pass

  def runCommon(self, ticks, world):
    pass
    
  def run(self, ticks):
    self.time += ticks / 50.0

    if self.world:
      self.contactGroup.empty()
      self.space.collide(None, self.nearCallback)
      self.world.step(ticks / 512.0)

  def nearCallback(self, args, geom1, geom2):
    contacts = ode.collide(geom1, geom2)
    
    for c in contacts:
      c.setBounce(0.2)
      c.setMu(5000)
      j = ode.ContactJoint(self.world, self.contactGroup, c)
      j.attach(geom1.getBody(), geom2.getBody())

  def handleActorCreated(self, sender, id, owner, name):
    actor = globals()[name](self, owner)
    self.objects[id] = actor
    self.actors.append(actor)

  def handleActorDeleted(self, sender, id):
    actor = self.objects[id]
    self.actors.remove(actor)
    del self.objects[id]

class SceneClient(Scene, KeyListener):
  def __init__(self, engine, owner, session, **args):
    Scene.__init__(self, engine, owner, **args)
    self.session = session
    self.player = self.session.world.getLocalPlayer()
    self.player2 = self.session.world.getPlayer2()
    self.controls = Player.Controls()
    self.createClient(**args)

  def createClient(self, **args):
    pass

  def createActor(self, name):
    self.session.sendMessage(CreateActor(name = name))

  def shown(self):
    self.engine.input.addKeyListener(self)

  def hidden(self):
    self.engine.input.removeKeyListener(self)

  def keyPressed(self, key, unicode):
    c = self.controls.keyPressed(key)
    if c:
      self.session.sendMessage(ControlEvent(flags = self.controls.flags))
      return True
    return False

  def keyReleased(self, key):
    c = self.controls.keyReleased(key)
    if c:
      self.session.sendMessage(ControlEvent(flags = self.controls.flags))
      return True
    return False

  def handleControlData(self, sender, owner, flags):
    # TODO: player mapping
    for player in self.session.world.players:
      if player.owner == owner:
        player.controls.flags = flags
        break

  def handleActorData(self, sender, id, data):
    actor = self.objects[id]
    actor.setState(*data)

  def run(self, ticks):
    self.runCommon(ticks, self.session.world)
    Scene.run(self, ticks)
    
  def render3D(self):
    for actor in self.actors:
      actor.render()

  def render(self, visibility, topMost):
    font = self.engine.data.font

    # render the scene
    try:
      glMatrixMode(GL_PROJECTION)
      glPushMatrix()
      glLoadIdentity()
      gluPerspective(60, self.engine.view.aspectRatio, 0.1, 1000)
      glMatrixMode(GL_MODELVIEW)
      glLoadIdentity()
      
      glPushMatrix()
      self.camera.apply()
  
      self.render3D()
    finally:
      glPopMatrix()
      glMatrixMode(GL_PROJECTION)
      glPopMatrix()
      glMatrixMode(GL_MODELVIEW)

class SceneServer(Scene):
  def __init__(self, engine, owner, server, **args):
    Scene.__init__(self, engine, owner, **args)
    self.server = server
    self.updateInterval = self.engine.config.get("network", "updateinterval")
    self.updateCounter = 0
    self.changedControlData = {}

  def handleControlEvent(self, sender, flags):
    self.changedControlData[sender] = flags

  def handleControlData(self, sender, owner, flags):
    # TODO: player mapping
    for player in self.server.world.players:
      if player.owner == owner:
        player.controls.flags = flags
        break

  def handleCreateActor(self, sender, name):
    id = self.objects.generateId()
    self.server.broadcastMessage(ActorCreated(owner = sender, name = name, id = id))

  def handleSessionClosed(self, session):
    for actor in self.actors:
      if actor.owner == session.id:
        id = self.objects.id(actor)
        self.server.broadcastMessage(ActorDeleted(id = id))

  def handleSessionOpened(self, session):
    for actor in self.actors:
      id = self.objects.id(actor)
      session.sendMessage(ActorCreated(owner = actor.owner, name = actor.__name__, id = id))

  def broadcastState(self):
    for actor in self.actors:
      id = self.objects.id(actor)
      self.server.broadcastMessage(ActorData(id = id, data = actor.getState()), meToo = False)

    for sender, flags in self.changedControlData.items():
      self.server.broadcastMessage(ControlData(owner = sender, flags = flags))
    self.changedControlData = {}

  def run(self, ticks):
    self.runCommon(ticks, self.server.world)
    Scene.run(self, ticks)

    self.updateCounter += ticks
    if self.updateCounter > self.updateInterval:
      self.updateCounter %= self.updateInterval
      self.broadcastState()
