"""
Funcoes utilitarias do sistema.
"""

import uuid
import datetime
import re


def gerar_codigo():
    """Gera um codigo unico para vale presente."""
    raw = uuid.uuid4().hex.upper()
    return f"VP-{raw[:4]}-{raw[4:8]}"


def agora():
    """Retorna a data/hora atual como objeto datetime nativo.

    Antes retornava uma string formatada (herança do SQLite). Com o
    PostgreSQL/psycopg, o ideal é passar objetos datetime.datetime
    diretamente nos parâmetros (%s) das colunas TIMESTAMP — evita
    ambiguidade de tipo nas comparações/inserts."""
    return datetime.datetime.now()


def hoje():
    """Retorna a data atual como objeto date nativo.

    Antes retornava uma string ISO (herança do SQLite). Com o
    PostgreSQL/psycopg, o ideal é passar objetos datetime.date
    diretamente nos parâmetros (%s) das colunas DATE."""
    return datetime.date.today()


def brl(valor):
    """Formata um valor numerico para moeda brasileira."""
    return f"R$ {valor:,.2f}".replace(",","X").replace(".",",").replace("X",".")


def vencido(validade):
    """Verifica se uma data de validade ja passou.

    Aceita date, datetime ou string ISO (o psycopg devolve objetos
    date/datetime nativos para colunas DATE/TIMESTAMP do Postgres;
    strings continuam suportadas por compatibilidade)."""
    if not validade:
        return False
    if isinstance(validade, datetime.datetime):
        validade = validade.date()
    elif isinstance(validade, str):
        try:
            validade = datetime.date.fromisoformat(validade[:10])
        except Exception:
            return False
    if not isinstance(validade, datetime.date):
        return False
    return validade < datetime.date.today()


def formatar_data(valor):
    """Formata uma data/hora (date, datetime ou string) para exibição
    no formato AAAA-MM-DD. Retorna '—' se vazio."""
    if not valor:
        return "—"
    if isinstance(valor, (datetime.datetime, datetime.date)):
        return valor.strftime("%Y-%m-%d")
    return str(valor)[:10]


def validar_cpf(cpf):
    """Valida um CPF brasileiro."""
    cpf = re.sub(r"\D", "", cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for pos in range(9, 11):
        soma = sum(int(cpf[i]) * (pos + 1 - i) for i in range(pos))
        dig = (soma * 10 % 11) % 10
        if dig != int(cpf[pos]):
            return False
    return True


def formatar_cpf(texto):
    """Formata (parcial ou completo) uma sequência de dígitos como CPF:
    000.000.000-00. Aceita texto já formatado ou só números."""
    d = re.sub(r"\D", "", texto or "")[:11]
    if len(d) <= 3:
        return d
    if len(d) <= 6:
        return f"{d[:3]}.{d[3:]}"
    if len(d) <= 9:
        return f"{d[:3]}.{d[3:6]}.{d[6:]}"
    return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"


def formatar_telefone(texto):
    """Formata (parcial ou completo) uma sequência de dígitos como
    telefone brasileiro: (00) 0000-0000 (fixo) ou (00) 00000-0000 (celular)."""
    d = re.sub(r"\D", "", texto or "")[:11]
    if len(d) == 0:
        return ""
    if len(d) <= 2:
        return f"({d}"
    if len(d) <= 6:
        return f"({d[:2]}) {d[2:]}"
    if len(d) <= 10:
        return f"({d[:2]}) {d[2:6]}-{d[6:]}"
    return f"({d[:2]}) {d[2:7]}-{d[7:]}"


def validar_email(email):
    """Validação simples de formato de e-mail. Campo vazio é considerado
    válido (a obrigatoriedade é responsabilidade de quem chama)."""
    if not email:
        return True
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email.strip()))


def txt_para_float(texto):
    """Converte texto de moeda para float."""
    if not texto:
        return 0.0
    raw = texto.strip().replace(".", "").replace(",", ".")
    try:
        return float(raw)
    except:
        return 0.0


def validar_moeda(valor_str):
    """Valida se uma string esta no formato de moeda correto."""
    return bool(re.match(r"^\d+(?:,\d{1,2})?$", valor_str.strip()))


def creditar_cliente(cliente_id, valor, tipo, motivo, conn=None):
    """Credita um valor na conta de um cliente e registra a origem no
    histórico de crédito (historico_credito.tipo).

    Usada tanto pela venda de produtos Outlet ('outlet') quanto pelo
    resgate de Vale Presente ('vale') — os dois caem no mesmo
    clientes.saldo, mas ficam rastreáveis pelo campo `tipo`.

    Se `conn` for passado, a operação roda dentro dessa conexão/transação
    já aberta (quem chamou é responsável pelo commit). Caso contrário,
    abre e commita sua própria conexão.
    """
    from core.database import get_conn

    def _executar(c):
        c.execute(
            "INSERT INTO historico_credito (cliente_id,tipo,valor,motivo,criado) VALUES (%s,%s,%s,%s,%s)",
            (cliente_id, tipo, valor, motivo, agora())
        )
        c.execute(
            "UPDATE clientes SET saldo = COALESCE(saldo,0) + %s WHERE id=%s",
            (valor, cliente_id)
        )

    if conn is not None:
        _executar(conn)
    else:
        with get_conn() as c:
            _executar(c)
            c.commit()


# ═══════════════════════════════════════════
# Estruturas de produtos e cálculo de SKU
# ═══════════════════════════════════════════
TIPO_PREFIXOS = {
    "Shape": "SHP",
    "Rodas": "ROD",
    "Trucks": "TRK",
    "Lixas": "LIX",
    "Tênis": "TNS",
    "Vestuário": "VES",
    "Acessórios": "ACS",
    "Hardware": "HRD",
    "Outros": "OUT",
}

NUMERACAO_POR_TIPO = {
    "Shape": ["7.5\"", "7.75\"", "8.0\"", "8.125\"", "8.25\"", "8.375\"", "8.5\"", "8.75\"", "9.0\"", "Único"],
    "Rodas": ["50mm", "51mm", "52mm", "53mm", "54mm", "55mm", "56mm", "58mm", "60mm"],
    "Trucks": ["129mm", "139mm", "144mm", "149mm", "154mm", "159mm", "169mm"],
    "Tênis": ["34", "35", "36", "37", "38", "39", "40", "41", "42", "43", "44", "45"],
    "Vestuário": ["PP", "P", "M", "G", "GG", "XGG", "Único"],
    "Lixas": ["Padrão", "Grip Tape", "Único"],
    "Acessórios": ["Único", "Infantil", "Adulto"],
    "Hardware": ["7/8\"", "1\"", "1 1/8\"", "1 1/4\"", "Único"],
    "Outros": ["Único", "Padrão"]
}


def calcular_sku(tipo, marca, modelo, grafico, cor, numeracao, seed_id=None):
    """
    Calcula dinamente um SKU interno único no formato:
    WR-[TIPO]-[MARCA]-[TAMANHO]-[HASH] Ex: WR-SHP-SAN-80-4912
    """
    t_pref = TIPO_PREFIXOS.get(tipo, "OUT")
    
    m_clean = re.sub(r"[^A-Z0-9]", "", (marca or "").upper())
    m_pref = (m_clean[:3] if len(m_clean) >= 3 else m_clean.ljust(3, "X")) if m_clean else "GEN"

    n_clean = re.sub(r"[^A-Z0-9]", "", (numeracao or "").upper())
    n_pref = n_clean[:4] if n_clean else "UNI"

    if seed_id:
        seq = f"{int(seed_id):04d}"
    else:
        raw = f"{tipo}:{marca}:{modelo}:{grafico}:{cor}:{numeracao}".upper()
        h_val = abs(hash(raw)) % 10000
        seq = f"{h_val:04d}"

    return f"WR-{t_pref}-{m_pref}-{n_pref}-{seq}"


CODE39_PATTERNS = {
    '0': '101001101', '1': '201001002', '2': '102001002', '3': '202001001',
    '4': '101021002', '5': '201021001', '6': '102021001', '7': '101001202',
    '8': '201001201', '9': '102001201', 'A': '201002101', 'B': '102002101',
    'C': '202002100', 'D': '101022100', 'E': '201022100', 'F': '102022100',
    'G': '101002201', 'H': '201002200', 'I': '102002200', 'J': '101022200',
    'K': '201001021', 'L': '102001021', 'M': '202001020', 'N': '101021020',
    'O': '201021020', 'P': '102021020', 'Q': '101002021', 'R': '201002020',
    'S': '102002020', 'T': '101022020', 'U': '220010101', 'V': '120020101',
    'W': '220020100', 'X': '120010201', 'Y': '220010200', 'Z': '120020200',
    '-': '120010102', '.': '220010100', ' ': '120201001', '$': '120120100',
    '/': '120100120', '+': '120012010', '%': '100120120', '*': '120102010'
}


def gerar_imagem_barcode_sku(codigo_str: str, largura_px: int, altura_px: int):
    """Gera uma imagem PIL de código de barras Code39 universal para SKUs e EANs."""
    from PIL import Image, ImageDraw, ImageFont
    
    raw_code = str(codigo_str).upper().strip()
    valid_code = ''.join([c for c in raw_code if c in CODE39_PATTERNS])
    if not valid_code:
        valid_code = "SKU-0000"
        
    full_code = f"*{valid_code}*"
    
    largura_px = max(40, largura_px)
    altura_px = max(20, altura_px)
    
    modules = []
    for char in full_code:
        pat = CODE39_PATTERNS.get(char, CODE39_PATTERNS['*'])
        for i, val in enumerate(pat):
            is_bar = (i % 2 == 0)
            width = 2.2 if val == '2' else 1.0
            modules.append((is_bar, width))
        modules.append((False, 1.0))  # Gap entre caracteres
        
    total_units = sum(w for _, w in modules)
    unit_px = largura_px / float(total_units)
    
    img = Image.new("RGB", (largura_px, altura_px), "white")
    draw = ImageDraw.Draw(img)
    
    text_h = max(8, int(altura_px * 0.28))
    bar_h = altura_px - text_h
    
    curr_x = 0.0
    for is_bar, w_units in modules:
        next_x = curr_x + (w_units * unit_px)
        if is_bar:
            draw.rectangle([int(curr_x), 0, int(next_x), bar_h], fill="black")
        curr_x = next_x
        
    try:
        font = ImageFont.truetype("arialbd.ttf", text_h - 1)
    except IOError:
        font = ImageFont.load_default()
        
    if hasattr(draw, "textlength"):
        tw = draw.textlength(valid_code, font=font)
    else:
        bbox = font.getbbox(valid_code)
        tw = bbox[2] - bbox[0]
        
    tx = max(0, int((largura_px - tw) / 2))
    draw.text((tx, bar_h), valid_code, fill="black", font=font)
    
    return img