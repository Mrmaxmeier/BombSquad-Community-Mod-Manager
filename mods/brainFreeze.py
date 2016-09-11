import bs
import random

def bsGetAPIVersion():
    return 4

def bsGetGames():
    return [BrainFreezeGame]

def bsGetLevels():
    return [bs.Level('Brain Freeze',displayName='${GAME}',gameType=BrainFreezeGame,settings={},previewTexName='rampagePreview'),
            bs.Level('Epic Brain Freeze',displayName='${GAME}',gameType=BrainFreezeGame,settings={'Epic Mode':True},previewTexName='rampagePreview')]

class BrainFreezeGame(bs.TeamGameActivity):

    @classmethod
    def getName(cls):
        return 'Brain Freeze'

    @classmethod
    def getScoreInfo(cls):
        return {'scoreName':'Survived',
                'scoreType':'milliseconds',
                'scoreVersion':'B'}
    
    @classmethod
    def getDescription(cls,sessionType):
        return 'Dodge the falling ice bombs.'

    # we're currently hard-coded for one map..
    @classmethod
    def getSupportedMaps(cls,sessionType):
        return ['Rampage']

    @classmethod
    def getSettings(cls,sessionType):
        return [("Epic Mode",{'default':False})]
    
    # we support teams, free-for-all, and co-op sessions
    @classmethod
    def supportsSessionType(cls,sessionType):
        return True if (issubclass(sessionType,bs.TeamsSession)
                        or issubclass(sessionType,bs.FreeForAllSession)
                        or issubclass(sessionType,bs.CoopSession)) else False

    def __init__(self,settings):
        bs.TeamGameActivity.__init__(self,settings)

        if self.settings['Epic Mode']: self._isSlowMotion = True
        
        # print messages when players die (since its meaningful in this game)
        self.announcePlayerDeaths = True

        self._lastPlayerDeathTime = None
        
    # called when our game is transitioning in but not ready to start..
    # ..we can go ahead and set our music and whatnot
    def onTransitionIn(self):
        bs.TeamGameActivity.onTransitionIn(self, music='Epic' if self.settings['Epic Mode'] else 'Survival')


    # called when our game actually starts
    def onBegin(self):

        bs.TeamGameActivity.onBegin(self)
        # drop a wave every few seconds.. and every so often drop the time between waves
        # ..lets have things increase faster if we have fewer players
        self._meteorTime = 3000
        t = 7500 if len(self.players) > 2 else 4000
        if self.settings['Epic Mode']: t /= 4
        bs.gameTimer(t,self._decrementMeteorTime,repeat=True)

        # kick off the first wave in a few seconds
        t = 3000
        if self.settings['Epic Mode']: t /= 4
        bs.gameTimer(t,self._setMeteorTimer)

        self._timer = bs.OnScreenTimer()
        self._timer.start()
        
        
    # overriding the default character spawning..
    def spawnPlayer(self,player):

        spaz = self.spawnPlayerSpaz(player)

        # lets reconnect this player's controls to this
        # spaz but *without* the ability to attack or pick stuff up
        spaz.connectControlsToPlayer(enablePunch=False,
                                     enableBomb=False,
                                     enablePickUp=False)

        # also lets have them make some noise when they die..
        spaz.playBigDeathSound = True


    # various high-level game events come through this method
    def handleMessage(self,m):

        if isinstance(m,bs.PlayerSpazDeathMessage):

            bs.TeamGameActivity.handleMessage(self,m) # (augment standard behavior)

            deathTime = bs.getGameTime()
            
            # record the player's moment of death
            m.spaz.getPlayer().gameData['deathTime'] = deathTime

            # in co-op mode, end the game the instant everyone dies (more accurate looking)
            # in teams/ffa, allow a one-second fudge-factor so we can get more draws
            if isinstance(self.getSession(),bs.CoopSession):
                # teams will still show up if we check now.. check in the next cycle
                bs.pushCall(self._checkEndGame)
                self._lastPlayerDeathTime = deathTime # also record this for a final setting of the clock..
            else:
                bs.gameTimer(1000,self._checkEndGame)

        else:
            # default handler:
            bs.TeamGameActivity.handleMessage(self,m)

    def _checkEndGame(self):
        livingTeamCount = 0
        for team in self.teams:
            for player in team.players:
                if player.isAlive():
                    livingTeamCount += 1
                    break

        # in co-op, we go till everyone is dead.. otherwise we go until one team remains
        if isinstance(self.getSession(),bs.CoopSession):
            if livingTeamCount <= 0: self.endGame()
        else:
            if livingTeamCount <= 1: self.endGame()
        
    def _setMeteorTimer(self):
        bs.gameTimer(int((1.0+0.2*random.random())*self._meteorTime),self._dropBombCluster)
        
    def _dropBombCluster(self):

        # random note: code like this is a handy way to plot out extents and debug things
        if False:
            bs.newNode('locator',attrs={'position':(8,6,-5.5)})
            bs.newNode('locator',attrs={'position':(8,6,-2.3)})
            bs.newNode('locator',attrs={'position':(-7.3,6,-5.5)})
            bs.newNode('locator',attrs={'position':(-7.3,6,-2.3)})

        # drop several bombs in series..
		
        delay = 0
        for i in range(random.randrange(1,3)):
            # drop them somewhere within our bounds with velocity pointing toward the opposite side
            pos = (-7.3+15.3*random.random(),11,-5.5+2.1*random.random())
            vel = ((-5.0+random.random()*30.0) * (-1.0 if pos[0] > 0 else 1.0), -4.0,0)
            bs.gameTimer(delay,bs.Call(self._dropBomb,pos,vel))
            delay += 100
        self._setMeteorTimer()

    def _dropBomb(self,position,velocity):
        b = bs.Bomb(position=position,velocity=velocity,bombType='ice').autoRetain()

    def _decrementMeteorTime(self):
        self._meteorTime = max(10,int(self._meteorTime*0.9))

    def endGame(self):

        curTime = bs.getGameTime()
        
        # mark 'death-time' as now for any still-living players
        # and award players points for how long they lasted.
        # (these per-player scores are only meaningful in team-games)
        for team in self.teams:
            for player in team.players:

                # throw an extra fudge factor +1 in so teams that
                # didn't die come out ahead of teams that did
                if 'deathTime' not in player.gameData: player.gameData['deathTime'] = curTime+1
                    
                # award a per-player score depending on how many seconds they lasted
                # (per-player scores only affect teams mode; everywhere else just looks at the per-team score)
                score = (player.gameData['deathTime']-self._timer.getStartTime())/1000
                if 'deathTime' not in player.gameData: score += 50 # a bit extra for survivors
                self.scoreSet.playerScored(player,score,screenMessage=False)

        # stop updating our time text, and set the final time to match
        # exactly when our last guy died.
        self._timer.stop(endTime=self._lastPlayerDeathTime)
        
        # ok now calc game results: set a score for each team and then tell the game to end
        results = bs.TeamGameResults()

        # remember that 'free-for-all' mode is simply a special form of 'teams' mode
        # where each player gets their own team, so we can just always deal in teams
        # and have all cases covered
        for team in self.teams:

            # set the team score to the max time survived by any player on that team
            longestLife = 0
            for player in team.players:
                longestLife = max(longestLife,(player.gameData['deathTime'] - self._timer.getStartTime()))
            results.setTeamScore(team,longestLife)

        self.end(results=results)
