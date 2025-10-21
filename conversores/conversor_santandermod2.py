import re
import pandas as pd
from PyPDF2 import PdfReader
import tkinter as tk
from tkinter import filedialog, messagebox
import os

def selecionar_pdf():
    """Abre uma janela para o usuário selecionar um ou mais arquivos PDF."""
    root = tk.Tk()
    root.withdraw()
    return filedialog.askopenfilenames(
        title="Selecione os extratos Santander (Modelo 3 Final)",
        filetypes=[("Arquivos PDF", "*.pdf")]
    )

def limpar_valor(valor_str):
    """Remove a formatação monetária e converte para um número float."""
    if not valor_str:
        return 0.0
    s = str(valor_str).replace('.', '').replace(',', '.')
    try:
        return float(s)
    except (ValueError, TypeError):
        return 0.0

def processar_pdf_mod3(pdf_path):
    """
    Extrai transações de um PDF Santander com uma lógica robusta para todos os casos.
    """
    try:
        reader = PdfReader(pdf_path)
        full_text = ""
        for page in reader.pages:
            texto_pagina = page.extract_text()
            if texto_pagina:
                full_text += texto_pagina + "\n"

        if not full_text:
            messagebox.showwarning("Aviso", f"Não foi possível extrair texto do arquivo:\n{os.path.basename(pdf_path)}")
            return None

        transacoes = []
        transacao_pendente = None

        padrao_data_inicio = re.compile(r"^(\d{2}/\d{2}/\d{4})\s+(.*)")
        # Regex para encontrar todos os valores no formato monetário (ex: 1.234,56 ou -78,90)
        padrao_monetario = re.compile(r"-?[\d\.]*,\d{2}")

        palavras_negativas = [
            "boleto", "pix enviado", "tarifa", "tributo", "pagamento", "conta",
            "devolvido", "cancelado", "estorno", "darf", "ted enviada",
            "iof", "juros", "fgts"
        ]

        linhas = full_text.split('\n')

        for linha in linhas:
            linha = linha.strip()
            if not linha or "SALDO ANTERIOR" in linha.upper():
                continue

            match_data = padrao_data_inicio.match(linha)

            if match_data:
                if transacao_pendente:
                    transacao_pendente = None

                data_str = match_data.group(1)
                resto_linha = match_data.group(2).strip()

                # Encontra todos os valores monetários na linha
                valores_encontrados = padrao_monetario.findall(resto_linha)

                if len(valores_encontrados) > 0:
                    # Se há 2 valores (transação e saldo), pega o primeiro.
                    # Se há 1 valor, pega ele mesmo.
                    valor_str = valores_encontrados[-2] if len(valores_encontrados) >= 2 else valores_encontrados[-1]
                    
                    # A descrição é tudo que vem antes da primeira ocorrência do valor encontrado
                    posicao_valor = resto_linha.rfind(valor_str)
                    desc = resto_linha[:posicao_valor].strip()
                    
                    valor = limpar_valor(valor_str)
                    is_negativo = any(palavra in desc.lower() for palavra in palavras_negativas)
                    if is_negativo and valor > 0:
                        valor = -valor

                    transacoes.append({"Data": data_str, "Lançamento": desc, "Valor": valor})
                
                else: # Linha com data mas sem valor, início de transação multi-linha
                    transacao_pendente = {"Data": data_str, "Lançamento": resto_linha}

            elif transacao_pendente:
                valores_encontrados = padrao_monetario.findall(linha)

                if len(valores_encontrados) > 0:
                    valor_str = valores_encontrados[0] # Pega o primeiro valor da linha de continuação
                    posicao_valor = linha.rfind(valor_str)
                    desc_complemento = linha[:posicao_valor].strip()

                    desc_final = f"{transacao_pendente['Lançamento']} {desc_complemento}".strip()
                    valor = limpar_valor(valor_str)
                    
                    is_negativo = any(palavra in desc_final.lower() for palavra in palavras_negativas)
                    if is_negativo and valor > 0:
                        valor = -valor
                    
                    transacoes.append({"Data": transacao_pendente['Data'], "Lançamento": desc_final, "Valor": valor})
                    
                    transacao_pendente = None

        if not transacoes:
            messagebox.showwarning("Aviso", f"Nenhuma transação encontrada no formato esperado em:\n{os.path.basename(pdf_path)}")
            return None

        df = pd.DataFrame(transacoes)
        
        csv_path = os.path.splitext(pdf_path)[0] + "_mod3_corrigido.csv"
        df.to_csv(csv_path, index=False, sep=";", decimal=",", encoding="utf-8-sig")
        
        return csv_path

    except Exception as e:
        messagebox.showerror("Erro no Processamento", f"Erro ao processar o arquivo {os.path.basename(pdf_path)}:\n{e}")
        return None

def iniciar_processamento():
    """Função principal para orquestrar a seleção e processamento dos PDFs."""
    caminhos_pdf = selecionar_pdf()
    
    if not caminhos_pdf:
        return None

    caminho_ultimo_salvo = ""
    for caminho_pdf in caminhos_pdf:
        resultado_path = processar_pdf_mod3(caminho_pdf)
        if resultado_path:
            caminho_ultimo_salvo = resultado_path

    return caminho_ultimo_salvo

if __name__ == "__main__":
    iniciar_processamento()