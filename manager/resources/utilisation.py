#!/usr/bin/env python
import httplib2, json, sys, os
import threading, subprocess, time

from manager.resources.reservation import ReservationManager
from config import config_parser

class Monitor:

    UNDERUSED = 60.0
    OVERUSED  = 90.0

    def __init__(self):
        self.retriever = None
        self.data = []
        self.target = {}
        self.feedback = config_parser.get("main", "feedback") != "off"

    def setup(self, resources, reservation_id):
        self.resources = resources
        self.reservationID = reservation_id

    def get_monitoing(self):
        if self.feedback:
            info = ReservationManager.monitor(self.reservationID)
        else:
            print "Feedback is off."
        info = {}
        # keys = info.itervalues().next().keys()
        for machine in self.resources:
            addr = machine["Address"]
            info[addr] = {}
            for attr in info[addr]:
                ###  HACK  ###
                ### TODO: parse info from resource monitor
                info[addr][attr] = []
                continue
                ##############

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
                ### HACK ###
                recommendation[addr][attr] = 0
                continue
                ###########
                vals = result[addr][attr][:]
                vals = sorted(vals)
                if __smaller(vals, self.UNDERUSED) * 100.0 / len(vals) > 50:
                    recommendation[addr][attr] = -1
                elif (len(vals) - __smaller(vals, self.OVERUSED)) * 100.0 / len(vals) > 50:
                    recommendation[addr][attr] = +1
                else:
                    recommendation[addr][attr] = 0

        print "\ncrs_direction :", recommendation
        return recommendation


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
            for attr in res_attrs:
                ##### HACK ####
                botneck[addr][attr] = False
                continue
                ##############
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
