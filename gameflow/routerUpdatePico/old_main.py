import random
from machine import Pin, UART, PWM, I2C
from time import sleep
import utime  # Correctly import the utime module
from umqtt.simple import MQTTClient
import network
from pico_i2c_lcd import I2cLcd
from large_number_display import LargeNumberDisplay

# Wi-Fi credentials
SSID = "IgnalinosAtomine"
PASSWORD = "Muziejus2018"

# MQTT settings
BROKER = "192.168.0.102"
MQTT_TOPIC_SERVO = b"pico/servo/control"


# Define the GPIO pins for each button with pull-up resistors
buttons = {
    '0': Pin(11, Pin.IN, Pin.PULL_UP),
    '1': Pin(9, Pin.IN, Pin.PULL_UP),
    '2': Pin(2, Pin.IN, Pin.PULL_UP),
    '3': Pin(4, Pin.IN, Pin.PULL_UP),
    '4': Pin(5, Pin.IN, Pin.PULL_UP),
    '5': Pin(6, Pin.IN, Pin.PULL_UP),
    '6': Pin(7, Pin.IN, Pin.PULL_UP),
    '8': Pin(8, Pin.IN, Pin.PULL_UP),
    '9': Pin(12, Pin.IN, Pin.PULL_UP)


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
    initial_angle = 120
    ##print("Preparing servos to 150 degrees...")
    for servo in servo_pins:
        set_servo_angle(servo, initial_angle)

def clear_speed_display():
    lcd.move_to(2, 1)  # Starting position of the number
    lcd.putstr(" " * 16)  # Clear the middle two lines where the number is displayed
    lcd.move_to(2, 2)
    lcd.putstr(" " * 16)

def move_servos():
    start_time = utime.ticks_ms()  # Use utime.ticks_ms() for MicroPython
    initial_angle = 120
    final_angle = 20
    duration_fast = 13   # Duration for the servo on pin 16
    duration_slow = 19  # Duration for the servos on pins 17 and 18
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

    ##print("Servos movement completed.")
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
    ##print("Connected to Wi-Fi")

# MQTT message callback
def on_message(topic, msg):
    global speed  # Access the global speed variable
    ##print(f"Received message: {msg}")
    if topic == MQTT_TOPIC_SERVO:
        if msg == b'prepare':
            clear_speed_display()
            prepare_servos()
        elif msg == b'start':
            move_servos()
        elif msg == b'display':
            #print("Managing speed display via MQTT")
            manage_speed_display()

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
# lcd.putstr(" Garų priemaišos")  # Display the text on the first line


# Initialize the speed variable
speed = 10

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
        large_number_display.print_large_number(speed_str, 6, 1)  # Display the large number starting at column 2


# Function to manage speed display based on button inputs with timeout
def manage_speed_display():
    
    lcd.move_to(0, 3)  # Move to the beginning of the fourth line
# lcd.putstr("apsisukimai per min.")  # Display the text on the fourth line
    lcd.putstr(" Koncentracija ug/L")  # Display the text on the fourth line

    global speed
    speed = 10  # Start speed
    increments = 7  # Number of updates
    final_speed = 50  # The final speed value
    total_duration = 7  # Total duration in seconds
    update_interval = total_duration / increments  # Time interval between updates

    start_time = utime.ticks_ms()  # Start time in milliseconds

    for i in range(increments):
        # Calculate elapsed time since the last update
        elapsed_time = utime.ticks_diff(utime.ticks_ms(), start_time)

        # Wait for 1 second display delay
        while elapsed_time < (i + 1) * update_interval * 1000:
            elapsed_time = utime.ticks_diff(utime.ticks_ms(), start_time)

        # Increase speed by a random interval between 1 and 10
        speed += random.randint(1, 10)
        if i == increments - 1:  # On the last update, set speed to final value
            speed = final_speed
        elif speed > final_speed:
            speed = final_speed  # Ensure speed does not exceed 990 before final update

        # Update the display with the new speed
        update_speed_display(speed)
        #print(f"Updated speed: {speed}")

        # Wait for 1 second display delay after each update
        sleep(1)

    #print("Final speed reached: 990")

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
    game_button = Pin(10, Pin.IN, Pin.PULL_UP)

    # Start the servo at 90 degrees
    current_angle = 90
    set_servo_game_angle(servo_game, current_angle)

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
            #print(f"Current angle: {current_angle} degrees")
            
            # Check if the angle is within 90 ± 10 degrees and the button is pressed
            if 70 <= current_angle <= 110 and game_button.value() == 0:
                client.publish(MQTT_TOPIC_SERVO, b"9")  # Publish '9' to the MQTT topic
                while game_button.value() == 0:  # Wait here until the button is released
                    sleep(0.1)
                break  # Exit the loop after stopping completely
            elif game_button.value() == 0:
                sleep(2)  # Pause for 2 seconds if outside the range
            
            sleep(0.01)  # Adjust this delay for smoother/faster rotation
    finally:
        pass

 

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
        
        sleep(0.1)  # Adjust delay to balance responsiveness and CPU usage

##print("Starting button input check and MQTT listening...")


# Connect to Wi-Fi
connect_wifi()

# Connect to MQTT broker and subscribe to the topics
client.connect()
client.subscribe(MQTT_TOPIC_SERVO)


# Start checking buttons and listening for MQTT messages
check_buttons()