#!/usr/bin/env python3
# file: WireShrk_analog_plot.py
# date: 2021_09_28

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

def parse_usb_capdata2(capdata):
    by = bytes.fromhex(capdata.replace(':', ''))
    data = None
    if len(by) > 0:
        # [3f, 07, 03, 03, 00, 00, args...]
        # [3f, 2e, xx, xx, xx, xx, xx ...] // in streaming mode.
        args_len = int.from_bytes(by[3:(4 + 1)], 'little')
        data = {
            'total_len': by[0] + 1, # The total number of bytes in the payload - this is always = 64
            'len': by[1], # The total of number of actual bytes used in the payload
            'raw': by[2:], # The actual command, unparsed
            'ch00': int.from_bytes(by[2:(3 + 1)], 'little'), # The analog value of this channel
            'ch01': int.from_bytes(by[4:(5 + 1)], 'little'), # The analog value of this channel
            'ch02': int.from_bytes(by[6:(7 + 1)], 'little'), # The analog value of this channel
            'ch03': int.from_bytes(by[8:(9 + 1)], 'little'), # The analog value of this channel
            'ch04': int.from_bytes(by[10:(11 + 1)], 'little'), # The analog value of this channel
            'ch05': int.from_bytes(by[12:(13 + 1)], 'little'), # The analog value of this channel
            'ch06': int.from_bytes(by[14:(15 + 1)], 'little'), # The analog value of this channel
            'ch07': int.from_bytes(by[16:(17 + 1)], 'little'), # The analog value of this channel
            'ch08': int.from_bytes(by[18:(19 + 1)], 'little'), # The analog value of this channel
            'ch09': int.from_bytes(by[20:(21 + 1)], 'little'), # The analog value of this channel
            'ch10': int.from_bytes(by[22:(23 + 1)], 'little'), # The analog value of this channel
            'ch11': int.from_bytes(by[24:(25 + 1)], 'little'), # The analog value of this channel
            'ch12': int.from_bytes(by[26:(27 + 1)], 'little'), # The analog value of this channel
            'ch13': int.from_bytes(by[28:(29 + 1)], 'little'), # The analog value of this channel
        }
    return data
'''
'''

def check_packet2(pac, pac_num, t_prev, timings):
    data = None # Equals to None if no data was sent in this packet
    try:
        data = parse_usb_capdata2(pac.data.usb_capdata)
    except AttributeError:
        pass
    if pac_num < 50:
        pass
        # print(data['total_len'])
    # Check for packets of type: URB INTERRUPT OUT host to device
    if pac.usb.endpoint_address_direction == direction['out'] and pac.usb.src == 'host':
        print("Packet no. %d: from host to device" % (pac_num,))
            # cmds_queue.append({ 'cmd': data['cmd'], 'time': pac.sniff_time, 'pac_num': pac_num })
    # Check for packets of type: URB INTERRUPT IN device to host
    if pac.usb.endpoint_address_direction == direction['in'] and pac.usb.dst == 'host':
        if pac_num == 131:
            print(pac_num)
        # cur_time = pac.sniff_time.microsecond
        # delta_time =cur_time - t_prev.microsecond
        cur_time = pac.sniff_time
        delta_time = cur_time - t_prev
        # if delta_time < 0:
        #     print("delta time less then zero: {}".format(delta_time))
        # delta_time_ms = delta_time/1000    # from microsecond to miliseconds
        delta_time_ms = delta_time.total_seconds() * 1000  # from microsecond to miliseconds
        timings.append({'time': delta_time_ms, 'number': pac_num, 'ana_00':data['ch00'], 'ana_01':data['ch01'], 'ana_02':data['ch02'], 'ana_03':data['ch03'], 'ana_04':data['ch04'], 'ana_05':data['ch05'], 'ana_06':data['ch06'], 'ana_07':data['ch07'], 'ana_08':data['ch08'], 'ana_09':data['ch09'], 'ana_10':data['ch10'], 'ana_11':data['ch11'], 'ana_12':data['ch12'], 'ana_13':data['ch13']})
    #     if not data['response']:
    #         print("Packet no. %d: The device didn't echo the \"response\" byte (it's 0)" % (pac_num,))
        # if not any(i['cmd'] == data['cmd'] for i in cmds_queue):
        #     print("Packet no. %d: The device responded to a command not requested (0x%02x)" % (pac_num, data['cmd']))
        # else:
        #     if data['cmd'] != cmds_queue[0]['cmd']:
        #         skipped = 0
        #         for i in cmds_queue:
        #             if data['cmd'] == i['cmd']:
        #                 break
        #             skipped += 1
        #         del cmds_queue[:skipped]
        #         print("Packet no. %d: The device ignored the first %d commands in queue" % (pac_num, data['cmd']))
            # Found a legal response
    return pac.sniff_time

def main():
    if len(sys.argv) != 2:
        print("Usage: %s \"path/to/capture_file.pcapng\"" % (sys.argv[0],))
        return
    # cap_file = "r"+sys.argv[1]
    # cap_file = r"C:\Work\USB\WireShark\2021_09_09\on old board len=91.pcapng"
    cap_file = sys.argv[1]
    cap = pyshark.FileCapture(cap_file)
    cap_file_lst = cap_file.split("\\")
    fine_name = cap_file_lst[len(cap_file_lst)-1]
    print(fine_name)
    # print("return here for debug")
    # return

    # Skip to the first packet whose direction is OUT (first request for the device)
    pac_num = 1 # Packets start at index 1 in Wireshark
    pac, pac_num = pac_next(cap, pac_num)
    # print("return here for debug")
    #return
    # while pac is not None and pac.usb.endpoint_address_direction != direction['out']:
    #     pac, pac_num = pac_next(cap, pac_num)

    # Go over all the packets, and check for illegal requests or missing responses
    timings = []
    cmds_queue = []
    prev_time = pac.sniff_time
    prev_time =  check_packet2(pac, pac_num, prev_time, timings)
    pac, pac_num = pac_next(cap, pac_num)
    i=0
    while pac is not None:
        i = i+1
        if i%100==0:
            print(i)
        prev_time = check_packet2(pac, pac_num, prev_time, timings)
        pac, pac_num = pac_next(cap, pac_num)
        # if i>60:
        #     break

    # if len(cmds_queue) > 0:
    #     print("%d requests left without responses" % (len(cmds_queue),))

    times = [i['time'] for i in timings]
    ac_time =[]
    ac=0
    for i in range(len(times)):
        ac = ac + timings[i]['time']
        ac_time.append(ac)
    print("len of ac_time= {}".format(len(ac_time)))
    times2 = [2*i['time'] for i in timings]
    packet_num = [i['number'] for i in timings]
    responses = [2*i['number'] for i in timings]
    cha_00 = [i['ana_00'] for i in timings]
    cha_01 = [i['ana_01'] for i in timings]
    cha_02 = [i['ana_02'] for i in timings]
    cha_03 = [i['ana_03'] for i in timings]

    cha_08 = [i['ana_08'] for i in timings]
    cha_09 = [i['ana_09'] for i in timings]
    cha_10 = [i['ana_10'] for i in timings]
    cha_11 = [i['ana_11'] for i in timings]

    cha_12 = [i['ana_12'] for i in timings]
    cha_13 = [i['ana_13'] for i in timings]

    fig, (ax1,ax2) = plt.subplots(2, 1)
    ax1.grid(True)
    ax2.grid(True)
    # ax1.plot(packet_num, times, '+-', linewidth=0.75)
    # ax1.plot(packet_num, times2, 'ro', linewidth=0.75)
    first_4_channels = 1

    if first_4_channels:
        ax1.plot(packet_num, cha_00, 'c-', linewidth=0.75)
        ax2.plot(ac_time, cha_00, 'c-', linewidth=0.75)

        ax1.plot(packet_num, cha_01, 'm-', linewidth=0.75)
        ax1.plot(packet_num, cha_02, 'b-', linewidth=0.75)
        ax1.plot(packet_num, cha_03, 'r-', linewidth=0.75)
        ax1.set_xlabel("packet_num")
        # ax1.set_ylabel("Time [ms]")
        ax1.set_ylabel("ADC: 4095=3volt")
        # fig.suptitle('Voltage in channels: 0,1,2,3')
        fine_name = fine_name + " -- first 4 channels"
        fig.suptitle(fine_name)
    else:
        # need to plot channels: 8,11,12,13
        ax1.plot(packet_num, cha_08, 'c-', linewidth=0.75)
        ax2.plot(ac_time, cha_08, 'c-', linewidth=0.75)

        ax1.plot(packet_num, cha_11, 'm-', linewidth=0.75)
        ax1.plot(packet_num, cha_12, 'b-', linewidth=0.75)
        ax1.plot(packet_num, cha_13, 'r-', linewidth=0.75)
        ax1.set_xlabel("packet_num")
        # ax1.set_ylabel("Time [ms]")
        ax1.set_ylabel("ADC: 4095=3volt")
        # fig.suptitle('Voltage in channels: 8,11,12,13', y=1.03, fontsize=25)
        # fig.suptitle('Voltage in channels: 8,11,12,13')
        fine_name = fine_name + " -- in channels: 8, 11, 12(blue), 13"
        fig.suptitle(fine_name)
        # plt.title('Voltage in channels: 8,11,12,13')

    # ax2 = ax1.twiny()
    # ax2.plot(responses, times, '+-', linewidth=0.75)
    # ax2.set_xlabel("Response")

    plt.show()

if __name__ == "__main__":
    main()