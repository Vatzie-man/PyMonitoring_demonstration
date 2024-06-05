import time
import requests
from mattermost import Mattermost
from _pym_settings import secrets_oft, secrets_main, secrets_mm

destination: str = secrets_oft["call_me_bot_url"]
apikey: str = secrets_oft["cal_me_bot_apikey"]

dtp_destination_test: str = secrets_oft["call_me_bot_url_dtp_test"]
dtp_apikey_test: str = secrets_oft["cal_me_bot_apikey_dtp_test"]

vatzie_post_to_edit = secrets_main["vatzie_post_to_edit"]
vatzie_mm_api_token = secrets_mm["mm_waclaw_apikey"]

mm = Mattermost()


def connections_channels_checks() -> None:
    """Triggers test alarms, so the user is assured that alarms works"""
    requests.post(destination + "Test_Vatzie" + apikey)
    time.sleep(1)
    requests.post(dtp_destination_test + "Test_DTP" + dtp_apikey_test)
    time.sleep(1)
    # prevent apikey to get old
    mm.mm_edit(f"**Powyżej aktualne nastawy.** ({str(*time.asctime().split()[3:4])})", vatzie_post_to_edit, vatzie_mm_api_token)


connections_channels_checks()
