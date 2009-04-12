#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire                                                     #
# Copyright (C) 2009 Vlad Emelyanov                                 #
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

from OpenGL.GL.ARB.shader_objects import *
from OpenGL.GL.ARB.vertex_shader import *
from OpenGL.GL.ARB.fragment_shader import *

from OpenGL.GL import *

import os
import sys
import string
import random
import time
import Log

class shaderList:
  def __init__(self, dir = ""):
    self.shaders = {}
    self.backup = {}
    self.active = 0
    self.texcount = 0
    self.lastcompiled = ""
    self.noise3D = 0
    self.noise2D = 0
    self.noise1D = 0
    self.workdir = ""
    self.enabled = False
    self.var = {}
    time.clock()
    self.build(dir)
    self.reset()
    
  def build(self,dir = ""):
    if dir == "": return False
    try:
      names = os.listdir(dir)
    except (IOError, os.error), why:
      print u"Error: %s " % (why)
      raw_input()
      sys.exit()
    for name in names:
      fullname = os.path.join(dir, name)
      if name[-3:] == ".ps":
        program = self.compile(open(fullname[:-3]+".vs"), open(fullname))
        sArray = {"program": program, "name": name[:-3], "tex" : (), "textype" : ()}
        self.lastCompiled = name[:-3]
        self.getVars(fullname, program, sArray)
        self.getVars(fullname[:-3]+".vs", program, sArray)
        self.shaders[name[:-3]] = sArray
    if self.shaders!={}:
      return True
    else:
      return False
      
  def make(self,fname = "", name = ""):
    if fname == "": return False
    if name == "": name = fname
    fullname = os.path.join(self.workdir, fname)
    Log.debug("Compiling " + fname + " shader.")
    try:
      program = self.compile(open(fullname+".vs"), open(fullname+".ps"))
      sArray = {"program": program, "name": name, "tex" : (), "textype" : ()}
      self.lastCompiled = name
      self.getVars(fullname+".vs", program, sArray)
      self.getVars(fullname+".ps", program, sArray)
      self.shaders[name] = sArray
    except:
      Log.error("Error occured during compilation.")
      return False
    else:

      return True

          
  def compileShader(self, source, shaderType):
    """Compile shader source of given type"""
    shader = glCreateShaderObjectARB(shaderType)
    #print "glShaderSourceARB:", bool(glShaderSourceARB)
    glShaderSourceARB( shader, source )
    glCompileShaderARB( shader )
    return shader
    
  def getVars(self,fname, program, sArray):
    for line in open(fname):
      aline = line[:string.find(line,";")]
      aline = aline.split(' ')
      if '(' in aline[0]:
        break;
      if aline[0] == "uniform":
        value = None
        try:    n = int(aline[1][-1])
        except: n = 4
        if   aline[1] == "bool": value = False
        elif aline[1] == "int": value = 0
        elif aline[1] == "float": value = 0.0 
        elif aline[1][:-1] == "bvec": value = (False,)*n
        elif aline[1][:-1] == "ivec": value = (0,)*n
        elif aline[1][:-1] == "vec": value = (.0,)*n
        elif aline[1][:-1] == "mat": value = ((.0,)*n,)*n
        elif aline[1][:-2] == "sampler": 
          value, self.texcount = self.texcount, self.texcount + 1 
          if aline[1] == "sampler1D":   sArray["textype"] += (GL_TEXTURE_1D,)
          elif aline[1] == "sampler2D": sArray["textype"] += (GL_TEXTURE_2D,)
          elif aline[1] == "sampler3D": sArray["textype"] += (GL_TEXTURE_3D,)
        aline[2] = aline[2].split(',')
        for var in aline[2]:
          sArray[var] = [glGetUniformLocationARB(program, var), value]
    
    
  def compile(self, vertexSource=None, fragmentSource=None):
    program = glCreateProgramObjectARB()
  
    if vertexSource:
      vertexShader = self.compileShader(vertexSource, GL_VERTEX_SHADER_ARB)
      glAttachObjectARB(program, vertexShader)
    if fragmentSource:
      fragmentShader = self.compileShader(fragmentSource, GL_FRAGMENT_SHADER_ARB)
      glAttachObjectARB(program, fragmentShader)
    
    glValidateProgramARB( program )
    glLinkProgramARB(program)
    if vertexShader: glDeleteObjectARB(vertexShader)
    if fragmentShader: glDeleteObjectARB(fragmentShader)
    return program
    
  def getVar(self, var = "program", program = None):
    if program == None: program = self.active
    else: program = self[program]
    if program != 0:
      return program[var][1]
    
  def setVar(self, var, value, program = None):
    if program == None:  program = self.active
    else: program = self[program]
    
    if type(value) == str:
      value = self.var[value]
    
    if program != 0 and program.has_key(var):
      pos = program[var]
      pos[1] = value
      if program == self.active and program != 0:
        try:
          if type(value) == bool:
            if pos[1]: glUniform1i(pos[0],1)
            else: glUniform1i(pos[0],0)
          if type(value) == float:
            glUniform1f(pos[0],pos[1])
          elif type(value) == int:
            glUniform1i(pos[0],pos[1])
          elif type(value) == tuple:
            if type(value[0]) == float:
              if   len(value) == 2: glUniform2f(pos[0],*pos[1])
              elif len(value) == 3: glUniform3f(pos[0],*pos[1])
              elif len(value) == 4: glUniform4f(pos[0],*pos[1])
            elif type(value[0]) == int:
              if   len(value) == 2: glUniform2i(pos[0],*pos[1])
              elif len(value) == 3: glUniform3i(pos[0],*pos[1])
              elif len(value) == 4: glUniform4i(pos[0],*pos[1])
          elif type(value) == long:
            glUniform1i(pos[0],pos[1])
        except:
          return False
        else:
          return True
    return False
    
  def modVar(self, var, value, effect = 0.05, alphaAmp=1.0, program = None):  
    old = self.getVar(var,program)
    if type(old) == tuple:
      new = ()
      for i in range(len(old)):
        if i==3: new += (old[i] * (1-effect) + value[i] * effect*alphaAmp,)
        else: new += (old[i] * (1-effect) + value[i] * effect,)
    else:
      new = old * (1-effect) + value * effect
    self.setVar(var,new,program)
        
  def enable(self, shader):
    try:
      glUseProgramObjectARB(self[shader]["program"])
      self.active = self.shaders[shader]
      self.setTextures()
      self.setVar("time",self.time())
      self.update()
      return True
    except:
      return False
          
  def update(self):
    for i in self.active.keys():
      if type(self.active[i]) == type([]) and self.active[i][1] != None:
        self.setVar(i,self.active[i][1])
    
  def disable(self):
    if self.active !=0:
      glUseProgramObjectARB(0)
      self.active = 0
    
  def turnOff(self):
    if self.backup == {} and self.shaders != {}:
      self.backup = self.shaders
      self.shaders = {}
      
  def turnOn(self):
    if self.backup != {} and self.shaders == {}:
      self.shaders = self.backup
      self.backup = {}
    
  def activeProgram(self):
    if self.active !=0:
      return self.active["name"]
    else:
      return 0  
    
  def log(self):
    infologLength = 0
    charsWritten = 0
    obj = self[self.lastCompiled]["program"]
    glGetObjectParameterivARB(obj, GL_OBJECT_INFO_LOG_LENGTH_ARB, infologLength)
    glGetInfoLogARB(obj, infologLength, charsWritten, infoLog)
    return infoLog
    
  def setTextures(self, program = None):
    if program == None: program = self.active
    j = 0
    if type(program["tex"]) == tuple:
      for i in program["tex"]:
        if len(program["tex"]) > 1 and multiTex[j] != 0:
          glActiveTexture (multiTex[j])
        glBindTexture(program["textype"][j], i) 
        j += 1
    else:
      print type(program["tex"])
      glBindTexture(program["textype"][0], program["tex"]) 
      
  def makeNoise3D(self,size=32, c = 1, type = GL_RED):
    texels=[]
    for i in range(size):
      arr2 = []
      for j in range(size):
        arr = []
        for k in range(size):
          arr.append(random.random())
        arr2.append(arr)
      texels.append(arr2)
          
    self.smoothNoise3D(size, 2, texels)
    #self.smoothNoise3D(size, 4, texels)
    
    for i in range(size):
      for j in range(size):
        for k in range(size):
          texels[i][j][k] = int(255 * texels[i][j][k])

    texture = 0
    glBindTexture(GL_TEXTURE_3D, texture)
    glTexParameterf(GL_TEXTURE_3D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameterf(GL_TEXTURE_3D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameterf(GL_TEXTURE_3D, GL_TEXTURE_WRAP_R, GL_REPEAT)
    glTexParameterf(GL_TEXTURE_3D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameterf(GL_TEXTURE_3D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexImage3D(GL_TEXTURE_3D, 0, c,size, size, size, 0, type, GL_UNSIGNED_BYTE, texels)
    return texture
    
  def makeNoise2D(self,size=64, c = 1, type = GL_RED):
    texels=[]
    for i in range(size):
      texels.append([])
      for j in range(size):
        texels[i].append(random.random())
    
    self.smoothNoise(size, 2, texels)
    self.smoothNoise(size, 3, texels)
    self.smoothNoise(size, 4, texels)  
    
    for i in range(size):
      for j in range(size):
        texels[i][j] = int(255 * texels[i][j])
        
    texture = 0
    glBindTexture(GL_TEXTURE_2D, texture)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_R, GL_REPEAT)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, c,size, size, 0, type, GL_UNSIGNED_BYTE, texels)
    return texture
    
  def loadTex3D(self, fname, type = GL_RED):
    try:
      noise = open(os.path.join(self.workdir,fname)).read()
      size = int(len(noise)**(1/3.0))
    except:
      print "noise"
      return self.makeNoise3D(16)
    #print noise
          
    #self.smoothNoise3D(size, 2, texels)
    #self.smoothNoise3D(size, 4, texels)
    

    texture = 0
    glBindTexture(GL_TEXTURE_3D, texture)
    glTexParameterf(GL_TEXTURE_3D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameterf(GL_TEXTURE_3D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameterf(GL_TEXTURE_3D, GL_TEXTURE_WRAP_R, GL_REPEAT)
    glTexParameterf(GL_TEXTURE_3D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameterf(GL_TEXTURE_3D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexImage3D(GL_TEXTURE_3D, 0, 1,size, size, size, 0, type, GL_UNSIGNED_BYTE, noise)
    return texture
    
  def smoothNoise(self, size, c, noise):
    for x in range(size):
      for y in range(size):
        col1 = noise[x][y]
        col2 = noise[size/2/(1-c)+x/c][size/2/(1-c)+y/c]
        noise[x][y] = (1-1/float(c))*col1+1/float(c)*col2
    
  def smoothNoise3D(self, size, c, noise):
    for i in range(size):
      for j in range(size):
        for k in range(size):
          col1 = noise[i][j][k]
          col2 = noise[size/2/(1-c)+i/c][size/2/(1-c)+j/c][size/2/(1-c)+k/c]
          noise[i][j][k] = (1-1/float(c))*col1+1/float(c)*col2
      
  def __getitem__(self, name):
    if self.shaders.has_key(name):
      return self.shaders[name]
    else:
      return 0
      
  def time(self):
    return time.clock()
    
  def reset(self):
    self.var["color"]=(0.0,)*4      #color for guitar neck flashing
    self.var["drumcolor"]=(0.0,)*4  #color for drum neck flashing
    self.var["solocolor"]=(0.0,)*4  #color for GH3 solo lightnings
    self.var["eqcolor"]=(0.0,)*4    #color for equalizer
    self.var["drum"]=[-10.0]*5      #last fret note hit time
    self.var["fret"]=[-10.0]*5      #last drum note hit time

    
  def set(self, dir):
    self.enabled = True
    self.workdir = dir
    self.noise3D = self.loadTex3D("noise3d.dds")
    try:
      multiTex = (GL_TEXTURE0_ARB,GL_TEXTURE1_ARB,GL_TEXTURE2_ARB,GL_TEXTURE3_ARB)
    except:
      multiTex = (0,0,0,0)
      Log.error("Multitexturing failed. Upgrade to PyOpenGL 3.00!")  
    
    if self.make("lightning","stage"):
      self.enable("stage")
      self["stage"]["tex"]=(self.noise3D,)
      self.setVar("ambientGlowHeightScale",6.0)
      self.setVar("color",(0.0,0.0,0.0,0.0))
      self.setVar("glowFallOff",0.024)
      self.setVar("height",0.44)
      self.setVar("sampleDist",0.0076)
      self.setVar("speed",1.86)
      self.setVar("vertNoise",0.78)
      self.setVar("fading",1.0)
      self.setVar("solofx",False)
      self.setVar("scalexy",(1.6,1.2))
      self.setVar("fixalpha",True)
      self.setVar("offset",(0.0,-2.5))
      self.disable()
    else:
      Log.error("Shader has not been compiled: lightning")  
      
    if self.make("lightning","sololight"):
      self.enable("sololight")
      self["sololight"]["tex"]=(self.noise3D,)
      self.setVar("scalexy",(5.0,1.0))
      self.setVar("ambientGlow",0.5)
      self.setVar("ambientGlowHeightScale",6.0)
      self.setVar("solofx",True)
      self.setVar("height",0.3)
      self.setVar("glowFallOff",0.024)
      self.setVar("sampleDist",0.0076)
      self.setVar("fading",4.0)
      self.setVar("speed",1.86)
      self.setVar("vertNoise",0.78)
      self.setVar("solofx",True)
      self.setVar("color",(0.0,0.0,0.0,0.0))
      self.setVar("fixalpha",True)
      self.setVar("glowStrength",100.0)  
      self.disable()
    else:
      Log.error("Shader has not been compiled: lightning")  
      
    if self.make("lightning","tail"):
      self.enable("tail")
      self["tail"]["tex"]=(self.noise3D,)
      self.setVar("scalexy",(5.0,1.0))
      self.setVar("ambientGlow",0.1)
      self.setVar("ambientGlowHeightScale",6.0)
      self.setVar("solofx",True)
      self.setVar("fading",4.0)
      self.setVar("height",0.3)
      self.setVar("glowFallOff",0.024)
      self.setVar("sampleDist",0.0076)
      self.setVar("speed",1.86)
      self.setVar("vertNoise",0.78)
      self.setVar("solofx",True)
      self.setVar("color",(0.3,0.7,0.9,0.6))
      self.setVar("glowStrength",150.0) 
      self.setVar("fixalpha",True)
      self.setVar("offset",(0.0,0.0)) 
      self.disable()
    else:
      Log.error("Shader has not been compiled: lightning")  
      
    if not self.make("neck","neck"):
      Log.error("Shader has not been compiled: neck") 
    
    if not self.make("cd","cd"):
      Log.error("Shader has not been compiled: cd")  
  
multiTex = None
list = shaderList()