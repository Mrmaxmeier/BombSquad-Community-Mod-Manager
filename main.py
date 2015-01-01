import json
import os
import hashlib
from os import listdir
from os.path import isfile, join
import subprocess
import re

import cherrypy

from jinja2 import Environment, FileSystemLoader

#basePATH = './'
#env = Environment(loader=FileSystemLoader(basePATH+'frontend'))
#indexTmpl = env.get_template('index.html')

regexpattern = re.compile(r'\#ModManager\#.+\#ModManager\#')

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
		r = re.search(regexpattern, self.content)
		if r:
			s = r.group(0).replace("#ModManager#", '')
			d = json.loads(s)
			if 'author' in d:
				self.author = d['author']
			if 'name' in d:
				self.name = d['name']


	def dict(self):
		return {'name': self.name, 'filename': self.filename,
				'author': self.author,
				'md5': self.md5}

	def getData(self):
		return self.content





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
