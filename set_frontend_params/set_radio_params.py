import iio

class AD9361Controller:
    def __init__(self, ip="ip:192.168.3.2"):
        """Initializes the IIO context and connects to the AD9361 device."""
        self.mpsoc_ip = ip
        
        print(f"Connecting to IIO context at {self.mpsoc_ip}...")
        self.ctx = iio.Context(self.mpsoc_ip)

        # Find ad9361-phy device
        self.ad9361 = self.ctx.find_device("ad9361-phy")

        if self.ad9361 is None:
            raise Exception("Device 'ad9361-phy' not found. Check network connection and device tree.")
        else:
            print("Successfully connected to ad9361-phy.")

    # ==========================================
    # TX Control
    # ==========================================
    def set_tx_gain(self, gain_value):
        """Sets the TX hardware gain."""
        voltage0_out = self.ad9361.find_channel("voltage0", is_output=True)
        if voltage0_out is None:
            raise Exception("Channel 'voltage0' (TX) not found.")
        
        voltage0_out.attrs["hardwaregain"].value = str(gain_value)
        print(f"TX Gain set to {gain_value}")

    def get_tx_gain(self):
        """Gets the current TX hardware gain."""
        voltage0_out = self.ad9361.find_channel("voltage0", is_output=True)
        return voltage0_out.attrs["hardwaregain"].value

    def set_tx_freq(self, freq_value):
        """Sets the TX local oscillator (LO) frequency in Hz."""
        tx_lo = self.ad9361.find_channel("TX_LO", is_output=True)
        if tx_lo is None:
            raise Exception("Channel 'TX_LO' not found.")
        
        tx_lo.attrs["frequency"].value = str(freq_value)
        print(f"TX Frequency set to {freq_value} Hz")

    def get_tx_freq(self):
        """Gets the current TX local oscillator (LO) frequency."""
        tx_lo = self.ad9361.find_channel("TX_LO", is_output=True)
        return tx_lo.attrs["frequency"].value

    # ==========================================
    # RX Control
    # ==========================================
    def set_rx_gain(self, gain_value):
        """Sets the RX hardware gain."""
        voltage0_in = self.ad9361.find_channel("voltage0", is_output=False)
        if voltage0_in is None:
            raise Exception("Channel 'voltage0' (RX) not found.")
        
        voltage0_in.attrs["hardwaregain"].value = str(gain_value)
        print(f"RX Gain set to {gain_value}")

    def get_rx_gain(self):
        """Gets the current RX hardware gain."""
        voltage0_in = self.ad9361.find_channel("voltage0", is_output=False)
        return voltage0_in.attrs["hardwaregain"].value

    def set_rx_freq(self, freq_value):
        """Sets the RX local oscillator (LO) frequency in Hz."""
        rx_lo = self.ad9361.find_channel("RX_LO", is_output=True)
        if rx_lo is None:
            raise Exception("Channel 'RX_LO' not found.")
        
        rx_lo.attrs["frequency"].value = str(freq_value)
        print(f"RX Frequency set to {freq_value} Hz")

    def get_rx_freq(self):
        """Gets the current RX local oscillator (LO) frequency."""
        rx_lo = self.ad9361.find_channel("RX_LO", is_output=True)
        return rx_lo.attrs["frequency"].value


if __name__ == "__main__":
    # Minimal execution block to demonstrate usage
    try:
        # Initialize the radio controller
        radio = AD9361Controller(ip="ip:192.168.3.2")

        print("\n--- Applying New Settings ---")
        # Set Frequency (e.g., 2.4 GHz)
        radio.set_tx_freq(2400000000)
        radio.set_rx_freq(2400000000)

        # Set Gain (Check your specific AD9361 config for valid ranges)
        radio.set_tx_gain(-10) 
        radio.set_rx_gain(15)  

        print("\n--- Verifying Settings ---")
        print(f"Current TX Freq: {radio.get_tx_freq()} Hz")
        print(f"Current RX Freq: {radio.get_rx_freq()} Hz")
        print(f"Current TX Gain: {radio.get_tx_gain()} dB")
        print(f"Current RX Gain: {radio.get_rx_gain()} dB")

    except Exception as e:
        print(f"An error occurred: {e}")
