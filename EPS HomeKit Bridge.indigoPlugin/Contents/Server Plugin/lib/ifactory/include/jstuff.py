"""jstuff.py: JSON storage and retrieval method for Indigo form definitions."""

__version__ 	= "1.0.0"

__modname__		= "Indigo JSON Stuffer"
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
import random

# Third Party Modules
import indigo

# Package Modules
import ex
import calcs

# Enumerations
kFieldIndexer = "ipf_fieldStuffIndex"  # Field in valuesDict with fieldnames
kFieldStorage = "ipf_jstuff"  # Where the JSON stuff will be saved
kFieldUniqueId = "ipf_uniqueId" # Unique Id that is added to the form until it is closed so we can differentiate between them
kFieldRecChanged = "ipf_stashchanged"  # Boolean indicating that the JSON stash has changed
#kFieldMethod = "fieldStuffIndex"  # The method= that must be present to invoke this library

class JStuff:
	"""
	Manages JSON data storage inside of form definitions.
	"""
	
	RecordDefinitions = {}  # All record types defined by the form
	RecordFieldIndexes = {}  # Each field and all of the records it belongs to
	Records = {}  # All records
	
	ExcludedForms = []  # List of any forms that don't meet the criteria on record definition so we can exit this library on them
		
	def __init__(self, factory):
		try:
			self.factory = factory		# References the Indigo plugin
		
			self.logger = logging.getLogger ("Plugin.jstuff")
		
			self.logger.debug ("{} {} loaded".format(__modname__, __version__))
			
		except Exception as e:
			self.logger.error (ex.stack_trace(e))
			
		
	#
	# UI form field changed
	#
	def onformFieldChanged (self, valuesDict, typeId, devId):
		"""
		A form field was changed, prompting a call from the factory to here in case there are JSON parameters.
		"""
	
		try:
			errorsDict = indigo.Dict()
			
			if kFieldIndexer not in valuesDict: return valuesDict  # Record doesn't have record definitions so no need to do anything else			
			if kFieldUniqueId not in valuesDict: valuesDict[kFieldUniqueId] = str(int(random.random() * 100000000))  # Add unique Id
			
			#self.logger.info ("Saving record")
			
			records = {}
			if valuesDict[kFieldUniqueId] in self.Records: records = self.Records[valuesDict[kFieldUniqueId]]
			
			jstuff = {}
			if kFieldStorage in valuesDict: jstuff = json.loads(valuesDict[kFieldStorage])
			
			
			
			# See if any form fields are being used on records
			if valuesDict[kFieldUniqueId] in self.RecordDefinitions:
				#self.logger.info ("Extracting record data")
				
				recordSet = self.RecordDefinitions[valuesDict[kFieldUniqueId]]  # All records for this Id
				
				for field, value in valuesDict.iteritems():
					if field in self.RecordFieldIndexes:
						attachedRecords = self.RecordFieldIndexes[field]
						
						# Loop through all record definitions attached to this field
						for recordDefs in attachedRecords:
							(uniqueId, recordDef) = recordDefs.split("|")
							if uniqueId != valuesDict[kFieldUniqueId]: continue  # Different form
						
							# If we get here then we have a def, lets get the record definition class object
							recordClasses = self.RecordDefinitions[uniqueId]
							recordClass = recordClasses[recordDef]
							
							# No sense going further if the index value of the record def is empty
							if valuesDict[recordClass.indexField] == "":
								self.logger.info ("Index {} is empty, not saving {} record".format(recordClass.indexField, recordClass.name))
								continue
							
							# Get all records for this form
							formRecordTypes = {}
							if uniqueId in self.Records: formRecordTypes = self.Records[uniqueId]
							
							# Get all records for this record type
							formRecords = {}
							if recordDef in formRecordTypes: formRecords = formRecordTypes[recordDef]
							
							# Get this index						
							if recordClass.indexField in formRecords:
								rec = formRecords[recordClass.indexField]
							else:
								rec = _JStuffRecord (recordClass, valuesDict)
	
							# Capture the existing value and compare to new value if this is the index field
							if field == recordClass.indexField and getattr(rec, field) != value and rec.indexReset:
								self.logger.error ("Index field changed!")
	
							# Set the value						
							rec.set_field_value (field, value)
							if rec.updated: 
								valuesDict[kFieldRecChanged] = True
							else:
								valuesDict[kFieldRecChanged] = False
							
							# Save the record to cache
							formRecords[valuesDict[recordClass.indexField]] = rec  # Save record with the dict key being the value of the index field
							formRecordTypes[recordDef] = formRecords
							self.Records[uniqueId] = formRecordTypes
							
							
										
				valuesDict = self._saveJSON (valuesDict)  # Write the JSON data to the record
						
		except Exception as e:
			self.logger.error (ex.stack_trace(e))
			
		return (valuesDict, errorsDict)
		
	#
	# Write to JSON
	#
	def _saveJSON (self, valuesDict):
		"""
		Write the contents of the cached records to the valuesDict form field in JSON format.
		"""
		
		try:
			if kFieldIndexer not in valuesDict: return valuesDict  # It's not a jstuff defined form
			if kFieldUniqueId not in valuesDict: return valuesDict  # Can't do this without the unique Id
			if valuesDict[kFieldUniqueId] not in self.Records: return valuesDict  # Haven't saved records yet
			if valuesDict[kFieldUniqueId] in self.ExcludedForms: return valuesDict  # This uniqueId has been excluded
			
			formrecords = self.Records[valuesDict[kFieldUniqueId]]
			
			jdata = {}
			if kFieldStorage in valuesDict: jdata = json.loads(valuesDict[kFieldStorage])  # Load existing JSON if it is there
						
			for recordType, records in formrecords.iteritems():	
				data = {}
				for indexValue, record in records.iteritems():
					#indigo.server.log("{}: {}: \n{}".format(recordType, indexValue, unicode(record)))
					data[indexValue] = record.build_dict()  # Add record for each index
					
				jdata[recordType] = data  # Add dict of records for each record type
				
			jdump = json.dumps(jdata)
			indigo.server.log(unicode(jdump))
		
		except Exception as e:
			self.logger.error (ex.stack_trace(e))
			
		return valuesDict
		
		
	#
	# UI form passing a record definition
	#
	def fieldStuffIndex (self, filter, valuesDict, typeId, targetId):
		"""
		Device.xml dynamic list field that defines the jstuff record.
		"""
		
		try:
			ret = [("default", "")]
			if filter == "": 
				self.logger.error ("Form field {} cannot be processed without a filter".format(kFieldIndexer))
				return ret  # This doesn't work without filters
				
			if kFieldUniqueId not in valuesDict: return ret  # The first field change has not transpired if we don't this Id so we can't do this yet
						
			#self.logger.info ("Setting up jstuff record definition")
			
			# Break down the filter
			args = calcs.filter_to_dict(filter)
			#if not kFieldMethod in args: 
			#	indigo.server.log("Couldn't find {}".format(kFieldMethod))
			#	indigo.server.log(unicode(args))
			#	self.ExcludedForms.append(valuesDict[kFieldUniqueId])  # Add to excluded forms so formFieldChanged doesn't try to process
			#	return ret  # If the method= doesn't equal this then it is malformed
			
			# All record definitions for this unique Id
			definitions = {}
			if valuesDict[kFieldUniqueId] in self.RecordDefinitions: definitions = self.RecordDefinitions[valuesDict[kFieldUniqueId]]
			
			# See if this record definition has already been added
			if definitions and "name" in args and args["name"] in definitions: return ret
			
			# Process the filter
			rec = _JStuffRecordDefinition(args, valuesDict, typeId, targetId)
			definitions[rec.name] = rec  # Save this record definition to this unique Id list of record definitions
			self.RecordDefinitions[valuesDict[kFieldUniqueId]] = definitions  # Save to global cache
			
			# Create the index so we can find this later
			for field in rec.include:
				recitem = []
				if field in self.RecordFieldIndexes: recitem = self.RecordFieldIndexes[field]
				
				if not rec.name in recitem: recitem.append(valuesDict[kFieldUniqueId] + "|" + rec.name)
				self.RecordFieldIndexes[field] = recitem
				
			#indigo.server.log(unicode(self.RecordFieldIndexes))
			#indigo.server.log(unicode(self.RecordDefinitions))
						
		except Exception as e:
			self.logger.error (ex.stack_trace(e))
			
		return ret	


class _JStuffRecord:
	"""
	A record that will be JSON stuffed into the form fields.
	"""
	
	def __init__(self, recordDef, valuesDict):
		try:
			self.logger = logging.getLogger ("Plugin.jstuff_record")
			
			self.name = recordDef.name
			self.index = valuesDict[recordDef.indexField]
			self.updated = False
			self.debug = False
			self.indexReset = False
			
			self.debug = recordDef.debug
			self.indexReset = recordDef.indexReset
			
			for a in recordDef.include:
				setattr (self, a, valuesDict[a]) # Set an attribute matching the field value
				
			for a in recordDef.manual:
				setattr (self, a, valuesDict[a]) # Set an attribute matching the field value	
				
		except Exception as e:
			self.logger.error (ex.stack_trace(e))
			
	def __str__ (self):
		ret = ""
		
		ret += "JStuff Record : (JStuffRecord)\n"
		ret += "\tname : {0}\n".format(self.name)
		ret += "\tindex : {0}\n".format(self.index)
		ret += "\tupdated : {0}\n".format(self.updated)
		ret += "\tdebug : {0}\n".format(self.debug)
		
		for a in dir(self):
			if a == "name": continue
			if a == "debug": continue
			if a == "index": continue
			if a == "logger": continue
			if a.startswith("_"): continue
			if a == "set_field_value": continue
			if a == "build_dict": continue
			
			value = getattr(self, a)
			#indigo.server.log(unicode(type(value)))
			if unicode(type(value)) == "<class 'indigo.List'>": 
				ret += "\t{} : (List)\n".format(a)
				
				for i in value:
					ret += "\t\t{}\n".format(i)
			else:
				ret += "\t{} : {}\n".format(a, value)
		
		return ret	
		
	def set_field_value (self, attrib, value):
		"""
		Set the value of an attribute to the value provided, setting the change flag if different.
		"""
		
		try:
			thisUpdated = False
			
			if attrib in dir(self):
				if getattr (self, attrib) != value: 
					self.updated = True
					thisUpdated = True
				setattr (self, attrib, value)
				
				if self.debug and thisUpdated: self.logger.info("\nDEBUG MODE: CHANGED FIELD {} TO {}\n{}".format(attrib, value, unicode(self)))
				
				return True
			
		except Exception as e:
			self.logger.error (ex.stack_trace(e))
		
		return False
		
	def build_dict (self):
		try:
			rec = {}
			
			rec["name"] = self.name
			rec["index"] = self.index
			
			for a in dir(self):
				if a == "debug": continue
				if a == "name": continue
				if a == "index": continue
				if a == "logger": continue
				if a.startswith("_"): continue
				if a == "set_field_value": continue
				if a == "build_dict": continue
			
				value = getattr(self, a)
				
				if unicode(type(value)) == "<class 'indigo.List'>": 
					# Build non Indigo list so it can JSON encode
					newlist = []
					for i in value:
						newlist.append(i)
						
					rec[a] = newlist
				else:
					rec[a] = value
		
		except Exception as e:
			self.logger.error (ex.stack_trace(e))
		
		if self.debug: self.logger.info ("\nDEBUG MODE: JSON DATA\n{}".format(unicode(rec)))
		return rec
			

class _JStuffRecordDefinition:
	"""
	A record definition that is defined in Devices.xml using the fieldStuffIndex custom list callback that compiles all arguments into an object.
	"""
	
	def __init__(self, args, valuesDict, typeId, targetId):
		"""
		Create the record using arguments passed from the fieldStuffIndex function in JStuff.
		"""
	
		try:
			self.logger = logging.getLogger ("Plugin.jstuff_record_definition")
		
			self.name = ""
			self.include = []
			self.exclude = []
			self.manual = []
			self.indexField = ""
			self.debug = False
			self.indexReset = False
		
			if "name" in args: self.name = args["name"]
			if "indexfield" in args: self.indexField = args["indexfield"]
			
			if "exclude" in args: self.exclude = self.process_include_exclude(args["exclude"], valuesDict, self.indexField)
			if "include" in args: self.include = self.process_include_exclude(args["include"], valuesDict, self.indexField)
			if "manual" in args: self.manual = self.process_include_exclude(args["manual"], valuesDict, self.indexField)
			if "indexchangereset" in args and args["indexchangereset"].lower() == "true": self.indexReset = True
			
			# Populate the remaining fields if we got only excludes
			if not self.include:
				for field, value in valuesDict.iteritems():
					if field.startswith("ipf") or field == self.indexField: continue # Don't include these
					if not field in self.exclude: 
						self.include.append(field)
						
			# Populate the remaining fields if we got only excludes
			if not self.exclude:
				for field, value in valuesDict.iteritems():
					if field.startswith("ipf") or field == self.indexField: continue # Don't include these
					if not field in self.include: 
						self.exclude.append(field)		
						
			if "debug" in args and args["debug"].lower() == "true": 
				self.debug = True
				self.logger.info(unicode(self))
		
		except Exception as e:
			self.logger.error (ex.stack_trace(e))
			
	def __str__ (self):
		ret = ""
		
		ret += "JStuff Record Definition : (JStuffRecordDefinition)\n"
		ret += "\tname : {0}\n".format(self.name)
		ret += "\tindexField : {0}\n".format(self.indexField)
		ret += "\tdebug : {0}\n".format(self.debug)
		
		ret += "\texclude : (List)\n"
		for e in self.exclude:
			ret += "\t\t{}\n".format(e)
			
		ret += "\tinclude : (List)\n"
		for e in self.include:
			ret += "\t\t{}\n".format(e)	
			
		ret += "\tmanual : (List)\n"
		for e in self.manual:
			ret += "\t\t{}\n".format(e)		
		
		return ret
	
	
	def process_include_exclude (self, item, valuesDict, indexField):
		try:
			valueList = []
					
			items = item.replace("(", "").replace(")", "")
			items = items.split(";")
			
			for e in items:
				if e.startswith("ipf"): continue # Don't add special library fields to any list
				if e == indexField: continue # Don't add the index to any list
					
				e = e.strip()
				#indigo.server.log(e)
				if "*" in e:
					filter = e.replace("*", "")
					
					for field, value in valuesDict.iteritems():					
						#indigo.server.log(field)
						if field.startswith("ipf"): continue # Don't add special library fields to any list
						if field == indexField: continue # Don't add the index to any list
						
						if e.endswith("*"):	
							if field.startswith(filter): valueList.append(field)
							
						if e.startswith("*"):	
							if field.endswith(filter): valueList.append(field)		
						
				else:
					valueList.append(e)
					
				
		
		except Exception as e:
			self.logger.error (ex.stack_trace(e))

		return valueList
































