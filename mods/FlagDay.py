#FlagDay
import bs
import random
import bsUtils
import math

# http://www.froemling.net/docs/bombsquad-python-api
#if you really want in-depth explanations of specific terms, go here ^


# fixing random generation of players in setupNextRound

class FlagBearer(bs.PlayerSpaz):
    def handleMessage(self, m):
        bs.PlayerSpaz.handleMessage(self, m)
        if isinstance(m, bs.PowerupMessage):
            if self.getActivity().lastPrize == 'curse':
                self.getPlayer().getTeam().gameData['score'] += 25
                self.getActivity().updateScore()
            elif self.getActivity().lastPrize == 'landmines':
                self.getPlayer().getTeam().gameData['score'] += 15
                self.getActivity().updateScore()
                self.connectControlsToPlayer()
            elif self.getActivity().lastPrize == 'climb':
                self.getPlayer().getTeam().gameData['score'] += 50
                self.getActivity().updateScore()

#This gives the API version to the game to make sure that we are using the right vocabulary
def bsGetAPIVersion():
    return 4

#This tells the game what kind of program this is
def bsGetGames():
    return [FlagDay]

#this gives the game a unique code for our game in this case: "NewGame 124" (One of my other games was NewGame123) P.S. Don't change this half-way through making it
def bsGetLevels():
    return [bs.Level('FlagDay45986',
                     displayName='${GAME}',
                     gameType=FlagDay,
                     settings={},
                     previewTexName='courtyardPreview')]

#this is the class that will actually be saved to the game as a mini-game
class FlagDay(bs.TeamGameActivity):

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

#gives it a name
    @classmethod
    def getName(cls):
        return 'Flag Day'

#Gives it how things are scored
    @classmethod
    def getScoreInfo(cls):
        return {'scoreType':'points'}

#Gives a description of the game
    @classmethod
    def getDescription(cls,sessionType):
        return 'Pick up flags to receive a prize.\nBut beware...'

#Gives which maps are supported, in this case only courtyard though you could probably try it with others, too
    @classmethod
    def getSupportedMaps(cls,sessionType):
        return ['Courtyard']

#Tells the game what kinds of seesions are supported by this mini-game
    @classmethod
    def supportsSessionType(cls,sessionType):
        return True if issubclass(sessionType,bs.FreeForAllSession) or issubclass(sessionType,bs.TeamsSession) or issubclass(sessionType,bs.CoopSession) else False

#Tells the game what to do on the transition in
    def onTransitionIn(self):
        #Sets the music to "To the Death"
        bs.TeamGameActivity.onTransitionIn(self,music='ToTheDeath')

    def onPlayerJoin(self, player):
        player.getTeam().gameData['score'] = 0
        if self.hasBegun():
            bs.screenMessage(bs.Lstr(resource='playerDelayedJoinText', subs=[('${PLAYER}', player.getName(full=True))]),
                             color=(0, 1, 0))

    def onPlayerLeave(self, player):
        if player is self.currentPlayer:
            self.setupNextRound()
        self.checkEnd()
        bs.TeamGameActivity.onPlayerLeave(self,player)
        self.queueLine.remove(player)

    def onBegin(self):
        self.bombSurvivor = None
        self.light = None
        self.set = False
        #Do normal stuff: calls to the main class to operate everything that usually would be done
        bs.TeamGameActivity.onBegin(self)
        self.b = []
        self.queueLine = []
        self.playerIndex = 0
        for player in self.players:
            player.gameData['dead'] = False
            if player.actor is not None:
                player.actor.handleMessage(bs.DieMessage())
                player.actor.node.delete()
            self.queueLine.append(player)
        self.spawnPlayerSpaz(self.queueLine[self.playerIndex%len(self.queueLine)],(0,3,-2))
        self.lastPrize = 'none'
        self.currentPlayer = self.queueLine[0]
        #Declare a set of bots (enemies) that we will use later
        self._bots = bs.BotSet()
        #make another scoreboard? IDK why I did this, probably to make it easier to refer to in the future
        self._scoredis = bs.ScoreBoard()
        #for each team in the game's directory, give them a score of zero
        for team in self.teams:
            team.gameData['score'] = 0
        #Now we go ahead and put that on the scoreboard
        for player in self.queueLine:
            self._scoredis.setTeamValue(player.getTeam(),player.getTeam().gameData['score'])
        self.resetFlags()
        
        

#This handles all the messages that the game throws at us
    def handleMessage(self,m):
        #If it's a flag picked up...
        if isinstance(m,bs.FlagPickedUpMessage):
            #Get the last player to hold that flag
            m.flag._lastPlayerToHold = m.node.getDelegate().getPlayer()
            #Get the last actor to hold that flag (If you are a player, then your body is the actor, think of it like that)
            self._player = m.node.getDelegate()
            #The person to last hold a flag gets the prize, not the person to hold that flag, note.
            self._prizeRecipient = m.node.getDelegate().getPlayer()
            #Call a method to kill the flags
            self.killFlags()
            self.givePrize(random.randint(1,8))
            self.currentPlayer = self._prizeRecipient
        #If a player died...
        if isinstance(m,bs.PlayerSpazDeathMessage):
            #give them a nice farewell
            if bs.getGameTime() < 500: return
            if m.how == 'game': return
            guy = m.spaz.getPlayer()
            bs.screenMessage(str(guy.getName()) + " died!",color=guy.color)
            guy.gameData['dead'] = True
            if guy is self.currentPlayer:
                self.setupNextRound()
            #check to see if we can end the game
            self.checkEnd()

        #If a bot died...
        if isinstance(m,bs.SpazBotDeathMessage):
            #find out which team the last person to hold a flag was on
            team = self._prizeRecipient.getTeam()
            #give them their points
            team.gameData['score'] += self._badGuyCost
            #update the scores
            for team in self.teams:
                self._scoredis.setTeamValue(team,team.gameData['score'])
            bs.gameTimer(300,self.checkBots)

    def spawnPlayerSpaz(self,player,position=(0,0,0),angle=None):
        name = player.getName()
        color = player.color
        highlight = player.highlight

        lightColor = bsUtils.getNormalizedColor(color)
        displayColor = bs.getSafeColor(color,targetIntensity=0.75)
        spaz = FlagBearer(color=color,
                             highlight=highlight,
                             character=player.character,
                             player=player)
        player.setActor(spaz)
        if isinstance(self.getSession(),bs.CoopSession) and self.getMap().getName() in ['Courtyard','Tower D']:
            mat = self.getMap().preloadData['collideWithWallMaterial']
            spaz.node.materials += (mat,)
            spaz.node.rollerMaterials += (mat,)
        spaz.node.name = name
        spaz.node.nameColor = displayColor
        spaz.connectControlsToPlayer()
        spaz.handleMessage(bs.StandMessage(position,angle if angle is not None else random.uniform(0,360)))
        t = bs.getGameTime()
        bs.playSound(self._spawnSound,1,position=spaz.node.position)
        light = bs.newNode('light',attrs={'color':lightColor})
        spaz.node.connectAttr('position',light,'position')
        bsUtils.animate(light,'intensity',{0:0,250:1,500:0})
        bs.gameTimer(500,light.delete)
        return spaz



#a method to remake the flags
    def resetFlags(self):
        #remake the flags
        self._flag1 = bs.Flag(position=(0,3,1),touchable=True,color=(0,0,1))
        self._flag2 = bs.Flag(position=(0,3,-5),touchable=True,color=(1,0,0))
        self._flag3 = bs.Flag(position=(3,3,-2),touchable=True,color=(0,1,0))
        self._flag4 = bs.Flag(position=(-3,3,-2),touchable=True,color=(1,1,1))
        self._flag5 = bs.Flag(position=(1.8,3,.2),touchable=True,color=(0,1,1))
        self._flag6 = bs.Flag(position=(-1.8,3,.2),touchable=True,color=(1,0,1))
        self._flag7 = bs.Flag(position=(1.8,3,-3.8),touchable=True,color=(1,1,0))
        self._flag8 = bs.Flag(position=(-1.8,3,-3.8),touchable=True,color=(0,0,0))

#a method to kill the flags
    def killFlags(self):
        #destroy all the flags by erasing all references to them, indicated by None similar to null
        self._flag1 = None
        self._flag2 = None
        self._flag3 = None
        self._flag4 = None
        self._flag5 = None # 132, 210 ,12
        self._flag6 = None
        self._flag7 = None
        self._flag8 = None

    def setupNextRound(self):
        if self.light is not None: self.light.delete()
        for bomb in self.b:
            bomb.handleMessage(bs.DieMessage())
        self.killFlags()
        self._bots.clear()
        self.resetFlags()
        self.currentPlayer.actor.handleMessage(bs.DieMessage(how='game'))
        self.currentPlayer.actor.node.delete()
        c = 0
        self.playerIndex += 1
        self.playerIndex %= len(self.queueLine)
        if len(self.queueLine) > 0:
            while self.queueLine[self.playerIndex].gameData['dead']:
                if c > len(self.queueLine): return
                self.playerIndex += 1
                self.playerIndex %= len(self.queueLine)
                c += 1
            self.spawnPlayerSpaz(self.queueLine[self.playerIndex],(0,3,-2))
            self.currentPlayer = self.queueLine[self.playerIndex]
        self.lastPrize = 'none'
                
        

#a method to give the prize recipient a prize depending on what flag he took (not really).
    def givePrize(self, prize):
        if prize == 1:
            #Curse him aka make him blow up in 5 seconds
            #give them a nice message
            bs.screenMessage("You were", color=(1,0,0))
            bs.screenMessage("CURSED", color=(.1,.1,.1))
            self.makeHealthBox((0,0,0))
            self.lastPrize = 'curse'
            self._prizeRecipient.actor.curse()
            bs.gameTimer(5500,self.setupNextRound)
        if prize == 2:
            self.setupROF()
            bs.screenMessage("RUN", color=(1,.2,.1))
            self.lastPrize = 'ringoffire'
        if prize == 3:
            self.lastPrize = 'climb'
            self.light =bs.newNode('locator',attrs={'shape':'circle','position':(0,3,-9),
                                    'color':(1,1,1),'opacity':1,
                                    'drawBeauty':True,'additive':True})
            bs.screenMessage("Climb to the top",color=(.5,.5,.5))
            bs.gameTimer(3000, bs.Call(self.makeHealthBox,(0,6,-9)))
            bs.gameTimer(10000, self.setupNextRound)
        if prize == 4:
            self.lastPrize = 'landmines'
            self.makeHealthBox((6,5,-2))
            self.makeLandMines()
            self._prizeRecipient.actor.node.getDelegate().connectControlsToPlayer(enableBomb=False)
            self._prizeRecipient.actor.node.handleMessage(bs.StandMessage(position=(-6,3,-2)))
            bs.gameTimer(7000,self.setupNextRound)
        if prize == 5:
            #Make it rain bombs
            self.bombSurvivor = self._prizeRecipient
            bs.screenMessage("BOMB RAIN!", color=(1,.5,.16))
            #Set positions for the bombs to drop
            for bzz in range(-5,6):
                for azz in range(-5,2):
                    #for each position make a bomb drop there
                    self.makeBomb(bzz,azz)
            bs.gameTimer(3300,self.givePoints)
            self.lastPrize = 'bombrain'
        if prize == 6:
            self.setupBR()
            self.bombSurvivor = self._prizeRecipient
            bs.gameTimer(7000,self.givePoints)
            self.lastPrize = 'bombroad'
        if prize == 7:
            #makes killing a bad guy worth ten points
            self._badGuyCost = 2
            bs.screenMessage("Lame Guys", color=(1,.5,.16))
            #makes a set of nine positions
            for a in range(-1,2):
                for b in range(-3,0):
                    #and spawns one in each position
                    self._bots.spawnBot(bs.ToughGuyBotLame,pos=(a,2.5,b))
                    #and we give our player boxing gloves and a shield
            self._player.equipBoxingGloves()
            self._player.equipShields()
            self.lastPrize = 'lameguys'
        if prize == 8:
            bs.screenMessage("!JACKPOT!", color=(1,0,0))
            bs.screenMessage("!JACKPOT!", color=(0,1,0))
            bs.screenMessage("!JACKPOT!", color=(0,0,1))
            team = self._prizeRecipient.getTeam()
            #GIVE THEM A WHOPPING 50 POINTS!!!
            team.gameData['score'] += 50
            # and update the scores
            self.updateScore()
            self.lastPrize = 'jackpot'
            bs.gameTimer(2000,self.setupNextRound)

    def updateScore(self):
        for player in self.queueLine:
                self._scoredis.setTeamValue(player.getTeam(),player.getTeam().gameData['score'])

    def checkBots(self):
        if not self._bots.haveLivingBots():
            self.setupNextRound()

    def makeLandMines(self):
        self.b = []
        for i in range(-11,7):
            self.b.append(bs.Bomb(position=(0, 6, i/2.0), bombType='landMine', blastRadius=2.0))
            self.b[i+10].arm()

    def givePoints(self):
        if self.bombSurvivor is not None and self.bombSurvivor.isAlive():
            self.bombSurvivor.getTeam().gameData['score'] += 20
            self.updateScore()

    def makeHealthBox(self, position=(0,3,0)):
        if position == (0,3,0):
            position = (random.randint(-6,6),6,random.randint(-6,4))
        elif position == (0,0,0):
            position = random.choice(((-7,6,-5),(7,6,-5),(-7,6,1),(7,6,1)))
        self.healthBox = bs.Powerup(position=position,powerupType='health').autoRetain()

#called in prize #5
    def makeBomb(self,xpos,zpos):
        #makes a bomb at the given position then auto-retains it aka: makes sure it doesn't disappear because there is no reference to it
        b=bs.Bomb(position=(xpos, 12, zpos)).autoRetain()

    def setupBR(self):
        self.makeBombRow(6)
        self._prizeRecipient.actor.handleMessage(bs.StandMessage(position=(6,3,-2)))

    def makeBombRow(self, num):
        if num == 0:
            bs.gameTimer(1000, self.setupNextRound)
            return
        for i in range(-11,7):
            self.b.append(bs.Bomb(position=(-3, 3, i/2.0), velocity=(12,0,0),bombType='normal', blastRadius=1.2))
        if self._prizeRecipient.isAlive(): bs.gameTimer(1000,bs.Call(self.makeBombRow,num-1))
        else: self.setupNextRound()

    def setupROF(self):
        self.makeBlastRing(10)
        self._prizeRecipient.actor.handleMessage(bs.StandMessage(position=(0,3,-2)))

    def makeBlastRing(self,length):
        if length == 0:
            self.setupNextRound()
            self._prizeRecipient.getTeam().gameData['score'] += 50
            self.updateScore()
            return
        for angle in range(0,360,45):
            angle += random.randint(0,45)
            angle %= 360
            x = length * math.cos(math.radians(angle))
            z = length * math.sin(math.radians(angle))
            blast = bs.Blast(position=(x,2.2,z-2),blastRadius=3.5)
        if self._prizeRecipient.isAlive(): bs.gameTimer(750,bs.Call(self.makeBlastRing,length-1))
        else: self.setupNextRound()

#checks to see if we should end the game
    def checkEnd(self):
        for player in self.queueLine:
            if not player.gameData['dead']: return
        self.endGame()

#called when ready to end the game
    def endGame(self):
        if self.set == True: return
        self.set = True
        results = bs.TeamGameResults()
        #Set the results for the game to display at the end of the game
        for team in self.teams:
            results.setTeamScore(team, team.gameData['score'])
        self.end(results=results)
