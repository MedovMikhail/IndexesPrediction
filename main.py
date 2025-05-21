from tkinter_application import Application

class PredictionApplication:
	def __init__(self):
		self.application = Application()
		self.root = self.application.root

	def start(self):
		self.root.mainloop()


if __name__ == "__main__":
	pa = PredictionApplication()
	pa.start()
