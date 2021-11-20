# Filter-MSMARCO
# @File:   sanitize.py
# @Time:   17/11/2021
# @Author: Gabriel O.

def sanitize(palavra: str) -> str:
    """Substitui caracteres acentuados."""
    substituicoes = {
        "a": ["á", "â", "ã", "à"],
        "c": ["ç"],
        "e": ["é", "ê"],
        "i": ["í"],
        "o": ["ó", "ô", "õ"],
        "u": ["ú", "ü"],
    }
    for substituta, letras in substituicoes.items():
        for letra in letras:
            palavra = palavra.replace(letra, substituta)
    return palavra
