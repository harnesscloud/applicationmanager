#!/usr/bin/env local
from manager.utils.math_utils import MathUtils
from manager.executor import Executor
from manager.profiler.profiler import Profiler
from manager.modeller.extrapolator import Extrapolator
from manager.application.search_space import VariableMapper

from manager.state import State, CostModel

import copy

class SLOEnforcer:
	StateID = 2
	def __init__(self, application, slo, versions, models):
		self.application = application
		self.slo = slo
		self.versions = versions
		self.models = models
		
		self.Data = {}
		
		self.restore()
		
	def restore(self):
		if self.Data == {}:
			#load state
			for v in self.versions:
				version = ".".join(map(lambda s: str(s), v))
				data = State.get_data(version, self.StateID)
				if data in [None, {}, []]:
					continue					
				self.Data[version] = data[0]
				
			
	def save_state(self):
		print "Save state to file...",
		for v in self.versions:
			version = ".".join(map(lambda s: str(s), v))
			#don't care, replace it
			#data = State.get_data(self.version, self.StateID)		
			info = {
					"Input" : self.application.getExecutionParameters(self.slo.ExecutionArguments),
					"Data"   : self.Data[version]
					}
			#print "info to save :", info
			#State.checkpoint(version, self.StateID, [info])
		print "Done"
		
	def execute_application(self):
		parameters = self.application.getExecutionParameters(self.slo.ExecutionArguments)
		#predict performance on untested configurations
		if self.Data == {}:
			info = self._predict_performance(parameters)
			self.Data = copy.deepcopy(info)
			self.save_state()
			
		info = self.Data
			
		best_confs = self._select_best(info)
		
		def minimize_objective(target, best_confs):
			minim = None
			best_version = None
			best_conf = None
			for key in best_confs.keys():
				best = best_confs[key]
				if best == None:
					continue
				if minim == None:
					minim = best[target]
					best_version = key
					best_conf = best
					
				elif minim > best[target]:
						minim = best[target]
						best_version = key
						best_conf = best
			if best_conf == None:
				return None	
			return (best_version, best_conf)
			
		#get (version, configuration) with the bestest objective
		if "%execution_time" in self.slo.Objective.Optimize:
			bestest = minimize_objective("et", best_confs)
		else:
			bestest = minimize_objective("cost", best_confs)
		if bestest == None:
			print "Failed finding a configuration to satisfy objective!"
			raise Exception("No known configuration validating the slo.")
			return
		
		variable_order = bestest[1]["conf"].keys()
		configuration = bestest[1]["conf"]
		
		print "Best Version :", bestest[0]
		print "Best Configuration :", bestest[1]
		
		success, conf, cost, execution_time, gradient, utilisation = Executor.execute_on_configuration(self.application, map(lambda x: int(x), bestest[0].split(".")), variable_order,  configuration, parameters)
		print "Done"
		return (execution_time - bestest[1]["et"], cost - bestest[1]["cost"])
		

	def _predict_performance(self, parameters):
		info = {}
		for v in self.versions:
			version = ".".join(map(lambda s: str(s), v))
			
			variables, solutions_identified_in_profiling = Profiler(self.application, version).get_explored_solutions()
			modeller = Extrapolator(self.application, version, variables, solutions_identified_in_profiling, parameters)
			print "\n\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n\n"
			solutions_benchmark_input, solutions_current_input = modeller.get_explored_solutions()
			
			info[version] = {
								"InputProfiled" : map(lambda x: { "conf" : x["conf"], "et" : x["et"], "tested"  :True }, solutions_benchmark_input),
								"InputCurrent"  :  map(lambda x: { "conf" : x["conf"], "et" : x["et"], "tested"  :True }, solutions_current_input),
								"Variable_order" : variables
							}
							
			if len(info[version]["InputProfiled"]) > len(info[version]["InputCurrent"]):
				#get the mapper for the variables
				mapper = VariableMapper(self.application.getResourceVariableMap(v))
			
				#predict the performance of the untested profiled configurations with the current input
				confs_tested = map(lambda x:x["conf"], info[version]["InputCurrent"])
				benchmarked = map(lambda x:x["conf"], info[version]["InputProfiled"])
				not_tested_confs = filter(lambda x:not(x in confs_tested), benchmarked)
				
				#use model to predict the cost and et of the confs not tested with the current input
				model, constraints = self.models[version]
				
				#filter the configs not tested based on constraints to reduce the confs space
				not_tested_confs = filter(lambda z : all(map(lambda zz : True if not(zz in constraints.keys()) else mapper.isvalid(zz, z[zz], constraints[zz]), z.keys())), not_tested_confs)
				
				x = []
				for i in range(len(not_tested_confs)):
					conf = not_tested_confs[i]
					#predict
					index = benchmarked.index(conf) 
					x.append(info[version]["InputProfiled"][index]["et"])
				
				print "x = ",x
				fx = model.predict(x)
				
				predicted_confs = map(lambda i : {"conf" : not_tested_confs[i], "et" : fx[i], "tested" : False}, range(len(fx)) )
				
				info[version]["InputCurrent"].extend(predicted_confs)
					
		return info
				
			
	def _select_best(self, info):
		#search for the configurations validating the slo constraints
		valid = {}
		all_confs = {}
		pareto = {}
		best_choice = {}
		for version in self.versions:
			v  = ".".join(map(lambda s: str(s), version))
			data = info[v]["InputCurrent"][:]
			
			print data
			
			#update the cost
			for c in data:
				conf, _  = self.application.getResourceConfiguration(version, c["conf"])
				print conf
				
				cost = CostModel.calculate(conf)
				#update the dict
				c["cost"] = cost
				
		
			all_confs[v] = data[:]
			
			pareto[v] = self._get_pareto_experiments(data)[:]
			valid[v] = self._select_valid_configurations(pareto[v])
			if len(valid[v]) > 0:
				best_choice[v]  = valid[v][0]
			else:
				best_choice[v] = None
		
		return best_choice
			
			
	def _select_valid_configurations(self, exps):
		
		if "%execution_time" in self.slo.Objective.Optimize:
			pareto_exp = filter(lambda x: self.slo.Objective.validate(cost = x["cost"]), exps)
			
			#sort pareto frontier based on execution time and select the first
			sorted_exps = sorted(pareto_exp, key=lambda x:x["cost"])
			 
		else:
			pareto_exp = filter(lambda x: self.slo.Objective.validate(execution_time = x["et"]), exps)
			#sort pareto frontier based on cost and select the first
			sorted_exps = sorted(pareto_exp, key=lambda x:x["et"])
		
		return sorted_exps
			
		
	def _get_pareto_experiments(self, exps):
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
		
    
