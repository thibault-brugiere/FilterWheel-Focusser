# -*- coding: utf-8 -*-
"""
Created on Tue Oct 28 20:46:10 2025

@author: thbru
"""
import json
import time

from device_com import DeviceCOM

class FilterWheel:
    def __init__(self, port='COM20', baudrate=9600):
        self.port = port
        self.baudrate = baudrate
        
        self.fw = DeviceCOM()
        
        self._names_sent_once = False
        
        self.serial = None
        self.connected = False
        self.connecting = False 
        self.currentPosition = 0
        self.currentAngle = 0.0
        self.moving = False
        self.lastError = None
        self.num_positions = 8  # Simulation : 5 filtres
        self.filter_names = ["Luminance", "Red", "Green", "Blue", "None", "None", "None", "None"]
        self.filter_positions = [35.0, 80.0, 125.0, 170.0, 215.0, 260.0, 305.0, 360.0]
        self.focus_offsets = [0, 0, 0, 0, 0, 0, 0, 0]
        
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
            with open("filterwheel_parameters.json", "r", encoding="utf-8") as f:
                params = json.load(f)
                self.fw.port = params.get("port", self.fw.port)
                self.fw.baudrate = params.get("baudrate", self.fw.baudrate)
                self.num_positions = params.get("num_positions", self.num_positions)
                self.filter_names = params.get("filter_names", self.filter_names)
                self.filter_positions = params.get("filter_positions", self.filter_positions)
                self.focus_offsets = params.get("focus_offsets", self.focus_offsets)
                print("Paramètres chargés depuis filterwheel_parameters.json")
        except Exception as e:
            print(f"Impossible de charger les paramètres JSON : {e}")
        
        if not self.fw.connect():  # renvoie True/False
            self.connecting = False
            raise Exception("Impossible de se connecter à la roue")
        
        
        # Attendre que l'Arduino signale qu'il est prêt
        start_time = time.time()
        while True:
            line = self.fw.ser.readline().decode(errors='ignore').strip()
            if "READY" in line:
                self.connecting = False
                break
            if time.time() - start_time > 10:  # timeout 10s
                self.connecting = False
                raise Exception("Arduino non prêt après 10s")
        
        self.connected = True 
        self.set_position(0)
        time.sleep(1)
        self.connecting = False
        
    def disconnect(self):
        self.fw.close()
        self.connected = False
        self.connecting =  False
    
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
            raise Exception("Filter wheel not connected")
        return int(self.currentPosition)
    
    def get_names(self):
        """
        Renvoie la liste des noms de filtres sous forme de chaînes,
        avec exactement self.num_positions éléments.
        Ajoute 'None' si la liste est trop courte, tronque si trop longue.
        """
        names = [str(f) if f is not None else 'None' for f in self.filter_names]
        # Ajuste la longueur
        if len(names) < self.num_positions:
            names += ['None'] * (self.num_positions - len(names))
        elif len(names) > self.num_positions:
            names = names[:self.num_positions]
        return names
            
    def get_focus_offsets(self):
        """
        Renvoie la liste des offsets de focus sous forme d'entiers,
        avec exactement self.num_positions éléments.
        Ajoute 0 si la liste est trop courte, tronque si trop longue.
        """
        offsets = [int(f) if f is not None else 0 for f in self.focus_offsets]
        # Ajuste la longueur
        if len(offsets) < self.num_positions:
            offsets += [0] * (self.num_positions - len(offsets))
        elif len(offsets) > self.num_positions:
            offsets = offsets[:self.num_positions]
        return offsets
    
    #
    # --- Set the movement of the wheel -----
    #
    
    def set_position(self, position: int):
        """Déplace la roue vers la position demandée."""
        if not self.connected:
            raise Exception("Filter wheel not connected")
    
        if position < 0 or position >= len(self.filter_names):
            raise ValueError(f"Invalid filter position: {position}")
    
        move = self.fw.cmd_resp(f'goto {self.filter_positions[position]}')

        if move.startswith("ERR"):
            raise Exception(f"Filter wheel error: {move}")
    
        self.currentPosition = position
        self.moving = False