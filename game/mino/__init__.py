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
    @property
    def shape(self):
        return (
            (1, 0, 0),
            (1, 1, 1),
            (0, 0, 0)
        )

    @property
    def srs_table(self):
        return jlstz_wallkick_table

    @property
    def color(self):
        return 'blue'

class MinoJ(Mino):
    @property
    def shape(self):
        return (
            (0, 0, 1),
            (1, 1, 1),
            (0, 0, 0)
        )

    @property
    def srs_table(self):
        return jlstz_wallkick_table

    @property
    def color(self):
        return 'orange'

class MinoS(Mino):
    @property
    def shape(self):
        return (
            (0, 1, 1),
            (1, 1, 0),
            (0, 0, 0)
        )

    @property
    def srs_table(self):
        return jlstz_wallkick_table

    @property
    def color(self):
        return 'green'

class MinoZ(Mino):
    @property
    def shape(self):
        return (
            (1, 1, 0),
            (0, 1, 1),
            (0, 0, 0)
        )

    @property
    def srs_table(self):
        return jlstz_wallkick_table

    @property
    def color(self):
        return 'red'

class MinoT(Mino):
    @property
    def shape(self):
        return (
            (0, 1, 0),
            (1, 1, 1),
            (0, 0, 0)
        )

    @property
    def srs_table(self):
        return jlstz_wallkick_table

    @property
    def color(self):
        return 'purple'

class MinoO(Mino):
    @property
    def shape(self):
        return (
            (0, 0, 0, 0),
            (0, 1, 1, 0),
            (0, 1, 1, 0),
            (0, 0, 0, 0)
        )

    @property
    def color(self):
        return 'yellow'

class MinoI(Mino):
    @property
    def shape(self):
        return (
            (0, 0, 0, 0),
            (1, 1, 1, 1),
            (0, 0, 0, 0),
            (0, 0, 0, 0)
        )

    @property
    def srs_table(self):
        return {
            '01': (( 0,  0), (-2,  0), ( 1,  0), (-2, -1), ( 1,  2)),
            '10': (( 0,  0), ( 2,  0), (-1,  0), ( 2,  1), (-1, -2)),

            '12': (( 0,  0), (-1,  0), ( 1,  0), (-2, -1), ( 1,  2)),
            '21': (( 0,  0), ( 1,  0), (-1,  0), ( 2,  1), (-1, -2)),

            '23': (( 0,  0), ( 2,  0), (-1,  0), ( 2,  1), (-1, -2)),
            '32': (( 0,  0), (-2,  0), ( 1,  0), (-2, -1), ( 1,  2)),

            '30': (( 0,  0), ( 1,  0), (-2,  0), ( 1, -2), (-2,  1)),
            '03': (( 0,  0), (-1,  0), ( 2,  0), (-1,  2), ( 2, -1))
        }

    @property
    def color(self):
        return 'cyan'
