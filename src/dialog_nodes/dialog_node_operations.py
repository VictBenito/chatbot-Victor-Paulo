# Filter-MSMARCO
# @File:   dialog_node_operations.py
# @Time:   20/11/2021
# @Author: Gabriel O.

import ast
import uuid
from typing import List

import pandas as pd

from src.utils.list_dict_operations import remove_nans, flatten, drop_duplicates
from src.utils.plural import plural
from src.utils.sanitize import sanitize


def get_dialog_nodes(df: pd.DataFrame, confidence) -> List[dict]:
    records = df.to_dict(orient="records")
    nodes = [
        {
            "type": "standard",
            "title": get_titulo(record),
            "output": {
                "generic": [
                    {
                        "values": [{"text": record["resposta"]}],
                        "response_type": "text",
                        "selection_policy": "sequential",
                    }
                ]
            },
            "context": {"contexto": sanitize(record["rótulos"].replace("-", " "))},
            "conditions": get_all_conditions(record, confidence),
            "dialog_node": f"node_{uuid.uuid4().hex[:16]}",
            "fonte": record["fonte"],
            "intent": record["intent"],
            "modificador": record["modificador"],
            "substantivo": record["substantivo"],
            "recipiente": record["recipiente"],
        }
        for record in records
    ]
    nodes.sort(key=lambda x: x["conditions"])
    return nodes


def get_titulo(js: dict) -> str:
    """
    Returns a title for a node based on modificador, substantivo, recipiente
    and rótulos.
    """
    modificador = js["modificador"].replace("-", " ")
    substantivo = js["substantivo"].replace("-", " ")
    recipiente = js["recipiente"].replace("-", " ")

    contextos = get_contextos(js["rótulos"].split("_"))
    contextos = list(map(lambda x: x.replace("-", " "), contextos))
    contexto = f"{'/'.join(contextos)}"
    trechos = []

    if modificador in ["causa"]:
        if not (contexto or recipiente):
            raise ValueError(
                f"Perguntas do tipo 'causa' precisam de recipiente ou contexto!"
                f" Pergunta: {js['pergunta']}"
            )
        trechos.append(modificador)
        if substantivo:
            trechos.append(f"de {substantivo}")
        if recipiente:
            trechos.append(f"de {recipiente}")
        if contexto:
            trechos.append(f"de {contexto}")
        trechos.append("?")
    elif modificador in ["definição"]:
        trechos.append(modificador)
        if substantivo:
            trechos.append(f"de {substantivo}")
        if recipiente:
            trechos.append(f"de {recipiente}?")
        else:
            trechos.append(f"de {contexto}?")
    elif modificador in ["detalhar"]:
        if not (contexto or recipiente):
            raise ValueError(
                f"Perguntas do tipo 'detalhar' precisam de recipiente ou de contexto! "
                f"Pergunta: {js['pergunta']}"
            )
        trechos.append(modificador)
        if substantivo:
            trechos.append(f"{substantivo}")
        if recipiente:
            trechos.append(f"de {recipiente}")
        if contexto:
            trechos.append(f"de {contexto}")
    elif modificador in ["diferença"]:
        trechos.append(modificador)
        trechos.append(f"entre {substantivo}")
        trechos.append(f"e {recipiente or contextos[0]}?")
    elif modificador in ["é"]:
        if not (
            (substantivo and contexto)
            or (recipiente and contexto)
            or (substantivo and recipiente)
        ):
            raise ValueError(
                f"Perguntas do tipo 'é' precisam de contexto e substantivo ou "
                f"recipiente! Pergunta: {js['pergunta']}"
            )
        else:
            trechos.append(substantivo or contexto)
            trechos.append(f"é {recipiente or contexto}?")
    elif modificador in ["efeito"]:
        if contexto:
            trechos.append(contexto + ":")
        trechos.append(modificador)
        if substantivo:
            trechos.append(f"de {substantivo}")
        trechos.append(f"em {recipiente or contextos[0]}?")
    elif modificador in ["existe"]:
        if not recipiente:
            raise ValueError(
                f"Perguntas do tipo 'exist' precisam de recipiente! "
                f"Pergunta: {js['pergunta']}"
            )
        if contexto:
            trechos.append(contexto + ":")
        trechos.append(modificador)
        if substantivo:
            trechos.append(substantivo)
        trechos.append(f"em {recipiente}?")
    elif modificador in ["explicar"]:
        if not substantivo:
            raise ValueError(
                f"Perguntas do tipo 'explicar' precisam de substantivo! "
                f"Pergunta: {js['pergunta']}"
            )
        trechos.append(modificador)
        trechos.append(substantivo)
        if recipiente:
            trechos.append(f"de {recipiente}")
        if contexto:
            trechos.append(f"de {contexto}")
    elif modificador in ["listar"]:
        if substantivo:
            if recipiente:
                if contexto:
                    trechos.append(f"{contexto}:")
                trechos.append(modificador)
                trechos.append(plural(substantivo))
                trechos.append(f"de {recipiente}")
            else:
                trechos.append(modificador)
                trechos.append(plural(substantivo))
                if contexto:
                    trechos.append(f"de {contexto}")
        else:
            trechos.append(modificador)
            trechos.append(contexto)
    elif modificador in ["localização"]:
        if not (contexto or recipiente):
            raise ValueError(
                f"Perguntas do tipo 'detalhar' precisam de recipiente ou contexto!"
                f" Pergunta: {js['pergunta']}"
            )
        trechos.append(modificador)
        if substantivo:
            trechos.append(f"de {plural(substantivo)}")
        trechos.append(f"de {recipiente or contexto}?")
    elif modificador in ["maior", "menor"]:
        trechos.append(modificador)
        if substantivo:
            trechos.append(substantivo)
        if contexto:
            trechos.append(f"de {contexto}")
        if recipiente:
            trechos.append(f"de {recipiente}")
        trechos.append("?")
    elif modificador in ["maiores", "menores"]:
        trechos.append(modificador)
        trechos.append(plural(substantivo))
        if contexto:
            trechos.append(f"de {contexto}")
        if recipiente:
            trechos.append(f"de {recipiente}")
        trechos.append("?")
    elif modificador in ["porque"]:
        if not contexto:
            raise ValueError(
                f"Perguntas do tipo 'porque' precisam de contexto!"
                f" Pergunta: {js['pergunta']}"
            )
        elif len(contextos) == 2:
            trechos.append(f"{contextos[1]}:")
            trechos.append("motivo para")
            trechos.append(f"{contextos[0]}?")
        else:
            trechos.append(f"{contexto}:")
            trechos.append("motivo para")
            if recipiente:
                trechos.append(recipiente)
            trechos.append(f"?")
    elif modificador in ["quantidade"]:
        if not (substantivo or contexto):
            raise ValueError(
                f"Perguntas do tipo 'quantidade' precisam de substantivo ou contexto!"
                f" Pergunta: {js['pergunta']}"
            )
        if substantivo:
            trechos.append(f"{contexto}:")
            trechos.append(modificador)
            trechos.append(f"{plural(substantivo)}")
        else:
            trechos.append(modificador)
            trechos.append(f"de {contexto}")
        if recipiente:
            trechos.append(f"em {recipiente}")
        trechos.append("?")
    elif modificador in ["responsável"]:
        if not substantivo:
            raise ValueError(
                f"Perguntas do tipo 'responsável' precisam de substantivo! "
                f"Pergunta: {js['pergunta']}"
            )
        if not (contexto or recipiente):
            raise ValueError(
                f"Perguntas do tipo 'responsável' precisam de recipiente ou contexto! "
                f"Pergunta: {js['pergunta']}"
            )
        trechos.append(modificador)
        trechos.append(f"por {substantivo}")
        trechos.append(f"de {recipiente or contexto}?")
    else:
        raise NotImplementedError(f"Modificador '{modificador}' não programado!")
    trechos[0] = trechos[0].capitalize()
    titulo = " ".join(trechos)
    titulo = titulo.strip()
    substituir = {
        " ?": "?",
        "em amazônia azul": "na Amazônia Azul",
        "de amazônia azul": "da Amazônia Azul",
        "em brasil": "no Brasil",
        "de brasil": "no Brasil",
        "de extinção": "em extinção",
        "de oceano": "do oceano",
        "de governo": "do governo",
        "de mundo": "do mundo",
        "em ambiente": "no ambiente",
        "de branqueamento": "do branqueamento",
        "um tartaruga": "uma tartaruga",
        "de petróleo": "do petróleo",
        "de projeto de": "do projeto",
    }
    for palavra, substituta in substituir.items():
        titulo = titulo.replace(palavra, substituta)
    return titulo


def get_contextos(tags: List[str]) -> List[str]:
    """
    Returns the contexts of a question based on its tags, considering
    there are tags which do not define context.
    """
    non_contextual_tags = [
        "fauna",
        "flora",
        "outras",
        "física",
        "turismo",
        "saúde",
        "geologia",
    ]
    return [
        context
        for context in tags
        if all(tag not in context for tag in non_contextual_tags)
    ]


def get_all_conditions(js: dict, confidence: float = None) -> str:
    modificador = js["modificador"].replace("-", " ")
    substantivo = js["substantivo"].replace("-", " ")
    recipiente = js["recipiente"].replace("-", " ")
    rotulos = js["rótulos"].replace("-", " ").split("_")
    rotulos += [js["rótulos"].replace("-", " ")]
    rotulos = drop_duplicates(rotulos)
    contextos = get_contextos(rotulos)

    base_condition = f"#{js['intent']}"
    if confidence:
        base_condition += f" && intent.confidence > {confidence}"
    # the next part requires at least one element in the list
    if not contextos:
        contextos = [None]

    additional_conditions = [
        get_single_condition(modificador, substantivo, recipiente, contexto)
        for contexto in contextos
    ]
    conditions = [base_condition, *flatten(additional_conditions)]
    condition_string = " || ".join(conditions)
    return condition_string


def get_single_condition(modificador, substantivo, recipiente, contexto) -> list:
    trechos = [f"@modificador:({modificador})"]
    if substantivo:
        trechos.append(f"&& @substantivo:({substantivo})")
    if recipiente:
        trechos.append(f"&& @recipiente:({recipiente})")
    cond = " ".join(trechos)
    if contexto:
        out = [
            cond + f" && $contexto:({contexto})",
            cond + f" && @rótulos:({contexto})",
        ]
    else:
        out = [cond]
    return out


def convert_to_list(df: pd.DataFrame) -> List[dict]:
    list_of_dicts = df.to_dict(orient="records")
    list_of_dicts = [remove_nans(d) for d in list_of_dicts]
    list_of_dicts = [eval_context(d) for d in list_of_dicts]
    return list_of_dicts


def eval_context(d: dict):
    if "context" not in d:
        return d
    context = d["context"]
    if isinstance(context, str):
        evaluated = ast.literal_eval(context)
        d["context"] = evaluated
    return d
