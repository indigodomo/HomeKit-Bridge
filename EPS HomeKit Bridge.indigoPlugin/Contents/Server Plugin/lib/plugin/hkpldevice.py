"""hkpidevice.py: HomeKit device payload data for Homebridge-Indigo2."""

__version__ 	= "1.0.0"

__modname__		= "Homebridge-Indigo2 Device Payload"
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
import hkplcharacteristic

class HomebridgePayloadDevice:
	"""
	This class does nothing other than allow the user to manually set the values that will output a JSON data stream for HomeKit.
	"""
	
	###
	def __init__(self, factory):
		"""
		An empty class that allows the following attributes to be set.
		"""
		
		try:
			self.logger = logging.getLogger ("Plugin.HomebridgePayloadDevice")
			self.tabtitle = ""			# Title indention on __str__
			self.tabcontent = ""		# Content indention on __str__
			
			self.factory = factory		# References the HomeKit factory
						
			self.alias = None  			# Indigo device alias
			self.url = None  			# Callback URL for Homebridge-Indigo2 to contact us regarding this device
			self.serverId = 0  			# Server that this device is attached to
			self.id = None 				# JSON key
			self.type = None			# HomeKit device details type
			self.versByte = None		# HomeKit device details firmware version
			self.hkcharacteristics = []	# List of HomeKitPayloadCharacteristic records that define the HomeKit device
			self.hkservice = None		# The HomeKit service name for this device
			self.object = None			# Indigo object type that HKI2 will use to log what kind of object it created
					
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
	def legacy_populate_from_service (self, obj, r, serverId, characteristicName = None, characteristicValue = None):
		"""
		Create a payload device for the service object record passed.  This is transitional until all legacy methods and classes are cut over.
	
		Arguments:
			obj: 			service_* legacy HomeKit service class object
			r: 				the JSON 'r' record stored in the server
			serverId:		the server ID of the 'r' record
			characteristicName:		optional characteristic name to force a value
			characteristicValue:	optional characteristic value to force
	
		Returns:
			HomeKitPayloadDevice object
		"""
		
		try:
			try:
				alias = r"{}".format(r["alias"])
			except:
				alias = unicode(r["alias"])
				
			self.alias = alias
			self.url = u"/HomeKit?objId={}&serverId={}&jkey={}".format(str(obj.objId), str(serverId), r["jkey"])
			self.serverId = serverId
			self.id = r["jkey"]
			self.object = r["object"]
			self.hkservice = obj.type
			
			if obj.objId in indigo.devices:
				self.type = self.factory.convert.homekit_type_and_firmware (indigo.devices[serverId].pluginProps["modelValue"], obj.objId, serverId)
				self.versByte = self.factory.convert.homekit_type_and_firmware (indigo.devices[serverId].pluginProps["firmwareValue"], obj.objId, serverId)
			elif obj.objId in indigo.actionGroups:
				self.type = u"Action Group"
				self.versByte = u"{}".format(indigo.server.version)
			
			for charName, charValue in obj.characterDict.iteritems():
				if charName not in dir(obj):
					self.logger.error (u"Unable to find attribute {} in {}: {}".format(charName, obj.alias.value, unicode(obj)))
					continue
				
				characteristic = hkplcharacteristic.HomebridgePayloadCharacteristic()
				
				if not characteristicName is None and not characteristicValue is None and characteristicName == charName:
					# Don't use the value in the object, use the value passed to the method instead
					characteristic.legacy_populate_from_service (obj, charName, characteristicValue)
				else:
					characteristic.legacy_populate_from_service (obj, charName, charValue)
				
				characteristic.tabcontent = "\t\t"
				self.hkcharacteristics.append(characteristic)
			
			#indigo.server.log("Class:\n{}".format(unicode(self)))
			
			data = calcs.generic_class_to_dict(self)
			#indigo.server.log("JSON Output:\n{}".format(json.dumps(data, indent = 4)))
			
			return data
							
		except Exception as e:
				self.logger.error (ex.stack_trace(e))
				





























