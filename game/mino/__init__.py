from .mino import Tile, Mino

jlstz_wallkick_table = {
    '01': (( 0,  0), (-1,  0), (-1,  1), ( 0, -2), (-1, -2)),
    '10': (( 0,  0), ( 1,  0), ( 1, -1), ( 0,  2), ( 1,  2)),

    '12': (( 0,  0), ( 1,  0), ( 1, -1), ( 0,  2), ( 1,  2)),
    '21': (( 0,  0), (-1,  0), (-1,  1), ( 0, -2), (-1, -2)),

    '23': (( 0,  0), ( 1,  0), ( 1,  1), ( 0, -2), ( 1, -2)),
    '32': (( 0,  0), (-1,  0), (-1, -1), ( 0,  2), (-1,  2)),

    '30': (( 0,  0), (-1,  0), (-1, -1), ( 0,  2), (-1,  2)),
    '03': (( 0,  0), ( 1,  0), ( 1,  1), ( 0, -2), ( 1, -2))
}

class MinoL(Mino):
    shape = (
        (1, 0, 0),
        (2, 3, 4),
        (0, 0, 0)
    )
    name = 'l'
    view_yoffset = 0.5
    srs_table = jlstz_wallkick_table
    tiles = {
        1: (0, 2, 0),
        2: (0, 3, 0),
        3: (1, 3, 0),
        4: (2, 3, 0)
    }

class MinoJ(Mino):
    shape = (
        (0, 0, 1),
        (4, 3, 2),
        (0, 0, 0)
    )
    name = 'j'
    view_yoffset = 0.5
    srs_table = jlstz_wallkick_table
    tiles = {
        1: (0, 1, 180),
        2: (0, 0, 180),
        3: (1, 0, 180),
        4: (2, 0, 180)
    }

class MinoS(Mino):
    shape = (
        (0, 3, 4),
        (1, 2, 0),
        (0, 0, 0)
    )
    name = 's'
    view_yoffset = 0.5
    srs_table = jlstz_wallkick_table
    tiles = {
        1: (5, 3, 0),
        2: (6, 3, 0),
        3: (6, 2, 0),
        4: (7, 2, 0)
    }

class MinoZ(Mino):
    shape = (
        (1, 2, 0),
        (0, 3, 4),
        (0, 0, 0)
    )
    name = 'z'
    view_yoffset = 0.5
    srs_table = jlstz_wallkick_table
    tiles = {
        1: (4, 0, 0),
        2: (5, 0, 0),
        3: (5, 1, 0),
        4: (6, 1, 0)
    }

class MinoT(Mino):
    shape = (
        (0, 3, 0),
        (1, 2, 4),
        (0, 0, 0)
    )
    name = 't'
    view_yoffset = 0.5
    srs_table = jlstz_wallkick_table
    tiles = {
        1: (4, 1, 270),
        2: (4, 2, 270),
        3: (5, 2, 270),
        4: (4, 3, 270)
    }

class MinoO(Mino):
    shape = (
        (0, 0, 0, 0),
        (0, 1, 2, 0),
        (0, 4, 3, 0),
        (0, 0, 0, 0)
    )
    name = 'o'
    tiles = {
        1: (1, 1, 0),
        2: (2, 1, 0),
        3: (2, 2, 0),
        4: (1, 2, 0)
    }

class MinoI(Mino):
    shape = (
        (0, 0, 0, 0),
        (1, 2, 3, 4),
        (0, 0, 0, 0),
        (0, 0, 0, 0)
    )
    
    view_yoffset = 0.5

    srs_table = {
        '01': (( 0,  0), (-2,  0), ( 1,  0), (-2, -1), ( 1,  2)),
        '10': (( 0,  0), ( 2,  0), (-1,  0), ( 2,  1), (-1, -2)),

        '12': (( 0,  0), (-1,  0), ( 1,  0), (-2, -1), ( 1,  2)),
        '21': (( 0,  0), ( 1,  0), (-1,  0), ( 2,  1), (-1, -2)),

        '23': (( 0,  0), ( 2,  0), (-1,  0), ( 2,  1), (-1, -2)),
        '32': (( 0,  0), (-2,  0), ( 1,  0), (-2, -1), ( 1,  2)),

        '30': (( 0,  0), ( 1,  0), (-2,  0), ( 1, -2), (-2,  1)),
        '03': (( 0,  0), (-1,  0), ( 2,  0), (-1,  2), ( 2, -1))
    }

    name = 'i'
    tiles = {
        1: (3, 0, 270),
        2: (3, 1, 270),
        3: (3, 2, 270),
        4: (3, 3, 270)
    }

class MinoGarbage(Mino):
    shape = ((1, ), )
    name = 'garbage'
    tiles = {
        1: (6, 0, 0)
    }


minos = [MinoO, MinoT, MinoJ, MinoL, MinoS, MinoZ, MinoI]
minos_all = minos + [MinoGarbage]
mino_by_name = {mino.name: mino for mino in minos}

def get_mino(name):
    return mino_by_name.get(name)
