# Chatbot-Victor-Paulo

Código baseado em https://github.com/C4AI/blab-filter-msmarco, que parte dos intents e diálogos originais, mas com modificações para maior fluidez e adição de intents até o número 386, de acordo com a seção 5.

### Instalação do projeto e atualização de intents:

#### 1. Clonar git 

`git clone`

#### 2. Abrir o arquivo `Perguntas.xlsx` no diretório \results

#### 3. Atualizar a lista de intents respeitando as regras de estruturação

#### 4. Executar o programa `generate_skill.py` contido em \src

Esse programa gera, em \results, o arquivo 'skill-Amazônia-Azul2.JSON', que deve ser inserido na interface do Watson (https://cloud.ibm.com/) em Dialog/options/Upload/Download/Upload
