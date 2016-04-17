from bsMap import *

# This file generated from 'courtyard.blend'
points, boxes = {}, {}
points['botSpawnBottom'] = (-0.06281, 2.81477, 1.9508)
points['botSpawnBottomHalfLeft'] = (-2.05017, 2.81477, 1.9508)
points['botSpawnBottomHalfRight'] = (1.85516, 2.81477, 1.9508)
points['botSpawnBottomLeft'] = (-3.68097, 2.81477, 1.9508)
points['botSpawnBottomRight'] = (3.58646, 2.81477, 1.9508)
points['botSpawnLeft'] = (-6.44708, 2.81477, -2.318)
points['botSpawnLeftLower'] = (-6.44708, 2.81477, -1.50996)
points['botSpawnLeftLowerMore'] = (-6.44708, 2.81477, -0.48322)
points['botSpawnLeftUpper'] = (-6.44708, 2.81477, -3.18356)
points['botSpawnLeftUpperMore'] = (-6.44708, 2.81477, -4.01001)
points['botSpawnRight'] = (6.53974, 2.81477, -2.318)
points['botSpawnRightLower'] = (6.53974, 2.81477, -1.39604)
points['botSpawnRightLowerMore'] = (6.53974, 2.81477, -0.36235)
points['botSpawnRightUpper'] = (6.53974, 2.81477, -3.13007)
points['botSpawnRightUpperMore'] = (6.53974, 2.81477, -3.97743)
points['botSpawnTop'] = (-0.06281, 2.81477, -5.83327)
points['botSpawnTopHalfLeft'] = (-1.49422, 2.81477, -5.83327)
points['botSpawnTopHalfRight'] = (1.60083, 2.81477, -5.83327)
points['botSpawnTopLeft'] = (-3.12023, 2.81477, -5.95068)
points['botSpawnTopRight'] = (3.39675, 2.81477, -5.95068)
points['botSpawnTurretBottomLeft'] = (-6.12714, 3.32755, 1.91119)
points['botSpawnTurretBottomRight'] = (6.37291, 3.32755, 1.79865)
points['botSpawnTurretTopLeft'] = (-6.12714, 3.32755, -6.57288)
points['botSpawnTurretTopMiddle'] = (0.08149, 4.27028, -8.52229)
points['botSpawnTurretTopMiddleLeft'] = (-1.27138, 4.27028, -8.52229)
points['botSpawnTurretTopMiddleRight'] = (1.12846, 4.27028, -8.52229)
points['botSpawnTurretTopRight'] = (6.37291, 3.32755, -6.60369)
points['ffaSpawn1'] = (-8.98938, 7.82832, -2.21705) + (0.8701, 0.04, 0.68122)
points['ffaSpawn2'] = (8.85662, 7.54067, -3.41298) + (0.89973, 0.05, 0.68122)
points['ffaSpawn3'] = (8.86127, 8.54119, 3.24576) + (1.01595, 0.05, 0.60948)
points['ffaSpawn4'] = (-8.40508, 7.21303, 3.33691) + (0.58774, 0.05, 0.60051)
points['flag1'] = (-5.96566, 2.82001, -2.42884)
points['flag2'] = (5.90555, 2.80048, -2.21827)
points['flagDefault'] = (0.25162, 2.78421, -2.6442)
points['powerupSpawn1'] = (-3.55556, 3.16846, 0.36928)
points['powerupSpawn2'] = (3.62569, 3.16846, 0.40585)
points['powerupSpawn3'] = (3.62569, 3.16846, -4.98724)
points['powerupSpawn4'] = (-3.55556, 3.16846, -5.02381)
points['shadowLowerBottom'] = (0.52363, 0.02085, 5.34123)
points['shadowLowerTop'] = (0.52363, 1.20612, 5.34123)
points['shadowUpperBottom'] = (0.52363, 6.35902, 5.34123)
points['shadowUpperTop'] = (0.52363, 10.12386, 5.34123)
points['spawn1'] = (-7.51483, 3.80364, -2.10215) + (0.08787, 0.05, 2.19598)
points['spawn2'] = (7.4621, 3.77279, -1.83521) + (0.0288, 0.05, 2.22167)
boxes['areaOfInterestBounds'] = (0.35441, 3.95843, -2.17503) + (0, 0, 0) + (16.37702, 7.75567, 13.38681)
boxes['edgeBox'] = (0.0, 1.03673, -2.14249) + (0, 0, 0) + (12.01667, 11.4058, 7.80819)
boxes['levelBounds'] = (0.26088, 4.89966, -3.54367) + (0, 0, 0) + (29.23565, 14.19991, 29.92689)


class Defs():
	points = points
	boxes = boxes

def debugSpawns(self):
	for pt in self.ffaSpawnPoints:
		middle = list(pt[:3])
		size = list(pt[3:6]) if len(pt) > 3 else (0.5, 0, 0.5)
		size[1] = .05
		p1 = [v - size[i] for i, v in enumerate(middle)]
		size1 = [s*2 for s in size]
		bs.newNode('locator',attrs={'position':p1, 'size': size1})
		p2 = [v + size[i] for i, v in enumerate(middle)]
		size2 = [-s*2 for s in size]
		bs.newNode('locator',attrs={'position':p2, 'size': size2})



class TestMap(Map):
	#import courtyardLevelDefs as defs
	defs = Defs()
	name = 'Courtyard - Test'
	playTypes = ['melee','keepAway','teamFlag']

	@classmethod
	def getPreviewTextureName(cls):
		return 'courtyardPreview'

	@classmethod
	def onPreload(cls):
		data = {}
		data['model'] = bs.getModel('courtyardLevel')
		data['modelBottom'] = bs.getModel('courtyardLevelBottom')
		data['collideModel'] = bs.getCollideModel('courtyardLevelCollide')
		data['tex'] = bs.getTexture('courtyardLevelColor')
		data['bgTex'] = bs.getTexture('menuBG')
		data['bgModel'] = bs.getModel('thePadBG') # fixme - chop this into vr and non-vr chunks
		data['playerWallCollideModel'] = bs.getCollideModel('courtyardPlayerWall')

		data['playerWallMaterial'] = bs.Material()
		data['playerWallMaterial'].addActions(actions=(('modifyPartCollision','friction',0.0)))

		# anything that needs to hit the wall should apply this.
		data['collideWithWallMaterial'] = bs.Material()
		data['playerWallMaterial'].addActions(
			conditions=('theyDontHaveMaterial',data['collideWithWallMaterial']),
			actions=('modifyPartCollision','collide',False))

		data['vrFillMoundModel'] = bs.getModel('stepRightUpVRFillMound')
		data['vrFillMoundTex'] = bs.getTexture('vrFillMound')

		return data

	def __init__(self):
		Map.__init__(self)
		self.node = bs.newNode('terrain',
							   delegate=self,
							   attrs={'collideModel':self.preloadData['collideModel'],
									  'model':self.preloadData['model'],
									  'colorTexture':self.preloadData['tex'],
									  'materials':[bs.getSharedObject('footingMaterial')]})
		self.bg = bs.newNode('terrain',
							 attrs={'model':self.preloadData['bgModel'],
									'lighting':False,
									'background':True,
									'colorTexture':self.preloadData['bgTex']})
		self.bottom = bs.newNode('terrain',
								 attrs={'model':self.preloadData['modelBottom'],
										'lighting':False,
										'colorTexture':self.preloadData['tex']})

		bs.newNode('terrain',
				   attrs={'model':self.preloadData['vrFillMoundModel'],
						  'lighting':False,
						  'vrOnly':True,
						  'color':(0.53,0.57,0.5),
						  'background':True,
						  'colorTexture':self.preloadData['vrFillMoundTex']})

		# in challenge games, put up a wall to prevent players
		# from getting in the turrets (that would foil our brilliant AI)
		if 'CoopSession' in str(type(bs.getSession())):
			self.playerWall = bs.newNode('terrain',
										 attrs={'collideModel':self.preloadData['playerWallCollideModel'],
												'affectBGDynamics':False,
												'materials':[self.preloadData['playerWallMaterial']]})
		bsGlobals = bs.getSharedObject('globals')
		bsGlobals.tint = (1.2,1.17,1.1)
		bsGlobals.ambientColor = (1.2,1.17,1.1)
		bsGlobals.vignetteOuter = (0.6,0.6,0.64)
		bsGlobals.vignetteInner = (0.95,0.95,0.93)
		debugSpawns(self)

	def _isPointNearEdge(self,p,running=False):
		# count anything off our ground level as safe (for our platforms)
		#if p.y() > 3.1: return False
		# see if we're within edgeBox
		boxPosition = self.defs.boxes['edgeBox'][0:3]
		boxScale = self.defs.boxes['edgeBox'][6:9]
		x = (p.x() - boxPosition[0])/boxScale[0]
		z = (p.z() - boxPosition[2])/boxScale[2]
		return (x < -0.5 or x > 0.5 or z < -0.5 or z > 0.5)

registerMap(TestMap)
