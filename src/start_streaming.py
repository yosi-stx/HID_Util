#!/usr/bin/python3
# C:\Work\Python\HID_Util\src\grt_FW_version.py
# based on bsl.py

from binascii import hexlify
import sys
import argparse
import threading
from time import perf_counter as timer

# NOTE:             about include_dll_path for  __init__.py error.
# You MUST include the next line when working with full project path structure
import include_dll_path
import hid
import os
import keyboard

# VENDOR_ID = 0x24b3 # Simb
# PRODUCT_ID = 0x1005 # Simb MSP430 Controller
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
# VENDOR_ID = 0x24b3 # Simb
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

FILE1_PATH = "log\hid_log.csv"
# if not os.path.exists('log'):
#     os.makedirs('log')
# # file1 = None
# # open recording log file:
# # file1 = open("C:\Work\Python\HID_Util\src\log\log.csv","w") 
# # file1 = open(FILE1_PATH,"w") 
# file1 = open("log\get_FW_version_2021_03_11__00_42.csv","w") 

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

#.........................................................##........................................
WRITE_DATA_CMD_S = bytes.fromhex("3f3ebb00b127ff00ff00ff0053ff33ff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")
# 'A' - keep Alive + fast BLE update (every 20 msec)
WRITE_DATA_CMD_A = bytes.fromhex("3f3ebb00b127ff00ff00ff0041ff33ff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")
WRITE_DATA_CMD_GET_FW_VERSION = bytes.fromhex("3f040600000100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")
WRITE_DATA_CMD_START_STREAMING_GBU = bytes.fromhex("3f048200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")
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
# print("ANALOG_INDEX_LIST=",ANALOG_INDEX_LIST)
# ANALOG_INDEX_LIST= [8, 10, 12, 14, 16, 18, 20, 22]
LAP_ANALOG_INDEX_LIST = list(range(2,8 * 2 + 1, 2)) 

COUNTER_INDEX = 2 + 22 + 18 # Ignore the first two bytes, then skip XData1 (22 bytes) and OverSample (==XDataSlave1; 18 bytes)
CMOS_INDEX = 2 + 2   # maybe + 4???
#                       0  1  2  3  4 5 6 7  8 9 1011
# Received data: b'3f26 00 00 00 00 0674fc41 3f4efc70 0033a4513c5a0101210001000000650000000000000000000000167f070dd7aee89baff63fedcfcccb763acf041b00000010'
#                                   TORQUE   INSERTION

# global variables
special_cmd = 0

root = None

def main_loop(device):
    do_print = True
    print_time = 0.0
    time = timer()
    handle_time = timer()
    write_time_capture = timer()
    skip_write = 0
    prev_counter = 0
    send_stream_request_command_once = 1
    global special_cmd
    global WRITE_DATA
    
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
        elif special_cmd == 'A':
            # if PRODUCT_ID == PRODUCT_ID_LAP_NEW_CAMERA:
            if PRODUCT_ID in PRODUCT_ID_types:
                # WRITE_DATA = WRITE_DATA_CMD_GET_FW_VERSION
                if PRODUCT_ID == PRODUCT_ID_STATION:
                    WRITE_DATA = WRITE_DATA_CMD_START_0x304
                    print("special_cmd Start streaming 0x8D")
                else:
                    WRITE_DATA = WRITE_DATA_CMD_START_STREAMING_GBU
                    print("special_cmd A -> WRITE_DATA_CMD_START_STREAMING_GBU 0x82")
                device.write(WRITE_DATA)
            else:
                WRITE_DATA = WRITE_DATA_CMD_A
                print("special_cmd A -> keep Alive + fast BLE update (every 20 msec)")
            special_cmd = 0
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
        
        if WRITE_DATA == WRITE_DATA_CMD_B:
            break

        if WRITE_DATA == WRITE_DATA_CMD_START_STREAMING_GBU:
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
            #global file1
            #if count_dif > 1 :
            #    L = [ str(counter),",   ", str(clicker_analog), ", " , str(count_dif), " <<<<<--- " ,"\n" ]  
            #else:
            #    L = [ str(counter),",   ", str(clicker_analog), ", " , str(count_dif), "\n" ]  
            L = [ str(channel_0),",   ", str(channel_1), ", " , str(channel_2),", " , str(channel_3),", " , str(channel_4), "\n" ]  
            #file1.writelines(L) 
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
                    print("time:", time, end="")
                    print("  Received data: %s" % hexlify(value))
            # print("time: %.6f" % time)
            handle_time = timer() 
            prev_counter = counter

        # Update the do_print flag
        do_print = (timer() - print_time) >= PRINT_TIME

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
                        special_cmd = 'A'
                        print("set in init: special_cmd = 'A'")
        elif (path_mode):
            device = hid.Device(path=PATH)
        else:
            raise NotImplementedError


        # Create thread that calls
        threading.Thread(target=main_loop, args=(device,), daemon=True).start()
        global WRITE_DATA
        if WRITE_DATA == WRITE_DATA_CMD_B:
            print("WRITE_DATA == WRITE_DATA_CMD_B")
        # print(" Recording Ended !!!")
        print(" ")
        # print(" Please press <Enter> to Exit")
        keyboard.read_key() # wait for any key to be pressed on the keyboard.
        # input()

    finally:
#        global file1
#        file1.close() #to change file access modes 
        if device != None:
            device.close()

if __name__ == "__main__":
    main()