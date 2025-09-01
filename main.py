import os
import pandas as pd
from datetime import date
from src.forecaster import SiloForecaster
from src.data_handler import importar_sensores

if __name__ == "__main__":
    # --- Configuração de Caminhos ---
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        script_dir = os.getcwd()

    project_root = os.path.abspath(script_dir)
    sensores_path = os.path.join(project_root, 'assets', 'Sensores.csv')
    linhagem_folder = os.path.join(project_root, 'static', 'linhagem')
    reports_folder = os.path.join(project_root, 'reports')
    os.makedirs(reports_folder, exist_ok=True) # Garante que a pasta de relatórios exista
    # --- Fim da Configuração de Caminhos ---

    # --- Carregar Dados ---
    print(f"Carregando dados de sensores de '{sensores_path}'...")
    try:
        df_sensores_completo = importar_sensores(sensores_path)
        print("Dados carregados com sucesso.")
    except FileNotFoundError:
        print(f"Erro: Arquivo '{sensores_path}' não encontrado.")
        exit()
    except Exception as e:
        print(f"Ocorreu um erro ao carregar os dados: {e}")
        exit()

    # --- Processar Dados Iniciais ---
    if 'collector' not in df_sensores_completo.columns:
        print("Erro: O arquivo CSV carregado não contém a coluna 'collector'. Verifique o formato do arquivo.")
        exit()

    df_sensores_completo['aviario_num'] = pd.to_numeric(df_sensores_completo['collector'].str.extract('(\d+)', expand=False), errors='coerce')
    df_sensores_completo.dropna(subset=['aviario_num'], inplace=True)
    df_sensores_completo['aviario_num'] = df_sensores_completo['aviario_num'].astype(int)
    aviarios_disponiveis = sorted(df_sensores_completo['aviario_num'].unique())

    # --- Coletar Inputs do Usuário ---
    print("\n--- Parâmetros de Entrada ---")
    print(f"Aviários disponíveis: {aviarios_disponiveis}")
    
    aviario_selecionado = None
    while aviario_selecionado not in aviarios_disponiveis:
        try:
            aviario_selecionado = int(input("Selecione o Aviário: "))
            if aviario_selecionado not in aviarios_disponiveis:
                print("Aviário inválido. Por favor, escolha um da lista.")
        except ValueError:
            print("Entrada inválida. Por favor, insira um número.")

    data_alojamento = None
    while data_alojamento is None:
        try:
            data_alojamento_str = input("Data de Alojamento (AAAA-MM-DD): ")
            data_alojamento = date.fromisoformat(data_alojamento_str)
        except ValueError:
            print("Formato de data inválido. Use AAAA-MM-DD.")

    linhagem = None
    while linhagem not in ["cobb", "ross"]:
        linhagem = input("Selecione a Linhagem (cobb/ross): ").lower()
        if linhagem not in ["cobb", "ross"]:
            print("Linhagem inválida. Escolha 'cobb' ou 'ross'.")

    n_aves = None
    while n_aves is None:
        try:
            n_aves = int(input("Número de Aves: "))
        except ValueError:
            print("Entrada inválida. Por favor, insira um número inteiro.")

    print("\nExecutando projeção...")

    # --- Executar Projeção ---
    try:
        forecaster = SiloForecaster(
            df_sensores=df_sensores_completo,
            linhagem_folder=linhagem_folder,
            reports_folder=reports_folder
        )
        
        report_string, plot_fig = forecaster.run_forecast(
            aviario_selecionado=aviario_selecionado,
            data_alojamento=data_alojamento,
            linhagem=linhagem,
            n_aves=n_aves
        )

        print("\n--- Projeção Concluída ---")
        print(report_string)

        # --- Salvar Resultados ---
        plot_filename = f"forecast_aviario_{aviario_selecionado}_{date.today()}.png"
        plot_path = os.path.join(reports_folder, plot_filename)
        plot_fig.savefig(plot_path)
        print(f"\nGráfico salvo em: {plot_path}")

    except Exception as e:
        print(f"\nOcorreu um erro durante a projeção: {e}")