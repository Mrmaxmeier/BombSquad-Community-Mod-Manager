import bs
import bsVector
import bsSpaz
import bsBomb
import bsUtils
import random
import SnoBallz

#please note that this Minigame requires the separate file SnoBallz.py.
#It's a separate file to allow for snowballs as a powerup in any game.

def bsGetAPIVersion():
    # see bombsquadgame.com/apichanges
    return 4

def bsGetGames():
    return [SnowBallFightGame]

class PlayerSpaz_Sno(bs.PlayerSpaz):
    def handleMessage(self,m):
        #print m, self.hitPoints
        if isinstance(m,bsSpaz._PunchHitMessage): return True #Nullify punches

        super(self.__class__, self).handleMessage(m)

                
class SnowBallFightGame(bs.TeamGameActivity):

    @classmethod
    def getName(cls):
        return 'Snowball Fight'

    @classmethod
    def getDescription(cls,sessionType):
        return 'Kill a set number of enemies to win.'

    @classmethod
    def supportsSessionType(cls,sessionType):
        return True if (issubclass(sessionType,bs.TeamsSession)
                        or issubclass(sessionType,bs.FreeForAllSession)) else False

    @classmethod
    def getSupportedMaps(cls,sessionType):
        return bs.getMapsSupportingPlayType("melee")

    @classmethod
    def getSettings(cls,sessionType):
        settings = [("Kills to Win Per Player",{'minValue':1,'default':5,'increment':1}),
                    ("Time Limit",{'choices':[('None',0),('1 Minute',60),
                                              ('2 Minutes',120),('5 Minutes',300),
                                              ('10 Minutes',600),('20 Minutes',1200)],'default':0}),
                    ("Respawn Times",{'choices':[('Shorter',0.25),('Short',0.5),('Normal',1.0),('Long',2.0),('Longer',4.0)],'default':1.0}),
                    ("Snowball Rate",{'choices':[('Slowest',500),('Slow',400),('Normal',300),('Fast',200),('Lag City',100)],'default':300}),
                    ("Snowballs Melt",{'default':True}),
                    ("Snowballs Bust",{'default':True}),
                    ("Epic Mode",{'default':False})]
        
        # In teams mode, a suicide gives a point to the other team, but in free-for-all it
        # subtracts from your own score. By default we clamp this at zero to benefit new players,
        # but pro players might like to be able to go negative. (to avoid a strategy of just
        # suiciding until you get a good drop)
        if issubclass(sessionType, bs.FreeForAllSession):
            settings.append(("Allow Negative Scores",{'default':False}))

        return settings

    def __init__(self,settings):
        bs.TeamGameActivity.__init__(self,settings)
        if self.settings['Epic Mode']: self._isSlowMotion = True

        # print messages when players die since it matters here..
        self.announcePlayerDeaths = True
        
        self._scoreBoard = bs.ScoreBoard()
        
        #Initiate the SnoBall factory
        self.snoFact = SnoBallz.snoBall().getFactory()
        self.snoFact.defaultBallTimeout = self.settings['Snowball Rate']
        self.snoFact._ballsMelt = self.settings['Snowballs Melt']
        self.snoFact._ballsBust = self.settings['Snowballs Bust']
        self.snoFact._powerExpire = False
    def getInstanceDescription(self):
        return ('Crush ${ARG1} of your enemies.',self._scoreToWin)

    def getInstanceScoreBoardDescription(self):
        return ('kill ${ARG1} enemies',self._scoreToWin)

    def onTransitionIn(self):
        bs.TeamGameActivity.onTransitionIn(self, music='Epic' if self.settings['Epic Mode'] else 'ToTheDeath')

    def onTeamJoin(self,team):
        team.gameData['score'] = 0
        if self.hasBegun(): self._updateScoreBoard()

    def onBegin(self):
        bs.TeamGameActivity.onBegin(self)
        self.setupStandardTimeLimit(self.settings['Time Limit'])
        self.setupStandardPowerupDrops()
        if len(self.teams) > 0:
            self._scoreToWin = self.settings['Kills to Win Per Player'] * max(1,max(len(t.players) for t in self.teams))
        else: self._scoreToWin = self.settings['Kills to Win Per Player']
        self._updateScoreBoard()
        self._dingSound = bs.getSound('dingSmall')
        
    def _standardDropPowerup(self,index,expire=True):
        import bsPowerup
        forbidded = ['iceBombs','punch','stickyBombs','landMines', 'snoball']
        bsPowerup.Powerup(position=self.getMap().powerupSpawnPoints[index],
                          powerupType=bs.Powerup.getFactory().getRandomPowerupType(None,forbidded),expire=expire).autoRetain()    
                          
    def spawnPlayerSpaz(self,player,position=(0,0,0),angle=None):
        """
        Create and wire up a bs.PlayerSpaz for the provide bs.Player.
        """
        position = self.getMap().getFFAStartPosition(self.players)
        name = player.getName()
        color = player.color
        highlight = player.highlight

        lightColor = bsUtils.getNormalizedColor(color)
        displayColor = bs.getSafeColor(color,targetIntensity=0.75)
        spaz = PlayerSpaz_Sno(color=color,
                             highlight=highlight,
                             character=player.character,
                             player=player)
        player.setActor(spaz)

        # we want a bigger area-of-interest in co-op mode
        # if isinstance(self.getSession(),bs.CoopSession): spaz.node.areaOfInterestRadius = 5.0
        # else: spaz.node.areaOfInterestRadius = 5.0

        # if this is co-op and we're on Courtyard or Runaround, add the material that allows us to
        # collide with the player-walls
        # FIXME; need to generalize this
        if isinstance(self.getSession(),bs.CoopSession) and self.getMap().getName() in ['Courtyard','Tower D']:
            mat = self.getMap().preloadData['collideWithWallMaterial']
            spaz.node.materials += (mat,)
            spaz.node.rollerMaterials += (mat,)
        
        spaz.node.name = name
        spaz.node.nameColor = displayColor
        spaz.connectControlsToPlayer(enableBomb=False, enablePickUp=False)
        self.snoFact.giveBallz(spaz) 
        self.scoreSet.playerGotNewSpaz(player,spaz)

        # move to the stand position and add a flash of light
        spaz.handleMessage(bs.StandMessage(position,angle if angle is not None else random.uniform(0,360)))
        t = bs.getGameTime()
        bs.playSound(self._spawnSound,1,position=spaz.node.position)
        light = bs.newNode('light',attrs={'color':lightColor})
        spaz.node.connectAttr('position',light,'position')
        bsUtils.animate(light,'intensity',{0:0,250:1,500:0})
        bs.gameTimer(500,light.delete)
        return spaz
    
    def handleMessage(self,m):

        if isinstance(m,bs.PlayerSpazDeathMessage):
            bs.TeamGameActivity.handleMessage(self,m) # augment standard behavior

            player = m.spaz.getPlayer()
            self.respawnPlayer(player)

            killer = m.killerPlayer
            if killer is None: return

            # handle team-kills
            if killer.getTeam() is player.getTeam():

                # in free-for-all, killing yourself loses you a point
                if isinstance(self.getSession(),bs.FreeForAllSession):
                    newScore = player.getTeam().gameData['score'] - 1
                    if not self.settings['Allow Negative Scores']: newScore = max(0, newScore)
                    player.getTeam().gameData['score'] = newScore

                # in teams-mode it gives a point to the other team
                else:
                    bs.playSound(self._dingSound)
                    for team in self.teams:
                        if team is not killer.getTeam():
                            team.gameData['score'] += 1

            # killing someone on another team nets a kill
            else:
                killer.getTeam().gameData['score'] += 1
                bs.playSound(self._dingSound)
                # in FFA show our score since its hard to find on the scoreboard
                try: killer.actor.setScoreText(str(killer.getTeam().gameData['score'])+'/'+str(self._scoreToWin),color=killer.getTeam().color,flash=True)
                except Exception: pass

            self._updateScoreBoard()

            # if someone has won, set a timer to end shortly
            # (allows the dust to clear and draws to occur if deaths are close enough)
            if any(team.gameData['score'] >= self._scoreToWin for team in self.teams):
                bs.gameTimer(500,self.endGame)

        else: bs.TeamGameActivity.handleMessage(self,m)

    def _updateScoreBoard(self):
        for team in self.teams:
            self._scoreBoard.setTeamValue(team,team.gameData['score'],self._scoreToWin)

    def endGame(self):
        results = bs.TeamGameResults()
        for t in self.teams: results.setTeamScore(t,t.gameData['score'])
        self.end(results=results)
