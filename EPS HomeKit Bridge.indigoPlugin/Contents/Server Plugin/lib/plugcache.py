# lib.plugcache - Reads plugin information into a re-usable cache
#
# Memory usage: ~10MB for full plugin data cache / ~35MB for everything as of 1/9/2017
#
# Copyright (c) 2018 ColoradoFourWheeler / ext
#

import indigo
import logging
import ext
import dtutil
import ui
#import actionslib

from os import listdir
import os.path
from os.path import isfile, join
import glob
#from xml.dom import minidom
import xml.dom.minidom
import plistlib
import string
import os

validDeviceTypes = ["dimmer", "relay", "sensor", "speedcontrol", "thermostat", "sprinkler", "custom"]

fieldTypeTemplates = {
	# Key is node <Field> type attribute, value is template file name.
	u"serialport": u"_configUiField_serialPort.xml"
}

class plugfilter:
	#
	# Init
	#
	def __init__(self):
		self.getDevices = True
		self.getStates = True
		self.getFields = True
		self.getActions = True
		self.showHiddenFields = False
		self.pluginFilter = ""
		self.excludeFilter = []

class plugcache:
	
	pluginCache = indigo.Dict()
	
	#
	# Init
	#
	def __init__(self, factory, refreshtime = 24, filter = None):
		self.logger = logging.getLogger ("Plugin.plugincache")
		self.factory = factory
		self.refreshtime = refreshtime
		self.filter = filter
		if filter is None: self.filter = plugfilter()
		
		self.refresh()
		
	################################################################################
	# METHODS
	################################################################################		
	
	#
	# Get a list of fields suitable for a list or menu UI field
	#
	def getFieldUIList (self, obj):
		ret = []
		
		try:
			data = self._resolveObject (obj)
			if len(data[0]) == 0: return ret
			
			plugInfo = data[0]
			deviceTypeId = data[1]				
			
			if "xml" in plugInfo == False: return ret
			if "devices" in plugInfo["xml"] == False: return ret
										
			for id, info in plugInfo["xml"]["devices"].iteritems():
				if id == deviceTypeId:
					if len(info["ConfigUI"]) > 0:	
						for idx, configUI in info["ConfigUI"].iteritems():	
							for field in configUI:
								if field["hidden"]: continue
								
								if field["type"] == "separator":
									option = ("-line-", self.factory.ui.getSeparator())
									ret.append(option)
								elif field["type"] == "label":
									continue
								else:
									label = ""
									if field["Label"].strip() != "":
										label = field["Label"]
									else:
										label = field["Description"]
										
									if label == "": continue
									label = label.strip()
									
									option = (field["id"], label.replace(":", ""))
									ret.append (option)
							
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return self._cleanReturnList (ret)
	
	#
	# Get a list of states suitable for a list or menu UI field
	#
	def getStateUIList (self, obj, showUi = False):
		ret = []
		
		try:
			data = self._resolveObject (obj)
			if len(data[0]) == 0: return ret
			
			plugInfo = data[0]
			deviceTypeId = data[1]				
			
			if "xml" in plugInfo == False: return ret
			if "devices" in plugInfo["xml"] == False: return ret
										
			ret = self._getStateUIList (obj, plugInfo, deviceTypeId, showUi)
							
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return self._cleanReturnList (ret)
		
	#
	# Run the state list builder from getStateUIList
	#
	def _getStateUIList (self, obj, plugInfo, deviceTypeId, showUi = False):
		ret = []
		statesfound = []

		try:
			for id, info in plugInfo["xml"]["devices"].iteritems():
				if id == deviceTypeId:
					for state in info["States"]:
						if state["Type"] == 0:
							option = ("-line-", self.factory.ui.getSeparator())
							ret.append(option)
						else:
							option = (state["Key"], state["StateLabel"])
							ret.append (option)
														
			# Add Indigo built-in device states
			retIndigo = self.factory.ui.getBuiltInStates (obj)
			if len(retIndigo) > 0: 
				option = ("-line-", self.factory.ui.getSeparator())
				retIndigo.append(option)
				ret = retIndigo + ret
			
			# Compare actual object states to the states found to pick up stragglers
			retadded = []
			for state, statevalue in obj.states.iteritems():
				isFound = False
				for opt in ret:
					if opt[0] == state: 
						isFound = True
						continue
						
				if isFound: continue
				
				if len(state) > 4:
					if state[-3:] == ".ui": continue # don't confuse the poor user, plugins can decide to use the .ui version if needed
				
				option = (state, self.factory.ui.resolveStateNameToString(state))
				retadded.append(option)	
				
				if state + ".ui" in obj.states and showUi:
					option = (state + ".ui", self.factory.ui.resolveStateNameToString(state) + " (UI Value)")
					retadded.append(option)	
				
			if len(ret) > 0 and len(retadded) > 0:
				option = ("-line-", self.factory.ui.getSeparator())
				ret.append(option)
				
			ret += retadded	
			
			
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return ret
	
	#
	# Get a list of fields suitable for a list or menu UI field
	#
	def getActions (self, obj):
		ret = {}
		
		try:
			data = self._resolveObject (obj)
			if len(data[0]) == 0: return ret
			
			plugInfo = data[0]
			deviceTypeId = data[1]				
			
			if "xml" in plugInfo == False: return ret
			
			# For some reason the line below doesn't return false properly, using IF ELSE instead
			#if "actions" in plugInfo["xml"] == False: return ret
			if "actions" in plugInfo["xml"]:
				pass
			else:
				return ret
			
			for id, action in plugInfo["xml"]["actions"].iteritems():
				isOk = True
				
				if "DeviceFilter" in action:
					isOk = self._isForDevice (plugInfo, deviceTypeId, action["DeviceFilter"])
				
				if isOk:
					if deviceTypeId[0:7] == "indigo.":
						ret["indigo_" + id] = action
					else:
						ret["plugin_" + id] = action
				 
			# Add Indigo actions as long as this was not already done above
			if deviceTypeId[0:7] != "indigo.":
				data = self._resolveIndigoDevice (obj)
				
				for id, action in data[0]["xml"]["actions"].iteritems():
					isOk = True
				
					if "DeviceFilter" in action:
						isOk = self._isForDevice (data[0], data[1], action["DeviceFilter"])
				
					if isOk:
						ret["indigo_" + id] = action
						
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return ret
		
	#
	# Get a list of variable actions suitable for a list or menu UI field
	#
	def getVariableActionUIList (self, showUIConfig = False):
		ret = []
		
		try:
			plugInfo = self.pluginCache["Indigo"]
			deviceTypeId = "indigo.variable"	
			
			if "xml" in plugInfo == False: return ret
			if "actions" in plugInfo["xml"] == False: return ret
			
			ret = self._getActionUIList (plugInfo, deviceTypeId, showUIConfig, "indigo_")
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return self._cleanReturnList (ret)
		
	#
	# Get a list of sesrver actions suitable for a list or menu UI field
	#
	def getServerActionUIList (self, showUIConfig = False):
		ret = []
		
		try:
			plugInfo = self.pluginCache["Indigo"]
			deviceTypeId = "indigo.server"	
			
			if "xml" in plugInfo == False: return ret
			if "actions" in plugInfo["xml"] == False: return ret
			
			ret = self._getActionUIList (plugInfo, deviceTypeId, showUIConfig, "indigo_")
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return self._cleanReturnList (ret)
		
	#
	# Get a list of actions suitable for a list or menu UI field
	#
	def getActionUIList (self, obj, showUIConfig = False):
		ret = []
		
		try:
			data = self._resolveObject (obj)
			if len(data[0]) == 0: return ret
			
			plugInfo = data[0]
			deviceTypeId = data[1]				
			
			if "xml" in plugInfo == False: return ret
			
			#if "actions" in plugInfo["xml"] == False: return ret
			if "actions" in plugInfo["xml"]:
				pass
			else:
				return ret
			
			if deviceTypeId[0:7] == "indigo.":
				ret = self._getActionUIList (plugInfo, deviceTypeId, showUIConfig, "indigo_")
			else:
				ret = self._getActionUIList (plugInfo, deviceTypeId, showUIConfig)
			
			# Add Indigo actions as long as this was not already done above
			if deviceTypeId[0:7] != "indigo.":
				data = self._resolveIndigoDevice (obj)
				retEx = self._getActionUIList (data[0], data[1], showUIConfig, "indigo_") 
				retEx.append (("-line-", self.factory.ui.getSeparator()))
				ret = retEx + ret
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return self._cleanReturnList (ret)
		
	#
	# Run the action list builder from getActionUIList
	#
	def _getActionUIList (self, plugInfo, deviceTypeId, showUIConfig, prefix = "plugin_"):
		ret = []
		
		try:
			# Run through every device action and add a placeholder, we'll clean up after
			for id, action in plugInfo["xml"]["actions"].iteritems():
				ret.append ("")
							
			for id, action in plugInfo["xml"]["actions"].iteritems():
				isOk = True
				
				if "DeviceFilter" in action:
					isOk = self._isForDevice (plugInfo, deviceTypeId, action["DeviceFilter"])
					
				if "ConfigUI" in action:
					if showUIConfig == False and len(action["ConfigUI"]) > 0: isOk = False

				if isOk:
					if action["Name"] == " - ":
						option = ("-line-", self.factory.ui.getSeparator())
						ret[action["SortOrder"]] = option	
						
					else:
						option = (prefix + id, action["Name"])
						ret[action["SortOrder"]] = option	
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return ret
		
	#
	# Clean up a return list
	#
	def _cleanReturnList (self, dirtyList):
		ret = []
		
		try:
			lastRetItem = ""
			
			for i in range (0, len(dirtyList)):
				try:
					if lastRetItem != "": 
						if lastRetItem == dirtyList[i]: continue # don't add successive duplicates (mostly lines)
						
					if dirtyList[i] != "": lastRetItem = dirtyList[i]
											
					if dirtyList[i] is not None and dirtyList[i] != "": ret.append(dirtyList[i])
				except:
					continue
					
			if len(ret) > 0:
				# Make sure we don't start on a line
				if ret[0] == ("-line-", self.factory.ui.getSeparator()):
					del ret[0]
			
				# Make sure we don't end on a line
				if len(ret) > 0 and ret[len(ret) - 1] == ("-line-", self.factory.ui.getSeparator()):
					del ret[len(ret) - 1]
					
			return ret
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return dirtyList
		
		
	#
	# Compare filter string to device type
	#
	def _isForDevice (self, plugInfo, deviceTypeId, filter):
		try:
			if self._deviceMatchesFilter (plugInfo, deviceTypeId, filter): return True
			
			filters = filter.split(",")
			for f in filters:
				if self._deviceMatchesFilter (plugInfo, deviceTypeId, f): return True
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
		
		return False
		
	#
	# Check if a device type matches a filter
	#
	def _deviceMatchesFilter (self, plugInfo, deviceTypeId, filter):
		try:
			#self.logger.threaddebug ("Checking if filter '{0}' matches device type of '{1}'".format(filter, deviceTypeId))
		
			if filter == "": return True # Global
			filter = filter.strip()
			
			if filter == "self": return True # Global
			if filter == "self." + deviceTypeId: return True # Direct
			if filter == deviceTypeId: return True # Direct
			if filter == plugInfo["id"]: return True # Global
			if filter == plugInfo["id"] + "." + deviceTypeId: return True # Direct
			
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		#self.logger.threaddebug ("Filter '{0}' does not match device type of '{1}'".format(filter, deviceTypeId))
		
		return False
		
	#
	# Resolve an object to it's local plugin details
	#
	def _resolveObject (self, obj):
		try:
			plugInfo = None
			deviceTypeId = ""
			
			if type(obj) is str:
				self.logger.threaddebug ("Object is typed as '{0}'".format(unicode(type(obj))))
			else:
				self.logger.threaddebug ("Object '{0}' is typed as '{1}'".format(obj.name, unicode(type(obj))))
			
			if type(obj) is indigo.Variable:
				return self._resolveIndigoDevice (obj)
				
			elif type(obj) is indigo.Schedule:
				X = 1
				
			elif type(obj) is indigo.Trigger:
				X = 1
				
			elif type(obj) is indigo.ActionGroup:
				X = 1
				
			elif type(obj) is str:
				if obj == "server":
					plugInfo = self.pluginCache["Indigo"]
					deviceTypeId = "indigo.server"
				
			else:
				# It's a device
				if obj.pluginId != "" and obj.pluginId in self.pluginCache:
					plugInfo = self.pluginCache[obj.pluginId]
					deviceTypeId = obj.deviceTypeId
				else:
					# It's an indigo built in device
					return self._resolveIndigoDevice (obj)
				
			return (plugInfo, deviceTypeId)
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return ({}, "")
			
	#
	# Return Indigo device info
	#
	def _resolveIndigoDevice (self, obj):
		try:
			plugInfo = None
			deviceTypeId = ""
			
			plugInfo = self.pluginCache["Indigo"] # It's Indigo
			if type(obj) is indigo.RelayDevice: deviceTypeId = "indigo.relay"
			if type(obj) is indigo.DimmerDevice: deviceTypeId = "indigo.dimmer"
			if type(obj) is indigo.indigo.MultiIODevice: deviceTypeId = "indigo.iodevice"
			if type(obj) is indigo.SensorDevice: deviceTypeId = "indigo.sensor"
			if type(obj) is indigo.SpeedControlDevice: deviceTypeId = "indigo.speedcontrol"
			if type(obj) is indigo.SprinklerDevice: deviceTypeId = "indigo.sprinkler"
			if type(obj) is indigo.ThermostatDevice: deviceTypeId = "indigo.thermostat"
			
			if type(obj) is indigo.Variable: deviceTypeId = "indigo.variable"
		
			return (plugInfo, deviceTypeId)
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return ({}, "")
	
	################################################################################
	# PARSER
	################################################################################	
	#
	# Read in all plugin information and store
	#
	def refresh (self):
		try:
			self.lastUpdate = indigo.server.getTime()
			#self.plugins = self.pluglist()	
			#self.addIndigoActions ()
			
			self.logger.debug ("Refreshing plugin information")
			
			base = indigo.server.getInstallFolderPath() + "/Plugins"
			plugins = glob.glob(base + "/*.indigoPlugin")	
			plugInfo = ''
			
			for plugin in plugins:
				try:
					# IGNORE LIST - some of these cause problems, ignore until a resolution can be determined
					if plugin == base + "/Prowl.indigoPlugin":
						self.logger.info ("Ingoring the {0} plugin because it generates errors when we access it".format("Prowl"))
						continue
						
					if plugin == base + "/Network Devices.indigoPlugin":
						self.logger.info ("Ingoring the {0} plugin because it generates errors when we access it".format("Network Devices"))
						continue	
				
					plugInfo = self._parsePlist (plugin)
					#if plugInfo["id"] != "com.eps.indigoplugin.dev-template": continue

					pluginXML = indigo.Dict()
				
					# If it's this plugin then parse in the Indigo built-in commands
					if plugInfo["id"] == self.factory.plugin.pluginId:
						plugInfoEx = indigo.Dict()
						plugInfoEx["id"] = "Indigo"
						plugInfoEx["name"] = "Indigo Built-In Commands"
						plugInfoEx["path"] = ""
					
						if os.path.isfile(plugin + "/Contents/Server Plugin/lib/actionslib.xml"):
							pluginXML["actions"] = self._parseActionsXML(plugin + "/Contents/Server Plugin/lib/actionslib.xml")
						
						pluginXML["devices"] = indigo.Dict() # Placeholder
						
						plugInfoEx["xml"] = pluginXML	
						self.pluginCache["Indigo"] = plugInfoEx
						#indigo.server.log(unicode(plugInfoEx))	
				
					if os.path.isfile(plugin + "/Contents/Server Plugin/Devices.xml"):
						pluginXML["devices"] = self._parseDevicesXML(plugin + "/Contents/Server Plugin/Devices.xml")
											
					if os.path.isfile(plugin + "/Contents/Server Plugin/Actions.xml"):
						pluginXML["actions"] = self._parseActionsXML(plugin + "/Contents/Server Plugin/Actions.xml")
					
					try:
						plugInfo["xml"] = pluginXML # Represents about 10MB of plugin memory use
						#indigo.server.log(unicode(plugInfo))
						
						self.pluginCache[plugInfo["id"]] = plugInfo
						
					except Exception as e:
						self.logger.error ("Exception encountered with " + unicode(plugin) + " (this error is NOT critical and plugin caching will resume)")
						#self.logger.debug ("Plugin Information: " + unicode(plugInfo))
						self.logger.error (ext.getException(e))	
						continue	
					
				except Exception as e:
					self.logger.error ("Exception encountered with " + unicode(plugin) + " (this error is NOT critical)")
					#self.logger.debug ("Plugin Information: " + unicode(plugInfo))
					self.logger.error (ext.getException(e))	
					
	
			#self._parseDevicesXML(kDevicesFilename)
			#self._parseEventsXML(kEventsFilename)
			#self._parseActionsXML(kActionsFilename)
			
			#self.factory.memory_summary()
			
		except Exception as e:
			#raise
			self.logger.error (ext.getException(e))	
			
	#
	# Parse plist line data (pretty low brow but since plist breaks standard XML reads it works for now)
	#
	def _parsePlist (self, path):
		plugDict = indigo.Dict()
		plugDict["path"] = path
		
		try:
			plist = open(path + "/Contents/Info.plist")
			nameIdx = 0
			name = ""
			idIdx = 0
			id = ""
			for line in plist:
				if nameIdx == 1:
					name = line
					nameIdx = 0
					continue
					
				if idIdx == 1:
					id = line
					idIdx = 0
					continue
					
				x = string.find (line, 'CFBundleDisplayName')
				if x > -1: nameIdx = 1
				
				x = string.find (line, 'CFBundleIdentifier')
				if x > -1: idIdx = 1
				
			#indigo.server.log (name + "\t" + id)
			
			x = string.find (name, "<string>")
			y = string.find (name, "</string>")
			name = name[x + 8:y]
			
			x = string.find (id, "<string>")
			y = string.find (id, "</string>")
			id = id[x + 8:y]
			
			#return self.plugRecord (path, id, name)
			plugDict["id"] = id
			plugDict["name"] = name
					
		except Exception as e:
			self.logger.error (ext.getException(e))	
		
		#return self.plugRecord (path, "Unknown", "Unknown")	
		return plugDict
			
			
	################################################################################
	def _getChildElementsByTagName(self, elem, tagName):
		childList = []
		for child in elem.childNodes:
			if child.nodeType == child.ELEMENT_NODE and (tagName == u"*" or child.tagName == tagName):
				childList.append(child)
		return childList

	def _getXmlFromFile(self, filename):
		if not os.path.isfile(filename):
			return u""
		xml_file = file(filename, 'r')
		xml_data = xml_file.read()
		xml_file.close()
		return xml_data

	def _getXmlFromTemplate(self, templateName):
		filename = indigo.host.resourcesFolderPath + '/templates/' + templateName
		return self._getXmlFromFile(filename)

	def _getElementAttribute(self, elem, attrName, required=True, default=None, errorIfNotAscii=True, filename=u"unknown"):
		attrStr = elem.getAttribute(attrName)
		if attrStr is None or len(attrStr) == 0:
			if required:
				raise ValueError(u"required XML attribute '%s' is missing or empty in file %s" % (attrName,filename))
			return default
		elif errorIfNotAscii and attrStr[0] not in string.ascii_letters:
			raise ValueError(u"XML attribute '%s' in file %s has a value that starts with invalid characters: '%s' (should begin with A-Z or a-z):\n%s" % (attrName,filename,attrStr,elem.toprettyxml()))
		return attrStr

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
		
	################################################################################	
		
	def _parseMenuItemsXML(self, filename):
		if not os.path.isfile(filename):
			return
		try:
			dom = xml.dom.minidom.parseString(self._getXmlFromFile(filename))
		except:
			raise
			raise LookupError(u"%s is malformed" % (filename))
		menuItemsElem = self._getChildElementsByTagName(dom, u"MenuItems")
		if len(menuItemsElem) != 1:
			raise LookupError(u"Incorrect number of <MenuItems> elements found in file %s" % (filename))

		menuItems = self._getChildElementsByTagName(menuItemsElem[0], u"MenuItem")
		for menu in menuItems:
			menuDict = indigo.Dict()
			menuId = self._getElementAttribute(menu, u"id", filename=filename)
			if menuId in self.menuItemsDict:
				raise LookupError(u"Duplicate menu id (%s) found in file %s" % (menuId, filename))

			menuDict[u"Id"] = menuId
			menuDict[u"Name"] = self._getElementValueByTagName(menu, u"Name", False, filename=filename)

			if "Name" in menuDict:
				menuDict[u"ButtonTitle"] = self._getElementValueByTagName(menu, u"ButtonTitle", False, filename=filename)

				# Plugin should specify at least a CallbackMethod or ConfigUIRawXml (possibly both)
				menuDict[u"CallbackMethod"] = self._getElementValueByTagName(menu, u"CallbackMethod", False, filename=filename)
				configUIList = self._getChildElementsByTagName(menu, u"ConfigUI")
				if len(configUIList) > 0:
					#menuDict[u"ConfigUIRawXml"] = self._parseConfigUINode(dom, configUIList[0], filename=filename).toxml()
					menuDict[u"ConfigUI"] = self._parseConfigUINode (dom, configUIList[0])
				else:
					if not "CallbackMethod" in menuDict:
						raise ValueError(u"<MenuItem> elements must contain either a <CallbackMethod> and/or a <ConfigUI> element")

			self.menuItemsList.append(menuDict)
			self.menuItemsDict[menuId] = menuDict
			
	###################
	def _getDeviceStateDictForType(self, type, stateId, triggerLabel, controlPageLabel, disabled=False):
		stateDict = indigo.Dict()
		stateDict[u"Type"] = int(type)
		stateDict[u"Key"] = stateId
		stateDict[u"Disabled"] = disabled
		stateDict[u"TriggerLabel"] = triggerLabel
		stateDict[u"StateLabel"] = controlPageLabel
		return stateDict

	def getDeviceStateDictForSeparator(self, stateId):
		return self._getDeviceStateDictForType(indigo.kTriggerKeyType.Label, stateId, u"_Separator", u"_Separator", True)

	def getDeviceStateDictForSeperator(self, stateId):
		return self.getDeviceStateDictForSeparator(stateId)

	def getDeviceStateDictForNumberType(self, stateId, triggerLabel, controlPageLabel, disabled=False):
		return self._getDeviceStateDictForType(indigo.kTriggerKeyType.Number, stateId, triggerLabel, controlPageLabel, disabled)

	def getDeviceStateDictForStringType(self, stateId, triggerLabel, controlPageLabel, disabled=False):
		return self._getDeviceStateDictForType(indigo.kTriggerKeyType.String, stateId, triggerLabel, controlPageLabel, disabled)

	def getDeviceStateDictForEnumType(self, stateId, triggerLabel, controlPageLabel, disabled=False):
		return self._getDeviceStateDictForType(indigo.kTriggerKeyType.Enumeration, stateId, triggerLabel, controlPageLabel, disabled)

	def getDeviceStateDictForBoolOnOffType(self, stateId, triggerLabel, controlPageLabel, disabled=False):
		stateDict = self._getDeviceStateDictForType(indigo.kTriggerKeyType.BoolOnOff, stateId, triggerLabel, controlPageLabel, disabled)
		stateDict[u"StateLabel"] = stateDict[u"StateLabel"] + u" (on or off)"
		return stateDict

	def getDeviceStateDictForBoolYesNoType(self, stateId, triggerLabel, controlPageLabel, disabled=False):
		stateDict = self._getDeviceStateDictForType(indigo.kTriggerKeyType.BoolYesNo, stateId, triggerLabel, controlPageLabel, disabled)
		stateDict[u"StateLabel"] = stateDict[u"StateLabel"] + u" (yes or no)"
		return stateDict

	def getDeviceStateDictForBoolOneZeroType(self, stateId, triggerLabel, controlPageLabel, disabled=False):
		stateDict = self._getDeviceStateDictForType(indigo.kTriggerKeyType.BoolOneZero, stateId, triggerLabel, controlPageLabel, disabled)
		stateDict[u"StateLabel"] = stateDict[u"StateLabel"] + u" (1 or 0)"
		return stateDict

	def getDeviceStateDictForBoolTrueFalseType(self, stateId, triggerLabel, controlPageLabel, disabled=False):
		stateDict = self._getDeviceStateDictForType(indigo.kTriggerKeyType.BoolTrueFalse, stateId, triggerLabel, controlPageLabel, disabled)
		stateDict[u"StateLabel"] = stateDict[u"StateLabel"] + u" (true or false)"
		return stateDict

	def _parseActionsXML(self, filename):
		ret = indigo.Dict()
		
		if not os.path.isfile(filename):
			return
		try:
			dom = xml.dom.minidom.parseString(self._getXmlFromFile(filename))
		except:
			raise LookupError(u"%s is malformed" % (filename))
		actionsElement = self._getChildElementsByTagName(dom, u"Actions")
		if len(actionsElement) != 1:
			raise LookupError(u"Incorrect number of <Actions> elements found in file %s" % (filename))

		sortIndex = 0
		actionElemList = self._getChildElementsByTagName(actionsElement[0], u"Action")
		for action in actionElemList:
			serverVers = self._getElementAttribute(action, u"_minServerVers", required=False, errorIfNotAscii=False, filename=filename)
			if serverVers is not None and not PluginBase.serverVersCompatWith(serverVers):
				continue	# This version of Indigo Server isn't compatible with this object (skip it)

			actionDict = indigo.Dict()
			actionTypeId = self._getElementAttribute(action, u"id", filename=filename)
			try:
				actionDict[u"DeviceFilter"] = self._getElementAttribute(action, u"deviceFilter", False, u"", filename=filename)
				actionDict[u"Name"] = self._getElementValueByTagName(action, u"Name", filename=filename)
				actionDict[u"CallbackMethod"] = self._getElementValueByTagName(action, u"CallbackMethod", filename=filename)				
			except ValueError:
				# It's missing <Name> or <CallbackMethod> so treat it as a separator
				actionDict[u"Name"] = u" - "
				actionDict[u"CallbackMethod"] = u""
				#actionDict[u"DeviceFilter"] = u""
			actionDict[u"UiPath"] = self._getElementAttribute(action, u"uiPath", required=False, filename=filename)
			actionDict[u"PrivateUiPath"] = self._getElementAttribute(action, u"privateUiPath", required=False, filename=filename)
			actionDict[u"SortOrder"] = sortIndex
			sortIndex += 1

			configUIList = self._getChildElementsByTagName(action, u"ConfigUI")
			if len(configUIList) > 0:
				#actionDict[u"ConfigUIRawXml"] = self._parseConfigUINode(dom, configUIList[0], filename=filename).toxml()
				actionDict[u"ConfigUI"] = self._parseConfigUINode(dom, configUIList[0], filename=filename)
				
			#self.actionsTypeDict[actionTypeId] = actionDict
			ret[actionTypeId] = actionDict

		return ret

	def _parseDevicesXML(self, filename):
		ret = indigo.Dict()
		
		if not os.path.isfile(filename):
			return
		try:
			dom = xml.dom.minidom.parseString(self._getXmlFromFile(filename))
		except Exception, e:
			self.logger.error(u"%s has an error: %s" % (filename, unicode(e)))
			raise LookupError(u"%s is malformed" % (filename))

		# Now get all devices from the <Devices> element
		devicesElement = self._getChildElementsByTagName(dom, u"Devices")
		if len(devicesElement) != 1:
			raise LookupError(u"Incorrect number of <Devices> elements found in file %s" % (filename))

		# Look for a DeviceFactory element - that will be used to create devices
		# rather than creating them directly using the <Device> XML. This allows
		# a plugin to discover device types rather than forcing the user to select
		# the type up-front (like how INSTEON devices are added).
		deviceFactoryElements = self._getChildElementsByTagName(devicesElement[0], u"DeviceFactory")
		if len(deviceFactoryElements) > 1:
			raise LookupError(u"Incorrect number of <DeviceFactory> elements found in file %s" % (filename))
		elif len(deviceFactoryElements) == 1:
			deviceFactory = deviceFactoryElements[0]
			elems = self._getChildElementsByTagName(deviceFactory, u"Name")
			if len(elems) != 1:
				raise LookupError(u"<DeviceFactory> element must contain exactly one <Name> element in file %s" % (filename))
			elems = self._getChildElementsByTagName(deviceFactory, u"ButtonTitle")
			if len(elems) != 1:
				raise LookupError(u"<DeviceFactory> element must contain exactly one <ButtonTitle> element in file %s" % (filename))
			elems = self._getChildElementsByTagName(deviceFactory, u"ConfigUI")
			if len(elems) != 1:
				raise LookupError(u"<DeviceFactory> element must contain exactly one <ConfigUI> element in file %s" % (filename))
			self.deviceFactoryXml = deviceFactory.toxml()
		else:
			self.deviceFactoryXml = None

		sortIndex = 0
		deviceElemList = self._getChildElementsByTagName(devicesElement[0], u"Device")
		for device in deviceElemList:
			
			deviceDict = indigo.Dict()
			deviceTypeId = self._getElementAttribute(device, u"id", filename=filename)
			deviceDict[u"Type"] = self._getElementAttribute(device, u"type", filename=filename)
			if deviceDict[u"Type"] not in validDeviceTypes:
				raise LookupError(u"Unknown device type in file %s" % (filename))
			deviceDict[u"Name"] = self._getElementValueByTagName(device, u"Name", filename=filename)
			deviceDict[u"DisplayStateId"] = self._getElementValueByTagName(device, u"UiDisplayStateId", required=False, default=u"", filename=filename)
			deviceDict[u"SortOrder"] = sortIndex
			sortIndex += 1

			configUIList = self._getChildElementsByTagName(device, u"ConfigUI")
			if len(configUIList) > 0:
				#deviceDict[u"ConfigUIRawXml"] = self._parseConfigUINode(dom, configUIList[0], filename=filename).toxml()
				deviceDict[u"ConfigUI"] = self._parseConfigUINode(dom, configUIList[0], filename=filename)

			deviceStatesElementList = self._getChildElementsByTagName(device, u"States")
			statesList = indigo.List()
			if len(deviceStatesElementList) > 1:
				raise LookupError(u"Incorrect number of <States> elements found in file %s" % (filename))
			elif len(deviceStatesElementList) == 1:
				deviceStateElements = self._getChildElementsByTagName(deviceStatesElementList[0], u"State")
				for state in deviceStateElements:
					stateId = self._getElementAttribute(state, u"id", filename=filename)
					triggerLabel = self._getElementValueByTagName(state, u"TriggerLabel", required=False, default=u"", filename=filename)
					controlPageLabel = self._getElementValueByTagName(state, u"ControlPageLabel", required=False, default=u"", filename=filename)

					disabled = False	# ToDo: need to read this?
					stateValueTypes = self._getChildElementsByTagName(state, u"ValueType")
					if len(stateValueTypes) != 1:
						raise LookupError(u"<State> elements must have exactly one <ValueType> element in file %s" % (filename))

					valueListElements = self._getChildElementsByTagName(stateValueTypes[0], u"List")
					if len(valueListElements) > 1:
						raise LookupError(u"<ValueType> elements must have zero or one <List> element in file %s" % (filename))
					elif len(valueListElements) == 1:
						# It must have a TriggerLabel and a ControlPageLabel
						if (triggerLabel == "") or (controlPageLabel == ""):
							raise LookupError(u"State elements must have both a TriggerLabel and a ControlPageLabel in file %s" % (filename))
						# It's an enumeration -- add an enum type for triggering off of any changes
						# to this enumeration type:
						stateDict = self.getDeviceStateDictForEnumType(stateId, triggerLabel, controlPageLabel, disabled)
						statesList.append(stateDict)

						# And add individual true/false types for triggering off every enumeration
						# value possiblity (as specified by the Option list):
						triggerLabelPrefix = self._getElementValueByTagName(state, u"TriggerLabelPrefix", required=False, default=u"", filename=filename)
						controlPageLabelPrefix = self._getElementValueByTagName(state, u"ControlPageLabelPrefix", required=False, default=u"", filename=filename)

						valueOptions = self._getChildElementsByTagName(valueListElements[0], u"Option")
						if len(valueOptions) < 1:
							raise LookupError(u"<List> elements must have at least one <Option> element in file %s" % (filename))
						for option in valueOptions:
							subStateId = stateId + u"." + self._getElementAttribute(option, u"value", filename=filename)

							if len(triggerLabelPrefix) > 0:
								subTriggerLabel = triggerLabelPrefix + u" " + option.firstChild.data
							else:
								subTriggerLabel = option.firstChild.data

							if len(controlPageLabelPrefix) > 0:
								subControlPageLabel = controlPageLabelPrefix + u" " + option.firstChild.data
							else:
								subControlPageLabel = option.firstChild.data

							subDisabled = False		# ToDo: need to read this?

							subStateDict = self.getDeviceStateDictForBoolTrueFalseType(subStateId, subTriggerLabel, subControlPageLabel, subDisabled)
							statesList.append(subStateDict)
					else:
						# It's not an enumeration
						stateDict = None
						valueType = stateValueTypes[0].firstChild.data.lower()
						# It must have a TriggerLabel and a ControlPageLabel if it's not a separator
						if (valueType != u"separator"):
							if (triggerLabel == "") or (controlPageLabel == ""):
								raise LookupError(u"State elements must have both a TriggerLabel and a ControlPageLabel in file %s" % (filename))
						if valueType == u"boolean":
							boolType = stateValueTypes[0].getAttribute(u"boolType").lower()
							if boolType == u"onoff":
								stateDict = self.getDeviceStateDictForBoolOnOffType(stateId, triggerLabel, controlPageLabel, disabled)
							elif boolType == u"yesno":
								stateDict = self.getDeviceStateDictForBoolYesNoType(stateId, triggerLabel, controlPageLabel, disabled)
							elif boolType == u"onezero":
								stateDict = self.getDeviceStateDictForBoolOneZeroType(stateId, triggerLabel, controlPageLabel, disabled)
							else:
								stateDict = self.getDeviceStateDictForBoolTrueFalseType(stateId, triggerLabel, controlPageLabel, disabled)
						elif valueType == u"number" or valueType == u"float" or valueType == u"integer":
							stateDict = self.getDeviceStateDictForNumberType(stateId, triggerLabel, controlPageLabel, disabled)
						elif valueType == u"string":
							stateDict = self.getDeviceStateDictForStringType(stateId, triggerLabel, controlPageLabel, disabled)
						elif valueType == u"separator":
							stateDict = self.getDeviceStateDictForSeparator(stateId)

						if stateDict:
							statesList.append(stateDict)
			deviceDict[u"States"] = statesList
	
			ret[deviceTypeId] = deviceDict

		return ret
	
	
	################################################################################		
	def _parseConfigUINode(self, mainDom, configUI, filename=u"unknown"):
		UIDict = indigo.Dict()
				
		fieldElements = self._getChildElementsByTagName(configUI, u"Field")
		if len(fieldElements) > 0:
			fieldList = indigo.List()
			
			for field in fieldElements:
				fieldDict = indigo.Dict()
				fieldDict["separator"] = False
				
				try:		
					fieldDict["id"] = self._getElementAttribute(field, u"id", required=True, default="", errorIfNotAscii=False, filename=filename)
				except:
					fieldDict["id"] = ""
					
				try:		
					fieldDict["ValueType"] = self._getElementAttribute(field, u"valueType", required=False, default="", errorIfNotAscii=False, filename=filename)
				except:
					fieldDict["ValueType"] = "string"
					
				try:		
					fieldDict["Default"] = self._getElementAttribute(field, u"defaultValue", required=False, default="", errorIfNotAscii=False, filename=filename)
				except:
					fieldDict["Default"] = None
					
				fieldDict["type"] = fieldId = self._getElementAttribute(field, u"type", filename=filename)
				if fieldDict["type"].lower() == "separator": fieldDict["separator"] = True
				isHidden = self._getElementAttribute(field, u"hidden", required=False, default="false", filename=filename)
				if isHidden.lower() == "true": 
					fieldDict["hidden"] = True
				else:
					fieldDict["hidden"] = False
					
				try:
					fieldDict["Label"] = self._getElementValueByTagName(field, u"Label", required=False, default="", filename=filename)
				except:
					fieldDict["Label"] = ""
					
				try:
					fieldDict["Description"] = self._getElementValueByTagName(field, u"Description", required=False, default="", filename=filename)
				except:
					fieldDict["Description"] = ""
			
				listList = indigo.List()
				
				listElements = self._getChildElementsByTagName(field, u"List")
				if len(listElements) > 0:
					listDict = indigo.Dict()
					listDict["class"] = self._getElementAttribute(listElements[0], u"class", required=False, default="", filename=filename)
					
					optionsList = indigo.List()
					
					optionElements = self._getChildElementsByTagName(listElements[0], u"Option")
					if len(optionElements) > 0:
						for option in optionElements:
							optionDict = indigo.Dict()
							optionDict["value"] = self._getElementAttribute(option, u"value", required=False, default="", errorIfNotAscii=False, filename=filename)
							optionDict["Label"] = option.childNodes[0].data
							optionsList.append(optionDict)
						
					listDict["Options"] = optionsList
						
					listList.append(listDict)
					
				fieldDict["List"] = listList
			
				fieldList.append(fieldDict)
				
			UIDict["Fields"] = fieldList
		
		return UIDict


























