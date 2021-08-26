# Filter-MSMARCO
# @File:   choose_questions.py
# @Time:   25/08/2021
# @Author: Gabriel O.

import pandas as pd


def main():
    df = pd.read_excel('results/Perguntas.xlsx', 'edited', dtype=str)
    df = df.fillna('')
    tag_cols = [t.split('_', 1)[1] for t in df.columns if t.find('tag_') > -1]
    for i, row in df.iterrows():
        if row['chatbot?'] and int(row['chatbot?']) >= 0:
            # já preenchi
            continue
        print('Original:', row['original'])
        print('Pergunta:', row['pergunta'])
        while True:
            inp = input('-- ')
            if inp == '':
                df.loc[i, 'chatbot?'] = 0
                break
            inputs = inp.split(',')
            inputs = list(map(lambda x: x.lower().strip(), inputs))
            try:
                chatbot = int(inputs[0])
            except ValueError:
                print('Digite no formato: código[, tags]')
                continue
            tags = inputs[1:]
            for tag in tags:
                if tag in tag_cols:
                    df.loc[i, tag_cols[tag]] = 1
                else:
                    print('Tag não reconhecida:', tag)
            df.loc[i, 'chatbot?'] = chatbot
            break


if __name__ == '__main__':
    main()
