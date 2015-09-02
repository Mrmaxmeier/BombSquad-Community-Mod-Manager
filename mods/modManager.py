from __future__ import print_function
import bs
import os
import urllib, urllib2
import json
import random
import time
from md5 import md5
from bsUI import *
from functools import partial

try:
	from settings_patcher import SettingsButton
except ImportError:
	bs.screenMessage("settings_patcher missing", color(1, 0, 0))
	raise
try:
	from ui_wrappers import *
except ImportError:
	bs.screenMessage("ui_wrappers missing", color(1, 0, 0))
	raise

PROTOCOL_VERSION = 1.0
SUPPORTS_HTTPS = False
TESTING = False

quittoapply = None
checkedMainMenu = False


if not 'mod_manager_config' in bs.getConfig():
	bs.getConfig()['mod_manager_config'] = {}
	bs.writeConfig()

config = bs.getConfig()['mod_manager_config']

def index_file(branch=None):
	if branch:
		return "https://rawgit.com/Mrmaxmeier/BombSquad-Community-Mod-Manager/" + branch + "/index.json"
	return "https://rawgit.com/Mrmaxmeier/BombSquad-Community-Mod-Manager/" + config.get("branch", "master") + "/index.json"

web_cache = config.get("web_cache", {})
config["web_cache"] = web_cache


def get_index(callback, branch=None, force=False):
	if TESTING:
		bs.screenMessage("NOTE: ModManager offline mode enabled", color=(1, 1, 0))
		bs.screenMessage("NOTE: branches arn't supported", color=(1, 1, 0))
		if not os.path.isfile(bs.getEnvironment()['userScriptsDirectory'] + "/../index.json"):
			bs.screenMessage("NOTE: index.json not found", color=(1, 0, 0))
			return
		with open(bs.getEnvironment()['userScriptsDirectory'] + "/../index.json", "r") as f:
			callback(json.load(f))
			return
	url = index_file(branch)
	def cache(data):
		if data:
			web_cache[url] = (data, time.time())
			bs.writeConfig()

	def f(data):
		# TODO: cancel prev fetchs
		callback(data)
		cache(data)

	if force:
		mm_serverGet(url, {}, f)
		return

	if url in web_cache:
		data, timestamp = web_cache[url]
		if timestamp + 10 * 30 > time.time():
			mm_serverGet(url, {}, cache)
		if timestamp + 10 * 60 > time.time():
			callback(data)
			return

	mm_serverGet(url, {}, f)

def process_server_data(data):
	mods = data["mods"]
	version = data["version"]
	if version - 0.5 > PROTOCOL_VERSION:
		print("version diff:", version, PROTOCOL_VERSION)
		bs.screenMessage("please update the mod manager")
	return mods, version


def _cb_checkUpdateData(self, data):
	try:
		if data:
			m, v = process_server_data(data)
			mods = [Mod(d) for d in m.values()]
			for mod in mods:
				if mod.isInstalled() and mod.checkUpdate():
					if config.get("auto-update-old-mods", True) and mod.old_md5s:
						if mod.local_md5() in mod.old_md5s:
							bs.screenMessage("updating '" + str(mod.name) + "'")
							def cb(mod, success):
								if success:
									bs.screenMessage("'" + str(mod.name) + "' updated")
							mod.install(cb)
					else:
						if not (mod.old_md5s and mod.local_md5() in mod.old_md5s):
							bs.screenMessage("Update for '" + mod.name + "' available! Check the ModManager")
	except Exception, e:
		bs.printException()
		bs.screenMessage("failed to check for updates")





oldMainInit = MainMenuWindow.__init__

def newMainInit(self, transition='inRight'):
	global checkedMainMenu
	oldMainInit(self, transition)
	if checkedMainMenu: return
	checkedMainMenu = True
	if config.get("auto-check-updates", True):
		get_index(self._cb_checkUpdateData)

MainMenuWindow.__init__ = newMainInit
MainMenuWindow._cb_checkUpdateData = _cb_checkUpdateData

def _doModManager(swinstance):
	swinstance._saveState()
	bs.containerWidget(edit=swinstance._rootWidget, transition='outLeft')
	mm_window = ModManagerWindow(backLocationCls=swinstance.__class__)
	uiGlobals['mainMenuWindow'] = mm_window.getRootWidget()

SettingsButton(id="ModManager", icon="heart", sorting_position=6) \
	.setCallback(_doModManager) \
	.setText("Mod Manager") \
	.add()

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
			bsInternal._setThreadName("MM_ServerCallThread") # FIXME: using protected apis
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
				responseData = json.loads(response.read())
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
	_selectedMod, _selectedModIndex = None, None
	categories = set(["all"])
	tabs = []
	tabheight = 35
	mods = []
	_modWidgets = []
	currently_fetching = False
	timers = {}


	def __init__(self, transition='inRight', modal=False, showTab="all", onCloseCall=None, backLocationCls=None, originWidget=None):

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
		self._selectedTab = {'label': showTab}
		if showTab != "all":
			def check_tab_available():
				if not self._rootWidget.exists():
					return
				if any([mod.category == showTab for mod in self.mods]):
					return
				if "button" in self._selectedTab:
					return
				self._selectedTab = {"label": "all"}
				self._refresh()
			self.timers["check_tab_available"] = bs.Timer(300, check_tab_available, timeType='real')
		self._modal = modal

		self._windowTitleName = "Community Mod Manager"


		def sort_alphabetical(mods):
			return sorted(mods, key=lambda mod: mod.name.lower())

		def sort_playability(mods):
			mods = sorted(self.mods, key=lambda mod: mod.playability, reverse=True)
			if self._selectedTab["label"] == "minigames":
				bs.screenMessage('experimental minigames hidden.')
				return [mod for mod in mods if (mod.playability > 0 or mod.isLocal or mod.category != "minigames")]
			return mods

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
										onActivateCall=bs.Call(self._cb_refresh, force=True),
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
		self.columnPosY = self._height - 75 - self.tabheight
		self._scrollHeight = self._height - 119 - self.tabheight
		scrollWidget = bs.scrollWidget(parent=self._rootWidget,position=(140,self.columnPosY - self._scrollHeight),size=(self._width-180,self._scrollHeight+10))
		bs.widget(edit=backButton, downWidget=scrollWidget, leftWidget=scrollWidget) # FIXME: select Tabs
		c = self._columnWidget = bs.columnWidget(parent=scrollWidget)

		for b in [self.refreshButton, self.modInfoButton, self.settingsButton]:
			bs.widget(edit=b, rightWidget=scrollWidget)
		bs.widget(edit=scrollWidget, leftWidget=self.refreshButton)

		self._cb_refresh()

		bs.buttonWidget(edit=backButton, onActivateCall=self._back)
		bs.containerWidget(edit=self._rootWidget, startButton=backButton, onCancelCall=backButton.activate)

		bs.containerWidget(edit=self._rootWidget, selectedChild=scrollWidget)


	def _refresh(self, refreshTabs=True):
		while len(self._modWidgets) > 0:
			self._modWidgets.pop().delete()

		for mod in self.mods:
			if mod.category and not mod.category in self.categories:
				self.categories.add(mod.category)
		if refreshTabs: self._refreshTabs()

		self.mods = self.sortMode["func"](self.mods)
		visible = self.mods[:]
		if self._selectedTab["label"] != "all":
			visible = [m for m in visible if m.category == self._selectedTab["label"]]

		for index, mod in enumerate(visible):
			color = (0.6,0.6,0.7,1.0)
			if mod.isInstalled():
				color = (0.85, 0.85, 0.85,1)
				if mod.checkUpdate():
					if mod.local_md5() in mod.old_md5s:
						color = (0.85, 0.3, 0.3, 1)
					else:
						color = (1, 0.84, 0, 1)

			w = bs.textWidget(parent=self._columnWidget, size=(self._width - 40, 24),
							  maxWidth=self._width - 110,
							  text=mod.name,
							  hAlign='left',vAlign='center',
							  color=color,
							  alwaysHighlight=True,
							  onSelectCall=bs.Call(self._cb_select, index, mod),
							  onActivateCall=bs.Call(self._cb_info, True),
							  selectable=True)
			bs.widget(edit=w, showBufferTop=50, showBufferBottom=50)
			# hitting up from top widget shoud jump to 'back;
			if index == 0:
				tab_button = self.tabs[int((len(self.tabs)-1)/2)]["button"]
				bs.widget(edit=w, upWidget=tab_button)

			if self._selectedMod and mod.filename == self._selectedMod.filename:
				bs.containerWidget(edit=self._columnWidget, selectedChild=w, visibleChild=w)

			self._modWidgets.append(w)

	def _refreshTabs(self):
		if not self._rootWidget.exists():
			return
		for t in self.tabs:
			for widget in t.values():
				if isinstance(widget, bs.Widget):
					widget.delete()
		self.tabs = []
		total = len(self.categories)
		columnWidth = self._width - 180
		tabWidth = 100
		tabSpacing = 12
		# _______/-minigames-\_/-utilities-\_______
		for i, tab in enumerate(sorted(list(self.categories))):
			px = 140 + columnWidth / 2 - tabWidth * total / 2 + tabWidth * i
			pos = (px, self.columnPosY + 5)
			size = (tabWidth - tabSpacing, self.tabheight + 10)
			rad = 10
			center = (pos[0] + 0.1*size[0], pos[1] + 0.9 * size[1])
			txt = bs.textWidget(parent=self._rootWidget, position=center, size=(0, 0),
								hAlign='center', vAlign='center',
								maxWidth=1.4*rad, scale=0.6, shadow=1.0, flatness=1.0)
			button = bs.buttonWidget(parent=self._rootWidget, position=pos, autoSelect=True,
									 buttonType='tab', size=size, label=tab, enableSound=False,
									 onActivateCall=bs.Call(self._cb_select_tab, i),
									 color=(0.52, 0.48, 0.63), textColor=(0.65, 0.6, 0.7))
			self.tabs.append({'text': txt,
							  'button': button,
							  'label': tab})

		for i, tab in enumerate(self.tabs):
			if self._selectedTab["label"] == tab["label"]:
				self._cb_select_tab(i, refresh=False)

	def _cb_select_tab(self, index, refresh=True):
		bs.playSound(bs.getSound('click01'))
		self._selectedTab = self.tabs[index]
		label = self._selectedTab["label"]

		for i, tab in enumerate(self.tabs):
			button = tab["button"]
			if i == index:
				bs.buttonWidget(edit=button, color=(0.5, 0.4, 0.93), textColor=(0.85, 0.75, 0.95)) # lit
			else:
				bs.buttonWidget(edit=button, color=(0.52, 0.48, 0.63), textColor=(0.65, 0.6, 0.7)) # unlit
		if refresh:
			self._refresh(refreshTabs=False)

	def _cb_select(self, index, mod):
		self._selectedModIndex = index
		self._selectedMod = mod

	def _cb_refresh(self, force=False):
		self.mods = []
		request = None
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
		self.currently_fetching = True
		get_index(self._cb_serverdata, force=force)
		self.timers["showFetchingIndicator"] = bs.Timer(500, bs.WeakCall(self._showFetchingIndicator), timeType='real')

	def _cb_serverdata(self, data):
		self.currently_fetching = False
		if data:
			m, v = process_server_data(data)
			#when we got network add the network mods
			localMods = self.mods[:]
			netMods = [Mod(d) for d in m.values()]
			self.mods = netMods
			netFilenames = [m.filename for m in netMods]
			for localmod in localMods:
				if localmod.filename not in netFilenames:
					self.mods.append(localmod)
			self._refresh()
		else:
			bs.screenMessage('network error :(')

	def _showFetchingIndicator(self):
		if self.currently_fetching:
			bs.screenMessage("loading...")

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
		self.mod.install(lambda mod, success: self.onok())

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
		text = "Quit BS to reload mods?"
		if bs.getEnvironment()["platform"] == "android":
			text += "\n(On Android you have to kill the activity)"
		self._rootWidget = quittoapply = ConfirmWindow(text, self._doFadeAndQuit).getRootWidget()

	def _doFadeAndQuit(self):
		# FIXME: using protected apis
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
		textScale = 0.7 * s
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
			if mod.checkUpdate():
				if mod.local_md5() in mod.old_md5s:
					status = "update available"
				else:
					status = "unrecognized version"
			else:
				status = "installed"
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

		if not (gSmallUI or gMedUI):
			pos -= labelspacing * 0.25

		if buttons > 0:
			pos -= labelspacing * 2

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
			sx = {1: 100, 2: 80}[buttons] * s
			sy = 58 * s
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

		okButtonSize = (130 * s, 40 * s)
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
		height = 240 * s
		textScale = 0.7 * s

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
											hAlign="center", vAlign="top", scale=1.5 * textScale)

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
		self.checkUpdates = bs.checkBoxWidget(parent=self._rootWidget, text="auto check for updates",
											position=(width * 0.2, pos), size=(170, 30),
											textColor=(0.8, 0.8, 0.8),
											value=checkUpdatesValue,
											onValueChangeCall=self.setCheckUpdate)
		self.setCheckUpdateVal = checkUpdatesValue

		pos -= height * 0.2
		autoUpdatesValue = config.get("auto-update-old-mods", True)
		self.autoUpdates = bs.checkBoxWidget(parent=self._rootWidget, text="auto-update old mods",
											position=(width * 0.2, pos), size=(170, 30),
											textColor=(0.8, 0.8, 0.8),
											value=autoUpdatesValue,
											onValueChangeCall=self.setAutoUpdate)
		self.checkAutoUpdateState()

		okButtonSize = (150, 50)
		okButtonPos = (width * 0.5 - okButtonSize[0]/2, 20)
		okText = bs.getResource('okText')
		b = bs.buttonWidget(parent=self._rootWidget, position=okButtonPos, size=okButtonSize, label=okText, onActivateCall=self._ok)

		# back on window = okbutton
		bs.containerWidget(edit=self._rootWidget, onCancelCall=b.activate)
		bs.containerWidget(edit=self._rootWidget, selectedChild=b, startButton=b)

		bs.widget(edit=b, upWidget=self.autoUpdates)
		bs.widget(edit=self.autoUpdates, upWidget=self.checkUpdates)
		bs.widget(edit=self.checkUpdates, upWidget=self.branch)

	def _ok(self):
		if bs.textWidget(query=self.branch) != config.get("branch", "master"):
			# FIXME: setBranch doesnt get triggered immediately with onscreen input
			self.setBranch()
		bs.containerWidget(edit=self._rootWidget,transition='outLeft' if self._transitionOut is None else self._transitionOut)

	def setBranch(self):
		branch = bs.textWidget(query=self.branch)
		if branch == '':
			branch = "master"
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
			if self.branch.exists():
				bs.textWidget(edit=self.branch, text=newBranch)
			self.modManagerWindow._cb_refresh()

		get_index(cb, branch=branch)

	def setCheckUpdate(self, val):
		self.setCheckUpdateVal = val
		config["auto-check-updates"] = bool(val)
		bs.writeConfig()
		self.checkAutoUpdateState()

	def checkAutoUpdateState(self):
		if not self.setCheckUpdateVal:
			# FIXME: properly disable checkbox
			bs.checkBoxWidget(edit=self.autoUpdates, value=False,
							  color=(0.65,0.65,0.65), textColor=(0.65,0.65,0.65))
		else:
			# FIXME: match original color
			autoUpdatesValue = config.get("auto-update-old-mods", True)
			bs.checkBoxWidget(edit=self.autoUpdates, value=autoUpdatesValue,
							  color=(0.475, 0.6, 0.2), textColor=(0.8, 0.8, 0.8))

	def setAutoUpdate(self, val):
		# FIXME: properly disable checkbox
		# FIXME: find some way to query checkboxes
		#if not bs.checkBoxWidget(query=self.checkUpdates):
		if not self.setCheckUpdateVal:
			bs.playSound(bs.getSound("error"))
			bs.checkBoxWidget(edit=self.autoUpdates, value=0)
			return
		config["auto-update-old-mods"] = bool(val)
		bs.writeConfig()




class Mod:
	name = False
	author = None
	filename = False
	changelog = []
	old_md5s = []
	url = False
	isLocal = False
	playability = 0
	category = None
	requires = []
	supports = []
	def __init__(self, d):
		self.loadFromDict(d)


	def loadFromDict(self, d):
		self.author = d.get('author')
		if 'filename' in d:
			self.filename = d['filename']
		else:
			print(d)
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

		self.playability = d.get('playability', 0)
		self.changelog = d.get('changelog', [])
		self.old_md5s = d.get('old_md5s', [])
		self.category = d.get('category', None)
		self.requires = d.get('requires', [])
		self.supports = d.get('supports', [])

		if self.isInstalled():
			path = bs.getEnvironment()['userScriptsDirectory'] + "/" + self.filename
			with open(path, "r") as ownFile:
				self.ownData = ownFile.read()

	def writeData(self, callback, doQuitWindow, data):
		path = bs.getEnvironment()['userScriptsDirectory'] + "/" + self.filename

		if data:
			if self.isInstalled():
				os.rename(path, path + ".bak") # rename the old file to be able to recover it if something is wrong
			with open(path, 'w') as f:
				f.write(data)
		else:
			bs.screenMessage("Failed to write mod")

		if callback:
			callback(self, data is not None)
		if doQuitWindow:
			QuitToApplyWindow()

	def install(self, callback, doQuitWindow=True):
		if self.url:
			mm_serverGet(self.url, {}, partial(self.writeData, callback, doQuitWindow), eval_data=False)
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
		if self.local_md5() != self.md5:
			return True
		return False

	def isInstalled(self):
		return os.path.exists(bs.getEnvironment()['userScriptsDirectory'] + "/" + self.filename)

	def local_md5(self):
		return md5(self.ownData).hexdigest()

class LocalMod(Mod):
	isLocal = True
	def __init__(self, filename):
		self.filename = filename
		self.name = filename + " (Local Only)"
		with open(bs.getEnvironment()['userScriptsDirectory'] + "/" + filename, "r") as ownFile:
			self.ownData = ownFile.read()

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
	if hasattr(self, "_getMoreGamesButton"):
		if self._getMoreGamesButton.exists():
			self._getMoreGamesButton.delete()
	if tab == "minigames":
		self._getMoreGamesButton = bs.buttonWidget(parent=self._rootWidget, autoSelect=True,
												   label=bs.getResource("addGameWindow").getMoreGamesText,
												   color=(0.54, 0.52, 0.67),
												   textColor=(0.7, 0.65, 0.7),
												   onActivateCall=self._onGetMoreGamesPress,
												   size=(178,50), position=(70, 60))
		# TODO: transitions

def _onGetMoreGamesPress(self):
	if not self._modal:
		bs.containerWidget(edit=self._rootWidget, transition='outLeft')
	mm_window = ModManagerWindow(modal=self._modal, backLocationCls=self.__class__, showTab="minigames")
	if not self._modal:
		uiGlobals['mainMenuWindow'] = mm_window.getRootWidget()

StoreWindow._setTab = _setTab
StoreWindow._onGetMoreGamesPress = _onGetMoreGamesPress
