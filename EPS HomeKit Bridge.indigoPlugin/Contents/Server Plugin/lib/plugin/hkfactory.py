"""hkfactory.py: Base HomeKit Indigo integration class."""

__version__ 	= "1.0.0"

__modname__		= "HomeKit Integration Factory for Indigo"
__author__ 		= "ColoradoFourWheeler"
__copyright__ 	= "Copyright 2018, ColoradoFourWheeler & EPS"
__credits__ 	= ["ColoradoFourWheeler"]
__license__ 	= "GPL"
__maintainer__ 	= "ColoradoFourWheeler"
__email__ 		= "Indigo Forums"
__status__ 		= "Production"

# Python Modules
import sys
import os
import inspect
import logging
import linecache

# Third Party Modules
import indigo
from ..ifactory.include import ex

# Package Modules
import hkpldevice  # Payload device class

class HomeKitFactory:
	"""
	Primary launch point for all things HomeKit.
	"""
	
	###
	def __init__(self, factory):
		if factory is None: return # pre-loading before init
		
		try:
			self.logger = logging.getLogger ("Plugin.HomeKitFactory")
			
			self.factory = factory		# References the Indigo plugin
		
			self.logger.debug ("{} {} loaded".format(__modname__, __version__))
			
		except Exception as e:
			self.logger.error (ex.stack_trace(e))
			
	###
	def legacy_get_payload (self, obj, r, serverId):
		"""
		Create a payload device for the service object record passed.  This is transitional until all legacy methods and classes are cut over.
	
		Arguments:
			obj: 		service_* legacy HomeKit service class object
			r: 			the JSON 'r' record stored in the server
			serverId:	the server ID of the 'r' record
		Returns:
			HomeKitPayloadDevice object
		"""
	
		try:
			payload = hkpldevice.HomebridgePayloadDevice (self)
			payload.legacy_populate_from_service (obj, r, serverId)
	
		except Exception as e:
				self.logger.error (ex.stack_trace(e))