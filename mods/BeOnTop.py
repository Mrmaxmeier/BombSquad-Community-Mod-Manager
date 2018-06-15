import bs
import random

__author__ = "YashKandalkar"

def bsGetAPIVersion():
    return 4

def bsGetGames():
    return [BeOnTop]

class BeOnTop(bs.TeamGameActivity):
    #This game mod is created by YashKandalkar
    @classmethod
    def getName(cls):
        return 'Be On Top!'

    @classmethod
    def getDescription(cls, sessionType):
        return "Stay on top of this map to survive!\nYour health will be reduced if you're not."

    @classmethod
    def supportsSessionType(cls, sessionType):
        return True if issubclass(sessionType, bs.FreeForAllSession) else False

    @classmethod
    def getSupportedMaps(cls,sessionType):
        return ["Crag Castle"]

    @classmethod
    def getSettings(cls,sessionType):
        return [("Epic Mode", {'default' : False})]

    def __init__(self,settings):
        bs.TeamGameActivity.__init__(self, settings)

        if self.settings['Epic Mode']: 
            self._isSlowMotion = True

        self.announcePlayerDeaths = True

        self._lastPlayerDeathTime = None
        #self._timer = None #for some reason _timer does not gets set as an attribute

    def getInstanceDescription(self):
        return ("Go as high as you can!")

    def getInstanceScoreBoardDescription(self):
        return ("Stay on top of this map to survive!")

    def onTransitionIn(self):
        bs.TeamGameActivity.onTransitionIn(self, music='Epic' if self.settings['Epic Mode'] else 'Keep Away')

    def onBegin(self):

        bs.TeamGameActivity.onBegin(self)
        self.setupStandardPowerupDrops()

        if 0:
            bs.newNode('locator', attrs = {'position' : (-3, -2, 1.5)})
            bs.newNode('locator', attrs = {'position' : (0, 0, 0)})
            bs.newNode('locator', attrs = {'position' : ((-3, 6.5, 0))})
            bs.newNode('locator', attrs = {'position' : ((3, 6.5, 0))})

        self._timer = bs.OnScreenTimer()
        self._timer.start()


        def _reduceHealth():
            for player in self.players:
                if hasattr(player.actor, 'node') and player.isAlive():
                    actor = player.actor
                    position = actor.node.position
                    if position[1] < 9:
                        actor.node.handleMessage(bs.HitMessage(pos = (position[0], position[1]+1, position[2]),
                                                               velocity = (0,0,0),
                                                               magnitude = 100 if len(self.players) > 4 else 200,
                                                               hitType = 'explosion',
                                                               hitSubType = 'normal',
                                                               radius = 1.1,
                                                               sourcePlayer = player))
                        if actor.hitPoints <= 0:
                            player.gameData['_playerNode'].node.handleMessage(bs.DieMessage(immediate = False, how = 'impact'))
                            return
                        
        bs.gameTimer(1000, bs.Call(_reduceHealth), repeat = 1)

        def onlyOnePlayer():
            if len(self.players) <= 1:
                self.endGame()
        bs.gameTimer(5000, onlyOnePlayer)



    def onPlayerJoin(self, player):
        # don't allow joining after we start
        # (would enable leave/rejoin tomfoolery)
        if self.hasBegun():
            bs.screenMessage(bs.Lstr(resource='playerDelayedJoinText', subs=[('${PLAYER}', player.getName(full=True))]), color=(0,1,0))
            # for score purposes, mark them as having died right as the game started
            return

        #FIX ME!
        #onPlayerJoin is being caller before onBegin (?)
        if not hasattr(self, '_timer'):
            self._timer = bs.OnScreenTimer()
            self._timer.start()
        self.spawnPlayer(player)
        

    def onPlayerLeave(self, player):
        # augment default behavior...
        bs.TeamGameActivity.onPlayerLeave(self, player)
        #end the game if everyone left the party.
        deathTime = bs.getGameTime()
        if isinstance(self.getSession(), bs.FreeForAllSession):
                bs.pushCall(self._checkEndGame)
                self._lastPlayerDeathTime = deathTime # also record this for a final setting of the clock..
        else:
            bs.gameTimer(1000, self._checkEndGame)

    def spawnPlayer(self, player):
        spaz = self.spawnPlayerSpaz(player, position = random.choice([(-3, 7, 0), (3, 7, 0)]))
        player.gameData['deathTime'] = self._timer.getStartTime()
        spaz.playBigDeathSound = False

    def handleMessage(self, m):
        if isinstance(m, bs.PlayerSpazDeathMessage):
            
            deathTime = bs.getGameTime()

            bs.TeamGameActivity.handleMessage(self,m) # (augment standard behavior)
            m.spaz.getPlayer().gameData['deathTime'] = deathTime
            if isinstance(self.getSession(), bs.FreeForAllSession):
                bs.pushCall(self._checkEndGame)
                self._lastPlayerDeathTime = deathTime # also record this for a final setting of the clock..
            else:
                bs.gameTimer(1000, self._checkEndGame)

        else:
            bs.TeamGameActivity.handleMessage(self, m)

    def _checkEndGame(self):
        livingTeamCount = 0
        for team in self.teams:
            for player in team.players:
                if player.isAlive():
                    livingTeamCount += 1
                    break

        if isinstance(self.getSession(), bs.FreeForAllSession):
            if livingTeamCount <= 0: self.endGame()
        else:
            if livingTeamCount <= 1: self.endGame()

    def endGame(self):
        current_time = bs.getGameTime()
        
        for team in self.teams:
            for player in team.players:
                if 'deathTime' not in player.gameData: 
                    player.gameData['deathTime'] = current_time + 1
                    
                score = (player.gameData['deathTime'] - self._timer.getStartTime())/1000
                if 'deathTime' not in player.gameData: 
                    score += 50 # a bit extra for survivors
                self.scoreSet.playerScored(player, score, screenMessage=False)

        results = bs.TeamGameResults()

        for team in self.teams:
            # set the team score to the max time survived by any player on that team
            longestLife = 0
            for player in team.players:
                longestLife = max(longestLife, (player.gameData['deathTime'] - self._timer.getStartTime()))
            results.setTeamScore(team, longestLife)

        self.end(results = results)
