# eps.actionsv2 - Manage and execute actions (rewritten from original actions.py)
#
# Copyright (c) 2018 ColoradoFourWheeler / EPS
#

# This library varies greatly from the original actions library.  This is built to be much more static, so the field names on the form must match what this
# library is referencing since there will no longer be multiple form areas for actions, this library is meant to have a single area for the action and then
# adding that action then updates a JSON list, thus allowing for unlimited device/action group/variable actions to be added.  To reference the core field requirements
# check out the Home Patrol plugin for which this was initially developed

import indigo
import logging
import json

import ext
import dtutil

class actions:		
	#########################################################################################
	# GENERAL LIBRARY ACTIONS
	#########################################################################################
		
	#
	# Initialize the  class
	#
	def __init__(self, factory):
		self.logger = logging.getLogger ("Plugin.actions")
		self.factory = factory
		self.maxFields = 10 # Max number of fields to populate for ConfigUI actions

	#########################################################################################
	# ACTION RUN PROCESSING
	#########################################################################################
	
	#
	# Compile action options and run them
	#
	def runAction (self, obj, key, method = None):
		try:
			# See if we are allowing multiple objects, if not default to device
			objType = "device"
			propsDict = obj.pluginProps
			
			self.logger.threaddebug ("Running action type '{0}' for a '{1}' condition".format(objType, method))
			
			# If our properties exist then extract them
			if "actionItemLibData" in propsDict:
				actionDetails = json.loads(propsDict["actionItemLibData"])
				
				for actionDetail in actionDetails:
					if actionDetail["key"] == key:
						break
				
				if int(actionDetail["actionDevice"]) not in indigo.devices:
					self.logger.error ("Asked to run an action for device id {0} but that device no longer exists in Indigo, please change the device configuration to point elsewhere.".format(actionDetail["actionDevice"]))
					return False
				
				dev = indigo.devices[int(actionDetail["actionDevice"])]
				actions = self.factory.plugcache.getActions (dev)	
				
				args = {}
				actionItem = None
				rawAction = ""
				
				fieldIdx = 1
				for id, action in actions.iteritems():
					if id == actionDetail["deviceFunction"]:
						actionItem = action
						rawAction = id
						
						if "ConfigUI" in action:
							if "Fields" in action["ConfigUI"]:
								for field in action["ConfigUI"]["Fields"]:
									args[field["id"]] = self._getGroupFieldValue (actionDetail, field["ValueType"], field["Default"], fieldIdx)
									fieldIdx = fieldIdx + 1			
				
				self.logger.threaddebug ("Arguments: " + unicode(args))
				return self._executeAction (dev, rawAction, actionItem, args)
				
				
			else:
				self.logger.error ("Trying to run an action but the device doesn't have the required 'actionItemLibData' in order to run".format(obj.name))	
				return False
			
			return False
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return False
			
		return True
		
	#
	# Get the group field value for a given group ID
	#
	def _getGroupFieldValue (self, propsDict, type, default, index):
		ret = ""
		
		try:
			if ext.valueValid (propsDict, "optionGroup" + str(index), True):
				# In case the plugin is hiding a valid field, unhide it here
				propsDict["optionGroup" + str(index)] = self.toggleGroupVisibility (propsDict["optionGroup" + str(index)], True)
				
				if propsDict["optionGroup" + str(index)] == "textfield":
					ret = propsDict["strValue" + str(index)]
					
				elif propsDict["optionGroup" + str(index)] == "menu":
					ret = propsDict["menuValue" + str(index)]
					
				elif propsDict["optionGroup" + str(index)] == "list":
					ret = propsDict["listValue" + str(index)]
					
				elif propsDict["optionGroup" + str(index)] == "checkbox":
					ret = propsDict["checkValue" + str(index)]
					
				if ret is None or ret == "" and default is not None: ret = default
				
				if ret != "":
					if type == "integer": 
						ret = int(ret)
						
					elif type == "delay":
						# Convert HH:MM:SS to seconds
						timeStr = ret.split(":")
						ret = 0
						
						if len(timeStr) == 3:
							ret = ret + (int(timeStr[0]) * 1440)
							ret = ret + (int(timeStr[1]) * 60)
							ret = ret + int(timeStr[2])
							
					elif type == "list":
						# Converts a string or comma delimited string to a list
						data = ret.split(",")
						ret = []
						
						for d in data:
							ret.append(d.strip())
					
					elif type == "indigo_enum":
						# The value is the enum to lookup
						ret = ret.replace("indigo.", "")
						data = ret.split(".")

						ret = getattr (indigo, data[0])
						ret = getattr (ret, data[1])
					
					else:
						# It's a string
						ret = ret
					
					
				
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return ret	
		
	#########################################################################################
	# EXECUTE ACTION
	#########################################################################################	
	
	#
	# Execute an action
	#
	def _executeAction (self, obj, rawAction, action, args):	
		try:
			self.logger.info ("Executing Indigo action {0}".format(action["Name"]))
			
			#indigo.server.log(unicode(action))
			#indigo.server.log(rawAction)
			#indigo.server.log(unicode(args))
			
			# Check if we have some simple conversions to do before passing it on to Indigo or plugins
			if rawAction == "indigo_setBinaryOutput" or rawAction == "indigo_setBinaryOutput_2":
				args["index"] = args["index"] - 1 # Users will use 1 based but Indigo requires 0 based
				args["value"] = False # We have to put up the value here
				if rawAction == "indigo_setBinaryOutput": args["value"] = True
				rawAction = "indigo_setBinaryOutput"
				
			##########################################################################################	
				
			# Check if we have a known custom command
			if rawAction == "indigo_match":
				# Custom dimmer command to match brightness
				self.logger.threaddebug ("Executing custom command {0} using arguments {1}".format(rawAction, unicode(args)))
				
				for devId in args["devices"]:
					indigo.dimmer.setBrightness (int(devId), value=obj.states["brightnessLevel"], delay=args["delay"])
					
			elif rawAction == "indigo_sendEmailTo":		
				self.logger.threaddebug ("Executing custom command {0} using arguments {1}".format(rawAction, unicode(args)))	
				indigo.server.sendEmailTo(args["to"], subject=args["subject"], body=args["body"])
					
			elif rawAction == "indigo_removeDelayedAll":		
				self.logger.threaddebug ("Executing custom command {0} using arguments {1}".format(rawAction, unicode(args)))	
				indigo.server.removeAllDelayedActions()
					
			elif rawAction == "indigo_removeDelayedDevice":
				self.logger.threaddebug ("Executing custom command {0} using arguments {1}".format(rawAction, unicode(args)))
				indigo.device.removeDelayedActions(args["device"])
				
			elif rawAction == "indigo_removeDelayedTrigger":
				self.logger.threaddebug ("Executing custom command {0} using arguments {1}".format(rawAction, unicode(args)))
				indigo.trigger.removeDelayedActions(args["trigger"])
				
			elif rawAction == "indigo_removeDelayedSchedule":
				self.logger.threaddebug ("Executing custom command {0} using arguments {1}".format(rawAction, unicode(args)))		
				indigo.schedule.removeDelayedActions(args["schedule"])
					
			elif rawAction == "indigo_enableDevice":
				self.logger.threaddebug ("Executing custom command {0} using arguments {1}".format(rawAction, unicode(args)))
				indigo.device.enable(args["device"], value=True)
				
			elif rawAction == "indigo_enableTrigger":
				self.logger.threaddebug ("Executing custom command {0} using arguments {1}".format(rawAction, unicode(args)))
				indigo.trigger.enable(args["trigger"], value=True, duration=args["duration"], delay=args["delay"])
				
			elif rawAction == "indigo_enableSchedule":
				self.logger.threaddebug ("Executing custom command {0} using arguments {1}".format(rawAction, unicode(args)))		
				indigo.schedule.enable(args["schedule"], value=True, duration=args["duration"], delay=args["delay"])
					
			elif rawAction == "indigo_disableDevice":
				self.logger.threaddebug ("Executing custom command {0} using arguments {1}".format(rawAction, unicode(args)))
				indigo.device.enable(args["device"], value=False)
								
			elif rawAction == "indigo_disableTrigger":
				self.logger.threaddebug ("Executing custom command {0} using arguments {1}".format(rawAction, unicode(args)))
				indigo.trigger.enable(args["trigger"], value=False, duration=args["duration"], delay=args["delay"])
				
			elif rawAction == "indigo_disableSchedule":
				self.logger.threaddebug ("Executing custom command {0} using arguments {1}".format(rawAction, unicode(args)))
				indigo.schedule.enable(args["schedule"], value=False, duration=args["duration"], delay=args["delay"])
					
			elif rawAction == "indigo_setBinaryOutput_3":
				# Turn off all binary outputs
				self.logger.threaddebug ("Executing custom command {0} using arguments {1}".format(rawAction, unicode(args)))
				dev = indigo.devices[obj.id]
				
				for i in range (0, dev.binaryInputCount):
					indigo.iodevice.setBinaryOutput(dev.id, index=i, value=False)
					
			elif rawAction == "indigo_insertTimeStamp":
				# Insert pre-formatted timestamp into variable
				self.logger.threaddebug ("Executing custom command {0} using arguments {1}".format(rawAction, unicode(args)))
				indigo.variable.updateValue(obj.id, value=indigo.server.getTime().strftime("%Y-%m-%d %H:%M:%S"))
				
			elif rawAction == "indigo_insertTimeStamp_2":
				# Insert custom formatted timestamp into variable
				self.logger.threaddebug ("Executing custom command {0} using arguments {1}".format(rawAction, unicode(args)))
				indigo.variable.updateValue(obj.id, value=indigo.server.getTime().strftime(args["format"]))
				
			elif rawAction == "indigo_setVarToVar":
				# Insert custom formatted timestamp into variable
				self.logger.threaddebug ("Executing custom command {0} using arguments {1}".format(rawAction, unicode(args)))
				var = indigo.variables[obj.id]
				copyVar = indigo.variables[args["variable"]]
				
				indigo.variable.updateValue(obj.id, value=copyVar.value)
				
			elif rawAction == "indigo_setVarToVar":
				# Insert custom formatted timestamp into variable
				self.logger.threaddebug ("Executing custom command {0} using arguments {1}".format(rawAction, unicode(args)))
				var = indigo.variables[obj.id]
				copyVar = indigo.variables[args["variable"]]
				
				indigo.variable.updateValue(obj.id, value=copyVar.value)
				
			elif rawAction == "indigo_toggle_3":
				# Toggle between various true/false values in variable
				self.logger.threaddebug ("Executing custom command {0} using arguments {1}".format(rawAction, unicode(args)))
				
				var = indigo.variables[obj.id]
				oldVal = var.value
				newVal = "true"
				
				if args["value"] == "truefalse":
					if oldVal.lower() == "true":
						newVal = "false"
					else:
						newVal = "true"
						
				elif args["value"] == "onoff":
					if oldVal.lower() == "on":
						newVal = "off"
					else:
						newVal = "on"
						
				elif args["value"] == "yesno":
					if oldVal.lower() == "yes":
						newVal = "no"
					else:
						newVal = "yes"
						
				elif args["value"] == "enabledisable":
					if oldVal.lower() == "enable":
						newVal = "disable"
					else:
						newVal = "enable"
						
				elif args["value"] == "openclose":
					if oldVal.lower() == "open":
						newVal = "close"
					else:
						newVal = "open"
						
				elif args["value"] == "unlocklock":
					if oldVal.lower() == "unlock":
						newVal = "lock"
					else:
						newVal = "unlock"
						
				indigo.variable.updateValue(obj.id, value=newVal)
				
			elif rawAction[0:7] == "indigo_":
				# An indigo action
				rawAction = rawAction.replace("indigo_", "")
				
				topFunc = None
				if type(obj) is indigo.RelayDevice: topFunc = indigo.relay
				if type(obj) is indigo.DimmerDevice: topFunc = indigo.dimmer
				if type(obj) is indigo.indigo.MultiIODevice: topFunc = indigo.iodevice
				if type(obj) is indigo.SensorDevice: topFunc = indigo.sensor
				if type(obj) is indigo.SpeedControlDevice: topFunc = indigo.speedcontrol
				if type(obj) is indigo.SprinklerDevice: topFunc = indigo.sprinkler
				if type(obj) is indigo.ThermostatDevice: topFunc = indigo.thermostat
				
				if type(obj) is indigo.Variable: topFunc = indigo.variable
				
				func = getattr (topFunc, rawAction)
				
				self.logger.threaddebug ("Sending command to {0} using arguments {1}".format(unicode(func), unicode(args)))
				
				if len(args) > 0:
					func(obj.id, **args)
				else:
					func(obj.id)
					
			else:
				# A plugin action
				rawAction = rawAction.replace("plugin_", "")
				
				plugin = indigo.server.getPlugin (obj.pluginId)
				if plugin.isEnabled() == False:
					self.logger.error ("Unabled to run '{0}' on plugin '{1}' because the plugin is disabled".format(action["Name"], plugin.pluginDisplayName))
					return False
					
				self.logger.threaddebug ("Running action '{0}' for '{1}' using arguments {2}".format(rawAction, plugin.pluginDisplayName, unicode(args)))
				self.logger.info ("Running '{0}' action '{1}'".format(plugin.pluginDisplayName, action["Name"]))
			
				
				ret = None
				
				#indigo.server.log(rawAction)
				#indigo.server.log(unicode(args))
				
				try:
					ret = plugin.executeAction (rawAction, deviceId=obj.id, props=args)	
					
				except Exception as e:
					self.logger.error (ext.getException(e))	
					self.factory.plug.actionGotException (action, obj.id, args, e, plugin.pluginDisplayName)
					
				if ret is not None and ret != "":
					self.factory.plug.actionReturnedValue (action, obj.id, args, ret)
			
			return True
						
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return False	
			
	#########################################################################################
	# DIRECT-FROM-UI CALLS
	#########################################################################################
	
	#
	# Utility to toggle the visibility of a field so that the field is still considered active, just not displayed
	#
	def toggleGroupVisibility (self, fieldValue, unhide = False):
		try:
			if fieldValue == "hidden": return "hidden"
			
			if unhide == False:
				# In case we get the already hidden value
				if fieldValue == "invtxt": return fieldValue
				if fieldValue == "invmnu": return fieldValue
				if fieldValue == "invlst": return fieldValue
				if fieldValue == "invchk": return fieldValue
				
				# Return hidden value
				if fieldValue == "textfield": return "invtxt"
				if fieldValue == "menu": return "invmnu"
				if fieldValue == "list": return "invlst"
				if fieldValue == "checkbox": return "invchk"
				
			else:
				# In case we get the already unhidden value
				# In case we get the already hidden value
				if fieldValue == "textfield": return fieldValue
				if fieldValue == "menu": return fieldValue
				if fieldValue == "list": return fieldValue
				if fieldValue == "checkbox": return fieldValue
				
				# Return unhidden value
				if fieldValue == "invtxt": return "textfield"
				if fieldValue == "invmnu": return "menu"
				if fieldValue == "invlst": return "list"
				if fieldValue == "invchk": return "checkbox"
				
			# If we got here then there is an unknown option
			self.logger.warn ("Unable to change a group UI value {0}, this is could be critical depending on the plugin".format(fieldValue))
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
	
	#
	# Called from the plugin, this will load field values from an already decoded JSON dict - this is not loaded from plug.py because the UI list is different for each plugin so there's no way to determine what list to look for to know which entry they are decoding
	#
	def duplicateActionItem (self, valuesDict, actionItemKey):
		try:
			actionList = valuesDict["actionItemLibData"]
			actionItems = json.loads(actionList)
			
			for actionItem in actionItems:
				if actionItem["key"] == actionItemKey:
					break
			
			newActionItem = dict(actionItem)	
			d = indigo.server.getTime()	
			newActionItem["key"] = self.factory.ui.createHashKey (valuesDict["actionDevice"] + valuesDict["actionActionGroup"] + d.strftime("%Y-%m-%d %H:%M:%S %f"))
			valuesDict["actionItemLibKey"] = newActionItem["key"] # So the UI form knows what the new key is
			actionItems.append(newActionItem)
			
			jdata = json.dumps(actionItems)
			valuesDict["actionItemLibData"] = jdata
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return valuesDict
		
	#
	# Called from the plugin, this will delete field values from an already decoded JSON dict - this is not loaded from plug.py because the UI list is different for each plugin so there's no way to determine what list to look for to know which entry they are decoding
	#
	def deleteActionItem (self, valuesDict, actionItemKey):
		try:
			actionList = valuesDict["actionItemLibData"]
			actionItems = json.loads(actionList)
			newActionItems = []
			
			for actionItem in actionItems:
				if actionItem["key"] != actionItemKey:
					newActionItems.append (actionItem)
			
			jdata = json.dumps(newActionItems)
			valuesDict["actionItemLibData"] = jdata
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return valuesDict

	#
	# Called from the plugin, this will load field values from an already decoded JSON dict - this is not loaded from plug.py because the UI list is different for each plugin so there's no way to determine what list to look for to know which entry they are decoding
	#
	def loadFieldValuesFromDict (self, valuesDict, actionItem):
		try:
			valuesDict["actionType"] = actionItem["actionType"]
			valuesDict["actionDevice"] = actionItem["actionDevice"]
			valuesDict["actionActionGroup"] = actionItem["actionActionGroup"]
			
			valuesDict["showFunctions"] = actionItem["showFunctions"]
			valuesDict["deviceFunction"] = actionItem["deviceFunction"]
			
			for i in range (1, 10):
				if "optionGroup" + str(i) in valuesDict:
					valuesDict["optionGroup" + str(i)] = actionItem["optionGroup" + str(i)]
					valuesDict["optionLabel" + str(i)] = actionItem["optionLabel" + str(i)]
					valuesDict["optionId" + str(i)] = actionItem["optionId" + str(i)]
					valuesDict["checkValue" + str(i)] = actionItem["checkValue" + str(i)]
					valuesDict["strValue" + str(i)] = actionItem["strValue" + str(i)]
					valuesDict["menuValue" + str(i)] = actionItem["menuValue" + str(i)]
					
					#if len(valuesDict["listValue" + str(i)]) > 0:
					#	actionData["listValue" + str(i)] = ""
					#	for lvItem in valuesDict["listValue" + str(i)]:
					#		actionData["listValue" + str(i)] += lvItem + "||"
					#else:
					#	actionData["listValue" + str(i)] = ""
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return valuesDict

	#########################################################################################
	# DIRECT-FROM-ENGINE ONLY CALLS
	#########################################################################################
	
	#
	# Called only locally from actionAddToListButton, actionUpdateListButton and actionDeleteListButton
	#
	def _populateActionItemDict (self, valuesDict, actionData):
		try:
			actionData["objectName"] = "" # Until we figure it out below, this is THE name of this item depending on the object type selected so other routines can utilize it without calculation
			if "key" not in actionData: 
				d = indigo.server.getTime()
				actionData["key"] = self.factory.ui.createHashKey (valuesDict["actionDevice"] + valuesDict["actionActionGroup"] + d.strftime("%Y-%m-%d %H:%M:%S %f"))
				
			actionData["actionType"] = valuesDict["actionType"]
			actionData["actionDevice"] = valuesDict["actionDevice"]
			actionData["actionActionGroup"] = valuesDict["actionActionGroup"]
			
			if valuesDict["actionDevice"] != "":
				actionData["actionDeviceName"] = indigo.devices[int(valuesDict["actionDevice"])].name
				actionData["objectName"] = actionData["actionDeviceName"]
			else:
				actionData["actionDeviceName"] = ""
				
			if valuesDict["actionActionGroup"] != "":
				actionData["actionActionGroupName"] = indigo.actionGroups[int(valuesDict["actionActionGroup"])].name
				actionData["objectName"] = actionData["actionActionGroupName"]
			else:
				actionData["actionActionGroupName"] = ""
					
			
			actionData["showFunctions"] = valuesDict["showFunctions"]
			actionData["deviceFunction"] = valuesDict["deviceFunction"]
						
			for i in range (1, 10):
				if "optionGroup" + str(i) in valuesDict:
					actionData["optionGroup" + str(i)] = valuesDict["optionGroup" + str(i)]
					actionData["optionLabel" + str(i)] = valuesDict["optionLabel" + str(i)]
					actionData["optionId" + str(i)] = valuesDict["optionId" + str(i)]
					actionData["checkValue" + str(i)] = valuesDict["checkValue" + str(i)]
					actionData["strValue" + str(i)] = valuesDict["strValue" + str(i)]
					actionData["menuValue" + str(i)] = valuesDict["menuValue" + str(i)]
					
					if len(valuesDict["listValue" + str(i)]) > 0:
						actionData["listValue" + str(i)] = ""
						for lvItem in valuesDict["listValue" + str(i)]:
							actionData["listValue" + str(i)] += lvItem + "||"
					else:
						actionData["listValue" + str(i)] = ""
						
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return actionData

	#
	# Called from the plug.py this is what forms will use to update the form data in a JSON encoded field in valuesDict
	#
	def actionUpdateListButton (self, valuesDict, typeId, devId):
		try:	
			# We don't need to error check since it couldn't have been added unless it went through the checks built into actionAddToListButton
			if valuesDict["actionItemLibKey"] == "":
				errorsDict = indigo.Dict()
				errorsDict["actionDevice"] = "Edit error"
				errorsDict["showAlertText"] = "Update list function requires the item library key to be populated.  Only the developer can fix this issue, please submit screenshot of this form to the Indigo forum."
				return valuesDict, errorsDict
			
			if 'actionItemLibData' not in valuesDict:
				valuesDict['actionItemLibData'] = json.dumps([])  # Empty list in JSON container	
			
			actionList = valuesDict["actionItemLibData"]
			actionItems = json.loads(actionList)
			
			for actionItem in actionItems:
				if actionItem["key"] == valuesDict["actionItemLibKey"]:
					newActionItem = self._populateActionItemDict (valuesDict, actionItem)
					
					newActionItems = []
					
					for actionItemEx in actionItems:
						if actionItemEx["key"] != valuesDict["actionItemLibKey"]:
							newActionItems.append(actionItemEx)
						else:
							newActionItems.append(newActionItem)
			
					jdata = json.dumps(newActionItems)
					valuesDict["actionItemLibData"] = jdata
					
			# Clear all fields and values for the next addition
			valuesDict["actionType"] = "device"
			valuesDict["actionDevice"] = ""
			valuesDict["showFunctions"] = False
			valuesDict["deviceFunction"] = ""
			
			for i in range (1, 10):
				if "optionGroup" + str(i) in valuesDict:
					valuesDict["optionGroup" + str(i)] = self.toggleGroupVisibility(valuesDict["optionGroup" + str(i)])
					valuesDict["optionLabel" + str(i)] = ""
					valuesDict["optionId" + str(i)] = ""
					valuesDict["checkValue" + str(i)] = False
					valuesDict["strValue" + str(i)] = ""
					valuesDict["menuValue" + str(i)] = ""
					valuesDict["listValue" + str(i)] = ""
					
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return valuesDict

	#
	# Called from the plug.py this is what forms will use to add the form data to a JSON encoded field in valuesDict
	#
	def actionAddToListButton (self, valuesDict, typeId, devId):
		try:
			if valuesDict["actionType"] == "device" and valuesDict["actionDevice"] == "":
				errorsDict = indigo.Dict()
				errorsDict["actionDevice"] = "No device selected"
				errorsDict["showAlertText"] = "You must select a device."
				return valuesDict, errorsDict
				
			if valuesDict["actionType"] == "device" and valuesDict["deviceFunction"] == "":
				errorsDict = indigo.Dict()
				errorsDict["deviceFunction"] = "No device action selected"
				errorsDict["showAlertText"] = "You must select a device action to perform."
				return valuesDict, errorsDict
				
			# Special third party validations (we only get here if there is a valid device AND a device function)
			if valuesDict["actionType"] == "device":
				devEx = indigo.devices[int(valuesDict["actionDevice"])]

				if devEx.pluginId == "org.cynic.indigo.securityspy":
					if valuesDict["deviceFunction"] == "plugin_ptzpreset":
						if valuesDict["menuValue1"] == "": # Device
							errorsDict = indigo.Dict()
							errorsDict["menuValue1"] = "No device selected"
							errorsDict["showAlertText"] = "You must select a SecuritySpy device."
							return valuesDict, errorsDict
							
						if valuesDict["menuValue2"] == "": # Preset or Motion
							errorsDict = indigo.Dict()
							errorsDict["menuValue1"] = "No {0} selected".format(optionId2)
							errorsDict["showAlertText"] = "You must select a {0}.".format(optionId2)
							return valuesDict, errorsDict
									
			if 'actionItemLibData' not in valuesDict:
				valuesDict['actionItemLibData'] = json.dumps([])  # Empty list in JSON container	
			
			actionList = valuesDict["actionItemLibData"]
			actionItems = json.loads(actionList)	
			
			actionData = {}	
			valuesDict["actionItemLibKey"] = "" # We are adding a new item so this should never be populated, this is a failsafe to make sure of that	
			actionData = self._populateActionItemDict (valuesDict, actionData)					
					
			actionItems.append (actionData)
			
			jdata = json.dumps(actionItems)
			valuesDict["actionItemLibData"] = jdata
			valuesDict["actionItemLibKey"] = actionData["key"] # Represents the current fields key so any after call can reference us in the list
			
			# Clear all fields and values for the next addition
			valuesDict["actionType"] = "device"
			valuesDict["actionDevice"] = ""
			valuesDict["showFunctions"] = False
			valuesDict["deviceFunction"] = ""
			
			for i in range (1, 10):
				if "optionGroup" + str(i) in valuesDict:
					valuesDict["optionGroup" + str(i)] = self.toggleGroupVisibility(valuesDict["optionGroup" + str(i)])
					valuesDict["optionLabel" + str(i)] = ""
					valuesDict["optionId" + str(i)] = ""
					valuesDict["checkValue" + str(i)] = False
					valuesDict["strValue" + str(i)] = ""
					valuesDict["menuValue" + str(i)] = ""
					valuesDict["listValue" + str(i)] = ""
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return valuesDict

	#########################################################################################
	# UI INTERFACE AUTOMATIC ROUTINES
	#########################################################################################
	
	#
	# Based on the values of static form fields, enable or disable other fields depending on field for functions 
	#
	def setUIDefaults (self, propsDict):
		try:
			self.logger.threaddebug ("Actions V2 setUIDefaults executed")
			
			if "useActionExLibrary" not in propsDict:
				self.logger.debug ("Action V2 library setUIDefaults aborted, this device or action does not have the useActionExLibrary field")
				return propsDict
			
			# Our action object type is always determined from a menu called "actionType", even if there is just one action that will be offered to the end user
			# this menu will exist then as a hidden object defaulted to the desired type
			objType = propsDict["actionType"]
			
			# Assume no fields unless we find some
			maxFormFields = 0
			for j in range (1, self.maxFields): 
				if ext.valueValid (propsDict, "optionGroup" + str(j)):
					propsDict["optionGroup" + str(j)] = "hidden" 
					maxFormFields = maxFormFields + 1
					
			propsDict["showFunctions"] = False # Until it's OK to show it
			
			# Device specific fields
			if objType == "device":
				self.logger.threaddebug ("Object is a device")
				
				if ext.valueValid (propsDict, "actionDevice", True):
					# No sense proceeding here unless they selected an action so we know what options to turn on
					if ext.valueValid (propsDict, "deviceFunction", False):
						# We have a valid field, check if it's blank and thus not yet completed
						if propsDict["deviceFunction"] == "": 
							self.logger.threaddebug ("The deviceFunction is present but nothing has been selected for an action yet, exiting routine")
							
							# Make sure the deviceFunction is toggled to visible so the user can make a selection
							propsDict["showFunctions"] = True							
							return propsDict
					
					if ext.valueValid (propsDict, "deviceFunction", True):
						dev = indigo.devices[int(propsDict["actionDevice"])]
						propsDict["showFunctions"] = True # Because it got hidden above and they may need to change the action
						
						# Get the action list from plugcache for this device
						actions = self.factory.plugcache.getActions (dev)
						fieldIdx = 1
						for id, action in actions.iteritems():
							if id == propsDict["deviceFunction"]:
								if "ConfigUI" in action:
									if "Fields" in action["ConfigUI"]:
										# First make sure we have enough fields to support the action
										#if len(action["ConfigUI"]["Fields"]) > maxFormFields: propsDict["showFieldWarning" + method] = True
										
										for field in action["ConfigUI"]["Fields"]:
											propsDict = self._enableFieldToUI (propsDict, dev, action, field, fieldIdx)
											fieldIdx = fieldIdx + 1
											
					else:
						self.logger.threaddebug ("Object is a device and the device is selected but no deviceFunction field exists for us to base fields on")

				else:
					self.logger.threaddebug ("Object is a device but is missing the actionDevice field defining which device we are supposed to be using")
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return propsDict
			
	#
	# Called only from formFieldChanged, this will enable a UI field based on the field data mined from plugCache
	#
	def _enableFieldToUI (self, propsDict, obj, action, field, fieldIdx):
		try:
			#indigo.server.log(unicode(field))
			if ext.valueValid (propsDict, "optionGroup" + str(fieldIdx)):
				# See if this is a self callback, in which case we need to disable the action
				if len(field["List"]) > 0:
					for listItem in field["List"]:
						if listItem["class"] == "self":
							if obj.pluginId != "org.cynic.indigo.securityspy": # Special built-in supported added for these
								msg = "\n" + self.factory.ui.debugHeaderEx ()
								msg += self.factory.ui.debugLine ("Incompatible Device Action")
								msg += self.factory.ui.debugLine (" ")
								msg += self.factory.ui.debugLine ("Plugin Device: " + obj.name)
								msg += self.factory.ui.debugLine ("Action       : " + action["Name"])
								msg += self.factory.ui.debugLine (" ")
								msg += self.factory.ui.debugLine ("This action cannot be called because the plugin that manages it")
								msg += self.factory.ui.debugLine ("requires that one or more of their fields must 'callback' to")
								msg += self.factory.ui.debugLine ("their plugin in order for the action to work properly.")
								msg += self.factory.ui.debugLine (" ")
								msg += self.factory.ui.debugLine ("Please consider asking the developer of the plugin to add support")
								msg += self.factory.ui.debugLine ("for " + self.factory.plugin.pluginDisplayName + " by")
								msg += self.factory.ui.debugLine ("visiting our forum topic regarding developer API's.")

								msg += self.factory.ui.debugHeaderEx ()

								self.logger.warn (msg)
							
								propsDict["showWarning"] = True
							
								#indigo.server.log(unicode(obj))
			
				if field["hidden"]: return propsDict # never show hidden fields
				
				if field["Label"] != "":
					propsDict["optionLabel" + str(fieldIdx)] = field["Label"]
				else:
					propsDict["optionLabel" + str(fieldIdx)] = field["Description"]
			
				propsDict["optionId" + str(fieldIdx)] = field["id"]
				propsDict["optionGroup" + str(fieldIdx)] = field["type"]
							
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return propsDict
		
	#
	# Called from UI if the custom list type is "actionoptionlist"
	#
	def getActionOptionUIList (self, args, valuesDict):
		ret = [("default", "No data")]
		
		try:
			retList = []
			
			if ext.valueValid (args, "group", True) and ext.valueValid (args, "method", True): 
				group = args["group"]
				method = args["method"]
				
				objType = "device"
				#if ext.valueValid (valuesDict, self.FIELDPREFIX + method, True):
				#	if valuesDict[self.FIELDPREFIX + method] == "variable": objType = "variable"
				#	if valuesDict[self.FIELDPREFIX + method] == "server": objType = "server"
				
				# In order to populate we have to have a device and an action
				if ext.valueValid (valuesDict, "actionDevice", True) or objType == "server":
					if objType == "device": 
						if int(valuesDict["actionDevice"]) not in indigo.devices:
							self.logger.error ("Asked to get UI options on device id {0} but that device no longer exists in Indigo, please change the device configuration to point elsewhere.".format(valuesDict["actionDevice"]))
							return ret
						else:
							obj = indigo.devices[int(valuesDict["actionDevice"])]
						
					if objType == "variable": obj = indigo.variables[int(valuesDict["actionVariable"])]
					if objType == "server": obj = "server"

					listData = self._getActionOptionUIList (obj, objType, valuesDict, method, group)
					
					listIdx = 1
					for listItem in listData:
						# THE FOLLOWING WAS FIXED IN 2.4.0 AND IS LEFT HERE TO REFERENCE IF THERE ARE ISSUES IN THE CURRENTLY CIRCULATED VERSION OF THE LIBRARY
						# Only return the list for this group
						#if listIdx != int(group):
						#	listIdx = listIdx + 1
						#	#indigo.server.log("BREAK!")
						#	continue
					
						if len(listItem["Options"]) > 0:
							for opt in listItem["Options"]:
								if opt["value"] == "-line-":
									option = ("-line-", self.factory.ui.getSeparator())						
								else:
									option = (opt["value"], opt["Label"])
	
								retList.append (option)
								
						elif listItem["class"] == "indigo.dimmer":
							for d in indigo.devices.iter("indigo.dimmer"):
								option = (d.id, d.name)
								retList.append (option)
								
						elif listItem["class"] == "indigo.triggers":
							for d in indigo.triggers:
								option = (d.id, d.name)
								retList.append (option)
								
						elif listItem["class"] == "indigo.schedules":
							for d in indigo.schedules:
								option = (d.id, d.name)
								retList.append (option)
								
						elif listItem["class"] == "indigo.devices":
							for d in indigo.devices:
								option = (d.id, d.name)
								retList.append (option)
								
						elif listItem["class"] == "indigo.variables":
							for d in indigo.variables:
								option = (d.id, d.name)
								retList.append (option)
								
						elif listItem["class"] == "custom.zonenames":
							for i in range (0, 8):
								if obj.zoneEnableList[i]:
									option = (str(i + 1), dev.zoneNames[i])
									retList.append (option)
													
						listIdx = listIdx + 1
						
					
				
				if len(retList) > 0: return retList
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return ret
		
		return ret
		
	#
	# Get list data from plugcache (called from getActionOptionUIList)
	#
	def _getActionOptionUIList (self, obj, objType, valuesDict, method, group):
		try:
			# See if we have an exception for this field before we query the plug cache
			ret = self._getActionOptionUIList_Exceptions (obj, objType, valuesDict, method, group)
			if len(ret) > 0: return ret
		
			actions = self.factory.plugcache.getActions (obj)
			
			for id, action in actions.iteritems():
				#indigo.server.log(unicode(action))
				if id == valuesDict[objType + "Function"]:
					if "ConfigUI" in action:
						if "Fields" in action["ConfigUI"]:
							for field in action["ConfigUI"]["Fields"]:
								if field["id"] == valuesDict["optionId" + group]:
									return field["List"]
											
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return []	
		
	#
	# Specially created lists for plugins where we proactively created lists for their "self" list items
	#
	def _getActionOptionUIList_Exceptions (self, obj, objType, valuesDict, method, group):
		list = []
		item = indigo.Dict()
		Options = []
		
		
		try:
			# SecuritySpy PTZFilter List Return Class
			if obj.pluginId == "org.cynic.indigo.securityspy":
				if valuesDict[objType + "Function"] == "plugin_ptzpreset" or valuesDict[objType + "Function"] == "plugin_ptzmotion": # Remember that all plugins have the plugin_ prefix before action names!
					if valuesDict["optionId" + group] == "device":
						for dev in indigo.devices.iter("org.cynic.indigo.securityspy.camera"):
							if dev.id == int(valuesDict["actionDevice"]): # We already know what device we want to run the action on, this is just to make sure the field doesn't get some OTHER device instead
								thisitem = indigo.Dict()
								thisitem["Label"] = dev.name
								thisitem["value"] = str(dev.id)
								Options.append (thisitem)
							
			if len(Options) > 0:
				item["Options"]=Options
				list.append(item)
				return list
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return []
		
	#########################################################################################
	# BELOW THIS SECTION ARE ALL ORIGINAL METHOD RENAMED TO _ORIG FOR CLARITY
	#########################################################################################

	#
	# Compile action options and run them
	#
	def runAction_ORIG (self, propsDict, method = None):
		try:
			if method is None: method = self.FORMTERMS[0]
			
			# Check that we have either a strValuePassOn or strValueFailOn, if we don't then this is either
			# not an action or it's a pseudo action device that the plugin is handling one-off
			if ext.valueValid (propsDict, self.VALIDATION) == False:
				self.logger.threaddebug ("The current device is not an action device with {0}, not running action".format(self.VALIDATION))
				return False
				
			# See if we are allowing multiple objects, if not default to device
			objType = "device"
		
			# If we are allowing multiple objects make sure our selection is valid
			if ext.valueValid (propsDict, self.FIELDPREFIX + method):
				if ext.valueValid (propsDict, self.FIELDPREFIX + method, True):
					objType = propsDict[self.FIELDPREFIX + method]
				
				else:
					# It's blank or a line or something, just skip
					self.logger.warn ("No method was selected for an action, it cannot be run")
					return False
					
			self.logger.threaddebug ("Running action type '{0}' for a '{1}' condition".format(objType, method))
			
			if objType == "action":
				if ext.valueValid (propsDict, "action" + method, True):
					indigo.actionGroup.execute(int(propsDict["action" + method]))
			
			if objType == "device":
				if ext.valueValid (propsDict, self.DEV + method, True):
					# No sense proceeding here unless they selected an action so we know what options to turn on
					if ext.valueValid (propsDict, self.DEV_ACTION + method, True):		
						dev = indigo.devices[int(propsDict[self.DEV + method])]
						
						# Get the action list from plugcache for this device
						actions = self.factory.plugcache.getActions (dev)
						
						args = {}
						actionItem = None
						rawAction = ""
						
						fieldIdx = 1
						for id, action in actions.iteritems():
							if id == propsDict[self.DEV_ACTION + method]:
								actionItem = action
								rawAction = id
								
								if "ConfigUI" in action:
									if "Fields" in action["ConfigUI"]:
										for field in action["ConfigUI"]["Fields"]:
											args[field["id"]] = self._getGroupFieldValue (propsDict, method, field["ValueType"], field["Default"], fieldIdx)
											fieldIdx = fieldIdx + 1			
						
						
						return self._executeAction (dev, rawAction, actionItem, args)
						
			if objType == "server":
				# Get the action list from plugcache for this device
				actions = self.factory.plugcache.getActions ("server")
				args = {}
				actionItem = None
				rawAction = ""
				
				fieldIdx = 1
				for id, action in actions.iteritems():
					if id == propsDict["serverAction" + method]:
						actionItem = action
						rawAction = id
						
						if "ConfigUI" in action:
							if "Fields" in action["ConfigUI"]:
								for field in action["ConfigUI"]["Fields"]:
									args[field["id"]] = self._getGroupFieldValue (propsDict, method, field["ValueType"], field["Default"], fieldIdx)
									fieldIdx = fieldIdx + 1		
									
				return self._executeAction (None, rawAction, actionItem, args)	
						
			if objType == "variable":
				if ext.valueValid (propsDict, self.VAR + method, True):
					# No sense proceeding here unless they selected an action so we know what options to turn on
					if ext.valueValid (propsDict, self.VAR_ACTION + method, True):		
						var = indigo.variables[int(propsDict[self.VAR + method])]
						
						# Get the action list from plugcache for this device
						actions = self.factory.plugcache.getActions (var)
						
						args = {}
						actionItem = None
						rawAction = ""
						
						fieldIdx = 1
						for id, action in actions.iteritems():
							if id == propsDict[self.VAR_ACTION + method]:
								actionItem = action
								rawAction = id
								
								if "ConfigUI" in action:
									if "Fields" in action["ConfigUI"]:
										for field in action["ConfigUI"]["Fields"]:
											args[field["id"]] = self._getGroupFieldValue (propsDict, method, field["ValueType"], field["Default"], fieldIdx)
											fieldIdx = fieldIdx + 1			
						
						
						return self._executeAction (var, rawAction, actionItem, args)
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return False
			
		return True
		
	#
	# Execute an action
	#
	def _executeAction_ORIG (self, obj, rawAction, action, args):	
		try:
			self.logger.info ("Executing Indigo action {0}".format(action["Name"]))
			
			#indigo.server.log(unicode(action))
			#indigo.server.log(rawAction)
			#indigo.server.log(unicode(args))
			
			# Check if we have some simple conversions to do before passing it on to Indigo or plugins
			if rawAction == "indigo_setBinaryOutput" or rawAction == "indigo_setBinaryOutput_2":
				args["index"] = args["index"] - 1 # Users will use 1 based but Indigo requires 0 based
				args["value"] = False # We have to put up the value here
				if rawAction == "indigo_setBinaryOutput": args["value"] = True
				rawAction = "indigo_setBinaryOutput"
				
			##########################################################################################	
				
			# Check if we have a known custom command
			if rawAction == "indigo_match":
				# Custom dimmer command to match brightness
				self.logger.threaddebug ("Executing custom command {0} using arguments {1}".format(rawAction, unicode(args)))
				
				for devId in args["devices"]:
					indigo.dimmer.setBrightness (int(devId), value=obj.states["brightnessLevel"], delay=args["delay"])
					
			elif rawAction == "indigo_sendEmailTo":		
				self.logger.threaddebug ("Executing custom command {0} using arguments {1}".format(rawAction, unicode(args)))	
				indigo.server.sendEmailTo(args["to"], subject=args["subject"], body=args["body"])
					
			elif rawAction == "indigo_removeDelayedAll":		
				self.logger.threaddebug ("Executing custom command {0} using arguments {1}".format(rawAction, unicode(args)))	
				indigo.server.removeAllDelayedActions()
					
			elif rawAction == "indigo_removeDelayedDevice":
				self.logger.threaddebug ("Executing custom command {0} using arguments {1}".format(rawAction, unicode(args)))
				indigo.device.removeDelayedActions(args["device"])
				
			elif rawAction == "indigo_removeDelayedTrigger":
				self.logger.threaddebug ("Executing custom command {0} using arguments {1}".format(rawAction, unicode(args)))
				indigo.trigger.removeDelayedActions(args["trigger"])
				
			elif rawAction == "indigo_removeDelayedSchedule":
				self.logger.threaddebug ("Executing custom command {0} using arguments {1}".format(rawAction, unicode(args)))		
				indigo.schedule.removeDelayedActions(args["schedule"])
					
			elif rawAction == "indigo_enableDevice":
				self.logger.threaddebug ("Executing custom command {0} using arguments {1}".format(rawAction, unicode(args)))
				indigo.device.enable(args["device"], value=True)
				
			elif rawAction == "indigo_enableTrigger":
				self.logger.threaddebug ("Executing custom command {0} using arguments {1}".format(rawAction, unicode(args)))
				indigo.trigger.enable(args["trigger"], value=True, duration=args["duration"], delay=args["delay"])
				
			elif rawAction == "indigo_enableSchedule":
				self.logger.threaddebug ("Executing custom command {0} using arguments {1}".format(rawAction, unicode(args)))		
				indigo.schedule.enable(args["schedule"], value=True, duration=args["duration"], delay=args["delay"])
					
			elif rawAction == "indigo_disableDevice":
				self.logger.threaddebug ("Executing custom command {0} using arguments {1}".format(rawAction, unicode(args)))
				indigo.device.enable(args["device"], value=False)
								
			elif rawAction == "indigo_disableTrigger":
				self.logger.threaddebug ("Executing custom command {0} using arguments {1}".format(rawAction, unicode(args)))
				indigo.trigger.enable(args["trigger"], value=False, duration=args["duration"], delay=args["delay"])
				
			elif rawAction == "indigo_disableSchedule":
				self.logger.threaddebug ("Executing custom command {0} using arguments {1}".format(rawAction, unicode(args)))
				indigo.schedule.enable(args["schedule"], value=False, duration=args["duration"], delay=args["delay"])
					
			elif rawAction == "indigo_setBinaryOutput_3":
				# Turn off all binary outputs
				self.logger.threaddebug ("Executing custom command {0} using arguments {1}".format(rawAction, unicode(args)))
				dev = indigo.devices[obj.id]
				
				for i in range (0, dev.binaryInputCount):
					indigo.iodevice.setBinaryOutput(dev.id, index=i, value=False)
					
			elif rawAction == "indigo_insertTimeStamp":
				# Insert pre-formatted timestamp into variable
				self.logger.threaddebug ("Executing custom command {0} using arguments {1}".format(rawAction, unicode(args)))
				indigo.variable.updateValue(obj.id, value=indigo.server.getTime().strftime("%Y-%m-%d %H:%M:%S"))
				
			elif rawAction == "indigo_insertTimeStamp_2":
				# Insert custom formatted timestamp into variable
				self.logger.threaddebug ("Executing custom command {0} using arguments {1}".format(rawAction, unicode(args)))
				indigo.variable.updateValue(obj.id, value=indigo.server.getTime().strftime(args["format"]))
				
			elif rawAction == "indigo_setVarToVar":
				# Insert custom formatted timestamp into variable
				self.logger.threaddebug ("Executing custom command {0} using arguments {1}".format(rawAction, unicode(args)))
				var = indigo.variables[obj.id]
				copyVar = indigo.variables[args["variable"]]
				
				indigo.variable.updateValue(obj.id, value=copyVar.value)
				
			elif rawAction == "indigo_setVarToVar":
				# Insert custom formatted timestamp into variable
				self.logger.threaddebug ("Executing custom command {0} using arguments {1}".format(rawAction, unicode(args)))
				var = indigo.variables[obj.id]
				copyVar = indigo.variables[args["variable"]]
				
				indigo.variable.updateValue(obj.id, value=copyVar.value)
				
			elif rawAction == "indigo_toggle_3":
				# Toggle between various true/false values in variable
				self.logger.threaddebug ("Executing custom command {0} using arguments {1}".format(rawAction, unicode(args)))
				
				var = indigo.variables[obj.id]
				oldVal = var.value
				newVal = "true"
				
				if args["value"] == "truefalse":
					if oldVal.lower() == "true":
						newVal = "false"
					else:
						newVal = "true"
						
				elif args["value"] == "onoff":
					if oldVal.lower() == "on":
						newVal = "off"
					else:
						newVal = "on"
						
				elif args["value"] == "yesno":
					if oldVal.lower() == "yes":
						newVal = "no"
					else:
						newVal = "yes"
						
				elif args["value"] == "enabledisable":
					if oldVal.lower() == "enable":
						newVal = "disable"
					else:
						newVal = "enable"
						
				elif args["value"] == "openclose":
					if oldVal.lower() == "open":
						newVal = "close"
					else:
						newVal = "open"
						
				elif args["value"] == "unlocklock":
					if oldVal.lower() == "unlock":
						newVal = "lock"
					else:
						newVal = "unlock"
						
				indigo.variable.updateValue(obj.id, value=newVal)
				
			elif rawAction[0:7] == "indigo_":
				# An indigo action
				rawAction = rawAction.replace("indigo_", "")
				
				topFunc = None
				if type(obj) is indigo.RelayDevice: topFunc = indigo.relay
				if type(obj) is indigo.DimmerDevice: topFunc = indigo.dimmer
				if type(obj) is indigo.indigo.MultiIODevice: topFunc = indigo.iodevice
				if type(obj) is indigo.SensorDevice: topFunc = indigo.sensor
				if type(obj) is indigo.SpeedControlDevice: topFunc = indigo.speedcontrol
				if type(obj) is indigo.SprinklerDevice: topFunc = indigo.sprinkler
				if type(obj) is indigo.ThermostatDevice: topFunc = indigo.thermostat
				
				if type(obj) is indigo.Variable: topFunc = indigo.variable
				
				func = getattr (topFunc, rawAction)
				
				self.logger.threaddebug ("Sending command to {0} using arguments {1}".format(unicode(func), unicode(args)))
				
				if len(args) > 0:
					func(obj.id, **args)
				else:
					func(obj.id)
					
			else:
				# A plugin action
				rawAction = rawAction.replace("plugin_", "")
				
				plugin = indigo.server.getPlugin (obj.pluginId)
				if plugin.isEnabled() == False:
					self.logger.error ("Unabled to run '{0}' on plugin '{1}' because the plugin is disabled".format(action["Name"], plugin.pluginDisplayName))
					return False
					
				self.logger.threaddebug ("Running action '{0}' for '{1}' using arguments {2}".format(rawAction, plugin.pluginDisplayName, unicode(args)))
				self.logger.info ("Running '{0}' action '{1}'".format(plugin.pluginDisplayName, action["Name"]))
			
				
				ret = None
				
				#indigo.server.log(rawAction)
				#indigo.server.log(unicode(args))
				
				try:
					ret = plugin.executeAction (rawAction, deviceId=obj.id, props=args)	
					
				except Exception as e:
					self.logger.error (ext.getException(e))	
					self.factory.plug.actionGotException (action, obj.id, args, e, plugin.pluginDisplayName)
					
				if ret is not None and ret != "":
					self.factory.plug.actionReturnedValue (action, obj.id, args, ret)
			
			return True
						
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return False
			
		
		
	#
	# Get the group field value for a given group ID
	#
	def _getGroupFieldValue_ORIG (self, propsDict, method, type, default, index):
		ret = ""
		
		try:
			if ext.valueValid (propsDict, self.OPT_GROUP + method + str(index), True):
				# In case the plugin is hiding a valid field, unhide it here
				propsDict[self.OPT_GROUP + method + str(index)] = self.toggleGroupVisibility (propsDict[self.OPT_GROUP + method + str(index)], True)
				
				if propsDict[self.OPT_GROUP + method + str(index)] == "textfield":
					ret = propsDict[self.STR_VAL + method + str(index)]
					
				elif propsDict[self.OPT_GROUP + method + str(index)] == "menu":
					ret = propsDict[self.MENU_VAL + method + str(index)]
					
				elif propsDict[self.OPT_GROUP + method + str(index)] == "list":
					ret = propsDict[self.LIST_VAL + method + str(index)]
					
				elif propsDict[self.OPT_GROUP + method + str(index)] == "checkbox":
					ret = propsDict[self.CHECK_VAL + method + str(index)]
				
				if ret is None or ret == "" and default is not None: ret = default
				
				if ret != "":
					if type == "integer": 
						ret = int(ret)
						
					elif type == "delay":
						# Convert HH:MM:SS to seconds
						timeStr = ret.split(":")
						ret = 0
						
						if len(timeStr) == 3:
							ret = ret + (int(timeStr[0]) * 1440)
							ret = ret + (int(timeStr[1]) * 60)
							ret = ret + int(timeStr[2])
							
					elif type == "list":
						# Converts a string or comma delimited string to a list
						data = ret.split(",")
						ret = []
						
						for d in data:
							ret.append(d.strip())
					
					elif type == "indigo_enum":
						# The value is the enum to lookup
						ret = ret.replace("indigo.", "")
						data = ret.split(".")

						ret = getattr (indigo, data[0])
						ret = getattr (ret, data[1])
					
					else:
						# It's a string
						ret = ret
					
					
				
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return ret
				
	#
	# Execute an action
	#
	def _executeActionEx_ORIG (self, action, args):
		try:
			if action is None: return False
			
			# Break down the ID so we can determine the source
			command = action.id.split(".")
			topFunc = ""
			
			if command[0] == "indigo":
				# Built in action
				if command[1] == "DimmerDevice": topFunc = indigo.dimmer
				if command[1] == "RelayDevice": topFunc = indigo.relay
				if command[1] == "SprinklerDevice": topFunc = indigo.sprinkler
				if command[1] == "SensorDevice": topFunc = indigo.sensor
				if command[1] == "SpeedControlDevice": topFunc = indigo.speedcontrol
				if command[1] == "ThermostatDevice": topFunc = indigo.thermostat
				
				func = getattr (topFunc, command[len(command) - 1])
			
				self.logger.threaddebug ("Sending command to {0} using arguments {1}".format(unicode(func), unicode(args)))
				self.logger.info ("Executing Indigo action {0}".format(action.name))
				
				if len(args) > 0:
					func(*args)
				else:
					func()
				
			else:
				# It's a plugin
				indigo.server.log("PLUGIN")
				pluginId = command[0].replace(":", ".")
				plugin = indigo.server.getPlugin (pluginId)
				if plugin.isEnabled() == False:
					self.logger.error ("Unabled to run '{0}' on plugin '{1}' because the plugin is disabled".format(command[len(command) - 1], plugin.pluginDisplayName))
					return False
					
				#indigo.server.log(unicode(plugin))
				#indigo.server.log(unicode(command))
				#indigo.server.log(unicode(action))
				#indigo.server.log(unicode(args))
				
				self.logger.threaddebug ("Running action '{0}' for '{1}' using arguments {2}".format(command[len(command) - 1], plugin.pluginDisplayName, unicode(args)))
				self.logger.info ("Running '{0}' action '{1}'".format(plugin.pluginDisplayName, action.name))
			
				# The first arg should be the ID, the rest are props, put together the line
				id = args[0]
				props = {}
				
				if len(args) > 1:
					for i in range (1, len(args)):
						props[args[i]] = args[i]
					
				ret = None
				
				try:
					ret = plugin.executeAction (command[len(command) - 1], id, props=props)	
					
				except Exception as e:
					self.logger.error (ext.getException(e))	
					self.factory.plug.actionGotException (action, id, props, e, plugin.pluginDisplayName)
				
				if ret is not None and ret != "":
					self.factory.plug.actionReturnedValue (action, id, props, ret)
			
			
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return False
			
		return True
		
	#
	# Utility to toggle the visibility of a field so that the field is still considered active, just not displayed
	#
	def toggleGroupVisibility_ORIG (self, fieldValue, unhide = False):
		try:
			if fieldValue == "hidden": return "hidden"
			
			if unhide == False:
				# In case we get the already hidden value
				if fieldValue == "invtxt": return fieldValue
				if fieldValue == "invmnu": return fieldValue
				if fieldValue == "invlst": return fieldValue
				if fieldValue == "invchk": return fieldValue
				
				# Return hidden value
				if fieldValue == "textfield": return "invtxt"
				if fieldValue == "menu": return "invmnu"
				if fieldValue == "list": return "invlst"
				if fieldValue == "checkbox": return "invchk"
				
			else:
				# In case we get the already unhidden value
				# In case we get the already hidden value
				if fieldValue == "textfield": return fieldValue
				if fieldValue == "menu": return fieldValue
				if fieldValue == "list": return fieldValue
				if fieldValue == "checkbox": return fieldValue
				
				# Return unhidden value
				if fieldValue == "invtxt": return "textfield"
				if fieldValue == "invmnu": return "menu"
				if fieldValue == "invlst": return "list"
				if fieldValue == "invchk": return "checkbox"
				
			# If we got here then there is an unknown option
			self.logger.warn ("Unable to change a group UI value {0}, this is could be critical depending on the plugin".format(fieldValue))
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
		
	#
	# Set up any UI defaults that we need
	#
	def setUIDefaults_ORIG (self, propsDict, defaultCondition = "disabled", defaultState = "onOffState"):
		try:
			# Check that we have either a strValuePassOn or strValueFailOn, if we don't then this is either
			# not an action or it's a pseudo action device that the plugin is handling one-off
			if ext.valueValid (propsDict, self.VALIDATION) == False:
				self.logger.threaddebug ("The current device is not an action device, not setting defaults")
				return propsDict
				
			for i in range (0, len(self.FORMTERMS)):
				method = self.FORMTERMS[i]
				
				if ext.valueValid (propsDict, self.OPT_LABEL + method + "1") == False: 
					self.logger.threaddebug ("{0} doesn't seem to apply to this device, skipping defaults".format(method))
					continue # may not have pass or may not have fail
				
				# See if we are allowing multiple objects, if not default to device
				objType = "device"
			
				# If we are allowing multiple objects make sure our selection is valid
				if ext.valueValid (propsDict, self.FIELDPREFIX + method):
					if ext.valueValid (propsDict, self.FIELDPREFIX + method, True):
						objType = propsDict[self.FIELDPREFIX + method]
					
					else:
						# It's blank or a line or something, just skip
						continue
						
				# Assume no fields unless we find some
				maxFormFields = 0
				for j in range (1, self.maxFields): 
					if ext.valueValid (propsDict, self.OPT_GROUP + method + str(j)):
						propsDict[self.OPT_GROUP + method + str(j)] = "hidden" 
						maxFormFields = maxFormFields + 1
				
				# Assume this action can be run
				propsDict["showWarning" + method] = False
				propsDict["showFieldWarning" + method] = False
				
				indigo.server.log("1")
				
				if objType == "variable":	
					if ext.valueValid (propsDict, self.VAR + method, True):
						# No sense proceeding here unless they selected an action so we know what options to turn on
						if ext.valueValid (propsDict, self.VAR_ACTION + method, True):	
							var = indigo.variables[int(propsDict[self.VAR + method])]
				
							# Get the action list from plugcache for this device
							actions = self.factory.plugcache.getActions (var)
							fieldIdx = 1
							for id, action in actions.iteritems():
								if id == propsDict[self.VAR_ACTION + method]:
									if "ConfigUI" in action:
										if "Fields" in action["ConfigUI"]:
											# First make sure we have enough fields to support the action
											if len(action["ConfigUI"]["Fields"]) > maxFormFields: propsDict["showFieldWarning" + method] = True
											
											for field in action["ConfigUI"]["Fields"]:
												propsDict = self._addFieldToUI (propsDict, var, action, field, method, fieldIdx)
												fieldIdx = fieldIdx + 1
												
				elif objType == "server":
					actions = self.factory.plugcache.getActions ("server")
					fieldIdx = 1
					for id, action in actions.iteritems():
						if id == propsDict["serverAction" + method]:
							if "ConfigUI" in action:
								if "Fields" in action["ConfigUI"]:
									# First make sure we have enough fields to support the action
									if len(action["ConfigUI"]["Fields"]) > maxFormFields: propsDict["showFieldWarning" + method] = True
								
									for field in action["ConfigUI"]["Fields"]:
										propsDict = self._addFieldToUI (propsDict, None, action, field, method, fieldIdx)
										fieldIdx = fieldIdx + 1
						
				elif objType == "device":
					indigo.server.log("2")
					indigo.server.log(self.DEV + method)
					if ext.valueValid (propsDict, self.DEV + method, True):
						indigo.server.log("3")
						# No sense proceeding here unless they selected an action so we know what options to turn on
						if ext.valueValid (propsDict, self.DEV_ACTION + method, True):								
							dev = indigo.devices[int(propsDict[self.DEV + method])]

							# Get the action list from plugcache for this device
							actions = self.factory.plugcache.getActions (dev)
							fieldIdx = 1
							for id, action in actions.iteritems():
								if id == propsDict[self.DEV_ACTION + method]:
									if "ConfigUI" in action:
										if "Fields" in action["ConfigUI"]:
											# First make sure we have enough fields to support the action
											if len(action["ConfigUI"]["Fields"]) > maxFormFields: propsDict["showFieldWarning" + method] = True
											
											for field in action["ConfigUI"]["Fields"]:
												propsDict = self._addFieldToUI (propsDict, dev, action, field, method, fieldIdx)
												fieldIdx = fieldIdx + 1
												indigo.server.log("4")
									
							# In case our actions caused the developer warning, turn off all field options
							if propsDict["showWarning" + method] or propsDict["showFieldWarning" + method]:
								for j in range (1, self.maxFields): 
									if ext.valueValid (propsDict, self.OPT_GROUP + method + str(j)):
										propsDict[self.OPT_GROUP + method + str(j)] = "hidden" 
										
							# In case we got a developer warning make sure the field warning is off
							if propsDict["showWarning" + method]: propsDict["showFieldWarning" + method] = False
										
							
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
		
		#indigo.server.log(unicode(propsDict))
		return propsDict
		
	#
	# Build dynamic configUI fields
	#
	def _addFieldToUI_ORIG (self, propsDict, obj, action, field, method, fieldIdx):
		try:
			#indigo.server.log(unicode(field))
			if ext.valueValid (propsDict, self.OPT_GROUP + method + str(fieldIdx)):
				# See if this is a self callback, in which case we need to disable the action
				if len(field["List"]) > 0:
					for listItem in field["List"]:
						if listItem["class"] == "self":
							msg = "\n" + self.factory.ui.debugHeaderEx ()
							msg += self.factory.ui.debugLine ("Incompatible Device Action")
							msg += self.factory.ui.debugLine (" ")
							msg += self.factory.ui.debugLine ("Plugin Device: " + obj.name)
							msg += self.factory.ui.debugLine ("Action       : " + action["Name"])
							msg += self.factory.ui.debugLine (" ")
							msg += self.factory.ui.debugLine ("This action cannot be called because the plugin that manages it")
							msg += self.factory.ui.debugLine ("requires that one or more of their fields must 'callback' to")
							msg += self.factory.ui.debugLine ("their plugin in order for the action to work properly.")
							msg += self.factory.ui.debugLine (" ")
							msg += self.factory.ui.debugLine ("Please consider asking the developer of the plugin to add support")
							msg += self.factory.ui.debugLine ("for " + self.factory.plugin.pluginDisplayName + " by")
							msg += self.factory.ui.debugLine ("visiting our forum topic regarding developer API's.")

							msg += self.factory.ui.debugHeaderEx ()

							self.logger.warn (msg)
							
							propsDict["showWarning"] = True
					
			
				if field["hidden"]: return propsDict # never show hidden fields
				
				if field["Label"] != "":
					propsDict[self.OPT_LABEL + method + str(fieldIdx)] = field["Label"]
				else:
					propsDict[self.OPT_LABEL + method + str(fieldIdx)] = field["Description"]
			
				propsDict[self.OPT_GROUP + method + str(fieldIdx)] = field["type"]
							
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return propsDict
	
	#
	# Called from UI if the custom list type is "actionoptionlist"
	#
	def getActionOptionUIList_ORIG (self, args, valuesDict):
		ret = [("default", "No data")]
		
		try:
			retList = []
			
			if ext.valueValid (args, "group", True) and ext.valueValid (args, "method", True): 
				group = args["group"]
				method = args["method"]
				
				objType = "device"
				if ext.valueValid (valuesDict, self.FIELDPREFIX + method, True):
					if valuesDict[self.FIELDPREFIX + method] == "variable": objType = "variable"
					if valuesDict[self.FIELDPREFIX + method] == "server": objType = "server"
				
				# In order to populate we have to have a device and an action
				if ext.valueValid (valuesDict, objType + method, True) or objType == "server":
					if objType == "device": obj = indigo.devices[int(valuesDict[objType + method])]
					if objType == "variable": obj = indigo.variables[int(valuesDict[objType + method])]
					if objType == "server": obj = "server"

					listData = self._getActionOptionUIList (obj, objType, valuesDict, method)
					
					#indigo.server.log(unicode(listData))
					
					listIdx = 1
					for listItem in listData:
						# Only return the list for this group
						if listIdx != int(group):
							listIdx = listIdx + 1
							continue
					
						#indigo.server.log(unicode(listItem))
						#indigo.server.log(unicode(listItem["Options"]))
					
						if len(listItem["Options"]) > 0:
							for opt in listItem["Options"]:
								if opt["value"] == "-line-":
									option = ("-line-", self.factory.ui.getSeparator())						
								else:
									option = (opt["value"], opt["Label"])
	
								retList.append (option)
								
						elif listItem["class"] == "indigo.dimmer":
							for d in indigo.devices.iter("indigo.dimmer"):
								option = (d.id, d.name)
								retList.append (option)
								
						elif listItem["class"] == "indigo.triggers":
							for d in indigo.triggers:
								option = (d.id, d.name)
								retList.append (option)
								
						elif listItem["class"] == "indigo.schedules":
							for d in indigo.schedules:
								option = (d.id, d.name)
								retList.append (option)
								
						elif listItem["class"] == "indigo.devices":
							for d in indigo.devices:
								option = (d.id, d.name)
								retList.append (option)
								
						elif listItem["class"] == "indigo.variables":
							for d in indigo.variables:
								option = (d.id, d.name)
								retList.append (option)
								
						elif listItem["class"] == "custom.zonenames":
							for i in range (0, 8):
								if obj.zoneEnableList[i]:
									option = (str(i + 1), dev.zoneNames[i])
									retList.append (option)
													
						listIdx = listIdx + 1
						
					
				
				if len(retList) > 0: return retList
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return ret
		
		return ret
		
	#
	# Get list data from plugcache (called from getActionOptionUIList)
	#
	def _getActionOptionUIList_ORIG (self, obj, objType, valuesDict, method):
		try:
			actions = self.factory.plugcache.getActions (obj)
			
			#indigo.server.log(objType + "Action" + method)
			#indigo.server.log(valuesDict[objType + "Action" + method])
			
			for id, action in actions.iteritems():
				if id == valuesDict[objType + "Action" + method]:
					if "ConfigUI" in action:
						if "Fields" in action["ConfigUI"]:
							for field in action["ConfigUI"]["Fields"]:
								return field["List"]
											
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return []
		
	#
	# Validate the UI
	#
	def validateDeviceConfigUi_ORIG (self, valuesDict, typeId, devId):
		self.logger.debug ("Validating action parameters on device")
		errorDict = indigo.Dict()
		msg = ""
		
		try:
			# Check that we have either a strValuePassOn or strValueFailOn, if we don't then this is either
			# not an action or it's a pseudo action device that the plugin is handling one-off
			if ext.valueValid (valuesDict, self.VALIDATION) == False:
				self.logger.threaddebug ("The current device is not an action device, not validating actions")
				return (True, valuesDict, errorDict)
				
			# Make sure no -line- items are selected
			for i in range (0, len(self.FORMTERMS)):
				method = self.FORMTERMS[i]
				
				if ext.valueValid (valuesDict, self.OPT_LABEL + method + "1") == False: continue # may not have pass or may not have fail
				
				for j in range (1, self.maxFields): 
					if ext.valueValid (valuesDict, self.MENU_VAL + method + str(j)):
						if valuesDict[self.MENU_VAL + method + str(j)] == "-line-":
							msg += "Field {0} has a line selected.  ".format(str(j))
							errorDict[self.MENU_VAL + method + str(j)] = "Invalid selection"
							
				
			if msg != "":
				msg = "There are problems with your conditions:\n\n" + msg
				errorDict["showAlertText"] = msg
				return (False, valuesDict, errorDict)
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return (True, valuesDict, errorDict)







































		