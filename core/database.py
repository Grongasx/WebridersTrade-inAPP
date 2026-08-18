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

        # 4.1 Tabela Catálogo Hierárquico de Produtos (Cascata Tipo -> Marca -> Modelo)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS catalogo_produtos (
                id BIGSERIAL PRIMARY KEY,
                tipo VARCHAR(100) NOT NULL,
                marca VARCHAR(100) NOT NULL DEFAULT '',
                modelo VARCHAR(100) NOT NULL DEFAULT '',
                criado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT uq_tipo_marca_modelo UNIQUE (tipo, marca, modelo)
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_catalogo_tipo ON catalogo_produtos(tipo);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_catalogo_tipo_marca ON catalogo_produtos(tipo, marca);")

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


def obter_tipos():
    """Retorna lista ordenada de tipos/categorias cadastrados na hierarquia."""
    try:
        with get_conn() as conn:
            rows = conn.execute("""
                SELECT DISTINCT tipo FROM (
                    SELECT tipo FROM catalogo_produtos WHERE tipo IS NOT NULL AND TRIM(tipo) != ''
                    UNION
                    SELECT tipo FROM produtos_outlet WHERE tipo IS NOT NULL AND TRIM(tipo) != ''
                ) t ORDER BY tipo ASC;
            """).fetchall()
            return [r[0] for r in rows if r[0]]
    except Exception:
        return []


def obter_categorias():
    """Alias para obter_tipos mantendo compatibilidade."""
    return obter_tipos()


def obter_marcas_por_tipo(tipo=None):
    """Retorna marcas associadas a um tipo específico (ou todas caso tipo seja vazio)."""
    try:
        with get_conn() as conn:
            if tipo and str(tipo).strip():
                t_clean = str(tipo).strip()
                rows = conn.execute("""
                    SELECT DISTINCT marca FROM (
                        SELECT marca FROM catalogo_produtos 
                        WHERE LOWER(TRIM(tipo)) = LOWER(%s) AND marca IS NOT NULL AND TRIM(marca) != ''
                        UNION
                        SELECT marca FROM produtos_outlet 
                        WHERE LOWER(TRIM(tipo)) = LOWER(%s) AND marca IS NOT NULL AND TRIM(marca) != ''
                    ) t ORDER BY marca ASC;
                """, (t_clean, t_clean)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT DISTINCT marca FROM (
                        SELECT marca FROM catalogo_produtos WHERE marca IS NOT NULL AND TRIM(marca) != ''
                        UNION
                        SELECT marca FROM produtos_outlet WHERE marca IS NOT NULL AND TRIM(marca) != ''
                    ) t ORDER BY marca ASC;
                """).fetchall()
            return [r[0] for r in rows if r[0]]
    except Exception:
        return []


def obter_modelos_por_marca(tipo=None, marca=None):
    """Retorna modelos associados à marca e ao tipo selecionados."""
    try:
        with get_conn() as conn:
            t_clean = str(tipo or "").strip()
            m_clean = str(marca or "").strip()

            if t_clean and m_clean:
                rows = conn.execute("""
                    SELECT DISTINCT modelo FROM (
                        SELECT modelo FROM catalogo_produtos 
                        WHERE LOWER(TRIM(tipo)) = LOWER(%s) AND LOWER(TRIM(marca)) = LOWER(%s) AND modelo IS NOT NULL AND TRIM(modelo) != ''
                        UNION
                        SELECT modelo FROM produtos_outlet 
                        WHERE LOWER(TRIM(tipo)) = LOWER(%s) AND LOWER(TRIM(marca)) = LOWER(%s) AND modelo IS NOT NULL AND TRIM(modelo) != ''
                    ) t ORDER BY modelo ASC;
                """, (t_clean, m_clean, t_clean, m_clean)).fetchall()
            elif m_clean:
                rows = conn.execute("""
                    SELECT DISTINCT modelo FROM (
                        SELECT modelo FROM catalogo_produtos 
                        WHERE LOWER(TRIM(marca)) = LOWER(%s) AND modelo IS NOT NULL AND TRIM(modelo) != ''
                        UNION
                        SELECT modelo FROM produtos_outlet 
                        WHERE LOWER(TRIM(marca)) = LOWER(%s) AND modelo IS NOT NULL AND TRIM(modelo) != ''
                    ) t ORDER BY modelo ASC;
                """, (m_clean, m_clean)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT DISTINCT modelo FROM (
                        SELECT modelo FROM catalogo_produtos WHERE modelo IS NOT NULL AND TRIM(modelo) != ''
                        UNION
                        SELECT modelo FROM produtos_outlet WHERE modelo IS NOT NULL AND TRIM(modelo) != ''
                    ) t ORDER BY modelo ASC;
                """).fetchall()
            return [r[0] for r in rows if r[0]]
    except Exception:
        return []


def salvar_hierarquia(tipo, marca, modelo=None):
    """Salva dinamicamente a relação Tipo -> Marca -> Modelo no banco de dados."""
    t_clean = str(tipo or "").strip()
    m_clean = str(marca or "").strip()
    mod_clean = str(modelo or "").strip()

    if not t_clean:
        return

    try:
        with get_conn() as conn:
            conn.execute("""
                INSERT INTO catalogo_produtos (tipo, marca, modelo)
                VALUES (%s, '', '')
                ON CONFLICT (tipo, marca, modelo) DO NOTHING;
            """, (t_clean,))

            if m_clean:
                conn.execute("""
                    INSERT INTO catalogo_produtos (tipo, marca, modelo)
                    VALUES (%s, %s, '')
                    ON CONFLICT (tipo, marca, modelo) DO NOTHING;
                """, (t_clean, m_clean))

            if m_clean and mod_clean:
                conn.execute("""
                    INSERT INTO catalogo_produtos (tipo, marca, modelo)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (tipo, marca, modelo) DO NOTHING;
                """, (t_clean, m_clean, mod_clean))

            conn.commit()
    except Exception as e:
        print(f"[ERRO AO SALVAR HIERARQUIA]: {e}")


def salvar_categoria(nome_cat):
    """Alias para salvar_hierarquia(tipo, '', '') mantendo compatibilidade."""
    salvar_hierarquia(nome_cat, "")