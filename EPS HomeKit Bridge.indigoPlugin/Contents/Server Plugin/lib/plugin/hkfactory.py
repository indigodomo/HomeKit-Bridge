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
import hkconversions

# Package Modules
import hkplprocessor  # Payload processor
import hkpldevice  # Payload device class


class HomeKitFactory:
	"""
	Primary launch point for all things HomeKit.
	"""
	
	HKCACHE = {}  			# All HomeKit device payloads, updated dynamically as Indigo device changes are detected
	HKDEFINITIONS = {}  	# All service definitions for all HomeKit devices so that HKCACHE can update payloads
	HKCOMPLICATIONS = {}  	# All defined complications
	#HKSERVICES = {}  		# All HomeKit services
	#HKCHARACTERISTICS = {}	# All HomeKit characteristics
	
	###
	def __init__(self, factory):
		if factory is None: return # pre-loading before init
		
		try:
			self.logger = logging.getLogger ("Plugin.HomeKitFactory")
			
			self.factory = factory		# References the Indigo plugin
			self.init_libraries()		# Initial global libraries
		
			self.logger.debug ("{} {} loaded".format(__modname__, __version__))
			
		except Exception as e:
			self.logger.error (ex.stack_trace(e))
			
	###
	def init_libraries (self):
		"""
		Initialize any libraries that need to be accessed via this factory.
		"""
		
		try:
			self.convert = hkconversions.HomeKitDataConversion (self)
			self.api = hkplprocessor.HomebridgePayloadProcessor (self)
			
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
			return payload.legacy_populate_from_service (obj, r, serverId)
	
		except Exception as e:
			self.logger.error (ex.stack_trace(e))
				

	###
	def legacy_cache_device (self, r, serverId, norefresh = False):
		"""
		Creates or refreshes the service object in cache.
		
		Arguments:
			r:			JSON record to get the service object for
			serverId:	Indigo device Id of the server hosting this r device
			norefresh:	when false the attributes and payload won't refresh - built for calling back to HBI2 since it would have refreshed prior to that anyway
			
		Returns:
			payload:	the cached payload
			obj:		the service object
		"""
		
		try:
			if r["jkey"] in self.HKDEFINITIONS:
				if not norefresh: self.logger.threaddebug (u"Updating cache for '{}'".format(r["alias"]))
				if norefresh: self.logger.threaddebug (u"Retrieving cache for '{}'".format(r["alias"]))
				obj = self.HKDEFINITIONS[r["jkey"]]
				if not norefresh: obj.setAttributes()  # Refresh the characteristic values
			else:
				# Cache the service object
				self.logger.threaddebug (u"Caching '{}'".format(r["alias"]))
				obj = self.api.legacy_get_homekit_object (r["id"], serverId, r["hktype"])
				self.HKDEFINITIONS[r["jkey"]] = obj
			
			# Cache the API payload
			if not norefresh: 
				payload = self.legacy_get_payload(obj, r, serverId)
				self.HKCACHE[r["jkey"]] = payload
			else:
				payload = self.HKCACHE[r["jkey"]]
			
			return self.HKCACHE[r["jkey"]], obj
		
		except Exception as e:
			self.logger.error (ex.stack_trace(e))
			
		return {}, None

	###
	def process_incoming_api_call (self, request, query): return self.api.process_incoming_api_call (request, query)
		
			











