from datetime import date, timedelta, datetime

def data_params_to_string_sarima(period, interval, seasonal_length):
	return f"p{period}_i{interval}_s{seasonal_length}"

def data_params_to_string_lstm(period, interval):
	return f"p{period}_i{interval}"

def get_params(params):
	try:
		if (len(params) == 2):
			arima_params = params[0]
			sarima_params = params[1]
			return arima_params, sarima_params
	except:
		return []


def check_set_params(data, period, interval, seasonal_length):
	data_params = data_params_to_string_sarima(period, interval, seasonal_length)
	keys = data['data'].keys()
	if (data_params in keys):
		params_date = datetime.strptime(data['data'][data_params]['date'], "%Y-%m-%d").date()
		week = timedelta(7)
		if date.today() >= (params_date+week):
			return False
		return get_params(data['data'][data_params]['params'])
	return False
