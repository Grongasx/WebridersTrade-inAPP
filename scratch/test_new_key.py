import base64
import urllib.request
import json
import urllib.error

key = "cws-ch1_fyGM63xI2rFEfGeUEo6d2VicmlkZXJzOjk5MTI0OTcxMzk_MTpCejA6najfWLj3tuSbfAN"
contrato = "9912497139"

usuarios = [
    "webriders",
    "26.346.974/0001-15",
    "26346974000115"
]

for user in usuarios:
    auth = base64.b64encode(f"{user}:{key}".encode("utf-8")).decode("utf-8")
    
    endpoints = [
        ("https://api.correios.com.br/token/v1/autentica/contrato", json.dumps({"numero": contrato}).encode("utf-8")),
        ("https://api.correios.com.br/token/v1/autentica", b"{}")
    ]
    
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
                print(f"SUCCESS 201 with user '{user}' on {url}!")
                token = data.get("token")
                print("Token:", token[:30], "...")
                print("Expira em:", data.get("expiraEm"))
                
                # Test SRO Tracking with this token
                for cod in ["AP342874802BR", "OY850448629BR"]:
                    url_sro = f"https://api.correios.com.br/srorastro/v1/objetos/{cod}"
                    try:
                        req_sro = urllib.request.Request(
                            url_sro,
                            headers={
                                "Authorization": f"Bearer {token}",
                                "Accept": "application/json",
                                "User-Agent": "ValePresenteManager/2.1"
                            }
                        )
                        with urllib.request.urlopen(req_sro, timeout=8) as res_sro:
                            sro_data = json.loads(res_sro.read().decode("utf-8"))
                            print(f"SRO SUCCESS on {cod}:")
                            print(json.dumps(sro_data, indent=2, ensure_ascii=False)[:500])
                    except urllib.error.HTTPError as err_sro:
                        print(f"SRO FAIL {err_sro.code} on {cod}:", err_sro.read().decode("utf-8", errors="ignore")[:200])
                
                exit(0)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="ignore")
            print(f"FAIL {e.code} [{user}] on {url}: {body[:100]}")
        except Exception as ex:
            print(f"ERROR [{user}] on {url}: {ex}")
