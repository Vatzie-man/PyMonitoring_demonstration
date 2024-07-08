import json
import time

from helpers.chrome_options import get_chrome_options
from settings._pym_settings import secrets_enviro
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException

URL_ENVI = secrets_enviro["url_envi"]
USERNAME = secrets_enviro["username"]
PASSWORD = secrets_enviro["password"]


def initialize_driver():
    """Setup chrome driver"""
    driver = webdriver.Chrome(options=get_chrome_options())

    driver.implicitly_wait(10)
    driver.set_page_load_timeout(10)

    # Navigate to the login page !Seems it might work without that below
    driver.get(URL_ENVI)
    time.sleep(2)

    username_field = driver.find_element(By.NAME, "username")
    password_field = driver.find_element(By.NAME, "password")

    # Enter the username and password
    username_field.send_keys(USERNAME)
    password_field.send_keys(PASSWORD)

    login_button = driver.find_element(By.ID, "loginButton")
    login_button.click()
    time.sleep(2)

    return driver


class Alert:
    DICT_OF_DEV = secrets_enviro["dict_of_dev"]
    UNIT_STATUS_PARAMS = {
        12: "Standby",
        10: "Warning On",
        0: "Local ON",
        2: "Local OFF",
        8: "Power Failure",
        9: "Alarm ON",
        7: "No Water Flow"
    }

    def __init__(self):
        # occasionally device might send incomplete data; in that case previous status
        # is needed to avoid false alerts of state change
        self.DEVs_prev_states = {"ACH1": "Offline", "ACH2": "Offline", "ACH3": "Offline", "ACH4": "Offline"}

        self.driver = initialize_driver()

    def device_type(self, dev):
        """Strips full dev name to its type name"""
        return dev[0:3]

    @staticmethod
    def convert_str(s):
        """Proces str from http page"""
        count = 6
        while 1:
            try:
                out = float(s[1:count])
                break
            except:
                count -= 1
        return out

    def pcw(self, dev, page_source):
        """Fetch PCW devices"""

        def set_pcw_readings():
            data = [tuple(page_source.split(";")[x].split("=")) for x in range(1, 7)]

            return {
                dev: (data[0][1][1:3]),
                "Supply Air": Alert.convert_str(data[1][1]),
                "Return Air": Alert.convert_str(data[2][1]),
                "RH": Alert.convert_str(data[3][1]),
                "Fan Speed": Alert.convert_str(data[4][1]),
                "Cooling": Alert.convert_str(data[5][1])
            }

        def set_default_if_pcw_offline():
            """in the past this format was useful and was part of other function, now left for convenience"""
            return {
                "Unit": dev,
                "Return Air": "",
                "RH": ""
            }

        try:
            data = set_pcw_readings()
        except Exception:
            data = set_default_if_pcw_offline()

        return data

    def ach(self, page_source, dev):
        """Fetch ACH devises"""

        def set_ach_readings():
            data = json.loads(page_source[131:-20])

            # if the key is not in unit_status_parms then get that Key
            other = str(*data["values"][11]["value"]) + ": Stan nieokreślony."

            data = {
                dev: Alert.UNIT_STATUS_PARAMS.get(int(*data["values"][11]["value"]), other),
                "Inlet Temp": float(*data["values"][0]["value"]) / 10,
                "Outlet Temp": float(*data["values"][1]["value"]) / 10,
                "Ambient": float(*data["values"][3]["value"]) / 10,
                "Pumps": int(*data["values"][5]["value"]),
                "Compressors": int(*data["values"][6]["value"]),
                "Fans": int(*data["values"][7]["value"]),
                "Freecooling": int(*data["values"][8]["value"])
            }

            self.DEVs_prev_states[dev] = data[dev]
            return data

        def set_default_if_ach_offline():
            return {
                dev: self.DEVs_prev_states[dev],
                "Inlet Temp": 0.0,
                "Outlet Temp": 0.0,
                "Pumps": 0,
                "Compressors": 0,
                "Fans": 0,
                "Freecooling": 0
            }

        try:
            data = set_ach_readings()
        except Exception:
            data = set_default_if_ach_offline()

        return data

    def get_pcw_ach(self, lst_of_devs, dict_of_dev=None):
        """Fetch devices data"""
        data = {}
        if dict_of_dev is None:
            dict_of_dev = Alert.DICT_OF_DEV

        for dev in lst_of_devs:  # dev - http page
            data.update({dev: self.get_devices(dev, dict_of_dev, self.driver)})
        return data

    def get_devices(self, dev, dict_of_dev, driver):
        data = {}

        def fetch_dev_from_http():
            nonlocal data
            driver.get(dict_of_dev["server"][dev])
            page_source = driver.page_source
            dev_type = self.device_type(dev)
            if dev_type == "PCW":
                data = self.pcw(page_source=page_source, dev=dev)
            elif dev_type == "ACH":
                data = self.ach(page_source=page_source, dev=dev)
            return data

        def default_if_http_request_fails(e):
            nonlocal data
            if "ERR_CONNECTION_TIMED_OUT" in str(e):
                if dev[0:3] == "PCW":
                    data = {
                        "Unit": dev,
                        "Return Air": "",
                        "RH": ""
                    }
                else:
                    data = {dev: "Offline"}

            return data

        max_retries = 3
        for attempt in range(max_retries):

            try:
                data = fetch_dev_from_http()
                break

            except WebDriverException as e:
                if attempt < max_retries - 1:
                    time.sleep(10)

                else:
                    data = default_if_http_request_fails(e)

        return data


def main() -> None:
    o = Alert()
    print(o.get_pcw_ach(["PCW3 H1", "ACH1"]))


if __name__ == '__main__':
    main()
