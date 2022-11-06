# Filter-MSMARCO
# @File:   generate_skill.py
# @Time:   17/11/2021
# @Author: Gabriel O.

import re
from datetime import datetime
from pathlib import Path

from src.dialog_nodes.NodeOrganizer import NodeOrganizer
from src.dialog_nodes.dialog_node_operations import convert_to_list, get_dialog_nodes
from src.entities.entity_operations import get_entities
from src.intents.intent_operations import get_intents
from src.io.file_operations import load_questions, load_skill, save_skill
from src.skills.skill_operations import mix_skills
from src.utils.list_dict_operations import mix_list, remove
from tests import unit, collisions


def main(confidence: float, limit: int = 0):
    sheet_path = Path(__file__).parent / "../results/Perguntas.xlsx"
    questions = load_questions(sheet_path.resolve().as_posix())

    skill_path = Path(__file__).parent / "../results/skill-Amazônia-Azul.json"
    old_skill = load_skill(skill_path.resolve().as_posix())

    new_intents = get_intents(questions)
    print("Intents obtained!")
    mixed_intents = mix_list(old_skill["intents"], new_intents)
    print("Intents mixed!")

    new_entities = get_entities(questions)
    print("Entities obtained!")
    key_priority = {"conditions": 1, "title": 0}
    mixed_entities = mix_list(old_skill["entities"], new_entities, key_priority)
    mixed_entities.sort(key=lambda x: x["entity"])
    print("Entities mixed!")

    new_nodes = get_dialog_nodes(questions, confidence)
    print("Nodes obtained!")

    # delete old generated nodes
    old_nodes = old_skill["dialog_nodes"]
    old_nodes = [n for n in old_nodes if re.search(r"node_._", n["dialog_node"])]

    mixed_nodes = mix_list(old_nodes, new_nodes)
    print("Nodes mixed!")

    node_organizer = NodeOrganizer(mixed_nodes)
    node_organizer.run(intent_limit=limit)

    used_intents = node_organizer.get_intents()
    removed_intents = remove(mixed_intents, used_intents)
    mixed_intents = [
        intent for intent in mixed_intents if intent["intent"] in used_intents
    ]
    print("Unused intents removed!")

    collisions.run(node_organizer)
    unit.run(node_organizer.df)

    organized_nodes = convert_to_list(node_organizer.df)
    mixed_skill = mix_skills(
        old_skill,
        intents=mixed_intents,
        entities=mixed_entities,
        dialog_nodes=organized_nodes,
    )
    save_skill(skill_path.resolve(), mixed_skill)

    print("Finished at", datetime.now().strftime("%H:%M"))


if __name__ == "__main__":
    MINIMUM_CONFIDENCE = 0.8
    INTENT_LIMIT = 2000
    main(confidence=MINIMUM_CONFIDENCE, limit=INTENT_LIMIT)
