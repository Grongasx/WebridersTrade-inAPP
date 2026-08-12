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