# Filter-MSMARCO
# @File:   Folder.py
# @Time:   21/11/2021
# @Author: Gabriel O.

from typing import List

from src.dialog_nodes.Node import Node


class Folder:
    def __init__(self, name: str):
        self.node = Node(title=name)
        self.id = self.node.dialog_node
        self.nodes: List[Node] = []

    def add(self, node: Node):
        node.parent = self.id
        self.nodes.append(node)

    def to_list(self):
        return [node.to_dict() for node in self.nodes]
