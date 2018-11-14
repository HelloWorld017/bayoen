from game import Tetris, Controller
from pygame import display, event, locals as pg_locals, time

import pygame
import sys

def start_game():
    pygame.init()

    game = Tetris()
    game.start_game()

    screen = display.set_mode((1280, 720), pg_locals.DOUBLEBUF)
    display.set_caption('NenwTris')

    clock = time.Clock()

    game.visualize(screen)

    key_mapping = {
        pg_locals.K_LEFT: Controller.key_left,
        pg_locals.K_RIGHT: Controller.key_right,
        pg_locals.K_x: Controller.key_spin_cw,
        pg_locals.K_z: Controller.key_spin_ccw,
        pg_locals.K_c: Controller.key_hold,
        pg_locals.K_DOWN: Controller.key_softdrop,
        pg_locals.K_SPACE: Controller.key_harddrop
    }

    while True:
        for ev in event.get():
            if ev.type == pg_locals.QUIT:
                pygame.quit()
                sys.exit()

            elif ev.type == pg_locals.KEYDOWN:
                if ev.key in key_mapping:
                    game.controller.keydown(key_mapping[ev.key])

            elif ev.type == pg_locals.KEYUP:
                if ev.key in key_mapping:
                    game.controller.keyup(key_mapping[ev.key])

        game.update()
        clock.tick(60)
