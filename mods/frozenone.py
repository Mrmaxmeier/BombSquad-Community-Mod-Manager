import bs

def bsGetAPIVersion():
    return 3

def bsGetGames():
    return [FrozenOneGame]

class FrozenOneGame(bs.TeamGameActivity):

    @classmethod
    def getName(cls):
        return 'Frozen One'

    @classmethod
    def getScoreInfo(cls):
        return {'scoreName':'Time Held'}
    
    @classmethod
    def getDescription(cls,sessionType):
        return ('Be the Frozen one for a length of time to win.\n'
                'Kill the Frozen one to become it.')

    @classmethod
    def supportsSessionType(cls,sessionType):
        return True if (issubclass(sessionType,bs.TeamsSession)
                        or issubclass(sessionType,bs.FreeForAllSession)) else False

    @classmethod
    def getSupportedMaps(cls,sessionType):
        return bs.getMapsSupportingPlayType("keepAway")

    @classmethod
    def getSettings(cls,sessionType):
        return [("Frozen One Time",{'minValue':10,'default':30,'increment':10}),
                ("Frozen One Gets Gloves",{'default':True}),
                ("Time Limit",{'choices':[('None',0),('1 Minute',60),
                                        ('2 Minutes',120),('5 Minutes',300),
                                        ('10 Minutes',600),('20 Minutes',1200)],'default':0}),
                ("Respawn Times",{'choices':[('Shorter',0.25),('Short',0.5),('Normal',1.0),('Long',2.0),('Longer',4.0)],'default':1.0}),
                ("Epic Mode",{'default':False})]

    def __init__(self,settings):
        bs.TeamGameActivity.__init__(self,settings)
        if self.settings['Epic Mode']: self._isSlowMotion = True
        self._scoreBoard = bs.ScoreBoard()
        self._FrozenOnePlayer = None
        self._swipSound = bs.getSound("swip")
        self._countDownSounds = {10:bs.getSound('announceTen'),
                                 9:bs.getSound('announceNine'),
                                 8:bs.getSound('announceEight'),
                                 7:bs.getSound('announceSeven'),
                                 6:bs.getSound('announceSix'),
                                 5:bs.getSound('announceFive'),
                                 4:bs.getSound('announceFour'),
                                 3:bs.getSound('announceThree'),
                                 2:bs.getSound('announceTwo'),
                                 1:bs.getSound('announceOne')}

    def getInstanceDescription(self):
        return 'There can be only one.'

    def onTransitionIn(self):
        bs.TeamGameActivity.onTransitionIn(self, music='Epic' if self.settings['Epic Mode'] else 'Chosen One')

    def onTeamJoin(self,team):
        team.gameData['timeRemaining'] = self.settings["Frozen One Time"]
        self._updateScoreBoard()

    def onPlayerLeave(self,player):
        bs.TeamGameActivity.onPlayerLeave(self,player)
        if self._getFrozenOnePlayer() is player:
            self._setFrozenOnePlayer(None)
            
    def onBegin(self):

        # test...
        if not all(player.exists() for player in self.players):
            bs.printError("Nonexistant player in onBegin: "+str([str(p) for p in self.players])+': we are '+str(player))

        bs.TeamGameActivity.onBegin(self)
        self.setupStandardTimeLimit(self.settings['Time Limit'])
        self.setupStandardPowerupDrops()
        self._flagSpawnPos = self.getMap().getFlagPosition(None)
        self.projectFlagStand(self._flagSpawnPos)
        self._setFrozenOnePlayer(None)

        p = self._flagSpawnPos
        bs.gameTimer(1000,call=self._tick,repeat=True)

        m = self._resetRegionMaterial = bs.Material()
        m.addActions(conditions=('theyHaveMaterial',bs.getSharedObject('playerMaterial')),
                     actions=(('modifyPartCollision','collide',True),
                              ('modifyPartCollision','physical',False),
                              ('call','atConnect',bs.WeakCall(self._handleResetCollide))))

        self._resetRegion = bs.newNode('region',
                                       attrs={'position':(p[0],p[1]+0.75,p[2]),
                                              'scale': (0.5,0.5,0.5),
                                              'type': 'sphere',
                                              'materials':[m]
                                              })

    def _getFrozenOnePlayer(self):
        if self._FrozenOnePlayer is not None and self._FrozenOnePlayer.exists(): return self._FrozenOnePlayer
        else: return None

    def _handleResetCollide(self):
        # if we have a Frozen one ignore these
        if self._getFrozenOnePlayer() is not None: return
        try: player = bs.getCollisionInfo("opposingNode").getDelegate().getPlayer()
        except Exception: return
        if player is not None and player.isAlive():
            self._setFrozenOnePlayer(player)
        
    def _flashFlagSpawn(self):
        light = bs.newNode('light',
                           attrs={'position':self._flagSpawnPos,'color':(1,1,1),
                                  'radius':0.3,'heightAttenuated':False})
        bs.animate(light,"intensity",{0:0,250:0.5,500:0},loop=True)
        bs.gameTimer(1000,light.delete)

    def _tick(self):

        # give the Frozen one points
        player = self._getFrozenOnePlayer()
        if player is not None:

            # this shouldnt happen, but just in case..
            if not player.isAlive():
                bs.printError('got dead player as Frozen one in _tick')
                self._setFrozenOnePlayer(None)
            else:
                scoringTeam = player.getTeam()
                self.scoreSet.playerScored(player,3,screenMessage=False,display=False)

                scoringTeam.gameData['timeRemaining'] = max(0,scoringTeam.gameData['timeRemaining']-1)

                # show the count over their head
                try:
                    if scoringTeam.gameData['timeRemaining'] > 0:
                        player.actor.setScoreText(str(scoringTeam.gameData['timeRemaining']))
                except Exception: pass
                   
                self._updateScoreBoard()

                # announce numbers we have sounds for
                try: bs.playSound(self._countDownSounds[scoringTeam.gameData['timeRemaining']])
                except Exception: pass

                # winner
                if scoringTeam.gameData['timeRemaining'] <= 0:
                    self.endGame()

        # player is None
        else:
            # this shouldnt happen, but just in case..
            # (Frozen-one player ceasing to exist should trigger onPlayerLeave which resets Frozen-one)
            if self._FrozenOnePlayer is not None:
                bs.printError('got nonexistant player as Frozen one in _tick')
                self._setFrozenOnePlayer(None)
                

    def endGame(self):
        results = bs.TeamGameResults()
        for team in self.teams: results.setTeamScore(team,self.settings['Frozen One Time'] - team.gameData['timeRemaining'])
        self.end(results=results,announceDelay=0)


    def _setFrozenOnePlayer(self,player):
        try:
            for p in self.players: p.gameData['FrozenLight'] = None
            bs.playSound(self._swipSound)
            if player is None or not player.exists():
                self._flag = bs.Flag(color=(1,0.9,0.2),
                                     position=self._flagSpawnPos,
                                     touchable=False)
                self._FrozenOnePlayer = None

                l = bs.newNode('light',
                               owner=self._flag.node,
                               attrs={'position': self._flagSpawnPos,
                                      'intensity':0.6,
                                      'heightAttenuated':False,
                                      'volumeIntensityScale':0.1,
                                      'radius':0.1,
                                      'color': (1.2,1.2,0.4)})

                self._flashFlagSpawn()
            else:
                if player.actor is not None:
                    self._flag = None
                    self._FrozenOnePlayer = player

                    if player.actor.node.exists():
                        if self.settings['Frozen One Gets Gloves']: player.actor.handleMessage(bs.PowerupMessage('punch'))

                        player.actor.frozen = True
                        player.actor.node.frozen = 1
                        # use a color that's partway between their team color and white
                        color = [0.3+c*0.7 for c in bs.getNormalizedColor(player.getTeam().color)]
                        l = player.gameData['FrozenLight'] = bs.NodeActor(bs.newNode('light',
                                                                                     attrs={"intensity":0.6,
                                                                                            "heightAttenuated":False,
                                                                                            "volumeIntensityScale":0.1,
                                                                                            "radius":0.13,
                                                                                            "color": color}))

                        bs.animate(l.node,'intensity',{0:1.0, 200:0.4, 400:1.0},loop=True)
                        player.actor.node.connectAttr('position',l.node,'position')
        except Exception,e:
            import traceback
            print 'EXC in _setFrozenOnePlayer'
            traceback.print_exc(e)
            traceback,print_stack()

    def handleMessage(self,m):
        if isinstance(m,bs.PlayerSpazDeathMessage):
            bs.TeamGameActivity.handleMessage(self,m) # augment standard behavior
            player = m.spaz.getPlayer()
            if player is self._getFrozenOnePlayer():
                killerPlayer = m.killerPlayer
                self._setFrozenOnePlayer(None if (killerPlayer is None or killerPlayer is player or not killerPlayer.isAlive()) else killerPlayer)
            self.respawnPlayer(player)
        else: bs.TeamGameActivity.handleMessage(self,m)

    def _updateScoreBoard(self):
        for team in self.teams:
            self._scoreBoard.setTeamValue(team,team.gameData['timeRemaining'],self.settings['Frozen One Time'],countdown=True)
