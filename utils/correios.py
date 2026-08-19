"""
Módulo de Consulta e Rastreamento de Encomendas dos Correios.
"""

import json
import re
import urllib.request
import urllib.error
import webbrowser
from typing import Dict, Any, List, Optional

LINKTRACK_USER = "teste"
LINKTRACK_TOKEN = "1abcd00b2731640e886fb41a8a9671ad143c57c304c1e4a7f671225d6cb72e36"


def limpar_codigo_rastreio(codigo: str) -> str:
    """Remove espaços, traços e converte para maiúsculo."""
    return re.sub(r"[^A-Za-z0-9]", "", (codigo or "")).upper()


def validar_codigo_correios(codigo: str) -> bool:
    """Verifica se o código corresponde ao padrão SRO de 13 caracteres (ex: OY850448629BR)."""
    cod = limpar_codigo_rastreio(codigo)
    return bool(re.match(r"^[A-Z]{2}[0-9]{9}[A-Z]{2}$", cod))


def obter_url_correios_oficial(codigo: str) -> str:
    """Retorna o link direto oficial dos Correios com o parâmetro objetos=."""
    cod = limpar_codigo_rastreio(codigo)
    return f"https://rastreamento.correios.com.br/app/index.php?objetos={cod}"


def abrir_site_correios(codigo: str):
    """Abre a página oficial de rastreamento dos Correios no navegador padrão com 1 clique."""
    url = obter_url_correios_oficial(codigo)
    webbrowser.open(url)


def consultar_rastreio_correios(codigo: str) -> Dict[str, Any]:
    """
    Consulta o rastreamento do objeto postal em APIs públicas.
    Retorna dicionário padronizado com status geral e lista de eventos em ordem cronológica reversa.
    """
    cod = limpar_codigo_rastreio(codigo)
    if not cod:
        return {
            "codigo": "",
            "sucesso": False,
            "erro": "Código de rastreamento não informado."
        }

    # Tenta consultar via API pública LinkTrack
    url = f"https://api.linketrack.com/track/json?user={LINKTRACK_USER}&token={LINKTRACK_TOKEN}&codigo={cod}"

    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json"
            }
        )

        with urllib.request.urlopen(req, timeout=6) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                eventos_raw = data.get("eventos", [])
                eventos_formatados: List[Dict[str, Any]] = []

                for ev in eventos_raw:
                    data_ev = ev.get("data", "")
                    hora_ev = ev.get("hora", "")
                    status_ev = ev.get("status", "")
                    local_ev = ev.get("local", "")
                    destino_ev = ev.get("destino", "")
                    detalhe_ev = ev.get("detalhe", "") or ""

                    if destino_ev:
                        detalhe_ev = f"Origem: {local_ev} ➔ Destino: {destino_ev}" if not detalhe_ev else f"{detalhe_ev} (Para: {destino_ev})"

                    eventos_formatados.append({
                        "data": data_ev,
                        "hora": hora_ev,
                        "status": status_ev,
                        "local": local_ev,
                        "destino": destino_ev,
                        "detalhes": detalhe_ev
                    })

                if eventos_formatados:
                    ultimo_evento = eventos_formatados[0]
                    status_geral = ultimo_evento.get("status", "Objeto em processamento")
                    entregue = "entregue" in status_geral.lower()

                    return {
                        "codigo": cod,
                        "sucesso": True,
                        "servico": data.get("servico", "Correios"),
                        "quantidade": len(eventos_formatados),
                        "status_geral": status_geral,
                        "ultimo_local": ultimo_evento.get("local", ""),
                        "ultima_data": f"{ultimo_evento.get('data', '')} às {ultimo_evento.get('hora', '')}".strip(" às"),
                        "entregue": entregue,
                        "eventos": eventos_formatados
                    }

    except Exception:
        pass

    # Fallback amigável quando as APIs externas estiverem bloqueadas por captcha/firewall
    return {
        "codigo": cod,
        "sucesso": False,
        "erro": "Para visualizar o rastreamento em tempo real com segurança, abra a consulta oficial no portal dos Correios pelo botão abaixo."
    }
