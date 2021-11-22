# Filter-MSMARCO
# @File:   file_operations.py
# @Time:   20/11/2021
# @Author: Gabriel O.

import json
import os
from pathlib import Path

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
    df = df[subs]
    df = df.rename(columns=subs)
    df = df.fillna("")
    return df


def load_skill(filepath: str) -> dict:
    with open(filepath, "r", encoding="utf-8") as f:
        sk = json.load(f)
    return sk


def save_skill(filepath: Path, to_save: dict):
    new_stem = f"{filepath.stem}2"
    new_path = filepath.with_name(new_stem + filepath.suffix)
    with open(new_path, "w", encoding="utf-8") as f:
        json.dump(to_save, f, ensure_ascii=False, indent=2)
    common_path = os.path.commonpath([Path(__file__), new_path])
    print(f"Skill saved as {new_path.relative_to(common_path).as_posix()}!")
