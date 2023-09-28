#!/usr/bin/python3
# C:\Work\Python\HID_Util\src\HID_recorder.py

# file history:
# 2022_07_06__01_39 - adding plotting by using matplotlib 
# 2022_06_30__19_12 - adding special calculation for Torque and Insertion
# 2023_02_03__15_46 - print the version of this file 
# 2023_02_21__00_30 - added uint_16_unsigned_to_int_signed()
# last modified at: Friday, ‎March ‎12, ‎2021, ‏‎06:16:05 PM

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

import os
from string_date_time import get_date_time
import csv
import time
import matplotlib.pyplot as plt

recorder_version = "2023_03_13.a"
print("This Recorder Version: ",recorder_version)

# for debugging the slippage issue:
use_delta_instead_of_tool_size = 1

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
# USB\VID_2047&PID_0302&REV_0200
VENDOR_ID = 0x2047 # Texas Instruments
PRODUCT_ID = 0x0302 # Joystick.
PRODUCT_ID_JOYSTICK = 0x0302 # Joystick.
PRODUCT_ID_ROUTER   = 0x0301 # Router
PRODUCT_ID_STATION = 0x0304
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
  0x2005: "BOARD_TYPE: PRODUCT_ID_LAP_NEW_CAMERA",  #board type is enforced in FW (descriptors.h)
  0x1965: "yosi"
}

# FILE1_PATH = "log\hid_log.csv"
FILE1_PATH = "log\hid_" # log.csv"
start_date_time = get_date_time()
FIGURE_FILE1_PATH = FILE1_PATH + start_date_time + ".png"
FILE1_PATH = FILE1_PATH + start_date_time + ".csv"
display_text = ""

print("Recording result at: ", FILE1_PATH, "\n")
if not os.path.exists('log'):
    os.makedirs('log')
# file1 = None
# open recording log file:
file1 = open(FILE1_PATH,"w") 
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
IMAGE_QUALITY_INDEX = TORQUE_INDEX + 4

# global variables
special_cmd = 0
my_thread_run = True
my_thread_ended = False
max_insertion = 0
insertion = 0
start_insertion = 0

def gui_loop(device):
    do_print = True
    print_time = 0.0
    time = timer()
    handle_time = timer()
    write_time_capture = timer()
    skip_write = 0
    prev_counter = 0
    send_stream_request_command_once = 1
    do_once = 1
    # cnt = None
    # prev_cnt = None
    # value = None
    global special_cmd
    global max_insertion
    global insertion
    global start_insertion
    # global print_flag
    
    while my_thread_run:
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


        cycle_time = timer() - time
        # print("cycle timer: %.10f" % cycle_time)

        # If not enough time has passed, sleep for SLEEP_AMOUNT seconds
        sleep_time = SLEEP_AMOUNT - (cycle_time)

        # Measure the time
        time = timer()
        # print(" ")

        # Read the packet from the device
        value = device.read(READ_SIZE, timeout=READ_TIMEOUT)

        # Update the GUI
        if len(value) >= READ_SIZE:
            # save into file:
            #INSERTION_INDEX
            tool_size = (int(value[CMOS_INDEX + 1]) << 8) + int(value[CMOS_INDEX])
            tool_size = uint_16_unsigned_to_int_signed(tool_size)
# Received data: b'3f26 00 00 00 00 0674fc41 3f4efc70 0033a4513c5a0101210001000000650000000000000000000000167f070dd7aee89baff63fedcfcccb763acf041b00000010'
#                                   TORQUE   INSERTION
            # 0674 fc41
# -62847372 = FC41 0674
#   torque from Avago: bytes 6..9
            torque = (int(value[TORQUE_INDEX + 2]) << 24) + (int(value[TORQUE_INDEX+3]) <<16) + (int(value[TORQUE_INDEX]) <<8) + int(value[TORQUE_INDEX+1])  
            insertion = (int(value[INSERTION_INDEX + 2]) << 24) + (int(value[INSERTION_INDEX+3]) <<16) + (int(value[INSERTION_INDEX]) <<8) + int(value[INSERTION_INDEX+1])  
            station_current = (int(value[STATION_CURRENT_INDEX + 1]) << 8) + int(value[STATION_CURRENT_INDEX]) #station Report.current
            #global MAX_LONG_POSITIVE
            torque = long_unsigned_to_long_signed(torque)
            insertion = long_unsigned_to_long_signed(insertion)
            image_quality = (int(value[IMAGE_QUALITY_INDEX]) )
            analog = [(int(value[i + 1]) << 8) + int(value[i]) for i in LAP_ANALOG_INDEX_LIST]
            channel_0 = analog[0]
            channel_1 = analog[1]
            channel_2 = analog[2]
            channel_3 = analog[3]
            channel_4 = analog[4]
            counter = (int(value[COUNTER_INDEX + 1]) << 8) + int(value[COUNTER_INDEX])
            count_dif = counter - prev_counter 
            global file1
            #if count_dif > 1 :
            #    L = [ str(counter),",   ", str(clicker_analog), ", " , str(count_dif), " <<<<<--- " ,"\n" ]  
            #else:
            #    L = [ str(counter),",   ", str(clicker_analog), ", " , str(count_dif), "\n" ]  
            # L = [ str(channel_0),",   ", str(channel_1), ", " , str(channel_2),", " , str(channel_3),", " , str(channel_4), "\n" ]  

            ### recording ::  tool_size, insertion and  torque ###
            # L = [ str(tool_size),",   ", str(insertion), ", " , str(torque), "\n" ]  

            # save the max_insertion for % calculating later.
            if( abs(insertion) > abs(max_insertion) ):
                max_insertion = insertion
            if(do_once):  # do only once, for the first streaming value
                start_insertion = insertion
                do_once = 0
            ### recording ::  tool_size, insertion, torque and  image_quality ###
            L = [ str(tool_size),",   ", str(insertion), ", " , str(torque), ", " , str(image_quality), "\n" ]  
            file1.writelines(L) 
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
                    print("insertion: ", insertion, end="")
                    print(" ;     torque: ", torque)
                    
            # print("time: %.6f" % time)
            handle_time = timer() 
            prev_counter = counter

        # Update the do_print flag
        do_print = (timer() - print_time) >= PRINT_TIME
    global my_thread_ended
    my_thread_ended = True

def long_unsigned_to_long_signed( x ):
    if x > MAX_LONG_POSITIVE:
        x = x - MAX_UNSIGNED_LONG
    return x

def uint_16_unsigned_to_int_signed( x ):
    if x > MAX_U16_POSITIVE:
        x = x - MAX_U16
    return x

def date2dec(x):
    s = "%02x" % x
    return s
def handler(value, do_print=False):
    if do_print:
        print("Received data: %s" % hexlify(value))
    return # do without gui


PROGRESS_BAR_LEN = 300
LONG_PROGRESS_BAR_LEN = 590

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
    parser.add_argument(
        "-l", "--label",
        dest="label",
        metavar="LABEL",
        type=int,
        nargs=1,
        required=False,
        help="add first line of Label in the CSV file"
    )
    return parser

def main():
    global VENDOR_ID
    global PRODUCT_ID
    global file1
    global insertion
    global max_insertion    
    PATH = None
    
    # open recording log file:
    # file1 = open("C:\Work\Python\HID_Util\src\log\log2.txt","w") 

    # Parse the command line arguments
    parser = init_parser()
    args = parser.parse_args(sys.argv[1:])

    # Initialize the flags according from the command line arguments
    avail_vid = args.vendor_id != None   # "avail" for "available" 
    avail_pid = args.product_id != None
    avail_path = args.path != None
    avail_label = args.label != None
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
    if ( avail_label ):
        LABEL = args.label[0]
        print("-----------  avail_label - ----------")
        if LABEL > 0 :
            L = [ "tool_size",",   ", "insertion", ", " , "torque", "\n" ]  
            print(L)
            file1.writelines(L) 

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
                        # print("VID = %X PID = %X " % VENDOR_ID, PRODUCT_ID)
                        print("try with PID = %X " % PRODUCT_ID)
                        # print("PRODUCT_ID = %X" % PRODUCT_ID)
                        device = hid.Device(vid=VENDOR_ID, pid=PRODUCT_ID)
                        # device = hid.Device(vid=0x24B3, pid=0x2005)
                        # print("success vid=0x24B3, pid=0x2005 !!")
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
                    if PRODUCT_ID == PRODUCT_ID_LAP_NEW_CAMERA:
                        special_cmd = 'I'

            

        elif (path_mode):
            device = hid.Device(path=PATH)
        else:
            raise NotImplementedError


        print(" ")
        print(" --------------------------------------")
        print(" Please press <Enter> to stop recording")
        print(" --------------------------------------")
        print(" ")
        # Create thread that calls
        # threading.Thread(target=gui_loop, args=(device,), daemon=True).start()
        myThread = threading.Thread(target=gui_loop, args=(device,), daemon=True)
        myThread.start()
        input()
        print("Recording start: ", start_date_time)
        print("Recording end  : ", get_date_time())
        global insertion
        global max_insertion
        global start_insertion
        # print("start_insertion: ", start_insertion)
        # print("max_insertion: ", max_insertion,"   | Last insertion: ", insertion,"   | error (%): ", int(insertion/max_insertion*100),"%" )
        motion_error = abs(insertion-start_insertion)/max_insertion*100
        # print("max_insertion: %d   | Last insertion: %d    | error :%2.1f %%" % (max_insertion,insertion, motion_error))
        display_text = ("Max_insertion: %d   | Start_insertion: %d   | Last insertion: %d    | error :%2.1f %%" % ( max_insertion,start_insertion, insertion, motion_error))
        print(display_text)
        print("\n","Recording result at: ", FILE1_PATH)
        # try:
        #     with open(FILE1_PATH, 'r') as csvfile:
        #         plots = csv.reader(csvfile, delimiter=',')
        #     y1 = []
        #     y2 = []
        #     for row in plots:
        #         y1.append(int(row[1]))
        #         y2.append(int(row[2]))
        #     print(y1[0:20])
        #     print("vector y1[0:20]  : ", y1[0:20])
        #     print("\n", "CSV FILE FILE1_PATH IS: ", FILE1_PATH)
        # except:
        #     print("--------------error: row in plots")

    finally:
        #global file1
        global my_thread_run
        my_thread_run =  False
        while (not my_thread_ended):
            pass
        file1.close() #to change file access modes
        file1 = open(FILE1_PATH,"r+")
        plots = csv.reader(file1, delimiter=',')
        y0 = []
        y1 = []
        y2 = []
        y3 = []
        for row in plots:
            y0.append(int(row[0]))
            y1.append(int(row[1]))
            y2.append(int(row[2]))
            y3.append(int(row[3]))
        # WinMove, ,,367,144,1358,598
        # resize the figure to w: 1358	h: 598
        my_dpi = 96 # by calculating width resolution / screen size = 2560/31.25' = 81.9
        # plt.figure(figsize=(1358/my_dpi, 598/my_dpi), dpi=my_dpi)
        height_fix =  598/671 # from measuring the actual results.
        plt.figure(figsize=(13.58, 5.98*height_fix), dpi=100)
        #print(y0[0:200])
        if( use_delta_instead_of_tool_size):
            plt.plot(y0,label="Delta_insertion")
        else:
            plt.plot(y0,label="tool_size")
        plt.plot(y1,label="insertion")
        #plt.plot(y1,marker='o',label="insertion")
        plt.plot(y2,label="torque")
        plt.plot(y3,label="image_quality")  # 2023_03_09 added.
        # plt.xlabel('Time')
        display_f_name = FILE1_PATH.split('\\')
        display_f_n = display_f_name[len(display_f_name)-1]
        # text = 'Time...' + "\n" + display_f_n
        if display_text == "":
            text = 'Time...' + "\n" + "no streaming was captured"
        else:
            text = 'Time...' + "\n" + display_text
        # text = 'Time...' + "\n" + FILE1_PATH
        plt.xlabel(text)
        plt.ylabel('Value')
        # plt.title('tool_size, insertion and  torque"')
        plt.title(display_f_n,fontsize=10, fontweight="ultralight")    
        # text = 'tool_size, insertion, torque and image_quality' + "\n" + file_name
        # plt.title('tool_size, insertion, torque and image_quality "', fontweight="bold")
        if( use_delta_instead_of_tool_size):
            plt.suptitle('Delta-insertion, insertion, torque and image_quality', fontsize=16, fontweight="bold")
        else:
            plt.suptitle('tool_size, insertion, torque and image_quality', fontsize=16, fontweight="bold")
        plt.legend()
        plt.grid() # 2023_02_20 added.
        
        # Save plot to disk to subfolder log
        # Create 'log' subfolder if it doesn't exist
        if not os.path.exists('log'):
            os.makedirs('log')
        # plt.savefig("log/figure.png", bbox_inches='tight', dpi=150)
        # plt.savefig(FIGURE_FILE1_PATH, bbox_inches='tight', dpi=150)
        plt.savefig(FIGURE_FILE1_PATH, bbox_inches='tight')
        

        plt.show() 
        if device != None:
            device.close()
        # time.sleep(2.5)
        print("--------- AFTER: device.close()--------------")

        # try:
        #     with open(FILE1_PATH, 'r') as csvfile:
        #         plots = csv.reader(csvfile, delimiter=',')
        #     y1 = []
        #     y2 = []
        #     for row in plots:
        #         y1.append(int(row[1]))
        #         y2.append(int(row[2]))
        #     print(y1[0:20])
        #     print("vector y1[0:20]  : ", y1[0:20])
        #     print("\n", "CSV FILE FILE1_PATH IS: ", FILE1_PATH)
        # except:
        #     print("--------------error: row in plots")

if __name__ == "__main__":
    main()

'''
history changes
2023_03_09 
- adding image_quality to recording. 
- resize the figure to w: 1358	h: 598
- adding csv file name to title 
- to save the plot file with the full date&time name at \log\
2023_03_17
- change the dpi of autoSave plot to same as the figure
- add to the recorder auto calculate of the error in %
- display extra information on the graph (Max_insertion, motion_error, etc.)
- change the label to : Delta-insertion
'''        