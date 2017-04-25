#Made by Paolo Valerdi
import bs
import random

def bsGetAPIVersion():
    return 4

def bsGetGames():
    return [GuessTheBombGame]

def bsGetLevels():
    return [bs.Level('Guess The Bomb',displayName='${GAME}',gameType=GuessTheBombGame,settings={},previewTexName='rampagePreview'),
            bs.Level('Epic Guess The Bomb',displayName='${GAME}',gameType=GuessTheBombGame,settings={'Epic Mode':True},previewTexName='rampagePreview')]

class GuessTheBombGame(bs.TeamGameActivity):

    @classmethod
    def getName(cls):
        return 'Guess The Bomb'

    @classmethod
    def getScoreInfo(cls):
        return {'scoreName':'Survived',
                'scoreType':'milliseconds',
                'scoreVersion':'B'}

    @classmethod
    def getDescription(cls,sessionType):
        return 'Dodge the falling bombs.'

    @classmethod
    def getSupportedMaps(cls,sessionType):
        return ['Rampage']

    @classmethod
    def getSettings(cls,sessionType):
        return [("Epic Mode",{'default':False})]

    @classmethod
    def supportsSessionType(cls,sessionType):
        return True if (issubclass(sessionType,bs.TeamsSession)
                        or issubclass(sessionType,bs.FreeForAllSession)
                        or issubclass(sessionType,bs.CoopSession)) else False

    def __init__(self,settings):
        bs.TeamGameActivity.__init__(self,settings)

        if self.settings['Epic Mode']: self._isSlowMotion = True

        self.announcePlayerDeaths = True

        self._lastPlayerDeathTime = None

    def onTransitionIn(self):
        bs.TeamGameActivity.onTransitionIn(self, music='Epic' if self.settings['Epic Mode'] else 'Survival')

    def onBegin(self):
        bs.TeamGameActivity.onBegin(self)
        self._meteorTime = 3000
        t = 7500 if len(self.players) > 2 else 4000
        if self.settings['Epic Mode']: t /= 4
        bs.gameTimer(t,self._decrementMeteorTime,repeat=True)

        t = 3000
        if self.settings['Epic Mode']: t /= 4
        bs.gameTimer(t,self._setMeteorTimer)

        self._timer = bs.OnScreenTimer()
        self._timer.start()

    def spawnPlayer(self,player):
        spaz = self.spawnPlayerSpaz(player)
        spaz.connectControlsToPlayer(enablePunch=False,
                                     enableBomb=False,
                                     enablePickUp=False)

        spaz.playBigDeathSound = True

    def handleMessage(self,m):

        if isinstance(m,bs.PlayerSpazDeathMessage):

            bs.TeamGameActivity.handleMessage(self,m)

            deathTime = bs.getGameTime()

            m.spaz.getPlayer().gameData['deathTime'] = deathTime

            if isinstance(self.getSession(),bs.CoopSession):
                bs.pushCall(self._checkEndGame)
                self._lastPlayerDeathTime = deathTime
            else:
                bs.gameTimer(1000,self._checkEndGame)

        else:
            bs.TeamGameActivity.handleMessage(self,m)

    def _checkEndGame(self):
        livingTeamCount = 0
        for team in self.teams:
            for player in team.players:
                if player.isAlive():
                    livingTeamCount += 1
                    break

        if isinstance(self.getSession(),bs.CoopSession):
            if livingTeamCount <= 0: self.endGame()
        else:
            if livingTeamCount <= 1: self.endGame()

    def _setMeteorTimer(self):
        bs.gameTimer(int((1.0+0.2*random.random())*self._meteorTime),self._dropBombCluster)

    def _dropBombCluster(self):

        if False:
            bs.newNode('locator',attrs={'position':(8,6,-5.5)})
            bs.newNode('locator',attrs={'position':(8,6,-2.3)})
            bs.newNode('locator',attrs={'position':(-7.3,6,-5.5)})
            bs.newNode('locator',attrs={'position':(-7.3,6,-2.3)})

        delay = 0
        for i in range(random.randrange(1,3)):
            types = ["normal", "ice", "sticky", "impact"]
            magic = random.choice(types)
            bt = magic
            pos = (-7.3+15.3*random.random(),11,-5.5+2.1*random.random())
            vel = ((-5.0+random.random()*30.0) * (-1.0 if pos[0] > 0 else 1.0), -4.0,0)
            bs.gameTimer(delay,bs.Call(self._dropBomb,pos,vel,bt))
            delay += 100
        self._setMeteorTimer()

    def _dropBomb(self,position,velocity,bombType):
        b = bs.Bomb(position=position,velocity=velocity,bombType=bombType).autoRetain()

    def _decrementMeteorTime(self):
        self._meteorTime = max(10,int(self._meteorTime*0.9))

    def endGame(self):

        curTime = bs.getGameTime()

        for team in self.teams:
            for player in team.players:

                if 'deathTime' not in player.gameData: player.gameData['deathTime'] = curTime+1

                score = (player.gameData['deathTime']-self._timer.getStartTime())/1000
                if 'deathTime' not in player.gameData: score += 50
                self.scoreSet.playerScored(player,score,screenMessage=False)

        self._timer.stop(endTime=self._lastPlayerDeathTime)

        results = bs.TeamGameResults()

        for team in self.teams:

            longestLife = 0
            for player in team.players:
                longestLife = max(longestLife,(player.gameData['deathTime'] - self._timer.getStartTime()))
            results.setTeamScore(team,longestLife)

        self.end(results=results)