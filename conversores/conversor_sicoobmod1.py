# conversor_sicoobmod1.py (Corrigido)

import pdfplumber
import pandas as pd
from tkinter import filedialog, messagebox
import os
import re

def extrair_dados_do_pdf(caminho_pdf):
    """
    Extrai dados de transações (Modelo 1) e RETORNA um DataFrame.
    """
    date_pattern = re.compile(r"^(\d{2}\/\d{2}\/\d{4})")
    value_pattern = re.compile(r"([\d\.,]+)([CD])$")
    
    transacoes = []
    data_atual = None

    try:
        with pdfplumber.open(caminho_pdf) as pdf:
            for page in pdf.pages:
                texto_pagina = page.extract_text(x_tolerance=2)
                if not texto_pagina:
                    continue

                linhas = texto_pagina.split('\n')
                
                for linha in linhas:
                    if "SALDO ANTERIOR" in linha or "SALDO DO DIA" in linha or "EXTRATO CONTA CORRENTE" in linha:
                        continue

                    match_data = date_pattern.search(linha)
                    if match_data:
                        data_atual = match_data.group(1)

                    match_valor = value_pattern.search(linha.strip())
                    if match_valor and data_atual:
                        valor_original = f"{match_valor.group(1)}{match_valor.group(2)}"
                        lancamento = linha[:match_valor.start()].strip()
                        
                        if match_data:
                            lancamento = lancamento[match_data.end():].strip()
                        
                        # Remove o número do documento que pode vir no início
                        lancamento = re.sub(r"^\S+\s", "", lancamento, count=1)

                        if lancamento:
                            transacoes.append([data_atual, lancamento.strip(), valor_original])

        if not transacoes:
            return pd.DataFrame()

        df = pd.DataFrame(transacoes, columns=["Data", "Lancamento", "Valor_Original"])

        # --- FUNÇÃO DE FORMATAÇÃO CORRIGIDA ---
        def formatar_valor(valor_str):
            """
            Formata o valor para o padrão CSV brasileiro.
            Ex: "1.234,56D" -> "-1234,56"
            """
            # Verifica se é Débito (D) e remove a letra
            is_debit = valor_str.endswith('D')
            valor_numerico_str = valor_str[:-1]

            # 1. Remove o ponto separador de milhar.
            valor_sem_ponto = valor_numerico_str.replace('.', '')
            
            # 2. Adiciona o sinal de negativo se for débito.
            if is_debit:
                return '-' + valor_sem_ponto
            else:
                return valor_sem_ponto

        df['Valor'] = df['Valor_Original'].apply(formatar_valor)
        df_final = df[["Data", "Lancamento", "Valor"]]
        
        return df_final

    except Exception as e:
        messagebox.showerror("Erro no Modelo 1", f"Ocorreu um erro ao processar o PDF:\n{e}")
        return None

def iniciar_processamento():
    """Função chamada pelo programa principal para iniciar a conversão."""
    caminho_dos_arquivos = filedialog.askopenfilenames(
        title="Selecione os extratos (Sicoob - Modelo 1)",
        filetypes=[("PDF", "*.pdf")]
    )
    if not caminho_dos_arquivos:
        raise UserWarning("") # Levanta aviso de cancelamento para o menu principal

    sucesso_geral = False
    for path in caminho_dos_arquivos:
        df_transacoes = extrair_dados_do_pdf(path)
        if df_transacoes is not None and not df_transacoes.empty:
            csv_path = os.path.splitext(path)[0] + '.csv'
            df_transacoes.to_csv(csv_path, index=False, sep=';', encoding='utf-8-sig')
            sucesso_geral = True
    
    if not sucesso_geral:
        # Se nenhum arquivo gerou transações, considera como um cancelamento ou falha
        raise UserWarning("Nenhuma transação válida encontrada nos arquivos selecionados.")

    # return True # Retorna True para sinalizar sucesso ao menu principal
# Lógica de salvamento inteligente
    primeiro_arquivo_path = caminho_dos_arquivos[0]
    diretorio_base = os.path.dirname(primeiro_arquivo_path)

    if len(caminho_dos_arquivos) == 1:
        nome_base, _ = os.path.splitext(os.path.basename(primeiro_arquivo_path))
        nome_arquivo_sugerido = nome_base + ".xlsx"
    else:
        nome_arquivo_sugerido = "Conversao Consolidada Sicoob Mod2.xlsx"

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
        # Aqui você pode adicionar a lógica para ordenar por data se necessário
        # df_final.to_excel(caminho_salvar, index=False)
        return caminho_salvar # Retorna o caminho para a mensagem de sucesso
    except Exception as e:
        messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar o arquivo consolidado.\n\nErro: {e}")
        return None