#!/usr/bin/env python

from base import Base
from module import Module, ModelManagement

class Application(Base, ModelManagement):
    accepted_params = [ 
            { 
            'name' : 'ApplicationName', 
            'type' : str,
            'is_array' : False, 
            'is_required' : True
            }, 
            { 
            'name' : 'Author',
            'type' : str,
            'is_array' : False,
            'is_required' : False
            }, 
            { 
            'name' : 'Modules',
            'type' : Module,
            'is_array' : True,
            'is_required' : True
            }
            ]
        
    
    