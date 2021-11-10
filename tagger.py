import abc
import json
import os
from collections import defaultdict

from transaction import Transaction


class Tag(object):
    def __init__(self, name, identifier, parent_id=None, income=True, color="#000000", default=False):
        self._name = name
        self._parent_id = parent_id
        self._identifier = identifier
        self._color = color
        self._income = income
        self._default = default

    def __repr__(self):
        return "Tag(id={}, name={})".format(self._identifier, self._name)

    @property
    def name(self):
        return self._name

    @property
    def parent_id(self):
        return self._parent_id

    @property
    def identifier(self):
        return self._identifier

    @property
    def color(self):
        return self._color

    @property
    def income(self):
        return self._income

    @property
    def default(self):
        return self._default


class TagTree(object):
    def __init__(self, path):
        self._tags, self._roots, self._tree = self.load_tree(path)

    def __getitem__(self, item):
        return self._tags[item]

    def __len__(self):
        return len(self._tags)

    @classmethod
    def load_tree(cls, path):
        with open(os.path.join(path, "tags.json"), "r", encoding="utf8") as file:
            loaded = json.load(file)
            tags = defaultdict()
            id_tree = defaultdict(set)
            roots = set()
            for tag in loaded:
                identifier = tag["categoryId"]
                tag = Tag(
                    name=tag["description"],
                    identifier=identifier,
                    parent_id=tag.get("parentId"),
                    color=tag["color"],
                    income=tag["income"],
                    default=tag["default"]
                )
                if tag.parent_id is not None:
                    id_tree[tag.parent_id].add(tag.identifier)
                else:
                    roots.add(tag.identifier)
                tags[identifier] = tag
            return tags, roots, id_tree

    def pprint(self):
        for root in self._roots:
            self._print_children(root)
            print()

    def _print_children(self, node, level=0):
        tag = self._tags[node]
        print(" " * (level * 2) + "- {} [{}]".format(tag.name, "+" if tag.income else "-"), end="")
        if len(self._tree[node]) > 0:
            print(":")
            for child in self._tree[node]:
                self._print_children(child, level + 1)
        else:
            print()


# class TransactionClassifier(metaclass=abc.ABCMeta):
#     @abc.abstractmethod
#     def tag(self, t: Transaction):


if __name__ == "__main__":
    tree = TagTree("./data")
    tree.pprint()