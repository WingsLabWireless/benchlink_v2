import socket
import struct
import csv 

HOST = '127.0.0.1'
PORT = 52007
BUFFER_SIZE = 960
CSV_FILE_NAME = 'output.csv'

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HOST, PORT))

try:
    with open(CSV_FILE_NAME, mode='w', newline='') as file:
        csv_writer = csv.writer(file)
        print(f"Listening on {HOST}:{PORT}... Logging to {CSV_FILE_NAME}")
        
        while True:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            
            if not data:
                break
                
            # Unpack 960 bytes into 240 unsigned 32-bit integers
            unpacked_data = struct.unpack('<240I', data)
            
            # Write the data as a new row in the CSV
            csv_writer.writerow(unpacked_data)
            
except KeyboardInterrupt:
    print("\nProgram interrupted. Server stopped.")
finally:
    sock.close()
