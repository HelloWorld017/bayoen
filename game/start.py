from game import Tetris, Controller, Visualizer
from pygame import display, event, locals as pg_locals, time

import pygame
import sys

def start_game(is_opponent=False):
    pygame.init()

    game = Tetris()

    game.start_game()

    if is_opponent:
        opponent = Tetris(name='Opponent')
        game.connect_opponent(opponent)
        opponent.start_game()
        opponent.connect_opponent(game)

    screen = display.set_mode((1280, 720), pg_locals.DOUBLEBUF)
    vis = Visualizer(game, screen)
    display.set_caption('NenwTris')

    clock = time.Clock()

    key_mapping = {
        pg_locals.K_LEFT: Controller.key_left,
        pg_locals.K_RIGHT: Controller.key_right,
        pg_locals.K_x: Controller.key_spin_cw,
        pg_locals.K_z: Controller.key_spin_ccw,
        pg_locals.K_c: Controller.key_hold,
        pg_locals.K_DOWN: Controller.key_softdrop,
        pg_locals.K_SPACE: Controller.key_harddrop
    }

    game_delay = 0
    opponent_delay = 0
    events = []

    def handle_event(ev):
        if ev.type == pg_locals.QUIT:
            pygame.quit()
            sys.exit()

        elif ev.type == pg_locals.KEYDOWN:
            if ev.key in key_mapping:
                if not game_paused:
                    game.controller.keydown(key_mapping[ev.key])
                else:
                    events.append(ev)

        elif ev.type == pg_locals.KEYUP:
            if ev.key in key_mapping:
                if not game_paused:
                    game.controller.keyup(key_mapping[ev.key])

                else:
                    events.append(ev)

    while True:
        game_paused = game_delay > 0

        for ev in event.get():
            handle_event(ev)

        for i in range(len(events)):
            handle_event(events.pop(0))

        if game_delay <= 0:
            game.update()

        else:
            game_delay -= 1

        if is_opponent:
            if opponent_delay <= 0:
                opponent.update()

            else:
                opponent_delay -= 1

            game_delay_delta, opponent_delay_delta = vis.update()
            opponent_delay += opponent_delay_delta

        else:
            game_delay_delta,  = vis.update()

        game_delay += game_delay_delta

        clock.tick(60)
