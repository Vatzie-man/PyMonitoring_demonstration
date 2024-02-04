import time


class MM_Str:

    def __init__(self):
        self

    @staticmethod
    def which_dot(s):

        stats = {'Standby': ':large_yellow_circle:',
                 'Warning On': ':warning_green_circle_w:',
                 'Local ON': ':large_green_circle:',
                 'Local OFF': ':red_circle:',
                 'Alarm ON': ':a:',
                 'Power Failure': ':red_circle:'
                 }

        return stats.get(s, 'Stan:' + s)

    def make_mm_str(self, data):
        info = ''

        for k, v in data.items():
            if k[0:3] == 'Are':
                info += '**' + str(k) + '**' + ': ' + str(int(float(v) / 1000)) + 'kW' + '\n'

            if k[0:3] == 'CDU':
                info += ('**' + str(k) + '**' + ':    '
                         + 'T1: ' + str(float(v['t1'])) + 'C   '
                         + 'T2: ' + str(float(v['t2'])) + 'C   '
                         + 'T4: ' + str(float(v['t4'])) + 'C   '
                         + 'Pump: ' + str(int(v['pumpspeed'])) + '%' + '\n')

            # 'try' helps when there is a Power Failure on ACH device
            try:
                if k[0:3] == 'ACH':
                    info += ('**' + str(k) + '**' + ' ' + MM_Str.which_dot(str(v[k])).ljust(6, ' ')
                             + '  Inlet: ' + '**' + str(v['Inlet Temp']) + '**' + 'C  '
                             + 'Outlet: ' + '**' + str(v['Outlet Temp']) + '**' + 'C  '

                             + ('Pump' if str(v['Pumps']) == '1' else '')
                             + (', **Fans**' if str(v['Fans']) == '1' else '')
                             + (', **Compr**' if str(v['Compressors']) == '1' else '')
                             + (', **Free**' if str(v['Freecooling']) == '1' else '') + '\n')

            except Exception:
                info += '**' + str(k) + '**' + ':    ' + ':white_circle: **Brak komunikacji.**'

            try:
                if k[0:3] == 'PCW' and len(v) == 6:

                    # that is for PCW1/PCW2, where only one is ON and i need the data from that which is ON
                    if str(v[k]) == "on":

                        info += (('**Po UPS-1**' if str(k) == 'PCW UPS-1' else '')
                                 + ('**Po UPS.1**' if str(k) == 'PCW UPS+1' else '')
                                 + ('**' + str(k) + '**' if (str(k) != 'PCW UPS-1' and str(k) != 'PCW UPS+1') else '')

                                 + '  '
                                 + 'Supply: ' + '**' + str(v['Supply Air']) + '**' + 'C  '
                                 + 'Return: ' + '**' + str(v['Return Air']) + '**' + 'C  '

                                 + 'RH: ' + str(int(v['RH']))
                                 + ' Fans: ' + str(int(v['Fan Speed']))
                                 + ' Cool: ' + str(int(v['Cooling'])) + '\n')

                    # that is for PCW1/PCW2 H1 if one works and the other is off
                    else:
                        continue
            except Exception:
                pass

            try:
                if k[0:3] == 'PCW' and len(v) == 3:
                    info += "**" + str(k) + '**' + ' :  ' + 'Offline' + '\n'
            except Exception:
                pass

            info += '\n'

        t = time.asctime().split()

        info = ('Listening: ' + data['Listening']).ljust(40, ' ') + '\n' + '### ' + (
                t[0] + ' ' + t[3] + ' ' + t[2] + ' ' + t[1] + ' ' + t[4]) + '\n' + info

        return info, t[3]
