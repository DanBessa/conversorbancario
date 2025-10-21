import pandas as pd
import pdfplumber
import re
from tkinter import filedialog, messagebox
import datetime # Importa a biblioteca para manipulação de datas

def extrair_dados_extrato_safra(caminho_pdf: str) -> pd.DataFrame:
    """
    Extrai as transações de um extrato do Banco Safra, adicionando o ano atual
    às datas extraídas.
    """
    lancamentos_brutos = []
    try:
        with pdfplumber.open(caminho_pdf) as pdf:
            for pagina in pdf.pages:
                tabelas = pagina.extract_tables(table_settings={
                    "vertical_strategy": "text",
                    "horizontal_strategy": "text",
                    "snap_tolerance": 5,
                })
                
                for tabela in tabelas:
                    if not tabela: continue

                    header_row_index = -1
                    for i, linha in enumerate(tabela):
                        linha_str = " ".join(filter(None, [str(celula) for celula in linha]))
                        if "Lançamento" in linha_str and "Valor" in linha_str and "Data" in linha_str:
                            header_row_index = i
                            break
                    
                    if header_row_index != -1:
                        lancamentos_brutos.extend(tabela[header_row_index + 1:])

    except Exception as e:
        messagebox.showerror("Erro ao Ler PDF", f"Não foi possível processar o arquivo PDF.\n\nDetalhes: {e}")
        return pd.DataFrame()

    if not lancamentos_brutos:
        return pd.DataFrame()

    # Pega o ano atual do sistema para adicionar às datas
    ano_atual = datetime.date.today().year

    dados_processados = []
    for linha in lancamentos_brutos:
        linha_limpa = [str(celula).strip() for celula in linha if celula and str(celula).strip()]
        
        if len(linha_limpa) < 1:
            continue

        primeiro_elemento = linha_limpa[0]
        match = re.match(r'(\d{2}/\d{2})(.*)', primeiro_elemento, re.DOTALL)
        
        if match:
            # Extrai a data (dd/mm) e adiciona o ano atual
            data_sem_ano = match.group(1).strip()
            data = f"{data_sem_ano}/{ano_atual}"
            
            resto_do_primeiro_elemento = match.group(2).strip()
            
            if len(linha_limpa) < 2:
                continue
            
            valor = linha_limpa[-1]
            
            elementos_descricao = [resto_do_primeiro_elemento] + linha_limpa[1:-1]
            descricao = " ".join(filter(None, elementos_descricao))

            dados_processados.append([data, descricao, valor])

    if not dados_processados:
        return pd.DataFrame()

    df = pd.DataFrame(dados_processados, columns=["Data", "Descricao", "Valor_RS"])

    # --- Limpeza Final e Formatação ---
    df["Valor_RS"] = df["Valor_RS"].astype(str).str.replace('.', '', regex=False)
    df["Valor_RS"] = df["Valor_RS"].str.replace(',', '.', regex=False)
    df["Valor_RS"] = pd.to_numeric(df["Valor_RS"], errors='coerce')
    
    df.dropna(subset=["Valor_RS", "Data"], inplace=True)

    return df

def iniciar_processamento():
    """
    Função principal chamada pelo menu da aplicação.
    """
    caminho_pdf = filedialog.askopenfilename(
        title="Selecione o extrato PDF do Banco Safra",
        filetypes=[("Arquivos PDF", "*.pdf")]
    )
    if not caminho_pdf:
        return None

    df_resultado = extrair_dados_extrato_safra(caminho_pdf)

    if df_resultado.empty:
        messagebox.showwarning("Aviso", "Nenhuma transação válida foi encontrada no arquivo PDF. Verifique se o modelo do extrato está correto.")
        return None

    caminho_salvar = filedialog.asksaveasfilename(
        title="Salvar arquivo Excel",
        defaultextension=".xlsx",
        filetypes=[("Arquivos Excel", "*.xlsx")],
        initialfile="Extrato Safra Convertido.xlsx"
    )
    if not caminho_salvar:
        return None

    try:
        df_resultado.to_excel(caminho_salvar, index=False)
        return caminho_salvar
    except Exception as e:
        messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar o arquivo Excel.\n\nErro: {e}")
        return None