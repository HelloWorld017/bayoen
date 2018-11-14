from .mino import Mino

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
        (1, 1, 1),
        (0, 0, 0)
    )
    name = 'l'
    srs_table = jlstz_wallkick_table
    color = 'blue-400'

class MinoJ(Mino):
    shape = (
        (0, 0, 1),
        (1, 1, 1),
        (0, 0, 0)
    )
    name = 'j'
    srs_table = jlstz_wallkick_table
    color = 'orange-400'

class MinoS(Mino):
    shape = (
        (0, 1, 1),
        (1, 1, 0),
        (0, 0, 0)
    )
    name = 's'
    srs_table = jlstz_wallkick_table
    color = 'green-400'

class MinoZ(Mino):
    shape = (
        (1, 1, 0),
        (0, 1, 1),
        (0, 0, 0)
    )
    name = 'z'
    srs_table = jlstz_wallkick_table
    color = 'red-400'

class MinoT(Mino):
    shape = (
        (0, 1, 0),
        (1, 1, 1),
        (0, 0, 0)
    )
    name = 't'
    srs_table = jlstz_wallkick_table
    color = 'purple-400'

class MinoO(Mino):
    shape = (
        (0, 0, 0, 0),
        (0, 1, 1, 0),
        (0, 1, 1, 0),
        (0, 0, 0, 0)
    )
    name = 'o'
    color = 'yellow-400'

class MinoI(Mino):
    shape = (
        (0, 0, 0, 0),
        (1, 1, 1, 1),
        (0, 0, 0, 0),
        (0, 0, 0, 0)
    )

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
    color = 'cyan-600'

class MinoGarbage(Mino):
    shape = ((0, ), )
    name = 'garbage'
    color = 'grey-700'

minos = [MinoO, MinoT, MinoJ, MinoL, MinoS, MinoZ, MinoI]
mino_by_name = {mino.name: mino for mino in minos}

def get_mino(name):
    return mino_by_name.get(name)
