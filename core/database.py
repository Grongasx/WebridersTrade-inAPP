"""
Módulo de conexão e inicialização do banco de dados PostgreSQL (Neon).
"""

import os
import sys
import psycopg
from contextlib import contextmanager
from dotenv import load_dotenv

# Determina o diretório base (pasta do .exe quando empacotado ou raiz do projeto)
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ENV_PATH = os.path.join(BASE_DIR, ".env")
if os.path.exists(ENV_PATH):
    load_dotenv(ENV_PATH)
else:
    load_dotenv()


def get_db_url():
    """Obtém dinamicamente a URL de conexão."""
    return os.getenv("DATABASE") or os.getenv("DATABASE_URL")


@contextmanager
def get_conn():
    """
    Gerenciador de contexto para obter e fechar a conexão com o banco de dados.
    """
    db_url = get_db_url()
    if not db_url and os.path.exists(ENV_PATH):
        load_dotenv(ENV_PATH, override=True)
        db_url = get_db_url()

    if not db_url:
        raise ValueError("A variável 'DATABASE' não foi encontrada no arquivo .env!")

    conn = psycopg.connect(db_url)
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
        conn.execute("""
            ALTER TABLE historico_credito
                ADD COLUMN IF NOT EXISTS cliente_id BIGINT REFERENCES clientes(id) ON DELETE CASCADE,
                ADD COLUMN IF NOT EXISTS valor NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
                ADD COLUMN IF NOT EXISTS tipo VARCHAR(50) NOT NULL DEFAULT 'manual',
                ADD COLUMN IF NOT EXISTS descricao TEXT,
                ADD COLUMN IF NOT EXISTS motivo TEXT,
                ADD COLUMN IF NOT EXISTS criado TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
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
        conn.execute("""
            ALTER TABLE produtos_outlet
                ADD COLUMN IF NOT EXISTS cliente_id BIGINT REFERENCES clientes(id) ON DELETE SET NULL,
                ADD COLUMN IF NOT EXISTS sku VARCHAR(100) UNIQUE,
                ADD COLUMN IF NOT EXISTS tipo VARCHAR(100),
                ADD COLUMN IF NOT EXISTS marca VARCHAR(100),
                ADD COLUMN IF NOT EXISTS modelo VARCHAR(100),
                ADD COLUMN IF NOT EXISTS grafico VARCHAR(255),
                ADD COLUMN IF NOT EXISTS cor VARCHAR(100),
                ADD COLUMN IF NOT EXISTS numeracao VARCHAR(50),
                ADD COLUMN IF NOT EXISTS tamanho VARCHAR(50),
                ADD COLUMN IF NOT EXISTS quantidade INT DEFAULT 1,
                ADD COLUMN IF NOT EXISTS estoque INT DEFAULT 1,
                ADD COLUMN IF NOT EXISTS valor_sugerido NUMERIC(10, 2);
        """)

        # 4.1 Tabela Categorias de Produtos (Armazenamento dinâmico de categorias)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS categorias_produto (
                id BIGSERIAL PRIMARY KEY,
                nome VARCHAR(100) UNIQUE NOT NULL,
                criado TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Migração: Popula categorias_produto com categorias padrão e existentes
        conn.execute("""
            INSERT INTO categorias_produto (nome)
            VALUES ('Shape'), ('Rodas'), ('Trucks'), ('Lixas'), ('Tênis'), ('Vestuário'), ('Acessórios'), ('Hardware'), ('Outros')
            ON CONFLICT (nome) DO NOTHING;
        """)
        conn.execute("""
            INSERT INTO categorias_produto (nome)
            SELECT DISTINCT tipo FROM produtos_outlet 
            WHERE tipo IS NOT NULL AND TRIM(tipo) != ''
            ON CONFLICT (nome) DO NOTHING;
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
        # Índices de performance
        conn.execute("CREATE INDEX IF NOT EXISTS idx_vales_usado_validade ON vales(usado, validade);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_vales_cliente_id ON vales(cliente_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_vales_codigo ON vales(codigo);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_produtos_outlet_codigo_barras ON produtos_outlet(codigo_barras);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_produtos_outlet_sku ON produtos_outlet(sku);")

        # Migração: Garante que todos os produtos outlet possuam EAN-13 numérico válido de 13 dígitos
        cur = conn.cursor()
        cur.execute("SELECT id, codigo_barras FROM produtos_outlet WHERE codigo_barras IS NULL OR length(codigo_barras) != 13;")
        prods_sem_ean = cur.fetchall()
        for p_id, _ in prods_sem_ean:
            base12 = f"200{str(p_id).zfill(9)}"[:12]
            soma = sum(int(c) * (1 if i % 2 == 0 else 3) for i, c in enumerate(base12))
            dv = (10 - (soma % 10)) % 10
            novo_ean = f"{base12}{dv}"
            cur.execute("UPDATE produtos_outlet SET codigo_barras = %s WHERE id = %s", (novo_ean, p_id))

        conn.commit()


def obter_categorias():
    """Retorna lista ordenada de categorias cadastradas no banco."""
    try:
        with get_conn() as conn:
            rows = conn.execute("""
                SELECT DISTINCT nome FROM (
                    SELECT nome FROM categorias_produto
                    UNION
                    SELECT tipo AS nome FROM produtos_outlet WHERE tipo IS NOT NULL AND TRIM(tipo) != ''
                ) t WHERE TRIM(nome) != '' ORDER BY nome ASC;
            """).fetchall()
            return [r[0] for r in rows if r[0]]
    except Exception:
        return ["Shape", "Rodas", "Trucks", "Lixas", "Tênis", "Vestuário", "Acessórios", "Hardware", "Outros"]


def salvar_categoria(nome_cat):
    """Salva dinamicamente uma nova categoria no banco de dados."""
    if not nome_cat or not str(nome_cat).strip():
        return
    nome_limpo = str(nome_cat).strip()
    try:
        with get_conn() as conn:
            conn.execute("""
                INSERT INTO categorias_produto (nome)
                VALUES (%s)
                ON CONFLICT (nome) DO NOTHING;
            """, (nome_limpo,))
            conn.commit()
    except Exception as e:
        print(f"[ERRO AO SALVAR CATEGORIA]: {e}")