# Filter-MSMARCO
# @File:   unit.py
# @Time:   22/11/2021
# @Author: Gabriel O.
from pathlib import Path

from src.io.file_operations import load_skill
import pandas as pd


def main():
    skill_path = Path(__file__).parent / "../results/skill-Amazônia-Azul2.json"
    skill = load_skill(skill_path.resolve().as_posix())
    df = pd.DataFrame(skill["dialog_nodes"])

    dup = df[df.dialog_node.duplicated()]
    empty = df[df.dialog_node.isna()]
    print("End")


if __name__ == "__main__":
    main()
