#Musical Flags

import bs
from random import randint
import math
import bsVector
import bsUtils
from math import sin, cos, degrees

def bsGetAPIVersion():
    return 4

def bsGetGames():
    return [MusicalFlags]

def bsGetLevels():
    return [bs.Level('Musical Flags',
                     displayName='${GAME}',
                     gameType=MusicalFlags,
                     settings={},
                     previewTexName='courtyardPreview')]

class MusicalFlags(bs.TeamGameActivity):

    tips = ['Though it seems that the flags to the sides are closer,\nthey are all the same distance from you.',
            'You can always pick up your opponent to keep them from scoring.',
            'If a player leaves, there would be enough flags for everyone\nso the next round starts automatically.',
            'RUN!',
            'If you accidentally run off a cliff, no worries.\nYou respawn!']
    
    @classmethod
    def getName(cls):
        return "Musical Flags"

    @classmethod
    def getDescription(cls, sessionType):
        return "Don't be the one stuck without a flag!"

    @classmethod
    def getScoreInfo(cls):
        return{'scoreType':'points'}

    @classmethod
    def getSettings(cls, sessionType):
        return [("Epic Mode", {'default': False}),
                ("Enable Running", {'default': True}),
                ("Enable Punching", {'default': True}),
                ("Time Limit", {
                    'choices': [
                        ("30 Seconds", 30),
                        ("1 Minute", 60),
                        ("2 Minutes", 120),
                        ("3 Minutes", 180)
                        ],
                    'default': 60})]
    
    @classmethod
    def getSupportedMaps(cls, sessionType):
        return ['Doom Shroom']

    @classmethod
    def supportsSessionType(cls, sessionType):
        return True if issubclass(sessionType, bs.FreeForAllSession) else False

    def __init__(self,settings):
        bs.TeamGameActivity.__init__(self,settings)
        if self.settings['Epic Mode']: self._isSlowMotion = True
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

    def onTransitionIn(self):
        bs.TeamGameActivity.onTransitionIn(self,music='FlagCatcher')

    def onBegin(self):
        self.timer = bs.OnScreenCountdown(self.settings['Time Limit'], endCall=self.endGame)
        self.timer.start()
        self.joined = []
        self.ended = False
        self.roundNumber = 1
        self.nodes = []
        self.flags = []
        self.leftPlayers = 0
        self.scores = {}
        for player in self.players:
            self.scores[player] = 0
        self.survived = self.players
        bs.TeamGameActivity.onBegin(self)
        self.makeRound()
        
    def onPlayerJoin(self,player):
        if self.hasBegun():
            bs.screenMessage(bs.Lstr(resource='playerDelayedJoinText',subs=[('${PLAYER}',player.getName(full=True))]),color=(0,1,0))
            self.joined.append(player)
            self.checkEnd()

    def onPlayerLeave(self,player):
        message = str(player.getName(icon=False)) + " has chickened out!"
        bs.screenMessage(message, color=player.color)
        player.actor.handleMessage(bs.DieMessage())
        self.leftPlayers += 1
        if len(self.players) == 1: self.endGame()
        else: self.endRoundFromLeave()

    def makeRound(self):
        angle = randint(0,359)
        try: spacing = 360 // len(self.survived)-1
        except: return
        colors = [(1,0,0),(0,1,0),(0,0,1),(1,1,0),(1,0,1),(0,1,1),(0,0,0)]
        for i in range(len(self.survived)-1):
            angle += spacing
            angle %= 360
            x=6 * sin(degrees(angle))
            z=6 * cos(degrees(angle))
            flag = bs.Flag(position=(x+.5,5,z-4), color=colors[i]).autoRetain()
            self.flags.append(flag)
        
        for player in self.survived:
            self.spawnPlayerSpaz(player,(.5,5,-4))
        self.survived = []
        
    def killRound(self):
        deadGuy = list((set(self.players) - set(self.survived)))[0]
        if deadGuy not in self.joined:
            deadGuy.actor.handleMessage(bs.FreezeMessage())
            deadGuy.actor.handleMessage(bs.ShouldShatterMessage())
        for i in self.nodes:
            i.delete()
            
    def spawnPlayerSpaz(self,player,position=(.5,5,-4),angle=0):
        s = self.settings
        name = player.getName()
        color = player.color
        highlight = player.highlight
        players = self.players
        num = len(players)
        i = 0
        position = (.5,5,-4)
        angle = 0
        spaz = bs.PlayerSpaz(color=color,
                             highlight=highlight,
                             character=player.character,
                             player=player)
        player.setActor(spaz)
        spaz.connectControlsToPlayer(enableBomb=False, enableRun=s["Enable Running"], enablePunch=s["Enable Punching"])
        spaz.handleMessage(bs.StandMessage(position,angle))
        
    def handleMessage(self, m):
        if isinstance(m, bs.FlagPickedUpMessage):
            self.survived.append(m.node.getDelegate().getPlayer())
            l = bs.newNode('light',
                                 owner=m.node,
                                 attrs={'color':m.node.color,
                                        'position':(m.node.positionCenter),
                                        'intensity':1})
            self.nodes.append(l)
            m.flag.handleMessage(bs.DieMessage())
            m.node.handleMessage(bs.DieMessage())
            
        if isinstance(m, bs.PlayerSpazDeathMessage):
            self.scores[m.spaz.getPlayer()] = self.roundNumber
            if not self.roundOver(): self.spawnPlayerSpaz(m.spaz.getPlayer(),(.5,5,-4))
            if not self.ended: bs.gameTimer(1000,bs.Call(self.checkEnd))
    def checkEnd(self):
        i = 0
        for player in self.players:
            if player.isAlive():
                i+=1
        if i < 2:
            self.roundNumber += 1
            self.killRound()
            if self.roundNumber == len(self.players) + self.leftPlayers: self.endGame()
            else: self.makeRound()
            
    def roundOver(self):
        if (len(self.survived) == len(self.players) - 1): return True
        else: return False
        
    def endRoundFromLeave(self):
        for player in self.players:
            if player.isAlive():
                self.survived.append(player)
                player.handleMessage(bs.DieMessage())
        for i in self.nodes:
            i.delete()
        for flag in self.flags:
            flag.handleMessage(bs.DieMessage())
        self.makeRound()
        
    def endGame(self):
        self.ended = True
        if isinstance(self.getSession(), bs.FreeForAllSession):
            for player in self.players:
                if player in self.survived:
                    player.gameData['score'] = 1
                else:
                    player.gameData['score'] = 0
            results = bs.TeamGameResults()
            for team in self.teams:
                for player in team.players:
                    if player not in self.joined: results.setTeamScore(team, self.scores[player] * 2)
        self.end(results=results)
        for i in self.nodes:
            i.delete()
        for flag in self.flags:
            flag.handleMessage(bs.DieMessage())
