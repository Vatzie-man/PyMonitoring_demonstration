import requests
import logging
import time

from mattermost import Mattermost
from settings import secrets_oft, only_OO

info_logger = logging.getLogger(__name__)
info_logger.setLevel(logging.INFO)
formatter_info = logging.Formatter('%(name)s >> %(message)s', datefmt='%Y-%m-%d %H:%M')
handler_info = logging.StreamHandler()
handler_info.setFormatter(formatter_info)
info_logger.addHandler(handler_info)

# call_me_bot
CALL_ME_BOT_URL = secrets_oft['call_me_bot_url']
CALL_ME_BOT_APIKEY = secrets_oft['cal_me_bot_apikey']

# each user devices states
DEVs_prev_states = {'wk': None, 'ms': None, 'gs': None, 'wc': None, 'kr': None, 'ks': None, 'pk': None, 'oo': None}


class OutOfTolerance:

    def __init__(self):
        self.first_program_run = True
        self.settings = None

        self.mm = Mattermost()
        self.persons = dict((int(k), v) for k, v in secrets_oft['personons'].items())
        self.dict_person_settings = dict((int(k), v) for k, v in secrets_oft['dict_person_settings'].items())  # [nastawy, alert destination]

    @staticmethod
    def current_DEVs_state(data):
        return {
            # states
            'ACH1': data['ACH1']['ACH1'],
            'ACH2': data['ACH2']['ACH2'],
            'ACH3': data['ACH3']['ACH3'],
            'ACH4': data['ACH4']['ACH4'],
            'PCW1 H0': 'Online',
            'PCW1 H1': 'Online',
            'PCW2 H1': 'Online',
            'PCW UPS+1': 'Online',
            'PCW UPS-1': 'Online',
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

    def set_first_program_run(self, data):
        for k in DEVs_prev_states.keys():
            DEVs_prev_states[k] = self.current_DEVs_state(data)
        self.first_program_run = False

    def send_alerts(self, message, send_alert_sets):
        if message:
            notifications, whatsapp, person_settings = send_alert_sets
            if notifications:
                channel_id = self.dict_person_settings[person_settings][1]
                self.mm.mm_post(' ' + message, channel_id)

                if self.settings['Plus WhatsApp'] == 1:
                    if whatsapp:
                        requests.post(
                            CALL_ME_BOT_URL + self.persons[person_settings] + ': ' + message + CALL_ME_BOT_APIKEY)
                time.sleep(1)

    def check_temp(self, x, settings, data, state):
        # x, self.persons[person_settings], data, state = 'inlet'

        if state == 'inlet':
            settings_key = '_inlet'
            data_key = 'Inlet Temp'
            message_key = "temp wejściowa"

        if state == 'outlet':
            settings_key = '_outlet'
            data_key = 'Outlet Temp'
            message_key = "temp wyjściowa"

        if self.settings[x + settings_key] < float(data[x][data_key]):
            if DEVs_prev_states[settings][x + settings_key]:
                value = float(data[x][data_key])
                message = f"{x} {message_key}: {value}C"
                DEVs_prev_states[settings][x + settings_key] = False
                return message
        else:
            DEVs_prev_states[settings][x + settings_key] = True
            return None

    def check_status(self, x, settings, data):
        # x, self.persons[person_settings], data

        if (DEVs_prev_states[settings][x] in ('Warning On', 'Local ON')) != (data[x][x] in ('Warning On', 'Local ON')):
            value = 'On' if data[x][x] in ('Warning On', 'Local ON') else data[x][x]
            message = f"{x}: {value}"
            DEVs_prev_states[settings][x] = data[x][x]
            return message
        else:
            DEVs_prev_states[settings][x] = data[x][x]
            return None

        if (DEVs_prev_states[self.persons[person_settings]][x] in ('Warning On', 'Local ON')) != (data[x][x] in ('Warning On', 'Local ON')):

            value = 'On' if data[x][x] in ('Warning On', 'Local ON') else data[x][x]
            message = f"{x}: {value}"
            self.send_alerts(message, send_alert_sets)

            DEVs_prev_states[self.persons[person_settings]][x] = data[x][x]
        else:
            DEVs_prev_states[self.persons[person_settings]][x] = data[x][x]

    def handle_offline(self, x, settings):
        if DEVs_prev_states[settings][x] == 'Offline':
            return None
        else:
            DEVs_prev_states[settings][x] = 'Offline'
            message = f'{x}: Offline.'
            return message

    def check(self, data, person_settings, notifications, whatsapp, zabbix_online):
        send_alert_sets = [notifications, whatsapp, person_settings]
        if self.first_program_run:

            if only_OO:
                self.settings = self.mm.make_dict_from_mm(self.dict_person_settings[person_settings][0])
                info_logger.info('%s %s', str(self.persons[person_settings]), str(self.settings) + '\n')
            self.set_first_program_run(data)

        try:

            if not only_OO:  # in only_OO mode the dips are used; if that mode is off it must be as switches are always on (notifications and whatsapp)
                self.settings = self.mm.make_dict_from_mm(self.dict_person_settings[person_settings][0])
                notifications = True
                whatsapp = True

            # destination of a channel if any parameters are out of tolerance
            channel_id = self.dict_person_settings[person_settings][1]

            # if user wish not to listen it will be omitted.
            if self.settings['Powiadomienia'] == 0:
                DEVs_prev_states[self.persons[person_settings]] = self.current_DEVs_state(data)
                return ''

            # CDUs operations and temp comparisons
            if zabbix_online == True:  # if there is data from Zabbix

                for x in [k for k in data.keys() if k[0:3] == 'CDU']:

                    if self.settings['CDUs_t1_min'] > float(data[x]['t1']):
                        if DEVs_prev_states[self.persons[person_settings]][x + '_t1_min']:
                            value = float(data[x]['t1'])
                            message = f"Niska Temp 1 {x} {value}C"
                            self.send_alerts(message, send_alert_sets)

                            DEVs_prev_states[self.persons[person_settings]][x + '_t1_min'] = False
                    else:
                        DEVs_prev_states[self.persons[person_settings]][x + '_t1_min'] = True

                    if self.settings['CDUs_t1_max'] < float(data[x]['t1']):
                        if DEVs_prev_states[self.persons[person_settings]][x + '_t1_max']:
                            value = float(data[x]['t1'])
                            message = f"Wysoka Temp 1 {x} {value}C"
                            self.send_alerts(message, send_alert_sets)

                            DEVs_prev_states[self.persons[person_settings]][x + '_t1_max'] = False
                    else:
                        DEVs_prev_states[self.persons[person_settings]][x + '_t1_max'] = True

                DEVs_prev_states[self.persons[person_settings]]['Zabbix'] = 1

            if zabbix_online == False and DEVs_prev_states[self.persons[person_settings]]['Zabbix'] == True:
                DEVs_prev_states[self.persons[person_settings]]['Zabbix'] = False
                message = f"Brak danych z Zabbix."
                self.send_alerts(message, send_alert_sets)

            # ACH's operations and temp comparisons
            for x in [k for k in data.keys() if k[0:3] == 'ACH']:
                try:

                    message = self.check_temp(x, self.persons[person_settings], data, state='inlet')
                    self.send_alerts(message, send_alert_sets)

                    message = self.check_temp(x, self.persons[person_settings], data, state='outlet')
                    self.send_alerts(message, send_alert_sets)

                    message = self.check_status(x, self.persons[person_settings], data)
                    self.send_alerts(message, send_alert_sets)

                except Exception:
                    message = self.handle_offline(x, self.persons[person_settings])
                    self.send_alerts(message, send_alert_sets)

            # PCWs operations and temp comparisons
            for x, y in [(k, '_'.join(k.split(' '))) for k in data.keys() if k[0:3] == 'PCW']:
                try:
                    if self.settings[y + '_return'] < float(data[x]['Return Air']):
                        if DEVs_prev_states[self.persons[person_settings]][y + '_return']:
                            value = float(data[x]['Return Air'])
                            message = f"{x} Return: {value}C"
                            self.send_alerts(message, send_alert_sets)

                            DEVs_prev_states[self.persons[person_settings]][y + '_return'] = False
                    else:
                        DEVs_prev_states[self.persons[person_settings]][y + '_return'] = True

                    DEVs_prev_states[self.persons[person_settings]][y] = 'Online'
                except Exception:
                    if DEVs_prev_states[self.persons[person_settings]][y] == 'Offline':
                        pass
                    else:
                        DEVs_prev_states[self.persons[person_settings]][y] = 'Offline'
                        message = f"{x} Offline."
                        self.send_alerts(message, send_alert_sets)

            if only_OO:
                return ('notifications' if (notifications and self.settings['Powiadomienia']) else '') + (
                    ', whatsapp' if (notifications and whatsapp and self.settings['Plus WhatsApp']) else '')
            else:
                return self.persons[person_settings].upper() + ' ' if self.settings['Plus WhatsApp'] else self.persons[person_settings] + ' '

        except Exception:
            return ''
