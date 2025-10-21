import os
import sys
import importlib
import pandas as pd
import customtkinter as ctk
from tkinter import messagebox, filedialog
from PIL import Image
from customtkinter import CTkImage
import contextlib
from tkinter import filedialog as tkfiledialog 
import traceback
import json
import base64
import datetime
import requests
import subprocess
import threading
import time
from packaging import version
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature

def is_frozen():
    """ Verifica se o script está rodando como um executável compilado pelo PyInstaller. """
    return hasattr(sys, '_MEIPASS')

# Adiciona a subpasta 'conversores' ao caminho do Python
try:
    base_path = sys._MEIPASS
except AttributeError:
    base_path = os.path.dirname(os.path.abspath(__file__))

conversores_path = os.path.join(base_path, 'conversores')
if conversores_path not in sys.path:
    sys.path.insert(0, conversores_path)

# --- CONFIGURAÇÕES DE ATUALIZAÇÃO E VERSÃO ---
# ### MUDANÇA ### - Lembre-se de atualizar esta variável a cada novo release!
CURRENT_VERSION = "2.0.8" 
GITHUB_REPO = "DanBessa/pdf-table-extractor"
# Mude para True para desativar checagens online durante testes
MODO_DESENVOLVIMENTO = False
# -----------------------------------------------

# --- IDENTIDADE VISUAL ---
COLORS = {
    "background": "#424141", "frame": "#a6a3a3", "accent": "#b9b9b9", "hover": "#d9d9d9",
    "text": "#0f0e0e", "disabled": "#4A4D5A", "success": "#2ECC71", "warning": "#F39C12", "error": "#E74C3C",
    "info": "#f1f3f4", "text_light": "#F0F0F0"
}
FONTS = {"title": ("Consolas", 30, "bold"), "button": ("Consolas UI", 12, "bold"), "status": ("Segoe UI", 12)}

# --- DICIONÁRIO DE CONFIGURAÇÃO DOS CONVERSORES ---
CONVERTERS = {
    "bb": {
        "nome": "Banco do Brasil", "icons": "bblogo.png", "aba": "pdf", "type": "model_choice",
        "model_config": {
            "titulo": "Seleção de Modelo BB",
            "label": "Selecione o modelo do extrato do Banco do Brasil:",
            "opcoes": {"modelo1": "Modelo 1 (Com Cabeçalho)", "modelo2": "Modelo 2"}
        }
    },
    "inter": { "nome": "Inter", "icons": "inter.png", "aba": "pdf", "type": "simple_run", "module": "conversor_inter", "function": "iniciar_processamento" },
    "itau": { "nome": "Itaú", "icons": "itaulogo.png", "aba": "pdf", "type": "itau_special" },
    "sicoob": {
        "nome": "Sicoob", "icons": "sicoob2.png", "aba": "pdf", "type": "model_choice",
        "model_config": {
            "titulo": "Seleção de Modelo Sicoob",
            "label": "Selecione o modelo do extrato do Sicoob:",
            "opcoes": {"modelo1": "Modelo 1",
                       "modelo2": "Modelo 2 (Quebras)",
                       "modelo3": "Modelo 3 (Novo Layout)"}
        }
    },
    "santander": {
        "nome": "Santander", "icons": "santander.png", "aba": "pdf", "type": "model_choice",
        "model_config": {
            "titulo": "Seleção de Modelo Santander",
            "label": "Selecione o modelo do extrato do Santander:",
            "opcoes": {"modelo1": "Modelo 1 (Consolidado)",
                       "modelo2": "Modelo 2",}
        }
    },
    "safra": {
        "nome": "Safra", "icons": "safra.png", "aba": "pdf", "type": "model_choice",
        "model_config": {
            "titulo": "Seleção de Modelo Safra",
            "label": "Selecione o modelo do extrato do Safra:",
            "opcoes": {"modelo1": "Modelo 1 (Simples)",
                       "modelo2": "Modelo 2",}
        }
    },
    "bradesco": { "nome": "Bradesco", "icons": "bradesco.png", "aba": "pdf", "type": "simple_run", "module": "conversor_bradesco", "function": "main" },
    "pagbank": { "nome": "PagBank", "icons": "pagbank.png", "aba": "pdf", "type": "multi_file", "module": "conversor_pagbank", "function": "main", "enabled": True },
    "cef": { "nome": "Caixa Econômica", "icons": "cef.png", "aba": "pdf", "type": "simple_run", "module": "conversor_cef", "function": "main" },
    "c6": { "nome": "C6 Bank", "icons": "c6logo.png", "aba": "pdf", "type": "simple_run", "module": "conversor_c6", "function": "iniciar_processamento" },
    "banestes": { "nome": "Banestes", "icons": "banestes.png", "aba": "pdf", "type": "simple_run", "module": "conversor_banestes", "function": "iniciar_processamento" },
    "paycash": { "nome": "PayCash", "icons": "paycash.png", "aba": "pdf", "type": "simple_run", "module": "conversor_paycash", "function": "iniciar_processamento" },
    # "safra": { "nome": "Safra", "icons": "safra.png", "aba": "pdf", "type": "simple_run", "module": "conversor_safra", "function": "iniciar_processamento" },
    "sicredi": { "nome": "Sicredi", "icons": "sicredi.png", "aba": "pdf", "type": "simple_run", "module": "conversor_sicredi", "function": "iniciar_processamento" },
    "stone": { "nome": "Stone", "icons": "stone.png", "aba": "pdf", "type": "simple_run", "module": "conversor_stone", "function": "main", "enabled": True },
    "ofx": { "nome": "Converter Arquivo(s) OFX para Excel", "icons": None, "aba": "ofx", "type": "ofx" },
}
# --- COLE O CONTEÚDO DA SUA CHAVE PÚBLICA AQUI ---
CHAVE_PUBLICA_PEM = """
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAlH4rwrpr4hdIlStJxsg+
I6Y8I/O19GmifJYGXBOBMLlRnRpndf9qMqZUhR2wq8Xq3s4kP6JGRLPp0paWlzJ6
veMbME1odu8adtfPsgt4mrPlxVdyb5FEmpS56O/fl+t0FlsIAH9cHKBWZ7wRI2cr
eScMJVyCHlUEYjAYH+nQkXJaOj7/G3QEAUv3FhJsiRbXw0sdg8sY14QsHh/1Fjw/
K+DACi0a3oLYqr/M7iPQHFP7oRcZa0mcMNuqcic6VLFS90cQSrv59otqnzSs5B0V
XO/3tee2cRPqZHaWqv6R2uUR8SSpuO2H4xYQDiEfZHFrR0PgGIjD043IfwbHCXlS
BwIDAQAB
-----END PUBLIC KEY-----
"""
# --- COLOQUE APENAS O ID DO SEU GIST AQUI ---
GIST_ID = "88012cdb74eaad2cf9dee06fe465d490"

# --- FUNÇÕES DE VERIFICAÇÃO DE LICENÇA ---
def carregar_chave_publica():
    return serialization.load_pem_public_key(CHAVE_PUBLICA_PEM.encode('utf-8'))

def verificar_licenca_online():
    try:
        url_api = f"https://api.github.com/gists/{GIST_ID}"
        response = requests.get(url_api, timeout=5)
        response.raise_for_status()
        gist_data = response.json()
        conteudo_str = gist_data['files']['config_licenca.json']['content']
        config = json.loads(conteudo_str)
        return config.get("licenca_obrigatoria", False)
    except requests.exceptions.RequestException as e:
        print(f"Aviso: Não foi possível verificar a licença online: {e}")
        return False
    except (KeyError, json.JSONDecodeError) as e:
        print(f"Erro ao processar a resposta da API: {e}")
        return False
    except Exception as e:
        print(f"ERRO GERAL na verificação online: {e}")
        return False

def verificar_licenca_local(caminho_licenca):
    try:
        with open(caminho_licenca, 'r') as f:
            chave_ativacao = f.read()
        pacote_decodificado = base64.b64decode(chave_ativacao)
        pacote = json.loads(pacote_decodificado)
        mensagem = base64.b64decode(pacote['dados'])
        assinatura = base64.b64decode(pacote['assinatura'])
        public_key = carregar_chave_publica()
        public_key.verify(assinatura, mensagem, padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH), hashes.SHA256())
        dados_licenca = json.loads(mensagem)
        data_expiracao = datetime.date.fromisoformat(dados_licenca['expira_em'])
        if datetime.date.today() > data_expiracao:
            messagebox.showerror("Licença Expirada", f"Sua licença expirou em {data_expiracao.strftime('%d/%m/%Y')}.")
            return False
        return True
    except FileNotFoundError:
        return None
    except Exception:
        return False

def pedir_e_ativar_chave(caminho_licenca):
    chave = ctk.CTkInputDialog(text="Por favor, insira sua chave de ativação:", title="Ativação do Programa").get_input()
    if not chave:
        return False
    try:
        pacote_decodificado = base64.b64decode(chave)
        pacote = json.loads(pacote_decodificado)
        mensagem = base64.b64decode(pacote['dados'])
        assinatura = base64.b64decode(pacote['assinatura'])
        public_key = carregar_chave_publica()
        public_key.verify(assinatura, mensagem, padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH), hashes.SHA256())
        dados_licenca = json.loads(mensagem)
        data_expiracao = datetime.date.fromisoformat(dados_licenca['expira_em'])
        if datetime.date.today() > data_expiracao:
            messagebox.showerror("Chave Inválida", "A chave de ativação inserida já está expirada.")
            return False
        with open(caminho_licenca, 'w') as f:
            f.write(chave)
        messagebox.showinfo("Sucesso", f"Programa ativado com sucesso! Sua licença é válida até {data_expiracao.strftime('%d/%m/%Y')}.")
        return True
    except Exception as e:
        messagebox.showerror("Chave Inválida", f"A chave de ativação inserida é inválida ou está corrompida.\n\nDetalhes: {e}")
        return False

# --- CLASSE DE BOTÃO PARA ESTILO CONSISTENTE ---
# --- CLASSE DE BOTÃO PARA ESTILO CONSISTENTE ---
### MUDANÇA - CORREÇÃO DO ERRO DE MÚLTIPLOS VALORES ###
class ModernButton(ctk.CTkButton):
    def __init__(self, master, **kwargs):
        # Retira os argumentos específicos do dicionário kwargs antes de passá-lo adiante.
        # Se o argumento não existir em kwargs, usa um valor padrão.
        anchor = kwargs.pop('anchor', 'w')
        fg_color = kwargs.pop('fg_color', COLORS["accent"])
        hover_color = kwargs.pop('hover_color', COLORS["hover"])
        font = kwargs.pop('font', FONTS["button"])
        height = kwargs.pop('height', 55)

        # Agora, chama o construtor pai com os valores definidos e o restante dos kwargs.
        # Não há mais risco de duplicatas.
        super().__init__(master=master, font=font, fg_color=fg_color, hover_color=hover_color,
                         text_color=COLORS["text"], height=height, corner_radius=10, anchor=anchor,
                         border_spacing=10, compound="left", cursor="hand2", **kwargs)
### MUDANÇA ### - CLASSE ATUALIZADA PARA GERENCIAR A ATUALIZAÇÃO
class UpdateManager:
    def __init__(self, app_instance):
        self.app = app_instance
        self.base_path = self.app._get_base_path()
        self.current_exe_path = os.path.realpath(sys.executable)
        self.current_exe_dir = os.path.dirname(self.current_exe_path)
        
    def cleanup_old_version(self):
        """Procura e remove versões antigas (.old) do executável."""
        old_exe_path = self.current_exe_path + ".old"
        if os.path.exists(old_exe_path):
            try:
                # Tenta remover algumas vezes em caso de lock pelo sistema
                for _ in range(5):
                    try:
                        os.remove(old_exe_path)
                        print(f"Versão antiga '{old_exe_path}' removida com sucesso.")
                        break
                    except PermissionError:
                        time.sleep(1)
                else:
                    print(f"AVISO: Não foi possível remover o arquivo da versão antiga: {old_exe_path}")
            except Exception as e:
                print(f"Erro ao tentar limpar versão antiga: {e}")

    def check_for_updates(self):
        """Verifica se há uma nova versão no GitHub Releases em uma thread separada."""
        def run_check():
            try:
                api_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
                response = requests.get(api_url, timeout=10)
                response.raise_for_status()
                latest_release = response.json()

                latest_version_str = latest_release['tag_name'].lstrip('v').strip()
                current_version_str = CURRENT_VERSION.strip()
                
                print(f"Versão atual: '{current_version_str}' / Versão mais recente: '{latest_version_str}'")

                if version.parse(latest_version_str) > version.parse(current_version_str):
                    self.app.after(0, lambda: self._show_update_dialog(latest_version_str, latest_release))
                else:
                    self.app.after(0, self.app.show_up_to_date_status)

            except requests.exceptions.RequestException as e:
                print(f"Não foi possível verificar atualizações: {e}")
            except Exception as e:
                print(f"Erro ao processar verificação de atualização: {e}")
        
        # Executa a verificação em uma thread para não bloquear a UI
        threading.Thread(target=run_check, daemon=True).start()

    def _show_update_dialog(self, new_version, release_info):
        release_notes = release_info.get('body', "Nenhuma nota de lançamento disponível.")
        title = "Atualização Disponível!"
        message = (
            f"Uma nova versão ({new_version}) está disponível.\n"
            f"Sua versão atual: {CURRENT_VERSION}\n\n"
            f"Notas da versão:\n{release_notes}\n\n"
            "Deseja baixar e instalar a atualização agora?\n"
            "O programa será reiniciado."
        )
        if messagebox.askyesno(title, message):
            # Inicia o download em outra thread para não congelar a UI
            threading.Thread(target=self._download_and_apply_update, args=(release_info,), daemon=True).start()

    def _download_and_apply_update(self, release_info):
        try:
            assets = release_info.get('assets', [])
            # Prioriza .exe
            asset = next((a for a in assets if a['name'].endswith('.exe')), None)
            if not asset:
                self.app.after(0, lambda: messagebox.showerror("Erro de Atualização", "Não foi possível encontrar um arquivo .exe na nova versão."))
                return

            download_url = asset['browser_download_url']
            new_exe_filename = "new_" + os.path.basename(self.current_exe_path)
            temp_update_path = os.path.join(self.current_exe_dir, new_exe_filename)

            self.app.after(0, lambda: self.app.update_status("Baixando atualização...", COLORS["warning"]))
            
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            bytes_downloaded = 0
            
            with open(temp_update_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    bytes_downloaded += len(chunk)
                    if total_size > 0:
                        progress = (bytes_downloaded / total_size) * 100
                        # Limita a frequência de atualização da UI para evitar lentidão
                        if bytes_downloaded == total_size or (bytes_downloaded % (8192 * 10) == 0):
                            self.app.after(0, lambda p=progress: self.app.update_status(f"Baixando... {p:.1f}%", COLORS["warning"]))
            
            self.app.after(0, lambda: self.app.update_status("Download concluído. Aplicando atualização...", COLORS["success"]))
            
            # --- LÓGICA DE ATUALIZAÇÃO "RENAME-ON-REBOOT" ---
            old_exe_path = self.current_exe_path + ".old"
            
            # 1. Renomeia o executável atual para .old
            os.rename(self.current_exe_path, old_exe_path)
            
            # 2. Renomeia o novo executável para o nome original
            os.rename(temp_update_path, self.current_exe_path)
            
            self.app.after(0, lambda: self.app.update_status("Atualização aplicada. Reiniciando...", COLORS["success"]))
            
            # 3. Reinicia a aplicação usando o novo executável
            subprocess.Popen([self.current_exe_path])
            
            # 4. Fecha o processo antigo
            self.app.after(100, self.app.destroy)

        except Exception as e:
            # Em caso de erro, tenta reverter as mudanças
            if 'old_exe_path' in locals() and os.path.exists(old_exe_path):
                try:
                    os.rename(old_exe_path, self.current_exe_path)
                except Exception as revert_e:
                     print(f"Falha CRÍTICA ao reverter a atualização: {revert_e}")
            self.app.after(0, lambda: messagebox.showerror("Erro na Atualização", f"Ocorreu um erro:\n\n{e}"))
            self.app.after(0, lambda: self.app.update_status("Falha na atualização.", COLORS["error"]))

# --- CLASSE PRINCIPAL DA APLICAÇÃO ---
class ConversorApp(ctk.CTk):
    def __init__(self):
        super().__init__(fg_color=COLORS["background"])
        
        self.base_path = self._get_base_path()
        self.update_manager = UpdateManager(self)
        self.update_manager.cleanup_old_version()
        
        if is_frozen() and not MODO_DESENVOLVIMENTO:
            self.update_manager.check_for_updates()
            
        caminho_licenca = os.path.join(self.base_path, 'licenca.dat')
        status_local = verificar_licenca_local(caminho_licenca)
        
        if status_local is True:
            pass
        elif status_local is False:
            self.destroy()
            return
        elif status_local is None:
            if not MODO_DESENVOLVIMENTO and verificar_licenca_online():
                if not pedir_e_ativar_chave(caminho_licenca):
                    self.destroy()
                    return
        
        self.title(f"Conversor Bancário")
        self.geometry("500x500")
        self.resizable(False, False)
        
        self.icons = self._load_icons()
        self._create_widgets()
    @contextlib.contextmanager
    def patch_file_dialogs(self, return_path):
        """
        Gerenciador de contexto para substituir temporariamente as funções de 
        seleção de arquivo e fazê-las retornar um caminho já conhecido.
        """
        if not return_path:
            yield # Se não houver caminho, não faz nada
            return

        # Funções "falsas" que retornarão o caminho pré-selecionado
        def fake_askopenfilename(*args, **kwargs):
            print(f"File dialog 'askopenfilename' interceptado. Retornando: {return_path}")
            return return_path

        def fake_askopenfilenames(*args, **kwargs):
            print(f"File dialog 'askopenfilenames' interceptado. Retornando: {[return_path]}")
            return [return_path]

        # Salva as funções originais
        original_ctk_ask = ctk.filedialog.askopenfilename
        original_tk_ask = tkfiledialog.askopenfilename
        original_ctk_asks = ctk.filedialog.askopenfilenames
        original_tk_asks = tkfiledialog.askopenfilenames
        
        try:
            # Substitui as funções originais pelas nossas funções falsas
            ctk.filedialog.askopenfilename = fake_askopenfilename
            tkfiledialog.askopenfilename = fake_askopenfilename
            ctk.filedialog.askopenfilenames = fake_askopenfilenames
            tkfiledialog.askopenfilenames = fake_askopenfilenames
            yield # Permite a execução do código dentro do bloco 'with'
        finally:
            # Bloco 'finally' garante que as funções originais sejam restauradas
            # mesmo que ocorra um erro na conversão.
            print("Restaurando file dialogs originais.")
            ctk.filedialog.askopenfilename = original_ctk_ask
            tkfiledialog.askopenfilename = original_tk_ask
            ctk.filedialog.askopenfilenames = original_ctk_asks
            tkfiledialog.askopenfilenames = original_tk_asks

    def _get_base_path(self):
        try: return sys._MEIPASS
        except AttributeError: return os.path.dirname(os.path.abspath(__file__))

    def _load_icons(self):
        icons = {}
        pasta_icons = os.path.join(self.base_path, "icons")
        for key, config in CONVERTERS.items():
            if not config.get("icons"): continue
            try:
                path = os.path.join(pasta_icons, config['icons'])
                image = Image.open(path)
                icons[key] = CTkImage(dark_image=image, light_image=image, size=(28, 28))
            except Exception as e: print(f"Erro ao carregar ícone para '{key}': {e}")
        return icons

    ### MUDANÇA ### - A interface foi simplificada para um fluxo "arquivo primeiro".
    def _create_widgets(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=3, pady=3)
        titulo = ctk.CTkLabel(container, text="Conversor Bancário", font=FONTS["title"], text_color=COLORS["info"])
        titulo.pack(pady=(10, 25))
        version_label = ctk.CTkLabel(container, text=f"Versão {CURRENT_VERSION}",
                                     font=("Consolas", 10, "italic"),
                                     text_color="gray70")
        version_label.pack(pady=(0, 10))
        
        tabs = ctk.CTkTabview(container, fg_color=COLORS["frame"], segmented_button_fg_color=COLORS["frame"],
                               segmented_button_selected_color=COLORS["accent"], segmented_button_selected_hover_color=COLORS["hover"],
                               segmented_button_unselected_color=COLORS["frame"], text_color=COLORS["text"],
                               border_width=2, border_color=COLORS["accent"])
        tabs.pack(fill="both", expand=True)
        
        # --- Aba de Conversores PDF ---
        self.tab_pdf = tabs.add("Conversores PDF")
        btn_iniciar_pdf = ModernButton(master=self.tab_pdf, text="Selecionar PDF e Converter",
                                     command=self.iniciar_fluxo_conversao_pdf,
                                     anchor="center", font=("Consolas UI", 16, "bold"), height=80)
        btn_iniciar_pdf.pack(expand=True, fill="x", padx=50, pady=50)

        # --- Aba de Conversor OFX ---
        self.tab_ofx = tabs.add("Conversor OFX")
        ofx_config = CONVERTERS.get("ofx")
        if ofx_config:
            btn_ofx = ModernButton(master=self.tab_ofx, text=ofx_config['nome'],
                                   command=lambda: self.processar_conversao("ofx"),
                                   anchor="center", fg_color="#eeeeee", hover_color="#d9d9d9")
            btn_ofx.pack(expand=True, fill="x", padx=50, pady=50)

        # --- Status Bar ---
        self.status_label = ctk.CTkLabel(container, text="Pronto para iniciar.", font=FONTS["status"], text_color=COLORS["text_light"])
        self.status_label.pack(pady=(20, 0), side="bottom", fill="x")

    ### MUDANÇA ### - Novo método principal que guia o novo fluxo de trabalho.
    def iniciar_fluxo_conversao_pdf(self):
        # 1. Usuário seleciona o arquivo PDF primeiro
        caminho_pdf = filedialog.askopenfilename(
            title="Selecione o arquivo PDF para conversão",
            filetypes=[("Arquivos PDF", "*.pdf")]
        )
        if not caminho_pdf:
            self.update_status("Operação cancelada pelo usuário.", COLORS["warning"])
            self.after(5000, lambda: self.update_status("Pronto para iniciar."))
            return

        # 2. Usuário escolhe a qual banco o PDF pertence
        banco_key = self._escolher_banco_dialog()
        if not banco_key:
            self.update_status("Nenhum banco selecionado.", COLORS["warning"])
            self.after(5000, lambda: self.update_status("Pronto para iniciar."))
            return
            
        # 3. Inicia o processo de conversão com o arquivo e o banco já definidos
        self.processar_conversao(banco_key, caminho_pdf=caminho_pdf)

    ### MUDANÇA ### - Novo dialog para o usuário escolher o banco após selecionar o arquivo.
    def _escolher_banco_dialog(self):
        banco_selecionado = ctk.StringVar()
        janela = ctk.CTkToplevel(self)
        janela.title("Seleção de Banco")
        janela.geometry("700x450") 
        janela.resizable(False, False)
        janela.transient(self)
        janela.grab_set()

        def selecionar_e_fechar(banco_key):
            banco_selecionado.set(banco_key)
            janela.destroy()

        ctk.CTkLabel(janela, text="Para qual banco é este extrato?", font=("Segoe UI", 16, "bold")).pack(pady=(20, 10))

        search_var = ctk.StringVar()
        
        # --- INÍCIO DA MUDANÇA: Controle manual do placeholder ---
        
        placeholder_text = "Busque por um banco..."
        placeholder_color = "gray55"
        
        # Cria o campo de entrada sem o placeholder nativo
        search_entry = ctk.CTkEntry(janela, 
                                    textvariable=search_var,
                                    font=("Segoe UI", 14))
        search_entry.pack(fill="x", padx=15, pady=(0, 10))
        
        # Salva a cor padrão do texto
        default_text_color = search_entry.cget("text_color")

        # Função para quando o usuário clica DENTRO do campo
        def on_focus_in(event):
            if search_entry.get() == placeholder_text:
                search_entry.delete(0, "end")
                search_entry.configure(text_color=default_text_color)

        # Função para quando o usuário clica FORA do campo
        def on_focus_out(event):
            if not search_entry.get():
                search_entry.insert(0, placeholder_text)
                search_entry.configure(text_color=placeholder_color)

        # Associa as funções aos eventos de foco
        search_entry.bind("<FocusIn>", on_focus_in)
        search_entry.bind("<FocusOut>", on_focus_out)

        # Define o estado inicial do campo com o placeholder
        on_focus_out(None)
        
        # --- FIM DA MUDANÇA ---

        scroll_frame = ctk.CTkScrollableFrame(janela, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=15, pady=10)

        pdf_converters = {k: v for k, v in CONVERTERS.items() if v.get('aba') == 'pdf'}
        sorted_converters = sorted(pdf_converters.items(), key=lambda item: item[1]['nome'])

        def popular_lista_bancos(filtro=""):
            for widget in scroll_frame.winfo_children():
                widget.destroy()

            filtro = filtro.lower()
            
            # Garante que o texto do placeholder não seja usado como filtro
            if filtro == placeholder_text.lower():
                filtro = ""

            for key, config in sorted_converters:
                if filtro in config['nome'].lower():
                    btn = ModernButton(master=scroll_frame, text=config['nome'],
                                       image=self.icons.get(key),
                                       command=lambda k=key: selecionar_e_fechar(k))
                    
                    if config.get('enabled') is False:
                        btn.configure(state="disabled", fg_color=COLORS["disabled"])
                    
                    btn.pack(fill="x", padx=10, pady=6)
        
        search_var.trace_add("write", lambda name, index, mode: popular_lista_bancos(search_var.get()))

        popular_lista_bancos()

        self.wait_window(janela)
        return banco_selecionado.get()

    def _set_buttons_state(self, new_state: str):
        # Adapta a função para desabilitar os botões principais nas abas
        for tab in [self.tab_pdf, self.tab_ofx]:
            for widget in tab.winfo_children():
                if isinstance(widget, ModernButton):
                    if new_state == "normal" and widget.cget("fg_color") == COLORS["disabled"]:
                        continue
                    widget.configure(state=new_state)

    def show_up_to_date_status(self):
        default_text = "Pronto para iniciar."
        self.update_status("Você já está na versão mais recente.", COLORS["success"])
        self.after(5000, lambda: self.update_status(default_text))

    def update_status(self, message, color=None):
        self.status_label.configure(text=message, text_color=color or COLORS["text_light"])
        self.update_idletasks()

    ### MUDANÇA ### - A função agora aceita um `caminho_pdf` opcional.
    def processar_conversao(self, key, caminho_pdf=None):
        self._set_buttons_state("disabled")
        self.update_status(f"Iniciando: {CONVERTERS[key]['nome']}", COLORS["warning"])
        try:
            # Passa o caminho do PDF para a função que executa o conversor
            resultado = self.run_converter(key, caminho_pdf)
            if resultado and isinstance(resultado, str):
                self.update_status("Processo concluído com sucesso!", COLORS["success"])
                messagebox.showinfo("Sucesso", f"Arquivo salvo com sucesso em:\n\n{resultado}")
        except UserWarning as e:
            self.update_status("Operação cancelada pelo usuário.", COLORS["warning"])
            if str(e):
                messagebox.showwarning("Operação Cancelada", str(e))
        except Exception:
            error_details = traceback.format_exc()
            messagebox.showerror("Erro Crítico na Execução", f"Ocorreu um erro inesperado:\n\n{error_details}")
            self.update_status("Ocorreu um erro crítico.", COLORS["error"])
        finally:
            self._set_buttons_state("normal")
            self.after(5000, lambda: self.update_status("Pronto para iniciar."))

    ### MUDANÇA ### - A função agora aceita `caminho_pdf` e o passa para os handlers.
    def run_converter(self, key, caminho_pdf=None):
        config = CONVERTERS[key]
        handler_type = config.get("type")
        
        try:
            # Conversores que JÁ foram adaptados não precisam do patch
            if handler_type == "itau_special":
                return self._run_itau_converter(key, config, caminho_pdf)
            elif handler_type == "single_file":
                return self._run_single_file_converter(key, config, caminho_pdf)
            
            # Conversores que abrem suas próprias janelas (OFX, multi-file)
            # ou não precisam de um caminho (ainda) são chamados fora do patch.
            elif handler_type == "ofx":
                return self._run_ofx_converter()
            elif handler_type == "multi_file":
                return self._run_multi_file_converter(key, config)

            # Para todos os outros tipos que chamam módulos externos (`simple_run`, `model_choice`),
            # nós ativamos o patch para interceptar a chamada da janela de arquivo.
            else:
                with self.patch_file_dialogs(caminho_pdf):
                    if handler_type == "model_choice":
                        return self._run_model_choice_converter(key, config)
                    elif handler_type == "simple_run":
                        return self._run_simple_converter(key, config)

        finally:
            if self.winfo_exists() and self.state() == 'withdrawn':
                self.deiconify()

    def _run_ofx_converter(self):
        from ofxparse import OfxParser
        from openpyxl import Workbook
        caminhos = filedialog.askopenfilenames(title="Selecione os arquivos OFX", filetypes=[("Arquivos OFX", "*.ofx")])
        if not caminhos: raise UserWarning("")
        wb = Workbook(); wb.remove(wb.active)
        for path in caminhos:
            self.update_status(f"Processando {os.path.basename(path)}...")
            with open(path, 'r', encoding='latin-1', errors='ignore') as f:
                ofx = OfxParser.parse(f)
            ws = wb.create_sheet(title=os.path.splitext(os.path.basename(path))[0][:31])
            ws.append(['Data', 'Descrição', 'Valor'])
            for t in ofx.account.statement.transactions: ws.append([t.date.strftime('%d/%m/%Y'), t.memo, t.amount])
        caminho_salvamento = os.path.splitext(caminhos[0])[0] + ".xlsx"
        wb.save(caminho_salvamento)
        return caminho_salvamento

    def _run_model_choice_converter(self, key, config):
        modelo = self._escolher_modelo(config['model_config'])
        if not modelo: raise UserWarning("")
        # Nota: Assumimos que a função 'iniciar_processamento' dentro destes módulos
        # vai pedir ao usuário para selecionar o arquivo. Não passamos o caminho_pdf
        # para não quebrar a compatibilidade com eles.
        module_name = f"conversor_{key}mod{modelo[-1]}"
        module = importlib.import_module(module_name)
        return module.iniciar_processamento()

    ### MUDANÇA ### - Esta função agora usa o `caminho_pdf` recebido.
    def _run_single_file_converter(self, key, config, path):
        # Se o caminho não foi fornecido (por algum motivo), pede ao usuário como fallback.
        if not path:
            path = filedialog.askopenfilename(title=f"Selecione o PDF do {config['nome']}", filetypes=[("PDF files", "*.pdf")])
        if not path: raise UserWarning("")
        module = importlib.import_module(config['module'])
        func = getattr(module, config['function'])
        return func(path)

    def _run_multi_file_converter(self, key, config, caminho_pdf=None):
        module = importlib.import_module(config['module'])
        
        # MUDANÇA CRÍTICA: Em vez de chamar a janela de seleção de arquivo,
        # usamos o caminho do PDF que já foi selecionado pelo usuário.
        if not caminho_pdf:
            messagebox.showerror("Erro", "Nenhum caminho de arquivo foi fornecido para o conversor.")
            raise UserWarning("Nenhum arquivo para processar.")
        
        paths = [caminho_pdf] # O tratamos como uma lista para manter a lógica de processamento em lote
        
        all_dataframes = []
        self.update_status(f"Processando {len(paths)} arquivo(s)...", COLORS["warning"])
        
        for i, path in enumerate(paths):
            self.update_status(f"Lendo arquivo {i+1}/{len(paths)}: {os.path.basename(path)}", COLORS["warning"])
            try:
                # A lógica de extração chama a função correta do módulo (extrair_texto_pdf)
                df = module.extrair_texto_pdf(path)
                if df is not None and not df.empty:
                    all_dataframes.append(df)
            except Exception as e:
                messagebox.showwarning("Erro de Leitura", f"Não foi possível processar o arquivo:\n{os.path.basename(path)}\n\nErro: {e}")
                continue
        
        if not all_dataframes:
            # Mostra um aviso mais amigável em vez de levantar uma exceção
            messagebox.showinfo("Aviso", "Nenhuma transação encontrada no arquivo selecionado.")
            return None # Retorna None para indicar que o processo terminou sem gerar arquivo

        self.update_status("Consolidando dados...", COLORS["warning"])
        try:
            combined_df = pd.concat(all_dataframes, ignore_index=True)
        except Exception as e:
            messagebox.showerror("Erro de Consolidação", f"Ocorreu um erro ao juntar os dados dos arquivos.\n\nErro: {e}")
            return None

        # A lógica de salvamento permanece a mesma
        caminho_salvar = os.path.splitext(paths[0])[0] + ".xlsx"
        
        if not caminho_salvar: raise UserWarning("Operação de salvamento cancelada.")
        
        self.update_status("Salvando arquivo Excel...", COLORS["warning"])
        try:
            combined_df.to_excel(caminho_salvar, index=False)
            return caminho_salvar
        except Exception as e:
            messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar o arquivo Excel.\n\nErro: {e}")
            return None
            
    # Para que a mudança funcione, precisamos passar o argumento `caminho_pdf` no `run_converter`
    # Por favor, verifique se seu método `run_converter` já está passando esse argumento para 
    # _run_multi_file_converter. Deve se parecer com isto:

    def run_converter(self, key, caminho_pdf=None):
        config = CONVERTERS[key]
        handler_type = config.get("type")
        
        try:
            if handler_type == "multi_file":
                 # Garanta que o caminho_pdf está sendo passado aqui
                return self._run_multi_file_converter(key, config, caminho_pdf)

            # ... resto do seu método run_converter ...
            # (o código abaixo deve estar correto com base nas nossas interações anteriores)

            elif handler_type == "itau_special":
                return self._run_itau_converter(key, config, caminho_pdf)
            elif handler_type == "single_file":
                return self._run_single_file_converter(key, config, caminho_pdf)
            elif handler_type == "ofx":
                return self._run_ofx_converter()
            else:
                with self.patch_file_dialogs(caminho_pdf):
                    if handler_type == "model_choice":
                        return self._run_model_choice_converter(key, config)
                    elif handler_type == "simple_run":
                        return self._run_simple_converter(key, config)
        finally:
            if self.winfo_exists() and self.state() == 'withdrawn':
                self.deiconify()
    
    ### MUDANÇA ### - Esta função agora usa o `caminho_pdf` recebido.
    def _run_itau_converter(self, key, config, path):
        # Se o caminho não foi fornecido, pede ao usuário como fallback.
        if not path:
            path = filedialog.askopenfilename(title="Selecione o PDF do Itaú", filetypes=[("PDF files", "*.pdf")])
        if not path: raise UserWarning("")
        itau_configs = {'flavor': 'stream', 'page_1': {'table_areas': ['149,257, 552,21'], 'columns': ['144,262, 204,262, 303,262, 351,262, 406,262, 418,262, 467,262, 506,262, 553,262']}, 'page_2_end': {'table_areas': ['151,760, 553,20'], 'columns': ['157,757, 173,757, 269,757, 309,757, 363,757, 380,757, 470,757, 509,757, 545,757']}}
        module = importlib.import_module("conversor_itau")
        extractor = module.PDFTableExtractor(path, itau_configs)
        return extractor.start()

    def _run_simple_converter(self, key, config):
        # Nota: Assim como 'model_choice', assumimos que a função chamada aqui
        # já implementa sua própria lógica de seleção de arquivo.
        module = importlib.import_module(config['module'])
        func = getattr(module, config['function'])
        caminho_salvo = func() 
        if not caminho_salvo: raise UserWarning("")
        return caminho_salvo

    def _escolher_modelo(self, config_modelo):
        modelo_selecionado = ctk.StringVar()
        janela = ctk.CTkToplevel(self)
        janela.title(config_modelo['titulo']); janela.geometry("700x180"); janela.resizable(False, False)
        janela.transient(self); janela.grab_set()
        def selecionar_e_fechar(modelo):
            modelo_selecionado.set(modelo)
            janela.destroy()
        ctk.CTkLabel(janela, text=config_modelo['label'], font=("Segoe UI", 14)).pack(pady=20)
        frame_botoes = ctk.CTkFrame(janela, fg_color="transparent")
        frame_botoes.pack(pady=10)
        for key, text in config_modelo['opcoes'].items():
            ctk.CTkButton(frame_botoes, text=text, command=lambda m=key: selecionar_e_fechar(m), width=180).pack(side="left", padx=10, pady=10)
        self.wait_window(janela)
        return modelo_selecionado.get()

if __name__ == "__main__":
    try:
        app = ConversorApp()
        if hasattr(app, 'title') and app.winfo_exists(): # Checa se o app foi inicializado corretamente
            app.mainloop()
    except Exception as e:
        messagebox.showerror("Erro Crítico de Inicialização", f"O programa não pôde ser iniciado.\n\n{traceback.format_exc()}")