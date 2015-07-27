#!/usr/bin/env python

from manager.modeller.model import FunctModel
from manager.utils.math_utils import MathUtils
from manager.modeller.utils import Converter
from manager.state import solution
import numpy, random, copy, time
import matplotlib.pyplot as plt
import math, sys, os, json
import simplejson
from sklearn.cross_validation import cross_val_score, KFold, ShuffleSplit, LeavePLabelOut


class ModellingMethod:	
		
	def __init__(self, solutions, execution_function, variable_mapper, profiling_input):
		#functions to call when running the app on a configuration
		self.app_execution_function_call = execution_function
		self.benchmark_input = profiling_input
		self.variable_mapper = variable_mapper
		#dicts
		self.profiling_solutions = solutions
		#solutions not tested during profiling but discovered during modelling
		#solution objects
		self.additional_solutions = []
		self.training_set = []
		self.failed_set = []
		#dicts
		self.selected_solutions = []
		self.testing_set = []
		#start from linear model
		self.model = FunctModel()
		self.max_evals = 7
		self.iterations = 0
		self.init_steps = 3
		
		self.constraints = {}
		#start the modelling process by seleting a number of optimal/non-optimal configurations to test on the big size input
		self.selected_solutions = self.select_training_configurations()
		self.testing_set = self.selected_solutions[:]
		
		
		
	def update_state(self, params = {}): 
		if params == {}:
			return
		self.max_evals = params["max_evals"]
		self.init_steps = params["init_steps"]
		self.iterations = params["iterations"]
		self.constraints = params["constraints"]
		self.training_set = map(lambda s: solution(s), params["training_set"])
		self.testing_set = params["testing_set"]
		self.additional_solutions = map(lambda s: solution(s), params["additiona_small_input_solutions"])
		self.selected_solutions = params["selected_configurations"]
		self.failed_set = map(lambda s: solution(s), params["failed_set"])
		
		self.model.restore(params["mathematical_model"])
		
		
	def get_state(self):
		
		result = { 
					"max_evals" : self.max_evals, 
					"init_steps": self.init_steps,
					"iterations"  : self.iterations,
					"constraints"  :self.constraints,
					"additiona_small_input_solutions":map(lambda sol: sol.get(), self.additional_solutions),
					"training_set" : map(lambda sol: sol.get(), self.training_set), 
					"testing_set" : self.testing_set,
					"failed_set" : map(lambda sol: sol.get(), self.failed_set),
					"selected_configurations" : self.selected_solutions,
					"mathematical_model" : self.model.save_state()
		}
		if self.constraints == []:
			self.constraints = {}
		return result
		

	def run_step(self):
		#self.check_state()
		if self.stop_condition():
			return 0
			
		print "Running extrapolating step..."		
		conf_to_test = self.testing_set[0]
		
		print "Testing conf:", conf_to_test
		success, var_order, cost, et, direction, monitor = self.app_execution_function_call(conf_to_test)
		print success
		if success["Success"]:
			self.training_set.append(solution({"conf" : conf_to_test, "x" : None, "cost" : cost, "et" : et, "gradient" : direction, "monitor" : monitor, "success" : success["Success"]}))
			self.iterations += 1
		else:
			self.failed_set.append(solution({"conf" : conf_to_test, "x" : None, "cost" : cost, "et" : et, "gradient" : direction, "monitor" : monitor, "success" : success["Success"]}))
			#add new conf to test in solutions
			bottlenecks = success["Bottleneck"]
			
			indexes = filter(lambda i : bottlenecks[i], range(len(bottlenecks)))
			if indexes == []:
				#can't detect the bottleneck from the utilisation 
				print "Unknown failure."
				self.testing_set = self.testing_set[1:]	
				return	
				
			#derive the new configuration
			new_conf = copy.deepcopy(conf_to_test)
			print indexes
			for ind in indexes:
				#store bound in constraints
				self.constraints[var_order[i]] = conf_to_test[var_order[i]]
				#get a higher value for the bottleneck resource
				new_conf[var_order[i]] = self.mapper.get_next_value_from(var_order[i], conf_to_test[var_order[i]])
				
				if new_conf[var_order[i]] == None:
					raise Exception("Field %s has no valid value for extrapolation." %(var_order[i]))
					return
					
			pf =  map(lambda x:x["conf"], self.profiling_solutions)
			small_input = self.benchmark_input
			#if new_conf hasn't been discovered during profiling we must test the small input size 
			if not (new_conf in pf):
				#run the small input on the new configuration
				success, var_order, cost, et, direction, monitor = self.app_execution_function_call(new_conf, small_input)
				print success
				if success["Success"]:
					self.additional_solutions.append(solution({"conf" : conf_to_test, "x" : None, "cost" : cost, "et" : et, "gradient" : direction, "monitor" : monitor, "success" : success["Success"]}))
				else:
					print "Invalid solution for benchmarking input. Remove the current tested solution."
					self.testing_set = self.testing_set[1:]					
					return
				
			
			#store the new configuration to be tested
			self.testing_set[0] = new_conf 
			return
			
		self.generate_model()
			
		#remove configuration from the testing set
		self.testing_set = self.testing_set[1:]
		print "Failed : ", len(self.failed_set)	
			
	def stop_condition(self):
		return self.iterations >= self.max_evals or (self.iterations > 0 and self.testing_set == [])
		
	def generate_model(self):
		#need at least 2 points to create a model
		if self.iterations < 2:
			return
		
		train_confs =  map(lambda sol:sol.conf, self.training_set)
		xtrain, ytrain = [], [] 
		for c in train_confs:
			#add small input execution time from the profiling
			all_benchmarked_confs = map(lambda z : (z["conf"], z["et"]), self.profiling_solutions)
			#add et from confs discovered during modelling and not during profiling
			all_benchmarked_confs.extend(map(lambda z : (z.conf, z.et), self.additional_solutions))
			
			the_one = filter(lambda z: c == z[0], all_benchmarked_confs)[0]
			#z = tuple of (conf, et)
			xtrain.append(the_one[1])
			
			#now append the big size input et
			the_one = filter(lambda sol:c == sol.conf, self.training_set)[0]				
			ytrain.append(the_one.et)
			
		print xtrain,  ytrain
		self.model.fit(xtrain, ytrain)
		
		#scores.append(self.model.score(xtest, ytest))
	
	def select_training_configurations(self):
		#1/3 cost pareto optimal 
		#1/3 et pareto optimal
		#1/3 non-pareto
		
		num = self.max_evals
		pex = self.get_pareto_experiments(self.profiling_solutions)
		exps = []
		if len(pex) < 2 * (num/3):
			exps.extend(pex[:])
		else:
			exps.extend(pex[:num/3])
			exps.extend(pex[num/3:])
			
		while len(exps) < num and len(exps) <= len(self.profiling_solutions):
			left_exps = filter(lambda e: not(e["conf"] in map(lambda x:x["conf"], exps)), self.profiling_solutions)
			e = left_exps[random.randint(0,len(left_exps ) - 1)]
			#print map(lambda x:x["Configuration"], pex)
			#print e["Configuration"]
			if not(e["conf"] in map(lambda x:x["conf"], exps)):
				exps.append(e)
		print "done selecting test configurations : "
		return map(lambda e:e["conf"], exps)
		
	def get_pareto_experiments(self, exps):
		"""
			Select experiments with the optimal cost-et trade-off        
		"""
		cost = map(lambda x: x["cost"], exps)
		et = map(lambda x: x["et"], exps)

		pcost, pet = MathUtils.pareto_frontier(cost, et)
		print "Pareto cost:", pcost
		print "Pareto et  :", pet
		print "Total Number experiments :", len(exps)
		print "Number Pareto experiments :", len(pcost)
		pex = []

		for exp in exps:
			for i in range(len(pcost)):
				if exp["cost"] == pcost[i] and exp["et"] == pet[i]:
					pex.append(exp)	
		return pex
		
	def get_model(self):
		if self.constraints == []:
			self.constraints = {}
		if self.model.F == None:
			#fit a model based on data gathered so far
			self.generate_model()
		return (self.model, self.constraints)
	
	def get_all_solutions(self):
		
		small_input_exps	= self.profiling_solutions + map(lambda sol: sol.get(), self.additional_solutions)
		big_input_exps  	=  map(lambda sol: sol.get(), self.training_set)
		
		return (small_input_exps, big_input_exps)
