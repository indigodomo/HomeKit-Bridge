# eps.support - Various support functions
#
# Copyright (c) 2018 ColoradoFourWheeler / EPS
#

import indigo
import logging

import ext

class support:
	#
	# Initialize the  class
	#
	def __init__(self, factory):
		try:
			self.factory = factory
		
			self.logger = logging.getLogger ("Plugin.support")
			
		except Exception as e:
			self.logger.error (ext.getException(e))
	
	# Show basic version information
	def pluginMenuSupportInfo (self, returnString = False):
		try:
			ret = ""
			ret += self.factory.ui.debugHeader (self.factory.plugin.pluginDisplayName)
			ret += self.factory.ui.debugLine (" ")
			ret += self.factory.ui.debugLine ("Plugin Version      : {0}".format(self.factory.plugin.pluginVersion))
			ret += self.factory.ui.debugLine ("Template Version    : {0}".format(self.factory.plugin.TVERSION))
			ret += self.factory.ui.debugLine ("Core Engine Version : {0}".format(self.factory.VERSION))
			ret += self.factory.ui.debugLine ("Indigo Version      : {0}".format(indigo.server.version))
			ret += self.factory.ui.debugLine ("Indigo API Version  : {0}".format(indigo.server.apiVersion))
			ret += self.factory.ui.debugLine (" ")
			
			if returnString: return ret
			
			ret += self.factory.ui.debugLine ("Alphas, Betas and Pre-Releases can be downloaded from:")
			ret += self.factory.ui.debugLine ("   https://github.com/Colorado4Wheeler")
			ret += self.factory.ui.debugLine (" ")
			ret += self.factory.ui.debugLine ("All support inquiries, questions or comments go to:")
			ret += self.factory.ui.debugLine ("   http://forums.indigodomo.com/viewforum.php?f=192")
			ret += self.factory.ui.debugLine (" ")
			ret += self.factory.ui.debugLine ("Copyright (c) 2018 - Colorado4Wheeler & EPS")
			ret += self.factory.ui.debugLine (" ")
			ret += self.factory.ui.debugHeaderEx ()
			
			self.logger.info (ret)
			
		except Exception as e:
			self.logger.error (ext.getException(e))
					
	#
	# Show a dump of all important information that the user can send to us
	#
	def dumpAll (self):
		try:
			ret = self.pluginMenuSupportInfo (True)
			
			ret += self._getPluginPrefs()

			ret += self._getCacheDump ()			
			
			ret += self._getLocalDevices () # Always last so it shows at the bottom
			
			ret += self.factory.ui.debugLine (" ")
			ret += self.factory.ui.debugHeaderEx ()
			
			self.logger.info (ret)
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
	#
	# Show a dump of all important information that the user can send to us
	#
	def dumpPlugin (self):
		try:
			ret = self.pluginMenuSupportInfo (True)
			
			ret += self._getPluginPrefs()
			
			ret += self._getLocalDevices ()
			
			ret += self.factory.ui.debugLine (" ")
			ret += self.factory.ui.debugHeaderEx ()
			
			self.logger.info (ret)
		
		except Exception as e:
			self.logger.error (ext.getException(e))	


	#
	# Add plugin preferences to dump
	#
	def _getPluginPrefs (self):
		try:
			ret = self.factory.ui.debugHeaderEx ("=")
			ret += self.factory.ui.debugLine ("PLUGIN PREFERENCES", "=")
			ret += self.factory.ui.debugHeaderEx ("=")
			
			for prop, value in self.factory.plugin.pluginPrefs.iteritems():
				ret += self.factory.ui.debugLine (prop + " = " + unicode(value), "=")
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return ret


	#
	# Add plugin devices to support dump
	#
	def _getLocalDevices (self):
		try:
			devs = indigo.devices.iter(self.factory.plugin.pluginId)
			if devs is not None:
				ret = self.factory.ui.debugHeaderEx ("=")
				ret += self.factory.ui.debugLine ("PLUGIN DEVICES", "=")
				ret += self.factory.ui.debugHeaderEx ("=")
				
				for dev in devs:
					ret += self.factory.ui.debugHeaderEx ("*")
					ret += self.factory.ui.debugLine ("'{0}' ({1})".format(dev.name, str(dev.id)), "*")
					ret += self.factory.ui.debugHeaderEx ("*")
					
					ret += self.factory.ui.debugHeaderEx ("+")
					ret += self.factory.ui.debugLine ("Attributes", "+")
					ret += self.factory.ui.debugHeaderEx ("+")
		
					for prop in [a for a in dir(dev) if not a.startswith('__') and not callable(getattr(dev,a))]:
						if prop != "states" and prop != "ownerProps" and prop != "pluginProps" and prop != "globalProps":
							value = getattr(dev, prop)
							ret += self.factory.ui.debugLine (prop + " = " + unicode(value), "+")
							
					ret += self.factory.ui.debugHeaderEx ("+")
					ret += self.factory.ui.debugLine ("Configuration", "+")
					ret += self.factory.ui.debugHeaderEx ("+")
		
					for prop, value in dev.pluginProps.iteritems():
						ret += self.factory.ui.debugLine (prop + " = " + unicode(value), "+")
					
					ret += self.factory.ui.debugHeaderEx ("+")
					ret += self.factory.ui.debugLine ("States", "+")
					ret += self.factory.ui.debugHeaderEx ("+")
		
					for state, value in dev.states.iteritems():
						ret += self.factory.ui.debugLine (state + " = " + unicode(value), "+")
						
							
							
				return ret
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
		

	#
	# Add cache info to support dump
	#
	def _getCacheDump (self):
		try:
			if "cache" in dir(self.factory):
				ret = self.factory.ui.debugHeaderEx ("=")
				ret += self.factory.ui.debugLine ("CACHE", "=")
				ret += self.factory.ui.debugHeaderEx ("=")
				
				if len(self.factory.cache.items) == 0:
					ret += self.factory.ui.debugLine ("Cache is empty", "=")
					ret += self.factory.ui.debugHeaderEx ("=")
					return ret
					
				ret += self.factory.ui.debugLine ("Cache Summary", "=")
				ret += self.factory.ui.debugLine (" ", "=")
				
				ret += self.factory.ui.debugLine ("Items: " + str(len(self.factory.cache.items)), "=")
				ret += self.factory.ui.debugLine (" ", "=")
				
				ret += self.factory.ui.debugHeaderEx ("+")
				ret += self.factory.ui.debugLine ("Cache Details", "+")
				ret += self.factory.ui.debugHeaderEx ("+")
				
				variables = ""
				devices = ""
				actiongroups = ""
				watchingIds = []
				
				for item in self.factory.cache.items:
					if item is not None:
						cacheItem = ""
						
						cacheItem +=     self.factory.ui.debugLine ("Type:        {0}".format(item.itemType), "+")
						cacheItem +=     self.factory.ui.debugLine ("Name:        {0}".format(item.name), "+")
						cacheItem +=     self.factory.ui.debugLine ("ID:          {0}".format(item.id), "+")
						
						if item.itemType == "Device":
							cacheItem += self.factory.ui.debugLine ("Address:     {0}".format(item.address), "+")
							cacheItem += self.factory.ui.debugLine ("Device Type: {0}".format(item.deviceTypeId), "+")
							cacheItem += self.factory.ui.debugLine ("Plugin:      {0}".format(item.pluginId), "+")
					
						if len(item.watching) > 0:
							cacheItem +=     self.factory.ui.debugLine ("Watching:", "+")
						
						for watcher in item.watching:
							if watcher.id in watchingIds:
								pass
							else:
								watchingIds.append (watcher.id)
								
							cacheItem += self.factory.ui.debugLine ("   ID: {0}".format(watcher.id), "+")
							if len(watcher.states) > 0: 
								cacheItem += self.factory.ui.debugLine ("      States:", "+")
								for state in watcher.states:
									cacheItem += self.factory.ui.debugLine ("         {0}".format(state), "+")	
								
							if len(watcher.properties) > 0: 
								cacheItem += self.factory.ui.debugLine ("      Properties:", "+")
								for prop in watcher.properties:
									cacheItem += self.factory.ui.debugLine ("         {0}".format(prop), "+")	
								
							if len(watcher.attributes) > 0: 
								cacheItem += self.factory.ui.debugLine ("      Attributes:", "+")
								for attr in watcher.attributes:
									cacheItem += self.factory.ui.debugLine ("         {0}".format(attr), "+")	
								
							if len(watcher.states) > 0 or len(watcher.properties) > 0 or len(watcher.attributes) > 0: cacheItem += self.factory.ui.debugLine (" ", "+")
							
						if len(item.watchedBy) > 0:
							cacheItem +=     self.factory.ui.debugLine ("Watched By:", "+")
							
						for watcher in item.watchedBy:
							cacheItem += self.factory.ui.debugLine ("   ID: {0}".format(watcher.id), "+")
							if len(watcher.states) > 0: 
								cacheItem += self.factory.ui.debugLine ("      States:", "+")
								for state in watcher.states:
									cacheItem += self.factory.ui.debugLine ("         {0}".format(state), "+")	
								
							if len(watcher.properties) > 0: 
								cacheItem += self.factory.ui.debugLine ("      Properties:", "+")
								for prop in watcher.properties:
									cacheItem += self.factory.ui.debugLine ("         {0}".format(prop), "+")	
								
							if len(watcher.attributes) > 0: 
								cacheItem += self.factory.ui.debugLine ("      Attributes:", "+")
								for attr in watcher.attributes:
									cacheItem += self.factory.ui.debugLine ("         {0}".format(attr), "+")	
							if len(watcher.states) > 0 or len(watcher.properties) > 0 or len(watcher.attributes) > 0: cacheItem += self.factory.ui.debugLine (" ", "+")
												
						cacheItem += self.factory.ui.debugLine (" ", "+")
						
						if item.itemType == "Device": devices += cacheItem
						if item.itemType == "Variable": variables += cacheItem
						if item.itemType == "ActionGroup": actiongroups += cacheItem
						
				ret += self.factory.ui.debugHeaderEx ("-")
				ret += self.factory.ui.debugLine ("Devices", "-")
				ret += self.factory.ui.debugHeaderEx ("-")
				ret += devices
				
				ret += self.factory.ui.debugHeaderEx ("-")
				ret += self.factory.ui.debugLine ("Variables", "-")
				ret += self.factory.ui.debugHeaderEx ("-")
				ret += variables
				
				ret += self.factory.ui.debugHeaderEx ("-")
				ret += self.factory.ui.debugLine ("Action Groups", "-")
				ret += self.factory.ui.debugHeaderEx ("-")
				ret += actiongroups
				
				if len(watchingIds) > 0:				
					ret += self.factory.ui.debugHeaderEx ("-")
					ret += self.factory.ui.debugLine ("Watched Devices", "-")
					ret += self.factory.ui.debugHeaderEx ("-")
					
					for id in watchingIds:
						if id in indigo.devices:
							dev = indigo.devices[int(id)]
							
							ret += self.factory.ui.debugHeaderEx ("-")
							ret += self.factory.ui.debugLine ("'{0}' ({1})".format(dev.name, str(dev.id)), "-")
							ret += self.factory.ui.debugHeaderEx ("-")
							
							ret += self.factory.ui.debugHeaderEx ("!")
							ret += self.factory.ui.debugLine ("States", "!")
							ret += self.factory.ui.debugHeaderEx ("!")
				
							for state, value in dev.states.iteritems():
								ret += self.factory.ui.debugLine (state + " = " + unicode(value), "!")
								
							ret += self.factory.ui.debugHeaderEx ("!")
							ret += self.factory.ui.debugLine ("Attributes", "!")
							ret += self.factory.ui.debugHeaderEx ("!")
				
							for prop in [a for a in dir(dev) if not a.startswith('__') and not callable(getattr(dev,a))]:
								if prop != "states" and prop != "ownerProps" and prop != "pluginProps" and prop != "globalProps":
									value = getattr(dev, prop)
									ret += self.factory.ui.debugLine (prop + " = " + unicode(value), "!")
				
				
				
				
				ret += self.factory.ui.debugHeaderEx ("=")
				
				
				
			
				return ret
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return ""




























































			