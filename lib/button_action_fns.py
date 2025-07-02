"""
button_action_functions.py 2025-06-27 v 1.1

Author: Brent Goode

File containing the functions that are called when a screen button is pressed.

"""

import utils
from utils import color_converter, set_time, parse_time, show_message
from timer import setup_timer, start_timer, stop_timer
import requests
import json
import time
import micropyLMS

def initialize_other_vars(kwargs):
    """
    Required setup function for using the ButtonSet class with this script.
    """
    other_vars = kwargs.get('other_vars')
    
    if other_vars.get('buzzer_pin'):
        from presto import Buzzer
        global buzzer
        buzzer = Buzzer(other_vars.pop('buzzer_pin'))
    
    utils.timezone = other_vars.pop('timezone','GMT')
    set_time()

    if other_vars.get('timers'):
        for name,timer_def in other_vars.pop('timers').items():
            setup_timer(name,timer_def)

    
    if other_vars.get('night'):
        global night
        night = str(other_vars.pop('night'))
        night_list = night.split(':')
        night_list.append('0')
        night = float(night_list[0])+float(night_list[1])/60.0
    if other_vars.get('morning'):
        global morning
        morning = str(other_vars.pop('morning'))
        morning_list = morning.split(':')
        morning_list.append('0')
        morning = float(morning_list[0])+float(morning_list[1])/60.0
    change_brightness()
        
    if other_vars.get('host'):
        server_url = micropyLMS.build_url(other_vars.pop('host'),
                                          other_vars.pop('prefix','http'),
                                          other_vars.pop('port','9000'),
                                          other_vars.pop('username',None),
                                          other_vars.pop('password',None))
        try:
            global player
            player_name = other_vars.pop('player',None)
            player = micropyLMS.get_player(server_url,player_name)
            if player:
                player.status_update()
            else:
                show_message(board_obj,"Error setting up player")
                time.sleep(10)
                import machine
                machine.reset()
        except Exception as exc:
            print(f'Error setting up player named {player_name} connected to host at {server_url}')
            print(exc)
            raise ValueError(f"Error setting up player named {player_name} connected to host at {server_url}")
        
        ButtonSet.get_button_obj((0,0,0)).label = parse_time(*time.localtime())
        
        if player.power:
            ButtonSet.current_page = 1
            draw_now_playing()
            player.last_update_current_track = player.current_track
            ButtonSet.needs_redrawing = False
            start_timer('now_playing_update')
        else:
            ButtonSet.current_page = 0
            start_timer('check_power')
        
    if other_vars:
        for var_name, var_value in other_vars.items():
            globals()[var_name]=var_value
        
        
def change_brightness():
    """
    Checks time, dims screen between 'night' and 'morning' and sets timer
    for the next brightness change
    """
    now = time.localtime()
    if now[3]+now[4]/60.0 >= night:
        board_obj.set_backlight(0.1)
        change_time = time.mktime((now[0], now[1], now[2], 6, 0, 0, now[6], now[7])) + 86400
    elif  now[3]+now[4]/60.0 < morning:
        board_obj.set_backlight(0.1)
        change_time = time.mktime((now[0], now[1], now[2], 6, 0, 0, now[6], now[7]))
    else:
        board_obj.set_backlight(1)
        change_time = time.mktime((now[0], now[1], now[2], 22, 0, 0, now[6], now[7]))
    setup_timer('change_brightness',{"expiration":change_time,"action":"change_brightness","library":"button_action_fns","running":True,"long":True})


def draw_now_playing():
    """ Pulls scaled image file for cover button and resets label button text
    """
    # draw cover
    url = player.scaled_image_url
    # NOTE: this scales down an image to 240x240, but currently doesn't scale up
    cover_request = requests.get(url)
    with open("art/cover.png",mode='wb') as file:
        file.write(cover_request.content)
    # add text
    if player.title:
        if len(player.title) > 25:
            title = player.title[:21] + '...'
        else:
            title = player.title
    label_text = title
    if player.artist:
        if len(player.artist) > 25:
            artist = player.artist[:21] + '...'
        else:
            artist = player.artist
        label_text += '\n' + artist
    if player.album:
        if len(player.album) > 25:
            album = player.album[:21] + '...'
        else:
            album = player.album
        label_text += '\n' + album
    elif player.remote_title:
        if len(player.remote_title) > 25:
            remote_title = player.remote_title[:21] + '...'
        else:
            remote_title = player.remote_title
        label_text += '\n' + remote_title
    ButtonSet.get_button_obj((1,1,0)).label = label_text
    ButtonSet.needs_redrawing = True
    return

def update_clock():
    """Changes clock time and sets next check"""
    ButtonSet.get_button_obj((0,0,0)).label = parse_time(*time.localtime())
    if ButtonSet.current_page == 0:
        ButtonSet.needs_redrawing = True
    start_timer('clock_update')
    
def menu_inaction():
    """After no interaction for a time goes back to clock or now playing"""
    player.status_update()
    if player.power:
       ButtonSet.current_page = 1
       draw_now_playing()
       start_timer('now_playing_update')
    else:
       ButtonSet.current_page = 0
       ButtonSet.needs_redrawing = True
       player.last_update_current_track =  None
       start_timer('check_power')

def refresh_now_playing_screen():
    """If on and if song has changed since last call, refreshes now playing screen"""
    if player.power:
        start_timer('now_playing_update')
        player.status_update()
        if player.last_update_current_track != player.current_track:
            player.last_update_current_track = player.current_track
            if ButtonSet.current_page == 1:
                draw_now_playing()
    else:
        ButtonSet.current_page = 0 
        ButtonSet.needs_redrawing = True
        player.last_update_current_track =  None
        start_timer('check_power')

def check_power():
    """While power is off, checks if remote source has turned the player on"""
    player.status_update()
    if not player.power:
        start_timer('check_power')
    else:
        ButtonSet.current_page = 1
        if player.last_update_current_track != player.current_track:
            player.last_update_current_track = player.current_track
            draw_now_playing()
        start_timer('now_playing_update')

def jump_to_menu():
    """If user taps screen when in power off/clock mode goes to first menu page"""
    ButtonSet.current_page = 2
    ButtonSet.needs_redrawing = True
    stop_timer('check_power')
    start_timer('menu_interaction')

def next_page_w_interaction():
    """changes to next menu page"""
    ButtonSet.next_page()
    start_timer('menu_interaction')

def previous_page_w_interaction():
    """changes to previous menu page"""
    ButtonSet.previous_page()
    start_timer('menu_interaction')

def play_pause():
    """Toggles play/plause"""
    player.toggle_pause()
    start_timer('menu_interaction')

def previous_track():
    """Goes to begging of this track or previous track in playlist"""
    player.player_query("button", "rew.single")
    start_timer('menu_interaction')

def next_track():
    """Goes to next track in the playlist"""
    player.player_query("button", "fwd.single")
    start_timer('menu_interaction')

def play_kexp():
    """
    Replaces current playlist with the remote stream of the greatest radio station in the world
    Listener powered KEXP - where the music matters. kexp.org
    """
    kexp_url = 'https://kexp.streamguys1.com/kexp160.aac'
    player.load_url(kexp_url)
    start_timer('menu_interaction')

def play_random_songs():
    """Replaces the current playlist with the Random Songs playlist"""
    player.player_query("randomplay", "tracks")
    start_timer('menu_interaction')

def play_random_album():
    """Replaces the current playlist with a randomly chosen album"""
    player.player_query("randomplay", "albums")
    start_timer('menu_interaction')

def play_random_artist():
    """Replaces the current playlist with all tracks by a randomly chosen artist"""
    player.player_query("randomplay", "contributors")
    start_timer('menu_interaction')

def play_favorite_number(number):
    """
    Replaces the current playlist with the item in the favorites list at 
    the position given as the arg. List starts at 0"""
    raw_favorites = player.player_query("favorites","items","0","want_url:1")
    favorites = raw_favorites.get('loop_loop')
    if number in range(len(favorites)):
        single_item_playlist = [favorites[number]]
        player.load_playlist(single_item_playlist)
    else:
        print(f'ERROR: provided favorite number {number} is our of range')
    start_timer('menu_interaction')

def play_playlist_number(number):
    """
    Replaces the current playlist with the item in the saved playlists at 
    the position given as the arg. List starts at 0"""
    get_count = player.player_query("playlists","0","1")
    raw_playlists = player.player_query("playlists","0",str(get_count.get('count',0)),"tags:u")
    playlists = raw_playlists.get('playlists_loop')
    if number in range(len(playlists)):
        single_item_playlist = [playlists[number]]
        player.load_playlist(single_item_playlist)
    else:
        print(f'ERROR: provided playlist number {number} is our of range')
    start_timer('menu_interaction')

def add_to_favorites():
    """Adds the currently playing track to the favorites list"""
    player.status_update()
    if player.remote:
        title = player.remote_title
    else:
        title = player.title
    player.player_query('favorites', 'add', f'url:{player.url}',f'title:{title}')
    start_timer('menu_interaction')

def goto_now_playing():
    """Manually triggers goeing to the now playing screen before inaction time"""
    stop_timer('menu_interaction')
    menu_inaction()

def toggle_power():
    """Turns the player on or off"""
    player.status_update()
    if player.power:
        power_off()
    else:
        power_on()

def power_off():
    """turns the player off and sets local state"""
    player.set_power(False)
    stop_timer('menu_interaction')
    player.last_update_current_track =  None
    start_timer('check_power')
    ButtonSet.current_page = 0
    ButtonSet.needs_redrawing = True

def power_on():
    """turns the player on and sets local state"""
    player.set_power(True)
    start_timer('menu_interaction')

def volume_up(amount):
    """Increases player volume by amount"""
    player.set_volume(f'+{amount}')
    start_timer('menu_interaction')

def volume_down(amount):
    """Decreases player volume by amount"""
    player.set_volume(f'-{amount}')
    start_timer('menu_interaction')

def mute():
    """mutes the player"""
    player.status_update()
    player.set_muting(not player.muting)
    start_timer('menu_interaction')

def shuffle(mode = None):
    """
    Either sets player shuffle mode to the state given as the arg or 
    goes to the next shuffle state if no arg given
    none -> song -> album -> none
    """
    if mode:
        player.set_shuffle(mode)
    else:
        player.player_query("button", "shuffle.single")
    start_timer('menu_interaction')

def repeat(mode = None):
    """
    Either sets player repeat mode to the state given as the arg or 
    goes to the next repeat state if no arg given
    none -> song -> playlist -> none
    """
    if mode:
        player.set_repeat(mode)
    else:
        player.player_query("button", "repeat")
    start_timer('menu_interaction')

def go_to_sleep(time: int | str):
    """Starts a timer for the player to shut off after a number of minutes given as arg"""
    if isinstance(time, int):
        time = str(60*time)
    elif isinstance(time,str):
        time = str(60*int(time))
    player.player_query("sleep", time)
    start_timer('menu_interaction')

def press_button(button_name: str):
    """
    Issues a command to player that matches one of the remote control command
    listed in the Default.map file
    """
    player.player_query("button", button_name)
    start_timer('menu_interaction')

def send_command(*command):
    """
    Generic query to send a command to the LMS server with no return
    For how to structure commands see https://lyrion.org/reference/cli/using-the-cli/
    under the jsonrpc.js section and the command part of the body of the request
    """
    player.player_query(*command)
    start_timer('menu_interaction')

def send_query(*query):
    """
    Generic query to send a command to the LMS server and capture the response
    For how to structure commands see https://lyrion.org/reference/cli/using-the-cli/
    under the jsonrpc.js section and the command part of the body of the request
    """
    start_timer('menu_interaction')
    return player.player_query(*query)
    

def light_backlight(color: str | list | tuple | None = None) -> None:
    """Lights Presto backlight to the color given by color"""
    r,g,b = color_converter(color)
    for i in range(7):
        board_obj.set_led_rgb(i,r,g,b)

def sound_buzzer(tone: int):
    """
    Sounds the buzzer hardware object
    Args:
        tone: the intensity of the buzzer sound. An int from 0 to 255
    """
    buzzer.set_tone(tone)

def cycle_through_colors(address):
    """
    Cycles the outline color of a button throng the global color_cycle list
    Args:
        address: a comma separated string of three ints with the page, row,
            and column of the button
    """
    address = tuple([int(i) for i in address.split(',')])
    this_button = ButtonSet.get_button_obj(address)
    color_cycle.append(color_cycle.pop(0))
    this_button.outline_color = board_obj.display.create_pen(*color_converter(color_cycle[0]))
    this_button.redraw_button()
    
def add_amount_to_label(address,amount):
    """
    Changes the number label of a button at address by amount and redraws
    Args:
        address: a comma separated string of three ints with the page, row,
            and column of the button
        amount: a signed int of the amount to add to the label
    """
    address = tuple([int(i) for i in address.split(',')])
    this_button = ButtonSet.get_button_obj(address)
    this_button.label = str(int(this_button.label)+amount)
    this_button.redraw_button()

def set_label(address,text):
    """
    Sets the label of a button to be the input text and redraws
    Args:
        address: a comma separated string of three ints with the page, row,
            and column of the button
        text: the new text for the label
    """
    address = tuple([int(i) for i in address.split(',')])
    this_button = ButtonSet.get_button_obj(address)
    this_button.label = str(text)
    this_button.redraw_button()

def http_post(url,query_data):
    """
    Makes a POST request to the give url
    Args:
        url: the web page address to send the request to
        query_data: a dictionary object to send to the url
    """
    try:
        request = requests.post(url, json = query_data)
    except Exception as exc:
        print(exc)

def http_get(url,query_data):
    """
    Makes a GET request to the give url
    Args:
        url: the web page address to send the request to
        query_data: a dictionary object to send to the url
    Returns:
        the request response object the web page sent
    """
    try:
        request = requests.get(url, json = query_data)
        result_data = json.loads(request.content.decode(request.encoding))
        return result_data
    except Exception as exc:
        print(exc)

