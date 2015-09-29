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

from manager.profiler.profiler import Profiler
from manager.modeller.extrapolator import Extrapolator
from manager.selection import SLOEnforcer
from manager.application.search_space import VariableMapper
from manager.state import State
import  subprocess, traceback
from config import config_parser

class Controller:
	application = None
	@staticmethod
	def load(slo):
		
		#### LOADING SLOs ####
		Controller.slo = SLOParser.parse(slo)		
		
		Controller.application = ManifestParser.load(Controller.slo.ManifestURL)
		#print Controller.application.getVariableMap()		
		Controller.versions = Controller.application.generate_app_versions()
		
	@staticmethod 
	def run():
		done, models = Controller.model_application()
		print "Modelling done?",done
		if done:			
			#application model has been built; enforce slo
			enforcer = SLOEnforcer(Controller.application, Controller.slo, Controller.versions, models)
			print "Enforce objective ..."
			result = enforcer.execute_application()
			return result
		print "Bye!"		
	@staticmethod 
	def model_application():
		#we can run the modelling in parallel for each version
		q = True 
		models = {}
		for v in Controller.versions:
			done, model = Controller.model_version(v)
			models[".".join(map(lambda s: str(s), v))] = model
			q = q and done 
		
		return q, models
			
	@staticmethod
	def model_version(v):
		version = ".".join(map(lambda s: str(s), v))
		#LOOK FOR PROFILE DATA
		profile_dir = os.path.abspath(os.path.join(os.path.dirname( __file__ ), "../profiles"))
		data_file = "%s/%s-%s.pf" % (profile_dir, Controller.application.Name, version)
		
		State.load(version, data_file)
		
		current_state = State.get_current_state(version)
	
		if current_state == 0:
			print "Profiling state."
			#profiling with static input phase
			#get the first small input size to profile with
			parameters = VariableMapper(Controller.application.getParameterVariableMap()).lower_bound_values()
			#start profiler to create a model
			Profiler.StateID = current_state
			profiler = Profiler(Controller.application, version, parameters = parameters)
			try:
				profiler.run()
			except:
				traceback.print_exc()
				print 'Profiler interrupted. Exiting'
				return False, None
			State.change_state(version)
			current_state = State.get_current_state(version)
			State.checkpoint(version, current_state)
			
		#get the input size from the SLO for which to make prediction
		input_size = Controller.application.getExecutionParameters(Controller.slo.ExecutionArguments)
		modeller = None
		if current_state >= 1:
			print "Modelling state."
			#profiling variable input
			#modelling state - use function to predict
			Extrapolator.StateID = current_state
			variables, solutions_identified_in_profiling, constraints = Profiler(Controller.application, version).get_explored_solutions()
			
			print constraints
			#print map(lambda c:(c["cost"], c["et"]), solutions_identified_in_profiling[0]["Configurations"])
			for c in solutions_identified_in_profiling[0]["Configurations"]:
				print c["conf"], c["success"], c["et"],
				if c["success"]:
					print c["cost"]
				else:
					print "0"
				
			modeller = Extrapolator(Controller.application, version, variables, solutions_identified_in_profiling, input_size)
			try:
				modeller.run()
			except:
				traceback.print_exc()
				print 'Modeller interrupted. Exiting'
				return False, None
			State.change_state(version)
			current_state = State.get_current_state(version)
			
		print "Current state", current_state
		State.save(version)
		#retrieve the model - tuple (function,constraints)
		model = modeller.get_model() 
		return True, model
			
if __name__ == "__main__":	
	
	if len(sys.argv) > 1:
		s = sys.argv[1]
	else:
		s = config_parser.get("main", "slo_url")
		
	Controller.load(s)
	Controller.run()


