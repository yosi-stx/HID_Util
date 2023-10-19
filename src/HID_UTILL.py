#!/usr/bin/python3
# C:\Work\Python\HID_Util\src\HID_UTILL.py 

util_verstion = "2023_10_19.c"
DEBUG_SLIPPAGE = 0

from binascii import hexlify
import sys
import argparse
import threading
from time import sleep
from time import process_time as timer

import tkinter as tk
from tkinter import ttk
import tkinter.messagebox
import pywinusb.hid as win_hid
from datetime import datetime
import winsound
import os

import include_dll_path
# work around to solve issue with importing the hidapi.dll
# workaround using "ctypes.CDLL" taken from:
# https://stackoverflow.com/questions/70894915/cant-load-hidapi-with-python-library-hid-on-windows
py_version = sys.version_info[:3]  # get major, minor, and micro version as a tuple
print(py_version)
if py_version < (3, 7, 4):
    print("Python version is less than 3.7.4")
elif py_version > (3, 7, 4):
    print("Python version is greater than 3.7.4")
    import ctypes
    ctypes.CDLL('..\\x64\\hidapi.dll')
else:
    print("Python version is 3.7.4")    

import hid  # after workaround

from string_date_time import get_date_time
from string_date_time import get_date_time_sec
# Define the path to the low battery alarm sound file
sound_file_path = os.path.join(os.path.expandvars("%SystemRoot%"), "media", "Windows Battery Low.wav")

# BOARD_TYPE_MAIN = 0,
# BOARD_TYPE_JOYSTICKS = 1,
# BOARD_TYPE_TOOLS_MASTER = 2,
# BOARD_TYPE_STATION = 3,
# BOARD_TYPE_SUITE2PRIPH = 4,
# BOARD_TYPE_TOOLS_SLAVE = 5,
# BOARD_TYPE_GBU = 6,
# BOARD_TYPE_LAP = 7

# USB\VID_24B3&PID_1005\887D1B510A000A00 - USB Input Device
# VENDOR_ID = 0x24b3 # Simbionix
# PRODUCT_ID = 0x1005 # Simbionix MSP430 Controller
PRODUCT_ID_CTAG = 0x1005 # Simbionix MSP430 Controller
# USB\VID_2047&PID_0302&REV_0200
VENDOR_ID = 0x2047 # Texas Instruments
PRODUCT_ID = 0x0302 # Joystick.
PRODUCT_ID_JOYSTICK = 0x0302 # Joystick.
PRODUCT_ID_ROUTER   = 0x0301 # Router
PRODUCT_ID_TOOLS = 0x0303
PRODUCT_ID_STATION = 0x0304
PRODUCT_ID_GBU_TOOLS = 0x0309
PRODUCT_ID_LAP_NEW_CAMERA = 0x2005
# 2021_01_24
# USB\VID_24B3&PID_2005&REV_0200
# 0x24B3 = 9395
# 0x2005 = 8197
# VENDOR_ID = 0x24b3 # Simbionix
# PRODUCT_ID = 0x2005 # LAP_NEW_CAMERA.
PRODUCT_ID_types =  {
  0x0302: "BOARD_TYPE: Joystick/Universal",
  0x0301: "BOARD_TYPE: Router/Main",
  0x0304: "BOARD_TYPE: STATION",
  0x0303: "BOARD_TYPE: TOOLS_MASTER",
  0x0305: "BOARD_TYPE: SUITE2PRIPH",
  0x0306: "BOARD_TYPE: TOOLS_SLAVE",
  0x0307: "BOARD_TYPE: GBU",
  0x0308: "BOARD_TYPE: LAP camera",
  0x0309: "BOARD_TYPE: GBU-TOOLS_MASTER",
  0x2005: "BOARD_TYPE: PRODUCT_ID_LAP_NEW_CAMERA",  #board type is enforced in FW (descriptors.h)
  0x1965: "yosi"
}

# for recording feature
# FILE1_PATH = "log\hid_" # log.csv"
# start_date_time = get_date_time()
# #FIGURE_FILE1_PATH = FILE1_PATH + start_date_time + ".png"
# FILE1_PATH = FILE1_PATH + start_date_time + ".csv"

if not os.path.exists('log'):
    os.makedirs('log')

SERIAL_NUM_LIST =[]
PRODUCT_ID_LIST =[]
SERIAL_NUMBER = "_"
# file1 = None
# open recording log file:
# file1 = open("C:\Work\Python\HID_Util\src\log\log.csv","w") 

hid_util_fault = 0

READ_SIZE = 64 # The size of the packet
READ_TIMEOUT = 2 # 2ms

WRITE_DATA = bytes.fromhex("3f3ebb00b127ff00ff00ff00ffffffff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")
DEFAULT_WRITE_DATA = WRITE_DATA
WRITE_DATA_CMD_I = bytes.fromhex("3f3ebb00b127ff00ff00ff0049ff33ff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")
# start streaming command:
# 3f 04 82 00 00
WRITE_DATA_CMD_START = bytes.fromhex("3f048200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")
WRITE_DATA_CMD_START_ = bytes.fromhex("3f048200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")
# start streaming command for station 0x303:
WRITE_DATA_CMD_START_0x304 = bytes.fromhex("3f048d00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")
WRITE_DATA_CMD_START_0x303 = bytes.fromhex("3f048300000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")

# Get Board Type command:
# 01h 00h 00h 01h
WRITE_DATA_CMD_GET_BOARD_TYPE = bytes.fromhex("3f040100000100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")
# WRITE_DATA_CMD_START = bytes.fromhex("3f048200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")
# WRITE_DATA_CMD_START = bytes.fromhex("3f048200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")

#.........................................................##........................................
WRITE_DATA_CMD_S = bytes.fromhex("3f3ebb00b127ff00ff00ff0053ff33ff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")
# 'A' - keep Alive + fast BLE update (every 20 msec)
WRITE_DATA_CMD_A = bytes.fromhex("3f3ebb00b127ff00ff00ff0041ff33ff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")
WRITE_DATA_CMD_GET_FW_VERSION = bytes.fromhex("3f040600000100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")
WRITE_DATA_CMD_RST_INS_TORQUE = bytes.fromhex("3f049200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")
# moderate BLE update rate every 50 mSec by 'M' command
WRITE_DATA_CMD_M = bytes.fromhex("3f3ebb00b127ff00ff00ff004dff33ff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")
# set_BSL_mode
# WRITE_DATA_CMD_B = bytes.fromhex("3f3eaa00b127ff00ff00ff004dff33ff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")
#0xAA	Run BSL
WRITE_DATA_CMD_B = bytes.fromhex("3f04aa00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")
# basic start for general command 
WRITE_DATA_CMD___bytearray = bytearray(b'\x3f')  # initialization of the command


SLEEP_AMOUNT = 0.002 # Read from HID every 2 milliseconds
# PRINT_TIME = 1.0 # Print every 1 second
# PRINT_TIME = 0.5 # Print every 0.5 second
PRINT_TIME = 2 # Print every 2 second

START_INDEX = 2 + 4 # Ignore the first two bytes, then skip the version (4 bytes)
# ANALOG_INDEX_LIST = list(range(START_INDEX + 2, START_INDEX + 4 * 2 + 1, 2)) + [START_INDEX + 6 * 2,]
# for 8 analog channels:
ANALOG_INDEX_LIST = list(range(START_INDEX + 2, START_INDEX + 8 * 2 + 1, 2)) 
# for 12+10=22 analog channels:
ANALOG_INDEX_LIST_TOOLS = list(range(START_INDEX + 2, START_INDEX + 22 * 2 + 1, 2)) 
# ANALOG_INDEX_LIST = [8, 10, 12, 14, 16, 18, 20, 22]
COUNTER_INDEX = 2 + 22 + 18 # Ignore the first two bytes, then skip XData1 (22 bytes) and OverSample (==XDataSlave1; 18 bytes)
CMOS_INDEX = 2 + 2   # maybe + 4???
#                       0  1  2  3  4 5 6 7  8 9 1011
# Received data: b'3f26 00 00 00 00 0674fc41 3f4efc70 0033a4513c5a0101210001000000650000000000000000000000167f070dd7aee89baff63fedcfcccb763acf041b00000010'
#                                   TORQUE   INSERTION
# INSERTION_INDEX = 2 + 8
# TORQUE_INDEX = 2 + 4
# after switching the X and Y orientation due to PixArt alignment. 
INSERTION_INDEX = 2 + 4
TORQUE_INDEX = 2 + 8
STATION_CURRENT_INDEX = 25
MAX_LONG_POSITIVE = 2**31
MAX_UNSIGNED_LONG = 2**32
MAX_U16_POSITIVE = 2**15
MAX_U16  = 2**16
MAX_INT16_POSITIVE = 2**15
MAX_UNSIGNED_INT = 2**16
# IMAGE_QUALITY_INDEX = INSERTION_INDEX + 4
IMAGE_QUALITY_INDEX = TORQUE_INDEX + 4
SHUTTER_INDEX = IMAGE_QUALITY_INDEX + 2
FRAME_AVG_INDEX = SHUTTER_INDEX + 3

HID_STREAM_CHANNEL1_STYLE = "HIDStreamChannel1"
HID_STREAM_CHANNEL2_STYLE = "HIDStreamChannel2"
INNER_HANDLE_CHANNEL1_STYLE = "InnerHandleChannel1"
INNER_HANDLE_CHANNEL2_STYLE = "InnerHandleChannel2"
CLICKER_STYLE = "Clicker"
SLEEPTIMER_STYLE = "sleepTimer"
BATTERY_LEVEL_STYLE = "batteryLevel"
MOTOR_CURRENT_STYLE = "motorCurrent"

style_names = [
    HID_STREAM_CHANNEL1_STYLE,
    HID_STREAM_CHANNEL2_STYLE,
    INNER_HANDLE_CHANNEL1_STYLE,
    INNER_HANDLE_CHANNEL2_STYLE,
    CLICKER_STYLE,
    SLEEPTIMER_STYLE,
    BATTERY_LEVEL_STYLE,
    MOTOR_CURRENT_STYLE
]

# global variables
progressbar_styles = list()
progressbars = list()
inner_clicker = list()
red_handle = list()
reset_check = list()
counter_entry = list()
clicker_counter_entry = list()
text_1_entry = list()
text_2_entry = list()
text_3_entry = list()
big_jump_value_entry =  list()
Recording_gap_entry =  list()
special_cmd = 0
ignore_red_handle_button = None
ignore_red_handle_checkbutton = None
ignore_red_handle_state = False
gui_handler_counter = 0
debug_pwm_print = True
debug_check_box = None
root = None
Fw_Version = "NA"
Fw_Date = "NA"
popup_message = 0
stream_data = None
last_stream_data = None
date_time_text = "NA"
big_jump_rt_flag = 0
BJ_rt_insertion = 0        # BJ = big_jump
BJ_rt_prev_insertion = 0
BJ_rt_insertion_hex = 0 
BJ_rt_prev_insertion_hex = 0
Do_Play_Sound_Var = 0
g_recording_flag = 0
file1 = None
g_big_jump_threshold = 1000 
Display_popup_help_Var = 1
g_recording_gap = 1  # the default recording gap is every sample, aka: 1
g_columns = []

def list_hid_devices():
    all_devices = win_hid.HidDeviceFilter().get_devices()
    i = 0

    for device in all_devices:
        # or the VID of TI: 0x2047
        if device.vendor_id == 0x24B3 or device.vendor_id == 0x2047:
            i += 1
            # usage = device.usage
            vendor_id = device.vendor_id
            product_id = device.product_id
            serial_number = device.serial_number
            global SERIAL_NUM_LIST
            global PRODUCT_ID_LIST
            SERIAL_NUM_LIST.append(serial_number)
            PRODUCT_ID_LIST.append(product_id)

            print(f"({i:d}) VID: {vendor_id:04X}, PID: {product_id:04X}, Serial Number: {serial_number}")
    # print(SERIAL_NUM_LIST)

def msg1():
    tkinter.messagebox.showinfo('information', 'Hi! You got a prompt.')
def msg2(txt1,txt2):
    tkinter.messagebox.showinfo(txt1, txt2)
    
def update_checkbox(checkbox, bool_value):
    if (bool_value):
        checkbox.select()
    else:
        checkbox.deselect()

def streaming_button_CallBack():
    global special_cmd
    global ignore_red_handle_state
    special_cmd = 'I'
    ignore_red_handle_state = True

def board_type_button_callback():
    global special_cmd
    special_cmd = 'S'

def alive_button_CallBack():
    global special_cmd
    special_cmd = 'A'

def moderate_button_CallBack():
    global special_cmd
    special_cmd = 'M'

def BSL_mode_button_CallBack():
    global special_cmd
    special_cmd = 'B'
	
def PWM_value_button_CallBack():
    global special_cmd
    global WRITE_DATA_CMD___bytearray
    WRITE_DATA_CMD___bytearray.append(12)
    special_cmd = 'G'

def display_last_stream_callback():
    global last_stream_data
    if last_stream_data != None:
        gui_handler(last_stream_data, do_print=True)
    else:
        print("no streaming data yet!!!")

def start_stop_recording_callback():
    # toggle recording indication
    global recording_label
    global g_recording_flag
    if start_stop_recording_callback.toggle == 1:
        # create a recording file:
        start_recordig()
        # put the indication
        start_stop_recording_callback.toggle = 0
        recording_label.config(text = "Recording ON",foreground="#FF0000",font=("TkDefaultFont", 20, "bold"))
        g_recording_flag = 1
    else:
        # close the recording file:
        stop_recordig()
        # remove the indication
        start_stop_recording_callback.toggle = 1
        recording_label.config(text = ".",foreground="#0000FF",font=("TkDefaultFont", 20))
        g_recording_flag = 0
start_stop_recording_callback.toggle = 1

def on_enter_key(event):
    global g_big_jump_threshold
    global g_recording_gap
    g_big_jump_threshold = int(big_jump_value_entry.get())
    g_recording_gap = int(Recording_gap_entry.get())
    try:
        user_numeric_value = float(g_big_jump_threshold)
        print("User g_big_jump_threshold numeric value:", user_numeric_value)
        user_numeric_value = float(g_recording_gap)
        print("User g_recording_gap numeric value:", user_numeric_value)
    except ValueError:
        print("Invalid numeric value entered.")

def display_help_big_jumps(event):
    global Display_popup_help_Var
    if Display_popup_help_Var.get() == 0:
        return
    # Create a Toplevel window for the popup
    popup = tk.Toplevel()
    popup.wm_title("Help")
    
    # Create and display the help message
    help_message = "Threshold for big jumps:\n sets the value on which it sens BIG JUMP between two consecutive samples."
    label = ttk.Label(popup, text=help_message, padding=20)
    label.pack()

    # Position the popup near the label
    x, y, _, _ = event.widget.bbox("insert")
    x += event.widget.winfo_rootx() + 25
    y += event.widget.winfo_rooty() + 25
    popup.wm_geometry(f"+{x}+{y}")

    # Close the popup when the mouse moves away from the label
    def close_popup(e):
        popup.destroy()

    event.widget.bind("<Leave>", close_popup)

def display_help_pwm_bcd(event):
    global Display_popup_help_Var
    if Display_popup_help_Var.get() == 0:
        return
    # Create a Toplevel window for the popup
    popup = tk.Toplevel()
    popup.wm_title("Help")
    
    # Create and display the help message
    help_message = "A scrollbar command to CMD_0x95: PWM bcd command % \n sets the value on of PWM between 0..100%."
    label = ttk.Label(popup, text=help_message, padding=20)
    label.pack()

    # Position the popup near the label
    x, y, _, _ = event.widget.bbox("insert")
    x += event.widget.winfo_rootx() + 25
    y += event.widget.winfo_rooty() + 40
    popup.wm_geometry(f"+{x}+{y}")

    # Close the popup when the mouse moves away from the label
    def close_popup(e):
        popup.destroy()

    event.widget.bind("<Leave>", close_popup)

def display_help_pwm_cmd_0x97(event):
    global Display_popup_help_Var
    if Display_popup_help_Var.get() == 0:
        return
    # Create a Toplevel window for the popup
    popup = tk.Toplevel()
    popup.wm_title("Help")
    
    # Create and display the help message
    help_message = "command CMD_0x97: PWM \n sets the value on of PWM between 0..255 (255=100%)"
    label = ttk.Label(popup, text=help_message, padding=20)
    label.pack()

    # Position the popup near the label
    x, y, _, _ = event.widget.bbox("insert")
    x += event.widget.winfo_rootx() + 25
    y += event.widget.winfo_rooty() + 40
    popup.wm_geometry(f"+{x}+{y}")

    # Close the popup when the mouse moves away from the label
    def close_popup(e):
        popup.destroy()

    event.widget.bind("<Leave>", close_popup)

prev_pwm = 0
pwm_widget = 0
def show_pwm_values():
    global pwm_widget
    return pwm_widget.get()
    
prev_pwm_16 = 0
pwm_16 = 256
pwm_16_widget = 0
pwm_text_widget = 0
pwm_text = None
def show_pwm_16_values():
    global pwm_16_widget
    global pwm_text_widget
    global pwm_text
    #pwm_percent = pwm_16/(2**16-1)*100
    # pwm_percent = pwm_16/(2**12-1)*100
    pwm_percent = pwm_16/(2**8-1)*100
    temp_txt = ("{:.2f}".format(pwm_percent))
    # str(pwm_16/(2**16-1)*100)
    label_pwm16_text = "PWM: "+ temp_txt +"%"
    pwm_text.set(label_pwm16_text)
    return pwm_16_widget.get()
    
def gui_loop(device):
    do_print = True
    print_time = 0.0
    time = timer()
    # cnt = None
    # prev_cnt = None
    # value = None
    global special_cmd
    # global print_flag
    global debug_pwm_print
    
    while True:
        # Reset the counter
        if (do_print):
            print_time = timer()

        # Write to the device (request data; keep alive)
        if special_cmd == 'I':
            if PRODUCT_ID == PRODUCT_ID_STATION:
                WRITE_DATA = WRITE_DATA_CMD_START_0x304
            elif PRODUCT_ID == PRODUCT_ID_TOOLS or PRODUCT_ID == PRODUCT_ID_GBU_TOOLS:
                WRITE_DATA = WRITE_DATA_CMD_START_0x303 
            else:
                WRITE_DATA = WRITE_DATA_CMD_START
            device.write(WRITE_DATA)
            print("special_cmd Start")
            special_cmd = 0
        elif special_cmd == 'S':
            WRITE_DATA = WRITE_DATA_CMD_GET_BOARD_TYPE
            device.write(WRITE_DATA)
            print("special_cmd CMD_GET_BOARD_TYPE")
            # print_flag = 1
            special_cmd = 0
        elif special_cmd == 'A':
            if PRODUCT_ID != PRODUCT_ID_CTAG: 
                WRITE_DATA = WRITE_DATA_CMD_GET_FW_VERSION
                print("special_cmd A -> WRITE_DATA_CMD_GET_FW_VERSION")
                device.write(WRITE_DATA)
            else:
                WRITE_DATA = WRITE_DATA_CMD_A
                print("special_cmd A -> keep Alive + fast BLE update (every 20 msec)")
            special_cmd = 0
        elif special_cmd == 'M':
            if PRODUCT_ID == PRODUCT_ID_STATION:
                print("special_cmd M -> reset to the Insertion and Torque")
                WRITE_DATA = WRITE_DATA_CMD_RST_INS_TORQUE
                device.write(WRITE_DATA)
            else:
                print("special_cmd M -> moderate BLE update rate every 50 mSec")
                WRITE_DATA = WRITE_DATA_CMD_M
            special_cmd = 0
        elif special_cmd == 'B':
            WRITE_DATA = WRITE_DATA_CMD_B
            if PRODUCT_ID != PRODUCT_ID_CTAG:
                device.write(WRITE_DATA)
            print("special_cmd B -> set_BSL_mode  --- this will stop HID communication with this GUI")
            special_cmd = 0
        elif special_cmd == 'G':
            WRITE_DATA = WRITE_DATA_CMD_G 
            device.write(WRITE_DATA)
            #print("special_cmd G -> set_PWM_value  ")
            special_cmd = 0
        else:
            WRITE_DATA = DEFAULT_WRITE_DATA
        
        if PRODUCT_ID == PRODUCT_ID_CTAG:
            device.write(WRITE_DATA)
        if WRITE_DATA == WRITE_DATA_CMD_B:
            root. destroy() 

        # If not enough time has passed, sleep for SLEEP_AMOUNT seconds
        if (timer() - time) < SLEEP_AMOUNT:
            # if value:
            #     prev_cnt = cnt
            #     cnt = value[COUNTER_INDEX]
            #     if prev_cnt and cnt < prev_cnt:
            #         print("Invalid counter")
            sleep(SLEEP_AMOUNT)

        # handle the PWM command to device
        global prev_pwm
        WRITE_DATA_CMD___bytearray = bytearray(b'\x3f')  # initialization of the command
        pwm_val = show_pwm_values()
        if (prev_pwm) != (pwm_val):
            print("prev_pwm=  ",int(prev_pwm), "     pwm_val= ",int(pwm_val) )
            WRITE_DATA_CMD___bytearray.append(5)
            WRITE_DATA_CMD___bytearray.append(0x95)
            WRITE_DATA_CMD___bytearray.append(1)
            WRITE_DATA_CMD___bytearray.append(0)
            WRITE_DATA_CMD___bytearray.append(0)
            pwm_10 = pwm_val//10
            pwm_01 = pwm_val%10
            hex_pwm_val = pwm_10*16+pwm_01
            WRITE_DATA_CMD___bytearray.append(int(hex_pwm_val))
            for i in range(63-5):
                WRITE_DATA_CMD___bytearray.append(0)
            # print("WRITE_DATA_CMD___bytearray = %s " % WRITE_DATA_CMD___bytearray)
            WRITE_DATA_CMD_G = bytes(WRITE_DATA_CMD___bytearray)
            if debug_pwm_print:
                print("WRITE_DATA_CMD_G = %s " % WRITE_DATA_CMD_G)
            special_cmd = 'G'
        prev_pwm = pwm_val

        global prev_pwm_16
        global pwm_16
        # send_command.py  -c 97 08 00 00 55 20 03 04 05 06 07 08
        WRITE_DATA_CMD___bytearray = bytearray(b'\x3f')  # initialization of the command
        pwm_16 = show_pwm_16_values()
        if (prev_pwm_16) != (pwm_16):
            print("prev_pwm_16=  ",int(prev_pwm_16), "     pwm_16= ",int(pwm_16) )
            WRITE_DATA_CMD___bytearray.append(12)
            WRITE_DATA_CMD___bytearray.append(0x97)
            WRITE_DATA_CMD___bytearray.append(8)
            WRITE_DATA_CMD___bytearray.append(0)
            WRITE_DATA_CMD___bytearray.append(0)
            pwm_16_lo = pwm_16 & 0x00FF
            pwm_16_hi = pwm_16 >> 8
            WRITE_DATA_CMD___bytearray.append(int(pwm_16_lo))
            WRITE_DATA_CMD___bytearray.append(int(pwm_16_hi))
            for i in range(63-6):
                WRITE_DATA_CMD___bytearray.append(0)
            # print("WRITE_DATA_CMD___bytearray = %s " % WRITE_DATA_CMD___bytearray)
            WRITE_DATA_CMD_G = bytes(WRITE_DATA_CMD___bytearray)
            if debug_pwm_print:
                print("WRITE_DATA_CMD_G = %s " % WRITE_DATA_CMD_G)
            special_cmd = 'G'
        prev_pwm_16 = pwm_16

        # global popup_message
        # if( popup_message==1):
            # popup_message==0
            # tkinter.messagebox.showinfo("Welcome to GFG", "East Button clicked")

        # Measure the time
        time = timer()

        # Read the packet from the device
        # value = device.read(READ_SIZE, timeout=READ_TIMEOUT)
        global stream_data
        if( stream_data != None ):
            gui_handler(stream_data, do_print=do_print)
            stream_data = None

#        # Update the GUI
#        if len(value) >= READ_SIZE:
#            handler(value, do_print=do_print)
#            # print("handler called")
#        else:
#            print("---------------------- len(value) < READ_SIZE  ------------------------------")

        # Update the do_print flag
        do_print = (timer() - print_time) >= PRINT_TIME

def start_recordig():
    global file1
    global g_recording_gap
    global g_columns
    
    dummy=[]
    recording_handler(dummy) # call just to set the g_columns of metadata
    FILE1_PATH = "log\hid_" # log.csv"
    start_date_time = get_date_time_sec()
    print("start_date_time: ", start_date_time)
    #FIGURE_FILE1_PATH = FILE1_PATH + start_date_time + ".png"
    FILE1_PATH = FILE1_PATH + start_date_time + ".csv"
    print("Recording result at: ", FILE1_PATH)
    # open recording log file:
    file1 = open(FILE1_PATH,"w") 
    L = [ "# util_verstion=",util_verstion, "\n" ]  
    file1.writelines(L) 
    L = [ "# gap=",str(g_recording_gap), "\n" ]  
    file1.writelines(L) 
    result = ', '.join(g_columns)
    L = [ "# columns=", result, "\n" ]  
    file1.writelines(L) 
    print("-------------------- Recording started...")
    print("L= ",L)

def stop_recordig():
    global file1
    if file1 != None:
        file1.close()
        print("-------------------- Recording Stopped!")
        file1 = None
    else:
        print("Recording file was not found")

def recording_handler(value):
    global file1
    global g_columns
    if recording_handler.once:
        print("   >>> recording_handler.once")
        recording_handler.once = 0
        g_columns.append("Tool Size")
        # g_columns.append("frame_avg")
        g_columns.append("Insertion")
        g_columns.append("Torque")
        # g_columns.append("shutter")
        g_columns.append("Image Quality")
        result = ', '.join(g_columns)
        print("# recording_handler() columns=",result)
    if len(value) >= READ_SIZE:
        tool_size = (int(value[CMOS_INDEX + 1]) << 8) + int(value[CMOS_INDEX])
        tool_size = uint_16_unsigned_to_int_signed(tool_size)
        torque = (int(value[TORQUE_INDEX + 2]) << 24) + (int(value[TORQUE_INDEX+3]) <<16) + (int(value[TORQUE_INDEX]) <<8) + int(value[TORQUE_INDEX+1])  
        insertion = (int(value[INSERTION_INDEX + 2]) << 24) + (int(value[INSERTION_INDEX+3]) <<16) + (int(value[INSERTION_INDEX]) <<8) + int(value[INSERTION_INDEX+1])  
        torque = long_unsigned_to_long_signed(torque)
        insertion = long_unsigned_to_long_signed(insertion)
        image_quality = (int(value[IMAGE_QUALITY_INDEX]) )
        shutter = (int(value[SHUTTER_INDEX]) )
        frame_avg = (int(value[FRAME_AVG_INDEX]) )
        ### recording ::  tool_size, insertion, torque and  image_quality ###
        L = [ str(tool_size),",   ", str(insertion), ", " , str(torque), ", " , str(image_quality), "\n" ]  
        # L = [ str(tool_size),",   ", str(insertion), ", " , str(shutter), ", " , str(image_quality), "\n" ]  
        # - record  Shutter value instead of torque and Frame_Avg instead of tool_size
        # L = [ str(frame_avg),",   ", str(insertion), ", " , str(shutter), ", " , str(image_quality), "\n" ]  
        if file1 != None:
            file1.writelines(L) 
        else:
            print("try to write to closed file... file was not found !!!")
recording_handler.once = 1

def hid_read( device ):
    global stream_data
    global last_stream_data
    global big_jump_rt_flag
    global BJ_rt_insertion
    global BJ_rt_prev_insertion
    global BJ_rt_insertion_hex
    global BJ_rt_prev_insertion_hex
    global g_big_jump_threshold
    
    read_thread_counter = 0
    always_counter = 0
    hid_read.prev_time = datetime.now()
    while True:
        # Read the packet from the device
        always_counter += 1
        value = device.read(READ_SIZE, timeout=READ_TIMEOUT)
        if len(value) >= READ_SIZE:
            stream_data = value
            insertion = stream2insertion(value)
            BJ_rt_insertion_hex = insertion
            rt_insertion = long_unsigned_to_long_signed(insertion)
            if abs(rt_insertion - hid_read.prev_insertion) > g_big_jump_threshold:  #was: > 1000 
                big_jump_rt_flag = 1
                BJ_rt_insertion = rt_insertion
                BJ_rt_prev_insertion = hid_read.prev_insertion
                BJ_rt_prev_insertion_hex = hid_read.prev_insertion_hex
                print(" rt_insertion: %d   (big jump now)" %(rt_insertion))
            hid_read.prev_insertion = rt_insertion
            hid_read.prev_insertion_hex = BJ_rt_insertion_hex
            if value[1] == 38: # meaning: if "Station" streaming packet from device
                last_stream_data = stream_data
            
            
            read_thread_counter += 1
            if read_thread_counter > 1000:
                read_thread_counter = 0 
                current_time = datetime.now()
                delta_1000 = current_time - hid_read.prev_time
                delta_micro = delta_1000.microseconds
                # print(" insertion: %d    delta: %f " %(insertion,delta_micro))
                hid_read.prev_time = current_time
                # print("last_stream_data: %s" % hexlify(last_stream_data))

        # toggle the recording indication
        global recording_label
        global g_recording_flag
        global g_recording_gap
        if g_recording_flag == 1:
            # do recording into the last file that was opened by the button press
            if (always_counter % g_recording_gap) == 0:
                recording_handler(value)
            if (always_counter % 250)  < 175:
                recording_label.config(text = "Recording ON",foreground="#FF0000",font=("TkDefaultFont", 20, "bold"))
            else:
                recording_label.config(text = " ",foreground="#FF0000",font=("TkDefaultFont", 20, "bold"))
        else:
                recording_label.config(text = " ",foreground="#FF0000",font=("TkDefaultFont", 20, "bold"))
            
                
hid_read.prev_time = 0                
hid_read.prev_insertion = 0                
hid_read.prev_insertion_hex = 0                
            
    
    
def long_unsigned_to_long_signed( x ):
    if x > MAX_LONG_POSITIVE:
        x = x - MAX_UNSIGNED_LONG
    return x

def uint_16_unsigned_to_int_signed( x ):
    if x > MAX_U16_POSITIVE:
        x = x - MAX_U16
    return x

def unsigned_to_signed( x ):
    if x > MAX_INT16_POSITIVE:
        x = x - MAX_UNSIGNED_INT
    return x

def date2dec(x):
    s = "%02x" % x
    return s

def stream2insertion(value):
    insertion = (int(value[INSERTION_INDEX + 2]) << 24) + (int(value[INSERTION_INDEX+3]) <<16) + (int(value[INSERTION_INDEX]) <<8) + int(value[INSERTION_INDEX+1])  
    return insertion

# this handler is called only upon a new packet from device
def gui_handler(value, do_print=False):
    # global print_flag

        
    # if print_flag:
        # print("command response: %s" % hexlify(value))
        # print_flag = 0

#   tool_size from CMOS: bytes 5..6
#   3f260000370b
    global gui_handler_counter
    global PRODUCT_ID
    global Last_Stream_Packet_Time
    global date_time_text
    global Total_Stream_Time
    global big_jump_rt_flag
    global BJ_rt_insertion
    global BJ_rt_prev_insertion
    global BJ_rt_insertion_hex
    global BJ_rt_prev_insertion_hex
    global Do_Play_Sound_Var 

    gui_handler_counter = gui_handler_counter + 1  # displayed as: PacketsCounter: 2023_08_09 
    current_time = datetime.now()
    if gui_handler.once == 0:
        gui_handler.once = 1
        gui_handler.start_streaming_time = current_time
    formatted_time = current_time.strftime("%Y_%m_%d__%H:%M:%S")    # Format the date and time in the desired format
    last_date_time_text = date_time_text + formatted_time
    Last_Stream_Packet_Time.config(text = last_date_time_text) # for update the string field.
    total_streaming_time = current_time - gui_handler.start_streaming_time
    
    # Extract hours, minutes, and seconds
    hours = total_streaming_time.seconds // 3600
    minutes = (total_streaming_time.seconds // 60) % 60
    seconds = total_streaming_time.seconds % 60

    # Format the total streaming time in HH:MM:SS format
    formatted_streaming_time = f"{hours:02}:{minutes:02}:{seconds:02}"    
    
    # formatted_time = total_streaming_time.strftime("%Y_%m_%d__%H:%M:%S")    # Format the date and time in the desired format
    # formatted_time = gui_handler.start_streaming_time.strftime("%Y_%m_%d__%H:%M:%S")    # Format the date and time in the desired format
    Total_Stream_Time.config(text = formatted_streaming_time) # for update the string field.
    # print( 

    global hid_util_fault
    hid_util_fault = (int(value[START_INDEX+1]) & 0xF )
    digital = (int(value[START_INDEX + 1]) << 8) + int(value[START_INDEX + 0])
    if PRODUCT_ID == PRODUCT_ID_TOOLS:
        analog = [(int(value[i + 1]) << 8) + int(value[i]) for i in ANALOG_INDEX_LIST_TOOLS]
    else:
        analog = [(int(value[i + 1]) << 8) + int(value[i]) for i in ANALOG_INDEX_LIST]
    counter = (int(value[COUNTER_INDEX + 1]) << 8) + int(value[COUNTER_INDEX])
    tool_size = (int(value[CMOS_INDEX + 1]) << 8) + int(value[CMOS_INDEX])
# Received data: b'3f26 00 00 00 00 0674fc41 3f4efc70 0033a4513c5a0101210001000000650000000000000000000000167f070dd7aee89baff63fedcfcccb763acf041b00000010'
#                                   TORQUE   INSERTION
            # 0674 fc41
# -62847372 = FC41 0674
#   torque from Avago: bytes 6..9
    torque = (int(value[TORQUE_INDEX + 2]) << 24) + (int(value[TORQUE_INDEX+3]) <<16) + (int(value[TORQUE_INDEX]) <<8) + int(value[TORQUE_INDEX+1])  
    torque_hex = torque
    # insertion = (int(value[INSERTION_INDEX + 2]) << 24) + (int(value[INSERTION_INDEX+3]) <<16) + (int(value[INSERTION_INDEX]) <<8) + int(value[INSERTION_INDEX+1])  
    insertion = stream2insertion(value)
    insertion_hex = insertion
    image_quality = (int(value[IMAGE_QUALITY_INDEX]) )
    station_current = (int(value[STATION_CURRENT_INDEX + 1]) << 8) + int(value[STATION_CURRENT_INDEX]) #station Report.current
    if DEBUG_SLIPPAGE == 1:   # Delta insertion
        station_current = unsigned_to_signed(station_current)
    #global MAX_LONG_POSITIVE
    torque = long_unsigned_to_long_signed(torque)
    insertion = long_unsigned_to_long_signed(insertion)

    if do_print:
        print("Received data: %s" % hexlify(value))
        if PRODUCT_ID == PRODUCT_ID_STATION:
            print("insertion[4bytes]: %08x  " % (int(insertion_hex)))
            print("torque[4bytes]: %08x  " % (int(torque_hex)))
            print("insertion[byte-2-3-0-1]: %02x-%02x-%02x-%02x  || image_quality: %02x  %d" % (int(value[INSERTION_INDEX+2]),int(value[INSERTION_INDEX+3]),int(value[INSERTION_INDEX+0]),int(value[INSERTION_INDEX+1]),image_quality, image_quality))
            print("torque[byte-2-3-0-1]: %02x-%02x-%02x-%02x  " % (int(value[TORQUE_INDEX+2]),int(value[TORQUE_INDEX+3]),int(value[TORQUE_INDEX]),int(value[TORQUE_INDEX+1])))
        if PRODUCT_ID == PRODUCT_ID_TOOLS:
            pass 
            # print(analog)
        # print("tool_size    : %d" % tool_size)
        # print("insertion : %d" % insertion , end="")
        # print("   torque : %d" % torque)
    # print every packet received //2022_01_27__12_30
    # print("Packet bytes: %s" % hexlify(value))

    # parsing FW version response :
    if value[2] == 6 and value[3] == 6 and value[4] == 0 and value[5] == 1:
        print("FW friendly version: %s" % hexlify(value))
        #   0 1 2 3 4 5   6 7 8 9 0 1    2 3 4 5 6 7 8 9 0 
        # b'3f0a06060001  030004060321   d6bb2c3fc2b49c3fe877fecef602fffe5787dedfcf750cfb129efe7ffd7ed60daedefca4f9fff58efc5eb47c237eb5a93dd72f55'
        print("")
        Fw_Version = "FW version: "+str(value[6])+"." +str(value[7])+"." +str(value[8])
        print(Fw_Version )
        # print("FW version: "+str(value[6])+"." +str(value[7])+"." +str(value[8]))
        # print("FW date   : "+str(value[9])+"/" +str(value[10])+"/20" +str(value[11]))
        Fw_Date = "FW date   : "+date2dec(value[9])+"/" +date2dec(value[10])+"/20" +date2dec(value[11])
        print(Fw_Date)
        # print("FW date   : "+date2dec(value[9])+"/" +date2dec(value[10])+"/20" +date2dec(value[11]))
        global popup_message
        popup_message = 1;
        # msg2(Fw_Version,Fw_Date)
        popup_txt = Fw_Version + "\n" + Fw_Date
        msg2("Version Info",popup_txt)
        

    # parsing FW version response :
    if value[2] == 1 and value[3] == 1 and value[4] == 0 and value[5] == 1:
        print("Board type: %s" % hexlify(value))
        print("analog: ")
        print(analog)
        #   0 1 2 3 4 5   6 7 8 9 0 1    2 3 4 5 6 7 8 9 0 
        # b'3f0a06060001  030004060321   d6bb2c3fc2b49c3fe877fecef602fffe5787dedfcf750cfb129efe7ffd7ed60daedefca4f9fff58efc5eb47c237eb5a93dd72f55'
        print("")
        print("Board type: "+str(value[6]))

    # if value[2] == 6 and value[3] == 6 and value[4] == 0 :
        # print("value[2] == 6 and value[3] == 6 and value[4] == 0: %s" % hexlify(value))
    # if value[2] == 6 and value[3] == 6 :
        # print("value[2] == 6 and value[3] == 6 : %s" % hexlify(value))
    # if value[2] == 6 :
        # print("value[2] == 6  : %s" % hexlify(value))
        
    clicker_counter = (int(value[COUNTER_INDEX+2 + 1]) << 8) + int(value[COUNTER_INDEX+2]) #clicker_counter --> numeric_box_view
    # sleepTimer = (int(value[COUNTER_INDEX+4 + 1]) << 8) + int(value[COUNTER_INDEX+4])
    sleepTimer = (int(value[32 + 1]) << 8) + int(value[32]) # PWM_command_stream_back

    MotorCur = analog[4]
    clicker_analog = analog[5]
    # ClickerRec = analog[6]
    # batteryLevel = analog[6]
    
    # 
    batteryLevel = analog[7]
    if PRODUCT_ID == PRODUCT_ID_TOOLS:
        batteryLevel = analog[13] #injector_Sig1
    
    # file1 = open("C:\Work\Python\HID_Util\src\log\log2.txt","w") 
    # global file1
    # L = [ str(clicker_analog), "," ,"\n" ]  
    # file1.writelines(L) 




    bool_clicker = bool((digital >> 2) & 0x0001)
    bool_reset = bool((digital >> 4) & 0x0001)
    bool_red_handle = bool((digital >> 7) & 0x0001)
    bool_ignore_red_handle = ignore_red_handle_state
    if PRODUCT_ID != PRODUCT_ID_STATION:
        int_hid_stream_channel1 = analog[1]
        int_inner_handle_channel1 = analog[0]
        int_inner_handle_channel2 = analog[3]
    else:
        int_hid_stream_channel1 = insertion
        int_inner_handle_channel1 = torque
        int_inner_handle_channel2 = image_quality
    int_hid_stream_channel2 = tool_size
    int_clicker = clicker_analog
    int_sleepTimer = sleepTimer
    int_batteryLevel = batteryLevel
    int_MotorCur = MotorCur
    if PRODUCT_ID == PRODUCT_ID_STATION:
        counter = gui_handler_counter
    int_counter = counter
    int_hid_util_fault = hid_util_fault
    int_clicker_counter = clicker_counter
    int_hid_stream_insertion = insertion
    if PRODUCT_ID != PRODUCT_ID_STATION:
        precentage_hid_stream_channel1 = int((int_hid_stream_channel1 / 4096) * 100)
        precentage_inner_handle_channel1 = int((int_inner_handle_channel1 / 4096) * 100)
        precentage_inner_handle_channel2 = int((int_inner_handle_channel2 / 4096) * 100)
    else:
        precentage_hid_stream_channel1 = abs(int((int_hid_stream_channel1 / 1000) * 100))
        precentage_inner_handle_channel1 = abs(int((int_inner_handle_channel1 / 1000) * 100))
        precentage_inner_handle_channel2 = int((int_inner_handle_channel2 / 255) * 100)

    precentage_hid_stream_channel2 = int((int_hid_stream_channel2 / 4096) * 100)
    precentage_clicker = int((int_clicker / 4096) * 100)
    # precentage_sleepTimer = int((int_sleepTimer / 600) * 100)
    PWM_command_stream_back = ((int_sleepTimer/255 )*100) # PWM_command_stream_back
    precentage_sleepTimer = round(PWM_command_stream_back, 0)
    precentage_batteryLevel = int((int_batteryLevel / 4096) * 100)
    if PRODUCT_ID != PRODUCT_ID_STATION:
        precentage_MotorCur = int((int_MotorCur / 4096) * 100)
    else:
        precentage_MotorCur = int((station_current / 4096) * 100)
        if DEBUG_SLIPPAGE == 1:
            # use the station_current to show the Delta insertion , scaled to 255
            precentage_MotorCur = abs(int((station_current / 255) * 100))
            

    # the following lines are allocation of variables (on the left side) to progressbar_styles
    # that were created in my_widgets() function in a sophisticated loop the go over all style_names[]
    # were progressbar_styles[] is global list of styles.
    progressbar_style_hid_stream_channel1 = progressbar_styles[0]
    progressbar_style_hid_stream_channel2 = progressbar_styles[1]
    progressbar_style_inner_handle_channel1 = progressbar_styles[2]
    progressbar_style_inner_handle_channel2 = progressbar_styles[3]
    progressbar_style_clicker = progressbar_styles[4]
    progressbar_style_sleepTimer = progressbar_styles[5]
    progressbar_style_batteryLevel = progressbar_styles[6]
    progressbar_style_MotorCur = progressbar_styles[7]
    
    # the following lines are allocation of variables (on the left side) to ProgressBars
    # that were created in my_widgets() function, were progressbars[] is global list of widgets.
    progressbar_hid_stream_channel1 = progressbars[0]
    progressbar_hid_insertion = progressbars[0] #can I duplicate it?
    progressbar_hid_stream_channel2 = progressbars[1]
    progressbar_inner_handle_channel1 = progressbars[2]
    progressbar_inner_handle_channel2 = progressbars[3]
    progressbar_clicker = progressbars[4]
    progressbar_sleepTimer = progressbars[5]
    progressbar_batteryLevel = progressbars[6]
    progressbar_MotorCur = progressbars[7]
#    checkbox_inner_clicker = inner_clicker
    checkbox_red_handle = red_handle
    checkbox_reset_check = reset_check
    checkbox_ignore_red_handle = ignore_red_handle_checkbutton
    entry_counter = counter_entry
    entry_clicker_counter = clicker_counter_entry
    # entry_fault = text_1_entry
    
    progressbar_style_hid_stream_channel1.configure(HID_STREAM_CHANNEL1_STYLE,text=("%d"%int_hid_stream_channel1))
    progressbar_style_hid_stream_channel2.configure(HID_STREAM_CHANNEL2_STYLE,text=("%d"%int_hid_stream_channel2))
    progressbar_style_inner_handle_channel1.configure(INNER_HANDLE_CHANNEL1_STYLE,text=("%d"%int_inner_handle_channel1))
    progressbar_style_inner_handle_channel2.configure(INNER_HANDLE_CHANNEL2_STYLE,text=("%d"%int_inner_handle_channel2))
    progressbar_style_clicker.configure(CLICKER_STYLE,text=("%d"%int_clicker))
    # progressbar_style_sleepTimer.configure(SLEEPTIMER_STYLE,text=("%d"%sleepTimer))
    progressbar_style_sleepTimer.configure(SLEEPTIMER_STYLE,text=("%d"%precentage_sleepTimer)) # PWM_command_stream_back
    progressbar_style_batteryLevel.configure(BATTERY_LEVEL_STYLE,text=("%d"%batteryLevel))
    if PRODUCT_ID != PRODUCT_ID_STATION:
        progressbar_style_MotorCur.configure(MOTOR_CURRENT_STYLE,text=("%d"%MotorCur))
    else:
        if DEBUG_SLIPPAGE == 1:
            if( station_current > 0 ):
                progressbar_style_MotorCur.configure(MOTOR_CURRENT_STYLE,text=("%d"%station_current), background="green")
            else:
                # for negative direction show the bar in red color 
                progressbar_style_MotorCur.configure(MOTOR_CURRENT_STYLE,text=("%d"%station_current), background="red")
        else:
            progressbar_style_MotorCur.configure(MOTOR_CURRENT_STYLE,text=("%d"%station_current))
    # if ( batteryLevel <= 2310 ):
    if ( batteryLevel <= 2288 ):  # about 2.8 volt
        progressbar_style_batteryLevel.configure(BATTERY_LEVEL_STYLE,foreground="white", background="#d92929")
    else:
        progressbar_style_batteryLevel.configure(BATTERY_LEVEL_STYLE, foreground="white", background="blue")
    

    progressbar_hid_stream_channel1["value"] = precentage_hid_stream_channel1
    progressbar_hid_stream_channel2["value"] = precentage_hid_stream_channel2
    progressbar_inner_handle_channel1["value"] = precentage_inner_handle_channel1
    progressbar_inner_handle_channel2["value"] = precentage_inner_handle_channel2
    progressbar_clicker["value"] = precentage_clicker
    progressbar_sleepTimer["value"] = precentage_sleepTimer
    # progressbar_sleepTimer["maximum"] = 600
    progressbar_sleepTimer["maximum"] = 100 
    progressbar_batteryLevel["value"] = precentage_batteryLevel
    progressbar_MotorCur["value"] = precentage_MotorCur

#    update_checkbox(checkbox_inner_clicker, bool_clicker)
    update_checkbox(checkbox_red_handle, bool_red_handle)
    update_checkbox(checkbox_reset_check, bool_reset)
    update_checkbox(checkbox_ignore_red_handle, bool_ignore_red_handle)

    entry_counter.delete(0, tk.END)
    entry_counter.insert(tk.END, "%d" % int_counter)

    entry_clicker_counter.delete(0, tk.END)
    entry_clicker_counter.insert(tk.END, "%d" % int_clicker_counter)

    # entry_fault.delete(0, tk.END)
    # entry_fault.insert(tk.END, "%d" % int_hid_util_fault)
    text_1_entry.delete(0, tk.END)
    text_1_entry.insert(tk.END, "%08X" % (int(insertion_hex)))

    if big_jump_rt_flag:
        big_jump_rt_flag = 0
        # Play the sound
        if Do_Play_Sound_Var.get():
            winsound.PlaySound("SystemDefault", winsound.SND_ALIAS)
        text_2_entry.delete(0, tk.END)
        text_2_entry.insert(tk.END, "last: %d (0x%08X)   insertion: %d (0x%08X)" % (BJ_rt_prev_insertion, BJ_rt_prev_insertion_hex, BJ_rt_insertion, BJ_rt_insertion_hex,))
        if gui_handler.toggle == 1:
            gui_handler.toggle = 0
            text_2_entry.configure(bd=1,fg="#ff0055" ) 
        else:
            text_2_entry.configure(bd=1,fg="black") # the "fg" argumetn is relevant for tk widgets (not for ttk)
            gui_handler.toggle = 1

        #update the Big_jump_Time_Text
        Big_jump_Time_Text = "Big jump time:  " + formatted_time  
        Big_jump_Time.config(text = Big_jump_Time_Text) # for update the string field.

        # text_2_entry.configure(bg="black", fg="blue")
        text_3_entry.delete(0, tk.END)
        abs_jump = abs(BJ_rt_insertion - BJ_rt_prev_insertion)
        text_3_entry.insert(tk.END, "abs insertion jump: %d (0x%08X)" % (abs_jump,abs_jump))
    
    gui_handler.last_insertion = insertion
    gui_handler.insertion_hex = insertion_hex
    
    root.update()  #end of gui_handler()
gui_handler.once = 0    
gui_handler.start_streaming_time = 0
gui_handler.last_insertion = 0
gui_handler.insertion_hex = 0
gui_handler.toggle = 1

PROGRESS_BAR_LEN = 300
LONG_PROGRESS_BAR_LEN = 590

# function: my_channel_row() - create two ProgressBar with their Label at the same line. 
def my_channel_row(frame, row, label, style):
    ttk.Label(frame,text=label).grid(row=row,sticky=tk.W)

    row += 1

    if PRODUCT_ID != PRODUCT_ID_STATION:
        # InnerHandle
        text_name = "Channel 4 (analog[0] = bytes 8,9)"
        ttk.Label(frame,text=text_name).grid(row=row,column=0)
        text_name = "Channel 7 (analog[3] = bytes 14,15)"
        ttk.Label(frame,text=text_name).grid(row=row,column=1)
    else:
        ttk.Label(frame,text="Torque").grid(row=row,column=0)
        ttk.Label(frame,text="Image Quality").grid(row=row,column=1) # image_quality

    row += 1

    w = ttk.Progressbar(frame,orient=tk.HORIZONTAL,length=PROGRESS_BAR_LEN,style=("%sChannel1"%style))
    progressbars.append(w)
    w.grid(row=row,column=0)
    w = ttk.Progressbar(frame,orient=tk.HORIZONTAL,length=PROGRESS_BAR_LEN,style=("%sChannel2"%style))
    progressbars.append(w)
    w.grid(row=row,column=1)

    return row + 1


def my_seperator(frame, row):
    ttk.Separator(
        frame,
        orient=tk.HORIZONTAL
    ).grid(
        pady=10,
        row=row,
        columnspan=4,
        sticky=(tk.W + tk.E)
    )
    return row + 1

def my_widgets(frame):
    global pwm_widget
    global pwm_16_widget
    bold_font = ("TkDefaultFont", 9, "bold")
    # bold_font = ("TkDefaultFont", 9, "normal")

    # Add style for labeled progress bar
    for name in style_names:
        style = ttk.Style(frame)
        progressbar_styles.append(style)
        style.layout(
            name,
            [
                (
                    "%s.trough" % name,
                    {
                        "children":
                        [
                            ("%s.pbar" % name,{"side": "left", "sticky": "ns"}),
                            ("%s.label" % name,{"sticky": ""})
                        ],
                        "sticky": "nswe"
                    }
                )
            ]
        )
        if name == SLEEPTIMER_STYLE:
            # style.configure(name, foreground="white", background="blue")
            #style.configure(name, foreground="white", background="#d9d9d9")
            style.configure(name, foreground="white", background="#007fff")  # PWM_command_stream_back (azure color)
        elif name == BATTERY_LEVEL_STYLE:
            # style.configure(name, foreground="white", background="blue")
            style.configure(name, foreground="white", background="#d92929")
        else:
            # style.configure(name, background="lime")
            style.configure(name, background="#06B025")
        # print(style)


    row = 0

    # Outer Handle
    ttk.Label(frame,text="HID Streaming Values").grid(row=row,sticky=tk.W)

    global Last_Stream_Packet_Time
    global date_time_text
    date_time_text = "Last stream packet time:  "
    Last_Stream_Packet_Time = ttk.Label(frame,text = date_time_text,font=bold_font, foreground="#000077")
    Last_Stream_Packet_Time.grid(row=row,column=1,sticky=tk.W,)
    # last_date_time_text = date_time_text + "2023_08_10__18_00"
    # Last_Stream_Packet_Time.config(text = last_date_time_text) # for update the string field.


    # ttk.Label(frame,text="Tool Version:  2023_02_05.a").grid(row=row,column=1)
    global device_SN_label
    global SERIAL_NUMBER
    serial_number_text = "Serial Number: " + SERIAL_NUMBER
    # device_SN_label = ttk.Label(frame,text="Serial Number: ", foreground="#0000FF")
    device_SN_label = ttk.Label(frame,text = serial_number_text, foreground="#0000FF")
    device_SN_label.grid(row=row,column=2,sticky=tk.W,)

    row += 1
    ttk.Label(frame,text="----------------------").grid(row=row,sticky=tk.NW)
    
    global Total_Stream_Time
    Total_Stream_Time_Text = "Total stream time:  "
    Total_Stream_Time = ttk.Label(frame,text = Total_Stream_Time_Text,font=bold_font, foreground="#000077")
    Total_Stream_Time.grid(row=row,column=1,sticky=tk.W,)

    row += 1
    if PRODUCT_ID == PRODUCT_ID_STATION:
        text_name =\
"ADCs...  \
\t\t\t\t\t\
NOTE: \tZero value in Tool_size \
\n\t\t\t\t\t\
\t resets the Insertion value"
        ttk.Label(frame,text=text_name).grid(row=row,sticky=tk.NW)
    else:
        ttk.Label(frame,text="ADCs...").grid(row=row,sticky=tk.NW)
        
    # Create the "popup_help" checkbox
    global Display_popup_help_Var 
    # Display_popup_help_Var = tk.BooleanVar()
    Display_popup_help_Var = tk.BooleanVar(value=True)  # Set the default value to True (checked)
    popup_help_checkbox = tk.Checkbutton(frame, text="popup help", variable=Display_popup_help_Var)
    popup_help_checkbox.grid(row=row, column=2)
        
    row += 1

    #
    # 0,1 (packet length,data length); 2,3 (Chanel 1); 4,5 (Chanel 2); 6,7 (Chanel 3); 8,9 (Chanel 4); 10,11 (Chanel 5); 
    # 12,13 (Chanel 6); 14,15 (Chanel 7);
    text_name = "Channel 5 (analog[1] = bytes 10,11)"
    if PRODUCT_ID == PRODUCT_ID_STATION:
        text_name = "Insertion"
    ttk.Label(frame,text=text_name).grid(row=row,column=0)
    
    row += 1
    w = ttk.Progressbar(frame,orient=tk.HORIZONTAL,length=PROGRESS_BAR_LEN,style=("HIDStreamChannel1"))
    progressbars.append(w)
    w.grid(row=row,column=0)

    row -= 1    # go line back for text header

    text_name = "Channel 2 (analog[?] = bytes 4,5)"
    global DEBUG_SLIPPAGE
    if PRODUCT_ID == PRODUCT_ID_STATION:
        text_name = "Tool Size"
        if DEBUG_SLIPPAGE == 1:
            text_name = "Delta insertion (or Tool Size)"
    ttk.Label(frame,text=text_name).grid(row=row,column=1)

    row += 1

    w = ttk.Progressbar(frame,orient=tk.HORIZONTAL,length=PROGRESS_BAR_LEN,style=("HIDStreamChannel2"))
    progressbars.append(w)
    w.grid(row=row,column=1)

    row += 1

    # Seperator
    row = my_seperator(frame, row)
    
    # ------------------------------------------------------
    # using the old convention of my_channel_row() function
    if PRODUCT_ID != PRODUCT_ID_STATION:
        # Inner Handle
        # row = my_channel_row(frame=frame,row=row,label="InnerHandle",style="InnerHandle")
        row = my_channel_row(frame=frame,row=row,label="More ADCs...",style="InnerHandle")
    else:
        row = my_channel_row(frame=frame,row=row,label="PRODUCT_ID_STATION",style="InnerHandle")
    # ------------------------------------------------------
        

    # Seperator
    row = my_seperator(frame, row)

    # Clicker labels
#    ttk.Label(frame,text="InnerClicker").grid(row=row,column=0,sticky=tk.W)
    ttk.Label(frame,text="Channel 9").grid(row=row,column=0)
    ttk.Label(frame,text="Channel_22 Numeric (bytes 44,45)").grid(row=row,column=1)  #ClickerCounter -> Channel_22 Numeric

    row += 1

    # Clicker data
#    w = tk.Checkbutton(frame,state=tk.DISABLED)
#    global inner_clicker
#    inner_clicker = w
#    w.grid(row=row,column=0)
    w = ttk.Progressbar(frame,orient=tk.HORIZONTAL,length=PROGRESS_BAR_LEN,style="Clicker")
    progressbars.append(w)
    w.grid(row=row,column=0)
    # yg: adding clicker counter display
    w = ttk.Entry(frame,width=20,)
    global clicker_counter_entry
    clicker_counter_entry = w
    w.grid(
        #padx=10,#pady=5,
        row=row,
        column=1,#sticky=tk.W,
        )

    row += 1

    # Seperator
    row = my_seperator(frame, row)
    # ------------------------------------------------------

    # was: Red handle and reset button labels
    ttk.Label(frame,text="TBD_digital_1").grid(row=row,column=0) # without the sticky it is in the middle by default.
    ttk.Label(frame,text="TBD_digital_2").grid(row=row,column=1)
    ttk.Label(frame,text="TBD_digital_3").grid(row=row,column=2)

    row += 1

    # Red handle and reset button data
    w = tk.Checkbutton(frame,state=tk.DISABLED)
    global red_handle
    red_handle = w
    w.grid(row=row,column=0)
    w = tk.Checkbutton(frame,state=tk.DISABLED)
    global reset_check
    reset_check = w
    w.grid(row=row,column=1)

    # checkbox for the ignore red handle 
    w = tk.Checkbutton(frame,state=tk.DISABLED)
    # global ignore_red
    # ignore_red = w
    global ignore_red_handle_checkbutton
    ignore_red_handle_checkbutton = w
    w.grid(row=row,column=2)

    # move to lower widgets line:
    # temp_widget = tk.Button(frame,text ="Start streaming",command = streaming_button_CallBack)
    # temp_widget.grid(row=row,column=3)

    row += 1

    # Seperator
    row = my_seperator(frame, row)
    # ------------------------------------------------------

    # Counter
    # ttk.Label(frame,text="PacketsCounter:").grid(row=row,column=0,sticky=tk.E,)
    w = ttk.Label(frame,text="PacketsCounter:")
    w.grid(row=row,column=0,sticky=tk.W,)
    
    w = ttk.Entry(frame,width=25)
    #w.grid(row=row,column=0,sticky=tk.W,)
# width=20 make the Entry window for 20 chars long.    
# adding the state=tk.DISABLED  to widget : makes it gray        
    global counter_entry
    counter_entry = w
    # w.grid(padx=10,pady=5,row=row,column=1,columnspan=2,sticky=tk.W,)
    next_row = row+1
    # w.grid(padx=10,pady=5,row=row,column=0,columnspan=1,sticky=tk.E,)
    w.grid(padx=10,pady=5,row=row,column=0,columnspan=1)
    # columnspan − How many columns widget occupies; default 1

    #                       |||||                       #
    # HID_Util insertion[4bytes]
    bold_font2 = ("TkDefaultFont", 8, "bold")
    ttk.Label(frame,text="Hex(insertion):").grid(row=row,column=1,sticky=tk.W,)
    w = tk.Entry(frame,width=20,fg="blue",font=bold_font2)
    global text_1_entry
    text_1_entry = w
    w.grid(padx=10,pady=5,row=row,column=1,columnspan=1)#,sticky=tk.E,)

    # HID_Util big jump of insertion[4bytes]
    ttk.Label(frame,text="Big jumps:").grid(row=row,column=2,sticky=tk.W,)
    global text_2_entry
    # text_2_entry = ttk.Entry(frame,width=55,)
    text_2_entry = tk.Entry(frame,width=55,fg="blue",font=bold_font2)
    text_2_entry.grid(padx=10,pady=5,row=row,column=2,columnspan=1,sticky=tk.E,)

    row += 1
    # user value for big jumps
    w = ttk.Label(frame,text="big jumps threshold:")
    w.grid(row=row,column=0,sticky=tk.W,)
    w.bind("<Enter>", display_help_big_jumps)

    w = ttk.Entry(frame,width=25)
    global big_jump_value_entry
    big_jump_value_entry = w
    w.grid(padx=10,pady=5,row=row,column=0,columnspan=1)
    # Bind the Enter key to the on_enter_key function
    big_jump_value_entry.bind('<Return>', on_enter_key)
    big_jump_value_entry.insert(tk.END, str(g_big_jump_threshold))
    
    # play sound checkbox:
    # ttk.Label(frame,text="Play sound:").grid(row=row,column=1,sticky=tk.W,)

    # Create the "play sound" checkbox
    global Do_Play_Sound_Var 
    Do_Play_Sound_Var = tk.BooleanVar()
    Do_Play_Sound_checkbox = tk.Checkbutton(frame, text="Play sound (on big jump)", variable=Do_Play_Sound_Var)
    Do_Play_Sound_checkbox.grid(row=row, column=1)


    #  big jumps abs value[4bytes]
    ttk.Label(frame,text="ABS jump:").grid(row=row,column=2,sticky=tk.W,)
    global text_3_entry
    text_3_entry = ttk.Entry(frame,width=55,)
    text_3_entry.grid(padx=10,pady=5,row=row,column=2,columnspan=1,sticky=tk.E,)

    row += 1
    global Big_jump_Time
    Big_jump_Time_Text = "Big jump time:  "
    Big_jump_Time = ttk.Label(frame,text = Big_jump_Time_Text,foreground="#000077") #,font=bold_font, foreground="#000077")
    Big_jump_Time.grid(row=row,column=2,sticky=tk.W,)

    row += 1
    row += 1

    # Seperator
    row = my_seperator(frame, row)
    # ------------------------------------------------------

    # sleepTimer    "#0000FF" 
    # ttk.Label(frame,text="Sleep Timer",foreground="#999999").grid(row=row,column=0,sticky=tk.E,)
    # PWM_command_stream_back
    ttk.Label(frame,text="PWM command stream back").grid(row=row,column=0,sticky=tk.E,)
    # ttk.Label(frame,text="Sleep Timer").grid(row=row,column=0,sticky=tk.E,)
    # ttk.Label.tag_configure("blue", foreground="blue")
    # ttk.Label.tag_add("blue", "1.0", "1.4")

   #w = ttk.Progressbar(frame,orient=tk.HORIZONTAL,length=PROGRESS_BAR_LEN,style="Clicker")
    w = ttk.Progressbar(frame,orient=tk.HORIZONTAL,length=LONG_PROGRESS_BAR_LEN,style="sleepTimer")
    progressbars.append(w)
    w.grid(
        row=row,
        column=1,
        # columnspan=3
        columnspan=2
    )

    row += 1

    # Seperator
    row = my_seperator(frame, row)
    # ------------------------------------------------------

    two_color_style = ttk.Style()
    two_color_style.configure("Main_text.TLabel", foreground="black")
    two_color_style.configure("Second_text.TLabel", foreground="#999999")

    # battery level
    text_name = "batterylevel"
    if PRODUCT_ID == PRODUCT_ID_STATION:
        text_name = "Pressure   (bytes 22,23)"
        if DEBUG_SLIPPAGE == 1:
            text_name = "Tool Size [was: Pressure] (bytes 22,23)"
    if PRODUCT_ID == PRODUCT_ID_TOOLS:
        text_name = "injector_Sig1   (bytes 32,33)"
    
    if DEBUG_SLIPPAGE == 0:
        ttk.Label(frame,text=text_name).grid(row=row,column=0,sticky=tk.E,) #bytes 22,23 
    else:
        # use two colors label:
        # ttk.Label(frame,text=text_name).grid(row=row,column=0,sticky=tk.E,) #bytes 22,23 
        ttk.Label(frame, text="Tool Size ------------------------------", style="Main_text.TLabel").grid(row=row, column=0, sticky=tk.E)
        ttk.Label(frame, text=           "[was: Pressure] (bytes 22,23)", style="Second_text.TLabel").grid(row=row, column=0, sticky=tk.E)

    w = ttk.Progressbar(frame,orient=tk.HORIZONTAL,length=LONG_PROGRESS_BAR_LEN,style="batteryLevel")
    progressbars.append(w)
    w.grid(
        row=row,
        column=1,
        # columnspan=3
        columnspan=2
    )

    row += 1

    # Seperator
    row = my_seperator(frame, row)
    # ------------------------------------------------------

    # Motor Cur
    if PRODUCT_ID != PRODUCT_ID_STATION:
        ttk.Label(frame,text="MotorCurrent").grid(row=row,column=0,sticky=tk.E,)
    else:
        text_name = "Station MotorCurrent (bytes 25,26)"
        if DEBUG_SLIPPAGE == 0:
            ttk.Label(frame,text=text_name).grid(row=row,column=0,sticky=tk.E,)
        else:
            # use two colors label:
            # ttk.Label(frame,text=text_name).grid(row=row,column=0,sticky=tk.E,) #bytes 22,23 
            ttk.Label(frame, text="Delta insertion____________________________________________", style="Main_text.TLabel").grid(row=row, column=0, sticky=tk.E)
            ttk.Label(frame, text=                  "[was: Station MotorCurrent] (bytes 25,26)", style="Second_text.TLabel").grid(row=row, column=0, sticky=tk.E)

    w = ttk.Progressbar(frame,orient=tk.HORIZONTAL,length=LONG_PROGRESS_BAR_LEN,style="motorCurrent")
    progressbars.append(w)
    w.grid(row=row,column=1,columnspan=2)

    row += 1

    # Seperator
    row = my_seperator(frame, row)
    # ------------------------------------------------------
    text_name = "PWM command out:"
    w = ttk.Label(frame,text=text_name) #.grid(row=row,column=0,sticky=tk.W,)
    w.grid(row=row,column=0,sticky=tk.W,)
    w.bind("<Enter>", display_help_pwm_bcd)

    pwm_widget = tk.Scale(frame, from_=0, to=99, orient='horizontal',length=200)#, orient=HORIZONTAL)
    # pwm_widget = tk.Scale(frame, from_=0, to=255, orient='horizontal',length=200)#, orient=HORIZONTAL)
    pwm_widget.grid(row=row,column=0,sticky=tk.E,)
    pwm_widget.bind("<Enter>", display_help_pwm_bcd)

    # w = ttk.Label(frame,text="PWM debug print:").grid(row=row,column=1,sticky='W')
    
    global debug_check_box
    debug_check_box = tk.IntVar()
    # debug_check_box.grid(row=row,column=1)#,tk.sticky='E')
    w = tk.Checkbutton(frame,text="PWM debug print:",variable=debug_check_box,onvalue=1,offvalue=0,command=isChecked)
    # w.grid(row=row,column=1,sticky='W')
    w.grid(row=row,column=1)
    
   
    # temp_widget = tk.Button(frame, text='Print PWM', command=show_pwm_values).grid(row=row,column=1)
    # pwm_16_widget = tk.Scale(frame, from_=0, to=2**16-1, orient='horizontal',length=400)#, orient=HORIZONTAL)
    # pwm_16_widget = tk.Scale(frame, from_=0, to=2**12-1, orient='horizontal',length=300)#, orient=HORIZONTAL)
    # change the scale to 0..255
    pwm_16_widget = tk.Scale(frame, from_=0, to=2**8-1, orient='horizontal',length=400)#, orient=HORIZONTAL)
    # tk.Button(frame,text ="Get Board Type",command = board_type_button_callback)
    pwm_16_widget.grid(row=row,column=2,sticky='W')
    pwm_16_widget.bind("<Enter>", display_help_pwm_cmd_0x97)

    global pwm_text
    # pwm_text = "PWM: "+str(pwm_16)
    pwm_text = tk.StringVar()
    # pwm_text_widget = ttk.Label(frame,text=pwm_text).grid(row=row,column=3,sticky=tk.W,)
    pwm_text_widget = ttk.Label(frame,textvariable=pwm_text).grid(row=row,column=3,sticky=tk.W,)
    row += 1

    # Seperator
    row = my_seperator(frame, row)
    # ------------------------------------------------------

    temp_widget = tk.Button(frame,text ="Get Board Type",command = board_type_button_callback)
    temp_widget.grid(row=row,column=0)

    if PRODUCT_ID != PRODUCT_ID_CTAG: # PRODUCT_ID_LAP_NEW_CAMERA, PRODUCT_ID_STATION...
        temp_widget = tk.Button(frame,text ="Get friendly FW version",command = alive_button_CallBack)
    else:
        temp_widget = tk.Button(frame,text ="Keep alive (fast BLE)",command = alive_button_CallBack)
    temp_widget.grid(row=row,column=1)
    row += 1

    row = my_seperator(frame, row)
    # ------------------------------------------------------ 
    
    temp_widget = tk.Button(frame,text ="Start streaming",command = streaming_button_CallBack, bg="#66FFFF")
    # button_text = tk.Label(frame, text="<u>S</u>tart streaming", justify=tk.CENTER, anchor=tk.W)
    temp_widget.grid(row=row,column=0)
    
    frame.bind('s', lambda event=None: streaming_button_CallBack())


    if PRODUCT_ID == PRODUCT_ID_STATION:
        temp_widget = tk.Button(frame,text ="Reset Ins & Torque",command = moderate_button_CallBack, bg="#00FF00") # green button.
    else:
        temp_widget = tk.Button(frame,text ="Moderate BLE",command = moderate_button_CallBack, bg="#00FF00") 
    temp_widget.grid(row=row,column=1)

    # Bind hotkey to root window :  Ctrl+r to press "Reset Ins & Torque" button.
    frame.bind("<Control-r>", lambda event: moderate_button_CallBack())

    row += 1

    row = my_seperator(frame, row)
    # ------------------------------------------------------ 
    # Display last stream  display_last_stream_callback
    temp_widget = tk.Button(frame,text ="Display last stream",command = display_last_stream_callback)
    temp_widget.grid(row=row,column=0)
    
    # temp_widget = tk.Button(frame,text ="BSL !!!(DONT PRESS)",command = BSL_mode_button_CallBack, bg="red")
    temp_widget = tk.Button(frame,text ="BSL !!!(DONT PRESS)",command = BSL_mode_button_CallBack, bg="#FFE0E0")
    temp_widget.grid(row=row,column=2)
    
    row += 1

    row = my_seperator(frame, row)
    # ------------------------------------------------------ 
    # Start/Stop Recording start_stop_recording
    temp_widget = tk.Button(frame,text ="Start/Stop Recording",command = start_stop_recording_callback)
    temp_widget.grid(row=row,column=0)

    # user value for Recording gap
    w = ttk.Label(frame,text="    Recording gap:")
    w.grid(row=row,column=1,sticky=tk.W,)
    # w.bind("<Enter>", display_help_big_jumps)

    w = ttk.Entry(frame,width=10)
    global Recording_gap_entry
    global g_recording_gap
    Recording_gap_entry = w
    w.grid(padx=10,pady=5,row=row,column=1,columnspan=1)
    # Bind the Enter key to the on_enter_key function
    Recording_gap_entry.bind('<Return>', on_enter_key)
    Recording_gap_entry.insert(tk.END, str(g_recording_gap))


    recording_text = "Press the button to record"
    global recording_label
    recording_label = tk.Label(frame,text = recording_text, foreground="#777777")
    recording_label.grid(row=row,column=1,sticky=tk.W,)

    row += 1

    row = my_seperator(frame, row)
    # ------------------------------------------------------ 

    
def isChecked():
    global debug_pwm_print
    global debug_check_box
    if debug_check_box.get() == 1:
        debug_pwm_print = 1
        print("debug_pwm_print = 1")
        # btn['state'] = NORMAL
        # btn.configure(text='Awake!')
    elif debug_check_box.get() == 0:
        debug_pwm_print = 0
        print("debug_pwm_print = 0")
        # btn['state'] = DISABLED
        # btn.configure(text='Sleeping!')
    else:
        messagebox.showerror('PythonGuides', 'Something went wrong!')

    
def init_parser():
    parser = argparse.ArgumentParser(
        description="Read the HID data from target board.\nIf no argument is given, the program exits."
    )
    parser.add_argument(
        "-v", "--vendor",
        dest="vendor_id",
        metavar="VENDOR_ID",
        type=int,
        nargs=1,
        required=False,
        help="connects to the device with the vendor ID"
    )
    parser.add_argument(
        "-p", "--product",
        dest="product_id",
        metavar="PRODUCT_ID",
        type=int,
        nargs=1,
        required=False,
        help="connects to the device with that product ID"
    )
    parser.add_argument(
        "-a", "--path",
        dest="path",
        metavar="PATH",
        type=str,
        nargs=1,
        required=False,
        help="connects to the device with the given path"
    )
#    parser.add_argument(
#        "-l", "--label",
#        dest="label",
#        metavar="LABEL",
#        type=int,
#        nargs=1,
#        required=False,
#        help="add first line of Label in the CSV file"
#    )
    parser.add_argument(
        "-s", "--serial",
        dest="serial_num",
        metavar="SERIAL_NUM",
        type=str,
        nargs='*',
        required=False,
        # help="connects to the device with that serial number/n example: Arthro -s 123456"
        help="""connects to the device with that serial number
        examples:   \n                                               
        Arthro -s 2426114711002400        or         Arthro -s       
        ;with the second method you can choose from list of devices...
        """
        
    )
    return parser

def main():
    global VENDOR_ID
    global PRODUCT_ID
    global SERIAL_NUMBER
    PATH = None
    
    # open recording log file:
    # file1 = open("C:\Work\Python\HID_Util\src\log\log2.txt","w") 
    
    # list the relevant hid devices and their SN
    list_hid_devices()

    # Parse the command line arguments
    parser = init_parser()
    args = parser.parse_args(sys.argv[1:])

    # Initialize the flags according from the command line arguments
    avail_vid = args.vendor_id != None
    avail_pid = args.product_id != None
    avail_path = args.path != None
    # avail_label = args.label != None
    id_mode = avail_pid and avail_vid
    path_mode = avail_path
    default_mode = (not avail_vid) and (not avail_pid) and (not avail_path)
    if (path_mode and (avail_pid or avail_vid)):
        print("The path argument can't be mixed with the ID arguments")
        return
    if ((not avail_path) and ((avail_pid and (not avail_vid)) or ((not avail_pid) and avail_vid))):
        print("Both the product ID and the vendor ID must be given as arguments")
        return
    #-----------  LABEL  -----------
    #if ( avail_label ):
    #    LABEL = args.label[0]
    #    print("-----------  avail_label - ----------")
    #    if LABEL > 0 :
    #        L = [ "tool_size",",   ", "insertion", ", " , "torque", "\n" ]  
    #        print(L)
    #        file1.writelines(L) 

    if (default_mode):
        print("No arguments were given, defaulting to:")
        print("VENDOR_ID = %X" % VENDOR_ID)
        print("PRODUCT_ID = %X" % PRODUCT_ID)
        id_mode = True
    elif (id_mode):
        VENDOR_ID = args.vendor_id[0]
        PRODUCT_ID = args.product_id[0]  #run over with 772 == 0x304
    elif (path_mode):
        PATH = args.path[0]
    else:
        raise NotImplementedError

    device = None

    try:
        if (id_mode):
            try:
                print("try with default device:")
                print("VENDOR_ID = %X" % VENDOR_ID)
                print("PRODUCT_ID = %X" % PRODUCT_ID)
                device = hid.Device(vid=VENDOR_ID, pid=PRODUCT_ID)
            except:
                print("wrong ID")
                print(" ")
            
            # 0x24B3 = 9395
            # 0x2005 = 8197
            for n in range(7):
                if device is None:
                    try:
                        # print("try with other device")
                        VENDOR_ID = 0x24b3 # Simbionix
                        PRODUCT_ID = 0x2000 + n # LAP_NEW_CAMERA. is 0x2005
                        if PRODUCT_ID not in PRODUCT_ID_LIST:
                            continue
                        # print("VID = %X PID = %X " % VENDOR_ID, PRODUCT_ID)
                        print("try with PID = %X " % PRODUCT_ID)
                        if args.serial_num != None :
                            if len(args.serial_num) == 0:
                                print("\nSelect which device to connect to (0 to exit):")
                                user_in = input()
                                if int(user_in) == 0:
                                    return
                                device_number = int(user_in)-1
                                if device_number < len(SERIAL_NUM_LIST):
                                    # print(SERIAL_NUM_LIST[device_number])
                                    print("You have selected device SN:",SERIAL_NUM_LIST[device_number])
                                    SERIAL_NUMBER = SERIAL_NUM_LIST[device_number]
                                    device = hid.Device(vid=VENDOR_ID, pid=PRODUCT_ID, serial=SERIAL_NUMBER)
                                else:
                                    print("Must be betwenn 1 to ",len(SERIAL_NUM_LIST))
                                    return
                            else:
                                SERIAL_NUMBER = args.serial_num[0]
                                print("SERIAL_NUMBER = ",SERIAL_NUMBER)
                                # return
                                device = hid.Device(vid=VENDOR_ID, pid=PRODUCT_ID, serial=SERIAL_NUMBER)
                        else:
                            device = hid.Device(vid=VENDOR_ID, pid=PRODUCT_ID)
                            SERIAL_NUMBER = device.serial
                        # print(f'-------------->Serial Number: {device.serial}')
                        # print("PRODUCT_ID = %X" % PRODUCT_ID)
                        #device = hid.Device(vid=VENDOR_ID, pid=PRODUCT_ID)
                        # device = hid.Device(vid=0x24B3, pid=0x2005)
                        # print("success vid=0x24B3, pid=0x2005 !!")
                    except:
                        print("wrong ID2")
                    
            if device is None:
                try:
                    # print("try with other device")
                    VENDOR_ID = 0x24b3 # Simbionix
                    PRODUCT_ID = PRODUCT_ID_CTAG
                    print("try with PID = %X " % PRODUCT_ID)
                    device = hid.Device(vid=VENDOR_ID, pid=PRODUCT_ID)
                except:
                    print("wrong ID3")
            # VENDOR_ID = 2047
            # PRODUCT_ID = 304
            # 0x2047 = 8263
            # 0x304 = 772
            # 0x0301    // Product ID (PID) - base for Prime products family
            for n in range(len(PRODUCT_ID_types)):
                if device is None:
                    try:
                        # print("try with other device")
                        VENDOR_ID = 0x2047 # Texas Instrument
                        PRODUCT_ID = 0x301 + n # BOARD_TYPE_MAIN is 0x301
                        if PRODUCT_ID not in PRODUCT_ID_LIST:
                            continue
                        else:
                            print( "---------- PRODUCT_ID  in PRODUCT_ID_LIST")
                        # print("VID = %X PID = %X " % VENDOR_ID, PRODUCT_ID)
                        print("try with PID = %X " % PRODUCT_ID)
                        if args.serial_num != None :
                            if len(args.serial_num) == 0:
                                print("\nSelect which device to connect to (0 to exit):")
                                user_in = input()
                                if int(user_in) == 0:
                                    return
                                device_number = int(user_in)-1
                                if device_number < len(SERIAL_NUM_LIST):
                                    # print(SERIAL_NUM_LIST[device_number])
                                    print("You have selected device SN:",SERIAL_NUM_LIST[device_number])
                                    SERIAL_NUMBER = SERIAL_NUM_LIST[device_number]
                                    device = hid.Device(vid=VENDOR_ID, pid=PRODUCT_ID, serial=SERIAL_NUMBER)
                                else:
                                    print("Must be betwenn 1 to ",len(SERIAL_NUM_LIST))
                                    return
                            else:
                                SERIAL_NUMBER = args.serial_num[0]
                                print("SERIAL_NUMBER = ",SERIAL_NUMBER)
                                # return
                                device = hid.Device(vid=VENDOR_ID, pid=PRODUCT_ID, serial=SERIAL_NUMBER)
                        else:
                            device = hid.Device(vid=VENDOR_ID, pid=PRODUCT_ID)
                            SERIAL_NUMBER = device.serial
                        # print("PRODUCT_ID = %X" % PRODUCT_ID)
                        #device = hid.Device(vid=VENDOR_ID, pid=PRODUCT_ID)
                        # device = hid.Device(vid=0x24B3, pid=0x2005)
                        # print("success vid=0x24B3, pid=0x2005 !!")
                    except:
                        print("wrong ID4")
                    
            if device is None:
                print("no device attached")
            else:
                print("VENDOR_ID = %X" % VENDOR_ID)
                print("PRODUCT_ID = %X" % PRODUCT_ID)
                if PRODUCT_ID in PRODUCT_ID_types:
                    print(PRODUCT_ID_types[PRODUCT_ID])

            

        elif (path_mode):
            device = hid.Device(path=PATH)
        else:
            raise NotImplementedError

        # Initialize the main window
        global root
        global util_verstion
        root = tk.Tk()
        util_title = "SIMBionix HID_Util"+" (version:"+util_verstion+")"
        # root.title("SIMBionix HID_Util")
        root.title(util_title)

        # Initialize the GUI widgets
        my_widgets(root)

        # Create thread that calls
        threading.Thread(target=gui_loop, args=(device,), daemon=True).start()

        threading.Thread(target=hid_read, args=(device,), daemon=True).start()

        # Run the GUI main loop
        root.mainloop()
    finally:
        # close recording file if was not closed by the user.
        global file1
        if file1 != None:
            file1.close()
        if device != None:
            device.close()
        

if __name__ == "__main__":
    main()

'''
history changes
2022_08_25
- to remove:
 "inner_clicker" and "InnerClicker" indication. and to move left the rest of item in this line.
 "red_handle" "RedHandle"
- added: WRITE_DATA_CMD___bytearray
  based on send_command.py 
2022_08_27
- adding the scale widget for PWM.
2023_03_09
- adding explanatory comments
2023_03_16
- put some colors in the buttons 
- move the location of the buttons.
- Ctrl+r to press "Reset Ins & Torque" button.
2023_04_02
- use the station_current to show the Delta insertion , scaled to 255
- for negative direction show the bar in red color
2023_04_09 
- adding debug prints 
2023_08_15
- instead of "Faultindication:" to put the insertion value in Hex (clue about big negative value)
2023_08_20
- adding serial number support by adding the '-s' command argument.
- display the serial number on the main gui. example: Serial Number: 2044365D3452
- adding two informative labels:
-- Last stream packet time:  // this show the last packet time (PC clock)
-- Total stream time:        // this show the time from start sreaming to last packet time
- modifying the Entry widget "Faultindication:" to "Hex(insertion):" for showing the current Insertion in HEX
- adding new Entry widgets:
-- Big jumps: // shows the previous and current insertion when big jumps occur
-- ABS jump:  // shows the absolute value of big jumps of insertion.
- adding sound indication on big jumps of insertion.
- adding Label widget: Big_jump_Time // PC time of the big jump
comment:
- by experiment: the default font size are 8
2023_09_01
- add real time handing of the big_jump: instead of gui_loop thread it is handled in hid_read
- add stream2insertion() function.
2023_09_10
- Create the "play sound" checkbox. using: Do_Play_Sound_Var
- binding the 's' with "Start streaming
2023_09_12 
- add button: "Display last stream" to the GUI. use: display_last_stream_callback()
- add button: "Start/Stop Recording" to the GUI.
2023_09_25
- add recording handler in the hid_read() thread
- fix the label in the GUI back to "Tool Size" by setting: DEBUG_SLIPPAGE = 0
- change the sleepTimer to "PWM command stream back"
2023_09_28 
- add user value g_big_jump_threshold for big jumps indication.
2023_09_28.b
- fix the scroll-bar units 
- add indication in/out for scroll-bar 
2023_10_03
- popup help for label: "big jumps threshold:" 
2023_10_03.b
- fix bug when try to write to closed file1.
2023_10_10.a
- add a popup_help_checkbox to display or not display the popup_help.
2023_10_12.a
- adding functions: display_help_pwm_bcd() display_help_pwm_cmd_0x97()
2023_10_12.b
- add user value g_recording_gap for big jumps indication.
- adding columns as meta data to recording file.
2023_10_16
- removal of redundant print in hid_read()
- fix bug: missing columns in metadata, by adding recording_handler(dummy) call in start_recordig()
2023_10_19
- adding util_verstion to the metadata.
- temp experiments:
-- use Shutter value instead of image_quality in recording.
-- use Shutter value instead of torque in recording and record the image_quality in parallel.
-- record  Shutter value instead of torque and Frame_Avg instead of tool_size
- return the recording parameters to their default: tool_size, insertion, torque, image_quality
-
'''    