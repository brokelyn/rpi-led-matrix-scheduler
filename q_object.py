

class QObject:

    def __init__(self, priority, id, fnc):
        self.base_prio = priority
        self.curr_prio = priority
        self.call_fnc = fnc

        self.id = id

    def get_fnc(self):
        self.curr_prio = self.base_prio
        return self.call_fnc

    def __lt__(self, other):
        if self.curr_prio < other.curr_prio:
            return True
        else:
            return False

    def adjust_prio(self):
        self.curr_prio = max(1.1, self.curr_prio - 0.2)
