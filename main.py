import json
import os
import hashlib
import ast # literal eval for the win
from os import listdir
from os.path import isfile, join
#import subprocess

import cherrypy

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



class Mod:
	def __init__(self, filename):
		self.name = filename
		self.filename = filename
		self.author = ""
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


	def dict(self):
		return {'name': self.name, 'filename': self.filename,
				'author': self.author,
				'md5': self.md5, 'uniqueInstalls': self.numInstalled()}

	def getData(self):
		return self.content

	def numInstalled(self):
		num = 0
		for user, data in userData.items():
			if self.filename in data['installedMods']:
				num += 1
		return num







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
		#self.filename2mod = {mod.filename:mod for mod in self.mods}
	
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
		print(stats)
		if not 'uniqueID' in stats:
			print('no id in stats', stats)
			return
		userData[stats['uniqueID']] = stats
		writeUserData()





	@cherrypy.expose
	def index(self):
		return "top kek"#indexTmpl.render(loginname = cherrypy.request.remote.ip, serverstatus=self.server.status, log=self.server.console_log)



path = os.path.dirname(os.path.abspath(__file__))+"/"
cherrypy.engine.autoreload.files.add("mods/")



cherrypy.config.update({'server.socket_host': '0.0.0.0',
						'server.socket_port': 3666,
					 	'log.error_file': './error.log'})

cherrypy.tree.mount(Root(), '/')
cherrypy.engine.start()
cherrypy.engine.block()
