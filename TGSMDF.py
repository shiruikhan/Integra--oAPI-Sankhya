import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

auth_url = os.getenv("SANKHYA_AUTH_URL")
api_url = os.getenv("SANKHYA_API_URL")
app_key = os.getenv("SANKHYA_APP_KEY")
auth_token = os.getenv("SANKHYA_AUTH_TOKEN")
username = os.getenv("SANKHYA_USERNAME")
password = os.getenv("SANKHYA_PASSWORD")

IBGE_MUNICIPIOS_URL = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios/"
CHUNK_SIZE = 500

def get_bearer_token():
    headers = {"AppKey": app_key, "Token": auth_token, "Username": username, "Password": password}
    r = requests.post(auth_url, headers=headers, timeout=60)
    if r.status_code == 200:
        token = r.json().get("bearerToken")
        if not token:
            raise Exception("Token não encontrado na resposta.")
        return token
    raise Exception(f"Erro ao autenticar: {r.status_code} - {r.text}")


def obter_municipios_ibge():
    r = requests.get(IBGE_MUNICIPIOS_URL, timeout=120)
    if r.status_code != 200:
        raise Exception(f"Falha ao consultar IBGE: {r.status_code} - {r.text}")
    dados = r.json()
    if not isinstance(dados, list):
        raise Exception("Resposta inesperada do IBGE.")
    municipios = []
    for item in dados:
        mid = item.get("id")
        nome = item.get("nome")
        if mid is None or nome is None:
            continue
        municipios.append({"id": mid, "nome": nome})
    return municipios


def enviar_lote_para_sankhya(lote, headers):
    fields = ["ID", "MUNICIPIO"]
    records = [{"values": {"0": m["id"], "1": m["nome"]}} for m in lote]
    payload = {
        "serviceName": "DatasetSP.save",
        "requestBody": {"entityName": "AD_TGSMDF", "standAlone": False, "fields": fields, "records": records},
    }
    return requests.post(api_url, headers=headers, data=json.dumps(payload), timeout=120)


def enviar_unitario(m, headers):
    fields = ["ID", "MUNICIPIO"]
    payload = {
        "serviceName": "DatasetSP.save",
        "requestBody": {"entityName": "AD_TGSMDF", "standAlone": False, "fields": fields, "records": [{"values": {"0": m["id"], "1": m["nome"]}}]},
    }
    return requests.post(api_url, headers=headers, data=json.dumps(payload), timeout=120)


def chunks(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i : i + size]


if __name__ == "__main__":
    try:
        token = get_bearer_token()
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}

        municipios = obter_municipios_ibge()
        print(f"[INFO] {len(municipios)} municípios retornados pelo IBGE.")

        total_ok, total_fail = 0, 0
        lotes = list(chunks(municipios, CHUNK_SIZE))
        for idx, lote in enumerate(lotes, start=1):
            try:
                resp = enviar_lote_para_sankhya(lote, headers)
                if resp.status_code == 200:
                    dados = resp.json()
                    if isinstance(dados, dict) and dados.get("status") == "ERROR":
                        print(f"[ERRO] Lote {idx}/{len(lotes)} falhou (retorno ERROR). Tentando unitário...")
                        for m in lote:
                            r2 = enviar_unitario(m, headers)
                            if r2.status_code == 200 and not (isinstance(r2.json(), dict) and r2.json().get("status") == "ERROR"):
                                total_ok += 1
                                print(f"  [OK] ID={m['id']} '{m['nome']}' enviado.")
                            else:
                                total_fail += 1
                                print(f"  [ERRO] ID={m['id']} - {r2.status_code}: {r2.text}")
                    else:
                        total_ok += len(lote)
                        print(f"[OK] Lote {idx}/{len(lotes)} enviado: +{len(lote)} registros.")
                else:
                    print(f"[ERRO] Lote {idx}/{len(lotes)} HTTP {resp.status_code}. Tentando unitário...")
                    for m in lote:
                        r2 = enviar_unitario(m, headers)
                        if r2.status_code == 200 and not (isinstance(r2.json(), dict) and r2.json().get("status") == "ERROR"):
                            total_ok += 1
                            print(f"  [OK] ID={m['id']} '{m['nome']}' enviado.")
                        else:
                            total_fail += 1
                            print(f"  [ERRO] ID={m['id']} - {r2.status_code}: {r2.text}")
            except Exception as e:
                print(f"[EXCEÇÃO] Lote {idx}/{len(lotes)} - {str(e)}. Tentando unitário...")
                for m in lote:
                    try:
                        r2 = enviar_unitario(m, headers)
                        if r2.status_code == 200 and not (isinstance(r2.json(), dict) and r2.json().get("status") == "ERROR"):
                            total_ok += 1
                            print(f"  [OK] ID={m['id']} '{m['nome']}' enviado.")
                        else:
                            total_fail += 1
                            print(f"  [ERRO] ID={m['id']} - {r2.status_code}: {r2.text}")
                    except Exception as ee:
                        total_fail += 1
                        print(f"  [EXCEÇÃO] ID={m['id']} - {str(ee)}")

        print(f"[RESUMO] Sucessos: {total_ok} | Falhas: {total_fail}")
    except Exception as e:
        print(f"[FATAL] {str(e)}")