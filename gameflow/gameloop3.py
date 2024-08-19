import paho.mqtt.client as mqtt
import time
import threading
import serial
import pygame
import statecontroller
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

def is_button_pressed(button, serial_data):
    return serial_data and button in serial_data.split(', ')

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
    state = statecontroller.StateController()

    # MQTT Configuration
    MQTT_BROKER_HOST = "0.0.0.0"
    MQTT_BROKER_PORT = 1883

    # Variables to track timing and alarm state
    time_at_five = None
    time_at_six = None
    time_above_six = None
    alarm_active = False  # Track the state of the alarm
    current_percentage = None

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT broker successfully")
            client.subscribe("reactor/power_percentage")
        else:
            print(f"Failed to connect, return code {rc}")

    def on_message(client, userdata, msg):
        nonlocal current_percentage
        try:
            current_percentage = int(msg.payload.decode().strip())
            print(f"Received reactor power percentage: {current_percentage}%")
        except Exception as e:
            print(f"Error decoding message: {e}")

    def start_alarm():
        nonlocal alarm_active
        if not alarm_active:
            print("Starting alarm on main PC.")
            pygame.mixer.init()
            pygame.mixer.music.load("./data/danger.mp3")
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(-1)
            alarm_active = True

    def stop_alarm():
        nonlocal alarm_active
        if alarm_active:
            print("Stopping alarm on main PC.")
            pygame.mixer.music.stop()
            pygame.mixer.quit()
            alarm_active = False

    def disconnect_mqtt():
        print("Disconnecting from MQTT broker.")
        client.loop_stop()  # Stop the loop
        client.disconnect()  # Disconnect from the MQTT broker


    button_port, telephone_port = find_serial_ports()

    serial_reader_0 = SerialReader(button_port)
    serial_reader_1 = SerialReader(telephone_port)


    while True:


        if state.get_state() == "idle":
            if not hasattr(state, 'mqtt_initialized') or not state.mqtt_initialized:
                MQTT_BROKER_HOST = "0.0.0.0"
                MQTT_BROKER_PORT = 1883

                #connect to mqtt broker
                client = mqtt.Client()
                client.on_connect = on_connect
                client.on_message = on_message
                connected = False
                while not connected:
                    try:
                        client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
                        connected = True
                    except Exception as e:
                        print(f"Connection failed: {e}. Retrying in 5 seconds...")
                        time.sleep(5)
                client.loop_start()  # Start the MQTT loop to process messages

            client.publish("reactor/reset", "new_game")
            client.publish("pico/servo/control", "prepare")

            if not serial_reader_0.is_alive():
                serial_reader_0 = SerialReader(button_port)
                serial_reader_0.start()
            if  not serial_reader_1.is_alive():
                serial_reader_1 = SerialReader(telephone_port)
                serial_reader_1.start()

            state.set_infoscreen_state("idle")
            print("Waiting for button 0 to be pressed...")
            while state.get_state() == "idle":
                serial_data = serial_reader_0.get_data()
                if is_button_pressed('0', serial_data):
                    print("Button 0 is pressed")
                    state.set_state("initial_call")
                time.sleep(0.1)
        
        elif state.get_state() == "initial_call":
            state.set_infoscreen_state("initial_call")
            pygame.mixer.init()
            pygame.mixer.music.load("./data/ring.mp3")
            pygame.mixer.music.play(-1)
            print("Waiting for button Raised to be pressed...")
            while state.get_state() == "initial_call":
                serial_data = serial_reader_1.get_data()
                if is_button_pressed('Raised', serial_data):
                    print("Button Raised is pressed. Moving on with the rest of the code.")
                    state.set_state("initial_call_up")
                time.sleep(0.1)

        elif state.get_state() == "initial_call_up":
            state.set_infoscreen_state("initial_call_up")
            pygame.mixer.music.stop()
            pygame.mixer.quit()
            time.sleep(0.5)
            pygame.mixer.init(channels=1, devicename="SC")
            pygame.mixer.music.load("./data/call1.mp3")
            pygame.mixer.music.play()
            print("Waiting for button Putdown to be pressed...")
            while state.get_state() == "initial_call_up":
                serial_data = serial_reader_1.get_data()
                if is_button_pressed('Putdown', serial_data):
                    print("Button Putdown is pressed. Moving on with the rest of the code.")
                    pygame.mixer.quit()
                    state.set_state("second_call")
                time.sleep(0.1)

        elif state.get_state() == "dial_up":
            correct_number = "1124" 
            entered_number = ""

            state.set_infoscreen_state("dial_up")
            print("Please enter the 4-digit number")

            while state.get_state() == "dial_up":
                serial_data = serial_reader_1.get_data()
                if serial_data and serial_data.isdigit():
                    entered_number += serial_data
                    print(f"Current entered number: {entered_number}")

                    if len(entered_number) == 4:
                        if entered_number == correct_number:
                            print("Correct number entered!")
                            state.set_state("second_call_up")
                        else:
                            print("Incorrect number. Please try again.")
                            state.set_infoscreen_state("wrong_number")
                            entered_number = ""  # Reset entered number for retry

                time.sleep(0.1)  # Sleep for 100 milliseconds

        elif state.get_state() == "second_call":
            print("Waiting for button Raised to be pressed...")
            while state.get_state() == "second_call":
                serial_data = serial_reader_1.get_data()
                if is_button_pressed('Raised', serial_data):
                    print("Button Raised is pressed. Moving on with the rest of the code.")
                    state.set_state("dial_up")
                time.sleep(0.1)

        elif state.get_state() == "second_call_up":
            state.set_infoscreen_state("initial_call_up")
            time.sleep(0.5)
            pygame.mixer.init(channels=1, devicename="SC")
            pygame.mixer.music.load("./data/call2.mp3")
            pygame.mixer.music.play()
            print("Waiting for button Putdown to be pressed...")
            while state.get_state() == "second_call_up":
                serial_data = serial_reader_1.get_data()
                if is_button_pressed('Putdown', serial_data):
                    print("Button Putdown is pressed. Moving on with the rest of the code.")
                    pygame.mixer.quit()
                    state.set_state("backup_generators")
                time.sleep(0.1)
        
        elif state.get_state() == "backup_generators":
            state.set_infoscreen_state("backup_generators")
            print("Waiting for button 1 to be pressed...")
            while state.get_state() == "backup_generators":
                serial_data = serial_reader_0.get_data()
                if is_button_pressed('1', serial_data):
                    print("Button 1 is pressed. Moving on with the rest of the code.")
                    state.set_state("backup_pumps")
                time.sleep(0.1)

        elif state.get_state() == "backup_pumps":
            print("Waiting for button 2 to be pressed...")
            while state.get_state() == "backup_pumps":
                serial_data = serial_reader_0.get_data()
                if is_button_pressed('2', serial_data):
                    print("Button 2 is pressed. Moving on with the rest of the code.")
                    state.set_state("circulation_pump")
                time.sleep(0.1)
        
        elif state.get_state() == "circulation_pump":
            print("Waiting for button 3 to be pressed...")
            state.set_infoscreen_state("circulation_pump")
            while state.get_state() == "circulation_pump":
                serial_data = serial_reader_0.get_data()
                if is_button_pressed('3', serial_data):
                    print("Button 3 is pressed. Moving on with the rest of the code.")
                    state.set_state("condenser")
                time.sleep(0.1)
        
        elif state.get_state() == "condenser":
            state.set_infoscreen_state("condenser")
            print("Waiting for button 4 to be pressed...")
            while state.get_state() == "condenser":
                serial_data = serial_reader_0.get_data()
                if is_button_pressed('4', serial_data):
                    print("Button 4 is pressed. Moving on with the rest of the code.")
                    state.set_state("water_cleaning")
                time.sleep(0.1)
        
        elif state.get_state() == "water_cleaning":
            print("Waiting for button 5 to be pressed...")
            state.set_infoscreen_state("water_cleaning")
            while state.get_state() == "water_cleaning":
                serial_data = serial_reader_0.get_data()
                if is_button_pressed('5', serial_data):
                    print("Button 5 is pressed. Moving on with the rest of the code.")
                    state.set_state("idle_pump")
                time.sleep(0.1)
        
        elif state.get_state() == "idle_pump":
            print("Waiting for button 6 to be pressed...")
            state.set_infoscreen_state("idle_pump")
            while state.get_state() == "idle_pump":
                serial_data = serial_reader_0.get_data()
                if is_button_pressed('6', serial_data):
                    print("Button 6 is pressed. Moving on with the rest of the code.")
                    state.set_state("main_pump")
                time.sleep(0.1)
        
        elif state.get_state() == "main_pump": 
            state.set_infoscreen_state("main_pump")
            print("Waiting for button 7 to be pressed...")
            while state.get_state() == "main_pump":
                serial_data = serial_reader_0.get_data()
                if is_button_pressed('7', serial_data): 
                    print("Button 7 is pressed. Moving on with the rest of the code.") 
                    state.set_state("control_rods") 
                time.sleep(0.1)
        
        elif state.get_state() == "control_rods": 
            # Check if the MQTT client is already connected
            if not hasattr(state, 'mqtt_initialized') or not state.mqtt_initialized:
                # MQTT Client Setup
                client = mqtt.Client()
                client.on_connect = on_connect
                client.on_message = on_message

                connected = False
                while not connected:
                    try:
                        client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
                        connected = True
                    except Exception as e:
                        print(f"Connection failed: {e}. Retrying in 5 seconds...")
                        time.sleep(5)

                client.loop_start()  # Start the MQTT loop to process messages

                # Mark the MQTT client as initialized
                state.mqtt_initialized = True

            print("Control rods state is active, processing logic...")
            if current_percentage is not None:
                if current_percentage < 5:
                    if alarm_active:
                        stop_alarm()
                    time_at_five = time_at_six = time_above_six = None
                    current_percentage = None  # Reset current_percentage after handling

                elif current_percentage == 5:
                    if time_at_five is None:
                        time_at_five = time.time()
                        print("Starting timer for state 'waiting'.")
                    elif time.time() - time_at_five >= 3:
                        print("Message has been 5 for 3 consecutive seconds. Changing state to 'waiting'.")
                        state.set_state("waiting")
                        stop_alarm()
                        time_at_five = None
                        current_percentage = None  # Reset current_percentage after handling

                elif current_percentage == 6:
                    if time_at_six is None:
                        time_at_six = time.time()
                        print("Starting timer for state 'game_early_end_timeout'.")
                    elif time.time() - time_at_six >= 10:
                        print("Message has been 6 for 10 consecutive seconds. Resetting percentage to 0.")
                        stop_alarm()
                        state.set_state("game_early_end_timeout")
                        time_at_six = None
                        current_percentage = None  # Reset current_percentage after handling

                    if not alarm_active and current_percentage is not None:
                        start_alarm()

                elif current_percentage > 6:
                    if time_above_six is None:
                        time_above_six = time.time()
                        print("Starting timer for state 'game_early_end_timeout' due to >6%.")
                    elif time.time() - time_above_six >= 3:
                        print("Message has been above 6 for 3 consecutive seconds. Resetting percentage to 0.")
                        stop_alarm()
                        state.set_state("game_early_end_timeout")
                        time_above_six = None
                        current_percentage = None  # Reset current_percentage after handling

                    if not alarm_active and current_percentage is not None:
                        start_alarm()

                else:
                    if alarm_active:
                        stop_alarm()
                    time_at_five = time_at_six = time_above_six = None
                    current_percentage = None  # Reset current_percentage after handling

            time.sleep(1)  # Prevent tight looping


        elif state.get_state() == "waiting":
            pygame.mixer.quit()
            state.set_infoscreen_state("waiting")
            client.publish("pico/servo/control", "start")
            time.sleep(18)
            state.set_state("turbine_startup")

        elif state.get_state() == "turbine_startup": 
            state.set_infoscreen_state("turbine_startup")
            print("Waiting for button 8 to be pressed...")
            while state.get_state() == "turbine_startup":
                serial_data = serial_reader_0.get_data()
                if is_button_pressed('8', serial_data): 
                    print("Button 8 is pressed. Moving on with the rest of the code.") 
                    state.set_state("turbine_connection") 
                time.sleep(0.1)
        
        elif state.get_state() == "turbine_connection": 
            state.set_infoscreen_state("turbine_connection")
            print("Waiting for button 9 to be pressed...")
            while state.get_state() == "turbine_connection":
                serial_data = serial_reader_0.get_data()
                if is_button_pressed('9', serial_data): 
                    print("Button 9 is pressed. Moving on with the rest of the code.") 
                    state.set_state("steam_connection") 
                time.sleep(0.1)
        
        elif state.get_state() == "steam_connection": 
            state.set_infoscreen_state("steam_connection")
            print("Waiting for button 10 to be pressed...")
            while state.get_state() == "steam_connection":
                serial_data = serial_reader_0.get_data()
                if is_button_pressed('10', serial_data): 
                    print("Button 10 is pressed. Moving on with the rest of the code.") 
                    state.set_state("power_up") 
                time.sleep(0.1)
        
        elif state.get_state() == "power_up": 
            state.set_infoscreen_state("power_up")
            print("Waiting for button 11 to be pressed...")
            while state.get_state() == "power_up":
                serial_data = serial_reader_0.get_data()
                if is_button_pressed('11', serial_data): 
                    print("Button 11 is pressed. Moving on with the rest of the code.") 
                    state.set_state("game_end") 
                time.sleep(0.1)
        

        elif state.get_state() == "game_early_end_timeout":
            pygame.mixer.quit()
            state.set_infoscreen_state("game_early_end_timeout")
            serial_reader_0.stop()
            serial_reader_1.stop()
            time.sleep(30)
            state.set_state("idle")

        
        elif state.get_state() == "game_end": 
            state.set_infoscreen_state("game_end")
            serial_reader_0.stop()
            serial_reader_1.stop()
            time.sleep(30)
            state.set_state("idle")



        

if __name__ == "__main__":
    main()
