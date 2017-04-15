import bs
import random
import bsUtils
import bsPowerup
from bsSpaz import PlayerSpazHurtMessage

def bsGetAPIVersion():
    # see bombsquadgame.com/apichanges
    return 4

def bsGetGames():
    return [Greed]
        
class PlayerSpaz_Greed(bs.PlayerSpaz):
    def handleMessage(self, m):
        #print(m)

        #First we copy handling from PlayerSpaz, then almost the whole HitMessage handling from bsSpaz, but just to calculate the "damage".
        if isinstance(m,bs.HitMessage):
            #Damage is calculated in the bsSpaz message handling, which happens
            #after the PlayerSpaz message handling.  Here we have to pull the code
            #from PlayerSpaz in order to give kill credit (and avoid suicide), then the code from Spaz. 
            if m.sourcePlayer is not None and m.sourcePlayer.exists():
                self.lastPlayerAttackedBy = m.sourcePlayer
                self.lastAttackedTime = bs.getGameTime()
                self.lastAttackedType = (m.hitType,m.hitSubType)
            #self.__superHandleMessage(m) # augment standard behavior #super is not needed anymore due to being copied here below
            activity = self._activity()
            if activity is not None:
                activity.handleMessage(PlayerSpazHurtMessage(self))
            #End of code from bsPlayerSpaz
            #Now the code from bsSpaz
            boxDamage = 0
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
                #################################
                boxDamage = damage
                if bs.getActivity().settings['Hits damage players']:
                    if damage > self.hitPoints:
                        boxDamage = self.hitPoints  #Only take boxes for the remaining health
                        if boxDamage < 0:
                            boxDamage = 0 #might be hitting a corpse
                    self.hitPoints -= damage  #Only take hit points for damage if settings allow
                    self.node.hurt = 1.0 - float(self.hitPoints)/self.hitPointsMax
                # if we're cursed, *any* damage blows us up
                if self._cursed and damage > 0:
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
            
            #Now calculate the number of boxes to spew.  Idea is to spew half of boxes if damage is 1000 (basically one0shot kill)
            player = self.getPlayer()
            if player.exists(): #Don't spew boxes for hitting a corpse!
                ptot = 0
                for p2 in player.getTeam().players:
                    if p2.exists():
                        ptot +=1
                if (player.getTeam().gameData['score']/ptot <= 2) and boxDamage >= 800:
                    boxes = 1
                else:
                    boxes = int(player.getTeam().gameData['score']/ptot  * boxDamage / 2000)
                if boxes >= player.getTeam().gameData['score']: #somehow the team loses more than all theri boxes?
                    boxes = player.getTeam().gameData['score']
                #print([damage, boxes])
                if boxes > 0:
                    player.getTeam().gameData['score'] -= boxes
                    self.setScoreText(str(player.getTeam().gameData['score']), player.color)
                    bs.gameTimer(50,bs.WeakCall(self.getActivity().spewBoxes,self.node.position, boxes))
                    if player.getTeam().gameData['score'] == 0:
                        self.handleMessage(bs.DieMessage())
                    self.getActivity()._updateScoreBoard()
            return    
        if isinstance(m,bs.PowerupMessage): #Have to handle health powerups ourselves
            if m.powerupType == 'health':
                if self._dead: return True
                if self.pickUpPowerupCallback is not None:
                    self.pickUpPowerupCallback(self)
                player = self.getPlayer()
                if player.exists():
                    player.getTeam().gameData['score'] += 1 
                    self.getActivity()._updateScoreBoard()
                    self.setScoreText(str(player.getTeam().gameData['score']), player.color)
                self.node.handleMessage("flash")
                if m.sourceNode.exists():
                    m.sourceNode.handleMessage(bs.PowerupAcceptMessage())
                return True
            else:
                super(self.__class__, self).handleMessage(m)
        else:
            super(self.__class__, self).handleMessage(m)
            
class Greed(bs.TeamGameActivity):

    @classmethod
    def getName(cls):
        return 'Greed'

    @classmethod
    def getScoreInfo(cls):
        return {'scoreName':'score',
                'scoreType':'points',
                'noneIsWinner':False,
                'lowerIsBetter':False}
    
    @classmethod
    def getDescription(cls,sessionType):
        return 'Steal all the health boxes for yourself'

    @classmethod
    def supportsSessionType(cls,sessionType):
        return True if (issubclass(sessionType,bs.TeamsSession)
                        or issubclass(sessionType,bs.FreeForAllSession)) else False

    @classmethod
    def getSupportedMaps(cls,sessionType):
        return bs.getMapsSupportingPlayType("melee")

    @classmethod
    def getSettings(cls,sessionType):
        settings = [("Time Limit",{'choices':[('30 Seconds',30),('1 Minute',60),
                                            ('90 Seconds',90),('2 Minutes',120),
                                            ('3 Minutes',180),('5 Minutes',300)],'default':60}),
                    ("Respawn Times",{'choices':[('Shorter',0.25),('Short',0.5),('Normal',1.0),('Long',2.0),('Longer',4.0)],'default':1.0}),
                    ("Starting Points", {'default':10,'minValue':5, 'maxValue':50,'increment':5}),
                    ("Gloves:",{'choices':[('Everyone',1),('Spawn',2),('None',3)],'default':3}),
                    ("Hits damage players",{'default':True}),
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
        return 'Steal all the health boxes for yourself' if isinstance(self.getSession(),bs.TeamsSession) else 'Steal all the health boxes for yourself'

    def getInstanceScoreBoardDescription(self):
        return 'Steal all the health boxes for yourself' if isinstance(self.getSession(),bs.TeamsSession) else 'Steal all the health boxes for yourself'

    def onTransitionIn(self):
        bs.TeamGameActivity.onTransitionIn(self, music='Epic' if self.settings['Epic Mode'] else 'Survival')
        self._startGameTime = bs.getGameTime()

    def onTeamJoin(self,team):
        team.gameData['survivalSeconds'] = None
        team.gameData['spawnOrder'] = []
        team.gameData['score'] = 0


    def onPlayerJoin(self, player):

        # no longer allowing mid-game joiners here... too easy to exploit
        if self.hasBegun():
            player.gameData['lives'] = 0
            player.gameData['icons'] = []
            # make sure our team has survival seconds set if they're all dead
            # (otherwise blocked new ffa players would be considered 'still alive' in score tallying)
            if self._getTotalTeamLives(player.getTeam()) == 0 and player.getTeam().gameData['survivalSeconds'] is None:
                player.getTeam().gameData['survivalSeconds'] = 1000
            bs.screenMessage(bs.Lstr(resource='playerDelayedJoinText',subs=[('${PLAYER}',player.getName(full=True))]),color=(0,1,0))
            return
        player.gameData['lives'] = 1
        player.getTeam().gameData['score'] = self.settings['Starting Points']
        self._updateScoreBoard()
        
        if self._soloMode:
            #player.gameData['icons'] = []
            player.getTeam().gameData['spawnOrder'].append(player)
            self._updateSoloMode()
        else:
            # create our icon and spawn
            #player.gameData['icons'] = [Icon(player,position=(0,50),scale=0.8)]
            if player.gameData['lives'] > 0:
                self.spawnPlayer(player)

        # dont waste time doing this until begin
        if self.hasBegun():
            pass#self._updateIcons()

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
        """This next line is the default spawn line. But we need to spawn our special guy"""
        #self.spawnPlayerSpaz(player,self._getSpawnPoint(player))
        #position = self._getSpawnPoint(player)
        #if isinstance(self.getSession(), bs.TeamsSession):
        #    position = self.getMap().getStartPosition(player.getTeam().getID())
        #else:
        #	# otherwise do free-for-all spawn locations
        position = self.getMap().getFFAStartPosition(self.players)

        angle = 20


        #spaz = self.spawnPlayerSpaz(player)

        # lets reconnect this player's controls to this
        # spaz but *without* the ability to attack or pick stuff up
        #spaz.connectControlsToPlayer(enablePunch=False,
        #							 enableBomb=False,
        #							 enablePickUp=False)

        # also lets have them make some noise when they die..
        #spaz.playBigDeathSound = True

        name = player.getName()

        lightColor = bsUtils.getNormalizedColor(player.color)
        displayColor = bs.getSafeColor(player.color, targetIntensity=0.75)

        spaz = PlayerSpaz_Greed(color=player.color,
                             highlight=player.highlight,
                             character=player.character,
                             player=player)
        player.setActor(spaz)
        # we want a bigger area-of-interest in co-op mode
        # if isinstance(self.getSession(),bs.CoopSession): spaz.node.areaOfInterestRadius = 5.0
        # else: spaz.node.areaOfInterestRadius = 5.0

        # if this is co-op and we're on Courtyard or Runaround, add the material that allows us to
        # collide with the player-walls
        # FIXME; need to generalize this
        if isinstance(self.getSession(), bs.CoopSession) and self.getMap().getName() in ['Courtyard', 'Tower D']:
            mat = self.getMap().preloadData['collideWithWallMaterial']
            spaz.node.materials += (mat,)
            spaz.node.rollerMaterials += (mat,)

        spaz.node.name = name
        spaz.node.nameColor = displayColor
        spaz.connectControlsToPlayer()
        self.scoreSet.playerGotNewSpaz(player, spaz)

        # move to the stand position and add a flash of light
        spaz.handleMessage(bs.StandMessage(position, angle if angle is not None else random.uniform(0, 360)))
        t = bs.getGameTime()
        bs.playSound(self._spawnSound, 1, position=spaz.node.position)
        light = bs.newNode('light', attrs={'color': lightColor})
        spaz.node.connectAttr('position', light, 'position')
        bsUtils.animate(light, 'intensity', {0: 0, 250: 1, 500: 0})
        bs.gameTimer(500, light.delete)
        #Start code to spawn special guy:
        #End of code to spawn special guy
        if not self._soloMode:
            bs.gameTimer(1000,bs.WeakCall(self.updateSpazScore, player,spaz), repeat=True)
            #spaz.setScoreText(str(player.getTeam().gameData['score']), player.color)
        if self.settings['Gloves:'] == 1:
            spaz.equipBoxingGloves()    
        # if we have any icons, update their state
        #for icon in player.gameData['icons']:
        #    icon.handlePlayerSpawned()
        
    def updateSpazScore(self,player,spaz):
        if player.isAlive():
            if spaz.isAlive():
                spaz.setScoreText(str(player.getTeam().gameData['score']), player.color)

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

        #player.gameData['icons'] = None
        player.gameData['score'] = 0

        # remove us from spawn-order
        if self._soloMode:
            if player in player.getTeam().gameData['spawnOrder']:
                player.getTeam().gameData['spawnOrder'].remove(player)

        # update icons in a moment since our team will be gone from the list then
        #bs.gameTimer(0, self._updateIcons)


    def onBegin(self):
        bs.TeamGameActivity.onBegin(self)
        self.setupStandardTimeLimit(self.settings['Time Limit'])
        self.setupStandardPowerupDrops()

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
        self.excludePowerups = ['health','iceBombs','curse']
        if self.settings['Gloves:'] == 3:
            self.excludePowerups.append('punch')
        #self._updateIcons()

        # we could check game-over conditions at explicit trigger points,
        # but lets just do the simple thing and poll it...
        bs.gameTimer(1000, self._update, repeat=True)
        
    def _getTotalTeamLives(self,team):
        return sum(player.gameData['lives'] for player in team.players)

    def handleMessage(self,m):
        if isinstance(m,bs.PlayerSpazDeathMessage):
            bs.TeamGameActivity.handleMessage(self, m) # augment standard behavior
            player = m.spaz.getPlayer()
            if m.killerPlayer == player:
                player.getTeam().gameData['score'] /= 2
                self._updateScoreBoard()
            #print([player, m.spaz.hitPoints, "killed by", m.killerPlayer])
            if player.getTeam().gameData['score'] == 0: #Only permadeath if they lost all their boxes.
                player.gameData['lives'] -= 1
                
            if player.gameData['lives'] < 0:
                bs.printError('Got lives < 0 in Elim; this shouldnt happen. solo:'+str(self._soloMode))
                player.gameData['lives'] = 0

            # if we have any icons, update their state
            #for icon in player.gameData['icons']:
            #    icon.handlePlayerDied()

            # play big death sound on our last death or for every one in solo mode
            if self._soloMode or player.gameData['lives'] == 0:
                bs.playSound(bs.Spaz.getFactory().singlePlayerDeathSound)

            # if we hit zero lives, we're dead (and our whole team is too, since 0 boxes left)
            if player.gameData['lives'] == 0:
                pass
                # if the whole team is now dead, mark their survival time..
                #if all(teammate.gameData['lives'] == 0 for teammate in player.getTeam().players):
                #if self._getTotalTeamLives(player.getTeam()) == 0:
                #    player.getTeam().gameData['survivalSeconds'] = (bs.getGameTime()-self._startGameTime)/1000
                #for p2 in player.getTeam().players:
                #    p2.gameData['lives'] = 0
                #    self.scoreSet._players[player.getName()].getSpaz().handleMessage(bs.DieMessage())
            else:
                # otherwise, in regular mode, respawn..
                if not self._soloMode:
                    self.respawnPlayer(player)

            # in solo, put ourself at the back of the spawn order
            if self._soloMode:
                player.getTeam().gameData['spawnOrder'].remove(player)
                player.getTeam().gameData['spawnOrder'].append(player)
        else:
            bs.TeamGameActivity.handleMessage(self, m)
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
                            #self._updateIcons()
                        break
        
        # if we're down to 1 or fewer living teams, start a timer to end the game
        # (allows the dust to settle and draws to occur if deaths are close enough)
        if (len(self._getLivingTeams()) < 2):
            self._roundEndTimer = bs.Timer(500,self.endGame)
            
    def spewBoxes(self, pos, boxes):
        p2 = list(pos)
        p2[1] += 1
        for n in range(0,boxes):
            #print(["spewbox", [p2[0], p2[1] + 1.5 + (x*0.4), p2[2]]])
            #Let's create a spiral, just for fun
            gap = 0.1
            x=gap*float(n+2)*((-1.0)**float(int((n % 4)/2)))
            #x = (-1.0)^float(3)
            y=gap*float(n+2)*((-1.0)**float(int((n + 1 % 4)/2)))
            bs.gameTimer(int((1+n)*25), bs.Call(self.spewWithTimer, [p2[0]+x, p2[1] + 1.0 + (n*gap), p2[2]+y]))
    def spewWithTimer(self,pos):
        bsPowerup.Powerup(position=pos, powerupType='health',expire=False).autoRetain()
    def _standardDropPowerup(self,index,expire=True): #Overloaded from bsGame in order to randomize without curse, health, or freeze.
        bsPowerup.Powerup(position=self.getMap().powerupSpawnPoints[index],
                          powerupType=bs.Powerup.getFactory().getRandomPowerupType(forceType=None, excludeTypes=self.excludePowerups),expire=expire).autoRetain()
    def _getLivingTeams(self):
        return [team for team in self.teams if len(team.players) > 0 and any(player.gameData['lives'] > 0 for player in team.players)]
    def _updateScoreBoard(self):
        for team in self.teams:
            self._scoreBoard.setTeamValue(team, team.gameData['score'])
    def endGame(self):
        if self.hasEnded(): return
        results = bs.TeamGameResults()
        self._vsText = None # kill our 'vs' if its there
        for team in self.teams:
            results.setTeamScore(team, team.gameData['score'])
        self.end(results=results)
        
