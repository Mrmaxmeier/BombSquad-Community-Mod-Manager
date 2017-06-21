import bs
import random
import bsUtils
import weakref

'''
    Gamemode: Collector
    Creator: TheMikirog
    Website: https://bombsquadjoyride.blogspot.com/
    
    This is a gamemode purely made by me just to spite unchallenged modders out there that put out crap to the market. 
    We don't want gamemodes that are just the existing ones with some novelties! Gamers deserve more!
    
    In this gamemode you have to kill others in order to get their Capsules. Capsules can be collected and staked in your inventory, how many as you please.
    After you kill an enemy that carries some of them, they drop a respective amount of Capsules they carried + two more.
    Your task is to collect these Capsules, get to the flag and score them KOTH style. You can't score if you don't have any Capsules with you.
    The first player or team to get to the required ammount wins.
    This is a gamemode all about trying to stay alive and picking your battles in order to win. A rare skill in BombSquad, where everyone is overly aggressive.
'''

# scripts specify an API-version they were written against
# so the game knows to ignore out-of-date ones.
def bsGetAPIVersion():
    return 4
# how BombSquad asks us what games we provide
def bsGetGames():
    return [CollectorGame]

class CollectorGame(bs.TeamGameActivity):

    tips = ['Making you opponent fall down the pit makes his Capsules wasted!\nTry not to kill enemies by throwing them off the cliff.',
            'Don\'t be too reckless. You can lose your loot quite quickly!',
            'Don\'t let the leading player score his Capsules at the Deposit Point!\nTry to catch him if you can!',
            'Lucky Capsules give 4 to your inventory and they have 8% chance of spawning after kill!',
            'Don\t camp in one place! Make your move first, so hopefully you get some dough!']

    FLAG_NEW = 0
    FLAG_UNCONTESTED = 1
    FLAG_CONTESTED = 2
    FLAG_HELD = 3

    @classmethod
    def getName(cls):
        return 'Collector'

    @classmethod
    def getDescription(cls,sessionType):
        return ('Kill your opponents to steal their Capsules.\n'
               'Collect them and score at the Deposit point!')

    def onBegin(self):
        bs.TeamGameActivity.onBegin(self)
        self.setupStandardTimeLimit(self.settings['Time Limit'])
        self.setupStandardPowerupDrops()
        if len(self.teams) > 0:
            self._scoreToWin = self.settings['Capsules to Collect'] * max(1,max(len(t.players) for t in self.teams))
        else: self._scoreToWin = self.settings['Capsules to Collect']
        self._updateScoreBoard()
        self._dingSound = bs.getSound('dingSmall')
        if isinstance(bs.getActivity().getSession(),bs.FreeForAllSession):
            self._flagNumber = random.randint(0,1)
            self._flagPos = self.getMap().getFlagPosition(self._flagNumber)
        else: self._flagPos = self.getMap().getFlagPosition(None)
        bs.gameTimer(1000,self._tick,repeat=True)
        self._flagState = self.FLAG_NEW
        self.projectFlagStand(self._flagPos)

        self._flag = bs.Flag(position=self._flagPos,
                             touchable=False,
                             color=(1,1,1))
        self._flagLight = bs.newNode('light',
                                     attrs={'position':self._flagPos,
                                            'intensity':0.2,
                                            'heightAttenuated':False,
                                            'radius':0.4,
                                            'color':(0.2,0.2,0.2)})

        # flag region
        bs.newNode('region',
                   attrs={'position':self._flagPos,
                          'scale': (1.8,1.8,1.8),
                          'type': 'sphere',
                          'materials':[self._flagRegionMaterial,bs.getSharedObject('regionMaterial')]})
        self._updateFlagState()
        
    @classmethod
    def supportsSessionType(cls,sessionType):
        return True if (issubclass(sessionType,bs.TeamsSession)
                        or issubclass(sessionType,bs.FreeForAllSession)) else False
                        
    @classmethod
    def getSupportedMaps(cls,sessionType):
        return bs.getMapsSupportingPlayType("keepAway")

    @classmethod
    def getSettings(cls,sessionType):
        settings = [("Capsules to Collect",{'minValue':1,'default':10,'increment':1}),
                    ("Capsules on Death",{'minValue':1,'maxValue':10,'default':2,'increment':1}),
                    ("Time Limit",{'choices':[('None',0),('1 Minute',60),
                                              ('2 Minutes',120),('5 Minutes',300),
                                              ('10 Minutes',600),('20 Minutes',1200)],'default':0}),
                    ("Respawn Times",{'choices':[('Shorter',0.25),('Short',0.5),('Normal',1.0),('Long',2.0),('Longer',4.0)],'default':1.0}),
                    ("Allow Lucky Capsules",{'default':True}),
                    ("Epic Mode",{'default':False})]
        return settings
        
    def __init__(self,settings):
        bs.TeamGameActivity.__init__(self,settings)
        if self.settings['Epic Mode']: self._isSlowMotion = True

        # print messages when players die since it matters here..
        self.announcePlayerDeaths = True
        
        self._scoreBoard = bs.ScoreBoard()
        self._swipSound = bs.getSound("swip")
        self._tickSound = bs.getSound('tick')
        
        self._scoreToWin = self.settings['Capsules to Collect']
        
        self._capsuleModel = bs.getModel('bomb')
        self._capsuleTex = bs.getTexture('bombColor')
        self._capsuleLuckyTex = bs.getTexture('bombStickyColor')
        
        self._collectSound = bs.getSound('powerup01')
        self._luckyCollectSound = bs.getSound('cashRegister2')
        
        self._capsuleMaterial = bs.Material()
        self._capsuleMaterial.addActions(conditions=("theyHaveMaterial",bs.getSharedObject('playerMaterial')),
                                     actions=(("call","atConnect",self._onCapsulePlayerCollide),))
        self._capsules = []
        
        self._flagRegionMaterial = bs.Material()
        self._flagRegionMaterial.addActions(conditions=("theyHaveMaterial",bs.getSharedObject('playerMaterial')),
                                            actions=(("modifyPartCollision","collide",True),
                                                     ("modifyPartCollision","physical",False),
                                                     ("call","atConnect",bs.Call(self._handlePlayerFlagRegionCollide,1)),
                                                     ("call","atDisconnect",bs.Call(self._handlePlayerFlagRegionCollide,0))))
        
    def getInstanceDescription(self):
        return ('Score ${ARG1} capsules from your enemies.',self._scoreToWin)

    def getInstanceScoreBoardDescription(self):
        return ('collect ${ARG1} capsules',self._scoreToWin)
        
    def onTeamJoin(self,team):
        team.gameData['capsules'] = 0
        self._updateScoreBoard()

    def onPlayerJoin(self,player):
        bs.TeamGameActivity.onPlayerJoin(self,player)
        player.gameData['atFlag'] = 0
        player.gameData['capsules'] = 0
        
    def spawnPlayer(self,player):
        spaz = self.spawnPlayerSpaz(player)
        spaz.connectControlsToPlayer()
        player.gameData['capsules'] = 0
        
    def _tick(self):
        self._updateFlagState()
        scoringTeam = None if self._scoringTeam is None else self._scoringTeam()

        # give holding players points
        for player in self.players:
            if player.gameData['atFlag'] > 0 and player.gameData['capsules'] > 0 and self._flagState == self.FLAG_HELD and scoringTeam.gameData['capsules'] < self._scoreToWin:
                player.gameData['capsules'] -= 1
                self._handleCapsuleStorage((self._flagPos[0],self._flagPos[1]+1,self._flagPos[2]),player)
                self.scoreSet.playerScored(player,3,screenMessage=False,display=False)

                if scoringTeam:
        
                    if scoringTeam.gameData['capsules'] < self._scoreToWin: bs.playSound(self._tickSound)
        
                    scoringTeam.gameData['capsules'] = max(0,scoringTeam.gameData['capsules']+1)
                    self._updateScoreBoard()
                    if scoringTeam.gameData['capsules'] > 0:
                        self._flag.setScoreText(str(self._scoreToWin-scoringTeam.gameData['capsules']))
        
                    # winner
                    if scoringTeam.gameData['capsules'] >= self._scoreToWin:
                        self.endGame()
                        
                
    def endGame(self):
        results = bs.TeamGameResults()
        for team in self.teams: results.setTeamScore(team,team.gameData['capsules'])
        self.end(results=results,announceDelay=0)
        
    def _updateFlagState(self):
        holdingTeams = set(player.getTeam() for player in self.players if player.gameData['atFlag'])
        prevState = self._flagState
        if len(holdingTeams) > 1:
            self._flagState = self.FLAG_CONTESTED
            self._scoringTeam = None
            self._flagLight.color = (0.6,0.6,0.1)
            self._flag.node.color = (1.0,1.0,0.4)
        elif len(holdingTeams) == 1:
            holdingTeam = list(holdingTeams)[0]
            self._flagState = self.FLAG_HELD
            self._scoringTeam = weakref.ref(holdingTeam)
            self._flagLight.color = bs.getNormalizedColor(holdingTeam.color)
            self._flag.node.color = holdingTeam.color
        else:
            self._flagState = self.FLAG_UNCONTESTED
            self._scoringTeam = None
            self._flagLight.color = (0.2,0.2,0.2)
            self._flag.node.color = (1,1,1)
        if self._flagState != prevState:
            bs.playSound(self._swipSound)

    def _handlePlayerFlagRegionCollide(self,colliding):
        flagNode,playerNode = bs.getCollisionInfo("sourceNode","opposingNode")
        try: player = playerNode.getDelegate().getPlayer()
        except Exception: return

        # different parts of us can collide so a single value isn't enough
        # also don't count it if we're dead (flying heads shouldnt be able to win the game :-)
        if colliding and player.isAlive(): player.gameData['atFlag'] += 1
        else: player.gameData['atFlag'] = max(0,player.gameData['atFlag'] - 1)

        self._updateFlagState()

    def _updateScoreBoard(self):
        for team in self.teams:
            self._scoreBoard.setTeamValue(team,team.gameData['capsules'],self.settings['Capsules to Collect'],countdown=True)
        
    def onTransitionIn(self):
        bs.TeamGameActivity.onTransitionIn(self, music='Epic' if self.settings['Epic Mode'] else 'Scary')
        
    def _updateScoreBoard(self):
        for team in self.teams:
            self._scoreBoard.setTeamValue(team,team.gameData['capsules'],self._scoreToWin)
            
    def _onCapsulePlayerCollide(self):
        if not self.hasEnded():
            capsuleNode, playerNode = bs.getCollisionInfo('sourceNode','opposingNode')
            if capsuleNode is not None and playerNode is not None:
                capsule = capsuleNode.getDelegate()
                spaz = playerNode.getDelegate()
                player = spaz.getPlayer() if hasattr(spaz,'getPlayer') else None
                if player is not None and player.exists() and capsule is not None:
                    if player.isAlive():
                        if capsuleNode.colorTexture == self._capsuleLuckyTex:
                            player.gameData['capsules'] += 4
                            bsUtils.PopupText('BONUS!',
                                              color=(1,1,0),
                                              scale=1.5,
                                              position=(capsuleNode.position)).autoRetain()
                            bs.playSound(self._luckyCollectSound,1.0,position=capsuleNode.position)
                            bs.emitBGDynamics(position=capsuleNode.position,velocity=(0,0,0),count=int(6.4+random.random()*24),scale=1.2, spread=2.0,chunkType='spark');
                            bs.emitBGDynamics(position=capsuleNode.position,velocity=(0,0,0),count=int(4.0+random.random()*6),emitType='tendrils');
                        else:
                            player.gameData['capsules'] += 1
                            bs.playSound(self._collectSound,0.6,position=capsuleNode.position)
                        # create a flash
                        light = bs.newNode('light',
                                        attrs={'position': capsuleNode.position,
                                                'heightAttenuated':False,
                                                'radius':0.1,
                                                'color':(1,1,0)})
                        
                        # Create a short text informing about your inventory
                        self._handleCapsuleStorage(playerNode.position,player)
                        
                        bs.animate(light,'intensity',{0:0,100:0.5,200:0},loop=False)
                        bs.gameTimer(200,light.delete)
                        capsule.handleMessage(bs.DieMessage())
                        
    def _handleCapsuleStorage(self,pos,player):
        self.capsules = player.gameData['capsules']
        
        if player.gameData['capsules'] > 10: 
            player.gameData['capsules'] = 10
            self.capsules = 10
            bsUtils.PopupText('Full Capacity!',
                            color=(1,0.85,0),
                            scale=1.75,
                            position=(pos[0],pos[1]-1,pos[2])).autoRetain()
        # Make a different color and size depending on the storage
        if self.capsules > 7:
            self.color = (1,0,0)
            self.size = 2.4
        elif self.capsules > 7:
            self.color = (1,0.4,0.4)
            self.size = 2.1
        elif self.capsules > 4:
            self.color = (1,1,0.4)
            self.size = 2.0
        else:
            self.color = (1,1,1)
            self.size = 1.9
        if self.capsules < 10:
            bsUtils.PopupText((str(player.gameData['capsules'])),
                                            color=self.color,
                                            scale=self.size+(0.02*self.capsules),
                                            position=(pos[0],pos[1]-1,pos[2])).autoRetain()
        
    # various high-level game events come through this method
    def handleMessage(self,m):

        # respawn dead players
        if isinstance(m,bs.PlayerSpazDeathMessage):
            bs.TeamGameActivity.handleMessage(self,m) # augment standard behavior

            player = m.spaz.getPlayer()
            self.respawnPlayer(player) # Respawn the player
            pt = m.spaz.node.position
            
            for i in range(player.gameData['capsules'] + self.settings['Capsules on Death']): # Throw out capsules that the victim has + 2 more to keep the game running
                w = 0.6 # How far from each other these capsules should spawn
                s = 0.005 - (player.gameData['capsules']*0.01) # How much these capsules should fly after spawning
                self._capsules.append(Capsule(position=(pt[0]+random.uniform(-w,w),
                                                pt[1]+0.75+random.uniform(-w,w),
                                                pt[2]),
                                                velocity=(random.uniform(-s,s),
                                                random.uniform(-s,s),
                                                random.uniform(-s,s)),
                                                lucky=False))
            if random.randint(1,12) == 1 and self.settings['Allow Lucky Capsules']:
                w = 0.6 # How far from each other these capsules should spawn
                s = 0.005 # How much these capsules should fly after spawning
                self._capsules.append(Capsule(position=(pt[0]+random.uniform(-w,w),
                                                pt[1]+0.75+random.uniform(-w,w),
                                                pt[2]),
                                                velocity=(random.uniform(-s,s),
                                                random.uniform(-s,s),
                                                random.uniform(-s,s)),
                                                lucky=True))
            player.gameData['atFlag'] = 0
        else:
            # default handler:
            bs.TeamGameActivity.handleMessage(self,m)
            
class Capsule(bs.Actor):

    def __init__(self, position=(0,1,0), velocity=(0,0.5,0),lucky=False):
        bs.Actor.__init__(self)
        self._luckyAppearSound = bs.getSound('ding')
        
        activity = self.getActivity()
        
        # spawn just above the provided point
        self._spawnPos = (position[0], position[1], position[2])
        if lucky:
            bs.playSound(self._luckyAppearSound,1.0,self._spawnPos)
            self.capsule = bs.newNode("prop",
                                attrs={'model': activity._capsuleModel,
                                        'colorTexture': activity._capsuleLuckyTex,
                                        'body':'crate',
                                        'reflection':'powerup',
                                        'modelScale':0.8,
                                        'bodyScale':0.65,
                                        'density':6.0,
                                        'reflectionScale':[0.15],
                                        'shadowSize': 0.65,
                                        'position':self._spawnPos,
                                        'velocity':velocity,
                                        'materials': [bs.getSharedObject('objectMaterial'),activity._capsuleMaterial]
                                        },
                                delegate=self)
            bs.animate(self.capsule,"modelScale",{0:0, 100:0.9, 160:0.8})
            self.lightCapsule = bs.newNode('light',
                                            attrs={'position':self._spawnPos,
                                                'heightAttenuated':False,
                                                'radius':0.5,
                                                'color':(0.2,0.2,0)})
        else:
            self.capsule = bs.newNode("prop",
                                attrs={'model': activity._capsuleModel,
                                        'colorTexture': activity._capsuleTex,
                                        'body':'capsule',
                                        'reflection':'soft',
                                        'modelScale':0.6,
                                        'bodyScale':0.3,
                                        'density':4.0,
                                        'reflectionScale':[0.15],
                                        'shadowSize': 0.6,
                                        'position':self._spawnPos,
                                        'velocity':velocity,
                                        'materials': [bs.getSharedObject('objectMaterial'),activity._capsuleMaterial]
                                        },
                                delegate=self)
            bs.animate(self.capsule,"modelScale",{0:0, 100:0.6, 160:0.5})
            self.lightCapsule = bs.newNode('light',
                                            attrs={'position':self._spawnPos,
                                                'heightAttenuated':False,
                                                'radius':0.1,
                                                'color':(0.2,1,0.2)})
        self.capsule.connectAttr('position',self.lightCapsule,'position')

    def handleMessage(self,m):
        if isinstance(m,bs.DieMessage):
            self.capsule.delete()
            try:
                bs.animate(self.lightCapsule,'intensity',{0:1.0,50:0.0},loop=False)
                bs.gameTimer(50,self.lightCapsule.delete)
            except AttributeError: pass
        elif isinstance(m,bs.OutOfBoundsMessage):
            self.handleMessage(bs.DieMessage())
        elif isinstance(m,bs.HitMessage):
            self.capsule.handleMessage("impulse",m.pos[0],m.pos[1],m.pos[2],
                                    m.velocity[0]/8,m.velocity[1]/8,m.velocity[2]/8,
                                    1.0*m.magnitude,1.0*m.velocityMagnitude,m.radius,0,
                                    m.forceDirection[0],m.forceDirection[1],m.forceDirection[2])
        else:
            bs.Actor.handleMessage(self,m)
    
