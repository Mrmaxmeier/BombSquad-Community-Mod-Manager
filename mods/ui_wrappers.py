import bs

#- [x] bs.buttonWidget()
#- [x] bs.checkBoxWidget()
#- [ ] bs.columnWidget()
#- [x] bs.containerWidget()
#- [ ] bs.hScrollWidget()
#- [ ] bs.imageWidget()
#- [ ] bs.rowWidget()
#- [ ] bs.scrollWidget()
#- [x] bs.textWidget()
#- [x] bs.widget()

class Widget(bs.Widget):
	_instance = None
	_values = dict(upWidget=None, downWidget=None, leftWidget=None, rightWidget=None, showBufferTop=None, showBufferBottom=None, showBufferLeft=None, showBufferRight=None, autoSelect=None)
	_required = []
	_func = None
	_can_create = False
	_values_funcs = {}

	def __init__(self, **kwargs):
		if not self._can_create:
			raise Exception("cant create widget of type " + str(self.__class__))
		for key in self._required:
			if not key in kwargs:
				raise ValueError("expected " + key)
		self._instance = self._call_func(self._func, kwargs)
		self._values_funcs = {}
		self._values = {}
		for cls in [self.__class__] + list(self.__class__.__bases__):
			if cls == Widget:
				continue
			self._values_funcs[cls._func] = cls._values
			self._values.update(cls._values)

	def _call_func(self, func, kwargs):
		d = {}
		for key, value in kwargs.items():
			d[key] = value
			if isinstance(value, Widget):
				d[key] = value._instance
		return func(**d)

	def set(self, **kwargs):
		for key, value in kwargs.items():
			setattr(self, key, value)

	def __getattr__(self, key):
		if hasattr(self._instance, key):
			return getattr(self._instance, key)
		if key in self._values:
			return self._vaules[key]
		raise AttributeError("type object '" + str(type(self)) + "' has no attribute '" + key + "'")

	def __setattr__(self, key, value):
		for func, values in self._values_funcs.items():
			if key in values:
				self._call_func(func, {"edit": self._instance, key: value})
				self._values[key] = value
				return
		self.__dict__[key] = value

class TextWidget(Widget):
	_values = dict(parent=None, size=None, position=None, vAlign=None, hAlign=None, editable=False,
				   padding=None, onReturnPressCall=None, selectable=None, onActivateCall=None,
				   query=None, maxChars=None, color=None, clickActivate=None, scale=None,
				   alwaysHighlight=None, drawController=None, description=None, transitionDelay=None,
				   flatness=None, enabled=None, forceInternalEditing=False, alwaysShowCarat=None,
				   maxWidth=None, maxHeight=None, big=False) # FIXME: check default values
	_required = ["parent", "position", "size"]
	_func = bs.textWidget
	_can_create = True

	def text(self):
		return self._func(query=self._instance)

class ButtonWidget(Widget):
	_values = dict(parent=None, size=None, position=None, onActivateCall=None, label=None,
				   color=None, texture=None, textScale=None, enableSound=True, modelTransparent=None,
				   modelOpaque=None, transitionDelay=None, onSelectCall=None, extraTouchBorderScale=None,
				   buttonType=None, touchOnly=None, showBufferTop=None, icon=None, iconScale=None,
				   iconTint=None, iconColor=None, autoSelect=None, repeat=None, maskTexture=None,
				   tintTexture=None, tintColor=None) # FIXME: check default values
	_required = ["parent", "position", "size"]
	_func = bs.buttonWidget
	_can_create = True

class CheckBoxWidget(Widget):
	_values = dict(parent=None, size=None, position=None, value=None, clickSelect=None,
				   onActivateCall=None, onValueChangeCall=None, onSelectCall=None,
				   isRadioButton=False, scale=None, maxWidth=None, autoSelect=None, color=None) # FIXME: check default values
	_required = ["parent", "position"]
	_func = bs.checkBoxWidget
	_can_create = True

class ContainerWidget(Widget):
	_values = dict(parent=None, size=None, position=None, selectedChild=None, transition=None,
				   cancelButton=None, startButton=None, rootSelectable=None, onActivateCall=None,
				   claimsLeftRight=None, claimsTab=None, selectionLoops=None, selectionLoopToParent=None,
				   scale=None, type=None, onOutsideClickCall=None, singleDepth=None, visibleChild=None,
				   stackOffset=None, color=None, onCancelCall=None, printListExitInstructions=None,
				   clickActivate=None, alwaysHighlight=None, selectable=None, scaleOriginStackOffset=None) # FIXME: check default values
	_required = ["size"]
	_func = bs.containerWidget
	_can_create = True

	def doTransition(self, transition):
		self.transition = transition

class ScrollWidget(Widget):
	_values = dict(parent=None, size=None, position=None, captureArrows=False, onSelectCall=None,
				   centerSmallContent=None, color=None, highlight=None, borderOpacity=None) # FIXME: check default values
	_required = ["parent", "position", "size"]
	_func = bs.scrollWidget
	_can_create = True
