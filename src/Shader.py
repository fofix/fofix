from OpenGL.GL.ARB.shader_objects import *
from OpenGL.GL.ARB.vertex_shader import *
from OpenGL.GL.ARB.fragment_shader import *
from OpenGL.GL.ARB.multisample import *

from OpenGL.GL import *
from OpenGL.GLU import *

import os
import sys

multiTex = None

class shaderList:
  def __init__(self, dir = ""):
    self.shaders = {}
    self.textures = []
    self.active = 0
    self.texcount = 0
    self.build(dir)
    
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
        sArray = {"program": program, "name": name[:-3], "tex" : ()}
        self.getVars(fullname, program, sArray)
        self.getVars(fullname[:-3]+".vs", program, sArray)
        self.shaders[name[:-3]] = sArray
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
      aline = line.split(" ")
      if aline[0] == "uniform":
        aline[2] = aline[2][:-2]
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
        elif aline[1][:-2] == "sampler": value, self.texcount = self.texcount, self.texcount + 1
        sArray[aline[2]] = [glGetUniformLocationARB(program, aline[2]), value]
    
    
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
    
  def setVar(self, var, value, Mod = False, program = None):
    if program == None:  program = self.active
    else: program = self[program]
    if program != 0:
      pos = program[var]
      if Mod: pos[1] += value
      else:   pos[1] = value
    
      if program == self.active and program != 0:
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
        
  def enable(self, shader):
    if self.shaders.has_key(shader):
      glUseProgramObjectARB(self[shader]["program"])
      self.active = dict(self.shaders[shader])
      #self.setTextures()
      return True
    else:
      return False
          
  def update(self):
    for i in self.active.keys():
      if type(self.active[i]) == type([]) and self.active[i][1] != None:
        self.setVar(i,self.active[i][1])
    
  def disable(self):
    glUseProgramObjectARB(0)
    self.active = 0
    
  def enabled(self):
    if self.active !=0:
      return self.active["name"]
    else:
      return 0  
    
  def log(self,shader):
    infologLength = 0
    charsWritten = 0
    obj = self[shader]["program"]
    glGetObjectParameterivARB(obj, GL_OBJECT_INFO_LOG_LENGTH_ARB, infologLength)
    glGetInfoLogARB(obj, infologLength, charsWritten, infoLog)
    return infoLog
    
  def setTextures(self, program = None):
    if program == None: program = self.active
    j = 0
    for i in program["tex"]:
      glActiveTexture (multiTex[j])
      glBindTexture(GL_TEXTURE_2D, i.texture) 
      j += 1
      
  def __getitem__(self, name):
    if self.shaders.has_key(name):
      return self.shaders[name]
    else:
      return 0
    
list = shaderList()