import pickle
import osm
from osm import RouteSection


def store_file(ways, dbfilename):
    with open(dbfilename, 'wb') as sink:
        pickle.dump(ways, sink)


def load_file(dbfilename):
    with open(dbfilename, 'rb') as source:
        return pickle.load(source)
