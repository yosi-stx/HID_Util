# HID_UTILL

## Prerequisites
```
1)pip3 install hid
2)Copy the 2 dll's that are in "x64" folder into:
C:\Windows\System32
```

## Installation
Your installtion folder should look like this:
```
.
├── install_folder
│   ├── HID_UTILL.py
│   ├── include_dll_path
│   │   └── __init__.py
│   ├── x64
│   │   └── hidapi.dll
│   └── x86
│       └── hidapi.dll
```

## fixing issue with hid lib:
2023_04_26 found out issue: 
import hid
```
AttributeError: function 'hid_get_input_report' not found
```
solution:
```
pip uninstall hid
pip install hid==1.0.4
```

the solution is from this [thread](https://github.com/Poohl/joycontrol/issues/17#issuecomment-1253062321) which describes that new “hid” using the new symbol 
that is not yet supported by the old shared object

