# Cipher machine
import multiprocessing
import pickle
import random
import time

import serial


class Harris:
    def __init__(self):
        self.correct = False
        self.on = False
        self.ready = False

        self.process = multiprocessing.Process(target=self.run)
        self.process.start()

    def kill(self):
        self.process.kill()

    def sync(self):
        try:
            with open("./states/harris", "rb") as f:
                data = pickle.load(f)

                self.correct = data["correct"]
                self.on = data["on"]
                self.ready = data["ready"]
        except:
            time.sleep(1)
            return self.sync()

    def run(self):
        machine = serial.Serial("/dev/ttyACM1", 115200, timeout=1)

        correct = False
        on = False
        ready = False

        while True:
            data = machine.readline()

            if b"correct" in data:
                correct = True
            else:
                correct = False

            if b"on" in data:
                on = True

            elif b"off" in data:
                on = False

            if b"ready" in data:
                ready = True

            with open("./states/harris", "wb") as f:
                pickle.dump({
                    "correct": correct,
                    "on": on,
                    "ready": ready
                }, f)

    def generate_frequency(self):
        # Generate a random integer part (0 to 999)
        integer_part = random.randint(100, 199)

        # Generate a random validation code (0 to 9999)
        validation_code = 60000  # Example validation code

        # Calculate the decimal part based on the validation algorithm
        decimal_part = (200 - integer_part) * 1000

        # Combine the integer and decimal parts
        frequency = integer_part + decimal_part / 100000

        return frequency if self.check_frequency(frequency) else self.generate_frequency()

    @staticmethod
    def check_frequency(frequency):
        # Extract the integer and decimal parts
        integer_part = int(frequency)
        decimal_part = int((frequency - integer_part) * 100000)

        # Check if the last three decimal places are zeros
        if decimal_part % 1000 == 0:
            decimal_part = decimal_part // 1000
            # Perform additional validation using a shared algorithm
            validation_code = integer_part + decimal_part

            if validation_code == 200:  # Example validation code
                return True

        return False
