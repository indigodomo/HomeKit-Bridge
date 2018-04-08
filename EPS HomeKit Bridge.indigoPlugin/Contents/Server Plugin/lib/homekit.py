#! /usr/bin/env python
# -*- coding: utf-8 -*-

# lib.homekit - HomeKit integration via Homebridge-Indigo2
#
# Copyright (c) 2018 ColoradoFourWheeler / EPS
#

import indigo
import logging

import ext
import dtutil

import sys, inspect, json

HomeKitServiceList = []

class HomeKit:

	#
	# Initialize the class
	#
	def __init__ (self, factory):
		global HomeKitServiceList
		
		self.logger = logging.getLogger ("Plugin.homekit")
		self.factory = factory
		
		filename = indigo.server.getInstallFolderPath() + "/Plugins/EPS HomeKit Bridge.indigoPlugin/Contents/Server Plugin/services.json"
		file = open(filename)
		HomeKitServiceList = json.loads(file.read())
		file.close()
		
			
	#
	# This only gets run manually in code when new devices are added to facilitate the lookup needed for classes
	#
	def printClassLookupDict (self):
		try:
			clsmembers = inspect.getmembers(sys.modules[__name__], inspect.isclass)
			
			serviceList = "\n"

			d = "\n***\n## Services\n\n"
			
			d += "**Index**: [INDEX]\n\n***\n\n"
			index = ""

			for cls in clsmembers:
				if "service_" in cls[0]:
					index += "[{}](#{}) | ".format(cls[0].replace("service_", ""), cls[0].replace("service_", "").lower())
										
					d += "### {}\n\n".format(cls[0].replace("service_", ""))	
						
					cclass = cls[1]
					obj = cclass(self.factory, 0, 0, {}, [], True)
					
					serviceList += "* [{}](https://github.com/Colorado4Wheeler/HomeKit-Bridge/wiki/HomeKit-Model-Reference#{})\n".format(unicode(obj.desc), cls[0].replace("service_", "").lower())
					
					d += "**Device**: {}\n\n".format(unicode(obj.desc))

					if "wiki" in dir(obj): d += "**Notes**: {}\n\n".format(obj.wiki)
					
					requiredItems = ""
					optionalItems = ""
					values = ""
					
					if "required" in dir(obj): 
						for characteristic, getter in obj.required.iteritems():
							requiredItems += "[{}](#{}) | ".format(characteristic, characteristic.lower())
							
							values += "* {}: ".format(characteristic)
							if len(getter) > 0:
								for devtype, state in getter.iteritems():
									if "special_" in state:
										values += "**{}** ({}) | ".format("Calculated", state.replace("special_", "")) 
									else:
										values += "**{}** ({}) | ".format(state.replace("attr_", "").replace("state_", ""), devtype.replace("*", "all").replace("indigo.", "")) 
							else:
								values += "**TBD** | "
								
							values = values[0:len(values) - 3]	
							values += "\n"
						
						
					if len(requiredItems) > 0:
						requiredItems = requiredItems[0:len(requiredItems) - 3]
						
					d += "**Required**: {}\n\n".format(unicode(requiredItems))
					
					if "optional" in dir(obj): 
						for characteristic, getter in obj.optional.iteritems():
							optionalItems += "[{}](#{}) | ".format(characteristic, characteristic.lower())
							
							values += "* {}: ".format(characteristic)
							if len(getter) > 0:
								for devtype, state in getter.iteritems():
									if "special_" in state:
										values += "**{}** ({}) | ".format("Calculated", state.replace("special_", "")) 
									else:
										values += "**{}** ({}) | ".format(state.replace("attr_", "").replace("state_", ""), devtype.replace("*", "all").replace("indigo.", "")) 
							else:
								values += "**TBD** | "
								
							values = values[0:len(values) - 3]	
							values += "\n"
						
					if len(optionalItems) > 0:
						optionalItems = optionalItems[0:len(optionalItems) - 3]
					
					if len(optionalItems) > 0:	
						d += "**Optional**: {}\n\n".format(unicode(optionalItems))
					else:
						d += "**Optional**: None\n\n"
					
					d += "__Default Indigo Values__:\n\n{}\n\n***\n".format(values)
					
			index = index[0:len(index) - 3]
			d = d.replace("[INDEX]", index)
					
			d += "\n\n## Characteristics\n\n"
			
			d += "**Index**: [INDEX]\n\n***\n\n"
			index = ""	
			
			for cls in clsmembers:
				if "characteristic_" in cls[0]:
					index += "[{}](#{}) | ".format(cls[0].replace("characteristic_", ""), cls[0].replace("characteristic_", "").lower())
					
					d += "### {}\n\n".format(cls[0].replace("characteristic_", ""))
					
					cclass = cls[1]
					obj = cclass()
					
					if "value" in dir(obj):	d += "\tvalue = {}\n".format(unicode(obj.value))
					if "maxValue" in dir(obj):	d += "\tmaxValue = {}\n".format(unicode(obj.maxValue))
					if "minValue" in dir(obj):	d += "\tminValue = {}\n".format(unicode(obj.minValue))
					
					if "validValues" in dir(obj):	
						if "validValuesStr" in dir(obj):	
							d += "\tvalidValues = {} ({})\n".format(unicode(obj.validValues), unicode(obj.validValuesStr))
						else:
							d += "\tvalidValues = {}\n".format(unicode(obj.validValues))
					
					if "readonly" in dir(obj):	d += "\treadonly = {}\n".format(unicode(obj.readonly))
					if "notify" in dir(obj):	d += "\tnotify = {}\n".format(unicode(obj.notify))
										
					d += "\n\n***\n"
					#d += '"' + name.replace("characteristic_", "") + '": ' + name + ", "

			d += "\n"
			
			index = index[0:len(index) - 3]
			d = d.replace("[INDEX]", index)
			
			indigo.server.log(unicode(serviceList) + "\n\n\n\n\n\n")					
			indigo.server.log(unicode(d))
					
		except Exception as e:
			self.logger.error (ext.getException(e))		
		
	#
	# Either map to the requested service class or figure out what this devices should be autodetected as
	#
	def getServiceObject (self, objId, serverId = 0, serviceClass = None, autoDetect = False, loadOptional = False, characterDict = {}, deviceActions = []):
		try:
			# Get all classes in this module
			clsmembers = inspect.getmembers(sys.modules[__name__], inspect.isclass)
			serviceObj = None
			objId = int(objId) # Failsafe
			
			if serviceClass is None and autoDetect:
				serviceClass = self.detectHomeKitType (objId)
			
			# Find the class matching the name and instantiate the class
			for cls in clsmembers:
				if cls[0] == serviceClass:
					cclass = cls[1]
					serviceObj = cclass(self.factory, objId, serverId, characterDict, deviceActions, loadOptional)
					break
					
			if serviceObj is None: return None
			
			serviceObj = self._setIndigoDefaultValues (serviceObj)
			
			return serviceObj
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
	#
	# Return all service class names
	#
	def getHomeKitServices (self):
		try:
			classes = {}
			
			clsmembers = inspect.getmembers(sys.modules[__name__], inspect.isclass)
			for cls in clsmembers:
				if "service_" in cls[0]:
					cclass = cls[1]
					#factory, objId, characterDict = {}, deviceActions = [], loadOptional = False
					obj = cclass (self.factory, 0)
					classes[cls[0]] = obj.desc
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return classes
			
	#
	# Detect a HomeKit type from an Indigo type
	#
	def detectHomeKitType (self, objId):
		try:
			if objId in indigo.actionGroups:
				return "service_Switch"
				
			dev = indigo.devices[objId]
				
			if dev.pluginId == "com.perceptiveautomation.indigoplugin.zwave" and dev.deviceTypeId == "zwLockType":
				return "service_LockMechanism"
				
			if dev.pluginId == "com.perceptiveautomation.indigoplugin.airfoilpro" and dev.deviceTypeId == "speaker":
				return "service_Speaker"
				
			if dev.pluginId == "com.pennypacker.indigoplugin.senseme":
				return "service_Fanv2"		
				
			if dev.pluginId == "com.GlennNZ.indigoplugin.BlueIris" or dev.pluginId == "org.cynic.indigo.securityspy":
				return "service_CameraRTPStreamManagement"
			
			elif "brightnessLevel" in dev.states and "brightness" in dir(dev):
				return "service_Lightbulb"
			
			elif "Outlet" in dev.model:
				return "service_Outlet"
			
			elif "speedIndex" in dir(dev):
				return "service_Fanv2"
			
			elif "sensorInputs" in dir(dev):	
				if "protocol" in dir(dev) and unicode(dev.protocol) == "Insteon" and dev.model == "I/O-Linc Controller":
					return "service_GarageDoorOpener"
				
				else:
					return "service_GarageDoorOpener"
			
			elif "sensorValue" in dir(dev):
				if unicode(dev.protocol) == "Insteon" and "Motion Sensor" in dev.model: 
					return "service_MotionSensor"
					
				elif dev.pluginId == "com.perceptiveautomation.indigoplugin.zwave" and dev.deviceTypeId == "zwValueSensorType" and "LightSensor" in unicode(dev.displayStateImageSel):
					return "service_LightSensor"
					
				elif "Leak" in dev.model:
					return "service_LeakSensor"
					
				elif "Smoke" in dev.model:
					return "service_SmokeSensor"	
					
				elif "Humidity" in dev.model:
					return "service_HumiditySensor"	
				
				else:
					return "service_MotionSensor"
					
			elif "supportsCoolSetpoint" in dir(dev):
				return "service_Thermostat"
				
			elif "zoneCount" in dir(dev):
				return "service_IrrigationSystem"
				
				
			else:
				# Fallback but only if there is an onstate, otherwise we return an unknown
				if "onState" in dir(dev):
					return "service_Switch"
				else:
					self.logger.warning (u"{} is defaulting to a HomeKit switch because the device type cannot be determined but does not support On/Off and likely won't do anything in HomeKit".format(dev.name))
					return "service_Switch"
					#return "Dummy"
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
	
	
	
	
	################################################################################
	# DEVICE CONVERSIONS FROM INDIGO TO HOMEKIT
	################################################################################		
	#
	# Convert Indigo boolean to 0/1
	#
	def _homeKitBooleanAttribute (self, dev, attribute):
		try:
			curval = 0
			
			if attribute in dir(dev):
				obj = getattr (dev, attribute)
				if obj: 
					curval = 1
				else:
					curval = 0
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return curval
	
	#
	# Assign default values and actions for various device types
	#
	def _setIndigoDefaultValues (self, serviceObj):
		try:
			definedActions = []
			for a in serviceObj.actions:
				#definedActions.append (a["name"])
				definedActions.append (a.characteristic)
				
				
			if serviceObj.objId in indigo.actionGroups:
				# Always a switch object so set switch defaults
				if "On" not in serviceObj.characterDict: serviceObj.characterDict["On"] = False
				if "On" not in definedActions:
					serviceObj.actions.append (HomeKitAction("On", "equal", True, "actionGroup.execute", [serviceObj.objId], 0, {}))
										
				return serviceObj
						
			if serviceObj.objId not in indigo.devices: return
			
			dev = indigo.devices[serviceObj.objId]
				
			# Derive the service class to auto call the matching conversion function
			serviceClassName = str(type(serviceObj)).replace("<class 'lib.homekit.service_", "").replace("'>", "")
			if "_setIndigoDefaultValues_{}".format(serviceClassName) in dir(self):
				func = getattr (self, "_setIndigoDefaultValues_{}".format(serviceClassName))
				serviceObj =  func (serviceObj, definedActions, dev)
			
			return serviceObj
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return serviceObj
		
			
	#
	# Check for the presence of an attrib in indigo device and characteristic in the service and set the value if it's not been set
	#
	def _setServiceValueFromAttribute (self, serviceObj, dev, attribName, characteristic, value = None):
		try:
			if attribName in dir(dev) and characteristic not in serviceObj.characterDict: 
				if value is not None: 
					serviceObj.characterDict[characteristic] = value
				else:
					attrib = getattr (dev, attribName)
					serviceObj.characterDict[characteristic] = attrib
				
			return serviceObj		
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return serviceObj
		
	#
	# Check for the presence of a state in indigo device and characteristic in the service and set the value if it's not been set
	#
	def _setServiceValueFromState (self, serviceObj, dev, stateName, characteristic, value = None):
		try:
			if stateName in dev.states and characteristic not in serviceObj.characterDict: 
				if value is not None: 
					serviceObj.characterDict[characteristic] = value
				else:
					serviceObj.characterDict[characteristic] = dev.states[stateName]
				
			return serviceObj		
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return serviceObj	
		
	#
	# Auto convert temperature based on settings
	#
	def setTemperatureValue (self, serviceObj, value):
		try:
			if serviceObj.serverId != 0:
				server = indigo.devices[serviceObj.serverId]
				if "tempunits" in server.pluginProps:
					# If our source is celsius then that's what HomeKit wants, just return it
					if server.pluginProps["tempunits"] == "c": return value
					
					# If our source is fahrenheit then we need to convert it
					value = float(value)
					value = (value - 32) / 1.8000
					return round(value, 2)
					
					return (round(((value - 32.0) * 5.0 / 9.0) * 10.0) / 10.0)# - .5 # -1 to adjust it to be correct?
		
		except Exception as e:
			self.logger.error (ext.getException(e))		
			
	# ==============================================================================
	# FAN V2 DEFAULTS
	# ==============================================================================
	def _setIndigoDefaultValues_Fanv2xxx (self, serviceObj, definedActions, dev):	
		try:
			if type(dev) == indigo.SpeedControlDevice:
				serviceObj = self._setServiceValueFromAttribute (serviceObj, dev, "onState", "Active", self._homeKitBooleanAttribute (dev, "onState"))
				#serviceObj = self._setServiceValueFromAttribute (serviceObj, dev, "onState", "CurrentFanState", self._homeKitBooleanAttribute (dev, "onState") + 1)
				#serviceObj = self._setServiceValueFromAttribute (serviceObj, dev, "onState", "TargetFanState", 0) # Not supported
				serviceObj = self._setServiceValueFromAttribute (serviceObj, dev, "speedLevel", "RotationSpeed")
				
				if "Active" not in definedActions:
					serviceObj.actions.append (HomeKitAction("Active", "equal", 0, "device.turnOff", [serviceObj.objId], 0, {serviceObj.objId: "attr_onState"}))
					serviceObj.actions.append (HomeKitAction("Active", "equal", 1, "device.turnOn", [serviceObj.objId], 0, {serviceObj.objId: "attr_onState"}))
				
				if "RotationSpeed" not in definedActions:
					serviceObj.actions.append (HomeKitAction("RotationSpeed", "between", 0, "speedcontrol.setSpeedLevel", [serviceObj.objId, "=value="], 100, {serviceObj.objId: "attr_speedLevel"}))

			if type(dev) == indigo.ThermostatDevice:
				serviceObj = self._setServiceValueFromAttribute (serviceObj, dev, "fanIsOn", "Active", self._homeKitBooleanAttribute (dev, "fanIsOn"))
				#serviceObj = self._setServiceValueFromAttribute (serviceObj, dev, "fanIsOn", "CurrentFanState", self._homeKitBooleanAttribute (dev, "fanIsOn") + 1)
				#serviceObj = self._setServiceValueFromAttribute (serviceObj, dev, "fanIsOn", "TargetFanState", 0)
				
				#if "TargetFanState" not in definedActions:
				#	serviceObj.actions.append (HomeKitAction("TargetFanState", "equal", 0, "thermostat.setFanMode", [serviceObj.objId, indigo.kFanMode.Auto], 0, {serviceObj.objId: "attr_fanIsOn"}))
				#	serviceObj.actions.append (HomeKitAction("TargetFanState", "equal", 1, "thermostat.setFanMode", [serviceObj.objId, indigo.kFanMode.AlwaysOn], 0, {serviceObj.objId: "attr_fanMode"}))
				
				if "Active" not in definedActions:
					serviceObj.actions.append (HomeKitAction("Active", "equal", 0, "thermostat.setFanMode", [serviceObj.objId, indigo.kFanMode.Auto], 0, {serviceObj.objId: "attr_fanIsOn"}))
					serviceObj.actions.append (HomeKitAction("Active", "equal", 1, "thermostat.setFanMode", [serviceObj.objId, indigo.kFanMode.AlwaysOn], 0, {serviceObj.objId: "attr_fanMode"}))
				
			if type(dev) == indigo.RelayDevice:
				serviceObj = self._setServiceValueFromAttribute (serviceObj, dev, "onState", "Active", self._homeKitBooleanAttribute (dev, "onState"))
				#serviceObj = self._setServiceValueFromAttribute (serviceObj, dev, "onState", "CurrentFanState", self._homeKitBooleanAttribute (dev, "onState") + 1)
				#serviceObj = self._setServiceValueFromAttribute (serviceObj, dev, "onState", "TargetFanState", 1)
				
				if "Active" not in definedActions:
					serviceObj.actions.append (HomeKitAction("Active", "equal", 0, "device.turnOff", [serviceObj.objId], 0, {serviceObj.objId: "attr_onState"}))
					serviceObj.actions.append (HomeKitAction("Active", "equal", 1, "device.turnOn", [serviceObj.objId], 0, {serviceObj.objId: "attr_onState"}))

			if type(dev) == indigo.DimmerDevice:
				serviceObj = self._setServiceValueFromAttribute (serviceObj, dev, "onState", "Active", self._homeKitBooleanAttribute (dev, "onState"))
				serviceObj = self._setServiceValueFromAttribute (serviceObj, dev, "brightness", "RotationSpeed")
				
				if "Active" not in definedActions:
					serviceObj.actions.append (HomeKitAction("Active", "equal", 0, "device.turnOff", [serviceObj.objId], 0, {serviceObj.objId: "attr_onState"}))
					serviceObj.actions.append (HomeKitAction("Active", "equal", 1, "device.turnOn", [serviceObj.objId], 0, {serviceObj.objId: "attr_onState"}))

				if "RotationSpeed" not in definedActions:
					serviceObj.actions.append (HomeKitAction("RotationSpeed", "between", 0, "dimmer.setBrightness", [serviceObj.objId, "=value="], 100, {serviceObj.objId: "attr_brightness"}))


			return serviceObj
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return serviceObj		
			
	# ==============================================================================
	# GARAGE DOOR OPENER DEFAULTS
	# ==============================================================================
	def _setIndigoDefaultValues_GarageDoorOpenerxxx (self, serviceObj, definedActions, dev):	
		try:
			# Insteon Multi I/O controller
			if "protocol" in dir(dev) and unicode(dev.protocol) == "Insteon" and dev.model == "I/O-Linc Controller":
				if "binaryInput1" in dev.states and "CurrentDoorState" not in serviceObj.characterDict: 
					serviceObj.characterDict["CurrentDoorState"] = 1 # Open
					if not dev.states["binaryInput1"]: serviceObj.characterDict["CurrentDoorState"] = 0 # Closed
					
				if "binaryInput1" in dev.states and "TargetDoorState" not in serviceObj.characterDict: 
					serviceObj.characterDict["TargetDoorState"] = 1 # Open
					if not dev.states["binaryInput1"]: serviceObj.characterDict["TargetDoorState"] = 0 # Closed	
					
				if "ObstructionDetected" not in serviceObj.characterDict: serviceObj.characterDict["ObstructionDetected"] = False # Unsupported but it's required right now
			
				#if "CurrentDoorState" not in definedActions:
				#	serviceObj.actions.append (HomeKitAction("CurrentDoorState", "equal", 0, "iodevice.setBinaryOutput", [serviceObj.objId, 1, True], 0, {serviceObj.objId: "state_binaryInput1"}))
				#	serviceObj.actions.append (HomeKitAction("CurrentDoorState", "equal", 1, "iodevice.setBinaryOutput", [serviceObj.objId, 1, True], 0, {serviceObj.objId: "state_binaryInput1"}))
					
				if "TargetDoorState" not in definedActions:
					serviceObj.actions.append (HomeKitAction("TargetDoorState", "equal", 0, "iodevice.setBinaryOutput", [serviceObj.objId, 0, True], 0, {serviceObj.objId: "state_binaryInput1"}))
					serviceObj.actions.append (HomeKitAction("TargetDoorState", "equal", 1, "iodevice.setBinaryOutput", [serviceObj.objId, 0, True], 0, {serviceObj.objId: "state_binaryInput1"}))	
		
			return serviceObj
		
		except Exception as e:
			serviceObj.logger.error (ext.getException(e))	
			return serviceObj			
						
			
	# ==============================================================================
	# LIGHTBULB DEFAULTS
	# ==============================================================================
	def _setIndigoDefaultValues_Lightbulbxxx (self, serviceObj, definedActions, dev):	
		try:
			serviceObj = self._setServiceValueFromAttribute (serviceObj, dev, "onState", "On")
			serviceObj = self._setServiceValueFromAttribute (serviceObj, dev, "brightness", "Brightness")
			
			if "On" not in definedActions:
				serviceObj.actions.append (HomeKitAction("On", "equal", False, "device.turnOff", [serviceObj.objId], 0, {serviceObj.objId: "attr_onState"}))
				serviceObj.actions.append (HomeKitAction("On", "equal", True, "device.turnOn", [serviceObj.objId], 0, {serviceObj.objId: "attr_onState"}))
				
			if "Brightness" not in definedActions:
				serviceObj.actions.append (HomeKitAction("Brightness", "between", 0, "dimmer.setBrightness", [serviceObj.objId, "=value="], 100, {serviceObj.objId: "attr_brightness"}))
	
			return serviceObj
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return serviceObj	
			
	# ==============================================================================
	# MOTION SENSOR DEFAULTS
	# ==============================================================================
	def _setIndigoDefaultValues_MotionSensorxxx (self, serviceObj, definedActions, dev):	
		try:
			serviceObj = self._setServiceValueFromAttribute (serviceObj, dev, "onState", "MotionDetected")
			
			if "batteryLevel" in dir(dev) and dev.batteryLevel is not None: 
				serviceObj.characterDict["StatusLowBattery"] = 0
				
				if "lowbattery" in self.factory.plugin.pluginPrefs:
					lowbattery = int(self.factory.plugin.pluginPrefs["lowbattery"])
					if lowbattery > 0: lowbattery = lowbattery / 100
					
					if dev.batteryLevel < ((100 * lowbattery) + 1): serviceObj.characterDict["StatusLowBattery"] = 1
					
			# Special consideration for Fibaro sensors that fill up a couple more Characteristics (if this grows we may need to call a function for these)
			if "model" in dir(dev) and "FGMS001" in dev.model:
				# See if we can find all the devices with this Zwave ID
				for idev in indigo.devices.iter("com.perceptiveautomation.indigoplugin.zwave.zwOnOffSensorType"):
					if idev.address == dev.address:
						# Same Fibaro model
						if "Tilt/Tamper" in idev.subModel:
							serviceObj.characterDict["StatusTampered"] = 0
							if idev.onState: serviceObj.characterDict["StatusTampered"] = 1
							
							# Make sure this gets added to our watch list
							serviceObj.actions.append (HomeKitAction("StatusTampered", "equal", False, "device.turnOff", [idev.id], 0, {idev.id: "attr_onState"}))
						
			
			# This is a read only device so it'll never need this but it must be here so when we get activity for this device we can tell
			# homekit to update, if this isn't here it'll never know that attr_onState should trigger an HK update
			serviceObj.actions.append (HomeKitAction("MotionDetected", "equal", False, "device.turnOff", [serviceObj.objId], 0, {serviceObj.objId: "attr_onState"}))
			serviceObj.actions.append (HomeKitAction("StatusLowBattery", "equal", False, "device.turnOff", [serviceObj.objId], 0, {serviceObj.objId: "attr_batteryLevel"}))
				
			return serviceObj
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return serviceObj		
			
	# ==============================================================================
	# OUTLET DEFAULTS
	# ==============================================================================
	def _setIndigoDefaultValues_Outletxxx (self, serviceObj, definedActions, dev):	
		try:
			serviceObj = self._setServiceValueFromAttribute (serviceObj, dev, "onState", "On")
			serviceObj = self._setServiceValueFromAttribute (serviceObj, dev, "onState", "OutletInUse")
			
			if "On" not in definedActions:
				serviceObj.actions.append (HomeKitAction("On", "equal", False, "device.turnOff", [serviceObj.objId], 0, {serviceObj.objId: "attr_onState"}))
				serviceObj.actions.append (HomeKitAction("On", "equal", True, "device.turnOn", [serviceObj.objId], 0, {serviceObj.objId: "attr_onState"}))
			
			return serviceObj
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return serviceObj	
			
	# ==============================================================================
	# LOCK MECHANISM DEFAULTS
	# ==============================================================================
	def _setIndigoDefaultValues_LockMechanismxxx (self, serviceObj, definedActions, dev):	
		try:
			serviceObj = self._setServiceValueFromAttribute (serviceObj, dev, "onState", "LockCurrentState", self._homeKitBooleanAttribute (dev, "onState"))
			serviceObj = self._setServiceValueFromAttribute (serviceObj, dev, "onState", "LockTargetState", self._homeKitBooleanAttribute (dev, "onState"))
			
			if "LockTargetState" not in definedActions:
				serviceObj.actions.append (HomeKitAction("LockTargetState", "equal", 0, "device.turnOff", [serviceObj.objId], 0, {serviceObj.objId: "attr_onState"}))
				serviceObj.actions.append (HomeKitAction("LockTargetState", "equal", 1, "device.turnOn", [serviceObj.objId], 0, {serviceObj.objId: "attr_onState"}))
			
			return serviceObj
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return serviceObj								
			
	# ==============================================================================
	# SWITCH DEFAULTS
	# ==============================================================================
	def _setIndigoDefaultValues_Switchxxx (self, serviceObj, definedActions, dev):	
		try:
			if "onState" in dir(dev) and "On" not in serviceObj.characterDict: 
				serviceObj.characterDict["On"] = dev.onState	
			else:
				serviceObj.characterDict["On"] = False # Since all devices default to this type, this ensure that we never have NO characteristics
			
			if "On" not in definedActions:
				serviceObj.actions.append (HomeKitAction("On", "equal", False, "device.turnOff", [serviceObj.objId], 0, {serviceObj.objId: "attr_onState"}))
				serviceObj.actions.append (HomeKitAction("On", "equal", True, "device.turnOn", [serviceObj.objId], 0, {serviceObj.objId: "attr_onState"}))

			return serviceObj
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return serviceObj		

	# ==============================================================================
	# THERMOSTAT DEFAULTS
	# ==============================================================================
	def _setIndigoDefaultValues_Thermostatxxx (self, serviceObj, definedActions, dev):	
		try:
			targettemp = 0
			
			if "TemperatureDisplayUnits" not in serviceObj.characterDict and serviceObj.serverId != 0:
				server = indigo.devices[serviceObj.serverId]
				if "tempunits" in server.pluginProps:
					if server.pluginProps["tempunits"] == "c":
						serviceObj.characterDict["TemperatureDisplayUnits"] = 0
					else:
						serviceObj.characterDict["TemperatureDisplayUnits"] = 1
						
				else:
					serviceObj.characterDict["TemperatureDisplayUnits"] = 0						
		
			serviceObj = self._setServiceValueFromAttribute (serviceObj, dev, "hvacMode", "CurrentHeatingCoolingState")
			if "CurrentHeatingCoolingState" in serviceObj.characterDict: 
				if str(serviceObj.characterDict["CurrentHeatingCoolingState"]) == "Heat": # Standard Indigo thermostat
					serviceObj.characterDict["CurrentHeatingCoolingState"] = 1
				elif str(serviceObj.characterDict["CurrentHeatingCoolingState"]) == "Cool": 
					serviceObj.characterDict["CurrentHeatingCoolingState"] = 2
				else:
					serviceObj.characterDict["CurrentHeatingCoolingState"] = 0 # Off
					
			if "TargetHeatingCoolingState" not in serviceObj.characterDict and "CurrentHeatingCoolingState" in serviceObj.characterDict: serviceObj.characterDict["TargetHeatingCoolingState"] = serviceObj.characterDict["CurrentHeatingCoolingState"]
			
			#serviceObj = self._setServiceValueFromAttribute (serviceObj, dev, "onState", "TargetHeatingCoolingState", self._homeKitBooleanAttribute (dev, "onState"))
			serviceObj = self._setServiceValueFromState (serviceObj, dev, "temperatureInput1", "CurrentTemperature", self.setTemperatureValue(serviceObj, dev.states["temperatureInput1"]))
			
			if "CurrentHeatingCoolingState" in serviceObj.characterDict and serviceObj.characterDict["CurrentHeatingCoolingState"] == 2: 
				serviceObj = self._setServiceValueFromAttribute (serviceObj, dev, "coolSetpoint", "TargetTemperature", self.setTemperatureValue(serviceObj, dev.coolSetpoint))
			else:
				serviceObj = self._setServiceValueFromAttribute (serviceObj, dev, "heatSetpoint", "TargetTemperature", self.setTemperatureValue(serviceObj, dev.heatSetpoint))
			
			serviceObj = self._setServiceValueFromState (serviceObj, dev, "humidityInput1", "CurrentRelativeHumidity")
			#serviceObj = self._setServiceValueFromState (serviceObj, dev, "humidityInput1", "TargetRelativeHumidity") # Only if they can set humidity
			#serviceObj = self._setServiceValueFromAttribute (serviceObj, dev, "coolSetpoint", "CoolingThresholdTemperature", self.setTemperatureValue(serviceObj, dev.coolSetpoint))
			#serviceObj = self._setServiceValueFromAttribute (serviceObj, dev, "heatSetpoint", "HeatingThresholdTemperature", self.setTemperatureValue(serviceObj, dev.heatSetpoint))
			
			if "TargetTemperature" not in definedActions:
				serviceObj.actions.append (HomeKitAction("TargetTemperature", "between", 0.0, "homekit.commandSetTargetThermostatTemperature", [serviceObj.objId, serviceObj.serverId, "=value="], 100.0, {serviceObj.objId: "attr_coolSetpoint"}))
			
			if "TargetHeatingCoolingState" not in definedActions: # Using various states/attribs for watching instead of using stubs since we have 4 of these
				serviceObj.actions.append (HomeKitAction("TargetHeatingCoolingState", "equal", 0, "thermostat.setHvacMode", [serviceObj.objId, indigo.kHvacMode.Off], 0, {serviceObj.objId: "attr_heatSetpoint"}))
				serviceObj.actions.append (HomeKitAction("TargetHeatingCoolingState", "equal", 1, "thermostat.setHvacMode", [serviceObj.objId, indigo.kHvacMode.Heat], 0, {serviceObj.objId: "state_temperatureInput1"}))
				serviceObj.actions.append (HomeKitAction("TargetHeatingCoolingState", "equal", 2, "thermostat.setHvacMode", [serviceObj.objId, indigo.kHvacMode.Cool], 0, {serviceObj.objId: "state_humidityInput1"}))
				serviceObj.actions.append (HomeKitAction("TargetHeatingCoolingState", "equal", 3, "thermostat.setHvacMode", [serviceObj.objId, indigo.kHvacMode.HeatCool], 0, {serviceObj.objId: "attr_hvacMode"}))

			

			# Stubs so we monitor for state changes
			#serviceObj.actions.append (HomeKitAction("STUB", "equal", True, "NULL", [serviceObj.objId], 0, {serviceObj.objId: "attr_heatSetpoint"}))
			#serviceObj.actions.append (HomeKitAction("STUB", "equal", True, "NULL", [serviceObj.objId], 0, {serviceObj.objId: "state_temperatureInput1"}))
			#serviceObj.actions.append (HomeKitAction("STUB", "equal", True, "NULL", [serviceObj.objId], 0, {serviceObj.objId: "state_humidityInput1"}))
			#serviceObj.actions.append (HomeKitAction("STUB", "equal", True, "NULL", [serviceObj.objId], 0, {serviceObj.objId: "attr_hvacMode"}))
			
			return serviceObj
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return serviceObj			

################################################################################
# BASE SERVICE CLASS THAT ALL SERVICE CLASSES INHERIT
#
# Handles all functionality for each service type
################################################################################
class Service (object):

	#
	# Initialize the class (Won't happen unless called from child)
	#
	def __init__ (self, factory, hktype, desc, objId, serverId, deviceCharacteristics, deviceActions, loadOptional):
		global HomeKitServiceList
		
		self.logger = logging.getLogger ("Plugin.HomeKit.Service." + hktype)
		self.factory = factory
		
		try:
			self.type = hktype
			self.desc = desc
			self.objId = objId
			self.required = {}
			self.optional = {}
			self.native = True # Functions can map directly to Indigo or a plugin (see requiresPlugin) natively without any customization
			self.requiresPlugin = [] # For this device to work Indigo must have one or more plugins installed
			self.actions = []	
			self.characterDict = {}
			self.loadOptional = loadOptional # Create attributes for the optional fields
			self.serverId = serverId
			self.indigoType = "Unable to detect"
			self.pluginType = "Built-In"
			self.invertOnState = False # This is set by the HTTP utility during processing if the user passed it in the stash
			self.convertFahrenheit = False # This is set by the HTTP utility during processing if the user passes it in the stash
			
			# For timer baseed operations
			self.recurringUpdate = False # When true, the API will schedule a thread to refresh every X seconds
			self.recurringSeconds = 0


			self.jsoninit = False # Just while we are dialing in the JSON dict file, this needs to be removed when we convert all HK types to the new method

			
			# Get the indigo class for this object
			if objId in indigo.devices:
				#indigo.server.log("adding device type {}".format(indigo.devices[objId].name))
				self.indigoType = str(type(indigo.devices[objId])).replace("<class '", "").replace("'>", "")
				if indigo.devices[objId].pluginId != "":
					self.pluginType = self.indigoType + "." + indigo.devices[objId].pluginId + "." + indigo.devices[objId].deviceTypeId
			elif objId in indigo.actionGroups:
				self.indigoType = "indigo.actionGroup"
			
			# We have to append from here, if we were to set self.actions equal an outside list it would share among all instances of this class
			for d in deviceActions:
				self.actions.append (d)
		
			for k, v in deviceCharacteristics.iteritems():
				self.characterDict[k] = v
			
			self.deviceInitialize()
			
			if self.type in HomeKitServiceList:
				self.loadJSONDictData()
			else:
				#self.logger.error (u"HomeKit service '{}' should have been in the dictionary but wasn't, control of this kind of device is impossible and errors will occur!".format(self.type))
				pass
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
	def loadJSONDictData (self):
		global HomeKitServiceList
		
		return # Until ready to release
		
		try:
			self.logger.info (u"HomeKit service '{}' loaded".format(self.type))
			
			#self.required["ContactSensorState"] = {"*": "special_invertedOnState", "indigo.ThermostatDevice": "attr_fanIsOn", "indigo.MultiIODevice": "state_binaryOutput1", "indigo.SprinklerDevice": "activeZone", "indigo.Device.com.eps.indigoplugin.device-extensions.epsdecon": "state_convertedBoolean", "indigo.Device.com.frightideas.indigoplugin.dscAlarm.alarmZone": "state_state.open"}
			
			# Try to load the service definitions from HomeKitServiceList
			service = HomeKitServiceList[self.type]
			for characteristic, charprops in service["characteristics"].iteritems():
				characterDict = {}
				
				for objdev, objprops in charprops["objects"].iteritems():
					for objpropname, objgetters in objprops.iteritems():
						if objpropname != "setters": characterDict[objdev] = objpropname
										
				if charprops["required"]:
					self.required[characteristic] = characterDict
				else:
					self.optional[characteristic] = characterDict
			
			# Lastly set this if all went well and we are done
			self.jsoninit = True
			
			indigo.server.log(unicode(self.required))
			indigo.server.log(unicode(self.optional))
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
	def __str__ (self):
		ret = ""
		
		ret += "Service : \n"
		
		ret += "\talias : {0}\n".format(self.alias.value)
		ret += "\tmodel : {0}\n".format(self.model.value)
		ret += "\tsubModel : {0}\n".format(self.subModel.value)
		ret += "\tindigoType : {0}\n".format(self.indigoType)
		ret += "\tpluginType : {0}\n".format(self.pluginType)
		
		ret += "\ttype : {0}\n".format(self.type)
		ret += "\tdesc : {0}\n".format(self.desc)
		ret += "\tobjId : {0}\n".format(unicode(self.objId))
		ret += "\tserverId : {0}\n".format(unicode(self.serverId))
		
		ret += "\tinvertOnState : {0}\n".format(unicode(self.invertOnState))
		ret += "\tconvertFahrenheit : {0}\n".format(unicode(self.convertFahrenheit))

		ret += "\trequired : (List)\n"
		for i in self.required:
			if i in dir(self):
				obj = getattr(self, i)
				ret += "\t\t{0} : {1}\n".format(i, unicode(obj.value))
			else:
				ret += "\t\t{0}\n".format(i)

		
		ret += "\toptional : (List)\n"
		for i in self.optional:
			if i in dir(self):
				obj = getattr(self, i)
				ret += "\t\t{0} : {1}\n".format(i, unicode(obj.value))
			else:
				ret += "\t\t{0}\n".format(i)
		
		ret += "\tnative : {0}\n".format(unicode(self.native))
		
		ret += "\trequiresPlugin : (List)\n"
		for i in self.requiresPlugin:
			ret += "\t\t{0}\n".format(i)
		
		ret += "\tactions : (List)\n"
		for i in self.actions:
			ret += "\t\tAction : (HomeKitAction)\n"
			ret += "\t\t\tCharacteristic : {0}\n".format(i.characteristic)
			ret += "\t\t\tWhen : {0}\n".format(i.whenvalueis)
			ret += "\t\t\tValue : {0} ({1})\n".format(unicode(i.whenvalue), str(type(i.whenvalue)).replace("<type '", "").replace("'>", "") )
			ret += "\t\t\tValue2 : {0} ({1})\n".format(unicode(i.whenvalue2), str(type(i.whenvalue)).replace("<type '", "").replace("'>", ""))
			ret += "\t\t\tCommand : {0}\n".format(unicode(i.command))
			ret += "\t\t\tArguments : {0}\n".format(unicode(i.arguments))
			ret += "\t\t\tmonitors : {0}\n".format(unicode(i.monitors))
		
		ret += "\tloadOptional : {0}\n".format(unicode(self.loadOptional))
		
		ret += "\tcharacterDict : (Dict)\n"
		for i, v in self.characterDict.iteritems():
			ret += "\t\t{0} : {1}\n".format(i, unicode(v))
		
		return ret		
			
	#
	# Device startup to set various attributes
	#
	def deviceInitialize (self):
		try:
			self.model = characteristic_Name()
			self.subModel = characteristic_Name()
			self.alias = characteristic_Name()
			
			if self.objId == 0: 
				self.alias.value = "Invalid Indigo Object"
				return
			
			if self.objId in indigo.devices: 
				obj = indigo.devices[self.objId]
				self.model.value = unicode(obj.model)
				self.model.value = unicode(obj.subModel)
				
			if self.objId in indigo.actionGroups: 
				obj = indigo.actionGroups[self.objId]
				self.model.value = "Action Group"
			
			self.alias = characteristic_Name()
			self.alias.value = unicode(obj.name)
			
			# While we are here if we have a server and an object then we can pull the stash
			r = self.getStashRecordForObject()
			if not r is None:
				if "invert" in r and r["invert"]: self.invertOnState = True
				if "tempIsF" in r and r["tempIsF"]: self.convertFahrenheit = True

			
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
	#
	# Find a device in a server stash and return the record
	#
	def getStashRecordForObject (self):
		try:
			if self.serverId != 0 and self.objId != 0 and self.serverId in indigo.devices:
				serverProps = indigo.devices[self.serverId].pluginProps
				includedDevices = json.loads(serverProps["includedDevices"])
				includedActions = json.loads(serverProps["includedActions"])
				
				r = self.factory.jstash.getRecordWithFieldEquals (includedDevices, "id", self.objId)
				if r is None: r = self.factory.jstash.getRecordWithFieldEquals (includedActions, "id", self.objId)
				return r		
				
		except Exception as e:
			e.args += (u"Server Id: {}".format(self.serverId),)
			if self.serverId != 0: e.args += (u"Server data: {}".format(unicode(indigo.devices[self.serverId].pluginProps)),)
			self.logger.error (ext.getException(e))
						
		return None	
	
	#
	# Set device attributes from the required and optional parameters
	#
	def setAttributesXXX (self):
		try:
			# Build a list of all classes in this module and turn it into a dict for lookup
			clsmembers = inspect.getmembers(sys.modules[__name__], inspect.isclass)
			classes = {}
			for cls in clsmembers:
				classes[cls[0]] = cls[1]

			# Add all required characteristics
			for a in self.required:
				classname = "characteristic_{}".format(a)
				if classname in classes:
					self.logger.threaddebug (u"Adding {} attribute to {}".format(a, self.alias.value))
					cclass = classes[classname]
					setattr (self, a, cclass())
					
			# Add optional characteristics if they were added by the call or if the loadOptional was set as true
			for a in self.optional:
				if a in self.characterDict or self.loadOptional:
					classname = "characteristic_{}".format(a)
					if classname in classes:
						self.logger.threaddebug (u"Adding {} attribute to {}".format(a, self.alias.value))
						cclass = classes[classname]
						setattr (self, a, cclass())
						
			# If they passed values then use them, this also lets us audit to ensure no rogue values that don't apply get weeded out
			for key, value in self.characterDict.iteritems():
				if key in dir(self):
					self.setAttributeValue (key, value)
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
	#
	# Set device attributes from the required and optional parameters
	#
	def setAttributes (self):
		global HomeKitServiceList
		
		try:
			# Use the previous method for actions since it handles it well
			if self.indigoType == "indigo.actionGroup": 
				# All action groups are switches, period, never anything else regardless of what someone may call them
				setattr (self, "On", characteristic_On())
				if "On" not in self.characterDict: self.characterDict["On"] = False
				if "On" not in self.actions:
					self.actions.append (HomeKitAction("On", "equal", True, "actionGroup.execute", [self.objId], 0, {}))
					
				return
				
			if self.objId == 0: return # We'll error out all over the place when we do fake instantiation for getting service defaults
			
			# Build a list of all classes in this module and turn it into a dict for lookup
			clsmembers = inspect.getmembers(sys.modules[__name__], inspect.isclass)
			classes = {}
			for cls in clsmembers:
				classes[cls[0]] = cls[1]
				
			# Add all required characteristics
			self.detCharacteristicValues (classes, self.required)
			
			# Add all optional characteristics
			self.detCharacteristicValues (classes, self.optional, True)
					
			
		except Exception as e:
			self.logger.error (ext.getException(e))		
			
	#
	# Set device attribute from service definition fields
	#
	def detCharacteristicValues (self, classes, sourceDict, isOptional = False):
		try:
			for characteristic, getters in sourceDict.iteritems():
				# While working on this, back out if there's no type
				if "indigoType" not in dir(self): 
					return
				
				# See if this type is in the getters
				getter = None
				if self.pluginType in getters:
					getter = getters[self.pluginType]
				elif self.indigoType in getters:
					getter = getters[self.indigoType]
				elif "*" in getters:
					getter = getters["*"]
					
				#indigo.server.log ("{}: {} is {}".format(self.alias.value, characteristic, getter))
				#if getter is None: indigo.server.log ("{}: {}".format(self.alias.value, self.pluginType))
					
				if getter is None: 
					if isOptional: 
						continue # Nothing to do
					else:
						getter =  "attr_STUB" # we MUST pass all required items, so force this through the works and we'll continue out after it creates our attribute
				
				# See if this characteristic can get a value at all
				hasvalue = False
				if getter[0:5] == "attr_":
					if getter.replace("attr_", "") in dir(indigo.devices[self.objId]): hasvalue = True
					
				if getter[0:6] == "state_":
					obj = indigo.devices[self.objId]
					if "states" in dir(obj) and getter.replace("state_", "") in obj.states: hasvalue = True
					
				if getter[0:8] == "special_":
					hasvalue = True # Always force these through
					
				# Exit now if it's optional fields and we dont want them
				if isOptional:
					if characteristic in self.characterDict or self.loadOptional or hasvalue:
						pass
					else:
						return
			
				# Create the characteristic as an attribute
				classname = "characteristic_{}".format(characteristic)
				if classname in classes:
					if not characteristic in dir(self):
						self.logger.threaddebug (u"Adding {} attribute to {}".format(characteristic, self.alias.value))
						cclass = classes[classname]
						setattr (self, characteristic, cclass())
						
					else:
						# Using the cache, remove the characteristic so it will repopulate on refreshes
						if characteristic in self.characterDict: del(self.characterDict[characteristic])
					
					if getter == "attr_STUB":
						# Add the default value to the characterdict so it passes through to the API and then exit out
						if characteristic not in self.characterDict: self.characterDict[characteristic] = getattr (self, characteristic).value
						continue
					
				if getter[0:5] == "attr_":
					if getter.replace("attr_", "") in dir(indigo.devices[self.objId]): 
						obj = indigo.devices[self.objId]
						obj = getattr (obj, getter.replace("attr_", ""))
						
						self.setAttributeValue (characteristic, obj)
						if characteristic not in self.characterDict: self.characterDict[characteristic] = getattr (self, characteristic).value
						
						#indigo.server.log ("Alias: {} | Invert: {} | Getter: {}".format(self.alias.value, unicode(self.invertOnState), getter))
						if self.invertOnState and getter == "attr_onState": # In case we are reversing AND this is the onState attribute
							self.logger.threaddebug (u"Inverting {}".format(self.alias.value))
							if getattr (self, characteristic).value:
								self.setAttributeValue (characteristic, False) # Make true false
							else:
								self.setAttributeValue (characteristic, True) # Make false true
							
							# If we don't set the characterDict value then it won't show in the API
							self.characterDict[characteristic] = getattr (self, characteristic).value
						
						# Since we are here we can calculate the actions needed to change this attribute
						self.calculateDefaultActionsForAttribute (getter.replace("attr_", ""), characteristic)
						
				elif getter[0:6] == "state_":
					obj = indigo.devices[self.objId]
					if "states" in dir(obj) and getter.replace("state_", "") in obj.states: 
						if "states" in dir(obj) and getter.replace("state_", "") in obj.states:
							self.setAttributeValue (characteristic, obj.states[getter.replace("state_", "")])
							if characteristic not in self.characterDict: self.characterDict[characteristic] = getattr (self, characteristic).value
							
							#if obj.id == 624004987: indigo.server.log("{} Set to {} adjusted to {}".format(getter, unicode(obj.states[getter.replace("state_", "")]), unicode(getattr (self, characteristic).value)  ))
							
							# Since we are here we can calculate the actions needed to change this attribute
							self.calculateDefaultActionsForState (getter.replace("state_", ""), characteristic)
						
				# SPECIAL DIRECTIVES	
				else:
					if getter in dir(self):
						obj = getattr (self, getter)
						obj (classes, sourceDict, getter, characteristic, isOptional)		
						
		except Exception as e:
			self.logger.error (ext.getException(e) + "\nFor object id {} alias '{}'".format(str(self.objId), self.alias.value))		



			
	#
	# Calculate default actions based on the attribute value that is being changed
	#
	def calculateDefaultActionsForAttribute (self, attrib, characteristic):
		try:
			if characteristic in self.actions: return # The user has passed their own actions
			if characteristic not in dir(self): return # We need to reference the details, it should have been created by now
			
			a = getattr (self, characteristic)
			invalidType = False
			
			#if a.readonly: 
			#	self.logger.threaddebug (u"Not setting a default action for {} because that characteristic is read only".format(characteristic))
			#	return # There are no actions for readonly characteristics, why add unnecessary data?
			
			# Define some defaults
			minValue = 0
			maxValue = 100
			minStep = 1
			trueValue = True
			falseValue = False
			method = "UNKNOWN"
			if "minValue" in dir(a): minValue = a.minValue
			if "maxValue" in dir(a): maxValue = a.maxValue
			if "minStep" in dir(a): minStep = a.minStep
			
			# Determine which data method the characteristic is using (T/F, 0/1, Range)
			if type(a.value) == bool:
				method = "TF"
				
			elif "validValues" in dir(a) and len(a.validValues) == 2:
				method = "01"
				trueValue = 1
				falseValue = 0
								
			elif "validValues" in dir(a) and len(a.validValues) > 2:
				method = "RANGE"
				
			elif "validValues" not in dir(a) and "minValue" in dir(a):
				method = "RANGE"
			
			# MOST DEVICES
			if attrib == "onState":	
				if self.invertOnState:
					self.logger.debug (u"Inverting the action for characteristic {} on '{}'".format(characteristic, self.alias.value))
					# This attribute is the only thing impacted by this setting but it means we have to reverse the commands because the characteristic
					# value was reversed in HomeKit.  We need to remove all default actions because they will be replaced here and if we don't we'll end up
					# appending the regular and inverted commands together
					newactions = []
					for a in self.actions:
						if a.characteristic != characteristic: newactions.append(a)
						
						# The following line was what it started as so that if there was a user overrride (i.e., plugin or complications) then
						# those would not be purged but that means that each iteration of this function would only put in THIS characteristic,
						# which was fine for onState but if there are multiple states that can be changed then they now all get purged if the
						# device is inverted (i.e., issue #
						#if not a.default: newactions.append(a)
						
					self.actions = newactions
					
					
					if method == "TF" or method == "01":	
						self.actions.append (HomeKitAction(characteristic, "equal", falseValue, "device.turnOn", [self.objId], 0, {self.objId: "attr_onState"}))
						self.actions.append (HomeKitAction(characteristic, "equal", trueValue, "device.turnOff", [self.objId], 0, {self.objId: "attr_onState"}))
		
					elif method == "RANGE":
						self.actions.append (HomeKitAction(characteristic, "equal", minValue, "device.turnOn", [self.objId], 0, {self.objId: "attr_onState"}))
						self.actions.append (HomeKitAction(characteristic, "between", minValue + minStep, "device.turnOff", [self.objId], maxValue, {self.objId: "attr_onState"}))	
					
					else:
						invalidType = True
					
				else:				
					if method == "TF" or method == "01":			
						self.actions.append (HomeKitAction(characteristic, "equal", falseValue, "device.turnOff", [self.objId], 0, {self.objId: "attr_onState"}))
						self.actions.append (HomeKitAction(characteristic, "equal", trueValue, "device.turnOn", [self.objId], 0, {self.objId: "attr_onState"}))
		
					elif method == "RANGE":
						self.actions.append (HomeKitAction(characteristic, "equal", minValue, "device.turnOff", [self.objId], 0, {self.objId: "attr_onState"}))
						self.actions.append (HomeKitAction(characteristic, "between", minValue + minStep, "device.turnOn", [self.objId], maxValue, {self.objId: "attr_onState"}))	
					
					else:
						invalidType = True
			
			# DIMMERS
			elif attrib == "brightness":
				cmd = "dimmer.setBrightness"
				if method == "TF" or method == "01":		
					self.actions.append (HomeKitAction(characteristic, "equal", falseValue, cmd, [self.objId, 0], 0, {self.objId: "attr_brightness"}))
					self.actions.append (HomeKitAction(characteristic, "equal", trueValue, cmd, [self.objId, 100], 0, {self.objId: "attr_brightness"}))
			
				elif method == "RANGE":
					self.actions.append (HomeKitAction(characteristic, "between", minValue, cmd, [self.objId, "=value="], maxValue, {self.objId: "attr_brightness"}))
				
				else:
					invalidType = True
			
			# SPEED CONTROL	
			elif attrib == "speedLevel":
				cmd = "speedcontrol.setSpeedLevel"
				if method == "TF" or method == "01":		
					self.actions.append (HomeKitAction(characteristic, "equal", falseValue, cmd, [self.objId, 0], 0, {self.objId: "attr_speedLevel"}))
					self.actions.append (HomeKitAction(characteristic, "equal", trueValue, cmd, [self.objId, 100], 0, {self.objId: "attr_speedLevel"}))
				
				elif method == "RANGE":	
					self.actions.append (HomeKitAction(characteristic, "between", minValue, cmd, [self.objId, "=value="], maxValue, {self.objId: "attr_speedLevel"}))	
				
				else:
					invalidType = True
					
			# SENSORS
			elif attrib == "sensorValue":
				cmd = "speedcontrol.setSpeedLevel"
				# Nothing to do, this is almost always read-only but here we can trigger change orders
				self.actions.append (HomeKitAction(characteristic, "between", minValue, cmd, [self.objId, "=value="], maxValue, {self.objId: "attr_sensorValue"}))	
			
			# THERMOSTAT	
			elif attrib == "fanIsOn":
				cmd = "thermostat.setFanMode"
				if method == "TF" or method == "01":	
					self.actions.append (HomeKitAction(characteristic, "equal", falseValue, cmd, [self.objId, indigo.kFanMode.Auto], 0, {self.objId: "attr_fanIsOn"}))
					self.actions.append (HomeKitAction(characteristic, "equal", trueValue, cmd, [self.objId, indigo.kFanMode.AlwaysOn], 0, {self.objId: "attr_fanMode"}))
				
				elif method == "RANGE":	
					self.actions.append (HomeKitAction(characteristic, "equal", 0, cmd, [self.objId, indigo.kFanMode.Auto], 0, {self.objId: "attr_fanIsOn"}))
					self.actions.append (HomeKitAction(characteristic, "between", minValue, cmd, [self.objId, indigo.kFanMode.AlwaysOn], maxValue, {self.objId: "attr_fanMode"}))	
				
				else:
					invalidType = True
			
			elif attrib == "coolSetpoint":
				cmd = "thermostat.setFanMode"
				if method == "RANGE":	
					self.actions.append (HomeKitAction(characteristic, "between", 0.0, "homekit.commandSetTargetThermostatCooling", [self.objId, self.serverId, "=value="], 100.0, {self.objId: "attr_coolSetpoint"}))						
				else:
					invalidType = True
					
			elif attrib == "heatSetpoint":
				cmd = "thermostat.setFanMode"
				if method == "RANGE":	
					self.actions.append (HomeKitAction(characteristic, "between", 0.0, "homekit.commandSetTargetThermostatHeating", [self.objId, self.serverId, "=value="], 100.0, {self.objId: "attr_coolSetpoint"}))						
				else:
					invalidType = True		
			
					
			else:
				# Whatever else, if we didn't specify it, will get a dummy action associated with it and it could cause errors if the characteristic is
				# not read-only, but we need this so the plugin will monitor for any changes to the attribute
				self.actions.append (HomeKitAction(characteristic, "equal", "STUB", "STUB", [self.objId, 0], 0, {self.objId: "attr_" + attrib}))
						
			if invalidType:
				self.logger.warning (u"Unable to create default action for {} attribute '{}', the characteristic '{}' data type is {} and we can't translate to that from '{}'".format(self.alias.value, attrib, characteristic, str(type(a.value)).replace("<type '", "").replace("'>", ""), attrib))
				return
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
	#
	# Calculate default actions based on the attribute value that is being changed
	#
	def calculateDefaultActionsForState (self, state, characteristic):
		try:
			if characteristic in self.actions: return # The user has passed their own actions
			if characteristic not in dir(self): return # We need to reference the details, it should have been created by now
			
			a = getattr (self, characteristic)
			invalidType = False
			
			if a.readonly: 
				self.logger.threaddebug (u"Not setting a default action for {} because that characteristic is read only".format(characteristic))
				self.actions.append (HomeKitAction(characteristic, "equal", "STUB", "STUB", [self.objId, 0], 0, {self.objId: "state_" + state}))
				return # There are no actions for readonly characteristics, why add unnecessary data?
			
			# Define some defaults
			minValue = 0
			maxValue = 100
			minStep = 1
			trueValue = True
			falseValue = False
			method = "UNKNOWN"
			if "minValue" in dir(a): minValue = a.minValue
			if "maxValue" in dir(a): maxValue = a.maxValue
			if "minStep" in dir(a): minStep = a.minStep
			
			# Determine which data method the characteristic is using (T/F, 0/1, Range)
			if type(a.value) == bool:
				method = "TF"
				
			elif "validValues" in dir(a) and len(a.validValues) == 2:
				method = "01"
				trueValue = 1
				falseValue = 0
								
			elif "validValues" in dir(a) and len(a.validValues) > 2:
				method = "RANGE"
				
			elif "validValues" not in dir(a) and "minValue" in dir(a):
				method = "RANGE"
			
			# MULTI-I/O (INPUTOUTPUT)	
			if state == "binaryOutput1":
				# NOTE: This is really only tuned to the garage door use of this, actual other uses of this will probably not work using this config since
				# we use only one command "turn on output" which is what we need to do to both open and close a garage door.  If users need more function
				# then we'll have to move some or all of this to the functions instead so we can do some tweaking
				
				cmd = "iodevice.setBinaryOutput"
				if method == "TF" or method == "01":	
					self.actions.append (HomeKitAction(characteristic, "equal", falseValue, cmd, [self.objId, 0, True], 0, {self.objId: "state_binaryOutput1"}))
					self.actions.append (HomeKitAction(characteristic, "equal", trueValue, cmd, [self.objId, 0, True], 0, {self.objId: "state_binaryOutput1"}))
				
				elif method == "RANGE":	
					self.actions.append (HomeKitAction(characteristic, "equal", minValue, cmd, [self.objId, 0, True], 0, {self.objId: "state_binaryOutput1"}))
					self.actions.append (HomeKitAction(characteristic, "between", minValue + minStep, cmd, [self.objId, 0, True], maxValue, {self.objId: "state_binaryOutput1"}))	
				
				else:
					invalidType = True
					
			elif state == "binaryInput1":
				# NOTE: This is really only tuned to the garage door use of this, actual other uses of this will probably not work using this config since
				# we use only one command "turn on output" which is what we need to do to both open and close a garage door.  If users need more function
				# then we'll have to move some or all of this to the functions instead so we can do some tweaking
				
				cmd = "iodevice.setBinaryOutput"
				if method == "TF" or method == "01":	
					self.actions.append (HomeKitAction(characteristic, "equal", falseValue, cmd, [self.objId, 0, True], 0, {self.objId: "state_binaryInput1"}))
					self.actions.append (HomeKitAction(characteristic, "equal", trueValue, cmd, [self.objId, 0, True], 0, {self.objId: "state_binaryInput1"}))
				
				elif method == "RANGE":	
					self.actions.append (HomeKitAction(characteristic, "equal", minValue, cmd, [self.objId, 0, True], 0, {self.objId: "state_binaryInput1"}))
					self.actions.append (HomeKitAction(characteristic, "between", minValue + minStep, cmd, [self.objId, 0, True], maxValue, {self.objId: "state_binaryInput1"}))	
				
				else:
					invalidType = True
					
			# Airfoil Speakers (perhaps Sonos, don't have the plugin so don't know)
			elif state == "status.disconnected": # Speaker or Microphone Control turing MUTE on and off (reversed state)
				cmd = "homekit.runPluginAction"
				
				if method == "TF" or method == "01":	
					self.actions.append (HomeKitAction(characteristic, "equal", falseValue, cmd, [indigo.devices[self.objId].pluginId, "=value=", ["connect", self.objId]], 0, {self.objId: "state_status.disconnected"}))
					self.actions.append (HomeKitAction(characteristic, "equal", trueValue, cmd, [indigo.devices[self.objId].pluginId, "=value=", ["disconnect", self.objId]], 0, {self.objId: "state_status.disconnected"}))
			
				elif method == "RANGE":	
					self.actions.append (HomeKitAction(characteristic, "equal", minValue, cmd, [indigo.devices[self.objId].pluginId, "=value=", ["disconnect", self.objId]], 0, {self.objId: "state_status.disconnected"}))
					self.actions.append (HomeKitAction(characteristic, "between", minValue + minStep, cmd, [indigo.devices[self.objId].pluginId, "=value=", ["connect", self.objId]], maxValue, {self.objId: "state_status.disconnected"}))	
			
				else:
					invalidType = True		

			elif state == "status.connected": # Lightbulb Control turing CONNECT on and off (opposite of normal speaker/microphone control)
				cmd = "homekit.runPluginAction"
				if method == "TF" or method == "01":	
					self.actions.append (HomeKitAction(characteristic, "equal", falseValue, cmd, [indigo.devices[self.objId].pluginId, "=value=", ["disconnect", self.objId]], 0, {self.objId: "state_status.disconnected"}))
					self.actions.append (HomeKitAction(characteristic, "equal", trueValue, cmd, [indigo.devices[self.objId].pluginId, "=value=", ["connect", self.objId]], 0, {self.objId: "state_status.disconnected"}))
			
				elif method == "RANGE":	
					self.actions.append (HomeKitAction(characteristic, "equal", minValue, cmd, [indigo.devices[self.objId].pluginId, "=value=", ["connect", self.objId]], 0, {self.objId: "state_status.disconnected"}))
					self.actions.append (HomeKitAction(characteristic, "between", minValue + minStep, cmd, [indigo.devices[self.objId].pluginId, "=value=", ["disconnect", self.objId]], maxValue, {self.objId: "state_status.disconnected"}))	
			
				else:
					invalidType = True		

					
			elif state == "volume":
				cmd = "homekit.runPluginAction"
				if method == "TF" or method == "01":	
					self.actions.append (HomeKitAction(characteristic, "equal", falseValue, cmd, [indigo.devices[self.objId].pluginId, "=value=", ["setVolume", self.objId, {'volume': 0}]], 0, {self.objId: "state_volume"}))
					self.actions.append (HomeKitAction(characteristic, "equal", trueValue, cmd, [indigo.devices[self.objId].pluginId, "=value=", ["setVolume", self.objId, {'volume': 50}]], 0, {self.objId: "state_volume"}))
				
				elif method == "RANGE":	
					self.actions.append (HomeKitAction(characteristic, "between", minValue, cmd, [indigo.devices[self.objId].pluginId, "=value=", ["setVolume", self.objId, {'volume': "=value="}]], maxValue, {self.objId: "state_volume"}))	
				
				else:
					invalidType = True
					
			elif state == "activeZone":
				cmd = "sprinkler.setActiveZone"
				if method == "TF" or method == "01":	
					self.actions.append (HomeKitAction(characteristic, "equal", falseValue, cmd, [self.objId, 0], 0, {self.objId: "state_activeZone"}))
					self.actions.append (HomeKitAction(characteristic, "equal", trueValue, cmd, [self.objId, 1], 0, {self.objId: "state_activeZone"}))
				
				elif method == "RANGE":	
					self.actions.append (HomeKitAction(characteristic, "equal", minValue, cmd, [self.objId, "=value="], 0, {self.objId: "state_activeZone"}))
					self.actions.append (HomeKitAction(characteristic, "between", minValue + minStep, cmd, [self.objId, "=value="], maxValue, {self.objId: "state_activeZone"}))	
				
				else:
					invalidType = True	
					
					
			# Hue Bulbs		
			elif state == "hue":
				cmd = "homekit.runPluginAction"
				
				obj = indigo.devices[self.objId]
				
				# Replicate the values using all the current device values for anything but this and the form default values for everything else
				valuesDict = {'rgbColor': "=", 'hue': "=value=", 'saturation': obj.states['saturation'], 'brightnessSource': 'custom', 'brightness': obj.brightness, 'useRateVariable': False, 'rate': 0, 'rateVariable':  '', 'rampRateLabel': 0}
				
				if method == "RANGE":	
				
					self.actions.append (HomeKitAction(characteristic, "equal", minValue, cmd, [indigo.devices[self.objId].pluginId, "=value=", ["setHSB", self.objId, valuesDict]], 0, {self.objId: "state_hue"}))
					self.actions.append (HomeKitAction(characteristic, "between", minValue + minStep, cmd, [indigo.devices[self.objId].pluginId, "=value=", ["setHSB", self.objId, valuesDict]], maxValue, {self.objId: "state_hue"}))	
				
				else:
					invalidType = True
					
			elif state == "saturation":
				cmd = "homekit.runPluginAction"
				
				obj = indigo.devices[self.objId]
				
				# Replicate the values using all the current device values for anything but this and the form default values for everything else
				valuesDict = {'rgbColor': "=", 'hue': obj.states['hue'], 'saturation': '=value=', 'brightnessSource': 'custom', 'brightness': obj.brightness, 'useRateVariable': False, 'rate': 0, 'rateVariable':  '', 'rampRateLabel': 0}
				
				if method == "RANGE":	
				
					self.actions.append (HomeKitAction(characteristic, "equal", minValue, cmd, [indigo.devices[self.objId].pluginId, "=value=", ["setHSB", self.objId, valuesDict]], 0, {self.objId: "state_hue"}))
					self.actions.append (HomeKitAction(characteristic, "between", minValue + minStep, cmd, [indigo.devices[self.objId].pluginId, "=value=", ["setHSB", self.objId, valuesDict]], maxValue, {self.objId: "state_hue"}))	
				
				else:
					invalidType = True		
					
			elif state == "brightness":
				cmd = "homekit.runPluginAction"
				
				obj = indigo.devices[self.objId]
				
				# Replicate the values using all the current device values for anything but this and the form default values for everything else
				valuesDict = {'rgbColor': "=", 'hue': obj.states['hue'], 'saturation': obj.states['saturation'], 'brightnessSource': 'custom', 'brightness': '=value=', 'useRateVariable': False, 'rate': 0, 'rateVariable':  '', 'rampRateLabel': 0}
				
				if method == "RANGE":	
				
					self.actions.append (HomeKitAction(characteristic, "equal", minValue, cmd, [indigo.devices[self.objId].pluginId, "=value=", ["setHSB", self.objId, valuesDict]], 0, {self.objId: "state_hue"}))
					self.actions.append (HomeKitAction(characteristic, "between", minValue + minStep, cmd, [indigo.devices[self.objId].pluginId, "=value=", ["setHSB", self.objId, valuesDict]], maxValue, {self.objId: "state_hue"}))	
				
				else:
					invalidType = True	
					
			elif state == "colorTemp":
				cmd = "homekit.runPluginAction"
				
				obj = indigo.devices[self.objId]
				
				# Replicate the values using all the current device values for anything but this and the form default values for everything else
				valuesDict = {'preset': "relax", 'temperatureSource': 'custom', 'temperature': "=value=", 'brightnessSource': 'custom', 'brightness': obj.brightness, 'useRateVariable': False, 'rate': 0, 'rateVariable':  '', 'rampRateLabel': 0}
				
				if method == "RANGE":	
				
					self.actions.append (HomeKitAction(characteristic, "equal", minValue, cmd, [indigo.devices[self.objId].pluginId, "=value=", ["setCT", self.objId, valuesDict]], 0, {self.objId: "state_hue"}))
					self.actions.append (HomeKitAction(characteristic, "between", minValue + minStep, cmd, [indigo.devices[self.objId].pluginId, "=value=", ["setCT", self.objId, valuesDict]], maxValue, {self.objId: "state_hue"}))	
				
				else:
					invalidType = True	
					
			# LIFX Bulbs		
			elif state == "hsbkHue":
				cmd = "homekit.runPluginAction"
				
				obj = indigo.devices[self.objId]
				
				# Replicate the values using all the current device values for anything but this and the form default values for everything else
				#valuesDictColor = {'actionType':'Standard', 'modeStandard':'Color', 'hueStandard': obj.states['hsbkHue'], 'saturationStandard': obj.states['hsbkSaturation'], 'brightnessStandard':obj.brightness, 'durationStandard':1.0 }
				#valuesDictWhite = {'actionType':'Standard', 'modeStandard':'White', 'kelvinStandard': obj.states['hsbkKelvin'], 'brightnessStandard':obj.brightness, 'durationStandard':1.0 })
				
				valuesDictColor = {'actionType':'Standard', 'modeStandard':'Color', 'hueStandard': "=value=", 'saturationStandard': obj.states['hsbkSaturation'], 'brightnessStandard':obj.brightness, 'durationStandard':1.0 }
				valuesDictWhite = {'actionType':'Standard', 'modeStandard':'White', 'kelvinStandard': 9000, 'brightnessStandard':obj.brightness, 'durationStandard':1.0 }
								
				if method == "RANGE":	
				
					self.actions.append (HomeKitAction(characteristic, "equal", minValue, cmd, [indigo.devices[self.objId].pluginId, "=value=", ["setColorWhite", self.objId, valuesDictWhite]], 0, {self.objId: "state_hsbkHue"}))
					self.actions.append (HomeKitAction(characteristic, "between", minValue + minStep, cmd, [indigo.devices[self.objId].pluginId, "=value=", ["setColorWhite", self.objId, valuesDictColor]], maxValue, {self.objId: "state_hsbkHue"}))	
				
				else:
					invalidType = True
					
			elif state == "hsbkSaturation":
				cmd = "homekit.runPluginAction"
				
				obj = indigo.devices[self.objId]
				
				valuesDictColor = {'actionType':'Standard', 'modeStandard':'Color', 'hueStandard': obj.states['hsbkHue'], 'saturationStandard': "=value=", 'brightnessStandard':obj.brightness, 'durationStandard':1.0 }
				valuesDictWhite = {'actionType':'Standard', 'modeStandard':'White', 'kelvinStandard': obj.states['hsbkKelvin'], 'brightnessStandard':obj.brightness, 'durationStandard':1.0 }
								
				if method == "RANGE":	
				
					self.actions.append (HomeKitAction(characteristic, "equal", minValue, cmd, [indigo.devices[self.objId].pluginId, "=value=", ["setColorWhite", self.objId, valuesDictWhite]], 0, {self.objId: "state_hsbkSaturation"}))
					self.actions.append (HomeKitAction(characteristic, "between", minValue + minStep, cmd, [indigo.devices[self.objId].pluginId, "=value=", ["setColorWhite", self.objId, valuesDictColor]], maxValue, {self.objId: "state_hsbkSaturation"}))	

				else:
					invalidType = True		
					
			elif state == "hsbkKelvin":
				cmd = "homekit.runPluginAction"
				
				obj = indigo.devices[self.objId]
				
				valuesDictColor = {'actionType':'Standard', 'modeStandard':'Color', 'hueStandard': obj.states['hsbkHue'], 'saturationStandard': obj.states['hsbkSaturation'], 'brightnessStandard':obj.brightness, 'durationStandard':1.0 }
				valuesDictWhite = {'actionType':'Standard', 'modeStandard':'White', 'kelvinStandard': "=value=", 'brightnessStandard':obj.brightness, 'durationStandard':1.0 }
				
				if method == "RANGE":	
				
					self.actions.append (HomeKitAction(characteristic, "equal", minValue, cmd, [indigo.devices[self.objId].pluginId, "=value=", ["setColorWhite", self.objId, valuesDictWhite]], 0, {self.objId: "state_hsbkKelvin"}))
					self.actions.append (HomeKitAction(characteristic, "between", minValue + minStep, cmd, [indigo.devices[self.objId].pluginId, "=value=", ["setColorWhite", self.objId, valuesDictColor]], maxValue, {self.objId: "state_hsbkKelvin"}))	

				else:
					invalidType = True	
			
			# SecuritySpy
			elif state == "recording":
				cmd = "homekit.runPluginAction"
				
				if method == "TF" or method == "01":	
					self.actions.append (HomeKitAction(characteristic, "equal", trueValue, cmd, [indigo.devices[self.objId].pluginId, "=value=", ["setactive", self.objId]], 0, {self.objId: "state_recording"}))
					self.actions.append (HomeKitAction(characteristic, "equal", falseValue, cmd, [indigo.devices[self.objId].pluginId, "=value=", ["setpassive", self.objId]], 0, {self.objId: "state_recording"}))
				
				elif method == "RANGE":	
					self.actions.append (HomeKitAction(characteristic, "equal", minValue, cmd, [indigo.devices[self.objId].pluginId, "=value=", ["setactive", self.objId]], 0, {self.objId: "state_recording"}))
					self.actions.append (HomeKitAction(characteristic, "between", minValue + minStep, cmd, [indigo.devices[self.objId].pluginId, "=value=", ["setpassive", self.objId]], maxValue, {self.objId: "state_recording"}))	
				
				else:
					invalidType = True									
					
			else:
				# Whatever else, if we didn't specify it, will get a dummy action associated with it and it could cause errors if the characteristic is
				# not read-only, but we need this so the plugin will monitor for any changes to the state
				self.actions.append (HomeKitAction(characteristic, "equal", "STUB", "STUB", [self.objId, 0], 0, {self.objId: "state_" + state}))
			
				
		
			if invalidType:
				self.logger.warning (u"Unable to create default action for {} attribute '{}', the characteristic '{}' data type is {} and we can't translate to that from '{}'".format(self.alias.value, attrib, characteristic, str(type(a.value)).replace("<type '", "").replace("'>", ""), attrib))
				return
				
			#state_binaryOutput1
			
			
		except Exception as e:
			self.logger.error (ext.getException(e))				
			
	#
	# All devices point back to here to set an attribute value so we can do calculations and keep everything uniform across devices (and less coding)
	#	
	def setAttributeValue (self, attribute, value):
		try:
			ret = True
		
			if not attribute in dir(self):
				self.logger.error (u"Cannot set {} value of {} because it is not an attribute".format(attribute, dev.Alias.value))
				return False
			
			obj = getattr (self, attribute)	
	
			if type(value) == type(obj.value):
				obj.value = value
				#indigo.server.log ("Set {} to {}".format(attribute, unicode(value)))
			else:
				# Try to do a basic conversion if possible
				vtype = str(type(value)).replace("<type '", "").replace("'>", "")
				atype = str(type(obj.value)).replace("<type '", "").replace("'>", "")
				
				self.logger.threaddebug (u"Converting value type of {} to charateristic type of {} for {}".format(vtype, atype, attribute))
				#if self.objId == 624004987: self.logger.info (u"Converting value type of {} to charateristic type of {} for {}".format(vtype, atype, attribute))
			
				converted = False
				if vtype == "NoneType":
					if atype == "float": obj.value = 0.0
					if atype == "int": obj.value = 0
					if atype == "bool": obj.value = False
					converted = True					
					
				if vtype == "bool": converted = self.convertFromBoolean (attribute, value, atype, vtype, obj)
				if vtype == "str" and atype == "unicode":
					obj.value = value
					converted = True
				if vtype == "int" and atype == "float":
					obj.value = float(value)
					converted = True
				if vtype == "float" and atype == "int":
					obj.value = int(round(value))
					converted = True
			
				if not converted:
					self.logger.warning (u"Unable to set the value of {} on {} to {} because that attribute requires {} and it was given {}".format(attribute, self.alias.value, unicode(value), atype, vtype))
					return False
					
					
			# Now that we have made sure the value type matches, make sure it conforms to the min/max/valid values
			if type(value) != bool and type(value) != str and type(value) != unicode:
				#if "minValue" in dir(obj) and obj.value < obj.minValue: obj.value = obj.minValue
				#if "maxValue" in dir(obj) and obj.value > obj.maxValue: obj.value = obj.maxValue
				pass
				
			# Special min/max adjustment for SenseMe fans
			if self.pluginType == "indigo.Device.com.pennypacker.indigoplugin.senseme.SenseME_fan":
				if attribute == "Brightness":
					self.Brightness.minValue = 0
					self.Brightness.maxValue = 16
				if attribute == "RotationSpeed":
					self.RotationSpeed.minValue = 0
					self.RotationSpeed.maxValue = 7
	
			# Do temperature conversion on the value
			if attribute in ["CurrentTemperature", "TargetTemperature", "HeatingThresholdTemperature", "CoolingThresholdTemperature"]:
				if self.convertFahrenheit:
					try:
						cvalue = float(obj.value)
						cvalue = (cvalue - 32) / 1.8000
						if cvalue < 0: cvalue = 0
						obj.value = cvalue
					except:
						pass # Nothing happened, leave the current value
	
		except Exception as e:
			self.logger.error (ext.getException(e))	
			ret = False
		
		return ret			
		
	#
	# Convert from boolean
	#
	def convertFromBoolean (self, attribute, value, atype, vtype, obj):
		try:
			newvalue = None
	
			# Convert to integer
			if atype == "int":
				if value: newvalue = 1
				if not value: newvalue = 0
		
			elif atype == "str":
				if value: newvalue = "true"
				if not value: newvalue = "false"	
				
			else:
				self.logger.warning (u"Unable to convert from {} to {}".format(vtype, atype))
		
			if "validValues" in dir(obj) and newvalue in obj.validValues: 
				obj.value = newvalue
				return True
		
			elif "validValues" in dir(obj) and newvalue not in obj.validValues: 
				indigo.server.log("Converted {} for {} from {} to {} but the coverted value of {} was not a valid value for this attribute and will not be accepted by HomeKit, it will remain at the current value of {}".format(attribute, dev.Alias.value, vtype, atype, unicode(newvalue), unicode(obj.value)))
				return False
			
			obj.value = newvalue	
			return True
	
		except Exception as e:
			self.logger.error (ext.getException(e))	
	
		return False		
		
	################################################################################
	# SPECIAL ACTIONS
	################################################################################		
	#
	# Check if a device's battery level is below the configured threshold
	#
	def special_lowbattery (self, classes, sourceDict, getter, characteristic, isOptional = False):
		try:
			obj = indigo.devices[self.objId]
			if "batteryLevel" in dir(obj) and "lowbattery" in self.factory.plugin.pluginPrefs:
				# If it's set to None then we really don't have battery levels and can skip this all
				if obj.batteryLevel is not None:
					lowbattery = int(self.factory.plugin.pluginPrefs["lowbattery"])
					if lowbattery > 0: lowbattery = lowbattery / 100
					if obj.batteryLevel < ((100 * lowbattery) + 1): 
						self.setAttributeValue (characteristic, 1)
						self.characterDict[characteristic] = getattr (self, characteristic).value
					else:
						self.setAttributeValue (characteristic, 0)
						self.characterDict[characteristic] = getattr (self, characteristic).value
					
					# So we get notified of any changes, add a trigger for this in actions, it won't do anything other than monitor
					self.actions.append (HomeKitAction(characteristic, "equal", False, "device.turnOff", [self.objId], 0, {self.objId: "attr_batteryLevel"}))
			
		
		except Exception as e:
			self.logger.error (ext.getException(e) + "\nFor object id {} alias '{}'".format(str(self.objId), self.alias.value))	
			
	#
	# DEVICE EXTENSIONS: Replace Filter
	#
	def special_deReplaceFilter	 (self, classes, sourceDict, getter, characteristic, isOptional = False):
		try:
			obj = indigo.devices[self.objId]
			if "sensorValue" in dir(obj) and obj.sensorValue is not None:
				self.setAttributeValue (characteristic, 1)
				self.characterDict[characteristic] = getattr (self, characteristic).value
				
				self.actions.append (HomeKitAction(characteristic, "between", 0, "homekit.runPluginAction", [indigo.devices[self.objId].pluginId, None, ["filterSensorChange", self.objId]], 100, {self.objId: "attr_sensorValue"}))		
		
		except Exception as e:
			self.logger.error (ext.getException(e) + "\nFor object id {} alias '{}'".format(str(self.objId), self.alias.value))		

	#
	# Check if an outlet is in use by looking at its power consumption
	#
	def special_inuse (self, classes, sourceDict, getter, characteristic, isOptional = False):
		try:
			obj = indigo.devices[self.objId]
			if "energyCurLevel" in dir(obj) and obj.energyCurLevel is not None:
				# It supports energy reporting
				if obj.energyCurLevel > 0:
					self.setAttributeValue (characteristic, True)
					self.characterDict[characteristic] = getattr (self, characteristic).value
				else:
					self.setAttributeValue (characteristic, False)
					self.characterDict[characteristic] = getattr (self, characteristic).value
			else:
				if "onState" in dir(obj) and obj.onState:
					self.setAttributeValue (characteristic, True)
					self.characterDict[characteristic] = getattr (self, characteristic).value
				else:
					self.setAttributeValue (characteristic, False)
					self.characterDict[characteristic] = getattr (self, characteristic).value
		
		except Exception as e:
			self.logger.error (ext.getException(e) + "\nFor object id {} alias '{}'".format(str(self.objId), self.alias.value))	


	#
	# Invert the on/off state of an onState attribute
	#
	def special_invertedOnState (self, classes, sourceDict, getter, characteristic, isOptional = False):
		try:
			obj = indigo.devices[self.objId]
			if "onState" in dir(obj):
				if not self.invertOnState:
					if obj.onState:
						self.setAttributeValue (characteristic, False)
						self.characterDict[characteristic] = getattr (self, characteristic).value 
					else:
						self.setAttributeValue (characteristic, True)
						self.characterDict[characteristic] = getattr (self, characteristic).value
				else:
					if not obj.onState:
						self.setAttributeValue (characteristic, False)
						self.characterDict[characteristic] = getattr (self, characteristic).value 
					else:
						self.setAttributeValue (characteristic, True)
						self.characterDict[characteristic] = getattr (self, characteristic).value
						
			else:
				self.setAttributeValue (characteristic, False)
				self.characterDict[characteristic] = getattr (self, characteristic).value
				
			if not self.invertOnState:
				self.actions.append (HomeKitAction(characteristic, "equal", False, "device.turnOn", [self.objId], 0, {self.objId: "attr_onState"}))
				self.actions.append (HomeKitAction(characteristic, "between", True, "device.turnOff", [self.objId], 100, {self.objId: "attr_onState"}))
			else:
				self.actions.append (HomeKitAction(characteristic, "equal", True, "device.turnOn", [self.objId], 0, {self.objId: "attr_onState"}))
				self.actions.append (HomeKitAction(characteristic, "between", False, "device.turnOff", [self.objId], 100, {self.objId: "attr_onState"}))
		
		except Exception as e:
			self.logger.error (ext.getException(e) + "\nFor object id {} alias '{}'".format(str(self.objId), self.alias.value))	
			
	#
	# Use an onState boolean value and convert to 1 or 100 for brightness devices
	#
	def special_onStateToFullBrightness (self, classes, sourceDict, getter, characteristic, isOptional = False):
		try:
			obj = indigo.devices[self.objId]
			
			onValue = 100
			offValue = 0
			
			if self.invertOnState:
				onValue = 0
				offValue = 100
			
			if "onState" in dir(obj):
				if obj.onState:
					self.setAttributeValue (characteristic, onValue)
					self.characterDict[characteristic] = getattr (self, characteristic).value
				else:
					self.setAttributeValue (characteristic, offValue)
					self.characterDict[characteristic] = getattr (self, characteristic).value
			else:
				self.setAttributeValue (characteristic, offValue)
				self.characterDict[characteristic] = getattr (self, characteristic).value 
				
			if self.invertOnState:	
				# Remove all default actions or we'll end up just appending these on top and they won't get fired
				newactions = []
				for a in self.actions:
					if not a.default: newactions.append(a)
					
				self.actions = newactions
					
				self.actions.append (HomeKitAction(characteristic, "equal", 0, "device.turnOn", [self.objId], 0, {self.objId: "attr_onState"}))
				self.actions.append (HomeKitAction(characteristic, "between", 1, "device.turnOff", [self.objId], 100, {self.objId: "attr_onState"}))
			else:
				self.actions.append (HomeKitAction(characteristic, "equal", 0, "device.turnOff", [self.objId], 0, {self.objId: "attr_onState"}))
				self.actions.append (HomeKitAction(characteristic, "between", 1, "device.turnOn", [self.objId], 100, {self.objId: "attr_onState"}))
		
		except Exception as e:
			self.logger.error (ext.getException(e) + "\nFor object id {} alias '{}'".format(str(self.objId), self.alias.value))				

	#
	# Pi Beacon Status
	#
	def special_piBeaconStatus (self, classes, sourceDict, getter, characteristic, isOptional = False):
		try:
			obj = indigo.devices[self.objId]
			
			if "status" in obj.states and obj.states["status"].lower() == "up":
				self.setAttributeValue (characteristic, True) # Heating
				self.characterDict[characteristic] = getattr (self, characteristic).value
			else:
				self.setAttributeValue (characteristic, False) # Off
				self.characterDict[characteristic] = getattr (self, characteristic).value
			
			self.actions.append (HomeKitAction(characteristic, "equal", 0, "STUB", [self.objId, indigo.kHvacMode.Off], 0, {self.objId: "state_status"}))
		
		except Exception as e:
			self.logger.error (ext.getException(e) + "\nFor object id {} alias '{}'".format(str(self.objId), self.alias.value))	

	#
	# Nest HVAC mode
	#
	def special_nestHvacMode (self, classes, sourceDict, getter, characteristic, isOptional = False):
		try:
			obj = indigo.devices[self.objId]
			
			if "isheating" in obj.states and obj.states["isheating"].lower() == "yes":
				self.setAttributeValue (characteristic, 1) # Heating
				self.characterDict[characteristic] = getattr (self, characteristic).value
			elif "iscooling" in obj.states and obj.states["iscooling"].lower() == "yes":
				self.setAttributeValue (characteristic, 2) # Cooling
				self.characterDict[characteristic] = getattr (self, characteristic).value
			else:
				self.setAttributeValue (characteristic, 0) # Off
				self.characterDict[characteristic] = getattr (self, characteristic).value
			
			self.actions.append (HomeKitAction(characteristic, "equal", 0, "STUB", [self.objId, indigo.kHvacMode.Off], 0, {self.objId: "state_isheating"}))
			self.actions.append (HomeKitAction(characteristic, "equal", 0, "STUB", [self.objId, indigo.kHvacMode.Off], 0, {self.objId: "state_iscooling"}))
		
		except Exception as e:
			self.logger.error (ext.getException(e) + "\nFor object id {} alias '{}'".format(str(self.objId), self.alias.value))	
			

	#
	# Thermostat HVAC mode
	#
	def special_thermHVACMode (self, classes, sourceDict, getter, characteristic, isOptional = False):
		try:
			obj = indigo.devices[self.objId]
			
			if "heatIsOn" in dir(obj) and obj.heatIsOn:
				self.setAttributeValue (characteristic, 1) # Heating
				self.characterDict[characteristic] = getattr (self, characteristic).value
			elif "heatIsOn" in dir(obj) and obj.coolIsOn:
				self.setAttributeValue (characteristic, 2) # Cooling
				self.characterDict[characteristic] = getattr (self, characteristic).value
			else:
				self.setAttributeValue (characteristic, 0) # Off
				self.characterDict[characteristic] = getattr (self, characteristic).value
			
			self.actions.append (HomeKitAction(characteristic, "equal", 0, "STUB", [self.objId, indigo.kHvacMode.Off], 0, {self.objId: "attr_heatIsOn"}))
			self.actions.append (HomeKitAction(characteristic, "equal", 0, "STUB", [self.objId, indigo.kHvacMode.Off], 0, {self.objId: "attr_coolIsOn"}))
		
		except Exception as e:
			self.logger.error (ext.getException(e) + "\nFor object id {} alias '{}'".format(str(self.objId), self.alias.value))	
			
			
	#
	# Thermostat set HVAC mode
	#
	def special_thermHVACModeSet (self, classes, sourceDict, getter, characteristic, isOptional = False):
		try:
			obj = indigo.devices[self.objId]
			if "hvacMode" in dir(obj):
				if unicode(obj.hvacMode) == "Heat" or unicode(obj.hvacMode) == "ProgramHeat":
					self.setAttributeValue (characteristic, 1)
					self.characterDict[characteristic] = getattr (self, characteristic).value
				elif unicode(obj.hvacMode) == "Cool" or unicode(obj.hvacMode) == "ProgramCool":
					self.setAttributeValue (characteristic, 2)
					self.characterDict[characteristic] = getattr (self, characteristic).value
				elif unicode(obj.hvacMode) == "HeatCool" or unicode(obj.hvacMode) == "ProgramHeatCool":
					self.setAttributeValue (characteristic, 3)
					self.characterDict[characteristic] = getattr (self, characteristic).value	
				else:
					self.setAttributeValue (characteristic, 0)
					self.characterDict[characteristic] = getattr (self, characteristic).value
				
				#self.actions.append (HomeKitAction(characteristic, "equal", falseValue, cmd, [self.objId, 0], 0, {self.objId: "attr_brightness"}))
					
			else:
				self.setAttributeValue (characteristic, 0)
				self.characterDict[characteristic] = 0 
				
			self.actions.append (HomeKitAction(characteristic, "equal", 0, "thermostat.setHvacMode", [self.objId, indigo.kHvacMode.Off], 0, {self.objId: "attr_hvacMode"}))
			self.actions.append (HomeKitAction(characteristic, "equal", 1, "thermostat.setHvacMode", [self.objId, indigo.kHvacMode.Heat], 0, {self.objId: "attr_hvacMode"}))
			self.actions.append (HomeKitAction(characteristic, "equal", 2, "thermostat.setHvacMode", [self.objId, indigo.kHvacMode.Cool], 0, {self.objId: "attr_hvacMode"}))
			self.actions.append (HomeKitAction(characteristic, "equal", 3, "thermostat.setHvacMode", [self.objId, indigo.kHvacMode.HeatCool], 0, {self.objId: "attr_hvacMode"}))
		
		except Exception as e:
			self.logger.error (ext.getException(e) + "\nFor object id {} alias '{}'".format(str(self.objId), self.alias.value))				
						
	#
	# Change a thermostats set point
	#
	def special_thermTemperatureSetPointXXX (self, classes, sourceDict, getter, characteristic, isOptional = False):
		try:
			obj = indigo.devices[self.objId]
			if self.serverId == 0: return
			
			if self.convertFahrenheit:
				value = float(obj.coolSetpoint)
				if unicode(obj.hvacMode) == "Heat" or unicode(obj.hvacMode) == "ProgramHeat": value = float(obj.heatSetpoint)
				value = (value - 32) / 1.8000
				if value < 0: value = 0
				
				self.setAttributeValue (characteristic, round(value, 2))
				self.characterDict[characteristic] = getattr (self, characteristic).value
			else:
				value = float(obj.coolSetpoint)
				if unicode(obj.hvacMode) == "Heat" or unicode(obj.hvacMode) == "ProgramHeat": value = float(obj.heatSetpoint)
				
				self.setAttributeValue (characteristic, round(float(value), 2))
				self.characterDict[characteristic] = getattr (self, characteristic).value
										
			if unicode(obj.hvacMode) == "Heat" or unicode(obj.hvacMode) == "ProgramHeat":
				self.actions.append (HomeKitAction(characteristic, "between", 0.0, "homekit.commandSetTargetThermostatTemperature", [self.objId, self.serverId, "=value="], 100.0, {self.objId: "attr_heatSetpoint"}))
			else:	
				self.actions.append (HomeKitAction(characteristic, "between", 0.0, "homekit.commandSetTargetThermostatTemperature", [self.objId, self.serverId, "=value="], 100.0, {self.objId: "attr_coolSetpoint"}))		
				
			
					
		except Exception as e:
			self.logger.error (ext.getException(e) + "\nFor object id {} alias '{}'".format(str(self.objId), self.alias.value))	
			
			
	#
	# Change a thermostats set point
	#
	def special_thermTemperatureSetPoint (self, classes, sourceDict, getter, characteristic, isOptional = False):
		try:
			obj = indigo.devices[self.objId]
			if self.serverId == 0: return
			
			value = float(obj.coolSetpoint)
			if unicode(obj.hvacMode) == "Heat" or unicode(obj.hvacMode) == "ProgramHeat": value = float(obj.heatSetpoint)
			
			self.setAttributeValue (characteristic, round(float(value), 2))
			self.characterDict[characteristic] = getattr (self, characteristic).value
										
			if unicode(obj.hvacMode) == "Heat" or unicode(obj.hvacMode) == "ProgramHeat":
				self.actions.append (HomeKitAction(characteristic, "between", 0.0, "homekit.commandSetTargetThermostatTemperature", [self.objId, self.serverId, "=value="], 100.0, {self.objId: "attr_heatSetpoint"}))
			else:	
				self.actions.append (HomeKitAction(characteristic, "between", 0.0, "homekit.commandSetTargetThermostatTemperature", [self.objId, self.serverId, "=value="], 100.0, {self.objId: "attr_coolSetpoint"}))		
				
			
					
		except Exception as e:
			self.logger.error (ext.getException(e) + "\nFor object id {} alias '{}'".format(str(self.objId), self.alias.value))	
			
			
	
	#
	# Change a thermostats cooling set point
	#
	def special_thermCoolSet (self, classes, sourceDict, getter, characteristic, isOptional = False):
		try:
			obj = indigo.devices[self.objId]
			if self.serverId == 0: return
			
			if self.convertFahrenheit:
				value = float(obj.coolSetpoint)
				value = (value - 32) / 1.8000
				
				self.setAttributeValue (characteristic, round(value, 2))
				self.characterDict[characteristic] = getattr (self, characteristic).value
			else:
				value = float(obj.coolSetpoint)
				
				self.setAttributeValue (characteristic, round(float(value), 2))
				self.characterDict[characteristic] = getattr (self, characteristic).value
										
			self.actions.append (HomeKitAction(characteristic, "between", 0.0, "homekit.commandSetTargetThermostatCooling", [self.objId, self.serverId, "=value="], 100.0, {self.objId: "attr_coolSetpoint"}))		
				
			
					
		except Exception as e:
			self.logger.error (ext.getException(e) + "\nFor object id {} alias '{}'".format(str(self.objId), self.alias.value))		
			
	#
	# Change a thermostats heating set point
	#
	def special_thermHeatSet (self, classes, sourceDict, getter, characteristic, isOptional = False):
		try:
			obj = indigo.devices[self.objId]
			if self.serverId == 0: return
			
			if self.convertFahrenheit:
				value = float(obj.heatSetpoint)
				value = (value - 32) / 1.8000
				
				self.setAttributeValue (characteristic, round(value, 2))
				self.characterDict[characteristic] = getattr (self, characteristic).value
			else:
				value = float(obj.heatSetpoint)
				
				self.setAttributeValue (characteristic, round(float(value), 2))
				self.characterDict[characteristic] = getattr (self, characteristic).value
										
			self.actions.append (HomeKitAction(characteristic, "between", 0.0, "homekit.commandSetTargetThermostatHeating", [self.objId, self.serverId, "=value="], 100.0, {self.objId: "attr_heatSetpoint"}))		
				
			
					
		except Exception as e:
			self.logger.error (ext.getException(e) + "\nFor object id {} alias '{}'".format(str(self.objId), self.alias.value))								
			

	#
	# WeatherSnoop temperature
	#
	def special_wsTemperature (self, classes, sourceDict, getter, characteristic, isOptional = False):
		try:
			obj = indigo.devices[self.objId]

			if self.convertFahrenheit:
				value = float(obj.states["temperature_F"])
				value = (value - 32) / 1.8000
				
				self.setAttributeValue (characteristic, round(value, 2))
				self.characterDict[characteristic] = getattr (self, characteristic).value
				
				# Dummy action just so we get status updates for temperature	
				self.actions.append (HomeKitAction(characteristic, "equal", "STUB", "STUB", [self.objId, 0], 0, {self.objId: "state_temperature_F"}))
			else:
				self.setAttributeValue (characteristic, float(obj.states["temperature_C"]))
				self.characterDict[characteristic] = getattr (self, characteristic).value
				
				# Dummy action just so we get status updates for temperature	
				self.actions.append (HomeKitAction(characteristic, "equal", "STUB", "STUB", [self.objId, 0], 0, {self.objId: "state_temperature_C"}))
				
		
		except Exception as e:
			self.logger.error (ext.getException(e) + "\nFor object id {} alias '{}'".format(str(self.objId), self.alias.value))				
			
	#
	# Weather Underground temperature
	#
	def special_wuTemperature (self, classes, sourceDict, getter, characteristic, isOptional = False):
		try:
			obj = indigo.devices[self.objId]

			if self.convertFahrenheit:
				value = float(obj.states["temp"])
				value = (value - 32) / 1.8000
				
				self.setAttributeValue (characteristic, round(value, 2))
				self.characterDict[characteristic] = getattr (self, characteristic).value
			else:
				self.setAttributeValue (characteristic, float(obj.states["temp"]))
				self.characterDict[characteristic] = getattr (self, characteristic).value
				
			# Dummy action just so we get status updates for temperature	
			self.actions.append (HomeKitAction(characteristic, "equal", "STUB", "STUB", [self.objId, 0], 0, {self.objId: "state_temp"}))	
		
		except Exception as e:
			self.logger.error (ext.getException(e) + "\nFor object id {} alias '{}'".format(str(self.objId), self.alias.value))	


	#
	# Get temperature from sensorvalue
	#
	def special_sensorTemperature (self, classes, sourceDict, getter, characteristic, isOptional = False):
		try:
			obj = indigo.devices[self.objId]
			
			if self.convertFahrenheit:
				value = float(obj.sensorValue)
				value = (value - 32) / 1.8000
				
				self.setAttributeValue (characteristic, round(value, 2))
				self.characterDict[characteristic] = getattr (self, characteristic).value
			else:
				self.setAttributeValue (characteristic, float(obj.sensorValue))
				self.characterDict[characteristic] = getattr (self, characteristic).value
			
			# Dummy action just so we get status updates for temperature	
			self.actions.append (HomeKitAction(characteristic, "equal", "STUB", "STUB", [self.objId, 0], 0, {self.objId: "attr_sensorValue"}))	
			
		except Exception as e:
			self.logger.error (ext.getException(e) + "\nFor object id {} alias '{}'".format(str(self.objId), self.alias.value))			
			

	#
	# Get thermostat current temperature
	#
	def special_thermTemperature (self, classes, sourceDict, getter, characteristic, isOptional = False):
		try:
			obj = indigo.devices[self.objId]
			
			if self.convertFahrenheit:
				value = float(obj.states["temperatureInput1"])
				value = (value - 32) / 1.8000
				if value < 0: value = 0
				
				self.setAttributeValue (characteristic, round(value, 2))
				self.characterDict[characteristic] = getattr (self, characteristic).value
			else:
				self.setAttributeValue (characteristic, float(obj.states["temperatureInput1"]))
				self.characterDict[characteristic] = getattr (self, characteristic).value
		
			# Dummy action just so we get status updates for temperature	
			self.actions.append (HomeKitAction(characteristic, "equal", "STUB", "STUB", [self.objId, 0], 0, {self.objId: "state_temperatureInput1"}))	
			
		except Exception as e:
			self.logger.error (ext.getException(e) + "\nFor object id {} alias '{}'".format(str(self.objId), self.alias.value))				
			
			
	#
	# Thermostat show units in F or C
	#
	def special_serverCorFSetting (self, classes, sourceDict, getter, characteristic, isOptional = False):
		try:
			if self.serverId == 0: return
		
			obj = indigo.devices[self.serverId]
			if "tempunits" in obj.pluginProps:
				if obj.pluginProps["tempunits"] == "f":
					self.setAttributeValue (characteristic, 1)
					self.characterDict[characteristic] = getattr (self, characteristic).value
				else:
					self.setAttributeValue (characteristic, 0)
					self.characterDict[characteristic] = getattr (self, characteristic).value
			else:
				self.setAttributeValue (characteristic, 1)
				self.characterDict[characteristic] = getattr (self, characteristic).value
		
		except Exception as e:
			self.logger.error (ext.getException(e) + "\nFor object id {} alias '{}'".format(str(self.objId), self.alias.value))	
			

	#
	# Sprinkler program mode
	#
	def special_sprinklerProgramMode (self, classes, sourceDict, getter, characteristic, isOptional = False):
		try:
			if self.serverId == 0: return
		
			obj = indigo.devices[self.objId]
			if "activeZone" in dir(obj):
				if obj.activeZone is None or obj.activeZone == 0:
					self.setAttributeValue (characteristic, 0)
					self.characterDict[characteristic] = getattr (self, characteristic).value
			
				else:
					if len(obj.zoneScheduledDurations) == 0:
						# Manually running
						self.setAttributeValue (characteristic, 2)
						self.characterDict[characteristic] = getattr (self, characteristic).value
						
					else:
						# Program running 
						self.setAttributeValue (characteristic, 1)
						self.characterDict[characteristic] = getattr (self, characteristic).value
			else:
				self.setAttributeValue (characteristic, 1)
				self.characterDict[characteristic] = getattr (self, characteristic).value 	
		
		except Exception as e:
			self.logger.error (ext.getException(e) + "\nFor object id {} alias '{}'".format(str(self.objId), self.alias.value))	
			
	#
	# Sprinkler remaining duration
	#
	def special_sprinklerRemainingDuration (self, classes, sourceDict, getter, characteristic, isOptional = False):
		try:
			if self.serverId == 0: return
			
			obj = indigo.devices[self.objId]
			if "activeZone" in dir(obj):
				if obj.activeZone is None or obj.activeZone == 0:
					self.recurringUpdate = False
					self.setAttributeValue (characteristic, 0)
					self.characterDict[characteristic] = 0 
			
				else:
					self.recurringUpdate = True
					self.recurringSeconds = 5 # Update every second during runtime
					
					totalScheduledTime = 0
					secondsRunTimeRemaining = 0
					
					if len(obj.zoneScheduledDurations) == 0:
						# Manual run, use max times
						totalScheduledTime = obj.zoneMaxDurations[obj.activeZone - 1]
						
					else:
						# Scheduled run, use schedule times
						totalScheduledTime = obj.zoneScheduledDurations[obj.activeZone - 1]
						
					# Convert scheduled time to seconds, since Indigo runs in minutes
					totalScheduledTime = totalScheduledTime * 60
					
					# Calculate number of seconds that have transpired since the last time the device was updated, it should only update when we
					# make changes that impact this routine anyway
					seconds = dtutil.dateDiff ("seconds", indigo.server.getTime(), obj.lastChanged)
					
					# The remaining runtime should be total time less seconds since last change
					secondsRunTimeRemaining = int(totalScheduledTime - seconds)

					self.setAttributeValue (characteristic, secondsRunTimeRemaining)
					self.characterDict[characteristic] = getattr (self, characteristic).value
					
					if getattr (self, characteristic).value == 0:
						# They ran past the time, could be an Indigo problem, stop the auto refreshing as it's always going to be zero anyway
						self.recurringUpdate = False
					
			else:
				pass # Do nothing, it's an optional characteristic so if we don't populate it then it just simply won't display
		
		
		except Exception as e:
			self.logger.error (ext.getException(e) + "\nFor object id {} alias '{}'".format(str(self.objId), self.alias.value))				
		
	#
	# SenseMe Fan Control
	#
	def special_SenseMeFanToggle (self, classes, sourceDict, getter, characteristic, isOptional = False):
		try:
			if self.serverId == 0: return
		
			obj = indigo.devices[self.objId]
			self.setAttributeValue (characteristic, obj.states["fan"])
			self.characterDict[characteristic] = getattr (self, characteristic).value
			
			self.actions.append (HomeKitAction(characteristic, "equal", True, "homekit.runPluginAction", [indigo.devices[self.objId].pluginId, None, ["fanOn", self.objId]], 100, {self.objId: "state_fan"}))			
			self.actions.append (HomeKitAction(characteristic, "equal", False, "homekit.runPluginAction", [indigo.devices[self.objId].pluginId, None, ["fanOff", self.objId]], 100, {self.objId: "state_fan"}))			
			self.actions.append (HomeKitAction(characteristic, "equal", 1, "homekit.runPluginAction", [indigo.devices[self.objId].pluginId, None, ["fanOn", self.objId]], 100, {self.objId: "state_fan"}))			
			self.actions.append (HomeKitAction(characteristic, "equal", 0, "homekit.runPluginAction", [indigo.devices[self.objId].pluginId, None, ["fanOff", self.objId]], 100, {self.objId: "state_fan"}))			
		
		except Exception as e:
			self.logger.error (ext.getException(e) + "\nFor object id {} alias '{}'".format(str(self.objId), self.alias.value))	
			
	#
	# SenseMe Fan Speed
	#
	def special_SenseMeFanSpeed (self, classes, sourceDict, getter, characteristic, isOptional = False):
		try:
			if self.serverId == 0: return
		
			valuesDict = {'speed': "=value="}
			self.actions.append (HomeKitAction(characteristic, "between", 0, "homekit.runPluginAction", [indigo.devices[self.objId].pluginId, None, ["fanSpeed", self.objId, valuesDict]], 7, {self.objId: "state_speed"}))			
					
		except Exception as e:
			self.logger.error (ext.getException(e) + "\nFor object id {} alias '{}'".format(str(self.objId), self.alias.value))	

	#
	# SenseMe Fan Speed
	#
	def special_SenseMeFanSpeedXXX (self, classes, sourceDict, getter, characteristic, isOptional = False):
		try:
			if self.serverId == 0: return
		
			obj = indigo.devices[self.objId]
			self.setAttributeValue (characteristic, int(obj.states["speed"]) * 12.5)
			self.characterDict[characteristic] = getattr (self, characteristic).value
			
			valuesDict = {'speed': "=calc="}
			self.actions.append (HomeKitAction(characteristic, "between", 0, "homekit.runPluginAction_ModifyValue", [indigo.devices[self.objId].pluginId, "=value=", "divide", 12.5, ["fanSpeed", self.objId, valuesDict]], 100, {self.objId: "state_speed"}))			
		
		except Exception as e:
			self.logger.error (ext.getException(e) + "\nFor object id {} alias '{}'".format(str(self.objId), self.alias.value))		

	#
	# SenseMe Light Brightness
	#
	def special_SenseMeLightLevel (self, classes, sourceDict, getter, characteristic, isOptional = False):
		try:
			if self.serverId == 0: return
		
			valuesDict = {'lightLevel': "=value="}
			self.actions.append (HomeKitAction(characteristic, "between", 0, "homekit.runPluginAction", [indigo.devices[self.objId].pluginId, None, ["fanLightBrightness", self.objId, valuesDict]], 16, {self.objId: "state_brightness"}))			
					
		except Exception as e:
			self.logger.error (ext.getException(e) + "\nFor object id {} alias '{}'".format(str(self.objId), self.alias.value))	

			
	#
	# SenseMe Light Brightness
	#
	def special_SenseMeLightLevelXXX (self, classes, sourceDict, getter, characteristic, isOptional = False):
		try:
			if self.serverId == 0: return
		
			obj = indigo.devices[self.objId]
			
			value = int(obj.states["brightness"]) * 5.89
			if value > 100: value = 100
			if value < 5.89: value = 0
			if value > 83: value = 100 # 100 - 16
						
			self.setAttributeValue (characteristic, value)
			self.characterDict[characteristic] = getattr (self, characteristic).value
			
			valuesDict = {'lightLevel': "=calc="}
			self.actions.append (HomeKitAction(characteristic, "between", 0, "homekit.runPluginAction_ModifyValue", [indigo.devices[self.objId].pluginId, "=value=", "divide", 5.89, ["fanLightBrightness", self.objId, valuesDict]], 100, {self.objId: "state_brightness"}))			
		
		except Exception as e:
			self.logger.error (ext.getException(e) + "\nFor object id {} alias '{}'".format(str(self.objId), self.alias.value))	
			
	#
	# SenseMe Light Toggle
	#
	def special_SenseMeLightToggle (self, classes, sourceDict, getter, characteristic, isOptional = False):
		try:
			if self.serverId == 0: return
		
			obj = indigo.devices[self.objId]
			self.setAttributeValue (characteristic, obj.states["light"])
			self.characterDict[characteristic] = getattr (self, characteristic).value
						
			self.actions.append (HomeKitAction(characteristic, "equal", True, "homekit.runPluginAction", [indigo.devices[self.objId].pluginId, None, ["fanLightOn", self.objId]], 100, {self.objId: "state_light"}))			
			self.actions.append (HomeKitAction(characteristic, "equal", False, "homekit.runPluginAction", [indigo.devices[self.objId].pluginId, None, ["fanLightOff", self.objId]], 100, {self.objId: "state_light"}))			
			
		except Exception as e:
			self.logger.error (ext.getException(e) + "\nFor object id {} alias '{}'".format(str(self.objId), self.alias.value))										
			
		
	#
	# DSC Alarm Plugin Keypad
	#
	def special_dscKeypadState (self, classes, sourceDict, getter, characteristic, isOptional = False):
		try:
			if self.serverId == 0: return
		
			obj = indigo.devices[self.objId]
			if "ArmedState" in obj.states:
				if obj.states["ArmedState.disarmed"]:
					self.setAttributeValue (characteristic, 3)
					self.characterDict[characteristic] = getattr (self, characteristic).value
					
				if obj.states["ArmedState.stay"]:
					self.setAttributeValue (characteristic, 0)
					self.characterDict[characteristic] = getattr (self, characteristic).value	
					
				if obj.states["ArmedState.away"]:
					self.setAttributeValue (characteristic, 1)
					self.characterDict[characteristic] = getattr (self, characteristic).value
					
				if obj.states["state.tripped"]:
					self.setAttributeValue (characteristic, 4)
					self.characterDict[characteristic] = getattr (self, characteristic).value			
			else:
				self.setAttributeValue (characteristic, 3)
				self.characterDict[characteristic] = getattr (self, characteristic).value	
				
			self.actions.append (HomeKitAction(characteristic, "equal", 0, "homekit.runPluginAction", [indigo.devices[self.objId].pluginId, None, ["actionArmStay", self.objId]], 100, {self.objId: "state_ArmedState.stay"}))			
			self.actions.append (HomeKitAction(characteristic, "equal", 1, "homekit.runPluginAction", [indigo.devices[self.objId].pluginId, None, ["actionArmAway", self.objId]], 100, {self.objId: "state_ArmedState.away"}))			
			self.actions.append (HomeKitAction(characteristic, "equal", 2, "homekit.runPluginAction", [indigo.devices[self.objId].pluginId, None, ["actionArmStay", self.objId]], 100, {self.objId: "state_ArmedState.stay"}))			
			self.actions.append (HomeKitAction(characteristic, "equal", 3, "homekit.runPluginAction", [indigo.devices[self.objId].pluginId, None, ["actionDisarm", self.objId]], 100, {self.objId: "state_ArmedState.disarmed"}))			

			self.actions.append (HomeKitAction(characteristic, "equal", 99, "STUB", [indigo.devices[self.objId].pluginId, None, ["actionDisarm", self.objId]], 100, {self.objId: "state_state.tripped"}))			
		
		except Exception as e:
			self.logger.error (ext.getException(e) + "\nFor object id {} alias '{}'".format(str(self.objId), self.alias.value))	
			
			
				
	#
	# Convert RGB to Hue, Saturation and Color Temperature
	#
	def special_HSL (self, classes, sourceDict, getter, characteristic, isOptional = False):
		try:
			if self.serverId == 0: return
		
			obj = indigo.devices[self.objId]
			if "activeZone" in dir(obj):
				if obj.activeZone is None or obj.activeZone == 0:
					self.setAttributeValue (characteristic, 0)
					self.characterDict[characteristic] = getattr (self, characteristic).value
			
				else:
					if len(obj.zoneScheduledDurations) == 0:
						# Manually running
						self.setAttributeValue (characteristic, 2)
						self.characterDict[characteristic] = getattr (self, characteristic).value
						
					else:
						# Program running 
						self.setAttributeValue (characteristic, 1)
						self.characterDict[characteristic] = getattr (self, characteristic).value
			else:
				self.setAttributeValue (characteristic, 1)
				self.characterDict[characteristic] = getattr (self, characteristic).value 	
		
		except Exception as e:
			self.logger.error (ext.getException(e) + "\nFor object id {} alias '{}'".format(str(self.objId), self.alias.value))		
			
			
			
			
			
	#
	# TESTING CAMERA SETUP
	#
	def special_video (self, classes, sourceDict, getter, characteristic, isOptional = False):
		try:
			self.setAttributeValue (characteristic, "rtsp://admin:xxx@10.1.200.197/user=admin_password=tlJwpbo6_channel=1_stream=0.sdp")
			self.characterDict[characteristic] = getattr (self, characteristic).value
		
		except Exception as e:
			self.logger.error (ext.getException(e) + "\nFor object id {} alias '{}'".format(str(self.objId), self.alias.value))		
			
	def special_rtp (self, classes, sourceDict, getter, characteristic, isOptional = False):
		try:
			self.setAttributeValue (characteristic, "rtsp://admin:xxx@10.1.200.197/user=admin_password=tlJwpbo6_channel=1_stream=0.sdp")
			self.characterDict[characteristic] = getattr (self, characteristic).value
		
		except Exception as e:
			self.logger.error (ext.getException(e) + "\nFor object id {} alias '{}'".format(str(self.objId), self.alias.value))		
			
	def special_rtpstream (self, classes, sourceDict, getter, characteristic, isOptional = False):
		try:
			self.setAttributeValue (characteristic, "rtsp://admin:xxx@10.1.200.197/user=admin_password=tlJwpbo6_channel=1_stream=0.sdp")
			self.characterDict[characteristic] = getattr (self, characteristic).value
		
		except Exception as e:
			self.logger.error (ext.getException(e) + "\nFor object id {} alias '{}'".format(str(self.objId), self.alias.value))								
				
			
################################################################################
# HOMEKIT ACTIONS
#
# Defines and executes actions associated with a characteristic
################################################################################	
class HomeKitAction ():
	def __init__(self, characteristic, whenvalueis = "equal", whenvalue = 0, command = "", arguments = [], whenvalue2 = 0, monitors = {}, default = True):
		try:
			self.logger = logging.getLogger ("Plugin.HomeKitAction")
			
			self.characteristic = characteristic
			self.whenvalueis = whenvalueis
			self.whenvalue = whenvalue
			self.whenvalue2 = whenvalue2
			self.command = command
			self.arguments = arguments
			self.monitors = monitors # Dict of objId: attr_* | state_* | prop_* that we will monitor for this action - partly for future use if we are tying multiple objects to different properties and actions but also so our subscribe to changes knows what will trigger an update
			self.default = default # This action is a default action, mostly for if we need to replace default actions for special circumstances like invert
			
			# Determine the value data type by creating a mock object
			clsmembers = inspect.getmembers(sys.modules[__name__], inspect.isclass)
			for cls in clsmembers:
				if cls[0] == "characteristic_{}".format(characteristic):
					cclass = cls[1]
					break

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
		
	def run (self, value, objId, waitForComplete = True):
		try:
			# See if the value falls within the actions limitations and if it does then run the associated command
			#indigo.server.log(unicode(self))
			
			# If it's a device grab the last changed value so we can test below for it being updated
			runStartTime = indigo.server.getTime()
			
			# Catalog all monitor items
			monitors = {}
			obj = None
			for devId, prop in self.monitors.iteritems():
				if "attr_" in prop:
					obj = getattr (indigo.devices[devId], prop.replace("attr_", ""))
					monitors[devId] = {prop: obj}
				if "state_" in prop:
					if "states" in dir(indigo.devices[devId]):
						obj = indigo.devices[devId]
						if prop.replace("state_", "") in obj.states:
							monitors[devId] = {prop: obj.states[prop.replace("state_", "")]}
							
			# Special exception for Hue bulbs to not wait for state changes since we'll get three in succession
			if not obj is None and type(obj) == indigo.DimmerDevice and obj.pluginId == "com.nathansheldon.indigoplugin.HueLights":
				self.logger.threaddebug (u"Special exception mode for {} to allow for rapid changes in the Hue plugin".format(obj.name))
				waitForComplete = False
				
			# Special exception for Indigo virtual action groups that don't actually change value
			if not obj is None and type(obj) == indigo.DimmerDevice and obj.pluginId == "com.nathansheldon.indigoplugin.HueLights":
				self.logger.threaddebug (u"Special exception mode for {} to allow for rapid changes in the Hue plugin".format(obj.name))
				waitForComplete = False	
		
			# Get the value type of the value so we can convert from string to that type
			if type(self.whenvalue) == bool:
				if value.lower() == "true": 
					value = True
				elif value.lower() == "false":
					value = False
					
			elif type(self.whenvalue) == int:
				value = int(value)
				
			elif type(self.whenvalue) == float:
				value = float(value)
				
			else:
				self.logger.error (u"Unknown value for processAction: {}".format(str(type(self.whenvalue)).replace("<type '", "").replace("'>", "")))
				return False
				
			isValid = False
			
			if self.whenvalueis == "equal" and value == self.whenvalue:
				isValid = True
				
			elif self.whenvalueis == "between" and value >= self.whenvalue and value <= self.whenvalue2:
				isValid = True
			
			if isValid:
				# Try to run the command
				try:
					try:
						self.logger.debug (u"{} is running because the rule passes for {}".format(self.characteristic, self.command))
					except:
						pass
					
					# Fix up the arguments for placeholders
					args = []
					for a in self.arguments:
						if unicode(a) == "=value=":
							args.append(value)
						else:
							args.append(a)
							
						#indigo.server.log (unicode(type(a)) + "\t" + unicode(a))
				
					cmd = self.command.split(".")
					func = indigo
					if self.command[0:8] == "homekit.":
						func = self
						cmd = self.command.replace("homekit.", "")
						cmd = cmd.split(".")
				
					for c in cmd:
						func = getattr(func, c)
				
					if len(args) > 0: 
						retval = func(*args)
					else:
						retval = func()
						
					if waitForComplete:
						self.logger.threaddebug (u"Waiting for {} to complete".format(self.command))
						# We never do this for action groups, the HTML return will immediately return success so we can do a call back, this is only for devices
						if "actionGroup" not in self.command:
							for devId, prop in self.monitors.iteritems():							
								if devId in indigo.devices: 
									loopstart = indigo.server.getTime()
									runcomplete = False
									failsafe = 0
							
									while not runcomplete:
										failsafe = failsafe + 1
										if failsafe > 50000:
											self.logger.error (u"While setting the '{}' HomeKit characteristic for '{}' (HomeKit device '{}') the race condition failsafe was engaged, meaning the condition to break out of the action loop was not met.  This is fairly critical, please report to developer!".format(self.characteristic, indigo.devices[int(devId)].name, indigo.devices[int(objId)].name))
											runcomplete = True
											break
								
										d = dtutil.dateDiff ("seconds", indigo.server.getTime(), loopstart)
										if d > 25:
											self.logger.error (u"Maximum time exceeded while setting the '{}' HomeKit characteristic for '{}' (HomeKit device '{}'), aborting attempt.  This can happen if you try to set a device to a state is is already in (i.e., turning off a device that is already off).".format(self.characteristic, indigo.devices[int(devId)].name, indigo.devices[int(objId)].name))
											runcomplete = True
											break
								
										
										d = dtutil.dateDiff ("seconds", runStartTime, indigo.devices[int(devId)].lastChanged)
										#indigo.server.log(str(d) + " : " + str(indigo.devices[int(devId)].lastChanged))
										if d <= 0:
											# Something changed, see if it is one of our attributes, ANY attribute change (if there are multiple) will result in success
											for devId, prop in self.monitors.iteritems():
												if "attr_" in prop:
													#self.logger.threaddebug (u"Target device '{}' changed, checking attribute '{}' to see if it was updated".format(indigo.devices[devId].name, prop.replace("attr_", "")))
													obj = getattr (indigo.devices[devId], prop.replace("attr_", ""))
													self.logger.threaddebug (u"No change: " + unicode(monitors[devId]) + " = " + unicode({prop: obj}))
													# Not only check if the state changed, but check if it's already what HK asked to be, if it said to turn off and it's off then it's done
													# this comes up with brightness/onOff because brightness turns it on and if we get an onOff afterwards it'll hang because it'll never update the state
													if monitors[devId] != {prop: obj} or obj == value:
														self.logger.debug (u"Target device '{}' attribute '{}' was updated, the command succeeded".format(indigo.devices[devId].name, prop.replace("attr_", "")))
														runcomplete = True
														break
														
													self.logger.threaddebug (u"Target device '{}' attribute '{}' was not updated, still waiting".format(indigo.devices[devId].name, prop.replace("attr_", "")))
														
												if "state_" in prop:
													if "states" in dir(indigo.devices[devId]):
														#self.logger.threaddebug (u"Target device '{}' changed, checking state '{}' to see if it was updated".format(indigo.devices[devId].name, prop.replace("state_", "")))
														obj = indigo.devices[devId]
														if prop.replace("state_", "") in obj.states:
															state = obj.states[prop.replace("state_", "")]
															#indigo.server.log("Monitor: " + unicode(monitors[devId]))
															#indigo.server.log("Compare: " + unicode({prop: state}))
															#indigo.server.log("State: " + unicode(obj.states[prop.replace("state_", "")]))
															if monitors[devId] != {prop: state} or obj.states[prop.replace("state_", "")] == value:
																self.logger.debug (u"Target device '{}' state '{}' was updated, the command succeeded".format(indigo.devices[devId].name, prop.replace("state_", "")))
																runcomplete = True
																break
															#else:
															#	self.logger.info (u"Target device '{}' state '{}' value '{}' is equal to '{}'".format(indigo.devices[devId].name, prop.replace("state_", ""), unicode({prop: obj.states[prop.replace("state_", "")]}), unicode(monitors[devId])))
																
																
														#self.logger.threaddebug (u"Target device '{}' state '{}' was not updated, still waiting".format(indigo.devices[devId].name, prop.replace("state_", "")))

				
				except Exception as ex:
					self.logger.error (ext.getException(ex))
					return False
		
				return True
			
			else:
				self.logger.debug (u"{} was not set because the rule didn't pass for {}".format(self.characteristic, self.command))
				return False
				
		
		except Exception as e:
			self.logger.error (ext.getException(e))
			return False
		
		return True			
		
		
	################################################################################
	# COMMAND STUBS
	################################################################################
	
	#
	# Convert a value and then run a plugin action for it
	#
	def runPluginAction_ModifyValue (self, pluginId, value, calculationMethod, calculationValue, arguments):
		try:
			if calculationMethod == "divide" and value != 0 and calculationValue != 0:
				value = float(value) / calculationValue
				
			elif calculationMethod == "multiply" and value != 0 and calculationValue != 0:
				value = float(value) * calculationValue	
				
			# Iterate through the arguments LIST
			newarguments = []
			for arg in arguments:
				if type(arg) == dict:
					newdict = {}
					for key, val in arg.iteritems():
						if val == "=calc=": 
							newdict[key] = value
						else:
							newdict[key] = val
						
					newarguments.append(newdict)
					
				else:
					if arg == "=calc=": 
						newarguments.append(value)
					else:
						newarguments.append(arg)
			
			
				
			return self.runPluginAction (pluginId, value, newarguments)
		
		except Exception as e:
			self.logger.error (ext.getException(e))
			return False		
	
	#
	# Connect to specified plugin and run the actions
	#
	def runPluginAction (self, pluginId, value, arguments):
		try:
			plugin = indigo.server.getPlugin(pluginId)
			if plugin.isEnabled():
				args = []
				for a in arguments:
					# Since we are passing arguments in this way make sure we dig into additional lists or dicts
					if type(a) == list:
						largs = []
						for l in a:
							if unicode(l) == "=value=":
								largs.append(value)
							else:
								largs.append(l)
								
						args.append (largs)
						
					elif type(a) == dict:
						dargs = {}
						for key, d in a.iteritems():
							if unicode(d) == "=value=":
								dargs[key] = value
							else:
								dargs[key] = d

						args.append (dargs)
											
					else:
						if unicode(a) == "=value=":
							args.append(value)
						else:
							args.append(a)
							
				self.logger.threaddebug (u"Running plugin action on {} with {}".format(pluginId, unicode(args)))
				result = plugin.executeAction(*args, waitUntilDone=True)
				self.logger.threaddebug (u"Plugin action return value: " + unicode(result))
			else:
				self.logger.error (u"Unable to run plugin command because {} is not installed or disabled".format(pluginid))
				return False
			
			#[indigo.devices[self.objId].pluginId, ["disconnect", self.objId]]
			
		except Exception as e:
			self.logger.error (ext.getException(e))
			return False
			
	#
	# Change thermostat temperature
	#
	def commandSetTargetThermostatHeating (self, devId, serverId, targetTemperature):
		try:
			server = indigo.devices[serverId]
			dev = indigo.devices[devId]
			if type(dev) != indigo.ThermostatDevice:
				self.logger.error (u"Attempting to run {} as a thermostat with thermostat commands but it is not a thermostat".format(dev.name))
				return
				
			serverProps = server.pluginProps
			includedDevices = json.loads(serverProps["includedDevices"])
			includedActions = json.loads(serverProps["includedActions"])
			
			r = None
			for rec in includedDevices:
				if rec["id"] == devId:
					r = rec
					break
					
			if r is None:
				for rec in includedActions:
					if rec["id"] == devId:
						r = rec
						break
			
			if r is None:
				self.logger.error (u"Attempting to change {} thermostat settings but could not find the thermostat in stash".format(dev.name))
				return
							
			if "tempIsF" in r and r["tempIsF"]:
				# If our source is fahrenheit then we need to convert it
				value = float(targetTemperature)
				value = (value * 1.8000) + 32
				value = round(value, 0) # We fahrenheit users never use fractions - if someone requests it in the future we can add an option

			else:
				value = targetTemperature
							
			indigo.thermostat.setHeatSetpoint (devId, value)
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
			
	#
	# Change thermostat temperature
	#
	def commandSetTargetThermostatCooling (self, devId, serverId, targetTemperature):
		try:
			server = indigo.devices[serverId]
			dev = indigo.devices[devId]
			if type(dev) != indigo.ThermostatDevice:
				self.logger.error (u"Attempting to run {} as a thermostat with thermostat commands but it is not a thermostat".format(dev.name))
				return
				
			serverProps = server.pluginProps
			includedDevices = json.loads(serverProps["includedDevices"])
			includedActions = json.loads(serverProps["includedActions"])
			
			r = None
			for rec in includedDevices:
				if rec["id"] == devId:
					r = rec
					break
					
			if r is None:
				for rec in includedActions:
					if rec["id"] == devId:
						r = rec
						break
			
			if r is None:
				self.logger.error (u"Attempting to change {} thermostat settings but could not find the thermostat in stash".format(dev.name))
				return
							
			if "tempIsF" in r and r["tempIsF"]:
				# If our source is fahrenheit then we need to convert it
				value = float(targetTemperature)
				value = (value * 1.8000) + 32
				value = round(value, 0) # We fahrenheit users never use fractions - if someone requests it in the future we can add an option

			else:
				value = targetTemperature
							
			indigo.thermostat.setCoolSetpoint (devId, value)
		
		except Exception as e:
			self.logger.error (ext.getException(e))				
						
	
	#
	# Change thermostat temperature
	#
	def commandSetTargetThermostatTemperature (self, devId, serverId, targetTemperature):
		try:
			server = indigo.devices[serverId]
			dev = indigo.devices[devId]
			if type(dev) != indigo.ThermostatDevice:
				self.logger.error (u"Attempting to run {} as a thermostat with thermostat commands but it is not a thermostat".format(dev.name))
				return
				
			serverProps = server.pluginProps
			includedDevices = json.loads(serverProps["includedDevices"])
			includedActions = json.loads(serverProps["includedActions"])
			
			r = None
			for rec in includedDevices:
				if rec["id"] == devId:
					r = rec
					break
					
			if r is None:
				for rec in includedActions:
					if rec["id"] == devId:
						r = rec
						break
			
			if r is None:
				self.logger.error (u"Attempting to change {} thermostat settings but could not find the thermostat in stash".format(dev.name))
				return
							
			if "tempIsF" in r and r["tempIsF"]:
				# If our source is fahrenheit then we need to convert it
				value = float(targetTemperature)
				value = (value * 1.8000) + 32
				value = round(value, 0) # We fahrenheit users never use fractions - if someone requests it in the future we can add an option

			else:
				value = targetTemperature
							
			if unicode(dev.hvacMode) == "Heat" or unicode(dev.hvacMode) == "ProgramHeat":			
				#indigo.server.log ("Set heat set point of {} on server {} to {}".format(str(devId), str(serverId), str(value)))
				indigo.thermostat.setHeatSetpoint (devId, value)
				
			if unicode(dev.hvacMode) == "Cool" or unicode(dev.hvacMode) == "ProgramCool":			
				#indigo.server.log ("Set cool set point of {} on server {} to {}".format(str(devId), str(serverId), str(value)))
				indigo.thermostat.setCoolSetpoint (devId, value)
		
		except Exception as e:
			self.logger.error (ext.getException(e))	

################################################################################
# HOMEKIT SERVICES
#
# Inherits the service class and defines the service
################################################################################	

# ==============================================================================
# DUMMY SERVICE WHEN WE CANNOT AUTODETECT
# ==============================================================================
class Dummy (Service):

	#
	# Initialize the class
	#
	def __init__ (self, factory, objId, serverId = 0, characterDict = {}, deviceActions = [], loadOptional = False):
		type = "Dummy"
		desc = "Invalid"
	
		super(Dummy, self).__init__ (factory, type, desc, objId, serverId, characterDict, deviceActions, loadOptional)
		
		self.required = {}
		self.optional = {}
					
		super(Dummy, self).setAttributes ()
				
		if objId != 0: self.logger.debug (u'{} started as a HomeKit {}'.format(self.alias.value, self.desc))		
		#self.logger.warning ('{} has no automatic conversion to HomeKit and will not be usable unless custom mapped'.format(self.alias.value))	

# ==============================================================================
# AIR QUALITY SENSOR
# ==============================================================================
class service_AirQualitySensor (Service):

	#
	# Initialize the class
	#
	def __init__ (self, factory, objId, serverId = 0, characterDict = {}, deviceActions = [], loadOptional = False):
		type = "AirQualitySensor"
		desc = "Air Quality Sensor"
		
		super(service_AirQualitySensor, self).__init__ (factory, type, desc, objId, serverId, characterDict, deviceActions, loadOptional)
		
		self.required = {}
		self.required["AirQuality"] = {"indigo.SensorDevice": "attr_sensorValue"}
		
		self.optional = {}
		self.optional["StatusActive"] = {"*": "attr_onState"}
		self.optional["StatusFault"] = {}
		self.optional["StatusTampered"] = {}
		self.optional["StatusLowBattery"] = {"*": "special_lowbattery"}
		self.optional["Name"] = {}
		self.optional["OzoneDensity"] = {}
		self.optional["NitrogenDioxideDensity"] = {}
		self.optional["SulphurDioxideDensity"] = {}
		self.optional["PM2_5Density"] = {}
		self.optional["PM10Density"] = {}
		self.optional["VOCDensity"] = {}
		self.optional["CarbonMonoxideLevel"] = {}
		self.optional["CarbonDioxideLevel"] = {}
					
		super(service_AirQualitySensor, self).setAttributes ()					
				
		if objId != 0: self.logger.debug (u'{} started as a HomeKit {}'.format(self.alias.value, self.desc))	

# ==============================================================================
# AIR PURIFIER
# ==============================================================================
class service_AirPurifier (Service):

	#
	# Initialize the class
	#
	def __init__ (self, factory, objId, serverId = 0, characterDict = {}, deviceActions = [], loadOptional = False):
		type = "AirPurifier"
		desc = "Air Purifier"
		
		super(service_AirPurifier, self).__init__ (factory, type, desc, objId, serverId, characterDict, deviceActions, loadOptional)
		
		self.required = {}
		self.required["Active"] = {"*": "attr_onState"}
		self.required["CurrentAirPurifierState"] = {"*": "attr_onState"}
		self.required["TargetAirPurifierState"] = {"*": "attr_onState"}
	
		self.optional = {}
		self.optional["LockPhysicalControls"] = {}
		self.optional["Name"] = {}
		self.optional["SwingMode"] = {}
		self.optional["RotationSpeed"] = {"*": "attr_brightness"}
					
		super(service_AirPurifier, self).setAttributes ()					
				
		if objId != 0: self.logger.debug (u'{} started as a HomeKit {}'.format(self.alias.value, self.desc))	

# ==============================================================================
# BATTERY SERVICE
# ==============================================================================
class service_BatteryService (Service):

	#
	# Initialize the class
	#
	def __init__ (self, factory, objId, serverId = 0, characterDict = {}, deviceActions = [], loadOptional = False):
		type = "BatteryService"
		desc = "Battery Service (3rd Party and Siri Only)"
		
		self.wiki = "This service is unsupported by the native Apple Home application but is supported, in varying degrees, in 3rd party HomeKit apps.  Apps tested with this service that work are the [non-Apple version of Home](https://itunes.apple.com/us/app/home-smart-home-automation/id995994352?mt=8) and [Elgato Eve](https://itunes.apple.com/us/app/elgato-eve/id917695792?mt=8)."
	
		super(service_BatteryService, self).__init__ (factory, type, desc, objId, serverId, characterDict, deviceActions, loadOptional)
		
		self.required = {}
		self.required["BatteryLevel"] = {"*": "attr_batteryLevel"}
		self.required["ChargingState"] = {}
		self.required["StatusLowBattery"] = {"*": "special_lowbattery"}
	
		self.optional = {}
		self.optional["Name"] = {}
					
		super(service_BatteryService, self).setAttributes ()					
				
		if objId != 0: self.logger.debug (u'{} started as a HomeKit {}'.format(self.alias.value, self.desc))		
		
# ==============================================================================
# CAMERA RTP STREAM MANAGEMENT
# ==============================================================================
class service_CameraRTPStreamManagement (Service):

	#
	# Initialize the class
	#
	def __init__ (self, factory, objId, serverId = 0, characterDict = {}, deviceActions = [], loadOptional = False):
		type = "CameraRTPStreamManagement"
		desc = "Camera RTP Stream"
		
		self.wiki = "Only supported for SecuritySpy and Blue Iris Indigo devices currently"
			
		super(service_CameraRTPStreamManagement, self).__init__ (factory, type, desc, objId, serverId, characterDict, deviceActions, loadOptional)
		
		self.required = {}
		self.required["SupportedVideoStreamConfiguration"] = {"*": "special_video"}
		self.required["SupportedAudioStreamConfiguration"] = {"*": "special_audio"}
		self.required["SupportedRTPConfiguration"] = {"*": "special_rtp"}
		self.required["SelectedRTPStreamConfiguration"] = {"*": "special_rtpstream"}
		self.required["StreamingStatus"] = {"*": "special_streamstatus"}
		self.required["SetupEndpoints"] = {"*": "special_endpoints"}
	
		self.optional = {}
		self.optional["Name"] = {}
					
		super(service_CameraRTPStreamManagement, self).setAttributes ()					
				
		if objId != 0: self.logger.debug (u'{} started as a HomeKit {}'.format(self.alias.value, self.desc))			
		
# ==============================================================================
# CARBON DIOXIDE SENSOR
# ==============================================================================
class service_CarbonDioxideSensor (Service):

	#
	# Initialize the class
	#
	def __init__ (self, factory, objId, serverId = 0, characterDict = {}, deviceActions = [], loadOptional = False):
		type = "CarbonDioxideSensor"
		desc = "Carbon Dioxide (CO2) Sensor"
	
		super(service_CarbonDioxideSensor, self).__init__ (factory, type, desc, objId, serverId, characterDict, deviceActions, loadOptional)
		
		self.required = {}
		self.required["CarbonDioxideDetected"] = {"*": "attr_onState"}
	
		self.optional = {}
		self.optional["StatusActive"] = {}
		self.optional["StatusFault"] = {}
		self.optional["StatusTampered"] = {}
		self.optional["StatusLowBattery"] = {"*": "special_lowbattery"}
		self.optional["Name"] = {}
		self.optional["CarbonDioxideLevel"] = {"indigo.SensorDevice": "attr_sensorValue", "indigo.DimmerDevice": "attr_brightness"}
		self.optional["CarbonDioxidePeakLevel"] = {}
					
		super(service_CarbonDioxideSensor, self).setAttributes ()				
				
		if objId != 0: self.logger.debug (u'{} started as a HomeKit {}'.format(self.alias.value, self.desc))		
		
# ==============================================================================
# CARBON MONOXIDE SENSOR
# ==============================================================================
class service_CarbonMonoxideSensor (Service):

	#
	# Initialize the class
	#
	def __init__ (self, factory, objId, serverId = 0, characterDict = {}, deviceActions = [], loadOptional = False):
		type = "CarbonMonoxideSensor"
		desc = "Carbon Monoxide (CO) Sensor"
	
		super(service_CarbonMonoxideSensor, self).__init__ (factory, type, desc, objId, serverId, characterDict, deviceActions, loadOptional)
		
		self.required = {}
		self.required["CarbonMonoxideDetected"] = {"*": "attr_onState"}
	
		self.optional = {}
		self.optional["StatusActive"] = {}
		self.optional["StatusFault"] = {}
		self.optional["StatusTampered"] = {}
		self.optional["StatusLowBattery"] = {"*": "special_lowbattery"}
		self.optional["Name"] = {}
		self.optional["CarbonMonoxideLevel"] = {"indigo.SensorDevice": "attr_sensorValue", "indigo.DimmerDevice": "attr_brightness"}
		self.optional["CarbonMonoxidePeakLevel"] = {}
					
		super(service_CarbonMonoxideSensor, self).setAttributes ()				
				
		if objId != 0: self.logger.debug (u'{} started as a HomeKit {}'.format(self.alias.value, self.desc))				

# ==============================================================================
# CONTACT SENSOR
# ==============================================================================
class service_ContactSensor (Service):

	#
	# Initialize the class
	#
	def __init__ (self, factory, objId, serverId = 0, characterDict = {}, deviceActions = [], loadOptional = False):
		type = "ContactSensor"
		desc = "Contact Sensor"
	
		super(service_ContactSensor, self).__init__ (factory, type, desc, objId, serverId, characterDict, deviceActions, loadOptional)
		
		if not self.jsoninit:
			self.required = {}
			self.required["ContactSensorState"] = {"*": "special_invertedOnState", "indigo.ThermostatDevice": "attr_fanIsOn", "indigo.MultiIODevice": "state_binaryOutput1", "indigo.SprinklerDevice": "activeZone", "indigo.Device.com.eps.indigoplugin.device-extensions.epsdecon": "state_convertedBoolean", "indigo.Device.com.frightideas.indigoplugin.dscAlarm.alarmZone": "state_state.open"}
	
			self.optional = {}
			self.optional["StatusActive"] = {}
			self.optional["StatusFault"] = {}
			self.optional["StatusTampered"] = {}
			self.optional["StatusLowBattery"] = {"*": "special_lowbattery"}
			self.optional["Name"] = {}
					
		super(service_ContactSensor, self).setAttributes ()				
				
		if objId != 0: self.logger.debug (u'{} started as a HomeKit {}'.format(self.alias.value, self.desc))		
		
# ==============================================================================
# DOOR
# ==============================================================================
class service_Door (Service):

	#
	# Initialize the class
	#
	def __init__ (self, factory, objId, serverId = 0, characterDict = {}, deviceActions = [], loadOptional = False):
		type = "Door"
		desc = "Door"
	
		super(service_Door, self).__init__ (factory, type, desc, objId, serverId, characterDict, deviceActions, loadOptional)
		
		self.required = {}
		self.required["CurrentPosition"] = {"*": "attr_brightness", "indigo.RelayDevice": "special_onStateToFullBrightness"}
		self.required["PositionState"] = {}
		self.required["TargetPosition"] = {"*": "attr_brightness", "indigo.RelayDevice": "special_onStateToFullBrightness"}

		self.optional = {}
		self.optional["HoldPosition"] = {}
		self.optional["ObstructionDetected"] = {}
		self.optional["Name"] = {}
					
		super(service_Door, self).setAttributes ()			
		
		if objId != 0: self.logger.debug (u'{} started as a HomeKit {}'.format(self.alias.value, self.desc))			
		
# ==============================================================================
# DOOR BELL
# ==============================================================================
class service_Doorbell (Service):

	#
	# Initialize the class
	#
	def __init__ (self, factory, objId, serverId = 0, characterDict = {}, deviceActions = [], loadOptional = False):
		type = "Doorbell"
		desc = "Doorbell (Experimental & Unsupported)"
		
		self.wiki = "This service is completely experimental as it relies on an undocumented HomeKit method that is still being decoded, consider this unusable until further notice and only appears in the plugin for development testing"
	
		super(service_Doorbell, self).__init__ (factory, type, desc, objId, serverId, characterDict, deviceActions, loadOptional)
		
		self.required = {}
		self.required["ProgrammableSwitchEvent"] = {"*": "attr_onState"}

		self.optional = {}
		self.optional["Brightness"] = {"*": "attr_brightness"}
		self.optional["Volume"] = {}
		self.optional["Name"] = {}
					
		super(service_Doorbell, self).setAttributes ()			
						
		if objId != 0: self.logger.debug (u'{} started as a HomeKit {}'.format(self.alias.value, self.desc))							

# ==============================================================================
# FAN
# ==============================================================================
class service_Fan (Service):

	#
	# Initialize the class
	#
	def __init__ (self, factory, objId, serverId = 0, characterDict = {}, deviceActions = [], loadOptional = False):
		type = "Fan"
		desc = "Fan (Original)"
		
		self.wiki = "This fan acts pretty much just like the Fanv2, except it has fewer capabilities.  There may be reasons to hold on to it and that may become apparent in the future but consider this a device that may be depreciated and may not be included in future versions."
	
		super(service_Fan, self).__init__ (factory, type, desc, objId, serverId, characterDict, deviceActions, loadOptional)
	
		self.required = {}
		self.required["On"] = {"*": "attr_onState", "indigo.ThermostatDevice": "attr_fanIsOn", "indigo.MultiIODevice": "state_binaryOutput1", "indigo.SprinklerDevice": "activeZone", "indigo.Device.com.pennypacker.indigoplugin.senseme.SenseME_fan": "special_SenseMeFanToggle"}
	
		self.optional = {}
		self.optional["Name"] = {}
		self.optional["RotationDirection"] = {}
		self.optional["RotationSpeed"] = {"indigo.DimmerDevice": "attr_brightness", "indigo.SpeedControlDevice": "attr_speedLevel", "indigo.Device.com.pennypacker.indigoplugin.senseme.SenseME_fan": "special_SenseMeFanSpeed"}
				
		super(service_Fan, self).setAttributes ()
			
		if objId != 0: self.logger.debug (u'{} started as a HomeKit {}'.format(self.alias.value, self.desc))	

# ==============================================================================
# FAN V2
# ==============================================================================
class service_Fanv2 (Service):

	#
	# Initialize the class
	#
	def __init__ (self, factory, objId, serverId = 0, characterDict = {}, deviceActions = [], loadOptional = False):
		type = "Fanv2"
		desc = "Fan"

		super(service_Fanv2, self).__init__ (factory, type, desc, objId, serverId, characterDict, deviceActions, loadOptional)
	
		self.required = {}
		self.required["Active"] = {"*": "attr_onState", "indigo.ThermostatDevice": "attr_fanIsOn", "indigo.MultiIODevice": "state_binaryOutput1", "indigo.SprinklerDevice": "activeZone", "indigo.Device.com.pennypacker.indigoplugin.senseme.SenseME_fan": "special_SenseMeFanToggle"}
	
		self.optional = {}
		self.optional["CurrentFanState"] = {}
		self.optional["TargetFanState"] = {}
		self.optional["LockPhysicalControls"] = {}
		self.optional["Name"] = {}
		self.optional["RotationDirection"] = {}
		self.optional["RotationSpeed"] = {"indigo.DimmerDevice": "attr_brightness", "indigo.SpeedControlDevice": "attr_speedLevel", "indigo.Device.com.pennypacker.indigoplugin.senseme.SenseME_fan": "special_SenseMeFanSpeed"}
		self.optional["SwingMode"] = {}
				
		super(service_Fanv2, self).setAttributes ()
			
		if objId != 0: self.logger.debug (u'{} started as a HomeKit {}'.format(self.alias.value, self.desc))	
		
# ==============================================================================
# FAUCET
# ==============================================================================
class service_Faucet (Service):

	#
	# Initialize the class
	#
	def __init__ (self, factory, objId, serverId = 0, characterDict = {}, deviceActions = [], loadOptional = False):
		type = "Faucet"
		desc = "Faucet (3rd Party and Siri Only)"
		
		self.wiki = "This service is unsupported by the native Apple Home application but is supported, in varying degrees, in 3rd party HomeKit apps.  Apps tested with this service that work are the [non-Apple version of Home](https://itunes.apple.com/us/app/home-smart-home-automation/id995994352?mt=8) and [Elgato Eve](https://itunes.apple.com/us/app/elgato-eve/id917695792?mt=8)."
		
		super(service_Faucet, self).__init__ (factory, type, desc, objId, serverId, characterDict, deviceActions, loadOptional)
		
		self.required = {}
		self.required["Active"] = {"*": "attr_onState"}

		self.optional = {}
		self.optional["StatusFault"] = {}
		self.optional["Name"] = {}
					
		super(service_Faucet, self).setAttributes ()			
						
		if objId != 0: self.logger.debug (u'{} started as a HomeKit {}'.format(self.alias.value, self.desc))				
		
# ==============================================================================
# FILTER MAINTENANCE
# ==============================================================================
class service_FilterMaintenance (Service):

	#
	# Initialize the class
	#
	def __init__ (self, factory, objId, serverId = 0, characterDict = {}, deviceActions = [], loadOptional = False):
		type = "FilterMaintenance"
		desc = "Filter Maintenance (3rd Party and Siri Only)"

		self.wiki = "This service is unsupported by the native Apple Home application but is supported, in varying degrees, in 3rd party HomeKit apps.  Apps tested with this service that work are the [non-Apple version of Home](https://itunes.apple.com/us/app/home-smart-home-automation/id995994352?mt=8) and [Elgato Eve](https://itunes.apple.com/us/app/elgato-eve/id917695792?mt=8)."

		super(service_FilterMaintenance, self).__init__ (factory, type, desc, objId, serverId, characterDict, deviceActions, loadOptional)
	
		self.required = {}
		self.required["FilterChangeIndication"] = {"*": "attr_onState"}
	
		self.optional = {}
		self.optional["FilterLifeLevel"] = {"*": "attr_brightness", "indigo.SensorDevice": "attr_sensorValue"}
		self.optional["ResetFilterIndication"] = {"indigo.Device.com.eps.indigoplugin.device-extensions.Filter-Sensor": "special_deReplaceFilter"}
				
		super(service_FilterMaintenance, self).setAttributes ()
			
		if objId != 0: self.logger.debug (u'{} started as a HomeKit {}'.format(self.alias.value, self.desc))			

		
# ==============================================================================
# GARAGE DOOR OPENER
# ==============================================================================
class service_GarageDoorOpener (Service):

	#
	# Initialize the class
	#
	def __init__ (self, factory, objId, serverId = 0, characterDict = {}, deviceActions = [], loadOptional = False):
		type = "GarageDoorOpener"
		desc = "Garage Door Opener"
	
		super(service_GarageDoorOpener, self).__init__ (factory, type, desc, objId, serverId, characterDict, deviceActions, loadOptional)
		
		self.required = {}
		self.required["CurrentDoorState"] = {"*": "attr_onState", "indigo.MultiIODevice": "state_binaryInput1", "indigo.Device.com.frightideas.indigoplugin.dscAlarm.alarmZone": "state_state.open"}
		self.required["TargetDoorState"] = {"*": "attr_onState", "indigo.MultiIODevice": "state_binaryInput1", "indigo.Device.com.frightideas.indigoplugin.dscAlarm.alarmZone": "state_state.open"}
		self.required["ObstructionDetected"] = {}
	
		self.optional = {}
		self.optional["LockCurrentState"] = {}
		self.optional["LockTargetState"] = {}
		self.optional["Name"] = {}
					
		super(service_GarageDoorOpener, self).setAttributes ()			
						
		if objId != 0: self.logger.debug (u'{} started as a HomeKit {}'.format(self.alias.value, self.desc))			

# ==============================================================================
# HEATER / COOLER
# ==============================================================================
class service_HeaterCooler (Service):

	#
	# Initialize the class
	#
	def __init__ (self, factory, objId, serverId = 0, characterDict = {}, deviceActions = [], loadOptional = False):
		type = "HeaterCooler"
		desc = "Heater / Cooler"
	
		super(service_HeaterCooler, self).__init__ (factory, type, desc, objId, serverId, characterDict, deviceActions, loadOptional)
		
		self.required = {}
		self.required["Active"] = {"*": "attr_onState"}
		self.required["CurrentHeaterCoolerState"] = {"indigo.ThermostatDevice": "special_thermHVACMode"}
		self.required["TargetHeaterCoolerState"] = {"indigo.ThermostatDevice": "special_thermHVACMode"}
		self.required["CurrentTemperature"] = {"indigo.ThermostatDevice": "special_thermTemperature"}
	
		self.optional = {}
		self.optional["LockPhysicalControls"] = {}
		self.optional["Name"] = {}
		self.optional["SwingMode"] = {}
		self.optional["CoolingThresholdTemperature"] = {}
		self.optional["HeatingThresholdTemperature"] = {}
		self.optional["TemperatureDisplayUnits"] = {"indigo.ThermostatDevice": "special_serverCorFSetting"}
		self.optional["RotationSpeed"] = {"indigo.DimmerDevice": "attr_brightness", "indigo.SpeedControlDevice": "attr_speedLevel"}
		self.optional["Name"] = {}
					
		super(service_HeaterCooler, self).setAttributes ()				
				
		if objId != 0: self.logger.debug (u'{} started as a HomeKit {}'.format(self.alias.value, self.desc))	

# ==============================================================================
# HUMIDIFIER / DEHUMIDIFIER
# ==============================================================================
class service_HumidifierDehumidifier (Service):

	#
	# Initialize the class
	#
	def __init__ (self, factory, objId, serverId = 0, characterDict = {}, deviceActions = [], loadOptional = False):
		type = "HumidifierDehumidifier"
		desc = "Humidifier / Dehumidifier"
	
		super(service_HumidifierDehumidifier, self).__init__ (factory, type, desc, objId, serverId, characterDict, deviceActions, loadOptional)
		
		self.required = {}
		self.required["CurrentRelativeHumidity"] = {"*": "attr_sensorValue", "indigo.ThermostatDevice": "state_humidityInput1", "indigo.Device.com.fogbert.indigoplugin.wunderground.wunderground": "state_relativeHumidity"}
		self.required["CurrentHumidifierDehumidifierState"] = {}
		self.required["TargetHumidifierDehumidifierState"] = {}
		self.required["Active"] = {"*": "attr_onState"}
	
		self.optional = {}
		self.optional["LockPhysicalControls"] = {}
		self.optional["Name"] = {}
		self.optional["SwingMode"] = {}
		self.optional["WaterLevel"] = {}
		self.optional["RelativeHumidityDehumidifierThreshold"] = {}
		self.optional["RelativeHumidityHumidifierThreshold"] = {}
		self.optional["RotationSpeed"] = {"indigo.DimmerDevice": "attr_brightness", "indigo.SpeedControlDevice": "attr_speedLevel"}
					
		super(service_HumidifierDehumidifier, self).setAttributes ()				
				
		if objId != 0: self.logger.debug (u'{} started as a HomeKit {}'.format(self.alias.value, self.desc))		

# ==============================================================================
# HUMIDITY SENSOR
# ==============================================================================
class service_HumiditySensor (Service):

	#
	# Initialize the class
	#
	def __init__ (self, factory, objId, serverId = 0, characterDict = {}, deviceActions = [], loadOptional = False):
		type = "HumiditySensor"
		desc = "Humidity Sensor"
	
		super(service_HumiditySensor, self).__init__ (factory, type, desc, objId, serverId, characterDict, deviceActions, loadOptional)
		
		self.required = {}
		self.required["CurrentRelativeHumidity"] = {"*": "attr_sensorValue", "indigo.ThermostatDevice": "state_humidityInput1", "indigo.Device.com.fogbert.indigoplugin.wunderground.wunderground": "state_relativeHumidity", "indigo.Device.com.karlwachs.piBeacon.i2cBMExx": "state_Humidity"}
	
		self.optional = {}
		self.optional["StatusActive"] = {}
		self.optional["StatusFault"] = {}
		self.optional["StatusTampered"] = {}
		self.optional["StatusLowBattery"] = {"*": "special_lowbattery"}
		self.optional["Name"] = {}
					
		super(service_HumiditySensor, self).setAttributes ()				
				
		if objId != 0: self.logger.debug (u'{} started as a HomeKit {}'.format(self.alias.value, self.desc))		
		
		
# ==============================================================================
# IRRIGATION SYSTEM
# ==============================================================================
class service_IrrigationSystem (Service):

	#
	# Initialize the class
	#
	def __init__ (self, factory, objId, serverId = 0, characterDict = {}, deviceActions = [], loadOptional = False):
		type = "IrrigationSystem"
		desc = "Irrigation System"
		
		self.wiki = "This service will automatically refresh back to HomeKit every 5 seconds if it is connected to an Indigo irrigation controller and if the controller has an active zone running so it can inform HomeKit of the number of remaining seconds left on the __current zone__."
	
		super(service_IrrigationSystem, self).__init__ (factory, type, desc, objId, serverId, characterDict, deviceActions, loadOptional)
		
		self.required = {}
		self.required["Active"] = {"*": "attr_onState", "indigo.SprinklerDevice": "state_activeZone"}
		self.required["ProgramMode"] = {"*": "special_sprinklerProgramMode"}
		self.required["InUse"] = {"*": "attr_onState", "indigo.SprinklerDevice": "state_activeZone"}
	
		self.optional = {}
		self.optional["RemainingDuration"] = {"indigo.SprinklerDevice": "special_sprinklerRemainingDuration"} #- maybe in the future, need to create an ongoing scheduled update to HomeKit for this to be effective
		self.optional["StatusFault"] = {}
		self.optional["Name"] = {}
					
		super(service_IrrigationSystem, self).setAttributes ()				
		
		if objId != 0: self.logger.debug (u'{} started as a HomeKit {}'.format(self.alias.value, self.desc))	
				

# ==============================================================================
# LEAK SENSOR
# ==============================================================================
class service_LeakSensor (Service):

	#
	# Initialize the class
	#
	def __init__ (self, factory, objId, serverId = 0, characterDict = {}, deviceActions = [], loadOptional = False):
		type = "LeakSensor"
		desc = "Leak Sensor"
	
		super(service_LeakSensor, self).__init__ (factory, type, desc, objId, serverId, characterDict, deviceActions, loadOptional)
		
		self.required = {}
		self.required["LeakDetected"] = {"*": "attr_onState"}
	
		self.optional = {}
		self.optional["StatusActive"] = {}
		self.optional["StatusFault"] = {}
		self.optional["StatusTampered"] = {}
		self.optional["StatusLowBattery"] = {"*": "special_lowbattery"}
		self.optional["Name"] = {}
					
		super(service_LeakSensor, self).setAttributes ()				
				
		if objId != 0: self.logger.debug (u'{} started as a HomeKit {}'.format(self.alias.value, self.desc))		
		
# ==============================================================================
# LIGHT BULB
# ==============================================================================
class service_Lightbulb (Service):

	#
	# Initialize the class
	#
	def __init__ (self, factory, objId, serverId = 0, characterDict = {}, deviceActions = [], loadOptional = False):
		type = "Lightbulb"
		desc = "Lightbulb"
	
		super(service_Lightbulb, self).__init__ (factory, type, desc, objId, serverId, characterDict, deviceActions, loadOptional)
		
		self.required = {}
		self.required["On"] = {"*": "attr_onState", "indigo.ThermostatDevice": "attr_fanIsOn", "indigo.MultiIODevice": "state_binaryOutput1", "indigo.SprinklerDevice": "activeZone", "indigo.Device.com.perceptiveautomation.indigoplugin.airfoilpro.speaker": "state_status.connected", "indigo.Device.com.pennypacker.indigoplugin.senseme.SenseME_fan": "special_SenseMeLightToggle"}
	
		self.optional = {}
		self.optional["Brightness"] = {"indigo.DimmerDevice": "attr_brightness", "indigo.SpeedControlDevice": "attr_speedLevel", "indigo.Device.com.perceptiveautomation.indigoplugin.airfoilpro.speaker": "state_volume", "indigo.Device.com.pennypacker.indigoplugin.senseme.SenseME_fan": "special_SenseMeLightLevel"}
		self.optional["Hue"] = {"indigo.DimmerDevicexxx": "special_HSL", "indigo.DimmerDevice.com.nathansheldon.indigoplugin.HueLights.hueBulb": "state_hue", "indigo.DimmerDevice.com.autologplugin.indigoplugin.lifxcontroller.lifxDevice": "state_hsbkHue"}
		self.optional["Saturation"] = {"indigo.DimmerDevicexxx": "special_HSL", "indigo.DimmerDevice.com.nathansheldon.indigoplugin.HueLights.hueBulb": "state_saturation", "indigo.DimmerDevice.com.autologplugin.indigoplugin.lifxcontroller.lifxDevice": "state_hsbkSaturation"}
		self.optional["Name"] = {}
		self.optional["ColorTemperature"] = {"indigo.DimmerDevicexxx": "special_HSL", "indigo.DimmerDevice.com.nathansheldon.indigoplugin.HueLights.hueBulb": "state_colorTemp", "indigo.DimmerDevice.com.autologplugin.indigoplugin.lifxcontroller.lifxDevice": "state_hsbkKelvin"}
					
		super(service_Lightbulb, self).setAttributes ()					
				
		if objId != 0: self.logger.debug (u'{} started as a HomeKit {}'.format(self.alias.value, self.desc))			
		
# ==============================================================================
# LIGHT SENSOR
# ==============================================================================
class service_LightSensor (Service):

	#
	# Initialize the class
	#
	def __init__ (self, factory, objId, serverId = 0, characterDict = {}, deviceActions = [], loadOptional = False):
		type = "LightSensor"
		desc = "Light Sensor"
	
		super(service_LightSensor, self).__init__ (factory, type, desc, objId, serverId, characterDict, deviceActions, loadOptional)
		
		self.required = {}
		self.required["CurrentAmbientLightLevel"] = {"*": "attr_sensorValue"}
	
		self.optional = {}
		self.optional["StatusActive"] = {}
		self.optional["StatusFault"] = {}
		self.optional["StatusTampered"] = {}
		self.optional["StatusLowBattery"] = {"*": "special_lowbattery"}
		self.optional["Name"] = {}
					
		super(service_LightSensor, self).setAttributes ()				
				
		if objId != 0: self.logger.debug (u'{} started as a HomeKit {}'.format(self.alias.value, self.desc))				
		
# ==============================================================================
# MICROPHONE
# ==============================================================================
class service_Microphone (Service):

	#
	# Initialize the class
	#
	def __init__ (self, factory, objId, serverId = 0, characterDict = {}, deviceActions = [], loadOptional = False):
		type = "Microphone"
		desc = "Microphone (3rd Party and Siri Only)"
		
		self.wiki = "This service is unsupported by the native Apple Home application but is supported, in varying degrees, in 3rd party HomeKit apps.  Apps tested with this service that work are the [non-Apple version of Home](https://itunes.apple.com/us/app/home-smart-home-automation/id995994352?mt=8) and [Elgato Eve](https://itunes.apple.com/us/app/elgato-eve/id917695792?mt=8)."
	
		super(service_Microphone, self).__init__ (factory, type, desc, objId, serverId, characterDict, deviceActions, loadOptional)
		
		self.required = {}
		self.required["Mute"] = {"*": "attr_onState", "indigo.Device.com.perceptiveautomation.indigoplugin.airfoilpro.speaker": "state_status.disconnected"}
	
		self.optional = {}
		self.optional["Volume"] = {"*": "attr_brightness", "indigo.Device.com.perceptiveautomation.indigoplugin.airfoilpro.speaker": "state_volume"}
		self.optional["Name"] = {}
					
		super(service_Microphone, self).setAttributes ()	
				
		if objId != 0: self.logger.debug (u'{} started as a HomeKit {}'.format(self.alias.value, self.desc))			
		
# ==============================================================================
# MOTION SENSOR
# ==============================================================================
class service_MotionSensor (Service):

	#
	# Initialize the class
	#
	def __init__ (self, factory, objId, serverId = 0, characterDict = {}, deviceActions = [], loadOptional = False):
		type = "MotionSensor"
		desc = "Motion Sensor"
	
		super(service_MotionSensor, self).__init__ (factory, type, desc, objId, serverId, characterDict, deviceActions, loadOptional)
		
		self.required = {}
		self.required["MotionDetected"] = {"*": "attr_onState", "indigo.ThermostatDevice": "attr_fanIsOn", "indigo.MultiIODevice": "state_binaryOutput1", "indigo.SprinklerDevice": "activeZone", "indigo.Device.com.frightideas.indigoplugin.dscAlarm.alarmZone": "state_state.open", "indigo.Device.org.cynic.indigo.securityspy.camera": "state_motion"}
	
		self.optional = {}
		self.optional["StatusActive"] = {}
		self.optional["StatusFault"] = {}
		self.optional["StatusTampered"] = {}
		self.optional["StatusLowBattery"] = {"*": "special_lowbattery"}
		self.optional["Name"] = {}
					
		super(service_MotionSensor, self).setAttributes ()				
				
		if objId != 0: self.logger.debug (u'{} started as a HomeKit {}'.format(self.alias.value, self.desc))			
		
# ==============================================================================
# OCCUPANCY SENSOR
# ==============================================================================
class service_OccupancySensor (Service):

	#
	# Initialize the class
	#
	def __init__ (self, factory, objId, serverId = 0, characterDict = {}, deviceActions = [], loadOptional = False):
		type = "OccupancySensor"
		desc = "Occupancy Sensor"
	
		super(service_OccupancySensor, self).__init__ (factory, type, desc, objId, serverId, characterDict, deviceActions, loadOptional)
		
		self.required = {}
		self.required["OccupancyDetected"] = {"*": "attr_onState", "indigo.ThermostatDevice": "attr_fanIsOn", "indigo.MultiIODevice": "state_binaryOutput1", "indigo.SprinklerDevice": "activeZone", "indigo.Device.com.frightideas.indigoplugin.dscAlarm.alarmZone": "state_state.open", "indigo.Device.com.karlwachs.piBeacon.beacon": "special_piBeaconStatus"}
	
		self.optional = {}
		self.optional["StatusActive"] = {}
		self.optional["StatusFault"] = {}
		self.optional["StatusTampered"] = {}
		self.optional["StatusLowBattery"] = {"*": "special_lowbattery"}
		self.optional["Name"] = {}
					
		super(service_OccupancySensor, self).setAttributes ()				
				
		if objId != 0: self.logger.debug (u'{} started as a HomeKit {}'.format(self.alias.value, self.desc))				
		
# ==============================================================================
# OUTLET
# ==============================================================================
class service_Outlet (Service):

	#
	# Initialize the class
	#
	def __init__ (self, factory, objId, serverId = 0, characterDict = {}, deviceActions = [], loadOptional = False):
		type = "Outlet"
		desc = "Outlet"
	
		super(service_Outlet, self).__init__ (factory, type, desc, objId, serverId, characterDict, deviceActions, loadOptional)
		
		self.required = {}
		self.required["On"] = {"*": "attr_onState", "indigo.ThermostatDevice": "attr_fanIsOn", "indigo.MultiIODevice": "state_binaryOutput1", "indigo.SprinklerDevice": "activeZone"}
		self.required["OutletInUse"] = {"*": "special_inuse"}
	
		self.optional = {}
					
		super(service_Outlet, self).setAttributes ()							
				
		if objId != 0: self.logger.debug (u'{} started as a HomeKit {}'.format(self.alias.value, self.desc))			
		
# ==============================================================================
# LOCK MECHANISM
# ==============================================================================
class service_LockMechanism (Service):

	#
	# Initialize the class
	#
	def __init__ (self, factory, objId, serverId = 0, characterDict = {}, deviceActions = [], loadOptional = False):
		type = "LockMechanism"
		desc = "Lock Mechanism"
	
		super(service_LockMechanism, self).__init__ (factory, type, desc, objId, serverId, characterDict, deviceActions, loadOptional)
		
		self.required = {}
		self.required["LockCurrentState"] = {"*": "attr_onState", "indigo.ThermostatDevice": "attr_fanIsOn", "indigo.MultiIODevice": "state_binaryOutput1", "indigo.SprinklerDevice": "activeZone", "indigo.Device.com.frightideas.indigoplugin.dscAlarm.alarmZone": "state_state.open"}
		self.required["LockTargetState"] = {"*": "attr_onState", "indigo.ThermostatDevice": "attr_fanIsOn", "indigo.MultiIODevice": "state_binaryOutput1", "indigo.SprinklerDevice": "activeZone", "indigo.Device.com.frightideas.indigoplugin.dscAlarm.alarmZone": "state_state.open"}
	
		self.optional = {}
		self.optional["Name"] = {}
					
		super(service_LockMechanism, self).setAttributes ()					
				
		if objId != 0: self.logger.debug (u'{} started as a HomeKit {}'.format(self.alias.value, self.desc))		
		
# ==============================================================================
# SECURITY SYSTEM
# ==============================================================================
class service_SecuritySystem (Service):

	#
	# Initialize the class
	#
	def __init__ (self, factory, objId, serverId = 0, characterDict = {}, deviceActions = [], loadOptional = False):
		type = "SecuritySystem"
		desc = "Security System"
		
		super(service_SecuritySystem, self).__init__ (factory, type, desc, objId, serverId, characterDict, deviceActions, loadOptional)
		
		self.required = {}
		self.required["SecuritySystemCurrentState"] = {"*": "attr_onState", "indigo.Device.com.frightideas.indigoplugin.dscAlarm.alarmKeypad": "special_dscKeypadState"}
		self.required["SecuritySystemTargetState"] = {"*": "attr_onState", "indigo.Device.com.frightideas.indigoplugin.dscAlarm.alarmKeypad": "special_dscKeypadState"}

		self.optional = {}
		self.optional["StatusFault"] = {}
		self.optional["StatusTampered"] = {}
		self.optional["SecuritySystemAlarmType"] = {}
		self.optional["Name"] = {}
					
		super(service_SecuritySystem, self).setAttributes ()			
						
		if objId != 0: self.logger.debug (u'{} started as a HomeKit {}'.format(self.alias.value, self.desc))			
		
# ==============================================================================
# SLAT
# ==============================================================================
class service_Slat (Service):

	#
	# Initialize the class
	#
	def __init__ (self, factory, objId, serverId = 0, characterDict = {}, deviceActions = [], loadOptional = False):
		type = "Slat"
		desc = "Slat (3rd Party and Siri Only)"
		
		self.wiki = "This service is unsupported by the native Apple Home application but is supported, in varying degrees, in 3rd party HomeKit apps.  Apps tested with this service that work are the [non-Apple version of Home](https://itunes.apple.com/us/app/home-smart-home-automation/id995994352?mt=8) and [Elgato Eve](https://itunes.apple.com/us/app/elgato-eve/id917695792?mt=8)."
		
		super(service_Slat, self).__init__ (factory, type, desc, objId, serverId, characterDict, deviceActions, loadOptional)
		
		self.required = {}
		self.required["SlatType"] = {}
		self.required["CurrentSlatState"] = {"*": "attr_onState"}

		self.optional = {}
		self.optional["CurrentTiltAngle"] = {}
		self.optional["TargetTiltAngle"] = {}
		self.optional["SwingMode"] = {}
		self.optional["Name"] = {}
					
		super(service_Slat, self).setAttributes ()			
						
		if objId != 0: self.logger.debug (u'{} started as a HomeKit {}'.format(self.alias.value, self.desc))				
		
# ==============================================================================
# SMOKE SENSOR
# ==============================================================================
class service_SmokeSensor (Service):

	#
	# Initialize the class
	#
	def __init__ (self, factory, objId, serverId = 0, characterDict = {}, deviceActions = [], loadOptional = False):
		type = "SmokeSensor"
		desc = "Smoke Sensor"
	
		super(service_SmokeSensor, self).__init__ (factory, type, desc, objId, serverId, characterDict, deviceActions, loadOptional)
		
		self.required = {}
		self.required["SmokeDetected"] = {"*": "attr_onState", "indigo.Device.com.frightideas.indigoplugin.dscAlarm.alarmZone": "state_state.open", "indigo.Device.com.frightideas.indigoplugin.dscAlarm.alarmZone": "state_state.open"}
	
		self.optional = {}
		self.optional["StatusActive"] = {}
		self.optional["StatusFault"] = {}
		self.optional["StatusTampered"] = {}
		self.optional["StatusLowBattery"] = {"*": "special_lowbattery"}
		self.optional["Name"] = {}
					
		super(service_SmokeSensor, self).setAttributes ()				
				
		if objId != 0: self.logger.debug (u'{} started as a HomeKit {}'.format(self.alias.value, self.desc))										

# ==============================================================================
# SPEAKER
# ==============================================================================
class service_Speaker (Service):

	#
	# Initialize the class
	#
	def __init__ (self, factory, objId, serverId = 0, characterDict = {}, deviceActions = [], loadOptional = False):
		type = "Speaker"
		desc = "Speaker (3rd Party and Siri Only)"
		
		self.wiki = "This service is unsupported by the native Apple Home application but is supported, in varying degrees, in 3rd party HomeKit apps.  Apps tested with this service that work are the [non-Apple version of Home](https://itunes.apple.com/us/app/home-smart-home-automation/id995994352?mt=8) and [Elgato Eve](https://itunes.apple.com/us/app/elgato-eve/id917695792?mt=8)."
	
		super(service_Speaker, self).__init__ (factory, type, desc, objId, serverId, characterDict, deviceActions, loadOptional)
		
		self.required = {}
		self.required["Mute"] = {"*": "attr_onState", "indigo.Device.com.perceptiveautomation.indigoplugin.airfoilpro.speaker": "state_status.disconnected"}
	
		self.optional = {}
		self.optional["Volume"] = {"*": "attr_brightness", "indigo.Device.com.perceptiveautomation.indigoplugin.airfoilpro.speaker": "state_volume"}
		self.optional["Name"] = {}
					
		super(service_Speaker, self).setAttributes ()	
				
		if objId != 0: self.logger.debug (u'{} started as a HomeKit {}'.format(self.alias.value, self.desc))	
		
# ==============================================================================
# SWITCH
# ==============================================================================
class service_Switch (Service):

	#
	# Initialize the class
	#
	def __init__ (self, factory, objId, serverId = 0, characterDict = {}, deviceActions = [], loadOptional = False):
		type = "Switch"
		desc = "Switch"
	
		super(service_Switch, self).__init__ (factory, type, desc, objId, serverId, characterDict, deviceActions, loadOptional)
		
		self.required = {}
		self.required["On"] = {"*": "attr_onState", "indigo.ThermostatDevice": "attr_fanIsOn", "indigo.MultiIODevice": "state_binaryOutput1", "indigo.SprinklerDevice": "activeZone", "indigo.Device.com.frightideas.indigoplugin.dscAlarm.alarmZone": "state_state.open", "indigo.Device.org.cynic.indigo.securityspy.camera": "state_recording"}
	
		self.optional = {}
					
		super(service_Switch, self).setAttributes ()	
				
		if objId != 0: self.logger.debug (u'{} started as a HomeKit {}'.format(self.alias.value, self.desc))			
		
# ==============================================================================
# TEMPERATURE SENSOR
# ==============================================================================
class service_TemperatureSensor (Service):

	#
	# Initialize the class
	#
	def __init__ (self, factory, objId, serverId = 0, characterDict = {}, deviceActions = [], loadOptional = False):
		type = "TemperatureSensor"
		desc = "Temperature Sensor"
	
		super(service_TemperatureSensor, self).__init__ (factory, type, desc, objId, serverId, characterDict, deviceActions, loadOptional)
		
		self.required = {}
		#self.required["CurrentTemperature"] = {"indigo.SensorDevice": "special_sensorTemperature", "indigo.Device.com.fogbert.indigoplugin.wunderground.wunderground": "special_wuTemperature", "indigo.ThermostatDevice": "special_thermTemperature", "indigo.Device.com.perceptiveautomation.indigoplugin.weathersnoop.ws3station": "special_wsTemperature"}
		self.required["CurrentTemperature"] = {"indigo.SensorDevice": "attr_sensorValue", "indigo.Device.com.fogbert.indigoplugin.wunderground.wunderground": "state_temp", "indigo.ThermostatDevice": "state_temperatureInput1", "indigo.Device.com.perceptiveautomation.indigoplugin.weathersnoop.ws3station": "state_temperature_F", "indigo.Device.com.karlwachs.piBeacon.i2cTMP102": "state_Temperature", "indigo.Device.com.karlwachs.piBeacon.i2cBMExx": "state_Temperature", "indigo.Device.com.karlwachs.piBeacon.i2cMS5803": "state_Temperature"}
	
		self.optional = {}
		self.optional["StatusActive"] = {}
		self.optional["StatusFault"] = {}
		self.optional["StatusTampered"] = {}
		self.optional["StatusLowBattery"] = {"*": "special_lowbattery"}
		self.optional["Name"] = {}
					
		super(service_TemperatureSensor, self).setAttributes ()				
				
		if objId != 0: self.logger.debug (u'{} started as a HomeKit {}'.format(self.alias.value, self.desc))					
		
# ==============================================================================
# THERMOSTAT
# ==============================================================================
class service_Thermostat (Service):

	#
	# Initialize the class
	#
	def __init__ (self, factory, objId, serverId = 0, characterDict = {}, deviceActions = [], loadOptional = False):
		type = "Thermostat"
		desc = "Thermostat"
	
		super(service_Thermostat, self).__init__ (factory, type, desc, objId, serverId, characterDict, deviceActions, loadOptional)
		
		self.required = {}
		self.required["CurrentHeatingCoolingState"] = {"indigo.ThermostatDevice": "special_thermHVACMode", "indigo.ThermostatDevice.com.corporatechameleon.nestplugBeta.nestThermostat": "special_nestHvacMode"}
		self.required["TargetHeatingCoolingState"] = {"indigo.ThermostatDevice": "special_thermHVACModeSet"}
		#self.required["CurrentTemperature"] = {"indigo.ThermostatDevice": "special_thermTemperature"}
		self.required["CurrentTemperature"] = {"indigo.ThermostatDevice": "state_temperatureInput1"}
		self.required["TargetTemperature"] = {"indigo.ThermostatDevice": "special_thermTemperatureSetPoint"}
		#self.required["TargetTemperature"] = {"indigo.ThermostatDevice": "state_temperatureInput1"}
		self.required["TemperatureDisplayUnits"] = {"indigo.ThermostatDevice": "special_serverCorFSetting"}
	
		self.optional = {}
		self.optional["CurrentRelativeHumidity"] = {"indigo.ThermostatDevice": "state_humidityInput1"}
		self.optional["TargetRelativeHumidity"] = {}
		#self.optional["CoolingThresholdTemperature"] = {"indigo.ThermostatDevice": "special_thermCoolSet"}
		#self.optional["HeatingThresholdTemperature"] = {"indigo.ThermostatDevice": "special_thermHeatSet"}
		self.optional["CoolingThresholdTemperature"] = {"indigo.ThermostatDevice": "attr_coolSetpoint"}
		self.optional["HeatingThresholdTemperature"] = {"indigo.ThermostatDevice": "attr_heatSetpoint"}
		self.optional["Name"] = {}
					
		super(service_Thermostat, self).setAttributes ()	
				
		if objId != 0: self.logger.debug (u'{} started as a HomeKit {}'.format(self.alias.value, self.desc))			
		
		
# ==============================================================================
# VALVE
# ==============================================================================
class service_Valve (Service):

	#
	# Initialize the class
	#
	def __init__ (self, factory, objId, serverId = 0, characterDict = {}, deviceActions = [], loadOptional = False):
		type = "Valve"
		desc = "Valve"
		
		self.wiki = "This service is unsupported by the native Apple Home application but is supported, in varying degrees, in 3rd party HomeKit apps.  Apps tested with this service that work are the [non-Apple version of Home](https://itunes.apple.com/us/app/home-smart-home-automation/id995994352?mt=8) and [Elgato Eve](https://itunes.apple.com/us/app/elgato-eve/id917695792?mt=8)."
		
		super(service_Valve, self).__init__ (factory, type, desc, objId, serverId, characterDict, deviceActions, loadOptional)
		
		self.required = {}
		self.required["Active"] = {"*": "attr_onState"}
		self.required["InUse"] = {"*": "attr_onState"}
		self.required["ValveType"] = {}

		self.optional = {}
		self.optional["SetDuration"] = {}
		self.optional["RemainingDuration"] = {}
		self.optional["IsConfigured"] = {}
		self.optional["ServiceLabelIndex"] = {}
		self.optional["StatusFault"] = {}
		self.optional["Name"] = {}
					
		super(service_Valve, self).setAttributes ()			
						
		if objId != 0: self.logger.debug (u'{} started as a HomeKit {}'.format(self.alias.value, self.desc))		
				

# ==============================================================================
# WINDOW
# ==============================================================================
class service_Window (Service):

	#
	# Initialize the class
	#
	def __init__ (self, factory, objId, serverId = 0, characterDict = {}, deviceActions = [], loadOptional = False):
		type = "Window"
		desc = "Window"
	
		super(service_Window, self).__init__ (factory, type, desc, objId, serverId, characterDict, deviceActions, loadOptional)
		
		self.required = {}
		self.required["CurrentPosition"] = {"*": "attr_brightness", "indigo.RelayDevice": "special_onStateToFullBrightness"}
		self.required["PositionState"] = {}
		self.required["TargetPosition"] = {"*": "attr_brightness", "indigo.RelayDevice": "special_onStateToFullBrightness"}
	
		self.optional = {}
		self.optional["HoldPosition"] = {}
		self.optional["ObstructionDetected"] = {}
		self.optional["Name"] = {}
					
		super(service_Window, self).setAttributes ()			
						
		if objId != 0: self.logger.debug (u'{} started as a HomeKit {}'.format(self.alias.value, self.desc))		
		
# ==============================================================================
# WINDOW COVERING
# ==============================================================================
class service_WindowCovering (Service):

	#
	# Initialize the class
	#
	def __init__ (self, factory, objId, serverId = 0, characterDict = {}, deviceActions = [], loadOptional = False):
		type = "WindowCovering"
		desc = "Window Covering"
	
		super(service_WindowCovering, self).__init__ (factory, type, desc, objId, serverId, characterDict, deviceActions, loadOptional)
		
		self.required = {}
		self.required["CurrentPosition"] = {"*": "attr_brightness","indigo.RelayDevice": "special_onStateToFullBrightness"}
		self.required["PositionState"] = {}
		self.required["TargetPosition"] = {"*": "attr_brightness","indigo.RelayDevice": "special_onStateToFullBrightness"}
	
		self.optional = {}
		self.optional["HoldPosition"] = {}
		self.optional["TargetHorizontalTiltAngle"] = {}
		self.optional["TargetVerticalTiltAngle"] = {}
		self.optional["CurrentHorizontalTiltAngle"] = {}
		self.optional["CurrentVerticalTiltAngle"] = {}
		self.optional["ObstructionDetected"] = {}
		self.optional["Name"] = {}
					
		super(service_WindowCovering, self).setAttributes ()			
						
		if objId != 0: self.logger.debug (u'{} started as a HomeKit {}'.format(self.alias.value, self.desc))			
		
################################################################################
# HOMEKIT CHARACTERISTICS
#
# 
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
		self.validValuesStr = "[active, inactive]"
		
		self.readonly = False
		self.notify = True
		self.changeMinMax = False
		
# ==============================================================================
# BATTERY LEVEL
# ==============================================================================
class characteristic_BatteryLevel:
	def __init__(self):
		self.value = 0
		self.maxValue = 100
		self.minValue = 0
		self.minStep = 1
		
		self.readonly = True
		self.notify = True
		self.changeMinMax = False	
		
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
		self.changeMinMax = False
		
# ==============================================================================
# CARBON DIOXIDE DETECTED
# ==============================================================================
class characteristic_CarbonDioxideDetected:	
	def __init__(self):
		self.value = 0 
		self.maxValue = 1
		self.minValue = 0
		
		self.validValues = [0, 1]
		self.validValuesStr = "[levels normal, levels abnormal]"
		
		self.readonly = True
		self.notify = True	
		self.changeMinMax = False
		
# ==============================================================================
# CARBON DIOXIDE LEVEL
# ==============================================================================
class characteristic_CarbonDioxideLevel:
	def __init__(self):
		self.value = 0.0
		self.maxValue = 10000
		self.minValue = 0
		
		self.readonly = False
		self.notify = True	
		self.changeMinMax = False
		
# ==============================================================================
# CARBON DIOXIDE PEAK LEVEL
# ==============================================================================
class characteristic_CarbonDioxidePeakLevel:
	def __init__(self):
		self.value = 0.0
		self.maxValue = 10000
		self.minValue = 0
		
		self.readonly = False
		self.notify = True	
		self.changeMinMax = False		
		
# ==============================================================================
# CARBON MONOXIDE DETECTED
# ==============================================================================
class characteristic_CarbonMonoxideDetected:	
	def __init__(self):
		self.value = 0 
		self.maxValue = 1
		self.minValue = 0
		
		self.validValues = [0, 1]
		self.validValuesStr = "[levels normal, levels abnormal]"
		
		self.readonly = True
		self.notify = True	
		self.changeMinMax = False
		
# ==============================================================================
# CARBON MONOXIDE LEVEL
# ==============================================================================
class characteristic_CarbonMonoxideLevel:
	def __init__(self):
		self.value = 0.0
		self.maxValue = 100
		self.minValue = 0
		
		self.readonly = False
		self.notify = True	
		self.changeMinMax = False
		
# ==============================================================================
# CARBON MONOXIDE PEAK LEVEL
# ==============================================================================
class characteristic_CarbonMonoxidePeakLevel:
	def __init__(self):
		self.value = 0.0
		self.maxValue = 100
		self.minValue = 0
		
		self.readonly = False
		self.notify = True		
		self.changeMinMax = False				
		
# ==============================================================================
# CHARGING STATE
# ==============================================================================
class characteristic_ChargingState:	
	def __init__(self):
		self.value = 0 
		self.maxValue = 2
		self.minValue = 0
		
		self.validValues = [0, 1, 2]
		self.validValuesStr = "[not charging, charging, not chargable]"
		
		self.readonly = False
		self.notify = True		
		self.changeMinMax = False	
		
# ==============================================================================
# COLOR TEMPERATURE (Need to update homebridge/hap-nodejs/lib/gen/HomeKitTypes.js to extend this range)
# ==============================================================================		
class characteristic_ColorTemperature:
	def __init__(self):
		self.value = 140
		self.minValue = 140
		#self.maxValue = 500
		self.maxValue = 15000
		self.minStep = 1	
		
		self.readonly = False
		self.notify = True	
		self.changeMinMax = True
		
# ==============================================================================
# CONTACT SENSOR STATE
# ==============================================================================
class characteristic_ContactSensorState:	
	def __init__(self):
		self.value = 0 
		self.maxValue = 1
		self.minValue = 0
		
		self.validValues = [0, 1]
		self.validValuesStr = "[contact detected, contact not detected]"
		
		self.readonly = False
		self.notify = True		
		self.changeMinMax = False	
		
# ==============================================================================
# COOLING THRESHOLD TEMPERATURE
# ==============================================================================		
class characteristic_CoolingThresholdTemperature:
	def __init__(self):
		self.value = 0.0
		self.maxValue = 35
		self.minValue = 10
		self.minStep = 0.1

		self.readonly = False
		self.notify = True		
		self.changeMinMax = False	
		
# ==============================================================================
# CURRENT AMBIENT LIGHT LEVEL
# ==============================================================================		
class characteristic_CurrentAmbientLightLevel:
	def __init__(self):
		self.value = 0.0
		self.maxValue = 100
		self.minValue = 0.0001
		self.minStep = 0.0001

		self.readonly = True
		self.notify = True		
		self.changeMinMax = False	
	
# ==============================================================================
# CURRENT AIR PURIFIER STATE
# ==============================================================================
class characteristic_CurrentAirPurifierState:	
	def __init__(self):
		self.value = 0 # open [closed, opening, closing, stopped]
		self.maxValue = 2
		self.minValue = 0
		
		self.validValues = [0, 1, 2]
		self.validValuesStr = "[inactive, idle, purifying air]"
		
		self.readonly = True
		self.notify = True		
		self.changeMinMax = False	
				
# ==============================================================================
# CURRENT DOOR STATE
# ==============================================================================
class characteristic_CurrentDoorState:	
	def __init__(self):
		self.value = 0 # open [closed, opening, closing, stopped]
		self.maxValue = 4
		self.minValue = 0
		
		self.validValues = [0, 1, 2, 3, 4]
		self.validValuesStr = "[open, closed, opening, closing, stopped]"
		
		self.readonly = True
		self.notify = True		
		self.changeMinMax = False	
		
# ==============================================================================
# CURRENT FAN STATE
# ==============================================================================
class characteristic_CurrentFanState:	
	def __init__(self):
		self.value = 0 # inactive [idle, blowing air]
		self.maxValue = 2
		self.minValue = 0
		
		self.validValues = [0, 1, 2]
		self.validValuesStr = "[inactive, idle, blowing air]"
		
		self.readonly = True
		self.notify = True	
		self.changeMinMax = False	
		
# ==============================================================================
# CURRENT HEATING/COOLING STATE
# ==============================================================================
class characteristic_CurrentHeatingCoolingState:	
	def __init__(self):
		self.value = 0 # off [heat, cool]
		self.maxValue = 2
		self.minValue = 0
		
		self.validValues = [0, 1, 2]
		self.validValuesStr = "[off, heat cool]"
		
		self.readonly = True
		self.notify = True		
		self.changeMinMax = False
		
# ==============================================================================
# CURRENT HEATER/COOLER STATE
# ==============================================================================
class characteristic_CurrentHeaterCoolerState:	
	def __init__(self):
		self.value = 1
		self.maxValue = 3
		self.minValue = 0
		
		self.validValues = [0, 1, 2, 3]
		self.validValuesStr = "[inactive, idle, heating, cooling]"
		
		self.readonly = True
		self.notify = True	
		self.changeMinMax = False		
		
# ==============================================================================
# CURRENT HORIZONTAL TILT ANGLE
# ==============================================================================		
class characteristic_CurrentHorizontalTiltAngle:
	def __init__(self):
		self.value = 0
		self.maxValue = 90
		self.minValue = -90
		self.minStep = 1

		self.readonly = True
		self.notify = True	
		self.changeMinMax = False
		
# ==============================================================================
# CURRENT HUMIDIFIER / DEHUMIDIFIER STATE
# ==============================================================================
class characteristic_CurrentHumidifierDehumidifierState:	
	def __init__(self):
		self.value = 0 
		self.maxValue = 3
		self.minValue = 0
		
		self.validValues = [0, 1, 2, 3]
		self.validValuesStr = "[inactive, idle, humidifying, dehumidifying]"
		
		self.readonly = True
		self.notify = True	
		self.changeMinMax = False			
		
# ==============================================================================
# CURRENT POSITION
# ==============================================================================		
class characteristic_CurrentPosition:
	def __init__(self):
		self.value = 0
		self.maxValue = 100
		self.minValue = 0
		self.minStep = 1

		self.readonly = True
		self.notify = True	
		self.changeMinMax = False		
		
# ==============================================================================
# CURRENT RELATIVE HUMIDITY
# ==============================================================================		
class characteristic_CurrentRelativeHumidity:
	def __init__(self):
		self.value = 0.0
		self.maxValue = 100
		self.minValue = 0
		self.minStep = 1

		self.readonly = True
		self.notify = True		
		self.changeMinMax = False
		
# ==============================================================================
# CURRENT SLAT STATE
# ==============================================================================
class characteristic_CurrentSlatState:	
	def __init__(self):
		self.value = 0 
		self.maxValue = 2
		self.minValue = 0
		
		self.validValues = [0, 1, 2]
		self.validValuesStr = "[fixed, jammed, swinging]"
		
		self.readonly = False
		self.notify = True		
		self.changeMinMax = False		
		
# ==============================================================================
# CURRENT TEMPERATURE (Need to update homebridge/hap-nodejs/lib/gen/HomeKitTypes.js to extend this range)
# ==============================================================================		
class characteristic_CurrentTemperature:
	def __init__(self):
		self.value = 0.0
		#self.maxValue = 100
		self.maxValue = 500
		#self.minValue = 0
		self.minValue = -100
		self.minStep = 0.1

		self.readonly = True
		self.notify = True	
		self.changeMinMax = True
		
# ==============================================================================
# CURRENT TILT ANGLE
# ==============================================================================		
class characteristic_CurrentVerticalTiltAngle:
	def __init__(self):
		self.value = 0
		self.maxValue = 90
		self.minValue = -90
		self.minStep = 1

		self.readonly = True
		self.notify = True			
		self.changeMinMax = False	
		
# ==============================================================================
# CURRENT VERTICAL TILT ANGLE
# ==============================================================================		
class characteristic_CurrentVerticalTiltAngle:
	def __init__(self):
		self.value = 0
		self.maxValue = 90
		self.minValue = -90
		self.minStep = 1

		self.readonly = True
		self.notify = True		
		self.changeMinMax = False		
		
# ==============================================================================
# FILTER CHANGE INDICATION
# ==============================================================================
class characteristic_FilterChangeIndication:	
	def __init__(self):
		self.value = 0 
		self.maxValue = 1
		self.minValue = 0
		
		self.validValues = [0, 1]
		self.validValuesStr = "[filter OK, change filter]"
		
		self.readonly = False
		self.notify = True	
		self.changeMinMax = False	
		
# ==============================================================================
# FILTER LIFE LEVEL
# ==============================================================================		
class characteristic_FilterLifeLevel:
	def __init__(self):
		self.value = 0.0
		self.maxValue = 100
		self.minValue = 0
		self.minStep = 1

		self.readonly = True
		self.notify = True	
		self.changeMinMax = False			
		
# ==============================================================================
# HEATING THRESHOLD TEMPERATURE
# ==============================================================================		
class characteristic_HeatingThresholdTemperature:
	def __init__(self):
		self.value = 0.0
		self.maxValue = 25
		self.minValue = 0
		self.minStep = 0.1

		self.readonly = False
		self.notify = True	
		self.changeMinMax = False
		
# ==============================================================================
# HOLD POSITION
# ==============================================================================
class characteristic_HoldPosition:
	def __init__(self):
		self.value = True
		
		self.validValues = [True, False]
		
		self.readonly = True
		self.notify = False	
		self.changeMinMax = False				
		
# ==============================================================================
# HUE
# ==============================================================================		
class characteristic_Hue:
	def __init__(self):
		self.value = 0.0
		self.maxValue = 360.0
		self.minValue = 0.0
		self.minStep = 1
		
		self.readonly = False
		self.notify = True
		self.changeMinMax = False
		
# ==============================================================================
# IN USE
# ==============================================================================
class characteristic_InUse:	
	def __init__(self):
		self.value = 0 
		self.maxValue = 1
		self.minValue = 0
		
		self.validValues = [0, 1]
		self.validValuesStr = "[not in use, in use]"
		
		self.readonly = True
		self.notify = True		
		self.changeMinMax = False
		
# ==============================================================================
# IS CONFIGURED
# ==============================================================================
class characteristic_IsConfigured:	
	def __init__(self):
		self.value = 0 
		self.maxValue = 1
		self.minValue = 0
		
		self.validValues = [0, 1]
		self.validValuesStr = "[not configured, is configured]"
		
		self.readonly = False
		self.notify = True			
		self.changeMinMax = False	
		
# ==============================================================================
# LEAK DETECTED
# ==============================================================================
class characteristic_LeakDetected:	
	def __init__(self):
		self.value = 0 # clockwise [counter-clockwise]
		self.maxValue = 1
		self.minValue = 0
		
		self.validValues = [0, 1]
		self.validValuesStr = "[leak not detected, leak detected]"
		
		self.readonly = False
		self.notify = True		
		self.changeMinMax = False	
		
# ==============================================================================
# LOCK CURRENT STATE
# ==============================================================================
class characteristic_LockCurrentState:	
	def __init__(self):
		self.value = 0 # Unsecured [Secured, Jammed, Unknown]
		self.maxValue = 3
		self.minValue = 0
		
		self.validValues = [0, 1, 2, 3]		
		self.validValuesStr = "[unsecured, secured, jammed, unknown]"
		
		self.readonly = True
		self.notify = True
		self.changeMinMax = False
		
# ==============================================================================
# LOCK PHYSICAL CONTROLS
# ==============================================================================
class characteristic_LockPhysicalControls:	
	def __init__(self):
		self.value = 0 # lock disabled [lock enabled]
		self.maxValue = 1
		self.minValue = 0
		
		self.validValues = [0, 1]
		self.validValuesStr = "[lock disabled, lock enabled]"
		
		self.readonly = False
		self.notify = True		
		self.changeMinMax = False
		
# ==============================================================================
# LOCK TARGET STATE
# ==============================================================================
class characteristic_LockTargetState:	
	def __init__(self):
		self.value = 0 # Unsecured [Secured]
		self.maxValue = 1
		self.minValue = 0
		
		self.validValues = [0, 1]	
		self.validValuesStr = "[unsecured, secured]"
		
		self.readonly = False
		self.notify = True		
		self.changeMinMax = False

# ==============================================================================
# MOTION DETECTED
# ==============================================================================
class characteristic_MotionDetected:
	def __init__(self):
		self.value = False
		
		self.validValues = [True, False]
		
		self.readonly = True
		self.notify = False	
		self.changeMinMax = False	
		
# ==============================================================================
# MUTE
# ==============================================================================
class characteristic_Mute:
	def __init__(self):
		self.value = False
		
		self.validValues = [True, False]
		
		self.readonly = False
		self.notify = False		
		self.changeMinMax = False		
		
# ==============================================================================
# NAME
# ==============================================================================		
class characteristic_Name:
	def __init__(self):
		self.value = u""	
		
		self.readonly = False
		self.notify = False
		self.changeMinMax = False
		
# ==============================================================================
# NITROGEN DIOXIDE DENSITY
# ==============================================================================
class characteristic_NitrogenDioxideDensity:	
	def __init__(self):
		self.value = 0.0 
		self.maxValue = 1000.0
		self.minValue = 0.0
		self.minStep = 1
		
		self.readonly = True
		self.notify = True	
		self.changeMinMax = False		
		
# ==============================================================================
# OCCUPANCY DETECTED
# ==============================================================================
class characteristic_OccupancyDetected:
	def __init__(self):
		self.value = False
		
		self.validValues = [True, False]
		
		self.readonly = True
		self.notify = False			
		self.changeMinMax = False
		
# ==============================================================================
# OBSTRUCTION DETECTED
# ==============================================================================
class characteristic_ObstructionDetected:	
	def __init__(self):
		self.value = False
		
		self.validValues = [True, False]
		
		self.readonly = True
		self.notify = False		
		self.changeMinMax = False		
		
# ==============================================================================
# ON
# ==============================================================================
class characteristic_On:
	def __init__(self):
		self.value = False
		
		self.validValues = [True, False]
		
		self.readonly = False
		self.notify = False	
		self.changeMinMax = False	
		
# ==============================================================================
# OUTLET IN USE
# ==============================================================================
class characteristic_OutletInUse:
	def __init__(self):
		self.value = False
		
		self.validValues = [True, False]	
		
		self.readonly = True
		self.notify = True		
		self.changeMinMax = False
		
# ==============================================================================
# OZONE DENSITY
# ==============================================================================
class characteristic_OzoneDensity:	
	def __init__(self):
		self.value = 0.0 
		self.maxValue = 1000.0
		self.minValue = 0.0
		self.minStep = 1
		
		self.readonly = True
		self.notify = True	
		self.changeMinMax = False		
		
# ==============================================================================
# PM2_5 DENSITY
# ==============================================================================
class characteristic_PM2_5Density:	
	def __init__(self):
		self.value = 0.0 
		self.maxValue = 1000.0
		self.minValue = 0.0
		self.minStep = 1
		
		self.readonly = True
		self.notify = True	
		self.changeMinMax = False	
		
# ==============================================================================
# PM10 DENSITY
# ==============================================================================
class characteristic_PM10Density:	
	def __init__(self):
		self.value = 0.0 
		self.maxValue = 1000.0
		self.minValue = 0.0
		self.minStep = 1
		
		self.readonly = True
		self.notify = True	
		self.changeMinMax = False		
		
# ==============================================================================
# POSITION STATE
# ==============================================================================
class characteristic_PositionState:	
	def __init__(self):
		self.value = 2 
		self.maxValue = 2
		self.minValue = 0
		
		self.validValues = [0, 1, 2]
		self.validValuesStr = "[decreasing, increasing, stopped]"
		
		self.readonly = True
		self.notify = True		
		self.changeMinMax = False
		
# ==============================================================================
# PROGRAM MODE
# ==============================================================================
class characteristic_ProgramMode:	
	def __init__(self):
		self.value = 0
		self.maxValue = 2
		self.minValue = 0
		
		self.validValues = [0, 1, 2]
		self.validValuesStr = "[no program scheduled, program scheduled, manual mode]"
		
		self.readonly = True
		self.notify = True	
		self.changeMinMax = False	
		
# ==============================================================================
# PROGRAMMABLE SWITCH EVENT
# ==============================================================================
class characteristic_ProgrammableSwitchEvent:	
	def __init__(self):
		self.value = 0
		self.maxValue = 2
		self.minValue = 0
		
		self.validValues = [0, 1, 2]
		self.validValuesStr = "[single press, double press, long press]"
		
		self.readonly = True
		self.notify = True	
		self.changeMinMax = False		
		
# ==============================================================================
# RELATIVE HUMIDITY DEHUMIDIFIER THRESHOLD
# ==============================================================================		
class characteristic_RelativeHumidityDehumidifierThreshold:
	def __init__(self):
		self.value = 0.0
		self.maxValue = 100.0
		self.minValue = 0.0
		self.minStep = 1

		self.readonly = False
		self.notify = True		
		self.changeMinMax = False
		
# ==============================================================================
# RELATIVE HUMIDITY HUMIDIFIER THRESHOLD
# ==============================================================================		
class characteristic_RelativeHumidityHumidifierThreshold:
	def __init__(self):
		self.value = 0.0
		self.maxValue = 100.0
		self.minValue = 0.0
		self.minStep = 1

		self.readonly = False
		self.notify = True	
		self.changeMinMax = False			
		
# ==============================================================================
# REMAINING DURATION (Need to update homebridge/hap-nodejs/lib/gen/HomeKitTypes.js to extend this range)
# ==============================================================================
class characteristic_RemainingDuration:	
	def __init__(self):
		self.value = 0
		self.maxValue = 43200 # This is in seconds and defaulted to a ridiculous 3600 seconds or 5 minute duration!  Updated it to be 12 hours
		self.minValue = 0
		self.minStep = 1
				
		self.readonly = True
		self.notify = True		
		self.changeMinMax = True		
		
# ==============================================================================
# RESET FILTER INDICATION
# ==============================================================================
class characteristic_ResetFilterIndication:	
	def __init__(self):
		self.value = 1
		self.maxValue = 1
		self.minValue = 1
		
		self.validValues = [1]
		self.validValuesStr = "[reset filter indication]"
		
		self.readonly = False
		self.notify = True		
		self.changeMinMax = False			
		
# ==============================================================================
# ROTATION DIRECTION
# ==============================================================================
class characteristic_RotationDirection:	
	def __init__(self):
		self.value = 0 # clockwise [counter-clockwise]
		self.maxValue = 1
		self.minValue = 0
		
		self.validValues = [0, 1]
		self.validValuesStr = "[clockwise, counter clockwise]"
		
		self.readonly = False
		self.notify = True	
		self.changeMinMax = False	
		
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
		self.changeMinMax = False
	
# ==============================================================================
# SATURATION
# ==============================================================================		
class characteristic_Saturation:
	def __init__(self):
		self.value = 0.0
		self.maxValue = 100.0
		self.minValue = 0.0
		self.minStep = 1

		self.readonly = False
		self.notify = True
		self.changeMinMax = False
		
# ==============================================================================
# SERVICE LABEL INDEX
# ==============================================================================		
class characteristic_ServiceLabelIndex:
	def __init__(self):
		self.value = 1
		self.maxValue = 255
		self.minValue = 1
		self.minStep = 1

		self.readonly = False
		self.notify = False	
		self.changeMinMax = False	
		
# ==============================================================================
# SET DURATION (Need to update homebridge/hap-nodejs/lib/gen/HomeKitTypes.js to extend this range)
# ==============================================================================
class characteristic_SetDuration:	
	def __init__(self):
		self.value = 0
		self.maxValue = 43200 # This is in seconds and defaulted to a ridiculous 3600 seconds or 5 minute duration!  Updated it to be 12 hours
		self.minValue = 0
		self.minStep = 1
				
		self.readonly = False
		self.notify = True		
		self.changeMinMax = True				
		
# ==============================================================================
# SLAT TYPE
# ==============================================================================
class characteristic_SlatType:	
	def __init__(self):
		self.value = 0 # clockwise [counter-clockwise]
		self.maxValue = 1
		self.minValue = 0
		
		self.validValues = [0, 1]
		self.validValuesStr = "[horizontal, vertical]"
		
		self.readonly = True
		self.notify = True	
		self.changeMinMax = False		
		
# ==============================================================================
# SMOKE DETECTED
# ==============================================================================
class characteristic_SmokeDetected:	
	def __init__(self):
		self.value = 0 # clockwise [counter-clockwise]
		self.maxValue = 1
		self.minValue = 0
		
		self.validValues = [0, 1]
		self.validValuesStr = "[smoke not detected, smoke detected]"
		
		self.readonly = False
		self.notify = True	
		self.changeMinMax = False		
		
# ==============================================================================
# STATUS ACTIVE
# ==============================================================================
class characteristic_StatusActive:
	def __init__(self):
		self.value = True
		
		self.validValues = [True, False]
		
		self.readonly = True
		self.notify = False		
		self.changeMinMax = False	
		
# ==============================================================================
# STATUS FAULT
# ==============================================================================
class characteristic_StatusFault:	
	def __init__(self):
		self.value = 0 # no fault [fault]
		self.maxValue = 1
		self.minValue = 0
		
		self.validValues = [0, 1]
		self.validValuesStr = "[no fault, fault]"
		
		self.readonly = True
		self.notify = True		
		self.changeMinMax = False	
		
# ==============================================================================
# STATUS LOW BATTERY
# ==============================================================================
class characteristic_StatusLowBattery:	
	def __init__(self):
		self.value = 0 # normal [low]
		self.maxValue = 1
		self.minValue = 0
		
		self.validValues = [0, 1]
		self.validValuesStr = "[normal, low]"
		
		self.readonly = True
		self.notify = True	
		self.changeMinMax = False		
		
# ==============================================================================
# STATUS TAMPERED
# ==============================================================================
class characteristic_StatusTampered:	
	def __init__(self):
		self.value = 0 # not tampered [tampered]
		self.maxValue = 1
		self.minValue = 0
		
		self.validValues = [0, 1]
		self.validValuesStr = "[not tampered, tampered]"
		
		self.readonly = True
		self.notify = True		
		self.changeMinMax = False	
		
# ==============================================================================
# SWING MODE
# ==============================================================================
class characteristic_SwingMode:	
	def __init__(self):
		self.value = 0 
		self.maxValue = 1
		self.minValue = 0
		
		self.validValues = [0, 1]
		self.validValuesStr = "[disabled, enabled]"
		
		self.readonly = False
		self.notify = True		
		self.changeMinMax = False
		
# ==============================================================================
# SECURITY SYSTEM ALARM TYPE
# ==============================================================================
class characteristic_SecuritySystemAlarmType:	
	def __init__(self):
		self.value = 0
		self.maxValue = 1
		self.minValue = 0
		
		self.validValues = [0, 1]
		self.validValuesStr = "[no alarm, alarm]"
		
		self.readonly = True
		self.notify = True		
		self.changeMinMax = False	
		
# ==============================================================================
# SECURITY SYSTEM CURRENT STATE
# ==============================================================================
class characteristic_SecuritySystemCurrentState:	
	def __init__(self):
		self.value = 0 
		self.maxValue = 4
		self.minValue = 0
		
		self.validValues = [0, 1, 2, 3, 4]
		self.validValuesStr = "[stay armed, away armed, night armed, disarmed, alarm triggered]"
		
		self.readonly = True
		self.notify = True		
		self.changeMinMax = False	
		
# ==============================================================================
# SECURITY SYSTEM TARGET STATE
# ==============================================================================
class characteristic_SecuritySystemTargetState:	
	def __init__(self):
		self.value = 0 # disabled [enabled]
		self.maxValue = 4
		self.minValue = 0
		
		self.validValues = [0, 1, 2, 3]
		self.validValuesStr = "[stay arm, away arm, night arm, disarm]"
		
		self.readonly = False
		self.notify = True	
		self.changeMinMax = False	
		
# ==============================================================================
# SELECTED RTP STREAM CONFIGURATION
# ==============================================================================
class characteristic_SelectedRTPStreamConfiguration:	
	def __init__(self):
		self.value = u"" 
		
		self.readonly = True
		self.notify = False		
		self.changeMinMax = False	
		
# ==============================================================================
# SET UP ENDPOINTS
# ==============================================================================
class characteristic_SetupEndpoints:	
	def __init__(self):
		self.value = u"" 
		
		self.readonly = True
		self.notify = True	
		self.changeMinMax = False
		
# ==============================================================================
# STREAMING STATUS
# ==============================================================================
class characteristic_StreamingStatus:	
	def __init__(self):
		self.value = u"" 
		
		self.readonly = True
		self.notify = True		
		self.changeMinMax = False		
		
# ==============================================================================
# SULPHUR DIOXIDE DENSITY
# ==============================================================================
class characteristic_SulphurDioxideDensity:	
	def __init__(self):
		self.value = 0.0 
		self.maxValue = 1000.0
		self.minValue = 0.0
		self.minStep = 1
		
		self.readonly = True
		self.notify = True	
		self.changeMinMax = False

# ==============================================================================
# SUPPORTED AUDIO STREAM CONFIGURATION
# ==============================================================================
class characteristic_SupportedAudioStreamConfiguration:	
	def __init__(self):
		self.value = u"" 
		
		self.readonly = True
		self.notify = False	
		self.changeMinMax = False
		
# ==============================================================================
# SUPPORTED RTP CONFIGURATION
# ==============================================================================
class characteristic_SupportedRTPConfiguration:	
	def __init__(self):
		self.value = u"" 
		
		self.readonly = True
		self.notify = False	
		self.changeMinMax = False		
		
# ==============================================================================
# SUPPORTED VIDEO STREAM CONFIGURATION
# ==============================================================================
class characteristic_SupportedVideoStreamConfiguration:	
	def __init__(self):
		self.value = u"" 
		
		self.readonly = True
		self.notify = False		
		self.changeMinMax = False		
		
# ==============================================================================
# TARGET AIR PURIFIER STATE
# ==============================================================================
class characteristic_TargetAirPurifierState:	
	def __init__(self):
		self.value = 0 
		self.maxValue = 2
		self.minValue = 0
		
		self.validValues = [0, 1]
		self.validValuesStr = "[manual, auto]"
		
		self.readonly = False
		self.notify = True		
		self.changeMinMax = False	
		
# ==============================================================================
# TARGET DOOR STATE
# ==============================================================================
class characteristic_TargetDoorState:	
	def __init__(self):
		self.value = 0 # open [closed]
		self.maxValue = 1
		self.minValue = 0
		
		self.validValues = [0, 1]
		self.validValuesStr = "[open, closed]"
		
		self.readonly = False
		self.notify = True			
		self.changeMinMax = False

# ==============================================================================
# TARGET FAN STATTE
# ==============================================================================
class characteristic_TargetFanState:	
	def __init__(self):
		self.value = 0 # manual [auto]
		self.maxValue = 1
		self.minValue = 0
		
		self.validValues = [0, 1]
		self.validValuesStr = "[manual, auto]"
		
		self.readonly = False
		self.notify = True
		self.changeMinMax = False
		
# ==============================================================================
# TARGET HEATING/COOLING STATE
# ==============================================================================
class characteristic_TargetHeatingCoolingState:	
	def __init__(self):
		self.value = 0 # off [heat, cool, auto]
		self.maxValue = 3
		self.minValue = 0
		
		self.validValues = [0, 1, 2, 3]
		self.validValuesStr = "[off, heat, cool, auto]"
		
		self.readonly = False
		self.notify = True		
		self.changeMinMax = False
		
# ==============================================================================
# TARGET HEATER/COOLER STATE
# ==============================================================================
class characteristic_TargetHeaterCoolerState:	
	def __init__(self):
		self.value = 1
		self.maxValue = 2
		self.minValue = 0
		
		self.validValues = [0, 1, 2]
		self.validValuesStr = "[auto, heat, cool]"
		
		self.readonly = True
		self.notify = True	
		self.changeMinMax = False		
		
# ==============================================================================
# TARGET HORIZONTAL TILT ANGLE
# ==============================================================================		
class characteristic_TargetHorizontalTiltAngle:
	def __init__(self):
		self.value = 0
		self.maxValue = 90
		self.minValue = -90
		self.minStep = 1

		self.readonly = False
		self.notify = True		
		self.changeMinMax = False
		
# ==============================================================================
# TARGET HUMIDIFIER / DEHUMIDIFIER STATE
# ==============================================================================
class characteristic_TargetHumidifierDehumidifierState:	
	def __init__(self):
		self.value = 0 
		self.maxValue = 2
		self.minValue = 0
		
		self.validValues = [0, 1, 2]
		self.validValuesStr = "[humidifier or dehumidifier, humidifier, dehumidifier]"
		
		self.readonly = False
		self.notify = True		
		self.changeMinMax = False		
		
# ==============================================================================
# TARGET POSITION
# ==============================================================================		
class characteristic_TargetPosition:
	def __init__(self):
		self.value = 0
		self.maxValue = 100
		self.minValue = 0
		self.minStep = 1

		self.readonly = False
		self.notify = True		
		self.changeMinMax = False	
		
# ==============================================================================
# TARGET TEMPERATURE
# ==============================================================================		
class characteristic_TargetTemperature:
	def __init__(self):
		self.value = 0.0
		self.maxValue = 38
		self.minValue = 10
		self.minStep = 0.1

		self.readonly = False
		self.notify = True	
		self.changeMinMax = True		

# ==============================================================================
# TARGET RELATIVE HUMIDITY
# ==============================================================================		
class characteristic_TargetRelativeHumidity:
	def __init__(self):
		self.value = 0.0
		self.maxValue = 100
		self.minValue = 0
		self.minStep = 1

		self.readonly = False
		self.notify = True	
		self.changeMinMax = False
		
# ==============================================================================
# TARGET TILT ANGLE
# ==============================================================================		
class characteristic_TargetTiltAngle:
	def __init__(self):
		self.value = 0
		self.maxValue = 90
		self.minValue = -90
		self.minStep = 1

		self.readonly = False
		self.notify = True	
		self.changeMinMax = False			
		
# ==============================================================================
# TARGET VERTICAL TILT ANGLE
# ==============================================================================		
class characteristic_TargetVerticalTiltAngle:
	def __init__(self):
		self.value = 0
		self.maxValue = 90
		self.minValue = -90
		self.minStep = 1

		self.readonly = False
		self.notify = True	
		self.changeMinMax = False	
		
# ==============================================================================
# TEMPERATURE DISPLAY UNITS
# ==============================================================================
class characteristic_TemperatureDisplayUnits:	
	def __init__(self):
		self.value = 0 # celsius [fahrenheit]
		self.maxValue = 1
		self.minValue = 0
		
		self.validValues = [0, 1]
		self.validValuesStr = "[celsius, fahrenheit]"
		
		self.readonly = False
		self.notify = True		
		self.changeMinMax = False
		
# ==============================================================================
# VOC DENSITY
# ==============================================================================
class characteristic_VOCDensity:	
	def __init__(self):
		self.value = 0.0 
		self.maxValue = 1000.0
		self.minValue = 0.0
		self.minStep = 1
		
		self.readonly = True
		self.notify = True	
		self.changeMinMax = False		
				
# ==============================================================================
# VOLUME
# ==============================================================================		
class characteristic_Volume:
	def __init__(self):
		self.value = 0
		self.maxValue = 100
		self.minValue = 0
		self.minStep = 1

		self.readonly = False
		self.notify = True		
		self.changeMinMax = False
		
# ==============================================================================
# VALVE TYPE
# ==============================================================================
class characteristic_ValveType:	
	def __init__(self):
		self.value = 0 # celsius [fahrenheit]
		self.maxValue = 3
		self.minValue = 0
		
		self.validValues = [0, 1, 2, 3]
		self.validValuesStr = "[generic, irrigation, shower head, water faucet]"
		
		self.readonly = True
		self.notify = True	
		self.changeMinMax = False					
		
# ==============================================================================
# WATER LEVEL
# ==============================================================================		
class characteristic_WaterLevel:
	def __init__(self):
		self.value = 0.0
		self.maxValue = 100.0
		self.minValue = 0.0

		self.readonly = True
		self.notify = True		
		self.changeMinMax = False	