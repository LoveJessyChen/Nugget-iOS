from exploit.restore import restore_files, FileToRestore, restore_file
from tweaks import tweaks, TweakModifyType, FeatureFlagTweak
from constants import Device

from pymobiledevice3.exceptions import PyMobileDevice3Exception
from pymobiledevice3.services.diagnostics import DiagnosticsService
from pymobiledevice3 import usbmux
from pymobiledevice3.lockdown import create_using_usbmux

from pathlib import Path
from tempfile import TemporaryDirectory
import plistlib
import traceback

running = True
passed_check = False
num_tweaks = len(tweaks)

gestalt_path = Path.joinpath(Path.cwd(), "com.apple.MobileGestalt.plist")
flags_path = Path.joinpath(Path.cwd(), "Global.plist")
device = None

def print_option(num: int, active: bool, message: str):
    txt = str(num) + ". "
    if active:
        txt = txt + "[Y] "
    txt = txt + message
    print(txt)

while running:
    print("""\n\n\n\n
                                                                      
         ,--.                                                         
       ,--.'|                                                 ___     
   ,--,:  : |                                               ,--.'|_   
,`--.'`|  ' :         ,--,                                  |  | :,'  
|   :  :  | |       ,'_ /|  ,----._,.  ,----._,.            :  : ' :  
:   |   \\ | :  .--. |  | : /   /  ' / /   /  ' /   ,---.  .;__,'  /   
|   : '  '; |,'_ /| :  . ||   :     ||   :     |  /     \\ |  |   |    
'   ' ;.    ;|  ' | |  . .|   | .\\  .|   | .\\  . /    /  |:__,'| :    
|   | | \\   ||  | ' |  | |.   ; ';  |.   ; ';  |.    ' / |  '  : |__  
'   : |  ; .':  | : ;  ; |'   .   . |'   .   . |'   ;   /|  |  | '.'| 
|   | '`--'  '  :  `--'   \\`---`-'| | `---`-'| |'   |  / |  ;  :    ; 
'   : |      :  ,      .-./.'__/\\_: | .'__/\\_: ||   :    |  |  ,   /  
;   |.'       `--`----'    |   :    : |   :    : \\   \\  /    ---`-'   
'---'                       \\   \\  /   \\   \\  /   `----'              
                             `--`-'     `--`-'                        
    """)
    print("by LeminLimez")
    print("Thanks @disfordottie for the clock animation")
    print("v1.5.1\n")
    print("Please back up your device before using!")

    while device == None:
        connected_devices = usbmux.list_devices()
        # Connect via usbmuxd
        for current_device in connected_devices:
            if current_device.is_usb:
                try:
                    ld = create_using_usbmux(serial=current_device.serial)
                    vals = ld.all_values
                    device = Device(name=vals['DeviceName'], version=vals['ProductVersion'], model=vals['ProductType'], ld=ld)
                except Exception as e:
                    print(traceback.format_exc())
                    input("Press Enter to continue...")
        
        if device == None:
            print("Please connect your device and try again!")
            input("Press Enter to continue...")

    print(f"Connected to {device.name}\niOS {device.version}\n")
    
    if not passed_check and Path.exists(gestalt_path) and Path.is_file(gestalt_path):
        passed_check = True
    
    if passed_check:
        for n in range(num_tweaks):
            # do not show if the tweak is not compatible
            if tweaks[n].is_compatible(device.version):
                print_option(n + 1, tweaks[n].enabled, tweaks[n].label)
                if tweaks[n].divider_below:
                    print()

        # apply will still be the number of tweaks just to keep consistency
        print(f"\n{num_tweaks + 1}. Apply")
        print("0. Exit\n")
        page = int(input("Enter a number: "))
        if page == num_tweaks + 1:
            print()
            # set the tweaks and apply
            # first open the file in read mode
            with open(gestalt_path, 'rb') as in_fp:
                gestalt_plist = plistlib.load(in_fp)
            # create the other plists
            flag_plist: dict = {}

            # verify the device credentials before continuing
            if gestalt_plist["CacheExtra"]["qNNddlUK+B/YlooNoymwgA"] != device.version or gestalt_plist["CacheExtra"]["0+nc/Udy4WNG8S+Q7a/s1A"] != device.model:
                print("com.apple.mobilegestalt.plist does not match the device!")
                input("Please make sure you are using the correct file!")
                continue # break applying and return to the main page
            
            # set the plist keys
            for tweak in tweaks:
                if isinstance(tweak, FeatureFlagTweak):
                    flag_plist = tweak.apply_tweak(flag_plist)
                else:
                    gestalt_plist = tweak.apply_tweak(gestalt_plist)

            # create the restore file list
            files_to_restore = [
                FileToRestore(
                    contents=plistlib.dumps(gestalt_plist),
                    restore_path="/var/containers/Shared/SystemGroup/systemgroup.com.apple.mobilegestaltcache/Library/Caches/",
                    restore_name="com.apple.MobileGestalt.plist"
                ),
                FileToRestore(
                    contents=plistlib.dumps(flag_plist),
                    restore_path="/var/preferences/FeatureFlags/",
                    restore_name="Global.plist"
                )
            ]
            # restore to the device
            try:
                restore_files(files=files_to_restore)
            except PyMobileDevice3Exception as e:
                if "Find My" in str(e):
                    print("Find My must be disabled in order to use this tool.")
                    print("Disable Find My from Settings (Settings -> [Your Name] -> Find My) and then try again.")
                elif "crash_on_purpose" not in str(e):
                    raise e
                else:
                    print("Success! Rebooting your device...")
                    with DiagnosticsService(device.ld) as diagnostics_service:
                        diagnostics_service.restart()
                    print("Remember to turn Find My back on!")
            except Exception as e:
                print(traceback.format_exc())
            finally:
                input("Press Enter to exit...")
                running = False
        elif page == 0:
            # exit the panel
            print("Goodbye!")
            running = False
        else:
            if page > 0 and page <= num_tweaks and tweaks[page - 1].is_compatible(device.version):
                if tweaks[page - 1].edit_type == TweakModifyType.TEXT:
                    # text input
                    # for now it is just for set model, deal with a fix later
                    print("\n\nSet Model Name")
                    print("Leave blank to turn off custom name.\n")
                    name = input("Enter Model Name: ")
                    if name == "":
                        tweaks[page - 1].set_enabled(False)
                    else:
                        tweaks[page - 1].set_value(name)
                else:
                    tweaks[page - 1].toggle_enabled()
    else:
        print("No MobileGestalt file found!")
        print(f"Please place the file in \'{Path.cwd()}\' with the name \'com.apple.MobileGestalt.plist\'")
        print("Remember to make a backup of the file!!\n")
        print("1. Retry")
        print("2. Enter path\n")
        choice = int(input("Enter number: "))
        if choice == 2:
            new_path = input("Enter new path to file: ")
            gestalt_path = Path(new_path)
