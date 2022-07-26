#!/usr/bin/python3
# C:\Work\Python\HID_Util\src\toradex_plot.py
# toradex_plot.py  that uses a pcapng file and parse it and plot the values.
# for plotting pcapng files by using matplotlib and tkinter
# date: 2022_07_23

# usage:
#       toradex_plot.py -o
#           or
#       toradex_plot.py "C:\Work\USB\WireShark\2022_07_19\2022_07_19__19_00_Toradex.pcapng"

# usage:
# WireShrk_Station_plot.py "C:\Work\USB\WireShark\2022_07_14\2022_07_14__17_34__streaming_recorded_with_movement.pcapng"
# Toradex_plot.py "C:\Work\USB\WireShark\2022_07_19\2022_07_19__19_00_Toradex.pcapng"

import sys
import pyshark
import numpy as np
import matplotlib.pyplot as plt
from string_date_time import get_date_time_sec
from string_date_time import get_date_time
from datetime import datetime

from tkinter import *
# from tkinter import filedialog
from tkinter.filedialog import askopenfilename
import os

# packet.usb.src -- Packet's source (host/device)
# packet.usb.dst -- Packet's destination (host/device)
# packet.usb.endpoint_address_direction -- URB INTERRUPT IN/OUT
# packet.usb.data_len -- Packet's payload length
# packet.data.usb_capdata -- Packet's payload (in this format '3f:07:03:...:00')
# global veriables:
debug_print = 0
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
MAX_LONG_POSITIVE = 2**31
MAX_UNSIGNED_LONG = 2**32
def long_unsigned_to_long_signed( x ):
    if x > MAX_LONG_POSITIVE:
        x = x - MAX_UNSIGNED_LONG
    return x

def pac_next(cap, pac_num):
    try:
        return cap.next(), pac_num + 1
    except StopIteration:
        return None, pac_num

data_index = 0
file_indx = 0
aggregate_counter = 0
def parse_usb_capdata2(capdata):
    global  debug_print
    global  data_index
    global file_indx
    by = bytes.fromhex(capdata.replace(':', ''))
    data = None
    # TORQUE_INDEX = 6
    # INSERTION_INDEX = 10
    # toradex index for reverse engineering
    TORQUE_INDEX = 4
    INSERTION_INDEX = 8
    len_by = len(by)
    if len_by > 0:
        # [3f, 07, 03, 03, 00, 00, args...]
        # [3f, 2e, xx, xx, xx, xx, xx ...] // in streaming mode.
        # [ ReturnCode , Param[31] ] // in Toradex protocol.
        # args_len = int.from_bytes(by[3:(4 + 1)], 'little')
        ReturnCode = by[0]
        data = {
            'byte_0': by[0],
            'word_0': int.from_bytes(by[0:(1 + 1)], 'little'), #The first 2 bytes in the data from the stream report: Report.Ch0_LSB  and Report.Ch0_MSB
            # 'len': by[1], # The total of number of actual bytes used in the payload
            # 'raw': by[2:], # The actual command, unparsed
            # 'fill': int.from_bytes(by[2:(3 + 1)], 'little'), # The dummy 2 bytes that are not used yet
            'cmos': int.from_bytes(by[2:(3 + 1)], 'little'), # The analog value of this channel
            # 'cmos': int(by[2]), # The analog value of this channel

            # 'ch01': int.from_bytes(by[6:(9 + 1)], 'little'), # The Torque value 4 bytes signed integer
            # 'ch01': long_unsigned_to_long_signed(int.from_bytes(by[6:(9 + 1)], 'little')), # The Torque value 4 bytes signed integer

            # 00 00 02 00
            # 2  3  0  1
            # 'ch01': long_unsigned_to_long_signed((int(by[TORQUE_INDEX + 2]) << 24) + (int(by[TORQUE_INDEX+3]) <<16) + (int(by[TORQUE_INDEX]) <<8) + int(by[TORQUE_INDEX+1])),
            #
            'ch01': long_unsigned_to_long_signed((int(by[TORQUE_INDEX+1]) << 24) + (int(by[TORQUE_INDEX]) <<16) + (int(by[TORQUE_INDEX+3]) <<8) + int(by[TORQUE_INDEX+2])),
            # 'ch01_0': by[TORQUE_INDEX] ,
            # 'ch01_1': by[TORQUE_INDEX+1] ,
            # 'ch01_2': by[TORQUE_INDEX+2] ,
            # 'ch01_3': by[TORQUE_INDEX+3] ,

            # 'ch01': long_unsigned_to_long_signed((int(by[TORQUE_INDEX + 2]) << 24) + (int(by[TORQUE_INDEX+3]) <<16) + (int(by[TORQUE_INDEX]) <<8) + int(by[TORQUE_INDEX+1])),
            # 'ch01': long_unsigned_to_long_signed((int(by[TORQUE_INDEX + 2]) << 24) + (int(by[TORQUE_INDEX+3]) <<16) + (int(by[TORQUE_INDEX]) <<8) + int(by[TORQUE_INDEX+1])),
            # 'ch01': long_unsigned_to_long_signed((int(by[TORQUE_INDEX + 2]) << 24) + (int(by[TORQUE_INDEX+3]) <<16) + (int(by[TORQUE_INDEX]) <<8) + int(by[TORQUE_INDEX+1])),

            # 'ch02': int.from_bytes(by[10:(13 + 1)], 'little'), # The insertion value 4 bytes signed integer
            # 'ch03': int.from_bytes(by[14:(14 + 1)], 'little'), # The analog value of this channel
            # 'ch02': 17, # The insertion value 4 bytes signed integer

            # 'ch02': long_unsigned_to_long_signed((int(by[INSERTION_INDEX + 2]) << 24) + (int(by[INSERTION_INDEX+3]) <<16) + (int(by[INSERTION_INDEX]) <<8) + int(by[INSERTION_INDEX+1])),
            'ch02': long_unsigned_to_long_signed((int(by[INSERTION_INDEX+1]) << 24) + (int(by[INSERTION_INDEX]) <<16) + (int(by[INSERTION_INDEX+3]) <<8) + int(by[INSERTION_INDEX+2])),

            # 'ch02_0': (int(by[INSERTION_INDEX]) ),
            # 'ch02': long_unsigned_to_long_signed((int(by[INSERTION_INDEX + 2]) << 24) + (int(by[INSERTION_INDEX+3]) <<16) + (int(by[INSERTION_INDEX]) <<8) + int(by[INSERTION_INDEX+1])),
            # 'ch02': long_unsigned_to_long_signed((int(by[INSERTION_INDEX + 2]) << 24) + (int(by[INSERTION_INDEX+3]) <<16) + (int(by[INSERTION_INDEX]) <<8) + int(by[INSERTION_INDEX+1])),
            # 'ch02': long_unsigned_to_long_signed((int(by[INSERTION_INDEX + 2]) << 24) + (int(by[INSERTION_INDEX+3]) <<16) + (int(by[INSERTION_INDEX]) <<8) + int(by[INSERTION_INDEX+1])),

            # 'ch03': int.from_bytes(by[11:(11 + 1)], 'little'), # Toradex: Report.Ch[9] = buf[6];	// Squal
            'ch03': by[12],  # image_quality
            # 'ch05': int.from_bytes(by[12:(13 + 1)], 'little'), # The analog value of this channel
            'data_index': data_index,
            'file_indx': file_indx,
        }
        data_index = data_index +1
        debug_print = debug_print + 1
        if (debug_print%100) == 0:
            # print("> data here:   ",data,"   debug_print   ", debug_print, "  ")
            pass
        # elif (debug_print>880 and debug_print< 900):
        #     print(" >")
        #     print("data here:   ", data, "   debug_print   ", debug_print, end="  ")
        elif (data['data_index'] >= 880 and data['data_index'] <= 900):
            pass
            # print("i> data here:   ", data, "   data_index   ", data['data_index'], "  ")

    return data


def check_packet2(pac, pac_num, t_prev, timings):
    data = None # Equals to None if no data was sent in this packet
    global file_indx
    global aggregate_counter
    file_indx = file_indx + 1
    try:
        # data = parse_usb_capdata2(pac.data.usb_capdata)
        data = parse_usb_capdata2(pac.data.usb_control_response)
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

        if data != None:  #2022_07_23__22_57
            # if data['word_0'] != 0xff:
            # aggregate only streaming and relevant packets
            if data['byte_0'] != 0xff and (data['cmos'] < 4000) and ( abs(data['ch01']) < 1000000) and ( abs(data['ch02']) < 1000000):
            # if True:
                # timings.append({'time': delta_time_ms, 'number': pac_num, 'ana_00':data['cmos'], 'ana_01':data['ch01'], 'ana_02':data['ch02'], 'ana_03':data['ch03'], 'ana_04':data['ch04'], 'ana_05':data['ch05'], 'ana_06':data['ch06'], 'ana_07':data['ch07'], 'ana_08':data['ch08'], 'ana_09':data['ch09'], 'ana_10':data['ch10'], 'ana_11':data['ch11'], 'ana_12':data['ch12'], 'ana_13':data['ch13']})

                    # removing the extra channels did not improve the parsing time
                    # timings.append({'time': delta_time_ms, 'number': pac_num, 'ana_00':data['cmos'], 'ana_01':data['ch01_0'], 'ana_02':data['ch02_0'], 'ana_03':data['ch03']})
                    skipped = check_packet2.skip_cntr
                    timings.append({'time': delta_time_ms, 'number': pac_num, 'ana_00':data['cmos'], 'ana_01':data['ch01'], 'ana_02':data['ch02'], 'ana_03':data['ch03'], 'file_indx':file_indx,'skipped':skipped})
                    check_packet2.skip_cntr = 0

            # timings.append({'time': delta_time_ms, 'number': pac_num, 'ana_00':data['cmos'], 'ana_01':11, 'ana_02':22, 'ana_03':data['ch03'], 'file_indx':file_indx})
                    # timings.append({'time': delta_time_ms, 'number': pac_num, 'ana_00':data['cmos'], 'ana_01':11, 'ana_02':22, 'ana_03':33, 'file_indx':file_indx})

                    # timings.append({'time': delta_time_ms, 'number': pac_num, 'ana_00':data['cmos'], 'ana_01':1, 'ana_02':2, 'ana_03':data['ch03'], 'file_indx':file_indx })
                    aggregate_counter = aggregate_counter +1
            else:
                check_packet2.skip_cntr += 1
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
check_packet2.skip_cntr = 0

def main():
    global filepath
    use_tKinter = 0

    if len(sys.argv) != 2:
        print("Usage: %s \"path/to/capture_file.pcapng\"" % (sys.argv[0],))
        return

    # using gui to select a file:
    if sys.argv[1] == "-o" :
        my_Path = "C:\\Work\\USB\\WireShark"
        print("Use tKinter")
        use_tKinter = 1
        
        root = Tk()
        root.withdraw()
        isExist = os.path.exists(my_Path)
        if isExist :
            file_path = askopenfilename(initialdir=my_Path,
                                        filetypes= (("pcapng files","*.pcapng"),("all files","*.*")))
        else:
            file_path = askopenfilename(filetypes= (("pcapng files","*.pcapng"),("all files","*.*")))
        root.destroy()
        # print("with the use of withdraw() : %s" % file_path)
        cap_file =  file_path
        print("the user input file: %s" % cap_file)
        # return 
    else:
        cap_file = sys.argv[1]
        print("the user input file: %s" % cap_file)

    cap = pyshark.FileCapture(cap_file)
    cap_file_lst = cap_file.split("\\")
    fine_name = cap_file_lst[len(cap_file_lst)-1]
    # print(fine_name)
    
    # print("return here for debug")
    # return
    start_date_time = get_date_time_sec()
    t0 = datetime.now()


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
    # return # for debug
    timings = []  # to remove the first element.
    pac, pac_num = pac_next(cap, pac_num)
    i=0
    while pac is not None:
        i = i+1
        if i%100==0:
            print(i)
            
        # if i > 3346 and i < 3359 :
            # print(i)
        prev_time = check_packet2(pac, pac_num, prev_time, timings)
        pac, pac_num = pac_next(cap, pac_num)
        # 2022_07_25__16_09
        # if i>2000:
        #     break
        # if i>60:
        #     break

    # if len(cmds_queue) > 0:
    #     print("%d requests left without responses" % (len(cmds_queue),))
    print("aggregate_counter: %d  ; pac_num: %d  file_indx: %d" % (aggregate_counter,pac_num,file_indx))
    
    timings = timings[1:]
    timings_len = len(timings)
    print("timings_len: ",timings_len)
    times = [i['time'] for i in timings]
    ac_time =[]
    ac=0
    for i in range(len(times)):
        ac = ac + timings[i]['time']
        ac_time.append(ac)
    print("len of ac_time= {}".format(len(ac_time)))
    times2 = [2*i['time'] for i in timings]
    packet_num = [i['number'] for i in timings]
    packet_num_mod = [(i['number'])%100 for i in timings]
    responses = [2*i['number'] for i in timings]
    cha_00 = [i['ana_00'] for i in timings]
    cha_01 = [i['ana_01'] for i in timings]
    cha_02 = [i['ana_02'] for i in timings]
    cha_03 = [i['ana_03'] for i in timings]
    used_index = [i['file_indx'] for i in timings]
    skipped= [i['skipped'] for i in timings]
    # print("timings[3310:3315]: ",timings[3310:3315])


    fig, (ax1,ax2) = plt.subplots(2, 1)
    ax1.grid(True)
    ax2.grid(True)
    # ax1.plot(packet_num, times, '+-', linewidth=0.75)
    # ax1.plot(packet_num, times2, 'ro', linewidth=0.75)
    first_4_channels = 1

    if first_4_channels:
        ax2.plot(ac_time, cha_00, 'c+', linewidth=0.75)
        ax1.set_xlabel("ac_time")

        # plt.plot(y0,label="tool_size")
        # plt.plot(y1,label="insertion")
        # plt.plot(y2,label="torque")

        # color = #008000
        # use_color = '#008000'
        # use_color = '#ebaee8'
        use_color = '#83fc95'
        ax1.plot(packet_num, cha_03, color=use_color, linewidth=0.75,label="image_quality") # be first to overwrite
        use_color = '#735e53'
        ax1.plot(packet_num, skipped, color=use_color, linewidth=0.75,label="skipped cntr") # be first to overwrite
        ax1.plot(packet_num, cha_00, 'c+-', linewidth=0.75,label="tool_size")
        ax1.plot(packet_num, cha_01, 'm-', linewidth=0.75,label="insertion") # swapped with torque regarding Hamamatsu 
        ax1.plot(packet_num, cha_02, 'b-', linewidth=0.75,label="torque")    # swapped with insertion regarding Hamamatsu 
        # ax1.plot(packet_num, packet_num_mod, 'k.', linewidth=0.75,label="packet_num")
        # ax1.set_xlim([0, 5000])
        # ax1.set_ylim([-10, 600])

        # ax1.plot(packet_num, cha_03, 'r-', linewidth=0.75,label="image_quality")
        ax1.set_xlabel("packet_num")
        ax1.legend()

        # ax1.set_ylabel("Time [ms]")
        ax1.set_ylabel("ADC: 4095=3volt")
        ax2.set_ylabel("tool_size: 2047=Max")
        # fig.suptitle('Voltage in channels: 0,1,2,3')
        fine_name = fine_name + " -- [ tool_size   torque   insertion    image_quality ]"
        fig.suptitle(fine_name)
    else:
        pass
        # # need to plot channels: 8,11,12,13
        # ax1.plot(packet_num, cha_08, 'c-', linewidth=0.75)
        # ax2.plot(ac_time, cha_08, 'c-', linewidth=0.75)

        # ax1.plot(packet_num, cha_11, 'm-', linewidth=0.75)
        # ax1.plot(packet_num, cha_12, 'b-', linewidth=0.75)
        # ax1.plot(packet_num, cha_13, 'r-', linewidth=0.75)
        # ax1.set_xlabel("packet_num")
        # # ax1.set_ylabel("Time [ms]")
        # ax1.set_ylabel("ADC: 4095=3volt")
        # # fig.suptitle('Voltage in channels: 8,11,12,13', y=1.03, fontsize=25)
        # # fig.suptitle('Voltage in channels: 8,11,12,13')
        # fine_name = fine_name + " -- in channels: 8, 11, 12(blue), 13"
        # fig.suptitle(fine_name)
        # # plt.title('Voltage in channels: 8,11,12,13')

    # ax2 = ax1.twiny()
    # ax2.plot(responses, times, '+-', linewidth=0.75)
    # ax2.set_xlabel("Response")
    t1 = datetime.now()
    print("Parsing start time: ", start_date_time)
    print("Parsing end time: ", get_date_time_sec())
    print("Delta Parsing time: ", t1-t0)

    plt.show()

if __name__ == "__main__":
    main()