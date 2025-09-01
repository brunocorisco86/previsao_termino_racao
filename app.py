import streamlit as st
import pandas as pd
from src.data_handler import importar_sensores, importar_consumo
from src.forecaster import SiloForecaster
import os
from datetime import date
import traceback
import matplotlib.pyplot as plt
import re
from src.report_generator import PDFReportGenerator

# --- Page Config ---
st.set_page_config(
    page_title="Forecast Peso Silo",
    page_icon="🐔",
    layout="wide"
)

# --- Cached Data Loading ---
@st.cache_data
def load_sensor_data(uploaded_file):
    df = importar_sensores(uploaded_file)
    return df

# --- Cached Consumption Data Loading ---
@st.cache_data
def load_consumption_data(linhagem_folder):
    # Assuming 'cobb.xlsx' and 'ross.xlsx' are always in 'static/linhagem'
    # and are part of the deployed app or pre-loaded.
    # If they were to be uploaded by the user, this function would need adaptation.
    cobb_path = os.path.join(linhagem_folder, 'cobb.xlsx')
    ross_path = os.path.join(linhagem_folder, 'ross.xlsx')
    
    # For Streamlit deployment, these paths might need to be relative to the app.py
    # or handled differently if they are not bundled with the app.
    # For now, assuming they are accessible via the relative path.
    
    # This part needs to be robust for deployment. 
    # For local testing, it works if static/linhagem is in the project root.
    
    # A more robust solution for Streamlit Cloud would be to use st.secrets or 
    # allow user to upload these files too, but that's a later enhancement.
    
    # For now, let's assume the static folder is accessible relative to the app.py
    # or the script's execution directory.
    
    # Let's define the absolute path for the static folder
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(script_dir)
    linhagem_folder_abs = os.path.join(project_root, 'static', 'linhagem')

    df_cobb = importar_consumo('cobb', linhagem_folder_abs)
    df_ross = importar_consumo('ross', linhagem_folder_abs)
    return {'cobb': df_cobb, 'ross': df_ross}

# --- Title ---
st.title("🐔 Forecast Peso Silo")
st.write("Esta aplicação analisa o consumo de ração de um silo e projeta a sua autonomia.")

# --- Sidebar for Inputs ---
st.sidebar.header("Parâmetros de Entrada")

uploaded_file = st.sidebar.file_uploader(
    "Carregue aqui o seu arquivo `Sensores.csv`",
    type=['csv']
)

# Define project_root and reports_folder for SiloForecaster
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(script_dir)
reports_folder = os.path.join(project_root, 'reports')
linhagem_folder = os.path.join(project_root, 'static', 'linhagem')

if uploaded_file is not None:
    st.sidebar.success("Arquivo carregado!")
    
    df_sensores_completo = load_sensor_data(uploaded_file)
    
    # Ensure 'Collector' column exists before proceeding
    if 'collector' not in df_sensores_completo.columns:
        st.error("O arquivo CSV carregado não contém a coluna 'Collector' ou 'Coletor'. Verifique o formato do arquivo.")
        st.stop()

    df_sensores_completo['aviario_num'] = pd.to_numeric(df_sensores_completo['collector'].str.extract('(\d+)', expand=False), errors='coerce')
    df_sensores_completo.dropna(subset=['aviario_num'], inplace=True)
    df_sensores_completo['aviario_num'] = df_sensores_completo['aviario_num'].astype(int)
    
    aviarios_disponiveis = sorted(df_sensores_completo['aviario_num'].unique())

    # --- Get other inputs ---
    st.sidebar.subheader("Informações do Lote")

    aviario_selecionado = st.sidebar.selectbox(
        "Selecione o Aviário",
        options=aviarios_disponiveis
    )

    data_alojamento = st.sidebar.date_input(
        "Data de Alojamento",
        value=None # Let user select, or provide a sensible default if possible
    )

    linhagem = st.sidebar.selectbox(
        "Selecione a Linhagem",
        options=["cobb", "ross"]
    )

    n_aves = st.sidebar.number_input(
        "Número de Aves",
        min_value=0,
        value=25000
    )

    if st.sidebar.button("Executar Projeção"):
        if data_alojamento is None:
            st.error("Por favor, selecione a Data de Alojamento.")
        else:
            try:
                # Instantiate and run the forecaster
                forecaster = SiloForecaster(
                    df_sensores=df_sensores_completo, 
                    linhagem_folder=linhagem_folder, 
                    reports_folder=reports_folder
                )
                
                report_string, plot_fig = forecaster.run_forecast(
                    aviario_selecionado=aviario_selecionado,
                    data_alojamento=data_alojamento,
                    linhagem=linhagem,
                    n_aves=n_aves # Use o número de aves original
                )

                st.success("Projeção concluída com sucesso!")

                # Display Metrics (extracted from report_string or calculated here)
                # For now, let's parse from report_string as it's already formatted
                
                # Example parsing (this can be made more robust)
                peso_atual_match = re.search(r"- Peso Atual no Silo: (\d+\.\d{2}) kg", report_string)
                autonomia_match = re.search(r"- Autonomia Estimada: (\d+) dias e (\d+) horas", report_string)
                esgotamento_match = re.search(r"- Data Estimada de Esgotamento: (.*)", report_string)

                col1, col2, col3 = st.columns(3)
                with col1:
                    if peso_atual_match: st.metric("Peso Atual no Silo", f"{peso_atual_match.group(1)} kg")
                with col2:
                    if autonomia_match: st.metric("Autonomia Estimada", f"{autonomia_match.group(1)} dias e {autonomia_match.group(2)} horas")
                with col3:
                    if esgotamento_match: st.metric("Data de Esgotamento", esgotamento_match.group(1))

                st.markdown("## Resultados Detalhados")
                tab1, tab2, tab3 = st.tabs(["Gráfico de Projeção", "Relatório Completo", "Dados Processados"]) # Added tab3

                with tab1:
                    st.pyplot(plot_fig)
                    plt.close(plot_fig) # Close the figure to free memory

                with tab2:
                    st.markdown(report_string)
                    # If you want to display the deliveries table separately, you'd need to return it from forecaster
                    # For now, it's part of the markdown string.

                with tab3:
                    st.subheader("Dados Horários Processados")
                    st.dataframe(forecaster.df_hourly) # Access the processed dataframe from the forecaster instance

            except Exception as e:
                st.error(f"Ocorreu um erro durante a projeção: {e}")
                st.exception(e) # Display full traceback for debugging

    st.markdown("---")
    st.subheader("Gerar Relatório PDF Completo")
    if st.button("Gerar Relatório PDF Completo"):
        if data_alojamento is None:
            st.error("Por favor, selecione a Data de Alojamento para gerar o relatório completo.")
        else:
            with st.spinner("Gerando relatório PDF para todos os aviários..."):
                forecaster_instances_for_pdf = {}
                for av_num in aviarios_disponiveis:
                    try:
                        # Create a new forecaster instance for each aviary
                        # This ensures each aviary's data is processed independently
                        temp_forecaster = SiloForecaster(
                            df_sensores=df_sensores_completo, 
                            linhagem_folder=linhagem_folder, 
                            reports_folder=reports_folder
                        )
                        # Run forecast for the current aviary using the selected parameters
                        temp_forecaster.run_forecast(
                            aviario_selecionado=av_num,
                            data_alojamento=data_alojamento, # Using the selected date for all
                            linhagem=linhagem,               # Using the selected lineage for all
                            n_aves=n_aves                    # Using the selected n_aves for all
                        )
                        forecaster_instances_for_pdf[av_num] = temp_forecaster
                    except Exception as e:
                        st.warning(f"Não foi possível gerar o relatório para o aviário {av_num}: {e}")
                        # Continue to next aviary even if one fails

                if forecaster_instances_for_pdf:
                    pdf_generator = PDFReportGenerator()
                    # Pass the dictionary of forecaster instances
                    pdf_generator.generate_full_report(forecaster_instances_for_pdf, "relatorio_completo_granja.pdf")
                    
                    with open("relatorio_completo_granja.pdf", "rb") as pdf_file:
                        st.download_button(
                            label="Baixar Relatório PDF",
                            data=pdf_file,
                            file_name="relatorio_completo_granja.pdf",
                            mime="application/pdf"
                        )
                    st.success("Relatório PDF gerado com sucesso!")
                else:
                    st.error("Nenhum relatório pôde ser gerado para os aviários selecionados.")

else:
    st.info("Por favor, carregue o arquivo `Sensores.csv` na barra lateral para começar.")
    st.markdown("---")
    st.subheader("Como obter os dados do eProdutor")
    st.image("images/2 - Sensores.png", caption="1. Na barra lateral, selecione 'Sensores'", width=300)
    st.image("images/3 - Monitoramento.png", caption="2. Em seguida, selecione 'Monitoramento'", width=300)
    st.image("images/4 - filtro.png", caption="3. Clique no filtro laranja", width=150)