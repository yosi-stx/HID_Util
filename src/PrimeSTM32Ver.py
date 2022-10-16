# file: PrimeSTM32Ver.py
# by: YG.  (2022_10_16__13_39)
# Retrive the FM version and Date from INTEL-HEX-file (*.HEX)
# passing the argument to this python from cmd line.
# -
# example: 
# PrimeSTM32Ver.py Prime_L552.hex
# the output is: 
#                FW version: 6.0.2
#                FW date   : 22/09/2022

#                Version: 3.0.0
#                Date: 10.10.2017

# algorithm:
# the offset of PAR32_VERSION_VALUE is: 8*PAR8 + 8*PAR16 + 2*PAR32 = 8+16+8 = 32bytes offset.
# // need to look for line start with: :10F020 
# // and focus on the 9-th byte after the ":"

# special treatment for Bootloader files that includes the 
# values of registers at address: 0x10001014  = UICR.NRFFW[0]
import tkinter
from tkinter import filedialog
import os
import sys

def print1(x):
    print(x)
    return
    
root = tkinter.Tk()
root.withdraw() #use to hide tkinter window

currdir = os.getcwd()
if len(sys.argv) < 2:
    tempfile = filedialog.askopenfilename(parent=root, initialdir=currdir, title='Select a file',filetypes = (("FW files",("*.hex", "*.txt")),("txt files","*.txt"),("all files","*.*")))
else:
    tempfile = str(sys.argv[1])
    print( 'usage: PrimeVer.py <inputfile.txt> ')

# tempfile = "C:/Projects/inductive_ports/FLEX3/Debug/FLEX3.txt"
if len(tempfile) > 0:
    print( "You chose: %s" % tempfile)

file_extention = tempfile.split(".")  #split
file_extention = file_extention[len(file_extention)-1]
print1( "file_extention = %s" % file_extention )

fhand = open(tempfile)

number_line = 0
version_line = 0
version_line_number = 0
for line in fhand:
  temp_line = line[0:15]
  number_line += 1
  # if temp_line == '@fc00':  # this line is for TI file.
  #if temp_line == ':10F020':
  if temp_line == ':020000040803EF':
    version_line_number = number_line + 3
    #version_line_number = number_line # since 10F020 includes the offset from 10F000
    print1('number_line')
    print1(number_line)
    continue
  if number_line == version_line_number:
    version_line = line

#define VERSION_PRIMARY         3
#define VERSION_SECONDARY       0
#define VERSION_BUILD_DAY       10
#define VERSION_BUILD_MONTH     10
#define VERSION_BUILD_YEAR      17
#define VERSION_BUILDER         0
#define PAR32_VERSION_VALUE ( \

    # (((uint32_t)VERSION_PRIMARY     << 28) & 0xF0000000) | \
    # (((uint32_t)VERSION_SECONDARY   << 24) & 0x0F000000) | \
    # (((uint32_t)VERSION_BUILD_DAY   << 16) & 0x00FF0000) | \
    # (((uint32_t)VERSION_BUILD_MONTH << 12) & 0x0000F000) | \
    # (((uint32_t)VERSION_BUILD_YEAR  <<  4) & 0x00000FF0) | \
    # (((uint32_t)VERSION_BUILDER     <<  0) & 0x0000000F) )
#10 A1 0A 30
 
if version_line_number == 0:
    print('\nThere is no version indication in this image file!!!')
    print('Try another file')
    quit()

print1(version_line[9:17])
version_line = version_line[9:17]
#01234567
#62911660
aligned_version = version_line[6:8] + version_line[4:6] + version_line[2:4] + version_line[0:2]
print1(aligned_version)
VERSION_PRIMARY = aligned_version[0]
print1("VERSION_PRIMARY   %s" % aligned_version[0])
print1("VERSION_SECONDARY %s" % aligned_version[1])
VERSION_BUILDER = aligned_version[7:8]
print1("VERSION_BUILDER   %d" % int(VERSION_BUILDER,16))
print()
print("Version: %s.%s.%d" % (aligned_version[0], aligned_version[1], int(VERSION_BUILDER,16)) )
print()
VERSION_BUILD_DAY = aligned_version[2:4]
print1("VERSION_BUILD_DAY   %d" % int(VERSION_BUILD_DAY,16))
VERSION_BUILD_MONTH = aligned_version[4:5]
print1("VERSION_BUILD_MONTH %d" % int(VERSION_BUILD_MONTH,16))
VERSION_BUILD_YEAR = aligned_version[5:7]
print1("VERSION_BUILD_YEAR  20%d" % int(VERSION_BUILD_YEAR,16))
print("Date: %d.%d.20%d" % (int(VERSION_BUILD_DAY,16), int(VERSION_BUILD_MONTH,16), int(VERSION_BUILD_YEAR,16)) )



