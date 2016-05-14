from __future__ import print_function
import bs
import bsInternal
import os
import urllib
import urllib2
import json
import random
import time
import threading
import weakref
from md5 import md5
from bsUI import gSmallUI, gMedUI, gHeadingColor, uiGlobals, ConfirmWindow, StoreWindow, MainMenuWindow, Window
from functools import partial

try:
    from settings_patcher import SettingsButton
except ImportError:
    bs.screenMessage("library settings_patcher missing", color=(1, 0, 0))
    raise
try:
    from ui_wrappers import TextWidget, ContainerWidget, ButtonWidget, CheckBoxWidget, ScrollWidget, ColumnWidget, Widget
except ImportError:
    bs.screenMessage("library ui_wrappers missing", color=(1, 0, 0))
    raise


# roll own uuid4 implementation because uuid module might not be available
def uuid4():
    components = [8, 4, 4, 4, 12]
    return "-".join([('%012x' % random.randrange(16**a))[12-a:] for a in components])

PROTOCOL_VERSION = 1.0
SUPPORTS_HTTPS = False
STAT_SERVER_URI = "http://bsmm.thuermchen.com"

_supports_auto_reloading = True
_auto_reloader_type = "patching"
StoreWindow_setTab = StoreWindow._setTab
MainMenuWindow__init__ = MainMenuWindow.__init__


def _prepare_reload():
    settingsButton.remove()
    MainMenuWindow.__init__ = MainMenuWindow__init__
    del MainMenuWindow._cb_checkUpdateData
    StoreWindow._setTab = StoreWindow_setTab
    del StoreWindow._onGetMoreGamesPress


def bsGetAPIVersion():
    return 3

quittoapply = None
checkedMainMenu = False


if 'mod_manager_config' not in bs.getConfig():
    bs.getConfig()['mod_manager_config'] = {}
    bs.writeConfig()

config = bs.getConfig()['mod_manager_config']


def index_file(branch=None):
    if branch:
        return "https://rawgit.com/Mrmaxmeier/BombSquad-Community-Mod-Manager/" + branch + "/index.json"
    return "https://rawgit.com/Mrmaxmeier/BombSquad-Community-Mod-Manager/" + config.get("branch", "master") + "/index.json"

web_cache = config.get("web_cache", {})
config["web_cache"] = web_cache

if 'uuid' not in config:
    config['uuid'] = uuid4()
    bs.writeConfig()


def get_cached(url, callback, force_fresh=False, fallback_to_outdated=True):
    def cache(data, status_code):
        if data:
            web_cache[url] = (data, time.time())
            bs.writeConfig()

    def f(data, status_code):
        # TODO: cancel prev fetchs
        callback(data, status_code)
        cache(data, status_code)

    if force_fresh:
        mm_serverGet(url, {}, f)
        return

    if url in web_cache:
        data, timestamp = web_cache[url]
        if timestamp + 10 * 30 > time.time():
            mm_serverGet(url, {}, cache)
        if fallback_to_outdated or timestamp + 10 * 60 > time.time():
            callback(data, None)
            return

    mm_serverGet(url, {}, f)


def get_index(callback, branch=None, **kwargs):
    url = index_file(branch)
    get_cached(url, callback, **kwargs)


def fetch_ratings(callback, **kwargs):
    url = STAT_SERVER_URI + "/ratings?uuid=" + config['uuid']
    get_cached(url, callback, **kwargs)


def stats_cached():
    url = STAT_SERVER_URI + "/ratings?uuid=" + config['uuid']
    return url in web_cache


def submit_mod_rating(mod, rating, callback):
    url = STAT_SERVER_URI + "/submit"
    data = {
        "uuid": config['uuid'],
        "mod_str": mod.base,
        "rating": rating,
    }

    def cb(data, status_code):
        if status_code == 200:
            bs.screenMessage("rating submitted")
            callback()
        else:
            bs.screenMessage("failed to submit rating")

    mm_serverPost(url, data, cb, eval_data=False)


def process_server_data(data):
    mods = data["mods"]
    version = data["version"]
    if version - 0.5 > PROTOCOL_VERSION:
        print("version diff:", version, PROTOCOL_VERSION)
        bs.screenMessage("please update the mod manager")
    return mods, version


def _cb_checkUpdateData(self, data, status_code):
    try:
        if data:
            m, v = process_server_data(data)
            mods = [Mod(d) for d in m.values()]
            for mod in mods:
                mod._mods = {m.base: m for m in mods}
                if mod.isInstalled() and mod.checkUpdate():
                    if config.get("auto-update-old-mods", True):
                        if mod.is_outdated():
                            bs.screenMessage("updating '" + str(mod.name) + "'")

                            def cb(mod, success):
                                if success:
                                    bs.screenMessage("'" + str(mod.name) + "' updated")

                            mod.install(cb)
                    else:
                        if not mod.is_outdated():
                            bs.screenMessage("Update for '" + mod.name + "' available! Check the ModManager")
    except:
        bs.printException()
        bs.screenMessage("failed to check for updates")


oldMainInit = MainMenuWindow.__init__


def newMainInit(self, transition='inRight'):
    global checkedMainMenu
    oldMainInit(self, transition)
    if checkedMainMenu:
        return
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

settingsButton = SettingsButton(id="ModManager", icon="heart", sorting_position=6) \
    .setCallback(_doModManager) \
    .setText("Mod Manager") \
    .add()


class MM_ServerCallThread(threading.Thread):

    def __init__(self, request, requestType, data, callback, eval_data=True):
        threading.Thread.__init__(self)
        self._request = request.encode("ascii")  # embedded python2.7 has weird encoding issues
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

    def _runCallback(self, *args):

        # if we were created in an activity context and that activity has since died, do nothing
        # (hmm should we be using a context-call instead of doing this manually?)
        if self._activity is not None and (self._activity() is None or self._activity().isFinalized()):
            return

        # (technically we could do the same check for session contexts, but not gonna worry about it for now)
        with self._context:
            self._callback(*args)

    def run(self):
        try:
            bsInternal._setThreadName("MM_ServerCallThread")  # FIXME: using protected apis
            env = {'User-Agent': bs.getEnvironment()['userAgentString']}
            if self._requestType != "get" or self._data:
                if self._requestType == 'get':
                    if self._data:
                        request = urllib2.Request(self._request+'?'+urllib.urlencode(self._data), None, env)
                    else:
                        request = urllib2.Request(self._request, None, env)
                elif self._requestType == 'post':
                    request = urllib2.Request(self._request, json.dumps(self._data), env)
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
                bs.callInGameThread(bs.Call(self._runCallback, responseData, response.getcode()))

        except:
            if self._callback is not None:
                bs.callInGameThread(bs.Call(self._runCallback, None, None))


def mm_serverGet(request, data, callback=None, eval_data=True):
    MM_ServerCallThread(request, 'get', data, callback, eval_data=eval_data).start()


def mm_serverPost(request, data, callback=None, eval_data=True):
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
            transition = 'inScale'
        else:
            self._transitionOut = 'outRight'

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

        def sort_rating(mods):
            return sorted(mods, key=lambda mod: mod.rating, reverse=True)

        def sort_alphabetical(mods):
            return sorted(mods, key=lambda mod: mod.name.lower())

        _sortModes = [
            ('Rating', sort_rating, lambda m: stats_cached()),
            ('Downloads', sort_alphabetical, lambda m: stats_cached()),
            ('Alphabetical', sort_alphabetical),
        ]

        self.sortModes = {}
        for i, sortMode in enumerate(_sortModes):
            name, func = sortMode[:2]
            next_sortMode = _sortModes[(i+1) % len(_sortModes)]
            condition = sortMode[2] if len(sortMode) > 2 else (lambda mods: True)
            self.sortModes[name] = {
                'func': func,
                'condition': condition,
                'next': next_sortMode[0],
                'name': name,
                'index': i,
            }

        sortMode = config.get('sortMode')
        if not sortMode or sortMode not in self.sortModes:
            sortMode = _sortModes[0][0]
        self.sortMode = self.sortModes[sortMode]

        self._width = 650
        self._height = 380 if gSmallUI else 420 if gMedUI else 500
        topExtra = 20 if gSmallUI else 0

        self._rootWidget = ContainerWidget(size=(self._width, self._height+topExtra), transition=transition,
                                           scale=2.05 if gSmallUI else 1.5 if gMedUI else 1.0,
                                           stackOffset=(0, -10) if gSmallUI else (0, 0))

        self._backButton = backButton = ButtonWidget(parent=self._rootWidget, position=(self._width-160, self._height-60),
                                                     size=(160, 68), scale=0.77,
                                                     autoSelect=True, textScale=1.3,
                                                     label=bs.getResource('doneText' if self._modal else 'backText'),
                                                     onActivateCall=self._back)
        self._rootWidget.cancelButton = backButton
        TextWidget(parent=self._rootWidget, position=(0, self._height-47),
                   size=(self._width, 25),
                   text=self._windowTitleName, color=gHeadingColor,
                   maxWidth=290,
                   hAlign="center", vAlign="center")

        v = self._height - 59
        h = 41
        bColor = (0.6, 0.53, 0.63)
        bTextColor = (0.75, 0.7, 0.8)

        s = 1.1 if gSmallUI else 1.27 if gMedUI else 1.57
        v -= 63.0*s
        self.refreshButton = ButtonWidget(parent=self._rootWidget,
                                          position=(h, v),
                                          size=(90, 58.0*s),
                                          onActivateCall=bs.Call(self._cb_refresh, force_fresh=True),
                                          color=bColor,
                                          autoSelect=True,
                                          buttonType='square',
                                          textColor=bTextColor,
                                          textScale=0.7,
                                          label="Reload List")

        v -= 63.0*s
        self.modInfoButton = ButtonWidget(parent=self._rootWidget, position=(h, v), size=(90, 58.0*s),
                                          onActivateCall=bs.Call(self._cb_info),
                                          color=bColor,
                                          autoSelect=True,
                                          textColor=bTextColor,
                                          buttonType='square',
                                          textScale=0.7,
                                          label="Mod Info")

        v -= 63.0*s
        self.sortButtonData = {"s": s, "h": h, "v": v, "bColor": bColor, "bTextColor": bTextColor}
        self.sortButton = ButtonWidget(parent=self._rootWidget, position=(h, v), size=(90, 58.0*s),
                                       onActivateCall=bs.Call(self._cb_sorting),
                                       color=bColor,
                                       autoSelect=True,
                                       textColor=bTextColor,
                                       buttonType='square',
                                       textScale=0.7,
                                       label="Sorting:\n" + self.sortMode['name'])

        v -= 63.0*s
        self.settingsButton = ButtonWidget(parent=self._rootWidget, position=(h, v), size=(90, 58.0*s),
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
        scrollWidget = ScrollWidget(parent=self._rootWidget, position=(140, self.columnPosY - self._scrollHeight),
                                    size=(self._width-180, self._scrollHeight+10))
        backButton.set(downWidget=scrollWidget, leftWidget=scrollWidget)
        self._columnWidget = ColumnWidget(parent=scrollWidget)

        for b in [self.refreshButton, self.modInfoButton, self.settingsButton]:
            # bs.widget(edit=b, rightWidget=scrollWidget)
            b.rightWidget = scrollWidget
        scrollWidget.leftWidget = self.refreshButton

        self._cb_refresh()

        backButton.onActivateCall = self._back
        self._rootWidget.startButton = backButton
        self._rootWidget.onCancelCall = backButton.activate
        self._rootWidget.selectedChild = scrollWidget

    def _refresh(self, refreshTabs=True):
        while len(self._modWidgets) > 0:
            self._modWidgets.pop().delete()

        for mod in self.mods:
            if mod.category:
                self.categories.add(mod.category)
        if refreshTabs:
            self._refreshTabs()

        while not self.sortMode['condition'](self.mods):
            self.sortMode = self.sortModes[self.sortMode['next']]
            self.sortButton.label = "Sorting:\n" + self.sortMode['name']

        self.mods = self.sortMode["func"](self.mods)
        visible = self.mods[:]
        if self._selectedTab["label"] != "all":
            visible = [m for m in visible if m.category == self._selectedTab["label"]]

        for index, mod in enumerate(visible):
            color = (0.6, 0.6, 0.7, 1.0)
            if mod.isInstalled():
                color = (0.85, 0.85, 0.85, 1)
                if mod.checkUpdate():
                    if mod.is_outdated():
                        color = (0.85, 0.3, 0.3, 1)
                    else:
                        color = (1, 0.84, 0, 1)

            w = TextWidget(parent=self._columnWidget, size=(self._width - 40, 24),
                           maxWidth=self._width - 110,
                           text=mod.name,
                           hAlign='left', vAlign='center',
                           color=color,
                           alwaysHighlight=True,
                           onSelectCall=bs.Call(self._cb_select, index, mod),
                           onActivateCall=bs.Call(self._cb_info, True),
                           selectable=True)
            w.showBufferTop = 50
            w.showBufferBottom = 50
            # hitting up from top widget shoud jump to 'back;
            if index == 0:
                tab_button = self.tabs[int((len(self.tabs)-1)/2)]["button"]
                w.upWidget = tab_button

            if self._selectedMod and mod.filename == self._selectedMod.filename:
                self._columnWidget.set(selectedChild=w, visibleChild=w)

            self._modWidgets.append(w)

    def _refreshTabs(self):
        if not self._rootWidget.exists():
            return
        for t in self.tabs:
            for widget in t.values():
                if isinstance(widget, bs.Widget) or isinstance(widget, Widget):
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
            txt = TextWidget(parent=self._rootWidget, position=center, size=(0, 0),
                             hAlign='center', vAlign='center',
                             maxWidth=1.4*rad, scale=0.6, shadow=1.0, flatness=1.0)
            button = ButtonWidget(parent=self._rootWidget, position=pos, autoSelect=True,
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

        for i, tab in enumerate(self.tabs):
            button = tab["button"]
            if i == index:
                button.set(color=(0.5, 0.4, 0.93), textColor=(0.85, 0.75, 0.95))  # lit
            else:
                button.set(color=(0.52, 0.48, 0.63), textColor=(0.65, 0.6, 0.7))  # unlit
        if refresh:
            self._refresh(refreshTabs=False)

    def _cb_select(self, index, mod):
        self._selectedModIndex = index
        self._selectedMod = mod

    def _cb_refresh(self, force_fresh=False):
        self.mods = []
        localfiles = os.listdir(bs.getEnvironment()['userScriptsDirectory'] + "/")
        for file in localfiles:
            if file.endswith(".py"):
                self.mods.append(LocalMod(file))

        # if CHECK_FOR_UPDATES:
        #     for mod in self.mods:
        #         if mod.checkUpdate():
        #             bs.screenMessage('Update available for ' + mod.filename)
        #             UpdateModWindow(mod, self._cb_refresh)

        self._refresh()
        self.currently_fetching = True

        def f(*args, **kwargs):
            kwargs["force_fresh"] = force_fresh
            self._cb_serverdata(*args, **kwargs)
        get_index(f, force_fresh=force_fresh)
        self.timers["showFetchingIndicator"] = bs.Timer(500, bs.WeakCall(self._showFetchingIndicator), timeType='real')

    def _cb_serverdata(self, data, status_code, force_fresh=False):
        if not self._rootWidget.exists():
            return
        self.currently_fetching = False
        if data:
            m, v = process_server_data(data)
            # when we got network add the network mods
            localMods = self.mods[:]
            netMods = [Mod(d) for d in m.values()]
            self.mods = netMods
            netFilenames = [m.filename for m in netMods]
            for localmod in localMods:
                if localmod.filename not in netFilenames:
                    self.mods.append(localmod)
            for mod in self.mods:
                mod._mods = {m.base: m for m in self.mods}
            self._refresh()
        else:
            bs.screenMessage('network error :(')
        fetch_ratings(self._cb_ratings, force_fresh=force_fresh)

    def _cb_ratings(self, data, status_code):
        if not self._rootWidget.exists():
            return
        if not data or 'average' not in data:
            return
        for mod_id, rating in data['average'].items():
            for mod in self.mods:
                if mod.base == mod_id:
                    mod.rating = rating

        for mod_id, rating in data.get('own', {}).items():
            for mod in self.mods:
                if mod.base == mod_id:
                    mod.own_rating = rating

        for mod_id, amount in data.get('amount', {}).items():
            for mod in self.mods:
                if mod.base == mod_id:
                    mod.rating_submissions = amount

        self._refresh()

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
        while not self.sortMode['condition'](self.mods):
            self.sortMode = self.sortModes[self.sortMode['next']]
        config['sortMode'] = self.sortMode['name']
        bs.writeConfig()
        self.sortButton.label = "Sorting:\n" + self.sortMode['name']
        self._cb_refresh()

    def _back(self):
        self._rootWidget.doTransition(self._transitionOut)
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
        text = text % (mod.filename)
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

        self._rootWidget = ConfirmWindow("Are you sure you want to delete " + mod.filename + self.ok).getRootWidget()

    def ok(self):
        self.mod.delete(self.onok)
        QuitToApplyWindow()


class RateModWindow(Window):
    levels = ["Poor", "Below Average", "Average", "Above Average", "Excellent"]
    icons = ["trophy0b", "trophy1", "trophy2", "trophy3", "trophy4"]

    def __init__(self, mod, onok, swish=True, back=False):
        self._back = back
        self.mod = mod
        self.onok = onok
        if swish:
            bs.playSound(bs.getSound('swish'))
        text = "How do you want to rate {}?".format(mod.name)

        okText = bs.getResource('okText')
        cancelText = bs.getResource('cancelText')
        width = 360
        height = 330

        self._rootWidget = ContainerWidget(size=(width, height), transition='inRight',
                                           scale=2.1 if gSmallUI else 1.5 if gMedUI else 1.0)

        TextWidget(parent=self._rootWidget, position=(width*0.5, height - 30), size=(0, 0),
                   hAlign="center", vAlign="center", text=text, maxWidth=width*0.9, maxHeight=height-75)

        b = ButtonWidget(parent=self._rootWidget, autoSelect=True, position=(20, 20), size=(150, 50), label=cancelText, onActivateCall=self._cancel)
        self._rootWidget.set(cancelButton=b)
        okButtonH = width-175

        b = ButtonWidget(parent=self._rootWidget, autoSelect=True, position=(okButtonH, 20), size=(150, 50), label=okText, onActivateCall=self._ok)

        self._rootWidget.set(selectedChild=b, startButton=b)

        columnPosY = height - 75
        _scrollHeight = height - 150

        scrollWidget = ScrollWidget(parent=self._rootWidget, position=(20, columnPosY - _scrollHeight), size=(width - 40, _scrollHeight+10))
        columnWidget = ColumnWidget(parent=scrollWidget)

        self._rootWidget.set(selectedChild=columnWidget)

        self.selected = self.mod.own_rating or 2
        for num, name in enumerate(self.levels):
            s = bs.getSpecialChar(self.icons[num]) + name
            w = TextWidget(parent=columnWidget, size=(width - 40, 24 + 8),
                           maxWidth=width - 110,
                           text=s,
                           scale=0.85,
                           hAlign='left', vAlign='center',
                           alwaysHighlight=True,
                           onSelectCall=bs.Call(self._select, num),
                           onActivateCall=bs.Call(self._ok),
                           selectable=True)
            w.showBufferTop = 50
            w.showBufferBottom = 50

            if num == self.selected:
                columnWidget.set(selectedChild=w, visibleChild=w)
                self._rootWidget.set(selectedChild=w)
            elif num == 4:
                w.downWidget = b

    def _select(self, index):
        self.selected = index

    def _cancel(self):
        self._rootWidget.doTransition('outRight')

    def _ok(self):
        if not self._rootWidget.exists():
            return
        self._rootWidget.doTransition('outLeft')
        self.onok(self.selected)


class QuitToApplyWindow(Window):

    def __init__(self):
        global quittoapply
        if quittoapply is not None:
            quittoapply.delete()
            quittoapply = None
        bs.playSound(bs.getSound('swish'))
        text = "Quit BS to reload mods?"
        if bs.getEnvironment()["platform"] == "android":
            text += "\n(On Android you have to close the activity)"
        self._rootWidget = quittoapply = ConfirmWindow(text, self._doFadeAndQuit).getRootWidget()

    def _doFadeAndQuit(self):
        # FIXME: using protected apis
        bsInternal._fadeScreen(False, time=200, endCall=bs.Call(bs.quit, soft=True))
        bsInternal._lockAllInput()
        # unlock and fade back in shortly.. just in case something goes wrong
        # (or on android where quit just backs out of our activity and we may come back)
        bs.realTimer(300, bsInternal._unlockAllInput)
        # bs.realTimer(300,bs.Call(bsInternal._fadeScreen,True))


class ModInfoWindow(Window):
    def __init__(self, mod, modManagerWindow, originWidget=None):
        # TODO: cleanup
        self.modManagerWindow = modManagerWindow
        self.mod = mod
        s = 1.1 if gSmallUI else 1.27 if gMedUI else 1.57
        bColor = (0.6, 0.53, 0.63)
        bTextColor = (0.75, 0.7, 0.8)
        width = 360 * s
        height = 40 + 100 * s
        if mod.author:
            height += 25
        if not mod.isLocal:
            height += 50
        if mod.rating:
            height += 50

        buttons = sum([(mod.checkUpdate() or not mod.isInstalled()), mod.isInstalled(), mod.isInstalled(), True])

        color = (1, 1, 1)
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

        self._rootWidget = ContainerWidget(size=(width, height), transition=transition,
                                           scale=2.1 if gSmallUI else 1.5 if gMedUI else 1.0,
                                           scaleOriginStackOffset=scaleOrigin)

        # t = bs.textWidget(parent=self._rootWidget,position=(width*0.5,height-5-(height-75)*0.5),size=(0,0),
        #                   hAlign="center",vAlign="center",text=text,scale=textScale,color=color,maxWidth=width*0.9,maxHeight=height-75)
        pos = height * (0.9 if buttons else 0.8)
        labelspacing = height * (0.15 if buttons else 0.175)

        TextWidget(parent=self._rootWidget, position=(width*0.5, pos), size=(0, 0),
                   hAlign="center", vAlign="center", text=mod.name, scale=textScale * 1.5,
                   color=color, maxWidth=width*0.9, maxHeight=height-75)
        pos -= labelspacing
        if mod.author:
            TextWidget(parent=self._rootWidget, position=(width*0.5, pos), size=(0, 0),
                       hAlign="center", vAlign="center", text="by "+mod.author, scale=textScale,
                       color=color, maxWidth=width*0.9, maxHeight=height-75)
            pos -= labelspacing
        if not mod.isLocal:
            if mod.checkUpdate():
                if mod.is_outdated():
                    status = "update available"
                else:
                    status = "unrecognized version"
            else:
                status = "installed"
            if not mod.isInstalled():
                status = "not installed"
            TextWidget(parent=self._rootWidget, position=(width*0.45, pos), size=(0, 0),
                       hAlign="right", vAlign="center", text="Status:", scale=textScale,
                       color=color, maxWidth=width*0.9, maxHeight=height-75)
            status = TextWidget(parent=self._rootWidget, position=(width*0.55, pos), size=(0, 0),
                                hAlign="left", vAlign="center", text=status, scale=textScale,
                                color=color, maxWidth=width*0.9, maxHeight=height-75)
            pos -= labelspacing * 0.8

        if mod.rating:
            TextWidget(parent=self._rootWidget, position=(width*0.45, pos), size=(0, 0),
                       hAlign="right", vAlign="center", text="Rating:", scale=textScale,
                       color=color, maxWidth=width*0.9, maxHeight=height-75)
            rating_str = bs.getSpecialChar(RateModWindow.icons[mod.rating]) + RateModWindow.levels[mod.rating]
            TextWidget(parent=self._rootWidget, position=(width*0.4725, pos), size=(0, 0),
                       hAlign="left", vAlign="center", text=rating_str, scale=textScale,
                       color=color, maxWidth=width*0.9, maxHeight=height-75)
            pos -= labelspacing * 0.8
            submissions = "({} {})".format(mod.rating_submissions, "submission" if mod.rating_submissions < 2 else "submissions")
            TextWidget(parent=self._rootWidget, position=(width*0.4725, pos), size=(0, 0),
                       hAlign="left", vAlign="center", text=submissions, scale=textScale,
                       color=color, maxWidth=width*0.9, maxHeight=height-75)
            pos += labelspacing * 0.4

        if not mod.author and mod.isLocal:
            pos -= labelspacing

        if not (gSmallUI or gMedUI):
            pos -= labelspacing * 0.25

        pos -= labelspacing * 2.75

        self.button_index = -1

        def button_pos():
            self.button_index += 1
            d = {
                1: [0.5],
                2: [0.3, 0.7],
                3: [0.2, 0.45, 0.8],
                4: [0.17, 0.390, 0.61, 0.825],
            }
            x = width * d[buttons][self.button_index]
            y = pos
            sx, sy = button_size()
            x -= sx / 2
            y += sy / 2
            return x, y

        def button_size():
            sx = {1: 100, 2: 80, 3: 80, 4: 75}[buttons] * s
            sy = 40 * s
            return sx, sy

        def button_text_size():
            return {1: 0.8, 2: 1.0, 3: 1.2, 4: 1.2}[buttons]

        if mod.checkUpdate() or not mod.isInstalled():
            self.downloadButton = ButtonWidget(parent=self._rootWidget,
                                               position=button_pos(), size=button_size(),
                                               onActivateCall=bs.Call(self._download,),
                                               color=bColor,
                                               autoSelect=True,
                                               textColor=bTextColor,
                                               buttonType='square',
                                               textScale=button_text_size(),
                                               label="Update Mod" if mod.checkUpdate() else "Download Mod")

        if mod.isInstalled():
            self.deleteButton = ButtonWidget(parent=self._rootWidget,
                                             position=button_pos(), size=button_size(),
                                             onActivateCall=bs.Call(self._delete),
                                             color=bColor,
                                             autoSelect=True,
                                             textColor=bTextColor,
                                             buttonType='square',
                                             textScale=button_text_size(),
                                             label="Delete Mod")

            self.rateButton = ButtonWidget(parent=self._rootWidget,
                                           position=button_pos(), size=button_size(),
                                           onActivateCall=bs.Call(self._rate),
                                           color=bColor,
                                           autoSelect=True,
                                           textColor=bTextColor,
                                           buttonType='square',
                                           textScale=button_text_size(),
                                           label="Rate Mod" if mod.own_rating is None else "Change Rating")

        okButtonSize = button_size()
        okButtonPos = button_pos()
        okText = bs.getResource('okText')
        b = ButtonWidget(parent=self._rootWidget, autoSelect=True, position=okButtonPos, size=okButtonSize, label=okText, onActivateCall=self._ok)

        self._rootWidget.onCancelCall = b.activate
        self._rootWidget.selectedChild = b
        self._rootWidget.startButton = b

    def _ok(self):
        self._rootWidget.doTransition('outLeft' if self._transitionOut is None else self._transitionOut)

    def _delete(self):
        DeleteModWindow(self.mod, self.modManagerWindow._cb_refresh)
        self._ok()

    def _download(self):
        UpdateModWindow(self.mod, self.modManagerWindow._cb_refresh)
        self._ok()

    def _rate(self):

        def submit_cb():
            self.modManagerWindow._cb_refresh(force_fresh=True)

        def cb(rating):
            submit_mod_rating(self.mod, rating, submit_cb)

        RateModWindow(self.mod, cb)
        self._ok()


class SettingsWindow(Window):
    def __init__(self, mod, modManagerWindow, originWidget=None):
        self.modManagerWindow = modManagerWindow
        self.mod = mod
        s = 1.1 if gSmallUI else 1.27 if gMedUI else 1.57
        bTextColor = (0.75, 0.7, 0.8)
        width = 380 * s
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

        self._rootWidget = ContainerWidget(size=(width, height), transition=transition,
                                           scale=2.1 if gSmallUI else 1.5 if gMedUI else 1.0,
                                           scaleOriginStackOffset=scaleOrigin)

        self._titleText = TextWidget(parent=self._rootWidget, position=(0, height - 52),
                                     size=(width, 30), text="ModManager Settings", color=(1.0, 1.0, 1.0),
                                     hAlign="center", vAlign="top", scale=1.5 * textScale)

        pos = height * 0.65
        TextWidget(parent=self._rootWidget, position=(width*0.35, pos), size=(0, 40),
                   hAlign="right", vAlign="center",
                   text="Branch:", scale=textScale,
                   color=bTextColor, maxWidth=width*0.9, maxHeight=height-75)
        self.branch = TextWidget(parent=self._rootWidget, position=(width*0.4, pos),
                                 size=(width * 0.4, 40), text=config.get("branch", "master"),
                                 hAlign="left", vAlign="center",
                                 editable=True, padding=4,
                                 onReturnPressCall=self.setBranch)

        pos -= height * 0.15
        checkUpdatesValue = config.get("auto-check-updates", True)
        self.checkUpdates = CheckBoxWidget(parent=self._rootWidget, text="auto check for updates",
                                           position=(width * 0.2, pos), size=(170, 30),
                                           textColor=(0.8, 0.8, 0.8),
                                           value=checkUpdatesValue,
                                           onValueChangeCall=self.setCheckUpdate)

        pos -= height * 0.2
        autoUpdatesValue = config.get("auto-update-old-mods", True)
        self.autoUpdates = CheckBoxWidget(parent=self._rootWidget, text="auto-update old mods",
                                          position=(width * 0.2, pos), size=(170, 30),
                                          textColor=(0.8, 0.8, 0.8),
                                          value=autoUpdatesValue,
                                          onValueChangeCall=self.setAutoUpdate)
        self.checkAutoUpdateState()

        okButtonSize = (150, 50)
        okButtonPos = (width * 0.5 - okButtonSize[0]/2, 20)
        okText = bs.getResource('okText')
        b = ButtonWidget(parent=self._rootWidget, position=okButtonPos, size=okButtonSize, label=okText, onActivateCall=self._ok)

        # back on window = okbutton
        self._rootWidget.set(onCancelCall=b.activate, selectedChild=b, startButton=b)

        b.upWidget = self.autoUpdates
        self.autoUpdates.upWidget = self.checkUpdates
        self.checkUpdates.upWidget = self.branch

    def _ok(self):
        if self.branch.text() != config.get("branch", "master"):
            self.setBranch()
        self._rootWidget.doTransition('outLeft' if self._transitionOut is None else self._transitionOut)

    def setBranch(self):
        branch = self.branch.text()
        if branch == '':
            branch = "master"
        bs.screenMessage("fetching branch '" + branch + "'")

        def cb(data, status_code):
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
        config["auto-check-updates"] = bool(val)
        bs.writeConfig()
        self.checkAutoUpdateState()

    def checkAutoUpdateState(self):
        if not self.checkUpdates.value:
            # FIXME: properly disable checkbox
            self.autoUpdates.set(value=False,
                                 color=(0.65, 0.65, 0.65),
                                 textColor=(0.65, 0.65, 0.65))
        else:
            # FIXME: match original color
            autoUpdatesValue = config.get("auto-update-old-mods", True)
            self.autoUpdates.set(value=autoUpdatesValue,
                                 color=(0.475, 0.6, 0.2),
                                 textColor=(0.8, 0.8, 0.8))

    def setAutoUpdate(self, val):
        # FIXME: properly disable checkbox
        if not self.checkUpdates.value:
            bs.playSound(bs.getSound("error"))
            self.autoUpdates.value = False
            return
        config["auto-update-old-mods"] = bool(val)
        bs.writeConfig()


class Mod:
    name = False
    author = None
    filename = None
    base = None
    changelog = []
    old_md5s = []
    url = False
    isLocal = False
    experimental = False
    category = None
    requires = []
    supports = []
    rating = None
    rating_submissions = 0
    own_rating = None
    downloads = None

    def __init__(self, d):
        self.author = d.get('author')
        if 'filename' in d:
            self.filename = d['filename']
            self.base = self.filename[:-3]
        else:
            print(d)
            raise RuntimeError('mod without filename')
        if 'name' in d:
            self.name = d['name']
        else:
            self.name = self.filename
        if 'md5' in d:
            self.md5 = d['md5']
        else:
            raise RuntimeError('mod without md5')
        if 'url' in d:
            self.url = d['url']
        else:
            raise RuntimeError('mod without url')

        self.changelog = d.get('changelog', [])
        self.old_md5s = d.get('old_md5s', [])
        self.category = d.get('category', None)
        self.requires = d.get('requires', [])
        self.supports = d.get('supports', [])
        self.experimental = d.get('experimental', self.experimental)

    def writeData(self, callback, doQuitWindow, data, status_code):
        path = bs.getEnvironment()['userScriptsDirectory'] + "/" + self.filename

        if data:
            if self.isInstalled():
                os.rename(path, path + ".bak")  # rename the old file to be able to recover it if something is wrong
            with open(path, 'w') as f:
                f.write(data)
        else:
            bs.screenMessage("Failed to write mod")

        if callback:
            callback(self, data is not None)
        if doQuitWindow:
            QuitToApplyWindow()

    def install(self, callback, doQuitWindow=True):
        def check_deps_and_install(mod=None, succeded=True):
            if any([dep not in self._mods for dep in self.requires]):
                raise Exception("dependency inconsistencies")
            if not all([self._mods[dep].uptodate() for dep in self.requires]) or not succeded:
                return
            if self.url:
                mm_serverGet(self.url, {}, partial(self.writeData, callback, doQuitWindow), eval_data=False)
            else:
                bs.screenMessage("cannot download mod without url")
                raise Exception("mod.install() without url")
        if len(self.requires) < 1:
            check_deps_and_install()
        else:
            for dep in self.requires:
                bs.screenMessage(self.name + " requires " + dep + "; installing...")
                if not self._mods:
                    raise Exception("missing mod._mods")
                if dep not in self._mods:
                    raise Exception("dependency inconsistencies (missing " + dep + ")")
                self._mods[dep].install(check_deps_and_install, False)

    @property
    def ownData(self):
        path = bs.getEnvironment()['userScriptsDirectory'] + "/" + self.filename
        if os.path.exists(path):
            with open(path, "r") as ownFile:
                return ownFile.read()

    def delete(self, cb=None):
        path = bs.getEnvironment()['userScriptsDirectory'] + "/" + self.filename
        os.rename(path, path + ".bak")  # rename the old file to be able to recover it if something is wrong
        if os.path.exists(path + "c"):
            os.remove(path + "c")  # remove .pyc files because importing them still works without .py file
        if cb:
            cb()

    def checkUpdate(self):
        if not self.isInstalled():
            return False
        if self.local_md5() != self.md5:
            return True
        return False

    def uptodate(self):
        return self.isInstalled() and self.local_md5() == self.md5

    def isInstalled(self):
        return os.path.exists(bs.getEnvironment()['userScriptsDirectory'] + "/" + self.filename)

    def local_md5(self):
        return md5(self.ownData).hexdigest()

    def is_outdated(self):
        if not self.old_md5s:
            return False
        local_md5 = self.local_md5()
        for old_md5 in self.old_md5s:
            if local_md5.startswith(old_md5):
                return True
        return False


class LocalMod(Mod):
    isLocal = True

    def __init__(self, filename):
        self.filename = filename
        self.base = self.filename[:-3]
        self.name = filename + " (Local Only)"
        with open(bs.getEnvironment()['userScriptsDirectory'] + "/" + filename, "r") as ownFile:
            self.ownData = ownFile.read()

    def checkUpdate(self):
        return False

    def isInstalled(self):
        return True

    def uptodate(self):
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
                                                   size=(178, 50), position=(70, 60))
        # TODO: transitions


def _onGetMoreGamesPress(self):
    if not self._modal:
        bs.containerWidget(edit=self._rootWidget, transition='outLeft')
    mm_window = ModManagerWindow(modal=self._modal, backLocationCls=self.__class__, showTab="minigames")
    if not self._modal:
        uiGlobals['mainMenuWindow'] = mm_window.getRootWidget()

StoreWindow._setTab = _setTab
StoreWindow._onGetMoreGamesPress = _onGetMoreGamesPress
