# Indigo Voice Plugin API
# Copyright (c) 2018 ColoradoFourWheeler / EPS
# Version 1.0.0
#
# Include this library in your plugin using the following syntax at the top of your Indigo plugin:
#
#	If saving ivoice.py to a subfolder under Server Plugin called "lib" (for example):
# 		from lib.ivoice import IndigoVoice
# 		hbb = HomebridgeBuddy()
#
#		If you include it from a subfolder please ensure that the folder has a file named __init__.py as well. This file can be blank but MUST be present.
#
#	If saving ivoice.py to the same folder as plugin.py:
#		
#		from ivoice import IndigoVoice
#		ivoice = IndigoVoice()
#
# Place the following function definitions into your plugin.py file to utilize this library:
#	def voiceIntegrationFieldChange (self, valuesDict, typeId, devId): return ivoice.integrationFieldChange (valuesDict, typeId, devId)
#	def voiceHKBIntegrationServerList (self, filter="", valuesDict=None, typeId="", targetId=0): return ivoice.integrationServerList (filter, valuesDict, typeId, targetId)
#	def voiceAHBIntegrationServerList (self, filter="", valuesDict=None, typeId="", targetId=0): return ivoice.integrationServerList (filter, valuesDict, typeId, targetId)
#	def voiceIntegrationHKBDeviceTypeList (self, filter="", valuesDict=None, typeId="", targetId=0): return ivoice.integrationDeviceList (filter, valuesDict, typeId, targetId)
	



import indigo
import logging
import linecache
import sys

class IndigoVoice:
	# Enumerations
	kHomeKitPlugin = u'com.eps.indigoplugin.homekit-bridge'
	kAlexaPlugin = u'com.indigodomo.opensource.alexa-hue-bridge'
	
	kVoiceAPIActionName = u'voiceAPI'
	
	#
	# Initialize the class
	#
	def __init__ (self):
		self.logger = logging.getLogger ("Plugin.ivoice")
		self.libversion = "1.0.0"
		
		self.HKB = indigo.server.getPlugin(kHomeKitPlugin)
		self.AHB = indigo.server.getPlugin(kAlexaPlugin)
		
		self.logger.debug ("Starting Indigo Voice plugin API version {0}".format(self.version))
		
	#
	# Report back our version number (in case the calling plugin wants to include that in their support dump)
	#
	def version (self):
		return self.libversion
		
	#
	# Check that props/valuesDict has the required fields
	#
	def checkFields (self, valuesDict):
		try:
			errorDict = indigo.Dict()
			success = True
			
			requiredFields = ["voiceIntegrated", "voiceHKBAvailable", "voiceAHBAvailable", "voiceHKBServer", "voiceAHBServer", "voiceHKBDeviceType"]
			
			for r in requiredFields:		
				if "voiceIntegrated" not in valuesDict:
					errorDict["showAlertText"] 		= "Indigo voice integration failure.  Device is missing the voiceIntegrated field, integration is not possible."
					return (False, valuesDict, errorDict)
		
		except Exception as e:
			success = False
			errorDict["showAlertText"] = unicode(e)
			self.logger.error (self.getException(e))
			
		return (success, valuesDict, errorDict)
			
			
	#
	# Request that HBB add a device to a server
	#
	def addDevice (self, devId, valuesDict, plug = self.kHomeKitPlugin):
		try:
			# Check for all required fields
			(chSuccess, chValues, chErrors) = self.checkFields (valuesDict)
			if not chSuccess:
				return False
				
			success = True
			plugin = indigo.server.getPlugin(plug)
			
			if plugin.isEnabled():
				apiprops = {}
				apiprops["libversion"] = self.version()
				apiprops["command"] = "addDevice"
				apiprops["params"] = (devId, valuesDict)
				
				(success, data, errors) = plugin.executeAction(self.kVoiceAPIActionName, deviceId=0, waitUntilDone=True, props=apiprops)
			
				if not success:
					self.logger.error (errors["message"])
					return False

			else:
				self.logger.error ("Attempting to add a device to {} but neither is enabled.".format(plugin.name))
				return False
						
		except Exception as e:
			success = False
			errorDict["showAlertText"] = unicode(e)
			self.logger.error (self.getException(e))
			
		return success
		
	#
	# Request that HBB update a device
	#
	def updateDevice (self, devId, valuesDict, plug = self.kHomeKitPlugin):
		try:
			# Check for all required fields
			(chSuccess, chValues, chErrors) = self.checkFields (valuesDict)
			if not chSuccess:
				return False
				
			success = True
			plugin = indigo.server.getPlugin(plug)
			
			if plugin.isEnabled():
				apiprops = {}
				apiprops["libversion"] = self.version()
				apiprops["command"] = "updateDevice"
				apiprops["params"] = (devId, valuesDict)
				
				(success, data, errors) = plugin.executeAction(self.kVoiceAPIActionName, deviceId=0, waitUntilDone=True, props=apiprops)
				
				if not success:
					self.logger.error (errors["message"])
					return False
				
			else:
				self.logger.error ("Attempting to update a device on {} but it is not enabled.".format(plugin.name))
				return False
						
		except Exception as e:
			success = False
			errorDict["showAlertText"] = unicode(e)
			self.logger.error (self.getException(e))
			
		return success	
	
	#
	# An HBB Integration API form field changed
	#
	def integrationFieldChange (self, valuesDict, typeId, devId):
		try:
			errorDict = indigo.Dict()
			
			hkb = indigo.server.getPlugin(self.kHomeKitPlugin)
			ahb = indigo.server.getPlugin(self.kAlexaPlugin)
			
			# Check for all required fields
			(chSuccess, chValues, chErrors) = self.checkFields (valuesDict)
			if not chSuccess:
				return (chValues, chErrors)
			
			if valuesDict["voiceIntegrated"]:
				# Set fields based on integraton
				valuesDict["voiceHKBAvailable"] = True
				valuesDict["voiceAHBAvailable"] = False # Until we get Alexa integration keep this at false
				if hkb.pluginDisplayName == "- plugin not installed -": valuesDict["voiceHKBAvailable"] = False
				if ahb.pluginDisplayName == "- plugin not installed -": valuesDict["voiceAHBAvailable"] = False
								
				# Make sure they have the required fields
				if not valuesDict["voiceHKBAvailable"] and not valuesDict["voiceAHBAvailable"]:
					valuesDict["voiceIntegrated"] 		= False
					errorDict["voiceIntegrated"] 		= "Voice integration plugin not installed"
					errorDict["showAlertText"] 			= "Please install HomeKit Bridge from the Indigo plugin store to enable this device for HomeKit."
					#errorDict["showAlertText"] 		= "Please install HomeKit Bridge from the Indigo plugin store to enable this device for HomeKit and/or the Alexa-Hue Bridge from the Indigo plugin store to enable this device for Alexa."
					return (valuesDict, errorDict)
					
				# If the have HKB and it's disabled and AHB is not installed at all
				if hkb.isEnabled() == False and not valuesDict["voiceAHBAvailable"]:
					valuesDict["voiceIntegrated"] 		= False
					errorDict["voiceIntegrated"] 		= "HomeKit Bridge not enabled"
					errorDict["showAlertText"] 			= "HomeKit Bridge is currently disabled and this plugin cannot talk to it, please re-enable HomeKit Bridge before trying to add this device to HomeKit."
					return (valuesDict, errorDict)
					
				# If the have AHB and it's disabled and HKB is not installed at all
				#if ahb.isEnabled() == False and not valuesDict["voiceHKBAvailable"]:
				#	valuesDict["voiceIntegrated"] 		= False
				#	errorDict["voiceIntegrated"] 		= "Alexa-Hue Bridge not enabled"
				#	errorDict["showAlertText"] 			= "Alexa-Hue Bridge is currently disabled and this plugin cannot talk to it, please re-enable Alexa-Hue Bridge before trying to add this device to Alexa."
				#	return (valuesDict, errorDict)	
				
				# If all voice integration is not enabled
				#if hkb.isEnabled() == False and ahb.isEnabled() == False:
				#	valuesDict["voiceIntegrated"] 		= False
				#	errorDict["voiceIntegrated"] 		= "Voice integration plugins are not enabled"
				#	errorDict["showAlertText"] 			= "All voice integration plugins are currently disabled and this plugin cannot talk to them, please re-enable HomeKit Bridge and/or Alexa-Hue Bridge before trying to add this device to HomeKit or Alexa."
				#	return (valuesDict, errorDict)
				
				# Just to be safe, do a blank call to the API to make sure our version is OK
				success = False
				apiprops = {}
				apiprops["libversion"] = self.version()
				apiprops["command"] = "none"
				apiprops["params"] = "none"
				
				if hkb.isEnabled():	
					hkbVer = int(hkb.pluginVersion.replace(".", ""))
					if hkbVer < 130:
						valuesDict["voiceIntegrated"] 		= False
						errorDict["voiceIntegrated"] 		= "HomeKit Bridge needs upgraded"
						errorDict["showAlertText"] 			= "You are running a version of HomeKit Bridge that does not support this feature, please upgrade to the latest version to enable this device for HomeKit."
						return (valuesDict, errorDict)	
						
					(success, data, errors) = hkb.executeAction(self.kVoiceAPIActionName, deviceId=0, waitUntilDone=True, props=apiprops)
					
				#if ahb.isEnabled():	
				#	ahbVer = int(ahb.pluginVersion.replace(".", ""))
				#	if ahbVer < 130:
				#		valuesDict["voiceIntegrated"] 		= False
				#		errorDict["voiceIntegrated"] 		= "HomeKit Bridge needs upgraded"
				#		errorDict["showAlertText"] 			= "You are running a version of HomeKit Bridge that does not support this feature, please upgrade to the latest version to enable this device for HomeKit."
				#		return (valuesDict, errorDict)		
					
				#	(success, data, errors) = ahb.executeAction(self.kVoiceAPIActionName, deviceId=0, waitUntilDone=True, props=apiprops)
				
				if not success:
					self.logger.error (errors["message"])
					valuesDict["voiceIntegrated"] 		= False
					valuesDict["voiceHKBServer"] 		= "none"
					valuesDict["voiceHKBDeviceType"] 	= "default"
					errorDict["showAlertText"]			= errors["message"]
					return (valuesDict, errorDict)	
				
				if valuesDict["voiceHKBServer"] == "": valuesDict["voiceHKBServer"]			= "none" # In case there is a problem
				if valuesDict["voiceHKBDeviceType"] == "": valuesDict["voiceHKBDeviceType"] = "default"
					
			
		except Exception as e:
			success = False
			errorDict["showAlertText"] = unicode(e)
			self.logger.error (self.getException(e))
			
		return (valuesDict, errorDict)	
		

	#
	# Request a list of valid servers from HomeKit Bridge
	#
	def HKBIntegrationServerList (self, filter="", valuesDict=None, typeId="", targetId=0):
		try:
			ret = [("default", "No HomeKit Bridge servers found")]
			
			if "voiceHKBAvailable" in valuesDict:
				if valuesDict["voiceHKBAvailable"]:
					hkb = indigo.server.getPlugin(self.kHomeKitPlugin)
					if hkb.isEnabled():
						apiprops = {}
						apiprops["libversion"] = self.version()
						apiprops["command"] = "getServerList"
						apiprops["params"] = "server" # Cannot add devices to guests or customs for now since guest is an exclusion of a server and custom doesn't integrate into Indog
						
						(success, data, errors) = hkb.executeAction(self.kVoiceAPIActionName, deviceId=0, waitUntilDone=True, props=apiprops)
						
						if success:
							ret = []
							for d in data:
								ret.append ((d[0], d[1]))
						else:
							self.logger.error (errors["message"])

		except Exception as e:
			self.logger.error (self.getException(e))
			
		return ret
		
	#
	# Request a list of valid servers from Alexa Hue Bridge
	#
	def AHBIntegrationServerList (self, filter="", valuesDict=None, typeId="", targetId=0):
		try:
			ret = [("default", "No Alexa-Hue Bridge servers found")]
			
			if "voiceAHBAvailable" in valuesDict:
				if valuesDict["voiceAHBAvailable"]:
					ahb = indigo.server.getPlugin(self.kAlexaPlugin)
					if ahb.isEnabled():
						apiprops = {}
						apiprops["libversion"] = self.version()
						apiprops["command"] = "getServerList"
						apiprops["params"] = "server" # Cannot add devices to guests or customs for now since guest is an exclusion of a server and custom doesn't integrate into Indog
						
						(success, data, errors) = ahb.executeAction(self.kVoiceAPIActionName, deviceId=0, waitUntilDone=True, props=apiprops)
						
						if success:
							ret = []
							for d in data:
								ret.append ((d[0], d[1]))
						else:
							self.logger.error (errors["message"])

		except Exception as e:
			self.logger.error (self.getException(e))
			
		return ret		
	
	#
	# Request a list of valid device types from HomeKit Bridge
	#	
	def IntegrationHKBDeviceTypeList (self, filter="", valuesDict=None, typeId="", targetId=0):
		try:
			ret = [("default", "No Homebridge types found")]
			
			if "voiceHKBAvailable" in valuesDict:
				if valuesDict["voiceHKBAvailable"]:
					hkb = indigo.server.getPlugin(self.kHomeKitPlugin)
					if hkb.isEnabled():
						apiprops = {}
						apiprops["libversion"] = self.version()
						apiprops["command"] = "getDeviceTypes"
						apiprops["params"] = "allowNone"
						
						(success, data, errors) = hkb.executeAction(self.kVoiceAPIActionName, deviceId=0, waitUntilDone=True, props=apiprops)
						
						if success:
							ret = []
							for d in data:
								ret.append ((d[0], d[1]))
						else:
							self.logger.error (errors["message"])

		except Exception as e:
			self.logger.error (self.getException(e))
			
		return ret	
		
	#
	# Validate device config
	#
	def validateDeviceConfigUi(self, valuesDict, typeId, devId):
		try:
			errorDict = indigo.Dict()
			
			if "voiceIntegrated" in valuesDict:
				if valuesDict["voiceIntegrated"]:
					if valuesDict["voiceHKBAvailable"]:
						if valuesDict["voiceHKBServer"] == "":
							errorDict["voiceHKBServer"] 	= "Select a HomeKit Bridge server"
							errorDict["showAlertText"] 		= "If you opt to integrate with HomeKit Bridge then you must select which server to attach this device to."
							return (valuesDict, errorDict)
						
						if valuesDict["voiceHKBDeviceType"] == "":
							errorDict["voiceHKBDeviceType"] = "Select a HomeKit Bridge device type"
							errorDict["showAlertText"] 		= "If you opt to integrate with HomeKit Bridge then you must select how you want this device treated."
							return (valuesDict, errorDict)
			
		except Exception as e:
			self.logger.error (self.getException(e))
			
		return (valuesDict, errorDict)
		
	#
	# Get exception details
	#
	def getException (self, e):
		exc_type, exc_obj, tb = sys.exc_info()
		f = tb.tb_frame
		lineno = tb.tb_lineno
		filenameEx = f.f_code.co_filename
		filename = filenameEx.split("/")
		filename = filename[len(filename)-1]
		filename = filename.replace(".py", "")
		filename = filename.replace(".pyc","")
		linecache.checkcache(filename)
		line = linecache.getline(filenameEx, lineno, f.f_globals)
		exceptionDetail = "Exception in %s.%s line %i: %s\n\t\t\t\t\t\t\t CODE: %s" % (filename, f.f_code.co_name, lineno, str(e), line.replace("\t",""))
	
		return exceptionDetail		