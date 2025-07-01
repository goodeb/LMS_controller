"""
utils.py 2025-06-02 v 1.0

Author: Brent Goode

Utility functions for the stream deck project

"""

import json
import requests
import time
from timer import setup_timer


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

remembered_timezone=None

def set_time(timezone):
    """ Queries worldtimeapi.org to set the internal clock to the correct local time given 
        by the arg timezone. Full list of timezones at http://worldtimeapi.org/timezones
    """
    if timezone:
        remembered_timezone = timezone
    elif remembered_timezone:
        timezone = remembered_timezone
    else:
        timezone = 'GMT'
    
    retries = 1
    total_tries = 5
    success = False
    response = None
    while not success and retries <= total_tries:
        try:
            response = requests.get(f'http://worldtimeapi.org/api/timezone/{timezone}',timeout=5)
            success = True
        except Exception as exc:
            wait = retries * 3
            print(f'{exc}, Waiting {wait} seconds to retry.')
            time.sleep(wait)
            retries += 1
    if response:
        if response.status_code != 200:
                print(f"Bad return status of: {response}")
                return False
    if not success:
        print('Maximum retries reached')
        print('Will try setting clock again in one hour')
        setup_timer('initial_clock_set',{"interval":3600,"action":"set_time","library":"utils","running":True,"long":True})
        return False
    result_data = json.loads(response.content.decode(response.encoding))
    date_time = result_data.get('datetime').replace('T',':').replace('-',':').replace('+',':').split(':')
    day_of_week = result_data.get('day_of_week')-1
    if day_of_week < 0:
        day_of_week = 6
    print(date_time)
    import machine
    machine.RTC().datetime((int(date_time[0]),
                            int(date_time[1]), 
                            int(date_time[2]), 
                            day_of_week, 
                            int(date_time[3]), 
                            int(date_time[4]), 
                            float(date_time[5]), 
                            0))
    if result_data.get('dst'):
        dst_end = result_data.get('dst_until').replace('T',':').replace('-',':').replace('+',':').split(':')
        dst_end_s = time.mktime((dst_end[0], dst_end[1], dst_end[2], dst_end[3], dst_end[4]+10, dst_end[5], 0, 0)) 
        # dst_until is in GMT, and we just set our clock to local
        dst_end_s += result_data.get('raw_offset') + result_data.get('dst_offset')
        expiration_time = dst_end_s
    else:
        recheck_time = time.mktime((date_time[0], date_time[1], date_time[2], 2, 10, 0, date_time[6], date_time[7])) + 86400
        expiration_time = recheck_time
    setup_timer('dst_change',{"expiration":expiration_time,"action":"set_time","library":"utils","running":True,"long":True})
    return True

def parse_time(year, month, mday, hour, minute, second, weekday, yearday):
    """breaks out the response to time.localimte() and returns a string of the time
        to be displayed on screen
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

