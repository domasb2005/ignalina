import serial

# Replace '/dev/ttyACM0' with your actual port name
ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)

def read_button_states():
    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').strip()
            print(f"Buttons pressed: {line}")
            if '0' in line.split(', '):
                print("HELLO")

if __name__ == "__main__":
    try:
        read_button_states()
    except KeyboardInterrupt:
        print("Exiting program.")
    finally:
        ser.close()
