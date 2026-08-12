# Diretrizes Gerais do Projeto Vale Presente Manager v4.0

Este repositório contém o sistema **Vale Presente Manager v4.0 (PDF Edition)**, uma aplicação desktop Python/Tkinter de alta performance com banco de dados PostgreSQL (Neon) e sistema de impressão de etiquetas em impressoras térmicas (Zebra/PDF).

## Arquitetura do Projeto

```
vale_presente_manager/
├── main.py                  # Ponto de entrada, janela principal App(tk.Tk), rotas e navegação
├── config.py                # Cores globais (Dark Mode + Dourado), fontes e constantes
├── config_local.json        # Configuração local da impressora e modelo de etiqueta
├── core/
│   ├── database.py          # Conexão psycopg com Neon DB, inicialização e migrations de tabelas
│   └── config_local.py      # Gerenciador de leitura/escrita do JSON de configuração local
├── ui/
│   ├── components/          # Widgets Tkinter reutilizáveis (Sidebar, Toast, Loading, UIBuilder)
│   └── screens/             # Telas da aplicação e Popups modais (Dashboard, Clientes, Vales, Outlet, Config)
└── utils/
    ├── formatters.py        # Formatadores dinâmicos de campo (moeda BRL, CPF, Telefone)
    ├── helpers.py           # Funções auxiliares (UUID, validações, creditar_cliente, datetime)
    └── printer.py           # Engine de impressão win32print/PIL (geração de etiquetas 3 colunas, EAN-13)
```

## Regras de Código e Boas Práticas

1. **Persistência PostgreSQL (`psycopg`)**:
   - Use o gerenciador de contexto `get_conn()` de [core/database.py](file:///c:/Users/Latitude/OneDrive/%C3%81rea%20de%20Trabalho/Projetos%20Pessoais/vale_presente_manager/core/database.py) para todas as operações de banco.
   - Sempre utilize parâmetros seguras (`%s`) para evitar SQL Injection.
   - Passe objetos `datetime.datetime` ou `datetime.date` do Python diretamente nos parâmetros de colunas `TIMESTAMP`/`DATE`.
   - Adicione migrações usando `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`.

2. **Interface Gráfica (`Tkinter` / `UIBuilder`)**:
   - Respeite o tema escuro pré-definido em [config.py](file:///c:/Users/Latitude/OneDrive/%C3%81rea%20de%20Trabalho/Projetos%20Pessoais/vale_presente_manager/config.py) (`BG=#1A1A2E`, `BG2=#16213E`, `GOLD=#F5A623`, `ACCENT=#E94560`).
   - Operações assíncronas no banco de dados devem usar `self.app.executar_async(funcao_task, callback_sucesso)` para manter a UI responsiva e exibir o indicador de carregamento.
   - Toda notificação visual deve ser apresentada utilizando `self.app.toast.show(mensagem, tipo)`.

3. **Impressão e Etiquetas**:
   - As etiquetas térmicas (34x22mm por coluna) devem calcular o passo e gap sem acumular erro de arredondamento de pixels (`gerar_imagem_carreira` em [utils/printer.py](file:///c:/Users/Latitude/OneDrive/%C3%81rea%20de%20Trabalho/Projetos%20Pessoais/vale_presente_manager/utils/printer.py)).
   - Toda alteração nas configurações de impressão deve ser salva usando `salvar_config_local()`.

4. **Estilo de Comunicação (Homem das Cavernas)**:
   - Remova palavras de preenchimento. Nada de enrolação.
   - Resposta direta apenas. Frases de 3 a 6 palavras.
   - Direto ao resultado. Sem narrar. Sem explicar além do necessário.

5. **Versionamento e Changelog**:
   - Toda modificação deve atualizar o [CHANGELOG.md](file:///c:/Users/Latitude/OneDrive/%C3%81rea%20de%20Trabalho/Projetos%20Pessoais/vale_presente_manager/CHANGELOG.md).
   - `MAJOR` (`2.0.0`): Mudanças gigantes e estruturais.
   - `MINOR` (`1.1.0`): Atualizações médias e novas funções.
   - `PATCH` (`1.0.1`): Pequenos ajustes e hotfixes.

6. **Fluxo de Git Commit**:
   - Validação com `py_compile` ok $\rightarrow$ atualizar `CHANGELOG.md` $\rightarrow$ executar `git commit`.
