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
    output: Dict = None
    context: Dict = None
    conditions: str = None
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
        out = [self.to_dict()]
        for node in self.children:
            out += node.to_list()
        # the priority of the sort key is higher on later sorts
        # 'zzzzz' is used to ensure that empty values go last without needing to reverse
        out.sort(key=lambda x: sanitize(x.get("recipiente", "zzzzz")))
        out.sort(key=lambda x: sanitize(x.get("substantivo", "zzzzz")))
        out.sort(key=lambda x: sanitize(x.get("modificador", "zzzzz")))
        out.sort(key=lambda x: sanitize(x.get("rotulos", "")))
        out = self.apply_previous_siblings(out)
        return out

    def to_dict(self) -> NodeDict:
        return drop_empty(self.__dict__)

    @staticmethod
    def apply_previous_siblings(nodes: List[NodeDict]) -> List[NodeDict]:
        for i, node in enumerate(nodes):
            if i == 0:
                continue
            node["previous_sibling"] = nodes[i - 1]["dialog_node"]
        return nodes


NodeDict = Node.__annotations__
