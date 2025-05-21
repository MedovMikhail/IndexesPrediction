import json
from datetime import date, datetime
from pathlib import Path

from secpickle import pickle

from json_service import check_set_params, data_params_to_string_sarima, data_params_to_string_lstm

source_dir = "./local_db/"

def default(o):
    if isinstance(o, (date, datetime)):
        return o.isoformat()


class SarimaFiles:
    def __init__(self, index_name):
        self.dir = Path(source_dir+'sarima/')
        self.name = index_name

    def check_index(self):
        file = self.dir / (self.name+'.json')
        return file.exists()

    def check_params(self, period, interval, seasonal_length):
        return check_set_params(self.get_data(), period, interval, seasonal_length)

    def create_file(self):
        file = self.dir / (self.name+'.json')
        file.open("w+")
        data = {
            "data": {}
        }
        file.write_text(json.dumps(data), encoding='UTF-8')

    def get_data(self):
        if self.check_index():
            file = self.dir / (self.name + '.json')
            file.open("r")
            return json.loads(file.read_text(encoding='UTF-8'))
        else:
            self.create_file()
            return self.get_data()

    def write_in_file(self, period, interval, seasonal, arima_params, sarima_params):
        data = self.get_data()
        data_params = data_params_to_string_sarima(period, interval, seasonal)
        file = self.dir / (self.name + '.json')
        file.open("w+")
        try:
            data['data'].update({
                data_params: {
                    "params": [arima_params, sarima_params],
                    "date": default(date.today())
                }
            })
        except:
            data['data'].update({
                data_params: {
                    "params": [arima_params, sarima_params],
                    "date": default(date.today())
                }
            })
        finally:
            file.write_text(json.dumps(data), encoding='utf-8')


class LSTMFiles:
    def __init__(self, index_name):
        self.dir = Path(source_dir + 'lstm/')
        self.name = index_name

    def check_index(self):
        file = self.dir / self.name
        return file.exists() and file.is_dir()

    def check_file(self, interval, period):
        return self.get_data(interval, period) is not None

    def get_data(self, interval, period):
        if not self.check_index(): return None
        string_data_params = data_params_to_string_lstm(interval, period)
        dir = self.dir / self.name
        match_patterns = list(dir.glob(f"{string_data_params}*.pkl"))
        if len(match_patterns) == 0: return None
        true_file = None
        for match in match_patterns:
            string_date = match.name.split('=')[-1].split('.')[0]
            file_date = datetime.strptime(string_date, "%Y-%m-%d").date()
            if date.today() != file_date: match.unlink()
            else: true_file = match
        if true_file is None: return None
        return pickle.load(open(true_file, 'rb'))

    def create_dir(self):
        if self.check_index(): return False
        dir = self.dir / self.name
        try:
            dir.mkdir()
            return True
        except:
            return False

    def create_file(self, model, interval, period):
        string_data_params = data_params_to_string_lstm(interval, period)
        if self.check_index():
            file = self.dir / self.name / f"{string_data_params}={date.today()}.pkl"
            pickle.dump(model, open(file.absolute(), 'wb'), protocol=pickle.HIGHEST_PROTOCOL)
        else:
            self.create_dir()
            self.create_file(model, interval, period)

# lf = LSTMFiles("^GSPC")
# lf.create_file(None, "5y", "1d")
# print(lf.get_data("5y", "1d"))