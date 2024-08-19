import paho.mqtt.client as mqtt
import time

# MQTT Broker details
MQTT_BROKER_HOST = "192.168.4.142"  # Replace with your broker's IP address
MQTT_BROKER_PORT = 1883
MQTT_TOPIC = "pico/servo/control"
PUBLISH_MESSAGE = "start"  # The message to trigger the servo

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
        if message == "start":
            print("Triggering servo movement...")
            # Here you would trigger the servo movement
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
    # Optionally, publish a start message to trigger servo movement
    client.publish(MQTT_TOPIC, "prepare")
    time.sleep(5)  # Wait for the message to be received
    client.publish(MQTT_TOPIC, PUBLISH_MESSAGE)
    print(f"Published message: {PUBLISH_MESSAGE} to topic: {MQTT_TOPIC}")

    # Wait before the next iteration or action
    time.sleep(10)  # Adjust the delay as needed

except KeyboardInterrupt:
    print("Exiting...")
    client.loop_stop()
    client.disconnect()
