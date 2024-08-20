import paho.mqtt.client as mqtt

# MQTT Configuration
MQTT_BROKER_HOST = "0.0.0.0"  # Replace with your broker's IP address
MQTT_BROKER_PORT = 1883
MQTT_TOPIC = "pico/servo/control"

# The callback for when the client receives a connection response from the server.
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker successfully")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"Failed to connect, return code {rc}")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(f"Received message: {msg.payload.decode()} on topic {msg.topic}")

# Create an MQTT client instance
client = mqtt.Client()

# Assign the callback functions
client.on_connect = on_connect
client.on_message = on_message

# Connect to the broker
client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)

# Start the loop to process MQTT messages
client.loop_forever()
