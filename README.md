# 🐔 Silo Feed Forecaster

Um sistema inteligente para análise e projeção da autonomia de ração em silos de aviários, ajudando a otimizar a gestão de estoque e evitar rupturas na alimentação.

## ✨ Funcionalidades

- **Análise Histórica:** Processa dados de sensores de peso para construir um histórico de consumo.
- **Fator de Consumo Real:** Calcula a taxa de consumo real do lote e a compara com a tabela padrão da linhagem (Cobb/Ross), gerando um "fator de consumo" que ajusta a projeção à realidade do campo.
- **Projeção Inteligente:** Estima a data e a hora em que a ração do silo irá acabar, com base no consumo real e na curva de consumo padrão.
- **Detecção de Entregas:** Identifica automaticamente os eventos de reabastecimento de ração no silo.
- **Relatórios Completos:** Gera um relatório em PDF com as principais métricas de autonomia e um gráfico com a curva de esvaziamento projetada.
- **Interface Interativa:** Coleta os dados do lote (aviário, data de alojamento, linhagem e número de aves) de forma interativa através de diálogos simples.

## ⚙️ Como Funciona

O fluxo de operação é o seguinte:

1.  **Coleta de Dados:** O sistema solicita ao usuário as informações essenciais do lote.
2.  **Processamento de Dados:** Ele importa e limpa os dados brutos dos sensores de peso (`Sensores.csv`).
3.  **Cálculo de Consumo:** A taxa de consumo por hora é calculada, e o "fator de consumo" do lote é estabelecido.
4.  **Projeção:** Utilizando o peso atual, a projeção da linhagem (`cobb.xlsx` ou `ross.xlsx`) e o fator de consumo, o sistema projeta o esvaziamento do silo hora a hora.
5.  **Geração de Saídas:** Um relatório final e um gráfico são gerados e salvos na pasta `reports`.

## 📋 Pré-requisitos

- Python 3.8 ou superior.

## 🚀 Instalação

1.  Clone este repositório.
2.  Crie e ative um ambiente virtual:
    ```bash
    python -m venv .venv
    .venv/Scripts/activate  # Windows
    # source .venv/bin/activate  # macOS/Linux
    ```
3.  Instale as dependências:
    ```bash
    pip install -r requirements.txt
    ```

## 📂 Estrutura de Dados de Entrada

Para que o sistema funcione, os seguintes arquivos devem estar presentes:

-   `assets/Sensores.csv`: Arquivo com os dados dos sensores. Deve conter as colunas `Date`, `Hour`, `Collector`, `Channel` e `Value`.
-   `static/linhagem/cobb.xlsx` e `static/linhagem/ross.xlsx`: Tabelas de consumo padrão para cada linhagem, contendo as colunas `dia de vida` e `consumo`.

### Obtendo os Dados do eProdutor

Para extrair o arquivo `Sensores.csv` da plataforma eProdutor, siga os passos:

1.  Abra o aplicativo **eProdutor**.
2.  Selecione **'Sensores'** na barra lateral principal.
    ![Passo 2](images/2%20-%20Sensores.png)
3.  Na barra lateral acessória, selecione **'Monitoramento'**.
    ![Passo 3](images/3%20-%20Monitoramento.png)
4.  Clique no ícone de filtro (laranja, no canto inferior direito).
    ![Passo 4](images/4%20-%20filtro.png)
5.  Em **Grandeza**, selecione **'PESO DO SILO'**.
    ![Passo 5](images/5%20-%20Peso%20do%20silo.png)
6.  Filtre os últimos **15 dias** em 'Data Inicial' e 'Data Final'.
    ![Passo 6](images/6%20-%20filtro%20data.png)
7.  Clique em **'BUSCAR'**.
    ![Passo 7](images/7%20-%20Buscar.png)
8.  Clique no botão **'Exportar CSV'** e salve o arquivo dentro da pasta `assets`.
    ![Passo 8](images/8%20-%20Exportar%20CSV.png)

## ▶️ Execução

Para iniciar a análise, execute o seguinte comando na raiz do projeto:

```bash
python main.py
```

O programa abrirá janelas de diálogo para solicitar as informações necessárias.

## 📊 Estrutura de Saída

Os resultados são salvos na pasta `reports/`:

-   `relatorio_final_aviario_[...].pdf`: Um relatório detalhado com o peso atual, a autonomia estimada em dias e horas, a data prevista de esgotamento e um histórico de entregas de ração.
-   `projecao_aviario_[...].pdf`: Um gráfico visual mostrando o histórico de peso do silo e a curva de projeção de esvaziamento.