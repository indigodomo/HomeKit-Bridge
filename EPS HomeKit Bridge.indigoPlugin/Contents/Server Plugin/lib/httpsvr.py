#! /usr/bin/env python
# -*- coding: utf-8 -*-


# httpsvr - HTTP server
#
# Copyright (c) 2018 ColoradoFourWheeler / EPS
#

import indigo
import linecache # exception reporting
import sys # exception reporting
import logging # logging
import ext

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
import threading
from urlparse import urlparse, parse_qs
import base64

factory = None

class httpServer:	
	#
	# Initialize the  class
	#
	def __init__(self, factoryref):
		global factory
		
		self.logger = logging.getLogger ("Plugin.http")
		factory = factoryref
		self.httpd = None
		self.stopped = False
		#self.startServer(8558)
		
	def run (self, port, username = None, password = None):
		self.myThread = threading.Thread(target=self.startServer, args=[port])
		self.myThread.daemon = True
		self.myThread.start()
		
	def stop (self):
		self.logger.debug ("Stopping HTTP server")
		self.httpd.shutdown
		#self.httpd.socket.close() # not really needed, if enabled it will cause an error because for some reason the HTTP will try to start again but will crash because the socket is closed
		self.httpd = None
		self.myThread.paused = True
		self.stopped = True
		
	def startServer (self, port, username = None, password = None):
		try:
			if self.stopped: return # It can try starting again after we stopped, causing an error on the except below
			
			port = int(port)
			
			if username is None: 
				self.authKey = ""
			else:
				self.authKey = base64.b64encode("api:api")
				
			# Single Threaded
			#self.httpd = MyHTTPServer(("", port), AuthHandler)
			
			# Multi Threaded
			self.httpd = ThreadedHTTPServer(('', port), AuthHandler)
			self.httpd.serve_forever()

		except Exception as e:
			self.logger.error (ext.getException(e))
			self.logger.error("Unable to open port {} for HTTP Server".format(str(port)))
			self.httpd = None
			
		else:
			self.httpd.timeout = 1.0
			self.httpd.setKey(self.authKey)
			
	def runConcurrentThread (self):
		try:
			return
			if not self.httpd is None: self.httpd.handle_request()
		except:
			# We don't care right now
			pass

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""


class MyHTTPServer(HTTPServer):

    def setKey(self, authKey):
        self.authKey = authKey
        
        
class AuthHandler(BaseHTTPRequestHandler):
	global factory
	logger = logging.getLogger("Plugin.httphandler")
	
	def do_POST(self):
		client_host, client_port = self.client_address
		self.logger.debug("AuthHandler: POST from %s:%s to %s" % (str(client_host), str(client_port), self.path))

		self.send_response(200)
		self.send_header("Content-type", "text/html")
		self.end_headers()

	def do_GETxxx(self):
		self.send_response(200)
		self.send_header("Content-type", "text/html")
		self.end_headers()
		
		self.wfile.write("<html>\n<head><title>C4W EPS Web</title></head>\n<body>")
		self.wfile.write("\n<p>Basic Authentication Required</p>")
		self.wfile.write("\n</body>\n</html>\n")

	def do_GET(self):
		global factory
		
		client_host, client_port = self.client_address
		self.logger.threaddebug("HTTP Handler: GET from %s:%s for %s" % (str(client_host), str(client_port), self.path))
		
		self.send_response(200)
		
		try:
			request = urlparse(self.path)
			query = parse_qs(request.query)
			
			type, content = factory.plug.onReceivedHTTPGETRequest (request, query)
			
			self.send_header("Content-type", type)
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
			self.send_header("Content-type", "text/html")
			
			self.wfile.write("<html>\n<head><title>C4W EPS Web</title></head>\n<body>")
			self.wfile.write("\n<p>Invalid request</p>")
			self.wfile.write("\n</body>\n</html>\n")
			
			return
				
		self.end_headers()
		
		self.wfile.write (content)
		
		return
		
		# Legacy below
		
		self.send_response(200)
		self.send_header("Content-type", "text/html")
		self.end_headers()

		auth_header = self.headers.getheader('Authorization')
		
		# Unable to work this from any browser, so for now:
		auth_header = ('Basic ' + self.server.authKey)

		if auth_header == None:
			self.logger.debug("HTTP Handler: Request has no Authorization header")
			self.wfile.write("<html>\n<head><title>C4W EPS Web</title></head>\n<body>")
			self.wfile.write("\n<p>Basic Authentication Required</p>")
			self.wfile.write("\n</body>\n</html>\n")

		elif auth_header == ('Basic ' + self.server.authKey):
			self.logger.debug(u"HTTP Handler: Request has correct Authorization header")
			self.wfile.write("<html>\n<head><title>C4W EPS Web</title></head>\n<body>")
			request = urlparse(self.path)
			query = parse_qs(request.query)

			# Raise request handler
			factory.plug.onReceivedHTTPGETRequest (request, query)
				
			if request.path == "/setvar":
				query = parse_qs(request.query)
				for key in query:
					self.logger.debug(u"AuthHandler: setting variable httpd_%s to %s" % (key, query[key][0]))
					updateVar("httpd_"+key, query[key][0], indigo.activePlugin.pluginPrefs["folderId"])
					self.wfile.write("\n<p>Updated variable %s</p>" % key)

				indigo.activePlugin.triggerCheck()

			else:
				self.logger.debug(u"HTTP Handler: Unknown request: %s" % self.request)

			self.wfile.write("\n</body>\n</html>\n")

		else:
			self.logger.debug(u"HTTP Handler: Request with invalid Authorization header")
			self.wfile.write("<html>\n<head><title>C4W EPS Web</title></head>\n<body>")
			self.wfile.write("\n<p>Invalid Authentication</p>")
			self.wfile.write("\n</body>\n</html>\n")
            
            
                    