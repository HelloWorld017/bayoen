from pygame import display, draw, gfxdraw, Surface

import math

palette = {
    'grey-100': (24, 24, 24),
    'grey-200': (37, 37, 37),
    'grey-700': (180, 180, 180),
    'grey-750': (190, 190, 190),
    'grey-800': (210, 210, 210),
    'red-400': (255, 82, 82),
    'orange-400': (255, 121, 63),
    'yellow-400': (246, 185, 59),
    'green-400': (120, 224, 143),
    'cyan-400': (5, 186, 221),
    'cyan-600': (130, 204, 221),
    'blue-400': (52, 172, 224),
    'purple-400': (112, 111, 211)
}


def draw_circle(*args, **kwargs):
    gfxdraw.aacircle(*args, **kwargs)
    gfxdraw.filled_circle(*args, **kwargs)


class Visualizer(object):
    def __init__(self, game, screen):
        self.game = game
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()

        mino_size = int(min(int(self.width * 0.35), int(self.height * 0.4)) / 10)
        if mino_size % 2 == 0:
            mino_size += 1

        self.playfield_layer = Surface((10 * mino_size, 20 * mino_size))
        self.playfield_width = 10 * mino_size
        self.playfield_height = 20 * mino_size
        self.mino_size = mino_size

    def update(self):
        self.render_background()
        self.render_playfield()

        offset_x = self.width * 0.1 + (self.width * 0.4 - self.playfield_width) / 2
        offset_y = (self.height * 0.8 - self.playfield_height) / 2
        self.screen.blit(self.playfield_layer, (int(offset_x), int(offset_y)))

        display.flip()

    def render_background(self):
        self.screen.fill(palette['grey-800'])
        self.playfield_layer.fill(palette['grey-100'])

    def render_playfield(self):
        for x in range(9):
            draw.rect(
                self.playfield_layer,
                palette['grey-200'],
                ((x + 1) * self.mino_size - 1, 0, 2, self.playfield_height)
            )

        for y in range(19):
            draw.rect(
                self.playfield_layer,
                palette['grey-200'],
                (0, (y + 1) * self.mino_size - 1, self.playfield_width, 2)
            )

        self.render_minos()

    def render_minos(self):
        playfield = self.game.playfield_dropping

        for y in range(20):
            for x in range(10):
                curr_tile = playfield[y][x]

                if curr_tile is None:
                    continue

                x_position = x * self.mino_size
                y_position = (19 - y) * self.mino_size
                mino_center = self.mino_size * 0.5

                draw.rect(
                    self.playfield_layer,
                    palette[curr_tile.color],
                    (x_position, y_position, self.mino_size, self.mino_size)
                )

                radius = math.ceil(self.mino_size / 5)
                line_size = math.ceil(radius / 3)
                if line_size % 2 == 0:
                    line_size += 1

                draw_circle(
                    self.playfield_layer,
                    math.ceil(x_position + mino_center),
                    math.ceil(y_position + mino_center),
                    radius, palette['grey-800']
                )

                if y - 1 > 0 and playfield[y - 1][x] is not None and playfield[y - 1][x].id == curr_tile.id:
                    draw.rect(
                        self.playfield_layer,
                        palette['grey-800'],
                        (
                            math.ceil(x_position + mino_center) - math.floor(line_size / 2),
                            math.ceil(y_position + mino_center),
                            line_size,
                            self.mino_size
                        )
                    )

                if x - 1 > 0 and playfield[y][x - 1] is not None and playfield[y][x - 1].id == curr_tile.id:
                    draw.rect(
                        self.playfield_layer,
                        palette['grey-800'],
                        (
                            math.ceil(x_position - mino_center) - math.floor(line_size / 2),
                            math.ceil(y_position + mino_center),
                            self.mino_size,
                            line_size
                        )
                    )
