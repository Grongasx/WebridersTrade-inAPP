import os
import base64
import urllib.request
import json
import dotenv

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

parts = token.split(".")
if len(parts) >= 2:
    payload_b64 = parts[1] + "=="
    payload = json.loads(base64.urlsafe_b64decode(payload_b64.encode()))
    print("JWT Payload:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
