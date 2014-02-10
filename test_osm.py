#! /usr/bin/python3
from collections import Counter
import xml.sax as sax
import osm
import unittest


class TestLoading(unittest.TestCase):
    def test_loading(self):
        osmhandler = osm.OSMHandler()
        parser = sax.make_parser()
        parser.setContentHandler(osmhandler)
        parser.parse('south-yorkshire-latest.osm')
        res = osmhandler.nodes, osmhandler.ways, osmhandler.graph
        self.assertEqual(len(res[0]), 1076738)
        self.assertEqual(len(res[1]), 10164)
        print("Node size", total_size(res[0]))
        print("Way size", total_size(res[1][:100]))
        print("Graph size", total_size(res[2]))
        print(Counter(len(b) for b in res[2].values()))
        print(max(sum(r.interest for r in w['nodes']) for w in res[1]))

    def test_loading_with_geograhic_restriction(self):
        pass


from sys import getsizeof, stderr
from itertools import chain
from collections import deque
try:
        from reprlib import repr
except ImportError:
        pass

def total_size(o, handlers={}, verbose=False):
    """ Returns the approximate memory footprint an object and all of its contents.

        Automatically finds the contents of the following builtin containers and
        their subclasses:  tuple, list, deque, dict, set and frozenset.
        To search other containers, add handlers to iterate over their contents:

        handlers = {SomeContainerClass: iter,
        OtherContainerClass: OtherContainerClass.get_elements}

    """
    dict_handler = lambda d: chain.from_iterable(d.items())
    all_handlers = {tuple: iter,
                    list: iter,
                    deque: iter,
                    dict: dict_handler,
                    set: iter,
                    frozenset: iter,
                    }
    all_handlers.update(handlers)     # user handlers take precedence
    seen = set()                      # track which object id's have already been seen
    default_size = getsizeof(0)       # estimate sizeof object without __sizeof__

    def sizeof(o):
        if id(o) in seen:       # do not double count the same object
            return 0
        seen.add(id(o))
        s = getsizeof(o, default_size)

        if verbose:
            print(s, type(o), repr(o), file=stderr)

        for typ, handler in all_handlers.items():
            if isinstance(o, typ):
                s += sum(map(sizeof, handler(o)))
                break
        return s

    return sizeof(o)

if __name__ == '__main__':
    unittest.main()
