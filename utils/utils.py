from binascii import b2a_hex
from os import urandom
from time import time

import math

def now():
    return int(time() * 1000)

def transpose(matrix):
    return tuple([tuple([row[i] for row in matrix]) for i in range(len(matrix[0]))])

def reverse_row(matrix):
    return tuple(matrix[::-1])

def rotate_cw(matrix):
    return reverse_row(transpose(matrix))

def merge_dict(*dicts):
    base_dict = {}

    for dict_source in dicts:
        for key, value in dict_source.items():
            if isinstance(value, dict):
                if key not in base_dict:
                    base_dict[key] = {}

                base_dict[key] = merge_dict(base_dict[key], value)

            else:
                base_dict[key] = value

    return base_dict

def event_emitter(cls):
    def on(self, event_name, callback):
        if not hasattr(self, '_events'):
            self._events = {}

        if event_name not in self._events:
            self._events[event_name] = []

        self._events[event_name].append(callback)

    def emit(self, event_name, payload=None):
        if event_name not in self._events:
            return

        for callback in self._events[event_name]:
            callback(payload)

    cls.on = on
    cls.emit = emit

    return cls

def random_id():
    return b2a_hex(urandom(15))

def ease(ease_function, time, start, dest, duration, time_start=0, time_limit=True):
    time -= time_start
    time = max(0, time)

    change = dest - start

    if time_limit:
        time = min(time, duration)

    return ease_function(time, start, change, duration)

def ease_exp_in(t, b, c, d):
    return c * pow(2, 10 * (t / d - 1)) + b

def ease_sin_in_out(t, b, c, d):
    return - c / 2 * (math.cos(math.pi * t / d) - 1) + b

def get_soft_update_from_global_to_local(global_network, local_network, tau=1.):
    target_weights = local_network.trainable_weights + \
        sum([layer.non_trainable_weights for layer in local_network.layers], [])

    source_weights = global_network.trainable_weights + \
        sum([layer.non_trainable_weights for layer in global_network.layers], [])

    updates = []
    for tw, sw in zip(target_weights):
        updates.append((tw, tau * sw + (1. - tau) * tw))

    return updates

class MaxQueue(list):
    def __init__(self, maxlen=1000):
        self.maxlen = maxlen

    def push(self, value):
        list.append(self, value)

        if len(self) > self.maxlen:
            list.pop(self, 0)

    @property
    def average(self):
        if len(self) == 0:
            return 0

        return sum(self) / len(self)
