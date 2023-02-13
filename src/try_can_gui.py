# //C:\Work\Python\HID_Util\src\try_can_gui.py

import can
import tkinter as tk
from tkinter import ttk

# create a CAN bus instance with a bitrate of 1M
bus = can.interface.Bus(bustype='ixxat', channel=0, bitrate=1000000)
# define a CAN message filter to receive messages with ID 0x103 and 0x104
can_filter = [{"can_id": 0x103, "can_mask": 0x7FF}, {"can_id": 0x104, "can_mask": 0x7FF}]

# create a tkinter window
root = tk.Tk()
root.title("CAN Bus Progress Bars")
root.geometry("400x200")

# create two horizontal progress bars
pb1 = ttk.Progressbar(root, orient='horizontal', length=200, mode='determinate')
pb1.pack(pady=20)
pb2 = ttk.Progressbar(root, orient='horizontal', length=200, mode='determinate')
pb2.pack(pady=20)

# update the progress bars based on received CAN messages
message_count = 0
while True:
    # receive a message from the bus
    msg = bus.recv()
    # if a message is received
    if msg is not None:
#        try:
#            data_str = msg.data.decode('utf-8')
#        except UnicodeDecodeError:
#            data_str = msg.data.decode('utf-8', 'ignore')  # ignore non-decodable bytes
            # or data_str = msg.data.decode('utf-8', 'replace')  # replace non-decodable bytes with a placeholder
        # if the message ID is 0x103
        if msg.arbitration_id == 0x103:
            # if message count is divisible by 100, update the progress bars
            if message_count % 100 == 0:
                # convert the first 2 bytes of the message data to an integer
                data_int_1 = int.from_bytes(msg.data[:2], byteorder='little', signed=False)
                # convert the next 3 bytes of the message data to an integer
                data_int_2 = int.from_bytes(msg.data[2:5], byteorder='little', signed=False)
                
                # print: the: message: data-and-the- first: 3- bytes: as:an: integer: and: the: next: 3:bytes
                print("Received-message:with ID @x103 and data:",msg.data,"First-3-bytes-as-int:",data_int_1,-"Next-3-bytes:as:-int:",data_int_2}
                
                # update the progress bars
                pb1['value'] = min(data_int_1, 5000)
                pb2['value'] = min(data_int_2, 5000)
                root.update()
            # increment the message count
            message_count += 1
        # if the message ID is 0x104, print "start streaming"
        elif msg.arbitration_id == 0x104:
            print("Received message with ID 0x104: start streaming")
        # if the message data contains the string "quit", break out of the loop
        # if "quit" in data_str:
        if "quit" in msg.data.decode('utf-8', 'ignore'):
            break

# close the tkinter window
root.destroy()

# 2023_02_13__13_33
# debug:
# AttributeError: module 'tkinter' has no attribute 'ttk'
