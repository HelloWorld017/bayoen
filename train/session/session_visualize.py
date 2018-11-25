from pygame import display, event, locals as pg_locals
from time import sleep
from train.session import SessionTetris

class SessionVisualize(SessionTetris):
    def __init__(self):
        super().__init__()

        screen = display.set_mode((1280, 720), pg_locals.DOUBLEBUF)
        self.vis = Visualizer(self.game, screen)

    def update(self):
        super().update()
        self.vis.update()

        for ev in event.get():
            if ev.type == pg_locals.QUIT:
                pygame.quit()
                sys.exit()

        sleep(0.02)
        return self.game.finished
