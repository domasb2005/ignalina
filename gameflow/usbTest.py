import threading
import serial
import time
import pyudev

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
    
def find_serial_ports():
    context = pyudev.Context()
    found_ports = []

    for device in context.list_devices(subsystem='tty'):
        if 'ID_VENDOR_ID' in device and 'ID_MODEL_ID' in device:
            vid = device.get('ID_VENDOR_ID')
            pid = device.get('ID_MODEL_ID')
            dev_node = device.device_node

            if vid == '2e8a' and pid == '0005':
                found_ports.append(dev_node)

    if len(found_ports) < 2:
        raise Exception("Unable to find the required serial ports. Check device connections.")

    # Assign the first found port to button_port and the second to telephone_port
    button_port = found_ports[0]
    telephone_port = found_ports[1]
    
    return button_port, telephone_port


def main():

    button_port, telephone_port = find_serial_ports()

    serial_reader_0 = SerialReader(button_port)
    serial_reader_1 = SerialReader(telephone_port)

    
    # Start the serial reader threads
    serial_reader_0.start()
    serial_reader_1.start()

    try:
        while True:
            # Get and print data from the first serial reader
            data_0 = serial_reader_0.get_data()
            if data_0:
                print(f"Serial 0 received: {data_0}")

            # Get and print data from the second serial reader
            data_1 = serial_reader_1.get_data()
            if data_1:
                print(f"Serial 1 received: {data_1}")
            
            time.sleep(0.1)  # Sleep for a short time to prevent high CPU usage

    except KeyboardInterrupt:
        print("Stopping serial readers...")
        serial_reader_0.stop()
        serial_reader_1.stop()

if __name__ == "__main__":
    main()
