# Main game loop
import os
import stat
import time

import pygame

import statecontroller
import signalwall
from harris import Harris
from telephone import Telephone
from pdfgen import generate_pdf
import psutil

def is_system_plugged_in():
    battery = psutil.sensors_battery()
    return battery.power_plugged


def main():
    state = statecontroller.StateController()
    signal_wall = signalwall.SignalWall()
    harris = Harris()
    telephone = Telephone()

    station1 = "Žvalgų būrys"
    station2 = "Jono brigada"

    freq = harris.generate_frequency()

    freq_to_put = str(freq).ljust(9, "0")

    print(freq_to_put)
    print(station1, station2)

    generate_pdf(station2, "151.49")

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
                for _ in range(2):
                    signal_wall.sync()
                    if signal_wall.person_detected and is_system_plugged_in():
                        start = True
                        print("Starting in", 1 - _)
                    else:
                        start = False
                        break
                    time.sleep(0.5)
                if start:
                    state.set_state("phone_check")

                    break

        ################
        # initial_call
        ################

        elif state.get_state() == "phone_check":
            with open("./states/telkill", "r") as f:
                if f.read() == "raised":
                    state.set_infoscreen_state("phone_not_ready")
                    while telephone.get_state() != "putDown":
                        time.sleep(0.2)
                else:
                    state.set_state("initial_call")

        elif state.get_state() == "initial_call":
            if state.single_exec():
                telephone.set_state("ring")
                state.set_infoscreen_state("initial_call")

            if telephone.get_state() == "raised":
                state.set_state("initial_call_up")

        elif state.get_state() == "initial_call_up":
            telephone.play_sound("./data/call1.mp3")
            state.set_state("initial_call_end")
            pass

        elif state.get_state() == "initial_call_end":
            if state.single_exec(): state.set_infoscreen_state("initial_call_up")
            if telephone.get_state() == "putDown":
                state.set_state("show_email")
                state.set_infoscreen_state("email_information")

        ################
        # show_email
        ################

        elif state.get_state() == "show_email":
            with open("states/.playerscreen", "w+") as ps:
                ps.write("email")
            time.sleep(20)
            state.set_state("cipher_wait_on")
            state.set_infoscreen_state("cipher_wait_on")

            ################
            # cipher
            ################

        elif state.get_state() == "cipher_wait_on":
            harris.sync()
            if harris.on:   
                state.set_state("cipher_wait_ready")
                state.set_infoscreen_state("cipher_wait_ready")
            
        elif state.get_state() == "cipher_wait_ready":
            harris.sync()
            if harris.ready:
                state.set_state("cipher_wait_set")
                state.set_infoscreen_state("cipher_enter")

        elif state.get_state() == "cipher_wait_set":
            harris.sync()
            if harris.correct:
                state.set_state("cipher_set")

        elif state.get_state() == "cipher_set":
            state.set_state("cipher_no_link")
            state.set_infoscreen_state("jamming_information")

        elif state.get_state() == "cipher_no_link":
            time.sleep(8)
            state.set_state("second_call")
            state.set_infoscreen_state("initial_call")

        ################
        # second_call
        ################

        elif state.get_state() == "second_call":
            if state.single_exec(): telephone.set_state("ring")
            if telephone.get_state() == "raised":
                state.set_state("second_call_up")
                

        elif state.get_state() == "second_call_up":
            telephone.play_sound("./data/call2.mp3")
            state.set_state("second_call_end")

        elif state.get_state() == "second_call_end":
            if state.single_exec(): state.set_infoscreen_state("initial_call_up")
            if telephone.get_state() == "putDown":
                state.set_state("cipher_off")
                state.set_infoscreen_state("harris_off")

        elif state.get_state() == "cipher_off":
            harris.sync()
            if not harris.on:
                state.set_state("phone_wall_wait_set")
                state.set_infoscreen_state("phone_wall_information")


        ################
        # sign
        ################

        elif state.get_state() == "phone_wall_wait_set":
            if signal_wall.matches(station1, station2):
                state.set_state("phone_wall_set")

        elif state.get_state() == "phone_wall_set":
            time.sleep(2)
            state.set_state("rx")
            state.set_infoscreen_state("phonetic_alphabet")


        ################
        # tx
        ################

        elif state.get_state() == "rx":
            # pygame.mixer.quit()
            time.sleep(0.5)
            pygame.mixer.init(channels=1, devicename="RACIJA")
            pygame.mixer.music.stop()
            pygame.mixer.music.load("./data/laidinisRysys.mp3")
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                continue
            pygame.mixer.music.stop()

            state.set_state("tx")
            

        elif state.get_state() == "tx":

            os.system("pactl load-module module-loopback latency_msec=1")
            time.sleep(60)
            os.system("pactl unload-module module-loopback")

            state.set_state("game_end")
            pass

        ################
        # game_end
        ################

        elif state.get_state() == "game_end":
            state.set_infoscreen_state("game_end")
            state.set_state("game_reset_timer")

        elif state.get_state() == "game_reset_timer":
            # Wait 30 seconds to reset game
            with open("states/.playerscreen", "w+") as ps:
                ps.write("email_empty")

            harris.kill()
            signal_wall.kill()
            telephone.kill()

            pygame.mixer.quit()

            time.sleep(30)
            state.set_state("idle")
            state.set_infoscreen_state("idle")
            with open("./states/telkill", "w+") as f:
                f.write(telephone.get_state())

            time.sleep(1)
            exit()
        ###############
        # OTHER ENDINGS
        ###############

        elif state.get_state() == "game_early_end_timeout":
            state.set_infoscreen_state("game_early_end_timeout")
            state.set_state("game_reset_timer")
            pass

        elif state.get_state() == "game_early_end_error":
            state.set_infoscreen_state("game_early_end_error")
            state.set_state("game_reset_timer")
            pass

if __name__ == "__main__":
    while True:
        main()
