#SharksAndMinnows

import bs
import bsUtils
import random

def bsGetAPIVersion():
    return 4

def bsGetGames():
    return [SharksAndMinnows]

class Minnow(bs.PlayerSpaz):
    isShark = False
    nextZone = 2
    def handleMessage(self, m):
        if isinstance(m, bs.PickedUpMessage):
            self.disconnectControlsFromPlayer()
            self.node.delete()
            self.getActivity().sharkify(self.getPlayer())
        bs.PlayerSpaz.handleMessage(self, m)

class Shark(bs.PlayerSpaz):
    isShark = True
    def handleMessage(self, m):
        if isinstance(m, bs.PickUpMessage):
            if not m.node.getDelegate().isShark:
                if self.getPlayer().getTeam() is m.node.getDelegate().getPlayer().getTeam(): points = 5
                else: points = 20
                self.getPlayer().getTeam().gameData['score'] += points
                self.getActivity().scoreSet.playerScored(self.getPlayer(),20,screenMessage=False,display=False)
                self.getActivity().updateScore()
        bs.PlayerSpaz.handleMessage(self, m)

class SharksAndMinnows(bs.TeamGameActivity):
    
    @classmethod
    def getName(cls):
        return "Sharks and Minnows"

    @classmethod
    def getDescription(cls, sessionType):
        return "Eat or be eaten."

    @classmethod
    def getScoreInfo(cls):
        return{'scoreType':'points'}

    @classmethod
    def getSupportedMaps(cls, sessionType):
        return ['Football Stadium']

    @classmethod
    def supportsSessionType(cls, sessionType):
        return True if issubclass(sessionType, bs.FreeForAllSession) or issubclass(sessionType, bs.TeamsSession)else False

    def __init__(self,settings):
        bs.TeamGameActivity.__init__(self,settings)
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
        self._safeZoneMaterial = bs.Material()
        self._scoredis = bs.ScoreBoard()
        self._safeZoneMaterial.addActions(conditions=("theyHaveMaterial",bs.getSharedObject('playerMaterial')),
                                            actions=(("modifyPartCollision","collide",True),
                                                     ("modifyPartCollision","physical",False),
                                                     ("call","atConnect",bs.Call(self.handleSafeZoneEnter))))
        self.safeZone1 = bs.newNode('region',
                   attrs={'position':(-11,0,0),
                          'scale': (1.8,1.8,1.8),
                          'type': 'sphere',
                          'materials':[self._safeZoneMaterial,bs.getSharedObject('regionMaterial')]})
        self.safeZone2 = bs.newNode('region',
                   attrs={'position':(11,0,0),
                          'scale': (1.8,1.8,1.8),
                          'type': 'sphere',
                          'materials':[self._safeZoneMaterial,bs.getSharedObject('regionMaterial')]})
        self.zoneLocator1 = bs.newNode('locator',attrs={'shape':'circle','position':(-11,0,0),
                                         'color':(1,1,1),'opacity':1,
                                         'drawBeauty':True,'additive':True})
        bs.animateArray(self.zoneLocator1,'size',1,{0:[0.0],200:[1.8*2.0]})
        self.zoneLocator2 = bs.newNode('locator',attrs={'shape':'circle','position':(11,0,0),
                                         'color':(1,1,1),'opacity':1,
                                         'drawBeauty':True,'additive':True})
        bs.animateArray(self.zoneLocator2,'size',1,{0:[0.0],200:[1.8*2.0]})
        
    def getInstanceScoreBoardDescription(self):
        return ('Sharks pick up minnows to score')
        
    def onTransitionIn(self):
        bs.TeamGameActivity.onTransitionIn(self,music='FlagCatcher')

    def onBegin(self):
        bs.TeamGameActivity.onBegin(self)
        for team in self.teams:
            team.gameData['score'] = 0
        teamNum = random.randint(0,len(self.teams)-1)
        for player in self.players:
            if player in self.teams[teamNum].players:
                bs.gameTimer(100, bs.Call(self.setupSharks, player=player))
            else:
                self.spawnPlayerSpaz(player)
        self.setupStandardPowerupDrops(True)
        for team in self.teams:
            self._scoredis.setTeamValue(team,team.gameData['score'])

    def setupSharks(self, player):
        self.sharkify(player)

    def respawnPlayer(self, player):
        if player.actor.node.getDelegate().isShark:
            self.sharkify(player)
            return
        else: bs.TeamGameActivity.respawnPlayer(self,player)
        
    def spawnPlayerSpaz(self,player,position=(-10,1,0),angle=None):
        try:
            if player.actor.node.getDelegate().isShark:
                self.sharkify(player)
                return
        except:
            pass
        name = player.getName()
        color = player.color
        highlight = player.highlight
        spaz = Minnow(color=color,
                             highlight=highlight,
                             character=player.character,
                             player=player)
        player.setActor(spaz)
        pos = [0,1,0]
        pos[0] = position[0] + random.random() * 2 * (-1)**random.randint(0,1)
        pos[2] = position[2] + random.random() * 2 * (-1)**random.randint(0,1)
        player.actor.connectControlsToPlayer(enableBomb=True, enableRun = True, enableJump = True, enablePickUp = False, enablePunch=True)
        spaz.handleMessage(bs.StandMessage(pos,90))

    def sharkify(self, player):
        name = player.getName()
        color = (0,0,0)
        highlight = player.getTeam().color
        spaz = Shark(color=color,
                             highlight=highlight,
                             character=player.character,
                             player=player)
        if player.actor is not None: player.actor.node.delete()
        player.setActor(spaz)
        pos = [0,.5,-5+(random.random()*10)]
        player.actor.connectControlsToPlayer(enableBomb=False, enableRun = True, enableJump = False, enablePickUp = True,enablePunch = False)
        spaz.handleMessage(bs.StandMessage(pos,90))
        self.checkEnd()

    def onPlayerJoin(self, player):
        if self.hasBegun():
            bs.screenMessage(bs.Lstr(resource='playerDelayedJoinText',subs=[('${PLAYER}',player.getName(full=True))]),color=(0,1,0))
            return

    def updateScore(self):
        for team in self.teams:
            self._scoredis.setTeamValue(team,team.gameData['score'])

    def handleSafeZoneEnter(self):
        self.checkEnd()
        zoneNode,playerNode = bs.getCollisionInfo("sourceNode","opposingNode")
        try: player = playerNode.getDelegate().getPlayer()
        except Exception: return
        if player.isAlive() and player.actor.node.getDelegate().isShark:
            player.actor.handleMessage(bs.DieMessage())
            self.sharkify(player)
        elif player.isAlive() and not player.actor.node.getDelegate().isShark:
            if player.actor.node.positionCenter[0] < 0 and player.actor.node.getDelegate().nextZone == 1:
                player.getTeam().gameData['score'] += 10
                self.scoreSet.playerScored(player,10,screenMessage=False,display=False)
                self.updateScore()
                player.actor.node.getDelegate().nextZone = 2
            elif player.actor.node.positionCenter[0] > 0 and player.actor.node.getDelegate().nextZone == 2:
                player.getTeam().gameData['score'] += 10
                self.scoreSet.playerScored(player,10,screenMessage=False,display=False)
                self.updateScore()
                player.actor.node.getDelegate().nextZone = 1

    def handleMessage(self,m):
        if isinstance(m, bs.PlayerSpazDeathMessage):
            bs.TeamGameActivity.handleMessage(self,m)
            bs.gameTimer(3100, self.checkEnd)
            if not m.spaz.isShark:
                self.respawnPlayer(m.spaz.getPlayer())
        else: bs.TeamGameActivity.handleMessage(self, m)

    def checkEnd(self):
        if bs.getGameTime() < 5000: return
        count = 0
        for player in self.players:
            if player.isAlive() and player.actor.node.getDelegate().isShark:
                count += 1
        if count < 1: self.endGame()
        count = 0
        for player in self.players:
            if player.isAlive(): count += 1
        if count < 2: self.endGame()
        count = 0
        for player in self.players:
            if player.isAlive() and player.actor.node.getDelegate().isShark == False:
                count += 1
        if count < 1: self.endGame()
        for team in self.teams:
            if team.gameData['score'] >= 300:
                self.endGame()

    def endGame(self):
        results = bs.TeamGameResults()
        for team in self.teams:
            score = team.gameData['score']
            results.setTeamScore(team,score)
        self.end(results=results,announceDelay=10)
