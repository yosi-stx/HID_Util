#!/usr/bin/python3
# C:\Work\Python\HID_Util\src\CAN_UTILL.py 
util_verstion = "2023_04_09.a"

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
special_cmd = 0

def streaming_button_CallBack():
    global special_cmd
    special_cmd = 'I'

# gui_loop() - this is the gui funtion that is running endlessly as a thread
# functions: 
#            1) write to device according to global indication: special_cmd
#            2) read from the device each time. 
#               the main delay between device reads is due to the update of the gui by handler 
def gui_loop(device):  # the device is CAN device
    do_print = True
    global special_cmd
    skips = 190
    while True:
        # Write to the device (request data; keep alive)
        if special_cmd == 'I':
            # WRITE_DATA = WRITE_DATA_CMD_START_0x304
            # WRITE_DATA
            cmd = "Start"
            data = [ord(c) for c in cmd]
            # "0x01 Start" = 01 53 74 61 72 74
            message = can.Message(arbitration_id=0x104, data=[0x01] + data, is_extended_id=False)
            device.write(WRITE_DATA)
            print("special_cmd Start")
            special_cmd = 0

        # Read the packet from the device
        # value = device.read(READ_SIZE, timeout=READ_TIMEOUT)
        msg = device.recv()

        # Update the GUI
        #if len(value) >= READ_SIZE:
        #    handler(value, do_print=do_print)
        if msg is not None and msg.arbitration_id == 0x103:
            skips += 1 
            if (skips%200) == 0:
                print("Received message with data:", msg.data)
                do_print = 1
            # pass the binary data to the handler
            value = msg.data
            gui_updater_handler(value,do_print)
            do_print = 0
            


# gui_updater_handler: 
#   input: value - packet from the device that was read in the gui_loop()
#   called by:  gui_loop() each time a full packet of 64 bytes was read by device.read()
#   function:   update auxiliary varibles and then the relevant GUI elements. // example: tool_size
def gui_updater_handler(value, do_print=False):
    CMOS_INDEX = 1
    # the value[] vector:
    #                |tool_siz|           |  torque
    #    bytearray(b'\x00\x00\x04\xd8\x00\x1d\xf0\x00')
    #                         | insertion|    
    #    (b'\x00\x00\x04\xd8\x00\x1d\xf0\x00')
    # byte:           b1  b0  b2
    # index:  0    1   2   3   4   5   6   7        
    if len(value) == 8:
        insertion = (int(value[2]) << 8) + int(value[3]) + (int(value[4]) << 16)
        if do_print:
            print("insertion[2bytes]: %06x    %d  " % (int(insertion), insertion))
        # scaling to progressbar range 0..100 
        precentage_stream_channel2 = int((insertion / 10000) * 100)

        torque = (int(value[5]) << 8) + int(value[6]) + (int(value[7]) << 16)
        if do_print:
            print("torque[2bytes]: %06x    %d  " % (int(torque), torque))
        # scaling to progressbar range 0..100 
        precentage_stream_channel3 = int((torque / 10000) * 100)
    else:
        precentage_stream_channel2 = 17 # default value for debug.
        precentage_stream_channel3 = 18 # default value for debug.
        
    # allocation of variables (on the left side) to ProgressBars
    # that were created in my_widgets() function, were progressbars[] is global list of widgets.
    progressbar_stream_channel2 = progressbars[1]
    progressbar_stream_channel3 = progressbars[2]

    # the actual update of the "value" in the GUI progressbar element associated variable
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
    w = ttk.Progressbar(frame,orient=tk.HORIZONTAL,length=CMOS_PROGRESS_BAR_LEN) #,style="batteryLevel")
    # adding the actual widget to the progressbars global list 
    progressbars.append(w)
    w.grid(row=row,column=1,columnspan=2)
    row += 1
    w = ttk.Progressbar(frame,orient=tk.HORIZONTAL,length=LONG_PROGRESS_BAR_LEN) #,style="batteryLevel")
    # adding the actual widget to the progressbars global list 
    progressbars.append(w)
    w.grid(row=row,column=1,columnspan=2)
    row += 1
    w = ttk.Progressbar(frame,orient=tk.HORIZONTAL,length=LONG_PROGRESS_BAR_LEN) #,style="batteryLevel")
    # adding the actual widget to the progressbars global list 
    progressbars.append(w)
    w.grid(row=row,column=1,columnspan=2)
    row += 1
    # Seperator
    # row = my_seperator(frame, row)
    
    
def main():
    # ...
    # Initialize the main window
    global root
    root = tk.Tk()
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
'''    