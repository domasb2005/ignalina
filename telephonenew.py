from machine import Pin, UART
import time

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

# Initialize UART
uart = UART(0, baudrate=115200)

# Track the state of each button except "Raised"
button_states = {key: False for key, button in buttons.items() if key != 'Raised'}

# Track the state of the "Raised" button separately
raised_button_pressed = False

def read_buttons():
    global raised_button_pressed

    while True:
        for key, button in buttons.items():
            if key == 'Raised':
                if button.value() == 0:  # Button is pressed (active low)
                    if not raised_button_pressed:
                        print("Raised")
                        uart.write("Raised\n")
                        raised_button_pressed = True
                else:  # Button is not pressed
                    if raised_button_pressed:
                        print("Putdown")
                        uart.write("Putdown\n")
                        raised_button_pressed = False
                continue

            if button.value() == 0:  # Button is pressed (active low)
                if not button_states[key]:  # If the button was not previously pressed
                    print(key)
                    uart.write(key + "\n")
                    button_states[key] = True
            else:
                button_states[key] = False  # Reset the state when the button is released
        
        time.sleep(0.1)  # Adjust delay to balance responsiveness and CPU usage

print("Starting button input check...")
read_buttons()

