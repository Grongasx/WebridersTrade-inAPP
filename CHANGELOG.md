# Histórico de Versões - Vale Presente Manager

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
