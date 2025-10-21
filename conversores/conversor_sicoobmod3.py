import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import pdfplumber
import re
import os
from typing import List
import datetime

def extrair_dados_sicoob(pdf_path: str) -> pd.DataFrame:
    """
    Extrai as transações de um extrato PDF do Sicoob usando uma abordagem
    robusta de análise de texto, focando no início e fim de cada linha.
    """
    print(f"[DEBUG] Iniciando extração do arquivo: {pdf_path}")
    
    transacoes = []
    ano_atual = datetime.date.today().year
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"[DEBUG] PDF aberto com sucesso. Total de páginas: {len(pdf.pages)}")
            
            texto_completo = ""
            for i, pagina in enumerate(pdf.pages):
                texto_pagina = pagina.extract_text()
                if texto_pagina:
                    texto_completo += texto_pagina + "\n"
                    print(f"[DEBUG] Página {i+1} processada. Caracteres extraídos: {len(texto_pagina)}")
                else:
                    print(f"[DEBUG] Página {i+1} não retornou texto")
            
            print(f"[DEBUG] Texto total extraído: {len(texto_completo)} caracteres")
            
            # Salva uma amostra do texto para análise
            with open("debug_texto_extraido.txt", "w", encoding="utf-8") as f:
                f.write(texto_completo[:2000])  # Primeiros 2000 caracteres
            print("[DEBUG] Amostra do texto salva em 'debug_texto_extraido.txt'")
            
            linhas_texto = texto_completo.split('\n')
            print(f"[DEBUG] Total de linhas para processar: {len(linhas_texto)}")
            
            linhas_processadas = 0
            matches_encontrados = 0

            for linha in linhas_texto:
                if not linha.strip():
                    continue
                
                linhas_processadas += 1

                # Expressão Regular simplificada e robusta
                padrao = re.compile(
                    r"^(?P<data>\d{2}/\d{2}(?:/\d{4})?)\s+"  # Grupo 'data': Data no início da linha
                    r"(?P<meio>.*)\s+"                      # Grupo 'meio': Todo o conteúdo do meio
                    r"(?P<valor>R\$\s*[\d\.]*,\d{2}\s?[CD])$" # Grupo 'valor': Valor no final da linha
                )
                
                match = padrao.match(linha.strip())

                if match:
                    matches_encontrados += 1
                    dados = match.groupdict()
                    
                    print(f"[DEBUG] Match {matches_encontrados}: {dados}")
                    
                    data_str = dados['data']
                    data = f"{data_str}/{ano_atual}" if len(data_str) < 10 else data_str
                    
                    valor_str = dados['valor']
                    tipo_transacao = valor_str[-1]
                    valor_limpo_str = re.sub(r'[^\d,]', '', valor_str)
                    valor_numerico = float(valor_limpo_str.replace(',', '.'))
                    if tipo_transacao == 'D':
                        valor_numerico = -abs(valor_numerico)

                    # Tenta extrair o documento do "meio"
                    meio_str = dados['meio']
                    documento = ""
                    historico = meio_str
                    
                    match_doc = re.match(r"^([\d\w]+)\s+(.*)", meio_str)
                    if match_doc:
                        doc_candidate = match_doc.group(1)
                        if doc_candidate.isdigit() or doc_candidate.lower() in ['pix', 'cashback']:
                            documento = doc_candidate
                            historico = match_doc.group(2)

                    transacoes.append({
                        'Data': data,
                        'Histórico': historico.strip(),
                        'Documento': documento,
                        'Valor': valor_numerico
                    })
                else:
                    # Para debug, vamos mostrar algumas linhas que não fizeram match
                    if linhas_processadas <= 20:  # Mostra apenas as primeiras 20 para não poluir
                        print(f"[DEBUG] Linha sem match: '{linha.strip()}'")

            print(f"[DEBUG] Processamento concluído:")
            print(f"[DEBUG] - Linhas processadas: {linhas_processadas}")
            print(f"[DEBUG] - Matches encontrados: {matches_encontrados}")
            print(f"[DEBUG] - Transações extraídas: {len(transacoes)}")

        df = pd.DataFrame(transacoes)
        print(f"[DEBUG] DataFrame criado com {len(df)} registros")
        return df

    except Exception as e:
        print(f"[DEBUG] ERRO durante a extração: {e}")
        import traceback
        print(f"[DEBUG] Traceback completo: {traceback.format_exc()}")
        messagebox.showerror("Erro de Leitura", f"Ocorreu um erro ao processar o arquivo PDF '{os.path.basename(pdf_path)}'.\n\nDetalhes: {e}")
        return pd.DataFrame()

def iniciar_processamento():
    """
    Função principal que gerencia a interface com o usuário, com salvamento automático
    para arquivo único e sem a janela de aviso inicial.
    """
    print("[DEBUG] Iniciando processamento do Sicoob Modelo 3")
    
    root = tk.Tk()
    root.withdraw()

    pdf_paths = filedialog.askopenfilenames(
        title="Selecione o(s) extrato(s) do Sicoob",
        filetypes=[("Arquivos PDF", "*.pdf")]
    )

    if not pdf_paths:
        print("[DEBUG] Nenhum arquivo selecionado")
        return

    print(f"[DEBUG] Arquivos selecionados: {pdf_paths}")

    lista_de_dfs: List[pd.DataFrame] = []
    for path in pdf_paths:
        print(f"[DEBUG] Processando arquivo: {path}")
        df = extrair_dados_sicoob(path)
        if not df.empty:
            lista_de_dfs.append(df)
            print(f"[DEBUG] Arquivo processado com sucesso: {len(df)} transações")
        else:
            print(f"[DEBUG] Arquivo não retornou dados: {path}")

    if not lista_de_dfs:
        print("[DEBUG] Nenhum DataFrame válido foi criado")
        messagebox.showinfo("Sem Dados", "Nenhuma transação válida foi encontrada nos arquivos selecionados.")
        return

    df_final = pd.concat(lista_de_dfs, ignore_index=True)
    print(f"[DEBUG] DataFrame final criado com {len(df_final)} registros")

    # --- LÓGICA DE SALVAMENTO AUTOMÁTICO ---
    save_path = ""
    if len(pdf_paths) == 1:
        pdf_path = pdf_paths[0]
        base_name = os.path.splitext(pdf_path)[0]
        save_path = base_name + ".xlsx"
    else:
        save_path = filedialog.asksaveasfilename(
            title="Salvar arquivo Excel consolidado",
            defaultextension=".xlsx",
            filetypes=[("Arquivos Excel", "*.xlsx")]
        )

    if not save_path:
        print("[DEBUG] Salvamento cancelado")
        messagebox.showwarning("Cancelado", "Operação de salvamento cancelada.")
        return

    try:
        df_final.to_excel(save_path, index=False)
        print(f"[DEBUG] Arquivo salvo com sucesso: {save_path}")
        return save_path  # Importante: retorna o caminho para o menu principal
    except Exception as e:
        print(f"[DEBUG] Erro ao salvar: {e}")
        messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar o arquivo.\n\nErro: {e}")
        return None

if __name__ == "__main__":
    iniciar_processamento()