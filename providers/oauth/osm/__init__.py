#!/usr/bin/env python3
from requests_oauthlib import OAuth1
import xml.etree.ElementTree as dom
import requests, sys
class provider():
	def getOAuthInstance(self):
		return OAuth1
	def providerName(self):
		return "osm"
	def getUserIdentifier(self, oauthSession, config):
		r = requests.get(url=config["userDetails"], auth=oauthSession)
		userDetails = dom.fromstring(r.text)
		user = userDetails[0].attrib # Returns a XML unluckily, convert it to python3 object and get the attribute of the "user" XML element
		
		return str(user["id"]), str(userDetails[0].find("img").get("href"))
		
