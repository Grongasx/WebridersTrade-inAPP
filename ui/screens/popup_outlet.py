"""
Popup de entrada de produto outlet com suporte a SKU dinâmico, categorias e numeração por tipo.
"""

import tkinter as tk
from tkinter import ttk
import time
from config import (
    BG,
    BG2,
    BG3,
    ACCENT,
    GOLD,
    TEXT,
    TEXT_DIM,
    SUCCESS,
    DANGER,
    FONT_H2,
    FONT_BODY,
    FONT_SMALL,
    FONT_CODE,
)
from ui.components.base import UIBuilder
from core.cache import cache
from core.database import (
    get_conn,
    obter_tipos,
    obter_marcas_por_tipo,
    obter_modelos_por_marca,
    salvar_hierarquia,
)
from utils.helpers import (
    agora,
    txt_para_float,
    brl,
    calcular_sku,
    gerar_e_persistir_ean13,
    NUMERACAO_POR_TIPO,
    TIPO_PREFIXOS,
    formatar_data,
)
from utils.formatters import CurrencyFormatter


class PopupProdutoEntrada:
    """Popup para dar entrada de produto no outlet com seleção em cascata Tipo -> Marca -> Modelo."""
    
    def __init__(self, app, callback):
        self.app = app
        self.callback = callback
        self._build()
    
    def _build(self):
        win = tk.Toplevel(self.app)
        win.title("Entrada de Produto Outlet — SKU & Atributos")
        UIBuilder.centralizar_janela(win, 1040, 700, parent=self.app)
        win.configure(bg=BG)
        win.grab_set()

        main_fm = UIBuilder.card(win, bg=BG2, px=24, py=20)
        main_fm.pack(fill="both", expand=True, padx=15, pady=15)

        split = UIBuilder.frame(main_fm, bg=BG2)
        split.pack(fill="both", expand=True)
        
        # ═══════════════════════════════════════════
        # Coluna Esquerda - Proprietário (Cliente)
        # ═══════════════════════════════════════════
        col_e = UIBuilder.frame(split, bg=BG2, width=380)
        col_e.pack(side="left", fill="both", expand=True, padx=(0, 15))
        col_e.pack_propagate(False)

        UIBuilder.label(col_e, "1. Proprietário (Cliente) *", font=FONT_H2, bg=BG2, fg=GOLD).pack(anchor="w", pady=(0, 5))
        
        f_b = UIBuilder.frame(col_e, bg=BG2)
        f_b.pack(fill="x", pady=5)
        v_b = tk.StringVar()
        UIBuilder.label(f_b, "🔍", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(side="left", padx=(0, 4))
        UIBuilder.entry(f_b, var=v_b, width=28).pack(side="left", fill="x", expand=True, ipady=3)
        
        tf_cli = UIBuilder.frame(col_e, bg=BG2)
        tf_cli.pack(fill="both", expand=True, pady=5)
        tv_cli = UIBuilder.make_tree(tf_cli, ("ID", "Nome", "CPF"), [45, 200, 110], ["center", "w", "center"])
        
        # Carrega clientes uma única vez na inicialização em memória
        try:
            with get_conn() as conn:
                self._todos_clientes = conn.execute("SELECT id, nome, cpf FROM clientes ORDER BY nome").fetchall()
        except Exception:
            self._todos_clientes = []

        def filtrar(*_):
            t = v_b.get().strip().lower()
            for r in tv_cli.get_children(): 
                tv_cli.delete(r)
            for r in self._todos_clientes:
                if t and (t not in r[1].lower() and (not r[2] or t not in r[2].lower())):
                    continue
                tv_cli.insert("", "end", iid=str(r[0]), values=(r[0], r[1], r[2] or "—"))
        v_b.trace_add("write", filtrar)
        filtrar()

        # ═══════════════════════════════════════════
        # Coluna Direita - Dados do Produto & SKU
        # ═══════════════════════════════════════════
        col_d = UIBuilder.frame(split, bg=BG2, width=540)
        col_d.pack(side="right", fill="both", expand=True, padx=(15, 0))
        col_d.pack_propagate(False)

        UIBuilder.label(col_d, "2. Detalhes do Produto & SKU", font=FONT_H2, bg=BG2, fg=GOLD).pack(anchor="w", pady=(0, 8))

        # Variáveis dos atributos - todas iniciam vazias
        vs = {
            "tipo": tk.StringVar(value=""),
            "marca": tk.StringVar(value=""),
            "modelo": tk.StringVar(value=""),
            "grafico": tk.StringVar(value=""),
            "cor": tk.StringVar(value=""),
            "numeracao": tk.StringVar(value=""),
            "qtd": tk.StringVar(value="1"),
            "sku": tk.StringVar(value=""),
        }

        # Sub-container com scroll para os campos
        scroll_fm = UIBuilder.frame(col_d, bg=BG2)
        scroll_fm.pack(fill="both", expand=True)
        canvas, inner_d = UIBuilder.scrolled_canvas(scroll_fm)

        # Carrega catálogo completo em memória para filtros instantâneos sem tráfego de rede
        try:
            with get_conn() as conn:
                rows = conn.execute("SELECT tipo, COALESCE(marca, ''), COALESCE(modelo, '') FROM catalogo_produtos UNION SELECT tipo, COALESCE(marca, ''), COALESCE(modelo, '') FROM produtos_outlet").fetchall()
                self._catalogo_local = [(r[0] or "", r[1] or "", r[2] or "") for r in rows]
        except Exception:
            self._catalogo_local = []

        # 1. Categoria / Tipo e Marca (Cascata nível 1 -> 2)
        r1 = UIBuilder.frame(inner_d, bg=BG2, pady=4)
        r1.pack(fill="x")
        
        f_tipo = UIBuilder.frame(r1, bg=BG2)
        f_tipo.pack(side="left", fill="x", expand=True, padx=(0, 8))
        UIBuilder.label(f_tipo, "Categoria / Tipo *", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w")
        tipos_salvos = sorted(list({r[0] for r in self._catalogo_local if r[0]}))
        cb_tipo = ttk.Combobox(f_tipo, textvariable=vs["tipo"], values=tipos_salvos, font=FONT_BODY)
        cb_tipo.pack(fill="x", ipady=3, pady=(2, 0))

        f_marca = UIBuilder.frame(r1, bg=BG2)
        f_marca.pack(side="left", fill="x", expand=True, padx=(8, 0))
        UIBuilder.label(f_marca, "Marca *", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w")
        marcas_iniciais = sorted(list({r[1] for r in self._catalogo_local if r[1]}))
        cb_marca = ttk.Combobox(f_marca, textvariable=vs["marca"], values=marcas_iniciais, font=FONT_BODY)
        cb_marca.pack(fill="x", ipady=3, pady=(2, 0))

        # 2. Modelo (Cascata nível 3) e Gráfico (Estampa)
        r2 = UIBuilder.frame(inner_d, bg=BG2, pady=4)
        r2.pack(fill="x")

        f_mod = UIBuilder.frame(r2, bg=BG2)
        f_mod.pack(side="left", fill="x", expand=True, padx=(0, 8))
        UIBuilder.label(f_mod, "Modelo / Edição *", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w")
        modelos_iniciais = sorted(list({r[2] for r in self._catalogo_local if r[2]}))
        cb_mod = ttk.Combobox(f_mod, textvariable=vs["modelo"], values=modelos_iniciais, font=FONT_BODY)
        cb_mod.pack(fill="x", ipady=3, pady=(2, 0))

        f_graf = UIBuilder.frame(r2, bg=BG2)
        f_graf.pack(side="left", fill="x", expand=True, padx=(8, 0))
        UIBuilder.label(f_graf, "Gráfico / Estampa (Opcional)", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w")
        UIBuilder.entry(f_graf, var=vs["grafico"], width=22).pack(fill="x", ipady=3, pady=(2, 0))

        # 3. Cor e Numeração
        r3 = UIBuilder.frame(inner_d, bg=BG2, pady=4)
        r3.pack(fill="x")

        f_cor = UIBuilder.frame(r3, bg=BG2)
        f_cor.pack(side="left", fill="x", expand=True, padx=(0, 8))
        UIBuilder.label(f_cor, "Cor Dominante", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w")
        cores_lista = ["Preto", "Branco", "Vermelho", "Azul", "Verde", "Amarelo", "Cinza", "Roxo", "Natural / Madeira", "Multicolor"]
        cb_cor = ttk.Combobox(f_cor, textvariable=vs["cor"], values=cores_lista, font=FONT_BODY)
        cb_cor.pack(fill="x", ipady=3, pady=(2, 0))

        f_num = UIBuilder.frame(r3, bg=BG2)
        f_num.pack(side="left", fill="x", expand=True, padx=(8, 0))
        UIBuilder.label(f_num, "Numeração / Tamanho", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w")
        cb_num = ttk.Combobox(f_num, textvariable=vs["numeracao"], font=FONT_BODY)
        cb_num.pack(fill="x", ipady=3, pady=(2, 0))

        # ═══════════════════════════════════════════
        # Atualizações Reativas em Cascata (100% em Memória Local)
        # ═══════════════════════════════════════════
        def atualizar_cascata_tipo(*_):
            tipo_sel = vs["tipo"].get().strip().lower()
            if tipo_sel:
                marcas_filtradas = sorted(list({r[1] for r in self._catalogo_local if r[1] and r[0].lower() == tipo_sel}))
                modelos_filtrados = sorted(list({r[2] for r in self._catalogo_local if r[2] and r[0].lower() == tipo_sel}))
            else:
                marcas_filtradas = sorted(list({r[1] for r in self._catalogo_local if r[1]}))
                modelos_filtrados = sorted(list({r[2] for r in self._catalogo_local if r[2]}))

            cb_marca.config(values=marcas_filtradas)
            cb_mod.config(values=modelos_filtrados)

            # Sugestões de numeração caso pertença a tipo com medidas conhecidas
            orig_tipo = vs["tipo"].get().strip()
            if orig_tipo in NUMERACAO_POR_TIPO:
                cb_num.config(values=NUMERACAO_POR_TIPO[orig_tipo])

        def atualizar_cascata_marca(*_):
            tipo_sel = vs["tipo"].get().strip().lower()
            marca_sel = vs["marca"].get().strip().lower()
            if tipo_sel and marca_sel:
                modelos_filtrados = sorted(list({r[2] for r in self._catalogo_local if r[2] and r[0].lower() == tipo_sel and r[1].lower() == marca_sel}))
            elif marca_sel:
                modelos_filtrados = sorted(list({r[2] for r in self._catalogo_local if r[2] and r[1].lower() == marca_sel}))
            elif tipo_sel:
                modelos_filtrados = sorted(list({r[2] for r in self._catalogo_local if r[2] and r[0].lower() == tipo_sel}))
            else:
                modelos_filtrados = sorted(list({r[2] for r in self._catalogo_local if r[2]}))

            cb_mod.config(values=modelos_filtrados)

        cb_tipo.bind("<<ComboboxSelected>>", lambda *_: (atualizar_cascata_tipo(), recalcular_sku_auto()))
        cb_marca.bind("<<ComboboxSelected>>", lambda *_: (atualizar_cascata_marca(), recalcular_sku_auto()))

        # 4. Quantidade e Valores
        r4 = UIBuilder.frame(inner_d, bg=BG2, pady=4)
        r4.pack(fill="x")

        f_qtd = UIBuilder.frame(r4, bg=BG2)
        f_qtd.pack(side="left", fill="x", expand=True, padx=(0, 8))
        UIBuilder.label(f_qtd, "Quantidade *", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w")
        UIBuilder.entry(f_qtd, var=vs["qtd"], width=10).pack(fill="x", ipady=3, pady=(2, 0))

        f_porig = UIBuilder.frame(r4, bg=BG2)
        f_porig.pack(side="left", fill="x", expand=True, padx=(4, 4))
        UIBuilder.label(f_porig, "Preço Original (R$)", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w")
        e_orig = UIBuilder.entry(f_porig, width=14)
        e_orig.pack(fill="x", ipady=3, pady=(2, 0))
        e_orig.bind("<KeyRelease>", lambda _: CurrencyFormatter.formatar_moeda_local(e_orig))

        f_pout = UIBuilder.frame(r4, bg=BG2)
        f_pout.pack(side="left", fill="x", expand=True, padx=(8, 0))
        UIBuilder.label(f_pout, "Valor Sugerido Outlet *", font=FONT_SMALL, bg=BG2, fg=GOLD).pack(anchor="w")
        e_out = UIBuilder.entry(f_pout, width=14)
        e_out.pack(fill="x", ipady=3, pady=(2, 0))
        e_out.bind("<KeyRelease>", lambda _: CurrencyFormatter.formatar_moeda_local(e_out))

        # 5. SKU Calculado em Tempo Real
        r_sku = UIBuilder.card(inner_d, bg=BG3, px=14, py=10)
        r_sku.pack(fill="x", pady=10)

        top_sku = UIBuilder.frame(r_sku, bg=BG3)
        top_sku.pack(fill="x")
        UIBuilder.label(top_sku, "🏷️ SKU (Código de Controle Interno Calculado)", font=FONT_SMALL, bg=BG3, fg=GOLD).pack(side="left")
        
        e_sku = UIBuilder.entry(r_sku, var=vs["sku"], width=30)
        e_sku.pack(fill="x", ipady=4, pady=(4, 0))

        def recalcular_sku_auto(*_):
            tipo = vs["tipo"].get().strip()
            marca = vs["marca"].get().strip()
            modelo = vs["modelo"].get().strip()
            grafico = vs["grafico"].get().strip()
            cor = vs["cor"].get().strip()
            numeracao = vs["numeracao"].get().strip()

            if not (tipo or marca or modelo):
                vs["sku"].set("")
                return

            sku_calc = calcular_sku(
                tipo=tipo,
                marca=marca,
                modelo=modelo,
                grafico=grafico,
                cor=cor,
                numeracao=numeracao
            )
            if vs["sku"].get() != sku_calc:
                vs["sku"].set(sku_calc)

        # Triggers de cálculo automático do SKU e cascata dinâmica (100% síncronos e instantâneos)
        vs["tipo"].trace_add("write", lambda *_: (atualizar_cascata_tipo(), recalcular_sku_auto()))
        vs["marca"].trace_add("write", lambda *_: (atualizar_cascata_marca(), recalcular_sku_auto()))
        for k in ["modelo", "grafico", "cor", "numeracao"]:
            vs[k].trace_add("write", lambda *_: recalcular_sku_auto())

        recalcular_sku_auto()

        # ═══════════════════════════════════════════
        # Ação Salvar
        # ═══════════════════════════════════════════
        def salvar():
            sel = tv_cli.selection()
            if not sel: 
                self.app.toast.show("Selecione o proprietário do produto (Cliente)", "erro")
                return
            
            tipo = vs["tipo"].get().strip()
            marca = vs["marca"].get().strip()
            modelo = vs["modelo"].get().strip()
            grafico = vs["grafico"].get().strip() or None
            cor = vs["cor"].get().strip() or None
            numeracao = vs["numeracao"].get().strip() or None
            sku = vs["sku"].get().strip()

            if not tipo:
                self.app.toast.show("Informe a Categoria / Tipo do produto.", "erro")
                return
            if not marca:
                self.app.toast.show("Informe a Marca do produto.", "erro")
                return
            if not modelo:
                self.app.toast.show("Informe o Modelo do produto.", "erro")
                return

            preco_orig = txt_para_float(e_orig.get())
            preco_outlet = txt_para_float(e_out.get())
            if preco_outlet <= 0:
                self.app.toast.show("Informe um Valor Sugerido de Venda válido.", "erro")
                return

            try:
                qtd = int(vs["qtd"].get().strip() or 1)
            except ValueError:
                qtd = 1

            # Armazena a cascata Tipo -> Marca -> Modelo no catálogo
            salvar_hierarquia(tipo, marca, modelo)

            # Nome composto para exibição
            nome_composto = f"{marca} {modelo}" + (f" ({grafico})" if grafico else "")

            with get_conn() as conn:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO produtos_outlet (
                        cliente_id, sku, codigo_barras, tipo, marca, modelo, grafico, cor, 
                        numeracao, tamanho, preco_original, preco_outlet, valor_sugerido, 
                        estoque, quantidade, status, criado, nome
                    ) 
                    VALUES (%s, %s, NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Disponível', %s, %s)
                    RETURNING id
                """, (
                    int(sel[0]), sku, tipo, marca, modelo, grafico, cor, 
                    numeracao, numeracao, preco_orig, preco_outlet, preco_outlet, 
                    qtd, qtd, agora(), nome_composto
                ))
                
                pid = cur.fetchone()[0]
                ean_final = gerar_e_persistir_ean13(conn, pid)
                conn.commit()

            from core.cache import cache
            cache.invalidate_prefix("outlet")
            cache.invalidate_prefix("dashboard")
            cache.invalidate_prefix("fila")
            
            if hasattr(self.app, "_adicionar_fila_impressao"):
                self.app._adicionar_fila_impressao(pid)
                
            win.destroy()
            self.callback()
            self.app.toast.show(f"Produto salvo! EAN-13 '{ean_final}' gerado e enviado para impressão.", "sucesso")
        
        UIBuilder.button(main_fm, "✨ Salvar Produto & Enviar p/ Fila de Impressão", salvar, color=GOLD, fg="#000", width=40).pack(pady=14, ipady=6)


class PopupProdutoEditar:
    """Popup para editar atributos, proprietário, preços e status de um produto outlet."""

    def __init__(self, app, pid, callback):
        self.app = app
        self.pid = pid
        self.callback = callback
        self._build()

    def _build(self):
        with get_conn() as conn:
            row = conn.execute("""
                SELECT p.id, p.cliente_id, COALESCE(p.sku, ''), COALESCE(p.codigo_barras, ''),
                       COALESCE(p.tipo, ''), COALESCE(p.marca, ''), COALESCE(p.modelo, ''),
                       COALESCE(p.grafico, ''), COALESCE(p.cor, ''), COALESCE(p.numeracao, p.tamanho, ''),
                       COALESCE(p.preco_original, 0), COALESCE(p.preco_outlet, p.valor_sugerido, 0),
                       COALESCE(p.quantidade, p.estoque, 1), COALESCE(p.status, 'Disponível'),
                       c.nome, c.cpf
                FROM produtos_outlet p
                LEFT JOIN clientes c ON p.cliente_id = c.id
                WHERE p.id = %s
            """, (self.pid,)).fetchone()

        if not row:
            self.app.toast.show("Produto não encontrado.", "erro")
            return

        (
            pid, cliente_id, sku_atual, ean_atual,
            tipo_atual, marca_atual, modelo_atual,
            grafico_atual, cor_atual, num_atual,
            preco_orig_atual, preco_out_atual,
            qtd_atual, status_atual,
            cli_nome, cli_cpf
        ) = row

        win = tk.Toplevel(self.app)
        win.title(f"Editar Produto Outlet — ID #{pid}")
        UIBuilder.centralizar_janela(win, 1040, 700, parent=self.app)
        win.configure(bg=BG)
        win.grab_set()

        main_fm = UIBuilder.card(win, bg=BG2, px=24, py=20)
        main_fm.pack(fill="both", expand=True, padx=15, pady=15)

        split = UIBuilder.frame(main_fm, bg=BG2)
        split.pack(fill="both", expand=True)

        # ═══════════════════════════════════════════
        # Coluna Esquerda - Proprietário (Cliente)
        # ═══════════════════════════════════════════
        col_e = UIBuilder.frame(split, bg=BG2, width=380)
        col_e.pack(side="left", fill="both", expand=True, padx=(0, 15))
        col_e.pack_propagate(False)

        UIBuilder.label(col_e, "1. Proprietário (Cliente) *", font=FONT_H2, bg=BG2, fg=GOLD).pack(anchor="w", pady=(0, 5))

        f_b = UIBuilder.frame(col_e, bg=BG2)
        f_b.pack(fill="x", pady=5)
        v_b = tk.StringVar()
        UIBuilder.label(f_b, "🔍", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(side="left", padx=(0, 4))
        UIBuilder.entry(f_b, var=v_b, width=28).pack(side="left", fill="x", expand=True, ipady=3)

        tf_cli = UIBuilder.frame(col_e, bg=BG2)
        tf_cli.pack(fill="both", expand=True, pady=5)
        tv_cli = UIBuilder.make_tree(tf_cli, ("ID", "Nome", "CPF"), [45, 200, 110], ["center", "w", "center"])

        try:
            with get_conn() as conn:
                self._todos_clientes = conn.execute("SELECT id, nome, cpf FROM clientes ORDER BY nome").fetchall()
        except Exception:
            self._todos_clientes = []

        def filtrar(*_):
            t = v_b.get().strip().lower()
            for r in tv_cli.get_children():
                tv_cli.delete(r)
            for r in self._todos_clientes:
                if t and (t not in r[1].lower() and (not r[2] or t not in r[2].lower())):
                    continue
                tv_cli.insert("", "end", iid=str(r[0]), values=(r[0], r[1], r[2] or "—"))
            if cliente_id and str(cliente_id) in tv_cli.get_children():
                tv_cli.selection_set(str(cliente_id))
                tv_cli.see(str(cliente_id))

        v_b.trace_add("write", filtrar)
        filtrar()

        # ═══════════════════════════════════════════
        # Coluna Direita - Dados do Produto & SKU
        # ═══════════════════════════════════════════
        col_d = UIBuilder.frame(split, bg=BG2, width=540)
        col_d.pack(side="right", fill="both", expand=True, padx=(15, 0))
        col_d.pack_propagate(False)

        UIBuilder.label(col_d, f"2. Detalhes do Produto #{pid} & SKU", font=FONT_H2, bg=BG2, fg=GOLD).pack(anchor="w", pady=(0, 8))

        vs = {
            "tipo": tk.StringVar(value=tipo_atual),
            "marca": tk.StringVar(value=marca_atual),
            "modelo": tk.StringVar(value=modelo_atual),
            "grafico": tk.StringVar(value=grafico_atual),
            "cor": tk.StringVar(value=cor_atual),
            "numeracao": tk.StringVar(value=num_atual),
            "qtd": tk.StringVar(value=str(qtd_atual)),
            "sku": tk.StringVar(value=sku_atual),
            "status": tk.StringVar(value=status_atual),
        }

        scroll_fm = UIBuilder.frame(col_d, bg=BG2)
        scroll_fm.pack(fill="both", expand=True)
        canvas, inner_d = UIBuilder.scrolled_canvas(scroll_fm)

        try:
            with get_conn() as conn:
                rows = conn.execute("SELECT tipo, COALESCE(marca, ''), COALESCE(modelo, '') FROM catalogo_produtos UNION SELECT tipo, COALESCE(marca, ''), COALESCE(modelo, '') FROM produtos_outlet").fetchall()
                self._catalogo_local = [(r[0] or "", r[1] or "", r[2] or "") for r in rows]
        except Exception:
            self._catalogo_local = []

        # 1. Categoria / Tipo e Marca
        r1 = UIBuilder.frame(inner_d, bg=BG2, pady=4)
        r1.pack(fill="x")

        f_tipo = UIBuilder.frame(r1, bg=BG2)
        f_tipo.pack(side="left", fill="x", expand=True, padx=(0, 8))
        UIBuilder.label(f_tipo, "Categoria / Tipo *", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w")
        tipos_salvos = sorted(list({r[0] for r in self._catalogo_local if r[0]}))
        cb_tipo = ttk.Combobox(f_tipo, textvariable=vs["tipo"], values=tipos_salvos, font=FONT_BODY)
        cb_tipo.pack(fill="x", ipady=3, pady=(2, 0))

        f_marca = UIBuilder.frame(r1, bg=BG2)
        f_marca.pack(side="left", fill="x", expand=True, padx=(8, 0))
        UIBuilder.label(f_marca, "Marca *", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w")
        marcas_iniciais = sorted(list({r[1] for r in self._catalogo_local if r[1]}))
        cb_marca = ttk.Combobox(f_marca, textvariable=vs["marca"], values=marcas_iniciais, font=FONT_BODY)
        cb_marca.pack(fill="x", ipady=3, pady=(2, 0))

        # 2. Modelo e Gráfico
        r2 = UIBuilder.frame(inner_d, bg=BG2, pady=4)
        r2.pack(fill="x")

        f_mod = UIBuilder.frame(r2, bg=BG2)
        f_mod.pack(side="left", fill="x", expand=True, padx=(0, 8))
        UIBuilder.label(f_mod, "Modelo / Edição *", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w")
        modelos_iniciais = sorted(list({r[2] for r in self._catalogo_local if r[2]}))
        cb_mod = ttk.Combobox(f_mod, textvariable=vs["modelo"], values=modelos_iniciais, font=FONT_BODY)
        cb_mod.pack(fill="x", ipady=3, pady=(2, 0))

        f_graf = UIBuilder.frame(r2, bg=BG2)
        f_graf.pack(side="left", fill="x", expand=True, padx=(8, 0))
        UIBuilder.label(f_graf, "Gráfico / Estampa (Opcional)", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w")
        UIBuilder.entry(f_graf, var=vs["grafico"], width=22).pack(fill="x", ipady=3, pady=(2, 0))

        # 3. Cor e Numeração
        r3 = UIBuilder.frame(inner_d, bg=BG2, pady=4)
        r3.pack(fill="x")

        f_cor = UIBuilder.frame(r3, bg=BG2)
        f_cor.pack(side="left", fill="x", expand=True, padx=(0, 8))
        UIBuilder.label(f_cor, "Cor Dominante", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w")
        cores_lista = ["Preto", "Branco", "Vermelho", "Azul", "Verde", "Amarelo", "Cinza", "Roxo", "Natural / Madeira", "Multicolor"]
        cb_cor = ttk.Combobox(f_cor, textvariable=vs["cor"], values=cores_lista, font=FONT_BODY)
        cb_cor.pack(fill="x", ipady=3, pady=(2, 0))

        f_num = UIBuilder.frame(r3, bg=BG2)
        f_num.pack(side="left", fill="x", expand=True, padx=(8, 0))
        UIBuilder.label(f_num, "Numeração / Tamanho", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w")
        cb_num = ttk.Combobox(f_num, textvariable=vs["numeracao"], font=FONT_BODY)
        if tipo_atual in NUMERACAO_POR_TIPO:
            cb_num.config(values=NUMERACAO_POR_TIPO[tipo_atual])
        cb_num.pack(fill="x", ipady=3, pady=(2, 0))

        # Cascata Tipo / Marca
        def atualizar_cascata_tipo(*_):
            tipo_sel = vs["tipo"].get().strip().lower()
            if tipo_sel:
                marcas_filtradas = sorted(list({r[1] for r in self._catalogo_local if r[1] and r[0].lower() == tipo_sel}))
                modelos_filtrados = sorted(list({r[2] for r in self._catalogo_local if r[2] and r[0].lower() == tipo_sel}))
            else:
                marcas_filtradas = sorted(list({r[1] for r in self._catalogo_local if r[1]}))
                modelos_filtrados = sorted(list({r[2] for r in self._catalogo_local if r[2]}))

            cb_marca.config(values=marcas_filtradas)
            cb_mod.config(values=modelos_filtrados)

            orig_tipo = vs["tipo"].get().strip()
            if orig_tipo in NUMERACAO_POR_TIPO:
                cb_num.config(values=NUMERACAO_POR_TIPO[orig_tipo])

        def atualizar_cascata_marca(*_):
            tipo_sel = vs["tipo"].get().strip().lower()
            marca_sel = vs["marca"].get().strip().lower()
            if tipo_sel and marca_sel:
                modelos_filtrados = sorted(list({r[2] for r in self._catalogo_local if r[2] and r[0].lower() == tipo_sel and r[1].lower() == marca_sel}))
            elif marca_sel:
                modelos_filtrados = sorted(list({r[2] for r in self._catalogo_local if r[2] and r[1].lower() == marca_sel}))
            elif tipo_sel:
                modelos_filtrados = sorted(list({r[2] for r in self._catalogo_local if r[2] and r[0].lower() == tipo_sel}))
            else:
                modelos_filtrados = sorted(list({r[2] for r in self._catalogo_local if r[2]}))

            cb_mod.config(values=modelos_filtrados)

        cb_tipo.bind("<<ComboboxSelected>>", lambda *_: (atualizar_cascata_tipo(), recalcular_sku_auto()))
        cb_marca.bind("<<ComboboxSelected>>", lambda *_: (atualizar_cascata_marca(), recalcular_sku_auto()))

        # 4. Quantidade, Valores e Status
        r4 = UIBuilder.frame(inner_d, bg=BG2, pady=4)
        r4.pack(fill="x")

        f_qtd = UIBuilder.frame(r4, bg=BG2)
        f_qtd.pack(side="left", fill="x", expand=True, padx=(0, 4))
        UIBuilder.label(f_qtd, "Qtd / Estoque *", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w")
        UIBuilder.entry(f_qtd, var=vs["qtd"], width=8).pack(fill="x", ipady=3, pady=(2, 0))

        f_porig = UIBuilder.frame(r4, bg=BG2)
        f_porig.pack(side="left", fill="x", expand=True, padx=(4, 4))
        UIBuilder.label(f_porig, "Preço Original (R$)", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w")
        e_orig = UIBuilder.entry(f_porig, width=12)
        e_orig.insert(0, f"{float(preco_orig_atual):.2f}".replace(".", ","))
        e_orig.pack(fill="x", ipady=3, pady=(2, 0))
        e_orig.bind("<KeyRelease>", lambda _: CurrencyFormatter.formatar_moeda_local(e_orig))

        f_pout = UIBuilder.frame(r4, bg=BG2)
        f_pout.pack(side="left", fill="x", expand=True, padx=(4, 4))
        UIBuilder.label(f_pout, "Preço Outlet *", font=FONT_SMALL, bg=BG2, fg=GOLD).pack(anchor="w")
        e_out = UIBuilder.entry(f_pout, width=12)
        e_out.insert(0, f"{float(preco_out_atual):.2f}".replace(".", ","))
        e_out.pack(fill="x", ipady=3, pady=(2, 0))
        e_out.bind("<KeyRelease>", lambda _: CurrencyFormatter.formatar_moeda_local(e_out))

        f_status = UIBuilder.frame(r4, bg=BG2)
        f_status.pack(side="left", fill="x", expand=True, padx=(4, 0))
        UIBuilder.label(f_status, "Status", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w")
        cb_status = ttk.Combobox(f_status, textvariable=vs["status"], values=["Disponível", "Baixado", "Reservado"], font=FONT_BODY)
        cb_status.pack(fill="x", ipady=3, pady=(2, 0))

        # 5. SKU e EAN
        r_sku = UIBuilder.card(inner_d, bg=BG3, px=14, py=10)
        r_sku.pack(fill="x", pady=10)

        top_sku = UIBuilder.frame(r_sku, bg=BG3)
        top_sku.pack(fill="x")
        UIBuilder.label(top_sku, f"🏷️ SKU & EAN-13 (EAN: {ean_atual or 'N/A'})", font=FONT_SMALL, bg=BG3, fg=GOLD).pack(side="left")
        
        e_sku = UIBuilder.entry(r_sku, var=vs["sku"], width=30)
        e_sku.pack(fill="x", ipady=4, pady=(4, 0))

        def recalcular_sku_auto(*_):
            tipo = vs["tipo"].get().strip()
            marca = vs["marca"].get().strip()
            modelo = vs["modelo"].get().strip()
            grafico = vs["grafico"].get().strip()
            cor = vs["cor"].get().strip()
            numeracao = vs["numeracao"].get().strip()

            if not (tipo or marca or modelo):
                return

            sku_calc = calcular_sku(
                tipo=tipo,
                marca=marca,
                modelo=modelo,
                grafico=grafico,
                cor=cor,
                numeracao=numeracao
            )
            if vs["sku"].get() != sku_calc:
                vs["sku"].set(sku_calc)

        vs["tipo"].trace_add("write", lambda *_: (atualizar_cascata_tipo(), recalcular_sku_auto()))
        vs["marca"].trace_add("write", lambda *_: (atualizar_cascata_marca(), recalcular_sku_auto()))
        for k in ["modelo", "grafico", "cor", "numeracao"]:
            vs[k].trace_add("write", lambda *_: recalcular_sku_auto())

        # Botão Salvar
        def salvar():
            sel = tv_cli.selection()
            if not sel:
                self.app.toast.show("Selecione o proprietário do produto (Cliente)", "erro")
                return

            novo_cli_id = int(sel[0])
            tipo = vs["tipo"].get().strip()
            marca = vs["marca"].get().strip()
            modelo = vs["modelo"].get().strip()
            grafico = vs["grafico"].get().strip() or None
            cor = vs["cor"].get().strip() or None
            numeracao = vs["numeracao"].get().strip() or None
            sku = vs["sku"].get().strip()
            status_novo = vs["status"].get().strip() or "Disponível"

            if not tipo:
                self.app.toast.show("Informe a Categoria / Tipo do produto.", "erro")
                return
            if not marca:
                self.app.toast.show("Informe a Marca do produto.", "erro")
                return
            if not modelo:
                self.app.toast.show("Informe o Modelo do produto.", "erro")
                return

            preco_orig = txt_para_float(e_orig.get())
            preco_outlet = txt_para_float(e_out.get())
            if preco_outlet <= 0:
                self.app.toast.show("Informe um Valor de Outlet válido.", "erro")
                return

            try:
                qtd = int(vs["qtd"].get().strip() or 1)
            except ValueError:
                qtd = 1

            estoque_val = 0 if status_novo == "Baixado" else qtd

            salvar_hierarquia(tipo, marca, modelo)
            nome_composto = f"{marca} {modelo}" + (f" ({grafico})" if grafico else "")

            with get_conn() as conn:
                conn.execute("""
                    UPDATE produtos_outlet SET
                        cliente_id = %s,
                        sku = %s,
                        tipo = %s,
                        marca = %s,
                        modelo = %s,
                        grafico = %s,
                        cor = %s,
                        numeracao = %s,
                        tamanho = %s,
                        preco_original = %s,
                        preco_outlet = %s,
                        valor_sugerido = %s,
                        estoque = %s,
                        quantidade = %s,
                        status = %s,
                        nome = %s
                    WHERE id = %s
                """, (
                    novo_cli_id, sku, tipo, marca, modelo, grafico, cor,
                    numeracao, numeracao, preco_orig, preco_outlet, preco_outlet,
                    estoque_val, qtd, status_novo, nome_composto, self.pid
                ))
                conn.commit()

            from core.cache import cache
            cache.invalidate_prefix("outlet")
            cache.invalidate_prefix("dashboard")
            cache.invalidate_prefix("fila")
            cache.invalidate_prefix("creditos")

            win.destroy()
            self.callback()
            self.app.toast.show(f"Produto #{self.pid} atualizado com sucesso!", "sucesso")

        b_salvar = UIBuilder.button(main_fm, "💾 Salvar Alterações", salvar, color=SUCCESS, fg="#000", width=36)
        b_salvar.pack(pady=14, ipady=6)


class PopupProdutoDetalhes:
    """Popup de visualização completa dos detalhes do produto outlet com ações de edição e baixa."""

    def __init__(self, app, pid, callback=None):
        self.app = app
        self.pid = pid
        self.callback = callback
        self.win = None
        self._build_container()
        self._carregar_dados()

    def _build_container(self):
        self.win = tk.Toplevel(self.app)
        self.win.title(f"Detalhes do Produto — ID #{self.pid}")
        UIBuilder.centralizar_janela(self.win, 800, 660, parent=self.app)
        self.win.configure(bg=BG)
        self.win.grab_set()

    def _carregar_dados(self):
        def _buscar():
            with get_conn() as conn:
                return conn.execute("""
                    SELECT p.id, 
                           COALESCE(p.codigo_barras, '—') AS ean, 
                           COALESCE(p.sku, '—') AS sku, 
                           COALESCE(p.tipo, '—') AS tipo, 
                           COALESCE(p.marca, '—') AS marca, 
                           COALESCE(p.modelo, p.nome) AS modelo,
                           COALESCE(p.grafico, '—') AS grafico, 
                           COALESCE(p.cor, '—') AS cor, 
                           COALESCE(p.numeracao, p.tamanho, '—') AS numeracao,
                           COALESCE(p.preco_original, 0) AS preco_orig, 
                           COALESCE(p.preco_outlet, p.valor_sugerido, 0) AS preco_out, 
                           COALESCE(p.quantidade, p.estoque, 1) AS quantidade, 
                           COALESCE(p.status, 'Disponível') AS status, 
                           p.criado,
                           COALESCE(c.nome, '—') AS cliente_nome, 
                           COALESCE(c.cpf, '—') AS cliente_cpf,
                           COALESCE(c.telefone, '—') AS cliente_tel,
                           c.id AS cliente_id
                    FROM produtos_outlet p 
                    LEFT JOIN clientes c ON p.cliente_id = c.id 
                    WHERE p.id = %s
                """, (self.pid,)).fetchone()

        def _render(row):
            if not row:
                self.app.toast.show("Produto não encontrado.", "erro")
                self.win.destroy()
                return

            for w in self.win.winfo_children():
                w.destroy()

            (
                pid, ean, sku, tipo, marca, modelo,
                grafico, cor, numeracao,
                preco_orig, preco_out, qtd, status,
                criado, cli_nome, cli_cpf, cli_tel, cli_id
            ) = row

            main_fm = UIBuilder.card(self.win, bg=BG2, px=24, py=20)
            main_fm.pack(fill="both", expand=True, padx=16, pady=16)

            # Cabeçalho com Status Badge
            h_row = UIBuilder.frame(main_fm, bg=BG2)
            h_row.pack(fill="x", pady=(0, 12))

            h_left = UIBuilder.frame(h_row, bg=BG2)
            h_left.pack(side="left")
            UIBuilder.label(h_left, f"🏷️ {marca} {modelo}", font=FONT_H2, bg=BG2, fg=GOLD).pack(anchor="w")
            UIBuilder.label(h_left, f"ID #{pid}  •  Adicionado em: {formatar_data(criado)}", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w")

            status_cor = SUCCESS if status == "Disponível" else (DANGER if status == "Baixado" else GOLD)
            status_bg = "#162E20" if status == "Disponível" else ("#2E1619" if status == "Baixado" else "#2E2416")
            badge = tk.Label(h_row, text=f"  {status.upper()}  ", font=("Segoe UI", 10, "bold"), bg=status_bg, fg=status_cor, padx=8, pady=4, relief="flat")
            badge.pack(side="right", padx=(8, 0))

            # Corpo com Scrolled Canvas
            scroll_fm = UIBuilder.frame(main_fm, bg=BG2)
            scroll_fm.pack(fill="both", expand=True)
            canvas, inner = UIBuilder.scrolled_canvas(scroll_fm)

            # 1. Informações de Identificação & SKU
            c1 = UIBuilder.card(inner, bg=BG3, px=16, py=12)
            c1.pack(fill="x", pady=(0, 10))
            UIBuilder.label(c1, "🔢 Identificação & Códigos", font=FONT_SMALL, bg=BG3, fg=GOLD).pack(anchor="w", pady=(0, 6))
            
            g1 = UIBuilder.frame(c1, bg=BG3)
            g1.pack(fill="x")
            
            f_sku = UIBuilder.frame(g1, bg=BG3)
            f_sku.pack(side="left", fill="x", expand=True)
            UIBuilder.label(f_sku, "SKU Interno:", font=FONT_SMALL, bg=BG3, fg=TEXT_DIM).pack(anchor="w")
            UIBuilder.label(f_sku, sku, font=FONT_CODE, bg=BG3, fg=TEXT).pack(anchor="w")

            f_ean = UIBuilder.frame(g1, bg=BG3)
            f_ean.pack(side="left", fill="x", expand=True, padx=(12, 0))
            UIBuilder.label(f_ean, "Código EAN-13:", font=FONT_SMALL, bg=BG3, fg=TEXT_DIM).pack(anchor="w")
            UIBuilder.label(f_ean, ean, font=FONT_CODE, bg=BG3, fg=TEXT).pack(anchor="w")

            # 2. Atributos do Produto
            c2 = UIBuilder.card(inner, bg=BG3, px=16, py=12)
            c2.pack(fill="x", pady=(0, 10))
            UIBuilder.label(c2, "📦 Características do Produto", font=FONT_SMALL, bg=BG3, fg=GOLD).pack(anchor="w", pady=(0, 6))

            g2 = UIBuilder.frame(c2, bg=BG3)
            g2.pack(fill="x", pady=2)

            for col_title, col_val in [("Categoria / Tipo", tipo), ("Marca", marca), ("Modelo / Edição", modelo)]:
                fc = UIBuilder.frame(g2, bg=BG3)
                fc.pack(side="left", fill="x", expand=True)
                UIBuilder.label(fc, col_title, font=FONT_SMALL, bg=BG3, fg=TEXT_DIM).pack(anchor="w")
                UIBuilder.label(fc, col_val, font=FONT_BODY, bg=BG3, fg=TEXT).pack(anchor="w")

            g2_b = UIBuilder.frame(c2, bg=BG3)
            g2_b.pack(fill="x", pady=(8, 0))

            for col_title, col_val in [("Gráfico / Estampa", grafico), ("Cor Dominante", cor), ("Numeração / Tamanho", numeracao)]:
                fc = UIBuilder.frame(g2_b, bg=BG3)
                fc.pack(side="left", fill="x", expand=True)
                UIBuilder.label(fc, col_title, font=FONT_SMALL, bg=BG3, fg=TEXT_DIM).pack(anchor="w")
                UIBuilder.label(fc, col_val, font=FONT_BODY, bg=BG3, fg=TEXT).pack(anchor="w")

            # 3. Valores e Estoque
            c3 = UIBuilder.card(inner, bg=BG3, px=16, py=12)
            c3.pack(fill="x", pady=(0, 10))
            UIBuilder.label(c3, "💰 Valores & Estoque", font=FONT_SMALL, bg=BG3, fg=GOLD).pack(anchor="w", pady=(0, 6))

            g3 = UIBuilder.frame(c3, bg=BG3)
            g3.pack(fill="x")

            f_po = UIBuilder.frame(g3, bg=BG3)
            f_po.pack(side="left", fill="x", expand=True)
            UIBuilder.label(f_po, "Preço Original", font=FONT_SMALL, bg=BG3, fg=TEXT_DIM).pack(anchor="w")
            UIBuilder.label(f_po, brl(preco_orig), font=FONT_BODY, bg=BG3, fg=TEXT).pack(anchor="w")

            f_pout = UIBuilder.frame(g3, bg=BG3)
            f_pout.pack(side="left", fill="x", expand=True)
            UIBuilder.label(f_pout, "Preço Outlet (Venda)", font=FONT_SMALL, bg=BG3, fg=GOLD).pack(anchor="w")
            UIBuilder.label(f_pout, brl(preco_out), font=FONT_H2, bg=BG3, fg=SUCCESS).pack(anchor="w")

            f_qtd = UIBuilder.frame(g3, bg=BG3)
            f_qtd.pack(side="left", fill="x", expand=True)
            UIBuilder.label(f_qtd, "Qtd em Estoque", font=FONT_SMALL, bg=BG3, fg=TEXT_DIM).pack(anchor="w")
            UIBuilder.label(f_qtd, str(qtd), font=FONT_H2, bg=BG3, fg=TEXT).pack(anchor="w")

            # 4. Proprietário (Cliente)
            c4 = UIBuilder.card(inner, bg=BG3, px=16, py=12)
            c4.pack(fill="x", pady=(0, 6))
            UIBuilder.label(c4, "👤 Proprietário (Cliente)", font=FONT_SMALL, bg=BG3, fg=GOLD).pack(anchor="w", pady=(0, 6))

            g4 = UIBuilder.frame(c4, bg=BG3)
            g4.pack(fill="x")

            f_cnome = UIBuilder.frame(g4, bg=BG3)
            f_cnome.pack(side="left", fill="x", expand=True)
            UIBuilder.label(f_cnome, "Nome do Cliente", font=FONT_SMALL, bg=BG3, fg=TEXT_DIM).pack(anchor="w")
            UIBuilder.label(f_cnome, cli_nome, font=FONT_BODY, bg=BG3, fg=TEXT).pack(anchor="w")

            f_ccpf = UIBuilder.frame(g4, bg=BG3)
            f_ccpf.pack(side="left", fill="x", expand=True)
            UIBuilder.label(f_ccpf, "CPF", font=FONT_SMALL, bg=BG3, fg=TEXT_DIM).pack(anchor="w")
            UIBuilder.label(f_ccpf, cli_cpf, font=FONT_BODY, bg=BG3, fg=TEXT).pack(anchor="w")

            f_ctel = UIBuilder.frame(g4, bg=BG3)
            f_ctel.pack(side="left", fill="x", expand=True)
            UIBuilder.label(f_ctel, "Telefone", font=FONT_SMALL, bg=BG3, fg=TEXT_DIM).pack(anchor="w")
            UIBuilder.label(f_ctel, cli_tel, font=FONT_BODY, bg=BG3, fg=TEXT).pack(anchor="w")

            # Barra Inferior de Botões de Ação
            b_row = UIBuilder.frame(main_fm, bg=BG2)
            b_row.pack(fill="x", pady=(14, 0))

            def _abrir_edicao():
                PopupProdutoEditar(self.app, self.pid, lambda: (self._carregar_dados(), self.callback and self.callback()))

            def _abrir_baixa():
                PopupBaixaProduto(self.app, self.pid, lambda: (self.win.destroy(), self.callback and self.callback()))

            def _imprimir():
                from utils.printer import PDFPrinter
                printer = PDFPrinter()
                def _tarefa():
                    return printer.imprimir_produtos_direto([self.pid], {self.pid: 1})
                def _fim(res):
                    sucesso, msg = res
                    self.app.toast.show(msg, "sucesso" if sucesso else "erro")
                self.app.executar_async(funcao_task=_tarefa, callback_sucesso=_fim, mensagem="Imprimindo etiqueta...")

            botoes_det_out = [
                ("✏️ Editar Produto", _abrir_edicao, GOLD, "#000"),
            ]
            if status != "Baixado":
                botoes_det_out.append(("✅ Dar Baixa / Venda", _abrir_baixa, SUCCESS, "#000"))
            botoes_det_out.append(("🖨️ Imprimir Etiqueta", _imprimir, ACCENT, TEXT))
            botoes_det_out.append(("Fechar", self.win.destroy, BG3, TEXT))

            b_row = UIBuilder.responsive_button_bar(self.win, botoes_det_out, breakpoint=680, bg=BG2, py_btn=7)
            b_row.pack(fill="x", padx=24, pady=12)

        self.app.executar_async(
            funcao_task=_buscar,
            callback_sucesso=_render,
            mensagem="Carregando detalhes do produto..."
        )


class PopupBaixaProduto:
    """Popup para registrar a baixa / venda de um produto outlet com toggle moderno para conversão em crédito."""

    def __init__(self, app, pid, callback):
        self.app = app
        self.pid = pid
        self.callback = callback
        self._build()

    def _build(self):
        with get_conn() as conn:
            row = conn.execute("""
                SELECT p.id, COALESCE(p.nome, CONCAT(p.marca, ' ', p.modelo)) AS produto,
                       COALESCE(p.preco_outlet, p.valor_sugerido, 0) AS preco,
                       p.cliente_id, c.nome AS cliente_nome, p.status, COALESCE(p.sku, '—') AS sku
                FROM produtos_outlet p
                LEFT JOIN clientes c ON p.cliente_id = c.id
                WHERE p.id = %s
            """, (self.pid,)).fetchone()

        if not row:
            self.app.toast.show("Produto não encontrado.", "erro")
            return

        pid, nome_prod, preco_outlet, cliente_id, cliente_nome, status, sku = row
        preco_val = float(preco_outlet or 0)
        cli_nome = cliente_nome or "Sem proprietário vinculado"

        win = tk.Toplevel(self.app)
        win.title(f"Baixa de Produto — ID #{pid}")
        UIBuilder.centralizar_janela(win, 540, 480, parent=self.app)
        win.configure(bg=BG)
        win.resizable(False, False)
        win.grab_set()

        # Container Principal
        card = UIBuilder.card(win, bg=BG2, px=28, py=22)
        card.pack(fill="both", expand=True, padx=16, pady=16)

        # Cabeçalho
        UIBuilder.label(card, "✅ Baixa / Venda de Produto", font=FONT_H2, bg=BG2, fg=SUCCESS).pack(anchor="w", pady=(0, 4))
        UIBuilder.label(card, f"Produto: {nome_prod}", font=FONT_BODY, bg=BG2, fg=TEXT).pack(anchor="w")
        UIBuilder.label(card, f"SKU: {sku}  •  Proprietário: {cli_nome}", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w", pady=(0, 14))

        # Campo Valor de Venda
        UIBuilder.label(card, "Valor Final da Venda (R$)*", font=FONT_SMALL, bg=BG2, fg=GOLD).pack(anchor="w")
        e_venda = UIBuilder.entry(card, width=28)
        e_venda.pack(fill="x", ipady=5, pady=(3, 16))
        e_venda.insert(0, f"{preco_val:.2f}".replace(".", ","))
        e_venda.bind("<KeyRelease>", lambda _: CurrencyFormatter.formatar_moeda_local(e_venda))

        # Variável de estado do crédito
        tem_cliente = bool(cliente_id)
        add_cred = tk.BooleanVar(value=tem_cliente)

        # Card / Toggle Moderno de Conversão em Crédito
        toggle_card = tk.Frame(
            card, 
            bg="#12241A" if tem_cliente else BG3, 
            padx=14, 
            pady=12,
            highlightbackground=SUCCESS if tem_cliente else "#3A3A45", 
            highlightthickness=1, 
            cursor="hand2" if tem_cliente else "arrow"
        )
        toggle_card.pack(fill="x", pady=(0, 16))

        top_row = tk.Frame(toggle_card, bg=toggle_card["bg"])
        top_row.pack(fill="x")

        lbl_badge = tk.Label(
            top_row, 
            text="🟢 CRÉDITO ATIVO" if tem_cliente else "⚪ DESATIVADO",
            font=("Segoe UI", 9, "bold"), 
            bg="#1A3D29" if tem_cliente else BG2,
            fg=SUCCESS if tem_cliente else TEXT_DIM, 
            padx=8, 
            pady=2
        )
        lbl_badge.pack(side="left")

        lbl_titulo = tk.Label(
            top_row, 
            text="Converter valor em Crédito para o Cliente",
            font=("Segoe UI", 10, "bold"), 
            bg=toggle_card["bg"],
            fg=TEXT if tem_cliente else TEXT_DIM
        )
        lbl_titulo.pack(side="left", padx=(8, 0))

        lbl_desc = tk.Label(
            toggle_card,
            text=f"O valor pago será creditado diretamente no saldo de '{cli_nome}'." if tem_cliente else "Nenhum cliente vinculado para receber o crédito.",
            font=FONT_SMALL,
            bg=toggle_card["bg"],
            fg=SUCCESS if tem_cliente else TEXT_DIM,
            wraplength=420,
            justify="left"
        )
        lbl_desc.pack(anchor="w", pady=(6, 0))

        def alternar_credito(event=None):
            if not cliente_id:
                self.app.toast.show("Este produto não possui cliente proprietário vinculado.", "aviso")
                return
            novo_estado = not add_cred.get()
            add_cred.set(novo_estado)
            
            bg_cor = "#12241A" if novo_estado else BG3
            badge_bg = "#1A3D29" if novo_estado else BG2
            border_cor = SUCCESS if novo_estado else "#3A3A45"
            fg_texto = SUCCESS if novo_estado else TEXT_DIM

            toggle_card.configure(bg=bg_cor, highlightbackground=border_cor)
            top_row.configure(bg=bg_cor)
            lbl_titulo.configure(bg=bg_cor, fg=TEXT if novo_estado else TEXT_DIM)
            lbl_badge.configure(
                text="🟢 CRÉDITO ATIVO" if novo_estado else "⚪ DESATIVADO",
                bg=badge_bg,
                fg=fg_texto
            )
            lbl_desc.configure(
                bg=bg_cor,
                fg=fg_texto,
                text=f"O valor pago será creditado diretamente no saldo de '{cli_nome}'." if novo_estado else "Apenas altera status para 'Baixado' sem creditar o cliente."
            )

        if tem_cliente:
            toggle_card.bind("<Button-1>", alternar_credito)
            for w in (top_row, lbl_badge, lbl_titulo, lbl_desc):
                w.bind("<Button-1>", alternar_credito)

        # Ações
        def confirmar():
            val = txt_para_float(e_venda.get())
            if val < 0:
                self.app.toast.show("Valor de venda inválido.", "erro")
                return
            win.destroy()

            def _tarefa_baixa():
                with get_conn() as conn:
                    conn.execute("UPDATE produtos_outlet SET status='Baixado', estoque=0 WHERE id=%s", (pid,))
                    conn.execute("""
                        INSERT INTO vendas_outlet (cliente_id, produto_id, quantidade, preco_pago, criado) 
                        VALUES (%s,%s,%s,%s,%s)
                    """, (cliente_id, pid, 1, val, agora()))
                    if add_cred.get() and cliente_id:
                        conn.execute("UPDATE clientes SET saldo = COALESCE(saldo,0) + %s WHERE id=%s", (val, cliente_id))
                        conn.execute("""
                            INSERT INTO historico_credito (cliente_id,tipo,valor,motivo,criado) 
                            VALUES (%s,%s,%s,%s,%s)
                        """, (cliente_id, "entrada", val, f"Venda outlet: {nome_prod}", agora()))
                    conn.commit()
                cache.invalidate_prefix("outlet")
                cache.invalidate_prefix("dashboard")
                cache.invalidate_prefix("creditos")
                cache.invalidate_prefix("clientes")

            def _ao_concluir_baixa(_):
                self.app.toast.show("Baixa realizada com sucesso!", "sucesso")
                self.callback()

            self.app.executar_async(
                funcao_task=_tarefa_baixa,
                callback_sucesso=_ao_concluir_baixa,
                mensagem="Registrando baixa e crédito..."
            )

        f_acoes = UIBuilder.responsive_button_bar(
            card,
            [
                ("Cancelar", win.destroy, BG3, TEXT),
                ("✅ Confirmar Baixa", confirmar, SUCCESS, "#000"),
            ],
            breakpoint=450,
            bg=BG2,
            py_btn=7
        )
        f_acoes.pack(fill="x", pady=(10, 0))