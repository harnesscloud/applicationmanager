#!/usr/bin/env python
import time
import subprocess            
            
            
    
class SimulatorManager:
    @staticmethod
    def deploy_simulator():
        pass
    
    @staticmethod 
    def simulate(env_vars, simcall):
        #time.sleep(5)
        cmd = ";".join(["export %s=%s" % (key, env_vars[key]) for key in env_vars] + [simcall])
        et = float(subprocess.check_output([cmd], shell = True))
        print "Execution Time :",et
        #print type(et)
        return et
        