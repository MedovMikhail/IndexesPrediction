import itertools

import json_service
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error
from statsmodels.tsa.statespace.sarimax import SARIMAX


class SarimaxModel:
	def __init__(self, data_set, data_params, seasonal_cycle_length, is_automatic, steps, offset=0):
		self.full_data_set = data_set
		self.data_set = data_set[:len(data_set) - offset]
		self.offset = offset
		self.is_automatic = is_automatic
		self.data_params = data_params
		self.seasonal_cycle_length = seasonal_cycle_length
		self.steps = steps
		self.model = None
		self.model_fit = None
		self.mse = 0
		self.mae = 0
		self.preds = None

	def check_params(self):
		model_params = json_service.check_set_sarima(self.data_params[0], self.data_params[1], self.data_params[2],
													 self.seasonal_cycle_length)
		if not model_params or model_params == []:
			order_param, seasonal_param = self.search_optimal_sarima(self.data_set.values)
			json_service.set_values_sarima(self.data_params[0], self.data_params[1], self.data_params[2], self.seasonal_cycle_length,
										   order_param, seasonal_param)
			return [order_param, seasonal_param]

		else:
			return model_params

	def training(self, params=None):
		if self.is_automatic:
			[order_param, seasonal_param] = self.check_params()
			self.model = self.teach_sarima(order_param, seasonal_param)
		else:
			self.model = self.teach_sarima(params)
		self.model_fit = self.model.fit()
		self.preds = self.get_preds()

	def teach_sarima(self, params, seasonal_param=None):
		if not self.is_automatic or seasonal_param is None:
			order_vals = diff_vals = ma_vals = range(0, 2)
			pdq_combinations = list(itertools.product(order_vals, diff_vals, ma_vals))
			seasonal_combinations = [(combo[0], combo[1], combo[2], self.seasonal_cycle_length) for combo in
									 pdq_combinations]
			seasonal_param = self.find_seasonal_params(self.data_set, params, seasonal_combinations)[1]
		print(params)
		print(seasonal_param)
		return SARIMAX(self.data_set, order=params, seasonal_order=seasonal_param)

	def search_optimal_sarima(self, time_series):
		order_vals = diff_vals = ma_vals = range(0, 2)
		pdq_combinations = list(itertools.product(order_vals, diff_vals, ma_vals))
		seasonal_combinations = [(combo[0], combo[1], combo[2], self.seasonal_cycle_length) for combo in
								 pdq_combinations]

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

	def get_preds(self):
		interval = self.data_params[2]
		pred_future = self.model_fit.get_forecast(steps=self.steps)
		preds = pd.DataFrame()
		predicted = pred_future.predicted_mean

		self.mse = mean_squared_error(self.full_data_set.values[-self.offset:-(self.offset-self.steps)], predicted)
		self.mae = mean_absolute_error(self.full_data_set.values[-self.offset:-(self.offset-self.steps)], predicted)

		# values = [self.data_set.values[-2], self.data_set.values[-1]]
		values = [self.data_set.values[-1]]
		values.extend(predicted.values)
		preds['Close'] = values
		time_type = ''
		if "mo" in interval:
			time_type = 'M'
		elif "d" in interval:
			time_type = 'D'
		elif "wk" in interval:
			time_type = 'W'
		pred_dates = np.datetime64(self.data_set.reset_index()['Date'].values[-1], time_type)
		pred_dates = pred_dates + np.arange(self.steps + 1)
		preds["Date"] = pred_dates
		preds.set_index('Date', inplace=True)
		for i in range(len(preds["Close"].values)):
			preds["Close"].values[i] = int(preds["Close"].values[i])
		return preds