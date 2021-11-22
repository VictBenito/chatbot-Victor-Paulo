# Filter-MSMARCO
# @File:   collisions.py
# @Time:   22/11/2021
# @Author: Gabriel O.
from typing import List

import pandas as pd

from src.dialog_nodes.NodeOrganizer import NodeOrganizer
from src.utils.list_dict_operations import flatten


def run(organizer: NodeOrganizer):
    df = organizer.df_generated[organizer.answers]
    possible_collisions = []

    for tags, df_tag in df.groupby(["rotulos"], dropna=False):
        for modificador, df_modifier in df_tag.groupby(["modificador"]):
            possible_collisions.append(
                check_collisions(
                    df_modifier, tags, modificador, "substantivo", "recipiente"
                )
            )
            possible_collisions.append(
                check_collisions(
                    df_modifier, tags, modificador, "recipiente", "substantivo"
                )
            )

    possible_collisions = flatten(possible_collisions)
    if possible_collisions:
        possible_collisions.insert(0, "Possible collisions found:")
        collisions_string = "\n\t".join(possible_collisions)
        print(collisions_string)


def check_collisions(
    df: pd.DataFrame, tags: str, modifier: str, col: str, other_col: str
) -> List[str]:
    collisions = []
    for col_value, d in df.groupby(col):
        if d.shape[0] > 1 and d[other_col].isna().sum() > 0:
            intent = f"#{tags}" if tags == tags else "(no context)"

            collisions.append(
                f"{intent}--{modifier}-{col_value}-____: "
                f"({', '.join(d[other_col].fillna('___').to_list())})"
            )
    return collisions
