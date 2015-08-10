#!/usr/bin/env python
import httplib2, json, sys, os
import threading, subprocess, time

# from manager.resources.connection import RemoteConnection
from manager.resources.reservation import ReservationManager
from config import config_parser

# class UtilizationDataThread(threading.Thread):

#     def __init__(self, function = None, addresses = [], interval = 0.5):
#         threading.Thread.__init__(self)
#         self.Enabled = True 
#         self.function = function
#         self.addresses = addresses
#         self.interval = interval
#         self.data = []
        
#         print "Recording usage for ", self.addresses

#     def run(self):
#         if self.data == None:
#             self.Enabled = False
#             return

#         #try:
#         while self.Enabled:
#             time.sleep(self.interval)
#             self.data.append(self.function(self.addresses))
#         #except:
#         #    self.Enabled = False


#     def stop(self):
#         self.Enabled = False
#         self.join()
        
#         return self.data
        


class Monitor:
    
    UNDERUSED = 60.0
    OVERUSED  = 90.0 
    
    def __init__(self):
        self.retriever = None
        self.data = []
        self.target = {
            "Machine": {
                "CPU_U_S_TIME": { "PollTimeMultiplier": 1 },
                "CPU_TOT_TIME": { "PollTimeMultiplier": 1 },  
                "MEM_U_S_BYTE": { "PollTimeMultiplier": 1 },
                "MEM_TOT_BYTE": { "PollTimeMultiplier": 1 }  
            },
            # "Storage": {
            #     "STG_CAPACITY": {"PollTimeMultiplier": 3 }
            # },
            "PollTime": 1000
        }
    
    def calculateCpuUsage(self, proc_data, tot_data):
        result = []
        for i in range(len(proc_data)-1):
        # for i in range(len(proc_data)):
            # print "DEBUG: %s %s %s" % (tot_data[i+1], tot_data[i], (tot_data[i+1] - tot_data[i]))
            util = 100 * ((proc_data[i+1] - proc_data[i]) / (tot_data[i+1] - tot_data[i]))
            # util = 100 * (proc_data[i]) / (tot_data[i])
            result.append(round(util, 2))
        return result

    def calculateMemoryUsage(self, proc_data, tot_data):
        result = []
        for i in range(len(proc_data)):
            # print "DEBUG: %s %s %s" % (tot_data[i+1], tot_data[i], (tot_data[i+1] - tot_data[i]))
            util = 100 * (proc_data[i]) / (tot_data[i])
            result.append(round(util, 2))
        return result
        

    def setup(self, resources, reservation_id):
        self.resources = resources
        self.reservationID = reservation_id

    # def __get_utilization(self, addresses):
    #     info = {}
    #     for address in addresses:
    #         d, response = httplib2.Http().request('http://%s:9292' % address,
    #                      'POST',
    #                      None,
    #                      headers={'Content-Type': 'application/json'})
    #         #print response
    #         info[address] = eval(response)
    #     return info
        
    # def run(self):
    #     conn = RemoteConnection()
    #     #start monitoring   
        
    #     #redirect to null 
    #     backup = sys.stdout
    #     sys.stdout = open(os.devnull, 'w')
        
    #     addrs = []
    #     for machine in self.resources:
    #         cmd = "curl -O %s;chmod +x monitor;nohup python monitor < /dev/null &> /dev/null &" % config_parser.get("main", "monitor_url")
    #         if machine["Type"] in ["Machine", "VM"]:
    #             conn.run(machine["Address"], cmd)
    #             addrs.append(machine["Address"])
        
    #     time.sleep(2)
    #     self.retriever = UtilizationDataThread(function = self.__get_utilization, addresses = addrs)
        
    #     self.retriever.start()
    #     #restore stdout
    #     sys.stdout = backup
    #     #done

    
    def get_monitoing(self):
        info = {}
        for machine in self.resources:
            monitor_data = ReservationManager.monitor(self.reservationID, machine["Address"])
            info[machine["Address"]] = monitor_data
        
        # keys = info.itervalues().next().keys()
        for addr in info:
            for attr in info[addr]:
                values = []
                all_vals = info[addr][attr]
                # lines = all_vals.split(',')
                # for i in range(0,len(lines),3):
                #     values.append(float(lines[i+2]))
                lines = all_vals.split('\n')
                for line in lines:
                    vals = line.split(',')
                    if len(vals) > 1:
                        values.append(float(vals[2]))
                info[addr][attr] = values

            cpu_util = self.calculateCpuUsage(info[addr]['CPU_U_S_TIME'], info[addr]['CPU_TOT_TIME'])
            memory_util = self.calculateMemoryUsage(info[addr]['MEM_U_S_BYTE'], info[addr]['MEM_TOT_BYTE'])
            # for attr in info[addr]:
            info[addr]={}
            info[addr]['Cores'] = cpu_util
            info[addr]['Memory'] = memory_util

        recommendation = self.get_recommendation(info)
        result = {"resources" : self.resources, "utilisation" : info}
        return recommendation, result
        # print "DEBUG: crs_monitor: %s" % result

    def get_recommendation(self, result):
        def __smaller(vals, v):
            i = 0
            while i < len(vals) and vals[i] <= v:
                i += 1
            return i

        recommendation = {}
        #get if resource needs to be increased or not
        for addr in result:
            recommendation[addr] = {}
            for attr in result[addr]:
                 vals = result[addr][attr][:]
                 vals = sorted(vals)
                 if __smaller(vals, self.UNDERUSED) * 100.0 / len(vals) > 50:
                     recommendation[addr][attr] = -1
                 elif (len(vals) - __smaller(vals, self.OVERUSED)) * 100.0 / len(vals) > 50:
                     recommendation[addr][attr] = +1
                 else:
                     recommendation[addr][attr] = 0

        print "\ncrs_direction :", recommendation

    # def process_usage(self, data = []):
    #     result = {}
        
    #     if not self.retriever:
    #         if not data:
    #             return {}
        
    #     if not data:
    #         usage = self.retriever.data[:]
    #     else:
    #         usage = data
        
    #     addresses = []
    #     for addr in self.resources:
    #         if addr["Type"] in ["Machine", "VM"]:
    #             addresses.append(addr["Address"])
                
    #     if usage == []:
    #         return {}
    #     keys = usage[0].values()[0].keys()
    #     print "keys monitored:", keys
    #     for addr in addresses:
    #         result[addr] = {}
    #         for key in keys:
    #             result[addr][key] = []
            
    #     for record in usage:
    #         for addr in record:
    #             for attr in record[addr]:
    #                 result[addr][attr].append(record[addr][attr])
                
    #     #print "\n~~~~~~~~~~~~~~ Monitoring result ~~~~~~~~~~~~~",
    #     #for addr in result:
    #     #   print addr
    #     #   for k in result[addr]:
    #     #       print  k, result[addr][k],      
    
    #     def __smaller(vals, v):
    #         i = 0
    #         while i < len(vals) and vals[i] <= v:
    #             i += 1
    #         return i
        
        
    #     recommendation = {}
    #     #get if resource needs to be increased or not
    #     for addr in result:
    #         recommendation[addr] = {}
    #         for attr in result[addr]:
    #              vals = result[addr][attr][:]
    #              vals = sorted(vals)
    #              if __smaller(vals, self.UNDERUSED) * 100.0 / len(vals) > 50:
    #                  recommendation[addr][attr] = -1
    #              elif (len(vals) - __smaller(vals, self.OVERUSED)) * 100.0 / len(vals) > 50:
    #                  recommendation[addr][attr] = +1
    #              else:
    #                  recommendation[addr][attr] = 0
    #     print "\ntop_direction :", recommendation
        
    #     """
    #     monitor = {
    #     "utilisation": 
    #     {
    #                 "10.158.4.49": {"Cores": [0.5, 0.6, 0.6, 0.7], "Swap": [0.0, 0.08, 0.08, 0.08, 0.08], "Memory": [4.4, 94.43, 94.46, 94.54, 94.58, 94.61, 94.64, 94.69]},
    #                 "10.158.4.50": {"Cores": [14.1, 14.0, 14.0, 14.0], "Swap": [0.0, 0.0, 0.0, 0.0, 0.0], "Memory": [4.37, 22.15, 57.36, 57.37, 57.36, 57.37, 57.43]}
    #     }, 
    #     "resources": 
    #     [
    #                 {"Attributes": {"Cores": 7, "Memory": 2048}, "Type": "Machine", "GroupID": "id0", "Role": "MASTER", "Address": "10.158.4.49"}, 
    #                 {"Attributes": {"Cores": 1, "Memory": 2048}, "Type": "Machine", "GroupID": "id1", "Role": "SLAVE", "Address": "10.158.4.50"}
    #     ]
    # }
    #     """
    #     return recommendation, {"resources" : self.resources, "utilisation" : result}
        
    # def stop(self):
    #     if self.retriever:
    #         data = self.retriever.stop()
            
    #         processed_data = self.process_usage(data)
    #         print "DEBUG top_monitor: %s" % processed_data[1]
    #         return processed_data
            
            
    def get_bottleneck(self, data):
        """
        data = {
            "utilisation": 
            {
                        "10.158.4.49": {"Cores": [0.5, 0.6, 0.6, 0.7], "Swap": [0.0, 0.08, 0.08, 0.08, 0.08], "Memory": [4.4, 94.43, 94.46, 94.54, 94.58, 94.61, 94.64, 94.69]},
                        "10.158.4.50": {"Cores": [14.1, 14.0, 14.0, 14.0], "Swap": [0.0, 0.0, 0.0, 0.0, 0.0], "Memory": [4.37, 22.15, 57.36, 57.37, 57.36, 57.37, 57.43]}
            }, 
            "resources": 
            [
                        {"Attributes": {"Cores": 7, "Memory": 2048}, "Type": "Machine", "GroupID": "id0", "Role": "MASTER", "Address": "10.158.4.49"}, 
                        {"Attributes": {"Cores": 1, "Memory": 2048}, "Type": "Machine", "GroupID": "id1", "Role": "SLAVE", "Address": "10.158.4.50"}
            ]
        }
        """
        botneck = {}
        #get if resource needs to be increased or not
        for addr in data["utilisation"]:
            res_attrs = filter(lambda x: x["Address"] == addr, data["resources"])[0]["Attributes"].keys()
            
            botneck[addr] = {}
            for attr in res_attrs:#data["utilisation"][addr]:
                vals = data["utilisation"][addr][attr][:]

                i = len(vals) - 1
                counter = 0
                while i > 0 and vals[i] > 90:
                    counter += 1
                    i -= 1
                #if the last 10 utilisation values > 90% ====> it may be a bottleneck causing failure
                if counter > 10 or (len(vals) < 10 and counter > 3):
                    botneck[addr][attr] = True
                else:
                    botneck[addr][attr] = False
        return botneck
    
                
#####   TEST PURPOSE  #######
if __name__ == "__main__":
    print "Testing Monitor"
    # conf = [
    #           {'Attributes': {'Cores': 7, 'Memory': 8192}, 'Type': 'Machine', 'GroupID': 'id0', 'Role': 'MASTER', 'Address': '10.158.0.79'}, 
    #           {'Attributes': {'Cores': 7, 'Memory': 6144}, 'Type': 'Machine', 'GroupID': 'id1', 'Role': 'SLAVE', 'Address': '10.158.0.80'}
    #       ]
    # mon = Monitor(conf)
    
    # usage = {
    #   "utilisation": 
    #   {
    #               "10.158.4.49": {"Cores": [0.5, 0.6, 0.6, 0.7], "Swap": [0.0, 0.08, 0.08, 0.08, 0.08], "Memory": [4.4, 94.43, 94.46, 94.54, 94.58, 94.61, 94.64, 94.69]},
    #               "10.158.4.50": {"Cores": [14.1, 14.0, 14.0, 14.0], "Swap": [0.0, 0.0, 0.0, 0.0, 0.0], "Memory": [4.37, 22.15, 57.36, 57.37, 57.36, 57.37, 57.43]}
    #   }, 
    #   "resources": 
    #   [
    #               {"Attributes": {"Cores": 7, "Memory": 2048}, "Type": "Machine", "GroupID": "id0", "Role": "MASTER", "Address": "10.158.4.49"}, 
    #               {"Attributes": {"Cores": 1, "Memory": 2048}, "Type": "Machine", "GroupID": "id1", "Role": "SLAVE", "Address": "10.158.4.50"}
    #   ]
    # }
    
    # print mon.get_bottleneck(usage)
    
    # sys.exit()
    # mon.run()
    
    # time.sleep(10)
    
    # data = mon.stop()
    
    # print "\n Recommendation :", mon.process_usage(data)
        
############################


