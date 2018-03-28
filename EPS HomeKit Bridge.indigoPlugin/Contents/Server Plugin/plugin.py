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
import operator # sorting
from distutils.version import LooseVersion # version checking
import requests # get outside website data
import xml.dom.minidom # read xml for 3rd party plugin support

#from lib.httpsvr import httpServer
#hserver = httpServer(None)
#from lib import httpsvr

# New iFactory libraries
from lib import hkfactory

eps = eps(None)
HomeKit = hkfactory.HomeKitFactory(None)

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
	PLUGIN_LIBS = ["api", "homekit"] #["actions3", "cache", "plugcache", "irr"]
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
		
		HomeKit.__init__ (self)
		
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
	# Development Testing
	#
	def devTest (self):
		try:
			self.logger.warning (u"DEVELOPMENT TEST FUNCTION ACTIVE")
			
			#eps.api.startServer (self.pluginPrefs.get('apiport', '8558'))
			#eps.api.stopServer ()
			#eps.api.run (self.pluginPrefs.get('apiport', '8558'))
			
			#self.version_check()
			
			HomeKit.test()
			
			#x = eps.homekit.getServiceObject (1642494335, 1794022133, "service_ContactSensor")
			#indigo.server.log (unicode(x))
						
			#x = eps.homekit.getServiceObject (361446525, 1794022133, "service_Fanv2")
			#indigo.server.log (unicode(x))
			
			#x = eps.homekit.getServiceObject (361446525, 1794022133, "service_GarageDoorOpener")
			#indigo.server.log (unicode(x))
			
			#x = eps.homekit.getServiceObject (182494986, 1794022133, "service_Lightbulb")
			#indigo.server.log (unicode(x))
			
			#x = eps.homekit.getServiceObject (762522700, 1794022133, "service_MotionSensor")
			#indigo.server.log (unicode(x))
			
			#x = eps.homekit.getServiceObject (145155245, 1794022133, "service_Outlet")
			#indigo.server.log (unicode(x))
			
			#x = eps.homekit.getServiceObject (174276019, 1794022133, "service_LockMechanism")
			#indigo.server.log (unicode(x))
			
			#x = eps.homekit.getServiceObject (1010303036, 1794022133, "service_Switch")
			#indigo.server.log (unicode(x))
			#indigo.server.log (unicode(dir(x)))
			
			#x = eps.homekit.getServiceObject (954521198, 1794022133, "service_Thermostat")
			#indigo.server.log (unicode(x))
			
			#x = eps.homekit.getServiceObject (558499318, 1794022133, "service_Speaker")
			#indigo.server.log (unicode(x))
			
			#x = eps.homekit.getServiceObject (658907852, 1794022133, "service_BatteryService")
			#indigo.server.log (unicode(x))
			
			#x = eps.homekit.getServiceObject (1021929362, 1794022133, "service_WindowCovering")
			#indigo.server.log (unicode(x))
			
			#for a in x.actions:
				#if a.characteristic == "Mute" and not a.whenvalue:
				#	a.run ("false", 558499318, False)
				#	break
				
			#	if a.characteristic == "Volume":
			#		a.run ("75", 558499318, True)
			#		break
			
			#x = eps.homekit.getHomeKitServices ()
			#indigo.server.log (unicode(x))
			
			#self.complicationTestOutput()
			
			#self.migrateFromHomebridgeBuddy()
			
			pass
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
	#
	# Plugin startup
	#
	def onAfter_startup (self):
		try:
			# Only uncomment this when new characteristics have been added so the class lookup can be printed
			#eps.homekit.printClassLookupDict()
			
			# Start the httpd listener
			eps.api.startServer (self.pluginPrefs.get('apiport', '8558'))
			
			# Set up the config path in the Indigo preferences folder
			self.CONFIGDIR = '{}/Preferences/Plugins/{}'.format(indigo.server.getInstallFolderPath(), self.pluginId)
			self.logger.debug (u"Config path set to {}".format(self.CONFIGDIR))
			
			# Just to be safe, check for our configdir on startup, this should fix issues where new installs can't start a server until reloading
			if not os.path.exists (self.CONFIGDIR):
				os.makedirs (self.CONFIGDIR)
				
				if not os.path.exists (self.CONFIGDIR):
					self.logger.error (u"Unable to create the configuration folder under '{0}', '{1}' will be unable to run until this issue is resolved.  Please verify permissions and create the folder by hand if needed.".format(self.CONFIGDIR, dev.name))
			
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
			
			#self.serverListHomeKitDeviceTypes (None, None)
				
			#if len(self.SERVERS) == 0:
			#	self.logger.info (u"No servers detected, attempting to migrate from Homebridge-Indigo and/or Homebridge Buddy if they are installed and enabled")
			#	self.migrateFromHomebridgeBuddy()
				
			if "hiddenIds" in self.pluginPrefs:
				hidden = json.loads (self.pluginPrefs["hiddenIds"])
				plural = ""
				if len(hidden) > 1: plural = "s"
				
				msg = eps.ui.debugHeader ("HOMEKIT BRIDGE HIDDEN ITEMS WARNING")
				msg += eps.ui.debugLine ("You have {} Indigo item{} being hidden, you can manage these ".format(str(len(hidden)), plural))
				msg += eps.ui.debugLine ("from the plugin menu.")
				msg += eps.ui.debugHeaderEx ()
				
				self.logger.warning (msg)
				
			self.version_check()
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
			
	#
	# Check plugin store version
	#		
	def version_check(self):
		return
		# Create some URLs we'll use later on
		pluginId = self.pluginId
		current_version_url = "https://api.indigodomo.com/api/v2/pluginstore/plugin-version-info.json?pluginId={}".format(pluginId)
		store_detail_url = "https://www.indigodomo.com/pluginstore/{}/"
		try:
			# GET the url from the servers with a short timeout (avoids hanging the plugin)
			reply = requests.get(current_version_url, timeout=5)
			# This will raise an exception if the server returned an error
			reply.raise_for_status()
			# We now have a good reply so we get the json
			reply_dict = reply.json()
			plugin_dict = reply_dict["plugins"][0]
			# Make sure that the 'latestRelease' element is a dict (could be a string for built-in plugins).
			latest_release = plugin_dict["latestRelease"]
			if isinstance(latest_release, dict):
				# Compare the current version with the one returned in the reply dict
				if LooseVersion(latest_release["number"]) > LooseVersion(self.pluginVersion):
					# The release in the store is newer than the current version.
					# We'll do a couple of things: first, we'll just log it
					self.logger.error(
						"A new version of HomeKit Bridge (v{}) is available at: {}".format(
							latest_release["number"],
							store_detail_url.format(plugin_dict["id"])
						)
					)
					# We'll change the value of a variable named "Plugin_Name_Current_Version" to the new version number
					# which the user can then build a trigger on (or whatever). You could also insert the download URL,
					# the store URL, whatever.
					try:
						variable_name = "{}_Current_Version".format(self.pluginDisplayName.replace(" ", "_"))
						indigo.variable.updateValue(variable_name, latest_release["number"])
					except:
						pass
					# We'll execute an action group named "New Version for Plugin Name". The action group could
					# then get the value of the variable above to do some kind of notification.
					try:
						action_group_name = "New Version for {}".format(self.pluginDisplayName)
						indigo.actionGroup.execute(action_group_name)
					except:
						pass
					# There are lots of other things you could do here. The final thing we're going to do is send
					# an email to self.version_check_email which I'll assume that you've set from the plugin
					# config.
					if hasattr(self, 'version_check_email') and self.version_check_email:
						indigo.server.sendEmailTo(
							self.version_check_email, 
							subject="New version of Indigo Plugin '{}' is available".format(self.pluginDisplayName),
							body="It can be downloaded here: {}".format(store_detail_url)
						)
						
				else:
					self.logger.info("HomeKit Bridge is running the latest version, no update needed")

				
		except Exception as e:
			self.logger.error (ext.getException(e))			
			
			
	#
	# Compose and output a sample complication (pseudo documentation)
	#
	def complicationTestOutput (self):
		try:
			complications = []
			
			#########################
			# Sample of one to many #
			#########################
			
			# Complication Data
			complication = {}
			complication["name"] 			= "Indigo Thermostat and Fan"
			complication["deviceIds"] 		= []
			complication["method"]	 		= 0 # One to many
			complication["devId"]	 		= 12345
			complication["indigoDevTypes"]	= ["indigo.ThermostatDevice"] # Only if these are found, an * anywhere will fall to conditions
			complication["criteriaScope"]	= "indigo.devices"
			complication["criteria"]		= []
						
			members = []
			
			# The Thermostat
			member = {}
			member["type"]					= 0 # Same device
			member["object"]				= "state_temperatureInput1"
			member["service"]				= "Thermostat"
			member["prefix"]				= ""
			member["suffix"]				= ""
			member["lookup"]				= []
			member["characteristics"]		= {}
			member["actions"]				= []
			
			members.append(member)
			
			# The Fan
			member = {}
			member["type"]					= 0 # Same device
			member["object"]				= "attr_fanIsOn"
			member["service"]				= "Fanv2"
			member["prefix"]				= ""
			member["suffix"]				= " (Fan)"
			member["lookup"]				= []
			
			characteristics = {} # For demonstration purposes, if left blank then use plugin defaults
			characteristics["active"]				= {"indigo.ThermostatDevice": "attr_fanIsOn"}
			characteristics["CurrentFanState"]		= {"indigo.ThermostatDevice": "special_thermFanMode"}
			
			member["characteristics"]		= characteristics
			
			actions = [] # For demonstration purposes, if left blank then use plugin defaults
			
			# First action condition
			action = {}
			action["characteristic"]		= "Active"
			action["qualifier"]				= "equal"
			action["value"]					= True
			action["highValue"]				= None
			action["command"]				= "thermostat.setFanMode"
			action["args"]					= ["=memberDevId=", indigo.kFanMode.Auto]
			
			actions.append (action)
			
			# Second action condition
			action = {}
			action["characteristic"]		= "Active"
			action["qualifier"]				= "equal"
			action["value"]					= False
			action["highValue"]				= None
			action["command"]				= "thermostat.setFanMode"
			action["args"]					= ["=memberDevId=", indigo.kFanMode.AlwaysOn]
			
			actions.append (action)
			
			member["actions"]				= actions
						
			members.append(member)
			
			# Add all members to complication
			complication["members"] 		= members
			
			# Add complication to all complications
			complications.append(complication)
			
			##########################
			# Sample of many to many #
			##########################
			
			complication = {}
			complication["name"] 			= "Fibaro Motion Sensor FBGS001"
			complication["deviceIds"] 		= []
			complication["method"]	 		= 1 # Many to many
			complication["devId"]	 		= 12345
			complication["indigoDevTypes"]	= [] # Empty means analyse all against criteria
			complication["criteriaScope"]	= "indigo.devices"
			
			allcriteria = [] # If more than one then it is always AND, if OR is needed then create another complication with THOSE criteria
			
			# 1st Criteria
			criteria = {}
			criteria["object"]				= "attr_model"
			criteria["qualifier"]			= "contains"
			criteria["value"]				= "FGS001"
			
			allcriteria.append(criteria)
			
			#2nd Criteria (AND)
			criteria = {}
			criteria["object"]				= "attr_model"
			criteria["qualifier"]			= "contains"
			criteria["value"]				= "Motion Sensor"
			
			allcriteria.append(criteria)
			
			complication["criteria"]		= allcriteria
			
			members = []
			
			# The Motion Sensor
			member = {}
			member["type"]					= 0
			member["object"]				= "attr_onState"
			member["service"]				= "MotionSensor"
			member["prefix"]				= ""
			member["suffix"]				= ""
			member["lookup"]				= []
			member["characteristics"]		= {}
			member["actions"]				= []
			
			members.append(member)
			
			# The Light Sensor
			member = {}
			member["type"]					= 1 # Device lookup
			member["object"]				= "attr_onState"
			member["service"]				= "LightSensor"
			member["prefix"]				= ""
			member["suffix"]				= " (Lux)"
			
			lookups = [] # If more than one then it is always AND, if OR is needed then create another complication with THOSE criteria
			
			# 1st Criteria
			lookup = {}
			lookup["object"]				= "attr_address"
			lookup["qualifier"]				= "equal"
			lookup["value"]					= "=address="
			
			lookups.append(lookup)
			
			# 2nd Criteria
			lookup = {}
			lookup["object"]				= "attr_model"
			lookup["qualifier"]				= "contains"
			lookup["value"]					= "FGS001"
			
			lookups.append(lookup)
			
			# 3rd Criteria
			lookup = {}
			lookup["object"]				= "attr_model"
			lookup["qualifier"]				= "contains"
			lookup["value"]					= "Luminance"
			
			lookups.append(lookup)
			
			member["lookup"]				= lookups
			
			member["characteristics"]		= {}
			member["actions"]				= []
			
			members.append(member)
			
			# The Temperature Sensor
			member = {}
			member["type"]					= 1 # Device lookup
			member["object"]				= "attr_onState"
			member["service"]				= "TemperatureSensor"
			member["prefix"]				= ""
			member["suffix"]				= " (Temp)"
			
			lookups = [] # If more than one then it is always AND, if OR is needed then create another complication with THOSE criteria
			
			# 1st Criteria
			lookup = {}
			lookup["object"]				= "attr_address"
			lookup["qualifier"]				= "equal"
			lookup["value"]					= "=address="
			
			lookups.append(lookup)
			
			# 2nd Criteria
			lookup = {}
			lookup["object"]				= "attr_model"
			lookup["qualifier"]				= "contains"
			lookup["value"]					= "FGS001"
			
			lookups.append(lookup)
			
			# 3rd Criteria
			lookup = {}
			lookup["object"]				= "attr_model"
			lookup["qualifier"]				= "contains"
			lookup["value"]					= "Temperature"
			
			lookups.append(lookup)
			
			member["lookup"]				= lookups
			
			member["characteristics"]		= {}
			member["actions"]				= []
			
			members.append(member)
			
			# Add all members to complication
			complication["members"] 		= members
			
			# Add complication to all complications
			complications.append(complication)
			
			
			
			# Output
			indigo.server.log(unicode(json.dumps(complications, indent = 4)))
			indigo.server.log(unicode(json.dumps(complications)))
		
		except Exception as e:
			self.logger.error (ext.getException(e))		
			
	#
	# Plugin upgraded
	#
	def pluginUpgraded (self, lastVersion, currentVersion):
		try:
			lastmajor, lastminor, lastrev = lastVersion.split(".")
			
			if lastVersion == "0.0.1": # Prior to adding version to prefs
				self.logger.info (u"Upgrading plugin to {}".format(currentVersion))
			else:
				self.logger.info (u"Upgrading plugin from {} to {}".format(lastVersion, currentVersion))
				
			if "enableComplications" in self.pluginPrefs: del (self.pluginPrefs["enableComplications"])
			if "enableComplicationsDialogs" in self.pluginPrefs: del (self.pluginPrefs["enableComplicationsDialogs"])
			
			for dev in indigo.devices.iter(self.pluginId + ".Server"):
				props = dev.pluginProps
				changed = False
				
				if props["device"] != "": 	
					props["device"] = "" # Force "-FILL-" out of the system so it will populate a device
					changed = True
					
				if "filterIncluded" in props:
					del (props["filterIncluded"])
					changed = True
					
				if "objectAction" in props:
					props["objectAction"] = "add" # New default setting
					changed = True
				
				# 0.17.6	
				if "configOption" in props and props["configOption"] != "include":
					props["configOption"] = "include" 
					changed = True
					
				# 0.17.6	
				if not "modelValue" in props:
					props["modelValue"] = "indigoSubmodel"
					changed = True
					
				# 0.17.6
				if not "firmwareValue" in props:
					props["firmwareValue"] = "indigoVersion"
					changed = True
					
				# 0.19.10
				if not "SupportsStatusRequest" in props:
					props["SupportsStatusRequest"] = False
					changed = True
					
				if changed: 
					self.logger.info (u"Upgrading {} for changes in this plugin release".format(dev.name))
					dev.replacePluginPropsOnServer(props)
				
			
		except Exception as e:
			self.logger.error (ext.getException(e))		
			return False
			
		return True
			
	#
	# Plugin shutdown
	#
	def onAfter_shutdown (self):		
		try:
			# Shut down ALL servers if they are running (since the API doesn't work when the plugin is not running anyway)
			msg = eps.ui.debugHeader ("HOMEKIT BRIDGE RUNNING SERVER SHUTDOWN")
			msg += eps.ui.debugLine ("Now blind stopping all running servers, due to Indigo timeout ")
			msg += eps.ui.debugLine ("limits the plugin cannot wait for them to stop but will instead ")
			msg += eps.ui.debugLine ("shut them down blindly and let them refresh when the plugin ")
			msg += eps.ui.debugLine ("restarts")
			msg += eps.ui.debugHeaderEx ()
			haswarned = False
			
			for dev in indigo.devices.iter(self.pluginId + ".Server"):
				if dev.states["onOffState"]: 
					if not haswarned:
						self.logger.warning (msg)
						haswarned = True
					self.shellHBStopServer (dev, False, True)
			
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
						self.logger.info (u"Server '{}' has successfully started, you can use your HomeKit apps or Siri for this accessory".format(indigo.devices[devId].name))
					
						# Remove this from the list so we don't check anymore
						newList = []
						for d in self.SERVER_STARTING:
							if d == devId: continue
							newList.append (d)
						
						self.SERVER_STARTING = newList
					
				#if len(self.SERVER_STARTING) > 0 and self.STICKS > 30:
				#	for devId in self.SERVER_STARTING:
				#		self.logger.info (u"Server '{}' has not responded to a start request after more than 30 seconds, forcing an abort on the startup".format(indigo.devices[devId].name))
				#		self.shellHBStopServer (indigo.devices[devId])
				#		
				#	self.STICKS = 0
					
			except Exception as e:
				self.logger.error (ext.getException(e))		
		
		# At 30 ticks we check server running state (more or less between 30 seconds and a minute but keeps us from having to do date calcs here which use CPU)
		if self.CTICKS == 30:
			try:
				#self.logger.debug (u"Checking running state of all servers")
				for dev in indigo.devices.iter(self.pluginId + ".Server"):
					self.checkRunningHBServer (dev)
			
				self.CTICKS = 0
				
			except Exception as e:
				self.logger.error (ext.getException(e))	
				
		# Check updates every day at 10:00am
		dateSTR = datetime.datetime.now().strftime("%H:%M:%S" )
		if dateSTR == ("10:00:00"):	
			self.version_check()
			
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
	# Plugin configuration dialog validation
	#
	def onAfter_validatePrefsConfigUi(self, valuesDict):
		errorsDict = indigo.Dict()
		success = True
		
		try:
			# Basic defaults if they left it blank
			if valuesDict["lowbattery"] == "" or valuesDict["lowbattery"] == "0": valuesDict["lowbattery"] = "20"
			if valuesDict["bitrate"] == "" or valuesDict["bitrate"] == "0": valuesDict["bitrate"] = "300"
			if valuesDict["packetsize"] == "" or valuesDict["packetsize"] == "0": valuesDict["packetsize"] = "1316"
			
			# Validate the packet size since it has to be in increments of 188
			packetPasses = False
			for i in range (188, 1317, 188):
				if int(valuesDict["packetsize"]) == i:
					packetPasses = True
					break
					
			if not packetPasses:
				errorsDict["showAlertText"] = "Packet sizes must be in increments of 188.  Please set the packet size to be an increment of 188 up to a maximum of 1316."
				errorsDict["packetsize"] = "Invalid value"
				return (False, valuesDict, errorsDict)	
				
			if len(self.SERVER_STARTING) > 0:
				errorsDict["showAlertText"] = "You still have servers that are trying to start, unable to save plugin preferences until all servers have finished starting."
				return (False, valuesDict, errorsDict)		
				
			if valuesDict["bitrate"] != self.pluginPrefs.get("bitrate", "300") or valuesDict["packetsize"] != self.pluginPrefs.get("packetsize", "1316") or valuesDict["cameradebug"] != self.pluginPrefs.get("cameradebug", False):
				for dev in indigo.devices.iter(self.pluginId + ".Server"):
					needsRestart = False
					if "includedDevices" in dev.pluginProps:
						objects = json.loads(dev.pluginProps["includedDevices"])	
						for r in objects:
							if r["hktype"] == "service_CameraRTPStreamManagement":
								needsRestart = True
								break

					if needsRestart:
						thread.start_new_thread(self.restartRunningServer, (dev,))
										
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return (success, valuesDict, errorsDict)
			
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
	# Device delete
	#
	def onAfter_nonpluginDeviceDeleted (self, dev):		
		try:
			if dev.id in self.SERVER_ID:
				self.logger.warning (u"Indigo device {} was removed and is linked to HomeKit, removing from any impacted servers".format(dev.name))
				
				for serverId in self.SERVER_ID[dev.id]:
					if serverId not in indigo.devices:
						self.logger.debug (u"Server ID {} has been removed from Indigo but is still in cache, ignoring this update and removing it from cache to avoid further message or false positives".format(str(serverId)))
						rebuildRequired = True
						continue
						
					valuesDict = self.serverCheckForJSONKeys (indigo.devices[serverId].pluginProps)	
					includedDevices = json.loads(valuesDict["includedDevices"])
					includedActions = json.loads(valuesDict["includedActions"])
					
					includedDevices = eps.jstash.removeRecordFromStash (includedDevices, "id", dev.id)
					includedActions = eps.jstash.removeRecordFromStash (includedActions, "id", dev.id)
					
					props = indigo.devices[serverId].pluginProps
					props["includedDevices"] = json.dumps(includedDevices)
					props["includedActions"] = json.dumps(includedActions)				
					indigo.devices[serverId].replacePluginPropsOnServer(props)
					
				self.catalogServerDevices() # Reindex everything
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
			
	#
	# Device update
	#
	def onAfter_nonpluginDeviceUpdated (self, origDev, newDev):
		try:
			# If this is the stupid NEST thermostat that updates every damn second then ignore most changes
			if newDev.pluginId == "com.corporatechameleon.nestplugBeta":
				#self.logger.debug (u"Idiotic NEST plugin updating 8-12 states every 1 second, ignoring")
				wecareabout = ["coolSetpoint", "hvacMode", "temperatures", "heatSetpoint", "humidities"]
				youshallnotpass = True
				for w in wecareabout:
					if w in dir(origDev):
						o = getattr(origDev, w)
						n = getattr(newDev, w)
						if o != n: youshallnotpass = False
					
				if youshallnotpass: return
				
			rebuildRequired = False
				
			#indigo.server.log (newDev.name)
			if newDev.id in self.SERVER_ID:
				try:
					self.logger.debug (u"Indigo device {} changed and is linked to HomeKit, checking if that change impacts HomeKit".format(unicode(newDev.name)))
				except:
					pass
					
				devId = newDev.id
				
				
				for serverId in self.SERVER_ID[devId]:
					if serverId not in indigo.devices:
						self.logger.debug (u"Server ID {} has been removed from Indigo but is still in cache, ignoring this update and removing it from cache to avoid further message or false positives".format(str(serverId)))
						rebuildRequired = True
						continue
						
					valuesDict = self.serverCheckForJSONKeys (indigo.devices[serverId].pluginProps)	
					includedDevices = json.loads(valuesDict["includedDevices"])
					includedActions = json.loads(valuesDict["includedActions"])
					
					r = eps.jstash.getRecordWithFieldEquals (includedDevices, "id", devId)
					if r is None: r = eps.jstash.getRecordWithFieldEquals (includedActions, "id", devId)
					if r is None: continue
					
					# See if this is an API linked device and update the server stash if it is
					#if self.apiDeviceIsLinked (devId):
					#	r["hktype"] = newDev.ownerProps["voiceHKBDeviceType"]
					#	r["alias"] = newDev.ownerProps["voiceAlias"]
				
					
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
												
									if monitor[0:6] == "state_": # If it is an state
										action = monitor.replace("state_", "")
										if action in newDev.states and action in origDev.states:
											n = newDev.states[action]
											o = origDev.states[action]
											
											if n != o:
												updateRequired = True
												break
												
												
					if updateRequired:
						self.logger.debug (u"Device {} had an update that HomeKit needs to know about".format(obj.alias.value))
						#self.serverSendObjectUpdateToHomebridge (indigo.devices[serverId], newDev.id)
						self.serverSendObjectUpdateToHomebridge (indigo.devices[serverId], r["jkey"])
						
			if rebuildRequired:
				self.catalogServerDevices()
					
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
			
	#
	# Plugin device created
	#
	def onAfter_pluginDeviceCreated (self, dev):
		try:
			indigo.server.log ("NEW DEVICE")
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
						self.logger.error (u"Unable to stop '{}' before it was deleted, you may need to restart your Mac to make sure it isn't running any longer".format(dev.name))
						
				# Remove the folder structure
				if os.path.exists (self.CONFIGDIR + "/" + str(dev.id)):
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



	#
	# Advanced Device Actions
	#
	def onAfter_btnAdvDeviceAction (self, valuesDict, typeId):	
		try:
			if valuesDict["deviceActions"] == "hblog": 
				server = indigo.devices[int(valuesDict["device"])]
				
				startpath = self.CONFIGDIR + "/" + str(server.id)
			
				# Failsafe to make sure we have a server folder
				if not os.path.exists (startpath):
					self.logger.error (u"Unable to find a configuration folder for this server in {}".format(startpath))
					return
			
				if os.path.exists (startpath):
					filepath = startpath + "/homebridge.log"
					if os.path.isfile(filepath):
						file = open(filepath, 'r')
						logdetails = file.read()
					else:
						self.logger.error (u"Unable to open the Homebridge log at {}.  This is likely because Homebridge has tried to start, as any attempt to start Homebridge should result in a log file".format(filepath))
						return
											
					self.logger.info (logdetails)
					
			if valuesDict["deviceActions"] == "hbconfig": 
				server = indigo.devices[int(valuesDict["device"])]
				
				startpath = self.CONFIGDIR + "/" + str(server.id)
			
				# Failsafe to make sure we have a server folder
				if not os.path.exists (startpath):
					self.logger.error (u"Unable to find a configuration folder for this server in {}".format(startpath))
					return
			
				if os.path.exists (startpath):
					filepath = startpath + "/config.json"
					if os.path.isfile(filepath):
						file = open(filepath, 'r')
						logdetails = file.read()
					else:
						self.logger.error (u"Unable to open the Homebridge configuration at {}.  This indicates that the configuration was unable to write to this folder or there may be a filesystem problem.".format(filepath))
						return
											
					self.logger.info (logdetails)		
					
			if valuesDict["deviceActions"] == "rebuild": 
				server = indigo.devices[int(valuesDict["device"])]
				
				self.rebuildHomebridgeFolder (server)
				
				self.logger.warning (u"Homebridge folder for {} at {} has been rebuilt".format(server.name, self.CONFIGDIR + "/" + str(server.id)))
				
			if valuesDict["deviceActions"] == "simhomekit":
				serverProps = self.serverCheckForJSONKeys (indigo.devices[int(valuesDict["device"])].pluginProps)	
				includedDevices = json.loads(serverProps["includedDevices"])
				includedActions = json.loads(serverProps["includedActions"])
				
				r = eps.jstash.getRecordWithFieldEquals (includedDevices, "id", int(valuesDict["simdevice"]))
				if r is None: r = eps.jstash.getRecordWithFieldEquals (includedActions, "id", int(valuesDict["simdevice"]))
				if r is None: 
					self.logger.error (u"Unable to simuluate server item because it could not be found in the stash")
					return
				
				valuesDict["showall"] = True
				valuesDict["device2"] = valuesDict["simdevice"]
				valuesDict["hkType"] = r["hktype"]
				self.onAfter_btnAdvPluginAction_Simulate (valuesDict, typeId, int(valuesDict["device"]))
			
				
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
	#
	# Get list of devices attached to a server
	#
	def onAfter_btnAdvDeviceAction_GetAttachedJSONDevices (self, args, valuesDict):	
		try:
			if "device" not in valuesDict: return [("default", "No data")]	
			if valuesDict["device"] == "": return [("default", "No data")]	
			if "deviceActions" not in valuesDict: return [("default", "No data")]	
			if valuesDict["deviceActions"] != "simhomekit": return [("default", "No data")]	
			
			server = indigo.devices[int(valuesDict["device"])]
			return self.serverListJSONDevices (None, server.pluginProps)
			
		except Exception as e:
			self.logger.error (ext.getException(e))			
			return [("default", "No data")]	
			
	#
	# Advanced Plugin Actions
	#
	def onAfter_btnAdvPluginAction (self, valuesDict, typeId):	
		try:
			if valuesDict["pluginActions"] == "migratehbb": self.migrateFromHomebridgeBuddy()
			if valuesDict["pluginActions"] == "simhomekit": self.onAfter_btnAdvPluginAction_Simulate (valuesDict, typeId)
				
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
	#
	# Run advanced plugin action to simulate a homekit device
	#
	def onAfter_btnAdvPluginAction_Simulate (self, valuesDict, typeId, serverId = 0):
		try:
			dev = indigo.devices[int(valuesDict["device2"])]
						
			self.logger.info (u"Simulating HomeKit values for {}".format(dev.name))
			
			if valuesDict["showall"]:
				self.logger.info (u"##### DEVICE DATA DUMP #####")
				self.logger.info (unicode(dev))
			
			self.logger.info (u"##### DEVICE SIMULATION DATA #####")
			x = eps.homekit.getServiceObject (dev.id, serverId, valuesDict["hkType"])
			
			if valuesDict["invert"]:
				#self.logger.info (u"##### INVERT IS TRUE #####")
				x.invertOnState = True
				x.setAttributes()
			
			if valuesDict["fahrenheit"]:
				#self.logger.info (u"##### FAHRENHEIT IS TRUE #####")
				x.convertFahrenheit = True
				x.setAttributes()	
				
			self.logger.info (unicode(x))
			
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
					
					# Invert if configured - Now in library
					#if "invert" in r: 
					#	obj.invertOnState = r["invert"]
					#	if obj.invertOnState: obj.setAttributes() # Force it to refresh values so we get our inverted action
					
					# Loop through actions to see if any of them are in the query
					processedActions = False
					response = False
					thisCharacteristic = None
					thisValue = None
					#indigo.server.log(unicode(obj))
					for a in obj.actions:
						#indigo.server.log(unicode(a))
						#indigo.server.log("Checking if {} is in {}".format(a.characteristic, unicode(query)))
						if a.characteristic in query and not processedActions: 
							self.logger.debug (u"Received {} in query, setting to {} using {} if rules apply".format(a.characteristic, query[a.characteristic][0], a.command))
							#processedActions.append(a.characteristic)
							#ret = a.run (query[a.characteristic][0], r["id"], True)
							
							thisCharacteristic = a.characteristic
							thisValue = query[a.characteristic][0]
							ret = a.run (thisValue, r["id"])
							#self.HKREQUESTQUEUE[obj.id] = a.characteristic # It's ok that this overwrites, it's the same
							if ret: 
								response = True # Only change it if its true, that way we know the operation was a success
								processedActions = True
								break # we only ever get a single command on each query
										
					r = self.buildHKAPIDetails (devId, serverId, r["jkey"], thisCharacteristic, thisValue, isAction)		
					return "text/css",	json.dumps(r, indent=4)
				
				if "cmd" in query and query["cmd"][0] == "getInfo":
					if "objId" in query:
						devId = int(query["objId"][0])
						jkey = query["jkey"][0]
			
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
						
						r = self.buildHKAPIDetails (devId, serverId, jkey)
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
							r = self.buildHKAPIDetails (d["id"], serverId, d["jkey"])
							if r is not None and len(r) > 0: ret.append (r)
							
						for a in includedActions:
							r = self.buildHKAPIDetails (a["id"], serverId, a["jkey"])
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
	# Compose the type and versByte from server details
	#
	def getHKAPIModel (self, server, r):
		try:
			if r["object"] != "Action":
				if "model" in r and r["model"] != "":
					r["type"] = r["model"]
					del(r["model"])
				elif "modelValue" in server.pluginProps:
					r["type"] = self._getHKAPIModelData (r, server.pluginProps["modelValue"])
				else:
					r["type"] = indigo.devices[r["id"]].model
				
				if "firmware" in r and r["firmware"] != "":
					r["versByte"] = r["firmware"]
					del(r["firmware"])	
				elif "firmwareValue" in server.pluginProps:
					r["versByte"] = self._getHKAPIModelData (r, server.pluginProps["firmwareValue"])
				else:	
					r["versByte"] = indigo.devices[r["id"]].pluginId
					
			else:
				r["type"] = "Action Group"
				r["versByte"] = ""
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return r
		
	#
	# Compose the type and versByte from server details
	#
	def _getHKAPIModelData (self, r, value):
		try:			
			if value == "indigoModel":
				return u"{}".format(indigo.devices[r["id"]].model)
			elif value == "indigoModelSubmodel":
				return u"{}: {}".format(indigo.devices[r["id"]].model, indigo.devices[r["id"]].subModel)
			elif value == "indigoName":
				return u"{}".format(indigo.devices[r["id"]].name)
			elif value == "indigoType":
				return u"{}".format(str(type(indigo.devices[r["id"]])).replace("<class '", "").replace("'>", "").replace("indigo.",""))
			elif value == "pluginName":
				if indigo.devices[r["id"]].pluginId != "":
					plugin = indigo.server.getPlugin(indigo.devices[r["id"]].pluginId)
					#indigo.server.log(unicode(plugin))
					return u"{}".format(plugin.pluginDisplayName)
				else:
					return "Indigo"
			elif value == "pluginType":
				if indigo.devices[r["id"]].deviceTypeId != "":
					return u"{}".format(indigo.devices[r["id"]].deviceTypeId)	
				else:
					return u"{}".format(str(type(indigo.devices[r["id"]])).replace("<class '", "").replace("'>", "").replace("indigo.",""))
			elif value == "pluginVersion":
				if indigo.devices[r["id"]].pluginId != "":
					plugin = indigo.server.getPlugin(indigo.devices[r["id"]].pluginId)
					#indigo.server.log(unicode(plugin))
					return u"{}".format(plugin.pluginVersion)	
				else:
					return u"{}".format(indigo.server.version)
			elif value == "indigoVersion":
				return u"{}".format(indigo.devices[r["id"]].version)			
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return ""
			
	#
	# Build HK API details for object ID
	#
	def buildHKAPIDetails (self, objId, serverId, jkey, characteristic = None, value = None, runningAction = False):
		try:
			#http://10.1.200.3:8558/HomeKit?cmd=deviceList&serverId=1794022133
			valuesDict = self.serverCheckForJSONKeys (indigo.devices[serverId].pluginProps)	
			includedDevices = json.loads(valuesDict["includedDevices"])
			includedActions = json.loads(valuesDict["includedActions"])
			
			r = eps.jstash.getRecordWithFieldEquals (includedDevices, "jkey", jkey)
			#if r is None: r = eps.jstash.getRecordWithFieldEquals (includedActions, "id", objId)
			if r is None: r = eps.jstash.getRecordWithFieldEquals (includedActions, "jkey", jkey)
			
			# Create an HK object so we can get all default data
			self.logger.threaddebug (u"Looking for HomeKit class {}".format(r["hktype"]))
			services = eps.homekit.getHomeKitServices()
			if r["hktype"] not in services:
				self.logger.error (u"Server '{}' device '{}' is trying to reference a HomeKit class of {} that isn't defined.".format(indigo.devices[serverId].name, r["alias"], r["hktype"]))
				return []
			if r["hktype"] == "service_CameraRTPStreamManagement": return []  # Cameras are handled in the config build because it has its own platform
			
			obj = eps.homekit.getServiceObject (r["id"], serverId, r["hktype"], False, True)
			server = indigo.devices[int(serverId)]
			
			#if r["id"] == 145155245: HomeKit.legacy_get_payload (obj, r, serverId)
			
			# Invert if configured
			#if "invert" in r: 
			#	obj.invertOnState = r["invert"]
			#	if obj.invertOnState: obj.setAttributes() # Force it to refresh values so we get our inverted onState
			
			# Add model and firmware
			r = self.getHKAPIModel (server, r)
				
			# Add the callback
			r["url"] = "/HomeKit?objId={}&serverId={}&jkey={}".format(str(objId), str(serverId), jkey)	
			
			# Fix characteristics for readability
			charList = []
			for charName, charValue in obj.characterDict.iteritems():
				charItem = {}
				
				if charName not in dir(obj):
					self.logger.error (u"Unable to find attribute {} in {}: {}".format(charName, obj.alias.value, unicode(obj)))
					continue
					
				characteristic = getattr (obj, charName)
				charItem["name"] = charName
				charItem["value"] = charValue
				
				if runningAction and charItem["name"] == "On": charItem["value"] = True
				if not characteristic is None and not value is None and charItem["name"] == characteristic: charItem["value"] = value # Force it to see what it expects to see so it doesn't beachball
				
				charItem["readonly"] = characteristic.readonly
				charItem["notify"] = characteristic.notify
				charList.append (charItem)
				
			r["hkcharacteristics"] = charList
			
			# Fix up for output
			r["hkservice"] = r["hktype"].replace("service_", "")
			del r["hktype"]
			#del r["jkey"]
			#del r["type"]
			del r["char"]
			if "invert" in r: del r["invert"]
			
			# Fix actions for readability
			actList = []
			for a in obj.actions:
				if not a.characteristic in actList: actList.append(a.characteristic)
				
			r["action"] = actList
			
			# This will only come up if an action group was turned on and then called down to here so this should be safe, but we need to now
			# notify Homebridge that the action has completed and to get the false value
			if runningAction:
				#self.serverSendObjectUpdateToHomebridge (indigo.devices[int(serverId)], r["id"])
				#thread.start_new_thread(self.timedCallbackToURL, (serverId, r["id"], 2))
				thread.start_new_thread(self.timedCallbackToURL, (serverId, r["jkey"], 2))
			
			if obj.recurringUpdate:
				thread.start_new_thread(self.timedCallbackToURL, (serverId, r["jkey"], obj.recurringSeconds))	
			
			
			# Before we return r, use the jstash ID for our ID instead of the Indigo ID
			r["deviceId"] = r["id"] # So we still have it
			r["id"] = r["jkey"]
			del r["jkey"]
			
			# Fix up the alias name for any problematic characters
			alias = unicode(r["alias"])
			try:
				alias = r"{}".format(alias)
			except:
				alias = unicode(r["alias"])
				
			r["alias"] = alias
			
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
	# API
	################################################################################	
	
	#
	# Check if a given device is API enabled
	#
	def apiDeviceIsLinked (self, devId):
		try:
			#if str(devId) == "-fill-" or str(devId) == "-line-": return False
			if int(devId) not in indigo.devices: return False
			dev = indigo.devices[int(devId)]
			
			if "voiceIntegrated" in dev.ownerProps and dev.ownerProps["voiceIntegrated"]:
				if "voiceIntegration" in dev.ownerProps and (dev.ownerProps["voiceIntegration"] == "ALL" or dev.ownerProps["voiceIntegration"] == "HomeKit"):
					if "voiceHKBAvailable" in dev.ownerProps and dev.ownerProps["voiceHKBAvailable"]:
						return True
			
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return False
	
	#
	# Server API commands
	#
	def apiCall (self, action):
		try:	
			success = True
			errors = indigo.Dict()
			data = indigo.Dict() # Default, can be changed as needed
			payload = {}
			
			props = action.props
			
			libversion = props["libversion"]
			libver = libversion.split(".")
			if int(libver[0]) < 1:
				errors["param"] = "libversion"
				errors["message"] = "The version of HomeKit Bridge you have installed requires an API lib version of 1.0.0.  Please upgrade your plugin to the latest version or contact the plugin developer so that they can update to the latest Indigo Voice API."
				return (False, data, payload, errors)	
				
			self.logger.debug (u"Received {} API request".format(props["command"]))
				
			if props["command"] == "getServerList":
				#indigo.server.log(unicode(props))
				if "devId" not in props:
					errors["param"] = "devId"
					errors["message"] = "HomeKit Bridge Voice API received the '{0}' command, but the device ID was not passed.  Unable to complete API call.".format(props["command"])
					return (False, data, payload, errors)
				
				data = []
				
				for dev in indigo.devices.iter(self.pluginId + ".Server"):
					data.append( (str(dev.id), dev.name) )			
					
			elif props["command"] == "getDeviceTypes":
				services = eps.homekit.getHomeKitServices ()
				sortedservices = sorted(services.items(), key=operator.itemgetter(0))
			
				data = []
			
				valuesDict = {}
				validTypes = {}
				
				if "valuesDict" in props: valuesDict = props["valuesDict"]
				
				if "voiceHKBDeviceTypeList" in valuesDict and valuesDict["voiceHKBDeviceTypeList"] != "":
					validTypes = valuesDict["voiceHKBDeviceTypeList"].split(",")
			
				for name, desc in sortedservices:
					#indigo.server.log (name)
					if "service_" in name:
						if len(validTypes) == 0 or name.replace("service_", "") in validTypes:
							data.append ((name.replace("service_", ""), desc))
			
			elif props["command"] == "loadDevice":
				return self.apiCall_loadDevice (action)
				
			elif props["command"] == "updateDevice":
				return self.apiCall_updateDevice (action)
				
			elif props["command"] == "none":
				pass
						
			else:
				errors["param"] = "command"
				errors["message"] = "HomeKit Bridge Voice API received the '{0}' command, but that command is not implemented.  Unable to complete API call.".format(props["command"])
				return (False, data, payload, errors)
				
		except Exception as e:
			self.logger.error (ext.getException(e))		
			errors["param"] = "command"
			errors["message"] = "HomeKit Bridge Indigo Voice API got an exception:\n\n".format(ext.getException(e))
			return (False, data, payload, errors)
			
		return (success, data, payload, errors)	
		
	#
	# Server API commands
	#
	def apiCall_updateDevice (self, action):	
		try:
			success = True
			errors = indigo.Dict()
			data = indigo.Dict() # Default, can be changed as needed
			payload = {}	
			
			props = action.props
			
			valuesDict = {}
			if "valuesDict" in props: valuesDict = props["valuesDict"]
			#indigo.server.log(unicode(valuesDict))
			
			if not valuesDict["voiceIntegrated"] or not valuesDict["voiceHKBAvailable"]:
				
				# Integration is turned off, if we have a copy of this around we need to remove it
				dev = indigo.devices[int(props["devId"])]
				self.logger.info (u"Processing inbound device de-integration request for {}".format(dev.name))				
				
				if dev.id in self.SERVER_ID:
					if len(self.SERVER_ID[dev.id]) > 1:
						msg = "API request to de-integrate {} failed because that device is assigned to more than one server.  Please remove this manually.".format(dev.name)
						self.logger.warning (msg)
						errors["param"] = "command"
						errors["message"] = "msg"
			
						return (False, data, payload, errors)	
						
					else:
						server = indigo.devices[self.SERVER_ID[dev.id][0]]
						props = server.pluginProps
						includedDevices = json.loads(props["includedDevices"])
						r = eps.jstash.getRecordWithFieldEquals (includedDevices, "id", dev.id)
						if r is None: 
							msg = "API request to de-integrate {} failed because the server that it is supposed to be attached do doesn't have it attached.".format(dev.name)
							self.logger.warning (msg)
							errors["param"] = "command"
							errors["message"] = "msg"
						else:
							# Have to remove it if it is there so we don't create a duplicate
							includedDevices = json.loads(props["includedDevices"])
							includedDevices = eps.jstash.removeRecordFromStash (includedDevices, "id", int(dev.id))
							props["includedDevices"] = json.dumps(includedDevices)
							server.replacePluginPropsOnServer (props)
							
							self.catalogServerDevices () # Always re-catalog so we don't show this device in the array
				
			else:			
				server = indigo.devices[int(valuesDict["voiceHKBServer"])]
				dev = indigo.devices[int(props["devId"])]
			
				self.logger.info (u"Processing inbound device update request for {} on server {}".format(dev.name, server.name))
			
				includedDevices = []
				props = server.pluginProps
				if "includedDevices" in props: includedDevices = json.loads(props["includedDevices"])

				r = eps.jstash.getRecordWithFieldEquals (includedDevices, "id", dev.id)
				if r is None: 
					r = self.createJSONItemRecord (dev, valuesDict["voiceAlias"])
				else:
					# Have to remove it if it is there so we don't create a duplicate
					includedDevices = eps.jstash.removeRecordFromStash (includedDevices, "id", int(dev.id))
				
				r["hktype"] = "service_" + valuesDict["voiceHKBDeviceType"]
				r["alias"] = valuesDict["voiceAlias"]
				r["api"] = True
				r["apilock"] = False
				
				includedDevices.append(r)
			
				props["includedDevices"] = json.dumps(includedDevices)
				server.replacePluginPropsOnServer (props)
			
	
		except Exception as e:
			self.logger.error (ext.getException(e))		
			errors["param"] = "command"
			errors["message"] = "HomeKit Bridge Indigo Voice API got an exception:\n\n".format(ext.getException(e))
			return (False, data, payload, errors)
			
		return (success, data, payload, errors)				
		
	#
	# Server API commands
	#
	def apiCall_loadDevice (self, action):		
		try:
			success = True
			errors = indigo.Dict()
			data = indigo.Dict() # Default, can be changed as needed
			payload = {}
			
			props = action.props
			
			if "devId" not in props:
				errors["param"] = "devId"
				errors["message"] = "HomeKit Bridge Voice API received the '{0}' command, but the device ID was not passed.  Unable to complete API call.".format(props["command"])
				return (False, data, payload, errors)
				
			# See if this device is already in use elsewhere
			if int(props["devId"]) in self.SERVER_ID:
				devId = int(props["devId"])
				serverId = int(self.SERVER_ID[devId][0])
				server = indigo.devices[serverId]
				
				includedDevices = []
				if "includedDevices" in server.pluginProps: includedDevices = json.loads(server.pluginProps["includedDevices"])
				r = eps.jstash.getRecordWithFieldEquals (includedDevices, "id", devId)
				
				if not r is None:				
					hktype = r["hktype"]
					hktype = hktype.replace("service_", "")
			
					if len(self.SERVER_ID[devId]) > 1:
						# Multiple servers, they cannot edit from the API
						#success = False
						payload["serverId"] = serverId
						payload["voiceDataType"] = hktype
						payload["eligible"] = False
						payload["uimessage"] = "This device is assigned to multiple HomeKit Bridge servers and cannot be changed from here.\n\nPlease edit this device's link to HomeKit Bridge from the servers it has been assigned to instead."
					
					else:
						# One server, fill it in
						payload["serverId"] = serverId
						payload["voiceDataType"] = hktype
					
			else:
				# Give them a default server and device type, first find a server with room
				serverId = 0
				
				obj = eps.homekit.getServiceObject (int(props["devId"]), 0, None, True, True)
				hktype = obj.type # Set to the default type	
				
				for dev in indigo.devices.iter(self.pluginId + ".Server"):
					includedDevices = []
					if "includedDevices" in dev.pluginProps: 
						includedDevices = json.loads(dev.pluginProps["includedDevices"])
						
					if len(includedDevices) < 99:
						serverId = dev.id
						break
						
				payload["serverId"] = serverId
				payload["voiceDataType"] = hktype
		
	
		except Exception as e:
			self.logger.error (ext.getException(e))		
			errors["param"] = "command"
			errors["message"] = "HomeKit Bridge Indigo Voice API got an exception:\n\n".format(ext.getException(e))
			return (False, data, payload, errors)
			
		return (success, data, payload, errors)	
	
	################################################################################
	# GENERAL METHODS
	################################################################################
	
	#
	# Migrate from HBB
	#
	def migrateFromHomebridgeBuddy (self):
		try:
			self.logger.info (u"Migrating from Homebridge Buddy and Homebridge-Indigo to HomeKit Bridge...")
				
			# See if we have the folder we need
			folderId = 0
			migration = False
			
			if "HomeKit Bridge" not in indigo.devices.folders:
				folder = indigo.devices.folder.create("HomeKit Bridge")
				folderId = folder.id
			else:
				folder = indigo.devices.folders["HomeKit Bridge"]
				folderId = folder.id
			
			# Check for Homebridge-Indigo
			from os.path import expanduser
			configdir = expanduser("~") + "/.homebridge"
			
			if os.path.exists (configdir):
				migration = True
				filename = configdir + "/config.json" #.new"
				if os.path.isfile(filename):
					self.logger.info (u"   Migrating found Homebridge-Indigo configuration")
					self.migrateFromHomebridgeBuddy_parseJSON (filename, folderId, "Homebridge-Indigo")
					
			# Check for Homebridge Buddy
			for server in indigo.devices.iter("com.eps.indigoplugin.homebridge"):
				if server.deviceTypeId == "Homebridge-Server" or server.deviceTypeId == "Homebridge-Guest":
					migration = True
					configdir = indigo.server.getInstallFolderPath() + "/Plugins/EPS Homebridge.indigoPlugin/Contents/Server Plugin/bin/hb/homebridge/{}".format(str(server.id))
					
					if os.path.exists (configdir):
						filename = configdir + "/config.json"
						if os.path.isfile(filename):
							self.logger.info (u"   Migrating Homebridge Buddy server '{}'".format(server.name))		
							self.migrateFromHomebridgeBuddy_parseJSON (filename, folderId, server.name)
			
			if migration:
				self.logger.info (u"Homebridge Buddy migration has completed, you will find any servers that were created in a folder called 'HomeKit Bridge' in your devices.")
			else:
				self.logger.info (u"No Homebridge-Indigo or Homebridge Buddy servers found, migration not needed")
				
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
	#
	# HBB migration, parse and process JSON file
	#
	def migrateFromHomebridgeBuddy_parseJSON (self, filename, folderId, migratedServerName):
		try:
			file = open(filename)
			config = json.loads(file.read())
			file.close()
			
			includedDevices = []
			includedActions = []
			props = {} # Server props when we create it, need it here for temp conversion
			
			# Concoct a server name
			iteration = 0
			servername = "HomeKit Bridge"
			isok = False
			failsafe = 0
			
			while not isok:
				for dev in indigo.devices:
					failsafe = failsafe + 1
					if failsafe > 5000: isok = True
					isok = True
					
					if dev.name == servername:
						iteration = iteration + 1
						servername = "HomeKit Bridge {}".format(str(iteration))
						isok = False
						break # start over
						
							
				
			for platform in config["platforms"]:
				if platform["platform"] == "Indigo":
					# Check temp conversion
					if "thermostatsInCelsius" in platform and platform["thermostatsInCelsius"]:
						props["tempunits"] = "c"
					else:
						props["tempunits"] = "f"
				
					# If we are including everything then take the first 99 and then we are done
					if ("includeIds" in platform and len(platform["includeIds"]) == 0) or "includeIds" not in platform:
						includeIds = []
						for dev in indigo.devices:
							if "excludeIds" in platform and str(dev.id) in platform["excludeIds"]: continue						
							includeIds.append(str(dev.id))
							if len(includeIds) == 99:
								self.logger.warning (u"      configuration was blanket including all devices, only allowing the first 99!")
								break
								
						platform["includeIds"] = includeIds
						
					if "includeActions" in platform and platform["includeActions"] and len(platform["includeIds"]) < 99:
						# We are good to add actions up to the limit
						limit = 99 - len(platform["includeIds"])
						
						for action in indigo.actionGroups:
							rec = self.createJSONItemRecord (action, action.name)
							self.logger.info (u"      adding action group '{}' as a switch".format(action.name))		
							rec["hktype"] = "service_Switch"
							
							includedActions.append(rec)
							
							if len(includedActions) == limit:
								self.logger.warning (u"      configuration was blanket including all action groups, only allowing the first 99 devices and action groups!")
								break
				
					# Process include Id's
					for devId in platform["includeIds"]:
						if int(devId) in indigo.devices:
							if "excludeIds" in platform and devId in platform["excludeIds"]: continue
							if int(devId) not in indigo.devices: continue
							
							dev = indigo.devices[int(devId)]
								
							rec = self.createJSONItemRecord (dev, dev.name)
							rec["invert"] = False
							
							if dev.deviceTypeId == "Homebridge-Alias":
								# We don't need these anymore, instead use the alias name and point to the parent device
								dev = indigo.devices[int(dev.ownerProps["device"])]
								#indigo.server.log ("Using {} instead of {} because it was an HBB alias".format(dev.name, indigo.devices[int(devId)].name))
								rec = self.createJSONItemRecord (dev, indigo.devices[int(devId)].name)
								rec["invert"] = False
																
							# As a failsafe make sure we aren't adding the same device ID, particularly since we are using the
							# referenced Alias ID if it was an HBB alias
							r = eps.jstash.getRecordWithFieldEquals (includedDevices, "id", dev.id)
							if r is not None:
								self.logger.warning (u"      skipping '{}' because that device is already being used on this server".format(dev.name))
								continue
							
							if "treatAsGarageDoorIds" in platform and devId in platform["treatAsGarageDoorIds"]:
								self.logger.info (u"      adding '{}' as a garage door opener".format(dev.name))	
								rec["hktype"] = "service_GarageDoorOpener"
								
							elif "treatAsMotionSensorIds" in platform and devId in platform["treatAsMotionSensorIds"]:
								self.logger.info (u"      adding '{}' as a motion sensor".format(dev.name))	
								rec["hktype"] = "service_MotionSensor"
								
							elif "treatAsSwitchIds" in platform and devId in platform["treatAsSwitchIds"]:
								self.logger.info (u"      adding '{}' as a switch".format(dev.name))		
								rec["hktype"] = "service_Switch"
								
							elif "treatAsWindowCoveringIds" in platform and devId in platform["treatAsWindowCoveringIds"]:
								self.logger.info (u"      adding '{}' as a window covering".format(dev.name))
								rec["hktype"] = "service_WindowCovering"
								
							elif "treatAsLockIds" in platform and devId in platform["treatAsLockIds"]:
								self.logger.info (u"      adding '{}' as a lock".format(dev.name))
								rec["hktype"] = "service_LockMechanism"
								
							elif "treatAsDoorIds" in platform and devId in platform["treatAsDoorIds"]:
								self.logger.info (u"      adding '{}' as a door".format(dev.name))
								rec["hktype"] = "service_Door"
								
							elif "treatAsContactSensorIds" in platform and devId in platform["treatAsContactSensorIds"]:
								self.logger.info (u"      adding '{}' as a contact sensor".format(dev.name))
								rec["hktype"] = "service_ContactSensor"
								
							elif "treatAsWindowIds" in platform and devId in platform["treatAsWindowIds"]:
								self.logger.info (u"      adding '{}' as a window".format(dev.name))
								rec["hktype"] = "service_Window"
								
							else:
								obj = eps.homekit.getServiceObject (dev.id, 0, None, True, True)
								rec["hktype"] = "service_" + obj.type # Set to the default type	
								
								if rec["hktype"] == "service_Dummy" or rec["hktype"] == "service_" or "(Unsupported)" in obj.desc:
									if "brightness" in dir(dev):
										self.logger.info (u"      adding '{}' as a lightbulb (assumed)".format(dev.name))						
										rec["hktype"] = "service_Lightbulb"
									else:
										self.logger.info (u"      adding '{}' as a switch (assumed)".format(dev.name))		
										rec["hktype"] = "service_Switch"
										
									if "(Unsupported)" in obj.desc:
										self.logger.info (u"         normally '{}' would be a {} but that is not yet supported".format(dev.name, rec["hktype"].replace("service_", "")))
						
								else:
									self.logger.info (u"      adding '{}' as a {} (autodetected)".format(dev.name, rec["hktype"].replace("service_", "")))
									
							if "invertOnOffIds" in platform and devId in platform["invertOnOffIds"]:
								if "onState" in dir(dev):
									rec["invert"] = True
									
							includedDevices.append(rec)
							
							if dev.deviceTypeId == "Homebridge-Wrapper" or dev.deviceTypeId == "Homebridge-Alias":
								pass
							
								
			#indigo.server.log(unicode(includedDevices))
			# Create the server props
			
			props["serverOverride"] = False
			props["username"] = self.getNextAvailableUsername (0, True)
			props["port"] = str(self.getNextAvailablePort (51826, 0, True))
			props["listenPort"] = str(self.getNextAvailablePort (8445, 0, True))
			
			props["deviceLimitReached"] = False
			if len(includedDevices) + len(includedActions) > 98: props["deviceLimitReached"] = True
			
			props["includedDevices"] = json.dumps(includedDevices)
			props["includedActions"] = json.dumps(includedActions)

			props["pin"] = "031-45-154"			
			#props["address"] = "{} | {}".format(props["pin"], props["port"])
			props["listSort"] = "sortbyname"
			props["hiddenIds"] = "[]"
			props["filterIncluded"] = True
			props["deviceOrActionSelected"] = False
			props["showEditArea"] = False
			props["enableOnOffInvert"] = False
			props["isFahrenheitEnabled"] = False
			props["editActive"] = False
			props["device"] = ""
			props["action"] = ""
			props["objectType"] = "device"
			props["autoStartStop"] = True
			props["accessoryNamePrefix"] = ""
			
			server = indigo.device.create (protocol = indigo.kProtocol.Plugin,
				address = "{} | {}".format(props["pin"], props["port"]),
				name = servername,
				description = "Migrated from {}".format(migratedServerName),
				pluginId = "com.eps.indigoplugin.homekit-bridge",
				deviceTypeId = "Server",
				props = props,
				folder = folderId)
			
			self.logger.info (u"   HomeKit Bridge server '{}' created".format(server.name))
			
			self.checkserverFoldersAndStartIfConfigured (server)
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
	def migrateFromHomebridgeBuddyXXXX (self):
		try:			
			# Run through each HBB server
			for server in indigo.devices.iter("com.eps.indigoplugin.homebridge.Homebridge-Server"):
				self.logger.info (u"   Migrating '{}'...".format(server.name))
				
				includedDevices = []
				includedActions = []
				
				for devId in server.ownerProps["actinclude"]:
					if devId == "-none-" or devId == "-all-" or devId == "-line-": continue
					
					if int(devId) not in indigo.actionGroups:
						self.logger.warning (u"      action ID {} no longer in Indigo, skipping".format(str(devId)))
						continue
						
					if devId in server.ownerProps["actexclude"]:
						#self.logger.info (u"      action ID {} actively excluded, skipping".format(str(devId)))
						continue	
						
					self.logger.info (u"      adding '{}' as a switch (HomeKit Bridge only allows action groups as switches)".format(indigo.actionGroups[int(devId)].name))		
				
				for devId in server.ownerProps["devinclude"]:
					if devId == "-none-" or devId == "-all-" or devId == "-line-": continue
					
					if int(devId) not in indigo.devices:
						self.logger.warning (u"      device ID {} no longer in Indigo, skipping".format(str(devId)))
						continue
						
					if devId in server.ownerProps["devexclude"]:
						#self.logger.info (u"      device ID {} actively excluded, skipping".format(str(devId)))
						continue
						
					if devId in server.ownerProps["treatasdoor"]:
						self.logger.info (u"      adding '{}' as a door".format(indigo.devices[int(devId)].name))
					elif devId in server.ownerProps["treatasdrapes"]:
						self.logger.info (u"      adding '{}' as a window covering".format(indigo.devices[int(devId)].name))	
					elif devId in server.ownerProps["treatasfans"]:
						self.logger.info (u"      adding '{}' as a fan".format(indigo.devices[int(devId)].name))	
					elif devId in server.ownerProps["treatasgarage"]:
						self.logger.info (u"      adding '{}' as a garage door opener".format(indigo.devices[int(devId)].name))	
					elif devId in server.ownerProps["treatassensors"]:
						self.logger.info (u"      adding '{}' as a motion sensor".format(indigo.devices[int(devId)].name))	
					elif devId in server.ownerProps["treatasswitch"]:
						self.logger.info (u"      adding '{}' as a switch".format(indigo.devices[int(devId)].name))	
					elif devId in server.ownerProps["treataswindows"]:
						self.logger.info (u"      adding '{}' as a window".format(indigo.devices[int(devId)].name))	
					elif devId in server.ownerProps["treataslock"]:
						self.logger.info (u"      adding '{}' as a lock".format(indigo.devices[int(devId)].name))			
					else:
						self.logger.info (u"      adding '{}' as a lightbulb".format(indigo.devices[int(devId)].name))		
				
				
				for dev in indigo.devices.iter("com.eps.indigoplugin.homebridge"):
					if "treatAs" in dev.ownerProps:
						if dev.ownerProps["treatAs"] == "door":	
							self.logger.info (u"      adding '{}' as a door".format(dev.name))
							
						elif dev.ownerProps["treatAs"] == "drape":
							self.logger.info (u"      adding '{}' as a window covering".format(dev.name))
						
						elif dev.ownerProps["treatAs"] == "fan":
							self.logger.info (u"      adding '{}' as a fan".format(dev.name))
						
						elif dev.ownerProps["treatAs"] == "garage":
							self.logger.info (u"      adding '{}' as a garage door opener".format(dev.name))
						
						elif dev.ownerProps["treatAs"] == "sensor":
							self.logger.info (u"      adding '{}' as a motion sensor".format(dev.name))
						
						elif dev.ownerProps["treatAs"] == "switch":
							self.logger.info (u"      adding '{}' as a switch".format(dev.name))
						
						elif dev.ownerProps["treatAs"] == "window":
							self.logger.info (u"      adding '{}' as a window".format(dev.name))
						
						elif dev.ownerProps["treatAs"] == "lock":
							self.logger.info (u"      adding '{}' as a lock".format(dev.name))
						
						else:
							self.logger.info (u"      adding '{}' as a lightbulb".format(dev.name))
					
			
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
	
	#
	# Find an available Homebridge username starting from the default
	#
	def getNextAvailableUsername (self, devId, suppressLogging = False):
		try:
			# Each failure will do a continue, if we get to the bottom them it is unique
			for i in range (10, 100):
				username = "CC:22:3D:E3:CE:{}".format(str(i))
				
				self.logger.threaddebug (u"Validating Homebridge username {}".format(username))
				
				# Check our own servers to make sure we aren't going to use this port elsewhere
				needtocontinue = False
				for dev in indigo.devices.iter(self.pluginId + ".Server"):
					if dev.id == devId:
						# If we passed a devId then ignore it, we don't want to check against the server calling this function
						needtocontinue = True
					
					if "username" in dev.ownerProps and dev.ownerProps["username"] == username:
						self.logger.threaddebug (u"Found username {} in '{}', incrementing username".format(username, dev.name))
						needtocontinue = True
						
				if needtocontinue: continue
						
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
			self.SERVERS = []
			self.SERVER_ID = {}
			
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
	# Restart a server if it is running
	#
	def restartRunningServer (self, dev):
		try:
			# Restart the server if it's running, otherwise leave it off
			if self.checkRunningHBServer (dev):
				self.logger.debug(u"Restart requested, {} is running".format(dev.name))
				if self.shellHBStopServer (dev):
					self.logger.debug(u"Restart requested, {} was stopped, now restarting".format(dev.name))
					self.shellHBStartServer (dev)
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
	
	#
	# See if a port connection can be made - used to test if HB is running for a specific server
	#
	def checkRunningHBServer (self, dev, noStatus = False):
		try:
			if not "port" in dev.pluginProps: return False # Obviously the server was not fully configured, user probably canceled initial setup
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
					#self.shellHBStartServer (dev)
					thread.start_new_thread(self.shellHBStartServer, (dev, False))
		
		except Exception as e:
			self.logger.error (ext.getException(e))		
			
			
	#
	# Check if a port is in use
	#
	def portIsOpen (self, port, devId = 0, suppressLogging = False):
		try:
			ret = True
			
			self.logger.threaddebug (u"Verifying that {0} is available".format(port))
			if str(port) == "":
				self.logger.warning (u"Attempted to verify a null port on portIsOpen, this shouldn't happen.")
				return False
			
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

			try:
				s.bind(("127.0.0.1", int(port) ))
				
			except socket.error as e:
				ret = False
				
				if e.errno == 98:
					self.logger.threaddebug (u"Port is already in use")
					
				elif e.errno == 48:
					self.logger.threaddebug (u"Port is already in use!")
					
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
					if not suppressLogging: self.logger.warning (u"Unable to use port {0} because another HomeKit-Bridge Server '{1}' is assigned to that port".format(str(port), dev.name))
					return False
					
				if "listenPort" in dev.ownerProps and dev.ownerProps["listenPort"] == str(port):
					if not suppressLogging: self.logger.warning (u"Unable to use port {0} because another HomeKit-Bridge Server '{1}' call back is assigned to that port".format(str(port), dev.name))
					return False
			
			# So far, so good, now lets check Homebridge Buddy Legacy servers to see if one is wanting to use this port and just isn't running
			for dev in indigo.devices.iter("com.eps.indigoplugin.homebridge.Homebridge-Server"):
				if "hbport" in dev.ownerProps and dev.ownerProps["hbport"] == str(port):
					if not suppressLogging: self.logger.warning (u"Unable to use port {0} because a Homebridge Buddy Server '{1}' is assigned to that port".format(str(port), dev.name))
					return False
					
				if "hbcallback" in dev.ownerProps and dev.ownerProps["hbcallback"] == str(port):
					self.logger.warning (u"Unable to use port {0} because a Homebridge Buddy Server '{1}' call back is assigned to that port".format(str(port), dev.name))
					return False
					
			for dev in indigo.devices.iter("com.eps.indigoplugin.homebridge.Homebridge-Guest"):
				if "hbport" in dev.ownerProps and dev.ownerProps["hbport"] == str(port):
					if not suppressLogging: self.logger.warning (u"Unable to use port {0} because a Homebridge Buddy Guest Server '{1}' is assigned to that port".format(str(port), dev.name))
					return False
					
				if "hbcallback" in dev.ownerProps and dev.ownerProps["hbcallback"] == str(port):
					if not suppressLogging: self.logger.warning (u"Unable to use port {0} because a Homebridge Buddy Guest Server '{1}' call back is assigned to that port".format(str(port), dev.name))
					return False				
					
			for dev in indigo.devices.iter("com.eps.indigoplugin.homebridge.Homebridge-Custom"):
				if "hbport" in dev.ownerProps and dev.ownerProps["hbport"] == str(port):
					if not suppressLogging: self.logger.warning (u"Unable to use port {0} because a Homebridge Buddy Custom Server '{1}' is assigned to that port".format(str(port), dev.name))
					return False
					
				if "hbcallback" in dev.ownerProps and dev.ownerProps["hbcallback"] == str(port):
					if not suppressLogging: self.logger.warning (u"Unable to use port {0} because a Homebridge Buddy Custom Server '{1}' call back is assigned to that port".format(str(port), dev.name))
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
			rec["hktype"]		= ""	# The HomeKit API class
			rec["link"]			= []	# List of other added devices this is linked to
			rec["complex"]		= False	# If this device is the primary device in a complication
			rec["invert"]		= False # If this device will invert it's on/off state (requires that devices has boolean onState attribute
			rec["api"]			= False # If the device was created by an API call rather than directly
			rec["apilock"]		= False	# If the device was created by an API call and cannot be altered by us, must be altered by the plugin
			rec["tempIsF"]		= False # If the value of a temperature devices is in Fahrenheit
			
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
				rec["alias"] = alias
				if alias is None: rec["alias"] = ""
				#rec["type"] = ""
				#rec["typename"] = ""
				rec["object"] = ""
				#rec["treatas"] = "none" # Legacy Homebridge Buddy
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return None
			
		return rec
		
	################################################################################
	# OBJECT MOVER
	################################################################################
	#
	# List of unselected servers
	#
	def objectMoverAvailableServerList (self, args, valuesDict):
		ret = [("default", "SELECT A SERVER")]
		if "sourceServer" not in valuesDict: return ret
		if valuesDict["sourceServer"] == "": return ret
		
		try:
			retList = []
			
			for dev in indigo.devices.iter("com.eps.indigoplugin.homekit-bridge.Server"):
				if str(dev.id) != valuesDict["sourceServer"]:
					retList.append ( (str(dev.id), dev.name) )
				
			return retList
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return ret	
			
	#
	# List of objects on the server
	#
	def objectMoverItemsList (self, args, valuesDict):
		ret = [("default", "No data")]
		
		try:
			if "sourceServer" not in valuesDict or "destinationServer" not in valuesDict: return ret
			if valuesDict["sourceServer"] == "" or valuesDict["destinationServer"] == "": return ret
			
			source = indigo.devices[int(valuesDict["sourceServer"])]
			dest = indigo.devices[int(valuesDict["destinationServer"])]

			includedDevices = []
			includedActions = []
			includedDevicesDest = []
			includedActionsDest = []
			
			if "includedDevices" in source.pluginProps: includedDevices = json.loads(source.pluginProps["includedDevices"])
			if "includedActions" in source.pluginProps: includedActions = json.loads(source.pluginProps["includedActions"])
			
			if "includedDevices" in dest.pluginProps: includedDevicesDest = json.loads(dest.pluginProps["includedDevices"])
			if "includedActions" in dest.pluginProps: includedActionsDest = json.loads(dest.pluginProps["includedActions"])
			
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
			
			includedObjects = eps.jstash.sortStash (includedObjects, "sortbyname")
			
			for d in includedObjects:
				# See if this is in the destination
				suffix = ""
				
				rec = eps.jstash.getRecordWithFieldEquals (includedDevicesDest, "alias", d["alias"])	
				if rec is None: rec = eps.jstash.getRecordWithFieldEquals (includedActionsDest, "alias", d["alias"])
				if not rec is None: suffix = " [Will Rename]"
				
				rec = eps.jstash.getRecordWithFieldEquals (includedDevicesDest, "id", d["id"])	
				if rec is None: rec = eps.jstash.getRecordWithFieldEquals (includedActionsDest, "id", d["id"])
				if not rec is None: suffix = " [Unmovable]"
				
				if d["id"] not in indigo.devices and d["id"] not in indigo.actionGroups:
					self.logger.error (u"Object '{}' ID {} is no longer part of Indigo, please remove this device from your server!".format(d["alias"], d["id"]))

				
				name = d["alias"]
				if name == "": name = d["name"]
				name = "{0}: {1}".format(d["object"], name)
				name += suffix
				
				# Homebridge Buddy Legacy support
				if d["id"] in indigo.devices and "indicateHBB" in valuesDict and valuesDict["indicateHBB"]:
					dev = indigo.devices[d["id"]]
					if dev.pluginId == "com.eps.indigoplugin.homebridge":
						if dev.deviceTypeId == "Homebridge-Wrapper":
							name += " => [HBB " + dev.ownerProps["treatAs"].upper() + " Wrapper]"
						elif dev.deviceTypeId == "Homebridge-Alias":
							name += " => [HBB " + dev.ownerProps["treatAs"].upper() + " Alias]"
				
				retList.append ( (str(d["id"]), name) )
				
			return retList
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return ret	
			
	#
	# Form field changed
	#
	def objectMoverFormFieldChanged (self, valuesDict, typeId):	
		try:
			errorsDict = indigo.Dict()		
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return (valuesDict, errorsDict)		
		
	#
	# Move items between servers
	#
	def objectMoverRun (self, valuesDict, typeId):		
		try:
			success = True
			errorsDict = indigo.Dict()	
			
			if valuesDict["sourceServer"] == "":
				errorsDict["showAlertText"] = "Select a source server to move your items from."
				errorsDict["sourceServer"] = "Invalid server"
				return (False, valuesDict, errorsDict)	
				
			if valuesDict["destinationServer"] == "":
				errorsDict["showAlertText"] = "Select a destination server to move your items to."
				errorsDict["destinationServer"] = "Invalid server"
				return (False, valuesDict, errorsDict)		
				
			if len(valuesDict["moveItems"]) == 0:
				errorsDict["showAlertText"] = "This process will be far more successful if you choose items to move."
				errorsDict["moveItems"] = "Invalid selection"
				return (False, valuesDict, errorsDict)	
				
			source = indigo.devices[int(valuesDict["sourceServer"])]

			includedDevicesSource = []
			includedActionsSource = []
			
			if "includedDevices" in source.pluginProps: includedDevicesSource = json.loads(source.pluginProps["includedDevices"])
			if "includedActions" in source.pluginProps: includedActionsSource = json.loads(source.pluginProps["includedActions"])
			
			dest = indigo.devices[int(valuesDict["destinationServer"])]

			includedDevicesDest = []
			includedActionsDest = []
			
			if "includedDevices" in dest.pluginProps: includedDevicesDest = json.loads(dest.pluginProps["includedDevices"])
			if "includedActions" in dest.pluginProps: includedActionsDest = json.loads(dest.pluginProps["includedActions"])	
			
			if len(includedDevicesDest) + len(includedActionsDest) + len(valuesDict["moveItems"]) > 99:
				allowed = 100 - (len(includedDevicesDest) + len(includedActionsDest))
				errorsDict["showAlertText"] = "You are unable to move all of these items because it would cause '{}' to have more than the maximum 99 items.\n\nChange your selection, the server can handle up to {} more items.".format(dest.name, str(allowed))
				errorsDict["moveItems"] = "Too many items"
				return (False, valuesDict, errorsDict)	
			
			badNames = {}	
			badIds = {}
			
			for devId in valuesDict["moveItems"]:
				rec = eps.jstash.getRecordWithFieldEquals (includedDevicesSource, "id", int(devId))	
				if rec is None: rec = eps.jstash.getRecordWithFieldEquals (includedActionsSource, "id", int(devId))	
				
				# See if this alias name exists on the destination
				alias = eps.jstash.getRecordWithFieldEquals (includedDevicesDest, "alias", rec["alias"])	
				if alias is None: alias = eps.jstash.getRecordWithFieldEquals (includedActionsDest, "alias", rec["alias"])		
				if not alias is None: badNames[alias["id"]] = rec["alias"]
				
				# See if this ID exists on the destination
				id = eps.jstash.getRecordWithFieldEquals (includedDevicesDest, "id", rec["id"])	
				if id is None: id = eps.jstash.getRecordWithFieldEquals (includedActionsDest, "id", rec["id"])		
				if not id is None: badIds[id["id"]] = rec["alias"]
				
			if len(badIds) > 0:
				# Show up to 10 items
				itemlist = "\n"
				itemcount = 0
				for devId, devName in badIds.iteritems():
					itemlist += devName + "\n"
					itemcount = itemcount + 1
					if itemcount == 10: break
					
				errorsDict["showAlertText"] = "{} of the items you selected cannot be moved to '{}' because that server is already referencing those items and having multiple references to the same item is not permitted.\n\nPlease remove:{}".format(str(len(badIds)), dest.name, itemlist)
				errorsDict["moveItems"] = "Unmovable items"
				return (False, valuesDict, errorsDict)
				
			# Move the items
			sourceProps = source.pluginProps
			destProps = dest.pluginProps
			
			for devId in valuesDict["moveItems"]:
				suffix = ""
				
				if devId in badIds: continue # Failsafe, we should never get here
				if devId in badNames: suffix = " Copy"
				
				srcrec = eps.jstash.getRecordWithFieldEquals (includedDevicesSource, "id", int(devId))	
				if srcrec is None: srcrec = eps.jstash.getRecordWithFieldEquals (includedActionsSource, "id", int(devId))	 	
				
				# Add the record to the destination server
				if srcrec["object"] == "Device":
					includedDevicesDest.append(srcrec)
				else: 
					includedActionsDest.append(srcrec)
					
				# Remove from our list
				includedDevicesSource = eps.jstash.removeRecordFromStash (includedDevicesSource, "id", int(devId))
				includedActionsSource = eps.jstash.removeRecordFromStash (includedActionsSource, "id", int(devId))
				
				# Now write it all to both servers
				self.logger.info (u"Moving '{}' from '{}' to '{}' as name '{}'".format(srcrec["alias"], source.name, dest.name, srcrec["alias"] + suffix))
				srcrec["alias"] += suffix
				
				
			sourceProps["includedDevices"] = json.dumps(includedDevicesSource)
			sourceProps["includedActions"] = json.dumps(includedActionsSource)				
			source.replacePluginPropsOnServer(sourceProps)
			
			destProps["includedDevices"] = json.dumps(includedDevicesDest)
			destProps["includedActions"] = json.dumps(includedActionsDest)				
			dest.replacePluginPropsOnServer(destProps)
				
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return (False, valuesDict, errorsDict)	
			
		return (True, valuesDict, errorsDict)	
		
				
		
	################################################################################
	# HIDDEN ITEMS MANAGEMENT
	################################################################################
	
	#
	# All hidden actions
	#
	def hiddenObjectItemsList (self, args, valuesDict):
		ret = [("default", "No data")]
		
		try:
			if "hiddenIds" in self.pluginPrefs:
				hidden = json.loads (self.pluginPrefs["hiddenIds"])
			else:
				hidden = []
				
			if len(hidden) == 0: return [("default", "You have not hidden any Indigo objects from HomeKit Bridge")]
				
			retList = []
			includedObjects = []
			
			for objId in hidden:
				d = {}
				
				if objId in indigo.devices:
					name = indigo.devices[objId].name
					object = "Device"
				elif objId in indigo.actionGroups:
					name = indigo.actionGroups[objId].name	
					object = "Action"
				
				d["id"] = objId
				d["sortbyname"] = name.lower()
				d["name"] = name
				d["object"] = object
				
				name = "{0}: {1}".format(object, name)
				d["sortbytype"] = name.lower()
				
				includedObjects.append (d)
				
			if "listSort" in valuesDict:
				includedObjects = eps.jstash.sortStash (includedObjects, valuesDict["listSort"])
			else:
				includedObjects = eps.jstash.sortStash (includedObjects, "sortbyname")
				
			for d in includedObjects:
				name = d["name"]
				name = "{0}: {1}".format(d["object"], name)
				
				retList.append ( (str(d["id"]), name) )	
				
			return retList
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return ret		
			
	#
	# All hidden actions
	#
	def hiddenObjectSelectList (self, args, valuesDict):
		ret = [("default", "No data")]
		
		objectType = "device"
		if "objectType" in valuesDict: objectType = valuesDict["objectType"]
		
		try:
			if "hiddenIds" in self.pluginPrefs:
				hidden = json.loads (self.pluginPrefs["hiddenIds"])
			else:
				hidden = []
				
			retList = []

			if objectType == "device":			
				for dev in indigo.devices:
					if dev.id in hidden: continue
					retList.append ( (str(dev.id), dev.name) )
			
			if objectType == "action":
				for dev in indigo.actionGroups:
					if dev.id in hidden: continue
					retList.append ( (str(dev.id), dev.name) )
					
			if objectType == "hbb":
				for dev in indigo.devices.iter("com.eps.indigoplugin.homebridge"):
					if dev.id in hidden: continue
					retList.append ( (str(dev.id), dev.name) )
					
			if objectType == "hbbwrapper":
				for dev in indigo.devices.iter("com.eps.indigoplugin.homebridge.Homebridge-Wrapper"):
					if dev.id in hidden: continue
					retList.append ( (str(dev.id), dev.name) )
					
			if objectType == "hbbalias":
				for dev in indigo.devices.iter("com.eps.indigoplugin.homebridge.Homebridge-Alias"):
					if dev.id in hidden: continue
					retList.append ( (str(dev.id), dev.name) )
				
			return retList
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return ret			
			
	#
	# Hidden actions form field change
	#
	def hiddenObjectsFormFieldChanged (self, valuesDict, typeId):	
		try:
			errorsDict = indigo.Dict()		
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return (valuesDict, errorsDict)		
		
	#
	# Hide objects button
	#
	def hiddenObjectsHideTheseItems (self, valuesDict, typeId):
		try:
			errorsDict = indigo.Dict()
			
			if len(valuesDict["objectList"]) == 0:
				errorsDict["showAlertText"] = "You must select something to perform an action on it."
				return (valuesDict, errorsDict)
				
			if "hiddenIds" in self.pluginPrefs:
				hidden = json.loads (self.pluginPrefs["hiddenIds"])
			else:
				hidden = []	
			
			for id in valuesDict["objectList"]:
				hidden.append (int(id))
				
			self.pluginPrefs["hiddenIds"] = json.dumps (hidden)
				
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return (valuesDict, errorsDict)			
		
	#
	# Un-hide objects button
	#
	def hiddenObjectsShowTheseItems (self, valuesDict, typeId):
		try:
			errorsDict = indigo.Dict()
			
			if len(valuesDict["hideList"]) == 0:
				errorsDict["showAlertText"] = "You must select something to perform an action on it."
				return (valuesDict, errorsDict)
				
			if "hiddenIds" in self.pluginPrefs:
				hidden = json.loads (self.pluginPrefs["hiddenIds"])
			else:
				hidden = []	
			
			newhidden = []
			
			for id in hidden:
				if str(id) in valuesDict["hideList"]: continue
				newhidden.append (int(id))
			
			self.pluginPrefs["hiddenIds"] = json.dumps (newhidden)
				
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return (valuesDict, errorsDict)		
		
					
	
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
					self.logger.warning (u"\nYou have unusable HomeKit devices.  These will still be added to a server but that server cannot be started.\nIf a future plugin update can map them they will be automatically moved to their appropriate server.")
					self.logger.debug (u"\nThe following plugin devices are included in this list:\n{}".format(unicode(unusablePlugins)))
						
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
			sortedservices = sorted(services.items(), key=operator.itemgetter(0))
			
			validTypes = []
			if "device" in valuesDict and valuesDict["device"] != "":
				if self.apiDeviceIsLinked(valuesDict["device"]):
					dev = indigo.devices[int(valuesDict["device"])]
					if "voiceHKBDeviceTypeList" in dev.ownerProps and dev.ownerProps["voiceHKBDeviceTypeList"] != "":
						validTypes = dev.ownerProps["voiceHKBDeviceTypeList"].split(",")
			
			for name, desc in sortedservices:
				#indigo.server.log (name)
				if "service_" in name:
					if len(validTypes) > 0 and name.replace("service_", "") in validTypes:
						retList.append ((name, desc + " (Plugin API Restricted)"))
						
					elif len(validTypes) == 0:
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
			
			if "hiddenIds" in self.pluginPrefs:
				hidden = json.loads (self.pluginPrefs["hiddenIds"])
			else:
				hidden = []
				
			if "hiddenIds" in valuesDict:
				for objId in json.loads(valuesDict["hiddenIds"]):
					hidden.append (int(objId)) # so it gets excluded below with the global hide

					
			retList = []
			
			# Add our custom options
			#retList.append (("-all-", "All Indigo Devices"))
			#retList.append (("-fill-", "Fill With Unassigned Devices"))
			#retList.append (("-none-", "Don't Include Any Devices"))
			#retList = eps.ui.addLine (retList)
			
			# Build a block list of current devices
			used = []
				
			if "objectType" in valuesDict and valuesDict["objectType"] == "devicefiltered":
				for dev in indigo.devices.iter(self.pluginId + ".Server"):	
					if "includedDevices" in dev.pluginProps:
						objects = json.loads(dev.pluginProps["includedDevices"])	
						for r in objects:
							used.append (r["id"])
			else:
				for r in includedDevices:
					used.append (r["id"])
			
			
			for dev in indigo.devices:
				if dev.id in hidden: 
					#self.logger.info("Device '{}' is being hidden and will not be shown on the list".format(dev.name))
					continue
				if dev.id in used:
					#self.logger.info("Device '{}' is already being used on this server and will not be shown on the list".format(dev.name)) 
					continue
				
				devId = dev.id
				name = dev.name
				
				# HomeKit doesn't allow the same ID more than once and the only way WE will allow it is
				# via a complication or customization
				r = eps.jstash.getRecordWithFieldEquals (includedDevices, "id", dev.id)
				if r is not None: continue					
				
				# Homebridge Buddy Legacy support
				if dev.pluginId == "com.eps.indigoplugin.homebridge":
					if dev.deviceTypeId == "Homebridge-Wrapper":
						name += " => [HBB " + dev.ownerProps["treatAs"].upper() + " Wrapper]"
					elif dev.deviceTypeId == "Homebridge-Alias":
						name += " => [HBB " + dev.ownerProps["treatAs"].upper() + " Alias]"
					
				retList.append ( (str(devId), name) )
				
				#if type(dev) == indigo.ThermostatDevice:
				#	# Add one device for the thermostat and one for the fan
				#	retList.append ( (str(devId + .1), name + " (Thermostat)") )
				#	retList.append ( (str(devId + .2), name + " (Fan)") )
					
				#else:
								
					# HomeKit doesn't allow the same ID more than once and the only way WE will allow it is
					# via a complication or customization
					#r = eps.jstash.getRecordWithFieldEquals (includedDevices, "id", dev.id)
					#	if r is None:
					#		retList.append ( (str(devId), name) )
				
					#if "filterIncluded" in valuesDict and valuesDict["filterIncluded"]:
					#	# Only include devices that are not already
					#	r = eps.jstash.getRecordWithFieldEquals (includedDevices, "id", devId)
					#	if r is None:
					#		retList.append ( (str(devId), name) )
					#else:
					#	retList.append ( (str(devId), name) )
			
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
			valuesDict = self.serverCheckForJSONKeys (valuesDict)	
			includedActions = json.loads(valuesDict["includedActions"])
			
			if "hiddenIds" in self.pluginPrefs:
				hidden = json.loads (self.pluginPrefs["hiddenIds"])
			else:
				hidden = []
				
			if "hiddenIds" in valuesDict:
				for objId in json.loads(valuesDict["hiddenIds"]):
					hidden.append (int(objId)) # so it gets excluded below with the global hide
				
			retList = []
			
			# Add our custom options
			#retList.append (("-all-", "All Indigo Action Groups"))
			#retList.append (("-fill-", "Fill With Unassigned Action Groups"))
			#retList.append (("-none-", "Don't Include Any Action Groups"))
			#retList = eps.ui.addLine (retList)
			
			used = []
				
			if "objectType" in valuesDict and valuesDict["objectType"] == "actionfiltered":
				for dev in indigo.devices.iter(self.pluginId + ".Server"):	
					if "includedActions" in dev.pluginProps:
						objects = json.loads(dev.pluginProps["includedActions"])	
						for r in objects:
							used.append (r["id"])
			else:
				for r in includedActions:
					used.append (r["id"])
			
			for dev in indigo.actionGroups:
				if dev.id in hidden: continue
				if dev.id in used: continue
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
				
				name = u"{0}: {1}".format(d["object"], name)
				d["sortbytype"] = name.lower()
				
				
				includedObjects.append (d)
				
			for d in includedActions:
				name = d["alias"]
				if name == "": name = d["name"]
				d["sortbyname"] = name.lower()
				
				name = u"{0}: {1}".format(d["object"], name)
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
				name = u"{0}\t{1}".format(d["object"], name)
				
				retList.append ( (str(d["id"]), name) )
				
			return retList
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return ret		
			

		
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
				
			if valuesDict["objectAction"] == "remove":	
				deleted = 0
				if "hiddenIds" in self.pluginPrefs:
					hidden = json.loads (self.pluginPrefs["hiddenIds"])
				else:
					hidden = []
				
				for id in valuesDict["deviceList"]:
					includedDevices = eps.jstash.removeRecordFromStash (includedDevices, "id", int(id))
					includedActions = eps.jstash.removeRecordFromStash (includedActions, "id", int(id))
					deleted = deleted + 1
					hidden.append (int(id))
					
				self.pluginPrefs["hiddenIds"] = json.dumps(hidden)
					
				errorsDict["showAlertText"] = "You removed {0} items and can add up to {1} more.\n\nThe devices you removed will be hidden from ALL devices from now on until you stop hiding them, which you can do from the plugin menu.\n\nNote that even if you cancel this form these devices will remain hidden and will have to be unhidden if you want to see them again.".format(str(deleted), str(99 - len(includedDevices) - len(includedActions)))
				valuesDict["deviceLimitReached"] = False # Since removing even just one guarantees we aren't at the limit yet
				
			if valuesDict["objectAction"] == "hide":	
				deleted = 0
				if "hiddenIds" in valuesDict:
					hidden = json.loads (valuesDict["hiddenIds"])
				else:
					hidden = []
				
				for id in valuesDict["deviceList"]:
					includedDevices = eps.jstash.removeRecordFromStash (includedDevices, "id", int(id))
					includedActions = eps.jstash.removeRecordFromStash (includedActions, "id", int(id))
					deleted = deleted + 1
					hidden.append (int(id))
					
				valuesDict["hiddenIds"] = json.dumps(hidden)
					
				errorsDict["showAlertText"] = "You removed {0} items and can add up to {1} more.\n\nThe devices you removed will be hidden for the remainder of the time this window is open, meaning if you save or cancel this form then these items will appear on the list again when you reopen this server configuration.".format(str(deleted), str(99 - len(includedDevices) - len(includedActions)))
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
							
							if "onState" in dir(indigo.devices[int(valuesDict["device"])]):
								valuesDict["enableOnOffInvert"] = True
							else:
								valuesDict["enableOnOffInvert"] = False
								
							if r["hktype"] == "service_Thermostat" or r["hktype"] == "service_TemperatureSensor":
								valuesDict["isFahrenheitEnabled"] = True
							else:
								valuesDict["isFahrenheitEnabled"] = False

							
						if isAction: 
							valuesDict["objectType"] = "action"
							valuesDict["action"] = str(r["id"])
							valuesDict["enableOnOffInvert"] = False
							valuesDict["isFahrenheitEnabled"] = False
						
						valuesDict["name"] = r["name"]
						valuesDict["alias"] = r["alias"]
						#valuesDict["typename"] = r["typename"]
						#valuesDict["type"] = r["type"]
						valuesDict["hkType"] = r["hktype"]
						valuesDict["hkStatesJSON"] = r["char"]
						valuesDict["hkActionsJSON"] = r["action"]
						valuesDict["deviceOrActionSelected"] = True
						if "invert" in r: 
							valuesDict["invertOnOff"] = r["invert"]
						else:
							valuesDict["invertOnOff"] = False
							
						if "tempIsF" in r:
							valuesDict["isFahrenheit"] = r["tempIsF"]
						else:
							valuesDict["isFahrenheit"] = False
							
						if "api" in r: 
							valuesDict["isAPIDevice"] = r["api"]
						else:
							valuesDict["isAPIDevice"] = False
						
						
						valuesDict["deviceLimitReached"] = False # Since we only allow 99 we are now at 98 and valid again
						valuesDict["editActive"] = True # Disable fields so the user knows they are in edit mode
						valuesDict["showEditArea"] = True # Display the device add/edit fields

			valuesDict['includedDevices'] = json.dumps(includedDevices)
			valuesDict['includedActions'] = json.dumps(includedActions)								
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
	
		return (valuesDict, errorsDict)	
	
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
			if "device" in valuesDict["objectType"]:
				thistype = "Device"
			elif "action" in valuesDict["objectType"]:
				thistype = "Action"
			elif "stream" in valuesDict["objectType"]:
				thistype = "Stream"
				
			if thistype == "Stream":
				(valuesDict, errorsDict) = self.serverButtonAddDeviceOrAction_Stream (valuesDict, errorsDict, thistype, devId)
			else:
				(valuesDict, errorsDict) = self.serverButtonAddDeviceOrAction_Object (valuesDict, errorsDict, thistype, devId)
				
			if "showAlertText" in errorsDict: return (valuesDict, errorsDict)	
			
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
			valuesDict["deviceOrActionSelected"] = False # We saved, so nothing is selected
			valuesDict["enableOnOffInvert"] = False # Nothing is selected, we don't know this, set it false
			valuesDict["isFahrenheitEnabled"] = False
			
			if valuesDict["objectAction"] != "add": 
				valuesDict["showEditArea"] = False

			# Defaults if there are none
			if valuesDict["device"] == "": valuesDict["device"] = ""
			if valuesDict["action"] == "": valuesDict["action"] = ""	
			valuesDict["invertOnOff"] = False # Failsafe
			valuesDict["isFahrenheit"] = False # Failsafe
			if valuesDict["objectType"] == "stream": valuesDict["objectType"] = "device"
				
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return (valuesDict, errorsDict)		
		

		
	#
	# Add camera stream
	#
	def serverButtonAddDeviceOrAction_Stream (self, valuesDict, errorsDict, thistype, serverId):	
		try:
			#valuesDict = self.serverCheckForJSONKeys (valuesDict)
			total = 0
			
			requiredfields = ["videoURL", "stillURL", "alias"]
			
			for f in requiredfields:
				if valuesDict[f] == "":
					errorsDict = eps.ui.setErrorStatus (errorsDict, "Invalid field value, please correct the red field.")
					errorsDict[f] = "Invalid value"
					return (valuesDict, errorsDict)
				
			packetPasses = False
			for i in range (188, 1317, 188):
				if int(valuesDict["packet"]) == i:
					packetPasses = True
					break
					
			if not packetPasses:
				errorsDict["showAlertText"] = "Packet sizes must be in increments of 188.  Please set the packet size to be an increment of 188 up to a maximum of 1316."
				errorsDict["packet"] = "Invalid value"
				return (False, valuesDict, errorsDict)		
			
			(includeList, max) = self.getIncludeStashList (thistype, valuesDict)
			
			device = self.createJSONItemRecord (None, valuesDict["alias"])
			device["object"] = "Stream"
			device["api"] = False
			device["apilock"] = False
			device["hktype"] = "service_CameraRTPStreamManagement"
			device["name"] = device["alias"]
						
			from random import randint
			device["id"] = randint(100000, 100000001)
			
			total = total + 1			
			includeList.append (device)
		
			valuesDict = self.getIncludeStashList (thistype, valuesDict, includeList)
			return (valuesDict, errorsDict)
	
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
			
			if thistype == "Device":
				if valuesDict["device"] == "" or valuesDict["device"] == "-line-" or valuesDict["device"] == "-fill-":
					errorsDict = eps.ui.setErrorStatus (errorsDict, "{} is not a valid device ID, please verify your selection.".format(valuesDict["device"]))
					errorsDict["device"] = "Invalid device"
					return (valuesDict, errorsDict)
			else:
				if valuesDict["action"] == "" or valuesDict["action"] == "-line-" or valuesDict["action"] == "-fill-":
					errorsDict = eps.ui.setErrorStatus (errorsDict, "{} is not a valid action ID, please verify your selection.".format(valuesDict["action"]))
					errorsDict["action"] = "Invalid action"
					return (valuesDict, errorsDict)
					
			if valuesDict["hkType"] == "":
				errorsDict = eps.ui.setErrorStatus (errorsDict, "Select a valid HomeKit device type.")
				errorsDict["hkType"] = "Invalid type"
				return (valuesDict, errorsDict)
			
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
					if "enableOnOffInvert" in valuesDict and valuesDict["enableOnOffInvert"]: device["invert"] = valuesDict["invertOnOff"]
					if "isFahrenheit" in valuesDict and valuesDict["isFahrenheit"]: device["tempIsF"] = valuesDict["isFahrenheit"]
					if "isAPIDevice" in valuesDict and valuesDict["isAPIDevice"]: 
						device["api"] = True
					else:
						device["api"] = False
						device["apilock"] = False
					
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
				
				# See if we should show the invert checkbox
				if "onState" in dir(indigo.devices[int(valuesDict["device"])]):
					valuesDict["enableOnOffInvert"] = True
				else:
					valuesDict["enableOnOffInvert"] = False
					
				# Populate the name of the device if it is not already populated (this way if they are editing and change devices the alias remains the same)
				if valuesDict["alias"] == "": valuesDict["alias"] = indigo.devices[int(valuesDict["device"])].name
							
				# So long as we are not in edit mode then pull the HK defaults for this device and populate it
				if not valuesDict["editActive"]:
					obj = eps.homekit.getServiceObject (valuesDict["device"], devId, None, True, True)
					#obj = hkapi.automaticHomeKitDevice (indigo.devices[int(valuesDict["device"])], True)
					#valuesDict = self.serverFormFieldChanged_RefreshHKDef (valuesDict, obj) # For our test when we were defining the HK object here
					valuesDict["hkType"] = "service_" + obj.type # Set to the default type		
					
					# Check if this is a HBB device and default to THAT type instead
					if int(valuesDict["device"]) in indigo.devices and indigo.devices[int(valuesDict["device"])].pluginId == "com.eps.indigoplugin.homebridge":
						hbb = indigo.devices[int(valuesDict["device"])]
						if "treatAs" in hbb.ownerProps and (hbb.deviceTypeId == "Homebridge-Wrapper" or hbb.deviceTypeId == "Homebridge-Alias"):
							if hbb.ownerProps["treatAs"] == "dimmer": valuesDict["hkType"] = "service_Lightbulb"
							if hbb.ownerProps["treatAs"] == "switch": valuesDict["hkType"] = "service_Switch"
							if hbb.ownerProps["treatAs"] == "lock": valuesDict["hkType"] = "service_LockMechanism"
							if hbb.ownerProps["treatAs"] == "door": valuesDict["hkType"] = "service_Door"
							if hbb.ownerProps["treatAs"] == "garage": valuesDict["hkType"] = "service_GarageDoorOpener"
							if hbb.ownerProps["treatAs"] == "window": valuesDict["hkType"] = "service_Window"
							if hbb.ownerProps["treatAs"] == "drape": valuesDict["hkType"] = "service_WindowCovering"
							if hbb.ownerProps["treatAs"] == "sensor": valuesDict["hkType"] = "service_MotionSensor"
							if hbb.ownerProps["treatAs"] == "fan": valuesDict["hkType"] = "service_Fanv2"
							
				# If the type is correct then turn on temperature
				if valuesDict["hkType"] != "" and (valuesDict["hkType"] == "service_Thermostat" or valuesDict["hkType"] == "service_TemperatureSensor"):			
					valuesDict["isFahrenheitEnabled"] = True
				else:
					valuesDict["isFahrenheitEnabled"] = False	
							
			else:
				pass
				#indigo.server.log("nothing selected")
				
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
				valuesDict["enableOnOffInvert"] = False # NEVER show this on Actions
				valuesDict["isFahrenheitEnabled"] = False
				
				valuesDict["alias"] = indigo.actionGroups[int(valuesDict["action"])].name
				
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
			if valuesDict["device"] == "": valuesDict["device"] = ""
			if valuesDict["action"] == "": valuesDict["action"] = ""
			
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
			
			# Sanity checks to make sure we don't put the form in an unusable state
			valuesDict["homeKitTypeEnabled"] = True  # Until determined otherwise
						
			if "device" in valuesDict["objectType"]:
				if valuesDict["device"] != "" and valuesDict["device"] != "-fill-" and valuesDict["device"] != "-line-":
					valuesDict["deviceOrActionSelected"] = True
					
					#(type, typename) = self.deviceIdToHomeKitType (valuesDict["device"])
					#valuesDict["type"] = type
					#valuesDict["typename"] = typename
					
					# So long as we aren't editing (in which case we already saved our treatAs) then set the device type to discovery
				else:
					valuesDict["deviceOrActionSelected"] = False	

			if "action" in valuesDict["objectType"]:
				if valuesDict["action"] != "" and valuesDict["action"] != "-fill-" and valuesDict["action"] != "-line-":
					valuesDict["deviceOrActionSelected"] = True
					#valuesDict["type"] = self.deviceIdToHomeKitType (valuesDict["action"])
						
				else:
					valuesDict["deviceOrActionSelected"] = False	
					
			if "stream" in valuesDict["objectType"]:
				errorsDict["showAlertText"] = u"You have selected the custom camera stream, a type which is not yet supported by this plugin and is experimental.  You should not expect this to work properly and may cause errors in how this server device operates.\n\nWhen this service is supported it will no longer be labeled as 'Experimental' and this message will not appear.\n\nThe configuration fields and how they are evaluated may change on each release until finalized.\n\nUse at your own risk!"
				valuesDict["deviceOrActionSelected"] = True
				valuesDict["homeKitTypeEnabled"] = False
				valuesDict["hkType"] = "service_CameraRTPStreamManagement"
				
			if valuesDict["hkType"] == "service_Thermostat" or valuesDict["hkType"] == "service_TemperatureSensor":
				valuesDict["isFahrenheitEnabled"] = True
			else:
				valuesDict["isFahrenheitEnabled"] = False
					
			if valuesDict["objectAction"] == "add":
				valuesDict["showEditArea"] = True
			else:
				if not valuesDict["editActive"]: 
					valuesDict["showEditArea"] = False
				else:
					valuesDict["showEditArea"] = True
					
			# Failsafe in case they are not even looking at this window:
			if valuesDict["configOption"] != "include":
				valuesDict["showEditArea"] = False
					
			
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
			
			# If the server is running and the ports didn't change then we know we should be OK, otherwise we need to check
			server = indigo.devices[devId]
			
			# If they hit save while in edit mode we need to pop a warning but let them move forward
			if valuesDict["editActive"] and "editActiveWarning" not in valuesDict:
				errorsDict["showAlertText"] = "You are actively editing a list item, if you save now you will lose your edit.\n\nTo save your edit please click the button labeled 'Add To HomeKit'.\n\nYou can also choose to cancel the configuration and lose any changes you have made.\n\nThis is only a warning, if you click save again you will save your other changes and effectively remove whatever item you were editing."
				valuesDict["editActiveWarning"] = True
				#errorsDict["device"] = "Finish editing before saving your device"
				#errorsDict["action"] = "Finish editing before saving your device"
				#errorsDict["alias"] = "Finish editing before saving your device"
				#errorsDict["add"] = "Finish editing before saving your device"
				success = False
				
			# Sanity check to make sure we have our required startup info				
			if valuesDict["port"] == "":
				valuesDict["port"] = str(self.getNextAvailablePort (51826, devId, True))
			
			# Now check the callback port
			if valuesDict["listenPort"] == "":
				valuesDict["listenPort"] = str(self.getNextAvailablePort (8445, devId, True))
			
			# Now check the username
			if valuesDict["username"] == "":
				valuesDict["username"] = self.getNextAvailableUsername (devId, True)	
				
			if success:
				# Reset the form back so when they open it again it has some defaults in place
				valuesDict["objectAction"] = "add"
				valuesDict["showEditArea"] = True
				valuesDict["device"] = ""
				valuesDict["action"] = ""
				valuesDict["objectType"] = "device"
				valuesDict["enableOnOffInvert"] = False
				valuesDict["isFahrenheitEnabled"] = False
				valuesDict["invertOnOff"] = False
				valuesDict["isFahrenheit"] = False
				valuesDict["deviceOrActionSelected"] = False
				valuesDict["isAPIDevice"] = False
				valuesDict["editActive"] = False
				valuesDict["configOption"] = "include"
				
				# See if any of our critical items changed from the current config (or if this is a new device)
				if "port" not in server.pluginProps or server.pluginProps["port"] != valuesDict["port"] or server.pluginProps["listenPort"] != valuesDict["listenPort"] or server.pluginProps["username"] != valuesDict["username"]:
					if server.onState:
						currentports = "Port: {}\nCallback: {}".format(server.pluginProps["port"], server.pluginProps["listenPort"])
						errorsDict["showAlertText"] = "You cannot change the server port while the server is running.  If you want to change the server port then please turn off the server first so that the plugin can perform an accurate port validation to prevent possible collisions and failure.\n\nFor your reference, the port values should remain at:\n\n{}".format(currentports)
						return (False, valuesDict, errorsDict)
					
					# This is a new device or we changed it manually because these things wouldn't change if it were all automatic
					self.logger.info (u"Server '{}' has changed ports or users, validating config".format(server.name))
					
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
			#self._catalogServerDevices (server)
			self.catalogServerDevices ()
				
			# No matter what happens, if we are hiding objects for this session only then remove that cache now
			if "hiddenIds" in valuesDict:
				del valuesDict["hiddenIds"]
				
			# In case we warned about being in edit mode above, remove that now
			if "editActiveWarning" in valuesDict: del(valuesDict["editActiveWarning"])
			
			# For our API we need to go through all devices and see if they were added by an API so we can update them
			includedDevices = json.loads(valuesDict["includedDevices"])
			for i in includedDevices:
				if "api" in i and i["api"]:
					dev = indigo.devices[i["id"]]
					
					plugin = indigo.server.getPlugin (dev.pluginId)
					props = {}
					props["command"] = "updateDevice"
					
					values = indigo.Dict()
					values["voiceIntegrated"] = True
					values["voiceHKBAvailable"] = True
					values["voiceHKBServer"] = str(devId)
					values["voiceHKBDeviceType"] = i["hktype"].replace("service_", "")
					values["voiceAlias"] = i["alias"]
					
					props["valuesDict"] = values
					
					(apisuccess, data, payload, errors) = plugin.executeAction("voiceAPI", deviceId=i["id"], waitUntilDone=True, props=props)
					
					if not apisuccess:
						self.logger.error (u"Attempted to update {} on {} but the plugin returned an error: {}.".format(dev.name, plugin.pluginDisplayName, errors["message"]))
						
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return (success, valuesDict, errorsDict)
		
	#
	# Server prop changed
	#
	def serverPropChanged (self, origDev, newDev, changedProps):
		try:
			self.logger.threaddebug (u"Server property change: " + unicode(changedProps))
			
			# States that will prompt us to save and restart the server
			watchStates = ["port", "listenPort", "includedDevices", "includedActions", "accessoryNamePrefix", "pin", "username", "modelValue", "firmwareValue"]
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
				# Rebuild indexes
				self.catalogServerDevices()	
				
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
			#self.logger.threaddebug (u"Server attribute change: " + unicode(changedProps))
						
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
				# Rebuild indexes
				self.catalogServerDevices()	
				
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
			# Failsafe check to not attempt to start the server unless we have our ports configured
			if "pin" not in dev.pluginProps or "port" not in dev.pluginProps or "listenPort" not in dev.pluginProps or "username" not in dev.pluginProps:
				self.logger.debug (u"One or more required fields are missing on '{}' (port, pin, listenPort or usrename), we'll assume it is yet unconfigured and won't error on the user".format(dev.name))
				return False
				
			if dev.pluginProps["pin"] == "" or dev.pluginProps["port"] == "" or dev.pluginProps["listenPort"] == "" or dev.pluginProps["username"] == "":
				self.logger.debug (u"One or more required fields are present but blank on '{}' (port, pin, listenPort or usrename), we'll assume it is yet unconfigured and won't error on the user".format(dev.name))
				return False
			
							
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
				self.logger.debug (u"Homebridge update requested, but '{}' isn't running, ignoring update request".format(server.name))
				return
			
			url = "http://127.0.0.1:{1}/devices/{0}".format(str(objId), server.pluginProps["listenPort"])
			
			#data = {'isOn':1, 'brightness': 100}
			data = {}
			
			data_json = json.dumps(data)
			payload = {'json_payload': data_json}
			
			self.logger.debug (u"Homebridge update requested, querying {0} on {1}".format(url, server.name))
			
			r = requests.get(url, data=payload)
			
			#indigo.server.log(unicode(r))
			
			
		
		except Exception as e:
			self.logger.error (ext.getException(e) + "\nServer: {}".format(server.name))	
		
		
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
					self.logger.error (u"Unable to create the configuration folder under '{0}', '{1}' will be unable to run until this issue is resolved.  Please verify permissions and create the folder by hand if needed.".format(self.CONFIGDIR, dev.name))
					return False
					
			# Now ask Homebridge to create our structure there
			if not os.path.exists (self.CONFIGDIR + "/" + str(dev.id)):
				os.system('"' + self.HBDIR + '/createdir" "' + self.CONFIGDIR + "/" + str(dev.id) + '"')
				
				if not os.path.exists (self.CONFIGDIR + "/" + str(dev.id)):
					self.logger.error (u"Unable to create the configuration folder under '{0}', '{1}' will be unable to run until this issue is resolved.  Please verify permissions and create the folder by hand if needed.".format(self.CONFIGDIR + "/" + str(dev.id), dev.name))
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
			includedDevices = []
			includedActions = []
				
			if "includedDevices" in dev.pluginProps: includedDevices = json.loads(dev.pluginProps["includedDevices"])
			if "includedActions" in dev.pluginProps: includedActions = json.loads(dev.pluginProps["includedActions"])	

			if len(includedDevices) + len(includedActions) == 0:
				self.logger.info (u"Server '{}' has no devices to publish to HomeKit, the server won't be started since there is nothing to serve".format(dev.name))
				return False
			
			# Since we are here and have the devices and actions, verify that each of these actions and devices are valid
			propschanged = False
			for rec in includedDevices:
				if rec["id"] not in indigo.devices:
					self.logger.warning (u"Device ID {} ({}) is linked to server '{}' but that device ID no longer exists in Indigo and will be removed from the configuration".format(unicode(rec["id"]), rec["name"], dev.name))
					includedDevices = eps.jstash.removeRecordFromStash (includedDevices, "id", int(rec["id"]))
					propschanged = True
					
			for rec in includedActions:
				if rec["id"] not in indigo.actionGroups:
					self.logger.warning (u"Action group ID {} ({}) is linked to server '{}' but that device ID no longer exists in Indigo and will be removed from the configuration".format(unicode(rec["id"]), rec["name"], dev.name))
					includedActions = eps.jstash.removeRecordFromStash (includedActions, "id", int(rec["id"]))		
					propschanged = True
					
			if propschanged:
				props = dev.pluginProps
				props["includedDevices"] = json.dumps(includedDevices)
				props["includedActions"] = json.dumps(includedActions)				
				dev.replacePluginPropsOnServer(props)
				self.catalogServerDevices() # Reindex everything
							
			self.logger.debug (u"Rebuilding configuration for '{0}'".format(dev.name))
			self.saveConfigurationToDisk (dev)
			
			# Start the HB server
			self.logger.threaddebug ('Running: "' + self.HBDIR + '/load" "' + self.CONFIGDIR + "/" + str(dev.id) + '"')
			os.system('"' + self.HBDIR + '/load" "' + self.CONFIGDIR + "/" + str(dev.id) + '"')
			
			indigo.devices[dev.id].updateStateOnServer("onOffState", False, uiValue="Starting")
			self.logger.info (u"Attempting to start '{0}'".format(dev.name))
			self.SERVER_STARTING.append(dev.id)
						
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
					self.logger.debug (u"HomeKit server '{0}' has been started".format(dev.name))
					return True
					
				loopcount = loopcount + 1
					
			self.logger.error (u"HomeKit server '{0}' could not be started, please check the service logs for more information,\nnow issuing a forced shutdown of the service to be safe.\n\nIf you continue to have problems starting this server use the Advanced Plugin Actions menu option to rebuild the Homebridge folder.\nInstructions at https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/Plugin-Menu-Utilities#rebuild-homebridge-folder".format(dev.name))	
			self.shellHBStopServer (dev)
			
			# To help prevent a possible hang	
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return False
			
		return False
		
	#
	# Stop HB for the provided server
	#
	def shellHBStopServer (self, dev, noStatus = False, blind = False):
		try:
			# If it's in the startup list then remove it
			if dev.id in self.SERVER_STARTING:
				newlist = []
				for id in self.SERVER_STARTING:
					if id != dev.id: newlist.append(id)
					
				self.SERVER_STARTING = newlist
			
			# Start the HB server
			self.logger.threaddebug ('Running: "' + self.HBDIR + '/unload" "' + self.CONFIGDIR + "/" + str(dev.id) + '"')
			os.system('"' + self.HBDIR + '/unload" "' + self.CONFIGDIR + "/" + str(dev.id) + '"')
			
			if not blind:
				self.logger.info (u"Attempting to stop '{0}'".format(dev.name))
				if not noStatus: indigo.devices[dev.id].updateStateOnServer("onOffState", True, uiValue="Stopping")
			else:
				self.logger.info (u"Blind stopping '{0}'".format(dev.name))
				if not noStatus: indigo.devices[dev.id].updateStateOnServer("onOffState", False, uiValue="Blind Stop")
			
			if blind: return True
			
			# Give it up to 60 seconds to respond to a port query to know if it started
			loopcount = 1
			while loopcount < 13:
				time.sleep (5)
				result = self.checkRunningHBServer (dev)
				if not result: 
					self.logger.info (u"HomeKit server '{0}' has been stopped".format(dev.name))
					return True
					
				loopcount = loopcount + 1		
					
			self.logger.error (u"HomeKit server '{0}' could not be stopped, please check the service logs for more information".format(dev.name))		
			
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return False
			
		return False	
		
		
	################################################################################
	# HOMEBRIDGE CONFIGURATION BUILDER
	################################################################################	
	
	#
	# Do a folder sanity check on the Homebridge folder and rebuild it if it's not correct
	#
	def homebridgeFolderSanityCheck (self, server, checkForConfig = True):
		try:
			files = [u"com.webdeck.homebridge.{}.plist".format(server.id)]
			folders = ["accessories", "persist"]
			
			if checkForConfig: files.append(config.json)
			
			isSane = True
			startpath = self.CONFIGDIR + "/" + str(server.id)
			
			if os.path.exists (startpath):
				for f in files:
					if not os.path.isfile(u"{}/{}".format(startpath, f)):
						self.logger.error (u"While performing a sanity check on the config folder, {}/{} was not there.".format(startpath, f))
						isSane = False
						break
						
				for f in folders:
					if not os.path.exists(u"{}/{}".format(startpath, f)):
						self.logger.error (u"While performing a sanity check on the config folder, {}/{} was not there.".format(startpath, f))
						isSane = False
						break

			else:
				self.logger.error (u"While performing a sanity check on the config folder, {} was not there.".format(startpath))
				isSane = False
				
			if not isSane:
				self.rebuildHomebridgeFolder (server)
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return False
			
		return True	
		
	#
	# Recreate the homebridge folder
	#
	def rebuildHomebridgeFolder (self, server):
		try:
			startpath = self.CONFIGDIR + "/" + str(server.id)
			
			if os.path.exists (startpath):
				self.logger.info (u"Removing {} so it can be regenerated.".format(startpath))
				import shutil
				shutil.rmtree(self.CONFIGDIR + "/" + str(server.id))
			
			self.shellCreateServerConfigFolders (server)
			self.logger.info (u"Recreated the configuration folder at {}.".format(startpath))
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return False
			
		return True	
	
	#
	# Write server configuration to disk
	#
	def saveConfigurationToDisk (self, server):
		try:
			self.logger.debug (u"Saving '{}' configuration to {}".format(server.name, self.CONFIGDIR + "/" + str(server.id)))
			self.homebridgeFolderSanityCheck (server, False)
			
			config = self.buildServerConfigurationDict (server.id)
			if config is None:
				self.logger.error (u"Unable to build server configuration for '{0}'.".format(server.name))
				return False
				
			jsonData = json.dumps(config, indent=8)
			#self.logger.debug (unicode(jsonData))
			
			startpath = self.CONFIGDIR + "/" + str(server.id)
			
			# Failsafe to make sure we have a server folder
			if not os.path.exists (startpath):
				os.makedirs (startpath)
				
				if not os.path.exists (startpath):
					self.logger.error (u"Unable to create the configuration folder under '{0}', '{1}' will be unable to run until this issue is resolved.  Please verify permissions and create the folder by hand if needed.".format(startpath, dev.name))
					return False
			
			if os.path.exists (startpath):
				with open(startpath + "/config.json", 'w') as file_:
					file_.write (jsonData)
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return False
			
		return True
		
	#
	# Get XML child element from dom
	#
	def _getChildElementsByTagName(self, elem, tagName):
		childList = []
		for child in elem.childNodes:
			if child.nodeType == child.ELEMENT_NODE and (tagName == u"*" or child.tagName == tagName):
				childList.append(child)
		return childList

	#
	# Get value of element from dom
	#	
	def _getElementValueByTagName(self, elem, tagName, required=True, default=None, filename=u"unknown"):
		valueElemList = self._getChildElementsByTagName(elem, tagName)
		if len(valueElemList) == 0:
			if required:
				raise ValueError(u"required XML element <%s> is missing in file %s" % (tagName,filename))
			return default
		elif len(valueElemList) > 1:
			raise ValueError(u"found more than one XML element <%s> (should only be one) in file %s" % (tagName,filename))

		valueStr = valueElemList[0].firstChild.data
		if valueStr is None or len(valueStr) == 0:
			if required:
				raise ValueError(u"required XML element <%s> is empty in file %s" % (tagName,filename))
			return default
		return valueStr			
	
	#
	# Build a configuration Dict for a given server
	#
	def buildServerConfigurationDict (self, serverId, debugMode = False):
		try:
			if int(serverId) not in indigo.devices: return None
			if "apiport" not in self.pluginPrefs:
				msg = "\nSomething is wrong, your plugin preferences should have a setting that it seems to be missing.  The only way to not\n"
				msg += "have this setting is if you canceled our configuration preferences when you first installed HomeKit Bridge.  Please\n"
				msg += "go to Plugins -> HomeKit Bridge -> Configure and be absolutely certain that you click the SAVE button in the lower\n"
				msg += "right-hand part of the window and try to start your server again.  If you tried this and still get the same error\n"
				msg += "then please post the following on the forum or in Git issues so it can be diagnosed:\n"
				self.logger.error (msg)
				self.logger.info (eps.plug.pluginMenuSupportInfo ())
				#return None
			
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
			hb["port"] = self.pluginPrefs.get('apiport', '8558')
			#hb["path"] = self.pluginPrefs["path"]
			#hb["username"] = self.pluginPrefs["username"]
			#hb["password"] = self.pluginPrefs["password"]
			hb["listenPort"] = server.pluginProps["listenPort"]
			hb["serverId"] = serverId
			
			platforms.append (hb)
			
			# See if there are any securityspy camera devices
			cam = {}
			cam["platform"] = "Camera-ffmpeg"
			cameras = []
			
			# Check for any cameras
			for r in includedDevices:
				# Blue Iris Cameras
				if r["hktype"] == "service_CameraRTPStreamManagement" and indigo.devices[int(r["id"])].pluginId == "com.GlennNZ.indigoplugin.BlueIris":
					biDev = indigo.devices[int(r["id"])]
					biWidth = biDev.states["width"]
					biHeight = biDev.states["height"]
					biName = biDev.states["optionValue"]
					biFPS = biDev.states["FPS"]
					biAudio = biDev.states['audio']
					if biFPS == 0: biFPS = 30
					biURL = ""
					
					# Read the Blue Iris preferences file
					prefFile = '{}/Preferences/Plugins/com.GlennNZ.indigoplugin.BlueIris.indiPref'.format(indigo.server.getInstallFolderPath())
					
					if os.path.isfile(prefFile):
						file = open(prefFile, 'r')
						prefdata = file.read()
						dom = xml.dom.minidom.parseString(prefdata)	
						prefs = self._getChildElementsByTagName(dom, u"Prefs")
						biServerIp = self._getElementValueByTagName(prefs[0], u"serverip", required=False, default=u"")
						biPort = self._getElementValueByTagName(prefs[0], u"serverport", required=False, default=u"")
						biUser = self._getElementValueByTagName(prefs[0], u"serverusername", required=False, default=u"")
						biPass = self._getElementValueByTagName(prefs[0], u"serverpassword", required=False, default=u"")
						
						if biPass == "":
							biURL = u"http://{}:{}".format(biServerIp, biPort)
						else:
							biURL = u"http://{}:{}@{}:{}".format(biUser, biPass, biServerIp, biPort)
							
						file.close()
							
					if biURL != "":						
						camera = {}	
						videoConfig = {}
					
						videoConfig["source"] = u"-re -i {}/h264/{}/temp.m".format(biURL, biName)
						videoConfig["stillImageSource"] = u"-i {}/image/{}".format(biURL, biName)
						videoConfig["maxWidth"] = biWidth
						videoConfig["maxHeight"] = biHeight
						videoConfig["maxFPS"] = biFPS
						videoConfig['maxBitrate'] = int(self.pluginPrefs.get("bitrate", "300"))
						videoConfig['packetSize'] = int(self.pluginPrefs.get("packetsize", "1316"))
						if self.pluginPrefs.get("cameradebug", False): videoConfig['debug'] = True
						videoConfig['audio'] = biAudio 
					
						camera["name"] = r["alias"]
						camera["videoConfig"] = videoConfig
					
						cameras.append(camera)	
					
				# Security Spy Cameras
				if r["hktype"] == "service_CameraRTPStreamManagement" and indigo.devices[int(r["id"])].pluginId == "org.cynic.indigo.securityspy":
					# Get the device and it's SS server
					ssDev = indigo.devices[int(r["id"])]
					ssServerId, ssCameraNum = ssDev.ownerProps["xaddress"].split("@")
					ssServer = indigo.devices[int(ssServerId)]
					ssSystem = u"http://{}:{}/++systemInfo".format(ssServer.ownerProps["xaddress"],ssServer.ownerProps["port"])
					ssWidth = 640
					ssHeight = 480
					ssFPS = 30
					
					if ssServer.ownerProps["password"] == "":
						data = requests.get(ssSystem).content	# Pull XML data
						ssURL = u"http://{}:{}".format(ssServer.ownerProps["xaddress"],ssServer.ownerProps["port"])
						if ssServer.ownerProps["xaddress"] == "": ssURL = u"http://{}".format(ssServer.ownerProps["address"])
					else:
						data = requests.get(ssSystem, auth=(ssServer.ownerProps["username"], ssServer.ownerProps["password"])).content	
						ssURL = u"http://{}:{}@{}:{}".format(ssServer.ownerProps["username"],ssServer.ownerProps["password"],ssServer.ownerProps["xaddress"],ssServer.ownerProps["port"])
						if ssServer.ownerProps["xaddress"] == "": ssURL = u"http://{}:{}@{}".format(ssServer.ownerProps["username"],ssServer.ownerProps["password"], ssServer.ownerProps["address"])
						
					# Extract XML data
					dom = xml.dom.minidom.parseString(data)			
					system = self._getChildElementsByTagName(dom, u"system")
					sscameralist = self._getChildElementsByTagName(system[0], u"cameralist")
					sscameras = self._getChildElementsByTagName(sscameralist[0], u"camera")
					
					# Get the width and height from XML dta
					for sscamera in sscameras:
						try:
							number = self._getElementValueByTagName(sscamera, u"number", required=False, default=u"")
							if int(number) == int(ssCameraNum):
								ssWidth = int(self._getElementValueByTagName(sscamera, u"width", required=False, default=u""))
								ssHeight = int(self._getElementValueByTagName(sscamera, u"height", required=False, default=u""))
								ssFPS = int(float(self._getElementValueByTagName(sscamera, u"current-fps", required=False, default=u"")))
								if ssFPS < 10: ssFPS = 10
								break
						except:
							self.logger.warning (u"Unable to retrieve SecuritySpy parameters for {}, defaulting to {}x{} and {} FPS".format(r["alias"], ssWidth, ssHeight, ssFPS))
					
					camera = {}	
					videoConfig = {}
					
					videoConfig["source"] = u"-re -i {}/++video?cameraNum={}&width={}&height={}".format(ssURL, ssCameraNum, ssWidth, ssHeight)
					videoConfig["stillImageSource"] = u"-i {}/++image?cameraNum={}&width={}&height={}".format(ssURL, ssCameraNum, ssWidth, ssHeight)
					videoConfig["maxWidth"] = ssWidth
					videoConfig["maxHeight"] = ssHeight
					videoConfig["maxFPS"] = ssFPS	
					videoConfig['maxBitrate'] = int(self.pluginPrefs.get("bitrate", "300"))
					videoConfig['packetSize'] = int(self.pluginPrefs.get("packetsize", "1316"))	
					if self.pluginPrefs.get("cameradebug", False): videoConfig['debug'] = True
					
					camera["name"] = r["alias"]
					camera["videoConfig"] = videoConfig
					
					cameras.append(camera)
					
			if cameras:
				cam["cameras"] = cameras			
				platforms.append (cam)	
			
			# Add platforms
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
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	