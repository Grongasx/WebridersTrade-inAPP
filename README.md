# ❖ WebRiders TCV — Vale Presente & Outlet Manager

<p align="center">
  <strong>Sistema Desktop de Gestão Comercial, Trade-In, Vales Presente e Impressão Térmica de Etiquetas</strong><br>
  Versão 1.9.0 • Arquitetura Python / Tkinter • PostgreSQL (Neon DB) • Windows GDI / Zebra
</p>

---

## 📌 Sobre o Projeto

O **WebRiders TCV** (Trade-in, Créditos & Vales) é uma aplicação desktop de alta performance desenvolvida especificamente para a operação comercial da WebRiders. O sistema centraliza o controle de clientes, emissão e validação de vales presente, gestão de contas de crédito/trade-in de clientes, catálogo e estoque de produtos de outlet e impressão em tempo real de etiquetas térmicas em 3 colunas padrão EAN-13.

---

## ✨ Principais Funcionalidades

### 1. 📊 Dashboard Operacional em Tempo Real
- Métricas consolidadas: Total de clientes cadastrados, vales ativos, saldo geral de créditos em circulação e faturamento de outlet.
- Cache de alta performance em memória (`MemoryCache`) com sincronização em segundo plano via threads assíncronas.

### 2. 👥 Gestão de Clientes & CRM
- Cadastro ágil de clientes (Nome, CPF, Telefone, WhatsApp, E-mail, Observações).
- Histórico consolidado de vales emitidos, produtos no outlet e saldo financeiro.

### 3. 💳 Créditos, Saldos & Trade-In
- Conta corrente interna por cliente para transações de trade-in e devoluções.
- Extrato financeiro auditável com lançamentos de créditos, débitos e histórico de transações.

### 4. 🏷️ Catálogo & Gestão de Produtos Outlet
- Cadastro de peças com relacionamento hierárquico em cascata: **Tipo $\rightarrow$ Marca $\rightarrow$ Modelo**.
- Busca e filtragem instantânea 100% em memória local (latência zero na digitação).
- Geração automatizada de SKU e códigos de barra internacionais **EAN-13** (prefixo interno `200` com dígito verificador módulo 10).
- Registro de vendas com baixa imediata de estoque e geração de créditos automáticos.

### 5. 🎁 Emissão & Resgate de Vales Presente
- Criação de vales presente com códigos alfanuméricos únicos.
- Definição de prazos de validade e controle de status (*Ativo*, *Utilizado*, *Expirado*).
- Cópia rápida para a área de transferência e geração de comprovantes.

### 6. 🖨️ Motor de Impressão Térmica de Etiquetas (3 Colunas)
- Motor de impressão baseado em **Windows GDI** (`win32print` / `PIL`) para impressoras Zebra e térmicas de alta velocidade.
- Layout de 3 colunas de 34x22mm por etiqueta (largura total 108mm) sem acúmulo de erro de arredondamento de pixels.
- Fila de impressão persistida no banco com suporte a impressão em lote e envio direto.

### 7. 🚀 Atualizações Automáticas Estilo Discord
- Verificação silenciosa de novas versões publicadas no GitHub Releases (`Grongasx/WebridersTrade-inAPP`).
- Botão de notificação integrado na barra superior em verde vibrante (`📥 Atualização vX.Y.Z`).
- Modal integrado para visualização do changelog, download com barra de progresso em tempo real e reinicialização automatizada.

---

## 🛠️ Arquitetura e Tecnologias

- **Linguagem**: Python 3.10+
- **Interface Gráfica**: Tkinter com Design System customizado (Dark Mode Off-Black `#0D0D10` & Vermelho Elétrico `#FF1E27`)
- **Banco de Dados**: PostgreSQL Serverless ([Neon](https://neon.tech)) via driver `psycopg` (v3) com pool de conexões e gerenciador de contexto
- **Concorrência**: Threads assíncronas dedicadas com fallback de sincronização na UI principal (`app.executar_async`)
- **Cache Local**: `MemoryCache` thread-safe (`RLock`) com suporte a TTL e invalidação granular por prefixo
- **Geração de Código de Barras**: `python-barcode` (EAN-13)
- **Empacotamento**: PyInstaller (`--windowed`, `--noconsole`) + Inno Setup 6 (`Setup.exe`)

---

## 📁 Estrutura de Diretórios

```
WebridersTrade-inAPP/
├── main.py                     # Ponto de entrada, janela App(tk.Tk), rotas e navegação
├── config.py                   # Constantes visuais, paleta de cores, fontes e versão global
├── config_local.json           # Configurações de hardware locais (impressora térmica e margens)
├── build_installer.py          # Script de automação de build (PyInstaller + Inno Setup)
├── gerar_instalador.bat        # Script batch para compilação em 1 clique
├── core/
│   ├── database.py             # Conexão psycopg com Neon DB e migrations de schema
│   ├── cache.py                # Implementação singleton do MemoryCache thread-safe
│   └── config_local.py         # Leitura/escrita de configurações locais JSON
├── ui/
│   ├── components/
│   │   ├── base.py             # UIBuilder, ToastNotification, LoadingPopup, ScrollableFrame
│   │   ├── sidebar.py          # Barra lateral de navegação principal
│   │   └── topbar.py           # Barra superior com status online e botão estilo Discord
│   └── screens/
│       ├── base_screen.py      # Classe base para telas do sistema
│       ├── dashboard_screen.py # Dashboard de indicadores
│       ├── clientes_screen.py  # Listagem e busca de clientes
│       ├── novo_cliente_screen.py # Cadastro de clientes
│       ├── creditos_screen.py  # Gestão de saldos e extrato
│       ├── outlet_screen.py    # Listagem de produtos outlet e registro de venda
│       ├── vales_screen.py     # Gestão e resgate de vales
│       ├── novo_vale_screen.py # Emissão de novos vales
│       ├── configuracoes_screen.py # Calibração de impressora, fila e auto-update
│       ├── update_modal.py     # Modal de download e progresso da atualização
│       ├── popup_outlet.py     # Modais de cadastro e edição de produtos outlet
│       └── popup_config.py     # Modais de configuração de margens e fila
└── utils/
    ├── formatters.py           # Formatadores dinâmicos (BRL, CPF, Telefone)
    ├── helpers.py              # EAN-13, SKU, datetime e validações
    ├── printer.py              # Engine de impressão GDI / PIL para etiquetas 3 colunas
    └── updater.py              # Consulta GitHub Releases API, streaming e execução do instalador
```

---

## 🚀 Instalação e Execução Local

### Pré-requisitos
- Python 3.10 ou superior instalado no Windows.
- Acesso à internet para conexão com o banco Neon PostgreSQL.

### Passo a Passo

1. **Clonar o Repositório**:
   ```bash
   git clone https://github.com/Grongasx/WebridersTrade-inAPP.git
   cd WebridersTrade-inAPP
   ```

2. **Criar e Ativar Ambiente Virtual**:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Instalar Dependências**:
   ```bash
   pip install psycopg[binary] pillow pywin32 python-barcode tkcalendar python-dotenv babel pyinstaller
   ```

4. **Configurar o Arquivo de Credenciais (`.env`)**:
   Copie o modelo de exemplo e adicione a string de conexão com o banco Neon PostgreSQL:
   ```bash
   copy .env.example .env
   ```
   Edite o `.env`:
   ```ini
   DATABASE="postgresql://usuario:senha@ep-exemplo.us-east-2.aws.neon.tech/neondb?sslmode=require"
   ```

5. **Executar o Sistema**:
   ```bash
   python main.py
   ```

---

## 📦 Gerando o Instalador Executável (`.exe`)

Para gerar o pacote de distribuição autônomo com PyInstaller e instalador do Inno Setup:

```bash
python build_installer.py
```
*Ou simplesmente execute com dois cliques o arquivo `gerar_instalador.bat`.*

O build criará:
- `dist/ValePresenteManager/`: Pasta contendo o executável `.exe`, `.env`, assets e dependências empacotadas.
- `dist/ValePresenteManager_v1.9.0_Instalador_Completo.zip`: Pacote ZIP pronto para envio.
- `dist/ValePresenteManager_v1.9.0_Setup.exe`: Instalador com assistente do Windows (se o Inno Setup estiver instalado).

---

## 📄 Licença e Uso

Propriedade privada de **WebRiders Club**. Todos os direitos reservados.
