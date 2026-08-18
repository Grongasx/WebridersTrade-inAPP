"""
Tela Novo Vale - Emissão de vale presente.
"""

import tkinter as tk
from tkcalendar import DateEntry
import datetime
import re
from config import BG, BG2, BG3, ACCENT, GOLD, TEXT, TEXT_DIM, DANGER
from config import FONT_TITLE, FONT_H2, FONT_BODY, FONT_SMALL
from ui.screens.base_screen import BaseScreen
from ui.components.base import UIBuilder
from core.database import get_conn
from utils.helpers import gerar_codigo, agora, brl


class NovoValeScreen(BaseScreen):
    """Tela de emissão de novo vale presente."""
    
    def __init__(self, app, content_frame):
        super().__init__(app, content_frame)
        self._valor_var = None
        self._tipo_val = None
        self._obs_var = None
        self._cal = None
    
    def show(self, **kwargs):
        self.clear()
        self._build()
    
    def _build(self):
        h = UIBuilder.frame(self.content, pady=20, padx=28)
        h.pack(fill="x", side="top")
        UIBuilder.label(h, "✨ Emitir Vale Presente", font=FONT_TITLE, fg=GOLD).pack(side="left")
        UIBuilder.separator(self.content).pack(fill="x", padx=28, side="top")

        brow = UIBuilder.frame(self.content, bg=BG, pady=15, padx=40)
        brow.pack(fill="x", side="bottom")
        btn_submit = UIBuilder.button(brow, "✨ Emitir Vale", self._salvar, color=GOLD, fg="#000", width=22)
        btn_submit.pack(side="left")
        UIBuilder.button(brow, "Cancelar", lambda: self.app.show("vales"), color=BG3, width=12).pack(side="left", padx=10)

        sf = UIBuilder.frame(self.content, padx=40, pady=10)
        sf.pack(fill="both", expand=True, side="top")
        _, inner = UIBuilder.scrolled_canvas(sf)

        fm = UIBuilder.card(inner, bg=BG2, px=44, py=25)
        fm.pack(fill="x", padx=40, pady=10)

        UIBuilder.label(
            fm, "ℹ️ O vale é gerado sem cliente associado. Ele será vinculado a um cliente somente quando for resgatado.",
            font=FONT_SMALL, bg=BG2, fg=TEXT_DIM, wraplength=420, justify="left"
        ).pack(anchor="w", pady=(0, 15))

        # Valor
        UIBuilder.label(fm, "Valor (R$) *", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w")
        self._valor_var = tk.StringVar(value="R$ 0,00")
        r_val = UIBuilder.frame(fm, bg=BG2)
        r_val.pack(fill="x")
        e_valor = UIBuilder.entry(r_val, var=self._valor_var, width=36)
        e_valor.pack(fill="x", ipady=7)
        tk.Frame(r_val, bg=GOLD, height=1).pack(fill="x", pady=(0,10))

        def formatar(event=None):
            if event and event.keysym in ("Left","Right","Up","Down","Shift_L","Shift_R","Tab","Return"): 
                return
            val_atual = e_valor.get()
            digits = re.sub(r"\D", "", val_atual)
            if not digits: 
                digits = "0"
            fmt = f"R$ {int(digits)/100:,.2f}".replace(",","X").replace(".",",").replace("X",".")
            if val_atual != fmt:
                e_valor.delete(0, "end")
                e_valor.insert(0, fmt)
                e_valor.icursor("end")
        e_valor.bind("<KeyRelease>", formatar)

        # Atalhos
        bq = UIBuilder.frame(fm, bg=BG2, pady=5)
        bq.pack(fill="x", pady=(0,15))
        UIBuilder.label(bq, "Atalhos:", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(side="left", padx=(0,6))
        for v in [50, 100, 150, 200, 300, 500]:
            UIBuilder.button(bq, f"R$ {v}", lambda x=v: [e_valor.delete(0,"end"), e_valor.insert(0,f"R$ {x},00"), formatar()], 
                           color=BG3, width=5).pack(side="left", padx=2)

        # Validade
        UIBuilder.label(fm, "Validade *", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w")
        r_validade = UIBuilder.frame(fm, bg=BG2, pady=8)
        r_validade.pack(fill="x")
        self._tipo_val = tk.StringVar(value="vitalicio")
        tk.Radiobutton(r_validade, text="∞  Vitalício", variable=self._tipo_val, value="vitalicio", 
                      bg=BG2, fg=TEXT, selectcolor=BG3, activebackground=BG2, font=FONT_BODY, 
                      command=lambda: toggle_cal()).pack(anchor="w", pady=2)
        r_agenda = UIBuilder.frame(r_validade, bg=BG2)
        r_agenda.pack(anchor="w", pady=2)
        tk.Radiobutton(r_agenda, text="📅 Data:", variable=self._tipo_val, value="data", 
                      bg=BG2, fg=TEXT, selectcolor=BG3, activebackground=BG2, font=FONT_BODY, 
                      command=lambda: toggle_cal()).pack(side="left")
        self._cal = DateEntry(r_agenda, width=12, font=FONT_BODY, locale="pt_BR", 
                             date_pattern="dd-mm-yyyy", mindate=datetime.date.today())
        self._cal.pack(side="left", padx=10, ipady=3)

        def toggle_cal(): 
            self._cal.config(state="disabled" if self._tipo_val.get()=="vitalicio" else "readonly")
        toggle_cal()
        tk.Frame(fm, bg=GOLD, height=1).pack(fill="x", pady=(15,15))

        # Observação
        self._obs_var = tk.StringVar()
        UIBuilder.label(fm, "Observação", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w")
        e_obs = UIBuilder.entry(fm, var=self._obs_var, width=36)
        e_obs.pack(fill="x", ipady=7)
        tk.Frame(fm, bg=BG3, height=1).pack(fill="x", pady=(0,10))

    def _salvar(self):
        digits = re.sub(r"\D", "", self._valor_var.get())
        try:
            valor = float(digits) / 100
            if valor <= 0: 
                raise ValueError
        except ValueError:
            self.app.toast.show("⚠ Informe um valor válido.", "erro")
            return

        validade = None if self._tipo_val.get() == "vitalicio" else self._cal.get_date()

        obs = self._obs_var.get().strip() or None

        codigo = gerar_codigo()
        with get_conn() as conn:
            conn.execute("INSERT INTO vales (codigo,cliente_id,valor,validade,criado,observacao) VALUES (%s,%s,%s,%s,%s,%s)", 
                       (codigo, None, valor, validade, agora(), obs))
            conn.commit()

        from core.cache import cache
        cache.invalidate_prefix("vales")
        cache.invalidate_prefix("dashboard")

        self.app.show("confirmacao", codigo=codigo, nome_cli=None, valor=valor, validade=validade)