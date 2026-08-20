"""
Popup de consulta de vale.
"""

import tkinter as tk
from config import BG, BG2, BG3, ACCENT, GOLD, TEXT, TEXT_DIM, SUCCESS, DANGER
from config import FONT_TITLE, FONT_H2, FONT_BODY, FONT_SMALL
from ui.components.base import UIBuilder, ScrollableFrame
from core.database import get_conn
from utils.helpers import brl, agora, vencido


class PopupConsultaVale:
    """Popup de consulta de vale presente."""
    
    def __init__(self, app):
        self.app = app
        self._build()
    
    def _build(self):
        win = tk.Toplevel(self.app)
        win.title("Consultar Vale")
        win.geometry("650x680")
        win.configure(bg=BG)
        win.transient(self.app)
        win.grab_set()
        
        self.scroll_container = ScrollableFrame(win)
        self.scroll_container.pack(fill="both", expand=True)
        pai_tela = self.scroll_container.scrollable_frame
        
        h = UIBuilder.frame(pai_tela, pady=20, padx=28)
        h.pack(side="top", fill="x")
        UIBuilder.label(h, "🔍 Consultar Vale", font=FONT_TITLE).pack(side="left")
        UIBuilder.separator(pai_tela).pack(side="top", fill="x", padx=28)
        
        sf = UIBuilder.frame(pai_tela, padx=40, pady=10)
        sf.pack(side="top", fill="x")
        self._resultado_frame = UIBuilder.frame(sf, bg=sf.cget("bg"))
        
        busc_card = UIBuilder.card(sf, bg=BG2, px=32, py=24)
        busc_card.pack(fill="x", padx=40, pady=(15,10))
        UIBuilder.label(busc_card, "Código:", font=FONT_H2, bg=BG2).pack(anchor="w", pady=(0,12))
        
        row_busca = UIBuilder.frame(busc_card, bg=BG2)
        row_busca.pack(fill="x")
        self._cod_var = tk.StringVar()
        e = tk.Entry(row_busca, textvariable=self._cod_var, font=("Consolas",16,"bold"), bg=BG3, fg=GOLD, insertbackground=GOLD, relief="flat", bd=0, width=22, justify="center")
        e.pack(side="left", ipady=11, padx=(0,12))
        e.bind("<Return>", lambda _: self._consultar())
        UIBuilder.button(row_busca, "🔍 Pesquisar", self._consultar, color=ACCENT, width=16).pack(side="left", ipady=5)
        self._resultado_frame.pack(fill="x", padx=40, pady=10)

    def _consultar(self):
        if not hasattr(self, "_resultado_frame") or not self._resultado_frame.winfo_exists(): 
            return
        for w in list(self._resultado_frame.winfo_children()): 
            w.destroy()
        cod = self._cod_var.get().strip().upper()
        if not cod: 
            return
        with get_conn() as conn:
            row = conn.execute("""
                SELECT v.codigo, c.nome, v.valor, v.usado, v.validade, v.criado, v.observacao, v.usado_em 
                FROM vales v JOIN clientes c ON c.id=v.cliente_id 
                WHERE v.codigo=%s
            """, (cod,)).fetchone()
        if not row:
            rf = UIBuilder.card(self._resultado_frame, bg=BG2, px=24, py=20)
            rf.pack(fill="x", pady=10)
            UIBuilder.label(rf, "❌ Não localizado.", font=FONT_H2, bg=BG2, fg=DANGER).pack(anchor="w")
            return

        v_cod, c_nome, v_valor, v_usado, v_validade, v_criado, v_obs, v_usado_em = row
        _venc = vencido(v_validade) and not v_usado
        if v_usado: 
            status, color_status = "USADO", TEXT_DIM
        elif _venc: 
            status, color_status = "VENCIDO", DANGER
        else: 
            status, color_status = "VÁLIDO", SUCCESS

        rf = UIBuilder.card(self._resultado_frame, bg=BG2, px=36, py=28)
        rf.pack(fill="x", pady=10)
        UIBuilder.label(rf, f"{status} - {v_cod}", font=("Consolas",16,"bold"), bg=BG2, fg=color_status).pack()
        UIBuilder.label(rf, f"Dono: {c_nome}", font=FONT_BODY, bg=BG2, fg=TEXT).pack()
        UIBuilder.label(rf, f"Valor: {brl(v_valor)}", font=FONT_H2, bg=BG2, fg=color_status).pack()

        if not v_usado and not _venc:
            def resgatar():
                with get_conn() as conn:
                    conn.execute("UPDATE vales SET usado=1, usado_em=%s WHERE codigo=%s", (agora(), v_cod))
                    conn.commit()
                self.app.toast.show("Vale resgatado com sucesso!", "sucesso")
                self._consultar()
            UIBuilder.button(rf, "✔ Resgatar Vale", resgatar, color=SUCCESS, fg="#000", width=24).pack(pady=15, ipady=5)