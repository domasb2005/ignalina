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


import serial
import time
import pyudev

# Global variable to hold the serial connection
led_device_serial = None

def find_led_device_port(target_serial="12648509806167176500"):
    """
    Finds the device port for the Arduino with the specified serial number.
    
    Args:
        target_serial (str): The serial number of the target Arduino.
    
    Returns:
        str: The device node (e.g., /dev/ttyACM0).
    
    Raises:
        Exception: If the device is not found.
    """
    context = pyudev.Context()
    for device in context.list_devices(subsystem='tty'):
        serial = device.get('ID_SERIAL_SHORT')
        dev_node = device.device_node
        if serial == target_serial:
            print(f"Found LED device: Serial={serial}, Node={dev_node}")
            return dev_node
    raise Exception("LED device with specified serial number not found.")

def sendToLedDevice(state):
    """
    Sends an integer to the LED device over UART.
    
    Args:
        state (int): The integer to send to the LED device.
    """
    global led_device_serial
    try:
        if led_device_serial is None or not led_device_serial.is_open:
            led_device_port = find_led_device_port()
            led_device_serial = serial.Serial(led_device_port, baudrate=9600, timeout=1)
            time.sleep(2)  # Allow some time for the connection to initialize
            print(f"Serial connection established on {led_device_port}")

        # Send the state to the LED device
        led_device_serial.write(f"{state}\n".encode())
        print(f"Sent state to LED device: {state}")
    except Exception as e:
        print(f"Error sending to LED device: {e}")
    finally:
        pass



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
        # print(data)
        # print("\n")
        return data

    def clear_data(self):
        """Clears the current serial data and flushes the input buffer."""
        time.sleep(1)
        self.serial_data = None
        self.ser.reset_input_buffer()


def is_button_pressed(button, serial_data):

    """
    Checks if the specified button is pressed in the serial data.
    If any other digit is found, changes the state to 'game_early_end_timeout'.

    Args:
        button (str): The expected button to check.
        serial_data (str): The incoming serial data string.
        state (StateController): The state controller instance.

    Returns:
        bool: True if the expected button is pressed, False otherwise.
    """
    if not serial_data:
        return False  # No data received

    # Split the serial data into components (assuming comma-separated values)
    data_parts = serial_data.split(', ')

    # Check for any unexpected digit
    for part in data_parts:
        if part.isdigit() and part != button:
            print(f"wrong action: Unexpected digit '{part}' received.")
            state.set_state("game_early_end_timeout")
            return False  # An unexpected number was found

    # Return whether the expected button is in the data
    return button in data_parts


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



state = statecontroller.StateController()

def main():

    # MQTT Configuration
    MQTT_BROKER_HOST = "0.0.0.0"
    MQTT_BROKER_PORT = 1883

    # Variables to track timing and alarm state
    time_at_five = None
    alarm_start_time = None  # Tracks when the alarm starts in control_rods
    time_at_six = None
    time_above_six = None
    buffer_timer_start = None
    alarm_active = False  # Track the state of the alarm
    current_percentage = None
    current_buffer_value = None

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT broker successfully")
            client.subscribe("reactor/power_percentage")
            client.subscribe("reactor/buffer_value")
            client.subscribe("pico/servo/control")  # Subscribe to the servo topic here as well
        else:
            print(f"Failed to connect, return code {rc}")

    def on_message(client, userdata, msg):
        nonlocal current_percentage
        nonlocal current_buffer_value
        
        # Check the topic to decide the action
        if msg.topic == "reactor/power_percentage":
            try:
                current_percentage = int(msg.payload.decode().strip())
                print(f"Received reactor power percentage: {current_percentage}%")
                # Handle the reactor power percentage as needed
            except Exception as e:
                print(f"Error decoding message: {e}")

        elif msg.topic == "reactor/buffer_value":
            try:
                current_buffer_value = int(msg.payload.decode().strip())
                print(f"Received reactor buffer value: {current_buffer_value}%")
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
            pygame.mixer.init(channels=1, devicename="USB Audio Device Analog Stereo")
            pygame.mixer.music.load("./data/danger.mp3")
            pygame.mixer.music.set_volume(0.2)
            pygame.mixer.music.play(-1)
            sendToLedDevice(-1)

            # client.publish("reactor/alarm", "start")
            alarm_active = True
            # play_through_specific("speaker", 20, True, "./data/danger.mp3")

    def stop_alarm():
        nonlocal alarm_active
        if alarm_active:
            print("Stopping alarm on main PC.")
            alarm_active = False
            pygame.mixer.quit()

    def start_lamp():
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
            sendToLedDevice(0)


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
            sendToLedDevice(1)
            state.set_infoscreen_state("initial_call")
            serial_reader_0.clear_data()
            pygame.mixer.init()
            pygame.mixer.music.load("./data/ring.mp3")
            pygame.mixer.music.set_volume(1.0)
            pygame.mixer.music.play(-1)
            alarm_active = True
            # play_through_specific("ringer", 100, True, "./data/ring.mp3")
            print("Waiting for button Raised to be pressed...")
            while state.get_state() == "initial_call":

                serial_data_0 = serial_reader_0.get_data()
                if serial_data_0 is not None:
                    print("Unexpected data received from serial_reader_0. Transitioning to game_early_end_timeout.")
                    state.set_state("game_early_end_timeout")
                    break

                serial_data = serial_reader_1.get_data()
                if is_button_pressed('Raised', serial_data):
                    print("Button Raised is pressed. Moving on with the rest of the code.")
                    state.set_state("initial_call_up")
                time.sleep(0.1)

        elif state.get_state() == "initial_call_up":
            # serial_reader_0.clear_data
            pygame.mixer.music.stop()
            pygame.mixer.quit()
            time.sleep(1.5)
            pygame.mixer.init(channels=1, devicename="PCM2902 Audio Codec Analog Stereo")
            pygame.mixer.music.set_volume(1)
            pygame.mixer.music.load("./data/pirmas.mp3")
            pygame.mixer.music.play()
            alarm_active = True


            print("Waiting for button Putdown to be pressed...")
            while state.get_state() == "initial_call_up":
                if not pygame.mixer.music.get_busy():
                    state.set_infoscreen_state("initial_call_up")
                
                serial_data_0 = serial_reader_0.get_data()
                if serial_data_0 is not None:
                    print("Unexpected data received from serial_reader_0. Transitioning to game_early_end_timeout.")
                    state.set_state("game_early_end_timeout")
                    break

                serial_data = serial_reader_1.get_data()
                if is_button_pressed('Putdown', serial_data):
                    print("Button Putdown is pressed. Moving on with the rest of the code.")
                    stop_alarm()
                    state.set_state("second_call")
                time.sleep(0.1)

        elif state.get_state() == "dial_up":
            correct_number = "1124"
            entered_number = ""

            state.set_infoscreen_state("dial_up")
            # serial_reader_0.clear_data()
            print("Please enter the 4-digit number")

            while state.get_state() == "dial_up":
                serial_data_0 = serial_reader_0.get_data()
                if serial_data_0 is not None:
                    print("Unexpected data received from serial_reader_0. Transitioning to game_early_end_timeout.")
                    state.set_state("game_early_end_timeout")
                    break

                serial_data = serial_reader_1.get_data()
                if serial_data:
                    if serial_data == "Putdown":
                        print("Putdown signal received. Exiting digit input loop.")
                        state.set_state("second_call")
                        break  # Exit the loop immediately
                    
                    if serial_data.isdigit():
                        entered_number += serial_data
                        print(f"Current entered number: {entered_number}")

                        if len(entered_number) == 4:
                            if entered_number == correct_number:
                                print("Correct number entered!")
                                state.set_state("second_call_up")
                            else:
                                print("Incorrect number. Please try again.")
                                # state.set_infoscreen_state("wrong_number")
                                entered_number = ""  # Reset entered number for retry

                time.sleep(0.1)  # Sleep for 100 milliseconds

        elif state.get_state() == "second_call":
            state.set_infoscreen_state("dial_up")
            # serial_reader_0.clear_data()
            print("Waiting for button Raised to be pressed...")
            while state.get_state() == "second_call":
                serial_data_0 = serial_reader_0.get_data()
                if serial_data_0 is not None:
                    print("Unexpected data received from serial_reader_0. Transitioning to game_early_end_timeout.")
                    state.set_state("game_early_end_timeout")
                    break

                serial_data = serial_reader_1.get_data()
                if is_button_pressed('Raised', serial_data):
                    print("Button Raised is pressed. Moving on with the rest of the code.")
                    state.set_state("dial_up")
                time.sleep(0.1)

        elif state.get_state() == "second_call_up":
            # state.set_infoscreen_state("initial_call_up")  # Set the infoscreen state to initial_call_up
            # serial_reader_0.clear_data()
            pygame.mixer.init(channels=1, devicename="PCM2902 Audio Codec Analog Stereo")
            pygame.mixer.music.load("./data/antras.mp3")
            pygame.mixer.music.set_volume(1)
            pygame.mixer.music.play()
            alarm_active = True
            # play_through_specific("phone", 100, True, "./data/call2.mp3")
            print("Waiting for button Putdown to be pressed...")
            while state.get_state() == "second_call_up":

                if not pygame.mixer.music.get_busy():
                    state.set_infoscreen_state("initial_call_up")

                serial_data_0 = serial_reader_0.get_data()
                if serial_data_0 is not None:
                    print("Unexpected data received from serial_reader_0. Transitioning to game_early_end_timeout.")
                    state.set_state("game_early_end_timeout")
                    break

                serial_data = serial_reader_1.get_data()
                if is_button_pressed('Putdown', serial_data):
                    print("Button Putdown is pressed. Moving on with the rest of the code.")
                    stop_alarm()
                    state.set_state("particle_check")
                time.sleep(0.1)
        
        elif state.get_state() == "particle_check":
            state.set_infoscreen_state("particle_check")
            serial_reader_0.clear_data()
            time.sleep(1)
            print("Waiting for button 1 to be pressed...")
            while state.get_state() == "particle_check":
                serial_data = serial_reader_0.get_data()
                if serial_data:
                    if is_button_pressed('1', serial_data):
                        print("Button 1 is pressed. Moving on with the rest of the code.")
                        start_lamp()
                        state.set_state("steam_monitoring")
                time.sleep(0.1)

        elif state.get_state() == "steam_monitoring":
            print("Waiting for button 2 to be pressed...")
            serial_reader_0.clear_data()
            time.sleep(1)
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
            serial_reader_0.clear_data()
            time.sleep(1)
            print("Waiting for button 3 to be pressed...")
            state.set_infoscreen_state("steam_connection")
            while state.get_state() == "steam_connection":
                serial_data = serial_reader_0.get_data()
                if is_button_pressed('3', serial_data):
                    print("Button 3 is pressed. Moving on with the rest of the code.")
                    stop_alarm()
                    sendToLedDevice(1)
                    state.set_state("condenser")
                time.sleep(0.1)
        
        elif state.get_state() == "condenser":
            serial_reader_0.clear_data()
            time.sleep(1)
            state.set_infoscreen_state("condenser")
            print("Waiting for button 4 to be pressed...")
            while state.get_state() == "condenser":
                serial_data = serial_reader_0.get_data()
                if is_button_pressed('4', serial_data):
                    print("Button 4 is pressed. Moving on with the rest of the code.")
                    client.publish("reactor/counter", "go")
                    state.set_infoscreen_state("control_rods")
                    serial_reader_0.clear_data()
                    time.sleep(1)
                    state.set_state("control_rods")
                
        
        elif state.get_state() == "control_rods": 
            # Ensure the MQTT client is initialized
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

            print("Control rods state is active, processing logic...")

            last_percentage_check_time = None  # Tracks the last time percentage was received
            stable_at_75_start_time = None    # Tracks when percentage first stabilized at 75

            while state.get_state() == "control_rods":
                serial_data_0 = serial_reader_0.get_data()
                if serial_data_0 is not None:
                    print("Unexpected data received from serial_reader_0. Transitioning to game_early_end_timeout.")
                    state.set_state("game_early_end_timeout")
                    current_percentage = None
                    break  # Exit the loop immediately

                # Handle percentage and buffer conditions
                if current_percentage is not None or current_buffer_value is not None:
                    percentage_alarm_condition = current_percentage is not None and current_percentage > 75
                    buffer_alarm_condition = current_buffer_value is not None and abs(current_buffer_value) > 45

                    # Handle the 75% logic
                    if current_percentage == 75:
                        if stable_at_75_start_time is None:
                            stable_at_75_start_time = time.time()  # Start the timer
                            print("Percentage stabilized at 75%. Starting timer.")
                        elif time.time() - stable_at_75_start_time >= 3:
                            print("Maintained 75% for 3 seconds. Transitioning to idle_pump.")
                            client.publish("reactor/counter", "lock5")
                            stop_alarm()
                            sendToLedDevice(1)
                            state.set_state("idle_pump")
                            
                            break  # Exit the loop immediately
                    else:
                        stable_at_75_start_time = None  # Reset the timer if percentage deviates

                    # Handle percentage conditions > 75%
                    if percentage_alarm_condition:
                        if time_at_six is None:
                            time_at_six = time.time()
                            print("Percentage condition exceeded threshold. Starting timer.")
                        elif time.time() - time_at_six >= 10:
                            print("Percentage condition sustained for 10 seconds. Transitioning to game_early_end_timeout.")
                            client.publish("reactor/counter", "prepare")
                            sendToLedDevice(1)
                            current_percentage = None
                            state.set_state("game_early_end_timeout")
                            break
                    else:
                        time_at_six = None  # Reset timer if back below threshold

                    # Handle buffer conditions
                    if buffer_alarm_condition:
                        if buffer_timer_start is None:
                            buffer_timer_start = time.time()
                            print("Buffer value exceeded threshold. Starting 6-second timer.")
                        elif time.time() - buffer_timer_start >= 6:
                            print("Buffer value sustained for 6 seconds. Transitioning to game_early_end_timeout.")
                            state.set_state("game_early_end_timeout")
                            break
                    else:
                        buffer_timer_start = None  # Reset timer if buffer is below threshold

                    # Handle alarm conditions
                    if percentage_alarm_condition or buffer_alarm_condition:
                        if not alarm_active:
                            start_alarm()
                            alarm_start_time = time.time()
                            print("Starting alarm due to percentage or buffer condition.")
                    elif alarm_active and alarm_start_time and time.time() - alarm_start_time >= 5:
                        stop_alarm()
                        sendToLedDevice(1)
                        print("Stopping alarm as no condition is met after minimum duration.")

                # Exit the loop if the state changes
                if state.get_state() != "control_rods":
                    print(f"Exiting control_rods state: new state is {state.get_state()}")
                    break

                time.sleep(0.1)  # Prevent tight looping


        

        elif state.get_state() == "idle_pump":
            buffer_timer_start = None
            time_at_six = None
            stable_at_75_start_time = None


            state.set_infoscreen_state("idle_pump")
            print("Waiting for button 5 to be pressed...")
            while state.get_state() == "idle_pump":
                serial_data = serial_reader_0.get_data()
                if is_button_pressed('5', serial_data):
                    print("Button 5 is pressed. Moving on with the rest of the code.")
                    start_alarm()
                    # sendToLedDevice(-1)
                    state.set_state("main_pump")
                time.sleep(0.1)
        
        elif state.get_state() == "main_pump":
            serial_reader_0.clear_data()
            time.sleep(1)
            state.set_infoscreen_state("main_pump")
            print("Waiting for button 6 to be pressed...")
            while state.get_state() == "main_pump":
                serial_data = serial_reader_0.get_data()
                if is_button_pressed('6', serial_data):
                    print("Button 6 is pressed. Moving on with the rest of the code.")
                    stop_alarm()
                    sendToLedDevice(7)
                    state.set_state("waiting")
                time.sleep(0.1)

        elif state.get_state() == "waiting":
            pygame.mixer.quit()
            state.set_infoscreen_state("waiting")
            client.publish("pico/servo/control", "start")
            serial_reader_0.clear_data()
            time.sleep(1)
            countdown_time = 17  # Total countdown time in seconds
            start_time = time.time()

            while state.get_state() == "waiting":
                # Check elapsed time
                elapsed_time = time.time() - start_time
                remaining_time = countdown_time - elapsed_time

                if remaining_time <= 0:
                    print("Countdown complete. Transitioning to turbine_connection.")
                    state.set_state("turbine_connection")
                    break

                # Monitor serial_reader_0
                serial_data_0 = serial_reader_0.get_data()
                if serial_data_0 is not None:
                    print("Unexpected data received from serial_reader_0. Transitioning to game_early_end_timeout.")
                    state.set_state("game_early_end_timeout")
                    break

                time.sleep(0.1)  # Sleep for 1 second



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
                    state.set_infoscreen_state("power_up")
                    # serial_reader_0.clear_data()
                    state.set_state("power_up")

            while state.get_state() == "turbine_connection":
                serial_data_0 = serial_reader_0.get_data()
                if serial_data_0 is not None:
                    print("Unexpected data received from serial_reader_0. Transitioning to game_early_end_timeout.")
                    state.set_state("game_early_end_timeout")
                    break
                
                time.sleep(0.1)
        
                
        elif state.get_state() == "power_up": 
            state.set_infoscreen_state("power_up")
            # Ensure the MQTT client is initialized
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

            print("Control rods state is active, processing logic...")

            last_percentage_check_time = None  # Tracks the last time percentage was received
            stable_at_75_start_time = None    # Tracks when percentage first stabilized at 75

            while state.get_state() == "power_up":
                serial_data_0 = serial_reader_0.get_data()
                if serial_data_0 is not None:
                    print("Unexpected data received from serial_reader_0. Transitioning to game_early_end_timeout.")
                    state.set_state("game_early_end_timeout")
                    current_percentage = None
                    break  # Exit the loop immediately

                # Handle percentage and buffer conditions
                if current_percentage is not None or current_buffer_value is not None:
                    percentage_alarm_condition = current_percentage is not None and current_percentage > 95
                    buffer_alarm_condition = current_buffer_value is not None and abs(current_buffer_value) > 45

                    # Handle the 75% logic
                    if current_percentage == 95:
                        if stable_at_75_start_time is None:
                            stable_at_75_start_time = time.time()  # Start the timer
                            print("Percentage stabilized at 95%. Starting timer.")
                        elif time.time() - stable_at_75_start_time >= 3:
                            print("Maintained 95% for 3 seconds. Transitioning to game_end.")
                            client.publish("reactor/counter", "lock50")
                            stop_alarm()
                            sendToLedDevice(7)
                            current_percentage = None
                            state.set_state("game_end")
                            
                            break  # Exit the loop immediately
                    else:
                        stable_at_75_start_time = None  # Reset the timer if percentage deviates

                    # Handle percentage conditions > 75%
                    if percentage_alarm_condition:
                        if time_at_six is None:
                            time_at_six = time.time()
                            print("Percentage condition exceeded threshold. Starting timer.")
                        elif time.time() - time_at_six >= 10:
                            print("Percentage condition sustained for 10 seconds. Transitioning to game_early_end_timeout.")
                            client.publish("reactor/counter", "prepare")
                            sendToLedDevice(1)
                            current_percentage = None
                            state.set_state("game_early_end_timeout")
                            break
                    else:
                        time_at_six = None  # Reset timer if back below threshold

                    # Handle buffer conditions
                    if buffer_alarm_condition:
                        if buffer_timer_start is None:
                            buffer_timer_start = time.time()
                            print("Buffer value exceeded threshold. Starting 6-second timer.")
                        elif time.time() - buffer_timer_start >= 6:
                            print("Buffer value sustained for 6 seconds. Transitioning to game_early_end_timeout.")
                            state.set_state("game_early_end_timeout")
                            break
                    else:
                        buffer_timer_start = None  # Reset timer if buffer is below threshold

                    # Handle alarm conditions
                    if percentage_alarm_condition or buffer_alarm_condition:
                        if not alarm_active:
                            start_alarm()
                            alarm_start_time = time.time()
                            print("Starting alarm due to percentage or buffer condition.")
                    elif alarm_active and alarm_start_time and time.time() - alarm_start_time >= 5:
                        stop_alarm()
                        sendToLedDevice(7)
                        print("Stopping alarm as no condition is met after minimum duration.")

                # Exit the loop if the state changes
                if state.get_state() != "power_up":
                    buffer_timer_start = None
                    time_at_six = None
                    stable_at_75_start_time = None

                    print(f"Exiting control_rods state: new state is {state.get_state()}")
                    break

                time.sleep(0.1)


        elif state.get_state() == "game_early_end_timeout":
            buffer_timer_start = None
            time_at_six = None
            stable_at_75_start_time = None
            current_percentage = None
            state.set_infoscreen_state("game_early_end_timeout")
            stop_alarm()
            client.publish("reactor/counter", "prepare")
            start_alarm()
            time.sleep(10)
            stop_alarm()
            sendToLedDevice(7)
            serial_reader_0.stop()
            serial_reader_1.stop()
            state.set_state("idle")

        
        elif state.get_state() == "game_end": 
            current_percentage = None
            buffer_timer_start = None
            time_at_six = None
            stable_at_75_start_time = None
            state.set_infoscreen_state("game_end")
            sendToLedDevice(7)
            serial_reader_0.stop()
            serial_reader_1.stop()
            time.sleep(20)
            state.set_state("idle")



        

if __name__ == "__main__":
    main()
