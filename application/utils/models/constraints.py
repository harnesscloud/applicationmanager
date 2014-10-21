#!/usr/bin/env python
import sys

class Constraint:
    def __init__(self, expr):
        self.expression = expr
        self.variable = "x"
        self.f = lambda x: eval(self.expression)
        
    def evaluate(self, x):
        result = self.f(x = x)
        
        
        print "Evaluating ",self.expression," for ",self.variable, "=", x , "as", result
        return result

    
    
def c(s):
    constr = []
    for ss in s:
        constr.append(Constraint(ss))
    return constr
    
    
def e(n):
    s = ["x < 3", "x > 0"]
    
    
    constr = []
    for ss in s:
        constr.append(Constraint(ss))
    
    print reduce(lambda x,y: x and y, map(lambda c: c.evaluate(n), constr))
    
        
e(0)


class ConstraintGroup:
    
    def __init__(self):
        pass