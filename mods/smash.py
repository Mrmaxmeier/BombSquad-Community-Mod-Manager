import random
import bs
import bsUtils
import bsElimination
import bsBomb

class Icon(bsElimination.Icon):
	def updateForLives(self):
		if self._player.exists():
			lives = self._player.gameData['lives']
		else: lives = 0
		if self._showLives:
			if lives > 0:
				self._livesText.text = 'x' + str(lives - 1)
			elif lives < 0:
				self._livesText.text = str(lives)
			else:
				self._livesText.text = ''
		if lives == 0:
			if hasattr(bs.getActivity(), 'timeLimitOnly'):
				if not bs.getActivity().timeLimitOnly:
					self._nameText.opacity = 0.2
					self.node.color = (0.7, 0.3, 0.3)
					self.node.opacity = 0.2

class PowBox(bsBomb.Bomb):
	def __init__(self, position=(0, 1, 0), velocity=(0, 0, 0)):
		bsBomb.Bomb.__init__(self, position, velocity,
						bombType='tnt', blastRadius=2.5,
						sourcePlayer=None, owner=None)
		self.setPowText()


	def setPowText(self, color=(1, 1, 0.4)):
		m = bs.newNode('math', owner=self.node, attrs={'input1': (0, 0.7, 0), 'operation': 'add'})
		self.node.connectAttr('position', m, 'input2')
		self._powText = bs.newNode('text',
									  owner=self.node,
									  attrs={'text':'POW!',
											 'inWorld':True,
											 'shadow':1.0,
											 'flatness':1.0,
											 'color':color,
											 'scale':0.0,
											 'hAlign':'center'})
		m.connectAttr('output', self._powText, 'position')
		bs.animate(self._powText, 'scale', {0: 0.0, 1000: 0.01})

	def handleMessage(self, m):
		if isinstance(m, bs.PickedUpMessage):
			self._heldBy = m.node
		elif isinstance(m, bs.DroppedMessage):
			bs.animate(self._powText, 'scale', {0:0.01, 600: 0.03})
			bs.gameTimer(600, bs.WeakCall(self.pow))
		bsBomb.Bomb.handleMessage(self, m)

	def pow(self):
		self.explode()


class PlayerSpaz_Smash(bs.PlayerSpaz):
	multiplyer = 1
	isDead = False

	#def __init__(self, *args, **kwargs):
	#	super(self.__class__, self).init(*args, **kwargs)
	#	self.multiplyer = 0


	def handleMessage(self, m):
		if isinstance(m, bs.HitMessage):
			if not self.node.exists():
				return
			if self.node.invincible == True:
				bs.playSound(self.getFactory().blockSound, 1.0, position=self.node.position)
				return True

			# if we were recently hit, don't count this as another
			# (so punch flurries and bomb pileups essentially count as 1 hit)
			gameTime = bs.getGameTime()
			if self._lastHitTime is None or gameTime - self._lastHitTime > 1000:
				self._numTimesHit += 1
				self._lastHitTime = gameTime

			mag = m.magnitude * self._impactScale
			velocityMag = m.velocityMagnitude * self._impactScale

			damageScale = 0.22

			# if they've got a shield, deliver it to that instead..
			if self.shield is not None:
				if m.flatDamage:
					damage = m.flatDamage * self._impactScale
				else:
					# hit our spaz with an impulse but tell it to only return theoretical damage; not apply the impulse..
					self.node.handleMessage("impulse", m.pos[0], m.pos[1], m.pos[2],
											m.velocity[0], m.velocity[1], m.velocity[2],
											mag, velocityMag, m.radius, 1,
											m.forceDirection[0], m.forceDirection[1], m.forceDirection[2])
					damage = damageScale * self.node.damage

				self.shieldHitPoints -= damage

				self.shield.hurt = 1.0 - self.shieldHitPoints / self.shieldHitPointsMax
				# its a cleaner event if a hit just kills the shield without damaging the player..
				# however, massive damage events should still be able to damage the player..
				# this hopefully gives us a happy medium.
				maxSpillover = 500
				if self.shieldHitPoints <= 0:
					# fixme - transition out perhaps?..
					self.shield.delete()
					self.shield = None
					bs.playSound(self.getFactory().shieldDownSound, 1.0, position=self.node.position)
					# emit some cool lookin sparks when the shield dies
					t = self.node.position
					bs.emitBGDynamics(position=(t[0], t[1]+0.9, t[2]),
									  velocity=self.node.velocity,
									  count=random.randrange(20, 30), scale=1.0,
									  spread=0.6, chunkType='spark')

				else:
					bs.playSound(self.getFactory().shieldHitSound, 0.5, position=self.node.position)

				# emit some cool lookin sparks on shield hit
				bs.emitBGDynamics(position=m.pos,
								  velocity=(m.forceDirection[0]*1.0,
											m.forceDirection[1]*1.0,
											m.forceDirection[2]*1.0),
								  count=min(30, 5+int(damage*0.005)), scale=0.5, spread=0.3, chunkType='spark')


				# if they passed our spillover threshold, pass damage along to spaz
				if self.shieldHitPoints <= -maxSpillover:
					leftoverDamage = -maxSpillover - self.shieldHitPoints
					shieldLeftoverRatio = leftoverDamage / damage

					# scale down the magnitudes applied to spaz accordingly..
					mag *= shieldLeftoverRatio
					velocityMag *= shieldLeftoverRatio
				else:
					return True # good job shield!
			else: shieldLeftoverRatio = 1.0

			if m.flatDamage:
				damage = m.flatDamage * self._impactScale * shieldLeftoverRatio
			else:
				# hit it with an impulse and get the resulting damage
				#bs.screenMessage(str(velocityMag))
				if self.multiplyer > 3.0:
					# at about 8.0 the physics glitch out
					velocityMag *= min((3.0 + (self.multiplyer-3.0)/4), 7.5) ** 1.9
				else:
					velocityMag *= self.multiplyer ** 1.9
				self.node.handleMessage("impulse", m.pos[0], m.pos[1], m.pos[2],
										m.velocity[0], m.velocity[1], m.velocity[2],
										mag, velocityMag, m.radius, 0,
										m.forceDirection[0], m.forceDirection[1], m.forceDirection[2])

				damage = damageScale * self.node.damage
			self.node.handleMessage("hurtSound")

			# play punch impact sound based on damage if it was a punch
			if m.hitType == 'punch':

				self.onPunched(damage)

				# if damage was significant, lets show it
				#if damage > 350: bsUtils.showDamageCount('-'+str(int(damage/10))+"%",m.pos,m.forceDirection)

				# lets always add in a super-punch sound with boxing gloves just to differentiate them
				if m.hitSubType == 'superPunch':
					bs.playSound(self.getFactory().punchSoundStronger, 1.0,
								 position=self.node.position)

				if damage > 500:
					sounds = self.getFactory().punchSoundsStrong
					sound = sounds[random.randrange(len(sounds))]
				else: sound = self.getFactory().punchSound
				bs.playSound(sound, 1.0, position=self.node.position)

				# throw up some chunks
				bs.emitBGDynamics(position=m.pos,
								  velocity=(m.forceDirection[0]*0.5,
											m.forceDirection[1]*0.5,
											m.forceDirection[2]*0.5),
								  count=min(10, 1+int(damage*0.0025)), scale=0.3, spread=0.03)

				bs.emitBGDynamics(position=m.pos,
								  chunkType='sweat',
								  velocity=(m.forceDirection[0]*1.3,
											m.forceDirection[1]*1.3+5.0,
											m.forceDirection[2]*1.3),
								  count=min(30, 1 + int(damage * 0.04)),
								  scale=0.9,
								  spread=0.28)
				# momentary flash
				hurtiness = damage*0.003
				hurtiness = min(hurtiness, 750 * 0.003)
				punchPos = (m.pos[0]+m.forceDirection[0]*0.02,
							m.pos[1]+m.forceDirection[1]*0.02,
							m.pos[2]+m.forceDirection[2]*0.02)
				flashColor = (1.0, 0.8, 0.4)
				light = bs.newNode("light",
								   attrs={'position':punchPos,
										  'radius':0.12+hurtiness*0.12,
										  'intensity':0.3*(1.0+1.0*hurtiness),
										  'heightAttenuated':False,
										  'color':flashColor})
				bs.gameTimer(60, light.delete)


				flash = bs.newNode("flash",
								   attrs={'position':punchPos,
										  'size':0.17+0.17*hurtiness,
										  'color':flashColor})
				bs.gameTimer(60, flash.delete)

			if m.hitType == 'impact':
				bs.emitBGDynamics(position=m.pos,
								  velocity=(m.forceDirection[0]*2.0,
											m.forceDirection[1]*2.0,
											m.forceDirection[2]*2.0),
								  count=min(10, 1 + int(damage * 0.01)), scale=0.4, spread=0.1)

			if self.hitPoints > 0:

				# its kinda crappy to die from impacts, so lets reduce impact damage
				# by a reasonable amount if it'll keep us alive
				if m.hitType == 'impact' and damage > self.hitPoints:
					# drop damage to whatever puts us at 10 hit points, or 200 less than it used to be
					# whichever is greater (so it *can* still kill us if its high enough)
					newDamage = max(damage-200, self.hitPoints-10)
					damage = newDamage

				self.node.handleMessage("flash")
				# if we're holding something, drop it
				if damage > 0.0 and self.node.holdNode.exists():
					self.node.holdNode = bs.Node(None)
				#self.hitPoints -= damage
				self.multiplyer += min(damage / 2000, 0.15)
				if damage/2000 > 0.05:
					self.setScoreText(str(int((self.multiplyer-1)*100))+"%")
				#self.node.hurt = 1.0 - self.hitPoints/self.hitPointsMax
				self.node.hurt = 0.0
				# if we're cursed, *any* damage blows us up
				if self._cursed and damage > 0:
					bs.gameTimer(50, bs.WeakCall(self.curseExplode, m.sourcePlayer))
				# if we're frozen, shatter.. otherwise die if we hit zero
				#if self.frozen and (damage > 200 or self.hitPoints <= 0):
				#	self.shatter()
				#elif self.hitPoints <= 0:
				#	self.node.handleMessage(bs.DieMessage(how='impact'))

			# if we're dead, take a look at the smoothed damage val
			# (which gives us a smoothed average of recent damage) and shatter
			# us if its grown high enough
			#if self.hitPoints <= 0:
			#	damageAvg = self.node.damageSmoothed * damageScale
			#	if damageAvg > 1000:
			#		self.shatter()
		elif isinstance(m, bs.DieMessage):
			self.oob_effect()
			super(self.__class__, self).handleMessage(m)
		elif isinstance(m, bs.PowerupMessage):
			if m.powerupType == 'health':
				if self.multiplyer > 2:
					self.multiplyer *= 0.5
				else:
					self.multiplyer *= 0.75
				self.multiplyer = max(1, self.multiplyer)
				self.setScoreText(str(int((self.multiplyer-1)*100))+"%")
			super(self.__class__, self).handleMessage(m)
		else:
			super(self.__class__, self).handleMessage(m)

	def oob_effect(self):
		if self.isDead:
			return
		self.isDead = True
		if self.multiplyer > 1.25:
			blastType = 'tnt'
			radius = min(self.multiplyer * 5, 20)
		else:
			# penalty for killing people with low multiplyer
			blastType = 'ice'
			radius = 7.5

		bs.Blast(position=self.node.position, blastRadius=radius, blastType=blastType).autoRetain()



def bsGetAPIVersion():
	return 4

def bsGetGames():
	return [SuperSmash]

class SuperSmash(bs.TeamGameActivity):

	@classmethod
	def getName(cls):
		return 'Super Smash'

	@classmethod
	def getScoreInfo(cls):
		if cls == SuperSmash:
			if bs.getActivity().__class__ == SuperSmash and hasattr(bs.getActivity(), 'timeLimitOnly'):
				# some sanity checks that probably arent needed
				if bs.getActivity().timeLimitOnly:
					# if its timeonlymode return different scoreinfo
					return {'scoreName':'Deaths',
							'scoreType':'points',
							'scoreVersion':'B',
							'noneIsWinner':True,
							'lowerIsBetter': True}

		return {'scoreName':'Survived',
			'scoreType':'seconds',
			'scoreVersion':'B',
			'noneIsWinner':True}

	@classmethod
	def getDescription(cls, sessionType):
		return "Kill everyone with your knockback."


	def getInstanceDescription(self):
		return 'Knock everyone off the map.'

	def getInstanceScoreBoardDescription(self):
		if self.timeLimitOnly:
			return 'Knock everyone off the map.'
		else:
			if self.settings['Lives'] > 1:
				return ('Knock the others off ${ARG1} times.', self.settings['Lives'])
			else:
				return 'Knock everyone off once.'


	@classmethod
	def supportsSessionType(cls, sessionType):
		return True if (issubclass(sessionType, bs.TeamsSession)
						or issubclass(sessionType, bs.FreeForAllSession)) else False

	@classmethod
	def getSupportedMaps(cls, sessionType):
		maps = bs.getMapsSupportingPlayType("melee")
		for m in ['Lake Frigid', 'Hockey Stadium', 'Football Stadium']:
			# remove maps without bounds
			maps.remove(m)
		return maps

	@classmethod
	def getSettings(cls, sessionType):
		return [("Time Limit", {'choices':[('None', 0), ('1 Minute', 60), ('2 Minutes', 120),
											('5 Minutes', 300)], 'default': 0}),
				("Lives (0 = Unlimited)", {'minValue': 0, 'default': 3, 'increment': 1}),
				("Epic Mode", {'default': False})]

	def __init__(self, settings):
		bs.TeamGameActivity.__init__(self, settings)
		self.settings['Lives'] = self.settings["Lives (0 = Unlimited)"]
		self.timeLimitOnly = (self.settings['Lives'] == 0)
		if self.timeLimitOnly:
			self.settings['Time Limit'] = max(60, self.settings['Time Limit'])

		if self.settings['Epic Mode']:
			self._isSlowMotion = True

		# print messages when players die (since its meaningful in this game)
		self.announcePlayerDeaths = True

		self._lastPlayerDeathTime = None

		self._startGameTime = 1000


	def onTransitionIn(self):
		bs.TeamGameActivity.onTransitionIn(self, music='Epic' if self.settings['Epic Mode'] else 'Survival')
		self._startGameTime = bs.getGameTime()

	def onBegin(self):
		bs.TeamGameActivity.onBegin(self)
		self.setupStandardTimeLimit(self.settings['Time Limit'])
		self.setupStandardPowerupDrops(enableTNT=False)
		self._pow = None
		self._tntDropTimer = bs.Timer(1000 * 30, bs.WeakCall(self._dropPowBox), repeat=True)
		self._updateIcons()

	def _dropPowBox(self):
		if self._pow is not None and self._pow.exists():
			return
		if len(self.getMap().tntPoints) == 0:
			return
		pos = random.choice(self.getMap().tntPoints)
		pos = (pos[0], pos[1] + 1, pos[2])
		self._pow = PowBox(position=pos, velocity=(0, 1, 0))

	def onPlayerJoin(self, player):
		if 'lives' not in player.gameData:
			player.gameData['lives'] = self.settings['Lives']
		# create our icon and spawn
		player.gameData['icons'] = [Icon(player, position=(0, 50), scale=0.8)]
		if player.gameData['lives'] > 0 or self.timeLimitOnly:
			self.spawnPlayer(player)

		# dont waste time doing this until begin
		if self.hasBegun():
			self._updateIcons()

	def onPlayerLeave(self, player):
		bs.TeamGameActivity.onPlayerLeave(self, player)

		player.gameData['icons'] = None

		# update icons in a moment since our team will be gone from the list then
		bs.gameTimer(0, self._updateIcons)

		if sum([len(team.players) >= 1 for team in self.teams]) < 2:
			self.endGame()

	def _updateIcons(self):
		# in free-for-all mode, everyone is just lined up along the bottom
		if isinstance(self.getSession(), bs.FreeForAllSession):
			count = len(self.teams)
			xOffs = 85
			x = xOffs*(count-1) * -0.5
			for team in self.teams:
				if len(team.players) > 1:
					print('WTF have', len(team.players), 'players in ffa team')
				elif len(team.players) == 1:
					player = team.players[0]
					if len(player.gameData['icons']) != 1:
						print('WTF have', len(player.gameData['icons']), 'icons in non-solo elim')
					for icon in player.gameData['icons']:
						icon.setPositionAndScale((x, 30), 0.7)
						icon.updateForLives()
					x += xOffs

		# in teams mode we split up teams
		else:
			for team in self.teams:
				if team.getID() == 0:
					x = -50
					xOffs = -85
				else:
					x = 50
					xOffs = 85
				for player in team.players:
					if len(player.gameData['icons']) != 1:
						print('WTF have', len(player.gameData['icons']), 'icons in non-solo elim')
					for icon in player.gameData['icons']:
						icon.setPositionAndScale((x, 30), 0.7)
						icon.updateForLives()
					x += xOffs


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

		spaz = PlayerSpaz_Smash(color=player.color,
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
		light = bs.newNode('light', attrs={'color': lightColor})
		spaz.node.connectAttr('position', light, 'position')
		bsUtils.animate(light, 'intensity', {0: 0, 250: 1, 500: 0})
		bs.gameTimer(500, light.delete)


		# if we have any icons, update their state
		for icon in player.gameData['icons']:
			icon.handlePlayerSpawned()



	# various high-level game events come through this method
	def handleMessage(self, m):
		if isinstance(m, bs.PlayerSpazDeathMessage):

			bs.TeamGameActivity.handleMessage(self, m) # augment standard behavior
			player = m.spaz.getPlayer()

			player.gameData['lives'] -= 1

			# if we have any icons, update their state
			for icon in player.gameData['icons']:
				icon.handlePlayerDied()

			# play big death sound on our last death or for every one in solo mode
			if  player.gameData['lives'] == 0:
				bs.playSound(bs.Spaz.getFactory().singlePlayerDeathSound)

			# if we hit zero lives we're dead and the game might be over
			if player.gameData['lives'] == 0 and not self.timeLimitOnly:

				# if the whole team is dead, make note of how long they lasted
				if all(teammate.gameData['lives'] == 0 for teammate in player.getTeam().players):

					# log the team survival if we're the last player on the team
					player.getTeam().gameData['survivalSeconds'] = (bs.getGameTime()-self._startGameTime)/1000

					# if someone has won, set a timer to end shortly
					# (allows the dust to settle and draws to occur if deaths are close enough)
					if len(self._getLivingTeams()) < 2:
						self._roundEndTimer = bs.Timer(1000, self.endGame)

			# we still have lives; yay!
			else:
				self.respawnPlayer(player)

		else:
			# default handler:
			super(self.__class__, self).handleMessage(m)#bs.TeamGameActivity.handleMessage(self,m)

	def endGame(self):

		curTime = bs.getGameTime()
		if not self.timeLimitOnly:
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
		else:
			results = bs.TeamGameResults()
			for team in self.teams:
				deaths = sum([0 - player.gameData['lives'] for player in team.players])
				results.setTeamScore(team, deaths)
			self.end(results=results)

	def _getLivingTeams(self):
		return [team for team in self.teams if len(team.players) > 0 and any(player.gameData['lives'] > 0 for player in team.players)]
