# @Time:   30/06/2021
# @Author: Gabriel O.

import json
from tqdm import tqdm


def fix_lookup(lookup: dict, marco_query: dict) -> dict:
    """
    Por algum motivo, a lookup table não anotou corretamente o query id de cada query capturada.
    Então, para cada query presente na lookup table, iteramos sobre as queries do arquivo original
    até encontrar o id correto.

    :param lookup: conteudo da lookup_table
    :param marco_query: queries do ms marco
    :return:
    """
    new_lookup = {}
    print("Consertando lookup! ~1min")
    for l_index, l_query in tqdm(lookup["Doc"].items()):
        real_key = next(
            m_index for m_index, m_query in marco_query.items() if m_query == l_query
        )
        new_lookup[real_key] = l_query
    return new_lookup


def extract_questions():
    # Ler os diferentes jsons (queries, answers, well formed answers)
    with open("data/train_v2.1_query.json", "r") as file:
        marco_query = json.load(file)

    with open("data/train_v2.1_answers.json", "r") as file:
        marco_answers = json.load(file)

    with open("data/train_v2.1_wellFormedAnswers.json", "r") as file:
        marco_wfanswers = json.load(file)

    with open("results/lookup_table.json", "r") as file:
        lookup_table = json.load(file)

    # substituir chaves pelas corretas
    lookup_table = fix_lookup(lookup_table, marco_query)

    final = {}
    print("Formando arquivo final...")
    for qid, query in tqdm(lookup_table.items()):
        answer = marco_answers[qid][0]
        wf_answer = marco_wfanswers[qid][0]
        final[qid] = {
            "query": query,
            "answer": answer if wf_answer == "[" else wf_answer,
        }

    print("Feito! Salvando...")
    with open("results/filtered_qna.json", "w") as finalfile:
        json.dump(final, finalfile)


if __name__ == "__main__":
    extract_questions()
