import bs
import bsUtils
import bsVector
import random
import copy


class PlayerHitMessage(object):
    pass


class ProtectedAreaHitMessage(object):
    pass


class FootingHitMessage(object):
    pass


class ObjectFactory(object):

    def __init__(self):
        self.texSno = bs.getTexture("bunnyColor")
        self.texHail = bs.getTexture("bombColorIce")
        self.snoModel = bs.getModel("frostyPelvis")
        self.hailModel = bs.getModel("powerup")
        self.snowMaterial = bs.Material()
        self.impactSound = bs.getSound('impactMedium')
        self.areaMaterial = bs.Material()
        self.snowMaterial.addActions(conditions=(('theyHaveMaterial', bs.getSharedObject('playerMaterial')), 'and',
                                                 ('theyDontHaveMaterial', bs.getSharedObject('footingMaterial'))),
                                     actions=(('modifyPartCollision', 'physical', False),
                                              ('message', 'ourNode', 'atConnect', PlayerHitMessage())))
        self.snowMaterial.addActions(conditions=(('theyHaveMaterial', self.areaMaterial), 'and',
                                                 ('theyHaveMaterial', bs.getSharedObject('regionMaterial')), 'and',
                                                 ('theyDontHaveMaterial', bs.getSharedObject('footingMaterial'))),
                                     actions=('message', 'ourNode', 'atConnect', ProtectedAreaHitMessage()))
        self.snowMaterial.addActions(conditions=(('theyDontHaveMaterial', bs.getSharedObject('playerMaterial')), 'and',
                                                 ('theyHaveMaterial', bs.getSharedObject('footingMaterial'))),
                                     actions=('message', 'ourNode', 'atConnect', FootingHitMessage()))
        self.defaultBallTimeout = 300
        self._ballsBust = True
        self._powerExpire = True
        self._powerLife = 20000


class SnowBall(bs.Actor):
    def __init__(self, position=(0, 1, 0), velocity=(5, 0, 5)):
        bs.Actor.__init__(self)

        factory = self.getFactory()
        self.node = bs.newNode("prop",
                               delegate=self,
                               attrs={'model': factory.snoModel,
                                      'body': 'sphere',
                                      'colorTexture': factory.texSno,
                                      'reflection': 'soft',
                                      'modelScale': 0.4,
                                      'bodyScale': 0.4,
                                      'density': 1,
                                      'reflectionScale': [0.15],
                                      'shadowSize': 0.6,
                                      'position': position,
                                      'velocity': velocity,
                                      'materials': [bs.getSharedObject('objectMaterial'), factory.snowMaterial]
                                      })
        self._exploded = False
        if factory._ballsBust:
            self.shouldBust = True
        else:
            self.shouldBust = False

    def handleMessage(self, m):
        if isinstance(m, bs.DieMessage):
            self.node.delete()
        elif isinstance(m, bs.OutOfBoundsMessage):
            self.handleMessage(bs.DieMessage(how="outOfBounds"))
        elif isinstance(m, bs.HitMessage):
            self.node.handleMessage("impulse", m.pos[0], m.pos[1], m.pos[2],
                                    m.velocity[0], m.velocity[1], m.velocity[2],
                                    1.0 * m.magnitude, 1.0 * m.velocityMagnitude, m.radius, 0,
                                    m.forceDirection[0], m.forceDirection[1], m.forceDirection[2])
        elif isinstance(m, bs.ImpactDamageMessage):
            print [dir(m), m.intensity]
        elif isinstance(m, PlayerHitMessage):
            if self._exploded:
                return
            v = self.node.velocity
            if bs.Vector(*v).length() > 5.0:
                node = bs.getCollisionInfo("opposingNode")

                if node is not None and node.exists():
                    t = self.node.position
                    hitDir = self.node.velocity

                    node.handleMessage(bs.HitMessage(pos=t,
                                                     velocity=v,
                                                     magnitude=bsVector.Vector(*v).length(),
                                                     velocityMagnitude=bsVector.Vector(*v).length() * 0.5,
                                                     radius=0,
                                                     srcNode=self.node,
                                                     sourcePlayer=None,
                                                     forceDirection=hitDir,
                                                     hitType='snoBall',
                                                     hitSubType='default'))
            self._exploded = True

            bs.gameTimer(1, bs.WeakCall(self.handleMessage, bs.DieMessage(how="snoMessage")))
        elif isinstance(m, ProtectedAreaHitMessage):
            self.handleMessage(bs.DieMessage(how="areaMessage"))
        elif isinstance(m, FootingHitMessage):
            if self._exploded:
                return
            bs.gameTimer(1000, bs.WeakCall(self.handleMessage, bs.DieMessage()))
        else:
            bs.Actor.handleMessage(self, m)

    def _disappear(self):
        self._exploded = True
        if self.exists():
            scl = self.node.modelScale
            bsUtils.animate(self.node, "modelScale", {0: scl * 1.0, 300: scl * 0.5, 500: 0.0})
            bs.gameTimer(550, bs.WeakCall(self.handleMessage, bs.DieMessage(how="disappeared")))

    @classmethod
    def getFactory(cls):
        activity = bs.getActivity()
        if activity is None:
            raise Exception("no current activity")
        try:
            return activity._sharedSnowStormFactory
        except Exception:
            f = activity._sharedSnowStormFactory = ObjectFactory()
            return f


class HailStone(bs.Actor):
    def __init__(self, position=(0, 1, 0), velocity=(5, 0, 5)):
        bs.Actor.__init__(self)

        factory = self.getFactory()
        self.node = bs.newNode("prop",
                               delegate=self,
                               attrs={'model': factory.hailModel,
                                      'body': 'sphere',
                                      'colorTexture': factory.texHail,
                                      'reflection': 'soft',
                                      'modelScale': 0.2,
                                      'bodyScale': 0.2,
                                      'density': 1,
                                      'reflectionScale': [0.15],
                                      'shadowSize': 0.6,
                                      'position': position,
                                      'velocity': velocity,
                                      'materials': [bs.getSharedObject('objectMaterial'), factory.snowMaterial]
                                      })
        self._exploded = False
        if factory._ballsBust:
            self.shouldBust = True
        else:
            self.shouldBust = False

    def handleMessage(self, m):
        if isinstance(m, bs.DieMessage):
            self.node.delete()
        elif isinstance(m, bs.OutOfBoundsMessage):
            self.handleMessage(bs.DieMessage(how="outOfBounds"))
        elif isinstance(m, bs.HitMessage):
            self.node.handleMessage("impulse", m.pos[0], m.pos[1], m.pos[2],
                                    m.velocity[0], m.velocity[1], m.velocity[2],
                                    1.0 * m.magnitude, 1.0 * m.velocityMagnitude, m.radius, 0,
                                    m.forceDirection[0], m.forceDirection[1], m.forceDirection[2])
        elif isinstance(m, bs.ImpactDamageMessage):
            print [dir(m), m.intensity]
        elif isinstance(m, PlayerHitMessage):
            if self._exploded:
                return
            v = self.node.velocity
            node = bs.getCollisionInfo("opposingNode")

            if node is not None and node.exists():
                if not node.getDelegate().frozen:
                    node.getDelegate().handleMessage(bs.FreezeMessage())
                else:
                    node.getDelegate().handleMessage(bs.ShouldShatterMessage())
                    node.getDelegate().handleMessage(bs.DieMessage())

            bs.gameTimer(1, bs.WeakCall(self.handleMessage, bs.DieMessage(how="snoMessage")))
        elif isinstance(m, ProtectedAreaHitMessage):
            self.handleMessage(bs.DieMessage(how="areaMessage"))
        elif isinstance(m, FootingHitMessage):
            if self._exploded:
                return
            bs.gameTimer(1000, bs.WeakCall(self.handleMessage, bs.DieMessage()))
        else:
            bs.Actor.handleMessage(self, m)

    def _disappear(self):
        self._exploded = True
        if self.exists():
            scl = self.node.modelScale
            bsUtils.animate(self.node, "modelScale", {0: scl * 1.0, 300: scl * 0.5, 500: 0.0})
            bs.gameTimer(550, bs.WeakCall(self.handleMessage, bs.DieMessage(how="disappeared")))

    @classmethod
    def getFactory(cls):
        activity = bs.getActivity()
        if activity is None:
            raise Exception("no current activity")
        try:
            return activity._sharedSnowStormFactory
        except Exception:
            f = activity._sharedSnowStormFactory = ObjectFactory()
            return f


class ProtectedSpazArea(bs.Actor):
    """For making the area to give the spaz protection from ice hail stones."""

    def __init__(self, position, radius):
        bs.Actor.__init__(self)
        self.position = (position[0], position[1] - 0.5, position[2])
        self.radius = radius
        color = (random.random(), random.random(), random.random())
        factory = self.getFactory()
        self.node = bs.newNode('region',
                               attrs={'position': (self.position[0], self.position[1], self.position[2]),
                                      'scale': (self.radius, self.radius, self.radius),
                                      'type': 'sphere',
                                      'materials': [factory.areaMaterial, bs.getSharedObject("regionMaterial")]})
        self.visualRadius = bs.newNode('shield', attrs={'position': self.position, 'color': color, 'radius': 0.1})
        bsUtils.animate(self.visualRadius, "radius", {0: 0, 500: self.radius * 2})
        bsUtils.animateArray(self.node, "scale", 3, {0: (0, 0, 0), 500: (self.radius, self.radius, self.radius)})

    def delete(self):
        if self.node.exists():
            self.node.delete()
        if self.visualRadius.exists():
            self.visualRadius.delete()

    @classmethod
    def getFactory(cls):
        activity = bs.getActivity()
        if activity is None:
            raise Exception("no current activity")
        try:
            return activity._sharedSnowStormFactory
        except Exception:
            f = activity._sharedSnowStormFactory = ObjectFactory()
            return f


def bsGetAPIVersion():
    return 4


def bsGetGames():
    return [SnowStormGame]


class Icon(bs.Actor):
    def __init__(self, player, position, scale, showLives=True, showDeath=True, nameScale=1.0, nameMaxWidth=115.0,
                 flatness=1.0, shadow=1.0):
        bs.Actor.__init__(self)

        self._player = player
        self._showLives = showLives
        self._showDeath = showDeath
        self._nameScale = nameScale

        self._outlineTex = bs.getTexture('characterIconMask')

        icon = player.getIcon()
        self.node = bs.newNode(
            'image',
            owner=self,
            attrs={
                'texture': icon['texture'],
                'tintTexture': icon['tintTexture'],
                'tintColor': icon['tintColor'],
                'vrDepth': 400,
                'tint2Color': icon['tint2Color'],
                'maskTexture': self._outlineTex,
                'opacity': 1.0,
                'absoluteScale': True,
                'attach': 'bottomCenter'
            })
        self._nameText = bs.newNode(
            'text',
            owner=self.node,
            attrs={
                'text': bs.Lstr(value=player.getName()),
                'color': bs.getSafeColor(player.getTeam().color),
                'hAlign': 'center',
                'vAlign': 'center',
                'vrDepth': 410,
                'maxWidth': nameMaxWidth,
                'shadow': shadow,
                'flatness': flatness,
                'hAttach': 'center',
                'vAttach': 'bottom'
            })
        if self._showLives:
            self._livesText = bs.newNode(
                'text',
                owner=self.node,
                attrs={
                    'text': 'x0',
                    'color': (1, 1, 0.5),
                    'hAlign': 'left',
                    'vrDepth': 430,
                    'shadow': 1.0,
                    'flatness': 1.0,
                    'hAttach': 'center',
                    'vAttach': 'bottom'
                })
        self.setPositionAndScale(position, scale)

    def setPositionAndScale(self, position, scale):
        self.node.position = position
        self.node.scale = [70.0 * scale]
        self._nameText.position = (position[0], position[1] + scale * 52.0)
        self._nameText.scale = 1.0 * scale * self._nameScale
        if self._showLives:
            self._livesText.position = (position[0] + scale * 10.0,
                                        position[1] - scale * 43.0)
            self._livesText.scale = 1.0 * scale

    def updateForLives(self):
        if self._player.exists():
            lives = self._player.gameData['lives']
        else:
            lives = 0
        if self._showLives:
            if lives > 0:
                self._livesText.text = 'x' + str(lives - 1)
            else:
                self._livesText.text = ''
        if lives == 0:
            self._nameText.opacity = 0.2
            self.node.color = (0.7, 0.3, 0.3)
            self.node.opacity = 0.2

    def handlePlayerSpawned(self):
        if not self.node.exists():
            return
        self.node.opacity = 1.0
        self.updateForLives()

    def handlePlayerDied(self):
        if not self.node.exists():
            return
        if self._showDeath:
            bs.animate(
                self.node, 'opacity', {
                    0: 1.0,
                    50: 0.0,
                    100: 1.0,
                    150: 0.0,
                    200: 1.0,
                    250: 0.0,
                    300: 1.0,
                    350: 0.0,
                    400: 1.0,
                    450: 0.0,
                    500: 1.0,
                    550: 0.2
                })
            lives = self._player.gameData['lives']
            if lives == 0:
                bs.gameTimer(600, self.updateForLives)


class SnowStormGame(bs.TeamGameActivity):
    @classmethod
    def getName(cls):
        return 'Snow Storm'

    @classmethod
    def getScoreInfo(cls):
        return {
            'scoreName': 'Survived',
            'scoreType': 'seconds',
            'noneIsWinner': True
        }

    @classmethod
    def getDescription(cls, sessionType):
        return 'Stay protected from the snow and hails.'

    @classmethod
    def supportsSessionType(cls, sessionType):
        return True if (issubclass(sessionType, bs.TeamsSession) or issubclass(
            sessionType, bs.FreeForAllSession)) else False

    @classmethod
    def getSupportedMaps(cls, sessionType):
        return bs.getMapsSupportingPlayType("melee")

    @classmethod
    def getSettings(cls, sessiontype):
        settings = [
            ("Lives Per Player", {
                'default': 1, 'minValue': 1,
                'maxValue': 10, 'increment': 1
            }),
            ("Time Limit", {
                'choices': [('None', 0), ('1 Minute', 60),
                            ('2 Minutes', 120), ('5 Minutes', 300),
                            ('10 Minutes', 600), ('20 Minutes', 1200)],
                'default': 0
            }),
            ("Respawn Times", {
                'choices': [('Shorter', 0.25), ('Short', 0.5), ('Normal', 1.0),
                            ('Long', 2.0), ('Longer', 4.0)],
                'default': 1.0
            }),
            ("Epic Mode", {'default': False})]  # yapf: disable

        if issubclass(sessiontype, bs.TeamsSession):
            settings.append(("Balance Total Lives", {'default': False}))

        return settings

    def __init__(self, settings):
        bs.TeamGameActivity.__init__(self, settings)
        if self.settings['Epic Mode']:
            self._isSlowMotion = True

        # show messages when players die since it's meaningful here
        self.announcePlayerDeaths = True

        self._scoreBoard = bs.ScoreBoard()
        self.timesPrecipitated = 0
        self.timesProtected = 0
        self.protectedArea = None

    def getInstanceDescription(self):
        return 'Last team standing wins.' if isinstance(
            self.getSession(), bs.TeamsSession) else 'Last one standing wins.'

    def getInstanceScoreBoardDescription(self):
        return 'last team standing wins' if isinstance(
            self.getSession(), bs.TeamsSession) else 'last one standing wins'

    def onTransitionIn(self):
        bs.TeamGameActivity.onTransitionIn(
            self, music='Epic' if self.settings['Epic Mode'] else 'Survival')
        self._startGameTime = bs.getGameTime()

    def onTeamJoin(self, team):
        team.gameData['survivalSeconds'] = None
        team.gameData['spawnOrder'] = []

    def onPlayerJoin(self, player):

        # no longer allowing mid-game joiners here... too easy to exploit
        if self.hasBegun():
            player.gameData['lives'] = 0
            player.gameData['icons'] = []
            # make sure our team has survival seconds set if they're all dead
            # (otherwise blocked new ffa players would be considered 'still
            # alive' in score tallying)
            if self._getTotalTeamLives(player.getTeam(
            )) == 0 and player.getTeam().gameData['survivalSeconds'] is None:
                player.getTeam().gameData['survivalSeconds'] = 0
            bs.screenMessage(
                bs.Lstr(
                    resource='playerDelayedJoinText',
                    subs=[('${PLAYER}', player.getName(full=True))]),
                color=(0, 1, 0))
            return

        player.gameData['lives'] = self.settings['Lives Per Player']

        # create our icon and spawn
        player.gameData['icons'] = [
            Icon(player, position=(0, 50), scale=0.8)
        ]
        if player.gameData['lives'] > 0:
            self.spawnPlayer(player)

        # dont waste time doing this until begin
        if self.hasBegun():
            self._updateIcons()

    def _updateIcons(self):
        # in free-for-all mode, everyone is just lined up along the bottom
        if isinstance(self.getSession(), bs.FreeForAllSession):
            count = len(self.teams)
            xOffs = 85
            x = xOffs * (count - 1) * -0.5
            for i, team in enumerate(self.teams):
                if len(team.players) == 1:
                    player = team.players[0]
                    for icon in player.gameData['icons']:
                        icon.setPositionAndScale((x, 30), 0.7)
                        icon.updateForLives()
                    x += xOffs

        # in teams mode we split up teams
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
                        icon.setPositionAndScale((x, 30), 0.7)
                        icon.updateForLives()
                    x += xOffs

    def spawnPlayer(self, player):

        self.spawnPlayerSpaz(player=player)
        bs.gameTimer(300, bs.Call(self._printLives, player))

        # if we have any icons, update their state
        for icon in player.gameData['icons']:
            icon.handlePlayerSpawned()

    def spawnPlayerSpaz(self, player, position=None, angle=None):
        """
        Create and wire up a bs.PlayerSpaz for the provide bs.Player.
        """

        if position is None:
            # in teams-mode get our team-start-location
            if isinstance(self.getSession(), bs.TeamsSession):
                position = self.getMap().getStartPosition(player.getTeam().getID())
            else:
                # otherwise do free-for-all spawn locations
                position = self.getMap().getFFAStartPosition(self.players)
        name = player.getName()
        color = player.color
        highlight = player.highlight

        lightColor = bsUtils.getNormalizedColor(color)
        displayColor = bs.getSafeColor(color, targetIntensity=0.75)
        spaz = bs.PlayerSpaz(color=color,
                             highlight=highlight,
                             character=player.character,
                             player=player)
        player.setActor(spaz)

        # if this is co-op and we're on Courtyard or Runaround, add the
        # material that allows us to collide with the player-walls
        # FIXME; need to generalize this
        if isinstance(
                self.getSession(),
                bs.CoopSession) and self.getMap().getName() in [
            'Courtyard', 'Tower D']:
            mat = self.getMap().preloadData['collideWithWallMaterial']
            spaz.node.materials += (mat,)
            spaz.node.rollerMaterials += (mat,)

        spaz.node.name = name
        spaz.node.nameColor = displayColor
        spaz.connectControlsToPlayer()
        spaz.disconnectControlsFromPlayer()
        spaz.connectControlsToPlayer(enableJump=True, enablePunch=False, enablePickUp=False, enableBomb=False,
                                     enableRun=True, enableFly=True)
        self.scoreSet.playerGotNewSpaz(player, spaz)

        # move to the stand position and add a flash of light
        spaz.handleMessage(
            bs.StandMessage(
                position, angle
                if angle is not None else random.uniform(0, 360)))
        t = bs.getGameTime()
        bs.playSound(self._spawnSound, 1, position=spaz.node.position)
        light = bs.newNode('light', attrs={'color': lightColor})
        spaz.node.connectAttr('position', light, 'position')
        bsUtils.animate(light, 'intensity', {0: 0, 250: 1, 500: 0})
        bs.gameTimer(500, light.delete)
        return spaz

    def _printLives(self, player):
        if not player.exists() or not player.isAlive():
            return
        try:
            pos = player.actor.node.position
        except Exception, e:
            print 'EXC getting player pos in bsElim', e
            return
        bs.PopupText(
            'x' + str(player.gameData['lives'] - 1),
            color=(1, 1, 0, 1),
            offset=(0, -0.8, 0),
            randomOffset=0.0,
            scale=1.8,
            position=pos).autoRetain()

    def onPlayerLeave(self, player):
        bs.TeamGameActivity.onPlayerLeave(self, player)
        player.gameData['icons'] = None

        # update icons in a moment since our team will be gone from the
        # list then
        bs.gameTimer(0, self._updateIcons)

    def onBegin(self):
        bs.TeamGameActivity.onBegin(self)
        self.setupStandardTimeLimit(self.settings['Time Limit'])
        self.setupStandardPowerupDrops()

        # if balance-team-lives is on, add lives to the smaller team until
        # total lives match
        if (isinstance(self.getSession(), bs.TeamsSession)
                and self.settings['Balance Total Lives']
                and len(self.teams[0].players) > 0
                and len(self.teams[1].players) > 0):
            if self._getTotalTeamLives(
                    self.teams[0]) < self._getTotalTeamLives(self.teams[1]):
                lesserTeam = self.teams[0]
                greaterTeam = self.teams[1]
            else:
                lesserTeam = self.teams[1]
                greaterTeam = self.teams[0]
            addIndex = 0
            while self._getTotalTeamLives(
                    lesserTeam) < self._getTotalTeamLives(greaterTeam):
                lesserTeam.players[addIndex].gameData['lives'] += 1
                addIndex = (addIndex + 1) % len(lesserTeam.players)

        self._updateIcons()
        self._precipitate()
        self._createProtection()

        # we could check game-over conditions at explicit trigger points,
        # but lets just do the simple thing and poll it...
        bs.gameTimer(1000, self._update, repeat=True)

    def _getTotalTeamLives(self, team):
        return sum(player.gameData['lives'] for player in team.players)

    def _precipitate(self):
        self.timesPrecipitated += 1
        activity = bs.getActivity()
        position = self.getRandomPosition(activity)

        def precipitate(pos):
            v = ((-5.0 + random.random() * 30.0) * (-1.0 if pos[0] > 0 else 1.0), pos[1] - 3,
                 (-5.0 + random.random() * 30.0) * (-1.0 if pos[0] > 0 else 1.0))
            vs = ((-5.0 + random.random() * 30.0) * (-1.0 if pos[0] > 0 else 1.0), pos[1] - 2,
                  (-5.0 + random.random() * 30.0) * (-1.0 if pos[0] > 0 else 1.0))
            vh = ((-5.0 + random.random() * 30.0) * (-1.0 if pos[0] > 0 else 1.0), pos[1] - 2,
                  (-5.0 + random.random() * 30.0) * (-1.0 if pos[0] > 0 else 1.0))
            bs.emitBGDynamics(position=pos, velocity=v, count=10, scale=1 + random.random(), spread=10,
                              chunkType='spark')
            SnowBall(position=(pos[0], pos[1] + 3, pos[2]), velocity=vs).autoRetain()
            HailStone(position=(pos[0], pos[1] + 3, pos[2]), velocity=vh).autoRetain()

        precipitate(position)
        r = random.randint(3, 10)
        precipitate(pos=(position[0] + r, position[1], position[2]))
        precipitate(pos=(position[0] - r, position[1], position[2]))
        precipitate(pos=(position[0], position[1], position[2] + r))
        precipitate(pos=(position[0], position[1], position[2] - r))
        precipitate(pos=(position[0] + r, position[1], position[2] + r))
        precipitate(pos=(position[0] - r, position[1], position[2] - r))
        precipitate(pos=(position[0] - r, position[1], position[2] + r))
        precipitate(pos=(position[0] + r, position[1], position[2] - r))
        if self.timesPrecipitated < 10:
            bs.gameTimer(1500, self._precipitate)
        elif self.timesPrecipitated < 15:
            bs.gameTimer(1100, self._precipitate)
        elif self.timesPrecipitated < 18:
            bs.gameTimer(850, self._precipitate)
        elif self.timesPrecipitated < 21:
            bs.gameTimer(700, self._precipitate)
        elif self.timesPrecipitated < 23:
            bs.gameTimer(500, self._precipitate)
        else:
            bs.gameTimer(150, self._precipitate)

    def _createProtection(self):
        self.timesProtected += 1
        activity = bs.getActivity()
        position = self.getRandomPosition(activity)

        def again(timeInMillis):
            bs.gameTimer(timeInMillis, self.protectedArea.delete)
            bs.gameTimer(timeInMillis + 500, self._createProtection)

        self.protectedArea = ProtectedSpazArea(position, 1.5)
        if self.timesProtected < 7:
            again(5200)
        elif self.timesProtected < 11:
            again(4100)
        elif self.timesProtected < 15:
            again(3250)
        elif self.timesProtected < 19:
            again(2700)
        elif self.timesProtected < 23:
            again(2200)
        else:
            again(1800)

    def handleMessage(self, m):
        if isinstance(m, bs.PlayerSpazDeathMessage):

            bs.TeamGameActivity.handleMessage(self, m)  # augment standard behavior
            player = m.spaz.getPlayer()

            player.gameData['lives'] -= 1
            if player.gameData['lives'] < 0:
                bs.printError("Got lives < 0 in Snow Storm; this shouldn't happen.")
                player.gameData['lives'] = 0

            # if we have any icons, update their state
            for icon in player.gameData['icons']:
                icon.handlePlayerDied()

            # play big death sound on our last death
            if player.gameData['lives'] == 0:
                bs.playSound(bs.Spaz.getFactory().singlePlayerDeathSound)

            # if we hit zero lives, we're dead (and our team might be too)
            if player.gameData['lives'] == 0:
                # if the whole team is now dead, mark their survival time..
                if self._getTotalTeamLives(player.getTeam()) == 0:
                    player.getTeam().gameData['survivalSeconds'] = (bs.getGameTime() - self._startGameTime) / 1000
            else:
                # otherwise, in regular mode, respawn..
                self.respawnPlayer(player)

    def _update(self):

        # if we're down to 1 or fewer living teams, start a timer to end
        # the game (allows the dust to settle and draws to occur if deaths
        # are close enough)
        if len(self._getLivingTeams()) < 2:
            self._roundEndTimer = bs.Timer(500, self.endGame)

    def _getLivingTeams(self):
        return [
            team for team in self.teams
            if len(team.players) > 0 and any(player.gameData['lives'] > 0
                                             for player in team.players)
        ]

    def endGame(self):
        if self.hasEnded():
            return
        results = bs.TeamGameResults()
        self._vsText = None  # kill our 'vs' if its there
        for team in self.teams:
            results.setTeamScore(team, team.gameData['survivalSeconds'])
        self.end(results=results)

    @classmethod
    def getRandomPosition(cls, activity):

        pts = copy.copy(activity.getMap().ffaSpawnPoints)
        pts2 = activity.getMap().powerupSpawnPoints
        for i in pts2:
            pts.append(i)
        pos = [[999, -999], [999, -999], [999, -999]]
        for pt in pts:
            for i in range(3):
                pos[i][0] = min(pos[i][0], pt[i])
                pos[i][1] = max(pos[i][1], pt[i])
        # The credit of this random position finder goes to Deva but I did some changes too.
        ru = random.uniform
        ps = pos
        t = ru(ps[0][0] - 1.0, ps[0][1] + 1.0), ps[1][1] + ru(0.1, 1.5), ru(ps[2][0] - 1.0, ps[2][1] + 1.0)
        s = (t[0], t[1] - ru(1.0, 1.3), t[2])
        return s
