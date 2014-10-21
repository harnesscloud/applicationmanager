#!/usr/bin/env python
from application.predictor.basemodel import BaseModel

from sklearn import svm
import math

     
class SVRmodel(BaseModel):
    
    
    def __init__(self, kernel = "rbf"):
        BaseModel.__init__(self)
        
        self.model = svm.SVR(kernel = kernel)        
    
    
    def train(self, inputs, outputs):
        
        self.model.fit(inputs, outputs)
        

    def test(self, inputs, outputs):
        
        predicted_output = list(self.model.predict(inputs))  
        
        square_dif = map(lambda i: (outputs[i] - predicted_output[i])**2, range(len(predicted_output)))
        
        standard_deviation = math.sqrt(reduce(lambda x, y : x + y, square_dif) / len(predicted_output)) 
        print predicted_output            
        print outputs
        print "SD :", standard_deviation
        return (predicted_output, standard_deviation)