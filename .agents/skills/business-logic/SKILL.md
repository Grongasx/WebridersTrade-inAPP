---
name: business-logic
description: Regras de negócio, formatação de moedas/CPF, emissão e validação de Vales Presente, controle de saldo e peças de Outlet.
---

# Skill: Business Logic & Rules (`business-logic`)

Esta skill sintetiza e orienta a manutenção de todas as regras de negócio, utilitários e validações do **Vale Presente Manager**.

## Módulos Principais

As regras de negócio e funções auxiliares encontram-se nos seguintes módulos:
- [utils/helpers.py](file:///c:/Users/Latitude/OneDrive/%C3%81rea%20de%20Trabalho/Projetos%20Pessoais/vale_presente_manager/utils/helpers.py)
- [utils/formatters.py](file:///c:/Users/Latitude/OneDrive/%C3%81rea%20de%20Trabalho/Projetos%20Pessoais/vale_presente_manager/utils/formatters.py)

---

## Regras de Negócio e Validações

### 1. Gestão de Vales Presente (`vales`)
- **Geração de Código Único**: `gerar_codigo()` produz uma string no formato `VP-XXXX-XXXX` usando `uuid.uuid4()`.
- **Validade**: A verificação `vencido(validade)` compara a data de expiração (objeto `date`, `datetime` ou string ISO) com `datetime.date.today()`.
- **Status do Vale**:
  - `usado == 0` e não vencido $\rightarrow$ **Ativo**
  - `usado == 1` $\rightarrow$ **Utilizado**
  - `usado == 0` e `vencido(validade) == True` $\rightarrow$ **Vencido**
- **Resgate**: Ao resgatar um vale presente, a flag `usado` é alterada para `1`, grava-se a data/hora em `usado_em`, e o valor do vale é creditado na conta do cliente via `creditar_cliente(cliente_id, valor, tipo='vale', ...)` em [utils/helpers.py](file:///c:/Users/Latitude/OneDrive/%C3%81rea%20de%20Trabalho/Projetos%20Pessoais/vale_presente_manager/utils/helpers.py).

### 2. Controle de Saldo e Histórico do Cliente
- O saldo do cliente (`clientes.saldo`) acumula créditos de vales resgatados e devoluções/vendas de peças Outlet.
- Toda movimentação deve registrar uma entrada em `historico_credito` contendo:
  - `cliente_id`: ID do cliente beneficiado
  - `valor`: Quantia numérica
  - `tipo`: Origem (`'outlet'`, `'vale'`, ou `'manual'`)
  - `motivo`: Descrição humana amigável

### 3. Gestão de Outlet (`produtos_outlet` / `vendas_outlet`)
- Produtos possuem `preco_original`, `preco_outlet`, `defeito`, `marca`, `tamanho` e um cliente consignador (`cliente_id`).
- Ao vender um produto outlet, a venda é registrada em `vendas_outlet`, o estoque é decrementado, e o crédito correspondente é adicionado ao saldo do cliente consignador.

### 4. Validações e Formatadores
- **CPF**: `validar_cpf(cpf)` executa a verificação dos dígitos verificadores módulo 11. `formatar_cpf(texto)` aplica a máscara `000.000.000-00`.
- **Telefone**: `formatar_telefone(texto)` aplica máscaras para fixo `(00) 0000-0000` ou celular `(00) 00000-0000`.
- **Validação de Email**: `validar_email(email)` executa validação por expressão regular.
- **Moeda BRL**: `brl(valor)` converte `float` em string formatada `R$ X.XXX,XX`. `txt_para_float(texto)` limpa e converte strings de entradas do usuário para `float`.
- **`CurrencyFormatter`**: Classe em [utils/formatters.py](file:///c:/Users/Latitude/OneDrive/%C3%81rea%20de%20Trabalho/Projetos%20Pessoais/vale_presente_manager/utils/formatters.py) para formatação dinâmica de campos `tk.Entry` enquanto o usuário digita.
