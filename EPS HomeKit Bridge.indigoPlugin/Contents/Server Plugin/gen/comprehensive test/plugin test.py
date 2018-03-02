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

from lib import hkapi

# Plugin libraries
import json # for encoding server devices/actions
from os.path import expanduser # getting ~ user from shell
import shutil # shell level utilities for dealing with our local HB server, mostly removing non empty folders
import socket # port checking

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
	PLUGIN_LIBS = ["api", "actions3"] #["cache", "plugcache", "irr"]
	UPDATE_URL 	= ""
	
	SERVERS = []			# All servers
	SERVER_INCLUDE = {} 	# Included device aliases and their server as SERVER_INCLUDE[aliasName] = serverId (helps prevent duplicate alias names)
	
	# For shell commands
	PLUGINDIR = os.getcwd()
	HBDIR = PLUGINDIR + "/bin/hb/homebridge"
	CONFIGDIR = expanduser("~") + "/.HomeKit-Bridge"
	
	#
	# Init
	#
	def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
		indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
		
		eps.__init__ (self)
		eps.loadLibs (self.PLUGIN_LIBS)
		
		# Create JSON stash record for server devices
		self.setupJstash ()
				
						
	################################################################################
	# PLUGIN HANDLERS
	#
	# Raised onBefore_ and onAfter_ for interesting Indigo or custom commands that 
	# we want to intercept and do something with
	################################################################################	
	
	#
	# Plugin startup
	#
	def onAfter_startup (self):
		try:
			# Start the httpd listener
			eps.api.startServer (self.pluginPrefs.get('apiport', '8558'))
			
			# Check that we have a server set up
			for dev in indigo.devices.iter(self.pluginId + ".Server"):
				self.SERVERS.append (dev.id)
				
				# Just for now
				self.checkRunningHBServer (dev)
				
				# Test shell scripts
				self.shellCreateServerConfigFolders (dev)
				
				# Test config builder
				#self.saveConfigurationToDisk (dev)
				
			#xdev = hkapi.service_LightBulb (624004987)
			#indigo.server.log(unicode(xdev))
			
			#x = eps.plugdetails.getFieldUIList (indigo.devices[70743945])
			#indigo.server.log(unicode(x))
			
			#indigo.server.log(unicode(eps.plugdetails.pluginCache))
			
			
			self.serverListHomeKitDeviceTypes (None, None)
				
			if len(self.SERVERS) == 0:
				self.logger.info ("No servers detected, creating your first HomeKit server")
				
			
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
	#
	# Concurrent thread
	#
	def onAfter_runConcurrentThread (self):
		#hserver.runConcurrentThread()		
		pass
			
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
		
	################################################################################
	# PLUGIN SPECIFIC ROUTINES
	#
	# Routines not raised by plug events that are specific to this plugin
	################################################################################	
	
	################################################################################
	# GENERAL METHODS
	################################################################################
	
	#
	# See if a port connection can be made - used to test if HB is running for a specific server
	#
	def checkRunningHBServer (self, dev):
		try:
			if dev.pluginProps["port"] == "": return False
			port = int(dev.pluginProps["port"])
			
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			result = sock.connect_ex(("127.0.0.1", int(port)))
			
			if result == 0:
				indigo.devices[dev.id].updateStateOnServer("onOffState", True, uiValue="Running")
				indigo.devices[dev.id].updateStateImageOnServer(indigo.kStateImageSel.SensorOn)
				return True
			else:
				indigo.devices[dev.id].updateStateOnServer("onOffState", False, uiValue="Stopped")
				indigo.devices[dev.id].updateStateImageOnServer(indigo.kStateImageSel.SensorOff)
				return False
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return False
			
			
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
			rec["char"]			= {}	# HomeKit characteristics [hkchar]
			rec["action"]		= {}	# HomeKit action map [hkaction]
			
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
				#if "Run Action Group" in rec["typename"]: rec["object"] = "Action"
				
				indigo.server.log(unicode(rec))
				
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
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return valuesDict
		
	#
	# States for this device JSON stashed in record
	#
	def serverListJSONStates (self, args, valuesDict):	
		try:
			ret = [("default", "No data")]
			retList = []
			
			if not "hkStatesJSON" in valuesDict: return ret
			if valuesDict["hkStatesJSON"] == "": return ret
			
			states = json.loads(valuesDict["hkStatesJSON"])
			for state in states:
				name = state["name"]
				if state["source"] == "<default>":
					name += " (USE PLUGIN DEFAULT)"
				elif state["source"] == "<unused>":
					name += " (Undefined {0} type)".format(state["type"])	
				else:
					name += " ({0} {1} type {2})".format(state["source"], state["sourcedata"], state["type"])
				
				retList.append ((state["jkey"], name))
				
			# Now add all required and optional states so they can choose one to configure
			
					
			#indigo.server.log(unicode(retList))
			
			return retList	
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return ret	
			
	#
	# Actions for this device JSON stashed in record
	#
	def serverListJSONActions (self, args, valuesDict):	
		try:
			ret = [("default", "No data")]
			retList = []
			
			if not "hkActionsJSON" in valuesDict: return ret
			if valuesDict["hkActionsJSON"] == "": return ret
			
			# Add our custom options
			retList.append (("-none-", "Select An Action"))
			retList.append (("-new-", "Create New Action"))
			retList = eps.ui.addLine (retList)
			
			actions = json.loads(valuesDict["hkActionsJSON"])
			for action in actions:
				name = "{0} {1} {2}".format( action["characteristic"], action["whenvalueis"], unicode(action["whenvalue"]) )
				if action["whenvalueis"] == "between":
					name = "{0} {1} {2} and {3}".format( action["characteristic"], action["whenvalueis"], unicode(action["whenvalue"]), unicode(action["whenvalue2"]) )
				
				retList.append ((action["jkey"], name))
					
			#indigo.server.log(unicode(retList))
			
			return retList	
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return ret		
			
	#
	# Data types for HK values
	#
	def serverListHomeKitActionValueType (self, args, valuesDict):	
		try:
			ret = [("default", "No data")]
			retList = []
			
			retList.append (("bool", "Boolean (True/False)"))
			retList.append (("float", "Float (Decimal)"))
			retList.append (("int", "Integer"))
			retList.append (("unicode", "String"))
			
			# These are used to toggle on the TO field(s) and since nobody sees them it doesnt matter what we call them
			retList.append (("bbetween", "Boolean (True/False) Between"))
			retList.append (("fbetween", "Float (Decimal) Between"))
			retList.append (("ibetween", "Integer Between"))
			retList.append (("ubetween", "String Between"))
			
			# So we can toggle totally off
			retList.append (("none", "None"))
			
			return retList	
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return ret			
			
	#
	# Dynamice value data based on value type for HK Values
	#
	def serverListHomeKitActionValues (self, args, valuesDict):	
		try:
			ret = [("default", "No data")]
			retList = []
			
			if not "hkActionsValueType" in valuesDict: return ret
			if valuesDict["hkActionsValueType"] == "": return ret
			
			valueType = valuesDict["hkActionsValueType"]
			
			#indigo.server.log(valueType)
			
			if valueType == "bool" or valueType == "bbetween":
				retList.append (("true", "True"))
				retList.append (("false", "False"))
			
			elif valueType == "int" or valueType == "ibetween":
				for i in range (0, 101):
					retList.append ((str(i), str(i)))

				
			
			
			return retList	
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return ret						
			
	#
	# States for the HKAction
	#
	def serverListHomeKitStatesForAction (self, args, valuesDict):	
		try:
			ret = [("default", "No data")]
			retList = []
			
			if not "hkStatesJSON" in valuesDict: return ret
			if valuesDict["hkStatesJSON"] == "": return ret
			
			# Since our states are already fully populated in the JSON we can get our list from there
			states = json.loads(valuesDict["hkStatesJSON"])
			for state in states:
				name = state["name"]
				name += " ({0} type)".format(state["type"])
				
				retList.append ((state["name"], name))
			
			return retList	
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return ret						
		
	#
	# HomeKit device types
	#
	def serverListHomeKitDeviceTypes (self, args, valuesDict):	
		try:
			ret = [("default", "No data")]
			retList = []
			
			for name in dir(hkapi):
				if "service_" in name:
					obj = getattr (hkapi, name)
					obja = obj()
					retList.append ((name, obja.desc))
					
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
			retList.append (("-all-", "All Indigo Devices"))
			retList.append (("-fill-", "Fill With Unassigned Devices"))
			retList.append (("-none-", "Don't Include Any Devices"))
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
			retList.append (("-all-", "All Indigo Action Groups"))
			retList.append (("-fill-", "Fill With Unassigned Action Groups"))
			retList.append (("-none-", "Don't Include Any Action Groups"))
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
						
						if not isAction: valuesDict["device"] = str(r["id"])
						if isAction: valuesDict["action"] = str(r["id"])
						
						valuesDict["name"] = r["name"]
						valuesDict["alias"] = r["alias"]
						#valuesDict["typename"] = r["typename"]
						valuesDict["type"] = r["type"]
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
			hk = getattr (hkapi, valuesDict["hkType"]) # Find the class matching the selection
			obj = hk (int(valuesDict["device"]), {}, [], True) # init the class so we can pull the values, loading all optional values so we can type them
			
			return obj
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
	#
	# Look through HK item and build a list of characteristics defaults or unused and return list for processing
	#
	def serverCheckHKObjectForDefaultAndUnused (self, obj):
		try:
			charList = []
		
			for k,v in obj.characterDict.iteritems():
				char = eps.jstash.createRecord ("hkchar")
			
				char["name"] = k
				char["source"] = "<default>" # if it comes from the library then it's whatever we set the default to (i.e., state)
				char["sourcedata"] = "<default>" # The default, i.e., onOffState or onState, etc
				
				attrib = getattr (obj, k)
				char["type"] = str(type(attrib.value)).replace("<type '", "").replace("'>", "")
										
				charList.append(char)
				
			# Add any items that didn't  have definitions but can still be characteristics
			for k in obj.required:
				if k not in obj.characterDict:
					char = eps.jstash.createRecord ("hkchar")
			
					char["name"] = k
					char["source"] = "<unused>" 
					char["sourcedata"] = "<unused>"
					
					attrib = getattr (obj, k)
					char["type"] = str(type(attrib.value)).replace("<type '", "").replace("'>", "")
					
					charList.append(char)
					
			for k in obj.optional:
				if k not in obj.characterDict:
					char = eps.jstash.createRecord ("hkchar")
			
					char["name"] = k
					char["source"] = "<unused>" 
					char["sourcedata"] = "<unused>"
					
					attrib = getattr (obj, k)
					char["type"] = str(type(attrib.value)).replace("<type '", "").replace("'>", "")
					
					charList.append(char)	
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return charList			
				
			
	#
	# Save HK characteristic setting
	#
	def serverButtonSaveHKState (self, valuesDict, errorsDict, thistype):		
		try:
			errorsDict = indigo.Dict()
			
			obj = self.serverGetHomeKitObjectFromFormData (valuesDict)
			
			# Get the states record from JSON
			state = eps.jstash.getRecordWithFieldEquals (json.loads(valuesDict["hkStatesJSON"]), "jkey", valuesDict["hkStates"][0])
			
			for required in obj.required:
				if required == state["name"]:
					# This state is required, make sure if it's default that it is defined and if it's not that the user picked a state or attribute
					if valuesDict["hkStatesPicker"] == "default" and state["name"] not in obj.characterDict:
						errorsDict["showAlertText"] = "This is a required state but it is not configured to an Indigo item value, use the source field to assign a valid value to this state.\n\nNot all HomeKit device definitions automatically map to all Indigo device types, especially custom or plugin devices.\n\nValid default definitions will say PLUGIN DEFAULT, meaning that state has been mapped by default by the plugin and you do not need to remap it for it to work, if it indicates Unused then it does not have a default map.\n\nIf you need greater flexibility consider installing the Device Extensions plugin for Indigo to create custom devices."
						errorsDict["hkStates"] = "Required state"
						errorsDict["hkStatesPicker"] = "Invalid source"
						return (valuesDict, errorsDict)
						
			if "attr_" in valuesDict["hkStatesPicker"]:
				state["source"] = "attribute"
				state["sourcedata"] = valuesDict["hkStatesPicker"].replace("attr_", "")
				
			elif valuesDict["hkStatesPicker"] == "default":
				# Default means the API default, this can be default or unused, do a lookup to figure out which it is
				charList = self.serverCheckHKObjectForDefaultAndUnused (obj)
				for c in charList:
					if c["name"] == state["name"]:
						state["source"] = c["source"]
						state["sourcedata"] = c["sourcedata"]
						state["sourceextra"] = c["sourceextra"]	
						
			elif valuesDict["hkStatesPicker"] == "-line-":
				# Well, a line isn't valid
				errorsDict["showAlertText"] = "It was a little interesting when you selected it and got warned that a line wasn't a good idea.  Now it's a little silly that you tried to save it anyway.  Please select something valid!"
				errorsDict["hkStatesPicker"] = "Invalid selection"
				return (valuesDict, errorsDict)			
									
			else:
				state["source"] = "state"
				state["sourcedata"] = valuesDict["hkStatesPicker"]
			
			states = eps.jstash.removeRecordFromStash (json.loads(valuesDict["hkStatesJSON"]), "jkey", valuesDict["hkStates"][0])
			states.append (state)
			valuesDict["hkStatesJSON"] = json.dumps (states)
			
			indigo.server.log(unicode(valuesDict["hkStatesJSON"]))
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return (valuesDict, errorsDict)	
	
	#
	# Add device or action
	#
	def serverButtonAddDeviceOrAction (self, valuesDict, devId, typeId):
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
				
			if valuesDict[thistype.lower()] == "-none-":
				(valuesDict, errorsDict) = self.serverButtonAddDeviceOrAction_None (valuesDict, errorsDict, thistype)
			elif valuesDict[thistype.lower()] == "-all-":
				(valuesDict, errorsDict) = self.serverButtonAddDeviceOrAction_All (valuesDict, errorsDict, thistype)
			elif valuesDict[thistype.lower()] == "-fill-":
				(valuesDict, errorsDict) = self.serverButtonAddDeviceOrAction_Fill (valuesDict, errorsDict, thistype)
			else:
				(valuesDict, errorsDict) = self.serverButtonAddDeviceOrAction_Object (valuesDict, errorsDict, thistype)
			
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
	# Add NONE type
	#
	def serverButtonAddDeviceOrAction_None (self, valuesDict, errorsDict, thistype):	
		try:
			total = 0
			
			(includeList, max) = self.getIncludeStashList (thistype, valuesDict)
			
			# If we already have a none then ignore and return
			r = eps.jstash.getRecordWithFieldEquals (includeList, "type", "NONE")
			if r is not None: return (valuesDict, errorsDict) # Just ignore it, we have it already
			
			# If its already set to all then change it out with none and pop a message
			r = eps.jstash.getRecordWithFieldEquals (includeList, "type", "ALL")
			if r is not None: 
				includeList = eps.jstash.removeRecordFromStash (includeList, "type", "ALL")
				errorsDict = eps.ui.setErrorStatus (errorsDict, "You had specified to include ALL {0}s, you are now not including any.".format(thistype.lower()) )
				
			# If they have devices already then let them know we are removing them all
			if len(includeList) > 0:
				errorsDict = eps.ui.setErrorStatus (errorsDict, "The {0}s that you had added have all been removed because you specified you don't want to include {0}s any longer.".format(thistype.lower()) )
				includeList = []
							
			device = self.createJSONItemRecord (None)
			device["name"] = "NO {0}S".format(thistype.upper())
			device["alias"] = device["name"]
			#device["type"] = "NONE"
			#device["typename"] = "NONE"
			device["object"] = thistype
			
			valuesDict["deviceLimitReached"] = False # Don't lock them out
			
			includeList.append (device)
			
			valuesDict = self.getIncludeStashList (thistype, valuesDict, includeList)
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return (valuesDict, errorsDict)	
		
	#
	# Add ALL type
	#
	def serverButtonAddDeviceOrAction_All (self, valuesDict, errorsDict, thistype):	
		try:
			total = 0
			
			(includeList, max) = self.getIncludeStashList (thistype, valuesDict)
			
			# If we already have a none then ignore and return
			r = eps.jstash.getRecordWithFieldEquals (includeList, "type", "ALL")
			if r is not None: return (valuesDict, errorsDict) # Just ignore it, we have it already
			
			# If its already set to all then change it out with none and pop a message
			r = eps.jstash.getRecordWithFieldEquals (includeList, "type", "NONE")
			if r is not None: 
				includeList = eps.jstash.removeRecordFromStash (includeList, "type", "NONE")
				errorsDict["showAlertText"] = "You had specified to include no {0}s, you are now including them all.".format(thistype.lower())
				
			# If they have devices already then let them know we are removing them all
			if len(includeList) > 0:
				errorsDict["showAlertText"] = "The {0}s that you had added have all been removed because you specified you want to include all {0}s, which would include any devices you previously added.\n\nIncluding all {0}s means you cannot give them an alias, if you need that functionality then either use the Fill function or select your {0}s individually.".format(thistype.lower())				
				includeList = []
		
			device = self.createJSONItemRecord (None)
			device["name"] = "ALL {0}S".format(thistype.upper())
			device["alias"] = device["name"]
			#device["type"] = "ALL"
			#device["typename"] = "ALL"
			device["object"] = thistype
			msg = "Using all {0}s could mean that you exceed the 99 device limit for HomeKit so only the first 99 Indigo items will be able to be used.  You gain more flexibility by using the Fill option or selecting your {0}s individually.".format(thistype.lower())
			errorsDict = eps.ui.setErrorStatus (errorsDict, msg)
			
			valuesDict["deviceLimitReached"] = False # Don't lock them out
			
			includeList.append (device)	
			
			valuesDict = self.getIncludeStashList (thistype, valuesDict, includeList)
			
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return (valuesDict, errorsDict)	
		
	#
	# Add FILL type
	#
	def serverButtonAddDeviceOrAction_Fill (self, valuesDict, errorsDict, thistype):	
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
	def serverButtonAddDeviceOrAction_Object (self, valuesDict, errorsDict, thistype):	
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
					device['treatas'] = valuesDict["treatAs"] # Homebridge Buddy Legacy
					
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
	def serverFormFieldChanged_HKAction (self, valuesDict, typeId, devId):	
		try:
			errorsDict = indigo.Dict()	
			
			action = eps.jstash.getRecordWithFieldEquals (json.loads(valuesDict["hkActionsJSON"]), "jkey", valuesDict["hkActions"][0])
			
			valuesDict["hkActionsSource"] = action["characteristic"]
			valuesDict["hkActionsOperator"] = action["whenvalueis"]
			valuesDict["hkActionsCommand"] = action["command"]
			valuesDict["hkActionsArgs"] = unicode(action["arguments"])
			valuesDict["hkActionsValueType"]  = action["type"]
			
			if action["type"] == "bool":
				valuesDict["hkActionsValue1Select"] = unicode(action["whenvalue"]).lower()
				if valuesDict["hkActionsOperator"] == "between": 
					valuesDict["hkActionsValueType"] = "bbetween" # so we can toggle field viz
					valuesDict["hkActionsValue2Select"] = unicode(action["whenvalue2"]).lower()
			
			elif action["type"] == "int":
				valuesDict["hkActionsValue1Select"] = str(action["whenvalue"])
				if valuesDict["hkActionsOperator"] == "between": 
					valuesDict["hkActionsValueType"] = "ibetween" # so we can toggle field viz
					valuesDict["hkActionsValue2Select"] = str(action["whenvalue2"])
					
			elif action["type"] == "float":
				valuesDict["hkActionsValue1Text"] = str(action["whenvalue"])
				if valuesDict["hkActionsOperator"] == "between": 
					valuesDict["hkActionsValueType"] = "fbetween" # so we can toggle field viz
					valuesDict["hkActionsValue2Text"] = str(action["whenvalue2"])	
					
			elif action["type"] == "unicode":
				valuesDict["hkActionsValue1Text"] = str(action["whenvalue"])
				if valuesDict["hkActionsOperator"] == "between": 
					valuesDict["hkActionsValueType"] = "ubetween" # so we can toggle field viz
					valuesDict["hkActionsValue2Text"] = str(action["whenvalue2"])				
				
			# We don't want to encourage the user to put in static values so replace any device id with a keyword instead so they
			# understand that is how it is meant to be set up
			valuesDict["hkActionsArgs"] = valuesDict["hkActionsArgs"].replace(valuesDict["device"], "=devId=")
		
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
			if valuesDict["device"] != "" and valuesDict["device"] != "-fill-" and valuesDict["device"] != "-all-" and valuesDict["device"] != "-none-" and valuesDict["device"] != "-line-":
				valuesDict["deviceOrActionSelected"] = True # Enable fields
				
				# So long as we are not in edit mode then pull the HK defaults for this device and populate it
				if not valuesDict["editActive"]:
					obj = hkapi.automaticHomeKitDevice (indigo.devices[int(valuesDict["device"])], True)
					valuesDict = self.serverFormFieldChanged_RefreshHKDef (valuesDict, obj)
					valuesDict["hkType"] = "service_" + obj.type # Set to the default type		
					
			if valuesDict["deviceOrActionSelected"]: valuesDict["actionsCommandEnable"] = True # Enable actions		
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return (valuesDict, errorsDict)
		

		
	#
	# Refresh the HomeKit definition values for a device
	#
	def serverFormFieldChanged_RefreshHKDef (self, valuesDict, obj):
		try:
			# The character dict is only when we create a device, we only loop it here to get characteristic names, nothing more
			charList = self.serverCheckHKObjectForDefaultAndUnused (obj)
			
			valuesDict["hkStatesJSON"] = json.dumps(charList)
			
			# Since the type changed we need to default which state is showing
			valuesDict["hkStates"] = charList[0]["jkey"]
			
			# The first pre-defined option that we are selecting is always going to be default unless loaded up elsewhere
			valuesDict["hkStatesPicker"] = "default"
		
			actionList = []
			for a in obj.actions:
				action = eps.jstash.createRecord ("hkaction")
				action["characteristic"] = a.characteristic
				action["whenvalueis"] = a.whenvalueis
				action["whenvalue"] = a.whenvalue
				action["command"] = a.command
				action["arguments"] = a.arguments
				action["whenvalue2"] = a.whenvalue2
				action["type"] = a.valuetype

				actionList.append(action)
		
			valuesDict["hkActionsJSON"] = json.dumps(actionList)
			
			# If we have an action then fill in the form
			if len(actionList) > 0:
				action = actionList[0]
				alist = indigo.List()
				alist.append(action["jkey"])
				valuesDict["hkActions"] = alist
				
				# Since we are already calculating this when we change the action field:
				(valuesDict, errorsDict) = self.serverFormFieldChanged_HKAction (valuesDict, 0, 0)
				
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return valuesDict
		
	#
	# Server form HK type field changed
	#
	def serverFormFieldChanged_HKType (self, valuesDict, typeId, devId):	
		try:
			errorsDict = indigo.Dict()	
			
			# The device changed, if it's not a generic type then fill in defaults
			if valuesDict["device"] != "" and valuesDict["device"] != "-fill-" and valuesDict["device"] != "-all-" and valuesDict["device"] != "-none-" and valuesDict["device"] != "-line-":
				valuesDict["deviceOrActionSelected"] = True # Enable fields
				
				# So long as we are not in edit mode then pull the HK defaults for this device and populate it
				if not valuesDict["editActive"]:
					hk = getattr (hkapi, valuesDict["hkType"]) # Find the class matching the selection
					obj = hk (int(valuesDict["device"]), {}, [], True) # init the class so we can pull the values, tell it to load optionals so we can get types
					valuesDict = self.serverFormFieldChanged_RefreshHKDef (valuesDict, obj)
					
					
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return (valuesDict, errorsDict)	
		
	#
	# Server form HK state map field changed
	#
	def serverFormFieldChanged_HKStateMapChanged (self, valuesDict, typeId, devId):	
		try:
			errorsDict = indigo.Dict()	
			
			obj = self.serverGetHomeKitObjectFromFormData (valuesDict)
			
			states = json.loads (valuesDict["hkStatesJSON"])
			state = eps.jstash.getRecordWithFieldEquals (json.loads(valuesDict["hkStatesJSON"]), "jkey", valuesDict["hkStates"][0])
			
			# Test to see if our data types are the same
			objAttrib = getattr (obj, state["name"])
			objecttype = str(type(objAttrib.value)).replace("<type '", "").replace("'>", "")
			
			dev = indigo.devices[int(valuesDict["device"])]
			
			if "attr_" in valuesDict["hkStatesPicker"]:
				devAttrib = getattr (dev, valuesDict["hkStatesPicker"].replace("attr_", ""))
			elif valuesDict["hkStatesPicker"] == "default":
				# Nothing to do, once this gets selected the lists will be rebuild and set to default
				return (valuesDict, errorsDict)
			elif valuesDict["hkStatesPicker"] == "-line-":
				# Well, a line isn't valid
				errorsDict["showAlertText"] = "That is a super interesting choice, to have a line become the HomeKit device state.  While this seems like it would be pretty fun, how about selecting something that won't cause your device to crash."
				errorsDict["hkStatesPicker"] = "Invalid selection"
				return (valuesDict, errorsDict)	
			else:
				devAttrib = dev.states[valuesDict["hkStatesPicker"]]
				
			devtype = str(type(devAttrib)).replace("<type '", "").replace("'>", "")	
				
			if type(objAttrib.value) != type(devAttrib):
				errorsDict["showAlertText"] = "The data type of the Indigo item ({0}) value does not match the data type of the state you are mapping it to ({1}), this may produce unexpected results.\n\nThe plugin will attempt to convert between the two but if it cannot then you will get an error and your HomeKit device may not show the correct value.\n\nPlease refer to the HomeKit Bridge wiki to see what the valid values are for this state and if your mismatched data type will convert properly to it or consider using a different value or a plugin that will convert the values for you.\n\nThis is only a warning, you can save this setting to see how it works.".format(devtype, objecttype)
				return (valuesDict, errorsDict)
				
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return (valuesDict, errorsDict)		
		
	#
	# Server form HK state field changed
	#
	def serverFormFieldChanged_HKStateChanged (self, valuesDict, typeId, devId):	
		try:
			errorsDict = indigo.Dict()	
			
			states = json.loads (valuesDict["hkStatesJSON"])
			state = eps.jstash.getRecordWithFieldEquals (json.loads(valuesDict["hkStatesJSON"]), "jkey", valuesDict["hkStates"][0])
			
			if state["source"] == "<default>" or state["source"] == "<unused>":
				valuesDict["hkStatesPicker"] = "default"
			elif state["source"] == "attribute":
				valuesDict["hkStatesPicker"] = "attr_" + state["sourcedata"]
			else:
				valuesDict["hkStatesPicker"] = state["source"]
				
			indigo.server.log(unicode(valuesDict["hkStates"]))
			
			indigo.server.log("This is when we need to read the custom state definition")
			
			# Run the HKStateMap changed action too since that will verify our data types match
			(valuesDict, errorsDict) = self.serverFormFieldChanged_HKStateMapChanged (valuesDict, typeId, devId)
					
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
			if valuesDict["device"] == "": valuesDict["device"] = "-fill-"
			if valuesDict["action"] == "": valuesDict["action"] = "-fill-"
			#if valuesDict["treatAs"] == "": valuesDict["treatAs"] = "service_Switch" # Default
			
			if valuesDict["objectType"] == "device":
				if valuesDict["device"] != "" and valuesDict["device"] != "-fill-" and valuesDict["device"] != "-all-" and valuesDict["device"] != "-none-" and valuesDict["device"] != "-line-":
					valuesDict["deviceOrActionSelected"] = True
					
					#(type, typename) = self.deviceIdToHomeKitType (valuesDict["device"])
					#valuesDict["type"] = type
					#valuesDict["typename"] = typename
					
					# So long as we aren't editing (in which case we already saved our treatAs) then set the device type to discovery
					
						
						
				else:
					valuesDict["deviceOrActionSelected"] = False	

			if valuesDict["objectType"] == "action":
				if valuesDict["action"] != "" and valuesDict["action"] != "-fill-" and valuesDict["action"] != "-all-" and valuesDict["action"] != "-none-" and valuesDict["action"] != "-line-":
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
				
				if server.states["onOffState"] and server.pluginProps["port"] == valuesDict["port"] and server.pluginProps["listenPort"] == valuesDict["listenPort"]:
					pass
					
				else:
					# Verify that the ports and user names are ok
					if not self.portIsOpen (valuesDict["port"], devId):
						if valuesDict["serverOverride"]:
							errorsDict["showAlertText"] = "The HB port {0} you entered is already being used by the Indigo server, please change it to something else.".format(valuesDict["port"])
							errorsDict["port"] = "This port number is already in use"
				
							return (False, valuesDict, errorsDict)
					
					if not self.portIsOpen (valuesDict["listenPort"], devId):
						if valuesDict["serverOverride"]:
							errorsDict["showAlertText"] = "The listen port {0} you entered is already being used by the Indigo server, please change it to something else.".format(valuesDict["listenPort"])
							errorsDict["listenPort"] = "This port number is already in use"
				
							return (False, valuesDict, errorsDict)	
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return (success, valuesDict, errorsDict)
		
	#
	# Server prop changed
	#
	def serverPropChanged (self, origDev, newDev, changedProps):
		try:
			indigo.server.log(unicode(changedProps))
			
			# States that will prompt us to save and restart the server
			watchStates = ["port", "listenPort", "includedDevices", "includedActions", "accessoryNamePrefix", "pin", "username"]
			needsRestart = False
			
			for w in watchStates:
				if w in changedProps:
					if origDev.states[w] != newDev.states[w]:
						needsRestart = True
						break
					
			if needsRestart:
				# Save the configuration
				self.saveConfigurationToDisk (newDev)
				
				# Restart the server
				
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
	#
	# Server attribute changed
	#
	def serverAttribChanged (self, origDev, newDev, changedProps):
		try:
			#indigo.server.log(unicode(changedProps))
						
			# States that will prompt us to save and restart the server
			watchStates = ["name"]
			needsRestart = False
			
			for w in watchStates:
				if w in changedProps:
					a = getattr(origDev, w)
					b = getattr(newDev, w)
					
					if a != b:					
						indigo.server.log ("CHANGED {0}".format(w))
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
	def shellHBStartServer (self, dev):
		try:
			self.logger.info ("Rebuilding configuration for '{0}'".format(dev.name))
			self.saveConfigurationToDisk (dev)

			# Start the HB server
			os.system('"' + self.HBDIR + '/load" ' + self.CONFIGDIR + "/" + str(dev.id))
			
			self.logger.info ("Attempting to start '{0}'".format(dev.name))
			
			# Give it up to 60 seconds to respond to a port query to know if it started
			loopcount = 1
			while loopcount < 13:
				time.sleep (5)
				result = self.checkRunningHBServer (dev)
				if result: 
					self.logger.info ("HomeKit server '{0}' has been started".format(dev.name))
					return True
					
			self.logger.error ("HomeKit server '{0}' could not be started, please check the service logs for more information".format(dev.name))		
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return False
			
		return False
		
	#
	# Stop HB for the provided server
	#
	def shellHBStopServer (self, dev):
		try:
			# Start the HB server
			os.system('"' + self.HBDIR + '/unload" ' + self.CONFIGDIR + "/" + str(dev.id))
			
			self.logger.info ("Attempting to stop '{0}'".format(dev.name))
			
			# Give it up to 60 seconds to respond to a port query to know if it started
			loopcount = 1
			while loopcount < 13:
				time.sleep (5)
				result = self.checkRunningHBServer (dev)
				if not result: 
					self.logger.info ("HomeKit server '{0}' has been stopped".format(dev.name))
					return True
					
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
			indigo.server.log(unicode(jsonData))
			
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
			
			hb["platform"] = "Indigo"
			hb["name"] = "HomeKit Bridge Server"
			
			# The following come from the plugin prefs for where to find Indigo's API
			hb["protocol"] = self.pluginPrefs["protocol"]
			hb["host"] = self.pluginPrefs["host"]
			hb["port"] = self.pluginPrefs["port"]
			hb["apiPort"] = self.pluginPrefs["apiport"] # Arbitrary when we develop the API
			hb["path"] = self.pluginPrefs["path"]
			hb["username"] = self.pluginPrefs["username"]
			hb["password"] = self.pluginPrefs["password"]
			hb["listenPort"] = server.pluginProps["listenPort"]
			
			hb["includeActions"] = True
			if len(includedActions) == 0: hb["includeActions"] = False
			
			treatAs = {}
			if debugMode: treatAs = indigo.Dict() # Legacy Homebridge Buddy
			
			includeIds = []
			if debugMode: includeIds = indigo.List()
			for d in includedDevices:
				includeIds.append (d["id"])
				
				# Legacy Homebridge Buddy
				if d["treatas"] != "none":
					if not d["treatas"] in treatAs:
						treat = []
						if debugMode: treat = indigo.List()
					else:
						treat = treatAs[d["treatas"]]
						
					treat.append(d["id"])
					treatAs[d["treatas"]] = treat
				
			for d in includedActions:
				includeIds.append (d["id"])	
			
			hb["includeIds"] = includeIds
			
			# The following is a Homebridge Buddy legacy config for the treatAs, it's only here while the plugin is being tested and must be removed
			# prior to public release.  It simply allows me to run HomeKit bridge instead of HBB until the API is written and the Homebridge plugin
			# is rewritten to support it
			if len(treatAs) > 0:
				for key, value in treatAs.iteritems():
					hb[key] = value
				
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
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	