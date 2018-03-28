"""processor.py: Picks up all Indigo calls and transfers them to their proper libraries."""

__version__ 	= "1.0.0"

__modname__		= "Indigo Plugin Redirector"
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

class RedirectProcessor:
	"""
	Manages JSON data storage inside of form definitions.
	"""
	
	#global __version__
	
	def __init__(self, factory):
		try:
			self.factory = factory		# References the Indigo plugin
		
			self.logger = logging.getLogger ("Plugin.processor")
		
			self.logger.debug ("{} {} loaded".format(__modname__, __version__))
			
		except Exception as e:
			self.logger.error (ex.stack_trace(e))
			

	################################################################################	
	# FACTORY CUSTOM: SEND ALL CALLS TO THEIR HANDLERS
	################################################################################

	def formFieldChanged (self, valuesDict, typeId, devId, setDefault=False): return self.factory.ui.formFieldChanged (valuesDict, typeId, devId, setDefault)
	
	def fieldStuffIndex (self, filter, valuesDict, typeId, targetId): return self.factory.jstuff.fieldStuffIndex (filter, valuesDict, typeId, targetId)
		
	################################################################################	
	# INDIGO NATIVE: SEND ALL CALLS TO THEIR HANDLERS
	################################################################################
	
	