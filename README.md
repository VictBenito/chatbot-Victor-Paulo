# blab-filter-msmarco
Código para selecionar por tema entre as mais de 800.000 perguntas no dataset MS MARCO, da Microsoft, e construir um chatbot Watson Assistant, da IBM, a partir de uma planilha de perguntas e respostas.

## Sentence Transformers.ipynb
Na seção 3 (Extraindo apenas queries do MS MARCO), apenas as perguntas são extraídas do json original do MS MARCO e salvas em um arquivo de texto (queries.txt). Na seção 4 (Topic modelling with BERT), as perguntas são lidas do txt e passadas de volta para string (isso foi feito, pois acelera o proceso de leitura). Então, são extraídos os embeddings das perguntas (representação vetorial) e eles são reduzidos através do método UMAP, passando de 768 parâmetros para apenas 5 por pergunta. Esses valores são salvos em um arquivo de texto para poder acessá-los rapidamente no futuro. Com a biblioteca HDBSCAN, são obtidos clusteres de perguntas através dos embeddings. Na parte de análise de resultados, cada tópico (cluster) é analisado e suas 10 palavras mais representativas são escolhidas. Depois, dentre essas palavras, são procuradas palavras chave (como "ocean" e "marine"). Em um loop, são impressas as top 10 palavras de cada cluster que possui entre elas pelo menos uma das palavras chave. Os clusteres relevantes são salvos no arquivo pre_lookup_table.json, no formato de um dicionário {id_da_pergunta: pergunta}.

## extract_questions.py
Pega o resultado do notebook, conserta a lookup_table (vide código) e cria um dicionário de perguntas e respostas, usando a well formed answer sempre que possível. Salva o dicionário no arquivo filtered_qna.json.

## choose_questions.py
Permite manualmente filtrar e rotular as perguntas do filtered_qna.json (que foram traduzidas e salvas na planilha Perguntas.xlsx, na aba filtered_qna_manual_sorted). Em um loop, uma pergunta e sua resposta são impressos no terminal e o usuário digita uma sequência de comandos, decidindo se a pergunta será mantida e a quais categorias (tags) ela pertence. O resultado é salvo na página "editadas".
