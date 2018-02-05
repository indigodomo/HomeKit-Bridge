# lib.ui - Custom list returns and UI enhancements
#
# Copyright (c) 2018 ColoradoFourWheeler / EPS
#

import indigo
import logging

import ext
import dtutil

import re
import ast
import datetime
from datetime import date, timedelta
import time
import sys
import string
import calendar

# For JSON Encoding
import json
import hashlib

class ui:
	listcache = {}
	
	#
	# Initialize the class
	#
	def __init__ (self, factory):
		self.logger = logging.getLogger ("Plugin.ui")
		self.factory = factory
		
	################################################################################
	# CUSTOM LISTS
	################################################################################
	#
	# Format: #type#[opt=value, opt=value ...]
	#
	#	Type: The custom list type to return
	#	Opt: The options required by the list type being used
	#		srcfield: The valuesDict field that contains the source data for the field
	#		index: If provided with the exact field name getting the lookup, a cache will be created for other lookups

	#
	# Same as getCustomList but for Actions library - 100% pass through
	#
	def getActionList (self, filter="", valuesDict=None, typeId="", targetId=0):
		try:
			ret = [("default", "No data")]
			
			if "actv3" not in dir(self.factory):
				self.logger.error ("Actions is not currently loaded into the factory, custom list actions cannot be processed")
				return ret
				
			return self.factory.actv3.getActionList (filter, valuesDict, typeId, targetId)
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return ret	

	#
	# Takes a custom line from filter and returns a list of custom values
	#
	def getCustomList (self, filter="", valuesDict=None, typeId="", targetId=0):
		ret = [("default", "No data")]
			
		#indigo.server.log("Generating list")
		#indigo.server.log(unicode(valuesDict))
		#self.logger.threaddebug ("List START: " + unicode(indigo.server.getTime()))
		
		try:	
			if filter == "": return ret
			
			# If our target ID is zero see if we have a "uniqueIdentifier" field to take it's place (for action groups and
			# other records where the targetId is never pass or where there can be multiple records under one Indigo ID)
			if targetId == 0:
				if ext.valueValid (valuesDict, "uniqueIdentifier"):
					if valuesDict["uniqueIdentifier"] != "" and valuesDict["uniqueIdentifier"] != "0":
						targetId = int(valuesDict["uniqueIdentifier"])
	
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
			
			# Since conditions take a very long time to calculate all the fields, do a quick check and don't actually
			# calculate for anything not currently visible if conditions are active and this is a conditions device
			if index != "" and "cond" in dir(self.factory) and ext.valueValid (valuesDict, "expandConditions1"): 
				conditionNum = index[-1]
				
				checkExpand = False
				for i in range (1, self.factory.cond.maxConditions + 1):
					if str(i).strip() == conditionNum.strip(): checkExpand = True
				
				if checkExpand:
					for i in range (1, self.factory.cond.maxConditions + 1):
						if ext.valueValid (valuesDict, "expandConditions" + str(i)):
							if valuesDict["expandConditions" + str(i)] == False and int(conditionNum) == i: 
								#self.logger.threaddebug ("List called for condition {0} but it is not expanded, skipping it".format(str(i)))
								
								# Return a single list item with the current value as the only option, this way we don't
								# lose our value since it would no longer be a valid list item
								if ext.valueValid (valuesDict, index) == False:
									# Just in case the field doesn't exist
									return ret
								elif str(valuesDict[index]) != "":
									return [(str(valuesDict[index]), "Condition collapsed, refreshing value")]
								else:
									return ret
			
			# Check cache for existing list - if nothing has changed then we should be OK to return cache instead of looking up
			cache = self._matchesCache (index, targetId, args, valuesDict)
			if cache: 
				#self.logger.debug ("Cached results of lookup match current parameters, returning the previous results")
				#self.logger.threaddebug ("List CACHE END: " + unicode(indigo.server.getTime()))
				return cache
			
			self.logger.threaddebug ("Generating custom list '{0}' (filter: {1}), typeId of {2}, targetId of {3} and arguments: {4}".format(listType, filter, str(typeId), str(targetId), unicode(args)))
			
			# Callback
			if listType.lower() == "plugin" and callback != "":
				func = getattr(self.factory.plugin, callback)
				results = func (args, valuesDict)
			
			# System
			if listType.lower() == "indigofolders":	results = self._getIndigoFolders (args, valuesDict)
			
			# Miscellaneous
			if listType.lower() == "numbers": results = self._getNumbers (args, valuesDict)
		
			# Conditions
			if listType.lower() == "conditions_topmenu": results = self._getConditionsTopMenu (args, valuesDict)
			if listType.lower() == "conditions_menu": results = self._getConditionsMenu (args, valuesDict)
			if listType.lower() == "conditions_operators": results = self._getConditionsOperators (args, valuesDict)
			if listType.lower() == "conditions_methods": results = self._getConditionsMethods (args, valuesDict)
		
			# Dates/Times
			if listType.lower() == "years": results = self._getYears (args, valuesDict)
			if listType.lower() == "months": results = self._getMonths (args, valuesDict)
			if listType.lower() == "days": results = self._getDays (args, valuesDict)
			if listType.lower() == "dows": results = self._getDows (args, valuesDict)
			if listType.lower() == "times": results = self._getTimes (args, valuesDict)
		
			# Specialty (future proofing)
			if listType.lower() == "fieldoptions": results = ret
			if listType.lower() == "stateoptions": results = ret
			if listType.lower() == "propoptions": results = ret
			
			# Actions - providing an index for this (and thus caching it) may cause the list not to get updated properly
			if listType.lower() == "actionoptionlist": results = self.factory.act.getActionOptionUIList (args, valuesDict)
			if listType.lower() == "actionoptionlist_v2": results = self.factory.actv2.getActionOptionUIList (args, valuesDict)
		
			# Variables
			if listType.lower() == "variableactions": results = self._getActionsForVariable (args, valuesDict)
			
			# Server
			if listType.lower() == "serveractions": results = self._getActionsForServer (args, valuesDict)
			
			# State Icons
			if listType.lower() == "stateicons": results = self._getStateIconsList (args, valuesDict)
		
			# Devices
			if listType.lower() == "filtereddevices": results = self._getFilteredDeviceList (args, valuesDict)
			if listType.lower() == "devicestates": results = self._getStatesForDevice (args, valuesDict)
			if listType.lower() == "devicefields": results = self._getFieldsForDevice (args, valuesDict)
			if listType.lower() == "devicevalues": results = self._getValuesForDevice (args, valuesDict)
			if listType.lower() == "deviceactions": results = self._getActionsForDevice (args, valuesDict)
			if listType.lower() == "devicestatesvalues": 
				results = self._getValuesForDevice (args, valuesDict)
				option = ("-line-", self.getSeparator())
				results.append(option)
				results += self._getStatesForDevice (args, valuesDict)
					
			if "nocache" in args and args["nocache"].lower() != "true": self._cacheResults (results, index, targetId, args, valuesDict)
		
			#self.logger.threaddebug ("List END: " + unicode(indigo.server.getTime()))
			#indigo.server.log(unicode(results))
			return results
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return ret	
	
	#
	# Remove a target ID from the cache so it's not saved if we close and re-open the same device again
	#
	def flushCache (self, targetId):
		try:
			if targetId in self.listcache:
				del self.listcache[targetId]
				self.logger.threaddebug ("UI cache flushed for {0}".format(str(targetId)))
				
		except Exception as e:
			self.logger.error (ext.getException(e))		
	
	#
	# Cache a list so other routines can access it
	#
	def _cacheResults (self, results, index, targetId, args, valuesDict):
		try:
			if len(results) == 0 or index == "" or targetId == 0: return
			if valuesDict is None or len(valuesDict) == 0: return
			
			if targetId in self.listcache:
				rec = self.listcache[targetId]
				
			else:
				self.listcache[targetId] = {}
				rec = self.listcache[targetId]
			
			cacheRec = {}
			
			cacheRec["targetId"] = targetId
			cacheRec["index"] = index
			cacheRec["results"] = results
			
			argVals = {}
			
			# See if any argument references a field
			for argName, argValue in args.iteritems():
				argVals[argName] = argValue
				
				if argValue in valuesDict:
					argVals[argName] = valuesDict[argValue]
					
					
			cacheRec["args"] = argVals
			
			rec[index] = cacheRec
			
			self.listcache[targetId] = rec
		
		except Exception as e:
			#self.logger.error ("index: {0}, targetId: {1}, args: {2}".format(unicode(index), unicode(targetId), unicode(args)))
			self.logger.error (ext.getException(e))	
			
			
	#
	# See if a custom list call matches the cache and return the cache results if so
	#
	def _matchesCache (self, index, targetId, args, valuesDict):
		try:
			if index == "" or targetId == 0: 
				#self.logger.info ("Index is nothing or target ID is 0")
				return
			if valuesDict is None or len(valuesDict) == 0: 
				#self.logger.info ("ValuesDict is empty")
				return
			
			if targetId in self.listcache:
				rec = self.listcache[targetId]
			else:
				#self.logger.info ("Target ID is not in cache")
				return False
				
			if index in rec:
				field = rec[index]
			else:
				#self.logger.info ("Index {0} is not in cache".format(index))
				return False
				
			# If we get here then we have a field record for the device record
			if field["targetId"] != targetId: 
				#self.logger.info ("Target ID does not match")
				return False
				
			if field["index"] != index: 
				#self.logger.info ("Index '{0}' does not match '{1}'".format(index, field["index"]))
				return False
				
			# See if all the args match
			for argName, argValue in args.iteritems():
				# Make sure that this argument exists in our cache
				if argName in field["args"]:
					# See if the argValue is a lookup from valuesDict
					if argValue != "" and argValue in valuesDict:
						# This is a lookup field, the value is the value of the lookup
						value = valuesDict[argValue]
					
					else:
						value = argValue
						
					# Now compare our value to the cached value
					if unicode(value) != unicode(field["args"][argName]):
						#self.logger.warn ("Value {0} differs from value {1} for argument {2}, not returning cache".format(unicode(value), unicode(args[argName]), argName)) 
						return False # The argument values passed don't match the argument values stored
					
				else:
					self.logger.warn ("{0} is not in cached arguments")
					return False # Argument difference
				
			return field["results"] # Everything is a match, return the cache
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return False
				
	
	#
	# Extract a default list item using the cache if possible
	#
	def getDefaultListItem (self, targetId, index, currentVal):
		try:
			if index == "" or targetId == 0: return currentVal
		
			if targetId in self.listcache:
				rec = self.listcache[targetId]
			else:
				return currentVal

			if index in rec:
				field = rec[index]
			else:
				return currentVal
				
			if field["index"] != index or len(field["results"]) == 0: return currentVal
			
			currentValid = False
			default = ""
			
			for result in field["results"]:
				if str(result[0]) == str(currentVal): 
					#indigo.server.log(str(result[0]) + " == " + str(currentVal))
					#indigo.server.log("1", isError=True)
					currentValid = True	
				
				if default == "": default = result[0]

			if currentValid: return currentVal

			return default				
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return currentVal
	
	################################################################################
	# LIST GENERATORS
	################################################################################	

	#
	# Indigo device state icons
	#
	def _getStateIconsList (self, args, valuesDict):
		ret = [("default", "No data")]
			
		try:
			retList = []
			
			retList.append (('Auto', 'automatic (default)'))
			retList.append (('None', 'no image icon'))
			retList.append (('Error', 'show an error device image icon'))
			retList.append (('Custom', 'plugin defined custom image icon (not yet implemented)'))
			retList.append (('PowerOff', 'power off icon'))
			retList.append (('PowerOn', 'power on icon'))
			retList.append (('DimmerOff', 'dimmer or bulb off icon'))
			retList.append (('DimmerOn', 'dimmer or bulb on icon'))
			retList.append (('FanOff', 'fan off icon'))
			retList.append (('FanLow', 'fan on (low) icon'))
			retList.append (('FanMedium', 'fan on (medium) icon'))
			retList.append (('FanHigh', 'fan on (high) icon'))
			retList.append (('SprinklerOff', 'sprinkler off icon'))
			retList.append (('SprinklerOn', 'sprinkler off icon'))
			retList.append (('HvacOff', 'thermostat off icon'))
			retList.append (('HvacCoolMode', 'thermostat in cool mode icon'))
			retList.append (('HvacHeatMode', 'thermostat in heat mode icon'))
			retList.append (('HvacAutoMode', 'thermostat in auto mode icon'))
			retList.append (('HvacFanOn', 'thermostat with fan blower on only icon'))
			retList.append (('HvacCooling', 'thermostat that is cooling icon'))
			retList.append (('HvacHeating', 'thermostat that is heating icon'))
			retList.append (('SensorOff', 'generic sensor off icon (gray circle)'))
			retList.append (('SensorOn', 'generic sensor on icon (green circle)'))
			retList.append (('SensorTripped', 'generic sensor tripped icon (red circle)'))
			retList.append (('EnergyMeterOff', 'energy meter off icon'))
			retList.append (('EnergyMeterOn', 'energy meter on icon'))
			retList.append (('LightSensor', 'light meter off icon'))
			retList.append (('LightSensorOn', 'light meter on icon'))
			retList.append (('MotionSensor', 'motion sensor icon'))
			retList.append (('MotionSensorTripped', 'motion sensor tripped/activated icon'))
			retList.append (('DoorSensorClosed', 'door sensor closed icon'))
			retList.append (('DoorSensorOpened', 'door sensor opened icon'))
			retList.append (('WindowSensorClosed', 'window sensor closed icon'))
			retList.append (('WindowSensorOpened', 'window sensor opened icon'))
			retList.append (('TemperatureSensor', 'temperature sensor icon'))
			retList.append (('TemperatureSensorOn', 'temperature sensor on icon'))
			retList.append (('HumiditySensor', 'humidity sensor icon'))
			retList.append (('HumiditySensorOn', 'humidity sensor on icon'))
			retList.append (('HumidifierOff', 'humidifier turned off icon'))
			retList.append (('HumidifierOn', 'humidifier turned on icon'))
			retList.append (('DehumidifierOff', 'dehumidifier turned off icon'))
			retList.append (('DehumidifierOn', 'dehumidifier turned on icon'))
			retList.append (('WindSpeedSensor', 'wind speed sensor icon'))
			retList.append (('WindSpeedSensorLow', 'wind speed sensor (low) icon'))
			retList.append (('WindSpeedSensorMedium', 'wind speed sensor (medium) icon'))
			retList.append (('WindSpeedSensorHigh', 'wind speed sensor (high) icon'))
			retList.append (('WindDirectionSensor', 'wind direction sensor icon'))
			retList.append (('WindDirectionSensorNorth', 'wind direction sensor (N) icon'))
			retList.append (('WindDirectionSensorNorthEast', 'wind direction sensor (NE) icon'))
			retList.append (('WindDirectionSensorEast', 'wind direction sensor (E) icon'))
			retList.append (('WindDirectionSensorSouthEast', 'wind direction sensor (SE) icon'))
			retList.append (('WindDirectionSensorSouth', 'wind direction sensor (S) icon'))
			retList.append (('WindDirectionSensorSouthWest', 'wind direction sensor (SW) icon'))
			retList.append (('WindDirectionSensorWest', 'wind direction sensor (W) icon'))
			retList.append (('WindDirectionSensorNorthWest', 'wind direction sensor (NW) icon'))
			retList.append (('BatteryCharger', 'battery charger icon'))
			retList.append (('BatteryChargerOn', 'battery charger on icon'))
			retList.append (('BatteryLevel', 'battery level icon'))
			retList.append (('BatteryLevelLow', 'battery level (low) icon'))
			retList.append (('BatteryLevel25', 'battery level (25%) icon'))
			retList.append (('BatteryLevel50', 'battery level (50%) icon'))
			retList.append (('BatteryLevel75', 'battery level (75%) icon'))
			retList.append (('BatteryLevelHigh', 'battery level (full) icon'))
			retList.append (('TimerOff', 'timer off icon'))
			retList.append (('TimerOn', 'timer on icon'))
			retList.append (('AvStopped', 'A/V stopped icon'))
			retList.append (('AvPaused', 'A/V paused icon'))
			retList.append (('AvPlaying', 'A/V playing icon'))
		
			if len(retList) > 0: return retList
	
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return ret

	#
	# Filtered device list
	#
	def _getFilteredDeviceList (self, args, valuesDict):
		ret = [("default", "No data")]
			
		try:
			retList = []
			
			state = ""
			proptrue = ""
			propfalse = ""
			excludeSelf = False
			
						
			# Only if it has a certain state
			if ext.valueValid (args, "onlywith", True): 
				state = args["onlywith"]
				
			# Only if a specific property is True
			if ext.valueValid (args, "proptrue", True): 
				proptrue = args["proptrue"]
				
			# Only if a specific property is False
			if ext.valueValid (args, "propfalse", True): 
				propfalse = args["propfalse"]	
				
			# Exclude plugin devices
			if ext.valueValid (args, "excludeself", True): 
				if args["excludeself"].lower() == "true":
					excludeSelf = True
		
			for dev in indigo.devices:
				isValid = True

				# Check for filtered state	
				if state != "":
					isValid = False
								
					if ext.valueValid (dev.states, state):
						isValid = True
						
				# Check for self filter
				if excludeSelf and dev.pluginId == self.factory.plugin.pluginId: isValid = False
				
				# Check for true attribute
				if proptrue != "":
					isValid = False
					
					try:
						prop = getattr(dev, proptrue)
						
						if prop: 
							isValid = True
							
					except AttributeError:
						pass
						
				# Check for false attribute
				if propfalse != "":
					isValid = False
					
					try:
						prop = getattr(dev, propfalse)
						
						if not prop: 
							isValid = True
							
					except AttributeError:
						pass		
					
				if isValid:
					retList.append ((str(dev.id), dev.name))	
					
			source = None # Memory reset
		
			if len(retList) > 0: return retList
	
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return ret

	#
	# Years list
	#
	def _getYears (self, args, valuesDict):
		ret = [("default", "No data")]
	
		try:
			retList = []
		
			startYear = int(indigo.server.getTime().strftime("%Y")) - 1 # default last year
			endYear = startYear + 21 # this year plus 20
		
			if ext.valueValid (args, "start", True): 
				startYear = int(args["start"])
				if ext.valueValid (args, "end", True) == False: endYear = startYear + 20
			
			if ext.valueValid (args, "end", True): 
				endYear = int(args["end"])
				if ext.valueValid (args, "start", True) == False: 
					startYear = endYear - 20
				
					# If the start year is more than 1 year behind us then make it last year
					if startYear > (int(indigo.server.getTime().strftime("%Y")) - 1): startYear = int(indigo.server.getTime().strftime("%Y")) - 1
			
			if ext.valueValid (args, "showany", True):
				if args["showany"].lower() == "true": retList.append (("-any-", "Any"))
				retList = self.addLine (retList)
			
			if ext.valueValid (args, "showcurrent", True):
				if args["showcurrent"].lower() == "true": retList.append (("-this-", "This year"))
			
			if ext.valueValid (args, "showlast", True):
				if args["showlast"].lower() == "true": retList.append (("-last-", "Last year"))
			
			if ext.valueValid (args, "shownext", True):
				if args["shownext"].lower() == "true": retList.append (("-next-", "Next year"))
		
			if len(retList) > 0:
				# We added options, put in a line to separate the year increments if we didn't end on a line already
				if retList[len(retList) - 1] != ("-line-", self.getSeparator()): retList = self.addLine (retList)
			
			for i in range (startYear, endYear + 1):
				retList.append ((str(i), str(i)))
		
			return retList
	
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return ret
		
	#
	# Months list
	#
	def _getMonths (self, args, valuesDict):
		ret = [("default", "No data")]
	
		try:
			retList = []
		
			if ext.valueValid (args, "showany", True):
				if args["showany"].lower() == "true": retList.append (("-any-", "Any"))
				retList = self.addLine (retList)
			
			if ext.valueValid (args, "showcurrent", True):
				if args["showcurrent"].lower() == "true": retList.append (("-this-", "This month"))
			
			if ext.valueValid (args, "showlast", True):
				if args["showlast"].lower() == "true": retList.append (("-last-", "Last month"))
			
			if ext.valueValid (args, "shownext", True):
				if args["shownext"].lower() == "true": retList.append (("-next-", "Next month"))
		
			if len(retList) > 0:
				# We added options, put in a line to separate the year increments if we didn't end on a line already
				if retList[len(retList) - 1] != ("-line-", self.getSeparator()):	retList = self.addLine (retList)
		
			for i in range (0, 12):
				yeardate = indigo.server.getTime().strftime("%Y") + "-" + "%02d" % (i + 1) + "-01"
				d = datetime.datetime.strptime (yeardate, "%Y-%m-%d")
				month = d.strftime ("%B")
				retList.append ((str(i), month))
			
			return retList
	
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return ret
		
	#
	# Days list
	#
	def _getDays (self, args, valuesDict):
		ret = [("default", "No data")]
		if valuesDict is None or len(valuesDict) == 0: return ret
	
		try:
			retList = []
		
			if ext.valueValid (args, "showany", True):
				if args["showany"].lower() == "true": retList.append (("-any-", "Any"))
				retList = self.addLine (retList)
			
			if ext.valueValid (args, "showcurrent", True):
				if args["showcurrent"].lower() == "true": retList.append (("-today-", "Today"))
			
			if ext.valueValid (args, "showlast", True):
				if args["showlast"].lower() == "true": retList.append (("-yesterday-", "Yesterday"))
			
			if ext.valueValid (args, "shownext", True):
				if args["shownext"].lower() == "true": retList.append (("-tomorrow-", "Tomorrow"))
			
			if ext.valueValid (args, "showlastday", True):
				if args["showlastday"].lower() == "true": retList.append (("-lastday-", "Last day of the month"))
			
			if ext.valueValid (args, "showrepeats", True):
				if args["showrepeats"].lower() == "true": 
					retList = self.addLine (retList)
					retList.append (("-first-", "First day of week occurance"))
					retList.append (("-second-", "Second day of week occurance"))
					retList.append (("-third-", "Third day of week occurance"))
					retList.append (("-fourth-", "Fourth day of week occurance"))
					retList.append (("-last-", "Last day of week occurance"))
		
			if len(retList) > 0:
				# We added options, put in a line to separate the year increments if we didn't end on a line already
				if retList[len(retList) - 1] != ("-line-", self.getSeparator()):	retList = self.addLine (retList)
		
			startDay = 1
			endDay = 31
			month = int(indigo.server.getTime().strftime("%m")) # default this month
			year = int(indigo.server.getTime().strftime("%Y")) # default this year
		
			if ext.valueValid (args, "monthsrc", True):
				if ext.valueValid (valuesDict, args["monthsrc"], True):
					if valuesDict[args["monthsrc"]] == "-any-" or valuesDict[args["monthsrc"]] == "-this-":
						month = month
					
					elif valuesDict[args["monthsrc"]] == "-last-":
						month = month - 1
						if month < 1: 
							month = 12
							year = year - 1
					
					elif valuesDict[args["monthsrc"]] == "-next-":
						month = month + 1
						if month > 12: 
							month = 1
							year = year + 1
				
					else:
						month = int(valuesDict[args["monthsrc"]]) + 1 # assume we are always using our own lookups here!
				
				if ext.valueValid (args, "yearsrc", True):
					if valuesDict[args["yearsrc"]] == "-any-" or valuesDict[args["yearsrc"]] == "-this-":
						year = year
					
					elif valuesDict[args["yearsrc"]] == "-last-":
						year = year - 1
					
					elif valuesDict[args["yearsrc"]] == "-next-":
						year = year + 1
				
					else:
						try:
							year = int(valuesDict[args["yearsrc"]])
						except:
							year = year
			
				endDay = calendar.monthrange(year, month)
				endDay = endDay[1]
			
			for i in range (1, (endDay + 1)):
				retList.append ((str(i), str(i)))
			
			return retList
	
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return ret
		
	#
	# Day of week list
	#
	def _getDows (self, args, valuesDict):
		ret = [("default", "No data")]
	
		try:
			retList = []
		
			if ext.valueValid (args, "showany", True):
				if args["showany"].lower() == "true": retList.append (("-any-", "Any"))
				retList = self.addLine (retList)
			
			if ext.valueValid (args, "showcurrent", True):
				if args["showcurrent"].lower() == "true": retList.append (("-today-", "Today"))
			
			if ext.valueValid (args, "showlast", True):
				if args["showlast"].lower() == "true": retList.append (("-yesterday-", "Yesterday"))
			
			if ext.valueValid (args, "shownext", True):
				if args["shownext"].lower() == "true": retList.append (("-tomorrow-", "Tomorrow"))
		
			if len(retList) > 0:
				# We added options, put in a line to separate the year increments if we didn't end on a line already
				if retList[len(retList) - 1] != ("-line-", self.getSeparator()):	retList = self.addLine (retList)
		
			days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
			for i in range (0, 7):
				retList.append ((str(i), days[i]))
			
			return retList
	
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return ret
		

	#
	# Times
	#
	def _getTimes (self, args, valuesDict):
		ret = [("default", "No data")]
	
		try:
			retList = []
		
			if ext.valueValid (args, "showany", True):
				if args["showany"].lower() == "true": retList.append (("-any-", "Any"))
				retList = self.addLine (retList)
			
			if ext.valueValid (args, "shownow", True):
				if args["shownow"].lower() == "true": retList.append (("-now-", "Now"))
			
			if len(retList) > 0:
				# We added options, put in a line to separate the year increments if we didn't end on a line already
				if retList[len(retList) - 1] != ("-line-", self.getSeparator()):	retList = self.addLine (retList)
			
			chunks = 4 # what increment to show, 4 is every 15 minutes (60 / 4)	
			
			if ext.valueValid (args, "chunks", True): chunks = int(args["chunks"])
			
			for h in range (0, 24):
				for minute in range (0, chunks):
					hour = h
					hourEx = h
					am = " AM"
		
					if hour == 0:
						hourEx = 12
				
					elif hour == 12:
						am = " PM"
		
					elif hour > 12:
						hourEx = hour - 12
						am = " PM"
			
					chunkvalue = 60 / chunks
					key = "%02d:%02d" % (hour, minute * chunkvalue)
					value = "%02d:%02d %s" % (hourEx, minute * chunkvalue, am)
		
					if key == "12:00": retList = self.addLine (retList)
		
					option = (key, value)
					retList.append(option)
			
			return retList
	
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return ret


	#
	# Add conditions to pop up
	#
	def _getConditionsMenu (self, args, valuesDict):
		ret = [("default", "^^ SELECT TO CONTINUE ^^")]
	
		try:
			evalList = ["disabled|CONDITION DISABLED"]
		
			showAll = True
			showDevice = True
			showVariable = True
			showDateTime = True
			showDevStateDate = True
			showVarDate = True
			showAttributes = True
			showAttribDate = True
			showFields = True
		
			if ext.valueValid (args, "showall", True): 
				if args["showall"].lower() == "false":
					showDevice = False
					showVariable = False
					showDateTime = False
					showDevStateDate = False
					showVarDate = False
					showAttributes = False
					showAttribDate = False
					showFields = False
								
			if ext.valueValid (args, "showdevice", True): 
				if args["showdevice"].lower() == "false": 
					showDevice = False
				else:
					showDevice = True
				
			if ext.valueValid (args, "showvariable", True): 
				if args["showvariable"].lower() == "false": 
					showVariable = False
				else:
					showVariable = True
				
			if ext.valueValid (args, "showdatetime", True): 
				if args["showdatetime"].lower() == "false": 
					showDateTime = False
				else:
					showDateTime = True
				
			if ext.valueValid (args, "showdevdate", True): 
				if args["showdevdate"].lower() == "false": 
					showDevStateDate = False
				else:
					showDevStateDate = True
				
			if ext.valueValid (args, "showvardate", True): 
				if args["showvardate"].lower() == "false": 
					showVarDate = False
				else:
					showVarDate = True
				
			if ext.valueValid (args, "showattribites", True): 
				if args["showattribites"].lower() == "false": 
					showAttributes = False
				else:
					showAttributes = True
				
			if ext.valueValid (args, "showattribdate", True): 
				if args["showattribdate"].lower() == "false": 
					showAttribDate = False
				else:
					showAttribDate = True
				
			if ext.valueValid (args, "showfields", True): 
				if args["showfields"].lower() == "false": 
					showFields = False
				else:
					showFields = True
				
			if showDevice: evalList.append("device|Device state")
			if showAttributes: evalList.append("attributes|Device properties and attributes")
			if showFields: evalList.append("fields|Device configuration parameters")
			if showVariable: evalList.append("variable|Variable value")
			if showDateTime: evalList.append("datetime|Current date and/or time")
			if showDevStateDate: evalList.append("devstatedatetime|Date and/or time from device state")
			if showAttribDate: evalList.append("devattribdatetime|Date and/or time from device property")
			if showVarDate: evalList.append("vardatetime|Date and/or time from variable")
		
			retList = []
		
			for s in evalList:
				eval = s.split("|")
				option = (eval[0], eval[1])
				retList.append (option)
	
			if len(retList) > 1:
				retList = self.insertLine (retList, 1)
	
			return retList
	
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return ret

	#
	# Add condition methods to pop up options
	#
	def _getConditionsMethods (self, args, valuesDict):
		ret = [("default", "^^ SELECT TO CONTINUE ^^")]
	
		try:
		
			#evalList = ["none|No conditions", "alltrue|All items are true", "anytrue|Any items are true", "allfalse|All items are false", "anyfalse|Any items are false"]
			evalList = []
		
			conditionNum = 0
			lastCondition = 0
		
			if ext.valueValid (args, "conditionNum", True): 
				conditionNum = int(args["showfields"])
				
			for i in range (1, self.factory.cond.maxConditions + 1):
				if ext.valueValid (valuesDict, "expandConditions" + str(i)): lastCondition = i
		
			retList = []
			
			retList.append (("default", "Default"))
		
			if conditionNum < lastCondition:
				if conditionNum > 1:
					retList.append (("and", "AND"))
					retList.append (("or", "OR"))
					retList = self.addLine (retList)
			
				retList.append (("(", "("))
				retList = self.addLine (retList)
			
				if conditionNum > 1:
					retList.append (("AND(", "AND ("))
					retList.append ((")AND", ") AND"))
					retList.append ((")AND(", ") AND ("))
					retList = self.addLine (retList)
			
					retList.append (("OR(", "OR ("))
					retList.append ((")OR", ") OR"))
					retList.append ((")OR(", ") OR ("))
					retList = self.addLine (retList)

					retList.append ((")", ")"))
			else:			
				retList.append ((")", ")"))
			
			return retList
	
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return ret

	#
	# Add condition to pop up options
	#
	def _getConditionsTopMenu (self, args, valuesDict):
		ret = [("default", "^^ SELECT TO CONTINUE ^^")]
	
		try:
		
			#evalList = ["none|No conditions", "alltrue|All items are true", "anytrue|Any items are true", "allfalse|All items are false", "anyfalse|Any items are false"]
			evalList = []
		
			allowNone = True
			allowAllTrue = True
			allowAnyTrue = True
			allowAllFalse = True
			allowAnyFalse = True
		
			if ext.valueValid (args, "allownone", True): 
				if args["allownone"].lower() == "false": allowNone = False
			
			if ext.valueValid (args, "allowalltrue", True): 
				if args["allowalltrue"].lower() == "false": allowAllTrue = False
			
			if ext.valueValid (args, "allowanytrue", True): 
				if args["allowanytrue"].lower() == "false": allowAnyTrue = False
			
			if ext.valueValid (args, "allowallfalse", True): 
				if args["allowallfalse"].lower() == "false": allowAllFalse = False
			
			if ext.valueValid (args, "allowanyfalse", True): 
				if args["allowanyfalse"].lower() == "false": allowAnyFalse = False
			
			if allowNone: evalList.append("none|No conditions")
			if allowAllTrue: evalList.append("alltrue|All items are true")
			if allowAnyTrue: evalList.append("anytrue|Any items are true")
			if allowAllFalse: evalList.append("allfalse|All items are false")
			if allowAnyFalse: evalList.append("anyfalse|Any items are false")
		
			retList = []
		
			for s in evalList:
				eval = s.split("|")
				option = (eval[0], eval[1])
				retList.append (option)
	
			return retList
	
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return ret
		
	#
	# Add condition operators to pop up options
	#
	def _getConditionsOperators (self, args, valuesDict):
		ret = [("default", "^^ SELECT TO CONTINUE ^^")]
	
		try:
		
			evalList = []
		
			showAll = True
			showEqual = True
			showGreater = True
			showBetween = True
			showContains = True
			showIn = True
		
			if ext.valueValid (args, "showall", True): 
				if args["showall"].lower() == "false":
					showEqual = False
					showGreater = False
					showBetween = False
					showContains = False
					showIn = False
				
			if ext.valueValid (args, "showequal", True): 
				if args["showequal"].lower() == "false": 
					showEqual = False
				else:
					showEqual = True
				
			if ext.valueValid (args, "showgreater", True): 
				if args["showgreater"].lower() == "false": 
					showGreater = False
				else:
					showGreater = True
				
			if ext.valueValid (args, "showbetween", True): 
				if args["showbetween"].lower() == "false": 
					showBetween = False
				else:
					showBetween = True
				
			if ext.valueValid (args, "showcontains", True): 
				if args["showcontains"].lower() == "false": 
					showContains = False
				else:
					showContains = True
				
			if ext.valueValid (args, "showin", True): 
				if args["showin"].lower() == "false": 
					showIn = False
				else:
					showIn = True
			
			if showEqual: 
				evalList.append("equal|Equal to")
				evalList.append("notequal|Not equal to")
			
			if showGreater: 
				evalList.append("greater|Greater than")
				evalList.append("less|Less than")
			
			if showBetween: 
				evalList.append("between|Between")
				evalList.append("notbetween|Not between")
			
			if showContains: 
				evalList.append("contains|Containing")
				evalList.append("notcontains|Not containing")
			
			if showIn: 
				evalList.append("in|In")
				evalList.append("notin|Not in")
		
			retList = []
		
			for s in evalList:
				eval = s.split("|")
				option = (eval[0], eval[1])
				retList.append (option)
	
			return retList
	
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return ret
	
	#
	# Get all states for a device
	#
	def _getStatesForDevice(self, args, valuesDict):
		ret = [("default", "^^ SELECT A DEVICE ^^")]
		if valuesDict is None or len(valuesDict) == 0: return ret
		
		try:		
			if ext.valueValid (args, "srcfield", True) == False: return ret
			if ext.valueValid (valuesDict, args["srcfield"], True) == False: return ret
		
			allowUi = False
			if ext.valueValid (args, "allowui", True): 
				if args["allowui"].lower() == "true": allowUi = True
				
			# There may be times where a non device is used, like when it is a line or something, these should have a "-" prefix
			if valuesDict[args["srcfield"]][0] == "-": 
				return ret	
			
			if int(valuesDict[args["srcfield"]]) not in indigo.devices:
				self.logger.error ("Referencing device ID {0} but that device is no longer an Indigo device.  Please change the device reference or remove this plugin device to prevent this error".format(valuesDict[args["srcfield"]]))
				return ret
				
			dev = indigo.devices[int(valuesDict[args["srcfield"]])]
		
			retList = []
		
			# If we have a plug cache then use that instead
			if "plugcache" in dir(self.factory) and self.factory.plugcache is not None:
				retList = self.factory.plugcache.getStateUIList (dev, allowUi)
				return retList
	
			for stateName, stateValue in dev.states.iteritems():
				if len(stateName) < 4:
					option = (stateName, stateName)
					retList.append(option)
			
				else:
					if stateName[-3:] != ".ui":
						option = (stateName, stateName)
						retList.append(option)
			
					else:
						if allowUi:
							option = (stateName, stateName)
							retList.append(option)
		
			return retList

		except Exception as e:
			self.logger.error (ext.getException(e))	
			return ret
		

	#
	# Get all config fields for a device
	#
	def _getFieldsForDevice(self, args, valuesDict):
		ret = [("default", "^^ SELECT A DEVICE ^^")]
		if valuesDict is None or len(valuesDict) == 0: return ret
		
		try:		
			if ext.valueValid (args, "srcfield", True) == False: return ret
			if ext.valueValid (valuesDict,args["srcfield"], True) == False: return ret

			allowUi = False
			if ext.valueValid (args, "allowui", True): 
				if args["allowui"].lower() == "true": allowUi = True
				
			# There may be times where a non device is used, like when it is a line or something, these should have a "-" prefix
			if valuesDict[args["srcfield"]][0] == "-": 
				return ret	
		
			dev = indigo.devices[int(valuesDict[args["srcfield"]])]
		
			retList = []
		
			# If we have a plug cache then use that instead
			if "plugcache" in dir(self.factory) and self.factory.plugcache is not None:
			
				retList = self.factory.plugcache.getFieldUIList (dev)
				if len(retList) == 0: return [("-none-", "No Config Fields For This Device")]
		
				return retList
				
			if "plugdetails" in dir(self.factory) and self.factory.plugdetails is not None:
			
				retList = self.factory.plugdetails.getFieldUIList (dev)
				if len(retList) == 0: return [("-none-", "No Config Fields For This Device")]
		
				return retList	

			return ret
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return ret		

	#
	# Get all actions for a device
	#
	def _getActionsForDevice(self, args, valuesDict):
		ret = [("default", "^^ SELECT A DEVICE ^^")]
		if valuesDict is None or len(valuesDict) == 0: return ret
		
		try:		
			if ext.valueValid (args, "srcfield", True) == False: return ret
			if valuesDict[args["srcfield"]] == "": return ret

			allowUi = False
			if ext.valueValid (args, "allowui", True): 
				if args["allowui"].lower() == "true": allowUi = True
				
			# There may be times where a non device is used, like when it is a line or something, these should have a "-" prefix
			if valuesDict[args["srcfield"]][0] == "-": 
				return ret
		
			if int(valuesDict[args["srcfield"]]) not in indigo.devices:
				self.logger.error ("Asked to get actions for device id {0} but that device no longer exists in Indigo, please change the device configuration to point elsewhere.".format(valuesDict[args["srcfield"]]))
				return ret
				
			dev = indigo.devices[int(valuesDict[args["srcfield"]])]
		
			retList = []
		
			# This requires the plugcache for anything other than basic Indigo commands
			if "plugcache" in dir(self.factory) and self.factory.plugcache is not None:
				retList = self.factory.plugcache.getActionUIList (dev, allowUi)
				if len(retList) == 0: return [("-none-", "No Actions For This Device")]
		
				return retList
				
			elif "plugdetails" in dir(self.factory) and self.factory.plugdetails is not None:
				retList = self.factory.plugdetails.getActionUIList (dev, allowUi)
				if len(retList) == 0: return [("-none-", "No Actions For This Device")]
		
				return retList	
			
			else:
				return ret

		except Exception as e:
			self.logger.error (ext.getException(e))	
			return ret
	
	
	#
	# Get all values for a device
	#
	def _getValuesForDevice(self, args, valuesDict):
		ret = [("default", "^^ SELECT A DEVICE ^^")]
		if valuesDict is None or len(valuesDict) == 0: return ret
		
		try:		
			if ext.valueValid (args, "srcfield", True) == False: return ret	
			if valuesDict[args["srcfield"]] == "": return ret
			
			# There may be times where a non device is used, like when it is a line or something, these should have a "-" prefix
			if valuesDict[args["srcfield"]][0] == "-": 
				return ret
				
			if int(valuesDict[args["srcfield"]]) not in indigo.devices:
				self.logger.error ("Referencing device ID {0} but that device is no longer an Indigo device.  Please change the device reference or remove this plugin device to prevent this error".format(valuesDict[args["srcfield"]]))
				return ret
			
			dev = indigo.devices[int(valuesDict[args["srcfield"]])]
	
			retList = self.getAttributesForDevice (dev)
			if len(retList) == 0: return [("-none-", "No Actions For This Device")]
			
			if ext.valueValid (args, "addoption", True):
				# Insert an option at the top of the list
				self.insertLine (retList, 0)
				
				# And now the option
				addopt = args["addoption"].split("|")
				retList.insert ( 0, (addopt[0], addopt[1]) )
		
			return retList
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return ret
	

	#
	# Get all actions for a variable
	#
	def _getActionsForVariable(self, args, valuesDict):
		ret = [("default", "^^ SELECT A VARIABLE ^^")]
				
		try:		
			allowUi = False
			if ext.valueValid (args, "allowui", True): 
				if args["allowui"].lower() == "true": allowUi = True
		
			retList = []
		
			# This requires the plugcache for anything other than basic Indigo commands
			if "plugcache" in dir(self.factory) and self.factory.plugcache is not None:
				retList = self.factory.plugcache.getVariableActionUIList (allowUi)
				if len(retList) == 0: return [("-none-", "No Variable Actions Found")]
		
				return retList
			
			else:
				return ret

		except Exception as e:
			self.logger.error (ext.getException(e))	
			return ret	
			
	#
	# Get all actions for servers
	#
	def _getActionsForServer(self, args, valuesDict):
		ret = [("default", "No actions")]
				
		try:		
			allowUi = False
			if ext.valueValid (args, "allowui", True): 
				if args["allowui"].lower() == "true": allowUi = True
		
			retList = []
		
			# This requires the plugcache for anything other than basic Indigo commands
			if "plugcache" in dir(self.factory) and self.factory.plugcache is not None:
				retList = self.factory.plugcache.getServerActionUIList (allowUi)
				if len(retList) == 0: return [("-none-", "No Server Actions Found")]
		
				return retList
			
			else:
				return ret

		except Exception as e:
			self.logger.error (ext.getException(e))	
			return ret	
	

	#
	# Return list of folders for various Indigo items, returns devices folders by default
	#
	def _getIndigoFolders (self, args, valuesDict):
		ret = [("default", "No folders found")]
	
		try:
			retList = []
		
			if ext.valueValid (args, "showtop", True):
				option = ("-98", "- Top Level Folder -")
				retList.append(option)
			
			if ext.valueValid (args, "showcreate", True):
				option = ("-99", "- Create Plugin Folder -")
				retList.append(option)
			
			if len(retList) > 0:
				# Add a separator
				option = ("-line-", self.getSeparator())
				retList.append(option)
		
			type = "devices"
			if ext.valueValid (args, "type", True): type = args["type"]
			if ext.valueValid (args, "srcfield", True): 
				if ext.valueValid (valuesDict, args["srcfield"], True): type = valuesDict[args["srcfield"]]
		
			func = getattr(indigo, type)
			for f in func.folders:
				option = (str(f.id), f.name)
				retList.append(option)						
					
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return ret
		
		return retList
	
	#
	# Return list of folders for various Indigo items, returns devices folders by default
	#
	def _getNumbers (self, args, valuesDict):
		ret = [("default", "No folders found")]
	
		try:
			retList = []
			
			low = 0
			high = 20
		
			if ext.valueValid (args, "low", True):
				low = int(args["low"])
				
			if ext.valueValid (args, "high", True):
				high = int(args["high"])
			
			for i in range (low, high + 1):
				option = (str(i), str(i))
				retList.append(option)		
					
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return ret
		
		return retList
	
	################################################################################
	# JSON LISTS
	################################################################################	
	
	#
	# Create JSON array from array
	#
	
	#
	# Create JSON array from UI list
	#
	
	
	#
	# Create a UI list from JSON array
	#
	
	#
	# Create a hash key if needed for JSON encoding/decoding
	#
	def createHashKey(self, keyString):
		hashKey = hashlib.sha256(keyString.encode('ascii', 'ignore')).digest().encode("hex")  # [0:16]
		return hashKey
	
	
	################################################################################
	# UTILITIES
	################################################################################	

	#
	# Separator line
	#
	def getSeparator (self):
		line = ""
		for z in range (0, 20):
			line += unicode("\xc4", "cp437")
			
		return line

	#
	# Add line option to results
	#
	def addLine (self, retList):
		option = ("-line-", self.getSeparator())
		retList.append(option)
	
		return retList
	
	#
	# Insert line option into results
	#
	def insertLine (self, retList, index):
		option = ("-line-", self.getSeparator())
		retList.insert(index, option)
	
		return retList
		
	#
	# Analyze an errorsDict and append to the alert text as needed
	#
	def setErrorStatus (self, errorsDict, statusText, insertBefore = False):
		try:
			if errorsDict is None: errorsDict = indigo.Dict()
			if "showAlertText" not in errorsDict: errorsDict["showAlertText"] = ""
			
			if errorsDict["showAlertText"] == "":			
				errorsDict["showAlertText"] = statusText
				
			else:
				if insertBefore:
					errorsDict["showAlertText"] = statusText + "\n\n" + errorsDict["showAlertText"]
					
				else:
					errorsDict["showAlertText"] += "\n\n" + statusText
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return errorsDict
			

	################################################################################
	# LOOKUPS
	################################################################################	
	
	#
	# Indigo icon keyword to Indigo icon
	#
	def getIndigoIconForKeyword (self, keyword):
		try:
			if keyword == 'Auto': return indigo.kStateImageSel.Auto
			if keyword == 'None': return indigo.kStateImageSel.None
			if keyword == 'Error': return indigo.kStateImageSel.Error
			if keyword == 'Custom': return indigo.kStateImageSel.Custom
			if keyword == 'PowerOff': return indigo.kStateImageSel.PowerOff
			if keyword == 'PowerOn': return indigo.kStateImageSel.PowerOn
			if keyword == 'DimmerOff': return indigo.kStateImageSel.DimmerOff
			if keyword == 'DimmerOn': return indigo.kStateImageSel.DimmerOn
			if keyword == 'FanOff': return indigo.kStateImageSel.FanOff
			if keyword == 'FanLow': return indigo.kStateImageSel.FanLow
			if keyword == 'FanMedium': return indigo.kStateImageSel.FanMedium
			if keyword == 'FanHigh': return indigo.kStateImageSel.FanHigh
			if keyword == 'SprinklerOff': return indigo.kStateImageSel.SprinklerOff
			if keyword == 'SprinklerOn': return indigo.kStateImageSel.SprinklerOn
			if keyword == 'HvacOff': return indigo.kStateImageSel.HvacOff
			if keyword == 'HvacCoolMode': return indigo.kStateImageSel.HvacCoolMode
			if keyword == 'HvacHeatMode': return indigo.kStateImageSel.HvacHeatMode
			if keyword == 'HvacAutoMode': return indigo.kStateImageSel.HvacAutoMode
			if keyword == 'HvacFanOn': return indigo.kStateImageSel.HvacFanOn
			if keyword == 'HvacCooling': return indigo.kStateImageSel.HvacCooling
			if keyword == 'HvacHeating': return indigo.kStateImageSel.HvacHeating
			if keyword == 'SensorOff': return indigo.kStateImageSel.SensorOff
			if keyword == 'SensorOn': return indigo.kStateImageSel.SensorOn
			if keyword == 'SensorTripped': return indigo.kStateImageSel.SensorTripped
			if keyword == 'EnergyMeterOff': return indigo.kStateImageSel.EnergyMeterOff
			if keyword == 'EnergyMeterOn': return indigo.kStateImageSel.EnergyMeterOn
			if keyword == 'LightSensor': return indigo.kStateImageSel.LightSensor
			if keyword == 'LightSensorOn': return indigo.kStateImageSel.LightSensorOn
			if keyword == 'MotionSensor': return indigo.kStateImageSel.MotionSensor
			if keyword == 'MotionSensorTripped': return indigo.kStateImageSel.MotionSensorTripped
			if keyword == 'DoorSensorClosed': return indigo.kStateImageSel.DoorSensorClosed
			if keyword == 'DoorSensorOpened': return indigo.kStateImageSel.DoorSensorOpened
			if keyword == 'WindowSensorClosed': return indigo.kStateImageSel.WindowSensorClosed
			if keyword == 'WindowSensorOpened': return indigo.kStateImageSel.WindowSensorOpened
			if keyword == 'TemperatureSensor': return indigo.kStateImageSel.TemperatureSensor
			if keyword == 'TemperatureSensorOn': return indigo.kStateImageSel.TemperatureSensorOn
			if keyword == 'HumiditySensor': return indigo.kStateImageSel.HumiditySensor
			if keyword == 'HumiditySensorOn': return indigo.kStateImageSel.HumiditySensorOn
			if keyword == 'HumidifierOff': return indigo.kStateImageSel.HumidifierOff
			if keyword == 'HumidifierOn': return indigo.kStateImageSel.HumidifierOn
			if keyword == 'DehumidifierOff': return indigo.kStateImageSel.DehumidifierOff
			if keyword == 'DehumidifierOn': return indigo.kStateImageSel.DehumidifierOn
			if keyword == 'WindSpeedSensor': return indigo.kStateImageSel.WindSpeedSensor
			if keyword == 'WindSpeedSensorLow': return indigo.kStateImageSel.WindSpeedSensorLow
			if keyword == 'WindSpeedSensorMedium': return indigo.kStateImageSel.WindSpeedSensorMedium
			if keyword == 'WindSpeedSensorHigh': return indigo.kStateImageSel.WindSpeedSensorHigh
			if keyword == 'WindDirectionSensor': return indigo.kStateImageSel.WindDirectionSensor
			if keyword == 'WindDirectionSensorNorth': return indigo.kStateImageSel.WindDirectionSensorNorth
			if keyword == 'WindDirectionSensorNorthEast': return indigo.kStateImageSel.WindDirectionSensorNorthEast
			if keyword == 'WindDirectionSensorEast': return indigo.kStateImageSel.WindDirectionSensorEast
			if keyword == 'WindDirectionSensorSouthEast': return indigo.kStateImageSel.WindDirectionSensorSouthEast
			if keyword == 'WindDirectionSensorSouth': return indigo.kStateImageSel.WindDirectionSensorSouth
			if keyword == 'WindDirectionSensorSouthWest': return indigo.kStateImageSel.WindDirectionSensorSouthWest
			if keyword == 'WindDirectionSensorWest': return indigo.kStateImageSel.WindDirectionSensorWest
			if keyword == 'WindDirectionSensorNorthWest': return indigo.kStateImageSel.WindDirectionSensorNorthWest
			if keyword == 'BatteryCharger': return indigo.kStateImageSel.BatteryCharger
			if keyword == 'BatteryChargerOn': return indigo.kStateImageSel.BatteryChargerOn
			if keyword == 'BatteryLevel': return indigo.kStateImageSel.BatteryLevel
			if keyword == 'BatteryLevelLow': return indigo.kStateImageSel.BatteryLevelLow
			if keyword == 'BatteryLevel25': return indigo.kStateImageSel.BatteryLevel25
			if keyword == 'BatteryLevel50': return indigo.kStateImageSel.BatteryLevel50
			if keyword == 'BatteryLevel75': return indigo.kStateImageSel.BatteryLevel75
			if keyword == 'BatteryLevelHigh': return indigo.kStateImageSel.BatteryLevelHigh
			if keyword == 'TimerOff': return indigo.kStateImageSel.TimerOff
			if keyword == 'TimerOn': return indigo.kStateImageSel.TimerOn
			if keyword == 'AvStopped': return indigo.kStateImageSel.AvStopped
			if keyword == 'AvPaused': return indigo.kStateImageSel.AvPaused
			if keyword == 'AvPlaying': return indigo.kStateImageSel.AvPlaying
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return ret
	
	#
	# Built-in Device States in list format
	#
	def getBuiltInStates (self, dev):
		ret = []
		
		try:
			self.logger.threaddebug ("Device '{0}' is typed as '{1}', retrieving built-in states".format(dev.name, unicode(type(dev))))
			
			if type(dev) is indigo.RelayDevice: 
				ret = self._addIndigoState (dev, "onOffState", ret)
								
			if type(dev) is indigo.DimmerDevice: 
				ret = self._addIndigoState (dev, "onOffState", ret)
				ret = self._addIndigoState (dev, "brightnessLevel", ret)
			
			if type(dev) is indigo.indigo.MultiIODevice: 
				ret = self._addIndigoState (dev, "binaryOutput1", ret)
				ret = self._addIndigoState (dev, "binaryOutputsAll", ret)
				ret = self.addLine(ret)
				ret = self._addIndigoState (dev, "binaryInput1", ret)
				ret = self._addIndigoState (dev, "binaryInputsAll", ret)
			
			if type(dev) is indigo.SensorDevice: deviceTypeId = "indigo.sensor"
			if type(dev) is indigo.SpeedControlDevice: deviceTypeId = "indigo.speedcontrol"
			
			if type(dev) is indigo.SprinklerDevice: 
				# These are all virtual and hard coded
				ret = self._addIndigoState (dev, "activeZone", ret)
				ret.append (("custom_activeZoneName", "Active Zone Name"))
				ret = self.addLine(ret)
				
				for i in range (0, 8):
					ret = self._addIndigoState (dev, "zone" + str(i+1), ret)	
					
				ret = self.addLine(ret)
				
				for i in range (0, 8):
					if dev.zoneEnableList[i]:
						ret.append (("custom_zone" + str(i + 1) + "Name", dev.zoneNames[i] + " (on or off)"))
			
			if type(dev) is indigo.ThermostatDevice: 
				ret = self._addIndigoState (dev, "temperatureInput1", ret)
				ret = self._addIndigoState (dev, "temperatureInputsAll", ret)
				ret = self.addLine(ret)
				ret = self._addIndigoState (dev, "humidityInput1", ret)
				ret = self._addIndigoState (dev, "humidityInputsAll", ret)
				ret = self.addLine(ret)
				ret = self._addIndigoState (dev, "setpointHeat", ret)
				ret = self._addIndigoState (dev, "setpointCool", ret)
				ret = self.addLine(ret)
				ret = self._addIndigoState (dev, "hvacOperationMode", ret)
				ret = self._addIndigoState (dev, "hvacOperationModeIsOff", ret)
				ret = self._addIndigoState (dev, "hvacOperationModeIsHeat", ret)
				ret = self._addIndigoState (dev, "hvacOperationModeIsCool", ret)
				ret = self._addIndigoState (dev, "hvacOperationModeIsAuto", ret)
				ret = self._addIndigoState (dev, "hvacOperationModeIsProgramHeat", ret)
				ret = self._addIndigoState (dev, "hvacOperationModeIsProgramCool", ret)
				ret = self._addIndigoState (dev, "hvacOperationModeIsProgramAuto", ret)
				ret = self.addLine(ret)
				ret = self._addIndigoState (dev, "hvacFanModeIsAlwaysOn", ret)
				ret = self._addIndigoState (dev, "hvacFanModeIsAuto", ret)
				ret = self._addIndigoState (dev, "hvacFanMode", ret)
				ret = self.addLine(ret)
				ret = self._addIndigoState (dev, "hvacCoolerIsOn", ret)
				ret = self._addIndigoState (dev, "hvacHeaterIsOn", ret)
				ret = self._addIndigoState (dev, "hvacFanIsOn", ret)
				ret = self._addIndigoState (dev, "hvacDehumidifierIsOn", ret)
				ret = self._addIndigoState (dev, "hvacHumidifierIsOn", ret)
				
						
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return ret
			
	#
	# Add built-in state to return list
	#
	def _addIndigoState (self, dev, state, ret):
		try:
			if state in dev.states:
				ret.append ((state, self.resolveStateNameToString(state)))
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return ret

	#
	# Terms for common built-in states
	#
	def resolveStateNameToString (self, state):
		# Relay and Dimmer
		if state == "onOffState": return "On/Off State"
		if state == "brightnessLevel": return "Brightness Level"
		
		# Sensor
		if state == "batteryLevel": return "Battery Level"
		
		# Sprinkler
		if state == "activeZone": return "Active Zone Number"
		if state == "zone1": return "Zone 1 State (on or off)"
		if state == "zone2": return "Zone 2 State (on or off)"
		if state == "zone3": return "Zone 3 State (on or off)"
		if state == "zone4": return "Zone 4 State (on or off)"
		if state == "zone5": return "Zone 5 State (on or off)"
		if state == "zone6": return "Zone 6 State (on or off)"
		if state == "zone7": return "Zone 7 State (on or off)"
		if state == "zone8": return "Zone 8 State (on or off)"
		
		# IO
		if state == "binaryInput1": return "Binary Input 1 (closed or open)"
		if state == "binaryInputsAll": return "Binary Status Across Inputs"
		if state == "binaryOutput1": return "Binary Output 1 (on or off)"
		if state == "binaryOutputsAll": return "Binary Status Across Outputs"
		
		# Thermostat
		if state == "hvacHumidifierIsOn": return "Humidifier Equipment State (on or off)"
		if state == "hvacCoolerIsOn": return "A/C Equipment State (on or off)"
		if state == "hvacDehumidifierIsOn": return "Dehumidifier Equipment State (on or off)"
		if state == "hvacFanIsOn": return "Fan Equipment State (on or off)"
		if state == "hvacFanMode": return "Fan Mode"
		if state == "hvacFanModeIsAlwaysOn": return "Fan Is Always On (true or false)"
		if state == "hvacFanModeIsAuto": return "Fan Is Auto On (true or false)"
		if state == "hvacHeaterIsOn": return "Heater Equipment State (on or off)"
		if state == "hvacOperationMode": return "Current Mode"
		if state == "hvacOperationModeIsOff": return "Mode is Off (true or false)"
		if state == "hvacOperationModeIsAuto": return "Mode is Auto (true or false)"
		if state == "hvacOperationModeIsCool": return "Mode Is Cool (true or false)"
		if state == "hvacOperationModeIsHeat": return "Mode is Heat (true or false)"
		if state == "hvacOperationModeIsProgramAuto": return "Mode is Program Auto (true or false)"
		if state == "hvacOperationModeIsProgramCool": return "Mode is Program Cool (true or false)"
		if state == "hvacOperationModeIsProgramHeat": return "Mode is Program Heat (true or false)"
		if state == "setpointCool": return "Heat Setpoint"
		if state == "setpointHeat": return "Cool Setpoint"
		if state == "temperatureInput1": return "Zone 1 Temperature"
		if state == "temperatureInput2": return "Zone 2 Temperature"
		if state == "temperatureInput3": return "Zone 3 Temperature"
		if state == "temperatureInput4": return "Zone 4 Temperature"
		if state == "temperatureInput5": return "Zone 5 Temperature"
		if state == "temperatureInputsAll": return "Current Temperature Across Zones"
		if state == "humidityInput1": return "Zone 1 Humidity"
		if state == "humidityInput2": return "Zone 2 Humidity"
		if state == "humidityInput3": return "Zone 3 Humidity"
		if state == "humidityInput4": return "Zone 4 Humidity"
		if state == "humidityInput5": return "Zone 5 Humidity"
		if state == "humidityInputsAll": return "Current Humidity Across Zones"
	
		return state

	#
	# Terms for common built-in devices
	#
	def getAttributesForDevice (self, dev):
		#indigo.server.log(unicode(dev))
	
		retList = []
	
		other = []
		device = []
		energy = []
		plugin = []
		state = []
		folder = []
		support = []
		hardware = []
		overview = []
		current = []
		ledlevels = []
		ledstates = []
		settings = []
		general1 = []
		general2 = []
		general3 = []
		general4 = []
		general5 = []
		general6 = []
		general7 = []
	
		allAttribs = "All Device Attributes\n"
		
		for p in [a for a in dir(dev) if not a.startswith('__') and not callable(getattr(dev,a))]:
		
			allAttribs += p + "\n"
		
			if p == "ownerProps" or p == "pluginProps" or p == "states" or p == "globalProps":
				continue # These are handled elsewhere and not really usable by the user anyway

			if p == "address": 
				hardware.append (("attr_" + p, "Address"))
			
			elif p == "batteryLevel": 
				energy.append (("attr_" + p, "Battery Level"))
			
			elif p == "buttonGroupCount": 
				hardware.append (("attr_" + p, "Number of Button Groups"))
			
			elif p == "configured": 
				plugin.append (("attr_" + p, "Configuration Completed (True/False)"))	
			
			elif p == "description": 
				overview.append (("attr_" + p, "Description"))	
			
			elif p == "deviceTypeId": 
				plugin.append (("attr_" + p, "Plugin Device ID"))	
			
			elif p == "displayStateId": 
				state.append (("attr_" + p, "State Used for List Display"))	
			
			elif p == "displayStateImageSel": 
				state.append (("attr_" + p, "Image Used for List Display"))	
			
			elif p == "displayStateValRaw": 
				state.append (("attr_" + p, "Raw Display Value"))	
			
			elif p == "displayStateValUi": 
				state.append (("attr_" + p, "Formatted Display Value"))	
			
			elif p == "enabled": 
				device.append (("attr_" + p, "Device is Enabled (True/False)"))	
			
			elif p == "energyAccumBaseTime": 
				energy.append (("attr_" + p, "Date/Time When Energy Collection Began"))	
			
			elif p == "energyAccumTimeDelta": 
				energy.append (("attr_" + p, "Total Seconds of Energy Usage Monitored"))	
			
			elif p == "energyAccumTotal": 
				energy.append (("attr_" + p, "Total Watts/Kilowatts of Energy Used"))	
			
			elif p == "energyCurLevel": 
				energy.append (("attr_" + p, "Current Watts/Kilowatts of Energy in Use"))	

			elif p == "errorState": 
				device.append (("attr_" + p, "Current Error State (If Device Is In Error)"))
			
			elif p == "folderId": 
				folder.append (("cust_folderName", "Folder Name"))
				folder.append (("attr_" + p, "Folder ID"))
			
			elif p == "id": 
				device.append (("attr_" + p, "Device ID"))
			
			elif p == "lastChanged": 
				device.append (("attr_" + p, "Date/Time Device Was Last Updated"))
				
			elif p == "lastSuccessfulComm": 
				device.append (("attr_" + p, "Date/Time Device Of Last Successful Communication"))	
			
			elif p == "model": 
				hardware.append (("attr_" + p, "Model"))
			
			elif p == "name": 
				overview.append (("attr_" + p, "Name"))
			
			elif p == "onState": 
				current.append (("attr_" + p, "Device Is On (True/False)"))
			
			elif p == "pluginId": 
				plugin.append (("attr_" + p, "Plugin ID Managing This Device"))
			
			elif p == "protocol": 
				hardware.append (("attr_" + p, "Protocol (X10/Insteon/ZWave/etc)"))
			
			elif p == "remoteDisplay": 
				device.append (("attr_" + p, "Accessible Remotely (True/False)"))
			
			elif p == "subModel": 
				hardware.append (("attr_" + p, "Sub Model"))
			
			elif p == "supportsAllLightsOnOff": 
				support.append (("attr_" + p, "Included in All Lights On/Off (True/False)"))
			
			elif p == "supportsAllOff": 
				support.append (("attr_" + p, "Included in All Off (True/False)"))
			
			elif p == "supportsStatusRequest": 
				support.append (("attr_" + p, "Can Return a Status Request (True/False)"))
			
			elif p == "supportsColor": 
				support.append (("attr_" + p, "Device supports Color (True/False)"))
			
			elif p == "supportsRGB": 
				support.append (("attr_" + p, "Can use RGB levels (True/False)"))
			
			elif p == "supportsRGBW": 
				support.append (("attr_" + p, "Can use RGBW levels (True/False)"))
				
			elif p == "supportsRGBandWhiteSimultaneously": 
				support.append (("attr_" + p, "Can use RGB levels and White Simultaneously (True/False)"))	
				
			elif p == "supportsTwoWhiteLevels": 
				support.append (("attr_" + p, "Can use two white levels (True/False)"))		
				
			elif p == "supportsTwoWhiteLevelsSimultaneously": 
				support.append (("attr_" + p, "Can use two white levels simultaneously (True/False)"))
				
			elif p == "supportsWhite": 
				support.append (("attr_" + p, "Can use white levels (True/False)"))	
				
			elif p == "supportsWhiteTemperature": 
				support.append (("attr_" + p, "Can use white temperature (True/False)"))				
			
			elif p == "version": 
				hardware.append (("attr_" + p, "Firmware Version"))
			
			elif p == "brightness": 
				current.append (("attr_" + p, "Current Brightness Level"))
			
			elif p == "blueLevel": 
				ledlevels.append (("attr_" + p, "Current Blue Level"))
			
			elif p == "greenLevel": 
				ledlevels.append (("attr_" + p, "Current Green Level"))
			
			elif p == "redLevel": 
				ledlevels.append (("attr_" + p, "Current Red Level"))
			
			elif p == "whiteLevel": 
				ledlevels.append (("attr_" + p, "Current White Level"))
				
			elif p == "whiteLevel2": 
				ledlevels.append (("attr_" + p, "Current White Level 2"))	
				
			elif p == "whiteTemperature": 
				ledlevels.append (("attr_" + p, "Current White Temperature"))
			
			elif p == "onBrightensToDefaultToggle": 
				settings.append (("attr_" + p, "Turning On Brightens to Default Brightness Level (True/False)"))
			
			elif p == "onBrightensToLast": 
				settings.append (("attr_" + p, "Turning On Brightens to Last Brightness (True/False)"))
			
			elif p == "defaultBrightness": 
				settings.append (("attr_" + p, "Default Brightness Level"))
			
			elif p == "ledStates": 
				if len(dev.ledStates) > 0:
					for i in range (1, len(dev.ledStates) + 1):
						settings.append (("custom_ledstate_" + str(i), "LED State %i Value" % i))
					
			elif p == "zoneNames": 
				if len(dev.zoneNames) > 0:
					for i in range (1, len(dev.zoneNames) + 1):
						general1.append (("custom_zonename_" + str(i), "Zone %i Name" % i))
					
			elif p == "zoneEnableList": 
				if len(dev.zoneEnableList) > 0:
					for i in range (1, len(dev.zoneEnableList) + 1):
						general5.append (("custom_zoneenabled_" + str(i), "Zone %i is Enabled (True/False)" % i))
					
			elif p == "zoneMaxDurations": 
				if len(dev.zoneMaxDurations) > 0:
					for i in range (1, len(dev.zoneMaxDurations) + 1):
						general3.append (("custom_zonemax_" + str(i), "Zone %i Maximum Default Duration" % i))
					
			elif p == "zoneScheduledDurations": 		
				for i in range (1, 9):
					general4.append (("custom_zoneschedule_" + str(i), "Zone %i Current Schedule Duration" % i))
		
			elif p == "activeZone": 
				general2.append (("attr_" + p, "Currently Active Zone Number"))
				
			elif p == "zoneCount": 
				general2.append (("attr_" + p, "Total Zones"))
			
			elif p == "pausedScheduleRemainingZoneDuration": 
				general2.append (("attr_" + p, "Duration Remaining on Paused Zone"))
			
			elif p == "pausedScheduleZone": 
				general2.append (("attr_" + p, "Currently Paused Zone Number"))
			
			elif p == "coolIsOn": 
				general1.append (("attr_" + p, "Cooling is Currently On (True/False)"))
			
			elif p == "coolSetpoint": 
				general1.append (("attr_" + p, "Cooling Set Point"))
			
			elif p == "heatIsOn": 
				general2.append (("attr_" + p, "Heating is Currently On (True/False)"))
			
			elif p == "heatSetpoint": 
				general2.append (("attr_" + p, "Heating Set Point"))
			
			elif p == "fanIsOn": 
				general3.append (("attr_" + p, "Fan is Currently On (True/False)"))
			
			elif p == "fanMode": 
				general3.append (("attr_" + p, "Current Fan Mode"))
			
			elif p == "hvacMode": 
				general4.append (("attr_" + p, "Current HVAC Mode"))
			
			elif p == "dehumidifierIsOn": 
				general5.append (("attr_" + p, "Dehumidifier is Currently On (True/False)"))
			
			elif p == "humidifierIsOn": 
				general5.append (("attr_" + p, "Humidifier is Currently On (True/False)"))
			
			elif p == "humiditySensorCount": 
				general5.append (("attr_" + p, "Number of Humidity Sensors"))
			
			elif p == "temperatureSensorCount": 
				general5.append (("attr_" + p, "Number of Temperature Sensors"))
			
			elif p == "humidities": 
				if len(dev.humidities) > 0:
					for i in range (1, len(dev.humidities) + 1):
						general6.append (("custom_humidity_" + str(i), "Humidity Sensor %i Value" % i))
					
			elif p == "temperatures": 
				if len(dev.temperatures) > 0:
					for i in range (1, len(dev.temperatures) + 1):
						general7.append (("custom_temperature_" + str(i), "Temperature Sensor %i Value" % i))

			else:
				other.append (("attr_" + p, p))
			
			
		if len(device) > 0:
			retList += overview
		
		if len(retList) > 0 and len(hardware) > 0:
			retList = self.addLine (retList)
			retList += hardware	
		
		if len(retList) > 0 and len(current) > 0:
			retList = self.addLine (retList)
			retList += current	
		
		
		if len(retList) > 0 and len(general1) > 0:
			retList = self.addLine (retList)
			retList += general1	
		
		if len(retList) > 0 and len(general2) > 0:
			retList = self.addLine (retList)
			retList += general2	
		
		if len(retList) > 0 and len(general3) > 0:
			retList = self.addLine (retList)
			retList += general3	
		
		if len(retList) > 0 and len(general4) > 0:
			retList = self.addLine (retList)
			retList += general4	
		
		if len(retList) > 0 and len(general5) > 0:
			retList = self.addLine (retList)
			retList += general5		
		
		if len(retList) > 0 and len(general6) > 0:
			retList = self.addLine (retList)
			retList += general6		
		
		if len(retList) > 0 and len(general7) > 0:
			retList = self.addLine (retList)
			retList += general7							
		
		if len(retList) > 0 and len(settings) > 0:
			retList = self.addLine (retList)
			retList += settings	
		
		if len(retList) > 0 and len(ledlevels) > 0:
			retList = self.addLine (retList)
			retList += ledlevels	
		
		if len(retList) > 0 and len(energy) > 0:
			retList = self.addLine (retList)
			retList += energy		
			
		if len(retList) > 0 and len(plugin) > 0:
			retList = self.addLine (retList)
			retList += plugin
		
		if len(retList) > 0 and len(state) > 0:
			retList = self.addLine (retList)
			retList += state	
		
		if len(retList) > 0 and len(device) > 0:
			retList = self.addLine (retList)
			retList += device	
		
		if len(retList) > 0 and len(folder) > 0:
			retList = self.addLine (retList)
			retList += folder	
		
		if len(retList) > 0 and len(support) > 0:
			retList = self.addLine (retList)
			retList += support	



		if len(retList) > 0 and len(other) > 0:
			retList = self.addLine (retList)
			retList += other

		#indigo.server.log(allAttribs)

		return retList


	################################################################################
	# LOG WINDOW DEBUGS
	################################################################################	

	#
	# Return debug header with message and closing line
	#
	def debugHeader (self, label, character = "#"):
		# Return 69 character strings
		# Return 69 character strings
		ret =  "\n\n" + self.debugHeaderEx(character)
		ret += self.debugLine(label, character)
		ret += self.debugHeaderEx(character)

		return ret

	#
	# Return debug header line only
	#
	def debugHeaderEx (self, character = "#"):
		# Return 69 character strings
	
		if character == "#":
			ret =  "#####################################################################\n"
			
		elif character == "=":
			ret =  "=====================================================================\n"
			
		elif character == "-":
			ret =  "---------------------------------------------------------------------\n"
			
		elif character == "+":
			ret =  "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n"
				
		elif character == "*":
			ret =  "*********************************************************************\n"
		
		elif character == "!":
			ret =  "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
		
		return ret

	#
	# Return debug message
	#	
	def debugLine (self, label, character = "#"):
		# Return 69 character strings
		return "%s %s %s\n" % (character, label.ljust(65), character)




			