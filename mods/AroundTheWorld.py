import bs
import random
import bsUtils

def bsGetAPIVersion():
    # see bombsquadgame.com/apichanges
    return 4

def bsGetGames():
    return [AroundTheWorld]

class AroundTheWorld(bs.TeamGameActivity):

    @classmethod
    def getName(cls):
        return 'Around The World'

    @classmethod
    def getDescription(cls,sessionType):
        return 'Race around the world.'

    @classmethod
    def getScoreInfo(cls):
        return {'scoreName':'Time',
                'lowerIsBetter':True,
                'scoreType':'milliseconds'}
    
    @classmethod
    def supportsSessionType(cls,sessionType):
        return True if (issubclass(sessionType,bs.TeamsSession)
                        or issubclass(sessionType,bs.FreeForAllSession)) else False

    @classmethod
    def getSupportedMaps(cls,sessionType):
        return ['Happy Thoughts']

    @classmethod
    def getSettings(cls,sessionType):
        settings = [("Laps",{'minValue':1,"default":3,"increment":1}),
                    ("Time Limit",{'choices':[('None',0),('1 Minute',60),
                                              ('2 Minutes',120),('5 Minutes',300),
                                              ('10 Minutes',600),('20 Minutes',1200)],'default':0}),
                    ("Epic Mode",{'default':False})]
        
        if issubclass(sessionType,bs.TeamsSession):
            settings.append(("Entire Team Must Finish",{'default':False}))
        return settings
        
    
    def __init__(self,settings):
        self._raceStarted = False
        bs.TeamGameActivity.__init__(self,settings)
        for player in self.players:
            player.gameData['lastPoint'] = 0
        self._scoreBoard = bs.ScoreBoard()
        if self.settings['Epic Mode']: self._isSlowMotion = True
        self._scoreSound = bs.getSound("score")
        self._swipSound = bs.getSound("swip")
        self._lastTeamTime = None
        self._frontRaceRegion = None
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
        

    def getInstanceDescription(self):
        if isinstance(self.getSession(),bs.TeamsSession) and self.settings.get('Entire Team Must Finish', False):
            tStr = ' Your entire team has to finish.'
        else: tStr = ''

        if self.settings['Laps'] > 1: s = ('${ARG1} laps.'+tStr,self.settings['Laps'])
        else: s = 'Fly 1 lap.'+tStr
        return s

    def getInstanceScoreBoardDescription(self):
        if self.settings['Laps'] > 1: s = ('fly ${ARG1} laps',self.settings['Laps'])
        else: s = 'fly 1 lap'
        return s

    def spawnPlayerSpaz(self,player,position=(0,0,0),angle=None):
        posList = ((0,5,0),(9,11,0),(0,12,0),(-11,11,0))
        try: pos = posList[player.gameData['lastPoint']]
        except: pos = (0,5,0)
        position = (pos[0]+random.random()*2 -1 ,pos[1],pos[2])
        name = player.getName()
        color = player.color
        highlight = player.highlight

        lightColor = bsUtils.getNormalizedColor(color)
        displayColor = bs.getSafeColor(color,targetIntensity=0.75)
        spaz = bs.PlayerSpaz(color=color,
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
        if self._raceStarted: spaz.connectControlsToPlayer()
        spaz.handleMessage(bs.StandMessage(position,angle if angle is not None else random.uniform(0,360)))
        t = bs.getGameTime()
        bs.playSound(self._spawnSound,1,position=spaz.node.position)
        light = bs.newNode('light',attrs={'color':lightColor})
        spaz.node.connectAttr('position',light,'position')
        bsUtils.animate(light,'intensity',{0:0,250:1,500:0})
        bs.gameTimer(500,light.delete)
        if not self._raceStarted: player.gameData['lastPoint'] = 0
        bs.gameTimer(250,bs.Call(self.checkPt,player))
        return spaz
        

    def onTransitionIn(self):
        bs.TeamGameActivity.onTransitionIn(self, music='Epic Race' if self.settings['Epic Mode'] else 'Race')

        self._nubTex = bs.getTexture('nub')
        self._beep1Sound = bs.getSound('raceBeep1')
        self._beep2Sound = bs.getSound('raceBeep2')

    def _flashPlayer(self,player,scale):
        pos = player.actor.node.position
        light = bs.newNode('light',
                           attrs={'position':pos,
                                  'color':(1,1,0),
                                  'heightAttenuated':False,
                                  'radius':0.4})
        bs.gameTimer(500,light.delete)
        bs.animate(light,'intensity',{0:0,100:1.0*scale,500:0})
        
                        
    def onTeamJoin(self,team):
        team.gameData['time'] = None
        team.gameData['lap'] = 0
        team.gameData['finished'] = False
        self._updateScoreBoard()

    def onPlayerJoin(self,player):
        player.gameData['lastRegion'] = 0
        player.gameData['lap'] = 0
        player.gameData['distance'] = 0.0
        player.gameData['finished'] = False
        player.gameData['rank'] = None
        bs.TeamGameActivity.onPlayerJoin(self,player)

    def onPlayerLeave(self,player):
        bs.TeamGameActivity.onPlayerLeave(self,player)
        if isinstance(self.getSession(),bs.TeamsSession) and self.settings.get('Entire Team Must Finish'):
            bs.screenMessage(bs.Lstr(translate=('statements', '${TEAM} is disqualified because ${PLAYER} left'),
                                     subs=[('${TEAM}',player.getTeam().name),
                                           ('${PLAYER}',player.getName(full=True))]),color=(1,1,0))
            player.getTeam().gameData['finished'] = True
            player.getTeam().gameData['time'] = None
            player.getTeam().gameData['lap'] = 0
            bs.playSound(bs.getSound("boo"))
            for player in player.getTeam().players:
                player.gameData['lap'] = 0
                player.gameData['finished'] = True
                try: player.actor.handleMessage(bs.DieMessage())
                except Exception: pass
        bs.gameTimer(1,self._checkEndGame)

    def _updateScoreBoard(self):
        for team in self.teams:
            distances = [player.gameData['distance'] for player in team.players]
            if len(distances) == 0: teamDist = 0
            else:
                if isinstance(self.getSession(),bs.TeamsSession) and self.settings.get('Entire Team Must Finish'):
                    teamDist = min(distances)
                else:
                    teamDist = max(distances)
            self._scoreBoard.setTeamValue(team,teamDist,self.settings['Laps'],flash=(teamDist >= float(self.settings['Laps'])),showValue=False)
            if (teamDist >= float(self.settings['Laps'])): self.checkEnd()

    def onBegin(self):
        bs.TeamGameActivity.onBegin(self)
        self.setupStandardTimeLimit(self.settings['Time Limit'])
        self.setupStandardPowerupDrops()
        self._teamFinishPts = 100

        # throw a timer up on-screen
        self._timeText = bs.NodeActor(bs.newNode('text',
                                                 attrs={'vAttach':'top','hAttach':'center','hAlign':'right',
                                                        'color':(1,1,1,.5),'flatness':0.5,'shadow':0.5,
                                                        'position':(600,-500),'scale':1.4,'text':'Touch\nthe\nright,\ntop,\nleft,\nand\nbottom\nplatforms\nin\norder.'}))
        self._timer = bs.OnScreenTimer()
        

        self._scoreBoardTimer = bs.Timer(250,self._updateScoreBoard,repeat=True)

        if self._isSlowMotion:
            tScale = 0.4
            lightY = 50
        else:
            tScale = 1.0
            lightY = 150
        lStart = int(7100*tScale)
        inc = int(1250*tScale)

        bs.gameTimer(lStart,self._doLight1)
        bs.gameTimer(lStart+inc,self._doLight2)
        bs.gameTimer(lStart+2*inc,self._doLight3)
        bs.gameTimer(lStart+3*inc,self._startRace)

        self._startLights = []
        for i in range(4):
            l = bs.newNode('image',
                           attrs={'texture':bs.getTexture('nub'),
                                  'opacity':1.0,
                                  'absoluteScale':True,
                                  'position':(-75+i*50,lightY),
                                  'scale':(50,50),
                                  'attach':'center'})
            bs.animate(l,'opacity',{4000*tScale:0,5000*tScale:1.0,12000*tScale:1.0,12500*tScale:0.0})
            bs.gameTimer(int(13000*tScale),l.delete)
            self._startLights.append(l)

        self._startLights[0].color = (0.2,0,0)
        self._startLights[1].color = (0.2,0,0)
        self._startLights[2].color = (0.2,0.05,0)
        self._startLights[3].color = (0.0,0.3,0)

    def _doLight1(self):
        self._startLights[0].color = (1.0,0,0)
        bs.playSound(self._beep1Sound)
    def _doLight2(self):
        self._startLights[1].color = (1.0,0,0)
        bs.playSound(self._beep1Sound)
    def _doLight3(self):
        self._startLights[2].color = (1.0,0.3,0)
        bs.playSound(self._beep1Sound)
    def _startRace(self):
        self._startLights[3].color = (0.0,1.0,0)
        bs.playSound(self._beep2Sound)
        for player in self.players:
            if player.actor is not None:
                try:player.actor.connectControlsToPlayer()
                except Exception,e: print 'Exception in race player connects:',e
        self._timer.start()
        
        self._raceStarted = True

    def checkPt(self,player):
        if not player.isAlive(): return
        pos = player.actor.node.positionCenter
        if 8 < pos[0] < 11 and 10.5 < pos[1] < 13:
            if player.gameData['lastPoint'] in (2,3):
                self.killPlayer(player)
                return
            elif player.gameData['lastPoint'] == 0: player.gameData['distance'] += .25
            player.gameData['lastPoint'] = 1
        if -1 < pos[0] < 1 and 11.5 < pos[1] < 15:
            if player.gameData['lastPoint'] in (3,0):
                self.killPlayer(player)
                return
            elif player.gameData['lastPoint'] == 1: player.gameData['distance'] += .25
            player.gameData['lastPoint'] = 2
        if -12.5 < pos[0] < -10 and 10.5 < pos[1] < 13:
            if player.gameData['lastPoint'] in (0,1):
                self.killPlayer(player)
                return
            elif player.gameData['lastPoint'] == 2: player.gameData['distance'] += .25
            player.gameData['lastPoint'] = 3
        if -2 < pos[0] < 2 and 4.5 < pos[1] < 6.5:
            if player.gameData['lastPoint'] in (1,2):
                self.killPlayer(player)
                return
            elif player.gameData['lastPoint'] == 3: player.gameData['distance'] += .25
            player.gameData['lastPoint'] = 0
        
        bs.gameTimer(250,bs.Call(self.checkPt,player))

    def checkEnd(self):
        for player in self.players:
            if player.gameData['distance'] >= self.settings['Laps']:
                player.getTeam().gameData['time'] = (bs.getGameTime() - self._timer.getStartTime())
                player.actor.node.delete()
                self.endGame()
                
    def killPlayer(self,player):
        player.actor.handleMessage(bs.DieMessage())
        bs.screenMessage("Killing " + player.getName() + " for skipping part of the track.", (1,0,0))
        
    def endGame(self):
        if self._timer.hasStarted():
            self._timer.stop(endTime=None if self._lastTeamTime is None else (self._timer.getStartTime()+self._lastTeamTime))
        
        results = bs.TeamGameResults()
        
        for t in self.teams: results.setTeamScore(t,t.gameData['time'])
        self.end(results=results,announceWinningTeam=True)

    def handleMessage(self,m):
        if isinstance(m,bs.PlayerSpazDeathMessage):
            bs.TeamGameActivity.handleMessage(self,m) # augment default
            try:
                player = m.spaz.getPlayer()
                if player is None:
                    bs.printError('FIXME: getPlayer() should no longer ever be returning None')
                else:
                    if not player.exists(): raise Exception()
                team = player.getTeam()
            except Exception: return
            if not player.gameData['finished']: self.respawnPlayer(player,respawnTime=1000)
        else:
            bs.TeamGameActivity.handleMessage(self,m)
