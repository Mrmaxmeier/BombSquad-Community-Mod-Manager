import bs
import random
import bsUtils
import bsBomb
import bsVector

def bsGetAPIVersion():
    # see bombsquadgame.com/apichanges
    return 4

def bsGetGames():
    return [Infection]

def bsGetLevels():
    return [ bs.Level('Infection', displayName='${GAME}', gameType=Infection,
                      settings={}, previewTexName='footballStadiumPreview') ]

class PlayerSpaz_Infection(bs.PlayerSpaz):
    def handleMessage(self, m):
        if isinstance(m, bs.HitMessage):
            if not self.node.exists():
                return True
            if m.sourcePlayer != self.getPlayer():
                return True
            else:
                super(self.__class__, self).handleMessage(m)
        else:
            super(self.__class__, self).handleMessage(m)
class myMine(bs.Bomb):
    #reason for the mine class is so we can add the death zone
    def __init__(self,pos):
        bs.Bomb.__init__(self,position=pos,bombType='landMine')
        showInSpace = False
        self.died = False
        self.rad = 0.3
        self.zone = bs.newNode('locator',attrs={'shape':'circle','position':self.node.position,'color':(1,0,0),'opacity':0.5,'drawBeauty':showInSpace,'additive':True})
        bs.animateArray(self.zone,'size',1,{0:[0.0],50:[2*self.rad]})
    
    def handleMessage(self,m):
        if isinstance(m,bs.DieMessage):
            if not self.died:
                self.getActivity().mineCount -= 1
                self.died = True
                bs.animateArray(self.zone,'size',1,{0:[2*self.rad],50:[0]})
                self.zone = None
            super(self.__class__, self).handleMessage(m)
        else:
            super(self.__class__, self).handleMessage(m)
                
class Infection(bs.TeamGameActivity):

    @classmethod
    def getName(cls):
        return 'Infection'

    @classmethod
    def getScoreInfo(cls):
        return { 'scoreName':'Survived',
                 'scoreType':'milliseconds',
                 'scoreVersion':'B' }
                
    @classmethod
    def supportsSessionType(cls, sessionType):
        return True if (issubclass(sessionType,bs.TeamsSession)
                        or issubclass(sessionType,bs.FreeForAllSession)
                        or issubclass(sessionType,bs.CoopSession)) else False
    
    @classmethod
    def getDescription(cls,sessionType):
        return "It's spreading!"

    @classmethod
    def getSupportedMaps(cls,sessionType):
        return ['Doom Shroom', 'Rampage', 'Hockey Stadium', 'Crag Castle', 'Big G', 'Football Stadium']

    @classmethod
    def getSettings(cls,sessionType):
        return [("Mines",{'minValue':5,'default':10,'increment':5}),
                ("Enable Bombs",{'default':True}),
                ("Sec/Extra Mine",{'minValue':1,'default':10,'increment':1}),
                ("Max Infected Size",{'minValue':4,'default':6,'increment':1}),
                ("Max Size Increases Every",{'choices':[('10s',10),('20s',20),
                                              ('30s',30),('Minute',60)],'default':20}),
                ("Infection Spread Rate",{'choices':[('Slowest',0.01),('Slow',0.02),('Normal',0.03),('Fast',0.04),('Faster',0.05),('Insane',0.08)],'default':0.03}),
                ]

    def __init__(self,settings):
        bs.TeamGameActivity.__init__(self, settings)
        
        # print messages when players die (since its meaningful in this game)
        self.announcePlayerDeaths = True

        self._lastPlayerDeathTime = None    

        self.mines = []
        self.maxMines = settings['Mines']
        self.updateRate = 100 #update the mine radii etc every this many milliseconds
        self.growthRate = self.settings['Infection Spread Rate'] #grow the radius of each death zone by this much every update
        self.maxSize = self.settings['Max Infected Size'] #We'll set a timer later to increase this

    def getInstanceDescription(self):
        return ('Avoid the spread!')

    def getInstanceScoreBoardDescription(self):
        return ('Avoid the spread!')

    def onTransitionIn(self):
        bs.TeamGameActivity.onTransitionIn(self, music='Survival')
        self._startGameTime = bs.getGameTime()
        
    def onBegin(self):
        bs.TeamGameActivity.onBegin(self)

        self.mineCount = 0
        bs.gameTimer(self.updateRate, bs.WeakCall(self.mineUpdate), repeat=True)
        bs.gameTimer(self.settings['Max Size Increases Every']*1000, bs.WeakCall(self.maxSizeUpdate), repeat=True)
        bs.gameTimer(self.settings['Sec/Extra Mine']*1000, bs.WeakCall(self.maxMineUpdate), repeat=True)
        self._timer = bs.OnScreenTimer()
        self._timer.start()
        # check for immediate end (if we've only got 1 player, etc)
        bs.gameTimer(5000, self._checkEndGame)
        
        
    def onPlayerJoin(self, player):
        # don't allow joining after we start
        # (would enable leave/rejoin tomfoolery)
        if self.hasBegun():
            bs.screenMessage(bs.Lstr(resource='playerDelayedJoinText',subs=[('${PLAYER}',player.getName(full=True))]),color=(0,1,0))
            # for score purposes, mark them as having died right as the game started
            player.gameData['deathTime'] = self._timer.getStartTime()
            return
        self.spawnPlayer(player)
        
    def onPlayerLeave(self, player):
         # augment default behavior...
        bs.TeamGameActivity.onPlayerLeave(self, player)
        # a departing player may trigger game-over
        self._checkEndGame()

    def maxMineUpdate(self):
        self.maxMines += 1
    
    def maxSizeUpdate(self):
        self.maxSize += 1
        
    def mineUpdate(self):
        #print self.mineCount
        #purge dead mines, update their animantion, check if players died
        for m in self.mines:
            if not m.exists():
                self.mines.remove(m)
            else:
                #First, check if any player is within the current death zone
                for player in self.players:
                    if not player.actor is None:
                        if player.actor.isAlive():
                            p1 = player.actor.node.position
                            p2 = m.node.position
                            diff = (bs.Vector(p1[0]-p2[0],0.0,p1[2]-p2[2]))
                            dist = (diff.length())
                            if dist < m.rad:
                                player.actor.handleMessage(bs.DieMessage())
                #Now tell the circle to grow to the new size
                if m.rad < self.maxSize:
                    bs.animateArray(m.zone,'size',1,{0:[m.rad*2],self.updateRate:[(m.rad+self.growthRate)*2]})
                    #Tell the circle to be the new size. This will be the new check radius next time.
                    m.rad +=self.growthRate
        #make a new mine if needed.
        if self.mineCount < self.maxMines:
            pos = self.getRandomPowerupPoint()
            self.mineCount += 1
            self._flashMine(pos)
            bs.gameTimer(950,bs.Call(self._makeMine,pos))
    
    def _makeMine(self,posn):
        m = myMine(pos=posn)
        m.arm()
        self.mines.append(m)
        

    def _flashMine(self,pos):
        light = bs.newNode("light",
                           attrs={'position':pos,
                                  'color':(1,0.2,0.2),
                                  'radius':0.1,
                                  'heightAttenuated':False})
        bs.animate(light,"intensity",{0:0,100:1.0,200:0},loop=True)
        bs.gameTimer(1000,light.delete)
        

    def endGame(self):
        results = bs.TeamGameResults()
        for t in self.teams: results.setTeamScore(t,t.gameData['survivalSeconds'])
        self.end(results=results,announceDelay=800)
        
    def _flashPlayer(self,player,scale):
        pos = player.actor.node.position
        light = bs.newNode('light',
                           attrs={'position':pos,
                                  'color':(1,1,0),
                                  'heightAttenuated':False,
                                  'radius':0.4})
        bs.gameTimer(500,light.delete)
        bs.animate(light,'intensity',{0:0,100:1.0*scale,500:0})


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
                bs.gameTimer(1000, self._checkEndGame)

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

    def spawnPlayer(self, player):

        spaz = self.spawnPlayerSpaz(player)

        # lets reconnect this player's controls to this
        # spaz but *without* the ability to attack or pick stuff up
        spaz.connectControlsToPlayer(enablePunch=False,
                                     enableBomb=self.settings['Enable Bombs'],
                                     enablePickUp=False)

        # also lets have them make some noise when they die..
        spaz.playBigDeathSound = True
        
    def spawnPlayerSpaz(self,player,position=(0,0,0),angle=None):
        """
        Create and wire up a bs.PlayerSpaz for the provide bs.Player.
        """
        position = self.getMap().getFFAStartPosition(self.players)
        name = player.getName()
        color = player.color
        highlight = player.highlight

        lightColor = bsUtils.getNormalizedColor(color)
        displayColor = bs.getSafeColor(color,targetIntensity=0.75)
        spaz = PlayerSpaz_Infection(color=color,
                             highlight=highlight,
                             character=player.character,
                             player=player)
        player.setActor(spaz)

        # we want a bigger area-of-interest in co-op mode
        # if isinstance(self.getSession(),bs.CoopSession): spaz.node.areaOfInterestRadius = 5.0
        # else: spaz.node.areaOfInterestRadius = 5.0

        # if this is co-op and we're on Courtyard or Runaround, add the material that allows us to
        # collide with the player-walls
        # FIXME; need to generalize this
        if isinstance(self.getSession(),bs.CoopSession) and self.getMap().getName() in ['Courtyard','Tower D']:
            mat = self.getMap().preloadData['collideWithWallMaterial']
            spaz.node.materials += (mat,)
            spaz.node.rollerMaterials += (mat,)
        
        spaz.node.name = name
        spaz.node.nameColor = displayColor
        spaz.connectControlsToPlayer()
        self.scoreSet.playerGotNewSpaz(player,spaz)

        # move to the stand position and add a flash of light
        spaz.handleMessage(bs.StandMessage(position,angle if angle is not None else random.uniform(0,360)))
        t = bs.getGameTime()
        bs.playSound(self._spawnSound,1,position=spaz.node.position)
        light = bs.newNode('light',attrs={'color':lightColor})
        spaz.node.connectAttr('position',light,'position')
        bsUtils.animate(light,'intensity',{0:0,250:1,500:0})
        bs.gameTimer(500,light.delete)
        return spaz
    def getRandomPowerupPoint(self):
        #So far, randomized points only figured out for mostly rectangular maps.
        #Boxes will still fall through holes, but shouldn't be terrible problem (hopefully)
        #If you add stuff here, need to add to "supported maps" above.
        #['Doom Shroom', 'Rampage', 'Hockey Stadium', 'Courtyard', 'Crag Castle', 'Big G', 'Football Stadium']
        myMap = self.getMap().getName()
        #print(myMap)
        if myMap == 'Doom Shroom':
            while True:
                x = random.uniform(-1.0,1.0)
                y = random.uniform(-1.0,1.0)
                if x*x+y*y < 1.0: break
            return ((8.0*x,2.5,-3.5+5.0*y))
        elif myMap == 'Rampage':
            x = random.uniform(-6.0,7.0)
            y = random.uniform(-6.0,-2.5)
            return ((x, 5.2, y))
        elif myMap == 'Hockey Stadium':
            x = random.uniform(-11.5,11.5)
            y = random.uniform(-4.5,4.5)
            return ((x, 0.2, y))
        elif myMap == 'Courtyard':
            x = random.uniform(-4.3,4.3)
            y = random.uniform(-4.4,0.3)
            return ((x, 3.0, y))
        elif myMap == 'Crag Castle':
            x = random.uniform(-6.7,8.0)
            y = random.uniform(-6.0,0.0)
            return ((x, 10.0, y))
        elif myMap == 'Big G':
            x = random.uniform(-8.7,8.0)
            y = random.uniform(-7.5,6.5)
            return ((x, 3.5, y))
        elif myMap == 'Football Stadium':
            x = random.uniform(-12.5,12.5)
            y = random.uniform(-5.0,5.5)
            return ((x, 0.32, y))
        else:
            x = random.uniform(-5.0,5.0)
            y = random.uniform(-6.0,0.0)
            return ((x, 8.0, y))
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




