# lib.iutil - Some useful miscellaneous utilities
#
# Copyright (c) 2018 ColoradoFourWheeler / EPS
#

import indigo

import ext

#
# Add items to a batch state update
#
def updateState (key, value, states = [], uiValue = None, decimalPlaces = None):
	try:
		newState = {}
		newState["key"] = key
		newState["value"] = value
		
		if uiValue is not None: newState["uiValue"] = uiValue
		if decimalPlaces is not None: newState["decimalPlaces"] = decimalPlaces
		
		states.append(newState)
		
		return states
	
	except Exception as e:
		self.logger.error (ext.getException(e))	