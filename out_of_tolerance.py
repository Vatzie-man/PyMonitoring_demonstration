from dataclasses import dataclass, field
from typing import Union
import requests
import typing
import time
import sys

from mattermost import Mattermost
from _pym_settings import secrets_oft, secrets_main, secrets_mm

if sys.platform == "win32":
    from mattermost import MonitorChannels

    platform = "WIN"
else:
    platform = "RPi"

watcher_alarm: bool = False


@dataclass
class MessageAlerts:
    watsapp_destination: str = secrets_oft["call_me_bot_url"]
    whatsapp_apikey: str = secrets_oft["cal_me_bot_apikey"]
    mm = Mattermost()

    def send_alerts(self, message: str, send_alert_settings: list) -> None:
        """Send alerts via different chanels"""
        global watcher_alarm

        if message:
            notifications, whatsapp, channel_id, name = send_alert_settings
            if notifications:

                watcher_alarm = True

                self.mm.mm_post(f"{message}", channel_id)

                if whatsapp:
                    try:
                        requests.post(
                            self.watsapp_destination + f"{message}" + self.whatsapp_apikey)
                    except Exception:
                        # it happend that request caused crash on RPi possibly due to a network connectivity problem or DNS misconfiguration
                        pass
            time.sleep(1)


@dataclass
class Person:
    name: str
    settings: str
    channel_id: str


@dataclass
class OutOfTolerance:
    if platform == "WIN":
        mm_monitor_channels = MonitorChannels()

    send_alerts = MessageAlerts()
    mm = Mattermost()

    person = Person

    send_alert_settings = typing.List[str]
    first_program_run: bool = True
    zabbix_online: bool = False
    devaices_prev_state = {"wk": None, "oo": None}

    @staticmethod
    def devaices_curr_state(data):
        def there_is_no_status(dev):
            try:
                return data[dev][dev]
            except Exception:
                return "Offline"

        return {
            # states
            "ACH1": there_is_no_status("ACH1"),
            "ACH2": there_is_no_status("ACH2"),
            "ACH3": there_is_no_status("ACH3"),
            "ACH4": there_is_no_status("ACH4"),
            "PCW1 H0": "Online",
            "PCW1 H1": "Online",
            "PCW2 H1": "Online",
            "PCW UPS+1": "Online",
            "PCW UPS-1": "Online",
            # PowerMonitoring
            "PowerMonitoring_status": True,
            "high_priority": int(data["power_monitoring"]["high_priority"]),
            "mid_priority": int(data["power_monitoring"]["mid_priority"]),
            "low_priority": int(data["power_monitoring"]["low_priority"]),
            # Zabbix
            "Zabbix": True,
            # CDUs temps
            "CDU1_t1_min": False,
            "CDU1_t1_max": False,
            "CDU2_t1_min": False,
            "CDU2_t1_max": False,
            "CDU3_t1_min": False,
            "CDU3_t1_max": False,
            # ACHs
            "ACH1_inlet": False,
            "ACH1_outlet": False,
            "ACH2_inlet": False,
            "ACH2_outlet": False,
            "ACH3_inlet": False,
            "ACH3_outlet": False,
            "ACH4_inlet": False,
            "ACH4_outlet": False,
            # PCWs
            "PCW1_H0_return": False,
            "PCW1_H1_return": False,
            "PCW2_H1_return": False,
            "PCW_UPS+1_return": False,
            "PCW_UPS-1_return": False,
        }

    def check(self, data: dict, opertatio_settings: dict, person: str, notifications: bool, whatsapp: bool, check_channels: bool, zabbix_online: bool) -> [str, bool]:
        """Main function in this file: checks devicase parameters against desired parameters"""
        global watcher_alarm
        self.data = data
        self.zabbix_online = zabbix_online
        self.user_settings = opertatio_settings

        if self.first_program_run:
            self.set_first_program_run(person)

        self.send_alert_settings = [notifications, whatsapp, self.person.channel_id, self.person.name]
        watcher_alarm = False

        self.extra_options_on_windows(check_channels)

        self.power_monitoring_checks()
        self.zabbix_checks()
        self.ach_checks()
        self.pcw_checks()

        return (("notifications" if notifications else "") + (", whatsapp" if (notifications and whatsapp) else ""), watcher_alarm)

    def set_first_program_run(self, person) -> None:
        """Assigns data to user"""
        self.person = Person(
            person,
            secrets_oft["person_settings"][person][0],
            secrets_oft["person_settings"][person][1]
        )
        # self.user_settings = self.mm.make_dict_from_mm(self.person.settings)

        # Assign default devices state at the begining
        for user in self.devaices_prev_state.keys():
            self.devaices_prev_state[user] = self.devaices_curr_state(self.data)
        self.first_program_run = False

    def extra_options_on_windows(self, check_channels) -> None:
        """check for new messages on channels"""
        if platform == "WIN":
            if check_channels:
                self.monitor_channels()

    def monitor_channels(self) -> None:
        """Monitors MM chcanels for new messages"""
        message = self.mm_monitor_channels.get_new_messages()
        if message: self.send_alerts.send_alerts(message, self.send_alert_settings)

    def power_monitoring_checks(self) -> None:
        """ PowerMonitoring alarm check """
        if self.data["power_monitoring"]["is_there_mp_data"]:
            self.devaices_prev_state[self.person.name]["PowerMonitoring_status"] = True

            for alert in (self.data["power_monitoring"].keys() - {"is_there_mp_data"}):
                message = self.check_PM_alerts(alert)
                self.send_alerts.send_alerts(message, self.send_alert_settings)

        if not (self.data["power_monitoring"]["is_there_mp_data"]) and (self.devaices_prev_state[self.person.name]["PowerMonitoring_status"]):
            self.devaices_prev_state[self.person.name]["PowerMonitoring_status"] = False
            message = f"Brak danych z PowerMonitoring."
            self.send_alerts.send_alerts(message, self.send_alert_settings)

    def check_PM_alerts(self, alert: str) -> Union[str, None]:
        """Checks whatever ther is any alarm from PowerMonitoring"""
        message_keys = {"high_priority": "PowerMonitoring High", "mid_priority": "PowerMonitoring Medium", "low_priority": "PowerMonitoring Low"}

        if int(self.data["power_monitoring"][alert]) > self.devaices_prev_state[self.person.name][alert]:
            message = f"{message_keys[alert]}: {self.data["power_monitoring"][alert]}"
            self.devaices_prev_state[self.person.name][alert] = int(self.data["power_monitoring"][alert])
            return message
        else:
            self.devaices_prev_state[self.person.name][alert] = int(self.data["power_monitoring"][alert])
            return None

    def zabbix_checks(self) -> None:
        """CDUs operations and temp comparisons"""
        if self.zabbix_online == True:  # is there data from Zabbix

            for device in [k for k in self.data.keys() if k[0:3] == "CDU"]:
                for state in ("CDUs_t1_min", "CDUs_t1_max"):
                    message = self.check_temp(device, state=state)
                    self.send_alerts.send_alerts(message, self.send_alert_settings)

            self.devaices_prev_state[self.person.name]["Zabbix"] = 1

        # if there is no data from zabbix in two request on the raw then alert message will be send; though single occurances of no data is frequnent
        if self.zabbix_online == False and self.devaices_prev_state[self.person.name]["Zabbix"] == True:
            self.devaices_prev_state[self.person.name]["Zabbix"] = False
            message = f"Brak danych z Zabbix."
            self.send_alerts.send_alerts(message, self.send_alert_settings)

    def ach_checks(self) -> None:
        """ACH"s operations and temp comparisons"""
        for device in [k for k in self.data.keys() if k[0:3] == "ACH"]:
            try:
                for state in ("ACH_inlet", "ACH_outlet"):
                    message = self.check_temp(device, state=state)
                    self.send_alerts.send_alerts(message, self.send_alert_settings)

                message = self.check_status(device)
                self.send_alerts.send_alerts(message, self.send_alert_settings)

            except Exception:
                message = self.handle_offline(device)
                self.send_alerts.send_alerts(message, self.send_alert_settings)

    def pcw_checks(self) -> None:
        """PCWs operations and temp comparisons"""
        for device in [k for k in self.data.keys() if k[0:3] == "PCW"]:

            try:
                message = self.check_temp(device, state="PCW_return")
                self.send_alerts.send_alerts(message, self.send_alert_settings)
                # if check_temp fails then check_status will not be called
                self.check_status(device)

            except Exception:
                message = self.handle_offline(device)
                # alerts are send to offten on windows
                # self.send_alerts.send_alerts(message, self.send_alert_settings)

    def check_status(self, dev: str) -> Union[str, None]:
        """Checks the ACH devices state: ON/OFF/Stadby; and assign online for PCW"""
        if dev[0:3] == "PCW":
            self.devaices_prev_state[self.person.name][dev] = "Online"

        if (self.devaices_prev_state[self.person.name][dev] in ("Warning On", "Local ON")) != (self.data[dev][dev] in ("Warning On", "Local ON")):

            value = "On" if self.data[dev][dev] in ("Warning On", "Local ON") else self.data[dev][dev]
            message = f"{dev}: {value}"
            self.devaices_prev_state[self.person.name][dev] = self.data[dev][dev]
            return message
        else:
            self.devaices_prev_state[self.person.name][dev] = self.data[dev][dev]
            return None

    def check_temp(self, x: str, state: str):
        """Checks devices temp mesaures against desired temps"""
        x, y, z, settings_key, data_key, message_key = self.key_maker_for_check_temp(x, state)

        if self.user_settings[y + settings_key] < float(self.data[x][data_key]):

            if self.devaices_prev_state[self.person.name][z + settings_key]:
                value = float(self.data[x][data_key])
                message = f"{x} {message_key}: {value}C"
                self.devaices_prev_state[self.person.name][z + settings_key] = False
                return message

        else:
            self.devaices_prev_state[self.person.name][z + settings_key] = True
            return None

    def key_maker_for_check_temp(self, x: str, state: str) -> tuple:
        """Creates keys pairs to combine different devices checks in one function"""
        if state == "ACH_inlet":
            return x, x, x, "_inlet", "Inlet Temp", "temp wejściowa"

        if state == "ACH_outlet":
            return x, x, x, "_outlet", "Outlet Temp", "temp wyjściowa"

        if state == "PCW_return":
            return x, x.replace(" ", "_"), x.replace(" ", "_"), "_return", "Return Air", "Return"

        if state == "CDUs_t1_min":
            return x, f"{x[0:3]}s", x, "_t1_min", "t1", "Niska Temp 1"

        if state == "CDUs_t1_max":
            return x, f"{x[0:3]}s", x, "_t1_max", "t1", "Wysoka Temp 1"

    def handle_offline(self, dev: str) -> Union[str, None]:
        """This function is called if an Exception has been rised during other checks"""
        if self.devaices_prev_state[self.person.name][dev] == "Offline":
            return None
        else:
            self.devaices_prev_state[self.person.name][dev] = "Offline"
            message = f"{dev}: Offline."
            return message
