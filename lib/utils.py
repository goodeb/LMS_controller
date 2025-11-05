"""
utils.py 2025-07-02 v 1.1

Author: Brent Goode

Utility functions for the stream deck project

"""

import json
import time
import ntptime
from micropytimer import setup_timer


def color_converter(color):
    """Takes a variety of color imports and converts them to r,g,b values 
        for use as inputs to Pimoroni pico display.create_pen() method
    """
    if isinstance(color,str):
        if color.lower() == 'black':
            return 0, 0, 0
        elif color.lower() == 'white':
            return 255, 255, 255
        elif color.lower() == 'red':
            return 255, 0, 0
        elif color.lower() == 'green':
            return 0, 255, 0
        elif color.lower() == 'blue':
            return 0, 0, 255
        elif color.lower() == 'yellow':
            return 255, 255, 0
        elif color.lower() == 'magenta':
            return 255, 0, 255
        elif color.lower() == 'aqua':
            return 0, 255, 255
        else:
            print(f'Unknown color: {color}. Defaulting to white.')
            return 255, 255, 255
    elif isinstance(color,tuple) or isinstance(color,list):
        return color[0], color[1], color[2]
    else:
        return 255, 255, 255

def show_message(board_obj,label):
    """Sets the screen of a Pimoroni pico device to show the text given by label.
        Useful for start up or other error messages"""
    board_obj.display.set_pen(board_obj.display.create_pen(*color_converter('black')))
    board_obj.display.clear()
    board_obj.display.set_pen(board_obj.display.create_pen(*color_converter('white')))
    display_width, display_height = board_obj.display.get_bounds()
    board_obj.display.text(label, 5, 10, display_width-10, 6)
    board_obj.update()
 
def read_input_file(json_file):
    """Reads the json input file for a presto-steam-deck project and parses 
        data into the correct form including custom vars for that project"""
    with open(json_file,'r') as file:
        init_data = json.load(file)
        buttons_defs = init_data.pop("buttons_defs")
        margin_ratio = init_data.pop("margin_ratio",0.1)
        default_color = init_data.pop("default_color",None)
        background_color = init_data.pop("background_color",None)
        default_font = init_data.pop("default_font",None)
        corner_radius = init_data.pop("corner_radius",None)
        other_vars = init_data
        return buttons_defs, margin_ratio, default_color, background_color, default_font, corner_radius, other_vars

timezone = None

def set_time():
    """ Uses micropython's ntptime module and local time zone data from the file
        tz_data.json to correctly set the clock to local time and to keep up
        with when to change to/from DTS.
    """
    with open('tz_data.json','r') as file:
        dst_database = json.load(file)
    
    current_tz = dst_database.get(timezone)
    if not current_tz:
        current_tz = {1735718400:0}
    current_tz = {int(k):v for k,v in current_tz.items()}
    
    retries = 1
    total_tries = 4
    success = False
    
    while not success and retries <= total_tries:
        try:
            gmt_time = ntptime.time()
            success = True
        except Exception as exc:
            wait = retries * 3
            print(f'{exc}, Waiting {wait} seconds to retry.')
            time.sleep(wait)
            retries += 1
    if not success:
        print('Maximum retries reached')
        print('Will try setting clock again in ten minutes')
        setup_timer('initial_clock_set',{"interval":600,
                                         "action":"set_time",
                                         "library":"utils",
                                         "running":True,
                                         "long":True})
        return False
    
    still_less = False
    next_time_change = None
    current_delta = 0
    
    for time_change in sorted(current_tz):
        print(time_change)
        if still_less:
            next_time_change = time_change
            still_less = False
        if time_change < gmt_time:
            current_delta = current_tz[time_change]
            still_less = True
    
    time_tuple = time.gmtime(gmt_time + current_delta)
    
    import machine
    machine.RTC().datetime((time_tuple[0],
                            time_tuple[1],
                            time_tuple[2],
                            time_tuple[6],
                            time_tuple[3],
                            time_tuple[4],
                            time_tuple[5],
                            0))
    
    if next_time_change:
        setup_timer('dst_change',{"expiration":next_time_change,
                                "action":"set_time",
                                "library":"utils",
                                "running":True,
                                "long":True})
    return True

def parse_time(year, month, mday, hour, minute, second, weekday, yearday):
    """breaks out the response to time.localimte() and returns a string of the
    time to be displayed on screen
    """
    raw_hour = hour
    am_pm = "AM"
    if raw_hour >= 12:
        am_pm = "PM"
        hour = raw_hour - 12
    else:
        hour = raw_hour
    if hour == 0:
        hour = 12
    if minute < 10:
        minute = f'0{minute}'
        
    return f"{hour}:{minute} {am_pm}"
    