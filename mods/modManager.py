import bs
import os
import urllib2, httplib, urllib
import ast
from md5 import md5
from bsUI import *

SUPPORTS_HTTPS = False


quittoapply = None
checkedMainMenu = False


# TODO: remove mm_uniqueID checks
if 'mm_uniqueID' in bs.getConfig():
	uniqueID = bs.getConfig().pop('mm_uniqueID')

if not 'mod_manager_config' in bs.getConfig():
	bs.getConfig()['mod_manager_config'] = {}
	bs.writeConfig()

config = bs.getConfig()['mod_manager_config']

def INDEX_FILE(branch=None):
	if branch:
		return "https://rawgit.com/Mrmaxmeier/BombSquad-Community-Mod-Manager/" + branch + "/index.json"
	return "https://rawgit.com/Mrmaxmeier/BombSquad-Community-Mod-Manager/" + config.get("branch", "master") + "/index.json"


def newInit(self, transition='inRight', originWidget=None):
	if originWidget is not None:
		self._transitionOut = 'outScale'
		scaleOrigin = originWidget.getScreenSpaceCenter()
		transition = 'inScale'
	else:
		self._transitionOut = 'outRight'
		scaleOrigin = None

	width = 750 if gSmallUI else 580
	height = 435

	buttonHeight = 42

	R = bs.getResource('settingsWindow')

	topExtra = 20 if gSmallUI else 0
	if originWidget is not None:
		self._rootWidget = bs.containerWidget(size=(width,height+topExtra),transition=transition,
											  scaleOriginStackOffset=scaleOrigin,
											  scale=1.75 if gSmallUI else 1.35 if gMedUI else 1.0,
											  stackOffset=(0,-8) if gSmallUI else (0,0))
	else:
		self._rootWidget = bs.containerWidget(size=(width,height+topExtra),transition=transition,
											  scale=1.75 if gSmallUI else 1.35 if gMedUI else 1.0,
											  stackOffset=(0,-8) if gSmallUI else (0,0))
	self._backButton = b = bs.buttonWidget(parent=self._rootWidget,autoSelect=True,position=(40,height-55),size=(130,60),scale=0.8,textScale=1.2,
						label=bs.getResource('backText'),buttonType='back',onActivateCall=self._doBack)
	bs.containerWidget(edit=self._rootWidget,cancelButton=b)

	t = bs.textWidget(parent=self._rootWidget,position=(0,height-44),size=(width,25),text=R.titleText,color=gTitleColor,
					  hAlign="center",vAlign="center",maxWidth=130)

	if gDoAndroidNav:
		bs.buttonWidget(edit=b,buttonType='backSmall',size=(60,60),label=bs.getSpecialChar('logoFlat'))
		bs.textWidget(edit=t,hAlign='left',position=(93,height-44))

	v = height - 80
	v -= 150

	bw = 215 if gSmallUI else 180
	bh = 175
	xOffs = 60 if gSmallUI else 36
	#######NEWSTUFF########
	xOffs2 = xOffs+bw-7
	xOffs3 = xOffs+2*(bw-7)
	xOffs4 = xOffs+0*(bw-7)
	xOffs5 = xOffs+1*(bw-7)
	xOffs6 = xOffs+2*(bw-7)
	#######################
	def _bTitle(x,y,button,text):
		bs.textWidget(parent=self._rootWidget,text=text,position=(x+bw*0.47,y+bh*0.22),
					  maxWidth=bw*0.7,size=(0,0),hAlign='center',vAlign='center',drawController=button,
					  color=(0.7,0.9,0.7,1.0))

	# acb = self._accountButton = b = bs.buttonWidget(parent=self._rootWidget,autoSelect=True,position=(xOffs,v),size=(bw,bh),buttonType='square',
	#                                                label='',onActivateCall=self._doAccount)
	# _bTitle(xOffs,v,acb,R.accountText)
	# iw = ih = 110
	# bs.imageWidget(parent=self._rootWidget,position=(xOffs+bw*0.49-iw*0.5,v+45),size=(iw,ih),
	#                            texture=bs.getTexture('accountIcon'),drawController=acb)

	pb = self._profilesButton = b = bs.buttonWidget(parent=self._rootWidget,autoSelect=True,position=(xOffs,v),size=(bw,bh),buttonType='square',
											   label='',onActivateCall=self._doProfiles)
	_bTitle(xOffs,v,pb,R.playerProfilesText)
	iw = ih = 100
	bs.imageWidget(parent=self._rootWidget,position=(xOffs+bw*0.49-iw*0.5,v+43),size=(iw,ih),
							   texture=bs.getTexture('cuteSpaz'),drawController=pb)

	cb = self._controllersButton = b = bs.buttonWidget(parent=self._rootWidget,autoSelect=True,position=(xOffs2,v),size=(bw,bh),buttonType='square',
												  label='',onActivateCall=self._doControllers)
	_bTitle(xOffs2,v,cb,R.controllersText)
	iw = ih = 130
	bs.imageWidget(parent=self._rootWidget,position=(xOffs2+bw*0.49-iw*0.5,v+35),size=(iw,ih),
							   texture=bs.getTexture('controllerIcon'),drawController=cb)

	gb = self._graphicsButton = b = bs.buttonWidget(parent=self._rootWidget,autoSelect=True,position=(xOffs3,v),size=(bw,bh),buttonType='square',
											   label='',onActivateCall=self._doGraphics)
	_bTitle(xOffs3,v,gb,R.graphicsText)
	iw = ih = 110
	bs.imageWidget(parent=self._rootWidget,position=(xOffs3+bw*0.49-iw*0.5,v+42),size=(iw,ih),
							   texture=bs.getTexture('graphicsIcon'),drawController=gb)

	v -= (bh-10)


	ab = self._audioButton = b = bs.buttonWidget(parent=self._rootWidget,autoSelect=True,position=(xOffs4,v),size=(bw,bh),buttonType='square',
											label='',onActivateCall=self._doAudio)
	_bTitle(xOffs4,v,ab,R.audioText)
	iw = ih = 120
	bs.imageWidget(parent=self._rootWidget,position=(xOffs4+bw*0.49-iw*0.5+5,v+35),size=(iw,ih),
				   color=(1,1,0),
				   texture=bs.getTexture('audioIcon'),drawController=ab)


	avb = self._advancedButton = b = bs.buttonWidget(parent=self._rootWidget,autoSelect=True,position=(xOffs5,v),size=(bw,bh),buttonType='square',
													 label='',onActivateCall=self._doAdvanced)
	_bTitle(xOffs5,v,avb,R.advancedText)
	iw = ih = 120
	bs.imageWidget(parent=self._rootWidget,position=(xOffs5+bw*0.49-iw*0.5+5,v+35),size=(iw,ih),
				   color=(0.8,0.95,1),
				   texture=bs.getTexture('advancedIcon'),drawController=avb)



	####NEWSTUFF####
	mb = self._modManagerButton = b = bs.buttonWidget(parent=self._rootWidget,autoSelect=True,position=(xOffs6,v),size=(bw,bh),buttonType='square',
													 label='',onActivateCall=self._doModManager)
	_bTitle(xOffs6,v,mb, 'Mod Manager')
	iw = ih = 120
	bs.imageWidget(parent=self._rootWidget,position=(xOffs6+bw*0.49-iw*0.5+5,v+35),size=(iw,ih),
				   color=(0.8,0.95,1),
				   texture=bs.getTexture('heart'),drawController=mb)
	################

	# self._profilesButton = b = bs.buttonWidget(parent=self._rootWidget,position=(53,v),size=(width-110,buttonHeight),
	#                                            label=R.playerProfilesText,onActivateCall=self._doProfiles)
	# v -= spacing * 1.6
	# self._controllersButton = b = bs.buttonWidget(parent=self._rootWidget,position=(61,v),size=(width-110,buttonHeight),
	#                                               label=R.controllersText,onActivateCall=self._doControllers)
	# v -= spacing * 1.6

	# self._graphicsButton = b = bs.buttonWidget(parent=self._rootWidget,position=(51,v),size=(width-110,buttonHeight),
	#                                            label=R.graphicsText,onActivateCall=self._doGraphics)
	# v -= spacing * 1.6
	# self._audioButton = b = bs.buttonWidget(parent=self._rootWidget,position=(57,v),size=(width-110,buttonHeight),
	#                                         label=R.audioText,onActivateCall=self._doAudio)
	# v -= spacing * 1.4
	# avb = self._advancedButton = b = bs.buttonWidget(parent=self._rootWidget,position=(59,v),size=(width-110,buttonHeight),
	#                                                  label=R.advancedText,onActivateCall=self._doAdvanced,
	#                                                  color=(0.55,0.5,0.6),
	#                                                  textColor=(0.65,0.6,0.7),
	# )

	# bs.buttonWidget(edit=acb,downWidget=gb)
	# bs.buttonWidget(edit=pb,downWidget=ab,upWidget=self._backButton)
	# bs.buttonWidget(edit=cb,downWidget=avb,upWidget=self._backButton)
	# bs.buttonWidget(edit=gb,upWidget=acb)
	# bs.buttonWidget(edit=ab,upWidget=pb)
	# bs.buttonWidget(edit=avb,upWidget=cb)
	# bs.buttonWidget(edit=cb,downWidget=ab)
	# bs.buttonWidget(edit=gb,downWidget=avb,upWidget=pb)
	# bs.buttonWidget(edit=ab,downWidget=avb,upWidget=cb)
	# bs.buttonWidget(edit=avb,upWidget=gb)

	# if 0:
	#     v -= spacing * 1.57
	#     configCheckBox(parent=self._rootWidget,position=(60,v),size=(width-100,30),name="Show Player Names",displayName=R.showPlayerNamesText,scale=0.9)
	#     v -= spacing * 1.27
	#     configCheckBox(parent=self._rootWidget,position=(60,v),size=(width-100,30),name="Kick Idle Players",displayName=R.kickIdlePlayersText,scale=0.9)
	#     v -= spacing * 0.63

	#     thisButtonWidth = 140
	#     b = bs.buttonWidget(parent=self._rootWidget,position=(width/2-thisButtonWidth/2,v-14),
	#                         color=(0.45,0.4,0.5),
	#                         size=(thisButtonWidth,22),
	#                         label=R.enterPromoCodeText,
	#                         textColor=(0.55,0.5,0.6),
	#                         textScale=0.7,
	#                         onActivateCall=PromoCodeWindow)


	self._restoreState()

	# re-select previous if applicable
	# selected = None
	# try:
	#     global gSettingsSelection
	#     try: selName = gSettingsSelection
	#     except Exception: selName = ''
	#     if selName == 'Account': selected = self._accountButton
	#     elif selName == 'Profiles': selected = self._profilesButton
	#     elif selName == 'Controllers': selected = self._controllersButton
	#     elif selName == 'Graphics': selected = self._graphicsButton
	#     elif selName == 'Audio': selected = self._audioButton
	#     elif selName == 'Advanced': selected = self._advancedButton
	# except Exception,ex:
	#     print 'Exception restoring settings UI state:',ex

	# if selected is not None: bs.containerWidget(edit=self._rootWidget,selectedChild=selected)
	# else: bs.containerWidget(edit=self._rootWidget,selectedChild=self._accountButton)

oldInit = SettingsWindow.__init__
SettingsWindow.__init__ = newInit


def _cb_checkUpdateData(self, data):
	if data:
		mods = [Mod(d) for d in data.values()]
		for mod in mods:
			if mod.isInstalled():
				if mod.checkUpdate():
					bs.screenMessage("Update for "+mod.name+" available! Check the ModManager")





oldMainInit = MainMenuWindow.__init__

def newMainInit(self, transition='inRight'):
	global checkedMainMenu
	oldMainInit(self, transition)
	if checkedMainMenu: return
	else: checkedMainMenu = True
	if config.get("auto-check-updates", True):
		mm_serverGet(INDEX_FILE(), {}, self._cb_checkUpdateData)

MainMenuWindow.__init__ = newMainInit
MainMenuWindow._cb_checkUpdateData = _cb_checkUpdateData
def _doModManager(self):
	bs.containerWidget(edit=self._rootWidget, transition='outLeft')
	mm_window = ModManagerWindow(backLocationCls=self.__class__)
	uiGlobals['mainMenuWindow'] = mm_window.getRootWidget()

SettingsWindow._doModManager = _doModManager




class MM_ServerCallThread(threading.Thread):

	def __init__(self, request, requestType, data, callback, eval_data=True):
		# Cant use the normal ServerCallThread because of the fixed Base-URL and eval

		threading.Thread.__init__(self)
		self._request = request.encode("ascii") # embedded python2.7 has weird encoding issues
		if not SUPPORTS_HTTPS and self._request.startswith("https://"):
			self._request = "http://" + self._request[8:]
		self._requestType = requestType
		self._data = {} if data is None else data
		self._eval_data = eval_data
		self._callback = callback

		self._context = bs.Context('current')

		# save and restore the context we were created from
		activity = bs.getActivity(exceptionOnNone=False)
		self._activity = weakref.ref(activity) if activity is not None else None

	def _runCallback(self,arg):

		# if we were created in an activity context and that activity has since died, do nothing
		# (hmm should we be using a context-call instead of doing this manually?)
		if self._activity is not None and (self._activity() is None or self._activity().isFinalized()): return

		# (technically we could do the same check for session contexts, but not gonna worry about it for now)
		with self._context: self._callback(arg)

	def run(self):
		try:
			bsInternal._setThreadName("MM_ServerCallThread")
			env = {'User-Agent': bs.getEnvironment()['userAgentString']}
			if self._requestType != "get" or self._data:
				if self._requestType == 'get':
					if self._data:
						request = urllib2.Request(self._request+'?'+urllib.urlencode(self._data), None, env)
					else:
						request = urllib2.Request(self._request, None, env)
				elif self._requestType == 'post':
					request = urllib2.Request(self._request, urllib.urlencode(self._data), env)
				else:
					raise RuntimeError("Invalid requestType: "+self._requestType)
				response = urllib2.urlopen(request)
			else:
				response = urllib2.urlopen(self._request)

			if self._eval_data:
				responseData = ast.literal_eval(response.read())
			else:
				responseData = response.read()
			if self._callback is not None:
				bs.callInGameThread(bs.Call(self._runCallback, responseData))

		except Exception, e:
			print(e)
			if self._callback is not None:
				bs.callInGameThread(bs.Call(self._runCallback, None))


def mm_serverGet(request, data, callback=None, eval_data=True):
	MM_ServerCallThread(request, 'get', data, callback, eval_data=eval_data).start()

def mm_serverPut(request, data, callback=None, eval_data=True):
	MM_ServerCallThread(request, 'post', data, callback, eval_data=eval_data).start()



class ModManagerWindow(Window):

	def __init__(self, transition='inRight', modal=False, showTab=None, onCloseCall=None, backLocationCls=None, originWidget=None):

		# if they provided an origin-widget, scale up from that
		if originWidget is not None:
			self._transitionOut = 'outScale'
			scaleOrigin = originWidget.getScreenSpaceCenter()
			transition = 'inScale'
		else:
			self._transitionOut = 'outRight'
			scaleOrigin = None


		self._backLocationCls = backLocationCls
		self._onCloseCall = onCloseCall
		self._showTab = showTab
		self._modal = modal

		self._windowTitleName = "Community Mod Manager"
		self.mods = []


		def sort_alphabetical(mods):
			return sorted(mods, key=lambda mod: mod.name.lower())

		def sort_playability(mods):
			bs.screenMessage('experimental mods hidden.')
			mods = sorted(self.mods, key=lambda mod: mod.playability, reverse=True)
			return [mod for mod in mods if (mod.playability > 0 or mod.isLocal)]

		self.sortModes = {
			'Alphabetical': {'func': sort_alphabetical, 'next': 'Playability'},
			'Playability': {'func': sort_playability, 'next': 'Alphabetical'}
		}

		smkeys = list(self.sortModes.keys())

		for i, key in enumerate(smkeys):
			self.sortModes[key]['index'] = i
			self.sortModes[key]['name'] = key
			self.sortModes[key]['next'] = smkeys[(i + 1) % len(smkeys)]

		sortMode = config.get('sortMode')
		if not sortMode or sortMode not in self.sortModes:
			sortMode = smkeys[0]
		self.sortMode = self.sortModes[sortMode]


		self._width = 650
		self._height = 380 if gSmallUI else 420 if gMedUI else 500
		spacing = 40
		buttonWidth = 350
		topExtra = 20 if gSmallUI else 0

		self._rootWidget = bs.containerWidget(size=(self._width,self._height+topExtra),transition=transition,
											  scale = 2.05 if gSmallUI else 1.5 if gMedUI else 1.0,
											  stackOffset=(0,-10) if gSmallUI else (0,0))

		self._backButton = backButton = b = bs.buttonWidget(parent=self._rootWidget, position=(self._width-160,self._height-60),
															size=(160,68), scale=0.77,
															autoSelect=True, textScale=1.3,
															label=bs.getResource('doneText' if self._modal else 'backText'),
															onActivateCall=self._back)
		bs.containerWidget(edit=self._rootWidget, cancelButton=b)
		t = bs.textWidget(parent=self._rootWidget,position=(0,self._height-47),
						  size=(self._width,25),
						  text=self._windowTitleName,color=gHeadingColor,
						  maxWidth=290,
						  hAlign="center",vAlign="center")


		v = self._height - 59
		h = 41
		hspacing = 15
		bColor = (0.6,0.53,0.63)
		bTextColor = (0.75,0.7,0.8)

		s = 1.1 if gSmallUI else 1.27 if gMedUI else 1.57
		v -= 63.0*s
		self.refreshButton = b = bs.buttonWidget(parent=self._rootWidget,position=(h,v),size=(90,58.0*s),
										onActivateCall=bs.Call(self._cb_refresh,),
										color=bColor,
										autoSelect=True,
										buttonType='square',
										textColor=bTextColor,
										textScale=0.7,
										label="Reload List")

		v -= 63.0*s
		self.modInfoButton = b = bs.buttonWidget(parent=self._rootWidget,position=(h,v),size=(90,58.0*s),
										   onActivateCall=bs.Call(self._cb_info),
										   color=bColor,
										   autoSelect=True,
										   textColor=bTextColor,
										   buttonType='square',
										   textScale=0.7,
										   label="Mod Info")

		v -= 63.0*s
		self.sortButtonData = {"s": s, "h": h, "v": v, "bColor": bColor, "bTextColor": bTextColor}
		self.sortButton = b = bs.buttonWidget(parent=self._rootWidget,position=(h,v),size=(90,58.0*s),
										   onActivateCall=bs.Call(self._cb_sorting),
										   color=bColor,
										   autoSelect=True,
										   textColor=bTextColor,
										   buttonType='square',
										   textScale=0.7,
										   label="Sorting:\n" + self.sortMode['name'])

		v -= 63.0*s
		self.settingsButton = b = bs.buttonWidget(parent=self._rootWidget,position=(h,v),size=(90,58.0*s),
										   onActivateCall=bs.Call(self._cb_settings),
										   color=bColor,
										   autoSelect=True,
										   textColor=bTextColor,
										   buttonType='square',
										   textScale=0.7,
										   label="Settings")

		v = self._height - 75
		self._scrollHeight = self._height - 119
		scrollWidget = bs.scrollWidget(parent=self._rootWidget,position=(140,v-self._scrollHeight),size=(self._width-180,self._scrollHeight+10))
		bs.widget(edit=backButton,downWidget=scrollWidget,leftWidget=scrollWidget)
		c = self._columnWidget = bs.columnWidget(parent=scrollWidget)



		h = 145
		v = self._height - self._scrollHeight - 109




		h += 210

		for b in [self.refreshButton, self.modInfoButton, self.settingsButton]:
			bs.widget(edit=b,rightWidget=scrollWidget)
		bs.widget(edit=scrollWidget,leftWidget=self.refreshButton)

		self._modWidgets = []

		self._cb_refresh()

		bs.buttonWidget(edit=backButton, onActivateCall=self._back)
		bs.containerWidget(edit=self._rootWidget, startButton=backButton, onCancelCall=backButton.activate)

		bs.containerWidget(edit=self._rootWidget, selectedChild=scrollWidget)



		#Submit stats every 10th launch
		#if True:#bs.getConfig()['launchCount'] % 10 == 0:
		#	bs.pushCall(bs.Call(self._cb_submit_stats))


	def _refresh(self):

		while len(self._modWidgets) > 0: self._modWidgets.pop().delete()

		self.mods = self.sortMode["func"](self.mods)

		index = 0
		for mod in self.mods:
			color = (0.6,0.6,0.7,1.0)
			if mod.isInstalled():
				color = (0.85,0.85,0.85,1)
				if mod.checkUpdate():
					color = (0.85, 0.3, 0.3, 1)
			w = bs.textWidget(parent=self._columnWidget,size=(self._width-40,24),
							  maxWidth=self._width-110,
							  text=mod.name,
							  hAlign='left',vAlign='center',
							  color=color,
							  alwaysHighlight=True,
							  onSelectCall=bs.Call(self._cb_select, index, mod),
							  onActivateCall=bs.Call(self._cb_info, True),
							  selectable=True)
			bs.widget(edit=w,showBufferTop=50,showBufferBottom=50)
			# hitting up from top widget shoud jump to 'back;
			if index == 0: bs.widget(edit=w,upWidget=self._backButton)
			index += 1
			self._modWidgets.append(w)

	def _cb_select(self, index, mod):
		self._selectedModIndex = index
		self._selectedMod = mod

	def _cb_refresh(self):
		#bs.screenMessage('Refreshing Modlist')
		self.mods = []
		request = None
		mm_serverGet(INDEX_FILE(), {}, self._cb_serverdata)
		localfiles = os.listdir(bs.getEnvironment()['userScriptsDirectory'] + "/")
		for file in localfiles:
			if file.endswith(".py"):
				self.mods.append(LocalMod(file))
		#if CHECK_FOR_UPDATES:
		#	for mod in self.mods:
		#		if mod.checkUpdate():
		#			bs.screenMessage('Update available for ' + mod.filename)
		#			UpdateModWindow(mod, self._cb_refresh)
		self._refresh()

	def _cb_serverdata(self, data):
		if data:
			if "version" in data and "mods" in data:
				data = data["mods"]
			#when we got network add the network mods
			localMods = self.mods[:]
			netMods = [Mod(d) for d in data.values()]
			self.mods = netMods
			netFilenames = [m.filename for m in netMods]
			for localmod in localMods:
				if localmod.filename not in netFilenames:
					self.mods.append(localmod)
			self._refresh()
		else:
			bs.screenMessage('network error :(')

	def _cb_info(self, withSound=False):
		if withSound:
			bs.playSound(bs.getSound('swish'))
		ModInfoWindow(self._selectedMod, self, originWidget=self.modInfoButton)

	def _cb_settings(self):
		SettingsWindow(self._selectedMod, self, originWidget=self.settingsButton)

	def _cb_sorting(self):
		self.sortMode = self.sortModes[self.sortMode['next']]
		config['sortMode'] = self.sortMode['name']
		bs.writeConfig()
		bs.buttonWidget(edit=self.sortButton, label="Sorting:\n" + self.sortMode['name'])
		self._cb_refresh()

	def _back(self):
		#self._saveState()
		#print("going back", self._modal, self._backLocationCls)
		bs.containerWidget(edit=self._rootWidget, transition=self._transitionOut)
		if not self._modal:
			uiGlobals['mainMenuWindow'] = self._backLocationCls(transition='inLeft').getRootWidget()
		if self._onCloseCall is not None:
			self._onCloseCall()



class UpdateModWindow(Window):

	def __init__(self, mod, onok, swish=True, back=False):
		self._back = back
		self.mod = mod
		self.onok = bs.WeakCall(onok)
		if swish:
			bs.playSound(bs.getSound('swish'))
		text = "Do you want to update %s?" if mod.isInstalled() else "Do you want to install %s?"
		text = text %(mod.filename)
		if mod.changelog and mod.isInstalled():
			text += "\n\nChangelog:"
			for change in mod.changelog:
				text += "\n"+change
		height = 100 * (1 + len(mod.changelog) * 0.3) if mod.isInstalled() else 100
		width = 360 * (1 + len(mod.changelog) * 0.15) if mod.isInstalled() else 360
		self._rootWidget = ConfirmWindow(text, self.ok, height=height, width=width).getRootWidget()

	def ok(self):
		self.mod.install(self.onok)

class DeleteModWindow(Window):

	def __init__(self, mod, onok, swish=True, back=False):
		self._back = back
		self.mod = mod
		self.onok = bs.WeakCall(onok)
		if swish:
			bs.playSound(bs.getSound('swish'))

		self._rootWidget = ConfirmWindow("Are you sure you want to delete " + mod.filename + "?",
														self.ok).getRootWidget()
	def ok(self):
		self.mod.delete(self.onok)
		QuitToApplyWindow()

class QuitToApplyWindow(Window):

	def __init__(self):
		global quittoapply
		if quittoapply is not None:
			quittoapply.delete()
			quittoapply = None
		bs.playSound(bs.getSound('swish'))
		text = "Quit BS to apply mod changes?"
		if bs.getEnvironment()["platform"] == "android":
			text += "\n(On Android you have to kill the activity)"
		self._rootWidget = quittoapply = ConfirmWindow(text,
														self._doFadeAndQuit).getRootWidget()

	def _doFadeAndQuit(self):
		bsInternal._fadeScreen(False, time=200, endCall=bs.Call(bs.quit, soft=True))
		bsInternal._lockAllInput()
		# unlock and fade back in shortly.. just in case something goes wrong
		# (or on android where quit just backs out of our activity and we may come back)
		bs.realTimer(300, bsInternal._unlockAllInput)
		#bs.realTimer(300,bs.Call(bsInternal._fadeScreen,True))



class ModInfoWindow(Window):
	def __init__(self, mod, modManagerWindow, originWidget=None):
		self.modManagerWindow = modManagerWindow
		self.mod = mod
		s = 1.1 if gSmallUI else 1.27 if gMedUI else 1.57
		bColor = (0.6,0.53,0.63)
		bTextColor = (0.75,0.7,0.8)
		width  = 360 * s
		height = 100 * s
		if mod.author:
			height += 25
		if not mod.isLocal:
			height += 50

		buttons = sum([(mod.checkUpdate() or not mod.isInstalled()), mod.isInstalled()])
		if buttons:
			height += 75

		color = (1, 1, 1)
		textScale = 1.0
		height += 40

		# if they provided an origin-widget, scale up from that
		if originWidget is not None:
			self._transitionOut = 'outScale'
			scaleOrigin = originWidget.getScreenSpaceCenter()
			transition = 'inScale'
		else:
			self._transitionOut = None
			scaleOrigin = None
			transition = 'inRight'

		self._rootWidget = bs.containerWidget(size=(width, height), transition=transition,
											  scale=2.1 if gSmallUI else 1.5 if gMedUI else 1.0,
											  scaleOriginStackOffset=scaleOrigin)

		#t = bs.textWidget(parent=self._rootWidget,position=(width*0.5,height-5-(height-75)*0.5),size=(0,0),
		#				  hAlign="center",vAlign="center",text=text,scale=textScale,color=color,maxWidth=width*0.9,maxHeight=height-75)
		pos = height * (0.9 if buttons else 0.8)
		labelspacing = height * (0.15 if buttons else 0.175)

		nameLabel = bs.textWidget(parent=self._rootWidget,position=(width*0.5, pos),size=(0,0),
								hAlign="center",vAlign="center",text=mod.name,scale=textScale * 1.5,
								color=color,maxWidth=width*0.9,maxHeight=height-75)
		pos -= labelspacing
		if mod.author:
			authorLabel = bs.textWidget(parent=self._rootWidget,position=(width*0.5, pos),size=(0,0),
									hAlign="center",vAlign="center",text="by "+mod.author,scale=textScale,
									color=color,maxWidth=width*0.9,maxHeight=height-75)
			pos -= labelspacing
		if not mod.isLocal:
			status = "update available" if mod.checkUpdate() else "installed"
			if not mod.isInstalled(): status = "not installed"
			statusLabel = bs.textWidget(parent=self._rootWidget,position=(width*0.45, pos),size=(0,0),
									hAlign="right",vAlign="center",text="Status:",scale=textScale,
									color=color,maxWidth=width*0.9,maxHeight=height-75)
			status = bs.textWidget(parent=self._rootWidget,position=(width*0.55, pos),size=(0,0),
									hAlign="left",vAlign="center",text=status,scale=textScale,
									color=color,maxWidth=width*0.9,maxHeight=height-75)
			pos -= labelspacing * 0.8

		if not mod.author and mod.isLocal:
			pos -= labelspacing


		if buttons > 0:
			pos -= labelspacing * 2.5
		self.button_index = -1
		def button_pos():
			self.button_index += 1
			d = {
				1: [0.5],
				2: [0.35, 0.65]
			}
			x = width * d[buttons][self.button_index]
			y = pos
			sx, sy = button_size()
			x -= sx / 2
			y += sy / 2
			return x, y

		def button_size():
			sx = {1: 120, 2: 100}[buttons]
			sy = 58*s
			return sx, sy

		def button_text_size():
			return {1: 0.8, 2: 1.0}[buttons]

		if mod.checkUpdate() or not mod.isInstalled():
			self.downloadButton = b = bs.buttonWidget(parent=self._rootWidget,
													  position=button_pos(), size=button_size(),
													  onActivateCall=bs.Call(self._download,),
													  color=bColor,
													  autoSelect=True,
													  textColor=bTextColor,
													  buttonType='square',
													  textScale=button_text_size(),
													  label="Update Mod" if mod.checkUpdate() else "Download Mod")

		if mod.isInstalled():
			self.deleteButton = b = bs.buttonWidget(parent=self._rootWidget,
													position=button_pos(), size=button_size(),
													onActivateCall=bs.Call(self._delete),
													color=bColor,
													autoSelect=True,
													textColor=bTextColor,
													buttonType='square',
													textScale=button_text_size(),
													label="Delete Mod")

		okButtonSize = (150, 50)
		okButtonPos = (width * 0.5 - okButtonSize[0]/2, 20)
		okText = bs.getResource('okText')
		b = bs.buttonWidget(parent=self._rootWidget, autoSelect=True, position=okButtonPos, size=okButtonSize, label=okText, onActivateCall=self._ok)

		# back on window = okbutton
		bs.containerWidget(edit=self._rootWidget,onCancelCall=b.activate)
		bs.containerWidget(edit=self._rootWidget,selectedChild=b,startButton=b)

	def _ok(self):
		bs.containerWidget(edit=self._rootWidget,transition='outLeft' if self._transitionOut is None else self._transitionOut)

	def _delete(self):
		DeleteModWindow(self.mod, self.modManagerWindow._cb_refresh)
		self._ok()

	def _download(self):
		UpdateModWindow(self.mod, self.modManagerWindow._cb_refresh)
		self._ok()





class SettingsWindow(Window):
	def __init__(self, mod, modManagerWindow, originWidget=None):
		self.modManagerWindow = modManagerWindow
		self.mod = mod
		s = 1.1 if gSmallUI else 1.27 if gMedUI else 1.57
		bColor = (0.6,0.53,0.63)
		bTextColor = (0.75,0.7,0.8)
		width  = 380 * s
		height = 200 * s
		textScale = 1.0

		# if they provided an origin-widget, scale up from that
		if originWidget is not None:
			self._transitionOut = 'outScale'
			scaleOrigin = originWidget.getScreenSpaceCenter()
			transition = 'inScale'
		else:
			self._transitionOut = None
			scaleOrigin = None
			transition = 'inRight'

		self._rootWidget = bs.containerWidget(size=(width, height), transition=transition,
											  scale=2.1 if gSmallUI else 1.5 if gMedUI else 1.0,
											  scaleOriginStackOffset=scaleOrigin)

		self._titleText = t = bs.textWidget(parent=self._rootWidget,position=(0, height - 52),
											size=(width, 30), text="ModManager Settings", color=(1.0, 1.0, 1.0),
											hAlign="center", vAlign="top", scale=1.5)

		pos = height * 0.65
		branchLabel = bs.textWidget(parent=self._rootWidget, position=(width*0.35, pos), size=(0, 40),
								hAlign="right", vAlign="center",
								text="Branch:", scale=textScale,
								color=bTextColor, maxWidth=width*0.9, maxHeight=height-75)
		self.branch = bs.textWidget(parent=self._rootWidget, position=(width*0.4, pos),
		 						size=(width * 0.4, 40), text=config.get("branch", "master"),
								hAlign="left", vAlign="center",
								editable=True, padding=4,
								onReturnPressCall=self.setBranch)

		pos -= height * 0.15
		checkUpdatesValue = config.get("auto-check-updates", True)
		checkUpdates = bs.checkBoxWidget(parent=self._rootWidget, text="auto check for updates",
										position=(width * 0.2, pos), size=(170, 30),
										textColor=(0.8, 0.8, 0.8),
										value=checkUpdatesValue,
										onValueChangeCall=self.setCheckUpdate)

		pos -= height * 0.2
		autoUpdatesValue = config.get("auto-update-old-mods", True)
		autoUpdates = bs.checkBoxWidget(parent=self._rootWidget, text="auto-update old mods",
										position=(width * 0.2, pos), size=(170, 30),
										textColor=(0.8, 0.8, 0.8),
										value=autoUpdatesValue,
										onValueChangeCall=self.setAutoUpdate)

		okButtonSize = (150, 50)
		okButtonPos = (width * 0.5 - okButtonSize[0]/2, 20)
		okText = bs.getResource('okText')
		b = bs.buttonWidget(parent=self._rootWidget, position=okButtonPos, size=okButtonSize, label=okText, onActivateCall=self._ok)

		# back on window = okbutton
		bs.containerWidget(edit=self._rootWidget, onCancelCall=b.activate)
		bs.containerWidget(edit=self._rootWidget, selectedChild=b, startButton=b)

		bs.widget(edit=backButton, upWidget=autoUpdates)
		bs.widget(edit=autoUpdates, upWidget=checkUpdates)
		bs.widget(edit=checkUpdates, upWidget=self.branch)

	def _ok(self):
		bs.containerWidget(edit=self._rootWidget,transition='outLeft' if self._transitionOut is None else self._transitionOut)

	def setBranch(self):
		branch = bs.textWidget(query=self.branch)
		bs.screenMessage("fetching branch '" + branch + "'")
		def cb(data):
			newBranch = branch
			if data:
				bs.screenMessage('ok')
			else:
				bs.screenMessage('failed to fetch branch')
				newBranch = "master"
			bs.screenMessage("set branch to " + newBranch)
			config["branch"] = newBranch
			bs.writeConfig()
			bs.textWidget(edit=self.branch, text=newBranch)

		mm_serverGet(INDEX_FILE(branch), {}, cb)

	def setCheckUpdate(self, val):
		config["auto-check-updates"] = bool(val)
		bs.writeConfig()

	def setAutoUpdate(self, val):
		config["auto-update-old-mods"] = bool(val)
		bs.writeConfig()




class Mod:
	name = False
	author = False
	filename = False
	changelog = []
	url = False
	# installs = 0
	isLocal = False
	playability = 0
	def __init__(self, d):
		self.loadFromDict(d)


	def loadFromDict(self, d):
		if 'author' in d:
			self.author = d['author']
		if 'filename' in d:
			self.filename = d['filename']
		else:
			raise RuntimeError('mod without filename')
		if 'name' in d:
			self.name = d['name']
		else: self.name = self.filename
		if 'md5' in d:
			self.md5 = d['md5']
		else:
			raise RuntimeError('mod without md5')
		if 'url' in d:
			self.url = d['url']
		else:
			raise RuntimeError('mod without url')
		if 'playability' in d:
			self.playability = d['playability']
		if 'changelog' in d:
			self.changelog = d['changelog']

		if self.isInstalled():
			path = bs.getEnvironment()['userScriptsDirectory'] + "/" + self.filename
			with open(path, "r") as ownFile:
				self.ownData = ownFile.read()

	def writeData(self, data):
		path = bs.getEnvironment()['userScriptsDirectory'] + "/" + self.filename

		if data:
			if self.isInstalled():
				os.rename(path, path + ".bak") # rename the old file to be able to recover it if something is wrong
			with open(path, 'w') as f:
				f.write(data)
		else:
			bs.screenMessage("Failed to write mod")

		self.install_temp_callback()
		QuitToApplyWindow()

	def install(self, callback):
		self.install_temp_callback = callback
		if self.url:
			mm_serverGet(self.url, {}, self.writeData, eval_data=False)
		else:
			bs.screenMessage("cannot download mod without url")


	def delete(self, cb=None):
		path = bs.getEnvironment()['userScriptsDirectory'] + "/" + self.filename
		os.rename(path, path+".bak") # rename the old file to be able to recover it if something is wrong
		if cb:
			cb()

	def checkUpdate(self):
		if not self.isInstalled():
			return False
		if md5(self.ownData).hexdigest() != self.md5:
			return True
		return False

	def isInstalled(self):
		return os.path.exists(bs.getEnvironment()['userScriptsDirectory'] + "/" + self.filename)

class LocalMod(Mod):
	isLocal = True
	def __init__(self, filename):
		self.filename = filename
		self.name = filename + " (Local Only)"

	def checkUpdate(self):
		return False

	def isInstalled(self):
		return True

	def getData(self):
		return False

	def writeData(self, data=None):
		bs.screenMessage("Can't update local-only mod!")



_setTabOld = StoreWindow._setTab
def _setTab(self, tab):
	_setTabOld(self, tab)
	if tab == "minigames":
		self._getMoreGamesButton = bs.buttonWidget(parent=self._rootWidget, autoSelect=True,
												   label=bs.getResource("addGameWindow").getMoreGamesText,
												   color=(0.54, 0.52, 0.67),
												   textColor=(0.7, 0.65, 0.7),
												   onActivateCall=self._onGetMoreGamesPress,
												   size=(178,50), position=(70, 60))
		# TODO: transitions
	else:
		if hasattr(self, "_getMoreGamesButton"):
			if self._getMoreGamesButton.exists():
				self._getMoreGamesButton.delete()

def _onGetMoreGamesPress(self):
	if not self._modal:
		bs.containerWidget(edit=self._rootWidget, transition='outLeft')
	mm_window = ModManagerWindow(modal=self._modal, backLocationCls=self.__class__)
	if not self._modal:
		uiGlobals['mainMenuWindow'] = mm_window.getRootWidget()

StoreWindow._setTab = _setTab
StoreWindow._onGetMoreGamesPress = _onGetMoreGamesPress
