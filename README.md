# conversorbancario
Conversor de extratos em PDF para CSV

# Conversor Bancário de Extratos PDF para Excel

![Versão](https://img.shields.io/badge/versão-2.0.7-blue)
![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Licença](https://img.shields.io/badge/licença-MIT-green)

Um aplicativo de desktop robusto para extrair transações de extratos bancários em formato PDF e convertê-los para planilhas Excel (`.xlsx`), além de converter arquivos OFX.

![Screenshot do Aplicativo](caminho/para/sua/imagem_do_app.png)
*Substitua o link acima por uma captura de tela real do seu aplicativo!*

---

## ✨ Principais Funcionalidades

- **Conversão de PDF para Excel**: Extrai tabelas de transações de extratos bancários em PDF de forma inteligente.
- **Suporte a Múltiplos Bancos**: Compatível com diversos layouts de extratos de diferentes bancos brasileiros.
- **Conversor OFX**: Ferramenta integrada para converter um ou mais arquivos OFX em uma única planilha Excel, com abas separadas para cada arquivo.
- **Interface Gráfica Moderna**: Desenvolvido com CustomTkinter para uma experiência de usuário limpa e agradável.
- **Atualizador Automático**: O aplicativo verifica novos releases no GitHub e oferece a opção de baixar e instalar a atualização automaticamente.
- **Sistema de Licenciamento**: Inclui um sistema de ativação e verificação de licença.
- **Empacotado para Facilidade**: Distribuído como um único executável para Windows, sem necessidade de instalação de dependências pelo usuário final.

---

## 🏦 Bancos Suportados

Atualmente, o conversor oferece suporte aos seguintes bancos:

- Banco do Brasil
- Banco Inter
- Bradesco
- Banestes
- C6 Bank
- Caixa Econômica Federal
- Itaú
- PagBank
- PayCash
- Safra
- Santander
- Sicoob
- Sicredi
- Stone

---

## 🛠️ Tecnologias Utilizadas

- **Linguagem**: Python 3
- **Interface Gráfica**: [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- **Extração de Dados PDF**: [Camelot-py](https://github.com/camelot-dev/camelot), [PDFPlumber](https://github.com/jsvine/pdfplumber), [PyPDF2](https://pypdf2.readthedocs.io/)
- **Manipulação de Dados**: [Pandas](https://pandas.pydata.org/)
- **Geração de Excel**: [Openpyxl](https://openpyxl.readthedocs.io/)
- **Empacotamento**: [PyInstaller](https://pyinstaller.org/)

---

## 🚀 Instalação e Execução (Ambiente de Desenvolvimento)

Siga os passos abaixo para configurar um ambiente de desenvolvimento limpo e funcional.

### Pré-requisitos

- **Python 3.10 ou superior**: [Download do Python](https://www.python.org/downloads/)
- **Git**: [Download do Git](https://git-scm.com/downloads)
- **Ghostscript**: (Obrigatório para a biblioteca Camelot no Windows) [Download do Ghostscript](https://www.ghostscript.com/releases/gsdnld.html)

### Passos para Configuração

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/seu-usuario/seu-repositorio.git](https://github.com/seu-usuario/seu-repositorio.git)
    cd seu-repositorio
    ```

2.  **Crie e ative um ambiente virtual:**
    ```bash
    # Criar o ambiente (pasta 'venv')
    python -m venv venv

    # Ativar no Windows (PowerShell)
    .\venv\Scripts\activate
    ```
    Seu terminal deve agora mostrar `(venv)` no início do prompt.

3.  **Instale todas as dependências:**
    O arquivo `requirements.txt` contém a lista de todas as bibliotecas nas versões exatas que garantem o funcionamento do projeto.
    ```bash
    pip install -r requirements.txt
    ```

4.  **Execute o aplicativo:**
    ```bash
    python menuestilizado.py
    ```

---

## 📦 Compilando o Executável (`.exe`)

O projeto utiliza o PyInstaller e um arquivo `.spec` customizado para gerar o executável final para distribuição.

1.  **Certifique-se de que o ambiente virtual está ativo.**
    ```powershell
    .\venv\Scripts\activate
    ```

2.  **Execute o PyInstaller usando o arquivo de especificação:**
    O arquivo `menuestilizado.spec` já contém todas as configurações necessárias (inclusão de ícones, pastas, módulos ocultos, etc.).
    ```bash
    pyinstaller menuestilizado.spec
    ```

3.  O executável final estará na pasta `dist/`.

---

## 📂 Estrutura do Projeto

```
.
├── menuestilizado.py       # Script principal da aplicação
├── menuestilizado.spec       # Arquivo de configuração do PyInstaller
├── requirements.txt        # Lista de dependências do projeto
├── conversores/            # Módulos específicos para cada banco
│   ├── conversor_itau.py
│   └── ...
└── icons/                  # Ícones e logotipos usados na interface
    ├── bblogo.png
    └── ...
```

---

## 🤝 Como Contribuir

Contribuições são bem-vindas! Se você deseja adicionar suporte a um novo banco ou melhorar uma funcionalidade existente:

1.  Faça um **Fork** deste repositório.
2.  Crie uma nova **Branch** (`git checkout -b feature/novo-banco`).
3.  Faça suas alterações e **Commit** (`git commit -m 'Adiciona suporte para o Novo Banco'`).
4.  Faça o **Push** para a Branch (`git push origin feature/novo-banco`).
5.  Abra um **Pull Request**.

---

## 📄 Licença

Este projeto é distribuído sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.
