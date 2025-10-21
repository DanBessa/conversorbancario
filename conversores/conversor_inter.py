import pandas as pd
import pdfplumber
import re
import os
from tkinter import filedialog, messagebox

def processar_pdf_inter(pdf_path):
    """
    Extrai dados de um único PDF do Inter e retorna um DataFrame.
    """
    datas, historicos, valores = [], [], []
    
    meses = {
        "Janeiro": "01", "Fevereiro": "02", "Março": "03", "Abril": "04",
        "Maio": "05", "Junho": "06", "Julho": "07", "Agosto": "08",
        "Setembro": "09", "Outubro": "10", "Novembro": "11", "Dezembro": "12"
    }
    
    date_pattern = re.compile(r"(\d{1,2}) de (\w+) de (\d{4})")
    valor_pattern = re.compile(r"(-?)R\$\s*(\d{1,3}(?:\.\d{3})*,\d{2})")
    ultima_data = "01/01/2000"

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                lines = text.split("\n")
                for line in lines:
                    date_match = date_pattern.search(line)
                    if date_match:
                        dia, mes, ano = date_match.groups()
                        mes_numero = meses.get(mes, "00")
                        ultima_data = f"{int(dia):02d}/{mes_numero}/{ano}"

                    match = valor_pattern.search(line)
                    if match:
                        sinal = match.group(1)
                        valor = match.group(2)
                        historico = line[:match.start()].strip()
                        valor = f"-{valor}" if sinal == "-" else valor
                        valor = re.sub(r"\.(?=\d{3},)", "", valor).replace(',', '.')
                        historico = historico.replace('"', '').replace("'", "")
                        
                        datas.append(ultima_data)
                        historicos.append(historico)
                        valores.append(float(valor))

    return pd.DataFrame({"Data": datas, "Histórico": historicos, "Valor": valores})

def iniciar_processamento():
    """
    Função principal que lida com múltiplos arquivos, consolida os dados
    e implementa a lógica de salvamento inteligente.
    """
    caminhos_dos_arquivos = filedialog.askopenfilenames(
        title="Selecione os extratos Inter",
        filetypes=[("Arquivos PDF", "*.pdf")]
    )
    if not caminhos_dos_arquivos:
        return None

    dfs_completos = []
    for pdf_path in caminhos_dos_arquivos:
        try:
            df = processar_pdf_inter(pdf_path)
            if not df.empty:
                dfs_completos.append(df)
        except Exception as e:
            messagebox.showwarning("Erro de Leitura", f"Não foi possível processar o arquivo:\n{os.path.basename(pdf_path)}\n\nErro: {e}")

    if not dfs_completos:
        messagebox.showerror("Falha na Extração", "Nenhuma transação válida foi encontrada nos arquivos selecionados.")
        return None

    df_final = pd.concat(dfs_completos, ignore_index=True)
    
    # Lógica de salvamento inteligente (Modelo BB)
    primeiro_arquivo_path = caminhos_dos_arquivos[0]
    diretorio_base = os.path.dirname(primeiro_arquivo_path)

    if len(caminhos_dos_arquivos) == 1:
        nome_base, _ = os.path.splitext(os.path.basename(primeiro_arquivo_path))
        nome_arquivo_sugerido = nome_base + ".xlsx"
    else:
        nome_arquivo_sugerido = "Conversao Consolidada Inter.xlsx"

    caminho_salvar = filedialog.asksaveasfilename(
        title="Salvar arquivo consolidado como...",
        initialdir=diretorio_base,
        initialfile=nome_arquivo_sugerido,
        defaultextension=".xlsx",
        filetypes=[("Arquivos Excel", "*.xlsx")]
    )

    if not caminho_salvar:
        return None

    try:
        df_final.to_excel(caminho_salvar, index=False)
        return caminho_salvar
    except Exception as e:
        messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar o arquivo consolidado.\n\nErro: {e}")
        return None