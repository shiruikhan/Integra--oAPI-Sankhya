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

    # Consulta dados da tabela 'clientes'
    cursor.execute("""
        SELECT 
            id_cliente, 
            nome, 
            documento, 
            email, 
            telefone,
            rua,
            numero,
            cep,
            bairro,
            cidade,
            estado,
            complemento
        FROM clientes
        WHERE integrado is null
    """)
    
    clientes = cursor.fetchall()

    print(f"[INFO] {len(clientes)} registros encontrados.")

    documentos_processados = set()

    for cliente in clientes:
        if cliente["documento"] in documentos_processados:
            print(f"[SKIP] Documento {cliente['documento']} já processado. Pulando...")
            # Atualiza o campo 'integrado' para TRUE
            update_query = "UPDATE clientes SET integrado = TRUE WHERE id_cliente = %s"
            cursor.execute(update_query, (cliente["id_cliente"],))
            conn.commit()
            continue
        
        documentos_processados.add(cliente["documento"])
        
        try:
            token = get_bearer_token()
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            }

            fields = [
                "ID", "RAZAOSOCIAL", "DOCUMENTO", "EMAIL", "TELEFONE", "ENDERECO", "NUMERO", "CEP", "BAIRRO", "CODCID", "SIGLA", "COMPLEMENTO"
            ]

            values = {
                "0": cliente["id_cliente"],
                "1": cliente["nome"],
                "2": cliente["documento"],
                "3": cliente["email"],
                "4": cliente["telefone"],
                "5": cliente["rua"],
                "6": cliente["numero"],
                "7": cliente["cep"],
                "8": cliente["bairro"],
                "9": cliente["cidade"],
                "10": cliente["estado"],
                "11": cliente["complemento"]
            }

            payload = {
                "serviceName": "DatasetSP.save",
                "requestBody": {
                    "entityName": "AD_TGSPAR",
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
                    print(f"[ERRO] Cliente {cliente['id_cliente']} - Retorno da API indicou erro: {response_data}")
                else:
                    print(f"[OK] Cliente {cliente['id_cliente']} integrado com sucesso. Retorno: {response_data}")

                    # Atualiza o campo 'integrado' para TRUE
                    update_query = "UPDATE clientes SET integrado = TRUE WHERE id_cliente = %s"
                    cursor.execute(update_query, (cliente["id_cliente"],))
                    conn.commit()
            else:
                print(f"[ERRO] Cliente {cliente['id_cliente']} falhou: {response.status_code} - {response.text}")

        except Exception as e:
            print(f"[EXCEÇÃO] Cliente {cliente['id_cliente']} - Erro: {str(e)}")


except Exception as e:
    print(f"[FATAL] Erro ao conectar no banco MySQL: {str(e)}")

finally:
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()
