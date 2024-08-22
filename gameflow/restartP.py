import serial
import time

# Replace '/dev/ttyACM0' with the correct port for your Pico
pico_port = '/dev/ttyACM0'
baud_rate = 115200

# Open serial connection to the Pico
ser = serial.Serial(pico_port, baud_rate, timeout=1)
time.sleep(2)  # Wait for the connection to initialize

# Send Ctrl+C to interrupt any running script and enter the REPL
ser.write(b'\x03')
time.sleep(1)

# Send the command to import the machine module with a carriage return and newline
ser.write(b'import machine\r\n')
time.sleep(1)

# Send the command to reset the Pico with a carriage return and newline
ser.write(b'machine.reset()\r\n')
time.sleep(1)

# Optionally, read the response from the Pico (if any)
response = ser.read_all().decode('utf-8')
print(response)

# Close the serial connection
ser.close()
