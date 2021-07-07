import json

"""
Script para filtrar mais uma vez, de forma manual, os resultados filtrados
por temas.
"""

with open('filtered_qna.json', 'rb') as f:
    filtered = json.load(f)

skip = ['hemp', 'canola', 'cbd', 'car', 'tanker', 'salt lake', 'argan', 'town', 'color',
        'castor', 'synthetic', 'oil change', 'change oil', 'uss', 'almond', 'bergamot',
        'essential', 'texas', 'tide pod', 'api', 'oregano', 'of the seas']
always_keep = ['turtle', 'sea wall']
new = {}
for i, (qid, qaw) in enumerate(filtered.items()):
    if i > 1200:
        break

    should_continue = False
    for word in skip:
        if qaw['query'].lower().find(word) >= 0:
            should_continue = True
            break

    if should_continue:
        continue

    newqaw = {'query': qaw['query']}
    wfa = qaw['wellFormedAnswer']
    newqaw['answer'] = wfa if wfa != '[' else qaw['answer']

    keep = False
    for word in always_keep:
        if qaw['query'].find(word) >= 0:
            keep = True
            break
    if not keep:
        print(f"Pergunta #{i}")
        print('Query: ', newqaw['query'])
        print('Answer:', newqaw['answer'])
        keep = input('Manter? ') == 'y'
    if keep:
        new[qid] = newqaw

with open('filtered_qna_.json', 'w') as f:
    json.dump(new, f)


oops = ['how far can a nation claim in the sea', 'why are rising sea levels a problem',
        'what resources do we use the ocean for']