# Filter-MSMARCO
# @File:   choose_questions.py
# @Time:   25/08/2021
# @Author: Gabriel O.

from textwrap import wrap

import pandas as pd

from utils import getInput, Buffer


def main():
    buffer = Buffer()
    df = pd.read_excel("results/Perguntas.xlsx", "editadas", dtype=str)
    df = df.fillna("")
    available_tags = [t.split("_", 1)[1] for t in df.columns if t.find("tag_") > -1]
    i = 0
    # iterar sobre as perguntas
    while True:
        row = df.loc[i]
        if row["chatbot?"] and int(row["chatbot?"]) >= 0:
            # já preenchi
            i += 1
            continue
        # printar as tags disponíveis
        formatted_tags = wrap(str(available_tags), width=90)
        for j, line in enumerate(formatted_tags):
            if j > 0:
                formatted_tags[j] = "                   " + line
        formatted_tags = "\n".join(formatted_tags)
        buffer.add(
            f"Tags disponíveis: {formatted_tags}\n"
            f"Original: {row['original']}\n"
            f"Pergunta: {row['pergunta']}"
        )
        buffer.print()
        # tentar obter input do usuário até ele digitar algo válido
        while True:
            input_sequence = input("-- ")
            if input_sequence == "":
                df.loc[i, "chatbot?"] = 0
                i += 1
                break
            elif input_sequence in ("h", "help"):
                buffer.print(
                    "Comandos disponíveis:\n"
                    "help (h): mostra esse texto\n"
                    "back (b): volta para a pergunta anterior\n"
                    "save (s): encerra e salva as mudanças"
                )
                df.loc[i - 1, "chatbot?"] = -1
                i -= 1
                break
            elif input_sequence in ("b", "back"):
                df.loc[i - 1, "chatbot?"] = -1
                i -= 1
                break
            elif input_sequence in ("s", "save"):
                save_df(df)
                buffer.print("\nSalvo!")
                return
            inputs = input_sequence.split(",")
            inputs = list(map(lambda x: x.lower().strip(), inputs))
            try:
                chatbot = int(inputs[0])
            except ValueError:
                buffer.print("Digite no formato: código[, tags]")
                continue
            tags = inputs[1:]
            for tag in tags:
                if tag not in available_tags:
                    if getInput(f"Tag não reconhecida: {tag}\nAdicionar a tag?"):
                        available_tags += [tag]
                    else:
                        continue
                df.loc[i, "tag_" + tag] = 1
            df.loc[i, "chatbot?"] = chatbot
            i += 1
            break
        if i >= len(df):
            buffer.print("Chegou ao fim do documento!")
            save_df(df)
            break


def save_df(df: pd.DataFrame):
    if getInput("Salvar?"):
        with pd.ExcelWriter(
            "results/Perguntas.xlsx",
            mode="a",
            engine="openpyxl",
            if_sheet_exists="replace",
        ) as writer:
            df.to_excel(writer, sheet_name="editadas", index=False)


if __name__ == "__main__":
    main()
