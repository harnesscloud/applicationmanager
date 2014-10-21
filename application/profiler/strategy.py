#!/usr/bin/env python

from application.core.context.parameters import VariableModel
from application.provisioner.resources import ReservationManager
from application.provisioner.simulator import SimulatorManager
import math, random, copy
from scipy.optimize import anneal
from threading import Lock
from datetime import datetime
import time
import json
from multiprocessing import Pool#, Queue

from Queue import Queue


class BaseStrategy:
    
    def __init__(self, implementation, save_to_log = False):
		"""
            Base Constructor.
            * Keeps the variable model for resources and for implementation arguments
            
        """
		if save_to_log:
			self.listed = False
		else: 
			self.listed = True
		self.EXPERIMENTS = []      
		self.implementation = implementation
		
		print "\n == In BaseStrategy =="
		
		self.generate_resource_model()
		print "\n ~ ResModel ~"
		str(self.ResModel)
		
		print "\n ~ Mapping for variables ~"
		print self.ResVarMap, "\n"
		
		self.generate_arguments_model()
		print "\n ~ ArgModel ~"
		str(self.ArgModel)
			
		print "\n ~ Order ~"
		self.VarOrder = self.ResModel.get_keys()
		print self.VarOrder
		print "\n =====\n"
        
    
    def generate_resource_model(self):
        """
            Build resource variables map
        """
        self.ResModel = VariableModel(self.implementation.Resources.getVariableMap())  
        self.ResVarMap = self.implementation.Resources.get_keys()
        
        
    def generate_arguments_model(self):
        """
            Build arguments variables map
        """
        arg_var = []
        for arg in self.implementation.Arguments:
            arg_var.extend(arg.getVariableMap())
            
        self.ArgModel = VariableModel(arg_var)
        
        
        
           
    def execute(self, values, lock = None):
		"""
			Implementation deployment and execution
				* acquire CONF
				* deploy implementation on CONF
				* execute application on CONF
				* release CONF
		"""
		#lock and make local copies of the variables and work on the copies - useful when executed on threads
		#print values
		variables = self.assign_keys(values)
			
		#denormalize values
		variables = self.ResModel.denormalize(variables)

		#setup application arguments
		args = self.ArgModel.denormalize(self.ArgModel.nrandomize())
		#print "\nApplication arguments :", args
		data = {}	
		implementation = copy.deepcopy(self.implementation)
		#data["Index"] = len(self.EXPERIMENTS)
		data["Configuration"] = copy.deepcopy(variables)
		data["Arguments"] = args
		print "~~~ Execution Resources and Args ~~~"
		print data["Configuration"]
		print data["Arguments"]
		if self.listed:
			already_done = None
			
			for exp in self.EXPERIMENTS:
				if exp["Configuration"] == variables and exp["Arguments"] == args:
					already_done = self.goodness(exp["Results"]["ExeTime"], exp["Results"]["TotalCost"])
					break                
			if already_done != None:
				return already_done 
		"""
			Get the configuration structure from the implementation
		"""
		configuration, roles = implementation.Resources.get_configuration(variables)
		
		""""
			Reserving resources
		"""
		reservation = ReservationManager.acquire_resources(configuration)
		if reservation == None:
			print "Experiment failed."
			return 0 
		"""
			Add roles to the acquired machines
		"""
		for i in range(len(reservation["Resources"])):
			reservation["Resources"][i]["Role"] = roles[i]
		
		print "\n ~ Acquired Resources ~"
		print reservation["Resources"]
		
		""""
			Execute Implementation
		"""
		variables.update(args)
		#get manifest special variables, environment variables
		variables.update(implementation.Resources.get_special_variables(reservation["Resources"]))
		
		reservation["Variables"] = variables
		"Deploy implementation"
		implementation.deploy(reservation)
		
		"Execute implementation"
		execution_time, utilization_data = implementation.execute(reservation)
		total_cost = execution_time * reservation["Cost"]
		
		
		"""
			Releasing resources
		"""
		reservation = ReservationManager.release_resources(reservation["ResID"])
		
		"Save output and update experiments list"
		data["Results"] = {"ExeTime" : execution_time, "TotalCost" : total_cost} 
		data["RuntimeData"] = utilization_data
		if self.listed:
			print "Add experiment to the Queue."
			self.EXPERIMENTS.append(data)
		else:
			#save to logs
			fname = str(datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H:%M:%S'))
			print "Save to log : ", fname
			f = open("/home/aiordache/exps/exp-%s" % fname, "w")
			f.write(unicode(json.dumps(data, ensure_ascii=False)))
			f.close()
		print "Done experiment."
		"Returns evaluation of the execution based on cost and execution time"
		return self.goodness(data["Results"]["ExeTime"], data["Results"]["TotalCost"])
			
        
    def explore(self):
        raise NotImplementedError, "Must be implemented in the derived class - based on different exploration strategies"

    
    def goodness(self, performance, cost):
        """
            Evaluation of implementation execution
        """
        quality = cost * performance
        "Less is better"
        return quality
    

    def order_values(self, variables):
        ordered_values = []
        for i in range(len(self.VarOrder)):
            key = self.VarOrder[i]
            ordered_values.append(variables[key])
                    
        return ordered_values

    def assign_keys(self, values):
        """Isolate variable names of their values such that we apply mathematical methods on vectors and remap them back later 
        to the names"""
        variables = {}
        for i in range(len(self.VarOrder)):
            key = self.VarOrder[i]
            variables[key] = values[i] 
        
        return variables

    def test_additional_configurations(self, configurations):
        
        self.EXPERIMENTS = []
        print "Additional experiments running..."
        for conf in configurations:
            print "Run configuration ", conf
            #normalize and order variables
            variables = self.order_values(self.ResModel.normalize(conf))
            self.simulate(variables) #self.execute
        
        return self.EXPERIMENTS
 
class BruteForce(BaseStrategy):

    def explore(self):
		combs = []
		resource_model = VariableModel(self.implementation.Resources.getVariableMap())  
        ##fork the search   
		conf = resource_model.lower_bound_values()
		keys = conf.keys()
		indices = []
		for i in range(len(keys)):
			indices.append(resource_model.get_values_range(keys[i]) - 1)
		from utils.generator import Combinations

	 	c = Combinations(indices)
		pool = Pool(processes = 10)
		queue = Queue()
		configurations = []
		lock = Lock()
		for comb in c.generate():
			conf = {}
			#rebuild conf
			for i in range(len(comb)):
				conf[keys[i]] = resource_model.get_value_at_index(keys[i], comb[i])
			#evaluate configuration
			#print "conf: ", conf
			variables = self.order_values(self.ResModel.normalize(conf))
			#put the configuration to be tested in the queue
			queue.put(conf)
			configurations.append(variables)
	
		print "~~~ Configurations ~~~~~"
		while not queue.empty():
		    print queue.get()

		print"\nStarting process pool."
		#pass the bag of configurations to the pool of workers
		pool.map(self.execute, configurations)
		pool.close() # no more tasks
		pool.join() 
		print "BruteForce strategy finished!"
		return self.EXPERIMENTS


class SimulatedAnnealingStrategy(BaseStrategy):
        
    def explore(self):
        print "\n ~ Running Simulated Annealing ~ "
        #print "x0 :",x_start, "\n"
        result = anneal(
                        self.execute,# self.simulate
                        [0]*len(self.VarOrder), 
                        lower = float(self.ResModel.Interval[0]), 
                        upper = float(self.ResModel.Interval[1]),
                        schedule = "boltzmann", dwell = 10)#"fast") #default = fast   
        
        
        print "\n\nStrategy Done!\n"
        print "Num iterations :", len(self.EXPERIMENTS)
        # print solution
        #print 'Return Code: ', result
        #print self.EXPERIMENTS
        
        return self.EXPERIMENTS
  
        
    def algorithm(self, function, x = [], lower = 0.0, upper = 1.0):
        """
        # Simulated Annealing
        ##Step 1: Initialize - Start with a random initial placement. Initialize a very high "temperature".
        ##Step 2: Move - Perturb the placement through a defined move.
        ##Step 3: Calculate score - calculate the change in the score due to the move made.
        ##Step 4: Choose - Depending on the change in score, accept or reject the move. The probability of acceptance depending on 
        ##the current "temperature". 
        ##Step 5: Update and repeat-Update the temperature value by lowering the temperature. Go back to Step 2.
        # 
        """
        # Number of trials per cycle
        num_trials = 7
        # Number of accepted solutions
        num_accepted_solutions = 0.0
        # Initial temperature
        curTemp = -1.0/math.log(0.7)
        # Final temperature
        finTemp = -1.0/math.log(0.001)
        # Fractional reduction every cycle
        decrease_ratio = (0.001 / curTemp) ** (1.0 / (num_trials - 1.0))  
        num_accepted_solutions = num_accepted_solutions + 1.0
        # DeltaE Average
        DeltaE_avg = None
        cur_solution = x
        result = function(cur_solution)
        
        while (curTemp > finTemp):
            
            print 'Cycle Temperature: ' + str(curTemp)
            print 'Target Temperature: ' + str(finTemp)
            print 'Decrease Ratio: ' + str(decrease_ratio)
            for j in range(num_trials):
                """
                    Generate new configuration  with a close specification to the current one 
                """
                new_solution = map(lambda x: max(min(x  + random.random() - 0.5, upper), lower), cur_solution)
                
                result_new_solution = function(new_solution) 
                DeltaE = abs(result_new_solution - result)
                
                # on the first iteration
                if (DeltaE_avg == None): DeltaE_avg = DeltaE
                
                if (result_new_solution > result):
                    # objective function is worse
                    # generate probability of acceptance
                    p = math.exp(-DeltaE/(DeltaE_avg * curTemp))
                    # determine whether to accept worse point
                    if (random.random()< p):
                        # accept the worse solution
                        accept = True
                    else:
                        # don't accept the worse solution
                        accept = False
                else:
                    # objective function is lower, automatically accept
                    accept = True
                    
                if (accept==True):
                    result = result_new_solution
                    # increment number of accepted solutions
                    num_accepted_solutions = num_accepted_solutions + 1.0
                    # update DeltaE_avg
                    DeltaE_avg = (DeltaE_avg * (num_accepted_solutions-1.0) +  DeltaE) / num_accepted_solutions
           
            curTemp = decrease_ratio * curTemp


class UniformSearch(BaseStrategy):

    def explore(self):
        self.EXPERIMENTS = []
        combs = []
        resource_model = VariableModel(self.implementation.Resources.getVariableMap())  
        ##fork the search   
        conf = resource_model.lower_bound_values()
        keys = sorted(conf.keys())
        indices = []
        
        #print "keys : ", keys
        for i in range(len(keys)):
            indices.append(resource_model.get_values_range(keys[i]))
        
        from utils.generator import Combinations
        
        c = Combinations(indices)
        configurations = []
        for comb in c.generate():
            conf = {}
            #rebuild conf
            for i in range(len(comb)):
                conf[keys[i]] = resource_model.get_value_at_index(keys[i], comb[i])
            #evaluate configuration
            #print "Conf: ", conf
            variables = self.order_values(self.ResModel.normalize(conf))
            #print "Normalized vals :", variables
            #put the configuration to be tested in the queue
            configurations.append(variables)
            self.execute(variables)
        
        print "Num of experiments : ", len(self.EXPERIMENTS)
        print "Uniform search strategy finished!"
        return self.EXPERIMENTS



class UtilizationBasedStrategy(BaseStrategy):

	def explore(self):
		LowerThreshold = 50
		UpperThreshold = 70
		
		
		self.EXPERIMENTS = []
		configurations = []
		print "\n ~ Running usage based ~"
		resource_model = VariableModel(self.implementation.Resources.getVariableMap())
		x_start = resource_model.nrandomize()
		
		i = 0 
		#simulating a queue using a list
		next_experiments = [resource_model.denormalize(x_start)]
		tested_configurations = []
		while len(next_experiments) > 0:
			#run exp
			conf = next_experiments[0]
			variables = self.order_values(resource_model.normalize(conf))
			#remove from queue
			next_experiments = next_experiments[1:]
			#execute
			result = self.execute(variables)
			#if result == float("inf"):
			#	#comb not possible -- skip it
			#	if len(tested_configurations) == 0:
			#		next_experiments.append(resource_model.denormalize(resource_model.nrandomize()))
			#	continue
				
			tested_configurations.append(conf)
			#print conf
			usage_data = self.get_usage_ratio(self.EXPERIMENTS[-1])

			#great! check usage and generate new exps#	
			#self.ResVarMap contains the mapping "%master_core" : Cores, "%master_ram" : RAM

			mapping = self.ResVarMap
			
			#print "\nUsage :", usage_data, "\n"

			model = copy.deepcopy(conf)
			for key in model:
				#if key in usage_data.keys():
					#print "raise...."
					usage = usage_data[mapping[key]]["maxAvg"]
					ratio = usage_data[mapping[key]]["maxRatio"]
					if usage < LowerThreshold and ratio > 50:
						#decrease this parameter if bound not reached
						next_value = resource_model.get_previous_value_from(key, model[key])
						if next_value != None:
							model[key] = next_value
							#generate exp with only this decreased 
							model_decreased = copy.deepcopy(conf)
							model_decreased[key] = next_value
							if not((model_decreased in tested_configurations) or (model_decreased in next_experiments)):
								next_experiments.append(model_decreased)
							
							
					if usage > UpperThreshold and ratio > 50:
						#increase this parameter if bound not reached
						next_value = resource_model.get_next_value_from(key, model[key])
						if next_value != None:
							model[key] = next_value
							#generate exp with only this increased 
							model_increased = copy.deepcopy(conf)
							model_increased[key] = next_value
							if not((model_increased in tested_configurations) or (model_increased in next_experiments)):
								next_experiments.append(model_increased)		
					
			if model != conf and (not ((model in next_experiments) or (model in tested_configurations))):
				#append exp with all parameters modified if it is different from previous
				next_experiments.append(model)


		#print "\nTested confs :\n"
		#for e in tested_configurations:
			#print e
		#print "\n"
			
				
		print "Num of experiments : ", len(self.EXPERIMENTS)
		return self.EXPERIMENTS
		
		
	def get_usage_ratio(self, experiment):
		
		result = {}
		if len(experiment["RuntimeData"]["Usage"]) > 0:
			data = {}
			for key in simplejson.loads(experiment["RuntimeData"]["Usage"][0].replace("'","\"")).keys():
				data[key] = []
				result[key] = 0 

			for use in experiment["RuntimeData"]["Usage"]:
				u = simplejson.loads(use.replace("'","\""))
				for k in u:
					data[k].append(int(u[k]))
			"""
				data is now like {"Cores" : [1,2,3,4], "RAM" : [1,2,3]} instead of ["'Cores' : 1, 'RAM' : 1", "'Cores' : 2, 'RAM' : 2", "'Cores' : 3, 'RAM' : 3" ...]
			"""
			#print data
			## process data - usage ratio
			highest = {}
			for key in data:
				highest[key] = heapq.nlargest(len(data[key])/5, set(data[key]))
			
			"""
			print data
			print "\nLEN : ", len(data[data.keys()[0]])
			print "HIGH and SMALL"
			print highest
			"""
			
			for key in result:
				result[key] = {
					"maxAvg" : self.get_prop_mean(highest[key], data[key])
				}
				maxCount =  self.get_longest_consecutive(highest[key][-1], 100, data[key])
				result[key]["maxRatio"] =  (maxCount * 100) / len(data[key])
				
			#print result
		return  result

	def get_prop_mean(self, vals, alist):
		subsum = []
		subcount = []
		for x in vals:
			#print x
			c = alist.count(x)
			subsum.append(x * c)
			subcount.append(c)
		
		return sum(subsum)/sum(subcount)

	def get_longest_consecutive(self, minim, maxim, a_list):
		n 		= len(a_list)
		i 		= 0
		j		= 0
		max_len = 1
		current_len = 1
		while(j < n):
			if a_list[j] >= minim and a_list[j] <= maxim:
				current_len = j - i + 1
			else:
				if current_len > max_len:
					max_len = current_len
				current_len = 1
				i = j + 1
			j = j+ 1
		if current_len > max_len:
			max_len = current_len

		return max_len
    
