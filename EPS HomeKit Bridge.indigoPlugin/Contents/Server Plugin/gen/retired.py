# Routines that were either for testing or were retired during release where there was enough code retired to keep here in case
# the feature wants to be revisited later

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
				
			if valuesDict[thistype.lower()] == "-none-":
				(valuesDict, errorsDict) = self.serverButtonAddDeviceOrAction_None (valuesDict, errorsDict, thistype)
			elif valuesDict[thistype.lower()] == "-all-":
				(valuesDict, errorsDict) = self.serverButtonAddDeviceOrAction_All (valuesDict, errorsDict, thistype, devId)
			elif valuesDict[thistype.lower()] == "-fill-":
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
	def serverButtonAddDeviceOrAction_All (self, valuesDict, errorsDict, thistype, serverId):	
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