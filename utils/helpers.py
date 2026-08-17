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


def converter_para_ean13(codigo_str: str) -> str:
    """Converte qualquer identificador/SKU/texto em um código EAN-13 numérico válido de 13 dígitos com DV."""
    digits_raw = "".join(filter(str.isdigit, str(codigo_str)))
    if len(digits_raw) == 13:
        # Valida se o DV está correto
        base = digits_raw[:12]
        soma = sum(int(c) * (1 if i % 2 == 0 else 3) for i, c in enumerate(base))
        dv = (10 - (soma % 10)) % 10
        return f"{base}{dv}"

    if not digits_raw:
        # Se for string alfa pura, gera base numérica consistente
        h_val = abs(hash(str(codigo_str).upper())) % 1000000000
        digits_raw = str(h_val)

    # Prefixo 200 (uso restrito interno / in-store) + 9 dígitos + dígito verificador
    base12 = f"200{digits_raw.zfill(9)}"[:12]
    soma = sum(int(c) * (1 if i % 2 == 0 else 3) for i, c in enumerate(base12))
    dv = (10 - (soma % 10)) % 10
    return f"{base12}{dv}"


def gerar_e_persistir_ean13(conn, produto_id: int, ean_atual: str = None) -> str:
    """Garante e persiste um EAN-13 único e 100% válido no banco de dados para o produto."""
    if ean_atual and str(ean_atual).strip() and str(ean_atual).strip().lower() not in ["none", "—", "", "null"]:
        digits = "".join(filter(str.isdigit, str(ean_atual)))
        if len(digits) == 13:
            return digits

    novo_ean = converter_para_ean13(str(produto_id))
    if conn:
        try:
            conn.execute(
                "UPDATE produtos_outlet SET codigo_barras = %s WHERE id = %s",
                (novo_ean, produto_id)
            )
            conn.commit()
        except Exception:
            pass

    return novo_ean


def gerar_imagem_ean13(codigo_str: str, largura_px: int, altura_px: int):
    """
    Gera uma imagem PIL de Código de Barras EAN-13 padronizado e nítido para leitores óticos/scanners.
    Utiliza python-barcode com fallback para renderizador GDI/PIL pixel-perfect.
    """
    from PIL import Image, ImageDraw, ImageFont

    ean13_str = converter_para_ean13(codigo_str)
    largura_px = max(60, int(largura_px))
    altura_px = max(20, int(altura_px))

    try:
        import barcode
        from barcode.writer import ImageWriter

        ean_cls = barcode.get_barcode_class("ean13")
        writer = ImageWriter()
        ean_inst = ean_cls(ean13_str[:12], writer=writer)
        img_bar = ean_inst.render({
            "module_width": 0.28,
            "module_height": 11.0,
            "font_size": 8,
            "text_distance": 2.5,
            "quiet_zone": 4.5,
            "write_text": True
        })
        return img_bar.resize((largura_px, altura_px), Image.Resampling.LANCZOS)
    except Exception:
        pass

    # Fallback: renderizador puro PIL EAN-13 (95 módulos + quiet zones)
    L_PATTERNS = ["0001101", "0011001", "0010011", "0111101", "0100011", "0110001", "0101111", "0111011", "0110111", "0001011"]
    G_PATTERNS = ["0100111", "0110011", "0011011", "0100001", "0011101", "0111001", "0000101", "0010001", "0001001", "0010111"]
    R_PATTERNS = ["1110010", "1100110", "1101100", "1000010", "1011100", "1001110", "1010000", "1000100", "1001000", "1110100"]
    PARITY_TABLE = ["LLLLLL", "LLGLGG", "LLGGLG", "LLGGGL", "LGLLGG", "LGGGLL", "LGGGGL", "LGLGLG", "LGLGGL", "LGGLGL"]

    first = int(ean13_str[0])
    parity = PARITY_TABLE[first]

    bits = []
    for b in "101":
        bits.append((b == "1", True))

    for i in range(6):
        d = int(ean13_str[i + 1])
        pat = L_PATTERNS[d] if parity[i] == "L" else G_PATTERNS[d]
        for b in pat:
            bits.append((b == "1", False))

    for b in "01010":
        bits.append((b == "1", True))

    for i in range(6):
        d = int(ean13_str[i + 7])
        pat = R_PATTERNS[d]
        for b in pat:
            bits.append((b == "1", False))

    for b in "101":
        bits.append((b == "1", True))

    quiet_left = 9
    quiet_right = 7
    total_modules = 95 + quiet_left + quiet_right
    module_w = largura_px / float(total_modules)

    img = Image.new("RGB", (largura_px, altura_px), "white")
    draw = ImageDraw.Draw(img)

    text_h = max(7, int(altura_px * 0.26))
    bar_h_normal = max(10, altura_px - text_h - 2)
    bar_h_guard = max(bar_h_normal, min(altura_px - 1, bar_h_normal + int(text_h * 0.45)))

    start_x = quiet_left * module_w
    for idx, (is_black, is_guard) in enumerate(bits):
        if is_black:
            x0 = int(start_x + (idx * module_w))
            x1 = max(x0 + 1, int(start_x + ((idx + 1) * module_w)))
            h = bar_h_guard if is_guard else bar_h_normal
            draw.rectangle([x0, 0, x1, h], fill="black")

    try:
        font = ImageFont.truetype("arial.ttf", text_h)
    except IOError:
        font = ImageFont.load_default()

    draw.text((max(0, int(start_x - (text_h * 0.75))), bar_h_normal - 1), ean13_str[0], fill="black", font=font)
    left_str = ean13_str[1:7]
    x_left_center = start_x + (3 + 21) * module_w
    draw.text((int(x_left_center - (len(left_str) * text_h * 0.28)), bar_h_normal + 1), left_str, fill="black", font=font)

    right_str = ean13_str[7:13]
    x_right_center = start_x + (3 + 42 + 5 + 21) * module_w
    draw.text((int(x_right_center - (len(right_str) * text_h * 0.28)), bar_h_normal + 1), right_str, fill="black", font=font)

    return img


def gerar_imagem_barcode_sku(codigo_str: str, largura_px: int, altura_px: int):
    """Alias para gerar_imagem_ean13 mantendo compatibilidade com leitor ótico."""
    return gerar_imagem_ean13(codigo_str, largura_px, altura_px)