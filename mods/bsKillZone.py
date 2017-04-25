import bs
import random
import math

def bsGetAPIVersion():
    return 4

def bsGetGames():
    return [KillZoneGame]

def bsGetLevels():
    return [bs.Level('Kill Zone',displayName='${GAME}',gameType=KillZoneGame,settings={},previewTexName='doomShroomPreview')]


class KillZoneGame(bs.TeamGameActivity):

    @classmethod
    def getName(cls):
        return 'Kill Zone - Kill no-shirts on targets'

    @classmethod
    def getDescription(cls,sessionType):
        return 'Get points for killing enemies within the targets.'

    @classmethod
    def getSupportedMaps(cls,sessionType):
        return ['Doom Shroom']

    @classmethod
    def supportsSessionType(cls,sessionType):
        # we support teams, co-op, and free-for-all
        return True if (issubclass(sessionType,bs.CoopSession)
                        or issubclass(sessionType,bs.TeamsSession)
                        or issubclass(sessionType,bs.FreeForAllSession)) else False
    
    def __init__(self,settings):
        bs.TeamGameActivity.__init__(self,settings)

        self._scoreBoard = bs.ScoreBoard()
        
    def onTransitionIn(self):
        bs.TeamGameActivity.onTransitionIn(self, music='ForwardMarch')

    def onTeamJoin(self,team):
        team.gameData['score'] = 0
        if self.hasBegun(): self._updateScoreBoard()
        
    def onBegin(self):
        bs.TeamGameActivity.onBegin(self)
        self._updateScoreBoard()

        self._targets = []

        # number of targets is based on player count
        numTargets = min(5,len(self.initialPlayerInfo)+2)
        for i in range(numTargets):
            bs.gameTimer(5000+i*1000,self._spawnTarget)
        
        
        # this wrangles our bots
        self._bots = bs.BotSet()

        # start some timers to spawn bots
        bs.gameTimer(1000,bs.Call(self._bots.spawnBot,bs.ToughGuyBot,pos=(3,3,-2),spawnTime=3000))
        #bs.gameTimer(2000,bs.Call(self._bots.spawnBot,bs.ToughGuyBot,pos=(-3,3,-2),spawnTime=3000))
        #bs.gameTimer(3000,bs.Call(self._bots.spawnBot,bs.NinjaBot,pos=(5,3,-2),spawnTime=3000))
        #bs.gameTimer(4000,bs.Call(self._bots.spawnBot,bs.NinjaBot,pos=(-5,3,-2),spawnTime=3000))

        # add a few extras for multiplayer
        if len(self.initialPlayerInfo) > 2:
            bs.gameTimer(5000,bs.Call(self._bots.spawnBot,bs.ToughGuyBot,pos=(0,3,-5),spawnTime=3000))
        if len(self.initialPlayerInfo) > 3:
            bs.gameTimer(6000,bs.Call(self._bots.spawnBot,bs.ToughGuyBot,pos=(0,3,1),spawnTime=3000))

        # note: if spawns were spread out more we'd probably want to set some sort of flag on the
        # last spawn to ensure we don't inadvertantly allow a 'win' before every bot is spawned.
        # (ie: if bot 1, 2, and 3 got killed but 4 hadn't spawned yet, the game might end because
        # it sees no remaining bots.
        self._updateTimer = bs.Timer(1000,self._update,repeat=True)

        self._countdown = bs.OnScreenCountdown(150,endCall=self.endGame)
        bs.gameTimer(4000,self._countdown.start)
        
    def spawnPlayer(self,player):
        spawnCenter = (0,3,-5)
        pos = (spawnCenter[0]+random.uniform(-1.5,1.5),spawnCenter[1],spawnCenter[2]+random.uniform(-1.5,1.5))

        # reset their streak
        player.gameData['streak'] = 0
        
        spaz = self.spawnPlayerSpaz(player,position=pos)
        spaz.equipBoxingGloves()
        spaz.connectControlsToPlayer(enablePunch=True,
                                     enableBomb=False,
                                     enablePickUp=True)
        
        # give players permanent triple impact bombs and wire them up
        # to tell us when they drop a bomb
        spaz.bombType = 'impact'
        spaz.setBombCount(3)
        spaz.addDroppedBombCallback(self._onSpazDroppedBomb)

    def _spawnTarget(self):

        # gen a few random points; we'll use whichever one is farthest from
        # our existing targets. (dont want overlapping targets)
        points = []
        
        for i in range(4):
            # calc a random point within a circle
            while True:
                x = random.uniform(-1.0,1.0)
                y = random.uniform(-1.0,1.0)
                if x*x+y*y < 1.0: break
            points.append((8.0*x,2.2,-3.5+5.0*y))
            
        def getMinDistFromTarget(point):
            return min((t.getDistFromPoint(point) for t in self._targets))

        # if we have existing targets, use the point with the highest min-distance-from-targets
        if self._targets: point = max(points,key=getMinDistFromTarget)
        else: point = points[0]
        
        self._targets.append(Target(position=point))
        
    def _onSpazDroppedBomb(self,spaz,bomb):
        # wire up this bomb to inform us when it blows up
        pass
        #bomb.addExplodeCallback(self._onBombExploded)#Commented out to prevent bomb wiring. Get info from spazbot death message instead
        
    def _onSpazBotDied(self,DeathMsg):
        x = random.uniform(-1.0,1.0)
        y = random.uniform(-1.0,1.0)
        self._bots.spawnBot(bs.ToughGuyBot,pos=(8.0*x,3,5.0*y),spawnTime=1000)
        pos = DeathMsg.badGuy.node.position

        # debugging: throw a locator down where we landed..
        #bs.newNode('locator',attrs={'position':blast.node.position})

        # feed the explosion point to all our targets and get points in return..
        # note: we operate on a copy of self._targets since the list may change
        # under us if we hit stuff (dont wanna get points for new targets)
        print(DeathMsg.how)
        if DeathMsg.killerPlayer is None:
            #print("No killer")
            pass
        else:
            player = DeathMsg.killerPlayer
            #print(player)
            if not player.exists(): return # could happen if they leave after throwing a bomb..
            #print("got here")
            bullsEye = any(target.doHitAtPosition(pos,player) for target in list(self._targets))

            if bullsEye: player.gameData['streak'] += 1
            else: player.gameData['streak'] = 0
        
    def _update(self):

        # misc. periodic updating..
        
        # clear out targets that have died
        self._targets = [t for t in self._targets if t.exists()]
        
    def handleMessage(self,m):
        
        # when players die, respawn them
        if isinstance(m,bs.PlayerSpazDeathMessage):
            bs.TeamGameActivity.handleMessage(self,m) # do standard stuff
            self.respawnPlayer(m.spaz.getPlayer()) # kick off a respawn
        elif isinstance(m,Target.TargetHitMessage):
            # a target is telling us it was hit and will die soon..
            # ..so make another one.
            self._spawnTarget()
        elif isinstance(m,bs.SpazBotDeathMessage):
            self._onSpazBotDied(m)
            bs.TeamGameActivity.handleMessage(self,m)
            #bs.PopupText("died",position=self._position,color=popupColor,scale=popupScale).autoRetain()
        else:
            bs.TeamGameActivity.handleMessage(self,m)
            
    def _updateScoreBoard(self):
        for team in self.teams:
            self._scoreBoard.setTeamValue(team,team.gameData['score'])

    def endGame(self):
        results = bs.TeamGameResults()
        for team in self.teams:
            results.setTeamScore(team,team.gameData['score'])
        self.end(results)
        
class Target (bs.Actor):

    class TargetHitMessage(object):
        pass
    
    def __init__(self,position):
        self._r1 = 0.45
        self._r2 = 1.1
        self._r3 = 2.0
        self._rFudge = 0.15
        bs.Actor.__init__(self)
        self._position = bs.Vector(*position)
        self._hit = False
        showInSpace = False # it can be handy to test with this on to make sure the projection isn't too far off from the actual object..
        n1 = bs.newNode('locator',attrs={'shape':'circle','position':position,'color':(0,1,0),'opacity':0.5,'drawBeauty':showInSpace,'additive':True})
        n2 = bs.newNode('locator',attrs={'shape':'circleOutline','position':position,'color':(0,1,0),'opacity':0.3,'drawBeauty':False,'additive':True})
        n3 = bs.newNode('locator',attrs={'shape':'circleOutline','position':position,'color':(0,1,0),'opacity':0.1,'drawBeauty':False,'additive':True})
        self._nodes = [n1,n2,n3]
        bs.animateArray(n1,'size',1,{0:[0.0],200:[self._r1*2.0]})
        bs.animateArray(n2,'size',1,{50:[0.0],250:[self._r2*2.0]})
        bs.animateArray(n3,'size',1,{100:[0.0],300:[self._r3*2.0]})
        bs.playSound(bs.getSound('laserReverse'))

    def exists(self):
        return True if self._nodes else False
    
    def handleMessage(self,m):
        if isinstance(m,bs.DieMessage):
            for node in self._nodes: node.delete()
            self._nodes = []
        else:
            bs.Actor.handleMessage(self,m)

    def getDistFromPoint(self,pos):
        'Given a point, returns distance squared from it'
        return (bs.Vector(*pos)-self._position).length()
        
    def doHitAtPosition(self,pos,player):
        activity = self.getActivity()
        #print("Hit target?")

        # ignore hits if the game is over or if we've already been hit
        if activity.hasEnded() or self._hit or not self._nodes: return 0

        diff = (bs.Vector(*pos)-self._position)
        diff[1] = 0.0 # disregard y difference (our target point probably isnt exactly on the ground anyway)
        dist = diff.length()

        bullsEye = False
        points = 0
        if dist <= self._r3+self._rFudge:
            # inform our activity that we were hit
            self._hit = True
            self.getActivity().handleMessage(self.TargetHitMessage())
            keys = {0:(1,0,0),49:(1,0,0),50:(1,1,1),100:(0,1,0)}
            cDull = (0.3,0.3,0.3)
            if dist <= self._r1+self._rFudge:
                bullsEye = True
                self._nodes[1].color = cDull
                self._nodes[2].color = cDull
                bs.animateArray(self._nodes[0],'color',3,keys,loop=True)
                popupScale = 1.8
                popupColor = (1,1,0,1)
                streak = player.gameData['streak']
                points = 10 + min(20,streak * 2)
                bs.playSound(bs.getSound('bellHigh'))
                if streak > 0:
                    bs.playSound(bs.getSound('orchestraHit4' if streak > 3
                                             else 'orchestraHit3' if streak > 2
                                             else 'orchestraHit2' if streak > 1
                                             else 'orchestraHit'))
            elif dist <= self._r2+self._rFudge:
                self._nodes[0].color = cDull
                self._nodes[2].color = cDull
                bs.animateArray(self._nodes[1],'color',3,keys,loop=True)
                popupScale = 1.25
                popupColor = (1,0.5,0.2,1)
                points = 4
                bs.playSound(bs.getSound('bellMed'))
            else:
                self._nodes[0].color = cDull
                self._nodes[1].color = cDull
                bs.animateArray(self._nodes[2],'color',3,keys,loop=True)
                popupScale= 1.0
                popupColor = (0.8,0.3,0.3,1)
                points = 2
                bs.playSound(bs.getSound('bellLow'))

            # award points/etc.. (technically should probably leave this up to the activity)
            popupStr = "+"+str(points)
            
            # if there's more than 1 player in the game, include their names and colors
            # so they know who got the hit
            if len(activity.players) > 1:
                popupColor = bs.getSafeColor(player.color,targetIntensity=0.75)
                popupStr += ' '+player.getName()
            bs.PopupText(popupStr,position=self._position,color=popupColor,scale=popupScale).autoRetain()

            # give this player's team points and update the score-board
            player.getTeam().gameData['score'] += points
            activity._updateScoreBoard()

            # also give this individual player points (only applies in teams mode)
            activity.scoreSet.playerScored(player,points,showPoints=False,screenMessage=False)
                
            bs.animateArray(self._nodes[0],'size',1,{800:self._nodes[0].size,1000:[0.0]})
            bs.animateArray(self._nodes[1],'size',1,{850:self._nodes[1].size,1050:[0.0]})
            bs.animateArray(self._nodes[2],'size',1,{900:self._nodes[2].size,1100:[0.0]})
            bs.gameTimer(1100,bs.Call(self.handleMessage,bs.DieMessage()))
            
        return bullsEye
