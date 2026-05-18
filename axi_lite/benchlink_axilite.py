import paramiko
import time

class AxiRemoteController:
    def __init__(self, ip, username, password):
        self.ip = ip
        self.username = username
        self.password = password
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
    def connect(self):
        self.ssh.connect(self.ip, username=self.username, password=self.password)

    def read_axi_register(self, base_addr, offset):
        '''
        Executes a single AXI-Lite memory-mapped read using devmem over SSH.
        '''
        target_addr = base_addr + offset
        
        # Omit the value argument to perform a read
        command = f"devmem 0x{target_addr:X} 32"
        
        stdin, stdout, stderr = self.ssh.exec_command(command)
        error = stderr.read().decode().strip()
        result = stdout.read().decode().strip()
        
        if error:
            print(f"AXI Read Error at 0x{target_addr:X}: {error}")
            return None
            
        print(f"AXI Read Success: 0x{target_addr:X} = {result}")
        return result

    def write_register(self, base_addr, offset, value):
        # Calculate the absolute physical address
        target_addr = base_addr + offset
        
        # Format the devmem command (e.g., 'devmem 0x8000012C 32 0x2')
        command = f"devmem 0x{target_addr:X} 32 0x{value:X}"
        
        stdin, stdout, stderr = self.ssh.exec_command(command)
        error = stderr.read().decode().strip()
        if error:
            print(f"Error writing to AXI at 0x{target_addr:X}: {error}")
        else:
            print(f"AXI Write Success: 0x{target_addr:X} = 0x{value:X}")

    def disconnect(self):
        self.ssh.close()

# --- Execution Block ---
if __name__ == "__main__":
    # Register Definitions
    AXI_BASE_ADDR = 0x80000000
    AXI_TX_CODE = 0x104
    AXI_TX_ENB = 0x108
    AXI_AGC_ENB =  0x10C
    AXI_CFC_ENB = 0x110
    AXI_EQ_ENB = 0x114
    AXI_CFC_THRESHOLD = 0x11C
    AXI_PD_THRESHOLD = 0x120
    AXI_RX_CODE = 0x128
    AXI_CFC_AVG_ENB = 0x144
    AXI_MULTICODE_TX = 0x124
    AXI_MULTICODE_RX = 0X13C
    
    # Replace with your board's credentials
    axi_ctrl = AxiRemoteController("192.168.3.2", "root", "root") 
    
    print("Connecting to target...")
    axi_ctrl.connect()
    print("Connected.")
    
    try:
        print("Initializing AXI registers...")
        
        # Initialize AXI values using the write_register method
        axi_ctrl.write_register(AXI_BASE_ADDR, AXI_TX_ENB, 1) 
        axi_ctrl.write_register(AXI_BASE_ADDR, AXI_AGC_ENB, 1)
        axi_ctrl.write_register(AXI_BASE_ADDR, AXI_CFC_ENB, 1)
        axi_ctrl.write_register(AXI_BASE_ADDR, AXI_EQ_ENB, 1)
        axi_ctrl.write_register(AXI_BASE_ADDR, AXI_CFC_THRESHOLD, 90)
        axi_ctrl.write_register(AXI_BASE_ADDR, AXI_PD_THRESHOLD, 50)
        axi_ctrl.write_register(AXI_BASE_ADDR, AXI_CFC_AVG_ENB, 1)
        axi_ctrl.write_register(AXI_BASE_ADDR, AXI_TX_CODE, 85)
        axi_ctrl.write_register(AXI_BASE_ADDR, AXI_RX_CODE, 85)
        axi_ctrl.write_register(AXI_BASE_ADDR, AXI_MULTICODE_TX, 0)
        axi_ctrl.write_register(AXI_BASE_ADDR, AXI_MULTICODE_RX, 0)
        
        print("Initialization complete.")
        
    except KeyboardInterrupt:
        print("Execution interrupted by user.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        axi_ctrl.disconnect()
        print("Disconnected.")
