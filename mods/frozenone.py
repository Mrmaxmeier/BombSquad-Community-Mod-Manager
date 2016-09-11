import bs
from bsChosenOne import ChosenOneGame

def bsGetAPIVersion():
	return 4

def bsGetGames():
	return [FrozenOneGame]

class FrozenOneGame(ChosenOneGame):

	@classmethod
	def getName(cls):
		return 'Frozen One'

	@classmethod
	def getDescription(cls,sessionType):
		return ('Be the Frozen one for a length of time to win.\n'
				'Kill the Frozen one to become it.')

	@classmethod
	def getSettings(cls, sessionType):
		return [('Frozen One Time', {'default': 30, 'increment': 10, 'minValue': 10}),
				('Frozen One Gets Gloves', {'default': True}),
				('Time Limit',
				 {'choices': [('None', 0),
							  ('1 Minute', 60),
							  ('2 Minutes', 120),
							  ('5 Minutes', 300),
							  ('10 Minutes', 600),
							  ('20 Minutes', 1200)],
				  'default': 0}),
				('Respawn Times',
				 {'choices': [('Shorter', 0.25),
							  ('Short', 0.5),
							  ('Normal', 1.0),
							  ('Long', 2.0),
							  ('Longer', 4.0)],
				  'default': 1.0}),
				('Epic Mode', {'default': False})]

	def onTeamJoin(self,team):
		team.gameData['timeRemaining'] = self.settings["Frozen One Time"]
		self._updateScoreBoard()

	def endGame(self):
		results = bs.TeamGameResults()
		for team in self.teams: results.setTeamScore(team,self.settings['Frozen One Time'] - team.gameData['timeRemaining'])
		self.end(results=results,announceDelay=0)

	def _setChosenOnePlayer(self, player):
		try:
			for p in self.players: p.gameData['FrozenLight'] = None
			bs.playSound(self._swipSound)
			if player is None or not player.exists():
				self._flag = bs.Flag(color=(1,0.9,0.2),
									 position=self._flagSpawnPos,
									 touchable=False)
				self._chosenOnePlayer = None

				l = bs.newNode('light',
							   owner=self._flag.node,
							   attrs={'position': self._flagSpawnPos,
									  'intensity':0.6,
									  'heightAttenuated':False,
									  'volumeIntensityScale':0.1,
									  'radius':0.1,
									  'color': (1.2,1.2,0.4)})

				self._flashFlagSpawn()
			else:
				if player.actor is not None:
					self._flag = None
					self._chosenOnePlayer = player

					if player.actor.node.exists():
						if self.settings['Frozen One Gets Gloves']: player.actor.handleMessage(bs.PowerupMessage('punch'))

						player.actor.frozen = True
						player.actor.node.frozen = 1
						# use a color that's partway between their team color and white
						color = [0.3+c*0.7 for c in bs.getNormalizedColor(player.getTeam().color)]
						l = player.gameData['FrozenLight'] = bs.NodeActor(bs.newNode('light',
																					 attrs={"intensity":0.6,
																							"heightAttenuated":False,
																							"volumeIntensityScale":0.1,
																							"radius":0.13,
																							"color": color}))

						bs.animate(l.node, 'intensity', {0:1.0, 200:0.4, 400:1.0}, loop=True)
						player.actor.node.connectAttr('position',l.node,'position')
		except Exception, e:
			import traceback
			print 'EXC in _setChosenOnePlayer'
			traceback.print_exc(e)
			traceback.print_stack()

	def _updateScoreBoard(self):
		for team in self.teams:
			self._scoreBoard.setTeamValue(team,team.gameData['timeRemaining'],self.settings['Frozen One Time'], countdown=True)
