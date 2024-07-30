from PyMonitoring.settings._pym_settings import data_base
from PyMonitoring.django_db.db_items import PostRepository
from PyMonitoring.django_db.create_dict_for_db import DictForDataBaseModification


class ModifyDB:

    def __init__(self):
        self.PCW_H1 = None
        self.dict_for_db: dict = {}
        self.django_db = DictForDataBaseModification()

    def db_modification(self, data) -> None:

        repo = PostRepository(data_base['primary_db'])

        def assign_common_db():
            for i in range(1, 14):
                repo.update(i,
                            title=get_title(i),
                            description=get_description(i),
                            txt_1="non",
                            txt_2="non",
                            txt_3="non",
                            txt_4="non",
                            alert=get_alert(i),
                            other="non")

        def assign_ach_db(d):

            for i in range(1, 12):
                try:
                    repo.update(d[i][0],
                                title=f"{v}_{get_suffix(i)}",
                                description=self.dict_for_db[d[i][1] + f"_{get_suffix(i)}"],
                                txt_1=self.dict_for_db["ACH" + d[i][1]]["Fan 1 on"],
                                txt_2=self.dict_for_db["ACH" + d[i][1]]["Fan 1 off"],
                                txt_3=self.dict_for_db["ACH" + d[i][1]]["Fan 2 on"],
                                txt_4=self.dict_for_db["ACH" + d[i][1]]["Fan 2 off"],
                                alert=get_alert_ach_db(i),
                                other=self.dict_for_db["ACH" + d[i][1]]["ambient_temp"])
                except Exception:
                    repo.update(d[i][0],
                                title=f"{v}_{get_suffix(i)}",
                                description=self.dict_for_db[d[i][1] + f"_{get_suffix(i)}"],
                                txt_1="0",
                                txt_2="102",
                                txt_3="0",
                                txt_4="102",
                                alert=get_alert_ach_db(i),
                                other="non")

        def get_alert_ach_db(i):
            alerts = ["non", "view_ach_detail_fans", "view_ach_detail_compressors", "non", "non", "non", "non", "non", "non", "non", "non"]
            return alerts[i - 1] if i <= len(alerts) else "non"

        def get_suffix(i):

            suffixes = ["Time",
                        "Fan",
                        "Compressor",
                        "Pump",
                        "Temp and Free",
                        "Condensing Pressure",
                        "Evaporating Pressure",
                        "Saturation Temp",
                        "Super Heating",
                        "Liquid Temp",
                        "Sub-Cooling"]

            return suffixes[i - 1] if i <= len(suffixes) else "non"

        def get_alert(i):

            alerts = ["time",
                      "pm",
                      "non",
                      "non",
                      "line_after_cdu3",
                      self.dict_for_db["ACH2"]["alert"],
                      self.dict_for_db["ACH4"]["alert"],
                      self.dict_for_db["ACH3"]["alert"],
                      self.dict_for_db["ACH1"]["alert"],
                      "line_before_pcw1_h0", "non", "non", "non"]

            return alerts[i - 1] if i <= len(alerts) else "non"

        def get_description(i):

            titles = [self.dict_for_db["Time"],
                      self.dict_for_db["Ares"],
                      self.dict_for_db["CDU1"],
                      self.dict_for_db["CDU2"],
                      self.dict_for_db["CDU3"],
                      self.dict_for_db["ACH2"]["data"],
                      self.dict_for_db["ACH4"]["data"],
                      self.dict_for_db["ACH3"]["data"],
                      self.dict_for_db["ACH1"]["data"],
                      self.dict_for_db["PCW1 H0"],
                      self.dict_for_db[self.PCW_H1],
                      self.dict_for_db["Po UPS.1"],
                      self.dict_for_db["Po UPS-1"]]

            return titles[i - 1] if i <= len(titles) else "non"

        def get_title(i):

            descriptions = ["Time",
                            "Ares",
                            "CDU1",
                            "CDU2",
                            "CDU3",
                            "ACH2",
                            "ACH4",
                            "ACH3",
                            "ACH1",
                            "PCW1 H0",
                            self.PCW_H1,
                            "Po UPS.1",
                            "Po UPS-1"]

            return descriptions[i - 1] if i <= len(descriptions) else "non"

        range_1 = {15: "1", 16: "1", 17: "1", 18: "1", 19: "1", 20: "1", 21: "1", 22: "1", 23: "1", 24: "1", 25: "1"}
        range_2 = {26: "2", 27: "2", 28: "2", 29: "2", 30: "2", 31: "2", 32: "2", 33: "2", 34: "2", 35: "2", 36: "2"}
        range_3 = {37: "3", 38: "3", 39: "3", 40: "3", 41: "3", 42: "3", 43: "3", 44: "3", 45: "3", 46: "3", 47: "3"}
        range_4 = {48: "4", 49: "4", 50: "4", 51: "4", 52: "4", 53: "4", 54: "4", 55: "4", 56: "4", 57: "4", 58: "4"}

        self.dict_for_db, self.PCW_H1 = self.django_db.dict_for_database(data)

        for dic in (range_1, range_2, range_3, range_4):
            dict_for_assign_ach_db, count = {}, 1
            for k, v in dic.items():
                dict_for_assign_ach_db[count] = [k, v]
                count += 1

            assign_ach_db(dict_for_assign_ach_db)

        assign_common_db()


def main() -> None:
    repo = PostRepository(data_base['primary_db'])

    # repo.add(title="Listening", description="notifications, whatsapp", txt_1="non", txt_2="non", txt_3="non", txt_4="non", alert="non", other="non")

    db_rows = repo.get_all()
    for row in db_rows:
        print(row)


if __name__ == '__main__':
    main()
