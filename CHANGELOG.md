# Histórico de Versões - Vale Presente Manager

## [1.8.0] - 2026-08-18
- Estrutura hierárquica em cascata Tipo -> Marca -> Modelo, ícone customizado `tcv.ico` e limpeza integral do banco ([build_installer.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/build_installer.py), [main.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/main.py), [ui/screens/popup_outlet.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/ui/screens/popup_outlet.py), [core/database.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/core/database.py), [utils/helpers.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/utils/helpers.py)):
  - Criação da tabela `catalogo_produtos` para gerenciar relacionamentos em cascata Tipo $\rightarrow$ Marca $\rightarrow$ Modelo com índices de busca otimizados.
  - Implementação de comboboxes reativos no formulário de cadastro: ao escolher ou digitar um Tipo, o campo Marca filtra dinamicamente suas marcas associadas; ao escolher uma Marca, o campo Modelo filtra dinamicamente seus modelos.
  - Salvamento automático de novas combinações de Tipo/Marca/Modelo na hierarquia do catálogo durante o cadastro de produtos.
  - Limpeza integral de todas as tabelas operacionais do Neon PostgreSQL (`TRUNCATE TABLE fila_impressao, vendas_outlet, produtos_outlet, historico_credito, vales, clientes, catalogo_produtos CASCADE`).
  - Definição do ícone executável `.exe` e da janela principal com `assets/ico/tcv.ico`.
  - Atualização do cálculo dinâmico de SKU em `calcular_sku` para suportar qualquer categoria customizada.
  - Recompilação completa do pacote executável e instalador ZIP em `dist/`.

## [1.7.6] - 2026-08-18
- Eliminação do desvio acumulativo nas colunas e geração do pacote final de distribuição ([utils/printer.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/utils/printer.py), [core/config_local.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/core/config_local.py), [config_local.json](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/config_local.json), [ui/screens/popup_config.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/ui/screens/popup_config.py)):
  - Posicionamento estrito das 3 colunas individuais em `34.0 mm` com margem esquerda inicial de `2.0 mm` e gap zero, eliminando o estiramento artificial e o desvio da última coluna para fora do papel.
  - Compilação concluída do pacote instalador ZIP e executável prontos para envio em `dist/`.

## [1.7.5] - 2026-08-18
- Margens laterais aplicadas estritamente na fileira total ([utils/printer.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/utils/printer.py), [ui/screens/popup_config.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/ui/screens/popup_config.py)):
  - As margens esquerda e direita agora atuam exclusivamente nos limites da tira/fileira total, eliminando qualquer espaçamento ou recuo entre as colunas individuais de etiquetas.
  - Recompilação automática do pacote executável e instalador em `dist/`.

## [1.7.4] - 2026-08-18
- Gap entre colunas zerado (`0.0 mm`) e largura contígua de 36.0 mm ([config_local.json](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/config_local.json), [core/config_local.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/core/config_local.py), [ui/screens/popup_config.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/ui/screens/popup_config.py)):
  - Configuração de `etiq_espaco_colunas_mm = 0.0 mm` e `etiq_indiv_largura_mm = 36.0 mm` (`3 x 36.0 mm = 108.0 mm`), eliminando qualquer espaçamento intermediário entre as colunas de impressão.
  - Recompilação automática do pacote executável em `dist/`.

## [1.7.3] - 2026-08-18
- Expansão forçada de impressão para 108.0 mm via DEVMODE em memória ([utils/printer.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/utils/printer.py), [config_local.json](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/config_local.json), [core/config_local.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/core/config_local.py), [ui/screens/popup_config.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/ui/screens/popup_config.py)):
  - Injeção de estrutura `DEVMODE` customizada em memória (`PaperWidth = 1080`, `PaperLength = 250`, `PaperSize = 0`) no Device Context da impressora Windows, expandindo a largura de impressão para 108.0 mm sem modificar as preferências globais do Windows.
  - Renderização das 3 colunas de 34.0 mm preenchendo toda a cabeça de impressão de 108.0 mm com margem esquerda zerada.
  - Recompilação do pacote executável e instalador em `dist/`.

## [1.7.2] - 2026-08-18
- Padronização de dimensões 76.20 x 59.80 mm e eliminação do gap da extremidade esquerda ([config_local.json](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/config_local.json), [core/config_local.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/core/config_local.py), [utils/printer.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/utils/printer.py), [ui/screens/popup_config.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/ui/screens/popup_config.py)):
  - Ajuste de `etiq_margem_esq` para `0.0 mm` e `etiq_margem_dir` para `0.0 mm`.
  - Ampliação da largura individual das 3 colunas para `24.4 mm` (`etiq_indiv_largura_mm`) com gap de `1.5 mm` (`etiq_espaco_colunas_mm`), preenchendo com precisão a largura total de `76.20 mm`.
  - Recompilação automática do pacote executável e instalador ZIP em `dist/`.
  - Documentação da calibração na seção 1.7 da skill [problem-troubleshooting](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/.agents/skills/problem-troubleshooting/SKILL.md).

## [1.7.0] - 2026-08-18
- Gerador de Instalador automatizado com empacotamento seguro de `.env` e proteção Git ([build_installer.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/build_installer.py), [gerar_instalador.bat](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/gerar_instalador.bat), [core/database.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/core/database.py), [core/config_local.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/core/config_local.py), [.gitignore](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/.gitignore), [.env.example](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/.env.example)):
  - Criação do script [build_installer.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/build_installer.py) e inicializador em lote [gerar_instalador.bat](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/gerar_instalador.bat) para compilação PyInstaller (`--windowed`, `--noconsole`).
  - Suporte completo a execução congelada (`sys.frozen`), carregando o arquivo `.env` e `config_local.json` dinamicamente a partir da pasta do `.exe`.
  - Cópia e empacotamento automático do arquivo `.env` e `config_local.json` ativos dentro da pasta distribuível `dist/ValePresenteManager/` e no pacote ZIP de 1 clique.
  - Geração de script do Inno Setup (`installer.iss`) para compilação de instalador executável `Setup.exe`.
  - Atualização estrita do [.gitignore](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/.gitignore) e criação do [.env.example](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/.env.example) para blindagem completa contra vazamento de credenciais em repositórios públicos.

## [1.6.1] - 2026-08-18
- Otimização da busca dinâmica na aba de impressão e correção de importação ([ui/screens/popup_config.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/ui/screens/popup_config.py), [ui/screens/outlet_screen.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/ui/screens/outlet_screen.py)):
  - Eliminação de consultas SQL repetidas a cada tecla no modal de adicionar produtos para impressão (`PopupAddProduto`), substituindo por carregamento único em memória e filtragem instantânea via `MemoryCache`.
  - Correção de `NameError: name 'ACCENT' is not defined` no botão de impressão direta de `OutletScreen`.
  - Documentação da solução na seção 1.6 da skill [problem-troubleshooting](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/.agents/skills/problem-troubleshooting/SKILL.md).

## [1.6.0] - 2026-08-18
- Implementação de **MemoryCache** global thread-safe e desativação temporária da aba Exportar Dados ([core/cache.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/core/cache.py), [main.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/main.py), [ui/components/sidebar.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/ui/components/sidebar.py), [ui/screens/dashboard_screen.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/ui/screens/dashboard_screen.py), [ui/screens/clientes_screen.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/ui/screens/clientes_screen.py), [ui/screens/creditos_screen.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/ui/screens/creditos_screen.py), [ui/screens/outlet_screen.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/ui/screens/outlet_screen.py), [ui/screens/vales_screen.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/ui/screens/vales_screen.py), [ui/screens/configuracoes_screen.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/ui/screens/configuracoes_screen.py)):
  - Criação do módulo [core/cache.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/core/cache.py) com a classe `MemoryCache`, suporte a TTL, sincronização thread-safe com `RLock` e invalidação granular por prefixo (`invalidate_prefix`).
  - Cacheamento de consultas e métricas pesadas do Dashboard, Clientes, Créditos, Outlet, Vales e Fila de Impressão, tornando a navegação instantânea.
  - Invalidação automática e reativa em todas as rotinas de escrita (`INSERT`, `UPDATE`, `DELETE`, vendas, baixas e emissões).
  - Desativação temporária da aba **Exportar Dados** via comentário no menu da [Sidebar](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/ui/components/sidebar.py) e rotas do [main.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/main.py).
  - Documentação da arquitetura e diagnóstico na seção 1.5 da skill [problem-troubleshooting](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/.agents/skills/problem-troubleshooting/SKILL.md).

## [1.5.0] - 2026-08-18
- Persistência obrigatória do código **EAN-13** no PostgreSQL e impressão direta a partir do banco de dados ([core/database.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/core/database.py), [utils/printer.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/utils/printer.py), [utils/helpers.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/utils/helpers.py), [ui/screens/outlet_screen.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/ui/screens/outlet_screen.py), [ui/screens/popup_outlet.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/ui/screens/popup_outlet.py), [ui/screens/popup_config.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/ui/screens/popup_config.py), [main.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/main.py)):
  - Migração em `init_db()` para popular a coluna `codigo_barras` com EAN-13 válido (13 dígitos numéricos) em todos os registros legados da tabela `produtos_outlet`.
  - Criação de índices de busca rápida `idx_produtos_outlet_codigo_barras` e `idx_produtos_outlet_sku`.
  - Implementação de `imprimir_produtos_direto` em [utils/printer.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/utils/printer.py) para impressão de etiquetas diretamente dos dados persistidos no PostgreSQL, com histórico registrado na `fila_impressao`.
  - Adição do botão **"🖨️ Imprimir Etiqueta"** e modal de quantidade na tela `OutletScreen`, exibindo a coluna `EAN-13` na listagem de produtos.
  - Sincronização do código EAN-13 em `PopupAddProduto` e `PopupEditarEtiqueta`.
  - Documentação da arquitetura e diagnóstico na seção 1.4 da skill [problem-troubleshooting](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/.agents/skills/problem-troubleshooting/SKILL.md).

## [1.4.4] - 2026-08-17
- Padronização de notificações visuais Toast e resolução de erro estático `NoneType` ([ui/screens/configuracoes_screen.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/ui/screens/configuracoes_screen.py), [ui/screens/outlet_screen.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/ui/screens/outlet_screen.py), [ui/screens/novo_vale_screen.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/ui/screens/novo_vale_screen.py), [ui/screens/novo_cliente_screen.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/ui/screens/novo_cliente_screen.py), [ui/screens/creditos_screen.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/ui/screens/creditos_screen.py), [ui/screens/clientes_screen.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/ui/screens/clientes_screen.py)):
  - Substituição de chamadas `self.toast.show(...)` por `self.app.toast.show(...)`, eliminando o erro de atributo de `NoneType` do analisador estático.
  - Correção de referência de callback `_ao_excluir_sucesso` na exclusão assíncrona de clientes.
  - Documentação da resolução na seção 2.5 da skill [problem-troubleshooting](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/.agents/skills/problem-troubleshooting/SKILL.md).

## [1.4.3] - 2026-08-17
- Correção de tipagem em chamada de função ([ui/screens/popup_config.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/ui/screens/popup_config.py)):
  - Conversão explícita de `data["texto"]` para `str` na chamada `gerar_imagem_ean13(str(data["texto"]), ...)`, eliminando falso positivo de união de tipos `float | int | str` do verificador estático.
  - Declaração explícita de `self.layout_elementos: Dict[str, Dict[str, Any]]`.
  - Documentação da resolução na skill [problem-troubleshooting](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/.agents/skills/problem-troubleshooting/SKILL.md).

## [1.4.2] - 2026-08-17
- Correção de tipagem estática no Designer Visual ([ui/screens/popup_config.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/ui/screens/popup_config.py)):
  - Declaração explícita de `self._drag_data: Dict[str, Any]` em `PopupConfigDimensoes` para evitar inferência restritiva `dict[str, int | None]` do Pyright/Pylance.
  - Catalogação da solução na skill [problem-troubleshooting](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/.agents/skills/problem-troubleshooting/SKILL.md).

## [1.4.1] - 2026-08-17
- Migração e geração de códigos de barra para o padrão internacional **EAN-13** ([utils/helpers.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/utils/helpers.py), [utils/printer.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/utils/printer.py), [ui/screens/popup_outlet.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/ui/screens/popup_outlet.py), [main.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/main.py)):
  - Substituição da renderização Code39 por gerador oficial EAN-13 numérico com cálculo de dígito verificador (módulo 10).
  - Inclusão de margens de silêncio (quiet zones) e barras de guarda estendidas para leitura instantânea em leitores óticos e scanners Zebra/Honeywell/Elgin.
  - Persistência e garantia de EAN-13 no cadastro de novos produtos outlet e na fila de impressão.
  - Atualização do catálogo de diagnósticos na skill [problem-troubleshooting](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/.agents/skills/problem-troubleshooting/SKILL.md).

## [1.4.0] - 2026-08-17
- Reformulação da tela de Etiquetas e Fila de Impressão ([ui/screens/configuracoes_screen.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/ui/screens/configuracoes_screen.py), [ui/screens/popup_config.py](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/ui/screens/popup_config.py)):
  - Exibição do ID do produto na coluna principal da Treeview da fila em vez do ID de impressão.
  - Implementação de modal avançado `PopupAddProduto` com barra de pesquisa dinâmica por ID, Nome, Marca, Modelo, Dono ou SKU.
  - Renomeação do botão de inserção para `"➕ Add Produto"`.
  - Renomeação do botão de exclusão para `"🗑️ Excluir"`.
  - Adição de seletores numéricos (Spinbox/stepper com setas `➕`/`➖`) com validação de quantidade manual restrita a $x \ge 1$.
  - Suporte a edição individual com ajuste de cópias em `PopupEditarEtiqueta`.

## [1.3.15] - 2026-08-17
- Criação da skill de diagnóstico e troubleshooting [problem-troubleshooting](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/.agents/skills/problem-troubleshooting/SKILL.md):
  - Catalogação de erros frequentes e resoluções (banco Neon/psycopg, tipagem estática Pyright/win32, driver de impressão GDI e concorrência Tkinter).
  - Atualização do [AGENTS.md](file:///c:/Users/Windows/Desktop/vale_presente_manager/WebridersTrade-inAPP-1/.agents/AGENTS.md) com diretriz contínua de documentação de novas soluções e problemas.

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
