#!/usr/bin/python3
# C:\Work\Python\HID_Util\src\HID_recorder.py

from binascii import hexlify
import sys
import argparse
import threading
from time import perf_counter as timer

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

# import os
# BOARD_TYPE_MAIN = 0,
# BOARD_TYPE_JOYSTICKS = 1,
# BOARD_TYPE_TOOLS_MASTER = 2,
# BOARD_TYPE_STATION = 3,
# BOARD_TYPE_SUITE2PRIPH = 4,
# BOARD_TYPE_TOOLS_SLAVE = 5,
# BOARD_TYPE_GBU = 6,
# BOARD_TYPE_LAP = 7

# VENDOR_ID = 0x24b3 # Simbionix
# PRODUCT_ID = 0x1005 # Simbionix MSP430 Controller
PRODUCT_ID_CTAG = 0x1005 # Simbionix MSP430 Controller
# USB\VID_2047&PID_0302&REV_0200
VENDOR_ID = 0x2047 # Texas Instruments
PRODUCT_ID = 0x0302 # Joystick.
PRODUCT_ID_JOYSTICK = 0x0302 # Joystick.
PRODUCT_ID_ROUTER   = 0x0301 # Router
PRODUCT_ID_STATION = 0x0304
PRODUCT_ID_LAP_NEW_CAMERA = 0x2005
PRODUCT_ID_LAP_OLD_CAMERA = 0x3005
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
  0x030B: "BOARD_TYPE: KFIR_SINGA",
  0x2005: "BOARD_TYPE: PRODUCT_ID_LAP_NEW_CAMERA",  #board type is enforced in FW (descriptors.h)
  0x3005: "BOARD_TYPE: PRODUCT_ID_LAP_OLD_CAMERA",  #board type is enforced in FW (descriptors.h)
  0x1965: "yosi"
}

FILE1_PATH = "log\hid_log.csv"
# if not os.path.exists('log'):
    # os.makedirs('log')
# file1 = None
# open recording log file:
# file1 = open("C:\Work\Python\HID_Util\src\log\log.csv","w") 
# file1 = open(FILE1_PATH,"w") 
# file1 = open("log\hid_log.csv","w") 

hid_util_fault = 0
print_every = 0

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

# Get Board Type command:
# 01h 00h 00h 01h
WRITE_DATA_CMD_GET_BOARD_TYPE = bytes.fromhex("3f040100000100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")
# WRITE_DATA_CMD_START = bytes.fromhex("3f048200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")
# WRITE_DATA_CMD_START = bytes.fromhex("3f048200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")

#.........................................................##........................................
WRITE_DATA_CMD_S = bytes.fromhex("3f3ebb00b127ff00ff00ff0053ff33ff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")
# 'A' - keep Alive + fast BLE update (every 20 msec)
WRITE_DATA_CMD_A = bytes.fromhex("3f3ebb00b127ff00ff00ff0041ff33ff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")
# moderate BLE update rate every 50 mSec by 'M' command
WRITE_DATA_CMD_M = bytes.fromhex("3f3ebb00b127ff00ff00ff004dff33ff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")
# set_BSL_mode
# WRITE_DATA_CMD_B = bytes.fromhex("3f3eaa00b127ff00ff00ff004dff33ff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")
#0xAA	Run BSL
WRITE_DATA_CMD_B = bytes.fromhex("3f04aa00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")


SLEEP_AMOUNT = 0.002 # Read from HID every 2 milliseconds
PRINT_TIME = 1.0 # Print every 1 second
# PRINT_TIME = 0.5 # Print every 0.5 second
#PRINT_TIME = 2 # Print every 2 second

START_INDEX = 2 + 4 # Ignore the first two bytes, then skip the version (4 bytes)
# ANALOG_INDEX_LIST = list(range(START_INDEX + 2, START_INDEX + 4 * 2 + 1, 2)) + [START_INDEX + 6 * 2,]
ANALOG_INDEX_LIST = list(range(START_INDEX + 2, START_INDEX + 8 * 2 + 1, 2)) 
print("ANALOG_INDEX_LIST=",ANALOG_INDEX_LIST)
# ANALOG_INDEX_LIST= [8, 10, 12, 14, 16, 18, 20, 22]
LAP_ANALOG_INDEX_LIST = list(range(2,8 * 2 + 1, 2)) 

COUNTER_INDEX = 2 + 22 + 18 # Ignore the first two bytes, then skip XData1 (22 bytes) and OverSample (==XDataSlave1; 18 bytes)
CMOS_INDEX = 2 + 2   # maybe + 4???
#                       0  1  2  3  4 5 6 7  8 9 1011
# Received data: b'3f26 00 00 00 00 0674fc41 3f4efc70 0033a4513c5a0101210001000000650000000000000000000000167f070dd7aee89baff63fedcfcccb763acf041b00000010'
#                                   TORQUE   INSERTION
INSERTION_INDEX = 2 + 8
TORQUE_INDEX = 2 + 4

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
fault_entry = list()
special_cmd = 0
ignore_red_handle_button = None
ignore_red_handle_checkbutton = None
ignore_red_handle_state = False

root = None

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
	
def gui_loop(device):
    do_print = True
    print_time = 0.0
    time = timer()
    handle_time = timer()
    write_time_capture = timer()
    skip_write = 0
    prev_counter = 0
    send_stream_request_command_once = 1
    # cnt = None
    # prev_cnt = None
    # value = None
    global special_cmd
    global WRITE_DATA
    # global print_flag
    
    while True:
        # Reset the counter
        if (do_print):
            print_time = timer()

        # Write to the device 
#        if send_stream_request_command_once == 1:
#            send_stream_request_command_once = 0
#            if PRODUCT_ID == PRODUCT_ID_LAP_NEW_CAMERA:
#                print("enforce streaming of data with command 0x82"
                # if device is attached enforce streaming of data.
                # device.write(WRITE_DATA_CMD_START)
        
        if special_cmd == 'I':
            if PRODUCT_ID == PRODUCT_ID_STATION:
                WRITE_DATA = WRITE_DATA_CMD_START_0x304
            else:
                WRITE_DATA = WRITE_DATA_CMD_START
            device.write(WRITE_DATA)
            print("special_cmd Start")
            special_cmd = 0
#        elif special_cmd == 'S':
#            WRITE_DATA = WRITE_DATA_CMD_GET_BOARD_TYPE
#            device.write(WRITE_DATA)
#            print("special_cmd CMD_GET_BOARD_TYPE")
#            # print_flag = 1
#            special_cmd = 0
#        elif special_cmd == 'A':
#            WRITE_DATA = WRITE_DATA_CMD_A
#            print("special_cmd A -> keep Alive + fast BLE update (every 20 msec)")
#            special_cmd = 0
#        elif special_cmd == 'M':
#            WRITE_DATA = WRITE_DATA_CMD_M
#            print("special_cmd M -> moderate BLE update rate every 50 mSec")
#            special_cmd = 0
        elif special_cmd == 'B':
           WRITE_DATA = WRITE_DATA_CMD_B
           device.write(WRITE_DATA)
           print("special_cmd B -> set_BSL_mode  --- this will stop HID communication with this GUI")
           special_cmd = 0
#        else:
#            WRITE_DATA = DEFAULT_WRITE_DATA
        
#        # device.write(WRITE_DATA)
        if WRITE_DATA == WRITE_DATA_CMD_B:
            break

        cycle_time = timer() - time
        # print("cycle timer: %.10f" % cycle_time)

        # If not enough time has passed, sleep for SLEEP_AMOUNT seconds
        sleep_time = SLEEP_AMOUNT - (cycle_time)

        # Measure the time
        time = timer()

        # Read the packet from the device
        value = device.read(READ_SIZE, timeout=READ_TIMEOUT)

        # Update the GUI
        if len(value) >= READ_SIZE:
            # save into file:
            analog = [(int(value[i + 1]) << 8) + int(value[i]) for i in LAP_ANALOG_INDEX_LIST]
            channel_0 = analog[0]
            channel_1 = analog[1]
            channel_2 = analog[2]
            channel_3 = analog[3]
            channel_4 = analog[4]
            counter = (int(value[COUNTER_INDEX + 1]) << 8) + int(value[COUNTER_INDEX])
            count_dif = counter - prev_counter 
            # global file1
            #if count_dif > 1 :
            #    L = [ str(counter),",   ", str(clicker_analog), ", " , str(count_dif), " <<<<<--- " ,"\n" ]  
            #else:
            #    L = [ str(counter),",   ", str(clicker_analog), ", " , str(count_dif), "\n" ]  
            L = [ str(channel_0),",   ", str(channel_1), ", " , str(channel_2),", " , str(channel_3),", " , str(channel_4), "\n" ]  
            # file1.writelines(L) 
            # handler(value, do_print=do_print)
            # print("Received data: %s" % hexlify(value))
            Handler_Called = (timer() - handle_time)
            
            if Handler_Called > 0.002 :
            # if Handler_Called > 0.02 :
                #print("handler called: %.6f" % Handler_Called)
                global print_every
                print_every = print_every + 1
                if print_every >= 500:
                    print_every = 0
                    print("time:", time, end="")
                    print("  Received data: %s" % hexlify(value))
            # print("time: %.6f" % time)
            handle_time = timer() 
            prev_counter = counter

        # Update the do_print flag
        do_print = (timer() - print_time) >= PRINT_TIME

def handler(value, do_print=False):
    if do_print:
        print("Received data: %s" % hexlify(value))
    return # do without gui

        

#   tool_size from CMOS: bytes 5..6
#   3f260000370b

    global hid_util_fault
    hid_util_fault = (int(value[START_INDEX+1]) & 0xF )
    digital = (int(value[START_INDEX + 1]) << 8) + int(value[START_INDEX + 0])
    analog = [(int(value[i + 1]) << 8) + int(value[i]) for i in ANALOG_INDEX_LIST]
    counter = (int(value[COUNTER_INDEX + 1]) << 8) + int(value[COUNTER_INDEX])
    tool_size = (int(value[CMOS_INDEX + 1]) << 8) + int(value[CMOS_INDEX])
# Received data: b'3f26 00 00 00 00 0674fc41 3f4efc70 0033a4513c5a0101210001000000650000000000000000000000167f070dd7aee89baff63fedcfcccb763acf041b00000010'
#                                   TORQUE   INSERTION
            # 0674 fc41
# -62847372 = FC41 0674
#   torque from Avago: bytes 6..9
    torque = (int(value[TORQUE_INDEX + 2]) << 24) + (int(value[TORQUE_INDEX+3]) <<16) + (int(value[TORQUE_INDEX]) <<8) + int(value[TORQUE_INDEX+1])  
    insertion = (int(value[INSERTION_INDEX + 2]) << 24) + (int(value[INSERTION_INDEX+3]) <<16) + (int(value[INSERTION_INDEX]) <<8) + int(value[INSERTION_INDEX+1])  
    if torque > 2**31:
        torque = torque - 2**32

    if do_print:
        print("Received data: %s" % hexlify(value))
        # print("tool_size    : %d" % tool_size)
        # print("insertion : %d" % insertion , end="")
        # print("   torque : %d" % torque)
    
    
    clicker_counter = (int(value[COUNTER_INDEX+2 + 1]) << 8) + int(value[COUNTER_INDEX+2])
    sleepTimer = (int(value[COUNTER_INDEX+4 + 1]) << 8) + int(value[COUNTER_INDEX+4])

    encoder1 = analog[3]
    encoder2 = analog[0]
    encoder3 = analog[1]
    encoder4 = analog[2]
    MotorCur = analog[4]
    clicker_analog = analog[5]
    # ClickerRec = analog[6]
    # batteryLevel = analog[6]
    
    # ClickerRec is actually connected to Pin of the VREF+ that is on that input P5.0
    batteryLevel = analog[7]
    
    # file1 = open("C:\Work\Python\HID_Util\src\log\log2.txt","w") 
    # global file1
    L = [ str(clicker_analog), "," ,"\n" ]  
    # file1.writelines(L) 




    bool_clicker = bool((digital >> 2) & 0x0001)
    bool_reset = bool((digital >> 4) & 0x0001)
    bool_red_handle = bool((digital >> 7) & 0x0001)
    bool_ignore_red_handle = ignore_red_handle_state
    if PRODUCT_ID != PRODUCT_ID_STATION:
        int_hid_stream_channel1 = analog[1]
        int_inner_handle_channel1 = analog[0]
    else:
        int_hid_stream_channel1 = insertion
        int_inner_handle_channel1 = torque
    int_hid_stream_channel2 = tool_size
    int_inner_handle_channel2 = analog[3]
    int_clicker = clicker_analog
    int_sleepTimer = sleepTimer
    int_batteryLevel = batteryLevel
    int_MotorCur = MotorCur
    int_counter = counter
    int_hid_util_fault = hid_util_fault
    int_clicker_counter = clicker_counter
    int_hid_stream_insertion = insertion
    if PRODUCT_ID != PRODUCT_ID_STATION:
        precentage_hid_stream_channel1 = int((int_hid_stream_channel1 / 4096) * 100)
        precentage_inner_handle_channel1 = int((int_inner_handle_channel1 / 4096) * 100)
    else:
        precentage_hid_stream_channel1 = abs(int((int_hid_stream_channel1 / 1000) * 100))
        precentage_inner_handle_channel1 = abs(int((int_inner_handle_channel1 / 1000) * 100))
    precentage_hid_stream_channel2 = int((int_hid_stream_channel2 / 4096) * 100)
    precentage_inner_handle_channel2 = int((int_inner_handle_channel2 / 4096) * 100)
    precentage_clicker = int((int_clicker / 4096) * 100)
    # precentage_sleepTimer = int((int_sleepTimer / 600) * 100)
    precentage_sleepTimer = int(int_sleepTimer )
    precentage_batteryLevel = int((int_batteryLevel / 4096) * 100)
    precentage_MotorCur = int((int_MotorCur / 4096) * 100)
    progressbar_style_hid_stream_channel1 = progressbar_styles[0]
    progressbar_style_hid_stream_channel2 = progressbar_styles[1]
    progressbar_style_inner_handle_channel1 = progressbar_styles[2]
    progressbar_style_inner_handle_channel2 = progressbar_styles[3]
    progressbar_style_clicker = progressbar_styles[4]
    progressbar_style_sleepTimer = progressbar_styles[5]
    progressbar_style_batteryLevel = progressbar_styles[6]
    progressbar_style_MotorCur = progressbar_styles[7]
    progressbar_hid_stream_channel1 = progressbars[0]
    progressbar_hid_insertion = progressbars[0] #can I duplicate it?
    progressbar_hid_stream_channel2 = progressbars[1]
    progressbar_inner_handle_channel1 = progressbars[2]
    progressbar_inner_handle_channel2 = progressbars[3]
    progressbar_clicker = progressbars[4]
    progressbar_sleepTimer = progressbars[5]
    progressbar_batteryLevel = progressbars[6]
    progressbar_MotorCur = progressbars[7]
    checkbox_inner_clicker = inner_clicker
    checkbox_red_handle = red_handle
    checkbox_reset_check = reset_check
    checkbox_ignore_red_handle = ignore_red_handle_checkbutton
    entry_counter = counter_entry
    entry_clicker_counter = clicker_counter_entry
    entry_fault = fault_entry
    
    progressbar_style_hid_stream_channel1.configure(
        HID_STREAM_CHANNEL1_STYLE,
        text=("%d" % int_hid_stream_channel1)
    )
    progressbar_style_hid_stream_channel2.configure(
        HID_STREAM_CHANNEL2_STYLE,
        text=("%d" % int_hid_stream_channel2)
    )
    progressbar_style_inner_handle_channel1.configure(
        INNER_HANDLE_CHANNEL1_STYLE,
        text=("%d" % int_inner_handle_channel1)
    )
    progressbar_style_inner_handle_channel2.configure(
        INNER_HANDLE_CHANNEL2_STYLE,
        text=("%d" % int_inner_handle_channel2)
    )
    progressbar_style_clicker.configure(
        CLICKER_STYLE,
        text=("%d" % int_clicker)
    )
    progressbar_style_sleepTimer.configure(
        SLEEPTIMER_STYLE,
        text=("%d" % sleepTimer)
    )
    progressbar_style_batteryLevel.configure(
        BATTERY_LEVEL_STYLE,
        text=("%d" % batteryLevel)
    )
    progressbar_style_MotorCur.configure(
        MOTOR_CURRENT_STYLE,
        text=("%d" % MotorCur)
    )
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
    progressbar_sleepTimer["maximum"] = 600
    progressbar_batteryLevel["value"] = precentage_batteryLevel
    progressbar_MotorCur["value"] = precentage_MotorCur

    update_checkbox(checkbox_inner_clicker, bool_clicker)
    update_checkbox(checkbox_red_handle, bool_red_handle)
    update_checkbox(checkbox_reset_check, bool_reset)
    update_checkbox(checkbox_ignore_red_handle, bool_ignore_red_handle)

    entry_counter.delete(0, tk.END)
    entry_counter.insert(tk.END, "%d" % int_counter)

    entry_clicker_counter.delete(0, tk.END)
    entry_clicker_counter.insert(tk.END, "%d" % int_clicker_counter)

    entry_fault.delete(0, tk.END)
    entry_fault.insert(tk.END, "%d" % int_hid_util_fault)

    root.update()

PROGRESS_BAR_LEN = 300
LONG_PROGRESS_BAR_LEN = 590

def my_channel_row(frame, row, label, style):
    ttk.Label(frame,text=label).grid(row=row,sticky=tk.W)

    row += 1

    if PRODUCT_ID != PRODUCT_ID_STATION:
        # Inner Handle
        ttk.Label(frame,text="Channel 1").grid(row=row,column=0)
        ttk.Label(frame,text="Channel 2").grid(row=row,column=1)
    else:
        ttk.Label(frame,text="Torque").grid(row=row,column=0)
        ttk.Label(frame,text="Channel 2").grid(row=row,column=1)

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
        columnspan=3,
        sticky=(tk.W + tk.E)
    )
    return row + 1

def my_widgets(frame):
    # Add style for labeled progress bar
    for name in style_names:
        style = ttk.Style(
            frame
        )
        progressbar_styles.append(style)
        style.layout(
            name,
            [
                (
                    "%s.trough" % name,
                    {
                        "children":
                        [
                            (
                                "%s.pbar" % name,
                                {"side": "left", "sticky": "ns"}
                            ),
                            (
                                "%s.label" % name,
                                {"sticky": ""}
                            )
                        ],
                        "sticky": "nswe"
                    }
                )
            ]
        )
        if name == SLEEPTIMER_STYLE:
            # style.configure(name, foreground="white", background="blue")
            style.configure(name, foreground="white", background="#d9d9d9")
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

    row += 1

    text_name = "Channel 1"
    if PRODUCT_ID == PRODUCT_ID_STATION:
        text_name = "Insertion"
    ttk.Label(frame,text=text_name).grid(row=row,column=0)
    
    row += 1
    w = ttk.Progressbar(frame,orient=tk.HORIZONTAL,length=PROGRESS_BAR_LEN,style=("HIDStreamChannel1"))
    progressbars.append(w)
    w.grid(row=row,column=0)

    row -= 1    # go line back for text header

    text_name = "Channel 2"
    if PRODUCT_ID == PRODUCT_ID_STATION:
        text_name = "Tool Size"
    ttk.Label(frame,text=text_name).grid(row=row,column=1)

    row += 1

    w = ttk.Progressbar(frame,orient=tk.HORIZONTAL,length=PROGRESS_BAR_LEN,style=("HIDStreamChannel2"))
    progressbars.append(w)
    w.grid(row=row,column=1)

    row += 1

    # Seperator
    row = my_seperator(frame, row)

    if PRODUCT_ID != PRODUCT_ID_STATION:
        # Inner Handle
        row = my_channel_row(frame=frame,row=row,label="InnerHandle",style="InnerHandle")
    else:
        row = my_channel_row(frame=frame,row=row,label="PRODUCT_ID_STATION",style="InnerHandle")
        

    # Seperator
    row = my_seperator(frame, row)

    # Clicker labels
    ttk.Label(frame,text="InnerClicker").grid(row=row,column=0,sticky=tk.W)
    ttk.Label(frame,text="Clicker").grid(row=row,column=1)
    ttk.Label(frame,text="ClickerCounter").grid(row=row,column=2)

    row += 1

    # Clicker data
    w = tk.Checkbutton(frame,state=tk.DISABLED)
    global inner_clicker
    inner_clicker = w
    w.grid(row=row,column=0)
    w = ttk.Progressbar(frame,orient=tk.HORIZONTAL,length=PROGRESS_BAR_LEN,style="Clicker")
    progressbars.append(w)
    w.grid(row=row,column=1)
    # yg: adding clicker counter display
    w = ttk.Entry(frame,width=20,)
    global clicker_counter_entry
    clicker_counter_entry = w
    w.grid(
        #padx=10,#pady=5,
        row=row,
        column=2,#sticky=tk.W,
        )

    row += 1

    # Seperator
    row = my_seperator(frame, row)

    # Red handle and reset button labels
    ttk.Label(frame,text="RedHandle").grid(row=row,column=0,sticky=tk.W)
    ttk.Label(frame,text="ResetButton").grid(row=row,column=1)

    ttk.Label(frame,text="IgnoreRedHandlefault").grid(row=row,column=2)

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

    red_handle_ignore = tk.Button(frame,text ="Start streaming",command = streaming_button_CallBack)
    red_handle_ignore.grid(row=row,column=3)
    
    # checkbox for the ignore red handle 
    w = tk.Checkbutton(frame,state=tk.DISABLED)
    # global ignore_red
    # ignore_red = w
    global ignore_red_handle_checkbutton
    ignore_red_handle_checkbutton = w
    w.grid(row=row,column=2)

    row += 1

    # Seperator
    row = my_seperator(frame, row)

    # Counter
    ttk.Label(frame,text="PacketsCounter:").grid(row=row,column=0,sticky=tk.E,)
    w = ttk.Entry(frame,width=20,
        # """state=tk.DISABLED"""
        )
    global counter_entry
    counter_entry = w
    w.grid(padx=10,pady=5,row=row,column=1,columnspan=2,sticky=tk.W,)
    # HID_Util Fault indication
    ttk.Label(frame,text="Faultindication:").grid(row=row,column=1,sticky=tk.E,)
    w = ttk.Entry(
        frame,
        width=20,
    )
    global fault_entry
    fault_entry = w
    w.grid(
        padx=10,
        pady=5,
        row=row,
        column=2,
        columnspan=2,
        sticky=tk.W,
    )

    row += 1

    # Seperator
    row = my_seperator(frame, row)

    # sleepTimer
    ttk.Label(
        frame,
        text="Sleep Timer"
    ).grid(
        row=row,
        column=0,
        sticky=tk.E,
    )

    w = ttk.Progressbar(
        frame,
        orient=tk.HORIZONTAL,
        length=LONG_PROGRESS_BAR_LEN,
        style="sleepTimer"
    )
    progressbars.append(w)
    w.grid(
        row=row,
        column=1,
        columnspan=3
    )

    row += 1

    # Seperator
    row = my_seperator(frame, row)

    # battery level
    ttk.Label(
        frame,
        text="battery level"
    ).grid(
        row=row,
        column=0,
        sticky=tk.E,
    )

    w = ttk.Progressbar(
        frame,
        orient=tk.HORIZONTAL,
        length=LONG_PROGRESS_BAR_LEN,
        style="batteryLevel"
    )
    progressbars.append(w)
    w.grid(
        row=row,
        column=1,
        columnspan=3
    )

    row += 1

    # Seperator
    row = my_seperator(frame, row)

    # Motor Cur
    ttk.Label(
        frame,
        text="Motor Current"
    ).grid(
        row=row,
        column=0,
        sticky=tk.E,
    )

    w = ttk.Progressbar(
        frame,
        orient=tk.HORIZONTAL,
        length=LONG_PROGRESS_BAR_LEN,
        style="motorCurrent"
    )
    progressbars.append(w)
    w.grid(
        row=row,
        column=1,
        columnspan=3
    )

    row += 1

    # Seperator
    row = my_seperator(frame, row)

    red_handle_ignore = tk.Button(frame,text ="Get Board Type",command = board_type_button_callback)
    red_handle_ignore.grid(row=row,column=0)

    red_handle_ignore = tk.Button(frame,text ="Keep alive (fast BLE)",command = alive_button_CallBack)
    red_handle_ignore.grid(row=row,column=1)

    red_handle_ignore = tk.Button(frame,text ="Moderate BLE",command = moderate_button_CallBack)
    red_handle_ignore.grid(row=row,column=2)

    row += 1

    row = my_seperator(frame, row)
    red_handle_ignore = tk.Button(frame,text ="BSL !!!(DONT PRESS)",command = BSL_mode_button_CallBack)
    red_handle_ignore.grid(row=row,column=2)
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
    return parser

def main():
    global VENDOR_ID
    global PRODUCT_ID
    PATH = None
    
    # Parse the command line arguments
    parser = init_parser()
    args = parser.parse_args(sys.argv[1:])

    # Initialize the flags according from the command line arguments
    avail_vid = args.vendor_id != None
    avail_pid = args.product_id != None
    avail_path = args.path != None
    id_mode = avail_pid and avail_vid
    path_mode = avail_path
    default_mode = (not avail_vid) and (not avail_pid) and (not avail_path)
    if (path_mode and (avail_pid or avail_vid)):
        print("The path argument can't be mixed with the ID arguments")
        return
    if ((not avail_path) and ((avail_pid and (not avail_vid)) or ((not avail_pid) and avail_vid))):
        print("Both the product ID and the vendor ID must be given as arguments")
        return

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
                        # print("VID = %X PID = %X " % VENDOR_ID, PRODUCT_ID)
                        print("try with PID = %X " % PRODUCT_ID)
                        # print("PRODUCT_ID = %X" % PRODUCT_ID)
                        device = hid.Device(vid=VENDOR_ID, pid=PRODUCT_ID)
                        # device = hid.Device(vid=0x24B3, pid=0x2005)
                        # print("success vid=0x24B3, pid=0x2005 !!")
                    except:
                        print("wrong ID2")

            # new device based on old camera, added at: 2022_12_22
            if device is None:
                try:
                    # print("try with other device")
                    VENDOR_ID = 0x24b3 # Simb
                    PRODUCT_ID = PRODUCT_ID_LAP_OLD_CAMERA # LAP_OLD_CAMERA. is 0x3005
                    # print("VID = %X PID = %X " % VENDOR_ID, PRODUCT_ID)
                    print("try with PID = %X " % PRODUCT_ID)
                    # print("PRODUCT_ID = %X" % PRODUCT_ID)
                    device = hid.Device(vid=VENDOR_ID, pid=PRODUCT_ID)
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
                    if device is not None:
                        device.write(DEFAULT_WRITE_DATA)
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
                        print("try with PID = %X " % PRODUCT_ID)
                        device = hid.Device(vid=VENDOR_ID, pid=PRODUCT_ID)
                    except:
                        print("wrong ID4")
                    
            if device is None:
                print("no device attached")
            else:
                print("VENDOR_ID = %X" % VENDOR_ID)
                print("PRODUCT_ID = %X" % PRODUCT_ID)
                global special_cmd
                if PRODUCT_ID in PRODUCT_ID_types:
                    print(PRODUCT_ID_types[PRODUCT_ID])
                    # if PRODUCT_ID == PRODUCT_ID_LAP_NEW_CAMERA:
                    if PRODUCT_ID in PRODUCT_ID_types:
                        special_cmd = 'B'
                        # root. destroy() 
                elif PRODUCT_ID == PRODUCT_ID_CTAG:
                    print("BOARD_TYPE: CTAG  --- new in bsl.exe")
                    # if PRODUCT_ID == PRODUCT_ID_LAP_NEW_CAMERA:
                    if PRODUCT_ID in PRODUCT_ID_types:
                        special_cmd = 'B'

                    

            

        elif (path_mode):
            device = hid.Device(path=PATH)
        else:
            raise NotImplementedError

#        # Initialize the main window
#        global root
#        root = tk.Tk()
#        root.title("HID_Util")
#
#        # Initialize the GUI widgets
#        my_widgets(root)

        # Create thread that calls
        threading.Thread(target=gui_loop, args=(device,), daemon=True).start()
        global WRITE_DATA
        if WRITE_DATA == WRITE_DATA_CMD_B:
            print("WRITE_DATA == WRITE_DATA_CMD_B")
            # threading.Thread(target=gui_loop, args=(device,), daemon=True).stop()
        print(" Recording Ended !!!")
        print(" ")
        print(" Please press <Enter> to Exit")
        input()

        # Run the GUI main loop
#        root.mainloop()
    finally:
        # global file1
        # file1.close() #to change file access modes 
        if device != None:
            device.close()

if __name__ == "__main__":
    main()