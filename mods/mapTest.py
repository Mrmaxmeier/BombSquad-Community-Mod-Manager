from bsMap import *

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
	import pentominoDefs as defs
	name = 'Test Map!'
	playTypes = ['melee','keepAway','teamFlag']

	@classmethod
	def getPreviewTextureName(cls):
		return 'courtyardPreview'

	@classmethod
	def onPreload(cls):
		data = {}
		data['model'] = bs.getModel('pentomino') #bs.getModel('courtyardLevel')
		#data['modelBottom'] = bs.getModel('courtyardLevelBottom')
		data['collideModel'] = bs.getCollideModel('pentomino') #bs.getCollideModel('courtyardLevelCollide')
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
									  #'colorTexture':self.preloadData['tex'],
									  'materials':[bs.getSharedObject('footingMaterial')]})
		self.bg = bs.newNode('terrain',
							 attrs={'model':self.preloadData['bgModel'],
									'lighting':False,
									'background':True,
									'colorTexture':self.preloadData['bgTex']})
		#self.bottom = bs.newNode('terrain',
		#						 attrs={'model':self.preloadData['modelBottom'],
		#								'lighting':False,
		#								'colorTexture':self.preloadData['tex']})

		bs.newNode('terrain',
				   attrs={'model':self.preloadData['vrFillMoundModel'],
						  'lighting':False,
						  'vrOnly':True,
						  'color':(0.53,0.57,0.5),
						  'background':True,
						  'colorTexture':self.preloadData['vrFillMoundTex']})

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
