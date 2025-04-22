import mysql.connector
import requests
import json
import os
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

# --- CONFIGURAÇÕES ---

# Conexão MySQL (nuvem - Hostinger)
mysql_config = {
    'host': os.getenv("MYSQL_HOST"),
    'user': os.getenv("MYSQL_USER"),
    'password': os.getenv("MYSQL_PASSWORD"),
    'database': os.getenv("MYSQL_DATABASE")
}

# URLs e autenticação API Sankhya
auth_url = os.getenv("SANKHYA_AUTH_URL")
api_url = os.getenv("SANKHYA_API_URL")
app_key = os.getenv("SANKHYA_APP_KEY")
auth_token = os.getenv("SANKHYA_AUTH_TOKEN")
username = os.getenv("SANKHYA_USERNAME")
password = os.getenv("SANKHYA_PASSWORD")

# --- FUNÇÃO PARA OBTER TOKEN BEARER ---
def get_bearer_token():
    headers = {
        "AppKey": app_key,
        "Token": auth_token,
        "Username": username,
        "Password": password
    }

    response = requests.post(auth_url, headers=headers)
    
    if response.status_code == 200:
        token_data = response.json()
        token = token_data.get("bearerToken")
        if not token:
            raise Exception("Token não encontrado na resposta.")
        return token
    else:
        raise Exception(f"Erro ao autenticar: {response.status_code} - {response.text}")

# --- INÍCIO DO PROCESSO ---

try:
    # Conecta ao MySQL
    conn = mysql.connector.connect(**mysql_config)
    cursor = conn.cursor(dictionary=True)

    # Consulta dados da tabela 'pedido_itens'
    cursor.execute("""
        SELECT 
            id_item,
            id_pedido,
            numeros_serie
        FROM pedido_itens
        WHERE integradoser is null
    """)
    
    pedido_itens = cursor.fetchall()

    print(f"[INFO] {len(pedido_itens)} registros encontrados.")

    documentos_processados = set()

    for pedido_iten in pedido_itens:
        if pedido_iten["id_item"] in documentos_processados:
            print(f"[SKIP] ItemPedido {pedido_iten['id_item']} já processado. Pulando...")
            # Atualiza o campo 'integrado' para TRUE
            update_query = "UPDATE pedido_itens SET integradoser = TRUE WHERE id_item = %s"
            cursor.execute(update_query, (pedido_iten["id_item"],))
            conn.commit()
            continue
        
        documentos_processados.add(pedido_iten["id_item"])
        
        try:
            token = get_bearer_token()
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            }

            # Converte string JSON para lista Python
            try:
                series = json.loads(pedido_iten["numeros_serie"])
                if not isinstance(series, list):
                    raise ValueError("Formato inválido: esperado array JSON.")
            except Exception as e:
                print(f"[ERRO] Falha ao interpretar números de série para o item {pedido_iten['id_item']}: {str(e)}")
                continue

            sucesso = True

            for serie in series:
                fields = ["IDITEM", "NUPED", "SERIE"]
                values = {
                    "0": pedido_iten["id_item"],
                    "1": pedido_iten["id_pedido"],
                    "2": serie,
                }

                payload = {
                    "serviceName": "DatasetSP.save",
                    "requestBody": {
                        "entityName": "AD_TGSSER",
                        "standAlone": False,
                        "fields": fields,
                        "records": [
                            {
                                "values": values
                            }
                        ]
                    }
                }

                response = requests.post(api_url, headers=headers, data=json.dumps(payload))

            if response.status_code == 200:
                response_data = response.json()
    
                
                if "status" in response_data and response_data["status"] == "ERROR":
                    print(f"[ERRO] ItemPedido {pedido_iten['id_item']} - Retorno da API indicou erro: {response_data}")
                    sucesso = False
                    break
                else:
                    print(f"[OK] ItemPedido {pedido_iten['id_item']} integrado com sucesso. Retorno: {response_data}")

                    
                    
            else:
                print(f"[ERRO] ItemPedido {pedido_iten['id_item']} falhou: {response.status_code} - {response.text}")
                sucesso = False
                break
            if sucesso:
                update_query = "UPDATE pedido_itens SET integradoser = TRUE WHERE id_item = %s"
                cursor.execute(update_query, (pedido_iten["id_item"],))
                conn.commit()

        except Exception as e:
            print(f"[EXCEÇÃO] ItemPedido {pedido_iten['id_item']} - Erro: {str(e)}")


except Exception as e:
    print(f"[FATAL] Erro ao conectar no banco MySQL: {str(e)}")

finally:
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()
