import time


class MM_Str:

    def __init__(self):
        pass

    @staticmethod
    def which_dot(s: str) -> str:

        stats = {
                 'Standby': ':large_yellow_circle:',
                 'Warning On': ':large_green_circle:',
                 'Local ON': ':large_green_circle:',
                 'Local OFF': ':red_circle:',
                 'Alarm ON': ':red_circle:',
                 'Power Failure': ':red_circle:'
                 }

        return stats.get(s, 'Stan:' + s)

    def make_mm_str(self, data: dict,  watcher_extra: bool, watcher_alarm: bool) -> str:

        info = ''

        for k, v in data.items():

            if k == 'power_monitoring':
                info += (
                    f"**PM:** Low: **{data['power_monitoring']['low_priority']}**  "
                    f"Med: **{data['power_monitoring']['mid_priority']}**  "
                    f"High: **{data['power_monitoring']['high_priority']}**   "
                    f"|**Ares**: {int(float(data['Ares']) / 1000)}kW"
                ) + '\n'

            if k[0:3] == 'CDU':
                info += (
                            f"**{k}**: T1: {float(v['t1'])}C  "
                            f"T2: {float(v['t2'])}C  "
                            f"T3: {float(v['t3'])}C  "
                            f"Pump: {str(int(v['pumpspeed']))}%"
                        ) + '\n'

            try:
                if k[0:3] == 'ACH':
                    info += (
                            f"**{str(k)}** {MM_Str.which_dot(str(v[k])).ljust(6, ' ')}"
                            f"  Inlet: **{str(v['Inlet Temp'])}**C "
                            f"Outlet: **{str(v['Outlet Temp'])}**C "

                            + (f"Pump" if str(v['Pumps']) == '1' else '')
                            + (f", **Fans**" if str(v['Fans']) == '1' else '')
                            + (f", **Compr**" if str(v['Compressors']) == '1' else '')
                            + (f", **Free**" if str(v['Freecooling']) == '1' else '') + '\n')

            except Exception:
                #when there is a lack of communication with the device
                info += f"**{str(k)}** :white_circle: Offline" + '\n'

            try:
                if k[0:3] == 'PCW':

                    # if/esle is for PCW1/PCW2, when one is ON the other is OFF
                    if str(v[k]) == "on":

                        info += (
                                        (f"**Po UPS-1**" if str(k) == 'PCW UPS-1' else '')
                                        + (f"**Po UPS.1**" if str(k) == 'PCW UPS+1' else '')
                                        + ('**' + str(k) + '**' if (str(k) != 'PCW UPS-1' and str(k) != 'PCW UPS+1') else '')
                                        + '  '
                                        + f"Supply: **{str(v['Supply Air'])}**C "
                                        + f"Return: **{str(v['Return Air'])}**C "
                                        + f"RH: {str(int(v['RH']))}"
                                        + f" Fans: {str(int(v['Fan Speed']))}"
                                        + f" Cool: {str(int(v['Cooling']))}") + '\n'

                    else:
                        continue
            except Exception:
                info += f"**{str(k)}**  :white_circle: **Brak komunikacji.**"

            info += '\n'

        t = time.asctime().split()

        # (first line below) if extra options for WATCHER are ON and there is Alert the '!' in Listening will be a flag for esp32 to produce sound
        info = (( ('Listening! 'if (watcher_extra and watcher_alarm) else 'Listening: ')
                 + data['Listening']).ljust(40, ' ') + '\n'
                 + f"### {t[0]} {t[3]} {t[2]} {t[1]} {t[4]}" + info)

        return info
