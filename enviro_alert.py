import sys
import json
import time

from settings import secrets_enviro
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException

URL_ENVI = secrets_enviro['url_envi']
USERNAME = secrets_enviro['username']
PASSWORD = secrets_enviro['password']


def _get_chrome_options():
    '''Setup chrome driver'''
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option('prefs', {
        'credentials_enable_service': True,
        'profile.password_manager_enabled': True})

    # Create Chrome options with headless mode
    chrome_options.add_argument("--headless")
    return chrome_options


class Alert:
    DICT_OF_DEV = secrets_enviro['dict_of_dev']
    UNIT_STATUS_PARAMS = {
        12: 'Standby',
        10: 'Warning On',
        0: 'Local ON',
        2: 'Local OFF',
        8: 'Power Failure',
        9: 'Alarm ON'
    }

    def __init__(self):
        # occasionally device might send incomplete data; in that case previous status
        # is needed to avoid false alerts of state change
        self.DEVs_prev_states = {'ACH1': 'Offline', 'ACH2': 'Offline', 'ACH3': 'Offline', 'ACH4': 'Offline'}

        if sys.platform == 'win32':
            self.driver = webdriver.Chrome(options=_get_chrome_options())
        else:
            from selenium.webdriver.chrome.service import Service
            from pyvirtualdisplay import Display

            chrome_binary_path = Service('/usr/bin/chromedriver')

            display = Display(visible=False, size=(800, 600))
            display.start()

            self.driver = webdriver.Chrome(service=chrome_binary_path)

        self.driver.implicitly_wait(10)
        self.driver.set_page_load_timeout(10)

        # Navigate to the login page !Seems it might work without that below
        self.driver.get(URL_ENVI)
        time.sleep(1)

        username_field = self.driver.find_element(By.NAME, 'username')
        password_field = self.driver.find_element(By.NAME, 'password')

        # Enter the username and password
        username_field.send_keys(USERNAME)
        password_field.send_keys(PASSWORD)

        login_button = self.driver.find_element(By.ID, 'loginButton')
        login_button.click()
        time.sleep(2)

    def device_type(self, dev):
        '''Strips full dev name to it's type name'''
        return dev[0:3]

    @staticmethod
    def convert_str(s):
        '''Proces str from http page'''
        count = 6
        while 1:
            try:
                out = float(s[1:count])
                break
            except:
                count -= 1
        return out

    def pcw(self, dev, page_source):
        '''Fetch PCW devices'''
        try:
            data = [tuple(page_source.split(';')[x].split('=')) for x in range(1, 7)]

            return {
                dev: (data[0][1][1:3]),
                'Supply Air': Alert.convert_str(data[1][1]),
                'Return Air': Alert.convert_str(data[2][1]),
                'RH': Alert.convert_str(data[3][1]),
                'Fan Speed': Alert.convert_str(data[4][1]),
                'Cooling': Alert.convert_str(data[5][1])
            }

        except Exception:
            # in the past this format was useful and was part of other function, now left for convenience
            return {
                'Unit': dev,
                'Return Air': '',
                'RH': ''
            }

    def ach(self, page_source, dev):
        '''Fetch ACH devises'''
        try:
            data = json.loads(page_source[131:-20])
            # if the key is not in unit_status_parms to catch that rare Key
            other = str(*data['values'][11]['value'])

            data = {
                dev: Alert.UNIT_STATUS_PARAMS.get(int(*data['values'][11]['value']), other),
                'Inlet Temp': float(*data['values'][0]['value']) / 10,
                'Outlet Temp': float(*data['values'][1]['value']) / 10,
                'Pumps': int(*data['values'][5]['value']),
                'Compressors': int(*data['values'][6]['value']),
                'Fans': int(*data['values'][7]['value']),
                'Freecooling': int(*data['values'][8]['value'])
            }

            self.DEVs_prev_states[dev] = data[dev]
            return data

        except Exception:
            print(f"{' '.join(time.asctime().split()[1:4])} > EnviroAlert data error")

            return {
                dev: self.DEVs_prev_states[dev],
                'Inlet Temp': 0.0,
                'Outlet Temp': 0.0,
                'Pumps': 0,
                'Compressors': 0,
                'Fans': 0,
                'Freecooling': 0
            }

    def get_pcw_ach(self, lst_of_devs, dict_of_dev=None):
        '''Fetch devices data'''
        if dict_of_dev is None:
            dict_of_dev = Alert.DICT_OF_DEV

        data = dict()
        for dev in lst_of_devs:  # dev - http page
            data.update({dev: self.get_devices(dev, dict_of_dev, self.driver)})
        return data

    def get_devices(self, dev, dict_of_dev, driver):
        data = ''

        try:
            driver.get(dict_of_dev['server'][dev])
            page_source = driver.page_source
            dev_type = self.device_type(dev)

            if dev_type == 'PCW':
                data = self.pcw(page_source=page_source, dev=dev)
            elif dev_type == 'ACH':
                data = self.ach(page_source=page_source, dev=dev)

        # when the server is down return below
        except WebDriverException as e:
            if "ERR_CONNECTION_TIMED_OUT" in str(e):
                if dev[0:3] == 'PCW':
                    data = {
                        'Unit': dev,
                        'Return Air': '',
                        'RH': ''
                    }
                else:
                    # if there is not any data for ACH devices Offline status is assigned
                    data = {dev: 'Offline'}

        return data
