#!/usr/bin/python3
# C:\Work\Python\HID_Util\src\CAN_UTILL.py 
util_verstion = "2023_06_01.a"

from binascii import hexlify
import sys
import argparse
import threading
from time import sleep
from time import process_time as timer
import can

import tkinter as tk
from tkinter import ttk
import tkinter.messagebox



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


prev_pwm = 0
pwm_widget = 0
def show_pwm_values():
    global pwm_widget
    if pwm_widget != None:  # wait for widget to be created first.
        return pwm_widget.get()
    return 0

slot_entry = 0
def print_entry_value(event):
    print("inside the print_entry_value")
    print(event)
    global slot_entry
    if slot_entry != None:  # wait for widget to be created first.
        new_value = slot_entry.get()
        print("New entry value:", new_value)

# set_entry_value is called when pressing Enter key
def set_entry_value():
    print("inside the set_entry_value")
    global slot_entry
    if slot_entry != None:  # wait for widget to be created first.
        new_value = slot_entry.get()
        print("New entry value:", new_value)

# from chatGpt:
def entry_changed(event):
    new_value = slot_entry.get()  # Get the new value from the entry field
    print("New value:", new_value)
    try:
        numeric_value = int(new_value)  # Convert the new value to an integer
        # Use the numeric_value in the rest of your code
        print("Numeric value:", numeric_value)
    except ValueError:
        print("Invalid value entered")
        
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
            print("special_cmd Stop", data )
            special_cmd = 0

        if special_cmd == 'G':
            art_data = bytearray([0x08,0,0,0]) + hex_pwm_val + bytearray([0x20,0,0,0])
            out_data = hex_pwm_val
            # message = can.Message(arbitration_id=0x354, data=art_data, is_extended_id=False)
            # out_opcode_id = (OPCODE_PWM_BYTE_COMMAND*16+SLOT_NUMBER)
            out_opcode_id = ((OPCODE_PWM_BYTE_COMMAND<<4)+SLOT_NUMBER)
            message = can.Message(arbitration_id=out_opcode_id, data=art_data, is_extended_id=False)
            device.send(message)
            print("special_cmd pwm: ", art_data )
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

        # handle the PWM command to device
        global prev_pwm
        # WRITE_DATA_CMD___bytearray = bytearray(b'\x3f')  # initialization of the command
        pwm_val = show_pwm_values()
        if (prev_pwm) != (pwm_val):
            byte_array = bytearray()  # create an empty bytearray
            # byte_array.append((pwm_val & 0xFF00) >> 8 )   # MSB
            byte_array.append((pwm_val & 0x00FF))         # LSB
            print("prev_pwm=  ",int(prev_pwm), "     pwm_val= ",int(pwm_val) )
            hex_pwm_val = byte_array
            print("hex_pwm_val =",hex_pwm_val)
            special_cmd = 'G'
        prev_pwm = pwm_val

        # Read the packet from the device
        # value = device.read(READ_SIZE, timeout=READ_TIMEOUT)
        msg = device.recv(timeout=0.1)
        # the msg.data is of type bytearray()

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
            if do_print:
                print("insertion[2bytes]: %06x    %d  " % (int(insertion), signed_insertion))
            # scaling to progressbar range 0..100 
            precentage_stream_channel2 = abs(int((signed_insertion / 10000) * 100))

            # torque = (int(value[5]) << 8) + int(value[6]) + (int(value[7]) << 16)
            # bytes  5,6,7 --now-->> (5/2),6,7 
            torque = ((int(value[5])&0x0f) << 16) + (int(value[6])<<8) + (int(value[7]))
            signed_torque = U20_bits_to_signed(torque)
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

# my_widgets(): is the place were all the widgets are created 
#               (aka: size, orientation, style, position etc.)
# argument: frame - in this argument we pass the global class "root"
def my_widgets(frame):
    # ...
    row = 0
    CMOS_PROGRESS_BAR_LEN = 250 
    LONG_PROGRESS_BAR_LEN = 300 

    # Label + Entry for slot_entry
    ttk.Label(frame,text="Enter slot number:").grid(row=row,column=0,sticky=tk.W,)
    w = ttk.Entry(frame,width=5,)
    global slot_entry
    slot_entry = w
    slot_entry.insert(0, "4")  # Set the default value
    slot_entry.bind("<<Modified>>", print_entry_value)
    # w.grid(padx=10,pady=5,row=row,column=1,columnspan=1)#,sticky=tk.E,)
    w.grid(padx=10,pady=5,row=row,column=0,columnspan=1,sticky=tk.E,)
    row += 1
    frame.bind("<Control-s>", lambda event: set_entry_value())
    # frame.bind("<Enter>", lambda event: set_entry_value()) 
    # // the usage of <Enter> caused every mouse move to call the lambda function.
    # Bind the event to the entry widget
    slot_entry.bind("<Return>", entry_changed)  # Call entry_changed when Enter key is pressed
    
    w = ttk.Progressbar(frame,orient=tk.HORIZONTAL,length=CMOS_PROGRESS_BAR_LEN) #,style="batteryLevel")
    # adding the actual widget to the progressbars global list 
    progressbars.append(w)
    w.grid(row=row,column=0,columnspan=2)
    row += 1
    w = ttk.Progressbar(frame,orient=tk.HORIZONTAL,length=LONG_PROGRESS_BAR_LEN) #,style="batteryLevel")
    # adding the actual widget to the progressbars global list 
    progressbars.append(w)
    w.grid(row=row,column=0,columnspan=2)
    row += 1
    w = ttk.Progressbar(frame,orient=tk.HORIZONTAL,length=LONG_PROGRESS_BAR_LEN) #,style="batteryLevel")
    # adding the actual widget to the progressbars global list 
    progressbars.append(w)
    w.grid(row=row,column=0,columnspan=2)
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
    
    
def main():
    # ...
    # Initialize the main window
    global root
    root = tk.Tk()
    screen_width = root.winfo_screenwidth()  # Width of the screen
    screen_height = root.winfo_screenheight() # Height of the screen
    # Calculate Starting X and Y coordinates for Window
    w = 436 #from AHK CAN_UTILL
    h = 255
    # x = (screen_width*2/3) - (w*3/4)
    x = (screen_width*1/3) - (w*3/4)
    y = (screen_height*0.1) 
    root.geometry('%dx%d+%d+%d' % (w, h, x, y))
    #root.geometry('+%d+%d' % (x, y))
    util_title = "SIMBionix CAN_UTILL"+" (version:"+util_verstion+")"
    root.title(util_title)
    # Initialize the GUI widgets
    my_widgets(root)
    
    # create a CAN bus instance
    device = can.interface.Bus(bustype='ixxat', channel=0, bitrate=1000000)

    # Create thread that calls gui_loop()
    threading.Thread(target=gui_loop, args=(device,), daemon=True).start()
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
'''    