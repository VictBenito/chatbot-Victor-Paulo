# Filter-MSMARCO
# @File:   collisions.py
# @Time:   22/11/2021
# @Author: Gabriel O.

import pandas as pd

from src.dialog_nodes.NodeOrganizer import NodeOrganizer


def run(organizer: NodeOrganizer):
    df = organizer.df_generated[organizer.answers]
    for tags, df_tag in df.groupby(["rotulos"], dropna=False):
        for modificador, df_modifier in df_tag.groupby(["modificador"]):
            check_collisions(df_modifier, tags, modificador, "substantivo", "recipiente")
            check_collisions(df_modifier, tags, modificador, "recipiente", "substantivo")


def check_collisions(
    df: pd.DataFrame, tags: str, modifier: str, col: str, other_col: str
):
    for col_value, d in df.groupby(col):
        if d.shape[0] > 1 and d[other_col].isna().sum() > 0:
            intent = tags if tags == tags else "..."
            print(
                f"Possible collisions for #{intent}--{modifier}-{col_value}-____: "
                f"{d[other_col].fillna('').to_list()}"
            )
