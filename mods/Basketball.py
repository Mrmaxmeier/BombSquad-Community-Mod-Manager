#Basketball
import bs
import bsUtils
import math
import random

# This game is played with the same rules as the classic American sport, Bombsquad style!
# Featuring: a hoop, fouls, foul shots, jump-balls, three-pointers, a referee, and two teams ready to duke it out.
# Dedicated to - David

def bsGetAPIVersion():
    return 4

def bsGetGames():
    return [Basketball]

class ImpactMessage(object):
    pass

class Referee(bs.SpazBot):
    character = 'Bernard'
    chargeDistMax = 9999
    throwDistMin = 9999
    throwDistMax = 9999
    color=(0,0,0)
    highlight=(1,1,1)
    punchiness = 0.0
    chargeSpeedMin = 0.0
    chargeSpeedMax = 0.0

class Hoop(bs.Actor):
    def __init__(self,position=(0,5,-8),color=(1,1,1)):
        self._r1 = 0.7
        self._rFudge = 0.15
        bs.Actor.__init__(self)
        self._position = bs.Vector(*position)
        self.color = color
        p1 = position
        p2 = (position[0]+1,position[1],position[2])
        p3 = (position[0]-1,position[1],position[2])
        showInSpace = False
        self._hit = False
        n1 = bs.newNode('locator',attrs={'shape':'circle','position':p1,
                                         'color':self.color,'opacity':0.5,
                                         'drawBeauty':showInSpace,'additive':True})
        n2 = bs.newNode('locator',attrs={'shape':'circle','position':p2,
                                         'color':self.color,'opacity':0.5,
                                         'drawBeauty':showInSpace,'additive':True})
        n3 = bs.newNode('locator',attrs={'shape':'circle','position':p3,
                                         'color':self.color,'opacity':0.5,
                                         'drawBeauty':showInSpace,'additive':True})
        n4 = bs.newNode('light',attrs={'color':self.color,'position':p1,'intensity':.5})

        bs.animateArray(n1,'size',1,{0:[0.0],200:[self._r1*2.0]})
        bs.animateArray(n2,'size',1,{0:[0.0],200:[self._r1*2.0]})
        bs.animateArray(n3,'size',1,{0:[0.0],200:[self._r1*2.0]})
        self._nodes = [n1,n2,n3,n4]

class ThreePointLine(bs.Actor):
    def __init__(self):
        bs.Actor.__init__(self)
        r1 = 6
        n1 = bs.newNode('locator',attrs={'shape':'circleOutline','position':(0,4,-8),'color':(1,1,1),'opacity':.3,'drawBeauty':False,'additive':True})
        self._nodes = [n1]
        bs.animateArray(n1,'size',1,{50:[0.0],250:[r1*2.0]})

class BasketBallFactory(bs.BombFactory):
    def __init__(self):
        self.basketBallMaterial = bs.Material()
        self.basketBallMaterial.addActions(conditions=(('weAreOlderThan',200),
                        'and',('theyAreOlderThan',200),
                        'and',('evalColliding',),
                        'and',(('theyHaveMaterial',bs.getSharedObject('footingMaterial')),
                               'or',('theyHaveMaterial',bs.getSharedObject('objectMaterial')))),
            actions=(('message','ourNode','atConnect',ImpactMessage())))
        bs.BombFactory.__init__(self)

class Baller(bs.PlayerSpaz):
    
    def onBombPress(self):
        pass

    def onPickUpPress(self):
        bs.PlayerSpaz.onPickUpPress(self)
        self.node.getDelegate()._pos = self.node.positionCenter
    
class BasketBomb(bs.Bomb):
    def __init__(self,position=(0,1,0),velocity=(0,0,0),bombType='normal',blastRadius=2.0,sourcePlayer=None,owner=None):
        bs.Actor.__init__(self)
        self.up = False
        factory = BasketBallFactory()
        self.bombType = 'basketball'
        self._exploded = False
        self.blastRadius = blastRadius
        self._explodeCallbacks = []
        self.sourcePlayer = sourcePlayer
        self.hitType = 'impact'
        self.hitSubType = 'basketball'
        owner = bs.Node(None)
        self.owner = owner
        materials = (factory.bombMaterial, bs.getSharedObject('objectMaterial'))
        materials = materials + (factory.normalSoundMaterial,)
        materials = materials + (factory.basketBallMaterial,)
        self.node = bs.newNode('prop',
                                   delegate=self,
                                   attrs={'position':position,
                                          'velocity':velocity,
                                          'body':'sphere',
                                          'model':factory.bombModel,
                                          'shadowSize':0.3,
                                          'colorTexture':bs.getTexture('bonesColorMask'),
                                          'reflection':'soft',
                                          'reflectionScale':[1.5],
                                          'materials':materials})
        bsUtils.animate(self.node,"modelScale",{0:0, 200:1.3, 260:1})

    def handleMessage(self, m):
        if isinstance(m, bs.OutOfBoundsMessage):
            self.getActivity().respawnBall((not self.getActivity().possession))
            bs.Bomb.handleMessage(self, m)
        elif isinstance(m, bs.PickedUpMessage):
            self.heldLast = m.node.getDelegate().getPlayer()
            self.getActivity().heldLast = self.heldLast
            if self.heldLast in self.getActivity().teams[0].players: self.getActivity().possession = True
            else: self.getActivity().possession = False
            bs.Bomb.handleMessage(self, m)
            if self.up == True:
                activity = self.getActivity()
                bs.gameTimer(3000,bs.WeakCall(activity.jumpBall))
            self.up = True
        elif isinstance(m, ImpactMessage): self.getActivity().handleShot(self)
        elif isinstance(m, bs.DroppedMessage): self.up = False
        else: bs.Bomb.handleMessage(self, m)

class Basketball(bs.TeamGameActivity):
    @classmethod
    def getName(cls):
        return "Basketball"

    @classmethod
    def getDescription(cls, sessionType):
        return "A classic sport, Bombsquad style!"

    @classmethod
    def getScoreInfo(cls):
        return{'scoreType':'points'}

    @classmethod
    def getSettings(cls, sessionType):
        return [("Epic Mode", {'default': False}),
                ("Enable Running", {'default': True}),
                ("Enable Jumping", {'default': True}),
                ("Play To: ", {
                    'choices': [
                        ('1 point', 1),
                        ('11 points', 11),
                        ('21 points', 21),
                        ('45 points', 45),
                        ('100 points', 100)
                        ],
                    'default': 21})]
    
    @classmethod
    def getSupportedMaps(cls, sessionType):
        return ['Courtyard']

    @classmethod
    def supportsSessionType(cls, sessionType):
        return True if issubclass(sessionType, bs.TeamsSession) else False

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
        self.possession = True
        self.heldLast = None
        self.fouled = False
        self.firstFoul = False
        self.jb = True
        self.blueBench = bs.newNode('light', attrs={
            'color':(0,0,1),'intensity':1,'position':(-6.5,0,-2)})
        self.redBench = bs.newNode('light', attrs={
            'color':(1,0,0),'intensity':1,'position':(6.5,0,-2)})
        self._bots = bs.BotSet()
        self.hoop = Hoop((0,5,-8), (1,1,1))
        self.threePointLine = ThreePointLine().autoRetain()
        self._scoredis = bs.ScoreBoard()
        self.referee = Referee

        bs.gameTimer(10,bs.Call(self._bots.spawnBot,self.referee,pos=(-6,3,-6),spawnTime=1))
        
    def onTransitionIn(self):
        bs.TeamGameActivity.onTransitionIn(self,music='Sports')

    def onBegin(self):
        bs.TeamGameActivity.onBegin(self)
        s = self.settings
        for player in self.players:
            player.actor.connectControlsToPlayer(enableBomb=False, enableRun = s["Enable Running"], enableJump = s["Enable Jumping"])
            player.sessionData['fouls'] = 0
        self.respawnBall(None)
        self.teams[0].gameData['score'] = 0
        self.teams[1].gameData['score'] = 0
        self._scoredis.setTeamValue(self.teams[0],self.teams[1].gameData['score'])
        self._scoredis.setTeamValue(self.teams[1],self.teams[1].gameData['score'])
        self.updateScore()
        self.checkEnd()

    def spawnPlayerSpaz(self,player,position=(0,5,-3),angle=None, killedDuringFoulShots = False):
        name = player.getName()
        color = player.color
        highlight = player.highlight
        spaz = Baller(color=color,
                             highlight=highlight,
                             character=player.character,
                             player=player)
        player.setActor(spaz)
        if player in self.teams[0].players: position = (-6.5,3.2,(random.random()*5)-4.5)
        else: position = (6.5,3.2,(random.random()*5)-4.5)
        if self.fouled == True and killedDuringFoulShots == False: position = (0,3.2,-3)
        s = self.settings
        player.actor.connectControlsToPlayer(enableBomb=False, enableRun = s["Enable Running"], enableJump = s["Enable Jumping"])
        spaz.handleMessage(bs.StandMessage(position,90))

    def respawnBall(self, owner):
        if owner == True:
            self.basketball = BasketBomb(position=(-6,5,-3)).autoRetain()
        elif owner == False:
            self.basketball = BasketBomb(position=(6,5,-3)).autoRetain()
        else:
            self.basketball = BasketBomb(position=(0,5,-2.5)).autoRetain()

    def handleMessage(self, m):
        if isinstance(m, bs.SpazBotDeathMessage):
            if m.killerPlayer in self.teams[0].players:
                results = bs.TeamGameResults()
                results.setTeamScore(self.teams[0],0)
                results.setTeamScore(self.teams[1],100)
                self.end(results=results)
                bs.screenMessage("Don't take it out on the ref!", color=(1,0,0))
            elif m.killerPlayer in self.teams[1].players:
                results = bs.TeamGameResults()
                results.setTeamScore(self.teams[1],0)
                results.setTeamScore(self.teams[0],100)
                self.end(results=results)
                bs.screenMessage("Don't take it out on the ref!", color=(0,0,1))
        elif isinstance(m, bs.PlayerSpazDeathMessage):
            if m.killed:
                if m.spaz.getPlayer() in self.teams[0].players:
                    team = self.teams[0]
                elif m.spaz.getPlayer() in self.teams[1].players: team = self.teams[1]
                if m.killerPlayer not in team.players:
                    m.killerPlayer.sessionData['fouls'] += 1
                    m.killerPlayer.actor.setScoreText("FOUL " + str(m.killerPlayer.sessionData['fouls']))
                    bs.playSound(bs.getSound('bearDeath'))
                    if m.killerPlayer.sessionData['fouls'] == 3: self.foulOut(m.killerPlayer)
                    if self.fouled == True:
                        self.spawnPlayerSpaz(player=m.spaz.getPlayer(),killedDuringFoulShots=True)
                        return
                    self.fouled = True
                    self.giveFoulShots(m.spaz)
                elif m.spaz.getPlayer().sessionData['fouls'] < 3: self.respawnPlayer(m.spaz.getPlayer())
            elif m.spaz.getPlayer().sessionData['fouls'] < 3: self.respawnPlayer(m.spaz.getPlayer())
            s = self.settings
        else: bs.TeamGameActivity.handleMessage(self, m)

    def giveFoulShots(self, player):
        for p in self.players:
            p.actor.disconnectControlsFromPlayer()
            if p in self.teams[0].players and p != player: p.actor.node.handleMessage('stand',-6.5,3.2,(random.random()*5)-4.5, 0)
            if p in self.teams[1].players and p != player: p.actor.node.handleMessage('stand',6.5,3.2,(random.random()*5)-4.5, 0)
        self.spawnPlayerSpaz(player.getPlayer())
        name = player.getPlayer().getName()
        for p in self.players:
            if p.getName() == name:
                player = p.actor
        s = self.settings
        player.connectControlsToPlayer(enableBomb=False, enableRun = s["Enable Running"], enableJump = s["Enable Jumping"],enablePunch = False)
        self.firstFoul = True
        self.basketball.node.delete()
        self.respawnBall(None)
        sound = bs.getSound('announceTwo')
        bs.gameTimer(1000, bs.Call(bs.playSound,sound))
        player.node.handleMessage('stand',0,3.2,-3, 0)
        player.onPickUpPress()
        player.onPickUpRelease()
        player.setScoreText("5 seconds to shoot")
        bs.gameTimer(6000, bs.Call(self.continueFoulShots,player))

    def continueFoulShots(self, player):
        if self.basketball.node.exists(): self.basketball.node.delete()
        self.firstFoul = False
        player.node.handleMessage('stand',0,3.2,-3, 0)
        self.respawnBall(None)
        bs.playSound(bs.getSound('announceOne'))
        player.onPickUpPress()
        player.onPickUpRelease()
        bs.playSound(bs.getSound('bear1'))
        player.setScoreText("5 seconds to shoot")
        bs.gameTimer(6000, bs.Call(self.continuePlay))

    def continuePlay(self):
        self.fouled = False
        if self.basketball.node.exists(): self.basketball.node.delete()
        self.respawnBall(not self.possession)
        s = self.settings
        for player in self.players:
            player.actor.connectControlsToPlayer(enableBomb=False, enableRun = s["Enable Running"], enableJump = s["Enable Jumping"], enablePunch = True)
        if player in self.teams[0].players:
                player.actor.node.handleMessage('stand',-6.5,3.2,(random.random()*5)-4.5, 0)
        elif player in self.teams[1].players:
                player.actor.node.handleMessage('stand',6.5,3.2,(random.random()*5)-4.5, 0)
        
    def foulOut(self, player):
        player.actor.shatter()
        player.actor.setScoreText("FOULED OUT")

    def jumpBall(self):
        ball = self.basketball
        if ball.up == True:
            self.basketball.heldLast.actor.setScoreText("Jump Ball")
            for player in self.teams[0].players:
                player.actor.node.handleMessage('stand',-6.5,3.2,(random.random()*5)-4.5, 0)
            for player in self.teams[1].players:
                player.actor.node.handleMessage('stand',6.5,3.2,(random.random()*5)-4.5, 0)
            ball.node.delete()
            self.respawnBall(not self.jb)
            self.jb = not self.jb
            
    def handleShot(self, ball):
        if ball.node.position[0] > -1.5 and ball.node.position[0] < 1.5:
            if ball.node.position[1] > 4 and ball.node.position[1] < 5:
                if ball.node.position[2] > -9 and ball.node.position[2] < -8:
                    if self.isTendingGoal(ball):
                        ball.node.delete()
                        self.respawnBall(not self.possession)
                        bs.playSound(bs.getSound('bearDeath'))
                        ball.heldLast.actor.shatter()
                        return
                    bs.playSound(bs.getSound('bear' +str(random.randint(1,4))))
                    for node in self.hoop._nodes:
                        node.delete()
                    self.hoop = None
                    if not self.fouled:
                        if self.possession:
                            pts = self.checkThreePoint(ball)
                            self.teams[0].gameData['score'] += pts
                            ball.heldLast.actor.setScoreText(str(pts) + " Points")
                            self.hoop = Hoop((0,5,-8),(0,0,1))
                            for player in self.teams[0].players:
                                player.actor.node.handleMessage('stand',-6.5,3.2,(random.random()*5)-4.5, 0)
                        else:
                            pts = self.checkThreePoint(ball)
                            self.teams[1].gameData['score'] += pts
                            ball.heldLast.actor.setScoreText(str(pts) + " Points")
                            self.hoop = Hoop((0,5,-8),(1,0,0))
                            for player in self.teams[1].players:
                                player.actor.node.handleMessage('stand',6.5,3.2,(random.random()*5)-4.5, 0)
                        self.updateScore()
                        ball.node.delete()
                        self.respawnBall(not self.possession)
                    else:
                        if self.possession:
                            self.hoop = Hoop((0,5,-8),(0,0,1))
                            self.teams[0].gameData['score'] += 1
                        else:
                            self.hoop = Hoop((0,5,-8),(1,0,0))
                            self.teams[1].gameData['score'] += 1
                        ball.heldLast.actor.setScoreText("1 Point")
                        self.updateScore()
                        ball.node.delete()

    def checkThreePoint(self, ball):
        pos = ball.heldLast.actor._pos
        if pos[0]*pos[0] + (pos[2]+8)*(pos[2]+8) >= 36: return 3
        else: return 2

    def isTendingGoal(self,ball):
        pos = ball.heldLast.actor._pos
        if pos[0] > -1.5 and pos[0] < 1.5:
            if pos[2] > -9 and pos[2] < -8: return True
        return False
    
    def updateScore(self):
        for team in self.teams:
            self._scoredis.setTeamValue(team,team.gameData['score'])
        self.checkEnd()

    def checkEnd(self):
        for team in self.teams:
            i = 0
            if team.gameData['score'] >= self.settings['Play To: ']: self.endGame()
            for player in team.players:
                if player.isAlive(): i = 1
            if i == 0: self.endGame()
        
    def endGame(self):
        results = bs.TeamGameResults()
        for team in self.teams:
            results.setTeamScore(team, team.gameData['score'])
            i = 0
            for player in team.players:
                if player.isAlive(): i = 1
            if i == 0: results.setTeamScore(team, 0)
        self.end(results=results)
