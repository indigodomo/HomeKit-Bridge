"""C4W's core plugin libary."""

__version__ 	= "1.0.0"

__modname__		= "C4W Core Plugin Library"
__author__ 		= "ColoradoFourWheeler"
__copyright__ 	= "Copyright 2018, ColoradoFourWheeler & EPS"
__credits__ 	= ["ColoradoFourWheeler"]
__license__ 	= "GPL"
__maintainer__ 	= "ColoradoFourWheeler"
__email__ 		= "Indigo Forums"
__status__ 		= "Production"

# System loads
import os
import glob
import indigo
import importlib

# Import the generic plugin factory
from ifactory import ifactory

# Read all files from the plugin folder and import them for reference in the plugin
from plugin import hkfactory
