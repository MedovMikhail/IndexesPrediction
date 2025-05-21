import yfinance as yf
import pandas as pd


def find_not_none(values, values_len, i):
    while i < values_len:
        try:
            int(values[i][0])
            return values[i][0]
        except:
            i += 1
    return None


def get_interval(interval):
    if interval == '1d':
        return 'd'
    if interval == '1wk':
        return 'W'
    if interval == '1mo':
        return 'M'

class Indexes:
    def __init__(self, name, period, interval):
        self.data = pd.DataFrame(yf.download(name, period=period, interval='1d'))
        self.data = self.data.asfreq('d')
        self.data['Close'] = self.set_not_none(self.data['Close'])
        self.data = self.data.asfreq(get_interval(interval))
        self.dates = self.data.reset_index()['Date'].values
        self.data_set = self.data['Close']
        self.set_not_none(self.data_set)

    def set_not_none(self, data_set):
        i = 0
        data_len = len(data_set.values)
        for el in data_set.isnull().values:
            if el[0]:
                if i == 0:
                    value = find_not_none(data_set.values, data_len, i)
                    if value is None:
                        break
                    data_set.values[i][0] = value
                elif i == data_len - 1:
                    data_set.values[i][0] = data_set.values[i - 1][0]
                else:
                    value = find_not_none(data_set.values, data_len, i)
                    if value is None:
                        data_set.values[i][0] = data_set.values[i][0]
                    else:
                        data_set.values[i][0] = int(abs(value + data_set.values[i - 1][0]) / 2)
            i += 1
        return data_set
