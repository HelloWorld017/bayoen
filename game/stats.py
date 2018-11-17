from copy import deepcopy
from utils import now

class StatWindow(object):
    def __init__(self):
        self.dict = {}
        self.connected = []

    def push(self, key, value, has_timestamp=False):
        if key not in self.dict:
            self.dict[key] = []

        if has_timestamp:
            data = value

        else:
            data = [value, now()]

        self.dict[key].append(data)

        for connected in self.connected:
            connected.push(key, data, True)

    def get_value(self, key):
        if key not in self.dict:
            return 0

        value_sum = sum([value for value, timestamp in self.dict[key]])

        if '-per-' in key:
            return value_sum / len(self.dict[key])

        return value_sum

    def clear(self):
        for key, value in self.dict.items():
            if isinstance(value, list):
                self.dict[key] = []

            else:
                self.dict[key] = 0

    def connect(self, window):
        self.connected.append(window)

    def clone(self):
        window = StatWindow()
        window.dict = deepcopy(self.dict)

        return window


class Statistics(object):
    def __init__(self, game, reset_rate=60):
        self.last_stats = StatWindow()
        self.overall_stats = StatWindow()
        self.overall_stats.connect(self.last_stats)

        self.key_before_drops = 0
        self.tick = 0
        self.reset_rate = reset_rate

        self.game = game
        self.game.on('clear', lambda payload: self.on_drop(*payload))
        self.game.on('keydown', lambda payload: self.on_key())

    def update(self):
        self.tick += 1

        time_limit = now() - 1000 * self.reset_rate
        for key, value_array in self.last_stats.dict.items():
            self.last_stats[key] = [value for value in value_array if value[1] > time_limit]

    def on_key(self):
        self.key_before_drops += 1
        self.overall_stats.push('key', 1)

    def on_drop(self, damage, text, clear_info):
        self.overall_stats.push('clear', clear_info['clear'])
        self.overall_stats.push('drops', 1)
        self.overall_stats.push('damage', damage)
        self.overall_stats.push('key-per-drop', self.key_before_drops)
        self.key_before_drops = 0

    def get_stats(self, stat_name, is_overall=False, per_name=None, per_stat_offset=1):
        stat_window = self.last_stats

        if is_overall:
            stat_window = self.overall_stats

        stat = stat_window.get_value(stat_name)
        per_stat = 1

        if per_name is not None:
            if per_name == 'minute':
                per_stat = self.tick / 3600
                if not is_overall:
                    per_stat = max(self.reset_rate / 60, per_stat)

            elif per_name == 'second':
                per_stat = self.tick / 60
                if not is_overall:
                    per_stat = max(self.reset_rate, per_stat)

            else:
                per_stat = stat_window.get_value(per_name)

            per_stat += per_stat_offset

        return stat / per_stat
