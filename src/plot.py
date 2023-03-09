#!/usr/bin/python3
# C:\Work\Python\HID_Util\src\plot.py
# for plotting CSV files by using matplotlib and tkinter

# usage:
#       plot.py -o
#           or
#       plot.py "C:\Work\Python\HID_Util\src\log\hid_2021_03_11__12_14.csv"

import matplotlib.pyplot as plt
import numpy as np
import csv
import sys
from tkinter import *
# from tkinter import filedialog
from tkinter.filedialog import askopenfilename
import os

plot_version = "2023_03_09.a"
print("This Recorder Version: ",plot_version)

# from ctag_hid_log_files_path import *

FILE1_PATH = "log\hid_2022_06_30__23_33.csv"
# FILE2_PATH = "log\clicker_overSample.csv"
# "C:\Work\Python\HID_Util\src\log\hid_2022_06_30__23_33.csv"
filepath = "here_should_be_path"

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
        my_Path = "C:\\Work\\Python\\HID_Util\\src\\log"
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
            plot_file( file1, filepath )
            
        else:
            file1 = open(cap_file,"r+")
            plot_file( file1, cap_file )
    except FileNotFoundError:
        print("Bad file path in user input argument: %s  !!!" % cap_file)
        return
    exit()
    return
        
def plot_file( file1, file_name ):
    # return
    plots = csv.reader(file1, delimiter=',')
    y0 = []
    y1 = []
    y2 = []
    y3 = []
    for row in plots:
        y0.append(int(row[0]))
        y1.append(int(row[1]))
        y2.append(int(row[2]))
        y3.append(int(row[3]))

    # WinMove, ,,367,144,1358,598
    # resize the figure to w: 1358	h: 598
    my_dpi = 96 # by calculating width resolution / screen size = 2560/31.25' = 81.9
    # plt.figure(figsize=(1358/my_dpi, 598/my_dpi), dpi=my_dpi)
    height_fix =  598/671 # from measuring the actual results.
    plt.figure(figsize=(13.58, 5.98*height_fix), dpi=100)

    #print(y0[0:200])
    plt.plot(y0,label="tool_size")
    # plt.plot(y0,label="Delta_insertion")
    plt.plot(y1,marker='o',label="insertion")
    plt.plot(y2,label="torque")
    plt.plot(y3,label="image_quality")  # 2023_03_09 added.
    # plt.xlabel('Time')
    display_f_name = file_name.split('\\')
    display_f_n = display_f_name[len(display_f_name)-1]
    text = 'Time...' + "\n" + display_f_n
    plt.xlabel(text)
    plt.ylabel('Value')
    # plt.title('tool_size, insertion and  torque"')
    # plt.title('Delta_insertion, insertion and  torque"')
    #plt.suptitle(file_name) 
    # plt.suptitle(file_name, x=0.5, y=1.05, fontsize=16, fontweight="bold")    
    # https://matplotlib.org/stable/api/text_api.html#matplotlib.text.Text.set_fontweight
    plt.title(display_f_n,fontsize=10, fontweight="ultralight")    
    # text = 'tool_size, insertion, torque and image_quality' + "\n" + file_name
    # plt.title('tool_size, insertion, torque and image_quality "', fontweight="bold")
    plt.suptitle('tool_size, insertion, torque and image_quality', fontsize=16, fontweight="bold")
    
    # plt.title(text)
    plt.legend()
    plt.grid() # 2023_02_20 added.
    plt.show() 
    file1.close()    
    return


if __name__ == "__main__":
    main()


'''
history changes
2023_03_09 
- adding image_quality to recording. 
- resize the figure to w: 1358	h: 598
- adding csv file name to title 

'''            