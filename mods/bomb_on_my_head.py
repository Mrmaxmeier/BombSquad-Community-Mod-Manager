import random

import bs
import bsUtils
from bsSpaz import _BombDiedMessage

class PlayerSpazBombOnMyHead(bs.PlayerSpaz):

	def handleMessage(self, m):
		if isinstance(m, _BombDiedMessage):
			#bs.screenMessage('recyceling')
			self.bombCount += 1
			self.checkAvalibleBombs()
		else:
			super(self.__class__, self).handleMessage(m)

	def checkAvalibleBombs(self):
		if self.exists():
			if self.bombCount >= 1:
				if not self.node.holdNode.exists():
					self.onBombPress()
					self.onBombRelease()

	def startBombChecking(self):
		self.checkAvalibleBombs()
		self._bombCheckTimer = bs.gameTimer(500, bs.WeakCall(self.checkAvalibleBombs), repeat=True)

	def dropBomb(self):
		lifespan = 3000

		if (self.bombCount <= 0) or self.frozen:
			return
		p = self.node.positionForward
		v = self.node.velocity

		bombType = "normal"

		bomb = bs.Bomb(position=(p[0], p[1] - 0.0, p[2]),
					   velocity=(v[0], v[1], v[2]),
					   bombType=bombType,
					   blastRadius=self.blastRadius,
					   sourcePlayer=self.sourcePlayer,
					   owner=self.node).autoRetain()

		bsUtils.animate(bomb.node, 'modelScale', {0:0.0,
								   lifespan*0.1:1.5,
								   lifespan*0.5:1.0})



		self.bombCount -= 1
		bomb.node.addDeathAction(bs.WeakCall(self.handleMessage, _BombDiedMessage()))

		self._pickUp(bomb.node)

		for meth in self._droppedBombCallbacks:
			meth(self, bomb)

		return bomb


def bsGetAPIVersion():
	return 4

def bsGetGames():
	return [BombOnMyHead]

class BombOnMyHead(bs.TeamGameActivity):

	@classmethod
	def getName(cls):
		return 'Bomb on my Head'

	@classmethod
	def getScoreInfo(cls):
		return {'scoreName':'Survived',
				'scoreType':'milliseconds',
				'scoreVersion':'B'}

	@classmethod
	def getDescription(cls, sessionType):
		return "You'll always have a bomb on your head. \n Survive as long as you can!"


	def getInstanceDescription(self):
		return 'Survive as long as you can'

	@classmethod
	def supportsSessionType(cls, sessionType):
		return True if (issubclass(sessionType, bs.TeamsSession)
						or issubclass(sessionType, bs.FreeForAllSession)) else False

	@classmethod
	def getSupportedMaps(cls, sessionType):
		return bs.getMapsSupportingPlayType("melee")

	@classmethod
	def getSettings(cls,sessionType):
		return [("Time Limit", {'choices':[('None', 0), ('1 Minute', 60),
										('2 Minutes', 120), ('5 Minutes', 300),
										('10 Minutes', 600), ('20 Minutes', 1200)], 'default':0}),
				("Max Bomb Limit", {'choices':[('Normal', 1.0), ('Two', 2.0), ('Three', 3.0), ('Four', 4.0)], 'default':1.0}),
				("Epic Mode", {'default':False})]

	def __init__(self, settings):
		bs.TeamGameActivity.__init__(self, settings)

		if self.settings['Epic Mode']:
			self._isSlowMotion = True

		# print messages when players die (since its meaningful in this game)
		self.announcePlayerDeaths = True

		self._lastPlayerDeathTime = None

		self.startTime = 1000


	def onTransitionIn(self):
		bs.TeamGameActivity.onTransitionIn(self, music='Epic' if self.settings['Epic Mode'] else 'Chosen One')

	def onBegin(self):

		bs.TeamGameActivity.onBegin(self)


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

		spaz = PlayerSpazBombOnMyHead(color=player.color,
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
		spaz.connectControlsToPlayer()
		self.scoreSet.playerGotNewSpaz(player, spaz)

		# move to the stand position and add a flash of light
		spaz.handleMessage(bs.StandMessage(position, angle if angle is not None else random.uniform(0, 360)))
		t = bs.getGameTime()
		bs.playSound(self._spawnSound, 1, position=spaz.node.position)
		light = bs.newNode('light', attrs={'color':lightColor})
		spaz.node.connectAttr('position', light, 'position')
		bsUtils.animate(light, 'intensity', {0:0, 250:1, 500:0})
		bs.gameTimer(500, light.delete)


		#bs.gameTimer(1000, bs.WeakCall(spaz.onBombPress))
		bs.gameTimer(self.startTime, bs.WeakCall(spaz.startBombChecking))
		spaz.setBombCount(self.settings['Max Bomb Limit'])


	# various high-level game events come through this method
	def handleMessage(self,m):
		if isinstance(m, bs.PlayerSpazDeathMessage):

			super(self.__class__, self).handleMessage(m)#bs.TeamGameActivity.handleMessage(self,m) # (augment standard behavior)

			deathTime = bs.getGameTime()

			# record the player's moment of death
			m.spaz.getPlayer().gameData['deathTime'] = deathTime

			# in co-op mode, end the game the instant everyone dies (more accurate looking)
			# in teams/ffa, allow a one-second fudge-factor so we can get more draws
			if isinstance(self.getSession(), bs.CoopSession):
				# teams will still show up if we check now.. check in the next cycle
				bs.pushCall(self._checkEndGame)
				self._lastPlayerDeathTime = deathTime # also record this for a final setting of the clock..
			else:
				bs.gameTimer(1000, self._checkEndGame)

		else:
			# default handler:
			super(self.__class__, self).handleMessage(m)#bs.TeamGameActivity.handleMessage(self,m)

	def _checkEndGame(self):
		livingTeamCount = 0
		for team in self.teams:
			for player in team.players:
				if player.isAlive():
					livingTeamCount += 1
					break

		# in co-op, we go till everyone is dead.. otherwise we go until one team remains
		if isinstance(self.getSession(), bs.CoopSession):
			if livingTeamCount <= 0:
				self.endGame()
		else:
			if livingTeamCount <= 1:
				self.endGame()

	def endGame(self):

		curTime = bs.getGameTime()

		# mark 'death-time' as now for any still-living players
		# and award players points for how long they lasted.
		# (these per-player scores are only meaningful in team-games)
		for team in self.teams:
			for player in team.players:

				# throw an extra fudge factor +1 in so teams that
				# didn't die come out ahead of teams that did
				if 'deathTime' not in player.gameData:
					player.gameData['deathTime'] = curTime+1 - self.startTime

				# award a per-player score depending on how many seconds they lasted
				# (per-player scores only affect teams mode; everywhere else just looks at the per-team score)
				score = (player.gameData['deathTime'])
				if 'deathTime' not in player.gameData:
					score += 50 # a bit extra for survivors
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
				longestLife = max(longestLife, (player.gameData['deathTime'] - self.startTime))
			results.setTeamScore(team, longestLife)

		self.end(results=results)
