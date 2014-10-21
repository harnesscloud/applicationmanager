#!/usr/bin/env python
from application.utils.math import MathUtils
from application.profiler.profiler import Profiler
import numpy, random

#import matplotlib.pyplot as plt

class Model:
	def __init__(self, application):
		self.application = application
		

	def profile(self):
		print  "\nRunning Profiling Process..."
		"""
			PROFILING
		"""
		profiler = Profiler(self.application)
		exps = profiler.run()
		
		return exps
		
	def extract_model(self):
		pass
        
	def create_model(self):
		#static input experiments
		#Identification of the Pareto Frontier
		exps = self.profile()
		#continue by varying input size
		
		return exps

	def update_model(self, conf_to_exclude = []):
		pass

	
