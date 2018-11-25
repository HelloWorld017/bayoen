from argparse import ArgumentParser
from game.start import start_game
from train import start_train_tetris
from os import path

import os
import sys


if __name__ == '__main__':
    # Directory Creation
    def check_and_create_dir(dir_name):
        if not path.isdir(dir_name):
            os.mkdir(dir_name)

    check_and_create_dir("./train/models/")
    check_and_create_dir("./train/output/")

    # Argument Parsing
    parser = ArgumentParser(
        prog='bayoen',
        description='Bayoen to all your Tetris opponents!'
    )
    sub_parser = parser.add_subparsers(help='Commands')

    # Game sub commands
    game_parser = sub_parser.add_parser('game', help='Start a "Puyo Puyo Tetris"-like tetris game.')
    game_parser.set_defaults(which='game')


    # Train sub commands
    train_parser = sub_parser.add_parser('train', help='Start training Tetris Net / Bayoen Net')
    train_parser.set_defaults(which='train')


    # Starting Program
    args = parser.parse_args()
    if 'which' not in args:
        parser.print_help()
        sys.exit(2)

    if args.which == 'game':
        start_game()

    elif args.which == 'train':
        start_train_tetris()
