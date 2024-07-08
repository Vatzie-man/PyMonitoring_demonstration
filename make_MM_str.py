import time


class MmStr:

    def __init__(self):
        pass

    @staticmethod
    def which_dot(s: str) -> str:

        stats = {
            "Standby": ":large_yellow_circle:",
            "Warning On": ":large_green_circle:",
            "Local ON": ":large_green_circle:",
            "Local OFF": ":red_circle:",
            "Alarm ON": ":red_circle:",
            "Power Failure": ":red_circle:"
        }

        return stats.get(s, "Stan:" + s)

    @staticmethod
    def make_mm_str(data: dict) -> str:

        global ACH1_Fans, ACH_1_Compressors, ACH_2_Compressors, ACH3_Fans, ACH2_Fans, ACH_3_Compressors, ACH_4_Compressors, ACH4_Fans
        info = ""

        for k, v in data.items():

            if k == "ach_overview":
                ACH1_Fans = (f'Fan 1: {"|" * int(int(data["ach_overview"]["ACH1"]["Fan 1 on"]) / 5)}'
                             f'{".." * int(int(data["ach_overview"]["ACH1"]["Fan 1 off"]) / 5)}{data["ach_overview"]["ACH1"]["Fan 1 speed"]}'
                             f' Fan 2: {"|" * int(int(data["ach_overview"]["ACH1"]["Fan 2 on"]) / 5)}'
                             f'{".." * int(int(data["ach_overview"]["ACH1"]["Fan 2 off"]) / 5)}{data["ach_overview"]["ACH1"]["Fan 2 speed"]}')
                ACH_1_Compressors = f'{data["ach_overview"]["ACH1"]["Compressor"]}'

                ACH2_Fans = (f'Fan 1: {"|" * int(int(data["ach_overview"]["ACH2"]["Fan 1 on"]) / 5)}'
                             f'{".." * int(int(data["ach_overview"]["ACH2"]["Fan 1 off"]) / 5)}{data["ach_overview"]["ACH2"]["Fan 1 speed"]}'
                             f' Fan 2: {"|" * int(int(data["ach_overview"]["ACH2"]["Fan 2 on"]) / 5)}'
                             f'{".." * int(int(data["ach_overview"]["ACH2"]["Fan 2 off"]) / 5)}{data["ach_overview"]["ACH2"]["Fan 2 speed"]}')
                ACH_2_Compressors = f'{data["ach_overview"]["ACH2"]["Compressor"]}'

                ACH3_Fans = (f'Fan 1: {"|" * int(int(data["ach_overview"]["ACH3"]["Fan 1 on"]) / 5)}'
                             f'{".." * int(int(data["ach_overview"]["ACH3"]["Fan 1 off"]) / 5)}{data["ach_overview"]["ACH3"]["Fan 1 speed"]}'
                             f' Fan 2: {"|" * int(int(data["ach_overview"]["ACH3"]["Fan 2 on"]) / 5)}'
                             f'{".." * int(int(data["ach_overview"]["ACH3"]["Fan 2 off"]) / 5)}{data["ach_overview"]["ACH3"]["Fan 2 speed"]}')
                ACH_3_Compressors = f'{data["ach_overview"]["ACH3"]["Compressor"]}'

                ACH4_Fans = (f'Fan 1: {"|" * int(int(data["ach_overview"]["ACH4"]["Fan 1 on"]) / 5)}'
                             f'{".." * int(int(data["ach_overview"]["ACH4"]["Fan 1 off"]) / 5)}{data["ach_overview"]["ACH4"]["Fan 1 speed"]}'
                             f' Fan 2: {"|" * int(int(data["ach_overview"]["ACH4"]["Fan 2 on"]) / 5)}'
                             f'{".." * int(int(data["ach_overview"]["ACH4"]["Fan 2 off"]) / 5)}{data["ach_overview"]["ACH4"]["Fan 2 speed"]}')
                ACH_4_Compressors = f'{data["ach_overview"]["ACH4"]["Compressor"]}'

            if k == "power_monitoring":
                info += (
                            f"**PM:** Low: **{data['power_monitoring']['low_priority']}**  "
                            f"Med: **{data['power_monitoring']['mid_priority']}**  "
                            f"High: **{data['power_monitoring']['high_priority']}**   "
                            f"|**Ares**: {int(float(data['Ares']) / 1000)}kW"
                        ) + "\n"

            if k[0:3] == "CDU":
                info += (
                            f"**{k}**: T1: {float(v['t1'])}C  "
                            f"T2: {float(v['t2'])}C  "
                            f"T3: {float(v['t3'])}C  "
                            f"Pump: {str(int(v['pumpspeed']))}%"
                        ) + "\n"

            try:
                if k[0:3] == "ACH":
                    info += (
                            f"**{str(k)}** {MmStr.which_dot(str(v[k])).ljust(6, ' ')}"
                            f"  Inlet: **{str(v['Inlet Temp'])}**C "
                            f"Outlet: **{str(v['Outlet Temp'])}**C "

                            + (f"Pump" if str(v["Pumps"]) == "1" else "") + "\n"
                            + (f", **Free**" if str(v["Freecooling"]) == "1" else "") + "\n"

                            + ((ACH1_Fans + "\n" + ACH_1_Compressors + "\n") if k == "ACH1" else "")
                            + ((ACH2_Fans + "\n" + ACH_2_Compressors + "\n") if k == "ACH2" else "")
                            + ((ACH3_Fans + "\n" + ACH_3_Compressors + "\n") if k == "ACH3" else "")
                            + ((ACH4_Fans + "\n" + ACH_4_Compressors + "\n") if k == "ACH4" else "")
                    )



            except Exception:
                # when there is a lack of communication with the device
                info += f"**{str(k)}** :white_circle: Offline" + "\n"

            try:
                if k[0:3] == "PCW":

                    # if/else is for PCW1/PCW2, when one is ON the other is OFF
                    if str(v[k]) == "on":

                        info += (
                                        (f"**Po UPS-1**" if str(k) == "PCW UPS-1" else "")
                                        + (f"**Po UPS.1**" if str(k) == "PCW UPS+1" else "")
                                        + ("**" + str(k) + "**" if (str(k) != "PCW UPS-1" and str(k) != "PCW UPS+1") else "")
                                        + "  "
                                        + f"Supply: **{str(v['Supply Air'])}**C "
                                        + f"Return: **{str(v['Return Air'])}**C "
                                        + f"RH: {str(int(v['RH']))}"
                                        + f" Fans: {str(int(v['Fan Speed']))}"
                                        + f" Cool: {str(int(v['Cooling']))}") + "\n"

                    else:
                        continue
            except Exception:
                info += f"**{str(k)}** Offline"

            info += "\n"

        t = time.asctime().split()

        info = (("Listening: " + data["Listening"]).ljust(40, " ") + "\n"
                + f"### {t[0]} {t[3]} {t[2]} {t[1]} {t[4]}" + info)

        return info
