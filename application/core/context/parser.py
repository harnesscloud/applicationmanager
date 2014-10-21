#!/usr/bin/env python

import os, sys
import simplejson
from application.core.application import Application
import urllib

from application.core.base import Base
   
class ManifestParser:
    
    REQUIRED_FIELDS = ["Name", "Modules"]
    @staticmethod
    def load(path):
        print "Parsing manifest..."
        
        print path
        manifest = urllib.urlopen(path)
        #manifest = open(path, "r")
        data = manifest.read()
        data = simplejson.loads(data)
        #print data
        app = Application(data)
        #print "Done!"
        #print "---  Application  ------------------"
        #print app
        #print "------------------------------------"
         
        return app

   
    @staticmethod
    def __validate(data = {}):
        """
            Checking if user provided the Applications, relationships and the SLOs for the execution
        """
        #check for the required parameters describing an application
        
        print data.keys()
        for rf in ManifestParser.REQUIRED_FIELDS:
            if not data.has_key(rf):
                raise Exception("Missing field from manifest : <%s>." % rf)
              
              



#data = ManifestParser(manifest)
#data = ManifestParser().load({})
#print data
#print '\nENDEXE'

