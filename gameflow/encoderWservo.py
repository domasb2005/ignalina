#!/usr/bin/env python3

# ------------------------------------------------------------------------------
# Toggle for GUI mode (True) vs. headless mode (False)
# ------------------------------------------------------------------------------
ENABLE_GUI = True

import time
import threading
import subprocess
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO

# If GUI is enabled, import Pygame and PIL ImageFont
if ENABLE_GUI:
    import pygame
    from PIL import ImageFont


# ------------------------------------------------------------------------------
# Relay (Lamp) Control
# ------------------------------------------------------------------------------
def handle_lamp_message(message):
    """
    Turn relay ON/OFF (no blinking).
    'start'  -> Relay ON
    'stop'   -> Relay OFF
    """
    if message == "start":
        GPIO.output(relay_pin, GPIO.HIGH)
        print("Relay ON")
    elif message == "stop":
        GPIO.output(relay_pin, GPIO.LOW)
        print("Relay OFF")


# ------------------------------------------------------------------------------
# Rendering (GUI) or stubs (headless)
# ------------------------------------------------------------------------------
if ENABLE_GUI:
    def render_text(text, font, color=(255, 0, 0)):
        """
        Using Pygame's font from TTF path.
        If using PIL's ImageFont, adapt accordingly.
        """
        font_surface = pygame.font.Font(font.path, font.size)
        return font_surface.render(text, True, color)

    def update_display():
        """
        Updates the GUI display with the current power percentage.
        """
        screen.fill((0, 0, 0))
        
        screen_width, screen_height = pygame.display.get_surface().get_size()
        
        header_text = render_text("Dabartinė reaktoriaus galia", header_font)
        header_rect = header_text.get_rect(center=(screen_width // 2, (screen_height // 6) - 20))
        screen.blit(header_text, header_rect)
        
        number_text = render_text(f"{power_percentage}", seven_seg_font)
        number_rect = number_text.get_rect(midright=(screen_width // 2 + 45, screen_height // 2 + 20))
        screen.blit(number_text, number_rect)
        
        percent_text = render_text("%", percent_font)
        percent_rect = percent_text.get_rect(midleft=(number_rect.right - 5, screen_height // 2 + 20))
        screen.blit(percent_text, percent_rect)
        
        pygame.display.flip()

else:
    def update_display():
        """
        No-op function for headless mode.
        """
        pass

# ------------------------------------------------------------------------------
# GPIO setup
# ------------------------------------------------------------------------------
CLK = 16
DT = 12
relay_pin = 26  # Relay GPIO pin
SERVO_PIN = 20  # Servo GPIO pin

GPIO.setmode(GPIO.BCM)
GPIO.setup(CLK, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(DT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(relay_pin, GPIO.OUT)
GPIO.setup(SERVO_PIN, GPIO.OUT)

# Ensure the relay is off by default
GPIO.output(relay_pin, GPIO.LOW)

# ------------------------------------------------------------------------------
# Initialize variables
# ------------------------------------------------------------------------------
counter = 500
clkLastState = GPIO.input(CLK)
power_percentage = 50
previous_power_percentage = -1  # Trigger first MQTT publish
counter_locked = False
buffer = 0  # Servo buffer for angle adjustment
servo_angle = 90  # Default servo angle (90 degrees)

MQTT_BROKER_HOST = "192.168.0.102"  # Set to the actual IP of your broker or "localhost"
MQTT_BROKER_PORT = 1883
BUFFER_TOPIC = "reactor/buffer_value"  # New MQTT topic for the buffer value


def publish_buffer():
    """
    Publishes the current buffer value to the MQTT buffer topic.
    """
    client.publish(BUFFER_TOPIC, buffer)
    print(f"Published Buffer: {buffer} to {BUFFER_TOPIC}")


# ------------------------------------------------------------------------------
# Servo setup
# ------------------------------------------------------------------------------
servo_pwm = GPIO.PWM(SERVO_PIN, 50)  # 50 Hz frequency
servo_pwm.start(0)

def calculate_duty_cycle(angle):
    """
    Converts angle to PWM duty cycle.
    Servo expects duty cycle between ~2% (0°) and ~12% (180°).
    """
    return 2 + (angle / 18)

# ------------------------------------------------------------------------------
# If GUI is enabled, initialize Pygame stuff
# ------------------------------------------------------------------------------
if ENABLE_GUI:
    # Initialize Pygame
    pygame.init()
    pygame.mouse.set_visible(False)

    # Setup the display for fullscreen mode
    screen = pygame.display.set_mode((0, 0))#, pygame.FULLSCREEN)
    pygame.display.set_caption('Reactor Power')

    # Define fonts (PIL fonts used with Pygame)
    font_path = "1.ttf"
    percent_font_path = "2.ttf"

    seven_seg_font = ImageFont.truetype(font_path, 180)
    percent_font = ImageFont.truetype(percent_font_path, 250)
    header_font = ImageFont.truetype(percent_font_path, 38)

# ------------------------------------------------------------------------------
# Rotary Encoder Thread
# ------------------------------------------------------------------------------
def monitor_encoder():
    global clkLastState, counter, power_percentage, previous_power_percentage, counter_locked, buffer
    while True:
        if not counter_locked:
            clkState = GPIO.input(CLK)
            dtState = GPIO.input(DT)

            if clkState != clkLastState:
                if dtState != clkState:
                    counter -= 1
                    buffer += 2  # Inverted logic for servo
                else:
                    counter += 1
                    buffer -= 2  # Inverted logic for servo
                
                buffer = max(-90, min(90, buffer))

                if counter < 0:
                    counter = 0

                power_percentage = counter // 10

                if power_percentage != previous_power_percentage:
                    publish_state()
                    previous_power_percentage = power_percentage
                    print(f"Counter: {counter}, Power Percentage: {power_percentage}%")
                

            clkLastState = clkState
        time.sleep(0.001)

# ------------------------------------------------------------------------------
# Servo Thread with Buffer Fallback

last_published_buffer = None
# ------------------------------------------------------------------------------
def update_servo():
    global buffer, servo_angle, last_published_buffer
    while True:
        # Gradually return buffer to 0
        if buffer > 0:
            buffer -= 1
        elif buffer < 0:
            buffer += 1

        buffer = max(-90, min(90, buffer))

        if buffer != last_published_buffer:
            publish_buffer()
            last_published_buffer = buffer

        # Calculate the new servo angle
        servo_angle = 90 + buffer

        # Clamp the servo angle to valid range (0° to 180°)
        servo_angle = max(0, min(180, servo_angle))

        # Update the servo's PWM duty cycle
        duty_cycle = calculate_duty_cycle(servo_angle)
        servo_pwm.ChangeDutyCycle(duty_cycle)

        # Debug print for servo angle and buffer
        print(f"Servo Angle: {servo_angle}° (Buffer: {buffer})")

        time.sleep(0.1)

# ------------------------------------------------------------------------------
# Utility functions for resetting or locking the counter
# ------------------------------------------------------------------------------
def reset_percentage():
    global counter, power_percentage, previous_power_percentage
    counter = 500  # Reset the counter
    power_percentage = 50
    previous_power_percentage = power_percentage

def lock_counter():
    global counter_locked
    counter_locked = True
    print("Counter has been locked.")

def unlock_counter():
    global counter_locked
    counter_locked = False
    print("Counter has been unlocked.")

def set_percentage_and_lock(target_percentage):
    global counter, power_percentage, previous_power_percentage
    counter = target_percentage * 10
    power_percentage = target_percentage
    previous_power_percentage = power_percentage
    lock_counter()
    print(f"Counter set and locked at {power_percentage}%.")

# ------------------------------------------------------------------------------
# MQTT Publishing
# ------------------------------------------------------------------------------
def publish_state():
    client.publish("reactor/power_percentage", power_percentage)

# ------------------------------------------------------------------------------
# MQTT Callbacks
# ------------------------------------------------------------------------------
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker with result code " + str(rc))
    client.subscribe("reactor/reset")
    client.subscribe("reactor/alarm")
    client.subscribe("reactor/counter")
    client.subscribe("reactor/lamp")

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode().strip()

    if topic == "reactor/reset" and payload == "new_game":
        reset_percentage()
    elif topic == "reactor/alarm":
        handle_alarm_message(payload)
    elif topic == "reactor/counter":
        if payload == "prepare":
            reset_percentage()
            lock_counter()
        elif payload == "go":
            unlock_counter()
        elif payload == "lock5":
            set_percentage_and_lock(75)
        elif payload == "lock50":
            set_percentage_and_lock(95)
    elif topic == "reactor/lamp":
        handle_lamp_message(payload)

# ------------------------------------------------------------------------------
# Main Program
# ------------------------------------------------------------------------------
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

# Start threads
encoder_thread = threading.Thread(target=monitor_encoder, daemon=True)
servo_thread = threading.Thread(target=update_servo, daemon=True)

encoder_thread.start()
servo_thread.start()

running = True
try:
    while running:
        if ENABLE_GUI:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False

        # Update display
        update_display()
        time.sleep(0.1)

except KeyboardInterrupt:
    print("Interrupted by user.")

finally:
    if ENABLE_GUI:
        pygame.quit()
    GPIO.cleanup()
    client.loop_stop()
    client.disconnect()
    servo_pwm.stop()
