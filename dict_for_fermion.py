import time


class Dict_For_Fermion:

    def __init__(self):
        self.out = {
            "time": "",
            "CDU_t1": "",
            "CDU_t4": "",
            "ACH2": "",
            "ACH4": "",
            "ACH3": "",
            "ACH1": "",
            "ACH2_Return": "",
            "ACH4_Return": "",
            "ACH3_Return": "",
            "ACH1_Return": "",
            "H1": "",
            "H0": "",
            "UPS+1": "",
            "UPS-1": ""}

    def dict_for_fermion(self, data_dict):

        ach_devices = ["ACH2", "ACH4", "ACH3", "ACH1"]
        pcw_devices = ["PCW1 H0", "PCW1 H1", "PCW2 H1", "PCW UPS+1", "PCW UPS-1"]
        cdu_devices = ["CDU1", "CDU2", "CDU3"]

        for i in ach_devices:

            try:
                if data_dict[i][i] == "Local ON" or data_dict[i][i] == "Warning On":
                    self.out[i] = "on"
                    self.out[i + "_Return"] = data_dict[i]["Outlet Temp"]

                if data_dict[i][i] == "Standby":
                    self.out[i] = "st"
                    self.out[i + "_Return"] = data_dict[i]["Outlet Temp"]

                if data_dict[i][i] == "Local OFF" or data_dict[i][i] == "Power Failure" or data_dict[i] == "Alarm ON":
                    self.out[i] = "er"
                    self.out[i + "_Return"] = data_dict[i]["Outlet Temp"]

            except Exception:
                pass

        # PCWs - PCW1/PCW2 on H1 is changing
        for x in pcw_devices:

            try:
                if x == "PCW1 H0":
                    i = "H0"
                if x == "PCW1 H1":
                    i = "H1"
                if x == "PCW2 H1":
                    i = "H1"
                if x == "PCW UPS+1":
                    i = "UPS+1"
                if x == "PCW UPS-1":
                    i = "UPS-1"

                if data_dict[x][x] == "Offline":
                    self.out[i] = "BRAK"

                if data_dict[x][x] == "on":
                    self.out[i] = str(data_dict[x]["Return Air"])

                if data_dict[x][x] == "of":
                    pass

            except Exception:
                pass

        # CDUs
        if (dev for dev in cdu_devices) in data_dict.keys():

            try:
                cdu_1_temp = 0
                cdu_4_temp = 0

                for i in cdu_devices:
                    cdu_1_temp += float(data_dict[i]["t1"])
                    cdu_4_temp += float(data_dict[i]["t4"])

                self.out["CDU_t1"] = str(cdu_1_temp / 3)[0:4]
                self.out["CDU_t4"] = str(cdu_4_temp / 3)[0:4]

            except:
                pass

        # time
        self.out["time"] = " ".join(time.asctime().split()[3:4])[0:-3]

        return self.out
