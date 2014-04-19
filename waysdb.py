import pickle


def store_graph(ways, dbfilename):
    with open(dbfilename, 'wb') as sink:
        pickle.dump(ways, sink)


def load_graph(dbfilename):
    with open(dbfilename, 'rb') as source:
        return pickle.load(source)
