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

class CostModel:

    #cpu_cost = 0.04 #eurocents per Ghz
    c_ram = 0.0186323 #eurocents per GB
    c_cores = 0.0396801 #eurocents per core
    C = 0.0417027

    @staticmethod
    def vm_cost_per_hour(attrs = {}):
        """
            Currently, only the num of cores and the RAM are considered
        """
        cost = 0
        for attr in attrs:
            if attr.upper() == "RAM" :
                cost = cost + CostModel.c_ram * attrs[attr] / 1024.0
            elif attr.upper() == "CORES" :
                cost = cost + CostModel.c_cores * attrs[attr]

        cost =  cost + CostModel.C
        return cost

    @staticmethod
    def conf_cost_per_hour(machines = []):
        total_cost = 0
        for vm in machines:
            total_cost = total_cost  + CostModel.vm_cost_per_hour(vm)
        return total_cost



conn = CloudClient(sys.argv[1])

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
		if action == "/prepareReservation":
			print "Prepare Reservation : ", data
			extended_list = []
			for gr in data["Resources"]:
				del gr["GroupID"]
				num = gr["NumInstances"]
				del gr["NumInstances"]
				for i in range(num):
					extended_list.append(copy.deepcopy(gr))  
			response = {
			   "ConfigID"  : str(uuid.uuid1()),
			   "Cost"      : 0.003,
			   "Resources" : extended_list            
			}
			reservations[response["ConfigID"]] = extended_list
			print "Response : ", response
			
		elif action == "/getResourceTypes":
			response = {}
			
		elif action == "/getMonitoringInfo":
			response = {}
		elif action == "/checkReservation":
			rid = data["ResID"]
			#retrieve machine state
			ready = True
			
			for r in reservations[rid]:
				ready = (ready and (conn.get_state(id_vm = r["Attributes"]["ID"])["STATE"] == "RUNNING")) 
			response = {"Ready" : ready}
			if ready:
				response["Addresses"] = map(lambda r : r["Attributes"]["IP"], reservations[rid])
				print "Check Reservation : Ready"

		elif action == "/createReservation":
			print "Create Reservation : ", data
			for r in reservations[data["ConfigID"]]:    
				r["Attributes"]["name"] = (str(uuid.uuid1())).replace("-", "")
				print "Creating VM with :", r["Attributes"]
				result = conn.create_vm(r["Attributes"])

				r["Attributes"]["ID"] = result["ID"]
				r["Attributes"]["IP"] = result["IP"]
				
			response = { "ResID": data["ConfigID"] }
			print response

		elif action == "/releaseReservation":
			print "Release reservation : ",reservations[data["ResID"]]
			for r in reservations[data["ResID"]]:
				conn.destroy_vm(r["Attributes"]["ID"])
			del reservations[data["ResID"]]
			response = {}
		elif action == "/reset":
			print "Reset."
			for r in reservations.values():
				for c in r:
					conn.destroy_vm(c["Attributes"]["ID"])
			reservations = {}
			
		#print "response : ", response
		response = {"result" : response}
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
    
    start_application_manager()
    
