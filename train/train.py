from train import TetrisNet, TetrisNetAgent
from train.session import SessionTetris, SessionVisualize

def start_train_tetris(configs={}, saved_path=None):
    network = TetrisNet(configs)

    if saved_path is not None:
        network.load_model(saved_path)

    else:
        network.generate_model()

    agents = []
    threads = []

    for session_num in range(network.configs['sessions']):
        sess = SessionTetris()
        agent = TetrisNetAgent(sess, network)
        agents.append(agent)

    if networks.configs['vis_session']:
        sess = SessionVisualize()
        agent = TetrisNetAgent(sess, network)
        agents.append(agent)

    for agent in agents:
        thread = Thread(target=agent.run, args=(agent))
        thread.daemon = True
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()
