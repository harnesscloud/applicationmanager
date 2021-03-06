#!/usr/bin/env python
from pprint import pprint
import random
from manager.application.base import Base

class Variable(Base):
	accepted_params = [ 
			{ 
			'name' : 'Value',
			'is_array' : False,
			'is_required' : False
			},
			{ 
			'name' : 'Range',
			'is_array' : True,
			'is_required' : False
			}, 
			{ 
			'name' : 'Values',
			'is_array' : True,
			'is_required' : False
			}
			]
	def __init__(self, hashmap={}):
		self.VarID = None
		self.Range = None
		self.Values = None
		self.Value = None

		if 'Var' in hashmap and hashmap['Var'].startswith(self.VAR_SIGN):
			self.VarID = str(hashmap['Var'])
			
		if self.VarID:
			if not("Range" in hashmap or "Values" in hashmap):
				raise Exception("Missing Range/Values to variable %s." % self.VarID)
		elif not ("Value" in hashmap):
			raise Exception("Missing Value/Var in field: \n %s" % str(hashmap))

		Base.__init__(self, hashmap)
			
				
	def print_str(self, index = 0):
		sep = "  :  " 
		i = '\n'+('  '* index)
		s = ""
		return " " + str(self.Value) #+ "Value" + sep 
	  
	  

	def getVariableMap(self):
		"""
			Override Base method
		"""
		if not self.VarID:
			return []
		if self.Range:
			interval = self.Range
			discrete_set = False
		elif self.Values: 
			interval = self.Values
			discrete_set = True
		else:
			interval = [self.Value, self.Value]
			discrete_set = False
			
		return [{ self.VarID : interval, "Discrete" : discrete_set}] 


	def get_range_size(self):
		"""
			Retrieves number of possible values the argument may take.
		"""
		if "Range" in self.__dict__:
			return self.Range[-1] - self.Range[0] + 1
		else:
			return len(self.Values) 
		
	def get_value_at_index(self, index):
		"""
			Retrieves arguments value found at index in Values/Range
		"""
		if "Range" in self.__dict__:
			return max(min(self.Range[0] + index, self.Range[-1]), self.Range[0])
		else:
			return self.Values[min(max(index, 0), len(self.Values))] 

	def set_values(self, values):
		"""
			Set arguments value found at index in Values/Range
		"""
		if "Range" in self.__dict__:
			self.Range = values
		else:
			self.Values = list(set(values))  
			  
	def get_id(self):
		return self.VarID
		
        
class VariableMapper:
	'''
		Mapping model for manifest/system variables
	'''
	"All variables are normalized to [0,1] range"
	Interval = [0.0, 1.0]
	def __init__(self, variables):
		'''
		Constructor
		 Mapping discrete variables to continuous ones     
		'''        
		self.vars = {}
		
		for varr in variables:
			
			key = filter(lambda k: k != "Discrete", varr.keys())[0]
			self.vars[key] = {"Continuous" : not(varr["Discrete"]), "Values" : varr[key], "Type" : type(varr[key][0])}
			
			#compute unit
			if self.vars[key]["Continuous"]:
				self.vars[key]["unit"] = (self.Interval[1] - self.Interval[0])/(self.vars[key]["Values"][-1] - self.vars[key]["Values"][0] + 1)
			else:
				self.vars[key]["unit"] = (self.Interval[1] - self.Interval[0])/len(self.vars[key]["Values"])
			
		
	def nrandomize(self, keys = None):
		
		values = {}
		if keys == None:
			keys = self.vars.keys()
		for key in keys:
			values[key] = random.uniform(0, 1)
			 
		return values     
		
		

	def denormalize(self, variables):
		#print "Values to deMap = ", variables
		values = {}
		
		for key in variables:
			variables[key] = max(min(variables[key],self.Interval[1]),self.Interval[0])
		
			#print "Value to Convert =", variables[key]
			increase_rate = round(float(variables[key]) / float(self.vars[key]["unit"]))
			
			if self.vars[key]["Continuous"]:
				values[key] = self.vars[key]["Type"](max(min( self.vars[key]["Values"][0] + increase_rate, self.vars[key]["Values"][-1]),self.vars[key]["Values"][0]))
				
			else:
				index = int(increase_rate)
				values[key] = self.vars[key]["Type"](self.vars[key]["Values"][max(min(index, len(self.vars[key]["Values"]) - 1),0)])
				
		#print "Result :", values
		return values


		
	def normalize(self, variables):
		#print "Map ", variables
		values = {}
		
		for key in variables:
			if self.vars[key]["Continuous"]:
				values[key] = self.Interval[0] + (variables[key] - self.vars[key]["Values"][0]) * self.vars[key]["unit"]
			else:
				values[key] = self.Interval[0] + self.vars[key]["Values"].index(variables[key]) * self.vars[key]["unit"]
		#print "Result : ", values
		return values


	def __str__(self):
		print "Mapping Interval", self.Interval
		pprint(self.vars)
		print
		return str(self.vars)
		
	def get_keys(self):
		return self.vars.keys()


	def lower_bound_values(self):
		
		variables = {}
		#get first value for all the variables
		for v in self.vars:
			variables[v] = self.vars[v]["Values"][0]
			
		return variables


	def upper_bound_values(self):
		
		variables = {}
		#get first value for all the variables
		for v in self.vars:
			variables[v] = self.vars[v]["Values"][-1]
			
		return variables

	def get_next_value_from(self,key, value):
		if self.vars[key]["Continuous"]:
			if value + 1 <= self.vars[key]["Values"][-1]:
				return value + 1
		else:
			index = self.vars[key]["Values"].index(value) + 1
			if index < len(self.vars[key]["Values"]):
				return self.vars[key]["Values"][index]
		return None

	def get_previous_value_from(self, key, value):
		if self.vars[key]["Continuous"]:
			if value - 1 >= self.vars[key]["Values"][0]:
				return value - 1
		else:
			index = self.vars[key]["Values"].index(value) - 1
			if index >= 0:
				return self.vars[key]["Values"][index]
		return None


	def get_values_range(self, key):
		if self.vars[key]["Continuous"]:
			return self.vars[key]["Values"][-1] - self.vars[key]["Values"][0]
		else:
			return len(self.vars[key]["Values"]) - 1

	def get_value_at_index(self, key, index):
		if self.vars[key]["Continuous"]:
			return self.vars[key]["Values"][0] + index
		else:
			return self.vars[key]["Values"][index]


	def isvalid(self, key, value, constraint):
		vals = self.vars[key]["Values"]
		index = vals.index(constraint)
		if type(value) == str:
			if value in vals[:index + 1]:
				return False
		else:
			if value <= constraint:
				return False
		return True
				
			


if __name__ == "__main__":
	d = {
                    "Var": "%master_mem",
                    "Values": [
                      2048,
                      4096,
                      6144,
                      8192]}
	v = Variable(d)
	print v.get_id()
