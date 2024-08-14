import paho.mqtt.client as mqtt
import time
import threading
import serial
import pygame
import statecontroller


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

def main():
    state = statecontroller.StateController()

    while True:
        if state.get_state() == "idle":
            serial_reader_0 = SerialReader('/dev/ttyACM0')
            serial_reader_1 = SerialReader('/dev/ttyACM1')
    
            serial_reader_0.start()
            serial_reader_1.start()
            state.set_infoscreen_state("idle")
            print("Waiting for button 0 to be pressed...")
            while state.get_state() == "idle":
                serial_data = serial_reader_0.get_data()
                if is_button_pressed('0', serial_data):
                    print("Button 0 is pressed")
                    state.set_state("initial_call")
                time.sleep(0.1)
        
        # elif state.get_state() == "phone_check":
        #     set = False
        #     while state.get_state() == "phone_check":
        #         serial_data = serial_reader_1.get_data()
        #         if is_button_pressed('Raised', serial_data):
        #             if not set:
        #                 state.set_infoscreen_state("initial_call_up")
        #                 set = True
        #         else:
        #             state.set_state("initial_call")

        #         time.sleep(0.1)

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
                    state.set_state("dial_up")
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
                            state.set_state("second_call")
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
                    state.set_state("second_call_up")
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
                    state.set_state("circulation_pump")
                time.sleep(0.1)
        
        elif state.get_state() == "circulation_pump":
            print("Waiting for button 2 to be pressed...")
            state.set_infoscreen_state("circulation_pump")
            while state.get_state() == "circulation_pump":
                serial_data = serial_reader_0.get_data()
                if is_button_pressed('2', serial_data):
                    print("Button 2 is pressed. Moving on with the rest of the code.")
                    state.set_state("condenser")
                time.sleep(0.1)
        
        elif state.get_state() == "condenser":
            state.set_infoscreen_state("condenser")
            print("Waiting for button 3 to be pressed...")
            while state.get_state() == "condenser":
                serial_data = serial_reader_0.get_data()
                if is_button_pressed('3', serial_data):
                    print("Button 3 is pressed. Moving on with the rest of the code.")
                    state.set_state("water_cleaning")
                time.sleep(0.1)
        
        elif state.get_state() == "water_cleaning":
            print("Waiting for button 4 to be pressed...")
            state.set_infoscreen_state("water_cleaning")
            while state.get_state() == "water_cleaning":
                serial_data = serial_reader_0.get_data()
                if is_button_pressed('4', serial_data):
                    print("Button 4 is pressed. Moving on with the rest of the code.")
                    state.set_state("idle_pump")
                time.sleep(0.1)
        
        elif state.get_state() == "idle_pump":
            print("Waiting for button 5 to be pressed...")
            state.set_infoscreen_state("idle_pump")
            while state.get_state() == "idle_pump":
                serial_data = serial_reader_0.get_data()
                if is_button_pressed('5', serial_data):
                    print("Button 5 is pressed. Moving on with the rest of the code.")
                    state.set_state("main_pump")
                time.sleep(0.1)
        
        elif state.get_state() == "main_pump": 
            state.set_infoscreen_state("main_pump")
            print("Waiting for button 6 to be pressed...")
            while state.get_state() == "main_pump":
                serial_data = serial_reader_0.get_data()
                if is_button_pressed('6', serial_data): 
                    print("Button 6 is pressed. Moving on with the rest of the code.") 
                    state.set_state("control_rods") 
                time.sleep(0.1)
        
        elif state.get_state() == "control_rods": 
            # MQTT Configuration
            MQTT_BROKER_HOST = "0.0.0.0"  # Set to the actual IP of your broker or "localhost" if running locally
            MQTT_BROKER_PORT = 1883

            # Variables to track timing

            def on_connect(client, userdata, flags, rc):
                if rc == 0:
                    print("Connected to MQTT broker successfully")
                    # Subscribing to the topic once connected
                    client.subscribe("reactor/power_percentage")
                else:
                    print(f"Failed to connect, return code {rc}")

            def on_message(client, userdata, msg):
                global time_at_five, time_at_six, time_above_six
                time_at_five = None
                time_at_six = None
                time_above_six = None
                try:
                    message = int(msg.payload.decode())
                    print(f"Received reactor power percentage: {message}%")
                    
                    # Handle different percentage values
                    if message < 5:
                        time_at_five = None  # Reset the timer if the message is no longer 5
                        time_at_six = None  # Reset the timer if the message is no longer 6
                        time_above_six = None  # Reset the timer if the message is no longer above 6
                        stop_alarm()  # Stop alarm when percentage is 5 or less

                    elif message == 5:
                        if time_at_five is None:
                            time_at_five = time.time()  # Set the timer when the message first equals 5
                        elif time.time() - time_at_five >= 3:
                            print("Message has been 5 for 3 consecutive seconds. Changing state to 'waiting'.")
                            state.set_state("waiting")
                            break
                        stop_alarm()  # Stop alarm when percentage is 5
                        time_at_five = None  # Reset the timer if the message is no longer 5

                    elif message == 6:
                        if time_at_six is None:
                            time_at_six = time.time()  # Start timing when percentage equals 6
                        elif time.time() - time_at_six >= 10:
                            print("Message has been 6 for 10 consecutive seconds. Resetting percentage to 0.")
                            stop_alarm()  # Stop alarm after resetting
                            time_at_six = None
                            time_above_six = None  # Reset above six timer
                            state.set_state("game_early_end_timeout")
                            break
                        start_alarm()  # Start alarm when percentage is above 5
                        time_at_five = None  # Reset the timer if the message is no longer 5

                    elif message > 6:
                        if time_above_six is None:
                            time_above_six = time.time()  # Start timing when percentage is above 6
                        elif time.time() - time_above_six >= 3:
                            print("Message has been above 6 for 3 consecutive seconds. Resetting percentage to 0.")
                            stop_alarm()  # Stop alarm after resetting
                            time_above_six = None
                            time_at_six = None  # Reset exactly at six timer
                            state.set_state("game_early_end_timeout")
                            break
                        start_alarm()  # Start alarm when percentage is above 5
                        time_at_five = None  # Reset the timer if the message is no longer 5

                    else:
                        time_at_five = None  # Reset the timer if the message is no longer 5
                        time_at_six = None  # Reset the timer if the message is no longer 6
                        time_above_six = None  # Reset the timer if the message is no longer above 6
                except Exception as e:
                    print(f"Error decoding message: {e}")

            def start_alarm():
                print("Starting alarm on main PC.")
                # Add your logic here to trigger the alarm on the main PC.

            def stop_alarm():
                print("Stopping alarm on main PC.")
                # Add your logic here to stop the alarm on the main PC.


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

            # control_rods State Block
            if state.get_state() == "control_rods": 
                state.set_infoscreen_state("control_rods")
                
                # Your control_rods logic here...
                
                # Example: Wait for some input or condition
                while state.get_state() == "control_rods":
                    # The on_message function will be handling the percentage updates and state transitions.
                    time.sleep(0.1)  # Small delay to prevent busy-waiting

                client.loop_stop()  # Stop the MQTT loop when exiting the control_rods state


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
