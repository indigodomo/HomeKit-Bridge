"""calcs.py: Useful calculations."""

__version__ 	= "1.0.0"

__modname__		= "Useful Calculations"
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
import linecache
import json

# Third Party Modules
import indigo

# Package Modules
import ex

# Enumerations
kExceptionOutputPrefix = "\n\n\t\t\t\t\t\t\t "

class CalcsException(Exception):
    pass

###
def filter_to_dict (filter):
	"""
	Reads a filter passed from Devices.xml into a dictionary and returns it.
	"""

	try:	
		args = {}
		filter = filter.replace("[", "").replace("]","")
				
		for f in filter.split(","):
			f = f.strip()  # Clean  up spaces
			valkey = f.split("=")
			valname = valkey[0].lower().strip()
			args[valname] = valkey[1].strip()
			
		return args
			
	except Exception as e:
		e.args += (filter,)
		raise CalcsException (kExceptionOutputPrefix + ex.stack_trace(e))
		
###
def type_to_unicode_output (obj):
	"""
	Converts the type of the object to a string representation.
	"""

	try:	
		if obj is None: return "None"
		return u"{} ({})".format(obj, unicode(type(obj)).replace("<type '", "").replace("'>","").replace("<class '", ""))
			
	except Exception as e:
		e.args += (unicode(type(obj)),)
		raise CalcsException (kExceptionOutputPrefix + ex.stack_trace(e))
		
###
def generic_unicode_output (tabtitle, tabcontent, obj, title = None):
	"""
	Generic unicode output for custom classes
	"""
	
	try:
		ret = ""
		
		if title: ret += u"{}{} : {}\n".format(tabtitle, title, type_to_unicode_output(obj) )
		
		for a in dir(obj):
			if callable(getattr(obj, a)): continue
			if a.startswith("_"): continue
			if a == "factory": continue
			if a == "logger": continue
			if a == "tabtitle" or a == "tabcontent": continue
		
			if type(getattr(obj, a)) == list:
				ret += u"{}{} : (list) \n".format(tabcontent, a)
				
				for l in getattr(obj, a):
					ret += u"\t{}item :\n{}{}".format(tabcontent, tabcontent, l)
			else:
				ret += u"{}{} : {}\n".format(tabcontent, a, type_to_unicode_output(getattr(obj, a)) )
	
	except Exception as e:
		e.args += (unicode(type(obj)),)
		raise CalcsException (kExceptionOutputPrefix + ex.stack_trace(e))
		
	return ret

###
def generic_class_to_dict (obj):
	"""
	Using the same exclusions as generic_unicode_output, convert class data to a JSON record
	"""
	
	try:
		data = {}
		
		for a in dir(obj):
			if callable(getattr(obj, a)): continue
			if a.startswith("_"): continue
			if a == "factory": continue
			if a == "logger": continue
			if a == "tabtitle" or a == "tabcontent": continue
		
			if type(getattr(obj, a)) == list:
				listitem = []
	
				for l in getattr(obj, a):
					if "'instance'" in unicode(type(l)):
						listitem.append(generic_class_to_dict(l))
					else:
						listitem.append(l)
						
				data[a] = listitem
								
			else:
				data[a] = getattr(obj, a)
			
	except Exception as e:
		e.args += (unicode(type(obj)),)
		raise CalcsException (kExceptionOutputPrefix + ex.stack_trace(e))
		
	return data























