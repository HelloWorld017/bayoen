from game import Controller
from keras import backend
from keras.models import Model, load_model, model_from_config
from keras.layers import Dense, Concatenate, Flatten, Input, LSTM
from keras.layers.convolutional import Convolution2D
from keras.optimizers import Adam
from os import path
from threading import Thread
from utils import get_soft_update_from_global_to_local, merge_dict, MaxQueue

import numpy as np
import tensorflow as tf

default_configuration = {
    'lr': 0.001,
    'window_size': 20000
}


class TetrisNet():
    def __init__(self, configuration):
        self.model = None
        self.configs = merge_dict(default_configuration, configuration)

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
        return self.model.predict(np.array([state]))[0]

    def get_local_network(self):
        config = {
            'class_name': self.model.__class__.__name__,
            'config': self.model.get_config()
        }

        clone = model_from_config(config)
        clone.set_weights(self.model.get_weights())

        return clone


class Agent():
    def __init__(self, session, network, lock):
        self.age = 0
        self.session = session
        self.network = network
        self.model = network.model
        self.local_model = network.get_local_model()
        self.lock = lock

        self.state_window = MaxQueue(self.network.configs['batch_size'])
        self.action_window = MaxQueue(self.network.configs['batch_size'])
        self.reward_window = MaxQueue(self.network.configs['batch_size'])
        self.terminal_window = MaxQueue(self.network.configs['batch_size'])

        self.generate_train()

    def run_one(self):
        s = np.array(self.session.get_state())
        _, action_policy = self.network.predict(s)
        a = max(enumerate(action_policy), key=lambda v: v[1])[0]

        self.state_window.push(s)
        self.action_window.push(a)

        self.session.act(a)
        terminal = self.session.update()

        self.terminal_window.push(terminal)
        r = self.session.get_reward()
        self.reward_window.push(r)
        self.age += 1

        if len(self.state_window) <= self.network.configs['batch_size']:
            return

        state_batch = np.array(self.state_window)
        v_s, policy = self.model.predict_on_batch(state_batch)

        last_reward = 0. if terminal else v_s[-1]
        r_s = [last_reward]

        for r_t, t in zip(reversed(self.reward_window[:-1]), reversed(self.terminal_window[:-1])):
            last_reward = r_t + self.network.configs['gamma'] * last_reward if not t else r_t

        r_s = list(reversed(r_s))

        state_batch = np.array(state_batch[:-1])
        action_batch = np.array(self.action_window[:-1])

    def generate_train(self):
        updates = self.network.updates
        updates += get_soft_update_from_global_to_local(self.model, self.local_model)
        updates += self.model.updates

        self.train = backend.function(self.model.inputs, self.model.outputs, updates=updates)
