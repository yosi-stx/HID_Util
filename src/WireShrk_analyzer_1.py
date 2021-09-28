#!/usr/bin/env python3

import sys
import pyshark
import numpy as np
import matplotlib.pyplot as plt

# packet.usb.src -- Packet's source (host/device)
# packet.usb.dst -- Packet's destination (host/device)
# packet.usb.endpoint_address_direction -- URB INTERRUPT IN/OUT
# packet.usb.data_len -- Packet's payload length
# packet.data.usb_capdata -- Packet's payload (in this format '3f:07:03:...:00')

direction = {
    'in': '1',
    'out': '0'
}

# List of commands for the Router, with how many bytes to expect in the request/response
# (from "FLEX3 Protocol Description" 2021-07-06)
cmds = {
    # Generic commands
    0xAA: { 'request': 0, 'response': 0, 'name': 'Run BSL' },
    0x01: { 'request': 0, 'response': 1, 'name': 'Get Board Type' },
    0x02: { 'request': 2, 'response': 1, 'name': 'Get GPIO' },
    0x03: { 'request': 3, 'response': 0, 'name': 'Set GPIO' },
    0x04: { 'request': 0, 'response': 0, 'name': 'Keep-alive' },
    0x05: { 'request': 0, 'response': 4, 'name': 'Get FW version' },
    0x06: { 'request': 0, 'response': 4, 'name': 'Get FW readable version' },
    0x07: { 'request': 0, 'response': 0, 'name': 'Reset Command' },

    # Router-specific commands
    0x80: { 'request': 0, 'response': 2, 'name': 'Get Motor Current' },
    0x81: { 'request': 2, 'response': 0, 'name': 'Set motor 1 state' },
    0x82: { 'request': 0, 'response': 3, 'name': 'Get motor 1 state' },
    0x83: { 'request': 2, 'response': 0, 'name': 'Set motor 2 state' },
    0x84: { 'request': 0, 'response': 3, 'name': 'Get motor 2 state' },
    0x86: { 'request': 0, 'response': 4, 'name': 'Get motor 1 position' },
    0x87: { 'request': 0, 'response': 0, 'name': 'Reset motor 1 position' },
    0x88: { 'request': 1, 'response': 0, 'name': 'Move motor 1 up or down' },
    0x89: { 'request': 2, 'response': 0, 'name': 'Move motor 1 up or down delta position' },
    0x8A: { 'request': 0, 'response': 4, 'name': 'Get motor 2 position' },
    0x8B: { 'request': 0, 'response': 0, 'name': 'Reset motor 2 position' },
    0x8C: { 'request': 1, 'response': 0, 'name': 'Move motor 2 up or down' },
    0x8D: { 'request': 2, 'response': 0, 'name': 'Move motor 2 up or down delta position' },
}

def pac_next(cap, pac_num):
    try:
        return cap.next(), pac_num + 1
    except StopIteration:
        return None, pac_num

def parse_usb_capdata(capdata):
    by = bytes.fromhex(capdata.replace(':', ''))
    data = None
    if len(by) > 0:
        # [3f, 07, 03, 03, 00, 00, args...]
        args_len = int.from_bytes(by[3:(4 + 1)], 'little')
        data = {
            'total_len': by[0] + 1, # The total number of bytes in the payload
            'len': by[1], # The total of number of actual bytes used in the payload
            'raw': by[2:], # The actual command, unparsed
            'cmd': by[2], # The commands opcode
            'args_len': args_len, # The command arguments' length
            'cmd_len': args_len + 4, # The actual command's length, calculated using 'args_len'
            'response': True if by[5] else False, # Does the command request a response?
            'args': by[6:], # The commands arguments, unparsed
        }
    return data

def check_packet(pac, pac_num, cmds_queue, timings):
    data = None # Equals to None if no data was sent in this packet
    try:
        data = parse_usb_capdata(pac.data.usb_capdata)
    except AttributeError:
        pass
    # Check for packets of type: URB INTERRUPT OUT host to device
    if pac.usb.endpoint_address_direction == direction['out'] and pac.usb.src == 'host':
        if int(pac.usb.data_len) != 64:
            print("Packet no. %d: Payload length is not 64 bytes" % (pac_num,))
        if data['total_len'] != int(pac.usb.data_len):
            print("Packet no. %d: Sent payload with first byte different than 0xf3 (63 bytes)" % (pac_num,))
        if data['len'] != data['cmd_len']:
            print("Packet no. %d: The payload's actual length (0x%02x) doesn't match the reported one (0x%02x)" % (pac_num, data['cmd_len'], data['len']))
        if data['cmd'] not in cmds:
            print("Packet no. %d: Opcode not found 0x%02x" % (pac_num, data['cmd']))
        if data['args_len'] != cmds[data['cmd']]['request']:
            print("Packet no. %d: The number of arguments (%d) doesn't match the expected number (%d)" % (pac_num, data['args_len'], cmds[data['cmd']]['request']))
        if not all(i == 0 for i in data['args'][data['args_len']:]):
            print("Packet no. %d: The host didn't fill with 0 the rest of the payload" % (pac_num,))
        if data['response']:
            # Found a legal request
            cmds_queue.append({ 'cmd': data['cmd'], 'time': pac.sniff_time, 'pac_num': pac_num })
    # Check for packets of type: URB INTERRUPT IN device to host
    if pac.usb.endpoint_address_direction == direction['in'] and pac.usb.dst == 'host':
        if int(pac.usb.data_len) != 64:
            print("Packet no. %d: Payload length is not 64 bytes" % (pac_num,))
        if data['total_len'] != int(pac.usb.data_len):
            print("Packet no. %d: Sent payload with first byte different than 0xf3 (63 bytes)" % (pac_num,))
        if data['len'] != data['cmd_len']:
            print("Packet no. %d: The payload's actual length (0x%02x) doesn't match the reported one (0x%02x)" % (pac_num, data['cmd_len'], data['len']))
        if data['cmd'] not in cmds:
            print("Packet no. %d: Opcode not found 0x%02x" % (pac_num, data['cmd']))
        if data['args_len'] != cmds[data['cmd']]['response']:
            print("Packet no. %d: The number of arguments (%d) doesn't match the expected number (%d)" % (pac_num, data['args_len'], cmds[data['cmd']]['response']))
        if not data['response']:
            print("Packet no. %d: The device didn't echo the \"response\" byte (it's 0)" % (pac_num,))
        if not any(i['cmd'] == data['cmd'] for i in cmds_queue):
            print("Packet no. %d: The device responded to a command not requested (0x%02x)" % (pac_num, data['cmd']))
        else:
            if data['cmd'] != cmds_queue[0]['cmd']:
                skipped = 0
                for i in cmds_queue:
                    if data['cmd'] == i['cmd']:
                        break
                    skipped += 1
                del cmds_queue[:skipped]
                print("Packet no. %d: The device ignored the first %d commands in queue" % (pac_num, data['cmd']))
            # Found a legal response
            delta_time = pac.sniff_time - cmds_queue[0]['time']
            delta_time_ms = delta_time.total_seconds() * 1000
            timings.append({ 'time': delta_time_ms, 'request': cmds_queue[0]['pac_num'], 'response': pac_num })
            del cmds_queue[0]

def main():
    if len(sys.argv) != 2:
        print("Usage: %s \"path/to/capture_file.pcapng\"" % (sys.argv[0],))
        return
    cap_file = sys.argv[1]
    cap = pyshark.FileCapture(cap_file)

    # Skip to the first packet whose direction is OUT (first request for the device)
    pac_num = 1 # Packets start at index 1 in Wireshark
    pac, pac_num = pac_next(cap, pac_num)
    while pac is not None and pac.usb.endpoint_address_direction != direction['out']:
        pac, pac_num = pac_next(cap, pac_num)


    # Go over all the packets, and check for illegal requests or missing responses
    timings = []
    cmds_queue = []
    check_packet(pac, pac_num, cmds_queue, timings)
    pac, pac_num = pac_next(cap, pac_num)
    while pac is not None:
        check_packet(pac, pac_num, cmds_queue, timings)
        pac, pac_num = pac_next(cap, pac_num)

    if len(cmds_queue) > 0:
        print("%d requests left without responses" % (len(cmds_queue),))

    times = [i['time'] for i in timings]
    requests = [i['request'] for i in timings]
    responses = [i['response'] for i in timings]

    fig, ax1 = plt.subplots(1, 1)
    ax1.plot(requests, times, '+-', linewidth=0.75)
    ax1.set_xlabel("Request")
    ax1.set_ylabel("Time [ms]")
    ax1.grid(True)

    ax2 = ax1.twiny()
    ax2.plot(responses, times, '+-', linewidth=0.75)
    ax2.set_xlabel("Response")

    plt.show()

if __name__ == "__main__":
    main()