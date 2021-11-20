# Filter-MSMARCO
# @File:   plural.py
# @Time:   17/11/2021
# @Author: Gabriel O.

import re


def plural(palavra: str) -> str:
    """
    Passa uma palavra em português para o plural. Não funciona sempre,
    devido à quantidade de exceções que precisam ser programadas à mão.
    """
    palavra = palavra.strip()

    # se for vazia ou mais de uma palavra, retorna sem alterar
    if not palavra or len(palavra.split(" ")) > 1:
        return palavra

    # se a palavra no plural é igual no singular, retorna sem alterar
    invariaveis = [r"x$"]
    for p in invariaveis:
        if re.search(p, palavra):
            return palavra

    substituicoes = {
        r"ão": r"õe",
        r"r$": r"re",
        r"z$": r"ze",
        r"(?<=[aeou])l": r"i",
        r"il": r"ei",
        r"m$": r"n",
    }
    for p, s in substituicoes.items():
        palavra = re.sub(p, s, palavra)

    return palavra + "s" if palavra[-1] != "s" else palavra
