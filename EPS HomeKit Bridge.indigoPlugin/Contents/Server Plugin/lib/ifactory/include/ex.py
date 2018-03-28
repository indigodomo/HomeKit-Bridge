"""exception_handler.py: Python exception handling for Indigo."""

__author__ 		= "ColoradoFourWheeler"
__copyright__ 	= "Copyright 2018, ColoradoFourWheeler & EPS"
__credits__ 	= ["ColoradoFourWheeler"]
__license__ 	= "GPL"
__version__ 	= "1.0.0"
__maintainer__ 	= "ColoradoFourWheeler"
__email__ 		= "Indigo Forums"
__status__ 		= "Production"

# Python Modules
import sys
import logging
import linecache

# Third Party Modules


# Package Modules



def stack_trace (e):
	"""
	Returns the stack trace for a general exception.
	
	Arguments:
	e = Exception
	"""
	
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