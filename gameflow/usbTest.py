import threading
import serial
import time
import pyudev

# Define the SerialReader class
class SerialReader(threading.Thread):
    def __init__(self, port, baudrate=115200, timeout=1):
        threading.Thread.__init__(self)
        self.serial_port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = serial.Serial(self.serial_port, self.baudrate, timeout=self.timeout)
        self.serial_data = None
        self.running = True

    def run(self):
        while self.running:
            if self.ser.in_waiting > 0:
                self.serial_data = self.ser.readline().decode('utf-8').strip()

    def stop(self):
        self.running = False
        self.ser.close()

    def get_data(self):
        data = self.serial_data
        self.serial_data = None
        return data

# Function to find and correctly assign the serial ports
def find_serial_ports():
    context = pyudev.Context()
    found_ports = {}

    for device in context.list_devices(subsystem='tty'):
        if 'ID_VENDOR_ID' in device and 'ID_MODEL_ID' in device:
            vid = device.get('ID_VENDOR_ID')
            pid = device.get('ID_MODEL_ID')
            dev_node = device.device_node
            serial = device.get('ID_SERIAL_SHORT')  # Unique serial number
            print(f"Found device: VID={vid}, PID={pid}, Node={dev_node}, Serial={serial}")

            # Match the serial number to the correct device
            if serial == "e66141040383622c":  # Serial number for Buttons
                found_ports['telephone'] = dev_node
            elif serial == "e6614104035f442e":  # Serial number for Telephone
                found_ports['buttons'] = dev_node

    if 'buttons' not in found_ports or 'telephone' not in found_ports:
        raise Exception("Unable to find both required serial ports. Check device connections.")

    return found_ports['buttons'], found_ports['telephone']

# Main function
def main():
    try:
        button_port, telephone_port = find_serial_ports()
        print(f"Button port: {button_port}, Telephone port: {telephone_port}")

        # Initialize and start SerialReaders for both devices
        serial_reader_buttons = SerialReader(button_port)
        serial_reader_telephone = SerialReader(telephone_port)
        serial_reader_buttons.start()
        serial_reader_telephone.start()

    except Exception as e:
        print(e)
        return

    try:
        while True:
            # Get and print data from the buttons serial reader
            data_buttons = serial_reader_buttons.get_data()
            if data_buttons:
                print(f"Buttons serial received: {data_buttons}")

            # Get and print data from the telephone serial reader
            data_telephone = serial_reader_telephone.get_data()
            if data_telephone:
                print(f"Telephone serial received: {data_telephone}")
            
            time.sleep(0.1)  # Sleep for a short time to prevent high CPU usage

    except KeyboardInterrupt:
        print("Stopping serial readers...")
        serial_reader_buttons.stop()
        serial_reader_telephone.stop()

if __name__ == "__main__":
    main()
