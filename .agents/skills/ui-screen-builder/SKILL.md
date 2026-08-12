---
name: ui-screen-builder
description: Padrões de desenvolvimento de interface Tkinter, construtor de componentes, navegação, popups modais e concorrência assíncrona.
---

# Skill: UI Screen Builder (`ui-screen-builder`)

Esta skill fornece orientações e padrões de código para criar e modificar telas, popups e componentes de interface no **Vale Presente Manager**.

## Sistema de Design (Cores e Fontes)

Todas as cores e fontes estão centralizadas em [config.py](file:///c:/Users/Latitude/OneDrive/%C3%81rea%20de%20Trabalho/Projetos%20Pessoais/vale_presente_manager/config.py). Nunca utilize cores hexadecimais "hardcoded" nas telas; import as constantes:

- **Fundo Principal**: `BG` (`#1A1A2E`)
- **Fundo Secundário/Cards**: `BG2` (`#16213E`)
- **Fundo de Destaque**: `BG3` (`#0F3460`)
- **Acento / Destaque**: `GOLD` (`#F5A623`) e `ACCENT` (`#E94560`)
- **Texto**: `TEXT` (`#EAEAEA`) e `TEXT_DIM` (`#8A8FA8`)
- **Status**: `SUCCESS` (`#4CAF50`), `WARNING` (`#FF9800`), `DANGER` (`#E94560`)
- **Fontes**: `FONT_TITLE`, `FONT_H2`, `FONT_BODY`, `FONT_SMALL`, `FONT_MONO`, `FONT_CODE`

## Estrutura de Uma Tela (`BaseScreen`)

Telas do sistema herdam de `BaseScreen` (em [ui/screens/base_screen.py](file:///c:/Users/Latitude/OneDrive/%C3%81rea%20de%20Trabalho/Projetos%20Pessoais/vale_presente_manager/ui/screens/base_screen.py)) ou implementam a seguinte interface básica:

```python
import tkinter as tk
from config import BG, BG2, GOLD, TEXT, FONT_TITLE, FONT_BODY
from ui.components.base import UIBuilder

class ExemploScreen:
    def __init__(self, app, content):
        self.app = app
        self.content = content
        self.frame = None

    def show(self, **kwargs):
        """Renderiza e exibe a tela no container de conteúdo principal."""
        if self.frame:
            self.frame.destroy()

        self.frame = UIBuilder.frame(self.content, bg=BG)
        self.frame.pack(fill="both", expand=True, px=20, py=20)

        # Título da tela
        UIBuilder.label(self.frame, "Título da Tela", font=FONT_TITLE, fg=GOLD).pack(anchor="w", pady=(0, 20))

        # Carregamento assíncrono de dados
        self._carregar_dados()

    def _carregar_dados(self):
        def task():
            # Consulta pesada no banco
            with get_conn() as conn:
                return conn.execute("SELECT ...").fetchall()

        def on_sucesso(dados):
            # Atualiza widgets na Thread Principal do Tkinter
            self._renderizar_tabela(dados)

        self.app.executar_async(task, callback_sucesso=on_sucesso, mensagem="Carregando dados...")
```

## Componentes Utilitários (`UIBuilder`)

O arquivo [ui/components/base.py](file:///c:/Users/Latitude/OneDrive/%C3%81rea%20de%20Trabalho/Projetos%20Pessoais/vale_presente_manager/ui/components/base.py) disponibiliza ajudantes estáticos para rápida instanciação de widgets padronizados:

- `UIBuilder.frame(parent, bg)`: Cria container estilizado.
- `UIBuilder.button(parent, text, command, bg, fg)`: Botão com efeito hover automático.
- `UIBuilder.entry(parent, width, justify)`: Input de texto com fundo escuro e borda fina.
- `UIBuilder.setup_tree_style()`: Estilização global dos componentes `ttk.Treeview`.

## Popups e Modais Escurecidos

Janelas popup devem estender `ModalWindow` ou seguir o padrão visual overlay:

1. Importar `ModalWindow` de `ui.components.base`.
2. Definir dimensões e título centralizado.
3. Notificar o usuário usando `self.app.toast.show("Operação concluída!", "sucesso")`.

## Registro e Navegação no `main.py`

Para adicionar uma nova tela ao sistema:
1. Adicione a instância da tela em `_register_screens()` no arquivo [main.py](file:///c:/Users/Latitude/OneDrive/%C3%81rea%20de%20Trabalho/Projetos%20Pessoais/vale_presente_manager/main.py).
2. Adicione o botão correspondente no componente [ui/components/sidebar.py](file:///c:/Users/Latitude/OneDrive/%C3%81rea%20de%20Trabalho/Projetos%20Pessoais/vale_presente_manager/ui/components/sidebar.py).
