import os
import stat
import time
import pygame
import statecontroller
import serial
import psutil

def read_button_states(ser):
    if ser.in_waiting > 0:
        line = ser.readline().decode('utf-8').strip()
        print(f"Serial data read: {line}")  # Debug print
        return line
    return None

def is_button_pressed(button, serial_data):
    if serial_data:
        pressed_buttons = serial_data.split(', ')
        print(f"Buttons pressed: {pressed_buttons}")  # Debug print
        return button in pressed_buttons
    return False

def main():
    ser_idle = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
    ser_initial_call = serial.Serial('/dev/ttyACM1', 115200, timeout=1)
    
    state = statecontroller.StateController()
    while True:
        if state.get_state() == "idle":
            state.set_infoscreen_state("idle")
            with open("./states/.playerscreen", "w+") as f:
                f.write("email_empty")
            while True:
                serial_data = read_button_states(ser_idle)
                if serial_data:
                    print(f"Received serial data: {serial_data}")  # Debug print
                    if is_button_pressed('0', serial_data):
                        print("Button 0 is pressed")
                        break
                print("Waiting for button 0 to be pressed...")
                time.sleep(0.5)
            print("Button 0 was pressed. Moving on with the rest of the code.")
            state.set_state("initial_call")

        if state.get_state() == "initial_call":
            state.set_infoscreen_state("initial_call")
            pygame.mixer.init()
            pygame.mixer.music.load("./data/ring.mp3")
            pygame.mixer.music.play(-1)
            while True:
                serial_data = read_button_states(ser_initial_call)
                if serial_data:
                    print(f"Received serial data: {serial_data}")  # Debug print
                    if is_button_pressed('Raised', serial_data):
                        print("Button Raised is pressed")
                        break
                print("Waiting for button Raised to be pressed...")
                time.sleep(0.1)
            
            pygame.mixer.music.stop()
            state.set_state("initial_call_up")

        if state.get_state() == "initial_call_up":
            pygame.mixer.music.stop()
            pygame.mixer.quit()
            time.sleep(0.5)
            pygame.mixer.init(channels=1, devicename="SC")
            pygame.mixer.music.load("./data/call1.mp3")
            pygame.mixer.music.play()
            while True:
                serial_data = read_button_states(ser_initial_call)
                if serial_data:
                    print(f"Received serial data: {serial_data}")  # Debug print
                    if not is_button_pressed('Raised', serial_data):
                        print("Button Raised is not pressed")
                        break
                print("Waiting for button Raised not to be pressed...")
                time.sleep(0.1)
            pygame.mixer.music.stop()
            state.set_state("dial_up")

        if state.get_state() == "dial_up":
            print("Dialing up")
            with open("states/.playerscreen", "w+") as ps:
                ps.write("email")
            time.sleep(20)
            state.set_state("cipher_wait_on")
            state.set_infoscreen_state("cipher_wait_on")
            break

    ser_idle.close()
    ser_initial_call.close()

if __name__ == "__main__":
    main()
