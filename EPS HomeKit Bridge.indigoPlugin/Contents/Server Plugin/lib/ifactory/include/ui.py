"""ui.py: Handles all core user interface callbacks and form interaction."""

__version__ 	= "1.0.0"

__modname__		= "Indigo Plugin User Interface"
__author__ 		= "ColoradoFourWheeler"
__copyright__ 	= "Copyright 2018, ColoradoFourWheeler & EPS"
__credits__ 	= ["ColoradoFourWheeler"]
__license__ 	= "GPL"
__maintainer__ 	= "ColoradoFourWheeler"
__email__ 		= "Indigo Forums"
__status__ 		= "Production"

# Python Modules
import logging
import sys
import json

# Third Party Modules
import indigo

# Package Modules
import ex

# Enumerations
kDeviceVersion = "ipf_deviceVersion"

class UserInterface:
	"""
	Handle callbacks and dynmaic list generation.
	"""
	
	
	def __init__(self, factory):
		try:
			self.factory = factory		# References the Indigo plugin
			self.logger = logging.getLogger ("Plugin.ui")
			self.logger.debug ("{} {} loaded".format(__modname__, __version__))
			
			self.deviceFieldCache = {}  # For retrieving defaults and knowing if a field changed
			
		except Exception as e:
			self.logger.error (ex.stack_trace(e))
			
			
	###	
	def formFieldChanged (self, valuesDict, typeId, devId, setDefault):
		"""
		Called from the plugin whenever any form field is changed, then attempts to raise an event in the plugin or ifactory and returns the result.
		
		Arguments:
		valuesDict = form fields
		typeId = device type Id
		devId = device Id
		setDefault = read last list retrieved for this field and default to the first value if the field is blank or its value doesn't exist on the list
		"""
		
		try:
			errorsDict = indigo.Dict()
			
			# If there's no version then add it, after this version changes can only happen elsewhere
			if kDeviceVersion not in valuesDict: valuesDict[kDeviceVersion] = self.factory.PluginBase.pluginVersion
			
			# Process through jstuff
			(valuesDict, cbErrors) = self.factory.jstuff.onformFieldChanged (valuesDict, typeId, devId)
			if cbErrors: return (valuesDict, cbErrors)
			
			# Plugin callbacks
			callback = self.factory._callback ([])  # Base callback
			if callback: 
				(valuesDict, cbErrors) = callback
				if cbErrors: return (valuesDict, cbErrors)
				
			cleantypeId = ''.join(e for e in typeId if e.isalnum())	 # Scrub type ID to be a valid function name
				
			callback = self.factory._callback ([valuesDict, typeId, devId], None, cleantypeId + "_")  # Device type prefix callback
			if callback: 
				(valuesDict, cbErrors) = callback
				if cbErrors: return (valuesDict, cbErrors)	
			
			callback = self.factory._callback ([valuesDict, typeId, devId], None, None, "_" + cleantypeId)  # Device type suffix callback
			if callback: 
				(valuesDict, cbErrors) = callback
				if cbErrors: return (valuesDict, cbErrors)
			
		except Exception as e:
			self.logger.error (ex.stack_trace(e))
			
		return (valuesDict, errorsDict)














