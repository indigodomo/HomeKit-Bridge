# eps.actions3 - Manage and execute actions (rewritten from original actions.py)
#
# Copyright (c) 2018 ColoradoFourWheeler / EPS
#
# For this to work there needs to be an Action 3 block in the devices that has our stock field names

import indigo
import logging

import ext
import dtutil

import re
import json

class actions:	
	FIELDLIST = ["actionsCommandReferenceField", "actionsCommandEnable", "actionsArgsEnable", "actionsCommandArgsValueType", "actionsCommandSelect", "actionsCommandArgs", "actionsCommandArgsValueList", "actionsCommandArgsValueText", "actionsCommandArgsValueCheckbox"]
	ATTRIBUTELIST = ["actionsCommandArgsChanged", "actionsCommandArgsValueChanged"]
	LOCALCACHE = {} # A copy of the plugdetails cache plus the saved version of what we are currently working on, gets cleared when the form is closed

	#
	# Initialize the  class
	#
	def __init__(self, factory):
		self.logger = logging.getLogger ("Plugin.actions")
		self.factory = factory
		
		for k, v in self.factory.plugdetails.pluginCache.iteritems():
			self.LOCALCACHE[k] = v

	#
	# Get the actions for a given object
	#
	def getActionsForObject (self, obj):
		try:
			objtype = str(type(obj)).replace("<class '", "").replace("'>", "")
			
			#indigo.server.log(objtype)
			
			if objtype == "custom":
				self.logger.debug ("Actions 3 does not currently support custom device types, '{0}' actions could not be compiled".format(obj.name))
				return None
				
			
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
	#
	# Same as getCustomList in UI but for Actions library
	#
	def getActionList (self, filter="", valuesDict=None, typeId="", targetId=0):			
		try:
			ret = [("default", "No data")]
			
			method = re.findall("\#.*?\#", filter)
			if len(method) == 0: return ret
	
			listType = method[0].replace("#", "")
			filter = filter.replace(method[0], "")

			args = {}
			index = ""
			callback = ""
	
			if filter != "":
				filter = filter.replace("[", "").replace("]","")
				for f in filter.split(","):
					f = f.strip()			
					valkey = f.split("=")
					args[valkey[0].lower().strip()] = valkey[1].strip()
					if valkey[0].lower().strip() == "index":
						index = valkey[1].strip()
					if valkey[0].lower().strip() == "callback":
						callback = valkey[1].strip()
					if valkey[0].lower().strip() == "includetarget":
						if valkey[1].lower() == "true":
							del args[valkey[0].lower().strip()]
							args["targetId"] = str(targetId)
						

			#indigo.server.log(unicode(index))
			#if index != "": args["index"] = index
			
			# Index can throw things off, make sure it's not in args
			if "index" in args: del args["index"]

			results = []
			
			if listType.lower() == "fields": 
				results = self._getActionList_Fields (args, valuesDict)
				
			return results
					
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return ret	
			
	#
	# Return list of UI fields for a device and command
	#
	def _getActionList_Fields (self, args, valuesDict):
		try:
			ret = [("default", "No data")]
			retlist = []
			
			if "srcfield" not in args: return ret
			if args["srcfield"] == "": return ret
			if args["srcfield"] not in valuesDict: return ret
			if valuesDict[args["srcfield"]] == "": return ret
			if valuesDict[args["srcfield"]][0] == "-": return ret # our standard "extra" notation, i.e., -none-
			if valuesDict["actionsCommandSelect"] == "": return ret
			if valuesDict["actionsCommandSelect"] == "default": return ret
			
			if "plugdetails" not in dir(self.factory):
				self.logger.error ("Unable to use actions unless the plugdetails library is also loaded.")
				return ret
			
			dev = indigo.devices[int(valuesDict[args["srcfield"]])]
			
			rawcommand = valuesDict["actionsCommandSelect"]
			
			#indigo.server.log(rawcommand)
			
			if rawcommand[0:7] == "indigo_":
				# Get command arguments from the Indigo definitions
				plugInfo = self.factory.plugdetails.pluginCache["Indigo"]
				rawcommand = rawcommand.replace("indigo_", "")
				
			else:
				plugInfo = {}
				
			# Add a none option to the top of the list in case they don't need or want to set arguments
			retlist.append (("-none-", "None"))
			retlist = self.factory.ui.addLine (retlist)
				
			for cmd, action in plugInfo["xml"]["actions"].iteritems():
				if cmd == rawcommand:
					for field in action["ConfigUI"]["Fields"]:
						retlist.append ( (field["id"], field["Label"] ) )
			
			return retlist
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return ret		
			
			
			
	################################################################################
	# USER INTERFACE FORM FUNCTIONS
	################################################################################			
	
	#
	# Get the raw command and plugInfo for the currently selected form command
	#
	def getPlugInfoForForm (self, valuesDict):
		try:
			plugInfo = {}
			rawcommand = valuesDict["actionsCommandSelect"]
			
			if rawcommand[0:7] == "indigo_":
				# Get command arguments from the Indigo definitions
				plugInfo = self.LOCALCACHE["Indigo"]
				rawcommand = rawcommand.replace("indigo_", "")
			else:
				plugInfo = {}
		
		except Exception as e:
			self.logger.error (ext.getException(e))	

		return plugInfo, rawcommand
			
	#
	# Command argument method changed
	#
	def actionsCommandArgsChanged (self, valuesDict, typeId, devId):
		try:
			errorsDict = indigo.Dict()
			
			if "actionsCommandJSONData" not in valuesDict: valuesDict["actionsCommandJSONData"] = json.dumps ({})
			actionArgs = json.loads (valuesDict["actionsCommandJSONData"])
			
			# If they don't want to use args then clear them
			if valuesDict["actionsCommandArgs"] == "-none-":
				valuesDict["actionsCommandJSONData"] = json.dumps ({})
				
			
				
			# Toggle the argument value field on or off
			plugInfo, rawcommand = self.getPlugInfoForForm (valuesDict)
				
			for cmd, action in plugInfo["xml"]["actions"].iteritems():
				if cmd == rawcommand:
					if len(action["ConfigUI"]["Fields"]) > 0:
						for field in action["ConfigUI"]["Fields"]:
							if field["id"] == valuesDict["actionsCommandArgs"]:
								if field["type"] == "integer" or field["type"] == "delay" or field["type"] == "textfield": 
									valuesDict["actionsCommandArgsValueType"] = "text"
								
								elif field["type"] == "list": 
									valuesDict["actionsCommandArgsValueType"] = "menu"
								
								else:
									self.logger.warning ("While populating field types, Actions encountered a type of {} that could not be resolved".format(field["type"]))
									valuesDict["actionsCommandArgsValueType"] = "none"
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return (valuesDict, errorsDict)
	
	#
	# Command argument value changed
	#	
	def actionsCommandArgsValueChanged (self, valuesDict, typeId, devId):
		try:
			errorsDict = indigo.Dict()
			
			if "actionsCommandJSONData" not in valuesDict: valuesDict["actionsCommandJSONData"] = json.dumps ({})
			actionArgs = json.loads (valuesDict["actionsCommandJSONData"])
			newActionArgs = {}
			
			# Save and store the update JSON
			if valuesDict["actionsCommandSelect"] != "" and valuesDict["actionsCommandSelect"] != "default" and valuesDict["actionsCommandArgs"] != "" and valuesDict["actionsCommandArgs"] != "default":
				# Simply replace the dict item with the new values
				arg = {}
				arg["forcommand"] = valuesDict["actionsCommandSelect"]
				arg["value"] = ""
				
				if valuesDict["actionsCommandArgsValueType"] == "menu":
					arg["value"] = valuesDict["actionsCommandArgsValueList"]
					
				elif valuesDict["actionsCommandArgsValueType"] == "list":
					arg["value"] = valuesDict["actionsCommandArgsValueList"]
				
				elif valuesDict["actionsCommandArgsValueType"] == "check":
					arg["value"] = valuesDict["actionsCommandArgsValueCheckbox"]
				
				else:
					arg["value"] = valuesDict["actionsCommandArgsValueText"]
				
				actionArgs[valuesDict["actionsCommandArgs"]] = arg
				
				# A quick sanity check, recompile args into a new dict so we aren't carrying over another commands arguments
				for argname, arg in actionArgs.iteritems():
					if arg["forcommand"] == valuesDict["actionsCommandSelect"]: newActionArgs[argname] = arg
				
				valuesDict["actionsCommandJSONData"] = json.dumps (newActionArgs)
				
				indigo.server.log(unicode(valuesDict["actionsCommandJSONData"]))
				indigo.server.log(unicode(newActionArgs))
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return (valuesDict, errorsDict)
			
	#
	# Default processor called from Plug when formFieldChanged gets called, which is only when the initial command is selected
	#
	def setUIDefaults (self, valuesDict, errorsDict):
		try:
			# Just in case we didn't populate
			if len(self.LOCALCACHE) == 0:
				for k, v in self.factory.plugdetails.pluginCache.iteritems():
					self.LOCALCACHE[k] = v
			
			# First do a sanity check to make sure all of our fields exist
			missingFields = []
			for f in self.FIELDLIST:
				if f not in valuesDict: missingFields.append(f)
				
			missingAttribs = []
			for a in self.ATTRIBUTELIST:
				if a not in dir(self.factory.plugin): missingAttribs.append(a)
				
			if len(missingFields) > 0:
				errorsDict["showAlertText"] = "Implementation of actions is incomplete, the following fields are missing from the form: " + unicode(missingFields)
				return (valuesDict, errorsDict)
				
			if len(missingAttribs) > 0:
				errorsDict["showAlertText"] = "Implementation of actions is incomplete, the following functions are missing from the plugin: " + unicode(missingAttribs)
				return (valuesDict, errorsDict)	
				
			# Toggle the argument value field on or off
			plugInfo, rawcommand = self.getPlugInfoForForm (valuesDict)
				
			for cmd, action in plugInfo["xml"]["actions"].iteritems():
				if cmd == rawcommand:
					if len(action["ConfigUI"]["Fields"]) > 0:
						valuesDict["actionsArgsEnable"] = True # Toggle on args
					else:
						valuesDict["actionsArgsEnable"] = False # Toggle off args	
			
			return (valuesDict, errorsDict)
				
			# If the currently selected argument is not in the list of arguments then select none
			if len(newActionArgs) == 0 or valuesDict["actionsCommandArgs"] == "default" or valuesDict["actionsCommandArgs"] == "": valuesDict["actionsCommandArgs"] = "-none-"	
			
			# Toggle value field visibility depending on the argument chosen
			#dev = indigo.devices[int(valuesDict[args["srcfield"]])]
			rawcommand = valuesDict["actionsCommandSelect"]
			
			if rawcommand[0:7] == "indigo_":
				# Get command arguments from the Indigo definitions
				plugInfo = self.factory.plugdetails.pluginCache["Indigo"]
				rawcommand = rawcommand.replace("indigo_", "")
				
			else:
				plugInfo = {}
				
			for cmd, action in plugInfo["xml"]["actions"].iteritems():
				if cmd == rawcommand:
					if len(action["ConfigUI"]["Fields"]) > 0:
						valuesDict["actionsArgsEnable"] = True # Toggle on args
						
						for field in action["ConfigUI"]["Fields"]:
							if field["id"] == valuesDict["actionsCommandArgs"]:
								if field["type"] == "integer" or field["type"] == "delay" or field["type"] == "textfield": 
									valuesDict["actionsCommandArgsValueType"] = "text"
								
								elif field["type"] == "list": 
									valuesDict["actionsCommandArgsValueType"] = "menu"
								
								else:
									self.logger.warning ("While populating field types, Actions encountered a type of {} that could not be resolved".format(field["type"]))
									valuesDict["actionsCommandArgsValueType"] = "none"
									
					else:
						valuesDict["actionsArgsEnable"] = False # Toggle off args
							
			
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return (valuesDict, errorsDict)
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		