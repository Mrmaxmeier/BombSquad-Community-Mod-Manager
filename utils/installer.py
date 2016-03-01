import bs
import bsInternal
import threading
import json
import urllib2
import weakref
import os, os.path

branch = "master"
url = "https://rawgit.com/Mrmaxmeier/BombSquad-Community-Mod-Manager/" + branch + "/index.json"
SUPPORTS_HTTPS = False
modPath = bs.getEnvironment()['userScriptsDirectory'] + "/"
mod =  "modManager"

class SimpleGetThread(threading.Thread):
	def __init__(self, url, callback=None):
		threading.Thread.__init__(self)
		self._url = url.encode("ascii") # embedded python2.7 has weird encoding issues
		if not SUPPORTS_HTTPS and self._url.startswith("https://"):
			self._url = "http://" + self._url[8:]
		self._callback = callback or (lambda d: None)
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
			bsInternal._setThreadName("SimpleGetThread")
			response = urllib2.urlopen(self._url)
			bs.callInGameThread(bs.Call(self._runCallback, response.read()))
		except Exception, e:
			print(e)
			bs.callInGameThread(bs.Call(self._runCallback, None))

installed = []
installing = []
def check_finished():
	if any([m not in installed for m in installing]):
		return
	bs.screenMessage("installed everything.")
	if os.path.isfile(modPath + __name__ + ".pyc"):
		os.remove(modPath + __name__ + ".pyc")
	if os.path.isfile(modPath + __name__ + ".py"):
		os.remove(modPath + __name__ + ".py")
		bs.screenMessage("deleted self")
	bs.screenMessage("activating modManager")
	__import__(mod)

def install(data, mod):
	installing.append(mod)
	bs.screenMessage("installing " + str(mod))
	print("installing", mod)
	for dep in data[mod].get("requires", []):
		install(data, dep)
	url = data[mod]["url"]
	filename = data[mod]["filename"]
	def f(data):
		print("writing", filename)
		with open(modPath + filename, "w") as f:
			f.write(data)
		installed.append(mod)
		check_finished()
	SimpleGetThread(url, f).start()

def onIndex(data):
	if not data:
		bs.screenMessage("network error :(")
		return
	data = json.loads(data)
	install(data["mods"], mod)


SimpleGetThread(url, onIndex).start()
