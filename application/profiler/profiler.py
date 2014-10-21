#!/usr/bin/env python
from application.core.context.parameters import VariableModel
from application.profiler.strategy import * 
from application.utils.math import MathUtils

import sys, os

class Profiler:
    
    def __init__(self, app):
        self.application = app
        self.strategy = None
        
    def run(self):        
        """
            GENERATE COMPONENTS COMBINATIONS    
        """
        print "\nProfiling application...\n"
        
        print "--->  Implementation Selection Process  <---"
        self.components_index = []
        
        for i in range(len(self.application.Modules)):
            self.components_index.append(len(self.application.Modules[i].Implementations) - 1) 
        
        print "Component's index :", self.components_index
        
        for item in MathUtils.generate_combinations(self.components_index):
            '''
                profiling a combination of modules
            '''
            components = []
        
            for i in range(len(item)):
                print "Selecting implemention %d from module %d" % (i, item[i])
                components.append(self.application.Modules[i].Implementations[self.components_index[item[i]]])  
        
            """
                EXPLORE A COMBINATION 
            """
            #self.__profile(components)
            self.__exhaust_space(components)
        print "\nProfiling process ended!\n\n"
    

    def __exhaust_space(self, apps):
		implementation = apps[0]
		strategy = BruteForce(implementation, save_to_log = True)
		experiments = []
		experiments = strategy.explore()

		#save experiments to log files
		#f = open("/home/aiordache/exp/logs")
	


    def __profile(self, apps):
        """
            Profiling Routine
            * Search space for the smallest input size #the first value of each argument
            * Select Pareto experiments
            * Modify input size and test on the Pareto configurations 
        """
        #print "Profiling process id =", Thread.getName(self)
        implementation = apps[0]
        arguments = implementation.Arguments
        #create strategy
        strategy = SimulatedAnnealingStrategy(implementation)
        
        """
            Experiment with different input sizes.
            * generate combinations
        """
        experiments = []
        pareto_experiments = []
        
        print "~ Generate Argument Combinations ~"
        argument_combinations = Combinations()
        
        for values in MathUtils.generate_combinations(map(lambda arg: arg.get_range_size() - 1, arguments)):
            """
                Set the arguments for the current list of experiments.
            """
            new_args = []
            for i in range(len(arguments)):
                new_args.append(copy.deepcopy(arguments[i]))
                #get the argument value
                val = arguments[i].get_value_at_index(values[i])
                #set range or values as only having this value
                new_args[-1].set_values([val, val])
            
            #change input size here
            strategy.implementation.Arguments = new_args
            #update arguments model
            strategy.generate_arguments_model()
            
            if pareto_experiments == []:
                """
                    Apply the search strategy for the first combination
                """
                #don't want to see experiments trace in the output
                #redirect to null 
                backup = sys.stdout
                sys.stdout = open(os.devnull, 'w')
                
                #explore parameter space with the first input size /first value for arguments                   
                experiments = strategy.explore()
                #restore stdout    
                sys.stdout = backup
                                
                pareto_experiments = self.get_pareto_experiments(experiments)
                
                pareto_configurations = map(lambda exp: exp["Configuration"], pareto_experiments)
                print "Pareto Configurations per input size :", pareto_configurations
                
                print "Test different input sizes."
            else:
                """
                    Test different input sizes on the efficient configurations only
                """
                backup = sys.stdout
                sys.stdout = open(os.devnull, 'w')
               
                #test the pareto configurations with the current arguments
                pareto_experiments.extend(strategy.test_additional_configurations(pareto_configurations))
                
                #restore stdout    
                sys.stdout = backup
        
        
        print "Total Pareto experiments : %d."% len(pareto_experiments)
        Traces.TrainingSet = experiments
        Traces.ParetoExperiments = pareto_experiments
        
        
        
        
    def get_pareto_experiments(self, exps):
        """
            Select experiments with the optimal cost-et trade-off        
        """
        cost = map(lambda x: x["Results"]["TotalCost"], exps)
        et = map(lambda x: x["Results"]["ExeTime"], exps)
        
        pcost, pet = MathUtils.pareto_frontier(cost, et)
        print "Pareto cost:", pcost
        print "Pareto et  :", pet
        print "Number experiments :", len(pcost)
        pex = []
        
        for exp in exps:
            for i in range(len(pcost)):
                if exp["Results"]["TotalCost"] == pcost[i] and exp["Results"]["ExeTime"] == pet[i]:
                    pex.append(exp)
                    
                    
        print "~ Pareto Experiments ~"
        print pex,"\n\n"
        return pex
                  
        
        
