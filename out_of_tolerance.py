from dataclasses import dataclass, field
import requests
import typing
import logging
import time
import sys

from mattermost import Mattermost
from settings import secrets_oft, secrets_main, data_read_once_at_start

info_logger = logging.getLogger(__name__)
info_logger.setLevel(logging.INFO)
formatter_info = logging.Formatter('%(name)s >> %(message)s', datefmt='%Y-%m-%d %H:%M')
handler_info = logging.StreamHandler()
handler_info.setFormatter(formatter_info)
info_logger.addHandler(handler_info)

# TODO
# vatzie_post_to_edit = secrets_main['vatzie_post_to_edit']

@dataclass
class WhatsApp:
    destination: str = secrets_oft['call_me_bot_url']
    apikey: str = secrets_oft['cal_me_bot_apikey']

    destination_test: str = secrets_oft['call_me_bot_url_dtp_test']
    apikey_test: str = secrets_oft['cal_me_bot_apikey_dtp_test']


@dataclass
class Person:
    name: str
    settings: str
    channel_id: str


class OutOfTolerance():

    def __init__(self):

        self.mm = Mattermost()
        self.whatsapp = WhatsApp()

        self.user_settings: dict = None
        self.first_program_run: bool = True
        self.devaices_prev_state: dict = {'wk': None, 'oo': None}

    @staticmethod
    def devaices_curr_state(data):
        def there_is_no_status(dev):
            try:
                return data[dev][dev]
            except Exception:
                return 'Offline'

        return {
            # states
            'ACH1': there_is_no_status('ACH1'),
            'ACH2': there_is_no_status('ACH2'),
            'ACH3': there_is_no_status('ACH3'),
            'ACH4': there_is_no_status('ACH4'),
            'PCW1 H0': 'Online',
            'PCW1 H1': 'Online',
            'PCW2 H1': 'Online',
            'PCW UPS+1': 'Online',
            'PCW UPS-1': 'Online',
            # PowerMonitoring
            'PowerMonitoring_status': True,
            'high_priority': int(data['power_monitoring']['high_priority']),
            'mid_priority': int(data['power_monitoring']['mid_priority']),
            'low_priority': int(data['power_monitoring']['low_priority']),
            # Zabbix
            'Zabbix': True,
            # CDUs temps
            'CDU1_t1_min': False,
            'CDU1_t1_max': False,
            'CDU2_t1_min': False,
            'CDU2_t1_max': False,
            'CDU3_t1_min': False,
            'CDU3_t1_max': False,
            # ACHs
            'ACH1_inlet': False,
            'ACH1_outlet': False,
            'ACH2_inlet': False,
            'ACH2_outlet': False,
            'ACH3_inlet': False,
            'ACH3_outlet': False,
            'ACH4_inlet': False,
            'ACH4_outlet': False,
            # PCWs
            'PCW1_H0_return': False,
            'PCW1_H1_return': False,
            'PCW2_H1_return': False,
            'PCW_UPS+1_return': False,
            'PCW_UPS-1_return': False
        }

    def set_first_program_run(self, data: dict) -> None:
        for user in self.devaices_prev_state.keys():
            self.devaices_prev_state[user] = self.devaices_curr_state(data)
        self.first_program_run = False

    def send_alerts(self, message: str, send_alert_settings: list) -> None:
        if message:
            notifications, whatsapp, channel_id, name = send_alert_settings
            if notifications:

                self.mm.mm_post(f' {message}', channel_id)

                if self.user_settings['Plus WhatsApp'] == 1:
                    if whatsapp:
                        requests.post(
                            self.whatsapp.destination + name
                            + f': {message}' + self.whatsapp.apikey)
                time.sleep(1)

    # key maker helps crete keys for multi temp chceck in one function
    def key_maker(self, x: str, state: str) -> tuple:

        if state == 'ACH_inlet':
            return x, x, x, '_inlet', 'Inlet Temp', "temp wejściowa"

        if state == 'ACH_outlet':
            return x, x, x, '_outlet', 'Outlet Temp', "temp wyjściowa"

        if state == 'PCW_return':
            return x, x.replace(' ', '_'), x.replace(' ', '_'), '_return', 'Return Air', "Return"

        if state == 'CDUs_t1_min':
            return x, f'{x[0:3]}s', x, '_t1_min', 't1', "Niska Temp 1"

        if state == 'CDUs_t1_max':
            return x, f'{x[0:3]}s', x, '_t1_max', 't1', "Wysoka Temp 1"

    def check_temp(self, x: str, user: str, data: dict, state: str):

        x, y, z, settings_key, data_key, message_key = self.key_maker(x, state)

        if self.user_settings[y + settings_key] < float(data[x][data_key]):

            if self.devaices_prev_state[user][z + settings_key]:
                value = float(data[x][data_key])
                message = f"{x} {message_key}: {value}C"
                self.devaices_prev_state[user][z + settings_key] = False
                return message

        else:
            self.devaices_prev_state[user][z + settings_key] = True
            return None

        if x[0:3] == 'PCW':
            self.devaices_prev_state[user][y] = 'Online'

    def check_PM_alerts(self, alert: str, user: str, data: dict):

        message_keys = {'high_priority': 'PowerMonitoring High', 'mid_priority': 'PowerMonitoring Medium', 'low_priority': 'PowerMonitoring Low'}

        if int(data['power_monitoring'][alert]) > self.devaices_prev_state[user][alert]:
            message = f"{message_keys[alert]}: {data['power_monitoring'][alert]}"
            self.devaices_prev_state[user][alert] = int(data['power_monitoring'][alert])
            return message
        else:
            self.devaices_prev_state[user][alert] = int(data['power_monitoring'][alert])
            return None

    def check_status(self, dev: str, user: str, data: dict):

        if (self.devaices_prev_state[user][dev] in ('Warning On', 'Local ON')) != (data[dev][dev] in ('Warning On', 'Local ON')):

            value = 'On' if data[dev][dev] in ('Warning On', 'Local ON') else data[dev][dev]
            message = f"{dev}: {value}"
            self.devaices_prev_state[user][dev] = data[dev][dev]
            return message
        else:
            self.devaices_prev_state[user][dev] = data[dev][dev]
            return None

    def handle_offline(self, dev: str, user: str):

        if self.devaices_prev_state[user][dev] == 'Offline':
            return None
        else:
            self.devaices_prev_state[user][dev] = 'Offline'
            message = f'{dev}: Offline.'
            return message

    def check(self, data: dict, user: int, notifications: str, whatsapp: str, zabbix_online: bool) -> str:

        person = Person(
            dict((int(k), v) for k, v in secrets_oft['personons'].items())[user],
            dict((int(k), v) for k, v in secrets_oft['dict_person_settings'].items())[user][0],
            dict((int(k), v) for k, v in secrets_oft['dict_person_settings'].items())[user][1],

        )

        send_alert_settings = [notifications, whatsapp, person.channel_id, person.name]

        if self.first_program_run:

            if data_read_once_at_start:  # settings are read only once at first: notifications and whatsapp are managed by switches on RPi
                self.user_settings = self.mm.make_dict_from_mm(person.settings)
                print(f"{person.name}: Powiadomienia: {bool(self.user_settings['Powiadomienia'])}, WhatsApp: {bool(self.user_settings['Plus WhatsApp'])}" + '\n')

            # make checks at start if notifications are working
            # if sys.platform == 'win32':
            #     requests.post(self.whatsapp.destination + "Test_Vatzie" + self.whatsapp.apikey)
            #     time.sleep(1)
            #     requests.post(self.whatsapp.destination_test + "Test_DTP" + self.whatsapp.apikey_test)
            #     # time.sleep(1)
            #     # self.mm.mm_edit("message", vatzie_post_to_edit) - i must provide Vatzie tooken

            self.set_first_program_run(data)

        if not data_read_once_at_start:  # settings will be read each time from user settings and switches must simulate always on state (notifications and whatsapp)
            self.user_settings = self.mm.make_dict_from_mm(person.settings)
            notifications = True
            whatsapp = True

        channel_id = person.channel_id  # destination of a channel if any parameters are out of tolerance

        if self.user_settings['Powiadomienia'] == 0:
            self.devaices_prev_state[person.name] = self.devaices_curr_state(data)
            return 'Brak powiadomień.'

        if self.user_settings['Powiadomienia'] == 503:
            # here "devaices_prev_state = devaisces_curr_state" is omited cos during server down something might change
            return 'Data not awelable.'

        # PowerMonitoring alarm check
        if data['power_monitoring']['status'] == True:  # is there data from PM

            for alert in (data['power_monitoring'].keys() - {'status'}):
                # value = data['power_monitoring'][alert]
                message = self.check_PM_alerts(alert, person.name, data)
                self.send_alerts(message, send_alert_settings)

        if data['power_monitoring']['status'] == False and self.devaices_prev_state[person.name]['PowerMonitoring_status'] == True:
            self.devaices_prev_state[person.name]['PowerMonitoring_status'] == False
            message = f"Brak danych z PowerMonitoring."
            self.send_alerts(message, send_alert_settings)

        # CDUs operations and temp comparisons
        if zabbix_online == True:  # is there data from Zabbix

            for device in [k for k in data.keys() if k[0:3] == 'CDU']:
                for state in ('CDUs_t1_min', 'CDUs_t1_max'):
                    message = self.check_temp(device, person.name, data, state=state)
                    self.send_alerts(message, send_alert_settings)

            self.devaices_prev_state[person.name]['Zabbix'] = 1

        # if there is no data from zabbix in two request on the raw then alert message will be send; though single occurances of no data is frequnent
        if zabbix_online == False and self.devaices_prev_state[person.name]['Zabbix'] == True:
            self.devaices_prev_state[person.name]['Zabbix'] = False
            message = f"Brak danych z Zabbix."
            self.send_alerts(message, send_alert_settings)

        # ACH's operations and temp comparisons
        for device in [k for k in data.keys() if k[0:3] == 'ACH']:
            try:
                for state in ('ACH_inlet', 'ACH_outlet'):
                    message = self.check_temp(device, person.name, data, state=state)
                    self.send_alerts(message, send_alert_settings)

                message = self.check_status(device, person.name, data)
                self.send_alerts(message, send_alert_settings)

            except Exception:
                message = self.handle_offline(device, person.name)
                self.send_alerts(message, send_alert_settings)

        # PCWs operations and temp comparisons
        for device in [k for k in data.keys() if k[0:3] == 'PCW']:

            try:
                message = self.check_temp(device, person.name, data, state='PCW_return')
                self.send_alerts(message, send_alert_settings)

            except Exception:
                message = self.handle_offline(device, person.name)
                self.send_alerts(message, send_alert_settings)

        if data_read_once_at_start:
            return ('notifications' if (notifications and self.user_settings['Powiadomienia']) else '') + (
                ', whatsapp' if (notifications and whatsapp and self.user_settings['Plus WhatsApp']) else '')
        else:
            return person.name.upper() + ' ' if self.user_settings['Plus WhatsApp'] else person.name + ' '
