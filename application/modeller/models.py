#!/usr/bin/env python
from application.core.patterns.store import Traces
from application.utils.math import MathUtils
from application.model.profiler.profiler import Profiler
from application.predictor.methods.svm.model import SVRmodel
from application.predictor.methods.ann.model import ANNmodel
import numpy, random

#import matplotlib.pyplot as plt

class Model:
	pass




class PerformanceModel:
    
    Models   = []
    KeyOrder = []
    
    
    def __init__(self):
        """
            Extracting dependency model from the training set using several techniques
            * generate models
            * test models
        """
        
        self.Experiments = Traces.ParetoExperiments
        print "~~~ Creating Mathematical Model using SVR / ANNs. ~~~~\n"
        
        self.__format_data()
        
        print "TRAIN :", len(self.TrainSet)
        print "TEST  :", len(self.TestSet)
        
        """
            Test Support Vector Machines for Regression with rbf kernel
        """
        return
        #self.Models.append(SVRmodel())
        self.Models.append(ANNmodel(len(self.TrainSet["Input"][0]),1, [2, 2]))
        
        
        self.train_models(self.TrainSet["Input"], self.TrainSet["Output"])
        
        results = self.test_models()
        
        
        print "\n~~ Done Building Model ~~\n\n"
        print "Results :", results
        
        return
        self.show_prediction(self.TestSet["Output"], results[0][0], map(lambda x: str(x),self.TestSet["Input"]), results[0][1])
        #self.show_plot()
        
        
    def train_models(self, inputs, outputs):
        for model in self.Models:
            model.train(inputs, outputs)     
         
         
    def test_models(self):
        
        results = []
        for model in self.Models:
            results.append(model.test(self.TestSet["Input"], self.TestSet["Output"]))          
         
        return results
    
    
    def __format_data(self):
        
        key_order = []
        
        key_order.extend(self.Experiments[0]["Arguments"].keys()) 
        key_order.extend(self.Experiments[0]["Configuration"].keys())
        
        
        print "input keys order :", key_order
        
        inputs = []
        outputs = []
        cost = []
        for exp in self.Experiments:
            inputs.append([])
            
            for i in range(len(key_order)):
                if key_order[i] in exp["Arguments"]:
                    inputs[-1].append(exp["Arguments"][key_order[i]])
                else:#if key_order[i] in exp["Configuration"]:
                    inputs[-1].append(exp["Configuration"][key_order[i]])
            
            outputs.append(exp["Results"]["ExeTime"] * 1000)
            cost.append(exp["Results"]["TotalCost"] * 1000)
            
        self.KeyOrder = key_order
        
        """
            Randomly select configurations for test 
        """
        n = len(inputs)/10 + 1 #testing samples
        pos = []
        for i in range(n):
            pos.append(random.randint(0, len(inputs)))
        
        self.TrainSet = {"Input" : [], "Output" : [], "Cost" : []}
        self.TestSet = {"Input" : [], "Output" : [], "Cost" : []}
        
        
        for i in range(len(inputs)):
            if i in pos:
                self.TestSet["Input"].append(inputs[i])
                self.TestSet["Output"].append(outputs[i])
                self.TestSet["Cost"].append(cost[i])
        
            else:
                self.TrainSet["Input"].append(inputs[i])
                self.TrainSet["Output"].append(outputs[i])
                self.TrainSet["Cost"].append(cost[i])
        
        
        print "inputs  :", inputs
        print "outputs :", outputs 
        print "cost    :", cost
        
        
    
    def show_prediction(self, rout, pout, labels, stand_dev):
        
        width = 0.35
        ind = range(len(rout))
        
        fig, ax = plt.subplots()
        rects1 = ax.bar(ind, rout, width, color='g')#, yerr=menStd)
        
        ind = map(lambda x: x + width, ind)
        rects2 = ax.bar(ind, pout, width, color='r')#, yerr=womenStd)
        
        # add some
        ax.set_ylabel('Execution time')
        ax.set_title('Standard Deviation: %f' % stand_dev)
        ax.set_xticks(ind)
        ax.set_xticklabels( labels )
        
        ax.legend( (rects1[0], rects2[0]), ('Real', 'Predicted') )
        
        
        plt.show()
        
    def show_plot(self):
        # look at the results
        plt.scatter(self.TrainSet["Cost"], self.TrainSet["Output"], c='r', label='data')
        #plt.plot(X, y_poly, c='b', label='Polynomial model')
        plt.xlabel('data')
        plt.ylabel('target')
        plt.title('Support Vector Regression')
        plt.legend()
        plt.show()
        
        
        
    
    
