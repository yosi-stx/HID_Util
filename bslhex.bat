@echo off
REM file name: bslhex.bat
echo v_id is %1
echo p_id is %2
set /A v_id=0x%1%
set /A p_id=0x%2%
@echo on
bsl2 -v %v_id% -p %p_id%

REM credit:
REM this batch file is based on information from the following link:
REM https://stackoverflow.com/questions/33005186/hexadecimal-to-decimal-batch-file

REM usage example:
REM bslhex 2047 307
REM - 
REM result in:
REM bsl2 -v 8263 -p 775