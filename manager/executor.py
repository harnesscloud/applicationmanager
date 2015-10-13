#!/usr/bin/env python
from manager.resources.reservation import ReservationManager
from manager.resources.utilisation import Monitor

from manager.state import CostModel
import sys

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
            #recommendation, utilisation = monitor.stop()
            recommendation, utilisation = monitor.get_monitoing()
        else:
            recommendation = monitor.get_recommendation(feedback["utilisation"])
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
                    group_variables = application.getGroupIDVars(version_indexes, c["Group"])
                    for v in group_variables:
                        if variable_keys[v] in recommendation[rec].keys():
                            rd[v] += recommendation[rec][variable_keys[v]]
                            bn[v] = bn[v] or bottlenecks[rec][variable_keys[v]]
        #order values and zip to dict
        gradient = dict(zip(variables_order, [rd[v] for v in variables_order]))
        bottlenecks = dict(zip(variables_order, [bn[v] for v in variables_order]))
        return (utilisation, gradient, bottlenecks)

    @staticmethod
    def _execute_on_configuration(application, version_indexes, variables_order,  conf_variables, parameters):
        #get resource configuration
        print "Run on ", conf_variables
        roles, configuration, constraints = application.getResourceConfiguration(version_indexes, conf_variables)
        #print roles
        print configuration

        monitor = Monitor()
        reservation = ReservationManager.reserve(configuration, constraints, monitor.target)
        #print "Reservation ready :", reservation

        for i in range(len(configuration)):
            configuration[i]["Address"] = reservation["Addresses"][i]
            configuration[i]["Role"]    = roles[i]

        all_variables = {}
        all_variables.update(parameters)
        all_variables.update(conf_variables)

        monitor.setup(configuration, reservation['ReservationID'])
        print "\nExecuting application on the following resources :\n", configuration, "\n"

        #execute application
        successful_execution, execution_time = application.execute(version_indexes, configuration[:], all_variables)
        #this will stop also the monitor
        utilisation, gradient, bottlenecks = Executor._process_feedback(monitor, application, version_indexes, configuration, variables_order, conf_variables, None)
        success = {"Success"  : successful_execution, "Bottleneck" : bottlenecks}
        #release configuration
        ReservationManager.release(reservation["ReservationID"])
        cost_unit = ReservationManager.get_cost(configuration, constraints)
        cost =  execution_time * cost_unit #CostModel.calculate(configuration)
        print "Cost: ",cost, " ET :", execution_time
        print "Done!"
        return  (success, conf_variables, cost, execution_time, gradient, utilisation)
