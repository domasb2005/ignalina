import paho.mqtt.client as mqtt
import time
import threading
import pygame
import statecontroller


class MQTTClientThread(threading.Thread):
    def __init__(self, mqtt_broker_host, mqtt_broker_port, mqtt_topic, on_message_callback=None):
        threading.Thread.__init__(self)
        self.mqtt_broker_host = mqtt_broker_host
        self.mqtt_broker_port = mqtt_broker_port
        self.mqtt_topic = mqtt_topic
        self.on_message_callback = on_message_callback
        self.received_data = None
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.running = True
        self.connected = False

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"Connected to MQTT Broker on topic '{self.mqtt_topic}' successfully")
            self.client.subscribe(self.mqtt_topic)
            self.connected = True
        else:
            print(f"Failed to connect to MQTT Broker, return code {rc}. Retrying...")
            self.connected = False
            while rc != 0:
                try:
                    time.sleep(5)  # Wait for 5 seconds before retrying
                    rc = client.reconnect()
                except Exception as e:
                    print(f"Reconnect failed: {e}. Retrying in 5 seconds...")
                    time.sleep(5)

    def on_message(self, client, userdata, msg):
        if self.on_message_callback:
            self.on_message_callback(client, userdata, msg)
        else:
            self.received_data = msg.payload.decode('utf-8').strip()

    def run(self):
        self.client.connect(self.mqtt_broker_host, self.mqtt_broker_port, 60)
        self.client.loop_start()
        while self.running:
            time.sleep(0.1)

    def stop(self):
        self.running = False
        self.client.loop_stop()
        self.client.disconnect()

    def get_data(self):
        data = self.received_data
        self.received_data = None
        return data

    def publish(self, topic, message):
        if not self.connected:
            print(f"Cannot publish message '{message}' to topic '{topic}': Not connected to MQTT Broker")
            return
        result = self.client.publish(topic, message)
        if result.rc != 0:
            print(f"Failed to publish message '{message}' to topic '{topic}', result code: {result.rc}")
        else:
            print(f"Published message '{message}' to topic '{topic}'")

def check_start_failsafe(button_client, telephone_client, mqtt_broker_host, mqtt_broker_port):
    button_check_start_received = False
    telephone_check_start_received = False

    # Wait until both clients are connected
    while not button_client.connected or not telephone_client.connected:
        print("Waiting for both MQTT clients to connect...")
        time.sleep(1)

    # Send ping to both devices using the thread's publish method
    print("Pinging Pico W devices to ensure connectivity...")
    button_client.publish("button/command", "ping")
    telephone_client.publish("telephone/command", "ping")

    # Set a timeout for the failsafe check
    start_time = time.time()
    timeout = 10  # 10 seconds timeout for the ping-pong

    while time.time() - start_time < timeout:
        button_data = button_client.get_data()
        telephone_data = telephone_client.get_data()

        if button_data == "pong":
            button_check_start_received = True
            print("Received 'pong' from button Pico")

        if telephone_data == "pong":
            telephone_check_start_received = True
            print("Received 'pong' from telephone Pico")

        if button_check_start_received and telephone_check_start_received:
            print("Received 'pong' from both Picos. Ready to start the game.")
            return True

        time.sleep(0.1)

    print("Failed to receive 'pong' from both Picos. Restarting MQTT connection...")
    button_client.stop()
    telephone_client.stop()

    # Reinitialize the MQTT clients
    button_client = MQTTClientThread(mqtt_broker_host, mqtt_broker_port, "button/pressed")
    telephone_client = MQTTClientThread(mqtt_broker_host, mqtt_broker_port, "telephone/pressed")

    # Start the MQTT clients again
    button_client.start()
    telephone_client.start()

    # Retry the failsafe check
    return check_start_failsafe(button_client, telephone_client, mqtt_broker_host, mqtt_broker_port)

def is_button_pressed(button, mqtt_data):
    """Check if the specific button is mentioned in the MQTT data."""
    return mqtt_data and button in mqtt_data.split(', ')


def control_rods_on_message(client, userdata, msg):
    global time_at_five, time_at_six, time_above_six
    state = userdata['state']

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
            stop_alarm()  # Stop alarm when percentage is 5

        elif message == 6:
            if time_at_six is None:
                time_at_six = time.time()  # Start timing when percentage equals 6
            elif time.time() - time_at_six >= 10:
                print("Message has been 6 for 10 consecutive seconds. Resetting percentage to 0.")
                stop_alarm()  # Stop alarm after resetting
                state.set_state("game_early_end_timeout")
            start_alarm()  # Start alarm when percentage is above 5

        elif message > 6:
            if time_above_six is None:
                time_above_six = time.time()  # Start timing when percentage is above 6
            elif time.time() - time_above_six >= 3:
                print("Message has been above 6 for 3 consecutive seconds. Resetting percentage to 0.")
                stop_alarm()  # Stop alarm after resetting
                state.set_state("game_early_end_timeout")
            start_alarm()  # Start alarm when percentage is above 5

    except Exception as e:
        print(f"Error decoding message: {e}")


def start_alarm():
    print("Starting alarm on main PC.")
    # Add your logic here to trigger the alarm on the main PC.


def stop_alarm():
    print("Stopping alarm on main PC.")
    # Add your logic here to stop the alarm on the main PC.


def main():
    state = statecontroller.StateController()

    mqtt_broker_host = "0.0.0.0"  # Replace with your MQTT broker IP address
    mqtt_broker_port = 1883

    print("Initializing MQTT clients...")
    
    button_client = MQTTClientThread(mqtt_broker_host, mqtt_broker_port, "button/pressed")
    telephone_client = MQTTClientThread(mqtt_broker_host, mqtt_broker_port, "telephone/pressed")
    control_rods_client = MQTTClientThread(
        mqtt_broker_host, mqtt_broker_port, "reactor/power_percentage",
        on_message_callback=control_rods_on_message
    )

    print("Starting MQTT client threads...")
    button_client.start()
    telephone_client.start()
    control_rods_client.start()

    print("Ensuring all Pico W devices are ready...")
    if not check_start_failsafe(button_client, telephone_client, mqtt_broker_host, mqtt_broker_port):
        print("Failed to initialize. Exiting.")
        return

    print("Entering main loop...")
    
    # Main game loop starts here
    while True:
        if state.get_state() == "idle":
            state.set_infoscreen_state("idle")
            print("Waiting for button 0 to be pressed...")
            while state.get_state() == "idle":
                mqtt_data = button_client.get_data()
                if is_button_pressed('0', mqtt_data):
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
                mqtt_data = telephone_client.get_data()
                if is_button_pressed('Raised', mqtt_data):
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
                mqtt_data = telephone_client.get_data()
                if is_button_pressed('Putdown', mqtt_data):
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
                mqtt_data = telephone_client.get_data()
                if mqtt_data and mqtt_data.isdigit():
                    entered_number += mqtt_data
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
                mqtt_data = telephone_client.get_data()
                if is_button_pressed('Raised', mqtt_data):
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
                mqtt_data = telephone_client.get_data()
                if is_button_pressed('Putdown', mqtt_data):
                    print("Button Putdown is pressed. Moving on with the rest of the code.")
                    pygame.mixer.quit()
                    state.set_state("backup_generators")
                time.sleep(0.1)

        elif state.get_state() == "backup_generators":
            state.set_infoscreen_state("backup_generators")
            print("Waiting for button 1 to be pressed...")
            while state.get_state() == "backup_generators":
                mqtt_data = button_client.get_data()
                if is_button_pressed('1', mqtt_data):
                    print("Button 1 is pressed. Moving on with the rest of the code.")
                    state.set_state("circulation_pump")
                time.sleep(0.1)

        elif state.get_state() == "circulation_pump":
            print("Waiting for button 2 to be pressed...")
            state.set_infoscreen_state("circulation_pump")
            while state.get_state() == "circulation_pump":
                mqtt_data = button_client.get_data()
                if is_button_pressed('2', mqtt_data):
                    print("Button 2 is pressed. Moving on with the rest of the code.")
                    state.set_state("condenser")
                time.sleep(0.1)

        elif state.get_state() == "condenser":
            state.set_infoscreen_state("condenser")
            print("Waiting for button 3 to be pressed...")
            while state.get_state() == "condenser":
                mqtt_data = button_client.get_data()
                if is_button_pressed('3', mqtt_data):
                    print("Button 3 is pressed. Moving on with the rest of the code.")
                    state.set_state("water_cleaning")
                time.sleep(0.1)

        elif state.get_state() == "water_cleaning":
            print("Waiting for button 4 to be pressed...")
            state.set_infoscreen_state("water_cleaning")
            while state.get_state() == "water_cleaning":
                mqtt_data = button_client.get_data()
                if is_button_pressed('4', mqtt_data):
                    print("Button 4 is pressed. Moving on with the rest of the code.")
                    state.set_state("idle_pump")
                time.sleep(0.1)

        elif state.get_state() == "idle_pump":
            print("Waiting for button 5 to be pressed...")
            state.set_infoscreen_state("idle_pump")
            while state.get_state() == "idle_pump":
                mqtt_data = button_client.get_data()
                if is_button_pressed('5', mqtt_data):
                    print("Button 5 is pressed. Moving on with the rest of the code.")
                    state.set_state("main_pump")
                time.sleep(0.1)

        elif state.get_state() == "main_pump":
            state.set_infoscreen_state("main_pump")
            print("Waiting for button 6 to be pressed...")
            while state.get_state() == "main_pump":
                mqtt_data = button_client.get_data()
                if is_button_pressed('6', mqtt_data):
                    print("Button 6 is pressed. Moving on with the rest of the code.")
                    state.set_state("control_rods")
                time.sleep(0.1)

        elif state.get_state() == "control_rods":
            # The control rods logic will be handled by the control_rods_on_message callback.
            state.set_infoscreen_state("control_rods")
            while state.get_state() == "control_rods":
                time.sleep(0.1)  # Small delay to prevent busy-waiting

        elif state.get_state() == "waiting":
            state.set_infoscreen_state("waiting")
            time.sleep(30)
            state.set_state("turbine_startup")

        elif state.get_state() == "turbine_startup":
            state.set_infoscreen_state("turbine_startup")
            print("Waiting for button 8 to be pressed...")
            while state.get_state() == "turbine_startup":
                mqtt_data = button_client.get_data()
                if is_button_pressed('8', mqtt_data):
                    print("Button 8 is pressed. Moving on with the rest of the code.")
                    state.set_state("turbine_connection")
                time.sleep(0.1)

        elif state.get_state() == "turbine_connection":
            state.set_infoscreen_state("turbine_connection")
            print("Waiting for button 9 to be pressed...")
            while state.get_state() == "turbine_connection":
                mqtt_data = button_client.get_data()
                if is_button_pressed('9', mqtt_data):
                    print("Button 9 is pressed. Moving on with the rest of the code.")
                    state.set_state("steam_connection")
                time.sleep(0.1)

        elif state.get_state() == "steam_connection":
            state.set_infoscreen_state("steam_connection")
            print("Waiting for button 10 to be pressed...")
            while state.get_state() == "steam_connection":
                mqtt_data = button_client.get_data()
                if is_button_pressed('10', mqtt_data):
                    print("Button 10 is pressed. Moving on with the rest of the code.")
                    state.set_state("power_up")
                time.sleep(0.1)

        elif state.get_state() == "power_up":
            state.set_infoscreen_state("power_up")
            print("Waiting for button 11 to be pressed...")
            while state.get_state() == "power_up":
                mqtt_data = button_client.get_data()
                if is_button_pressed('11', mqtt_data):
                    print("Button 11 is pressed. Moving on with the rest of the code.")
                    state.set_state("game_end")
                time.sleep(0.1)

        elif state.get_state() == "game_early_end_timeout":
            pygame.mixer.quit()
            state.set_infoscreen_state("game_early_end_timeout")
            button_client.stop()
            telephone_client.stop()
            control_rods_client.stop()
            time.sleep(30)
            state.set_state("idle")

        elif state.get_state() == "game_end":
            state.set_infoscreen_state("game_end")
            button_client.stop()
            telephone_client.stop()
            control_rods_client.stop()
            time.sleep(30)
            state.set_state("idle")


if __name__ == "__main__":
    main()
