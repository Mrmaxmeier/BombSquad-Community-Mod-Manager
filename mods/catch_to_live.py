# coding=utf-8
# coding=utf8
import bs
import bsUtils
import random


class CheckNeedNewMadMessage(object):
    def __init__(self, spaz=None):
        self.spaz = spaz


class ClearProtectMessage(object):
    def __init__(self):
        pass


class grimPlayer(bs.PlayerSpaz):
    def __init__(self, color, highlight, character, player, gameProtectionTime=3):
        bs.PlayerSpaz.__init__(self, color=color, highlight=highlight, character=character, player=player)
        self._inmad = False  # 默认不是处于疯狂状态
        self._madProtect = False  # 默认处于无保护状态
        self.hitPoints = 5000
        self.hitPointsMax = 5000
        self.gameProtectionTime = gameProtectionTime

    def handleMessage(self, m):
        if isinstance(m, bs.PickedUpMessage):
            if not self.getPlayer().isAlive():
                return
            oppoSpaz = m.node.getDelegate()
            if not oppoSpaz.getPlayer().isAlive():
                return

            # 让对方放手
            oppoSpaz.onPickUpRelease()
            oppoSpaz.onPickUpPress()
            oppoSpaz.onPickUpRelease()
            if self._madProtect:
                bs.PlayerSpaz.handleMessage(self, m)
                return
            if oppoSpaz._inmad:
                oppoSpaz.stopMad()
                oppoSpaz.protectAdd()
                leftTime = (oppoSpaz._allMadTime - bs.getGameTime() + oppoSpaz._startMadTime)
                self.onMad(leftTime)

            bs.PlayerSpaz.handleMessage(self, m)
        elif isinstance(m, bs.DieMessage):
            self._inmad = False
            if not self._dead and not m.immediate:
                self._activity().handleMessage(CheckNeedNewMadMessage(self))
            bs.PlayerSpaz.handleMessage(self, m)
        else:
            bs.PlayerSpaz.handleMessage(self, m)

    def protectAdd(self):
        self.setScoreText(str(self.gameProtectionTime) + 's Crazy Protection')
        self.node.color = (0, 0, 1)
        self._madProtect = True
        bs.gameTimer(self.gameProtectionTime * 1000, bs.Call(self.protectClear))

    def protectClear(self):
        self._madProtect = False
        if self._inmad:
            # 躲不了系统给的MAD
            return
        self.node.color = (0, 1, 0)

    def onMad(self, madTime=10000):
        # 10秒后炸掉
        if self._inmad:
            return
        self._inmad = True
        self.getPlayer().assignInputCall('pickUpPress', self.onPickUpPress)
        self.getPlayer().assignInputCall('pickUpRelease', self.onPickUpRelease)
        self.node.hockey = True
        self.node.color = (1, 0, 0)
        self._startMadTime = bs.getGameTime()
        self._allMadTime = madTime
        bs.gameTimer(madTime, bs.WeakCall(self.madExplode, self._startMadTime))

    def stopMad(self):
        self._inmad = False
        self.getPlayer().assignInputCall('pickUpPress', lambda: None)
        self.getPlayer().assignInputCall('pickUpRelease', lambda: None)
        self.node.hockey = False
        self.node.color = (0, 1, 0)

    def madExplode(self, checkStartTime):
        if self._inmad and self._startMadTime == checkStartTime:
            self.shatter(extreme=True)
            self.handleMessage(bs.DieMessage())


def bsGetAPIVersion():
    return 4


def bsGetGames():
    return [CatchToLiveGame]


class CatchToLiveGame(bs.TeamGameActivity):
    @classmethod
    def getName(cls):
        return 'Catch To Live'

    @classmethod
    def getScoreInfo(cls):
        return {'scoreName': 'Survived',
                'scoreType': 'milliseconds',
                'scoreVersion': 'B'}

    @classmethod
    def getDescription(cls, sessionType):
        return 'If you\'re CRAZY and don\'t wanna die\nThen PICKUP others!'

    @classmethod
    def getSupportedMaps(cls, sessionType):
        # return ['Rampage']
        return bs.getMapsSupportingPlayType("melee")

    @classmethod
    def getSettings(cls, sessionType):
        return [("Mad Time To Die (Approximate)", {'minValue': 5, 'default': 10, 'increment': 1}),
                ("Protection Time After Catching", {'minValue': 1, 'default': 3, 'increment': 1}),
                ("Epic Mode", {'default': False}),
                ("Allow Landmine", {'default': True})]

    # we support teams, free-for-all, and co-op sessions
    @classmethod
    def supportsSessionType(cls, sessionType):
        return True if (issubclass(sessionType, bs.TeamsSession)
                        or issubclass(sessionType, bs.FreeForAllSession)
                        or issubclass(sessionType, bs.CoopSession)) else False

    def __init__(self, settings):
        bs.TeamGameActivity.__init__(self, settings)

        if self.settings['Epic Mode']: self._isSlowMotion = True

        # print messages when players die (since its meaningful in this game)
        self.announcePlayerDeaths = True

        self._lastPlayerDeathTime = None

    # called when our game is transitioning in but not ready to start..
    # ..we can go ahead and set our music and whatnot
    def onTransitionIn(self):
        bs.TeamGameActivity.onTransitionIn(self, music='Epic' if self.settings['Epic Mode'] else 'Survival')

    # called when our game actually starts
    def onBegin(self):
        # self.playerList = []
        bs.TeamGameActivity.onBegin(self)
        self._madTime = self.settings['Mad Time To Die (Approximate)'] * 1000

        # bs.gameTimer(t,self._decrementMeteorTime,repeat=True)

        # kick off the first wave in a few seconds
        t = 3000
        if self.settings['Epic Mode']: t /= 4
        # bs.gameTimer(t,self._setMeteorTimer)

        self._timer = bs.OnScreenTimer()
        self._timer.start()

        bs.gameTimer(10, bs.WeakCall(self.updateSpazText), repeat=True)

        bs.gameTimer(t, bs.WeakCall(self.handleMessage, CheckNeedNewMadMessage()), repeat=False)
        bs.gameTimer(1000, self._checkNeedMad, repeat=True)

        # bs.gameTimer(5000, self._checkEndGame)  # 4秒之后检测一波

    def updateSpazText(self):
        for team in self.teams:
            for player in team.players:
                try:
                    if player.actor._inmad:
                        leftTime = (player.actor._allMadTime - bs.getGameTime() + player.actor._startMadTime) / 1000.0
                        if leftTime > 0.0:
                            player.actor.setScoreText('Crazy')
                            # player.actor.setScoreText('%.2f' % (leftTime), color=(1, 1, 1))
                        else:
                            player.actor.setScoreText('')
                except:
                    pass

    # overriding the default character spawning..
    def spawnPlayer(self, player):

        position = self.getMap().getFFAStartPosition(self.players)
        angle = 20
        name = player.getName()

        lightColor = bsUtils.getNormalizedColor(player.color)
        displayColor = bs.getSafeColor(player.color, targetIntensity=0.75)

        spaz = grimPlayer(color=(0, 1, 0),
                          highlight=(0, 1, 0),
                          character=player.character,
                          player=player,
                          gameProtectionTime=self.settings['Protection Time After Catching'])
        player.setActor(spaz)
        # For some reason, I can't figure out how to get a list of all spaz.
        # Therefore, I am making the list here so I can get which spaz belongs
        # to the player supplied by HitMessage.
        # self.playerList.append(spaz)

        spaz.node.name = name
        spaz.node.nameColor = displayColor
        spaz.connectControlsToPlayer()
        self.scoreSet.playerGotNewSpaz(player, spaz)

        # add landmine
        spaz.bombTypeDefault = 'landMine'#random.choice(['ice', 'impact', 'landMine', 'normal', 'sticky', 'tnt'])
        spaz.bombType = spaz.bombTypeDefault

        # move to the stand position and add a flash of light
        spaz.handleMessage(bs.StandMessage(position, angle if angle is not None else random.uniform(0, 360)))
        t = bs.getGameTime()
        bs.playSound(self._spawnSound, 1, position=spaz.node.position)
        light = bs.newNode('light', attrs={'color': lightColor})
        spaz.node.connectAttr('position', light, 'position')
        bsUtils.animate(light, 'intensity', {0: 0, 250: 1, 500: 0})
        bs.gameTimer(500, light.delete)

        # lets reconnect this player's controls to this
        # spaz but *without* the ability to attack or pick stuff up
        spaz.connectControlsToPlayer(enablePunch=False,
                                     enableBomb=self.settings['Allow Landmine'],
                                     enablePickUp=False)
        # player.assignInputCall('pickUpPress', lambda: None)
        # player.assignInputCall('pickUpRelease', lambda: None)
        # also lets have them make some noise when they die..
        spaz.playBigDeathSound = True

        return spaz

    def onPlayerJoin(self, player):
        # don't allow joining after we start
        # (would enable leave/rejoin tomfoolery)
        if self.hasBegun():
            bs.screenMessage(bs.Lstr(resource='playerDelayedJoinText', subs=[('${PLAYER}', player.getName(full=True))]),
                             color=(0, 1, 0))
            # for score purposes, mark them as having died right as the game started
            player.gameData['noScore'] = True
            return
        self.spawnPlayer(player)

    def onPlayerLeave(self, player):
        # augment default behavior...
        bs.TeamGameActivity.onPlayerLeave(self, player)
        # a departing player may trigger game-over
        bs.gameTimer(100, bs.Call(self._checkEndGame))

    # various high-level game events come through this method
    def handleMessage(self, m):

        if isinstance(m, bs.PlayerSpazDeathMessage):

            bs.TeamGameActivity.handleMessage(self, m)  # (augment standard behavior)

            deathTime = bs.getGameTime()

            # record the player's moment of death
            m.spaz.getPlayer().gameData['deathTime'] = deathTime

            # in co-op mode, end the game the instant everyone dies (more accurate looking)
            # in teams/ffa, allow a one-second fudge-factor so we can get more draws
            if isinstance(self.getSession(), bs.CoopSession):
                # teams will still show up if we check now.. check in the next cycle
                bs.pushCall(self._checkEndGame)
                self._lastPlayerDeathTime = deathTime  # also record this for a final setting of the clock..
            else:
                bs.gameTimer(1000, self._checkEndGame)

        elif isinstance(m, CheckNeedNewMadMessage):
            self._checkNeedMad()
        else:
            # default handler:
            bs.TeamGameActivity.handleMessage(self, m)

    def _checkNeedMad(self):
        # print('check if we need a new mad')
        alivePlayers = []
        for team in self.teams:
            for player in team.players:
                if player.isAlive():
                    alivePlayers.append(player)
                    if player.actor._inmad:
                        # print('no need for new mad')
                        return

        if len(alivePlayers) == 0:
            return

        selectedPlayer = random.choice(alivePlayers)
        selectedPlayer.actor.onMad(random.randint(self._madTime - 2500, self._madTime + 2500))

    def _checkEndGame(self):
        livingTeamCount = 0
        for team in self.teams:
            for player in team.players:
                if player.isAlive():
                    livingTeamCount += 1
                    break

        # in co-op, we go till everyone is dead.. otherwise we go until one team remains
        if isinstance(self.getSession(), bs.CoopSession):
            if livingTeamCount <= 0: self.endGame()
        else:
            if livingTeamCount <= 1: self.endGame()

    def endGame(self):

        curTime = bs.getGameTime()

        # mark 'death-time' as now for any still-living players
        # and award players points for how long they lasted.
        # (these per-player scores are only meaningful in team-games)
        for team in self.teams:
            for player in team.players:

                # throw an extra fudge factor +1 in so teams that
                # didn't die come out ahead of teams that did
                if 'deathTime' not in player.gameData: player.gameData['deathTime'] = curTime + 1
                if 'noScore' in player.gameData: player.gameData['deathTime'] = self._timer.getStartTime()

                # award a per-player score depending on how many seconds they lasted
                # (per-player scores only affect teams mode; everywhere else just looks at the per-team score)
                score = (player.gameData['deathTime'] - self._timer.getStartTime()) / 1000
                if 'deathTime' not in player.gameData: score += 50  # a bit extra for survivors
                self.scoreSet.playerScored(player, score, screenMessage=False)

        # stop updating our time text, and set the final time to match
        # exactly when our last guy died.
        self._timer.stop(endTime=self._lastPlayerDeathTime)

        # ok now calc game results: set a score for each team and then tell the game to end
        results = bs.TeamGameResults()

        # remember that 'free-for-all' mode is simply a special form of 'teams' mode
        # where each player gets their own team, so we can just always deal in teams
        # and have all cases covered
        for team in self.teams:

            # set the team score to the max time survived by any player on that team
            longestLife = 0
            for player in team.players:
                longestLife = max(longestLife, (player.gameData['deathTime'] - self._timer.getStartTime()))
            results.setTeamScore(team, longestLife)

        self.end(results=results)
