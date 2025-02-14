# HR_util.py
util_verstion = "2025_02_14.a"

import tkinter as tk
from tkinter import ttk

import ctypes
ctypes.CDLL('..\\x64\\hidapi.dll')
import hid  # after workaround
from binascii import hexlify
import sys
import argparse
import threading
from time import perf_counter as timer
# import time 
from time import sleep

from datetime import datetime

import queue  # new consent from perplexity

# to do connect
VENDOR_ID = 0x2047 # Texas Instruments
PRODUCT_ID = 0x0302 # Joystick.
PRODUCT_ID_JOYSTICK = 0x0302 # Joystick.
PRODUCT_ID_ROUTER   = 0x0301 # Router
PRODUCT_ID_STATION = 0x0304
PRODUCT_ID_LAP_NEW_CAMERA = 0x2005
PRODUCT_ID_LAP_OLD_CAMERA = 0x3005

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
  0x2005: "BOARD_TYPE: PRODUCT_ID_LAP_NEW_CAMERA",  #board type is enforced in FW (TI: descriptors.h) or (STM32: App/usbd_desc.c)
  0x3005: "BOARD_TYPE: PRODUCT_ID_LAP_OLD_CAMERA",  #board type is enforced in FW (descriptors.h)
  0x1965: "yosi"
}

print_every = 0
SERIAL_NUMBER = "_"
READ_SIZE = 64 # The size of the packet
READ_TIMEOUT = 2 # 2ms
WRITE_DATA = bytes.fromhex("3f3ebb00b127ff00ff00ff00ffffffff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")
# start streaming command for station 0x303:
WRITE_DATA_CMD_START_0x304 = bytes.fromhex("3f048d00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")
WRITE_DATA_CMD_GET_FW_VERSION = bytes.fromhex("3f040600000100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")
WRITE_DATA_CMD_B = bytes.fromhex("3f04aa00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")
WRITE_DATA_CMD_G = 0
PRINT_TIME = 1.0 # Print every 1 second

special_cmd = 0
prev_pwm = 0
hr_slider = 0
pulse_amp = 4
def show_hr_values():
    global hr_slider  # this is a widget
    return int(hr_slider.get())


slider_queue = queue.Queue()

def build_WRITE_DATA_CMD(pulse_amp, hr_value):
    global WRITE_DATA_CMD_G
    global special_cmd
    WRITE_DATA_CMD___bytearray = bytearray(b'\x3f')  # initialization of the command
    print("hr_value=  ",int(hr_value))
    WRITE_DATA_CMD___bytearray.append(6)    # this is yat value in wireshark!
    WRITE_DATA_CMD___bytearray.append(0x9D) # command opcode.
    WRITE_DATA_CMD___bytearray.append(2)    # command with 2 parameters.
    WRITE_DATA_CMD___bytearray.append(0)
    WRITE_DATA_CMD___bytearray.append(0)
    # add the amplitude // TBD to put the relevant gui value 
    WRITE_DATA_CMD___bytearray.append(pulse_amp) # temporary use fix 4 
    # add the heart rate:
    WRITE_DATA_CMD___bytearray.append(int(hr_value))
    # WRITE_DATA_CMD___bytearray.append(0x3d) # test with 61
    for i in range(63-6):
        WRITE_DATA_CMD___bytearray.append(0)
    # print("WRITE_DATA_CMD___bytearray = %s " % WRITE_DATA_CMD___bytearray)
    WRITE_DATA_CMD_G = bytes(WRITE_DATA_CMD___bytearray)
    # print("WRITE_DATA_CMD_G = %s " % WRITE_DATA_CMD_G)
    print("command data: %s" % hexlify(WRITE_DATA_CMD_G))
    special_cmd = 'G'
    

def on_slider_release(event):
    value = int(hr_slider.get())
    slider_queue.put(value)
    build_WRITE_DATA_CMD(pulse_amp,value)


# def main_loop(device):
def gui_loop(device):
    do_print = True
    print_time = 0.0
    current_time = timer()
    handle_time = timer()
    write_time_capture = timer()
    skip_write = 0
    prev_counter = 0
    global special_cmd
    global WRITE_DATA
    
    while True:
        # Reset the counter
        if (do_print):
            print_time = timer()

        # Write to the device 
        if special_cmd == 'I':
            WRITE_DATA = WRITE_DATA_CMD_START_0x304
            device.write(WRITE_DATA)
            print("special_cmd Start")
            special_cmd = 0
        elif special_cmd == 'A':
            # if PRODUCT_ID == PRODUCT_ID_LAP_NEW_CAMERA:
            if PRODUCT_ID in PRODUCT_ID_types:
                WRITE_DATA = WRITE_DATA_CMD_GET_FW_VERSION
                print("special_cmd A -> WRITE_DATA_CMD_GET_FW_VERSION")
                device.write(WRITE_DATA)
            special_cmd = 0
        elif special_cmd == 'B':
           WRITE_DATA = WRITE_DATA_CMD_B
           device.write(WRITE_DATA)
           print("special_cmd B -> set_BSL_mode  --- this will stop HID communication with this GUI")
           special_cmd = 0
        elif special_cmd == 'G':
            print("------------ special_cmd heart_pulse ------------")
            WRITE_DATA = WRITE_DATA_CMD_G 
            device.write(WRITE_DATA)
            special_cmd = 0
#        else:
#            WRITE_DATA = DEFAULT_WRITE_DATA
        
        if WRITE_DATA == WRITE_DATA_CMD_B:
            break

        cycle_time = timer() - current_time
        # print("cycle timer: %.10f" % cycle_time)

        # If not enough time has passed, sleep for SLEEP_AMOUNT seconds
        # sleep_time = SLEEP_AMOUNT - (cycle_time)

        # Measure the time
        current_time = timer()

        # Read the packet from the device
        value = device.read(READ_SIZE, timeout=READ_TIMEOUT)

        # Update the GUI
        if len(value) >= READ_SIZE:
            # counter = (int(value[COUNTER_INDEX + 1]) << 8) + int(value[COUNTER_INDEX])
            # count_dif = counter - prev_counter 
            handler(value, do_print=do_print)
            # print("Received data: %s" % hexlify(value))
            Handler_Called = (timer() - handle_time)
            
            if Handler_Called > 0.002 :
            # if Handler_Called > 0.02 :
                #print("handler called: %.6f" % Handler_Called)
                global print_every
                print_every = print_every + 1
                if print_every >= 500:
                    print_every = 0
                    print("current_time:", current_time, end="")
                    print("  Received data: %s" % hexlify(value))
            # print("current_time: %.6f" % current_time)
            handle_time = timer() 
            # prev_counter = counter

        # Update the do_print flag
        do_print = (timer() - print_time) >= PRINT_TIME

        # Process slider queue
        try:
            slider_value = slider_queue.get_nowait()
            print(f"HR Slider value: {slider_value}")
        except queue.Empty:
            pass

        # 2025_02_13__21_33
        if do_print:
            # all things I want to have once a second
            # print(print_time)
            hr_slider_value = show_hr_values()
            if (hr_slider_value != gui_loop.prev_hr_slider_value):
                print(show_hr_values())
            gui_loop.prev_hr_slider_value = hr_slider_value

        # Add a small delay to prevent high CPU usage
        sleep(0.1)  #on 2025_02_14 I get that:  AttributeError: 'float' object has no attribute 'sleep' 
gui_loop.prev_hr_slider_value = 60            

def hid_read( device ):
    global stream_data
    always_counter = 0
    hid_read.prev_time = datetime.now()
    while True:
        # Read the packet from the device
        always_counter += 1
        value = device.read(READ_SIZE, timeout=READ_TIMEOUT)
        if len(value) >= READ_SIZE:
            stream_data = value
hid_read.prev_time = 0                

def date2dec(x):
    s = "%02x" % x
    return s

def handler(value, do_print=False):
    if do_print:
        print("Received data: %s" % hexlify(value))

    # parsing FW version response :
    if value[2] == 6 and value[3] == 6 and value[4] == 0 and value[5] == 1:
        print("FW friendly version: %s" % hexlify(value))
        #   0 1 2 3 4 5   6 7 8 9 0 1    2 3 4 5 6 7 8 9 0 
        # b'3f0a06060001  030004060321   d6bb2c3fc2b49c3fe877fecef602fffe5787dedfcf750cfb129efe7ffd7ed60daedefca4f9fff58efc5eb47c237eb5a93dd72f55'
        print("")
        print("FW version: "+str(value[6])+"." +str(value[7])+"." +str(value[8]))
        print("FW date   : "+date2dec(value[9])+"/" +date2dec(value[10])+"/20" +date2dec(value[11]))

        print(" ")
        print(" Please press <Enter> to Exit")

    return # do without gui
    
def my_seperator(frame, row):
    ttk.Separator(frame, orient=tk.HORIZONTAL).grid(pady=10, row=row, columnspan=4, sticky=(tk.W + tk.E))
    return row + 1
    
def my_widgets(frame):
    global hr_slider  # this is a widget
    bold_font = ("TkDefaultFont", 9, "bold")
    row = 0
    # row += 1

    # Seperator
    row = my_seperator(frame, row)

    # Outer Handle
    ttk.Label(frame,text="HID Streaming Values").grid(row=row,sticky=tk.W)
    global Last_Stream_Packet_Time
    global date_time_text
    date_time_text = "Last stream packet time:  "
    Last_Stream_Packet_Time = ttk.Label(frame,text = date_time_text,font=bold_font, foreground="#000077")
    Last_Stream_Packet_Time.grid(row=row,column=1,sticky=tk.W,)
    global device_SN_label
    global SERIAL_NUMBER
    serial_number_text = "Serial Number: " + SERIAL_NUMBER
    # device_SN_label = ttk.Label(frame,text="Serial Number: ", foreground="#0000FF")
    device_SN_label = ttk.Label(frame,text = serial_number_text, foreground="#0000FF")
    device_SN_label.grid(row=row,column=2,sticky=tk.W,)
    
    # Add HR slider // from perplexity 
    row += 1
    ttk.Label(frame, text="Heart Rate (BPM):").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
    hr_slider = ttk.Scale(frame, from_=20, to=120, orient=tk.HORIZONTAL, length=200)
    hr_slider.grid(row=row, column=1, columnspan=2, sticky=tk.W+tk.E, padx=5, pady=5)
    hr_slider.set(60)  # Set default value to 60 BPM

    # Add label to display current HR value
    hr_value_label = ttk.Label(frame, text="60")
    hr_value_label.grid(row=row, column=3, sticky=tk.W, padx=5, pady=5)

    # Update label when slider value changes
    def update_hr_label(value):
        hr_value_label.config(text=f"{int(float(value))}")

    hr_slider.config(command=update_hr_label)

    # Bind the slider release event
    hr_slider.bind("<ButtonRelease-1>", on_slider_release)    

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
                        VENDOR_ID = 0x24b3 # Simb
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
                        print("wrong ID2")
                    
            if device is None:
                print("no device attached")
            else:
                print("VENDOR_ID = %X" % VENDOR_ID)
                print("PRODUCT_ID = %X" % PRODUCT_ID)
                if PRODUCT_ID in PRODUCT_ID_types:
                    print(PRODUCT_ID_types[PRODUCT_ID])
                    global special_cmd
                    # if PRODUCT_ID == PRODUCT_ID_LAP_NEW_CAMERA:
                    if PRODUCT_ID in PRODUCT_ID_types:
                        # special_cmd = 'A'
                        # print("set in init: special_cmd = 'A'")
                        pass 
        elif (path_mode):
            device = hid.Device(path=PATH)
        else:
            raise NotImplementedError

        # Initialize the main window
        global root
        global util_verstion
        root = tk.Tk()
        util_title = "SIMBionix HR_Util"+" (version:"+util_verstion+")"
        # root.title("SIMBionix HID_Util")
        root.title(util_title)

        # Initialize the GUI widgets
        my_widgets(root)

        # Create thread that calls
        threading.Thread(target=gui_loop, args=(device,), daemon=True).start()
        threading.Thread(target=hid_read, args=(device,), daemon=True).start()

        # Run the GUI main loop
        root.mainloop()

        # threading.Thread(target=main_loop, args=(device,), daemon=True).start()
        # global WRITE_DATA
        # if WRITE_DATA == WRITE_DATA_CMD_B:
            # print("WRITE_DATA == WRITE_DATA_CMD_B")
        # print(" ")
        # input()

    finally:
#        global file1
#        file1.close() #to change file access modes 
        if device != None:
            device.close()

if __name__ == "__main__":
    main()

# development helper:
# the HID sending command to embedded it done by 
# command for HeartPulse(4,120 ) with No replay from device:
#   9D 02 00 00 04 78
# WRITE_DATA_CMD_Heart_Pulse = bytes.fromhex("3f048d00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")
# WRITE_DATA_CMD_Heart_Pulse = bytes.fromhex("3f069d02000004780000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")

'''



'''
