# Phonewall communication
import random
import time

import serial
import multiprocessing
import pickle


class SignalWall:
    _endpoints = [
        "Sparno pulkas", "Vilko pulkas", "Šerno kuopa", "Šiaurės kuopa", "NENAUDOJAMA", "Žvalgų būrys", "Ryšio kuopa", "Jono brigada", "Miško būrys", "Vyčio pulkas",
        "Erelio kuopa", "Vytauto pulkas", "Rūko brigada"
    ]

    def __init__(self):
        self.process = multiprocessing.Process(target=self.run)
        self.process.start()

        self.person_detected = False

        self.radio_ptt = False
        self.radio_tone = False

        self.connected_points = []

    def kill(self):
        self.process.kill()

    def sync(self):
        try:
            with open("./states/signalwall", "rb") as f:
                p = pickle.load(f)

                self.person_detected = p["person_detected"]
                self.radio_ptt = p["radio_ptt"]
                self.radio_tone = p["radio_tone"]
                self.connected_points = p["connected_points"]
        except:
            time.sleep(0.5)
            return self.sync()

    def run(self):
        self.person_detected = False

        self.radio_ptt = False
        self.radio_tone = False

        self.connected_points = []

        self.ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
        while True:
            data = self.ser.readline()
            data = data.decode("utf-8").strip().split(" ")
            # Remove empty
            if "" in data:
                data.remove("")

            data = list(map(int, data))

            if 13 in data:
                self.person_detected = True
            else:
                self.person_detected = False

            if 14 in data:
                self.radio_tone = True
            else:
                self.radio_tone = False

            self.connected_points = [self._endpoints[x] for x in data if x in range(13) and x != 4]

            with open("./states/signalwall", "wb") as f:
                pickle.dump({
                    "person_detected": self.person_detected,
                    "radio_ptt": self.radio_ptt,
                    "radio_tone": self.radio_tone,
                    "connected_points": self.connected_points
                }, f)

    def get_random_point(self, point1=None):
        c = random.choice(self._endpoints)
        if c == point1 or c == "NENAUDOJAMA":
            return self.get_random_point(point1)

        return c

    def matches(self, station1, station2):
        # If both stations in connected points, return True
        # No other points should be connected
        self.sync()

        if station1 in self.connected_points and station2 in self.connected_points:
            if len(self.connected_points) == 2:
                return True

        return False
