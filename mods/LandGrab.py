import bs
import random
import math
import bsUtils
import bsBomb
import bsVector
import bsSpaz

def bsGetAPIVersion():
    # see bombsquadgame.com/apichanges
    return 4

def bsGetGames():
    return [LandGrab]

class PlayerSpaz_Grab(bs.PlayerSpaz):

    def dropBomb(self):
        """
        Tell the spaz to drop one of his bombs, and returns
        the resulting bomb object.
        If the spaz has no bombs or is otherwise unable to
        drop a bomb, returns None.
        
        Overridden for Land Grab: 
        -Add condition for mineTimeout,
        -make it create myMine instead of regular mine
        -set this spaz's last mine time to current time
        -Don't decrement LandMineCount.  We'll set to 0 when spaz double-punches.
        """
        t = bs.getGameTime()
        if ((self.landMineCount <= 0 or t-self.lastMine < self.mineTimeout) and self.bombCount <= 0) or self.frozen: return
        p = self.node.positionForward
        v = self.node.velocity

        if self.landMineCount > 0:
            droppingBomb = False
            #self.setLandMineCount(self.landMineCount-1) #Don't decrement mine count. Unlimited mines.
            if t - self.lastMine < self.mineTimeout:
                return #Last time we dropped  mine was too short ago. Don't drop another one.
            else:
                self.lastMine = t
                self.node.billboardCrossOut = True
                bs.gameTimer(self.mineTimeout,bs.WeakCall(self.unCrossBillboard))
                bomb = myMine(pos=(p[0],p[1] - 0.0,p[2]),
                           vel=(v[0],v[1],v[2]),
                           bRad=self.blastRadius,
                           sPlay=self.sourcePlayer,
                           own=self.node).autoRetain()
                self.getPlayer().gameData['mines'].append(bomb)
        elif self.dropEggs:
            if len(self.getPlayer().gameData['bots']) > 0 : return #Only allow one snowman at a time.
            droppingBomb = True
            bomb = Egg(position=(p[0],p[1] - 0.0,p[2]), sourcePlayer=self.sourcePlayer,owner=self.node).autoRetain()
            
        else:
            droppingBomb = True
            bombType = self.bombType

            bomb = bs.Bomb(position=(p[0],p[1] - 0.0,p[2]),
                       velocity=(v[0],v[1],v[2]),
                       bombType=bombType,
                       blastRadius=self.blastRadius,
                       sourcePlayer=self.sourcePlayer,
                       owner=self.node).autoRetain()

        if droppingBomb:
            self.bombCount -= 1
            bomb.node.addDeathAction(bs.WeakCall(self.handleMessage,bsSpaz._BombDiedMessage()))
            if not self.eggsHatch:
                bomb.hatch = False
            else:
                bomb.hatch = True
        self._pickUp(bomb.node)

        for c in self._droppedBombCallbacks: c(self,bomb)
        
        return bomb
    def unCrossBillboard(self):
        if self.node.exists():
            self.node.billboardCrossOut = False
    def onPunchPress(self):
        """
        Called to 'press punch' on this spaz;
        used for player or AI connections.
        Override for land grab: catch double-punch to switch bombs!
        """
        if not self.node.exists() or self.frozen or self.node.knockout > 0.0: return
        
        if self.punchCallback is not None:
            self.punchCallback(self)
        t = bs.getGameTime()
        self._punchedNodes = set() # reset this..
        ########This catches punches and switches between bombs and mines
        #if t - self.lastPunchTime < 500:
        if self.landMineCount < 1:
            self.landMineCount = 1
            bs.animate(self.node,"billboardOpacity",{0:0.0,100:1.0,400:1.0})
        else:
            self.landMineCount = 0
            bs.animate(self.node,"billboardOpacity",{0:1.0,400:0.0})
        if t - self.lastPunchTime > self._punchCooldown:
            self.lastPunchTime = t
            self.node.punchPressed = True
            if not self.node.holdNode.exists():
                bs.gameTimer(100,bs.WeakCall(self._safePlaySound,self.getFactory().swishSound,0.8))
    def handleMessage(self, m):
        #print m.sourcePlayer
        if isinstance(m, bs.HitMessage):
            #print m.sourcePlayer.getName()
            if not self.node.exists():
                return True
            if m.sourcePlayer != self.getPlayer():
                return True
            else:
                super(self.__class__, self).handleMessage(m)
        else:
            super(self.__class__, self).handleMessage(m)
class myMine(bs.Bomb):
    #reason for the mine class is so we can intercept messages.
    def __init__(self,pos,vel,bRad,sPlay,own):
        bs.Bomb.__init__(self,position=pos,velocity=vel,bombType='landMine',blastRadius=bRad,sourcePlayer=sPlay,owner=own)
        self.isHome = False
        self.died = False
        self.activated = False
        self.defRad = self.getActivity().claimRad
        self.rad = 0.0# Will set to self.getActivity().settings['Claim Size'] when arming
        #Don't do this until mine arms
        self.zone = None 
        fm = bs.getSharedObject('footingMaterial')
        materials = getattr(self.node,'materials')
        if not fm in materials:
            setattr(self.node,'materials',materials + (fm,))
    
    def handleMessage(self,m):
        if isinstance(m,bsBomb.ArmMessage): 
            self.arm()#This is all the  main bs.Bomb does.  All below is extra
            self.activateArea()
        elif isinstance(m, bs.HitMessage):
            #print m.hitType, m.hitSubType
            if self.isHome: return True
            if m.sourcePlayer == self.sourcePlayer:
                return True #I think this should stop mines from exploding due to self activity or chain reactions?.
            if not self.activated: return True
            else:
                super(self.__class__, self).handleMessage(m)
        elif isinstance(m,bsBomb.ImpactMessage):
            if self.isHome: return True #Never explode the home bomb.
            super(self.__class__, self).handleMessage(m)
        elif isinstance(m,bs.DieMessage):
            if self.isHome: return True #Home never dies (even if player leaves, I guess...)
            if self.exists() and not self.died:
                self.died = True
                self.rad = 0.0
                if self.zone.exists():
                    bs.animateArray(self.zone,'size',1,{0:[2*self.rad],1:[0]})
                self.zone = None
            super(self.__class__, self).handleMessage(m)
        else:
            super(self.__class__, self).handleMessage(m)
    
    def activateArea(self):
        mineOK = False
        if self.exists():
            r = self.defRad
            fudge = self.getActivity().minOverlap #This is the minimum overlap to join owner's territory (not used to check enemy overlap)
            p1 = self.node.position
            self.node.maxSpeed = 0.0 #We don't want mines moving around. They could leave their zone.
            self.damping = 100
        #First, confirm that this mine "touches" owner's mines
        if self.sourcePlayer.exists():
            for m in self.sourcePlayer.gameData['mines']:
                if m.exists() and not m.died:
                    if m.rad != 0: #Don't check un-activated mines
                        p2 = m.node.position
                        diff = (bs.Vector(p1[0]-p2[0],0.0,p1[2]-p2[2]))
                        dist = (diff.length())
                        if dist < (m.rad + r)-fudge: #We check m.rad just in case it's somehow different. However, this probably shouldn't happen. Unless I change gameplay later.
                            mineOK = True #mine adjoins owner's territory. Will set to false if it also adjoin's enemy though.
                            break #Get out of the loop
        takeovers = []
        if mineOK:
            for p in self.getActivity().players:
                if not p is self.sourcePlayer:
                    if p.exists():
                        for m in p.gameData['mines']:
                            if m.rad != 0.0: #Don't check un-activated mines
                                p2 = m.node.position
                                diff = (bs.Vector(p1[0]-p2[0],0.0,p1[2]-p2[2]))
                                dist = (diff.length())
                                if dist < m.rad + r: #We check m.rad just in case it's somehowdifferent. However, this probably shouldn't happen. Unless I change gameplay later.
                                    mineOK = False
                                    takeovers = []
                                    break

        #If we made it to here and mineOK is true, we can activate.  Otherwise, we'll flash red and die.
        self.zone = bs.newNode('locator',attrs={'shape':'circle','position':self.node.position,'color':self.sourcePlayer.color,'opacity':0.5,'drawBeauty':False,'additive':True})
        bs.animateArray(self.zone,'size',1,{0:[0.0],150:[2*r]}) #Make circle at the default radius to show players where it would go if OK
        if mineOK or self.isHome:
            self.activated = True
            self.rad = r #Immediately set this mine's radius
        else: #mine was not OK
            keys = {0:(1,0,0),49:(1,0,0),50:(1,1,1),100:(0,1,0)}
            bs.animateArray(self.zone,'color',3,keys,loop=True)
            bs.gameTimer(800, bs.WeakCall(self.handleMessage, bs.DieMessage()), repeat=False)
        #Takeovers didn't work so well.  Very confusing.
        #if len(takeovers) > 0:
        #    #Flash it red and kill it
        #    for m in takeovers:
        #        if m.exists():
        #            if not m._exploded:
        #                if not m.died:
        #                    keys = {0:(1,0,0),49:(1,0,0),50:(1,1,1),100:(0,1,0)}
        #                    if m.zone.exists():
        #                        bs.animateArray(m.zone,'color',3,keys,loop=True)
        #                    bs.gameTimer(800, bs.WeakCall(m.handleMessage, bs.DieMessage()), repeat=False)
    def _handleHit(self,m):
        #This one is overloaded to prevent chaining of explosions
        isPunch = (m.srcNode.exists() and m.srcNode.getNodeType() == 'spaz')

        # normal bombs are triggered by non-punch impacts..  impact-bombs by all impacts
        if not self._exploded and not isPunch or self.bombType in ['impact','landMine']:
            # also lets change the owner of the bomb to whoever is setting us off..
            # (this way points for big chain reactions go to the person causing them)
            if m.sourcePlayer not in [None]:
                #self.sourcePlayer = m.sourcePlayer

                # also inherit the hit type (if a landmine sets off by a bomb, the credit should go to the mine)
                # the exception is TNT.  TNT always gets credit.
                #if self.bombType != 'tnt':
                #    self.hitType = m.hitType
                #    self.hitSubType = m.hitSubType
                pass
            bs.gameTimer(100+int(random.random()*100),bs.WeakCall(self.handleMessage,bsBomb.ExplodeMessage()))
        self.node.handleMessage("impulse",m.pos[0],m.pos[1],m.pos[2],
                                m.velocity[0],m.velocity[1],m.velocity[2],
                                m.magnitude,m.velocityMagnitude,m.radius,0,m.velocity[0],m.velocity[1],m.velocity[2])

        if m.srcNode.exists():
            pass
            #print 'FIXME HANDLE KICKBACK ON BOMB IMPACT'
            # bs.nodeMessage(m.srcNode,"impulse",m.srcBody,m.pos[0],m.pos[1],m.pos[2],
            #                     -0.5*m.force[0],-0.75*m.force[1],-0.5*m.force[2])
    def _handleImpact(self,m):
        #This is overridden so that we can keep from exploding due to own player's activity.
        node,body = bs.getCollisionInfo("opposingNode","opposingBody")
        # if we're an impact bomb and we came from this node, don't explode...
        # alternately if we're hitting another impact-bomb from the same source, don't explode...
        
        try: nodeDelegate = node.getDelegate() #This could be a bomb or a spaz (or none)
        except Exception: nodeDelegate = None
        if node is not None and node.exists():
            if isinstance(nodeDelegate, PlayerSpaz_Grab):
                if nodeDelegate.getPlayer() is self.sourcePlayer:
                    #print("Hit by own self, don't blow")
                    return True
            if (node is self.owner) or ((isinstance(nodeDelegate,bs.Bomb) or isinstance(nodeDelegate, Egg) or isinstance(nodeDelegate,bs.SpazBot)) and nodeDelegate.sourcePlayer is self.sourcePlayer): 
                #print("Hit by owr own bomb")
                return
            else: 
                #print 'exploded handling impact'
                self.handleMessage(bsBomb.ExplodeMessage())            

class Egg(bs.Actor):

    def __init__(self, position=(0,1,0), sourcePlayer=None, owner=None):
        bs.Actor.__init__(self)

        activity = self.getActivity()
        
        # spawn just above the provided point
        self._spawnPos = (position[0], position[1]+1.0, position[2])
        #This line was replaced by 'color' belwo: 'colorTexture': bsBomb.BombFactory().impactTex,
        self.node = bs.newNode("prop",
                               attrs={'model': activity._ballModel,
                                      'body':'sphere',
                                      'colorTexture': bs.getTexture("frostyColor"),
                                      'reflection':'soft',
                                      'modelScale':2.0,
                                      'bodyScale':2.0,
                                      'density':0.08,
                                      'reflectionScale':[0.15],
                                      'shadowSize': 0.6,
                                      'position':self._spawnPos,
                                      'materials': [bs.getSharedObject('objectMaterial'),activity._bombMat]
                                      },
                               delegate=self)
        self.sourcePlayer = sourcePlayer
        self.owner = owner
    def handleMessage(self,m):
        if isinstance(m,bs.DieMessage):
            self.node.delete()
        elif isinstance(m,bs.DroppedMessage): self._handleDropped(m)
        elif isinstance(m,bs.OutOfBoundsMessage):
            self.handleMessage(bs.DieMessage())
        elif isinstance(m,bs.HitMessage):
            self.node.handleMessage("impulse",m.pos[0],m.pos[1],m.pos[2],
                                    m.velocity[0],m.velocity[1],m.velocity[2],
                                    1.0*m.magnitude,1.0*m.velocityMagnitude,m.radius,0,
                                    m.forceDirection[0],m.forceDirection[1],m.forceDirection[2])
        else:
            bs.Actor.handleMessage(self,m)
    def _handleDropped(self,m):
        if self.exists():
            bs.gameTimer(int(self.getActivity().settings['Egg Lifetime']*1000),self._disappear)
    def _disappear(self):
        if self.node.exists():
            scl = self.node.modelScale
            bsUtils.animate(self.node,"modelScale",{0:scl*1.0, 300:scl*0.5, 500:0.0})
            self.maxSpeed = 0
            if self.hatch and self.sourcePlayer.exists():
                if len(self.sourcePlayer.gameData['bots']) < 3:
                    self.materials = []
                    p = self.node.position
                    #self.getActivity()._bots.spawnBot(ToughGuyFrostBot,pos=(p[0],p[1]-0.8,p[2]),spawnTime=0, onSpawnCall=self.setupFrosty)
                    self.sourcePlayer.gameData['bset'].spawnBot(ToughGuyFrostBot,pos=(p[0],p[1]-0.8,p[2]),spawnTime=0, onSpawnCall=self.setupFrosty)
            bs.gameTimer(550,bs.WeakCall(self.handleMessage,bs.DieMessage()))
    def setupFrosty(self,spaz):
        spaz.sourcePlayer = self.sourcePlayer
        spaz.sourcePlayer.gameData['bots'].append(spaz)
        bs.gameTimer(5000,bs.WeakCall(spaz.handleMessage,bs.DieMessage())) #Kill spaz after 5 seconds
        #bsUtils.animate(spaz.node, "modelScale",{0:0.1, 500:0.3, 800:1.2, 1000:1.0})

class zBotSet(bs.BotSet):   #the botset is overloaded to prevent adding players to the bots' targets if they are zombies too.         
    def startMoving(self): #here we overload the default startMoving, which normally calls _update.
        #self._botUpdateTimer = bs.Timer(50,bs.WeakCall(self._update),repeat=True)
        self._botUpdateTimer = bs.Timer(50,bs.WeakCall(self.zUpdate),repeat=True)
        
    def zUpdate(self):

        # update one of our bot lists each time through..
        # first off, remove dead bots from the list
        # (we check exists() here instead of dead.. we want to keep them around even if they're just a corpse)
        #####This is overloaded from bsSpaz to walk over other players' mines, but not source player.
        try:
            botList = self._botLists[self._botUpdateList] = [b for b in self._botLists[self._botUpdateList] if b.exists()]
        except Exception:
            bs.printException("error updating bot list: "+str(self._botLists[self._botUpdateList]))
        self._botUpdateList = (self._botUpdateList+1)%self._botListCount

        # update our list of player points for the bots to use
        playerPts = []
        for player in bs.getActivity().players:
            try:
                if player.exists():
                    if not player is self.sourcePlayer:  #If the player has lives, add to attack points
                        for m in player.gameData['mines']:
                            if not m.isHome and m.exists():
                                playerPts.append((bs.Vector(*m.node.position),
                                        bs.Vector(0,0,0)))
            except Exception:
                bs.printException('error on bot-set _update')

        for b in botList:
            b._setPlayerPts(playerPts)
            b._updateAI()
        
class ToughGuyFrostBot(bsSpaz.SpazBot):
    """
    category: Bot Classes
    
    A manly bot who walks and punches things.
    """
    character = 'Frosty'
    color = (1,1,1)
    highlight = (1,1,1)
    punchiness = 0.0
    chargeDistMax = 9999.0
    chargeSpeedMin = 1.0
    chargeSpeedMax = 1.0
    throwDistMin = 9999
    throwDistMax = 9999
    
    def handleMessage(self,m):
        if isinstance(m, bs.PickedUpMessage):
            self.handleMessage(bs.DieMessage())
        super(self.__class__, self).handleMessage(m)

    
class LandGrab(bs.TeamGameActivity):

    @classmethod
    def getName(cls):
        return 'Land Grab'

    @classmethod
    def getScoreInfo(cls):
        return {'scoreName':'score',
                'scoreType':'points',
                'noneIsWinner':False,
                'lowerIsBetter':False}
                
    @classmethod
    def supportsSessionType(cls, sessionType):
        return True if issubclass(sessionType,bs.FreeForAllSession) else False
    
    @classmethod
    def getDescription(cls,sessionType):
        return 'Grow your territory'

    @classmethod
    def getSupportedMaps(cls,sessionType):
        return ['Doom Shroom', 'Rampage', 'Hockey Stadium', 'Crag Castle', 'Big G', 'Football Stadium']

    @classmethod
    def getSettings(cls,sessionType):
        return [("Claim Size",{'minValue':2,'default':5,'increment':1}),
                ("Min Sec btw Claims",{'minValue':1,'default':3,'increment':1}),
                ("Eggs Not Bombs",{'default':True}),
                ("Snowman Eggs",{'default':True}),
                ("Egg Lifetime",{'minValue':0.5,'default':2.0,'increment':0.5}),
                ("Time Limit",{'choices':[('30 Seconds',30),('1 Minute',60),
                                            ('90 Seconds',90),('2 Minutes',120),
                                            ('3 Minutes',180),('5 Minutes',300)],'default':60}),
                ("Respawn Times",{'choices':[('Shorter',0.25),('Short',0.5),('Normal',1.0),('Long',2.0),('Longer',4.0)],'default':1.0}),
                ("Epic Mode",{'default':False})]

    def __init__(self,settings):
        bs.TeamGameActivity.__init__(self, settings)

        if self.settings['Epic Mode']: self._isSlowMotion = True        
        # print messages when players die (since its meaningful in this game)
        self.announcePlayerDeaths = True
        self._scoreBoard = bs.ScoreBoard()
        #self._lastPlayerDeathTime = None    

        self.minOverlap = 0.2 # This is the minimum amount of linear overlap for a spaz's own area to guarantee they can walk to it
        self.claimRad = math.sqrt(self.settings['Claim Size']/3.1416) #This is so that the settings can be in units of area, same as score
        self.updateRate = 200 #update the mine radii etc every this many milliseconds
        #This game's score calculation is very processor intensive.
        #Score only updated 2x per second during game, at lower resolution
        self.scoreUpdateRate = 1000
        self.inGameScoreRes = 40
        self.finalScoreRes = 300
        self._eggModel = bs.getModel('egg')
        try: myFactory = self._sharedSpazFactory
        except Exception:
            myFactory = self._sharedSpazFactory = bsSpaz.SpazFactory()
        m=myFactory._getMedia('Frosty')
        self._ballModel = m['pelvisModel']
        self._bombMat = bsBomb.BombFactory().bombMaterial
        self._mineIconTex=bs.Powerup.getFactory().texLandMines

    def getInstanceDescription(self):
        return ('Control territory with mines')

    def getInstanceScoreBoardDescription(self):
        return ('Control the most territory with mines\nDouble punch to switch between mines and bombs\n')

    def onTransitionIn(self):
        bs.TeamGameActivity.onTransitionIn(self, music='Epic' if self.settings['Epic Mode'] else 'Survival')
        self._startGameTime = bs.getGameTime()
        
    def onBegin(self):
        bs.TeamGameActivity.onBegin(self)
        self.setupStandardTimeLimit(self.settings['Time Limit'])
        bs.gameTimer(self.scoreUpdateRate, bs.WeakCall(self._updateScoreBoard), repeat=True)
        bs.gameTimer(1000, bs.WeakCall(self.startUpdating), repeat=False)#Delay to allow for home mine to spawn
        #self._bots = bs.BotSet() 
        # check for immediate end (if we've only got 1 player, etc)
        #bs.gameTimer(5000, self._checkEndGame)

    def onTeamJoin(self,team):
        team.gameData['spawnOrder'] = []
        team.gameData['score'] = 0        
        
    def onPlayerJoin(self, player):
        # don't allow joining after we start
        # (would enable leave/rejoin tomfoolery)
        player.gameData['mines'] = []
        if self.hasBegun():
            bs.screenMessage(bs.Lstr(resource='playerDelayedJoinText',subs=[('${PLAYER}',player.getName(full=True))]),color=(0,1,0))
            # for score purposes, mark them as having died right as the game started
            #player.gameData['deathTime'] = self._timer.getStartTime()
            return
        player.gameData['home'] = None
        player.gameData['bots'] = []
        player.gameData['bset'] = zBotSet()
        player.gameData['bset'].sourcePlayer = player
        self.spawnPlayer(player)
        
    def onPlayerLeave(self, player):
         # augment default behavior...
        for m in player.gameData['mines']:
            m.handleMessage(bs.DieMessage())
        player.gameData['mines'] = []
        bs.TeamGameActivity.onPlayerLeave(self, player)
        # a departing player may trigger game-over
        self._checkEndGame()

    def startUpdating(self):
        bs.gameTimer(self.updateRate, bs.WeakCall(self.mineUpdate), repeat=True)

    def _updateScoreBoard(self):
        for team in self.teams:
            team.gameData['score'] = self.areaCalc(team,self.inGameScoreRes)
            self._scoreBoard.setTeamValue(team,team.gameData['score'])
        
    def mineUpdate(self):
        for player in self.players:
            #Need to purge mines, whether or not player is living
            for m in player.gameData['mines']:
                if not m.exists():
                    player.gameData['mines'].remove(m)
            if not player.actor is None:
                if player.actor.isAlive():
                    pSafe = False
                    p1 = player.actor.node.position
                    for teamP in player.getTeam().players:
                        for m in teamP.gameData['mines']:
                            if m.exists():
                                if not m._exploded:
                                    p2 = m.node.position
                                    diff = (bs.Vector(p1[0]-p2[0],0.0,p1[2]-p2[2]))
                                    dist = (diff.length())
                                    if dist < m.rad:
                                        pSafe = True
                                        break
                    if not pSafe:
                        #print player.getName(), "died with mines:", len(player.gameData['mines'])
                        player.actor.handleMessage(bs.DieMessage())
        

    def endGame(self):
        results = bs.TeamGameResults()
        for t in self.teams: results.setTeamScore(t,t.gameData['score'])
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

        if isinstance(m, bs.SpazBotDeathMessage):
            if m.badGuy.sourcePlayer.exists():
                m.badGuy.sourcePlayer.gameData['bots'].remove(m.badGuy)
        elif isinstance(m,bs.PlayerSpazDeathMessage):

            bs.TeamGameActivity.handleMessage(self,m) # (augment standard behavior)
            self.respawnPlayer(m.spaz.getPlayer())
            #deathTime = bs.getGameTime()
            
            # record the player's moment of death
            #m.spaz.getPlayer().gameData['deathTime'] = deathTime

            # in co-op mode, end the game the instant everyone dies (more accurate looking)
            # in teams/ffa, allow a one-second fudge-factor so we can get more draws
            #if isinstance(self.getSession(),bs.CoopSession):
                # teams will still show up if we check now.. check in the next cycle
            #    bs.pushCall(self._checkEndGame)
            #    self._lastPlayerDeathTime = deathTime # also record this for a final setting of the clock..
            #else:
                #bs.gameTimer(1000, self._checkEndGame)

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
        #Overloaded for this game to respawn at home instead of random FFA spots
        if not player.exists():
            bs.printError('spawnPlayer() called for nonexistant player')
            return
        if player.gameData['home'] is None:
            pos = self.getMap().getFFAStartPosition(self.players)
            bomb = myMine(pos,
                           (0.0,0.0,0.0),
                           0.0,
                           player,
                           None).autoRetain()
            bomb.isHome = True
            bomb.handleMessage(bsBomb.ArmMessage())
            position = [pos[0],pos[1]+0.3,pos[2]]
            player.gameData['home'] = position
            player.gameData['mines'].append(bomb)
        else:
            position = player.gameData['home']
        spaz = self.spawnPlayerSpaz(player, position)

        # lets reconnect this player's controls to this
        # spaz but *without* the ability to attack or pick stuff up
        spaz.connectControlsToPlayer(enablePunch=True,
                                     enableBomb=True,
                                     enablePickUp=True)
        #Wire up the spaz with mines
        spaz.landMineCount = 1
        spaz.node.billboardTexture = self._mineIconTex
        bs.animate(spaz.node,"billboardOpacity",{0:0.0,100:1.0,400:1.0})
        t = bs.getGameTime()
        if t - spaz.lastMine < spaz.mineTimeout:
            spaz.node.billboardCrossOut = True
            bs.gameTimer((spaz.mineTimeout-t+spaz.lastMine),bs.WeakCall(spaz.unCrossBillboard))
        spaz.dropEggs = self.settings['Eggs Not Bombs']
        spaz.eggsHatch = self.settings['Snowman Eggs']

        # also lets have them make some noise when they die..
        spaz.playBigDeathSound = True  
      
    def spawnPlayerSpaz(self,player,position=(0,0,0),angle=None):
        """
        Create and wire up a bs.PlayerSpaz for the provide bs.Player.
        """
        #position = self.getMap().getFFAStartPosition(self.players)
        name = player.getName()
        color = player.color
        highlight = player.highlight

        lightColor = bsUtils.getNormalizedColor(color)
        displayColor = bs.getSafeColor(color,targetIntensity=0.75)
        spaz = PlayerSpaz_Grab(color=color,
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
        
        ###These special attributes are for Land Grab:
        spaz.lastMine = 0
        spaz.mineTimeout = self.settings['Min Sec btw Claims'] * 1000
        
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

    def areaCalc(self,team,res):
        ##This routine calculates (well, approximates) the area covered by a team
        ##and returns their score.  the "res" argument is the resolution.  Higher res,
        ##better approximation.
        ##Most of this code was stolen from rosettacode.org/wiki/Total_circles_area
        circles = ()
        for p in team.players:
            for m in p.gameData['mines']:
                if m.exists():
                    if m.rad != 0:
                        if not m._exploded:
                            circles += ((m.node.position[0],m.node.position[2], m.rad),)
        # compute the bounding box of the circles
        if len(circles) == 0: return 0
        x_min = min(c[0] - c[2] for c in circles)
        x_max = max(c[0] + c[2] for c in circles)
        y_min = min(c[1] - c[2] for c in circles)
        y_max = max(c[1] + c[2] for c in circles)
     
        box_side = res
     
        dx = (x_max - x_min) / box_side
        dy = (y_max - y_min) / box_side
     
        count = 0
     
        for r in xrange(box_side):
            y = y_min + r * dy
            for c in xrange(box_side):
                x = x_min + c * dx
                if any((x-circle[0])**2 + (y-circle[1])**2 <= (circle[2] ** 2)
                       for circle in circles):
                    count += 1
     
        return int(count * dx * dy  *10)    
            
    def endGame(self):

        if self.hasEnded(): return
        #sorryTxt = bsUtils.Text('Calculating final scores!...')
        for team in self.teams:
            team.gameData['score'] = str(round(self.areaCalc(team,self.finalScoreRes),2))
        #sorryTxt.handleMessage(bs.DieMessage())
        #print 'calc time:', (bs.getRealTime() - t)
        bs.gameTimer(300, bs.Call(self.waitForScores))
    def waitForScores(self):
        results = bs.TeamGameResults()
        self._vsText = None # kill our 'vs' if its there
        for team in self.teams:
            results.setTeamScore(team, team.gameData['score'])
        self.end(results=results)




