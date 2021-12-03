# Filter-MSMARCO
# @File:   unit.py
# @Time:   22/11/2021
# @Author: Gabriel O.

import pandas as pd


def run(df: pd.DataFrame):
    dup = df[df.dialog_node.duplicated()]
    empty = df[df.dialog_node.isna()]
    is_self_parent = df[df.dialog_node == df.parent]
    is_self_sibling = df[df.dialog_node == df.previous_sibling]

    print("Running tests...")
    assert dup.shape[0] == 0, "There are nodes with duplicated dialog_node"
    assert empty.shape[0] == 0, "There are nodes without dialog_node"
    assert is_self_parent.shape[0] == 0, "There are nodes which are their own parent"
    assert (
        is_self_sibling.shape[0] == 0
    ), "There are nodes which are their own previous_sibling"
    print("Tests finished.")
