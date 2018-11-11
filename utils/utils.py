from time import time

def now():
    return int(time() * 1000)

def transpose(matrix):
    return tuple([tuple([row[i] for row in matrix]) for i in range(len(matrix[0]))])

def reverse(matrix):
    return tuple([tuple(row[::-1]) for row in matrix])

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
