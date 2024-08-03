import time


class StateController:
    def __init__(self):
        self._state = "idle"
        self._first_exec = True
        self._start_time = 0
        self._available_states = {"idle": -1,
                                  "phone_check": 30,
                                  "game_early_end_timeout": -1,
                                  "game_early_end_error": -1,

                                  "initial_call": 30,
                                  "initial_call_up": -1,
                                  "initial_call_end": 20 + 16,
                                  "show_email": -1,
                                  "cipher_wait_on": 60,
                                  "cipher_wait_ready": 240,
                                  "cipher_wait_set": 240,
                                  "cipher_set": -1,
                                  "cipher_no_link": -1,
                                  "cipher_off": 30,
                                  "second_call": 20,
                                  "second_call_up": -1,
                                  "second_call_end": 20 + 16,
                                  "phone_wall_wait_set": 180,
                                  "phone_wall_set": -1,
                                  "rx": -1,
                                  "tx": -1,
                                  "game_reset_timer": -1,
                                  "game_end": -1}

        self._infoscreen_state = "idle"
        self._available_infoscreen_states = ["idle", "game_early_end_timeout", "game_early_end_error",
                                             "initial_call",
                                             "initial_call_up",
                                             "cipher_wait_on",
                                             "cipher_wait_ready",
                                             "email_information",
                                             "cipher_enter",
                                             "jamming_information",
                                             "phone_not_ready",
                                             "phone_wall_information",
                                             "harris_off",
                                             "phonetic_alphabet",
                                             "game_end"
                                             ]

        self._comp_s = None
        self._comp_i = None

    def set_state(self, state):
        print("Setting state to " + state)
        self._start_time = time.time()
        if state in list(self._available_states.keys()):
            self._state = state
            self._first_exec = True
            return True
        else:
            return False

    def get_state(self):
        self.check_timeout()
        return self._state

    def check_timeout(self):
        if self._state in self._available_states.keys():
            if self._available_states[self._state] != -1:
                if time.time() - self._start_time > self._available_states[self._state]:
                    self.set_state("game_early_end_timeout")

    def set_infoscreen_state(self, state):
        if state in self._available_infoscreen_states:
            self._infoscreen_state = state
            with open("./states/info", "w+") as f:
                f.write(state)
            return True
        else:
            return False

    def get_infoscreen_state(self):
        return self._infoscreen_state

    def is_states_changed(self):
        changed = True if self._comp_s != self._state or self._comp_i != self._infoscreen_state else False
        self._comp_s = self._state
        self._comp_i = self._infoscreen_state
        return changed

    def single_exec(self):
        try:
            return self._first_exec
        finally:
            self._first_exec = False
