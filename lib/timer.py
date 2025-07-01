
import time

timer_registry = {}

def check_timers():
    for name, timer in timer_registry.items():
        timer.check_timer()

def setup_timer(name,timer_def):
    if timer_def.get('long'):
        timer_registry[name] = LongTimer(timer_def)
    else:
        timer_registry[name] = ShortTimer(timer_def)

def start_timer(name):
    timer_registry.get(name).start()

def stop_timer(name):
    timer_registry.get(name).stop()

def show_timers():
    for name, timer in timer_registry.items():
        print(f'{name}:\n',repr(timer))

class Timer():
    """
    """
    def __init__(self,timer_def):
        exec(f'from {timer_def.get("library")} import {timer_def.get("action")}')
        self.action = locals()[timer_def.get('action')]
        self.is_set = timer_def.get('running')
    
    def __repr__(self):
        return_string = f' Type:{self.__class__.__name__}\n'
        return_string +=f'  Is set:{self.is_set}\n'
        return_string +=f'  Action:{self.action}\n'
        return_string +=f'  Interval:{self.interval}\n'
        return_string +=f'  Expiration:{self.expiration}\n'
        return return_string
    
    def stop(self):
        self.is_set = False

class ShortTimer(Timer):
    """
    """
    def __init__(self,timer_def):
        if timer_def.get('interval'):
            self.interval = 1000*timer_def.get('interval')
            self.expiration = time.ticks_ms() + self.interval
        else:
            self.interval = None
            self.expiration = timer_def.get('expiration')
        super().__init__(timer_def)

    def start(self):
        if self.interval:
            self.expiration = time.ticks_ms() + self.interval
        else:
            self.expiration = self.get('expiration')
        self.is_set = True

    def check_timer(self):
        now = time.ticks_ms()
        if time.ticks_diff(now, self.expiration) > 0 and self.is_set:
            self.is_set = False # timers are one shot by default
            self.action() # if timer needs to repeat, reset it in action fn
        
class LongTimer(Timer):
    """
    """
    def __init__(self,timer_def):
        if timer_def.get('interval'):
            self.interval = timer_def.get('interval')
            self.expiration = time.time() + self.interval
        else:
            self.interval = None
            self.expiration = timer_def.get('expiration')
        super().__init__(timer_def)

    def start(self):
        if self.get('interval'):
            self.expiration = time.time() + self.interval
        else:
            self.expiration = self.get('expiration')
        self.is_set = True

    def check_timer(self):
        now = time.time()
        if now > self.expiration and self.is_set:
            self.is_set = False # timers are one shot by default
            self.action() # if timer needs to repeat, reset it in action fn


