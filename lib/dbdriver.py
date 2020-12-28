#!/usr/bin/env python3
import importlib, logging, os, sys

class Driver():
	def __printError(self):
		logging.error("FATAL ERROR: database driver '{}' couldn't be found in '{}' and therefore hasn't been imported".format(self.conf["dbdriver"], os.path.join(os.path.dirname(__file__), "drivers", self.conf["dbdriver"] + ".py")))
	
	def __init__(self, conf):
		self.conf = conf
		
		logging.info("loading '{}' database driver...".format(conf["dbdriver"]))
		if os.path.exists(os.path.join(os.path.dirname(__file__), "drivers", conf["dbdriver"] + ".py")):
			sys.path.append(os.path.dirname(__file__))
			mod = importlib.import_module("drivers." + conf["dbdriver"])
			self.driver = mod.Driver(conf)
		else:
			self.__printError()
			
			self.name = "dbdriver loader for FedGate"
			self.version = "1.0"
			self.description = "dbdriver loader for FedGate. If you see this message, then dbdriver loader couldn't find the requested driver '{}' on the server and therefore couldn't load it. Without the driver this FedGate instance will not work and will return bunch of error codes. The driver is needed for fetching/modifying/removing data".format(conf["dbdriver"])
			self.author = "Sören Reinecke alias Valor Naram"
	
	def getEntries(self, json):
		self.__printError()
		return {}
	
	def getEntriesDistinct(self, json):
		self.__printError()
		return {}
	
	def getUnique(self, json):
		self.__printError()
		return {}
	
	def changeEntry(self, json):
		self.__printError()
		return False
	
	def addEntry(self, json):
		self.__printError()
		return False
	
	def removeEntry(self, json):
		self.__printError()
		return False
	
	def exit(self):
		self.__printError()
		return True
