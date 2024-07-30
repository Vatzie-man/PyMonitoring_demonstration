import time
import requests

from pyzabbix import ZabbixAPI
from collections import defaultdict
from settings._pym_settings import secrets_zabbix

ZABBIX_URL = secrets_zabbix["zabbix_url"]
ZABBIX_USER = secrets_zabbix["zabbix_user"]
ZABBIX_PASS = secrets_zabbix["zabbix_password"]

requests.packages.urllib3.disable_warnings()

session = requests.Session()
session.verify = False  # Disable SSL verification


class Zabbix:
    max_retries = 6
    retry_delay = 10

    @staticmethod
    def helper(data):

        for k, v in data.items():

            if k == "Total power usage":
                data[k] = data[k]["lastvalue"]

            if k != "Total power usage":
                data[k] = {
                    "pumpspeed": data[k]["pumpspeed"]["lastvalue"],
                    "valve": data[k]["valvefeedback"]["lastvalue"],

                    "t1": data[k]["t1"]["lastvalue"],
                    "t2": data[k]["t2"]["lastvalue"],
                    "t3": data[k]["t3"]["lastvalue"],
                    "t4": data[k]["t4"]["lastvalue"],
                    "numalarms": data[k]["numalarms"]["lastvalue"],
                    "numwarnings": data[k]["numwarnings"]["lastvalue"]
                }

        return {
            "status": True,
            "data": data
        }

    def __init__(self):
        self.zapi = None
        self.login()
        self.method = "item.get"
        self.params = {
            "jsonrpc": "2.0",
            "params": {},
            "auth": "",
            "id": 1
        }
        self.wanted_hosts = {
            "10401": "CDU1",
            "10680": "CDU2",
            "10681": "CDU3"
        }

    def login(self):
        self.zapi = ZabbixAPI(ZABBIX_URL, session=session)
        try:
            self.zapi.login(ZABBIX_USER, ZABBIX_PASS)  # when server was down it caused program crash
        except Exception:
            print("Can't login to zabbix.")

    def get_data(self):
        for retry_attempt in range(Zabbix.max_retries):
            try:
                return self.zapi.do_request(self.method, self.params)
            except Exception as e:
                print(f"{' '.join(time.asctime().split()[1:4])} > Unable to pull Zabbix data")
                time.sleep(Zabbix.retry_delay)
                self.login()

        return None

    def request(self):
        response = self.get_data()
        if response:
            out = response["result"][0:]

            data = [[self.wanted_hosts[x["hostid"]], x] for x in out if x["hostid"] in self.wanted_hosts.keys()]

            # print(data)
            # for k, v in response["result"][1].items():
            #     print(k, v)


            out = defaultdict(dict)
            out["Total power usage"] = {
                k: x for k, x in response["result"][0].items() if
                k not in ("name", "lastclock") and k == "lastvalue"
            }

            for x in data:
                out[x[0]][x[1]["name"]] = {k: x[1][k] for k in x[1].keys() if k != "name"}

            return self.helper(out)

        return {"status": False}


def main() -> None:
    get_data = Zabbix()
    data = get_data.request()
    print(data)

if __name__ == '__main__':
    main()
