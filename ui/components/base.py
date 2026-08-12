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
        
class ScrollableFrame(tk.Frame):
    """Frame com scroll vertical."""
    
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        bg_color = parent.cget("bg")
        self.configure(bg=bg_color)
        self.canvas = tk.Canvas(self, bg=bg_color, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
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
        if event.num == 4: self.canvas.yview_scroll(-1, "units")
        elif event.num == 5: self.canvas.yview_scroll(1, "units")
        else: self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


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
    def button(parent, text, cmd, color=ACCENT, fg=TEXT, width=16, **kw):
        px = kw.pop('padx', 12)
        py = kw.pop('pady', 8)
        return tk.Button(parent, text=text, command=cmd, font=("Segoe UI", 10, "bold"), bg=color, fg=fg, activebackground=color, activeforeground=fg, relief="flat", bd=0, cursor="hand2", padx=px, pady=py, width=width, **kw)
    
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
    def setup_tree_style():
        s = ttk.Style()
        s.theme_use("default")
        s.configure("Dark.Treeview", background=BG2, foreground=TEXT, fieldbackground=BG2, font=FONT_BODY, rowheight=34)
        s.configure("Dark.Treeview.Heading", background=BG3, foreground=GOLD, font=("Segoe UI", 10, "bold"), relief="flat")
        s.map("Dark.Treeview", background=[("selected", BG3)], foreground=[("selected", TEXT)])
    
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
                canvas.yview_scroll(-2, "units")
            elif event.num == 5:
                canvas.yview_scroll(2, "units")
            else:
                delta = int(-1 * (event.delta / 40))
                if delta == 0:
                    delta = -1 if event.delta > 0 else 1
                canvas.yview_scroll(delta, "units")

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