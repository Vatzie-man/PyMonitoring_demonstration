from mattermost import MonitorChannels
from dataclasses import dataclass
from typing import Union
import requests
import typing
import time

from mattermost import Mattermost
from settings._pym_settings import secrets_oft, secrets_main, secrets_mm


@dataclass
class MessageAlerts:
    """"""
    whatsapp_destination: str = secrets_oft["call_me_bot_url"]
    whatsapp_apikey: str = secrets_oft["cal_me_bot_apikey"]
    mm = Mattermost()

    def send_alerts(self, message: str, send_alert_settings: list) -> None:
        """Send alerts via different chanels"""

        if message:
            notifications, whatsapp, channel_id, name = send_alert_settings
            if notifications:

                self.mm.mm_post(f"{message}", channel_id)

            if whatsapp:
                try:
                    requests.post(
                        self.whatsapp_destination + f"{message}" + self.whatsapp_apikey)
                except Exception:
                    # it happened that request caused crash on RPi possibly due to a network connectivity problem or DNS misconfiguration
                    pass

            time.sleep(1)


@dataclass
class OutOfTolerance:
    name = "wk"
    channel_id = secrets_oft["person_settings"][name][1]
    data = None
    user_settings = None
    devivces_previous_state = None

    mm_monitor_channels = MonitorChannels()
    send_alerts = MessageAlerts()
    mm = Mattermost()

    send_alert_settings = typing.List[str]
    first_program_run: bool = True
    zabbix_online: bool = False

    @staticmethod
    def devices_state_on_startup(data):
        def try_get_ach_state(dev):
            try:
                return data[dev][dev]
            except Exception:
                return "Offline"

        return {
            # states
            "ACH1": try_get_ach_state("ACH1"),
            "ACH2": try_get_ach_state("ACH2"),
            "ACH3": try_get_ach_state("ACH3"),
            "ACH4": try_get_ach_state("ACH4"),
            "PCW1 H0": "Online",
            "PCW1 H1": "Online",
            "PCW2 H1": "Online",
            "PCW UPS+1": "Online",
            "PCW UPS-1": "Online",
            # PowerMonitoring alarms and warnings
            "PowerMonitoring_status_online": True,
            "high_priority": int(data["power_monitoring"]["high_priority"]),
            "mid_priority": int(data["power_monitoring"]["mid_priority"]),
            "low_priority": int(data["power_monitoring"]["low_priority"]),
            # Zabbix
            "Zabbix_status_online": True,
            # CDUs temps
            "CDU1_t1_min": False,
            "CDU1_t1_max": False,
            "CDU2_t1_min": False,
            "CDU2_t1_max": False,
            "CDU3_t1_min": False,
            "CDU3_t1_max": False,
            # CDUs alarms and warnings
            "CDU1_num_alarms": int(data["CDU1"]["numalarms"]),
            "CDU1_num_warnings": int(data["CDU1"]["numwarnings"]),
            "CDU2_num_alarms": int(data["CDU2"]["numalarms"]),
            "CDU2_num_warnings": int(data["CDU2"]["numwarnings"]),
            "CDU3_num_alarms": int(data["CDU3"]["numalarms"]),
            "CDU3_num_warnings": int(data["CDU3"]["numwarnings"]),
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

    def check(self, data: dict, operation_settings: dict, notifications: bool, whatsapp: bool, check_channels: bool, zabbix_online: bool) -> [str,
                                                                                                                                              bool]:
        """Main function in this file: checks devices parameters against desired parameters"""
        self.data = data
        self.zabbix_online = zabbix_online
        self.user_settings = operation_settings

        if self.first_program_run:
            self.set_first_program_run()

        self.send_alert_settings = [notifications, whatsapp, self.channel_id, self.name]

        self.monitor_group_channels_for_posts(check_channels)

        self.power_monitoring_checks()
        self.zabbix_checks()
        self.ach_checks()
        self.pcw_checks()

        return ("notifications" if notifications else "") + (" whatsapp" if whatsapp else "")

    def set_first_program_run(self) -> None:
        """Assigns entry data"""
        self.devices_previous_state = self.devices_state_on_startup(self.data)
        self.first_program_run = False

    def monitor_group_channels_for_posts(self, check_channels) -> None:
        """check for new messages on channels"""
        if check_channels:
            self.monitor_channels()

    def monitor_channels(self) -> None:
        """Monitors MM channels for new messages"""
        message = self.mm_monitor_channels.get_new_messages()
        if message:
            self.send_alerts.send_alerts(message, self.send_alert_settings)

    def power_monitoring_checks(self) -> None:
        """ PowerMonitoring alarm check """
        if self.data["power_monitoring"]["is_there_mp_data"]:
            self.devices_previous_state["PowerMonitoring_status_online"] = True

            for alert in (self.data["power_monitoring"].keys() - {"is_there_mp_data"}):
                message = self.check_power_monitoring_alerts(alert)
                self.send_alerts.send_alerts(message, self.send_alert_settings)

        if not (self.data["power_monitoring"]["is_there_mp_data"]) and (self.devices_previous_state["PowerMonitoring_status_online"]):
            self.devices_previous_state["PowerMonitoring_status_online"] = False
            message = f"No data from PowerMonitoring."
            self.send_alerts.send_alerts(message, self.send_alert_settings)

    def check_power_monitoring_alerts(self, alert: str) -> Union[str, None]:
        """Checks whatever there is any alarm from PowerMonitoring"""
        message_keys = {"high_priority": "PowerMonitoring High", "mid_priority": "PowerMonitoring Medium", "low_priority": "PowerMonitoring Low"}

        if int(self.data["power_monitoring"][alert]) > self.devices_previous_state[alert]:
            message = f"{message_keys[alert]}: {self.data['power_monitoring'][alert]}"
            self.devices_previous_state[alert] = int(self.data["power_monitoring"][alert])
            return message
        else:
            self.devices_previous_state[alert] = int(self.data["power_monitoring"][alert])
            return None

    def zabbix_checks(self) -> None:
        """CDUs operations and temp comparisons"""
        if self.zabbix_online:  # is there data from Zabbix

            self.zabbix_temps_checks()
            self.zabbix_alarms_and_warnings_checks()

            self.devices_previous_state["Zabbix_status_online"] = True

        # if there is no data from zabbix in two request on the raw then alert message will be sent; though single occurances of no data is frequnent
        if not self.zabbix_online and self.devices_previous_state["Zabbix_status_online"]:
            self.devices_previous_state["Zabbix_status_online"] = False
            message = f"No data from Zabbix."
            self.send_alerts.send_alerts(message, self.send_alert_settings)

    def zabbix_temps_checks(self) -> None:
        """"""
        for device in [k for k in self.data.keys() if k[0:3] == "CDU"]:
            for state in ("CDUs_t1_min", "CDUs_t1_max"):
                message = self.check_temp(device, state=state)
                self.send_alerts.send_alerts(message, self.send_alert_settings)

    def zabbix_alarms_and_warnings_checks(self) -> None:
        """"""
        for dev in ["CDU1", "CDU2", "CDU3"]:

            if int(self.data[dev]["numalarms"]) > self.devices_previous_state[f"{dev}_num_alarms"]:
                message = f'{dev} Alarms: {self.data[dev]["numalarms"]}'
                self.send_alerts.send_alerts(message, self.send_alert_settings)
                self.devices_previous_state[f"{dev}_num_alarms"] = int(self.data[dev]["numalarms"])
            else:
                self.devices_previous_state[f"{dev}_num_alarms"] = int(self.data[dev]["numalarms"])

            if int(self.data[dev]["numwarnings"]) > self.devices_previous_state[f"{dev}_num_warnings"]:
                message = f'{dev}: Warnings: {self.data[dev]["numwarnings"]}'
                self.send_alerts.send_alerts(message, self.send_alert_settings)
                self.devices_previous_state[f"{dev}_num_warnings"] = int(self.data[dev]["numwarnings"])
            else:
                self.devices_previous_state[f"{dev}_num_warnings"] = int(self.data[dev]["numwarnings"])

    def ach_checks(self) -> None:
        """ACHs operations and temp comparisons"""
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

            except Exception:
                pass  # there is no need to deal with that

    def check_status(self, dev: str) -> Union[str, None]:
        """Checks the ACH devices state: ON/OFF/Standby"""
        if (self.devices_previous_state[dev] in ("Warning On", "Local ON")) != (self.data[dev][dev] in ("Warning On", "Local ON")):

            value = "On" if self.data[dev][dev] in ("Warning On", "Local ON") else self.data[dev][dev]
            message = f"{dev}: {value}"
            self.devices_previous_state[dev] = self.data[dev][dev]
            return message
        else:
            self.devices_previous_state[dev] = self.data[dev][dev]
            return None

    def check_temp(self, x: str, state: str):
        """Checks devices temp measures against desired temps"""
        x, y, z, settings_key, data_key, message_key = self.key_maker_for_check_temp(x, state)

        # it happens that temp value == 0 when there is problem with ACH communication (default values in enviro_alert)
        if (self.user_settings[y + settings_key] < float(self.data[x][data_key])) and (float(self.data[x][data_key]) != 0):

            if self.devices_previous_state[z + settings_key]:
                # check if temp was out of tolerance twice before rise warning as sometimes devices don't post values
                value = float(self.data[x][data_key])
                message = f"{x} {message_key}: {value}C"
                self.devices_previous_state[z + settings_key] = False
                return message

        else:
            self.devices_previous_state[z + settings_key] = True
            return None

    @staticmethod
    def key_maker_for_check_temp(x: str, state: str) -> tuple:
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
        """This function is called if an Exception has been raised during other checks"""
        if self.devices_previous_state[dev] == "Offline":
            return None
        else:
            self.devices_previous_state[dev] = "Offline"
            message = f"{dev}: Offline."
            return message
