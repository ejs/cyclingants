import pickle
import osm
from osm import RouteSection


def store(ways, dbfilename):
    with open(dbfilename, 'wb') as sink:
        pickle.dump(ways, sink)


def load(dbfilename):
    with open(dbfilename, 'rb') as source:
        return pickle.load(source)
