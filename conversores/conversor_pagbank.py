# Arquivo: conversores/conversor_pagbank.py

import pdfplumber
import pandas as pd
import re
from tkinter import messagebox

# A função selecionar_pdfs() foi REMOVIDA, pois não é mais necessária.

def extrair_texto_pdf(pdf_path):
    """
    Extrai transações de um único arquivo PDF e RETORNA um DataFrame.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

        pattern_corrected = re.compile(r"(\d{2}/\d{2}/\d{4})\s+(.+?)\s+(-?R?\$\s?[\d\.]+,\d{2})")
        matches = pattern_corrected.findall(text)

        if not matches:
            print(f"Nenhuma transação encontrada no arquivo: {pdf_path}")
            # Retorna um DataFrame vazio se não encontrar nada.
            return pd.DataFrame()

        # A função agora cria e retorna o DataFrame.
        df = pd.DataFrame(matches, columns=["Data", "Descrição", "Valor"])
        return df

    except Exception as e:
        messagebox.showerror("Erro ao Processar Arquivo", f"Não foi possível processar o arquivo:\n{pdf_path}\n\nErro: {e}")
        # Retorna um DataFrame vazio em caso de erro.
        return pd.DataFrame()

# O bloco if __name__ == "__main__" não é necessário, pois a lógica
# é totalmente controlada pelo script principal menuestilizado.py.