import os
import base64
import urllib.request
import json
import dotenv
import urllib.error

dotenv.load_dotenv()

u_raw = (os.getenv("CORREIOS_USUARIO") or "").strip().strip('"').strip("'")
code = (os.getenv("CORREIOS_CODIGO_ACESSO") or "").strip().strip('"').strip("'")
digits = "".join(c for c in u_raw if c.isdigit())
formatted = f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}" if len(digits) == 14 else u_raw

auth = base64.b64encode(f"{formatted}:{code}".encode("utf-8")).decode("utf-8")

req = urllib.request.Request(
    "https://api.correios.com.br/token/v1/autentica",
    data=b"{}",
    headers={
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "ValePresenteManager/2.1"
    },
    method="POST"
)
res = urllib.request.urlopen(req)
data = json.loads(res.read().decode("utf-8"))
token = data.get("token")

cod = "OY850448629BR"

test_paths = [
    f"https://api.correios.com.br/sro/v1/objetos/{cod}",
    f"https://api.correios.com.br/sro/v1/objetos/{cod}?resultado=T",
    f"https://api.correios.com.br/sro-rastro/v1/objetos/{cod}",
    f"https://api.correios.com.br/rastreamento/v1/objetos/{cod}",
    f"https://api.correios.com.br/srorastreador/v1/objetos/{cod}",
    f"https://api.correios.com.br/srorastreador/v1/app/objetos/{cod}",
    f"https://api.correios.com.br/prepostagem/v1/rastreamento/{cod}",
    f"https://api.correios.com.br/sro/v1/eventos/{cod}",
    f"https://api.correios.com.br/sro/v1/objetos?codigo={cod}",
]

for url in test_paths:
    try:
        req_sro = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "User-Agent": "ValePresenteManager/2.1"
            }
        )
        with urllib.request.urlopen(req_sro, timeout=6) as res_sro:
            body = res_sro.read().decode("utf-8")
            print(f"✅ SUCCESS {res_sro.status} on {url}:")
            print(body[:600])
            break
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        print(f"❌ {e.code} on {url}: {body[:150]}")
    except Exception as ex:
        print(f"❌ ERROR on {url}: {ex}")
