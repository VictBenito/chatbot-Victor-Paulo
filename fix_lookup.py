# @Time:   30/06/2021
# @Author: Gabriel O.

import json
from tqdm import tqdm


def fix_lookup(lookup):
    """
    Por algum motivo, a lookup table não anotou corretamente o query id de cada query capturada.
    Então, para cada query presente na lookup table, iteramos sobre as queries do arquivo original
    até encontrar o id correto.

    :param lookup:
    :return:
    """
    new_lookup = {}
    print('Consertando lookup! ~1min')
    for l_index, l_query in tqdm(lookup['Doc'].items()):
        real_key = next(m_index for m_index, m_query in marco_query.items() if m_query == l_query)
        new_lookup[real_key] = l_query
    return new_lookup


if __name__ == '__main__':
    # Ler os diferentes jsons (queries, answers, well formed answers)
    with open('data/train_v2.1_query.json', 'r') as marco_query:
        marco_query = json.load(marco_query)

    with open('data/train_v2.1_answers.json', 'r') as marco_answers:
        marco_answers = json.load(marco_answers)

    with open('data/train_v2.1_wellFormedAnswers.json', 'r') as marco_wfanswers:
        marco_wfanswers = json.load(marco_wfanswers)

    with open('results/lookup_table.json', 'r') as lookupfile:
        lookup_table = json.load(lookupfile)

    # substituir chaves pelas corretas
    lookup_table = fix_lookup(lookup_table)

    final = {}
    print('Formando arquivo final...')
    for qid, query in tqdm(lookup_table.items()):
        temp = {
            'query':            query,
            'answer':           marco_answers[qid][0],
            'wellFormedAnswer': marco_wfanswers[qid][0]
        }
        final[qid] = temp

    print('Feito! Salvando...')
    with open('results/filtered_qna.json', 'w') as finalfile:
        json.dump(final, finalfile)

