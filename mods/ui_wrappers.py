import bs

DEBUG = False


class Widget(bs.Widget):
    _instance = None
    _values = dict(upWidget=None, downWidget=None, leftWidget=None, rightWidget=None,
                   showBufferTop=None, showBufferBottom=None, showBufferLeft=None,
                   showBufferRight=None, autoSelect=None)
    _required = []
    _func = bs.widget
    _can_create = False
    _values_funcs = {}

    def __init__(self, **kwargs):
        if not self._can_create:
            raise Exception("cant create widget of type " + str(self.__class__))
        for key in self._required:
            if key not in kwargs:
                raise ValueError("expected " + key)
        self._instance = self._call_func(self._func, kwargs)
        self._values_funcs = {}
        self._values = {}
        for cls in [self.__class__] + list(self.__class__.__bases__):
            self._values_funcs[cls._func] = cls._values
            self._values.update(cls._values)
        self._values.update(kwargs)

    def _call_func(self, func, kwargs):
        d = {}
        for key, value in kwargs.items():
            d[key] = value
            if isinstance(value, Widget):
                d[key] = value._instance
        if DEBUG:
            print("bs.{}(**{})".format(func.__name__, d))
        return func(**d)

    def set(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def reset_value(self, key):
        setattr(self, key, self.__class__._values[key])

    def activate(self, *args, **kwargs):
        return self._instance.activate(*args, **kwargs)

    def delete(self, *args, **kwargs):
        return self._instance.delete(*args, **kwargs)

    def exists(self, *args, **kwargs):
        return self._instance.exists(*args, **kwargs)

    def getChildren(self, *args, **kwargs):
        return self._instance.getChildren(*args, **kwargs)

    def getScreenSpaceCenter(self, *args, **kwargs):
        return self._instance.getScreenSpaceCenter(*args, **kwargs)

    def getSelectedChild(self, *args, **kwargs):
        return self._instance.getSelectedChild(*args, **kwargs)

    def getWidgetType(self, *args, **kwargs):
        return self._instance.getWidgetType(*args, **kwargs)

    def __getattr__(self, key):
        if hasattr(self._instance, key):
            return getattr(self._instance, key)
        if key in self._values:
            return self._values[key]
        raise AttributeError("type object '{}' has no attribute '{}'".format(type(self), key))

    def __setattr__(self, key, value):
        if DEBUG:
            print("__setattr__({}, {})".format(repr(key), value))
        for func, values in self._values_funcs.items():
            if key in values:
                self._call_func(func, {"edit": self._instance, key: value})
                self._values[key] = value
                return
        self.__dict__[key] = value

    def __repr__(self):
        return object.__repr__(self)

    def __str__(self):
        return object.__str__(self)


class TextWidget(Widget):
    _values = dict(parent=None, size=None, position=None, vAlign=None, hAlign=None, editable=False,
                   padding=None, onReturnPressCall=None, selectable=None, onActivateCall=None,
                   query=None, maxChars=None, color=None, clickActivate=None, scale=None,
                   alwaysHighlight=None, drawController=None, description=None, transitionDelay=None,
                   flatness=None, enabled=None, forceInternalEditing=False, alwaysShowCarat=None,
                   maxWidth=None, maxHeight=None, big=False)  # FIXME: check default values
    _required = ["parent"]
    _func = bs.textWidget
    _can_create = True

    # FIXME: textWidget.set(text=...) shadows instance method
    def text(self):
        return self._func(query=self._instance)


class ButtonWidget(Widget):
    _values = dict(parent=None, size=None, position=None, onActivateCall=None, label=None,
                   color=None, texture=None, textScale=None, enableSound=True, modelTransparent=None,
                   modelOpaque=None, transitionDelay=None, onSelectCall=None, extraTouchBorderScale=None,
                   buttonType=None, touchOnly=None, showBufferTop=None, icon=None, iconScale=None,
                   iconTint=None, iconColor=None, autoSelect=None, repeat=None, maskTexture=None,
                   tintTexture=None, tintColor=None)  # FIXME: check default values
    _required = ["parent", "position", "size"]
    _func = bs.buttonWidget
    _can_create = True
    COLOR_GREY = (0.52, 0.48, 0.63)
    TEXTCOLOR_GREY = (0.65, 0.6, 0.7)


class CheckBoxWidget(Widget):
    _values = dict(parent=None, size=None, position=None, value=None, clickSelect=None,
                   onActivateCall=None, onValueChangeCall=None, onSelectCall=None,
                   isRadioButton=False, scale=None, maxWidth=None, autoSelect=None, color=None)  # FIXME: check default values
    _required = ["parent", "position"]
    _func = bs.checkBoxWidget
    _can_create = True

    def __init__(self, **kwargs):
        super(self.__class__, self).__init__(**kwargs)
        if not self.onValueChangeCall:
            def f(val):
                print(val)
                self._values["value"] = val
            self._func(edit=self._instance, onValueChangeCall=f)

    def _call_func(self, func, kwargs):
        d = {}
        for key, value in kwargs.items():
            d[key] = value
            if isinstance(value, Widget):
                d[key] = value._instance
            if key == "onValueChangeCall":
                def w(value):
                    def f(val):
                        self._values["value"] = val
                        value(val)
                    return f
                d[key] = w(value)
        return func(**d)


class ContainerWidget(Widget):
    _values = dict(parent=None, size=None, position=None, selectedChild=None, transition=None,
                   cancelButton=None, startButton=None, rootSelectable=None, onActivateCall=None,
                   claimsLeftRight=None, claimsTab=None, selectionLoops=None, selectionLoopToParent=None,
                   scale=None, type=None, onOutsideClickCall=None, singleDepth=None, visibleChild=None,
                   stackOffset=None, color=None, onCancelCall=None, printListExitInstructions=None,
                   clickActivate=None, alwaysHighlight=None, selectable=None, scaleOriginStackOffset=None)  # FIXME: check default values
    _required = ["size"]
    _func = bs.containerWidget
    _can_create = True

    def doTransition(self, transition):
        self.set(transition=transition)


class ScrollWidget(Widget):
    _values = dict(parent=None, size=None, position=None, captureArrows=False, onSelectCall=None,
                   centerSmallContent=None, color=None, highlight=None, borderOpacity=None)  # FIXME: check default values
    _required = ["parent", "position", "size"]
    _func = bs.scrollWidget
    _can_create = True


class ColumnWidget(Widget):
    _values = dict(parent=None, size=None, position=None, singleDepth=None,
                   printListExitInstructions=None, leftBorder=None,
                   selectedChild=None, visibleChild=None)  # FIXME: check default values
    _required = ["parent"]
    _func = bs.columnWidget
    _can_create = True


class HScrollWidget(Widget):
    _values = dict(parent=None, size=None, position=None, captureArrows=False, onSelectCall=None,
                   centerSmallContent=None, color=None, highlight=None, borderOpacity=None)  # FIXME: check default values
    _required = ["parent", "position", "size"]
    _func = bs.hScrollWidget
    _can_create = True


class ImageWidget(Widget):
    _values = dict(parent=None, size=None, position=None, color=None, texture=None,
                   model=None, modelTransparent=None, modelOpaque=None, hasAlphaChannel=True,
                   tintTexture=None, tintColor=None, transitionDelay=None, drawController=None,
                   tiltScale=None, maskTexture=None)  # FIXME: check default values
    _required = ["parent", "size", "position"]
    _func = bs.imageWidget
    _can_create = True


class RowWidget(Widget):
    _values = dict(parent=None, size=None, position=None, selectable=False)
    _required = ["parent", "size", "position"]
    _func = bs.rowWidget
    _can_create = True
