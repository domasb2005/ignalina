# Main game loop
import os
import stat
import time

import pygame

import statecontroller
import serial
import psutil

def read_button_states(serial_port, baudrate=115200, timeout=1):
    with serial.Serial(serial_port, baudrate, timeout=timeout) as ser:
        if ser.in_waiting > 0:
            return ser.readline().decode('utf-8').strip()
    return None

def is_button_pressed(button, serial_data):
    return serial_data and button in serial_data.split(', ')



def main():

    state = statecontroller.StateController()
    while True:
        ################
        # idle
        ################
        start = False

        if state.get_state() == "idle":
            state.set_infoscreen_state("idle")

            with open("./states/.playerscreen", "w+") as f:
                f.write("email_empty")

            while True:
                serial_data = read_button_states('/dev/ttyACM0')
                if is_button_pressed('0', serial_data):
                    print("Button 0 is pressed")
                    break
                print("Waiting for button 0 to be pressed...")
                time.sleep(0.5)
            
            print("Button 0 was pressed. Moving on with the rest of the code.")
            state.set_state("initial_call")

            break

        ################
        # initial_call
        ################

        elif state.get_state() == "initial_call":
            state.set_infoscreen_state("initial_call")
            pygame.mixer.init(channels=1, devicename="SC")
            pygame.mixer.music.load("./data/ring.mp3")
            pygame.mixer.music.play(-1)

            while True:
                serial_data = read_button_states('/dev/ttyACM1')
                if is_button_pressed('0', serial_data):
                    print("Button 0 is pressed")
                    break
                print("Waiting for button 0 to be pressed...")
                time.sleep(0.5)

            state.set_state("initial_call_up")

        elif state.get_state() == "initial_call_up":
            pygame.mixer.music.stop()
            pygame.mixer.quit()
            time.sleep(0.5)
            pygame.mixer.init()
            pygame.mixer.music.load("./data/call1.mp3")
            pygame.mixer.music.play(-1)
            while True:
                serial_data = read_button_states('/dev/ttyACM1')
                if not is_button_pressed('Raised', serial_data):
                    print("Button Raised is not pressed")
                    break
                print("Waiting for button Raised not to be pressed...")
                time.sleep(0.5)
                
            state.set_state("dial_up")


        elif state.get_state() == "dial_up":
            with open("states/.playerscreen", "w+") as ps:
                ps.write("email")
            time.sleep(20)
            state.set_state("cipher_wait_on")
            state.set_infoscreen_state("cipher_wait_on")

            ################
            # cipher
            ################

        # elif state.get_state() == "cipher_wait_on":
        #     harris.sync()
        #     if harris.on:   
        #         state.set_state("cipher_wait_ready")
        #         state.set_infoscreen_state("cipher_wait_ready")
            
        # elif state.get_state() == "cipher_wait_ready":
        #     harris.sync()
        #     if harris.ready:
        #         state.set_state("cipher_wait_set")
        #         state.set_infoscreen_state("cipher_enter")

        # elif state.get_state() == "cipher_wait_set":
        #     harris.sync()
        #     if harris.correct:
        #         state.set_state("cipher_set")

        # elif state.get_state() == "cipher_set":
        #     state.set_state("cipher_no_link")
        #     state.set_infoscreen_state("jamming_information")

        # elif state.get_state() == "cipher_no_link":
        #     time.sleep(8)
        #     state.set_state("second_call")
        #     state.set_infoscreen_state("initial_call")

        # ################
        # # second_call
        # ################

        # elif state.get_state() == "second_call":
        #     if state.single_exec(): telephone.set_state("ring")
        #     if telephone.get_state() == "raised":
        #         state.set_state("second_call_up")
                

        # elif state.get_state() == "second_call_up":
        #     telephone.play_sound("./data/call2.mp3")
        #     state.set_state("second_call_end")

        # elif state.get_state() == "second_call_end":
        #     if state.single_exec(): state.set_infoscreen_state("initial_call_up")
        #     if telephone.get_state() == "putDown":
        #         state.set_state("cipher_off")
        #         state.set_infoscreen_state("harris_off")

        # elif state.get_state() == "cipher_off":
        #     harris.sync()
        #     if not harris.on:
        #         state.set_state("phone_wall_wait_set")
        #         state.set_infoscreen_state("phone_wall_information")


        # ################
        # # sign
        # ################

        # elif state.get_state() == "phone_wall_wait_set":
        #     if signal_wall.matches(station1, station2):
        #         state.set_state("phone_wall_set")

        # elif state.get_state() == "phone_wall_set":
        #     time.sleep(2)
        #     state.set_state("rx")
        #     state.set_infoscreen_state("phonetic_alphabet")


        # ################
        # # tx
        # ################

        # elif state.get_state() == "rx":
        #     # pygame.mixer.quit()
        #     time.sleep(0.5)
        #     pygame.mixer.init(channels=1, devicename="RACIJA")
        #     pygame.mixer.music.stop()
        #     pygame.mixer.music.load("./data/laidinisRysys.mp3")
        #     pygame.mixer.music.play()
        #     while pygame.mixer.music.get_busy():
        #         continue
        #     pygame.mixer.music.stop()

        #     state.set_state("tx")
            

        # elif state.get_state() == "tx":

        #     os.system("pactl load-module module-loopback latency_msec=1")
        #     time.sleep(60)
        #     os.system("pactl unload-module module-loopback")

        #     state.set_state("game_end")
        #     pass

        # ################
        # # game_end
        # ################

        # elif state.get_state() == "game_end":
        #     state.set_infoscreen_state("game_end")
        #     state.set_state("game_reset_timer")

        # elif state.get_state() == "game_reset_timer":
        #     # Wait 30 seconds to reset game
        #     with open("states/.playerscreen", "w+") as ps:
        #         ps.write("email_empty")

        #     harris.kill()
        #     signal_wall.kill()
        #     telephone.kill()

        #     pygame.mixer.quit()

        #     time.sleep(30)
        #     state.set_state("idle")
        #     state.set_infoscreen_state("idle")
        #     with open("./states/telkill", "w+") as f:
        #         f.write(telephone.get_state())

        #     time.sleep(1)
        #     exit()
        # ###############
        # # OTHER ENDINGS
        # ###############

        elif state.get_state() == "game_early_end_timeout":
            state.set_infoscreen_state("game_early_end_timeout")
            state.set_state("game_reset_timer")
            pass

        # elif state.get_state() == "game_early_end_error":
        #     state.set_infoscreen_state("game_early_end_error")
        #     state.set_state("game_reset_timer")
        #     pass

if __name__ == "__main__":
    while True:
        main()
