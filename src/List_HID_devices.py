# 2023_07_21__18_06 // add the manufacturer_name
import pywinusb.hid as win_hid

def list_hid_devices():
    all_devices = win_hid.HidDeviceFilter().get_devices()

    for device in all_devices:
        # or the VID of TI: 0x2047
        if device.vendor_id == 0x24B3 or device.vendor_id == 0x2047:
            # usage = device.usage
            vendor_id = device.vendor_id
            product_id = device.product_id
            serial_number = device.serial_number

            print(f"VID: {vendor_id:04X}, PID: {product_id:04X}, Serial Number: {serial_number}")

if __name__ == "__main__":
    list_hid_devices()
