import json

"""
Script para filtrar mais uma vez, de forma manual, os resultados filtrados
por temas.
"""

if __name__ == '__main__':
    with open('results/filtered_qna.json', 'rb') as f:
        filtered = json.load(f)

    skip = ['hemp', 'canola', 'cbd', 'car', 'tanker', 'salt lake', 'argan', 'town', 'color',
            'castor', 'synthetic', 'oil change', 'change oil', 'uss', 'almond', 'bergamot',
            'essential', 'texas', 'tide pod', 'api', 'oregano', 'of the seas']
    always_keep = ['turtle', 'sea wall']
    new_json = {}

    for i, (question_id, question_dict) in enumerate(filtered.items()):
        should_skip = False
        for word in skip:
            if question_dict['query'].lower().find(word) >= 0:
                should_skip = True
                break

        if should_skip:
            continue

        new_question_dict = {'query': question_dict['query']}
        wfa = question_dict['wellFormedAnswer']
        new_question_dict['answer'] = question_dict['answer'] if wfa == '[' else wfa

        keep = False
        for word in always_keep:
            if question_dict['query'].find(word) >= 0:
                keep = True
                break
        if not keep:
            print(f"Pergunta #{i}")
            print('Query: ', new_question_dict['query'])
            print('Answer:', new_question_dict['answer'])
            keep = input('Manter? ') == 'y'
        if keep:
            new_json[question_id] = new_question_dict

    with open('filtered_qna_.json', 'w') as f:
        json.dump(new_json, f)

    # how far can a nation claim in the sea
    # why are rising sea levels a problem
    # what resources do we use the ocean for
