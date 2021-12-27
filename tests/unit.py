# Filter-MSMARCO
# @File:   unit.py
# @Time:   22/11/2021
# @Author: Gabriel O.

from typing import List

import pandas as pd


def run(df: pd.DataFrame):
    dup = df[df.dialog_node.duplicated()]
    empty = df[df.dialog_node.isna()]
    is_self_parent = df[df.dialog_node == df.parent]
    is_self_sibling = df[df.dialog_node == df.previous_sibling]

    errors = []
    print("Running tests...")
    if dup.shape[0] > 0:
        errors.append("There are nodes with duplicated dialog_node")
    if empty.shape[0] > 0:
        errors.append("There are nodes without dialog_node")
    if is_self_parent.shape[0] > 0:
        errors.append("There are nodes which are their own parent")
    if is_self_sibling.shape[0] > 0:
        errors.append("There are nodes which are their own previous_sibling")

    errors = test_collisions(df, errors)

    if errors:
        errors.insert(0, "")
        print("Tests failed:", "\n\t- ".join(errors))
    else:
        print("Tests passed!")


def test_collisions(df: pd.DataFrame, errors: List[str]) -> List[str]:
    """
    Looks for collisions in nodes, which is when a dialog_node is the previous_sibling of
    more than one node.
    """
    df["prev_sib_count"] = df.dialog_node.apply(
        lambda x: df.previous_sibling.str.contains(x).sum()
    )
    collisions = df[df.prev_sib_count > 1]
    if collisions.shape[0] != 0:
        errors.append(
            f"There are collisions in nodes: {', '.join(collisions.dialog_node.to_list())}"
        )
    return errors
