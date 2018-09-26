# Jumping Contest

# This simple game tests each player's ability in an underappreciated aspect of the game: jumping.
import bs
import bsUtils
import random

def bsGetAPIVersion():
    return 4

def bsGetGames():
    return [JumpingContest]

def bsGetLevels():
    return [bs.Level('Jumping Contest',
                     displayName='${GAME}',
                     gameType=JumpingContest,
                     settings={},
                     previewTexName='courtyardPreview')]


class RaceTimer:
	# the race timer to start things off
	def __init__(self, incTime=1000):
		lightY = 150
		self.pos = 0
		self._beep1Sound = bs.getSound('raceBeep1')
		self._beep2Sound = bs.getSound('raceBeep2')
		self.lights = []
		for i in range(4):
			l = bs.newNode('image',
						   attrs={'texture':bs.getTexture('nub'),
								  'opacity':1.0,
								  'absoluteScale':True,
								  'position':(-75+i*50, lightY),
								  'scale':(50, 50),
								  'attach':'center'})
			bs.animate(l, 'opacity', {10:0, 1000:1.0})
			self.lights.append(l)
		self.lights[0].color = (0.2, 0, 0)
		self.lights[1].color = (0.2, 0, 0)
		self.lights[2].color = (0.2, 0.05, 0)
		self.lights[3].color = (0.0, 0.3, 0)
		self.cases = {1: self._doLight1, 2: self._doLight2, 3: self._doLight3, 4: self._doLight4}
		self.incTimer = None
		self.incTime = incTime

	def start(self):
		self.incTimer = bs.Timer(self.incTime, bs.WeakCall(self.increment), timeType="game", repeat=True)

	def _doLight1(self):
		self.lights[0].color = (1.0, 0, 0)
		bs.playSound(self._beep1Sound)

	def _doLight2(self):
		self.lights[1].color = (1.0, 0, 0)
		bs.playSound(self._beep1Sound)

	def _doLight3(self):
		self.lights[2].color = (1.0, 0.3, 0)
		bs.playSound(self._beep1Sound)

	def _doLight4(self):
		self.lights[3].color = (0.0, 1.0, 0)
		bs.playSound(self._beep2Sound)
		for l in self.lights:
			bs.animate(l, 'opacity', {0: 1.0, 1000: 0.0})
			bs.gameTimer(1000, l.delete)
		self.incTimer = None
		self.onFinish()
		del self

	def onFinish(self):
		pass

	def onIncrement(self):
		pass

	def increment(self):
		self.pos += 1
		if self.pos in self.cases:
			self.cases[self.pos]()
		self.onIncrement()

class JumpSpaz(bs.PlayerSpaz):
    def onMove(self,x,y):
        pass
    def onMoveLeftRight(self,value):
        pass
    def onMoveUpDown(self,value):
        pass
    def onPunchPress(self):
        self.getActivity().setEndHeight(self)
    def onJumpPress(self):
        self.getActivity().setStartHeight(self)
        bs.PlayerSpaz.onJumpPress(self)

class JumpingContest(bs.TeamGameActivity):

    @classmethod
    def getName(cls):
        return "Jumping Contest"

    @classmethod
    def getDescription(cls, sessionType):
        return "Jump as high as you can."

    @classmethod
    def getScoreInfo(cls):
        return{'scoreType':'points'}

    @classmethod
    def getSettings(cls, sessionType):
        return [("Epic Mode", {'default': False})]
    
    @classmethod
    def getSupportedMaps(cls, sessionType):
        listy = bs.getMapsSupportingPlayType('melee')
        listy.remove("Happy Thoughts")
        return listy

    @classmethod
    def supportsSessionType(cls, sessionType):
        return True if issubclass(sessionType, bs.FreeForAllSession) or issubclass(sessionType, bs.TeamsSession) else False

    def __init__(self,settings):
        bs.TeamGameActivity.__init__(self,settings)
        self.called = False
        if self.settings['Epic Mode']: self._isSlowMotion = True
        self.info = bs.NodeActor(bs.newNode('text',
                                                   attrs={'vAttach': 'bottom',
                                                          'hAlign': 'center',
                                                          'vrDepth': 0,
                                                          'color': (0,.2,0),
                                                          'shadow': 1.0,
                                                          'flatness': 1.0,
                                                          'position': (0,0),
                                                          'scale': 0.8,
                                                          'text': "Created by MattZ45986 on Github",
                                                          }))
        self._scoredis = bs.ScoreBoard()
        self.timer = bs.OnScreenCountdown(30,self.endGame)
        
        
    def onTransitionIn(self):
        bs.TeamGameActivity.onTransitionIn(self,music='FlagCatcher')

    def getInstanceScoreBoardDescription(self):
        return ('Punch to lock in your score')

    def onBegin(self):
        bs.TeamGameActivity.onBegin(self)
        s = self.settings
        bs.gameTimer(3500, bs.Call(self.doRaceTimer))
        for team in self.teams:
            team.gameData['score'] = 0
        self.updateScore()

    def onPlayerJoin(self, player):
        if self.hasBegun():
            bs.screenMessage(bs.Lstr(resource='playerDelayedJoinText',subs=[('${PLAYER}',player.getName(full=True))]),color=(0,1,0))
            self.checkEnd()
            return
        else:
            self.spawnPlayerSpaz(player)
    def spawnPlayerSpaz(self,player,position=(0,0,0),angle=None):
        name = player.getName()
        color = player.color
        highlight = player.highlight

        lightColor = bsUtils.getNormalizedColor(color)
        displayColor = bs.getSafeColor(color,targetIntensity=0.75)
        position = self.getMap().getFFAStartPosition(self.players)
        spaz = JumpSpaz(color=color,
                             highlight=highlight,
                             character=player.character,
                             player=player)
        player.setActor(spaz)
        spaz.handleMessage(bs.StandMessage(position,angle if angle is not None else random.uniform(0,360)))

    def handleMessage(self, m):
        if isinstance(m, bs.PlayerSpazDeathMessage):
            bs.TeamGameActivity.handleMessage(self,m)
            m.spaz.getPlayer().actor.disconnectControlsFromPlayer()
            m.spaz.getPlayer().sessionData['score'] = 0

    def updateScore(self):
        for team in self.teams:
            self._scoredis.setTeamValue(team,round(team.gameData['score'],2))

    def startJump(self):
        for player in self.players:
            player.actor.connectControlsToPlayer(enableBomb=False, enablePunch=True, enablePickUp=False, enableRun=False, enableFly = False)
            player.sessionData['jumped'] = False
        self.timer.start()
        self.backupTimer = bs.gameTimer(30000,self.backupEnd)

    def doRaceTimer(self):
	self.raceTimer = RaceTimer()
	bs.gameTimer(1000, bs.Call(self.raceTimer.start))
	self.raceTimer.onFinish = bs.WeakCall(self.startJump)

    def setStartHeight(self, player):
        player = player.getPlayer()
        player.sessionData['height'] = player.actor.node.positionCenter[1]
        player.sessionData['jumped'] = True

    def setEndHeight(self,player):
        player = player.getPlayer()
        if not player.sessionData['jumped']: return
        player.sessionData['score'] = (player.actor.node.positionCenter[1] - player.sessionData['height']) * 10
        if player.sessionData['score'] > player.getTeam().gameData['score']: player.getTeam().gameData['score'] = player.sessionData['score']
        self.updateScore()

    def backupEnd(self):
        if not self.called: self.endGame()

    def endGame(self):
        self.called = True
        results = bs.TeamGameResults()
        for team in self.teams:
            results.setTeamScore(team, round(team.gameData['score'],2))
        self.end(results=results)
