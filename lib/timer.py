"""
timer.py 2025-07-02 v 1.1

Author: Brent Goode

Implements two timer classes 

"""
import time

timer_registry = {}

def check_timers():
    """Iterate through all registered timers and call their check_timer() fn"""
    for name, timer in timer_registry.items():
        timer.check_timer()

def force_restart():
    """Iterate through all registered timers and restart any that are running"""
    for name, timer in timer_registry.items():
        if timer.is_set:
            timer.start()

def setup_timer(name,timer_def):
    """
    Add a new timer to the timer registry
        Args:
            name: a string with the name of this timer
            timer_def: a dictionary containing the timer's definition
    """
    if timer_def.get('long'):
        timer_registry[name] = LongTimer(timer_def)
    else:
        timer_registry[name] = ShortTimer(timer_def)

def start_timer(name):
    """
    Starts a timer
        Args:
            name: string with the timer name to be started
    """
    timer_registry.get(name).start()

def stop_timer(name):
    """
    Stops a timer before it expires. Won't trigger the timer's action
        Args:
            name: string with the timer name to be stope
    """
    timer_registry.get(name).stop()

def trigger_timer(name):
    """
    Triggers a timer's action before it expires.
        Args:
            name: string with the timer name to be triggered
    """
    timer_registry.get(name).stop()
    timer_registry.get(name).action()

def override_timer_expiration(name, interval):
    """
    Overrides previous interval to set expiration to interval from now.
    Args:
        name: string with the timer name to have it expiration overridden
        interval: time till new expiration in milliseconds if ShortTimer
                  seconds if LongTimer
    """
    timer_registry.get(name).override_expiration(interval)

def show_timers():
    """Shows all timers in the registry"""
    for name, timer in timer_registry.items():
        print(f'{name}:\n',repr(timer))

class Timer():
    """
    A parent class for two other types of timers. Doesn't have a function to 
    check the timer. NOT TO BE INSTANTIATED ON ITS OWN

    Attributes
    ----------
    action: callable
        The function to be executed when the timer expires
    is_set: bool
        Whether the timer is set. Determines if the timer is checked or not
    
    Methods
    -------
    stop()
        Stops the timer
    """
    def __init__(self,timer_def):
        exec(f'from {timer_def.get("library")} import {timer_def.get("action")}')
        self.action = locals()[timer_def.get('action')]
        if isinstance(timer_def.get('running'),str):
            if timer_def.get('running').lower() == 'false':
                self.is_set = False
            else:
                self.is_set = True
        else:
            self.is_set = timer_def.get('running')
        
    def __repr__(self):
        return_string = f' Type:{self.__class__.__name__}\n'
        return_string +=f'  Is set:{self.is_set}\n'
        return_string +=f'  Action:{self.action}\n'
        return_string +=f'  Interval:{self.interval}\n'
        return_string +=f'  Expiration:{self.expiration}\n'
        return return_string
    
    def stop(self):
        """Stops the timer before it fires"""
        self.is_set = False

class ShortTimer(Timer):
    """
    A micropython only timer for limited interval lengths in milliseconds

    Short timers are useful for timers that trigger very frequently, but they 
    have a maximum interval based on the hardware's wraparound value. See 
    the tick_ms() documentation https://docs.micropython.org/en/latest/library/time.html
    for more information
    Timers are either defined by interval or expiration, but not both. Interval
    timers trigger at a fixed interval after they are started. Expiration timers
    trigger at a fixed time in their definition. If that time has already passed,
    the timer won't trigger.
    Timers are by default one shot. They do not automatically restart. To
    make a looping timer, the function called by self.action should call the 
    start_timer() method for that timer's name

    Attributes
    ----------
    action: callable
        The function to be executed when the timer expires
    is_set: bool
        Whether the timer is set. Determines if the timer is checked or not
    interval: int
        The number of milliseconds after starting when the timer will fire
    expiration: int
        A fixed clock time after an arbitrary zero when the timer will fire

    Methods
    -------
    start()
        Stars the timer with the correct expiation
    stop()
        Stops the timer before it fires
    check_timer()
        Evaluates whether the time has expired. If so timer is stopped and
        the action is triggered.
    override_expiration(interval: int)
        Overrides previous interval to set expiration to interval milliseconds
        from now.
    """
    def __init__(self,timer_def):
        if timer_def.get('interval'):
            self.interval = timer_def.get('interval')
            self.expiration = time.ticks_add(time.ticks_ms(), self.interval)
        else:
            self.interval = None
            self.expiration = timer_def.get('expiration')
        super().__init__(timer_def)

    def start(self):
        """Stars the timer with the correct expiation"""
        if self.interval:
            self.expiration = time.ticks_add(time.ticks_ms(), self.interval)
        else:
            self.expiration = self.expiration
        self.is_set = True

    def check_timer(self):
        """
        Evaluates if the time has expired. If so timer is stopped and
        the action is triggered.
        """
        now = time.ticks_ms()
        if time.ticks_diff(now, self.expiration) > 0 and self.is_set:
            self.is_set = False # timers are one shot by default
            self.action() # if timer needs to repeat, reset it in action fn
    
    def override_expiration(self, interval: int):
        """
        Overrides previous interval to set expiration to interval milliseconds 
        from now.
        Args:
            interval: integer number of second from now to expire
        """
        self.expiration = time.ticks_add(time.ticks_ms(), interval)

        
class LongTimer(Timer):
    """
    A generic timer with an interval in seconds

    Long timers are useful for longer intervals that do not need much precision.
    Timers are either defined by interval or expiration, but not both. Interval
    timers trigger at a fixed interval after they are started. Expiration timers
    trigger at a fixed time in their definition. If that time has already passed,
    the timer won't trigger.
    Timers are by default one shot. They do not automatically restart. To
    make a looping timer, the function called by self.action should call the 
    start_timer() method for that timer's name

    Attributes
    ----------
    action: callable
        The function to be executed when the timer expires
    is_set: bool
        Whether the timer is set. Determines if the timer is checked or not
    interval: int
        The number of seconds after starting when the timer will fire
    expiration: int
        A fixed clock time in seconds since epoch start when the timer will fire

    Methods
    -------
    start()
        Stars the timer with the correct expiation
    stop()
        Stops the timer before it fires
    check_timer()
        Evaluates whether the time has expired. If so timer is stopped and
        the action is triggered.
    override_expiration(interval: int)
        Overrides previous interval to set expiration to interval seconds 
        from now.
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
        """Stars the timer with the correct expiation"""
        if self.interval:
            self.expiration = time.time() + self.interval
        else:
            self.expiration = self.expiration
        self.is_set = True

    def check_timer(self):
        """
        Evaluates if the time has expired. If so timer is stopped and
        the action is triggered.
        """
        now = time.time()
        if now > self.expiration and self.is_set:
            self.is_set = False # timers are one shot by default
            self.action() # if timer needs to repeat, reset it in action fn

    def override_expiration(self, interval: int):
        """
        Overrides previous interval to set expiration to interval seconds 
        from now.
        Args:
            interval: integer number of second from now to expire
        """
        self.expiration = time.time() + interval
