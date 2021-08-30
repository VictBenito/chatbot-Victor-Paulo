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
        print(f"Original: {row['original']}\nPergunta: {row['pergunta']}")
        # tentar obter input do usuário até ele digitar algo válido
        while True:
            input_sequence = input("-- ")
            if input_sequence == "":
                df.loc[i, "chatbot?"] = 0
                i += 1
                break
            elif input_sequence in ("h", "help"):
                print(
                    "Comandos disponíveis:\n"
                    "help (h): mostra esse texto\n"
                    "back (b): volta para a pergunta anterior\n"
                    "save (s): encerra e salva as mudanças\n"
                    "tags (t): mostra as tags disponíveis"
                )
                df.loc[i - 1, "chatbot?"] = -1
                i -= 1
                break
            elif input_sequence in ("b", "back"):
                df.loc[i - 1, "chatbot?"] = -1
                i -= 1
                break
            elif input_sequence in ("s", "save"):
                salvar = input("Salvar? s/n") == "s"
                if salvar:
                    with pd.ExcelWriter(
                        "results/Perguntas.xlsx",
                        mode="a",
                        engine="openpyxl",
                        if_sheet_exists="replace",
                    ) as writer:
                        df.to_excel(writer, sheet_name="edited", index=False)
                        print("Salvo!")
                return
            elif input_sequence in ("t", "tags"):
                print("Tags disponíveis:", tag_cols)
                continue
            inputs = input_sequence.split(",")
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
                    adicionar_tag = input("Adicionar a tag? s/n").lower().strip() == "s"
                    if adicionar_tag:
                        df.loc[i, "tag_" + tag] = 1
            df.loc[i, "chatbot?"] = chatbot
            i += 1
            break


if __name__ == "__main__":
    main()
