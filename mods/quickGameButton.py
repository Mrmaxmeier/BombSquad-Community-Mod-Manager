import bs
import bsInternal
import bsTeamGame
from bsUI import PlayWindow, AddGameWindow, gSmallUI, gMedUI, gTitleColor, uiGlobals, gWindowStates
import bsUtils

_supports_auto_reloading = True
_auto_reloader_type = "patching"
PlayWindow__init__ = PlayWindow.__init__
PlayWindow_save_state = PlayWindow._save_state
PlayWindow_restore_state = PlayWindow._restore_state


def _prepare_reload():
    PlayWindow.__init__ = PlayWindow__init__
    PlayWindow._save_state = PlayWindow_save_state
    PlayWindow._restore_state = PlayWindow_restore_state

# TODO: support other gametypes than free-for-all

if "quickGameButton" in bs.getConfig():
    config = bs.getConfig()["quickGameButton"]
else:
    config = {"selected": None, "config": None}
    bs.getConfig()["quickGameButton"] = config
    bs.writeConfig()


def startGame(session, fadeout=True):
    def callback():
        if fadeout:
            bsInternal._unlockAllInput()
        try:
            bsInternal._newHostSession(session)
        except Exception:
            import bsMainMenu
            bs.printException("exception running session", session)
            # drop back into a main menu session..
            bsInternal._newHostSession(bsMainMenu.MainMenuSession)

    if fadeout:
        bsInternal._fadeScreen(False, time=250, endCall=callback)
        bsInternal._lockAllInput()
    else:
        callback()


class SimplePlaylist(object):
    def __init__(self, settings, gameType):
        self.settings = settings
        self.gameType = gameType

    def pullNext(self):
        if "map" not in self.settings["settings"]:
            settings = dict(map=self.settings["map"], **self.settings["settings"])
        else:
            settings = self.settings["settings"]
        return dict(resolvedType=self.gameType, settings=settings)


class CustomSession(bsTeamGame.FreeForAllSession):
    def __init__(self, *args, **kwargs):
        self._useTeams = False
        self._tutorialActivityInstance = None
        bs.Session.__init__(self, teamNames=None,
                            teamColors=None,
                            useTeamColors=False,
                            minPlayers=1,
                            maxPlayers=self.getMaxPlayers())

        self._haveShownControlsHelpOverlay = False

        self._seriesLength = 1
        self._ffaSeriesLength = 1

        # which game activity we're on
        self._gameNumber = 0
        self._playlist = SimplePlaylist(self._config, self._gameType)
        config["selected"] = self._gameType.__name__
        config["config"] = self._config
        bs.writeConfig()

        # get a game on deck ready to go
        self._currentGameSpec = None
        self._nextGameSpec = self._playlist.pullNext()
        self._nextGame = self._nextGameSpec["resolvedType"]

        # go ahead and instantiate the next game we'll use so it has lots of time to load
        self._instantiateNextGame()

        # start in our custom join screen
        self.setActivity(bs.newActivity(bsTeamGame.TeamJoiningActivity))


class SelectGameWindow(AddGameWindow):
    def __init__(self, transition='inRight'):
        class EditSession:
            _sessionType = bs.FreeForAllSession

            def getSessionType(self): return self._sessionType

        self._editSession = EditSession()
        self._width = 650
        self._height = 346 if gSmallUI else 380 if gMedUI else 440
        topExtra = 30 if gSmallUI else 20

        self._scrollWidth = 210

        self._rootWidget = bs.containerWidget(size=(self._width, self._height+topExtra), transition=transition,
                                              scale=2.17 if gSmallUI else 1.5 if gMedUI else 1.0,
                                              stackOffset=(0, 1) if gSmallUI else (0, 0))

        self._backButton = bs.buttonWidget(parent=self._rootWidget, position=(58, self._height-53),
                                           size=(165, 70), scale=0.75, textScale=1.2, label=bs.Lstr(resource='backText'),
                                           autoSelect=True,
                                           buttonType='back', onActivateCall=self._back)
        self._selectButton = selectButton = bs.buttonWidget(parent=self._rootWidget, position=(self._width-172, self._height-50),
                                                            autoSelect=True, size=(160, 60), scale=0.75, textScale=1.2,
                                                            label=bs.Lstr(resource='selectText'), onActivateCall=self._add)
        bs.textWidget(parent=self._rootWidget, position=(self._width*0.5, self._height-28), size=(0, 0), scale=1.0,
                      text="Select Game", hAlign='center', color=gTitleColor, maxWidth=250, vAlign='center')
        v = self._height - 64

        self._selectedTitleText = bs.textWidget(parent=self._rootWidget, position=(self._scrollWidth+50+30, v-15), size=(0, 0),
                                                scale=1.0, color=(0.7, 1.0, 0.7, 1.0), maxWidth=self._width-self._scrollWidth-150,
                                                hAlign='left', vAlign='center')
        v -= 30

        self._selectedDescriptionText = bs.textWidget(parent=self._rootWidget, position=(self._scrollWidth+50+30, v), size=(0, 0),
                                                      scale=0.7, color=(0.5, 0.8, 0.5, 1.0), maxWidth=self._width-self._scrollWidth-150,
                                                      hAlign='left')

        scrollHeight = self._height-100

        v = self._height - 60

        self._scrollWidget = bs.scrollWidget(parent=self._rootWidget, position=(61, v-scrollHeight), size=(self._scrollWidth, scrollHeight))
        bs.widget(edit=self._scrollWidget, upWidget=self._backButton, leftWidget=self._backButton, rightWidget=selectButton)
        self._column = None

        v -= 35
        bs.containerWidget(edit=self._rootWidget, cancelButton=self._backButton, startButton=selectButton)
        self._selectedGameType = None

        bs.containerWidget(edit=self._rootWidget, selectedChild=self._scrollWidget)

        self._refresh()
        if config["selected"]:
            for gt in bsUtils.getGameTypes():
                if not gt.supportsSessionType(self._editSession._sessionType):
                    continue
                if gt.__name__ == config["selected"]:
                    self._refresh(selected=gt)
                    self._setSelectedGameType(gt)

    def _refresh(self, selectGetMoreGamesButton=False, selected=None):

        if self._column is not None:
            self._column.delete()

        self._column = bs.columnWidget(parent=self._scrollWidget)
        gameTypes = [gt for gt in bsUtils.getGameTypes() if gt.supportsSessionType(self._editSession._sessionType)]
        # sort in this language
        gameTypes.sort(key=lambda g: g.getDisplayString())

        for i, gameType in enumerate(gameTypes):
            t = bs.textWidget(parent=self._column, position=(0, 0), size=(self._width-88, 24), text=gameType.getDisplayString(),
                              hAlign="left", vAlign="center",
                              color=(0.8, 0.8, 0.8, 1.0),
                              maxWidth=self._scrollWidth*0.8,
                              onSelectCall=bs.Call(self._setSelectedGameType, gameType),
                              alwaysHighlight=True,
                              selectable=True, onActivateCall=bs.Call(bs.realTimer, 100, self._selectButton.activate))
            if i == 0:
                bs.widget(edit=t, upWidget=self._backButton)
            if gameType == selected:
                bs.containerWidget(edit=self._column, selectedChild=t, visibleChild=t)

        self._getMoreGamesButton = bs.buttonWidget(parent=self._column, autoSelect=True,
                                                   label=bs.Lstr(resource='addGameWindow.getMoreGamesText'),
                                                   color=(0.54, 0.52, 0.67),
                                                   textColor=(0.7, 0.65, 0.7),
                                                   onActivateCall=self._onGetMoreGamesPress,
                                                   size=(178, 50))
        if selectGetMoreGamesButton:
            bs.containerWidget(edit=self._column, selectedChild=self._getMoreGamesButton,
                               visibleChild=self._getMoreGamesButton)

    def _add(self):
        bsInternal._lockAllInput()  # make sure no more commands happen
        bs.realTimer(100, bsInternal._unlockAllInput)
        gameconfig = {}
        if config["selected"] == self._selectedGameType.__name__:
            if config["config"]:
                gameconfig = config["config"]
        if "map" in gameconfig:
            gameconfig["settings"]["map"] = gameconfig.pop("map")
        self._selectedGameType.createConfigUI(self._editSession._sessionType, gameconfig, self.onEditGameDone)

    def onEditGameDone(self, config):
        if config:
            CustomSession._config = config
            CustomSession._gameType = self._selectedGameType
            startGame(CustomSession)
        else:
            bs.containerWidget(edit=uiGlobals["mainMenuWindow"], transition='outRight')
            uiGlobals["mainMenuWindow"] = SelectGameWindow(transition="inLeft").getRootWidget()

    def _back(self):
        bs.containerWidget(edit=self._rootWidget, transition='outRight')
        uiGlobals["mainMenuWindow"] = PlayWindow(transition="inLeft").getRootWidget()


oldInit = PlayWindow.__init__


def newInit(self, *args, **kwargs):
    oldInit(self, *args, **kwargs)

    width = 800
    height = 550

    def doQuickGame():
        self._save_state()
        uiGlobals["mainMenuWindow"] = SelectGameWindow().getRootWidget()
        bs.containerWidget(edit=self._rootWidget, transition='outLeft')

    self._quickGameButton = bs.buttonWidget(parent=self._rootWidget, autoSelect=True,
                                            position=(width - 55 - 120, height - 132), size=(120, 60),
                                            scale=1.1, textScale=1.2,
                                            label="custom...", onActivateCall=doQuickGame,
                                            color=(0.54, 0.52, 0.67),
                                            textColor=(0.7, 0.65, 0.7))
    self._restore_state()

PlayWindow.__init__ = newInit


def states(self):
    return {
        "Team Games": self._teamsButton,
        "Co-op Games": self._coopButton,
        "Free-for-All Games": self._freeForAllButton,
        "Back": self._backButton,
        "Quick Game": self._quickGameButton
    }


def _save_state(self):
    swapped = {v: k for k, v in states(self).items()}
    if self._rootWidget.getSelectedChild() in swapped:
        gWindowStates[self.__class__.__name__] = swapped[self._rootWidget.getSelectedChild()]
    else:
        print("error saving state for ", self.__class__, self._rootWidget.getSelectedChild())
PlayWindow._save_state = _save_state


def _restore_state(self):
    if not hasattr(self, "_quickGameButton"):
        return  # ensure that our monkey patched init ran
    if self.__class__.__name__ not in gWindowStates:
        bs.containerWidget(edit=self._rootWidget, selectedChild=self._coopButton)
        return
    sel = states(self).get(gWindowStates[self.__class__.__name__], None)
    if sel:
        bs.containerWidget(edit=self._rootWidget, selectedChild=sel)
    else:
        bs.containerWidget(edit=self._rootWidget, selectedChild=self._coopButton)
        print('error restoring state (', gWindowStates[self.__class__.__name__], ') for', self.__class__)
PlayWindow._restore_state = _restore_state
