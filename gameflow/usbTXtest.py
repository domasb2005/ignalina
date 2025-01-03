import serial
import time
import pyudev

# Function to find the Arduino port based on a specific serial number
def find_arduino_port(target_serial="12648509806167176500"):
    context = pyudev.Context()
    
    for device in context.list_devices(subsystem='tty'):
        serial = device.get('ID_SERIAL_SHORT')  # Get the serial number
        dev_node = device.device_node  # Get the device node (e.g., /dev/ttyACM0)
        
        # Check if this device matches the target serial number
        if serial == target_serial:
            print(f"Found Arduino: Serial={serial}, Node={dev_node}")
            return dev_node  # Return the device node if found

    raise Exception("Arduino with specified serial number not found.")

# Main function
def main():
    try:
        # Find the Arduino port
        arduino_port = find_arduino_port()
        print(f"Arduino port: {arduino_port}")

        # Set up serial connection
        ser = serial.Serial(arduino_port, baudrate=9600, timeout=1)
        time.sleep(2)  # Allow some time for the connection to initialize

        # States to send
        states = [0, 1, 7]
        index = 0  # Index for the current state

        while True:
            state = states[index]  # Get the current state to send
            ser.write(f"{state}\n".encode())  # Send the state as a string with a newline
            print(f"Sent state: {state}")  # Print the sent state
            
            # Rotate the index to the next state
            index = (index + 1) % len(states)

            time.sleep(5)  # Delay between sends

    except Exception as e:
        print(e)

    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()  # Close the serial connection when done

if __name__ == "__main__":
    main()
