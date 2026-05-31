# -*- coding: utf-8 -*-
"""
Created on Tue Oct 28 20:46:10 2025

@author: thbru
"""
import json
from pathlib import Path
import time

from device_com import DeviceCOM

class Focuser:
    def __init__(self, port='COM23', baudrate=9600):
        self.port = port
        self.baudrate = baudrate
        
        self.foc = DeviceCOM(port)
        
        self._names_sent_once = False
        
        self.serial = None
        self.connected = False
        self.connecting = False 
        self.currentPosition = 0
        self.moving = False
        self.lastError = None
        
        self.max_increment = 200
        self.absolute = True
        self.max_step = 10000
        self.step_size = 1
        self.temp_comp = False
        self.currentPosition = 5000
        
        print("""Dans NINA → Options → ASCOM Alpaca, vérifier que Discovery port = 32227
              =>Resolve DNS name : OFF =>Use ipv4 ON =>Use HTTPS OFF =>Use ipv6 OFF""")


    #
    # ----- Connection and disconnection protocol -----
    #
    
    def connect(self):
        if self.connected or self.connecting:
            print("Déjà connecté ou en cours de connexion à la roue.")
            return True
    
        self.connecting = True
        
        try:
            config_path = Path(__file__).parent / "filterwheel_parameters.json" # Todo modifié ici
            
            with open(config_path, encoding="utf-8") as f:
                params = json.load(f)
                self.foc.port = params.get("port_foc", self.foc.port)
                self.step_size = params.get("step_size")
                self.foc.baudrate = params.get("baudrate", self.foc.baudrate)
                print("Paramètres chargés depuis filterwheel_parameters.json")
        except Exception as e:
            print(f"Impossible de charger les paramètres JSON : {e}")
        
        if not self.foc.connect():  # renvoie True/False
            self.connecting = False
            raise Exception("Impossible de se connecter au focuser")
        
        
        # Attendre que l'Arduino signale qu'il est prêt
        start_time = time.time()
        while True:
            line = self.foc.ser.readline().decode(errors='ignore').strip()
            if "READY" in line:
                break
            if time.time() - start_time > 5:  # timeout 10s
                self.connecting = False
                raise Exception("Arduino non prêt après 5s")
        
        self.connected = True
        time.sleep(1)
        self.connecting = False
        
    def disconnect(self):
        self.foc.close()
        self.connected = False
    
    #
    # ----- Return states of the wheel -----
    #
    def isConnected(self):
        return self.connected

    def isConnecting(self):
        return self.connecting
    
    def isMoving(self):
        time.sleep(0.05)
        return self.moving

    def get_position(self):
        time.sleep(0.05)
        if not self.connected:
            raise Exception("Filter wheel not connected")
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
    
    def move_to(self, position): #TODO à coder ici pour l'arduino
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
            
        if position < 0 or position >= self.max_step :
            raise ValueError(f"Invalid focuser position: {position}/{self.max_step}")
            
        steps = position - self.currentPosition
        if steps > 0 :
            direction = 1
        else:
            steps = -steps
            direction = 0
        
        self.moving = True
        print(f"Moving focusser to position {position}")
        time.sleep(0.2)
        move = self.foc.move(steps * self.step_size, 500, direction)
        
        if move.startswith("ERR"):
            raise Exception(f"Focuser error: {move}")
        
        self.currentPosition = position
        self.moving = False
            