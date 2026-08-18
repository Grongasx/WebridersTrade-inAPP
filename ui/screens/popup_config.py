"""
Popups de configuração de etiquetas e Designer Visual No-Code.
Recursos:
 - Sincronização e recálculo dinâmico do Gap para eliminar desvio horizontal acumulativo
 - Suporte a margens verticais e horizontais estritas
"""

import json
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Dict
from PIL import Image, ImageDraw, ImageFont, ImageTk

from config import (
    BG,
    BG2,
    BG3,
    GOLD,
    TEXT,
    TEXT_DIM,
    SUCCESS,
    DANGER,
    ACCENT,
    FONT_H2,
    FONT_BODY,
    FONT_SMALL,
)
from ui.components.base import UIBuilder
from core.database import get_conn
from core.config_local import carregar_config_local, salvar_config_local
from utils.helpers import brl, agora, gerar_e_persistir_ean13, gerar_imagem_ean13


class PopupAddProduto:
    """Popup avançado para pesquisar e adicionar produtos na fila de impressão."""

    def __init__(self, app, callback):
        self.app = app
        self.callback = callback
        self._build()

    def _build(self):
        win = tk.Toplevel(self.app)
        win.title("Adicionar Produto à Fila de Impressão")
        win.geometry("720x580")
        win.minsize(620, 480)
        win.configure(bg=BG)
        win.grab_set()

        # Cabeçalho Modal
        h_modal = UIBuilder.frame(win, bg=BG2, padx=18, pady=12)
        h_modal.pack(fill="x")
        UIBuilder.label(
            h_modal, "📦 Adicionar Produto à Fila", font=FONT_H2, bg=BG2, fg=GOLD
        ).pack(anchor="w")

        # Corpo Modal
        b_modal = UIBuilder.frame(win, bg=BG, padx=18, pady=12)
        b_modal.pack(fill="both", expand=True)

        # Barra de Pesquisa Dinâmica
        f_busca = UIBuilder.frame(b_modal, bg=BG, pady=4)
        f_busca.pack(fill="x")
        UIBuilder.label(
            f_busca,
            "🔍 Pesquisar Produto (ID, Nome, Marca, Modelo, Dono ou SKU):",
            font=FONT_SMALL,
            bg=BG,
            fg=TEXT,
        ).pack(anchor="w", pady=(0, 4))

        v_busca = tk.StringVar()
        e_busca = UIBuilder.entry(f_busca, var=v_busca, width=40)
        e_busca.pack(fill="x", ipady=5)
        e_busca.focus_set()

        # Treeview de Produtos
        tf_prod = UIBuilder.frame(b_modal, bg=BG2, pady=6)
        tf_prod.pack(fill="both", expand=True, pady=(8, 10))

        cols = ("ID", "Produto / Modelo", "EAN-13", "SKU", "Dono", "Preço")
        tv_prod = UIBuilder.make_tree(
            tf_prod,
            cols,
            [50, 210, 110, 110, 110, 80],
            ["center", "w", "center", "center", "w", "center"],
        )

        # Carregamento inteligente em memória com MemoryCache
        from core.cache import cache
        todos_prods = cache.get("outlet:produtos_modal")
        if todos_prods is None:
            with get_conn() as conn:
                raw_rows = conn.execute("""
                    SELECT p.id, p.nome, p.marca, p.modelo, p.grafico, p.preco_outlet, 
                           p.sku, p.codigo_barras, c.nome, p.tamanho
                    FROM produtos_outlet p
                    LEFT JOIN clientes c ON p.cliente_id = c.id
                    ORDER BY p.id DESC
                """).fetchall()

            todos_prods = []
            for r in raw_rows:
                pid = r[0]
                nome = r[1] or ""
                marca = r[2] or ""
                modelo = r[3] or ""
                grafico = r[4] or ""
                preco_val = r[5]
                preco_str = brl(preco_val) if preco_val is not None else "R$ 0,00"
                sku = r[6] or "—"
                ean = r[7] or f"200{pid:09d}"
                dono = r[8] or "—"

                prod_desc = f"{marca} {modelo}".strip() or nome
                if grafico:
                    prod_desc += f" ({grafico})"
                if not prod_desc:
                    prod_desc = f"Produto #{pid}"

                conteudo = f"{pid} {nome} {marca} {modelo} {grafico} {dono} {sku} {ean}".lower()
                todos_prods.append((pid, prod_desc, ean, sku, dono, preco_str, conteudo))

            cache.set("outlet:produtos_modal", todos_prods, ttl=60)

        def filtrar(*_):
            termo = v_busca.get().strip().lower()
            for item in tv_prod.get_children():
                tv_prod.delete(item)

            for item in todos_prods:
                pid, prod_desc, ean, sku, dono, preco_str, conteudo = item
                if termo and termo not in conteudo:
                    continue
                tv_prod.insert(
                    "", "end", iid=str(pid), values=(pid, prod_desc, ean, sku, dono, preco_str)
                )

        v_busca.trace_add("write", filtrar)
        filtrar()

        # Barra Inferior: Quantidade com Spinbox / Stepper (mínimo 1) e Botões
        bot_bar = UIBuilder.card(b_modal, bg=BG2, px=14, py=10)
        bot_bar.pack(fill="x", pady=(4, 0))

        lbl_qtd = UIBuilder.label(
            bot_bar, "Quantidade de Cópias:", font=FONT_BODY, bg=BG2, fg=TEXT
        )
        lbl_qtd.pack(side="left", padx=(4, 10))

        v_qtd_prod = tk.StringVar(value="1")

        def decrementar():
            try:
                val = int(v_qtd_prod.get())
                if val > 1:
                    v_qtd_prod.set(str(val - 1))
            except ValueError:
                v_qtd_prod.set("1")

        def incrementar():
            try:
                val = int(v_qtd_prod.get())
                v_qtd_prod.set(str(max(1, val + 1)))
            except ValueError:
                v_qtd_prod.set("1")

        btn_dec = tk.Button(
            bot_bar,
            text="➖",
            command=decrementar,
            bg=BG3,
            fg=TEXT,
            activebackground=ACCENT,
            activeforeground="#FFF",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=6,
            pady=2,
            cursor="hand2",
        )
        btn_dec.pack(side="left", padx=(0, 2))

        sp_qtd = ttk.Spinbox(
            bot_bar,
            from_=1,
            to=9999,
            textvariable=v_qtd_prod,
            width=5,
            justify="center",
            font=("Segoe UI", 10, "bold"),
        )
        sp_qtd.pack(side="left", padx=2)

        btn_inc = tk.Button(
            bot_bar,
            text="➕",
            command=incrementar,
            bg=BG3,
            fg=TEXT,
            activebackground=ACCENT,
            activeforeground="#FFF",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=6,
            pady=2,
            cursor="hand2",
        )
        btn_inc.pack(side="left", padx=(2, 15))

        def confirmar():
            sel = tv_prod.selection()
            if not sel:
                # Se não houver seleção mas a busca retornou exatamente 1 item, seleciona ele
                filhos = tv_prod.get_children()
                if len(filhos) == 1:
                    sel = [filhos[0]]
                else:
                    self.app.toast.show("Selecione um produto na lista.", "aviso")
                    return

            try:
                qtd_final = int(v_qtd_prod.get().strip())
                if qtd_final < 1:
                    qtd_final = 1
            except ValueError:
                qtd_final = 1

            prod_id = int(sel[0])

            try:
                with get_conn() as conn:
                    p_row = conn.execute("""
                        SELECT p.id, p.nome, p.preco_outlet, p.sku, p.codigo_barras, 
                               p.marca, p.modelo, p.tamanho, c.nome
                        FROM produtos_outlet p 
                        LEFT JOIN clientes c ON p.cliente_id = c.id 
                        WHERE p.id = %s
                    """, (prod_id,)).fetchone()

                    if not p_row:
                        self.app.toast.show("Produto não encontrado no banco.", "erro")
                        return

                    cod_final = gerar_e_persistir_ean13(conn, prod_id, p_row[4])
                    nome_prod = p_row[1] or f"{p_row[5] or ''} {p_row[6] or ''}".strip() or f"Produto #{prod_id}"
                    preco_formatado = brl(p_row[2]) if p_row[2] is not None else "R$ 0,00"

                    dados = {
                        "id": prod_id,
                        "id_banco": str(prod_id),
                        "nome": nome_prod,
                        "preco": preco_formatado,
                        "codigo": cod_final,
                        "codigo_barras": cod_final,
                        "sku": p_row[3] or cod_final,
                        "marca": p_row[5] or "",
                        "modelo": p_row[6] or "",
                        "tamanho": p_row[7] or "",
                        "dono": p_row[8] or "",
                    }

                    conn.execute("""
                        INSERT INTO fila_impressao (produto_id, texto_etiqueta, quantidade, status, criado) 
                        VALUES (%s, %s, %s, 'Pendente', CURRENT_TIMESTAMP)
                    """, (prod_id, json.dumps(dados), qtd_final))
                    conn.commit()

                from core.cache import cache
                cache.invalidate_prefix("fila")
                cache.invalidate_prefix("outlet")

                win.destroy()
                self.callback()
                self.app.toast.show(
                    f"Produto ID {prod_id} adicionado à fila ({qtd_final} etiqueta{'s' if qtd_final > 1 else ''})!",
                    "sucesso",
                )
            except Exception as e:
                self.app.toast.show(f"Erro ao adicionar: {str(e)}", "erro")

        tv_prod.bind("<Double-1>", lambda _: confirmar())
        e_busca.bind("<Return>", lambda _: confirmar())

        UIBuilder.button(
            bot_bar, "✔️ Adicionar à Fila", confirmar, color=SUCCESS, fg="#000", width=18
        ).pack(side="right", padx=(5, 0))

        UIBuilder.button(
            bot_bar, "❌ Cancelar", win.destroy, color=BG3, width=12
        ).pack(side="right")


PopupAddPorId = PopupAddProduto


class PopupConfigDimensoes:
    """Designer Visual com ajuste dinâmico do Gap e travamento rígido de bordas."""

    DPI_PRINTER = 203.0
    PX_PER_MM = DPI_PRINTER / 25.4

    def __init__(self, app, callback):
        self.app = app
        self.callback = callback
        self._photo_cache = {}

        self.layout_elementos = {
            "nome": {
                "tipo": "texto",
                "texto": "CAMISA POLO MASCULINA OUTLET",
                "x_mm": 1.0,
                "y_mm": 0.5,
                "font_size": 7,
                "max_w_mm": 32.0,
                "height_mm": 5.0,
            },
            "preco": {
                "tipo": "texto",
                "texto": "R$ 89,90",
                "x_mm": 1.0,
                "y_mm": 5.5,
                "font_size": 11,
                "max_w_mm": 32.0,
                "height_mm": 5.0,
            },
            "codigo": {
                "tipo": "barcode",
                "texto": "200000000001",
                "x_mm": 1.0,
                "y_mm": 11.0,
                "font_size": 7,
                "max_w_mm": 32.0,
                "height_mm": 9.0,
            },
        }

        self._drag_data: Dict[str, Any] = {
            "mode": None,
            "handle": None,
            "key": None,
            "start_x": 0,
            "start_y": 0,
            "initial_x_mm": 0,
            "initial_y_mm": 0,
            "initial_w_mm": 0,
            "initial_h_mm": 0,
            "initial_font": 7,
        }
        self.item_selecionado = "nome"
        self._build()

    def _build(self):
        self.win = tk.Toplevel(self.app)
        self.win.title("⚙️ Configuração & Designer Visual da Etiqueta")
        self.win.geometry("1020x780")
        self.win.configure(bg=BG)
        self.win.grab_set()

        cfgs = carregar_config_local()

        self.v_w = tk.StringVar(value=cfgs.get("etiq_largura_mm", "108.0"))
        self.v_h = tk.StringVar(value=cfgs.get("etiq_altura_mm", "25.0"))
        self.v_c = tk.StringVar(value=cfgs.get("etiq_por_linha", "3"))
        self.v_iw = tk.StringVar(value=cfgs.get("etiq_indiv_largura_mm", "36.0"))
        self.v_ih = tk.StringVar(value=cfgs.get("etiq_indiv_altura_mm", "22.0"))
        self.v_gap = tk.StringVar(value=cfgs.get("etiq_espaco_colunas_mm", "0.0"))
        self.v_me = tk.StringVar(value=cfgs.get("etiq_margem_esq", "0.0"))
        self.v_md = tk.StringVar(value=cfgs.get("etiq_margem_dir", "0.0"))
        self.v_mt = tk.StringVar(value=cfgs.get("etiq_margem_top", "0.5"))
        self.v_mb = tk.StringVar(value=cfgs.get("etiq_margem_baix", "0.5"))

        if "layout" in cfgs and isinstance(cfgs["layout"], dict):
            for k, val in cfgs["layout"].items():
                if k in self.layout_elementos:
                    self.layout_elementos[k].update(val)

        main_fm = UIBuilder.frame(self.win, bg=BG, padx=15, pady=10)
        main_fm.pack(fill="both", expand=True)

        col_esq = UIBuilder.frame(main_fm, bg=BG, width=300)
        col_esq.pack(side="left", fill="y", padx=(0, 10))

        # CARD 1: Carreira / Folha
        c1 = UIBuilder.card(col_esq, bg=BG2, px=12, py=8)
        c1.pack(fill="x", pady=(0, 8))
        UIBuilder.label(c1, "1. Carreira / Folha (mm)", font=FONT_SMALL, bg=BG2, fg=GOLD).pack(anchor="w")
        f1 = UIBuilder.frame(c1, bg=BG2)
        f1.pack(fill="x")
        UIBuilder.label(f1, "Larg. Total:", bg=BG2, fg=TEXT).grid(row=0, column=0, sticky="w")
        e_w = UIBuilder.entry(f1, var=self.v_w, width=6)
        e_w.grid(row=0, column=1, padx=(2, 8))
        
        UIBuilder.label(f1, "Alt. Total:", bg=BG2, fg=TEXT).grid(row=0, column=2, sticky="w")
        e_h = UIBuilder.entry(f1, var=self.v_h, width=6)
        e_h.grid(row=0, column=3)

        # CARD 2: Etiqueta Individual
        c2 = UIBuilder.card(col_esq, bg=BG2, px=12, py=8)
        c2.pack(fill="x", pady=(0, 8))
        UIBuilder.label(c2, "2. Etiqueta Individual (mm)", font=FONT_SMALL, bg=BG2, fg=GOLD).pack(anchor="w")
        f2 = UIBuilder.frame(c2, bg=BG2)
        f2.pack(fill="x")
        
        UIBuilder.label(f2, "Cols:", bg=BG2, fg=TEXT).grid(row=0, column=0, sticky="w")
        e_c = UIBuilder.entry(f2, var=self.v_c, width=4)
        e_c.grid(row=0, column=1, padx=(2, 6))
        
        UIBuilder.label(f2, "Larg. Indiv:", bg=BG2, fg=TEXT).grid(row=0, column=2, sticky="w")
        e_iw = UIBuilder.entry(f2, var=self.v_iw, width=5)
        e_iw.grid(row=0, column=3, padx=(2, 6))
        
        UIBuilder.label(f2, "Alt. Indiv:", bg=BG2, fg=TEXT).grid(row=0, column=4, sticky="w")
        e_ih = UIBuilder.entry(f2, var=self.v_ih, width=5)
        e_ih.grid(row=0, column=5)

        # CARD 3: Margens e Espaçamentos
        c3 = UIBuilder.card(col_esq, bg=BG2, px=12, py=8)
        c3.pack(fill="x", pady=(0, 8))
        UIBuilder.label(c3, "3. Margens & Espaços (mm)", font=FONT_SMALL, bg=BG2, fg=GOLD).pack(anchor="w")
        f3 = UIBuilder.frame(c3, bg=BG2)
        f3.pack(fill="x")
        
        UIBuilder.label(f3, "Marg. Top:", bg=BG2, fg=TEXT).grid(row=0, column=0, sticky="w")
        e_mt = UIBuilder.entry(f3, var=self.v_mt, width=4)
        e_mt.grid(row=0, column=1, padx=(2, 6), pady=2)
        
        UIBuilder.label(f3, "Marg. Base:", bg=BG2, fg=TEXT).grid(row=0, column=2, sticky="w")
        e_mb = UIBuilder.entry(f3, var=self.v_mb, width=4)
        e_mb.grid(row=0, column=3, padx=(2, 6), pady=2)

        UIBuilder.label(f3, "Marg. Esq:", bg=BG2, fg=TEXT).grid(row=1, column=0, sticky="w")
        e_me = UIBuilder.entry(f3, var=self.v_me, width=4)
        e_me.grid(row=1, column=1, padx=(2, 6), pady=2)

        UIBuilder.label(f3, "Marg. Dir:", bg=BG2, fg=TEXT).grid(row=1, column=2, sticky="w")
        e_md = UIBuilder.entry(f3, var=self.v_md, width=4)
        e_md.grid(row=1, column=3, padx=(2, 6), pady=2)

        UIBuilder.label(f3, "Gap Cols:", bg=BG2, fg=TEXT).grid(row=2, column=0, sticky="w")
        e_gap = UIBuilder.entry(f3, var=self.v_gap, width=4)
        e_gap.grid(row=2, column=1, padx=(2, 6), pady=2)

        for entry_widget in (e_w, e_h, e_c, e_iw, e_ih, e_mt, e_mb, e_me, e_md, e_gap):
            entry_widget.bind("<KeyRelease>", lambda e: self._atualizar_dimensoes_canvas())

        col_dir = UIBuilder.card(main_fm, bg=BG2, px=15, py=10)
        col_dir.pack(side="left", fill="both", expand=True)

        UIBuilder.label(col_dir, "🎨 Designer Visual No-Code", font=FONT_H2, bg=BG2, fg=GOLD).pack(anchor="w", pady=(0, 2))
        UIBuilder.label(
            col_dir,
            "• O sistema auto-calcula o Gap ideal para eliminar desvio acumulativo nas colunas.\n"
            "• Dica: Verifique se a largura física das suas etiquetas é exatamente 34mm ou 33mm.",
            font=FONT_SMALL,
            bg=BG2,
            fg=TEXT_DIM,
        ).pack(anchor="w", pady=(0, 8))

        canvas_container = UIBuilder.frame(col_dir, bg=BG3, padx=10, pady=10)
        canvas_container.pack(fill="both", expand=True)

        w_mm = float(self.v_iw.get() or 34)
        h_mm = float(self.v_ih.get() or 22)
        canvas_w = int(w_mm * self.PX_PER_MM)
        canvas_h = int(h_mm * self.PX_PER_MM)

        self.canvas = tk.Canvas(
            canvas_container,
            width=canvas_w,
            height=canvas_h,
            bg="#FFFFFF",
            highlightthickness=2,
            highlightbackground=GOLD,
        )
        self.canvas.pack(anchor="center", pady=10)

        prop_fm = UIBuilder.frame(col_dir, bg=BG2)
        prop_fm.pack(fill="x", pady=(5, 0))

        r1 = UIBuilder.frame(prop_fm, bg=BG2)
        r1.pack(fill="x", pady=(0, 5))

        UIBuilder.label(r1, "Elemento:", bg=BG2, fg=TEXT).pack(side="left", padx=(0, 5))
        self.v_elem_sel = tk.StringVar(value="nome")
        cb_elem = ttk.Combobox(
            r1,
            textvariable=self.v_elem_sel,
            values=["nome", "preco", "codigo"],
            state="readonly",
            width=8,
        )
        cb_elem.pack(side="left", padx=(0, 10))
        cb_elem.bind("<<ComboboxSelected>>", lambda e: self._selecionar_elemento(self.v_elem_sel.get()))

        UIBuilder.label(r1, "Texto Teste:", bg=BG2, fg=TEXT).pack(side="left", padx=(0, 5))
        self.v_elem_texto = tk.StringVar(value=self.layout_elementos["nome"]["texto"])
        ent_texto = UIBuilder.entry(r1, var=self.v_elem_texto, width=28)
        ent_texto.pack(side="left", fill="x", expand=True)
        ent_texto.bind("<KeyRelease>", self._on_texto_changed)

        r2 = UIBuilder.frame(prop_fm, bg=BG2)
        r2.pack(fill="x")

        UIBuilder.label(r2, "Tam. Fonte (pt):", bg=BG2, fg=TEXT).pack(side="left", padx=(0, 5))
        self.v_font_size = tk.StringVar(value="7")
        sp_font = ttk.Spinbox(r2, from_=4, to=24, textvariable=self.v_font_size, width=4, command=self._alterar_tamanho_fonte)
        sp_font.pack(side="left", padx=(0, 10))
        sp_font.bind("<Return>", lambda e: self._alterar_tamanho_fonte())

        UIBuilder.label(r2, "Max W (mm):", bg=BG2, fg=TEXT).pack(side="left", padx=(0, 5))
        self.v_max_w = tk.StringVar(value="32")
        sp_w = ttk.Spinbox(r2, from_=5, to=34, textvariable=self.v_max_w, width=4, command=self._alterar_max_w)
        sp_w.pack(side="left")
        sp_w.bind("<Return>", lambda e: self._alterar_max_w())

        self.lbl_pos = UIBuilder.label(r2, "X: 1.0mm | Y: 0.5mm", bg=BG2, fg=GOLD)
        self.lbl_pos.pack(side="right")

        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)
        self.canvas.bind("<MouseWheel>", self._on_mouse_scroll)
        self.canvas.bind("<Button-4>", lambda e: self._alterar_fonte_delta(1))
        self.canvas.bind("<Button-5>", lambda e: self._alterar_fonte_delta(-1))

        self._renderizar_canvas()

        btn_bar = UIBuilder.frame(self.win, bg=BG, padx=20, pady=10)
        btn_bar.pack(fill="x")
        UIBuilder.button(btn_bar, "💾 Salvar Medidas e Layout", self._salvar_tudo, color=SUCCESS, width=26).pack(side="right")

    def _atualizar_dimensoes_canvas(self):
        try:
            w_mm = float(self.v_iw.get() or 34)
            h_mm = float(self.v_ih.get() or 22)

            # Auto-sincroniza o Gap ideal no campo UI caso a soma não bata
            w_tot = float(self.v_w.get() or 108)
            cols = int(self.v_c.get() or 3)
            m_esq = float(self.v_me.get() or 2)
            m_dir = float(self.v_md.get() or 2)

            if cols > 1:
                espaco_gap = w_tot - m_esq - m_dir - (cols * w_mm)
                if espaco_gap >= 0:
                    gap_calc = round(espaco_gap / float(cols - 1), 2)
                    self.v_gap.set(str(gap_calc))

            self.canvas.config(
                width=int(w_mm * self.PX_PER_MM),
                height=int(h_mm * self.PX_PER_MM),
            )
            self._renderizar_canvas()
        except ValueError:
            pass

    def _renderizar_canvas(self):
        self.canvas.delete("all")
        self._photo_cache.clear()

        try:
            w_indiv_mm = float(self.v_iw.get() or 34)
            h_indiv_mm = float(self.v_ih.get() or 22)
            
            c_w = int(w_indiv_mm * self.PX_PER_MM)
            c_h = int(h_indiv_mm * self.PX_PER_MM)
            self.canvas.config(width=c_w, height=c_h)

            mt_px = int(float(self.v_mt.get() or 0.5) * self.PX_PER_MM)
            mb_px = c_h - int(float(self.v_mb.get() or 0.5) * self.PX_PER_MM)
            
            self.canvas.create_line(0, mt_px, c_w, mt_px, fill="#E11D48", dash=(2, 2))
            self.canvas.create_line(0, mb_px, c_w, mb_px, fill="#E11D48", dash=(2, 2))
        except ValueError:
            w_indiv_mm = 34.0

        for key, data in self.layout_elementos.items():
            x_mm = data["x_mm"]
            y_mm = data["y_mm"]
            max_w_mm = data.get("max_w_mm", 32.0)

            max_w_disponivel = max(1.0, w_indiv_mm - x_mm)
            max_w_efetivo_mm = min(max_w_mm, max_w_disponivel)

            x_px = int(x_mm * self.PX_PER_MM)
            y_px = int(y_mm * self.PX_PER_MM)
            max_w_px = max(20, int(max_w_efetivo_mm * self.PX_PER_MM))

            is_selected = key == self.item_selecionado
            cor_texto = "#000000" if not is_selected else "#D97706"

            if key == "codigo" or data.get("tipo") == "barcode":
                h_mm = float(data.get("height_mm", 9.0))
                h_px = max(15, int(h_mm * self.PX_PER_MM))

                bar_pil = gerar_imagem_ean13(str(data["texto"]), max_w_px, h_px)
                bar_photo = ImageTk.PhotoImage(bar_pil)
                self._photo_cache[key] = bar_photo

                item_id = self.canvas.create_image(
                    x_px, y_px, image=bar_photo, anchor="nw", tags=("drag_item", key)
                )
            else:
                f_pt = data["font_size"]
                px_font = int(f_pt * (self.DPI_PRINTER / 72.0))
                is_bold = "bold" if key in ["nome", "preco"] else "normal"

                item_id = self.canvas.create_text(
                    x_px,
                    y_px,
                    text=data["texto"],
                    anchor="nw",
                    width=max_w_px,
                    font=("Arial", -px_font, is_bold),
                    fill=cor_texto,
                    tags=("drag_item", key),
                )

            if is_selected:
                bbox = self.canvas.bbox(item_id)
                if bbox:
                    x1, y1, x2, y2 = bbox
                    self.canvas.create_rectangle(
                        x1 - 2, y1 - 2, x2 + 2, y2 + 2,
                        outline=GOLD, dash=(2, 2), tags="selection_box"
                    )

                    hs = 4
                    handles = {
                        "nw": (x1 - hs, y1 - hs, x1 + hs, y1 + hs),
                        "ne": (x2 - hs, y1 - hs, x2 + hs, y1 + hs),
                        "sw": (x1 - hs, y2 - hs, x1 + hs, y2 + hs),
                        "se": (x2 - hs, y2 - hs, x2 + hs, y2 + hs),
                    }

                    for h_name, (hx1, hy1, hx2, hy2) in handles.items():
                        self.canvas.create_rectangle(
                            hx1, hy1, hx2, hy2,
                            fill=GOLD, outline="#000000",
                            tags=("resize_handle", h_name, key)
                        )

    def _selecionar_elemento(self, key):
        self.item_selecionado = key
        self.v_elem_sel.set(key)
        data = self.layout_elementos[key]
        self.v_elem_texto.set(data["texto"])
        self.v_font_size.set(str(data["font_size"]))
        self.v_max_w.set(str(data.get("max_w_mm", 32.0)))

        self.lbl_pos.config(text=f"X: {data['x_mm']:.1f}mm | Y: {data['y_mm']:.1f}mm")
        self._renderizar_canvas()

    def _on_texto_changed(self, event=None):
        if self.item_selecionado:
            self.layout_elementos[self.item_selecionado]["texto"] = self.v_elem_texto.get()
            self._renderizar_canvas()

    def _alterar_tamanho_fonte(self):
        try:
            sz = int(self.v_font_size.get())
            if sz > 0 and self.item_selecionado:
                self.layout_elementos[self.item_selecionado]["font_size"] = sz
                self._renderizar_canvas()
        except ValueError:
            pass

    def _alterar_max_w(self):
        try:
            w = float(self.v_max_w.get())
            if w > 0 and self.item_selecionado:
                self.layout_elementos[self.item_selecionado]["max_w_mm"] = w
                self._renderizar_canvas()
        except ValueError:
            pass

    def _alterar_fonte_delta(self, delta):
        if self.item_selecionado:
            data = self.layout_elementos[self.item_selecionado]
            if self.item_selecionado == "codigo":
                curr_h = data.get("height_mm", 9.0)
                data["height_mm"] = max(3.0, min(20.0, round(curr_h + (delta * 0.5), 1)))
            else:
                curr_sz = data["font_size"]
                data["font_size"] = max(4, min(24, curr_sz + delta))
                self.v_font_size.set(str(data["font_size"]))

            self._renderizar_canvas()

    def _on_mouse_scroll(self, event):
        delta = 1 if event.delta > 0 else -1
        self._alterar_fonte_delta(delta)

    def _on_canvas_click(self, event):
        items = self.canvas.find_withtag("current")
        if not items:
            return

        tags = self.canvas.gettags(items[0])

        if "resize_handle" in tags:
            h_name = tags[1]
            key = tags[2]
            self._selecionar_elemento(key)
            data = self.layout_elementos[key]
            self._drag_data = {
                "mode": "resize",
                "handle": h_name,
                "key": key,
                "start_x": event.x,
                "start_y": event.y,
                "initial_x_mm": data["x_mm"],
                "initial_y_mm": data["y_mm"],
                "initial_w_mm": data.get("max_w_mm", 32.0),
                "initial_h_mm": data.get("height_mm", 9.0),
                "initial_font": data["font_size"],
            }
            return

        if "drag_item" in tags:
            for t in tags:
                if t in self.layout_elementos:
                    self._selecionar_elemento(t)
                    data = self.layout_elementos[t]
                    self._drag_data = {
                        "mode": "move",
                        "key": t,
                        "start_x": event.x,
                        "start_y": event.y,
                        "initial_x_mm": data["x_mm"],
                        "initial_y_mm": data["y_mm"],
                    }
                    break

    def _on_canvas_drag(self, event):
        mode = self._drag_data.get("mode")
        key = self._drag_data.get("key")
        if not mode or not key:
            return

        w_indiv_mm = float(self.v_iw.get() or 34)

        dx_mm = (event.x - self._drag_data["start_x"]) / self.PX_PER_MM
        dy_mm = (event.y - self._drag_data["start_y"]) / self.PX_PER_MM

        if mode == "move":
            new_x = max(0.0, min(w_indiv_mm - 2.0, round(self._drag_data["initial_x_mm"] + dx_mm, 1)))
            new_y = max(-2.0, round(self._drag_data["initial_y_mm"] + dy_mm, 1))

            self.layout_elementos[key]["x_mm"] = new_x
            self.layout_elementos[key]["y_mm"] = new_y
            self.lbl_pos.config(text=f"X: {new_x:.1f}mm | Y: {new_y:.1f}mm")
            self._renderizar_canvas()

        elif mode == "resize":
            handle = self._drag_data["handle"]
            data = self.layout_elementos[key]

            init_x = self._drag_data["initial_x_mm"]
            init_y = self._drag_data["initial_y_mm"]
            init_w = self._drag_data["initial_w_mm"]
            init_font = self._drag_data["initial_font"]
            init_h = self._drag_data["initial_h_mm"]

            new_w = init_w
            new_x = init_x
            new_y = init_y
            delta_height = 0

            if "e" in handle:
                new_w = max(5.0, round(init_w + dx_mm, 1))
            elif "w" in handle:
                possible_w = init_w - dx_mm
                if possible_w >= 5.0:
                    new_w = round(possible_w, 1)
                    new_x = round(init_x + dx_mm, 1)

            if "s" in handle:
                delta_height = dy_mm
            elif "n" in handle:
                delta_height = -dy_mm
                new_y = round(init_y + dy_mm, 1)

            data["max_w_mm"] = new_w
            data["x_mm"] = new_x
            data["y_mm"] = new_y

            if key == "codigo":
                data["height_mm"] = max(3.0, round(init_h + delta_height, 1))
            else:
                new_font = max(4, min(24, int(init_font + (delta_height * 1.2))))
                data["font_size"] = new_font
                self.v_font_size.set(str(new_font))

            self.v_max_w.set(str(new_w))
            self.lbl_pos.config(text=f"X: {new_x:.1f}mm | Y: {new_y:.1f}mm")
            self._renderizar_canvas()

    def _on_canvas_release(self, event):
        self._drag_data = {"mode": None, "handle": None, "key": None}

    def _salvar_tudo(self):
        novas_cfgs = {
            "etiq_largura_mm": self.v_w.get().strip(),
            "etiq_altura_mm": self.v_h.get().strip(),
            "etiq_por_linha": self.v_c.get().strip(),
            "etiq_indiv_largura_mm": self.v_iw.get().strip(),
            "etiq_indiv_altura_mm": self.v_ih.get().strip(),
            "etiq_espaco_colunas_mm": self.v_gap.get().strip(),
            "etiq_margem_esq": self.v_me.get().strip(),
            "etiq_margem_dir": self.v_md.get().strip(),
            "etiq_margem_top": self.v_mt.get().strip(),
            "etiq_margem_baix": self.v_mb.get().strip(),
            "layout": self.layout_elementos,
        }

        sucesso = salvar_config_local(novas_cfgs)
        if sucesso:
            self.win.destroy()
            if self.callback:
                self.callback()
            self.app.toast.show("Medidas e Layout salvos com sucesso!", "sucesso")
        else:
            messagebox.showerror("Erro", "Não foi possível salvar o arquivo.")


class PopupEditarEtiqueta:
    """Popup para editar dados da etiqueta individualmente."""

    def __init__(self, app, fid, callback):
        self.app = app
        self.fid = fid
        self.callback = callback
        self._build()

    def _build(self):
        with get_conn() as conn:
            row = conn.execute(
                "SELECT texto_etiqueta, quantidade FROM fila_impressao WHERE id=%s",
                (self.fid,),
            ).fetchone()

        if not row:
            self.app.toast.show("Item não encontrado.", "erro")
            return

        try:
            dados = json.loads(row[0]) if isinstance(row[0], str) else row[0]
        except Exception:
            self.app.toast.show("Erro ao carregar JSON.", "erro")
            return

        win = tk.Toplevel(self.app)
        win.title("Editar Etiqueta")
        win.geometry("450x520")
        win.configure(bg=BG)
        win.grab_set()

        fm = UIBuilder.frame(win, bg=BG, padx=25, pady=15)
        fm.pack(fill="both", expand=True)

        vs = {k: tk.StringVar(value=dados.get(k, "")) for k in ["nome", "marca", "tamanho", "preco", "codigo"]}
        v_qtd = tk.StringVar(value=str(row[1]))

        UIBuilder.field(fm, "Nome", vs["nome"], bg=BG)
        UIBuilder.field(fm, "Código EAN", vs["codigo"], bg=BG)

        r_m = UIBuilder.frame(fm, bg=BG)
        r_m.pack(fill="x")
        f_l = UIBuilder.frame(r_m, bg=BG)
        f_l.pack(side="left", fill="x", expand=True)
        f_r = UIBuilder.frame(r_m, bg=BG)
        f_r.pack(side="left", fill="x", expand=True)
        UIBuilder.field(f_l, "Preço", vs["preco"], bg=BG)
        UIBuilder.field(f_r, "Tam", vs["tamanho"], bg=BG)
        # Stepper para quantidade
        f_qtd = UIBuilder.frame(fm, bg=BG, pady=5)
        f_qtd.pack(fill="x")
        UIBuilder.label(f_qtd, "Qtd (Impressões):", font=FONT_SMALL, bg=BG, fg=TEXT_DIM).pack(anchor="w", pady=(0, 2))

        f_sp = UIBuilder.frame(f_qtd, bg=BG)
        f_sp.pack(anchor="w")

        def dec_qtd():
            try:
                val = int(v_qtd.get())
                if val > 1:
                    v_qtd.set(str(val - 1))
            except ValueError:
                v_qtd.set("1")

        def inc_qtd():
            try:
                val = int(v_qtd.get())
                v_qtd.set(str(max(1, val + 1)))
            except ValueError:
                v_qtd.set("1")

        tk.Button(
            f_sp,
            text="➖",
            command=dec_qtd,
            bg=BG3,
            fg=TEXT,
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=6,
            pady=2,
            cursor="hand2",
        ).pack(side="left", padx=(0, 2))

        sp_edit = ttk.Spinbox(
            f_sp,
            from_=1,
            to=9999,
            textvariable=v_qtd,
            width=6,
            justify="center",
            font=("Segoe UI", 10, "bold"),
        )
        sp_edit.pack(side="left", padx=2)

        tk.Button(
            f_sp,
            text="➕",
            command=inc_qtd,
            bg=BG3,
            fg=TEXT,
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=6,
            pady=2,
            cursor="hand2",
        ).pack(side="left", padx=(2, 0))

        def salvar():
            d = {k: v.get().strip() for k, v in vs.items()}
            d["dono"] = dados.get("dono", "")
            d["id"] = dados.get("id")
            d["sku"] = dados.get("sku")
            d["codigo_barras"] = d.get("codigo")
            try:
                qtd_salvar = max(1, int(v_qtd.get().strip()))
            except ValueError:
                qtd_salvar = 1

            prod_id = dados.get("id") or dados.get("produto_id")

            with get_conn() as conn:
                conn.execute(
                    "UPDATE fila_impressao SET texto_etiqueta=%s, quantidade=%s WHERE id=%s",
                    (json.dumps(d), qtd_salvar, self.fid),
                )
                if prod_id and d.get("codigo"):
                    try:
                        conn.execute(
                            "UPDATE produtos_outlet SET codigo_barras=%s WHERE id=%s",
                            (d["codigo"], int(prod_id))
                        )
                    except Exception:
                        pass
                conn.commit()
            from core.cache import cache
            cache.invalidate_prefix("fila")
            cache.invalidate_prefix("outlet")
            win.destroy()
            self.callback()
            self.app.toast.show("Etiqueta atualizada com sucesso!", "sucesso")

        UIBuilder.button(fm, "💾 Atualizar", salvar, color=SUCCESS, width=20).pack(pady=10)