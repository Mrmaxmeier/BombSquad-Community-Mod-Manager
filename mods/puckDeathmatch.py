import bs
import random

import bsHockey


class PuckTouchedMessage(object):
	pass

class Puck(bsHockey.Puck):
	def __init__(self, position, team):
		bsHockey.Puck.__init__(self, position)
		self.team = team


	def handleMessage(self,m):
		if isinstance(m, PuckTouchedMessage):
			node = bs.getCollisionInfo("opposingNode")
			#bs.screenMessage(str(node.position))
			#node.sourcePlayer
			if (node.sourcePlayer.getTeam() == self.team): return


			#Score - isAlive to avoid multiple kills per death
			if 'notKilled' not in node.sourcePlayer.gameData:
				node.sourcePlayer.gameData['notKilled'] = True
			if node.sourcePlayer.gameData['notKilled']:
				#node.sourcePlayer.getTeam().gameData['timesKilled'] += 1
				self.team.gameData['score'] += 1
				bs.getActivity()._updateScoreBoard()
			node.sourcePlayer.gameData['notKilled'] = False

			x, y, z = node.position
			node.handleMessage("impulse", x, y, z,
							0, 0, 0, #velocity
							1000.0, 0, 3, 0,
							0, 0, 0) # forceDirection
			node.frozen = True
			bs.gameTimer(1000, node.sourcePlayer.actor.shatter)
		else:
			bsHockey.Puck.handleMessage(self,m)

def bsGetAPIVersion():
	return 3

def bsGetGames():
	return [PuckDeathMatch]

class PuckDeathMatch(bs.TeamGameActivity):

	@classmethod
	def getName(cls):
		return 'Puck Deathmatch'
	
	@classmethod
	def getScoreInfo(cls):
		return {'scoreType':'points',
				'lowerIsBetter':False,
				'scoreName':'Score'}
	
	@classmethod
	def getDescription(cls,sessionType):
		return 'Kill everyone with your Puck'
	
	@classmethod
	def getSupportedMaps(cls,sessionType):
		return bs.getMapsSupportingPlayType("melee")

	@classmethod
	def supportsSessionType(cls,sessionType):
		return True if (issubclass(sessionType,bs.TeamsSession)
						or issubclass(sessionType,bs.FreeForAllSession)) else False

	@classmethod
	def getSettings(cls,sessionType):
		return [("Kills to Win",{'minValue':1,'default':5,'increment':1})]

	# in the constructor we should load any media we need/etc.
	# but not actually create anything yet.
	def __init__(self,settings):
		bs.TeamGameActivity.__init__(self,settings)
		self._winSound = bs.getSound("score")
		self._cheerSound = bs.getSound("cheer")
		self._chantSound = bs.getSound("crowdChant")
		self._foghornSound = bs.getSound("foghorn")
		self._swipSound = bs.getSound("swip")
		self._whistleSound = bs.getSound("refWhistle")
		self._puckModel = bs.getModel("puck")
		self._puckTex = bs.getTexture("puckColor")
		self._puckSound = bs.getSound("metalHit")

		self._puckMaterial = bs.Material()
		self._puckMaterial.addActions(actions=( ("modifyPartCollision","friction",0.1)))
		self._puckMaterial.addActions(conditions=("theyHaveMaterial",bs.getSharedObject('pickupMaterial')),
									  actions=( ("modifyPartCollision","collide",False) ) )
		self._puckMaterial.addActions(conditions=( ("weAreYoungerThan",100),'and',
												   ("theyHaveMaterial",bs.getSharedObject('objectMaterial')) ),
									  actions=( ("modifyNodeCollision","collide",False) ) )
		self._puckMaterial.addActions(conditions=("theyHaveMaterial",bs.getSharedObject('footingMaterial')),
									  actions=(("impactSound",self._puckSound,0.2,5)))
		# keep track of which player last touched the puck
		self._puckMaterial.addActions(conditions=("theyHaveMaterial",bs.getSharedObject('playerMaterial')),
									  actions=(("call","atConnect",self._handlePuckPlayerCollide),))

		# we want the puck to kill powerups; not get stopped by them
		self._puckMaterial.addActions(conditions=("theyHaveMaterial",bs.Powerup.getFactory().powerupMaterial),
									  actions=(("modifyPartCollision","physical",False),
											   ("message","theirNode","atConnect",bs.DieMessage())))



		# dis is kill
		self._puckMaterial.addActions(conditions=("theyHaveMaterial",bs.getSharedObject('playerMaterial')),
									  actions=(("modifyPartCollision","physical",False),
											   ("message", "ourNode", "atConnect", PuckTouchedMessage())))


		self._scoreBoard = bs.ScoreBoard()
		self._killsToWin = self.settings['Kills to Win']
		self._scoreSound = bs.getSound("score")

		self.pucks = []
		

	# called when our game is transitioning in but not ready to start..
	# ..we can go ahead and start creating stuff, playing music, etc.
	def onTransitionIn(self):
		bs.TeamGameActivity.onTransitionIn(self, music='ToTheDeath')

	# called when our game actually starts
	def onBegin(self):
		bs.TeamGameActivity.onBegin(self)

		self._won = False
		#for team in self.teams:
		#	team.gameData['timesKilled'] = 0
		#self._updateScoreBoard()
		#for team in self.teams:
		#	self._spawnPuck(team.getID())
		
		self.setupStandardPowerupDrops()
		
		self._timer = bs.OnScreenTimer()
		bs.gameTimer(4000,self._timer.start)

	def onPlayerJoin(self, player):
		self._spawnPuck(player.getTeam())
		self._updateScoreBoard()
		bs.TeamGameActivity.onPlayerJoin(self, player)

	def onTeamJoin(self, team):
		team.gameData['score'] = 0
		bs.TeamGameActivity.onTeamJoin(self, team)

	# called for each spawning player
	def spawnPlayer(self,player):
		# lets spawn close to the center
		#spawnCenter = (1,4,0)
		#pos = (spawnCenter[0]+random.uniform(-1.5,1.5),spawnCenter[1],spawnCenter[2]+random.uniform(-1.5,1.5))
		pos = self.getMap().getStartPosition(player.getTeam().getID())
		spaz = self.spawnPlayerSpaz(player,position=pos)

		spaz.connectControlsToPlayer(enablePunch=True,
									 enableBomb=False,
									 enablePickUp=True)
		player.gameData['notKilled'] = True

	def _flashPuckSpawn(self, pos):
		light = bs.newNode('light',
						   attrs={'position': pos,
								  'heightAttenuated':False,
								  'color': (1,0,0)})
		bs.animate(light,'intensity',{0:0,250:1,500:0},loop=True)
		bs.gameTimer(1000,light.delete)

	def _spawnPuck(self, team):
		puckPos = self.getMap().getStartPosition(team.getID())
		lightcolor = team.color
		bs.playSound(self._swipSound)
		bs.playSound(self._whistleSound)
		self._flashPuckSpawn(puckPos)

		puck = Puck(position=puckPos, team=team)
		puck.scored = False
		puck.lastHoldingPlayer = None
		puck.light = bs.newNode('light',
									  owner=puck.node,
									  attrs={'intensity':0.3,
											 'heightAttenuated':False,
											 'radius':0.2,
											 'color': lightcolor})
		puck.node.connectAttr('position',puck.light,'position')
		self.pucks.append(puck)

	def _handlePuckPlayerCollide(self):
		try:
			puckNode,playerNode = bs.getCollisionInfo('sourceNode','opposingNode')
			puck = puckNode.getDelegate()
			player = playerNode.getDelegate().getPlayer()
		except Exception: player = puck = None

		if player is not None and player.exists() and puck is not None: puck.lastPlayersToTouch[player.getTeam().getID()] = player


	def _checkIfWon(self):
		# simply end the game if there's no living bots..
		for team in self.teams:
			if team.gameData['score'] >= self._killsToWin:
				self._won = True
				self.endGame()

	def _updateScoreBoard(self):
		for team in self.teams:
			self._scoreBoard.setTeamValue(team,team.gameData['score'],self._killsToWin)
		self._checkIfWon()



	# called for miscellaneous events
	def handleMessage(self,m):
		if isinstance(m,bs.PlayerSpazDeathMessage):
			bs.TeamGameActivity.handleMessage(self,m) # do standard stuff
			self.respawnPlayer(m.spaz.getPlayer()) # kick off a respawn
			
		else:
			# let the base class handle anything we don't..
			bs.TeamGameActivity.handleMessage(self,m)
			
	# when this is called, we should fill out results and end the game
	# *regardless* of whether is has been won. (this may be called due
	# to a tournament ending or other external reason)
	def endGame(self):

		# stop our on-screen timer so players can see what they got
		self._timer.stop()
		results = bs.TeamGameResults()
		for t in self.teams: results.setTeamScore(t,t.gameData['score'])
		self.end(results=results)
