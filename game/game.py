from game.mino import MinoL, MinoJ, MinoS, MinoZ, MinoT, MinoI, MinoO
from game.visualizer import Visualizer
from random import shuffle
from utils import event_emitter, merge_dict

default_configuration = {
    'drop': {
        'normal': {
            'frame': 32,
            'amount': 1
        },

        'soft': {
            'frame': 2,
            'amount': 1
        }
    },

    'lock': 30,

    'das': {
        'start': 12,
        'period': 2
    }
}

class Controller(object):
    key_left = 'left'
    key_right = 'right'
    key_spin_cw = 'spin_cw'
    key_spin_ccw = 'spin_ccw'
    key_hold = 'hold'
    key_harddrop = 'harddrop'
    key_softdrop = 'softdrop'

    def __init__(self, game):
        self.game = game
        self.pressed_keys = []

    def keydown(self, key_name):
        pass

    def keyup(self, key_name):
        pass

class Drop(object):
    def __init__(self, game):
        self.game = game
        self.dropping_piece = None
        self.create_bag()
        self.drop_tick = 0

    def create_bag(self):
        self.randomizer = [MinoL, MinoJ, MinoS, MinoZ, MinoT, MinoI, MinoO]
        shuffle(self.randomizer)

    def new_piece(self):
        piece = self.randomizer.pop()

        if len(self.randomizer) == 0:
            self.create_bag()

        if not piece.is_placeable:
            self.game.game_over()

        self.dropping_piece = piece

    def update(self):
        self.dropping_piece.update()
        self.drop_tick += 1

        key = 'normal'
        if self.game.controller.is_pressed(Controller.key_softdrop):
            key = 'soft'

        if self.drop_tick > self.game.configuration['drop'][key]['frame']:
            self.dropping_piece.drop(self.game.configuration['drop'][key]['amount'])

class Hold(object):
    def __init__(self, game):
        self.game = game
        self.holding_piece = None
        self.is_last_hold = False

@event_emitter
class Tetris(object):
    def __init__(self, configuration):
        self.playfield = [[None] * 10] * 40
        self.configuration = merge_dict(default_configuration, configuration)
        self.controller = Controller(self)
        self.drop = Drop(self)
        self.hold = Hold(self)
        self.visualizer = None
        self.last_clear = None

    @property
    def curr_piece(self):
        return self.drop.dropping_piece

    @property
    def playfield_dropping(self):
        return [
            [self.curr_piece if self.curr_piece.is_position_mino(x, y) else self.playfield[x][y] for x in range(10)]
            for y in range(40)
        ]

    def start_game(self):
        self.drop_piece()

    def update(self):
        self.drop.update()

        if self.visualizer is not None:
            self.visualizer.visualize()

    def drop_piece(self):
        self.drop.new_piece()

    def visualize(self):
        self.visualizer = Visualizer(self)

    def on_locked(self):
        for y in range(self.curr_piece.size):
            for x in range(self.curr_piece.size):
                if self.curr_piece.rotation_shape[y][x] == 1:
                    self.playfield[y + self.curr_piece.y][x + self.curr_piece.x] = self.curr_piece

        clear_target = []
        for y in range(40):
            clear = True

            for x in self.playfield[y]:
                if self.playfield[y][x] is None:
                    clear = False

            if clear:
                clear_target.append(y)

        for y in clear_target:
            self.playfield[y] = None

        score = 0
        if len(clear_target) != 0:
            score, last_clear = self.calc_score(clear_target)
            self.last_clear = last_clear
            self.playfield = list([row if row is not None for row in self.playfield])
            self.playfield = self.playfield + [[None] * 10] * (40 - len(self.playfield))

        self.drop_piece()

        return score

    def calc_score(self, clear_target):
        pass

    def game_over(self):
        self.emit('gameover')
