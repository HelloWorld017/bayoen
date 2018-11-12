from game.mino import get_mino, minos
from game.visualizer import Visualizer
from random import shuffle
from utils import event_emitter, merge_dict, now

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
        self.tick = 0

    def keydown(self, key_name):
        if key_name == self.key_hold:
            self.game.hold.hold()

        elif key_name == self.key_spin_ccw:
            self.game.curr_piece.rotate_left()

        elif key_name == self.key_spin_cw:
            self.game.curr_piece.rotate_right()

        elif key_name == self.key_harddrop:
            self.game.curr_piece.harddrop()

        elif key_name == self.key_left:
            self.game.curr_piece.move_left()

        elif key_name == self.key_right:
            self.game.curr_piece.move_right()

        self.pressed_keys[key_name] = [True, self.tick]

    def keyup(self, key_name):
        self.pressed_keys[key_name] = [False]

    def update(self):
        self.tick += 1

        for key in (self.key_left, self.key_right):
            if key not in self.pressed_keys or not self.pressed_keys[key][0]:
                continue

            if self.pressed_keys[key][1] < self.game.configuration['das']['start']:
                continue

            if self.pressed_keys[key][1] % self.game.configuration['das']['preiod'] == 0:
                if key == self.key_left:
                    self.game.curr_piece.move_left()

                elif key == self.key_right:
                    self.game.curr_piece.move_right()

    def is_pressed(self, key):
        return key in self.pressed_keys and self.pressed_keys[key][0]


class Drop(object):
    def __init__(self, game):
        self.game = game
        self.dropping_piece = None
        self.drop_tick = 0
        self.current_bag = None
        self.next_bag = None
        self.create_bag()
        self.create_bag()

    def create_bag(self):
        self.current_bag = self.next_bag
        self.next_bag = minos[:]
        shuffle(self.current_bag)

    def new_piece(self, piece_type=None, broadcast=True):
        if piece_type is not None:
            NewPiece = get_mino(piece_type)

        else:
            NewPiece = self.current_bag.pop(0)

        piece = NewPiece()

        if len(self.current_bag) == 0:
            self.create_bag()

        if not piece.is_placeable:
            self.game.game_over()

        self.dropping_piece = piece

        if broadcast:
            self.game.emit('drop', piece)

    def update(self):
        self.dropping_piece.update()
        self.drop_tick += 1

        key = 'normal'
        if self.game.controller.is_pressed(Controller.key_softdrop):
            key = 'soft'

        if self.drop_tick > self.game.configuration['drop'][key]['frame']:
            self.dropping_piece.drop(self.game.configuration['drop'][key]['amount'])

    @property
    def next_n_piece(self, n):
        amount = min(7, n)
        slice_one = self.current_bag[:amount]

        left_amount = amount - len(slice_one)
        slice_two = self.next_bag[:left_amount]

        return slice_one + slice_two

class Hold(object):
    def __init__(self, game):
        self.game = game
        self.holding_piece = None
        self.is_last_hold = False

        self.game.on('drop', lambda: self.on_drop())

    def hold():
        if self.is_last_hold:
            return

        original_holding = self.holding_piece
        self.holding_piece = self.game.curr_piece.name
        self.drop_piece(original_holding, broadcast=False)

        self.is_last_hold = True

    def on_drop():
        self.is_last_hold = False

class ScoreCalc(object):
    line_clear_text = ['Single', 'Double', 'Triple', 'Tetris']
    combo_damage = [0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 4]

    def __init__(self, game):
        self.game = game
        self.b2b = False
        self.combo = 0

    def calc_score(self, clear_target):
        damage = 0
        text = []
        piece = self.game.curr_piece
        last_b2b = self.b2b
        clear_y = [y for y, row in clear_target]

        self.b2b = False

        # T-Spin
        if piece.last_successful_movement == 'rotate' and piece.name == 't':
            center_x = piece.x + 1
            center_y = piece.y - 1

            corners = 0
            for dx in range(2):
                for dy in range(2):
                    diagonal_x = center_x + (2 * dx - 1)
                    diagonal_y = center_y + (2 * dy - 1)

                    if self.game.is_filled(diagonal_x, diagonal_y):
                        corners += 1

            if corners >= 3:
                is_mini = True

                lri = piece.last_rotation_info

                if lri[1] == -2 and lri[0] != 0:
                    is_mini = False

                rotation_vector = rotation_to_vector[piece.rotation]
                normal_vector = (rotation_vector[1], rotation_vector[0])
                rotate_center = (center_x + rotation_vector[0], center_y + rotation_vector[1])

                diag1 = (rotate_center[0] + normal_vector[0], rotate_center[1] + normal_vector[1])
                diag2 = (rotate_center[0] + normal_vector[0] * -1, rotate_center[1] + normal_vector * -1)

                if self.game.is_filled(diag1[0], diag1[1]) and self.game.is_filled(diag2[0], diag2[1]):
                    is_mini = False

                if not is_mini:
                    damage += 1 + len(clear_target)
                    text.append('T-Spin')

                else:
                    text.append('T-Spin Mini')

                self.b2b = True

        # Default damage
        if len(clear_target) > 0:
            if len(clear_target) < 4:
                damage += len(clear_target) - 1

            else:
                damage += 4
                self.b2b = True

            text.append(self.line_clear_text[len(clear_target) - 1])

        # Perfect Clear
        is_perfect = True
        for y in range(40):
            if y in clear_y:
                continue

            for x in range(10):
                if self.playfield[y][x] is not None:
                    is_perfect = False

        if is_perfect:
            damage += 10

            text.append("Perfect Clear")

        # Back to Back
        if last_b2b:
            text.append("Back-to-Back")

        # Combo Damage
        if self.combo > 0:
            if self.combo <= 10:
                damage += self.combo_damage[self.combo]

            else:
                damage += 5

            text.append("%d Ren" % self.combo)

        if len(clear_target) > 0:
            self.combo += 1

        else:
            self.combo = 0

        return damage, " ".join(text)


@event_emitter
class Tetris(object):
    def __init__(self, configuration):
        self.playfield = [[None] * 10] * 40
        self.configuration = merge_dict(default_configuration, configuration)
        self.controller = Controller(self)
        self.drop = Drop(self)
        self.hold = Hold(self)
        self.calc = ScoreCalc(self)
        self.visualizer = None
        self.last_clear = None

    @property
    def curr_piece(self):
        return self.drop.dropping_piece

    @property
    def playfield_dropping(self):
        return [
            [self.curr_piece if self.curr_piece.is_position_mino(x, y) else self.playfield[y][x] for x in range(10)]
            for y in range(40)
        ]

    def is_filled(self, x, y):
        if x < 0 or x > 9:
            return True

        if y < 0 or y > 39:
            return True

        return self.playfield[y][x] is not None

    def start_game(self):
        self.drop_piece()

    def update(self):
        self.drop.update()
        self.controller.update()

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
                clear_target.append([y, self.playfield[y]])

        score, last_clear = self.calc.calc_score(clear_target)
        self.last_clear = last_clear

        for y, row in clear_target:
            self.playfield[y] = None

        self.playfield = list([row if row is not None for row in self.playfield])
        self.playfield = self.playfield + [[None] * 10] * (40 - len(self.playfield))

        self.drop_piece()
        self.emit('clear', score)

    def game_over(self):
        self.emit('gameover')
