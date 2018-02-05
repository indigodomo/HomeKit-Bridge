# eps.update - Check for updates to the plugin and/or libraries
#
# Copyright (c) 2018 ColoradoFourWheeler / EPS
#

import indigo
import logging

import datetime
from datetime import date, timedelta
import re
import urllib2

import ext
import dtutil

class update:
	AUTOCHECK_FREQUENCY = 72 # Hours between checks if last check reports this version is current
	AUTOCHECK_NAG 		= 2 # Hours between nags if last check reports this version is not current
	
	#
	# Initialize the  class
	#
	def __init__(self, factory):
		try:
			self.factory = factory
		
			self.logger = logging.getLogger ("Plugin.update")
				
			if factory.plugin.UPDATE_URL is None or factory.plugin.UPDATE_URL == "":
				factory.plugin.pluginPrefs["latestVersion"] = False
				factory.plugin.pluginPrefs["lastUpdateCheck"] = "2016-01-01 23:59:59"
				factory.logger.threaddebug ("Update URL not passed, aborting initialization")
				return
		
			self._validatePrefs()
			self.check(True, True) # Always check on startup
		
			self.logger.threaddebug ("Update initialized")
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
		
	#
	# Check and report on version
	#
	def check (self, force = False, reportCurrent = True):
		try:
			if self.factory.plugin.UPDATE_URL is None or self.factory.plugin.UPDATE_URL == "": return
			
			version = self._check (force)
			if version:
				self.logger.error ("Version %s is available, you are running version %s" % (version, self.factory.plugin.pluginVersion))
				self.factory.plugin.pluginPrefs["latestVersion"] = False
				
			else:
				if reportCurrent: self.logger.info ("You are running the most current version of {0}".format(self.factory.plugin.pluginDisplayName))
					
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
		
	#
	# Check source and get the latest version number
	#	
	def _check (self, force = False):
		try:
			if self.factory.plugin.UPDATE_URL == "" or self.factory.plugin.UPDATE_URL is None: return False
			if force == False and self._autoCheckOk() == False: return False
			
			self.logger.threaddebug("Checking site for current version")
			
			sock = urllib2.urlopen(self.factory.plugin.UPDATE_URL)
			page = sock.read()
			sock.close()
			result = re.findall("\#Version\|.*?\#", page)
			if len(result) == 0: return False
			
			versioninfo = result[0].replace("#", "").split("|")
			self.factory.plugin.pluginPrefs["lastUpdateCheck"] = indigo.server.getTime().strftime("%Y-%m-%d %H:%M:%S")
			if self._upToDate (versioninfo[1]) == False: return versioninfo[1]
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return False
		
		return False
		
	#
	# See if it's ok to automatically check
	#
	def _autoCheckOk (self):
		d = indigo.server.getTime()
		
		try:
			last = datetime.datetime.strptime (self.factory.plugin.pluginPrefs["lastUpdateCheck"], "%Y-%m-%d %H:%M:%S")
			lastCheck = dtutil.dateDiff ("hours", d, last)
			
			if self.factory.plugin.pluginPrefs["latestVersion"]:
				if lastCheck < self.AUTOCHECK_FREQUENCY: return False # if last check has us at the latest then only check every 3 days
			else:
				if lastCheck < self.AUTOCHECK_NAG: return False # only check every four hours in case they don't see it in the log
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return False
			
		return True
			
	#
	# Validate that we have the proper prefs for update checking
	#
	def _validatePrefs (self):
		try:
			if ext.valueValid (self.factory.plugin.pluginPrefs, "latestVersion", True) == False: self.factory.plugin.pluginPrefs["latestVersion"] = False
			if ext.valueValid (self.factory.plugin.pluginPrefs, "lastUpdateCheck", True) == False:
				d = indigo.server.getTime()	
				d = dtutil.dateAdd ("days", -30, d) # Forces us to check next time
				self.factory.plugin.pluginPrefs["lastUpdateCheck"] = d.strftime("%Y-%m-%d %H:%M:%S")
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		
	#
	# Check if latest version is newer than current version
	#
	def _upToDate (self, latest):
		try:
			self.logger.threaddebug ("Latest version is %s" % latest)
			self.logger.threaddebug ("Current version is %s" % self.factory.plugin.pluginVersion)
		
			latest = latest.split(".")
			current = str(self.factory.plugin.pluginVersion).split(".")
		
			if int(latest[0]) > int(current[0]): return False
		
			self.logger.threaddebug (self.factory.plugin.pluginDisplayName + " is up-to-date")
			return True
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return True
		
		
	