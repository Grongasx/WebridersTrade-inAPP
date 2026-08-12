---
name: pdf-label-printer
description: Gestão do mecanismo de impressão de etiquetas térmicas PDF/Zebra, cálculo de layout 3 colunas, fila de impressão e códigos de barra EAN-13.
---

# Skill: PDF & Thermal Label Printer (`pdf-label-printer`)

Esta skill orienta o gerenciamento e manutenção do sistema de geração de etiquetas, código de barras EAN-13, fila de impressão e comunicação com impressoras térmicas no **Vale Presente Manager**.

## Arquitetura do Sistema de Impressão

O módulo [utils/printer.py](file:///c:/Users/Latitude/OneDrive/%C3%81rea%20de%20Trabalho/Projetos Pessoais/vale_presente_manager/utils/printer.py) gerencia o envio direto de trabalhos de impressão para impressoras no Windows (`win32print`, `win32ui`).

### 1. Leitura de Configurações Locais (`config_local.json`)
As configurações da impressora e especificações físicas das etiquetas são salvas e lidas por [core/config_local.py](file:///c:/Users/Latitude/OneDrive/%C3%81rea%20de%20Trabalho/Projetos Pessoais/vale_presente_manager/core/config_local.py):

```json
{
    "nome_impressora": "Zebra ZD220",
    "etiq_largura_mm": "108",
    "etiq_altura_mm": "25",
    "etiq_por_linha": "3",
    "etiq_indiv_largura_mm": "34",
    "etiq_espaco_colunas_mm": "2",
    "etiq_margem_esq": "2",
    "etiq_margem_dir": "2",
    "etiq_margem_top": "2",
    "etiq_margem_baix": "2"
}
```

### 2. Geração da Imagem da Carreira sem Erro Acumulativo
A função `gerar_imagem_carreira` em `utils/printer.py` calcula o posicionamento horizontal de cada coluna em milímetros antes de converter para pixels:

$$\text{espaco\_gaps\_mm} = \text{w\_tot\_mm} - \text{m\_esq\_mm} - \text{m\_dir\_mm} - (\text{cols} \times \text{w\_indiv\_mm})$$
$$\text{gap\_efetivo\_mm} = \frac{\text{espaco\_gaps\_mm}}{\text{cols} - 1}$$
$$\text{col\_x\_start\_mm} = \text{m\_esq\_mm} + \text{col} \times (\text{w\_indiv\_mm} + \text{gap\_efetivo\_mm})$$

Este cálculo impede desvios horizontais acumulativos ao imprimir tiras de 3 etiquetas acopladas.

### 3. Fila de Impressão e Códigos EAN-13
- Os itens a serem impressos são gravados na tabela `fila_impressao` do banco com `status = 'Pendente'`.
- Durante a execução de `processar_impressao_multi_colunas`:
  1. Cada produto é processado pela função `gerar_e_persistir_ean13(conn, item_id, codigo_atual)`.
  2. A imagem do código de barras EAN-13 é gerada via PIL/python-barcode (`gerar_imagem_ean13`).
  3. Após envio bem sucedido ao DC da impressora (`win32ui.CreateDC`), o status na `fila_impressao` é alterado para `'Impresso'`.

## Verificação e Resolução de Erros de Impressão

1. **Impressora Não Encontrada**:
   - `_obter_impressoras_windows()` em [main.py](file:///c:/Users/Latitude/OneDrive/%C3%81rea%20de%20Trabalho/Projetos%20Pessoais/vale_presente_manager/main.py) lista impressoras disponíveis via `win32print.EnumPrinters` ou PowerShell `Get-Printer`.
   - Se o nome configurado em `config_local.json` não for encontrado nas impressoras do sistema, a aplicação exibe um alerta orientando a seleção na tela de Configurações.

2. **Ajuste de Offsets de Hardware**:
   - As impressoras térmicas possuem margens físicas em hardware. A engine compensa essas diferenças obtendo `PHYSICALOFFSETX` e `PHYSICALOFFSETY` via GDI (`win32con`).

3. **Inclusão de Novos Itens na Fila**:
   - Use `_adicionar_fila_impressao(produto_id)` em `main.py` para enfileirar etiquetas de peças do Outlet.
