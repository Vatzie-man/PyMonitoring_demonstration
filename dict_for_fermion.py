import time


class Dict_For_Fermion:

    def __init__(self):
        self.out = {
            'time': None,
            'CDU_t1': None,
            'CDU_t4': None,
            'ACH2': None,
            'ACH4': None,
            'ACH3': None,
            'ACH1': None,
            'ACH2_Return': None,
            'ACH4_Return': None,
            'ACH3_Return': None,
            'ACH1_Return': None,
            'H1': None,
            'H0': None,
            'UPS+1': None,
            'UPS-1': None}

    def dict_for_fermion(self, data_dict):

        # try in case something went wrong, so other progrmas will not crash
        try:

            for i in ['ACH2', 'ACH4', 'ACH3', 'ACH1']:

                if data_dict[i][i] == 'Local ON' or data_dict[i][i] == 'Warning On':
                    self.out[i] = 'on'
                    self.out[i + '_Return'] = data_dict[i]['Outlet Temp']

                if data_dict[i][i] == 'Standby':
                    self.out[i] = 'st'
                    self.out[i + '_Return'] = data_dict[i]['Outlet Temp']

                if data_dict[i][i] == 'Local OFF' or data_dict[i][i] == 'Power Failure' or data_dict[i] == 'Alarm ON':
                    self.out[i] = 'er'
                    self.out[i + '_Return'] = data_dict[i]['Outlet Temp']

                if data_dict[i][i] == 'Offline':
                    self.out[i] = 'na'
                    self.out[i + '_Return'] = 0.0

            # PCWs - PCW1/PCW2 on H1 is changing
            for x in ['PCW1 H0', 'PCW1 H1', 'PCW2 H1', 'PCW UPS+1', 'PCW UPS-1']:

                if x == 'PCW1 H0': i = 'H0'
                if x == 'PCW1 H1': i = 'H1'
                if x == 'PCW2 H1': i = 'H1'
                if x == 'PCW UPS+1': i = 'UPS+1'
                if x == 'PCW UPS-1': i = 'UPS-1'

                if data_dict[x][x] == 'Offline':
                    self.out[i] = 'BRAK'

                if data_dict[x][x] == 'on':
                    self.out[i] = str(data_dict[x]['Return Air'])

                if data_dict[x][x] == 'of':
                    pass

            # CDUs
            if 'CDU1' and 'CDU2' and 'CDU3' in data_dict.keys():
                cdu_1_temp = 0
                cdu_4_temp = 0

                for i in ['CDU1', 'CDU2', 'CDU3']:
                    cdu_1_temp += float(data_dict[i]['t1'])
                    cdu_4_temp += float(data_dict[i]['t4'])

                self.out['CDU_t1'] = str(cdu_1_temp / 3)[0:4]
                self.out['CDU_t4'] = str(cdu_4_temp / 3)[0:4]

            # time
            self.out['time'] = ' '.join(time.asctime().split()[3:4])[0:-3]
        except Exception:
            self.out = False

        return self.out
