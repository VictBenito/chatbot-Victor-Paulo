# Filter-MSMARCO
# @File:   file_operations.py
# @Time:   20/11/2021
# @Author: Gabriel O.

import json
import os

import pandas as pd


def load_questions(filepath: str) -> pd.DataFrame:
    df = pd.read_excel(filepath, sheet_name="finais")
    df = df.dropna(subset=["Resposta"])
    subs = {
        "Pergunta": "pergunta",
        "Resposta": "resposta",
        "Fonte": "fonte",
        "Intenção": "intent",
        "Rótulos": "rótulos",
        "Modificador": "modificador",
        "Substantivo": "substantivo",
        "Recipiente": "recipiente",
        "Elocuções": "examples",
    }
    df = df[list(subs.keys())]
    df = df.rename(columns=subs)
    df = df.fillna("")
    return df


def load_skill(filepath: str) -> dict:
    with open(filepath, "r", encoding="utf-8") as f:
        sk = json.load(f)
    return sk


def save_skill(filepath: str, to_save: dict):
    root, extension = os.path.splitext(filepath)
    new_skill_path = f"{root}2{extension}"
    with open(new_skill_path, "w", encoding="utf-8") as f:
        json.dump(to_save, f, ensure_ascii=False, indent=4)
    print(f"Skill saved as {new_skill_path}!")
