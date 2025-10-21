import re
import pandas as pd
from PyPDF2 import PdfReader
import tkinter as tk
from tkinter import filedialog, messagebox
import os

def selecionar_pdf():
    # Esta função já existe no seu código e está correta para selecionar múltiplos arquivos.
    # Ela será chamada por iniciar_extracao_santander().
    root = tk.Tk()
    root.withdraw()
    return filedialog.askopenfilenames(
        title="Selecione os PDFs do extrato Santander",
        filetypes=[("Arquivos PDF", "*.pdf")]
    )

def extrair_dados(linha, data_corrente):
    # Sua função extrair_dados (sem alterações nesta lógica)
    match_valor = re.search(r"(\d{1,3}(?:\.\d{3})*,\d{2}-?)", linha)
    if not match_valor:
        return None

    valor_raw = match_valor.group(1)
    valor_index = linha.rfind(valor_raw)
    lancamento = linha[:valor_index].strip()

    doc_match = re.search(r"(\d{6,})(?:\s+|\s*-\s*)?" + re.escape(valor_raw), linha)
    documento = doc_match.group(1) if doc_match else ""

    historico_minusculo = lancamento.lower()
    palavras_negativas = ["boleto", "outros bancos", "aplicacao", "pix enviado", "transferência enviada","tarifa","comercial",
                          "tributo","estadual","esgoto","telefone","devolvido","cancelado","estorno","distribuidora","fornecedores","darf","celular","salario","debito pagamento","bananas","ted enviada","pagsal"]
    valor_final_str = "" # Variável para armazenar o valor formatado como string

    for palavra in palavras_negativas:
        if palavra in historico_minusculo:
            valor_final_str = "-" + valor_raw.replace("-", "").rstrip("-")
            break
    else:
        tem_hifen = valor_raw.endswith("-")
        valor_final_str = "-" + valor_raw[:-1] if tem_hifen else valor_raw
    
    return [data_corrente, lancamento, valor_final_str, documento]

def preparar_linha(linhas, idx):
    # Sua função preparar_linha (sem alterações nesta lógica)
    linha = linhas[idx].strip().replace('\t', ' ')
    linhas_usadas = 1
    
    data_inicio_regex_lookahead = re.compile(r"^(\d{2}/\d{2}(?:/\d{2,4})?)\b")
    for offset in range(1, 3):
        if idx + offset < len(linhas):
            extra = linhas[idx + offset].strip().replace('\t', ' ')
            if not re.search(r"\d{1,3}(?:\.\d{3})*,\d{2}-?", linha) and \
               not data_inicio_regex_lookahead.match(extra) and \
               extra:
                linha += " " + extra
                linhas_usadas += 1
            else:
                break
        else:
            break

    linha = re.sub(r"(\d{6,})(\d{1,3}(?:\.\d{3})*,\d{2}-?)", r"\1 \2", linha)
    return linha, linhas_usadas

def processar_pdf(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        data = []
        current_date = ""
        start_extract = False
        data_inicio_regex = re.compile(r"^(\d{2}/\d{2}(?:/\d{2,4})?)\b")
        fim_conteudo = "EXTRATO CONSOLIDADO"

        for i, page in enumerate(reader.pages):
            texto = page.extract_text()
            if not texto:
                continue

            linhas = texto.split('\n')
            idx = 0
            while idx < len(linhas):
                linha_base = linhas[idx].strip()

                if "Movimentação" in linha_base:
                    start_extract = True
                    for skip_idx in range(idx + 1, min(idx + 4, len(linhas))):
                        if re.match(r"^\s*SALDO (ANTERIOR|EM \d{2}/\d{2}/\d{4})", linhas[skip_idx].strip().upper()):
                            idx = skip_idx + 1
                            break
                        if data_inicio_regex.match(linhas[skip_idx].strip()):
                            idx = skip_idx
                            break
                    else:
                        idx += 2
                    continue
                
                if not start_extract or (fim_conteudo in linha_base and not data_inicio_regex.match(linha_base)):
                    idx += 1
                    continue

                linha_completa, usadas = preparar_linha(linhas, idx)

                match_data = data_inicio_regex.match(linha_completa)
                if match_data:
                    current_date = match_data.group(1)
                    linha_completa = data_inicio_regex.sub('', linha_completa, 1).strip()

                if current_date:
                    entrada = extrair_dados(linha_completa, current_date)
                    if entrada:
                        data.append(entrada)

                idx += usadas

        if not data:
            messagebox.showwarning("Aviso", f"Nenhuma transação encontrada ou extraída em:\n{os.path.basename(pdf_path)}")
            return None # <-- MUDANÇA: Retorna None se não encontrar dados

        df = pd.DataFrame(data, columns=["Data", "Lançamento", "Valor", "Documento"])
        
        def converter_valor_para_numerico(valor_str):
            if isinstance(valor_str, (int, float)):
                return valor_str
            s = valor_str.replace('.', '').replace(',', '.')
            try:
                return float(s)
            except ValueError:
                return None

        df["Valor"] = df["Valor"].apply(converter_valor_para_numerico)
        df.drop_duplicates(inplace=True)

        df = df[~df['Lançamento'].str.contains("SALDO ANTERIOR", case=False, na=False)]
        df = df[~df['Lançamento'].str.match(r"^\s*SALDO EM \d{2}/\d{2}(?:/\d{2,4})?\s*$", case=False, na=False)]

        if df.empty:
            messagebox.showwarning("Aviso", f"Nenhuma transação válida após limpeza em:\n{os.path.basename(pdf_path)}")
            return None # <-- MUDANÇA: Retorna None se o dataframe ficar vazio

        csv_path = os.path.splitext(pdf_path)[0] + ".csv"
        df.to_csv(csv_path, index=False, sep=";", decimal=",", encoding="utf-8-sig")
        
        # <-- MUDANÇA 1: Retorna o caminho do CSV em caso de sucesso
        return csv_path

    except Exception as e:
        messagebox.showerror("Erro no Processamento", f"Erro ao processar o arquivo {os.path.basename(pdf_path)}:\n{e}")
        # <-- MUDANÇA: Retorna None se ocorrer um erro
        return None

def iniciar_processamento():
    caminhos_pdf = selecionar_pdf()
    
    if not caminhos_pdf:
        return None # Retorna None se o usuário cancelar a seleção

    caminho_ultimo_salvo = "" # Variável para guardar o caminho do último arquivo salvo
    for caminho_pdf in caminhos_pdf:
        # <-- MUDANÇA 2: Captura o retorno da função processar_pdf
        resultado_path = processar_pdf(caminho_pdf)
        
        # Se o processamento daquele PDF deu certo, guarda o caminho dele
        if resultado_path:
            caminho_ultimo_salvo = resultado_path

    # <-- MUDANÇA 3: Retorna o caminho do último arquivo salvo com sucesso para a interface
    return caminho_ultimo_salvo

if __name__ == "__main__":
    iniciar_processamento()