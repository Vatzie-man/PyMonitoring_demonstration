from typing import Any


class DictForDataBaseModification:
    def __init__(self):
        self.PCW_H1: str = ""
        self.data: dict
        self.dict_for_db: dict

    @staticmethod
    def assign_working_pcw(data):
        try:
            return "PCW1 H1" if data["PCW1 H1"]["PCW1 H1"] == "on" else "PCW2 H1"
        except Exception:
            return "PCW2 H1"

    @staticmethod
    def ares(data):
        try:
            return f"{int(float(data['Ares']) / 1000)} kW"
        except Exception:
            return f""

    @staticmethod
    def cdu_devices(data, device):
        try:
            return \
                (f'T1: {round(float(data[device]["t1"]), 1)}C | '
                 f'T2: {round(float(data[device]["t2"]), 1)}C | '
                 f'T3: {round(float(data[device]["t3"]), 1)}C | '
                 f'Pump: {data[device]["pumpspeed"]}% | '
                 f'Valve: {data[device]["valve"]}%')

        except Exception:
            return f"No Zabbix data"

    @staticmethod
    def ach_devices(data, device):

        return \
            (({"alert": data[device][device],
               "ambient_temp": data[device]['Ambient'],
               "Fan 1 on": data['ach_overview'][device]['Fan 1 on'],
               "Fan 1 off": data['ach_overview'][device]['Fan 1 off'],
               "Fan 2 on": data['ach_overview'][device]['Fan 2 on'],
               "Fan 2 off": data['ach_overview'][device]['Fan 2 off'],
               "data": f'Inlet: {data[device]["Inlet Temp"]}C | '
                       f'Outlet: {data[device]["Outlet Temp"]}C'
                       + (' | Pump ' if data[device]["Pumps"] else '')
                       + (' | Freecooling ' if data[device]["Freecooling"] else '')})

             if data["ach_overview"][device] != "no ACH connection"
             else ({"alert": "Offline", "data": "Offline"}))

    @staticmethod
    def pcw_devices(data, device):
        try:
            return \
                (f"Supply: {data[device[0]]['Supply Air']}C "
                 f"Return: {data[device[0]]['Return Air']}C | "
                 f"RH: {int(data[device[0]]['RH'])}% "
                 f"Fans: {int(data[device[0]]['Fan Speed'])}% "
                 f"Cool: {int(data[device[0]]['Cooling'])}%")
        except KeyError:
            return f"Offline"

    def dict_for_database(self, data) -> tuple[dict[str, str | dict[str, str | Any] | dict[str, str] | Any], str]:

        self.data = data
        self.PCW_H1 = self.assign_working_pcw(self.data)

        data_out = dict()

        data_out["Time"] = self.data["Time"]
        data_out["Ares"] = self.ares(self.data)

        # CDU devices dict
        for device in ["CDU1", "CDU2", "CDU3"]:
            data_out[device] = self.cdu_devices(self.data, device)

        # ACH devices dict
        for device in ["ACH1", "ACH2", "ACH3", "ACH4"]:
            data_out[device] = self.ach_devices(self.data, device)

        # PCW devices dict
        devs = {"PCW1 H0": "PCW1 H0", "PCW UPS+1": "Po UPS.1", "PCW UPS-1": "Po UPS-1", self.PCW_H1: self.PCW_H1}
        for device in devs.items():
            data_out[device[1]] = self.pcw_devices(self.data, device)

        def assign_data(data_out, num, field, default_value):
            """assign additional data for ACH devices"""
            try:
                data_out[f"{num}_{field}"] = f"{self.data['ach_overview'][f'ACH{num}'][field]}"
            except Exception:
                data_out[f"{num}_{field}"] = default_value

        # Fields and their default values
        fields_defaults = {
            "Time": "",
            "Fan": "Fan 1: .............................. (?)% | Fan 2: .............................. (?)%",
            "Compressor": "Comp 1: (??) | Comp 2: (??) | Comp 3: (??) | Comp 4: (??)",
            "Pump": "",
            "Temp and Free": "",
            "Condensing Pressure": "|",
            "Evaporating Pressure": "|",
            "Saturation Temp": "|",
            "Super Heating": "|",
            "Liquid Temp": "|",
            "Sub-Cooling": "|"
        }

        # Assign additional data for each ACH number
        for num in ["1", "2", "3", "4"]:
            for field, default_value in fields_defaults.items():
                assign_data(data_out, num, field, default_value)

        return data_out, self.PCW_H1
