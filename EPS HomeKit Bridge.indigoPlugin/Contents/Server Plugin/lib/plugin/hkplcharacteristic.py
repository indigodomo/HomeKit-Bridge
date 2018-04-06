"""hkpicharacteristic.py: HomeKit characteristic payload data for Homebridge-Indigo2."""

__version__ 	= "1.0.0"

__modname__		= "Homebridge-Indigo2 Payload Data"
__author__ 		= "ColoradoFourWheeler"
__copyright__ 	= "Copyright 2018, ColoradoFourWheeler & EPS"
__credits__ 	= ["ColoradoFourWheeler"]
__license__ 	= "GPL"
__maintainer__ 	= "ColoradoFourWheeler"
__email__ 		= "Indigo Forums"
__status__ 		= "Production"

# Python Modules
import sys
import logging
import json

# Third Party Modules
import indigo

# Package Modules
from ..ifactory.include import ex
from ..ifactory.include import calcs

class HomebridgePayloadCharacteristic:
	"""
	This class does nothing other than allow the user to manually set the values that will output a JSON data stream for HomeKit.
	"""
	
	###
	def __init__(self):
		"""
		An empty class that allows the following attributes to be set.
		"""
		
		try:
			self.logger = logging.getLogger ("Plugin.HomebridgePayloadCharacteristic")
			self.tabtitle = ""			# Title indention on __str__
			self.tabcontent = ""		# Content indention on __str__
			
			#self.factory = factory		# References the Indigo plugin
			
			self.name = ""  			# Characteristic name
			self.maxValue = 0			# Maximum value
			self.minValue = 0			# Minimum value
			self.readonly = False		# Characteristic is read only
			self.notify = True			# Characteristic can be used in notifications
			self.value = None			# Value of the characteristic		
			self.changeMinMax = False	# True when min/max are different than HapNode.JS
					
			self.logger.debug ("{} {} loaded".format(__modname__, __version__))
			
		except Exception as e:
			self.logger.error (ex.stack_trace(e))
			
	###
	def __str__ (self):
		try:
			ret = calcs.generic_unicode_output (self.tabtitle, self.tabcontent, self)
			
		except Exception as e:
			self.logger.error (ex.stack_trace(e))
				
		return ret	
		
	###
	def legacy_populate_from_service (self, obj, charName, charValue):
		"""
		Create a payload characteristic for the service object record passed.  This is transitional until all legacy methods and classes are cut over.
	
		Arguments:
			obj: 		service_* legacy HomeKit service class object
			
		Returns:
			HomebridgePayloadCharacteristic object
		"""
		
		try:
			characteristic = getattr (obj, charName)
			self.name = charName
			self.value = charValue
			
			#if runningAction and charItem["name"] == "On": charItem["value"] = True
			#if not characteristic is None and not value is None and charItem["name"] == characteristic: charItem["value"] = value # Force it to see what it expects to see so it doesn't beachball
			
			self.readonly = characteristic.readonly
			self.notify = characteristic.notify
			
			if "changeMinMax" in dir(characteristic) and characteristic.changeMinMax:
				self.changeMinMax = True
				self.minValue = characteristic.minValue
				self.maxValue = characteristic.maxValue
							
		except Exception as e:
				self.logger.error (ex.stack_trace(e))
				
				









