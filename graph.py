from collections import Counter, defaultdict


def bag():
    return defaultdict(list)


class Graph:
    def __init__(self):
        self.node_info = {}
        self.node_links = defaultdict(bag)

    def set_node(self, nid, info):
        self.node_info[nid] = info

    def get_node(self, nid):
        return self.node_info[nid]

    def del_node(self, nid):
        if nid in self.node_info:
            del self.node_info[nid]
        if nid in self.node_links:
            del self.node_links[nid]
        for edges in self.node_links.values():
            if nid in edges:
                del edges[nid]

    def __str__(self):
        return "Graph with {} nodes and {} edges".format(len(self), sum(len(self.get_edges(n)) for n in self))

    def __len__(self):
        return len(self.node_info)

    def __iter__(self):
        return iter(self.node_info)

    def add_edge(self, fid, tid, info):
        if fid not in self.node_info or tid not in self.node_info:
            raise KeyError()
        self.node_links[fid][tid].append(info)

    def get_edges(self, fid, tid=None):
        if fid not in self.node_info:
            raise KeyError()
        if tid and tid not in self.node_info:
            raise KeyError()
        if tid:
            return self.node_links[fid][tid]
        else:
            return [e for es in self.node_links[fid].values() for e in es]

    def clean(self):
        for n in list(self):
            if n not in self.node_links:
                if not any(self.get_edges(nd, n) for nd in list(self)):
                    self.del_node(n)

    def trim(self):
        # N.B. Handle nodes which are one directional e.g. a -> b -> c
        # currently b looks like it can be trimmed out
        while any(sum(len(b) for b in a.values()) == 1 for a in self.node_links.values()):
            # trim back all dead ends
            for nid in list(self.node_links):
                edges = self.get_edges(nid)
                if len(edges) == 1:
                    self.del_node(nid)
        self.clean()

    def compact(self, combiner=None):
        """ This take a function that expects to recieve
            a : the edge from A to the node about to be removed
            b : information about the node about to be removed
            c : the edge from the node about to be removed to B

            and returns the new edge A, B

            Currently assumes that edges in the road are always paired to make
            effectivly bi-directional links.
        """
        if not combiner:
            combiner = lambda a, n, b: a
        self.trim()
        flag = True
        while flag:
            flag = False
            for nid in list(self):
                nodes = list(self.node_links[nid])
                edges = [self.node_links[nid][n] for n in nodes]
                if [len(e) for e in edges] == [1, 1]:
                    flag = True
                    fid, tid = nodes
                    self.add_edge(fid, tid, combiner(self.get_edges(fid, nid)[0], self.get_node(nid), self.get_edges(nid, tid)[0]))
                    self.add_edge(tid, fid, combiner(self.get_edges(tid, nid)[0], self.get_node(nid), self.get_edges(fid, tid)[0]))
                    self.del_node(nid)

    def find_most_connected_nodes(self):
        most_connected, starting_points = 0, []
        for node in self:
            edges = self.get_edges(node)
            if len(edges) > most_connected:
                most_connected = len(edges)
                starting_points = [node]
            elif len(edges) == most_connected:
                starting_points.append(node)
        return sorted(starting_points)
