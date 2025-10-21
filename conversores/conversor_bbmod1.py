import pdfplumber
import re
import pandas as pd
from typing import Optional, List
import os
import tkinter as tk
from tkinter import filedialog, messagebox

# Substitua a sua função antiga por esta
def limpar_e_converter_valor_cac(valor_str: Optional[str]) -> float:
    """
    Converte a string de valor para o formato CAC.
    Ex: "1.234,56 (+)" -> 1234.56
    """
    if not valor_str:
        return 0.0

    # O padrão regex para encontrar o valor e o sinal está correto.
    match = re.search(r'([\d\.,]+)\s*\(\s*([+-])\s*\)', valor_str)
    if match:
        valor_num_str, sinal = match.groups()
        
        # --- LINHA CORRIGIDA ---
        # 1. Remove os pontos (separador de milhar).
        # 2. Substitui a vírgula (separador decimal) por um ponto.
        valor_limpo = valor_num_str.replace('.', '').replace(',', '.').strip()
        
        # Agora a conversão para float funcionará corretamente
        valor_final = float(valor_limpo)
        
        if sinal == '-':
            valor_final *= -1
        return valor_final
        
    return 0.0

def extrair_formato_cac(caminho_pdf: str) -> Optional[pd.DataFrame]:
    """
    Extrai transações de extratos bancários no formato CAC COMERCIAL,
    usando uma lógica de buffer para lidar com layouts complexos.
    """
    transacoes: List[dict] = []
    
    padrao_data = re.compile(r'^\d{2}/\d{2}/\d{2,4}')
    padrao_valor = re.compile(r'([\d\.,\s]+\(\s*[-+]\s*\))$')
    padrao_ignorar = re.compile(
        r'^(Lançamentos|Histórico|Saldo Anterior|Dia\s+Lote|Extrato de Conta Corrente|Cliente\s|Agência:|Total Aplicações|Informações Adicionais|SALDO|Informações Complementares)', 
        re.IGNORECASE
    )

    try:
        with pdfplumber.open(caminho_pdf) as pdf:
            texto_completo = ""
            # --- BLOCO CORRIGIDO ---
            # O 'if' que pulava a página foi removido daqui.
            # Agora o script lê todas as páginas.
            for pagina in pdf.pages:
                texto_pagina = pagina.extract_text(x_tolerance=2, y_tolerance=3)
                if texto_pagina:
                    texto_completo += texto_pagina + "\n"
            
            linhas = texto_completo.split('\n')
            
            buffer_data = None
            buffer_descricao: List[str] = []

            for linha in linhas:
                linha = linha.strip()
                # A lógica de ignorar linhas de cabeçalho/resumo já existente cuidará da limpeza.
                if not linha or padrao_ignorar.search(linha):
                    continue

                data_match = padrao_data.search(linha)

                if data_match:
                    buffer_data = data_match.group(0)
                    descricao_inicial = padrao_data.sub('', linha).strip()
                    descricao_inicial = re.sub(r'^\s*\d+\s+[\d\w]+\s*', '', descricao_inicial)
                    buffer_descricao = [descricao_inicial]
                elif buffer_data:
                    buffer_descricao.append(linha)
                
                if buffer_data:
                    texto_buffer_completo = ' '.join(buffer_descricao)
                    valor_match_no_buffer = padrao_valor.search(texto_buffer_completo)

                    if valor_match_no_buffer:
                        valor_str = valor_match_no_buffer.group(1)
                        
                        descricao_sem_valor = padrao_valor.sub('', texto_buffer_completo).strip()
                        descricao_final = re.sub(r'\s+', ' ', descricao_sem_valor)
                        
                        transacao = {
                            "Data": buffer_data,
                            "Lançamento": descricao_final,
                            "Valor": limpar_e_converter_valor_cac(valor_str)
                        }
                        
                        if transacao["Valor"] != 0.0:
                            transacoes.append(transacao)
                        
                        buffer_data = None
                        buffer_descricao = []
        
        if not transacoes:
            return None

        return pd.DataFrame(transacoes)

    except Exception as e:
        print(f"Ocorreu um erro ao processar o arquivo {os.path.basename(caminho_pdf)}: {e}")
        return None

if __name__ == '__main__':
    root = tk.Tk()
    root.withdraw()
    caminhos_dos_arquivos = filedialog.askopenfilenames(
        title="Selecione os extratos (formato CAC)",
        filetypes=[("Arquivos PDF", "*.pdf")]
    )

    if not caminhos_dos_arquivos:
        print("Nenhum arquivo selecionado.")
    else:
        sucessos = 0
        for arquivo_path in caminhos_dos_arquivos:
            nome_arquivo_original = os.path.basename(arquivo_path)
            print(f"--- Processando: {nome_arquivo_original} ---")
            df_transacoes = extrair_formato_cac(arquivo_path)
            if df_transacoes is not None and not df_transacoes.empty:
                print(f"{len(df_transacoes)} transações encontradas.")
                nome_base, _ = os.path.splitext(arquivo_path)
                caminho_csv = nome_base + '.csv'
                try:
                    df_transacoes.to_csv(caminho_csv, index=False, sep=';', encoding='utf-8-sig')
                    print(f"SUCESSO! Salvo em: {caminho_csv}\n")
                    sucessos += 1
                except Exception as e:
                    print(f"ERRO ao salvar: {e}\n")
            else:
                print("Nenhuma transação encontrada ou extraída.\n")
        print("="*60)
        print(f"Processamento concluído. {sucessos} de {len(caminhos_dos_arquivos)} arquivo(s) foram convertidos com sucesso.")
        print("="*60)

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
            df_transacoes = extrair_formato_cac(arquivo_path)
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
