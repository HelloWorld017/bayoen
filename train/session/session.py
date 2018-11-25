from game import Tetris

autorepeat_keys = {'left', 'right', 'softdrop'}

class Session():
    def get_state(self):
        pass

    def get_reward(self):
        pass

    def update(self):
        pass

class SessionTetris(Session):
    def __init__(self):
        self.game = Tetris()
        self.last_damage = 0

        def clear_callback(payload):
            self.last_damage = payload[0]

        self.game.on('clear', clear_callback)

    def act(self, a):
        action = game.controller.keys[a]

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

        holdnext = self.game.holding_piece + self.game.drop.next_n_piece(5)
        holdnext = list([piece.rotation_shape for piece in holdnext])

        return playfield, holdnext

    def get_reward(self):
        return self.last_damage / 12

    def update(self):
        self.game.update()
        return self.game.finished
