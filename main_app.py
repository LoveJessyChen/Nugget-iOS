from exploit.restore import restore_files, FileToRestore, restore_file
from tweaks.tweaks import tweaks, TweakModifyType, FeatureFlagTweak, EligibilityTweak
from constants import Device

from pymobiledevice3.exceptions import PyMobileDevice3Exception
from pymobiledevice3.services.diagnostics import DiagnosticsService
from pymobiledevice3 import usbmux
from pymobiledevice3.lockdown import create_using_usbmux

from pathlib import Path
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

def get_apply_number(num: int) -> int:
    return num + 5-num%5

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
    print("v1.6")
    print("by LeminLimez")
    print("Thanks @disfordottie for the clock animation and @lrdsnow for EU Enabler\n")
    print("Please back up your device before using!")

    while device == None:
        connected_devices = usbmux.list_devices()
        # Connect via usbmuxd
        for current_device in connected_devices:
            if current_device.is_usb:
                try:
                    ld = create_using_usbmux(serial=current_device.serial)
                    vals = ld.all_values
                    device = Device(name=vals['DeviceName'], version=vals['ProductVersion'], model=vals['ProductType'], locale=ld.locale, ld=ld)
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
        print(f"\n{get_apply_number(num_tweaks + 1)}. Apply")
        print(f"{get_apply_number(num_tweaks + 1) + 1}. Remove All Tweaks")
        print("0. Exit\n")
        page = int(input("Enter a number: "))
        if page == get_apply_number(num_tweaks + 1) or page == get_apply_number(num_tweaks + 1) + 1:
            # either apply or reset tweaks
            print()
            resetting = page == (get_apply_number(num_tweaks + 1) + 1)
            # set the tweaks and apply
            # first open the file in read mode
            with open(gestalt_path, 'rb') as in_fp:
                gestalt_plist = plistlib.load(in_fp)
            # create the other plists
            flag_plist: dict = {}
            eligibility_files = None

            # verify the device credentials before continuing
            if gestalt_plist["CacheExtra"]["qNNddlUK+B/YlooNoymwgA"] != device.version or gestalt_plist["CacheExtra"]["0+nc/Udy4WNG8S+Q7a/s1A"] != device.model:
                print("com.apple.mobilegestalt.plist does not match the device!")
                input("Please make sure you are using the correct file!")
                continue # break applying and return to the main page
            
            # set the plist keys
            if not resetting:
                for tweak in tweaks:
                    if isinstance(tweak, FeatureFlagTweak):
                        flag_plist = tweak.apply_tweak(flag_plist)
                    elif isinstance(tweak, EligibilityTweak):
                        tweak.set_region_code(device.locale[-2:])
                        eligibility_files = tweak.apply_tweak()
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
            if eligibility_files != None:
                files_to_restore += eligibility_files
            # restore to the device
            try:
                restore_files(files=files_to_restore, reboot=True, lockdown_client=device.ld)
            except Exception as e:
                print(traceback.format_exc())
            finally:
                input("Press Enter to exit...")
                running = False
        elif page == 0:
            # exit the panel
            print("Goodbye!")
            running = False
        elif page == 69420:
            # bootloop device
            print("\n\n\nWARNING: You have chosen to bootloop your device.")
            print("I am not responsible for any data loss as a result of you choosing this option.")
            choice1 = input("Are you sure you want to continue? (y/n) ")
            if choice1.lower() == 'y':
                choice2 = input("\nAre you really sure you want to bootloop? (y/n) ")
                if choice2.lower() == 'y':
                    # they have chosen death, engage the bootloop
                    restore_files(
                            files=[FileToRestore(
                                    contents=b"",
                                    restore_path="/var/mobile/Library/Caches/TelephonyUI-9/", # writing to this folder bootloops
                                    restore_name="en-0---white.png"
                                )],
                            reboot=True,
                            lockdown_client=device.ld
                        )
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
                elif tweaks[page - 1].edit_type == TweakModifyType.PICKER:
                    # pick between values
                    print("\n\nSelect a value.")
                    print("If you do not know which to try, start with the first option.")
                    values = tweaks[page - 1].value
                    for option in range(len(values)):
                        print_option(
                                num=option+1,
                                active=(tweaks[page-1].enabled and tweaks[page-1].get_selected_option() == option),
                                message=str(values[option])
                            )
                    print_option(num=len(values)+1, active=(not tweaks[page-1].enabled), message="Disable")
                    picker_choice = int(input("Select option: "))
                    if picker_choice > 0 and picker_choice <= len(values):
                        tweaks[page-1].set_selected_option(picker_choice-1)
                    elif picker_choice == len(values)+1:
                        tweaks[page-1].set_enabled(False)
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
