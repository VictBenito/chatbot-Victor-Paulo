# Filter-MSMARCO
# @File:   NodeOrganizer.py
# @Time:   20/11/2021
# @Author: Gabriel O.

import uuid
from typing import List
import re

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
        self.anything_else_node = pd.Series(dtype=object)
        self.generated_nodes = pd.Series(dtype=object)
        self.manual_nodes = pd.Series(dtype=object)
        self.root = pd.Series(dtype=object)
        self.df_anything_else = pd.DataFrame()
        self.df_generated = pd.DataFrame()
        self.df_manual = pd.DataFrame()
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
        self.anything_else_node = self._df.parent.isna() & (
            self._df.conditions == "anything_else"
        )
        self.generated_nodes = ~self._df.dialog_node.str.match(r"node_._")
        self.manual_nodes = ~self.generated_nodes & ~self.anything_else_node
        self.df_anything_else = self._df[self.anything_else_node].copy()
        self.df_generated = self._df[self.generated_nodes].copy()
        self.df_manual = self._df[self.manual_nodes].copy()
        self.root = (
            self.df_manual.previous_sibling.isna()
            & self.df_manual.parent.isna()
            & self.df_manual.next_step.isna()
        )

    def _build(self):
        """Updates the main dataframe to reflect changes in its subparts."""
        self._df = self.df_manual.append(self.df_generated).append(self.df_anything_else)
        self._df.reset_index(drop=True, inplace=True)
        self._extract_intents()

    @property
    def df(self) -> pd.DataFrame:
        """Returns the main dataframe after building and dropping temporary columns."""
        self._build()
        out = self._df.drop(
            columns=["fonte", "intent", "modificador", "substantivo", "recipiente"],
            errors="ignore",
        )
        return out

    def run(self, intent_limit: int = 0):
        self.sort_nodes()
        self.limit_intents(intent_limit)
        self.set_contexts_node()
        self.set_help_node()
        self.set_sources()
        self.cleanup_previous_siblings()
        self.fix_previous_siblings()

    def sort_nodes(self):
        self.df_manual = self.sort_by_previous_siblings(df=self.df_manual, root=self.root)
        self.df_generated.sort_values(by=["intent"], inplace=True)
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
        df = self.df_generated.reset_index(drop=True)
        titles = df.title.to_dict()
        titles = {str(k): v for k, v in titles.items()}

        welcome_node = self.df_manual.conditions.str.contains("welcome").fillna(False)
        node_context = self.df_manual.loc[welcome_node, "context"].to_list()[0]
        node_context["titles"] = titles
        self.df_manual.loc[welcome_node, "context"] = str(node_context)
        print("Contexts set!")

    def set_help_node(self, number_of_hints: int = 3):
        help_node = self.df_manual.conditions.str.contains("ajuda").fillna(False)
        number_of_intents = self.df_generated.shape[0]
        intents_per_hint = number_of_intents // number_of_hints
        node_context = {
            f"dica{i}": f"<? new Random().nextInt({intents_per_hint}) +{i * intents_per_hint} ?>"
            for i in range(number_of_hints)
        }
        self.df_manual.loc[help_node, "context"] = str(node_context)
        print("Help node set!")

    def cleanup_previous_siblings(self):
        """Removes the previous_sibling field of all nodes except manual ones."""
        self.df_generated["previous_sibling"] = np.nan
        self.df_anything_else["previous_sibling"] = np.nan
        print("Previous siblings cleaned up!")

    def fix_previous_siblings(self):
        """
        Applies previous_sibling to nodes which don't have one (generated) based on the
        node above. Then, connects the generated nodes to the manual nodes and the last
        node (anything_else).
        """
        no_upstream = (
            self.df_generated.previous_sibling.isna() & self.df_generated.parent.isna()
        )
        df_no_upstream = self.df_generated[no_upstream].copy()
        df_no_upstream.reset_index(inplace=True)
        df_no_upstream.previous_sibling = df_no_upstream.dialog_node.shift(1)

        # assign the last manual node as the previous sibling for the first generated node
        df_no_upstream.loc[0, "previous_sibling"] = self._find_last_root_node(
            self.df_manual
        )
        df_no_upstream.set_index("index", inplace=True)

        # assign the last generated node as the previous sibling for the anything_else node
        root_level = self.df_generated.parent.isna()
        last_root_generated_node = self.df_generated.loc[
            root_level, "dialog_node"
        ].to_list()[-1]
        self.df_anything_else["previous_sibling"] = last_root_generated_node

        # overwrites df_generated with values from df_no_upstream based on index
        self.df_generated.update(df_no_upstream)
        print("Previous siblings fixed!")

    @staticmethod
    def _find_last_root_node(df: pd.DataFrame):
        """
        Returns the identifier of the last entry which is a root node (does not have
        parents).
        """
        no_parent = df.parent.isna()
        no_parent_indices = no_parent.index[no_parent].to_list()
        last_no_parent = no_parent_indices.pop()
        return df.loc[last_no_parent].dialog_node

    def set_sources(self):
        """
        For each generated node, adds a child node which is activated if the user asks
        for the source of the information.
        """
        df = self.df_generated.reset_index(drop=False)
        sources = df.apply(self._create_source, axis=1, cols=df.columns)
        df_with_sources = pd.concat([df, sources])
        df_with_sources.set_index("index", inplace=True)
        df_with_sources.sort_index(inplace=True)
        df_with_sources.reset_index(drop=True, inplace=True)
        self.df_generated = df_with_sources
        print("Sources set!")

    @staticmethod
    def _create_source(parent: pd.Series, cols: pd.Index) -> pd.Series:
        fontes = parent["fonte"].split("--")
        fontes = drop_duplicates(fontes)
        if len(fontes) > 1:
            answer = "As fontes dessa resposta são: " + ", ".join(fontes)
        elif len(fontes) > 0:
            answer = "A fonte dessa resposta é: " + ", ".join(fontes)
        else:
            answer = """
                Desculpe, não tenho uma fonte específica para essa resposta.
            """.strip()

        content = {
            "index": parent["index"] + 0.5,
            "type": "standard",
            "title": "Fonte",
            "output": {
                "generic": [
                    {
                        "values": [{"text": answer}],
                        "response_type": "text",
                        "selection_policy": "sequential",
                    }
                ]
            },
            "conditions": "#fonte",
            "dialog_node": f"node_{uuid.uuid4().hex[:16]}",
            "parent": parent["dialog_node"],
        }
        output = pd.Series(content, index=cols)
        return output

    def limit_intents(self, limit: int):
        """
        In case there is an intent limit (100 on the lite plan), cuts down on the generated
        nodes to respect the maximum number.
        """
        if not limit:
            return
        manual_intents = self.df_manual.conditions.str.contains(r"#\S+")
        self.df_generated.drop(
            self.df_generated.tail(limit - manual_intents.sum()), inplace=True
        )
        self._separate_nodes()
        print("Intents limited!")

    def get_intents(self) -> list:
        """Returns a list of the intents used in the dialog nodes."""
        self._build()
        intents = self._df["intent"].to_list()
        return drop_duplicates(intents)
