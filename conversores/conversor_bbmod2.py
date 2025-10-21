import pdfplumber
import re
import pandas as pd
from typing import Optional, List
import os
import tkinter as tk
from tkinter import filedialog

# Se a lógica for diferente, altere estas funções.
# Caso contrário, pode deixar como está.
def _limpar_e_converter_valor(valor_str: Optional[str]) -> float:
    if not valor_str:
        return 0.0
    match = re.search(r'([\d\.,]+)\s*([CD])', valor_str)
    if match:
        valor_numerico, tipo = match.groups()
        valor_limpo = valor_numerico.replace('.', '').replace(',', '.').strip()
        valor_final = float(valor_limpo)
        if tipo == 'D':
            valor_final *= -1
        return valor_final
    return 0.0

def _extrair_transacoes_de_pdf(caminho_pdf: str) -> Optional[pd.DataFrame]:
    transacoes: List[dict] = []
    padrao_linha_transacao = re.compile(r'^\d{2}/\d{2}/\d{2,4}')
    padrao_valor_geral = re.compile(r'([\d\.,]+\s[CD])')

    with pdfplumber.open(caminho_pdf) as pdf:
        linhas_texto: List[str] = []
        for pagina in pdf.pages:
            texto_pagina = pagina.extract_text(x_tolerance=2, y_tolerance=3)
            if texto_pagina:
                linhas_texto.extend(texto_pagina.split('\n'))
        
        transacao_atual = None
        for linha in linhas_texto:
            if padrao_linha_transacao.search(linha):
                if transacao_atual and transacao_atual.get('Valor') is not None:
                    descricao_completa = ' '.join(transacao_atual['Lançamento']).strip()
                    transacao_atual['Lançamento'] = re.sub(r'\s+', ' ', descricao_completa)
                    transacoes.append(transacao_atual)
                
                data = linha.split()[0]
                todos_valores_encontrados = padrao_valor_geral.findall(linha)
                valor_str = todos_valores_encontrados[0] if todos_valores_encontrados else None
                
                descricao_inicial = linha.replace(data, '', 1).strip()
                if valor_str:
                    for v_str in todos_valores_encontrados:
                        descricao_inicial = descricao_inicial.replace(v_str, '').strip()

                transacao_atual = {
                    "Data": data,
                    "Lançamento": [descricao_inicial],
                    "Valor": _limpar_e_converter_valor(valor_str)
                }
            elif transacao_atual:
                if not re.search(r'(Lançamentos|Histórico|Saldo Anterior|SALDO|G336)', linha):
                    transacao_atual['Lançamento'].append(linha.strip())
        
        if transacao_atual and transacao_atual.get('Valor') is not None:
            descricao_completa = ' '.join(transacao_atual['Lançamento']).strip()
            transacao_atual['Lançamento'] = re.sub(r'\s+', ' ', descricao_completa)
            transacoes.append(transacao_atual)
    
    if not transacoes:
        return None

    df = pd.DataFrame(transacoes)
    df = df[~df['Lançamento'].str.contains("Saldo Anterior", na=False)]
    df = df[df['Valor'] != 0.0]
    return df

import os # Garanta que o 'os' está importado no topo do seu arquivo
from tkinter import filedialog, messagebox
import pandas as pd

# Supondo que suas outras funções (extrair_formato_cac) estejam no mesmo arquivo...

def iniciar_processamento():
    caminhos_dos_arquivos = filedialog.askopenfilenames(
        title="Selecione os extratos (BB - Modelo 1)",
        filetypes=[("Arquivos PDF", "*.pdf")]
    )
    if not caminhos_dos_arquivos:
        return None

    dfs_completos = []
    erros = []
    
    for arquivo_path in caminhos_dos_arquivos:
        nome_arquivo_original = os.path.basename(arquivo_path)
        try:
            df_transacoes = _extrair_transacoes_de_pdf(arquivo_path)
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
        nome_arquivo_sugerido = "Conversao Consolidada BB.xlsx"

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