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
	# Generic error
    pass
    
class TypeConversionError(Exception):
	# Error converting from one data type to another
    pass 
    
###
def convert_temperature (value, toCelsius = False, asInteger = False):
	"""
	Convert a temperature value to Celsius or Fahrenheit.
	
	Arguments:
		toCelsius:		convert value to Celsius (default is Fahrenheit)
		asInteger:		returns full float value when false and integer value when true
		
	Returns:
		Converted value as a float
	"""
	
	try:
		if toCelsius:
			# Convert value to celsius
			value = float(value)
			value = (value - 32) / 1.8000
			value = round(value, precision)
		
			if asInteger: return int(value)
		
			return value
		
		else:
			# Default: convert value to fahrenheit
			value = float(value)
			value = (value * 1.8000) + 32
			value = round(value, precision)
		
			if asInteger: return int(value)
		
			return value
	
	except Exception as e:
		e.args += (value,)
		e.args += (u"to Celsius: {}".format(toCelsius),)
		raise CalcsException (kExceptionOutputPrefix + ex.stack_trace(e))
	

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
	Converts the type of the object to a string representation including the type (used for __str__ functions).
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
	Generic unicode output for custom classes (called by __str__ functions).
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
	Using the same exclusions as generic_unicode_output, convert class data to a dictionary object.
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

###
def convert_to_compared_datatype (source, destination):
	"""
	Converts the source value to the destination data type.
	
	Arguments:
		source:			the source value who's data type needs to be changed
		destination:	the value that the data type will be derived from
		
	Returns:
		source:			value of source converted to the data type of destination
	"""
	
	try:	
		converted = False  # Assume failure
			
		# Convert to string types for ease
		stype = str(type(source)).replace("<type '", "").replace("'>", "")
		dtype = str(type(destination)).replace("<type '", "").replace("'>", "")
		
		
		# Convert from None
		if stype == "NoneType":
			if dtype == "float": source = 0.0
			if dtype == "int": source = 0
			if dtype == "bool": source = False
			if dtype == "string": source = ""
			converted = True
		
		# Convert from Boolean
		if stype == "bool":
			
			# To integer
			if dtype == "int":
				if source: source = 1
				if not source: source = 0
				converted = True
				
			# To float
			elif dtype == "float":
				if source: source = 1.0
				if not source: source = 0.0
				converted = True
			
			# To string	
			elif dtype == "str":
				if source: source = "true"
				if not source: source = "false"
				converted = True
		
		# From string
		if stype == "str":
		
			# To unicode
			if dtype == "unicode":
				source = unicode(source)
				converted = True
				
			# To boolean
			if dtype == "bool":
				if source.lower() == "true": 
					source = True
				else:
					source = False  # It's either absolutely true or it's always false
				
				converted = True
				
			# To integer
			if dtype == "int":
				try:
					source = int(source)
					converted = True
				except:
					raise TypeConversionError (u"{} value {} cannot be converted to {}".format(stype, source, dtype))
					
			# To float
			if dtype == "float":
				try:
					source = float(source)
					converted = True
				except:
					raise TypeConversionError (u"{} value {} cannot be converted to {}".format(stype, source, dtype))
			
		# From unicode to string
		if stype == "unicode" and dtype == "str":
			source = str(source)
			converted = True	
			
		# From integer to float
		if stype == "int" and dtype == "float":
			source = float(source)
			converted = True
		
		# From float to integer
		if stype == "float" and dtype == "int":
			source = int(round(source))
			converted = True	
		
		if not converted:
			raise TypeConversionError (u"Unable to convert source {} to type {}".format(stype, dtype))
	
	except Exception as e:
		e.args += (u"{} to {}".format(stype, dtype),)
		raise CalcsException (kExceptionOutputPrefix + ex.stack_trace(e))
		
	return source




















