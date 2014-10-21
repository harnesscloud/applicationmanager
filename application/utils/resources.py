#!/usr/bin/env python
import pxssh
import sys
import time
import httplib2

import paramiko

def get_utilization(machines):
    
    util_data = []
    for host in machines:
       d, response = httplib2.Http().request('http://%s:9292' % host,
                     'POST',
                     None,
                     headers={'Content-Type': 'application/json'})
    
       #print "MonD response   = ",response
       
       util_data.append(response)
    return util_data


class RemoteConnection:
    
    def __init__(self, devicetype = "VM", environ_vars = {}):
        """
            Constructor.
            Uses Paramiko   
            Connection protocol is different depending on the resource type we are trying to connect to
        """
        self.type = devicetype 
        self.env_vars = environ_vars
        paramiko.util.log_to_file('/home/aiordache/.logs/am/ssh.log') 
    
    def run(self, host, cmd = None, script = None, user = "root"):
		#output = None
		ssh = paramiko.SSHClient()
		ssh.load_system_host_keys()
		ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		tries = 3;
		#print "Connecting to ", host 
		while(tries > 0):
			try:	
				ssh.connect(host, username = user)
				#print "Success"
				break;
			except:
				tries = tries - 1;
				print "Failed connecting to %s, try connecting later..." % host
				time.sleep(10)
		if tries == 0:
			return None
		cmd_to_execute = ";".join(["export %s=%s" % (key, self.env_vars[key]) for key in self.env_vars])
		if cmd != None:
			cmd_to_execute = cmd_to_execute + ";" + cmd
		else:
			f = script.split("/")[-1]
			cmd_to_execute = cmd_to_execute + ";" + ";".join(["wget %s" % script, "chmod +x %s" % f, ". %s" % f])
		cmd_to_execute = cmd_to_execute.strip(";")
		print "Executing :", cmd_to_execute, " on ", host
		ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd_to_execute)
		output = ssh_stdout.read()
		output += "\nERROR: ["
		output += ssh_stderr.read()
		output += "]"
		exit_status = ssh_stdout.channel.recv_exit_status()
		ssh.close()
		del ssh

		return output

#s = RemoteConnection()
#print s.run("10.176.0.1", cmd = "wget http://public.rennes.grid5000.fr/~aiordache/harness/apps/rtm/1/start.sh;chmod +x ~/start.sh;~/start.sh")


class PXSSHRemoteConnection:
    
    def __init__(self, devicetype = "VM", environ_vars = {}):
        """
            Constructor.
            
            Connection protocol is different depending on the resource type we are trying to connect to
        """
        self.type = devicetype 
        self.env_vars = environ_vars
            
    
    def run(self, host, cmd = None, script = None, user = "root"):
        output = None
        conn = pxssh.pxssh()
	tries = 5; 
        while (not conn.login (host, user, login_timeout = None)) and tries > 0:
            print "SSH session failed on site %s." % host
            print str(self.conn)
            #sys.exit(1)
	    time.sleep(10)
	    tries = tries - 1
        if tries == 0:
	    return None
        cmd_to_execute = ";".join(["export %s=%s" % (key, self.env_vars[key]) for key in self.env_vars])
        if cmd != None:
            cmd_to_execute = cmd_to_execute + ";" + cmd
        else:
            f = script.split("/")[-1]
            cmd_to_execute = cmd_to_execute + ";" + ";".join(["wget %s" % script, "chmod +x %s" % f, ". %s" % f])
        cmd_to_execute = cmd_to_execute.strip(";")
        print "Executing :", cmd_to_execute
        conn.sendline(cmd_to_execute)
        conn.prompt(timeout = None)
        output = conn.before[:]
        #print "output :", output
        conn.logout()
        del conn
        
        return output
