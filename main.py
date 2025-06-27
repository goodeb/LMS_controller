"""
stream_deck.py 2025-06-02 v 1.0

Author: Brent Goode

Main script for stream deck app

"""

from presto import Presto
from button_set import ButtonSet
from utils import show_message, read_input_file
from timer import check_timers
import ezwifi

board_obj = Presto(full_res=True)

show_message(board_obj,"Loading...")

ezwifi.connect(verbose=True)

buttons_defs, margin_ratio, default_color, background_color, \
    default_font, corner_radius, other_vars = read_input_file('button_defs.json')

buttons = ButtonSet(buttons_defs,
                    board_obj,
                    margin_ratio,
                    default_color,
                    background_color,
                    default_font,
                    corner_radius,
                    other_vars=other_vars)

buttons.draw_page()

while True:
    action_result = buttons.touch_to_action()
    
    check_timers()
    
    if ButtonSet.needs_redrawing:
        buttons.draw_page()
        ButtonSet.needs_redrawing = False
