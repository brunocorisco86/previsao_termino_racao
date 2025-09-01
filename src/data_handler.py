import pandas as pd
import os

def importar_sensores(source):
    """Carrega os dados dos sensores a partir de um arquivo CSV ou objeto de arquivo."""
    df = pd.read_csv(source, sep=';', encoding='utf-8', skiprows=1, decimal=',', thousands='.')
    df.columns = df.columns.str.strip().str.lower()

    # Check for 'value' or 'valor' column
    if 'value' in df.columns:
        pass # Column is already 'value' (lowercase)
    elif 'valor' in df.columns:
        df.rename(columns={'valor': 'value'}, inplace=True) # Rename 'valor' to 'value'
    else:
        raise KeyError("A coluna 'Value' ou 'Valor' não foi encontrada no Sensores.csv.")

    df['value'] = pd.to_numeric(df['value'], errors='coerce') # Use lowercase 'value'
    df.dropna(subset=['value'], inplace=True) # Use lowercase 'value'

    # Check for 'date' or 'data'
    if 'date' in df.columns:
        pass # Column is already 'date' (lowercase)
    elif 'data' in df.columns:
        df.rename(columns={'data': 'date'}, inplace=True) # Rename 'data' to 'date'
    else:
        raise KeyError("A coluna 'Date' ou 'Data' não foi encontrada no Sensores.csv.")

    # Check for 'hour' or 'hora'
    if 'hour' in df.columns:
        pass # Column is already 'hour' (lowercase)
    elif 'hora' in df.columns:
        df.rename(columns={'hora': 'hour'}, inplace=True) # Rename 'hora' to 'hour'
    else:
        raise KeyError("As colunas 'Hour' ou 'Hora' não foram encontradas no Sensores.csv.")

    # --- Add check for 'collector' or 'coletor' ---
    if 'collector' in df.columns:
        pass # Column is already 'collector' (lowercase)
    elif 'coletor' in df.columns:
        df.rename(columns={'coletor': 'collector'}, inplace=True) # Rename 'coletor' to 'collector'
    else:
        raise KeyError("A coluna 'Collector' ou 'Coletor' não foi encontrada no Sensores.csv.")
    # --- End add check for 'collector' or 'coletor' ---

    # --- Add check for 'channel' or 'canal' ---
    if 'channel' in df.columns:
        pass # Column is already 'channel' (lowercase)
    elif 'canal' in df.columns:
        df.rename(columns={'canal': 'channel'}, inplace=True) # Rename 'canal' to 'channel'
    else:
        raise KeyError("A coluna 'Channel' ou 'Canal' não foi encontrada no Sensores.csv.")
    # --- End add check for 'channel' or 'canal' ---

    # --- Debugging/Robustness additions ---
    if not pd.api.types.is_string_dtype(df['date']):
        df['date'] = df['date'].astype(str)
    if not pd.api.types.is_string_dtype(df['hour']):
        df['hour'] = df['hour'].astype(str)
    # --- End Debugging/Robustness additions ---

    df['timedate'] = pd.to_datetime(df['date'] + ';' + df['hour'], format='%d/%m/%Y;%H:%M:%S', errors='coerce')
    
    # --- Debugging/Robustness additions ---
    if df['timedate'].isnull().all():
        raise ValueError("Não foi possível converter as colunas 'Date' e 'Hour' para formato de data/hora. Verifique o formato dos dados nessas colunas.")
    # --- End Debugging/Robustness additions ---

    df.dropna(subset=['timedate'], inplace=True)
    
    df = df.set_index('timedate').sort_index()
    return df

def importar_consumo(linhagem, folder_path):
    """Importa a tabela de consumo da linhagem."""
    path = os.path.join(folder_path, f'{linhagem}.xlsx')
    df = pd.read_excel(path)
    df.rename(columns={'dia de vida': 'idade', 'consumo': 'consumo_gr_ave_dia'}, inplace=True)
    return df