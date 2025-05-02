import json
from pathlib import Path

path = "./local_db/parametrs_set.json"
path = Path(path)

def get_data():
	global path
	return json.loads(path.read_text(encoding='utf-8'))

def data_params_to_string_sarima(period, interval, seasonal_length):
	return f"p{period}_i{interval}_s{seasonal_length}"

def data_params_to_string_arima(period, interval):
	return f"p{period}_i{interval}"

def get_params(params):
	try:
		if (len(params) == 1):
			arima_params = params[0]
			return arima_params
		if (len(params) == 2):
			arima_params = params[0]
			sarima_params = params[1]
			return arima_params, sarima_params
	except:
		return []

def set_values_sarima(index_name, period, interval, seasonal_length, arima_params, sarima_params):
	data_params = data_params_to_string_sarima(period, interval, seasonal_length)
	data = get_data()
	if (arima_params == None or sarima_params == None):
		return
	try:
		data['data'][index_name].update({
				data_params: [arima_params, sarima_params]
			})
	except:
		data['data'].update({
			index_name: {
				data_params: [arima_params, sarima_params]
			}
		})
	path.write_text(json.dumps(data), encoding='utf-8')

def set_values_arima(index_name, period, interval, arima_params):
	data_params = data_params_to_string_arima(period, interval, )
	data = get_data()
	if (arima_params == None):
		return
	try:
		data['data'][index_name].update({
				data_params: [arima_params]
			})
	except:
		data['data'].update({
			index_name: {
				data_params: [arima_params]
			}
		})
	path.write_text(json.dumps(data), encoding='utf-8')




def check_set_sarima(index_name, period, interval, seasonal_length):
	data_params = data_params_to_string_sarima(period, interval, seasonal_length)
	data = get_data()

	keys = data['data'].keys()
	if (index_name in keys):
		params_keys = data['data'][index_name].keys()
		if data_params in params_keys:
			return get_params(data['data'][index_name][data_params])
	return False

def check_set_arima(index_name, period, interval):
	data_params = data_params_to_string_arima(period, interval)
	data = get_data()

	keys = data['data'].keys()
	if (index_name in keys):
		params_keys = data['data'][index_name].keys()
		if data_params in params_keys:
			return get_params(data['data'][index_name][data_params])
	return False

