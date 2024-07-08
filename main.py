import json
import time
import shutil

from settings._pym_settings import secrets_main, data_base
from dict_for_fermion import Dict_For_Fermion
from enviro_alert import Alert
from make_MM_str import MmStr
from mattermost import Mattermost
from out_of_tolerance import OutOfTolerance
from zabbix import Zabbix
from power_monitoring import PowerMonitoringAlert
from ach_overview import AchOverview
from django_db.create_db_for_django_page import ModifyDB
from gui_options_db.read_options_db import get_opt

# from gui_tk import controller_run
not_plain_mode = None
data_formatted = None
WATCHER_POST_DESTINATION = secrets_main["watcher"]

settings_for_oft = {
    "CDUs_t1_min": 16.0,
    "CDUs_t1_max": 25.0,
    "ACH1_inlet": 18.0,
    "ACH1_outlet": 16.0,
    "ACH2_inlet": 18.0,
    "ACH2_outlet": 16.0,
    "ACH3_inlet": 18.0,
    "ACH3_outlet": 16.0,
    "ACH4_inlet": 18.0,
    "ACH4_outlet": 16.0,
    "PCW1_H0_return": 25.0,
    "PCW1_H1_return": 26.0,
    "PCW2_H1_return": 26.0,
    "PCW_UPS+1_return": 25.0,
    "PCW_UPS-1_return": 25.0
}


class Options:
    """Basic setups on the go"""

    def __init__(self):
        self.time_program_started: str = " ".join(time.asctime().split()[1:4])
        self.current_options_settings: dict = dict()

    def check_options_settings_from_db(self):

        global not_plain_mode, data_formatted
        options = get_opt()
        if options != self.current_options_settings:
            order = ["notifications", "whatsapp", "check channels", "display_mode", "time_delay"]
            displayed_option_name = {
                "notifications": "Notifications",
                "whatsapp": "Whatsapp",
                "check channels": "Check channels",
                "display_mode": "Display mode",
                "time_delay": "Time delay"
            }
            print("\n" * 30)
            print(self.time_program_started)
            print(", ".join([f"{displayed_option_name[order[option]]}: {options[order[option]]}" for option in sorted(map(order.index, options))]))
            print("\n" * 3)

        self.current_options_settings = options

        if options["display_mode"] == "plain mode":
            not_plain_mode = False
            data_formatted = False
        if options["display_mode"] == "json":
            not_plain_mode = True
            data_formatted = False
        if options["display_mode"] == "data formatted":
            not_plain_mode = True
            data_formatted = True

        alert_notifications = options["notifications"]
        whatsapp = options["whatsapp"]
        check_channels = options["check channels"]
        wait_time = options["time_delay"]
        fermion_watcher = False

        return [alert_notifications, whatsapp, check_channels, not_plain_mode, data_formatted, fermion_watcher, wait_time, settings_for_oft]


class ModifyDjangoDB:
    """Modify db for Django webpage"""

    def __init__(self):
        self.primary_db: str = data_base["primary_db"]
        self.replica_db: str = data_base["replica_db"]

        self.django_db = ModifyDB()

    def database_operations(self, data):
        self.django_db.db_modification(data)
        self.update_replica_database()

    def update_replica_database(self):
        shutil.copyfile(self.primary_db, self.replica_db)


class ReadRunOptions:
    def __init__(self):
        self.options_db: str = "_options.db"


class Executor:
    # list of devs data of which is gathered (zabbix not included here)
    LST_OF_DEVS = ["ACH2", "ACH4", "ACH3", "ACH1", "PCW1 H0", "PCW1 H1", "PCW2 H1", "PCW UPS+1", "PCW UPS-1"]
    enviro_devs = dict.fromkeys(LST_OF_DEVS)

    def __init__(self, platform=None):
        self.platform: str = platform
        self.notifications: str = str()
        self.options: str = str()

        self.settings_for_oft: dict = dict()
        self.data: dict = dict()
        self.out_power_monitoring: dict = dict()
        self.out_enviro: dict = dict()
        self.out_zabbix: dict = dict()
        self.ach_overview: dict = dict()

        self.alert = Alert()
        self.zabbix = Zabbix()
        self.oft = OutOfTolerance()
        self.mm = Mattermost()
        self.mm_str = MmStr()
        self.fermion = Dict_For_Fermion()
        self.power_monitoring = PowerMonitoringAlert()
        self.ACH_overview = AchOverview()

        self.modify_db = ModifyDjangoDB()
        self.options_settings = Options()

        self.main_post_destination = secrets_main["which_platform_WIN"]

    def get_options_from_db(self):
        self.options = self.options_settings.check_options_settings_from_db()

    def run(self) -> None:
        while True:
            self.get_options_from_db()

            (self.alert_notifications, self.whatsapp, self.check_channels, self.not_plain_mode,
             self.data_formatted, self.fermion_watcher, self.wait_time, self.settings_for_oft) = self.options

            self.out_power_monitoring = self.power_monitoring.get_power_monitoring_alerts()
            time.sleep(self.wait_time * 2)

            self.out_enviro = self.alert.get_pcw_ach(Executor.LST_OF_DEVS)
            time.sleep(self.wait_time * 2)

            self.ach_overview = self.ACH_overview.get_ach_overview_info()

            self.out_zabbix = self.zabbix.request()

            self.make_data_dict()

            self.out_of_tolerance()

            self.user_interface()

            self.modify_db.database_operations(self.data)

    def make_data_dict(self) -> None:
        """Create dict which is passed to out_of_tolerance check"""
        if self.out_zabbix["status"]:
            self.data = {
                "Listening": "",
                "power_monitoring": self.out_power_monitoring,
                "ach_overview": self.ach_overview,

                "Ares": self.out_zabbix["data"]["Total power usage"],
                "CDU1": self.out_zabbix["data"]["CDU1"],
                "CDU2": self.out_zabbix["data"]["CDU2"],
                "CDU3": self.out_zabbix["data"]["CDU3"]
            }

        else:
            self.data = {
                "Listening": "",
                "power_monitoring": self.out_power_monitoring,
                "ach_overview": self.ach_overview
            }
        # add to data all key-value pairs from out_enviro; these might change
        for k in Executor.enviro_devs.keys():
            self.data[k] = self.out_enviro[k]

    def out_of_tolerance(self) -> None:
        self.notifications \
            = self.oft.check(self.data, self.settings_for_oft, self.alert_notifications,
                             self.whatsapp, self.check_channels, self.out_zabbix["status"])

    def user_interface(self) -> None:
        """Graphical presentation in MM"""
        self.data["Listening"] = self.notifications
        self.data["Time"] = f"{' '.join(time.asctime().split()[1:4])}"

        self.data_to_mm()
        self.fermion_watcher_display()

    def data_to_mm(self):
        """not_plain_mode - data send to MM as json or formated string"""
        if self.not_plain_mode:
            def message():
                return self.mm_str.make_mm_str(self.data) if self.data_formatted else json.dumps(self.data)

            self.mm.mm_edit(message(), self.main_post_destination)

    def fermion_watcher_display(self):
        """ESP32_fermion_screen"""
        if self.fermion_watcher and (json_fermion := self.fermion.dict_for_fermion(self.data)):
            time.sleep(self.wait_time * 2)
            self.mm.mm_edit(json.dumps(json_fermion), WATCHER_POST_DESTINATION)


def main():
    Executor().run()


if __name__ == "__main__":
    main()
