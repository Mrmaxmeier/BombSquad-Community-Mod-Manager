import bs
import random
import bsUtils
import bsPowerup

def bsGetAPIVersion():
    # see bombsquadgame.com/apichanges
    return 4

def bsGetGames():
    return [SurviveCurseGame]


class Icon(bs.Actor):
        
    def __init__(self,player,position,scale,showLives=True,showDeath=True,
                 nameScale=1.0,nameMaxWidth=115.0,flatness=1.0,shadow=1.0):
        bs.Actor.__init__(self)

        self._player = player
        self._showLives = showLives
        self._showDeath = showDeath
        self._nameScale = nameScale

        self._outlineTex = bs.getTexture('characterIconMask')
        
        icon = player.getIcon()
        self.node = bs.newNode('image',
                               owner=self,
                               attrs={'texture':icon['texture'],
                                      'tintTexture':icon['tintTexture'],
                                      'tintColor':icon['tintColor'],
                                      'vrDepth':400,
                                      'tint2Color':icon['tint2Color'],
                                      'maskTexture':self._outlineTex,
                                      'opacity':1.0,
                                      'absoluteScale':True,
                                      'attach':'bottomCenter'})
        self._nameText = bs.newNode('text',
                                    owner=self.node,
                                    attrs={'text':player.getName(),
                                           'color':bs.getSafeColor(player.getTeam().color),
                                           'hAlign':'center',
                                           'vAlign':'center',
                                           'vrDepth':410,
                                           'maxWidth':nameMaxWidth,
                                           'shadow':shadow,
                                           'flatness':flatness,
                                           'hAttach':'center',
                                           'vAttach':'bottom'})
        if self._showLives:
            self._livesText = bs.newNode('text',
                                         owner=self.node,
                                         attrs={'text':'x0',
                                                'color':(1,1,0.5),
                                                'hAlign':'left',
                                                'vrDepth':430,
                                                'shadow':1.0,
                                                'flatness':1.0,
                                                'hAttach':'center',
                                                'vAttach':'bottom'})
        self.setPositionAndScale(position,scale)

    def setPositionAndScale(self,position,scale):
        self.node.position = position
        self.node.scale = [70.0*scale]
        self._nameText.position = (position[0],position[1]+scale*52.0)
        self._nameText.scale = 1.0*scale*self._nameScale
        if self._showLives:
            self._livesText.position = (position[0]+scale*10.0,position[1]-scale*43.0)
            self._livesText.scale = 1.0*scale

    def updateForLives(self):
        if self._player.exists():
            lives = self._player.gameData['lives']
        else: lives = 0
        if self._showLives:
            if lives > 0: self._livesText.text = 'x'+str(lives-1)
            else: self._livesText.text = ''
        if lives == 0:
            self._nameText.opacity = 0.2
            self.node.color = (0.7,0.3,0.3)
            self.node.opacity = 0.2
        
    def handlePlayerSpawned(self):
        if not self.node.exists(): return
        self.node.opacity = 1.0
        self.updateForLives()

    def handlePlayerDied(self):
        if not self.node.exists(): return
        if self._showDeath:
            bs.animate(self.node,'opacity',{0:1.0,50:0.0,100:1.0,150:0.0,200:1.0,250:0.0,
                                            300:1.0,350:0.0,400:1.0,450:0.0,500:1.0,550:0.2})
            lives = self._player.gameData['lives']
            if lives == 0: bs.gameTimer(600,self.updateForLives)
        
class PlayerSpaz_Curse(bs.PlayerSpaz):
    minExplodeTime = 0
    curseDamageExplode = 350 #This is done to reduce likelihood of dying by damage. Normal curse is any damage at all.
    def onJumpPress(self):
        """
        Called to 'press jump' on this spaz;
        used by player or AI connections.
        This was just overridden to provide an easy way to get map extents.
        """
        if not self.node.exists(): return
        self.node.jumpPressed = True
        #print(self.node.position)
    def handleMessage(self,m):
        if isinstance(m,bs.PowerupMessage): #Have to handle powerups ourselves
            if self._dead: return True
            if self.pickUpPowerupCallback is not None:
                self.pickUpPowerupCallback(self)

            if (m.powerupType == 'health'):
                self.reCurse() #Just reset the curse timer
            elif (m.powerupType == 'curse'):
                self.curseExplodeNoShrapnel()
            self.node.handleMessage("flash")
            if m.sourceNode.exists():
                m.sourceNode.handleMessage(bs.PowerupAcceptMessage())
            return True
        elif isinstance(m,bs.HitMessage): #Have to override this whole message handling just to reduce chance of dying by damage while cursed
            if not self.node.exists(): return
            if self.node.invincible == True:
                bs.playSound(self.getFactory().blockSound,1.0,position=self.node.position)
                return True

            # if we were recently hit, don't count this as another
            # (so punch flurries and bomb pileups essentially count as 1 hit)
            gameTime = bs.getGameTime()
            if self._lastHitTime is None or gameTime-self._lastHitTime > 1000:
                self._numTimesHit += 1
                self._lastHitTime = gameTime
            
            mag = m.magnitude * self._impactScale
            velocityMag = m.velocityMagnitude * self._impactScale

            damageScale = 0.22

            # if they've got a shield, deliver it to that instead..
            if self.shield is not None:

                if m.flatDamage: damage = m.flatDamage * self._impactScale
                else:
                    # hit our spaz with an impulse but tell it to only return theoretical damage; not apply the impulse..
                    self.node.handleMessage("impulse",m.pos[0],m.pos[1],m.pos[2],
                                            m.velocity[0],m.velocity[1],m.velocity[2],
                                            mag,velocityMag,m.radius,1,m.forceDirection[0],m.forceDirection[1],m.forceDirection[2])
                    damage = damageScale * self.node.damage

                self.shieldHitPoints -= damage

                self.shield.hurt = 1.0 - float(self.shieldHitPoints)/self.shieldHitPointsMax
                # its a cleaner event if a hit just kills the shield without damaging the player..
                # however, massive damage events should still be able to damage the player..
                # this hopefully gives us a happy medium.
                # maxSpillover = 500
                maxSpillover = self.getFactory().maxShieldSpilloverDamage
                if self.shieldHitPoints <= 0:
                    # fixme - transition out perhaps?..
                    self.shield.delete()
                    self.shield = None
                    bs.playSound(self.getFactory().shieldDownSound,1.0,position=self.node.position)
                    # emit some cool lookin sparks when the shield dies
                    t = self.node.position
                    bs.emitBGDynamics(position=(t[0],t[1]+0.9,t[2]),
                                      velocity=self.node.velocity,
                                      count=random.randrange(20,30),scale=1.0,spread=0.6,chunkType='spark')

                else:
                    bs.playSound(self.getFactory().shieldHitSound,0.5,position=self.node.position)

                # emit some cool lookin sparks on shield hit
                bs.emitBGDynamics(position=m.pos,
                                  velocity=(m.forceDirection[0]*1.0,
                                            m.forceDirection[1]*1.0,
                                            m.forceDirection[2]*1.0),
                                  count=min(30,5+int(damage*0.005)),scale=0.5,spread=0.3,chunkType='spark')


                # if they passed our spillover threshold, pass damage along to spaz
                if self.shieldHitPoints <= -maxSpillover:
                    leftoverDamage = -maxSpillover-self.shieldHitPoints
                    shieldLeftoverRatio = leftoverDamage/damage

                    # scale down the magnitudes applied to spaz accordingly..
                    mag *= shieldLeftoverRatio
                    velocityMag *= shieldLeftoverRatio
                else:
                    return True # good job shield!
            else: shieldLeftoverRatio = 1.0

            if m.flatDamage:
                damage = m.flatDamage * self._impactScale * shieldLeftoverRatio
            else:
                # hit it with an impulse and get the resulting damage
                self.node.handleMessage("impulse",m.pos[0],m.pos[1],m.pos[2],
                                        m.velocity[0],m.velocity[1],m.velocity[2],
                                        mag,velocityMag,m.radius,0,m.forceDirection[0],m.forceDirection[1],m.forceDirection[2])

                damage = damageScale * self.node.damage
            self.node.handleMessage("hurtSound")

            # play punch impact sound based on damage if it was a punch
            if m.hitType == 'punch':

                self.onPunched(damage)

                # if damage was significant, lets show it
                if damage > 350: bsUtils.showDamageCount('-'+str(int(damage/10))+"%",m.pos,m.forceDirection)
                                               
                # lets always add in a super-punch sound with boxing gloves just to differentiate them
                if m.hitSubType == 'superPunch':
                    bs.playSound(self.getFactory().punchSoundStronger,1.0,
                                 position=self.node.position)

                if damage > 500:
                    sounds = self.getFactory().punchSoundsStrong
                    sound = sounds[random.randrange(len(sounds))]
                else: sound = self.getFactory().punchSound
                bs.playSound(sound,1.0,position=self.node.position)

                # throw up some chunks
                bs.emitBGDynamics(position=m.pos,
                                  velocity=(m.forceDirection[0]*0.5,
                                            m.forceDirection[1]*0.5,
                                            m.forceDirection[2]*0.5),
                                  count=min(10,1+int(damage*0.0025)),scale=0.3,spread=0.03);

                bs.emitBGDynamics(position=m.pos,
                                  chunkType='sweat',
                                  velocity=(m.forceDirection[0]*1.3,
                                            m.forceDirection[1]*1.3+5.0,
                                            m.forceDirection[2]*1.3),
                                  count=min(30,1+int(damage*0.04)),
                                  scale=0.9,
                                  spread=0.28);
                # momentary flash
                hurtiness = damage*0.003
                punchPos = (m.pos[0]+m.forceDirection[0]*0.02,
                            m.pos[1]+m.forceDirection[1]*0.02,
                            m.pos[2]+m.forceDirection[2]*0.02)
                flashColor = (1.0,0.8,0.4)
                light = bs.newNode("light",
                                   attrs={'position':punchPos,
                                          'radius':0.12+hurtiness*0.12,
                                          'intensity':0.3*(1.0+1.0*hurtiness),
                                          'heightAttenuated':False,
                                          'color':flashColor})
                bs.gameTimer(60,light.delete)


                flash = bs.newNode("flash",
                                   attrs={'position':punchPos,
                                          'size':0.17+0.17*hurtiness,
                                          'color':flashColor})
                bs.gameTimer(60,flash.delete)

            if m.hitType == 'impact':
                bs.emitBGDynamics(position=m.pos,
                                  velocity=(m.forceDirection[0]*2.0,
                                            m.forceDirection[1]*2.0,
                                            m.forceDirection[2]*2.0),
                                  count=min(10,1+int(damage*0.01)),scale=0.4,spread=0.1);
                
            if self.hitPoints > 0:

                # its kinda crappy to die from impacts, so lets reduce impact damage
                # by a reasonable amount if it'll keep us alive
                if m.hitType == 'impact' and damage > self.hitPoints:
                    # drop damage to whatever puts us at 10 hit points, or 200 less than it used to be
                    # whichever is greater (so it *can* still kill us if its high enough)
                    newDamage = max(damage-200,self.hitPoints-10)
                    damage = newDamage

                self.node.handleMessage("flash")
                # if we're holding something, drop it
                if damage > 0.0 and self.node.holdNode.exists():
                    self.node.holdNode = bs.Node(None)
                self.hitPoints -= damage
                self.node.hurt = 1.0 - float(self.hitPoints)/self.hitPointsMax
                # if we're cursed, *any* damage blows us up
                if self._cursed and damage > self.curseDamageExplode:
                    bs.gameTimer(50,bs.WeakCall(self.curseExplode,m.sourcePlayer))
                # if we're frozen, shatter.. otherwise die if we hit zero
                if self.frozen and (damage > 200 or self.hitPoints <= 0):
                    self.shatter()
                elif self.hitPoints <= 0:
                    self.node.handleMessage(bs.DieMessage(how='impact'))

            # if we're dead, take a look at the smoothed damage val
            # (which gives us a smoothed average of recent damage) and shatter
            # us if its grown high enough
            if self.hitPoints <= 0:
                damageAvg = self.node.damageSmoothed * damageScale
                if damageAvg > 1000:
                    self.shatter()
        else:
            super(self.__class__, self).handleMessage(m)
    def reCurse(self):
        self.node.curseDeathTime = bs.getGameTime()+5000
        bs.gameTimer(5000,bs.WeakCall(self.curseExplodeIfNotReset))
    
    def curse(self):
        """
        Give this poor spaz a curse;
        he will explode in 5 seconds.
        We have to override this from the parent class to allow
        for resetting the curse timing.  Changed the WeakCall at the end
        to curseExplodeIfNotReset instead of straight curseExplode.
        """
        if not self._cursed:
            factory = self.getFactory()
            self._cursed = True
            # add the curse material..
            for attr in ['materials','rollerMaterials']:
                materials = getattr(self.node,attr)
                if not factory.curseMaterial in materials:
                    setattr(self.node,attr,materials + (factory.curseMaterial,))

            # -1 specifies no time limit
            if self.curseTime == -1:
                self.node.curseDeathTime = -1
            else:
                self.node.curseDeathTime = bs.getGameTime()+5000
                bs.gameTimer(5000,bs.WeakCall(self.curseExplodeIfNotReset))
                
    def curseExplodeIfNotReset(self):
        if self.node.exists():
            if self.node.curseDeathTime <= bs.getGameTime():
                self.curseExplodeNoShrapnel()
    def curseExplodeNoShrapnel(self,sourcePlayer=None):
        """
        Explode the poor spaz as happens when
        a curse timer runs out. Less shrapnel for surviveCurse, just explode.
        Otherwise, shrapnel hits other players too much. Player shrapnel causes instant
        curse explosion of other players.  Over too quickly.
        I could probably figure out how to prevent.  However, too lazy.
        Making immediate=True in the DieMessage prevents shrapnel. 
        However, spaz node disappears instantly and no cleanup happens.
        """
        # convert None to an empty player-ref
        if sourcePlayer is None: sourcePlayer = bs.Player(None)
        
        if self._cursed and self.node.exists():
            #self.shatter(extreme=True)
            self.handleMessage(bs.DieMessage(immediate=False))
            activity = self._activity()
            if activity:
                bs.Blast(position=self.node.position,
                         velocity=self.node.velocity,
                         blastRadius=3.0,blastType='normal',
                         sourcePlayer=sourcePlayer if sourcePlayer.exists() else self.sourcePlayer).autoRetain()
            self._cursed = False            
        
class SurviveCurseGame(bs.TeamGameActivity):

    @classmethod
    def getName(cls):
        return 'Survive the Curse!'

    @classmethod
    def getScoreInfo(cls):
        return {'scoreName':'Survived',
                'scoreType':'seconds',
                'noneIsWinner':True}
    
    @classmethod
    def getDescription(cls,sessionType):
        return 'Last remaining alive wins.'

    @classmethod
    def supportsSessionType(cls,sessionType):
        return True if (issubclass(sessionType,bs.TeamsSession)
                        or issubclass(sessionType,bs.FreeForAllSession)) else False

    @classmethod
    def getSupportedMaps(cls,sessionType):
        return ['Doom Shroom', 'Rampage', 'Hockey Stadium', 'Courtyard', 'Crag Castle', 'Big G', 'Football Stadium']

    @classmethod
    def getSettings(cls,sessionType):
        settings = [("Lives Per Player",{'default':1,'minValue':1,'maxValue':1,'increment':1}),
                    ("Time Limit",{'choices':[('None',0),('1 Minute',60),
                                            ('2 Minutes',120),('5 Minutes',300),
                                            ('10 Minutes',600),('20 Minutes',1200)],'default':0}),
                    ("Respawn Times",{'choices':[('Shorter',0.25),('Short',0.5),('Normal',1.0),('Long',2.0),('Longer',4.0)],'default':1.0}),
                    ("Box Reduction Rate",{'choices':[('Faster',0.1),('Fast',0.07),('Normal',0.05),('Slow',0.03),('Slower',0.01)],'default':0.05}),
                    ("Curse Box Chance (lower = more chance)",{'default':10,'minValue':5,'maxValue':15,'increment':1}),
                    ("Epic Mode",{'default':False})]

        if issubclass(sessionType,bs.TeamsSession):
            settings.append(("Solo Mode",{'default':False}))
            settings.append(("Balance Total Lives",{'default':False}))
            
        return settings

    def __init__(self,settings):
        bs.TeamGameActivity.__init__(self,settings)
        if self.settings['Epic Mode']: self._isSlowMotion = True

        # show messages when players die since it's meaningful here
        self.announcePlayerDeaths = True
        
        try: self._soloMode = settings['Solo Mode']
        except Exception: self._soloMode = False
        self._scoreBoard = bs.ScoreBoard()

    def getInstanceDescription(self):
        return 'Last team standing wins.' if isinstance(self.getSession(),bs.TeamsSession) else 'Last one standing wins.'

    def getInstanceScoreBoardDescription(self):
        return 'last team standing wins' if isinstance(self.getSession(),bs.TeamsSession) else 'last one standing wins'

    def onTransitionIn(self):
        bs.TeamGameActivity.onTransitionIn(self, music='Epic' if self.settings['Epic Mode'] else 'Survival')
        self._startGameTime = bs.getGameTime()

    def onTeamJoin(self,team):
        team.gameData['survivalSeconds'] = None
        team.gameData['spawnOrder'] = []

    def onPlayerJoin(self, player):

        # no longer allowing mid-game joiners here... too easy to exploit
        if self.hasBegun():
            player.gameData['lives'] = 0
            player.gameData['icons'] = []
            # make sure our team has survival seconds set if they're all dead
            # (otherwise blocked new ffa players would be considered 'still alive' in score tallying)
            if self._getTotalTeamLives(player.getTeam()) == 0 and player.getTeam().gameData['survivalSeconds'] is None:
                player.getTeam().gameData['survivalSeconds'] = 0
            bs.screenMessage(bs.Lstr(resource='playerDelayedJoinText',subs=[('${PLAYER}',player.getName(full=True))]),color=(0,1,0))
            return
        
        player.gameData['lives'] = self.settings['Lives Per Player']

        if self._soloMode:
            player.gameData['icons'] = []
            player.getTeam().gameData['spawnOrder'].append(player)
            self._updateSoloMode()
        else:
            # create our icon and spawn
            player.gameData['icons'] = [Icon(player,position=(0,50),scale=0.8)]
            if player.gameData['lives'] > 0:
                self.spawnPlayer(player)

        # dont waste time doing this until begin
        if self.hasBegun():
            self._updateIcons()

    def _updateSoloMode(self):
        # for both teams, find the first player on the spawn order list with lives remaining
        # and spawn them if they're not alive
        for team in self.teams:
            # prune dead players from the spawn order
            team.gameData['spawnOrder'] = [p for p in team.gameData['spawnOrder'] if p.exists()]
            for player in team.gameData['spawnOrder']:
                if player.gameData['lives'] > 0:
                    if not player.isAlive(): self.spawnPlayer(player)
                    break

    def _updateIcons(self):
        # in free-for-all mode, everyone is just lined up along the bottom
        if isinstance(self.getSession(),bs.FreeForAllSession):
            count = len(self.teams)
            xOffs = 85
            x = xOffs*(count-1) * -0.5
            for i,team in enumerate(self.teams):
                if len(team.players) == 1:
                    player = team.players[0]
                    for icon in player.gameData['icons']:
                        icon.setPositionAndScale((x,30),0.7)
                        icon.updateForLives()
                    x += xOffs

        # in teams mode we split up teams
        else:
            if self._soloMode:
                # first off, clear out all icons
                for player in self.players:
                    player.gameData['icons'] = []
                # now for each team, cycle through our available players adding icons
                for team in self.teams:
                    if team.getID() == 0:
                        x = -60
                        xOffs = -78
                    else:
                        x = 60
                        xOffs = 78
                    isFirst = True
                    testLives = 1
                    while True:
                        playersWithLives = [p for p in team.gameData['spawnOrder'] if p.exists() and p.gameData['lives'] >= testLives]
                        if len(playersWithLives) == 0: break
                        for player in playersWithLives:
                            player.gameData['icons'].append(Icon(player,
                                                                 position=(x,(40 if isFirst else 25)),
                                                                 scale=1.0 if isFirst else 0.5,
                                                                 nameMaxWidth=130 if isFirst else 75,
                                                                 nameScale=0.8 if isFirst else 1.0,
                                                                 flatness=0.0 if isFirst else 1.0,
                                                                 shadow=0.5 if isFirst else 1.0,
                                                                 showDeath=True if isFirst else False,
                                                                 showLives=False))
                            x += xOffs * (0.8 if isFirst else 0.56)
                            isFirst = False
                        testLives += 1
            # non-solo mode
            else:
                for team in self.teams:
                    if team.getID() == 0:
                        x = -50
                        xOffs = -85
                    else:
                        x = 50
                        xOffs = 85
                    for player in team.players:
                        for icon in player.gameData['icons']:
                            icon.setPositionAndScale((x,30),0.7)
                            icon.updateForLives()
                        x += xOffs
                    
    def _getSpawnPoint(self,player):
        # in solo-mode, if there's an existing live player on the map, spawn at whichever
        # spot is farthest from them (keeps the action spread out)
        if self._soloMode:
            livingPlayer = None
            for team in self.teams:
                for player in team.players:
                    if player.isAlive():
                        p = player.actor.node.position
                        livingPlayer = player
                        livingPlayerPos = p
                        break
            if livingPlayer:
                playerPos = bs.Vector(*livingPlayerPos)
                points = []
                for team in self.teams:
                    startPos = bs.Vector(*self.getMap().getStartPosition(team.getID()))
                    points.append([(startPos-playerPos).length(),startPos])
                points.sort()
                return points[-1][1]
            else:
                return None
        else:
            return None

        
    def spawnPlayer(self,player):
        self.spawnPlayerSpaz(player,self._getSpawnPoint(player))
        if not self._soloMode:
            bs.gameTimer(300,bs.Call(self._printLives,player))

        # if we have any icons, update their state
        for icon in player.gameData['icons']:
            icon.handlePlayerSpawned()
            
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
        spaz = PlayerSpaz_Curse(color=color,
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
        spaz.connectControlsToPlayer()
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
        
    def _printLives(self,player):
        if not player.exists() or not player.isAlive(): return
        try: pos = player.actor.node.position
        except Exception,e:
            print 'EXC getting player pos in bsElim',e
            return
        bs.PopupText('x'+str(player.gameData['lives']-1),color=(1,1,0,1),
                           offset=(0,-0.8,0),randomOffset=0.0,scale=1.8,position=pos).autoRetain()

    def onPlayerLeave(self,player):

        bs.TeamGameActivity.onPlayerLeave(self,player)

        player.gameData['icons'] = None

        # remove us from spawn-order
        if self._soloMode:
            if player in player.getTeam().gameData['spawnOrder']:
                player.getTeam().gameData['spawnOrder'].remove(player)

        # update icons in a moment since our team will be gone from the list then
        bs.gameTimer(0, self._updateIcons)


    def onBegin(self):
        bs.TeamGameActivity.onBegin(self)
        self.setupStandardTimeLimit(self.settings['Time Limit'])
        #self.setupStandardPowerupDrops() #No standard powerups.  We'll drop 'em from the sky.

        if self._soloMode:
            self._vsText = bs.NodeActor(bs.newNode("text",
                                                   attrs={'position':(0,105),
                                                          'hAttach':"center",
                                                          'hAlign':'center',
                                                          'maxWidth':200,
                                                          'shadow':0.5,
                                                          'vrDepth':390,
                                                          'scale':0.6,
                                                          'vAttach':"bottom",
                                                          'color':(0.8,0.8,0.3,1.0),
                                                          'text':bs.Lstr(resource='vsText')}))

        # if balance-team-lives is on, add lives to the smaller team until total lives match
        if (isinstance(self.getSession(),bs.TeamsSession)
            and self.settings['Balance Total Lives']
            and len(self.teams[0].players) > 0
            and len(self.teams[1].players) > 0):
            if self._getTotalTeamLives(self.teams[0]) < self._getTotalTeamLives(self.teams[1]):
                lesserTeam = self.teams[0]
                greaterTeam = self.teams[1]
            else:
                lesserTeam = self.teams[1]
                greaterTeam = self.teams[0]
            addIndex = 0
            while self._getTotalTeamLives(lesserTeam) < self._getTotalTeamLives(greaterTeam):
                lesserTeam.players[addIndex].gameData['lives'] += 1
                addIndex = (addIndex + 1) % len(lesserTeam.players)

        self._updateIcons()
        for pName in self.scoreSet._players:
            spz = self.scoreSet._players[pName].getSpaz()
            if not spz is None:
                bs.gameTimer(1500,bs.WeakCall(spz.curse)) #Curse you all!
            
        #bsPowerup.Powerup(position=self.getMap().powerupSpawnPoints[0], powerupType='health',expire=False).autoRetain()
        #bsPowerup.Powerup(position=self.getMap().powerupSpawnPoints[1], powerupType='curse',expire=False).autoRetain()
        #bsPowerup.Powerup(position=self.getMap().powerupSpawnPoints[3], powerupType='health',expire=False).autoRetain()
        #bsPowerup.Powerup(position=self.getMap().powerupSpawnPoints[2], powerupType='curse',expire=False).autoRetain()
        self.boxMult = 4.0
        self.totBoxes = []
        self.boxSpawn()
        # we could check game-over conditions at explicit trigger points,
        # but lets just do the simple thing and poll it...
        bs.gameTimer(1000, self._update, repeat=True)
        
        
    def _getTotalTeamLives(self,team):
        return sum(player.gameData['lives'] for player in team.players)
        

        
    def handleMessage(self,m):
        if isinstance(m,bs.PlayerSpazDeathMessage):
            
            bs.TeamGameActivity.handleMessage(self, m) # augment standard behavior
            player = m.spaz.getPlayer()

            player.gameData['lives'] -= 1
            if player.gameData['lives'] < 0:
                bs.printError('Got lives < 0 in Elim; this shouldnt happen. solo:'+str(self._soloMode))
                player.gameData['lives'] = 0

            # if we have any icons, update their state
            for icon in player.gameData['icons']:
                icon.handlePlayerDied()

            # play big death sound on our last death or for every one in solo mode
            if self._soloMode or player.gameData['lives'] == 0:
                bs.playSound(bs.Spaz.getFactory().singlePlayerDeathSound)

            # if we hit zero lives, we're dead (and our team might be too)
            if player.gameData['lives'] == 0:
                # if the whole team is now dead, mark their survival time..
                #if all(teammate.gameData['lives'] == 0 for teammate in player.getTeam().players):
                if self._getTotalTeamLives(player.getTeam()) == 0:
                    player.getTeam().gameData['survivalSeconds'] = (bs.getGameTime()-self._startGameTime)/1000
            else:
                # otherwise, in regular mode, respawn..
                if not self._soloMode:
                    self.respawnPlayer(player)

            # in solo, put ourself at the back of the spawn order
            if self._soloMode:
                player.getTeam().gameData['spawnOrder'].remove(player)
                player.getTeam().gameData['spawnOrder'].append(player)
                
    def boxSpawn(self):
        Plyrs = 0
        for team in self.teams:
            for player in team.players:
                if player.gameData['lives'] > 0:
                    Plyrs += 1
                    
        maxBoxes = Plyrs * self.boxMult
        if maxBoxes > 16:
            maxBoxes = 16
        for box in self.totBoxes:
            if not box.exists():
                self.totBoxes.remove(box)
        while len(self.totBoxes) < maxBoxes:
            #print([Plyrs, self.boxMult,len(self.totBoxes), maxBoxes])
            if random.randint(1,self.settings["Curse Box Chance (lower = more chance)"]) == 1:
                self.totBoxes.append(bsPowerup.Powerup(position=self.getRandomPowerupPoint(), powerupType='curse',expire=False).autoRetain())
            else:
                self.totBoxes.append(bsPowerup.Powerup(position=self.getRandomPowerupPoint(), powerupType='health',expire=False).autoRetain())
        self.boxMult -= self.settings["Box Reduction Rate"]
        
    def getRandomPowerupPoint(self):
        #So far, randomized points only figured out for mostly rectangular maps.
        #Boxes will still fall through holes, but shouldn't be terrible problem (hopefully)
        #If you add stuff here, need to add to "supported maps" above.
        #['Doom Shroom', 'Rampage', 'Hockey Stadium', 'Courtyard', 'Crag Castle', 'Big G', 'Football Stadium']
        myMap = self.getMap().getName()
        #print(myMap)
        if myMap == 'Doom Shroom':
            while True:
                x = random.uniform(-1.0,1.0)
                y = random.uniform(-1.0,1.0)
                if x*x+y*y < 1.0: break
            return ((8.0*x,8.0,-3.5+5.0*y))
        elif myMap == 'Rampage':
            x = random.uniform(-6.0,7.0)
            y = random.uniform(-6.0,-2.5)
            return ((x, 8.0, y))
        elif myMap == 'Hockey Stadium':
            x = random.uniform(-11.5,11.5)
            y = random.uniform(-4.5,4.5)
            return ((x, 5.0, y))
        elif myMap == 'Courtyard':
            x = random.uniform(-4.3,4.3)
            y = random.uniform(-4.4,0.3)
            return ((x, 8.0, y))
        elif myMap == 'Crag Castle':
            x = random.uniform(-6.7,8.0)
            y = random.uniform(-6.0,0.0)
            return ((x, 12.0, y))
        elif myMap == 'Big G':
            x = random.uniform(-8.7,8.0)
            y = random.uniform(-7.5,6.5)
            return ((x, 8.0, y))
        elif myMap == 'Football Stadium':
            x = random.uniform(-12.5,12.5)
            y = random.uniform(-5.0,5.5)
            return ((x, 8.0, y))
        else:
            x = random.uniform(-5.0,5.0)
            y = random.uniform(-6.0,0.0)
            return ((x, 8.0, y))
    def _update(self):

        if self._soloMode:
            # for both teams, find the first player on the spawn order list with lives remaining
            # and spawn them if they're not alive
            for team in self.teams:
                # prune dead players from the spawn order
                team.gameData['spawnOrder'] = [p for p in team.gameData['spawnOrder'] if p.exists()]
                for player in team.gameData['spawnOrder']:
                    if player.gameData['lives'] > 0:
                        if not player.isAlive():
                            self.spawnPlayer(player)
                            self._updateIcons()
                        break
        
        # if we're down to 1 or fewer living teams, start a timer to end the game
        # (allows the dust to settle and draws to occur if deaths are close enough)
        self.boxSpawn()
        if len(self._getLivingTeams()) < 2:
            self._roundEndTimer = bs.Timer(500,self.endGame)


    def _getLivingTeams(self):
        return [team for team in self.teams if len(team.players) > 0 and any(player.gameData['lives'] > 0 for player in team.players)]

    def endGame(self):
        if self.hasEnded(): return
        results = bs.TeamGameResults()
        self._vsText = None # kill our 'vs' if its there
        for team in self.teams:
            results.setTeamScore(team, team.gameData['survivalSeconds'])
        self.end(results=results)
        
