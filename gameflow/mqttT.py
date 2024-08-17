import paho.mqtt.client as mqtt
import time
# MQTT Broker details
MQTT_BROKER_HOST = "0.0.0.0"  # Replace with your broker's IP address
MQTT_BROKER_PORT = 1883
MQTT_TOPIC = "reactor/power_percentage"

# Callback when the client receives a connection acknowledgment from the broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker successfully")
        # Subscribe to the topic
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"Failed to connect, return code {rc}")

# Callback when a PUBLISH message is received from the broker
def on_message(client, userdata, msg):
    try:
        message = msg.payload.decode()
        print(f"Received message on topic {msg.topic}: {message}")
    except Exception as e:
        print(f"Error decoding message: {e}")

# Set up MQTT client
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# Connect to the MQTT broker
connected = False
while not connected:
    try:
        client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
        connected = True
    except Exception as e:
        print(f"Connection failed: {e}. Retrying in 5 seconds...")
        time.sleep(5)

# Start the MQTT client loop
client.loop_start()

try:
    # Keep the script running to listen to incoming messages
    while True:
        time.sleep(1)  # Sleep to prevent high CPU usage
except KeyboardInterrupt:
    print("Exiting...")
    client.loop_stop()
    client.disconnect()
