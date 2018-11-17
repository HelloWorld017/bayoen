from game.mino import get_mino, minos_all
from os import path
from pygame import display, draw, gfxdraw, image, locals as pg_locals, transform, Surface
from pygame.font import Font
from utils import ease, ease_exp_in, ease_sin_in_out

import math

palette = {
    'grey-100': (24, 24, 24),
    'grey-200': (37, 37, 37),
    'grey-700': (180, 180, 180),
    'grey-800': (190, 190, 190),
    'grey-850': (220, 220, 220),
    'grey-900': (241, 241, 241),
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


def draw_text(surface, position, font, text, align_right=True, color=palette['grey-100']):
    text_image = font.render(text, True, color)
    text_rect = text_image.get_rect()

    text_rect.topleft = position

    if align_right:
        text_rect.right = position[0]

    surface.blit(text_image, text_rect)


def draw_batch(surface, x, y, gap, font, text_list, **kwargs):
    for i, text in enumerate(text_list):
        draw_text(surface, (x, y + i * gap), font, text, **kwargs)


def get_stat(stat, *args, **kwargs):
    number = stat.get_stats(*args, **kwargs)

    if number > 1000000:
        return math.floor(text / 1000000) + 'M'

    elif number > 1000:
        return math.floor(text / 1000) + 'K'

    if number % 1 == 0:
        return str(int(number))

    return str(math.floor(number * 100) / 100)


class AnimationLarge(object):
    def __init__(self, visualizer, text, color, size=None):
        self.vis = visualizer
        self.text = text
        self.color = color
        self.tick = 0
        self.text_layer = self.vis.fonts['roboto-bold'].render(text, True, color)
        self.invert_layer = self.vis.fonts['roboto-bold'].render(text, True, (255, 255, 255))
        self.alpha_filter = Surface(self.invert_layer.get_rect().size, pg_locals.SRCALPHA)

        if size is not None:
            self.width, self.height = size

        else:
            rect = self.invert_layer.get_rect()
            self.width = int(rect.width * 5 / 2)
            self.height = int(rect.height * 5 / 3)

        self.surface = Surface((self.width, self.height), flags=pg_locals.SRCALPHA)
        self.finished = False

    def update(self):
        self.tick += 0.2

        line_length = ease(ease_exp_in, self.tick, 0, self.width + self.height, 30)
        cursor_opacity = ease(ease_sin_in_out, self.tick, 0, 255, 5, time_start=3)
        cursor_x = ease(ease_exp_in, self.tick, self.width / 5, self.width * 4 / 5, 17, time_start=8)
        cursor_invert = ease(ease_exp_in, self.tick, self.width * 4 / 5, self.width / 5, 23, time_start=25)
        line_opacity = ease(ease_sin_in_out, self.tick, 255, 0, 15, time_start=30)
        invert_opacity = ease(ease_sin_in_out, self.tick, 255, 0, 12, time_start=48)
        invert_text_opacity = ease(ease_sin_in_out, self.tick, 255, 0, 12, time_start=60)
        surface_opacity = ease(ease_sin_in_out, self.tick, 80, 0, 12, time_start=72)

        # Rest
        self.surface.fill((0, 0, 0, int(surface_opacity)))

        # Line Draw
        line_color = (*self.color, line_opacity)
        x_length = int(min(line_length, self.width))
        y_length = int(max(line_length - self.width, 0))
        rect = self.text_layer.get_rect(center=(int(self.width / 2), int(self.height / 2)))

        self.surface.fill(line_color, (0, 0, x_length, 3))
        self.surface.fill(line_color, (self.width - 3, 0, 3, y_length))
        self.surface.fill(line_color, (self.width - x_length, self.height - 3, x_length, 3))
        self.surface.fill(line_color, (0, self.height - y_length, 3, y_length))

        if int(invert_text_opacity) != 255:
            self.alpha_filter.fill((255, 255, 255, int(invert_text_opacity)))
            text_copy = self.invert_layer.copy()
            text_copy.blit(self.alpha_filter, (0, 0), special_flags=pg_locals.BLEND_RGBA_MULT)
            self.surface.blit(text_copy, rect)

            if self.tick >= 84:
                self.finished = True

            return

        # Cursor Draw
        cursor_color = (*self.color, cursor_opacity)
        self.surface.fill(cursor_color, (cursor_x - 6, int(self.height * 1 / 5), 6, int(self.height * 3 / 5)))

        # Text Draw
        clip_rect = (0, 0, max(0, min(rect.width, cursor_x - rect.left)), rect.height)
        self.surface.blit(self.text_layer, rect, clip_rect)

        # Invert Draw
        invert_color = (*self.color, invert_opacity)
        invert_rect = (cursor_invert, rect.top, int(self.width * 4 / 5 - cursor_invert), rect.height)
        self.surface.fill(invert_color, invert_rect)

        cursor_position = max(0, min(rect.width, cursor_invert - rect.left))
        layer_position = (rect.left + cursor_position, rect.top)
        clip_rect = (cursor_position, 0, rect.width - cursor_position, rect.height)
        self.surface.blit(self.invert_layer, layer_position, clip_rect)

class AnimationSmall(object):
    pass

class Visualizer(object):
    def __init__(self, game, screen, theme='default'):
        self.game = [game]
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()

        mino_size = int(min(int(self.width * 0.35), int(self.height * 0.4)) / 10)
        if mino_size % 2 != 0:
            mino_size += 1

        self.playfield_layer = [Surface((10 * mino_size, 20 * mino_size))]
        self.playfield_width = 10 * mino_size
        self.playfield_height = 20 * mino_size
        self.mino_size = mino_size

        self.statistics_width = int(self.width / 3)
        self.statistics_layer = Surface((self.statistics_width, self.height))

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

        self.fonts['noto-black64'] = Font(path.join('resources', 'fonts', 'NotoKR-Black.ttf'), 64)

        self.animations = [[]]
        self.animation_tick = [0]
        self.names = [None, None]

        if game.opponent is not None:
            self.game.append(game.opponent)
            self.playfield_layer.append(Surface((10 * mino_size, 20 * mino_size)))
            self.animations.append([])
            self.animation_tick.append(0)

        for game_key, game_instance in enumerate(self.game):
            game_instance.on('clear', lambda payload, game_key=game_key: self.add_animation(payload, game_key))
            self.names[game_key] = self.fonts['roboto-boldi'].render(game_instance.name, True, palette['grey-100'])

        self.prepare_statistics()

    def add_animation(self, payload, player_id):
        new_anim = None
        if payload[2]['perfect']:
            new_anim = AnimationLarge(self, "Perfect Clear", palette['purple-400'])

        elif payload[2]['tetris']:
            new_anim = AnimationLarge(self, "Tetris", palette['cyan-400'])

        elif payload[2]['ren'] > 5:
            new_anim = AnimationLarge(self, "%d Ren" % payload[2]['ren'], palette['red-400'])

        elif payload[2]['tspin']:
            add_anim = False

            if payload[2]['clear'] == 3:
                text = 'T-Spin Triple'
                add_anim = True

            elif payload[2]['clear'] == 2:
                text = 'T-Spin Double'
                add_anim = True

            if add_anim:
                new_anim = AnimationLarge(self, text, palette['orange-400'])

        if new_anim is not None:
            if isinstance(new_anim, AnimationLarge):
                self.animations = [anim for anim in self.animations if not isinstance(animation, AnimationLarge)]

            self.animations.append(new_anim)


    def update(self):
        self.screen.fill(palette['grey-900'])

        offset_x = self.width * 0.1 + (self.width * 0.4 - self.playfield_width) / 2
        offset_y = self.height * 0.12 + (self.height * 0.8 - self.playfield_height) / 2
        offset = (int(offset_x), int(offset_y))

        self.render_playfield(0, offset)

        if len(self.game) > 1:
            opponent_offset = (int(self.width - offset_x - self.playfield_width), int(offset_y))
            self.render_playfield(1, opponent_offset)

        else:
            self.render_statistics(self.game[0])

        display.flip()

        old_tick = self.animation_tick
        self.animation_tick = [0] * len(old_tick)

        return old_tick

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


    def render_playfield(self, player_id, offset):
        playfield_layer = self.playfield_layer[player_id]
        game = self.game[player_id]

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

        for key, anim in enumerate(self.animations[player_id]):
            anim.update()
            surface_rect = anim.surface.get_rect(center=(
                int(self.playfield_width / 2),
                int(self.playfield_height * 3 / 4)
            ))

            playfield_layer.blit(anim.surface, surface_rect)

            if anim.finished == True:
                self.animations[player_id][key] = None

        self.animations[player_id] = [anim for anim in self.animations[player_id] if anim is not None]

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

        self.screen.blit(self.names[player_id], (offset[0], offset[1] - self.names[player_id].get_rect().height - 10))


    def prepare_statistics(self):
        draw.rect(self.statistics_layer, palette['grey-850'], (0, 0, self.statistics_width, self.height))

        text_x = int(self.width / 3 - 90)
        text_y = 150
        text_gap = 40
        font = self.fonts['noto-bold']

        title_font = self.fonts['noto-black64']
        title_x = 50

        draw_text(self.statistics_layer, (title_x, 40), title_font, '공격력', align_right=False)
        draw_batch(self.statistics_layer, text_x, text_y, text_gap, font,
            ['분당 공격량', '줄당 공격량', '블럭당 공격량', '총 공격량'])

        text_y = 500
        draw_text(self.statistics_layer, (title_x, 390), title_font, '속도', align_right=False)
        draw_batch(self.statistics_layer, text_x, text_y, text_gap, font,
            ['블럭당 입력 수', '초당 입력 수', '분당 제거 줄 수', '초당 블럭 수'])

    def render_statistics(self, game):
        stat = game.statistics

        self.screen.blit(
            self.statistics_layer,
            (int(self.width * 2 / 3), 0)
        )

        text_x = self.width - 15
        text_y = 150
        text_gap = 40

        apm = get_stat(stat, 'damage', per_name='minute')
        apl = get_stat(stat, 'damage', per_name='clear')
        app = get_stat(stat, 'damage', per_name='drops')
        att = get_stat(stat, 'damage', is_overall=True)

        draw_batch(self.screen, text_x, 150, 40, self.fonts['noto-bold'],
            [apm, apl, app, att], color=palette['cyan-400'])

        kpt = get_stat(stat, 'kpt')
        kps = get_stat(stat, 'key', per_name='second')
        lpm = get_stat(stat, 'line', per_name='minute')
        pps = get_stat(stat, 'drops', per_name='second')

        draw_batch(self.screen, text_x, 500, 40, self.fonts['noto-bold'],
            [kpt, kps, lpm, pps], color=palette['cyan-400'])
