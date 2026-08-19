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

        # 7. Tabela Garantias & RMA
        conn.execute("""
            CREATE TABLE IF NOT EXISTS garantias (
                id BIGSERIAL PRIMARY KEY,
                protocolo VARCHAR(50) UNIQUE NOT NULL,
                cliente_id BIGINT REFERENCES clientes(id) ON DELETE SET NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'solicitacao_cliente',
                tipo_produto VARCHAR(100),
                marca VARCHAR(100),
                modelo VARCHAR(100),
                grafico VARCHAR(255),
                cor VARCHAR(100),
                numeracao VARCHAR(50),
                tamanho VARCHAR(50),
                numero_serie VARCHAR(100),
                nota_fiscal VARCHAR(100),
                valor_produto NUMERIC(10, 2) DEFAULT 0.00,
                defeito_relatado TEXT,
                fornecedor_nome VARCHAR(255),
                protocolo_fornecedor VARCHAR(100),
                codigo_reversa_cliente VARCHAR(100),
                rastreio_cliente_loja VARCHAR(100),
                codigo_reversa_fornecedor VARCHAR(100),
                rastreio_loja_fornecedor VARCHAR(100),
                rastreio_fornecedor_loja VARCHAR(100),
                rastreio_loja_cliente VARCHAR(100),
                observacoes TEXT,
                criado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                atualizado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                concluido_em TIMESTAMP
            );
        """)

        # Migração defensiva para colunas em garantias
        conn.execute("""
            ALTER TABLE garantias
                ADD COLUMN IF NOT EXISTS cliente_id BIGINT REFERENCES clientes(id) ON DELETE SET NULL,
                ADD COLUMN IF NOT EXISTS status VARCHAR(50) NOT NULL DEFAULT 'solicitacao_cliente',
                ADD COLUMN IF NOT EXISTS tipo_produto VARCHAR(100),
                ADD COLUMN IF NOT EXISTS marca VARCHAR(100),
                ADD COLUMN IF NOT EXISTS modelo VARCHAR(100),
                ADD COLUMN IF NOT EXISTS grafico VARCHAR(255),
                ADD COLUMN IF NOT EXISTS cor VARCHAR(100),
                ADD COLUMN IF NOT EXISTS numeracao VARCHAR(50),
                ADD COLUMN IF NOT EXISTS tamanho VARCHAR(50),
                ADD COLUMN IF NOT EXISTS numero_serie VARCHAR(100),
                ADD COLUMN IF NOT EXISTS nota_fiscal VARCHAR(100),
                ADD COLUMN IF NOT EXISTS valor_produto NUMERIC(10, 2) DEFAULT 0.00,
                ADD COLUMN IF NOT EXISTS defeito_relatado TEXT,
                ADD COLUMN IF NOT EXISTS fornecedor_nome VARCHAR(255),
                ADD COLUMN IF NOT EXISTS protocolo_fornecedor VARCHAR(100),
                ADD COLUMN IF NOT EXISTS codigo_reversa_cliente VARCHAR(100),
                ADD COLUMN IF NOT EXISTS rastreio_cliente_loja VARCHAR(100),
                ADD COLUMN IF NOT EXISTS codigo_reversa_fornecedor VARCHAR(100),
                ADD COLUMN IF NOT EXISTS rastreio_loja_fornecedor VARCHAR(100),
                ADD COLUMN IF NOT EXISTS rastreio_fornecedor_loja VARCHAR(100),
                ADD COLUMN IF NOT EXISTS rastreio_loja_cliente VARCHAR(100),
                ADD COLUMN IF NOT EXISTS observacoes TEXT,
                ADD COLUMN IF NOT EXISTS criado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ADD COLUMN IF NOT EXISTS atualizado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ADD COLUMN IF NOT EXISTS concluido_em TIMESTAMP;
        """)

        # Índices de performance
        conn.execute("CREATE INDEX IF NOT EXISTS idx_vales_usado_validade ON vales(usado, validade);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_vales_cliente_id ON vales(cliente_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_vales_codigo ON vales(codigo);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_produtos_outlet_codigo_barras ON produtos_outlet(codigo_barras);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_produtos_outlet_sku ON produtos_outlet(sku);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_garantias_status ON garantias(status);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_garantias_cliente ON garantias(cliente_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_garantias_protocolo ON garantias(protocolo);")

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


def obter_catalogo_completo():
    """Retorna lista de todas as triplas (tipo, marca, modelo) da hierarquia com cache em memória."""
    from core.cache import cache
    cached = cache.get("catalogo:completo")
    if cached is not None:
        return cached

    try:
        with get_conn() as conn:
            rows = conn.execute("""
                SELECT tipo, marca, modelo FROM (
                    SELECT tipo, marca, modelo FROM catalogo_produtos 
                    WHERE tipo IS NOT NULL AND TRIM(tipo) != ''
                    UNION
                    SELECT tipo, COALESCE(marca, ''), COALESCE(modelo, '') FROM produtos_outlet 
                    WHERE tipo IS NOT NULL AND TRIM(tipo) != ''
                ) t ORDER BY tipo ASC, marca ASC, modelo ASC;
            """).fetchall()
            resultado = [(r[0] or "", r[1] or "", r[2] or "") for r in rows]
            cache.set("catalogo:completo", resultado, ttl=120)
            return resultado
    except Exception:
        return []


def obter_tipos():
    """Retorna lista ordenada de tipos/categorias cadastrados na hierarquia a partir do cache."""
    cat = obter_catalogo_completo()
    return sorted(list({r[0] for r in cat if r[0] and r[0].strip()}))


def obter_categorias():
    """Alias para obter_tipos mantendo compatibilidade."""
    return obter_tipos()


def obter_marcas_por_tipo(tipo=None):
    """Retorna marcas associadas a um tipo específico a partir do cache."""
    cat = obter_catalogo_completo()
    t_clean = (tipo or "").strip().lower()
    if t_clean:
        return sorted(list({r[1] for r in cat if r[1] and r[1].strip() and r[0].lower() == t_clean}))
    return sorted(list({r[1] for r in cat if r[1] and r[1].strip()}))


def obter_modelos_por_marca(tipo=None, marca=None):
    """Retorna modelos associados à marca e ao tipo selecionados a partir do cache."""
    cat = obter_catalogo_completo()
    t_clean = (tipo or "").strip().lower()
    m_clean = (marca or "").strip().lower()

    if t_clean and m_clean:
        return sorted(list({r[2] for r in cat if r[2] and r[2].strip() and r[0].lower() == t_clean and r[1].lower() == m_clean}))
    elif m_clean:
        return sorted(list({r[2] for r in cat if r[2] and r[2].strip() and r[1].lower() == m_clean}))
    elif t_clean:
        return sorted(list({r[2] for r in cat if r[2] and r[2].strip() and r[0].lower() == t_clean}))
    return sorted(list({r[2] for r in cat if r[2] and r[2].strip()}))


def salvar_hierarquia(tipo, marca, modelo=None):
    """Salva dinamicamente a relação Tipo -> Marca -> Modelo no banco de dados e invalida cache."""
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

        from core.cache import cache
        cache.invalidate_prefix("catalogo")
    except Exception as e:
        print(f"[ERRO AO SALVAR HIERARQUIA]: {e}")


def salvar_categoria(nome_cat):
    """Alias para salvar_hierarquia(tipo, '', '') mantendo compatibilidade."""
    salvar_hierarquia(nome_cat, "")


def gerar_protocolo_garantia(conn=None):
    """Gera um protocolo único de garantia no formato GAR-YYYY-XXXX."""
    import datetime
    ano = datetime.datetime.now().year

    def _exec(c):
        row = c.execute("SELECT COUNT(*) FROM garantias WHERE protocolo LIKE %s", (f"GAR-{ano}-%",)).fetchone()
        count = (row[0] if row else 0) + 1
        return f"GAR-{ano}-{str(count).zfill(4)}"

    if conn:
        return _exec(conn)
    with get_conn() as conn_local:
        return _exec(conn_local)
