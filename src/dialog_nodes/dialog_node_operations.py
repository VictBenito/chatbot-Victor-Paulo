# Filter-MSMARCO
# @File:   dialog_node_operations.py
# @Time:   20/11/2021
# @Author: Gabriel O.

import ast
import uuid
from typing import List, Tuple

import pandas as pd

from src.dialog_nodes.Folder import Folder
from src.dialog_nodes.Node import Node
from src.dialog_nodes.get_title import get_contexts, get_title
from src.utils.list_dict_operations import (
    remove_nans,
    drop_duplicates,
    drop_empty,
)
from src.utils.sanitize import sanitize


def get_dialog_nodes(df: pd.DataFrame, confidence) -> List[dict]:
    """
    Extracts dialog nodes from the spreadsheet. They serve the following purposes:
    1. Detect and set context
    2. Detect intent via modifier, noun and recipient
    3. Detect intent directly and give the answer
    They are grouped, respectively, in the folders: Context, Intent, Answers. This is
    also the order in which they are evaluated when the bot analyses user input.

    Inside the Intent folder, there is one folder for each possible context. Nodes from
    the first folder jump to the corresponding context's folder. Nodes inside those
    folders jump to nodes in the answers folder. There are also contextless nodes, which
    stay in the Intent folder and also jump to nodes with answers.

    This model ensures that, if the user's input contains a tag, it will override the
    previous context. If it doesn't, it will skip over the Context nodes to
    the Intent nodes, where it can identify intent. Lastly, if there was no previous
    context but also no tag in the input, it will attempt to evaluate intentions directly.

    Thus, direct intent matching by Watson is the last resort, for when other means of
    identification have failed.
    """
    records = df.to_dict(orient="records")
    tags = df["rótulos"].drop_duplicates().to_list()
    contexts = get_contexts(tags)

    context_folder = Node(type="folder", title="Contexto")
    intent_folder = Node(type="folder", title="Intenção")
    answer_folder = Node(type="folder", title="Respostas")

    for context in contexts:
        intent_subfolder = Node(
            conditions=f"$contexto:({context})",
        )
        intent_folder.add_child(intent_subfolder)

        context_node = Node(
            context={"contexto": context},
            conditions=f"rótulos:({context})",
            next_step={
                "behavior": "jump_to",
                "selector": "body",
                "dialog_node": intent_subfolder.dialog_node,
            },
        )
        context_folder.add_child(context_node)

    # context_nodes.sort(key=lambda x: x["intent"])
    # intent_nodes.sort(key=lambda x: x["intent"])
    # answer_nodes.sort(key=lambda x: x["intent"])

    return []


def get_all_nodes(
    record: dict,
    confidence: float,
    context_folder_id: str,
    intent_folder_id: str,
    answer_folder_id: str,
) -> Tuple[dict, dict, dict]:
    """Returns the tag, context and answer nodes for a record."""
    tags = record["rótulos"].replace("-", " ")
    context_node_id = f"node_{uuid.uuid4().hex[:16]}"
    answer_node_id = f"node_{uuid.uuid4().hex[:16]}"

    return (
        get_tag_node(
            record,
            parent_node_id=context_folder_id,
            next_node_id=context_node_id,
            tags=tags,
        ),
        get_context_node(
            record,
            parent_node_id=intent_folder_id,
            self_id=context_node_id,
            next_node_id=answer_node_id,
            tags=tags,
        ),
        get_answer_node(
            record,
            parent_node_id=answer_folder_id,
            self_id=answer_node_id,
            tags=tags,
            confidence=confidence,
        ),
    )


def get_tag_node(record: dict, parent_node_id: str, next_node_id: str, tags: str) -> dict:
    """
    Nodes which detect tags, set the context accordingly and redirect to 'context' nodes.
    """
    if not tags:
        return {}

    context = sanitize(tags)

    return {
        "type": "standard",
        "context": {"contexto": context},
        "conditions": f"rótulos:({context})",
        "dialog_node": f"node_{uuid.uuid4().hex[:16]}",
        "parent": parent_node_id,
        "next_step": {
            "behavior": "jump_to",
            "selector": "body",
            "dialog_node": next_node_id,
        },
        "intent": record["intent"],
        "modificador": record["modificador"],
        "substantivo": record["substantivo"],
        "recipiente": record["recipiente"],
    }


def get_context_node(
    record: dict, parent_node_id: str, self_id: str, next_node_id: str, tags: str
) -> dict:
    """
    Nodes which detect intent based on context, modifier, noun and recipient
    then redirect to the correct 'answer' nodes.
    """
    return {
        "type": "standard",
        "conditions": get_full_condition(record, tags),
        "dialog_node": self_id,
        "parent": parent_node_id,
        "next_step": {
            "behavior": "jump_to",
            "selector": "body",
            "dialog_node": next_node_id,
        },
        "intent": record["intent"],
        "modificador": record["modificador"],
        "substantivo": record["substantivo"],
        "recipiente": record["recipiente"],
    }


def get_answer_node(
    record: dict, parent_node_id: str, self_id: str, tags: str, confidence: float = None
) -> dict:
    """
    Nodes which either detect the intent directly or are redirected to and provide
    the answer.
    """
    contexts = get_contexts(tags.split("_"))

    return {
        "type": "standard",
        "title": get_title(record, contexts),
        "output": {
            "generic": [
                {
                    "values": [{"text": record["resposta"]}],
                    "response_type": "text",
                    "selection_policy": "sequential",
                }
            ]
        },
        "conditions": f"#{record['intent']} && intent.confidence > {confidence}",
        "dialog_node": self_id,
        "parent": parent_node_id,
        "fonte": record["fonte"],
        "intent": record["intent"],
        "modificador": record["modificador"],
        "substantivo": record["substantivo"],
        "recipiente": record["recipiente"],
    }


def get_contexts(tags: List[str]) -> List[str]:
    """
    Returns the contexts of a question based on its tags, considering
    there are tags which do not define context.
    """
    non_contextual_tags = [
        "fauna",
        "flora",
        "outras",
        "física",
        "turismo",
        "saúde",
        "geologia",
    ]
    return [
        context
        for context in tags
        if all(tag not in context for tag in non_contextual_tags)
    ]


def get_full_condition(js: dict, tags: str) -> str:
    modifier = js["modificador"].replace("-", " ")
    noun = js["substantivo"].replace("-", " ")
    recipient = js["recipiente"].replace("-", " ")
    tag_list = [tags, *(tags.split("_"))]
    tag_list = drop_duplicates(tag_list)
    contexts = get_contexts(tag_list)

    base_condition = get_base_condition(modifier, noun, recipient)

    if not contexts:
        return base_condition

    conditions = [f"${contexto} && " + base_condition for contexto in contexts]
    condition_string = " || ".join(conditions)
    return condition_string


def get_base_condition(modifier, noun, recipient) -> str:
    condition = f"@modificador:({modifier})"
    if noun:
        condition += f" && @substantivo:({noun})"
    if recipient:
        condition += f" && @recipiente:({recipient})"
    return condition


def convert_to_list(df: pd.DataFrame) -> List[dict]:
    list_of_dicts = df.to_dict(orient="records")
    list_of_dicts = [remove_nans(d) for d in list_of_dicts]
    list_of_dicts = [eval_context(d) for d in list_of_dicts]
    return list_of_dicts


def eval_context(d: dict):
    if "context" not in d:
        return d
    context = d["context"]
    if isinstance(context, str):
        evaluated = ast.literal_eval(context)
        d["context"] = evaluated
    return d
