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
    """Verifica se o código corresponde ao padrão SRO de 13 caracteres (ex: NL123456789BR)."""
    cod = limpar_codigo_rastreio(codigo)
    return bool(re.match(r"^[A-Z]{2}[0-9]{9}[A-Z]{2}$", cod))


def abrir_site_correios(codigo: str):
    """Abre a página oficial de rastreamento dos Correios no navegador padrão."""
    cod = limpar_codigo_rastreio(codigo)
    url = f"https://rastreamento.correios.com.br/app/index.php?codigo={cod}"
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

    url = f"https://api.linketrack.com/track/json?user={LINKTRACK_USER}&token={LINKTRACK_TOKEN}&codigo={cod}"

    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "ValePresenteManager-Tracking/2.0",
                "Accept": "application/json"
            }
        )

        with urllib.request.urlopen(req, timeout=12) as response:
            if response.status != 200:
                return {
                    "codigo": cod,
                    "sucesso": False,
                    "erro": f"Serviço de rastreamento retornou código HTTP {response.status}."
                }
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

            # Constrói descrição do trajeto se houver destino
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

        ultimo_evento = eventos_formatados[0] if eventos_formatados else {}
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

    except urllib.error.HTTPError as e:
        if e.code == 429:
            return {
                "codigo": cod,
                "sucesso": False,
                "erro": "Limite temporário de consultas da API atingido. Tente abrir pelo site dos Correios."
            }
        return {
            "codigo": cod,
            "sucesso": False,
            "erro": f"Erro na consulta do objeto {cod} (HTTP {e.code})."
        }
    except Exception as e:
        return {
            "codigo": cod,
            "sucesso": False,
            "erro": f"Não foi possível conectar ao serviço de rastreamento ({e})."
        }
