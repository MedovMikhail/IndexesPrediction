import yfinance as yf

class Indexes:
	def __init__(self, name, period, interval):
		self.data = yf.download(name, period=period, interval=interval)
		self.dates = self.data.reset_index()['Date'].values
