# //C:\Work\Python\HID_Util\src\try_can_gui.py

import can
import tkinter as tk
from tkinter import ttk

print("version: 2023_02_14__21_39")
# create a CAN bus instance with a bitrate of 1M
bus = can.interface.Bus(bustype='ixxat', channel=0, bitrate=1000000)
# define a CAN message filter to receive messages with ID 0x103 and 0x104
can_filter = [{"can_id": 0x103, "can_mask": 0x7FF}, {"can_id": 0x104, "can_mask": 0x7FF}]

# function to start streaming
def start_streaming():
    msg = can.Message(arbitration_id=0x104, data=[0x01], is_extended_id=False)
    bus.send(msg)

# function to stop streaming
def stop_streaming():
    msg = can.Message(arbitration_id=0x104, data=[0x00], is_extended_id=False)
    bus.send(msg)

# create a tkinter window
root = tk.Tk()
root.title("CAN Bus Progress Bars")
root.geometry("400x200")

# create two horizontal progress bars
pb1 = ttk.Progressbar(root, orient="horizontal", length=200, mode="determinate", maximum=5000)
pb1.pack(pady=20)
# pb2 = ttk.Progressbar(root, orient="horizontal", length=200, mode="determinate", maximum=99000)
# pb2.pack(pady=20)

# create "start" and "stop" buttons
# start_button = tk.Button(root, text="Start", command=start_streaming)
# start_button.pack(side="left", padx=10)
# stop_button = tk.Button(root, text="Stop", command=stop_streaming)
# stop_button.pack(side="left")

# update the progress bars based on received CAN messages
# function to update the progress bar based on received CAN messages
def update_progress_bar():
    message_count = 0
    root.update()
    while True:
        # receive a message from the bus
        msg = bus.recv()
        # if a message is received
        if msg is not None:
            # if the message ID is 0x103
            if msg.arbitration_id == 0x103:
                # if message count is divisible by 100, update the progress bar
                if message_count % 100 == 0:
                    # convert the first 2 bytes of the message data to an integer
                    data_int = int.from_bytes(msg.data[:2], byteorder='little', signed=False)
                    # update the progress bar
                    pb1['value'] = data_int
                    root.update()
                # increment the message count
                message_count += 1
            # if the message data contains the string "quit", break out of the loop
            if "quit" in msg.data.decode('utf-8', 'ignore'):
                break
        # schedule the update_progress function to be called again after 1 second
        # root.after(100, update_progress_bar)

# function to send a start message with data[0] = 0x01
def send_start():
    msg = can.Message(arbitration_id=0x104, data=[0x01])
    bus.send(msg)

# create a "start" button that calls the send_start function when pressed
start_button = ttk.Button(root, text="Start", command=send_start)
start_button.pack()
stop_button = ttk.Button(root, text="Stop", command=stop_streaming)
stop_button.pack()

# start the function to update the progress bar based on received CAN messages
update_progress_bar()

# close the tkinter window
root.destroy()

# 2023_02_13__13_33
# debug:
# AttributeError: module 'tkinter' has no attribute 'ttk'
