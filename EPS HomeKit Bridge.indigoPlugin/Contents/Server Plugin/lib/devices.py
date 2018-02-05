# lib.devices - Extensions for Indigo devices
#
# Copyright (c) 2018 ColoradoFourWheeler / EPS
#

import indigo
import logging


import ext
import dtutil
import datetime
from datetime import date, timedelta

#
# Irrigation Controllers
#
class devices:

	#
	# Initialize the  class
	#
	def __init__(self, factory):
		self.logger = logging.getLogger ("Plugin.devices")
		self.factory = factory
		
		self.items = {}
		
	#
	# Add a device
	#
	def add (self, obj):
		try:
			isNew = True
			for devId, dev in self.items.iteritems():
				if devId == obj.id:
					isNew = False
					break
		
			if isNew:
				if type(obj) is indigo.SprinklerDevice:
					self.items[obj.id] = self.SprinklerDeviceEx (self, obj)
				else:
					return None
				
				#indigo.server.log(unicode(self.items[obj.id]))
				
			return self.items[obj.id]	
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
	#
	# Process a device change
	#
	def deviceUpdated (self, origDev, newDev, change):
		try:
			if newDev.id in self.items:
				if "deviceUpdated" in dir(self.items[newDev.id]):
					self.items[newDev.id].deviceUpdated (origDev, newDev, change)
						
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
	#
	# Recurring thread actions
	#
	def runConcurrentThread(self):
		try:
			for devId, dev in self.items.iteritems():
				if "runConcurrentThread" in dir(dev):
					dev.runConcurrentThread ()
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			

	#
	# Device extension class
	#
	class SprinklerDeviceEx:
	
		#
		# Initialize the  class
		#
		def __init__ (self, parent, obj):
			try:			
				self.logger = logging.getLogger ("Plugin.SprinklerDeviceEx")
				self.dev = obj			
				self.parent = parent
				self._setProperties()
				self._refresh()
				
				self._checkInProgress()

				self.logger.threaddebug ("Sprinkler device '{0}' is being extended".format(self.dev.name))

			except Exception as e:
				self.logger.error (ext.getException(e))	
				
		#
		# Raise any needed events for in-progress devices (only happens on device startup)
		#
		def _checkInProgress (self):
			try:
				update = None
				
				if self.isPaused:
					# We are starting up mid-pause
					update = self.parent.factory.raiseEvent ("onSprinklerPauseInProgress", [self, self.SprinklerDeviceExUpdate()])
			
				if self.isRunning:
					# We are starting up mid-schedule
					update = self.parent.factory.raiseEvent ("onSprinklerScheduleInProgress", [self, self.SprinklerDeviceExUpdate()])
		
				self._processUpdateRecord (update)
		
			except Exception as e:
				self.logger.error (ext.getException(e))	
		
		#
		# Print output
		#		
		def __str__(self):
			ret = ""
			
			try:
				self._refresh()
				
				ret += self._addLine ("name", self.dev.name)
				
				ret += self._addLine ("activeZone", unicode(self.activeZone))
				ret += self._addLine ("pausedZone", unicode(self.pausedZone))
				
				ret += self._addLine ("schedule", "")
				ret += self._addLine ("scheduleStartTime", unicode(self.scheduleStartTime), 1)
				ret += self._addLine ("scheduleEndTime", unicode(self.scheduleEndTime), 1)
				ret += self._addLine ("scheduleRunTime", unicode(self.scheduleRunTime), 1)
				ret += self._addLine ("scheduleMinutesRemaining", unicode(self.scheduleMinutesRemaining), 1)
				ret += self._addLine ("scheduleMinutesComplete", unicode(self.scheduleMinutesComplete), 1)
				ret += self._addLine ("schedulePercentRemaining", unicode(self.schedulePercentRemaining), 1)
				ret += self._addLine ("schedulePercentCompleted", unicode(self.schedulePercentCompleted), 1)
				ret += self._addLine ("scheduleZonesComplete", unicode(self.scheduleZonesComplete), 1)
				ret += self._addLine ("scheduleZonesRemaining", unicode(self.scheduleZonesRemaining), 1)
				
				ret += self._addLine ("zone", "")				
				ret += self._addLine ("zoneStartTime", unicode(self.zoneStartTime), 1)
				ret += self._addLine ("zoneEndTime", unicode(self.zoneEndTime), 1)
				ret += self._addLine ("zoneRunTime", unicode(self.zoneRunTime), 1)
				ret += self._addLine ("zoneMinutesRemaining", unicode(self.zoneMinutesRemaining), 1)
				ret += self._addLine ("zoneMinutesComplete", unicode(self.zoneMinutesComplete), 1)
				ret += self._addLine ("zonePercentRemaining", unicode(self.zonePercentRemaining), 1)
				ret += self._addLine ("zonePercentCompleted", unicode(self.zonePercentCompleted), 1)
								
				ret += self._addLine ("isRunning", unicode(self.isRunning))
				ret += self._addLine ("isPaused", unicode(self.isPaused))
				
			except Exception as e:
				self.logger.error (ext.getException(e))	
				
			return ret

		#
		# Add a line and optional indent to the str output
		#
		def _addLine (self, title, value, indents = 0):
			try:
				indent = ""
	
				for i in range(0, indents):
					indent += "\t"
			
				for i in range(0, self.indent):
					indent += "\t"
	
				return indent + title + " : " + unicode(value) + "\n"
				
			except Exception as e:
				self.logger.error (ext.getException(e))	
				return ""

		#
		# Set extended properties
		#
		def _setProperties (self):
			try:
				self.indent = 0
				self.isRunning = False
				self.isPaused = False
				self.activeZone = 0
				self.pausedZone = 0
				
				self.scheduleStartTime = None
				self.scheduleEndTime = None
				self.scheduleRunTime = 0
				self.scheduleMinutesRemaining = 0
				self.scheduleMinutesComplete = 0
				self.schedulePercentCompleted = 0
				self.schedulePercentRemaining = 0
				self.scheduleZonesComplete = 0
				self.scheduleZonesRemaining = 0
				
				self.zoneStartTime = None
				self.zoneEndTime = None
				self.zoneRunTime = 0
				self.zoneMinutesRemaining = 0
				self.zoneMinutesComplete = 0
				self.zonePercentCompleted = 0
				self.zonePercentRemaining = 0
				
				self.pauseStartTime = None
				self.pauseEndTime = None
				self.isResuming = False
			
			except Exception as e:
				self.logger.error (ext.getException(e))	
				
		#
		# Return states and properties for this device that cache needs to watch for
		#
		def getWatchList (self):
			ret = {}
			ret["states"] = []
			ret["attribs"] = []
			
			try:
				ret["states"].append ("activeZone")
				ret["states"].append ("zone1")
				ret["states"].append ("zone2")
				ret["states"].append ("zone3")
				ret["states"].append ("zone4")
				ret["states"].append ("zone5")
				ret["states"].append ("zone6")
				ret["states"].append ("zone7")
				ret["states"].append ("zone8")
				
				ret["attribs"].append ("displayStateValRaw")
				ret["attribs"].append ("displayStateValUi")
				ret["attribs"].append ("enabled")
				ret["attribs"].append ("pausedScheduleRemainingZoneDuration")
				ret["attribs"].append ("pausedScheduleZone")
				ret["attribs"].append ("zoneCount")
				ret["attribs"].append ("zoneEnableList")
				ret["attribs"].append ("zoneMaxDurations")
				ret["attribs"].append ("zoneNames")
				ret["attribs"].append ("zoneScheduledDurations")
			
			except Exception as e:
				self.logger.error (ext.getException(e))	
				
			return ret
			
		#
		# Recurring thread actions
		#
		def runConcurrentThread(self):	
			try:
				if self.isRunning or self.isPaused:
					update = None
					
					self._refresh()
										
					# Do our calculations
					self.scheduleMinutesRemaining = round (dtutil.dateDiff ("minutes", self.scheduleEndTime, indigo.server.getTime()), 2)
					self.zoneMinutesRemaining = round (dtutil.dateDiff ("minutes", self.zoneEndTime, indigo.server.getTime()), 2)
					
					self.scheduleMinutesComplete = round (self.scheduleRunTime - self.scheduleMinutesRemaining, 2)
					self.zoneMinutesComplete = round (self.zoneRunTime - self.zoneMinutesRemaining, 2)
					
					self.schedulePercentRemaining = int(round(self.scheduleMinutesRemaining / self.scheduleRunTime, 2) * 100)
					if self.zoneRunTime > 0:
						self.zonePercentRemaining = int(round(self.zoneMinutesRemaining / self.zoneRunTime, 2) * 100)
					else:
						self.logger.info ("The zone run time is zero, unable to calculate time remaining.  This is not a critical problem and may only indicate that you stopped a sprinkler that wasn't running.")
					
					self.schedulePercentComplete = 100 - self.schedulePercentRemaining
					self.zonePercentComplete = 100 - self.zonePercentRemaining
					
					# Raise the event on the plugin
					update = self.parent.factory.raiseEvent ("onSprinklerProgressChanged", [self, self.SprinklerDeviceExUpdate()])
					update = self.parent.factory.raiseEvent ("onZoneProgressChanged", [self, self.SprinklerDeviceExUpdate()])
			
					self._processUpdateRecord (update)
			
			except Exception as e:
				self.logger.error (ext.getException(e))	

		#
		# Get the current status of the device
		#
		def _refresh (self):
			try:
				self.dev.refreshFromServer()
				dev = self.dev
				
				self._refreshRunningState (dev)
				
			except Exception as e:
				self.logger.error (ext.getException(e))	

		#
		# Get the current running state
		#
		def _refreshRunningState (self, dev):
			try:
				if dev.activeZone is None and dev.pausedScheduleZone is None:
					self.isPaused = False
					self.pausedZone = 0
					
					self.isRunning = False
					self.activeZone = 0
										
				elif dev.activeZone is not None:
					self.isPaused = False
					self.pausedZone = 0
					
					# Strange things can happen if we started up the plugin mid-schedule, we need to make sure we are ok
					if self.scheduleEndTime is None:
						self._updateFromSchedule()
					
					self.isRunning = True
					self.activeZone = dev.activeZone
					
				elif dev.pausedScheduleZone is not None:
					self.isPaused = True
					self.pausedZone = dev.pausedScheduleZone
					
					if self.scheduleEndTime is None:
						self._updateFromSchedule()
					
					self.isRunning = False
					self.activeZone = 0
					
			except Exception as e:
				self.logger.error (ext.getException(e))	


		#
		# Process a device change
		#
		def deviceUpdated (self, origDev, newDev, change):
			try:
				self._refresh()
				parent = indigo.devices[change.parentId]
				update = None
				
				if change.name == "pausedScheduleZone" and change.oldValue is None and change.newValue is not None:
					self.logger.threaddebug ("'{0}' has been paused".format(self.dev.name))
					update = self.parent.factory.raiseEvent ("onSprinklerSchedulePaused", [self, change, self.SprinklerDeviceExUpdate()])
					
					self.pauseStartTime = indigo.server.getTime()
					self.isRunning = False
					self.isPaused = True
					
				elif change.name == "pausedScheduleZone" and change.oldValue is not None and change.newValue is None:				
					self.logger.threaddebug ("'{0}' has resumed a schedule".format(self.dev.name))	
					update = self.parent.factory.raiseEvent ("onSprinklerScheduleResumed", [self, change, self.SprinklerDeviceExUpdate()])		
					
					self.pauseEndTime = indigo.server.getTime()
					
					# Adjust the run times based on how long we have been paused
					pauseMinutes = dtutil.dateDiff ("minutes", indigo.server.getTime(), self.pauseStartTime)
					self.scheduleEndTime = dtutil.dateAdd ("minutes", pauseMinutes, self.scheduleEndTime)
					self.zoneEndTime = dtutil.dateAdd ("minutes", pauseMinutes, self.zoneEndTime)
					self.runConcurrentThread() # to force UI updates if needed
					
					self.isRunning = True
					self.isPaused = False
					self.isResuming = True # So we don't start again
					
				elif change.name == "activeZone" and change.oldValue == 0 and change.newValue != 0 and self.isPaused == False:
					if self.isResuming:
						# We don't handle resumes since we can get a lot of them for one plugin, the plugin needs to make
						# that determination for us when we notify them
						self.logger.threaddebug ("'{0}' is trying to start a new schedule but the extension is paused".format(self.dev.name))	
						update = self.parent.factory.raiseEvent ("onSprinklerReleasePauseState", [self, change])
						if update is not None: self.isResuming = update
						
					else:					
						# A fresh schedule has begun
						self.logger.threaddebug ("'{0}' has started a new schedule".format(self.dev.name))
						update = self.parent.factory.raiseEvent ("onSprinklerScheduleStarted", [self, change, self.SprinklerDeviceExUpdate()])
						self._updateFromSchedule()
						self.isRunning = True
					
				elif change.name == "activeZone" and change.oldValue != 0 and change.newValue == 0 and self.isPaused == False:
					# Sprinklers have been stopped
					self.logger.threaddebug ("'{0}' has been stopped".format(self.dev.name))
					update = self.parent.factory.raiseEvent ("onSprinklerScheduleStopped", [self, change, self.SprinklerDeviceExUpdate()])
					self.isRunning = False
				
				self._processUpdateRecord (update)
					
				#indigo.server.log(unicode(self))
				#indigo.server.log(unicode(change))
				
			except Exception as e:
				self.logger.error (ext.getException(e))	


		#
		# Process a raised event update return
		#
		def _processUpdateRecord (self, update):
			try:
				if update is None: return
			
			except Exception as e:
				self.logger.error (ext.getException(e))	


		#
		# Set schedule and zone times
		#
		def _updateFromSchedule (self):
			try:
				scheduledTimes = []
				
				if len(self.dev.zoneScheduledDurations) > 0:
					scheduledTimes = self.dev.zoneScheduledDurations
					
				else:
					scheduledTimes = self.dev.zoneMaxDurations
					
				totalTime = 0
				zoneTime = 0
				zoneIdx = 1 # 1 based since activeZone is 1 based
				for i in scheduledTimes:
					if zoneIdx < self.dev.activeZone: 
						zoneIdx = zoneIdx + 1
						continue
						
					totalTime = totalTime + i
					if zoneIdx == self.dev.activeZone: zoneTime = i
						
					zoneIdx = zoneIdx + 1
					
				self.scheduleStartTime = indigo.server.getTime()
				self.zoneStartTime = indigo.server.getTime()
				
				self.scheduleRunTime = totalTime
				self.zoneRunTime = zoneTime
				
				self.scheduleEndTime = dtutil.dateAdd ("minutes", totalTime, self.scheduleStartTime)
				self.zoneEndTime = dtutil.dateAdd ("minutes", zoneTime, self.zoneStartTime)
			
			except Exception as e:
				self.logger.error (ext.getException(e))	


		#
		# Sub-class for the plugin to respond to an event
		#
		class SprinklerDeviceExUpdate:
			
			#
			# Initialize the  class
			#
			def __init__ (self):
				try:
					self.isRunning = None
					self.isPaused = None
					self.activeZone = None
					self.pausedZone = None
				
					self.scheduleStartTime = None
					self.scheduleEndTime = None
					self.scheduleRunTime = None
					self.scheduleMinutesRemaining = None
					self.scheduleMinutesComplete = None
					self.schedulePercentCompleted = None
					self.schedulePercentRemaining = None
					self.scheduleZonesComplete = None
					self.scheduleZonesRemaining = None
				
					self.zoneStartTime = None
					self.zoneEndTime = None
					self.zoneRunTime = None
					self.zoneMinutesRemaining = None
					self.zoneMinutesComplete = None
					self.zonePercentCompleted = None
					self.zonePercentRemaining = None

				except Exception as e:
					self.logger.error (ext.getException(e))	























