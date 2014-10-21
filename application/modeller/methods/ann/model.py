#!/usr/bin/env python
from application.predictor.basemodel import BaseModel
import neuralnetwork as ann
import math

              
class ANNmodel(BaseModel):

     def __init__(self, inputs, outputs, topology = []):
		BaseModel.__init__(self)

		self.topology = [inputs] + topology + [outputs]
		self.model = ann.create(self.topology)
    
     def train(self, inputs, outputs):
         #write training data to file

        path_to_file = "/tmp/train.txt"
        f = open(path_to_file, "w")

        header = " ".join(map(lambda x: str(x), [len(inputs), len(inputs[0]), 1]))

        f.write(header + "\n")

        data = "\n".join(map(lambda i : " ".join(map(lambda x : str(float(x)), inputs[i])) + "\n" +  str(float(outputs[i])), range(len(inputs))))

        f.write(data)
        f.close()

        self.model = ann.train(self.model, path_to_file)

 
     def test(self, inputs, outputs):
         
        print "Testing..."
        
        predicted_output =[]
        
        for i in range(len(inputs)):
              
            predicted_output.append(ann.predict(self.model, inputs[i]))
            
        square_dif = map(lambda i: (outputs[i] - predicted_output[i])**2, range(len(predicted_output)))
        
        standard_deviation = math.sqrt(reduce(lambda x, y : x + y, square_dif) / len(predicted_output)) 
        print "Predicted output :", predicted_output            
        print "Real output      :", outputs
        print "SD :", standard_deviation
        return (predicted_output, standard_deviation)
 
     def __predict(self):
         pass
         









   
