"""ifactory.py: Rapid and standardized plugin development libary for Indigo Home Automation."""

__version__ 	= "1.0.0"

__modname__		= "Indigo Plugin Factory"
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

# Third Party Modules
import indigo

# Package Modules
from include import ex
from include import jstuff
from include import processor
from include import ui

class IFactory:
	"""
	Base class for Indigo plugin development, all calls start here.
	"""
	
	#global __version__
	
	def __init__(self, plugin):
		"""
		Start the factory with references back to the base plugin.
		
		Arguments:
		plugin: Indigo plugin
		"""
	
		try:
			if plugin is None: return # pre-loading before init
			
			self.PluginBase = plugin	# References the Indigo plugin
			self._set_log_format()		# Set the standard log format
			self._init_libraries()		# Initialize the factory libs
		
			self.logger.debug ("{} {} loaded".format(__modname__, __version__))
			
		except Exception as e:
			self.logger.error (ex.stack_trace(e))
			
	###
	def _callback (self, args, funcname = None, prefix = None, suffix = None):
		"""
		Validates a method exists in the plugin base and if it does it's called and returned to the caller.
		"""
		
		try:
			caller = sys._getframe(1).f_code.co_name
			
			if funcname is None:
				funcname = "on" + caller
				
			if suffix: funcname += suffix
			if prefix: funcname = prefix + funcname
			
			if funcname in dir(self.PluginBase):	
				if caller != "runConcurrentThread":		
					#self.logger.threaddebug ("Raising {0} in plugin.py from call to {1}".format(funcname, caller))
					pass
			
				return self.raise_event (funcname, args)

			self.logger.info (funcname)
		
		except Exception as e:
			self.logger.error (ex.stack_trace(e))
			
		return None			
	
	###	
	def raise_event (self, method, args):
		"""
		Raises an event in the base plugin and returns the results.
		"""
		
		try:
			if method in dir(self.PluginBase):
				func = getattr(self.PluginBase, method)
				
				if len(args) > 0: 
					return func(*args)
				else:
					return func()
					
		except Exception as e:
			self.logger.error (ex.stack_trace(e))			
			
		return None		
	
	###
	def _init_libraries (self):
		"""
		Preload the main function libraries for the factory.
		"""
		
		try:
			self.jstuff = jstuff.JStuff(self)
			self.process = processor.RedirectProcessor(self)
			self.ui = ui.UserInterface(self)
		
		except Exception as e:
			self.logger.error (ex.stack_trace(e))
			
	###
	def _set_log_format (self):
		"""
		Sets the log format for all plugin logging and initializes this modules log.
		"""
		
		logformat = logging.Formatter('%(asctime)s.%(msecs)03d-25s [%(levelname)-12s] %(name)-45s  %(funcName)-45s  %(msg)s', datefmt='%Y-%m-%d %H:%M:%S')
		self.PluginBase.plugin_file_handler.setFormatter(logformat)
	
		# Sets the localized logger with the module name appended
		self.logger = logging.getLogger ("Plugin.ifactory")