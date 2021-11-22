# Filter-MSMARCO
# @File:   Node.py
# @Time:   21/11/2021
# @Author: Gabriel O.

import uuid
from dataclasses import dataclass
from typing import Dict

from src.utils.list_dict_operations import drop_empty


@dataclass
class Node:
    type: str = "standard"
    title: str = None
    output: Dict = None
    context: Dict = None
    conditions: str = None
    dialog_node: str = f"node_{uuid.uuid4().hex[:16]}"
    parent: str = None
    next_step: Dict[str, str] = None
    fonte: str = None
    intent: str = None
    modificador: str = None
    substantivo: str = None
    recipiente: str = None

    def to_dict(self):
        return drop_empty(self.__dict__)
