import bs
import os
import urllib2, httplib, urllib
import ast
import random
from md5 import md5
# no json in BombSquad-Python :'(
from bsUI import *


PORT = "3666"
DATASERVER = "http://thuermchen.com"+":"+PORT
#should now be online :)


#DATASERVER = "http://localhost"+":"+PORT

CHECK_FOR_UPDATES = True

quittoapply = None
checkedMainMenu = False


if 'mm_uniqueID' in bs.getConfig():
	uniqueID = bs.getConfig()['mm_uniqueID']
else:
	uniqueID = random.randint(0, 2**16-1)
	bs.getConfig()['mm_uniqueID'] = uniqueID
	bs.writeConfig()




def newInit(self,transition='inRight'):

		width = 750 if gSmallUI else 580
		height = 435

		buttonHeight = 42

		R = bs.getResource('settingsWindow')

		topExtra = 20 if gSmallUI else 0
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
		mods = [Mod(d) for d in data]
		for mod in mods:
			if mod.isInstalled():
				if mod.checkUpdate():
					bs.screenMessage("Update for "+mod.name+" available! Check the ModManager")#_doModManager(self) thats totally annoing





oldMainInit = MainMenuWindow.__init__
def newMainInit(self, transition='inRight'):
	global checkedMainMenu
	oldMainInit(self, transition)
	if not CHECK_FOR_UPDATES: return
	if checkedMainMenu: return
	else: checkedMainMenu = True
	mm_serverGet(DATASERVER+"/getModList", {}, self._cb_checkUpdateData)
MainMenuWindow.__init__ = newMainInit
MainMenuWindow._cb_checkUpdateData = _cb_checkUpdateData
def _doModManager(self):
	#self._saveState() doesn't work for some wierd reason
	bs.containerWidget(edit=self._rootWidget,transition='outLeft')
	uiGlobals['mainMenuWindow'] = ModManagerWindow().getRootWidget()

SettingsWindow._doModManager = _doModManager




class MM_ServerCallThread(threading.Thread):
		
	def __init__(self,request,requestType,data,callback, eval_data=True):
		# Cant use the normal ServerCallThread because of the fixed Base-URL and eval
		
		threading.Thread.__init__(self)
		self._request = request
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
			if self._requestType == 'get':
				response = urllib2.urlopen(urllib2.Request(self._request+'?'+urllib.urlencode(self._data),
														   None,
														   { 'User-Agent' : bs.getEnvironment()['userAgentString'] }))
			elif self._requestType == 'post':
				response = urllib2.urlopen(urllib2.Request(self._request,
														   urllib.urlencode(self._data),
														   { 'User-Agent' : bs.getEnvironment()['userAgentString'] }))
			else: raise Exception("Invalid requestType: "+self._requestType)
			if self._eval_data:
				responseData = ast.literal_eval(response.read())
			else:
				responseData = response.read()
			if self._callback is not None: bs.callInGameThread(bs.Call(self._runCallback,responseData))
		except Exception,e:
			print(e)
			if self._callback is not None: bs.callInGameThread(bs.Call(self._runCallback,None))


def mm_serverGet(request,data,callback=None, eval_data=True):
	MM_ServerCallThread(request,'get',data,callback, eval_data=eval_data).start()

def mm_serverPut(request,data,callback=None, eval_data=True):
	MM_ServerCallThread(request,'post',data,callback, eval_data=eval_data).start()



class ModManagerWindow(Window):

	def __init__(self,transition='inRight'):

		self._windowTitleName = "Community Mod Manager"
		self.mods = []
		

		self._width = 650
		self._height = 380 if gSmallUI else 420 if gMedUI else 500
		spacing = 40
		buttonWidth = 350
		topExtra = 20 if gSmallUI else 0
		
		self._rootWidget = bs.containerWidget(size=(self._width,self._height+topExtra),transition=transition,
											  scale = 2.05 if gSmallUI else 1.5 if gMedUI else 1.0,
											  stackOffset=(0,-10) if gSmallUI else (0,0))

		self._backButton = backButton = b = bs.buttonWidget(parent=self._rootWidget,position=(self._width-160,self._height-60),size=(160,68),scale=0.77,
															autoSelect=True,textScale=1.3,label=bs.getResource('doneText'))
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
		s *= 4/5.0 # now with 5 buttons
		v -= 63.0*s
		self.refreshButton = b = bs.buttonWidget(parent=self._rootWidget,position=(h,v),size=(90,58.0*s),
										onActivateCall=bs.Call(self._cb_refresh,),
										color=bColor,
										autoSelect=True,
										buttonType='square',
										textColor=bTextColor,
										textScale=0.7,
										label="Refresh List")

		v -= 63.0*s
		self.downloadButton = b = bs.buttonWidget(parent=self._rootWidget,position=(h,v),size=(90,58.0*s),
															onActivateCall=bs.Call(self._cb_download,),
															color=bColor,
															autoSelect=True,
															textColor=bTextColor,
															buttonType='square',
															textScale=0.7,
															label="Download Mod")

		v -= 63.0*s
		self.deleteButton = b = bs.buttonWidget(parent=self._rootWidget,position=(h,v),size=(90,58.0*s),
											  onActivateCall=bs.Call(self._cb_delete),
											  color=bColor,
											  autoSelect=True,
											  textColor=bTextColor,
											  buttonType='square',
											  textScale=0.7,
											  label="Delete Mod")

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
										   label="Sorting:\nDownloads")

		#self.autoCheckUpdates = bs.checkBoxWidget(parent=self._rootWidget,position=(50 ,v-40),size=(250,50),color=(0.5,0.5,0.7),value=True,
		#													 autoSelect=True,onValueChangeCall=self._cb_update_checkbox,text="auto update",scale=0.8,textColor=(0.6,0.6,0.6,0.6))

		v = self._height - 75
		self._scrollHeight = self._height - 119
		scrollWidget = bs.scrollWidget(parent=self._rootWidget,position=(140,v-self._scrollHeight),size=(self._width-180,self._scrollHeight+10))
		bs.widget(edit=backButton,downWidget=scrollWidget,leftWidget=scrollWidget)
		c = self._columnWidget = bs.columnWidget(parent=scrollWidget)


		
		h = 145
		v = self._height - self._scrollHeight - 109


		

		h += 210
		
		for b in [self.refreshButton,self.downloadButton,self.deleteButton,self.modInfoButton]:
			bs.widget(edit=b,rightWidget=scrollWidget)
		bs.widget(edit=scrollWidget,leftWidget=self.refreshButton)
		
		self._modWidgets = []



		self.sortMode = 0
		self._cb_refresh()

		bs.buttonWidget(edit=backButton,onActivateCall=self._back)
		bs.containerWidget(edit=self._rootWidget,startButton=backButton,onCancelCall=backButton.activate)

		bs.containerWidget(edit=self._rootWidget,selectedChild=scrollWidget)



		#Submit stats every 10th launch
		if True:#bs.getConfig()['launchCount'] % 10 == 0:
			bs.pushCall(bs.Call(self._cb_submit_stats))


	def _back(self):

		bs.containerWidget(edit=self._rootWidget,transition='outRight')
		uiGlobals['mainMenuWindow'] = SettingsWindow(transition='inLeft').getRootWidget()



	def _refresh(self):

		while len(self._modWidgets) > 0: self._modWidgets.pop().delete()

		if self.sortMode == 0:
			#sort by downloads
			self.mods = sorted(self.mods, key=lambda mod: mod.installs, reverse=True)
		elif self.sortMode == 1:
			#sort by playablilty
			self.mods = sorted(self.mods, key=lambda mod: mod.playability, reverse=True)
			self.mods = [mod for mod in self.mods if mod.playability > 0]
		elif self.sortMode == 2:
			#sort by alphabetical
			self.mods = sorted(self.mods, key=lambda mod: mod.name.lower())

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
							  onActivateCall=bs.Call(self._cb_info),
							  selectable=True)
			bs.widget(edit=w,showBufferTop=50,showBufferBottom=50)
			# hitting up from top widget shoud jump to 'back;
			if index == 0: bs.widget(edit=w,upWidget=self._backButton)
			self._playlistWidgets.append(w)
			index += 1

	def _cb(self, text="no info"):
		bs.screenMessage('pressed smth. ('+text+')')

	def _cb_update_checkbox(self, switchedOn = False):
		bs.screenMessage("autoupdates activated" if switchedOn else "autoupdates deactivated")
		bs.getConfig()['mm_autoCheckUpdate'] = switchedOn

	def _cb_select(self, index, mod):
		self._selectedModIndex = index
		self._selectedMod = mod

	def _cb_refresh(self):
		#bs.screenMessage('Refreshing Modlist')
		self.mods = []
		request = None
		mm_serverGet(DATASERVER + "/getModList", {}, self._cb_serverdata)
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
			#when we got network add the network mods
			localMods = self.mods[:]
			netMods = [Mod(d) for d in data]
			self.mods = netMods
			netFilenames = [m.filename for m in netMods]
			for localmod in localMods:
				if localmod.filename not in netFilenames:
					self.mods.append(localmod)
			self._refresh()
		else:
			bs.screenMessage('network error :(')

	def _cb_download(self):
		UpdateModWindow(self._selectedMod, self._selectedMod.isInstalled(), self._cb_refresh)

	def _cb_delete(self):
		DeleteModWindow(self._selectedMod, self._cb_refresh)

	def _cb_info(self):
		ModInfoWindow(self._selectedMod, self.modInfoButton)

	def _cb_sorting(self):
		sortModes = ["Downloads", "Playablilty", "Alphabetical"]
		self.sortMode += 1
		self.sortMode = self.sortMode % 3
		bs.buttonWidget(edit=self.sortButton, label="Sorting:\n"+sortModes[self.sortMode])
		if self.sortMode == 1:
			bs.screenMessage("experimental mods hidden.")
		self._cb_refresh()

	def _cb_submit_stats(self):
		stats = bs.getEnvironment().copy()
		stats['uniqueID'] = uniqueID
		mods = os.listdir(bs.getEnvironment()['userScriptsDirectory'] + "/")
		mods = [m for m in mods if m.endswith(".py")]
		mods = [m for m in mods if not m.startswith(".")]
		stats['installedMods'] = mods
		# remove either private or long data
		del stats['userScriptsDirectory']
		del stats['systemScriptsDirectory']
		del stats['configFilePath']
		mm_serverGet(DATASERVER+"/submitStats", {"stats":repr(stats)}, self._cb_submitted_stats, eval_data=False)

	def _cb_submitted_stats(self, data):
		if data is not None:
			# if "" is returned the request was successful
			bs.screenMessage('submitted non-private stats')





class UpdateModWindow(Window):

	def __init__(self, mod, isUpdate, onkay, swish=True, back=False):
		self._back = back
		self.mod = mod
		self.onkay = bs.WeakCall(onkay)
		if swish:
			bs.playSound(bs.getSound('swish'))
		text = "Do you want to update %s?" if isUpdate else "Do you want to install %s?"
		text = text %(mod.filename)
		if mod.changelog and isUpdate:
			text += "\n\nChangelog:"
			for change in mod.changelog:
				text += "\n"+change
		height = 100*(1+len(mod.changelog)*0.3) if isUpdate else 100
		width = 360*(1+len(mod.changelog)*0.15) if isUpdate else 360
		self._rootWidget = ConfirmWindow(text, self.kay, height=height, width=width).getRootWidget()
	def kay(self):
		self.mod.install(self.onkay)

class DeleteModWindow(Window):

	def __init__(self, mod, onkay, swish=True, back=False):
		self._back = back
		self.mod = mod
		self.onkay = bs.WeakCall(onkay)
		if swish:
			bs.playSound(bs.getSound('swish'))
			
		self._rootWidget = ConfirmWindow("Are you sure you want to delete " + mod.filename + "?",
														self.kay).getRootWidget()
	def kay(self):
		self.mod.delete(self.onkay)
		QuitToApplyWindow()

class QuitToApplyWindow(Window):

	def __init__(self):
		global quittoapply
		if quittoapply is not None:
			quittoapply.delete()
			quittoapply = None
		bs.playSound(bs.getSound('swish'))
		text = "Quit BS to apply mod changes?"
		text += "\n(On Android you have to kill the activity)" if bs.getEnvironment()["platform"]=="android" else ""
		self._rootWidget = quittoapply = ConfirmWindow(text,
														self._doFadeAndQuit).getRootWidget()

	def _doFadeAndQuit(self):
		bsInternal._fadeScreen(False,time=200,endCall=bs.Call(bs.quit,soft=True))
		bsInternal._lockAllInput()
		# unlock and fade back in shortly.. just in case something goes wrong
		# (or on android where quit just backs out of our activity and we may come back)
		bs.realTimer(300,bsInternal._unlockAllInput)
		#bs.realTimer(300,bs.Call(bsInternal._fadeScreen,True))



class ModInfoWindow(Window):

	def __init__(self, mod, originWidget = None):
		width  = 360  * 1.25
		height = 100  * 1.25
		if mod.author: height += 25
		if not mod.isLocal: height += 50
		if mod.installs != 0: height += 25
		color=(1,1,1)
		textScale=1.0
		okText=None
		if okText is None: okText = bs.getResource('okText')
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
		
		self._rootWidget = bs.containerWidget(size=(width,height),transition=transition,
											  scale=2.1 if gSmallUI else 1.5 if gMedUI else 1.0,
											  scaleOriginStackOffset=scaleOrigin)

		#t = bs.textWidget(parent=self._rootWidget,position=(width*0.5,height-5-(height-75)*0.5),size=(0,0),
		#				  hAlign="center",vAlign="center",text=text,scale=textScale,color=color,maxWidth=width*0.9,maxHeight=height-75)
		pos = height * 0.8

		nameLabel = bs.textWidget(parent=self._rootWidget,position=(width*0.5, pos),size=(0,0),
								hAlign="center",vAlign="center",text=mod.name,scale=textScale * 1.5,
								color=color,maxWidth=width*0.9,maxHeight=height-75)
		pos -= height * 0.175
		if mod.author:
			authorLabel = bs.textWidget(parent=self._rootWidget,position=(width*0.5, pos),size=(0,0),
									hAlign="center",vAlign="center",text="by "+mod.author,scale=textScale,
									color=color,maxWidth=width*0.9,maxHeight=height-75)
			pos -= height * 0.175
		if not mod.isLocal:
			status = "update available" if mod.checkUpdate() else "installed"
			if not mod.isInstalled(): status = "not installed"
			statusLabel = bs.textWidget(parent=self._rootWidget,position=(width*0.45, pos),size=(0,0),
									hAlign="right",vAlign="center",text="Status:",scale=textScale,
									color=color,maxWidth=width*0.9,maxHeight=height-75)
			status = bs.textWidget(parent=self._rootWidget,position=(width*0.55, pos),size=(0,0),
									hAlign="left",vAlign="center",text=status,scale=textScale,
									color=color,maxWidth=width*0.9,maxHeight=height-75)
			pos -= height * 0.1
		if mod.installs != 0:
			downloadsLabel = bs.textWidget(parent=self._rootWidget,position=(width*0.45, pos),size=(0,0),
									hAlign="right",vAlign="center",text="Downloads:",scale=textScale,
									color=color,maxWidth=width*0.9,maxHeight=height-75)
			downloads = bs.textWidget(parent=self._rootWidget,position=(width*0.55, pos),size=(0,0),
									hAlign="left",vAlign="center",text=str(mod.installs),scale=textScale,
									color=color,maxWidth=width*0.9,maxHeight=height-75)
			pos -= height * 0.1
		
		okButtonH = width*0.5-75
		b = bs.buttonWidget(parent=self._rootWidget,autoSelect=True,position=(okButtonH,20),size=(150,50),label=okText,onActivateCall=self._ok)

		# back on window = okbutton
		bs.containerWidget(edit=self._rootWidget,onCancelCall=b.activate)
		bs.containerWidget(edit=self._rootWidget,selectedChild=b,startButton=b)

	def _ok(self):
		bs.containerWidget(edit=self._rootWidget,transition='outLeft' if self._transitionOut is None else self._transitionOut)




class Mod:
	name = False
	author = False
	filename = False
	changelog = []
	installs = 0
	isLocal = False
	playability = 0
	def __init__(self, d):
		self.loadFromDict(d)


	def loadFromDict(self, d):
		if 'author' in d: self.author = d['author']
		if 'filename' in d: self.filename = d['filename']
		else:
			raise RuntimeError('mod without filename')
		if 'name' in d: self.name = d['name']
		else: self.name = self.filename
		if 'md5' in d: self.md5 = d['md5']
		else:
			raise RuntimeError('mod without md5')
		if 'uniqueInstalls' in d: self.installs = d['uniqueInstalls']
		if 'playability' in d: self.playability = d['playability']
		if 'changelog' in d:
			self.changelog = d['changelog']

		if self.isInstalled():
			path = bs.getEnvironment()['userScriptsDirectory'] + "/" + self.filename
			ownfile = open(path, "r")
			self.ownData = ownfile.read()
			ownfile.close()

	def writeData(self, data):
		path = bs.getEnvironment()['userScriptsDirectory'] + "/" + self.filename
		
		if data:
			if self.isInstalled():
				os.rename(path, path+".bak")# rename the old file to be able to recover it if something is wrong
			f=open(path,'w')
			f.write(data)
			f.close()
		else:
			bs.screenMessage("Failed to write mod")

		self.install_temp_callback()
		QuitToApplyWindow()

	def install(self, callback):
		self.install_temp_callback = callback
		mm_serverGet(DATASERVER+"/getData", {"md5":self.md5}, self.writeData, eval_data=False)


	def delete(self, cb=None):
		path = bs.getEnvironment()['userScriptsDirectory'] + "/" + self.filename
		os.rename(path, path+".bak")# rename the old file to be able to recover it if something is wrong
		if cb:
			cb()

	def checkUpdate(self):
		if not self.isInstalled(): return False
		if md5(self.ownData).hexdigest() != self.md5: return True
		return False

	def isInstalled(self):
		return os.path.exists(bs.getEnvironment()['userScriptsDirectory'] + "/" + self.filename)
		#return False

class LocalMod(Mod):
	isLocal = True
	def __init__(self, filename):
		self.filename = filename
		self.name = filename + " (Local Only)"

	def checkUpdate(self): return False

	def isInstalled(self): return True

	def getData(self): return False

	def writeData(self): bs.screenMessage("Can't update local-only mod!")


