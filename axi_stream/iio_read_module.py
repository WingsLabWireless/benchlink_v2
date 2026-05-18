import iio
import time
import socket
import errno
import threading

class iioModule:
    
    def __init__(self):
        # Network config for forwarding the read buffer data
        self.dest_ip = "127.0.0.1"
        self.dest_port_rx = 52007 
        self.mpsoc_ip = "ip:192.168.3.2"

        # Initialize IIO buffer context
        self.initialize_device_context(
            ip=self.mpsoc_ip, 
            rx_device="mwipcore0:s2mm0", 
            rx_buffer_size=256*16
        )

    def initialize_udp_socket_rx(self):
        """Initializes the UDP socket for sending buffer data out."""
        return socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def initialize_device_context(self, ip="ip:192.168.3.2", rx_device=None, rx_buffer_size=None):
        """Sets up the IIO context, locates the device/channel, and creates the buffer."""
        self.ctx = iio.Context(ip)
        self.dev = self.ctx.find_device(rx_device)
        self.ctx.set_timeout(0)

        if self.dev is None:
            raise Exception(f"Could not find device '{rx_device}'")
        
        self.rx_chan = self.dev.find_channel("data0", False)
        
        if self.rx_chan is None:
            raise Exception("Could not find channel 'data0'")
            
        self.rx_chan.enabled = True
        self.rx_buf = iio.Buffer(self.dev, rx_buffer_size, False)

    def s2mm0_read_loop(self):
        """Main loop that continuously reads from the IIO buffer and sends over UDP."""
        udp_socket = self.initialize_udp_socket_rx()
        
        if self.rx_buf is None:
            raise Exception("Could not find Rx Buffer")
            
        print('IIO Read Started')
        
        while True:
            try:
                # Refill and read from IIO buffer
                self.rx_buf.refill()
                data = self.rx_buf.read()

                # Send data to UDP server
                udp_server_address = (self.dest_ip, self.dest_port_rx)
                udp_socket.sendto(data, udp_server_address)

            except OSError as e:
                if e.errno == errno.ETIMEDOUT:
                    print("Timeout occurred: No data received. Waiting for transmission to resume...")
                    time.sleep(0.001)
                else:
                    print(f"Unexpected OSError: {e}")
                    break
            except Exception as e:
                print(f"Unexpected error: {e}")
                break


if __name__ == "__main__":
    
    rf_iio = iioModule()

    print("Starting IIO Buffer Read...")
    read_thread = threading.Thread(target=rf_iio.s2mm0_read_loop, daemon=True)
    read_thread.start()

    try:
        # Keep the main thread alive while the daemon thread runs
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping IIO Buffer Read...")
