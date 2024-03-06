import json
import sys
import time

from settings import secrets_main, wait_time, plain_mode

from dict_for_fermion import Dict_For_Fermion
from enviro_alert import Alert
from make_MM_str import MM_Str
from mattermost import Mattermost
from out_of_tolerance import OutOfTolerance
from zabbix import Zabbix
from power_monitoring import PowerMonitoringAlert

if sys.platform != 'win32':
    from readGPIO import get_switches_gpio

# watcher post_id
WATCHER_POST_DESTINATION = secrets_main['watcher']


def get_platform():
    if sys.platform == 'win32':
        return 'WIN'
    return 'RPi'


class Executor:
    # list of devs data of which is gathered (zabbix not included here)
    LST_OF_DEVS = ['ACH2', 'ACH4', 'ACH3', 'ACH1', 'PCW1 H0', 'PCW1 H1', 'PCW2 H1', 'PCW UPS+1', 'PCW UPS-1']
    enviro_devs = dict.fromkeys(LST_OF_DEVS)

    def __init__(self, platform=None):
        if platform is None:
            # Detect platform
            platform = get_platform()
        self.platform = platform

        # Set attributes depending on platform
        # on RPi switches are physical buttons; on windows these buttons are predefined
        if self.platform == 'WIN':
            from settings import notifications, whatsapp, fermion_watcher
            self.main_post_destination = secrets_main['which_platform_WIN']
            self.fermion_watcher = fermion_watcher
            self.notifications = notifications
            self.whatsapp = whatsapp
            self.users = 1  # these numbers are listening persons

            print(f"notifications: {self.notifications}, whatsapp: {self.whatsapp}, fermion_watcher: {self.fermion_watcher}")

        else:
            self.main_post_destination = secrets_main['which_platform_RPi']
            self.users = 8

        self.alert = Alert()
        self.zabbix = Zabbix()
        self.oft = OutOfTolerance()
        self.mm = Mattermost()
        self.mm_str = MM_Str()
        self.fermion = Dict_For_Fermion()
        self.powermonitoring = PowerMonitoringAlert()

    def user_interface(self, plain_mode: bool, notifications: str, data: dict) -> None:
        if not plain_mode:

            data['Listening'] = notifications

            message, t = self.mm_str.make_mm_str(data)
            self.mm.mm_edit(message, self.main_post_destination)

            # the ESP32_fermion_screen
            if self.fermion_watcher and (json_fermion := self.fermion.dict_for_fermion(data)):
                time.sleep(wait_time * 3)
                self.mm.mm_edit(json.dumps(json_fermion), WATCHER_POST_DESTINATION)
            else:
                time.sleep(wait_time * 3)
        else:
            time.sleep(30)

    def make_data_dict(self, out_powermonitoring: dict, out_enviro: dict, out_zabbix: dict) -> dict:

        if out_zabbix['status'] == True:
            data = {
                'Listening': '',
                'power_monitoring': out_powermonitoring,

                'Ares': out_zabbix['data']['Total power usage'],
                'CDU1': out_zabbix['data']['CDU1'],
                'CDU2': out_zabbix['data']['CDU2'],
                'CDU3': out_zabbix['data']['CDU3']
            }

        else:
            data = {
                'Listening': '',
                'power_monitoring': out_powermonitoring
            }
        # add to data all key-value pairs from out_enviro; these might change
        for k in Executor.enviro_devs.keys():
            data[k] = out_enviro[k]

        return data

    def run(self):

        while True:
            out_powermonitoring = self.powermonitoring.get_power_monitoring_alerts()
            time.sleep(2)  # delay: maybe webdriver will work better
            out_enviro = self.alert.get_pcw_ach(Executor.LST_OF_DEVS)
            out_zabbix = self.zabbix.request()

            if self.platform == 'RPi':
                self.notifications, self.whatsapp, self.fermion_watcher = get_switches_gpio()

            data = self.make_data_dict(out_powermonitoring, out_enviro, out_zabbix)

            notifications = self.oft.check(data, self.users, self.notifications, self.whatsapp, out_zabbix['status'])

            self.user_interface(plain_mode, notifications, data)
