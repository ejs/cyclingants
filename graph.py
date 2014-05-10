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
        return iter(self.node_links)

    def __getitem__(self, nodeid):
        return self.node_info[nodeid]

    def add_edge(self, fid, tid, info):
        if fid not in self.node_info or tid not in self.node_info:
            raise KeyError()
        self.node_links[fid][tid].append(info)

    def get_edges(self, fid=None, tid=None):
        if fid and fid not in self.node_info:
            raise KeyError()
        if tid and tid not in self.node_info:
            raise KeyError()
        if tid:
            return self.node_links[fid][tid]
        elif fid:
            return [(nid, e) for nid, es in self.node_links[fid].items() for e in es]
        else:
            return [(f, nid, e) for f in self for nid, es in self.node_links[f].items() for e in es]

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

    def transform(self, t_node=None, t_edge=None, t_id=None):
        t_id = t_id if t_id else lambda a: a
        t_node = t_node if t_node else lambda a: a
        t_edge = t_edge if t_edge else lambda a: a
        res = Graph()
        for n in self:
            res.set_node(t_id(n), t_node(self.get_node(n)))
        for n, nid, e in self.get_edges():
            res.add_edge(t_id(n), t_id(nid), t_edge(e))
        return res

    def connected_components(self):
        """ Use union find to check whole graph in linear time"""
        print(len(self.node_info))
        print(len(self.node_links))
        nodes = {nid:nid for nid in self}
        def find_parent(n):
            if nodes[n] != n:
                nodes[n] = find_parent(nodes[n])
            return nodes[n]
        for f, t, _ in self.get_edges():
            nodes[find_parent(f)] = find_parent(t)
        shape = Counter(find_parent(n) for n in nodes)
        return sum(1 for node, parent in nodes.items() if not node != parent)
