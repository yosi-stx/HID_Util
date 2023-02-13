import can

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

# read messages from the bus
while True:
    msg = bus.recv()
    if msg is not None and msg.arbitration_id == 0x103:
        print("Received message with data:", msg.data)
        if msg.data == 'quit':
            break
        if msg.data == b'quit':
            break
        

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