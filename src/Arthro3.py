#!/usr/bin/python3
# C:\Work\Python\HID_Util\src\Arthro.py

from binascii import hexlify
import sys
import argparse
import threading
from time import sleep
from time import process_time as timer

import tkinter as tk
from tkinter import ttk
import tkinter.messagebox

import include_dll_path
import hid


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
PRODUCT_ID_ARTHRO = 0x1007
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
  0x1007: "BOARD_TYPE: Arthro Master",
  0x1965: "yosi"
}


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
WRITE_DATA_CMD_START_0x304  = bytes.fromhex("3f048d00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")
WRITE_DATA_CMD_START_0x303  = bytes.fromhex("3f048300000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")
WRITE_DATA_CMD_START_0x1007 = bytes.fromhex("3f3ebb00b12700000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")
WRITE_DATA_CMD_STOP_STREAM  = bytes.fromhex("3f3ebb00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")

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
# IMAGE_QUALITY_INDEX = INSERTION_INDEX + 4
IMAGE_QUALITY_INDEX = TORQUE_INDEX + 4

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
Port_8_pin_2 = list()
reset_check = list()
counter_entry = list()
clicker_counter_entry = list()
fault_entry = list()
special_cmd = 0
ignore_red_handle_button = None
ignore_red_handle_checkbutton = None
ignore_red_handle_state = False
handler_counter = 0
g_prints_counter = 0
g_handler_counter = 0
handler_called_counter = 0
debug_pwm_print = True
cb = None
root = None
Fw_Version = "NA"
Fw_Date = "NA"
popup_message = 0

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
    pwm_percent = pwm_16/(2**16-1)*100
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
        # if (do_print):
            # print_time = timer()

        # Write to the device (request data; keep alive)
        if special_cmd == 'I':
            if PRODUCT_ID == PRODUCT_ID_STATION:
                WRITE_DATA = WRITE_DATA_CMD_START_0x304
            elif PRODUCT_ID == PRODUCT_ID_ARTHRO:
                WRITE_DATA = WRITE_DATA_CMD_START_0x1007
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
            elif PRODUCT_ID == PRODUCT_ID_ARTHRO:
                print("special_cmd M -> stop streaming by KeepAliveTimer = 0")
                WRITE_DATA = WRITE_DATA_CMD_STOP_STREAM
                device.write(WRITE_DATA)
                device.write(WRITE_DATA)
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

        # if (do_print):
            # print_time = timer()

        # Measure the time
        time = timer()

        # Read the packet from the device
        value = device.read(READ_SIZE, timeout=READ_TIMEOUT)

        # Update the GUI
        if len(value) >= READ_SIZE:
            # call the handler only once every 20 cycles
            global g_handler_counter
            g_handler_counter += 1
            if g_handler_counter == 1:
                if (do_print):
                    print_time = timer()
                #############     calling to the handler     #############
                handler(value, do_print=do_print)                        #
                # handler(value, do_print=1)                             #
                g_handler_counter = 0                                    #
                global handler_called_counter                            #
                handler_called_counter += 1                              #
                ##########################################################
                # print("handler called: %d" % handler_called_counter)

        # Update the do_print flag
        do_print = (timer() - print_time) >= PRINT_TIME
def long_unsigned_to_long_signed( x ):
    if x > MAX_LONG_POSITIVE:
        x = x - MAX_UNSIGNED_LONG
    return x

def date2dec(x):
    s = "%02x" % x
    return s


def handler(value, do_print=False):
    # global print_flag

        
    # if print_flag:
        # print("command response: %s" % hexlify(value))
        # print_flag = 0

#   tool_size from CMOS: bytes 5..6
#   3f260000370b
    global handler_counter
    global PRODUCT_ID

    handler_counter = handler_counter + 1
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
    insertion = (int(value[INSERTION_INDEX + 2]) << 24) + (int(value[INSERTION_INDEX+3]) <<16) + (int(value[INSERTION_INDEX]) <<8) + int(value[INSERTION_INDEX+1])  
    image_quality = (int(value[IMAGE_QUALITY_INDEX]) )
    station_current = (int(value[STATION_CURRENT_INDEX + 1]) << 8) + int(value[STATION_CURRENT_INDEX]) #station Report.current
    #global MAX_LONG_POSITIVE
    torque = long_unsigned_to_long_signed(torque)
    insertion = long_unsigned_to_long_signed(insertion)

    if do_print:
        print("Received data: %s" % hexlify(value))
        global g_prints_counter
        g_prints_counter += 1
        if( g_prints_counter == 10 ):
            g_prints_counter = 0
            # print(" ------------------- ")
            global special_cmd
            special_cmd = 'I'

        if PRODUCT_ID == PRODUCT_ID_STATION:
            print("insertion[last byte]: %02x  || image_quality: %02x  %d" % (int(value[INSERTION_INDEX+3]),image_quality, image_quality))
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
    sleepTimer = (int(value[COUNTER_INDEX+4 + 1]) << 8) + int(value[COUNTER_INDEX+4])

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
    L = [ str(clicker_analog), "," ,"\n" ]  
    # file1.writelines(L) 


    # Received data: b'3f3d04015200ffff2c042e0856044e048105c8038a02380300000000000000000000000000000000000007323032325f31315f31375f5f31365f333600000010'
    #  00010203040506070809101112131415161718192021222324252627282930313233343536373839404142434445464748495051525354555657585960616263
    # '3f3d04015200ffff2c042e0856044e048105c8038a02380300000000000000000000000000000000000007323032325f31315f31375f5f31365f333600000010'
    #                                                                                     |42| <<<----- byte 42 for Data.DigitalIO3
    
    DigitalIO_3 = (int(value[42]))
    bool_clicker = bool((digital >> 2) & 0x0001)
    bool_reset = bool((digital >> 4) & 0x0001)
    bool_red_handle = bool((digital >> 7) & 0x0001)
    
    bool_Port_8_pin_2 = bool((DigitalIO_3 >> 2) & 0x0001)
    bool_Port_8_pin_1 = bool((DigitalIO_3 >> 1) & 0x0001)
    bool_Port_8_pin_0 = bool((DigitalIO_3 >> 0) & 0x0001)

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
        counter = handler_counter
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
    precentage_sleepTimer = int(int_sleepTimer )
    precentage_batteryLevel = int((int_batteryLevel / 4096) * 100)
    if PRODUCT_ID != PRODUCT_ID_STATION:
        precentage_MotorCur = int((int_MotorCur / 4096) * 100)
    else:
        precentage_MotorCur = int((station_current / 4096) * 100)
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
#    checkbox_inner_clicker = inner_clicker
    # checkbox_red_handle = red_handle
    checkbox_reset_check = reset_check
    checkbox_ignore_red_handle = ignore_red_handle_checkbutton
    entry_counter = counter_entry
    entry_clicker_counter = clicker_counter_entry
    entry_fault = fault_entry
    
    progressbar_style_hid_stream_channel1.configure(HID_STREAM_CHANNEL1_STYLE,text=("%d"%int_hid_stream_channel1))
    progressbar_style_hid_stream_channel2.configure(HID_STREAM_CHANNEL2_STYLE,text=("%d"%int_hid_stream_channel2))
    progressbar_style_inner_handle_channel1.configure(INNER_HANDLE_CHANNEL1_STYLE,text=("%d"%int_inner_handle_channel1))
    progressbar_style_inner_handle_channel2.configure(INNER_HANDLE_CHANNEL2_STYLE,text=("%d"%int_inner_handle_channel2))
    progressbar_style_clicker.configure(CLICKER_STYLE,text=("%d"%int_clicker))
    progressbar_style_sleepTimer.configure(SLEEPTIMER_STYLE,text=("%d"%sleepTimer))
    progressbar_style_batteryLevel.configure(BATTERY_LEVEL_STYLE,text=("%d"%batteryLevel))
    if PRODUCT_ID != PRODUCT_ID_STATION:
        progressbar_style_MotorCur.configure(MOTOR_CURRENT_STYLE,text=("%d"%MotorCur))
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
    progressbar_sleepTimer["maximum"] = 600
    progressbar_batteryLevel["value"] = precentage_batteryLevel
    progressbar_MotorCur["value"] = precentage_MotorCur

#    update_checkbox(checkbox_inner_clicker, bool_clicker)
    update_checkbox(Port_8_pin_2, bool_Port_8_pin_2)
    update_checkbox(checkbox_reset_check, bool_Port_8_pin_1)
    update_checkbox(checkbox_ignore_red_handle, bool_Port_8_pin_0)

    entry_counter.delete(0, tk.END)
    entry_counter.insert(tk.END, "%d" % int_counter)

    entry_clicker_counter.delete(0, tk.END)
    entry_clicker_counter.insert(tk.END, "%d" % int_clicker_counter)

    entry_fault.delete(0, tk.END)
    entry_fault.insert(tk.END, "%d" % int_hid_util_fault)

    root.update()

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

    widget = ttk.Progressbar(frame,orient=tk.HORIZONTAL,length=PROGRESS_BAR_LEN,style=("%sChannel1"%style))
    progressbars.append(widget)
    widget.grid(row=row,column=0)
    widget = ttk.Progressbar(frame,orient=tk.HORIZONTAL,length=PROGRESS_BAR_LEN,style=("%sChannel2"%style))
    progressbars.append(widget)
    widget.grid(row=row,column=1)

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
    ttk.Label(frame,text="----------------------").grid(row=row,sticky=tk.NW)
    row += 1
    if PRODUCT_ID == PRODUCT_ID_STATION:
        text_name =\
"ADCs...  \t\t\t\t\t\
NOTE: Zero value in Tool_size reset the Insertion value"
        ttk.Label(frame,text=text_name).grid(row=row,sticky=tk.NW)
    else:
        ttk.Label(frame,text="ADCs...").grid(row=row,sticky=tk.NW)
    row += 1

    #
    # 0,1 (packet length,data length); 2,3 (Chanel 1); 4,5 (Chanel 2); 6,7 (Chanel 3); 8,9 (Chanel 4); 10,11 (Chanel 5); 
    # 12,13 (Chanel 6); 14,15 (Chanel 7);
    text_name = "Channel 5 (analog[1] = bytes 10,11)"
    if PRODUCT_ID == PRODUCT_ID_STATION:
        text_name = "Insertion"
    ttk.Label(frame,text=text_name).grid(row=row,column=0)
    
    row += 1
    widget = ttk.Progressbar(frame,orient=tk.HORIZONTAL,length=PROGRESS_BAR_LEN,style=("HIDStreamChannel1"))
    progressbars.append(widget)
    widget.grid(row=row,column=0)

    row -= 1    # go line back for text header

    text_name = "Channel 2 (analog[?] = bytes 4,5)"
    if PRODUCT_ID == PRODUCT_ID_STATION:
        text_name = "Tool Size"
    ttk.Label(frame,text=text_name).grid(row=row,column=1)

    row += 1

    widget = ttk.Progressbar(frame,orient=tk.HORIZONTAL,length=PROGRESS_BAR_LEN,style=("HIDStreamChannel2"))
    progressbars.append(widget)
    widget.grid(row=row,column=1)

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
#    widget = tk.Checkbutton(frame,state=tk.DISABLED)
#    global inner_clicker
#    inner_clicker = widget
#    widget.grid(row=row,column=0)
    widget = ttk.Progressbar(frame,orient=tk.HORIZONTAL,length=PROGRESS_BAR_LEN,style="Clicker")
    progressbars.append(widget)
    widget.grid(row=row,column=0)
    # yg: adding clicker counter display
    widget = ttk.Entry(frame,width=20,)
    global clicker_counter_entry
    clicker_counter_entry = widget
    widget.grid(
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
    widget = tk.Checkbutton(frame,state=tk.DISABLED)
    global Port_8_pin_2
    Port_8_pin_2 = widget
    widget.grid(row=row,column=0)
    
    widget = tk.Checkbutton(frame,state=tk.DISABLED)
    global reset_check
    reset_check = widget
    widget.grid(row=row,column=1)

    # checkbox for the ignore red handle 
    widget = tk.Checkbutton(frame,state=tk.DISABLED)
    global ignore_red_handle_checkbutton
    ignore_red_handle_checkbutton = widget
    widget.grid(row=row,column=2)

    temp_widget = tk.Button(frame,text ="Start streaming",command = streaming_button_CallBack)
    temp_widget.grid(row=row,column=3)

    row += 1

    # Seperator
    row = my_seperator(frame, row)
    # ------------------------------------------------------

    # Counter
    # ttk.Label(frame,text="PacketsCounter:").grid(row=row,column=0,sticky=tk.E,)
    widget = ttk.Label(frame,text="PacketsCounter:")
    widget.grid(row=row,column=0,sticky=tk.W,)
    
    widget = ttk.Entry(frame,width=25)
    #widget.grid(row=row,column=0,sticky=tk.W,)
# width=20 make the Entry window for 20 chars long.    
# adding the state=tk.DISABLED  to widget : makes it gray        
    global counter_entry
    counter_entry = widget
    # widget.grid(padx=10,pady=5,row=row,column=1,columnspan=2,sticky=tk.W,)
    next_row = row+1
    # widget.grid(padx=10,pady=5,row=row,column=0,columnspan=1,sticky=tk.E,)
    widget.grid(padx=10,pady=5,row=row,column=0,columnspan=1)
    # columnspan − How many columns widget occupies; default 1

    #                       |||||                       #
    # HID_Util Fault indication
    ttk.Label(frame,text="Faultindication:").grid(row=row,column=1,sticky=tk.W,)
    widget = ttk.Entry(frame,width=20,)
    global fault_entry
    fault_entry = widget
    widget.grid(padx=10,pady=5,row=row,column=1,columnspan=1)#,sticky=tk.E,)

    row += 1
    row += 1

    # Seperator
    row = my_seperator(frame, row)
    # ------------------------------------------------------

    # sleepTimer
    ttk.Label(frame,text="SleepTimer").grid(row=row,column=0,sticky=tk.E,)

    widget = ttk.Progressbar(frame,orient=tk.HORIZONTAL,length=LONG_PROGRESS_BAR_LEN,style="sleepTimer")
    progressbars.append(widget)
    widget.grid(row=row,column=1,columnspan=2)
    row += 1

    # Seperator
    row = my_seperator(frame, row)
    # ------------------------------------------------------

    # battery level
    text_name = "batterylevel"
    if PRODUCT_ID == PRODUCT_ID_STATION:
        text_name = "Pressure   (bytes 22,23)"
    if PRODUCT_ID == PRODUCT_ID_TOOLS:
        text_name = "injector_Sig1   (bytes 32,33)"
    ttk.Label(frame,text=text_name).grid(row=row,column=0,sticky=tk.E,) #bytes 22,23 

    widget = ttk.Progressbar(
        frame,
        orient=tk.HORIZONTAL,
        length=LONG_PROGRESS_BAR_LEN,
        style="batteryLevel"
    )
    progressbars.append(widget)
    widget.grid(
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
        ttk.Label(frame,text="Station MotorCurrent (bytes 25,26)").grid(row=row,column=0,sticky=tk.E,)

    widget = ttk.Progressbar(
        frame,
        orient=tk.HORIZONTAL,
        length=LONG_PROGRESS_BAR_LEN,
        style="motorCurrent"
    )
    progressbars.append(widget)
    widget.grid(
        row=row,
        column=1,
        # columnspan=3
        columnspan=2
    )

    row += 1

    # Seperator
    row = my_seperator(frame, row)
    # ------------------------------------------------------

    pwm_widget = tk.Scale(frame, from_=0, to=99, orient='horizontal',length=200)#, orient=HORIZONTAL)
    # tk.Button(frame,text ="Get Board Type",command = board_type_button_callback)
    pwm_widget.grid(row=row,column=0)

    # widget = ttk.Label(frame,text="PWM debug print:").grid(row=row,column=1,sticky='W')
    
    global cb
    cb = tk.IntVar()
    # cb.grid(row=row,column=1)#,tk.sticky='E')
    widget = tk.Checkbutton(frame,text="PWM debug print:",variable=cb,onvalue=1,offvalue=0,command=isChecked)
    widget.grid(row=row,column=1,sticky='W')
    
   
    # temp_widget = tk.Button(frame, text='Print PWM', command=show_pwm_values).grid(row=row,column=1)
    pwm_16_widget = tk.Scale(frame, from_=0, to=2**16-1, orient='horizontal',length=400)#, orient=HORIZONTAL)
    # tk.Button(frame,text ="Get Board Type",command = board_type_button_callback)
    pwm_16_widget.grid(row=row,column=2,sticky='W')

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
    if PRODUCT_ID == PRODUCT_ID_STATION:
        temp_widget = tk.Button(frame,text ="Reset Ins & Torque",command = moderate_button_CallBack)
    elif PRODUCT_ID == PRODUCT_ID_ARTHRO:
        temp_widget = tk.Button(frame,text ="Stop Streaming",command = moderate_button_CallBack)
    else:
        temp_widget = tk.Button(frame,text ="Moderate BLE",command = moderate_button_CallBack)
    temp_widget.grid(row=row,column=2)

    row += 1

    row = my_seperator(frame, row)
    # ------------------------------------------------------
    temp_widget = tk.Button(frame,text ="BSL !!!(DONT PRESS)",command = BSL_mode_button_CallBack)
    temp_widget.grid(row=row,column=2)
    
def isChecked():
    global debug_pwm_print
    global cb
    if cb.get() == 1:
        debug_pwm_print = 1
        print("debug_pwm_print = 1")
        # btn['state'] = NORMAL
        # btn.configure(text='Awake!')
    elif cb.get() == 0:
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
    return parser

def main():
    global VENDOR_ID
    global PRODUCT_ID
    PATH = None
    
    # open recording log file:
    # file1 = open("C:\Work\Python\HID_Util\src\log\log2.txt","w") 

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
            # idVendor:                        0x24B3 = Simbionix Ltd.
            # idProduct:                       0x1007
            if device is None:
                try:
                    # print("try with other device")
                    VENDOR_ID = 0x24b3 # Simbionix
                    PRODUCT_ID = 0x1007 # Arthro Master. is 0x1007
                    # print("VID = %X PID = %X " % VENDOR_ID, PRODUCT_ID)
                    print("try with PID = %X " % PRODUCT_ID)
                    # print("PRODUCT_ID = %X" % PRODUCT_ID)
                    device = hid.Device(vid=VENDOR_ID, pid=PRODUCT_ID)
                    # device = hid.Device(vid=0x24B3, pid=0x2005)
                    # print("success vid=0x24B3, pid=0x2005 !!")
                except:
                    print("wrong 0x1007")
            ###############    on the end of tries #######################
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
        root = tk.Tk()
        root.title("Arthro HID_Util")

        # Initialize the GUI widgets
        my_widgets(root)

        # Create thread that calls
        threading.Thread(target=gui_loop, args=(device,), daemon=True).start()

        # Run the GUI main loop
        root.mainloop()
    finally:
        # global file1
        # file1.close() #to change file access modes 
        if device != None:
            device.close()

if __name__ == "__main__":
    main()

'''
history changes
2022_11_18
- replace variables:
    red_handle reset_check ignore_red_handle_checkbutton
  with:
  Port_8_pin_2, Port_8_pin_1 and Port_8_pin_0

'''    