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

plot_version = "2023_10_19.a"
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
    use_legend  = 1

    if len(sys.argv) != 2:
        print("Usage: %s \"path/to/log_file.csv\"" % (sys.argv[0],))
        print("      or")
        print("      plot.py -0        // to select input file")
        print("      or")
        print("      plot.py -g        // plot without legends")
        return

    if sys.argv[1] == "-g" :
        use_legend  = 0

    if sys.argv[1] == "-o" or sys.argv[1] == "-g" :
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
            # csv_size( file1, filepath )
            plot_file( file1, filepath, use_legend )
            
        else:
            file1 = open(cap_file,"r+")
            # csv_size( file1, cap_file )
            plot_file( file1, cap_file, use_legend )
    except FileNotFoundError:
        print("Bad file path in user input argument: %s  !!!" % cap_file)
        return
    exit()
    return

def is_comment(line):
    return line.startswith('#')

def csv_size( file1, file_name ):   # not in use now 2023_10_03
    # return
    # plots = csv.reader(file1, delimiter=',')
    
    # use filter to disregard recording lines with '#', according to :
    # https://stackoverflow.com/questions/14158868/python-skip-comment-lines-marked-with-in-csv-dictreader
    plots = csv.DictReader(filter(lambda row: row[0]!='#', file1))
    print("csv size:")
    rows = 0
    columns = 0
    for temp in plots:
        rows += 1
        if len(temp) > columns:
            columns = len(temp)
    print("Number of rows:", rows)
    print("Number of columns:", columns)
    return(rows,columns)

def get_info( file1, field):
    # search for gap indication in the file:
    i = 0
    gap = 1
    for line in file1:
        i += 1
        if i>5:
            break
        print(line,end='')
        # if "gap" in line:
        if field in line:
            line = line.rstrip()
            L = line.split('=')
            print(L)
            gap= int(L[1])
            # sampling_gap = gap
            print("recording sampling gap: %d ..." %(gap))
            return gap
    # field was not found
    print("field: '%s' was not found!!!" %(field))
    return gap

def get_columns_info( file1, field):
    # search for gap indication in the file:
    i = 0
    labels = None
    for line in file1:
        i += 1
        if i>5:
            break
        print(line,end='')
        # if "gap" in line:
        if field in line:
            line = line.rstrip()
            L = line.split('=')
            print(L)
            labels= L[1]
            # sampling_gap = gap
            print("labels are: %s ..." %(labels))
            return labels
    # field was not found
    print("field: '%s' was not found!!!" %(field))
    return labels


def plot_file( file1, file_name, use_legend):
    # return
    sampling_gap = 1
    sampling_gap = get_info(file1,"gap")
    columns_info = get_columns_info( file1, "columns")
    print("from csv file columns line: %s" %(columns_info) )
    if columns_info != None:
        columns_labals = columns_info.split(',')
        print("from csv file columns_labals: ",columns_labals )
        print("len(columns_labals): %d" %(len(columns_labals)) )
    file1.seek(0) # to start from begining of the file.
    # plots = csv.reader(file1, delimiter=',')
    plots = csv.DictReader(filter(lambda row: row[0]!='#', file1))
    print("csv size:")
    rows = 0
    columns = 0
    for temp in plots:
        rows += 1
        if len(temp) > columns:
            columns = len(temp)
    print("Number of rows:", rows)
    print("Number of columns:", columns)
    # iterate over the columns for get the keys:
    print(temp)
    all_keys = list(temp.keys())
    # print(all_keys[0],all_keys[1])
    use_dictionary = 1
    print("all_keys: ")
    for i in range(columns):
        print(all_keys[i],end='')
    print('')
       
    # plots = csv.reader(file1, delimiter=',')
    plots = csv.DictReader(filter(lambda row: row[0]!='#', file1))
    y0 = []
    y1 = []
    y2 = []
    y3 = []
    t  = []
    file1.seek(0) # to start from begining of the file.
    for row in plots:
        # print(row)
        # t.append(0.004)
        if use_dictionary == 0:
            y0.append(int(row[0]))
            y1.append(int(row[1]))
            if columns > 2:  #len(row) > 2:
                y2.append(int(row[2]))
            if columns > 3:  #len(row) > 3:
                y3.append(int(row[3]))
        else:
            y0.append(int(row[all_keys[0]]))
            y1.append(int(row[all_keys[1]]))
            if columns > 2:  #len(row) > 2:
                y2.append(int(row[all_keys[2]]))
            if columns > 3:  #len(row) > 3:
                y3.append(int(row[all_keys[3]]))

    t = np.arange(0, len(y0)*0.004*sampling_gap, 0.004*sampling_gap)  # create t list with increments of 0.004
    print("length of(t)= ",len(t))
    # WinMove, ,,367,144,1358,598
    # resize the figure to w: 1358	h: 598
    my_dpi = 96 # by calculating width resolution / screen size = 2560/31.25' = 81.9
    # plt.figure(figsize=(1358/my_dpi, 598/my_dpi), dpi=my_dpi)
    height_fix =  598/671 # from measuring the actual results.
    plt.figure(figsize=(13.58, 5.98*height_fix), dpi=100)

    #print(y0[0:200])
    # plt.plot(y0,marker='o',label="tool_size")
    last = len(y0)
    t = t[0:last] # truncate the time vector to match the recording vector
    print("new length of(t)= ",len(t))
    if columns == len(columns_labals):
        use_columns_labals = 1
    else:
        use_columns_labals = 0
        
    if use_columns_labals:
        plt.plot(t,y0,marker='o',label=columns_labals[0])
    else:
        plt.plot(t,y0,marker='o',label="tool_size")
    # plt.plot(t,y0,marker='o',label="Delta_Y")
    if use_columns_labals:
        plt.plot(t,y1,marker='o',label=columns_labals[1])
    else:
        plt.plot(t,y1,marker='o',label="insertion")

    try:
        if use_columns_labals:
            plt.plot(t,y2,label=columns_labals[2])
        else:
            plt.plot(t,y2,label="torque")
    except:
        print("Bad file: first line dont have descriptions !!!")
        print("used only the remaining columns")
    if columns > 3:
        if use_columns_labals:
            plt.plot(t,y3,label=columns_labals[3]) 
        else:
            plt.plot(t,y3,label="image_quality")  # 2023_03_09 added.

    # plt.xlabel('Time')
    display_f_name = file_name.split('\\')
    display_f_n = display_f_name[len(display_f_name)-1]
    # text = 'Time...' + "\n" + display_f_n
    text = 'Time...' + "(sampling gap =" + str(sampling_gap) + ")" + "\n" + display_f_n
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
    if use_legend:
        if use_columns_labals:
            plt.suptitle(columns_info, fontsize=16, fontweight="bold")
        else:
            plt.suptitle('tool_size, insertion, torque and image_quality', fontsize=16, fontweight="bold")
        # plt.suptitle('Delta_Y, insertion, torque and image_quality', fontsize=16, fontweight="bold")
    
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
- be able to plot also 3 column csv files.
2023_10_03
- using csv.DictReader instead of csv.reader
- add support of comments in the csv file.
- adding support of sampling_gap in csv file.
2023_10_13
- fix bug of: "x and y must have same first dimension" in plt.plot(t,y0...)
2023_10_19
- add get_columns_info() function.
- create automatic mechanism for parsing and deployment of meta date in CSV file into the plot
'''            