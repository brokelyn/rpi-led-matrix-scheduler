
class Subtask:

    def __init__(self, add_loop, rmv_loop, add_event):
        self.add_fnc = add_loop
        self.rmv_fnc = rmv_loop
        self.add_event_fnc = add_event
        self.fnc_id = None
