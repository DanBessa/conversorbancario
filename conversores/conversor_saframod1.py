# conversor_safra.py (VERSÃO FINAL - SEM SEPARADOR DE MILHAR)

import pdfplumber
import pandas as pd
import re
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from collections import defaultdict

def limpar_e_converter_valor(valor_str):
    """
    Limpa e converte uma string de moeda para um número float, lidando
    com o formato "1,234.56" encontrado no extrato Safra.
    """
    if not valor_str or not isinstance(valor_str, str):
        return 0.0
    
    str_limpa = valor_str.strip()
    str_limpa = str_limpa.replace(',', '')
    str_limpa = re.sub(r'[^\d.-]', '', str_limpa)

    try:
        return float(str_limpa)
    except (ValueError, TypeError):
        return 0.0

def formatar_para_brl(valor_numerico):
    """
    # <<< ALTERAÇÃO: Formata o número sem o ponto de milhar (ex: 12345,67).
    """
    if not isinstance(valor_numerico, (int, float)):
        return ""
    # Formata o número com duas casas decimais, usando ponto como separador.
    valor_str = f"{valor_numerico:.2f}"
    # Substitui o ponto pela vírgula para o padrão brasileiro.
    valor_str_brl = valor_str.replace('.', ',')
    return valor_str_brl

def iniciar_processamento():
    """
    Função principal que lida com a seleção, processamento e 
    salvamento consolidado dos extratos do Banco Safra.
    """
    root = tk.Tk()
    root.withdraw()

    caminhos_pdf = filedialog.askopenfilenames(
        title="Selecione os extratos do Banco Safra",
        filetypes=[("Arquivos PDF", "*.pdf")]
    )

    if not caminhos_pdf:
        return

    todas_as_transacoes = []
    
    for caminho_pdf in caminhos_pdf:
        try:
            with pdfplumber.open(caminho_pdf) as pdf:
                data_atual = None
                buffer_historico = []

                for pagina in pdf.pages:
                    palavras = pagina.extract_words(x_tolerance=2, y_tolerance=2, keep_blank_chars=False)
                    
                    linhas = defaultdict(list)
                    for palavra in palavras:
                        linhas[round(palavra['top'])].append(palavra)

                    for top in sorted(linhas.keys()):
                        palavras_na_linha = sorted(linhas[top], key=lambda p: p['x0'])
                        linha_texto = " ".join([p['text'] for p in palavras_na_linha])

                        correspondencia_data = re.fullmatch(r"(\d{2}/\d{2}/\d{4})", linha_texto.strip())
                        if correspondencia_data:
                            data_atual = correspondencia_data.group(1)
                            buffer_historico = []
                            continue
                        
                        if "Descrição" in linha_texto and "Valor (R$)" in linha_texto:
                            continue

                        palavras_descricao = []
                        palavras_valor = []
                        for palavra in palavras_na_linha:
                            if palavra['x0'] < 490:
                                palavras_descricao.append(palavra['text'])
                            else:
                                palavras_valor.append(palavra['text'])
                        
                        descricao_linha = " ".join(palavras_descricao).strip()
                        valor_str_completo = " ".join(palavras_valor).strip()

                        if not descricao_linha and not valor_str_completo:
                            continue
                        
                        if descricao_linha:
                            buffer_historico.append(descricao_linha)

                        if valor_str_completo:
                            valores_encontrados = re.findall(r'(-?[\d,]+\.\d+)', valor_str_completo)
                            historico_completo = " ".join(buffer_historico)
                            
                            if len(valores_encontrados) > 1 and "tar pix qr code safrapay" in historico_completo.lower():
                                desc_principal = re.sub(r'tar pix qr code safrapay', '', historico_completo, flags=re.IGNORECASE).strip()
                                val_principal = limpar_e_converter_valor(valores_encontrados[0])
                                if val_principal != 0:
                                    todas_as_transacoes.append({"Data": data_atual, "Histórico": desc_principal, "Valor": val_principal})

                                for val_tarifa_str in valores_encontrados[1:]:
                                    val_tarifa = limpar_e_converter_valor(val_tarifa_str)
                                    if val_tarifa != 0:
                                        todas_as_transacoes.append({"Data": data_atual, "Histórico": "tar pix qr code safrapay", "Valor": val_tarifa})
                            else:
                                for valor_individual_str in valores_encontrados:
                                    valor_numerico = limpar_e_converter_valor(valor_individual_str)
                                    if data_atual and valor_numerico != 0:
                                        todas_as_transacoes.append({"Data": data_atual, "Histórico": historico_completo, "Valor": valor_numerico})
                            
                            buffer_historico = []
                                
        except Exception as e:
            messagebox.showerror("Erro de Processamento", f"Falha ao processar o arquivo '{os.path.basename(caminho_pdf)}'.\n\nDetalhes: {e}")
            return

    if not todas_as_transacoes:
        messagebox.showinfo("Concluído", "Nenhuma transação foi encontrada nos arquivos selecionados.")
        return

    df_final = pd.DataFrame(todas_as_transacoes)

    df_final['Data'] = pd.to_datetime(df_final['Data'], format='%d/%m/%Y')
    df_final.sort_values(by='Data', inplace=True)

    df_final['Data'] = df_final['Data'].dt.strftime('%d/%m/%Y')
    df_final['Valor'] = df_final['Valor'].apply(formatar_para_brl)

    caminho_primeiro_arquivo = caminhos_pdf[0]
    diretorio_base = os.path.dirname(caminho_primeiro_arquivo)
    if len(caminhos_pdf) == 1:
        nome_base, _ = os.path.splitext(os.path.basename(caminho_primeiro_arquivo))
        nome_arquivo_sugerido = nome_base + ".xlsx"
    else:
        nome_arquivo_sugerido = "Extratos Safra Consolidados.xlsx"

    caminho_para_salvar = filedialog.asksaveasfilename(
        title="Salvar arquivo consolidado como...",
        initialdir=diretorio_base,
        initialfile=nome_arquivo_sugerido,
        defaultextension=".xlsx",
        filetypes=[("Arquivos Excel", "*.xlsx")]
    )

    if not caminho_para_salvar:
        return

    try:
        df_final.to_excel(caminho_para_salvar, index=False)
        messagebox.showinfo("Sucesso", f"Arquivo consolidado salvo com sucesso em:\n{caminho_para_salvar}")
    except Exception as e:
        messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar o arquivo consolidado.\n\nErro: {e}")

if __name__ == "__main__":
    iniciar_processamento()