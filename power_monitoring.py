import sys
import json
import time

from settings import power_monitoring
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException

URL_ENVI = power_monitoring['url_pm']
USERNAME = power_monitoring['username']
PASSWORD = power_monitoring['password']
URL_DATA = power_monitoring['url_data']


def _get_chrome_options():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option('prefs', {
        'credentials_enable_service': True,
        'profile.password_manager_enabled': True})

    # Create Chrome options with headless mode
    chrome_options.add_argument('--ignore-ssl-errors=yes')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument("--headless")

    return chrome_options


class PowerMonitoringAlert:

    def __init__(self):

        if sys.platform == 'win32':
            self.driver = webdriver.Chrome(options=_get_chrome_options())
        else:
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.chrome.options import Options
            from pyvirtualdisplay import Display

            chrome_options = Options()
            chrome_options.add_argument('--ignore-ssl-errors=yes')
            chrome_options.add_argument('--ignore-certificate-errors')

            chrome_binary_path = Service('/usr/bin/chromedriver')

            display = Display(visible=False, size=(800, 600))
            display.start()

            self.driver = webdriver.Chrome(service=chrome_binary_path, options=chrome_options)

        self.driver.implicitly_wait(10)
        self.driver.set_page_load_timeout(10)

        self.driver.get(URL_ENVI)

        time.sleep(2)

        username_field = self.driver.find_element(By.NAME, 'UserName')
        password_field = self.driver.find_element(By.NAME, 'Password')

        username_field.send_keys(USERNAME)
        password_field.send_keys(PASSWORD)

        login_button = self.driver.find_element(By.ID, 'logOnFormSubmitButton')

        login_button.click()
        time.sleep(1)

    def extract_data(self, page_source):

        try:
            data = json.loads(page_source[99:-64])['AlarmCounts']

            data = {
                'status': True,
                'high_priority': data[0]['Count'],
                'mid_priority': data[1]['Count'],
                'low_priority': data[2]['Count']
            }
            return data

        except Exception:
            print('PowerMonitoring data error')
            return {'status': False, 'high_priority': 0, 'mid_priority': 0, 'low_priority': 0}

    def get_power_monitoring_alerts(self):

        try:
            self.driver.get(URL_DATA)
            page_source = self.driver.page_source

            data = self.extract_data(page_source=page_source)
        except WebDriverException:
            data = {'status': False, 'high_priority': 0, 'mid_priority': 0, 'low_priority': 0}

        return data

# o = PowerMonitoringAlert()
# print(o.get_power_monitoring_alerts())


