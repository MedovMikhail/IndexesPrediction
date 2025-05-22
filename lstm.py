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
from datetime import timedelta, datetime
from indexes import Indexes
from data_processor import DataProcessor
from static_info import *
from errors_metrics import *
from files_service import LSTMFiles

class LSTMNetwork:
    def __init__(self, data_set, data_params, steps, offset=0):
        self.full_data_set = data_set
        self.data_len = len(data_set)
        self.data_set = data_set[:-offset]
        self.steps = steps
        self.offset = offset
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.full_data_set_scaled = self.scaler.fit_transform(self.full_data_set.values)
        self.data_set_scaled = self.full_data_set_scaled[:-offset]
        self.train_len = len(self.data_set_scaled)
        self.model = None
        self.lstm_files = LSTMFiles(data_params[0])
        self.mse = []
        self.mae = []
        self.mape = []
        self.fit_model(data_params)

    def get_predict_learning(self):
        inputs = self.full_data_set_scaled
        X_test = []

        for i in range(60, len(inputs-1)):
            X_test.append(inputs[i-60:i, 0])

        X_test = np.array(X_test)
        predict = self.model.predict(X_test)

        predicted = self.scaler.inverse_transform(predict)
        predicts = []
        for el in predicted:
            predicts.append(el[0])
        preds = pd.DataFrame()
        preds['Close'] = predicts
        pred_dates = self.full_data_set.reset_index()['Date'].values[60:]
        preds["Date"] = pred_dates
        preds.set_index('Date', inplace=True)
        return preds

    def get_forecast_learning(self):
        inputs = self.data_set_scaled[-60:]
        X_test = []
        for el in inputs:
            X_test.append(el[0])
        X_test = [X_test]
        predicted_values = []
        for i in range(self.steps):
            predict = self.model.predict(np.array([X_test[i]]))
            predicted_values.append(predict[0])
            X_test.append(X_test[i][1:60])
            X_test[i+1][-1] = predict[0][0]

        predicted = self.scaler.inverse_transform(predicted_values)

        values = [self.data_set.values[-1][0]]
        values.extend(predicted)
        preds = pd.DataFrame()
        preds['Close'] = values
        pred_dates = self.full_data_set.reset_index()['Date'].values[-self.offset-1:-(self.offset-self.steps)]
        preds["Date"] = pred_dates
        preds.set_index('Date', inplace=True)
        return preds

    def get_forecast(self):
        inputs = self.full_data_set_scaled[-60:]
        X_test = []
        for el in inputs:
            X_test.append(el[0])
        X_test = [X_test]
        predicted_values = []
        for i in range(self.steps):
            predict = self.model.predict(np.array([X_test[i]]))
            predicted_values.append(predict[0])
            X_test.append(X_test[i][1:60])
            X_test[i+1][-1] = predict[0][0]

        predicted = self.scaler.inverse_transform(predicted_values)

        values = [self.data_set.values[-1][0]]
        values.extend(predicted)
        preds = pd.DataFrame()
        preds['Close'] = values
        pred_dates = [self.full_data_set.reset_index()['Date'].values[-1]]
        for i in range(self.steps):
            pred_dates.append(np.datetime64(pred_dates[i].astype('M8[ms]').astype(datetime) + timedelta(1)))
        preds["Date"] = pred_dates
        preds.set_index('Date', inplace=True)
        return preds

    def fit_model(self, data_params):
        X_train, y_train = self.get_model(data_params)
        if self.model is None:
            self.model = self.create_model(X_train)
            self.model.fit(X_train, y_train, epochs=70, batch_size=32)
        self.lstm_files.create_file(self.model, data_params[1], data_params[2])

    def get_model(self, data_params):
        model = self.lstm_files.get_data(data_params[1], data_params[2])
        X_train, y_train = self.create_x_y()
        if model is not None:
            self.model = model
        return X_train, y_train


    def create_model(self, X_train):
        self.model = Sequential()
        self.model.add(LSTM(units=60, input_shape=(X_train.shape[1], 1), return_sequences=True))
        self.model.add(Dropout(0.2))
        self.model.add(LSTM(units=60))
        self.model.add(Dropout(0.2))
        self.model.add(Dense(units=1))
        self.model.compile(optimizer='adam', loss='mean_squared_error')
        return self.model

    def create_x_y(self):
        X_train = []
        y_train = []

        for i in range(60, self.train_len):
            X_train.append(self.data_set_scaled[i-60:i, 0])
            y_train.append(self.data_set_scaled[i][0])
        X_train, y_train = np.array(X_train), np.array(y_train)
        # X_train = np.reshape(X_train, (X_train.shape[0], X_train.shape[1], 1))
        return X_train, y_train
