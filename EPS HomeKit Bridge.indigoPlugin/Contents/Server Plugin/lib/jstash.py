# lib.ui - Custom list returns and UI enhancements
#
# Copyright (c) 2018 ColoradoFourWheeler / EPS
#

import indigo
import logging

import ext
import dtutil

import re
import ast
import datetime
from datetime import date, timedelta
import time
import sys
import string
import calendar

# For JSON Encoding
import json # duh
import hashlib # unique keys
import operator # sorting
from random import randint # unique keys

class jstash:

	RECORDS = {} # Record definitions
	
	#
	# Initialize the class
	#
	def __init__ (self, factory):
		self.logger = logging.getLogger ("Plugin.jstash")
		self.factory = factory
		
	#
	# Create a hash key if needed for JSON encoding/decoding
	#
	def createHashKey(self, keyString):
		hashKey = hashlib.sha256(keyString.encode('ascii', 'ignore')).digest().encode("hex")  # [0:16]
		return hashKey	
		

	#
	# Create a record definition
	#		
	def createRecordDefinition (self, recordName, fieldsDict):
		try:
			if "jkey" not in fieldsDict:
				fieldsDict["jkey"] = ""
				
			self.RECORDS[recordName] = fieldsDict
		
		except Exception as e:
			self.logger.error (ext.getException(e))
			return False
			
		return True
		
	#
	# Return a new record of type
	#
	def createRecord (self, recordName):
		try:
			rec = {}
			
			if recordName in self.RECORDS:
				template = self.RECORDS[recordName]
				for k, v in template.iteritems():
					rec[k] = v
					
					if k == "jkey":
						d = indigo.server.getTime()
						rec[k] = self.createHashKey (d.strftime("%Y-%m-%d %H:%M:%S %f") + str(randint(1000, 1000001)))
					
				return rec
			
		except Exception as e:
			self.logger.error (ext.getException(e))
			
		return {}
		
	#
	# Deserialize a specified JSON field into it's records
	#
	def deserializeJSONField (self, recordsList):
		try:
			pass
		
		except Exception as e:
			self.logger.error (ext.getException(e))
			
		return None
			
	#
	# Check to see if any records field equals a value
	#
	def getRecordWithFieldEquals (self, recordsList, fieldName, fieldValue, caseSensitive = False):
		try:
			if not caseSensitive and (type(fieldValue) is str or type(fieldValue) is unicode): fieldValue = fieldValue.lower()
			
			for r in recordsList:
				if fieldName in r:
					recfield = r[fieldName]
					#indigo.server.log(unicode(type(recfield)))
					if not caseSensitive and (type(recfield) is str or type(recfield) is unicode): recfield = recfield.lower()

					#indigo.server.log("Does {0} equal {1}?".format(str(recfield), str(fieldValue)))
					if recfield == fieldValue:
						return r
				
		except Exception as e:
			self.logger.error (ext.getException(e))
			
		return None
		
	#
	# Sort a list via one of the dict keys contained within it's objects
	#
	def sortStash (self, recordsList, sortField, sortDesc = False):
		try:
			newList = sorted(recordsList, key=operator.itemgetter(sortField), reverse=sortDesc)
			return newList
			
		except Exception as e:
			self.logger.error (ext.getException(e))
			
		return recordsList
		

	#
	# Run through a stash and remove a specific record
	#
	def removeRecordFromStash (self, recordsList, fieldName, fieldValue, caseSensitive = False):
		try:
			newRecordsList = []
			
			if not caseSensitive and (type(fieldValue) is str or type(fieldValue) is unicode): fieldValue = fieldValue.lower()
			
			for r in recordsList:
				if fieldName in r:
					recfield = r[fieldName]
					if not caseSensitive and (type(recfield) is str or type(recfield) is unicode): recfield = recfield.lower()

					#indigo.server.log("Does {0} equal {1}?".format(str(recfield), str(fieldValue)))
					if recfield != fieldValue:
						newRecordsList.append (r)
				
		except Exception as e:
			self.logger.error (ext.getException(e))
			return recordsList
			
		return newRecordsList