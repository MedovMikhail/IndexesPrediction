import math
def get_mse(origin_data, pred_data):
	len_origin = len(origin_data)
	if len_origin == len(pred_data):
		mse_values = []
		error = 0
		for i in range(len_origin):
			diff_sum = 0
			for j in range(i+1):
				diff_sum += math.pow(origin_data[j] - pred_data[j], 2)
			error = diff_sum/(i+1)
			mse_values.append(error)
		return [mse_values, error]
	else:
		return None


def get_mae(origin_data, pred_data):
	len_origin = len(origin_data)
	if len_origin == len(pred_data):
		mse_values = []
		error = 0
		for i in range(len_origin):
			diff_sum = 0
			for j in range(i+1):
				diff_sum += abs(origin_data[j] - pred_data[j])
			error = diff_sum/(i+1)
			mse_values.append(error)
		return [mse_values, error]
	else:
		return None


def get_mape(origin_data, pred_data):
	len_origin = len(origin_data)
	if len_origin == len(pred_data):
		mspe_values = []
		error = 0
		for i in range(len_origin):
			diff_sum = 0
			for j in range(i + 1):
				diff_sum += (abs(origin_data[j] - pred_data[j])) / abs(origin_data[j])
			error = diff_sum * 100 / (i + 1)
			mspe_values.append(error)
		return [mspe_values, error]
	else:
		return None