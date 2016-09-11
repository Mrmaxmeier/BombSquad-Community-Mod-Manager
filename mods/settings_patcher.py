import bs
from bsUI import SettingsWindow, gSmallUI, gMedUI, gTitleColor, gDoAndroidNav, gWindowStates

try:
    from ui_wrappers import TextWidget, ButtonWidget, ImageWidget
except ImportError:
    bs.screenMessage("ui_wrappers missing", color=(1, 0, 0))
    raise


class SettingsButton:
    def __init__(self, id, text=None, icon=None, iconColor=None, sorting_position=None):
        self.id = id
        self.text = text
        self.icon = icon
        self.iconColor = iconColor
        self.sorting_position = sorting_position
        self.textOnly = icon is None
        self._cb = lambda x: None
        self._buttonInstance = None
        self.instanceLocals = {}

    def setText(self, text):
        self.text = text
        return self

    def setCallback(self, cb):
        self._cb = cb
        return self

    def add(self):
        buttons.append(self)
        return self

    def remove(self):
        buttons.remove(self)
        return self

    def setLocals(self, swinstance=None, **kwargs):
        self.instanceLocals.update(kwargs)
        if swinstance:
            if "button" in self.instanceLocals:
                setattr(swinstance, self.instanceLocals["button"], self._buttonInstance)
        return self

    def x(self, swinstance, index, bw, wmodsmallui=0.4, wmod=0.2):
        if self.icon:
            layout = iconbuttonlayouts[sum([b.icon is not None for b in buttons])]
        else:
            layout = textbuttonlayouts[sum([b.textOnly for b in buttons])]
        bw += wmodsmallui if gSmallUI else wmod
        for i in range(len(layout) + 1):
            if sum(layout[:i]) > index:
                row = i - 1
                pos = index - sum(layout[:i - 1])
                return swinstance._width / 2 + bw * (pos - layout[row] / 2.0) * (1.0 if self.icon else 1.05)

    def _create_icon_button(self, swinstance, index):
        width, height = swinstance._width, swinstance._gOnlyHeight
        layout = iconbuttonlayouts[sum([b.icon is not None for b in buttons])]
        bw = width / (max(layout) + (0.4 if gSmallUI else 0.2))
        bwx = bw
        bh = height / (len(layout) + (0.5 if gSmallUI else 0.4))
        # try to keep it squared
        if abs(1 - bw / bh) > 0.1:
            bwx *= (bh / bw - 1) / 2 + 1
            bw = bh = min(bw, bh)

        for i in range(len(layout) + 1):
            if sum(layout[:i]) > index:
                row = i - 1
                break

        x = self.x(swinstance, index, bwx)
        y = swinstance._height - 95 - (row + 0.8) * (bh - 10)

        button = ButtonWidget(parent=swinstance._rootWidget, autoSelect=True,
                              position=(x, y), size=(bwx, bh), buttonType='square',
                              label='')
        button.onActivateCall = lambda: self._cb(swinstance)

        x += (bwx - bw) / 2
        TextWidget(parent=swinstance._rootWidget, text=self.text,
                   position=(x + bw * 0.47, y + bh * 0.22),
                   maxWidth=bw * 0.7, size=(0, 0), hAlign='center', vAlign='center',
                   drawController=button,
                   color=(0.7, 0.9, 0.7, 1.0))

        iw, ih = bw * 0.65, bh * 0.65
        i = ImageWidget(parent=swinstance._rootWidget, position=(x + bw * 0.49 - iw * 0.5, y + 43),
                        size=(iw, ih), texture=bs.getTexture(self.icon),
                        drawController=button)
        if self.iconColor:
            i.color = self.iconColor
        self._buttonInstance = button._instance
        return x, y

    def _create_text_button(self, swinstance, index, start_y):
        width, height = swinstance._width, swinstance._height - swinstance._gOnlyHeight
        layout = textbuttonlayouts[sum([b.textOnly for b in buttons])]
        bw = width / (max(layout) + (0.7 if gSmallUI else 0.4))
        bh = height / len(layout)

        for i in range(len(layout) + 1):
            if sum(layout[:i]) > index:
                row = i - 1
                break

        x = self.x(swinstance, index, bw, 0.7, 0.4)
        y = start_y - (row + 1) * bh

        button = ButtonWidget(parent=swinstance._rootWidget, autoSelect=True,
                              position=(x, y), size=(bw, bh),
                              label=self.text, color=ButtonWidget.COLOR_GREY,
                              textColor=ButtonWidget.TEXTCOLOR_GREY)
        button.onActivateCall = lambda: self._cb(swinstance)

        self._buttonInstance = button._instance
        return x, y


buttons = []
iconbuttonlayouts = {
    0: [],
    1: [1],
    2: [2],
    3: [2, 1],
    4: [2, 2],
    5: [3, 2],
    6: [3, 3],
    7: [4, 3],
    8: [3, 3, 2],
    9: [3, 3, 3]
}
textbuttonlayouts = {
    1: [1],
    2: [2],
    3: [3],
    4: [2, 2],
    5: [3, 2],
    6: [3, 3],
    7: [4, 3]
}

if hasattr(SettingsWindow, "_doProfiles"):
    SettingsButton(id="Profiles", icon="cuteSpaz") \
        .setCallback(lambda swinstance: swinstance._doProfiles()) \
        .setText(bs.Lstr(resource='settingsWindow.playerProfilesText')) \
        .add()

if hasattr(SettingsWindow, "_doControllers"):
    SettingsButton(id="Controllers", icon="controllerIcon") \
        .setCallback(lambda swinstance: swinstance._doControllers()) \
        .setText(bs.Lstr(resource='settingsWindow.controllersText')) \
        .setLocals(button="_controllersButton") \
        .add()

if hasattr(SettingsWindow, "_doGraphics"):
    SettingsButton(id="Graphics", icon="graphicsIcon") \
        .setCallback(lambda swinstance: swinstance._doGraphics()) \
        .setText(bs.Lstr(resource='settingsWindow.graphicsText')) \
        .setLocals(button="_graphicsButton") \
        .add()

if hasattr(SettingsWindow, "_doAudio"):
    SettingsButton(id="Audio", icon="audioIcon", iconColor=(1, 1, 0)) \
        .setCallback(lambda swinstance: swinstance._doAudio()) \
        .setText(bs.Lstr(resource='settingsWindow.audioText')) \
        .setLocals(button="_audioButton") \
        .add()

if hasattr(SettingsWindow, "_doAdvanced"):
    SettingsButton(id="Advanced", icon="advancedIcon", iconColor=(0.8, 0.95, 1)) \
        .setCallback(lambda swinstance: swinstance._doAdvanced()) \
        .setText(bs.Lstr(resource='settingsWindow.advancedText')) \
        .setLocals(button="_advancedButton") \
        .add()

for i, button in enumerate(buttons):
    button.sorting_position = i


def newInit(self, transition='inRight', originWidget=None):
    if originWidget is not None:
        self._transitionOut = 'outScale'
        scaleOrigin = originWidget.getScreenSpaceCenter()
        transition = 'inScale'
    else:
        self._transitionOut = 'outRight'
        scaleOrigin = None

    width = 600 if gSmallUI else 600
    height = 360 if gSmallUI else 435
    self._gOnlyHeight = height
    if any([b.textOnly for b in buttons]):
        if len(textbuttonlayouts[sum([b.textOnly for b in buttons])]) > 1:
            height += 80 if gSmallUI else 120
        else:
            height += 60 if gSmallUI else 80
    self._width, self._height = width, height

    R = bs.Lstr(resource='settingsWindow')

    topExtra = 20 if gSmallUI else 0
    if originWidget is not None:
        self._rootWidget = bs.containerWidget(size=(width, height+topExtra), transition=transition,
                                              scaleOriginStackOffset=scaleOrigin,
                                              scale=1.75 if gSmallUI else 1.35 if gMedUI else 1.0,
                                              stackOffset=(0, -8) if gSmallUI else (0, 0))
    else:
        self._rootWidget = bs.containerWidget(size=(width, height+topExtra), transition=transition,
                                              scale=1.75 if gSmallUI else 1.35 if gMedUI else 1.0,
                                              stackOffset=(0, -8) if gSmallUI else (0, 0))

    self._backButton = b = bs.buttonWidget(parent=self._rootWidget, autoSelect=True, position=(40, height-55),
                                           size=(130, 60), scale=0.8, textScale=1.2, label=bs.Lstr(resource='backText'),
                                           buttonType='back', onActivateCall=self._doBack)
    bs.containerWidget(edit=self._rootWidget, cancelButton=b)

    t = bs.textWidget(parent=self._rootWidget, position=(0, height-44), size=(width, 25),
                      text=bs.Lstr(resource='settingsWindow.titleText'), color=gTitleColor,
                      hAlign="center", vAlign="center", maxWidth=130)

    if gDoAndroidNav:
        bs.buttonWidget(edit=b, buttonType='backSmall', size=(60, 60), label=bs.getSpecialChar('logoFlat'))
        bs.textWidget(edit=t, hAlign='left', position=(93, height-44))

    icon_buttons = sorted([b for b in buttons if b.icon], key=lambda b: b.sorting_position)
    for i, button in enumerate(icon_buttons):
        x, y = button._create_icon_button(self, i)
    text_buttons = sorted([b for b in buttons if b.textOnly], key=lambda b: b.sorting_position)
    for i, button in enumerate(text_buttons):
        button._create_text_button(self, i, y)

    for button in buttons:
        button.setLocals(self)

    self._restoreState()

SettingsWindow.__init__ = newInit


def statedict(self):
    d = {button._buttonInstance: button.id for button in buttons}
    d.update({self._backButton: "Back"})
    return d


def _saveState(self):
    w = self._rootWidget.getSelectedChild()
    for k, v in statedict(self).items():
        if w == k:
            gWindowStates[self.__class__.__name__] = {'selName': v}
            return
    bs.printError('error saving state for ' + str(self.__class__))
SettingsWindow._saveState = _saveState


def _restoreState(self):
    sel = None
    if self.__class__.__name__ in gWindowStates and 'selName' in gWindowStates[self.__class__.__name__]:
        selName = gWindowStates[self.__class__.__name__]['selName']
        for k, v in statedict(self).items():
            if selName == v:
                sel = k
    sel = sel or buttons[0]._buttonInstance
    bs.containerWidget(edit=self._rootWidget, selectedChild=sel)
SettingsWindow._restoreState = _restoreState
