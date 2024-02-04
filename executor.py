import json
import sys
import time
import logging

from settings import secrets_main, only_OO, wait_time, plain_mode

from dict_for_fermion import Dict_For_Fermion
from enviro_alert import Alert
from make_MM_str import MM_Str
from mattermost import Mattermost
from out_of_tolerance import OutOfTolerance
from zabbix import Zabbix

info_logger = logging.getLogger(__name__)
info_logger.setLevel(logging.INFO)
formatter_info = logging.Formatter('%(asctime)s - %(name)s >> %(message)s', datefmt='%Y-%m-%d %H:%M')
handler_info = logging.StreamHandler()
handler_info.setFormatter(formatter_info)
info_logger.addHandler(handler_info)

# watcher post_id
WATCHER_POST_DESTINATION = secrets_main['watcher']


def get_platform():
    if sys.platform == 'win32':
        return 'WIN'
    return 'RPi'


class Executor:
    # list of devs data of which is gathered (zabbix not included here)
    LST_OF_DEVS = ['ACH2', 'ACH4', 'ACH3', 'ACH1', 'PCW1 H0', 'PCW1 H1', 'PCW2 H1', 'PCW UPS+1', 'PCW UPS-1']

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
            self.users = [1]  # these numbers are listening persons

            info_logger.info('notifications: %s, whatsapp: %s, fermion_watcher: %s', notifications, whatsapp, fermion_watcher)

        else:
            from PyMonitoring.readGPIO import get_switches_gpio
            self.notifications, self.whatsapp, self.fermion_watcher = get_switches_gpio()
            self.main_post_destination = secrets_main['which_platform_RPi']
            self.users = [8]

            info_logger.info('Running')

        self.alert = Alert()
        self.zabbix = Zabbix()
        self.oft = OutOfTolerance()
        self.mm = Mattermost()
        self.mm_str = MM_Str()
        self.fermion = Dict_For_Fermion()

    def run(self):

        devs = dict.fromkeys(Executor.LST_OF_DEVS)

        while True:
            out_zabbix = self.zabbix.request()
            out_enviro = self.alert.get_pcw_ach(Executor.LST_OF_DEVS)
            zabbix_online = out_zabbix['status']

            if zabbix_online == True:
                data = {
                    'Listening': '',
                    'Ares': out_zabbix['data']['Total power usage'],
                    'CDU1': out_zabbix['data']['CDU1'],
                    'CDU2': out_zabbix['data']['CDU2'],
                    'CDU3': out_zabbix['data']['CDU3'],

                }
                for k in devs.keys():
                    data[k] = out_enviro[k]

            else:
                data = {
                    'Listening': '',
                }
                for k in devs.keys():
                    data[k] = out_enviro[k]

            persons_str = ''
            for i, person_settings in enumerate(self.users):
                out = self.oft.check(data, person_settings, self.notifications, self.whatsapp, zabbix_online)

                try:
                    # if there is only one user which gather settings only once the time.sleep is not needed
                    if only_OO or len(self.users) == 1:
                        persons_str += out
                    else:
                        persons_str += out
                        time.sleep(wait_time)
                except Exception:
                    time.sleep(wait_time)
                    pass

            if not plain_mode:

                # indicates who is online listening to alerts or if only_OO==True indicates if notification and whatsapp
                data['Listening'] = persons_str

                message, t = self.mm_str.make_mm_str(data)
                self.mm.mm_edit(message, self.main_post_destination)

                # the ESP32_fermion_screen
                if self.fermion_watcher and (json_fermion := self.fermion.dict_for_fermion(data)):
                    time.sleep(wait_time * 4)
                    self.mm.mm_edit(json.dumps(json_fermion), WATCHER_POST_DESTINATION)
                else:
                    time.sleep(wait_time * 4)
            else:
                time.sleep(30)