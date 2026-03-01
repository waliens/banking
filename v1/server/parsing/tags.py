import json
import os
from collections import defaultdict


class Tag(object):
  def __init__(self, name, identifier, parent_id=None, color="#000000", icon="tag"):
    self._name = name
    self._parent_id = parent_id
    self._identifier = identifier
    self._color = color
    self._icon = icon

  def __repr__(self):
    return "Tag(id={}, name={})".format(self._identifier, self._name)

  @property
  def name(self):
    return self._name

  @property
  def parent_id(self):
    return self._parent_id

  @property 
  def id(self):
    return self.identifier
  
  @property
  def identifier(self):
    return self._identifier

  @property
  def color(self):
    return self._color

  @property
  def icon(self):
    return self._icon


class TagTree(object):
  def __init__(self, tags, roots, tree):
    self._tags, self._roots, self._tree = tags, roots, tree

  def __getitem__(self, item):
    return self._tags[item]

  def __contains__(self, item):
    return item in self._tags

  def tag_name(self, identifier):
    return self._tags[identifier].name

  def has_children(self, identifier):
    return identifier in self._tree

  def get_children(self, identifier):
    return list(self._tree.get(identifier, set()))
  
  @property
  def roots(self):
    return [self[_id] for _id in self._roots]

  def __len__(self):
    return len(self._tags)

  @classmethod
  def tree_from_file(cls, path="."):
    return TagTree(*cls.load_tree(path))

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
          icon=tag['icon']
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
    print(" " * (level * 2) + "- {} [{}]".format(tag.name), end="")
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
  tree = TagTree.tree_from_file()
  tree.pprint()