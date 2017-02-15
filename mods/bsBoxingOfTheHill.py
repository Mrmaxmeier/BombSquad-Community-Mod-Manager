import bs
import weakref

def bsGetAPIVersion():
    # see bombsquadgame.com/apichanges
    return 4

def bsGetGames():
    return [BoxingOfTheHillGame]

class BoxingOfTheHillGame(bs.TeamGameActivity):

    FLAG_NEW = 0
    FLAG_UNCONTESTED = 1
    FLAG_CONTESTED = 2
    FLAG_HELD = 3

    @classmethod
    def getName(cls):
        return 'Boxing of the Hill'

    @classmethod
    def getDescription(cls,sessionType):
        return 'Secure the flag for a set length of time. Gloves only!'

    @classmethod
    def getScoreInfo(cls):
        return {'scoreName':'Time Held'}
    
    @classmethod
    def supportsSessionType(cls,sessionType):
        return True if (issubclass(sessionType,bs.TeamsSession)
                        or issubclass(sessionType,bs.FreeForAllSession)) else False

    @classmethod
    def getSupportedMaps(cls,sessionType):
        return bs.getMapsSupportingPlayType("kingOfTheHill")

    @classmethod
    def getSettings(cls,sessionType):
        return [("Hold Time",{'minValue':10,'default':30,'increment':10}),
                ("Time Limit",{'choices':[('None',0),('1 Minute',60),
                                        ('2 Minutes',120),('5 Minutes',300),
                                        ('10 Minutes',600),('20 Minutes',1200)],'default':0}),
                ("Respawn Times",{'choices':[('Shorter',0.25),('Short',0.5),('Normal',1.0),('Long',2.0),('Longer',4.0)],'default':1.0})]

    def __init__(self,settings):
        bs.TeamGameActivity.__init__(self,settings)
        self._scoreBoard = bs.ScoreBoard()
        self._swipSound = bs.getSound("swip")
        self._tickSound = bs.getSound('tick')
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

        self._flagRegionMaterial = bs.Material()
        self._flagRegionMaterial.addActions(conditions=("theyHaveMaterial",bs.getSharedObject('playerMaterial')),
                                            actions=(("modifyPartCollision","collide",True),
                                                     ("modifyPartCollision","physical",False),
                                                     ("call","atConnect",bs.Call(self._handlePlayerFlagRegionCollide,1)),
                                                     ("call","atDisconnect",bs.Call(self._handlePlayerFlagRegionCollide,0))))

    def getInstanceDescription(self):
        return ('Secure the flag for ${ARG1} seconds.',self.settings['Hold Time'])

    def getInstanceScoreBoardDescription(self):
        return ('secure the flag for ${ARG1} seconds',self.settings['Hold Time'])

    def onTransitionIn(self):
        bs.TeamGameActivity.onTransitionIn(self, music='Scary')

    def onTeamJoin(self,team):
        team.gameData['timeRemaining'] = self.settings["Hold Time"]
        self._updateScoreBoard()

    def onPlayerJoin(self,player):
        bs.TeamGameActivity.onPlayerJoin(self,player)
        player.gameData['atFlag'] = 0

    def onBegin(self):
        bs.TeamGameActivity.onBegin(self)
        self.setupStandardTimeLimit(self.settings['Time Limit'])
        # self.setupStandardPowerupDrops() #no powerups due to boxing
        self._flagPos = self.getMap().getFlagPosition(None)
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

    def spawnPlayer(self,player):

        spaz = self.spawnPlayerSpaz(player)
        spaz.connectControlsToPlayer(enablePunch=True,
                                     enableBomb=False,
                                     enablePickUp=True)

        spaz.equipBoxingGloves()

    

    def _tick(self):
        self._updateFlagState()

        # give holding players points
        for player in self.players:
            if player.gameData['atFlag'] > 0:
                self.scoreSet.playerScored(player,3,screenMessage=False,display=False)

        scoringTeam = None if self._scoringTeam is None else self._scoringTeam()
        if scoringTeam:

            if scoringTeam.gameData['timeRemaining'] > 0: bs.playSound(self._tickSound)

            scoringTeam.gameData['timeRemaining'] = max(0,scoringTeam.gameData['timeRemaining']-1)
            self._updateScoreBoard()
            if scoringTeam.gameData['timeRemaining'] > 0:
                self._flag.setScoreText(str(scoringTeam.gameData['timeRemaining']))

            # announce numbers we have sounds for
            try: bs.playSound(self._countDownSounds[scoringTeam.gameData['timeRemaining']])
            except Exception: pass

            # winner
            if scoringTeam.gameData['timeRemaining'] <= 0:
                self.endGame()

    def endGame(self):
        results = bs.TeamGameResults()
        for team in self.teams: results.setTeamScore(team,self.settings['Hold Time'] - team.gameData['timeRemaining'])
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
            self._scoreBoard.setTeamValue(team,team.gameData['timeRemaining'],self.settings['Hold Time'],countdown=True)

    def handleMessage(self,m):
        if isinstance(m,bs.PlayerSpazDeathMessage):
            bs.TeamGameActivity.handleMessage(self,m) # augment default
            
            # no longer can count as atFlag once dead
            player = m.spaz.getPlayer()
            player.gameData['atFlag'] = 0
            self._updateFlagState()
            self.respawnPlayer(player)