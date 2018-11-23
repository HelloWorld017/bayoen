from game import Controller
from keras import backend
from keras.models import Model, load_model
from keras.layers import Dense, Concatenate, Flatten, Input, LSTM
from keras.layers.convolutional import Convolution2D
from keras.optimizers import Adam
from os import path
from threading import Thread
from utils import get_soft_update_from_global_to_local, merge_dict, MaxQueue

import tensorflow as tf

default_configuration = {
    'lr': 0.001,
    'window_size': 20000
}


class TetrisNet():
    def __init__(self, configuration):
        self.model = None
        self.configs = merge_dict(default_configuration, configuration)
        self.reward_window = MaxQueue(self.configs['window_size'])

    def generate_model(self):
        self.field_input = Input(shape=(None, 10, 40, 1))
        self.field_conv1 = Convolution2D(10, 6, (2, 2), activation='relu', name="field_conv1")(self.field_input)
        self.field_conv2 = Convolution2D(16, 3, (3, 3), activation='relu', name="field_conv2")(self.field_conv1)
        self.field_flatten = Flatten()(self.field_conv2)
        self.field_lstm = LSTM(32, activation='tanh', stateful=True)(self.field_flatten)

        self.holdnext_input = Input(shape=(None, 4, 4, 6))
        self.holdnext_conv1 = Convolution2D(16, 4, (1, 1), activation='relu', name='holdnext_conv')(self.holdnext_input)
        self.holdnext_flatten = Flatten()(self.holdnext_conv1)

        self.concat = Concatenate()([self.field_lstm, self.holdnext_flatten])
        self.dense1 = Dense(32, activation='relu')(self.concat)
        self.dense2 = Dense(16, activation='relu')(self.dense1)

        self.lstm = LSTM(64, activation='tanh', stateful=True)(self.dense2)

        self.policy_output = Dense(len(Controller.keys), activation='softmax' name='policy')(self.lstm)
        self.value_output = Dense(1, name='value')(self.lstm)

        self.model = Model(
            inputs=[self.field_input, self.holdnext_input],
            outputs=[self.policy_output, self.value_output]
        )

        self.model.compile(
            loss={
                'policy': lambda y_true, y_pred: - backend.sum(backend.log(
                        y_true * y_pred + (1 - y_true) * (1 - y_pred) + 1e-5
                    ), axis=-1),

                'value': lambda y_true, y_pred: backend.sum(backend.square(y_pred - y_true), axis=-1)
            },
            loss_weights={'policy': 1.0, 'value': 0.5},
            optimizer=Adam(lr=self.configs['lr'])
        )

        self.compile()

    def load_model(self, model_name):
        self.model = load_model(path.join('train', 'models', model_name))
        self.compile()

    def compile(self):
        self.updates = self.model.optimizer.get_updates(self.model.total_loss, self.model.trainable_weights)

    def sess_restart(self):
        self.model.reset_states()

    def predict(self, state):
        pass

    def get_local_network(self):
        pass

class Agent():
    def __init__(self, session, network, lock):
        self.age = 0
        self.session = session
        self.network = network
        self.model = network.model
        self.local_model = network.get_local_model()
        self.lock = lock
        self.last_state = None

    def run_one(self):
        if self.last_state is None:
            self.last_state = self.session.get_state()
            self.session.update()
            return

        s = self.last_state
        a = self.network.predict(s)
        self.session.act(a)
        self.session.update()
        r = self.session.get_reward()
        s_next = self.session.get_state()
        self.last_state = s_next

        self.lock.acquire()
        self.network.reward_window.push(r)
        self.lock.release()

        self.age += 1

    def generate_train(self):
        updates = self.network.updates
        updates += get_soft_update_from_global_to_local(self.model, self.local_model)
        updates += self.model.updates

        self.train = backend.function(self.model.inputs, self.model.outputs, updates=updates)
