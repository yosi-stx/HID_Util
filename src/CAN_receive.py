# C:\Work\Python\HID_Util\src\CAN_receive.py
import can
import sys
import time  # for use with : time.sleep(0.1) # 100ms sleep
import threading  #2023_04_05__23_42
import tkinter as tk
from tkinter import simpledialog

# create a CAN bus instance
bus = can.interface.Bus(bustype='ixxat', channel=0, bitrate=1000000)

# define a CAN message filter to receive messages with ID 0x103
# can_filter = can.Filter(
    # can_id=0x103,  # filter on ID 0x103
    # can_mask=0x7FF,  # match all bits in the mask
    # extended=False,  # standard frame (not extended)
# )

# define a CAN message filter to receive messages with ID 0x103
# can_filter = can.Filter.from_can_id(0x103, mask=0x7FF)

# define a CAN message filter to receive messages with ID 0x103
can_filter = [{"can_id": 0x103, "can_mask": 0x7FF}]


# start the CAN bus
# bus.start()

def my_simple_cmd():
    # create the root window
    root = tk.Tk()
    # hide the root window
    root.withdraw()
    while True:
        # create a dialog box to prompt the user for input
        cmd = simpledialog.askstring("Command", " Enter command\n \"exit\" or \"q\" to quit...\n i - for more commands")
        print(cmd)
        # print the user's cmd to the console
        if cmd == None:
            cmd = "esc"
            print("Command: " + cmd + "!")
            cmd = simpledialog.askstring("Command", "OK to continue, Cancel to exit")
            if cmd == None:
                sys.exit()
            else:
                cmd = "OK"
        print("Command: " + cmd + "!")
        if cmd == "exit" or cmd == "q" :
            print("Exit the cmd window")
            sys.exit()
            
        data = [ord(c) for c in cmd]
        if cmd=="Start" or cmd=="1":
            print("you entered Start:  ", data)
            message = can.Message(arbitration_id=0x104, data=[0x01] + data, is_extended_id=False)
            Prefix_data = data=[0x01] + data
        else:    
            print("you entered:", data)
            message = can.Message(arbitration_id=0x104, data=[0x00] + data, is_extended_id=False)
            Prefix_data = data=[0x00] + data
        print("message= ",  Prefix_data)
        bus = can.interface.Bus(bustype='ixxat', channel='0', bitrate=1000000)
        bus.send(message)

def Read_Messages():
    # read messages from the bus
    skips = 0 
    while True:
        msg = bus.recv()
        if msg is not None and msg.arbitration_id == 0x103:
            skips += 1 
            if (skips%800) == 0:
                print("Received message with data:", msg.data)
                if msg.data == 'quit':
                    break
                if msg.data == b'quit':
                    break
        
def my_function():
    a = 0
    while True:
        # a = input("press Enter")
        # print(a,end=" ")
        print(a)
        time.sleep(1)
        a += 1
        # print(a)
        # break
        pass

# threading.Thread(target=my_function, daemon=True).start()

# Read_Messages()
threading.Thread(target=Read_Messages, daemon=True).start()


threading.Thread(target=my_simple_cmd, daemon=True).start()
# # show the root window again (optional)
# root.deiconify()
# # run the event loop
# root.mainloop()

input()
    
print("Exit from CAN_receive")


#-------------------  EXIT -------------------#
sys.exit()
#---------------------------------------------#

# stop the CAN bus when done
# bus.stop()


'''

In this example, we first create a CAN bus instance using the can.interface.Bus constructor,
specifying the bustype as 'ixxat' and the channel as 0. We also set the bitrate to 500000 bits per
second, but you can change this to match your specific device and network configuration.
Next, we define a CAN message filter using the can.Filter constructor to receive only messages with ID
0x103. We set the can_mask to match all bits in the mask, which means that the filter will only match
messages with exactly the specified ID.
Then, we start the CAN bus using the bus.start method. This will initialize the device and allow us to
receive messages on the bus.
In the main loop, we use the bus.recv method to read messages from the bus. This method blocks until a
message is received. When a message is received, we check if it has the desired ID using
msg.arbitration_id. If it does, we print its data using msg.data.
Finally, we stop the CAN bus using the bus.stop method when we are done receiving messages.
'''
