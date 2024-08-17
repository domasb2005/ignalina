import network
import time
from machine import Pin, UART
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
    '0': Pin(15, Pin.IN, Pin.PULL_UP),
    '1': Pin(14, Pin.IN, Pin.PULL_UP),
    '2': Pin(13, Pin.IN, Pin.PULL_UP),
    '3': Pin(12, Pin.IN, Pin.PULL_UP),
    '4': Pin(11, Pin.IN, Pin.PULL_UP),
    '5': Pin(10, Pin.IN, Pin.PULL_UP),
    '6': Pin(9, Pin.IN, Pin.PULL_UP),
    '7': Pin(8, Pin.IN, Pin.PULL_UP),
    '8': Pin(7, Pin.IN, Pin.PULL_UP),
    '9': Pin(6, Pin.IN, Pin.PULL_UP),
    '10': Pin(5, Pin.IN, Pin.PULL_UP),
    '11': Pin(4, Pin.IN, Pin.PULL_UP),
    '12': Pin(2, Pin.IN, Pin.PULL_UP)
}

# Initialize UART
uart = UART(0, baudrate=115200)

# MQTT configuration
MQTT_BROKER = "192.168.4.142"
MQTT_TOPIC = "button/pressed"
COMMAND_TOPIC = "button/command"  # Topic to receive commands like "ping"
CLIENT_ID = "button_client"

# Initialize MQTT client
client = MQTTClient(CLIENT_ID, MQTT_BROKER)

# MQTT message callback function
def on_message(topic, msg):
    print(f"Received message on topic {topic}: {msg}")
    if msg == b'ping':
        print("Received 'ping', responding with 'pong'")
        client.publish(MQTT_TOPIC, "pong")

def mqtt_connect():
    while True:
        try:
            client.connect()
            print("Connected to MQTT Broker!")
            break  # Exit the loop once connected
        except Exception as e:
            print("Could not connect to MQTT Broker:", e)
            time.sleep(5)  # Wait before retrying

def check_buttons():
    pressed_buttons = []
    for key, button in buttons.items():
        if button.value() == 0:  # Button is pressed (active low)
            pressed_buttons.append(key)
    
    if pressed_buttons:
        pressed = ', '.join(pressed_buttons)
    else:
        pressed = "None"
    
    print(pressed)
    uart.write(pressed + "\n")
    
    try:
        client.publish(MQTT_TOPIC, pressed)
    except Exception as e:
        print("Failed to send message to MQTT Broker:", e)

def main():
    # Set the MQTT message callback
    client.set_callback(on_message)

    # Connect to Wi-Fi and MQTT broker
    mqtt_connect()

    # Subscribe to the command topic to receive "ping" messages
    client.subscribe(COMMAND_TOPIC)

    print("Starting button input check...")

    # Main loop to check buttons and process incoming MQTT messages
    while True:
        client.check_msg()  # Check for incoming messages more frequently
        check_buttons()     # Check button states
        time.sleep(0.05)    # Small delay to balance checking frequency

if __name__ == "__main__":
    main()

