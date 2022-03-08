#!/bin/python3

# BUGGY Run through another easily killable script or be ready to
# use your task manager.

import os
import sys
from argparse import ArgumentParser
from threading import Thread

if os.name == 'nt':
    import winsound

import socket
from time import sleep
from wakeup import calc, interpret
from errors import EmptyBufferError, PortInUseError

from assets import SPLASH_GIF

__version__ = '1.6.1'

WIN_TITLE = f'Broadcast SniffLer (v{__version__})'

numerical = None





class ArgParser(ArgumentParser):
    def __init__(self):
        super().__init__()

        self.add_argument('-m',
                          '--mute',
                          help="Don't play any sound while operating.",
                          action='store_true',
                          required=False,
                          default=False
                          )

        self.add_argument(
            '--copy-on-exit',
            help="Copy all the outout to the clipboard on exiting.",
            action='store_true',
            required=False,
            default=False
        )


args = ArgParser()
args = args.parse_args()


def install_missing(install_name):
    global numerical

    from os import system
    if not isinstance(install_name, list):
        if not isinstance(install_name, str):
            raise TypeError()
        if install_name != 'prompt-toolkit':
            to_install = install_name.replace(' ', '').split(',')
            to_install = install_name.split(',')
        else:
            to_install = ['prompt-toolkit']
    else:
        to_install = install_name
    if 'prompt-toolkit' in to_install:
        try:
            pass
        except ValueError as e:
            print(
                "Developer Error. Prompt Toolkit must be passed alone or with inspyre-toolbox"
            )

            raise e from e
    try:
        from inspyre_toolbox.humanize import Numerical
    except ModuleNotFoundError:
        print('Installing inspyre-toolbox')
        system('pip install inspyre_toolbox')
        from inspyre_toolbox.humanize import Numerical

    numerical = Numerical
    num_missing = numerical(len(to_install), 'package')
    missing_count = num_missing.count_noun()

    for pkg in to_install:
        print(f"Missing {install_name}, installing...")
        system(f'pip install {pkg}')


missing = []

try:
    from prompt_toolkit.shortcuts import yes_no_dialog
except ImportError as e:
    try:
        install_missing('prompt-toolkit')
        from prompt_toolkit.shortcuts import yes_no_dialog
    except:
        raise

try:
    import PySimpleGUI as psg
except ImportError:
    missing.append('PySimpleGUI')

try:
    from inspyre_toolbox.humanize import Numerical
except ImportError:
    install_missing('inspyre-toolbox')

try:
    import pyperclip as cb
except ImportError:
    missing.append('pyperclip')

if len(missing) >= 1:
    num = Numerical(len(missing), 'package')
    if yes_no_dialog(f"You are missing {num.count_noun()}. Should I install them?"):
        install_missing(missing)

import PySimpleGUI as psg
import pyperclip as cb

div_offset = 3

muted = args.mute
copy_on_exit = args.copy_on_exit

# Declare our theme choice
psg.theme("DarkAmber")

# Set a buffer var to print from
buffer = None

# A var for the daemonized thread to check if we're running
running = False

# Start a socket object
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


def get_win_layout():
    """
    Returns the layout object for our PySimpleGUI window
    Returns
    -------
    layout : iterable
        A list that will act as our layout plot for our window.
    """
    global muted, copy_on_exit

    return [
        [
            psg.Text('Incoming packets:')

        ],

        [
            psg.Multiline(
                'Starting output\n\n\n',
                size=(50, 25),
                key='MULTILINE',
                reroute_cprint=True,
                reroute_stdout=True,
                reroute_stderr=True,
                auto_refresh=True,

            )
        ],
        [
            psg.HSeparator()
        ],
        [
            psg.Checkbox(
                'Mute',
                enable_events=True,
                key='MUTE_CHECK',
                default=muted,
                tooltip="Mute incoming packet ding."
            ),
            psg.VerticalSeparator(),
            psg.Checkbox(
                'Copy on Exit',
                enable_events=True,
                key='COPY_ON_EXIT_CHECK',
                default=copy_on_exit,
                tooltip="Copy the output received upon exiting the program.",
            )

        ],
        [
            psg.Button('Quit', enable_events=True, key='QUIT_BTN'),
            psg.Button('Copy to Clipboard', key='COPY_BTN')

        ]

    ]


def udp_init(host='', port=5005):
    """

    Initialize the socket to listen on the indicated port at the indicated host.

    Args:
        host:
            The host to bind our socket to
        port:
            The port our socket should be listening on.

    Returns:
        None

    """
    sock.bind((host, port))
    # optional: set host to this computer's IP address


def receive(buffer_size=1024):
    data, addr = sock.recvfrom(buffer_size)
    return data, addr


def end():
    sock.close()


def to_cb(vals):
    field = vals['MULTILINE']
    cb.copy(field)


def beep():
    """
    Beeps if instance variable 'muted' is not bool(True)
    Returns
    -------
    None.
    """
    global muted

    if not muted and os.name == 'nt':
        winsound.Beep(1500, 60)


def wrap_message(message: str):
    """

    Returns a formatted output message which boxes off each separate entry received.

    Args:
        message:
            The message you want wrapped.

    Returns:
        The message passed as an argument, but wrapped in a type of text-container.

    """
    global div_offset

    # Set-up a divider
    _div = str('-' * 25)

    # Set up our string to return
    wrapped = ''

    # Add top divider.
    wrapped += f"{_div}\n"

    # Add left wall
    for line in message.splitlines():
        wrapped += str(f'|| {line}' + '\n')

    # Add bottom divider (3 extra dashes to match length with top divider and packet number.
    # ToDo:
    #     Will need to figure out how to add more dashes for packet numbers 10+
    _div_addition = '-' * div_offset
    wrapped += f"{_div}{_div_addition}\n"

    # Return wrapped message to caller.
    return wrapped


# A function to target with our thread spawner.
def listener():
    """
    Listens for UDP broadcast traffic as long as 'running' is bool(True)
    Returns
    -------
    None.
    """
    global buffer, running

    recv_port = 5606

    # Indicate that we are indeed running
    running = True

    while running:

        try:
            udp_init(port=recv_port)
            okay = True
        except OSError as e:
            statement = f'Port {recv_port} is already open by another application. Aborting.'
            okay = False
            raise PortInUseError(statement) from e

        while okay: 
            data, addr = receive()
            beep()
            batt_data = data[4:40]
            batt_data_first35 = batt_data[:35]
            received_crc = batt_data[35]
            calculated_crc = calc(batt_data_first35)
            msg = ""

            if received_crc == calculated_crc:
                (voltage, current, power, high_cell, low_cell, difference,
                 percent, temperatures) = interpret(batt_data)
                batt_data_hex = batt_data.hex()
                avg_temp = (temperatures[0] + temperatures[1] +
                            temperatures[2] + temperatures[3]) / 4.0

                msg += f"From {addr[0]}:{addr[1]} | Listening on port: {recv_port}"
                msg += f"\nCharge Level: {str(percent)}% | "
                msg += f"Temperature: {str(round(avg_temp, 2))}°C "
                msg += f"{str(round((avg_temp * 1.8) + 32.0, 1))}°F | "
                msg += f"Power Stats: Low {str(round(low_cell, 3))}V "
                msg += f"{str(round(voltage, 3))}V "
                msg += f"High {str(round(high_cell, 3))}V "
                msg += f"{str(round(current, 3))}A "
                msg += f"{str(round(power, 1))}W"
                msg += f"\nMessage Hex: {batt_data_hex}"

            else:
                msg = str(
                    f"From: {addr[0]}:{addr[1]} To port: {recv_port} \\\x1fBytes: {len(data)} Data packet received:\\\x1f\n{data.hex()}"
                )

            # Whatever the output, wrap it. (always good advice)
            buffer = wrap_message(msg)

    end()


def safe_exit(window, values=None):
    """
    Just as implied, exits the program safely.
    Exits the program safely, killing the daemonized thread by assigning
    bool(False) to 'running'
    Returns
    -------
    None.
    """
    global running, copy_on_exit
    print("Exiting per user request.")
    running = False
    if copy_on_exit and values is not None:
        to_cb(values)

    if not window.was_closed():
        window.close()

    sys.exit()


def main():
    global buffer, muted, copy_on_exit, div_offset

    # Configure our window, first a title for it

    # Then declare and instantiate the actual window object
    win = psg.Window(
        WIN_TITLE,
        layout=get_win_layout(),
        finalize=True,
        resizable=True, size=(900, 900)

    )

    # Before we start our window let's declare the listener thread
    listen = Thread(target=listener, daemon=True)

    # Then start it. Since it's daemonized and listening to the status of
    # 'running' we don't have to worry about '.join'ing later
    listen.start()

    # Let's set up a cache variable so our GUI will have a reference to decide
    # when one read is different from its last
    last_read = None

    counter = 0

    last_copy_check = None

    buffer_empty_count = 0

    # Start our GUI loop.
    while True:
        event, values = win.Read(timeout=100)

        # If the 'X' button is pressed;
        if event is None:
            print('User exited')
            safe_exit(win, values)
            break

        # If the 'Quit' button is pressed;
        if event == 'QUIT_BTN':
            print('User hit "Quit" button')
            safe_exit(win, values)
            break

        if event == 'MUTE_CHECK':
            muted = values['MUTE_CHECK']

        if event == 'COPY_BTN':
            to_cb(values)

        if event == 'COPY_ON_EXIT_CHECK':
            copy_on_exit = values['COPY_ON_EXIT_CHECK']

        copy_on_exit = bool(values['COPY_ON_EXIT_CHECK'])
        if last_copy_check != copy_on_exit:
            vis = not copy_on_exit
            win['COPY_BTN'].update(visible=vis)

        last_copy_check = copy_on_exit

        # If the buffer is different than the cached buffer;
        if buffer != last_read:
            counter += 1
            count = Numerical(counter)
            packet_count = f"[{count.commify()}]"

            if len(packet_count) != div_offset:
                div_offset = len(packet_count)

            out = f"{packet_count} {buffer} "
            win['MULTILINE'].print(out + '\n')
            last_read = buffer

        if buffer is None:
            buffer_empty_count += 1

            if buffer_empty_count >= 20:
                raise EmptyBufferError(__name__)


if __name__ == "__main__":
    for i in range(1000):
        psg.popup_animated(SPLASH_GIF)

    psg.popup_animated(None)

    main()
