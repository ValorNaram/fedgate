#!/usr/bin/env python3
from urllib.parse import parse_qs
import requests, time, hmac

class verification():
	def isAuthorized(self, token):
		if type(token) is bytes:
			token = token.decode("utf-8")
		clientToken, timestamp, clientHash = token.split("|")
		if hmac.compare_digest(self.generateToken(clientToken + "|" + timestamp), clientHash):
			if time.strptime(timestamp, "%Y/%m/%d/%H/%M") >= time.localtime():
				return True
		return False
	def generateToken(self, msg):
		return hmac.new(self.secretserverkey, bytes(msg, "utf-8"), "sha3_224").hexdigest()
	def getCurTime(self):
		curTime = time.localtime()
		curTime = time.strftime("%Y/%m/%d/%H/%M", curTime).split("/")
		return [int(curTime[0]), int(curTime[1]), int(curTime[2]), int(curTime[3]), int(curTime[4])]
	def createExpireTime(self):
		curTime = self.getCurTime()
		curTime[3] += 1
		for i in range(0, len(curTime)):
			curTime[i] = str(curTime[i])
		return curTime
	def oauthCallback(self, OAuth, accessTokenURL, client_key, client_secret, oauthToken, oauthVerifier):
		if oauthVerifier == "":
			oauthSession = OAuth(client_key, client_secret=client_secret, resource_owner_key=oauthToken, resource_owner_secret=self.resourceOwners[oauthToken], signature_type="auth_header") #3
		else:
			oauthSession = OAuth(client_key, client_secret=client_secret, resource_owner_key=oauthToken, verifier=oauthVerifier, resource_owner_secret=self.resourceOwners[oauthToken], signature_type="auth_header") #3
		r = requests.post(url=accessTokenURL, auth=oauthSession)
		creds = parse_qs(r.text)
		access_key = creds.get("oauth_token")
		access_secret = creds.get("oauth_token_secret")
		
		return OAuth(client_key, client_secret=client_secret, resource_owner_key=access_key[0], resource_owner_secret=access_secret[0], signature_type="auth_header")
	
	def oauthLogin(self, OAuth, requestTokenURL, client_key, client_secret): #0
		oauthSession = OAuth(client_key, client_secret=client_secret, signature_type="auth_header") #1
		r = requests.post(url=requestTokenURL, auth=oauthSession)
		creds = parse_qs(r.text)
		user_key = creds.get("oauth_token")
		user_secret = creds.get("oauth_token_secret")
		if not "resourceOwners" in dir(self):
			self.resourceOwners = {}
		self.resourceOwners[str(user_key[0])] = str(user_secret[0])
		
		return str(user_key[0])
