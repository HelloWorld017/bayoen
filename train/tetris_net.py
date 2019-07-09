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
    'alpha': 0.9,
    'epsilon': 0.7,
    'epsilon_decay': 0.0001,
    'epsilon_min': 0.05,
    'clip_epsilon': 0.2,
    'entropy_loss': 1e-3,
    'epochs': 1000000,
    'sessions': 1,
    'vis_session': False
}


class TetrisNet():
    def __init__(self, configuration):
        self.model = None
        self.configs = merge_dict(default_configuration, configuration)

    def generate_model(self):
        self.old_policy = Input(batch_shape=(self.configs['batch_window_size'], len(Controller.keys)))
        self.advantage = Input(batch_shape=(self.configs['batch_window_size'], 1))

        self.field_input = Input(batch_shape=(self.configs['batch_window_size'], 10, 40, 1))
        self.field_conv1 = Convolution2D(10, 6, strides=(2, 2), activation='relu', name='field_conv1')(self.field_input)
        self.field_conv2 = Convolution2D(16, 3, strides=(3, 3), activation='relu', name='field_conv2')(self.field_conv1)
        self.field_flatten = Flatten()(self.field_conv2)
        self.field_reshape = RepeatVector(1)(self.field_flatten)
        self.field_lstm = LSTM(32, activation='tanh', stateful=True)(self.field_reshape)

        self.holdnext_input = Input(batch_shape=(self.configs['batch_window_size'], 4, 4, 6))
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
            inputs=[self.field_input, self.holdnext_input, self.old_policy, self.advantage],
            outputs=[self.policy_output, self.value_output]
        )

        self.model.compile(
            optimizer=Adam(lr=self.configs['lr']),
            loss=[
                self.get_actor_loss(),
                self.get_critic_loss()
            ]
        )

    def load_model(self, model_name):
        self.model = load_model(path.join('train', 'models', model_name))

    def predict(self, state_playfield, state_holdnext):
        return self.model.predict([
            np.array([state_playfield]),
            np.array([state_holdnext]),
            np.zeros((1, 1)),
            np.zeros((1, len(Controller.keys)))
        ])[0]

    def split_state_batch(self, state_batch):
        playfield_batch, holdnext_batch = zip(*state_batch)
        return np.array(playfield_batch), np.array(holdnext_batch)

    def predict_on_batch(self, state_batch):
        return self.model.predict_on_batch(list(self.split_state_batch(state_batch)))

    def get_actor_loss(self):
        def loss(y_true, y_pred):
            prob = y_true * y_pred
            old_prob = y_true * self.old_policy
            r = prob / (old_prob + 1e-10)

            return -backend.mean(
                backend.minimum(
                    r * self.advantage,
                    backend.clip(
                        r,
                        min_value = 1 - self.configs['clip_epsilon'],
                        max_value = 1 + self.configs['clip_epsilon']
                    ) * self.advantage,
                ) +
                self.configs['entropy_loss'] * -(prob * backend.log(prob + 1e-10))
            )

        return loss

    def get_critic_loss(self):
        def loss(y_true, y_pred):
            return backend.sum(backend.square(y_true - y_pred))

        return loss

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

        self.epsilon = self.network.configs['epsilon']

        self.state_window = MaxQueue(self.network.configs['batch_window_size'])
        self.action_window = MaxQueue(self.network.configs['batch_window_size'])
        self.prediction_window = MaxQueue(self.network.configs['batch_window_size'])
        self.local_prediction_window = MaxQueue(self.network.configs['batch_window_size'])
        self.local_value_window = MaxQueue(self.network.configs['batch_window_size'])
        self.reward_window = MaxQueue(self.network.configs['batch_window_size'])

    def clear(self):
        self.state_window.clear()
        self.action_window.clear()
        self.prediction_window.clear()
        self.local_prediction_window.clear()
        self.local_value_window.clear()
        self.reward_window.clear()

    def run(self):
        log_step = self.network.configs['epochs'] / 500

        for epoch in range(self.network.configs['epochs']):
            self.run_one()

            if epoch % log_step == 0:
                print("Epoch: %d, Average Reward: %d" % (epoch, self.reward_window.average))

    def run_one(self):
        state = self.session.get_state()
        self.state_window.push(state)

        _, action_policy = self.network.predict(s[0], s[1])
        self.prediction_window.push(action_policy)

        value, local_prediction = self.local_network.predict(s[0], s[1])
        self.local_prediction_window.push(local_prediction)
        self.local_value_window.push(value)

        if random.random() > self.epsilon:
            action = random.randrange(0, len(Controller.keys))

        else:
            action = np.random.choice(len(Controller.keys), p = action_policy)

        self.session.act(action)

        action_batch = np.zeros(shape=(len(Controller.keys), ))
        action_batch[action] = 1
        self.action_window.push(action_batch)

        reward = self.session.get_reward()
        self.reward_window.push(reward)

        terminal = self.session.update()
        self.age += 1

        if self.epsilon > self.network.configs['epsilon_min']:
            self.epsilon -= self.network.configs['epsilon_decay']

        if terminal or len(self.reward_window) >= self.network.configs['batch_window_size']:
            self.train_one()
            self.clear()

    def train_one(self):
        batch_state = np.array(self.state_window)
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

        batch_advantage = np.array(discounted_reward.reverse()) - batch_value
        batch_discounted_reward = np.array(discounted_reward)

        self.network.fit(
            x = [batch_s, batch_advantage, batch_old_policy],
            y = [batch_action, batch_discounted_reward]
        )

        if terminal:
            self.model.reset_states()

    def update_global(self):
        self.model.set_weights(
            self.network.configs['alpha'] * np.array(self.local_model.get_weights()) +
            (1 - self.network.configs['alpha']) * np.array(self.model.get_weights())
        )
