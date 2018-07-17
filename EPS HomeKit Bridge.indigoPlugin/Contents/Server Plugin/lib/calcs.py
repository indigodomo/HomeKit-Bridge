# lib.calcs - Calculation utilities
#
# Copyright (c) 2018 ColoradoFourWheeler / EPS
#

import indigo
import math

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

#
# Convert Kelvin to RGB
#		
def convert_K_to_RGB(color_temperature):
    """
    Converts from K to RGB, algorithm courtesy of 
    http://www.tannerhelland.com/4435/convert-temperature-rgb-algorithm-code/
    """
    #range check
    if color_temperature < 1000: 
        color_temperature = 1000
    elif color_temperature > 40000:
        color_temperature = 40000
    
    tmp_internal = color_temperature / 100.0
    
    # red 
    if tmp_internal <= 66:
        red = 255
    else:
        tmp_red = 329.698727446 * math.pow(tmp_internal - 60, -0.1332047592)
        if tmp_red < 0:
            red = 0
        elif tmp_red > 255:
            red = 255
        else:
            red = tmp_red
    
    # green
    if tmp_internal <=66:
        tmp_green = 99.4708025861 * math.log(tmp_internal) - 161.1195681661
        if tmp_green < 0:
            green = 0
        elif tmp_green > 255:
            green = 255
        else:
            green = tmp_green
    else:
        tmp_green = 288.1221695283 * math.pow(tmp_internal - 60, -0.0755148492)
        if tmp_green < 0:
            green = 0
        elif tmp_green > 255:
            green = 255
        else:
            green = tmp_green
    
    # blue
    if tmp_internal >=66:
        blue = 255
    elif tmp_internal <= 19:
        blue = 0
    else:
        tmp_blue = 138.5177312231 * math.log(tmp_internal - 10) - 305.0447927307
        if tmp_blue < 0:
            blue = 0
        elif tmp_blue > 255:
            blue = 255
        else:
            blue = tmp_blue
    
    return red, green, blue		