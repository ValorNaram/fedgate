#!/usr/bin/env python3
import importlib, logging, os, sys

class FakeDriver():
	def __printError(self):
		logging.error("FATAL ERROR: database driver '{}' couldn't be found in '{}' and therefore hasn't been imported".format(self.dbdriver, os.path.join(os.getcwd(), "providers", "dbdrivers", self.dbdriver)))
	
	def __init__(self, conf):
		self.dbdriver = conf["dbdriver"]
		self.__printError()
		self.name = "FakeDriver for FedGate"
		self.version = "1.0"
		self.description = "FakeDriver for FedGate. If you see this message, then dbdriver loader couldn't find the requested driver '{}' on the server and therefore couldn't load it. Without the driver this FedGate instance will not work and will return bunch of error codes. The driver is needed for fetching/modifying/removing data".format(conf["dbdriver"])
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

class Loader():
	def __init__(self, conf):
		logging.info("loading '{}' database driver...".format(conf["dbdriver"]))
		if os.path.exists(os.path.join(os.getcwd(), "providers", "dbdrivers", conf["dbdriver"])):
			sys.path.append(os.path.join(os.getcwd(), "providers", "dbdrivers"))
			mod = importlib.import_module(conf["dbdriver"])
			self.driver = mod.Driver(conf)
		else:
			self.driver = FakeDriver(conf)
