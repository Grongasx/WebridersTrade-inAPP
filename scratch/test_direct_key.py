import urllib.request
import json
import urllib.error

key = "cws-ch1_fyGM63xI2rFEfGeUEo6d2VicmlkZXJzOjk5MTI0OTcxMzk_MTpCejA6najfWLj3tuSbfAN"
cod = "OY850448629BR"
url = f"https://api.correios.com.br/srorastro/v1/objetos/{cod}"

header_variations = [
    ("Bearer", {"Authorization": f"Bearer {key}"}),
    ("Direct Token", {"token": key, "Authorization": f"Bearer {key}"}),
    ("X-API-KEY", {"X-API-KEY": key}),
    ("api-key", {"api-key": key}),
    ("apikey", {"apikey": key}),
    ("Chave", {"Chave-Acesso": key}),
]

for name, headers in header_variations:
    headers["Accept"] = "application/json"
    headers["User-Agent"] = "ValePresenteManager/2.1"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=6) as res:
            data = json.loads(res.read().decode("utf-8"))
            print(f"SUCCESS {res.status} with header [{name}]:")
            print(json.dumps(data, indent=2, ensure_ascii=False)[:500])
            exit(0)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        print(f"FAIL {e.code} [{name}]: {body[:120]}")
    except Exception as ex:
        print(f"ERROR [{name}]: {ex}")
