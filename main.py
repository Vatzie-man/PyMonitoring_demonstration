import json
import sys
import time
import shutil

from settings import secrets_main, data_base

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


class Options():
    '''Basic seteups on the go'''
    def __init__(self):
        self.current_options_settings: list = []
        self.time_program_started: str = ' '.join(time.asctime().split()[1:4])

    def check_options_settings(self):
        with open('options_settings.json', 'r') as f:
            options = json.load(f)

        new_options_settings = [options['alert_notifications'], options['whatsapp'], options['check_channels'], options['not_plain_mode'],
                                options['data_formatted'], options['fermion_watcher'], options['wait_time']]

        if self.current_options_settings != new_options_settings:
            print(f"Running since: {self.time_program_started}")
            print(f"notifications: {bool(options['alert_notifications'])}, "
                  f"whatsapp: {bool(options['whatsapp'])}, "
                  f"check_channels: {bool(options['check_channels'])}, "
                  f"not_plain_mode: {bool(options['not_plain_mode'])}, "
                  f"data_formatted: {bool(options['data_formatted'])}, "
                  f"fermion_watcher: {bool(options['fermion_watcher'])}, "
                  f"wait_time: {float(options['wait_time'])}s")

        self.current_options_settings = [item for item in new_options_settings]
        return self.current_options_settings


class modifyDjangoDB:
    '''Modifys db for Django webpage'''
    def __init__(self):
        self.primary_db: str = data_base['primary_db']
        self.replica_db: str = data_base['replica_db']

        self.djangodb = DjangoDataBase()

    def database_operations(self, data):
        self.djangodb.db_modification(data)
        self.update_replica_database()

    def update_replica_database(self):
        shutil.copyfile(self.primary_db, self.replica_db)


class Executor:
    # list of devs data of which is gathered (zabbix not included here)
    LST_OF_DEVS = ['ACH2', 'ACH4', 'ACH3', 'ACH1', 'PCW1 H0', 'PCW1 H1', 'PCW2 H1', 'PCW UPS+1', 'PCW UPS-1']
    enviro_devs = dict.fromkeys(LST_OF_DEVS)

    def __init__(self, platform=None):
        if platform is None:
            platform = get_platform()

        self.platform: str = platform
        self.notifications: str = str()
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

        self.modify_db = modifyDjangoDB()
        self.options_settings = Options()

        if self.platform == 'WIN':
            self.main_post_destination = secrets_main['which_platform_WIN']
            self.users = 'wk'

        else:
            self.main_post_destination = secrets_main['which_platform_RPi']
            self.users = 'oo'

    def run(self) -> None:

        while True:
            (self.alert_notifications, self.whatsapp, self.check_channels, self.not_plain_mode,
             self.data_formatted, self.fermion_watcher, self.wait_time) = self.options_settings.check_options_settings()

            self.out_powermonitoring = self.powermonitoring.get_power_monitoring_alerts()
            time.sleep(self.wait_time * 2)

            self.out_enviro = self.alert.get_pcw_ach(Executor.LST_OF_DEVS)
            time.sleep(self.wait_time * 2)

            self.ach_overview = self.ACH_overview.get_ach_overview_info()

            self.out_zabbix = self.zabbix.request()

            if self.platform == 'RPi':
                self.notifications, self.whatsapp, self.fermion_watcher = get_switches_gpio()

            self.make_data_dict()

            self.out_of_tolerance()

            self.user_interface()

            self.modify_db.database_operations(self.data)

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

    def out_of_tolerance(self) -> None:
        self.notifications, self.alarm_for_watcher \
            = self.oft.check(self.data, self.users, self.alert_notifications, self.whatsapp, self.check_channels, self.out_zabbix['status'])

    def user_interface(self) -> None:
        '''Graphical presentation in MM'''
        self.data['Listening'] = self.notifications
        self.data['Time'] = f"{' '.join(time.asctime().split()[1:4])}"

        self.data_to_MM()
        self.fermion_watcher_display()

    def data_to_MM(self):
        '''not_plain_mode - data send to MM as json or formated string'''
        if self.not_plain_mode:
            def message():
                return self.mm_str.make_mm_str(self.data, self.fermion_watcher, self.alarm_for_watcher) \
                    if self.data_formatted else json.dumps(self.data)

            self.mm.mm_edit(message(), self.main_post_destination)

    def fermion_watcher_display(self):
        '''ESP32_fermion_screen'''
        if self.fermion_watcher and (json_fermion := self.fermion.dict_for_fermion(self.data)):
            time.sleep(self.wait_time * 2)
            self.mm.mm_edit(json.dumps(json_fermion), WATCHER_POST_DESTINATION)


def main():
    Executor().run()


if __name__ == "__main__":
    main()
