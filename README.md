# 🐔 Silo Feed Forecaster

Um sistema inteligente para análise e projeção da autonomia de ração em silos de aviários, ajudando a otimizar a gestão de estoque, evitar rupturas na alimentação e planejar a entrega final de ração para o abate.

## ✨ Funcionalidades

- **Análise Histórica:** Processa dados de sensores de peso para construir um histórico de consumo.
- **Fator de Consumo Real:** Calcula a taxa de consumo real do lote e a compara com a tabela padrão da linhagem (Cobb/Ross), gerando um "fator de consumo" que ajusta a projeção à realidade do campo.
- **Projeção de Autonomia:** Estima a data e a hora em que a ração do silo irá acabar, com base no consumo real e na curva de consumo padrão.
- **Projeção para o Abate:**
    - Calcula a quantidade exata de ração necessária para finalizar o lote, visando um saldo zero no silo no momento do início do jejum pré-abate.
    - Simula a entrega final de ração em um gráfico interativo, mostrando o aumento de saldo no silo e a curva de consumo até o esvaziamento completo no momento certo.
- **Detecção de Entregas:** Identifica automaticamente os eventos de reabastecimento de ração no silo.
- **Relatórios Completos:** Gera um relatório em PDF para download com as principais métricas de todos os aviários da granja.
- **Interface Interativa:** Uma aplicação web amigável para carregar dados, inserir parâmetros e visualizar os resultados em tempo real.

## ⚙️ Como Funciona

O fluxo de operação é o seguinte:

1.  **Carregamento de Dados:** O usuário carrega o arquivo `Sensores.csv` através da interface web.
2.  **Definição de Parâmetros:** Na barra lateral, o usuário informa os dados do lote (aviário, data de alojamento, linhagem, nº de aves) e, opcionalmente, os dados para o abate (data, hora e tempo de jejum).
3.  **Execução da Análise:**
    - Ao clicar em **"Executar Projeção"**, o sistema analisa a autonomia do silo.
    - Ao clicar em **"Calcular Ração para Abate"**, o sistema projeta a necessidade de ração para fechar o lote.
4.  **Visualização de Resultados:** As métricas, relatórios e gráficos são exibidos diretamente na interface, em abas organizadas.

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
8.  Clique no botão **'Exportar CSV'** e salve o arquivo. Você irá carregá-lo na interface da aplicação.
    ![Passo 8](images/8%20-%20Exportar%20CSV.png)

## ▶️ Execução

Para iniciar a aplicação, execute o seguinte comando na raiz do projeto:

```bash
streamlit run app.py
```

A aplicação será aberta automaticamente no seu navegador web.

## 📊 Estrutura de Saída

Os resultados são exibidos diretamente na interface da aplicação:

-   **Métricas Principais:** Cartões com o peso atual, idade do lote, autonomia estimada e data de esgotamento.
-   **Gráfico de Projeção:** Um gráfico visual mostrando o histórico de peso do silo e a curva de projeção de esvaziamento.
-   **Projeção para Abate:** Uma aba dedicada mostra o relatório de necessidade de ração e o gráfico que simula a última entrega e o consumo até o jejum.
-   **Download de Relatório:** Um botão permite gerar e baixar um relatório consolidado em PDF para toda a granja.
