import serial
import time

def test_port(port):
    try:
        ser = serial.Serial(port, baudrate=115200, timeout=1)
        print(f"Opened port: {port} with baudrate: 115200")
    except serial.SerialException as e:
        print(f"Failed to open port {port}: {e}")
        return

    try:
        while True:
            if ser.in_waiting > 0:
                data = ser.readline().decode('utf-8').strip()
                if data:
                    print(f"Received on {port}: {data}")
                else:
                    print(f"Received empty line on {port}")
            else:
                print(f"No data waiting on {port}")
            time.sleep(0.5)
    except KeyboardInterrupt:
        print(f"Stopping serial reader on {port}...")
    finally:
        ser.close()
        print(f"Closed serial port {port}")

# Test /dev/ttyACM0
test_port('/dev/ttyACM0')

# Test /dev/ttyACM1
test_port('/dev/ttyACM1')
