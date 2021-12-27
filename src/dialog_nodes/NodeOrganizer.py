# Filter-MSMARCO
# @File:   NodeOrganizer.py
# @Time:   20/11/2021
# @Author: Gabriel O.

import json
import re
from typing import List

import numpy as np
import pandas as pd

from src.utils.list_dict_operations import drop_duplicates


class NodeOrganizer:
    """
    Assumes nodes have either been added via the interface (manual) or generated automatically
    by this script (generated). There are two special cases: the last node (anything_else),
    which was added via interface but must always be the last one, and the root node, where
    the dialog begins.
    """

    def __init__(self, nodes: List[dict]):
        self._df = pd.DataFrame(nodes)
        self._extract_intents()
        self.df_anything_else = pd.DataFrame()
        self.df_generated = pd.DataFrame()
        self.df_manual = pd.DataFrame()
        self.answers = pd.Series(dtype=object)
        self.root_anything_else = pd.Series(dtype=object)
        self._separate_nodes()

    def _extract_intents(self):
        self._df["intent"] = (
            self._df["conditions"].astype(str).apply(self._extract_intent)
        )

    @staticmethod
    def _extract_intent(conditions: str) -> str:
        search = re.search(r"#(\S+)", conditions)
        return search.group(1) if search else ""

    def _separate_nodes(self):
        """
        Separates the dataframe into manually added questions, auto-generated ones,
        the anything_else node and the root node.
        """
        self.root_anything_else = self._df.parent.isna() & (
            self._df.conditions == "anything_else"
        )
        self.df_anything_else = self._df[self.root_anything_else].copy()

        generated_nodes = (
            ~self._df.dialog_node.str.match(r"node_._") & ~self.root_anything_else
        )
        self.df_generated = self._df[generated_nodes].copy()

        manual_nodes = ~generated_nodes & ~self.root_anything_else
        self.df_manual = self._df[manual_nodes].copy()

        answers_node = self.df_generated.title == "Respostas"
        answers_id = self.df_generated.loc[answers_node, "dialog_node"].values[0]
        self.answers = self.df_generated.parent == answers_id

    def _build(self):
        """Updates the main dataframe to reflect changes in its subparts."""
        self._df = pd.concat(
            [
                self.df_manual,
                self.df_generated,
                self.df_anything_else,
            ],
            axis=0,
            ignore_index=True,
        )
        self._extract_intents()

    @property
    def df(self) -> pd.DataFrame:
        """Returns the main dataframe after building and dropping temporary columns."""
        self._build()
        out = self._df.drop(
            columns=[
                "fonte",
                "intent",
                "modificador",
                "substantivo",
                "recipiente",
                "children",
                "rotulos",
                "node_above",
            ],
            errors="ignore",
        )
        return out

    def run(self, intent_limit: int = 0):
        self.sort_nodes()
        self.limit_intents(intent_limit)
        self.set_contexts_node()
        self.set_help_node()
        self.fix_previous_siblings()
        self.apply_previous_siblings()
        self.point_to_anything_else_node()

    def sort_nodes(self):
        root_node = (
            self.df_manual.previous_sibling.isna()
            & self.df_manual.parent.isna()
            & self.df_manual.next_step.isna()
        )
        self.df_manual = self.sort_by_previous_siblings(self.df_manual, root_node)
        self._build()
        self._separate_nodes()
        print("Nodes sorted!")

    @staticmethod
    def sort_by_previous_siblings(df: pd.DataFrame, root: pd.Series):
        """
        Sorts the rows in a dataframe to reflect how the nodes appear on the interface.
        """
        previous_siblings = df.previous_sibling.to_list()
        parents = df.parent.to_list()
        df.loc[root, "order"] = 0

        curr = 1
        last_node = df[root].dialog_node.values[0]
        while df.order.hasnans:
            if last_node in parents:
                next_node = (df.parent == last_node) & (df.previous_sibling.isna())
            elif last_node in previous_siblings:
                next_node = df.previous_sibling == last_node
            else:
                last_parent = df[df.dialog_node == last_node].parent.values[0]
                next_node = df.previous_sibling == last_parent
            df.loc[next_node, "order"] = curr
            try:
                last_node = df[next_node].dialog_node.values[0]
            except IndexError:
                break
            curr += 1

        df.sort_values(by=["order"], inplace=True)
        df.drop("order", inplace=True, axis=1)
        return df

    def set_contexts_node(self):
        """
        Adds contexts to the 'welcome' node which are a mapping of generated nodes'
        titles. This enables the 'help' node, which picks random integers and offers
        a set of questions to the user.
        """
        df = self.df_generated[self.answers].reset_index(drop=True)
        anys = df.conditions.str.contains("anything_else")
        df = df[~anys]
        titles = df.title.to_dict()
        titles = {str(k): v for k, v in titles.items()}

        welcome_node = self.df_manual.conditions.str.contains("welcome").fillna(False)
        node_context = self.df_manual.loc[welcome_node, "context"].values[0]
        node_context["titles"] = titles
        self.df_manual.loc[welcome_node, "context"] = str(node_context)
        print("Contexts set!")

    def set_help_node(self, number_of_hints: int = 3):
        help_node = self.df_manual.conditions.str.contains("ajuda").fillna(False)
        number_of_intents = self.df_generated[self.answers].shape[0]
        intents_per_hint = number_of_intents // number_of_hints
        node_context = {
            f"dica{i}": f"<? new Random().nextInt({intents_per_hint}) +{i * intents_per_hint} ?>"
            for i in range(number_of_hints)
        }
        self.df_manual.loc[help_node, "context"] = str(node_context)
        print("Help node set!")

    def fix_previous_siblings(self):
        self._build()
        all_dialog_nodes = self._df.dialog_node.to_list()
        self._df.previous_sibling = self._df.previous_sibling.apply(
            lambda x: x if x in all_dialog_nodes else np.nan
        )
        self._separate_nodes()

    def apply_previous_siblings(self):
        """
        Applies previous_sibling to root level nodes as the root level node above.
        """
        root_nodes = self._df.parent.isna()
        self._df.loc[root_nodes, "previous_sibling"] = self._df.loc[
            root_nodes, "dialog_node"
        ].shift(1)
        self._separate_nodes()

        self.df_generated["node_above"] = self.df_generated.dialog_node.shift(1)
        self.df_generated.previous_sibling = (
            self.df_generated[["previous_sibling", "node_above"]]
            .fillna("")
            .apply(
                lambda series: series["previous_sibling"]
                if series["previous_sibling"]
                else series["node_above"],
                axis=1,
            )
        )

        previous_sibling_is_parent = (
            self.df_generated.previous_sibling == self.df_generated.parent
        )
        self.df_generated.previous_sibling[previous_sibling_is_parent] = np.nan
        print("Previous siblings fixed!")

    def point_to_anything_else_node(self):
        """
        Fixes the "next_step" field of the anything_else node inside the answers folder to
        be the value of the root anything_else.
        """
        df_answers = self.df_generated[self.answers]
        anything_else = df_answers.conditions == "anything_else"
        root_node = self.df_anything_else.dialog_node.values[0]
        self.df_generated.loc[self.answers & anything_else, "next_step"] = json.dumps(
            {
                "behavior": "jump_to",
                "selector": "body",
                "dialog_node": root_node,
            }
        )

    def limit_intents(self, limit: int):
        """
        In case there is an intent limit (100 on the lite plan), cuts down on the generated
        nodes to respect the maximum number.
        """
        if not limit:
            return
        generated_intents = self.df_generated.intent.to_list()
        generated_intents = drop_duplicates(generated_intents)
        generated_intents.sort()
        number_of_intents_to_remove = len(self.get_intents()) - limit
        intents_to_remove = generated_intents[-number_of_intents_to_remove:]

        for intent in intents_to_remove:
            intent_nodes = self.df_generated.conditions.str.contains(intent)
            answer_node = self.df_generated[intent_nodes]
            self.drop_node_chain(answer_node)
        self._build()
        self._separate_nodes()
        print("Intents limited!")

    def get_intents(self) -> list:
        """Returns a list of the intents used in the dialog nodes."""
        self._build()
        intents = self._df["intent"].to_list()
        return drop_duplicates(intents)

    def drop_node_chain(self, nodes: pd.DataFrame):
        """
        Removes a subset of dialog nodes from the generated df and all nodes which jump
        to those in the subset.
        """
        nodes_above = self.df_generated.next_step.astype(str).apply(
            lambda x: "jump_to" in x
            and any(node in x for node in nodes.dialog_node.to_list())
        )
        df_nodes_above = self.df_generated[nodes_above]

        # drop the input nodes
        self.df_generated.drop(nodes.index, inplace=True)

        # drop the nodes above
        if nodes_above.sum() > 0:
            self.drop_node_chain(df_nodes_above)
