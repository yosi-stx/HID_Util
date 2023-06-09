#!/usr/bin/python3
# C:\Work\Python\HID_Util\src\CAN_UTILL.py 
util_verstion = "2023_06_09.a"

from binascii import hexlify
import sys
import argparse
import threading
from time import sleep
from time import process_time as timer
import time
import can

import tkinter as tk
from tkinter import ttk
import tkinter.messagebox
import pickle
import os
from colorama import Fore, Style


# create a global empty list for progressbars that will be added later in: my_widgets()
progressbars = list()
# create a global empty variable root to hold the class that represents the main window or the root 
#  window of your application.
root = None 
special_cmd = None

# defines from C FW project
    #define MAX_SLOT_NUMBER 7
    #define SLOT_NUMBER     4    
    #define MY_RX_ID        SLOT_NUMBER
    #define ID_MASK         0x00F
    #define DIR_MASK        0x400
    #define BROADCAST_ID        0
    #define STREAMING_DATA_TYPE_1 0x080
MAX_SLOT_NUMBER        = 7
SLOT_NUMBER            = 4    
MY_RX_ID               = SLOT_NUMBER
ID_MASK                = 0x00F
DIR_MASK               = 0x400
BROADCAST_ID           = 0
STREAMING_DATA_TYPE_1  = 0x080
STREAMING_DATA_TYPE_2  = 0x090
MAX_EXPERT_LINES       = 15

OPCODE_GENERAL_PURPOSE              =  0x00
OPCODE_GET_BOARD_TYPE               =  0x01
OPCODE_GET_GPIO                     =  0x02
OPCODE_SET_GPIO                     =  0x03
OPCODE_START_STOP_STREAMING         =  0x04
OPCODE_GET_FW_VERSION               =  0x05
OPCODE_GET_FW_READABLE_VERSION      =  0x06
OPCODE_RESET_COMMAND                =  0x07

OPCODE_GET_PARAM_8                  = 0x20
OPCODE_GET_PARAM_16                 = 0x21
OPCODE_GET_PARAM_32                 = 0x22
OPCODE_GET_PARAM_168                = 0x23
OPCODE_SET_PARAM_8                  = 0x24
OPCODE_SET_PARAM_16                 = 0x25
OPCODE_SET_PARAM_32                 = 0x26
OPCODE_SET_PARAM_168                = 0x27
OPCODE_GET_PIXART_REGISTER          = 0x28
OPCODE_SET_PIXART_REGISTER          = 0x29
OPCODE_RESET_CMOS_POSITION          = 0x2A
OPCODE_GET_STATION_PRESSURE         = 0x2B
OPCODE_GET_STATION_MOT_CURRENT      = 0x2C
# OPCODE_START_STREAMING              = 0x2D  legacy opcode.
OPCODE_SET_MOTOR_STATE              = 0x2E
OPCODE_GET_MOTOR_STATE              = 0x2F
OPCODE_GET_MOTION_BURST             = 0x30
OPCODE_GET_ENCODER_COUNT            = 0x31
OPCODE_RESET_INS_AND_TRQ            = 0x32
OPCODE_N_A                          = 0x33
OPCODE_GO_TO_POSITION_NON_BLOCKING  = 0x34
OPCODE_PWM_BYTE_COMMAND             = 0x35
OPCODE_RESET_ENCODER                = 0x36
OPCODE_JOG_CAN_TBD                  = 0x37
OPCODE_GO_TO_HOME_POS_NON_BLOCKING  = 0x38
OPCODE_SET_MOTOR_CURRENT_LIMIT      = 0x39
OPCODE_GET_STATION_LEDS_STATE       = 0x3A
OPCODE_GET_STATION_PIXART_ID        = 0x3B
OPCODE_SET_STATION_PIXART_INIT_SET  = 0x3C


MAX_LONG_POSITIVE = 2**31
MAX_UNSIGNED_LONG = 2**32
MAX_INT24_POSITIVE = 2**23
MAX_U4_INT = 2**24
MAX_INT20_POSITIVE = 2**19
MAX_U20_INT = 2**20
MAX_INT16_POSITIVE = 2**15
MAX_UNSIGNED_INT = 2**16
def long_unsigned_to_long_signed( x ):
    if x > MAX_LONG_POSITIVE:
        x = x - MAX_UNSIGNED_LONG
    return x

# when we uses 3 bytes of communication to pass unsigned long.
def U24_bits_to_signed( x ):
    if x > MAX_INT24_POSITIVE:
        x = x - MAX_U4_INT
    return x

def U20_bits_to_signed( x ):
    if x > MAX_INT20_POSITIVE:
        x = x - MAX_U20_INT
    return x

def unsigned_to_signed( x ):
    if x > MAX_INT16_POSITIVE:
        x = x - MAX_UNSIGNED_INT
    return x


def my_seperator(frame, row):
    ttk.Separator(frame, orient=tk.HORIZONTAL).grid(pady=10, row=row, columnspan=4, sticky=(tk.W + tk.E))
    return row + 1

def streaming_button_CallBack():
    global special_cmd
    print("streaming_button pressed")
    special_cmd = 'I'

def stop_streaming_CallBack():
    global special_cmd
    print("stop_button pressed")
    special_cmd = 'S'

def reset_ins_and_torque_CallBack():
    global special_cmd
    special_cmd = 'reset_ins_and_torque'

expert_send_index = 0
def expert_send_callback(button_index):
    global special_cmd
    global expert_send_index
    special_cmd = 'expert_send'
    print("Button", button_index, "clicked!")
    expert_send_index = button_index
    # Saving the values // save
    values = []
    for entry in g_id_entry + g_data_entry + g_count_entry + g_time_entry:
        values.append(entry.get())

    with open('parameters.pkl', 'wb') as f:
        pickle.dump(values, f)



prev_pwm = 0
pwm_widget = 0
def show_pwm_values():
    global pwm_widget
    if pwm_widget != None:  # wait for widget to be created first.
        return pwm_widget.get()
    return 0

slot_entry = 0
# from chatGpt:
def slot_entry_changed(event):
    global SLOT_NUMBER
    new_value = slot_entry.get()  # Get the new value from the entry field
    print("New value:", new_value)
    try:
        numeric_value = int(new_value)  # Convert the new value to an integer
        # Use the numeric_value in the rest of your code
        print("Numeric value:", numeric_value)
        if numeric_value <= MAX_SLOT_NUMBER:
            SLOT_NUMBER = numeric_value
        else:
            print("Invalid value entered: SLOT_NUMBER must be less or equal 7 !!!")
    except ValueError:
        print("Invalid value entered")

stream_data = None
def can_read( device ):
    global stream_data
    msg = None 
    prev_timestamp = 0
    while True:
        # Read the packet from the device
        msg = device.recv(timeout=0.001)
        # value = device.read(READ_SIZE, timeout=READ_TIMEOUT)
        if msg != None:
            if msg.timestamp > prev_timestamp:
                stream_data = msg 
            prev_timestamp = msg.timestamp
            

tool_size_label = None 
g_id_entry     = []  # Empty list
g_data_entry   = []  
g_count_entry  = [] 
g_time_entry   = []  
g_send_button  = []  
# def tool_size_changed(value):
    # global tool_size_label
    # if tool_size_label != None:
        # tool_size_label.config(text = str(value))
        # if( abs(tool_size_changed.prev_val - value) > 16):
            # print("New tool_size_label:", value)
        # tool_size_changed.prev_val = value
# tool_size_changed.prev_val = 0
        
# gui_loop() - this is the gui funtion that is running endlessly as a thread
# functions: 
#            1) write to device according to global indication: special_cmd
#            2) read from the device each time. 
#               the main delay between device reads is due to the update of the gui by handler 
def gui_loop(device):  # the device is CAN device
    do_print = True
    global special_cmd
    skips = 190
    hex_pwm_val = 0
    do_once = 1
    start_time1 = time.time() * 1000  # Convert current time to milliseconds
    msg = None
    while True:
            
        if special_cmd:
            print("special_cmd=",special_cmd)
        # Write to the device (request data; keep alive)
        if special_cmd == 'I':
            cmd = "Start"
            data = [ord(c) for c in cmd]
            # "0x01 Start" = 01 53 74 61 72 74
            # message = can.Message(arbitration_id=0x044, data=[0x01] + data, is_extended_id=False)
            out_opcode_id = ((OPCODE_START_STOP_STREAMING<<4)+SLOT_NUMBER)
            message = can.Message(arbitration_id=out_opcode_id, data=[0x01] + data, is_extended_id=False)
            
            device.send(message)
            print("special_cmd Start", data )
            special_cmd = 0

        if special_cmd == 'S':
            cmd = "Stop"
            data = [ord(c) for c in cmd]
            # "0x01 Start" = 00 53 74 61 72 74
            # message = can.Message(arbitration_id=0x044, data=[0x00] + data, is_extended_id=False)
            out_opcode_id = ((OPCODE_START_STOP_STREAMING<<4)+SLOT_NUMBER)
            message = can.Message(arbitration_id=out_opcode_id, data=[0x00] + data, is_extended_id=False)
            device.send(message)
            # print("special_cmd Stop", data )
            print("special_cmd stop ", "  data: ", Fore.YELLOW + str(data) + Style.RESET_ALL)
            special_cmd = 0

        if special_cmd == 'special_cmd_pwm':
            send_list = [0x08,0,0,0,0,0,0,0]
            send_list[0] = 1<<(SLOT_NUMBER-1)
            send_list[SLOT_NUMBER] = hex_pwm_val
            print(send_list)
            # art_data = bytearray([0x08,0,0,0]) + hex_pwm_val + bytearray([0x20,0,0,0])
            art_data = bytearray(send_list)
            out_data = hex_pwm_val
            # message = can.Message(arbitration_id=0x354, data=art_data, is_extended_id=False)
            # out_opcode_id = (OPCODE_PWM_BYTE_COMMAND*16+SLOT_NUMBER)
            out_opcode_id = ((OPCODE_PWM_BYTE_COMMAND<<4)+SLOT_NUMBER)
            message = can.Message(arbitration_id=out_opcode_id, data=art_data, is_extended_id=False)
            device.send(message)
            # print all as hex values instead of a printable char 
            hex_values = ' '.join(format(byte, '02X') for byte in art_data)
            print("special_cmd pwm: ", hex_values,"  in list:", send_list )
            special_cmd = 0

        if special_cmd == 'reset_ins_and_torque':
            # Reset Ins & Torque 
            # need to be empty command with no data 
            # message = can.Message(arbitration_id=0x324, data=[] , is_extended_id=False)
            out_opcode_id = ((OPCODE_RESET_INS_AND_TRQ<<4)+SLOT_NUMBER)
            message = can.Message(arbitration_id=out_opcode_id, data=[] , is_extended_id=False)
            device.send(message)
            print("special_cmd Reset Ins & Torque")
            special_cmd = 0

        if special_cmd == 'expert_send':
            # print("special_cmd expert_send")
            global expert_send_index
            out_opcode_id = g_id_entry[expert_send_index].get()
            print("out_opcode_id= %03x in hex in string %s" % (int(out_opcode_id,16),out_opcode_id) )
            a_send_list = g_data_entry[expert_send_index].get()
            print("a_send_list= %03x data string %s" % (int(out_opcode_id,16),a_send_list) )
            send_list = [int(pair, 16) for pair in a_send_list.split()]
            print("send_list=",send_list)
            art_data = bytearray(send_list)
            message = can.Message(arbitration_id=int(out_opcode_id,16), data=art_data, is_extended_id=False)
            device.send(message)
            # print all as hex values instead of a printable char 
            hex_values = ' '.join(format(byte, '02X') for byte in art_data)
            print("special_cmd expert_send: ", hex_values,"  in list:", send_list )

            special_cmd = 0

        # handle the PWM command to device
        global prev_pwm
        # WRITE_DATA_CMD___bytearray = bytearray(b'\x3f')  # initialization of the command
        pwm_val = show_pwm_values()
        if (prev_pwm) != (pwm_val):
            byte_array = bytearray()  # create an empty bytearray
            # byte_array.append((pwm_val & 0xFF00) >> 8 )   # MSB
            byte_array.append((pwm_val & 0x00FF))         # LSB
            print("prev_pwm=  ",int(prev_pwm), "     pwm_val= ",int(pwm_val) )
            # hex_pwm_val = byte_array
            hex_pwm_val = pwm_val & 0x00FF
            print("hex_pwm_val =",hex_pwm_val)
            special_cmd = 'special_cmd_pwm'
        prev_pwm = pwm_val
        
#        # Measure time based on delay_time1
#        delay_time1 = 1000  # Time in milliseconds
#        # Check if delay_time1 has passed
#        current_time = time.time() * 1000
#        # print("Time for current_time:", current_time)
#        if current_time - start_time1 >= delay_time1:
#            # print("Time for         delay_time1:", current_time)
#            start_time1 = time.time() * 1000  # Convert current time to milliseconds

        # Read the packet from the device
        # value = device.read(READ_SIZE, timeout=READ_TIMEOUT)
        
        # use the msg from the real-time thread can_read()
        # msg = device.recv(timeout=0.001)
        # the msg.data is of type bytearray()

        global stream_data
        if( stream_data != None ):
            msg = stream_data

        # Update the GUI
        #if len(value) >= READ_SIZE:
        #    handler(value, do_print=do_print)
        if msg is not None and msg.arbitration_id == (STREAMING_DATA_TYPE_1 + SLOT_NUMBER):
            skips += 1 
            if (skips%400) == 0:
                print("Received message with data:", msg.data)
                do_print = 1
            # pass the binary data to the handler
            value = msg.data
            msg_type = 1
            gui_updater_handler(value,msg_type,do_print)
            do_print = 0
        if msg is not None and msg.arbitration_id == (STREAMING_DATA_TYPE_2 + SLOT_NUMBER):
            skips += 1 
            if (skips%400) == 0:
                print("Received message with data:", msg.data)
                do_print = 1
            # pass the binary data to the handler
            value = msg.data
            msg_type = 1
            gui_updater_handler(value,msg_type,do_print)
            do_print = 0

        # reset the global and local indication of incoming streaming
        stream_data = None
        msg = None
            


# gui_updater_handler: 
#   input: value - packet from the device that was read in the gui_loop()
#   called by:  gui_loop() each time a full packet of 64 bytes was read by device.read()
#   function:   update auxiliary varibles and then the relevant GUI elements. // example: tool_size
def gui_updater_handler(value,msg_type, do_print=False):
    CMOS_INDEX = 1
    MAX_TOOL_SIZE = 2495
    # for 12 bits we use tool_size: 0..1247 (aka original/2)

#+---+---+---+---+-- +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
#|             byte-0            |            byte-1             |             byte-2            |            byte-3             |            byte-4             |             byte-5            |             byte-6            |             byte-7            |
#+---+---+---+---+-- +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
#| 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
#+---+---+---+---+-- +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
#|    TBD        |                   tool_size                   |       image quality           |                            insertion                                          |                        roll                                                   |
#+---+---+---+---+-- +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
    if len(value) == 8:
        if msg_type == 1:
            #### here is the new format of:      | TBD | tool_size| quality | insertion | torque |  ####
            # tool_size = (int(value[1]) << 8) + int(value[0])
            # we swaped the MSB LSB of byte-0 and byte-1 in the FW (aka: big endian)
            tool_size = ((int(value[0])&0xF) << 8) + int(value[1])
            signed_tool_size = U24_bits_to_signed(tool_size)
            global tool_size_label
            tool_size_label.config(text = str(signed_tool_size))
            # if gui_updater_handler.prev_signed_tool_size != signed_tool_size:
                # tool_size_changed(signed_tool_size)
            # gui_updater_handler.prev_signed_tool_size = signed_tool_size
            
            if do_print:
                print("tool_size[2bytes]: %06x    %d  " % (int(tool_size), signed_tool_size))
            # scaling to progressbar range 0..100 
            precentage_stream_channel1 = abs(int((signed_tool_size / MAX_TOOL_SIZE) * 100))
            
            image_quality  = int(value[2])

# // +-------------------------------+-------------------------------+-------------------------------+-------------------------------+-------------------------------+
# // |             byte-3            |             byte-4            |             byte-5            |             byte-6            |             byte-7            |
# // +===+===+===+===+===+===+===+===+===+===+===+===+===+===+===+===+===+===+===+===+===+===+===+===+===+===+===+===+===+===+===+===+===+===+===+===+===+===+===+===+
# // | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
# // +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
# // |                                   insertion                                   |                                     roll                                      |
# // +-------------------------------------------------------------------------------+-------------------------------------------------------------------------------+


            # insertion = (int(value[2]) << 8) + int(value[3]) + (int(value[4]) << 16)
            # bytes  2,3,4 --now-->> 3 4 (5/2) 
            insertion = (int(value[3]) << 12) + (int(value[4]) << 4) + ((int(value[5]) & 0xF0) >> 4)
            signed_insertion = U20_bits_to_signed(insertion)
            insertion_label.config(text = str(signed_insertion))
            if do_print:
                print("insertion[2bytes]: %06x    %d  " % (int(insertion), signed_insertion))
            # scaling to progressbar range 0..100 
            precentage_stream_channel2 = abs(int((signed_insertion / 10000) * 100))

            # torque = (int(value[5]) << 8) + int(value[6]) + (int(value[7]) << 16)
            # bytes  5,6,7 --now-->> (5/2),6,7 
            torque = ((int(value[5])&0x0f) << 16) + (int(value[6])<<8) + (int(value[7]))
            signed_torque = U20_bits_to_signed(torque)
            torque_label.config(text = str(signed_torque))
            if do_print:
                print("torque[2bytes]: %06x    %d  " % (int(torque), signed_torque))
            # scaling to progressbar range 0..100 
            precentage_stream_channel3 = abs(int((signed_torque / 10000) * 100))
        elif msg_type == 2:
            #### here is the old format of:      |tool_size| insertion | torque |  ####
            # the value[] vector:
            #                |tool_siz|           |  torque
            #    bytearray(b'\x00\x00\x04\xd8\x00\x1d\xf0\x00')
            #                         | insertion|    
            #
            #    (b'\x00\x00\x04\xd8\x00\x1d\xf0\x00')
            # byte:           b1  b0  b2
            # index:  0    1   2   3   4   5   6   7        
            tool_size = (int(value[1]) << 8) + int(value[0])
            signed_tool_size = U24_bits_to_signed(tool_size)
            if do_print:
                print("tool_size[2bytes]: %06x    %d  " % (int(tool_size), signed_tool_size))
            # scaling to progressbar range 0..100 
            precentage_stream_channel1 = abs(int((signed_tool_size / MAX_TOOL_SIZE) * 100))

            insertion = (int(value[2]) << 8) + int(value[3]) + (int(value[4]) << 16)
            signed_insertion = U24_bits_to_signed(insertion)
            if do_print:
                print("insertion[2bytes]: %06x    %d  " % (int(insertion), signed_insertion))
            # scaling to progressbar range 0..100 
            precentage_stream_channel2 = abs(int((signed_insertion / 10000) * 100))

            torque = (int(value[5]) << 8) + int(value[6]) + (int(value[7]) << 16)
            signed_torque = U24_bits_to_signed(torque)
            if do_print:
                print("torque[2bytes]: %06x    %d  " % (int(torque), signed_torque))
            # scaling to progressbar range 0..100 
            precentage_stream_channel3 = abs(int((signed_torque / 10000) * 100))
    else:
        precentage_stream_channel1 = 11 # default value for debug.
        precentage_stream_channel2 = 17 # default value for debug.
        precentage_stream_channel3 = 18 # default value for debug.
        
    # allocation of variables (on the left side) to ProgressBars
    # that were created in my_widgets() function, were progressbars[] is global list of widgets.
    progressbar_stream_channel1 = progressbars[0]
    progressbar_stream_channel2 = progressbars[1]
    progressbar_stream_channel3 = progressbars[2]

    # the actual update of the "value" in the GUI progressbar element associated variable
    progressbar_stream_channel1["value"] = precentage_stream_channel1
    progressbar_stream_channel2["value"] = precentage_stream_channel2
    progressbar_stream_channel3["value"] = precentage_stream_channel3

    # the actual updating of all the gui elements acording the above asosiated variables 
    root.update()
gui_updater_handler.prev_signed_tool_size = 0

# my_widgets(): is the place were all the widgets are created 
#               (aka: size, orientation, style, position etc.)
# argument: frame - in this argument we pass the global class "root"
def my_widgets(frame):
    # ...
    # Create a notebook widget
    notebook = ttk.Notebook(frame)
    notebook.grid(row=0, column=0, padx=10, pady=10)

    row = 1
    CMOS_PROGRESS_BAR_LEN = 250 
    LONG_PROGRESS_BAR_LEN = 300 

    # Create the first tab with Progressbar widgets
    tab1 = ttk.Frame(notebook)
    notebook.add(tab1, text="User / Basic")

    frame = tab1
    # Label + Entry for slot_entry
    ttk.Label(frame,text="Enter slot number:").grid(row=row,column=0,sticky=tk.W,)
    w = ttk.Entry(frame,width=5,)
    global slot_entry
    slot_entry = w
    slot_entry.insert(0, "4")  # Set the default value
    # slot_entry.bind("<<Modified>>", print_entry_value)
    # w.grid(padx=10,pady=5,row=row,column=1,columnspan=1)#,sticky=tk.E,)
    w.grid(padx=10,pady=5,row=row,column=0,columnspan=1,sticky=tk.E,)
    row += 1
    # frame.bind("<Control-s>", lambda event: set_entry_value())
    # // the usage of <Enter> caused every mouse move to call the lambda function.
    # Bind the event to the entry widget
    slot_entry.bind("<Return>", slot_entry_changed)  # Call slot_entry_changed when Enter key is pressed
    
    w = ttk.Progressbar(frame,orient=tk.HORIZONTAL,length=CMOS_PROGRESS_BAR_LEN) #,style="batteryLevel")
    # adding the actual widget to the progressbars global list 
    progressbars.append(w)
    w.grid(row=row,column=0,columnspan=2)
    
    #numeric indication label:
    global tool_size_label
    tool_size_label = ttk.Label(frame,text="tool_size", foreground="#0000FF")
    tool_size_label.grid(row=row,column=3,sticky=tk.W,)

    row += 1
    w = ttk.Progressbar(frame,orient=tk.HORIZONTAL,length=LONG_PROGRESS_BAR_LEN) #,style="batteryLevel")
    # adding the actual widget to the progressbars global list 
    progressbars.append(w)
    w.grid(row=row,column=0,columnspan=2)
    #numeric indication label:
    global insertion_label
    insertion_label = ttk.Label(frame,text="insertion", foreground="#0000FF")
    insertion_label.grid(row=row,column=3,sticky=tk.W,)

    row += 1
    w = ttk.Progressbar(frame,orient=tk.HORIZONTAL,length=LONG_PROGRESS_BAR_LEN) #,style="batteryLevel")
    # adding the actual widget to the progressbars global list 
    progressbars.append(w)
    w.grid(row=row,column=0,columnspan=2)
    #numeric indication label:
    global torque_label
    torque_label = ttk.Label(frame,text="torque", foreground="#0000FF")
    torque_label.grid(row=row,column=3,sticky=tk.W,)
    
    row += 1
    # Seperator
    row = my_seperator(frame, row)
    # ------------------------------------------------------ 
    temp_widget = tk.Button(frame,text ="Start streaming",command = streaming_button_CallBack, bg="#66FFFF")
    temp_widget.grid(row=row,column=0, sticky=(tk.W))

    temp_widget = tk.Button(frame,text ="Stop streaming",command = stop_streaming_CallBack)#, bg="#66FFFF")
    temp_widget.grid(row=row,column=1, sticky=(tk.E))
    row += 1
    # Seperator
    row = my_seperator(frame, row)
    # ------------------------------------------------------
    global pwm_widget
    # pwm_widget = tk.Scale(frame, from_=0, to=2**12, orient='horizontal',length=LONG_PROGRESS_BAR_LEN)
    pwm_widget = tk.Scale(frame, from_=0, to=2**8, orient='horizontal',length=LONG_PROGRESS_BAR_LEN)
    pwm_widget.grid(row=row,column=0,columnspan=2)
    row += 1
    # Seperator
    row = my_seperator(frame, row)
    # ------------------------------------------------------
    temp_widget = tk.Button(frame,text ="Reset Ins & Torque",command = reset_ins_and_torque_CallBack, bg="#00FF00")
    temp_widget.grid(row=row,column=0, sticky=(tk.W))

    # ------------------------------------------------------
    ###################### second tab ######################
    # ------------------------------------------------------
    # Create the second tab with Entry widgets
    tab2 = ttk.Frame(notebook)
    notebook.add(tab2, text="Expert")
    frame = tab2

    row = 0
    ttk.Label(frame,text="ID").grid(row=row,column=0,sticky=tk.W,)
    ttk.Label(frame,text="Data").grid(row=row,column=1,sticky=tk.W,)
    ttk.Label(frame,text="Count").grid(row=row,column=2,sticky=tk.W,)
    ttk.Label(frame,text="Time (ms)").grid(row=row,column=3,sticky=tk.W,)
    ttk.Label(frame,text="Tx").grid(row=row,column=4)#,sticky=tk.WE,)
    
    global g_id_entry
    global g_data_entry
    global g_count_entry
    global g_time_entry

    for i in range(MAX_EXPERT_LINES):
        row += 1
        w = ttk.Entry(frame,width=5,)
        # g_id_entry = w 
        g_id_entry.append(w)
        w.insert(0, "ID")  # Set the default value
        # w.grid(padx=10,pady=5,row=row,column=0,columnspan=1,sticky=tk.W,)
        w.grid(padx=2,pady=2,row=row,column=0,columnspan=1,sticky=tk.W,)

        w = ttk.Entry(frame,width=21,)
        g_data_entry.append(w)
        w.insert(0, "Data")  # Set the default value
        w.grid(padx=2,pady=2,row=row,column=1,columnspan=1,sticky=tk.W,)

        w = ttk.Entry(frame,width=7,)
        g_count_entry.append(w)
        w.insert(0, "Count")  # Set the default value
        w.grid(padx=2,pady=2,row=row,column=2,columnspan=1,sticky=tk.W,)

        w = ttk.Entry(frame,width=7,)
        g_time_entry.append(w)
        w.insert(0, "Time")  # Set the default value
        w.grid(padx=2,pady=2,row=row,column=3,columnspan=1,sticky=tk.W,)

        w = tk.Button(frame,text ="Send", command=lambda idx=i: expert_send_callback(idx)) #command = expert_send_callback)
        g_send_button.append(w)
        # w.insert(0, "Time")  # Set the default value
        w.grid(padx=2,pady=0,row=row,column=4,columnspan=1,sticky=tk.W,)


def init_widgets():
    values = []
    # Loading the values
    global g_id_entry
    global g_data_entry
    global g_count_entry
    global g_time_entry

    if os.path.exists('parameters.pkl'):
        try:
            with open('parameters.pkl', 'rb') as f:
                values = pickle.load(f)
                for i, entry in enumerate(g_id_entry + g_data_entry + g_count_entry + g_time_entry):
                    entry.delete(0, tk.END)  # Clear the existing value
                    entry.insert(0, values[i])
        except FileNotFoundError:
            print("No parameter file found.")
    else:
        print("No parameter file found, set default values...")
        for i in range(1,MAX_EXPERT_LINES):
            g_id_entry[i].delete(0, tk.END)
            g_id_entry[i].insert(0,"354")
            g_data_entry[i].delete(0, tk.END) 
            g_data_entry[i].insert(0,"18 01 00 90 80 00 00 00") 
            g_count_entry[i].delete(0, tk.END)
            g_count_entry[i].insert(0,"0")
            g_time_entry[i].delete(0, tk.END) 
            g_time_entry [i].insert(0,"50")

def main():
    # ...
    # Initialize the main window
    global root
    root = tk.Tk()
    screen_width = root.winfo_screenwidth()  # Width of the screen
    screen_height = root.winfo_screenheight() # Height of the screen
    # Calculate Starting X and Y coordinates for Window
    w = 436 #from AHK CAN_UTILL - modified.
    h = 300
    # x = (screen_width*2/3) - (w*3/4)
    x = (screen_width*1/3) - (w*3/4)
    y = (screen_height*0.08) 
    # to enforce the size and location on the screen uncomment the next line:
    root.geometry('%dx%d+%d+%d' % (w, h, x, y))
    util_title = "SIMBionix CAN_UTILL"+" (version:"+util_verstion+")"
    root.title(util_title)
    # Initialize the GUI widgets
    my_widgets(root)
    init_widgets()


    
    # create a CAN bus instance
    device = can.interface.Bus(bustype='ixxat', channel=0, bitrate=1000000)

    # Create thread that calls gui_loop()
    threading.Thread(target=gui_loop, args=(device,), daemon=True).start()

    # Create thread that calls can_read()
    threading.Thread(target=can_read, args=(device,), daemon=True).start()
    
    # Run the GUI main loop
    root.mainloop()


if __name__ == "__main__":
    main()


'''
history changes
2023_04_09 
- adding Progressbar for torque value 
- use U24_bits_to_signed() when needed.
- adding Start and Stop buttons.
2023_04_10
- adding values to tool_size progressbar
2023_04_11 
- adding the PWM scale pwm_widget.
2023_06_01
- change the geometry of the frame window
- add reset insertion and torque button
- adding out_opcode_id for using list of opcodes (from C code defines)
- Entry for slot_entry, to change the slot of the node to talk to.
2023_06_02
- clean all the redundant code for slot_entry from previous tries.
- making the "special_cmd_pwm" adjustable according to SLOT_NUMBER.
2023_06_03
- adding insertion_label,torque_label and tool_size_label 
2023_06_04
- adding "tabs" to the frame
- adding second tab with 10 lines of flexible commands to be sent (TBD)
- adding init_widgets() function. 
2023_06_06
- adding an argument to expert_send_callback()
- saving the user values of expert_send in file: parameters.pkl
- reloading the user last entered parameters of expert_send
- implementing and testing the special_cmd expert_send 
2023_06_09
- creating new demon thread to handle the can_read() and hence avoiding delay in GUI response.
'''    