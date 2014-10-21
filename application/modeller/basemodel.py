#!/usr/bin/env python

class BaseModel:
    
    def __init__(self):
        self.model = None
    
    def train(self):
        raise NotImplementedError, "Must be implemented in the derived class - based on different modeling algorithms"

    
    def test(self):
        raise NotImplementedError, "Must be implemented in the derived class - based on different modeling algorithms"

    
    def predict(self):
        raise NotImplementedError, "Must be implemented in the derived class - based on different modeling algorithms"

    
    
    