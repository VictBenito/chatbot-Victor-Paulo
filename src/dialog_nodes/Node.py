# Filter-MSMARCO
# @File:   Node.py
# @Time:   21/11/2021
# @Author: Gabriel O.

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Dict, List

from src.utils.list_dict_operations import drop_empty
from src.utils.sanitize import sanitize


@dataclass
class Node:
    type: str = "standard"
    title: str = None
    conditions: str = None
    context: Dict = None
    output: Dict = None
    dialog_node: str = field(
        default_factory=lambda: f"node_{uuid.uuid4().hex[:16]}", init=False
    )
    parent: str = None
    previous_sibling: str = None
    next_step: Dict[str, str] = None
    fonte: str = None
    intent: str = None
    modificador: str = None
    substantivo: str = None
    recipiente: str = None
    rotulos: str = None
    children: List["Node"] = field(default_factory=list, init=False)

    def add_child(self, node: Node):
        node.parent = self.dialog_node
        self.children.append(node)

    def to_list(self) -> List[NodeDict]:
        """
        Returns this node and its children as a list of dicts.

        First, sorts the children. The priority of the sort key is higher on later
        sorts and 'zzzzz' is used to ensure that empty values go last without needing
        to reverse the sorts.

        Then, assembles a list, converting itself to a dict and calling to_list()
        recursively on children.
        """
        if len(self.children) > 1:
            self.sort(key=lambda x: sanitize(x.recipiente or "zzzzz"))
            self.sort(key=lambda x: sanitize(x.substantivo or "zzzzz"))
            self.sort(key=lambda x: sanitize(x.modificador or "zzzzz"))
            self.sort(key=lambda x: sanitize(x.rotulos or ""))
            self.apply_previous_siblings()

        out = [self.to_dict()]
        for node in self.children:
            out += node.to_list()
        return out

    def to_dict(self) -> NodeDict:
        return drop_empty(self.__dict__)

    def sort(self, *args, **kwargs):
        self.children.sort(*args, **kwargs)
        for i, child in enumerate(self.children):
            child.sort(*args, **kwargs)

    def apply_previous_siblings(self):
        for i, node in enumerate(self.children):
            if i == 0:
                continue
            node.previous_sibling = self.children[i - 1].dialog_node


NodeDict = Node.__annotations__
