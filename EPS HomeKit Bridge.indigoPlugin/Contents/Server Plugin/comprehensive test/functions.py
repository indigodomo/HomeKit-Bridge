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