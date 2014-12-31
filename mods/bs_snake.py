#ModManager#{"author": "Mrmaxmeier", "dependencies": ["bs_ownUtils.py"]}#ModManager# <-- json stuff for the modmanager

import bs
from bs_ownUtils import RaceTimer

def bsGetAPIVersion(): return 3

def bsGetGames():
    return [SnakeGame]

class SnakeGame(bs.TeamGameActivity):
    tailIncrease = 0.2
    maxTailLength = 30
    mineDelay = 0.5

    @classmethod
    def getName(cls):
        return 'Snake'

    @classmethod
    def getScoreInfo(cls):
        return {'scoreName':'Mines Planted'}
    
    @classmethod
    def getDescription(cls,sessionType):
        return ('Plant as many Mines as you can')

    @classmethod
    def supportsSessionType(cls,sessionType):
        return True if (issubclass(sessionType,bs.TeamsSession)
                        or issubclass(sessionType,bs.FreeForAllSession)) else False

    @classmethod
    def getSupportedMaps(cls,sessionType):
        return bs.getMapsSupportingPlayType("keepAway")

    @classmethod
    def getSettings(cls,sessionType):
        return [("Mines to win",{'choices':[('Few', 60),('Some', 80),('Some more',120), ('Many much', 140), ('wow', 200)],'default':80}),
                ("Epic Mode",{'default':False})]

    def __init__(self,settings):
        bs.TeamGameActivity.__init__(self,settings)
        if self.settings['Epic Mode']: self._isSlowMotion = True
        self._scoreBoard = bs.ScoreBoard()
        self._swipSound = bs.getSound("swip")
        self._countDownSounds = {10:bs.getSound('announceTen'),
                                 9:bs.getSound('announceNine'),
                                 8:bs.getSound('announceEight'),
                                 7:bs.getSound('announceSeven'),
                                 6:bs.getSound('announceSix'),
                                 5:bs.getSound('announceFive'),
                                 4:bs.getSound('announceFour'),
                                 3:bs.getSound('announceThree'),
                                 2:bs.getSound('announceTwo'),
                                 1:bs.getSound('announceOne')}
        self.raceTimer = RaceTimer()
        self.raceTimer.onFinish = bs.WeakCall(self.timerCallback)
        self.maxTailLength = self.settings['Mines to win'] * self.tailIncrease
        self.isFinished = False
        self.hasStarted = False

    def getInstanceDescription(self):
        return 'Run around and don\'t get killed.'


    def getInstanceScoreBoardDescription(self):
        return ('Survive ${ARG1} mines', self.settings['Mines to win'])

    def onTransitionIn(self):
        bs.TeamGameActivity.onTransitionIn(self, music='Epic' if self.settings['Epic Mode'] else 'Chosen One')

    def onTeamJoin(self,team):
        team.gameData['tailLength'] = 0
        team.gameData['minesPlanted'] = 0
        self._updateScoreBoard()

    def onPlayerJoin(self, player):
        bs.TeamGameActivity.onPlayerJoin(self, player)
        player.gameData['mines'] = []
        if self.hasStarted:
            call = bs.WeakCall(self._spawnMine, player)
            self.mineTimers.append(bs.Timer(int(self.mineDelay * 1000), call,repeat=True))

    def onPlayerLeave(self,player):
        bs.TeamGameActivity.onPlayerLeave(self,player)
            
    def onBegin(self):
        self.mineTimers = []
        self.raceTimer.start()
        # test...
        if not all(player.exists() for player in self.players):
            bs.printError("Nonexistant player in onBegin: "+str([str(p) for p in self.players])+': we are '+str(player))

        
        bs.TeamGameActivity.onBegin(self)

    def timerCallback(self):
        for player in self.players:
            call = bs.WeakCall(self._spawnMine, player)
            self.mineTimers.append(bs.Timer(int(self.mineDelay * 1000), call,repeat=True))
        self.hasStarted = True


    def _spawnMine(self, player):
        #Dont spawn Mines if player is ded
        if not player.exists() or not player.isAlive(): return

        gameData = player.getTeam().gameData

        # no more mines for players who've already won
        # to get a working draw
        if gameData['minesPlanted'] >= self.settings['Mines to win']: return

        gameData['minesPlanted'] += 1
        gameData['tailLength'] = gameData['minesPlanted'] * self.tailIncrease + 2
        if gameData['minesPlanted'] >= self.settings['Mines to win'] - 10:
            num2win = self.settings['Mines to win'] - gameData['minesPlanted'] + 1
            if num2win in self._countDownSounds:
                bs.playSound(self._countDownSounds[num2win])



        self._updateScoreBoard()

        if player.getTeam().gameData['tailLength'] < 2:
            return

        pos = player.actor.node.position
        pos = (pos[0], pos[1] + 2, pos[2])
        mine = bs.Bomb(position=pos, velocity=(0, 0, 0), bombType='landMine', blastRadius=2.0, sourcePlayer=player, owner=player).autoRetain()
        player.gameData['mines'].append(mine)
        bs.gameTimer(int(self.mineDelay * 1000), bs.WeakCall(mine.arm))
        bs.gameTimer(int(int(player.getTeam().gameData['tailLength'] + 1) * self.mineDelay * 1000), bs.WeakCall(self._removeMine, player, mine))

    def _removeMine(self, player, mine):
        #kill it with(out) fire
        if mine in player.gameData:
            player.gameData['mines'].remove(mine)
        mine.handleMessage(bs.DieMessage())
        mine = None
        


    def endGame(self):
        results = bs.TeamGameResults()
        for team in self.teams: results.setTeamScore(team,min(int(team.gameData['minesPlanted']), self.settings['Mines to win']))
        self.end(results=results,announceDelay=0)


    def handleMessage(self,m):
        if isinstance(m,bs.PlayerSpazDeathMessage):
            bs.TeamGameActivity.handleMessage(self,m) # augment standard behavior
            player = m.spaz.getPlayer()
            for mine in player.gameData['mines']:
                self._removeMine(player, mine)
            self.respawnPlayer(player)
        else: bs.TeamGameActivity.handleMessage(self,m)

    def _updateScoreBoard(self):
        for team in self.teams:
            self._scoreBoard.setTeamValue(team, min(int(team.gameData['minesPlanted']), self.settings['Mines to win']), self.settings['Mines to win'], countdown=False)
            if int(team.gameData['minesPlanted']) >= self.settings['Mines to win']:
                bs.gameTimer(500, bs.WeakCall(self.endGame))
                self.isFinished = True
