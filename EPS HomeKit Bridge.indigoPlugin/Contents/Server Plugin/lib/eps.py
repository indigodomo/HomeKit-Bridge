# lib.eps - The factory that starts everything
#
# Copyright (c) 2018 ColoradoFourWheeler / EPS
#

import indigo
import logging
import sys

import ext

from plug import plug
#from update import update # Obsolete by Plugin Store November 2017
from ui import ui
from support import support
from jstash import jstash

class eps:
	VERSION = "3.0.0"
	
	#
	# Initialize the  class
	#
	def __init__(self, plugin):
		if plugin is None: return # pre-loading before init
		
		try:
			#self.memory_summary ()
			self.plugin = plugin
		
			# Sets the log format in the plugin and across all modules that can reference the plugin
			logformat = logging.Formatter('%(asctime)s.%(msecs)03d\t%(levelname)-12s\t%(name)s\t%(funcName)-25s\t%(msg)s', datefmt='%Y-%m-%d %H:%M:%S')
			plugin.plugin_file_handler.setFormatter(logformat)
		
			# Sets the localized logger with the module name appended
			self.logger = logging.getLogger ("Plugin.factory")
		
			# Initialize prefs and libraries
			self._prefInit ()
			plugin.indigo_log_handler.setLevel(int(plugin.pluginPrefs["logLevel"]))
			self._libInit ()
		
			# Do any previous generation cleanup
			self._cleanUp(plugin)
		
			# Done with init
			self.logger.threaddebug("EPS Factory {0} initialization complete".format(self.VERSION))
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
		
		
	#
	# See what libraries are needed and initialize them
	#
	def _libInit (self):
		try:
			# Initialize the main plugin engine
			self.plug = plug (self)
			#self.update = update (self) # Obsolete by Plugin Store November 2017
			self.ui = ui (self)
			self.support = support (self)
			self.jstash = jstash (self)
		
			self.logger.threaddebug("Dynamic libraries complete")
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
	#
	# Load libraries
	#
	def loadLibs (self, lib):
		liblist = []
		
		if type(lib) is list:
			liblist = lib
		else:
			liblist = [list]
			
		for lib in liblist:
			if lib == "cache":
				self.logger.threaddebug("Loading cache library")
				from cache import cache #, cacheDev
				self.cache = cache(self)
				
			if lib == "plugcache":
				self.logger.threaddebug("Loading plugin cache")
				from plugcache import plugcache
				self.plugcache = plugcache (self)
				
			if lib == "plugdetails" or lib == "actions3":
				self.logger.threaddebug("Loading plugin details library")
				from plugdetails import plugdetails
				self.plugdetails = plugdetails (self)	
				
			if lib == "actions":
				self.logger.threaddebug("Loading actions library")
				from actions import actions
				self.act = actions (self)
				
			if lib == "actionsv2":
				self.logger.threaddebug("Loading actions v2 library")
				from actions_v2 import actions
				self.actv2 = actions (self)	
				
			if lib == "actions3":
				# NOTE: The plugcache library MUST be loaded FIRST because the init of actions relies on it
				self.logger.threaddebug("Loading actions 3 library")
				from actions3 import actions
				self.actv3 = actions (self)		
				
			if lib == "devices":
				self.logger.threaddebug("Loading device extensions library")
				from devices import devices
				self.devices = devices (self)
				
			if lib == "http" or lib == "api":
				self.logger.threaddebug("Loading http server library")
				from httpsvr import httpServer
				self.http = httpServer (self)
				
			if lib == "api":
				self.logger.threaddebug("Loading RESTful api server library")
				from apienh import api
				self.api = api (self)	
				
			if lib == "homekit":
				self.logger.threaddebug("Loading HomeKit api server library")
				from homekit import HomeKit
				self.homekit = HomeKit (self)
											
			if lib == "conditions":
				self.logger.threaddebug("Loading conditions library")
				from conditions import conditions
				self.cond = conditions(self)
				
				# Conditions require plug cache
				if "plugcache" in dir(self):
					if self.plugcache is None:
						X = 1				
				else:
					self.logger.threaddebug("Loading plugin cache")
					from plugcache import plugcache
					self.plugcache = plugcache (self)
					
		self.logger.threaddebug("User libraries complete")
		
	#
	# Initialize the default preferences
	#
	def _prefInit (self):
		# Set any missing prefs
		self.plugin.pluginPrefs = ext.validateDictValue (self.plugin.pluginPrefs, "logLevel", "20", True)
		self.plugin.pluginPrefs = ext.validateDictValue (self.plugin.pluginPrefs, "pollingMode", "realTime", True)
		self.plugin.pluginPrefs = ext.validateDictValue (self.plugin.pluginPrefs, "pollingInterval", 1, True)
		self.plugin.pluginPrefs = ext.validateDictValue (self.plugin.pluginPrefs, "pollingFrequency", "s", True)
		
	#
	# If we are cleaning up from previous generations do that here
	#
	def _cleanUp (self, plugin):
		if ext.valueValid (plugin.pluginPrefs, "debugMode"): 
			self.logger.info(u"Upgraded plugin preferences from pre-Indigo 7, depreciated preferences removed")
			del plugin.pluginPrefs["debugMode"]
			
	#
	# Only for use in dev environment with Pympler installed so we can track memory usage
	def memory_summary(self):
		# Only import Pympler when we need it. We don't want it to
		# affect our process if we never call memory_summary.
		
		caller = sys._getframe(1).f_code.co_name # So we can reference the caller
		
		from pympler import summary, muppy
		mem_summary = summary.summarize(muppy.get_objects())
		rows = summary.format_(mem_summary)
		indigo.server.log ('\n\nCALLED BY: ' + caller + '\n\n' + '\n'.join(rows)	)	
				
		
	#
	# Call back a plugin method if it exists
	#
	def raiseEvent (self, method, args):
		retval = None
		
		try:
			if method in dir(self.plugin):
				func = getattr(self.plugin, method)
				
				if len(args) > 0: 
					retval = func(*args)
				else:
					retval = func()
					
		except Exception as e:
			self.logger.error (ext.getException(e))			
			
		return retval
				
				
				
				
				
				
				
				
				
				
				
				
				
				
				
				
				
				
				
				
				
				
				
				
				
				
				
				
				
				
				
				