# -------------------------------------------------------------------------
# Illusoft Collada 1.4 plugin for Blender version 0.3.89
# --------------------------------------------------------------------------
# ***** BEGIN GPL LICENSE BLOCK *****
#
# Copyright (C) 2006: Illusoft - colladablender@illusoft.com
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License,
# or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****
# --------------------------------------------------------------------------

from xml.dom.minidom import *
from datetime import *

# The number of decimals to export floats to
ROUND = 5

#---Functions----

angleToRadian = 3.1415926 / 180.0
radianToAngle = 180.0 / 3.1415926

# Convert a string to a float if the value exists
def ToFloat(val):
	if val is None or val == '':
		return None
	else:
		return float(val)

# Convert a string to a int if the value exists
def ToInt(val):
	if val is None or val == '':
		return None
	else:
		return int(val)
	
# Convert a string to a list of 3 floats e.g '1.0 2.0 3.0' -> [1.0, 2.0, 3.0]
def ToFloat3(stringValue):
	if stringValue is None:
		return None
	split = stringValue.split( )
	return [ float( split[ 0 ] ), float( split[ 1 ] ), float( split[ 2 ] ) ]

# Convert a string to a list of 2 floats e.g '1.0 2.0' -> [1.0, 2.0]
def ToFloat2(stringValue, errorText=''):
	if stringValue is None:
		return None
	split = stringValue.split( )
	try:
		return [ float( split[ 0 ] ), float( split[ 1 ] )]
	except IndexError:
		print 'Error: ' + errorText
		raise

def ToList(var):
	result = []
	if var is None:
		return result
	
	split = var.split( )
	for i in split:
		result.append(i)
	return result
	
# Convert a string or list to a list of floats
def ToFloatList(var):
	result = []
	if var is None:
		return result
		
	if type(var) == list:
		for i in var:
			result.append(float(i))
	else:	 
		split = var.split( )
		for i in split:
			result.append(float(i))
	return result

def ToIntList(lst):
	result = []
	if lst is None:
		return result
	if type(lst) == list:
		for i in lst:
			result.append(int(i))
	else:
		split = lst.split( )		
		for i in split:
			result.append(int(i))
	return result

def ToBoolList(lst):
	result = []
	if lst is None:
		return result
	for i in lst:
		result.append(bool(i))
	return result

# Convert a string to a list of 4 floats e.g '1.0 2.0 3.0 4.0' -> [1.0, 2.0, 3.0, 4.0]
def ToFloat4(stringValue):
	split = stringValue.split( )
	return [ float( split[ 0 ] ), float( split[ 1 ] ), float( split[ 2 ] ) , float( split[3])]

def ToFloat7(stringValue):
	data = stringValue.split( )
	return [ float(data[0]), float(data[1]), float(data[2]), float(data[3]), float(data[4]), float(data[5]), float(data[6])]

def AddVec3( vector1, vector2 ):
	vector1.x += vector2.x
	vector1.y += vector2.y
	vector1.z += vector2.z

def ToMatrix4( matrixElement ):
	data = matrixElement.split( )
	
	vec1 = [ float(data[0]), float(data[4]), float(data[8]), float(data[12]) ]
	vec2 = [ float(data[1]), float(data[5]), float(data[9]), float(data[13]) ]
	vec3 = [ float(data[2]), float(data[6]), float(data[10]), float(data[14]) ]
	vec4 = [ float(data[3]), float(data[7]), float(data[11]), float(data[15]) ]
	
	return [ vec1, vec2, vec3, vec4 ]

def ToMatrix3(matrixElement):
	data = matrixElement.split( )
	
	vec1 = [ float(data[0]), float(data[3]), float(data[6]) ]
	vec2 = [ float(data[1]), float(data[4]), float(data[7])]
	vec3 = [ float(data[2]), float(data[5]), float(data[8])]
	
	return [ vec1, vec2, vec3 ]
	
def GetVector3( element ):
	value = [ float( element[ 0 ] ), float( element[ 1 ] ), float( element[ 2 ] ) ]
	return value

def GetEuler( rotateElement ):
	euler = [ float( rotateElement[ 0 ] ) * float( rotateElement[ 3 ] ) * angleToRadian,
			  float( rotateElement[ 1 ] ) * float( rotateElement[ 3 ] ) * angleToRadian,
			  float( rotateElement[ 2 ] ) * float( rotateElement[ 3 ] ) * angleToRadian ]
	return euler

def AddEuler(euler1, euler2):
	euler1.x += euler2.x
	euler1.y += euler2.y
	euler1.z += euler2.z
	
def MatrixToString(mat, nDigits):
	result = ''
	if mat is None:
		return result
	
	for vec in mat:
		result += '\n\t'
		for i in vec:
			result += str(round(i, nDigits))+' '
		
	return result+'\n'
			
def RoundList(lst, nDigits):
	result = []
	for i in lst:
		result.append(round(i, nDigits))
	return result
		

def ListToString(lst):
	val  = ''
	if lst is None:
		return val
	else:
		for i in lst:
			if type(i) == list:
				val += ListToString(i)+'\n'
			else:
				val += str(i)+' '
		return val[:-1]

#---XML Utils---

# Returns the first child of the specified type in node
def FindElementByTagName(parentNode, type):
	child = parentNode.firstChild
	while child != None:
		if child.localName == type:
			return child
		child = child.nextSibling
##	  childs = parentNode.getElementsByTagName(type)
##	  if len(childs) > 0:
##		  return childs[0]
	return None

def FindElementsByTagName(parentNode, type):
	result = []
	child = parentNode.firstChild
	while child != None:
		if child.localName == type:
			result.append(child)
		child = child.nextSibling
	return result

def ReadAttribute(node,attributeName):
	if node != None and attributeName != None:
		attribute = node.getAttribute(attributeName)
		return attribute		
	return None

def ReadContents(node):
	if node != None:
		child = node.firstChild
		if child != None and child.nodeType == child.TEXT_NODE:
			return child.nodeValue
	return None

def ReadDateTime(node):
	if node == None:
		return None
	return GetDateTime(ReadContents(node))

def RemoveWhiteSpace(parent):	 
	for child in list(parent.childNodes):
		if child.nodeType==child.TEXT_NODE and child.data.strip()=='':
			parent.removeChild(child)
		else:
			RemoveWhiteSpace(child)

def RemoveWhiteSpaceNode(parent):
	for child in list(parent.childNodes):
		if child.nodeType == child.TEXT_NODE and child.data.strip()=='':
			parent.removeChild(child)
	return parent
			
##def RemoveWhiteSpace(node):
##	  removeList = []
##	  for child in node.childNodes:
##		  if child.nodeType == child.TEXT_NODE and not child.data.strip():
##			  removeList.append(child)
##		  elif child.hasChildNodes():
##			  RemoveWhiteSpace(child)
##	  
##	  for node in removeList:
##		  node.parentNode.removeChild(node)

def GetDateTime(xmlvalue):
  return xmlvalue
	#vals = xmlvalue.split('T')
	#datestr = vals[0]
	#timestr =  vals[1]
	#date = datestr.split('-')
	#time = timestr.split(':')
	#time[2]=time[2].rstrip('Z')    
	#return datetime(int(date[0]), int(date[1]), int(date[2]),int(time[0]), int(time[1]), int(float(time[2])))

def ToDateTime(val):
  return val
	#return '%s-%s-%sT%s:%s:%sZ'%(val.year,str(val.month).zfill(2),str(val.day).zfill(2), str(val.hour).zfill(2), str(val.minute).zfill(2),str(val.second).zfill(2))

def GetStringArrayFromNodes(xmlNodes):
	vals = []
	if xmlNodes == None:
		return vals
	for xmlNode in xmlNodes:
		stringvals = ReadContents(xmlNode).split( )
		for string in stringvals:
			vals.append(string) 		   
	return vals

def GetListFromNodes(xmlNodes, cast=None):
	result = []
	if xmlNodes is None:
		return result
	
	for xmlNode in xmlNodes:
		val = ReadContents(xmlNode).split( )
		if cast == float:
			val = ToFloatList(val)
		elif cast == int:
			val = ToIntList(val)
		elif cast == bool:
			val = ToBoolList(val)
		result.append(val)
	return result			 
		

def ToXml(xmlNode, indent='\t', newl='\n'):
	return '<?xml version="1.0" encoding="utf-8"?>\n%s'%(__ToXml(xmlNode, indent,newl))
	
def __ToXml(xmlNode, indent='\t',newl='\n',totalIndent=''):
	childs = xmlNode.childNodes
	if len(childs) > 0:
		attrs = ''
		attributes = xmlNode.attributes
		if attributes != None:
			for attr in attributes.keys():
				val = attributes[attr].nodeValue
				attrs += ' %s="%s"'%(attr,val)
		result = '%s<%s%s>'%(totalIndent,xmlNode.localName,attrs)
		tempnewl = newl
		tempTotIndent = totalIndent
		for child in childs:			
			if child.nodeType == child.TEXT_NODE:
				tempnewl = ''
				tempTotIndent = ''
			
			result += '%s%s'%(tempnewl,__ToXml(child, indent, newl, totalIndent+indent))
		result += '%s%s</%s>'%(tempnewl,tempTotIndent,xmlNode.localName)
		return result
	else:
		if xmlNode.nodeType == xmlNode.TEXT_NODE:
			return xmlNode.toxml().replace('\n','\n'+totalIndent[:-1])
		else:
			return totalIndent+xmlNode.toxml()

def AppendChilds(xmlNode, syntax, lst):
	if lst is None or syntax is None or xmlNode is None:
		return
	
	for i in lst:
		el = Element(syntax)
		text = Text()
		text.data = ListToString(i)
		el.appendChild(text)
		xmlNode.appendChild(el)
	
	return xmlNode		
		
# TODO: Collada API: finish DaeDocument
class DaeDocument(object):
	
	def __init__(self, debugM = False):
		global debugMode
		debugMode = debugM
		
		self.colladaVersion = '1.4.0'
		self.version = ''
		self.xmlns = ''
		self.asset = DaeAsset()
		self.extras = []
		
		
		# create all the libraries
		self.animationsLibrary = DaeLibrary(DaeSyntax.LIBRARY_ANIMATIONS,DaeAnimation,DaeSyntax.ANIMATION)
		self.animationClipsLibrary = DaeLibrary(DaeSyntax.LIBRARY_ANIMATION_CLIPS,DaeAnimationClip,DaeSyntax.ANIMATION_CLIP)
		self.camerasLibrary = DaeLibrary(DaeSyntax.LIBRARY_CAMERAS,DaeCamera,DaeSyntax.CAMERA)
		self.controllersLibrary = DaeLibrary(DaeSyntax.LIBRARY_CONTROLLERS,DaeController,DaeSyntax.CONTROLLER)
		self.effectsLibrary = DaeLibrary(DaeSyntax.LIBRARY_EFFECTS,DaeFxEffect,DaeFxSyntax.EFFECT)
		self.geometriesLibrary = DaeLibrary(DaeSyntax.LIBRARY_GEOMETRIES,DaeGeometry,DaeSyntax.GEOMETRY)
		self.imagesLibrary = DaeLibrary(DaeSyntax.LIBRARY_IMAGES, DaeImage, DaeSyntax.IMAGE)
		self.lightsLibrary = DaeLibrary(DaeSyntax.LIBRARY_LIGHTS,DaeLight,DaeSyntax.LIGHT)
		self.materialsLibrary = DaeLibrary(DaeSyntax.LIBRARY_MATERIALS,DaeFxMaterial,DaeFxSyntax.MATERIAL)
		self.nodesLibrary = DaeLibrary(DaeSyntax.LIBRARY_NODES, DaeNode, DaeSyntax.NODE)
		self.visualScenesLibrary = DaeLibrary(DaeSyntax.LIBRARY_VISUAL_SCENES,DaeVisualScene,DaeSyntax.VISUAL_SCENE)
		
		# Physics Support
		self.physicsMaterialsLibrary = DaeLibrary(DaeSyntax.LIBRARY_PHYSICS_MATERIALS, DaePhysicsMaterial, DaePhysicsSyntax.PHYSICS_MATERIAL)		 
		self.physicsScenesLibrary = DaeLibrary(DaeSyntax.LIBRARY_PHYSICS_SCENES, DaePhysicsScene, DaePhysicsSyntax.PHYSICS_SCENE)		 
		
		self.physicsModelsLibrary = DaeLibrary(DaeSyntax.LIBRARY_PHYSICS_MODELS, DaePhysicsModel, DaePhysicsSyntax.PHYSICS_MODEL)
				
		self.scene = None
		self.physicsScene = None
		
	def LoadDocumentFromFile(self, filename):
		global debugMode
		# Build DOM tree
		doc = parse( filename )
		
		# Get COLLADA element
		colladaNode = doc.documentElement	 
				
		# Get Attributes		
		self.version = colladaNode.getAttribute(DaeSyntax.VERSION)
		#if not IsVersionOk(self.version, self.colladaVersion):
		#	Debug.Debug('The version of the file (%s) is older then the version supported by this plugin(%s).'%(self.version, self.colladaVersion),'ERROR')
		#	doc.unlink()
		#	return 
		self.xmlns = colladaNode.getAttribute(DaeSyntax.XMLNS)
		
		# get the assets element
		self.asset.LoadFromXml(self,FindElementByTagName(colladaNode,DaeSyntax.ASSET))
		
		# get the extra elements
		self.extras = CreateObjectsFromXml(self,colladaNode,DaeSyntax.EXTRA,DaeExtra)
				
		# parse all the libraries
		self.imagesLibrary.LoadFromXml(self,FindElementByTagName(colladaNode,DaeSyntax.LIBRARY_IMAGES))
		self.animationsLibrary.LoadFromXml(self, FindElementByTagName(colladaNode,DaeSyntax.LIBRARY_ANIMATIONS))
		self.animationClipsLibrary.LoadFromXml(self,FindElementByTagName(colladaNode,DaeSyntax.LIBRARY_ANIMATION_CLIPS))
		self.camerasLibrary.LoadFromXml(self,FindElementByTagName(colladaNode,DaeSyntax.LIBRARY_CAMERAS))
		self.controllersLibrary.LoadFromXml(self,FindElementByTagName(colladaNode,DaeSyntax.LIBRARY_CONTROLLERS))
		self.effectsLibrary.LoadFromXml(self,FindElementByTagName(colladaNode,DaeSyntax.LIBRARY_EFFECTS))
		self.geometriesLibrary.LoadFromXml(self,FindElementByTagName(colladaNode,DaeSyntax.LIBRARY_GEOMETRIES))
		self.lightsLibrary.LoadFromXml(self, FindElementByTagName(colladaNode, DaeSyntax.LIBRARY_LIGHTS))
		self.materialsLibrary.LoadFromXml(self,FindElementByTagName(colladaNode,DaeSyntax.LIBRARY_MATERIALS))
		self.nodesLibrary.LoadFromXml(self,FindElementByTagName(colladaNode,DaeSyntax.LIBRARY_NODES))
		self.visualScenesLibrary.LoadFromXml(self, FindElementByTagName(colladaNode, DaeSyntax.LIBRARY_VISUAL_SCENES))
		
		self.physicsMaterialsLibrary.LoadFromXml(self, FindElementByTagName(colladaNode, DaeSyntax.LIBRARY_PHYSICS_MATERIALS))
		self.physicsModelsLibrary.LoadFromXml(self, FindElementByTagName(colladaNode, DaeSyntax.LIBRARY_PHYSICS_MODELS))
		self.physicsScenesLibrary.LoadFromXml(self, FindElementByTagName(colladaNode, DaeSyntax.LIBRARY_PHYSICS_SCENES))
		
		# Get the sceneNodes
		sceneNodes = colladaNode.getElementsByTagName(DaeSyntax.SCENE)
		
		# Get the scene
		sceneNode = FindElementByTagName(colladaNode, DaeSyntax.SCENE)
		if sceneNode != None:
			scene = DaeScene()
			scene.LoadFromXml(self, sceneNode)
			self.scene = scene
			
		doc.unlink()
		
		if debugMode:
			Debug.Debug('Directly exporting this DaeDocument...','DEBUG')
			self.SaveDocumentToFile(filename+'_out.dae')
			
	def SaveDocumentToFile(self, filename):
		self.version = '1.4.0'
		self.xmlns = 'http://www.collada.org/2005/11/COLLADASchema'
		colladaNode = Element(DaeSyntax.COLLADA)
		colladaNode.setAttribute(DaeSyntax.VERSION, self.version)
		colladaNode.setAttribute(DaeSyntax.XMLNS, self.xmlns)
		
		colladaNode.appendChild(self.asset.SaveToXml(self))
		
		# add the labraries
		AppendChild(self,colladaNode,self.animationsLibrary)
		AppendChild(self,colladaNode,self.animationClipsLibrary)
		AppendChild(self,colladaNode,self.camerasLibrary)
		AppendChild(self,colladaNode,self.controllersLibrary)
		AppendChild(self,colladaNode,self.effectsLibrary)
		AppendChild(self,colladaNode,self.geometriesLibrary)
		AppendChild(self,colladaNode,self.imagesLibrary)
		AppendChild(self,colladaNode,self.lightsLibrary)
		AppendChild(self,colladaNode,self.materialsLibrary)
		AppendChild(self,colladaNode,self.nodesLibrary)
		AppendChild(self,colladaNode,self.visualScenesLibrary)
		AppendChild(self,colladaNode,self.physicsMaterialsLibrary)
		AppendChild(self,colladaNode,self.physicsModelsLibrary)
		AppendChild(self,colladaNode,self.physicsScenesLibrary) 	   
		
		AppendChild(self,colladaNode,self.scene)
		
		# write xml to the file
		fileref = open(filename, 'w')
		fileref.write(ToXml(colladaNode))
		fileref.flush()
		fileref.close()
		colladaNode.unlink()
	
	def GetItemCount(self):
		return (##self.animationClipsLibrary.GetItemCount()+
	##self.animationsLibrary.GetItemCount()+
	##self.camerasLibrary.GetItemCount()+
	##self.controllersLibrary.GetItemCount()+
	##self.effectsLibrary.GetItemCount()+
	self.geometriesLibrary.GetItemCount()+
	self.lightsLibrary.GetItemCount()+
	##self.materialsLibrary.GetItemCount()+
	self.nodesLibrary.GetItemCount()##+
	##self.visualScenesLibrary.GetItemCount()
	)
	
	def __str__(self):
		return '%s version: %s, xmlns: %s, asset: %s, extras: %s, scene: %s'%(type(self), self.version, self.xmlns, self.asset, self.extras, self.scene)
		
class DaeEntity(object):
	def __init__(self):
		self.syntax = 'UNKNOWN'
		
	def LoadFromXml(self, daeDocument, xmlNode):
		Debug.Debug('DaeEntity: Override this method for %s'%(type(self)),'WARNING')
	
	def SaveToXml(self, daeDocument):
		node = Element(self.syntax)
		return node
	
	def GetType(self):
		return self.syntax
		
class DaeElement(DaeEntity):
	
	def __init__(self):
		super(DaeElement,self).__init__()
		
		self.id = ''
		self.name = ''
		
	
	def LoadFromXml(self,daeDocument, xmlNode):
		if xmlNode is None:
			return
		
		self.id = xmlNode.getAttribute(DaeSyntax.ID)
		self.name = xmlNode.getAttribute(DaeSyntax.NAME)
	
	def SaveToXml(self, daeDocument):
		node = super(DaeElement,self).SaveToXml(daeDocument)
		SetAttribute(node,DaeSyntax.ID,StripString(self.id))
		SetAttribute(node,DaeSyntax.NAME, StripString(self.name))
		return node
	
	def __str__(self):
		return super(DaeElement,self).__str__()+'id: %s, name: %s'%(self.id, self.name)

# TODO:  Collada API: finish DaeLibrary
class DaeLibrary(DaeElement):
	def __init__(self, syntax, objectType, objectSyntax):
		super(DaeLibrary,self).__init__()
		
		self.extras = []
		self.asset = None
		self.items = []
		
		self.__objectSyntax = objectSyntax
		
		self.syntax = syntax
		self.__objectType = objectType
		
	def LoadFromXml(self,daeDocument, xmlNode):
		if xmlNode is None:
			return
		super(DaeLibrary,self).LoadFromXml(daeDocument, xmlNode)
		
		self.extras = CreateObjectsFromXml(daeDocument, xmlNode, DaeSyntax.EXTRA, DaeExtra)
		self.asset = CreateObjectFromXml(daeDocument, xmlNode, DaeSyntax.ASSET, DaeAsset)
		self.items =  CreateObjectsFromXml(daeDocument, xmlNode, self.__objectSyntax, self.__objectType)
		
	def SaveToXml(self,daeDocument):
		if len(self.items) > 0:
			node = super(DaeLibrary,self).SaveToXml(daeDocument)
			# Add the assets
			AppendChild(daeDocument,node,self.asset)
			# Add the library_items
			AppendChilds(daeDocument,node,self.items)
			# Add the extra's
			AppendChilds(self,node,self.extras)
			return node
		else:
			return None
	def GetItemCount(self):
		return len(self.items)
	
	def FindObject(self,url):
		for i in self.items:
			if i.id == url:
				return i
		return None
	
	def AddItem(self,item):
		self.items.append(item)
		
	def __str__(self):
		return super(DaeLibrary,self).__str__() + 'extras: %s, asset: %s, items: %s'%(self.extras, self.asset, self.items)
		
class DaeAsset(DaeEntity):
	def __init__(self):
		super(DaeAsset,self).__init__()
		self.contributors = []
		self.created = None
		self.modified = None
		self.revision = None
		self.title = None
		self.subject = None
		self.keywords = []
		self.unit = DaeUnit()
		self.upAxis = 'Y_UP'
		
		self.syntax = DaeSyntax.ASSET
		
	def LoadFromXml(self, daeDocument, xmlNode):
		if xmlNode is None:
			return
		# Get the contributor(s)
		self.contributors = CreateObjectsFromXml(daeDocument, xmlNode,DaeSyntax.CONTRIBUTOR,DaeContributor)
		# Get created
		self.created = ReadDateTime(FindElementByTagName(xmlNode,DaeSyntax.CREATED))
		# Get modified
		self.modified = ReadDateTime(FindElementByTagName(xmlNode,DaeSyntax.MODIFIED))
		# Get revision
		self.revision = ReadContents(FindElementByTagName(xmlNode,DaeSyntax.REVISION))
		# Get title
		self.title = ReadContents(FindElementByTagName(xmlNode,DaeSyntax.TITLE))
		# Get subject
		self.subject = ReadContents(FindElementByTagName(xmlNode,DaeSyntax.SUBJECT))
		# Get keywords
		self.keywords = GetStringArrayFromNodes(xmlNode.getElementsByTagName(DaeSyntax.KEYWORDS))
		# Get Unit
		self.unit.LoadFromXml(daeDocument, FindElementByTagName(xmlNode, DaeSyntax.UNIT))
		# Get upAxis
		self.upAxis = ReadContents(FindElementByTagName(xmlNode,DaeSyntax.UP_AXIS))
	
	def SaveToXml(self, daeDocument):
		node = Element(DaeSyntax.ASSET)
		AppendChilds(daeDocument,node, self.contributors)
		AppendTextChild(node, DaeSyntax.CREATED, self.created)
		AppendTextChild(node, DaeSyntax.MODIFIED, self.modified)
		AppendTextChild(node, DaeSyntax.REVISION, self.revision)
		AppendTextChild(node, DaeSyntax.TITLE, self.title)
		AppendTextChild(node, DaeSyntax.SUBJECT, self.subject)
		AppendChild(daeDocument, node, self.unit)
		AppendTextChild(node, DaeSyntax.UP_AXIS, self.upAxis)
		
		
		
		return node
		
	
	def __str__(self):
		return super(DaeAsset,self).__str__()+'contributors: %s, created: %s, modified: %s, revision: %s, title: %s, subject: %s, keywords: %s, unit: %s, upAxis: %s'%(self.contributors, self.created, self.modified, self.revision, self.title, self.subject, self.keywords, self.unit, self.upAxis)
		
# TODO:  Collada API: finish DaeScene
class DaeScene(DaeEntity):
	def __init__(self):
		super(DaeScene,self).__init__()
		self.extras = []
		self.iVisualScenes = []
		self.iPhysicsScenes = []

		self.syntax = DaeSyntax.SCENE
		
	def LoadFromXml(self, daeDocument, xmlNode):
		if xmlNode is None:
			return
		self.iVisualScenes = CreateObjectsFromXml(daeDocument, xmlNode, DaeSyntax.INSTANCE_VISUAL_SCENE, DaeVisualSceneInstance)
		self.iPhysicsScenes = CreateObjectsFromXml(daeDocument, xmlNode, DaeSyntax.INSTANCE_PHYSICS_SCENE, DaePhysicsSceneInstance)
	
	def SaveToXml(self, daeDocument):
		node = super(DaeScene,self).SaveToXml(daeDocument)
		AppendChilds(daeDocument, node, self.iVisualScenes)
		AppendChilds(daeDocument, node, self.iPhysicsScenes)
		return node
	
	def GetVisualScenes(self):
		result = []
		for i in self.iVisualScenes:
			result.append(i.object)
		return result
	
	def GetPhysicsScenes(self):
		result = []
		for i in self.iPhysicsScenes:
			result.append(i.object)
		return result
	
	def __str__(self):
		return super(DaeScene,self).__str__()+'extras: %s, visualScenes: %s, physicsScenes: %s'%(self.extras, self.iVisualScenes, self.iPhysicsScenes)
		

class DaeUnit(DaeEntity):
	def __init__(self):
		super(DaeUnit,self).__init__()
		self.name = 'meter'
		self.meter = 1.0
		
		self.syntax = DaeSyntax.UNIT
		
	def LoadFromXml(self, daeDocument, xmlNode):
		if xmlNode is None:
			return
		name = xmlNode.getAttribute(DaeSyntax.NAME)
		if name != '':
			self.name = name
			
		meter = xmlNode.getAttribute(DaeSyntax.METER)
		if meter != '':
			self.meter = float(meter)
	
	def SaveToXml(self,daeDocument):
		node = super(DaeUnit, self).SaveToXml(daeDocument)
		SetAttribute(node, DaeSyntax.METER, self.meter)
		SetAttribute(node, DaeSyntax.NAME, self.name)
		return node
				
	def __str__(self):
		return super(DaeUnit, self).__str__()+' name: %s, meter: %s'%(self.name, self.meter)
	
class DaeContributor(DaeEntity):
	def __init__(self):
		super(DaeContributor, self).__init__()
		self.author = ''
		self.authoringTool = ''
		self.comments = ''
		self.copyright = ''
		self.sourceData = ''
		
		self.syntax = DaeSyntax.CONTRIBUTOR
		
	def LoadFromXml(self, daeDocument, xmlNode):
		self.author = ReadContents(FindElementByTagName(xmlNode,DaeSyntax.AUTHOR))
		self.authoringTool = ReadContents(FindElementByTagName(xmlNode,DaeSyntax.AUTHORING_TOOL))
		self.comments = ReadContents(FindElementByTagName(xmlNode,DaeSyntax.COMMENTS))
		self.copyright = ReadContents(FindElementByTagName(xmlNode,DaeSyntax.COPYRIGHT))
		self.sourceData = ReadContents(FindElementByTagName(xmlNode,DaeSyntax.SOURCE_DATA))
	
	def SaveToXml(self, daeDocument):
		node = super(DaeContributor, self).SaveToXml(daeDocument)
		AppendTextChild(node, DaeSyntax.AUTHOR, self.author)
		AppendTextChild(node, DaeSyntax.AUTHORING_TOOL, self.authoringTool)
		AppendTextChild(node, DaeSyntax.COMMENTS, self.comments)
		AppendTextChild(node, DaeSyntax.COPYRIGHT, self.copyright)
		AppendTextChild(node, DaeSyntax.SOURCE_DATA, self.sourceData)
		return node
		
		
	def __str__(self):
		return super(DaeContributor,self).__str__() + 'author: %s, authoring_tool: %s, comments: %s, copyright: %s, sourceData: %s'%(self.author, self.authoringTool, self.comments, self.copyright, self.sourceData)
	
class DaeAnimation(DaeElement):
	def __init__(self):
		super(DaeAnimation, self).__init__()
		self.sources = []
		self.samplers = []
		self.channels = []
		self.syntax = DaeSyntax.ANIMATION
		
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaeAnimation, self).LoadFromXml(daeDocument, xmlNode)
		self.channels = CreateObjectsFromXml(daeDocument, xmlNode, DaeSyntax.CHANNEL, DaeChannel)
		self.samplers = CreateObjectsFromXml(daeDocument, xmlNode, DaeSyntax.SAMPLER, DaeSampler)
		self.sources = CreateObjectsFromXml(daeDocument, xmlNode, DaeSyntax.SOURCE, DaeSource)
			
	def SaveToXml(self, daeDocument):
		node = super(DaeAnimation, self).SaveToXml(daeDocument)
		AppendChilds(daeDocument, node, self.sources)
		AppendChilds(daeDocument, node, self.samplers)
		AppendChilds(daeDocument, node, self.channels)
		return node

	def GetSource(self, sourceId):
		for source in self.sources:
			if source.id == sourceId:
				return source
		return None

class DaeSampler(DaeEntity):
	def __init__(self):
		self.syntax = DaeSyntax.SAMPLER
		self.id = None
		self.inputs = []
	
	def LoadFromXml(self, daeDocument, xmlNode):
		self.id = ReadAttribute(xmlNode, DaeSyntax.ID)
		self.inputs = CreateObjectsFromXml(daeDocument, xmlNode, DaeSyntax.INPUT, DaeInput)
		
	def SaveToXml(self, daeDocument):
		node = super(DaeSampler, self).SaveToXml(daeDocument)
		AppendChilds(daeDocument, node, self.inputs)
		SetAttribute(node, DaeSyntax.ID, StripString(self.id))
		return node
	
	def GetInput(self, semantic):
		for input in self.inputs:
			if input.semantic == semantic:
				return input
		return None

class DaeChannel(DaeEntity):
	def __init__(self):
		self.syntax = DaeSyntax.CHANNEL
		self.source = None
		self.target = None
	
	def LoadFromXml(self, daeDocument, xmlNode):
		self.source = ReadAttribute(xmlNode, DaeSyntax.SOURCE)
		self.target = ReadAttribute(xmlNode, DaeSyntax.TARGET)		
		
	def SaveToXml(self, daeDocument):
		node = super(DaeChannel, self).SaveToXml(daeDocument)
		SetAttribute(node, DaeSyntax.SOURCE, StripString('#'+self.source.id))
		SetAttribute(node, DaeSyntax.TARGET, self.target)
		return node

class DaeAnimationClip(DaeElement):
	pass
class DaeCamera(DaeElement):
	def __init__(self):
		super(DaeCamera,self).__init__()
		self.asset = None
		self.extras = []
		self.optics = DaeOptics()
		self.imager = None
		self.syntax = DaeSyntax.CAMERA
		
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaeCamera, self).LoadFromXml(daeDocument, xmlNode)
		self.extras = CreateObjectsFromXml(daeDocument, xmlNode, DaeSyntax.EXTRA, DaeExtra)
		self.asset = CreateObjectFromXml(daeDocument, xmlNode, DaeSyntax.ASSET, DaeAsset)
		self.optics.LoadFromXml(daeDocument, FindElementByTagName(xmlNode, DaeSyntax.OPTICS))
		self.imager = CreateObjectFromXml(daeDocument,xmlNode, DaeSyntax.IMAGER,DaeImager)
		
	
	def SaveToXml(self, daeDocument):
		node = super(DaeCamera, self).SaveToXml(daeDocument)
		# Add the assets
		AppendChild(daeDocument,node,self.asset)
		# Add the optics
		node.appendChild(self.optics.SaveToXml(daeDocument))
		# Add the imager
		AppendChild(daeDocument,node,self.imager)
		# Add the extra's
		AppendChilds(self,node,self.extras)
		return node
		
	def __str__(self):
		return super(DaeCamera,self).__str__()+'asset: %s, optics: %s, imager: %s, extras: %s'%(self.asset, self.optics, self.imager, self.extras)
  
class DaeController(DaeElement):
	pass
class DaeImage(DaeElement):
	def __init__(self):
		super(DaeImage,self).__init__()
		self.format = None
		self.height = None
		self.width = None
		self.depth = None
		self.initFrom = None
		self.syntax = DaeSyntax.IMAGE
		
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaeImage, self).LoadFromXml(daeDocument, xmlNode)
		self.format = ReadAttribute(xmlNode, DaeSyntax.FORMAT)
		self.height = ReadAttribute(xmlNode, DaeSyntax.HEIGHT)
		self.width = ReadAttribute(xmlNode, DaeSyntax.WIDTH)
		self.depth = ReadAttribute(xmlNode, DaeSyntax.DEPTH)
		self.initFrom = ReadContents(FindElementByTagName(xmlNode, DaeSyntax.INIT_FROM))	
		
	def SaveToXml(self, daeDocument):
		node = super(DaeImage, self).SaveToXml(daeDocument)
		SetAttribute(node, DaeSyntax.FORMAT, self.format)
		SetAttribute(node, DaeSyntax.HEIGHT, self.height)
		SetAttribute(node, DaeSyntax.WIDTH, self.width)
		SetAttribute(node, DaeSyntax.DEPTH, self.depth)
		AppendTextChild(node, DaeSyntax.INIT_FROM,self.initFrom, None)
		return node
	
##class DaeMaterial(DaeElement):
##	  def __init__(self):
##		  super(DaeMaterial,self).__init__()
##		  self.asset = None
##		  self.iEffects = []
##		  self.extras = None
##		  self.syntax = DaeSyntax.MATERIAL
##		  
##	  def LoadFromXml(self, daeDocument, xmlNode):
##		  super(DaeMaterial, self).LoadFromXml(daeDocument, xmlNode)
##		  self.extras = CreateObjectsFromXml(daeDocument, xmlNode, DaeSyntax.EXTRA, DaeExtra)
##		  self.asset = CreateObjectFromXml(daeDocument, xmlNode, DaeSyntax.ASSET, DaeAsset)
##		  self.iEffects = CreateObjectsFromXml(daeDocument,xmlNode, DaeSyntax.INSTANCE_EFFECT, DaeEffectInstance)
##	  
##	  def SaveToXml(self, daeDocument):
##		  node = super(DaeMaterial, self).SaveToXml(daeDocument)
##		  # Add the assets
##		  AppendChild(daeDocument,node,self.asset)
##		  # Add the effect instances
##		  AppendChilds(daeDocument, node, self.iEffects)
##		  # Add the extra's
##		  AppendChilds(self,node,self.extras)
##		  return node
##		  
##	  def __str__(self):
##		  return super(DaeLight,self).__str__()+' assets: %s, data: %s, extras: %s'%(self.asset, self.data, self.extras)

class DaeGeometry(DaeElement):
	def __init__(self):
		super(DaeGeometry,self).__init__()
		self.asset = None
		self.data = None
		self.extras = None
		self.syntax = DaeSyntax.GEOMETRY
		
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaeGeometry, self).LoadFromXml(daeDocument, xmlNode)
		self.extras = CreateObjectsFromXml(daeDocument, xmlNode, DaeSyntax.EXTRA, DaeExtra)
		self.asset = CreateObjectFromXml(daeDocument, xmlNode, DaeSyntax.ASSET, DaeAsset)
				
		self.data = CreateObjectFromXml(daeDocument, xmlNode, DaeSyntax.MESH, DaeMesh)
		if self.data is None:
			self.data = CreateObjectFromXml(daeDocument, xmlNode, DaeSyntax.CONVEX_MESH, DaeConvexMesh)
		if self.data is None:
			self.data = CreateObjectFromXml(daeDocument, xmlNode, DaeSyntax.SPLINE, DaeSpline)
	
	def SaveToXml(self, daeDocument):
		node = super(DaeGeometry, self).SaveToXml(daeDocument)
		# Add the assets
		AppendChild(daeDocument,node,self.asset)
		# Add the data
		AppendChild(daeDocument, node, self.data)
		# Add the extra's
		AppendChilds(self,node,self.extras)
		return node
		
	def __str__(self):
		return super(DaeGeometry,self).__str__()+' assets: %s, data: %s, extras: %s'%(self.asset, self.data, self.extras)
	
class DaeConvexMesh(DaeEntity):
	def __init__(self):
		super(DaeConvexMesh, self).__init__()
		self.syntax = DaeSyntax.CONVEX_MESH
		self.convexHullOf = None
	
	def LoadFromXml(self, daeDocument, xmlNode):
		self.convexHullOf = ReadAttribute(xmlNode, DaeSyntax.CONVEX_HULL_OF)
		
	def SaveToXml(self, daeDocument):
		node = super(DaeConvexMesh, self).SaveToXml(daeDocument)
		SetAttribute(node, DaeSyntax.CONVEX_HULL_OF, StripString(self.convexHullOf))
		return node
	
class DaeMesh(DaeEntity):
	def __init__(self):
		super(DaeMesh, self).__init__()
		self.sources = []
		self.vertices = None
		self.primitives = []
		self.extras = []
		self.syntax = DaeSyntax.MESH
		
	def LoadFromXml(self, daeDocument, xmlNode):
		if xmlNode is None:
			return
		self.vertices = CreateObjectFromXml(daeDocument, xmlNode, DaeSyntax.VERTICES, DaeVertices)		  
		self.sources = CreateObjectsFromXml(daeDocument, xmlNode, DaeSyntax.SOURCE, DaeSource)
		
		lines = CreateObjectsFromXml(daeDocument, xmlNode, DaeSyntax.LINES, DaeLines)
		linestrips = CreateObjectsFromXml(daeDocument, xmlNode, DaeSyntax.LINESTRIPS, DaeLineStrips)
		polygons = CreateObjectsFromXml(daeDocument, xmlNode, DaeSyntax.POLYGONS, DaePolygons)
		polylist = CreateObjectsFromXml(daeDocument, xmlNode, DaeSyntax.POLYLIST, DaePolylist)
		triangles = CreateObjectsFromXml(daeDocument, xmlNode, DaeSyntax.TRIANGLES, DaeTriangles)
		trifans = CreateObjectsFromXml(daeDocument, xmlNode, DaeSyntax.TRIFANS, DaeTriFans)
		tristrips = CreateObjectsFromXml(daeDocument, xmlNode, DaeSyntax.TRISTRIPS, DaeTriStrips)
		if lines != None: self.primitives += lines
		if linestrips != None: self.primitives += linestrips
		if polygons != None: self.primitives += polygons
		if polylist != None: self.primitives += polylist
		if triangles != None: self.primitives += triangles
		if trifans != None: self.primitives += trifans
		if tristrips != None: self.primitives += tristrips
		
		self.extras = CreateObjectsFromXml(daeDocument, xmlNode, DaeSyntax.EXTRA, DaeExtra)
		
	def FindSource(self,input):
		for s in self.sources:
			if s.id == input.source:
				return s
		return None
		
	def SaveToXml(self, daeDocument):
		node = super(DaeMesh, self).SaveToXml(daeDocument)
		AppendChilds(daeDocument, node, self.sources)
		AppendChild(daeDocument, node, self.vertices)
		AppendChilds(daeDocument, node, self.primitives)
		AppendChilds(daeDocument, node, self.extras)
		return node
class DaeVertices(DaeElement):
	def __init__(self):
		super(DaeVertices,self).__init__()
		self.inputs = []
		self.extras = []
		
		self.syntax = DaeSyntax.VERTICES
		
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaeVertices,self).LoadFromXml(daeDocument, xmlNode)
		self.inputs = CreateObjectsFromXml(daeDocument, xmlNode, DaeSyntax.INPUT, DaeInput)
		self.extras = CreateObjectsFromXml(daeDocument, xmlNode, DaeSyntax.EXTRA, DaeExtra)
		
	def SaveToXml(self, daeDocument):
		node = super(DaeVertices, self).SaveToXml(daeDocument)
		AppendChilds(daeDocument, node, self.inputs)
		AppendChilds(daeDocument, node, self.extras)
		return node
	
	def FindInput(self, semantic):
		for i in self.inputs:
			if i.semantic == semantic:
				return i
		return None
	
	def __str__(self):
		return super(DaeVertices,self).__str__() + ' inputs: %s, extras: %s'%(self.inputs, self.extras)
	
class DaeInput(DaeEntity):
	def __init__(self):
		super(DaeInput, self).__init__()
		self.offset = None
		self.semantic = ''
		self.source = ''
		self.set = ''
		self.syntax = DaeSyntax.INPUT
		
	def LoadFromXml(self, daeDocument, xmlNode):
		self.offset = CastAttributeFromXml(xmlNode, DaeSyntax.OFFSET, int)
		self.semantic = ReadAttribute(xmlNode, DaeSyntax.SEMANTIC)
		self.source = ReadAttribute(xmlNode, DaeSyntax.SOURCE)[1:]
		self.set = ReadAttribute(xmlNode, DaeSyntax.SET)
		
	def SaveToXml(self, daeDocument):
		node = super(DaeInput, self).SaveToXml(daeDocument)
		SetAttribute(node,DaeSyntax.OFFSET, self.offset)
		SetAttribute(node,DaeSyntax.SEMANTIC, self.semantic)
		SetAttribute(node,DaeSyntax.SOURCE, StripString('#'+self.source))
		SetAttribute(node,DaeSyntax.SET, self.set)
		return node

class DaeSource(DaeElement):
	def __init__(self):
		super(DaeSource, self).__init__()
		self.source = DaeArray()
		self.vectors = []
		self.techniqueCommon = None
		self.techniques = []
		
		self.syntax = DaeSyntax.SOURCE
		
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaeSource,self).LoadFromXml(daeDocument, xmlNode)
		if xmlNode is None:
			return
		bools = CreateObjectFromXml(daeDocument, xmlNode, DaeSyntax.BOOL_ARRAY, DaeBoolArray)
		floats = CreateObjectFromXml(daeDocument, xmlNode, DaeSyntax.FLOAT_ARRAY, DaeFloatArray)
		ints = CreateObjectFromXml(daeDocument, xmlNode, DaeSyntax.INT_ARRAY, DaeIntArray)
		names = CreateObjectFromXml(daeDocument, xmlNode, DaeSyntax.NAME_ARRAY, DaeNameArray)
		if bools != None:
			self.source = bools
		elif floats != None:
			self.source = floats
		elif ints != None:
			self.source = ints
		elif names != None:
			self.source = names
		
		self.techniqueCommon = CreateObjectFromXml(daeDocument, xmlNode, DaeSyntax.TECHNIQUE_COMMON, DaeSource.DaeTechniqueCommon)
		self.techniques = CreateObjectsFromXml(daeDocument, xmlNode, DaeSyntax.TECHNIQUE,DaeTechnique)
		if not (self.techniqueCommon is None):
			for i in range(0,self.techniqueCommon.accessor.count):
				vec = []			
				for j in range(0,self.techniqueCommon.accessor.stride):
					vec.append(self.source.data[i*self.techniqueCommon.accessor.stride+j])
				self.vectors.append(vec)	
		
	def SaveToXml(self, daeDocument):
		node = super(DaeSource, self).SaveToXml(daeDocument)
##		  if len(self.vectors) > 0:
##			  if type(self.vectors[0][0]) == float:
##				  self.source = DaeFloatArray()
##				  self.source.id = self.id+'-array'
##				  
##		  for i in range(len(self.vectors)):
##			  for j in range(len(self.vectors[i])):
##				  self.source.data.append(self.vectors[i][j])
			
		# Add the source
		AppendChild(daeDocument, node, self.source)
		# Add the technique common		 
		AppendChild(daeDocument,node,self.techniqueCommon)
		# Add the techniques
		AppendChilds(daeDocument, node, self.techniques)
		return node
	
	def __str__(self):
		return super(DaeSource,self).__str__()+' source: %s, techniqueCommon: %s, techniques: %s'%(self.source, self.techniqueCommon, self.techniques)

	class DaeTechniqueCommon(DaeEntity):
		def __init__(self):
			self.accessor = None
			self.syntax = DaeSyntax.TECHNIQUE_COMMON
			
		def LoadFromXml(self, daeDocument, xmlNode):
			self.accessor = CreateObjectFromXml(daeDocument, xmlNode, DaeSyntax.ACCESSOR, DaeAccessor)
			   
		def SaveToXml(self, daeDocument):
			node = super(DaeSource.DaeTechniqueCommon,self).SaveToXml(daeDocument)
			AppendChild(daeDocument,node, self.accessor)
			return node
		
		def __str__(self):
			return super(DaeSource.DaeTechniqueCommon,self).__str__()+' accessor: %s'%(self.accessor)
		
class DaeLight(DaeElement):
	def __init__(self):
		super(DaeLight,self).__init__()
		self.asset = None
		self.techniqueCommon = DaeLight.DaeTechniqueCommon()
		self.techniques = []
		self.extras = None
		self.syntax = DaeSyntax.LIGHT
		
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaeLight, self).LoadFromXml(daeDocument, xmlNode)
		self.extras = CreateObjectsFromXml(daeDocument, xmlNode, DaeSyntax.EXTRA, DaeExtra)
		self.asset = CreateObjectFromXml(daeDocument, xmlNode, DaeSyntax.ASSET, DaeAsset)
		##self.techniqueCommon.LoadFromXml(daeDocument, FindElementByTagName(xmlNode, DaeSyntax.TECHNIQUE_COMMON))
		self.techniques = CreateObjectsFromXml(daeDocument, xmlNode, DaeSyntax.TECHNIQUE,DaeTechnique)
		
		lightSourceNode = RemoveWhiteSpaceNode(FindElementByTagName(xmlNode, DaeSyntax.TECHNIQUE_COMMON)).firstChild
		lightSourceName = lightSourceNode.localName
		if lightSourceName == DaeSyntax.DIRECTIONAL:
			self.techniqueCommon = DaeLight.DaeDirectional()			
		elif lightSourceName == DaeSyntax.SPOT:
			self.techniqueCommon = DaeLight.DaeSpot()
		elif lightSourceName == DaeSyntax.AMBIENT:
			self.techniqueCommon = DaeLight.DaeAmbient()
		elif lightSourceName == DaeSyntax.POINT:
			self.techniqueCommon = DaeLight.DaePoint()
		self.techniqueCommon.LoadFromXml(daeDocument,lightSourceNode)
	
	def SaveToXml(self, daeDocument):
		node = super(DaeLight, self).SaveToXml(daeDocument)
		# Add the assets
		AppendChild(daeDocument,node,self.asset)
		# Add the technique common		 
		AppendChild(daeDocument,node,self.techniqueCommon)
		# Add the techniques
		AppendChilds(daeDocument, node, self.techniques)
		# Add the extra's
		AppendChilds(self,node,self.extras)
		return node
	
	def __str__(self):
		return super(DaeLight,self).__str__()+' techniqueCommon: %s, techniques: %s'%(self.techniqueCommon, self.techniques)
		
	class DaeTechniqueCommon(DaeEntity):
		def __init__(self):
			self.color = []
			self.lightSource = None
			self.syntax = DaeSyntax.TECHNIQUE_COMMON
			
		def LoadFromXml(self, daeDocument, xmlNode):
			self.color = ToFloat3(ReadContents(FindElementByTagName(xmlNode,DaeSyntax.COLOR)))
		
		def SaveToXml(self, daeDocument):
			node = Element(DaeSyntax.TECHNIQUE_COMMON)
			child = super(DaeLight.DaeTechniqueCommon,self).SaveToXml(daeDocument)
			AppendTextChild(child,DaeSyntax.COLOR, self.color)
			node.appendChild(child)
			return node
		
		def __str__(self):
			return super(DaeLight.DaeTechniqueCommon,self).__str__()+' color: %s'%(self.color)
		
	class DaeAmbient(DaeTechniqueCommon):
		def __init__(self):
			super(DaeLight.DaeAmbient,self).__init__()
			self.syntax = DaeSyntax.AMBIENT
			
		def LoadFromXml(self, daeDocument, xmlNode):
			super(DaeLight.DaeAmbient,self).LoadFromXml(daeDocument, xmlNode)
		
		def SaveToXml(self, daeDocument):
			node  = super(DaeLight.DaeAmbient,self).SaveToXml(daeDocument)
			return node
		
		def __str__(self):
			return super(DaeLight.DaeAmbient,self).__str__()
	
	class DaeSpot(DaeTechniqueCommon):
		def __init__(self):
			super(DaeLight.DaeSpot,self).__init__()
			self.defConstantAttenuation = 0.0
			self.defLinearAttenuation = 0.0
			self.defQuadraticAttenuation = 0.0
			self.defFalloffAngle = 180.0
			self.defFalloffExponent = 0.0
			
			self.constantAttenuation = 0.0
			self.linearAttenuation = 0.0
			self.quadraticAttenuation = 0.0
			self.falloffAngle = 180.0
			self.falloffExponent = 0.0
			self.syntax = DaeSyntax.SPOT
			
		def LoadFromXml(self, daeDocument, xmlNode):
			super(DaeLight.DaeSpot,self).LoadFromXml(daeDocument, xmlNode)
			self.constantAttenuation = CastFromXml(daeDocument,xmlNode,DaeSyntax.CONSTANT_ATTENUATION, float, self.defConstantAttenuation, 1.0)
			self.linearAttenuation = CastFromXml(daeDocument,xmlNode,DaeSyntax.LINEAR_ATTENUATION,float, self.defLinearAttenuation, 0)
			self.quadraticAttenuation = CastFromXml(daeDocument, xmlNode,DaeSyntax.QUADRATIC_ATTENUATION, float, self.defQuadraticAttenuation, 0)
			self.falloffAngle = CastFromXml(daeDocument, xmlNode, DaeSyntax.FALLOFF_ANGLE, float, self.defFalloffAngle, 180.0)
			self.falloffExponent = CastFromXml(daeDocument, xmlNode, DaeSyntax.FALLOFF_EXPONENT, float, self.defFalloffExponent, 0)
		
		def SaveToXml(self, daeDocument):
			node = super(DaeLight.DaeSpot,self).SaveToXml(daeDocument)
			AppendTextChild(node.firstChild,DaeSyntax.CONSTANT_ATTENUATION, self.constantAttenuation, self.defConstantAttenuation)
			AppendTextChild(node.firstChild,DaeSyntax.LINEAR_ATTENUATION, self.linearAttenuation, self.defLinearAttenuation)
			AppendTextChild(node.firstChild,DaeSyntax.QUADRATIC_ATTENUATION, self.quadraticAttenuation, self.defQuadraticAttenuation)
			AppendTextChild(node.firstChild,DaeSyntax.FALLOFF_ANGLE, self.falloffAngle, self.defFalloffAngle)
			AppendTextChild(node.firstChild,DaeSyntax.FALLOFF_EXPONENT, self.falloffExponent, self.defFalloffExponent)
			return node
			
		def __str__(self):
			return super(DaeLight.DaeSpot,self).__str__()+' const.att: %s, lin.att: %s, quad.att: %s, falloffAngle: %s, falloffExponent: %s'%(self.constantAttenuation, self.linearAttenuation, self.quadraticAttenuation, self.falloffAngle, self.falloffExponent)
			
	class DaeDirectional(DaeTechniqueCommon):
		# default direction is [0,0,-1] pointing down the -Z axis.
		# To change the direction, change the transform of the parent DaeNode
		def __init__(self):
			super(DaeLight.DaeDirectional,self).__init__()
			self.syntax = DaeSyntax.DIRECTIONAL
			
		def LoadFromXml(self, daeDocument, xmlNode):
			super(DaeLight.DaeDirectional,self).LoadFromXml(daeDocument, xmlNode)
		
		def SaveToXml(self, daeDocument):
			node  = super(DaeLight.DaeDirectional,self).SaveToXml(daeDocument)
			return node
		
		def __str__(self):
			return super(DaeLight.DaeDirectional,self).__str__()
	
	class DaePoint(DaeTechniqueCommon):
		def __init__(self):
			super(DaeLight.DaePoint,self).__init__()
			self.constantAttenuation = 0.0
			self.linearAttenuation = 0.0
			self.quadraticAttenuation = 0.0
			self.syntax = DaeSyntax.POINT
			
		def LoadFromXml(self, daeDocument, xmlNode):
			super(DaeLight.DaePoint,self).LoadFromXml(daeDocument, xmlNode)
			self.constantAttenuation = CastFromXml(daeDocument,xmlNode,DaeSyntax.CONSTANT_ATTENUATION, float, 1)
			self.linearAttenuation = CastFromXml(daeDocument,xmlNode,DaeSyntax.LINEAR_ATTENUATION,float, 0)
			self.quadraticAttenuation = CastFromXml(daeDocument, xmlNode,DaeSyntax.QUADRATIC_ATTENUATION, float, 0)
		
		def SaveToXml(self, daeDocument):
			node = super(DaeLight.DaePoint,self).SaveToXml(daeDocument)
			AppendTextChild(node.firstChild,DaeSyntax.CONSTANT_ATTENUATION, self.constantAttenuation)
			AppendTextChild(node.firstChild,DaeSyntax.LINEAR_ATTENUATION, self.linearAttenuation)
			AppendTextChild(node.firstChild,DaeSyntax.QUADRATIC_ATTENUATION, self.quadraticAttenuation)
			return node
		
		def __str__(self):
			return super(DaeLight.DaePoint,self).__str__()+' const.att: %s, lin.att: %s, quad.att: %s'%(self.constantAttenuation, self.linearAttenuation, self.quadraticAttenuation)
			
class DaeVisualScene(DaeElement):
	def __init__(self):
		super(DaeVisualScene,self).__init__()
		self.asset = None
		self.extras = None
		self.nodes = []
		self.syntax = DaeSyntax.VISUAL_SCENE		
		
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaeVisualScene, self).LoadFromXml(daeDocument, xmlNode)
		self.extras = CreateObjectsFromXml(daeDocument, xmlNode, DaeSyntax.EXTRA, DaeExtra)
		self.asset = CreateObjectFromXml(daeDocument, xmlNode, DaeSyntax.ASSET, DaeAsset)
		self.nodes = CreateObjectsFromXml(daeDocument, xmlNode, DaeSyntax.NODE, DaeNode)
		
	def SaveToXml(self, daeDocument):
		node = super(DaeVisualScene, self).SaveToXml(daeDocument)
		# Add the assets
		AppendChild(daeDocument,node,self.asset)
		# Add the nodes
		AppendChilds(daeDocument, node, self.nodes)
		# Add the extra's
		AppendChilds(self,node,self.extras)
		return node
	
	def FindNode(self, nodeUrl):
		for n in self.nodes:
			if n.id == nodeUrl:
				return n
		return None
		
		
	def __str__(self):
		return super(DaeVisualScene,self).__str__()+' asset: %s, nodes: %s, extras: %s'%(self.asset, self.nodes, self.extras)
	
class DaeNode(DaeElement):
	
	NODE = 2
	JOINT = 1	 
	
	def __init__(self):
		super(DaeNode,self).__init__()
		self.sid = None
		self.type = DaeNode.NODE
		self.layer = []
		self.transforms = []
		self.nodes = []
		
		self.iAnimations = []
		self.iCameras = []
		self.iControllers = []
		self.iGeometries = []
		self.iLights = []
		self.iNodes = []
		self.iVisualScenes = []
		
		self.syntax = DaeSyntax.NODE
		
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaeNode, self).LoadFromXml(daeDocument, xmlNode)
		self.sid = ReadAttribute(xmlNode, DaeSyntax.SID)
		type = ReadAttribute(xmlNode, DaeSyntax.TYPE)
		if type == DaeSyntax.TYPE_JOINT:
			self.type = DaeNode.JOINT
		else:
			self.type = DaeNode.NODE			
		self.layer = ReadAttribute(xmlNode, DaeSyntax.LAYER).split()
		
		# Get transforms
		RemoveWhiteSpaceNode(xmlNode)
		child = xmlNode.firstChild
		while child != None:
			name = child.localName
			sid = ReadAttribute(child, DaeSyntax.SID)
			if name == DaeSyntax.TRANSLATE:
				self.transforms.append([name,ToFloatList(ReadContents(child)), sid])
			elif name == DaeSyntax.ROTATE:
				self.transforms.append([name,ToFloatList(ReadContents(child)), sid])
			elif name == DaeSyntax.SCALE:
				self.transforms.append([name,ToFloatList(ReadContents(child)), sid])
			elif name == DaeSyntax.SKEW:
				self.transforms.append([name,ToFloatList(ReadContents(child)), sid])
			elif name == DaeSyntax.LOOKAT:
				self.transforms.append([name,ToFloatList(ReadContents(child)), sid])
			elif name == DaeSyntax.MATRIX:
				self.transforms.append([name,ToMatrix4(ReadContents(child)), sid])
				
			child = child.nextSibling
			
		# Get the instances
		self.iAnimations = CreateObjectsFromXml(daeDocument, xmlNode, DaeSyntax.INSTANCE_ANIMATION, DaeAnimationInstance)
		self.iCameras = CreateObjectsFromXml(daeDocument, xmlNode, DaeSyntax.INSTANCE_CAMERA, DaeCameraInstance)
		self.iControllers = CreateObjectsFromXml(daeDocument, xmlNode, DaeSyntax.INSTANCE_CONTROLLER, DaeControllerInstance)
		self.iGeometries = CreateObjectsFromXml(daeDocument, xmlNode, DaeSyntax.INSTANCE_GEOMETRY, DaeGeometryInstance)
		self.iLights = CreateObjectsFromXml(daeDocument, xmlNode, DaeSyntax.INSTANCE_LIGHT, DaeLightInstance)
		self.iNodes = CreateObjectsFromXml(daeDocument, xmlNode, DaeSyntax.INSTANCE_NODE, DaeNodeInstance)
		self.iVisualScenes = CreateObjectsFromXml(daeDocument, xmlNode, DaeSyntax.INSTANCE_VISUAL_SCENE, DaeVisualSceneInstance)

		# Get childs nodes
		self.nodes = CreateObjectsFromXml(daeDocument, xmlNode, DaeSyntax.NODE, DaeNode)

	def SaveToXml(self, daeDocument):
		node = super(DaeNode, self).SaveToXml(daeDocument)
		SetAttribute(node, DaeSyntax.SID, self.sid)
		if self.type == DaeSyntax.TYPE_JOINT:
			SetAttribute(node, DaeSyntax.TYPE, DaeNode.GetType(self.type))
		
		# Add the layers
		SetAttribute(node, DaeSyntax.LAYER, ListToString(self.layer))
		for i in self.transforms:
			writeTransform = False
			el = Element(i[0])
			val = i[1]
			if i[0] == DaeSyntax.MATRIX:
				val = MatrixToString(val,ROUND)
				AppendTextChild(node,i[0],val)
			else:
				orgval = val
				val = ListToString(RoundList(val, 5))
				if i[0] == DaeSyntax.SCALE:
					##AppendTextChild(node,i[0],val,"1.0 1.0 1.0")
					SetAttribute(AppendTextChild(node,i[0],val,None), DaeSyntax.SID, DaeSyntax.SCALE)
				elif i[0] == DaeSyntax.TRANSLATE:
					##AppendTextChild(node,i[0],val,"0.0 0.0 0.0")
					SetAttribute(AppendTextChild(node,i[0],val,None), DaeSyntax.SID, DaeSyntax.TRANSLATE)
				elif i[0] == DaeSyntax.ROTATE:
					##AppendTextChild(node,i[0],val,"0.0 0.0 0.0 0.0")
					axis = None
					if orgval[0] == 1 and orgval[1] == 0 and orgval[2] == 0:
						axis = "X"
					elif orgval[0] == 0 and orgval[1] == 1 and orgval[2] == 0:
						axis = "Y"
					elif orgval[0] == 0 and orgval[1] == 0 and orgval[2] == 1:
						axis = "Z"
					no = AppendTextChild(node,i[0],val,None)
					if axis != None:
						SetAttribute(no, DaeSyntax.SID, DaeSyntax.ROTATE+axis)
						
				elif i[0] == DaeSyntax.SKEW:
					AppendTextChild(node,i[0],val)
				elif i[0] == DaeSyntax.MATRIX or i[0] == DaeSyntax.LOOKAT:
					AppendTextChild(node,i[0],val)
		
		AppendChilds(daeDocument, node, self.nodes) 		   
	
		AppendChilds(daeDocument, node, self.iAnimations)
		AppendChilds(daeDocument, node, self.iCameras)
		AppendChilds(daeDocument, node, self.iControllers)
		AppendChilds(daeDocument, node, self.iGeometries)
		AppendChilds(daeDocument, node, self.iLights)
		AppendChilds(daeDocument, node, self.iNodes)
		AppendChilds(daeDocument, node, self.iVisualScenes)
		
		return node
	
	def IsJoint(self):
		return self.type == DaeNode.JOINT
	
	def GetType(type):
		if type == DaeNode.JOINT:
			return DaeSyntax.TYPE_JOINT
		else:
			return DaeSyntax.TYPE_NODE
	GetType = staticmethod(GetType)
		
	def GetInstances(self):
		return []+self.iAnimations+self.iCameras+self.iControllers+self.iGeometries+self.iLights+self.iNodes
	
	
	
# TODO:  Collada API: finish DaeTechnique 
class DaeTechnique(DaeEntity):
	def __init__(self):
		super(DaeTechnique,self).__init__()
		self.profile = ''
		self.xmlns = ''
		self.syntax = DaeSyntax.TECHNIQUE
		
	def LoadFromXml(self, daeDocument, xmlNode):
		self.profile = xmlNode.getAttribute(DaeSyntax.PROFILE)
		self.xmlns = xmlNode.getAttribute(DaeSyntax.XMLNS)
		
	def SaveToXml(self, daeDocument):
		node = super(DaeTechnique,self).SaveToXml(daeDocument)
		node.setAttribute(DaeSyntax.PROFILE, self.profile)
		SetAttribute(node, DaeSyntax.XMLNS, self.xmlns)
		return node
	
class DaeOptics(DaeEntity):
	def __init__(self):
		super(DaeOptics,self).__init__()
		self.techniqueCommon = DaeOptics.DaeTechniqueCommon()
		self.techniques = []
		self.extras = None
		self.syntax = DaeSyntax.OPTICS
		
	def LoadFromXml(self, daeDocument, xmlNode):
		self.extras = CreateObjectsFromXml(daeDocument, xmlNode, DaeSyntax.EXTRA, DaeExtra)
		#self.techniqueCommon.LoadFromXml(daeDocument, FindElementByTagName(xmlNode, DaeSyntax.TECHNIQUE_COMMON))
		self.techniques = CreateObjectsFromXml(daeDocument, xmlNode, DaeSyntax.TECHNIQUE,DaeTechnique)
		
		opticsSourceNode = RemoveWhiteSpaceNode(FindElementByTagName(xmlNode, DaeSyntax.TECHNIQUE_COMMON)).firstChild
		opticsSourceName = opticsSourceNode.localName
		if opticsSourceName == DaeSyntax.PERSPECTIVE:
			self.techniqueCommon = DaeOptics.DaePerspective()
		elif opticsSourceName == DaeSyntax.ORTHOGRAPHIC:
			self.techniqueCommon = DaeOptics.DaeOrthoGraphic()
		self.techniqueCommon.LoadFromXml(daeDocument,opticsSourceNode)
	
	def SaveToXml(self, daeDocument):
		node = super(DaeOptics, self).SaveToXml(daeDocument)
		# Add the technique common		 
		AppendChild(daeDocument,node,self.techniqueCommon)
		# Add the techniques
		AppendChilds(daeDocument, node, self.techniques)
		# Add the extra's
		AppendChilds(self,node,self.extras)
		return node
		
	def __str__(self):
		return super(DaeOptics,self).__str__()+' extras: %s, techniqueCommon: %s, techniques: %s'%(self.extras, self.techniqueCommon, self.techniques)
	
	class DaeTechniqueCommon(DaeEntity):
		def __init__(self):
			self.znear = 0.0
			self.zfar = 0.0
			self.aspectRatio = None
			
			self.syntax = DaeSyntax.TECHNIQUE_COMMON
			
		def LoadFromXml(self, daeDocument, xmlNode):
			self.znear = ToFloat(ReadContents(FindElementByTagName(xmlNode,DaeSyntax.ZNEAR)))
			self.zfar = ToFloat(ReadContents(FindElementByTagName(xmlNode,DaeSyntax.ZFAR)))
			self.aspectRatio = ToFloat(ReadContents(FindElementByTagName(xmlNode,DaeSyntax.ASPECT_RATIO)))
		
		def SaveToXml(self, daeDocument):
			node = Element(DaeSyntax.TECHNIQUE_COMMON)
			child = super(DaeOptics.DaeTechniqueCommon,self).SaveToXml(daeDocument)
##			  AppendTextChild(child,DaeSyntax.ZNEAR, self.znear)
##			  AppendTextChild(child,DaeSyntax.ZFAR, self.zfar)
##			  AppendTextChild(child,DaeSyntax.ASPECT_RATIO, self.aspectRatio)			 
			node.appendChild(child)
			return node
		
		def SavePropertiesToXml(self, daeDocument, node):			 
			AppendTextChild(node,DaeSyntax.ZNEAR, self.znear)
			AppendTextChild(node,DaeSyntax.ZFAR, self.zfar)
			AppendTextChild(node,DaeSyntax.ASPECT_RATIO, self.aspectRatio)
		
		def __str__(self):
			return super(DaeOptics.DaeTechniqueCommon,self).__str__()+' znear: %s, zfar: %s, aspectRatio: %s'%(self.znear, self.zfar, self.aspectRatio)
		
	class DaePerspective(DaeTechniqueCommon):
		def __init__(self):
			super(DaeOptics.DaePerspective,self).__init__()
			self.xfov = None
			self.yfov = None
			self.syntax = DaeSyntax.PERSPECTIVE
			
		def LoadFromXml(self, daeDocument, xmlNode):
			super(DaeOptics.DaePerspective,self).LoadFromXml(daeDocument, xmlNode)
			self.xfov = ToFloat(ReadContents(FindElementByTagName(xmlNode,DaeSyntax.XFOV)))
			self.yfov = ToFloat(ReadContents(FindElementByTagName(xmlNode,DaeSyntax.YFOV)))
		
		def SaveToXml(self, daeDocument):
			node  = super(DaeOptics.DaePerspective,self).SaveToXml(daeDocument)
			AppendTextChild(node.firstChild,DaeSyntax.XFOV, self.xfov)
			AppendTextChild(node.firstChild,DaeSyntax.YFOV, self.yfov)
			super(DaeOptics.DaePerspective,self).SavePropertiesToXml(daeDocument, node.firstChild)
			return node
		
		def __str__(self):
			return super(DaeOptics.DaePerspective,self).__str__()+' xfov: %s, yfov: %s'%(self.xfov, self.yfov)
			
	class DaeOrthoGraphic(DaeTechniqueCommon):
		def __init__(self):
			super(DaeOptics.DaeOrthoGraphic,self).__init__()
			self.xmag = None
			self.ymag = None
			self.syntax = DaeSyntax.ORTHOGRAPHIC
			
		def LoadFromXml(self, daeDocument, xmlNode):
			super(DaeOptics.DaeOrthoGraphic,self).LoadFromXml(daeDocument, xmlNode)
			self.xmag = ToFloat(ReadContents(FindElementByTagName(xmlNode,DaeSyntax.XMAG)))
			self.ymag = ToFloat(ReadContents(FindElementByTagName(xmlNode,DaeSyntax.YMAG)))
		
		def SaveToXml(self, daeDocument):
			node  = super(DaeOptics.DaeOrthoGraphic,self).SaveToXml(daeDocument)
			AppendTextChild(node.firstChild,DaeSyntax.XMAG, self.xmag)
			AppendTextChild(node.firstChild,DaeSyntax.YMAG, self.ymag)
			return node
		
		def __str__(self):
			return super(DaeOptics.DaeOrthoGraphic,self).__str__()+ 'xmag: %s, ymag: %s'%(self.xmag, self.ymag)

class DaeImager(DaeEntity):
	def __init__(self):
		super(DaeImager,self).__init__()
		self.techniques = []
		self.extras = None
		self.syntax = DaeSyntax.IMAGER
		
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaeImager, self).LoadFromXml(daeDocument, xmlNode)
		self.extras = CreateObjectsFromXml(daeDocument, xmlNode, DaeSyntax.EXTRA, DaeExtra)
		self.techniques = CreateObjectsFromXml(daeDocument, xmlNode, DaeSyntax.TECHNIQUE,DaeTechnique)
	
	def SaveToXml(self, daeDocument):
		node = super(DaeOptics, self).SaveToXml(daeDocument)
		# Add the techniques
		AppendChilds(daeDocument, node, self.techniques)
		# Add the extra's
		AppendChilds(self,node,self.extras)
		return node
		
	def __str__(self):
		return super(DaeImager,self).__str__()+' extras: %s, techniques: %s'%(self.techniqueCommon, self.techniques)
	
	
class DaeExtra(DaeEntity):
	def __init__(self):
		super(DaeExtra,self).__init__()
		self.type = None
		self.techniques = []
		self.syntax = DaeSyntax.EXTRA
		
	def LoadFromXml(self, daeDocument, xmlNode):
		self.type = xmlNode.getAttribute(DaeSyntax.TYPE)
		self.techniques = CreateObjectsFromXml(daeDocument, xmlNode,DaeSyntax.TECHNIQUE,DaeTechnique)
		
	def SaveToXml(self, daeDocument):
		node = super(DaeExtra,self).SaveToXml(daeDocument)
		AppendChilds(daeDocument, node, self.techniques)
		return node
		
		
	def __str__(self):
		return super(DaeExtra,self).__str__()+'techniques: %s'%(self.techniques)
	
class DaeAccessor(DaeEntity):
	def __init__(self):
		super(DaeAccessor,self).__init__()
		self.count = 0
		self.offset = None
		self.source = ''
		self.__stride = None
##		self.stride = property(self.GetStride)
		self.params = []
		
		self.syntax = DaeSyntax.ACCESSOR
	
	def LoadFromXml(self,daeDocument, xmlNode):
		self.count = CastAttributeFromXml(xmlNode, DaeSyntax.COUNT,int,0)
		self.offset = CastAttributeFromXml(xmlNode, DaeSyntax.OFFSET,int)
		self.source = ReadAttribute(xmlNode, DaeSyntax.SOURCE)
		self.stride = CastAttributeFromXml(xmlNode, DaeSyntax.STRIDE,int)
		self.params = CreateObjectsFromXml(daeDocument, xmlNode, DaeSyntax.PARAM, DaeParam)
		
	def SaveToXml(self, daeDocument):
		node = super(DaeAccessor,self).SaveToXml(daeDocument)
		node.setAttribute(DaeSyntax.COUNT, str(self.count))
		SetAttribute(node,DaeSyntax.OFFSET, self.offset)
		node.setAttribute(DaeSyntax.SOURCE, StripString('#'+self.source))
		SetAttribute(node, DaeSyntax.STRIDE, self.stride)
		AppendChilds(daeDocument, node, self.params)
		return node
	
	def AddParam(self, name, type):
		param = DaeParam()
		param.name = name
		param.type = type
		self.params.append(param)
	
	def GetStride(self):
		if self.__stride is None:
			return len(self.params)
		else:
			return self.__stride

	def SetStride(self, val):
		self.__stride = val
		
	def HasParam(self, paramName):
		return paramName in [param.name for param in self.params]


	stride = property(GetStride, SetStride)
	
class DaeParam(DaeEntity):
	def __init__(self):
		super(DaeParam,self).__init__()
		self.name = None
		self.semantic = None
		self.sid = None 
		self.type = ''	 
		self.syntax = DaeSyntax.PARAM
		
	def LoadFromXml(self, daeDocument, xmlNode):
		self.semantic = ReadAttribute(xmlNode, DaeSyntax.SEMANTIC)
		self.sid = ReadAttribute(xmlNode, DaeSyntax.SID)
		self.name = ReadAttribute(xmlNode, DaeSyntax.NAME)
		self.type = xmlNode.getAttribute(DaeSyntax.TYPE)
		
	def SaveToXml(self, daeDocument):
		node = super(DaeParam,self).SaveToXml(daeDocument)
		SetAttribute(node, DaeSyntax.SEMANTIC, self.semantic)
		SetAttribute(node, DaeSyntax.SID, self.sid)
		SetAttribute(node, DaeSyntax.NAME, self.name)
		node.setAttribute(DaeSyntax.TYPE, self.type)
		return node
	
class DaeArray(DaeElement):
	def __init__(self):
		super(DaeArray, self).__init__()
		self.count = 0
		self.data = []
		
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaeArray, self).LoadFromXml(daeDocument, xmlNode)
		self.count = ToInt(ReadAttribute(xmlNode, DaeSyntax.COUNT))
		self.data = ToList(ReadContents(xmlNode))
		
	def SaveToXml(self, daeDocument):
		node = super(DaeArray,self).SaveToXml(daeDocument)
		SetAttribute(node, DaeSyntax.COUNT, len(self.data))
		AppendTextInChild(node, self.data)
		return node
	
	def __str__(self):
		return super(DaeArray,self).__str__()+' count: %s'%(self.count)
		
	
class DaeFloatArray(DaeArray):
	def __init__(self):
		super(DaeFloatArray, self).__init__()
		self.syntax = DaeSyntax.FLOAT_ARRAY
		
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaeFloatArray, self).LoadFromXml(daeDocument, xmlNode)
		self.data = ToFloatList(self.data)
		
	
class DaeIntArray(DaeArray):
	def __init__(self):
		super(DaeIntArray, self).__init__()
		self.syntax = DaeSyntax.INT_ARRAY
		
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaeIntArray, self).LoadFromXml(daeDocument, xmlNode)
		self.data = ToIntList(self.data)
	
class DaeBoolArray(DaeArray):
	def __init__(self):
		super(DaeBoolArray, self).__init__()
		self.syntax = DaeSyntax.BOOL_ARRAY
		
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaeBoolArray, self).LoadFromXml(daeDocument, xmlNode)
		self.data = ToBoolList(self.data)
	
class DaeNameArray(DaeArray):
	def __init__(self):
		super(DaeNameArray, self).__init__()
		self.syntax = DaeSyntax.NAME_ARRAY
		
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaeNameArray, self).LoadFromXml(daeDocument, xmlNode)
		##self.data = ToFloatList(self.data)
	
class DaeIDREFArray(DaeArray):
	def __init__(self):
		super(DaeIDREFArray, self).__init__()
		self.syntax = DaeSyntax.IDREF_ARRAY
		
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaeIDREFArray, self).LoadFromXml(daeDocument, xmlNode)
		##self.data = ToFloatList(self.data)


#---Primitive Classes---
class DaePrimitive(DaeEntity):
	def __init__(self):
		super(DaePrimitive, self).__init__()
		self.name = None
		self.count = 0
		self.material = ''		  
		self.inputs = []
		
	def LoadFromXml(self, daeDocument, xmlNode):
		self.name = ReadAttribute(xmlNode, DaeSyntax.NAME)
		self.count = int(ReadAttribute(xmlNode, DaeSyntax.COUNT))
		self.material = ReadAttribute(xmlNode, DaeSyntax.MATERIAL)
		
	def SaveToXml(self, daeDocument):
		node = super(DaePrimitive, self).SaveToXml(daeDocument)
		SetAttribute(node, DaeSyntax.NAME, self.name)
		SetAttribute(node, DaeSyntax.MATERIAL, StripString(self.material))
		node.setAttribute(DaeSyntax.COUNT, str(self.count))
		return node
	
	def GetMaxOffset(self):
		if self.inputs != []:
			return max([i.offset for i in self.inputs])
		else:
			return None
		
	def FindInput(self, semantic):
		for i in self.inputs:
			if i.semantic == semantic:
				return i
		return None
		
class DaeLines(DaePrimitive):
	def __init__(self):
		super(DaeLines, self).__init__()
		self.syntax = DaeSyntax.LINES
		self.lines = []
		
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaeLines,self).LoadFromXml(daeDocument, xmlNode)
		self.syntax = DaeSyntax.LINES
		self.inputs = CreateObjectsFromXml(daeDocument, xmlNode, DaeSyntax.INPUT, DaeInput)
		self.lines = ToIntList(ReadContents(FindElementByTagName(xmlNode,DaeSyntax.P)))
	
	def SaveToXml(self, daeDocument):
		node = super(DaeLines,self).SaveToXml(daeDocument)
		AppendChilds(daeDocument, node, self.inputs)
		AppendTextChild(node, DaeSyntax.P, self.lines)
		return node
	
class DaeLineStrips(DaePrimitive):
	def __init__(self):
		super(DaeLineStrips, self).__init__()
		self.syntax = DaeSyntax.LINESTRIPS
		
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaeLineStrips,self).LoadFromXml(daeDocument, xmlNode)
		
		

class DaePolygons(DaePrimitive):
	def __init__(self):
		super(DaePolygons, self).__init__()
		self.syntax = DaeSyntax.POLYGONS
		self.polygons = []
		self.holedPolygons = []
		
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaePolygons,self).LoadFromXml(daeDocument, xmlNode)
		self.polygons = GetListFromNodes(xmlNode.getElementsByTagName(DaeSyntax.P), int)
		self.inputs = CreateObjectsFromXml(daeDocument, xmlNode, DaeSyntax.INPUT, DaeInput)
		
	def SaveToXml(self, daeDocument):
		node = super(DaePolygons,self).SaveToXml(daeDocument)
		AppendChilds(daeDocument, node, self.inputs)
		AppendChilds(node, DaeSyntax.P, self.polygons)
		return node 	   
	
class DaePolylist(DaePrimitive):
	def __init__(self):
		super(DaePolylist, self).__init__()
		self.syntax = DaeSyntax.POLYLIST
		
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaePolylist,self).LoadFromXml(daeDocument, xmlNode)
	
class DaeTriangles(DaePrimitive):
	def __init__(self):
		super(DaeTriangles, self).__init__()
		self.triangles = []
		self.syntax = DaeSyntax.TRIANGLES
		
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaeTriangles,self).LoadFromXml(daeDocument, xmlNode)
		self.triangles = ToIntList(ReadContents(FindElementByTagName(xmlNode,DaeSyntax.P)))
		self.inputs = CreateObjectsFromXml(daeDocument, xmlNode, DaeSyntax.INPUT, DaeInput)
		
	def SaveToXml(self, daeDocument):
		node = super(DaeTriangles,self).SaveToXml(daeDocument)
		AppendChilds(daeDocument, node, self.inputs)
		AppendTextChild(node, DaeSyntax.P, self.triangles)
		return node
	
class DaeTriFans(DaePrimitive):
	def __init__(self):
		super(DaeTriFans, self).__init__()
		self.syntax = DaeSyntax.TRIFANS
		
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaeTriFans,self).LoadFromXml(daeDocument, xmlNode)
	
class DaeTriStrips(DaePrimitive):
	def __init__(self):
		super(DaeTriStrips, self).__init__()
		self.syntax = DaeSyntax.TRISTRIPS
	
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaeTriStrips,self).LoadFromXml(daeDocument, xmlNode)
#---instance Classes---
class DaeInstance(DaeEntity):
	def __init__(self):
		super(DaeInstance, self).__init__()
		self.url = ''
		self.extras = []		
		self.object = None
		
	def LoadFromXml(self, daeDocument, xmlNode):
		self.url = ReadNodeUrl(xmlNode)
		self.extras = CreateObjectsFromXml(daeDocument, xmlNode, DaeSyntax.EXTRA, DaeExtra)
		
	def SaveToXml(self, daeDocument):
		node = super(DaeInstance,self).SaveToXml(daeDocument)
		AppendChilds(daeDocument, node, self.extras)
		WriteNodeUrl(node, self.object.id)
		return node
	
class DaeAnimationInstance(DaeInstance):
	def __init__(self):
		super(DaeAnimationInstance, self).__init__()		
		self.syntax = DaeSyntax.INSTANCE_ANIMATION
		
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaeAnimationInstance,self).LoadFromXml(daeDocument, xmlNode)
		self.object = daeDocument.animationsLibrary.FindObject(self.url)
		
	def SaveToXml(self, daeDocument):
		node = super(DaeAnimationInstance,self).SaveToXml(daeDocument)
		return node
	
class DaeCameraInstance(DaeInstance):
	def __init__(self):
		super(DaeCameraInstance, self).__init__()		 
		self.syntax = DaeSyntax.INSTANCE_CAMERA
		
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaeCameraInstance,self).LoadFromXml(daeDocument, xmlNode)
		self.object = daeDocument.camerasLibrary.FindObject(self.url)
		
	def SaveToXml(self, daeDocument):
		node = super(DaeCameraInstance,self).SaveToXml(daeDocument)
		return node
	
class DaeControllerInstance(DaeInstance):
	def __init__(self):
		super(DaeControllerInstance, self).__init__()		 
		self.skeletons = []
		self.bindMaterials = []
		self.syntax = DaeSyntax.INSTANCE_CONTROLLER
		
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaeControllerInstance,self).LoadFromXml(daeDocument, xmlNode)
		self.skeletons = CreateObjectsFromXml(daeDocument, xmlNode, DaeSyntax.SKELETON, DaeSkeleton)
		self.bindMaterials = CreateObjectsFromXml(daeDocument, xmlNode, DaeFxSyntax.BIND_MATERIAL, DaeFxBindMaterial)
		self.object = daeDocument.controllersLibrary.FindObject(self.url)
		
	def SaveToXml(self, daeDocument):
		node = super(DaeControllerInstance,self).SaveToXml(daeDocument)
		AppendChilds(daeDocument, node, self.skeletons)
		AppendChilds(daeDocument, node, self.bindMaterials)
		return node
	
# TODO:  Collada API: finish DaeEffectInstance
class DaeEffectInstance(DaeInstance):
	def __init__(self):
		super(DaeEffectInstance, self).__init__()		 
		
		self.syntax = DaeSyntax.INSTANCE_EFFECT
		
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaeEffectInstance,self).LoadFromXml(daeDocument, xmlNode)
		self.object = daeDocument.effectsLibrary.FindObject(self.url)
		
	def SaveToXml(self, daeDocument):
		node = super(DaeEffectInstance,self).SaveToXml(daeDocument)
		return node
	
class DaeGeometryInstance(DaeInstance):
	def __init__(self):
		super(DaeGeometryInstance, self).__init__()
		self.bindMaterials = []
		self.syntax = DaeSyntax.INSTANCE_GEOMETRY
		
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaeGeometryInstance,self).LoadFromXml(daeDocument, xmlNode)
		self.bindMaterials = CreateObjectsFromXml(daeDocument, xmlNode, DaeFxSyntax.BIND_MATERIAL, DaeFxBindMaterial)
		self.object = daeDocument.geometriesLibrary.FindObject(self.url)
		
	def SaveToXml(self, daeDocument):
		node = super(DaeGeometryInstance,self).SaveToXml(daeDocument)
		AppendChilds(daeDocument, node, self.bindMaterials)
		return node
	
class DaeLightInstance(DaeInstance):
	def __init__(self):
		super(DaeLightInstance, self).__init__()		   
		self.syntax = DaeSyntax.INSTANCE_LIGHT
		
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaeLightInstance,self).LoadFromXml(daeDocument, xmlNode)
		self.object = daeDocument.lightsLibrary.FindObject(self.url)
		
	def SaveToXml(self, daeDocument):
		node = super(DaeLightInstance,self).SaveToXml(daeDocument)
		return node
	
class DaeNodeInstance(DaeInstance):
	def __init__(self):
		super(DaeNodeInstance, self).__init__() 	   
		self.syntax = DaeSyntax.INSTANCE_NODE
		
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaeNodeInstance,self).LoadFromXml(daeDocument, xmlNode)
		self.object = daeDocument.nodesLibrary.FindObject(self.url)
		
	def SaveToXml(self, daeDocument):
		node = super(DaeNodeInstance,self).SaveToXml(daeDocument)
		return node

class DaeVisualSceneInstance(DaeInstance):
	def __init__(self):
		super(DaeVisualSceneInstance, self).__init__()		  
		self.syntax = DaeSyntax.INSTANCE_VISUAL_SCENE
		
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaeVisualSceneInstance,self).LoadFromXml(daeDocument, xmlNode)
		self.object = daeDocument.visualScenesLibrary.FindObject(self.url)
		
	def SaveToXml(self, daeDocument):
		node = super(DaeVisualSceneInstance,self).SaveToXml(daeDocument)
		return node
		
	
class DaeSkeleton(DaeEntity):
	def __init__(self):
		super(DaeSkeleton,self).__init__()
		self.iControllers = []
	
	def LoadFromXml(self, daeDocument, xmlNode):
		self.iControllers = CreateObjectsFromXml(daeDocument, xmlNode, DaeSyntax.INSTANCE_CONTROLLER, DaeControllerInstance)
		
	def SaveToXml(self, daeDocument):
		node = super(DaeSkeleton, self).SaveToXml(daeDocument)
		AppendChilds(daeDocument, node, self.iControllers)
		return node


class DaeSyntax(object):
	
	#---collada---
	COLLADA = 'COLLADA'
	VERSION = 'version'
	XMLNS = 'xmlns'
	
	BODY = 'body'
	TARGET = 'target'
	
	ASSET = 'asset'
	
	ID = 'id'
	NAME = 'name'
	URL = 'url'
	
	COUNT = 'count'
	OFFSET = 'offset'
	STRIDE = 'stride'
	
	METER = 'meter'
	SID = 'sid'
	SEMANTIC = 'semantic'
	PARAM = 'param'
	
	PROFILE = 'profile'
	TECHNIQUE = 'technique'
	TECHNIQUE_COMMON = 'technique_common'
	
	##BIND_MATERIAL = 'bind_material'
	SKELETON = 'skeleton'
	
	P = 'p'
	PH = 'ph'
	H = 'h'
	
	
	INPUT = 'input'
	SET  = 'set'
	
	#---light---
	COLOR = 'color'
	AMBIENT = 'ambient'
	SPOT = 'spot'
	DIRECTIONAL = 'directional'
	POINT = 'point'
	
	CONSTANT_ATTENUATION = 'constant_attenuation'
	LINEAR_ATTENUATION = 'linear_attenuation'
	QUADRATIC_ATTENUATION = 'quadratic_attenuation'
	
	FALLOFF_ANGLE = 'falloff_angle'
	FALLOFF_EXPONENT = 'falloff_exponent'
	
	#---camera--
	OPTICS = 'optics'
	PERSPECTIVE = 'perspective'
	ORTHOGRAPHIC = 'orthographic'
	IMAGER = 'imager'
	ZNEAR = 'znear'
	ZFAR = 'zfar'
	XFOV = 'xfov'
	YFOV = 'yfov'
	XMAG = 'xmag'
	YMAG ='ymag'
	ASPECT_RATIO = 'aspect_ratio'

	#---geometry---
	MESH = 'mesh'
	CONVEX_MESH ='convex_mesh'
	SPLINE = 'spline'
	SOURCE	='source'
	VERTICES = 'vertices'
	ACCESSOR = 'accessor'
	
	CONVEX_HULL_OF = 'convex_hull_of'

	#---primitives---
	LINES = 'lines'
	LINESTRIPS = 'linestrips'
	POLYGONS = 'polygons'
	POLYLIST = 'polylist'
	TRIANGLES = 'triangles'
	TRIFANS = 'trifans'
	TRISTRIPS = 'tristrips'
	
	#---libraries---
	LIBRARY_ANIMATIONS = 'library_animations'
	LIBRARY_ANIMATION_CLIPS = 'library_animation_clips'
	LIBRARY_CAMERAS = 'library_cameras'
	LIBRARY_CONTROLLERS = 'library_controllers'
	LIBRARY_EFFECTS = 'library_effects'
	LIBRARY_FORCE_FIELDS = 'library_force_fields'
	LIBRARY_GEOMETRIES = 'library_geometries'
	LIBRARY_IMAGES = 'library_images'
	LIBRARY_LIGHTS = 'library_lights'
	LIBRARY_MATERIALS = 'library_materials'
	LIBRARY_NODES = 'library_NODES'
	LIBRARY_PHYSICS_MATERIALS = 'library_physics_materials'
	LIBRARY_PHYSICS_MODELS = 'library_physics_models'
	LIBRARY_PHYSICS_SCENES = 'library_physics_scenes'
	LIBRARY_VISUAL_SCENES = 'library_visual_scenes'
	
	SCENE = 'scene'
	EXTRA = 'extra'
	TYPE = 'type'
	LIGHT = 'light'
	CAMERA = 'camera'
	ANIMATION = 'animation'
	ANIMATION_CLIP = 'animation_clip'
	GEOMETRY = 'geometry'
	IMAGE = 'image'
	##EFFECT = 'effect'
	VISUAL_SCENE = 'visual_scene'
	CONTROLLER = 'controller'
	MATERIAL = 'material'
	
	#---asset---
	CONTRIBUTOR = 'contributor'
	CREATED = 'created'
	MODIFIED = 'modified'
	REVISION = 'revision'
	TITLE = 'title'
	SUBJECT = 'subject'
	KEYWORDS = 'keywords'
	UNIT = 'unit'
	UP_AXIS = 'up_axis'
	
	Y_UP = 'Y_UP'
	Z_UP = 'Z_UP'
	
	#---contributor---
	AUTHOR = 'author'
	AUTHORING_TOOL = 'authoring_tool'
	COMMENTS = 'comments'
	COPYRIGHT = 'copyright'
	SOURCE_DATA = 'source_data'
	
	#---array---
	FLOAT_ARRAY = 'float_array'
	NAME_ARRAY = 'Name_array'
	BOOL_ARRAY = 'bool_array'
	INT_ARRAY = 'int_array'
	IDREF_ARRAY = 'IDREF_array'
	
	#---node---
	NODE = 'node'
	TYPE_JOINT = 'JOINT'
	TYPE_NODE = 'NODE'
	LAYER = 'layer'
	
	#---transforms---
	TRANSLATE = 'translate'
	ROTATE = 'rotate'
	SCALE = 'scale'
	SKEW = 'skew'
	MATRIX = 'matrix'
	LOOKAT = 'lookat'
	
	#---instances---
	INSTANCE_ANIMATION = 'instance_animation'
	INSTANCE_CAMERA = 'instance_camera'
	INSTANCE_CONTROLLER = 'instance_controller'
	##INSTANCE_EFFECT = 'instance_effect'
	INSTANCE_GEOMETRY = 'instance_geometry'
	INSTANCE_LIGHT = 'instance_light'
	INSTANCE_NODE = 'instance_node'
	INSTANCE_VISUAL_SCENE = 'instance_visual_scene'
	INSTANCE_PHYSICS_SCENE = 'instance_physics_scene'
	
	#---image---
	FORMAT = 'format'
	DEPTH = 'depth'
	HEIGHT = 'height'
	WIDTH = 'width'
	INIT_FROM = 'init_from'
	
	#---animation---
	SAMPLER = 'sampler'
	CHANNEL = 'channel'

class DaeFxBindMaterial(DaeEntity):
	def __init__(self):
		super(DaeFxBindMaterial, self).__init__()
		self.syntax = DaeFxSyntax.BIND_MATERIAL
		self.techniqueCommon = DaeFxBindMaterial.DaeFxTechniqueCommon() 	   
		
	def LoadFromXml(self, daeDocument, xmlNode):
		self.techniqueCommon = CreateObjectFromXml(daeDocument, xmlNode, DaeFxSyntax.TECHNIQUE_COMMON, DaeFxBindMaterial.DaeFxTechniqueCommon)
		
	def SaveToXml(self, daeDocument):
		node = super(DaeFxBindMaterial,self).SaveToXml(daeDocument)
		AppendChild(daeDocument, node, self.techniqueCommon)
		return node
		
	class DaeFxTechniqueCommon(DaeEntity):
		def __init__(self): 		   
			self.syntax = DaeFxSyntax.TECHNIQUE_COMMON
			self.iMaterials = []
			
		def LoadFromXml(self, daeDocument, xmlNode):
			self.iMaterials = CreateObjectsFromXml(daeDocument, xmlNode, DaeFxSyntax.INSTANCE_MATERIAL, DaeFxMaterialInstance)
			
		def SaveToXml(self, daeDocument):
			node = super(DaeFxBindMaterial.DaeFxTechniqueCommon,self).SaveToXml(daeDocument)
			AppendChilds(daeDocument, node, self.iMaterials)
			return node
		
		def __str__(self):
			return super(DaeFxBindMaterial.DaeFxTechniqueCommon,self).__str__()

		
class DaeFxMaterialInstance(DaeEntity):
	def __init__(self):
		super(DaeFxMaterialInstance, self).__init__()
		self.target = ''
		self.symbol = ''
		self.object = None
		self.syntax = DaeFxSyntax.INSTANCE_MATERIAL
		
	def LoadFromXml(self, daeDocument, xmlNode):
		self.target = ReadAttribute(xmlNode, DaeFxSyntax.TARGET)[1:]
		self.symbol = ReadAttribute(xmlNode, DaeFxSyntax.SYMBOL)
		self.object = daeDocument.materialsLibrary.FindObject(self.target)
		
	def SaveToXml(self, daeDocument):
		node = super(DaeFxMaterialInstance,self).SaveToXml(daeDocument)
		SetAttribute(node, DaeFxSyntax.TARGET, StripString('#'+self.object.id))
		SetAttribute(node, DaeFxSyntax.SYMBOL, StripString(self.object.id))
		return node

	def __str__(self):
		return super(DaeFxMaterialInstance,self).__str__()+' target: %s, symbol: %s'%(self.target, self.symbol)
		
class DaeFxMaterial(DaeElement):
	def __init__(self):
		super(DaeFxMaterial, self).__init__()
		self.asset = None
		self.iEffects = []
		self.extras = None
		self.syntax = DaeFxSyntax.MATERIAL
		
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaeFxMaterial, self).LoadFromXml(daeDocument, xmlNode)
		self.extras = CreateObjectsFromXml(daeDocument, xmlNode, DaeSyntax.EXTRA, DaeExtra)
		self.asset = CreateObjectFromXml(daeDocument, xmlNode, DaeSyntax.ASSET, DaeAsset)
		self.iEffects = CreateObjectsFromXml(daeDocument,xmlNode, DaeFxSyntax.INSTANCE_EFFECT, DaeFxEffectInstance)
		
	def SaveToXml(self, daeDocument):
		node = super(DaeFxMaterial,self).SaveToXml(daeDocument)
		# Add the assets
		AppendChild(daeDocument,node,self.asset)
		# Add the effect instances
		AppendChilds(daeDocument, node, self.iEffects)
		# Add the extra's
		AppendChilds(self,node,self.extras)
		return node
		
	def __str__(self):
		return super(DaeFxMaterial,self).__str__()+' assets: %s, iEffects: %s, extras: %s'%(self.asset, self.iEffects, self.extras)

class DaeFxEffectInstance(DaeEntity):
	def __init__(self):
		super(DaeFxEffectInstance, self).__init__()
		self.url = ''
		self.syntax = DaeFxSyntax.INSTANCE_EFFECT
	
	def LoadFromXml(self, daeDocument, xmlNode):
		self.url = ReadAttribute(xmlNode, DaeFxSyntax.URL)[1:]
		self.object = daeDocument.effectsLibrary.FindObject(self.url)
		
	def SaveToXml(self, daeDocument):
		node = super(DaeFxEffectInstance,self).SaveToXml(daeDocument)
		SetAttribute(node, DaeFxSyntax.URL, StripString('#'+self.object.id))
		return node
	
class DaeFxEffect(DaeElement):
	def __init__(self):
		super(DaeFxEffect, self).__init__()
		self.profileCommon = DaeFxProfileCommon()
		self.syntax = DaeFxSyntax.EFFECT
		
	
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaeFxEffect, self).LoadFromXml(daeDocument, xmlNode)
		self.profileCommon = CreateObjectFromXml(daeDocument, xmlNode, DaeFxSyntax.PROFILE_COMMON, DaeFxProfileCommon)
		
	def SaveToXml(self, daeDocument):
		node = super(DaeFxEffect,self).SaveToXml(daeDocument)
		AppendChild(daeDocument, node, self.profileCommon)
		return node
	
	def __str__(self):
		return super(DaeFxEffect, self).__str__() + ', profileCommon: %s' % (self.profileCommon)
	
	def AddShader(self, daeShader):
		self.profileCommon.technique.shader = daeShader
	
class DaeFxProfileCommon(DaeEntity):
	def __init__(self):
		super(DaeFxProfileCommon, self).__init__()
		self.technique = DaeFxTechnique()
		self.images = []
		self.newParams = []
		self.syntax = DaeFxSyntax.PROFILE_COMMON
		
	
	def LoadFromXml(self, daeDocument, xmlNode):
		self.images = CreateObjectsFromXml(daeDocument, xmlNode, DaeFxSyntax.IMAGE, DaeFxImage)
		self.newParams = CreateObjectsFromXml(daeDocument, xmlNode, DaeFxSyntax.NEWPARAM, DaeFxNewParam)
		self.technique = CreateObjectFromXml(daeDocument, xmlNode, DaeFxSyntax.TECHNIQUE, DaeFxTechnique)
		
	def SaveToXml(self, daeDocument):
		node = super(DaeFxProfileCommon,self).SaveToXml(daeDocument)
		AppendChilds(daeDocument, node, self.images)
		AppendChilds(daeDocument, node, self.newParams)
		AppendChild(daeDocument, node, self.technique)
		return node
	
	def __str__(self):
		return super(DaeFxProfileCommon, self).__str__() + ', technique: %s, images: %s, newParams: %s' % (self.technique, self.images, self.newParams)

class DaeFxImage(DaeEntity):
	def __init__(self):
		super(DaeFxImage, self).__init__()
		self.syntax = DaeFxSyntax.IMAGE
		
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaeFxImage, self).LoadFromXml(daeDocument, xmlNode)
		
	def SaveToXml(self, daeDocument):
		node = super(DaeFxImage,self).SaveToXml(daeDocument)
		return node
	
class DaeFxNewParam(DaeEntity):
	def __init__(self):
		super(DaeFxNewParam, self).__init__()
		self.syntax = DaeFxSyntax.NEWPARAM
		
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaeFxNewParam, self).LoadFromXml(daeDocument, xmlNode)
		
	def SaveToXml(self, daeDocument):
		node = super(DaeFxNewParam,self).SaveToXml(daeDocument)
		return node
	
class DaeFxTechnique(DaeEntity):
	def __init__(self):
		super(DaeFxTechnique, self).__init__()
		self.syntax = DaeFxSyntax.TECHNIQUE
		self.shader = DaeFxShadeConstant()
		self.sid = ''
		
	def LoadFromXml(self, daeDocument, xmlNode):
		# TODO:  Collada API: add asset and extra?
		self.sid = ReadAttribute(xmlNode, DaeFxSyntax.SID)
		lightSourceNode = FindElementByTagName(xmlNode, DaeFxSyntax.CONSTANT)
		if lightSourceNode:
			self.shader = CreateObjectFromXml(daeDocument, xmlNode, DaeFxSyntax.CONSTANT, DaeFxShadeConstant)			 
		else:
			lightSourceNode = FindElementByTagName(xmlNode, DaeFxSyntax.LAMBERT)
			if lightSourceNode:
				self.shader = CreateObjectFromXml(daeDocument, xmlNode, DaeFxSyntax.LAMBERT, DaeFxShadeLambert)
			else:
				lightSourceNode = FindElementByTagName(xmlNode, DaeFxSyntax.BLINN)
				if lightSourceNode:
					self.shader = CreateObjectFromXml(daeDocument, xmlNode, DaeFxSyntax.BLINN, DaeFxShadeBlinn)
				else:
					lightSourceNode = FindElementByTagName(xmlNode, DaeFxSyntax.PHONG)
					self.shader = CreateObjectFromXml(daeDocument, xmlNode, DaeFxSyntax.PHONG, DaeFxShadePhong)
		
		
	def SaveToXml(self, daeDocument):
		node = super(DaeFxTechnique,self).SaveToXml(daeDocument)
		node.setAttribute(DaeFxSyntax.SID, self.sid)
		AppendChild(daeDocument, node, self.shader)
		return node
	
	def __str__(self):
		return super(DaeFxTechnique,self).__str__()+' shader: %s'%(self.shader)


class DaeFxShadeConstant(DaeEntity):
	def __init__(self):
		super(DaeFxShadeConstant, self).__init__()
		self.emission = None
		self.reflective = None
		self.reflectivity = None
		self.transparent = None
		self.transparency = None
		self.indexOfRefraction = None
			
		self.syntax = DaeFxSyntax.CONSTANT
		
	def LoadFromXml(self, daeDocument, xmlNode):
		self.emission = CreateObjectFromXml(daeDocument, xmlNode, DaeFxSyntax.EMISSION, DaeFxCommonColorAndTextureContainer, True)
		self.reflective = CreateObjectFromXml(daeDocument, xmlNode, DaeFxSyntax.REFLECTIVE, DaeFxCommonColorAndTextureContainer, True)
		self.reflectivity = CreateObjectFromXml(daeDocument, xmlNode, DaeFxSyntax.REFLECTIVITY, DaeFxCommonFloatAndParamContainer, True)
		self.transparent = CreateObjectFromXml(daeDocument, xmlNode, DaeFxSyntax.TRANSPARENT, DaeFxCommonColorAndTextureContainer, True)
		self.transparency = CreateObjectFromXml(daeDocument, xmlNode, DaeFxSyntax.TRANSPARENCY, DaeFxCommonFloatAndParamContainer, True)
		self.indexOfRefraction = CreateObjectFromXml(daeDocument, xmlNode, DaeFxSyntax.INDEXOFREFRACTION, DaeFxCommonFloatAndParamContainer, True)
		
	def SaveToXml(self, daeDocument):
		node = super(DaeFxShadeConstant,self).SaveToXml(daeDocument)
		AppendChild(daeDocument, node, self.emission)
		if isinstance(self, DaeFxShadeLambert):
			AppendChild(daeDocument, node, self.ambient)
			AppendChild(daeDocument, node, self.diffuse)
			if isinstance(self,DaeFxShadeBlinn):
				AppendChild(daeDocument, node, self.specular)
				AppendChild(daeDocument, node, self.shininess)
		AppendChild(daeDocument, node, self.reflective)
		AppendChild(daeDocument, node, self.reflectivity)
		AppendChild(daeDocument, node, self.transparent)
		AppendChild(daeDocument, node, self.transparency)
		AppendChild(daeDocument, node, self.indexOfRefraction)
		return node
	
	def AddValue(self, type, val):
		col = DaeFxColor()
		col.rgba = val
		if type == DaeFxSyntax.EMISSION:
			if not self.emission:
				self.emission = DaeFxCommonColorAndTextureContainer(type)
			self.emission.color = col
		elif type == DaeFxSyntax.REFLECTIVE:
			if not self.reflective:
				self.reflective = DaeFxCommonColorAndTextureContainer(type)
			self.reflective.color = col
		elif type == DaeFxSyntax.REFLECTIVITY:
			if not self.reflectivity:
				self.reflectivity = DaeFxCommonFloatAndParamContainer(type)
			self.reflectivity.float = val
		elif type == DaeFxSyntax.TRANSPARENT:
			if not self.transparent:
				self.transparent = DaeFxCommonColorAndTextureContainer(type)
			self.transparent.color = col
		elif type == DaeFxSyntax.TRANSPARENCY:
			if not self.transparency:
				self.transparency = DaeFxCommonFloatAndParamContainer(type)
			self.transparency.float = val
		elif type == DaeFxSyntax.INDEXOFREFRACTION:
			if not self.indexOfRefraction:
				self.indexOfRefraction = DaeFxCommonFloatAndParamContainer(type)
			self.indexOfRefraction.float = val
		else:
			Debug.Debug('DaeFxShadeConstant: type: %s not recognised'%(type),'ERROR')

		
	
class DaeFxShadeLambert(DaeFxShadeConstant):
	def __init__(self):
		super(DaeFxShadeLambert, self).__init__()
		self.ambient = None
		self.diffuse = None
		self.syntax = DaeFxSyntax.LAMBERT
		
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaeFxShadeLambert, self).LoadFromXml(daeDocument, xmlNode)
		self.ambient = CreateObjectFromXml(daeDocument, xmlNode, DaeFxSyntax.AMBIENT, DaeFxCommonColorAndTextureContainer, True)
		self.diffuse = CreateObjectFromXml(daeDocument, xmlNode, DaeFxSyntax.DIFFUSE, DaeFxCommonColorAndTextureContainer, True)
		
		
	def SaveToXml(self, daeDocument):
		node = super(DaeFxShadeLambert,self).SaveToXml(daeDocument)
		#AppendChild(daeDocument, node, self.ambient)
		#AppendChild(daeDocument, node, self.diffuse)
		return node
	
	def AddValue(self, type, val):
		col = DaeFxColor()
		col.rgba = val
		if type == DaeFxSyntax.DIFFUSE:
			if not self.diffuse:
				self.diffuse = DaeFxCommonColorAndTextureContainer(type)
			if isinstance(val, DaeFxTexture): # its a texture
				self.diffuse.texture = val
			else: # it's a color
				self.diffuse.color = col
		elif type == DaeFxSyntax.AMBIENT:
			if not self.ambient:
				self.ambient = DaeFxCommonColorAndTextureContainer(type)
			self.ambient.color = col
		else:
			super(DaeFxShadeLambert,self).AddValue(type, val)
			
class DaeFxShadeBlinn(DaeFxShadeLambert):
	def __init__(self):
		super(DaeFxShadeBlinn, self).__init__()
		self.specular = None
		self.shininess = None
		self.syntax = DaeFxSyntax.BLINN
		
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaeFxShadeBlinn, self).LoadFromXml(daeDocument, xmlNode)
		self.specular = CreateObjectFromXml(daeDocument, xmlNode, DaeFxSyntax.SPECULAR, DaeFxCommonColorAndTextureContainer, True)
		self.shininess = CreateObjectFromXml(daeDocument, xmlNode, DaeFxSyntax.SHININESS, DaeFxCommonFloatAndParamContainer, True)
		
		
	def SaveToXml(self, daeDocument):
		node = super(DaeFxShadeBlinn,self).SaveToXml(daeDocument)
		#AppendChild(daeDocument, node, self.specular)
		#AppendChild(daeDocument, node, self.shininess)
		return node
	
	def AddValue(self, type, val):
		col = DaeFxColor()
		col.rgba = val
		if type == DaeFxSyntax.SPECULAR:
			if not self.specular:
				self.specular = DaeFxCommonColorAndTextureContainer(type)
			self.specular.color = col
		elif type == DaeFxSyntax.SHININESS:
			if not self.shininess:
				self.shininess = DaeFxCommonFloatAndParamContainer(type)
			self.shininess.float = val
		else:
			super(DaeFxShadeBlinn,self).AddValue(type, val)
			
class DaeFxShadePhong(DaeFxShadeBlinn):
	def __init__(self):
		super(DaeFxShadePhong, self).__init__()
		self.syntax = DaeFxSyntax.PHONG
	
class DaeFxCommonColorAndTextureContainer(DaeEntity):
	def __init__(self, syntax='UNKNOWN'):
		super(DaeFxCommonColorAndTextureContainer, self).__init__()
		self.color = None
		self.texture = None
		self.syntax = syntax
		
	def LoadFromXml(self, daeDocument, xmlNode):
		self.color = CreateObjectFromXml(daeDocument, xmlNode, DaeFxSyntax.COLOR, DaeFxColor)
		self.texture = CreateObjectFromXml(daeDocument, xmlNode, DaeFxSyntax.TEXTURE, DaeFxTexture)
		
	def SaveToXml(self, daeDocument):
		node = super(DaeFxCommonColorAndTextureContainer,self).SaveToXml(daeDocument)
		AppendChild(daeDocument, node, self.color)
		AppendChild(daeDocument, node, self.texture)
		return node
	
class DaeFxCommonFloatAndParamContainer(DaeEntity):
	def __init__(self, syntax = 'UNKNOWN'):
		super(DaeFxCommonFloatAndParamContainer, self).__init__()
		self.float = None
		self.param = None
		self.syntax = syntax
		
	def LoadFromXml(self, daeDocument, xmlNode):
		self.float = CastFromXml(daeDocument, xmlNode, DaeFxSyntax.FLOAT, float)
		##self.param = CreateObjectFromXml(daeDocument, xmlNode, DaeFxSyntax.PARAM, DaeFxParam)
		
	def SaveToXml(self, daeDocument):
		node = super(DaeFxCommonFloatAndParamContainer,self).SaveToXml(daeDocument)
		AppendTextChild(node, DaeFxSyntax.FLOAT, self.float)
		AppendChild(daeDocument, node, self.param)
		return node

class DaeFxColor(DaeEntity):
	def __init__(self):
		super(DaeFxColor, self).__init__()
		self.sid = ''
		self.rgba = []
		self.syntax = DaeFxSyntax.COLOR
		
	def LoadFromXml(self, daeDocument, xmlNode):
		self.sid = ReadAttribute(xmlNode, DaeFxSyntax.SID)
		self.rgba = ToFloatList(ReadContents(xmlNode))
		
	def SaveToXml(self, daeDocument):
		node = super(DaeFxColor,self).SaveToXml(daeDocument)
		SetAttribute(node, DaeFxSyntax.SID, self.sid)
		AppendTextInChild(node, self.rgba)
		return node
	
class DaeFxTexture(DaeEntity):
	def __init__(self):
		super(DaeFxTexture, self).__init__()
		self.texture = ''
		self.textCoord = ''
		self.syntax = DaeFxSyntax.TEXTURE
		
	def LoadFromXml(self, daeDocument, xmlNode):
		self.texture = daeDocument.imagesLibrary.FindObject(ReadAttribute(xmlNode, DaeFxSyntax.TEXTURE))
		self.textCoord = ReadAttribute(xmlNode, DaeFxSyntax.TEXCOORD)
		
	def SaveToXml(self, daeDocument):
		node = super(DaeFxTexture,self).SaveToXml(daeDocument)
		SetAttribute(node, DaeFxSyntax.TEXTURE, StripString(self.texture))
		SetAttribute(node, DaeFxSyntax.TEXCOORD, self.textCoord)
		return node
	
class DaeFxSyntax(object):
	COLOR = 'color'  
	INSTANCE_MATERIAL = 'instance_material'
	INSTANCE_EFFECT = 'instance_effect'
	TECHNIQUE_COMMON = 'technique_common'
	SID = 'sid'
	EMISSION = 'emission'
	REFLECTIVE ='reflective'
	REFLECTIVITY = 'reflectivity'	 
	TRANSPARENT = 'transparent'
	TRANSPARENCY = 'transparency'
	INDEXOFREFRACTION = 'index_of_refraction'
	TEXTURE = 'texture'
	TEXCOORD = 'texcoord'
	AMBIENT = 'ambient'
	DIFFUSE = 'diffuse'    
	
	BIND_MATERIAL ='bind_material'
	PROFILE_COMMON = 'profile_COMMON'
	SYMBOL = 'symbol'
	MATERIAL = 'material'
	EFFECT = 'effect'
	
	TARGET = 'target'
	URL = 'url'
	SYMBOL = 'symbol'
	
	BLINN = 'blinn'
	SHININESS = 'shininess'
	SPECULAR = 'specular'
	PHONG = 'phong'
	
	IMAGE = 'image'
	NEWPARAM = 'newparam'
	TECHNIQUE = 'technique'
	
	CONSTANT = 'constant'
	LAMBERT = 'lambert'
	
	FLOAT ='float'
#---COLLADA PHYSICS---
class DaePhysicsScene(DaeElement):
	def __init__(self):
		super(DaePhysicsScene,self).__init__()
		self.asset = None
		self.extras = None
		self.iPhysicsModels = []
		self.syntax = DaePhysicsSyntax.PHYSICS_SCENE	   
		
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaePhysicsScene, self).LoadFromXml(daeDocument, xmlNode)
		self.extras = CreateObjectsFromXml(daeDocument, xmlNode, DaeSyntax.EXTRA, DaeExtra)
		self.asset = CreateObjectFromXml(daeDocument, xmlNode, DaeSyntax.ASSET, DaeAsset)
		self.iPhysicsModels = CreateObjectsFromXml(daeDocument, xmlNode, DaePhysicsSyntax.INSTANCE_PHYSICS_MODEL, DaePhysicsModelInstance)
		
	def SaveToXml(self, daeDocument):
		node = super(DaePhysicsScene, self).SaveToXml(daeDocument)
		# Add the assets
		AppendChild(daeDocument,node,self.asset)
		# Add the phyics models
		AppendChilds(daeDocument, node, self.iPhysicsModels)
		# Add the extra's
		AppendChilds(self,node,self.extras)
		return node
		
	def __str__(self):
		return super(DaePhysicsScene,self).__str__()+' asset: %s, iPhysicsModels: %s, extras: %s'%(self.asset, self.iPhysicsModels, self.extras)
 
class DaePhysicsModelInstance(DaeInstance):
	def __init__(self):
		super(DaePhysicsModelInstance, self).__init__() 	   
		self.syntax = DaePhysicsSyntax.INSTANCE_PHYSICS_MODEL
		self.iRigidBodies = []
		
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaePhysicsModelInstance,self).LoadFromXml(daeDocument, xmlNode)
		self.object = daeDocument.physicsModelsLibrary.FindObject(self.url)
		self.iRigidBodies = self.CreateInstanceRigidBodies(daeDocument, xmlNode, self.object)
		
	def SaveToXml(self, daeDocument):
		node = super(DaePhysicsModelInstance,self).SaveToXml(daeDocument)
		AppendChilds(daeDocument, node, self.iRigidBodies)
		return node
	
	def CreateInstanceRigidBodies(self, daeDocument, xmlNode, physicsModel):
		objects = []
		CreateObjectsFromXml(daeDocument, xmlNode, DaePhysicsSyntax.INSTANCE_RIGID_BODY, DaeRigidBodyInstance)
		nodes = FindElementsByTagName(xmlNode,DaePhysicsSyntax.INSTANCE_RIGID_BODY)
		for node in nodes:
			object = DaeRigidBodyInstance()
			object.LoadFromXml(daeDocument, node)
			object.body = physicsModel.FindRigidBody(object.bodyString)
			n = None
			for visualScene in daeDocument.visualScenesLibrary.items:
				n = visualScene.FindNode(object.targetString)
				if not (n is None):
					break
			object.target = n
			objects.append(object)
		return objects
		
	
class DaePhysicsSceneInstance(DaeInstance):
	def __init__(self):
		super(DaePhysicsSceneInstance, self).__init__()
		self.syntax = DaeSyntax.INSTANCE_PHYSICS_SCENE
		
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaePhysicsSceneInstance,self).LoadFromXml(daeDocument, xmlNode)
		self.object = daeDocument.physicsScenesLibrary.FindObject(self.url)
		
	def SaveToXml(self, daeDocument):
		node = super(DaePhysicsSceneInstance,self).SaveToXml(daeDocument)
		return node
	
class DaePhysicsMaterialInstance(DaeInstance):
	def __init__(self):
		super(DaePhysicsMaterialInstance, self).__init__()		  
		self.syntax = DaePhysicsSyntax.INSTANCE_PHYSICS_MATERIAL
		
	def LoadFromXml(self, daeDocument, xmlNode):		
		super(DaePhysicsMaterialInstance,self).LoadFromXml(daeDocument, xmlNode)
		self.object = daeDocument.physicsMaterialsLibrary.FindObject(self.url)
		
	def SaveToXml(self, daeDocument):
		node = super(DaePhysicsMaterialInstance,self).SaveToXml(daeDocument)
		return node
	
class DaeRigidBodyInstance(DaeEntity):
	def __init__(self):
		super(DaeRigidBodyInstance, self).__init__()		
		self.syntax = DaePhysicsSyntax.INSTANCE_RIGID_BODY
		self.body = None
		self.target = None
		self.bodyString = ''
		self.targetString = ''
		
	def LoadFromXml(self, daeDocument, xmlNode):		
		self.bodyString = ReadAttribute(xmlNode, DaeSyntax.BODY)
		self.targetString = ReadAttribute(xmlNode, DaeSyntax.TARGET)[1:]
		
	def SaveToXml(self, daeDocument):
		node = super(DaeRigidBodyInstance,self).SaveToXml(daeDocument)
		SetAttribute(node, DaeSyntax.BODY, self.body.sid)
		SetAttribute(node, DaeSyntax.TARGET, StripString('#'+self.target.id))		 
		return node
	
class DaePhysicsModel(DaeElement):
	def __init__(self):
		super(DaePhysicsModel,self).__init__()
		self.syntax = DaePhysicsSyntax.PHYSICS_MODEL
		self.rigidBodies = []
	
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaePhysicsModel, self).LoadFromXml(daeDocument, xmlNode)
		self.rigidBodies = CreateObjectsFromXml(daeDocument, xmlNode, DaePhysicsSyntax.RIGID_BODY, DaeRigidBody)		
		
	def SaveToXml(self, daeDocument):
		node = super(DaePhysicsModel, self).SaveToXml(daeDocument)
		# Add the rigid bodies
		AppendChilds(daeDocument, node, self.rigidBodies)
		return node
	
	def FindRigidBody(self, url):
		for rigidBody in self.rigidBodies:
			if rigidBody.sid == url:
				return rigidBody
		return None

class DaePhysicsMaterial(DaeElement):
	def __init__(self):
		super(DaePhysicsMaterial,self).__init__()
		self.syntax = DaePhysicsSyntax.PHYSICS_MATERIAL
		self.techniqueCommon = DaePhysicsMaterial.DaeTechniqueCommon()
	
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaePhysicsMaterial, self).LoadFromXml(daeDocument, xmlNode)
		self.techniqueCommon = CreateObjectFromXml(daeDocument, xmlNode, DaeSyntax.TECHNIQUE_COMMON, DaePhysicsMaterial.DaeTechniqueCommon) 	   
		
	def SaveToXml(self, daeDocument):
		node = super(DaePhysicsMaterial, self).SaveToXml(daeDocument)
		AppendChild(daeDocument,node,self.techniqueCommon)
		return node
	
	class DaeTechniqueCommon(DaeEntity):
		def __init__(self):
			super(DaePhysicsMaterial.DaeTechniqueCommon,self).__init__()
			self.syntax = DaeSyntax.TECHNIQUE_COMMON
			self.dynamicFriction = 0
			self.restitution = 0
			self.staticFriction = 0
			
		def LoadFromXml(self, daeDocument, xmlNode):
			self.dynamicFriction = CastFromXml(daeDocument, xmlNode, DaePhysicsSyntax.DYNAMIC_FRICTION, float, 0)
			self.restitution = CastFromXml(daeDocument, xmlNode, DaePhysicsSyntax.RESTITUTION,	float, 0)
			self.staticFriction = CastFromXml(daeDocument, xmlNode, DaePhysicsSyntax.STATIC_FRICTION, float, 0)
		
		def SaveToXml(self, daeDocument):
			node = super(DaePhysicsMaterial.DaeTechniqueCommon,self).SaveToXml(daeDocument)
			AppendTextChild(node, DaePhysicsSyntax.DYNAMIC_FRICTION, self.dynamicFriction, None)
			AppendTextChild(node, DaePhysicsSyntax.RESTITUTION, self.restitution, None)
			AppendTextChild(node, DaePhysicsSyntax.STATIC_FRICTION, self.staticFriction, None)
			return node
		
		def __str__(self):
			return super(DaePhysicsMaterial.DaeTechniqueCommon,self).__str__()
	
class DaeRigidBody(DaeEntity):
	def __init__(self):
		super(DaeRigidBody, self).__init__()
		self.syntax = DaePhysicsSyntax.RIGID_BODY
		self.name = ''
		self.sid = ''
		self.techniqueCommon = DaeRigidBody.DaeTechniqueCommon()
	
	def LoadFromXml(self, daeDocument, xmlNode):
		self.name = xmlNode.getAttribute(DaeSyntax.NAME)
		self.sid = xmlNode.getAttribute(DaeSyntax.SID)
		self.techniqueCommon = CreateObjectFromXml(daeDocument, xmlNode, DaeSyntax.TECHNIQUE_COMMON, DaeRigidBody.DaeTechniqueCommon)		 
		
	def SaveToXml(self, daeDocument):
		node = super(DaeRigidBody, self).SaveToXml(daeDocument)
		SetAttribute(node,DaeSyntax.NAME, StripString(self.name))
		SetAttribute(node,DaeSyntax.SID, StripString(self.sid))
		AppendChild(daeDocument,node,self.techniqueCommon)
		return node
	
	class DaeTechniqueCommon(DaeEntity):
		def __init__(self):
			super(DaeRigidBody.DaeTechniqueCommon, self).__init__()
			self.syntax = DaeSyntax.TECHNIQUE_COMMON
			self.iPhysicsMaterial = None
			self.physicsMaterial = None
			self.dynamic = True 
			self.mass = None
			self.inertia = None
			self.shapes = []
			
		def LoadFromXml(self, daeDocument, xmlNode):
			self.iPhysicsMaterial = CreateObjectFromXml(daeDocument, xmlNode, DaePhysicsSyntax.INSTANCE_PHYSICS_MATERIAL, DaePhysicsMaterialInstance)		 
			self.physicsMaterial = CreateObjectFromXml(daeDocument, xmlNode, DaePhysicsSyntax.PHYSICS_MATERIAL, DaePhysicsMaterial) 	   
			self.dynamic = CastFromXml(daeDocument, xmlNode, DaePhysicsSyntax.DYNAMIC,bool,True)
			self.mass = CastFromXml(daeDocument, xmlNode, DaePhysicsSyntax.MASS, float, 1)
			self.inertia = ToFloat3(ReadContents(FindElementByTagName(xmlNode,DaePhysicsSyntax.INERTIA)))
			
			shapeNodes = FindElementsByTagName(xmlNode, DaePhysicsSyntax.SHAPE)
			for shapeNode in shapeNodes:
				s = FindElementByTagName(shapeNode, DaePhysicsSyntax.BOX)
				b = None
				if not (s is None):
					b = DaeBoxShape()
				else:
					s = FindElementByTagName(shapeNode, DaePhysicsSyntax.SPHERE)
					if not (s is None):
						b = DaeSphereShape()
					else:
						s = FindElementByTagName(shapeNode, DaePhysicsSyntax.PLANE)
						if not (s is None):
							b = DaePlaneShape()
						else:
							s = FindElementByTagName(shapeNode, DaeSyntax.INSTANCE_GEOMETRY)
							if not (s is None):
								b = DaeGeometryShape()
							else:
								s = FindElementByTagName(shapeNode, DaePhysicsSyntax.CYLINDER)
								if not (s is None):
									b = DaeCylinderShape()
								else:
									s = FindElementByTagName(shapeNode, DaePhysicsSyntax.TAPERED_CYLINDER)
									if not (s is None):
										b = DaeTaperedCylinderShape()
									else:
										s = FindElementByTagName(shapeNode, DaePhysicsSyntax.CAPSULE)
										if not (s is None):
											b = DaeCapsule()
										else: # TAPERED_CAPSULE
											b = DaeTaperedCapsuleShape()
				b.LoadFromXml(daeDocument, s)
				self.shapes.append(b)
		
		def SaveToXml(self, daeDocument):
			node = super(DaeRigidBody.DaeTechniqueCommon,self).SaveToXml(daeDocument)
			AppendChild(daeDocument,node,self.iPhysicsMaterial)
			AppendChild(daeDocument,node,self.physicsMaterial)
			shapes = Element(DaePhysicsSyntax.SHAPE)
			AppendChilds(daeDocument, shapes, self.shapes)
			node.appendChild(shapes)
			AppendTextChild(node, DaePhysicsSyntax.DYNAMIC, self.dynamic, None)
			AppendTextChild(node, DaePhysicsSyntax.MASS, self.mass, None)
			AppendTextChild(node, DaePhysicsSyntax.INERTIA, self.inertia, None)
			return node
		
		def GetPhysicsMaterial(self):
			if not (self.physicsMaterial is None):
				return self.physicsMaterial
			else:
				return self.iPhysicsMaterial.object
		
		def __str__(self):
			return super(DaeRigidBody.DaeTechniqueCommon,self).__str__()
		
class DaeShape(DaeEntity):
	def __init__(self):
		super(DaeShape, self).__init__()
		self.mass = None
		self.density = None
		self.syntax = DaePhysicsSyntax.SHAPE
		
	def LoadFromXml(self, daeDocument, xmlNode):
		self.iGeometry = CreateObjectFromXml(daeDocument, xmlNode, DaeSyntax.INSTANCE_GEOMETRY,DaeGeometryInstance)
		self.mass = CastFromXml(daeDocument, xmlNode, DaePhysicsSyntax.MASS, float, None)
		self.density = CastFromXml(daeDocument, xmlNode, DaePhysicsSyntax.DENSITY, float, None)
		
	def SaveToXml(self, daeDocument):
		node = super(DaeShape, self).SaveToXml(daeDocument)
		AppendTextChild(node, DaePhysicsSyntax.MASS, self.mass, None)
		AppendTextChild(node, DaePhysicsSyntax.DENSITY, self.density, None)
		return node

class DaeBoxShape(DaeShape):
	def __init__(self):
		super(DaeBoxShape, self).__init__()
		self.halfExtents = []
		self.syntax = DaePhysicsSyntax.BOX
		
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaeBoxShape, self).LoadFromXml(daeDocument, xmlNode)
		self.halfExtents = ToFloat3(ReadContents(FindElementByTagName(xmlNode,DaePhysicsSyntax.HALF_EXTENTS)))
		
	def SaveToXml(self, daeDocument):
		node = super(DaeBoxShape, self).SaveToXml(daeDocument)
		AppendTextChild(node, DaePhysicsSyntax.HALF_EXTENTS, self.halfExtents)
		return node

class DaeSphereShape(DaeShape):
	def __init__(self):
		super(DaeSphereShape, self).__init__()
		self.radius = None
		self.syntax = DaePhysicsSyntax.SPHERE
		
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaeSphereShape, self).LoadFromXml(daeDocument, xmlNode)
		self.radius = CastFromXml(daeDocument, xmlNode, DaePhysicsSyntax.RADIUS, float)
		
	def SaveToXml(self, daeDocument):
		node = super(DaeSphereShape, self).SaveToXml(daeDocument)
		AppendTextChild(node, DaePhysicsSyntax.RADIUS, self.radius)
		return node
	
class DaeCylinderShape(DaeShape):
	def __init__(self):
		super(DaeCylinderShape, self).__init__()
		self.radius = [1 , 1]
		self.height = None
		self.syntax = DaePhysicsSyntax.CYLINDER
		
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaeCylinderShape, self).LoadFromXml(daeDocument, xmlNode)
		self.radius = ToFloat2(ReadContents(FindElementByTagName(xmlNode, DaePhysicsSyntax.RADIUS)),'Not a valid radius found. Must consist of 2 floats')
		self.height = CastFromXml(daeDocument, xmlNode, DaeSyntax.HEIGHT, float)
		
	def SaveToXml(self, daeDocument):
		node = super(DaeCylinderShape, self).SaveToXml(daeDocument)
		AppendTextChild(node, DaePhysicsSyntax.RADIUS, self.radius)
		AppendTextChild(node, DaeSyntax.HEIGHT, self.height)
		return node
	
class DaeTaperedCylinderShape(DaeShape):
	def __init__(self):
		super(DaeTaperedCylinderShape, self).__init__()
		self.radius1 = [1 , 1]
		self.radius2 = [1 , 1]
		self.height = None
		self.syntax = DaePhysicsSyntax.TAPERED_CYLINDER
		
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaeTaperedCylinderShape, self).LoadFromXml(daeDocument, xmlNode)
		self.radius1 = ToFloat2(ReadContents(FindElementByTagName(xmlNode, DaePhysicsSyntax.RADIUS1)),'Not a valid radius found. Must consist of 2 floats')
		self.radius2 = ToFloat2(ReadContents(FindElementByTagName(xmlNode, DaePhysicsSyntax.RADIUS2)), 'Not a valid radius found. Must consist of 2 floats')
		self.height = CastFromXml(daeDocument, xmlNode, DaeSyntax.HEIGHT, float)
		
	def SaveToXml(self, daeDocument):
		node = super(DaeTaperedCylinderShape, self).SaveToXml(daeDocument)
		AppendTextChild(node, DaePhysicsSyntax.RADIUS1, self.radius1)
		AppendTextChild(node, DaePhysicsSyntax.RADIUS2, self.radius2)
		AppendTextChild(node, DaeSyntax.HEIGHT, self.height)
		return node
	
class DaePlaneShape(DaeShape):
	def __init__(self):
		super(DaePlaneShape, self).__init__()
		self.equation = []
		self.syntax = DaePhysicsSyntax.PLANE
		
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaePlaneShape, self).LoadFromXml(daeDocument, xmlNode)
		self.equation = ToFloat4(ReadContents(FindElementByTagName(xmlNode,DaePhysicsSyntax.EQUATION)))
	
	def SaveToXml(self, daeDocument):
		node = super(DaePlaneShape, self).SaveToXml(daeDocument)
		AppendTextChild(node, DaePhysicsSyntax.EQUATION, self.equation)
		return node

class DaeCapsuleShape(DaeShape):
	def __init__(self):
		super(DaeCapsuleShape, self).__init__()
		self.radius = None
		self.height = None
		self.syntax = DaePhysicsSyntax.CAPSULE
		
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaeCapsuleShape, self).LoadFromXml(daeDocument, xmlNode)
		self.radius = CastFromXml(daeDocument, xmlNode, DaePhysicsSyntax.RADIUS, float)
		self.height = CastFromXml(daeDocument, xmlNode, DaeSyntax.HEIGHT, float)
		
	def SaveToXml(self, daeDocument):
		node = super(DaeCapsuleShape, self).SaveToXml(daeDocument)
		AppendTextChild(node, DaePhysicsSyntax.RADIUS, self.radius)
		AppendTextChild(node, DaeSyntax.HEIGHT, self.height)
		return node

class DaeGeometryShape(DaeShape):
	def __init__(self):
		super(DaeGeometryShape, self).__init__()
		self.iGeometry = None
		
	def LoadFromXml(self, daeDocument, xmlNode):
		super(DaeGeometryShape, self).LoadFromXml(daeDocument, xmlNode)
		self.iGeometry = DaeGeometryInstance()
		self.iGeometry.LoadFromXml(daeDocument, xmlNode)
		#self.iGeometry = CreateObjectFromXml(daeDocument, xmlNode, DaeSyntax.INSTANCE_GEOMETRY, DaeGeometryInstance)
		#print self.iGeometry
		#print xmlNode.toxml()
		
	def SaveToXml(self, daeDocument):
		#node = super(DaeGeometryShape, self).SaveToXml(daeDocument)
		#AppendChild(daeDocument, node, self.iGeometry)
		return self.iGeometry.SaveToXml(daeDocument)
	
class DaePhysicsSyntax(object):
	PHYSICS_SCENE = 'physics_scene'
	PHYSICS_MODEL = 'physics_model'
	PHYSICS_MATERIAL = 'physics_material'
	
	RIGID_BODY = 'rigid_body'
	
	INSTANCE_PHYSICS_MODEL = 'instance_physics_model'
	INSTANCE_PHYSICS_MATERIAL = 'instance_physics_material'
	INSTANCE_RIGID_BODY = 'instance_rigid_body'
	
	RESTITUTION = 'restitution'
	STATIC_FRICTION = 'static_friction'
	DYNAMIC_FRICTION = 'dynamic_friction'
	
	DYNAMIC = 'dynamic'
	MASS = 'mass'
	INERTIA = 'inertia'
	SHAPE = 'shape'
	DENSITY = 'density'
	RADIUS = 'radius'
	RADIUS1 = 'radius1'
	RADIUS2 = 'radius2'
	
	
	BOX = 'box'
	PLANE = 'plane'
	CYLINDER = 'cylinder'
	SPHERE = 'sphere'
	CAPSULE = 'capsule'
	TAPERED_CAPSULE ='tapered_capsule'
	TAPERED_CYLINDER = 'tapered_cylinder'
	
	HALF_EXTENTS = 'half_extents'

#---Functions---
def CreateObjectsFromXml(colladaDocument, xmlNode, nodeType, objectType):
	if xmlNode is None:
		return None
	objects = []
	nodes = FindElementsByTagName(xmlNode,nodeType)
	for node in nodes:
		object = objectType()
		object.LoadFromXml(colladaDocument, node)
		objects.append(object)
	return objects

def CreateObjectFromXml(colladaDocument, xmlNode, nodeType, objectType, setSyntax = False):
	if xmlNode is None:
		return None
	node = FindElementByTagName(xmlNode, nodeType)   
	object = None
	if setSyntax:
		object = objectType(nodeType)
	else:
		object = objectType()
	if node != None:
		object.LoadFromXml(colladaDocument, node)
		return object
	return None

def CastFromXml(colladaDocument, xmlNode, nodeType, cast, default=None):
	if xmlNode is None:
		return default
	node = FindElementByTagName(xmlNode, nodeType)
	if node != None:
		textValue = ReadContents(node)
		if cast == bool:
			if textValue.lower() == 'false':
				return False
			else:
				return True
		return cast(textValue)
	return default
		
def CastAttributeFromXml(xmlNode, nodeType, cast, default=None):
	if xmlNode is None:
		return default
	val = ReadAttribute(xmlNode, nodeType)
	if val != None and val != '':
		return cast(val)
	return default
	
def AppendChild(daeDocument, xmlNode, daeEntity):
	if daeEntity is None or xmlNode is None:
		return
	else:
		child = daeEntity.SaveToXml(daeDocument)
		if child is None:
			return
		else :
			xmlNode.appendChild(child)
		
def AppendChilds(daeDocument, xmlNode, daeEntities):
	if daeEntities is None or xmlNode is None:
		return
	
	else:
		for daeEntity in daeEntities:
			AppendChild(daeDocument, xmlNode, daeEntity)
			
def AppendTextChild(xmlNode,syntax, object, default = None):
	if object is None:
		return
	if default != None and object == default:
		return
	node = Element(syntax)
	xmlNode.appendChild(node)
	return AppendTextInChild(node, object)

def AppendTextInChild(xmlNode, object):
	if object is None:
		return
	text = Text()
	if type(object) == datetime:
		text.data = object.isoformat()##ToDateTime(object)
	elif type(object) == list:
		if len(object) == 0: return
		if object[0] is not None and type(object[0]) == float:
			object = RoundList(object, ROUND)
		text.data = ListToString(object)
	elif type(object) == float:
		text.data = round(object, ROUND)
	elif type(object) == bool:
		text.data = str(object).lower()
	else:
		text.data = str(object)
	xmlNode.appendChild(text)
	return xmlNode

def SetAttribute(xmlNode,syntax, object):
	if xmlNode is None or object is None or str(object) == '':
		return
	xmlNode.setAttribute(syntax,str(object))

def ReadNodeUrl(node):
	attribute = ReadAttribute(node,DaeSyntax.URL)
	if attribute == None: return None
	else :		  
		attribute = str(attribute)
		if attribute.startswith('#'):
			return attribute[1:]	  
	return None

def WriteNodeUrl(node, url):
	node.setAttribute(DaeSyntax.URL, StripString('#'+url))
	
def IsVersionOk(version, curVersion):
	versionAr = version.split('.')
	curVersionAr = curVersion.split('.')
	for i in range(len(curVersionAr)):
		if versionAr[i] != curVersionAr[i]:
			return False
	return True

def StripString(text):
	return text.replace(' ','_').replace('.','_')
