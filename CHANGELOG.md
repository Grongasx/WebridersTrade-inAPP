# Histórico de Versões - Vale Presente Manager

## [1.2.0] - 2026-08-12
- Unificação dos popups de cliente (`Detalhe`, `Edição`, `Resgate de Vales` e `Detalhes do Vale`) em uma **única janela popup** baseada em seções dinâmicas em `popup_cliente.py`.
- Eliminação de múltiplas janelas modal sobrepostas.

## [1.1.4] - 2026-08-12
- Adicionado parâmetro `show_global_loading=False` em `executar_async` para evitar que a tela principal esmaecida/carregue ao abrir janelas popup.

## [1.1.3] - 2026-08-12
- Atualização do título da aplicação para **WebRiders TCV**.
- Vinculação dinâmica do subtítulo da barra lateral com a constante de versão do sistema (`config.APP_VERSION`).

## [1.1.2] - 2026-08-12
- Redesign completo da tela e popups de carregamento (`LoadingPopup`, `LoadingOverlay`, `PopupLoadingOverlay`).
- Novo spinner duplo animado em vermelho elétrico (`#FF1E27`), fundo esmaecido (`#070709`) e marca WEBRIDERS.

## [1.1.1] - 2026-08-12
- Correção da rota e rótulo da aba para `etiquetas` em `main.py` e `sidebar.py`.
- Ajuste e limpeza de símbolos/emojis para compatibilidade perfeita no Windows Tkinter.

## [1.1.0] - 2026-08-12
- Redesign completo da interface gráfica para a identidade visual **WEBRIDERS CLUB**.
- Nova paleta Off-Black (`#0D0D10`), Grafite (`#18181C`) e Vermelho Elétrico (`#FF1E27`).
- Atualização do logotipo e barra de navegação para `WEBRIDERS CLUB — Trade-in & Vale Manager`.

## [1.0.4] - 2026-08-12
- Passagem de objeto `date` nativo em `novo_vale_screen.py`.
- Tratamento de exceção genérica no cadastro em `novo_cliente_screen.py`.

## [1.0.3] - 2026-08-12
- Remoção de arquivos confidenciais (`.env`, `vale_presente.db`, `config_local.json`) e diretórios de IA/cache do versionamento Git.
- Adição do modelo seguro `.env.example`.
- Atualização do `.gitignore` para segurança total no GitHub.

## [1.0.2] - 2026-08-12
- Criação da skill `relatorio-feedback` em `.agents/skills/relatorio-feedback/SKILL.md`.
- Atualização das diretrizes de relatório final em `AGENTS.md`.

## [1.0.1] - 2026-08-12
- Remoção do arquivo legado `migrar.py`.
- Limpeza de imports e métodos não utilizados em `main.py`.
- Reindexação do grafo de código.

## [1.0.0] - 2026-08-12
- Lançamento inicial v4.0 PDF Edition.
- Integração PostgreSQL Neon via `psycopg`.
- Interface gráfica escuro e dourado Tkinter.
- Impressão térmica em 3 colunas e EAN-13.
- Cadastro de clientes, vales e outlet.
- Skills e regras de versionamento configuradas.
