import random
import numpy as np
import socket
import time

def send_packet(data):
    UDP_IP = "127.0.0.1"
    UDP_PORT = 12345

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(data, (UDP_IP, UDP_PORT))

try:
    while True:
        sym = range(64)
        original_array = np.random.choice(sym, size=240)
        
        final_array = original_array
        final_array = final_array.astype(np.uint32)
        
        repeated_array = np.tile(final_array, 8)
        
        send_packet(repeated_array)
        time.sleep(0.003)
        
except KeyboardInterrupt:
    print("\nProgram interrupted. Sending stopped.")
