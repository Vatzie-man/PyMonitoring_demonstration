import json
import time

from helpers.chrome_options import get_chrome_options
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from settings._pym_settings import ACH_comp_fans_pumps, ACH_main_parameters


class AchOverview:
    UNIT_STATUS_PARAMS = {
        1: "ON",
        2: "MNT",
        3: "OFF",
        4: "ALM"
    }

    def __init__(self):
        self.driver = webdriver.Chrome(options=get_chrome_options())
        self.driver.implicitly_wait(10)
        self.driver.set_page_load_timeout(10)
        self.out = {"ACH2": {"main": None, "second": None}, "ACH4": {"main": None, "second": None}, "ACH3": {"main": None, "second": None},
                    "ACH1": {"main": None, "second": None}}

    @staticmethod
    def ach_comp_fans_pumps(data):

        out = dict()
        try:
            out["Pumps"] = \
                (f"Pump 1: {AchOverview.UNIT_STATUS_PARAMS.get(data[1]['value'][0])} | "
                 f"Pump 2: {AchOverview.UNIT_STATUS_PARAMS.get(data[1]['value'][1])}")

            out["Fans1"] = int(data[3]["value"][0])
            out["Fans2"] = int(data[4]["value"][0])

            out["Compressors"] = (
                f" Comp 1: {AchOverview.UNIT_STATUS_PARAMS.get(data[2]['value'][0])} | "
                f"Comp 2: {AchOverview.UNIT_STATUS_PARAMS.get(data[2]['value'][1])} | "
                f"Comp 3: {AchOverview.UNIT_STATUS_PARAMS.get(data[2]['value'][3])} | "
                f"Comp 4: {AchOverview.UNIT_STATUS_PARAMS.get(data[2]['value'][4])} ")

        except Exception:
            return ""

        return out

    @staticmethod
    def ach_main_parameters(data):

        out = dict()
        try:
            out["Temp Setpoint 1"] = f"{float(data[0]['value'][0] / 10)}C"
            out["Temp Setpoint 2"] = f"{float(data[1]['value'][0] / 10)}C"
            out["Temp Setpoint 3"] = f"{float(data[2]['value'][0] / 10)}C"
            out["Condensing Pressure (HP) C1"] = f"{float(data[3]['value'][0] / 10)} bar"
            out["Condensing Pressure (HP) C2"] = f"{float(data[4]['value'][0] / 10)} bar"
            out["Evaporating Pressure C1"] = f"{float(data[5]['value'][0] / 10)} bar"
            out["Evaporating Pressure C2"] = f"{float(data[5]['value'][1] / 10)} bar"
            out["Saturation Temp C1"] = f"{float(data[7]['value'][0] / 10)}C"
            out["Saturation Temp C2"] = f"{float(data[7]['value'][1] / 10)}C"
            # out["Condensing Temp C1"] = f""
            # out["Condensing Temp C2"] = f""
            out["Super Heating C1"] = f"{float(data[8]['value'][0] / 10)}K"
            out["Super Heating C2"] = f"{float(data[8]['value'][1] / 10)}K"
            out["Free Cooling Valve"] = f"{int(data[6]['value'][0] / 10)}%"
            out["Liquid Temp C1"] = f"{float(data[9]['value'][0] / 10)}C"
            out["Liquid Temp C2"] = f"{float(data[10]['value'][0] / 10)}C"
            out["Sub-Cooling C1"] = f"{float(data[11]['value'][0] / 10)}K"
            out["Sub-Cooling C2"] = f"{float(data[12]['value'][0] / 10)}K"

        except Exception:
            return ""

        return out

    @staticmethod
    def extract_data(page_source):
        try:
            data = json.loads(page_source[131:-20])["values"]
            return data
        except Exception:
            return None

    def source(self, page):

        try:
            self.driver.get(page)
            data = self.extract_data(page_source=self.driver.page_source)
            return data
        except WebDriverException:
            return "no ACH connection"

    def make_str(self):
        out = {"ACH2": None, "ACH4": None, "ACH3": None, "ACH1": None}

        for k in out.keys():
            temp = dict()

            temp["Time"] = f"{' '.join(time.asctime().split()[1:4])}"
            try:

                temp["Fan 1 on"] = f"{int(round(self.out[k]['second']['Fans1']))}"
                temp["Fan 1 off"] = f"{100 - int(round(self.out[k]['second']['Fans1']))}" if self.out[k]['second']['Fans1'] > 0 else f"102"
                temp["Fan 1 speed"] = f"{self.out[k]['second']['Fans1']}%"

                temp["Fan 2 on"] = f"{int(round(self.out[k]['second']['Fans2']))}"
                temp["Fan 2 off"] = f"{100 - int(round(self.out[k]['second']['Fans2']))}" if self.out[k]['second']['Fans2'] > 0 else f"102"
                temp["Fan 2 speed"] = f"{self.out[k]['second']['Fans2']}%"

                temp["Compressor"] = f"{self.out[k]['second']['Compressors']}"
                temp["Pump"] = f"{self.out[k]['second']['Pumps']}"

                temp["Temp and Free"] = (f"Setpoint: {self.out[k]['main']['Temp Setpoint 1']} | "
                                         f"Free Cooling Valve: {self.out[k]['main']['Free Cooling Valve']}")

                temp["Condensing Pressure"] = (f"Condensing Pressure (HP) C1: {self.out[k]['main']['Condensing Pressure (HP) C1']} | "
                                               f"Condensing Pressure (HP) C2: {self.out[k]['main']['Condensing Pressure (HP) C2']}")

                temp["Evaporating Pressure"] = (f"Evaporating Pressure C1: {self.out[k]['main']['Evaporating Pressure C1']} | "
                                                f"Evaporating Pressure C2: {self.out[k]['main']['Evaporating Pressure C2']}")

                temp["Saturation Temp"] = (f"Saturation Temp C1: {self.out[k]['main']['Saturation Temp C1']} |"
                                           f"Saturation Temp C2: {self.out[k]['main']['Saturation Temp C2']}")

                temp["Super Heating"] = (f"Super Heating C1: {self.out[k]['main']['Super Heating C1']} | "
                                         f"Super Heating C2: {self.out[k]['main']['Super Heating C2']}")

                temp["Liquid Temp"] = (f"Liquid Temp C1: {self.out[k]['main']['Liquid Temp C1']} | "
                                       f"Liquid Temp C2: {self.out[k]['main']['Liquid Temp C2']}")

                temp["Sub-Cooling"] = (f"Sub-Cooling C1: {self.out[k]['main']['Sub-Cooling C1']} | "
                                       f"Sub-Cooling C2: {self.out[k]['main']['Sub-Cooling C2']}")

                out[k] = temp

            except Exception:
                out[k] = f"no ACH connection"

        return out

    def get_ach_overview_info(self):

        for k, page in ACH_main_parameters.items():
            data = self.source(page)
            if data:
                self.out[k]["main"] = self.ach_main_parameters(data)

        for k, page in ACH_comp_fans_pumps.items():
            data = self.source(page)
            if data:
                self.out[k]["second"] = self.ach_comp_fans_pumps(data)

        out = self.make_str()
        return out


def main() -> None:
    o = AchOverview()
    out = o.get_ach_overview_info()
    for k, v in out.items():
        print(k, v)


if __name__ == '__main__':
    main()
