import itertools

import json_service
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error
from statsmodels.tsa.arima.model import ARIMA


class ArimaModel:
	def __init__(self, data_set, data_params, steps):
		self.data_set = data_set[:len(data_set)-15]
		order_param = self.check_params(data_params)
		self.model = ARIMA(self.data_set, order=order_param)
		self.model_fit = self.model.fit()
		self.preds = self.get_preds(steps, data_params[2])

	def check_params(self, data_params):
		model_params = json_service.check_set_arima(data_params[0], data_params[1], data_params[2])
		if not model_params or model_params == []:
			order_param = self.search_optimal_sarima(self.data_set.values)
			json_service.set_values_arima(data_params[0], data_params[1], data_params[2], order_param)
			return order_param
		else:
			return model_params
	def search_optimal_sarima(self, time_series):
		order_vals = diff_vals = ma_vals = range(0, 6)
		pdq_combinations = list(itertools.product(order_vals, diff_vals, ma_vals))

		smallest_aic = float("inf")
		optimal_order_param = None
		i = 1
		for order_param in pdq_combinations:
			print(f"{i}/{len(pdq_combinations)}")
			j = 1
			try:
				arima_model = ARIMA(time_series, order=order_param, trend="ct")
				model_results = arima_model.fit()
				if model_results.aic < smallest_aic and model_results.aic > 80.0:
					smallest_aic = model_results.aic
					optimal_order_param = order_param
			except:
				continue
			i += 1
		return optimal_order_param

	def get_preds(self, steps, interval):
		pred_future = self.model_fit.get_forecast(steps=steps)
		preds = pd.DataFrame()
		predicted = pred_future.predicted_mean

		mse = mean_squared_error(self.data_set.values[-steps:], predicted)
		mae = mean_absolute_error(self.data_set.values[-steps:], predicted)
		print(f"MSE: {mse}")
		print(f"MAE: {mae}")

		# values = [self.data_set.values[-2], self.data_set.values[-1]]
		values = [self.data_set.values[-1]]
		values.extend(predicted.values)
		preds['Close'] = values
		time_type = ''
		if ("mo" in interval): time_type = 'M'
		elif ("d" in interval): time_type = 'D'
		elif ("wk" in interval): time_type = 'W'
		pred_dates = np.datetime64(self.data_set.reset_index()['Date'].values[-1], time_type)
		pred_dates = pred_dates + np.arange(steps+1)
		preds["Date"] = pred_dates
		preds.set_index('Date', inplace=True)
		for i in range(len(preds["Close"].values)):
			preds["Close"].values[i] = int(preds["Close"].values[i])
		return preds