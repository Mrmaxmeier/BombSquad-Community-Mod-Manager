import bs
import os
import os.path
from md5 import md5
import weakref

### importlib isnt importable...
"""Backport of importlib.import_module from 3.x."""
# While not critical (and in no way guaranteed!), it would be nice to keep this
# code compatible with Python 2.3.
import sys

def _resolve_name(name, package, level):
    """Return the absolute name of the module to be imported."""
    if not hasattr(package, 'rindex'):
        raise ValueError("'package' not set to a string")
    dot = len(package)
    for x in xrange(level, 1, -1):
        try:
            dot = package.rindex('.', 0, dot)
        except ValueError:
            raise ValueError("attempted relative import beyond top-level "
                              "package")
    return "%s.%s" % (package[:dot], name)


def import_module(name, package=None):
    """Import a module.

    The 'package' argument is required when performing a relative import. It
    specifies the package to use as the anchor point from which to resolve the
    relative import to an absolute import.

    """
    if name.startswith('.'):
        if not package:
            raise TypeError("relative imports require the 'package' argument")
        level = 0
        for character in name:
            if character != '.':
                break
            level += 1
        name = _resolve_name(name[level:], package, level)
    __import__(name)
    return sys.modules[name]
###

CHECK_INTERVAL = 1000 * 10
IMPORT_FOLDER = bs.getEnvironment()['userScriptsDirectory'] + "/auto_reloader_mods/"
sys.path.append(IMPORT_FOLDER) # FIXME

class GameWrapper(object):
    _game = None
    _instances = weakref.WeakSet()
    def __init__(self, filename):
        self._filename = filename
        self._reserved = ["_reserved", "_filename", "_module", "_game", "_is_available",
                          "_module_error", "_reload_module", "_did_print_error", "_module_md5"]
        with open(IMPORT_FOLDER + self._filename, "r") as f:
            self._module_md5 = md5(f.read()).hexdigest()
        self._did_print_error = False
        print("importing", filename)
        #self._module = imp.load_module("auto_reloader." + filename[:-3], None, IMPORT_FOLDER+filename, imp.get_suffixes())
        self._module = import_module(self._filename[:-3], package=IMPORT_FOLDER.split("/")[-2])
        print(self._module)
        if self._is_available():
            self._game = self._module.bsGetGames()[0]
        else:
            self._game = None
        print(self._is_available())
        print(self._game)
        print(dir(self._module))

    def _module_error(*args):
        print(self._filename + ": " + " ".join(*args))
        if not self._did_print_error:
            bs.screenMessage(self._filename + ": " + " ".join(*args))
            self._did_print_error = True

    def _is_available(self):
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
        if any([hasattr(self._module, attr) for attr in self._reserved]):
            self._module_error("defines reserved methods")
            return False
        return True

    def _reload_module(self):
        bs.screenMessage("reloading " + self._filename)
        if hasattr(self._module, "_prepare_reload"):
            self._module._prepare_reload()
        for instance in self._instances:
            if instance and hasattr(instance, "_prepare_reload"):
                instance._prepare_reload()
        self._module = import_module(self._filename[:-3], package=IMPORT_FOLDER.split("/")[-2])
        with open(IMPORT_FOLDER + self._filename, "r") as f:
            self._module_md5 = md5(f.read()).hexdigest()
        self._did_print_error = False
        if self._is_available():
            self._game = self._module.bsGetGames()[0]
        else:
            self._game = None

    def _check_update(self):
        with open(IMPORT_FOLDER + self._filename, "r") as f:
            if self._module_md5 != md5(f.read()).hexdigest():
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
