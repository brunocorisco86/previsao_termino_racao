from tkinter import Tk, simpledialog, messagebox
from datetime import datetime, date, timedelta
import pandas as pd

def obter_dados_dialogo(prompt, title):
    """Função genérica para obter dados do usuário via diálogo."""
    root = Tk()
    root.withdraw()
    return simpledialog.askstring(title, prompt)

def selecionar_aviario(df):
    """Mostra os números dos aviários disponíveis e pede para o usuário selecionar um."""
    print("  - Identificando aviários disponíveis...")
    if 'aviario_num' not in df.columns:
        messagebox.showerror("Erro", "A coluna 'aviario_num' não foi encontrada no dataframe.")
        return None

    aviarios = sorted(df['aviario_num'].unique())
    
    lista_str = ", ".join(map(str, aviarios))
    prompt = f"Aviários disponíveis (números):\n{lista_str}\n\nDigite o NÚMERO do aviário que deseja analisar:"

    while True:
        selecao_str = obter_dados_dialogo(prompt, "Seleção de Aviário")
        if not selecao_str: return None
        
        try:
            selecao_num = int(selecao_str)
            if selecao_num in aviarios:
                print(f"  - Aviário selecionado: {selecao_num}")
                return selecao_num
            else:
                messagebox.showwarning("Seleção Inválida", f"O número '{selecao_num}' não corresponde a um aviário válido.")
        except ValueError:
            messagebox.showwarning("Entrada Inválida", "Por favor, digite apenas o número do aviário.")

def obter_data_alojamento():
    """Pede e valida a data de alojamento."""
    today = date.today()
    min_date = today - timedelta(days=54)
    while True:
        date_str = obter_dados_dialogo("Digite a data de alojamento (dd/mm/aaaa):", "Entrada de Dados")
        if not date_str: return None
        try:
            alojamento_date = datetime.strptime(date_str, "%d/%m/%Y").date()
            if alojamento_date > today:
                messagebox.showerror("Erro", "A data de alojamento não pode ser uma data futura.")
            elif alojamento_date < min_date:
                messagebox.showerror("Erro", f"A data não pode ser anterior a {min_date.strftime('%d/%m/%Y')}.")
            else:
                return alojamento_date
        except ValueError:
            messagebox.showerror("Erro", "Formato de data inválido. Use dd/mm/aaaa.")

def obter_info_lote():
    """Obtém a linhagem e o número de aves."""
    linhagem = obter_dados_dialogo("Digite a linhagem (Cobb/Ross):", "Linhagem")
    if not linhagem or linhagem.lower() not in ['cobb', 'ross']:
        messagebox.showerror("Erro", "Linhagem inválida. Por favor, digite 'Cobb' ou 'Ross'.")
        return None, None

    n_aves_str = obter_dados_dialogo(f"Digite o número de aves alojadas:", "Número de Aves")
    try:
        n_aves = int(n_aves_str)
        if n_aves <= 0: raise ValueError
        return linhagem.lower(), n_aves
    except (ValueError, TypeError):
        messagebox.showerror("Erro", "Número de aves inválido. Insira um número inteiro positivo.")
        return None, None
