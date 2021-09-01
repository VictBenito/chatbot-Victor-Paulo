# EP2 Meccomp
# @File:   utils.py
# @Time:   29/06/2021
# @Author: Gabriel O.


def getInput(message, dic: dict = None):
    """
    Imprime em loop uma mensagem pedindo um input do usuario
    ate que ele digite uma resposta valida.

    :param message: mensagem que aparece para o usuário
    :param dic: dicionario onde valores sao respostas do
                usuario que devolvem a respectiva chave
    :return: chave do dicionario correspondente a entrada
    """
    if dic is None:
        dic = {True: ["s", "sim", "y", "yes"], False: ["n", "nao", "no"]}
    else:
        dic = {k.lower().strip() for k in dic.keys()}
    while True:
        options = "/".join([v[0] for k, v in dic.items()])
        input_str = sanitize(input(f"{message} ({options})"))
        try:
            out = next(key for key, value in dic.items() if input_str in value)
            return out
        except StopIteration:
            print("Digite uma resposta válida!")


def sanitize(string) -> str:
    """
    Substitui letras acentuadas pelas nao acentuadas, remove espacos
    nas pontas e transforma em minusculas.
    :param string: string a ser sanitizada
    :return out: string sem acentos
    """
    out = string.lower().strip()
    accented = {
        "a": ["ã", "á", "à", "â"],
        "e": ["é", "è", "ê"],
        "i": ["í", "ì", "î"],
        "o": ["õ", "ó", "ò", "ô"],
        "u": ["ú", "ù", "û"],
        "c": ["ç"],
    }
    for letra, acentuadas in accented.items():
        for acc in acentuadas:
            out = out.replace(acc, letra)
    return out
