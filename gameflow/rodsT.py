import paho.mqtt.client as mqtt
import time
import pygame

# Mock-up StateController for testing
class StateController:
    def __init__(self):
        self.state = "control_rods"
    
    def get_state(self):
        return self.state
    
    def set_state(self, new_state):
        print(f"State changed to: {new_state}")
        self.state = new_state

    def set_infoscreen_state(self, state_info):
        print(f"Info screen updated to: {state_info}")

# Replace with your actual state controller instance
state = StateController()

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
    global current_percentage
    try:
        current_percentage = int(msg.payload.decode().strip())
        print(f"Received reactor power percentage: {current_percentage}%")
    except Exception as e:
        print(f"Error decoding message: {e}")

def start_alarm():
    global alarm_active
    if not alarm_active:
        print("Starting alarm on main PC.")
        pygame.mixer.init()
        pygame.mixer.music.load("./data/danger.mp3")
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)
        alarm_active = True

def stop_alarm():
    global alarm_active
    if alarm_active:
        print("Stopping alarm on main PC.")
        pygame.mixer.music.stop()
        pygame.mixer.quit()
        alarm_active = False

def disconnect_mqtt():
    print("Disconnecting from MQTT broker.")
    client.loop_stop()  # Stop the loop
    client.disconnect()  # Disconnect from the MQTT broker

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

# Main loop
while True:
    if state.get_state() == "control_rods":
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
                    disconnect_mqtt()
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
                    disconnect_mqtt()
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
                    disconnect_mqtt()
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
        time.sleep(30)
        state.set_state("turbine_startup")

    elif state.get_state() == "game_early_end_timeout":
        pygame.mixer.quit()
        print("Handling early game end timeout...")
        time.sleep(30)
        state.set_state("idle")

    time.sleep(0.1)  # Prevent tight looping
