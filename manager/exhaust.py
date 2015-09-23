#!/usr/bin/env python
import sys
try:
    from manager.application.structure import Application
except:
	#we assume the package is not installed in the system
	print "Package not installed in the system. Running from current directory."
	import os
	sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname( __file__ ), "..")))
	sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname( __file__ ), "../manager")))

	from manager.application.structure import Application
	

from manager.specification.manifest import ManifestParser
from manager.specification.slo import SLOParser
from manager.executor import *
from manager.application.search_space import VariableMapper

import  subprocess, traceback, json
from threading import Thread

class Controller:
	application = None
	@staticmethod
	def load(slo):
		
		#### LOADING SLOs ####
		Controller.slo = SLOParser.parse(slo)		
		
		Controller.application = ManifestParser.load(Controller.slo.ManifestURL)
		#print application.getVariableMap()		
		Controller.versions = Controller.application.generate_app_versions()
		
	@staticmethod 
	def run():
		for v in Controller.versions:
			Controller.run_version(v)
		print "Bye!"		

	@staticmethod
	def run_version(v):
		version = ".".join(map(lambda s: str(s), v))
		#Controller.application, version, parameters = parameters)
		
		variables_order = sorted(Controller.application.get_Resource_Vars(v))
		
		params = [#{"%arg1": "http://public.rennes.grid5000.fr/~aiordache/harness/apps/rtm/rtm_parameters_medium.txt"}, 
		{"%arg1": "http://public.rennes.grid5000.fr/~aiordache/harness/apps/rtm/rtm_parameters_large.txt"}]
		
		
		m = [4096,  6144, 8192,16384,32768]
		c = map(lambda x: x+1, range(16))
		c = [4,5,6,7,8,9]
		m = [8192,16384, 32768]		
		confs = []
		for i in c:
			for j in m:
				confs.append({"%master_mem": j, "%master_cores": i})
		print confs
	
		
		def launch(app, version, parameters, conf):
			success, conf_variables, cost, execution_time, gradient, utilisation = 	Executor.execute_on_configuration(app, version, ["%master_cores", "%master_mem"], conf, parameters)
			
			f = open("/home/aiordache/exps/%s-%dx%d.log" %(parameters.values()[0].split("_")[-1].split(".")[0], conf["%master_cores"], conf["%master_mem"]), "w")
			f.write(json.dumps({
			"success":success,
			"conf":conf,
			"cost":cost,
			"et":execution_time,
			"gradient":gradient,
			"utilisation":utilisation,
			"parameters":parameters
			}, ensure_ascii=True))
			f.close()
			
		ps = []	
		i = 0
		for p in params:
			for c in confs:
				t = Thread(target=launch, args=(Controller.application,v, p,c))
				t.start()
				ps.append(t)
				i += 1
				if i == 4:
					for x in ps: 
						x.join()
					i = 0
					ps = []
		
		print "Done"
		
			
if __name__ == "__main__":	
	slo_local_test = {
		"SLO": {
			"ManifestURL": "/home/anca/Code/input/rtm-man.json",
			"ExecutionArguments": ["http://public.rennes.grid5000.fr/~aiordache/harness/apps/rtm/rtm_parameters_large.txt"],
			"Objective": {
				"Constraints": [
					"%cost <= 100"
				],
				"Optimize": "%execution_time"
			}
		}
	}
	s = "http://public.rennes.grid5000.fr/~aiordache/harness/apps/rtm/slo.json"
	Controller.load(s)
	Controller.run()

	

