
import bs
import bsUI
from bsUI import gSmallUI, gMedUI, gTitleColor, uiGlobals

try:
	from settings_patcher import SettingsButton
except ImportError:
	bs.screenMessage("settings_patcher missing", color=(1, 0, 0))
	raise
try:
	from ui_wrappers import *
except ImportError:
	bs.screenMessage("ui_wrappers missing", color=(1, 0, 0))
	raise

def _doConfigEditor(swinstance):
	swinstance._saveState()
	bs.containerWidget(edit=swinstance._rootWidget, transition='outLeft')
	uiGlobals['mainMenuWindow'] = ConfigEditorWindow(backLocationCls=swinstance.__class__, transition="inRight").getRootWidget()


settingsButton = SettingsButton(id="configEditor", text="Config Editor")
settingsButton.setCallback(_doConfigEditor)
settingsButton.add()

_supports_auto_reloading = True
_auto_reloader_type = "patching"
def _prepare_reload():
	settingsButton.remove()

bsGetAPIVersion = lambda: 3

max_width1 = 280
max_width2 = 70

class Input(object):
	def __init__(self, d):
		self.d = d
		self._default = d["_default"]
		self.nameWidget = None

	def refresh(self, containerWidget, pos, size):
		self.containerWidget = containerWidget
		self.pos = pos
		self.size = size

		self.rowWidget = r = RowWidget(parent=containerWidget, size=size)#
		r.set(claimsLeftRight=True, claimsTab=True, selectionLoopToParent=True)
		self.name()
		return r

	def name(self):
		self.nameWidget = TextWidget(parent=self.rowWidget, position=self.pos,
		                             size=self.size, text=self.d["_name"], hAlign="left",
		                             color=(0.8,0.8,0.8,1.0), vAlign="center",
		                             maxWidth=self.size[0])

	def delete(self):
		self.rowWidget.delete()
		self.nameWidget.delete()

	def write_data(self, val):
		self.d["_value"] = val
		bs.writeConfig()

class BooleanInput(Input):
	pass

class ListInput(Input):
	pass

class NumberInput(Input):
	pass

class TextInput(Input):
	pass

class ConfigEditorWindow(bsUI.Window):
	def __init__(self, backLocationCls, transition="inLeft"):
		self._backLocationCls = backLocationCls
		width = 620
		height = 365 if gSmallUI else 460 if gMedUI else 550
		spacing = 52
		self._rootWidget =  ContainerWidget(size=(width, height), transition=transition,
		                                    scale=2.19 if gSmallUI else 1.35 if gMedUI else 1.0,
		                                    stackOffset=(0, -17) if gSmallUI else (0, 0))

		self._back = ButtonWidget(parent=self._rootWidget,
		                          position=(45, height - 70),
		                          size=(180, 65),
		                          label=bs.getResource('backText'),
		                          buttonType='back',
		                          scale=0.75, textScale=1.3,
		                          onActivateCall=bs.Call(self._cancel))
		self._rootWidget.cancelButton = self._back

		self._title = TextWidget(parent=self._rootWidget, position=(-8, height-60), size=(width,25),
		                         text="Config-Editor",
		                         color=gTitleColor, maxWidth=235,
		                         scale=1.1, hAlign="center", vAlign="center")


		scrollWidth = width - 86
		self._scrollWidget = ScrollWidget(parent=self._rootWidget, position=(44, 35), size=(scrollWidth, height-120))
		self._subContainer = ContainerWidget(parent=self._scrollWidget, size=(scrollWidth, 0), background=False)

		# so selection loops through everything and doesn't get stuck in sub-containers
		self._scrollWidget.set(claimsLeftRight=True, claimsTab=True, selectionLoopToParent=True)
		self._subContainer.set(claimsLeftRight=True, claimsTab=True, selectionLoopToParent=True)


		self._settingWidgets = []
		self._refresh()

	def _cancel(self):
		self._rootWidget.doTransition("outRight")
		uiGlobals['mainMenuWindow'] = self._backLocationCls(transition='inLeft').getRootWidget()

	def settings(self, d=None):
		if not d:
			d = bs.getConfig()
		s = {}
		for key, value in d.items():
			if not isinstance(value, dict):
				continue
			if not "_default" in value:
				for key2, value2 in self.settings(value).items():
					if not key in s:
						s[key] = value.copy()
						s[key]["_container"] = True
					s[key][key2] = value2
				continue
			_default = value["_default"]
			if "_choices" in value:
				_type = ListInput
			elif isinstance(_default, bool):
				_type = BooleanInput
			elif isinstance(_default, int) or isinstance(_default, float):
				_type = NumberInput
			elif isinstance(_default, str) or isinstance(_default, unicode):
				_type = TextInput
			else:
				raise ValueError("invalid type " + str(value))
			s[key] = value.copy()
			s[key]["_type"] = _type
			if not "_name" in s[key]:
				s[key]["_name"] = key
		return s

	def _refresh(self):
		for w in self._settingWidgets:
			w.delete()
		x, y = (-50, -20)
		s = (self._scrollWidget.size[0], len(self.settings()))
		for key, settings in self.settings().items():
			name = settings.get("_name", key)
			print(settings)
			#bs.screenMessage(name)
			for elem in settings.values():
				if not isinstance(elem, dict) or "_type" not in elem:
					continue
				elem["_instance"] = elem["_type"](elem)
				rowWidget = elem["_instance"].refresh(self._subContainer, (max_width2, 30), (x, y))
				y -= rowWidget.size[1]
				self._settingWidgets.append(elem["_instance"])
				print(elem)

		return
		for settingName, setting in self._settingsDefs:

			mw1 = 280
			mw2 = 70

			# handle types with choices specially:
			if 'choices' in setting:

				for choice in setting['choices']:
					if len(choice) != 2: raise Exception("Expected 2-member tuples for 'choices'; got: "+repr(choice))
					if type(choice[0]) not in (str,unicode): raise Exception("First value for choice tuple must be a str; got: "+repr(choice))
					if type(choice[1]) is not valueType: raise Exception("Choice type does not match default value; choice:"+repr(choice)+"; setting:"+repr(setting))
				if valueType not in (int,float): raise Exception("Choice type setting must have int or float default; got: "+repr(setting))

				# start at the choice corresponding to the default if possible
				self._choiceSelections[settingName] = 0
				found = False
				for index,choice in enumerate(setting['choices']):
					if choice[1] == value:
						self._choiceSelections[settingName] = index
						break

				v -= spacing
				t = bs.textWidget(parent=self._subContainer,position=(h+50,v),size=(100,30),maxWidth=mw1,
								  text=nameTranslated,hAlign="left",color=(0.8,0.8,0.8,1.0),vAlign="center")
				t = bs.textWidget(parent=self._subContainer,position=(h+509-95,v),size=(0,28),
								  text=self._getLocalizedSettingName(setting['choices'][self._choiceSelections[settingName]][0]),editable=False,
								  color=(0.6,1.0,0.6,1.0),maxWidth=mw2,
								  hAlign="right",vAlign="center",padding=2)
				b1 = bs.buttonWidget(parent=self._subContainer,position=(h+509-50-1,v),size=(28,28),label="<",
									onActivateCall=bs.Call(self._choiceInc,settingName,t,setting,-1),repeat=True)
				b2 = bs.buttonWidget(parent=self._subContainer,position=(h+509+5,v),size=(28,28),label=">",
									onActivateCall=bs.Call(self._choiceInc,settingName,t,setting,1),repeat=True)
				widgetColumn.append([b1,b2])

			elif valueType in [int,float]:
				v -= spacing
				try: minValue = setting['minValue']
				except Exception: minValue = 0
				try: maxValue = setting['maxValue']
				except Exception: maxValue = 9999
				try: increment = setting['increment']
				except Exception: increment = 1
				t = bs.textWidget(parent=self._subContainer,position=(h+50,v),size=(100,30),
				                  text=nameTranslated,hAlign="left",color=(0.8,0.8,0.8,1.0),vAlign="center",maxWidth=mw1)
				t = bs.textWidget(parent=self._subContainer,position=(h+509-95,v),size=(0,28),
				                  text=str(value),editable=False,
				                  color=(0.6,1.0,0.6,1.0),maxWidth=mw2,
				                  hAlign="right",vAlign="center",padding=2)
				b1 = bs.buttonWidget(parent=self._subContainer,position=(h+509-50-1,v),size=(28,28),label="-",
				                     onActivateCall=bs.Call(self._inc,t,minValue,maxValue,-increment,valueType,settingName),repeat=True)
				b2 = bs.buttonWidget(parent=self._subContainer,position=(h+509+5,v),size=(28,28),label="+",
				                     onActivateCall=bs.Call(self._inc,t,minValue,maxValue,increment,valueType,settingName),repeat=True)
				widgetColumn.append([b1,b2])

			elif valueType == bool:
				v -= spacing
				t = bs.textWidget(parent=self._subContainer,position=(h+50,v),size=(100,30),
				                  text=nameTranslated,hAlign="left",color=(0.8,0.8,0.8,1.0),vAlign="center",maxWidth=mw1)
				t = bs.textWidget(parent=self._subContainer,position=(h+509-95,v),size=(0,28),
				                  text=bs.getResource('onText') if value else bs.getResource('offText'),editable=False,
				                  color=(0.6,1.0,0.6,1.0),maxWidth=mw2,
				                  hAlign="right",vAlign="center",padding=2)
				c = bs.checkBoxWidget(parent=self._subContainer,text='',position=(h+505-50-5,v-2),size=(200,30),
				                      textColor=(0.8,0.8,0.8),
				                      value=value,onValueChangeCall=bs.Call(self._checkValueChange,settingName,t))
				widgetColumn.append([c])

			else: raise Exception()
