
from selenium import webdriver

def get_chrome_options():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option('prefs', {
        'credentials_enable_service': True,
        'profile.password_manager_enabled': True})

    # Create Chrome options with headless mode
    chrome_options.add_argument('--ignore-ssl-errors=yes')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument("--headless")

    return chrome_options