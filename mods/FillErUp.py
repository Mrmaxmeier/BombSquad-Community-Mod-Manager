import bs
import bsSpaz
import random
import bsUtils
import bsPowerup

def bsGetAPIVersion():
    # see bombsquadgame.com/apichanges
    return 4

def bsGetGames():
    return [FillErUp]
        
        
class cargoBox(bs.Bomb):

    def __init__(self,pos):
        bs.Bomb.__init__(self,position=pos,bombType='tnt')
        #self = box
        self.node.maxSpeed = 0
        self.node.damping = 100
        #self.node.density = 10
        pam = bs.Powerup.getFactory().powerupAcceptMaterial
        nPum = self.getActivity().noPickMat
        materials = getattr(self.node,'materials')
        if not pam in materials:
            setattr(self.node,'materials',materials + (pam,))
        materials = getattr(self.node,'materials')
        if not nPum in materials:
            setattr(self.node,'materials',materials + (nPum,))
    def handleMessage(self,m):
        if isinstance(m, bs.HitMessage):
            #We don't want crates taking damage.
            return True
        if isinstance(m, bs.PowerupMessage): #Give or take points, depending on powerup received.
            for player in self.getActivity().players:
                if player.gameData['crate'] == self:
                    if m.powerupType == 'health':
                        player.getTeam().gameData['score'] += 1
                    else:
                        player.getTeam().gameData['score'] += self.getActivity().settings['Curse Box Points']
                    self.getActivity()._updateScoreBoard()
                    self.setboxScoreText(str(player.getTeam().gameData['score']), player.color)
            if m.sourceNode.exists():
                m.sourceNode.handleMessage(bs.PowerupAcceptMessage())
        else:
            super(self.__class__, self).handleMessage(m)

    def setboxScoreText(self,t,color=(1,1,0.4),flash=False):
        """
        Utility func to show a message momentarily over our spaz that follows him around;
        Handy for score updates and things.
        """
        colorFin = bs.getSafeColor(color)[:3]
        if not self.node.exists(): return
        try: exists = self._scoreText.exists()
        except Exception: exists = False
        if not exists:
            startScale = 0.0
            m = bs.newNode('math',owner=self.node,attrs={'input1':(0,1.4,0),'operation':'add'})
            self.node.connectAttr('position',m,'input2')
            self._scoreText = bs.newNode('text',
                                          owner=self.node,
                                          attrs={'text':t,
                                                 'inWorld':True,
                                                 'shadow':1.0,
                                                 'flatness':1.0,
                                                 'color':colorFin,
                                                 'scale':0.02,
                                                 'hAlign':'center'})
            m.connectAttr('output',self._scoreText,'position')
        else:
            self._scoreText.color = colorFin
            startScale = self._scoreText.scale
            self._scoreText.text = t
        if flash:
            combine = bs.newNode("combine",owner=self._scoreText,attrs={'size':3})
            sc = 1.8
            offs = 0.5
            t = 300
            for i in range(3):
                c1 = offs+sc*colorFin[i]
                c2 = colorFin[i]
                bs.animate(combine,'input'+str(i),{0.5*t:c2,
                                                   0.75*t:c1,
                                                   1.0*t:c2})
            combine.connectAttr('output',self._scoreText,'color')
            
        bs.animate(self._scoreText,'scale',{0:startScale,200:0.02})
        #self._scoreTextHideTimer = bs.Timer(1000,bs.WeakCall(self._hideScoreText))
        
    def setMovingText(self, theActor, theText, color):
        m = bs.newNode('math', owner=theActor.node, attrs={'input1': (0, 0.7, 0), 'operation': 'add'})
        theActor.node.connectAttr('position', m, 'input2')
        theActor._movingText = bs.newNode('text',
                                      owner=theActor.node,
                                      attrs={'text':theText,
                                             'inWorld':True,
                                             'shadow':1.0,
                                             'flatness':1.0,
                                             'color':color,
                                             'scale':0.0,
                                             'hAlign':'center'})
        m.connectAttr('output', theActor._movingText, 'position')
        bs.animate(theActor._movingText, 'scale', {0: 0.0, 1000: 0.01})                      
        
class FillErUp(bs.TeamGameActivity):

    @classmethod
    def getName(cls):
        return 'Fill \'Er Up'

    @classmethod
    def getScoreInfo(cls):
        return {'scoreName':'score',
                'scoreType':'points',
                'noneIsWinner':False,
                'lowerIsBetter':False}
    
    @classmethod
    def getDescription(cls,sessionType):
        return 'Fill your crate with boxes'

    @classmethod
    def supportsSessionType(cls,sessionType):
        return True if (issubclass(sessionType,bs.FreeForAllSession)) else False

    @classmethod
    def getSupportedMaps(cls,sessionType):
        return ['Doom Shroom','Courtyard']

    @classmethod
    def getSettings(cls,sessionType):
        settings = [("Time Limit",{'choices':[('30 Seconds',30),('1 Minute',60),
                                            ('90 Seconds',90),('2 Minutes',120),
                                            ('3 Minutes',180),('5 Minutes',300)],'default':60}),
                    ("Respawn Times",{'choices':[('Shorter',0.25),('Short',0.5),('Normal',1.0),('Long',2.0),('Longer',4.0)],'default':1.0}),
                    ("Curse Box Chance (lower = more chance)",{'default':10,'minValue':5,'maxValue':15,'increment':1}),
                    ("Curse Box Points",{'default':-2,'minValue':-10,'maxValue':-1,'increment':1}),
                    ("Boxes Per Player",{'default':1.0,'minValue':0.5,'maxValue':3.0,'increment':0.5}),
                    ("Epic Mode",{'default':False})]

        if issubclass(sessionType,bs.TeamsSession):
            settings.append(("Solo Mode",{'default':False}))
            settings.append(("Balance Total Lives",{'default':False}))
            
        return settings

    def __init__(self,settings):
        bs.TeamGameActivity.__init__(self,settings)
        if self.settings['Epic Mode']: self._isSlowMotion = True

        # show messages when players die since it's meaningful here
        self.announcePlayerDeaths = True
        
        try: self._soloMode = settings['Solo Mode']
        except Exception: self._soloMode = False
        self._scoreBoard = bs.ScoreBoard()
        self.totBoxes = []
        
        #Create a special powerup material for our boxes that allows pickup.
        self.fpowerupMaterial = bs.Material()

        # pass a powerup-touched message to applicable stuff
        pam = bs.Powerup.getFactory().powerupAcceptMaterial
        self.fpowerupMaterial.addActions(
            conditions=(("theyHaveMaterial",pam)),
            actions=(("modifyPartCollision","collide",True),
                     ("modifyPartCollision","physical",False),
                     ("message","ourNode","atConnect",bsPowerup._TouchedMessage())))

        # we DO wanna be picked up
        #self.powerupMaterial.addActions(
        #    conditions=("theyHaveMaterial",bs.getSharedObject('pickupMaterial')),
        #    actions=( ("modifyPartCollision","collide",False)))

        self.fpowerupMaterial.addActions(
            conditions=("theyHaveMaterial",bs.getSharedObject('footingMaterial')),
            actions=(("impactSound",bs.Powerup.getFactory().dropSound,0.5,0.1)))
        
        #Create a material to prevent TNT box pickup
        self.noPickMat = bs.Material()
        self.noPickMat.addActions(
            conditions=("theyHaveMaterial",bs.getSharedObject('pickupMaterial')),
            actions=( ("modifyPartCollision","collide",False)))

    def getInstanceDescription(self):
        return 'Steal all the health boxes for yourself' if isinstance(self.getSession(),bs.TeamsSession) else 'Fill your crate with boxes'

    def getInstanceScoreBoardDescription(self):
        return 'Steal all the health boxes for yourself' if isinstance(self.getSession(),bs.TeamsSession) else 'Fill your crate with boxes'

    def onTransitionIn(self):
        bs.TeamGameActivity.onTransitionIn(self, music='Epic' if self.settings['Epic Mode'] else 'Survival')
        self._startGameTime = bs.getGameTime()

    def onTeamJoin(self,team):
        team.gameData['survivalSeconds'] = None
        team.gameData['spawnOrder'] = []
        team.gameData['score'] = 0


    def onPlayerJoin(self, player):

        #player.gameData['lives'] = 1
        player.getTeam().gameData['score'] = 0
        player.gameData['home'] = None
        player.gameData['crate'] = None
        self._updateScoreBoard()
        
        if self._soloMode:
            #player.gameData['icons'] = []
            player.getTeam().gameData['spawnOrder'].append(player)
            self._updateSoloMode()
        else:
            # create our icon and spawn
            #player.gameData['icons'] = [Icon(player,position=(0,50),scale=0.8)]
            self.spawnPlayer(player)

        # dont waste time doing this until begin
        if self.hasBegun():
            pass#self._updateIcons()

    def _updateSoloMode(self):
        # for both teams, find the first player on the spawn order list with lives remaining
        # and spawn them if they're not alive
        for team in self.teams:
            # prune dead players from the spawn order
            team.gameData['spawnOrder'] = [p for p in team.gameData['spawnOrder'] if p.exists()]
            for player in team.gameData['spawnOrder']:
                if player.gameData['lives'] > 0:
                    if not player.isAlive(): self.spawnPlayer(player)
                    break

    def _getSpawnPoint(self,player):
        # in solo-mode, if there's an existing live player on the map, spawn at whichever
        # spot is farthest from them (keeps the action spread out)
        if self._soloMode:
            livingPlayer = None
            for team in self.teams:
                for player in team.players:
                    if player.isAlive():
                        p = player.actor.node.position
                        livingPlayer = player
                        livingPlayerPos = p
                        break
            if livingPlayer:
                playerPos = bs.Vector(*livingPlayerPos)
                points = []
                for team in self.teams:
                    startPos = bs.Vector(*self.getMap().getStartPosition(team.getID()))
                    points.append([(startPos-playerPos).length(),startPos])
                points.sort()
                return points[-1][1]
            else:
                return None
        else:
            return None

    def spawnPlayer(self,player):
        """
        Spawn *something* for the provided bs.Player.
        The default implementation simply calls spawnPlayerSpaz().
        """
        #Overloaded for this game to respawn at home instead of random FFA spots
        if not player.exists():
            bs.printError('spawnPlayer() called for nonexistant player')
            return
        if player.gameData['home'] is None:
            pos = self.getMap().getFFAStartPosition(self.players)
            if player.gameData['crate'] is None:
                box = cargoBox(pos)
                box.setMovingText(box,player.getName(),player.color)
                player.gameData['crate'] = box
            position = [pos[0],pos[1]+1.0,pos[2]]
            player.gameData['home'] = position
        else:
            position = player.gameData['home']
        spaz = self.spawnPlayerSpaz(player, position)
        #Need to prevent accepting powerups:
        pam = bs.Powerup.getFactory().powerupAcceptMaterial
        for attr in ['materials','rollerMaterials','extrasMaterials']:
                        materials = getattr(spaz.node,attr)
                        if pam in materials:
                            setattr(spaz.node,attr,tuple(m for m in materials if m != pam))
        return spaz
        


    def _printLives(self,player):
        if not player.exists() or not player.isAlive(): return
        try: pos = player.actor.node.position
        except Exception,e:
            print 'EXC getting player pos in bsElim',e
            return
        bs.PopupText('x'+str(player.gameData['lives']-1),color=(1,1,0,1),
                           offset=(0,-0.8,0),randomOffset=0.0,scale=1.8,position=pos).autoRetain()

    def onPlayerLeave(self,player):

        bs.TeamGameActivity.onPlayerLeave(self,player)

        #player.gameData['icons'] = None
        player.gameData['score'] = 0
        if player.gameData['crate'].exists():
            player.gameData['crate'].handleMessage(bs.DieMessage(immediate=True))
        # remove us from spawn-order
        if self._soloMode:
            if player in player.getTeam().gameData['spawnOrder']:
                player.getTeam().gameData['spawnOrder'].remove(player)


    def onBegin(self):
        bs.TeamGameActivity.onBegin(self)
        self.setupStandardTimeLimit(self.settings['Time Limit'])
        #self.setupStandardPowerupDrops()

        if self._soloMode:
            self._vsText = bs.NodeActor(bs.newNode("text",
                                                   attrs={'position':(0,105),
                                                          'hAttach':"center",
                                                          'hAlign':'center',
                                                          'maxWidth':200,
                                                          'shadow':0.5,
                                                          'vrDepth':390,
                                                          'scale':0.6,
                                                          'vAttach':"bottom",
                                                          'color':(0.8,0.8,0.3,1.0),
                                                          'text':bs.Lstr(resource='vsText')}))

        # if balance-team-lives is on, add lives to the smaller team until total lives match
        if (isinstance(self.getSession(),bs.TeamsSession)
            and self.settings['Balance Total Lives']
            and len(self.teams[0].players) > 0
            and len(self.teams[1].players) > 0):
            if self._getTotalTeamLives(self.teams[0]) < self._getTotalTeamLives(self.teams[1]):
                lesserTeam = self.teams[0]
                greaterTeam = self.teams[1]
            else:
                lesserTeam = self.teams[1]
                greaterTeam = self.teams[0]
            addIndex = 0
            while self._getTotalTeamLives(lesserTeam) < self._getTotalTeamLives(greaterTeam):
                lesserTeam.players[addIndex].gameData['lives'] += 1
                addIndex = (addIndex + 1) % len(lesserTeam.players)

        #self._updateIcons()

        # we could check game-over conditions at explicit trigger points,
        # but lets just do the simple thing and poll it...
        bs.gameTimer(1000, self._update, repeat=True)
        
    def _getTotalTeamLives(self,team):
        return sum(player.gameData['lives'] for player in team.players)

    def handleMessage(self,m):
        if isinstance(m,bs.PlayerSpazDeathMessage):
            
            bs.TeamGameActivity.handleMessage(self, m) # augment standard behavior
            player = m.spaz.getPlayer()

            self.respawnPlayer(player)

            # in solo, put ourself at the back of the spawn order
            if self._soloMode:
                player.getTeam().gameData['spawnOrder'].remove(player)
                player.getTeam().gameData['spawnOrder'].append(player)
        else:
            bs.TeamGameActivity.handleMessage(self, m)
    def _update(self):

        if self._soloMode:
            # for both teams, find the first player on the spawn order list with lives remaining
            # and spawn them if they're not alive
            for team in self.teams:
                # prune dead players from the spawn order
                team.gameData['spawnOrder'] = [p for p in team.gameData['spawnOrder'] if p.exists()]
                for player in team.gameData['spawnOrder']:
                    if player.gameData['lives'] > 0:
                        if not player.isAlive():
                            self.spawnPlayer(player)
                            #self._updateIcons()
                        break
        
        # if we're down to 1 or fewer living teams, start a timer to end the game
        # (allows the dust to settle and draws to occur if deaths are close enough)
        self.boxSpawn()

    def boxSpawn(self):
        Plyrs = 0
        for team in self.teams:
            for player in team.players:
                Plyrs += 1
                    
        maxBoxes = int(Plyrs * self.settings["Boxes Per Player"])
        if maxBoxes > 16:
            maxBoxes = 16
        elif maxBoxes < 1:
            maxBoxes = 1
        for box in self.totBoxes:
            if not box.exists():
                self.totBoxes.remove(box)
        while len(self.totBoxes) < maxBoxes:
            #print([Plyrs, self.boxMult,len(self.totBoxes), maxBoxes])
            if random.randint(1,self.settings["Curse Box Chance (lower = more chance)"]) == 1:
                type = 'curse'
            else:
                type = 'health'
            box = bsPowerup.Powerup(position=self.getRandomPowerupPoint(), powerupType=type,expire=False).autoRetain()
            #we have to remove the default powerup material because it doesn't allow for pickups.
            #Then we add our own powerup material.
            pm = box.getFactory().powerupMaterial
            materials = getattr(box.node,'materials')
            if pm in materials:
                setattr(box.node,'materials',tuple(m for m in materials if m != pm))
            materials = getattr(box.node,'materials')
            if not self.fpowerupMaterial in materials:
                setattr(box.node,'materials',materials + (self.fpowerupMaterial,))
            self.totBoxes.append(box)
            
        #self.boxMult -= self.settings["Box Reduction Rate"]
        
    def getRandomPowerupPoint(self):
        myMap = self.getMap().getName()
        #print(myMap)
        if myMap == 'Doom Shroom':
            while True:
                x = random.uniform(-1.0,1.0)
                y = random.uniform(-1.0,1.0)
                if x*x+y*y < 1.0: break
            return ((5.0*x,4.0,-3.5+3.0*y))
        elif myMap == 'Courtyard':
            x = random.uniform(-3.3,3.3)
            y = random.uniform(-3.9,-0.2)
            return ((x, 4.0, y))
        else:
            x = random.uniform(-5.0,5.0)
            y = random.uniform(-6.0,0.0)
            return ((x, 8.0, y))
    def _getLivingTeams(self):
        return [team for team in self.teams if len(team.players) > 0 and any(player.gameData['lives'] > 0 for player in team.players)]
    def _updateScoreBoard(self):
        for team in self.teams:
            self._scoreBoard.setTeamValue(team, team.gameData['score'])
    def endGame(self):
        if self.hasEnded(): return
        results = bs.TeamGameResults()
        self._vsText = None # kill our 'vs' if its there
        for team in self.teams:
            results.setTeamScore(team, team.gameData['score'])
        self.end(results=results)
        
