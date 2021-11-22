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
    context_folder = Node(type="folder", title="Contexto")
    intent_folder = Node(type="folder", title="Intenção")
    answer_folder = Node(type="folder", title="Respostas")

    create_context_folders_and_intent_subfolders(
        df=df, context_folder=context_folder, intent_folder=intent_folder
    )

    # create folder for intents without context
    contextless_subfolder = Node(title="sem contexto")
    intent_folder.add_child(contextless_subfolder)

    # create intent, answer and source nodes
    create_intent_and_answer_nodes(
        df=df,
        intent_folder=intent_folder,
        answer_folder=answer_folder,
        contextless_subfolder=contextless_subfolder,
        confidence=confidence,
    )

    # create anything_else nodes
    create_anything_else_nodes(intent_folder=intent_folder, answer_folder=answer_folder)

    return context_folder.to_list() + intent_folder.to_list() + answer_folder.to_list()


def create_context_folders_and_intent_subfolders(
    df: pd.DataFrame, intent_folder: Node, context_folder: Node
):
    all_tags = df["rótulos"].drop_duplicates().to_list()
    all_contexts = get_contexts(all_tags)
    for context in all_contexts:
        intent_subfolder = Node(
            title=context,
            conditions=f"$contexto:({context})",
            next_step={"behavior": "skip_user_input"},
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
        )
        context_folder.add_child(context_node)


def create_intent_and_answer_nodes(
    df: pd.DataFrame,
    intent_folder: Node,
    answer_folder: Node,
    contextless_subfolder: Node,
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
        )

        try:
            intent_subfolder = next(
                child for child in intent_folder.children if child.title in node_contexts
            )
            intent_subfolder.add_child(intent_node)
        except StopIteration:
            contextless_subfolder.add_child(intent_node)


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


def create_anything_else_nodes(intent_folder: Node, answer_folder: Node):
    first_answer_node = answer_folder.children[0]
    for subfolder in intent_folder.children:
        anything_else_node = Node(
            title="Antyhing else",
            conditions="anything_else",
            next_step={
                "behavior": "jump_to",
                "selector": "body",
                "dialog_node": first_answer_node.dialog_node,
            },
        )
        subfolder.add_child(anything_else_node)

    anything_else_node = Node(
        title="Antyhing else",
        conditions="anything_else",
        output={
            "generic": [
                {
                    "values": [
                        {
                            "text": "Não entendi ou não tenho essa resposta, pode reformular?"
                        }
                    ],
                    "response_type": "text",
                    "selection_policy": "sequential",
                }
            ]
        },
    )
    answer_folder.add_child(anything_else_node)


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
