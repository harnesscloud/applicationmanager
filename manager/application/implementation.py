#!/usr/bin/env python
from manager.application.base import Base
from manager.application.search_space import VariableMapper
from manager.resources.connection import RemoteConnection
from manager.utils.monitor import MonitorDataThread
from manager.application.elements.resources import Resources

import time, sys, os, simplejson

class Implementation(Base):
    accepted_params = [
		{
		'name':'ImplementationName',
		'is_array': False,
		'is_required': True
		},
		{
		'name':'Resources',
		'type' : Resources,
		'is_array': False,
		'is_required': True
		},
		{
		'name':'GlobalConstraints',
		'type' : str,
		'is_array': True,
		'is_required': True
		},
		{
		'name':'EnvironmentVars',
		'type' : dict,
		'is_array': False,
		'is_required': False
		},
		{
		'name':'Tarball',
		'type' : str,
		'is_array': False,
		'is_required': True
		},
		{
		'name':'DeploymentArgs',
		'type' : str,
		'is_array': False,
		'is_required': False
		},
		{
		'name':'ExecutionArgs',
		'type' : str,
		'is_array': False,
		'is_required': False
		}
    ]
    
    def __init__(self, hashmap = {}):
        Base.__init__(self, hashmap)
        self.Variables = self.get_Vars()
    def __process_args(self, args, variables):
        arg_str = args[:]

        for v in variables:
            if v in arg_str:
                arg_str = arg_str.replace(v, str(variables[v]))

        return arg_str

    def __process_environ_vars(self, machines, variables):
        result = {}
        env_vars = self.EnvironmentVars
        for key in env_vars:
            vars = env_vars[key]
            result[key] = ""
            values = vars.split(";")
            for val in values:
                if val.startswith("address(") and val.endswith(")"):
                   keyword = val[8:]
                   keyword = keyword[:-1]
                   gather_info = []
                   for machine in machines:
                      for k in machine:
                         if machine[k] == keyword:
                            gather_info.append(machine["Address"])
                   result[key] = result[key] + ";".join(map(lambda item: str(item), gather_info)) + ";"
                else:
                   new_value = val
                   for v in variables:
                       if v in new_value:
                           new_value = new_value.replace(v, str(variables[v]))
                   result[key] = result[key] + new_value + ";"
            if result[key].endswith(";"):
               result[key] = result[key][:-1]    
        return result


    def deploy(self, machines, variables):
        print "....... Application Deployment ......."
        env_vars = self.__process_environ_vars(machines, variables)
        instances={}
        instances['Instances'] = machines
        #don't want to see experiments trace in the output
        #redirect to null
        backup = sys.stdout
        #sys.stdout = open(os.devnull, 'w')
        conn = RemoteConnection(environ_vars = env_vars)
        #print "Run deployment scripts."
        #general cmds
        cmds = ["curl -O %s" % self.Tarball, "tar xzf %s" % self.Tarball.split("/")[-1]]
        cmds.extend(["mkdir -p /var/cache/harness/;", "echo '%s' > /var/cache/harness/instances.json" % simplejson.dumps(instances)])
        cmds.extend(["chmod +x init.sh", "chmod +x start.sh", "chmod +x cleanup.sh"])

        cmds.append(". init.sh %s" % (self.__process_args(self.DeploymentArgs, variables)))

        print "Running cmd on all machines :", cmds
        #of type Machine
        machines_to_execute = filter(lambda m  :m["Type"] in ["Machine"], machines)
        for cmd in cmds:
            print "Running cmd %s" %cmd
            for machine in machines_to_execute:
                conn.run(machine["Address"], cmd)

        time.sleep(3)
        #restore stdout
        sys.stdout = backup

        print "Deployment finished."

    def cleanup(self, machines, variables):
        print "....... Cleanup ......."
        env_vars = self.__process_environ_vars(machines, variables)

        #don't want to see experiments trace in the output
        #redirect to null
        backup = sys.stdout
        sys.stdout = open(os.devnull, 'w')
        conn = RemoteConnection(environ_vars = env_vars)
        #print "Run deployment scripts."
        #general cmds
        cmd = ". cleanup.sh"
        #of type Machine
        machines_to_execute = filter(lambda m  :m["Type"] in         ["Machine"], machines)
        print "Running %s on all machines." % cmd
        for machine in machines_to_execute:
            conn.run(machine["Address"], cmd)

        time.sleep(1)
        #restore stdout
        sys.stdout = backup
        print "Done."

    def execute(self, machines, variables):
        env_vars = self.__process_environ_vars(machines, variables)
        print env_vars

        conn = RemoteConnection(environ_vars = env_vars)
        print "---- Application Execution ---- "

        #don't want to see experiments trace in the outpu
        #redirect to null
        #backup = sys.stdout
        #sys.stdout = open(os.devnull, 'w')
        args = self.__process_args(self.ExecutionArgs, variables)
        print "Execution arguments:",args
        cmd = "./start.sh %s" % args
        success  = []
        #of type Machine
        machines_to_execute = filter(lambda m  :m["Type"] in         ["Machine"], machines)
        StartTime = time.time()
        for machine in machines_to_execute:
            exit_code, output = conn.run(machine["Address"], cmd)
            print "output : ", output
            success.append(exit_code)
        EndTime = time.time()
        #restore stdout
        #sys.stdout = backup

        print "Execution finished. Exit codes :", success
        return (sum(success) ,(EndTime - StartTime))
