# Filter-MSMARCO
# @File:   intent_operations.py
# @Time:   20/11/2021
# @Author: Gabriel O.

from typing import List

import pandas as pd


def get_intents(df: pd.DataFrame) -> List[dict]:
    subset = ["intent", "pergunta", "examples"]
    records = df[subset].to_dict(orient="records")
    intents = [
        {
            "intent": record["intent"],
            "examples": get_examples(record),
            "description": "",
        }
        for record in records
    ]
    intents.sort(key=lambda x: x["intent"])
    return intents


def get_examples(record: dict) -> List:
    # the question itself is one example
    out = [{"text": record["pergunta"]}]
    # everything in "examples" is also an example
    if record["examples"]:
        out += [{"text": exemplo} for exemplo in record["examples"].split("--")]
    return out
