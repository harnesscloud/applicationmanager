#!/usr/bin/env python

import os, sys, traceback
from pprint import pprint
import httplib2
import simplejson
from application.core.patterns.singleton import SingletonParent
    
class CrossResourceSchedulerConnection(SingletonParent):
    def __init__(self, url = "http://localhost:5558"):
        SingletonParent.__init__(self)
        self.conn = httplib2.Http()
        self.url = url +"/method"
        
    def __make_request(self, url, content = {}):
        #print "Conn ID =", id(self)
        #print "\nRequest :", url, content
        data, response = self.conn.request(self.url + url , 'POST',
                          simplejson.dumps(content),
                          headers={'Content-Type': 'application/json'})
        try:
            response = simplejson.loads(response)
        except:
            print traceback.print_exc()
            return response
        
        #print "Response :", response["result"]
        return response["result"]
    
    
    def prepareReservation(self, configuration = {}):
        response = self.__make_request("/prepareReservation", configuration)
        
        return response
    
    def createReservation(self, configurationID):
        response = self.__make_request("/createReservation", {"ConfigID" : configurationID})
        return response
    
    def releaseReservation(self, reservationID):
        response = self.__make_request("/releaseReservation", {"ResID" : reservationID})
        if response is {}:
            return True
    
    def checkReservation(self, reservationID):
        response = self.__make_request("/checkReservation", {"ResID" : reservationID})
        
        return response
    #for development only
    def reset(self):
        response = self.__make_request("/reset")
        return response

#test purpose
#
#conn = CrossResourceSchedulerConnection()
#
#res = conn.prepareReservation({
#   "Resources":[
#      {"GroupID":"id0",
#         "Type":"Machine",
#         "NumInstances":1,
#         "Attributes":{
#            "Cores":8,
#            "Memory":4096,
#         }}]})
#res = conn.createReservation(res["ConfigID"])
#
#conn.checkReservation(res["ResID"])
#
#conn.releaseReservation(res["ResID"])

