# -*- coding: utf-8 -*-
"""
Created on Fri Sep  5 09:40:41 2025

@author: tbrugiere
"""
import atexit
import serial
import time
import threading

class DeviceCOM:
    def __init__(self, port: str = 'COM14', baudrate: int = 9600):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.connect_count = 0
        
        self.lock = threading.Lock()
        atexit.register(self.closeEvent)

    def connect(self):
        if self.connect_count == 0 :
            try:
                self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
                time.sleep(2)  # Attendre la réinitialisation de l'Arduino
            except serial.SerialException as e:
                print(f"Erreur de connexion : {e}")
                return False
        
        self.connect_count += 1
        return True

    def close(self):
        if self.connect_count > 0 :
            self.connect_count -= 1
        
        if self.connect_count == 0 :
            if self.ser and self.ser.is_open:
                self.ser.close()
                print("Device disconnected")
    
    def closeEvent(self):
        self.connect_count == 0
        self.close()

    def cmd(self, commande: str):
        if self.ser and self.ser.is_open:
            self.ser.write((commande + '\n').encode())
            self.ser.flush()
    
    def cmd_resp(self, commande: str, timeout: float = 5.0):
        """
        Envoie une commande à l'Arduino et attend une réponse complète.
        S'arrête si 'OK', 'DONE' ou 'ERR' est reçu dans le flux série.
        """
        if not self.ser or not self.ser.is_open:
            return "Erreur : Port série non ouvert"
        
        self.ser.reset_input_buffer()
        self.ser.write((commande + '\n').encode())
        
        start_time = time.time()
        buffer = []
        while time.time() - start_time < timeout:
            if self.ser.in_waiting > 0:
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    print("→ Arduino:", line)  # log debug
                    buffer.append(line)
                    # Si la ligne contient un message de fin, on s'arrête
                    if any(kw in line.upper() for kw in ("OK", "DONE", "ERR")):
                        return "\n".join(buffer)
            time.sleep(0.01)
        
        return "Timeout: aucune réponse complète reçue"

    def read(self, timeout: float = 1.0):
        if not self.ser or not self.ser.is_open:
            return "Erreur : Port série non ouvert"
        start = time.time()
        response = ""
        while time.time() - start < timeout:
            if self.ser.in_waiting > 0:
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    response = line  # Garde la dernière ligne valide
            else:
                time.sleep(0.01)  # Évite de saturer le CPU
        return response if response else "Aucune donnée reçue"
    
    def move(self, steps: int, delay: int, direction: int = 0, timeout: float = 5.0):
        cmd = f"move {steps} {delay} {direction}"
        self.ser.reset_input_buffer()
        self.ser.write((cmd + '\n').encode())
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.ser.in_waiting > 0:
                response = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if response == "DONE":
                    return "OK: Déplacement terminé"
            time.sleep(0.01)
        return "Timeout: Déplacement non terminé"
    
# devicecom = DeviceCOM()