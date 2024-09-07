from constants import Version
from .tweak_classes import MobileGestaltTweak, MobileGestaltMultiTweak, MobileGestaltPickerTweak, FeatureFlagTweak, TweakModifyType
from .eligibility_tweak import EligibilityTweak

    
tweaks = [
    MobileGestaltPickerTweak("Toggle Dynamic Island", "oPeik/9e8lQWMszEjbPzng", "ArtworkDeviceSubType", [2556, 2796]),
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
    MobileGestaltTweak("Toggle Internal Storage (WARNING: May be risky for some devices)", "InternalBuild", divider_below=True),
    EligibilityTweak("EU Enabler", divider_below=True),
    MobileGestaltMultiTweak("Always On Display",
                            {"DeviceSupportsAlwaysOnDisplay": True, "DeviceSupportsAlwaysOnTime": True},
                            min_version=Version("18.0"), divider_below=True),
    FeatureFlagTweak("Toggle Lockscreen Clock Animation and more", flag_category='SpringBoard',
                     flag_names=['AutobahnQuickSwitchTransition', 'SlipSwitch', 'PosterEditorKashida', 'SwiftUITimeAnimation'],
                     min_version=Version("18.0")),
    FeatureFlagTweak("Enable Old Photo UI", flag_category='Photo', flag_names=['Lemonade'], is_list=False, inverted=True, min_version=Version("18.0")),
    FeatureFlagTweak("Enable Apple Intelligence", flag_category='SpringBoard', flag_names=['Domino', 'SuperDomino'], min_version=Version("18.1"))
]