#!/usr/bin/python3
# C:\Work\Python\HID_Util\src\LogicAnalyzer_spi2csv.py
# for converting Saleae SPI CSV files into data to plot CSV file.

# usage:
# To run the spi data converter use:
#       LogicAnalyzer_spi2csv.py -o
#
# chose the exported data from the original path.
# example:
# "C:\Work\Logic_Analyzer\2023_03_17\2023_03_17__00_26-exported-data.csv"
# the resulted CSV file will be at:
#                                    log\spi_data_2023_MM_DD_hh_mm.csv 
#
#           or
#       LogicAnalyzer_spi2csv.py "C:\Work\Logic_Analyzer\2023_03_17\2023_03_17__00_26-exported-data.csv"

import matplotlib.pyplot as plt
import numpy as np
import csv
import sys
from tkinter import *
# from tkinter import filedialog
from tkinter.filedialog import askopenfilename
import os
from string_date_time import get_date_time
from colorama import Fore, Back, Style

# Define ANSI escape sequences for various colors
GREEN = '\033[32m'
YELLOW = '\033[33m'
RESET = '\033[0m'


FILE1_PATH = "log\hid_2022_06_30__23_33.csv"
# "C:\Work\Python\HID_Util\src\log\hid_2022_06_30__23_33.csv"
filepath = "here_should_be_path"

FILE1_PATH = "log\spi_data_" # log.csv"
start_date_time = get_date_time()
FILE1_PATH = FILE1_PATH + start_date_time + ".csv"
print("Converting result to: ", FILE1_PATH, "\n")
if not os.path.exists('log'):
    os.makedirs('log')
# open recording log file:
result_file = open(FILE1_PATH,"w") 

'''
def openFile():
    global filepath
    filepath = filedialog.askopenfilename(initialdir="C:\\Work\\Python\\HID_Util\\src\\log",
                                          title="Open file okay?",
                                          filetypes= (("csv files","*.csv"),
                                          ("all files","*.*")))
    file = open(filepath,'r')
    print(filepath)
'''

def main():
    global filepath
    use_tKinter = 0

    if len(sys.argv) != 2:
        print("Usage: %s \"path/to/log_file.csv\"" % (sys.argv[0],))
        return

    if sys.argv[1] == "-o" :
        # my_Path = "C:\\Work\\Logic_Analyzer\\2023_02_21"
        my_Path = "C:\\Work\\Logic_Analyzer\\2023_03_19"
        print("Use tKinter")
        use_tKinter = 1
        
        root = Tk()
        root.withdraw()
        isExist = os.path.exists(my_Path)
        if isExist :
            file_path = askopenfilename(initialdir=my_Path,
                                        filetypes= (("csv files","*.csv"),("all files","*.*")))
        else:
            file_path = askopenfilename(filetypes= (("csv files","*.csv"),("all files","*.*")))
        root.destroy()
        print("with the use of withdraw() : %s" % file_path)
        filepath =  file_path
        print("the user input file: %s" % filepath)
        # return 
    else:
        cap_file = sys.argv[1]
        print("the user input file: %s" % cap_file)

    try:
        
        if use_tKinter == 1:
            print("we have a path from gui %s" % filepath)
            file1 = open(filepath,"r+")
            print_info( file1 )
            
        else:
            file1 = open(cap_file,"r+")
            print_info( file1 )
    except FileNotFoundError:
        print("bad file path in user input argument: %s  !!!" % cap_file)
        return
    exit()
    return
        
def print_info( file1 ):
    csv_line_number = 0
    line_number = 0
    prev_line = 0
    # read_delta = 0
    read_deltaX_l = 0
    read_deltaY_l = 0
    read_deltaX_h = 0
    read_deltaY_h = 0
    printed_lines = 0 
    motion_lines = 0 
    global result_file
    posx = 0
    posy = 0
    read_status_register = 0
    last_deltaY = 0
    status_register_read_line = 0
    motion_register = 0
    
    for line in file1:
        deltaX = 0
        deltaY = 0
        csv_line_number += 1
        line_number += 1
        line = line.strip()
        list = line.split(",")
        # print(list, end="")
        # print(list[1])
        # or  (list[4] == '0x04') or  (list[4] == '0x11') or  (list[4] == '0x12'):
        if (list[4] == '0x03'): 
            read_deltaX_l = line_number
        if (list[4] == '0x04'): 
            read_deltaY_l = line_number
        if (list[4] == '0x11'): 
            read_deltaX_h = line_number
        if (list[4] == '0x12'): 
            read_deltaY_h = line_number
        
        if (list[4] == '0x02'): # read status register // once for every "burst"
            status_register_read_line = line_number
            read_status_register = 1

        if list[1] == '"result"':
            if status_register_read_line == prev_line:
                motion_register = list[5]
                if motion_register == '0x80':
                    # there is movement in this query -> will be followed by "burst" query!
                    pass
                else:
                    # there is no movement (in both axes)  --> we zeroing the last delta Y 
                    last_deltaY = 0 # this is not completely true since there could be X movement...
            if read_deltaX_l == prev_line:
                deltaX_l = list[5]
                # print(list, end="")
                # print("    ",csv_line_number)
            if read_deltaY_l == prev_line:
                deltaY_l = list[5]
            if read_deltaX_h == prev_line:
                deltaX_h = list[5]
            if read_deltaY_h == prev_line:
                deltaY_h = list[5]
                motion_lines += 1
                # a read delta action happen for every movement, hence if there was in the current 
                # SPI sample (aka this 1ms) a delta read action, it must be 4 reads of x,y,xh,yh
                # therefore in the 4th read, we accomplished the sample movement information.
                # if motion_lines > 1000:  
                if 1:  
                    # print("deltaX: ", deltaX_h,deltaX_l,"   deltaY: ", deltaY_h,deltaY_l,end="")
                    print(GREEN + "deltaX: ", deltaX_h,deltaX_l,"   deltaY: ", deltaY_h,deltaY_l,end="")
                    deltaX = uint16_to_signed(int(deltaX_h,16)*256 + int(deltaX_l,16))
                    deltaY = uint16_to_signed(int(deltaY_h,16)*256 + int(deltaY_l,16))
                    print("    " + RESET, deltaX,deltaY)
                    printed_lines += 1
                    last_deltaY = deltaY
                    #if deltaX != 0 and deltaY == 0:   # this is for debug only.
                    #    print(Back.RED + " movement only on X but no Y movement:", "    deltaX: ",deltaX,"     deltaY: ",deltaY)
                    #    print(Style.RESET_ALL)
                        
                    
        prev_line = line_number
        posx += deltaX
        posy += deltaY
        tool_size = 0
        if read_status_register:
            # L = [ str(tool_size),",   ", str(posy), ", " , str(posx), "\n" ]             
            # instead of (tool_size) we want to see in the graph (deltaY)
            L = [ str(last_deltaY),",   ", str(posy), ", " , str(posx), "\n" ]  
            result_file.writelines(L) 
            read_status_register = 0 # put the into into file only once per read_motion_burst()
        if printed_lines > 20 :
            pass
            # break
    result_file.close() #to change file access modes
    return

def uint16_to_signed(val):
    if (val & (1 << 15)) != 0:  # If sign bit is set
        val = val - (1 << 16)  # Compute negative value
    return val
    
def plot_file( file1 ):
    # return
    plots = csv.reader(file1, delimiter=',')
    y0 = []
    y1 = []
    y2 = []
    for row in plots:
        y0.append(int(row[0]))
        y1.append(int(row[1]))
        y2.append(int(row[2]))
    #print(y0[0:200])
    plt.plot(y0,label="tool_size")
    plt.plot(y1,label="insertion")
    plt.plot(y2,label="torque")
    plt.xlabel('Time')
    plt.ylabel('Value')
    plt.title('tool_size, insertion and  torque"')
    plt.legend()
    plt.grid() # 2023_02_20 added.
    plt.show() 
    file1.close()    
    return


if __name__ == "__main__":
    main()
    
'''
2023_03_18
- to find the problem in  LogicAnalyzer_spi2csv that create 32 repeats of value in the output file

'''    