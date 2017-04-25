import bs
import random
import bsUtils
import bsBomb

def bsGetAPIVersion():
    # see bombsquadgame.com/apichanges
    return 4

def bsGetGames():
    return [HazardousCargo]

class boxCrossMessage(object):
    pass

class myMine(bs.Bomb):
    #reason for the mine class is so we can get the HitMessage.
    #We need the HitMessage to prevent chain reactions from pretty
    #much blowing the whole map.
    def __init__(self,pos):
        bs.Bomb.__init__(self,position=pos,bombType='landMine')
        self.hitSubType = 1 #Startt SubType at 1

    def handleMessage(self,m):
        #print(m)
        if isinstance(m, bs.HitMessage):
            #print(['hit',m.hitSubType])
            #hitSubType comes from the thing doing the hitting.
            #In our case, all the mines start with 1.  We want to increment
            #hitSubType with each successive hitter so that we can limit
            #chain reactions that pretty much clear the whole map.
            if m.hitSubType < 4:
                self.hitSubType = m.hitSubType + 1
                m.hitSubType = self.hitSubType
                super(self.__class__, self).handleMessage(m)
        else:
            super(self.__class__, self).handleMessage(m)
            
class cargoBox(bs.Bomb):

    def __init__(self,pos):
        bs.Bomb.__init__(self,position=pos,bombType='tnt')
        self.claimedBy = None
        self.scored = False
        #self = box
        fm = bs.Flag.getFactory().flagMaterial
        materials = getattr(self.node,'materials')
        if not fm in materials:
            setattr(self.node,'materials',materials + (fm,))

    def handleMessage(self,m):
        if isinstance(m,bs.HitMessage):
            if m.hitSubType == 'tnt':
                return True
            else:
                super(self.__class__, self).handleMessage(m)
        if isinstance(m, boxCrossMessage):
            self.getActivity().checkForScore(self)
        if isinstance(m, bs.PickedUpMessage):
            self._updateBoxState()
        if isinstance(m, bs.DieMessage):
            act = self.getActivity()
            act.updateBoxTimer()
            super(self.__class__, self).handleMessage(m)
        else:
            super(self.__class__, self).handleMessage(m)

    def _updateBoxState(self):
        claimerHold = False
        userperHold = False
        for player in self.getActivity().players:
            try:
                if player.actor.isAlive() and player.actor.node.holdNode.exists():
                    holdingBox = (player.actor.node.holdNode == self.node)
                else: holdingBox = False
            except Exception:
                bs.printException("exception checking hold flag")
            if holdingBox:
                if self.claimedBy is None:
                    self.claimedBy = player
                    claimerHold = True
                else:
                    if self.claimedBy == player:
                        claimerHold = True
                    else:
                        userperHold = True
        #release claim on any other existing boxes
        for box in self.getActivity().boxes:
            if box <> self and box.claimedBy == self.claimedBy:
                box.claimedBy = None
        #Blow up this box if it belongs to someone else
        if (not claimerHold) and userperHold:
            self.handleMessage(bs.HitMessage())
        

                
class HazardousCargo(bs.TeamGameActivity):

    @classmethod
    def getName(cls):
        return 'Hazardous Cargo'

    @classmethod
    def getScoreInfo(cls):
        return {'scoreName':'Survived',
                'scoreType':'seconds',
                'noneIsWinner':False,
                'lowerIsBetter':True}
                
    @classmethod
    def supportsSessionType(cls,sessionType):
        # we support teams, free-for-all
        return True if (issubclass(sessionType,bs.TeamsSession)
                        or issubclass(sessionType,bs.FreeForAllSession)) else False
    
    @classmethod
    def getDescription(cls,sessionType):
        return 'Go get a TNT box and return to the end zone.'

    @classmethod
    def getSupportedMaps(cls,sessionType):
        return bs.getMapsSupportingPlayType('football')

    @classmethod
    def getSettings(cls,sessionType):
        return [("Score to Win",{'minValue':1,'default':1,'increment':1}),
                ("Max Mines",{'minValue':20,'default':80,'increment':10}),
                ("Start Mines",{'minValue':20,'default':40,'increment':10}),
                ("Mines per Second",{'minValue':1,'default':5,'increment':1}),
                ("Enable Bombs",{'default':False}),
                ("One-Way Trip",{'default':False}),
                ("Time Limit",{'choices':[('None',0),('1 Minute',60),
                                        ('2 Minutes',120),('5 Minutes',300),
                                        ('10 Minutes',600),('20 Minutes',1200)],'default':120}),
                ("Respawn Times",{'choices':[('Shorter',0.25),('Short',0.5),('Normal',1.0),('Long',2.0),('Longer',4.0)],'default':1.0}),
                ]

    def __init__(self,settings):
        bs.TeamGameActivity.__init__(self,settings)
        self._scoreBoard = bs.ScoreBoard()
        self.boxes = []
        self.mines = []
        # load some media we need
        self._cheerSound = bs.getSound("cheer")
        self._chantSound = bs.getSound("crowdChant")
        self._scoreSound = bs.getSound("score")
        self._swipSound = bs.getSound("swip")
        self._whistleSound = bs.getSound("refWhistle")

        self.scoreRegionMaterial = bs.Material()
        self.scoreRegionMaterial.addActions(
            conditions=("theyHaveMaterial",bs.Flag.getFactory().flagMaterial),
            actions=(("modifyPartCollision","collide",True),
                     ("modifyPartCollision","physical",False),
                     ("message",'theirNode','atConnect',boxCrossMessage())))

    def getInstanceDescription(self):
        return ('Go get a TNT box and carry it to the end zone.')

    def getInstanceScoreBoardDescription(self):
        tds = self.settings['Score to Win']
        if tds > 1: return ('Bring back ${ARG1} TNT boxes. Better get your own!',tds)
        else: return ('Bring back a TNT box. Better get your own!')

    def onTransitionIn(self):
        bs.TeamGameActivity.onTransitionIn(self, music='Football')
        self._startGameTime = bs.getGameTime()
        
    def onBegin(self):
        bs.TeamGameActivity.onBegin(self)
        self.winners = []
        self.setupStandardTimeLimit(self.settings['Time Limit'])

        # set up the score region
        self._scoreRegions = []

        defs = self.getMap().defs
        self._scoreRegions.append(bs.NodeActor(bs.newNode('region',
                                                          attrs={'position':defs.boxes['goal1'][0:3],
                                                                 'scale':defs.boxes['goal1'][6:9],
                                                                 'type': 'box',
                                                                 'materials':(self.scoreRegionMaterial,)})))

        self._updateScoreBoard()
        self.updateBoxes()
        #Preload the play area with mines
        while len(self.mines) < self.settings['Start Mines']:
            x = random.uniform(-11.3, 11.3)
            y = random.uniform(-5.2,5.7)
            pos = [x,0.32,y]
            self._makeMine(pos)
        bs.playSound(self._chantSound)
        #Set up the timer for mine spawning
        bs.gameTimer(int(1000/self.settings['Mines per Second']), bs.WeakCall(self.mineUpdate), repeat=True)
        bs.gameTimer(1000, self._update, repeat=True)
        
    def updateBoxTimer(self):
        bs.gameTimer(50, self.updateBoxes)
    def updateBoxes(self):
        for box in self.boxes:
            if not box.exists():
                self.boxes.remove(box)
        while len(self.boxes) < len(self.teams):
            #x = random.uniform(-12.5,-11.3)
            y = random.uniform(-5,5.5)
            self.boxes.append(cargoBox([-12.3,0.4,y]))
            
    def onTeamJoin(self,team):
        team.gameData['score'] = 0
        team.gameData['survivalSeconds'] = None
        self._updateScoreBoard()
        self.updateBoxes()
        
    def checkForScore(self, box):
        if box.scored: return
        player = box.claimedBy
        if player.actor.isAlive() and player.actor.node.holdNode.exists():
            if player.actor.node.holdNode == box.node:
                box.scored = True
                player.getTeam().gameData['score'] +=1
                bsUtils.animate(box.node, "modelScale", {0:1.0, 150:0.5, 300:0.0})
                bs.gameTimer(300, bs.WeakCall(box.handleMessage, bs.DieMessage()))
                self._updateScoreBoard()
                for playa in player.getTeam().players:
                    try: playa.actor.node.handleMessage('celebrate',2000)
                    except Exception: pass
                if player.getTeam().gameData['score'] == self.settings['Score to Win']:
                    player.getTeam().gameData['survivalSeconds'] = (bs.getGameTime()-self._startGameTime)/1000
                    self.winners.append(player.getTeam())
                    for playa in player.getTeam().players:
                        self._flashPlayer(playa,1.0)
                        playa.actor.handleMessage(bs.DieMessage(immediate=True))
                bs.playSound(self._scoreSound)
                bs.playSound(self._cheerSound)
            else:
                #print('nobody scored')
                box.handleMessage(bs.HitMessage())
        else:
            box.handleMessage(bs.HitMessage())
            
    def _update(self):
        
        # if we're down to 1 or fewer living teams, start a timer to end the game
        # (allows the dust to settle and draws to occur if deaths are close enough)
        if (len([team for team in self.teams if team.gameData['score'] < self.settings['Score to Win'] ]) < 2) or len(self.winners) > 2:
            self._roundEndTimer = bs.Timer(500,self.endGame)
    def mineUpdate(self):
        #purge dead mines
        for m in self.mines:
            if not m.exists():
                self.mines.remove(m)
        #Remove an old mine (if needed) and make a new mine
        if len(self.mines) > self.settings['Max Mines']:
            self.mines[0].handleMessage(bs.DieMessage(immediate=True))
            del self.mines[0]
        x = random.uniform(-10.3, 11.3)
        y = random.uniform(-5.2,5.7)
        pos = [x,0.32,y]
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

    def _updateScoreBoard(self):
        winScore = self.settings['Score to Win']
        for team in self.teams:
            self._scoreBoard.setTeamValue(team,team.gameData['score'],winScore)

    def handleMessage(self,m):

        # respawn dead players if they're still in the game
        if isinstance(m,bs.PlayerSpazDeathMessage):
            bs.TeamGameActivity.handleMessage(self,m) # augment standard behavior
            self.respawnPlayer(m.spaz.getPlayer())

        else:
            bs.TeamGameActivity.handleMessage(self,m) # augment standard behavior

    def spawnPlayer(self,player):
        """
        Spawn *something* for the provided bs.Player.
        The default implementation simply calls spawnPlayerSpaz().
        """
        #Overloaded for this game to spawn players in the end zone instead of FFA spots
        if not player.exists():
            bs.printError('spawnPlayer() called for nonexistant player')
            return
        y = random.uniform(-5,5.5)
        if self.settings['One-Way Trip'] == True:
            x = -11.8
        else:
            x = 12.0
        spz = self.spawnPlayerSpaz(player, position=[x,0.35,y])
        spz.connectControlsToPlayer(enablePunch=True,
                                     enableBomb=self.settings['Enable Bombs'],
                                     enablePickUp=True)
        return spz
