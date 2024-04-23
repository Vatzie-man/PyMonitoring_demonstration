import json
import sys
import time
import shutil

from settings import secrets_main, wait_time, not_plain_mode, fermion_watcher, data_formatted, data_base

from dict_for_fermion import Dict_For_Fermion
from enviro_alert import Alert
from make_MM_str import MM_Str
from mattermost import Mattermost
from out_of_tolerance import OutOfTolerance
from zabbix import Zabbix
from power_monitoring import PowerMonitoringAlert
from ach_overview import AchOverview
from sqlitedb import DjangoDataBase

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
        self.notifications: str = str()
        self.primary_db: str = data_base['primary_db']
        self.replica_db: str = data_base['replica_db']
        self.check_channels: bool = False
        self.alarm_for_watcher: bool = False

        self.data: dict = dict()
        self.out_powermonitoring: dict = dict()
        self.out_enviro: dict = dict()
        self.out_zabbix: dict = dict()
        self.ach_overview: dict = dict()

        self.alert = Alert()
        self.zabbix = Zabbix()
        self.oft = OutOfTolerance()
        self.mm = Mattermost()
        self.mm_str = MM_Str()
        self.fermion = Dict_For_Fermion()
        self.powermonitoring = PowerMonitoringAlert()
        self.ACH_overview = AchOverview()
        self.djangodb = DjangoDataBase()

        # Set attributes depending on platform
        # on RPi switches are physical buttons; on windows these buttons are predefined
        if self.platform == 'WIN':
            from settings import notifications, whatsapp, check_channels
            self.main_post_destination = secrets_main['which_platform_WIN']
            self.fermion_watcher = fermion_watcher
            self.notifications = notifications
            self.whatsapp = whatsapp
            self.check_channels = check_channels
            self.users = 'wk'

            print(
                f"WIN: notifications: {self.notifications}, whatsapp: {self.whatsapp}, check_channels: {check_channels}, fermion_watcher: {self.fermion_watcher}")

        else:
            self.main_post_destination = secrets_main['which_platform_RPi']
            self.users = 'oo'

    def run(self) -> None:
        print(f"Running since {' '.join(time.asctime().split()[1:4])}")

        while True:
            self.out_powermonitoring = self.powermonitoring.get_power_monitoring_alerts()
            time.sleep(wait_time)  # delay for webdrivers objects; lack of it might caused ocasional crash

            self.out_enviro = self.alert.get_pcw_ach(Executor.LST_OF_DEVS)
            time.sleep(wait_time)

            self.ach_overview = self.ACH_overview.get_ach_overview_info()

            self.out_zabbix = self.zabbix.request()

            if self.platform == 'RPi':
                self.notifications, self.whatsapp, self.fermion_watcher = get_switches_gpio()

            self.make_data_dict()

            self.notifications, self.alarm_for_watcher \
                = self.oft.check(self.data, self.users, self.notifications, self.whatsapp, self.check_channels, self.out_zabbix['status'])

            self.user_interface()

            self.database_operations()

    def make_data_dict(self) -> None:
        '''Create dict which is passed to out_of_tolerance check'''
        if self.out_zabbix['status'] == True:
            self.data = {
                'Listening': '',
                'power_monitoring': self.out_powermonitoring,
                'ach_overview': self.ach_overview,

                'Ares': self.out_zabbix['data']['Total power usage'],
                'CDU1': self.out_zabbix['data']['CDU1'],
                'CDU2': self.out_zabbix['data']['CDU2'],
                'CDU3': self.out_zabbix['data']['CDU3']
            }

        else:
            self.data = {
                'Listening': '',
                'power_monitoring': self.out_powermonitoring,
                'ach_overview': self.ach_overview
            }
        # add to data all key-value pairs from out_enviro; these might change
        for k in Executor.enviro_devs.keys():
            self.data[k] = self.out_enviro[k]

    def user_interface(self) -> None:
        '''Graphical presentation in MM'''
        self.data['Listening'] = self.notifications
        self.data['Time'] = f"{' '.join(time.asctime().split()[1:4])}"

        self.data_to_MM()
        self.fermion_watcher()

    def data_to_MM(self):
        '''not_plain_mode - data send to MM as json or formated string'''
        if not_plain_mode:
            def message():
                return self.mm_str.make_mm_str(self.data, self.fermion_watcher, self.alarm_for_watcher) if data_formatted else json.dumps(self.data)

            self.mm.mm_edit(message(), self.main_post_destination)

    def fermion_watcher(self):
        '''ESP32_fermion_screen'''
        if self.fermion_watcher and (json_fermion := self.fermion.dict_for_fermion(self.data)):
            time.sleep(wait_time * 2)
            self.mm.mm_edit(json.dumps(json_fermion), WATCHER_POST_DESTINATION)

    def database_operations(self):
        self.djangodb.db_modification(self.data)
        self.update_replica_database()

    def update_replica_database(self):
        shutil.copyfile(self.primary_db, self.replica_db)


def main():
    Executor().run()


if __name__ == "__main__":
    main()
