import pdfplumber
import pandas as pd
import os
from tkinter import filedialog
import re # Importação necessária

def main():
    pdf_path = filedialog.askopenfilename(title="Selecione o PDF da Caixa", filetypes=[("PDF files", "*.pdf")])
    if not pdf_path:
        raise UserWarning("Nenhum arquivo selecionado.")
    
    all_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                all_text += text + "\n"
    
    transactions = []
    
    # Padrão RegEx para encontrar a data (no início da linha)
    date_pattern = re.compile(r'^(\d{2}/\d{2}/\d{4})')
    
    # Padrão RegEx para encontrar o valor 
    # MODIFICADO: Agora procura *apenas* o número (sem sinais)
    value_pattern = re.compile(r'([\d\.]*,\d{2})')

    for line in all_text.split('\n'):
        # 1. Verifica se a linha começa com uma data
        match_date = date_pattern.search(line)
        if not match_date:
            continue # Se não tem data, pula a linha

        # 2. Se tem data, procura pelo valor monetário na linha
        match_value = value_pattern.search(line)
        if not match_value:
            continue # Se tem data mas não tem valor, pula a linha

        # 3. Extrai os dados base
        date = match_date.group(0) # A data (ex: "01/10/2025")
        raw_value = match_value.group(0) # O valor bruto, ex: "150,00"
        
        # O histórico é tudo que está ENTRE a data e o valor
        start_desc = match_date.end()
        end_desc = match_value.start()
        description = line[start_desc:end_desc].strip()
        
        # 4. --- NOVA LÓGICA C/D ---
        # Pega o resto da linha, a partir do fim do valor
        suffix = line[match_value.end():].strip()
        
        final_value = raw_value # Por padrão, o valor é o que lemos

        if suffix.startswith('D'):
            # Se começar com 'D' (Débito), adiciona o hífen
            final_value = "-" + raw_value
        elif suffix.startswith('C'):
            # Se for 'C' (Crédito), já está positivo, não faz nada
            pass 
        
        # 5. Adiciona a transação formatada
        transactions.append([date, description, final_value])
            
    if not transactions:
        raise UserWarning("Nenhuma transação encontrada no PDF da Caixa. Verifique o layout do arquivo.")

    # Renomeando a coluna para refletir melhor o conteúdo
    df = pd.DataFrame(transactions, columns=['Data', 'Histórico', 'Valor']) 
    
    csv_path = os.path.splitext(pdf_path)[0] + ".csv"
    df.to_csv(csv_path, index=False, sep=';', encoding='utf-8-sig')

    return csv_path
