from utils import reverse, transpose

class Mino(object):
    color = 'black'
    shape = (
        (0, 0, 0),
        (0, 0, 0),
        (0, 0, 0)
    )
    name = ''
    srs_table = {
        '01': ((0, 0), ),
        '10': ((0, 0), ),
        '12': ((0, 0), ),
        '21': ((0, 0), ),
        '23': ((0, 0), ),
        '32': ((0, 0), ),
        '30': ((0, 0), ),
        '03': ((0, 0), )
    }

    rotation_to_vector = {
        0: (0, 1),
        1: (1, 0),
        2: (0, -1),
        3: (-1, 0)
    }

    def __init__(self, game):
        self.game = game
        self.x = 3
        self.y = 21
        self.rotation = 0

        self.shape_cache = {
            0: self.shape,
            1: reverse(transpose(self.shape)),
            2: reverse(self.shape),
            3: transpose(self.shape)
        }

        self.last_successful_movement = None
        self.last_rotation_info = None
        self.phase = 'drop'
        self.locking_start = 0
        self.tick = 0

    def placeable(self, x, y, rotation):
        shape = self.shape_cache[rotation]

        for dy in range(3):
            for dx in range(3):
                if x + dx < 0 or x + dx > 9:
                    return False

                if y + dy < 0 or y + dy > 39:
                    return False

                if shape[dy][dx] == 0:
                    continue

                if self.game.playfield[y - dy][x + dx] is not None:
                    return False

        return True

    @property
    def rotation_shape(self):
        return self.shape_cache[self.rotation]

    @property
    def is_placeable(self):
        return self.placeable(self.x, self.y, self.rotation)

    @property
    def is_locked(self):
        return self.phase == 'locked'

    @property
    def get_landing_position(self):
        max_drop = 0

        for i in range(40):
            if not placeable(self.x, self.y - i, self.rotation):
                max_drop = i - 1

        return self.x, self.y - max(0, max_drop), self.rotation

    @property
    def size(self):
        return len(self.shape)

    # /// Begin Rotation ///
    def rotate(self, direction=1):
        new_rotation = (self.rotation + direction + 4) % 4
        rotation_code = "%d%d" % (self.rotation, new_rotation)
        movement_success = False
        rotation_info = (0, 0)

        for x, y in srs_table[rotation_code]:
            if self.placeable(self.x + x, self.y + y, new_rotation):
                movement_success = True
                self.rotation = new_rotation
                self.x += x
                self.y += y

                rotation_info = (x, y)
                break

        if not movement_success:
            return False

        self.last_rotation_info = rotation_info
        self.last_successful_movement = 'rotate'
        return True

    def rotate_left(self):
        return self.rotate(-1)

    def rotate_right(self):
        return self.rotate(1)

    # /// End Rotation ///

    # /// Begin Drop ///

    def drop_one(self):
        if self.placeable(self.x, self.y - 1, self.rotation):
            if self.phase == 'locking':
                self.phase = 'drop'

            if self.phase == 'drop':
                self.last_successful_movement = 'drop'
                self.y -= 1

        else:
            if self.phase == 'drop':
                self.phase = 'locking'
                self.locking_start = self.tick

    def drop(self, amount):
        for i in range(amount):
            drop_one()

    def harddrop(self):
        x, y, rotation = self.get_landing_position()

        self.y = y
        self.last_successful_movement = 'drop'

        self.on_locked()

    # /// End Drop ///

    # /// Begin Movement ///

    def move(self, x):
        if self.placeable(self.x + x, self.y, self.rotation):
            self.last_successful_movement = 'move'
            self.x += x

    def move_left(self):
        return self.move(-1)

    def move_right(self):
        return self.move(1)

    # /// End Movement ///

    def on_locked(self):
        self.phase = 'locked'
        self.game.on_locked()

    def is_position_mino(self, x, y):
        dx = x - self.x
        dy = y - self.y

        if dx < 0 or dx >= self.size:
            return False

        if dy < 0 or dy >= self.size:
            return False

        return self.rotation_shape[dy][dx] == 1

    def update(self):
        self.tick += 1

        if self.phase == 'locking' and self.tick - self.locking_start >= self.game.configuration['lock']:
            self.on_locked()
