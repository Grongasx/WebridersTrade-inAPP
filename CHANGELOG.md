# Histórico de Versões - Vale Presente Manager

## [1.3.14] - 2026-08-17
- Correção de tipagem em [utils/printer.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/utils/printer.py):
  - Adição de validação explícita de `ImageWin` na checagem de módulos em `imprimir_etiquetas_direto`.
  - Uso de `cast(Any, ImageWin).Dib(img_carreira)` para evitar falso positivo do analisador estático quando `ImageWin` é importado condicionalmente.

## [1.3.13] - 2026-08-17
- Correção de tipagem em [utils/printer.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/utils/printer.py): uso de `cast(Any, hdc).StartDoc(...)` para suprimir falso positivo do stub `_win32typing.PyCDC.StartDoc`.

## [1.3.12] - 2026-08-17
- Correção de assinatura em [utils/printer.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/utils/printer.py): remoção do argumento `None` em `hdc.StartDoc("Impressao_Etiquetas_Outlet")` para satisfazer o verificador estático de tipos.

## [1.3.11] - 2026-08-17
- Correção de assinatura em [utils/printer.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/utils/printer.py):
  - Adição explícita do parâmetro `outputFile=None` na chamada `hdc.StartDoc("Impressao_Etiquetas_Outlet", None)` em conformidade com o stub de tipagem `PyCDC.StartDoc`.

## [1.3.10] - 2026-08-17
- Correção de tipagem em [utils/printer.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/utils/printer.py):
  - Aplicação de `cast(Any, None)` no parâmetro `InitData` de `win32gui.CreateDC` para compatibilidade com o stub `PyDEVMODEW` do Pyright/Pylance.

## [1.3.9] - 2026-08-17
- Correção de criação de Device Context (DC) de impressora em [utils/printer.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/utils/printer.py):
  - Resolução do erro `NoneType has no attribute 'CreatePrinterDC'` quando `win32ui.CreateDC()` retorna `None`.
  - Implementação de fallback resiliente via GDI nativo com `win32gui.CreateDC("WINSPOOL", ...)` e `win32ui.CreateDCFromHandle()`.
  - Tratamento seguro de desalocação (`DeleteDC`) no bloco `finally`.

## [1.3.8] - 2026-08-17
- Refatoração do módulo de impressão [utils/printer.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/utils/printer.py):
  - Remoção de acoplamento indevido (`from ui.screens.popup_config import gerar_e_persistir_ean13`).
  - Suporte e preservação nativa de SKUs internos inteligentes e códigos Code39 para etiquetas sem sobrescrever dados no banco.
  - Atualização em lote de status na tabela `fila_impressao` via `WHERE id = ANY(%s)`.
  - Tratamento aprimorado de quebra de linhas multi-parágrafos em `_aplicar_quebra_de_linha`.
  - Tratamento seguro de exceções e fallbacks caso os módulos Win32/PIL estejam ausentes.

## [1.3.7] - 2026-08-17
- Refatoração de migrações DDL em [core/database.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/core/database.py): substituição de loops dinâmicos com `sql.SQL()` por instruções DDL diretas (`ALTER TABLE ... ADD COLUMN IF NOT EXISTS`) em bloco único com `LiteralString`.
- Resolução do erro de verificação de tipos (`Argument str is not assignable to parameter obj with type LiteralString in function psycopg.sql.SQL.__init__`).
- Redução de latência de rede no Neon DB consolidando 18 queries individuais em 2 transações diretas.

## [1.3.6] - 2026-08-17
- Correção de tipagem e segurança em `core/database.py`: migração das queries DDL dinâmicas (`ALTER TABLE ... ADD COLUMN IF NOT EXISTS`) de f-strings para composição segura com `psycopg.sql` (`sql.SQL` e `sql.Identifier`).
- Resolução do erro de sobrecarga de tipo no Pyright/psycopg 3 (`Argument str is not assignable to parameter query with type LiteralString | Composed | SQL | bytes`).
- Otimização da consulta de fila de impressão em `utils/printer.py` para operador parametrizado nativo `WHERE id = ANY(%s)`.

## [1.3.5] - 2026-08-17
- Correção de migração de esquema no PostgreSQL: adição automática das colunas faltantes (`motivo`, `descricao`, `tipo`, `valor`) na tabela `historico_credito` via `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` em `core/database.py`.
- Resolução do erro `column "motivo" of relation "historico_credito" does not exist` durante o resgate de vales presente e lançamentos de crédito.

## [1.3.4] - 2026-08-13
- Validação de configuração de credenciais Git do usuário `grongasx` (`gustavinihb12@gmail.com`).

## [1.3.3] - 2026-08-12
- Redesign completo e estilização escura dos menus suspensos (`ttk.Combobox` e `Popdown Listbox`) em `base.py` alinhados com o tema visual **WEBRIDERS CLUB** (grafite `#18181C`, vermelho elétrico `#FF1E27` e seta personalizada).

## [1.3.2] - 2026-08-12
- Otimização de alta performance na digitação de valores em `CurrencyFormatter` (`formatters.py`) e `novo_vale_screen.py` evitando delete/insert redundantes.
- Tornada a geração de SKU determinística em `helpers.py` (remoção de `time.time()`), eliminando completamente o lag e recálculo infinito ao digitar atributos de produto.

## [1.3.1] - 2026-08-12
- Correção do erro de expressão regular (`re.PatternError: bad character range`) em `calcular_sku` em `helpers.py`.
- Reformulação do mecanismo de scroll vertical com mousewheel em `base.py` (`ScrollableFrame` e `scrolled_canvas`) para rolagem fluida e sem perda de foco.

## [1.3.0] - 2026-08-12
- Migração completa do cadastro de produtos outlet: remoção do EAN-13 e implementação do **SKU interno inteligente** (`calcular_sku`).
- Adição das colunas `sku`, `tipo`, `marca`, `modelo`, `grafico` (opcional/null), `cor`, `numeracao`, `quantidade` e `valor_sugerido` no PostgreSQL.
- Menu suspenso de numeração/tamanho categorizado dinamicamente pelo `Tipo` de produto.
- Renderizador Code39 em imagens PIL para código de barras de etiquetas térmicas a partir do SKU.

## [1.2.1] - 2026-08-12
- Correção do indicador de carregamento e parâmetro `show_global_loading=False` no resgate de vale presente em `vales_screen.py`.

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
