import paho.mqtt.client as mqtt
import time
import threading
import serial
import pygame
import statecontroller
import pyudev

import pygame
import subprocess
import time

# Mapping device names to indices
DEVICE_MAP = {
    "phone": "alsa_output.usb-C-Media_Electronics_Inc._USB_PnP_Sound_Device-00.analog-stereo-output",
    "ringer": "alsa_output.pci-0000_00_1b.0.analog-stereo",
    "speaker": "alsa_output.usb-GeneralPlus_USB_Audio_Device-00.analog-stereo"
}

def set_default_sink(sink_name):
    """Set the default audio sink (output device)."""
    try:
        subprocess.run(["pactl", "set-default-sink", sink_name], check=True)
        print(f"Default sink set to: {sink_name}")
    except subprocess.CalledProcessError as e:
        print(f"Error setting default sink: {e}")

def play_through_specific(deviceName, volume, loop, file):
    """
    Play audio through a specific device with specified volume and looping option.

    Args:
        deviceName (str): Name of the device ('phone', 'ringer', 'speaker').
        volume (int): Volume level (0-100).
        loop (bool): Whether to loop the audio indefinitely.
        file (str): Path to the audio file.
    """
    if deviceName not in DEVICE_MAP:
        print(f"Error: Unknown device name '{deviceName}'. Choose from {list(DEVICE_MAP.keys())}.")
        return

    # Set the audio sink
    sink_name = DEVICE_MAP[deviceName]
    set_default_sink(sink_name)

    # Initialize pygame mixer
    pygame.mixer.init()
    pygame.mixer.music.load(file)
    pygame.mixer.music.set_volume(volume / 100.0)  # Set volume (0.0 to 1.0)

    # Start playback
    loops = -1 if loop else 0  # -1 for infinite looping
    pygame.mixer.music.play(loops=loops)
    print(f"Playing {file} on {deviceName} ({sink_name}) with volume {volume}%")

    try:
        while pygame.mixer.music.get_busy():
            time.sleep(1)  # Keep the program alive while music is playing
    except KeyboardInterrupt:
        print("\nStopping playback.")
        pygame.mixer.music.stop()
        pygame.mixer.quit()


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

def reset_pico(pico_port):
    baud_rate = 115200
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

    # Close the serial connection
    ser.close()




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
            client.subscribe("pico/servo/control")  # Subscribe to the servo topic here as well
        else:
            print(f"Failed to connect, return code {rc}")

    def on_message(client, userdata, msg):
        nonlocal current_percentage
        
        # Check the topic to decide the action
        if msg.topic == "reactor/power_percentage":
            try:
                current_percentage = int(msg.payload.decode().strip())
                print(f"Received reactor power percentage: {current_percentage}%")
                # Handle the reactor power percentage as needed
            except Exception as e:
                print(f"Error decoding message: {e}")
        
        elif msg.topic == "pico/servo/control":
            message = msg.payload.decode().strip()
            print(f"Received servo control message: {message}")
            
            if message == "8" and state.get_state() == "turbine_startup":
                print("Message '8' received via MQTT. Moving on with the rest of the code.")
                state.set_state("turbine_connection")
            elif message == "9" and state.get_state() == "turbine_connection":
                print("Message '9' received via MQTT. Moving on with the rest of the code.")
                client.publish("reactor/counter", "go")
                state.set_state("power_up")

    def start_alarm():
        nonlocal alarm_active
        if not alarm_active:
            print("Starting alarm on main PC.")
            pygame.mixer.init(channels=1, devicename="SC")
            pygame.mixer.music.load("./data/danger.mp3")
            pygame.mixer.music.set_volume(0.2)
            pygame.mixer.music.play(-1)

            # client.publish("reactor/alarm", "start")
            alarm_active = True
            # play_through_specific("speaker", 20, True, "./data/danger.mp3")

    def stop_alarm():
        nonlocal alarm_active
        if alarm_active:
            print("Stopping alarm on main PC.")
            alarm_active = False
            # pygame.mixer.music.stop()
            # pygame.mixer.quit()
            pygame.mixer.music.stop()
            pygame.mixer.quit()

    def start_lamp():
        print("Starting alarm on main PC.")
        # pygame.mixer.init()
        # pygame.mixer.music.load("./data/danger.mp3")
        # pygame.mixer.music.set_volume(0.5)
        # pygame.mixer.music.play(-1)
        client.publish("reactor/lamp", "start")

    def stop_lamp():
        print("Stopping alarm on main PC.")
        # pygame.mixer.music.stop()
        # pygame.mixer.quit()
        client.publish("reactor/lamp", "stop")

    def disconnect_mqtt():
        print("Disconnecting from MQTT broker.")
        client.loop_stop()  # Stop the loop
        client.disconnect()  # Disconnect from the MQTT broker



    try:
        button_port, telephone_port = find_serial_ports()
        print(f"Initial Button port: {button_port}, Telephone port: {telephone_port}")

        # Reset the button Pico
        reset_pico(button_port)

        # Wait for a moment to ensure the Pico resets properly
        time.sleep(5)

        # Re-find the serial ports after reset
        button_port, telephone_port = find_serial_ports()
        print(f"After reset Button port: {button_port}, Telephone port: {telephone_port}")

        # Initialize and start SerialReaders for both devices
        serial_reader_0 = SerialReader(button_port)
        time.sleep(2)
        serial_reader_1 = SerialReader(telephone_port)
        serial_reader_0.start()
        serial_reader_1.start()

    except Exception as e:
        print(e)
        return

    while True:
        if state.get_state() == "idle":
            if not hasattr(state, 'mqtt_initialized') or not state.mqtt_initialized:
                # Connect to MQTT broker
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
                state.mqtt_initialized = True

            client.publish("reactor/counter", "prepare")
            client.publish("pico/servo/control", "prepare")
            stop_lamp()
            stop_alarm()

            if not serial_reader_0.is_alive():
                serial_reader_0 = SerialReader(button_port)
                serial_reader_0.start()
            if not serial_reader_1.is_alive():
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
            pygame.mixer.music.set_volume(1.0)
            pygame.mixer.music.play(-1)
            # play_through_specific("ringer", 100, True, "./data/ring.mp3")
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
            pygame.mixer.init(channels=1, devicename="SC1")
            pygame.mixer.music.set_volume(1)
            pygame.mixer.music.load("./data/call1.mp3")
            pygame.mixer.music.play()
            # play_through_specific("phone", 100, True, "./data/call1.mp3")
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
            state.set_infoscreen_state("dial_up")
            print("Waiting for button Raised to be pressed...")
            while state.get_state() == "second_call":
                serial_data = serial_reader_1.get_data()
                if is_button_pressed('Raised', serial_data):
                    print("Button Raised is pressed. Moving on with the rest of the code.")
                    state.set_state("dial_up")
                time.sleep(0.1)

        elif state.get_state() == "second_call_up":
            state.set_infoscreen_state("initial_call_up")  # Set the infoscreen state to initial_call_up
            time.sleep(0.5)
            pygame.mixer.init(channels=1, devicename="SC1")
            pygame.mixer.music.load("./data/call2.mp3")
            pygame.mixer.music.set_volume(1)
            pygame.mixer.music.play()
            # play_through_specific("phone", 100, True, "./data/call2.mp3")
            print("Waiting for button Putdown to be pressed...")
            while state.get_state() == "second_call_up":
                serial_data = serial_reader_1.get_data()
                if is_button_pressed('Putdown', serial_data):
                    print("Button Putdown is pressed. Moving on with the rest of the code.")
                    pygame.mixer.quit()
                    state.set_state("particle_check")
                time.sleep(0.1)
        
        elif state.get_state() == "particle_check":
            state.set_infoscreen_state("particle_check")
            print("Waiting for button 1 to be pressed...")
            while state.get_state() == "particle_check":
                serial_data = serial_reader_0.get_data()
                if is_button_pressed('1', serial_data):
                    print("Button 1 is pressed. Moving on with the rest of the code.")
                    start_lamp()
                    state.set_state("steam_monitoring")
                time.sleep(0.1)

        elif state.get_state() == "steam_monitoring":
            print("Waiting for button 2 to be pressed...")
            state.set_infoscreen_state("steam_monitoring")
            while state.get_state() == "steam_monitoring":
                serial_data = serial_reader_0.get_data()
                if is_button_pressed('2', serial_data):
                    print("Button 2 is pressed. Moving on with the rest of the code.")
                    #send display manage
                    client.publish("pico/servo/control", "display")
                    start_alarm()
                    state.set_state("steam_connection")
                time.sleep(0.1)
        
        elif state.get_state() == "steam_connection":
            print("Waiting for button 3 to be pressed...")
            state.set_infoscreen_state("steam_connection")
            while state.get_state() == "steam_connection":
                serial_data = serial_reader_0.get_data()
                if is_button_pressed('3', serial_data):
                    print("Button 3 is pressed. Moving on with the rest of the code.")
                    stop_alarm()
                    state.set_state("condenser")
                time.sleep(0.1)
        
        elif state.get_state() == "condenser":
            state.set_infoscreen_state("condenser")
            print("Waiting for button 4 to be pressed...")
            while state.get_state() == "condenser":
                serial_data = serial_reader_0.get_data()
                if is_button_pressed('4', serial_data):
                    print("Button 4 is pressed. Moving on with the rest of the code.")
                    client.publish("reactor/counter", "go")
                    state.set_infoscreen_state("control_rods")
                    state.set_state("control_rods")
                
        
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
                if current_percentage < 35:
                    if alarm_active:
                        stop_alarm()
                    time_at_five = time_at_six = time_above_six = None
                    current_percentage = None  # Reset current_percentage after handling

                elif current_percentage == 35:
                    if time_at_five is None:
                        time_at_five = time.time()
                        stop_alarm()
                        print("Starting timer for state 'waiting'.")
                    elif time.time() - time_at_five >= 3:
                        
                        client.publish("reactor/counter", "lock5")
                        print("Message has been 5 for 3 consecutive seconds. Changing state to 'waiting'.")
                        state.set_state("idle_pump")
                        stop_alarm()
                        time_at_five = None
                        current_percentage = None  # Reset current_percentage after handling

                elif current_percentage > 35:
                    if time_at_six is None:
                        time_at_six = time.time()
                        # state.set_infoscreen_state("wrong_percentage")
                        print("Starting timer for state 'game_early_end_timeout'.")
                    elif time.time() - time_at_six >= 10:
                        print("Message has been 6 for 10 consecutive seconds. Resetting percentage to 0.")
                        stop_alarm()
                        client.publish("reactor/counter", "prepare")
                        state.set_state("game_early_end_timeout")
                        time_at_six = None
                        current_percentage = None  # Reset current_percentage after handling

                    if not alarm_active and current_percentage is not None:
                        start_alarm()

                else:
                    if alarm_active:
                        stop_alarm()
                    time_at_five = time_at_six = time_above_six = None
                    current_percentage = None  # Reset current_percentage after handling

            time.sleep(1)  # Prevent tight looping
        

        elif state.get_state() == "idle_pump":
            state.set_infoscreen_state("idle_pump")
            print("Waiting for button 5 to be pressed...")
            while state.get_state() == "idle_pump":
                serial_data = serial_reader_0.get_data()
                if is_button_pressed('5', serial_data):
                    print("Button 5 is pressed. Moving on with the rest of the code.")
                    start_alarm()
                    state.set_state("main_pump")
                time.sleep(0.1)
        
        elif state.get_state() == "main_pump":
            state.set_infoscreen_state("main_pump")
            print("Waiting for button 6 to be pressed...")
            while state.get_state() == "main_pump":
                serial_data = serial_reader_0.get_data()
                if is_button_pressed('6', serial_data):
                    print("Button 6 is pressed. Moving on with the rest of the code.")
                    stop_alarm()
                    state.set_state("waiting")
                time.sleep(0.1)

        elif state.get_state() == "waiting":
            pygame.mixer.quit()
            state.set_infoscreen_state("waiting")
            client.publish("pico/servo/control", "start")
            time.sleep(18)
            state.set_state("turbine_connection")



        elif state.get_state() == "turbine_connection":
            state.set_infoscreen_state("turbine_connection")
            print("Waiting for message '9' via MQTT...")

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
                state.mqtt_initialized = True

            def on_message(client, userdata, msg):
                if msg.topic == "pico/servo/control" and msg.payload.decode() == "9":
                    print("Message '9' received via MQTT. Moving on with the rest of the code.")
                    client.publish("reactor/counter", "go")
                    state.set_state("power_up")

            while state.get_state() == "turbine_connection":
                time.sleep(0.1)
        
                
        elif state.get_state() == "power_up": 
            state.set_infoscreen_state("power_up")
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
                if current_percentage < 75:
                    if alarm_active:
                        stop_alarm()
                    time_at_five = time_at_six = time_above_six = None
                    current_percentage = None  # Reset current_percentage after handling

                elif current_percentage == 75:
                    if time_at_five is None:
                        time_at_five = time.time()
                        print("Starting timer for state 'game_end'.")
                    elif time.time() - time_at_five >= 3:
                        print("Message has been 5 for 3 consecutive seconds. Changing state to 'game_end'")
                        client.publish("reactor/counter", "lock50")
                        state.set_state("game_end")
                        stop_alarm()
                        time_at_five = None
                        current_percentage = None  # Reset current_percentage after handling

                elif current_percentage > 75:
                    if time_at_six is None:
                        time_at_six = time.time()
                        print("Starting timer for state 'game_early_end_timeout'.")
                    elif time.time() - time_at_six >= 10:
                        print("Message has been 6 for 10 consecutive seconds. Resetting percentage to 0.")
                        stop_alarm()
                        client.publish("reactor/counter", "prepare")
                        state.set_state("game_early_end_timeout")
                        time_at_six = None
                        current_percentage = None  # Reset current_percentage after handling

                    if not alarm_active and current_percentage is not None:
                        start_alarm()



                    if not alarm_active and current_percentage is not None:
                        start_alarm()

                else:
                    if alarm_active:
                        stop_alarm()
                    time_at_five = time_at_six = time_above_six = None
                    current_percentage = None  # Reset current_percentage after handling

            time.sleep(1)  # Prevent tight looping


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
