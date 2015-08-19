import bs
import bsUtils
import random


class State:
	def __init__(self, bomb=None, grab=False, punch=False, curse=False, required=False, final=False, name=""):
		self.bomb = bomb
		self.grab = grab
		self.punch = punch
		self.pickup = False
		self.curse = curse
		self.required = required or final
		self.final = final
		self.name = name
		self.next = None
		self.index = None

	def apply(self, spaz, disconnectControls=True):
		if disconnectControls:
			spaz.disconnectControlsFromPlayer()

		spaz.connectControlsToPlayer(enablePunch=self.punch,
									 enableBomb=bool(self.bomb),
									 enablePickUp=self.grab,
									 enableFly=True)
		if self.curse:
			spaz.curseTime = -1
			spaz.curse()
		if self.bomb:
			spaz.bombType = self.bomb
		spaz.setScoreText(self.name)


	def getSetting(self):
		return (self.name, {'default': True})


class ArmsRace(bs.TeamGameActivity):
	states = [
		State(bomb='normal', name='Basic Bombs'),
		State(bomb='ice', name='Frozen Bombs'),
		State(bomb='sticky', name='Sticky Bombs'),
		State(bomb='impact', name='Impact Bombs'),
		State(grab=True, name='Grabbing only'),
		State(punch=True, name='Punching only'),
		State(curse=True, name='Cursed', final=True)
	]

	@classmethod
	def getName(cls):
		return 'Arms Race'

	@classmethod
	def getScoreInfo(cls):
		return {'scoreType': 'points',
				'lowerIsBetter': False,
				'scoreName': 'Score'}

	@classmethod
	def getDescription(cls, sessionType):
		return "Upgrade your weapon by eliminating enemies.\nWin the match by being the first player\nto get a kill while cursed."

	def getInstanceDescription(self):
		return 'Upgrade your weapon by eliminating enemies.'

	def getInstanceScoreBoardDescription(self):
		return 'Kill {} Players to win'.format(len(self.states))

	@classmethod
	def supportsSessionType(cls, sessionType):
		return True if (issubclass(sessionType, bs.TeamsSession)
						or issubclass(sessionType, bs.FreeForAllSession)) else False

	@classmethod
	def getSupportedMaps(cls, sessionType):
		return bs.getMapsSupportingPlayType("melee")

	@classmethod
	def getSettings(cls, sessionType):
		settings = [("Epic Mode", {'default': False}),
					("Time Limit", {'choices': [('None', 0), ('1 Minute', 60),
												('2 Minutes', 120), ('5 Minutes', 300)],
												'default': 0})]
		for state in cls.states:
			if not state.required:
				settings.append(state.getSetting())
		return settings

	def __init__(self, settings):
		self.states = [s for s in self.states if settings.get(s.name, True)]
		for i, state in enumerate(self.states):
			if i < len(self.states) and not state.final:
				state.next = self.states[i + 1]
			state.index = i
		bs.TeamGameActivity.__init__(self, settings)
		if self.settings['Epic Mode']:
			self._isSlowMotion = True

	def onTransitionIn(self):
		bs.TeamGameActivity.onTransitionIn(self, music='Epic' if self.settings['Epic Mode'] else 'Survival')
		self._startGameTime = bs.getGameTime()

	def onBegin(self):
		bs.TeamGameActivity.onBegin(self)
		self.setupStandardTimeLimit(self.settings['Time Limit'])
		#self.setupStandardPowerupDrops(enableTNT=False)

	def onPlayerJoin(self, player):
		if 'state' not in player.gameData:
			player.gameData['state'] = self.states[0]
		self.spawnPlayer(player)

	# overriding the default character spawning..
	def spawnPlayer(self, player):
		state = player.gameData['state']

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

		spaz = bs.PlayerSpaz(color=player.color,
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
		self.scoreSet.playerGotNewSpaz(player, spaz)

		# move to the stand position and add a flash of light
		spaz.handleMessage(bs.StandMessage(position, angle if angle is not None else random.uniform(0, 360)))
		t = bs.getGameTime()
		bs.playSound(self._spawnSound, 1, position=spaz.node.position)
		light = bs.newNode('light', attrs={'color':lightColor})
		spaz.node.connectAttr('position', light,'position')
		bsUtils.animate(light,'intensity', {0:0, 250:1, 500:0})
		bs.gameTimer(500, light.delete)

		state.apply(spaz, False)


	# various high-level game events come through this method
	def handleMessage(self,m):
		if isinstance(m, bs.PlayerSpazDeathMessage):

			bs.TeamGameActivity.handleMessage(self,m) # augment standard behavior
			player = m.spaz.getPlayer()

			if m.killed and player is not m.killerPlayer and m.killerPlayer is not None:
				if not m.killerPlayer.gameData["state"].final:
					m.killerPlayer.gameData["state"] = m.killerPlayer.gameData["state"].next
					m.killerPlayer.gameData["state"].apply(m.killerPlayer.actor)
				else:
					self.scoreSet.playerScored(m.killerPlayer, len(self.states), screenMessage=True)
					self.endGame()
			if not player.gameData["state"].final:
				self.respawnPlayer(player)
			else:
				self.endGame()

		else:
			super(self.__class__, self).handleMessage(m)

	def endGame(self):
		results = bs.TeamGameResults()
		for team in self.teams:
			score = max([player.gameData["state"].index for player in team.players])
			results.setTeamScore(team, score)
		self.end(results=results, delay=1000)


def bsGetAPIVersion():
	return 3

def bsGetGames():
	return [ArmsRace]
