import contextlib
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass
from _pym_settings import data_base


@dataclass
class Project:
    id: int
    title: str
    description: str
    alert: str
    other: str


class Repository(ABC):
    @abstractmethod
    def get(self, id: int):
        raise NotImplementedError

    @abstractmethod
    def get_all(self):
        raise NotImplementedError

    @abstractmethod
    def add(self, **kwargs: object):
        raise NotImplementedError

    @abstractmethod
    def update(self, id: int, **kwargs: object):
        raise NotImplementedError

    @abstractmethod
    def delete(self, id: int):
        raise NotImplementedError


class PostRepository(Repository):
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.create_table()

    @contextlib.contextmanager
    def connect(self):
        with sqlite3.connect(self.db_path) as conn:
            yield conn.cursor()

    def create_table(self) -> None:
        with self.connect() as cursor:
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS pages_project (id INTEGER PRIMARY KEY, title TEXT, description TEXT, alert TEXT, other TEXT)"
            )

    def get(self, id: int) -> Project:
        with self.connect() as cursor:
            cursor.execute("SELECT * FROM pages_project WHERE id=?", (id,))
            post = cursor.fetchone()
            if post is None:
                raise ValueError(f"Project with id {id} does not exist")
            return Project(*post)

    def get_all(self) -> list[Project]:
        with self.connect() as cursor:
            cursor.execute("SELECT * FROM pages_project")
            return [Project(*post) for post in cursor.fetchall()]

    def add(self, **kwargs: object) -> None:
        with self.connect() as cursor:
            cursor.execute(
                "INSERT INTO pages_project (title, description, alert, other) VALUES (?, ?, ?, ?)",
                (kwargs["title"], kwargs["description"], kwargs["alert"], kwargs["other"]),
            )

    def update(self, id: int, **kwargs: object) -> None:
        with self.connect() as cursor:
            cursor.execute(
                "UPDATE pages_project SET title=?, description=? , alert=?, other=? WHERE id=?",
                (kwargs["title"], kwargs["description"], kwargs["alert"], kwargs["other"], id),
            )

    def delete(self, id: int) -> None:
        with self.connect() as cursor:
            cursor.execute("DELETE FROM pages_project WHERE id=?", (id,))


class DjangoDataBase:
    def __init__(self):
        self.data = None
        self.dict_for_db = None
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
                 f'Pump: {data[device]["pumpspeed"]}%')
        except Exception:
            return f"No Zabbix data"

    @staticmethod
    def ach_devices(data, device):
        return (({"alert": data[device][device],
                  "data": f'Inlet: {data[device]["Inlet Temp"]}C '
                          f'Outlet: {data[device]["Outlet Temp"]}C'
                          + (' Pump ' if data[device]["Pumps"] else '')
                          + (' Compressors ' if data[device]["Compressors"] else '')
                          + (' Fans ' if data[device]["Fans"] else '')
                          + (' Freecooling ' if data[device]["Freecooling"] else '')})

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

    def dict_for_database(self) -> None:

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

        # ACH devices extra data dict
        for num in ["1", "2", "3", "4"]:

            try:
                data_out[num + "_Time_ACH"] = f"{self.data['ach_overview']['ACH' + num]['Time']}"
                data_out[num + "_Fan"] = f"{self.data['ach_overview']['ACH' + num]['Fan']}"
                data_out[num + "_Compressor"] = f"{self.data['ach_overview']['ACH' + num]['Compressor']}"
                data_out[num + "_Pump"] = f"{self.data['ach_overview']['ACH' + num]['Pump']}"
                data_out[num + "_Temp and Free"] = f"{self.data['ach_overview']['ACH' + num]['Temp and Free']}"
                data_out[num + "_Condensing Pressure"] = f"{self.data['ach_overview']['ACH' + num]['Condensing Pressure']}"
                data_out[num + "_Evaporating Pressure"] = f"{self.data['ach_overview']['ACH' + num]['Evaporating Pressure']}"
                data_out[num + "_Saturation Temp"] = f"{self.data['ach_overview']['ACH' + num]['Saturation Temp']}"
                data_out[num + "_Super Heating"] = f"{self.data['ach_overview']['ACH' + num]['Super Heating']}"
                data_out[num + "_Liquid Temp"] = f"{self.data['ach_overview']['ACH' + num]['Liquid Temp']}"
                data_out[num + "_Sub-Cooling"] = f"{self.data['ach_overview']['ACH' + num]['Sub-Cooling']}"

            except Exception:
                data_out[num + "_Time_ACH"] = f""
                data_out[num + "_Fan"] = f"Fan 1: .............................. (?)% | Fan 2: .............................. (?)%"
                data_out[num + "_Compressor"] = f"Comp 1: (??) | Comp 2: (??) | Comp 3: (??) | Comp 4: (??)"
                data_out[num + "_Pump"] = f""
                data_out[num + "_Temp and Free"] = f""
                data_out[num + "_Condensing Pressure"] = f""
                data_out[num + "_Evaporating Pressure"] = f""
                data_out[num + "_Saturation Temp"] = f""
                data_out[num + "_Super Heating"] = f""
                data_out[num + "_Liquid Temp"] = f""
                data_out[num + "_Sub-Cooling"] = f""

        self.dict_for_db = data_out

    def db_modification(self, data) -> None:

        repo = PostRepository(data_base['primary_db'])

        range_1 = {15: "1", 16: "1", 17: "1", 18: "1", 19: "1", 20: "1", 21: "1", 22: "1", 23: "1", 24: "1", 25: "1"}
        range_2 = {26: "2", 27: "2", 28: "2", 29: "2", 30: "2", 31: "2", 32: "2", 33: "2", 34: "2", 35: "2", 36: "2"}
        range_3 = {37: "3", 38: "3", 39: "3", 40: "3", 41: "3", 42: "3", 43: "3", 44: "3", 45: "3", 46: "3", 47: "3"}
        range_4 = {48: "4", 49: "4", 50: "4", 51: "4", 52: "4", 53: "4", 54: "4", 55: "4", 56: "4", 57: "4", 58: "4"}

        def assign_common_db():
            repo.update(1, title="Time", description=self.dict_for_db["Time"], alert="time", other="non")
            repo.update(2, title="Ares", description=self.dict_for_db["Ares"], alert="pm", other="non")
            repo.update(3, title="CDU1", description=self.dict_for_db["CDU1"], alert="non", other="non")
            repo.update(4, title="CDU2", description=self.dict_for_db["CDU2"], alert="non", other="non")
            repo.update(5, title="CDU3", description=self.dict_for_db["CDU3"], alert="line_after_cdu3", other="non")
            repo.update(6, title="ACH2", description=self.dict_for_db["ACH2"]["data"], alert=self.dict_for_db["ACH2"]["alert"], other="non")
            repo.update(7, title="ACH4", description=self.dict_for_db["ACH4"]["data"], alert=self.dict_for_db["ACH4"]["alert"], other="non")
            repo.update(8, title="ACH3", description=self.dict_for_db["ACH3"]["data"], alert=self.dict_for_db["ACH3"]["alert"], other="non")
            repo.update(9, title="ACH1", description=self.dict_for_db["ACH1"]["data"], alert=self.dict_for_db["ACH1"]["alert"], other="non")
            repo.update(10, title="PCW1 H0", description=self.dict_for_db["PCW1 H0"], alert="line_before_pcw1_h0", other="non")
            repo.update(11, title=self.PCW_H1, description=self.dict_for_db[self.PCW_H1], alert="non", other="non")
            repo.update(12, title="Po UPS.1", description=self.dict_for_db["Po UPS.1"], alert="non", other="non")
            repo.update(13, title="Po UPS-1", description=self.dict_for_db["Po UPS-1"], alert="non", other="non")

        def assign_ach_db(k, v):
            repo.update(k, title=v + "_Time_ACH", description=self.dict_for_db[v + "_Time_ACH"], alert="non", other="non")
            repo.update(k, title=v + "_Fan", description=self.dict_for_db[v + "_Fan"], alert="view_ach_detail_home", other="non")
            repo.update(k, title=v + "_Compressor", description=self.dict_for_db[v + "_Compressor"], alert="view_ach_detail_home", other="non")
            repo.update(k, title=v + "_Pump", description=self.dict_for_db[v + "_Pump"], alert="non", other="non")
            repo.update(k, title=v + "_Temp and Free", description=self.dict_for_db[v + "_Temp and Free"], alert="non", other="non")
            repo.update(k, title=v + "_Condensing Pressure", description=self.dict_for_db[v + "_Condensing Pressure"], alert="non", other="non")
            repo.update(k, title=v + "_Evaporating Pressure", description=self.dict_for_db[v + "_Evaporating Pressure"], alert="non", other="non")
            repo.update(k, title=v + "_Saturation Temp", description=self.dict_for_db[v + "_Saturation Temp"], alert="non", other="non")
            repo.update(k, title=v + "_Super Heating", description=self.dict_for_db[v + "_Super Heating"], alert="non", other="non")
            repo.update(k, title=v + "_Liquid Temp", description=self.dict_for_db[v + "_Liquid Temp"], alert="non", other="non")
            repo.update(k, title=v + "_Sub-Cooling", description=self.dict_for_db[v + "_Sub-Cooling"], alert="non", other="non")

        self.data = data
        self.dict_for_database()
        assign_common_db()

        for dic in (range_1, range_2, range_3, range_4):
            _ = (assign_ach_db(k, v) for k, v in dic.items())

# modify = DjangoDataBase()
# modify.db_modification()

        """
         # Add post to db:
         # repo.add(title="Listening", description="notifications, whatsapp", alert="non", other="non")

         # Get specific post from db:
         # print(repo.get(1))

         # Delete specific post from db:
         # repo.delete(14)

         # Update specific post in a db:
         # repo.update(1, title="Listening", description="notifications, whatsapp", alert="COS", other="COS2")

         # show post in db:
         # for i, x in enumerate(repo.get_all(), 1):
         #     print(i, x)
         """