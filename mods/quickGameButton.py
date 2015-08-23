import bs
import bsInternal
import bsGame
import bsTeamGame
import bsMap
from bsUI import PlayWindow, AddGameWindow, gSmallUI, gMedUI, gTitleColor, uiGlobals
import copy

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
		settings = dict(map=self.settings["map"], **self.settings["settings"])
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
		self._R = R = bs.getResource('addGameWindow')
		self._width = 650
		self._height = 346 if gSmallUI else 380 if gMedUI else 440
		topExtra = 30 if gSmallUI else 20

		self._scrollWidth = 210

		self._rootWidget = bs.containerWidget(size=(self._width,self._height+topExtra),transition=transition,
		scale=2.17 if gSmallUI else 1.5 if gMedUI else 1.0,
		stackOffset=(0,1) if gSmallUI else (0,0))

		self._backButton = b = bs.buttonWidget(parent=self._rootWidget,position=(58,self._height-53),
											   size=(165,70),scale=0.75,textScale=1.2,label=bs.getResource('backText'),
											   autoSelect=True,
											   buttonType='back',onActivateCall=self._back)
		self._selectButton = selectButton = b = bs.buttonWidget(parent=self._rootWidget,position=(self._width-172,self._height-50),
																autoSelect=True,size=(160,60),scale=0.75,textScale=1.2,label=bs.getResource('selectText'),onActivateCall=self._add)
		bs.textWidget(parent=self._rootWidget,position=(self._width*0.5,self._height-28),size=(0,0),scale=1.0,
														text="Select Game",hAlign='center',color=gTitleColor,maxWidth=250,
														vAlign='center')
		v = self._height - 64


		self._selectedTitleText = bs.textWidget(parent=self._rootWidget,position=(self._scrollWidth+50+30,v-15),size=(0,0),
												scale=1.0,color=(0.7,1.0,0.7,1.0),maxWidth=self._width-self._scrollWidth-150,
												hAlign='left',vAlign='center')
		v -= 30

		self._selectedDescriptionText = bs.textWidget(parent=self._rootWidget,position=(self._scrollWidth+50+30,v),size=(0,0),
													  scale=0.7,color=(0.5,0.8,0.5,1.0),maxWidth=self._width-self._scrollWidth-150,
													  hAlign='left')

		#scrollHeight = 173 if gSmallUI else 220
		scrollHeight = self._height-100

		v = self._height - 60
		# v -= 95
		# v -= 94
		# v -= 75
		# if gSmallUI: v += 50


		self._scrollWidget = bs.scrollWidget(parent=self._rootWidget,position=(61,v-scrollHeight),size=(self._scrollWidth,scrollHeight))
		bs.widget(edit=self._scrollWidget,upWidget=self._backButton,leftWidget=self._backButton,rightWidget=selectButton)
		self._column = None

		v -= 35
		bs.containerWidget(edit=self._rootWidget,cancelButton=self._backButton,startButton=selectButton)
		self._selectedGameType = None

		bs.containerWidget(edit=self._rootWidget,selectedChild=self._scrollWidget)

		self._refresh()

	def _add(self):
		bsInternal._lockAllInput() # make sure no more commands happen
		bs.realTimer(100, bsInternal._unlockAllInput)
		config = None #FIXME: load previous config
		self._selectedGameType.createConfigUI(self._editSession._sessionType, copy.deepcopy(config), self.onEditGameDone)

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
		uiGlobals["mainMenuWindow"] = SelectGameWindow().getRootWidget()
		bs.containerWidget(edit=self._rootWidget, transition='outLeft')
		#s = CustomSession
		#startGame(s)

	bs.buttonWidget(parent=self._rootWidget, autoSelect=True,
					position=(width - 55 - 120, height - 132), size=(120, 60),
					scale=1.1, textScale=1.2,
					label="custom...", onActivateCall=doQuickGame,
					color=(0.54, 0.52, 0.67),
					textColor=(0.7, 0.65, 0.7))



PlayWindow.__init__ = newInit
