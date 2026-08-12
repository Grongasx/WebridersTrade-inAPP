---
name: db-manager
description: Gerenciamento do banco de dados PostgreSQL (Neon), conexões psycopg, migrações de tabelas e transações do Vale Presente Manager.
---

# Skill: Database Manager (`db-manager`)

Esta skill fornece instruções e padrões para gerenciar a camada de persistência de dados PostgreSQL (Neon) no projeto **Vale Presente Manager**.

## Estrutura das Tabelas

O banco de dados opera com as seguintes tabelas operacionais em [core/database.py](file:///c:/Users/Latitude/OneDrive/%C3%81rea%20de%20Trabalho/Projetos%20Pessoais/vale_presente_manager/core/database.py):

1. **`clientes`**:
   - `id BIGSERIAL PRIMARY KEY`
   - `nome VARCHAR(255) NOT NULL`, `cpf VARCHAR(14)`, `telefone VARCHAR(20)`, `email VARCHAR(255)`
   - `saldo NUMERIC(10, 2) DEFAULT 0.00`, `criado TIMESTAMP DEFAULT CURRENT_TIMESTAMP`

2. **`vales`**:
   - `id BIGSERIAL PRIMARY KEY`
   - `codigo VARCHAR(50) UNIQUE NOT NULL` (formato `VP-XXXX-XXXX`)
   - `cliente_id BIGINT REFERENCES clientes(id) ON DELETE SET NULL`
   - `valor NUMERIC(10, 2) NOT NULL`, `usado INT DEFAULT 0`, `validade DATE`
   - `criado TIMESTAMP`, `usado_em TIMESTAMP`, `observacao TEXT`

3. **`historico_credito`**:
   - `id BIGSERIAL PRIMARY KEY`
   - `cliente_id BIGINT REFERENCES clientes(id) ON DELETE CASCADE`
   - `valor NUMERIC(10, 2) NOT NULL`, `tipo VARCHAR(50)` ('outlet', 'vale', 'manual')
   - `descricao TEXT`, `motivo TEXT`, `criado TIMESTAMP`

4. **`produtos_outlet`**:
   - `id BIGSERIAL PRIMARY KEY`
   - `nome VARCHAR(255)`, `codigo_barras VARCHAR(100) UNIQUE` (EAN-13)
   - `preco_original NUMERIC`, `preco_outlet NUMERIC`, `defeito TEXT`
   - `cliente_id BIGINT REFERENCES clientes(id)`, `marca VARCHAR(100)`, `tamanho VARCHAR(50)`, `estoque INT`

5. **`vendas_outlet`**:
   - `id BIGSERIAL PRIMARY KEY`
   - `cliente_id BIGINT`, `produto_id BIGINT`, `quantidade INT`, `preco_pago NUMERIC`

6. **`fila_impressao`**:
   - `id BIGSERIAL PRIMARY KEY`
   - `produto_id BIGINT REFERENCES produtos_outlet(id) ON DELETE CASCADE`
   - `texto_etiqueta TEXT` (JSON string com dados da etiqueta), `status VARCHAR(50)` ('Pendente', 'Impresso')

## Diretrizes de Código para Banco de Dados

### 1. Gerenciamento de Conexão
Sempre utilize o gerenciador de contexto `get_conn()`:

```python
from core.database import get_conn

with get_conn() as conn:
    resultado = conn.execute(
        "SELECT id, nome, saldo FROM clientes WHERE id = %s;", 
        (cliente_id,)
    ).fetchone()
```

### 2. Transações e Commits
Ao realizar mutações (`INSERT`, `UPDATE`, `DELETE`), certifique-se de executar `conn.commit()`:

```python
with get_conn() as conn:
    conn.execute(
        "UPDATE clientes SET saldo = saldo + %s WHERE id = %s;",
        (valor, cliente_id)
    )
    conn.commit()
```

### 3. Migrações Seguras
Ao adicionar novos campos ou tabelas, altere a função `init_db()` em [core/database.py](file:///c:/Users/Latitude/OneDrive/%C3%81rea%20de%20Trabalho/Projetos%20Pessoais/vale_presente_manager/core/database.py) mantendo comandos idempotentes (`CREATE TABLE IF NOT EXISTS` e `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`).

### 4. Tipos de Dados Python vs PostgreSQL
- **Datas/Horas**: Passe objetos `datetime.datetime` ou `datetime.date` (utilizando as funções `agora()` e `hoje()` de [utils/helpers.py](file:///c:/Users/Latitude/OneDrive/%C3%81rea%20de%20Trabalho/Projetos%20Pessoais/vale_presente_manager/utils/helpers.py)) nos parâmetros `%s`.
- **Valores Monotários**: Trabalhe com `float` ou `Decimal` no Python, que são mapeados para `NUMERIC(10, 2)`.

### 5. Função Utilitária `creditar_cliente`
Para registrar créditos de vendas ou vales resgatados, use a função auxiliar unificada:

```python
from utils.helpers import creditar_cliente

# Dentro de uma transação existente
creditar_cliente(cliente_id, valor, tipo="vale", motivo="Resgate Vale VP-1234", conn=conn)

# Ou independente (commita automaticamente)
creditar_cliente(cliente_id, valor, tipo="outlet", motivo="Venda Peça Outlet")
```
