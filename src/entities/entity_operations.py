# Filter-MSMARCO
# @File:   entity_operations.py
# @Time:   20/11/2021
# @Author: Gabriel O.

from src.utils.list_dict_operations import drop_duplicates


def get_entities(df):
    subset = ["rótulos", "modificador", "substantivo", "recipiente"]
    entities = [
        {"entity": col, "values": get_entity_values(df[col]), "fuzzy_match": True}
        for col in subset
    ]
    entities.sort(key=lambda x: x["entity"])
    return entities


def get_entity_values(series):
    records = series.to_list()
    records = drop_duplicates(records)
    records = [r.replace("-", " ") for r in records]
    values = [{"type": "synonyms", "value": record, "synonyms": []} for record in records]
    values.sort(key=lambda x: x["value"])
    return values
