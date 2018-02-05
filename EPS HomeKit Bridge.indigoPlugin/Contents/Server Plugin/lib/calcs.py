# lib.calcs - Calculation utilities
#
# Copyright (c) 2018 ColoradoFourWheeler / EPS
#

import indigo

import ext

#
# Convert celsius to fahrenheit and fahrenheit to celsius
#
def temperature (value, convertC = False, precision = 1):
	try:
		if convertC:
			# Convert value to celsius
			value = float(value)
			value = (value - 32) / 1.8000
			value = round(value, precision)
		
			if precision == 0: return int(value)
		
			return value
		
		else:
			# Default: convert value to fahrenheit
			value = float(value)
			value = (value * 1.8000) + 32
			value = round(value, precision)
		
			if precision == 0: return int(value)
		
			return value
			
	except Exception as e:
		indigo.server.log (ext.getException(e), isError=True)	
		
#
# Determine high float value from string and device state
#
def getHighFloatValue (dev, stateName, strVar):
	try:
		if stateName in dev.states == False: return ""
	
		if strVar == "" or float(dev.states[stateName]) > float(strVar):
			return str(dev.states[stateName])
		else:
			return strVar
			
	except Exception as e:
		indigo.server.log (ext.getException(e), isError=True)
		return ""
		
#
# Determine low float value from string and device state
#
def getLowFloatValue (dev, stateName, strVar):
	try:
		if stateName in dev.states == False: return ""
	
		if strVar == "" or float(dev.states[stateName]) < float(strVar):
			return str(dev.states[stateName])
		else:
			return strVar
			
	except Exception as e:
		indigo.server.log (ext.getException(e), isError=True)
		return ""