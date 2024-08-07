import time


class StateController:
    def __init__(self):
        self._state = "idle"
        self._first_exec = True
        self._start_time = 0
        self._available_states = {"idle": -1,
                                  "phone_check": -1,
                                  "game_early_end_timeout": -1,
                                  "initial_call": 30,
                                  "initial_call_up": 20 + 16,
                                  "dial_up": 60,
                                  "second_call": 60,
                                  "second_call_up": 20 + 16,
                                  "backup_generators": 60,
                                  "circulation_pump": 60,
                                  "condenser": 60,
                                  "water_cleaning": 60,
                                  "idle_pump": 60,
                                  "main_pump": 60,
                                  "control_rods": 60,
                                  "turbine_startup": 60,
                                  "turbine_connection": 180,
                                  "steam_connection": 60,
                                  "power_up": 60,
                                  "game_end": -1}

        self._infoscreen_state = "idle"
        self._available_infoscreen_states = ["idle", "game_early_end_timeout",
                                             "initial_call",
                                             "initial_call_up",
                                             "dial_up",
                                             "wrong_number",
                                             "backup_generators",
                                             "circulation_pump",
                                             "condenser",
                                             "control_rods",
                                             "idle_pump",
                                             "main_pump",
                                             "power_up",
                                             "steam_connection",
                                             "turbine_connection",
                                             "turbine_startup",
                                             "water_cleaning"
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
