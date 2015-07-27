#!/usr/bin/env python

from twisted.web import server, resource
from twisted.internet import reactor

import sys, uuid
import simplejson
from pprint import pprint
import time

import os, traceback
import httplib2, copy

class CloudClient:
    def __init__(self, url):
        self.conn = httplib2.Http()
        self.url = "http://%s:9898" % url

    def _request(self, content):
        data, response = self.conn.request(self.url , 'POST',
                          simplejson.dumps(content),
                          headers={'Content-Type': 'application/json'})
        try:
            response = simplejson.loads(response)
        except:
            print traceback.print_exc()
            return response
        return response["result"]

    def create_vm(self, properties):
        #print "requesting vm with", properties
        data = {"Action" : "create_vm"}
        data.update(properties)
        return self._request(data)

    def destroy_vm(self, id_vm= None):
        data = {"Action" : "destroy_vm", "ID" : id_vm}
        self._request(data)
        

    def get_state(self, id_vm = None):
        data = {"Action" : "get_state", "ID" : id_vm}
        r = self._request(data)
        return r


frontend = open("frontend").read().strip()
conn = CloudClient(frontend)

reservations = {}

class Server(resource.Resource):

    ACTIONS = []
    
    isLeaf = True

    def http_handler(self, request):
		"""
			Handles user requests.
			:request: Dictionary with the request parameters 
		"""
		global conn, reservations

		#print request.__dict__
		action = request.path
		data = eval(request.content.read())
		action = action.replace("/method", "")
		#print "action =", action
		#print "data :", data, "\n"
		response = {}
		if action == "/createReservation":
			print "Create Reservation : ", data
			extended_list = []
			for gr in data["Allocation"]:
				if gr["Type"] == "Machine":
					if "NumInstances" in gr.keys():
						num = gr["NumInstances"]
					else:
						num = 1		
					for i in range(num):
						extended_list.append(copy.deepcopy(gr["Attributes"]))  
				
			rid = str(uuid.uuid1())
			reservations[rid] = extended_list
			
			for r in reservations[rid]:    
				r["name"] = (str(uuid.uuid1())).replace("-", "")
				print "Creating VM with :", r
				result = conn.create_vm(r)
				r["ID"] = result["ID"]
				r["IP"] = result["IP"]
			
			response  = {"ReservationID" :[rid] }
			
		elif action == "/checkReservation":
			rid = data["ReservationID"][0]
			#retrieve machine state
			ready = True
			
			for r in reservations[rid]:
				ready = (ready and (conn.get_state(id_vm = r["ID"])["STATE"] == "RUNNING")) 
			response = {"Instances" : { rid : {"Ready" : ready}}}
			if ready:
				response["Instances"][rid]["Address"] = map(lambda r : r["IP"], reservations[rid])
				print "Check Reservation : Ready"

		elif action == "/releaseReservation":
			rid = data["ReservationID"][0]
			print "Release reservation : ",reservations[rid]
			for r in reservations[rid]:
				conn.destroy_vm(r["ID"])
			del reservations[rid]
			response = {}
			
		elif action == "/reset":
			print "Reset."
			for r in reservations.values():
				for c in r:
					conn.destroy_vm(c["ID"])
			reservations = {}
			
		#print "Response : ", response
		return simplejson.dumps(response)
            
    def render_POST(self, request):
        return self.http_handler(request)

    def render_GET(self, request):
        return self.http_handler(request)


def start_application_manager(port = 5558):
    # Create and start a thread pool,
    service = Server()
    site = server.Site(service)
    reactor.listenTCP(port, site)
    print "reactor started .... listening on", port
    reactor.run()


if __name__ == '__main__':
	try:
		port = int(sys.argv[1])
	except:
		port = 5558
	start_application_manager(port)
    
