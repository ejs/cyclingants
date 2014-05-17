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
            edges.pop(nid, None)

    def __str__(self):
        return "Graph with {} nodes and {} edges".format(len(self), len(self.get_edges()))

    def __len__(self):
        return len(self.node_info)

    def __iter__(self):
        return iter(self.node_info)

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
        if tid and fid:
            return self.node_links[fid][tid]
        elif tid:
            return [(nid, e) for nid, es in self.node_links.items() for e in es[tid]]
        elif fid:
            return [(nid, e) for nid, es in self.node_links[fid].items() for e in es]
        else:
            return [(f, nid, e) for f in self for nid, es in self.node_links[f].items() for e in es]

    def remove_edges(self, fid, tid):
        try:
            del self.node_links[fid][tid]
        except KeyError:
            pass

    def remove_dead_ends(self):
        flag = False
        for node in list(self):
            if not self.node_links.get(node) or not self.get_edges(None, node):
                flag = True
                self.del_node(node)
        return flag

    def remove_fake_choices(self, combiner):
        flag = False
        for node in list(self):
            for to, edge in self.get_edges(node):
                options = set(n for n, _ in self.get_edges(to) if n != node)
                if len(options) == 0:
                    self.remove_edges(node, to)
                    flag = True
                elif len(options) == 1:
                    flag = True
                    for end, edge2 in self.get_edges(to):
                        if end != node:
                            self.add_edge(node, end, combiner(edge, self[to], edge2))
                    self.remove_edges(node, to)
        return flag

    def _spot_loop(self, start, step, *old):
        options = set(n for n, _ in self.get_edges(step) if n != start)
        if len(options) == 1:
            choice = options.pop()
            if choice in old:
                print("Loop found", old, start, step)
                return True
            return self._spot_loop(step, choice, start, *old)
        if 1 < len(options):
            return False
        return True

    def break_tight_loops(self):
        flag = False
        for node in list(self):
            for to in set(n for n, _ in self.get_edges(node)):
                options = set(n for n, _ in self.get_edges(to) if n != node)
                if len(options) == 1 and self._spot_loop(node, to):
                    self.remove_edges(node, to)
                    print("Removed Loop", node, to)
                    flag = True
        return flag

    def simplify(self, combiner=None):
        combiner = combiner if combiner else lambda a, b, c: a
        flag = True
        while flag:
            print("Cleaning", self)
            flag = False
            #flag = flag or self.remove_fake_choices(combiner)
            flag = flag or self.break_tight_loops()
            flag = flag or self.remove_dead_ends()
        print("Cleaned", self)

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
        nodes = {nid:nid for nid in self}
        def find_parent(n):
            if nodes[n] != n:
                nodes[n] = find_parent(nodes[n])
            return nodes[n]
        for f, t, _ in self.get_edges():
            nodes[find_parent(f)] = find_parent(t)
        shape = Counter(find_parent(n) for n in nodes)
        return sum(1 for node, parent in nodes.items() if not node != parent)
