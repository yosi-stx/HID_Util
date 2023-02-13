import can
bus = can.interface.Bus(bustype='ixxat', channel='0', bitrate=1000000)
message = can.Message(arbitration_id=0x304, data=[0x50,0x79,0x74,0x68,0x6F,0x6E], is_extended_id=False)
bus.send(message)
