#!/usr/bin/env python
from numpy import asarray, tan, exp, ones, squeeze, sign, log, sqrt, pi, shape, array, minimum, where, random, finfo
from manager.state import solution


class Algorithm:
	
	def __init__(self, function, x_size, lower, upper, already_found_test = None, max_eval = 20, init_steps = 5):
		
		self.function = function
		self.interval = {"lower" : lower, "upper" : upper}
		self.solutions = []
		self.max_evals = max_eval
		self.init_steps = init_steps
		self.already_tested = already_found_test
		self.x_size = x_size
		self.init_parameters()
		
		
	def init_parameters(self):
		raise NotImplementedError
		
	def update_state(self, params = {}): 
		self.solutions = []
		sol_info  = params["solutions"]
		for s in sol_info:
			self.solutions.append(solution(s))
		
		self.max_evals = params["max_evals"]
		self.init_steps = params["init_steps"]
		self.x_size = params["x_size"]

	def get_state(self):
		result = { 
					"solutions" : map(lambda sol: sol.get(), self.solutions), 
					"max_evals" : self.max_evals, 
					"init_steps": self.init_steps,
					"x_size"  	:self.x_size
				}
		return result
		

	def run_step(self):
		raise NotImplementedError


	def check_state(self):
		raise NotImplementedError

	def stop_condition(self):
		raise NotImplementedError
		
		
class SimulatedAnnealing(Algorithm):
    
	def init_parameters(self):
		self.current_solution = solution()
		self.best_solution = None
		self.T = None
		self.T0 = None
		self.Tf = None
		self.alpha = None 
		self.iterations = 0
		self.trial = 0
		self.trials_per_cycle = 3		
		

	def get_state(self):
		result = Algorithm.get_state(self)
		
		result["best_solution"] = None if not self.best_solution else self.best_solution.get()
		result["current_solution"] = self.current_solution.get()
		result["T"] = self.T
		result["T0"] = self.T0
		result["Tf"] = self.Tf
		result["alpha"] = self.alpha
		result["iterations"] = self.iterations
		result["trial"] = self.trial
		result["trials_per_cycle"] = self.trials_per_cycle
		
		return result
			
	def update_state(self, params):
		Algorithm.update_state(self, params)
		
		self.best_solution = None if not params["best_solution"] else solution(params["best_solution"])
		self.current_solution = solution(params["current_solution"])
		self.T = params["T"]
		self.T0 = params["T0"]
		self.Tf = params["Tf"]
		self.alpha = params["alpha"]
		self.iterations = params["iterations"]
		self.trial = params["trial"]
		self.trials_per_cycle = params["trials_per_cycle"]	

	def check_state(self):
		if not self.T:
			if self.iterations >= self.init_steps:
				self.init_temp()
				
	def stop_condition(self):
		if not self.T or not self.Tf:
			return False
		return self.T <= self.Tf or self.iterations >= self.max_evals

	def init_temp(self):
		good_sols = filter(lambda objective: objective < finfo(float).max, map(lambda s:self.objective_function(s), self.solutions))
		#if not at least 2 good solutions we keep going
		if len(good_sols) < 2:
			return False
		else:
			fmax  = max(good_sols)
			fmin  = min(good_sols)
			self.T0 = (fmax-fmin)*1.5
			self.T = self.T0
			self.alpha = (0.001 / self.T0) ** (1.0 / (self.trials_per_cycle - 1.0))
			self.Tf = 1e-12
		return True
	
	def update_temperature(self):
		#algorithm finishes when reaching the cool temperature Tf
		print "T =", self.T, " T0 =",self.T0, " Tf =",self.Tf
		self.T = self.T0 / log((self.iterations - self.init_steps)/ self.trials_per_cycle + 1.0)
		#self.T = self.T * self.alpha
		self.trial = 0
		
	def run_step(self):
		self.check_state()
		if self.T:
			if self.stop_condition():
				return 0
			#else generate a number of solutions for the current temperature
			if self.trial == self.trials_per_cycle:
				self.update_temperature()
		
		#build new solution
		new_solution = solution()
		x = self.neighbor(self.current_solution.x)
		
		#execute function which returns the cost as the product between the monetary cost and execution time
		#returns tuple (conf, cost)
		success, conf, cost, et, _, _ = self.function(x)
		if not success["Success"]:
			et = finfo(float).max
			return
		new_solution = solution({"conf" : conf, "x" : x, "cost" : cost, "et" : et, "success" : success["Success"]})
		self.solutions.append(new_solution)
		
		self.iterations += 1
		if not self.T:
			#if the temperature has not been initialized then we are are in the random tries to init it
			return new_solution
		
		self.trial += 1
		self.accept_or_reject_solution(new_solution)
		
		return self.best_solution
		
	def objective_function(self, solution):
		#we try to minimize the product between execution time and cost
		return solution.cost * solution.et
		

	def acceptance_probability(self, cur_sol, new_sol, T):
		if cur_sol.x  == None:
			return 1.0
		delta = abs(self.objective_function(new_sol) - self.objective_function(cur_sol))
		p = exp(-delta * 1.0 / T)
		return p
	
	def accept_or_reject_solution(self, new_solution):
		ap = self.acceptance_probability(self.current_solution, new_solution, self.T)
		
		if ap > random.random():
			self.current_solution = new_solution
			if not self.best_solution or self.objective_function(self.best_solution) > self.objective_function(self.current_solution):
				self.best_solution = self.current_solution
					
	def neighbor(self, solution = None):
		#generate a new solution
		x = None
		tested = False
		while (not x) or (x and tested):
			x = self.draw_random(solution)
			if not self.already_tested:
				#no test function provided
				tested = False
			else:
				confs  = map(lambda s:s.conf, self.solutions)
				tested = self.already_tested(confs, x)
		return x
		
	def draw_random(self, solution = None):		
		if solution:
			#get a nighbor
			std = minimum(sqrt(self.T) * ones(self.x_size), (self.interval["upper"] - self.interval["lower"]) / 3.0 / self.alpha)
			x0 = asarray(solution)
			xc = squeeze(random.normal(0, 1.0, size=self.x_size))
			x = x0 + xc * std * self.alpha
		else:
			#get random solution
			x = random.uniform(size = self.x_size) * (self.interval["upper"] - self.interval["lower"]) + self.interval["lower"]
		return list(x)
        
        
class DirectedSimulatedAnnealing(SimulatedAnnealing):
	
	PROB_GRADIENT = 80
	PROB_RANDOM   = 20
	
	def run_step(self):
		self.check_state()
		if self.T:
			if self.stop_condition():
				return 0
			#else generate a number of solutions for the current temperature
			if self.trial == self.trials_per_cycle:
				self.update_temperature()
		#build new solution
		new_solution = solution()
		x = self.neighbor(self.current_solution.x, self.current_solution.gradient)
		
		#execute function which returns the cost as the product between the monetary cost and execution time
		#returns tuple (conf, cost)
		success, conf, cost, et, direction, monitor = self.function(x)
		print success
		if not success["Success"]:
			et = finfo(float).max
			return
		new_solution = solution({"conf" : conf, "x" : x, "cost" : cost, "et" : et, "gradient" : direction, "monitor" : monitor, "success" : success["Success"]})
		self.solutions.append(new_solution)
		self.iterations += 1
		if not self.T:
			#if the temperature has not been initialized then we are are in the random tries to init it
			return new_solution
		self.trial += 1
		self.accept_or_reject_solution(new_solution)
		return self.best_solution
		

	def neighbor(self, solution = None, direction = None):
		#generate a new solution
		x = None
		tested = False
		while (not x) or (x and tested):
			#here check if we can use the feedback on utilisation
			if direction:
				if not all(item == 0 for item in direction): 
					prob = random.random() * sum([self.PROB_GRADIENT, self.PROB_RANDOM])
					if prob < self.PROB_GRADIENT:
						print "Follow direction ", direction
						x = self.draw_random_directed(solution, direction)
					else:
						x = self.draw_random(solution)
				else:
					print "Random neighbor"
					#get neighbor around the current
					x = self.draw_random(solution)
			else:
				x = self.draw_random(solution)
				
				if not self.already_tested:
					#no test function provided
					tested = False
				else:
					confs  = map(lambda s:s.conf, self.solutions)
					tested = self.already_tested(confs, x)
		return x
	
		
	def draw_random_directed(self, x0, direction, trials = 3):
		print "x0  :", x0
		print "dir :", direction
		xnew = []
		for i in range(len(x0)):
			if direction[i] > 0 and x0[i] < 1.0:
				xc = random.normal(0., 1.0 - x0[i]) 
				val = abs(xc)
			elif direction[i] < 0 and x0[i] > 0:
				xc = random.normal(0., x0[i])
				val = -(abs(xc))
			else:
				val = 0.
			
			val = x0[i] + val
			
			if val < 0.:
				val = 0. 
			elif val > 1.:
				val = 1. 
			
			xnew.append(val)
		
		if xnew == x0:
			if trials > 0:
				#try again to get close neighbor based on direction. 
				xnew = self.draw_random_directed(x0, direction, trials = trials - 1)
			else:
				#If it fails 3 times call the completely random method
				xnew = self.draw_random(x0)
				
		return xnew

#### TEST PURPOSE ####  

if __name__ == "__main__":
	
	def func(x  = []):
		return {"x" : 1, "y" : 2}, x[0] * 2 + x[1], 67

	alg = SimulatedAnnealing(func,2, 0.0, 1.0)
	
	test1 = False

	if test1:
		test_state = {
			'trials_per_cycle': 3, 'Tf': 1e-12, 
			'best_solution': {'x': [0.64625086986982416, 0.3116144340840481], 'cost': 1.6041161738236964, 'conf': {'y': 2, 'x': 1}}, 
			'trial': 2, 'x_size': 2, 
			'solutions': [
					{'x': [0.6977138903310971, 0.37191896687367498], 'cost': 1.7673467475358691, 'conf': {'y': 2, 'x': 1}}, 
					{'x': [0.77906844537692876, 0.83902365021207981], 'cost': 2.3971605409659373, 'conf': {'y': 2, 'x': 1}}, 
					{'x': [0.1113196653075863, 0.013359875638793595], 'cost': 0.2359992062539662, 'conf': {'y': 2, 'x': 1}}, 
					{'x': [0.87089169887311335, 0.29366347675403071], 'cost': 2.0354468745002574, 'conf': {'y': 2, 'x': 1}}, 
					{'x': [0.12041930244884924, 0.98824887196514288], 'cost': 1.2290874768628415, 'conf': {'y': 2, 'x': 1}}, 
					{'x': [0.6579405917168587, 0.41033407070006656], 'cost': 1.7262152541337841, 'conf': {'y': 2, 'x': 1}}, 
					{'x': [0.63030734525983256, 0.38444139363367502], 'cost': 1.6450560841533401, 'conf': {'y': 2, 'x': 1}}, 
					{'x': [0.64243060097425908, 0.31626110042626288], 'cost': 1.6011223023747809, 'conf': {'y': 2, 'x': 1}}, 
					{'x': [0.64232116090000435, 0.31040295925511685], 'cost': 1.5950452810551257, 'conf': {'y': 2, 'x': 1}}, 
					{'x': [0.64625086986982416, 0.3116144340840481], 'cost': 1.6041161738236964, 'conf': {'y': 2, 'x': 1}}], 
			'iterations': 10, 
			'alpha': 0.017563488309332492, 
			'max_evals': 20, 
			'init_steps': 5, 
			'T': 0.056936297755192662
			}
		print 
		alg.update_state(test_state)
		print alg.get_state()
		
		print alg.run_step().get()
		
		print alg.get_state()
	else:

		while (not alg.stop_condition()):
			print alg.run_step().get()
			alg.check_state()
			
		print alg.get_state()
#################
