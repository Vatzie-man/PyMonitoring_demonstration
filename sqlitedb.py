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
        self.dict_for_db = None
        self.data = None
        self.PCW_H1: str = ""
        self.data: dict
        self.dict_for_db: dict

    def dict_for_database(self) -> None:

        try:
            self.PCW_H1 = "PCW1 H1" if self.data["PCW1 H1"]["PCW1 H1"] == "on" else "PCW2 H1"
        except Exception:
            self.PCW_H1 = "PCW2 H1"

        data_out = dict()

        data_out["Time"] = self.data["Time"]
        try:
            data_out["PM"] = (f"High: {self.data["power_monitoring"]["high_priority"]} Medium: {self.data["power_monitoring"]["mid_priority"]} "
                              f"Low: {self.data["power_monitoring"]["low_priority"]} | Ares: {int(float(self.data["Ares"]) / 1000)} kW")
        except Exception:
            data_out["PM"] = f""

        try:
            data_out["CDU1"] = \
                (f"T1: {round(float(self.data["CDU1"]["t1"]), 1)}C | "
                 f"T2: {round(float(self.data["CDU1"]["t2"]), 1)}C | "
                 f"T3: {round(float(self.data["CDU1"]["t3"]), 1)}C | "
                 f"Pump: {self.data["CDU1"]["pumpspeed"]}%")

            data_out["CDU2"] = \
                (f"T1: {round(float(self.data["CDU2"]["t1"]), 1)}C | "
                 f"T2: {round(float(self.data["CDU2"]["t2"]), 1)}C | "
                 f"T3: {round(float(self.data["CDU2"]["t3"]), 1)}C | "
                 f"Pump: {self.data["CDU2"]["pumpspeed"]}%")

            data_out["CDU3"] = \
                (f"T1: {round(float(self.data["CDU3"]["t1"]), 1)}C | "
                 f"T2: {round(float(self.data["CDU3"]["t2"]), 1)}C | "
                 f"T3: {round(float(self.data["CDU3"]["t3"]), 1)}C | "
                 f"Pump: {self.data["CDU3"]["pumpspeed"]}%")

        except Exception:
            data_out["CDU1"] = f"No Zabbix data"
            data_out["CDU2"] = f"No Zabbix data"
            data_out["CDU3"] = f"No Zabbix data"

        data_out["ACH2"] = (({"alert": self.data["ACH2"]["ACH2"],
                              "data": f"Inlet: {self.data["ACH2"]["Inlet Temp"]}C "
                                      f"Outlet: {self.data["ACH2"]["Outlet Temp"]}C"
                                      + (" Pump " if self.data["ACH2"]["Pumps"] else "")
                                      + (" Compressors " if self.data["ACH2"]["Compressors"] else "")
                                      + (" Fans " if self.data["ACH2"]["Fans"] else "")
                                      + (" Freecooling " if self.data["ACH2"]["Freecooling"] else "")})
                            if self.data["ach_overview"]["ACH2"] != "no ACH connection"
                            else ({"alert": "Offline", "data": "Offline"}))

        data_out["ACH4"] = (({"alert": self.data["ACH4"]["ACH4"],
                              "data": f"Inlet: {self.data["ACH4"]["Inlet Temp"]}C "
                                      f"Outlet: {self.data["ACH4"]["Outlet Temp"]}C"
                                      + (" Pump " if self.data["ACH4"]["Pumps"] else "")
                                      + (" Compressors " if self.data["ACH4"]["Compressors"] else "")
                                      + (" Fans " if self.data["ACH4"]["Fans"] else "")
                                      + (" Freecooling " if self.data["ACH4"]["Freecooling"] else "")})
                            if self.data["ach_overview"]["ACH4"] != "no ACH connection"
                            else ({"alert": "Offline", "data": "Offline"}))

        data_out["ACH3"] = (({"alert": self.data["ACH3"]["ACH3"],
                              "data": f"Inlet: {self.data["ACH3"]["Inlet Temp"]}C "
                                      f"Outlet: {self.data["ACH3"]["Outlet Temp"]}C"
                                      + (" Pump " if self.data["ACH3"]["Pumps"] else "")
                                      + (" Compressors " if self.data["ACH3"]["Compressors"] else "")
                                      + (" Fans " if self.data["ACH3"]["Fans"] else "")
                                      + (" Freecooling " if self.data["ACH3"]["Freecooling"] else "")})
                            if self.data["ach_overview"]["ACH3"] != "no ACH connection"
                            else ({"alert": "Offline", "data": "Offline"}))

        data_out["ACH1"] = (({"alert": self.data["ACH1"]["ACH1"],
                              "data": f"Inlet: {self.data["ACH1"]["Inlet Temp"]}C "
                                      f"Outlet: {self.data["ACH1"]["Outlet Temp"]}C"
                                      + (" Pump " if self.data["ACH1"]["Pumps"] else "")
                                      + (" Compressors " if self.data["ACH1"]["Compressors"] else "")
                                      + (" Fans " if self.data["ACH1"]["Fans"] else "")
                                      + (" Freecooling " if self.data["ACH1"]["Freecooling"] else "")})
                            if self.data["ach_overview"]["ACH1"] != "no ACH connection"
                            else ({"alert": "Offline", "data": "Offline"}))

        try:
            data_out["PCW1 H0"] = (f"Supply: {self.data["PCW1 H0"]["Supply Air"]}C "
                                   f"Return: {self.data["PCW1 H0"]["Return Air"]}C | "
                                   f"RH: {int(self.data["PCW1 H0"]["RH"])}% "
                                   f"Fans: {int(self.data["PCW1 H0"]["Fan Speed"])}% "
                                   f"Cool: {int(self.data["PCW1 H0"]["Cooling"])}%")
        except KeyError:
            data_out["PCW1 H0"] = f"Offline"

        try:
            data_out[self.PCW_H1] = (f"Supply: {self.data[self.PCW_H1]["Supply Air"]}C "
                                     f"Return: {self.data[self.PCW_H1]["Return Air"]}C | "
                                     f"RH: {int(self.data[self.PCW_H1]["RH"])}% "
                                     f"Fans: {int(self.data[self.PCW_H1]["Fan Speed"])}% "
                                     f"Cool: {int(self.data[self.PCW_H1]["Cooling"])}%")
        except KeyError:
            data_out[self.PCW_H1] = f"Offline"

        try:
            data_out["Po UPS.1"] = (f"Supply: {self.data["PCW UPS+1"]["Supply Air"]}C "
                                    f"Return: {self.data["PCW UPS+1"]["Return Air"]}C | "
                                    f"RH: {int(self.data["PCW UPS+1"]["RH"])}% "
                                    f"Fans: {int(self.data["PCW UPS+1"]["Fan Speed"])}% "
                                    f"Cool: {int(self.data["PCW UPS+1"]["Cooling"])}%")
        except KeyError:
            data_out["Po UPS.1"] = f"Offline"

        try:
            data_out["Po UPS-1"] = (f"Supply: {self.data["PCW UPS-1"]["Supply Air"]}C "
                                    f"Return: {self.data["PCW UPS-1"]["Return Air"]}C | "
                                    f"RH: {int(self.data["PCW UPS-1"]["RH"])}% "
                                    f"Fans: {int(self.data["PCW UPS-1"]["Fan Speed"])}% "
                                    f"Cool: {int(self.data["PCW UPS-1"]["Cooling"])}%")
        except KeyError:
            data_out["Po UPS-1"] = f"Offline"

        try:
            data_out["1_Time_ACH"] = f"{self.data["ach_overview"]["ACH1"]["Time"]}"
            data_out["1_Fan"] = f"{self.data["ach_overview"]["ACH1"]["Fan"]}"
            data_out["1_Compressor"] = f"{self.data["ach_overview"]["ACH1"]["Compressor"]}"
            data_out["1_Pump"] = f"{self.data["ach_overview"]["ACH1"]["Pump"]}"
            data_out["1_Temp and Free"] = f"{self.data["ach_overview"]["ACH1"]["Temp and Free"]}"
            data_out["1_Condensing Pressure"] = f"{self.data["ach_overview"]["ACH1"]["Condensing Pressure"]}"
            data_out["1_Evaporating Pressure"] = f"{self.data["ach_overview"]["ACH1"]["Evaporating Pressure"]}"
            data_out["1_Saturation Temp"] = f"{self.data["ach_overview"]["ACH1"]["Saturation Temp"]}"
            data_out["1_Super Heating"] = f"{self.data["ach_overview"]["ACH1"]["Super Heating"]}"
            data_out["1_Liquid Temp"] = f"{self.data["ach_overview"]["ACH1"]["Liquid Temp"]}"
            data_out["1_Sub-Cooling"] = f"{self.data["ach_overview"]["ACH1"]["Sub-Cooling"]}"
        except Exception:
            data_out["1_Time_ACH"] = f""
            data_out["1_Fan"] = f"Fan 1: .............................. (?)% | Fan 2: .............................. (?)%"
            data_out["1_Compressor"] = f"Comp 1: (??) | Comp 2: (??) | Comp 3: (??) | Comp 4: (??)"
            data_out["1_Pump"] = f""
            data_out["1_Temp and Free"] = f""
            data_out["1_Condensing Pressure"] = f""
            data_out["1_Evaporating Pressure"] = f""
            data_out["1_Saturation Temp"] = f""
            data_out["1_Super Heating"] = f""
            data_out["1_Liquid Temp"] = f""
            data_out["1_Sub-Cooling"] = f""

        try:
            data_out["2_Time_ACH"] = f"{self.data["ach_overview"]["ACH2"]["Time"]}"
            data_out["2_Fan"] = f"{self.data["ach_overview"]["ACH2"]["Fan"]}"
            data_out["2_Compressor"] = f"{self.data["ach_overview"]["ACH2"]["Compressor"]}"
            data_out["2_Pump"] = f"{self.data["ach_overview"]["ACH2"]["Pump"]}"
            data_out["2_Temp and Free"] = f"{self.data["ach_overview"]["ACH2"]["Temp and Free"]}"
            data_out["2_Condensing Pressure"] = f"{self.data["ach_overview"]["ACH2"]["Condensing Pressure"]}"
            data_out["2_Evaporating Pressure"] = f"{self.data["ach_overview"]["ACH2"]["Evaporating Pressure"]}"
            data_out["2_Saturation Temp"] = f"{self.data["ach_overview"]["ACH2"]["Saturation Temp"]}"
            data_out["2_Super Heating"] = f"{self.data["ach_overview"]["ACH2"]["Super Heating"]}"
            data_out["2_Liquid Temp"] = f"{self.data["ach_overview"]["ACH2"]["Liquid Temp"]}"
            data_out["2_Sub-Cooling"] = f"{self.data["ach_overview"]["ACH2"]["Sub-Cooling"]}"
        except Exception:
            data_out["2_Time_ACH"] = f""
            data_out["2_Fan"] = f"Fan 1: .............................. (?)% | Fan 2: .............................. (?)%"
            data_out["2_Compressor"] = f"Comp 1: (??) | Comp 2: (??) | Comp 3: (??) | Comp 4: (??)"
            data_out["2_Pump"] = f""
            data_out["2_Temp and Free"] = f""
            data_out["2_Condensing Pressure"] = f""
            data_out["2_Evaporating Pressure"] = f""
            data_out["2_Saturation Temp"] = f""
            data_out["2_Super Heating"] = f""
            data_out["2_Liquid Temp"] = f""
            data_out["2_Sub-Cooling"] = f""

        try:
            data_out["3_Time_ACH"] = f"{self.data["ach_overview"]["ACH3"]["Time"]}"
            data_out["3_Fan"] = f"{self.data["ach_overview"]["ACH3"]["Fan"]}"
            data_out["3_Compressor"] = f"{self.data["ach_overview"]["ACH3"]["Compressor"]}"
            data_out["3_Pump"] = f"{self.data["ach_overview"]["ACH3"]["Pump"]}"
            data_out["3_Temp and Free"] = f"{self.data["ach_overview"]["ACH3"]["Temp and Free"]}"
            data_out["3_Condensing Pressure"] = f"{self.data["ach_overview"]["ACH3"]["Condensing Pressure"]}"
            data_out["3_Evaporating Pressure"] = f"{self.data["ach_overview"]["ACH3"]["Evaporating Pressure"]}"
            data_out["3_Saturation Temp"] = f"{self.data["ach_overview"]["ACH3"]["Saturation Temp"]}"
            data_out["3_Super Heating"] = f"{self.data["ach_overview"]["ACH3"]["Super Heating"]}"
            data_out["3_Liquid Temp"] = f"{self.data["ach_overview"]["ACH3"]["Liquid Temp"]}"
            data_out["3_Sub-Cooling"] = f"{self.data["ach_overview"]["ACH3"]["Sub-Cooling"]}"
        except Exception:
            data_out["3_Time_ACH"] = f""
            data_out["3_Fan"] = f"Fan 1: .............................. (?)% | Fan 2: .............................. (?)%"
            data_out["3_Compressor"] = f"Comp 1: (??) | Comp 2: (??) | Comp 3: (??) | Comp 4: (??)"
            data_out["3_Pump"] = f""
            data_out["3_Temp and Free"] = f""
            data_out["3_Condensing Pressure"] = f""
            data_out["3_Evaporating Pressure"] = f""
            data_out["3_Saturation Temp"] = f""
            data_out["3_Super Heating"] = f""
            data_out["3_Liquid Temp"] = f""
            data_out["3_Sub-Cooling"] = f""

        try:
            data_out["4_Time_ACH"] = f"{self.data["ach_overview"]["ACH4"]["Time"]}"
            data_out["4_Fan"] = f"{self.data["ach_overview"]["ACH4"]["Fan"]}"
            data_out["4_Compressor"] = f"{self.data["ach_overview"]["ACH4"]["Compressor"]}"
            data_out["4_Pump"] = f"{self.data["ach_overview"]["ACH4"]["Pump"]}"
            data_out["4_Temp and Free"] = f"{self.data["ach_overview"]["ACH4"]["Temp and Free"]}"
            data_out["4_Condensing Pressure"] = f"{self.data["ach_overview"]["ACH4"]["Condensing Pressure"]}"
            data_out["4_Evaporating Pressure"] = f"{self.data["ach_overview"]["ACH4"]["Evaporating Pressure"]}"
            data_out["4_Saturation Temp"] = f"{self.data["ach_overview"]["ACH4"]["Saturation Temp"]}"
            data_out["4_Super Heating"] = f"{self.data["ach_overview"]["ACH4"]["Super Heating"]}"
            data_out["4_Liquid Temp"] = f"{self.data["ach_overview"]["ACH4"]["Liquid Temp"]}"
            data_out["4_Sub-Cooling"] = f"{self.data["ach_overview"]["ACH4"]["Sub-Cooling"]}"
        except Exception:
            data_out["4_Time_ACH"] = f""
            data_out["4_Fan"] = f"Fan 1: .............................. (?)% | Fan 2: .............................. (?)%"
            data_out["4_Compressor"] = f"Comp 1: (??) | Comp 2: (??) | Comp 3: (??) | Comp 4: (??)"
            data_out["4_Pump"] = f""
            data_out["4_Temp and Free"] = f""
            data_out["4_Condensing Pressure"] = f""
            data_out["4_Evaporating Pressure"] = f""
            data_out["4_Saturation Temp"] = f""
            data_out["4_Super Heating"] = f""
            data_out["4_Liquid Temp"] = f""
            data_out["4_Sub-Cooling"] = f""

        self.dict_for_db = data_out

    def db_modification(self, data) -> None:
        """
        # Add post to db:
        # repo.add(title="Listening", description="notifications, whatsapp", alert="non", other="non")

        # Get specific post from db:
        # print(repo.get(1))

        # Delete specific post from db:
        # repo.delete(14)

        # Update specyfic post in a db:
        # repo.update(1, title="Listening", description="notifications, whatsapp", alert="COS", other="COS2")

        # show post in db:
        # for i, x in enumerate(repo.get_all(), 1):
        #     print(i, x)
        """

        self.data = data
        self.dict_for_database()
        repo = PostRepository(data_base["primary_db"])

        repo.update(1, title="Time", description=self.dict_for_db["Time"], alert="time", other="non")
        repo.update(2, title="PM", description=self.dict_for_db["PM"], alert="pm", other="non")
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

        repo.update(15, title="1_Time_ACH", description=self.dict_for_db["1_Time_ACH"], alert="non", other="non")
        repo.update(16, title="1_Fan", description=self.dict_for_db["1_Fan"], alert="view_ach_detail_home", other="non")
        repo.update(17, title="1_Compressor", description=self.dict_for_db["1_Compressor"], alert="view_ach_detail_home", other="non")
        repo.update(18, title="1_Pump", description=self.dict_for_db["1_Pump"], alert="non", other="non")
        repo.update(19, title="1_Temp and Free", description=self.dict_for_db["1_Temp and Free"], alert="non", other="non")
        repo.update(20, title="1_Condensing Pressure", description=self.dict_for_db["1_Condensing Pressure"], alert="non", other="non")
        repo.update(21, title="1_Evaporating Pressure", description=self.dict_for_db["1_Evaporating Pressure"], alert="non", other="non")
        repo.update(22, title="1_Saturation Temp", description=self.dict_for_db["1_Saturation Temp"], alert="non", other="non")
        repo.update(23, title="1_Super Heating", description=self.dict_for_db["1_Super Heating"], alert="non", other="non")
        repo.update(24, title="1_Liquid Temp", description=self.dict_for_db["1_Liquid Temp"], alert="non", other="non")
        repo.update(25, title="1_Sub-Cooling", description=self.dict_for_db["1_Sub-Cooling"], alert="non", other="non")

        repo.update(26, title="2_Time_ACH", description=self.dict_for_db["2_Time_ACH"], alert="non", other="non")
        repo.update(27, title="2_Fan", description=self.dict_for_db["2_Fan"], alert="view_ach_detail_home", other="non")
        repo.update(28, title="2_Compressor", description=self.dict_for_db["2_Compressor"], alert="view_ach_detail_home", other="non")
        repo.update(29, title="2_Pump", description=self.dict_for_db["2_Pump"], alert="non", other="non")
        repo.update(30, title="2_Temp and Free", description=self.dict_for_db["2_Temp and Free"], alert="non", other="non")
        repo.update(31, title="2_Condensing Pressure", description=self.dict_for_db["2_Condensing Pressure"], alert="non", other="non")
        repo.update(32, title="2_Evaporating Pressure", description=self.dict_for_db["2_Evaporating Pressure"], alert="non", other="non")
        repo.update(33, title="2_Saturation Temp", description=self.dict_for_db["2_Saturation Temp"], alert="non", other="non")
        repo.update(34, title="2_Super Heating", description=self.dict_for_db["2_Super Heating"], alert="non", other="non")
        repo.update(35, title="2_Liquid Temp", description=self.dict_for_db["2_Liquid Temp"], alert="non", other="non")
        repo.update(36, title="2_Sub-Cooling", description=self.dict_for_db["2_Sub-Cooling"], alert="non", other="non")

        repo.update(37, title="3_Time_ACH", description=self.dict_for_db["3_Time_ACH"], alert="non", other="non")
        repo.update(38, title="3_Fan", description=self.dict_for_db["3_Fan"], alert="view_ach_detail_home", other="non")
        repo.update(39, title="3_Compressor", description=self.dict_for_db["3_Compressor"], alert="view_ach_detail_home", other="non")
        repo.update(40, title="3_Pump", description=self.dict_for_db["3_Pump"], alert="non", other="non")
        repo.update(41, title="3_Temp and Free", description=self.dict_for_db["3_Temp and Free"], alert="non", other="non")
        repo.update(42, title="3_Condensing Pressure", description=self.dict_for_db["3_Condensing Pressure"], alert="non", other="non")
        repo.update(43, title="3_Evaporating Pressure", description=self.dict_for_db["3_Evaporating Pressure"], alert="non", other="non")
        repo.update(44, title="3_Saturation Temp", description=self.dict_for_db["3_Saturation Temp"], alert="non", other="non")
        repo.update(45, title="3_Super Heating", description=self.dict_for_db["3_Super Heating"], alert="non", other="non")
        repo.update(46, title="3_Liquid Temp", description=self.dict_for_db["3_Liquid Temp"], alert="non", other="non")
        repo.update(47, title="3_Sub-Cooling", description=self.dict_for_db["3_Sub-Cooling"], alert="non", other="non")

        repo.update(48, title="4_Time_ACH", description=self.dict_for_db["4_Time_ACH"], alert="non", other="non")
        repo.update(49, title="4_Fan", description=self.dict_for_db["4_Fan"], alert="view_ach_detail_home", other="non")
        repo.update(50, title="4_Compressor", description=self.dict_for_db["4_Compressor"], alert="view_ach_detail_home", other="non")
        repo.update(51, title="4_Pump", description=self.dict_for_db["4_Pump"], alert="non", other="non")
        repo.update(52, title="4_Temp and Free", description=self.dict_for_db["4_Temp and Free"], alert="non", other="non")
        repo.update(53, title="4_Condensing Pressure", description=self.dict_for_db["4_Condensing Pressure"], alert="non", other="non")
        repo.update(54, title="4_Evaporating Pressure", description=self.dict_for_db["4_Evaporating Pressure"], alert="non", other="non")
        repo.update(55, title="4_Saturation Temp", description=self.dict_for_db["4_Saturation Temp"], alert="non", other="non")
        repo.update(56, title="4_Super Heating", description=self.dict_for_db["4_Super Heating"], alert="non", other="non")
        repo.update(57, title="4_Liquid Temp", description=self.dict_for_db["4_Liquid Temp"], alert="non", other="non")
        repo.update(58, title="4_Sub-Cooling", description=self.dict_for_db["4_Sub-Cooling"], alert="non", other="non")

    # for i, x in enumerate(repo.get_all(), 1):
    #     print(i, x)

# modify = DjangoDataBase()
# modify.db_modification()
