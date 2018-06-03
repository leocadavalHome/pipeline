import pymel.core as pm
import maya.mel as mel
import unicodedata

## Model
def unlockNormals():
	geos = pm.ls (type = 'mesh')
	locked = False

	for geo in geos:
		if geo.isIntermediate():
			continue

		for id in range(geo.numNormals()-1):
			x = geo.isNormalLocked(id)

			if x:
				locked = True 
				break

	return locked

def selectUnlockNormals(*args):
	pm.select (cl=True)
	geos = pm.ls (type = 'mesh')

	for geo in geos:

		if geo.isIntermediate():
			continue

		for id in range(geo.numNormals()-1):
			x = geo.isNormalLocked(id)

			if x:
				obj = geo.listRelatives(p=True, type='transform')[0]
				pm.select (obj, add=True)

	return 'select'


def fixNormals(*args):
	geos = pm.ls (type = 'mesh')

	for geo in geos:
		if geo.isIntermediate():
			continue

		pm.polyNormalPerVertex(geo+'.vtx[*]', unFreezeNormal=True )

	return 'ok'

#########################################

def noNonManifold():
	geos = pm.ls (type = 'mesh')
	hasNMfold=False

	for geo in geos:

		if geo.isIntermediate():
			continue

		obj = geo.listRelatives(p=True, type='transform')
		p = pm.polyInfo(obj, nme=True , nmv=True )

		if p:
			hasNMfold=True
			break

	return hasNMfold

def cleanNonManifold(*args):
	x = mel.eval ('polyCleanupArgList 3 { "1","1","0","0","0","0","0","0","0","1e-005","0","1e-005","0","1e-005","0","1","0" }')
	pm.selectMode( object=True )
	pm.select (cl=True)

	return 'ok'

def selectNonManifold(*args):
	geos = pm.ls (type = 'mesh')

	for geo in geos:

		if geo.isIntermediate():
			continue

		obj = geo.listRelatives(p=True, type='transform')
		p = pm.polyInfo(obj, nme=True , nmv=True )

		if p:
			pm.select (p)

	return 'select'

######################################

def noLaminaFaces():
	geos = pm.ls (type = 'mesh')
	hasLamina=False

	for geo in geos:

		if geo.isIntermediate():
			continue

		obj = geo.listRelatives(p=True, type='transform')
		p = pm.polyInfo(obj, lf=True)

		if p:
			hasLamina=True
			break

	return hasLamina	

def cleanLaminaFaces(*args):
	x = mel.eval ('polyCleanupArgList 3 { "1","1","0","0","0","0","0","0","0","1e-005","0","1e-005","0","1e-005","0","-1","1" }')
	pm.selectMode( object=True )
	pm.select (cl=True)

	return 'ok'

def selectLaminaFaces(*args):
	geos = pm.ls (type = 'mesh')

	for geo in geos:

		if geo.isIntermediate():
			continue

		obj = geo.listRelatives(p=True, type='transform')
		p = pm.polyInfo(obj, lf=True)

		if p:
			pm.select (p)

	return 'select'

##################################

def noConstructionHistory():
	geos = pm.ls (geometry = True)
	hasHist = False

	for geo in geos:
		
		if geo.isIntermediate():
			continue

		hist = geo.history()
		hist = [x for x in hist if not x==geo]
		hist = [x for x in hist if not (pm.objectType(x) == 'groupId' or pm.objectType(x) == 'shadingEngine')]
		
		if hist:
			hasHist = True
			break

	return hasHist


def deleteHistory(*args):
	geos = pm.ls (type = 'surfaceShape')
	pm.delete (geos, ch=True)

	return 'ok'

##################################

def duplicatedNames():
	geos = pm.ls (type = 'mesh')
	nameErr=False

	for geo in geos:

		if geo.isIntermediate():
			continue

		obj = geo.listRelatives(p=True, type='transform')[0]

		if '|' in obj.name():
			nameErr =True
			break

	return nameErr

def fixDuplicatedNames(*args):
	geos = pm.ls (type = 'mesh')

	for geo in geos:

		if geo.isIntermediate():
			continue

		obj = geo.listRelatives(p=True, type='transform')[0]

		if '|' in obj.name():
			baseName = obj.name().split('|')[-1]
			sameNameObjs = pm.ls (baseName)
			num = len (sameNameObjs)

			for i in range (num):
				try:
					pm.rename (sameNameObjs[i], baseName+'_%03d' % (i+1))
				except:
					pm.confirmDialog( title='error',ma='center', message='Problem renaming. Try manually', button=['OK'], defaultButton='OK', dismissString='OK')
					return 'error'

	return 'ok'

def selectDuplicatedNames(*args):
	pm.select (cl=True)
	geos = pm.ls (type = 'mesh')

	for geo in geos:

		if geo.isIntermediate():
			continue

		obj = geo.listRelatives(p=True, type='transform')[0]

		if '|' in obj.name():
			pm.select (obj, add=True)

	return 'select'

#######################################

def validNames():
	nameErr = False
	geos = pm.ls (type = 'mesh')

	for geo in geos:

		if geo.isIntermediate():
			continue

		obj = geo.listRelatives(p=True, type = 'transform')[0]
		legalName = unicodedata.normalize('NFKD', obj.name()).encode('ascii', 'ignore')

		if obj.name() != legalName:
			nameErr = True
			break

	return nameErr

def fixInvalidNames(*args):
	geos = pm.ls (type = 'mesh')

	for geo in geos:

		if geo.isIntermediate():
			continue

		obj = geo.listRelatives(p=True, type = 'transform')[0]
		legalName = unicodedata.normalize('NFKD', obj.name()).encode('ascii', 'ignore')

		if obj.name() != legalName:
			pm.rename (obj, legalName)

	return 'ok'

def selectInvalidNames(*args):
	pm.select (cl=True)
	geos = pm.ls (type = 'mesh')

	for geo in geos:

		if geo.isIntermediate():
			continue

		obj = geo.listRelatives(p=True, type = 'transform')[0]
		legalName = unicodedata.normalize('NFKD', obj.name()).encode('ascii', 'ignore')

		if obj.name() != legalName:
			pm.select (obj, add=True)	

	return 'select'


###########################################

def validShapeNames():
	geos = pm.ls (type = 'mesh')
	nameErr=False

	for geo in geos:

		if geo.isIntermediate():
			continue

		obj = geo.listRelatives(p=True, type='transform')[0]

		if geo.name() != obj.name()+'Shape':
		    nameErr=True
		    break

	return nameErr

def fixShapeNames(*args):
	geos = pm.ls (type = 'mesh')

	for geo in geos:

		if geo.isIntermediate():
			continue

		obj = geo.listRelatives(p=True, type='transform')[0]
		if geo.name() != obj.name()+'Shape':
			try:
				pm.rename (geo, obj.name()+'Shape')
			except:
				pm.confirmDialog( title='error',ma='center', message='Problem renaming. Try manually', button=['OK'], defaultButton='OK', dismissString='OK')
				return 'error'
	return 'ok'

def selectInvalidShapeNames(*args):
	pm.select (cl=True)
	geos = pm.ls (type = 'mesh')

	for geo in geos:

		if geo.isIntermediate():
			continue

		obj = geo.listRelatives(p=True, type='transform')[0]

		if geo.name() != obj.name()+'Shape':
			pm.select (obj, add=True)			

	return 'select'

################################################

def noIntermediateShapes():
	geos = pm.ls (type = 'mesh')
	nameErr=False

	for geo in geos:
		if geo.isIntermediate():
			cntWMAux = pm.connectionInfo (geo+'.worldMesh[0]', isSource=True)

			if not cntWMAux:
				nameErr=True
			 	break

	return nameErr

def deleteIntermediateShapes(*args):
	geos = pm.ls (type = 'mesh')

	for geo in geos:
		if geo.isIntermediate():
			cntWMAux = pm.connectionInfo (geo+'.worldMesh[0]', isSource=True)
			if not cntWMAux:
				pm.delete (geo)

	return 'ok'

def selectIntermediateShapes(*args):
	pm.select (cl=True)
	geos = pm.ls (type = 'mesh')

	for geo in geos:
		if geo.isIntermediate():
			cntWMAux = pm.connectionInfo (geo+'.worldMesh[0]', isSource=True)

			if not cntWMAux:
				obj = geo.listRelatives(p=True, type='transform')[0]
				pm.select (obj, add=True)

	return 'select'


##################################################

def noShaders():
	geos = pm.ls (type = 'surfaceShape')
	shaderErr=False

	for geo in geos:

		if geo.isIntermediate():
			continue
		
		SGGeos = pm.listConnections(geo,type='shadingEngine')

		for SGGeo in SGGeos:
			if SGGeo.name() != 'initialShadingGroup':
				shaderErr = True

	return shaderErr

def fixShaders():
	geos = pm.ls (type = 'surfaceShape')
	inicialSG = pm.PyNode('initialShadingGroup')
	for geo in geos:

		if geo.isIntermediate():
			continue

		obj = geo.listRelatives(p=True, type='transform')[0]
		SGGeos = pm.listConnections(geo, type='shadingEngine')
		for SGGeo in SGGeos:
			if SGGeo.name() != 'initialShadingGroup':
				pm.sets (inicialSG,  forceElement = geo)

	return 'ok'

def selectShaderedObjs(*args):
	pm.select (cl=True)
	geos = pm.ls (type = 'surfaceShape')

	for geo in geos:

		if geo.isIntermediate():
			continue
		
		SGGeos = pm.listConnections(geo,type='shadingEngine')

		for SGGeo in SGGeos:
			if SGGeo.name() != 'initialShadingGroup':
				obj = geo.listRelatives(p=True, type='transform')[0]
				pm.select (obj, add=True)

	return 'select'

##################################################

def geosInsideGeoGroup():
	geoGrpErr = False
	geoGrps = pm.ls ('geo_group', r=True)

	if geoGrps:
		geoGrp = geoGrps[0]
	else:
		print 'geo_group doesnt exist on this scene'
		geoGrpErr = True
		return geoGrpErr

	geos = pm.ls (type = 'surfaceShape')

	for geo in geos:

		if geo.isIntermediate():
			continue

		obj = geo.listRelatives(p=True, type='transform')[0]

		if not obj.isChildOf(geoGrp):
			geoGrpErr = True
			print 'some geos outside geo_group'
			return geoGrpErr

	return geoGrpErr

def fixGeoGroup(*args):
	geoGrpErr = False
	geoGrps = pm.ls ('geo_group', r=True)

	if geoGrps:
		geoGrp = geoGrps[0]
	else:
		print 'geo_group doesnt exist on this scene'
		geoGrp = pm.group(em=True, n='geo_group')

	geos = pm.ls (type = 'surfaceShape')
	for geo in geos:

		if geo.isIntermediate():
			continue

		obj = geo.listRelatives(p=True, type='transform')[0]

		if not obj.isChildOf(geoGrp):
			obj.root().setParent(geoGrp)

	return 'ok'

###################################################

def noNameSpaces():
	root = pm.namespace (set =':')
	nameSpacesInScene = pm.namespaceInfo( listOnlyNamespaces=True, recurse =True, absoluteName=True )
	nameSpacesInScene.remove (':UI')
	nameSpacesInScene.remove (':shared')

	if nameSpacesInScene:
		return True

	return False

def deleteNameSpaces(*args):
	root = pm.namespace (set =':')
	nameSpacesInScene = pm.namespaceInfo( listOnlyNamespaces=True, recurse =True, absoluteName=True )
	nameSpacesInScene.remove (':UI')
	nameSpacesInScene.remove (':shared')

	try:
		for i in range(len(nameSpacesInScene)-1,-1,-1):
			pm.namespace(moveNamespace = [nameSpacesInScene[i],':'], force = True)
			pm.namespace(removeNamespace = nameSpacesInScene[i])

	except:	
		pm.confirmDialog( title='error',ma='center', message='Problem deleting namespaces. Try manually', button=['OK'], defaultButton='OK', dismissString='OK')
		return 'erro'	

	return 'ok'

def skip(*args):
	for a in args:
		print a

	print 'skip'
	return 'skip'


'''
Here some tests that could be unnecessary
def noFourSidedFaces():
	print 'nonFourSided'
	return False

def froozenTransforms():
	print 'froozenTransforms'
	return False

## Uvs
def noMultipleUVMaps():
	print 'noMultipleUVMaps'
	return False

## BlendShape
def geosInsideBspGroup():
	print 'noShaders'
	return False

## Textures

## Rigs
def geoGroup():
	print 'noShaders'
	return False

def controlSet():
	print 'noShaders'
	return False

def controlZeroedValues():
	print 'noShaders'
	return False

def noEmptyIntermediaryShapes():
	print 'noIntermediaryShapes'
	return False

#general
def noEmptyDisplayLayers():
	print 'noShaders'
	return False

## fix Actions

'''

## Main routine
class PublishWidget(object):
	def __init__(self, task):
	    self.checkProcedures = {
	                            'model':{  
	                                        1.0:{'label':'No namespace','check': noNameSpaces, 'fix': [deleteNameSpaces] },
	                                        2.0:{'label':'All geometry in geo_group','check': geosInsideGeoGroup, 'fix': [fixGeoGroup] },
	                                        3.0:{'label':'No Construction History','check': noConstructionHistory, 'fix': [deleteHistory] },
	                                        4.0:{'label':'No Intermediate Shapes','check': noIntermediateShapes, 'fix': [deleteIntermediateShapes, selectIntermediateShapes] },
	                                        5.0:{'label':'Valid Names','check': validNames, 'fix': [fixInvalidNames,selectInvalidNames] },
	                                        6.0:{'label':'No Duplicated Names','check': duplicatedNames, 'fix': [fixDuplicatedNames,selectDuplicatedNames] },
	                                        7.0:{'label':'Valid Shape Names', 'check': validShapeNames, 'fix': [fixShapeNames, selectInvalidShapeNames] },
	                                        8.0:{'label':'No Shaders','check': noShaders, 'fix': [fixShaders,selectShaderedObjs, skip] },                           
	                                        9.0:{'label':'No NonManifold', 'check': noNonManifold, 'fix': [cleanNonManifold, selectNonManifold, skip] },
	                                        10.0:{'label':'No Locked Normals','check': unlockNormals, 'fix': [fixNormals,selectUnlockNormals, skip] }, 
	                                        11.0:{'label':'No LaminaFaces','check': noLaminaFaces, 'fix': [cleanLaminaFaces,selectLaminaFaces, skip] }
	                                    },
	                            'uvs':{},
	                            'textures':{},
	                            'xlo':{},
	                            'rig':{},
	                            'blendShape':{},
	                            }

	    self.checksDict =   self.checkProcedures[task]
	    self.checksWidgets = {}


	def createWin(self):
		if (pm.window ('publishTest', exists=True)):
			pm.deleteUI ('publishTest', window=True) 

		self.win = pm.window ('publishTest', w=200, h=300)
		self.parentCol = pm.columnLayout ()
		self.col = pm.columnLayout ()
		self.btn = pm.button (p=self.parentCol, l ='VALIDATE', w=200,h = 50, c=self.runChecks)
		pm.showWindow(self.win)

		order = self.checksDict.keys()
		order.sort()

		for id in order:
			self.checksWidgets[id] = pm.iconTextButton (p = self.col, style='iconAndTextHorizontal', image1='D:JOBS/PIPELINE/pipeExemple/scenes/icons/empty.png', label=self.checksDict[id]['label'] )

	def closeWin(self):
		pm.deleteUI (self.win)

	def runChecks(self, *args):
		sucess = True

		order = self.checksDict.keys()
		order.sort()
		for id in order:
			result = self.checksDict[id]['check']()

			if result:
				sucess = False
				pm.iconTextButton (self.checksWidgets[id], e=True, image1='D:JOBS/PIPELINE/pipeExemple/scenes/icons/fix.png', label=self.checksDict[id]['label'] +' failled' )

				if not self.checksDict[id]['fix']:
					continue

				popup = pm.popupMenu(p = self.checksWidgets[id])

				for fix in self.checksDict[id]['fix']:
					pm.menuItem(p = popup,  l = fix.__name__, c= lambda x, y = fix, z = id : self.runFix (y, z))

			else:
				pm.iconTextButton (self.checksWidgets[id], e=True, image1='D:JOBS/PIPELINE/pipeExemple/scenes/icons/valid.png', label=self.checksDict[id]['label']+' Ok' )

		if sucess:
			print 'item valid!'
			pm.button (self.btn, e=True, l ='PUBLISH', c=self.publishFile)	


	def runFix(self, fix, id):
		x = fix()
		
		if x == 'ok':
			pm.iconTextButton (self.checksWidgets[id], e=True, image1='D:JOBS/PIPELINE/pipeExemple/scenes/icons/valid.png', label=self.checksDict[id]['label'] +' Ok' )
		elif x == 'skip':
			pm.iconTextButton (self.checksWidgets[id], e=True, image1='D:JOBS/PIPELINE/pipeExemple/scenes/icons/skip.png', label=self.checksDict[id]['label'] +' skipped' )

	def publishFile(self, *args):
		pass