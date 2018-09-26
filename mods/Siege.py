#Siege
import bs
import bsUtils
import random

def bsGetAPIVersion():
    return 4

def bsGetGames():
    return [Siege]

class SiegePowerupFactory(bs.PowerupFactory):
    def getRandomPowerupType(self,forceType=None,excludeTypes=['tripleBombs','iceBombs','impactBombs','shield','health','curse','snoball','bunny']):
        while True:
            t = self._powerupDist[random.randint(0,len(self._powerupDist)-1)]
            if t not in excludeTypes:
                break
        self._lastPowerupType = t
        return t

class Puck(bs.Actor): # Borrowed from the hockey game

    def __init__(self, position=(0,1,0)):
        bs.Actor.__init__(self)
        self.info = bs.NodeActor(bs.newNode('text',
                                                   attrs={'vAttach': 'bottom',
                                                          'hAlign': 'center',
                                                          'vrDepth': 0,
                                                          'color': (0,.2,0),
                                                          'shadow': 1.0,
                                                          'flatness': 1.0,
                                                          'position': (0,0),
                                                          'scale': 0.8,
                                                          'text': "Created by MattZ45986 on Github",
                                                          }))
        activity = self.getActivity()
        self._spawnPos = (position[0], position[1]+1.0, position[2])
        self.lastPlayersToTouch = {}
        self.node = bs.newNode("prop",
                               attrs={'model': bs.getModel('puck'),
                                      'colorTexture': bs.getTexture('puckColor'),
                                      'body':'puck',
                                      'reflection':'soft',
                                      'reflectionScale':[0.2],
                                      'shadowSize': 1.0,
                                      'gravityScale':2.5,
                                      'isAreaOfInterest':True,
                                      'position':self._spawnPos,
                                      'materials': [bs.getSharedObject('objectMaterial'),activity._puckMaterial]
                                      },
                               delegate=self)

class Siege(bs.TeamGameActivity):
    @classmethod
    def getName(cls):
        return "Siege"

    @classmethod
    def getDescription(cls, sessionType):
        return "Get the flag from the castle!"

    @classmethod
    def getScoreInfo(cls):
        return{'scoreType':'points'}

    @classmethod
    def getSupportedMaps(cls, sessionType):
        return ['Football Stadium']

    @classmethod
    def supportsSessionType(cls, sessionType):
        return True if issubclass(sessionType, bs.FreeForAllSession) or issubclass(sessionType, bs.TeamsSession) else False

    def __init__(self,settings):
        bs.TeamGameActivity.__init__(self,settings)
        self._puckMaterial = bs.Material()
        self._puckMaterial.addActions(actions=( ("modifyPartCollision","friction",100000)))
        self._puckMaterial.addActions(conditions=("theyHaveMaterial",bs.getSharedObject('pickupMaterial')),
                                      actions=( ("modifyPartCollision","collide",False)))
        self._puckMaterial.addActions(conditions=( ("weAreYoungerThan",100),'and',
                                                   ("theyHaveMaterial",bs.getSharedObject('objectMaterial')) ),
                                      actions=( ("modifyNodeCollision","collide",False)))
        self.pucks = []
        self.flag = bs.Flag(color=(1,1,1),
                                     position=(0,1,-2),
                                     touchable=True)
        
        
        
    def onTransitionIn(self):
        bs.TeamGameActivity.onTransitionIn(self,music='FlagCatcher')

    def _standardDropPowerup(self,index,expire=True):
        import bsPowerup
        bsPowerup.Powerup(position=self.getMap().powerupSpawnPoints[index],
                          powerupType=SiegePowerupFactory().getRandomPowerupType(),expire=expire).autoRetain()

    def onBegin(self):
        bs.TeamGameActivity.onBegin(self)
        self.setupStandardPowerupDrops(True)
        for j in range(0,12,3):
            for i in range(-6,4,3):
                self.pucks.append(Puck((3,j/4.0,i/2.0)))
                self.pucks.append(Puck((-3,j/4.0,i/2.0)))
            for i in range(-3,4,2):
                self.pucks.append(Puck((i/2.0,j/4.0,-3)))
                self.pucks.append(Puck((i/2.0,j/4.0,1.75)))
    def handleMessage(self,m):
        if isinstance(m,bs.FlagPickedUpMessage):
            winner = m.node.getDelegate()
            self.endGame(winner)
        elif isinstance(m,bs.PlayerSpazDeathMessage):
            self.respawnPlayer(m.spaz.getPlayer())
        else: bs.TeamGameActivity.handleMessage(self,m)

    def endGame(self, winner):
        results = bs.TeamGameResults()
        for team in self.teams:
            if winner.getPlayer() in team.players: score = 50
            else: score = 0
            results.setTeamScore(team,score)
        self.end(results=results,announceDelay=10)
