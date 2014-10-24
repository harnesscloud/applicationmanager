#!/usr/bin/env python

try:
    from application.core.application import Application
except:
	#we assume the package is not installed in the system
	print "Package not installed in the system. Running from current directory."
	import sys, os
	sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname( __file__ ), "..")))
	sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname( __file__ ), "../application")))

	from application.core.application import Application
	
	
	
from application.core.context.parser import ManifestParser
from application.model import Model
from application.slo import User, Objectives, SLOParser
from application.selection import SLOEnforcer

import random, subprocess


class Controller:
	
	@staticmethod
	def run(slo):
		#### LOADING SLOs ####
		slo = SLOParser.parse(slo)
		#print "User SLO :", Objectives.EXECUTION_TIME in User.SLO.Objective.Constraints
		print "---  SLOs  -------------------------"
		print slo.Objective
		print "---  Performance Model  ------------"
		User.Objectives = slo.Objective
		perf_model_path = slo.PerformanceModel
		print perf_model_path
		######################
		application = ManifestParser.load(slo.ManifestUrl)
		
		
		#Load Performance Model
		modeller = Model(application)
		
		
		if perf_model_path is None: 
			print "No Performance Model Found."
			"""
				BUILD PERFORMANCE MODEL
			"""		
			model = modeller.create_model()
			
		else:
			import json
			with open(perf_model_path) as f:
				model = json.load(f)["PerformanceModel"]
				f.close()
				
		
		"""
			PROCESS SLOs
		"""
		manager = SLOEnforcer(application)
		manager.slo_based_execution(User.Objectives, model)		
		print "\nTHE END!"





#########################################################
########		TEST ONLY                        ########
#########################################################

slo = {
    "SLO": {
        "ManifestUrl": "http://public.rennes.grid5000.fr/~aiordache/harness/apps/rtm/manifest.json", #"/home/anca/Desktop/Code/test/manifest.json",
        "PerformanceModel" : "/home/aiordache/AM/test/model.json",#"/home/anca/Desktop/Code/test/model.json",
        "ExecutionArgs": [
            {
                "Value": 500
            }
        ],
        "Objective": {
            "Constraints": [
                "%budget <= 100"
            ],
            "Optimization": "%execution_time"
        }
    }
}


slo_local_test = {
    "SLO": {
        "ManifestUrl": "/home/anca/Desktop/Code/test/manifest.json",
        "PerformanceModel" : "/home/anca/Desktop/Code/test/model.json",
        "ExecutionArgs": [
            {
                "Value": 500
            }
        ],
        "Objective": {
            "Constraints": [
                "%budget <= 100"
            ],
            "Optimization": "%execution_time"
        }
    }
}


Controller.run(slo)#_local_test)
	


