"""
generate_tz_data.py 2025-11-05 v 1.0

Author: Brent Goode

Script for generate time zone data file for the LMS_Controller project

"""

import argparse
import pytz
from datetime import datetime
import json

time_zone_list = pytz.all_timezones
dst_database = {}

parser = argparse.ArgumentParser()
parser.add_argument('--tz', type=str, default=None, help='Enter the name of a time zone')
parser.add_argument('--show_time_zones', default=False, action='store_true')
args = parser.parse_args()

if args.show_time_zones:
     print(time_zone_list)
     exit()

if args.tz:
    if args.tz not in time_zone_list:
         print(f'Provided time zone {args.tz} not in list')
         print('Will generate full time zone data file')
    else:
         time_zone_list = [args.tz]

for time_zone in time_zone_list:
    tz = pytz.timezone(time_zone)
    start = datetime(2025,1,1,0,0,0,0)
    dst_database[time_zone] = {int(start.timestamp()):int(tz.utcoffset(start).total_seconds())}
    try:
        dst_info = {int(x.timestamp()):int(tz.utcoffset(x).total_seconds()) for x in tz._utc_transition_times if x.year > 2024}
        if dst_info:
            dst_database[time_zone] = dst_info
    except:
        pass

with open('tz_data.json','w') as file:
        json.dump(dst_database,file)
    

