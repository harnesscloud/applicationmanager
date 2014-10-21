#!/usr/bin/env python
from application.provisioner.connections import CrossResourceSchedulerConnection
import time
import subprocess

class ReservationManager:
    
    @staticmethod
    def acquire_resources(configuration):
        "Require the scheduling of the configuration."
        reservation = ReservationManager.__prepare_resources(configuration)        
        "Starting the reservation."
        #print "Reservation prepared : ", reservation
        reservation.update(ReservationManager.__deploy_resources(reservation["ConfigID"]))
        while True:
            time.sleep(5)
            state, addresses = ReservationManager.check_reservation(reservation["ResID"])
            if state:
                for i in range(len(reservation["Resources"])):
                    reservation["Resources"][i]["IP"] = addresses[i]
                break
            

        print "Sleep while machines are booting."
        time.sleep(230)	
        return reservation
              
    @staticmethod
    def __prepare_resources(configuration, trials = 3):
        """
            Schedule the required configuration 
                * searching hosts with available resources
                * reserve resources on hosts for the future deployment of virtual machines
        """
        if trials == 0:
            return
        provisioner = CrossResourceSchedulerConnection()
        
        "Preparing for a reservation"
        try:
            result = provisioner.prepareReservation(configuration)
            if result == None:
                raise Exception()
        except:
            return ReservationManager.__prepare_resources(configuration, trials - 1)
        
       
        return result

    @staticmethod
    def __deploy_resources(configurationID, trials = 3):
        """
            Starting the reservation 
                * machine deployment 
                * booting
        """
        if trials == 0:
            return
        provisioner = CrossResourceSchedulerConnection()
        
        "Preparing for a reservation"
        try:
            result = provisioner.createReservation(configurationID)
            if result == None:
                raise Exception()
        except:
            return ReservationManager.__deploy_resources(configurationID, trials - 1)
        
        return result

    @staticmethod
    def check_reservation(reservationID):
        
        provisioner = CrossResourceSchedulerConnection()
        result = provisioner.checkReservation(reservationID)
        if not result["Ready"]:
            return False, []
        return result["Ready"], result["Addresses"]    

    @staticmethod
    def release_resources(reservationID):
        """
            Releasing all the reserved resources
        """
        print "Releasing resources..."
        provisioner = CrossResourceSchedulerConnection()
        provisioner.releaseReservation(reservationID)

            
            
