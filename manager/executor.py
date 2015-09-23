#!/usr/bin/env python
from manager.resources.reservation import ReservationManager
from manager.resources.utilisation import Monitor

from manager.state import CostModel
import sys

class Traces:
	Experiments = None
	@staticmethod
	def load(name):
		import json
		print "Loading trace ..", name
		data = open("../traces/%s-traces.json"%name.split("-")[0]).read()
		js = json.loads(data)
		Traces.Experiments = js["Experiments"]
		if len(Traces.Experiments) < 0:
			Graph.plot_exps(Traces.Experiments[0]["exps"])

	@staticmethod
	def get_experiment(param, conf_variables):
		e = None
		for dataset in Traces.Experiments:
			if dataset["parameters"] == param:
				for exp in dataset["exps"]:
					if exp["conf"] == conf_variables:
						e = exp
						break
				break
		return e
		
class Executor:
	
	@staticmethod
	def execute_on_configuration(application, version_indexes, variables_order,  conf_variables, parameters):
		## FOR TEST ONLY - uses experiment traces instead of executing
		#success, conf_variables, cost, execution_time, gradient, utilisation = Executor._get_execution_trace(application, version_indexes, variables_order,  conf_variables, parameters)
		success, conf_variables, cost, execution_time, gradient, utilisation = Executor._execute_on_configuration(application, version_indexes, variables_order,  conf_variables, parameters)
		return  (success, conf_variables, cost, execution_time, gradient, utilisation)


	@staticmethod
	def _process_feedback(monitor, application, version_indexes, configuration, variables_order, conf_variables, feedback = None):
		#stop monitoring
		if not feedback :
			#stop monitor here
			recommendation, utilisation = monitor.stop()
		else:
			recommendation = monitor.calculate_direction(feedback["utilisation"])
			utilisation = feedback
		bottlenecks = monitor.get_bottleneck(utilisation)
			
		#regroup and assign recommendation to variables
		variable_keys = application.getResourceVar2KeyMap(version_indexes)
		#print "Resource Variable Map :", variable_keys
		# -1 to decrease, 0 to don't know and +1 to increase the value (default 0)
		rd = {}
		bn = {}
		for key in variables_order:
			rd[key] = 0
			bn[key] = False
				
		for rec in recommendation:
			for c in configuration:
				if rec == c["Address"]:
					group_variables = application.getGroupIDVars(version_indexes, c["GroupID"])
					for v in group_variables:
						if variable_keys[v] in recommendation[rec].keys():
							rd[v] += recommendation[rec][variable_keys[v]]
							bn[v] = bn[v] or bottlenecks[rec][variable_keys[v]]
		
		#order values and zip to dict
		gradient = dict(zip(variables_order, [rd[v] for v in variables_order]))
		bottlenecks = dict(zip(variables_order, [bn[v] for v in variables_order]))
		
		return (utilisation, gradient, bottlenecks)

	@staticmethod
	def _get_execution_trace(application, version_indexes, variables_order, conf_variables, parameters):
		if not Traces.Experiments:
			Traces.load(application.Name)
		
		exp = Traces.get_experiment(parameters, conf_variables)
		if exp == None:
			raise Exception("Missing experiment : %s on %s" % (str(parameters), str(conf_variables)))

		#print "Run on ", conf_variables
		roles, configuration = application.getResourceConfiguration(version_indexes, conf_variables)
		
		feedback = exp["utilisation"]
		for i in range(len(configuration)):
			configuration[i]["Address"] = feedback["resources"][i]["Address"]
			configuration[i]["Role"]    = feedback["resources"][i]["Role"]
		
		#print "\nExecuting application on the following resources :\n", configuration, "\n"
		utilisation, gradient, bottlenecks =  Executor._process_feedback(Monitor(configuration), application, version_indexes, configuration, variables_order, conf_variables, feedback)
		
		execution_time = exp["et"] / 60.
		if exp["success"]["Success"]:
			#if execution was successful then there is no bottleneck
			bottlenecks = dict(zip(bottlenecks.keys(),[False] * len(bottlenecks.keys())))
		
		success = {"Success"  : exp["success"]["Success"], "Bottleneck" : bottlenecks}
		
		cost =  execution_time * CostModel.calculate(configuration)
		print conf_variables, "-------->","Cost: ",cost, " ET :", execution_time, bottlenecks
		
		
		return (success, conf_variables, cost, execution_time, gradient, utilisation) 
	
	@staticmethod
	def _execute_on_configuration(application, version_indexes, variables_order,  conf_variables, parameters):
		#get resource configuration
		print "Run on ", conf_variables
		roles, configuration = application.getResourceConfiguration(version_indexes, conf_variables)
		#print roles
		#print configuration
		reservation = ReservationManager.reserve(configuration)
		#print "Reservation ready :", reservation
		
		for i in range(len(configuration)):
			configuration[i]["Address"] = reservation["Addresses"][i]
			configuration[i]["Role"]    = roles[i]
		
		all_variables = {}
		all_variables.update(parameters)
		all_variables.update(conf_variables)
		
		#start monitoring
		monitor = Monitor(configuration)
		monitor.run()
		
		print "\nExecuting application on the following resources :\n", configuration, "\n"

		#execute application
		successful_execution, execution_time = application.execute(version_indexes, configuration[:], all_variables)
		#this will stop also the monitor
		utilisation, gradient, bottlenecks = self.process_feedback(monitor, application, version_indexes, configuration, variables_order, conf_variables, None)
		
		success = {"Success"  : successful_execution, "Bottleneck" : bottlenecks}
		
		#release configuration
		ReservationManager.release(reservation["ReservationID"])
		cost =  execution_time * CostModel.calculate(configuration)
		print "Cost: ",cost, " ET :", execution_time
		
		return  (success, conf_variables, cost, execution_time, gradient, utilisation)
