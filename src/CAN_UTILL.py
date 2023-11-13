#!/usr/bin/python3
# C:\Work\Python\HID_Util\src\CAN_UTILL.py 
util_verstion = "2023_11_09.b"

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
from datetime import datetime
from string_date_time import get_date_time
from string_date_time import get_date_time_sec

# ############
#   globals: 
# ############
# create a global empty list for progressbars that will be added later in: my_widgets()
progressbars = list()
# create a global empty list for entries that will be added later in: my_widgets()
entries = list()
packets_counter_entry = list()
Recording_gap_entry =  list()

# create a global empty variable root to hold the class that represents the main window or the root 
#  window of your application.
root = None 
special_cmd = None
special_multi_cmd = None
last_stream_data = None
date_time_text = "NA"
# 2023_11_06 
g_recording_flag = 0
g_recording_gap = 1  # the default recording gap is every sample, aka: 1
g_columns = []
file1 = None
READ_SIZE = 8 # The size of streaming packet

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

# OPCODE_GENERAL_PURPOSE              =  0x00
# OPCODE_GET_BOARD_TYPE               =  0x01
# OPCODE_GET_GPIO                     =  0x02
# OPCODE_SET_GPIO                     =  0x03
OPCODE_START_STOP_STREAMING         =  0x04
# OPCODE_GET_FW_VERSION               =  0x05
# OPCODE_GET_FW_READABLE_VERSION      =  0x06
# OPCODE_RESET_COMMAND                =  0x07

# OPCODE_GET_PARAM_8                  = 0x20
# OPCODE_GET_PARAM_16                 = 0x21
# OPCODE_GET_PARAM_32                 = 0x22
# OPCODE_GET_PARAM_168                = 0x23
# OPCODE_SET_PARAM_8                  = 0x24
# OPCODE_SET_PARAM_16                 = 0x25
# OPCODE_SET_PARAM_32                 = 0x26
# OPCODE_SET_PARAM_168                = 0x27
# OPCODE_GET_PIXART_REGISTER          = 0x28
# OPCODE_SET_PIXART_REGISTER          = 0x29
# OPCODE_RESET_CMOS_POSITION          = 0x2A
OPCODE_GET_STATION_PRESSURE         = 0x2B
# OPCODE_GET_STATION_MOT_CURRENT      = 0x2C
# OPCODE_START_STREAMING              = 0x2D  legacy opcode.
# OPCODE_SET_MOTOR_STATE              = 0x2E
# OPCODE_GET_MOTOR_STATE              = 0x2F
# OPCODE_GET_MOTION_BURST             = 0x30
# OPCODE_GET_ENCODER_COUNT            = 0x31
OPCODE_RESET_INS_AND_TRQ            = 0x32
# OPCODE_N_A                          = 0x33
# OPCODE_GO_TO_POSITION_NON_BLOCKING  = 0x34
OPCODE_PWM_BYTE_COMMAND             = 0x35  ## used for exception
# OPCODE_RESET_ENCODER                = 0x36
# OPCODE_JOG_CAN_TBD                  = 0x37
# OPCODE_GO_TO_HOME_POS_NON_BLOCKING  = 0x38
# OPCODE_SET_MOTOR_CURRENT_LIMIT      = 0x39
# OPCODE_GET_STATION_LEDS_STATE       = 0x3A
# OPCODE_GET_STATION_PIXART_ID        = 0x3B
# OPCODE_SET_STATION_PIXART_INIT_SET  = 0x3C


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

def opcode_to_type( x ):
    # opcode + DIR_MASK 
    y = (x + 0x40)<<4 
    return y



def my_seperator(frame, row):
    ttk.Separator(frame, orient=tk.HORIZONTAL).grid(pady=10, row=row, columnspan=4, sticky=(tk.W + tk.E))
    return row + 1

def streaming_button_CallBack():
    global special_cmd
    print("streaming_button pressed")
    special_cmd = 'I'

def Get_Pwm_Value_button_CallBack():
# Get_Pwm_Value
    global special_cmd
    print("Get PWM value pressed")
    special_cmd = 'get_pwm_value'

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

expert_multi_send_index = 0
def expert_multi_send_callback(button_index):
    return
    
    
    global special_multi_cmd
    global expert_multi_send_index
    special_multi_cmd = 'expert_multi_send'
    print("Button", button_index, "clicked!")
    expert_multi_send_index = button_index
    g_count_value[button_index] = int(g_count_entry[button_index].get())
    g_time_delay[button_index] = int(g_time_entry[button_index].get())
    g_start_time[button_index] = time.time() * 1000
    
    # # Saving the values // save
    # values = []
    # for entry in g_id_entry + g_data_entry + g_count_entry + g_time_entry:
        # values.append(entry.get())

    # with open('parameters.pkl', 'wb') as f:
        # pickle.dump(values, f)

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
    global g_recording_gap
    g_recording_gap = int(Recording_gap_entry.get())
    try:
        user_numeric_value = float(g_recording_gap)
        print("User g_recording_gap numeric value:", user_numeric_value)
    except ValueError:
        print("Invalid numeric value entered.")

def start_recordig():
    global file1
    global g_recording_gap
    global g_columns
    
    dummy=[]
    recording_handler(dummy) # call just to set the g_columns of metadata
    FILE1_PATH = "log\can_" # log.csv"
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
        # g_columns.append("Image Quality")
        result = ', '.join(g_columns)
        print("# recording_handler() columns=",result)
    if len(value) >= READ_SIZE:
        tool_size = ((int(value[0])&0xF) << 8) + int(value[1])
        tool_size = U24_bits_to_signed(tool_size)
        torque = ((int(value[5])&0x0f) << 16) + (int(value[6])<<8) + (int(value[7]))
        torque = U20_bits_to_signed(torque)
        insertion = (int(value[3]) << 12) + (int(value[4]) << 4) + ((int(value[5]) & 0xF0) >> 4)
        insertion = U20_bits_to_signed(insertion)
        # image_quality = (int(value[IMAGE_QUALITY_INDEX]) )
        # shutter = (int(value[SHUTTER_INDEX]) )
        # frame_avg = (int(value[FRAME_AVG_INDEX]) )
        ### recording ::  tool_size, insertion, torque ###
        L = [ str(tool_size),",   ", str(insertion), ", " , str(torque), "\n" ]  
        if file1 != None:
            file1.writelines(L) 
        else:
            print("try to write to closed file... file was not found !!!")
recording_handler.once = 1

g_incoming_msg = None 
def rt_parser(msg):
    # this function uses global indication to signal the other parts of slower code 
    # it some event comes in the can 
    global g_incoming_msg
    rt_parser.counter += 1
    if msg is not None and msg.arbitration_id == (opcode_to_type(OPCODE_GET_STATION_PRESSURE) + SLOT_NUMBER):
        print("RT Received message with data:", hexlify(msg.data))
        # pass the msg to other threads
        g_incoming_msg = msg
    else:
        value = msg.data
        # toggle the recording indication
        global recording_label
        global g_recording_flag
        global g_recording_gap
        if g_recording_flag == 1:
            # do recording into the last file that was opened by the button press
            if (rt_parser.counter % g_recording_gap) == 0:
                recording_handler(value)
            if (rt_parser.counter % 250)  < 175:
                recording_label.config(text = "Recording ON",foreground="#FF0000",font=("TkDefaultFont", 20, "bold"))
            else:
                recording_label.config(text = " ",foreground="#FF0000",font=("TkDefaultFont", 20, "bold"))
        else:
                recording_label.config(text = " ",foreground="#FF0000",font=("TkDefaultFont", 20, "bold"))
rt_parser.counter = 0
    

stream_data = None
g_packets_counter = 0
g_always_counter = 0
def can_read(device):
    global stream_data
    global g_packets_counter
    global g_always_counter
    msg = None 
    prev_timestamp = 0
    while True:
        g_always_counter += 1
        # Read the packet from the device
        msg = device.recv(timeout=0.001)
        # value = device.read(READ_SIZE, timeout=READ_TIMEOUT)
        if msg != None:
            if msg.timestamp > prev_timestamp:
                stream_data = msg 
                g_packets_counter += 1
                rt_parser(msg)
            prev_timestamp = msg.timestamp
            # reset the msg to go to sleep...
            msg = None
        else:
            time.sleep(100/1000)  # 100 miliSeconds delay before next read from CAN-BUS.
            # print(g_always_counter)
            
def can_send(device):  # TBD... 2023_06_10__15_10
    global special_multi_cmd
    msg = None 
    prev_timestamp = 0
    thread_counter = 0
    display_thread_counter = 0
    # delay_time = []
    current_time = []
    for i in range(len(g_time_entry)):
        current_time.append(0)
        pass
    while True:
        # send a packet acording to combination of count/time(ms)
        # value = device.read(READ_SIZE, timeout=READ_TIMEOUT)
        if special_multi_cmd == 'expert_multi_send':
            for indx in range( len(g_count_value)):
                if g_count_value[indx] > 0 :
                    current_time[indx] = time.time() * 1000
                    if current_time[indx] - g_start_time[indx] > g_time_delay[indx] :
                        print("special_multi_cmd -- expert_multi_send")
                        global expert_multi_send_index
                        out_opcode_id = g_id_entry[indx].get()
                        print("out_opcode_id= %03x in hex in string %s" % (int(out_opcode_id,16),out_opcode_id) )
                        a_send_list = g_data_entry[indx].get()
                        print("a_send_list= %03x data string %s" % (int(out_opcode_id,16),a_send_list) )
                        send_list = [int(pair, 16) for pair in a_send_list.split()]
                        print("send_list=",send_list)
                        art_data = bytearray(send_list)
                        message = can.Message(arbitration_id=int(out_opcode_id,16), data=art_data, is_extended_id=False)
                        device.send(message)
                        # print all as hex values instead of a printable char 
                        hex_values = ' '.join(format(byte, '02X') for byte in art_data)
                        print("special_multi_cmd expert_send: ", hex_values,"  in list:", send_list )
                        # decrement the count value to step down...
                        g_count_value[indx] -= 1
                        if g_count_value[indx] == 0:
                            special_multi_cmd = 0
                        g_start_time[indx] = time.time() * 1000

#        # Measure time based on delay_time1
#        delay_time1 = 1000  # Time in milliseconds
#        # Check if delay_time1 has passed
#        current_time = time.time() * 1000
#        # print("Time for current_time:", current_time)
#        if current_time - start_time1 >= delay_time1:
#            # print("Time for         delay_time1:", current_time)
#            start_time1 = time.time() * 1000  # Convert current time to milliseconds

        # if special_multi_cmd == 'expert_multi_send':
        # if( False):
        #     print("special_multi_cmd -- expert_multi_send")
        #     global expert_multi_send_index
        #     out_opcode_id = g_id_entry[expert_multi_send_index].get()
        #     print("out_opcode_id= %03x in hex in string %s" % (int(out_opcode_id,16),out_opcode_id) )
        #     a_send_list = g_data_entry[expert_multi_send_index].get()
        #     print("a_send_list= %03x data string %s" % (int(out_opcode_id,16),a_send_list) )
        #     send_list = [int(pair, 16) for pair in a_send_list.split()]
        #     print("send_list=",send_list)
        #     art_data = bytearray(send_list)
        #     message = can.Message(arbitration_id=int(out_opcode_id,16), data=art_data, is_extended_id=False)
        #     device.send(message)
        #     # print all as hex values instead of a printable char 
        #     hex_values = ' '.join(format(byte, '02X') for byte in art_data)
        #     print("special_multi_cmd expert_send: ", hex_values,"  in list:", send_list )

        #     special_multi_cmd = 0
        else:
            # busy wait delay if thread is idle. 
            time.sleep(1/1000)
            if( (thread_counter % 1000) == 0):
                print("can_send-- display_thread_counter = ", display_thread_counter)
                display_thread_counter +=1
            thread_counter +=1
            
            

tool_size_label = None 
g_id_entry     = []  # Empty list
g_data_entry   = []  
g_count_entry  = [] 
g_time_entry   = []  
g_send_button  = []  
g_multi_send_button  = [] 
g_time_delay   = [] 
g_count_value  = [] 
g_start_time   = []
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
            
        # if special_cmd:
            # print("special_cmd=",special_cmd)
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

        if special_cmd == 'get_pwm_value':
            out_opcode_id = ((OPCODE_GET_STATION_PRESSURE<<4)+SLOT_NUMBER)
            message = can.Message(arbitration_id=out_opcode_id, data=[], is_extended_id=False)
            device.send(message)
            print("special_cmd get_pwm_value: %x " %(out_opcode_id))
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
        

        # Read the packet from the device
        # value = device.read(READ_SIZE, timeout=READ_TIMEOUT)
        
        # use the msg from the real-time thread can_read()
        # msg = device.recv(timeout=0.001)
        # the msg.data is of type bytearray()

        global stream_data
        if( stream_data != None ):
            msg = stream_data

        # Update the GUI
        global debug_prints_var
        #if len(value) >= READ_SIZE:
        #    handler(value, do_print=do_print)
        if msg is not None and msg.arbitration_id == (STREAMING_DATA_TYPE_1 + SLOT_NUMBER):
            skips += 1 
            if (skips%400) == 0:
                if debug_prints_var.get():
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
                if debug_prints_var.get():
                    print("Received message with data:", msg.data)
                    do_print = 1
            # pass the binary data to the handler
            value = msg.data
            msg_type = 1
            gui_updater_handler(value,msg_type,do_print)
            do_print = 0

        # we use g_incoming_msg to capture any can message which is not streaming data.
        global g_incoming_msg
        if g_incoming_msg is not None:
            msg = g_incoming_msg
            print("GUI Received message with data:", hexlify(msg.data))
            g_incoming_msg = None
            value = msg.data
            msg_type = 3
            gui_updater_handler(value,msg_type,do_print)
            

        # reset the global and local indication of incoming streaming
        stream_data = None
        msg = None
            


# gui_updater_handler: 
#   input: value - packet from the device that was read in the gui_loop()
#   called by:  gui_loop() each time a full packet of 64 bytes was read by device.read()
#   function:   update auxiliary varibles and then the relevant GUI elements. // example: tool_size
def gui_updater_handler(value,msg_type, do_print=False):
    global Last_Stream_Packet_Time
    global date_time_text

    current_time = datetime.now()
    # initial values for handler variables
    if gui_updater_handler.once == 1:
        gui_updater_handler.once = 0
        gui_updater_handler.start_streaming_time = current_time
        precentage_stream_channel1 = 0 # default value for debug.
        precentage_stream_channel2 = 0 # default value for debug.
        precentage_stream_channel3 = 0 # default value for debug.

    formatted_time = current_time.strftime("%Y_%m_%d__%H:%M:%S")    # Format the date and time in the desired format
    last_date_time_text = date_time_text + formatted_time
    Last_Stream_Packet_Time.config(text = last_date_time_text) # for update the string field.
        
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
            gui_updater_handler.channel1 = abs(int((signed_tool_size / MAX_TOOL_SIZE) * 100))
            
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
            gui_updater_handler.channel2 = abs(int((signed_insertion / 10000) * 100))

            # torque = (int(value[5]) << 8) + int(value[6]) + (int(value[7]) << 16)
            # bytes  5,6,7 --now-->> (5/2),6,7 
            torque = ((int(value[5])&0x0f) << 16) + (int(value[6])<<8) + (int(value[7]))
            signed_torque = U20_bits_to_signed(torque)
            torque_label.config(text = str(signed_torque))
            if do_print:
                print("torque[2bytes]: %06x    %d  " % (int(torque), signed_torque))
            # scaling to progressbar range 0..100 
            gui_updater_handler.channel3 = abs(int((signed_torque / 10000) * 100))
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
            gui_updater_handler.channel1 = abs(int((signed_tool_size / MAX_TOOL_SIZE) * 100))

            insertion = (int(value[2]) << 8) + int(value[3]) + (int(value[4]) << 16)
            signed_insertion = U24_bits_to_signed(insertion)
            if do_print:
                print("insertion[2bytes]: %06x    %d  " % (int(insertion), signed_insertion))
            # scaling to progressbar range 0..100 
            gui_updater_handler.channel2 = abs(int((signed_insertion / 10000) * 100))

            torque = (int(value[5]) << 8) + int(value[6]) + (int(value[7]) << 16)
            signed_torque = U24_bits_to_signed(torque)
            if do_print:
                print("torque[2bytes]: %06x    %d  " % (int(torque), signed_torque))
            # scaling to progressbar range 0..100 
            gui_updater_handler.channel3 = abs(int((signed_torque / 10000) * 100))
        else:
            # do something
            pass
    else:
        print("2) len(value)",len(value))
        if msg_type == 3:
            # update the PWM progressbar
            input_pwm = int(value[0])
            pwm_percent = input_pwm/256 *100
            print("input_pwm", input_pwm,"  -->  input_pwm/256*100 = ", pwm_percent ,"%")
            gui_updater_handler.channel4 = pwm_percent 
            # update the PWM label indication according to percentage.
            temp_txt = ("{:.2f}".format(pwm_percent))
            label_pwm_text = temp_txt +"%"
            pwm_label.config(text = label_pwm_text)
            pass
        # precentage_stream_channel1 = 11 # default value for debug.
        # precentage_stream_channel2 = 17 # default value for debug.
        # precentage_stream_channel3 = 18 # default value for debug.
        
    # allocation of variables (on the left side) to ProgressBars
    # that were created in my_widgets() function, were progressbars[] is global list of widgets.
    # progressbar_stream_channel1 = progressbars[0]
    # progressbar_stream_channel2 = progressbars[1]
    # progressbar_stream_channel3 = progressbars[2]

    # the actual update of the "value" in the GUI progressbar element associated variable
    # progressbar_stream_channel1["value"] = precentage_stream_channel1
    # progressbar_stream_channel2["value"] = precentage_stream_channel2
    # progressbar_stream_channel3["value"] = precentage_stream_channel3
    progressbars[0]["value"] = gui_updater_handler.channel1
    progressbars[1]["value"] = gui_updater_handler.channel2
    progressbars[2]["value"] = gui_updater_handler.channel3
    progressbars[3]["value"] = gui_updater_handler.channel4

    # Update the text in the packets_counter_entry Entry widget
    global g_packets_counter
    packets_counter_entry.delete(0, tk.END)
    packets_counter_entry.insert(tk.END, "%d" % g_packets_counter)
    

    # the actual updating of all the gui elements acording the above asosiated variables 
    root.update()
gui_updater_handler.prev_signed_tool_size = 0
gui_updater_handler.start_streaming_time = 0
gui_updater_handler.once = 1
gui_updater_handler.channel1 = 1
gui_updater_handler.channel2 = 1
gui_updater_handler.channel3 = 1
gui_updater_handler.channel4 = 0

# my_widgets(): is the place were all the widgets are created 
#               (aka: size, orientation, style, position etc.)
# argument: frame - in this argument we pass the global class "root"
def my_widgets(frame):
    # ...
    # Create a notebook widget
    notebook = ttk.Notebook(frame)
    notebook.grid(row=0, column=0, padx=10, pady=10)
    
    bold_font = ("TkDefaultFont", 9, "bold")


    row = 1
    CMOS_PROGRESS_BAR_LEN = 250 
    LONG_PROGRESS_BAR_LEN = 300 

    # ------------------------------------------------------
    ###################### first tab ######################
    # ------------------------------------------------------
    # Create the first tab with Progressbar widgets
    tab1 = ttk.Frame(notebook)
    notebook.add(tab1, text="User / Basic")

    frame = tab1
    # Create labels to visualize column borders
    for i in range(4):
        separator_label = ttk.Label(frame, text=str(i), font=("Helvetica", 6),foreground="#999999")
        separator_label.grid(row=0, column=i)    
        # separator_label = ttk.Label(frame, text="|", font=("Helvetica", 9),foreground="#0000ff")
        # separator_label.grid(row=1, column=i,sticky=tk.E,)    
        # separator_label2 = ttk.Label(frame, text="!", font=("Helvetica", 9),foreground="#ff0000")
        # separator_label2.grid(row=1, column=i,sticky=tk.W,)

    row += 1
    # Label for last stream packet time.
    global Last_Stream_Packet_Time
    global date_time_text
    date_time_text = "Last stream packet time:  "
    Last_Stream_Packet_Time = ttk.Label(frame,text = date_time_text,font=bold_font, foreground="#000077")
    Last_Stream_Packet_Time.grid(row=row,column=1,columnspan=3,sticky=tk.W,)
    
    row += 1
    # Label + Entry for slot_entry
    ttk.Label(frame,text="Slot No.:").grid(row=row,column=0,sticky=tk.W,)
    w = ttk.Entry(frame,width=5,)
    global slot_entry
    slot_entry = w
    slot_entry.insert(0, "4")  # Set the default value
    # slot_entry.bind("<<Modified>>", print_entry_value)
    # w.grid(padx=10,pady=5,row=row,column=1,columnspan=1)#,sticky=tk.E,)
    w.grid(padx=0,pady=5,row=row,column=1,columnspan=1,sticky=tk.W,)
    row += 1
    # frame.bind("<Control-s>", lambda event: set_entry_value())
    # // the usage of <Enter> caused every mouse move to call the lambda function.
    # Bind the event to the entry widget
    slot_entry.bind("<Return>", slot_entry_changed)  # Call slot_entry_changed when Enter key is pressed

    # Label + Entry for packets_counter
    ttk.Label(frame,text="Packets:").grid(row=row,column=0,sticky=tk.W,)
    w = ttk.Entry(frame,width=15,)
    entries.append(w)
    global packets_counter_entry
    packets_counter_entry = w
    packets_counter_entry.insert(0, "0")  # Set the default value
    w.grid(padx=0,pady=5,row=row,column=1,columnspan=2,sticky=tk.W,)
    row += 1
    
    ttk.Label(frame,text="Tool_size:").grid(row=row,column=0,sticky=tk.W,)
    w = ttk.Progressbar(frame,orient=tk.HORIZONTAL,length=CMOS_PROGRESS_BAR_LEN) #,style="batteryLevel")
    # adding the actual widget to the progressbars global list 
    progressbars.append(w)
    w.grid(row=row,column=1,columnspan=2)
    
    #numeric indication label:
    global tool_size_label
    tool_size_label = ttk.Label(frame,text="tool_size", foreground="#0000FF")
    tool_size_label.grid(row=row,column=3,sticky=tk.W,)

    row += 1
    ttk.Label(frame,text="Insertion:").grid(row=row,column=0,sticky=tk.W,)

    w = ttk.Progressbar(frame,orient=tk.HORIZONTAL,length=LONG_PROGRESS_BAR_LEN) #,style="batteryLevel")
    # adding the actual widget to the progressbars global list 
    progressbars.append(w)
    w.grid(row=row,column=1,columnspan=2)
    #numeric indication label:
    global insertion_label
    insertion_label = ttk.Label(frame,text="insertion", foreground="#0000FF")
    insertion_label.grid(row=row,column=3,sticky=tk.W,)

    row += 1
    ttk.Label(frame,text="Torque:").grid(row=row,column=0,sticky=tk.W,)
    w = ttk.Progressbar(frame,orient=tk.HORIZONTAL,length=LONG_PROGRESS_BAR_LEN) #,style="batteryLevel")
    # adding the actual widget to the progressbars global list 
    progressbars.append(w)
    w.grid(row=row,column=1,columnspan=2)
    #numeric indication label:
    global torque_label
    torque_label = ttk.Label(frame,text="torque", foreground="#0000FF")
    torque_label.grid(row=row,column=3,sticky=tk.W,)
    
    row += 1
    # Seperator
    row = my_seperator(frame, row)
    # ------------------------------------------------------ 
    temp_widget = tk.Button(frame,text ="Start streaming",command = streaming_button_CallBack, bg="#66FFFF")
    temp_widget.grid(row=row,column=1, sticky=(tk.W))

    temp_widget = tk.Button(frame,text ="Stop streaming",command = stop_streaming_CallBack)#, bg="#66FFFF")
    temp_widget.grid(row=row,column=2, sticky=(tk.E))
    
    row += 1
    # Seperator
    row = my_seperator(frame, row)
    # ------------------------------------------------------

    # temp_widget = tk.Button(frame,text ="Get station pressure",command = Get_Pwm_Value_button_CallBack)
    temp_widget = tk.Button(frame,text ="Get PWM",command = Get_Pwm_Value_button_CallBack)
    temp_widget.grid(row=row,column=1, sticky=(tk.W))

    row += 1
    ttk.Label(frame,text="PWM:").grid(row=row,column=0,sticky=tk.W,)
    w = ttk.Progressbar(frame,orient=tk.HORIZONTAL,length=LONG_PROGRESS_BAR_LEN) #,style="batteryLevel")
    # adding the actual widget to the progressbars global list 
    progressbars.append(w)
    # w.grid(padx=20,pady=5,row=row,column=1,columnspan=2,sticky=tk.E,)
    w.grid(padx=0,pady=5,row=row,column=1,columnspan=2,sticky=tk.E,)
    #numeric indication label:
    global pwm_label
    pwm_label = ttk.Label(frame,text="pwm", foreground="#0000FF")
    pwm_label.grid(row=row,column=3,sticky=tk.W,)


    row += 1
    # Seperator
    row = my_seperator(frame, row)
    # ------------------------------------------------------
    ttk.Label(frame,text="PWM cmnd:").grid(row=row,column=0,sticky=tk.W,)
    global pwm_widget
    # pwm_widget = tk.Scale(frame, from_=0, to=2**12, orient='horizontal',length=LONG_PROGRESS_BAR_LEN)
    pwm_widget = tk.Scale(frame, from_=0, to=2**8, orient='horizontal',length=LONG_PROGRESS_BAR_LEN)
    pwm_widget.grid(row=row,column=1,columnspan=2)
    row += 1
    # Seperator
    row = my_seperator(frame, row)
    # ------------------------------------------------------
    temp_widget = tk.Button(frame,text ="Reset Ins & Torque",command = reset_ins_and_torque_CallBack, bg="#00FF00")
    # temp_widget = tk.Button(frame,text ="Reset",command = reset_ins_and_torque_CallBack, bg="#00FF00")
    temp_widget.grid(row=row,column=1,columnspan=4, sticky=(tk.W))

    row += 1
    row = my_seperator(frame, row)
    # ------------------------------------------------------

    temp_widget = tk.Button(frame,text ="Start/Stop Recording",command = start_stop_recording_callback)
    temp_widget.grid(row=row,column=0)

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
    ttk.Label(frame,text="multiTx").grid(row=row,column=5)#,sticky=tk.WE,)
    
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

        w = tk.Button(frame,text ="Multi Send", command=lambda idx=i: expert_multi_send_callback(idx)) #command = expert_multi_send_callback)  // g_multi_send_button
        g_send_button.append(w)
        # w.insert(0, "Time")  # Set the default value
        w.grid(padx=2,pady=0,row=row,column=5,columnspan=1,sticky=tk.W,)

    # ------------------------------------------------------
    ###################### third tab ######################
    # ------------------------------------------------------
    tab3 = ttk.Frame(notebook)
    notebook.add(tab3, text="Settings")
    frame = tab3

    row = 0
    # ttk.Label(frame,text="Enable debug prints:").grid(row=row,column=0,sticky=tk.W,)

    # Create the "debug_prints" checkbox
    global debug_prints_var 
    debug_prints_var = tk.BooleanVar(value=True)  # Set the default value to True (checked)
    debug_prints_checkbox = tk.Checkbutton(frame, text="enable streaming debug prints", variable=debug_prints_var)
    debug_prints_checkbox.grid(row=row, column=2)
        
    row += 1
    
    # ------------------------------------------------------
    ###################### 4-th tab  ######################
    # ------------------------------------------------------
    tab4 = ttk.Frame(notebook)
    notebook.add(tab4, text="Recording")
    frame = tab4

    for i in range(4):
        separator_label = ttk.Label(frame, text=str(i), font=("Helvetica", 6),foreground="#999999")
        separator_label.grid(row=0, column=i)    
    # ttk.Label(frame,text="Enable debug prints:").grid(row=row,column=0,sticky=tk.W,)

    # Create the "debug_prints" checkbox
    # global debug_prints_var 
    # debug_prints_var = tk.BooleanVar(value=True)  # Set the default value to True (checked)
    # debug_prints_checkbox = tk.Checkbutton(frame, text="enable streaming debug prints", variable=debug_prints_var)
    # debug_prints_checkbox.grid(row=row, column=2)
        
    row += 1

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
    w.grid(padx=10,pady=5,row=row,column=2,columnspan=1)

    Recording_gap_entry.bind('<Return>', on_enter_key)
    Recording_gap_entry.insert(tk.END, str(g_recording_gap))
    row += 1

    recording_text = "Press the button to record"
    global recording_label
    recording_label = tk.Label(frame,text = recording_text, foreground="#777777")
    recording_label.grid(row=row,column=0,columnspan=3,sticky=tk.W,)

    row += 1

    row = my_seperator(frame, row)
    # ------------------------------------------------------ 
    


def init_widgets():
    values = []
    # Loading the values
    global g_id_entry
    global g_data_entry
    global g_count_entry
    global g_time_entry
    global g_time_delay
    global g_count_value
    global g_start_time

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

    for i in range(len(g_time_entry)):
        new_value = g_time_entry[i].get()  # Get the new value from the entry field
        g_start_time.append(0)
        print("New value:", new_value)
        try:
            numeric_value = int(new_value)  # Convert the new value to an integer
            # Use the numeric_value in the rest of your code
            print("Numeric value:", numeric_value)
            g_time_delay.append(int(new_value))
        except ValueError:
            print("Invalid value entered")
            g_time_delay.append(11)

    for i in range(len(g_count_entry)):
        g_count_value.append(0)


def main():
    # ...
    # Initialize the main window
    global root
    root = tk.Tk()
    screen_width = root.winfo_screenwidth()  # Width of the screen
    screen_height = root.winfo_screenheight() # Height of the screen
    # Calculate Starting X and Y coordinates for Window
    # w = 436 #from AHK CAN_UTILL - modified.
    # w = 450 #from AHK CAN_UTILL - modified. 2023_11_01
    w = 500 #from AHK CAN_UTILL - modified. 2023_11_06
    h = 490
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

    # Create thread that calls can_send()
    # threading.Thread(target=can_send, args=(device,), daemon=True).start()
    
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
2023_06_10 
- creating new demon thread to handle the can_send() for sending the multiTx buttons.
- remove unused defines that are as globel variables (for easy code debug handling in VS code)
- adding a global list g_time_delay[] to pass the values for time delay to can_send
2023_06_11
- adding time delay between multi send, use: g_start_time,current_time,current_time
- commeting the multi thread process. 
2023_10_29
- adding special_cmd  'get_pwm_value' 
we don't want so put too much load of data in the streaming data of the CAN-BUS hence we added 
another query command to enable the PC to read back the PWM value, even though this value is 
originated from the PC in the first place.
- adding settings tab. 
- printing the _GET_STATION_PRESSURE response from device.
2023_10_30
- adding packets_counter_entry 
- refactoring the function gui_updater_handler()
2023_10_31
- adding PWM progressbars (not working yet)
- design of the widgets locations on the frame.
2023_11_02
- connect the PWM scrollbar to the returned value from cmd 2B
- add RT thread global indication g_incoming_msg, to signal the other parts of slower code 
- adding rt_parser() function.
- update the PWM label indication according to percentage.
2023_11_02.b
- to add time indication of the last streaming packet (using: datetime, Last_Stream_Packet_Time)
2023_11_06.a
- add streaming recording tab4: button, label and entry widgets.
2023_11_09.a
- fix the gap position on the recording TAB.
- add the g_recording_gap functionality.
2023_11_09.b
- add "Start/Stop Recording" button in the first (main) Tab.
'''    