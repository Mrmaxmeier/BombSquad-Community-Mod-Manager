# Wizard War
# In light of the new "Grumbledorf" character
# I have made a war just for him.
import bs
import random
import math
import bsVector
import bsUtils

def bsGetAPIVersion():
    return 4

def bsGetGames():
    return [WizardWar]

def bsGetLevels():
    return [bs.Level('Wizard War',
                     displayName='${GAME}',
                     gameType=WizardWar,
                     settings={},
                     previewTexName='courtyardPreview')]

class ExplodeMessage(object):
    pass
class ArmMessage(object):
    pass
class WarnMessage(object):
    pass
class DieMessage(object):
    pass
class _BombDiedMessage(object):
    pass


# A special type of bomb that is cast from the player's body.
# It is shaped like an orb and is colored according to the player's team
class WWBomb(bs.Bomb):

    def __init__(self,position=(0,1,0),velocity=(0,0,0),bombType='normal',blastRadius=2,sourcePlayer=None,owner=None):
        if not sourcePlayer.isAlive(): return
        bs.Actor.__init__(self)
        factory = self.getFactory()
        if not bombType in ('ice','impact','landMine','normal','sticky','tnt'): raise Exception("invalid bomb type: " + bombType)
        self.bombType = bombType
        self._exploded = False
        self.blastRadius = blastRadius
        self._explodeCallbacks = []
        self.sourcePlayer = sourcePlayer
        self.hitType = 'explosion'
        self.hitSubType = self.bombType
        if owner is None: owner = bs.Node(None)
        self.owner = owner
        materials = (factory.bombMaterial, bs.getSharedObject('objectMaterial'))
        materials = materials + (factory.impactBlastMaterial,)
        players = self.getActivity().players
        i = 0
        # This gives each player a unique orb color, made possible by the powerup textures within the game.
        while players[i] != sourcePlayer:
            i+=1
        color = ("powerupIceBombs","powerupPunch","powerupStickyBombs","powerupBomb","powerupCurse","powerupHealth","powerupShield","powerupLandMines")[i]
        if isinstance(self.getActivity().getSession(), bs.TeamsSession): # unless we're on teams, so we'll overide the color to be the team's color
            if sourcePlayer in self.getActivity().teams[0].players:
                color = "powerupIceBombs" # for blue
            else:
                color = "powerupPunch" # for red
        self.node = bs.newNode('prop',
                                   delegate=self,
                                   attrs={'position':position,
                                          'velocity':velocity,
                                          'body':'sphere',
                                          'model':bs.getModel("shield"),
                                          'shadowSize':0.3,
                                          'density':1,
                                          'bodyScale':3,
                                          'colorTexture':bs.getTexture(color),
                                          'reflection':'soft',
                                          'reflectionScale':[1.5],
                                          'materials':materials})
        self.armTimer = bs.Timer(200,bs.WeakCall(self.handleMessage,ArmMessage()))
        self.node.addDeathAction(bs.WeakCall(self.handleMessage,_BombDiedMessage()))


        bsUtils.animate(self.node,"modelScale",{0:0, 200:1.3, 260:1})

    
    def _handleImpact(self,m):
        node,body = bs.getCollisionInfo("opposingNode","opposingBody")
        if node is None: return
        try: player = node.getDelegate().getPlayer()
        except Exception: player = None
        if self.getActivity().settings["Orbs Explode Other Orbs"]:
            if isinstance(node.getDelegate(),WWBomb) and node.getNodeType() == 'prop' and (node.getDelegate().sourcePlayer.getTeam() is not self.sourcePlayer.getTeam()):
                self.handleMessage(ExplodeMessage())
        if (player is not None) and (player.getTeam() is not self.sourcePlayer.getTeam()):
            self.handleMessage(ExplodeMessage())
                    
    def handleMessage(self, m):
        if isinstance(m, _BombDiedMessage):
            self.sourcePlayer.actor._orbNum -= 1
        elif isinstance(m, ExplodeMessage): self.explode()
        else:
            bs.Bomb.handleMessage(self,m)

class WWSpaz(bs.PlayerSpaz):
    def onPunchPress(self):
        self.getActivity().shootBomb(self)

class WizardWar(bs.TeamGameActivity):

    @classmethod
    def getName(cls):
        return "Wizard War"

    @classmethod
    def getDescription(cls, sessionType):
        return "Punch to summon magic orbs\nLast mage standing wins"

    @classmethod
    def getScoreInfo(cls):
        return{'scoreType':'points'}

    @classmethod
    def getSettings(cls, sessionType):
        return [("Epic Mode", {'default': False}),
                ("Enable Running", {'default': False}),
                ("Enable Jumping", {'default': False}),
                ("Enable Punching", {'default': False}),
                ("Enable Picking Up", {'default': False}),
                ("Orbs Explode Other Orbs", {'default':True}),
                ("Orb Limit", {
                    'choices': [
                        ('1 Orb', 1),
                        ('2 Orbs', 2),
                        ('3 Orbs', 3),
                        ('5 Orbs', 5),
                        ('Infinite', 300)
                    ],
                    'default': 3})]
    @classmethod
    def getSupportedMaps(cls, sessionType):
        return bs.getMapsSupportingPlayType('melee')

    @classmethod
    def supportsSessionType(cls, sessionType):
        return True if issubclass(sessionType, bs.FreeForAllSession) or issubclass(sessionType, bs.TeamsSession) else False

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
        bs.TeamGameActivity.onTransitionIn(self,music='ToTheDeath')
        

    def onBegin(self):
        bs.TeamGameActivity.onBegin(self)
        s = self.settings
        for player in self.players:
            player.actor.connectControlsToPlayer(enableBomb=False, enablePickUp = s["Enable Picking Up"], enableRun = s["Enable Running"], enableJump = s["Enable Jumping"])
            player.gameData['score'] = 0
            pos = player.actor.node.positionCenter
            t = bs.newNode('text',
                                 owner=player.actor.node,
                                 attrs={'text':player.getName(),
                                        'inWorld':True,
                                        'color':player.color,
                                        'scale':0.015,
                                        'hAlign':'center',
                                        'position':(pos)})
            l = bs.newNode('light',
                                 owner=player.actor.node,
                                 attrs={'color':player.color,
                                        'position':(pos),
                                        'intensity':0.5})
            bs.gameTimer(2000,l.delete)
            bs.gameTimer(2000,t.delete)


    def onPlayerJoin(self, player):
        if self.hasBegun():
            bs.screenMessage(bs.Lstr(resource='playerDelayedJoinText',subs=[('${PLAYER}',player.getName(full=True))]),color=(0,1,0))
            self.checkEnd()
            return
        else:
            self.spawnPlayerSpaz(player)
    
    def spawnPlayerSpaz(self,player,position=(0,5,-3),angle=None):
        name = player.getName()
        color = player.color
        highlight = player.highlight
        players = self.players
        i = 0
        position = self.getMap().getFFAStartPosition(self.players)
        angle = 0
        spaz = WWSpaz(color=color,
                             highlight=highlight,
                             character="Grumbledorf",
                             player=player)
        player.setActor(spaz)
        spaz.handleMessage(bs.StandMessage(position,angle))
        spaz._orbNum = 0
    def shootBomb(self, spaz):
        if spaz._orbNum >= self.settings["Orb Limit"]: return
        spaz._orbNum += 1
        try: spaz.node.handleMessage('celebrate',100)
        except Exception: pass
        cen = spaz.node.positionCenter
        frw = spaz.node.positionForward
        direction = [cen[0]-frw[0],frw[1]-cen[1],cen[2]-frw[2]]
        direction[1] *= .03 
        mag = 20.0/bsVector.Vector(*direction).length()
        vel = [v * mag for v in direction]
        WWBomb(position=(spaz.node.position[0],spaz.node.position[1]+1,spaz.node.position[2]), velocity=vel, sourcePlayer = spaz.getPlayer(), bombType = 'impact').autoRetain()

    def handleMessage(self, m):
        if isinstance(m, bs.PlayerSpazDeathMessage):
            bs.TeamGameActivity.handleMessage(self,m)
            bs.gameTimer(1000,bs.Call(self.checkEnd))
            m.spaz.getPlayer().actor.disconnectControlsFromPlayer()
            if m.how == "fall": pts = 10
            elif m.how == "impact": pts = 50
            else: pts = 0
            self.scoreSet.playerScored(m.killerPlayer,pts,screenMessage=False)
            bs.screenMessage(str(m.spaz.getPlayer().getName()) + " died!", m.spaz.getPlayer().color, top=True)

    def checkEnd(self):
        if isinstance(self.getSession(), bs.FreeForAllSession):
            i = 0
            for player in self.players:
                if player.isAlive():
                    i += 1
            if i <= 1:
                self.endGame()
        if isinstance(self.getSession(), bs.TeamsSession):
            for team in self.teams:
                i=0
                team.gameData['score'] = 1
                for player in team.players:
                    if player.isAlive():
                        i += 1
                if i == 0:
                    team.gameData['score'] -= 1
            for team in self.teams:
                if team.gameData['score'] == 0:
                    self.endGame()
                        
                        

    def endGame(self):
        if isinstance(self.getSession(), bs.FreeForAllSession):
            for player in self.players:
                if player.isAlive():
                    player.gameData['score'] = 1
                else:
                    player.gameData['score'] = 0
            results = bs.TeamGameResults()
            for team in self.teams:
                for player in team.players:
                    if player.isAlive():
                        results.setTeamScore(team, 5)
                        break
                    else:
                        results.setTeamScore(team, 0)
        else:
            results = bs.TeamGameResults()
            for team in self.teams:
                results.setTeamScore(team, 0)
                for player in team.players:
                    if player.isAlive():
                        team.gameData['score'] = 1
                        results.setTeamScore(team, 10)
        self.end(results=results)

