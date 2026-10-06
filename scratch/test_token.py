import os
import base64
import urllib.request
import json
import dotenv
import urllib.error

dotenv.load_dotenv()

u_raw = (os.getenv("CORREIOS_USUARIO") or "").strip().strip('"').strip("'")
code = (os.getenv("CORREIOS_CODIGO_ACESSO") or "").strip().strip('"').strip("'")
cartao = (os.getenv("CORREIOS_CARTAO_POSTAGEM") or "").strip().strip('"').strip("'")
contrato = (os.getenv("CORREIOS_CONTRATO") or "").strip().strip('"').strip("'")

digits = "".join(c for c in u_raw if c.isdigit())
formatted = f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}" if len(digits) == 14 else (
    f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}" if len(digits) == 11 else u_raw
)

test_users = [
    ("Somente Numeros", digits),
    ("Formatado com Pontuacao", formatted),
    ("Original (.env)", u_raw)
]

for label, user_test in test_users:
    if not user_test:
        continue
    auth = base64.b64encode(f"{user_test}:{code}".encode("utf-8")).decode("utf-8")
    
    endpoints = [
        ("https://api.correios.com.br/token/v1/autentica", b"{}"),
    ]
    if cartao:
        endpoints.append(("https://api.correios.com.br/token/v1/autentica/cartaopostagem", json.dumps({"numero": cartao}).encode()))
    if contrato:
        endpoints.append(("https://api.correios.com.br/token/v1/autentica/contrato", json.dumps({"numero": contrato}).encode()))

    for url, payload in endpoints:
        try:
            req = urllib.request.Request(
                url,
                data=payload,
                headers={
                    "Authorization": f"Basic {auth}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "User-Agent": "ValePresenteManager/2.1"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=8) as res:
                data = json.loads(res.read().decode("utf-8"))
                print(f"SUCCESS 201 com [{label}] na URL: {url}!")
                print(f"Token: {data.get('token')[:30]}...")
                print(f"Expira em: {data.get('expiraEm')}")
                print(f"Ambiente: {data.get('ambiente')}")
                exit(0)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="ignore")
            print(f"FAIL {e.code} [{label}] em {url}: {body}")
        except Exception as ex:
            print(f"ERROR [{label}] em {url}: {ex}")
