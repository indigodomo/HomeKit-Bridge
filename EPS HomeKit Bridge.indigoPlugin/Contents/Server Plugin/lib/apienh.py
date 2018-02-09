#! /usr/bin/env python
# -*- coding: utf-8 -*-


# apienh - Enhanced Indigo RESTful API
#
# Copyright (c) 2018 ColoradoFourWheeler / EPS
#

import indigo
import linecache # exception reporting
import sys # exception reporting
import logging # logging
import ext

import urllib
import json

class api:	
	#
	# Initialize the  class
	#
	def __init__(self, factory):
		self.logger = logging.getLogger ("Plugin.api")
		self.factory = factory
		self.stopped = False
	
	#
	# Stop listening for http requests on the http server in factory
	#	
	def stopServer (self):
		try:
			if self.stopped: return
			
			self.factory.http.stop ()
			self.stopped = True
			
		except Exception as e:
			self.logger.error (ext.getException(e))
	
	#
	# Start listening for http requests on the http server in factory
	#	
	def startServer (self, port, username = None, password = None):
		try:
			#self.factory.http.startServer (port, username, password)			
			self.factory.http.run (port, username, password)			
		
		except Exception as e:
			self.logger.error (ext.getException(e))		


	#
	# HTTP GET request
	#
	def onReceivedHTTPGETRequest (self, request, query):
		try:
			self.logger.threaddebug ("HTTP GET request received by API processor")
			
			if request.path == "/devices.json":
				return self._deviceList_JSON (query)

			if "/devices/" in request.path:
				# They are looking for device info
				path = request.path.split("/")
				devStr = path[len(path) - 1]
				
				try:
					if "." in devStr: 
						devId = int(devStr.split(".")[0])
					else:
						devId = int(devStr)
						
					if devId in indigo.devices:
						return self._deviceDetails_JSON (devId, query)
						
				except Exception as ex:
					# Something is wrong or invalid
					self.logger.error (ext.getException(ex))		
					pass
			

			# If we can't figure it out
			self.logger.error ("Unable to decyper HTTP request '{}' and query '{}'".format(unicode(request), unicode(query)))
			content = ""
			content += "<html>\n<head><title>C4W EPS Web</title></head>\n<body>"
			content += "\n<p>API Request Unknown</p>"
			content += "\n</body>\n</html>\n"
			
			return "text/html", content
			
		except Exception as e:
			self.logger.error (ext.getException(e))		
			
	#
	# Convert non JSON serializable Indigo types to standard Py types
	#
	def convertIndigoType (self, obj):
		try:
			newObj = None
			
			if type(obj) is indigo.Dict:
				newObj = {}
				for key, value in obj.iteritems():
					newObj[key] = self.convertIndigoType (value) # Loop
					
			elif type(obj) is indigo.List:
				newObj = []
				for value in obj:
					newObj.append(self.convertIndigoType (value)) # Loop		
					
			else:
				return obj
					
			return newObj
		
		except Exception as e:
			self.logger.error (ext.getException(e))		
			
	#
	# Return legacy JSON list of specific device
	#
	def _deviceDetails_JSON (self, devId, query):
		try:
			dev = indigo.devices[devId]
			
			props = [a for a in dir(dev) if not a.startswith('__') and not callable(getattr(dev, a))]
			
			ret = {}
			for p in props:
				if p == "globalProps": continue # can't use this and its a dupe anyway
				if p == "ownerProps": continue 
				if p == "pluginProps": continue 
				if p == "states": continue 
				
				ret[p] = self.convertIndigoType (getattr(dev, p))
									
				if str(type(ret[p])) == "<type 'datetime.datetime'>":
					ret[p] = unicode(ret[p])
					
				#indigo.server.log(str(type(ret[p])))
			
			# Try to determine what kind of device we have here
			ret["deviceType"] = "custom"
			
			# Relay
			if "onOffState" in dev.states and "brightnessLevel" not in dev.states:
				ret["deviceType"] = "relay"
				if "supportsRGB" in dir(dev): ret["deviceType"] = "rgb-relay"
				
			elif "onOffState" in dev.states and "brightnessLevel" in dev.states:
				ret["deviceType"] = "dimmer"
				if "supportsRGB" in dir(dev): ret["deviceType"] = "rgb-dimmer"
			
				
			
			if "showstates" in query:
				if query["showstates"][0] == "true":	
					states = {}
					for key, value in dev.states.iteritems():
						states[key] = self.convertIndigoType (value)
				
					ret["states"] = states
						
			if "showprops" in query:
				if query["showprops"][0] == "true":	
					ownerprops = {}
					for key, value in dev.ownerProps.iteritems():
						ownerprops[key] = self.convertIndigoType (value)
				
					ret["ownerProps"] = ownerprops			
				
			if "css" in query:
				if query["css"][0] == "true":
					return "text/css",	json.dumps(ret, indent=4)
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return "application/json", json.dumps(ret)
			
	#
	# Return legacy JSON list of all devices
	#
	def _deviceList_JSON (self, query):
		try:
			self.logger.info ("HTTP returning JSON device list")
			
			content = "" # In case we're returning something other than straight JSON
			
			ret = []
			
			for d in indigo.devices:
				dev = {}
				
				dev["restParent"] = "devices"
				dev["restURL"] = "/devices/" + urllib.quote(d.name) + ".json"
				dev["restURLEx"] = "/devices/" + str(d.id) + ".json"
				dev["nameURLEncoded"] = urllib.quote(d.name)
				dev["name"] = d.name
				
				ret.append (dev)
				
			if "css" in query:
				if query["css"][0] == "true":
					return "text/css",	json.dumps(ret, indent=4)
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return "application/json", json.dumps(ret)
		