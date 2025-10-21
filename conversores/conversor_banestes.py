import tkinter as tk
from tkinter import filedialog,messagebox
import pandas as pd
import pdfplumber
import traceback
import re
import os
from collections import defaultdict

def selecionar_arquivo_pdf():
    """Abre uma janela para o usuário selecionar um arquivo PDF."""
    root = tk.Tk()
    root.withdraw()
    filepath = filedialog.askopenfilename(
        title="Selecione o extrato PDF do Banestes",
        filetypes=[("Arquivos PDF", "*.pdf")]
    )
    if not filepath:
        print("Nenhum arquivo selecionado. Encerrando.")
        exit()
    return filepath

def extrair_dados_do_pdf(caminho_pdf):
    """
    Processa o extrato PDF analisando a posição de cada palavra na página.
    """
    print(f"Iniciando extração avançada por coordenadas: {caminho_pdf}")
    
    # --- Parâmetros de Layout ---
    COLUNA_DATA_FIM_X = 75
    COLUNA_VALOR_INICIO_X = 480
    # ---------------------------

    transacoes = []
    
    try:
        with pdfplumber.open(caminho_pdf) as pdf:
            dia_atual = ""
            for page in pdf.pages:
                words = page.extract_words(x_tolerance=2, y_tolerance=2, keep_blank_chars=True)
                linhas_agrupadas = defaultdict(list)
                for word in words:
                    chave_y = round(word['top'], 0) 
                    linhas_agrupadas[chave_y].append(word)

                for y in sorted(linhas_agrupadas.keys()):
                    palavras_na_linha = sorted(linhas_agrupadas[y], key=lambda w: w['x0'])
                    
                    col_data_str, col_desc_str, col_valor_str = "", "", ""

                    for palavra in palavras_na_linha:
                        if palavra['x0'] < COLUNA_DATA_FIM_X:
                            col_data_str += palavra['text']
                        elif palavra['x0'] > COLUNA_VALOR_INICIO_X:
                            col_valor_str += palavra['text']
                        else:
                            col_desc_str += palavra['text'] + " "

                    col_data_str = col_data_str.strip()
                    col_desc_str = col_desc_str.strip()
                    col_valor_str = col_valor_str.strip()

                    if re.match(r'^\d{2}$', col_data_str):
                        dia_atual = col_data_str

                    if col_desc_str and col_valor_str and re.search(r'[\d]', col_valor_str):
                        if "lançamento" in col_desc_str.lower():
                            continue

                        # Limpa o valor e converte para float (ex: 4750.00)
                        valor_numerico = float(re.sub(r'[^\d,-]', '', col_valor_str).replace('.', '').replace(',', '.'))
                        
                        palavras_debito = ['Pix Enviado', 'Pagamento', 'Tarifa', 'Cesta']
                        if any(keyword in col_desc_str for keyword in palavras_debito) and valor_numerico > 0:
                            valor_numerico *= -1
                        
                        transacoes.append({
                            "Data": f"{dia_atual}/JUN/25",
                            "Lançamento": col_desc_str,
                            "Valor (R$)": valor_numerico
                        })
    except Exception as e:
        print(f"Ocorreu um erro inesperado durante o processamento: {e}")
        return None

    if not transacoes:
        print("Nenhuma transação foi extraída com a análise de coordenadas.")
        return None

    df = pd.DataFrame(transacoes)
    return df
def iniciar_processamento():
    """
    Função de entrada que orquestra o fluxo de conversão.
    """
    pdf_path = filedialog.askopenfilename(
        title="Selecione o extrato do Banestes",
        filetypes=[("PDF files", "*.pdf")]
    )
    if not pdf_path:
        return False

    try:
        df = extrair_dados_do_pdf(pdf_path)
        if df.empty:
            messagebox.showwarning("Aviso", "Nenhuma transação válida foi encontrada no arquivo.")
            return False

        output_csv_path = os.path.splitext(pdf_path)[0] + ".csv"
        df.to_csv(output_csv_path, index=False, sep=';', encoding='utf-8-sig', decimal=',')
        return True
    except Exception as e:
        traceback.print_exc()
        messagebox.showerror("Erro Crítico", f"Ocorreu um erro inesperado ao processar o extrato.\n\n{e}")
        return False

import os # Garanta que o 'os' está importado no topo do seu arquivo
from tkinter import filedialog, messagebox
import pandas as pd

# Supondo que suas outras funções (extrair_formato_cac) estejam no mesmo arquivo...

def iniciar_processamento():
    caminhos_dos_arquivos = filedialog.askopenfilenames(
        title="Selecione os extratos Banestes",
        filetypes=[("Arquivos PDF", "*.pdf")]
    )
    if not caminhos_dos_arquivos:
        return None

    dfs_completos = []
    erros = []
    
    for arquivo_path in caminhos_dos_arquivos:
        nome_arquivo_original = os.path.basename(arquivo_path)
        try:
            df_transacoes = extrair_dados_do_pdf(arquivo_path)
            if df_transacoes is not None and not df_transacoes.empty:
                dfs_completos.append(df_transacoes)
                print(f"SUCESSO! Dados de '{nome_arquivo_original}' extraídos.")
            else:
                erros.append(nome_arquivo_original)
        except Exception as e:
            print(f"ERRO! Falha em '{nome_arquivo_original}': {e}")
            erros.append(nome_arquivo_original)
    
    if not dfs_completos:
        messagebox.showerror("Falha na Extração", "Nenhuma transação válida foi encontrada nos arquivos selecionados.")
        return None

    df_final = pd.concat(dfs_completos, ignore_index=True)

    # --- LÓGICA PARA NOME DE ARQUIVO INTELIGENTE ---
    
    # Pega o caminho do primeiro arquivo como base
    primeiro_arquivo_path = caminhos_dos_arquivos[0]
    # Pega o diretório (a pasta) desse primeiro arquivo
    diretorio_base = os.path.dirname(primeiro_arquivo_path)

    # Decide o nome do arquivo sugerido
    if len(caminhos_dos_arquivos) == 1:
        # Se for só um arquivo, usa o nome dele
        nome_base, _ = os.path.splitext(os.path.basename(primeiro_arquivo_path))
        nome_arquivo_sugerido = nome_base + ".xlsx"
    else:
        # Se forem vários, usa um nome padrão para o arquivo consolidado
        nome_arquivo_sugerido = "Conversao Consolidada .xlsx"

    # --- FIM DA LÓGICA ---

    # Agora, usamos as variáveis que criamos para pré-popular a janela "Salvar Como"
    caminho_salvar = filedialog.asksaveasfilename(
        title="Salvar arquivo consolidado como...",
        initialdir=diretorio_base,             # <-- USA O DIRETÓRIO BASE
        initialfile=nome_arquivo_sugerido,     # <-- USA O NOME SUGERIDO
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