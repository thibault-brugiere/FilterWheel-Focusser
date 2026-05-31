# -*- coding: utf-8 -*-
"""
Created on Tue Oct 28 20:46:10 2025

@author: thbru
"""
import time as t

class Focuser:
    def __init__(self, port='COM14', baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self.connected = False
        self.connecting = False 
        self.currentPosition = 0
        self.moving = False
        self.lastError = None
        self.num_positions = 5  # Simulation : 5 filtres
        
        self.max_increment = 100
        self.absolute = True
        self.max_step = 5000
        self.step_size = 1
        self.temp_comp = False
        self.currentPosition = 2500

    #
    # ----- Connection and disconnection protocol -----
    #
    
    def connect(self):
        # Simulation simple
        self.connecting = True
        print("Simulated Focuser connected.")
        self.connected = True
        self.connecting = False
        
    def disconnect(self):
        print("Simulated Focuser disconnected.")
        self.connected = False
    
    #
    # ----- Return states of the wheel -----
    #
    def isConnected(self):
        return self.connected

    def isConnecting(self):
        return self.connecting
    
    def isMoving(self):
        return self.moving

    def get_position(self):
        if not self.connected:
            raise Exception("Focuser not connected")
        return int(self.currentPosition)
    
    #
    # --- Set the movement of focuser -----
    #
    
    def halt(self):
        """
        Stop the moovement
        """
        if not self.connected:
            raise Exception("Filter wheel not connected")
        return int(self.currentPosition)
    
    def move_to(self, position):
        """
        Move the focusser to an 

        Parameters
        ----------
        position : int
            absolute target position of the focusser
        Returns
        -------
        None.

        """
        if not self.connected:
            raise Exception("Focuser not connected")
        else :
            self.moving = True
            print(f"Moving focusser to position {position}")
            t.sleep(0.2)
            self.currentPosition = position
            self.moving = False
            