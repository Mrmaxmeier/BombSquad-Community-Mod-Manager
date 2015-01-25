import json
import os
import hashlib
import ast # literal eval for the win
import time
from os import listdir
from os.path import isfile, join
#import subprocess

import cherrypy
import git

#from jinja2 import Environment, FileSystemLoader

#basePATH = './'
#env = Environment(loader=FileSystemLoader(basePATH+'frontend'))
#indexTmpl = env.get_template('index.html')

userData = {}# {ID: {STATS}}

with open('stats.json', 'r') as f:
	userData = json.loads(f.read())

#print(userData)

def writeUserData():
	with open('stats.json', 'w') as f:
		f.write(json.dumps(userData))


gitRepo = git.Repo("./")



class Mod:
	def __init__(self, filename):
		self.name = filename
		self.filename = filename
		self.author = ""
		self.playability = 0# 0: not at all, 0.5: playable but buggy, 1: playable and featurecomplete
		file = open("./mods/"+filename, "r")
		self.content = file.read()
		m = hashlib.md5(self.content.encode("utf-8"))
		self.md5 = m.hexdigest()
		file.close()
		if os.path.exists("./mods/"+filename.replace(".py", ".json")):
			#json file avalible
			with open("./mods/"+filename.replace(".py", ".json"), "r") as jf:
				d = json.load(jf)
				if 'author' in d:
					self.author = d['author']
				if 'name' in d:
					self.name = d['name']
				if 'playability' in d:
					self.playability = d['playability']
		self.changelog = []


	def dict(self):
		return {'name': self.name, 'filename': self.filename,
				'author': self.author,
				'md5': self.md5, 'uniqueInstalls': self.numInstalled(),
				'changelog': self.changelog[:3], 'playability': self.playability}

	def getData(self):
		return self.content

	def numInstalled(self):
		num = 0
		for user, data in userData.items():
			if self.filename in data['installedMods']:
				num += 1
		return num

	def __repr__(self):
		return "{name} w/ {installs} unique installations\n".format(name=self.name, installs=self.numInstalled())







class Root:

	_cp_config = {
		'tools.sessions.on': True,
	}

	def __init__(self):
		print('rootInit')
		self.files = os.listdir("./mods")
		print(self.files)
		self.mods = []
		for file in self.files:
			if file.endswith(".py"):
				self.mods.append(Mod(file))
		self.hash2Mod = {mod.md5:mod for mod in self.mods}
		self.filename2mod = {mod.filename:mod for mod in self.mods}

		for commit in gitRepo.iter_commits(max_count=50, paths="mods/"):
			#print(commit.message)
			for filename in commit.stats.files:
				if filename.startswith("mods/"):
					filename = filename[5:]
					if filename.endswith(".py"):
						if filename in self.filename2mod:
							txt = commit.message
							txt = txt.replace("\n", "")
							self.filename2mod[filename].changelog.append(txt)
		#for mod in self.mods:
		#	print(mod.name, ":")
		#	print(mod.changelog)
	
	@cherrypy.expose
	def getModList(self):
		return repr([m.dict() for m in self.mods]) # no json in BombSquad-Python

	@cherrypy.expose
	def getData(self, md5):
		if md5 in self.hash2Mod:
			return self.hash2Mod[md5].getData()
		return False

	@cherrypy.expose
	def submitStats(self, stats):
		stats = ast.literal_eval(stats)
		stats['lastSubmitted'] = time.time()
		print(stats)
		if not 'uniqueID' in stats:
			print('no id in stats', stats)
			return
		userData[stats['uniqueID']] = stats
		writeUserData()





	@cherrypy.expose
	def index(self):
		mods = sorted(self.mods, key=lambda mod: mod.numInstalled(), reverse=True)
		return "<br \>".join([mod.__repr__() for mod in mods])
		#indexTmpl.render(loginname = cherrypy.request.remote.ip, serverstatus=self.server.status, log=self.server.console_log)



path = os.path.dirname(os.path.abspath(__file__))+"/"
cherrypy.engine.autoreload.files.add("mods/")



cherrypy.config.update({'server.socket_host': '0.0.0.0',
						'server.socket_port': 3666,
					 	'log.error_file': './error.log'})

cherrypy.tree.mount(Root(), '/')
cherrypy.engine.start()
cherrypy.engine.block()
