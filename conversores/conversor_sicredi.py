# conversor_sicredi.py

import pdfplumber
import pandas as pd
import re
from tkinter import filedialog, messagebox # Adicionado messagebox
import os

def formatar_para_brl(valor_numerico):
    """Formata um número para o padrão de moeda brasileiro."""
    valor_str = f"{valor_numerico:,.2f}"
    return valor_str.replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")

def extrair_dados(pdf_path):
    """Extrai dados de um Sicredi PDF usando extração de tabela e retorna um DataFrame."""
    transacoes = []
    date_pattern = re.compile(r'^\d{2}/\d{2}/\d{4}$')

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                tabelas = page.extract_tables()
                for tabela in tabelas:
                    for linha in tabela:
                        if not linha or len(linha) < 4:
                            continue

                        data = str(linha[0]).strip() if linha[0] else ""
                        
                        if not date_pattern.match(data):
                            continue

                        descricao = str(linha[1]).strip().replace('\n', ' ') if linha[1] else ""
                        doc = str(linha[2]).strip().replace('\n', ' ') if linha[2] else ""
                        valor_str = str(linha[3]).strip() if linha[3] else "0"
                        
                        try:
                            valor = float(valor_str.replace('.', '').replace(',', '.'))
                            
                            if any(kw in descricao.upper() for kw in ["TARIFA", "IOF", "DEVOLUCAO", "APLICACAO", "LIQ TED"]):
                                valor = -abs(valor)

                            transacoes.append({
                                "Data": data,
                                "Descrição": descricao,
                                "Documento": doc,
                                "Valor": valor
                            })
                        except (ValueError, IndexError):
                            print(f"Aviso: Linha ignorada em '{os.path.basename(pdf_path)}' por valor inválido: {linha}")
                            continue

        if not transacoes:
            return pd.DataFrame()

        df = pd.DataFrame(transacoes)
        df['Valor'] = df['Valor'].apply(formatar_para_brl)
        return df

    except Exception as e:
        print(f"Erro ao processar o arquivo {os.path.basename(pdf_path)}: {e}")
        return pd.DataFrame()


# --- FUNÇÃO ATUALIZADA ---
def iniciar_processamento():
    """
    Função principal que seleciona arquivos, consolida os dados e salva o Excel.
    Salva automaticamente se for um arquivo, ou pergunta se forem vários.
    """
    paths = filedialog.askopenfilenames(
        title="Selecione o(s) extrato(s) Sicredi",
        filetypes=[("Arquivos PDF", "*.pdf")]
    )
    if not paths:
        return False

    all_dfs = []
    for path in paths:
        df = extrair_dados(path)
        if not df.empty:
            all_dfs.append(df)
    
    if not all_dfs:
        messagebox.showinfo("Nenhum Dado", "Nenhuma transação foi encontrada nos arquivos selecionados.")
        return True

    df_final = pd.concat(all_dfs, ignore_index=True)
    
    # save_path = ""
    
    # Lógica de salvamento inteligente
    primeiro_arquivo_path = path[0]
    diretorio_base = os.path.dirname(primeiro_arquivo_path)

    if len(path) == 1:
        nome_base, _ = os.path.splitext(os.path.basename(primeiro_arquivo_path))
        nome_arquivo_sugerido = nome_base + ".xlsx"
    else:
        nome_arquivo_sugerido = "Conversao Consolidada Sicredi.xlsx"

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
        df_final.to_excel(caminho_salvar, index=False)
        return caminho_salvar # Retorna o caminho para a mensagem de sucesso
    except Exception as e:
        messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar o arquivo consolidado.\n\nErro: {e}")
        return None