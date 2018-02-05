# lib.cache - Caches devices and items from Indigo for lookup
#
# Copyright (c) 2018 ColoradoFourWheeler / EPS
#

import indigo
import logging

import ext

# CONSTANTS
DEV_FIELDS = ["device", "device1", "device2", "device3", "device4", "device5"]
VAR_FIELDS = ["variable", "variable1", "variable2", "variable3", "variable4", "variable5"]


#
# Main cache class
#
class cache:

	#
	# Initialize the  class
	#
	def __init__(self, factory):
		self.logger = logging.getLogger ("Plugin.cache")
		self.factory = factory
		self.items = cacheDict(factory)
		self.pluginItems = indigo.Dict() # Plugin devices by type
		self.pluginDevices = indigo.List() # All plugin devices
		self.pluginLocalCache = indigo.List() # If the plugin needs to cache something special
		
		self.logger.threaddebug ("Caching initialized")
		
	#
	# Initialize local properties
	#	
	def _initProps (self):
		return
			
	#
	# Add device to cache
	#
	def addDevice (self, dev):
		try:
			if self.items.isInCache (dev.id):
				self.logger.debug ("Not adding {0} to cache because it's already there".format(dev.name))
				return
			else:
				self.logger.debug ("Adding {0} to cache".format(dev.name))
		
			cDev = cacheDev(dev)
			self.items.add(cDev)
			
			if cDev.pluginId == self.factory.plugin.pluginId: 
				self._autoCacheFields (dev)
				
				if cDev.id in self.pluginDevices:
					pass
				else:
					self.pluginDevices.append(cDev.id) 
				
				pluginItem = indigo.Dict()
				if cDev.deviceTypeId in self.pluginItems:
					pluginItem = self.pluginItems[cDev.deviceTypeId]
				
				else:
					pluginItem = indigo.List()

				if cDev.id in pluginItem:
					pass
				else:
					pluginItem.append(cDev.id)
					
				self.pluginItems[cDev.deviceTypeId] = pluginItem	
				
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
	#
	# Remove device from cache
	#
	def removeDevice (self, obj):
		try:
			self.logger.threaddebug ("Removing '{0}' and any references from cache".format(obj.name))
			self.items.remove(obj)
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
	
	#
	# Automatically subscribe to changes
	#
	def subscribeToChanges (self, obj):
		try:
			if type(obj) is indigo.Variable and self.factory.plug.isSubscribedVariables == False:
				self.logger.threaddebug ("Variable is being watched, automatically subscribing to variable changes")
				indigo.variables.subscribeToChanges()
				self.factory.plug.isSubscribedVariables = True
				
			if type(obj) is indigo.ActionGroup and self.factory.plug.isSubscribedActionGroups == False:
				self.logger.threaddebug ("Action group is being watched, automatically subscribing to action group changes")
				indigo.actionGroups.subscribeToChanges()
				self.factory.plug.isSubscribedActionGroups = True
				
			else:
				if self.factory.plug.isSubscribedDevices == False:
					self.logger.threaddebug ("Device is being watched, automatically subscribing to device changes")
					indigo.devices.subscribeToChanges()
					self.factory.plug.isSubscribedDevices = True		
		
		except Exception as e:
			self.logger.error (ext.getException(e))		
			
	#
	# Resolve an address to a cached device
	#
	def addressToDev (self, address):
		try:
			obj = self.items.addressIsInCache (address)
			
			if obj:
				self.logger.threaddebug("Address '{0}' is cached, returning '{1}'".format(address, obj.name))
				return indigo.devices[obj.id]
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
	#
	# Get devices that are watching an ID
	#
	def getDevicesWatchingId (self, id):
		ret = []
		
		try:
			obj = self.items.isInCache (int(id))
			
			if obj:
				for watchItem in obj.watchedBy:
					ret.append(watchItem.id)
		
		except Exception as e:
			self.logger.error (ext.getException(e))		
			
		return ret
		
	#
	# Add watched states
	#
	def addWatchedStates (self, parent, watchedItemsDict):
		try:
			# If we are watching something then automatically turn on subscribeToChanges
			self.subscribeToChanges(parent)
			
			for devId, state in watchedItemsDict.iteritems():
				if int(devId) not in indigo.devices:
					self.logger.error ("Device '{0}' is referencing device ID {1} but that device is no longer an Indigo device.  Please change the device reference or remove '{0}' to prevent this error".format(parent.name, str(devId)))
					continue
						
				states = []
				
				# They can pass a single state or a list of states, we'll convert if needed
				if type(state) is list: 
					states = state
				else:
					states.append(state)
			
				for state in states:
					if ext.valueValid (indigo.devices[devId].states, state):
						self.logger.threaddebug ("Adding watched state '{0}' to child device '{1}' being watched by '{2}'".format(state, indigo.devices[devId].name, parent.name))
						self.items.addWatchedState (parent, indigo.devices[devId], state)
					else:
						# See if it's a custom state
						if state[0:7] == "custom_":
							self.logger.threaddebug ("Adding custom watched state '{0}' to child device '{1}' being watched by '{2}'".format(state, indigo.devices[devId].name, parent.name))
							self.items.addWatchedState (parent, indigo.devices[devId], state)
						else:
							self.logger.warning ("Cannot watch state '{0}' on child device '{1}' for '{2}' because the child doesn't have that state".format(state, indigo.devices[devId].name, parent.name))

			#self.logger.info(unicode(self.items))
				
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
	#
	# Add watched attributes
	#
	def addWatchedAttribute (self, parent, watchedItemsDict):
		try:			
			for devId, attribute in watchedItemsDict.iteritems():
				# If we are watching something then automatically turn on subscribeToChanges
				self.subscribeToChanges(indigo.devices[devId])
				
				attributes = []
				
				# They can pass a single state or a list of states, we'll convert if needed
				if type(attribute) is list: 
					attributes = attribute
				else:
					attributes.append(attribute)
			
				for attribute in attributes:
					# Assuming we use our own factory to generate the list, get rid of "attr_"
					attribute = attribute.replace("attr_", "")
					
					# This should only come from our own core, therefore attributes should be pre-pended with "attr_", fix that
					attribute = attribute.replace("attr_", "")
					self.logger.threaddebug ("Adding watched attribute '{0}' to child device '{1}' being watched by '{2}'".format(attribute, indigo.devices[devId].name, parent.name))
					self.items.addWatchedAttribute (parent, indigo.devices[devId], attribute)
					
			#self.logger.info(unicode(self.items))
				
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
	#
	# Add watched property
	#
	def addWatchedProperty (self, parent, watchedItemsDict):
		try:
			for devId, property in watchedItemsDict.iteritems():
				# If we are watching something then automatically turn on subscribeToChanges
				self.subscribeToChanges(indigo.devices[devId])
				
				properties = []
				
				# They can pass a single state or a list of states, we'll convert if needed
				if type(property) is list: 
					properties = property
				else:
					properties.append(property)
			
				for property in properties:
					if ext.valueValid (indigo.devices[devId].ownerProps, property):
						self.logger.threaddebug ("Adding watched property '{0}' to child device '{1}' being watched by '{2}'".format(property, indigo.devices[devId].name, parent.name))
						self.items.addWatchedProperty (parent, indigo.devices[devId], property)
					else:
						# If using our own engine then if there are no properties to watch it should be "-none-"
						if property != "-none-" and property != "":
							self.logger.warning ("Cannot watch property '{0}' on child device '{1}' for '{2}' because the child doesn't have that property ID".format(property, indigo.devices[devId].name, parent.name))

			#self.logger.info(unicode(self.items))
				
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
		

			
	#
	# Add watched variable - this is different in that we only ever look at one thing, the value of the variable
	#
	def addWatchedVariable (self, parent, watchedItemsDict):
		try:
			for varId, variable in watchedItemsDict.iteritems():
				if int(varId) in indigo.variables:
					# If we are watching something then automatically turn on subscribeToChanges
					self.subscribeToChanges(indigo.variables[varId])
					self.items.addWatchedItem (parent, indigo.variables[varId])
				else:
					self.logger.warning ("Cannot watch variable '{0}' on child device '{1}' because the variable doesn't exist".format(str(varId), parent.name))			
			
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
	#
	# Add watched action group - we don't look for anything that changed, it's here so we can notify the plugin that one we are watching was run
	#
	def addWatchedActionGroup (self, parent, watchedItemsDict):
		try:
			for agId, variable in watchedItemsDict.iteritems():
				if int(agId) in indigo.actionGroups:
					# If we are watching something then automatically turn on subscribeToChanges
					self.subscribeToChanges(indigo.actionGroups[agId])
					self.items.addWatchedItem (parent, indigo.actionGroups[agId])
				else:
					self.logger.warning ("Cannot watch action group '{0}' on child device '{1}' because the action group doesn't exist".format(str(agId), parent.name))			
			
		
		except Exception as e:
			self.logger.error (ext.getException(e))		
			
	#
	# Add watched object without any attribute, states, props or values being watched - called when no other property is appropriate but we still want to monitor the object
	#
	def addWatchedObject (self, parent, watchedItemsDict):
		try:
			for objId, objNothing in watchedItemsDict.iteritems():
				if int(objId) in indigo.devices:
					obj = indigo.devices[objId]
				elif int(objId) in indigo.variables:
					obj = indigo.variables[objId]
				else:
					self.logger.warn ("Trying to watch object id {0} on '{1}' but that id could not be resolved in Indigo, skipping cache".format(str(objId), parent.name))
				
				self._watchObject (parent, obj)
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
	#
	# After an update event, see if anything interesting changed
	#
	def watchedItemChanges (self, origObj, newObj):
		ret = []
		
		#indigo.server.log(origObj.name)
		#return ret
		# This routine takes .2 to .4 extra CPU, without it it's 1.2 instead of 1.6 to 1.8
		
		try:
			obj = self.items.isInCache (newObj.id)
			
			if obj:
				self.logger.threaddebug("'{0}' is cached, checking for changes".format(newObj.name))
				#self.watchedItemChanged_ShowAllChanges (origObj, newObj)
				ret = obj.getWatchedByChanges (origObj, newObj)
								
			else:
				return ret
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return ret
		
	#
	# Compare two devices and log the changes between them
	#
	def watchedItemChanged_ShowAllChanges (self, origObj, newObj):
		try:
			for s in newObj.states:
				if s in origObj.states:
					if newObj.states[s] != origObj.states[s]:
						self.logger.debug ("State {0} was {1} and is now {2}".format(s, unicode(origObj.states[s]), unicode(newObj.states[s])))
						
			for s in newObj.pluginProps:
				if s in origObj.pluginProps:
					if newObj.pluginProps[s] != origObj.pluginProps[s]:
						self.logger.debug ("Property {0} was {1} and is now {2}".format(s, unicode(origObj.pluginProps[s]), unicode(newObj.pluginProps[s])))
		
		except Exception as e:
			self.logger.error (ext.getException(e))	

			
	#
	# Watch an item (does not watch any states, props, attributes or values, just the device)
	#
	def _watchObject (self, dev, obj):
		try:
			self.subscribeToChanges (obj)
			self.items.addWatchedItem (dev, obj)
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
		
			
	#
	# Check for standard watch fields in a plugin device
	#
	def _autoCacheFields (self, dev):
		try:
			for fieldName, fieldValue in dev.pluginProps.iteritems():
				if fieldName in DEV_FIELDS and fieldValue != "":
					if int(fieldValue) not in indigo.devices:
						self.logger.error ("Device '{0}' is referencing device ID {1} but that device is no longer an Indigo device.  Please change the device reference or remove '{0}' to prevent this error".format(dev.name, str(fieldValue)))
						return False
				
					d = indigo.devices[int(fieldValue)]
					self.logger.debug ("Found device reference field '{1}' in plugin device '{0}', auto-watching '{2}' for changes".format(dev.name, fieldName, d.name))
					self._watchObject (dev, d)
					
				if fieldName in VAR_FIELDS and fieldValue != "":
					v = indigo.variables[int(fieldValue)]
					self.logger.debug ("Found variable reference field '{1}' in plugin device '{0}', auto-watching '{2}' for changes".format(dev.name, fieldName, v.name))
					self._watchObject (dev, v)
		
		except Exception as e:
			self.logger.error (ext.getException(e))	

#
# Cache item list
#
class cacheDict:
	#
	# Initialize the  class
	#
	def __init__(self, factory):
		self.logger = logging.getLogger ("Plugin.cacheDict")
		self.items = {}
		self.factory = factory
		
	def __len__ (self):
		try:
			return len(self.items)
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
	def __iter__ (self):
		self.iter_index = 0
		return self
		
	def next (self):
		try:
			if self.iter_index < len(self.items):
				idx = 0
				rec = None
				
				for devId, props in self.items.iteritems():
					if idx == self.iter_index:
						rec = props
						
					idx = idx + 1
					
				self.iter_index = self.iter_index + 1
			
				return rec
			else:
				raise StopIteration
				
		except Exception as e:
			#self.logger.error (ext.getException(e))		
			raise StopIteration
		
		
		
	def __str__(self):
		ret = "Cache List\n"
		for devId, props in self.items.iteritems():
			ret += "\n" + props.itemType + "\n"
			proplist = [a for a in dir(props) if not a.startswith('__') and not callable(getattr(props,a))]
			for p in proplist:
				value = getattr(props, p)
				
				if type(value) is list:
					ret += "\t" + p + " : " 
					if len(value) > 0:
						ret += " (list) :\n"
						for l in value:
							if isinstance(l, watchRec):
								ret += "\t\titem : " + str(l.id) + "\n"
								
								# If we have states then add them
								if len(l.states) > 0:
									ret += "\t\t\tstates : \n"
								
									for st in l.states:
										ret += "\t\t\t\t" + st + "\n"
										
								# If we have attributes then add them
								if len(l.attributes) > 0:
									ret += "\t\t\tattributes : \n"
								
									for st in l.attributes:
										ret += "\t\t\t\t" + st + "\n"
										
								# If we have plugin config properties then add them
								if len(l.attributes) > 0:
									ret += "\t\t\tproperties : \n"
								
									for st in l.properties:
										ret += "\t\t\t\t" + st + "\n"	
										
							else:
								ret += "\t\titem : " + unicode(l) + "\n"
					else:
						ret += "\n"
					
				elif type(value) is dict:
					ret += "\t" + p + " : (dict) : \n\t" + unicode(value) + "\n"
					
				else:
					ret += "\t" + p + " : " + unicode(value) + "\n"
			
		return ret
		
	#
	# If an item is in cache return the item
	#
	def isInCache (self, id):
		if int(id) in self.items: return self.items[id]
		
		return False
		
	#
	# If an address is in cache return the item
	#
	def addressIsInCache (self, address):
		for id, objinfo in self.items.iteritems():
			if objinfo.itemType == "Device" and unicode(objinfo.address) == unicode(address): return self.items[id]
			
		return False
	
	#
	# Add device to the list
	#	
	def add (self, obj):
		self.items[obj.id] = obj
		
	#
	# Remove device from list
	#
	def remove (self, obj):
		removeItems = []

		try:		
			for id, objinfo in self.items.iteritems():
				if id == obj.id:
					removeItems.append(obj.id) # This parent device will be removed
				
					# Go through all items that we are watching
					for winfo in objinfo.watching:
						newChildWatchedBy = []
						
						child = self.items[winfo.id] # This record should be there if we are watching something
						#indigo.server.log(unicode(child.id) + " - " + child.name)

						for cinfo in child.watchedBy:
							if cinfo.id != obj.id: newChildWatchedBy.append(cinfo)
							
						child.watchedBy = newChildWatchedBy
						
						if len(child.watching) == 0 and len(child.watchedBy) == 0: 
							removeItems.append(child.id) # Remove child if watched by if it's not watching or being watched
							
			for id in removeItems:
				self.logger.threaddebug ("Cache item '{0}' is no longer referenced by anything, removing from cache".format(self.items[id].name))
				del self.items[id]
										
						
		except Exception as e:
			self.logger.error (ext.getException(e))	
					
				
		
	#
	# Add watched states for parent and child
	#
	def addWatchedState (self, parent, child, state):
		parentFound = False
		childFound = False
		
		for id, props in self.items.iteritems():
			if str(id) == str(parent.id): parentFound = True
			if str(id) == str(child.id): childFound = True
			
		if parentFound == False or childFound == False:
			self.addWatchedItem (parent, child)
			
		parentWatch = self.items[parent.id]
		
		# It's possible the record is here but the watched/watching is empty, account for that here
		if len(parentWatch.watching) == 0:
			self.addWatchedItem (parent, child)
			
		for w in parentWatch.watching:
			if w.id == child.id:
				if state in w.states: 
					continue
				else:
					w.states.append(state)
		
		childWatch = self.items[child.id]
		for w in childWatch.watchedBy:
			if w.id == parent.id:
				if state in w.states: 
					continue
				else:
					w.states.append(state)
					
	#
	# Add watched attributes for parent and child
	#
	def addWatchedAttribute (self, parent, child, attribute):
		parentFound = False
		childFound = False
		
		for id, props in self.items.iteritems():
			if str(id) == str(parent.id): parentFound = True
			if str(id) == str(child.id): childFound = True
			
		if parentFound == False or childFound == False:
			self.addWatchedItem (parent, child)
			
		parentWatch = self.items[parent.id]
		for w in parentWatch.watching:
			if w.id == child.id:
				if attribute in w.attributes: 
					continue
				else:
					w.attributes.append(attribute)
		
		childWatch = self.items[child.id]
		for w in childWatch.watchedBy:
			if w.id == parent.id:
				if attribute in w.attributes: 
					continue
				else:
					w.attributes.append(attribute)
					
					
	#
	# Add watched properties for parent and child
	#
	def addWatchedProperty (self, parent, child, property):
		parentFound = False
		childFound = False
		
		for id, props in self.items.iteritems():
			if str(id) == str(parent.id): parentFound = True
			if str(id) == str(child.id): childFound = True
			
		if parentFound == False or childFound == False:
			self.addWatchedItem (parent, child)
			
		parentWatch = self.items[parent.id]
		for w in parentWatch.watching:
			if w.id == child.id:
				if property in w.properties: 
					continue
				else:
					w.properties.append(property)
		
		childWatch = self.items[child.id]
		for w in childWatch.watchedBy:
			if w.id == parent.id:
				if property in w.properties: 
					continue
				else:
					w.properties.append(property)
				
		
	#
	# Add watched item to watch list
	#
	def addWatchedItem (self, parent, child, iswatching = True):
		isFound = False
		for id, props in self.items.iteritems():
			if str(id) == str(parent.id): isFound = True
		
		if isFound == False:
			if type(parent) is indigo.Variable:
				self.logger.debug("Automatically adding watched variable '{0}' to cache as a watched item".format(parent.name))
				newitem = cacheVar(parent)
		
			elif type(parent) is indigo.ActionGroup:
				self.logger.debug("Automatically adding watched action group '{0}' to cache as a watched item".format(parent.name))
				newitem = cacheAg(parent)
				
			else:
				self.logger.debug("Automatically adding watched device '{0}' to cache as a watched item".format(parent.name))
				newitem = cacheDev(parent)

			self.add(newitem)
		
		if iswatching: 
			isFound = False
			for rec in self.items[parent.id].watching:
				if rec.id == child.id: isFound = True
			
			if isFound == False:
				self.items[parent.id].watching.append(watchRec(child))			
				self.addWatchedItem (child, parent, False)
		else:
			isFound = False
			for rec in self.items[parent.id].watching:
				if rec.id == child.id: isFound = True
				
			if isFound == False: self.items[parent.id].watchedBy.append(watchRec(child))
			
		if "devices" in dir(self.factory):
			devEx = self.factory.devices.add (child)
			
			if devEx:
				watchers = devEx.getWatchList()
				for state in watchers["states"]:
					self.addWatchedState (parent, child, state)
					
				for attrib in watchers["attribs"]:
					self.addWatchedAttribute (parent, child, attrib)
		
#
# Cache watch record
#
class watchRec:
	#
	# Initialize the  class
	#
	def __init__(self, obj):
		self.id = obj.id
		self.states = []
		self.attributes = []	
		self.properties = []
		self.indent = 1
		
		self.logger = logging.getLogger ("Plugin.watchRec")
		
	def __str__(self):
		ret = ""
		
		ret += self._addLine ("Watch Record", "(watchRec)")
		ret += self._addLine ("id", self.id, 1)
		
		if len(self.states) == 0:
			ret += self._addLine ("states", "", 1)
		else:
			ret += self._addLine ("states", "(dict)", 1)
			for state in self.states:
				ret += self._addLine ("state", state, 2)
				
		if len(self.attributes) == 0:
			ret += self._addLine ("attributes", "", 1)
		else:
			ret += self._addLine ("attributes", "(dict)", 1)
			for attrib in self.attributes:
				ret += self._addLine ("attribute", attrib, 2)
				
		if len(self.properties) == 0:
			ret += self._addLine ("properties", "", 1)
		else:
			ret += self._addLine ("properties", "(dict)", 1)
			for prop in self.properties:
				ret += self._addLine ("properties", prop, 2)
				
		return ret
		
	def _addLine (self, title, value, indents = 0):
		indent = ""
	
		for i in range(0, indents):
			indent += "\t"
			
		for i in range(0, self.indent):
			indent += "\t"
	
		return indent + title + " : " + unicode(value) + "\n"
	
	
#
# Device record
#		
class cacheDev:

	#
	# Initialize the  class
	#
	def __init__(self, dev):
		self.itemType = "Device"
		self.name = dev.name
		self.id = dev.id
		self.address = dev.address
		self.deviceTypeId = dev.deviceTypeId
		self.pluginId = dev.pluginId
		self.watchedBy = []
		self.watching = []
		self.indent = 0
		
		self.logger = logging.getLogger ("Plugin.cacheDev")
		
	def __str__(self):
		ret = ""
		
		try:
			ret += self._addLine ("name", self.name)
			ret += self._addLine ("type", self.itemType)
			ret += self._addLine ("id", self.id)
			ret += self._addLine ("address", self.address)
			ret += self._addLine ("deviceTypeId", self.deviceTypeId)
			ret += self._addLine ("pluginId", self.pluginId)
			
			if len(self.watchedBy) == 0:
				ret += self._addLine ("watchedBy", "")
			else:
				ret += self._addLine ("watchedBy", "(dict)")
				for watchinfo in self.watchedBy:
					ret += unicode(watchinfo)
					
			if len(self.watching) == 0:
				ret += self._addLine ("watching", "")
			else:
				ret += self._addLine ("watching", "(dict)")
				for watchinfo in self.watching:
					ret += unicode(watchinfo)
				
		except:
			raise
		
		return ret
		
	def _addLine (self, title, value, indents = 0):
		indent = ""
	
		for i in range(0, indents):
			indent += "\t"
			
		for i in range(0, self.indent):
			indent += "\t"
	
		return indent + title + " : " + unicode(value) + "\n"
		
		
	def getWatchedByChanges (self, origDev, newDev):
		ret = []
		
		try:
			for watchinfo in self.watchedBy:
				for state in watchinfo.states:
					if state[0:7] == "custom_":
						# Sprinkler zone on/off displayed as zone names to end user, check if the zone on/off changed
						for i in range(1, 9):
							if state == "custom_zone" + str(i) + "Name": state = "zone" + str(i)
							
						# Sprinkler active zone number displayed as zone name, check if activeZone changed
						if state == "custom_activeZoneName": state = "activeZone"				
				
					#self.logger.threaddebug ("Checking for '{0}' state '{1}' changes".format(newDev.name, state))
					if state in origDev.states and state in newDev.states:
						if origDev.states[state] != newDev.states[state]:
							self.logger.threaddebug ("'{0}' state '{1}' has changed, adding change record for '{2}'".format(newDev.name, state, indigo.devices[watchinfo.id].name))
							ret.append (cacheChange(self, "state", state, watchinfo.id, newDev.id, origDev.states[state], newDev.states[state]))
													
							
				for attribute in watchinfo.attributes:
					#self.logger.threaddebug ("Checking for '{0}' attribute '{1}' changes".format(newDev.name, attribute))
					origFunc = getattr (origDev, attribute)
					newFunc = getattr (newDev, attribute)
					
					if origFunc != newFunc: 
						self.logger.threaddebug ("'{0}' attribute '{1}' has changed, adding change record for '{2}'".format(newDev.name, attribute, indigo.devices[watchinfo.id].name))
						ret.append (cacheChange(self, "attribute", attribute, watchinfo.id, newDev.id, origFunc, newFunc))
						
				for property in watchinfo.properties:
					#self.logger.threaddebug ("Checking for '{0}' property '{1}' changes".format(newDev.name, property))
					if property in origDev.ownerProps and property in newDev.ownerProps:
						if origDev.ownerProps[property] != newDev.ownerProps[property]:
							self.logger.threaddebug ("'{0}' property '{1}' has changed, adding change record for '{2}'".format(newDev.name, property, indigo.devices[watchinfo.id].name))
							ret.append (cacheChange(self, "property", property, watchinfo.id, newDev.id, origDev.ownerProps[property], newDev.ownerProps[property]))
					
		except Exception as e:
			self.logger.error (ext.getException(e))	
		
		return ret

#
# Action group record
#
class cacheAg:
	#
	# Initialize the  class
	#
	def __init__(self, ag):
		self.itemType = "ActionGroup"
		self.name = ag.name
		self.id = ag.id
		self.watchedBy = []
		self.watching = []
		
		self.logger = logging.getLogger ("Plugin.cacheAg")
		
	def __str__(self):
		ret = ""
		
		try:
			ret += self._addLine ("name", self.name)
			ret += self._addLine ("type", self.itemType)
			ret += self._addLine ("id", self.id)
			
			if len(self.watchedBy) == 0:
				ret += self._addLine ("watchedBy", "")
			else:
				ret += self._addLine ("watchedBy", "(dict)")
				for watchinfo in self.watchedBy:
					ret += unicode(watchinfo)
					
			if len(self.watching) == 0:
				ret += self._addLine ("watching", "")
			else:
				ret += self._addLine ("watching", "(dict)")
				for watchinfo in self.watching:
					ret += unicode(watchinfo)
				
		except:
			raise
		
		return ret
		
	def getWatchedByChanges (self, origActionGroup, newActionGroup):
		ret = []
		
		try:
			# Until Indigo lets us dig into Action Groups there's nothing to watch for, so any change is interesting
			for watchinfo in self.watchedBy:
				if origActionGroup.name != newActionGroup.name:
					ret.append (cacheChange(self, "actiongroup", "name", watchinfo.id, newActionGroup.id, origActionGroup.name, newActionGroup.name))
					
		except Exception as e:
			self.logger.error (ext.getException(e))	
		
		return ret
		
#
# Variable record
#		
class cacheVar:

	#
	# Initialize the  class
	#
	def __init__(self, var):
		self.itemType = "Variable"
		self.name = var.name
		self.id = var.id
		self.watchedBy = []
		self.watching = []
	
		self.logger = logging.getLogger ("Plugin.cacheVar")
		
	def __str__(self):
		ret = ""
		
		try:
			ret += self._addLine ("name", self.name)
			ret += self._addLine ("type", self.itemType)
			ret += self._addLine ("id", self.id)
			
			if len(self.watchedBy) == 0:
				ret += self._addLine ("watchedBy", "")
			else:
				ret += self._addLine ("watchedBy", "(dict)")
				for watchinfo in self.watchedBy:
					ret += unicode(watchinfo)
					
			if len(self.watching) == 0:
				ret += self._addLine ("watching", "")
			else:
				ret += self._addLine ("watching", "(dict)")
				for watchinfo in self.watching:
					ret += unicode(watchinfo)
				
		except:
			raise
		
		return ret
		
	def getWatchedByChanges (self, origVar, newVar):
		ret = []
		
		try:
			for watchinfo in self.watchedBy:
				#indigo.server.log(unicode(watchinfo))
				if origVar.value != newVar.value:
					ret.append (cacheChange(self, "variable", newVar.name, watchinfo.id, newVar.id, origVar.value, newVar.value))
					
		except Exception as e:
			self.logger.error (ext.getException(e))	
		
		return ret
		
#
# Change record
#
class cacheChange:
	#
	# Initialize the  class
	#
	def __init__(self, obj, type, changedName, parentId, childId, oldValue, newValue):
		self.itemType = obj.itemType
		self.type = type
		self.name = changedName
		self.parentId = parentId
		self.childId = childId
		self.oldValue = oldValue
		self.newValue = newValue
		self.indent = 0

		self.logger = logging.getLogger ("Plugin.cacheChange")

	def __str__(self):
		ret = ""
		
		try:
			ret += self._addLine ("deviceTypeId", self.itemType)
			ret += self._addLine ("type", self.type)
			ret += self._addLine ("name", self.name)
			ret += self._addLine ("oldValue", self.oldValue)
			ret += self._addLine ("newValue", self.newValue)
			ret += self._addLine ("parentId", self.parentId)
			ret += self._addLine ("childId", self.childId)
				
		except:
			raise
		
		return ret
		
	def _addLine (self, title, value, indents = 0):
		indent = ""
	
		for i in range(0, indents):
			indent += "\t"
			
		for i in range(0, self.indent):
			indent += "\t"
	
		return indent + title + " : " + unicode(value) + "\n"


























