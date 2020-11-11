#!/usr/bin/env python3
import importlib, logging, os

class Driver():
	def __printError(self):
		logging.error("FATAL ERROR: database driver '{}' couldn't be found and therefore hasn't been imported".format(self.conf["dbdriver"]))
	
	def __init__(self, conf):
		self.conf = conf
		
		logging.info("loading '{}' database driver...".format(conf["dbdriver"]))
		if os.path.exists(os.path.join("drivers", conf["dbdriver"])):
			mod = importlib.import_module("drivers." + conf["dbdriver"])
			self = mod.Driver(conf)
		else:
			self.__printError()
			
			self.name = "dbdriver loader for FedGate"
			self.version = "1.0"
			self.description = "dbdriver loader for FedGate. If you see this message, then dbdriver loader couldn't find the requested driver '{}' on the server and therefore couldn't load it. Without the driver this FedGate instance will not work and will return bunch of error codes. The driver is needed for fetching/modifying/removing data".format(conf["dbdriver"])
			self.author = "Sören Reinecke alias Valor Naram"
	
	def getEntries(json):
		self.__printError()
		return {}
	
	def getEntriesDistinct(json):
		self.__printError()
		return {}
	
	def changeEntry(json):
		self.__printError()
		return False
	
	def addEntry(json):
		self.__printError()
		return False
	
	def removeEntry(json):
		self.__printError()
		return False
