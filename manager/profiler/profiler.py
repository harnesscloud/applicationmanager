#!/usr/bin/env python

from manager.application.search_space import VariableMapper
from manager.profiler.algorithms import SimulatedAnnealing, DirectedSimulatedAnnealing
from manager.state import State
from manager.executor import Executor

import sys, os, json, traceback

class Profiler:
	StateID = 0
	def __init__(self, application, version, parameters = {}):
		self.application = application
		self.strategy    = None
		self.version     = version
		self.version_indexes = map(lambda x: int(x), version.split("."))
		
		#print self.version_indexes
		self.variables 	 = sorted(self.application.get_Resource_Vars(self.version_indexes))
		
		self.parameters = parameters
		self.data        = None
		
		self.mapper = VariableMapper(self.application.getResourceVariableMap(self.version_indexes))
		
		self.strategy = DirectedSimulatedAnnealing(self.execute_application, len(self.variables), VariableMapper.Interval[0], VariableMapper.Interval[1])
		data = self.restore()
		if data == [] and self.parameters != {}:
			#to init state
			self.save_state()
		
	def restore(self):
		print "Restoring Profile."
		data = State.get_data(self.version, self.StateID)	
		q = False		
		for inputsize in data:
			try:
				algdata = inputsize["Algorithm"]
			except:		
					
				inputsize = {
					"ResourceVariables" : self.variables,
					"InputParameters" : self.parameters,
					"Algorithm" : {}
				}
				State.checkpoint(self.version, self.StateID, data)
				break
			if algdata != None and algdata != []:
				
				if inputsize["InputParameters"] == self.parameters:
					q = True
					self.strategy.update_state(algdata)
					#if profiling with the input size was finished go to the next one
					if not self.strategy.stop_condition():
						break
		if not q:
			return []
		return data			
		
	def run(self):
		print "Profiling version [", self.version, "]",
		self.restore()
		if self.strategy.stop_condition():
			print "... already done."
			return
		print "..."
		while not self.strategy.stop_condition():
			try:				
				ret = self.strategy.run_step()
			except:
				traceback.print_exc()
				print 'An exception/exit signal occurred. Exiting'
				raise Exception("Exit")
				break
			self.save_state()
			
			print "Return code : ", 0 if ret is 0 else 1, "(0 - stop condition was met)"
			if ret is 0:
				print "Profiling Done. "
				break
		
			
		
	def save_state(self):
		print "Save state to file."
		data = State.get_data(self.version, self.StateID)	
		algdata = self.strategy.get_state()
		info = {
				"ResourceVariables" : self.variables,
				"InputParameters" : self.parameters,
				"Algorithm"   : algdata
				}
	
		q = False
		for inputsize in data:
			if inputsize["InputParameters"] == self.parameters:
				inputsize.update(info)
				q = True
		if not q:
			data.append(info)
			
		State.checkpoint(self.version, self.StateID, data)
		
		
	def execute_application(self, x):
		#print "m = ", self.mapper
		mapped_variables = {}
		for i in range(len(x)):
			mapped_variables[self.variables[i]] = x[i]
		variables =  self.mapper.denormalize(mapped_variables)
		print self.variables
		print variables
		result = Executor.execute_on_configuration(self.application, self.version_indexes, self.variables, variables, self.parameters)
		#execute application should return the variables, cost and time of execution and feedback based on monitoring
		return result #(success, variables, cost, execution_time, gradient, utilisation)
					

	def get_explored_solutions(self):
		data = State.get_data(self.version, self.StateID)
		
		if data in [None, []]:
			return self.variables, None
			
		solutions = []
		
		for info in data:			
			solutions.append({"Input" : info["InputParameters"], "Configurations" : info["Algorithm"]["solutions"]})
			
		return self.variables, solutions
		
		

