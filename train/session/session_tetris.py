from game import Tetris
from game.mino import get_mino
from train.session import Session

import numpy as np

autorepeat_keys = {'left', 'right', 'softdrop'}

class SessionTetris(Session):
    def __init__(self):
        self.reset()

    def act(self, a):
        action = self.game.controller.keys[a]

        for key in self.game.controller.keys:
            if key in autorepeat_keys:
                key_pressed = key in self.game.controller.pressed_keys and \
                    self.game.controller.pressed_keys[key][0] == True

                if key != action and key_pressed:
                    self.game.controller.keyup(key)

                elif key == action and not key_pressed:
                    self.game.controller.keydown(key)

            else:
                if key == action:
                    self.game.controller.keydown(key)
                    self.game.controller.keyup(key)

    def get_state(self):
        playfield = self.game.playfield_dropping
        playfield = list([[0 if playfield[y][x] is not None else 1 for x in range(10)] for y in range(20)])

        holdnext_raw = [self.game.hold.holding_piece] + self.game.drop.next_n_piece(5)
        holdnext = []
        for piece in holdnext_raw:
            if piece is None:
                shape = np.zeros((4, 4))

            else:
                if isinstance(piece, str):
                    piece = get_mino(piece)

                shape = piece.shape

            if len(shape) == 3:
                shape = np.pad(shape, ((1, 0), (1, 0)), 'constant', constant_values=0)

            holdnext.append(shape)

        return playfield, holdnext

    def get_reward(self):
        # Max Damage: 12
        # return self.last_damage / 12
        return self.last_damage / 16 + (min(self.age, 200) / 800)

    def update(self):
        self.age += 1
        self.last_damage = 0
        self.game.update()
        return self.game.finished

    def reset(self):
        self.game = Tetris()
        self.game.start_game()
        self.last_damage = 0
        self.age = 0

        def clear_callback(payload):
            self.last_damage = payload[0]

        self.game.on('clear', clear_callback)
