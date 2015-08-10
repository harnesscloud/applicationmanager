#!/usr/bin/env python
from manager.resources.reservation import ReservationManager
from manager.resources.utilisation import Monitor

from manager.state import CostModel

class Executor:
	@staticmethod
	def execute_on_configuration(application, version_indexes, variables_order,  conf_variables, parameters):
		#get resource configuration
		print "Run on ", conf_variables
		configuration, roles = application.getResourceConfiguration(version_indexes, conf_variables)
		#print roles
		#print configuration
		monitor = Monitor()
		reservation = ReservationManager.reserve(configuration, monitor.target)
		
		print "Reservation ready :", reservation
		
		try:
			for i in range(len(configuration)):
				configuration[i]["Address"] = reservation["Addresses"][i]
				configuration[i]["Role"]    = roles[i]
			
			all_variables = {}
			all_variables.update(parameters)
			all_variables.update(conf_variables)
			
			#start monitoring
			monitor.setup(configuration, reservation['ReservationID'])
			# monitor.run()
			
			print "\nExecuting application on the following resources :\n", configuration, "\n"

			#execute application
			successful_execution, execution_time = application.execute(version_indexes, configuration[:], all_variables)
			
			
			recommendation, utilisation = monitor.get_monitoing()
			#stop monitoring
			# recommendation, utilisation = monitor.stop()
			
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
				
							
			#print "Recomandare :", rd
			
			gradient = []
			for v in conf_variables:
				gradient.append(rd[v])
			
			success = {"Success"  : successful_execution, "Bottleneck" : [ bn[v] for v in conf_variables]}
			
			#release configuration
			ReservationManager.release(reservation["ReservationID"])
			cost =  execution_time * CostModel.calculate(configuration)
			print "Cost: ",cost, " ET :", execution_time
			
			return  (success, conf_variables, cost, execution_time, gradient, utilisation)

		except Exception, e:
			ReservationManager.release(reservation['ReservationID'])
			raise e
