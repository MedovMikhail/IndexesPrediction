import itertools
import warnings
import json_service
import pandas as pd
import numpy as np
import statsmodels.api as sm
from sklearn.metrics import mean_squared_error, mean_absolute_error
from statsmodels.tsa.statespace.sarimax import SARIMAX
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

class SarimaxModel:
	def __init__(self, data_set, data_params, seasonal_cycle_length, steps, offset=0):
		self.data_set = data_set[:len(data_set)-offset]
		order_param, seasonal_param = self.check_params(data_params, seasonal_cycle_length)
		self.model = SARIMAX(self.data_set, order=order_param, seasonal_order=seasonal_param)
		self.model_fit = self.model.fit()
		self.mse = 0
		self.mae = 0
		self.preds = self.get_preds(steps, data_params[2])

	def check_params(self, data_params, seasonal_cycle_length):
		model_params = json_service.check_set_sarima(data_params[0], data_params[1], data_params[2], seasonal_cycle_length)
		if not model_params or model_params == []:
			order_param, seasonal_param = self.search_optimal_sarima(self.data_set.values, seasonal_cycle_length)
			json_service.set_values_sarima(data_params[0], data_params[1], data_params[2], seasonal_cycle_length, order_param, seasonal_param)
			return order_param, seasonal_param
		else:
			return model_params
	def search_optimal_sarima(self, time_series, seasonal_cycle):
		order_vals = diff_vals = ma_vals = range(0, 2)
		pdq_combinations = list(itertools.product(order_vals, diff_vals, ma_vals))
		seasonal_combinations = [(combo[0], combo[1], combo[2], seasonal_cycle) for combo in pdq_combinations]

		smallest_aic = float("inf")
		optimal_order_param = optimal_seasonal_param = None
		i = 1
		for order_param in pdq_combinations:
			print(f"{i}/{len(pdq_combinations)}")
			j = 1
			for seasonal_param in seasonal_combinations:
				try:
					sarima_model = SARIMAX(time_series,
													order=order_param,
													seasonal_order=seasonal_param)

					model_results = sarima_model.fit()
					if model_results.aic < smallest_aic and model_results.aic > 50.0:
						smallest_aic = model_results.aic
						optimal_order_param = order_param
						optimal_seasonal_param = seasonal_param
				except:
					continue
				print(f"{i}: {j}/{len(seasonal_combinations)}")
				j += 1
			i += 1
		return optimal_order_param, optimal_seasonal_param

	def get_preds(self, steps, interval):
		pred_future = self.model_fit.get_forecast(steps=steps)
		preds = pd.DataFrame()
		predicted = pred_future.predicted_mean

		self.mse = mean_squared_error(self.data_set.values[-steps:], predicted)
		self.mae = mean_absolute_error(self.data_set.values[-steps:], predicted)

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