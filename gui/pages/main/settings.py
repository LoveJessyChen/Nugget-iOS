from ..page import Page
from qt.ui_mainwindow import Ui_Nugget

from tweaks.tweaks import tweaks
from controllers.video_handler import set_ignore_frame_limit

class SettingsPage(Page):
    def __init__(self, window, ui: Ui_Nugget):
        super().__init__()
        self.window = window
        self.ui = ui

    def load_page(self):
        self.ui.allowWifiApplyingChk.toggled.connect(self.on_allowWifiApplyingChk_toggled)
        self.ui.autoRebootChk.toggled.connect(self.on_autoRebootChk_toggled)
        self.ui.showRiskyChk.toggled.connect(self.on_showRiskyChk_toggled)
        self.ui.showAllSpoofableChk.toggled.connect(self.on_showAllSpoofableChk_toggled)

        self.ui.revertRdarChk.toggled.connect(self.on_revertRdarChk_toggled)

        self.ui.skipSetupChk.toggled.connect(self.on_skipSetupChk_toggled)
        self.ui.supervisionChk.toggled.connect(self.on_supervisionChk_toggled)
        self.ui.supervisionOrganization.textEdited.connect(self.on_supervisionOrgTxt_textEdited)
        self.ui.resetPairBtn.clicked.connect(self.on_resetPairBtn_clicked)

    ## ACTIONS
    def on_allowWifiApplyingChk_toggled(self, checked: bool):
        self.window.device_manager.apply_over_wifi = checked
        # save the setting
        self.window.settings.setValue("apply_over_wifi", checked)
    def on_showRiskyChk_toggled(self, checked: bool):
        self.window.device_manager.allow_risky_tweaks = checked
        # save the setting
        self.window.settings.setValue("show_risky_tweaks", checked)
        # toggle the button visibility
        if checked:
            self.ui.advancedPageBtn.show()
            self.ui.ignorePBFrameLimitChk.show()
            try:
                self.ui.resetPBDrp.removeItem(4)
            except:
                pass
            self.ui.resetPBDrp.addItem("PB Extensions")
        else:
            self.ui.advancedPageBtn.hide()
            self.ui.ignorePBFrameLimitChk.hide()
            try:
                self.ui.resetPBDrp.removeItem(4)
            except:
                pass
    def on_ignorePBFrameLimitChk_toggled(self, checked: bool):
        set_ignore_frame_limit(checked)
        # save the setting
        self.window.settings.setValue("ignore_pb_frame_limit", checked)
    def on_showAllSpoofableChk_toggled(self, checked: bool):
        self.window.device_manager.show_all_spoofable_models = checked
        # save the setting
        self.window.settings.setValue("show_all_spoofable_models", checked)
        # refresh the list of spoofable models
        self.window.setup_spoofedModelDrp_models()
    def on_autoRebootChk_toggled(self, checked: bool):
        self.window.device_manager.auto_reboot = checked
        # save the setting
        self.window.settings.setValue("auto_reboot", checked)

    def on_revertRdarChk_toggled(self, checked: bool):
        tweaks["RdarFix"].set_enabled(checked)

    def on_skipSetupChk_toggled(self, checked: bool):
        self.window.device_manager.skip_setup = checked
        # save the setting
        self.window.settings.setValue("skip_setup", checked)
        # hide/show the warning label
        if checked:
            self.ui.skipSetupOnLbl.show()
        else:
            self.ui.skipSetupOnLbl.hide()
    def on_supervisionOrgTxt_textEdited(self, text: str):
        self.window.device_manager.organization_name = text
        self.window.settings.setValue("organization_name", text)
    def on_supervisionChk_toggled(self, checked: bool):
        self.window.device_manager.supervised = checked
        # save the setting
        self.window.settings.setValue("supervised", checked)

    # Device Options
    def on_resetPairBtn_clicked(self):
        self.window.device_manager.reset_device_pairing()