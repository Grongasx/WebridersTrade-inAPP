"""
Tela Novo Cliente - Cadastro de novos clientes com máscaras fluidas e validação.
"""

import tkinter as tk
import psycopg
import re
from config import BG, BG2, BG3, ACCENT, GOLD, TEXT, TEXT_DIM, DANGER
from config import FONT_TITLE, FONT_H2, FONT_BODY, FONT_SMALL
from ui.screens.base_screen import BaseScreen
from ui.components.base import UIBuilder
from core.database import get_conn
from utils.helpers import agora, validar_cpf


def formatar_cpf_texto(texto: str) -> str:
    """Formata uma string de números para o padrão xxx.xxx.xxx-xx."""
    numeros = re.sub(r"\D", "", texto)[:11]
    out = ""
    for i, char in enumerate(numeros):
        if i in (3, 6):
            out += "."
        elif i == 9:
            out += "-"
        out += char
    return out


def formatar_tel_texto(texto: str) -> str:
    """Formata telefone/celular: (XX) XXXX-XXXX ou (XX) XXXXX-XXXX."""
    numeros = re.sub(r"\D", "", texto)[:11]
    if not numeros:
        return ""
    
    out = "(" + numeros[:2]
    if len(numeros) > 2:
        out += ") "
        if len(numeros) <= 6:
            out += numeros[2:]
        elif len(numeros) <= 10:  # Telefone Fixo: (XX) XXXX-XXXX
            out += numeros[2:6] + "-" + numeros[6:]
        else:  # Celular: (XX) XXXXX-XXXX
            out += numeros[2:7] + "-" + numeros[7:]
    return out


def validar_email_texto(email: str) -> bool:
    """Valida se o email possui formato padrão usuario@dominio.com."""
    padrao = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return bool(re.match(padrao, email))


class NovoClienteScreen(BaseScreen):
    """Tela de cadastro de novo cliente."""
    
    def __init__(self, app, content_frame):
        super().__init__(app, content_frame)
        self._vs_cli = None
    
    def show(self, **kwargs):
        self.clear()
        self._build()
    
    def _build(self):
        self._vs_cli = {k: tk.StringVar() for k in ["nome", "email", "tel", "cpf"]}

        h = UIBuilder.frame(self.content, pady=20, padx=28)
        h.pack(side="top", fill="x")
        UIBuilder.label(h, "Novo Cliente", font=FONT_TITLE).pack(side="left")

        footer = UIBuilder.frame(self.content, bg=BG2, pady=20, padx=40)
        footer.pack(side="bottom", fill="x")
        UIBuilder.button(footer, "🧹 Limpar", lambda: [v.set("") for v in self._vs_cli.values()], color=BG3, width=12).pack(side="left")
        UIBuilder.button(footer, "Cancelar", lambda: self.app.show("clientes"), color=BG3, width=15).pack(side="right", padx=(10, 0))
        sb = UIBuilder.button(footer, "✅  Cadastrar Cliente", self._salvar, color=ACCENT, width=22)
        sb.pack(side="right")
        sb.config(font=("Segoe UI", 11, "bold"))

        sf = UIBuilder.frame(self.content, padx=40, pady=10)
        sf.pack(side="top", fill="both", expand=True)
        fm = UIBuilder.card(sf, bg=BG2, px=44, py=32)
        fm.pack(fill="x", padx=40, pady=20)
        UIBuilder.label(fm, "Cadastrar novo cliente", font=FONT_H2, bg=BG2).pack(anchor="w", pady=(0, 22))

        # Nome e CPF (CPF agora é opcional)
        row1 = UIBuilder.frame(fm, bg=BG2, pady=10)
        row1.pack(fill="x")
        col_L = UIBuilder.frame(row1, bg=BG2)
        col_L.pack(side="left", fill="x", expand=True, padx=(0, 15))
        col_R = UIBuilder.frame(row1, bg=BG2)
        col_R.pack(side="left", fill="x", expand=True, padx=(15, 0))

        self._campo(col_L, "Nome completo *", self._vs_cli["nome"])
        self._campo(col_R, "CPF", self._vs_cli["cpf"], key_callback=self._on_cpf_key)

        # Email e Telefone (Email agora é opcional)
        row2 = UIBuilder.frame(fm, bg=BG2, pady=10)
        row2.pack(fill="x")
        col_L2 = UIBuilder.frame(row2, bg=BG2)
        col_L2.pack(side="left", fill="x", expand=True, padx=(0, 15))
        col_R2 = UIBuilder.frame(row2, bg=BG2)
        col_R2.pack(side="left", fill="x", expand=True, padx=(15, 0))

        self._campo(col_L2, "E-mail", self._vs_cli["email"])
        self._campo(col_R2, "Telefone *", self._vs_cli["tel"], key_callback=self._on_tel_key)

    def _campo(self, parent, label, var, key_callback=None):
        r = UIBuilder.frame(parent, bg=BG2)
        r.pack(fill="x")
        UIBuilder.label(r, label, font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w")
        e = UIBuilder.entry(r, var=var)
        e.pack(fill="x", ipady=7, pady=(4, 2))
        tk.Frame(r, bg=ACCENT, height=1).pack(fill="x")
        e.bind("<Return>", lambda _: self._salvar())
        if key_callback:
            e.bind("<KeyRelease>", key_callback)
        return e

    # ═══════════════════════════════════════════
    # Formatação em Tempo Real com Controle do Cursor
    # ═══════════════════════════════════════════
    def _on_cpf_key(self, event):
        """Aplica a máscara no CPF mantendo a posição do cursor ajustada."""
        if event.keysym in ("Left", "Right", "Up", "Down", "Tab", "Shift_L", "Shift_R", "Control_L", "Control_R", "Return", "Escape"):
            return

        entry = event.widget
        texto_atual = entry.get()
        formatado = formatar_cpf_texto(texto_atual)

        if texto_atual != formatado:
            self._vs_cli["cpf"].set(formatado)
            entry.icursor(tk.END)

    def _on_tel_key(self, event):
        """Aplica a máscara no Telefone mantendo a posição do cursor ajustada."""
        if event.keysym in ("Left", "Right", "Up", "Down", "Tab", "Shift_L", "Shift_R", "Control_L", "Control_R", "Return", "Escape"):
            return

        entry = event.widget
        texto_atual = entry.get()
        formatado = formatar_tel_texto(texto_atual)

        if texto_atual != formatado:
            self._vs_cli["tel"].set(formatado)
            entry.icursor(tk.END)

    # ═══════════════════════════════════════════
    # Validação e Salvamento
    # ═══════════════════════════════════════════
    def _salvar(self):
        nome = self._vs_cli["nome"].get().strip()
        email = self._vs_cli["email"].get().strip()
        tel = self._vs_cli["tel"].get().strip()
        cpf = self._vs_cli["cpf"].get().strip()
        
        # 1. Validação de Nome
        if not nome:
            self.app.toast.show("⚠ O nome completo é obrigatório.", "erro")
            return
            
        # 2. Validação de CPF (Opcional, mas se preenchido precisa ser válido)
        if cpf and not validar_cpf(cpf):
            self.app.toast.show("⚠ CPF inválido. Verifique os números digitados.", "erro")
            return
            
        # 3. Validação de E-mail (Opcional, mas se preenchido precisa ser válido)
        if email and not validar_email_texto(email):
            self.app.toast.show("⚠ E-mail inválido. Utilize o formato nome@dominio.com", "erro")
            return
            
        # 4. Validação de Telefone (Garante pelo menos 10 dígitos: DDD + número)
        if not tel:
            self.app.toast.show("⚠ O telefone é obrigatório.", "erro")
            return
        tel_numeros = re.sub(r"\D", "", tel)
        if len(tel_numeros) < 10:
            self.app.toast.show("⚠ Telefone inválido. Informe o DDD e o número completo.", "erro")
            return

        # Trata campos opcionais para salvarem como NULL no banco caso estejam vazios
        cpf_db = cpf if cpf else None
        email_db = email if email else None

        # 5. Salvar no Banco
        try:
            with get_conn() as conn:
                conn.execute(
                    "INSERT INTO clientes (nome,email,telefone,cpf,criado) VALUES (%s,%s,%s,%s,%s)",
                    (nome, email_db, tel, cpf_db, agora())
                )
                conn.commit()
            
            for v in self._vs_cli.values():
                v.set("")
                
            self.app.toast.show(f"🎉 Cliente '{nome}' cadastrado com sucesso!", "sucesso")
            self.app.show("clientes")
            
        except psycopg.IntegrityError:
            self.app.toast.show("⚠ Erro: Este E-mail ou CPF já está cadastrado.", "erro")
        except Exception as e:
            self.app.toast.show(f"⚠ Erro ao cadastrar cliente: {str(e)}", "erro")