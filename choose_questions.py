# Filter-MSMARCO
# @File:   choose_questions.py
# @Time:   25/08/2021
# @Author: Gabriel O.

import pandas as pd


def main():
    df = pd.read_excel("results/Perguntas.xlsx", "edited", dtype=str)
    df = df.fillna("")
    tag_cols = [t.split("_", 1)[1] for t in df.columns if t.find("tag_") > -1]
    i = 0
    # iterar sobre as perguntas
    while True:
        row = df.loc[i]
        if row["chatbot?"] and int(row["chatbot?"]) >= 0:
            # já preenchi
            i += 1
            continue
        print("Original:", row["original"])
        print("Pergunta:", row["pergunta"])
        # tentar obter input do usuário até ele digitar algo válido
        while True:
            inp = input("-- ")
            if inp == "":
                df.loc[i, "chatbot?"] = 0
                i += 1
                break
            elif inp == "b":
                df.loc[i, "chatbot?"] = -1
                i -= 1
                break
            elif inp == "s":
                salvar = input("Salvar? s/n") == "s"
                if salvar:
                    with pd.ExcelWriter(
                        "results/Perguntas.xlsx", mode="a", if_sheet_exists="replace"
                    ) as writer:
                        df.to_excel(writer, sheet_name="edited")
                return
            inputs = inp.split(",")
            inputs = list(map(lambda x: x.lower().strip(), inputs))
            try:
                chatbot = int(inputs[0])
            except ValueError:
                print("Digite no formato: código[, tags]")
                continue
            tags = inputs[1:]
            for tag in tags:
                if tag in tag_cols:
                    df.loc[i, "tag_" + tag] = 1
                else:
                    print("Tag não reconhecida:", tag)
            df.loc[i, "chatbot?"] = chatbot
            i += 1
            break


if __name__ == "__main__":
    main()
