from game import Controller
from threading import Thread
from train import TetrisNet, TetrisNetAgent
from train.session import SessionTetris, SessionVisualize

def start_train_tetris(configs={}, saved_path=None):
    network = TetrisNet(len(Controller.keys), configs)

    if saved_path is not None:
        network.load_model(saved_path)

    else:
        network.generate_model()

    # TODO multi-agent ?
    sess = SessionVisualize() if network.configs['visualize'] else SessionTetris()
    agent = TetrisNetAgent(sess, network)
    agent.run()
