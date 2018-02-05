# lib.dtutil - Some useful date/time utilities
#
# Copyright (c) 2018 ColoradoFourWheeler / EPS
#

import indigo

import datetime
from datetime import date, timedelta
import time

import ext

#
# Like .NET dateadd, takes days, house, minutes or seconds as t
# If dates are sent as string they must be Y-m-d H:M:S
#		
def dateAdd (t, n, d):
	try:
		if type(d) is str:
			if d == "":
				d = "2000-01-01 00:00:00"
			d = datetime.datetime.strptime(d, "%Y-%m-%d %H:%M:%S") 
		
	except:
		indigo.server.log ("DateDiff ERROR: Got an error converting strings to datetimes, make sure they are in the format of Y-m-d H:M:S!", isError = True)
		raise
		return
	
	if n > -1:
		if t.lower() == "days":
			ret = d + datetime.timedelta(0,float( ((n * 60) * 60) * 24 ))

		if t.lower() == "hours":
			ret = d + datetime.timedelta(0,float( (n * 60) * 60 ))

		if t.lower() == "minutes":
			ret = d + datetime.timedelta(0,float(n * 60))
			
		if t.lower() == "seconds":
			ret = d + datetime.timedelta(0,float(n))
	else:
		n = n * -1
		
		if t.lower() == "days": ret = d - timedelta(days=n)
		if t.lower() == "hours": ret = d - timedelta(hours=n)
		if t.lower() == "minutes": ret = d - timedelta(minutes=n)
		if t.lower() == "seconds": ret = d - timedelta(seconds=n)
				
	return ret
	
#
# Like .NET datediff, takes days, house, minutes or seconds as t
# If dates are sent as string they must be Y-m-d H:M:S
# If d1 is earlier than d2 then a negative is returned, else a postitive is returned
#
def dateDiff (t, d1, d2):
	try:
		if type(d1) is str:
			if d1 == "":
				d1 = "2000-01-01 00:00:00"
			d1 = datetime.datetime.strptime(d1, "%Y-%m-%d %H:%M:%S") 
		if type(d2) is str:
			if d2 == "":
				d2 = "2000-01-01 00:00:00"
			d2 = datetime.datetime.strptime(d2, "%Y-%m-%d %H:%M:%S") 

	except:
		log ("DateDiff ERROR: Got an error converting strings to datetimes, make sure they are in the format of Y-m-d H:M:S!")
		raise
		return

	try:
		sum = time.mktime(d1.timetuple()) - time.mktime(d2.timetuple())
		if sum == 0:
			return 0

		if t.lower() == "days":
			ret = sum / 86400

		if t.lower() == "hours":
			ret = (sum / 86400) * 24

		if t.lower() == "minutes":
			ret = ((sum / 86400) * 24) * 60

		if t.lower() == "seconds":
			ret = (((sum / 86400) * 24) * 60) * 60

		return ret
	
	except:
		indigo.server.log ("DateDiff ERROR: Got an error converting to " + t)
		raise
		return
		
#
# Convert string date/time from one format to another
#
def dateStringFormat (value, oldFormat, newFormat):
	try:
		oldDate = datetime.datetime.strptime (value, oldFormat)
		return oldDate.strftime (newFormat)
	
	except Exception as e:
		self.logger.error (ext.getException(e))	