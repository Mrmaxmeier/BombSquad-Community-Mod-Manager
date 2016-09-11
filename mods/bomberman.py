import bs
import bsUtils
import bsElimination
import bsBomb
import bsSpaz
import random
import math


class Map:
	center = (0, 3, -4)
	radius = 8

	@classmethod
	def inBounds(cls, pos):
		dx, dy, dz = pos[0] - cls.center[0], pos[1] - cls.center[1], pos[2] - cls.center[2],
		return cls.radius >= math.sqrt(dx**2 + dy**2 + dz**2)



class Crate(bsBomb.Bomb):
	def __init__(self, position=(0, 1, 0), velocity=(0, 0, 0)):
		self.position = position
		bsBomb.Bomb.__init__(self, position, velocity,
						bombType='tnt', blastRadius=0.0,
						sourcePlayer=None, owner=None)
		self.node.extraAcceleration = (0, -50, 0)

	def handleMessage(self, m):
		#if isinstance(m, bs.PickedUpMessage):
		#	self._heldBy = m.node
		#elif isinstance(m, bs.DroppedMessage):
		#	bs.animate(self._powText, 'scale', {0:0.01, 500: 0.03})
		#	bs.gameTimer(500, bs.WeakCall(self.pow))
		bsBomb.Bomb.handleMessage(self, m)

	def explode(self):
		pos = self.position
		bs.gameTimer(100, bs.WeakCall(bs.getActivity().dropPowerup, pos))
		bs.gameTimer(1, bs.WeakCall(self.handleMessage, bs.DieMessage()))

class Bomb(bsBomb.Bomb):
	def explode(self):
		if self._exploded:
			return
		self._exploded = True
		size = int(self.blastRadius)
		for mod in range(-size, size+1):
			pos = self.node.position
			posX = (pos[0] + mod*1.0, pos[1], pos[2])
			posY = (pos[0], pos[1], pos[2] + mod*1.0)
			if Map.inBounds(posX):
				bs.gameTimer(abs(mod)*150, bs.Call(blast, posX, self.bombType, self.sourcePlayer, self.hitType, self.hitSubType))
			if Map.inBounds(posY):
				bs.gameTimer(abs(mod)*150, bs.Call(blast, posY, self.bombType, self.sourcePlayer, self.hitType, self.hitSubType))

		bs.gameTimer(1, bs.WeakCall(self.handleMessage, bs.DieMessage()))


class Blast(bsBomb.Blast):
	# all that code to reduce the camera shake effect
	def __init__(self,position=(0,1,0),velocity=(0,0,0),blastRadius=2.0,blastType="normal",sourcePlayer=None,hitType='explosion',hitSubType='normal'):
		"""
		Instantiate with given values.
		"""
		bs.Actor.__init__(self)


		factory = Bomb.getFactory()

		self.blastType = blastType
		self.sourcePlayer = sourcePlayer

		self.hitType = hitType;
		self.hitSubType = hitSubType;

		# blast radius
		self.radius = blastRadius

		self.node = bs.newNode('region',
							   attrs={'position':(position[0],position[1]-0.1,position[2]), # move down a bit so we throw more stuff upward
									  'scale':(self.radius,self.radius,self.radius),
									  'type':'sphere',
									  'materials':(factory.blastMaterial,bs.getSharedObject('attackMaterial'))},
							   delegate=self)

		bs.gameTimer(50,self.node.delete)

		# throw in an explosion and flash
		explosion = bs.newNode("explosion",
							   attrs={'position':position,
									  'velocity':(velocity[0],max(-1.0,velocity[1]),velocity[2]),
									  'radius':self.radius,
									  'big':(self.blastType == 'tnt')})
		if self.blastType == "ice":
			explosion.color = (0,0.05,0.4)

		bs.gameTimer(1000,explosion.delete)

		if self.blastType != 'ice': bs.emitBGDynamics(position=position,velocity=velocity,count=int(1.0+random.random()*4),emitType='tendrils',tendrilType='thinSmoke')
		bs.emitBGDynamics(position=position,velocity=velocity,count=int(4.0+random.random()*4),emitType='tendrils',tendrilType='ice' if self.blastType == 'ice' else 'smoke')
		bs.emitBGDynamics(position=position,emitType='distortion',spread=1.0 if self.blastType == 'tnt' else 2.0)

		# and emit some shrapnel..
		if self.blastType == 'ice':
			def _doEmit():
				bs.emitBGDynamics(position=position,velocity=velocity,count=30,spread=2.0,scale=0.4,chunkType='ice',emitType='stickers');
			bs.gameTimer(50,_doEmit) # looks better if we delay a bit


		elif self.blastType == 'sticky':
			def _doEmit():
				bs.emitBGDynamics(position=position,velocity=velocity,count=int(4.0+random.random()*8),spread=0.7,chunkType='slime');
				bs.emitBGDynamics(position=position,velocity=velocity,count=int(4.0+random.random()*8),scale=0.5, spread=0.7,chunkType='slime');
				bs.emitBGDynamics(position=position,velocity=velocity,count=15,scale=0.6,chunkType='slime',emitType='stickers');
				bs.emitBGDynamics(position=position,velocity=velocity,count=20,scale=0.7,chunkType='spark',emitType='stickers');
				bs.emitBGDynamics(position=position,velocity=velocity,count=int(6.0+random.random()*12),scale=0.8,spread=1.5,chunkType='spark');
			bs.gameTimer(50,_doEmit) # looks better if we delay a bit

		elif self.blastType == 'impact': # regular bomb shrapnel
			def _doEmit():
				bs.emitBGDynamics(position=position,velocity=velocity,count=int(4.0+random.random()*8),scale=0.8,chunkType='metal');
				bs.emitBGDynamics(position=position,velocity=velocity,count=int(4.0+random.random()*8),scale=0.4,chunkType='metal');
				bs.emitBGDynamics(position=position,velocity=velocity,count=20,scale=0.7,chunkType='spark',emitType='stickers');
				bs.emitBGDynamics(position=position,velocity=velocity,count=int(8.0+random.random()*15),scale=0.8,spread=1.5,chunkType='spark');
			bs.gameTimer(50,_doEmit) # looks better if we delay a bit

		else: # regular or land mine bomb shrapnel
			def _doEmit():
				if self.blastType != 'tnt':
					bs.emitBGDynamics(position=position,velocity=velocity,count=int(4.0+random.random()*8),chunkType='rock');
					bs.emitBGDynamics(position=position,velocity=velocity,count=int(4.0+random.random()*8),scale=0.5,chunkType='rock');
				bs.emitBGDynamics(position=position,velocity=velocity,count=30,scale=1.0 if self.blastType=='tnt' else 0.7,chunkType='spark',emitType='stickers');
				bs.emitBGDynamics(position=position,velocity=velocity,count=int(18.0+random.random()*20),scale=1.0 if self.blastType == 'tnt' else 0.8,spread=1.5,chunkType='spark');

				# tnt throws splintery chunks
				if self.blastType == 'tnt':
					def _emitSplinters():
						bs.emitBGDynamics(position=position,velocity=velocity,count=int(20.0+random.random()*25),scale=0.8,spread=1.0,chunkType='splinter');
					bs.gameTimer(10,_emitSplinters)

				# every now and then do a sparky one
				if self.blastType == 'tnt' or random.random() < 0.1:
					def _emitExtraSparks():
						bs.emitBGDynamics(position=position,velocity=velocity,count=int(10.0+random.random()*20),scale=0.8,spread=1.5,chunkType='spark');
					bs.gameTimer(20,_emitExtraSparks)

			bs.gameTimer(50,_doEmit) # looks better if we delay a bit

		light = bs.newNode('light',
						   attrs={'position':position,
								  'color': (0.6,0.6,1.0) if self.blastType == 'ice' else (1,0.3,0.1),
								  'volumeIntensityScale': 10.0})

		s = random.uniform(0.6,0.9)
		scorchRadius = lightRadius = self.radius
		if self.blastType == 'tnt':
			lightRadius *= 1.4
			scorchRadius *= 1.15
			s *= 3.0

		iScale = 1.6
		bsUtils.animate(light,"intensity",{0:2.0*iScale, int(s*20):0.1*iScale, int(s*25):0.2*iScale, int(s*50):17.0*iScale, int(s*60):5.0*iScale, int(s*80):4.0*iScale, int(s*200):0.6*iScale, int(s*2000):0.00*iScale, int(s*3000):0.0})
		bsUtils.animate(light,"radius",{0:lightRadius*0.2, int(s*50):lightRadius*0.55, int(s*100):lightRadius*0.3, int(s*300):lightRadius*0.15, int(s*1000):lightRadius*0.05})
		bs.gameTimer(int(s*3000),light.delete)

		# make a scorch that fades over time
		scorch = bs.newNode('scorch',
							attrs={'position':position,'size':scorchRadius*0.5,'big':(self.blastType == 'tnt')})
		if self.blastType == 'ice':
			scorch.color = (1,1,1.5)

		bsUtils.animate(scorch,"presence",{3000:1, 13000:0})
		bs.gameTimer(13000,scorch.delete)

		if self.blastType == 'ice':
			bs.playSound(factory.hissSound,position=light.position)

		p = light.position
		bs.playSound(factory.getRandomExplodeSound(),position=p)
		bs.playSound(factory.debrisFallSound,position=p)

		########
		bs.shakeCamera(intensity=5.0 if self.blastType == 'tnt' else 0.05)
		########

		# tnt is more epic..
		if self.blastType == 'tnt':
			bs.playSound(factory.getRandomExplodeSound(),position=p)
			def _extraBoom():
				bs.playSound(factory.getRandomExplodeSound(),position=p)
			bs.gameTimer(250,_extraBoom)
			def _extraDebrisSound():
				bs.playSound(factory.debrisFallSound,position=p)
				bs.playSound(factory.woodDebrisFallSound,position=p)
			bs.gameTimer(400,_extraDebrisSound)


def blast(pos, blastType, sourcePlayer, hitType, hitSubType):
	Blast(position=pos, velocity=(0, 1, 0),
		  blastRadius=0.5,blastType=blastType,
		  sourcePlayer=sourcePlayer,hitType=hitType,
		  hitSubType=hitSubType).autoRetain()

class Player(bs.PlayerSpaz):
	isDead = False

	#def __init__(self, *args, **kwargs):
	#	super(self.__class__, self).init(*args, **kwargs)
	#	self.multiplyer = 0


	def handleMessage(self, m):
		if False:
			pass
		elif isinstance(m, bs.PowerupMessage):
			if m.powerupType == 'punch':
				self.blastRadius += 1.0
				self.setScoreText("range up")
			super(self.__class__, self).handleMessage(m)
		else:
			super(self.__class__, self).handleMessage(m)

	def dropBomb(self):
		"""
		Tell the spaz to drop one of his bombs, and returns
		the resulting bomb object.
		If the spaz has no bombs or is otherwise unable to
		drop a bomb, returns None.
		"""

		if (self.landMineCount <= 0 and self.bombCount <= 0) or self.frozen: return
		p = self.node.positionForward
		v = self.node.velocity

		if self.landMineCount > 0:
			droppingBomb = False
			self.setLandMineCount(self.landMineCount-1)
			bombType = 'landMine'
		else:
			droppingBomb = True
			bombType = self.bombType

		bomb = Bomb(position=(p[0],p[1] - 0.0,p[2]),
					   velocity=(v[0],v[1],v[2]),
					   bombType=bombType,
					   blastRadius=self.blastRadius,
					   sourcePlayer=self.sourcePlayer,
					   owner=self.node).autoRetain()

		if droppingBomb:
			self.bombCount -= 1
			bomb.node.addDeathAction(bs.WeakCall(self.handleMessage,bsSpaz._BombDiedMessage()))

		self._pickUp(bomb.node)

		for c in self._droppedBombCallbacks: c(self,bomb)

		return bomb

def bsGetAPIVersion():
	return 4

def bsGetGames():
	return [Bomberman]

class Bomberman(bs.TeamGameActivity):

	@classmethod
	def getName(cls):
		return 'Bomberman'

	@classmethod
	def getScoreInfo(cls):
		return {'scoreName':'Survived',
			'scoreType':'seconds',
			'scoreVersion':'B',
			'noneIsWinner':True}

	@classmethod
	def getDescription(cls, sessionType):
		return "Destroy crates and collect powerups"


	def getInstanceDescription(self):
		return 'Destroy crates and collect powerups'

	@classmethod
	def supportsSessionType(cls, sessionType):
		return True if (issubclass(sessionType, bs.TeamsSession)
						or issubclass(sessionType, bs.FreeForAllSession)) else False

	@classmethod
	def getSupportedMaps(cls, sessionType):
		return ["Doom Shroom"]

	@classmethod
	def getSettings(cls, sessionType):
		return [("Time Limit",{'choices':[('None',0),('1 Minute',60),('2 Minutes',120),
											('5 Minutes',300)],'default':0}),
				("Lives (0 = Unlimited)",{'minValue':0,'default':3,'increment':1}),
				("Epic Mode",{'default':False})]

	def __init__(self, settings):
		bs.TeamGameActivity.__init__(self,settings)
		if self.settings['Epic Mode']:
			self._isSlowMotion = True

		# print messages when players die (since its meaningful in this game)
		self.announcePlayerDeaths = True

		self._lastPlayerDeathTime = None

		self._startGameTime = 1000
		self.gridsize = (1.0, 1.0)
		self.gridnum = (18, 18)


	def onTransitionIn(self):
		bs.TeamGameActivity.onTransitionIn(self, music='Epic' if self.settings['Epic Mode'] else 'Survival')
		self._startGameTime = bs.getGameTime()

	def onBegin(self):
		bs.TeamGameActivity.onBegin(self)
		self.setupStandardTimeLimit(self.settings['Time Limit'])
		for x in range(self.gridnum[0]):
			for y in range(self.gridnum[1]):
				self.dropCrate(x, y)


	def dropCrate(self, gridX, gridY):
		pos = (Map.center[0] + self.gridsize[0]*gridX - self.gridnum[0]*self.gridsize[0]*0.5,
				Map.center[1],
				Map.center[2] + self.gridsize[1]*gridY - self.gridnum[1]*self.gridsize[1]*0.5)
		#print('dropped crate @', pos)
		if Map.inBounds(pos):
			Crate(position=pos).autoRetain()

	def dropPowerup(self, position):
		powerupType = random.choice(["punch", "tripleBombs", "health"])
		bs.Powerup(position=position, powerupType=powerupType, expire=False).autoRetain()

	def onPlayerJoin(self, player):
		self.spawnPlayer(player)

	def onPlayerLeave(self, player):
		bs.TeamGameActivity.onPlayerLeave(self, player)

	# overriding the default character spawning..
	def spawnPlayer(self, player):



		if isinstance(self.getSession(), bs.TeamsSession):
			position = self.getMap().getStartPosition(player.getTeam().getID())
		else:
			# otherwise do free-for-all spawn locations
			position = self.getMap().getFFAStartPosition(self.players)

		angle = None


		#spaz = self.spawnPlayerSpaz(player)

		# lets reconnect this player's controls to this
		# spaz but *without* the ability to attack or pick stuff up
		#spaz.connectControlsToPlayer(enablePunch=False,
		#							 enableBomb=False,
		#							 enablePickUp=False)

		# also lets have them make some noise when they die..
		#spaz.playBigDeathSound = True

		name = player.getName()

		lightColor = bsUtils.getNormalizedColor(player.color)
		displayColor = bs.getSafeColor(player.color, targetIntensity=0.75)

		spaz = Player(color=player.color,
							 highlight=player.highlight,
							 character=player.character,
							 player=player)
		player.setActor(spaz)

		# we want a bigger area-of-interest in co-op mode
		# if isinstance(self.getSession(),bs.CoopSession): spaz.node.areaOfInterestRadius = 5.0
		# else: spaz.node.areaOfInterestRadius = 5.0

		# if this is co-op and we're on Courtyard or Runaround, add the material that allows us to
		# collide with the player-walls
		# FIXME; need to generalize this
		if isinstance(self.getSession(), bs.CoopSession) and self.getMap().getName() in ['Courtyard', 'Tower D']:
			mat = self.getMap().preloadData['collideWithWallMaterial']
			spaz.node.materials += (mat,)
			spaz.node.rollerMaterials += (mat,)

		spaz.node.name = name
		spaz.node.nameColor = displayColor
		spaz.connectControlsToPlayer( enableJump=True, enablePunch=True, enablePickUp=False, enableBomb=True, enableRun=True, enableFly=False)
		self.scoreSet.playerGotNewSpaz(player,spaz)

		# move to the stand position and add a flash of light
		spaz.handleMessage(bs.StandMessage(position,angle if angle is not None else random.uniform(0, 360)))
		t = bs.getGameTime()
		bs.playSound(self._spawnSound, 1, position=spaz.node.position)
		light = bs.newNode('light', attrs={'color': lightColor})
		spaz.node.connectAttr('position', light, 'position')
		bsUtils.animate(light, 'intensity', {0:0, 250:1, 500:0})
		bs.gameTimer(500, light.delete)



	# various high-level game events come through this method
	def handleMessage(self,m):
		if isinstance(m, bs.PlayerSpazDeathMessage):

			bs.TeamGameActivity.handleMessage(self, m) # augment standard behavior
			player = m.spaz.getPlayer()
			player.gameData["survivalSeconds"] = bs.getGameTime()

			if len(self._getLivingTeams()) < 2:
				self._roundEndTimer = bs.Timer(1000, self.endGame)

		else:
			# default handler:
			super(self.__class__, self).handleMessage(m)#bs.TeamGameActivity.handleMessage(self,m)

	def endGame(self):

		curTime = bs.getGameTime()
		# mark 'death-time' as now for any still-living players
		# and award players points for how long they lasted.
		# (these per-player scores are only meaningful in team-games)
		for team in self.teams:
			for player in team.players:

				# throw an extra fudge factor +1 in so teams that
				# didn't die come out ahead of teams that did
				if 'survivalSeconds' in player.gameData:
					score = player.gameData['survivalSeconds']
				elif 'survivalSeconds' in team.gameData:
					score = team.gameData['survivalSeconds']
				else:
					score = (curTime - self._startGameTime)/1000 + 1

				#if 'survivalSeconds' not in player.gameData:
				#	player.gameData['survivalSeconds'] = (curTime - self._startGameTime)/1000 + 1
				#	print('extraBonusSwag for player')

				# award a per-player score depending on how many seconds they lasted
				# (per-player scores only affect teams mode; everywhere else just looks at the per-team score)
				#score = (player.gameData['survivalSeconds'])
				self.scoreSet.playerScored(player, score, screenMessage=False)


		# ok now calc game results: set a score for each team and then tell the game to end
		results = bs.TeamGameResults()

		# remember that 'free-for-all' mode is simply a special form of 'teams' mode
		# where each player gets their own team, so we can just always deal in teams
		# and have all cases covered
		for team in self.teams:

			# set the team score to the max time survived by any player on that team
			longestLife = 0
			for player in team.players:
				if 'survivalSeconds' in player.gameData:
					time = player.gameData['survivalSeconds']
				elif 'survivalSeconds' in team.gameData:
					time = team.gameData['survivalSeconds']
				else:
					time = (curTime - self._startGameTime)/1000 + 1
				longestLife = max(longestLife, time)
			results.setTeamScore(team, longestLife)

		self.end(results=results)

	def _getLivingTeams(self):
		return [team for team in self.teams if len(team.players) > 0 and any('survivalSeconds' not in player.gameData for player in team.players)]

