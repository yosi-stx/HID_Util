@echo off
echo Create a local backup  --
echo This script makes a local backup to folder  C:\Work\Python\HID_Util\src\history_py_files
echo the sub folder will include in its name the environment variables %%date%% and %%time%%.
echo environment variables %%date%% and %%time%%.
echo -
echo #######################################
echo ###                                ####
echo ###  BACK UP OF "HID_UTILL"        ####
echo ###                                ####
echo ###                                ####
echo #######################################
REM pause
REM C:\Work\Python\HID_Util\src\local_backup_HID_Utill.bat
REM file:///C:/Work/Python/HID_Util/src/local_backup_HID_Utill.bat

REM sourcepath
REM "C:\Work\Python\HID_Util\src\HID_UTILL.py"
REM destpath
REM "C:\Work\Python\HID_Util\src\history_py_files\HID_UTILL.py"

copy "C:\Work\Python\HID_Util\src\HID_UTILL.py" "C:\Work\Python\HID_Util\src\history_py_files\HID_UTILL.py"

goto SKIP_TO_HERE

mkdir C:\Backup\Prime_L552\temp

:: XCOPY *.* D:\Mydir /EXCLUDE:
:: for first init use: Arthro_MSP430f5529 - 2019_07_19Copy
REM SET sourcepath="C:\Projects\C_TAG\SourceCTAG\YG_ctag\Arthro_MSP430f5529 - 2019_07_19Copy\"

SET sourcepath="C:\Work\ST\workspace_1.6.0\Prime_L552\"
SET destpath="C:\BackUp\Prime_L552\temp\"
xcopy %sourcepath%*.H  %destpath%*.H /E 
xcopy %sourcepath%*.C  %destpath%*.C /E 


:: special files for project
xcopy %sourcepath%*.map  %destpath%*.map /E
::xcopy %sourcepath%*.srec  %destpath%*.srec /E
xcopy %sourcepath%*.bat  %destpath%*.bat /E
::xcopy %sourcepath%*.exe  %destpath%*.exe /E
xcopy %sourcepath%*.hex  %destpath%*.hex /E
xcopy %sourcepath%*.txt  %destpath%*.txt /E
::xcopy %sourcepath%*.as  %destpath%*.as /E
xcopy %sourcepath%*.csv  %destpath%*.csv /E
xcopy %sourcepath%*.bin  %destpath%*.bin /E

:: New ones:
:: Version .cproject .cdtproject .cdtbuild .ccxml .ccsproject 
:: .project .cmd .opt .launch 
:: xcopy %sourcepath%Version.*        %destpath%Version.*
REM echo f | xcopy /f /y srcfile destfile
echo f | xcopy  /f /y %sourcepath%.cproject     %destpath%.cproject   
echo f | xcopy  /f /y %sourcepath%.cdtproject   %destpath%.cdtproject
echo f | xcopy  /f /y %sourcepath%.ccsproject   %destpath%.ccsproject /E
echo f | xcopy  /f /y %sourcepath%.project      %destpath%.project    /E
REM new one for stm32..
echo f | xcopy  /f /y %sourcepath%.mxproject    %destpath%.mxproject    /E
echo f | xcopy  /f /y %sourcepath%.gitignore    %destpath%.gitignore    /E
REM echo f | xcopy  /f /y %sourcepath%Prime_L552.ico    %destpath%Prime_L552.ico    /E
echo f | xcopy  /f /y %sourcepath%Prime_L552.ioc  %destpath%Prime_L552.ioc    /E

REM when there are file names with name before the point, the xcopy does it work
xcopy %sourcepath%*.cdtbuild     %destpath%*.cdtbuild   /E
xcopy %sourcepath%*.ccxml        %destpath%*.ccxml      /E
xcopy %sourcepath%*.cmd          %destpath%*.cmd        /E
xcopy %sourcepath%*.opt          %destpath%*.opt        /E
REM C:\Work\ST\workspace_1.6.0\Prime_L552\Core\Startup\startup_stm32l552zetxq.s
xcopy %sourcepath%startup_stm32*.s          %destpath%startup_stm32*.s        /E
REM there is a problem since there is space in the name of the next file:
xcopy %sourcepath%*.launch       %destpath%*.launch     /E
REM new ones for stm32..
REM xcopy %sourcepath%Prime_L552.ioc          %destpath%Prime_L552.ioc     /E
xcopy %sourcepath%*.ld           %destpath%*.ld     /E
:: Docklight file:
REM xcopy %sourcepath%*.ptp       %destpath%*.ptp     /E

:SKIP_TO_HERE
rem goto END

@echo on
REM C:
REM cd\
REM cd Backup
cd history_py_files
REM pause
dir
@echo on
rem               Year         Month        Day

IF %time:~-11,2% LSS 10 GOTO THREE
IF %time:~-11,2% GEQ 10 GOTO TWO
GOTO ONE
GOTO END
rem if date format 29-12-15  
rem    use:: 20%date:~-2,2%%date:~-5,2%%date:~-8,2%
rem else
rem    use:: %date:~-4,4%%date:~-10,2%%date:~-7,2%
:THREE
ECHO time is before 10
REM ren temp Boot_nRF52_20%date:~-2,2%%date:~-5,2%%date:~-8,2%_0%time:~-10,1%-%time:~-8,2%
REM the following line is for win10
ren temp ws_%date:~-4,4%%date:~-10,2%%date:~-7,2%_0%time:~-10,1%-%time:~-8,2%
GOTO END
:TWO
ECHO time is after 9

REM ren temp Boot_nRF52_20%date:~-2,2%%date:~-5,2%%date:~-8,2%_%time:~-11,2%-%time:~-8,2%
REM the following line is for win10
ren HID_UTILL.py HID_UTILL_%date:~-4,4%%date:~-10,2%%date:~-7,2%__%time:~-11,2%_%time:~-8,2%.py
GOTO END
:ONE
ECHO nothing is done, please debug BACKUP batch file

:END

REM pause
dir
echo test time format
echo %time:~-11,2%-%time:~-8,2%
cd..
@echo off

echo #######################################
echo ###                                ####
echo ###  BACK UP     DONE!!!!          ####
echo ###                                ####
echo #######################################
REM color printing to console 
REM \033[47m\033[31mhello 1\033[0m
echo [47m[31m look for in the dir above for file named: 1[0m
echo [47m[31m HID_UTILL_%date:~-4,4%%date:~-10,2%%date:~-7,2%__%time:~-11,2%_%time:~-8,2%.py  1[0m
echo [47m[31m if you don't find it, run this from CMD not from notepadd++ 1[0m
echo look for in the dir above for file named:
echo HID_UTILL_%date:~-4,4%%date:~-10,2%%date:~-7,2%__%time:~-11,2%_%time:~-8,2%.py
color
pause

