# Filter-MSMARCO
# @File:   Node.py
# @Time:   21/11/2021
# @Author: Gabriel O.

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Dict, List

from src.utils.list_dict_operations import drop_empty


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
        if self.children:
            node.previous_sibling = self.children[-1].dialog_node
        self.children.append(node)

    def to_list(self) -> List[dict]:
        out = [self.to_dict()]
        for node in self.children:
            out += node.to_list()
        out.sort(key=lambda x: x.get("intent", ""))
        return out

    def to_dict(self) -> dict:
        return drop_empty(self.__dict__)
