#ModManager#{"name": "Mod Manager (this thingy)", "author": "Mrmaxmeier"}#ModManager# <-- json stuff for the Mod Manager!

import bs
import os
import urllib2, httplib
import random
from md5 import md5
# no json in BombSquad-Python :'(
from bsUI import *


PORT = "3666"
DATASERVER = "http://thuermchen.com"+":"+PORT
#should now be online :)


#DATASERVER = "http://localhost"+":"+PORT


quittoapply = None


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


def checkUpdateMainMenu(self):
	try:
		self.mods = []
		request = None
		try:
			request = urllib2.urlopen(DATASERVER+"/getModList")
			networkData = eval(request.read()) # no json :(
			self.mods = [Mod(d) for d in networkData]
			for mod in self.mods:
				if mod.isInstalled():
					if mod.checkUpdate():
						_doModManager(self)
		except urllib2.HTTPError, e:
			bs.screenMessage('HTTPError = ' + str(e.code))
		except urllib2.URLError, e:
			bs.screenMessage('URLError = ' + str(e.reason))
		except httplib.HTTPException, e:
			bs.screenMessage('HTTPException')
	except Exception, e:
		print(e)
		return False


oldMainInit = MainMenuWindow.__init__
def newMainInit(self, transition='inRight'):
	oldMainInit(self, transition)
	self._checkUpdateTimer = bs.Timer(15000,bs.WeakCall(self.checkUpdateMainMenu),timeType='real')
MainMenuWindow.__init__ = newMainInit
MainMenuWindow.checkUpdateMainMenu = checkUpdateMainMenu

def _doModManager(self):
	#self._saveState() doesn't work for some wierd reason
	bs.containerWidget(edit=self._rootWidget,transition='outLeft')
	uiGlobals['mainMenuWindow'] = ModManagerWindow().getRootWidget()

SettingsWindow._doModManager = _doModManager



class ModManagerWindow(Window):

	def __init__(self,sessionType=bs.TeamsSession,transition='inRight',selectPlaylist="Mod Manager"):

		self._windowTitleName = "Community Mod Manager"
		self.mods = []
		

		self._sessionType = sessionType

		self._R = R = bs.getResource('gameListWindow')

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
		v -= 63.0*s
		refreshButton = b = bs.buttonWidget(parent=self._rootWidget,position=(h,v),size=(90,58.0*s),
										onActivateCall=bs.Call(self._cb_refresh,),
										color=bColor,
										autoSelect=True,
										buttonType='square',
										textColor=bTextColor,
										textScale=0.7,
										label="Refresh Index")

		v -= 63.0*s
		downloadButton = b = bs.buttonWidget(parent=self._rootWidget,position=(h,v),size=(90,58.0*s),
															onActivateCall=bs.Call(self._cb_download,),
															color=bColor,
															autoSelect=True,
															textColor=bTextColor,
															buttonType='square',
															textScale=0.7,
															label="Download Mod")

		v -= 63.0*s
		deleteButton = b = bs.buttonWidget(parent=self._rootWidget,position=(h,v),size=(90,58.0*s),
											  onActivateCall=bs.Call(self._cb_delete),
											  color=bColor,
											  autoSelect=True,
											  textColor=bTextColor,
											  buttonType='square',
											  textScale=0.7,
											  label="Delete Mod")

		v -= 63.0*s
		doSwagButton = b = bs.buttonWidget(parent=self._rootWidget,position=(h,v),size=(90,58.0*s),
										   onActivateCall=bs.Call(self._cb_submit_stats),
										   color=bColor,
										   autoSelect=True,
										   textColor=bTextColor,
										   buttonType='square',
										   textScale=0.7,
										   label="Do Swag")


		self.autoCheckUpdates = bs.checkBoxWidget(parent=self._rootWidget,position=(50 ,v-40),size=(250,50),color=(0.5,0.5,0.7),value=True,
															 autoSelect=True,onValueChangeCall=self._cb_update_checkbox,text="auto update",scale=0.8,textColor=(0.6,0.6,0.6,0.6))

		v = self._height - 75
		self._scrollHeight = self._height - 119
		scrollWidget = bs.scrollWidget(parent=self._rootWidget,position=(140,v-self._scrollHeight),size=(self._width-180,self._scrollHeight+10))
		bs.widget(edit=backButton,downWidget=scrollWidget,leftWidget=scrollWidget)
		c = self._columnWidget = bs.columnWidget(parent=scrollWidget)


		
		h = 145
		v = self._height - self._scrollHeight - 109


		
		self._doRandomizeVal = 0

		h += 210
		
		for b in [refreshButton,downloadButton,deleteButton,doSwagButton]:
			bs.widget(edit=b,rightWidget=scrollWidget)
		bs.widget(edit=scrollWidget,leftWidget=refreshButton)
		
		self._playlistWidgets = []

		self._cb_refresh()

		bs.buttonWidget(edit=backButton,onActivateCall=self._back)
		bs.containerWidget(edit=self._rootWidget,startButton=backButton,onCancelCall=backButton.activate)

		bs.containerWidget(edit=self._rootWidget,selectedChild=scrollWidget)

	def _back(self):

		bs.containerWidget(edit=self._rootWidget,transition='outRight')
		uiGlobals['mainMenuWindow'] = SettingsWindow(transition='inLeft').getRootWidget()



	def _refresh(self):


		while len(self._playlistWidgets) > 0: self._playlistWidgets.pop().delete()


		items = self.mods
		items.sort(key=lambda mod:mod.name.lower())
		index = 0
		for mod in items:
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
							  onActivateCall=bs.Call(self._cb_activate, mod),
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

	def _cb_activate(self, mod):
		bs.screenMessage('clicked on '+ mod.name)
		bs.screenMessage('checkUpdate() '+ str(mod.checkUpdate()))

	def _cb_refresh(self):
		#bs.screenMessage('Refreshing Modlist')
		self.mods = []
		request = None
		try:
			request = urllib2.urlopen(DATASERVER+"/getModList")
		except urllib2.HTTPError, e:
			bs.screenMessage('HTTPError = ' + str(e.code))
		except urllib2.URLError, e:
			bs.screenMessage('URLError = ' + str(e.reason))
		except httplib.HTTPException, e:
			bs.screenMessage('HTTPException')
		if request:
			#when we got network add the network mods
			networkData = eval(request.read()) # no json :(
			self.mods = [Mod(d) for d in networkData]

		modFilenames = [m.filename for m in self.mods]
		localfiles = os.listdir(bs.getEnvironment()['userScriptsDirectory'] + "/")
		for file in localfiles:
			if file.endswith(".py"):
				if file not in modFilenames:
					self.mods.append(LocalMod(file))

		for mod in self.mods:
			if mod.isInstalled():
				if mod.checkUpdate():
					bs.screenMessage('Update available for ' + mod.filename)
					UpdateModWindow(mod, self._cb_refresh)
		self._refresh()

	def _cb_download(self):
		UpdateModWindow(self._selectedMod, self._cb_refresh)

	def _cb_delete(self):
		DeleteModWindow(self._selectedMod, self._cb_refresh)

	def _cb_submit_stats(self):
		stats = bs.getEnvironment()
		stats['uniqueID'] = uniqueID
		# remove either private or long data
		del stats['userScriptsDirectory']
		del stats['systemScriptsDirectory']
		del stats['configFilePath']
		try:
			url = DATASERVER+"/submitStats?stats="+repr(stats)
			url = urllib2.quote(url, ":/?=") # fitting fake json in urls is wierd
			request = urllib2.urlopen(url)
		except urllib2.HTTPError, e:
			bs.screenMessage('HTTPError = ' + str(e.code))
		except urllib2.URLError, e:
			bs.screenMessage('URLError = ' + str(e.reason))
		except httplib.HTTPException, e:
			bs.screenMessage('HTTPException')

		bs.screenMessage('stats successfully submitted')






class UpdateModWindow(Window):

	def __init__(self, mod, onkay, swish=True, back=False):
		self._back = back
		self.mod = mod
		self.onkay = bs.WeakCall(onkay)
		if swish:
			bs.playSound(bs.getSound('swish'))
			
		self._rootWidget = ConfirmWindow("Do you want to update/change " + mod.filename + "?",
														self.kay).getRootWidget()
	def kay(self):
		self.mod.writeData(self.onkay)
		QuitToApplyWindow()

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
		text = "Quit BS to apply mod changes?" + "\n(On Android you have to kill the activity)" if bs.getEnvironment("platform")=="android" else ""
		self._rootWidget = quittoapply = ConfirmWindow(text,
														self._doFadeAndQuit).getRootWidget()

	def _doFadeAndQuit(self):
		bsInternal._fadeScreen(False,time=200,endCall=bs.Call(bs.quit,soft=True))
		bsInternal._lockAllInput()
		# unlock and fade back in shortly.. just in case something goes wrong
		# (or on android where quit just backs out of our activity and we may come back)
		bs.realTimer(300,bsInternal._unlockAllInput)
		#bs.realTimer(300,bs.Call(bsInternal._fadeScreen,True))





class Mod:
	name = "no name"
	author = "no author"
	filename = "no name"
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

		if self.isInstalled():
			path = bs.getEnvironment()['userScriptsDirectory'] + "/" + self.filename
			ownfile = open(path, "r")
			self.ownData = ownfile.read()
			ownfile.close()

	def getData(self):
		try:
			request = urllib2.urlopen(DATASERVER+"/getData?md5="+self.md5)
		except urllib2.HTTPError, e:
			bs.screenMessage('HTTPError = ' + str(e.code))
			return False
		except urllib2.URLError, e:
			bs.screenMessage('URLError = ' + str(e.reason))
			return False
		except httplib.HTTPException, e:
			bs.screenMessage('HTTPException')
			return False
		return request.read()

	def writeData(self, cb=None):
		path = bs.getEnvironment()['userScriptsDirectory'] + "/" + self.filename
		bs.screenMessage('writing to ' + path)
		
		data = self.getData()
		if data:
			f=open(path,'w')
			f.write(data)
			f.close()
		else:
			bs.screenMessage("Failed to write mod")
		if cb:
			cb()

	def delete(self, cb=None):
		path = bs.getEnvironment()['userScriptsDirectory'] + "/" + self.filename
		bs.screenMessage('removing ' + path)
		os.remove(path)
		if cb:
			cb()

	def checkUpdate(self):
		if not self.isInstalled(): return True
		if md5(self.ownData).hexdigest() != self.md5: return True
		return False

	def isInstalled(self):
		return os.path.exists(bs.getEnvironment()['userScriptsDirectory'] + "/" + self.filename)
		#return False

class LocalMod(Mod):
	def __init__(self, filename):
		self.filename = filename
		self.name = filename + " (Local Only)"

	def checkUpdate(self): return False

	def isInstalled(self): return True

	def getData(self): return False

	def writeData(self): bs.screenMessage("Can't update local-only mod!")


