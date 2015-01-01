#ModManager#{"name": "Puck Deathmatch", "author": "Mrmaxmeier", "dependencies": []}#ModManager# <-- json stuff for the modmanager


import bs
import random

class PuckTouchedMessage(object):
    pass


class Puck(bs.Actor):

    def __init__(self,position=(0,1,0), teamID = 0):
        bs.Actor.__init__(self)

        self.teamID = teamID
        activity = self.getActivity()
        
        # spawn just above the provided point
        self._spawnPos = (position[0],position[1]+1.0,position[2])
        self.lastPlayersToTouch = {}
        self.node = bs.newNode("prop",
                               attrs={'model': activity._puckModel,
                                      'colorTexture': activity._puckTex,
                                      'body':'puck',
                                      'reflection':'soft',
                                      'reflectionScale':[0.2],
                                      'shadowSize': 1.0,
                                      'isAreaOfInterest':True,
                                      'position':self._spawnPos,
                                      'materials': [bs.getSharedObject('objectMaterial'),activity._puckMaterial]
                                      },
                               delegate=self)

    def handleMessage(self,m):
        if isinstance(m, PuckTouchedMessage):
            node = bs.getCollisionInfo("opposingNode")
            #bs.screenMessage(str(node.position))
            #node.sourcePlayer
            tID = node.sourcePlayer.getTeam().getID()
            if (tID == self.teamID): return


            #Score - isAlive to avoid multiple kills per death
            if 'notKilled' not in node.sourcePlayer.gameData:
                node.sourcePlayer.gameData['notKilled'] = True
            if node.sourcePlayer.gameData['notKilled']:
                node.sourcePlayer.getTeam().gameData['timesKilled'] += 1
                bs.getActivity()._updateScoreBoard()
            node.sourcePlayer.gameData['notKilled'] = False

            x, y, z = node.position
            node.handleMessage("impulse", x, y, z,
                            0, 0, 0, #velocity
                            1000.0, 0, 3, 0,
                            0, 0, 0) # forceDirection
            node.frozen = True
            bs.gameTimer(1000, node.sourcePlayer.actor.shatter)


        if isinstance(m,bs.DieMessage):
            self.node.delete()
            activity = self._activity()
            if activity and not m.immediate:
                activity.handleMessage(PuckDeathMessage(self))

        # if we go out of bounds, move back to where we started...
        elif isinstance(m,bs.OutOfBoundsMessage):
            self.node.position = self._spawnPos

        elif isinstance(m,bs.HitMessage):
            #print(m.pos, m.velocity, m.magnitude, m.velocityMagnitude, m.radius, m.forceDirection)
            self.node.handleMessage("impulse",m.pos[0],m.pos[1],m.pos[2],
                                    m.velocity[0],m.velocity[1],m.velocity[2],
                                    1.0*m.magnitude,1.0*m.velocityMagnitude,m.radius,0,
                                    m.forceDirection[0],m.forceDirection[1],m.forceDirection[2])

            # if this hit came from a player, log them as the last to touch us
            if m.sourcePlayer is not None:
                activity = self._activity()
                if activity:
                    if m.sourcePlayer in activity.players:
                        self.lastPlayersToTouch[m.sourcePlayer.getTeam().getID()] = m.sourcePlayer
        else:
            bs.Actor.handleMessage(self,m)

def bsGetAPIVersion():
    # return the api-version this script expects.
    # this prevents it from attempting to run in newer versions of the game
    # where changes have been made to the modding APIs
    return 3

def bsGetGames():
    return [PuckDeathMatch]

def bsGetLevels():
    # Levels are unique named instances of a particular game with particular settings.
    # They show up as buttons in the co-op section, get high-score lists associated with them, etc.
    return [bs.Level('Machete mit Reis V0', # globally-unique name for this level (not seen by user)
                     displayName='${GAME}', # ${GAME} will be replaced by the results of the game's getName() call
                     gameType=PuckDeathMatch,
                     settings={}, # we currently dont have any settings; we'd specify them here if we did.
                     previewTexName='courtyardPreview')]


class PuckDeathMatch(bs.TeamGameActivity):

    def getPlayer0(self):
        return self.players[0]

    # name seen by the user
    @classmethod
    def getName(cls):
        return 'Puck Deathmatch'
    
    @classmethod
    def getScoreInfo(cls):
        return {'scoreType':'milliseconds',
                'lowerIsBetter':True,
                'scoreName':'Time'}
    
    @classmethod
    def getDescription(cls,sessionType):
        return 'Kill everyone with your Puck'
    
    @classmethod
    def getSupportedMaps(cls,sessionType):
        # for now we're hard-coding spawn positions and whatnot
        # so we need to be sure to specity that we only support
        # a specific map..
        return ['Lake Frigid', 'Rampage', 'Hockey']

    @classmethod
    def supportsSessionType(cls,sessionType):
        # we currently support Teamsession only
        return True if issubclass(sessionType,bs.TeamsSession) else False

    # in the constructor we should load any media we need/etc.
    # but not actually create anything yet.
    def __init__(self,settings):
        bs.TeamGameActivity.__init__(self,settings)
        self._winSound = bs.getSound("score")

        self._cheerSound = bs.getSound("cheer")
        self._chantSound = bs.getSound("crowdChant")
        self._foghornSound = bs.getSound("foghorn")
        self._swipSound = bs.getSound("swip")
        self._whistleSound = bs.getSound("refWhistle")
        self._puckModel = bs.getModel("puck")
        self._puckTex = bs.getTexture("puckColor")
        self._puckSound = bs.getSound("metalHit")

        self._puckMaterial = bs.Material()
        self._puckMaterial.addActions(actions=( ("modifyPartCollision","friction",0.1)))
        self._puckMaterial.addActions(conditions=("theyHaveMaterial",bs.getSharedObject('pickupMaterial')),
                                      actions=( ("modifyPartCollision","collide",False) ) )
        self._puckMaterial.addActions(conditions=( ("weAreYoungerThan",100),'and',
                                                   ("theyHaveMaterial",bs.getSharedObject('objectMaterial')) ),
                                      actions=( ("modifyNodeCollision","collide",False) ) )
        self._puckMaterial.addActions(conditions=("theyHaveMaterial",bs.getSharedObject('footingMaterial')),
                                      actions=(("impactSound",self._puckSound,0.2,5)))
        # keep track of which player last touched the puck
        self._puckMaterial.addActions(conditions=("theyHaveMaterial",bs.getSharedObject('playerMaterial')),
                                      actions=(("call","atConnect",self._handlePuckPlayerCollide),))

        # we want the puck to kill powerups; not get stopped by them
        self._puckMaterial.addActions(conditions=("theyHaveMaterial",bs.Powerup.getFactory().powerupMaterial),
                                      actions=(("modifyPartCollision","physical",False),
                                               ("message","theirNode","atConnect",bs.DieMessage())))



        # dis is kill
        self._puckMaterial.addActions(conditions=("theyHaveMaterial",bs.getSharedObject('playerMaterial')),
                                      actions=(("modifyPartCollision","physical",False),
                                               ("message", "ourNode", "atConnect", PuckTouchedMessage())))


        self._scoreBoard = bs.ScoreBoard()
        self._killsToWin = 5
        self._scoreSound = bs.getSound("score")
        

    # called when our game is transitioning in but not ready to start..
    # ..we can go ahead and start creating stuff, playing music, etc.
    def onTransitionIn(self):
        bs.TeamGameActivity.onTransitionIn(self, music='ToTheDeath')

    # called when our game actually starts
    def onBegin(self):
        bs.TeamGameActivity.onBegin(self)

        self._won = False
        for team in self.teams:
            team.gameData['timesKilled'] = 0
        self._updateScoreBoard()
        self.pucks = []
        self._spawnPuck(0)
        self._spawnPuck(1)
        
        self.setupStandardPowerupDrops()
        
        self._timer = bs.OnScreenTimer()
        bs.gameTimer(4000,self._timer.start)

    # called for each spawning player
    def spawnPlayer(self,player):
        # lets spawn close to the center
        #spawnCenter = (1,4,0)
        #pos = (spawnCenter[0]+random.uniform(-1.5,1.5),spawnCenter[1],spawnCenter[2]+random.uniform(-1.5,1.5))
        pos = self.getMap().getStartPosition(player.getTeam().getID())
        spaz = self.spawnPlayerSpaz(player,position=pos)

        spaz.connectControlsToPlayer(enablePunch=True,
                                     enableBomb=False,
                                     enablePickUp=True)
        player.gameData['notKilled'] = True

    def _flashPuckSpawn(self, pos):
        light = bs.newNode('light',
                           attrs={'position': pos,
                                  'heightAttenuated':False,
                                  'color': (1,0,0)})
        bs.animate(light,'intensity',{0:0,250:1,500:0},loop=True)
        bs.gameTimer(1000,light.delete)

    def _spawnPuck(self, teamID):
        #puckPos = (3, 5, 0) if teamID else (-3, 5, 0)

        puckPos = self.getMap().getStartPosition(teamID)
        #voher 0.3, 0.0, 1.0
        lightcolor = (1, 0, 0) if teamID else (0, 0, 1)
        bs.playSound(self._swipSound)
        bs.playSound(self._whistleSound)
        self._flashPuckSpawn(puckPos)

        puck = Puck(position=puckPos, teamID=teamID)
        puck.scored = False
        puck.lastHoldingPlayer = None
        puck.light = bs.newNode('light',
                                      owner=puck.node,
                                      attrs={'intensity':0.3,
                                             'heightAttenuated':False,
                                             'radius':0.2,
                                             'color': lightcolor})
        puck.node.connectAttr('position',puck.light,'position')
        self.pucks.append(puck)

    def _handlePuckPlayerCollide(self):
        try:
            puckNode,playerNode = bs.getCollisionInfo('sourceNode','opposingNode')
            puck = puckNode.getDelegate()
            player = playerNode.getDelegate().getPlayer()
        except Exception: player = puck = None

        if player is not None and player.exists() and puck is not None: puck.lastPlayersToTouch[player.getTeam().getID()] = player


    def _checkIfWon(self):
        # simply end the game if there's no living bots..
        for team in self.teams:
            if team.gameData['timesKilled'] >= self._killsToWin:
                self._won = True
                self.endGame()

    def _updateScoreBoard(self):
        for i, team in enumerate(self.teams):
            otherTeam = self.teams[i-1]
            team.gameData['score'] = otherTeam.gameData['timesKilled']
            self._scoreBoard.setTeamValue(team,team.gameData['score'],self._killsToWin)
        self._checkIfWon()



    # called for miscellaneous events
    def handleMessage(self,m):
        print(m)
        # a player has died
        if isinstance(m,bs.PlayerSpazDeathMessage):
            bs.TeamGameActivity.handleMessage(self,m) # do standard stuff
            self.respawnPlayer(m.spaz.getPlayer()) # kick off a respawn
            
        else:
            # let the base class handle anything we don't..
            bs.TeamGameActivity.handleMessage(self,m)
            
    # when this is called, we should fill out results and end the game
    # *regardless* of whether is has been won. (this may be called due
    # to a tournament ending or other external reason)
    def endGame(self):

        # stop our on-screen timer so players can see what they got
        self._timer.stop()
        results = bs.TeamGameResults()
        for t in self.teams: results.setTeamScore(t,t.gameData['score'])
        self.end(results=results)
