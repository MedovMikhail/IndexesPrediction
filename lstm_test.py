import keras
from secpickle import pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from keras.api.models import Sequential
from keras.api.layers import Dense
from keras.api.layers import LSTM
from keras.api.layers import Dropout
from keras.api.layers import Bidirectional
from keras.api.layers import GRU
from keras.api.optimizers import RMSprop
from keras.api.layers import *
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split
from indexes import Indexes
from data_processor import DataProcessor
from static_info import *
from errors_metrics import *
from files_service import LSTMFiles

data = Indexes(INDEX_NAMES["S&P 500"], PERIODS["5 лет"], INTERVALS["1 день"])
dp = DataProcessor(data.data_set)
processed_data = dp.get_processed_data()

data_len = len(processed_data)
training_len = int(0.8 * data_len)

sc = MinMaxScaler(feature_range=(0, 1))
data_set_scaled = sc.fit_transform(processed_data)

training_set = data_set_scaled[:training_len]
test_set = data_set_scaled[training_len:]

X_train = []
y_train = []

for i in range(60, training_len):
  X_train.append(training_set[i-60:i, 0])
  y_train.append(training_set[i, 0])
X_train, y_train = np.array(X_train), np.array(y_train)
# X_train = np.reshape(X_train, (X_train.shape[0], X_train.shape[1], 1))

print(X_train.shape)
print(y_train.shape)

#двунаправленную лстм попробовать
def create_model(X_train):
  model = Sequential()
  model.add(LSTM(units=50, input_shape=(X_train.shape[1], 1)))
  model.add(Dropout(0.2))
  model.add(Dense(units=1))

  # Compiling the RNN
  model.compile(optimizer='adam', loss='mean_squared_error')
  return model

def fit_model(X_train, y_train, model):
  # Fitting the RNN to the Training set
  model.fit(X_train, y_train, epochs=30, batch_size=32)

# model = create_model(X_train)
# fit_model(X_train, y_train, model)
#
# pickle.dump(model, open('model.pkl', 'wb'), protocol=pickle.HIGHEST_PROTOCOL)

model = pickle.load(open('model.pkl', 'rb'))

inputs = training_set[-60:]
X_test = []
for el in inputs:
    X_test.append(el[0])
# X_test = np.array(X_test)
# X_test = np.reshape(X_test, (X_test.shape[0], X_test.shape[1], 1))

X_test=[X_test]

predicted_values = []
print(np.array([X_test[0]]).shape)

for i in range(15):
  print(np.array([X_test[i]]))
  predicted_stock_price = model.predict(np.array([X_test[i]]))
  print(X_test[i])
  print(predicted_stock_price)
  predicted_values.append(predicted_stock_price[0])
  X_test.append(X_test[i][1:60])
  X_test[i+1][-1] = predicted_stock_price[0][0]

predicted_stock_price = sc.inverse_transform(predicted_values)
predicted_stock_price = np.concatenate((np.array([processed_data.values[training_len-1]]), predicted_stock_price))

print(predicted_stock_price)

plt.plot(data.dates[training_len-100:training_len+100], processed_data[training_len-100:training_len+100], color='blue', label='Real Price')
plt.plot(data.dates[training_len-1:training_len+15], predicted_stock_price, color='red', label='Predicted Price')
plt.title('Stock Price Prediction')
plt.xlabel('Time')
plt.ylabel('Stock Price')
plt.legend()
plt.show()