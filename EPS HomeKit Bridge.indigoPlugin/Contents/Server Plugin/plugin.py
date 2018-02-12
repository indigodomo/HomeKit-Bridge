#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Core libraries
import indigo
import os
import sys
import time
import datetime

# EPS 3.0 Libraries
import logging
from lib.eps import eps
from lib import ext
from lib import dtutil
from lib import iutil

#from lib import hkapi

# Plugin libraries
import json # for encoding server devices/actions
from os.path import expanduser # getting ~ user from shell
import shutil # shell level utilities for dealing with our local HB server, mostly removing non empty folders
import socket # port checking
import requests # for sending forced updates to HB-Indigo (POST JSON)
import math # for server wizard
import collections # dict sorting for server wizard
import thread # homebridge callbacks on actions

#from lib.httpsvr import httpServer
#hserver = httpServer(None)
#from lib import httpsvr

eps = eps(None)

################################################################################
# plugin - 	Basically serves as a shell for the main plugin functions, it passes
# 			all Indigo commands to the core engine to do the "standard" operations
#			and raises onBefore_ and onAfter_ if it wants to do something 
#			interesting with it.  The meat of the plugin is in here while the
#			EPS library handles the day-to-day and common operations.
################################################################################
class Plugin(indigo.PluginBase):

	# Define the plugin-specific things our engine needs to know
	TVERSION	= "3.3.1"
	PLUGIN_LIBS = ["api", "actions3", "homekit"] #["cache", "plugcache", "irr"]
	UPDATE_URL 	= ""
	
	SERVERS = []			# All servers
	SERVER_ALIAS = {}	 	# Included device aliases and their server as SERVER_ALIAS[aliasName] = serverId (helps prevent duplicate alias names)
	SERVER_ID = {}			# Included device ID's and their server as SERVER_ID[devId] = {serverId dict} (for http service)
	SERVER_STARTING = []	# List of servers that are pending a start, lets us know to check this in concurrent threads
	
	CTICKS = 0				# Number of concurrent thread ticks since last reset
	STICKS = 0				# Number of concurrent thread server start ticks since last reset
	
	# For shell commands
	PLUGINDIR = os.getcwd()
	HBDIR = PLUGINDIR + "/bin/hb/homebridge"
	#CONFIGDIR = expanduser("~") + "/.HomeKit-Bridge"
	CONFIGDIR = "" # Expanded in startup
	
	#
	# Init
	#
	def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
		indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
		
		eps.__init__ (self)
		eps.loadLibs (self.PLUGIN_LIBS)
		
		# Create JSON stash record for server devices
		self.setupJstash ()
		self.catalogServerDevices()
								
	################################################################################
	# PLUGIN HANDLERS
	#
	# Raised onBefore_ and onAfter_ for interesting Indigo or custom commands that 
	# we want to intercept and do something with
	################################################################################	
	
	
	#
	# This only gets run manually in code when new devices are added to facilitate the lookup needed for classes
	#
	def printClassLookupDict (self):
		try:
			d = "{"
			
			for name in dir(eps.homekit):
				if "characteristic_" in name:
					d += '"' + name.replace("characteristic_", "") + '": ' + name + ", "

			d += "}"
								
			indigo.server.log(unicode(d))
					
		except Exception as e:
			self.logger.error (ext.getException(e))				
	
	#
	# Development Testing
	#
	def devTest (self):
		try:
			self.logger.warning ("DEVELOPMENT TEST FUNCTION ACTIVE")
			
			#eps.api.startServer (self.pluginPrefs.get('apiport', '8558'))
			#eps.api.stopServer ()
			#eps.api.run (self.pluginPrefs.get('apiport', '8558'))
			
			#x = eps.homekit.getServiceObject (141323225, "service_Fanv2")
			#indigo.server.log (unicode(x))
			
			#x = eps.homekit.getServiceObject (361446525, "service_GarageDoorOpener")
			#indigo.server.log (unicode(x))
			
			#x = eps.homekit.getServiceObject (182494986, "service_Lightbulb")
			#indigo.server.log (unicode(x))
			
			#x = eps.homekit.getServiceObject (762522700, "service_MotionSensor")
			#indigo.server.log (unicode(x))
			
			#x = eps.homekit.getServiceObject (145155245, "service_Outlet")
			#indigo.server.log (unicode(x))
			
			#x = eps.homekit.getServiceObject (174276019, "service_LockMechanism")
			#indigo.server.log (unicode(x))
			
			#x = eps.homekit.getServiceObject (1010303036, "service_Switch")
			#indigo.server.log (unicode(x))
			
			x = eps.homekit.getServiceObject (954521198, 0, "service_Thermostat")
			indigo.server.log (unicode(x))
			
			#x = eps.homekit.getHomeKitServices ()
			#indigo.server.log (unicode(x))
			
			
			pass
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
	
	#
	# Plugin startup
	#
	def onAfter_startup (self):
		try:
			# Only uncomment this when new characteristics have been added so the class lookup can be printed
			#self.printClassLookupDict()
			
			# Start the httpd listener
			eps.api.startServer (self.pluginPrefs.get('apiport', '8558'))
			
			# Set up the config path in the Indigo preferences folder
			self.CONFIGDIR = '{}/Preferences/Plugins/{}'.format(indigo.server.getInstallFolderPath(), self.pluginId)
			self.logger.debug ("Config path set to {}".format(self.CONFIGDIR))
			
			# Subscribe to changes so we can send update requests to Homebridge
			eps.plug.subscribeChanges (["devices", "actionGroups"])
			
			# Check that we have a server set up
			for dev in indigo.devices.iter(self.pluginId + ".Server"):
				self.checkserverFoldersAndStartIfConfigured (dev)
					
			#indigo.server.log(unicode(self.SERVER_ID))	
				
			#xdev = hkapi.service_LightBulb (624004987)
			#indigo.server.log(unicode(xdev))
			
			#x = eps.plugdetails.getFieldUIList (indigo.devices[70743945])
			#indigo.server.log(unicode(x))
			
			#indigo.server.log(unicode(eps.plugdetails.pluginCache))
			
			#self.devTest()
			
			self.serverListHomeKitDeviceTypes (None, None)
				
			if len(self.SERVERS) == 0:
				self.logger.info ("No servers detected, creating your first HomeKit server (NOT YET IMPLEMENTED)")
				
			
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
	#
	# Plugin shutdown
	#
	def onAfter_shutdown (self):		
		try:
			# Shut down ALL servers if they are running (since the API doesn't work when the plugin is not running anyway)
			for dev in indigo.devices.iter(self.pluginId + ".Server"):
				if dev.states["onOffState"]: self.shellHBStopServer (dev)
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
	#
	# Concurrent thread
	#
	def onAfter_runConcurrentThread (self):
		#hserver.runConcurrentThread()		
		self.CTICKS = self.CTICKS + 1
		if len(self.SERVER_STARTING) > 0: self.STICKS = self.STICKS + 1
		
		# If we have servers starting then check every tick until the 30 mark
		if len(self.SERVER_STARTING) > 0:
			try:
				for devId in self.SERVER_STARTING:
					if self.checkRunningHBServer (indigo.devices[devId]):
						self.logger.info ("Server '{}' has successfully started and can answer Siri commands".format(indigo.devices[devId].name))
					
						# Remove this from the list so we don't check anymore
						newList = []
						for d in self.SERVER_STARTING:
							if d == devId: continue
							newList.append (d)
						
						self.SERVER_STARTING = newList
					
				if len(self.SERVER_STARTING) > 0 and self.STICKS > 30:
					for devId in self.SERVER_STARTING:
						self.logger.info ("Server '{}' has not responded to a start request after more than 30 seconds, forcing an abort on the startup".format(indigo.devices[devId].name))
						self.shellHBStopServer (indigo.devices[devId])
						
					self.STICKS = 0
					
			except Exception as e:
				self.logger.error (ext.getException(e))		
		
		# At 30 ticks we check server running state (more or less between 30 seconds and a minute but keeps us from having to do date calcs here which use CPU)
		if self.CTICKS == 30:
			try:
				self.logger.debug ("Checking running state of all servers")
				for dev in indigo.devices.iter(self.pluginId + ".Server"):
					self.checkRunningHBServer (dev)
			
				self.CTICKS = 0
				
			except Exception as e:
				self.logger.error (ext.getException(e))		
			
	#
	# A form field changed, update defaults
	#
	def onAfter_formFieldChanged (self, valuesDict, typeId, devId):
		try:	
			if typeId == "Server": 
				return self.serverFormFieldChanged (valuesDict, typeId, devId)
			
		except Exception as e:
			self.logger.error (ext.getException(e))		
			
	#
	# Device configuration validation
	#
	def onAfter_validateDeviceConfigUi(self, valuesDict, typeId, devId):
		try:
			if typeId == "Server": 
				return self.serverFormConfigValidation (valuesDict, typeId, devId)
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
	#
	# Plugin device updated
	#
	def onAfter_pluginDevicePropChanged (self, origDev, newDev, changedProps):
		try:
			if newDev.deviceTypeId == "Server": 
				self.serverPropChanged (origDev, newDev, changedProps)
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
	#
	# Plugin device updated
	#
	def onAfter_pluginDeviceAttribChanged (self, origDev, newDev, changedProps):
		try:
			if newDev.deviceTypeId == "Server": 
				self.serverAttribChanged (origDev, newDev, changedProps)
		
		except Exception as e:
			self.logger.error (ext.getException(e))			
			
	#
	# Device ON received
	#
	def onDeviceCommandTurnOn (self, dev):
		try:
			if dev.deviceTypeId == "Server": 
				return self.serverCommandTurnOn (dev)
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
	#
	# Device OFF received
	#
	def onDeviceCommandTurnOff (self, dev):
		try:
			if dev.deviceTypeId == "Server": 
				return self.serverCommandTurnOff (dev)
		
		except Exception as e:
			self.logger.error (ext.getException(e))		
			
	#
	# Device update
	#
	def onAfter_nonpluginDeviceUpdated (self, origDev, newDev):
		try:
			#indigo.server.log (newDev.name)
			if newDev.id in self.SERVER_ID:
				devId = newDev.id
				for serverId in self.SERVER_ID[devId]:
					valuesDict = self.serverCheckForJSONKeys (indigo.devices[serverId].pluginProps)	
					includedDevices = json.loads(valuesDict["includedDevices"])
					includedActions = json.loads(valuesDict["includedActions"])
					
					r = eps.jstash.getRecordWithFieldEquals (includedDevices, "id", devId)
					if r is None: r = eps.jstash.getRecordWithFieldEquals (includedActions, "id", devId)
					if r is None: continue
					
					#hk = getattr (hkapi, r["hktype"]) # Find the class matching the selection
					#obj = hk (int(r["id"]), {}, [], True)
					obj = eps.homekit.getServiceObject (r["id"], serverId, r["hktype"], False, True)
			
					updateRequired = False		
					for a in obj.actions:
						if devId in a.monitors: # This device is being monitored (generally it is)
							for deviceId, monitor in a.monitors.iteritems(): # Iter all monitors
								if deviceId == devId: # If the monitor is for this device
									if monitor[0:5] == "attr_": # If it is an attribute
										action = monitor.replace("attr_", "")
										if action in dir(newDev) and action in dir(origDev):
											n = getattr (newDev, action)
											o = getattr (origDev, action)
											
											if n != o:
												updateRequired = True
												break # We don't need to check anything else, if one thing needs an update then we need an update
												
					if updateRequired:
						self.serverSendObjectUpdateToHomebridge (indigo.devices[serverId], newDev.id)
					
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
			
	#
	# Plugin device created
	#
	def onAfter_pluginDeviceCreated (self, dev):
		try:
			if dev.deviceTypeId == "Server": 
				self.checkserverFoldersAndStartIfConfigured (dev)
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
	#
	# Plugin device deleted
	#
	def onAfter_pluginDeviceDeleted (self, dev):
		try:
			if dev.deviceTypeId == "Server": 
				# Stop it if it's running
				if self.checkRunningHBServer (dev, True):
					if self.shellHBStopServer (dev, True):
						pass
					else:
						self.logger.error ("Unable to stop '{}' before it was deleted, you may need to restart your Mac to make sure it isn't running any longer".format(dev.name))
						
				# Remove the folder structure
				import shutil
				shutil.rmtree(self.CONFIGDIR + "/" + str(dev.id))
				
				# Remove from cache
				newservers = []
				for s in self.SERVERS:
					if s != dev.id: newservers.append(s)
					
				self.SERVERS = newservers
				
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
	#
	# Plugin prefs were closed
	#
	def onAfter_closedPrefsConfigUi(self, valuesDict, userCancelled):
		try:
			pass
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
		
	################################################################################
	# PLUGIN SPECIFIC ROUTINES
	#
	# Routines not raised by plug events that are specific to this plugin
	################################################################################	
		
	################################################################################
	# HTTP Methods
	################################################################################
	
	#
	# HTTP GET request
	#
	def onBefore_onReceivedHTTPGETRequest (self, request, query):	
		try:
			#indigo.server.log("HTTP query to plugin")
			#indigo.server.log(unicode(request))
			#indigo.server.log(unicode(query))
			
			if "/HomeKit" in request.path:
				if "cmd" in query and query["cmd"][0] == "setCharacteristic":
					if "objId" in query:
						devId = int(query["objId"][0])
						
					if "serverId" in query:
						serverId = int(query["serverId"][0])
						
					# Load up the HK and server objects
					valuesDict = self.serverCheckForJSONKeys (indigo.devices[serverId].pluginProps)	
					includedDevices = json.loads(valuesDict["includedDevices"])
					includedActions = json.loads(valuesDict["includedActions"])
					
					isAction = False
					r = eps.jstash.getRecordWithFieldEquals (includedDevices, "id", devId)
					if r is None: 
						r = eps.jstash.getRecordWithFieldEquals (includedActions, "id", devId)
						isAction = True
					
					obj = eps.homekit.getServiceObject (r["id"], serverId, r["hktype"], False,  True)
					
					# Loop through actions to see if any of them are in the query
					processedActions = {}
					response = False
					
					for a in obj.actions:
						#indigo.server.log(unicode(a))
						if a.characteristic in query and a.characteristic not in processedActions: 
							self.logger.debug ("Received {} in query, setting to {}".format(a.characteristic, query[a.characteristic][0]))
							#processedActions.append(a.characteristic)
							ret = a.run (query[a.characteristic][0])
							#self.HKREQUESTQUEUE[obj.id] = a.characteristic # It's ok that this overwrites, it's the same
							if ret: response = True # Only change it if its true, that way we know the operation was a success
					
					# Loop for up to 30 seconds (this is in a thread so it won't hurt the plugin or other requests) to wait for
					# the given command to be completed
					if not isAction:
						commandComplete = False
						commandLoop = 0
						while not commandComplete:
							commandLoop = commandLoop + 1
							if commandLoop > 1000: 
								self.logger.error ("Attempting to control '{}' from HomeKit and have not gotten a response from the Indigo device for at least 10 seconds, aborting command".format(r["name"]))
								break # Failsafe

							d = dtutil.dateDiff ("seconds", indigo.server.getTime(), indigo.devices[int(r["id"])].lastChanged)
							if d == 0 or d == 1 or d == 2: 
								break # We got there, this is perfect timing
							elif d < 6:
								# A bit slow, log it
								self.logger.warning ("Attempting to control '{}' from HomeKit and we didn't get notified for {} seconds after the action was run, this is a bit slow".format(r["name"], unicode(d)))
								break
								
						time.sleep (1) # For good measure
							
					else:
						#time.sleep (2) # Give it time to run
						pass # Let it instant-report success 
					
					r = self.buildHKAPIDetails (devId, serverId, isAction)		
					return "text/css",	json.dumps(r, indent=4)
				
				if "cmd" in query and query["cmd"][0] == "getInfo":
					if "objId" in query:
						devId = int(query["objId"][0])
			
						serverId = 0
						#if devId in self.SERVER_ID: 
						#	if len(self.SERVER_ID[devId]) == 1: serverId = self.SERVER_ID[devId][0]
						if "serverId" in query:
							server = indigo.devices[int(query["serverId"][0])]
							serverId = server.id
						
						if serverId == 0:
							msg = {}
							msg["result"] = "fail"
							msg["message"] = "Server ID was not passed to query, unable to process"
							return "text/css",	json.dumps(msg, indent=4)
						
						r = self.buildHKAPIDetails (devId, serverId)
						return "text/css",	json.dumps(r, indent=4)
						
				if "cmd" in query and query["cmd"][0] == "deviceList":
					if "serverId" in query:
						server = indigo.devices[int(query["serverId"][0])]
						serverId = server.id
						
						# Load up the HK and server objects
						valuesDict = self.serverCheckForJSONKeys (indigo.devices[serverId].pluginProps)	
						includedDevices = json.loads(valuesDict["includedDevices"])
						includedActions = json.loads(valuesDict["includedActions"])
						
						ret = []
						for d in includedDevices:
							r = self.buildHKAPIDetails (d["id"], serverId)
							if r is not None and len(r) > 0: ret.append (r)
							
						for a in includedActions:
							r = self.buildHKAPIDetails (a["id"], serverId)
							if r is not None and len(r) > 0: ret.append (r)	
						
						return "text/css",	json.dumps(ret, indent=4)
						
			
			msg = {}
			msg["result"] = "fail"
			msg["message"] = "Unknown query or invalid parameters, nothing to do"
			return "text/css",	json.dumps(msg, indent=4)
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
			msg = {}
			msg["result"] = "fail"
			msg["message"] = "A fatal exception was encountered while processing your request, check the Indigo log for details"
			return "text/css",	json.dumps(msg, indent=4)
			
	#
	# Build HK API details for object ID
	#
	def buildHKAPIDetails (self, objId, serverId, runningAction = False):
		try:
			valuesDict = self.serverCheckForJSONKeys (indigo.devices[serverId].pluginProps)	
			includedDevices = json.loads(valuesDict["includedDevices"])
			includedActions = json.loads(valuesDict["includedActions"])
			
			r = eps.jstash.getRecordWithFieldEquals (includedDevices, "id", objId)
			if r is None: r = eps.jstash.getRecordWithFieldEquals (includedActions, "id", objId)
			
			# Create an HK object so we can get all default data
			self.logger.threaddebug ("Looking for HomeKit class {}".format(r["hktype"]))
			services = eps.homekit.getHomeKitServices()
			if r["hktype"] not in services:
				self.logger.error ("Server '{}' device '{}' is trying to reference a HomeKit class of {} that isn't defined.".format(indigo.devices[serverId].name, r["alias"], r["hktype"]))
				return []
			
			obj = eps.homekit.getServiceObject (r["id"], serverId, r["hktype"], False, True)
			#indigo.server.log(unicode(obj))
			
			# Fix up for output
			r["hkservice"] = r["hktype"].replace("service_", "")
			del r["hktype"]
			del r["jkey"]
			del r["type"]
			del r["char"]
			
			# Add the callback
			r["url"] = "/HomeKit?objId={}&serverId={}".format(str(objId), str(serverId))	
			
			# Fix characteristics for readability
			charList = []
			for charName, charValue in obj.characterDict.iteritems():
				charItem = {}
				characteristic = getattr (obj, charName)
				charItem["name"] = charName
				charItem["value"] = charValue
				
				if runningAction and charItem["name"] == "On": charItem["value"] = True
				
				charItem["readonly"] = characteristic.readonly
				charItem["notify"] = characteristic.notify
				charList.append (charItem)
				
			r["hkcharacteristics"] = charList
			
			# Fix actions for readability
			actList = []
			for a in obj.actions:
				if not a.characteristic in actList: actList.append(a.characteristic)
				
			r["action"] = actList
			
			# This will only come up if an action group was turned on and then called down to here so this should be safe, but we need to now
			# notify Homebridge that the action has completed and to get the false value
			if runningAction:
				#self.serverSendObjectUpdateToHomebridge (indigo.devices[int(serverId)], r["id"])
				thread.start_new_thread(self.timedCallbackToURL, (serverId, r["id"], 2))
			
			return r
		
		except Exception as e:
			self.logger.error (ext.getException(e))			
			
		return []
		
	#
	# Run in a thread, this will run the URL in the specified seconds
	#
	def timedCallbackToURL (self, serverId, devId, waitSeconds):
		try:
			if waitSeconds > 0: time.sleep(waitSeconds)
			self.serverSendObjectUpdateToHomebridge (indigo.devices[int(serverId)], devId)
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
	
	################################################################################
	# GENERAL METHODS
	################################################################################
	
	
	#
	# Find an available Homebridge username starting from the default
	#
	def getNextAvailableUsername (self, devId, suppressLogging = False):
		try:
			# Each failure will do a continue, if we get to the bottom them it is unique
			for i in range (10, 100):
				username = "CC:22:3D:E3:CE:{}".format(str(i))
				
				# Check our own servers to make sure we aren't going to use this port elsewhere
				for dev in indigo.devices.iter(self.pluginId + ".Server"):
					if dev.id == devId:
						# If we passed a devId then ignore it, we don't want to check against the server calling this function
						continue
					
					if "username" in dev.ownerProps and dev.ownerProps["username"] == username:
						continue
						
				# So far, so good, now lets check Homebridge Buddy Legacy servers to see if one is wanting to use this port and just isn't running
				for dev in indigo.devices.iter("com.eps.indigoplugin.homebridge.Homebridge-Server"):
					if "hbuser" in dev.ownerProps and dev.ownerProps["hbuser"] == username:
						continue
						
				for dev in indigo.devices.iter("com.eps.indigoplugin.homebridge.Homebridge-Guest"):
					if "hbuser" in dev.ownerProps and dev.ownerProps["hbuser"] == username:
						continue		
						
				for dev in indigo.devices.iter("com.eps.indigoplugin.homebridge.Homebridge-Custom"):
					if "hbuser" in dev.ownerProps and dev.ownerProps["hbuser"] == username:
						continue
						
				# If we get here then it must be unique
				return username

		
		except Exception as e:
			self.logger.error (ext.getException(e))	
	
	#
	# Find an available port, starting from the provided number
	#
	def getNextAvailablePort (self, startPort, devId = 0, suppressLogging = False):
		try:
			for port in range (startPort, startPort + 100):
				#indigo.server.log(str(port))
				if self.portIsOpen (port, devId, suppressLogging): return port		
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return 0
	
	#
	# Catalog the devices for each server into our globals
	#
	def catalogServerDevices (self, serverId = 0):
		try:
			if serverId == 0:
				for dev in indigo.devices.iter(self.pluginId + ".Server"):
					self._catalogServerDevices (dev)
					
			else:
				dev = indigo.devices[serverId]
				self._catalogServerDevices (dev)
				
			#indigo.server.log(unicode(self.SERVER_ALIAS))
			#indigo.server.log(unicode(self.SERVER_ID))
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
	#
	# Callback for catalog server devices
	#
	def _catalogServerDevices (self, dev):
		try:
			valuesDict = self.serverCheckForJSONKeys (dev.pluginProps)	
			includedDevices = json.loads(valuesDict["includedDevices"])
			includedActions = json.loads(valuesDict["includedActions"])
			
			self.SERVERS.append(dev.id)
			
			for d in includedDevices:
				self.SERVER_ALIAS[d["alias"]] = dev.id
				
				if d["id"] not in self.SERVER_ID:
					self.SERVER_ID[d["id"]] = [dev.id]
				else:
					servers = self.SERVER_ID[d["id"]]
					if dev.id not in servers: # Only add it if it's not already there
						servers.append(dev.id)
						self.SERVER_ID[d["id"]] = servers
						
			for d in includedActions:
				self.SERVER_ALIAS[d["alias"]] = dev.id
				
				if d["id"] not in self.SERVER_ID:
					self.SERVER_ID[d["id"]] = [dev.id]
				else:
					servers = self.SERVER_ID[d["id"]]
					if dev.id not in servers: # Only add it if it's not already there
						servers.append(dev.id)
						self.SERVER_ID[d["id"]] = servers			
				
		except Exception as e:
			self.logger.error (ext.getException(e))	
	
	#
	# See if a port connection can be made - used to test if HB is running for a specific server
	#
	def checkRunningHBServer (self, dev, noStatus = False):
		try:
			if dev.pluginProps["port"] == "": return False
			port = int(dev.pluginProps["port"])
			
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			result = sock.connect_ex(("127.0.0.1", int(port)))
			
			# If we are deleting and go past here we'll get errors and then never stop the running server
			if result == 0 and noStatus: return True
			if result != 0 and noStatus: return False
			
			# We can still get here on a delete, if the device is missing just return
			if dev.id not in indigo.devices: return
			
			if result == 0:
				indigo.devices[dev.id].updateStateOnServer("onOffState", True, uiValue="Running")
				indigo.devices[dev.id].updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
				return True
			else:
				if dev.id in self.SERVER_STARTING:
					indigo.devices[dev.id].updateStateOnServer("onOffState", False, uiValue="Starting")
					indigo.devices[dev.id].updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
					return False
				
				else:
					indigo.devices[dev.id].updateStateOnServer("onOffState", False, uiValue="Stopped")
					indigo.devices[dev.id].updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
					return False
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return False
		
	#
	# Health check, folder creation, caching and server startup for new devices or when plugin starts
	#
	def checkserverFoldersAndStartIfConfigured (self, dev):
		try:
			if dev.deviceTypeId == "Server": 
				self.SERVERS.append (dev.id)
				
				# Just for now
				self.checkRunningHBServer (dev)
				
				# Test shell scripts
				self.shellCreateServerConfigFolders (dev)
				
				# Since the config file is easily and quickly built, save it on startup
				self.saveConfigurationToDisk (dev)
				
				# If it's enabled then start the server
				if "autoStartStop" in dev.pluginProps and dev.pluginProps["autoStartStop"]:
					self.shellHBStartServer (dev)
		
		except Exception as e:
			self.logger.error (ext.getException(e))		
			
			
	#
	# Check if a port is in use
	#
	def portIsOpen (self, port, devId = 0, suppressLogging = False):
		try:
			ret = True
			
			self.logger.threaddebug ("Verifying that {0} is available".format(port))
			
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

			try:
				s.bind(("127.0.0.1", int(port) ))
				
			except socket.error as e:
				ret = False
				
				if e.errno == 98:
					self.logger.threaddebug ("Port is already in use")
					
				elif e.errno == 48:
					self.logger.threaddebug ("Port is already in use!")
					
				else:
					# something else raised the socket.error exception
					self.logger.threaddebug (unicode(e))
					
			s.close()	
			
			# If the port isn't open at this point then bounce back
			if not ret: return ret
			
			# Check our own servers to make sure we aren't going to use this port elsewhere
			for dev in indigo.devices.iter(self.pluginId + ".Server"):
				if dev.id == devId:
					# If we passed a devId then ignore it, we don't want to check against the server calling this function
					continue
					
				if "port" in dev.ownerProps and dev.ownerProps["port"] == str(port):
					if not suppressLogging: self.logger.warning ("Unable to use port {0} because another HomeKit-Bridge Server '{1}' is assigned to that port".format(str(port), dev.name))
					return False
					
				if "listenPort" in dev.ownerProps and dev.ownerProps["listenPort"] == str(port):
					self.logger.warning ("Unable to use port {0} because another HomeKit-Bridge Server '{1}' call back is assigned to that port".format(str(port), dev.name))
					return False
			
			# So far, so good, now lets check Homebridge Buddy Legacy servers to see if one is wanting to use this port and just isn't running
			for dev in indigo.devices.iter("com.eps.indigoplugin.homebridge.Homebridge-Server"):
				if "hbport" in dev.ownerProps and dev.ownerProps["hbport"] == str(port):
					if not suppressLogging: self.logger.warning ("Unable to use port {0} because a Homebridge Buddy Server '{1}' is assigned to that port".format(str(port), dev.name))
					return False
					
				if "hbcallback" in dev.ownerProps and dev.ownerProps["hbcallback"] == str(port):
					self.logger.warning ("Unable to use port {0} because a Homebridge Buddy Server '{1}' call back is assigned to that port".format(str(port), dev.name))
					return False
					
			for dev in indigo.devices.iter("com.eps.indigoplugin.homebridge.Homebridge-Guest"):
				if "hbport" in dev.ownerProps and dev.ownerProps["hbport"] == str(port):
					if not suppressLogging: self.logger.warning ("Unable to use port {0} because a Homebridge Buddy Guest Server '{1}' is assigned to that port".format(str(port), dev.name))
					return False
					
				if "hbcallback" in dev.ownerProps and dev.ownerProps["hbcallback"] == str(port):
					if not suppressLogging: self.logger.warning ("Unable to use port {0} because a Homebridge Buddy Guest Server '{1}' call back is assigned to that port".format(str(port), dev.name))
					return False				
					
			for dev in indigo.devices.iter("com.eps.indigoplugin.homebridge.Homebridge-Custom"):
				if "hbport" in dev.ownerProps and dev.ownerProps["hbport"] == str(port):
					if not suppressLogging: self.logger.warning ("Unable to use port {0} because a Homebridge Buddy Custom Server '{1}' is assigned to that port".format(str(port), dev.name))
					return False
					
				if "hbcallback" in dev.ownerProps and dev.ownerProps["hbcallback"] == str(port):
					if not suppressLogging: self.logger.warning ("Unable to use port {0} because a Homebridge Buddy Custom Server '{1}' call back is assigned to that port".format(str(port), dev.name))
					return False	
					
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return False
			
		return ret
		
	
	#
	# Set up jstash library for JSON records
	#
	def setupJstash (self):
		try:
			# Since the fields are the same for actions and devices
			rec 				= {}	# Indigo object to HomeKit device definition record [item]
			rec["id"] 			= 0		# Indigo object ID
			rec["name"] 		= ""	# Indigo object name
			rec["alias"] 		= ""	# HomeKit alias
			rec["type"] 		= ""	# HomeKit device type
			rec["object"] 		= ""	# Indigo object type [Device, Action, Variable]
			rec["char"]			= {}	# HomeKit characteristics [hkchar] for the advanced properties editor
			rec["action"]		= {}	# HomeKit action map [hkaction] for the advanced properties editor
			rec["url"]			= ""	# The Homebridge callback URL to change characteristics
			
			eps.jstash.createRecordDefinition ("item", rec)
			
			rec 				= {}	# HomeKit device characteristic source [hkchar]
			rec["name"] 		= ""	# Characteristic name, i.e., On, Brightness, CurrentLockStatus, etc
			rec["source"]		= ""	# Source for the data [state, attribute, property, variable]
			rec["sourcedata"]	= ""	# Data for thes source, i.e., state name, attribute name, property name, variable id
			rec["sourceextra"]	= ""	# Future proofing and any additional info we need, perhaps data conversions or conditions
			rec["type"]			= ""	# The data type
			
			eps.jstash.createRecordDefinition ("hkchar", rec)
			
			rec 				= {}	# HomeKit device characteristic action [hkaction]
			rec["characteristic"]= ""	# Characteristic name, i.e., On, Brightness, CurrentLockStatus, etc
			rec["whenvalueis"]	= ""	# Operator [equal, between, greater, etc]
			rec["whenvalue"]	= ""	# Value to compare to
			rec["command"]		= ""	# Full library command to execute, i.e., indigo.device.turnOn
			rec["arguments"] 	= ""	# Arguments for the command using static or keywords, i.e., [devId] [value]
			rec["whenvalue2"] 	= ""	# If operator requires a second value, such as [between]
			rec["type"]			= ""	# The data type
			
			eps.jstash.createRecordDefinition ("hkaction", rec)
					
		except Exception as e:
			self.logger.error (ext.getException(e))		
			
	
	#
	# Take a device ID and resolve it to a HomeKit default type
	#
	def deviceIdToHomeKitType (self, devId):
		try:
			type = ("error", "HomeKit doesn't know how to control this object, to use it you may need to wrap the device via a plugin like Device Extensions or ask the developer to implement the Voice Command Bridge API.")
			
			if int(devId) in indigo.devices:
				dev = indigo.devices[int(devId)]
				
				if "onOffState" in dev.states: 					type = ("relay", "On/Off Switch")
				if "brightnessLevel" in dev.states: 			type = ("dimmer", "Dimmer Switch")
				
				# Put attribute checks in try
				try:
					if dev.supportsRGB:							type = ("rgb", "Color Light")
				except Exception as ex:
					pass
					
			elif int(devId) in indigo.actionGroups:
				return ("relay", "On/Off Switch (Run Action Group)")
								
			else:
				type = ("error", "This item doesn't exist in Indigo and cannot be included.")
							
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return type
		
	#
	# Create a JSON device record from a device or action group
	#
	def createJSONItemRecord (self, obj, alias = None):
		try:
			rec = eps.jstash.createRecord ("item")
			rec["char"] = []
			rec["action"] = []
			
			if obj is not None:
				rec["id"] = obj.id
				rec["name"] = obj.name
				
				#indigo.server.log(unicode(type(obj)))
			
				if alias is None or alias == "":
					rec["alias"] = obj.name
				else:
					rec["alias"] = alias
			
				#(type, typename) = self.deviceIdToHomeKitType (obj.id)
			
				#rec["typename"] = typename # Just for showing the end user
				#rec["type"] = type
				
				#rec["treatas"] = "none" # Legacy Homebridge Buddy
			
				rec["object"] = "Device"
				if obj.id in indigo.actionGroups: rec["object"] = "Action"
				#if "Run Action Group" in rec["typename"]: rec["object"] = "Action"
				
				#indigo.server.log(unicode(rec))
				
			else:
				rec["id"] = 0
				rec["name"] = ""
				rec["alias"] = ""
				#rec["type"] = ""
				#rec["typename"] = ""
				rec["object"] = ""
				#rec["treatas"] = "none" # Legacy Homebridge Buddy
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return None
			
		return rec
	
	################################################################################
	# WIZARD METHODS
	################################################################################
	
	#
	# Build the device array for automatic server, either using valuesDict from the form or un-stashed JSON saved to plugin prefs
	#
	def wizardServerBuilder (self, valuesDict):	
		try:
			# Run through all of our own servers to build a list of device ID's that we won't use elsewhere
			inuse = []
			for dev in indigo.devices.iter(self.pluginId + ".Server"):
				if "excludedDevices" in dev.pluginProps:
					excludedDevices = json.loads(dev.pluginProps["excludedDevices"])
					for r in excludedDevices:
						inuse.append (r["id"])
		
			# Menu items won't have valuesDict on load and will error out, set defaults
			method = "homekit"
			if "method" in valuesDict: method = valuesDict["method"]
			
			hbbaliases = True
			if "hbbaliases" in valuesDict: hbbaliases = valuesDict["hbbaliases"]
			
			hbbdevices = True
			if "hbbdevices" in valuesDict: hbbdevices = valuesDict["hbbdevices"]
			
			mincount = 1
			if "mincount" in valuesDict: mincount = int(valuesDict["mincount"])
			
			security = True
			if "security" in valuesDict: security = valuesDict["security"]
			
			securitydevice = True
			if "securitydevice" in valuesDict: securitydevice = valuesDict["securitydevice"]
			
			typeDict = {}
			hasUnusable = False
			unusablePlugins = indigo.List()
			
			if "wizard" not in valuesDict or ("wizard" in valuesDict and valuesDict["wizard"] == "folder"):
				# Create the folders and then change the wizard type so it processes all devices below
				hbbdevices = False # This doesn't apply to this method
				
				for f in indigo.devices.folders:
					listName = f.name + " Devices"
					
					typeDict = collections.OrderedDict(sorted(typeDict.items()))
				
					thisList = []
					if listName in typeDict: thisList = typeDict[listName]
			
					#thisList.append(v["devId"])
			
					typeDict[listName] = thisList
					
				valuesDict["wizard"] = "folderdevices"
				
				
			if "wizard" in valuesDict and valuesDict["wizard"] == "alexa":
				itemcount = 0
				for dev in indigo.devices.iter("com.indigodomo.opensource.alexa-hue-bridge.emulatedHueBridge"):
					itemcount = itemcount + 1
					
					listName = "Alexa-Hue Mirror"
					
					alexaDevices = json.loads (dev.ownerProps["alexaDevices"])
					#indigo.server.log (unicode(alexaDevices))
					
					for k, v in alexaDevices.iteritems():
						if int(v["devId"]) in inuse: continue # Don't add anything we have a manual sever for
						#indigo.server.log ("{}: {}".format(v["devId"], v["devName"]))
					
						#typeDict = collections.OrderedDict(sorted(typeDict.items()))
					
						thisList = []
						if listName in typeDict: thisList = typeDict[listName]
				
						thisList.append(v["devId"])
				
						typeDict[listName] = thisList	
						
				if itemcount == 0: return {}
			
			if "wizard" in valuesDict and (valuesDict["wizard"] == "type" or valuesDict["wizard"] == "folderdevices" or valuesDict["wizard"] == "all"):
				for dev in indigo.devices:
					if dev.id in inuse: continue # Don't add anything we have a manual sever for
					
					# Devices we'll ignore entirely
					if dev.pluginId == "com.eps.indigoplugin.homebridge" and dev.deviceTypeId == "Homebridge-Server": continue
					if dev.pluginId == "com.eps.indigoplugin.homebridge" and dev.deviceTypeId == "Homebridge-Guest": continue
					if dev.pluginId == "com.eps.indigoplugin.homebridge" and dev.deviceTypeId == "Homebridge-Custom": continue
				
					# If we are converting HBB aliases then don't count them because we'll only be using their device ref, not them
					if hbbaliases and dev.pluginId == "com.eps.indigoplugin.homebridge" and dev.deviceTypeId == "Homebridge-Alias":
						continue

					obj = eps.homekit.getServiceObject (dev.id, 0, None, True, True)
					
					listName = "Unknown"
					if valuesDict["wizard"] == "type" and method == "homekit": listName = obj.desc + " Devices"
					if valuesDict["wizard"] == "folderdevices":	listName = indigo.devices.folders[dev.folderId].name + " Devices"
					if valuesDict["wizard"] == "all": listName = "Indigo Devices"
					
					if obj.desc == "Invalid": 
						listName = "- UNUSABE DEVICES (See Log) -"
						hasUnusable = True
						if dev.pluginId == "": indigo.server.log ("\tNative {} Device".format(unicode(type(dev))))
						pluginData = "{}.{}".format(dev.pluginId, dev.deviceTypeId)
						if pluginData not in unusablePlugins: unusablePlugins.append (pluginData)
						
					# If we are adding HBB devices to their own group
					if hbbdevices and dev.pluginId == "com.eps.indigoplugin.homebridge":
						if dev.deviceTypeId == "Homebridge-Wrapper": 
							listName = "HBB Wrappers"
							if valuesDict["wizard"] == "type" and method == "homekit": listName = "HBB Lightbulb Devices"
						
						if dev.deviceTypeId == "Homebridge-Alias": 
							listName = "HBB Aliases" # If they are excluded it won't make it here anyway
							if valuesDict["wizard"] == "type" and method == "homekit": listName = "HBB Lightbulb Devices"
						
						
					if security:
						# Since obj is populated no matter what we can use that since we already auto detect them, no need to figure locks or garage doors
						if obj.type == "GarageDoorOpener" or obj.type == "LockMechanism":
							listName = "- SECURITY DEVICES -"	
						
					#typeDict = collections.OrderedDict(sorted(typeDict.items()))
					
					thisList = []
					if listName in typeDict: thisList = typeDict[listName]
				
					thisList.append(dev.id)
				
					typeDict[listName] = thisList	
				
				
				if hasUnusable:
					self.logger.warning ("\nYou have unusable HomeKit devices.  These will still be added to a server but that server cannot be started.\nIf a future plugin update can map them they will be automatically moved to their appropriate server.")
					self.logger.debug ("\nThe following plugin devices are included in this list:\n{}".format(unicode(unusablePlugins)))
						
			# Add our overflow device in case the counts don't meet minimum requirements
			typeDict["Miscellaneous Overflow"] = []
		
			newTypeDict = {}
			
			for k, v in typeDict.iteritems():
				if securitydevice and security and (k == "Relay Devices" or k == "Switch Devices"):
					# Append a fake number to change the count of switches
					v.append (1)
				
				# If we don't meet the minimum count requirement then move it to the miscellaneous server and skip
				if k != "Miscellaneous Overflow" and k != "- SECURITY DEVICES -" and len(v) < mincount:
					newlist = typeDict["Miscellaneous Overflow"]
					for devId in v:
						newlist.append (devId)
					
					typeDict["Miscellaneous Overflow"] = newlist
				
					continue
				
				if len(v) == 0: continue # Mostly only happens with Miscellaneous if there's nothing to put there
				
				# If we get to here add it to the new typedict, we'll add misc after
				newTypeDict[k] = v
				
			if "Miscellaneous Overflow" in typeDict:
				if len(typeDict["Miscellaneous Overflow"]) > 0: newTypeDict["Miscellaneous Overflow"] = typeDict["Miscellaneous Overflow"]
				
			typeDict = newTypeDict
			typeDict = collections.OrderedDict(sorted(typeDict.items()))
				
			return typeDict
		
		except Exception as e:
			self.logger.error (ext.getException(e))
	
	#
	# Wizard device types
	#
	def wizardListMethodDeviceTypes (self, args, valuesDict):	
		try:
			ret = [("none", "No compatible device found to create servers for")]
			retList = []
			
			# Prepare the log output
			logStr = "SERVER DETAILS\n"
			
			typeDict = self.wizardServerBuilder (valuesDict)
			if len(typeDict) == 0: return ret
			
			for k, v in typeDict.iteritems():
				if len(v) == 0: continue
					
				serverterm = "Server"
				deviceterm = "Device"
				serverCount = int(math.ceil(len(v) / 99) + 1)
				if serverCount > 1: serverterm = "Servers"
				if len(v) > 1: deviceterm = "Devices"
				
				listName = "{}: {} {} | {} {} Needed".format(k, str(len(v)), deviceterm, str(serverCount), serverterm)
				retList.append ((k, listName))
				
				# Output to debug log for reporting purposes
				logStr += listName + "\n"
				for devId in v:
					if devId == 1:  # Security Device Placeholder
						logStr += "\tSECURITY DEVICE SERVER STUB\n"
					else:	
						logStr += "\t" + indigo.devices[devId].name + "\n"
			
			return retList
			
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return ret
			
	#
	# Wizard form field change
	#
	def wizardFormFieldChanged (self, valuesDict, typeId):	
		try:
			errorsDict = indigo.Dict()		
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return (valuesDict, errorsDict)
			
	################################################################################
	# SERVER METHODS
	################################################################################

	#
	# JSON data check for valuesDict
	#
	def serverCheckForJSONKeys (self, valuesDict):
		try:
			if 'includedDevices' not in valuesDict:
				valuesDict['includedDevices'] = json.dumps([])  # Empty list in JSON container	
				
			if 'includedActions' not in valuesDict:
				valuesDict['includedActions'] = json.dumps([])	
				
			if 'excludedDevices' not in valuesDict:
				valuesDict['excludedDevices'] = json.dumps([])
				
			if 'excludedActions' not in valuesDict:
				valuesDict['excludedActions'] = json.dumps([])
				
			if 'hkStatesJSON' not in valuesDict:
				valuesDict['excludedActions'] = json.dumps([])
				
			if 'hkActionsJSON' not in valuesDict:
				valuesDict['excludedActions'] = json.dumps([])
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return valuesDict
		
				
		
	#
	# HomeKit device types
	#
	def serverListHomeKitDeviceTypes (self, args, valuesDict):	
		try:
			ret = [("default", "No data")]
			retList = []
			
			services = eps.homekit.getHomeKitServices ()
			for name, desc in services.iteritems():
				#indigo.server.log (name)
				if "service_" in name:
					retList.append ((name, desc))
					
			#indigo.server.log(unicode(retList))
			
			return retList	
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return ret
		
	#
	# All devices
	#
	def serverListIncludeDevices (self, args, valuesDict):
		ret = [("default", "No data")]
		
		try:
			valuesDict = self.serverCheckForJSONKeys (valuesDict)	
			includedDevices = json.loads(valuesDict["includedDevices"])
			
			retList = []
			
			# Add our custom options
			#retList.append (("-all-", "All Indigo Devices"))
			retList.append (("-fill-", "Fill With Unassigned Devices"))
			#retList.append (("-none-", "Don't Include Any Devices"))
			retList = eps.ui.addLine (retList)
			
			for dev in indigo.devices:
				name = dev.name
				
				# Homebridge Buddy Legacy support
				if dev.pluginId == "com.eps.indigoplugin.homebridge":
					if dev.deviceTypeId == "Homebridge-Wrapper":
						name += " => [HBB " + dev.ownerProps["treatAs"].upper() + " Wrapper]"
					elif dev.deviceTypeId == "Homebridge-Alias":
						name += " => [HBB " + dev.ownerProps["treatAs"].upper() + " Alias]"
				
				if "filterIncluded" in valuesDict and valuesDict["filterIncluded"]:
					# Only include devices that are not already
					r = eps.jstash.getRecordWithFieldEquals (includedDevices, "id", dev.id)
					if r is None:
						retList.append ( (str(dev.id), name) )
				else:
					retList.append ( (str(dev.id), name) )
			
			return retList
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return ret
			
	#
	# All actions
	#
	def serverListIncludeActionGroups (self, args, valuesDict):
		ret = [("default", "No data")]
		
		try:
			retList = []
			
			# Add our custom options
			#retList.append (("-all-", "All Indigo Action Groups"))
			retList.append (("-fill-", "Fill With Unassigned Action Groups"))
			#retList.append (("-none-", "Don't Include Any Action Groups"))
			retList = eps.ui.addLine (retList)
			
			for dev in indigo.actionGroups:
				retList.append ( (str(dev.id), dev.name) )
				
			return retList
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return ret	
			
			
	#
	# All devices stored in our server JSON data
	#
	def serverListJSONDevices (self, args, valuesDict):
		ret = [("default", "No data")]
		
		try:
			valuesDict = self.serverCheckForJSONKeys (valuesDict)	
			includedDevices = json.loads(valuesDict["includedDevices"])
			includedActions = json.loads(valuesDict["includedActions"])
			
			# Combine the lists for the return
			includedObjects = []
			
			for d in includedDevices:
				name = d["alias"]
				if name == "": name = d["name"]
				d["sortbyname"] = name.lower()
				
				name = "{0}: {1}".format(d["object"], name)
				d["sortbytype"] = name.lower()
				
				
				includedObjects.append (d)
				
			for d in includedActions:
				name = d["alias"]
				if name == "": name = d["name"]
				d["sortbyname"] = name.lower()
				
				name = "{0}: {1}".format(d["object"], name)
				d["sortbytype"] = name.lower()
				
				includedObjects.append (d)	
			
			retList = []
			
			# Test for listsort since it won't be available if it's a new device
			if "listSort" in valuesDict:
				includedObjects = eps.jstash.sortStash (includedObjects, valuesDict["listSort"])
			else:
				includedObjects = eps.jstash.sortStash (includedObjects, "sortbyname")
			
			for d in includedObjects:
				name = d["alias"]
				if name == "": name = d["name"]
				name = "{0}: {1}".format(d["object"], name)
				
				retList.append ( (str(d["id"]), name) )
				
			return retList
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return ret		
			
	
	#
	# Run action on device(s) or action(s) selected in list
	#
	def serverButtonRunAction (self, valuesDict, devId, typeId):	
		try:
			errorsDict = indigo.Dict()
			includedDevices = json.loads(valuesDict["includedDevices"])
			includedActions = json.loads(valuesDict["includedActions"])
			
			if len(valuesDict["deviceList"]) == 0:
				errorsDict["showAlertText"] = "You must select something to perform an action on it."
				return (valuesDict, errorsDict)
				
			if valuesDict["objectAction"] == "delete":
				deleted = 0
				for id in valuesDict["deviceList"]:
					includedDevices = eps.jstash.removeRecordFromStash (includedDevices, "id", int(id))
					includedActions = eps.jstash.removeRecordFromStash (includedActions, "id", int(id))
					deleted = deleted + 1
					
				errorsDict["showAlertText"] = "You removed {0} items and can add up to {1} more.".format(str(deleted), str(99 - len(includedDevices) - len(includedActions)))
				valuesDict["deviceLimitReached"] = False # Since removing even just one guarantees we aren't at the limit yet
				
			if valuesDict["objectAction"] == "edit":
				if len(valuesDict["deviceList"]) > 1:	
					errorsDict["showAlertText"] = "You can only edit one device at a time, you selected multiple devices."
					return (valuesDict, errorsDict)
				
				else:
					isAction = False
					r = eps.jstash.getRecordWithFieldEquals (includedDevices, "id", int(valuesDict["deviceList"][0]))
					if r is None:
						r = eps.jstash.getRecordWithFieldEquals (includedActions, "id", int(valuesDict["deviceList"][0]))
						if r is not None: isAction = True
										
					if r is not None:
						# Remove from our list since technically we are removing and readding rather than editing
						includedDevices = eps.jstash.removeRecordFromStash (includedDevices, "id", int(valuesDict["deviceList"][0]))
						includedActions = eps.jstash.removeRecordFromStash (includedActions, "id", int(valuesDict["deviceList"][0]))
						
						if not isAction: 
							valuesDict["objectType"] = "device"
							valuesDict["device"] = str(r["id"])
							
						if isAction: 
							valuesDict["objectType"] = "action"
							valuesDict["action"] = str(r["id"])
						
						valuesDict["name"] = r["name"]
						valuesDict["alias"] = r["alias"]
						#valuesDict["typename"] = r["typename"]
						#valuesDict["type"] = r["type"]
						valuesDict["hktype"] = r["hktype"]
						valuesDict["hkStatesJSON"] = r["char"]
						valuesDict["hkActionsJSON"] = r["action"]
						valuesDict["deviceOrActionSelected"] = True
						valuesDict["deviceLimitReached"] = False # Since we only allow 99 we are now at 98 and valid again
						valuesDict["editActive"] = True # Disable fields so the user knows they are in edit mode

			valuesDict['includedDevices'] = json.dumps(includedDevices)
			valuesDict['includedActions'] = json.dumps(includedActions)								
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
	
		return (valuesDict, errorsDict)	
		
	#
	# Get the JSON stash list for the object type, return the list on saveAndReturn to write it to valuesDict and return all
	#
	def getIncludeStashList (self, thistype, valuesDict, saveAndReturn = None):
		try:
			includedDevices = json.loads(valuesDict["includedDevices"])
			includedActions = json.loads(valuesDict["includedActions"])
			
			max = 99 - len(includedDevices) - len(includedActions)
			
			retList = includedDevices
			if thistype == "Action": retList = includedActions
			
			if saveAndReturn is not None:
				if thistype == "Device":
					valuesDict['includedDevices'] = json.dumps(eps.jstash.sortStash (saveAndReturn, "alias"))
				else:
					valuesDict['includedActions'] = json.dumps(eps.jstash.sortStash (saveAndReturn, "alias"))
					
				return valuesDict
			else:
				return (retList, max)
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
	#
	# Get the JSON stash list for the object type, return the list on saveAndReturn to write it to valuesDict and return all
	#
	def getExcludeStashList (self, thistype, valuesDict, saveAndReturn = None):
		try:
			excludedDevices = json.loads(valuesDict["excludedDevices"])
			excludedActions = json.loads(valuesDict["excludedActions"])
			
			retList = excludedDevices
			if thistype == "Action": retList = excludedActions
			
			if saveAndReturn is not None:
				if thistype == "Device":
					valuesDict['excludedDevices'] = json.dumps(eps.jstash.sortStash (saveAndReturn, "alias"))
				else:
					valuesDict['excludedActions'] = json.dumps(eps.jstash.sortStash (saveAndReturn, "alias"))
					
				includedDevices = json.loads(valuesDict["excludedDevices"])
				includedActions = json.loads(valuesDict["excludedActions"])	
				
				return valuesDict
			else:
				return retList
		
		except Exception as e:
			self.logger.error (ext.getException(e))		
	
	#
	# Get the HK object from the server form values
	#
	def serverGetHomeKitObjectFromFormData (self, valuesDict):
		try:
			# Pull the HK object from the selected type and device so we can see if the required settings are set
			obj = eps.homekit.getServiceObject (r["id"], 0, r["hktype"], False, True)
			return obj
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
			

	
	#
	# Add device or action
	#
	def serverButtonAddDeviceOrAction (self, valuesDict, typeId, devId):
		try:
			errorsDict = indigo.Dict()
			
			if "deviceLimitReached" in valuesDict and valuesDict["deviceLimitReached"]: return valuesDict
			if valuesDict["device"] == "-line-":
				errorsDict["showAlertText"] = "You cannot add a separator as a HomeKit device."
				errorsDict["device"] = "Invalid device"
				errorsDict["action"] = "Invalid action"
				return (valuesDict, errorsDict)
				
			# Determine if we are processing devices or action groups
			if valuesDict["objectType"] == "device":
				thistype = "Device"
			else:
				thistype = "Action"
				
			if valuesDict[thistype.lower()] == "-fill-":
				(valuesDict, errorsDict) = self.serverButtonAddDeviceOrAction_Fill (valuesDict, errorsDict, thistype, devId)
			else:
				(valuesDict, errorsDict) = self.serverButtonAddDeviceOrAction_Object (valuesDict, errorsDict, thistype, devId)
			
			# Wrap up
			includedDevices = json.loads(valuesDict["includedDevices"])
			includedActions = json.loads(valuesDict["includedActions"])
			
			if len(includedDevices) + len(includedActions) >= 99:
				msg = "HomeKit can handle up to 99 devices and/or actions per server and you have reached the limit.  You can create additional servers if you need more than 99 devices and/or actions."
				errorsDict = eps.ui.setErrorStatus (errorsDict, msg)
				
				valuesDict["deviceLimitReached"] = True # Don't let them add any more
				valuesDict["deviceOrActionSelected"] = False # Turn off alias and type
				#return (valuesDict, errorsDict)
					
			valuesDict['includedDevices'] = json.dumps(eps.jstash.sortStash (includedDevices, "alias"))
			valuesDict['includedActions'] = json.dumps(eps.jstash.sortStash (includedActions, "alias"))
			valuesDict['alias'] = ""
			valuesDict['editActive'] = False # We definitely are not editing any longer	

			# Defaults if there are none
			if valuesDict["device"] == "": valuesDict["device"] = "-fill-"
			if valuesDict["action"] == "": valuesDict["action"] = "-fill-"	
				
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return (valuesDict, errorsDict)		
		

		
	#
	# Add FILL type
	#
	def serverButtonAddDeviceOrAction_Fill (self, valuesDict, errorsDict, thistype, serverId):	
		try:
			total = 0
			
			(includeList, max) = self.getIncludeStashList (thistype, valuesDict)
			
			totalRemoved = 0 # if we remove below because we need it to count
			
			# If we already have a none then ignore and return
			r = eps.jstash.getRecordWithFieldEquals (includeList, "type", "ALL")
			if r is not None: 
				includeList = eps.jstash.removeRecordFromStash (includeList, "type", "ALL")
				errorsDict = eps.ui.setErrorStatus (errorsDict, "You had specified to include all {0}s, that has been cleared so you can add them individually.".format(thistype.lower()))
				totalRemoved = totalRemoved - 1 # since we are adding the two together below but just removed one
			
			# If its already set to all then change it out with none and pop a message
			r = eps.jstash.getRecordWithFieldEquals (includeList, "type", "NONE")
			if r is not None: 
				includeList = eps.jstash.removeRecordFromStash (includeList, "type", "NONE")
				errorsDict = eps.ui.setErrorStatus (errorsDict, "You had specified to include no {0}s, that has been cleared so you can add them.".format(thistype.lower()))
				totalRemoved = totalRemoved - 1 # since we are adding the two together below but just removed one
				
			total = total + totalRemoved
			
			indigoObjects = indigo.devices
			if thistype == "Action": indigoObjects = indigo.actionGroups
			unknownType = False
			
			for dev in indigoObjects:
				if total < max:
					# Check our local stash
					r = eps.jstash.getRecordWithFieldEquals (includeList, "id", dev.id)
					if r is None:
						# Add the device to the device list
						device = self.createJSONItemRecord (dev)
						if device is not None: 
							if device["type"] == "error":
								unknownType = True
							else:				
								#device["url"] = "/HomeKit?cmd=setCharacteristic&objId={}&serverId={}".format(str(dev.id), str(serverId))	
								#device["url"] = "/HomeKit?objId={}&serverId={}".format(str(dev.id), str(serverId))	
								#obj = hkapi.automaticHomeKitDevice (indigo.devices[int(dev.id)], True)
								obj = eps.homekit.getServiceObject (dev.id, serverId, None, True, True)
								device['hktype'] = "service_" + obj.type # Set to the default type
								includeList.append (device)
								total = total + 1
								
								
				else:
					#indigo.server.log(str(total))
					break
					
			#indigo.server.log(str(len(includeList)))
			#indigo.server.log(str(max))
							
			valuesDict = self.getIncludeStashList (thistype, valuesDict, includeList)
			
			if unknownType:
				errorsDict = eps.ui.setErrorStatus (errorsDict, "HomeKit doesn't know how to control one or more of the devices, to use them you may need to wrap the device via a plugin like Device Extensions or ask the developer to implement the Voice Command Bridge API.  Only the devices that HomeKit can control have been added.")
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return (valuesDict, errorsDict)		
		
	#
	# Add individual object type
	#
	def serverButtonAddDeviceOrAction_Object (self, valuesDict, errorsDict, thistype, serverId):	
		try:
			#valuesDict = self.serverCheckForJSONKeys (valuesDict)
			total = 0
			
			(includeList, max) = self.getIncludeStashList (thistype, valuesDict)
			
			totalRemoved = 0 # if we remove below because we need it to count
			
			# If we already have a none then ignore and return
			r = eps.jstash.getRecordWithFieldEquals (includeList, "type", "ALL")
			if r is not None: 
				includeList = eps.jstash.removeRecordFromStash (includeList, "type", "ALL")
				errorsDict = eps.ui.setErrorStatus (errorsDict, "You had specified to include all {0}s, that has been cleared so you can add them individually.".format(thistype.lower()))
				totalRemoved = totalRemoved - 1 # since we are adding the two together below but just removed one
				
			# If its already set to all then change it out with none and pop a message
			r = eps.jstash.getRecordWithFieldEquals (includeList, "type", "NONE")
			if r is not None: 
				includeList = eps.jstash.removeRecordFromStash (includeList, "type", "NONE")
				errorsDict = eps.ui.setErrorStatus (errorsDict, "You had specified to include no {0}s, that has been cleared so you can add them.".format(thistype.lower()))
				totalRemoved = totalRemoved - 1 # since we are adding the two together below but just removed one
			
			total = total + totalRemoved
			
			if thistype == "Device":
				dev = indigo.devices[int(valuesDict["device"])]
			else:
				dev = indigo.actionGroups[int(valuesDict["action"])]
				
			device = self.createJSONItemRecord (dev, valuesDict["alias"])
			#indigo.server.log(unicode(device))
			
			if device is not None and device["type"] == "error":
				#errorsDict = eps.ui.setErrorStatus (errorsDict, device["typename"]) # Let the user know we don't know how to control the device
				errorsDict["device"] = "Invalid device"
				errorsDict["action"] = "Invalid action"
				
				valuesDict = self.getIncludeStashList (thistype, valuesDict, includeList)
				return (valuesDict, errorsDict)
			
			if device is not None: 
				
				r = eps.jstash.getRecordWithFieldEquals (includeList, "alias", device["alias"])
				if r is None:					
					#device['treatas'] = valuesDict["treatAs"] # Homebridge Buddy Legacy
					device['hktype'] = valuesDict["hkType"]
					#device["url"] = "/HomeKit?cmd=setCharacteristic&objId={}&serverId={}".format(str(dev.id), str(serverId))
					#device["url"] = "/HomeKit?objId={}&serverId={}".format(str(dev.id), str(serverId))	
					#device["char"] = valuesDict["hkStatesJSON"]
					#device["action"] = valuesDict["hkActionsJSON"]
					
					total = total + 1			
					includeList.append (device)
					
					valuesDict = self.getIncludeStashList (thistype, valuesDict, includeList)
					return (valuesDict, errorsDict)
					
				else:
					valuesDict["alias"] = device["alias"] # In case they didn't provide an alias
					errorsDict = eps.ui.setErrorStatus (errorsDict, "A device by that name already exists, please choose a different name.")
					errorsDict["alias"] = "Duplicate name"
					
					valuesDict = self.getIncludeStashList (thistype, valuesDict, includeList)
					return (valuesDict, errorsDict)
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return (valuesDict, errorsDict)	
		
	#
	# Do nothing, this serves only as a trigger to kick in automatic refreshing lists
	#
	def serverFormFieldChanged_DoNothing (self, valuesDict, typeId, devId):	
		try:
			return (valuesDict, indigo.Dict())			
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return (valuesDict, errorsDict)			
		
	
		
	#
	# Server form device field changed
	#
	def serverFormFieldChanged_Device (self, valuesDict, typeId, devId):	
		try:
			errorsDict = indigo.Dict()	
			
			# The device changed, if it's not a generic type then fill in defaults
			if valuesDict["device"] != "" and valuesDict["device"] != "-fill-" and valuesDict["device"] != "-line-":
				valuesDict["deviceOrActionSelected"] = True # Enable fields
				
				# So long as we are not in edit mode then pull the HK defaults for this device and populate it
				if not valuesDict["editActive"]:
					obj = eps.homekit.getServiceObject (valuesDict["device"], devId, None, True, True)
					#obj = hkapi.automaticHomeKitDevice (indigo.devices[int(valuesDict["device"])], True)
					#valuesDict = self.serverFormFieldChanged_RefreshHKDef (valuesDict, obj) # For our test when we were defining the HK object here
					valuesDict["hkType"] = "service_" + obj.type # Set to the default type		
					
			#if valuesDict["deviceOrActionSelected"]: valuesDict["actionsCommandEnable"] = True # Enable actions		
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return (valuesDict, errorsDict)
		

	#
	# Server form action field changed
	#
	def serverFormFieldChanged_Action (self, valuesDict, typeId, devId):	
		try:
			errorsDict = indigo.Dict()	
			
			# The device changed, if it's not a generic type then fill in defaults
			if valuesDict["action"] != "" and valuesDict["action"] != "-fill-" and valuesDict["action"] != "-line-":
				valuesDict["deviceOrActionSelected"] = True # Enable fields
				
				# So long as we are not in edit mode then pull the HK defaults for this device and populate it
				if not valuesDict["editActive"]:
					# Actions are always switches by default
					#obj = hkapi.automaticHomeKitDevice (indigo.actionGroups[int(valuesDict["action"])], True)
					obj = eps.homekit.getServiceObject (valuesDict["action"], devId, None, True, True)
					#valuesDict = self.serverFormFieldChanged_RefreshHKDef (valuesDict, obj) # For our test when we were defining the HK object here
					valuesDict["hkType"] = "service_" + obj.type # Set to the default type		
					
			#if valuesDict["deviceOrActionSelected"]: valuesDict["actionsCommandEnable"] = True # Enable actions		
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return (valuesDict, errorsDict)
		
	#
	# Server form field change
	#
	def serverFormFieldChanged (self, valuesDict, typeId, devId):	
		try:
			valuesDict = self.serverCheckForJSONKeys (valuesDict)					
			errorsDict = indigo.Dict()		
			
			# Defaults if there are none
			valuesDict["deviceOrActionSelected"] = False # We'll change it below if needed
			if valuesDict["device"] == "": valuesDict["device"] = "-fill-"
			if valuesDict["action"] == "": valuesDict["action"] = "-fill-"
			
			#if valuesDict["treatAs"] == "": valuesDict["treatAs"] = "service_Switch" # Default
			
			# If there is no port and the server hasn't been overridden then populate it (suppress logging, we don't need it)
			if valuesDict["port"] == "":
				valuesDict["port"] = str(self.getNextAvailablePort (51826, devId, True))
				
			# Now check the callback port
			if valuesDict["listenPort"] == "":
				valuesDict["listenPort"] = str(self.getNextAvailablePort (8445, devId, True))
				
			# Now check the username
			if valuesDict["username"] == "":
				valuesDict["username"] = self.getNextAvailableUsername (devId, True)
				
			#indigo.server.log ("Port: {}\tListen:{}xxxx\tUser:{}".format(valuesDict["port"], valuesDict["listenPort"], valuesDict["username"]))
			
			if valuesDict["objectType"] == "device":
				if valuesDict["device"] != "" and valuesDict["device"] != "-fill-" and valuesDict["device"] != "-line-":
					valuesDict["deviceOrActionSelected"] = True
					
					#(type, typename) = self.deviceIdToHomeKitType (valuesDict["device"])
					#valuesDict["type"] = type
					#valuesDict["typename"] = typename
					
					# So long as we aren't editing (in which case we already saved our treatAs) then set the device type to discovery
					
						
						
				else:
					valuesDict["deviceOrActionSelected"] = False	

			if valuesDict["objectType"] == "action":
				if valuesDict["action"] != "" and valuesDict["action"] != "-fill-" and valuesDict["action"] != "-line-":
					valuesDict["deviceOrActionSelected"] = True
					#valuesDict["type"] = self.deviceIdToHomeKitType (valuesDict["action"])
						
				else:
					valuesDict["deviceOrActionSelected"] = False	
					
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return (valuesDict, errorsDict)
		
	#
	# Server config validation
	#
	def serverFormConfigValidation (self, valuesDict, typeId, devId):	
		try:
			success = True
			errorsDict = indigo.Dict()
			
			if valuesDict["editActive"]:
				errorsDict["showAlertText"] = "You are actively editing a list item, finish editing that item and save it.\n\nIf you don't want that item any longer then highlight it on the list and select the action to delete it instead.\n\nYou can also choose to cancel the configuration and lose any changes you have made."
				errorsDict["device"] = "Finish editing before saving your device"
				errorsDict["action"] = "Finish editing before saving your device"
				errorsDict["alias"] = "Finish editing before saving your device"
				errorsDict["add"] = "Finish editing before saving your device"
				success = False
				
			if success:
				# Reset the form back so when they open it again it has some defaults in place
				valuesDict["objectAction"] = "edit"
				valuesDict["device"] = "-fill-"
				valuesDict["action"] = "-fill-"
				valuesDict["objectType"] = "device"
				
				# If the server is running and the ports didn't change then we know we should be OK, otherwise we need to check
				server = indigo.devices[devId]
				
				# See if any of our critical items changed from the current config (or if this is a new device)
				if "port" not in server.pluginProps or server.pluginProps["port"] != valuesDict["port"] or server.pluginProps["listenPort"] != valuesDict["listenPort"] or server.pluginProps["username"] != valuesDict["username"]:
					# This is a new device or we changed it manually because these things wouldn't change if it were all automatic
					self.logger.info ("Server '{}' has changed ports or users, validating config".format(server.name))
					
					if not self.portIsOpen (valuesDict["port"], devId):
						if valuesDict["serverOverride"]:
							errorsDict["showAlertText"] = "The HB port {0} you entered is already being used on the Indigo server, please change it to something else.".format(valuesDict["port"])
							errorsDict["port"] = "This port number is already in use"
				
							return (False, valuesDict, errorsDict)
				
					if not self.portIsOpen (valuesDict["listenPort"], devId):
						if valuesDict["serverOverride"]:
							errorsDict["showAlertText"] = "The listen port {0} you entered is already being used on the Indigo server, please change it to something else.".format(valuesDict["listenPort"])
							errorsDict["listenPort"] = "This port number is already in use"
				
							return (False, valuesDict, errorsDict)
							
				# If we make it to here then everything is good and we can set the server address
				valuesDict["address"] = valuesDict["pin"] + " | " + valuesDict["port"]
				
				# Just in case we are missing either of these, add them now so that we won't get errors when we start up
				if not "includedDevices" in valuesDict: valuesDict["includedDevices"] = json.dumps([])
				if not "includedActions" in valuesDict: valuesDict["includedActions"] = json.dumps([])
				
				# Re-catalog the server just to be safe
				self._catalogServerDevices (server)
						
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return (success, valuesDict, errorsDict)
		
	#
	# Server prop changed
	#
	def serverPropChanged (self, origDev, newDev, changedProps):
		try:
			self.logger.threaddebug ("Server property change: " + unicode(changedProps))
			
			# States that will prompt us to save and restart the server
			watchStates = ["port", "listenPort", "includedDevices", "includedActions", "accessoryNamePrefix", "pin", "username"]
			needsRestart = False
			
			for w in watchStates:
				if w in changedProps:
					if w not in origDev.states or w not in newDev.states:
						needsRestart = True
						break
						
					if origDev.states[w] != newDev.states[w]:
						needsRestart = True
						break
					
			if needsRestart:
				# Save the configuration
				self.saveConfigurationToDisk (newDev)
				
				# Restart the server
				if self.checkRunningHBServer (newDev):
					if self.shellHBStopServer (newDev):
						self.shellHBStartServer (newDev)
						
				else:
					indigo.server.log ("HomeKit server '{0}' is not currently running, the configuration has been saved and will be used the next time this server starts".format(newDev.name))
				
				
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
	#
	# Server attribute changed
	#
	def serverAttribChanged (self, origDev, newDev, changedProps):
		try:
			self.logger.threaddebug ("Server attribute change: " + unicode(changedProps))
						
			# States that will prompt us to save and restart the server
			watchStates = ["name"]
			needsRestart = False
			
			for w in watchStates:
				if w in changedProps:
					a = getattr(origDev, w)
					b = getattr(newDev, w)
					
					if a != b:					
						#indigo.server.log ("CHANGED {0}".format(w))
						needsRestart = True
						break
					
			if needsRestart:
				# Save the configuration
				self.saveConfigurationToDisk (newDev)
				
				# Restart the server if it's running, otherwise leave it off
				if self.checkRunningHBServer (newDev):
					if self.shellHBStopServer (newDev):
						self.shellHBStartServer (newDev)
						
				else:
					indigo.server.log ("HomeKit server '{0}' is not currently running, the configuration has been saved and will be used the next time this server starts".format(newDev.name))
				
		except Exception as e:
			self.logger.error (ext.getException(e))			
			
	#
	# Turn ON received
	#
	def serverCommandTurnOn (self, dev):
		try:
			return self.shellHBStartServer (dev)
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return False
		
	#
	# Turn OFF received
	#
	def serverCommandTurnOff (self, dev):
		try:
			return self.shellHBStopServer (dev)
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return False	
		
	#
	# Send an update to Homebridge
	#
	def serverSendObjectUpdateToHomebridge (self, server, objId):
		try:
			if not server.states["onOffState"]:
				self.logger.debug ("Homebridge update requested, but '{}' isn't running, ignoring update request".format(server.name))
				return
									
			url = "http://127.0.0.1:{1}/devices/{0}".format(str(objId), server.pluginProps["listenPort"])
			
			#data = {'isOn':1, 'brightness': 100}
			data = {}
			
			data_json = json.dumps(data)
			payload = {'json_payload': data_json}
			r = requests.get(url, data=payload)
			
			#indigo.server.log(unicode(r))
			
			self.logger.debug ("Homebridge update requested, querying {0}".format(url))
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
		
		
	################################################################################
	# SHELL COMMANDS
	################################################################################		
	
	#
	# Check for server config folder structure
	#
	def shellCreateServerConfigFolders (self, dev):
		try:
			# See if there's a home directory hidden folder
			if not os.path.exists (self.CONFIGDIR):
				os.makedirs (self.CONFIGDIR)
				
				if not os.path.exists (self.CONFIGDIR):
					self.logger.error ("Unable to create the configuration folder under '{0}', '{1}' will be unable to run until this issue is resolved.  Please verify permissions and create the folder by hand if needed.".format(self.CONFIGDIR, dev.name))
					return False
					
			# Now ask Homebridge to create our structure there
			if not os.path.exists (self.CONFIGDIR + "/" + str(dev.id)):
				os.system('"' + self.HBDIR + '/createdir" "' + self.CONFIGDIR + "/" + str(dev.id) + '"')
				
				if not os.path.exists (self.CONFIGDIR + "/" + str(dev.id)):
					self.logger.error ("Unable to create the configuration folder under '{0}', '{1}' will be unable to run until this issue is resolved.  Please verify permissions and create the folder by hand if needed.".format(self.CONFIGDIR + "/" + str(dev.id), dev.name))
					return False
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return False
			
		return True
		
	#
	# Start HB for the provided server
	#
	def shellHBStartServer (self, dev, noCheck = False):
		try:
			self.logger.info ("Rebuilding configuration for '{0}'".format(dev.name))
			self.saveConfigurationToDisk (dev)

			# Start the HB server
			self.logger.threaddebug ('Running: "' + self.HBDIR + '/load" "' + self.CONFIGDIR + "/" + str(dev.id) + '"')
			os.system('"' + self.HBDIR + '/load" "' + self.CONFIGDIR + "/" + str(dev.id) + '"')
			
			indigo.devices[dev.id].updateStateOnServer("onOffState", False, uiValue="Starting")
			self.logger.info ("Attempting to start '{0}'".format(dev.name))
						
			# We cannot check the running port and have the server start because that will pause our web server too, so add
			# it to the global so that concurrent threading can check on the startup
			#self.STICKS = 0 # Reset server concurrent count
			#self.SERVER_STARTING.append (dev.id) # So we can check on the startup
			#return True
			
			# Give it up to 60 seconds to respond to a port query to know if it started
			loopcount = 1
			while loopcount < 13:
				time.sleep (5)
				result = self.checkRunningHBServer (dev)
				if result: 
					self.logger.info ("HomeKit server '{0}' has been started".format(dev.name))
					return True
					
				loopcount = loopcount + 1
					
			self.logger.error ("HomeKit server '{0}' could not be started, please check the service logs for more information, now issuing a forced shutdown of the service to be safe.".format(dev.name))	
			self.shellHBStopServer (dev)
			
			# To help prevent a possible hang	
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return False
			
		return False
		
	#
	# Stop HB for the provided server
	#
	def shellHBStopServer (self, dev, noStatus = False):
		try:
			# Start the HB server
			self.logger.threaddebug ('Running: "' + self.HBDIR + '/unload" "' + self.CONFIGDIR + "/" + str(dev.id) + '"')
			os.system('"' + self.HBDIR + '/unload" "' + self.CONFIGDIR + "/" + str(dev.id) + '"')
			
			self.logger.info ("Attempting to stop '{0}'".format(dev.name))
			if not noStatus: indigo.devices[dev.id].updateStateOnServer("onOffState", True, uiValue="Stopping")
			
			# Give it up to 60 seconds to respond to a port query to know if it started
			loopcount = 1
			while loopcount < 13:
				time.sleep (5)
				result = self.checkRunningHBServer (dev)
				if not result: 
					self.logger.info ("HomeKit server '{0}' has been stopped".format(dev.name))
					return True
					
				loopcount = loopcount + 1		
					
			self.logger.error ("HomeKit server '{0}' could not be stopped, please check the service logs for more information".format(dev.name))		
			
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return False
			
		return False	
		
		
	################################################################################
	# HOMEBRIDGE CONFIGURATION BUILDER
	################################################################################		
	
	#
	# Write server configuration to disk
	#
	def saveConfigurationToDisk (self, server):
		try:
			config = self.buildServerConfigurationDict (server.id)
			if config is None:
				self.logger.error ("Unable to build server configuration for '{0}'.".format(server.name))
				return False
				
			jsonData = json.dumps(config, indent=8)
			self.logger.debug (unicode(jsonData))
			
			if os.path.exists (self.CONFIGDIR + "/" + str(server.id)):
				with open(self.CONFIGDIR + "/" + str(server.id) + "/config.json", 'w') as file_:
					file_.write (jsonData)
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return False
			
		return True
	
	#
	# Build a configuration Dict for a given server
	#
	def buildServerConfigurationDict (self, serverId, debugMode = False):
		try:
			if int(serverId) not in indigo.devices: return None
			
			server = indigo.devices[int(serverId)]
			includedDevices = json.loads(server.pluginProps["includedDevices"])
			includedActions = json.loads(server.pluginProps["includedActions"])
			
			config = {}
			if debugMode: config=indigo.Dict()
			
			# Homebridge config
			bridge = {}
			if debugMode: bridge = indigo.Dict()
			
			bridge["username"] = server.pluginProps["username"]
			bridge["name"] = server.name
			bridge["pin"] = server.pluginProps["pin"]
			bridge["port"] = server.pluginProps["port"]
						
			config["bridge"] = bridge
			
			# Accessories
			accessories = []
			if debugMode: accessories = indigo.List()
			
			config["accessories"] = accessories # List of accessory dicts
			
			# Description
			config["description"] = "HomeKit configuration generated by HomeKit Bridge on {0} for device {1}".format (str(indigo.server.getTime()), server.name)
			
			# Platforms
			platforms = []
			if debugMode: platforms = indigo.List()
			
			hb = {}
			if debugMode: hb = indigo.Dict()
			
			hb["platform"] = "Indigo2"
			hb["name"] = "HomeKit Bridge Server"
			
			# The following come from the plugin prefs for where to find Indigo's API
			#hb["protocol"] = self.pluginPrefs["protocol"]
			hb["protocol"] = "http"
			hb["host"] = "127.0.0.1" # Fixed localhost only for now
			#hb["port"] = self.pluginPrefs["port"]
			#hb["apiPort"] = self.pluginPrefs["apiport"] # Arbitrary when we develop the API
			hb["port"] = self.pluginPrefs["apiport"]
			#hb["path"] = self.pluginPrefs["path"]
			#hb["username"] = self.pluginPrefs["username"]
			#hb["password"] = self.pluginPrefs["password"]
			hb["listenPort"] = server.pluginProps["listenPort"]
			hb["serverId"] = serverId
			
			#hb["includeActions"] = True
			#if len(includedActions) == 0: hb["includeActions"] = False
			
			#treatAs = {}
			#if debugMode: treatAs = indigo.Dict() # Legacy Homebridge Buddy
			
			#includeIds = []
			#if debugMode: includeIds = indigo.List()
			#for d in includedDevices:
			#	includeIds.append (d["id"])
			#	
			#	# Legacy Homebridge Buddy
			#	if "treatas" in d and d["treatas"] != "none":
			#		if not d["treatas"] in treatAs:
			#			treat = []
			#			if debugMode: treat = indigo.List()
			#		else:
			#			treat = treatAs[d["treatas"]]
			#			
			#		treat.append(d["id"])
			#		treatAs[d["treatas"]] = treat
				
			#for d in includedActions:
			#	includeIds.append (d["id"])	
			
			#hb["includeIds"] = includeIds
			
			# The following is a Homebridge Buddy legacy config for the treatAs, it's only here while the plugin is being tested and must be removed
			# prior to public release.  It simply allows me to run HomeKit bridge instead of HBB until the API is written and the Homebridge plugin
			# is rewritten to support it
			#if len(treatAs) > 0:
			#	for key, value in treatAs.iteritems():
			#		hb[key] = value
				
			platforms.append (hb)
			
			# Add any additional plaforms here...
			
			config["platforms"] = platforms
							
			if debugMode: indigo.server.log(unicode(config))
			
			return config
		
		except Exception as e:
			self.logger.error (ext.getException(e))
			
		return None
				
	################################################################################
	# INDIGO COMMAND HAND-OFFS
	#
	# Everything below here are standard Indigo plugin actions that get handed off
	# to the engine, they really shouldn't change from plugin to plugin
	################################################################################
	
	################################################################################
	# INDIGO PLUGIN EVENTS
	################################################################################		
	
	# System
	def startup(self): return eps.plug.startup()
	def shutdown(self): return eps.plug.shutdown()
	def runConcurrentThread(self): return eps.plug.runConcurrentThread()
	def stopConcurrentThread(self): return eps.plug.stopConcurrentThread()
	def __del__(self): return eps.plug.delete()
	
	# UI
	def validatePrefsConfigUi(self, valuesDict): return eps.plug.validatePrefsConfigUi(valuesDict)
	def closedPrefsConfigUi(self, valuesDict, userCancelled): return eps.plug.closedPrefsConfigUi(valuesDict, userCancelled)
	
	################################################################################
	# INDIGO DEVICE EVENTS
	################################################################################
	
	# Basic comm events
	def deviceStartComm (self, dev): return eps.plug.deviceStartComm (dev)
	def deviceUpdated (self, origDev, newDev): return eps.plug.deviceUpdated (origDev, newDev)
	def deviceStopComm (self, dev): return eps.plug.deviceStopComm (dev)
	def deviceDeleted(self, dev): return eps.plug.deviceDeleted(dev)
	def actionControlDimmerRelay(self, action, dev): return eps.plug.actionControlDimmerRelay(action, dev)
	
	# UI Events
	def getDeviceDisplayStateId(self, dev): return eps.plug.getDeviceDisplayStateId (dev)
	def validateDeviceConfigUi(self, valuesDict, typeId, devId): return eps.plug.validateDeviceConfigUi(valuesDict, typeId, devId)
	def closedDeviceConfigUi(self, valuesDict, userCancelled, typeId, devId): return eps.plug.closedDeviceConfigUi(valuesDict, userCancelled, typeId, devId)		
	
	################################################################################
	# INDIGO PROTOCOL EVENTS
	################################################################################
	def zwaveCommandReceived(self, cmd): return eps.plug.zwaveCommandReceived(cmd)
	def zwaveCommandSent(self, cmd): return eps.plug.zwaveCommandSent(cmd)
	def insteonCommandReceived (self, cmd): return eps.plug.insteonCommandReceived(cmd)
	def insteonCommandSent (self, cmd): return eps.plug.insteonCommandSent(cmd)
	def X10CommandReceived (self, cmd): return eps.plug.X10CommandReceived(cmd)
	def X10CommandSent (self, cmd): return eps.plug.X10CommandSent(cmd)

	################################################################################
	# INDIGO VARIABLE EVENTS
	################################################################################
	
	# Basic comm events
	def variableCreated(self, var): return eps.plug.variableCreated(var)
	def variableUpdated (self, origVar, newVar): return eps.plug.variableUpdated (origVar, newVar)
	def variableDeleted(self, var): return self.variableDeleted(var)
		
	################################################################################
	# INDIGO EVENT EVENTS
	################################################################################
	
	# Basic comm events
	
	# UI
	def validateEventConfigUi(self, valuesDict, typeId, eventId): return eps.plug.validateEventConfigUi(valuesDict, typeId, eventId)
	def closedEventConfigUi(self, valuesDict, userCancelled, typeId, eventId): return eps.plug.closedEventConfigUi(valuesDict, userCancelled, typeId, eventId)
		
	################################################################################
	# INDIGO ACTION EVENTS
	################################################################################
	
	# Basic comm events
	def actionGroupCreated(self, actionGroup): eps.plug.actionGroupCreated(actionGroup)
	def actionGroupUpdated (self, origActionGroup, newActionGroup): eps.plug.actionGroupUpdated (origActionGroup, newActionGroup)
	def actionGroupDeleted(self, actionGroup): eps.plug.actionGroupDeleted(actionGroup)
		
	# UI
	def validateActionConfigUi(self, valuesDict, typeId, actionId): return eps.plug.validateActionConfigUi(valuesDict, typeId, actionId)
	def closedActionConfigUi(self, valuesDict, userCancelled, typeId, actionId): return eps.plug.closedActionConfigUi(valuesDict, userCancelled, typeId, actionId)
		
	################################################################################
	# INDIGO TRIGGER EVENTS
	################################################################################
	
	# Basic comm events
	def triggerStartProcessing(self, trigger): return eps.plug.triggerStartProcessing(trigger)
	def triggerStopProcessing(self, trigger): return eps.plug.triggerStopProcessing(trigger)
	def didTriggerProcessingPropertyChange(self, origTrigger, newTrigger): return eps.plug.didTriggerProcessingPropertyChange(origTrigger, newTrigger)
	def triggerCreated(self, trigger): return eps.plug.triggerCreated(trigger)
	def triggerUpdated(self, origTrigger, newTrigger): return eps.plug.triggerUpdated(origTrigger, newTrigger)
	def triggerDeleted(self, trigger): return eps.plug.triggerDeleted(trigger)
                                   
	# UI
	
	################################################################################
	# INDIGO SYSTEM EVENTS
	################################################################################
	
	# Basic comm events
	
	# UI
	
	################################################################################
	# EPS EVENTS
	################################################################################		
	
	# Plugin menu actions
	def pluginMenuSupportData (self): return eps.plug.pluginMenuSupportData ()
	def pluginMenuSupportDataEx (self): return eps.plug.pluginMenuSupportDataEx ()
	def pluginMenuSupportInfo (self): return eps.plug.pluginMenuSupportInfo ()
	def pluginMenuCheckUpdates (self): return eps.plug.pluginMenuCheckUpdates ()
	
	# UI Events
	def getCustomList (self, filter="", valuesDict=None, typeId="", targetId=0): return eps.ui.getCustomList (filter, valuesDict, typeId, targetId)
	def formFieldChanged (self, valuesDict, typeId, devId): return eps.plug.formFieldChanged (valuesDict, typeId, devId)
	
	# UI Events For Actions Lib
	def getActionList (self, filter="", valuesDict=None, typeId="", targetId=0): return eps.ui.getActionList (filter, valuesDict, typeId, targetId)
	
	################################################################################
	# ADVANCED PLUGIN ACTIONS (v3.3.0)
	################################################################################

	# Plugin menu advanced plugin actions 
	def advPluginDeviceSelected (self, valuesDict, typeId): return eps.plug.advPluginDeviceSelected (valuesDict, typeId)
	def btnAdvDeviceAction (self, valuesDict, typeId): return eps.plug.btnAdvDeviceAction (valuesDict, typeId)
	def btnAdvPluginAction (self, valuesDict, typeId): return eps.plug.btnAdvPluginAction (valuesDict, typeId)
	
	################################################################################
	# ACTIONS FORM COMMANDS (v.4.0.0)
	################################################################################	
	
	def actionsCommandArgsChanged (self, valuesDict, typeId, devId): return eps.actv3.actionsCommandArgsChanged (valuesDict, typeId, devId)
	def actionsCommandArgsValueChanged (self, valuesDict, typeId, devId): return eps.actv3.actionsCommandArgsValueChanged (valuesDict, typeId, devId)
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	