#SimonSays
# you had really better do what Simon says...
import bs
import random

def bsGetAPIVersion():
    return 4

def bsGetGames():
    return [SimonSays]

class SimonSays(bs.TeamGameActivity):
    @classmethod
    def getName(cls):
        return "Simon Says"

    @classmethod
    def getDescription(cls, sessionType):
        return "You had better do what Simon says..."

    @classmethod
    def getScoreInfo(cls):
        return{'scoreType':'points'}

    @classmethod
    def getSettings(cls, sessionType):
        return [("Epic Mode", {'default': False}),
                ("Enable Jumping", {'default': False}),
                ("Enable Punching", {'default': False}),
                ("Enable Picking Up", {'default': False})]
    
    @classmethod
    def getSupportedMaps(cls, sessionType):
        return ["Courtyard"]

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
        self.roundNum = 0
        self.simon = False
        self.time = 5000
        self._r1 = 2
        n1 = bs.newNode('locator',attrs={'shape':'circle','position':(-4,0,-6),
                                         'color':(1,0,0),'opacity':0.5,
                                         'drawBeauty':True,'additive':True})
        n2 = bs.newNode('locator',attrs={'shape':'circle','position':(0,0,-6),
                                         'color':(0,1,0),'opacity':0.5,
                                         'drawBeauty':True,'additive':True})
        n3 = bs.newNode('locator',attrs={'shape':'circle','position':(4,0,-6),
                                         'color':(0,0,1),'opacity':0.5,
                                         'drawBeauty':True,'additive':True})
        n4 = bs.newNode('locator',attrs={'shape':'circle','position':(-4,0,-2),
                                         'color':(1,1,0),'opacity':0.5,
                                         'drawBeauty':True,'additive':True})
        n5 = bs.newNode('locator',attrs={'shape':'circle','position':(0,0,-2),
                                         'color':(0,1,1),'opacity':0.5,
                                         'drawBeauty':True,'additive':True})
        n6 = bs.newNode('locator',attrs={'shape':'circle','position':(4,0,-2),
                                         'color':(1,0,1),'opacity':0.5,
                                         'drawBeauty':True,'additive':True})
        n7 = bs.newNode('locator',attrs={'shape':'circle','position':(-4,0,2),
                                         'color':(.5,.5,.5),'opacity':0.5,
                                         'drawBeauty':True,'additive':True})
        n8 = bs.newNode('locator',attrs={'shape':'circle','position':(0,0,2),
                                         'color':(.5,.325,0),'opacity':0.5,
                                         'drawBeauty':True,'additive':True})
        n9 = bs.newNode('locator',attrs={'shape':'circle','position':(4,0,2),
                                         'color':(1,1,1),'opacity':0.5,
                                         'drawBeauty':True,'additive':True})
        bs.animateArray(n1,'size',1,{0:[0.0],200:[self._r1*2.0]})
        bs.animateArray(n2,'size',1,{0:[0.0],200:[self._r1*2.0]})
        bs.animateArray(n3,'size',1,{0:[0.0],200:[self._r1*2.0]})
        bs.animateArray(n4,'size',1,{0:[0.0],200:[self._r1*2.0]})
        bs.animateArray(n5,'size',1,{0:[0.0],200:[self._r1*2.0]})
        bs.animateArray(n6,'size',1,{0:[0.0],200:[self._r1*2.0]})
        bs.animateArray(n7,'size',1,{0:[0.0],200:[self._r1*2.0]})
        bs.animateArray(n8,'size',1,{0:[0.0],200:[self._r1*2.0]})
        bs.animateArray(n9,'size',1,{0:[0.0],200:[self._r1*2.0]})
        self.options = ["red", "green", "blue", "yellow", "teal", "purple", "gray", "orange", "white", "top", "bottom", "middle row", "left", "right", "center column", "outside"]

    def onTransitionIn(self):
        bs.TeamGameActivity.onTransitionIn(self,music='FlagCatcher')
        
    def onPlayerJoin(self, player):
        if self.hasBegun():
            bs.screenMessage(bs.Lstr(resource='playerDelayedJoinText', subs=[('${PLAYER}', player.getName(full=True))]),
                             color=(0, 1, 0))

    def onBegin(self):
        s = self.settings
        bs.TeamGameActivity.onBegin(self)
        for team in self.teams:
            team.gameData['score'] = 0
        for player in self.players:
            player.gameData['score'] = 0
            self.spawnPlayerSpaz(player,self.getMap().getFFAStartPosition(self.players))
            player.actor.connectControlsToPlayer(enableBomb=False, enablePunch = s["Enable Punching"], enablePickUp = s["Enable Picking Up"], enableRun = True, enableJump = s["Enable Jumping"])
        self.explainGame()

    def explainGame(self):
        bs.screenMessage("Follow the commands...")
        bs.screenMessage("but only when Simon says!")
        bs.gameTimer(5000, self.callRound)

    def callRound(self):
        self.roundNum += 1
        self.num = random.randint(0, 15)
        num = self.num
        self.simon = random.choice([True, False])
        if num < 9: line = "Run to the " + self.options[num] + " circle!"
        elif num < 15: line = "Run to the " + self.options[num] + "!"
        else: line = "Run outside of the circles!"
        if self.simon: line = "Simon says " + line[0].lower() + line[1:]
        self.text = bs.PopupText(line, position=(0, 5, -4), color=(1, 1, 1), randomOffset=0.5, offset=(0, 0, 0), scale=2.0).autoRetain()
        self.time -= 100
        bs.gameTimer(self.time, self.checkRound)

    def checkRound(self):
        for player in self.players:
            if player.isAlive():
                safe = True if self.options[self.num] in self.inCircle(player.actor.node.positionCenter) else False
                if ((self.simon and safe == False) or ((not self.simon) and safe == True)):
                    player.getTeam().gameData["score"] = self.roundNum
                    player.actor.handleMessage(bs.DieMessage())
        self.callRound()
                        

    def inCircle(self, pos):
        circles = []
        x = pos[0]
        z = pos[2]
        if (x + 4) ** 2 + (z + 6) ** 2 < 4: circles.append("red")
        elif (x) ** 2 + (z + 6) ** 2 < 4: circles.append("green")
        elif (x - 4) ** 2 + (z + 6) ** 2 < 4: circles.append("blue")
        elif (x + 4) ** 2 + (z + 2) ** 2 < 4: circles.append("yellow")
        elif (x) ** 2 + (z + 2) ** 2 < 4: circles.append("teal")
        elif (x - 4) ** 2 + (z + 2) ** 2 < 4: circles.append("purple")
        elif (x + 4) ** 2 + (z - 2) ** 2 < 4: circles.append("gray")
        elif (x) ** 2 + (z - 2) ** 2 < 4: circles.append("orange")
        elif (x - 4) ** 2 + (z - 2) ** 2 < 4: circles.append("white")
        else: circles.append("outside")
        if x < -2: circles.append("left")
        if x > 2: circles.append("right")
        if x > -2 and x < 2: circles.append("center column")
        if z > 0: circles.append("bottom")
        if z < -4: circles.append("top")
        if z < 0 and z > -4: circles.append("middle row")
        return circles

    def handleMessage(self, m):
        if isinstance(m, bs.PlayerSpazDeathMessage): self.checkEnd()
        else: bs.TeamGameActivity.handleMessage(self, m)

    def onPlayerJoin(self, player):
        if self.hasBegun():
            bs.screenMessage(bs.Lstr(resource='playerDelayedJoinText',subs=[('${PLAYER}',player.getName(full=True))]),color=(0,1,0))
            return

    def checkEnd(self):
        i = 0
        for player in self.players:
            if player.isAlive(): i += 1
        if i < 2: self.endGame()

    def endGame(self):
        results = bs.TeamGameResults()
        for team in self.teams:
            results.setTeamScore(team, team.gameData['score'])
        self.end(results=results)
