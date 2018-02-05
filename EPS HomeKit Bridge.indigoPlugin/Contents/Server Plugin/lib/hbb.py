# Homebridge Buddy Plugin API
# Copyright (c) 2018 ColoradoFourWheeler / EPS
# Version 1.0.0
#
# Include this library in your plugin using the following syntax at the top of your Indigo plugin:
#
#	If saving hbb.py to a subfolder under Server Plugin called "lib" (for example):
# 		from lib.hbb import HomebridgeBuddy
# 		hbb = HomebridgeBuddy()
#
#		If you include it from a subfolder please ensure that the folder has a file named __init__.py as well. This file can be blank but MUST be present.
#
#	If saving hbb.py to the same folder as plugin.py:
#		
#		from hbb import HomebridgeBuddy
#		hbb = HomebridgeBuddy()
#
# Place the following function definitions into your plugin.py file to utilize this library:
#	def checkForPlugin (self): return hbb.hbbCheckForPlugin ()
#	def integrationFieldChange (self, valuesDict, typeId, devId): return hbb.hbbIntegrationFieldChange (valuesDict, typeId, devId)
#	def integrationServerList (self, filter="", valuesDict=None, typeId="", targetId=0): return hbb.hbbIntegrationServerList (filter, valuesDict, typeId, targetId)
#	def integrationTreatAsList (self, filter="", valuesDict=None, typeId="", targetId=0): return hbb.hbbIntegrationTreatAsList (filter=, valuesDict, typeId, targetId)
#



import indigo
import logging
import linecache
import sys

class HomebridgeBuddy:
	
	#
	# Initialize the class
	#
	def __init__ (self):
		self.logger = logging.getLogger ("Plugin.hbb")
		self.libversion = "1.0.0"
		
		self.logger.debug ("Starting Homebridge Buddy plugin API version {0}".format(self.version))
		
	#
	# Report back our version number (in case the calling plugin wants to include that in their support dump)
	#
	def version (self):
		return self.libversion
		
	#
	# Check for Homebridge Buddy
	#
	def checkForPlugin (self):
		try:
			return indigo.server.getPlugin("com.eps.indigoplugin.homebridge")
			
		except Exception as e:
			success = False
			errorDict["showAlertText"] = unicode(e)
			self.logger.error (self.getException(e))
			
	#
	# Check that props/valuesDict has the required fields
	#
	def checkFields (self, valuesDict):
		try:
			errorDict = indigo.Dict()
			success = True
			
			if "hbbIntegrated" not in valuesDict:
				errorDict["showAlertText"] 		= "Homebridge Buddy integration failure.  Device is missing the hbbIntegrated field, integration is not possible."
				return (False, valuesDict, errorDict)
				
			if "hbbServer" not in valuesDict:
				errorDict["showAlertText"] 		= "Homebridge Buddy integration failure.  Device is missing the hbbServer field, integration is not possible."
				return (False, valuesDict, errorDict)
				
			if "hbbTreatAs" not in valuesDict:
				errorDict["showAlertText"] 		= "Homebridge Buddy integration failure.  Device is missing the hbbTreatAs field, integration is not possible."
				return (False, valuesDict, errorDict)	
		
		except Exception as e:
			success = False
			errorDict["showAlertText"] = unicode(e)
			self.logger.error (self.getException(e))
			
		return (success, valuesDict, errorDict)
			
			
	#
	# Request that HBB add a device to a server
	#
	def addDevice (self, devId, valuesDict):
		try:
			# Check for all required fields
			(chSuccess, chValues, chErrors) = self.checkFields (valuesDict)
			if not chSuccess:
				return False
				
			success = True
			hbb = self.checkForPlugin()
			
			if hbb.isEnabled():
				apiprops = {}
				apiprops["libversion"] = self.version()
				apiprops["command"] = "addDevice"
				apiprops["params"] = (devId, valuesDict)
				
				(success, data, errors) = hbb.executeAction('hbbAPI', deviceId=0, waitUntilDone=True, props=apiprops)
				
				if not success:
					self.logger.error (errors["message"])
					return False
				
			else:
				self.logger.error ("Attempting to add a device to Homebridge Buddy but Homebridge Buddy is not enabled.")
				return False
						
		except Exception as e:
			success = False
			errorDict["showAlertText"] = unicode(e)
			self.logger.error (self.getException(e))
			
		return success
		
	#
	# Request that HBB update a device
	#
	def updateDevice (self, devId, valuesDict):
		try:
			# Check for all required fields
			(chSuccess, chValues, chErrors) = self.checkFields (valuesDict)
			if not chSuccess:
				return False
				
			success = True
			hbb = self.checkForPlugin()
			
			if hbb.isEnabled():
				apiprops = {}
				apiprops["libversion"] = self.version()
				apiprops["command"] = "updateDevice"
				apiprops["params"] = (devId, valuesDict)
				
				(success, data, errors) = hbb.executeAction('hbbAPI', deviceId=0, waitUntilDone=True, props=apiprops)
				
				if not success:
					self.logger.error (errors["message"])
					return False
				
			else:
				self.logger.error ("Attempting to update a device on Homebridge Buddy but Homebridge Buddy is not enabled.")
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
			
			hbb = self.checkForPlugin()
			
			# Check for all required fields
			(chSuccess, chValues, chErrors) = self.checkFields (valuesDict)
			if not chSuccess:
				return (chValues, chErrors)
			
			if valuesDict["hbbIntegrated"]:
				# Make sure they have the required fields
				if hbb.pluginDisplayName == "- plugin not installed -":
					valuesDict["hbbIntegrated"] 	= False
					errorDict["hbbIntegrated"] 		= "Homebridge Buddy not installed"
					errorDict["showAlertText"] 		= "Please install Homebridge Buddy from the Indigo plugin store to enable this device for HomeKit."
					return (valuesDict, errorDict)
					
				if hbb.isEnabled() == False:
					valuesDict["hbbIntegrated"] 	= False
					errorDict["hbbIntegrated"] 		= "Homebridge Buddy not enabled"
					errorDict["showAlertText"] 		= "Homebridge Buddy is currently disabled and this plugin cannot talk to it, please re-enable Homebridge Buddy before trying to add this device to HomeKit."
					return (valuesDict, errorDict)	
					
				hbbVer = int(hbb.pluginVersion.replace(".", ""))
				if hbbVer < 107:
					valuesDict["hbbIntegrated"] 	= False
					errorDict["hbbIntegrated"] 		= "Homebridge Buddy needs upgraded"
					errorDict["showAlertText"] 		= "You are running a version of Homebridge Buddy that does not support this feature, please upgrade to the latest version to enable this device for HomeKit."
					return (valuesDict, errorDict)	
					
				# Just to be safe, do a blank call to the API to make sure our version is OK
				apiprops = {}
				apiprops["libversion"] = self.version()
				apiprops["command"] = "none"
				apiprops["params"] = "none"
				
				(success, data, errors) = hbb.executeAction('hbbAPI', deviceId=0, waitUntilDone=True, props=apiprops)
				
				if not success:
					self.logger.error (errors["message"])
					valuesDict["hbbIntegrated"] = False
					valuesDict["hbbServer"] 	= "none"
					valuesDict["hbbTreatAs"] 	= "default"
					errorDict["showAlertText"]	= errors["message"]
					return (valuesDict, errorDict)	
				
				if valuesDict["hbbServer"] == "": valuesDict["hbbServer"] 	= "none" # In case there is a problem
				if valuesDict["hbbTreatAs"] == "": valuesDict["hbbTreatAs"] = "default"
					
			
		except Exception as e:
			success = False
			errorDict["showAlertText"] = unicode(e)
			self.logger.error (self.getException(e))
			
		return (valuesDict, errorDict)	
		

	#
	# Request a list of valid servers from Homebridge Buddy
	#
	def integrationServerList (self, filter="", valuesDict=None, typeId="", targetId=0):
		try:
			ret = [("default", "No Homebridge Buddy servers found")]
			
			if "hbbIntegrated" in valuesDict:
				if valuesDict["hbbIntegrated"]:
					hbb = self.checkForPlugin()
					if hbb.isEnabled():
						apiprops = {}
						apiprops["libversion"] = self.version()
						apiprops["command"] = "getServerList"
						apiprops["params"] = "server" # Cannot add devices to guests or customs for now since guest is an exclusion of a server and custom doesn't integrate into Indog
						
						(success, data, errors) = hbb.executeAction('hbbAPI', deviceId=0, waitUntilDone=True, props=apiprops)
						
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
	# Request a list of valid device types from Homebridge Buddy
	#	
	def integrationTreatAsList (self, filter="", valuesDict=None, typeId="", targetId=0):
		try:
			ret = [("default", "No Homebridge types found")]
			
			if "hbbIntegrated" in valuesDict:
				if valuesDict["hbbIntegrated"]:
					hbb = self.checkForPlugin()
					if hbb.isEnabled():
						apiprops = {}
						apiprops["libversion"] = self.version()
						apiprops["command"] = "getDeviceTypes"
						apiprops["params"] = "allowNone"
						
						(success, data, errors) = hbb.executeAction('hbbAPI', deviceId=0, waitUntilDone=True, props=apiprops)
						
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
			
			if "hbbIntegrated" in valuesDict:
				if valuesDict["hbbIntegrated"]:
					if valuesDict["hbbServer"] == "":
						errorDict["hbbServer"] 			= "Select a Homebridge Buddy server"
						errorDict["showAlertText"] 		= "If you opt to integrate with Homebridge Buddy then you must select which server to attach this device to."
						return (valuesDict, errorDict)
						
					if valuesDict["hbbTreatAs"] == "":
						errorDict["hbbTreatAs"] 		= "Select a Homebridge Buddy device type"
						errorDict["showAlertText"] 		= "If you opt to integrate with Homebridge Buddy then you must select how you want this device treated."
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