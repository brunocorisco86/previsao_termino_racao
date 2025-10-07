import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os

# Importa as funções dos outros módulos
from .data_handler import importar_consumo

class SiloForecaster:
    def __init__(self, df_sensores, linhagem_folder, reports_folder, idade_diluicao_start=19, sobra_inicial_kg=0.0):
        self.df_sensores = df_sensores
        self.linhagem_folder = linhagem_folder
        self.reports_folder = reports_folder
        self.idade_diluicao_start = idade_diluicao_start
        self.sobra_inicial_kg = sobra_inicial_kg
        
        # Atributos que serão preenchidos durante a execução
        self.df_hourly = None
        self.df_consumo = None
        self.forecast_series = None
        self.report_string = None
        self.plot_fig = None

    def run_forecast(self, aviario_selecionado, data_alojamento, linhagem, n_aves, idade_diluicao_start, sobra_inicial_kg):
        """Executa o pipeline completo de previsão com os dados fornecidos pelo Streamlit."""
        try:
            self.aviario_selecionado = aviario_selecionado
            self.data_alojamento = data_alojamento
            self.linhagem = linhagem
            self.n_aves = n_aves
            self.idade_diluicao_start = idade_diluicao_start
            self.sobra_inicial_kg = sobra_inicial_kg

            # Filtrar dados do aviário selecionado
            df_filtrado = self.df_sensores[self.df_sensores['aviario_num'] == self.aviario_selecionado].copy()
            if df_filtrado.empty:
                raise ValueError(f"Nenhum dado encontrado para o aviário {self.aviario_selecionado}.")

            self.df_consumo = importar_consumo(self.linhagem, self.linhagem_folder)

            # Preparar dados
            df_filtrado['idade'] = (df_filtrado.index.normalize() - pd.Timestamp(self.data_alojamento)).days + 1
            
            df_hourly = pd.DataFrame()
            resampled = df_filtrado.groupby('channel')['value'].resample('h').mean()
            df_hourly['peso_silo'] = resampled.unstack(level='channel').sum(axis=1)
            
            # Filtro para remover ruído de quedas abruptas para zero
            # Substitui 0 por NaN para interpolação
            df_hourly['peso_silo'].replace(0, np.nan, inplace=True)
            # Interpola os valores NaN, preenchendo no máximo 3 horas consecutivas
            df_hourly['peso_silo'].interpolate(method='linear', limit_direction='forward', limit=3, inplace=True)

            df_hourly.dropna(inplace=True)
            
            # Adicionar a coluna 'idade' ao df_hourly
            df_hourly['idade'] = (df_hourly.index.normalize() - pd.Timestamp(self.data_alojamento)).days + 1

            self.df_hourly = df_hourly

            # Calcular autonomia
            self._project_autonomy()

            # Gerar relatório e gráfico
            report_string, plot_fig, df_entregas = self._generate_report_and_plot()
            self.df_entregas = df_entregas # Store it for potential future use or direct access
            
            self.report_string = report_string
            self.plot_fig = plot_fig
            
            return report_string, plot_fig, df_entregas

        except Exception as e:
            # Em um app Streamlit, é melhor retornar a exceção para ser exibida pelo st.error
            raise e

    def _project_autonomy(self):
        """Calcula a taxa de consumo e projeta a autonomia."""
        self.df_hourly['consumo_real_kg'] = -self.df_hourly['peso_silo'].diff()
        consumos_validos = self.df_hourly['consumo_real_kg'][(self.df_hourly['consumo_real_kg'] > 0) & (self.df_hourly['consumo_real_kg'] < 500)]
        
        if consumos_validos.empty:
            raise ValueError("Não foi possível calcular uma taxa de consumo válida a partir dos dados. Verifique se há dados suficientes ou se os valores de peso estão corretos.")

        taxa_consumo_real_recente = consumos_validos.tail(24).mean()
        
        # Calcular a taxa de consumo real por ave por dia (em gramas/ave/dia)
        # taxa_consumo_real_recente está em kg/hora
        # Converter para gramas/ave/dia: (kg/hora * 1000 g/kg * 24 horas/dia) / n_aves
        taxa_consumo_real_recente_gr_ave_dia = (taxa_consumo_real_recente * 1000 * 24) / self.n_aves

        ultimo_peso = self.df_hourly['peso_silo'].iloc[-1]
        ultima_data = self.df_hourly.index[-1]
        idade_atual = self.df_hourly['idade'].iloc[-1] # Usar idade do df_hourly

        consumo_tabela_atual = self.df_consumo[self.df_consumo['idade'] == idade_atual]['consumo_gr_ave_dia']
        consumo_tabela_atual = consumo_tabela_atual.iloc[0] if not consumo_tabela_atual.empty else self.df_consumo['consumo_gr_ave_dia'].iloc[-1]

        # Calcular o fator de consumo baseado nas taxas por ave
        # Este fator indica o quanto o consumo real por ave se desvia do consumo por ave da tabela
        fator_consumo = taxa_consumo_real_recente_gr_ave_dia / consumo_tabela_atual

        pesos_projetados, datas_projetadas = [], []
        peso_atual = ultimo_peso
        
        # Apply initial deduction of leftover feed if applicable
        # This makes the silo virtually less until idade_diluicao_start
        if self.sobra_inicial_kg > 0:
            peso_atual -= self.sobra_inicial_kg

        sobra_added_back = False # Flag to ensure leftover is added back only once
        
        for hora in range(1, 24 * 30): # Projeta para 30 dias
            data_futura = ultima_data + timedelta(hours=hora)
            idade_futura = (data_futura.normalize().date() - self.data_alojamento).days + 1
            
            consumo_tabela_futuro = self.df_consumo[self.df_consumo['idade'] == idade_futura]['consumo_gr_ave_dia']
            consumo_tabela_futuro = consumo_tabela_futuro.iloc[0] if not consumo_tabela_futuro.empty else self.df_consumo['consumo_gr_ave_dia'].iloc[-1]

            consumo_projetado_kg_hr = (consumo_tabela_futuro / 1000 / 24) * self.n_aves * fator_consumo

            # Add back the leftover feed when idade_diluicao_start is reached
            if not sobra_added_back and self.sobra_inicial_kg > 0 and idade_futura >= self.idade_diluicao_start:
                peso_atual += self.sobra_inicial_kg
                sobra_added_back = True
            
            peso_atual -= consumo_projetado_kg_hr
            
            pesos_projetados.append(peso_atual)
            datas_projetadas.append(data_futura)

            if peso_atual <= 0: break
        
        self.forecast_series = pd.Series(pesos_projetados, index=datas_projetadas)

    def _detectar_entregas(self, df_hourly, threshold_kg=500):
        """Detecta e agrupa entregas de ração consecutivas."""
        df_hourly['mudanca_peso'] = df_hourly['peso_silo'].diff()
        entregas_raw = df_hourly[df_hourly['mudanca_peso'] > threshold_kg].copy()

        if entregas_raw.empty:
            return pd.DataFrame(columns=['Quantidade (kg)'], index=pd.Index([], name='Data da Entrega'))

        group_id = (entregas_raw.index.to_series().diff() > pd.Timedelta('1 hour')).cumsum()
        
        entregas_agrupadas = entregas_raw.groupby(group_id).agg(
            data_entrega=('mudanca_peso', 'idxmin'),
            quantidade_kg=('mudanca_peso', 'sum')
        )
        entregas_agrupadas.set_index('data_entrega', inplace=True)
        entregas_agrupadas.index.name = 'Data da Entrega'
        return entregas_agrupadas

    def _generate_report_and_plot(self):
        """Gera a string do relatório e o objeto do gráfico para o Streamlit."""
        df_entregas = self._detectar_entregas(self.df_hourly)
        
        initial_peso = self.df_hourly['peso_silo'].iloc[0] # Adicionado para a legenda
        zero_time = self.forecast_series.index[-1] if not self.forecast_series.empty else None
        autonomia_total = zero_time - self.df_hourly.index[-1] if zero_time else timedelta(days=0)
        dias = autonomia_total.days
        horas = autonomia_total.seconds // 3600
        
        report_header = f"""
        RELATÓRIO DE AUTONOMIA DE RAÇÃO
        ---------------------------------
        Data do Relatório: {datetime.now().strftime('%d/%m/%Y %H:%M')}
        Aviário Analisado: {self.aviario_selecionado}
        Linhagem: {self.linhagem.capitalize()}
        Número de Aves: {self.n_aves}
        """
        
        idade_atual = self.df_hourly['idade'].iloc[-1]
        idade_esgotamento = (zero_time.normalize().date() - self.data_alojamento).days + 1 if zero_time else 'N/A'

        report_kpis = f"""
        MÉTRICAS PRINCIPAIS
        ---------------------
        - Peso Atual no Silo: {self.df_hourly['peso_silo'].iloc[-1]:.2f} kg
        - Idade Atual do Lote: {idade_atual} dias
        - Autonomia Estimada: {dias} dias e {horas} horas
        - Data Estimada de Esgotamento: {zero_time.strftime('%d/%m/%Y %H:%M') if zero_time else 'N/A'}
        - Idade Estimada de Esgotamento: {idade_esgotamento} dias
        """

        report_entregas = "\nENTREGAS DE RAÇÃO DETECTADAS NO PERÍODO\n-----------------------------------------"
        if df_entregas.empty:
            report_entregas += "\nNenhuma entrega significativa (>500kg) foi detectada no período analisado."
        else:
            # Convert index to string for markdown table compatibility
            df_entregas_str = df_entregas.copy()
            df_entregas_str.index = df_entregas_str.index.strftime('%d/%m/%Y %H:%M')
            report_entregas += "\n" + df_entregas_str.to_markdown()

        final_report_string = f"{report_header}\n{report_kpis}\n{report_entregas}"

        # Gerar gráfico
        fig, ax = plt.subplots(figsize=(12, 7))
        ax.plot(self.df_hourly['peso_silo'], label=f'Histórico - Aviário {self.aviario_selecionado} (Início: {f"{initial_peso:,.0f}".replace(",", ".")} kg)', marker='o')
        ax.plot(self.forecast_series, label='Projeção de Esvaziamento', linestyle='--', color='red')
        
        if zero_time:
            ax.axvline(x=zero_time, color='r', linestyle=':', label=f'Previsão de Esgotamento: {zero_time.strftime("%d/%m %H:%M")}')

        # Adicionar linhas de entrega ao gráfico
        if not df_entregas.empty:
            for data_entrega, row in df_entregas.iterrows():
                idade_entrega = (data_entrega.normalize().date() - self.data_alojamento).days + 1
                ax.axvline(x=data_entrega, color='green', linestyle='--', label=f'Entrega: {data_entrega.strftime("%d/%m %H:%M")} ({idade_entrega} dias) {row["quantidade_kg"]:.0f} kg')

        ax.set_title(f'Projeção de Autonomia de Ração - Aviário {self.aviario_selecionado}')
        ax.set_xlabel('Data e Hora')
        ax.set_ylabel('Peso da Ração (kg)')
        ax.legend()
        ax.grid(True)
        plt.tight_layout()
        
        return final_report_string, fig, df_entregas