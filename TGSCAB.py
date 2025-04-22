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

    # Consulta dados da tabela 'pedidos'
    cursor.execute("""
        SELECT 
            id_pedido,
            id_cliente,
            forma_pagamento,
            data_pedido,
            observacao
        FROM pedidos
        WHERE integrado is null
    """)
    
    pedidos = cursor.fetchall()

    print(f"[INFO] {len(pedidos)} registros encontrados.")

    documentos_processados = set()

    for pedido in pedidos:
        if pedido["id_pedido"] in documentos_processados:
            print(f"[SKIP] Pedido {['id_pedido']} já processado. Pulando...")
            # Atualiza o campo 'integrado' para TRUE
            update_query = "UPDATE pedidos SET integrado = TRUE WHERE id_pedido = %s"
            cursor.execute(update_query, (pedido["id_pedido"],))
            conn.commit()
            continue
        
        documentos_processados.add(pedido["id_pedido"])
        
        try:
            token = get_bearer_token()
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            }

            fields = [
                "NUPED", "ID", "PGTO", "DTPED", "OBSERVACAO"
            ]

            values = {
                "0": pedido["id_pedido"],
                "1": pedido["id_cliente"],
                "2": pedido["forma_pagamento"],
                "3": pedido["data_pedido"].strftime("%d/%m/%Y"),
                "4": pedido["observacao"]
            }

            payload = {
                "serviceName": "DatasetSP.save",
                "requestBody": {
                    "entityName": "AD_TGSCAB",
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
    
                # Aqui você pode adaptar de acordo com a estrutura da resposta esperada
                if "status" in response_data and response_data["status"] == "ERROR":
                    print(f"[ERRO] Pedido {pedido['']} - Retorno da API indicou erro: {response_data}")
                else:
                    print(f"[OK] Pedido {pedido['id_pedido']} integrado com sucesso. Retorno: {response_data}")

                    # Atualiza o campo 'integrado' para TRUE
                    update_query = "UPDATE pedidos SET integrado = TRUE WHERE id_pedido = %s"
                    cursor.execute(update_query, (pedido["id_pedido"],))
                    conn.commit()
            else:
                print(f"[ERRO] Pedido {pedido['id_pedido']} falhou: {response.status_code} - {response.text}")

        except Exception as e:
            print(f"[EXCEÇÃO] Pedido {pedido['id_pedido']} - Erro: {str(e)}")


except Exception as e:
    print(f"[FATAL] Erro ao conectar no banco MySQL: {str(e)}")

finally:
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()
