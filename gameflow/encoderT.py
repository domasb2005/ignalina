import pygame
import RPi.GPIO as GPIO
import threading
import time
from PIL import ImageFont
import paho.mqtt.client as mqtt

# Initialize Pygame
pygame.init()
pygame.mouse.set_visible(False)

# Setup the display for fullscreen mode
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption('Reactor Power')

# Define fonts
font_path = "1.ttf"
percent_font_path = "2.ttf"
seven_seg_font = ImageFont.truetype(font_path, 180)
percent_font = ImageFont.truetype(percent_font_path, 250)
header_font = ImageFont.truetype(percent_font_path, 38)

# GPIO setup
CLK = 16
DT = 12
relay_pin = 26  # Relay GPIO pin

GPIO.setmode(GPIO.BCM)
GPIO.setup(CLK, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(DT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(relay_pin, GPIO.OUT)

# Ensure the relay is off by default
GPIO.output(relay_pin, GPIO.LOW)

# Initialize variables
counter = 0
clkLastState = GPIO.input(CLK)
power_percentage = 0
previous_power_percentage = -1  # Initialize with a value that will trigger the first publish
counter_locked = False  # Flag to lock/unlock the counter
blinking = False  # Flag to control relay blinking

MQTT_BROKER_HOST = "192.168.4.142"  # Set to the actual IP of your broker or "localhost" if running locally
MQTT_BROKER_PORT = 1883

# Function to monitor the rotary encoder
def monitor_encoder():
    global clkLastState, counter, power_percentage, previous_power_percentage, counter_locked
    while True:
        if not counter_locked:
            clkState = GPIO.input(CLK)
            dtState = GPIO.input(DT)

            if clkState != clkLastState:
                if dtState != clkState:
                    counter -= 1
                else:
                    counter += 1

                if counter < 0:
                    counter = 0

                power_percentage = counter // 10

                if power_percentage != previous_power_percentage:
                    publish_state()
                    previous_power_percentage = power_percentage  # Update the previous percentage
                    print(f"Counter: {counter}, Power Percentage: {power_percentage}%")

            clkLastState = clkState
        time.sleep(0.001)

# Function to reset the percentage and counter
def reset_percentage():
    global counter, power_percentage, previous_power_percentage
    counter = 0  # Reset the counter
    power_percentage = 0
    previous_power_percentage = power_percentage  # Update the previous percentage

# Function to lock the counter
def lock_counter():
    global counter_locked
    counter_locked = True
    print("Counter has been locked.")

# Function to unlock the counter
def unlock_counter():
    global counter_locked
    counter_locked = False
    print("Counter has been unlocked.")

# Function to set percentage and lock the counter
def set_percentage_and_lock(target_percentage):
    global counter, power_percentage, previous_power_percentage, counter_locked
    counter = target_percentage * 10  # Set the counter to match the target percentage
    power_percentage = target_percentage
    previous_power_percentage = power_percentage  # Update the previous percentage
    lock_counter()  # Lock the counter
    print(f"Counter set and locked at {power_percentage}%.")

# Function to render text on the screen
def render_text(text, font, color=(255, 0, 0)):
    font = pygame.font.Font(font.path, font.size)
    return font.render(text, True, color)

# Function to update the display
def update_display():
    screen.fill((0, 0, 0))
    
    screen_width, screen_height = pygame.display.get_surface().get_size()
    
    header_text = render_text("Dabartinė reaktoriaus galia:", header_font)
    header_rect = header_text.get_rect(center=(screen_width // 2, (screen_height // 6) - 20))
    screen.blit(header_text, header_rect)
    
    number_text = render_text(f"{power_percentage}", seven_seg_font)
    number_rect = number_text.get_rect(midright=(screen_width // 2 + 45, screen_height // 2 + 20))
    screen.blit(number_text, number_rect)
    
    percent_text = render_text("%", percent_font)
    percent_rect = percent_text.get_rect(midleft=(number_rect.right - 5, screen_height // 2 + 20))
    screen.blit(percent_text, percent_rect)
    
    pygame.display.flip()

# Function to publish the current state
def publish_state():
    client.publish("reactor/power_percentage", power_percentage)

# Function to handle the relay blinking
def test_relay():
    global blinking
    try:
        while True:
            if blinking:
                GPIO.output(relay_pin, GPIO.HIGH)
                print("Relay ON")
                time.sleep(1)
                GPIO.output(relay_pin, GPIO.LOW)
                print("Relay OFF")
                time.sleep(1)
            else:
                GPIO.output(relay_pin, GPIO.LOW)
                time.sleep(0.1)
    except KeyboardInterrupt:
        print("Relay control stopped by user")
    finally:
        GPIO.cleanup()

# MQTT connection setup
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker with result code " + str(rc))
    client.subscribe("reactor/reset")  # Subscribe to the reset topic
    client.subscribe("reactor/alarm")  # Subscribe to the alarm control topic
    client.subscribe("reactor/counter")  # Subscribe to the counter control topic

# Handling messages from MQTT
def on_message(client, userdata, msg):
    if msg.topic == "reactor/reset" and msg.payload.decode().strip() == "new_game":
        print("Received 'new_game' message. Resetting power percentage.")
        reset_percentage()
    elif msg.topic == "reactor/alarm":
        handle_alarm_message(msg.payload.decode().strip())
    elif msg.topic == "reactor/counter":
        handle_counter_message(msg.payload.decode().strip())

alarm_active = False

# Function to start the alarm
def start_alarm():
    global alarm_active, blinking
    if not alarm_active:
        print("Starting alarm on Raspberry Pi.")
        pygame.mixer.init()
        pygame.mixer.music.load("dangerCut.mp3")
        pygame.mixer.music.set_volume(0.2)  # Set volume to 20%
        pygame.mixer.music.play(-1)  # Loop indefinitely
        blinking = True  # Start relay blinking
        alarm_active = True

# Function to stop the alarm
def stop_alarm():
    global alarm_active, blinking
    if alarm_active:
        print("Stopping alarm on Raspberry Pi.")
        pygame.mixer.music.stop()
        pygame.mixer.quit()
        blinking = False  # Stop relay blinking
        GPIO.output(relay_pin, GPIO.LOW)  # Ensure relay is off
        alarm_active = False

# Function to handle alarm messages
def handle_alarm_message(message):
    if message == "start":
        start_alarm()
    elif message == "stop":
        stop_alarm()

# Function to handle counter messages
def handle_counter_message(message):
    if message == "prepare":
        reset_percentage()
        lock_counter()
    elif message == "go":
        unlock_counter()
    elif message == "lock5":
        set_percentage_and_lock(36)
    elif message == "lock50":
        set_percentage_and_lock(75)

# Setup MQTT client
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
client.loop_start()

# Start the encoder and relay threads
encoder_thread = threading.Thread(target=monitor_encoder)
encoder_thread.daemon = True
encoder_thread.start()

relay_thread = threading.Thread(target=test_relay)
relay_thread.daemon = True
relay_thread.start()

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
    
    update_display()
    time.sleep(0.1)

pygame.quit()
GPIO.cleanup()
client.loop_stop()
client.disconnect()