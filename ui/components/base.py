"""
Componentes UI base reutilizaveis.
"""

import tkinter as tk
from tkinter import ttk
from config import BG, BG2, BG3, ACCENT, GOLD, TEXT, TEXT_DIM, SUCCESS, WARNING, DANGER
from config import FONT_TITLE, FONT_H2, FONT_BODY, FONT_SMALL, FONT_MONO, FONT_CODE


class ToastNotification:
    """Notificacao toast flutuante."""
    
    def __init__(self, root):
        self.root = root
        self.active = False
        self.target_y = 15
        self.hide_y = -80
        self.current_y = self.hide_y
        self._after_id = None

        self.frame = tk.Frame(root, bg=DANGER, highlightbackground="#ffffff", highlightthickness=1)
        self.icon_lbl = tk.Label(self.frame, text="", bg=DANGER, font=("Segoe UI", 16), fg="#FFF")
        self.icon_lbl.pack(side="left", padx=(14, 4), pady=10)
        self.label = tk.Label(self.frame, text="", bg=DANGER, fg="#FFF", font=FONT_BODY, wraplength=440, justify="left", anchor="w")
        self.label.pack(side="left", padx=(0, 20), pady=12, fill="x", expand=True)

    def show(self, text, tipo="erro"):
        cores = {"sucesso": SUCCESS, "erro": DANGER, "aviso": WARNING}
        icones = {"sucesso": "✅", "erro": "❌", "aviso": "⚠️"}
        cor = cores.get(tipo, DANGER)
        icone = icones.get(tipo, "ℹ️")

        self.frame.configure(bg=cor)
        self.icon_lbl.configure(bg=cor, text=icone)
        self.label.configure(bg=cor, text=text)

        if self._after_id:
            self.root.after_cancel(self._after_id)
            self._after_id = None

        self.active = True
        self.current_y = self.hide_y
        self._animar_descida()

    def _animar_descida(self):
        if self.current_y < self.target_y:
            self.current_y += 8
            self._reposicionar()
            self.root.after(10, self._animar_descida)
        else:
            self._after_id = self.root.after(3500, self._animar_subida)

    def _animar_subida(self):
        if self.current_y > self.hide_y:
            self.current_y -= 8
            self._reposicionar()
            self.root.after(10, self._animar_subida)
        else:
            self.frame.place_forget()
            self.active = False
            self._after_id = None

    def _reposicionar(self):
        rw = self.root.winfo_width() or 900
        self.frame.place(x=(rw // 2) - 260, y=self.current_y, width=520)
        self.frame.lift()

class LoadingPopup(tk.Frame):
    """Popup modal com fundo esmaecido e indicador visual de carregamento WEBRIDERS CLUB."""
    
    def __init__(self, root):
        super().__init__(root, bg="#070709")
        self.root = root
        self.is_running = False
        self._angle = 0

        # Modal / Card centralizado com borda destacada em vermelho elétrico
        self.box = tk.Frame(
            self, 
            bg=BG2, 
            padx=36, 
            pady=28, 
            highlightbackground=ACCENT, 
            highlightthickness=1
        )
        self.box.place(relx=0.5, rely=0.5, anchor="center")

        # Emblem Webriders no topo do spinner
        tk.Label(self.box, text="❖ WEBRIDERS", font=("Segoe UI Black", 10, "bold"), bg=BG2, fg=ACCENT).pack(pady=(0, 10))

        # Canvas para animação do spinner
        self.canvas = tk.Canvas(self.box, width=48, height=48, bg=BG2, highlightthickness=0)
        self.canvas.pack(pady=(0, 12))

        # Texto da mensagem
        self.label = tk.Label(
            self.box, 
            text="Carregando...", 
            bg=BG2, 
            fg=TEXT, 
            font=("Segoe UI", 11, "bold"),
            wraplength=300,
            justify="center"
        )
        self.label.pack()

    def start(self, mensagem="Processando..."):
        """Exibe o fundo esmaecido e o popup centralizado."""
        self.label.config(text=mensagem)
        self.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.lift()
        self.is_running = True
        self._animate()

    def stop(self):
        """Oculta o popup e esconde o esmaecimento."""
        self.is_running = False
        self.place_forget()

    def _animate(self):
        """Animação circular do indicador de progresso."""
        if not self.is_running:
            return

        self.canvas.delete("all")
        # Trilho de fundo sutil
        self.canvas.create_oval(4, 4, 44, 44, outline=BG3, width=4)
        # Arco animado giratório em vermelho elétrico
        self.canvas.create_arc(
            4, 4, 44, 44,
            start=self._angle,
            extent=110,
            outline=ACCENT,
            width=4,
            style="arc"
        )
        self._angle = (self._angle + 14) % 360
        self.root.after(25, self._animate)
        
class SmoothScroller:
    """Controlador de rolagem ultra-suave com amortecimento cinético e interpolação de física."""

    def __init__(self, canvas, sensitivity=0.028, friction=0.25):
        self.canvas = canvas
        self.sensitivity = sensitivity  # Fração de deslocamento suave por entalhe de roda
        self.friction = friction        # Taxa de amortecimento suave (lerp)
        self.target_y = 0.0
        self.is_animating = False

    def scroll(self, delta):
        if not self.canvas.winfo_exists():
            return
        
        try:
            current_view = self.canvas.yview()
            if not current_view:
                return

            visible_range = current_view[1] - current_view[0]
            if visible_range >= 0.999:
                return  # Todo o conteúdo já cabe na tela

            if not self.is_animating:
                self.target_y = current_view[0]

            notches = float(delta) / 120.0
            self.target_y -= notches * self.sensitivity
            max_y = max(0.0, 1.0 - visible_range)
            self.target_y = max(0.0, min(max_y, self.target_y))

            if not self.is_animating:
                self.is_animating = True
                self._animate()
        except Exception:
            pass

    def _animate(self):
        if not self.canvas.winfo_exists():
            self.is_animating = False
            return

        try:
            current_view = self.canvas.yview()
            if not current_view:
                self.is_animating = False
                return

            curr_y = current_view[0]
            diff = self.target_y - curr_y

            if abs(diff) < 0.0005:
                self.canvas.yview_moveto(self.target_y)
                self.is_animating = False
            else:
                new_y = curr_y + (diff * self.friction)
                self.canvas.yview_moveto(new_y)
                self.canvas.after(14, self._animate)
        except Exception:
            self.is_animating = False


class ScrollableFrame(tk.Frame):
    """Frame com scroll vertical e rolagem cinemática ultra-suave."""
    
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        bg_color = parent.cget("bg")
        self.configure(bg=bg_color)
        self.canvas = tk.Canvas(self, bg=bg_color, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scroller = SmoothScroller(self.canvas)
        self.scrollable_frame = tk.Frame(self, bg=bg_color)
        self.scrollable_frame.bind("<Configure>", lambda e: self.after(20, self._ajustar_barra))
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))
        self.canvas.pack(side="left", fill="both", expand=True)
        self._ativar_scroll_mouse()

    def _ajustar_barra(self):
        if not self.canvas.winfo_exists(): return
        self.update_idletasks()
        larg = self.scrollable_frame.winfo_reqwidth()
        alt = self.scrollable_frame.winfo_reqheight()
        self.canvas.configure(scrollregion=(0, 0, larg, alt))
        if alt > self.canvas.winfo_height(): self.scrollbar.pack(side="right", fill="y")
        else: self.scrollbar.pack_forget()

    def _ativar_scroll_mouse(self):
        top = self.winfo_toplevel()
        top.bind_all("<MouseWheel>", self._on_mouse_wheel)
        top.bind_all("<Button-4>", self._on_mouse_wheel)
        top.bind_all("<Button-5>", self._on_mouse_wheel)

    def _on_mouse_wheel(self, event):
        if not self.canvas.winfo_exists(): return
        if event.num == 4:
            self.scroller.scroll(120)
        elif event.num == 5:
            self.scroller.scroll(-120)
        else:
            self.scroller.scroll(event.delta)


class UIBuilder:
    """Construtor de widgets UI comuns."""
    
    @staticmethod
    def frame(parent, bg=BG, **kw):
        return tk.Frame(parent, bg=bg, **kw)
    
    @staticmethod
    def label(parent, text="", font=FONT_BODY, fg=TEXT, bg=BG, **kw):
        return tk.Label(parent, text=text, font=font, fg=fg, bg=bg, **kw)
    
    @staticmethod
    def entry(parent, var=None, width=30, **kw):
        return tk.Entry(parent, textvariable=var, font=FONT_BODY, bg=BG3, fg=TEXT, insertbackground=TEXT, relief="flat", bd=0, width=width, **kw)
    
    @staticmethod
    def button(parent, text, cmd, color=ACCENT, fg=TEXT, width=None, **kw):
        px = kw.pop('padx', 14)
        py = kw.pop('pady', 8)
        kw_btn = {
            'text': text,
            'command': cmd,
            'font': ("Segoe UI", 10, "bold"),
            'bg': color,
            'fg': fg,
            'activebackground': color,
            'activeforeground': fg,
            'relief': "flat",
            'bd': 0,
            'cursor': "hand2",
            'padx': px,
            'pady': py
        }
        if width is not None:
            kw_btn['width'] = width
        kw_btn.update(kw)
        return tk.Button(parent, **kw_btn)

    @staticmethod
    def responsive_button_bar(parent, buttons_list, breakpoint=780, bg=BG, py_btn=7):
        """
        Cria uma barra de botões com grid 100% responsivo, adaptativo e auto-distribuído.
        buttons_list: Lista de tuplas (texto, callback, cor_bg, cor_fg)
        """
        bar = tk.Frame(parent, bg=bg)
        widgets = []
        for item in buttons_list:
            if isinstance(item, (tuple, list)):
                rotulo = item[0]
                cmd = item[1]
                cor_bg = item[2] if len(item) > 2 else ACCENT
                cor_fg = item[3] if len(item) > 3 else TEXT
            else:
                continue

            btn = UIBuilder.button(bar, rotulo, cmd, color=cor_bg, fg=cor_fg, width=None, pady=py_btn)
            widgets.append(btn)

        n = len(widgets)
        if n == 0:
            return bar

        def _reorganizar(event=None):
            w = event.width if event else bar.winfo_width()
            if w <= 1:
                w = 1000

            for btn in widgets:
                btn.grid_forget()

            if w < breakpoint and n > 2:
                cols = 2 if n <= 4 else 3
                for c in range(cols):
                    bar.grid_columnconfigure(c, weight=1, uniform="r_btn_sub")
                for c in range(cols, n):
                    bar.grid_columnconfigure(c, weight=0, uniform="")

                for idx, btn in enumerate(widgets):
                    r = idx // cols
                    c = idx % cols
                    btn.grid(row=r, column=c, padx=3, pady=3, sticky="ew")
            else:
                for c in range(n):
                    bar.grid_columnconfigure(c, weight=1, uniform="r_btn_main")

                for idx, btn in enumerate(widgets):
                    btn.grid(row=0, column=idx, padx=3, pady=2, sticky="ew")

        bar.bind("<Configure>", _reorganizar)
        _reorganizar()
        return bar

    @staticmethod
    def separator(parent, bg=BG3, h=1):
        return tk.Frame(parent, bg=bg, height=h)
    
    @staticmethod
    def card(parent, bg=BG2, px=20, py=16, **kw):
        return tk.Frame(parent, bg=bg, padx=px, pady=py, **kw)
    
    @staticmethod
    def field(parent, label_text, var, hint="", bg=BG2, line_color=ACCENT, width=36):
        r = UIBuilder.frame(parent, bg=bg, pady=5)
        r.pack(fill="x")
        UIBuilder.label(r, label_text, font=FONT_SMALL, bg=bg, fg=TEXT_DIM).pack(anchor="w")
        UIBuilder.entry(r, var=var, width=width).pack(fill="x", ipady=7)
        tk.Frame(r, bg=line_color, height=1).pack(fill="x")
        if hint:
            UIBuilder.label(r, hint, font=("Segoe UI", 8), bg=bg, fg=TEXT_DIM).pack(anchor="w")
        return r
    
    @staticmethod
    def centralizar_janela(win, w=None, h=None, parent=None):
        """Centraliza uma janela na tela ou em relação à janela mãe (parent), respeitando limites de resolução."""
        win.update_idletasks()
        if w is None:
            w = win.winfo_reqwidth()
        if h is None:
            h = win.winfo_reqheight()

        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()

        # Limites defensivos para nunca estourar a tela
        w = min(w, sw - 40)
        h = min(h, sh - 80)

        if parent and parent.winfo_exists():
            px = parent.winfo_rootx()
            py = parent.winfo_rooty()
            pw = parent.winfo_width()
            ph = parent.winfo_height()
            x = px + (pw - w) // 2
            y = py + (ph - h) // 2
        else:
            x = (sw - w) // 2
            y = (sh - h) // 2 - 25

        x = max(10, min(x, sw - w - 10))
        y = max(10, min(y, sh - h - 40))

        win.geometry(f"{w}x{h}+{x}+{y}")
    
    @staticmethod
    def setup_tree_style(root=None):
        s = ttk.Style()
        s.theme_use("default")
        
        # Estilização da Treeview
        s.configure("Dark.Treeview", background=BG2, foreground=TEXT, fieldbackground=BG2, font=FONT_BODY, rowheight=34)
        s.configure("Dark.Treeview.Heading", background=BG3, foreground=GOLD, font=("Segoe UI", 10, "bold"), relief="flat")
        s.map("Dark.Treeview", background=[("selected", BG3)], foreground=[("selected", TEXT)])

        # Estilização completa das Scrollbars (Vertical e Horizontal) no tema WEBRIDERS CLUB
        s.configure("Vertical.TScrollbar",
                    background=BG3,
                    troughcolor=BG,
                    bordercolor=BG,
                    darkcolor=BG2,
                    lightcolor=BG2,
                    arrowcolor=TEXT_DIM,
                    relief="flat",
                    arrowsize=11,
                    width=10)
        s.map("Vertical.TScrollbar",
              background=[("active", ACCENT), ("pressed", GOLD), ("!disabled", BG3)],
              arrowcolor=[("active", ACCENT), ("pressed", GOLD), ("!disabled", TEXT_DIM)])

        s.configure("Horizontal.TScrollbar",
                    background=BG3,
                    troughcolor=BG,
                    bordercolor=BG,
                    darkcolor=BG2,
                    lightcolor=BG2,
                    arrowcolor=TEXT_DIM,
                    relief="flat",
                    arrowsize=11,
                    width=10)
        s.map("Horizontal.TScrollbar",
              background=[("active", ACCENT), ("pressed", GOLD), ("!disabled", BG3)],
              arrowcolor=[("active", ACCENT), ("pressed", GOLD), ("!disabled", TEXT_DIM)])

        # Estilização completa do Combobox no tema WEBRIDERS CLUB
        s.configure("TCombobox", 
                    fieldbackground=BG3, 
                    background=BG2, 
                    foreground=TEXT, 
                    darkcolor=BG2, 
                    lightcolor=BG2, 
                    bordercolor=BG3, 
                    arrowcolor=ACCENT, 
                    padding=6,
                    font=("Segoe UI", 10, "bold"))
        s.map("TCombobox", 
              fieldbackground=[("readonly", BG3), ("focus", BG3)],
              selectbackground=[("readonly", ACCENT), ("focus", ACCENT)],
              selectforeground=[("readonly", TEXT), ("focus", TEXT)],
              foreground=[("readonly", TEXT)],
              arrowcolor=[("hover", GOLD), ("focus", ACCENT)])

        if root:
            # Estilização do menu flutuante (Popdown Listbox)
            root.option_add("*TCombobox*Listbox.background", BG2)
            root.option_add("*TCombobox*Listbox.foreground", TEXT)
            root.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
            root.option_add("*TCombobox*Listbox.selectForeground", TEXT)
            root.option_add("*TCombobox*Listbox.font", ("Segoe UI", 10))
            root.option_add("*TCombobox*Listbox.bd", 1)
            root.option_add("*TCombobox*Listbox.relief", "flat")
            root.option_add("*TCombobox*Listbox.highlightThickness", 1)
            root.option_add("*TCombobox*Listbox.highlightColor", ACCENT)
    
    @staticmethod
    def make_tree(parent, cols, widths, anchors=None):
        sb = ttk.Scrollbar(parent, orient="vertical")
        tv = ttk.Treeview(parent, columns=cols, show="headings", style="Dark.Treeview", yscrollcommand=sb.set)
        sb.config(command=tv.yview)
        for i, (col, w) in enumerate(zip(cols, widths)):
            anc = anchors[i] if anchors else "w"
            tv.heading(col, text=col)
            tv.column(col, width=w, anchor=anc)
        tv.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        return tv
    
    @staticmethod
    def scrolled_canvas(parent, bg=BG):
        canvas = tk.Canvas(parent, bg=bg, highlightthickness=0)
        vsb = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        inner = UIBuilder.frame(canvas, bg=bg)
        cw = canvas.create_window((0, 0), window=inner, anchor="nw")

        scroller = SmoothScroller(canvas, sensitivity=0.028, friction=0.25)
        state = {"after_id": None}

        def _settle():
            if not canvas.winfo_exists():
                return
            canvas.configure(scrollregion=canvas.bbox("all"))
            state["after_id"] = None

        def _on_mouse_wheel(event):
            if not canvas.winfo_exists():
                return
            if event.num == 4:
                scroller.scroll(120)
            elif event.num == 5:
                scroller.scroll(-120)
            else:
                scroller.scroll(event.delta)

        def _vincular_scroll(widget):
            try:
                widget.bind("<MouseWheel>", _on_mouse_wheel, add="+")
                widget.bind("<Button-4>", _on_mouse_wheel, add="+")
                widget.bind("<Button-5>", _on_mouse_wheel, add="+")
                for child in widget.winfo_children():
                    _vincular_scroll(child)
            except Exception:
                pass

        def _on_inner_configure(_e=None):
            if not canvas.winfo_exists():
                return
            canvas.configure(scrollregion=canvas.bbox("all"))
            _vincular_scroll(inner)
            if state["after_id"]:
                canvas.after_cancel(state["after_id"])
            state["after_id"] = canvas.after(30, _settle)

        inner.bind("<Configure>", _on_inner_configure)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(cw, width=e.width))
        _vincular_scroll(canvas)
        _vincular_scroll(inner)

        return canvas, inner