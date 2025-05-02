import threading
import time
import tkinter_creator as tc
from arimaModel import SarimaxModel
from data_processor import DataProcessor
from indexes import Indexes

WIDTH = 1200
HEIGHT = 750

INDEX_NAMES = {
	"S&P 500": "^GSPC",
	"Dow Jones": "^DJI",
	"Russel": "^RUT",
	"Nasdaq Composite": "^IXIC",
}

PERIODS = {
	"Максимум": "max",
	"7 лет": "7y",
	"5 лет": "5y",
	"3 года": "3y",
	"1 год": "1y",
}

INTERVALS = {
	"1 день": "1d",
	"1 неделя": "1wk",
	"1 месяц": "1mo",
	"3 месяца": "3mo"
}

class Application:
	def __init__(self):
		self.root = tc.create_root("НИР_8 V1.0.0", WIDTH, HEIGHT)

		self.processed_data = []
		self.data_params = []
		self.predict_button = None
		self.loading_label = None
		self.start_predict_btn = None
		self.type_learning_frame = None

		self.index_string_var = tc.add_string_var(list(INDEX_NAMES.keys())[0])
		self.period_string_var = tc.add_string_var(list(PERIODS.keys())[0])
		self.interval_string_var = tc.add_string_var(list(INTERVALS.keys())[0])
		self.type_learning_string_var = tc.add_string_var("auto")
		self.p_string_var = tc.add_string_var("0")
		self.q_string_var = tc.add_string_var("0")
		self.d_string_var = tc.add_string_var("0")

		self.upbar()

		self.canvas = tc.add_canvas(self.root)
		self.arima_frame = tc.add_frame(self.canvas, 1, "sunken", [8, 10])
		self.scrollbar = tc.add_scrollbar(self.root, "vertical", self.canvas.yview)

		tc.configure_canvas(self.canvas, self.scrollbar, self.arima_frame, WIDTH)

	def upbar(self):
		header = tc.add_label("Прогнозирование биржевых индексов", self.root, 20)
		header.pack()
		inputs_frame = tc.add_frame(self.root)

		indexes_frame = tc.add_frame(inputs_frame)
		periods_frame = tc.add_frame(inputs_frame)
		intervals_frame = tc.add_frame(inputs_frame)

		input_frame_elements = [
			tc.add_label("Выберите биржевой индекс:", indexes_frame, 16),
			tc.add_combobox(list(INDEX_NAMES.keys()), indexes_frame, self.index_string_var),
			tc.add_label("Выберите период:", periods_frame, 16),
			tc.add_combobox(list(PERIODS.keys()), periods_frame, self.period_string_var),
			tc.add_label("Выберите интервал:", intervals_frame, 16),
			tc.add_combobox(list(INTERVALS.keys()), intervals_frame, self.interval_string_var)
		]

		inputs_frame.pack(fill="x", pady=20)

		tc.add_grid(3, 1, inputs_frame)

		indexes_frame.grid(column=0, row=0)
		periods_frame.grid(column=1, row=0)
		intervals_frame.grid(column=2, row=0)

		tc.pack_elements(input_frame_elements, "w")

		self.start_predict_btn = tc.add_button(self.root, "Загрузить данные", 14, self.start_data)
		self.start_predict_btn.pack(anchor="center", pady=10, ipadx=5, ipady=3)

	def start_graphics(self):
		company_name = self.index_string_var.get()
		period_name = self.period_string_var.get()
		interval_name = self.interval_string_var.get()

		company_value = INDEX_NAMES.get(company_name)
		period_value = PERIODS.get(period_name)
		interval_value = INTERVALS.get(interval_name)

		for widget in self.arima_frame.winfo_children():
			widget.destroy()

		#Исходные данные
		self.data_params = [company_value, period_value, interval_value]
		indexes = Indexes(company_value, period_value, interval_value)
		tc.add_graphic("Исходные данные", company_name, indexes.data['Close'], self.arima_frame)

		#Преобразованные данные
		data_processor = DataProcessor(indexes.data['Close'])
		self.processed_data = data_processor.get_processed_data()
		tc.add_graphic("Преобразованные данные", company_name, self.processed_data, self.arima_frame)

		self.prepare_to_learning()

	def prepare_to_learning(self):
		#Выбор способа задания параметров
		self.type_learning_frame = tc.add_frame(self.arima_frame)
		type_learning_frame_static = tc.add_frame(self.type_learning_frame)
		tc.add_label("Выберите способ задания параметров:", type_learning_frame_static, 18).pack(pady=10)
		radio1 = tc.add_radiobutton(type_learning_frame_static, "Автоматически", "auto", self.type_learning_string_var)
		radio2 = tc.add_radiobutton(type_learning_frame_static, "Вручную", "manually", self.type_learning_string_var)

		radio1.configure(command=self.change_type_learning)
		radio2.configure(command=self.change_type_learning)
		radio1.pack(side="left")
		radio2.pack(side="right")

		type_learning_frame_static.pack()
		self.type_learning_frame.pack(pady=15)

		self.predict_button = tc.add_button(self.arima_frame, "Обучить модель", 14, self.start_prediction)
		self.predict_button.pack()

		self.update_canvas()
		self.end_processing(self.start_predict_btn)

	def learning(self):
		sarimaxModel = SarimaxModel(self.processed_data, self.data_params, 30, 15, 30)
		predict = sarimaxModel.preds
		canvas_graphic = tc.add_concat_graphic(
			"Проверка обученной модели",
			self.index_string_var.get(),
			self.processed_data[-100:],
			predict,
			self.arima_frame,
			"Реальные данные",
			"Спрогнозированные данные"
		)

		metric_frame = tc.add_frame(self.arima_frame, 1, "solid")
		metric_frame_elements = [
			tc.add_label("Метрики качества модели:", metric_frame, 18),
			tc.add_label(f"Среднеквадратичная ошибка: {sarimaxModel.mse:.3f}", metric_frame, 16),
			tc.add_label(f"Средне абсолютная ошибка: {sarimaxModel.mae:.3f}", metric_frame, 16)
		]
		tc.pack_elements(metric_frame_elements, "w")
		metric_frame.pack(ipadx=int((canvas_graphic.get_tk_widget().winfo_reqwidth()- metric_frame.winfo_reqwidth())/2), ipady=10)

		self.update_canvas()
		self.end_processing(self.predict_button)

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

	def start_prediction(self):
		thread_prediction = threading.Thread(target=self.learning)
		thread_anim_load = threading.Thread(target=self.anim_loading)

		self.start_processing(self.predict_button, "Обучение")

		thread_prediction.start()
		thread_anim_load.start()

	def start_data(self):
		thread_load_data = threading.Thread(target=self.start_graphics)
		thread_anim_load = threading.Thread(target=self.anim_loading)

		self.start_processing(self.start_predict_btn, "Загрузка данных")

		thread_load_data.start()
		thread_anim_load.start()

	def start_processing(self, button, text):
		button.configure(state=['disable'])
		self.loading_label = tc.add_label(text, self.root, 14)
		self.loading_label.pack()

	def end_processing(self, button):
		self.loading_label.destroy()
		self.loading_label = None
		button.configure(state=['normal'])

	def update_canvas(self):
		self.canvas.update_idletasks()
		self.canvas.configure(scrollregion=self.canvas.bbox("all"))

	def change_type_learning(self):
		try:
			self.type_learning_frame.nametowidget("learning_type").destroy()
		except:
			pass
		if self.type_learning_string_var.get() == "manually":
			frame = tc.add_frame(self.type_learning_frame, name="learning_type")
			input_p = tc.add_input_number(frame, self.p_string_var)
			input_q = tc.add_input_number(frame, self.q_string_var)
			input_d = tc.add_input_number(frame, self.d_string_var)
			input_p.grid(row=0, column=0)
			input_q.grid(row=0, column=1)
			input_d.grid(row=0, column=2)
			frame.pack(side="bottom")
