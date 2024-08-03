import time

import serial
import multiprocessing
import pygame


class Telephone:
    def __init__(self):
        self.process = multiprocessing.Process(target=self.run)
        self.process.start()

    def kill(self):
        self.process.kill()

    def run(self):
        self.started = False
        self.ring = False

        self.ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
        with open("ring", "w+") as f:
            f.write("")

        pygame.mixer.quit()
        time.sleep(0.5)
        pygame.mixer.init(channels=1, devicename="SC1")

        while True:
            with open("ring", "r") as f:
                r = f.read()
                if r == "ring":
                    pygame.mixer.music.stop()
                    pygame.mixer.quit()
                    time.sleep(0.5)
                    pygame.mixer.init(channels=1, devicename="SC1")
                    pygame.mixer.music.load("./data/ring.mp3")
                    pygame.mixer.music.play(-1)
                    self.ring = True
                elif "play" in r:
                    pygame.mixer.music.stop()
                    pygame.mixer.quit()
                    time.sleep(0.5)
                    pygame.mixer.init(channels=1, devicename="SC2")
                    pygame.mixer.music.load(r.replace("play", ""))
                    pygame.mixer.music.play()

            with open("ring", "w+") as f:
                data = self.ser.readline()
                if b"putDown" in data:
                    f.write("putDown")
                    if self.started:
                        pygame.mixer.music.pause()
                        self.started = False
                elif b"raised" in data:
                    f.write("raised")
                    if not self.started and not self.ring:
                        pygame.mixer.init(channels=1, devicename="SC2")
                        pygame.mixer.music.load("./data/425.mp3")
                        pygame.mixer.music.play()

                        self.started = True
                    elif self.ring:
                        self.started = True

    @staticmethod
    def get_state():
        with open("ring", "r") as f:
            return f.read()

    @staticmethod
    def set_state(state):
        with open("ring", "r") as f:
            s = f.read()
            if s != state:
                with open("ring", "w+") as f:
                    f.write(state)

    @staticmethod
    def play_sound(sound):
        with open("ring", "w+") as f:
            f.write("play" + sound)