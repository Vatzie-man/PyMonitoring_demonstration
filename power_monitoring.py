import json
import time

from helpers.chrome_options import get_chrome_options
from _pym_settings import power_monitoring
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException

URL_ENVI = power_monitoring["url_pm"]
USERNAME = power_monitoring["username"]
PASSWORD = power_monitoring["password"]
URL_DATA = power_monitoring["url_data"]


def initialize_driver():
    """Setup chrome driver"""
    driver = webdriver.Chrome(options=get_chrome_options())

    driver.implicitly_wait(10)
    driver.set_page_load_timeout(10)

    driver.get(URL_ENVI)

    time.sleep(4)

    username_field = driver.find_element(By.NAME, "UserName")
    password_field = driver.find_element(By.NAME, "Password")

    username_field.send_keys(USERNAME)
    password_field.send_keys(PASSWORD)

    login_button = driver.find_element(By.ID, "logOnFormSubmitButton")

    login_button.click()
    time.sleep(2)

    return driver


class PowerMonitoringAlert:

    def __init__(self):

        self.driver = initialize_driver()

        self.driver = webdriver.Chrome(options=get_chrome_options())

        self.driver.implicitly_wait(10)
        self.driver.set_page_load_timeout(10)

        self.driver.get(URL_ENVI)

        time.sleep(6)

        username_field = self.driver.find_element(By.NAME, "UserName")
        password_field = self.driver.find_element(By.NAME, "Password")

        username_field.send_keys(USERNAME)
        password_field.send_keys(PASSWORD)

        login_button = self.driver.find_element(By.ID, "logOnFormSubmitButton")

        login_button.click()
        time.sleep(2)

    @staticmethod
    def extract_data(page_source):
        try:
            data = json.loads(page_source[99:-64])["AlarmCounts"]

            data = {
                "is_there_mp_data": True,
                "high_priority": data[0]["Count"],
                "mid_priority": data[1]["Count"],
                "low_priority": data[2]["Count"]
            }

            return data

        except Exception:

            with open("things/cached.txt", "a") as file:
                file.write(f"PowerMonitoring data error: \n{page_source}\n\n")

            print("PowerMonitoring data error")
            return {"is_there_mp_data": False, "high_priority": 0, "mid_priority": 0, "low_priority": 0}

    def get_power_monitoring_alerts(self):

        try:
            self.driver.get(URL_DATA)
            page_source = self.driver.page_source

            data = self.extract_data(page_source=page_source)
        except WebDriverException:
            print("WebDriverException")
            data = {"is_there_mp_data": False, "high_priority": 0, "mid_priority": 0, "low_priority": 0}

        return data

# o = PowerMonitoringAlert()
# print(o.get_power_monitoring_alerts())
