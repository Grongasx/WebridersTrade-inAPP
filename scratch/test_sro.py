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
print("Token obtido com sucesso!")

for cod in ["AP342874802BR", "OY850448629BR"]:
    url_sro = f"https://api.correios.com.br/srorastreador/v1/objetos/{cod}?resultado=T"
    try:
        req_sro = urllib.request.Request(
            url_sro,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "User-Agent": "ValePresenteManager/2.1"
            }
        )
        with urllib.request.urlopen(req_sro, timeout=10) as res_sro:
            sro_data = json.loads(res_sro.read().decode("utf-8"))
            print(f"SRO {cod} status {res_sro.status}:")
            print(json.dumps(sro_data, indent=2, ensure_ascii=False)[:600])
    except urllib.error.HTTPError as e:
        print(f"SRO {cod} FAIL {e.code}:", e.read().decode("utf-8", errors="ignore"))
