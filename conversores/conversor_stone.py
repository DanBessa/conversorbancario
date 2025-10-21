# conversor_stone.py (VERSÃO CORRIGIDA E COMPLETA)

import pandas as pd
import pdfplumber
import re
import os
from tkinter import filedialog, messagebox

# ==============================================================================
# FUNÇÃO AUXILIAR
# ==============================================================================

def limpar_valor(texto_valor: str) -> float:
    """
    Converte uma string de valor monetário para float.
    """
    if not isinstance(texto_valor, str):
        return 0.0
    texto_limpo = texto_valor.replace(".", "").replace(",", ".")
    try:
        texto_limpo = re.sub(r'[^\d.-]', '', texto_limpo)
        return float(texto_limpo)
    except (ValueError, TypeError):
        return 0.0

# ==============================================================================
# FUNÇÃO PRINCIPAL DE EXTRAÇÃO (LÓGICA CORRIGIDA)
# ==============================================================================

def extrair_dados_pdf_stone(pdf_path: str) -> pd.DataFrame:
    """
    Extrai dados de um único extrato PDF da Stone e retorna um DataFrame.
    """
    texto_completo = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                texto_pagina = page.extract_text() # Usar layout=False pode ser melhor para texto contínuo
                if texto_pagina:
                    texto_completo += texto_pagina + "\n"

        transacoes = []
        # O padrão agora busca o início de um bloco de transação
        padrao_bloco = re.compile(r"(\d{2}/\d{2}/\d{4})\s+(Crédito|Débito)", re.IGNORECASE)
        matches = list(padrao_bloco.finditer(texto_completo))

        for i, match in enumerate(matches):
            # Define o bloco de texto para a transação atual
            start_pos = match.start()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(texto_completo)
            bloco_texto = texto_completo[start_pos:end_pos]

            linhas = [linha.strip() for linha in bloco_texto.strip().split('\n') if linha.strip()]
            if not linhas:
                continue

            # Extrai informações da primeira linha do bloco
            data = match.group(1)
            tipo = match.group(2)
            
            # Remove a data e o tipo da primeira linha para isolar o resto do texto
            primeira_linha_conteudo = padrao_bloco.sub('', linhas[0], 1).strip()
            
            # Junta o conteúdo da primeira linha com as linhas subsequentes
            texto_completo_historico = (primeira_linha_conteudo + " " + " ".join(linhas[1:])).strip()

            # Encontra todos os valores monetários no bloco
            valores_monetarios = re.findall(r"-?[\d\.]+,\d{2}", texto_completo_historico)
            
            valor_str = "0,00"
            if len(valores_monetarios) >= 2: # Geralmente Valor e Saldo
                valor_str = valores_monetarios[-2] # O valor da transação é o penúltimo
                # Remove os valores do texto para obter o histórico limpo
                historico = texto_completo_historico
                for valor in valores_monetarios:
                    historico = historico.replace(valor, "")
            else: # Fallback caso o padrão não seja encontrado
                 historico = texto_completo_historico

            historico = re.sub(r'\s+', ' ', historico).strip()
            
            valor_numerico = limpar_valor(valor_str)
            if tipo.lower() == "débito":
                valor_numerico = -abs(valor_numerico)

            transacoes.append({
                "Data": data,
                "Histórico": historico,
                "Valor": valor_numerico
            })
        
        return pd.DataFrame(transacoes)

    except Exception as e:
        messagebox.showerror(
            "Erro ao Processar PDF",
            f"Ocorreu um erro inesperado ao processar o arquivo {os.path.basename(pdf_path)}:\n\n{e}"
        )
        return pd.DataFrame()

# ==============================================================================
# FUNÇÃO MAIN (CHAMADA PELO PROGRAMA PRINCIPAL)
# ==============================================================================

def main():
    """
    Função principal que lida com múltiplos arquivos, consolida os dados
    e implementa a lógica de salvamento inteligente.
    """
    caminhos_dos_arquivos = filedialog.askopenfilenames(
        title="Selecione os extratos Stone",
        filetypes=[("Arquivos PDF", "*.pdf")]
    )
    if not caminhos_dos_arquivos:
        return None # Usuário cancelou

    dfs_completos = []
    for pdf_path in caminhos_dos_arquivos:
        df = extrair_dados_pdf_stone(pdf_path)
        if not df.empty:
            dfs_completos.append(df)

    if not dfs_completos:
        messagebox.showerror("Falha na Extração", "Nenhuma transação válida foi encontrada nos arquivos selecionados.")
        return None

    df_final = pd.concat(dfs_completos, ignore_index=True)
    
    # Lógica de salvamento inteligente (padrão BB)
    primeiro_arquivo_path = caminhos_dos_arquivos[0]
    diretorio_base = os.path.dirname(primeiro_arquivo_path)

    if len(caminhos_dos_arquivos) == 1:
        nome_base, _ = os.path.splitext(os.path.basename(primeiro_arquivo_path))
        nome_arquivo_sugerido = nome_base + ".xlsx"
    else:
        nome_arquivo_sugerido = "Conversao Consolidada Stone.xlsx"

    caminho_salvar = filedialog.asksaveasfilename(
        title="Salvar arquivo consolidado como...",
        initialdir=diretorio_base,
        initialfile=nome_arquivo_sugerido,
        defaultextension=".xlsx",
        filetypes=[("Arquivos Excel", "*.xlsx")]
    )

    if not caminho_salvar:
        return None # Usuário cancelou o salvamento

    try:
        # Garante a ordenação por data antes de salvar
        df_final['Data'] = pd.to_datetime(df_final['Data'], format='%d/%m/%Y')
        df_final = df_final.sort_values(by="Data", ascending=True).reset_index(drop=True)
        # Formata a data de volta para o padrão brasileiro para o Excel
        df_final['Data'] = df_final['Data'].dt.strftime('%d/%m/%Y')

        df_final.to_excel(caminho_salvar, index=False)
        return caminho_salvar # Retorna o caminho para a mensagem de sucesso
    except Exception as e:
        messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar o arquivo consolidado.\n\nErro: {e}")
        return None