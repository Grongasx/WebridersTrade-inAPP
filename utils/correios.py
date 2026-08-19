"""
Módulo de Consulta e Rastreamento Oficial de Encomendas dos Correios (API CWS / SRO).
"""

import os
import re
import json
import base64
import urllib.request
import urllib.error
import webbrowser
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

_TOKEN_CACHE = {
    "token": None,
    "expira_em": None,
    "ultimo_erro": None
}


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


def _formatar_documento(doc: str) -> List[str]:
    """Retorna lista de variações de formatação de CNPJ ou CPF para compatibilidade CWS."""
    digits = "".join(c for c in (doc or "") if c.isdigit())
    variacoes = [doc]

    if len(digits) == 14:
        cnpj_fmt = f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"
        if cnpj_fmt not in variacoes:
            variacoes.insert(0, cnpj_fmt)
        if digits not in variacoes:
            variacoes.append(digits)
    elif len(digits) == 11:
        cpf_fmt = f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"
        if cpf_fmt not in variacoes:
            variacoes.insert(0, cpf_fmt)
        if digits not in variacoes:
            variacoes.append(digits)

    return variacoes


def _obter_token_cws() -> Tuple[Optional[str], Optional[str]]:
    """
    Gera ou reaproveita o token Bearer da API oficial dos Correios (CWS).
    Utiliza as credenciais CORREIOS_USUARIO e CORREIOS_CODIGO_ACESSO do .env.
    """
    global _TOKEN_CACHE

    usuario = (os.getenv("CORREIOS_USUARIO") or "").strip().strip('"').strip("'")
    codigo_acesso = (os.getenv("CORREIOS_CODIGO_ACESSO") or "").strip().strip('"').strip("'")
    cartao_postagem = (os.getenv("CORREIOS_CARTAO_POSTAGEM") or "").strip().strip('"').strip("'")

    if not usuario or not codigo_acesso:
        return None, "Credenciais CORREIOS_USUARIO e CORREIOS_CODIGO_ACESSO não configuradas no .env."

    # Reaproveita token válido em cache
    if _TOKEN_CACHE["token"] and _TOKEN_CACHE["expira_em"]:
        try:
            expira_str = _TOKEN_CACHE["expira_em"]
            expira_dt = datetime.fromisoformat(expira_str)
            if datetime.now(timezone.utc) < expira_dt:
                return _TOKEN_CACHE["token"], None
        except Exception:
            pass

    candidatos_usuario = _formatar_documento(usuario)

    for u_cand in candidatos_usuario:
        auth_str = base64.b64encode(f"{u_cand}:{codigo_acesso}".encode("utf-8")).decode("utf-8")

        # Endpoint oficial de geração de token
        if cartao_postagem:
            url_token = "https://api.correios.com.br/token/v1/autentica/cartaopostagem"
            body_data = json.dumps({"numero": cartao_postagem}).encode("utf-8")
        else:
            url_token = "https://api.correios.com.br/token/v1/autentica"
            body_data = b"{}"

        try:
            req = urllib.request.Request(
                url_token,
                data=body_data,
                headers={
                    "Authorization": f"Basic {auth_str}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "User-Agent": "ValePresenteManager/2.1"
                },
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status in (200, 201):
                    res_data = json.loads(response.read().decode("utf-8"))
                    token = res_data.get("token")
                    _TOKEN_CACHE["token"] = token
                    _TOKEN_CACHE["expira_em"] = res_data.get("expiraEm")
                    _TOKEN_CACHE["ultimo_erro"] = None
                    return token, None
        except urllib.error.HTTPError as e:
            if e.code != 401:
                body = e.read().decode("utf-8", errors="ignore")
                erro_msg = f"HTTP {e.code}: Erro na autenticação com Correios ({body})."
                _TOKEN_CACHE["ultimo_erro"] = erro_msg
                return None, erro_msg
        except Exception as ex:
            erro_msg = f"Erro de conexão com o servidor de autenticação dos Correios ({ex})."
            _TOKEN_CACHE["ultimo_erro"] = erro_msg
            return None, erro_msg

    erro_msg = f"HTTP 401: Não foi possível autenticar o usuário '{usuario}'. Verifique as credenciais no portal CWS dos Correios."
    _TOKEN_CACHE["ultimo_erro"] = erro_msg
    return None, erro_msg


def consultar_rastreio_correios(codigo: str) -> Dict[str, Any]:
    """
    Consulta o rastreamento do objeto postal na API oficial dos Correios (SRO).
    Retorna dicionário estruturado para exibição no popup de timeline.
    """
    cod = limpar_codigo_rastreio(codigo)
    if not cod:
        return {
            "codigo": "",
            "sucesso": False,
            "erro": "Código de rastreamento não informado."
        }

    # 1. Tenta consulta pela API Oficial CWS dos Correios com Token Bearer
    token, erro_token = _obter_token_cws()
    if token:
        # Testa os endpoints de SRO dos Correios
        endpoints_sro = [
            f"https://api.correios.com.br/srorastreador/v1/objetos/{cod}?resultado=T",
            f"https://api.correios.com.br/sro/v1/objetos/{cod}"
        ]

        for url_sro in endpoints_sro:
            try:
                req_sro = urllib.request.Request(
                    url_sro,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": "application/json",
                        "User-Agent": "ValePresenteManager/2.1"
                    }
                )

                with urllib.request.urlopen(req_sro, timeout=8) as response:
                    if response.status == 200:
                        data = json.loads(response.read().decode("utf-8"))
                        objetos = data.get("objetos", [])
                        if objetos:
                            obj = objetos[0]
                            eventos_raw = obj.get("eventos", [])
                            eventos_formatados = []

                            for ev in eventos_raw:
                                descricao = ev.get("descricao", "")
                                detalhe = ev.get("detalhe", "") or ""
                                dt_hr_raw = ev.get("dtHrCriado", "")

                                data_fmt, hora_fmt = "", ""
                                if dt_hr_raw:
                                    try:
                                        dt_obj = datetime.fromisoformat(dt_hr_raw)
                                        data_fmt = dt_obj.strftime("%d/%m/%Y")
                                        hora_fmt = dt_obj.strftime("%H:%M")
                                    except Exception:
                                        data_fmt = dt_hr_raw[:10]
                                        hora_fmt = dt_hr_raw[11:16]

                                unidade = ev.get("unidade", {})
                                end_unidade = unidade.get("endereco", {})
                                cid_origem = end_unidade.get("cidade", "")
                                uf_origem = end_unidade.get("uf", "")
                                tipo_unidade = unidade.get("tipo", "Unidade")
                                local_str = f"{tipo_unidade} - {cid_origem}/{uf_origem}".strip(" - /")

                                unid_dest = ev.get("unidadeDestino", {})
                                end_dest = unid_dest.get("endereco", {})
                                cid_dest = end_dest.get("cidade", "")
                                uf_dest = end_dest.get("uf", "")
                                dest_str = f"{cid_dest}/{uf_dest}".strip("/")

                                if dest_str:
                                    if detalhe:
                                        detalhe = f"{detalhe} (Destino: {dest_str})"
                                    else:
                                        detalhe = f"Em trânsito para {dest_str}"

                                eventos_formatados.append({
                                "data": data_fmt,
                                "hora": hora_fmt,
                                "status": descricao,
                                "local": local_str,
                                "destino": dest_str,
                                "detalhes": detalhe
                            })

                            if eventos_formatados:
                                ultimo = eventos_formatados[0]
                                status_geral = ultimo.get("status", "Objeto em processamento")
                                entregue = "entregue" in status_geral.lower()

                                return {
                                    "codigo": cod,
                                    "sucesso": True,
                                    "servico": "Correios Oficial (CWS)",
                                    "quantidade": len(eventos_formatados),
                                    "status_geral": status_geral,
                                    "ultimo_local": ultimo.get("local", ""),
                                    "ultima_data": f"{ultimo.get('data', '')} às {ultimo.get('hora', '')}".strip(" às"),
                                    "entregue": entregue,
                                    "eventos": eventos_formatados
                                }
            except Exception:
                pass

    # 2. Fallback de API Pública LinkTrack
    try:
        url_linktrack = f"https://api.linketrack.com/track/json?user=teste&token=1abcd00b2731640e886fb41a8a9671ad143c57c304c1e4a7f671225d6cb72e36&codigo={cod}"
        req_lt = urllib.request.Request(
            url_linktrack,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json"
            }
        )
        with urllib.request.urlopen(req_lt, timeout=4) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                eventos_raw = data.get("eventos", [])
                eventos_formatados = []
                for ev in eventos_raw:
                    eventos_formatados.append({
                        "data": ev.get("data", ""),
                        "hora": ev.get("hora", ""),
                        "status": ev.get("status", ""),
                        "local": ev.get("local", ""),
                        "destino": ev.get("destino", ""),
                        "detalhes": ev.get("detalhe", "")
                    })
                if eventos_formatados:
                    ultimo = eventos_formatados[0]
                    status_geral = ultimo.get("status", "Objeto em processamento")
                    return {
                        "codigo": cod,
                        "sucesso": True,
                        "servico": "Correios (LinkTrack)",
                        "quantidade": len(eventos_formatados),
                        "status_geral": status_geral,
                        "ultimo_local": ultimo.get("local", ""),
                        "ultima_data": f"{ultimo.get('data', '')} às {ultimo.get('hora', '')}".strip(" às"),
                        "entregue": "entregue" in status_geral.lower(),
                        "eventos": eventos_formatados
                    }
    except Exception:
        pass

    # 3. Fallback Oficial com Botão 1-Clique
    return {
        "codigo": cod,
        "sucesso": False,
        "erro": "Acesse os detalhes oficiais em tempo real no portal dos Correios pelo botão abaixo."
    }
