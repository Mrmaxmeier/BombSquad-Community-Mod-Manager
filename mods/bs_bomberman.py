import random

import bs
import bsUtils
import bsElimination
import bsBomb
import bsSpaz


class Crate(bsBomb.Bomb):
	def __init__(self, position=(0, 1, 0), velocity=(0, 0, 0)):
		self.position = position
		bsBomb.Bomb.__init__(self, position, velocity,
						bombType='tnt', blastRadius=0.0,
						sourcePlayer=None, owner=None)

	def handleMessage(self, m):
		#if isinstance(m, bs.PickedUpMessage):
		#	self._heldBy = m.node
		#elif isinstance(m, bs.DroppedMessage):
		#	bs.animate(self._powText, 'scale', {0:0.01, 500: 0.03})
		#	bs.gameTimer(500, bs.WeakCall(self.pow))
		bsBomb.Bomb.handleMessage(self, m)

	def explode(self):
		pos = self.position
		bs.gameTimer(200, bs.WeakCall(bs.getActivity().dropPowerup, pos))
		bs.gameTimer(1,bs.WeakCall(self.handleMessage,bs.DieMessage()))

class Bomb(bsBomb.Bomb):
	def explode(self):
		if self._exploded: return
		self._exploded = True
		size = int(self.blastRadius)
		print('blasting with size:', size)
		for mod in range(-size, size+1):
			pos = self.node.position
			posX = (pos[0] + mod*1.0, pos[1], pos[2])
			posY = (pos[0], pos[1], pos[2] + mod*1.0)
			bs.gameTimer(abs(mod)*100, bs.Call(blast, posX, self.bombType, self.sourcePlayer, self.hitType, self.hitSubType))
			bs.gameTimer(abs(mod)*100, bs.Call(blast, posY, self.bombType, self.sourcePlayer, self.hitType, self.hitSubType))

		bs.gameTimer(1,bs.WeakCall(self.handleMessage,bs.DieMessage()))

def blast(pos, blastType, sourcePlayer, hitType, hitSubType):
	bsBomb.Blast(position=pos, velocity=(0, 1, 0),
				 blastRadius=0.3,blastType=blastType,
				 sourcePlayer=sourcePlayer,hitType=hitType,
				 hitSubType=hitSubType).autoRetain()

class Player(bs.PlayerSpaz):
	isDead = False

	#def __init__(self, *args, **kwargs):
	#	super(self.__class__, self).init(*args, **kwargs)
	#	self.multiplyer = 0


	def handleMessage(self, m):
		if False: pass
		elif isinstance(m, bs.PowerupMessage):
			if m.powerupType == 'health':
				pass
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
	return 3

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
	def getDescription(cls,sessionType):
		return "#yoloswag"


	def getInstanceDescription(self):
		return '#yolonese'

	@classmethod
	def supportsSessionType(cls,sessionType):
		return True if (issubclass(sessionType,bs.TeamsSession)
						or issubclass(sessionType,bs.FreeForAllSession)) else False

	@classmethod
	def getSupportedMaps(cls,sessionType):
		return ["Doom Shroom"]

	@classmethod
	def getSettings(cls,sessionType):
		return [("Time Limit",{'choices':[('None',0),('1 Minute',60),('2 Minutes',120),
											('5 Minutes',300)],'default':0}),
				("Lives (0 = Unlimited)",{'minValue':0,'default':3,'increment':1}),
				("Epic Mode",{'default':False})]

	def __init__(self,settings):
		bs.TeamGameActivity.__init__(self,settings)
		if self.settings['Epic Mode']: self._isSlowMotion = True
		
		# print messages when players die (since its meaningful in this game)
		self.announcePlayerDeaths = True

		self._lastPlayerDeathTime = None

		self._startGameTime = 1000
		self.center = (0, 3, -4)
		self.gridsize = (1.0, 1.0)
		self.gridnum = (9, 9)


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
		pos = (self.center[0] + self.gridsize[0]*gridX - self.gridnum[0]*self.gridsize[0]*0.5,
				self.center[1],
				self.center[2] + self.gridsize[1]*gridY - self.gridnum[1]*self.gridsize[1]*0.5)
		#print('dropped crate @', pos)
		Crate(position=pos).autoRetain()

	def dropPowerup(self, position):
		powerupType = random.choice(["punch", "tripleBombs", "health"])
		bs.Powerup(position=position, powerupType=powerupType, expire=False).autoRetain()

	def onPlayerJoin(self,player):
		self.spawnPlayer(player)

	def onPlayerLeave(self,player):
		bs.TeamGameActivity.onPlayerLeave(self,player)

	# overriding the default character spawning..
	def spawnPlayer(self,player):



		if isinstance(self.getSession(),bs.TeamsSession):
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
		if isinstance(self.getSession(),bs.CoopSession) and self.getMap().getName() in ['Courtyard','Tower D']:
			mat = self.getMap().preloadData['collideWithWallMaterial']
			spaz.node.materials += (mat,)
			spaz.node.rollerMaterials += (mat,)
		
		spaz.node.name = name
		spaz.node.nameColor = displayColor
		spaz.connectControlsToPlayer( enableJump=True, enablePunch=True, enablePickUp=False, enableBomb=True, enableRun=True, enableFly=False)
		self.scoreSet.playerGotNewSpaz(player,spaz)

		# move to the stand position and add a flash of light
		spaz.handleMessage(bs.StandMessage(position,angle if angle is not None else random.uniform(0,360)))
		t = bs.getGameTime()
		bs.playSound(self._spawnSound,1,position=spaz.node.position)
		light = bs.newNode('light',attrs={'color':lightColor})
		spaz.node.connectAttr('position',light,'position')
		bsUtils.animate(light,'intensity',{0:0,250:1,500:0})
		bs.gameTimer(500,light.delete)



	# various high-level game events come through this method
	def handleMessage(self,m):
		if isinstance(m,bs.PlayerSpazDeathMessage):
			
			bs.TeamGameActivity.handleMessage(self,m) # augment standard behavior
			player = m.spaz.getPlayer()
			player.gameData["survivalSeconds"] = bs.getGameTime()

			if len(self._getLivingTeams()) < 2:
				self._roundEndTimer = bs.Timer(1000,self.endGame)

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
				self.scoreSet.playerScored(player,score,screenMessage=False)

		
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
			results.setTeamScore(team,longestLife)

		self.end(results=results)

	def _getLivingTeams(self):
		return [team for team in self.teams if len(team.players) > 0 and any('survivalSeconds' not in player.gameData for player in team.players)]

