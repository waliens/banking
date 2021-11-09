import json


class UnionFind(dict):
    """
    Values of this dict are either another key or a set of keys.
    If self[k1] -> k2, then self[k2] -> {k2, ..., k1, ...} and k1 (and k2) not in any other set of the dict
    """
    def union(self, k1, k2):
        repr1 = self.find_repr(k1)
        repr2 = self.find_repr(k2)

        if repr1 is not None and repr2 is not None:
            if repr1 == repr2:
                return repr1
            set2 = self[repr2]
            for k in self[repr2]:
                self[k] = repr1
            self[repr1] = self[repr1].union(set2)
            return repr1
        elif repr1 is None and repr2 is not None:
            self.add_elem(k1, repr2)
            return repr2
        elif repr1 is not None and repr2 is None:
            self.add_elem(k2, repr1)
            return repr1
        else:
            self.add_repres(k1)
            self.add_elem(k2, k1)
            return k1

    def same_comp(self, k1, k2):
        if k1 not in self or k2 not in self:
            return None, False
        if isinstance(self[k1], set):
            return k1, k2 in self[k1]
        elif isinstance(self[k2], set):
            return k2, k1 in self[k2]
        else:
            return self[k1], self[k1] == self[k2]

    def find_repr(self, k):
        if k in self:
            return k if isinstance(self[k], set) else self[k]
        return None

    def find_comp(self, k):
        if k in self:
            return self[k] if isinstance(self[k], set) else self[self[k]]
        return None

    def update_repr(self, k_rep, k_new):
        if k_rep == k_new:
            return
        key_updates = [k for k, v in self.items() if not isinstance(v, set) and v == k_rep]
        for key_u in key_updates:
            self[key_u] = k_new
        self[k_new] = self[k_rep]
        self[k_rep] = k_new
        self[k_new].add(k_rep)

    def representatives(self):
        return {k for k, v in self.items() if isinstance(v, set)}

    def add_repres(self, k):
        if k in self:
            raise KeyError("key '{}' already in union find".format(k))
        self[k] = {k}

    def add_elem(self, k, repres):
        if k in self and self[k] == repres:
            return
        elif k in self:
            raise KeyError("key '{}' already in union find".format(k))
        if repres not in self:
            raise KeyError("repres key '{}' not in union find".format(repres))
        self[k] = repres
        self[repres].add(k)

    @staticmethod
    def load_from_json(path):
        with open(path, "r", encoding="utf8") as file:
            loaded = json.load(file)
            md = UnionFind()
            for dct in loaded:
                k = dct["key"]
                v = dct["val"]
                t = dct["type"]

                k = k if isinstance(k, str) else tuple(k)

                if t == "key":
                    md[k] = v if isinstance(v, str) else tuple(v)
                else:
                    md[k] = set([a if isinstance(a, str) else tuple(a) for a in v])

            return md

    def save_to_json(self, path):
        with open(path, "w", encoding="utf8") as file:
            json.dump([{
                "key": k ,
                "val": (list(v) if isinstance(v, set) else v),
                "type": ("set" if isinstance(v, set) else "key")
            } for k, v in self.items()], file)