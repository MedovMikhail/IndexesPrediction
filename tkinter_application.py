import threading
import time
from tkinter_creator import TkinterCreator
from sarimaModel import SarimaxModel
from lstm import LSTMNetwork
from data_processor import DataProcessor
from indexes import Indexes
from static_info import *
from errors_metrics import *

WIDTH = 1500
HEIGHT = 750

def convert_seasonal_to_number(seasonal, interval):
	year = 365
	interval_scale = {
		"1d": 1,
		"1wk": 7,
		"1mo": 30,
		"3mo": 90
	}
	seasonal_scale = {
		"year": year,
		"half_year": int(year / 2),
		"quarter": int(year / 4),
		"mo": int(year / 12)
	}

	return int(seasonal_scale[seasonal] / interval_scale[interval])


class Application:
	def __init__(self):
		self.tc = TkinterCreator()
		self.root = self.tc.create_root("НИР_8 V1.0.0", WIDTH, HEIGHT)

		self.data_processor = None
		self.data_set = []
		self.processed_data = []
		self.data_params = []
		self.learning_button_sarima = None
		self.predict_button_sarima = None
		self.learning_button_lstm = None
		self.predict_button_lstm = None
		self.loading_label = None
		self.get_index_btn = None
		self.type_learning_frame = None

		self.index_string_var = self.tc.add_string_var(list(INDEX_NAMES.keys())[0])
		self.period_string_var = self.tc.add_string_var(list(PERIODS.keys())[0])
		self.interval_string_var = self.tc.add_string_var(list(INTERVALS.keys())[0])
		self.seasonal_string_var = self.tc.add_string_var(list(SEASONAL.keys())[0])
		self.type_learning_string_var = self.tc.add_string_var("auto")
		self.p_string_var = self.tc.add_string_var("0")
		self.q_string_var = self.tc.add_string_var("0")
		self.d_string_var = self.tc.add_string_var("0")

		self.sarima_model = None
		self.lstm_model = None

		self.selected_interval = ""

		self.upbar()

		self.canvas = self.tc.add_canvas(self.root)
		self.main_frame = self.tc.add_frame(self.canvas, 1, "sunken", [8,10])
		self.scrollbar = self.tc.add_scrollbar(self.root, "vertical", self.canvas.yview)

		self.tc.configure_canvas(self.canvas, self.scrollbar, self.main_frame, WIDTH)
		self.models_frame = None
		self.sarima_frame = self.tc.add_frame(self.main_frame)
		self.lstm_frame = self.tc.add_frame(self.main_frame)

	def upbar(self):
		header = self.tc.add_label("Прогнозирование биржевых индексов", self.root, 20)
		header.pack()
		inputs_frame = self.tc.add_frame(self.root)

		indexes_frame = self.tc.add_frame(inputs_frame)
		periods_frame = self.tc.add_frame(inputs_frame)
		intervals_frame = self.tc.add_frame(inputs_frame)

		input_frame_elements = [
			self.tc.add_label("Выберите биржевой индекс:", indexes_frame, 16),
			self.tc.add_combobox(list(INDEX_NAMES.keys()), indexes_frame, self.index_string_var),
			self.tc.add_label("Выберите период:", periods_frame, 16),
			self.tc.add_combobox(list(PERIODS.keys()), periods_frame, self.period_string_var),
			self.tc.add_label("Выберите интервал:", intervals_frame, 16),
			self.tc.add_combobox(list(INTERVALS.keys()), intervals_frame, self.interval_string_var)
		]

		inputs_frame.pack(fill="x", pady=20)

		self.tc.add_grid(3, 1, inputs_frame)

		indexes_frame.grid(column=0, row=0)
		periods_frame.grid(column=1, row=0)
		intervals_frame.grid(column=2, row=0)

		self.tc.pack_elements(input_frame_elements, "w")

		self.get_index_btn = self.tc.add_button(self.root, "Загрузить данные", 14, self.start_data)
		self.get_index_btn.pack(anchor="center", pady=10, ipadx=5, ipady=3)

	def starts_graphics(self):
		company_name = self.index_string_var.get()
		period_name = self.period_string_var.get()
		interval_name = self.interval_string_var.get()

		company_value = INDEX_NAMES.get(company_name)
		period_value = PERIODS.get(period_name)
		interval_value = INTERVALS.get(interval_name)
		self.selected_interval = interval_name

		if "Месяц" not in list(SEASONAL.keys()):
			SEASONAL.update(SEASONAL_MONTH)
		if interval_value == "3mo":
			SEASONAL.pop("Месяц")

		for widget in self.main_frame.winfo_children():
			widget.destroy()

		#Исходные данные
		self.data_params = [company_value, period_value, interval_value]
		indexes = Indexes(company_value, period_value, interval_value)
		self.tc.add_graphic("Исходные данные", company_name, indexes.data_set, self.main_frame)

		#Преобразованные данные
		self.data_set = indexes.data_set
		self.data_processor = DataProcessor(self.data_set)
		self.processed_data = self.data_processor.get_processed_data()
		# self.tc.add_graphic("Преобразованные данные", company_name, self.processed_data, self.main_frame)

		self.models_frame = self.tc.add_frame(self.main_frame)
		self.models_frame.pack(fill='both', expand=True)
		for c in range(2): self.models_frame.columnconfigure(index=c, weight=1)
		self.sarima_frame = self.tc.add_frame(self.models_frame)
		self.lstm_frame = self.tc.add_frame(self.models_frame)
		self.sarima_frame.grid(column=0, row=0)
		self.lstm_frame.grid(column=1, row=0)
		self.sarima_part()
		self.lstm_part()

		self.update_canvas()
		self.end_processing()

	def sarima_part(self):
		for widget in self.sarima_frame.winfo_children():
			widget.destroy()

		self.tc.add_label("Модель SARIMA", self.sarima_frame, 32).pack(pady=10)

		self.type_learning_frame = self.tc.add_frame(self.sarima_frame)
		type_learning_frame_static = self.tc.add_frame(self.type_learning_frame)

		# Сезонность
		self.tc.add_label("Выберите сезонность:", type_learning_frame_static, 18).pack(pady=10)
		self.tc.add_combobox(list(SEASONAL.keys()), type_learning_frame_static, self.seasonal_string_var).pack()

		# Выбор способа задания параметров
		self.tc.add_label("Выберите способ задания параметров:", type_learning_frame_static, 18).pack(pady=10)
		radio1 = self.tc.add_radiobutton(type_learning_frame_static, "Автоматически", "auto", self.type_learning_string_var)
		radio2 = self.tc.add_radiobutton(type_learning_frame_static, "Вручную", "manually", self.type_learning_string_var)

		radio1.configure(command=self.change_type_learning)
		radio2.configure(command=self.change_type_learning)
		radio1.pack(side="left")
		radio2.pack(side="right")

		type_learning_frame_static.pack()
		self.type_learning_frame.pack(pady=15, ipadx=20, ipady=10)

		self.learning_button_sarima = self.tc.add_button(self.sarima_frame, "Обучить модель", 14, self.start_learning_sarima)
		self.learning_button_sarima.pack()

	def lstm_part(self):
		for widget in self.lstm_frame.winfo_children():
			widget.destroy()

		self.tc.add_label("Сеть LSTM", self.lstm_frame, 32).pack(pady=10)

		self.tc.add_label("", self.lstm_frame, 32).pack(pady=80)

		self.learning_button_lstm = self.tc.add_button(self.lstm_frame, "Обучить модель", 14, command=self.start_learning_lstm)
		self.learning_button_lstm.pack()

	def learning_sarima(self):
		try:
			for widget in self.sarima_frame.nametowidget(".learning_metric_predict").winfo_children():
				widget.destroy()
			for widget in self.sarima_frame.nametowidget(".learning_metric_forecast").winfo_children():
				widget.destroy()
			for widget in self.sarima_frame.nametowidget(".learning_predicted_frame").winfo_children():
				widget.destroy()
			for widget in self.sarima_frame.nametowidget(".learning_forecast_frame").winfo_children():
				widget.destroy()
			for widget in self.sarima_frame.nametowidget(".errors_frame").winfo_children():
				widget.destroy()
			for widget in self.sarima_frame.nametowidget(".predict_forecast_frame").winfo_children():
				widget.destroy()
		except:
			pass

		is_automatic = self.type_learning_string_var.get() == "auto"

		seasonal_param = SEASONAL[self.seasonal_string_var.get()]
		interval_param = INTERVALS[self.selected_interval]
		seasonal_cycle = convert_seasonal_to_number(seasonal_param, interval_param)
		steps = 10
		offset = int(len(self.processed_data)*0.2)
		if offset < steps:
			steps = offset-1
		self.sarima_model = SarimaxModel(self.processed_data, self.data_params, seasonal_cycle, is_automatic, steps, offset)

		if not is_automatic:
			self.sarima_model.training(self.get_params())
		else: self.sarima_model.training()

		left_offset = 50
		right_offset = 50
		if len(self.processed_data[-offset:]) < right_offset:
			right_offset = len(self.processed_data[-offset:]) - 1
		if len(self.processed_data[:-offset]) < left_offset:
			left_offset = len(self.processed_data[:-offset]) - 1

		predict = self.sarima_model.get_predict_for_training()
		self.data_processor.reverse_scaling(predict.values)
		learning_graphic_frame = self.tc.add_frame(self.sarima_frame, name="learning_predicted_frame")
		self.tc.add_concat_graphic(
			"Проверка обученной модели",
			self.index_string_var.get(),
			self.data_set,
			predict,
			learning_graphic_frame,
			"Реальные данные",
			"Спрогнозированные данные",
			(7,4)
		)
		learning_graphic_frame.pack()

		metric_frame = self.tc.add_frame(self.sarima_frame, 1, "solid", name="learning_metric_predict")
		predict_to_metrics = predict.values
		data_set_to_metrics = self.data_set.values
		mse = get_mse(data_set_to_metrics, predict_to_metrics)
		mae = get_mae(data_set_to_metrics, predict_to_metrics)
		mape = get_mape(data_set_to_metrics, predict_to_metrics)
		metric_frame_elements = [
			self.tc.add_label("Метрики качества модели:", metric_frame, 18),
			self.tc.add_label(f"Среднеквадратичная ошибка: {mse[1]:.3f}", metric_frame, 16),
			self.tc.add_label(f"Средняя абсолютная ошибка: {mae[1][0]:.3f}", metric_frame, 16),
			self.tc.add_label(f"Средняя абсолютная ошибка в процентах: {mape[1][0]:.3f}", metric_frame, 16)
		]
		self.tc.pack_elements(metric_frame_elements, "w")
		metric_frame.pack()

		predict = self.sarima_model.get_forecast_for_training()
		self.data_processor.reverse_scaling(predict.values)
		predict.values[0] = self.data_set.values[-offset - 1]
		learning_graphic_frame = self.tc.add_frame(self.sarima_frame, name="learning_forecast_frame")
		self.tc.add_concat_graphic(
			"Попытка прогноза от прошлого значения",
			self.index_string_var.get(),
			self.data_set[-(offset + left_offset):-(offset - right_offset)],
			predict,
			learning_graphic_frame,
			"Реальные данные",
			"Спрогнозированные данные",
			(7, 4)
		)
		learning_graphic_frame.pack()

		metric_frame = self.tc.add_frame(self.sarima_frame, 1, "solid", name="learning_metric_forecast")
		predict_to_metrics = predict.values[1:]
		data_set_to_metrics = self.data_set.values[-offset:-offset+steps]
		mse = get_mse(data_set_to_metrics, predict_to_metrics)
		mae = get_mae(data_set_to_metrics, predict_to_metrics)
		mape = get_mape(data_set_to_metrics, predict_to_metrics)
		metric_frame_elements = [
			self.tc.add_label("Метрики качества модели:", metric_frame, 18),
			self.tc.add_label(f"Среднеквадратичная ошибка: {mse[1]:.3f}", metric_frame, 16),
			self.tc.add_label(f"Средняя абсолютная ошибка: {mae[1][0]:.3f}", metric_frame, 16),
			self.tc.add_label(f"Средняя абсолютная ошибка в процентах: {mape[1][0]:.3f}", metric_frame, 16)
		]
		self.tc.pack_elements(metric_frame_elements, "w")
		metric_frame.pack()

		errors_graphic_frame = self.tc.add_frame(self.sarima_frame, name="errors_frame")
		self.tc.add_concat_graphic(
			"Изменение функций ошибок",
			"MSE и MAE",
			mse[0],
			mae[0],
			errors_graphic_frame,
			"mse",
			"mae",
			(7, 4)
		)
		errors_graphic_frame.pack()

		self.predict_button_sarima = self.tc.add_button(self.sarima_frame, "Сделать прогноз", 14, self.start_prediction_sarima)
		self.predict_button_sarima.pack()

		self.update_canvas()
		self.end_processing()

	def learning_lstm(self):
		try:
			for widget in self.lstm_frame.nametowidget(".predict_metric").winfo_children():
				widget.destroy()
			for widget in self.lstm_frame.nametowidget(".learning_predict_frame").winfo_children():
				widget.destroy()
			for widget in self.lstm_frame.nametowidget(".forecast_metric").winfo_children():
				widget.destroy()
			for widget in self.lstm_frame.nametowidget(".learning_forecast_frame").winfo_children():
				widget.destroy()
			for widget in self.lstm_frame.nametowidget(".errors_frame").winfo_children():
				widget.destroy()
			for widget in self.sarima_frame.nametowidget(".predict_forecast_frame").winfo_children():
				widget.destroy()
		except:
			pass

		steps = 10
		offset = int(len(self.processed_data)*0.2)
		if offset < steps:
			steps = offset-1
		self.lstm_model = LSTMNetwork(self.processed_data, self.data_params, steps, offset)

		left_offset = 50
		right_offset = 50
		if len(self.processed_data[-offset:]) < right_offset:
			right_offset = len(self.processed_data[-offset:]) - 1
		if len(self.processed_data[:-offset]) < left_offset:
			left_offset = len(self.processed_data[:-offset]) - 1

		predict = self.lstm_model.get_predict_learning()
		self.data_processor.reverse_scaling(predict.values)
		learning_graphic_frame = self.tc.add_frame(self.lstm_frame, name="learning_predict_frame")
		canvas_graphic = self.tc.add_concat_graphic(
			"Проверка обученной модели",
			self.index_string_var.get(),
			self.data_set,
			predict,
			learning_graphic_frame,
			"Реальные данные",
			"Спрогнозированные данные",
			(7, 4)
		)
		learning_graphic_frame.pack()
		metric_frame = self.tc.add_frame(self.lstm_frame, 1, "solid", name="predict_metric")
		predict_to_metrics = predict.values
		data_set_to_metrics = self.data_set.values[60:]
		mse = get_mse(data_set_to_metrics, predict_to_metrics)
		mae = get_mae(data_set_to_metrics, predict_to_metrics)
		mape = get_mape(data_set_to_metrics, predict_to_metrics)
		metric_frame_elements = [
			self.tc.add_label("Метрики качества модели:", metric_frame, 18),
			self.tc.add_label(f"Среднеквадратичная ошибка: {mse[1]:.3f}", metric_frame, 16),
			self.tc.add_label(f"Средняя абсолютная ошибка: {mae[1][0]:.3f}", metric_frame, 16),
			self.tc.add_label(f"Средняя абсолютная ошибка в процентах: {mape[1][0]:.3f}", metric_frame, 16)
		]
		self.tc.pack_elements(metric_frame_elements, "w")
		metric_frame.pack()

		predict = self.lstm_model.get_forecast_learning()
		self.data_processor.reverse_scaling(predict.values)
		predict.values[0] = self.data_set.values[-offset-1]
		learning_graphic_frame = self.tc.add_frame(self.lstm_frame, name="learning_forecast_frame")
		canvas_graphic = self.tc.add_concat_graphic(
			"Проверка обученной модели",
			self.index_string_var.get(),
			self.data_set[-(offset+left_offset):-(offset-right_offset)],
			predict,
			learning_graphic_frame,
			"Реальные данные",
			"Спрогнозированные данные",
			(7,4)
		)
		learning_graphic_frame.pack()
		metric_frame = self.tc.add_frame(self.lstm_frame, 1, "solid", name="forecast_metric")
		predict_to_metrics = predict.values[1:]
		data_set_to_metrics = self.data_set.values[-offset:-offset+steps]
		mse = get_mse(data_set_to_metrics, predict_to_metrics)
		mae = get_mae(data_set_to_metrics, predict_to_metrics)
		mape = get_mape(data_set_to_metrics, predict_to_metrics)
		metric_frame_elements = [
			self.tc.add_label("Метрики качества модели:", metric_frame, 18),
			self.tc.add_label(f"Среднеквадратичная ошибка: {mse[1]:.3f}", metric_frame, 16),
			self.tc.add_label(f"Средняя абсолютная ошибка: {mae[1][0][0]:.3f}", metric_frame, 16),
			self.tc.add_label(f"Средняя абсолютная ошибка в процентах: {mape[1][0][0]:.3f}", metric_frame, 16)
		]
		self.tc.pack_elements(metric_frame_elements, "w")
		metric_frame.pack()

		errors_graphic_frame = self.tc.add_frame(self.lstm_frame, name="errors_frame")
		self.tc.add_concat_graphic(
			"Изменение функций ошибок",
			"MSE и MAE",
			mse[0],
			mae[0],
			errors_graphic_frame,
			"mse",
			"mae",
			(7, 4)
		)
		errors_graphic_frame.pack()

		self.predict_button_lstm = self.tc.add_button(self.lstm_frame, "Сделать прогноз", 14, self.start_prediction_lstm)
		self.predict_button_lstm.pack()

		self.update_canvas()
		self.end_processing()

	def predict_sarima(self):
		try:
			for widget in self.sarima_frame.nametowidget(".predict_forecast_frame").winfo_children():
				widget.destroy()
		except:
			pass

		steps = 10
		offset = 0

		left_offset = 50

		predict = self.sarima_model.get_forecast_for_predict()
		self.data_processor.reverse_scaling(predict.values)
		predict.values[0] = self.data_set.values[-offset - 1]
		predict_graphic_frame = self.tc.add_frame(self.sarima_frame, name="predict_forecast_frame")
		self.tc.add_concat_graphic(
			"Прогноз в будущее",
			self.index_string_var.get(),
			self.data_set[-left_offset:],
			predict,
			predict_graphic_frame,
			"Реальные данные",
			"Спрогнозированные данные",
			(7, 4)
		)
		predict_graphic_frame.pack()

		self.update_canvas()
		self.end_processing()

	def predict_lstm(self):
		try:
			for widget in self.lstm_frame.nametowidget(".predict_forecast_frame").winfo_children():
				widget.destroy()
		except:
			pass

		offset = 0

		left_offset = 50

		predict = self.lstm_model.get_forecast()
		self.data_processor.reverse_scaling(predict.values)
		predict.values[0] = self.data_set.values[-offset-1]
		learning_graphic_frame = self.tc.add_frame(self.lstm_frame, name="predict_forecast_frame")
		canvas_graphic = self.tc.add_concat_graphic(
			"Прогнозирование в будущее",
			self.index_string_var.get(),
			self.data_set[-left_offset:],
			predict,
			learning_graphic_frame,
			"Реальные данные",
			"Спрогнозированные данные",
			(7,4)
		)
		learning_graphic_frame.pack()

		self.update_canvas()
		self.end_processing()


	def anim_loading(self):
		count = 0
		label_text = self.loading_label["text"]
		while self.loading_label is not None:
			if count == 0 and self.loading_label is not None:
				self.loading_label.config(text=f"{label_text}")
			elif count == 1 and self.loading_label is not None:
				self.loading_label.config(text=f"{label_text}.")
			elif count == 2 and self.loading_label is not None:
				self.loading_label.config(text=f"{label_text}..")
			elif count == 3 and self.loading_label is not None:
				self.loading_label.config(text=f"{label_text}...")
				count = -1
			count += 1
			time.sleep(0.5)

	def start_learning_sarima(self):
		thread_learning_sarima = threading.Thread(target=self.learning_sarima)
		thread_anim_load = threading.Thread(target=self.anim_loading)

		self.start_processing("Обучение")

		thread_learning_sarima.start()
		thread_anim_load.start()

	def start_prediction_sarima(self):
		thread_prediction_sarima = threading.Thread(target=self.predict_sarima)
		thread_anim_load = threading.Thread(target=self.anim_loading)

		self.start_processing("Прогнозирование")

		thread_prediction_sarima.start()
		thread_anim_load.start()

	def start_learning_lstm(self):
		thread_learning_lstm = threading.Thread(target=self.learning_lstm)
		thread_anim_load = threading.Thread(target=self.anim_loading)

		self.start_processing("Обучение")

		thread_learning_lstm.start()
		thread_anim_load.start()

	def start_prediction_lstm(self):
		thread_prediction_lstm = threading.Thread(target=self.predict_lstm)
		thread_anim_load = threading.Thread(target=self.anim_loading)

		self.start_processing("Прогнозирование")

		thread_prediction_lstm.start()
		thread_anim_load.start()

	def start_data(self):
		thread_load_data = threading.Thread(target=self.starts_graphics)
		thread_anim_load = threading.Thread(target=self.anim_loading)

		self.start_processing("Загрузка данных")

		thread_load_data.start()
		thread_anim_load.start()

	def start_processing(self, text):
		try:
			self.get_index_btn.configure(state=['disable'])
			self.learning_button_sarima.configure(state=['disable'])
			self.learning_button_lstm.configure(state=['disable'])
			self.predict_button_sarima.configure(state=['disable'])
			self.predict_button_lstm.configure(state=['disable'])
		except:
			pass
		self.loading_label = self.tc.add_label(text, self.root, 14)
		self.loading_label.pack()

	def end_processing(self):
		self.loading_label.destroy()
		self.loading_label = None
		try:
			self.get_index_btn.configure(state=['normal'])
			self.learning_button_sarima.configure(state=['normal'])
			self.learning_button_lstm.configure(state=['normal'])
			self.predict_button_sarima.configure(state=['normal'])
			self.predict_button_lstm.configure(state=['normal'])
		except:
			pass

	def get_params(self):
		return [int(self.p_string_var.get()), int(self.q_string_var.get()), int(self.d_string_var.get())]

	def update_canvas(self):
		self.canvas.update_idletasks()
		self.canvas.configure(scrollregion=self.canvas.bbox("all"))

	def change_type_learning(self):
		try:
			self.type_learning_frame.nametowidget("learning_type").destroy()
		except:
			pass
		if self.type_learning_string_var.get() == "manually":
			frame = self.tc.add_frame(self.type_learning_frame, name="learning_type")

			label_params = ["p", "q", "d"]
			string_vars = [self.p_string_var, self.q_string_var, self.d_string_var]

			for i in range(3):
				param_frame = self.tc.add_frame(frame)
				param_label = self.tc.add_label(f"Введите параметр {label_params[i]}:", param_frame)
				param_input = self.tc.add_input_number(param_frame, string_vars[i])
				param_input.configure(width=4)
				param_label.grid(row=0, column=0, padx=10)
				param_input.grid(row=0, column=1)
				param_frame.grid(row=0, column=i, ipady=10, ipadx=15)

			frame.pack(side="bottom")

			self.update_canvas()
