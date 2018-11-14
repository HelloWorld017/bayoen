from game.mino import get_mino, minos_all
from os import path
from pygame import display, draw, gfxdraw, image, transform, Surface
from pygame.font import Font
from utils import ease, ease_exp_in, ease_sin_in_out

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


class AnimationLarge(object):
    def __init__(self, visualizer, text, color, size=None):
        self.vis = visualizer
        self.text = text
        self.color = color
        self.tick = 0
        self.text_layer = self.vis.fonts['roboto-bold'].render(text, True, color)
        self.invert_layer = self.vis.fonts['roboto-bold'].render(text, True, (255, 255, 255), color)

        if size is not None:
            self.width, self.height = size

        else:
            rect = self.invert_layer.get_rect()
            self.width = int(rect.width * 5 / 3)
            self.height = int(rect.height * 5 / 3)

        self.surface = Surface((self.width, self.height))

    def update(self):
        self.surface.fill((0, 0, 0))
        self.tick += 1

        line_length = ease(ease_exp_in, self.tick, 0, self.width + self.height, 30)
        cursor_opacity = ease(ease_sin_in_out, self.tick, 0, 255, 5, time_start=3)
        cursor_x = ease(ease_exp_in, self.tick, self.width / 5, self.width * 4 / 5, 17, time_start=8)
        cursor_invert = ease(ease_exp_in, self.tick, self.width * 4 / 5, self.width / 5, 23, time_start=25)
        line_opacity = ease(ease_sin_in_out, self.tick, 255, 0, 15, time_start=30)
        text_opacity = ease(ease_sin_in_out, self.tick, 255, 0, 12, time_start=48)

        # Line Draw
        line_color = (*self.color, line_opacity)
        x_length = int(min(line_length, self.width))
        y_length = int(max(line_length - self.width, 0))

        gfxdraw.box(self.surface, (0, 0, x_length, 3), line_color)
        gfxdraw.box(self.surface, (self.width - 3, 0, 3, y_length), line_color)
        gfxdraw.box(self.surface, (self.width - x_length, self.height - 3, x_length, 3), line_color)
        gfxdraw.box(self.surface, (0, self.height - y_length, 3, y_length), line_color)

        # Cursor Draw
        cursor_color = (*self.color, cursor_opacity)
        gfxdraw.box(self.surface, (cursor_x - 6, self.height * 1 / 5, 6, self.height * 3 / 5), cursor_color)

        # Text Draw
        rect = self.text_layer.get_rect(center=(int(self.width / 2), int(self.height / 2)))
        self.text_layer.set_alpha(text_opacity)
        self.surface.blit(self.text_layer, rect, (0, 0, min(rect.width, cursor_x - rect.left), rect.height))

        irect = self.invert_layer.get_rect(center=(int(self.width / 2), int(self.height / 2)))
        irect_left = max(0, min(irect.width, cursor_invert - irect.left))
        self.invert_layer.set_alpha(text_opacity)
        self.surface.blit(self.invert_layer, rect, (irect_left, 0, irect.right - irect_left, rect.height))

class AnimationSmall(object):
    pass

class Visualizer(object):
    def __init__(self, game, screen, theme='default'):
        self.game = game
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()

        mino_size = int(min(int(self.width * 0.35), int(self.height * 0.4)) / 10)
        if mino_size % 2 != 0:
            mino_size += 1

        self.playfield_layer = Surface((10 * mino_size, 20 * mino_size))
        self.opponent_layer = Surface((10 * mino_size, 20 * mino_size))
        self.playfield_width = 10 * mino_size
        self.playfield_height = 20 * mino_size
        self.mino_size = mino_size

        self.texture_set = {}
        self.sprite = image.load(path.join('resources', 'images', '%s.png' % theme))
        sprite_size = self.sprite.get_width() / 8

        for MinoClass in minos_all:
            for key, tile in MinoClass.tiles.items():
                if isinstance(tile, str):
                    texture = Surface((mino_size, mino_size))
                    texture.fill(palette[tile])

                else:
                    x, y, rotation = tile

                    texture = Surface((sprite_size, sprite_size))
                    texture.blit(self.sprite, (-sprite_size * x, -sprite_size * y))

                    texture = transform.rotate(texture, -rotation)
                    texture = transform.scale(texture, (mino_size, mino_size))

                for i in range(4):
                    angle = i * 90
                    self.texture_set["%s:%d:%d" % (MinoClass.name, key, angle)] = transform.rotate(texture, -angle)

                self.texture_set["%s:%d:0.5x" % (MinoClass.name, key)] = transform.scale(
                    texture, (int(mino_size / 2), int(mino_size / 2))
                )

        self.fonts = {}
        font_list = {
            'noto-black': 'NotoKR-Black',
            'noto-bold': 'NotoKR-Bold',
            'roboto-bold': 'RobotoCondensed-Bold',
            'roboto-boldi': 'RobotoCondensed-BoldItalic'
        }

        for key, font in font_list.items():
            self.fonts[key] = Font(path.join('resources', 'fonts', "%s.ttf" % font), 32)

        self.animations = []
        self.animations.append(AnimationLarge(self, "Tetris", palette['cyan-400']))

    def update(self):
        self.screen.fill(palette['grey-800'])

        offset_x = self.width * 0.1 + (self.width * 0.4 - self.playfield_width) / 2
        offset_y = self.height * 0.15 + (self.height * 0.8 - self.playfield_height) / 2
        offset = (int(offset_x), int(offset_y))

        self.render_playfield(self.playfield_layer, self.game, offset)

        if self.game.opponent:
            opponent_offset = (int(self.width - offset_x - self.playfield_width), int(offset_y))

            self.render_playfield(self.opponent_layer, self.game.opponent, opponent_offset)

        display.flip()

    def draw_mino_holder(self, mino, position):
        x, y = position
        holder_size = self.mino_size * 3
        half_mino = self.mino_size / 2
        draw.rect(self.screen, palette['cyan-400'], (x, y, holder_size, holder_size), 4)

        holder_clip = ((x, y), (int(x + self.mino_size * 1.5), y), (x, int(y + self.mino_size * 1.5)))
        gfxdraw.aapolygon(self.screen, holder_clip, palette['grey-100'])
        gfxdraw.filled_polygon(self.screen, holder_clip, palette['grey-100'])

        draw.rect(self.screen, palette['cyan-400'], (
            x + holder_size - self.mino_size * 0.25,
            y + holder_size - self.mino_size * 1.5,
            self.mino_size * 0.25,
            self.mino_size * 1.5
        ))

        draw.rect(self.screen, palette['cyan-400'], (
            x + holder_size - self.mino_size * 1.5,
            y + holder_size - self.mino_size * 0.25,
            self.mino_size * 1.5,
            self.mino_size * 0.25
        ))

        if mino is None:
            return

        shape_size = len(mino.shape)

        offset_x = position[0] + ((4 - shape_size) / 2 + mino.view_xoffset + 1) * (self.mino_size / 2)
        offset_y = position[1] + ((4 - shape_size) / 2 + mino.view_yoffset + 1) * (self.mino_size / 2)

        for x in range(shape_size):
            for y in range(shape_size):
                if mino.shape[y][x] == 0:
                    continue

                texture = "%s:%d:0.5x" % (mino.name, mino.shape[y][x])
                self.screen.blit(
                    self.texture_set[texture],
                    (offset_x + x * self.mino_size / 2, offset_y + y * self.mino_size / 2)
                )


    def render_playfield(self, playfield_layer, game, offset):
        playfield_layer.fill(palette['grey-100'])

        for x in range(9):
            draw.rect(
                playfield_layer,
                palette['grey-200'],
                ((x + 1) * self.mino_size - 1, 0, 2, self.playfield_height)
            )

        for y in range(19):
            draw.rect(
                playfield_layer,
                palette['grey-200'],
                (0, (y + 1) * self.mino_size - 1, self.playfield_width, 2)
            )

        playfield = game.playfield_dropping
        ghost_x, ghost_y, ghost_rot = game.curr_piece.get_landing_position()


        for y in range(20):
            for x in range(10):
                curr_tile = playfield[y][x]

                ghost = False
                if game.curr_piece.is_position_mino_translate(x, y, ghost_x, ghost_y):
                    ghost = True

                    if curr_tile is not None:
                        ghost = False

                    curr_tile = game.curr_piece.get_position_tile_translate(x, y, ghost_x, ghost_y)

                elif curr_tile is None:
                    continue

                x_position = x * self.mino_size
                y_position = (19 - y) * self.mino_size
                mino_center = self.mino_size * 0.5

                texture = self.texture_set[curr_tile.texture + ":%d" % curr_tile.rotation]

                if ghost:
                    texture.set_alpha(128)

                playfield_layer.blit(
                    texture,
                    (x_position, y_position)
                )

                if ghost:
                    texture.set_alpha(255)

        self.screen.blit(playfield_layer, offset)

        for i, next in enumerate(game.drop.next_n_piece(5)):
            self.draw_mino_holder(next, (
                offset[0] + self.playfield_width + self.mino_size * 0.5,
                offset[1] + self.mino_size * 3.5 * i
            ))

        self.draw_mino_holder(get_mino(game.hold.holding_piece), (
            offset[0] - self.mino_size * 3.5,
            offset[1]
        ))

        if 'Tetris' in game.last_clear:
            self.animations.append(AnimationLarge(self, " ".join(game.last_clear), palette['cyan-400']))

        for anim in self.animations:
            anim.update()
            surface_rect = anim.surface.get_rect(center=(
                int(self.playfield_width / 2),
                int(self.playfield_height * 3 / 4)
            ))

            playfield_layer.blit(anim.surface, surface_rect)
