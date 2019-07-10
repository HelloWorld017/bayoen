from keras import backend
from keras.models import Model, clone_model, load_model
from keras.layers import Dense, Concatenate, Flatten, Input, LSTM, Reshape, RepeatVector
from keras.layers.convolutional import Convolution2D
from keras.optimizers import Adam
from os import path
from threading import Thread
from utils import get_soft_update_from_global_to_local, merge_dict, MaxQueue

import random
import numpy as np
import tensorflow as tf

default_configuration = {
    'lr': 0.001,
    'window_size': 20000,
    'batch_window_size': 128,
    'batch_size': 1,
    'gamma': 0.7,
    'alpha': 0.9,
    'epsilon': 0.7,
    'epsilon_decay': 0.0001,
    'epsilon_min': 0.05,
    'clip_epsilon': 0.2,
    'entropy_loss': 1e-3,
    'epochs': 1000000,
    'visualize': False
}


class TetrisNet():
    def __init__(self, actions, configuration):
        self.model = None
        self.configs = merge_dict(default_configuration, configuration)
        self.actions = actions

    def generate_model(self):
        self.old_policy = Input(batch_shape=(self.configs['batch_size'], self.actions), name='input_old')
        self.advantage = Input(batch_shape=(self.configs['batch_size'], 1), name='input_advantage')

        self.field_input = Input(batch_shape=(self.configs['batch_size'], 20, 10), name='input_field')
        self.field_reshape1 = Reshape((20, 10, 1))(self.field_input)
        self.field_conv1 = Convolution2D(10, 6, strides=(2, 2), activation='relu')(self.field_reshape1)
        self.field_conv2 = Convolution2D(16, 3, strides=(3, 3), activation='relu')(self.field_conv1)
        self.field_flatten = Flatten()(self.field_conv2)
        self.field_reshape2 = RepeatVector(1)(self.field_flatten)
        self.field_lstm = LSTM(32, activation='tanh', stateful=True)(self.field_reshape2)

        self.holdnext_input = Input(batch_shape=(self.configs['batch_size'], 6, 4, 4), name='input_holdnext')
        self.holdnext_conv1 = Convolution2D(
                16, 4, strides=(1, 1), activation='relu', data_format='channels_first'
            )(self.holdnext_input)
        self.holdnext_flatten = Flatten()(self.holdnext_conv1)

        self.concat = Concatenate()([self.field_lstm, self.holdnext_flatten])
        self.dense1 = Dense(32, activation='relu')(self.concat)
        self.dense2 = Dense(16, activation='relu')(self.dense1)

        self.lstm_reshape = RepeatVector(1)(self.dense2)
        self.lstm = LSTM(64, activation='tanh', stateful=True)(self.lstm_reshape)

        self.policy_output = Dense(self.actions, activation='softmax', name='policy')(self.lstm)
        self.value_output = Dense(1, name='value')(self.lstm)

        self.model = Model(
            inputs=[self.field_input, self.holdnext_input, self.old_policy, self.advantage],
            outputs=[self.policy_output, self.value_output]
        )

        self.compile_model()

    def compile_model(self):
        self.model.compile(
            optimizer=Adam(lr=self.configs['lr']),
            loss=[
                self.get_actor_loss(self.model.inputs[2], self.model.inputs[3]),
                self.get_critic_loss()
            ]
        )

        self.model._make_predict_function()
        self.model._make_train_function()

    def load_model(self, model_name):
        self.model = load_model(path.join('train', 'models', model_name))

    def predict(self, state_playfield, state_holdnext):
        prediction = self.model.predict([
            np.array([state_playfield]),
            np.array([state_holdnext]),
            np.zeros((1, self.actions)),
            np.zeros((1, 1))
        ])

        return prediction[0][0], prediction[1][0]

    def get_actor_loss(self, old_policy, advantage):
        def loss(y_true, y_pred):
            prob = y_true * y_pred
            old_prob = y_true * old_policy
            r = prob / (old_prob + 1e-10)

            return -backend.mean(
                backend.minimum(
                    r * advantage,
                    backend.clip(
                        r,
                        min_value = 1 - self.configs['clip_epsilon'],
                        max_value = 1 + self.configs['clip_epsilon']
                    ) * advantage,
                ) +
                self.configs['entropy_loss'] * -(prob * backend.log(prob + 1e-10))
            )

        return loss

    def get_critic_loss(self):
        def loss(y_true, y_pred):
            return backend.sum(backend.square(y_true - y_pred))

        return loss

    def get_local_network(self):
        local_network = TetrisNet(self.actions, self.configs)
        local_network.model = clone_model(self.model)
        local_network.model.set_weights(self.model.get_weights())
        local_network.compile_model()

        return local_network


class TetrisNetAgent():
    def __init__(self, session, network):
        self.age = 0
        self.session = session
        self.network = network
        self.local_network = network.get_local_network()
        self.model = self.network.model
        self.local_model = self.local_network.model

        self.epsilon = self.network.configs['epsilon']

        self.state_field_window = MaxQueue(self.network.configs['batch_window_size'])
        self.state_holdnext_window = MaxQueue(self.network.configs['batch_window_size'])
        self.action_window = MaxQueue(self.network.configs['batch_window_size'])
        self.prediction_window = MaxQueue(self.network.configs['batch_window_size'])
        self.local_prediction_window = MaxQueue(self.network.configs['batch_window_size'])
        self.local_value_window = MaxQueue(self.network.configs['batch_window_size'])
        self.reward_window = MaxQueue(self.network.configs['batch_window_size'])

    def clear(self, terminal):
        self.state_field_window.clear()
        self.state_holdnext_window.clear()
        self.action_window.clear()
        self.prediction_window.clear()
        self.local_prediction_window.clear()
        self.local_value_window.clear()
        self.reward_window.clear()

        if terminal:
            self.model.reset_states()
            self.local_model.reset_states()
            self.session.reset()

    def run(self):
        for epoch in range(self.network.configs['epochs']):
            self.run_one()

    def run_one(self):
        state_playfield, state_holdnext = self.session.get_state()
        self.state_field_window.push(state_playfield)
        self.state_holdnext_window.push(state_holdnext)

        action_policy, _ = self.network.predict(state_playfield, state_holdnext)
        self.prediction_window.push(action_policy)

        local_prediction, value = self.local_network.predict(state_playfield, state_holdnext)
        self.local_prediction_window.push(local_prediction)
        self.local_value_window.push(value)

        if random.random() > self.epsilon:
            action = random.randrange(0, self.network.actions)

        else:
            action = np.random.choice(self.network.actions, p = action_policy)

        self.session.act(action)

        action_batch = np.zeros(shape=(self.network.actions, ))
        action_batch[action] = 1
        self.action_window.push(action_batch)

        reward = self.session.get_reward()
        self.reward_window.push(reward)

        terminal = self.session.update()
        self.age += 1

        if self.epsilon > self.network.configs['epsilon_min']:
            self.epsilon -= self.network.configs['epsilon_decay']

        if terminal or (len(self.reward_window) >= self.network.configs['batch_window_size']):
            self.train_one(terminal)
            self.clear(terminal)

    def train_one(self, terminal):
        batch_state_field = np.array(self.state_field_window)
        batch_state_holdnext = np.array(self.state_holdnext_window)
        batch_action = np.array(self.action_window)
        batch_old_policy = np.array(self.prediction_window)
        batch_policy = np.array(self.local_prediction_window)
        batch_value = np.array(self.local_value_window)
        batch_reward = np.array(self.reward_window)

        last_reward = 0 if terminal else batch_reward[-1]
        discounted_reward = [last_reward]

        for r_t in reversed(self.reward_window[:-1]):
            last_reward = r_t + self.network.configs['gamma'] * last_reward
            discounted_reward.append(last_reward)

        discounted_reward.reverse()
        batch_discounted_reward = np.reshape(np.array(discounted_reward), (-1, 1))
        batch_advantage = batch_discounted_reward - batch_value

        print("Epoch: %d, Average Reward: %f" % (self.age, self.reward_window.average))

        self.local_model.fit(
            x = [batch_state_field, batch_state_holdnext, batch_old_policy, batch_advantage],
            y = [batch_action, batch_discounted_reward],
            batch_size=self.network.configs['batch_size']
        )

        self.update_global()

        if terminal:
            self.model.reset_states()

    def update_global(self):
        self.model.set_weights(
            self.network.configs['alpha'] * np.array(self.local_model.get_weights()) +
            (1 - self.network.configs['alpha']) * np.array(self.model.get_weights())
        )
