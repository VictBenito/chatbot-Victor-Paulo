# Filter-MSMARCO
# @File:   get_title.py
# @Time:   21/11/2021
# @Author: Gabriel O.

import re
from typing import List, Mapping

from src.utils.list_dict_operations import drop_duplicates
from src.utils.plural import plural


def get_contexts(tags: List[str]) -> List[str]:
    """
    Returns the contexts of a question which do not contain non-contextual tags.
    """
    tags = [t.replace("-", " ") for t in tags]
    non_contextual_tags = [
        "fauna",
        "flora",
        "outras",
        "física",
        "turismo",
        "saúde",
        "geologia",
    ]
    output = [
        context
        for context in tags
        if all(tag not in context for tag in non_contextual_tags)
    ]
    return drop_duplicates(output)


def get_title(js: Mapping, contexts: List[str]) -> str:
    """
    Returns a title for a node based on modificador, substantivo, recipiente
    and rótulos.
    """
    modificador = js["modificador"].replace("-", " ")
    substantivo = js["substantivo"].replace("-", " ")
    recipiente = js["recipiente"].replace("-", " ")

    contexto = "/".join(contexts)
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
        if not (recipiente or contexto):
            raise ValueError(
                f"Perguntas do tipo 'definição' precisam de recipiente ou de contexto! "
                f"Pergunta: {js['pergunta']}"
            )
        if recipiente:
            if contexto:
                trechos.append(f"{contexto}:")
            trechos.append(modificador)
            if substantivo:
                trechos.append(f"de {substantivo}")
            trechos.append(f"de {recipiente}?")
        elif contexto:
            trechos.append(modificador)
            if substantivo:
                trechos.append(f"de {substantivo}")
            trechos.append(f"de {contexto}?")
    elif modificador in ["detalhar"]:
        if not (recipiente or contexto):
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
        trechos.append(f"e {recipiente or contexto}?")
    elif modificador in ["é"]:
        if not (
            (substantivo and contexto)
            or (recipiente and contexto)
            or (substantivo and recipiente)
        ):
            raise ValueError(
                f"Perguntas do tipo 'é' precisam de dois entre substantivo, recipiente "
                f"e contexto! Pergunta: {js['pergunta']}"
            )
        else:
            trechos.append(substantivo or contexto)
            trechos.append(f"é {recipiente or contexto}?")
    elif modificador in ["efeito"]:
        trechos.append(modificador)
        if substantivo:
            trechos.append(f"de {substantivo}")
        if recipiente:
            if contexto:
                trechos.append(f"de {contexto}")
            trechos.append(f"em {recipiente}")
        else:
            trechos.append(f"em {contexto}")
        trechos.append("?")
    elif modificador in ["existe"]:
        if not recipiente:
            raise ValueError(
                f"Perguntas do tipo 'existe' precisam de recipiente! "
                f"Pergunta: {js['pergunta']}"
            )
        if contexto:
            trechos.append(contexto + ":")
        trechos.append(modificador)
        if substantivo:
            trechos.append(substantivo)
        trechos.append(f"em {recipiente}?")
    elif modificador in ["explicar"]:
        trechos.append(modificador)
        if substantivo:
            trechos.append(substantivo)
            if recipiente:
                trechos.append(f"de {recipiente}")
            if contexto:
                trechos.append(f"de {contexto}")
        else:
            trechos.append(contexto)
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
    elif modificador in ["onde"]:
        if not (contexto or recipiente):
            raise ValueError(
                f"Perguntas do tipo 'detalhar' precisam de recipiente ou contexto!"
                f" Pergunta: {js['pergunta']}"
            )
        trechos.append(f"{modificador} tem")
        if substantivo:
            trechos.append(plural(substantivo))
            trechos.append(f"de {recipiente or contexto}")
        else:
            trechos.append(contexto)
            if recipiente:
                trechos.append(f"em {recipiente}")
        trechos.append("?")
    elif modificador in ["porque"]:
        if not contexto:
            raise ValueError(
                f"Perguntas do tipo 'porque' precisam de contexto!"
                f" Pergunta: {js['pergunta']}"
            )
        trechos.append(f"{contexto}:")
        if recipiente:
            trechos.append(recipiente)
        trechos.append("por que?")
    elif modificador in ["quantidade"]:
        if not (substantivo or contexto):
            raise ValueError(
                f"Perguntas do tipo 'quantidade' precisam de substantivo ou contexto!"
                f" Pergunta: {js['pergunta']}"
            )
        if substantivo:
            trechos.append(f"{contexto}:")
            trechos.append(modificador)
            trechos.append(f"de {plural(substantivo)}")
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
        r"\bem amazônia azul": "na Amazônia Azul",
        r"\bde amazônia azul": "da Amazônia Azul",
        r"\bem brasil": "no Brasil",
        r"\bde brasil": "do Brasil",
        r"\bem oceano": "no oceano",
        r"\bde oceano": "do oceano",
        r"\bde governo": "do governo",
        r"\bde mundo": "do mundo",
        r"\bem ambiente": "no ambiente",
        r"\bde branqueamento": "do branqueamento",
        r"\bde poluição": "da poluição",
        r"\bum tartaruga": "uma tartaruga",
        r"\bde projeto de": "do projeto",
        r"\s+\?": "?",
        r"\s+": " ",
    }
    for pattern, subs in substituir.items():
        titulo = re.sub(pattern, subs, titulo)
    return titulo
