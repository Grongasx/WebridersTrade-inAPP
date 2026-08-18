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
        win.geometry("1020x680")
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
        
        UIBuilder.button(main_fm, "✨ Salvar Produto & Enviar p/ Fila de Impressão", salvar, color=GOLD, fg="#000", width=36).pack(pady=10)