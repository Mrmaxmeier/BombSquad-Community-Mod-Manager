#Plague
import bs
import bsUtils

def bsGetAPIVersion():
    return 4

def bsGetGames():
    return [Plague]

class PlagueMessage(object):
    pass
class _BombDiedMessage(object):
    pass
class PlagueSpazDeathMessage(object):
    pass


class PlagueBomb(bs.Bomb):
    def __init__(self,position=(0,1,0),velocity=(0,0,0),bombType='plague',blastRadius=2.0,sourcePlayer=None,owner=None):
        bs.Actor.__init__(self)
        factory = self.getFactory()
        self.bombType = 'plague'
        self._exploded = False
        self.blastRadius = self.getActivity().settings["Blast Size"]
        self._explodeCallbacks = []
        self.sourcePlayer = sourcePlayer
        self.hitType = 'explosion'
        self.hitSubType = 'plague'
        if owner is None: owner = bs.Node(None)
        self.owner = owner
        fuseTime = 6000
        sticky = False
        model = factory.bombModel
        rType = 'sharper'
        rScale = 1.8
        materials = (factory.bombMaterial, bs.getSharedObject('objectMaterial'))
        self.node = bs.newNode('bomb',
                               delegate=self,
                               attrs={'position':position,
                                      'velocity':velocity,
                                      'model':model,
                                      'shadowSize':0.3,
                                      'colorTexture':bs.getTexture("powerupCurse"),
                                      'sticky':sticky,
                                      'owner':owner,
                                      'reflection':rType,
                                      'reflectionScale':[rScale],
                                      'materials':materials})
        self.node.addDeathAction(bs.WeakCall(self.handleMessage,_BombDiedMessage()))

        sound = bs.newNode('sound',owner=self.node,attrs={'sound':factory.fuseSound,'volume':0.25})
        self.node.connectAttr('position',sound,'position')
        bsUtils.animate(self.node,'fuseLength',{0:1,fuseTime:0})
        bs.gameTimer(fuseTime,bs.Call(self.handleMessage, PlagueMessage()))

    def handleMessage(self, m):
        if isinstance(m, PlagueMessage): self.explode()
        elif isinstance(m, _BombDiedMessage): self.sourcePlayer.actor.bombCount += 1
        else: bs.Bomb.handleMessage(self, m)

    def explode(self):
        if self._exploded: return
        self._exploded = True
        activity = self.getActivity()
        if activity is not None and self.node.exists():
            blast = bs.Blast(position=self.node.position,velocity=self.node.velocity,
                          blastRadius=self.blastRadius,blastType=self.bombType,sourcePlayer=self.sourcePlayer,hitType=self.hitType,hitSubType=self.hitSubType).autoRetain()
            for c in self._explodeCallbacks: c(self,blast)
        bs.gameTimer(1,bs.WeakCall(self.handleMessage,bs.DieMessage()))

class PlagueSpaz(bs.PlayerSpaz):
    def __init__(self, color=(1,1,1), highlight=(0.5,0.5,0.5), character="Spaz", sourcePlayer=None, startInvincible=True,
                 canAcceptPowerups=True, powerupsExpire=False, demoMode=False):
        self._player = sourcePlayer
        bs.Spaz.__init__(self, color, highlight, character, sourcePlayer, startInvincible, canAcceptPowerups, powerupsExpire, demoMode)
    
    def handleMessage(self, m):
        if isinstance(m, bs.HitMessage):
            if m.hitSubType == 'plague': self.curse()
            else: bs.Spaz.handleMessage(self,m)    
        else: bs.Spaz.handleMessage(self,m)

    def dropBomb(self):
        if (self.landMineCount <= 0 and self.bombCount <= 0) or self.frozen: return
        p = self.node.positionForward
        v = self.node.velocity
        droppingBomb = True
        bombType = self.bombType
        bomb = PlagueBomb(position=(p[0],p[1] - 0.0,p[2]),
                       velocity=(v[0],v[1],v[2]),
                       bombType='plague',
                       blastRadius=self.blastRadius,
                       sourcePlayer=self.sourcePlayer,
                       owner=self.node).autoRetain()
        if droppingBomb:
            self.bombCount -= 1
            bomb.node.addDeathAction(bs.WeakCall(self.handleMessage,_BombDiedMessage()))
        self._pickUp(bomb.node)
        for c in self._droppedBombCallbacks: c(self,bomb)
        return bomb
class Plague(bs.TeamGameActivity):
    @classmethod
    def getName(cls):
        return "Plague"

    @classmethod
    def getDescription(cls, sessionType):
        return "Dodge the bombs, survive the plague!"

    @classmethod
    def getScoreInfo(cls):
        return{'scoreType':'points'}

    @classmethod
    def getSettings(cls, sessionType):
        return [("Epic Mode", {'default': False}),
                ("Enable Running", {'default': False}),
                ("Enable Jumping", {'default': False}),
                ("Enable Picking Up", {'default': False}),
                ("Blast Size", {
                    'choices': [
                        ('1', 1),
                        ('2', 2),
                        ('3', 3),
                        ('5', 5),
                        ('10', 10)
                    ],
                    'default': 2})]
    @classmethod
    def getSupportedMaps(cls, sessionType):
        return bs.getMapsSupportingPlayType('melee')

    @classmethod
    def supportsSessionType(cls, sessionType):
        return True if issubclass(sessionType, bs.FreeForAllSession) or issubclass(sessionType, bs.TeamsSession) else False

    def __init__(self,settings):
        bs.TeamGameActivity.__init__(self,settings)
        if self.settings['Epic Mode']: self._isSlowMotion = True
        
    def onTransitionIn(self):
        bs.TeamGameActivity.onTransitionIn(self,music='ToTheDeath')

    def onBegin(self):
        bs.TeamGameActivity.onBegin(self)
        for team in self.teams:
            team.gameData['score'] = 0
        for player in self.players:
            player.gameData['score'] = 0
        self.checkEnd()
    def spawnPlayerSpaz(self,player,position=(0,5,-3),angle=None):
        s = self.settings
        name = player.getName()
        color = player.color
        highlight = player.highlight
        players = self.players
        
        spaz = PlagueSpaz(color=color,
                             highlight=highlight,
                             character=player.character,
                             sourcePlayer=player)
        spaz.connectControlsToPlayer(enablePunch=False, enablePickUp = s["Enable Picking Up"], enableRun = s["Enable Running"], enableJump = s["Enable Jumping"])
        player.setActor(spaz)
        spaz.node.addDeathAction(bs.WeakCall(self.handleMessage,PlagueSpazDeathMessage()))
        spaz.handleMessage(bs.StandMessage(self.getMap().getFFAStartPosition(self.players),90))

    def handleMessage(self, m):
        if isinstance(m, PlagueSpazDeathMessage): self.checkEnd()
        else: bs.TeamGameActivity.handleMessage(self,m)
    def checkEnd(self):
        if isinstance(self.getSession(), bs.FreeForAllSession):
            i = 0
            for team in self.teams:
                if team.players[0].isAlive():
                    team.gameData['score'] += 1
                    i += 1
            if i <= 1:
                self.endGame()
        if isinstance(self.getSession(), bs.TeamsSession):
            for team in self.teams:
                i=0
                team.gameData['score'] = 1
                for player in team.players:
                    if player.isAlive():
                        team.gameData['score'] += 1
                        i += 1
                if i == 0: team.gameData['score'] = 0
            for team in self.teams:
                if team.gameData['score'] == 0: self.endGame()
    def endGame(self):
        results = bs.TeamGameResults()
        for team in self.teams:
            results.setTeamScore(team, team.gameData['score'])
        self.end(results=results)
