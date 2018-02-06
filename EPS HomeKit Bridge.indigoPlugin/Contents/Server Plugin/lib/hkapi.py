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
		if dev.pluginId == "com.perceptiveautomation.indigoplugin.zwave" and dev.deviceTypeId == "zwLockType":
			return service_LockMechanism (dev.id, {}, [], loadOptional)
			
		elif "brightnessLevel" in dev.states and "brightness" in dir(dev):
			return service_Lightbulb (dev.id, {}, [], loadOptional)
			
		elif "Outlet" in dev.model:
			return service_Outlet (dev.id, {}, [], loadOptional)
			
		else:
			return service_Switch (dev.id, {}, [], loadOptional)
	
	except Exception as e:
		indigo.server.log  (ext.getException(e), isError=True)

#
# Take characteristic name and return the characteristic class that matches
#
def characteristicsToClasses (characteristic):
	try:
		classes = {"Brightness": characteristic_Brightness, "ColorTemperature": characteristic_ColorTemperature, "Hue": characteristic_Hue, "LockCurrentState": characteristic_LockCurrentState, "LockTargetState": characteristic_LockTargetState, "Name": characteristic_Name, "On": characteristic_On, "OutletInUse": characteristic_OutletInUse, "Saturation": characteristic_Saturation }
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
		
		if int(devId) != 0 and int(devId) in indigo.devices: dev.devId = int(devId)
		
		# One shared property is name, we can set the alias of this right away
		if dev.devId != 0: 
			dev.Alias = characteristic_Name() # Generic enough for our use
			dev.Alias.value = indigo.devices[dev.devId].name			
			dev.Model = characteristic_Name()
			dev.Model.value = indigo.devices[dev.devId].model
		
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
	def __init__(self, characteristic, whenvalueis = "equal", whenvalue = 0, command = "", arguments = [], whenvalue2 = 0):
		try:
			self.logger = logging.getLogger ("Plugin.HomeKitAction")
			
			self.characteristic = characteristic
			self.whenvalueis = whenvalueis
			self.whenvalue = whenvalue
			self.whenvalue2 = whenvalue2
			self.command = command
			self.arguments = arguments
			
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
# LIGHT BULB
# ==============================================================================
class service_Lightbulb ():
	def __init__(self, devId = 0, characterDict = {}, deviceActions = [], loadOptional = False):
		try:
			self.type = "Lightbulb"
			self.desc = "Light Bulb"
			
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
			self.characterDict = characterDict # Always overwrite
			if self.devId != 0 and self.devId in indigo.devices:
				dev = indigo.devices[self.devId]
		
				if "onState" in dir(dev) and "On" not in characterDict: characterDict["On"] = dev.onState
				if "brightness" in dir(dev) and "Brightness" not in characterDict: characterDict["Brightness"] = dev.brightness		
				
				definedActions = []
				for a in self.actions:
					definedActions.append (a["name"])
				
				if "On" not in definedActions:
					self.actions.append (HomeKitAction("On", "equal", False, "device.turnOff", [self.devId]))
					self.actions.append (HomeKitAction("On", "equal", True, "device.turnOn", [self.devId]))
					
				if "Brightness" not in definedActions:
					self.actions.append (HomeKitAction("Brightness", "between", 1, "dimmer.setBrightness", [self.devId, "=value="], 99))
					self.actions.append (HomeKitAction("Brightness", "equal", 0, "device.turnOff", [self.devId]))
					self.actions.append (HomeKitAction("Brightness", "equal", 100, "device.turnOn", [self.devId]))
					

		except Exception as e:
			indigo.server.log  (ext.getException(e), isError=True)	
		
	def setValue (self, attribute, value):
		return setAttributeValue (self, attribute, value)
			
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
			self.characterDict = characterDict # Always overwrite
			if self.devId != 0 and self.devId in indigo.devices:
				dev = indigo.devices[self.devId]
		
				if "onState" in dir(dev) and "On" not in characterDict: characterDict["On"] = dev.onState	
				
				definedActions = []
				for a in self.actions:
					definedActions.append (a["name"])
				
				if "On" not in definedActions:
					self.actions.append (HomeKitAction("On", "equal", False, "device.turnOff", [self.devId]))
					self.actions.append (HomeKitAction("On", "equal", True, "device.turnOn", [self.devId]))

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
			self.characterDict = characterDict # Always overwrite
			if self.devId != 0 and self.devId in indigo.devices:
				dev = indigo.devices[self.devId]
		
				if "onState" in dir(dev) and "LockCurrentState" not in characterDict: characterDict["LockCurrentState"] = dev.onState
				if "onState" in dir(dev) and "LockTargetState" not in characterDict: characterDict["LockTargetState"] = dev.onState	
				
				definedActions = []
				for a in self.actions:
					definedActions.append (a["name"])
					
				if "LockTargetState" not in definedActions:
					self.actions.append (HomeKitAction("On", "equal", False, "device.turnOff", [self.devId]))
					self.actions.append (HomeKitAction("On", "equal", True, "device.turnOn", [self.devId]))

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
			
			self.required = ["On"]
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
			self.characterDict = characterDict # Always overwrite
			if self.devId != 0 and self.devId in indigo.devices:
				dev = indigo.devices[self.devId]
		
				if "onState" in dir(dev) and "On" not in characterDict: 
					characterDict["On"] = dev.onState	
				else:
					characterDict["On"] = False # Since all devices default to this type, this ensure that we never have NO characteristics
				
				definedActions = []
				for a in self.actions:
					definedActions.append (a["name"])
				
				if "On" not in definedActions:
					self.actions.append (HomeKitAction("On", "equal", False, "device.turnOff", [self.devId]))
					self.actions.append (HomeKitAction("On", "equal", True, "device.turnOn", [self.devId]))

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
# NAME
# ==============================================================================		
class characteristic_Name:
	def __init__(self):
		self.value = u""	
		
		self.readonly = False
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

