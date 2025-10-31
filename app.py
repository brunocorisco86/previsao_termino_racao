import streamlit as st
import pandas as pd
from src.data_handler import importar_sensores, importar_consumo
from src.forecaster import SiloForecaster
import os
from datetime import date, datetime
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

    df_sensores_completo['aviario_num'] = pd.to_numeric(df_sensores_completo['collector'].str.extract(r'(\d+)', expand=False), errors='coerce')
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

    st.sidebar.subheader("Parâmetros de Sobra de Ração")
    idade_diluicao_start = st.sidebar.number_input(
        "Idade de Diluição da Sobra (dias)",
        min_value=0,
        value=19,
        help="A sobra de ração será considerada até esta idade do lote."
    )
    sobra_inicial_kg = st.sidebar.number_input(
        "Sobra Inicial de Ração (kg)",
        min_value=0.0,
        value=0.0, # Default to 0, will be updated if conditions met
        help="Valor de ração remanescente do lote anterior. Será preenchido automaticamente se detectado."
    )

    st.sidebar.subheader("Parâmetros do Abate")
    data_abate = st.sidebar.date_input(
        "Data do Abate",
        value=None
    )
    hora_abate = st.sidebar.time_input(
        "Hora do Abate",
        step=1800
    )
    jejum_horas = st.sidebar.number_input(
        "Horas de Jejum",
        min_value=4,
        max_value=6,
        value=4
    )

    # --- Session State for Forecaster ---
    if 'forecaster' not in st.session_state:
        st.session_state.forecaster = None

    col1_sidebar, col2_sidebar = st.sidebar.columns(2)
    with col1_sidebar:
        if st.button("Executar Projeção"):
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
                    
                    report_string, plot_fig, df_entregas = forecaster.run_forecast(
                        aviario_selecionado=aviario_selecionado,
                        data_alojamento=data_alojamento,
                        linhagem=linhagem,
                        n_aves=n_aves,
                        idade_diluicao_start=idade_diluicao_start,
                        sobra_inicial_kg=sobra_inicial_kg
                    )
                    st.session_state.forecaster = forecaster # Save the instance
                    st.session_state.report_string = report_string
                    st.session_state.plot_fig = plot_fig
                    st.session_state.df_entregas = df_entregas

                except Exception as e:
                    st.error(f"Ocorreu um erro durante a projeção: {e}")
                    st.exception(e) # Display full traceback for debugging
    
    with col2_sidebar:
        if st.button("Calcular Ração para Abate"):
            if st.session_state.forecaster is None:
                st.error("Por favor, execute a projeção primeiro.")
            elif data_abate is None or hora_abate is None:
                st.error("Por favor, forneça a data e hora do abate.")
            else:
                try:
                    abate_datetime = datetime.combine(data_abate, hora_abate)
                    
                    # Call the new method
                    (abate_report, abate_plot, 
                     necessidade_racao, ultima_entrega_necessaria) = st.session_state.forecaster.calculate_abate_feed(
                        abate_datetime=abate_datetime,
                        jejum_horas=jejum_horas
                    )
                    
                    st.session_state.abate_report = abate_report
                    st.session_state.abate_plot = abate_plot
                    st.session_state.necessidade_racao = necessidade_racao
                    st.session_state.ultima_entrega_necessaria = ultima_entrega_necessaria

                except Exception as e:
                    st.error(f"Ocorreu um erro no cálculo para o abate: {e}")
                    st.exception(e)

    if st.session_state.get('forecaster'):
        st.success("Projeção carregada.")

        # Display Metrics
        report_string = st.session_state.report_string
        plot_fig = st.session_state.plot_fig
        df_entregas = st.session_state.df_entregas
        
        peso_atual_match = re.search(r"- Peso Atual no Silo: (\d+\.\d{2}) kg", report_string)
        idade_atual_match = re.search(r"- Idade Atual do Lote: (\d+) dias", report_string)
        autonomia_match = re.search(r"- Autonomia Estimada: (\d+) dias e (\d+) horas", report_string)
        esgotamento_match = re.search(r"- Data Estimada de Esgotamento: (.*)", report_string)
        idade_esgotamento_match = re.search(r"- Idade Estimada de Esgotamento: (\d+) dias", report_string)

        col1, col2, col3 = st.columns(3)
        if peso_atual_match: col1.metric("Peso Atual no Silo", f"{peso_atual_match.group(1)} kg")
        if idade_atual_match: col2.metric("Idade Atual do Lote", f"{idade_atual_match.group(1)} dias")
        if autonomia_match: col3.metric("Autonomia Estimada", f"{autonomia_match.group(1)} dias e {autonomia_match.group(2)} horas")

        col4, col5 = st.columns(2)
        if esgotamento_match: col4.metric("Data de Esgotamento", esgotamento_match.group(1))
        if idade_esgotamento_match: col5.metric("Idade de Esgotamento", f"{idade_esgotamento_match.group(1)} dias")

        col6, = st.columns(1)
        if not df_entregas.empty:
            total_delivered_feed = df_entregas['quantidade_kg'].sum()
            col6.metric("Total Ração Entregue", f"{total_delivered_feed:,.0f} kg".replace(",", "."))

        st.markdown("## Resultados Detalhados")
        
        tab_titles = ["Gráfico de Projeção", "Relatório Completo", "Dados Processados"]
        if 'abate_report' in st.session_state:
            tab_titles.append("Projeção para Abate")
            
        tabs = st.tabs(tab_titles)
        
        with tabs[0]:
            st.pyplot(plot_fig)
            plt.close(plot_fig)

        with tabs[1]:
            st.markdown(report_string)

        with tabs[2]:
            st.subheader("Dados Horários Processados")
            st.dataframe(st.session_state.forecaster.df_hourly)

        if "Projeção para Abate" in tab_titles:
            with tabs[3]:
                st.subheader("Resultados do Cálculo para Abate")
                
                col1_abate, col2_abate, col3_abate = st.columns(3)
                
                peso_atual_silo = st.session_state.forecaster.df_hourly['peso_silo'].iloc[-1]
                col1_abate.metric("Posição Atual do Silo", f"{peso_atual_silo:,.2f} kg".replace(",", "."))
                
                col2_abate.metric("Necessidade de Ração até o Jejum", f"{st.session_state.necessidade_racao:,.2f} kg".replace(",", "."))
                
                col3_abate.metric("Última Entrega de Ração Necessária", f"{st.session_state.ultima_entrega_necessaria:,.2f} kg".replace(",", "."))

                st.markdown(st.session_state.abate_report)
                st.pyplot(st.session_state.abate_plot)
                plt.close(st.session_state.abate_plot)

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
                            n_aves=n_aves,                   # Using the selected n_aves for all
                            idade_diluicao_start=idade_diluicao_start,
                            sobra_inicial_kg=sobra_inicial_kg
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
