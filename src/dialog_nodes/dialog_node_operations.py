# Filter-MSMARCO
# @File:   dialog_node_operations.py
# @Time:   20/11/2021
# @Author: Gabriel O.

import ast
import uuid
from typing import List, Tuple

import pandas as pd

from src.dialog_nodes.get_title import get_title
from src.utils.list_dict_operations import (
    remove_nans,
    drop_duplicates,
    drop_empty,
)
from src.utils.list_dict_operations import unzip
from src.utils.sanitize import sanitize


def get_dialog_nodes(df: pd.DataFrame, confidence) -> List[dict]:
    """
    For each question in the spreadsheet, creates 3 dialog nodes:
    - the first one detects the tag and sets the context, then jumps to the second one;
    - the second one detects the context, modifier, noun and recipient, then jumps to
        the third one;
    - the third one returns the answer.
    In total, there are 3 lists of nodes, called, respectively: tag nodes, context nodes
    and answer nodes. They are cancatenated in this order, and thus evaluated with this
    priority as well.
    This model ensures that, if the user's input contains a tag, it will override the
    previous context before evaluating it. Else, it will skip over the "tag" nodes to
    the "context" nodes, where, if the context was set previously, it will correctly
    identify intent. Lastly, if there was no context but also no tag, it will attempt
    to evaluate intentions directly.
    """
    records = df.to_dict(orient="records")

    tag_folder = create_folder_node("Rótulos")
    context_folder = create_folder_node("Contextos")
    answer_folder = create_folder_node("Respostas")

    all_nodes = [
        get_all_nodes(
            record,
            confidence,
            tag_folder_id=tag_folder["dialog_node"],
            context_folder_id=context_folder["dialog_node"],
            answer_folder_id=answer_folder["dialog_node"],
        )
        for record in records
    ]
    tag_nodes, context_nodes, answer_nodes = unzip(all_nodes)

    tag_nodes = drop_empty(tag_nodes)
    context_nodes = drop_empty(context_nodes)
    answer_nodes = drop_empty(tag_nodes)

    tag_nodes.sort(key=lambda x: x["intent"])
    context_nodes.sort(key=lambda x: x["intent"])
    answer_nodes.sort(key=lambda x: x["intent"])

    return [
        tag_folder,
        *tag_nodes,
        context_folder,
        *context_nodes,
        answer_folder,
        *answer_nodes,
    ]


def create_folder_node(title: str) -> dict:
    return {
        "type": "folder",
        "title": title,
        "dialog_node": f"node_{uuid.uuid4().hex[:16]}",
    }


def get_all_nodes(
    record: dict,
    confidence: float,
    tag_folder_id: str,
    context_folder_id: str,
    answer_folder_id: str,
) -> Tuple[dict, dict, dict]:
    """Returns the tag, context and answer nodes for a record."""
    context_node_id = f"node_{uuid.uuid4().hex[:16]}"
    answer_node_id = f"node_{uuid.uuid4().hex[:16]}"

    return (
        get_tag_node(record, next_node_id=context_node_id, parent_node_id=tag_folder_id),
        get_context_node(
            record,
            self_id=context_node_id,
            next_node_id=answer_node_id,
            parent_node_id=context_folder_id,
        ),
        get_answer_node(
            record,
            self_id=answer_node_id,
            confidence=confidence,
            parent_node_id=answer_folder_id,
        ),
    )


def get_tag_node(record: dict, next_node_id: str, parent_node_id: str) -> dict:
    """
    Nodes which detect tags, set the context accordingly and redirect to 'context' nodes.
    """
    context = sanitize(record["rótulos"].replace("-", " "))

    if not context:
        return {}

    return {
        "type": "standard",
        "context": {"contexto": context},
        "conditions": f"rótulos:({record['rótulos']})",
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
    record: dict, self_id: str, next_node_id: str, parent_node_id: str
) -> dict:
    """
    Nodes which detect intent based on context, modifier, noun and recipient
    then redirect to the correct 'answer' nodes.
    """
    return {
        "type": "standard",
        "conditions": get_full_condition(record),
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
    record: dict, self_id: str, parent_node_id: str, confidence: float = None
) -> dict:
    """
    Nodes which either detect the intent directly or are redirected to and provide
    the answer.
    """
    return {
        "type": "standard",
        "title": get_title(record),
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


def get_full_condition(js: dict) -> str:
    modifier = js["modificador"].replace("-", " ")
    noun = js["substantivo"].replace("-", " ")
    recipient = js["recipiente"].replace("-", " ")
    tags = js["rótulos"].replace("-", " ").split("_")
    tags += [js["rótulos"].replace("-", " ")]
    tags = drop_duplicates(tags)
    contexts = get_contexts(tags)

    base_condition = get_base_condition(modifier, noun, recipient)

    if not contexts:
        return base_condition

    conditions = [f"${contexto} &&" + base_condition for contexto in contexts]
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
