# acionar_licenca.py
import requests
import json

# --- INFORMAÇÕES QUE VOCÊ PRECISA PREENCHER ---

# O ID do seu Gist (o código que aparece na URL, ex: d1a2b3c4d5e6f7g8h9i0)
GIST_ID = "SEU GIST AQUI"

# O nome do arquivo no Gist
NOME_ARQUIVO = "config_licenca.json"

# Seu Token de Acesso Pessoal do GitHub.
# Crie em: GitHub > Settings > Developer settings > Personal access tokens > Tokens (classic)
# Marque a permissão "gist".
TOKEN_GITHUB = "SEU TOKEN AQUI"

# ------------------------------------------------


def mudar_status_licenca(ativar: bool):
    """Altera o status da licença no arquivo de controle do Gist."""

    url = f"https://api.github.com/gists/{GIST_ID}"

    headers = {
        "Authorization": f"token {TOKEN_GITHUB}",
        "Accept": "application/vnd.github.v3+json",
    }

    novo_conteudo = json.dumps({"licenca_obrigatoria": ativar}, indent=2)

    dados = {"files": {NOME_ARQUIVO: {"content": novo_conteudo}}}

    try:
        response = requests.patch(url, headers=headers, data=json.dumps(dados))
        response.raise_for_status()  # Lança um erro se a requisição falhar

        status = "OBRIGATÓRIA" if ativar else "NÃO OBRIGATÓRIA"
        print(f"Sucesso! A licença agora está definida como: {status}")

    except requests.exceptions.RequestException as e:
        print(f"ERRO ao se comunicar com a API do GitHub: {e}")


if __name__ == "__main__":
    # Para exigir a licença, execute o script com o argumento 'ativar'
    # Exemplo: python acionar_licenca.py ativar
    # Para desativar (voltar a ser gratuito), execute sem argumentos ou com 'desativar'
    import sys

    if len(sys.argv) > 1 and sys.argv[1].lower() == "ativar":
        mudar_status_licenca(ativar=True)
    else:
        mudar_status_licenca(ativar=False)
