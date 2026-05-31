# -*- coding: utf-8 -*-
"""
Created on Tue Oct 28 20:46:10 2025

@author: thbru
"""

class FilterWheel:
    def __init__(self, port='COM14', baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self.connected = False
        self.connecting = False 
        self.currentPosition = 0
        self.currentAngle = 0.0
        self.moving = False
        self.lastError = None
        self.num_positions = 5  # Simulation : 5 filtres
        self.filter_names = ["Luminance", "Red", "Green", "Blue", "Ha"]
        self.filter_positions = [0.0, 72.0, 144, 216, 288]
        self.focus_offsets = [0, 0, 0, 0, 0]


    #
    # ----- Connection and disconnection protocol -----
    #
    
    def connect(self):
        # Simulation simple
        self.connecting = True
        print("Simulated filter wheel connected.")
        self.connected = True
        self.connecting = False
        
    def disconnect(self):
        print("Simulated filter wheel disconnected.")
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
    
        # Simule un déplacement (plus tard : envoi d'une commande série à l'Arduino)
        self.moving = True
        print(f"Moving filter wheel to position {position} ({self.filter_names[position]})")
    
        # Ici tu pourrais envoyer : serial.write(f"SET_POS#{position}\n".encode())
        # ou gérer le retour de ton Arduino.
    
        self.currentPosition = position
        self.moving = False