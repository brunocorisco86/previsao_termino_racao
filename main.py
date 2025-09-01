
import os
from src.forecaster import SiloForecaster

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
    # --- Fim da Configuração de Caminhos ---

    # Instancia e executa o previsor
    forecaster = SiloForecaster(
        sensores_path=sensores_path,
        linhagem_folder=linhagem_folder,
        reports_folder=reports_folder
    )
    forecaster.run()
