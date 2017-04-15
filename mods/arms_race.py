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

	def apply(self, spaz):
		spaz.disconnectControlsFromPlayer()
		spaz.connectControlsToPlayer(enablePunch=self.punch,
									 enableBomb=bool(self.bomb),
									 enablePickUp=self.grab)
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
		self.announcePlayerDeaths = True
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
		super(self.__class__, self).spawnPlayer(player)
		state.apply(player.actor)

	def isValidKill(self, m):
		return all([
			m.killed,
			m.spaz.getPlayer() is not m.killerPlayer,
			m.killerPlayer is not None,
			m.spaz.getPlayer().color is not m.killerPlayer.color
		])

	# various high-level game events come through this method
	def handleMessage(self,m):
		if isinstance(m, bs.PlayerSpazDeathMessage):

			bs.TeamGameActivity.handleMessage(self, m) # augment standard behavior

			if self.isValidKill(m):
				if not m.killerPlayer.gameData["state"].final:
					m.killerPlayer.gameData["state"] = m.killerPlayer.gameData["state"].next
					m.killerPlayer.gameData["state"].apply(m.killerPlayer.actor)
				else:
					self.endGame()
			self.respawnPlayer(m.spaz.getPlayer())
		else:
			super(self.__class__, self).handleMessage(m)

	def endGame(self):
		results = bs.TeamGameResults()
		for team in self.teams:
			score = max([player.gameData["state"].index for player in team.players])
			results.setTeamScore(team, score)
		self.end(results=results)


def bsGetAPIVersion():
	return 4

def bsGetGames():
	return [ArmsRace]
