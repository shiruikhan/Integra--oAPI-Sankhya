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
            id_produto,
            quantidade,
            preco_unitario,
            desconto
        FROM pedido_itens
        WHERE integrado is null
    """)
    
    pedido_itens = cursor.fetchall()

    print(f"[INFO] {len(pedido_itens)} registros encontrados.")

    documentos_processados = set()

    for pedido_iten in pedido_itens:
        if pedido_iten["id_item"] in documentos_processados:
            print(f"[SKIP] ItemPedido {pedido_iten['id_item']} já processado. Pulando...")
            # Atualiza o campo 'integrado' para TRUE
            update_query = "UPDATE pedido_itens SET integrado = TRUE WHERE id_item = %s"
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

            fields = [
                "IDITEM", "NUPED", "QTDNEG", "VLRUNIT", "DESCONTO", "CODPROD"
            ]

            values = {
                "0": pedido_iten["id_item"],
                "1": pedido_iten["id_pedido"],
                "2": pedido_iten["quantidade"],
                "3": float(pedido_iten["preco_unitario"]),
                "4": float(pedido_iten["desconto"]),
                "5": pedido_iten["id_produto"]
            }

            payload = {
                "serviceName": "DatasetSP.save",
                "requestBody": {
                    "entityName": "AD_TGSITE",
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
                else:
                    print(f"[OK] ItemPedido {pedido_iten['id_item']} integrado com sucesso. Retorno: {response_data}")

                    
                    update_query = "UPDATE pedido_itens SET integrado = TRUE WHERE id_item = %s"
                    cursor.execute(update_query, (pedido_iten["id_item"],))
                    conn.commit()
            else:
                print(f"[ERRO] ItemPedido {pedido_iten['id_item']} falhou: {response.status_code} - {response.text}")

        except Exception as e:
            print(f"[EXCEÇÃO] ItemPedido {pedido_iten['id_item']} - Erro: {str(e)}")


except Exception as e:
    print(f"[FATAL] Erro ao conectar no banco MySQL: {str(e)}")

finally:
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()
