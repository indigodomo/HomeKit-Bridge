"""hkconversoins.py: Conversion methods for various HomeKit data points."""

__version__ 	= "1.0.0"

__modname__		= "HomeKit Data Conversion"
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

class HomeKitDataConversion:
	"""
	Converts data from various sources into HomeKit usable information.
	"""
	
	###
	def __init__(self, factory):
		"""
		An empty class that allows the following attributes to be set.
		"""
		
		try:
			self.logger = logging.getLogger ("Plugin.HomeKitDataConversion")
			self.tabtitle = ""			# Title indention on __str__
			self.tabcontent = ""		# Content indention on __str__
			
			self.factory = factory		# References the HomeKit factory
						
			self.logger.debug ("{} {} loaded".format(__modname__, __version__))
			
		except Exception as e:
			self.logger.error (ex.stack_trace(e))
			
	###
	def homekit_type_and_firmware (self, keyword, devId, serverId):
		"""
		Resolves a keyword to a value for either type or firmware when viewing HomeKit device details.
		
		Arguments:
			keyword:	the keyword to resolve
			devId:		the Indigo device Id for the device being evaluated
			serverId:	the Indigo device Id for the HKB server this device is on
	
		Returns:
			String of the converted value
		"""
		
		try:
			if devId not in indigo.devices:
				self.logger.error (u"Unable to process type or firmware because device Id {} no longer exists in Indigo".format(devId))
				return "Error"
				
			self.logger.debug (u"Converting {} keyword for HomeKit type or firmware on '{}'".format(keyword, indigo.devices[devId].name))
			
			if keyword is None or keyword == "":
				return "N/A"									
			elif keyword == "indigoModel":
				return u"{}".format(indigo.devices[devId].model)
			elif keyword == "indigoSubmodel":
				return u"{}".format(indigo.devices[devId].subModel)	
			elif keyword == "indigoModelSubmodel":
				if indigo.devices[devId].model != "" and indigo.devices[devId].subModel != "":
					return u"{}: {}".format(indigo.devices[devId].model, indigo.devices[devId].subModel)
				elif indigo.devices[devId].model != "" and indigo.devices[devId].subModel == "":
					return u"{}".format(indigo.devices[devId].model)
				else:
					return u"{}".format(indigo.devices[devId].subModel)
			elif keyword == "indigoName":
				return u"{}".format(indigo.devices[devId].name)
			elif keyword == "indigoType":
				return u"{}".format(str(type(indigo.devices[devId])).replace("<class '", "").replace("'>", "").replace("indigo.",""))
			elif keyword == "pluginName":
				if indigo.devices[devId].pluginId != "":
					plugin = indigo.server.getPlugin(indigo.devices[devId].pluginId)
					#indigo.server.log(unicode(plugin))
					return u"{}".format(plugin.pluginDisplayName)
				else:
					return "Indigo"
			elif keyword == "pluginType":
				if indigo.devices[devId].deviceTypeId != "":
					return u"{}".format(indigo.devices[devId].deviceTypeId)	
				else:
					return u"{}".format(str(type(indigo.devices[devId])).replace("<class '", "").replace("'>", "").replace("indigo.",""))
			elif keyword == "pluginVersion":
				if indigo.devices[devId].pluginId != "":
					plugin = indigo.server.getPlugin(indigo.devices[devId].pluginId)
					#indigo.server.log(unicode(plugin))
					return u"{}".format(plugin.pluginVersion)	
				else:
					return u"{}".format(indigo.server.version)
			elif keyword == "indigoVersion":
				return u"{}".format(indigo.devices[devId].version)	
			else:
				self.logger.warning (u"Unable to convert {} keyword for HomeKit type or firmware on '{}'".format(keyword, indigo.devices[devId].name))		
		
		except Exception as e:
			self.logger.error (ex.stack_trace(e))






















