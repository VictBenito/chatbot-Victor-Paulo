# Filter-MSMARCO
# @File:   dialog_node_operations.py
# @Time:   20/11/2021
# @Author: Gabriel O.

import ast
from typing import List, Mapping

import pandas as pd

from src.dialog_nodes.Node import Node
from src.dialog_nodes.get_title import get_contexts, get_title
from src.utils.list_dict_operations import (
    remove_nans,
    drop_duplicates,
)


def get_dialog_nodes(df: pd.DataFrame, confidence: float = None) -> List[dict]:
    """
    Extracts dialog nodes from the spreadsheet. They serve the following purposes:
    1. Detect and set context
    2. Detect intent via modifier, noun and recipient
        a. without context
        b. with context
    3. Detect intent directly and give the answer
    They are grouped, respectively, in the folders: Context, Contextless-intent, Intent
    and Answers. This is also the order in which they are evaluated when the bot analyses
    user input.

    The flow of this model is like so:
    1. Check whether there is a context in the input, overriding the previous one if so;
    2. check if the input matches any of the contextless conditions;
    3. check if the input matches any of the conditions in the present context's folder;
    4. check if the input matches any of the intents directly.

    At any of the steps 2-4, if there is a match the bot will yield the correct answer.

    This ensures that direct intent matching by Watson is the last resort, for when other
    means of identification have failed.
    """
    context_folder = Node(
        title="Contexto", conditions="true", next_step={"behavior": "skip_user_input"}
    )
    contextless_intent_folder = Node(
        title="Sem contexto", conditions="true", next_step={"behavior": "skip_user_input"}
    )
    intent_folder = Node(
        title="Intenção", conditions="true", next_step={"behavior": "skip_user_input"}
    )
    answer_folder = Node(
        title="Respostas", conditions="true", next_step={"behavior": "skip_user_input"}
    )

    create_context_nodes_and_intent_subfolders(
        df=df, context_folder=context_folder, intent_folder=intent_folder
    )

    # create intent, answer and source nodes
    create_intent_and_answer_nodes(
        df=df,
        contextless_intent_folder=contextless_intent_folder,
        intent_folder=intent_folder,
        answer_folder=answer_folder,
        confidence=confidence,
    )

    # create anything_else nodes
    create_anything_else_nodes(
        context_folder=context_folder,
        contextless_intent_folder=contextless_intent_folder,
        intent_folder=intent_folder,
        answer_folder=answer_folder,
    )

    return (
        contextless_intent_folder.to_list()
        + context_folder.to_list()
        + intent_folder.to_list()
        + answer_folder.to_list()
    )


def create_context_nodes_and_intent_subfolders(
    df: pd.DataFrame, context_folder: Node, intent_folder: Node
):
    all_tags = df["rótulos"].drop_duplicates().to_list()
    all_contexts = get_contexts(all_tags)
    for context in all_contexts:
        intent_subfolder = Node(
            title=context.capitalize(),
            conditions=f"$contexto:({context})",
            next_step={"behavior": "skip_user_input"},
            rotulos="_".join(all_tags),
        )
        intent_folder.add_child(intent_subfolder)

        context_node = Node(
            context={"contexto": context},
            conditions=f"@rótulos:({context})",
            next_step={
                "behavior": "jump_to",
                "selector": "body",
                "dialog_node": intent_subfolder.dialog_node,
            },
            rotulos="_".join(all_tags),
        )
        context_folder.add_child(context_node)


def create_intent_and_answer_nodes(
    df: pd.DataFrame,
    contextless_intent_folder: Node,
    intent_folder: Node,
    answer_folder: Node,
    confidence: float,
):
    """
    For every record on the spreadsheet, create one node with the answer, one child of
    that node containing the source and a node which jumps to the one with the answer.
    """
    for i, record in df.iterrows():
        node_tags = record["rótulos"].split("_")
        node_contexts = get_contexts(node_tags)
        answer_node = Node(
            title=get_title(record.to_dict(), node_contexts),
            conditions=f"#{record['intent']} && intent.confidence > {confidence}",
            context={"other_counter": 0},
            output={
                "generic": [
                    {
                        "values": [{"text": record["resposta"]}],
                        "response_type": "text",
                        "selection_policy": "sequential",
                    }
                ]
            },
            fonte=record["fonte"],
            intent=record["intent"],
            modificador=record["modificador"],
            substantivo=record["substantivo"],
            recipiente=record["recipiente"],
            rotulos="_".join(node_contexts),
        )

        source_node = create_source_node(record)
        answer_node.add_child(source_node)
        answer_folder.add_child(answer_node)

        intent_node = Node(
            conditions=get_full_condition(record),
            next_step={
                "behavior": "jump_to",
                "selector": "body",
                "dialog_node": answer_node.dialog_node,
            },
            modificador=record["modificador"],
            substantivo=record["substantivo"],
            recipiente=record["recipiente"],
            rotulos="_".join(node_contexts),
        )

        try:
            intent_subfolder = next(
                child
                for child in intent_folder.children
                if child.title.lower() in node_contexts
            )
            intent_subfolder.add_child(intent_node)
        except StopIteration:
            contextless_intent_folder.add_child(intent_node)


def create_source_node(record: pd.Series):
    fontes = record["fonte"].split("--")
    fontes = drop_duplicates(fontes)
    if len(fontes) > 1:
        answer = "As fontes dessa resposta são: " + ", ".join(fontes)
    elif len(fontes) > 0:
        answer = "A fonte dessa resposta é: " + ", ".join(fontes)
    else:
        answer = "Desculpe, não tenho uma fonte específica para essa resposta."
    return Node(
        title="Fonte",
        conditions="#fonte",
        output={
            "generic": [
                {
                    "values": [{"text": answer}],
                    "response_type": "text",
                    "selection_policy": "sequential",
                }
            ]
        },
    )


def create_anything_else_nodes(
    context_folder: Node,
    contextless_intent_folder: Node,
    intent_folder: Node,
    answer_folder: Node,
):
    """
    Creates the following anything_else nodes:
    1. one in the contextless intent folder, pointing to the context folder
    2. one in the context folder, pointing to the intent folder
    3. one in the intent folder, pointing to the answer folder
    4. one for each intent subfolder, pointing to the intent anything_else node
    5. one in the answer folder, which will later point to the root anything_else folder
        (this is done in the NodeOrganizer, since the root anything_else folder is made
        in the web interface)
    """
    # 1st type
    contextless_intent_anything_else = create_anything_else_node(
        context_folder.dialog_node
    )
    contextless_intent_folder.add_child(contextless_intent_anything_else)

    # 2nd type
    context_anything_else = create_anything_else_node(intent_folder.dialog_node)
    context_folder.add_child(context_anything_else)

    # 3rd type
    intent_anything_else = create_anything_else_node(answer_folder.dialog_node)
    intent_folder.add_child(intent_anything_else)

    # 4th type
    for i, subfolder in enumerate(intent_folder.children):
        if subfolder.conditions == "anything_else":
            continue
        subfolder_anything_else = create_anything_else_node(
            intent_anything_else.dialog_node
        )
        subfolder.add_child(subfolder_anything_else)

    # 5th type
    answer_anything_else = create_anything_else_node("")
    answer_folder.add_child(answer_anything_else)


def create_anything_else_node(jump_to: str) -> Node:
    return Node(
        title="Anything else",
        conditions="anything_else",
        next_step={
            "behavior": "jump_to",
            "selector": "body",
            "dialog_node": jump_to,
        },
        rotulos="zzzzz",
    )


def get_full_condition(js: Mapping) -> str:
    modifier = js["modificador"].replace("-", " ")
    noun = js["substantivo"].replace("-", " ")
    recipient = js["recipiente"].replace("-", " ")

    return get_base_condition(modifier, noun, recipient)


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
    list_of_dicts = [eval_column(d, "context") for d in list_of_dicts]
    list_of_dicts = [eval_column(d, "next_step") for d in list_of_dicts]
    return list_of_dicts


def eval_column(d: dict, col: str):
    if col not in d:
        return d
    value = d[col]
    if isinstance(value, str):
        evaluated = ast.literal_eval(value)
        d[col] = evaluated
    return d
