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
            platform = get_platform()

        self.platform: str = platform
        self.alarm_for_watcher: bool = False
        self.notifications: str = ''

        self.data: dict = None
        self.out_powermonitoring: dict = None
        self.out_enviro: dict = None
        self.out_zabbix: dict = None

        # Set attributes depending on platform
        # on RPi switches are physical buttons; on windows these buttons are predefined
        if self.platform == 'WIN':
            from settings import notifications, whatsapp, fermion_watcher
            self.main_post_destination = secrets_main['which_platform_WIN']
            self.fermion_watcher = fermion_watcher
            self.notifications = notifications
            self.whatsapp = whatsapp
            self.users = 'wk'

            print(f"notifications: {self.notifications}, whatsapp: {self.whatsapp}, fermion_watcher: {self.fermion_watcher}")

        else:
            self.main_post_destination = secrets_main['which_platform_RPi']
            self.users = 'oo'

        self.alert = Alert()
        self.zabbix = Zabbix()
        self.oft = OutOfTolerance()
        self.mm = Mattermost()
        self.mm_str = MM_Str()
        self.fermion = Dict_For_Fermion()
        self.powermonitoring = PowerMonitoringAlert()

    def user_interface(self) -> None:
        '''Graphical presentation'''
        if not plain_mode:

            self.data['Listening'] = self.notifications

            message, t = self.mm_str.make_mm_str(self.data, self.fermion_watcher, self.alarm_for_watcher)
            self.mm.mm_edit(message, self.main_post_destination)

            # the ESP32_fermion_screen
            if self.fermion_watcher and (json_fermion := self.fermion.dict_for_fermion(self.data)):
                time.sleep(wait_time * 3)
                self.mm.mm_edit(json.dumps(json_fermion), WATCHER_POST_DESTINATION)
            else:
                time.sleep(wait_time * 3)
        else:
            time.sleep(30)

    def make_data_dict(self) -> None:
        '''Create dict which is passed to out_of_tolerance check'''
        if self.out_zabbix['status'] == True:
            self.data = {
                'Listening': '',
                'power_monitoring': self.out_powermonitoring,

                'Ares': self.out_zabbix['data']['Total power usage'],
                'CDU1': self.out_zabbix['data']['CDU1'],
                'CDU2': self.out_zabbix['data']['CDU2'],
                'CDU3': self.out_zabbix['data']['CDU3']
            }

        else:
            self.data = {
                'Listening': '',
                'power_monitoring': self.out_powermonitoring
            }
        # add to data all key-value pairs from out_enviro; these might change
        for k in Executor.enviro_devs.keys():
            self.data[k] = self.out_enviro[k]

    def run(self):
        print(f"{' '.join(time.asctime().split()[1:4])} > Running..")

        while True:
            self.out_powermonitoring = self.powermonitoring.get_power_monitoring_alerts()
            time.sleep(2)  # delay for webdrivers objects; lack of it caused ocasional crash
            self.out_enviro = self.alert.get_pcw_ach(Executor.LST_OF_DEVS)
            self.out_zabbix = self.zabbix.request()

            if self.platform == 'RPi':
                self.notifications, self.whatsapp, self.fermion_watcher = get_switches_gpio()

            self.make_data_dict()

            self.notifications, self.alarm_for_watcher = self.oft.check(self.data, self.notifications, self.whatsapp, self.users, self.out_zabbix['status'])

            self.user_interface()
