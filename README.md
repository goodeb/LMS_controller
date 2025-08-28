# Presto LMS controller

Turns the Pimornoi Presto into a controller and display for a LMS music system

# Contents
* [Overview](#overview)
* [Getting Started](#getting-started)
* [Using](#using)
* [Customizing Buttons](#customizing-buttons)

# Overview

This project turns the Pimornoi Presto into a controller for a LMS music system. The device itself is not a player, but it is tied to one of the players in the system in order to issue commands and fetch status. When the music system is powered off, the controller turns into a clock. When powered on the default mode shows a the cover art, title, artist and album information for the song that is plying. Touching the screen in either of these two modes will take the device to the first page of control buttons. The configuration of the control buttons and the actions they trigger can be changed by editing the configuration JSON file without then need to dive into the code. This functionality is based on the stream deck project described in more detail here.

## Other Functionality

Screen dimming


# Getting Started

1. Install micropyLMS

First install the micropyLMS package. This can be done using Thony's package system or downloading the file manually. To manually install, download the package from GitHub here. Then copy the file ``micropyLMS.py`` to the Presto's ``/lib`` directory. 

2. Install micropytimer 

Next install the micropytimer package. This can be done using Thony's package system or downloading the file manually. To manually install, download the package from GitHub here. Then copy the file ``micropytimer.py`` to the Presto's ``/lib`` directory. 

3. Copy LMS_controller files to device.

Copy the the main script ``main.py`` and the definitions file ``button_defs.json`` into the Presto's top level directory. Next copy the contents of the projects' lib directory to the lib directory on the Presto. Finally copy the project's art directory and its contents onto the Presto. 

Note that this project overwrites the default ``main.py`` file so that other apps are not available, but after a power loss the device will boot back to the controller automatically. If you want to have this be just another button on the default set up, don't copy ``main.py`` to the device before renaming it.

4. Configure 

Next change the following fields in ``button_defs.json`` to the correct values for your local setup:
* host : this is the local network IP address for the server. If the port is the standard 9000, no additional argument is needed. If a non-default was used in the server setup, then that new value needs to be added into the JSON file here as ``"port":xxxx``
* player : This is the player name that this controller is tied to
* timezone : Pick your local timezone from the list at http://worldtimeapi.org/timezones. This will not only determine the correct time, but also when the clock heeds to be reset for daylight savings time, if its done in that time zone.

Other arguments that are optional to change if you want are:
* night: the time at night when the screen dims. Use 24 hour time instead of AM/PM. If you want a time that is not on the hour, put this in quotes like "22:30"
* morning: the time in the morning when the screen brightens. Use 24 hour time instead of AM/PM. If you want a time that is not on the hour, put this in quotes like "7:30"
* max_text_length: the maximum number of characters shown in the three now playing information fields (title, artist, and album) before the text is truncated with an ellipsis. The text size is rescaled so that all characters fit on the screen, so longer max_text_length values can result in unreadably small text when track info is extremely long.

Be aware that the clock may not set itself correctly during the initial boot up, but it will try again repeatedly until successful.

## Timers

It is also possible to change the timings of automatic actions like how quickly the controller goes back to the default screen after the last button press, how often the now playing information updates, and how quickly the controller activates after the music system turns on. In ``button_defs.json`` there is a block under the heading of ``"timers"``. Each of these has a name and a dictionary of that timer's attributes. The ``"interval"`` attribute defines that timer's timing and is given in milliseconds. For more on timers, how to define them and how they work, see the documentation for the micropytimer package located here.

# Customizing Button Layout and Function

Don't change the 'buttons' on page 0 and 1. These are the clock and now playing screens. The first page of control buttons is page 2. For a full description on how to configure these buttons see the customizing buttons section of the base project https://github.com/goodeb/Presto-Stream-Deck?tab=readme-ov-file#customizing-buttons.
The functions that can be called by a button are in the ``button_action_fns.py`` file in the ``/lib`` directory. Many useful actions already hav a function defined, but additional actions can be implemented without coding by calling the ``press_button()``, ``send_command()``, or ``send_query()`` functions with appropriate arguments.
The easiest option is the ``press_button()`` function, which acts like pressing a button on a remote with the button name given as an argument. The list of possible button names that can be given is in the ``Default.map`` file included in the project folder for easy reference.
If none of these do what is desired, then sending commands or queries via the ``send_command()`` or ``send_query()`` functions are available. The only difference between these functions is that ``send_query()`` captures the server's response and ``send_command()`` does not. The arguments to the functions need to be provided in ``button_defs.json`` file as lists. The function will unwind this list into multiple positional arguments. More information on how to configure these commands can be found at https://lyrion.org/reference/cli/using-the-cli/ under the jsonrpc.js section and the ``<command>`` part of the body of the request. As one example, if you wanted to have a button send the command to mute the player using the ``send_command()`` function as described in the first example here https://lyrion.org/reference/cli/using-the-cli/#examples you would configure the ``fn_name`` and ``args`` fields of the button definition as follows

```
    ...
    "fn_name":"send_command",
    "arg":["mixer","muting","1"],
    ...
```
Of note there is already a ``mute()`` function included in ``button_action_fns.py``.

