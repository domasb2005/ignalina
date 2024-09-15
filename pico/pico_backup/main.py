import random
from machine import Pin, UART, PWM, I2C
from time import sleep
import utime  # Correctly import the utime module
from umqtt.simple import MQTTClient
import network
from pico_i2c_lcd import I2cLcd
from large_number_display import LargeNumberDisplay

# Wi-Fi credentials
SSID = "Muziejus(Unifi)"
PASSWORD = "Muziejus2018"

# MQTT settings
BROKER = "192.168.4.142"
MQTT_TOPIC_SERVO = b"pico/servo/control"

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

# Define PWM pins for the servos
servo_pins = [PWM(Pin(16)), PWM(Pin(17)), PWM(Pin(18))]

# Set the PWM frequency to 50Hz for all servo motors
for servo in servo_pins:
    servo.freq(50)

def set_servo_angle(servo, angle):
    min_duty = 1000  # corresponds to 0 degrees
    max_duty = 9000  # corresponds to 180 degrees
    duty = int(min_duty + (angle / 180) * (max_duty - min_duty))
    servo.duty_u16(duty)

def prepare_servos():
    initial_angle = 150
    print("Preparing servos to 150 degrees...")
    for servo in servo_pins:
        set_servo_angle(servo, initial_angle)

def move_servos():
    start_time = utime.ticks_ms()  # Use utime.ticks_ms() for MicroPython
    initial_angle = 150
    final_angle = 0
    duration_fast = 10   # Duration for the servo on pin 16
    duration_slow = 16  # Duration for the servos on pins 17 and 18
    steps = 100  # Number of steps for smooth movement

    while True:
        elapsed_time = utime.ticks_diff(utime.ticks_ms(), start_time) / 1000  # Use utime.ticks_diff()

        if elapsed_time <= duration_fast:
            angle_16 = initial_angle - (initial_angle - final_angle) * (elapsed_time / duration_fast)
            set_servo_angle(servo_pins[0], angle_16)

        if elapsed_time <= duration_slow:
            angle_17 = initial_angle - (initial_angle - final_angle) * (elapsed_time / duration_slow)
            angle_18 = angle_17
            set_servo_angle(servo_pins[1], angle_17)
            set_servo_angle(servo_pins[2], angle_18)

        sleep(duration_slow / steps)

        if elapsed_time > duration_slow:
            break

    print("Servos movement completed.")
    start_servo_game()  # Start the servo game after reaching 3600

# Initialize UART
uart = UART(0, baudrate=115200)

# Connect to Wi-Fi
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    while not wlan.isconnected():
        sleep(1)
    print("Connected to Wi-Fi")

# MQTT message callback
def on_message(topic, msg):
    global speed  # Access the global speed variable
    print(f"Received message: {msg}")
    if topic == MQTT_TOPIC_SERVO:
        if msg == b'prepare':
            speed = 0  # Reset speed to 0
            update_speed_display(speed)  # Update the display to show speed as 0
            prepare_servos()
        elif msg == b'start':
            move_servos()

# Initialize MQTT client
client = MQTTClient("pico_client", BROKER)
client.set_callback(on_message)

# LCD and button logic
I2C_ADDR = 0x27
I2C_NUM_ROWS = 4
I2C_NUM_COLS = 20

i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=50000)
lcd = I2cLcd(i2c, I2C_ADDR, I2C_NUM_ROWS, I2C_NUM_COLS)

# Instantiate the LargeNumberDisplay class
large_number_display = LargeNumberDisplay(lcd)

# Set up GPIO pins for the speed buttons
button1 = Pin(19, Pin.IN, Pin.PULL_UP)
button2 = Pin(20, Pin.IN, Pin.PULL_UP)
button3 = Pin(21, Pin.IN, Pin.PULL_UP)

# Display static text on the first and last lines
lcd.clear()
lcd.move_to(0, 0)  # Move to the top-left corner of the screen
lcd.putstr(" Garų priemaišos")  # Display the text on the first line

lcd.move_to(0, 3)  # Move to the beginning of the fourth line
# lcd.putstr("apsisukimai per min.")  # Display the text on the fourth line
lcd.putstr(" koncentracija µg/L")  # Display the text on the fourth line

# Initialize the speed variable
speed = 990

# Function to update the speed display
def update_speed_display(speed):
    speed_str = str(speed)
    
    # Clear only the area where the large number is displayed
    lcd.move_to(2, 1)  # Starting position of the number
    lcd.putstr(" " * 16)  # Clear the middle two lines where the number is displayed
    lcd.move_to(2, 2)
    lcd.putstr(" " * 16)

    # Display the large number in the appropriate position
    if speed == 0:
        large_number_display.print_large_number(speed_str, 8, 1)  # Display the large number starting at column 8
    else:
        large_number_display.print_large_number(speed_str, 2, 1)  # Display the large number starting at column 2

# Display the initial speed of 0
update_speed_display(speed)

# Function to manage speed display based on button inputs with timeout
def manage_speed_display():
    global speed
    timeout = 120  # 2 minutes timeout
    start_time = utime.ticks_ms()  # Start the timeout timer using utime

    while True:
        elapsed_time = utime.ticks_diff(utime.ticks_ms(), start_time) / 1000

        if elapsed_time > timeout:
            print("Timeout reached. Resetting speed and stopping servos.")
            speed = 0
            update_speed_display(speed)
            prepare_servos()
            return  # Exit the function and return to the main loop

        # Check if button 1 is pressed and increase speed until 1200
        if button1.value() == 0 and speed < 1200:
            increment = random.randint(50, 100)
            speed += increment
            if speed > 1200:
                speed = 1200
            update_speed_display(speed)
            sleep(0.1)

        # Check if button 2 is pressed and increase speed until 2400
        elif button2.value() == 0 and speed < 2400 and speed >= 1200:
            increment = random.randint(50, 100)
            speed += increment
            if speed > 2400:
                speed = 2400
            update_speed_display(speed)
            sleep(0.1)

        # Check if button 3 is pressed and increase speed until 3600
        elif button3.value() == 0 and speed < 3600 and speed >= 2400:
            increment = random.randint(50, 100)
            speed += increment
            if speed > 3600:
                speed = 3600
            update_speed_display(speed)
            sleep(0.1)

        # Check if speed has reached 3600 to start the servo game
        if speed == 3600:
            print("Speed 3600 reached. Starting servo game...")
            client.publish(MQTT_TOPIC_SERVO, b"8")  # Publish '8' to the MQTT topic
            start_servo_game()  # Start the servo game after reaching 3600
            break  # Exit the loop once the game starts

        # Small delay to prevent excessive CPU usage
        sleep(0.05)

# Function to start the servo game with timeout
def start_servo_game():
    global speed
    # Initialize the PWM pin for the servo game
    servo_game = PWM(Pin(26))
    servo_game.freq(50)

    # Function to set the servo angle
    def set_servo_game_angle(servo, angle):
        min_duty = 1000  # corresponds to 0 degrees
        max_duty = 9000  # corresponds to 180 degrees
        duty = int(min_duty + (angle / 180) * (max_duty - min_duty))
        servo.duty_u16(duty)

    # Initialize button on GPIO 22 with pull-up resistor
    game_button = Pin(22, Pin.IN, Pin.PULL_UP)

    # Start the servo at 90 degrees
    current_angle = 90
    set_servo_game_angle(servo_game, current_angle)
    print(f"Starting at 90 degrees")

    # Set the speed of rotation
    speed = 2  # Adjust this value to control the speed (higher = faster)
    direction = 1  # 1 for increasing angle, -1 for decreasing angle
    start_time = utime.ticks_ms()  # Start the timeout timer using utime
    timeout = 120  # 2 minutes timeout

    # Rotate servo between 0 and 180 degrees until button is pressed or timeout
    try:
        client.publish(MQTT_TOPIC_SERVO, b"8")  # Publish '9' to the MQTT topic

        while True:  # Run indefinitely
            elapsed_time = utime.ticks_diff(utime.ticks_ms(), start_time) / 1000
            if elapsed_time > timeout:
                print("Timeout reached during servo game. Stopping and resetting.")
                speed = 0
                update_speed_display(speed)
                prepare_servos()
                return  # Exit the function and return to the main loop

            # Update the angle
            current_angle += direction * speed
            
            # Reverse direction at 0 and 180 degrees
            if current_angle >= 180:
                current_angle = 180
                direction = -1
            elif current_angle <= 0:
                current_angle = 0
                direction = 1
            
            set_servo_game_angle(servo_game, current_angle)
            print(f"Current angle: {current_angle} degrees")
            
            # Check if the angle is within 90 ± 10 degrees and the button is pressed
            if 80 <= current_angle <= 100 and game_button.value() == 0:
                print("Button pressed within 90 ± 10 degrees. Stopping...")
                client.publish(MQTT_TOPIC_SERVO, b"9")  # Publish '9' to the MQTT topic
                while game_button.value() == 0:  # Wait here until the button is released
                    sleep(0.1)
                break  # Exit the loop after stopping completely
            elif game_button.value() == 0:
                print("Button pressed outside 90 ± 10 degrees. Pausing for 2 seconds...")
                sleep(2)  # Pause for 2 seconds if outside the range
            
            sleep(0.01)  # Adjust this delay for smoother/faster rotation
    finally:
        print(f"Stopped at {current_angle} degrees")

# Check buttons and MQTT messages
def check_buttons():
    while True:
        # Check button states and publish over UART
        pressed_buttons = []
        for key, button in buttons.items():
            if button.value() == 0:  # Button is pressed (active low)
                pressed_buttons.append(key)
        
        if pressed_buttons:
            pressed = ', '.join(pressed_buttons)
            print(pressed)
            uart.write(pressed + "\n")
        
        # Check for MQTT messages
        client.check_msg()
        
        sleep(0.5)  # Adjust delay to balance responsiveness and CPU usage

print("Starting button input check and MQTT listening...")

# Connect to Wi-Fi
connect_wifi()

# Connect to MQTT broker and subscribe to the topics
client.connect()
client.subscribe(MQTT_TOPIC_SERVO)

# Start checking buttons and listening for MQTT messages
check_buttons()
