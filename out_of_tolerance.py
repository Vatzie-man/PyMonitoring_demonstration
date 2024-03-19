from dataclasses import dataclass, field
from typing import Union
import requests
import typing
import time
import sys

from mattermost import Mattermost
from settings import secrets_oft, secrets_main, data_read_once_at_start, secrets_mm


@dataclass
class WhatsApp:
    destination: str = secrets_oft['call_me_bot_url']
    apikey: str = secrets_oft['cal_me_bot_apikey']


@dataclass
class Person:
    name: str
    settings: str
    channel_id: str


class OutOfTolerance():

    def __init__(self):

        self.mm = Mattermost()
        self.whatsapp = WhatsApp()

        self.person = Person

        self.data: dict = None
        self.user_settings: dict = None
        self.watcher_alarm: bool = False
        self.first_program_run: bool = True
        self.zabbix_online: bool = False
        self.send_alert_settings: list = None
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
            'PCW_UPS-1_return': False,
        }

    def set_first_program_run(self) -> None:
        """Assign default devices state at the begining"""
        for user in self.devaices_prev_state.keys():
            self.devaices_prev_state[user] = self.devaices_curr_state(self.data)
        self.first_program_run = False

    def send_alerts(self, message: str) -> None:
        """Send alerts via different chanels"""
        if message:
            notifications, whatsapp, channel_id, name = self.send_alert_settings
            if notifications:

                self.watcher_alarm = True

                self.mm.mm_post(f' {message}', channel_id)

                if self.user_settings['Plus WhatsApp'] == 1:
                    if whatsapp:
                        requests.post(
                            self.whatsapp.destination + name
                            + f': {message}' + self.whatsapp.apikey)
                time.sleep(1)

    def key_maker(self, x: str, state: str) -> tuple:
        """Creates keys pairs to combine different devices chceck in one function"""
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

    def check_temp(self, x: str, state: str):
        """Checks temps of devices"""
        x, y, z, settings_key, data_key, message_key = self.key_maker(x, state)

        if self.user_settings[y + settings_key] < float(self.data[x][data_key]):

            if self.devaices_prev_state[self.person.name][z + settings_key]:
                value = float(self.data[x][data_key])
                message = f"{x} {message_key}: {value}C"
                self.devaices_prev_state[self.person.name][z + settings_key] = False
                return message

        else:
            self.devaices_prev_state[self.person.name][z + settings_key] = True
            return None

        if x[0:3] == 'PCW':
            self.devaices_prev_state[self.person.name][y] = 'Online'

    def check_PM_alerts(self, alert: str) -> Union[str, None]:
        """Checks whatever ther is any alarm from PowerMonitoring"""
        message_keys = {'high_priority': 'PowerMonitoring High', 'mid_priority': 'PowerMonitoring Medium', 'low_priority': 'PowerMonitoring Low'}

        if int(self.data['power_monitoring'][alert]) > self.devaices_prev_state[self.person.name][alert]:
            message = f"{message_keys[alert]}: {self.data['power_monitoring'][alert]}"
            self.devaices_prev_state[self.person.name][alert] = int(self.data['power_monitoring'][alert])
            return message
        else:
            self.devaices_prev_state[self.person.name][alert] = int(self.data['power_monitoring'][alert])
            return None

    def check_status(self, dev: str) -> Union[str, None]:
        """Checks the devices state: ON/OFF/Stadby"""
        if (self.devaices_prev_state[self.person.name][dev] in ('Warning On', 'Local ON')) != (self.data[dev][dev] in ('Warning On', 'Local ON')):

            value = 'On' if self.data[dev][dev] in ('Warning On', 'Local ON') else self.data[dev][dev]
            message = f"{dev}: {value}"
            self.devaices_prev_state[self.person.name][dev] = self.data[dev][dev]
            return message
        else:
            self.devaices_prev_state[self.person.name][dev] = self.data[dev][dev]
            return None

    def handle_offline(self, dev: str) -> Union[str, None]:
        """This function is called if an Exception has been rised during other checks"""
        if self.devaices_prev_state[self.person.name][dev] == 'Offline':
            return None
        else:
            self.devaices_prev_state[self.person.name][dev] = 'Offline'
            message = f'{dev}: Offline.'
            return message

    def first_run(self, user: str) -> None:
        """Assigns data to user"""
        self.person = Person(
            user,
            secrets_oft['person_settings'][user][0],
            secrets_oft['person_settings'][user][1]
        )

        if data_read_once_at_start:  # settings are read only once at first: notifications and whatsapp are managed by switches on RPi
            self.user_settings = self.mm.make_dict_from_mm(self.person.settings)
            print(f"{self.person.name}: Powiadomienia: {bool(self.user_settings['Powiadomienia'])}, "
                  f"WhatsApp: {bool(self.user_settings['Plus WhatsApp'])}" + '\n')

    def PowerMonitoringCheck(self) -> None:
        """ PowerMonitoring alarm check """
        if self.data['power_monitoring']['status'] == True:  # is there data from PM

            for alert in (self.data['power_monitoring'].keys() - {'status'}):
                message = self.check_PM_alerts(alert)
                self.send_alerts(message)

        if self.data['power_monitoring']['status'] == False and self.devaices_prev_state[self.person.name]['PowerMonitoring_status'] == True:
            self.devaices_prev_state[self.person.name]['PowerMonitoring_status'] == False
            message = f"Brak danych z PowerMonitoring."
            self.send_alerts(message)

    def ZabbixCheck(self) -> None:
        """CDUs operations and temp comparisons"""
        if self.zabbix_online == True:  # is there data from Zabbix

            for device in [k for k in self.data.keys() if k[0:3] == 'CDU']:
                for state in ('CDUs_t1_min', 'CDUs_t1_max'):
                    message = self.check_temp(device, state=state)
                    self.send_alerts(message)

            self.devaices_prev_state[self.person.name]['Zabbix'] = 1

        # if there is no data from zabbix in two request on the raw then alert message will be send; though single occurances of no data is frequnent
        if self.zabbix_online == False and self.devaices_prev_state[self.person.name]['Zabbix'] == True:
            self.devaices_prev_state[self.person.name]['Zabbix'] = False
            message = f"Brak danych z Zabbix."
            self.send_alerts(message)

    def ACHsCheck(self) -> None:
        """ACH's operations and temp comparisons"""
        for device in [k for k in self.data.keys() if k[0:3] == 'ACH']:
            try:
                for state in ('ACH_inlet', 'ACH_outlet'):
                    message = self.check_temp(device, state=state)
                    self.send_alerts(message)

                message = self.check_status(device)
                self.send_alerts(message)

            except Exception:
                message = self.handle_offline(device)
                self.send_alerts(message)

    def PCWsCheck(self) -> None:
        """PCWs operations and temp comparisons"""
        for device in [k for k in self.data.keys() if k[0:3] == 'PCW']:

            try:
                message = self.check_temp(device, state='PCW_return')
                self.send_alerts(message)

            except Exception:
                message = self.handle_offline(device)
                self.send_alerts(message)

    def check(self, data: dict, notifications: str, whatsapp: str, person: str, zabbix_online: bool) -> Union[str, bool]:
        """Main function in this file: checks devicase parameters against desired parameters"""
        self.data = data
        self.zabbix_online = zabbix_online

        if self.first_program_run:
            self.first_run(person)
            self.set_first_program_run()

        if not data_read_once_at_start:  # settings will be read each time from user settings and switches must simulate always on state (notifications and whatsapp)
            self.user_settings = self.mm.make_dict_from_mm(self.person.settings)
            notifications = True
            whatsapp = True

            if self.user_settings['Powiadomienia'] == 0:
                self.devaices_prev_state[self.person.name] = self.devaices_curr_state(self.data)
                return ('Brak powiadomień.', False)

            if self.user_settings['Powiadomienia'] == 503:
                # here "devaices_prev_state = devaisces_curr_state" is omited cos during server down something might change
                return ('Problem with MM settings.', True)

        self.send_alert_settings = [notifications, whatsapp, self.person.channel_id, self.person.name]
        self.watcher_alarm = False

        self.PowerMonitoringCheck()
        self.ZabbixCheck()
        self.ACHsCheck()
        self.PCWsCheck()

        if data_read_once_at_start:
            return (('notifications' if (notifications and self.user_settings['Powiadomienia']) else '') + (
                ', whatsapp' if (notifications and whatsapp and self.user_settings['Plus WhatsApp']) else ''), self.watcher_alarm)
        else:
            return (self.person.name.upper() + ' ' if self.user_settings['Plus WhatsApp'] else self.person.name + ' ', self.watcher_alarm)
