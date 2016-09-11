import bs
import random

def bsGetAPIVersion():
    # return the api-version this script expects.
    # this prevents it from attempting to run in newer versions of the game
    # where changes have been made to the modding APIs
    return 4

def bsGetGames():
    return [FightOfFaithGame]

def bsGetLevels():
    # Levels are unique named instances of a particular game with particular settings.
    # They show up as buttons in the co-op section, get high-score lists associated with them, etc.
    return [bs.Level('Fight of Faith', # globally-unique name for this level (not seen by user)
            displayName='${GAME}', # ${GAME} will be replaced by the results of the game's getName() call
            gameType=FightOfFaithGame,
            settings={}, # we currently dont have any settings; we'd specify them here if we did.
            previewTexName='courtyardPreview')]

class FightOfFaithGame(bs.TeamGameActivity):
    # name seen by the user
    @classmethod
    def getName(cls):
        return 'Fight of Faith'

    @classmethod
    def getScoreInfo(cls):
        return {'scoreType':'milliseconds',
                'lowerIsBetter':True,
                'scoreName':'Time'}

    @classmethod
    def getDescription(cls,sessionType):
        return 'How quickly you kill THEM?'

    @classmethod
    def getSupportedMaps(cls,sessionType):
        # for now we're hard-coding spawn positions and whatnot
        # so we need to be sure to specity that we only support
        # a specific map..
        return ['Courtyard']

    @classmethod
    def supportsSessionType(cls,sessionType):
        # we currently support Co-Op only
        return True if issubclass(sessionType,bs.CoopSession) else False

    # in the constructor we should load any media we need/etc.
    # but not actually create anything yet.
    def __init__(self,settings):
        bs.TeamGameActivity.__init__(self,settings)
        self._winSound = bs.getSound("score")

    # called when our game is transitioning in but not ready to start..
    # ..we can go ahead and start creating stuff, playing music, etc.
    def onTransitionIn(self):
        bs.TeamGameActivity.onTransitionIn(self, music='ToTheDeath')

    # called when our game actually starts
    def onBegin(self):

        bs.TeamGameActivity.onBegin(self)

        self._won = False

        self.setupStandardPowerupDrops()

        # make our on-screen timer and start it roughly when our bots appear
        self._timer = bs.OnScreenTimer()
        bs.gameTimer(4000,self._timer.start)

        # this wrangles our bots
        self._bots = bs.BotSet()

        # start some timers to spawn bots
        bs.gameTimer(2000,bs.Call(self._bots.spawnBot,bs.MelBot,pos=(3,3,-2),spawnTime=3000))
        bs.gameTimer(2000,bs.Call(self._bots.spawnBot,bs.ChickBot,pos=(-3,3,-2),spawnTime=3000))
        bs.gameTimer(2000,bs.Call(self._bots.spawnBot,bs.ToughGuyBotPro,pos=(5,3,-2),spawnTime=3000))
        bs.gameTimer(2000,bs.Call(self._bots.spawnBot,bs.BomberBotPro,pos=(-5,3,-2),spawnTime=3000))
        bs.gameTimer(2000,bs.Call(self._bots.spawnBot,bs.BomberBot,pos=(0,3,-5),spawnTime=3000))
        bs.gameTimer(2000,bs.Call(self._bots.spawnBot,bs.PirateBotNoTimeLimit,pos=(0,3,1),spawnTime=10000))

        # note: if spawns were spread out more we'd probably want to set some sort of flag on the
        # last spawn to ensure we don't inadvertantly allow a 'win' before every bot is spawned.
        # (ie: if bot 1, 2, and 3 got killed but 4 hadn't spawned yet, the game might end because
        # it sees no remaining bots.

    # called for each spawning player
    def spawnPlayer(self,player):

        # lets spawn close to the center
        spawnCenter = (0,3,-2)
        pos = (spawnCenter[0]+random.uniform(-1.5,1.5),spawnCenter[1],spawnCenter[2]+random.uniform(-1.5,1.5))

        self.spawnPlayerSpaz(player,position=pos)

    def _checkIfWon(self):
        # simply end the game if there's no living bots..
        if not self._bots.haveLivingBots():
            self._won = True
            self.endGame()

    # called for miscellaneous events
    def handleMessage(self,m):

        # a player has died
        if isinstance(m,bs.PlayerSpazDeathMessage):
            bs.TeamGameActivity.handleMessage(self,m) # do standard stuff
            self.respawnPlayer(m.spaz.getPlayer()) # kick off a respawn

        # a spaz-bot has died
        elif isinstance(m,bs.SpazBotDeathMessage):
            # unfortunately the bot-set will always tell us there are living
            # bots if we ask here (the currently-dying bot isn't officially marked dead yet)
            # ..so lets push a call into the event loop to check once this guy has finished dying.
            bs.pushCall(self._checkIfWon)

        else:
            # let the base class handle anything we don't..
            bs.TeamGameActivity.handleMessage(self,m)

    # when this is called, we should fill out results and end the game
    # *regardless* of whether is has been won. (this may be called due
    # to a tournament ending or other external reason)
    def endGame(self):

        # stop our on-screen timer so players can see what they got
        self._timer.stop()

        results = bs.TeamGameResults()

        # if we won, set our score to the elapsed time
        # (there should just be 1 team here since this is co-op)
        # ..if we didn't win, leave scores as default (None) which means we lost
        if self._won:
            elapsedTime = bs.getGameTime()-self._timer.getStartTime()
            self.cameraFlash()
            bs.playSound(self._winSound)
            for team in self.teams:
                team.celebrate() # woooo! par-tay!
                results.setTeamScore(team,elapsedTime)

        # ends this activity..
        self.end(results)
