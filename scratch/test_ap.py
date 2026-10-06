import urllib.request
import json

key = "cws-ch1_fyGM63xI2rFEfGeUEo6d2VicmlkZXJzOjk5MTI0OTcxMzk_MTpCejA6najfWLj3tuSbfAN"
cod = "AP342874802BR"
url = f"https://api.correios.com.br/srorastro/v1/objetos/{cod}"

req = urllib.request.Request(url, headers={
    "Authorization": f"Bearer {key}",
    "Accept": "application/json",
    "User-Agent": "ValePresenteManager/2.1"
})
with urllib.request.urlopen(req, timeout=6) as res:
    data = json.loads(res.read().decode("utf-8"))
    print("STATUS 200!")
    print(json.dumps(data, indent=2, ensure_ascii=False)[:800])
