from machine import UART, Pin
import time

# Initialize UART0 with TX on Pin 0 and RX on Pin 1
uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))

while True:
    # Send a test message
    uart.write('Hello from Pico!\n')
    print("Sent message")
    
    # Wait for 1 second before sending the next message
    time.sleep(1)
