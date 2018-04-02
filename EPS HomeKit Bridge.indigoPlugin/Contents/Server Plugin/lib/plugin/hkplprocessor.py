"""hkplprocessor.py: HomeKit device payload processor."""

__version__ 	= "1.0.0"

__modname__		= "HomeKit Payload Processor"
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
import thread

# Third Party Modules
import indigo

# Package Modules
from ..ifactory.include import ex
from ..ifactory.include import calcs
import hkpldevice

class HomebridgePayloadProcessor:
	"""
	Process an incoming API request and deliver the payload for it.
	"""
	
	###
	def __init__(self, factory):
		"""
		Set up the class.
		"""
		
		try:
			self.logger = logging.getLogger ("Plugin.HomebridgePayloadDevice")
			self.tabtitle = ""			# Title indention on __str__
			self.tabcontent = ""		# Content indention on __str__
			
			self.factory = factory		# References the HomeKit factory
						
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
	def process_incoming_api_call (self, request, query):
		""" 
		Process incoming HTTP API request from Homebridge-Indigo2.
		"""
		try:
			#indigo.server.log(unicode(query))
			#indigo.server.log(unicode(request))
			if not "/HomeKit" in request.path: return self.json_reply_error ("fail", "Invalid path")
			if not "cmd" in query: return self.json_reply_error ("fail", "Invalid request")
			if not "serverId" in query: return self.json_reply_error ("fail", "Invalid server")
						
			devId = None
			serverId = int(query["serverId"][0])
			jkey = None
			cmd = query["cmd"][0]
			
			if not serverId in indigo.devices: return self.json_reply_error ("fail", "Server Id invalid")
			
			if "objId" in query: devId = int(query["objId"][0])
			if "jkey" in query: jkey = query["jkey"][0]
			
			if cmd == "deviceList": return self.json_reply_command_devicelist (serverId)
			if cmd == "getInfo": return self.json_reply_command_getinfo (devId, jkey, serverId)
			if cmd == "setCharacteristic": return self.json_reply_command_set_characteristic (query, devId, jkey, serverId)
			
			return self.json_reply_error ("fail", "Nothing to process")

		
		except Exception as e:
			self.logger.error (ex.stack_trace(e))
			return self.json_reply_error ("fail", "A fatal exception was encountered while processing your request, check the Indigo log for details")

	###
	def legacy_get_homekit_object (self, devId, serverId, hkType):
		"""
		Call into the legacy factory in the plugin to retrieve the HomeKit service object for this device.
		
		Arguments:
			devId:		Indigo device Id for the service
			serverId:	Indigo device Id for the server hosting the device
			HkType:		HomeKit service_* type to resolve
		"""
		try:
			return self.factory.factory.PluginBase.epslibrary.homekit.getServiceObject (devId, serverId, hkType, False,  True)
		
		except Exception as e:
			self.logger.error (ex.stack_trace(e))
			
	###
	def legacy_extract_json_objects (self, serverId):
		"""
		Find the JSON encoded includedDevices and includedActions in server properties and return them as dictionaries.
		"""
		try:
			server = indigo.devices[serverId]
			includedDevices = []
			includedActions = []
			includedVariables = []
			
			if "includedDevices" in server.pluginProps: includedDevices = json.loads(server.pluginProps["includedDevices"])
			if "includedActions" in server.pluginProps: includedActions = json.loads(server.pluginProps["includedActions"])
			if "includedVariables" in server.pluginProps: includedVariables = json.loads(server.pluginProps["includedVariables"])
					
		except Exception as e:
			self.logger.error (ex.stack_trace(e))
			
		return includedDevices, includedActions, includedVariables
		
	###
	def extract_json_object (self, jkey, serverId, includedDevices, includedActions, includedVariables, excludeObject = False):
		"""
		Read through all included objects to find an item matching the provided jkey.
		"""
		
		try:
			foundIn = "includedDevices"
			rec = None
			obj = None
			
			for r in includedDevices:
				if r["jkey"] == jkey:
					rec = r
					if not excludeObject: obj = self.legacy_get_homekit_object (r["id"], serverId, r["hktype"])
					break
			
			if not obj:	
				for r in includedActions:
					if r["jkey"] == jkey:
						rec = r
						if not excludeObject: obj = self.legacy_get_homekit_object (r["id"], serverId, r["hktype"])
						break
						
			if not obj:	
				for r in includedVariables:
					if r["jkey"] == jkey:
						rec = r
						if not excludeObject: obj = self.legacy_get_homekit_object (r["id"], serverId, r["hktype"])
						break
			
		except Exception as e:
			self.logger.error (ex.stack_trace(e))
			
		return obj, rec

	###
	def json_reply_command_set_characteristic (self, query, devId, jkey, serverId):
		"""
		Process incoming API command 'setCharacteristic'.
		"""
		try:
			obj = None
			rec = None
			characteristic = None
			value = None
			
			for param, val in query.iteritems():
				if param == "serverId": continue
				if param == "objId": continue
				if param == "jkey": continue
				if param == "cmd": continue
				
				characteristic = param
				value = val[0]
				
			includedDevices, includedActions, includedVariables = self.legacy_extract_json_objects (serverId)	
										
			if jkey in self.factory.HKDEFINITIONS:
				obj = self.factory.HKDEFINITIONS[jkey]	
				toss, rec = self.extract_json_object (jkey, serverId, includedDevices, includedActions, includedVariables, True)
			else:								
				obj, rec = self.extract_json_object (jkey, serverId, includedDevices, includedActions, includedVariables)		
						
			if obj:		
				for a in obj.actions:
					if a.characteristic == characteristic: 
						result = a.run (value, obj.objId, False)
						if result: 
							# Result will be true it passes and runs
							payload = hkpldevice.HomebridgePayloadDevice (self.factory)
							newvalue = calcs.convert_to_compared_datatype (value, a.whenvalue)
							data = payload.legacy_populate_from_service (obj, rec, serverId)
							if devId in indigo.actionGroups:
								# Action groups don't do anything, just return that it is on and call back in 2 seconds to toggle off
								data = payload.legacy_populate_from_service (obj, rec, serverId, characteristic, newvalue)
								thread.start_new_thread(self.factory.factory.PluginBase.timedCallbackToURL, (serverId, jkey, 2, rec))
								
							if obj.recurringUpdate:
								# Timer based device where we need real-time updates
								thread.start_new_thread(self.factory.factory.PluginBase.timedCallbackToURL, (serverId, jkey, obj.recurringSeconds, rec))
							break  
				
				#indigo.server.log(json.dumps(data, indent=4))
				#thread.start_new_thread(self.factory.factory.PluginBase.timedCallbackToURL, (serverId, rec["jkey"], 0))
				return "text/css",	json.dumps(data, indent=4)
				
			return self.json_reply_error ("fail", "Object not found")
		
		except Exception as e:
			self.logger.error (ex.stack_trace(e))
			return self.json_reply_error ("fail", "A fatal exception was encountered while processing your request, check the Indigo log for details")

	###
	def json_reply_command_devicelist (self, serverId):
		"""
		Process incoming API command 'deviceList'.
		"""
		try:
			includedDevices, includedActions, includedVariables = self.legacy_extract_json_objects (serverId)
			
			deviceList = []

			for r in includedDevices:
				if r["jkey"] in self.factory.HKCACHE:
					deviceList.append(self.factory.HKCACHE[r["jkey"]])
				else:		
					if r["jkey"] in self.factory.HKDEFINITIONS:
						obj = self.factory.HKDEFINITIONS[r["jkey"]]
					else:				
						obj = self.legacy_get_homekit_object (r["id"], serverId, r["hktype"])
						
					payload = hkpldevice.HomebridgePayloadDevice (self.factory)
					deviceList.append(payload.legacy_populate_from_service (obj, r, serverId))
				
			for r in includedActions:
				if r["jkey"] in self.factory.HKCACHE:
					deviceList.append(self.factory.HKCACHE[r["jkey"]])
				else:		
					if r["jkey"] in self.factory.HKDEFINITIONS:
						obj = self.factory.HKDEFINITIONS[r["jkey"]]
					else:				
						obj = self.legacy_get_homekit_object (r["id"], serverId, r["hktype"])
						
					payload = hkpldevice.HomebridgePayloadDevice (self.factory)
					deviceList.append(payload.legacy_populate_from_service (obj, r, serverId))
					
				#obj = self.legacy_get_homekit_object (r["id"], serverId, r["hktype"])
				#payload = hkpldevice.HomebridgePayloadDevice (self.factory)
				#deviceList.append(payload.legacy_populate_from_service (obj, r, serverId))
				
			for r in includedVariables:
				if r["jkey"] in self.factory.HKCACHE:
					deviceList.append(self.factory.HKCACHE[r["jkey"]])
				else:		
					if r["jkey"] in self.factory.HKDEFINITIONS:
						obj = self.factory.HKDEFINITIONS[r["jkey"]]
					else:				
						obj = self.legacy_get_homekit_object (r["id"], serverId, r["hktype"])
						
					payload = hkpldevice.HomebridgePayloadDevice (self.factory)
					deviceList.append(payload.legacy_populate_from_service (obj, r, serverId))	
				
			return "text/css",	json.dumps(deviceList, indent=4)
		
		except Exception as e:
			self.logger.error (ex.stack_trace(e))
			return self.json_reply_error ("fail", "A fatal exception was encountered while processing your request, check the Indigo log for details")
			
	###
	def json_reply_command_getinfo (self, devId, jkey, serverId):
		"""
		Process incoming API command 'getInfo'.
		"""
		try:
			if jkey in self.factory.HKCACHE:
				return "text/css",	json.dumps(self.factory.HKCACHE[jkey], indent=4)
			else:
				includedDevices, includedActions, includedVariables = self.legacy_extract_json_objects (serverId)			
				obj, rec = self.extract_json_object (jkey, serverId, includedDevices, includedActions, includedVariables)		
						
				if obj:				
					payload = hkpldevice.HomebridgePayloadDevice (self.factory)
					data = payload.legacy_populate_from_service (obj, rec, serverId)
					return "text/css",	json.dumps(data, indent=4)
				
			return self.json_reply_error ("fail", "Object not found")		
		
		except Exception as e:
			self.logger.error (ex.stack_trace(e))	
			return self.json_reply_error ("fail", "A fatal exception was encountered while processing your request, check the Indigo log for details")		

	###
	def json_reply_error (self, result, message):
		"""
		Return generic error message to HTTP engine.
		"""
		try:
			msg = {}
			msg["result"] = result
			msg["message"] = message
			return "text/css",	json.dumps(msg, indent=4)
		
		except Exception as e:
			self.logger.error (ex.stack_trace(e))
			msg = {}
			msg["result"] = "fail"
			msg["message"] = "A fatal exception was encountered while processing your request, check the Indigo log for details"
			return "text/css",	json.dumps(msg, indent=4)























