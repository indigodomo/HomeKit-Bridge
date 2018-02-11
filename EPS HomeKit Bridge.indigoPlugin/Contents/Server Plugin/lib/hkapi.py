#! /usr/bin/env python
# -*- coding: utf-8 -*-


# hkapi - HomeKit services and characteristics API
#
# Copyright (c) 2018 ColoradoFourWheeler / EPS
#

import indigo
import linecache # exception reporting
import sys # exception reporting
import logging # logging
import ext

PLUGIN_PREFS = {}

################################################################################
# GENERAL FUNCTIONS
################################################################################
	
#
# Compare data types and return if they will convert
#
def compareDataTypes (self, HKItem, HKAttrib, IndigoItem, IndigoAttrib, isState = False):
	try:
		pass
		
	except Exception as e:
		indigo.server.log  (ext.getException(e), isError=True)

#
# Auto resolve an Indigo device to a HomeKit device (service)
#
def automaticHomeKitDevice (dev, loadOptional = False):
	try:
		if dev.id in indigo.actionGroups:
			return service_Switch (dev.id, {}, [], loadOptional)
		
		elif dev.pluginId == "com.perceptiveautomation.indigoplugin.zwave" and dev.deviceTypeId == "zwLockType":
			return service_LockMechanism (dev.id, {}, [], loadOptional)
			
		elif "brightnessLevel" in dev.states and "brightness" in dir(dev):
			return service_Lightbulb (dev.id, {}, [], loadOptional)
			
		elif "Outlet" in dev.model:
			return service_Outlet (dev.id, {}, [], loadOptional)
			
		elif "speedIndex" in dir(dev):
			return service_Fanv2 (dev.id, {}, [], loadOptional)	
			
		elif "sensorInputs" in dir(dev):	
			if "protocol" in dir(dev) and dev.protocol == "Insteon" and dev.model == "I/O-Linc Controller":
				return service_GarageDoorOpener (dev.id, {}, [], loadOptional)	
				
			else:
				return service_GarageDoorOpener (dev.id, {}, [], loadOptional)	
			
		elif "sensorValue" in dir(dev):
			if dev.protocol == "Insteon" and "Motion Sensor" in dev.model: 
				return service_MotionSensor (dev.id, {}, [], loadOptional)	
				
			else:
				return service_MotionSensor (dev.id, {}, [], loadOptional)	
				
		else:
			return service_Switch (dev.id, {}, [], loadOptional)
	
	except Exception as e:
		indigo.server.log  (ext.getException(e), isError=True)

#
# Take characteristic name and return the characteristic class that matches
#
def characteristicsToClasses (characteristic):
	try:
		classes = {"Active": characteristic_Active, "Brightness": characteristic_Brightness, "ColorTemperature": characteristic_ColorTemperature, "CurrentDoorState": characteristic_CurrentDoorState, "CurrentFanState": characteristic_CurrentFanState, "Hue": characteristic_Hue, "LockCurrentState": characteristic_LockCurrentState, "LockPhysicalControls": characteristic_LockPhysicalControls, "LockTargetState": characteristic_LockTargetState, "MotionDetected": characteristic_MotionDetected, "Name": characteristic_Name, "ObstructionDetected": characteristic_ObstructionDetected, "On": characteristic_On, "OutletInUse": characteristic_OutletInUse, "RotationDirection": characteristic_RotationDirection, "RotationSpeed": characteristic_RotationSpeed, "Saturation": characteristic_Saturation, "StatusActive": characteristic_StatusActive, "StatusFault": characteristic_StatusFault, "StatusLowBattery": characteristic_StatusLowBattery, "StatusTampered": characteristic_StatusTampered, "SwingMode": characteristic_SwingMode, "TargetDoorState": characteristic_TargetDoorState, "TargetFanState": characteristic_TargetFanState}

		if characteristic in classes: return classes[characteristic]
		
		return None
		
	except Exception as e:
		indigo.server.log  (ext.getException(e), isError=True)

#
# Device startup to set various attributes
#
def deviceInitialize (dev, devId, characterDict):
	try:
		dev.characterDict = characterDict
		dev.devId = 0
		
		if int(devId) != 0 and (int(devId) in indigo.devices or int(devId) in indigo.actionGroups): dev.devId = int(devId)
		
		# One shared property is name, we can set the alias of this right away
		if dev.devId != 0: 
			dev.Alias = characteristic_Name() # Generic enough for our use
			if int(devId) in indigo.devices:
				dev.Alias.value = indigo.devices[dev.devId].name			
			elif int(devId) in indigo.actionGroups:
				dev.Alias.value = indigo.actionGroups[dev.devId].name			
			
			dev.Model = characteristic_Name()
			if int(devId) in indigo.devices:
				dev.Model.value = indigo.devices[dev.devId].model
			elif int(devId) in indigo.actionGroups:
				dev.Model.value = "Action Group"
		
		dev.updateFromIndigoObject(characterDict)	
		
	
	except Exception as e:
		indigo.server.log  (ext.getException(e), isError=True)

#
# Set the attributes of the device based on what is set in the characteristics dict
#		
def setAttributesForDevice (dev):
	try:
		if "required" in dir(dev):
			for a in dev.required:
				cclass = characteristicsToClasses (a)
				#indigo.server.log (dev.type + "\t" + a)
				setattr (dev, a, cclass() )
				
		if "optional" in dir(dev):
			for a in dev.optional:
				if a in dev.characterDict or dev.loadOptional: # only process optional items if they passed a value for it or if we are forcing it
					cclass = characteristicsToClasses (a)
					setattr (dev, a, cclass() )		
					
		for key, value in dev.characterDict.iteritems():
			if key in dir(dev): # this prevents the user from adding arbitrary characteristics, if it's not in required or optional then it'll be ignored
				#obj = getattr (dev, key)
				#obj.value = value			
				setAttributeValue (dev, key, value)
		
	except Exception as e:
		indigo.server.log  (ext.getException(e), isError=True)
	
#
# Shortcut for each device to use when __str__ is called (i.e., unicoding a device)
#		
def getStr (dev):
	try:
		ret = ""
		proplist = [a for a in dir(dev) if not a.startswith('__') and not callable(getattr(dev, a))]
		for p in proplist:
			if p == "required": continue
			if p == "optional": continue
			if p == "devId": 
				ret += "Indigo Id : " + str(dev.devId) + "\n"
				if dev.devId in indigo.devices:
					ret += "Indigo Type : Device\n"
					ret += "URL : /devices/" + str(dev.devId) + ".json\n"
				elif dev.devId in indigo.actionGroups:
					ret += "Indigo Type : Action Group\n"
					ret += "URL : /actiongroups/" + str(dev.devId) + ".json\n"
				elif dev.devId in indigo.variables:
					ret += "Indigo Type : Variable\n"
					ret += "URL : /variables/" + str(dev.devId) + ".json\n"
					
				continue
			
			if p == "type":
				ret += "Type : " + dev.type + "\n"
				continue
			if p == "desc":
				ret += "Description : " + dev.desc + "\n"
				continue
			
			if p == "characterDict": 
				ret += "Characteristic Values : (Dict)\n"
				for k, v in dev.characterDict.iteritems():
					ret += "\tCharacteristic :\n"
					ret += "\t\tCharacteristic : {0}\n".format(k)
					ret += "\t\tValue : {0} ({1})\n".format(unicode(v), str(type(v)).replace("<type '", "").replace("'>", "") )
					
				continue
				
			if p == "actions":
				ret += "Actions : (List)\n"
				for action in dev.actions:
					ret += "\tAction : (HomeKitAction)\n"
					ret += "\t\tCharacteristic : {0}\n".format(action.characteristic)
					ret += "\t\tWhen : {0}\n".format(action.whenvalueis)
					ret += "\t\tValue : {0} ({1})\n".format(unicode(action.whenvalue), str(type(action.whenvalue)).replace("<type '", "").replace("'>", "") )
					ret += "\t\tValue2 : {0} ({1})\n".format(unicode(action.whenvalue2), str(type(action.whenvalue)).replace("<type '", "").replace("'>", ""))
					ret += "\t\tCommand : {0}\n".format(unicode(action.command))
					ret += "\t\tArguments : {0}\n".format(unicode(action.arguments))
				
				continue
			
			requirement = ""
			if "required" in dir(dev) and p in dev.required: requirement = " (required)"
			
			val = getattr(dev, p)
			ret += p + " : " + unicode(val.value) + requirement + "\n"
		
	except Exception as e:
		indigo.server.log  (ext.getException(e), isError=True)
		
	return ret

#
# All devices point back to here to set an attribute value so we can do calculations and keep everything uniform across devices (and less coding)
#	
def setAttributeValue (dev, attribute, value):
	try:
		ret = True
		
		if not attribute in dir(dev):
			indigo.server.log ("Cannot set {} value of {} because it is not an attribute".format(attribute, dev.Alias.value))
			return False
			
		obj = getattr (dev, attribute)	
	
		if type(value) == type(obj.value):
			obj.value = value
			#indigo.server.log ("Set {} to {}".format(attribute, unicode(value)))
		else:
			# Try to do a basic conversion if possible
			vtype = str(type(value)).replace("<type '", "").replace("'>", "")
			atype = str(type(obj.value)).replace("<type '", "").replace("'>", "")
			
			converted = False
			if vtype == "bool": converted = convertFromBoolean (dev, attribute, value, atype, vtype, obj)
			if vtype == "str" and atype == "unicode":
				obj.value = value
				converted = True
			if vtype == "int" and atype == "float":
				obj.value = float(obj.value)
				converted = True
			
			if not converted:
				indigo.server.log("Unable to set the value of {} on {} to {} because that attribute requires {} and it was given {}".format(attribute, dev.Alias.value, unicode(value), atype, vtype))
				return False
	
	except Exception as e:
		indigo.server.log  (ext.getException(e), isError=True)
		ret = False
		
	return ret
	
#
# Convert from boolean
#
def convertFromBoolean (dev, attribute, value, atype, vtype, obj):
	try:
		newvalue = None
		
		# Convert to integer
		if atype == "int":
			if value: newvalue = 1
			if not value: newvalue = 0
			
		if atype == "str":
			if value: newvalue = "true"
			if not value: newvalue = "false"	
			
		if "validValues" in dir(obj) and newvalue in obj.validValues: 
			obj.value = newvalue
			return True
			
		elif "validValues" in dir(obj) and newvalue not in obj.validValues: 
			indigo.server.log("Converted {} for {} from {} to {} but the coverted value of {} was not a valid value for this attribute and will not be accepted by HomeKit, it will remain at the current value of {}".format(attribute, dev.Alias.value, vtype, atype, unicode(newvalue), unicode(obj.value)))
			return False
		
	except Exception as e:
		indigo.server.log  (ext.getException(e), isError=True)
		
	return False
				

################################################################################
# DEVICES (MISC)
################################################################################

# ==============================================================================
# ACTION
# ==============================================================================
class HomeKitAction ():
	def __init__(self, characteristic, whenvalueis = "equal", whenvalue = 0, command = "", arguments = [], whenvalue2 = 0, monitors = {}):
		try:
			self.logger = logging.getLogger ("Plugin.HomeKitAction")
			
			self.characteristic = characteristic
			self.whenvalueis = whenvalueis
			self.whenvalue = whenvalue
			self.whenvalue2 = whenvalue2
			self.command = command
			self.arguments = arguments
			self.monitors = monitors # Dict of objId: attr_* | state_* | prop_* that we will monitor for this action - partly for future use if we are tying multiple objects to different properties and actions but also so our subscribe to changes knows what will trigger an update
			
			# Determine the value data type by creating a mock object
			cclass = characteristicsToClasses (characteristic)
			obj = cclass()
			self.valuetype = str(type(obj.value)).replace("<type '", "").replace("'>", "")
			
			self.validOperators = ["equal", "notequal", "greater", "less", "between"]
		
		except Exception as e:
			self.logger.error  (ext.getException(e))
			
	def xstr__(self):
		ret = ""
		
	def __str__ (self):
		ret = ""
		
		ret += "Action : (HomeKitAction)\n"
		ret += "\tCharacteristic : {0}\n".format(self.characteristic)
		ret += "\tWhen : {0}\n".format(self.whenvalueis)
		ret += "\tValue : {0} ({1})\n".format(unicode(self.whenvalue), str(type(self.whenvalue)).replace("<type '", "").replace("'>", "") )
		ret += "\tValue2 : {0} ({1})\n".format(unicode(self.whenvalue2), str(type(self.whenvalue)).replace("<type '", "").replace("'>", ""))
		ret += "\tCommand : {0}\n".format(unicode(self.command))
		ret += "\tArguments : {0}\n".format(unicode(self.arguments))
		
		return ret
		
	def run (self, value):
		try:
			# See if the value falls within the actions limitations and if it does then run the associated command
			#indigo.server.log(unicode(self))
		
			# Get the value type of the value so we can convert from string to that type
			if type(self.whenvalue) == bool:
				if value.lower() == "true": 
					value = True
				elif value.lower() == "false":
					value = False
					
			elif type(self.whenvalue) == int:
				value = int(value)
				
			else:
				self.logger.error ("Unknown value for processAction: {}".format(str(type(self.whenvalue)).replace("<type '", "").replace("'>", "")))
				return False
				
			isValid = False
			
			if self.whenvalueis == "equal" and value == self.whenvalue:
				isValid = True
				
			elif self.whenvalueis == "between" and value >= self.whenvalue and value <= self.whenvalue2:
				isValid = True
			
			if isValid:
				# Try to run the command
				try:
					# Fix up the arguments for placeholders
					args = []
					for a in self.arguments:
						if unicode(a) == "=value=":
							args.append(value)
						else:
							args.append(a)
				
					cmd = self.command.split(".")
					func = indigo
				
					for c in cmd:
						func = getattr(func, c)
				
					if len(args) > 0: 
						retval = func(*args)
					else:
						retval = func()
				
				except Exception as ex:
					self.logger.error (ext.getException(ex))
					return False
		
				return True
			
			else:
				return False
	
		except Exception as e:
			self.logger.error (ext.getException(e))
			return False
		
		return True


################################################################################
# DEVICES (SERVICES)
################################################################################

# ==============================================================================
# FAN V2
# ==============================================================================
class service_Fanv2 ():
	def __init__(self, devId = 0, characterDict = {}, deviceActions = [], loadOptional = False):
		try:
			self.type = "Fanv2"
			self.desc = "Fan Version 2"
			self.native = True # Functions can map directly to Indigo or a plugin (see requiresPlugin) natively without any customization
			self.requiresPlugin = [] # For this device to work Indigo must have one or more plugins installed, list of dict items with name and plugin id requirements
			
			self.required = ["Active"]
			self.optional = ["CurrentFanState", "TargetFanState", "LockPhysicalControls", "Name", "RotationDirection", "RotationSpeed", "SwingMode"]
			self.actions = []
			self.loadOptional = loadOptional # Create attributes for the optional fields
			
			# We have to append from here, if we were to set self.actions equal an outside list it would share among all instances of this class
			for d in deviceActions:
				self.actions.append (d)
			
			self.characterDict = characterDict
			self.devId = 0
			
			deviceInitialize (self, devId, characterDict)
			setAttributesForDevice (self)
			
		except Exception as e:
			indigo.server.log  (ext.getException(e), isError=True)	
			
	def updateFromIndigoObject (self, characterDict):
		try:
			definedActions = []
			for a in self.actions:
				definedActions.append (a["name"])
				
			self.characterDict = characterDict # Always overwrite
			if self.devId != 0 and self.devId in indigo.devices:
				dev = indigo.devices[self.devId]
				curval = 0 # Unsecure
				if "onState" in dir(dev):
					if dev.onState: 
						curval = 1
					else:
						curval = 0
		
				if "onState" in dir(dev) and "Active" not in characterDict: characterDict["Active"] = curval
				if "onState" in dir(dev) and "CurrentFanState" not in characterDict: characterDict["CurrentFanState"] = curval + 1
				if "onState" in dir(dev) and "TargetFanState" not in characterDict: characterDict["TargetFanState"] = 0 # Assume ceiling fan and, as such, it's always MANUAL or 0
				if "speedIndex" in dir(dev) and "RotationSpeed" not in characterDict: characterDict["RotationSpeed"] = dev.speedIndex		
				
				if "TargetFanState" not in definedActions:
					self.actions.append (HomeKitAction("Active", "equal", 0, "device.turnOff", [self.devId], 0, {self.devId: "attr_onState"}))
					self.actions.append (HomeKitAction("Active", "equal", 1, "device.turnOn", [self.devId], 0, {self.devId: "attr_brightness"}))
					
				if "speedIndex" not in definedActions:
					self.actions.append (HomeKitAction("RotationSpeed", "between", 0, "speedcontrol.setSpeedLevel", [self.devId, "=value="], 100, {self.devId: "attr_brightness"}))
					#self.actions.append (HomeKitAction("RotationSpeed", "equal", 0, "device.turnOff", [self.devId], 0, {self.devId: "attr_onState"}))
					#self.actions.append (HomeKitAction("RotationSpeed", "equal", 100, "device.turnOn", [self.devId], 0, {self.devId: "attr_onState"}))
					
			elif self.devId != 0 and self.devId in indigo.actionGroups:
				dev = indigo.actionGroups[self.devId]
				
				if "Active" not in characterDict: characterDict["On"] = False
				
				if "Active" not in definedActions:
					self.actions.append (HomeKitAction("Active", "equal", 1, "actionGroup.execute", [self.devId], 0, {}))
				
		except Exception as e:
			indigo.server.log  (ext.getException(e), isError=True)	
		
	def setValue (self, attribute, value):
		return setAttributeValue (self, attribute, value)
			
	def __str__(self):
		return getStr(self)
		
# ==============================================================================
# GARAGE DOOR OPENER
# ==============================================================================
class service_GarageDoorOpener ():
	def __init__(self, devId = 0, characterDict = {}, deviceActions = [], loadOptional = False):
		try:
			self.type = "GarageDoorOpener"
			self.desc = "Garage Door Opener"
			self.native = True # Functions can map directly to Indigo or a plugin (see requiresPlugin) natively without any customization
			self.requiresPlugin = [] # For this device to work Indigo must have one or more plugins installed, list of dict items with name and plugin id requirements
			
			self.required = ["CurrentDoorState", "TargetDoorState", "ObstructionDetected"]
			self.optional = ["LockCurrentState", "LockTargetState", "Name"]
			self.actions = []
			self.loadOptional = loadOptional # Create attributes for the optional fields
			
			# We have to append from here, if we were to set self.actions equal an outside list it would share among all instances of this class
			for d in deviceActions:
				self.actions.append (d)
			
			self.characterDict = characterDict
			self.devId = 0
			
			deviceInitialize (self, devId, characterDict)
			setAttributesForDevice (self)
			
		except Exception as e:
			indigo.server.log  (ext.getException(e), isError=True)	
			
	def updateFromIndigoObject (self, characterDict):
		try:
			definedActions = []
			for a in self.actions:
				definedActions.append (a["name"])
				
			self.characterDict = characterDict # Always overwrite
			if self.devId != 0 and self.devId in indigo.devices:
				dev = indigo.devices[self.devId]
		
				# Insteon Multi I/O controller
				if "protocol" in dir(dev) and unicode(dev.protocol) == "Insteon" and dev.model == "I/O-Linc Controller":
					if "binaryInput1" in dev.states and "CurrentDoorState" not in characterDict: 
						characterDict["CurrentDoorState"] = 1 # Open
						if not dev.states["binaryInput1"]: characterDict["CurrentDoorState"] = 0 # Closed
						
					if "binaryInput1" in dev.states and "TargetDoorState" not in characterDict: 
						characterDict["TargetDoorState"] = 1 # Open
						if not dev.states["binaryInput1"]: characterDict["TargetDoorState"] = 0 # Closed	
						
					if "ObstructionDetected" not in characterDict: characterDict["ObstructionDetected"] = 0 # Unsupported but it's required right now
				
					if "CurrentDoorState" not in definedActions:
						self.actions.append (HomeKitAction("CurrentDoorState", "equal", 0, "iodevice.setBinaryOutput", [self.devId, 1, True], 0, {self.devId: "state_binaryInput1"}))
						self.actions.append (HomeKitAction("CurrentDoorState", "equal", 1, "iodevice.setBinaryOutput", [self.devId, 1, True], 0, {self.devId: "state_binaryInput1"}))
						
					if "TargetDoorState" not in definedActions:
						self.actions.append (HomeKitAction("TargetDoorState", "equal", 0, "iodevice.setBinaryOutput", [self.devId, 1, True], 0, {self.devId: "state_binaryInput1"}))
						self.actions.append (HomeKitAction("TargetDoorState", "equal", 1, "iodevice.setBinaryOutput", [self.devId, 1, True], 0, {self.devId: "state_binaryInput1"}))	
					
					
			elif self.devId != 0 and self.devId in indigo.actionGroups:
				dev = indigo.actionGroups[self.devId]
				
				if "CurrentDoorState" not in characterDict: characterDict["CurrentDoorState"] = 1
				if "TargetDoorState" not in characterDict: characterDict["TargetDoorState"] = 1
				if "ObstructionDetected" not in characterDict: characterDict["ObstructionDetected"] = 0
				
				if "CurrentDoorState" not in definedActions:
					self.actions.append (HomeKitAction("CurrentDoorState", "equal", True, "actionGroup.execute", [self.devId], 0, {}))
					
				if "TargetDoorState" not in definedActions:
					self.actions.append (HomeKitAction("TargetDoorState", "equal", True, "actionGroup.execute", [self.devId], 0, {}))	
				
		except Exception as e:
			indigo.server.log  (ext.getException(e), isError=True)	
		
	def setValue (self, attribute, value):
		return setAttributeValue (self, attribute, value)
			
	def __str__(self):
		return getStr(self)		

# ==============================================================================
# LIGHT BULB
# ==============================================================================
class service_Lightbulb ():
	def __init__(self, devId = 0, characterDict = {}, deviceActions = [], loadOptional = False):
		try:
			self.type = "Lightbulb"
			self.desc = "Light Bulb"
			self.native = True # Functions can map directly to Indigo or a plugin (see requiresPlugin) natively without any customization
			self.requiresPlugin = [] # For this device to work Indigo must have one or more plugins installed, list of dict items with name and plugin id requirements
			
			self.required = ["On"]
			self.optional = ["Brightness", "Hue", "Saturation", "Name", "ColorTemperature"]
			self.actions = []
			self.loadOptional = loadOptional # Create attributes for the optional fields
			
			# We have to append from here, if we were to set self.actions equal an outside list it would share among all instances of this class
			for d in deviceActions:
				self.actions.append (d)
			
			self.characterDict = characterDict
			self.devId = 0
			
			deviceInitialize (self, devId, characterDict)
			setAttributesForDevice (self)
			
		except Exception as e:
			indigo.server.log  (ext.getException(e), isError=True)	
			
	def updateFromIndigoObject (self, characterDict):
		try:
			definedActions = []
			for a in self.actions:
				definedActions.append (a["name"])
				
			self.characterDict = characterDict # Always overwrite
			if self.devId != 0 and self.devId in indigo.devices:
				dev = indigo.devices[self.devId]
		
				if "onState" in dir(dev) and "On" not in characterDict: characterDict["On"] = dev.onState
				if "brightness" in dir(dev) and "Brightness" not in characterDict: characterDict["Brightness"] = dev.brightness		
				
				if "On" not in definedActions:
					self.actions.append (HomeKitAction("On", "equal", False, "device.turnOff", [self.devId], 0, {self.devId: "attr_onState"}))
					self.actions.append (HomeKitAction("On", "equal", True, "device.turnOn", [self.devId], 0, {self.devId: "attr_brightness"}))
					
				if "Brightness" not in definedActions:
					self.actions.append (HomeKitAction("Brightness", "between", 0, "dimmer.setBrightness", [self.devId, "=value="], 100, {self.devId: "attr_brightness"}))
					#self.actions.append (HomeKitAction("Brightness", "equal", 0, "device.turnOff", [self.devId], 0, {self.devId: "attr_onState"}))
					#self.actions.append (HomeKitAction("Brightness", "equal", 100, "device.turnOn", [self.devId], 0, {self.devId: "attr_onState"}))
					
			elif self.devId != 0 and self.devId in indigo.actionGroups:
				dev = indigo.actionGroups[self.devId]
				
				if "On" not in characterDict: characterDict["On"] = False
				
				if "On" not in definedActions:
					self.actions.append (HomeKitAction("On", "equal", True, "actionGroup.execute", [self.devId], 0, {}))
				
		except Exception as e:
			indigo.server.log  (ext.getException(e), isError=True)	
		
	def setValue (self, attribute, value):
		return setAttributeValue (self, attribute, value)
			
	def __str__(self):
		return getStr(self)
		
# ==============================================================================
# MOTION SENSOR
# ==============================================================================
class service_MotionSensor ():
	def __init__(self, devId = 0, characterDict = {}, deviceActions = [], loadOptional = False):
		try:
			self.type = "MotionSensor"
			self.desc = "Motion Sensor"
			self.native = True # Functions can map directly to Indigo or a plugin (see requiresPlugin) natively without any customization
			self.requiresPlugin = [] # For this device to work Indigo must have one or more plugins installed
			
			self.required = ["MotionDetected"]
			self.optional = ["StatusActive", "StatusFault", "StatusTampered", "StatusLowBattery", "Name"]
			self.actions = []
			self.loadOptional = loadOptional # Create attributes for the optional fields
			
			# We have to append from here, if we were to set self.actions equal an outside list it would share among all instances of this class
			for d in deviceActions:
				self.actions.append (d)
			
			self.characterDict = characterDict
			self.devId = 0
			
			deviceInitialize (self, devId, characterDict)
			setAttributesForDevice (self)
			
		except Exception as e:
			indigo.server.log  (ext.getException(e), isError=True)	
			
	def updateFromIndigoObject (self, characterDict):
		global PLUGIN_PREFS
		
		try:
			definedActions = []
			for a in self.actions:
				definedActions.append (a["name"])
				
			self.characterDict = characterDict # Always overwrite
			if self.devId != 0 and self.devId in indigo.devices:
				dev = indigo.devices[self.devId]
				
				if "onState" in dir(dev) and "MotionDetected" not in characterDict: characterDict["MotionDetected"] = dev.onState	
				if "batteryLevel" in dir(dev) and dev.batteryLevel is not None: 
					characterDict["StatusLowBattery"] = 0
					
					if "lowbattery" in PLUGIN_PREFS:
						lowbattery = int(PLUGIN_PREFS["lowbattery"])
						if lowbattery > 0: lowbattery = lowbattery / 100
						
						if dev.batteryLevel < ((100 * lowbattery) + 1): characterDict["StatusLowBattery"] = 1
						
				# Special consideration for Fibaro sensors that fill up a couple more Characteristics (if this grows we may need to call a function for these)
				if "model" in dir(dev) and "FGMS001" in dev.model:
					# See if we can find all the devices with this Zwave ID
					for idev in indigo.devices.iter("com.perceptiveautomation.indigoplugin.zwave.zwOnOffSensorType"):
						if idev.address == dev.address:
							# Same Fibaro model
							if "Tilt/Tamper" in idev.subModel:
								characterDict["StatusTampered"] = 0
								if idev.onState: characterDict["StatusTampered"] = 1
								
								# Make sure this gets added to our watch list
								self.actions.append (HomeKitAction("StatusTampered", "equal", False, "device.turnOff", [idev.id], 0, {idev.id: "attr_onState"}))
						
				# This is a read only device so it'll never need this but it must be here so when we get activity for this device we can tell
				# homekit to update, if this isn't here it'll never know that attr_onState should trigger an HK update
				self.actions.append (HomeKitAction("MotionDetected", "equal", False, "device.turnOff", [self.devId], 0, {self.devId: "attr_onState"}))
				self.actions.append (HomeKitAction("StatusLowBattery", "equal", False, "device.turnOff", [self.devId], 0, {self.devId: "attr_batteryLevel"}))
					
			elif self.devId != 0 and self.devId in indigo.actionGroups:
				dev = indigo.actionGroups[self.devId]
				
				if "MotionDetected" not in characterDict: characterDict["MotionDetected"] = False

				# This is a read only device so it'll never need this but it must be here so when we get activity for this device we can tell
				# homekit to update, if this isn't here it'll never know that attr_onState should trigger an HK update
				self.actions.append (HomeKitAction("MotionDetected", "equal", False, "device.turnOff", [self.devId], 0, {self.devId: "attr_onState"}))

				
		except Exception as e:
			indigo.server.log  (ext.getException(e), isError=True)			
		
	def setAttributeValue (self, attribute, value):
		return setDevValue (self, attribute, value)
			
	def __str__(self):
		return getStr(self)			
		
# ==============================================================================
# OUTLET
# ==============================================================================
class service_Outlet ():
	def __init__(self, devId = 0, characterDict = {}, deviceActions = [], loadOptional = False):
		try:
			self.type = "Outlet"
			self.desc = "Outlet"
			self.native = True # Functions can map directly to Indigo or a plugin (see requiresPlugin) natively without any customization
			self.requiresPlugin = [] # For this device to work Indigo must have one or more plugins installed
			
			self.required = ["On", "OutletInUse"]
			self.optional = []
			self.actions = []
			self.loadOptional = loadOptional # Create attributes for the optional fields
			
			# We have to append from here, if we were to set self.actions equal an outside list it would share among all instances of this class
			for d in deviceActions:
				self.actions.append (d)
			
			self.characterDict = characterDict
			self.devId = 0
			
			deviceInitialize (self, devId, characterDict)
			setAttributesForDevice (self)
			
		except Exception as e:
			indigo.server.log  (ext.getException(e), isError=True)	
			
	def updateFromIndigoObject (self, characterDict):
		try:
			definedActions = []
			for a in self.actions:
				definedActions.append (a["name"])
				
			self.characterDict = characterDict # Always overwrite
			if self.devId != 0 and self.devId in indigo.devices:
				dev = indigo.devices[self.devId]
		
				if "onState" in dir(dev) and "On" not in characterDict: characterDict["On"] = dev.onState	
				if "On" not in definedActions:
					self.actions.append (HomeKitAction("On", "equal", False, "device.turnOff", [self.devId], 0, {self.devId: "attr_onState"}))
					self.actions.append (HomeKitAction("On", "equal", True, "device.turnOn", [self.devId], 0, {self.devId: "attr_onState"}))
					
			elif self.devId != 0 and self.devId in indigo.actionGroups:
				dev = indigo.actionGroups[self.devId]
				
				if "On" not in characterDict: characterDict["On"] = False
				
				if "On" not in definedActions:
					self.actions.append (HomeKitAction("On", "equal", True, "actionGroup.execute", [self.devId], 0, {}))

		except Exception as e:
			indigo.server.log  (ext.getException(e), isError=True)			
		
	def setAttributeValue (self, attribute, value):
		return setDevValue (self, attribute, value)
			
	def __str__(self):
		return getStr(self)	
		
# ==============================================================================
# LOCK MECHANISM
# ==============================================================================
class service_LockMechanism ():
	def __init__(self, devId = 0, characterDict = {}, deviceActions = [], loadOptional = False):
		try:
			self.type = "LockMechanism"
			self.desc = "Lock Mechanism"
			self.native = True # Functions can map directly to Indigo or a plugin (see requiresPlugin) natively without any customization
			self.requiresPlugin = [] # For this device to work Indigo must have one or more plugins installed
			
			self.required = ["LockCurrentState", "LockTargetState"]
			self.optional = ["Name"]
			self.actions = []
			self.loadOptional = loadOptional # Create attributes for the optional fields
			
			# We have to append from here, if we were to set self.actions equal an outside list it would share among all instances of this class
			for d in deviceActions:
				self.actions.append (d)
			
			self.characterDict = characterDict
			self.devId = 0
			
			deviceInitialize (self, devId, characterDict)
			setAttributesForDevice (self)
			
		except Exception as e:
			indigo.server.log  (ext.getException(e), isError=True)	
			
	def updateFromIndigoObject (self, characterDict):
		try:
			definedActions = []
			for a in self.actions:
				definedActions.append (a["name"])
				
			self.characterDict = characterDict # Always overwrite
			if self.devId != 0 and self.devId in indigo.devices:
				dev = indigo.devices[self.devId]
				curval = 0 # Unsecure
				if "onState" in dir(dev):
					if dev.onState: 
						curval = 1
					else:
						curval = 0
		
				if "onState" in dir(dev) and "LockCurrentState" not in characterDict: characterDict["LockCurrentState"] = curval
				if "onState" in dir(dev) and "LockTargetState" not in characterDict: characterDict["LockTargetState"] = curval
					
				if "LockTargetState" not in definedActions:
					self.actions.append (HomeKitAction("LockTargetState", "equal", 0, "device.turnOff", [self.devId], 0, {self.devId: "attr_onState"}))
					self.actions.append (HomeKitAction("LockTargetState", "equal", 1, "device.turnOn", [self.devId], 0, {self.devId: "attr_onState"}))
					
			elif self.devId != 0 and self.devId in indigo.actionGroups:
				dev = indigo.actionGroups[self.devId]
				
				if "On" not in characterDict: characterDict["On"] = False
				
				if "On" not in definedActions:
					self.actions.append (HomeKitAction("On", "equal", True, "actionGroup.execute", [self.devId], 0, {}))		

		except Exception as e:
			indigo.server.log  (ext.getException(e), isError=True)			
		
	def setAttributeValue (self, attribute, value):
		return setDevValue (self, attribute, value)
			
	def __str__(self):
		return getStr(self)					
		
# ==============================================================================
# SWITCH
# ==============================================================================
class service_Switch ():
	def __init__(self, devId = 0, characterDict = {}, deviceActions = [], loadOptional = False):
		try:
			self.type = "Switch"
			self.desc = "Switch"
			self.native = True # Functions can map directly to Indigo or a plugin (see requiresPlugin) natively without any customization
			self.requiresPlugin = [] # For this device to work Indigo must have one or more plugins installed
			
			self.required = ["On"]
			self.optional = []
			self.actions = []
			self.loadOptional = loadOptional # Create attributes for the optional fields
			
			# We have to append from here, if we were to set self.actions equal an outside list it would share among all instances of this class
			for d in deviceActions:
				self.actions.append (d)
			
			self.characterDict = characterDict
			self.devId = 0
			
			#indigo.server.log(unicode(devId))
			deviceInitialize (self, devId, characterDict)
			setAttributesForDevice (self)
			
		except Exception as e:
			indigo.server.log  (ext.getException(e), isError=True)	
			
	def updateFromIndigoObject (self, characterDict):
		try:
			definedActions = []
			for a in self.actions:
				definedActions.append (a["name"])
					
			self.characterDict = characterDict # Always overwrite
			if self.devId != 0 and self.devId in indigo.devices:
				dev = indigo.devices[self.devId]
				
				if "onState" in dir(dev) and "On" not in characterDict: 
					characterDict["On"] = dev.onState	
				else:
					characterDict["On"] = False # Since all devices default to this type, this ensure that we never have NO characteristics
				
				if "On" not in definedActions:
					self.actions.append (HomeKitAction("On", "equal", False, "device.turnOff", [self.devId], 0, {self.devId: "attr_onState"}))
					self.actions.append (HomeKitAction("On", "equal", True, "device.turnOn", [self.devId], 0, {self.devId: "attr_onState"}))
					
			elif self.devId != 0 and self.devId in indigo.actionGroups:
				dev = indigo.actionGroups[self.devId]
				
				if "On" not in characterDict: characterDict["On"] = False
				
				if "On" not in definedActions:
					self.actions.append (HomeKitAction("On", "equal", True, "actionGroup.execute", [self.devId], 0, {}))
					

		except Exception as e:
			indigo.server.log  (ext.getException(e), isError=True)			
		
	def setAttributeValue (self, attribute, value):
		return setDevValue (self, attribute, value)
			
	def __str__(self):
		return getStr(self)				

################################################################################
# CHARACTERISTICS
################################################################################

# ==============================================================================
# ACTIVE
# ==============================================================================
class characteristic_Active:	
	def __init__(self):
		self.value = 0 # inactive
		self.maxValue = 1
		self.minValue = 0
		
		self.validValues = [0, 1]
		
		self.readonly = False
		self.notify = True
	
# ==============================================================================
# BRIGHTNESS
# ==============================================================================
class characteristic_Brightness:
	def __init__(self):
		self.value = 0
		self.maxValue = 100
		self.minValue = 0
		self.minStep = 1
		
		self.readonly = False
		self.notify = True
		
# ==============================================================================
# COLOR TEMPERATURE
# ==============================================================================		
class characteristic_ColorTemperature:
	def __init__(self):
		self.value = 140
		self.minValue = 140
		self.maxValue = 500
		self.minStep = 1	
		
		self.readonly = False
		self.notify = True	
		
# ==============================================================================
# CURRENT DOOR STATE
# ==============================================================================
class characteristic_CurrentDoorState:	
	def __init__(self):
		self.value = 0 # open [closed, opening, closing, stopped]
		self.maxValue = 4
		self.minValue = 0
		
		self.validValues = [0, 1, 2, 3, 4]
		
		self.readonly = True
		self.notify = True			
		
# ==============================================================================
# CURRENT FAN STATE
# ==============================================================================
class characteristic_CurrentFanState:	
	def __init__(self):
		self.value = 0 # inactive
		self.maxValue = 2
		self.minValue = 0
		
		self.validValues = [0, 1, 2]
		
		self.readonly = True
		self.notify = True		
		
# ==============================================================================
# HUE
# ==============================================================================		
class characteristic_Hue:
	def __init__(self):
		self.value = 0.0
		self.maxValue = 360
		self.minValue = 0
		self.minStep = 1
		
		self.readonly = False
		self.notify = True
		
# ==============================================================================
# LOCK CURRENT STATE
# ==============================================================================
class characteristic_LockCurrentState:	
	def __init__(self):
		self.value = 0 # Unsecured [Secured, Jammed, Unknown]
		self.maxValue = 3
		self.minValue = 0
		
		self.validValues = [0, 1, 2, 3]		
		
		self.readonly = True
		self.notify = True
		
# ==============================================================================
# LOCK PHYSICAL CONTROLS
# ==============================================================================
class characteristic_LockPhysicalControls:	
	def __init__(self):
		self.value = 0 # lock disabled [lock enabled]
		self.maxValue = 1
		self.minValue = 0
		
		self.validValues = [0, 1]
		
		self.readonly = False
		self.notify = True		
		
# ==============================================================================
# LOCK TARGET STATE
# ==============================================================================
class characteristic_LockTargetState:	
	def __init__(self):
		self.value = 0 # Unsecured [Secured]
		self.maxValue = 1
		self.minValue = 0
		
		self.validValues = [0, 1]	
		
		self.readonly = False
		self.notify = True		

# ==============================================================================
# MOTION DETECTED
# ==============================================================================
class characteristic_MotionDetected:
	def __init__(self):
		self.value = False
		
		self.validValues = [True, False]
		
		self.readonly = True
		self.notify = False		
		
# ==============================================================================
# NAME
# ==============================================================================		
class characteristic_Name:
	def __init__(self):
		self.value = u""	
		
		self.readonly = False
		self.notify = False
		
# ==============================================================================
# OBSTRUCTION DETECTED
# ==============================================================================
class characteristic_ObstructionDetected:	
	def __init__(self):
		self.value = False
		
		self.validValues = [True, False]
		
		self.readonly = True
		self.notify = False				
		
# ==============================================================================
# ON
# ==============================================================================
class characteristic_On:
	def __init__(self):
		self.value = False
		
		self.validValues = [True, False]
		
		self.readonly = False
		self.notify = False		
		
# ==============================================================================
# OUTLET IN USE
# ==============================================================================
class characteristic_OutletInUse:
	def __init__(self):
		self.value = False
		
		self.validValues = [True, False]	
		
		self.readonly = True
		self.notify = True		
		
# ==============================================================================
# ROTATION DIRECTION
# ==============================================================================
class characteristic_RotationDirection:	
	def __init__(self):
		self.value = 0 # clockwise [counter-clockwise]
		self.maxValue = 1
		self.minValue = 0
		
		self.validValues = [0, 1]
		
		self.readonly = False
		self.notify = True		
		
# ==============================================================================
# ROTATION SPEED
# ==============================================================================
class characteristic_RotationSpeed:	
	def __init__(self):
		self.value = 0.0
		self.maxValue = 100
		self.minValue = 0
		self.minStep = 1
				
		self.readonly = False
		self.notify = True		
	
# ==============================================================================
# SATURATION
# ==============================================================================		
class characteristic_Saturation:
	def __init__(self):
		self.value = 0.0
		self.maxValue = 100
		self.minValue = 0
		self.minStep = 1

		self.readonly = False
		self.notify = True
		
# ==============================================================================
# STATUS ACTIVE
# ==============================================================================
class characteristic_StatusActive:
	def __init__(self):
		self.value = True
		
		self.validValues = [True, False]
		
		self.readonly = True
		self.notify = False			
		
# ==============================================================================
# STATUS FAULT
# ==============================================================================
class characteristic_StatusFault:	
	def __init__(self):
		self.value = 0 # no fault [fault]
		self.maxValue = 1
		self.minValue = 0
		
		self.validValues = [0, 1]
		
		self.readonly = True
		self.notify = True			
		
# ==============================================================================
# STATUS LOW BATTERY
# ==============================================================================
class characteristic_StatusLowBattery:	
	def __init__(self):
		self.value = 0 # normal [low]
		self.maxValue = 1
		self.minValue = 0
		
		self.validValues = [0, 1]
		
		self.readonly = True
		self.notify = True			
		
# ==============================================================================
# STATUS TAMPERED
# ==============================================================================
class characteristic_StatusTampered:	
	def __init__(self):
		self.value = 0 # not tampered [tampered]
		self.maxValue = 1
		self.minValue = 0
		
		self.validValues = [0, 1]
		
		self.readonly = True
		self.notify = True			
		
# ==============================================================================
# SWING MODE
# ==============================================================================
class characteristic_SwingMode:	
	def __init__(self):
		self.value = 0 # disabled [enabled]
		self.maxValue = 1
		self.minValue = 0
		
		self.validValues = [0, 1]
		
		self.readonly = False
		self.notify = True		
		
# ==============================================================================
# TARGET DOOR STATE
# ==============================================================================
class characteristic_TargetDoorState:	
	def __init__(self):
		self.value = 0 # open [closed]
		self.maxValue = 1
		self.minValue = 0
		
		self.validValues = [0, 1]
		
		self.readonly = True
		self.notify = True			

# ==============================================================================
# TARGET FAN STATTE
# ==============================================================================
class characteristic_TargetFanState:	
	def __init__(self):
		self.value = 0 # inactive
		self.maxValue = 1
		self.minValue = 0
		
		self.validValues = [0, 1]
		
		self.readonly = False
		self.notify = True