# C:\Work\Python\HID_Util\src\CAN_send_string.py

import can
import sys

if len(sys.argv) < 2:
    input_str = input("Enter the string to send: ")
    data = [ord(c) for c in input_str]  # Convert string to a list of ASCII codes
else:    
    # Extract the string argument from the command line
    arg_str = sys.argv[1]
    # Convert the string to a list of ASCII codes
    data = [ord(c) for c in arg_str]
    input_str = arg_str




if input_str=="Start" or input_str=="1":
    print("you entered Start:  ", data)
    message = can.Message(arbitration_id=0x104, data=[0x01] + data, is_extended_id=False)
    Prefix_data = data=[0x01] + data
else:    
    print("you entered:", data)
    message = can.Message(arbitration_id=0x104, data=[0x00] + data, is_extended_id=False)
    Prefix_data = data=[0x00] + data
# print("message= ",  data=[0x00] + data)
print("message= ",  Prefix_data)

bus = can.interface.Bus(bustype='ixxat', channel='0', bitrate=1000000)
# message = can.Message(arbitration_id=0x304, data=[0x50,0x79,0x74,0x68,0x6F,0x6E], is_extended_id=False)
# message = can.Message(arbitration_id=0x104, data=[0x00,0x54,0x74,0x6F,0x07], is_extended_id=False) # "stop"
bus.send(message)
