import tkinter as tk
from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

class TkinterCreator:
	def create_root(self, title, width, height):
		root = tk.Tk()
		width_screen = root.winfo_screenwidth()
		root.title(title)
		root.geometry(f"{width}x{height}+{int((width_screen-width)/2)}+{0}")
		return root

	def add_graphic(self, name, title, data, root, size=(7, 4)):
		sub_root = self.add_frame(root)

		self.add_label(name, sub_root, 18).pack(pady=5)
		f = Figure(figsize=size, dpi=100)
		a = f.add_subplot(111)
		a.set_title(title)
		a.plot(data, label="Исходные данные")
		a.legend()
		canvas_graphic = FigureCanvasTkAgg(f, sub_root)
		canvas_graphic.get_tk_widget().pack()
		sub_root.pack(pady=20)

	def add_concat_graphic(self, name, title, data1, data2, root, label_text1, label_text2, size=(7, 4)):
		sub_root = self.add_frame(root)

		self.add_label(name, sub_root, 18).pack(pady=5)
		f = Figure(figsize=size, dpi=100)
		a = f.add_subplot(111)
		a.set_title(title)
		a.plot(data1, label=label_text1, lw=3)
		a.plot(data2, label=label_text2)
		a.legend()
		canvas_graphic = FigureCanvasTkAgg(f, sub_root)
		canvas_graphic.get_tk_widget().pack()

		sub_root.pack(pady=20)
		return canvas_graphic

	def add_concat_graphic_with_dot(self, name, title, data1, data2, root, label_text1, label_text2, dot_place, size=(7, 4)):
		sub_root = self.add_frame(root)

		self.add_label(name, sub_root, 18).pack(pady=5)
		f = Figure(figsize=size, dpi=100)
		a = f.add_subplot(111)
		a.set_title(title)
		a.plot(data1, label=label_text1, lw=3)
		a.plot(data2, label=label_text2)
		a.plot(
			data1.reset_index()['Date'].values[-dot_place], data1.values[-dot_place], marker='o',
			   	color='red', label='Начало динамического прогноза'
		)
		a.legend()
		canvas_graphic = FigureCanvasTkAgg(f, sub_root)
		canvas_graphic.get_tk_widget().pack()

		sub_root.pack(pady=20)
		return canvas_graphic

	def add_label(self, text, root, font_size=14, background=None):
		if background is not None:
			return ttk.Label(master=root, text=text, font=("Times New Roman", font_size), background=background)
		return ttk.Label(master=root, text=text, font=("Times New Roman", font_size))

	def add_frame(self, root, border_width=0, relief=None, padding=None, width=None, name=None):
		if padding is None:
			padding = [0, 0]
		if relief is None:
			if width is None:
				return ttk.Frame(master=root, borderwidth=border_width, padding=padding, name=name)
			else:
				return ttk.Frame(master=root, borderwidth=border_width, padding=padding, width=width, name=name)
		return ttk.Frame(master=root, borderwidth=border_width, relief=relief, padding=padding, width=width, name=name)

	def add_grid(self, columns, rows, root):
		for c in range(columns):
			root.columnconfigure(index=c, weight=1)
		for r in range(rows):
			root.rowconfigure(index=r, weight=1)

	def add_combobox(self, values, root, string_var=None):
		if string_var is None:
			return ttk.Combobox(
				master=root,
				values=values,
				font=("Times New Roman", 14),
				state="readonly"
			)
		return ttk.Combobox(
			master=root,
			textvariable=string_var,
			values=values,
			font=("Times New Roman", 14),
			state="readonly"
		)

	def add_string_var(self, value):
		return tk.StringVar(value=value)

	def add_radiobutton(self, root, text, value, string_var):
		return tk.Radiobutton(
			master=root,
			text=text,
			font=("Times New Roman", 14),
			value=value,
			variable=string_var
		)

	def add_input_number(self, root, string_var):
		check = (root.register(self.check_key), "%P")
		return ttk.Entry(master=root, textvariable=string_var, validate="key", validatecommand=check)

	def add_button(self, root, text, font_size, command, name=None):
		return tk.Button(
			master=root,
			text=text,
			font=("Times New Roman", font_size),
			command=command,
			background="white",
			borderwidth=2,
			name=name
		)

	def add_canvas(self, root):
		return tk.Canvas(master=root, borderwidth=0)

	def add_scrollbar(self, root, orient, command):
		return ttk.Scrollbar(master=root, orient=orient, command=command)

	def configure_canvas(self, canvas, scrollbar, window, width):
		canvas.configure(yscrollcommand=scrollbar.set)
		scrollbar.pack(side="right", fill="y", padx=10)
		canvas.pack(side="left", fill="both", expand=True)
		canvas.create_window((4, 4), window=window, anchor="nw", width=width)

		canvas.update_idletasks()
		canvas.configure(scrollregion=canvas.bbox("all"))

	def pack_element(self, element, anchor):
		element.pack(anchor=anchor)

	def pack_elements(self, elements, anchor):
		for element in elements:
			self.pack_element(element, anchor)

	def check_key(self, newval):
		if (newval == ""):
			return True
		try:
			newval = int(newval)
			if 0 <= newval < 10:
				return True
		except:
			return False
		return False
