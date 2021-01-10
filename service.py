#!/usr/bin/env python3
from urllib.parse import parse_qs
from lib.oauth import verification
#from lib.database import helper as dbhelper
from lib.dbdriver import Loader as DBDriverLoader

import cherrypy, os, importlib, copy, yaml, logging, sys

_EXPOSE = ["fetchrows", "fieldrepresentsatable", "orderbyfield", "primaryfield", "mandatoryfields", "tables", "dbdriver"]

HTMLEscape = {"<": "&lt;", ">": "&gt;", "/*": "\/\*", "*/": "\*\/"}

oauthProviders = {}
APIconf = {}
imageurls = {}
atShutdown = []

def validateReadAction(json):
	for i in APIconf["mandatoryfields"]:
		if not i in json: # if a mandatory field hasn't been supplied by the client, then
			return False # which means the input is wrong
			
	if not APIconf["fieldrepresentsatable"] in json: # if the table name specifier hasn't been supplied by the client, then
		return False # which means the input is wrong
	return True
	
def validateWriteAction(self, func):
	result = validateReadAction(json) # validate the 'json' python3 dictionary input using the validator 'validateReadAction'
			
	if not APIconf["primaryfield"] in json and not result == True: # if the primary key for the primary field to send with that write request hasn't been supplied by the client and the validator we called above does not return any result, then
		return False # which means the input is wrong
	return True

class Fedgate(verification):
	def __init__(self, secretserverkey):
		self.secretserverkey = secretserverkey
		self.dbdriver = DBDriverLoader(APIconf)
		atShutdown.append(self.dbdriver.exit)
	
	@cherrypy.expose
	def login(self, loginProvider):
		self.__crossOrigin()
		if loginProvider in oauthProviders:
			if "sessionId" in cherrypy.request.cookie:
				self.logout()
			plugin = oauthProviders[loginProvider]["plugin"]
			config = oauthProviders[loginProvider]["config"]
			key = self.oauthLogin(plugin.getOAuthInstance(), config["requestTokenURL"], config["customerKey"], config["customerSecret"])
			return config["loginPage"] + "?oauth_token=" + str(key)
	
	@cherrypy.expose
	def callback(self, callbackProvider, oauth_token, oauth_verifier=""):
		if callbackProvider in oauthProviders:
			plugin = oauthProviders[callbackProvider]["plugin"]
			config = oauthProviders[callbackProvider]["config"]
			oauthSession = self.oauthCallback(plugin.getOAuthInstance(), config["accessTokenURL"], config["customerKey"], config["customerSecret"], oauth_token, oauth_verifier)
			
			#receive user identifier (provider dependent), provider name (provider dependent), generate user token and set it as cookie
			userident, imageurl = plugin.getUserIdentifier(oauthSession, config)
			userident = str(plugin.providerName()) + "_" + userident
			usertoken = userident + "|" + str("/".join(self.createExpireTime()))
			usertoken_hash = self.generateToken(usertoken)
			cookie = usertoken + "|" + usertoken_hash
			
			cherrypy.response.headers["Set-Cookie"] = "sessionId=" + cookie + "; Max-Age=" + str(60*60) + "; Path=/; HttpOnly"
			
			self.__redirect("redirectToAfterLogin")
	
	def __removeCookie(self, name):
		if name in cherrypy.request.cookie:
			cherrypy.response.cookie[name] = cherrypy.request.cookie[name]
			cherrypy.response.cookie[name]["expires"] = 0
			cherrypy.response.cookie[name]["Max-Age"] = 0
	
	def __redirect(self, name):
		if name in APIconf:
			cherrypy.response.status = "303"
			cherrypy.response.headers["Location"] = APIconf[name]
		else:
			return "NO REDIRECT SPECIFIED"
	
	def __convertToHttps(self, url):
		if url.lower().startswith("http:") and not url.lower().startswith("https:"):
			return "https:" + url[5:len(url)]
		return url
	
	def __escapeHTML(self, string):
		for i in HTMLEscape:
			string = string.replace(i, HTMLEscape[i])
		
		if "HTMLEscape" in APIconf:
			for i in APIconf["HTMLEscape"]:
				string = string.replace(i, APIconf["HTMLEscape"][i])
		
		return string
	
	def __crossOrigin(self):
		if "Origin" in cherrypy.request.headers:
			cherrypy.response.headers["Access-Control-Allow-Origin"] = cherrypy.request.headers["Origin"]
		elif "Host" in cherrypy.request.headers:
			cherrypy.response.headers["Access-Control-Allow-Origin"] = cherrypy.request.headers["Host"]
	
	@cherrypy.expose
	@cherrypy.tools.json_out()
	def loggedIn(self):
		self.__crossOrigin()
		if "sessionId" in cherrypy.request.cookie and self.isAuthorized(cherrypy.request.cookie["sessionId"].value):
			return {"message": "userLoggedIn"}
		return {"message": "userNotLoggedIn"}
	
	@cherrypy.expose
	@cherrypy.tools.json_out()
	def logout(self):
		self.__crossOrigin()
		if "sessionId" in cherrypy.request.cookie and self.isAuthorized(cherrypy.request.cookie["sessionId"].value):
			userid = cherrypy.request.cookie["sessionId"].value.split("|")[0]
			
			self.__removeCookie("sessionId")
			return {"url": APIconf["redirectToAfterLogout"]}
		return {"message": "userNotLoggedIn"}
	
	"""
	Client sends a JSON in the following format (example):
		{
		"channel": "telegram",
		"region": "Africa"
		}
	to get all entries in the channel `Africa`
	
	or sends a JSON in the following format (example):
		{
		"id": "7da135f7-c4e6-4122-8dfd-14a507b05a09",
		"channel": "telegram"
		}
	to receive the entry with the id `7da135f7-c4e6-4122-8dfd-14a507b05a09`
	
	or sends a JSON in the following format (example):
		{
		"channel": "telegram",
		"region": "Latin America",
		"name": "Brasilia"
		}
	to get all entries in the channel `Latin America` having or containing the name `Brasilia`
	"""
	@cherrypy.expose
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out()
	def getEntries(self):
		"""
		API endpoint to receive one or more entries using a certain search criteria
		"""
		self.__crossOrigin()
		if "sessionId" in cherrypy.request.cookie and self.isAuthorized(cherrypy.request.cookie["sessionId"].value):
			result = {}
			userid = cherrypy.request.cookie["sessionId"].value.split("|")[0]
			json = cherrypy.request.json
			
			for entry in json:
				json[entry] = self.__escapeHTML(json[entry])
			if validateReadAction(json):
				result = self.dbdriver.getEntries(json)
			
			if len(result) == 0:
				return {"message": "noResult"}
			elif type(result) is dict:
				return result
			else:
				return {"message": "insufficientResultByDBDriver"}
		return {"message": "userNotLoggedIn"}
	
	
	"""
	Client sends a JSON in the following format (example):
		{
		"channel": "telegram",
		"region": "Africa"
		}
	to get all entries in the channel `Africa`
	
	or sends a JSON in the following format (example):
		{
		"id": "7da135f7-c4e6-4122-8dfd-14a507b05a09",
		"channel": "telegram"
		}
	to receive the entry with the id `7da135f7-c4e6-4122-8dfd-14a507b05a09`
	
	or sends a JSON in the following format (example):
		{
		"channel": "telegram",
		"region": "Latin America",
		"name": "Brasilia"
		}
	to get all entries in the region `Latin America` having or containing the name `Brasilia`
	"""
	@cherrypy.expose
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out()
	def getDistinctEntries(self):
		"""
		API endpoint to receive one or more entries using a certain search criteria which is unique in every value given in the JSON key
		"""
		self.__crossOrigin()
		if "sessionId" in cherrypy.request.cookie and self.isAuthorized(cherrypy.request.cookie["sessionId"].value):
			result = {}
			userid = cherrypy.request.cookie["sessionId"].value.split("|")[0]
			json = cherrypy.request.json
			
			for entry in json:
				json[entry] = self.__escapeHTML(json[entry])
			if validateReadAction(json):
				result = self.dbdriver.getEntriesDistinct(json)
			
			if len(result) == 0:
				return {"message": "noResult"}
			elif type(result) is dict:
				return result
			else:
				return {"message": "insufficientResultByDBDriver"}
		return {"message": "userNotLoggedIn"}
	
	"""
	Client sends a JSON in the following format (example):
		{
		"channel": "telegram",
		"column": "region"
		}
	"""
	@cherrypy.expose
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out()
	def getUnique(self):
		"""
		API endpoint to receive all variations of values a key takes
		"""
		self.__crossOrigin()
		if "sessionId" in cherrypy.request.cookie and self.isAuthorized(cherrypy.request.cookie["sessionId"].value):
			result = {}
			userid = cherrypy.request.cookie["sessionId"].value.split("|")[0]
			json = cherrypy.request.json
			
			for entry in json:
				json[entry] = self.__escapeHTML(json[entry])
			if validateReadAction(json):
				result = self.dbdriver.getUnique(json)
			
			if len(result) == 0:
				return {"message": "noResult"}
			elif type(result) is dict:
				return result
			else:
				return {"message": "insufficientResultByDBDriver"}
		return {"message": "userNotLoggedIn"}
	
	"""
	Client sends a JSON in the following format (example):
		{
		"id": "7da135f7-c4e6-4122-8dfd-14a507b05a09",
		"name": "Brasilian OSM group",
		"channel": "telegram",
		"region": "Latin America",
		"invitelink": "https://t.me/joinchat/FOu7NbaU6EYFzl1L8IsWqp",
		"username": "osmbrazil"
		}
	to change the entry in the database
	"""
	@cherrypy.expose
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out()
	def changeEntry(self):
		"""
		API endpoint to create or change an entry in the database
		"""
		self.__crossOrigin()
		if "sessionId" in cherrypy.request.cookie and self.isAuthorized(cherrypy.request.cookie["sessionId"].value):
			userid = cherrypy.request.cookie["sessionId"].value.split("|")[0]
			json = cherrypy.request.json
			
			for entry in json:
				json[entry] = self.__escapeHTML(json[entry])
			if validateWriteAction(json):
				if self.dbdriver.changeEntry(json):
					return {"message": True}
			return {"message": False}
		return {"message": "userNotLoggedIn"}
	
	"""
	Client sends a JSON in the following format (example):
		{
		"id": "7da135f7-c4e6-4122-8dfd-14a507b05a09",
		"channel": "telegram"
		}
	to remove the entry in the database
	"""
	@cherrypy.expose
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out()
	def removeEntry(self):
		"""
		API endpoint to remove an entry from the database
		"""
		self.__crossOrigin()
		if "sessionId" in cherrypy.request.cookie and self.isAuthorized(cherrypy.request.cookie["sessionId"].value):
			userid = cherrypy.request.cookie["sessionId"].value.split("|")[0]
			json = cherrypy.request.json
			
			for entry in json:
				json[entry] = self.__escapeHTML(json[entry])
			if validateWriteAction(json):
				if self.dbdriver.removeEntry(json):
					return {"message": True}
			return {"message": False}
		return {"message": "userNotLoggedIn"}
	
	"""Client sends a JSON in the following format (example):
		{
		"id": "7da135f7-c4e6-4122-8dfd-14a507b05a09",
		"name": "Brasilian OSM group",
		"channel": "telegram",
		"region": "Latin America",
		"invitelink": "https://t.me/joinchat/FLb5AczL4JXS3t2I7DqVgh",
		"username": "osmbrazil"
		}
	to create the entry in the database"""
	@cherrypy.expose
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out()
	def addEntry(self):
		"""
		API endpoint to create an entry in the database
		"""
		self.__crossOrigin()
		if "sessionId" in cherrypy.request.cookie and self.isAuthorized(cherrypy.request.cookie["sessionId"].value):
			userid = cherrypy.request.cookie["sessionId"].value.split("|")[0]
			json = cherrypy.request.json
			
			for entry in json:
				json[entry] = self.__escapeHTML(json[entry])
			if validateWriteAction(json):
				if self.dbdriver.addEntry(cherrypy.request.json):
					return {"message": True}
			return {"message": False}
		return {"message": "userNotLoggedIn"}
	
	@cherrypy.expose
	@cherrypy.tools.json_out()
	def getTables(self):
		"""
		API endpoint to receive all registered tables of the database
		"""
		self.__crossOrigin()
		if "sessionId" in cherrypy.request.cookie and self.isAuthorized(cherrypy.request.cookie["sessionId"].value):
			return {"message": APIconf["tables"]}
		return {"message": "userNotLoggedIn"}
	
	@cherrypy.expose
	@cherrypy.tools.json_out()
	def meta(self):
		self.__crossOrigin()
		meta = {}
		
		if "sessionId" in cherrypy.request.cookie and self.isAuthorized(cherrypy.request.cookie["sessionId"].value):
			meta["loggedIn"] = True
		else:
			meta["loggedIn"] = False
		
		meta["dbdriver"] = {
		"name": self.dbdriver.name if "name" in dir(self.dbdriver) else None,
		"version": self.dbdriver.version if "version" in dir(self.dbdriver) else None,
		"description": self.dbdriver.description if "description" in dir(self.dbdriver) else None,
		"author": self.dbdriver.author if "author" in dir(self.dbdriver) else None,
		"website": self.dbdriver.website if "website" in dir(self.dbdriver) else None,
		"source": self.dbdriver.source if "source" in dir(self.dbdriver) else None,
		"custom": self.dbdriver.customExpose if "customExpose" in dir(self.dbdriver) else None
		}
		
		for key in _EXPOSE:
			if key in APIconf:
				meta[key] = APIconf[key]
			else:
				meta[key] = None
		
		return meta
	
	def _cp_dispatch(self, vpath):
		if vpath[0] == "login":
			vpath.pop(0)
			cherrypy.request.params["loginProvider"] = vpath.pop(0)
			return self
		if vpath[0] == "callback":
			vpath.pop(0)
			cherrypy.request.params["callbackProvider"] = vpath.pop(0)
			cherrypy.request.params["oauthToken"] = vpath.pop(0)
			cherrypy.request.params["oauthVerifier"] = vpath.pop(0)
			return self
		
def main():
	global APIconf, oauthProviders, atShutdown
	
	print("Loading FedGate configuration...")
	loglevel = "info"
	sfile = open(os.path.join(os.getcwd(), "fedgate.yml"), "r")
	APIconf = yaml.safe_load(sfile)
	sfile.close()
	
	if "loglevel" in APIconf:
		loglevel = APIconf["loglevel"]
	if loglevel == "info":
		logging.basicConfig(format='[FedGate]: %(asctime)s %(message)s', level=logging.INFO, datefmt="%m/%d/%Y %I:%M:%S %p")
	elif loglevel == "debug":
		logging.basicConfig(format='[FedGate]: %(asctime)s %(message)s', level=logging.DEBUG, datefmt="%m/%d/%Y %I:%M:%S %p")
	
	logging.info("Generating secret server key just this instance knows...")
	secretserverkey = os.urandom(16)
	
	logging.info("Loading oauth provider plugins...")
	sys.path.append(os.path.join(os.path.dirname(__file__), "providers", "oauth"))
	for content in os.listdir("providers/oauth"):
		if os.path.isdir(os.path.join("providers", "oauth", content)):
			logging.info("  - " + content)
			oauthProviders[content] = {}
			oauthProviders[content]["plugin"] = importlib.import_module("oauth." + content).provider()
			sfile = open(os.path.join("providers", "oauth", content, "config.yml"), "r")
			oauthProviders[content]["config"] = yaml.safe_load(sfile)
			sfile.close()
	
	logging.info("Starting cherrypy server...")
	cherrypy.quickstart(Fedgate(secretserverkey), "/", "fedgate.cfg")
	
	logging.info("Beginning to shut down FedGate...")
	for func in atShutdown:
		func()
	logging.info("SHUT DOWN MESSAGE\nWas a nice time to serve for you :)\nBye, see you soon!")

if __name__ == "__main__":
	main() 
