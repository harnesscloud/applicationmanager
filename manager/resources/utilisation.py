#!/usr/bin/env python
import httplib2, json, sys, os
import threading, subprocess, time
from manager.resources.connection import RemoteConnection

class UtilizationDataThread(threading.Thread):

    def __init__(self, function = None, addresses = [], interval = 0.5):
        threading.Thread.__init__(self)
        self.Enabled = True 
        self.function = function
        self.addresses = addresses
        self.interval = interval
        self.data = []
        
        print "Recording usage for ", self.addresses

    def run(self):
		if self.data == None:
			self.Enabled = False
			return

		#try:
		while self.Enabled:
			time.sleep(self.interval)
			self.data.append(self.function(self.addresses))
		#except:
		#    self.Enabled = False


    def stop(self):
        self.Enabled = False
        self.join()
        
        return self.data
        


class Monitor:
	
	UNDERUSED = 60.0
	OVERUSED  = 90.0 
	
	def __init__(self, resources):
		self.resources = resources
		self.retriever = None
		self.data = []
		
	def __get_utilization(self, addresses):
		info = {}
		for address in addresses:
			d, response = httplib2.Http().request('http://%s:9292' % address,
						 'POST',
						 None,
						 headers={'Content-Type': 'application/json'})
			#print response
			info[address] = eval(response)
		return info
		
	def run(self):
		conn = RemoteConnection()
		#start monitoring	
		
		#redirect to null 
		backup = sys.stdout
		sys.stdout = open(os.devnull, 'w')
		
		addrs = []
		for machine in self.resources:
			cmd = "wget http://public.rennes.grid5000.fr/~aiordache/harness/monitor;chmod +x monitor;nohup python monitor < /dev/null &> /dev/null &"
			if machine["Type"] in ["Machine", "VM"]:
				conn.run(machine["Address"], cmd)
				addrs.append(machine["Address"])
		
		time.sleep(2)
		self.retriever = UtilizationDataThread(function = self.__get_utilization, addresses = addrs)
		
		self.retriever.start()
		#restore stdout
		sys.stdout = backup
		#done

	
	def process_usage(self, data = []):
		result = {}
		
		if not self.retriever:
			if not data:
				return {}
		
		if not data:
			usage = self.retriever.data[:]
		else:
			usage = data
		
		addresses = []
		for addr in self.resources:
			if addr["Type"] in ["Machine", "VM"]:
				addresses.append(addr["Address"])
				
		if usage == []:
			return {}
		keys = usage[0].values()[0].keys()
		print "keys monitored:", keys
		for addr in addresses:
			result[addr] = {}
			for key in keys:
				result[addr][key] = []
			
		for record in usage:
			for addr in record:
				for attr in record[addr]:
					result[addr][attr].append(record[addr][attr])
				
		#print "\n~~~~~~~~~~~~~~ Monitoring result ~~~~~~~~~~~~~",
		#for addr in result:
		#	print addr
		#	for k in result[addr]:
		#		print  k, result[addr][k],		
	
		def __smaller(vals, v):
			i = 0
			while i < len(vals) and vals[i] <= v:
				i += 1
			return i
		
		
		recommendation = {}
		#get if resource needs to be increased or not
		for addr in result:
			recommendation[addr] = {}
			for attr in result[addr]:
				 vals = result[addr][attr][:]
				 vals = sorted(vals)
				 if __smaller(vals, self.UNDERUSED) * 100.0 / len(vals) > 50:
					 recommendation[addr][attr] = -1
				 elif (len(vals) - __smaller(vals, self.OVERUSED)) * 100.0 / len(vals) > 50:
					 recommendation[addr][attr] = +1
				 else:
					 recommendation[addr][attr] = 0
		print "\nDirection :", recommendation
		
		"""
		monitor = {
		"utilisation": 
		{
					"10.158.4.49": {"Cores": [0.5, 0.6, 0.6, 0.7], "Swap": [0.0, 0.08, 0.08, 0.08, 0.08], "Memory": [4.4, 94.43, 94.46, 94.54, 94.58, 94.61, 94.64, 94.69]},
					"10.158.4.50": {"Cores": [14.1, 14.0, 14.0, 14.0], "Swap": [0.0, 0.0, 0.0, 0.0, 0.0], "Memory": [4.37, 22.15, 57.36, 57.37, 57.36, 57.37, 57.43]}
		}, 
		"resources": 
		[
					{"Attributes": {"Cores": 7, "Memory": 2048}, "Type": "Machine", "GroupID": "id0", "Role": "MASTER", "Address": "10.158.4.49"}, 
					{"Attributes": {"Cores": 1, "Memory": 2048}, "Type": "Machine", "GroupID": "id1", "Role": "SLAVE", "Address": "10.158.4.50"}
		]
	}
		"""
		return recommendation, {"resources" : self.resources, "utilisation" : result}
		
	def stop(self):
		if self.retriever:
			data = self.retriever.stop()
			return self.process_usage(data)
			
			
	def get_bottleneck(self, data):
		"""
		data = {
			"utilisation": 
			{
						"10.158.4.49": {"Cores": [0.5, 0.6, 0.6, 0.7], "Swap": [0.0, 0.08, 0.08, 0.08, 0.08], "Memory": [4.4, 94.43, 94.46, 94.54, 94.58, 94.61, 94.64, 94.69]},
						"10.158.4.50": {"Cores": [14.1, 14.0, 14.0, 14.0], "Swap": [0.0, 0.0, 0.0, 0.0, 0.0], "Memory": [4.37, 22.15, 57.36, 57.37, 57.36, 57.37, 57.43]}
			}, 
			"resources": 
			[
						{"Attributes": {"Cores": 7, "Memory": 2048}, "Type": "Machine", "GroupID": "id0", "Role": "MASTER", "Address": "10.158.4.49"}, 
						{"Attributes": {"Cores": 1, "Memory": 2048}, "Type": "Machine", "GroupID": "id1", "Role": "SLAVE", "Address": "10.158.4.50"}
			]
		}
		"""
		botneck = {}
		#get if resource needs to be increased or not
		for addr in data["utilisation"]:
			res_attrs = filter(lambda x: x["Address"] == addr, data["resources"])[0]["Attributes"].keys()
			
			botneck[addr] = {}
			for attr in res_attrs:#data["utilisation"][addr]:
				vals = data["utilisation"][addr][attr][:]

				i = len(vals) - 1
				counter = 0
				while i > 0 and vals[i] > 90:
					counter += 1
					i -= 1
				#if the last 10 utilisation values > 90% ====> it may be a bottleneck causing failure
				if counter > 10 or (len(vals) < 10 and counter > 3):
					botneck[addr][attr] = True
				else:
					botneck[addr][attr] = False
		return botneck
	
				
#####   TEST PURPOSE  #######
if __name__ == "__main__":
	print "Testing Monitor"
	conf = [
				{'Attributes': {'Cores': 7, 'Memory': 8192}, 'Type': 'Machine', 'GroupID': 'id0', 'Role': 'MASTER', 'Address': '10.158.0.79'}, 
				{'Attributes': {'Cores': 7, 'Memory': 6144}, 'Type': 'Machine', 'GroupID': 'id1', 'Role': 'SLAVE', 'Address': '10.158.0.80'}
			]
	mon = Monitor(conf)
	
	usage = {
		"utilisation": 
		{
					"10.158.4.49": {"Cores": [0.5, 0.6, 0.6, 0.7], "Swap": [0.0, 0.08, 0.08, 0.08, 0.08], "Memory": [4.4, 94.43, 94.46, 94.54, 94.58, 94.61, 94.64, 94.69]},
					"10.158.4.50": {"Cores": [14.1, 14.0, 14.0, 14.0], "Swap": [0.0, 0.0, 0.0, 0.0, 0.0], "Memory": [4.37, 22.15, 57.36, 57.37, 57.36, 57.37, 57.43]}
		}, 
		"resources": 
		[
					{"Attributes": {"Cores": 7, "Memory": 2048}, "Type": "Machine", "GroupID": "id0", "Role": "MASTER", "Address": "10.158.4.49"}, 
					{"Attributes": {"Cores": 1, "Memory": 2048}, "Type": "Machine", "GroupID": "id1", "Role": "SLAVE", "Address": "10.158.4.50"}
		]
	}
	
	print mon.get_bottleneck(usage)
	
	sys.exit()
	mon.run()
	
	time.sleep(10)
	
	data = mon.stop()
	
	print "\n Recommendation :", mon.process_usage(data)
		
############################
