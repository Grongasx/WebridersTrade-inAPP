"""
Tela Configurações - Configurações de etiquetas e fila de impressão.
"""

import json
import tkinter as tk
from tkinter import ttk, messagebox
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
    FONT_TITLE,
    FONT_H2,
    FONT_BODY,
    FONT_SMALL,
)
from ui.screens.base_screen import BaseScreen
from ui.components.base import UIBuilder
from core.database import get_conn
from core.config_local import carregar_config_local, salvar_config_local
from utils.printer import PDFPrinter


class ConfiguracoesScreen(BaseScreen):
    """Tela de configurações de etiquetas e fila de impressão."""

    def __init__(self, app, content_frame):
        super().__init__(app, content_frame)
        self._tree_fila = None
        self._printer = PDFPrinter()
        self._itens_fila = []

    def show(self, **kwargs):
        # Dispara o carregamento assíncrono sem limpar a tela imediatamente
        self._carregar_configuracoes()

    def _carregar_configuracoes(self):
        """Busca os itens pendentes da fila de impressão no banco em segundo plano."""

        def _buscar_db():
            with get_conn() as conn:
                return conn.execute("""
                    SELECT id, produto_id, texto_etiqueta, quantidade, status 
                    FROM fila_impressao 
                    WHERE status = 'Pendente' 
                    ORDER BY id ASC
                """).fetchall()

        def _ao_concluir(rows):
            self._itens_fila = rows
            self.clear()
            self._build()
            self._popular_tree()

        self.app.executar_async(
            funcao_task=_buscar_db,
            callback_sucesso=_ao_concluir,
            mensagem="Carregando configurações e fila..."
        )

    def _build(self):
        h = self.build_header("🖨  Etiquetas & Impressão Térmica", fg=GOLD)

        main_fm = UIBuilder.frame(self.content, padx=28, pady=10)
        main_fm.pack(fill="both", expand=True)

        # Coluna Esquerda - Configurações Locais
        col_esq = UIBuilder.card(main_fm, bg=BG2, px=18, py=14)
        col_esq.pack(side="left", fill="y", padx=(0, 10))
        UIBuilder.label(
            col_esq,
            "🖨  Hardware & Impressora (3 Colunas)",
            font=FONT_H2,
            bg=BG2,
            fg=GOLD,
        ).pack(anchor="w", pady=(0, 10))

        # Carrega as configurações salvas no arquivo JSON local
        cfgs = carregar_config_local()

        lista_impressoras = self.app._obter_impressoras_windows()
        imp_salva = cfgs.get("nome_impressora", "")

        val_inicial = (
            imp_salva
            if imp_salva in lista_impressoras
            else (
                lista_impressoras[0]
                if lista_impressoras
                else "Microsoft Print to PDF"
            )
        )
        v_imp = tk.StringVar(value=val_inicial)

        UIBuilder.label(
            col_esq,
            "Impressora no Windows:",
            font=FONT_SMALL,
            bg=BG2,
            fg=TEXT,
        ).pack(anchor="w", pady=(8, 2))
        cb_imp = ttk.Combobox(
            col_esq,
            textvariable=v_imp,
            values=lista_impressoras,
            state="readonly",
            font=FONT_BODY,
        )
        cb_imp.pack(fill="x", pady=(0, 10))

        UIBuilder.label(
            col_esq,
            "Configuração de Tamanho (mm):",
            font=FONT_SMALL,
            bg=BG2,
            fg=TEXT_DIM,
        ).pack(anchor="w", pady=(12, 4))
        ref_txt = (
            f"• Página Total: {cfgs.get('etiq_largura_mm', '108')}mm x {cfgs.get('etiq_altura_mm', '25')}mm\n"
            f"• Colunas: {cfgs.get('etiq_por_linha', '3')} Etiquetas\n"
            f"• Largura Indiv.: {cfgs.get('etiq_indiv_largura_mm', '34')}mm | Gap: {cfgs.get('etiq_espaco_colunas_mm', '2')}mm\n"
            f"• Margens: Esq {cfgs.get('etiq_margem_esq', '2')} | Dir {cfgs.get('etiq_margem_dir', '2')} | Top {cfgs.get('etiq_margem_top', '2')}"
        )
        UIBuilder.label(
            col_esq,
            ref_txt,
            font=("Segoe UI", 9),
            bg=BG3,
            fg=TEXT,
            justify="left",
            padx=10,
            pady=8,
        ).pack(fill="x", pady=(0, 15))

        def salvar_imp(*args):
            nome_selecionado = v_imp.get().strip()
            if nome_selecionado:
                salvar_config_local({"nome_impressora": nome_selecionado})
                self.toast.show(
                    f"Impressora '{nome_selecionado}' salva localmente!",
                    "sucesso",
                )

        cb_imp.bind("<<ComboboxSelected>>", salvar_imp)
        UIBuilder.button(
            col_esq, "💾 Salvar Impressora", salvar_imp, color=BG3, width=38
        ).pack(pady=(0, 10))
        UIBuilder.button(
            col_esq,
            "📏 Ajustar Medidas e Margens",
            self._abrir_config_dimensoes,
            color=GOLD,
            fg="#000",
            width=38,
        ).pack(pady=5)

        # Coluna Direita - Fila de Impressão (Mantida no Neon DB)
        col_dir = UIBuilder.card(main_fm, bg=BG2, px=18, py=14)
        col_dir.pack(side="left", fill="both", expand=True, padx=(10, 0))
        UIBuilder.label(
            col_dir, "📋 Fila de Impressão (PDF)", font=FONT_H2, bg=BG2, fg=GOLD
        ).pack(anchor="w", pady=(0, 10))

        tf = UIBuilder.frame(col_dir, bg=BG2)
        tf.pack(fill="both", expand=True)
        cols_fila = ("ID Prod", "Produto (Dados)", "Código", "Qtd", "Status")
        self._tree_fila = UIBuilder.make_tree(
            tf,
            cols_fila,
            [65, 230, 110, 50, 80],
            ["center", "w", "center", "center", "center"],
        )

        self._tree_fila.bind("<Double-1>", lambda e: self._editar())

        brow = UIBuilder.frame(col_dir, bg=BG2, pady=10)
        brow.pack(fill="x")
        UIBuilder.label(
            brow,
            "Pressione 'Shift' para selecionar várias.",
            font=("Segoe UI", 8),
            bg=BG2,
            fg=TEXT_DIM,
        ).pack(anchor="w", pady=(0, 4))
        UIBuilder.button(
            brow,
            "➕ Add Produto",
            self._add_produto,
            color=ACCENT,
            width=15,
        ).pack(side="left", padx=(0, 5), pady=5)
        UIBuilder.button(
            brow,
            "🖨️ Imprimir Lote",
            self._imprimir,
            color=SUCCESS,
            fg="#000",
            width=18,
        ).pack(side="left", padx=2, pady=5)
        UIBuilder.button(
            brow, "🗑️ Excluir", self._remover, color=DANGER, width=12
        ).pack(side="left", padx=2, pady=5)

    def _popular_tree(self):
        """Preenche a Treeview com os dados armazenados em memória exibindo o ID do produto."""
        if not self._tree_fila:
            return

        for r in self._tree_fila.get_children():
            self._tree_fila.delete(r)

        for r in self._itens_fila:
            fila_id = r[0]
            prod_id = r[1]
            try:
                d = json.loads(r[2]) if isinstance(r[2], str) else (r[2] or {})
                n = f"{d.get('nome')} | {d.get('preco')}"
                c = d.get("codigo") or d.get("sku") or "—"
                if not prod_id:
                    prod_id = d.get("id") or d.get("id_banco") or "—"
            except Exception:
                n, c = "ERRO DE FORMATO", "—"
                if not prod_id:
                    prod_id = "—"

            self._tree_fila.insert(
                "", "end", iid=str(fila_id), values=(prod_id, n, c, r[3], r[4])
            )

    def _editar(self):
        sel = self._tree_fila.selection()
        if not sel:
            self.toast.show("Selecione para editar.", "aviso")
            return
        from ui.screens.popup_config import PopupEditarEtiqueta

        PopupEditarEtiqueta(self.app, int(sel[0]), self._carregar_configuracoes)

    def _imprimir(self):
        sel = self._tree_fila.selection()
        if not sel:
            self.toast.show("Selecione itens para imprimir.", "aviso")
            return
        ids = [int(i) for i in sel]

        def _tarefa_imprimir():
            return self._printer.processar_impressao_multi_colunas(ids)

        def _ao_concluir_impressao(resultado):
            sucesso, msg = resultado
            if sucesso:
                self.toast.show(msg, "sucesso")
                self._carregar_configuracoes()
            else:
                self.toast.show(msg, "erro")

        self.app.executar_async(
            funcao_task=_tarefa_imprimir,
            callback_sucesso=_ao_concluir_impressao,
            mensagem="Gerando PDF e enviando para impressão..."
        )

    def _remover(self):
        sel = self._tree_fila.selection()
        if not sel:
            return

        ids = [int(i) for i in sel]

        def _tarefa_remover():
            with get_conn() as conn:
                for item_id in ids:
                    conn.execute(
                        "DELETE FROM fila_impressao WHERE id=%s", (item_id,)
                    )
                conn.commit()

        def _ao_remover_sucesso(_):
            self.toast.show(f"{len(ids)} item(ns) removido(s) da fila.", "aviso")
            self._carregar_configuracoes()

        self.app.executar_async(
            funcao_task=_tarefa_remover,
            callback_sucesso=_ao_remover_sucesso,
            mensagem="Removendo itens da fila..."
        )

    def _add_produto(self):
        from ui.screens.popup_config import PopupAddProduto

        PopupAddProduto(self.app, self._carregar_configuracoes)

    def _add_por_id(self):
        self._add_produto()

    def _abrir_config_dimensoes(self):
        from ui.screens.popup_config import PopupConfigDimensoes

        PopupConfigDimensoes(self.app, self._carregar_configuracoes)