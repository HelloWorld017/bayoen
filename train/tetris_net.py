from game import Controller
from keras import backend
from keras.models import Model, load_model, model_from_config
from keras.layers import Dense, Concatenate, Flatten, Input, LSTM, RepeatVector
from keras.layers.convolutional import Convolution2D
from keras.optimizers import Adam
from os import path
from threading import Thread
from utils import get_soft_update_from_global_to_local, merge_dict, MaxQueue

import numpy as np
import tensorflow as tf

default_configuration = {
    'lr': 0.001,
    'window_size': 20000,
    'batch_window_size': 32,
    'gamma': 0.7,
    'epochs': 1000000,
    'sessions': 3,
    'vis_session': True
}


class TetrisNet():
    def __init__(self, configuration):
        self.model = None
        self.configs = merge_dict(default_configuration, configuration)

    def generate_model(self):
        self.pi_theta_old = Input(batch_shape=())
        self.field_input = Input(batch_shape=(1, 10, 40, 1))
        self.field_conv1 = Convolution2D(10, 6, strides=(2, 2), activation='relu', name='field_conv1')(self.field_input)
        self.field_conv2 = Convolution2D(16, 3, strides=(3, 3), activation='relu', name='field_conv2')(self.field_conv1)
        self.field_flatten = Flatten()(self.field_conv2)
        self.field_reshape = RepeatVector(1)(self.field_flatten)
        self.field_lstm = LSTM(32, activation='tanh', stateful=True)(self.field_reshape)

        self.holdnext_input = Input(batch_shape=(1, 4, 4, 6))
        self.holdnext_conv1 = Convolution2D(
                16, 4, strides=(1, 1), activation='relu', name='holdnext_conv'
            )(self.holdnext_input)
        self.holdnext_flatten = Flatten()(self.holdnext_conv1)

        self.concat = Concatenate()([self.field_lstm, self.holdnext_flatten])
        self.dense1 = Dense(32, activation='relu')(self.concat)
        self.dense2 = Dense(16, activation='relu')(self.dense1)

        self.lstm_reshape = RepeatVector(1)(self.dense2)
        self.lstm = LSTM(64, activation='tanh', stateful=True)(self.lstm_reshape)

        self.policy_output = Dense(len(Controller.keys), activation='softmax', name='policy')(self.lstm)
        self.value_output = Dense(1, name='value')(self.lstm)

        self.model = Model(
            inputs=[self.field_input, self.holdnext_input],
            outputs=[self.policy_output, self.value_output]
        )

        self.model.compile(
            optimizer=Adam(lr=self.configs['lr']),
            loss=[

            ]
        )

        self.compile()

    def load_model(self, model_name):
        self.model = load_model(path.join('train', 'models', model_name))
        self.compile()

    def compile(self):
        self.actions = backend.placeholder(shape=(None, len(Controller.keys)))
        self.target_v = backend.placeholder(shape=(None, ))
        self.advantages = backend.placeholder(shape=(None, ))

        responsible_outputs = backend.sum(self.policy_output * self.actions, axis=1)

        value_loss = backend.sum(backend.square(self.target_v - self.value_output))
        policy_loss = -backend.sum(backend.log(backend.maximum(responsible_outputs, 1e-12)) * self.advantages)
        entopy = -backend.sum(self.policy_output * backend.log(backend.maximum(self.policy_output, 1e-12)))

        loss = 0.5 * value_loss + policy_loss - 0.01 * entropy

        self.updates = self.model.optimizer.get_updates(loss, self.model.trainable_weights)

    def predict(self, state_playfield, state_holdnext):
        return self.model.predict([
            np.array([state_playfield]),
            np.array([state_holdnext])
        ])[0]

    def split_state_batch(self, state_batch):
        playfield_batch, holdnext_batch = zip(*state_batch)
        return np.array(playfield_batch), np.array(holdnext_batch)

    def predict_on_batch(self, state_batch):
        return self.model.predict_on_batch(list(self.split_state_batch(state_batch)))

    def get_local_network(self):
        config = {
            'class_name': self.model.__class__.__name__,
            'config': self.model.get_config()
        }

        clone = model_from_config(config)
        clone.set_weights(self.model.get_weights())

        local_network = TetrisNet(self.configs)
        local_network.model = clone

        return local_network


class TetrisNetAgent():
    def __init__(self, session, network):
        self.age = 0
        self.session = session
        self.network = network
        self.local_network = network.get_local_network()
        self.model = self.network.model
        self.local_model = self.local_network.model

        self.replay_window = MaxQueue(self.network.configs['batch_window_size'])

    def run(self):
        for _ in xrange(self.network.configs['epochs']):
            self.run_one()

    def run_one(self):
        state = self.session.get_state()
        _, action_policy = self.network.predict(s[0], s[1])

        action = max(enumerate(action_policy), key=lambda v: v[1])[0]
        self.session.act(action)
        self.session.update()

        target_value = self.session.get_reward()
        self.age += 1

        value, policy = self.local_network.predict(state)

        state_playfield, state_holdnext = state
        action_batch = np.array(self.action_window[:-1])
        values = np.array(v_s[:-1])
        rewards = np.array(r_s[:-1])

        self.train([
            np.array([state_playfield]), np.array([state_holdnext]),
            state_field, state_lstm,
            action_batch, advantages, target_v
        ])

        if terminal:
            self.local_model.reset_states()

    def generate_train(self):
        # TODO lstm states?
        updates = self.local_network.updates
        updates += get_soft_update_from_global_to_local(self.model, self.local_model)
        updates += self.local_model.updates

        inputs = self.local_model.inputs + [self.local_network.advantages, self.local_network.target_v, self.local_network.actions]

        self.train = backend.function(inputs, self.local_model.outputs, updates=updates)
