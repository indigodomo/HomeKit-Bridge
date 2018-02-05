#! /usr/bin/env python
# -*- coding: utf-8 -*-


# proc - Process, system and memory information and handling
#
# Copyright (c) 2018 ColoradoFourWheeler / EPS
#

import indigo
import linecache # exception reporting
import sys # exception reporting

import subprocess
import re
import operator

plugin = None

#
# Get running processes (defaults to indigo plugins)
#
def getRunningProcesses (procName = "indigo", sort = True, sortKey = "memoryValue", sortDesc = True):
	try:
		procInfo = [] # Return
		
		data = subprocess.Popen(('ps ax | grep "{0}"'.format(procName) ), shell=True, stdout=subprocess.PIPE).communicate()[0]
		processes = data.split('\n')
		nfields = len(processes[0].split()) - 1
		
		for row in processes[1:]:
		    #indigo.server.log(unicode(row.split(None, nfields)))
			#pluginReport = {}
			procItem = {}
			
			psData = row.split(None, nfields)
			if len(psData) < 5: # Don't continue if there is nothing to process
				continue
		    
			procItem["pid"] = psData[0]   
			procItem["name"] = psData[4]
			
			#indigo.server.log ("Process: " + unicode(psData))
			
			# Get the name starting at where we find -p1176
			pfound = False
			for i in range (0, len(psData)):
				try:
					if psData[i] == "-p1176":
						pfound = True
						continue # We don't need this one
					
					if pfound:
						procItem["name"] += " " + psData[i]
						
				except Exception as ex:
					continue
					
			#if len(psData) >= 10:
			#	procItem["name"] = psData[9]

			#if len(psData) >= 11:
			#	procItem["name"] += " " + psData[10]
			    
			if procItem["name"] == "": continue # Don't process no name items
			if "grep" in procItem["name"]: continue # Don't process this ps command
			if "/bin/sh" in procItem["name"]: continue # Don't process this ps command
			
			# Clean up the process name
			procItem["name"] = procItem["name"].replace("-f", "")
			procItem["name"] = procItem["name"].replace(".indigoplugin", "")
			procItem["name"] = procItem["name"].replace(".indigoPlugin", "")
			procItem["name"] = procItem["name"].replace("/Library/Application ", "")
			
			# Get memory information
			#data = subprocess.Popen(('top -l 1 -s 0 | grep ' + procItem["pid"] ), shell=True, stdout=subprocess.PIPE).communicate()[0]
			data = subprocess.Popen(('top -l 1 -s 0 -pid ' + procItem["pid"] ), shell=True, stdout=subprocess.PIPE).communicate()[0]
			sep = re.compile('[\s]+')
			rowElements = sep.split(data)
			if len(rowElements) == 0: continue
			
			#indigo.server.log ("Top: " + unicode(rowElements))
			
			#if "/" in procItem["name"] and rowElements["1"] != "" : procItem["name"] = rowElements[1]
			
			procItem["cpu"] = "" #rowElements[18]
			if procItem["cpu"] != "" and procItem["cpu"] != "0":
				procItem["cpu"] = procItem["cpu"].replace("+", "") # get rid of the plus symbol
				procItem["cpu"] = str(round(float(procItem["cpu"]) / 1000, 2)) + "%"
			
			if len(rowElements) < 111: continue # Too few fields to be an Indigo plugin
			
			procItem["memory"] = rowElements[111]
						
			# Make memory readable
			procItem["memory"] = procItem["memory"].replace("+", "")
			procItem["memory"] = procItem["memory"].replace("M", " MB")
			procItem["memory"] = procItem["memory"].replace("K", " KB")
			
			procItem["memoryValue"] = procItem["memory"].replace(" KB", "")
			procItem["memoryValue"] = procItem["memoryValue"].replace(" MB", "")
			try:
				procItem["memoryValue"] = int(procItem["memoryValue"])
			except Exception as ex:
				procItem["memoryValue"] = 0
			
			procItem["realMemory"] = procItem["memoryValue"] * 1000000
			if "KB" in procItem["memory"]: procItem["realMemory"] = procItem["memoryValue"] * 1000
			
			procInfo.append(procItem)
			
		if sort:
			procInfo = sorted(procInfo, key=operator.itemgetter(sortKey), reverse=sortDesc)
	
	except Exception as e:
		indigo.server.log (getException(e), isError=True)
		
	return procInfo
	
#
# Get exception details
#
def getException (e):
	exc_type, exc_obj, tb = sys.exc_info()
	f = tb.tb_frame
	lineno = tb.tb_lineno
	filenameEx = f.f_code.co_filename
	filename = filenameEx.split("/")
	filename = filename[len(filename)-1]
	filename = filename.replace(".py", "")
	filename = filename.replace(".pyc","")
	linecache.checkcache(filename)
	line = linecache.getline(filenameEx, lineno, f.f_globals)
	exceptionDetail = "Exception in %s.%s line %i: %s\n\t\t\t\t\t\t\t CODE: %s" % (filename, f.f_code.co_name, lineno, str(e), line.replace("\t",""))
	
	return exceptionDetail
		
#
# Print exception details
#
def printException (e, logger = None):
	if logger is None:
		if plugin is not None:
			plugin.logger.error (e)
			
		else:
			indigo.server.log (unicode(e), isError=True)	
			
	else:
		logger.error (e)
		
#
# Get a JSON Py dictionary item for the key provided
#
def getJSONDictForKey (JData, key):
	try:
		keylist = ""
		itemList = json.loads(JData)
		for item in itemList:
			keylist += item["key"] + "\n"
			if item["key"] == key:
				return item
	
	except Exception as e:
		indigo.server.log (getException(e))
		
	indigo.server.log ("ext.getJSONDictForKey was unable to find an entry for key '{0}'.  The follow keys were found: \n{1}".format(key, keylist))
	return {}
