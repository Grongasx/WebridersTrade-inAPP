"""
Módulo de conexão e inicialização do banco de dados PostgreSQL (Neon).
"""

import os
import psycopg
from contextlib import contextmanager
from dotenv import load_dotenv

# Carrega as variáveis definidas no arquivo .env
load_dotenv()

# Obtém a string de conexão da chave DATABASE (ou DATABASE_URL) do .env
DB_URL = os.getenv("DATABASE") or os.getenv("DATABASE_URL")


@contextmanager
def get_conn():
    """
    Gerenciador de contexto para obter e fechar a conexão com o banco de dados.
    """
    if not DB_URL:
        raise ValueError("A variável 'DATABASE' não foi encontrada no arquivo .env!")

    conn = psycopg.connect(DB_URL)
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """
    Cria a estrutura inicial das tabelas operacionais no Neon PostgreSQL.
    """
    with get_conn() as conn:
        # Remove a tabela de configurações legada do banco, caso exista
        conn.execute("DROP TABLE IF EXISTS config_etiqueta CASCADE;")

        # 1. Tabela Clientes
        conn.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id BIGSERIAL PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                cpf VARCHAR(14),
                telefone VARCHAR(20),
                email VARCHAR(255),
                saldo NUMERIC(10, 2) DEFAULT 0.00,
                criado TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 2. Tabela Vales Presente
        conn.execute("""
            CREATE TABLE IF NOT EXISTS vales (
                id BIGSERIAL PRIMARY KEY,
                codigo VARCHAR(50) UNIQUE NOT NULL,
                cliente_id BIGINT REFERENCES clientes(id) ON DELETE SET NULL,
                valor NUMERIC(10, 2) NOT NULL,
                usado INT DEFAULT 0,
                validade DATE,
                criado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                usado_em TIMESTAMP,
                observacao TEXT
            );
        """)

        # 3. Tabela Histórico de Crédito
        conn.execute("""
            CREATE TABLE IF NOT EXISTS historico_credito (
                id BIGSERIAL PRIMARY KEY,
                cliente_id BIGINT REFERENCES clientes(id) ON DELETE CASCADE,
                valor NUMERIC(10, 2) NOT NULL,
                tipo VARCHAR(50) NOT NULL,
                descricao TEXT,
                motivo TEXT,
                criado TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Migração: Adiciona colunas faltantes na tabela historico_credito
        colunas_historico = [
            ("cliente_id", "BIGINT REFERENCES clientes(id) ON DELETE CASCADE"),
            ("valor", "NUMERIC(10, 2) NOT NULL DEFAULT 0.00"),
            ("tipo", "VARCHAR(50) NOT NULL DEFAULT 'manual'"),
            ("descricao", "TEXT"),
            ("motivo", "TEXT"),
            ("criado", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        ]
        for col_nome, col_def in colunas_historico:
            conn.execute(f"""
                ALTER TABLE historico_credito 
                ADD COLUMN IF NOT EXISTS {col_nome} {col_def};
            """)

        # 4. Tabela Produtos Outlet
        conn.execute("""
            CREATE TABLE IF NOT EXISTS produtos_outlet (
                id BIGSERIAL PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                codigo_barras VARCHAR(100) UNIQUE,
                preco_original NUMERIC(10, 2),
                preco_outlet NUMERIC(10, 2),
                defeito TEXT,
                status VARCHAR(50) DEFAULT 'Disponível',
                criado TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Migração: Adiciona colunas faltantes na tabela produtos_outlet
        colunas_outlet = [
            ("cliente_id", "BIGINT REFERENCES clientes(id) ON DELETE SET NULL"),
            ("sku", "VARCHAR(100) UNIQUE"),
            ("tipo", "VARCHAR(100)"),
            ("marca", "VARCHAR(100)"),
            ("modelo", "VARCHAR(100)"),
            ("grafico", "VARCHAR(255)"),
            ("cor", "VARCHAR(100)"),
            ("numeracao", "VARCHAR(50)"),
            ("tamanho", "VARCHAR(50)"),
            ("quantidade", "INT DEFAULT 1"),
            ("estoque", "INT DEFAULT 1"),
            ("valor_sugerido", "NUMERIC(10, 2)")
        ]
        for col_nome, col_def in colunas_outlet:
            conn.execute(f"""
                ALTER TABLE produtos_outlet 
                ADD COLUMN IF NOT EXISTS {col_nome} {col_def};
            """)


        # 5. Tabela Vendas Outlet
        conn.execute("""
            CREATE TABLE IF NOT EXISTS vendas_outlet (
                id BIGSERIAL PRIMARY KEY,
                cliente_id BIGINT REFERENCES clientes(id) ON DELETE SET NULL,
                produto_id BIGINT REFERENCES produtos_outlet(id) ON DELETE SET NULL,
                quantidade INT DEFAULT 1,
                preco_pago NUMERIC(10, 2),
                criado TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 6. Tabela Fila de Impressão
        conn.execute("""
            CREATE TABLE IF NOT EXISTS fila_impressao (
                id BIGSERIAL PRIMARY KEY,
                produto_id BIGINT REFERENCES produtos_outlet(id) ON DELETE CASCADE,
                texto_etiqueta TEXT,
                status VARCHAR(50) DEFAULT 'Pendente',
                criado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                quantidade INT DEFAULT 1
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_vales_usado_validade ON vales(usado, validade);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_vales_cliente_id ON vales(cliente_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_vales_codigo ON vales(codigo);")
        conn.commit()