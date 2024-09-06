from enum import Enum
from constants import Version

class TweakModifyType(Enum):
    TOGGLE = 1
    TEXT = 2

class Tweak:
    def __init__(
            self, label: str,
            key: str, subkey: str = None,
            value: any = True,
            edit_type: TweakModifyType = TweakModifyType.TOGGLE,
            min_version: Version = Version("1.0"),
            divider_below: bool = False
        ):
        self.label = label
        self.key = key
        self.subkey = subkey
        self.value = value
        self.min_version = min_version
        self.edit_type = edit_type
        self.divider_below = divider_below
        self.enabled = False

    def set_enabled(self, value: bool):
        self.enabled = value
    def toggle_enabled(self):
        self.enabled = not self.enabled
    def set_value(self, new_value: any):
        self.value = new_value
        self.enabled = True

    def is_compatible(self, device_ver: str):
        return Version(device_ver) >= self.min_version

    def apply_tweak(self):
        raise NotImplementedError


class MobileGestaltTweak(Tweak):
    def apply_tweak(self, plist: dict):
        if not self.enabled:
            return plist
        new_value = self.value
        if self.subkey == None:
            plist["CacheExtra"][self.key] = new_value
        else:
            plist["CacheExtra"][self.key][self.subkey] = new_value
        return plist
    
class MobileGestaltMultiTweak(Tweak):
    def __init__(self, label: str, keyValues: dict, min_version: Version = Version("1.0"), divider_below: bool = False):
        super().__init__(label=label, key=None, min_version=min_version, divider_below=divider_below)
        self.keyValues = keyValues
        # key values looks like ["key name" = value]

    def apply_tweak(self, plist: dict):
        if not self.enabled:
            return plist
        for key in self.keyValues:
            plist["CacheExtra"][key] = self.keyValues[key]
        return plist
    
class FeatureFlagTweak(Tweak):
    def __init__(
            self, label: str,
                flag_category: str, flag_names: list,
                is_list: bool=True, inverted: bool=False,
                min_version: Version = Version("1.0"),
                divider_below: bool = False
            ):
        super().__init__(label=label, key=None, min_version=min_version, divider_below=divider_below)
        self.flag_category = flag_category
        self.flag_names = flag_names
        self.is_list = is_list
        self.inverted = inverted
        
    def apply_tweak(self, plist: dict):
        to_enable = self.enabled
        if self.inverted:
            to_enable = not self.enabled
        # create the category list if it doesn't exist
        if not self.flag_category in plist:
            plist[self.flag_category] = {}
        for flag in self.flag_names:
            if self.is_list:
                plist[self.flag_category][flag] = {
                    'Enabled': to_enable
                }
            else:
                plist[self.flag_category][flag] = to_enable
        return plist
    
tweaks = [
    MobileGestaltTweak("Toggle Dynamic Island", "oPeik/9e8lQWMszEjbPzng", "ArtworkDeviceSubType", 2796),
    MobileGestaltTweak("Set Device Model Name", "oPeik/9e8lQWMszEjbPzng", "ArtworkDeviceProductDescription", "", TweakModifyType.TEXT),
    # MobileGestaltTweak("Fix Dynamic Island", "YlEtTtHlNesRBMal1CqRaA"),
    # MobileGestaltTweak("Set Dynamic Island Location", "Zg7DduDoSCy6vY6mhy3n2w", value="{ x: 390.000000, y: 205.848432, width: 50.000000, height: 105.651573 }"), # not sure what value this is supposed to be but it removes the island currently
    MobileGestaltTweak("Toggle Boot Chime", "DeviceSupportsBootChime"),
    MobileGestaltTweak("Toggle Charge Limit", "DeviceSupports80ChargeLimit"),
    MobileGestaltTweak("Disable Wallpaper Parallax", "UIParallaxCapability", value=False),
    MobileGestaltTweak("Toggle Stage Manager Supported (WARNING: risky on some devices, mainly phones)", "DeviceSupportsEnhancedMultitasking", value=1),
    MobileGestaltMultiTweak("Disable Region Restrictions (ie. Shutter Sound)", {"h63QSdBCiT/z0WU6rdQv6Q": "US", "zHeENZu+wbg7PUprwNwBWg": "LL/A"}),
    MobileGestaltTweak("Toggle Apple Pencil", "DeviceSupportsApplePencil"),
    MobileGestaltTweak("Toggle Action Button", "RingerButtonCapability"),
    MobileGestaltTweak("Toggle Internal Storage (WARNING: May be risky for some devices)", "InternalBuild"),
    MobileGestaltMultiTweak("Always On Display",
                            {"DeviceSupportsAlwaysOnDisplay": True, "DeviceSupportsAlwaysOnTime": True},
                            min_version=Version("18.0"), divider_below=True),
    FeatureFlagTweak("Toggle Lockscreen Clock Animation and more", flag_category='SpringBoard',
                     flag_names=['AutobahnQuickSwitchTransition', 'SlipSwitch', 'PosterEditorKashida', 'SwiftUITimeAnimation'],
                     min_version=Version("18.0")),
    FeatureFlagTweak("Enable Old Photo UI", flag_category='Photo', flag_names=['Lemonade'], is_list=False, inverted=True, min_version=Version("18.0")),
    FeatureFlagTweak("Enable Apple Intelligence", flag_category='SpringBoard', flag_names=['Domino', 'SuperDomino'], min_version=Version("19.0")) # note: this doesn't work
]