import bs
import os
import os.path
from md5 import md5
import weakref
import imp
import sys

CHECK_INTERVAL = int(1000 * 2.5)
IMPORT_FOLDER = bs.getEnvironment()['userScriptsDirectory'] + "/auto_reloader_mods/"
sys.path.append(IMPORT_FOLDER) # FIXME

class GameWrapper(object):
    _game = None
    _instances = weakref.WeakSet()
    def __init__(self, filename):
        self._filename = filename
        with open(IMPORT_FOLDER + self._filename, "r") as f:
            self._module_md5 = md5(f.read()).hexdigest()
        self._did_print_error = False
        self._import_module()
        if self._is_available():
            self._game = self._module.bsGetGames()[0]
        else:
            self._game = None

    def _import_module(self):
        try:
            data = imp.find_module(self._filename[:-3])
            self._module = imp.load_module(self._filename[:-3], *data)
        except Exception, e:
            print(e)
            self._module = None
            self._game = None
            self._module_error(str(e))

    def _module_error(self, *args):
        print(self._filename + ": " + " ".join(args))
        if not self._did_print_error:
            bs.screenMessage(self._filename + ": " + " ".join(args), color=(1, 0, 0))
            self._did_print_error = True

    def _is_available(self):
        if not self._module:
            return False
        if not hasattr(self._module, '_supports_auto_reloading'):
            self._module_error('missing _supports_auto_reloading')
            return False
        if not hasattr(self._module, '_prepare_reload'):
            self._module_error('missing _prepare_reload')
            return False
        if not hasattr(self._module, 'bsGetAPIVersion'):
            self._module_error('missing bsGetAPIVersion')
            return False
        if not hasattr(self._module, 'bsGetGames'):
            self._module_error('missing bsGetGames')
            return False

        if not self._module._supports_auto_reloading:
            self._module_error('doesnt support auto reloading')
            return False
        if not self._module.bsGetAPIVersion() == 3:
            self._module_error('missing wrong API Version', self._module.bsGetAPIVersion())
            return False
        if len(self._module.bsGetGames()) != 1:
            self._module_error("more than 1 game isnt supported") # FIXME
            return False
        return True

    def _prepare_reload(self):
        if hasattr(self._module, "_prepare_reload"):
            self._module._prepare_reload()
        for instance in self._instances:
            if instance and hasattr(instance, "_prepare_reload"):
                instance._prepare_reload()

    def _reload_module(self):
        bs.screenMessage("reloading " + self._filename)
        self._prepare_reload()
        self._import_module()
        #self._module = import_module(self._filename[:-3], package=IMPORT_FOLDER.split("/")[-2])
        with open(IMPORT_FOLDER + self._filename, "r") as f:
            self._module_md5 = md5(f.read()).hexdigest()
        self._did_print_error = False
        if self._is_available():
            self._game = self._module.bsGetGames()[0]
        else:
            self._game = None
        bs.playSound(bs.getSound('swish'))

    def _check_update(self):
        with open(IMPORT_FOLDER + self._filename, "r") as f:
            data = f.read()
            if self._module_md5 != md5(data).hexdigest():
                self._reload_module()

    def __call__(self, *args, **kwargs):
        instance = self._game(*args, **kwargs)
        self._instances.add(instance)
        return instance

    def __getattr__(self, key):
        "pass static methods"
        return getattr(self._game, key)

wrappers = []

if not os.path.isdir(IMPORT_FOLDER):
    os.mkdir(IMPORT_FOLDER)

for file in os.listdir(IMPORT_FOLDER):
    if not file.endswith(".py"):
        continue
    if file.startswith("."):
        continue
    wrappers.append(GameWrapper(file))

wrappers = [w for w in wrappers if w._is_available()]
print("tracking mods:", [wrapper._filename for wrapper in wrappers])

def check_wrappers():
    for wrapper in wrappers:
        wrapper._check_update()
    bs.realTimer(CHECK_INTERVAL, check_wrappers)

if CHECK_INTERVAL:
    bs.realTimer(CHECK_INTERVAL, check_wrappers)

def bsGetAPIVersion():
	return 3

def bsGetGames():
	return wrappers
