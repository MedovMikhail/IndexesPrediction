import pandas as pd


class DataProcessor:
	mean = 0
	data = []

	def __init__(self, data):
		self.data = data
		self.mean = (max(self.data.values) + min(self.data.values)) // 2
		self.scale = self.get_diff_scale()

	def get_diff_scale(self):
		max_diff = 0
		for i in range(len(self.data)):
			diff = abs(self.mean - self.data.values[i])
			if diff > max_diff:
				max_diff = diff
		return max_diff / 100

	def define_diff_rate(self, value):
		diff = abs(value - self.mean)
		if value > self.mean:
			rate = int(diff // self.scale) + 100
		else:
			rate = 100 - int(diff // self.scale)
		return rate

	def get_processed_data(self):
		values = []
		for el in self.data.values:
			values.append(self.define_diff_rate(el))
		data = pd.DataFrame()
		data['Close'] = values
		data["Date"] = self.data.reset_index()['Date'].values
		data.set_index('Date', inplace=True)
		return data

	def reverse_scaling(self, data):
		for i in range(len(data)):
			data[i] = self.mean + (data[i] - 100) * self.scale
		return data
