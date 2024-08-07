import os
import time
import threading
import serial
import pygame
import statecontroller

class SerialReader(threading.Thread):
    def __init__(self, port, baudrate=115200, timeout=1):
        threading.Thread.__init__(self)
        self.serial_port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = serial.Serial(self.serial_port, self.baudrate, timeout=self.timeout)
        self.serial_data = None
        self.running = True

    def run(self):
        while self.running:
            if self.ser.in_waiting > 0:
                self.serial_data = self.ser.readline().decode('utf-8').strip()

    def stop(self):
        self.running = False
        self.ser.close()

    def get_data(self):
        data = self.serial_data
        self.serial_data = None
        return data

def is_button_pressed(button, serial_data):
    return serial_data and button in serial_data.split(', ')

def main():
    state = statecontroller.StateController()

    while True:
        if state.get_state() == "idle":
            serial_reader_0 = SerialReader('/dev/ttyACM0')
            serial_reader_1 = SerialReader('/dev/ttyACM1')
    
            serial_reader_0.start()
            serial_reader_1.start()
            state.set_infoscreen_state("idle")
            print("Waiting for button 0 to be pressed...")
            while state.get_state() == "idle":
                serial_data = serial_reader_0.get_data()
                if is_button_pressed('0', serial_data):
                    print("Button 0 is pressed")
                    state.set_state("initial_call")
                time.sleep(0.1)
        
        # elif state.get_state() == "phone_check":
        #     set = False
        #     while state.get_state() == "phone_check":
        #         serial_data = serial_reader_1.get_data()
        #         if is_button_pressed('Raised', serial_data):
        #             if not set:
        #                 state.set_infoscreen_state("initial_call_up")
        #                 set = True
        #         else:
        #             state.set_state("initial_call")

        #         time.sleep(0.1)

        elif state.get_state() == "initial_call":
            state.set_infoscreen_state("initial_call")
            pygame.mixer.init()
            pygame.mixer.music.load("./data/ring.mp3")
            pygame.mixer.music.play(-1)
            print("Waiting for button Raised to be pressed...")
            while state.get_state() == "initial_call":
                serial_data = serial_reader_1.get_data()
                if is_button_pressed('Raised', serial_data):
                    print("Button Raised is pressed. Moving on with the rest of the code.")
                    state.set_state("initial_call_up")
                time.sleep(0.1)

        elif state.get_state() == "initial_call_up":
            state.set_infoscreen_state("initial_call_up")
            pygame.mixer.music.stop()
            pygame.mixer.quit()
            time.sleep(0.5)
            pygame.mixer.init(channels=1, devicename="SC")
            pygame.mixer.music.load("./data/call1.mp3")
            pygame.mixer.music.play()
            print("Waiting for button Putdown to be pressed...")
            while state.get_state() == "initial_call_up":
                serial_data = serial_reader_1.get_data()
                if is_button_pressed('Putdown', serial_data):
                    print("Button Putdown is pressed. Moving on with the rest of the code.")
                    pygame.mixer.quit()
                    state.set_state("dial_up")
                time.sleep(0.1)

        elif state.get_state() == "dial_up":
            correct_number = "1124" 
            entered_number = ""

            state.set_infoscreen_state("dial_up")
            print("Please enter the 4-digit number")

            while state.get_state() == "dial_up":
                serial_data = serial_reader_1.get_data()
                if serial_data and serial_data.isdigit():
                    entered_number += serial_data
                    print(f"Current entered number: {entered_number}")

                    if len(entered_number) == 4:
                        if entered_number == correct_number:
                            print("Correct number entered!")
                            state.set_state("second_call")
                        else:
                            print("Incorrect number. Please try again.")
                            state.set_infoscreen_state("wrong_number")
                            entered_number = ""  # Reset entered number for retry

                time.sleep(0.1)  # Sleep for 100 milliseconds

        elif state.get_state() == "second_call":
            print("Waiting for button Raised to be pressed...")
            while state.get_state() == "second_call":
                serial_data = serial_reader_1.get_data()
                if is_button_pressed('Raised', serial_data):
                    print("Button Raised is pressed. Moving on with the rest of the code.")
                    state.set_state("second_call_up")
                time.sleep(0.1)

        elif state.get_state() == "second_call_up":
            state.set_infoscreen_state("initial_call_up")
            time.sleep(0.5)
            pygame.mixer.init(channels=1, devicename="SC")
            pygame.mixer.music.load("./data/call2.mp3")
            pygame.mixer.music.play()
            print("Waiting for button Putdown to be pressed...")
            while state.get_state() == "second_call_up":
                serial_data = serial_reader_1.get_data()
                if is_button_pressed('Putdown', serial_data):
                    print("Button Putdown is pressed. Moving on with the rest of the code.")
                    pygame.mixer.quit()
                    state.set_state("backup_generators")
                time.sleep(0.1)
        
        elif state.get_state() == "backup_generators":
            state.set_infoscreen_state("backup_generators")
            print("Waiting for button 1 to be pressed...")
            while state.get_state() == "backup_generators":
                serial_data = serial_reader_0.get_data()
                if is_button_pressed('1', serial_data):
                    print("Button 1 is pressed. Moving on with the rest of the code.")
                    state.set_state("circulation_pump")
                time.sleep(0.1)
        
        elif state.get_state() == "circulation_pump":
            print("Waiting for button 2 to be pressed...")
            state.set_infoscreen_state("circulation_pump")
            while state.get_state() == "circulation_pump":
                serial_data = serial_reader_0.get_data()
                if is_button_pressed('2', serial_data):
                    print("Button 2 is pressed. Moving on with the rest of the code.")
                    state.set_state("condenser")
                time.sleep(0.1)
        
        elif state.get_state() == "condenser":
            state.set_infoscreen_state("condenser")
            print("Waiting for button 3 to be pressed...")
            while state.get_state() == "condenser":
                serial_data = serial_reader_0.get_data()
                if is_button_pressed('3', serial_data):
                    print("Button 3 is pressed. Moving on with the rest of the code.")
                    state.set_state("water_cleaning")
                time.sleep(0.1)
        
        elif state.get_state() == "water_cleaning":
            print("Waiting for button 4 to be pressed...")
            state.set_infoscreen_state("water_cleaning")
            while state.get_state() == "water_cleaning":
                serial_data = serial_reader_0.get_data()
                if is_button_pressed('4', serial_data):
                    print("Button 4 is pressed. Moving on with the rest of the code.")
                    state.set_state("idle_pump")
                time.sleep(0.1)
        
        elif state.get_state() == "idle_pump":
            print("Waiting for button 5 to be pressed...")
            state.set_infoscreen_state("idle_pump")
            while state.get_state() == "idle_pump":
                serial_data = serial_reader_0.get_data()
                if is_button_pressed('5', serial_data):
                    print("Button 5 is pressed. Moving on with the rest of the code.")
                    state.set_state("main_pump")
                time.sleep(0.1)
        
        elif state.get_state() == "main_pump": 
            state.set_infoscreen_state("main_pump")
            print("Waiting for button 6 to be pressed...")
            while state.get_state() == "main_pump":
                serial_data = serial_reader_0.get_data()
                if is_button_pressed('6', serial_data): 
                    print("Button 6 is pressed. Moving on with the rest of the code.") 
                    state.set_state("control_rods") 
                time.sleep(0.1)
        
        elif state.get_state() == "control_rods": 
            state.set_infoscreen_state("control_rods")
            print("Waiting for button 7 to be pressed...")
            while state.get_state() == "control_rods":
                serial_data = serial_reader_0.get_data()
                if is_button_pressed('7', serial_data): 
                    print("Button 7 is pressed. Moving on with the rest of the code.") 
                    state.set_state("turbine_startup") 
                time.sleep(0.1)

        elif state.get_state() == "turbine_startup": 
            state.set_infoscreen_state("turbine_startup")
            print("Waiting for button 8 to be pressed...")
            while state.get_state() == "turbine_startup":
                serial_data = serial_reader_0.get_data()
                if is_button_pressed('8', serial_data): 
                    print("Button 8 is pressed. Moving on with the rest of the code.") 
                    state.set_state("turbine_connection") 
                time.sleep(0.1)
        
        elif state.get_state() == "turbine_connection": 
            state.set_infoscreen_state("turbine_connection")
            print("Waiting for button 9 to be pressed...")
            while state.get_state() == "turbine_connection":
                serial_data = serial_reader_0.get_data()
                if is_button_pressed('9', serial_data): 
                    print("Button 9 is pressed. Moving on with the rest of the code.") 
                    state.set_state("steam_connection") 
                time.sleep(0.1)
        
        elif state.get_state() == "steam_connection": 
            state.set_infoscreen_state("steam_connection")
            print("Waiting for button 10 to be pressed...")
            while state.get_state() == "steam_connection":
                serial_data = serial_reader_0.get_data()
                if is_button_pressed('10', serial_data): 
                    print("Button 10 is pressed. Moving on with the rest of the code.") 
                    state.set_state("power_up") 
                time.sleep(0.1)
        
        elif state.get_state() == "power_up": 
            state.set_infoscreen_state("power_up")
            print("Waiting for button 11 to be pressed...")
            while state.get_state() == "power_up":
                serial_data = serial_reader_0.get_data()
                if is_button_pressed('11', serial_data): 
                    print("Button 11 is pressed. Moving on with the rest of the code.") 
                    state.set_state("game_end") 
                time.sleep(0.1)
        

        elif state.get_state() == "game_early_end_timeout":
            pygame.mixer.quit()
            state.set_infoscreen_state("game_early_end_timeout")
            serial_reader_0.stop()
            serial_reader_1.stop()
            time.sleep(30)
            state.set_state("idle")

        
        elif state.get_state() == "game_end": 
            state.set_infoscreen_state("game_end")
            serial_reader_0.stop()
            serial_reader_1.stop()
            time.sleep(30)
            state.set_state("idle")



        

if __name__ == "__main__":
    main()
