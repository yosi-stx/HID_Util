# file: PrimeVer.py
# by: YG.  (2020_07_17__18_33)
# modified by: YG.  (2022_10_25__17_29)
# Retrieve the FM version and Date from TI-file (*.txt)
# or Retrieve the FM version and Date from INTEL-HEX-file (*.HEX)
# or Retrieve the FM version and Date from binary file (*.bin)
# passing the argument to this python from cmd line.
# -
# example: 
# PrimeVer.py flex3.txt
# the output is: 
#                Version: 3.0.0
#                Date: 10.10.2017

# special treatment for Bootloader files that includes the 
# values of registers at address: 0x10001014  = UICR.NRFFW[0]
import tkinter
from tkinter import filedialog
import os
import sys
from binascii import hexlify

def print1(x):
    # print(x)
    return

def date2dec(x):
    s = "%02x" % x
    return s
    
root = tkinter.Tk()
root.withdraw() #use to hide tkinter window

currdir = os.getcwd()
if len(sys.argv) < 2:
    tempfile = filedialog.askopenfilename(parent=root, initialdir=currdir, title='Select a file',filetypes = (("FW files",("*.hex", "*.txt", "*.bin")),("txt files","*.txt"),("all files","*.*")))
else:
    tempfile = str(sys.argv[1])
    print( 'usage: PrimeVer.py <inputfile.txt> ')

# tempfile = "C:/Projects/inductive_ports/FLEX3/Debug/FLEX3.txt"
if len(tempfile) > 0:
    print( "You chose: %s" % tempfile)

file_extension = tempfile.split(".")  #split
file_extension = file_extension[len(file_extension)-1]
print1( "file_extension = %s" % file_extension )

if file_extension == "bin":
    print("this is a binarry file")
    # quit()
else:
    fhand = open(tempfile)

if file_extension == "bin":
    bin_fhand = open(tempfile,'rb')
    # print("read the bin file...")
    # read first 0x3f020 bytes from the image file:
    bin_fhand.read(0x3f020)
    version_line_number = 1 
    # quit()



if file_extension != "bin":
    number_line = 0
    version_line = 0
    version_line_number = 0
    for line in fhand:
      if file_extension == "hex":
        temp_line = line[0:15]
        number_line += 1
        # if the project mapping file will be changed: next line must be changed too
        if temp_line == ':020000040803EF':
          version_line_number = number_line + 3
          print1('number_line')
          print1(number_line)
          continue
      elif file_extension == "txt":
        temp_line = line[0:5]
        number_line += 1
        # if temp_line == '@fc00':  # this line is for TI file.
        if temp_line == '@fc00':
          version_line_number = number_line + 3
          print1('number_line')
          print1(number_line)
          continue
      else:
        print('unknown file extension, Try another file')
        
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

if file_extension == "hex":
    # for Prime based on STM32 MCU 
    print1(version_line[9:17])
    version_line = version_line[9:17]
    #01234567
    #62911660
    aligned_version = version_line[6:8] + version_line[4:6] + version_line[2:4] + version_line[0:2]
elif file_extension == "bin":
    # for Prime based on STM32 MCU (with bin file)
    val  = bin_fhand.read(4)
    print1("Read from file: %s" % hexlify(val))
    val_0 = val[0]
    val_1 = val[1]
    val_2 = val[2]
    val_3 = val[3]
    # print(date2dec(val_0))
    # print(date2dec(val_1))
    # print(date2dec(val_2))
    # print(date2dec(val_3))
    aligned_version = date2dec(val_3) + date2dec(val_2) + date2dec(val_1) + date2dec(val_0) 
    print1(aligned_version)
elif file_extension == "txt":
    # for Prime based on TI MSP430 MCU 
    print1(version_line[0:12])    
    aligned_version = version_line[9:11] + version_line[6:8] + version_line[3:5] + version_line[0:2]
else:
    print('unknown file extension, Try another file')

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



