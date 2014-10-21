#!/usr/bin/env python

from twisted.web import server, resource
from twisted.internet import reactor

from application.controller import Controller
from application.core.context.parser import ManifestParser
from thread import start_new_thread
import sys
import simplejson
from pprint import pprint

class Server(resource.Resource):

	ACTIONS = ['ProfileApplication', 'ExecuteApplication', 'AnalyseApplication', 'TerminateApplication', 'GetResourceTypes', 'experiments']
	
	isLeaf = True
	def __init__(self):
		#self.port = 8887
		'''
                                TESTING PURPOSE; TO BE REMOVED WHEN FINISHED
                                
                                - resets the infrastructure- not to restart the infra each time we start the app manager
                '''
                from application.provisioner.connections import CrossResourceSchedulerConnection
                infra = CrossResourceSchedulerConnection(url = "http://localhost:5558")
                infra.reset()
                del infra

                '''
                        DONE
                '''


	def http_handler(self, request):
		"""
			Handles user requests.
			:request: Dictionary with the request parameters 
		"""
		#print request.__dict__
		action = request.postpath[0]
		
		if not (action in Server.ACTIONS):
			return
		
		if action == "ExecuteApplication":
			slo = eval(request.content.read())
			start_new_thread(Controller.run, (slo,))
		elif action == "ProfileApplication":
			pass
		elif action == "AnalyseApplication":
			pass
		elif action == "TerminateApplication":
			pass
		elif action == "experiments": 
			response = {"result" : Controller.get_experiments()}
			pprint(response)
			return simplejson.dumps(response)
			
		response = "<Response>OK</Response>"
			
		print "response : " + response
		return response


	def render_POST(self, request):
		return self.http_handler(request)

	def render_GET(self, request):
		return self.http_handler(request)


def start_application_manager(port = 8887):
	
	service = Server()
	site = server.Site(service)
	
	reactor.listenTCP(port, site)
	print "reactor started .... listening on", port
	reactor.run()


if __name__ == '__main__':
	
	#data = ManifestParser(manifest)
	data = ManifestParser().load({})
	print data
	
	print '\nENDEXE'
	
	
	
	if len(sys.argv) > 1:
		start_application_manager(int(sys.argv[1]))
	else:
		raise Exception("Port not specified")
		sys.exit(1)
	
