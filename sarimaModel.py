import itertools

import numpy as np
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.stattools import adfuller
from errors_metrics import *
from files_service import SarimaFiles


class SarimaxModel:
	def __init__(self, data_set, data_params, seasonal_cycle_length, is_automatic, steps, offset=0):
		self.full_data_set = data_set
		self.data_set = data_set[:-offset]
		self.offset = offset
		self.is_automatic = is_automatic
		self.data_params = data_params
		self.seasonal_cycle_length = seasonal_cycle_length
		self.steps = steps
		self.model = None
		self.preds = None

		self.arima_params = []
		self.sarima_params = []

		self.sarima_files = SarimaFiles(data_params[0])

	def check_params(self):
		model_params = self.sarima_files.check_params(self.data_params[1], self.data_params[2],
													 self.seasonal_cycle_length)
		if not model_params or model_params == []:
			order_param, seasonal_param = self.search_optimal_sarima(self.full_data_set.values)
			self.sarima_files.write_in_file(self.data_params[1], self.data_params[2], self.seasonal_cycle_length,
										   order_param, seasonal_param)
			return [order_param, seasonal_param]

		else:
			return model_params

	def training(self, params=None):
		if self.is_automatic:
			[order_param, seasonal_param] = self.check_params()
			self.arima_params = order_param
			self.sarima_params = seasonal_param
		else:
			[order_param, seasonal_param] = self.teach_sarima(params)
			self.arima_params = order_param
			self.sarima_params = seasonal_param

	def teach_sarima(self, params, seasonal_param=None):
		if not self.is_automatic or seasonal_param is None:
			order_vals = diff_vals = ma_vals = range(0, 2)
			pdq_combinations = list(itertools.product(order_vals, diff_vals, ma_vals))
			seasonal_combinations = [(combo[0], combo[1], combo[2], self.seasonal_cycle_length) for combo in
									 pdq_combinations]
			seasonal_param = self.find_seasonal_params(self.full_data_set, params, seasonal_combinations)[1]

		return [params, seasonal_param]

	def search_optimal_sarima(self, time_series):
		order_vals = diff_vals = ma_vals = range(0, 2)
		pdq_combinations = list(itertools.product(order_vals, diff_vals, ma_vals))
		seasonal_combinations = [(combo[0], combo[1], combo[2], self.seasonal_cycle_length) for combo in
									 pdq_combinations]
		print(seasonal_combinations)
		smallest_aic = float("inf")
		optimal_order_param = optimal_seasonal_param = None
		i = 1
		for order_param in pdq_combinations:
			print(f"{i}/{len(pdq_combinations)}")
			[aic, seasonal_params] = self.find_seasonal_params(time_series, order_param, seasonal_combinations)
			if aic < smallest_aic:
				smallest_aic = aic
				optimal_seasonal_param = seasonal_params
				optimal_order_param = order_param
			i += 1
		return optimal_order_param, optimal_seasonal_param

	def find_seasonal_params(self, time_series, params, seasonal_combinations):
		optimal_seasonal_param = [0, 0, 0, self.seasonal_cycle_length]
		smallest_aic = float("inf")
		i = 1
		for seasonal_param in seasonal_combinations:
			print(f"\t{i}/{len(seasonal_combinations)}")
			try:
				sarima_model = SARIMAX(time_series,
									   order=params,
									   seasonal_order=seasonal_param)

				model_results = sarima_model.fit()
				if smallest_aic > model_results.aic > 50.0:
					smallest_aic = model_results.aic
					optimal_seasonal_param = seasonal_param
			except:
				continue
			i+=1
		return [smallest_aic, optimal_seasonal_param]

	def search_d(self):
		data = self.full_data_set
		result = adfuller(data)
		p_value = result[1]
		data.plot(figsize=(12, 6))
		d = 0
		while p_value > 0.05 and d < 4:
			data = data.diff(periods=1).dropna()
			result = adfuller(data, maxlag=self.seasonal_cycle_length)
			p_value = result[1]
			d += 1
		return d, data

	def search_D(self, data):
		result = adfuller(data)
		p_value = result[1]
		data.plot(figsize=(12, 6))
		d = 0
		while p_value > 0.05 and d < 4:
			data = data.diff(periods=1).dropna()
			result = adfuller(data, maxlag=self.seasonal_cycle_length)
			p_value = result[1]
			d += 1
		return d

	def get_predict_for_training(self):
		self.model = SARIMAX(self.full_data_set, order=self.arima_params, seasonal_order=self.sarima_params)
		self.model = self.model.fit()
		pred_future = self.model.get_prediction(start=1, end=len(self.full_data_set.values))
		predicted = pred_future.predicted_mean
		preds = pd.DataFrame()

		preds['Close'] = predicted.values
		preds["Date"] = self.full_data_set.reset_index()['Date'].values
		preds.set_index('Date', inplace=True)
		return preds

	def get_forecast_for_training(self):
		model = SARIMAX(self.data_set, order=self.arima_params, seasonal_order=self.sarima_params)
		model = model.fit()
		pred_future = model.get_forecast(steps=self.steps)
		preds = pd.DataFrame()
		predicted = pred_future.predicted_mean

		values = [self.data_set.values[-1][0]]
		values.extend(predicted.values)
		preds['Close'] = values
		pred_dates = self.full_data_set.reset_index()['Date'].values[-self.offset-1:-(self.offset-self.steps)]
		preds["Date"] = pred_dates
		preds.set_index('Date', inplace=True)
		return preds

	def get_forecast_for_predict(self):
		pred_future = self.model.get_forecast(steps=self.steps)
		preds = pd.DataFrame()
		predicted = pred_future.predicted_mean

		values = [self.data_set.values[-1][0]]
		values.extend(predicted.values)
		preds['Close'] = values
		pred_dates = [self.full_data_set.reset_index()['Date'].values[-1]]
		for val in predicted.reset_index()['index'].values:
			pred_dates.append(val)
		preds["Date"] = pred_dates
		preds.set_index('Date', inplace=True)
		return preds
