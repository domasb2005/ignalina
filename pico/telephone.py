import network
import time
from machine import Pin
from umqtt.simple import MQTTClient

# Wi-Fi Configuration
SSID = 'Muziejus(Unifi)'
PASSWORD = 'Muziejus2018'

# Connect to Wi-Fi
sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
sta_if.connect(SSID, PASSWORD)

# Wait for connection
while not sta_if.isconnected():
    print("Connecting to Wi-Fi...")
    time.sleep(1)

print("Connected to Wi-Fi")
print("Network configuration:", sta_if.ifconfig())

# Define the GPIO pins for each button with pull-up resistors
buttons = {
    '3': Pin(9, Pin.IN, Pin.PULL_UP),
    '2': Pin(1, Pin.IN, Pin.PULL_UP),
    '9': Pin(2, Pin.IN, Pin.PULL_UP),
    'Raised': Pin(27, Pin.IN, Pin.PULL_UP),
    '5': Pin(8, Pin.IN, Pin.PULL_UP),
    '4': Pin(6, Pin.IN, Pin.PULL_UP),
    '7': Pin(10, Pin.IN, Pin.PULL_UP),
    '6': Pin(5, Pin.IN, Pin.PULL_UP),
    '1': Pin(7, Pin.IN, Pin.PULL_UP),
    '8': Pin(4, Pin.IN, Pin.PULL_UP)
}

# Initialize button states
button_states = {key: False for key in buttons}

# Track the state of the "Raised" button separately
raised_button_pressed = False

# MQTT Configuration
MQTT_BROKER = "192.168.4.142"  # Replace with your MQTT broker IP address
MQTT_TOPIC = "telephone/pressed"
COMMAND_TOPIC = "telephone/command"
CLIENT_ID = "telephone_client"

# Initialize MQTT client
client = MQTTClient(CLIENT_ID, MQTT_BROKER)

def mqtt_connect():
    try:
        print("Attempting to connect to MQTT Broker...")
        client.connect()
        client.set_callback(on_message)
        client.subscribe(COMMAND_TOPIC)
        print(f"Connected to MQTT Broker and subscribed to {COMMAND_TOPIC} topic!")
    except Exception as e:
        print(f"Could not connect to MQTT Broker: {e}")
        time.sleep(5)
        mqtt_connect()  # Retry connection

def on_message(topic, msg):
    print(f"Received message on topic {topic}: {msg}")
    if msg == b'ping':
        print("Received ping, sending pong")
        client.publish(MQTT_TOPIC, "pong")

def read_buttons():
    global raised_button_pressed

    while True:
        for key, button in buttons.items():
            if key == 'Raised':
                if button.value() == 0:  # Button is pressed (active low)
                    if not raised_button_pressed:
                        print("Raised")
                        client.publish(MQTT_TOPIC, "Raised")
                        raised_button_pressed = True
                else:  # Button is not pressed
                    if raised_button_pressed:
                        print("Putdown")
                        client.publish(MQTT_TOPIC, "Putdown")
                        raised_button_pressed = False
                continue

            if button.value() == 0:  # Button is pressed (active low)
                if not button_states[key]:  # If the button was not previously pressed
                    print(key)
                    client.publish(MQTT_TOPIC, key)
                    button_states[key] = True
            else:
                button_states[key] = False  # Reset the state when the button is released
        
        client.check_msg()  # Check for MQTT messages (like ping command)
        time.sleep(0.1)  # Adjust delay to balance responsiveness and CPU usage

print("Starting button input check...")

# Connect to the MQTT broker
mqtt_connect()

# Start reading buttons and publishing to MQTT
read_buttons()

